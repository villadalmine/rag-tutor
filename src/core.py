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


class AgenticTutorCore:
    """Technical Platform Tutor with agentic refinement and architectural grounding."""

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        self.retriever = retriever or get_retriever()
        self._llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initializes connection to local LLM in Ollama."""
        try:
            from langchain_ollama import OllamaLLM

            self._llm = OllamaLLM(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL,
                temperature=config.OLLAMA_TEMPERATURE,
            )
        except Exception as e:
            print(f"[Warning] Could not connect to Ollama: {e}. Make sure 'ollama serve' is running.")
            self._llm = None

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Formats chunks with clear delimiters and citations."""
        if not chunks:
            return "No specific technical context found in the library."
        formatted = []
        for i, ch in enumerate(chunks, 1):
            citation = ch.to_citation()
            formatted.append(f"--- [Chunk {i} | Source: {citation}] ---\n{ch.content}")
        return "\n\n".join(formatted)

    def ask(self, question: str) -> Dict[str, Any]:
        """Executes the agentic grounded technical reasoning loop.

        Workflow:
        1. Initial hybrid or ontological retrieval.
        2. LLM sufficiency self-evaluation (verifying commands, manifests, and concepts).
        3. Secondary complementary retrieval pass if technical gaps are identified.
        4. Rigorous technical response generation with exact citations.
        """
        if not self._llm:
            return {
                "answer": "Error: Local LLM engine (Ollama) is unavailable. Please run 'ollama serve'.",
                "sources": [],
                "iterations": 0,
            }

        # Step 1: Initial retrieval
        chunks = self.retriever.retrieve(question, top_k=config.TOP_K_RETRIEVAL)
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
                        extra_chunks = self.retriever.retrieve(sub_query, top_k=2)
                        existing_contents = {c.content for c in chunks}
                        for ec in extra_chunks:
                            if ec.content not in existing_contents:
                                chunks.append(ec)
                                existing_contents.add(ec.content)
                        iterations = 2
            except Exception as e:
                print(f"[Warning in agentic evaluation]: {e}")

        # Step 4: Final grounded synthesis
        full_context = self._format_context(chunks[: config.TOP_K_FINAL])
        system_prompt = f"""You are a Principal Systems Engineer and Senior Cloud-Native Architect.
Your mission is to provide rigorous, accurate technical answers based EXCLUSIVELY on the following context extracted from the engineering books library.

Mandatory Rules:
1. If the context contains YAML manifests, Go code, CLI flags, or CRD definitions, use and explain them accurately.
2. Do not hallucinate non-existent configurations. If the context does not cover a specific aspect, state it transparently.
3. Explicitly cite the source books and sections when explaining architectural concepts.

Official Technical Context:
{full_context}

Engineer's Question:
{question}

Detailed Technical Answer:"""

        response = self._llm.invoke(system_prompt)
        sources = list(dict.fromkeys([c.to_citation() for c in chunks[: config.TOP_K_FINAL]]))

        return {
            "answer": response,
            "sources": sources,
            "iterations": iterations,
            "retrieved_chunks": len(chunks),
            "retriever_engine": config.RETRIEVER_TYPE,
            "llm_model": config.OLLAMA_MODEL,
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "reranker_model": config.RERANKER_MODEL_NAME,
        }

