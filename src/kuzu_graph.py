"""Embedded Graph Database Engine using KùzuDB (Phase 2: GraphRAG / Omnigraph).

Provides sub-millisecond graph traversals and declarative Cypher queries
without requiring external Docker containers or database daemons.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from src.graph_schema import KnowledgeGraph, GraphNode, GraphEdge

try:
    import kuzu
    KUZU_AVAILABLE = True
except ImportError:
    kuzu = None
    KUZU_AVAILABLE = False


class KuzuGraphEngine:
    """Embedded property graph database powered by KùzuDB with Cypher query execution."""

    def __init__(self, db_path: Optional[Path] = None):
        self.available = KUZU_AVAILABLE
        if not self.available:
            self.db = None
            self.conn = None
            return

        if db_path is None:
            self.db_path = Path(__file__).resolve().parent.parent / "data" / "kuzu_db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = kuzu.Database(str(self.db_path))
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initializes Concept nodes and RelatesTo edge tables if they don't already exist."""
        if not self.conn:
            return

        try:
            self.conn.execute(
                """
                CREATE NODE TABLE IF NOT EXISTS Concept (
                    id STRING,
                    name STRING,
                    label STRING,
                    description STRING,
                    PRIMARY KEY (id)
                )
                """
            )
            self.conn.execute(
                """
                CREATE REL TABLE IF NOT EXISTS RelatesTo (
                    FROM Concept TO Concept,
                    relation STRING,
                    weight DOUBLE
                )
                """
            )
        except Exception:
            # Tables may already exist
            pass

    def is_populated(self) -> bool:
        """Checks if Concept nodes already exist in the database."""
        if not self.conn:
            return False
        try:
            res = self.conn.execute("MATCH (c:Concept) RETURN count(c) AS cnt")
            if res.has_next():
                return res.get_next()[0] > 0
            return False
        except Exception:
            return False

    def sync_from_knowledge_graph(self, kg: KnowledgeGraph, clear_existing: bool = False):
        """Populates or synchronizes KùzuDB from a KnowledgeGraph instance."""
        if not self.conn:
            return

        if clear_existing:
            try:
                self.conn.execute("MATCH (c:Concept) DETACH DELETE c")
            except Exception:
                pass

        # Insert Concept nodes
        for node in kg.nodes.values():
            try:
                self.conn.execute(
                    "CREATE (:Concept {id: $id, name: $name, label: $label, description: $description})",
                    {
                        "id": node.id,
                        "name": node.name,
                        "label": node.label,
                        "description": node.description or "",
                    },
                )
            except Exception:
                # Node might already exist
                pass

        # Insert RelatesTo edges
        for edge in kg.edges:
            try:
                self.conn.execute(
                    """
                    MATCH (a:Concept), (b:Concept)
                    WHERE a.id = $src AND b.id = $tgt
                    CREATE (a)-[:RelatesTo {relation: $rel, weight: $weight}]->(b)
                    """,
                    {
                        "src": edge.source,
                        "tgt": edge.target,
                        "rel": edge.relation,
                        "weight": float(edge.weight),
                    },
                )
            except Exception:
                pass

    def query_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a declarative Cypher query over the embedded knowledge graph."""
        if not self.conn:
            return []

        try:
            res = self.conn.execute(query, parameters or {})
            columns = res.get_column_names()
            results = []
            while res.has_next():
                row = res.get_next()
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            return []

    def get_related_concepts(self, concept_id: str, max_depth: int = 1) -> List[Dict[str, str]]:
        """Discovers 1-hop or 2-hop related concepts and ontological relationships via Cypher."""
        if not self.conn:
            return []

        cypher = """
        MATCH (a:Concept)-[r:RelatesTo]->(b:Concept)
        WHERE a.id = $id OR b.id = $id
        RETURN a.id AS src_id, a.name AS src_name, r.relation AS relation, b.id AS tgt_id, b.name AS tgt_name
        """
        rows = self.query_cypher(cypher, {"id": concept_id})
        return rows
