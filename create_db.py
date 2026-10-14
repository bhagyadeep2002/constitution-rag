import pymupdf4llm
from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device":"cpu"}
)
md_text = pymupdf4llm.to_markdown("./constitution.pdf")
splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
documents = splitter.create_documents([md_text])
vector_store = FAISS.from_documents(documents,embeddings)
vector_store.save_local("local_vector")
db = FAISS.load_local("local_vector", embeddings, allow_dangerous_deserialization=True)
results = db.similarity_search("How is citizenship defined for union territories?", k=1)
print(results[0].page_content)
