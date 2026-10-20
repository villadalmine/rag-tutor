# 🚀 Demo Runbook: Sovereign Cloud Native Learning Platform & Tri-MCP Model

> **Live Demo & Deployment Guide**  
> Complete walkthrough to run, demonstrate, and orchestrate **study-cybercirujas**, **k8s-docs-mcp**, **rag-tutor**, **Ollama**, and **Open WebUI** in a 100% sovereign, local-first platform engineering environment.

---

## 🧭 Executive Summary: The Cloud Native Trifecta

Modern platform engineering education requires three complementary, sovereign layers:

```
                      ┌────────────────────────────────────────┐
                      │              USER / CLIENT             │
                      │  Open WebUI / Claude Desktop / Cursor  │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
     ┌────────────────────────┐┌────────────────────────┐┌────────────────────────┐
     │   study-cybercirujas   ││      k8s-docs-mcp      ││       rag-tutor        │
     │      (MCP Server)      ││      (MCP Server)      ││   (MCP / REST API)     │
     ├────────────────────────┤├────────────────────────┤├────────────────────────┤
     │  "The Syllabus & Labs" ││  "The API Truth & YAML"││  "The Architecture"   │
     │                        ││                        ││                        │
     │ • 38 Certifications   ││ • Official kubernetes.io││ • Manning Books RAG    │
     │ • 726 Exam Objectives  ││ • OpenAPI v3 Specs     ││ • KùzuDB GraphRAG      │
     │ • On-Demand Break/Fix  ││ • Pre-processed YAMLs  ││ • Agentic Loop         │
     │ • Zero API Tokens      ││ • Zero Deprecations    ││ • Cross-Encoder Rerank │
     └────────────────────────┘└────────────────────────┘└────────────────────────┘
                  ▲                       ▲                       ▲
                  └───────────────────────┼───────────────────────┘
                                          │ Local Ingestion & Offline Execution
                                          ▼
                               ┌────────────────────────┐
                               │     OLLAMA ENGINE      │
                               │  qwen2.5:7b / bge-m3   │
                               │ (100% Sovereign & GPU) │
                               └────────────────────────┘
```

| Engine | Primary Role | Source Material | Protocol | Port / Transport |
| :--- | :--- | :--- | :--- | :--- |
| **`study-cybercirujas`** | Syllabus & Lab Authority | CNCF / LPI / LF syllabi + break-fix labs | REST + Stdio MCP | `:8080` / `teach.mcp_server` |
| **`k8s-docs-mcp`** | Specification Authority | Upstream kubernetes/website + OpenAPI v3 | Stdio MCP | `k8s_docs_mcp.server` |
| **`rag-tutor`** | Architectural Authority | Manning Platform Engineering Corpus | REST + KùzuDB Cypher | `:8000` / `src.api:app` |
| **`Open WebUI`** | Unified Sovereign UI | Multi-agent Chat, Tools & RAG interface | Web / HTTP | `:3000` |
| **`Ollama`** | Sovereign LLM & Embeddings | Local Weights (`qwen2.5:7b`, `bge-m3`) | REST API | `:11434` |

---

## ⚡ Active Demo Dashboard (Pre-Warmed Services)

All services are **already initialized and active** in the background:

