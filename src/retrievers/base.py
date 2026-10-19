"""Abstract interface and data models for retrieval engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievedChunk:
    """Normalized representation of a retrieved content chunk."""

    content: str
    source: str
    page: Optional[int] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_citation(self) -> str:
        """Formats the source for grounded citations."""
        if self.page:
            return f"{self.source} (Page {self.page})"
        return self.source


class BaseRetriever(ABC):
    """Base contract implemented by all retrieval engines (Hybrid, Omnigraph, etc.)."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Retrieves top-k relevant chunks for a given query.

        Args:
            query: Question or search term.
            top_k: Number of desired candidate chunks.

        Returns:
            List of RetrievedChunk ordered by relevance.
        """
        pass

