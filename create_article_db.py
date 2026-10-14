import re
from pathlib import Path

import pymupdf4llm
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter


ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "constitution.pdf"
INDEX_PATH = ROOT / "local_vector_articles"

# In pymupdf4llm's output, article headings are bolded, for example:
# **5. Citizenship at the commencement of the Constitution.** —At ...
ARTICLE_PREFIX = r"^[ \t]*(?:>[ \t]*)?(?:\d+\[[ \t]*)?\*\*"
ARTICLE_START_RE = re.compile(
    ARTICLE_PREFIX + r"(?P<number>\d{1,3}[A-Z]{0,2})\.",
    re.MULTILINE,
)
ARTICLE_HEADER_RE = re.compile(
    ARTICLE_PREFIX
    + r"(?P<number>\d{1,3}[A-Z]{0,2})\.\s*(?P<title>.*?)"
    + r"(?:\*\*)?\s*\.?\s*[—–-]\s*(?:\*\*)?",
    re.DOTALL,
)
PART_HEADER_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?\*\*PART\s+[IVXLCDM]+\*\*.*$",
    re.MULTILINE,
)
SCHEDULE_HEADER_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\d+\[[ \t]*)?(?:\*\*)?(?:THE[ \t]+)?"
    r"(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|"
    r"NINTH|TENTH|ELEVENTH|TWELFTH)[ \t]+SCHEDULE\b",
    re.IGNORECASE | re.MULTILINE,
)


def _metadata_documents(text: str, section: str) -> list[Document]:
    if not text.strip():
        return []

    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = splitter.create_documents([text])
    for document in documents:
        document.metadata.update({"source": PDF_PATH.name, "section": section})
    return documents


def make_article_documents(markdown: str) -> list[Document]:
    article_matches = list(ARTICLE_START_RE.finditer(markdown))
    if not article_matches:
        raise ValueError(
            "No bold article headings were found in the extracted Markdown. "
            "Inspect the pymupdf4llm output and adjust ARTICLE_START_RE."
        )

    final_constitution_article = next(
        (
            match for match in reversed(article_matches)
            if match.group("number") == "395"
        ),
        article_matches[-1],
    )
    schedule_match = next(
        (
            match
            for match in SCHEDULE_HEADER_RE.finditer(markdown)
            if match.start() > final_constitution_article.start()
        ),
        None,
    )
    schedule_start = schedule_match.start() if schedule_match else len(markdown)
    if schedule_match is None:
        print("No schedule heading found after the final article; check the extracted document tail.")

    article_matches = [
        match for match in article_matches if match.start() < schedule_start
    ]

    # A Part heading belongs with its first article, not the previous article.
    part_matches = list(PART_HEADER_RE.finditer(markdown))
    article_starts: list[int] = []
    previous_article_start = -1
    for match in article_matches:
        preceding_parts = [
            part for part in part_matches
            if previous_article_start < part.start() < match.start()
        ]
        article_starts.append(
            preceding_parts[-1].start() if preceding_parts else match.start()
        )
        previous_article_start = match.start()

    documents = _metadata_documents(markdown[:article_starts[0]], "front_matter")
    article_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
    )

    for index, match in enumerate(article_matches):
        start = article_starts[index]
        end = (
            article_starts[index + 1]
            if index + 1 < len(article_starts)
            else schedule_start
        )
        raw_article = markdown[match.start():end].strip()
        header = ARTICLE_HEADER_RE.match(raw_article)

        number = match.group("number")
        if header:
            title = " ".join(header.group("title").split()).strip(" .—–-")
            body = raw_article[header.end():].strip()
        else:
            title = ""
            body = raw_article
            print(f"Could not parse the title for Article {number}; retaining its raw text.")

        section_prefix = markdown[start:match.start()].strip()
        repeated_heading = f"Article {number}"
        if title:
            repeated_heading += f": {title}"

        article_text = "\n\n".join(
            part for part in (section_prefix, repeated_heading, body) if part
        )
        for part_number, chunk in enumerate(
            article_splitter.split_text(article_text), start=1
        ):
            # Repeating the article heading keeps long-article subchunks searchable
            # even when the splitter starts them in the middle of the article.
            if part_number > 1:
                chunk = f"{repeated_heading}\n{chunk}"
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": PDF_PATH.name,
                        "article": number,
                        "title": title,
                        "part": part_number,
                    },
                )
            )

    if schedule_match:
        documents.extend(_metadata_documents(markdown[schedule_start:], "schedules"))

    print(
        f"Prepared {len(article_matches)} article sections as "
        f"{len(documents)} total chunks."
    )
    print(
        "Detected article headings:",
        ", ".join(match.group("number") for match in article_matches[:12]),
    )
    print(
        "Final detected article headings:",
        ", ".join(match.group("number") for match in article_matches[-5:]),
    )
    return documents


def main() -> None:
    markdown = pymupdf4llm.to_markdown(str(PDF_PATH))
    documents = make_article_documents(markdown)

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
    )
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(str(INDEX_PATH))
    print(f"Saved the article-aware index to {INDEX_PATH}")


if __name__ == "__main__":
    main()
