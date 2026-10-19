"""Módulo de capas de recuperación (Retrievers)."""

from .base import BaseRetriever, RetrievedChunk
from .hybrid import HybridRetriever
from .omnigraph import OmnigraphRetriever

__all__ = ["BaseRetriever", "RetrievedChunk", "HybridRetriever", "OmnigraphRetriever"]
