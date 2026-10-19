# Multi-MCP Integration Guide: Open WebUI + Study Cybercirujas + RAG Tutor

This guide explains how to connect **Open WebUI** with two simultaneous Model Context Protocol (MCP) servers to create an autonomous, 100% sovereign, and zero-cost **"Certification & Architecture AI Tutor"**:

1. 📚 **RAG Tutor MCP (`rag-tutor`):** Deep technical knowledge base covering 22+ engineering books, hybrid retrieval (ChromaDB + BM25), Cross-Encoder reranking, and exact page citations.
2. 🎯 **Study Cybercirujas MCP (`study-cybercirujas`):** Open IT certification platform (CKA, CKAD, CKS, LPIC, Azure, AWS) with official frozen vendor syllabi, practice exercises, and automated *break-and-fix labs*.

---

## 1. Multi-MCP System Architecture

```mermaid
flowchart TD
    User["Student / Engineer"] -->|1. 'Prepare me for CKA Objective 2.1 on Admission Controllers'| UI["Open WebUI / Claude Desktop\n(MCP Host & Chat Interface)"]
    
    subgraph Multi-Server MCP Tool Orchestration
        UI -->|Tool Call: get_topic('cka', '2.1')| MCP_CYBER["MCP Server: study-cybercirujas\n(teach.mcp_server)"]
        UI -->|Tool Call: consultar_libros_manning('Admission Controllers')| MCP_RAG["MCP Server: rag-tutor\n(src/mcp_server.py)"]
        
        MCP_CYBER -->|Returns Official Syllabus + Exercises + Break-Fix Lab| UI
        MCP_RAG -->|Returns Deep Architecture + YAML Manifests + Exact Book Citations| UI
    end
    
    UI -->|Combined context prompt to local Ollama qwen2.5:7b| LLM["Local LLM (Ollama)"]
    LLM -->|3. Comprehensive Synthesis: Exam Topic + Practical Lab + Deep Theory| User
```

---

## 2. Tools Exposed by Both MCP Servers

Both servers are implemented using the official Anthropic / Linux Foundation `mcp` SDK (v2.x `MCPServer`) over standard `stdio` JSON-RPC:

### Server 1: `study-cybercirujas` (Certifications & Labs)
- `list_certs()`: Lists all 28+ available certifications (CKA, CKAD, CKS, LPIC-1, KCNA, etc.).
- `get_syllabus(cert: str)`: Returns official exam objectives, domain weights, and language availability.
- `get_topic(cert: str, topic: str, lang: str)`: Returns official theory, exercises, and the break-and-fix shell lab script.
- `search_topics(query: str)`: Keyword search across titles and objectives in all certifications.

### Server 2: `rag-tutor` (Engineering Knowledge Base & Code Retrieval)
- `consultar_libros_manning(pregunta: str, dominio: str, solo_codigo: bool)`: Hybrid retrieval and agentic reflection loop over the technical books with exact page citations.
- `buscar_codigo_yaml(termino: str)`: Exact lexical search for YAML manifests, CRDs, CLI commands, and Go snippets without LLM distortion.

---

## 3. Configuration Setup in Open WebUI & MCP Clients

### Option A: Configuration in Claude Desktop or Goose CLI (`claude_desktop_config.json`)
Add both servers to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag-tutor": {
      "command": "C:\\Users\\rino\\Documents\\GitHub\\rag-tutor\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\rino\\Documents\\GitHub\\rag-tutor\\src\\mcp_server.py"
      ]
    },
    "study-cybercirujas": {
      "command": "python",
      "args": [
        "-m",
        "teach.mcp_server"
      ],
      "cwd": "C:\\path\\to\\study-cybercirujas"
    }
  }
}
```

### Option B: Integration in Open WebUI
In **Open WebUI**, connect the servers via:
1. **Open WebUI MCPO / Pipes:** Enable MCP server connections under *Workspace -> Tools* in Open WebUI.
2. **Native OpenAPI REST Connection:** Connect `http://localhost:8000/chat` directly as an OpenAPI connector in Open WebUI.

---

## 4. End-to-End Simulation: The Certification Study Tutor

### User Prompt in Open WebUI:
> *"I want to study Admission Controllers for the CKA certification. Give me the official exam objective, the practice exercise from Cybercirujas, and explain in detail using the engineering books how to implement it with YAML manifests and OPA Gatekeeper."*

### Empirical Execution Flow:
1. **Tool Invocation 1 (Cybercirujas):** Open WebUI calls `get_topic("cka", "2.1", "en")`.
   - Retrieves the official CNCF syllabus objective: *"Understand Admission Controllers and Webhooks"*.
   - Retrieves the hands-on break-and-fix lab scenario.
2. **Tool Invocation 2 (RAG Tutor):** Open WebUI calls `consultar_libros_manning("Admission Controllers validation and OPA Gatekeeper")`.
   - Retrieves relevant chunks from **Core Kubernetes (Page 286)** and **Effective Platform Engineering (Pages 122, 127)**.
   - Extracts the exact webhook configuration YAML manifest and the `image.sha` validation flow.
3. **Local LLM Synthesis:**
   - Presents the official exam syllabus context.
   - Provides the hands-on lab break scenario.
   - Delivers in-depth engineering theory with verified page citations and executable YAML.
