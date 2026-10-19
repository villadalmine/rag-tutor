"""Script de Ingesta y Construcción del Grafo de Conocimiento (Fase 2: GraphRAG / Omnigraph)."""

import sys
from pathlib import Path

# Configurar encoding UTF-8 en consola de Windows
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
    """Construye la ontología estructural de Platform Engineering, AI Agents y LLMs."""
    kg = KnowledgeGraph()

    # =========================================================================
    # 1. Nodos: Conceptos de Platform Engineering (Effective Platform Engineering)
    # =========================================================================
    nodes_data = [
        # Platform Engineering
        GraphNode(
            id="platform-engineering",
            label="Discipline",
            name="Platform Engineering",
            description="Disciplina de diseñar y construir toolchains y flujos de trabajo que habilitan el autoservicio para desarrolladores.",
        ),
        GraphNode(
            id="internal-developer-platform",
            label="System",
            name="Internal Developer Platform (IDP)",
            description="Capa unificada de herramientas e infraestructura que reduce la carga cognitiva de los equipos de ingeniería.",
        ),
        GraphNode(
            id="paved-roads",
            label="Pattern",
            name="Paved Roads (Golden Paths)",
            description="Caminos dorados y plantillas estandarizadas recomendadas para acelerar el desarrollo con seguridad integrada.",
        ),
        GraphNode(
            id="self-service",
            label="Principle",
            name="Self-Service",
            description="Autonomía de los equipos para aprovisionar y operar servicios sin tickets manuales entre áreas.",
        ),
        GraphNode(
            id="platform-as-a-product",
            label="Principle",
            name="Platform as a Product",
            description="Gestionar la plataforma como un producto con usuarios internos, métricas de adopción y feedback continuo.",
        ),
        GraphNode(
            id="domain-driven-design",
            label="Methodology",
            name="Domain-Driven Design (DDD)",
            description="Alineación del diseño de plataformas con los límites de contexto y dominios del negocio.",
        ),
        # AI Agents & Frameworks (AI Agents and Applications & HF in Action)
        GraphNode(
            id="ai-agent",
            label="Architecture",
            name="AI Agent",
            description="Entidad autónoma basada en LLM capaz de razonar, planificar y utilizar herramientas externas.",
        ),
        GraphNode(
            id="react-pattern",
            label="Pattern",
            name="ReAct Pattern",
            description="Ciclo interactivo de Razonamiento y Acción (Thought, Action, Observation) para resolver tareas complejas.",
        ),
        GraphNode(
            id="langgraph",
            label="Framework",
            name="LangGraph",
            description="Framework para coordinar agentes cíclicos y con estado usando grafos dirigidos.",
        ),
        GraphNode(
            id="tools-and-function-calling",
            label="Component",
            name="Tools & Function Calling",
            description="Capacidad del LLM para invocar funciones tipadas y comunicarse con sistemas externos.",
        ),
        GraphNode(
            id="langsmith",
            label="Tool",
            name="LangSmith",
            description="Plataforma de observabilidad, evaluación y depuración de llamadas y trazas de agentes.",
        ),
        # LLMs in Production
        GraphNode(
            id="rag",
            label="Architecture",
            name="RAG (Retrieval-Augmented Generation)",
            description="Técnica que combina recuperación de documentos en bases vectoriales con generación condicionada en LLMs.",
        ),
        GraphNode(
            id="fine-tuning",
            label="Methodology",
            name="Fine-Tuning",
            description="Adaptación de los pesos de un modelo preentrenado a un estilo, tarea o terminología específica.",
        ),
        GraphNode(
            id="lora",
            label="Technique",
            name="LoRA (Low-Rank Adaptation)",
            description="Afinamiento eficiente de parámetros (PEFT) congelando el modelo base y entrenando matrices de bajo rango.",
        ),
        GraphNode(
            id="vector-store",
            label="Component",
            name="Vector Store (ChromaDB)",
            description="Almacenamiento y búsqueda de similitud por embeddings de texto de alta dimensionalidad.",
        ),
        GraphNode(
            id="reranker",
            label="Component",
            name="Reranker (Cross-Encoder)",
            description="Modelo secundario que reordena los candidatos recuperados computando atención cruzada query-documento.",
        ),
    ]

    for n in nodes_data:
        kg.add_node(n)

    # =========================================================================
    # 2. Aristas: Relaciones Ontológicas y Dependencias Técnicas
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
        # Cross-Domain relations (Agentes en Plataforma y LLMs en Plataforma)
        GraphEdge(source="ai-agent", target="rag", relation="LEVERAGES_KNOWLEDGE_VIA"),
        GraphEdge(source="platform-engineering", target="rag", relation="OPERATES"),
        GraphEdge(source="ai-agent", target="internal-developer-platform", relation="AUTOMATES_TASKS_ON"),
    ]

    for e in edges_data:
        kg.add_edge(e)

    return kg


def run_graph_ingestion():
    """Genera y persiste el grafo de conocimiento para Fase 2."""
    print("=" * 65)
    print(" 🕸️  Iniciando Ingesta de Grafo Ontológico (Fase 2: GraphRAG)")
    print("=" * 65)

    kg = build_platform_knowledge_graph()
    kg.save(config.GRAPH_DATA_PATH)

    print(f"\n[OK] Grafo de conocimiento generado y persistido en:")
    print(f"     {config.GRAPH_DATA_PATH}")
    print(f"[+] Total de Entidades (Nodos): {len(kg.nodes)}")
    print(f"[+] Total de Relaciones (Aristas): {len(kg.edges)}")
    print("\n[+] Resumen de Entidades Principales:")
    for n in list(kg.nodes.values())[:8]:
        print(f"    • [{n.label}] {n.name}: {n.description[:60]}...")

    print("\n" + "=" * 65)
    print(" ¡Fase 2 (GraphRAG / Omnigraph) lista!")
    print(" Para activar la búsqueda de grafos por defecto, define:")
    print("   $env:RETRIEVER_TYPE = 'omnigraph'")
    print("=" * 65)


if __name__ == "__main__":
    run_graph_ingestion()
