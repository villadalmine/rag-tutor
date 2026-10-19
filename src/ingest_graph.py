"""Knowledge Graph Ingestion & Construction Script (Phase 2: GraphRAG / Omnigraph).

This script builds a seed ontology for Platform Engineering, AI Agents, and LLMs.
NOTE: This file provides a structural template. Users can adapt or replace these entities
and relations according to their own technical books and domain needs.
"""

import sys
from pathlib import Path

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


def run_graph_ingestion():
    """Generates and persists the knowledge graph for Phase 2."""
    print("=" * 65)
    print(" 🕸️  Starting Ontological Graph Ingestion (Phase 2: GraphRAG)")
    print("=" * 65)

    kg = build_platform_knowledge_graph()
    kg.save(config.GRAPH_DATA_PATH)

    print(f"\n[OK] Knowledge graph generated and saved at:")
    print(f"     {config.GRAPH_DATA_PATH}")
    print(f"[+] Total Entities (Nodes): {len(kg.nodes)}")
    print(f"[+] Total Relationships (Edges): {len(kg.edges)}")
    print("\n[+] Summary of Primary Entities:")
    for n in list(kg.nodes.values())[:8]:
        print(f"    • [{n.label}] {n.name}: {n.description[:60]}...")

    print("\n" + "=" * 65)
    print(" 🎉 Phase 2 (GraphRAG / Omnigraph) Ready!")
    print(" To activate GraphRAG by default, set:")
    print("   $env:RETRIEVER_TYPE = 'omnigraph'")
    print("=" * 65)


if __name__ == "__main__":
    run_graph_ingestion()

