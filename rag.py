import argparse

from pathlib import Path
import os

from dotenv import load_dotenv
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter

load_dotenv()

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "local_vector_articles"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "mps"},
)

db = FAISS.load_local(
    str(INDEX_PATH),
    embeddings,
    allow_dangerous_deserialization=True,
)
retriever = db.as_retriever(search_kwargs={"k": 5})

# llm = ChatOllama(model="qwen3:4b", temperature=0)
llm = ChatOpenRouter(
    model="liquid/lfm-2.5-2.6b:free",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY")
)

prompt = ChatPromptTemplate.from_template("""
You are an assistant answering questions about the Constitution of India.

Answer using only the context below. If it does not contain enough information,
say so. Respect the scope and timing stated in each provision. In particular,
do not present a rule that applies "at the commencement" as a current general
rule. Use provisions on territory to establish where a rule applies when the
context provides them. Do not infer a separate Union Territory citizenship
rule from provisions about Union Territory administration. Cite each legal
claim using the source number, such as [Source 1]. Use only source numbers
shown in the context, and place the citation beside the claim it supports.

Context:
{context}

Question:
{question}

Answer:
""")


def ask(question: str, *, show_sources: bool = False) -> dict[str, object]:
    docs = retriever.invoke(question)
    context_parts = []
    sources = []
    for index, doc in enumerate(docs, start=1):
        article = doc.metadata.get("article")
        title = doc.metadata.get("title")
        label = f"Article {article}" if article else doc.metadata.get("section", "Unlabelled section")
        if title:
            label += f": {title}"
        context_parts.append(f"[Source {index} — {label}]\n{doc.page_content}")
        sources.append({
            "id": index,
            "label": label,
            "document": doc.metadata.get("source"),
            "article": article,
            "title": title,
            "section": doc.metadata.get("section"),
            "text": doc.page_content,
            "part": doc.metadata.get("part"),
        })
    
    if show_sources:
        print("Retrieved sources:")
        for source in sources:
            excerpt = " ".join(str(source["text"]).split())[:260]
            print(f"[Source {source['id']} — {source['label']}] {excerpt}...")

    context = "\n\n".join(context_parts)
    messages = prompt.invoke({"context": context, "question": question})
    response = llm.invoke(messages)
    return {"answer": response.content, "sources": sources}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about the Constitution of India.")
    parser.add_argument("question", nargs="*", help="Question to ask; omit it to be prompted.")
    args = parser.parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = input("Question: ").strip()
    if not question:
        parser.error("Please provide a question.")
    result = ask(question, show_sources=True)
    print(result["answer"])


if __name__ == "__main__":
    main()
