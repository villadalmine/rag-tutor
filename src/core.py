"""Core de Inteligencia Artificial del Tutor con loop agéntico de auto-reflexión."""

from typing import Any, Dict, List, Optional
from src import config
from src.retrievers.base import BaseRetriever, RetrievedChunk
from src.retrievers.hybrid import HybridRetriever
from src.retrievers.omnigraph import OmnigraphRetriever


def get_retriever() -> BaseRetriever:
    """Fábrica para instanciar el recuperador según la configuración (Fase 1 vs Fase 2)."""
    if config.RETRIEVER_TYPE == "omnigraph":
        print("[Info] Utilizando OmnigraphRetriever (Fase 2: GraphRAG)")
        return OmnigraphRetriever()
    print("[Info] Utilizando HybridRetriever (Fase 1: ChromaDB + BM25 + Reranker)")
    return HybridRetriever()


class AgenticTutorCore:
    """Tutor de Plataformas con capacidad agéntica de refinamiento y verificación técnica."""

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        self.retriever = retriever or get_retriever()
        self._llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Inicializa la conexión con el modelo local en Ollama."""
        try:
            from langchain_ollama import OllamaLLM

            self._llm = OllamaLLM(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL,
                temperature=config.OLLAMA_TEMPERATURE,
            )
        except Exception as e:
            print(f"[Aviso] No se pudo conectar a Ollama: {e}. Asegúrate de ejecutar 'ollama serve'.")
            self._llm = None

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Formatea los fragmentos con delimitadores y fuentes claras."""
        if not chunks:
            return "No se encontró contexto técnico específico en la biblioteca."
        formatted = []
        for i, ch in enumerate(chunks, 1):
            citation = ch.to_citation()
            formatted.append(f"--- [Fragmento {i} | Fuente: {citation}] ---\n{ch.content}")
        return "\n\n".join(formatted)

    def ask(self, question: str) -> Dict[str, Any]:
        """Ejecuta el loop agéntico de respuesta técnica fundamentada.

        Flujo:
        1. Búsqueda inicial híbrida.
        2. Auto-evaluación del LLM sobre la suficiencia del código y contexto.
        3. Segunda pasada complementaria si se identifican vacíos técnicos.
        4. Generación de respuesta técnica precisa.
        """
        if not self._llm:
            return {
                "answer": "Error: El motor LLM local (Ollama) no está disponible. Inicia Ollama con 'ollama serve'.",
                "sources": [],
                "iterations": 0,
            }

        # Paso 1: Recuperación inicial
        chunks = self.retriever.retrieve(question, top_k=config.TOP_K_RETRIEVAL)
        iterations = 1

        # Paso 2: Evaluación rápida de suficiencia (Agentic Loop liviano)
        if chunks:
            context_preview = self._format_context(chunks[:2])
            eval_prompt = f"""Eres un revisor técnico. Evalúa si el siguiente contexto técnico contiene información suficiente para responder a la pregunta del ingeniero (especialmente verificando si hay comandos, YAMLs o código relevante).

Contexto disponible:
{context_preview}

Pregunta del Ingeniero:
{question}

Responde EXACTAMENTE con:
SUFICIENTE
o bien:
NECESITO_MAS_INFO: [concepto exacto, comando o manifest YAML que falta buscar]"""

            try:
                eval_res = self._llm.invoke(eval_prompt).strip()
                if "NECESITO_MAS_INFO:" in eval_res:
                    sub_query = eval_res.split("NECESITO_MAS_INFO:")[1].strip()
                    if sub_query:
                        # Paso 3: Búsqueda complementaria
                        extra_chunks = self.retriever.retrieve(sub_query, top_k=2)
                        existing_contents = {c.content for c in chunks}
                        for ec in extra_chunks:
                            if ec.content not in existing_contents:
                                chunks.append(ec)
                                existing_contents.add(ec.content)
                        iterations = 2
            except Exception as e:
                print(f"[Aviso en evaluación agéntica]: {e}")

        # Paso 4: Generación de respuesta técnica final
        full_context = self._format_context(chunks[: config.TOP_K_FINAL])
        system_prompt = f"""Eres un Ingeniero Principal de Plataformas y Arquitecto Senior Cloud-Native.
Tu misión es responder con máxima rigurosidad técnica basándote EXCLUSIVAMENTE en el siguiente contexto extraído de libros de Manning.

Reglas obligatorias:
1. Si el contexto contiene manifiestos YAML, código en Go, flags de CLI o definiciones de CRDs, úsalos y explícalos de forma precisa.
2. No inventes configuraciones inexistentes. Si el contexto no cubre algún aspecto, indícalo con transparencia.
3. Cita explícitamente los libros o secciones de origen al explicar la arquitectura.

Contexto Técnico Oficial de Manning:
{full_context}

Pregunta del Ingeniero:
{question}

Respuesta técnica detallada:"""

        response = self._llm.invoke(system_prompt)
        sources = list(dict.fromkeys([c.to_citation() for c in chunks[: config.TOP_K_FINAL]]))

        return {
            "answer": response,
            "sources": sources,
            "iterations": iterations,
            "retrieved_chunks": len(chunks),
        }
