"""API REST FastAPI para el Tutor de Manning (compatible con Web UIs y Open WebUI)."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src import config
from src.core import AgenticTutorCore

app = FastAPI(
    title="Manning Platform Engineering Tutor API",
    description="API REST para interactuar con el Tutor RAG Agéntico sobre libros de Manning.",
    version="1.0.0",
)

tutor = AgenticTutorCore()


class QueryRequest(BaseModel):
    question: str = Field(..., description="Pregunta técnica sobre los libros de Manning.")


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    iterations: int
    retrieved_chunks: int


@app.get("/health", tags=["Sistema"])
def health_check() -> Dict[str, Any]:
    """Estado de salud del servicio y de los componentes del tutor."""
    return {
        "status": "online",
        "retriever_type": config.RETRIEVER_TYPE,
        "ollama_model": config.OLLAMA_MODEL,
        "chroma_dir_exists": config.CHROMA_DIR.exists(),
        "bm25_index_exists": config.BM25_INDEX_PATH.exists(),
    }


@app.post("/chat", response_model=QueryResponse, tags=["Chat"])
def chat_endpoint(payload: QueryRequest):
    """Endpoint principal de consulta con loop agéntico."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    result = tutor.ask(payload.question)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        iterations=result["iterations"],
        retrieved_chunks=result["retrieved_chunks"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
