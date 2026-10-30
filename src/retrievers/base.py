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
        """Formats the source for grounded citations (including publication year, section/page, and video timestamp)."""
        year = self.metadata.get("publication_year")
        src_label = f"{self.source} [{year}]" if year else self.source
        chapter = self.metadata.get("chapter") or self.metadata.get("section_title")
        timestamp = self.metadata.get("timestamp")
        ts_suffix = f" @ [{timestamp}]" if timestamp else ""

        if self.page and chapter:
            return f"{src_label} ({chapter}, Page {self.page}{ts_suffix})"
        if self.page:
            return f"{src_label} (Page {self.page}{ts_suffix})"
        if chapter:
            return f"{src_label} ({chapter}{ts_suffix})"
        return f"{src_label}{ts_suffix}"


class BaseRetriever(ABC):
    """Base contract implemented by all retrieval engines (Hybrid, Omnigraph, etc.)."""

    @abstractmethod
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
        """Retrieves top-k relevant chunks for a given query with optional WHERE-style metadata filters."""
        pass

