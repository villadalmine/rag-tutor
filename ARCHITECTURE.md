# Architecture & Roadmap: Universal Technical RAG Tutor

> **Architecture Decision Records (ADRs) and Iterative Evolution Plan**  
> **Start Date:** October 2026  
> **Workspace:** `rag-tutor`  
> **Target Hardware:** Local workstation (Dual Xeon, 256 GB RAM, local Ollama / vLLM inference).

---

## 1. Context and Problem Statement

The goal of this project is to build an **Agnostic, Sovereign Local AI Tutor** specialized in technical books (covering **Software Engineering**, **Kubernetes Internals**, **Go Operators**, **Crossplane**, **Service Meshes**, **Databases**, and **Cloud-Native Architectures**).

### Technical Challenges Identified:
1. **Shortcomings of Naive Vector RAG:**
   - Standard dense vector embeddings (`all-MiniLM-L6-v2`, `bge-base`, etc.) capture broad conceptual meaning well, but suffer critical degradation with exact syntax: Custom Resource Definition names (`kind: CompositeResourceDefinition`), `kubectl`/`kubebuilder` flags, indentation-sensitive YAML, or Go function signatures.
2. **Loss of Architectural Context (Fragmented Chunking):**
   - Naive character-count splitters (e.g. slicing PDFs every 1000 characters) sever code blocks and disconnect relationships between distributed components (e.g., how a Custom Controller watches a resource and validates via an Admission Webhook).
3. **Dual Consumption Needs:**
   - The tutor must serve both human interactive workflows (Web UI / Open WebUI via REST API) and AI agent workflows natively in the terminal via the **Model Context Protocol (MCP)** (for clients like Claude Desktop, Goose CLI, or Antigravity).

---

## 2. Design Decision: Two-Phase Iterative Roadmap

To balance **immediate operational value without early over-engineering (*no overkill*)** against the long-term necessity of **formal knowledge graphs**, we adopted a two-phase architecture.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  ITERATIVE ROADMAP                                     │
│                                                                                        │
│   PHASE 1: Operational Foundation (Current)     PHASE 2: GraphRAG Evolution            │
│   ┌───────────────────────────────────┐         ┌───────────────────────────────────┐  │
│   │ • Hybrid RAG (Chroma + BM25)      │         │ • Omnigraph (Lance Lakehouse)     │  │
│   │ • Local Cross-Encoder Reranker    │  ────►  │ • Ontological Platform Schema     │  │
│   │ • Lightweight Agentic Loop (Py)   │         │ • Git-Style Context Branching     │  │
│   │ • FastMCP + FastAPI Exposure      │         │ • Native Omnigraph MCP Server     │  │
│   └───────────────────────────────────┘         └───────────────────────────────────┘  │
│                     ▲                                             ▲                    │
│                     └───────────────────┬─────────────────────────┘                    │
│                                         │                                              │
│                            BaseRetriever Abstraction Layer                             │
│                           (Switch engines without rewrites)                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: Operational Foundation & Agentic Hybrid RAG (Current State)

Phase 1 delivers a 100% self-contained, offline Python stack running locally without requiring heavy external graph databases:

### Core Components:
1. **Ingestion & Code-Preserving Chunking (`src/ingest.py`):**
   - High-speed text and layout extraction via `PyMuPDFLoader`.
   - Syntax-aware chunking using `RecursiveCharacterTextSplitter` with hierarchical code separators: `["\n## ", "\n### ", "\n```yaml", "\n```go", "\n```", "\n\n", "\n"]`.
   - Chunk size: 400-600 tokens with 100-token overlap, preserving semantic blocks intact.
2. **Hybrid Retrieval Engine (`src/retrievers/hybrid.py`):**
   - **Vector Store:** Persistent ChromaDB at `./chroma_db` with local Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
   - **Lexical Search:** Inverted index with BM25 Okapi (`rank_bm25`) for exact token matching of CRDs, functions, and commands.
   - **Reranker:** Local Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) scoring the top 12 candidate pairs to deliver the top 4 pure chunks.
3. **Controlled Agentic Reflection Loop (`src/core.py`):**
   - Rather than introducing heavy external agent frameworks, `AgenticTutorCore` executes a focused self-reflection cycle (max 2 steps):
     1. *Step A (Candidate Retrieval):* Retrieves the initial pool of candidate documents.
     2. *Step B (Sufficiency Evaluation):* The LLM assesses whether code, YAML, and theory are sufficient. If gaps exist, it generates a targeted sub-query (`NECESITO_MAS_INFO: [sub-query]`).
     3. *Step C (Consolidation):* Synthesizes the final answer strictly grounded in the books with verified page citations.
4. **Dual Interface Exposure:**
   - **FastMCP (`src/mcp_server.py`):** Exposes `consultar_libros_manning` and `buscar_codigo_yaml` tools over standard stdio JSON-RPC.
   - **FastAPI (`src/api.py`):** Exposes `POST /chat` and `GET /health` with Swagger UI for Open WebUI and HTTP clients.

