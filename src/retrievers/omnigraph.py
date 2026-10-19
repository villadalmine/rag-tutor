"""Phase 2: Ontological & Vector Retriever (Omnigraph & GraphRAG).

Supports two complementary operational modes:
1. Native HTTP / MCP connection to Omnigraph service daemon (if running).
2. Local In-Memory Ontological Graph Engine (executes entity traversal and relation discovery
   using `knowledge_graph.json`, requiring zero external services).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import requests

from src import config
from src.graph_schema import KnowledgeGraph
from src.kuzu_graph import KuzuGraphEngine
from .base import BaseRetriever, RetrievedChunk
from .hybrid import HybridRetriever


class OmnigraphRetriever(BaseRetriever):
    """Phase 2 Ontological Retriever: Unifies graph relationships with vectors and BM25."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        branch: Optional[str] = None,
        graph_path: Optional[Path] = None,
    ):
        self.api_url = (api_url or config.OMNIGRAPH_API_URL).rstrip("/")
        self.branch = branch or config.OMNIGRAPH_BRANCH
        self.graph_path = graph_path or config.GRAPH_DATA_PATH

        # Load local graph engine and hybrid fallback
        self.local_kg = KnowledgeGraph.load(self.graph_path)
        self.hybrid_fallback = HybridRetriever()

        # Embedded KùzuDB Cypher engine with graceful in-memory fallback
        self.kuzu_engine = KuzuGraphEngine()
        if self.kuzu_engine.available and not self.kuzu_engine.is_populated():
            self.kuzu_engine.sync_from_knowledge_graph(self.local_kg)

    def check_connection(self) -> bool:
        """Checks if the remote Omnigraph daemon/container is reachable via HTTP."""
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def _query_remote_omnigraph(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """Queries the remote Omnigraph service (Lance + Graph)."""
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
            print(f"[Omnigraph Remote Warning]: Could not reach daemon ({e}). Falling back to local graph engine.")
            return []

    def _match_entities_in_query(self, query: str) -> List[str]:
        """Detects graph entities mentioned in the query."""
        q_lower = query.lower()
        matched = []
        for node_id, node in self.local_kg.nodes.items():
            if node.name.lower() in q_lower or node_id.replace("-", " ") in q_lower:
                matched.append(node_id)
        return matched

    def _traverse_local_graph(self, matched_nodes: List[str]) -> Dict[str, Any]:
        """Traverses dependencies and relationships of matched concepts using KùzuDB (Cypher) or BFS."""
        related_nodes: Set[str] = set()
        relations_summary: List[str] = []

        # 1. Try declarative Cypher query via KùzuDB
        if self.kuzu_engine.available and self.kuzu_engine.is_populated():
            for n_id in matched_nodes:
                related_nodes.add(n_id)
                rows = self.kuzu_engine.get_related_concepts(n_id)
                for r in rows:
                    related_nodes.add(r["src_id"])
                    related_nodes.add(r["tgt_id"])
                    rel_str = f"({r['src_name']}) ──[{r['relation']}]──► ({r['tgt_name']})"
                    if rel_str not in relations_summary:
                        relations_summary.append(rel_str)
            if relations_summary:
                return {
                    "node_ids": list(related_nodes),
                    "relations": relations_summary[:6],
                }

        # 2. Fallback to in-memory BFS on KnowledgeGraph
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
        """Executes Phase 2 retrieval (Graph Ontology + Vector / Lexical Search)."""
        # 1. If Omnigraph daemon is running, prioritize remote query
        if self.check_connection():
            remote_results = self._query_remote_omnigraph(query, top_k)
            if remote_results:
                return remote_results

        # 2. Local Graph Engine (In-Memory GraphRAG)
        base_chunks = self.hybrid_fallback.retrieve(query, top_k=top_k * 2)
        if not base_chunks:
            return []

        matched_entities = self._match_entities_in_query(query)
        if not matched_entities or not self.local_kg.nodes:
            # If no specific graph concepts match, return top hybrid candidates
            return base_chunks[:top_k]

        graph_context = self._traverse_local_graph(matched_entities)
        related_node_ids = set(graph_context["node_ids"])

        # Prioritize chunks mentioning related concepts discovered via graph traversal
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

        # Inject architectural topology into the top chunk if graph relations were discovered
        if graph_context["relations"] and final_chunks:
            topo_header = (
                "[Related Architecture Topology in Knowledge Graph]:\n"
                + "\n".join(f"  • {rel}" for rel in graph_context["relations"])
                + "\n\n"
            )
            final_chunks[0].content = topo_header + final_chunks[0].content

        return final_chunks

