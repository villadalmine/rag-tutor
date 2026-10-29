"""Centralized configuration for Universal Technical RAG Tutor."""

import os
import sys
import warnings
from pathlib import Path

# Smart offline mode: if both embedding and reranker models are cached locally in
# ~/.cache/huggingface/hub, enable HF_HUB_OFFLINE=1 for instant zero-network startup.
# Otherwise, allow automatic download on first run.
_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
_emb_ready = any(_hf_cache.glob("models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*/*.safetensors"))
_rerank_ready = any(_hf_cache.glob("models--cross-encoder--ms-marco-MiniLM-L*6-v2/snapshots/*/*.safetensors"))
if _emb_ready and _rerank_ready:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
warnings.filterwarnings("ignore")

# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BOOKS_DIR = BASE_DIR / "books"
CHROMA_DIR = BASE_DIR / "chroma_db"
BM25_INDEX_PATH = BASE_DIR / "bm25_index.pkl"
GRAPH_DATA_PATH = BASE_DIR / "knowledge_graph.json"

# Retrieval Strategy (Default: 'omnigraph' [Phase 2: KùzuDB Cypher + Hybrid ChromaDB + BM25 + Reranker], or 'hybrid' [Phase 1])
RETRIEVER_TYPE = os.getenv("RETRIEVER_TYPE", "omnigraph").lower()

# Local Embedding & Reranking Models
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
RERANKER_MODEL_NAME = os.getenv(
    "RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Ollama Configuration (Optional Local LLM Inference)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))

# Chunking Configuration (Optimized for Code & YAML)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "250"))

# Retrieval Parameters
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "6"))
TOP_K_FINAL = int(os.getenv("TOP_K_FINAL", "4"))

# Omnigraph Remote Configuration (Optional Phase 2 Daemon)
OMNIGRAPH_API_URL = os.getenv("OMNIGRAPH_API_URL", "http://localhost:8080")
OMNIGRAPH_BRANCH = os.getenv("OMNIGRAPH_BRANCH", "main")
