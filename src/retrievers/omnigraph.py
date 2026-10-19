"""Fase 2: Conector para ModernRelay Omnigraph (Lakehouse Graph + Lance Vector).

Este módulo implementa la interfaz BaseRetriever conectándose a una instancia
de Omnigraph (https://github.com/ModernRelay/omnigraph) para realizar recorridos
de grafo ontológico (Graph Traversal) combinados con búsqueda vectorial sobre Lance.
"""

from typing import List, Optional
import requests

from src import config
from .base import BaseRetriever, RetrievedChunk


class OmnigraphRetriever(BaseRetriever):
    """Recuperador ontológico y vectorial basado en Omnigraph.

    En Fase 2, los libros de Manning se indexan como un grafo de dependencias
    (nodos: CRD, Controller, Reconciler, Webhook, Compositions) y aristas de
    relación semántica.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        branch: Optional[str] = None,
    ):
        self.api_url = (api_url or config.OMNIGRAPH_API_URL).rstrip("/")
        self.branch = branch or config.OMNIGRAPH_BRANCH

    def check_connection(self) -> bool:
        """Verifica si el servicio local de Omnigraph está activo."""
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Consulta el grafo de conocimiento y vectores en Omnigraph.

        Ejecuta una consulta híbrida multimodal (Graph traversal + Lance ANN).
        """
        if not self.check_connection():
            print(
                f"[Aviso Omnigraph] No se pudo conectar a Omnigraph en {self.api_url}. "
                "Asegúrate de tener el daemon o contenedor de Omnigraph corriendo (Fase 2). "
                "Para usar el motor local de Fase 1, configura RETRIEVER_TYPE='hybrid'."
            )
            return []

        endpoint = f"{self.api_url}/api/v1/graphs/query"
        payload = {
            "branch": self.branch,
            "query": query,
            "top_k": top_k,
            "include_relations": True,
        }

        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            results: List[RetrievedChunk] = []
            for item in data.get("nodes", []):
                results.append(
                    RetrievedChunk(
                        content=item.get("content", ""),
                        source=item.get("properties", {}).get("source", "Omnigraph Graph"),
                        page=item.get("properties", {}).get("page"),
                        score=item.get("score", 1.0),
                        metadata=item.get("properties", {}),
                    )
                )
            return results
        except Exception as e:
            print(f"[Error consultando Omnigraph]: {e}")
            return []
