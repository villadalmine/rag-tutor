# Arquitectura y Roadmap: Manning Platform Engineering Tutor

> **Registro de Decisiones de Arquitectura (ADR) y Plan de Evolución Iterativa**  
> **Fecha de Inicio:** Octubre 2026  
> **Workspace:** `rag-tutor`  
> **Hardware Objetivo:** Estación de trabajo local (Dual Xeon, 256 GB RAM, inferencia local con Ollama / vLLM).

---

## 1. Contexto y Problema

El objetivo del proyecto es construir un **Tutor de Inteligencia Artificial Local** especializado en libros técnicos avanzados de Manning (enfocados en **Ingeniería de Plataformas**, **Kubernetes Internals**, **Operadores en Go**, **Crossplane**, **Service Meshes** y **Arquitecturas Cloud-Native**).

### Desafíos Técnicos Identificados:
1. **Fallas del RAG puramente vectorial:**
   - La búsqueda vectorial estándar (`all-MiniLM-L6-v2`, `bge-base`, etc.) comprende bien conceptos genéricos, pero pierde precisión crítica ante identificadores exactos: nombres de Custom Resource Definitions (`kind: CompositeResourceDefinition`), flags de `kubectl`/`kubebuilder`, sintaxis YAML con indentaciones estrictas o firmas de funciones en Go.
2. **Pérdida de la "visión arquitectónica" (Chunking fragmentado):**
   - Cortar PDFs en trozos fijos de 1000 caracteres rompe bloques de código y desconecta las relaciones entre componentes distribuidos (por ejemplo: cómo un Custom Controller vigila un recurso y se comunica con un webhook de admisión).
3. **Dualidad de consumo:**
   - El tutor debe poder ser consultado tanto interactivamente mediante interfaces Web (API REST / Open WebUI) como de forma integrada en la terminal como herramienta nativa mediante el **Model Context Protocol (MCP)** (para clientes como Goose CLI, Claude Desktop o Antigravity).

---

## 2. Decisión de Diseño: Estrategia de Evolución Iterativa

Para balancear **valor inmediato y funcionalidad práctica sin sobrediseño inicial (*no overkill*)** frente a la necesidad de **grafos de conocimiento complejos**, adoptamos una estrategia en **dos fases iterativas**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ROADMAP ITERATIVO                                    │
│                                                                                        │
│   FASE 1: Fundamento Operativo (Actual)         FASE 2: Evolución GraphRAG             │
│   ┌───────────────────────────────────┐         ┌───────────────────────────────────┐  │
│   │ • RAG Híbrido (Chroma + BM25)     │         │ • Omnigraph (Lance Lakehouse)     │  │
│   │ • Cross-Encoder Reranker local    │  ────►  │ • Mapeo Ontológico de Plataforma  │  │
│   │ • Loop Agéntico liviano (Python)  │         │ • Git-Style Branching de contexto │  │
│   │ • Exposición FastMCP + FastAPI    │         │ • Omnigraph MCP nativo            │  │
│   └───────────────────────────────────┘         └───────────────────────────────────┘  │
│                     ▲                                             ▲                    │
│                     └───────────────────┬─────────────────────────┘                    │
│                                         │                                              │
│                            BaseRetriever Abstraction Layer                             │
│                           (Permite alternar sin reescribir)                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fase 1: Fundamento Operativo y RAG Híbrido Agéntico (Estado Actual)

La Fase 1 implementa un stack 100% autónomo y autocontenido en Python que corre sobre el hardware local sin necesidad de levantar bases de datos de grafos pesadas externas:

### Componentes:
1. **Ingesta y Chunking Técnico (`src/ingest.py`):**
   - Extracción de PDFs con `PyMuPDFLoader`.
   - Chunking adaptado a código y arquitectura mediante `RecursiveCharacterTextSplitter` con jerarquía de separadores: `["\n## ", "\n### ", "\n```", "\n\n", "\n"]`.
   - Tamaño de fragmento: 400-600 tokens con overlap de 100 tokens, preservando bloques sintácticos.
2. **Motor Híbrido de Recuperación (`src/retrievers/hybrid.py`):**
   - **Vector Store:** ChromaDB persistente en `./chroma_db` con embeddings locales HuggingFace (`sentence-transformers/all-MiniLM-L6-v2` o `BAAI/bge-base-en-v1.5`).
   - **Buscador Léxico:** BM25 (`rank_bm25`) para captura exacta de nombres de paquetes, comandos y manifiestos YAML.
   - **Reranker:** Cross-Encoder local (`cross-encoder/ms-marco-MiniLM-L-6-v2` o `BAAI/bge-reranker-base`) para filtrar el top de fragmentos relevantes antes del LLM.
