"""Esquema ontológico para el Grafo de Conocimiento (Fase 2: Omnigraph & GraphRAG)."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class GraphNode:
    """Representa una entidad o concepto técnico en el grafo."""

    id: str  # Identificador único normalizado (ej. "platform-engineering", "langgraph")
    label: str  # Tipo de nodo: Concept, Framework, Component, Pattern, Book
    name: str  # Nombre legible (ej. "Platform Engineering", "LangGraph")
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    chunk_ids: List[str] = field(default_factory=list)  # Enlace a fragmentos de texto


@dataclass
class GraphEdge:
    """Representa una relación dirigida entre dos entidades."""

    source: str  # ID del nodo origen
    target: str  # ID del nodo destino
    relation: str  # DEPENDS_ON, IMPLEMENTS, EXPLAINS, COMPARES_WITH, INTEGRATES_WITH
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """Contenedor en memoria del grafo de conocimiento con capacidades de traversal."""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode):
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        if edge.source not in self._adjacency:
            self._adjacency[edge.source] = []
        self._adjacency[edge.source].append(edge)

    def get_neighbors(self, node_id: str, max_depth: int = 1) -> Set[str]:
        """Recorre el grafo en anchura (BFS) para encontrar conceptos conectados."""
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if curr in visited or depth > max_depth:
                continue
            visited.add(curr)

            for edge in self._adjacency.get(curr, []):
                if edge.target not in visited:
                    queue.append((edge.target, depth + 1))

        return visited

    def save(self, filepath: Path):
        """Serializa el grafo a formato JSON."""
        data = {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Path) -> "KnowledgeGraph":
        """Carga el grafo desde JSON."""
        kg = cls()
        if not filepath.exists():
            return kg

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for n_data in data.get("nodes", []):
            kg.add_node(GraphNode(**n_data))

        for e_data in data.get("edges", []):
            kg.add_edge(GraphEdge(**e_data))

        return kg
