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
Add both servers to your agent's MCP configuration (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rag-tutor": {
      "command": "/path/to/rag-tutor/.venv/bin/python",
      "args": [
        "/path/to/rag-tutor/src/mcp_server.py"
      ]
    },
    "study-cybercirujas": {
      "command": "/path/to/study-cybercirujas/.venv/bin/python",
      "args": [
        "-m",
        "teach.mcp_server"
      ],
      "cwd": "/path/to/study-cybercirujas"
    }
  }
}
```

### Option B: Integration in Open WebUI
In **Open WebUI**, connect the servers via:
1. **Open WebUI MCPO / Pipes:** Enable MCP server connections under *Workspace -> Tools* in Open WebUI.
2. **Native OpenAPI REST Connection:** Connect `http://localhost:8000/chat` directly as an OpenAPI connector in Open WebUI.

---

## 4. End-to-End Verified Live Session: The Certification Study Tutor

The following live session was executed and verified against both `study-cybercirujas`'s corpus and `rag-tutor`'s local engine across Phase 1 (Hybrid) and Phase 2 (GraphRAG):

```text
======================================================================
 🎓 LIVE MULTI-MCP ORCHESTRATION SESSION (STUDY + RAG-TUTOR)
======================================================================

[MCP Client] Calling Tool: study-cybercirujas.search_topics('admission controllers')...
  --> Found Objective: CNPE 3.4 - Using Policy Engines and Admission Controllers for Governance
  --> Certification:    Certified Cloud Native Platform Engineer (CNPE) (Weight: 3%)

[MCP Client] Calling Tool: study-cybercirujas.get_topic('cnpe', '3.4')...
  --> Official Study Guide Excerpt:
      # Study Guide: Domain 3.4 — Using Policy Engines and Admission Controllers for Governance
      **Certification:** CNCF Certified Cloud Native Platform Engineer (CNPE)  
      **Domain Weight:** 3%  
      **Target Role:** Principal Platform Architect / Senior SRE  
      ---

----------------------------------------------------------------------
[MCP Client] Calling Tool: rag-tutor.consultar_libros_manning (Phase 1: Hybrid)...
  Query: 'How do mutating and validating admission webhooks enforce platform governance?'

--- Phase 1 Grounded Answer Preview ---
Mutating and validating admission webhooks are key components in enforcing platform governance in Kubernetes by providing a flexible and extensible way to enforce policies and validate API requests before they are persisted in the cluster. Let's break down how each type of webhook works and their role in governance.

### Mutating Admission Webhooks
Mutating admission webhooks are designed to modify the objects being created or updated before they are persisted in the cluster. These webhooks can inject or modify fields in the API objects, ensuring that the objects meet certain criteria before they are applied.

#### Example Scenario: Enforcing Container Security Policies
Consider a scenario where you want to enforce that all containers running in the cluster are not allowed to run as `root`. You can use a mutating webhook to automatically set the `runAsUser` field to a non-root value for any `Pod` that is created or updated...
...

📖 Consulted Sources (Phase 1):
  • study-cybercirujas MCP: CNPE Topic 3.4 (Using Policy Engines and Admission Controllers for Governance)
  • Effective_Platform_Engineering.pdf (Page 143)
  • GitOps_and_Kubernetes.pdf (Page 212)
  • Effective_Platform_Engineering.pdf (Page 121)
  • Core_Kubernetes.pdf (Page 286)

----------------------------------------------------------------------
[MCP Client] Calling Tool: rag-tutor.consultar_libros_manning (Phase 2: GraphRAG)...
  Query: 'How does an Internal Developer Platform relate to admission controllers and paved roads?'

--- Phase 2 Graph-Grounded Answer Preview ---
An Internal Developer Platform (IDP) plays a crucial role in integrating admission controllers and the concept of "paved roads" (also known as "golden paths") into the development and deployment processes. Let's break down the relationship between these components based on the provided context.

### Internal Developer Platform (IDP) and Admission Controllers
1. **Standardized Service Templates**:
   - **IDP** provides **standardized service templates** that ensure best practices are followed across teams. These templates can include preconfigured setups for common microservices, which can be validated and enforced by admission controllers.
2. **Automated Service Provisioning**:
   - **IDP** enables **automated service provisioning** in a controlled environment. Admission controllers validate service configurations before deployment, ensuring correct resource requests and limits.
3. **Integrated CI/CD Pipelines**:
   - **IDP** integrates CI/CD pipelines that automate testing, security scans, and deployments, ensuring that only validated and compliant code is deployed.
...

📖 Consulted Sources (Phase 2):
  • study-cybercirujas MCP: CNPE Topic 3.4 (Using Policy Engines and Admission Controllers for Governance)
  • Effective_Platform_Engineering.pdf (Page 143)
  • Effective_Platform_Engineering.pdf (Page 35)
  • Effective_Platform_Engineering.pdf (Page 363)
  • Effective_Platform_Engineering.pdf (Page 381)

======================================================================
 🎉 Session Complete: Both MCPs and Both RAG Phases Verified Live!
======================================================================
```
