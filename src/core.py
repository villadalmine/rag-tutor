"""AI Tutor Core with Lightweight Agentic Self-Reflection Loop."""

from typing import Any, Dict, List, Optional
from src import config
from src.retrievers.base import BaseRetriever, RetrievedChunk
from src.retrievers.hybrid import HybridRetriever
from src.retrievers.omnigraph import OmnigraphRetriever


def get_retriever() -> BaseRetriever:
    """Factory to instantiate the retriever based on configuration (Phase 1 vs Phase 2)."""
    if config.RETRIEVER_TYPE == "omnigraph":
        print("[Info] Using OmnigraphRetriever (Phase 2: GraphRAG)")
        return OmnigraphRetriever()
    print("[Info] Using HybridRetriever (Phase 1: ChromaDB + BM25 + Reranker)")
    return HybridRetriever()


class OpenAICompatLLM:
    """Minimal client for any OpenAI-compatible `/chat/completions` endpoint (no extra dependency)."""

    def __init__(self, base_url: str, model: str, api_key: str = "", temperature: float = 0.2,
                 max_tokens: int = 900, timeout: float = 180):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.api_key = model, api_key
        self.temperature, self.max_tokens, self.timeout = temperature, max_tokens, timeout

    def invoke(self, prompt: str) -> str:
        import requests

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = requests.post(
            self.url,
            headers=headers,
            timeout=self.timeout,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""


class AgenticTutorCore:
    """Technical Platform Tutor with agentic refinement and architectural grounding."""

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        self.retriever = retriever or get_retriever()
        self._llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Connects the synthesis LLM: an OpenAI-compatible endpoint (LLM_BASE_URL) or Ollama."""
        try:
            if config.LLM_PROVIDER == "openai":
                if not config.LLM_BASE_URL:
                    raise ValueError("LLM_PROVIDER=openai needs LLM_BASE_URL")
                self._llm = OpenAICompatLLM(
                    base_url=config.LLM_BASE_URL,
                    model=config.LLM_MODEL,
                    api_key=config.LLM_API_KEY,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS,
                    timeout=config.LLM_TIMEOUT,
                )
                return
            from langchain_ollama import OllamaLLM

            self._llm = OllamaLLM(
                base_url=config.OLLAMA_BASE_URL,
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
            )
        except Exception as e:
            print(f"[Warning] No synthesis LLM available ({e}). Retrieval-only mode.")
            self._llm = None

    @property
    def llm_label(self) -> str:
        """`provider:model` of the synthesis LLM, or a note when there is none."""
        return f"{config.LLM_PROVIDER}:{config.LLM_MODEL}" if self._llm else "none (retrieve-only)"

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Formats chunks with clear delimiters and citations."""
        if not chunks:
            return "No specific technical context found in the library."
        formatted = []
        for i, ch in enumerate(chunks, 1):
            citation = ch.to_citation()
            formatted.append(f"--- [Chunk {i} | Source: {citation}] ---\n{ch.content}")
        return "\n\n".join(formatted)

    def retrieve_only(
        self,
        question: str,
        top_k: Optional[int] = None,
        domain: Optional[str] = None,
        code_lang: Optional[str] = None,
        book: Optional[str] = None,
        min_year: Optional[int] = None,
        tag: Optional[str] = None,
        section: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes deterministic retrieval (Hybrid + Reranker + KùzuDB Graph) WITHOUT requiring an LLM (Ollama).

        Ideal for automated tests, CI pipelines, and token-efficient MCP retrieval.
        """
        k = top_k or config.TOP_K_FINAL
        chunks = self.retriever.retrieve(
            question,
            top_k=k,
            domain=domain,
            code_lang=code_lang,
            book=book,
            min_year=min_year,
            tag=tag,
            section=section,
        )
        sources = list(dict.fromkeys([c.to_citation() for c in chunks]))
        formatted_context = self._format_context(chunks)
        return {
            "answer": formatted_context,
            "chunks": chunks,
            "sources": sources,
            "iterations": 1,
            "retrieved_chunks": len(chunks),
            "retriever_engine": config.RETRIEVER_TYPE,
            "llm_model": "none (retrieve-only / LLM-free mode)",
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "reranker_model": config.RERANKER_MODEL_NAME,
        }

    def ask(
        self,
        question: str,
        extra_chunks: Optional[List[RetrievedChunk]] = None,
        domain: Optional[str] = None,
        code_lang: Optional[str] = None,
        book: Optional[str] = None,
        min_year: Optional[int] = None,
        tag: Optional[str] = None,
        section: Optional[str] = None,
        no_llm: bool = False,
    ) -> Dict[str, Any]:
        """Executes the agentic grounded technical reasoning loop.

        Workflow:
        1. Initial hybrid or ontological retrieval (augmented with any external MCP chunks).
        2. LLM sufficiency self-evaluation (verifying commands, manifests, and concepts).
        3. Secondary complementary retrieval pass if technical gaps are identified.
        4. Rigorous technical response generation with exact citations.
        (If no_llm=True or Ollama is unreachable, falls back cleanly to deterministic retrieval).
        """
        if no_llm or not self._llm:
            return self.retrieve_only(
                question,
                domain=domain,
                code_lang=code_lang,
                book=book,
                min_year=min_year,
                tag=tag,
                section=section,
            )

        # Step 1: Initial retrieval
        retrieved_chunks = self.retriever.retrieve(
            question,
            top_k=config.TOP_K_RETRIEVAL,
            domain=domain,
            code_lang=code_lang,
            book=book,
            min_year=min_year,
            tag=tag,
            section=section,
        )
        chunks = (extra_chunks or []) + retrieved_chunks
        iterations = 1

        # Step 2: Lightweight sufficiency self-reflection
        if chunks:
            context_preview = self._format_context(chunks[:2])
            eval_prompt = f"""You are a technical reviewer. Evaluate whether the following technical context contains sufficient information to answer the engineer's question (especially checking for commands, YAML manifests, or relevant code).

Available Context:
{context_preview}

Engineer's Question:
{question}

Respond EXACTLY with:
SUFFICIENT
or:
NEED_MORE_INFO: [exact concept, command, or YAML manifest to search]"""

            try:
                eval_res = self._llm.invoke(eval_prompt).strip()
                trigger_key = None
                if "NEED_MORE_INFO:" in eval_res:
                    trigger_key = "NEED_MORE_INFO:"
                elif "NECESITO_MAS_INFO:" in eval_res:
                    trigger_key = "NECESITO_MAS_INFO:"

                if trigger_key:
                    sub_query = eval_res.split(trigger_key)[1].strip()
                    if sub_query:
                        # Step 3: Targeted complementary retrieval
                        extra_retrieved = self.retriever.retrieve(
                            sub_query,
                            top_k=2,
                            domain=domain,
                            code_lang=code_lang,
                            book=book,
                            min_year=min_year,
                            tag=tag,
                            section=section,
                        )
                        existing_contents = {c.content for c in chunks}
                        for ec in extra_retrieved:
                            if ec.content not in existing_contents:
                                chunks.append(ec)
                                existing_contents.add(ec.content)
                        iterations = 2
            except Exception as e:
                print(f"[Warning in agentic evaluation ({e}) — falling back to LLM-free retrieval]")
                return self.retrieve_only(
                    question,
                    domain=domain,
                    code_lang=code_lang,
                    book=book,
                    min_year=min_year,
                    tag=tag,
                    section=section,
                )

        # Step 4: Final grounded synthesis
        total_k = config.TOP_K_FINAL + (len(extra_chunks) if extra_chunks else 0)
        full_context = self._format_context(chunks[:total_k])
        system_prompt = f"""You are a Principal Systems Engineer and Senior Cloud-Native Architect.
Your mission is to provide rigorous, accurate technical answers based EXCLUSIVELY on the following technical context (which includes official certification syllabi and engineering books).

Mandatory Rules:
1. If the context contains certification requirements, YAML manifests, Go code, CLI flags, or CRD definitions, use and explain them accurately.
2. Do not hallucinate non-existent configurations. If the context does not cover a specific aspect, state it transparently.
3. Explicitly cite all sources (certification syllabi, books, and page numbers) when explaining concepts.

Official Technical Context:
{full_context}

Engineer's Question:
{question}

Detailed Technical Answer:"""

        try:
            response = self._llm.invoke(system_prompt)
        except Exception as e:
            print(f"[Warning: synthesis LLM not reachable ({e}) — returning retrieved context directly]")
            return self.retrieve_only(
                question,
                domain=domain,
                code_lang=code_lang,
                book=book,
                min_year=min_year,
                tag=tag,
                section=section,
            )
        sources = list(dict.fromkeys([c.to_citation() for c in chunks[:total_k]]))

        return {
            "answer": response,
            "sources": sources,
            "iterations": iterations,
            "retrieved_chunks": len(chunks),
            "retriever_engine": config.RETRIEVER_TYPE,
            "llm_model": self.llm_label,
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "reranker_model": config.RERANKER_MODEL_NAME,
        }