---

## 4. Phase 2: GraphRAG Evolution via Omnigraph (`ModernRelay/omnigraph`)

### Why Omnigraph?
[Omnigraph](https://github.com/ModernRelay/omnigraph) is a lakehouse-native graph database built on the **Lance** columnar format:
- **Unified Graph + Vectors:** Bridges the divide between dense vector similarity and discrete dependency graphs.
- **Git-Style Branching:** Agents can branch graph state to explore architectural hypotheses without mutating the ground truth.
- **Platform Ontology:** Maps technical books into directed dependency graphs:
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

### Implementation Details in the Codebase:
1. **`BaseRetriever` Abstraction (`src/retrievers/base.py`):**
   - `AgenticTutorCore` only depends on the unified `BaseRetriever` interface.
2. **Dual `OmnigraphRetriever` Connector (`src/retrievers/omnigraph.py`):**
   - **Remote Mode (Omnigraph Daemon):** If a local or containerized Omnigraph instance is active at `http://localhost:8080`, queries its GraphQL/REST API.
   - **Local Integrated Mode (In-Memory GraphRAG):** When running without an external daemon, automatically loads `knowledge_graph.json` and performs multi-hop BFS relationship traversal in memory.
3. **Ontological Ingestion Pipeline (`src/ingest_graph.py`):**
   - Maps 16 key technical entities and 16 directed relationships covering Platform Engineering, AI Agents (LangGraph, ReAct), and MLOps.
4. **Containerized Deployment (`docker-compose.yml`):**
   - Ready to run `ghcr.io/modernrelay/omnigraph:latest` for scaled graph lakehouse persistence.

---

## 5. Architectural Trade-offs & Decisions

| Criterion | Phase 1 (Chroma + BM25 + Python Loop) | Phase 2 (Omnigraph GraphRAG) |
| :--- | :--- | :--- |
| **Deployment Complexity** | **Minimal:** 100% native Python, local disk directories. | **Moderate:** Requires Omnigraph service and schema maintenance. |
| **Time to First Query** | Instant (minutes after placing PDFs). | Follows volume and query complexity validation. |
| **Exact Syntax Search (Code/YAML)** | Excellent (BM25 + Cross-Encoder). | Outstanding (Multimodal indexing + graph attributes). |
| **Architectural Dependencies** | Resolved in 2 steps via the Agentic Loop. | Natively encoded in the graph topology. |
| **Agentic Branching** | Unavailable (static). | Natively available (Git-style branching). |
| **Infrastructure Overhead** | **Zero:** no background services required. | Lightweight daemon service. |

---

## 6. Architecture Decision Record: Universal Deterministic Metadata Engine (Zero-Config)

### Context & Problem
Scaling the technical library across dozens of heterogeneous sources (over 23,000 chunks) introduces two major risks to naive vector search:
1. **Semantic Dilution from Polysemous Terms:** Words like *"pipeline"*, *"controller"*, or *"cluster"* carry radically different meanings in Kubernetes, MLOps, Event Streaming, and Databases.
2. **Code Blindness:** Dense embeddings struggle to differentiate executable syntax (YAML, Go, SQL, Rust) from theoretical commentary.

### Design Decision: Two-Level Deterministic Cascade
Rather than relying on LLMs for chunk-level tagging (slow, non-deterministic, and costly), we implement a deterministic engine:
1. **Macro Level (Document):** Automatic lexical profiling reads the first pages of each PDF (TOC and preface) to assign domain tags (`cloud_native`, `ai_agents`, `mlops`, `databases_and_storage`, `systems_programming`, `web_and_frontend`, `devsecops`, etc.) and persists them in `metadata_registry.json`.
2. **Micro Level (Chunk):** Pure regex syntax detection categorizes code blocks (`has_code`, `code_lang: yaml|go|python|sql|rust|bash|typescript`, `is_heading`).
3. **Fallback Mechanism:** Unrecognized books receive the universal fallback domain `general_technical` with auto-extracted TF-IDF keywords.

### Operational Impact
- **HNSW Pre-Filtering:** ChromaDB performs scalar metadata pre-filtering before calculating Euclidean distances, reducing the vector search space from 23k+ to < 5k chunks in < 5 ms.
- **Phase 2 Bridge:** Domain and tag metadata directly map into node attributes and edge properties within Omnigraph / KùzuDB.
- Consult the full specification in [METADATA_SYSTEM.md](METADATA_SYSTEM.md).

---

## 7. Strategic Value & Use Cases for AI Platform / Kubernetes Engineers

For an **AI Platform & Kubernetes Infrastructure Engineer**, `rag-tutor` solves two complementary problems:

### A. Drastic Token & Rate-Limit Savings on Paid Cloud Subscriptions (Claude Pro/Code, GitHub Copilot, Cursor, OpenAI)
- **The Problem:** Feeding 5–10 technical books (or long chapters on vLLM, Ray, KubeRay, MCP, or Kubernetes Operators) into a cloud agent burns **50,000 to 200,000 tokens per turn**, exhausting 5-hour subscription quotas in a few prompts and suffering from "lost-in-the-middle" context degradation.
- **The Solution (`WHERE`-Filtered MCP):**
  1. The agent calls `listar_libros_y_secciones(domain="cloud_native", min_year=2025)` (**~250 tokens**).
  2. The agent calls `buscar_fragmentos_secciones(consulta="vLLM GPU scheduling", min_year=2025, domain="cloud_native", tag="kubernetes", top_k=3)` (**~800 tokens**).
  3. **Result:** Over **95% reduction in token consumption**, zero deprecated pre-2024 APIs, and surgical answers grounded in your latest 2025/2026 technical reference library.

### B. Sovereign Local Execution on Apple Silicon (Mac ARM M-Series) or Local GPU with Small 7B/12B Models
- **Why 7B/12B Models Fail Alone:** A local 7B–14B model (`qwen2.5:7b`, `qwen2.5-coder:14b`, `llama3.1:8b`) running on a MacBook Pro (Apple Silicon Unified Memory) or Linux GPU has limited parametric memory for bleeding-edge specs (e.g., Kubernetes DRA, LeaderWorkerSet, Gateway API Inference Extension, MCP protocol schemas, or KubeRay CRDs) and will hallucinate YAML fields if asked from memory.
- **Why 7B/12B Models Excel with `rag-tutor`:** Small models are **exceptionally good at reading comprehension, synthesis, and code adaptation** when given the exact reference chunk in their prompt. Because `rag-tutor` runs embeddings (`all-MiniLM-L6-v2`, ~90 MB), Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`, ~90 MB), BM25, and KùzuDB locally in **< 300 ms on CPU/ARM**, it feeds the 7B/12B model the exact verified YAML and architecture section—turning a lightweight local model on your Mac ARM into a senior AI Platform Architect with **zero cloud cost and 100% data privacy**.
- **High-Value Day-to-Day Use Cases (AI Platform on K8s):**
  1. **Designing & Debugging LLM Serving on K8s:** vLLM, TGI, Triton, KServe, and Ray/KubeRay manifests with GPU topology, MIG, time-slicing, and DRA (`--domain cloud_native --tag gpu --min-year 2025`).
  2. **Building & Auditing MCP Servers and Multi-Agent Systems:** Grounding LangGraph, CrewAI, and Model Context Protocol (MCP) security, auth, and tool schemas (`--domain ai_agents --tag mcp --min-year 2025`).
  3. **RAG & Knowledge Graph Pipelines in Production:** Comparing vector indexing, chunking strategies, hybrid reranking, and GraphRAG patterns (`--domain mlops --tag rag --min-year 2025`).
  4. **Offline / CI Automated Verification (`--no-llm`):** Extracting canonical YAML manifests and architectural checklists directly from the CLI without running any LLM at all.

---

## 8. ADR: Local Small LLMs (7B/12B on CPU/GPU/Mac ARM) vs. Frontier "Thinking" LLMs via MCP

When operating `rag-tutor`, the retrieval layer (`ChromaDB` + `BM25` + `Cross-Encoder` + `KùzuDB`) is **100% local and deterministic**. However, the synthesis and reasoning layer can be served by either a **Small Local LLM (7B–12B)** or a **Frontier "Thinking" LLM (Claude 3.7/4 Sonnet/Opus, o3, GPT-5)** connected via MCP:

1. **Why Local 7B/12B Models Are Ideal for Fact Extraction & Daily Execution ($0 Cost):**
   - When `rag-tutor` pre-filters 20+ books by `min_year=2025`, `domain`, and `tag` and delivers the top 3 reranked chunks (~900 tokens), a 7B/12B model does not need to rely on its compressed parametric weights. It excels at **reading comprehension, command extraction, and boilerplate adaptation** completely offline.
2. **Why Frontier "Thinking" LLMs + `rag-tutor` MCP Excel at Complex System Architecture & Critical Opinions:**
   - Asking an LLM to *"design a multi-tenant Kubernetes AI platform with eBPF network isolation and microVM sandboxes for MCP coding agents, and critique the trade-offs"* requires **multi-hop constraint satisfaction and test-time compute (Chain-of-Thought)**.
   - Without `rag-tutor` MCP, a cloud Thinking LLM either relies on stale pre-2024 training weights or burns 150,000+ tokens reading raw books.
   - Connected to `rag-tutor` MCP (`buscar_fragmentos_secciones` + `consultar_grafo_kuzu`), the Thinking LLM consumes only **~1,100 tokens** of verified 2025–2026 reference architecture and dedicates its full reasoning budget to **evaluating trade-offs, failure modes, and security boundaries** (see full case study and diagrams in [STRATEGIC_GUIDE_AND_USAGE.md](STRATEGIC_GUIDE_AND_USAGE.md)).
