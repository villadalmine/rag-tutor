# 🚀 Command Cheatsheet & Demo Reference: Sovereign RAG & Tri-MCP Stack

This practical cheatsheet contains all CLI commands, LLM-free verification commands, SQL-like `WHERE` filter examples, `curl` calls, hardware checks (GPU vs CPU), and setup steps for demonstrating **`rag-tutor`** standalone or as part of the **Tri-MCP Sovereign Stack**.

---

## 📑 Quick Navigation
1. [Standalone `rag-tutor` CLI & LLM-Free Commands (Zero Ollama Required)](#1-standalone-rag-tutor-cli--llm-free-commands-zero-ollama-required)
2. [Direct MCP Tool Invocations (Progressive Zero-Token-Burn)](#2-direct-mcp-tool-invocations-progressive-zero-token-burn)
3. [Service Map, Ports & Web Links](#3-service-map-ports--web-links)
4. [Hardware Verification: GPU vs CPU](#4-hardware-verification-gpu-vs-cpu)
5. [cURL & PowerShell Gateway Cheatsheet (`/health`, `/mcp/status`, `/mcp/test`, `/chat`)](#5-curl--powershell-gateway-cheatsheet-health-mcpstatus-mcptest-chat)
6. [Open WebUI, VS Code & Cursor Integration](#6-open-webui-vs-code--cursor-integration)
7. [Cold-Start Boot Sequence](#7-cold-start-boot-sequence)

---

## 1. Standalone `rag-tutor` CLI & LLM-Free Commands (Zero Ollama Required)

### 1.1 Automated End-to-End Verification Suite (No LLM Required)
```bash
.venv/bin/python tests/test_no_llm_pipeline.py
```

### 1.2 Incremental Multi-Format Ingestion & 3-Layer Deduplication
```bash
# Ingest all new or modified sources in books/ (.pdf, .md, .txt, .json, .jsonl, or Markdown folders)
.venv/bin/python src/ingest.py

# Sync only Markdown/ chapter folders from an external export directory and index incrementally:
.venv/bin/python src/ingest.py --sync-dir /path/to/external/markdown-library

# Force a full rebuild of ChromaDB, BM25, and KùzuDB from scratch:
.venv/bin/python src/ingest.py --reset
```

### 1.3 Inspecting & Filtering the Indexed Catalog (`--list-books`)
```bash
# List all indexed books with publication year, domain, tags, and chapter/section tree:
.venv/bin/python src/cli.py --list-books

# Filter catalog by domain and publication year (excludes pre-2025 books automatically):
.venv/bin/python src/cli.py --list-books --domain cloud_native --min-year 2025
```

### 1.4 Querying with SQL-like `WHERE` Filters (`--no-llm` Retrieve-Only or Full Agentic Mode)
```bash
# Deterministic retrieval without an LLM (~2s on CPU, returns reranked chunks + KùzuDB topology):
.venv/bin/python src/cli.py "How to deploy and serve LLMs with vLLM on Kubernetes?" \
  --domain cloud_native \
  --min-year 2025 \
  --tag kubernetes \
  --no-llm

# Filter strictly by code block language (yaml, go, python, bash, sql, rust):
.venv/bin/python src/cli.py "CiliumNetworkPolicy egress DNS rules" \
  --domain cloud_native \
  --code yaml \
  --min-year 2025 \
  --no-llm

# Filter by specific chapter/section substring:
.venv/bin/python src/cli.py "Sandboxing coding agent execution microVMs gVisor" \
  --domain ai_agents \
  --section "Secure Execution" \
  --min-year 2025 \
  --no-llm
```

### 1.5 Manual Metadata Override (Protected Across Re-Index Runs)
```bash
.venv/bin/python src/cli.py \
  --set-book "ebpf-and-cilium-networking" \
  --set-domain "cloud_native" \
  --set-tags "cilium,ebpf,kubernetes,hubble,cni,zero_trust" \
  --set-year 2026
```

---

## 2. Direct MCP Tool Invocations (Progressive Zero-Token-Burn)

Test the 5 MCP tools exposed by [`src/mcp_server.py`](src/mcp_server.py) directly from your terminal:

```bash
.venv/bin/python -c '
from src.mcp_server import (
    listar_libros_y_secciones,
    buscar_fragmentos_secciones,
    consultar_grafo_kuzu,
    buscar_codigo_yaml,
)

# Step 1: Compact catalog discovery (~300 tokens)
print(listar_libros_y_secciones(domain="ai_agents", min_year=2025, incluir_secciones=False))

# Step 2: Targeted section retrieval (~900 tokens)
print(buscar_fragmentos_secciones(
    consulta="agent sandbox runtime isolation Firecracker gVisor",
    top_k=3,
    domain="ai_agents",
    min_year=2025,
))

# Step 3: KùzuDB Cypher graph inspection
print(consultar_grafo_kuzu("ai-agent"))

# Step 4: Exact YAML code extraction
print(buscar_codigo_yaml("CiliumNetworkPolicy", code_lang="yaml", min_year=2025))
'
```

---

## 3. Service Map, Ports & Web Links

| Service | Local Port | Interactive URL | Primary Role |
| :--- | :--- | :--- | :--- |
| **Open WebUI** | `:3000` | [http://localhost:3000](http://localhost:3000) | Self-hosted web chat interface with Python tool integration. |
| **RAG Tutor Gateway API** | `:8000` | [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger) | Tri-MCP Orchestrator, Hybrid RAG (ChromaDB + BM25 + Reranker), and KùzuDB GraphRAG. |
| **Study Cybercirujas** | `:8080` | [http://localhost:8080](http://localhost:8080) / [Catalog API](http://localhost:8080/api/catalog) | Official CNCF/LPI certification syllabi and interactive break/fix labs. |
| **Ollama LLM Engine** | `:11434` | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | Optional local LLM inference server (GPU / Apple Silicon / CPU). |

---

## 4. Hardware Verification: GPU vs CPU

- **Retrieval Stack (`ChromaDB` + `BM25` + `Cross-Encoder` + `KùzuDB`):** Uses lightweight models (~180 MB total RAM) and runs in **< 2 seconds on pure CPU** or Apple Silicon with `HF_HUB_OFFLINE=1`.
- **Optional Local LLM (`Ollama`):** Check whether Ollama models are offloaded to GPU VRAM:

```bash
# Linux / macOS / WSL
curl -s http://localhost:11434/api/ps | jq '.models[] | {name, size_vram, runner}'
```

```powershell
# Windows PowerShell
(Invoke-RestMethod -Uri "http://localhost:11434/api/ps").models | Select-Object name, size_vram, runner | Format-Table -AutoSize
```

---

## 5. cURL & PowerShell Gateway Cheatsheet (`/health`, `/mcp/status`, `/mcp/test`, `/chat`)

### 5.1 Healthcheck (`/health`)
```bash
curl -s http://localhost:8000/health | jq
```
Expected response:
```json
{
  "status": "online",
  "service": "rag-tutor",
  "retriever_type": "omnigraph",
  "ollama_model": "qwen2.5:7b",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
  "chroma_dir_exists": true,
  "bm25_index_exists": true,
  "knowledge_graph_exists": true
}
```

### 5.2 Tri-MCP Cluster Monitoring (`/mcp/status`)
```bash
curl -s http://localhost:8000/mcp/status | jq
```

### 5.3 Live Audit Logs (`/mcp/logs`)
```bash
curl -s http://localhost:8000/mcp/logs | jq
```

### 5.4 Live Diagnostic Test (`/mcp/test`)
```bash
curl -s -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{
    "target": "all",
    "query": "three example how i can create a pod yaml definition and a theory how works"
  }' | jq
```

### 5.5 Querying `/chat` with `WHERE` Filters (`min_year`, `domain`, `tag`, `no_llm`)
```bash
# Retrieve-only mode over HTTP (no Ollama required):
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to serve LLMs with vLLM on Kubernetes?",
    "domain": "cloud_native",
    "min_year": 2025,
    "tag": "kubernetes",
    "no_llm": true,
    "orchestrate_tri_mcp": false
  }' | jq

# Full Tri-MCP + Local LLM synthesis:
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do in-tree ValidatingAdmissionPolicies work in Kubernetes?",
    "min_year": 2024,
    "orchestrate_tri_mcp": true
  }' | jq
```

---

## 6. Open WebUI, VS Code & Cursor Integration

The file [`mcp_servers_config.json`](mcp_servers_config.json) defines the MCP servers for **Claude Desktop**, **Cursor** (`.cursor/mcp.json`), **VS Code (Cline / Roo Code)**, or **Antigravity**:

```json
{
  "mcpServers": {
    "study-cybercirujas": {
      "command": "python",
      "args": ["-m", "teach.mcp_server"],
      "cwd": "../study-cybercirujas"
    },
    "k8s-docs-mcp": {
      "command": "uv",
      "args": ["--directory", "../k8s-docs-mcp", "run", "k8s-docs-mcp"]
    },
    "rag-tutor": {
      "command": ".venv/bin/python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "."
    }
  }
}
```

For **Open WebUI**, import [`openwebui_tool_tri_mcp.py`](openwebui_tool_tri_mcp.py) under **Workspace ➔ Tools ➔ `+` (Create Tool)** and enable it on your model.

---

## 7. Cold-Start Boot Sequence

```bash
# 1. Run automated LLM-free verification (works immediately offline):
.venv/bin/python tests/test_no_llm_pipeline.py

# 2. Start RAG Tutor Gateway API on port 8000:
.venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# 3. (Optional) Start Ollama if using local LLM synthesis:
ollama run qwen2.5:7b ""

# 4. (Optional) Start study-cybercirujas on port 8080:
cd ../study-cybercirujas && python -m uvicorn teach.api:app --host 0.0.0.0 --port 8080
```
