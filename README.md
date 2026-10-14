# Constitution RAG

A small FastAPI app for asking questions about the Constitution of India.

## Setup

From the project directory, create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
uv pip install -r requirements.txt
```

Add your OpenRouter key to a `.env` file in the project directory:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

The first time you set up the project, build the active vector store:

```bash
python create_article_db.py
```

This reads `constitution.pdf` and creates `local_vector_articles/`. The directory is ignored by Git, so build it again when setting up a fresh checkout.

At runtime, `rag.py` configures embeddings for Apple's MPS device. On a machine without MPS support, change `device` to `"cpu"` in `rag.py`.

## Start the app

```bash
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> in your browser. Stop the server with `Ctrl+C`.

## Vector store note

`rag.py` uses the article-aware store in `local_vector_articles/`, created by `create_article_db.py`.

`create_db.py` creates the older `local_vector/` store. The current RAG app does not use it; it remains in the project for reference.
