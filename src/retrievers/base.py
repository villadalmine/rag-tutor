"""Interfaz abstracta y modelos para los motores de recuperación."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievedChunk:
    """Representación normalizada de un fragmento recuperado."""

    content: str
    source: str
    page: Optional[int] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_citation(self) -> str:
        """Formatea la fuente para citación en la respuesta."""
        if self.page:
            return f"{self.source} (pág. {self.page})"
        return self.source


class BaseRetriever(ABC):
    """Contrato base que deben implementar todos los recuperadores (Hybrid, Omnigraph, etc.)."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Recupera los fragmentos más relevantes para una consulta dada.

        Args:
            query: Pregunta o término de búsqueda.
            top_k: Cantidad de fragmentos finales deseados.

        Returns:
            Lista de RetrievedChunk ordenados por relevancia.
        """
        pass