| Service | Local URL / Direct Link | Health Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **Study Platform Web UI** | [http://localhost:8080](http://localhost:8080) | [http://localhost:8080/healthz](http://localhost:8080/healthz) | **RUNNING** |
| **Study Platform API Docs** | [http://localhost:8080/docs](http://localhost:8080/docs) | [http://localhost:8080/api/catalog](http://localhost:8080/api/catalog) | **RUNNING** |
| **RAG Tutor REST API** | [http://localhost:8000](http://localhost:8000) | [http://localhost:8000/health](http://localhost:8000/health) | **RUNNING** |
| **RAG Tutor Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | **RUNNING** |
| **Open WebUI Frontend** | [http://localhost:3000](http://localhost:3000) | [http://localhost:3000/api/config](http://localhost:3000/api/config) | **RUNNING** |
| **Ollama Local Engine** | [http://localhost:11434](http://localhost:11434) | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | **RUNNING** |

---

## 📋 Step-by-Step Demo Walkthrough

### Part 1: Exploring `study-cybercirujas` (The Educational Platform)

`study-cybercirujas` is a self-service IT certification platform built on a pure Markdown/YAML corpus, featuring automated syllabus tracking, multi-language support (ES, EN, FR, DE, ZH, JA, PT), and reproducible break/fix hands-on labs.
GitHub: [https://github.com/villadalmine/study-cybercirujas](https://github.com/villadalmine/study-cybercirujas)

#### 1.1 Open the Interactive Web Platform
Click the link to open directly in your browser:
👉 **[Open Study Platform (http://localhost:8080)](http://localhost:8080)**

- **What to show in the demo:**
  1. **Certification Catalog:** 38 technical certifications organized by domains:
     - Cloud Native: `CKA`, `CKAD`, `CKS`, `KCNA`, `KCSA`, `CNPE`
     - Linux & Systems: `LPI 010-160`, `LPIC-1`, `LPIC-2`, `LPIC-3`
     - Infrastructure as Code: `Terraform Associate (004)`, `Terraform Advanced`
     - AI & Protocols: `Model Context Protocol Associate (MCPA)`, `NVIDIA NCA/NCP`
  2. **Topic Deep Dive:** Click on **CKA** or **CNPE** -> select any topic (e.g., *Domain 3.4 - Using Policy Engines and Admission Controllers*).
  3. **Break/Fix Hands-on Labs:** Show that every objective includes an incident scenario with a reproducible bash script (`break_fix.sh --break` and `--check`) ready to run in a local cluster.

#### 1.2 Inspecting the Platform REST API
You can click these live endpoints directly in your browser or curl them:
- **Catalog API:** [http://localhost:8080/api/catalog](http://localhost:8080/api/catalog)
- **Search API (e.g. admission):** [http://localhost:8080/api/search?q=admission](http://localhost:8080/api/search?q=admission)
- **Topic API (CNPE 3.4):** [http://localhost:8080/api/certs/cnpe/topics/3.4?lang=en](http://localhost:8080/api/certs/cnpe/topics/3.4?lang=en)
- **Swagger Interactive Docs:** [http://localhost:8080/docs](http://localhost:8080/docs)

```bash
# Verify catalog and certification listing
curl -s http://localhost:8080/api/catalog | jq 'keys'

# Search across all 726 objectives for admission control or etcd
curl -s "http://localhost:8080/api/search?q=admission" | jq '.hits[0:2]'

# Retrieve full topic theory and lab specifications
curl -s "http://localhost:8080/api/certs/cnpe/topics/3.4?lang=en" | jq '.topic.title, .generated_by'
```

#### 1.3 How to Run `study-cybercirujas` from Scratch
If running on a new machine:
```bash
git clone https://github.com/villadalmine/study-cybercirujas.git
cd study-cybercirujas

# Setup environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e '.[mcp,lab]'

# Launch the server (Web UI + REST API)
python -m teach.cli serve --host 0.0.0.0 --port 8080
# Or via Makefile:
make serve PORT=8080
```

---

### Part 2: Using the `study-cybercirujas` MCP Server

The platform exposes its entire knowledge base via the standard **Model Context Protocol (MCP)** using `teach.mcp_server`.
GitHub repository: [https://github.com/villadalmine/study-cybercirujas](https://github.com/villadalmine/study-cybercirujas)

#### 2.1 The MCP Contract (Four Sovereign Tools)
1. `list_certs()`: Returns all 38 certifications and counts of generated objectives.
2. `get_syllabus(cert: str)`: Returns full objective hierarchy and exam weights.
3. `get_topic(cert: str, topic: str, lang: str)`: Retrieves verified theory, references, and break/fix lab scripts.
4. `search_topics(query: str, cert: str | None)`: Fast keyword search across titles, domains, and exam objectives.

#### 2.2 Adding `teach.mcp_server` to Claude Desktop / Cursor
You can configure both [study-cybercirujas](https://github.com/villadalmine/study-cybercirujas) and [k8s-docs-mcp](https://github.com/villadalmine/k8s-docs-mcp) simultaneously in your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "study-cybercirujas": {
      "command": "/path/to/study-cybercirujas/.venv/bin/python",
      "args": ["-m", "teach.mcp_server"],
      "cwd": "/path/to/study-cybercirujas"
    },
    "k8s-docs-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/k8s-docs-mcp", "run", "k8s-docs-mcp"]
    }
  }
}
```

---

### Part 3: Connecting Open WebUI and Ollama

Open WebUI provides a unified UI for local models, OpenAPI tools, and multi-agent workflows without cloud telemetry.

#### 3.1 Verifying Ollama Engine
Ollama runs locally on port `11434`. You can inspect available models via browser or curl:
- **Ollama Tags API:** [http://localhost:11434/api/tags](http://localhost:11434/api/tags)

```bash
curl -s http://localhost:11434/api/tags | jq '.models[].name'
```
Expected output:
- `qwen2.5:7b` (General reasoning & technical coding)
- `qwen3:4b` / `llama3.2:3b` (Lightweight reasoning)
- `bge-m3:latest` (Dense multilingual embeddings)

#### 3.2 Accessing Open WebUI
Click the link to open directly in your browser:
👉 **[Open WebUI Interface (http://localhost:3000)](http://localhost:3000)**

- Open WebUI runs in Docker with `WEBUI_AUTH=False` (instant access, zero login hurdles for live demos).
- The models from Ollama are detected automatically via `http://host.docker.internal:11434`.

#### 3.3 Registering `rag-tutor` as an OpenAPI Tool in Open WebUI
Open WebUI can directly call REST APIs that expose OpenAPI 3.0 specs:
- **RAG Tutor OpenAPI Spec:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **RAG Tutor Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

1. In Open WebUI, navigate to: **Workspace -> Tools -> `+` (Create Tool)**.
2. Click on the three dots `...` in the top right or select **Import from OpenAPI**.
3. Enter the internal container OpenAPI URL:
   ```text
   http://host.docker.internal:8000/openapi.json
   ```
4. Click **Import**. Open WebUI will register the `chat_endpoint` and `health_check` tools.
5. In any chat session, enable the `rag-tutor` tool so that `qwen2.5:7b` can delegate complex technical and architectural questions to the local RAG engine!

---

### Part 4: The Tri-MCP Live Orchestration Demo

This is the centerpiece of the demonstration: showing how autonomous agents coordinate **all three MCP servers** simultaneously to produce an authoritative, hallucination-free answer.

#### 4.1 How Autonomous Routing Works (The 3 Questions)
When an engineer asks:
> *"How do in-tree ValidatingAdmissionPolicies (CEL) and admission webhooks enforce platform governance, and what are their architectural trade-offs?"*

The agent routes the query through the Trifecta:
1. **Query `study-cybercirujas`**:
   - *Question asked:* What is the official certification context and exam scope?
   - *Tool called:* `search_topics("admission controllers")` -> `get_topic("cnpe", "3.4")`.
   - *Result:* Retrieves CNPE Domain 3.4 objective, official LF curriculum, and break/fix lab.
2. **Query `k8s-docs-mcp`**:
   - *Question asked:* What is the exact API version and canonical YAML syntax?
   - *Tool called:* `check_api_version("ValidatingAdmissionPolicy")` -> `get_canonical_manifest("ValidatingAdmissionPolicy")`.
   - *Result:* Authoritatively confirms `admissionregistration.k8s.io/v1` (STABLE) and injects canonical manifest from kubernetes.io.
3. **Query `rag-tutor`**:
   - *Question asked:* Why does this matter architecturally, and how does it integrate with GitOps pipelines?
   - *Tool called:* `HybridRetriever` + `OmnigraphRetriever` (KùzuDB GraphRAG).
   - *Result:* Extracts trade-offs from Manning books (*Core Kubernetes*, *Effective Platform Engineering*, *GitOps and Kubernetes*).

#### 4.2 Running the Live Tri-MCP Script
Execute the end-to-end verification script from the root of `rag-tutor`:

```bash
# In your terminal:
python test_multi_mcp_live.py
```

#### 4.3 Expected Real-Time Output
```text
========================================================================
 🎓 LIVE TRI-MCP ORCHESTRATION SESSION (STUDY + K8S-DOCS + RAG-TUTOR)
========================================================================

[MCP 1: study-cybercirujas] Calling search_topics('admission controllers')...
  --> Identified Objective: CNPE 3.4 - Using Policy Engines and Admission Controllers for Governance
  --> Certification:        Certified Cloud Native Platform Engineer (CNPE) (Weight: 3%)

[MCP 1: study-cybercirujas] Calling get_topic('cnpe', '3.4')...
  --> Official Syllabus Excerpt:
      # Study Guide: Domain 3.4 — Using Policy Engines and Admission Controllers for Governance
      **Certification:** CNCF Certified Cloud Native Platform Engineer (CNPE)  
      **Domain Weight:** 3%  
      **Target Role:** Principal Platform Architect / Senior SRE  

------------------------------------------------------------------------
[MCP 2: k8s-docs-mcp] Calling check_api_version('ValidatingAdmissionPolicy')...
  --> Authoritative Kubernetes API Check: ValidatingAdmissionPolicy
  --> Current Stable apiVersion: admissionregistration.k8s.io/v1
  --> Status: STABLE

[MCP 2: k8s-docs-mcp] Calling get_canonical_manifest('ValidatingAdmissionPolicy')...
  --> Canonical Manifest Preview:
      apiVersion: admissionregistration.k8s.io/v1
      kind: ValidatingAdmissionPolicy
      metadata:
        name: "demo-policy.example.com"
      ...

------------------------------------------------------------------------
[MCP 3: rag-tutor] Phase 1: Hybrid Retrieval (ChromaDB + BM25 + Cross-Encoder)...
[MCP 3: rag-tutor] Phase 2: GraphRAG (KùzuDB Cypher + Knowledge Graph Traversal)...

📖 Consulted Sources (Synthesized Ground Truth):
  • study-cybercirujas MCP: CNPE Topic 3.4 (Using Policy Engines and Admission Controllers)
  • k8s-docs-mcp MCP: kubernetes.io (ValidatingAdmissionPolicy CEL Specification)
  • Effective_Platform_Engineering.pdf (Page 143)
  • Effective_Platform_Engineering.pdf (Page 121)
  • Core_Kubernetes.pdf (Page 286)
  • GitOps_and_Kubernetes.pdf (Page 212)

========================================================================
 🎉 Tri-MCP Session Complete: Verified Live Across All 3 Engines!
========================================================================
```

---

## 🎤 Presenter's Cheat Sheet (3-Minute Live Demo)

If you have 3 minutes to present this platform:

1. **Minute 1: The Problem & The Platform UI ([http://localhost:8080](http://localhost:8080))**
   - *"Engineers preparing for CKA or platform roles currently struggle with fragmented documentation and outdated YAMLs.*
   - *Here is [study-cybercirujas](https://github.com/villadalmine/study-cybercirujas): a 100% sovereign learning catalog covering 38 certifications and 700+ topics with hands-on break/fix labs.*
   - *Notice that every topic is open, tracked against official CNCF syllabi, and runs completely offline."*

2. **Minute 2: The Multi-MCP Trifecta (`test_multi_mcp_live.py`)**
   - *"When asking an LLM for technical assistance, single-source prompts hallucinate deprecated APIs.*
   - *We solved this with a Cloud Native Trifecta: [study-cybercirujas](https://github.com/villadalmine/study-cybercirujas) tells the agent what is in scope; [k8s-docs-mcp](https://github.com/villadalmine/k8s-docs-mcp) validates the exact kubernetes.io API and canonical manifest; [rag-tutor](https://github.com/villadalmine/rag-tutor) provides the architectural depth from Manning engineering books.*
   - *Let's run `python test_multi_mcp_live.py` in live terminal — watch the agent query the syllabus, pull the official CEL manifest, and ground the answer in platform engineering literature."*

3. **Minute 3: Open WebUI & Local Sovereignty ([http://localhost:3000](http://localhost:3000))**
   - *"Finally, here is [Open WebUI](http://localhost:3000) connected to local Ollama running Qwen 2.5.*
   - *All three tools are accessible right in the chat interface. Zero cloud costs, zero privacy leakage, 100% deterministic platform engineering."*

---

## 🛠️ Operational Maintenance & Commands

| Action | Command |
| :--- | :--- |
| **Check Active Ports** | `Get-NetTCPConnection -LocalPort 3000, 8000, 8080, 11434` |
| **Restart Open WebUI** | `docker restart open-webui` |
| **View Open WebUI Logs** | `docker logs open-webui -f` |
| **Restart Study Platform** | `uvicorn teach.api:app --host 0.0.0.0 --port 8080` (inside `study-cybercirujas`) |
| **Restart RAG Tutor API** | `uvicorn src.api:app --host 0.0.0.0 --port 8000` (inside `rag-tutor`) |
| **Re-run Tri-MCP Test** | `python test_multi_mcp_live.py` (inside `rag-tutor`) |
