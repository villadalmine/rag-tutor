"""Fase 2: Recuperador Ontológico y Vectorial (Omnigraph & GraphRAG).

Soporta dos modalidades complementarias:
1. Conexión HTTP / MCP nativa con servicio Omnigraph (si está levantado el daemon).
2. Motor de Grafo Ontológico Local (ejecuta traversal de entidades y aristas en memoria
   usando `knowledge_graph.json`, sin requerir servicios externos).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import requests

from src import config
from src.graph_schema import KnowledgeGraph
from .base import BaseRetriever, RetrievedChunk
from .hybrid import HybridRetriever


class OmnigraphRetriever(BaseRetriever):
    """Recuperador ontológico de Fase 2: Une relaciones de grafo con vectores y BM25."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        branch: Optional[str] = None,
        graph_path: Optional[Path] = None,
    ):
        self.api_url = (api_url or config.OMNIGRAPH_API_URL).rstrip("/")
        self.branch = branch or config.OMNIGRAPH_BRANCH
        self.graph_path = graph_path or config.GRAPH_DATA_PATH

        # Cargar motor de grafo local y fallback híbrido
        self.local_kg = KnowledgeGraph.load(self.graph_path)
        self.hybrid_fallback = HybridRetriever()

    def check_connection(self) -> bool:
        """Verifica si el daemon o contenedor de Omnigraph está activo vía HTTP."""
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def _query_remote_omnigraph(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """Consulta el servicio remoto de Omnigraph (Lance + Graph)."""
        endpoint = f"{self.api_url}/api/v1/graphs/query"
        payload = {
            "branch": self.branch,
            "query": query,
            "top_k": top_k,
            "include_relations": True,
        }
        try:
            resp = requests.post(endpoint, json=payload, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            results: List[RetrievedChunk] = []
            for item in data.get("nodes", []):
                results.append(
                    RetrievedChunk(
                        content=item.get("content", ""),
                        source=item.get("properties", {}).get("source", "Omnigraph"),
                        page=item.get("properties", {}).get("page"),
                        score=item.get("score", 1.0),
                        metadata=item.get("properties", {}),
                    )
                )
            return results
        except Exception as e:
            print(f"[Aviso Omnigraph Remoto]: Error al consultar daemon ({e}). Usando motor local.")
            return []

    def _match_entities_in_query(self, query: str) -> List[str]:
        """Detecta entidades del grafo mencionadas en la consulta."""
        q_lower = query.lower()
        matched = []
        for node_id, node in self.local_kg.nodes.items():
            if node.name.lower() in q_lower or node_id.replace("-", " ") in q_lower:
                matched.append(node_id)
        return matched

    def _traverse_local_graph(self, matched_nodes: List[str]) -> Dict[str, Any]:
        """Recorre las dependencias y relaciones de los conceptos encontrados."""
        related_nodes: Set[str] = set()
        relations_summary: List[str] = []

        for n_id in matched_nodes:
            neighbors = self.local_kg.get_neighbors(n_id, max_depth=1)
            related_nodes.update(neighbors)

            for edge in self.local_kg.edges:
                if edge.source == n_id or edge.target == n_id:
                    src_name = self.local_kg.nodes.get(edge.source, None)
                    tgt_name = self.local_kg.nodes.get(edge.target, None)
                    if src_name and tgt_name:
                        relations_summary.append(
                            f"({src_name.name}) ──[{edge.relation}]──► ({tgt_name.name})"
                        )

        return {
            "node_ids": list(related_nodes),
            "relations": relations_summary[:6],
        }

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Ejecuta recuperación de Fase 2 (Ontología de Grafo + Búsqueda Vectorial/Léxica)."""
        # 1. Si el daemon de Omnigraph está corriendo, usarlo prioritariamente
        if self.check_connection():
            remote_results = self._query_remote_omnigraph(query, top_k)
            if remote_results:
                return remote_results

        # 2. Motor de Grafo Local (GraphRAG en memoria)
        base_chunks = self.hybrid_fallback.retrieve(query, top_k=top_k * 2)
        if not base_chunks:
            return []

        matched_entities = self._match_entities_in_query(query)
        if not matched_entities or not self.local_kg.nodes:
            # Si no hay conceptos de grafo específicos, devolver top híbrido
            return base_chunks[:top_k]

        graph_context = self._traverse_local_graph(matched_entities)
        related_node_ids = set(graph_context["node_ids"])

        # Priorizar fragmentos que contengan los conceptos relacionados descubiertos por el grafo
        for chunk in base_chunks:
            content_lower = chunk.content.lower()
            bonus = 0.0
            for r_id in related_node_ids:
                node = self.local_kg.nodes.get(r_id)
                if node and node.name.lower() in content_lower:
                    bonus += 0.25
            chunk.score += bonus

        base_chunks.sort(key=lambda x: x.score, reverse=True)
        final_chunks = base_chunks[:top_k]

        # Si encontramos relaciones en el grafo, enriquecemos el primer fragmento con la topología
        if graph_context["relations"] and final_chunks:
            topo_header = (
                "[Topología de Arquitectura Relacionada en el Grafo]:\n"
                + "\n".join(f"  • {rel}" for rel in graph_context["relations"])
                + "\n\n"
            )
            final_chunks[0].content = topo_header + final_chunks[0].content

        return final_chunks
