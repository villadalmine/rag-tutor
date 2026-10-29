"""Phase 1: Hybrid Retriever (ChromaDB + BM25 + Cross-Encoder Reranker)."""

import os
import pickle
from typing import Any, Dict, List, Optional

from src import config
from .base import BaseRetriever, RetrievedChunk


class HybridRetriever(BaseRetriever):
    """Combines semantic vector search with lexical BM25 retrieval and Cross-Encoder reranking."""

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
        """Loads ChromaDB if the persisted directory exists."""
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
                print(f"[Warning] Could not load ChromaDB: {e}")
        else:
            print(f"[Warning] ChromaDB directory not found at {self.chroma_dir}. Run 'python src/ingest.py' first.")

    def _initialize_bm25(self):
        """Loads the persisted BM25 index."""
        if os.path.exists(self.bm25_path):
            try:
                with open(self.bm25_path, "rb") as f:
                    data = pickle.load(f)
                    self._bm25_index = data.get("bm25")
                    self._bm25_corpus = data.get("corpus", [])
            except Exception as e:
                print(f"[Warning] Error loading BM25 index: {e}")
        else:
            print(f"[Warning] BM25 index not found at {self.bm25_path}. It will be generated during ingestion.")

    def _initialize_reranker(self):
        """Loads the CrossEncoder model for reranking."""
        try:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(self.reranker_model)
        except Exception as e:
            # Reranker is optional when memory is constrained
            print(f"[Info] CrossEncoder not initialized ({e}). Falling back to base score fusion.")
            self._reranker = None

    def _build_chroma_filter(
        self,
        domain: Optional[str] = None,
        code_lang: Optional[str] = None,
        book: Optional[str] = None,
        min_year: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Builds the scalar HNSW pre-filter for ChromaDB."""
        conditions = []
        if domain:
            conditions.append({"domain": domain})
        if code_lang:
            conditions.append({"code_lang": code_lang})
        if book:
            conditions.append({"source": book})
        if min_year:
            conditions.append({"publication_year": {"$gte": int(min_year)}})
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    @staticmethod
    def _matches_post_filters(
        meta: Dict[str, Any],
        domain: Optional[str] = None,
        book: Optional[str] = None,
        tag: Optional[str] = None,
        section: Optional[str] = None,
    ) -> bool:
        """Evaluates WHERE filters (domain/secondary_domains, book, tag, section) on chunk metadata."""
        if domain:
            dom_match = (meta.get("domain") == domain) or (domain.lower() in str(meta.get("tags", "")).lower())
            if not dom_match:
                return False
        if book and book.lower() not in str(meta.get("source", "")).lower():
            return False
        if tag:
            tags_str = f"{meta.get('tags', '')} {meta.get('domain', '')}".lower()
            if tag.lower() not in tags_str:
                return False
        if section:
            sec_str = f"{meta.get('chapter', '')} {meta.get('section_title', '')}".lower()
            if section.lower() not in sec_str:
                return False
        return True

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        domain: Optional[str] = None,
        code_lang: Optional[str] = None,
        book: Optional[str] = None,
        min_year: Optional[int] = None,
        tag: Optional[str] = None,
        section: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Executes combined hybrid search (with optional WHERE pre-filtering) and reranks candidates."""
        candidates: Dict[str, RetrievedChunk] = {}
        # Pre-filter code_lang and min_year in HNSW and evaluate domain/secondary_domains/book/tag/section in _matches_post_filters
        chroma_filter = self._build_chroma_filter(
            domain=None, code_lang=code_lang, book=None, min_year=min_year
        )
        fetch_k = top_k * 5 if (domain or book or tag or section) else top_k * 2

        # 1. Vector Search (Semantic)
        if self._vectorstore:
            try:
                search_kwargs: Dict[str, Any] = {"k": fetch_k}
                if chroma_filter:
                    search_kwargs["filter"] = chroma_filter
                docs = self._vectorstore.similarity_search(query, **search_kwargs)
                for doc in docs:
                    if not self._matches_post_filters(doc.metadata, domain=domain, book=book, tag=tag, section=section):
                        continue
                    key = doc.page_content.strip()
                    candidates[key] = RetrievedChunk(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "Technical Book"),
                        page=doc.metadata.get("page"),
                        score=0.5,
                        metadata=doc.metadata,
                    )
            except Exception as e:
                print(f"[Vector Search Error]: {e}")

        # 2. Lexical Search (BM25 for exact YAML keys, CRDs, CLI flags, and function names)
        if self._bm25_index and self._bm25_corpus:
            try:
                tokens = query.lower().split()
                scores = self._bm25_index.get_scores(tokens)
                ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

                matched_bm25 = 0
                for idx in ranked_indices:
                    if matched_bm25 >= top_k * 2:
                        break
                    item = self._bm25_corpus[idx]
                    meta = item.get("metadata", {})
                    if code_lang and meta.get("code_lang") != code_lang:
                        continue
                    if min_year:
                        pub_y = meta.get("publication_year")
                        if not pub_y or int(pub_y) < int(min_year):
                            continue
                    if not self._matches_post_filters(meta, domain=domain, book=book, tag=tag, section=section):
                        continue

                    matched_bm25 += 1
                    key = item["content"].strip()
                    if key in candidates:
                        # Boost base priority when matched by both dense and sparse engines
                        candidates[key].score += 0.3
                    else:
                        candidates[key] = RetrievedChunk(
                            content=item["content"],
                            source=item.get("source", "Technical Book"),
                            page=item.get("page"),
                            score=0.4,
                            metadata=meta,
                        )
            except Exception as e:
                print(f"[BM25 Search Error]: {e}")

        candidate_list = list(candidates.values())
        if not candidate_list:
            return []

        # 3. Cross-Encoder Reranking (if available)
        if self._reranker and len(candidate_list) > 1:
            try:
                pairs = [[query, chunk.content] for chunk in candidate_list]
                rerank_scores = self._reranker.predict(pairs)
                for chunk, score in zip(candidate_list, rerank_scores):
                    chunk.score = float(score)
                candidate_list.sort(key=lambda x: x.score, reverse=True)
            except Exception as e:
                print(f"[Reranker Warning]: {e}. Using base score order.")
                candidate_list.sort(key=lambda x: x.score, reverse=True)
        else:
            candidate_list.sort(key=lambda x: x.score, reverse=True)

        return candidate_list[:top_k]
