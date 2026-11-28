from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rag import ask

app = FastAPI(
    title="Legal GraphRAG API",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=2000,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask_question(request: QuestionRequest):
    try:
        return ask(request.question)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="GraphRAG 검색 중 오류가 발생했습니다.",
        ) from e