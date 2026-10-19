"""Fase 1: Recuperador Híbrido (ChromaDB + BM25 + Cross-Encoder Reranker)."""

import os
import pickle
from typing import Any, Dict, List, Optional

from src import config
from .base import BaseRetriever, RetrievedChunk


class HybridRetriever(BaseRetriever):
    """Combina búsqueda vectorial semántica con búsqueda léxica BM25 y reranking."""

    def __init__(
        self,
        chroma_dir: Optional[str] = None,
        bm25_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        reranker_model: Optional[str] = None,
    ):
        self.chroma_dir = str(chroma_dir or config.CHROMA_DIR)
        self.bm25_path = str(bm25_path or config.BM25_INDEX_PATH)
        self.embedding_model = embedding_model or config.EMBEDDING_MODEL_NAME
        self.reranker_model = reranker_model or config.RERANKER_MODEL_NAME

        self._vectorstore = None
        self._bm25_corpus: List[Dict[str, Any]] = []
        self._bm25_index = None
        self._reranker = None

        self._initialize_vectorstore()
        self._initialize_bm25()
        self._initialize_reranker()

    def _initialize_vectorstore(self):
        """Carga ChromaDB si existe el directorio persistido."""
        if os.path.exists(self.chroma_dir):
            try:
                from langchain_chroma import Chroma
                from langchain_huggingface import HuggingFaceEmbeddings

                embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
                self._vectorstore = Chroma(
                    persist_directory=self.chroma_dir,
                    embedding_function=embeddings,
                )
            except Exception as e:
                print(f"[Aviso] No se pudo cargar ChromaDB: {e}")
        else:
            print(f"[Aviso] No existe el directorio de ChromaDB en {self.chroma_dir}. Ejecuta 'python src/ingest.py' primero.")

    def _initialize_bm25(self):
        """Carga el índice BM25 persistido."""
        if os.path.exists(self.bm25_path):
            try:
                with open(self.bm25_path, "rb") as f:
                    data = pickle.load(f)
                    self._bm25_index = data.get("bm25")
                    self._bm25_corpus = data.get("corpus", [])
            except Exception as e:
                print(f"[Aviso] Error cargando índice BM25: {e}")
        else:
            print(f"[Aviso] No se encontró el índice BM25 en {self.bm25_path}. Se generará en la ingesta.")

    def _initialize_reranker(self):
        """Carga el modelo CrossEncoder para reranking."""
        try:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(self.reranker_model)
        except Exception as e:
            # Reranker es opcional si hay limitaciones de memoria
            print(f"[Info] CrossEncoder no inicializado ({e}). Se usará fusión por puntajes estándar.")
            self._reranker = None

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Ejecuta búsqueda híbrida combinada y reordena los resultados."""
        candidates: Dict[str, RetrievedChunk] = {}

        # 1. Búsqueda Vectorial (Semántica)
        if self._vectorstore:
            try:
                docs = self._vectorstore.similarity_search(query, k=top_k * 2)
                for doc in docs:
                    key = doc.page_content.strip()
                    candidates[key] = RetrievedChunk(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "Manning"),
                        page=doc.metadata.get("page"),
                        score=0.5,
                        metadata=doc.metadata,
                    )
            except Exception as e:
                print(f"[Error en búsqueda vectorial]: {e}")

        # 2. Búsqueda Léxica (BM25 para nombres exactos de YAML, CRDs, funciones)
        if self._bm25_index and self._bm25_corpus:
            try:
                tokens = query.lower().split()
                scores = self._bm25_index.get_scores(tokens)
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k * 2]

                for idx in top_indices:
                    item = self._bm25_corpus[idx]
                    key = item["content"].strip()
                    if key in candidates:
                        # Si coincide en ambos, elevamos la prioridad base
                        candidates[key].score += 0.3
                    else:
                        candidates[key] = RetrievedChunk(
                            content=item["content"],
                            source=item.get("source", "Manning"),
                            page=item.get("page"),
                            score=0.4,
                            metadata=item.get("metadata", {}),
                        )
            except Exception as e:
                print(f"[Error en búsqueda BM25]: {e}")

        candidate_list = list(candidates.values())
        if not candidate_list:
            return []

        # 3. Reranking con Cross-Encoder (si está disponible)
        if self._reranker and len(candidate_list) > 1:
            try:
                pairs = [[query, chunk.content] for chunk in candidate_list]
                rerank_scores = self._reranker.predict(pairs)
                for chunk, score in zip(candidate_list, rerank_scores):
                    chunk.score = float(score)
                candidate_list.sort(key=lambda x: x.score, reverse=True)
            except Exception as e:
                print(f"[Aviso en Reranker]: {e}. Usando orden base.")
                candidate_list.sort(key=lambda x: x.score, reverse=True)
        else:
            candidate_list.sort(key=lambda x: x.score, reverse=True)

        return candidate_list[:top_k]
