from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from rag import ask

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer = ask(request.question)
    return {"answer": answer}

app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent / "frontend", html=True),
    name="frontend",
)
