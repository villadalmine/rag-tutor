"""Contract schemas for external certification syllabi, MCP payloads, and ingestion metadata.

Ensures strict schema validation between study-cybercirujas, external MCPs, and rag-tutor,
preventing silent failures when upstream curricula change.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SyllabusTopicModel(BaseModel):
    """Schema validation for an official certification objective/topic from study-cybercirujas."""
    cert: str = Field(..., description="Certification identifier, e.g. 'cnpe', 'cka', 'cks'")
    id: str = Field(..., description="Topic or domain identifier, e.g. '3.4'")
    title: str = Field(..., description="Official topic title")
    weight: Optional[str] = Field(None, description="Domain weight percentage in the official exam")
    content: Optional[str] = Field(None, description="Full guide or summary content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional syllabus metadata")


class CertificationCatalogModel(BaseModel):
    """Schema validation for a certification syllabus catalog entry."""
    cert_id: str
    name: str
    organization: str = "CNCF / Linux Foundation"
    topics: List[SyllabusTopicModel] = Field(default_factory=list)


class BookMetadataManifest(BaseModel):
    """Tracks SHA-256 content hashes of ingested technical literature for incremental ingestion."""
    filename: str
    sha256: str
    total_pages: int
    total_chunks: int
    last_indexed_at: str
