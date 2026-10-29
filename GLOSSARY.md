# 📖 Technology Glossary of the Sovereign Tri-MCP Ecosystem

> **Educational Reference Guide for Technical and Non-Technical Readers**  
> This document explains every technology, library, protocol, and retrieval engine used across the ecosystem (**`rag-tutor`**, **`study-cybercirujas`**, and **`k8s-docs-mcp`**).  
> Each concept includes a **simple everyday analogy**, its **formal engineering definition**, the **official upstream link**, and **why it was chosen for this architecture**.

---

## 📑 Table of Contents
1. [Artificial Intelligence, RAG & Reasoning](#1-artificial-intelligence-rag--reasoning)
   - [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
   - [Universal Deterministic Metadata Engine & WHERE Filters](#universal-deterministic-metadata-engine--where-filters)
   - [LLM (Large Language Model)](#llm-large-language-model)
   - [Embeddings (Semantic Vectors)](#embeddings-semantic-vectors)
   - [Cross-Encoder Reranker](#cross-encoder-reranker)
   - [GraphRAG (Graph-Enhanced RAG)](#graphrag-graph-enhanced-rag)
   - [Context Window & KV Cache](#context-window--kv-cache)
2. [Protocols, Connectivity & Integration](#2-protocols-connectivity--integration)
   - [Model Context Protocol (MCP) & Zero-Token-Burn Navigation](#model-context-protocol-mcp--zero-token-burn-navigation)
   - [REST API & OpenAPI / Swagger](#rest-api--openapi--swagger)
   - [FastAPI & Uvicorn](#fastapi--uvicorn)
3. [Databases & Search Engines](#3-databases--search-engines)
   - [ChromaDB](#chromadb)
   - [Rank-BM25](#rank-bm25)
   - [KùzuDB](#kùzudb)
   - [SQLite with FTS5](#sqlite-with-fts5)
4. [Hardware, Local Inference & Sovereignty](#4-hardware-local-inference--sovereignty)
   - [Ollama](#ollama)
   - [Qwen Model Family (Qwen 2.5 / Qwen 3)](#qwen-model-family-qwen-25--qwen-3)
   - [AMD ROCm, Apple Silicon & llama.cpp](#amd-rocm-apple-silicon--llamacpp)
   - [Docker & Process Sandboxing](#docker--process-sandboxing)
5. [Language, Packaging & Documentation Tools](#5-language-packaging--documentation-tools)
   - [uv (Astral)](#uv-astral)
   - [PyMuPDF (fitz)](#pymupdf-fitz)
   - [Pydantic](#pydantic)
   - [Open WebUI](#open-webui)
6. [Maintenance Rules for Developers & AI Agents](#6-maintenance-rules-for-developers--ai-agents)

---

## 1. Artificial Intelligence, RAG & Reasoning

### RAG (Retrieval-Augmented Generation)
- **Everyday Analogy:** Taking an *open-book exam*. Instead of trying to memorize thousands of pages and guessing when unsure, the student first opens the exact chapter and page in the reference textbook and writes the answer with the verified book open on the desk.
- **Technical Definition:** An AI architecture that separates knowledge storage from reasoning: first it retrieves relevant document chunks from local vector/lexical/graph indices (*Retrieval*), and then injects those verified chunks into the prompt (*Generation*).
- **Official Link:** [AWS What is RAG?](https://aws.amazon.com/what-is/retrieval-augmented-generation/) | [Original Paper (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401)
- **Why It Is Used in This Project:** Eliminates hallucinations in critical infrastructure engineering by forcing responses to cite exact source names, publication years, and chapter/page numbers.

---

### Universal Deterministic Metadata Engine & WHERE Filters
- **Everyday Analogy:** A librarian who stamps every incoming book with its **publication year**, **subject category**, **chapter index**, and **programming language** before placing it on the shelf—so when you ask for *"Kubernetes GPU guides from 2025 onward"*, the librarian immediately ignores 2019 books without even opening them.
- **Technical Definition:** A pure-Python lexical and regex profiler ([`src/metadata_engine.py`](src/metadata_engine.py)) that runs in `< 50 ms` per book with zero LLM dependency. It extracts `publication_year`, `domain`, `secondary_domains`, `tags`, `sections` (`H1/H2/H3` hierarchy), and `code_lang` (`yaml`, `go`, `python`, `rust`, `sql`, `bash`), enabling SQL-like `WHERE` pre-filtering across ChromaDB and BM25.
- **Official Link:** [METADATA_SYSTEM.md](METADATA_SYSTEM.md)
- **Why It Is Used in This Project:** Prevents deprecated pre-2024 APIs from polluting answers and reduces MCP context token usage by **95–99%**.

---

### LLM (Large Language Model)
- **Everyday Analogy:** A highly articulate technical writer who can synthesize complex ideas in seconds, or—when using a frontier "Thinking" model—an experienced systems architect who weighs trade-offs across multiple constraints.
- **Technical Definition:** A Transformer neural network trained to predict and reason over token sequences. In `rag-tutor`, the LLM is optional (`--no-llm` mode works without any LLM) and can be either a small local model (`qwen2.5:7b`) or a frontier "Thinking" LLM connected via MCP.
- **Official Link:** [Qwen Official Website](https://qwenlm.github.io/) | [Hugging Face LLM Docs](https://huggingface.co/docs)
- **Why It Is Used in This Project:** Synthesizes retrieved technical chunks into clear explanations or multi-constraint architectural designs.

---

### Embeddings (Semantic Vectors)
- **Everyday Analogy:** Assigning GPS coordinates on a 3D concept map to every paragraph. Phrases like *"the pod crashed due to out-of-memory"* and *"the container was terminated with OOMKilled"* share almost no identical words, yet land on the exact same street corner on the map because their meaning is identical.
- **Technical Definition:** Transforming text into a fixed-length dense numerical vector (384 dimensions via `sentence-transformers/all-MiniLM-L6-v2`) where semantic similarity is computed via cosine similarity.
- **Official Link:** [Sentence-Transformers (SBERT)](https://sbert.net/)
- **Why It Is Used in This Project:** Finds conceptually matching explanations even when the engineer's phrasing differs from the author's terminology.

---

### Cross-Encoder Reranker
- **Everyday Analogy:** A fast recruiter first gathers 15 resumes using keyword filters. Then a senior principal engineer reads those 15 resumes side-by-side with the job description and scores them strictly from -10 to +10 to select only the top 3.
- **Technical Definition:** A neural cross-attention transformer (`cross-encoder/ms-marco-MiniLM-L-6-v2`) that processes `[CLS] Query [SEP] Chunk` jointly across all attention heads, producing a calibrated relevance logit far more accurate than bi-encoder cosine distance alone.
- **Official Link:** [SBERT Cross-Encoder Documentation](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- **Why It Is Used in This Project:** Eliminates context dilution by discarding noisy candidates before they ever reach the LLM or MCP client.

---

### GraphRAG (Graph-Enhanced RAG)
- **Everyday Analogy:** While a normal search engine only finds pages containing your exact words, a detective's corkboard with red strings shows how concepts connect across multiple hops: `(AI Agent) ──[USES]──► (Tools & Function Calling)` and `(cilium-guide) ──[EXPLAINS]──► (Zero Trust)`.
- **Technical Definition:** Combining vector/lexical retrieval with an ontological property graph (`KnowledgeGraph` + `KùzuDB`). Enabled by default via `RETRIEVER_TYPE="omnigraph"`.
- **Official Link:** [Microsoft Research GraphRAG](https://www.microsoft.com/en-us/research/project/graphrag/) | [KùzuDB](https://kuzudb.com/)
- **Why It Is Used in This Project:** Injects architectural topology and multi-book concept relationships directly into retrieved results.

---

### Context Window & KV Cache
- **Everyday Analogy:** The size of the desk where an architect spreads open blueprints. If you dump 20 entire books onto the desk at once, you run out of space (VRAM/RAM) or burn your entire token budget in two questions.
- **Technical Definition:** The maximum token capacity an LLM processes in a single turn, backed by Key-Value (KV) attention matrices cached in memory.
- **Why It Is Used in This Project:** By combining `WHERE` pre-filtering (`min_year`, `domain`, `tag`, `section`) with Cross-Encoder reranking, `rag-tutor` delivers the exact answer in **~1,000 tokens** instead of 150,000+ tokens.

---

## 2. Protocols, Connectivity & Integration

### Model Context Protocol (MCP) & Zero-Token-Burn Navigation
- **Everyday Analogy:** The **universal USB-C port** for AI agents. Any MCP-compatible agent (Claude Desktop, Claude Code, Cursor, Antigravity) can plug directly into `rag-tutor` and call its 5 tools using a single standard protocol.
- **Technical Definition:** An open JSON-RPC 2.0 client-server protocol over Stdio or Streamable HTTP exposing typed `Tools`, `Resources`, and `Prompts`. `rag-tutor` exposes 5 tools in [`src/mcp_server.py`](src/mcp_server.py): `listar_libros_y_secciones`, `buscar_fragmentos_secciones`, `consultar_grafo_kuzu`, `consultar_libros_manning`, and `buscar_codigo_yaml`.
- **Official Link:** [Model Context Protocol Specification](https://modelcontextprotocol.io/) | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- **Why It Is Used in This Project:** Allows external coding agents to inspect the compact catalog first (~300 tokens) and pull only the exact sections needed (~900 tokens).

---

### REST API & OpenAPI / Swagger
- **Everyday Analogy:** An illustrated restaurant menu showing every dish, ingredient, and price clearly so any customer or web app knows how to order.
- **Technical Definition:** HTTP endpoints (`/health`, `/mcp/status`, `/mcp/logs`, `/mcp/test`, `/chat`) formally documented under **OpenAPI 3.0** with interactive **Swagger UI** at `/docs`.
- **Official Link:** [OpenAPI Initiative](https://www.openapis.org/) | [Swagger UI](https://swagger.io/tools/swagger-ui/)
- **Why It Is Used in This Project:** Connects Open WebUI, CI scripts, and external HTTP dashboards to the tutor gateway.

---

### FastAPI & Uvicorn
- **Everyday Analogy:** FastAPI is the high-speed kitchen chef, and Uvicorn is the express conveyor belt delivering orders in milliseconds.
- **Technical Definition:** **FastAPI** is an async Python web framework with automatic Pydantic validation; **Uvicorn** is a lightning-fast ASGI server.
- **Official Link:** [FastAPI Documentation](https://fastapi.tiangolo.com/) | [Uvicorn](https://www.uvicorn.org/)
- **Why It Is Used in This Project:** Powers [`src/api.py`](src/api.py) on port `8000`.

---

## 3. Databases & Search Engines

### ChromaDB
- **Everyday Analogy:** A library organized by **similarity of ideas** rather than alphabetical order, with instant category filters on every shelf.
- **Technical Definition:** An embedded open-source vector database storing HNSW dense vector embeddings and scalar metadata attributes on disk (`chroma_db/`).
- **Official Link:** [ChromaDB Official Site](https://www.trychroma.com/) | [ChromaDB GitHub](https://github.com/chroma-core/chroma)
- **Why It Is Used in This Project:** Provides sub-50ms semantic similarity search with HNSW scalar pre-filtering (`min_year`, `code_lang`).

---

### Rank-BM25
- **Everyday Analogy:** A supercharged `Ctrl + F` that ranks paragraphs by how rare and specific your technical search terms are.
- **Technical Definition:** An implementation of the probabilistic **Okapi BM25** lexical ranking algorithm (`bm25_index.pkl`).
- **Official Link:** [rank_bm25 on PyPI](https://pypi.org/project/rank-bm25/)
- **Why It Is Used in This Project:** Captures exact Kubernetes resource names (`CiliumNetworkPolicy`, `ValidatingAdmissionPolicy`, CLI flags) that dense vector embeddings can blur.

---

### KùzuDB
- **Everyday Analogy:** An embedded graph engine (like SQLite, but for connected networks of concepts) that traces relationships across books and domains in sub-milliseconds.
- **Technical Definition:** An embedded, disk-backed C++ property graph database supporting declarative **Cypher** queries ([`src/kuzu_graph.py`](src/kuzu_graph.py), stored at `data/kuzu_db`).
- **Official Link:** [KùzuDB Official Site](https://kuzudb.com/) | [KùzuDB GitHub](https://github.com/kuzudb/kuzu)
- **Why It Is Used in This Project:** Powers Phase 2 GraphRAG (`OmnigraphRetriever` and the `consultar_grafo_kuzu` MCP tool) without requiring any external Docker containers or database daemons.

---

### SQLite with FTS5
- **Everyday Analogy:** A single-file index card catalog that fits on a thumb drive and locates any word across thousands of official manual pages in milliseconds.
- **Technical Definition:** SQLite's native **Full-Text Search 5 (FTS5)** extension with Porter stemming and BM25 ranking.
- **Official Link:** [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
- **Why It Is Used in This Project:** Used by the sibling **`k8s-docs-mcp`** server to index official `kubernetes.io` documentation and canonical YAML manifests.

---

## 4. Hardware, Local Inference & Sovereignty

### Ollama
- **Everyday Analogy:** Like the VLC media player, but for open-weights AI models—running them locally on your own CPU, GPU, or Mac ARM with a single command.
- **Technical Definition:** A local LLM runtime managing GGUF weights and exposing an inference API on port `11434`.
- **Official Link:** [Ollama Official Website](https://ollama.com/)
- **Why It Is Used in This Project:** Enables 100% offline generative synthesis when paired with `rag-tutor` (while `--no-llm` mode works even without Ollama).

---

### Qwen Model Family (Qwen 2.5 / Qwen 3)
- **Everyday Analogy:** Compact, coding-specialized open-weights models that excel at reading retrieved technical excerpts and synthesizing structured answers.
- **Technical Definition:** Open-weights transformer models (`qwen2.5:7b`, `qwen2.5-coder`, `qwen3:4b`) developed by Alibaba Cloud.
- **Official Link:** [QwenLM on GitHub](https://github.com/QwenLM/Qwen2.5)
- **Why It Is Used in This Project:** Delivers strong YAML/Go/Python comprehension within 5–7 GB of VRAM/RAM.

---

### AMD ROCm, Apple Silicon & llama.cpp
- **Everyday Analogy:** While the CPU is a versatile professor solving tasks sequentially, the GPU or Unified Memory Neural Engine is a stadium of thousands of calculators solving matrix math in parallel.
- **Technical Definition:** Hardware acceleration backends (**AMD ROCm**, **NVIDIA CUDA**, **Apple Metal**) used by `llama.cpp` and PyTorch. Note that `rag-tutor`'s retrieval stack (`all-MiniLM-L6-v2` + `ms-marco-MiniLM-L-6-v2` + `BM25` + `KùzuDB`) is lightweight enough (~180 MB RAM) to run fast even on **pure CPU**.
- **Official Link:** [llama.cpp on GitHub](https://github.com/ggerganov/llama.cpp)
- **Why It Is Used in This Project:** Ensures the retrieval stack runs anywhere (Linux CPU, Mac ARM, or GPU workstation).

---

### Docker & Process Sandboxing
- **Everyday Analogy:** A sealed shipping container with its own wiring and locks so workloads run isolated from the host machine.
- **Technical Definition:** OS-level containerization (`namespaces`, `cgroups`) and deeper runtime sandboxes (`gVisor`, `Firecracker` microVMs, `CiliumNetworkPolicy`).
- **Official Link:** [Docker Official Site](https://www.docker.com/)
- **Why It Is Used in This Project:** Runs Open WebUI or optional Omnigraph services in isolated containers, and forms a core architectural pattern in our Agent Sandboxing reference guide.

---

## 5. Language, Packaging & Documentation Tools

### uv (Astral)
- **Everyday Analogy:** A Rust-powered bullet train for Python package management that installs dependencies in seconds instead of minutes.
- **Technical Definition:** An ultra-fast Python package and virtual environment manager written in Rust.
- **Official Link:** [Astral uv Documentation](https://docs.astral.sh/uv/)
- **Why It Is Used in This Project:** Provides fast, reproducible virtual environments across the Tri-MCP stack.

---

### PyMuPDF (fitz)
- **Everyday Analogy:** A high-speed laser scanner that extracts text and exact page numbers from 800-page PDF books in less than a second.
- **Technical Definition:** Python bindings for the C-based **MuPDF** library.
- **Official Link:** [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- **Why It Is Used in This Project:** Powers PDF ingestion alongside native Markdown, TXT, JSON, and JSONL loaders in [`src/ingest.py`](src/ingest.py).

---

### Pydantic
- **Everyday Analogy:** A strict customs inspector verifying that every incoming data packet matches the exact required schema before letting it through.
- **Technical Definition:** Type-enforced data validation library for Python used across [`src/schemas.py`](src/schemas.py) and [`src/api.py`](src/api.py).
- **Official Link:** [Pydantic Documentation](https://docs.pydantic.dev/)
- **Why It Is Used in This Project:** Guarantees strict schema contracts across REST and MCP boundaries.

---

### Open WebUI
- **Everyday Analogy:** The touchscreen dashboard of a modern vehicle—giving you a visual chat interface over your local models and Tri-MCP tools.
- **Technical Definition:** An extensible, self-hosted web interface for Ollama and OpenAI-compatible APIs supporting custom Python tool plugins ([`openwebui_tool_tri_mcp.py`](openwebui_tool_tri_mcp.py)).
- **Official Link:** [Open WebUI Official Website](https://openwebui.com/)
- **Why It Is Used in This Project:** Provides the optional visual web chat frontend on port `3000`.

---

## 6. Maintenance Rules for Developers & AI Agents

This glossary is a **living document**. Every developer or AI agent modifying the repository must follow these three rules:
1. **When adding a new dependency to `requirements.txt`:** Add an entry explaining what it is (with an everyday analogy), its official link, and why it was added.
2. **When updating models or retrieval engines in `src/config.py`:** Update the corresponding section in this glossary.
3. **Keep explanations accessible:** Always preserve the **Everyday Analogy** + **Technical Definition** format.
