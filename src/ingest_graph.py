"""Knowledge Graph Ingestion & Construction Script (Phase 2: GraphRAG / Omnigraph).

This script builds a seed ontology for Platform Engineering, AI Agents, and LLMs.
NOTE: This file provides a structural template. Users can adapt or replace these entities
and relations according to their own technical books and domain needs.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Configure UTF-8 encoding on Windows console
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.graph_schema import GraphEdge, GraphNode, KnowledgeGraph
from src.kuzu_graph import KuzuGraphEngine


def build_platform_knowledge_graph() -> KnowledgeGraph:
    """Builds the structural ontology for Platform Engineering, AI Agents, and LLMs."""
    kg = KnowledgeGraph()

    # =========================================================================
    # 1. Nodes: Platform Engineering Concepts
    # =========================================================================
    nodes_data = [
        # Platform Engineering
        GraphNode(
            id="platform-engineering",
            label="Discipline",
            name="Platform Engineering",
            description="Discipline of designing and building toolchains and workflows that enable self-service capabilities for software engineering organizations.",
        ),
        GraphNode(
            id="internal-developer-platform",
            label="System",
            name="Internal Developer Platform (IDP)",
            description="Unified layer of tools and infrastructure that reduces developer cognitive load across engineering teams.",
        ),
        GraphNode(
            id="paved-roads",
            label="Pattern",
            name="Paved Roads (Golden Paths)",
            description="Standardized, recommended Golden Paths and templates to accelerate development with built-in security.",
        ),
        GraphNode(
            id="self-service",
            label="Principle",
            name="Self-Service",
            description="Team autonomy to provision and operate services without manual inter-departmental ticket queues.",
        ),
        GraphNode(
            id="platform-as-a-product",
            label="Principle",
            name="Platform as a Product",
            description="Managing internal platforms as products with developer user feedback, adoption metrics, and continuous iteration.",
        ),
        GraphNode(
            id="domain-driven-design",
            label="Methodology",
            name="Domain-Driven Design (DDD)",
            description="Alignment of platform boundaries and service APIs with bounded business domains.",
        ),
        # AI Agents & Frameworks
        GraphNode(
            id="ai-agent",
            label="Architecture",
            name="AI Agent",
            description="Autonomous LLM-driven architecture capable of reasoning, planning, and executing tools.",
        ),
        GraphNode(
            id="react-pattern",
            label="Pattern",
            name="ReAct Pattern",
            description="Interactive Reasoning and Action (Thought, Action, Observation) loop for complex problem-solving.",
        ),
        GraphNode(
            id="langgraph",
            label="Framework",
            name="LangGraph",
            description="Orchestration framework for building stateful, multi-agent cyclical workflows using directed graphs.",
        ),
        GraphNode(
            id="tools-and-function-calling",
            label="Component",
            name="Tools & Function Calling",
            description="Model capability to trigger typed function executions and interact with external systems.",
        ),
        GraphNode(
            id="langsmith",
            label="Tool",
            name="LangSmith",
            description="Observability, debugging, and tracing platform for agent execution runs.",
        ),
        # LLMs in Production
        GraphNode(
            id="rag",
            label="Architecture",
            name="RAG (Retrieval-Augmented Generation)",
            description="Retrieval-Augmented Generation architecture combining external vector/lexical retrieval with LLM generation.",
        ),
        GraphNode(
            id="fine-tuning",
            label="Methodology",
            name="Fine-Tuning",
            description="Supervised adaptation of pre-trained model weights to specialized domains, styles, or tasks.",
        ),
        GraphNode(
            id="lora",
            label="Technique",
            name="LoRA (Low-Rank Adaptation)",
            description="Low-Rank Adaptation technique (PEFT) freezing base weights and training small rank-decomposition matrices.",
        ),
        GraphNode(
            id="vector-store",
            label="Component",
            name="Vector Store (ChromaDB)",
            description="High-dimensional text embedding storage enabling semantic similarity search.",
        ),
        GraphNode(
            id="reranker",
            label="Component",
            name="Reranker (Cross-Encoder)",
            description="Secondary neural cross-encoder scoring query-document attention to reorder retrieved candidates.",
        ),
    ]

    for n in nodes_data:
        kg.add_node(n)

    # =========================================================================
    # 2. Edges: Ontological Relations & Technical Dependencies
    # =========================================================================
    edges_data = [
        # Platform Engineering relations
        GraphEdge(source="platform-engineering", target="internal-developer-platform", relation="DELIVERS"),
        GraphEdge(source="internal-developer-platform", target="self-service", relation="ENABLES"),
        GraphEdge(source="internal-developer-platform", target="paved-roads", relation="PROVIDES"),
        GraphEdge(source="platform-engineering", target="platform-as-a-product", relation="MANAGES_AS"),
        GraphEdge(source="platform-engineering", target="domain-driven-design", relation="APPLIES"),
        # AI Agents relations
        GraphEdge(source="ai-agent", target="react-pattern", relation="IMPLEMENTS"),
        GraphEdge(source="ai-agent", target="tools-and-function-calling", relation="USES"),
        GraphEdge(source="langgraph", target="ai-agent", relation="BUILDS"),
        GraphEdge(source="ai-agent", target="langsmith", relation="MONITORED_BY"),
        # LLM Architecture relations
        GraphEdge(source="fine-tuning", target="rag", relation="COMPARES_WITH"),
        GraphEdge(source="fine-tuning", target="lora", relation="OPTIMIZED_BY"),
        GraphEdge(source="rag", target="vector-store", relation="RETRIEVES_FROM"),
        GraphEdge(source="rag", target="reranker", relation="REORDERED_BY"),
        # Cross-Domain relations (Agents in Platforms & LLMs in Platforms)
        GraphEdge(source="ai-agent", target="rag", relation="LEVERAGES_KNOWLEDGE_VIA"),
        GraphEdge(source="platform-engineering", target="rag", relation="OPERATES"),
        GraphEdge(source="ai-agent", target="internal-developer-platform", relation="AUTOMATES_TASKS_ON"),
    ]

    for e in edges_data:
        kg.add_edge(e)

    return kg


def enrich_graph_from_corpus(
    kg: KnowledgeGraph,
    corpus: List[Dict[str, Any]],
    catalog: Dict[str, Any],
) -> KnowledgeGraph:
    """Dynamically enriches the ontological graph with real indexed books, domains, and concepts."""
    # 1. Create nodes for each book and its domain
    for book_name, meta in catalog.items():
        book_id = "book-" + re.sub(r"[^a-z0-9]+", "-", book_name.lower()).strip("-")[:50]
        domain = meta.get("domain", "general_technical")
        domain_id = "domain-" + domain.replace("_", "-")
        tags = meta.get("tags", [])

        if domain_id not in kg.nodes:
            kg.add_node(
                GraphNode(
                    id=domain_id,
                    label="Discipline",
                    name=domain.replace("_", " ").title(),
                    description=f"Technical engineering domain: {domain}",
                )
            )

        kg.add_node(
            GraphNode(
                id=book_id,
                label="Book",
                name=book_name,
                description=f"Technical reference book in domain '{domain}' covering {', '.join(tags)}.",
                properties={"domain": domain, "tags": tags},
            )
        )
        kg.add_edge(GraphEdge(source=book_id, target=domain_id, relation="BELONGS_TO_DOMAIN"))

        for tag in tags:
            tag_id = re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
            if not tag_id:
                continue
            if tag_id not in kg.nodes:
                kg.add_node(
                    GraphNode(
                        id=tag_id,
                        label="Concept",
                        name=tag.replace("_", " ").title(),
                        description=f"Core technical concept extracted from {book_name}.",
                    )
                )
            kg.add_edge(GraphEdge(source=book_id, target=tag_id, relation="COVERS_CONCEPT"))

    # 2. Link real chunks to graph nodes when they mention the concept
    existing_edges = {(e.source, e.target, e.relation) for e in kg.edges}
    for idx, item in enumerate(corpus):
        content_lower = item.get("content", "").lower()
        source_book = item.get("source", "")
        book_id = "book-" + re.sub(r"[^a-z0-9]+", "-", source_book.lower()).strip("-")[:50]
        chunk_id = f"chunk-{idx}"

        for node_id, node in list(kg.nodes.items()):
            if node.label == "Book":
                continue
            if node.name.lower() in content_lower or node_id.replace("-", " ") in content_lower:
                if len(node.chunk_ids) < 25 and chunk_id not in node.chunk_ids:
                    node.chunk_ids.append(chunk_id)
                if book_id in kg.nodes and (book_id, node_id, "EXPLAINS") not in existing_edges:
                    kg.add_edge(GraphEdge(source=book_id, target=node_id, relation="EXPLAINS"))
                    existing_edges.add((book_id, node_id, "EXPLAINS"))

    return kg


def sync_graph_and_kuzu(
    corpus: List[Dict[str, Any]] | None = None,
    catalog: Dict[str, Any] | None = None,
) -> KnowledgeGraph:
    """Builds the ontological graph, enriches it with the real corpus, saves JSON, and syncs KùzuDB."""
    kg = build_platform_knowledge_graph()
    if corpus is not None and catalog is not None:
        kg = enrich_graph_from_corpus(kg, corpus, catalog)

    kg.save(config.GRAPH_DATA_PATH)
    kuzu_engine = KuzuGraphEngine()
    if kuzu_engine.available:
        kuzu_engine.sync_from_knowledge_graph(kg, clear_existing=True)
    return kg


def run_graph_ingestion():
    """Generates and persists the knowledge graph for Phase 2."""
    print("=" * 65)
    print(" 🕸️  Starting Ontological Graph Ingestion (Phase 2: GraphRAG)")
    print("=" * 65)

    kg = sync_graph_and_kuzu()

    print(f"\n[OK] Knowledge graph generated and saved at:")
    print(f"     {config.GRAPH_DATA_PATH}")
    print(f"[+] Total Entities (Nodes): {len(kg.nodes)}")
    print(f"[+] Total Relationships (Edges): {len(kg.edges)}")
    print("\n[+] Summary of Primary Entities:")
    for n in list(kg.nodes.values())[:8]:
        print(f"    • [{n.label}] {n.name}: {n.description[:60]}...")

    print("\n" + "=" * 65)
    print(" 🎉 Phase 2 (GraphRAG / Omnigraph + KùzuDB) Ready!")
    print(" To activate GraphRAG by default, set:")
    print("   export RETRIEVER_TYPE=omnigraph")
    print("=" * 65)


if __name__ == "__main__":
    run_graph_ingestion()

