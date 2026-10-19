"""Configuración centralizada para el Tutor de Ingeniería de Plataformas."""

import os
import sys
import warnings
from pathlib import Path

# Suprimir avisos de Hugging Face cuando se corre de forma local sin login
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

# Rutas del Proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
BOOKS_DIR = BASE_DIR / "books"
CHROMA_DIR = BASE_DIR / "chroma_db"
BM25_INDEX_PATH = BASE_DIR / "bm25_index.pkl"
GRAPH_DATA_PATH = BASE_DIR / "knowledge_graph.json"

# Estrategia de Recuperación (Fase 1: 'hybrid', Fase 2: 'omnigraph')
RETRIEVER_TYPE = os.getenv("RETRIEVER_TYPE", "hybrid").lower()

# Modelos Locales y Embeddings
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
RERANKER_MODEL_NAME = os.getenv(
    "RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Configuración de Ollama (Inferencia Local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))

# Configuración de Chunking (Optimizado para código y YAML)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "250"))

# Parámetros de Recuperación
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "6"))
TOP_K_FINAL = int(os.getenv("TOP_K_FINAL", "4"))

# Configuración de Omnigraph (Fase 2)
OMNIGRAPH_API_URL = os.getenv("OMNIGRAPH_API_URL", "http://localhost:8080")
OMNIGRAPH_BRANCH = os.getenv("OMNIGRAPH_BRANCH", "main")