3. **Loop Agéntico Controlado en Python (`src/core.py`):**
   - En lugar de requerir frameworks agénticos pesados, `AgenticTutorCore` ejecuta un ciclo de auto-reflexión de máximo 2 iteraciones:
     1. *Paso A (Búsqueda inicial):* Recupera el primer conjunto de documentos candidatos.
     2. *Paso B (Evaluación de Suficiencia):* El LLM evalúa si el contexto tiene el código, YAML y teoría necesarios. Si detecta vacíos, emite una sub-query técnica refinada (`NECESITO_MAS_INFO: [sub-query]`).
     3. *Paso C (Consolidación):* Sintetiza la respuesta final garantizando fundamentación estricta en los libros.
4. **Exposición Dual:**
   - **FastMCP (`src/mcp_server.py`):** Herramientas `consultar_libros_manning` y `buscar_codigo_yaml` listas para clientes MCP.
   - **FastAPI (`src/api.py`):** Endpoint POST `/chat` para interfaces de usuario y Open WebUI.

---

## 4. Fase 2: Evolución hacia Omnigraph (`ModernRelay/omnigraph`)

### ¿Por qué Omnigraph?
[Omnigraph](https://github.com/ModernRelay/omnigraph) es una base de datos de grafos nativa de lakehouse diseñada sobre el formato columnar **Lance**. Ofrece:
- **Grafo + Vectores Unificados:** Resuelve la separación artificial entre almacenamiento semántico y relaciones de dependencia.
- **Git-Style Branching:** Los agentes pueden ramificar estados del grafo y explorar hipótesis de arquitectura sin afectar el conocimiento base.
- **Ontología de Plataforma:** Permite mapear los libros como grafos dirigidos de conceptos de Kubernetes:
  ```text
  (CustomResourceDefinition) ──[defined_by]──► (Go Struct / Kubebuilder Markers)
              │
         [watched_by]
              ▼
    (CustomController) ──[executes]──► (Reconcile Loop)
              │
         [calls_api]
              ▼
   (Kubernetes API Server) ──[webhook_validated_by]──► (AdmissionWebhook)
  ```

### ¿Cómo se alcanza la Fase 2 sin reescribir el proyecto?
1. **Capa de Abstracción `BaseRetriever` (`src/retrievers/base.py`):**
   - El Core del tutor (`TutorCore`) no interactúa directamente con ChromaDB ni con Omnigraph. Consume la interfaz:
     ```python
     class BaseRetriever(ABC):
         @abstractmethod
         def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
             pass
     ```
2. **Conector `OmnigraphRetriever` (`src/retrievers/omnigraph.py`):**
   - Se conecta al daemon local o contenedor de Omnigraph vía su API HTTP o `@modernrelay/omnigraph-mcp`.
   - Realiza traversal de nodos en el grafo combinado con búsqueda ANN en Lance.
3. **Pipeline de Ingesta Ontológica:**
   - Se añade un script `src/ingest_graph.py` que, además de generar fragmentos de texto, extrae entidades técnicas (CRDs, Controladores, Pipelines, Operadores) y genera las aristas en Omnigraph.

---

## 5. Resumen de Trade-offs y Decisiones

| Criterio | Fase 1 (Chroma + BM25 + Loop Python) | Fase 2 (Omnigraph GraphRAG) |
| :--- | :--- | :--- |
| **Complejidad de Despliegue** | **Mínima:** 100% Python nativo, carpetas locales. | **Media:** Requiere servicio Omnigraph y esquema ontológico. |
| **Tiempo de Puesta en Marcha** | Inmediato (minutos tras colocar PDFs). | Posterior a validar el volumen y tipo de consultas. |
| **Búsqueda Exacta (Código/YAML)** | Excelente (BM25 + Reranker). | Sobresaliente (Indexación multimodal + atributos). |
| **Relaciones Arquitectónicas** | Resueltas en 2 pasos mediante el Agentic Loop. | Mapeadas nativamente en la topología del grafo. |
| **Branching de Agentes** | No disponible (estático). | Disponible de forma nativa (estilo Git). |
| **Sobrecarga de Infraestructura** | **Cero:** sin servicios extra. | Servicio adicional en segundo plano. |

> **Conclusión del Equipo:**  
> Comenzamos desplegando y validando la **Fase 1**. Una vez que los libros estén indexados y hayamos evaluado la calidad de las respuestas en situaciones de alta interconexión arquitectónica, activamos el conector de **Omnigraph** dentro de la abstracción `BaseRetriever`.
