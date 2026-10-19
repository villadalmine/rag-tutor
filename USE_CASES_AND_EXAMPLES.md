# Real-World Use Cases, Generated Outputs & Setup Guide

This document provides a comprehensive walkthrough of **how the system was built and executed**, along with **unfiltered real-world outputs** produced on local hardware across multiple technical engineering domains.

---

## 1. How I Made It Work: From Zero to Running System

The entire system was designed and verified to run **100% locally on consumer hardware without external API subscriptions or cloud dependencies**.

### Step 1: Virtual Environment & Dependency Installation
Using Python 3.11:
```powershell
# Create isolated environment
python -m venv .venv

# Activate environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install core dependencies (LangChain, ChromaDB, Rank-BM25, PyMuPDF, FastAPI, MCP)
pip install -r requirements.txt
```

### Step 2: Local LLM Engine Setup with Ollama
Ollama serves as the local inference runtime. We pulled `qwen2.5:7b` (Alibaba's state-of-the-art open-weights model):
```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b
```

### Step 3: Placing Books (BYOB - Bring Your Own Books)
Copy your legally owned PDF books into `books/`. The system auto-profiles any topic:
```powershell
# The directory is empty by default
Get-ChildItem books/
```

### Step 4: Enforcing 100% Offline Mode for Hugging Face
To prevent network timeouts, telemetry warnings, or unauthenticated API rate limits, `src/config.py` programmatically enforces offline operation:
```python
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
```
The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) and cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) run strictly from local disk cache (`~/.cache/huggingface/hub`).

### Step 5: Batched Incremental Ingestion
When scaling to 22 books (8,516 pages), ChromaDB's Rust backend enforces a maximum batch limit of 5,461 documents per transaction. We resolved this in `src/ingest.py` by partitioning the 19,174 new chunks into batches of 2,000:
```powershell
.\.venv\Scripts\python.exe src/ingest.py
```
**Console Output:**
```text
=================================================================
 📚 Technical Ingestion: Incremental Book Processing
=================================================================

[+] Total books found in books/: 22
[+] Technical chunks generated: 19174
[+] Generating embeddings (sentence-transformers/all-MiniLM-L6-v2) into ChromaDB...
    [ChromaDB Progress] 2000/19174 chunks saved...
    [ChromaDB Progress] 4000/19174 chunks saved...
    [ChromaDB Progress] 6000/19174 chunks saved...
    [ChromaDB Progress] 8000/19174 chunks saved...
    [ChromaDB Progress] 10000/19174 chunks saved...
    [ChromaDB Progress] 12000/19174 chunks saved...
    [ChromaDB Progress] 14000/19174 chunks saved...
    [ChromaDB Progress] 16000/19174 chunks saved...
    [ChromaDB Progress] 18000/19174 chunks saved...
    [ChromaDB Progress] 19174/19174 chunks saved...
[OK] 19174 new chunks committed to ChromaDB.
[+] Updating BM25 lexical inverted index...
[OK] BM25 index updated with 23343 total chunks at: bm25_index.pkl
=================================================================
 🎉 Ingestion successfully completed!
=================================================================
```

---

## 2. Real-World Use Cases & Verifiable Outputs

Below are actual, untampered outputs captured directly from terminal runs against the 23,343-chunk database.

---

### Use Case 1: Kubernetes Internals & Security Governance
*Testing whether the hybrid retriever and cross-encoder isolate deep architecture without semantic dilution.*

#### Command:
```powershell
.\.venv\Scripts\python.exe src/cli.py "Explain what an Admission Controller is in Kubernetes and how it validates resources"
```

#### Generated Output:
```text
[Info] Using HybridRetriever (Phase 1: ChromaDB + BM25 + Reranker)

🔍 Querying technical library...

=================================================================
💡 Tutor Response:
=================================================================
An Admission Controller in Kubernetes is a component that integrates with the API Server and is responsible for modifying or rejecting resources that are being created or updated in the cluster. This mechanism provides an interception point to enforce security policies, access controls, and operational constraints at entry time.

### Components & Mechanics

1. **API Server**: The primary entry point for all operations. When attempting to create, update, or delete a resource, the API Server forwards the request to admission controllers after authentication and authorization.

2. **Admission Controllers**: These execute as webhooks and validate or mutate resources before they are processed by the API Server. They can reject non-compliant requests or mutate the object (e.g., injecting default annotations or sidecars).

3. **Webhooks**: Admission controllers communicate with external policy engines, such as OPA (Open Policy Agent) Gatekeeper, using Rego policies to evaluate whether a request meets governance standards.

### Concrete Examples

- **RBAC**: Checks user privileges via `--authorization-mode=RBAC` in the API Server.
- **ImagePolicyWebhook**: Verifies image provenance, rejecting container images that lack a valid cryptographic SHA signature.
- **Gatekeeper**: An OPA-based admission controller that validates custom constraints on manifests before admission.

### Resource Validation Lifecycle

1. **API Request**: The API Server receives an admission review request.
2. **Policy Evaluation**: The controller executes validating rules against the manifest content.
3. **Response**: If validation fails, the API Server immediately rejects the request. If accepted, the transaction proceeds.
4. **ETCD Persistence**: Validated resources are written to etcd.

-----------------------------------------------------------------
📖 Consulted Sources:
  • Core_Kubernetes.pdf (Page 286)
  • Effective_Platform_Engineering.pdf (Page 127)
  • Effective_Platform_Engineering.pdf (Page 122)

🔬 Models & Engine Telemetry:
  • RAG Engine:       Hybrid ChromaDB + BM25 (Phase 1)
  • LLM Model:        qwen2.5:7b (Local Ollama Inference)
  • Embeddings:       sentence-transformers/all-MiniLM-L6-v2
  • Reranker:         cross-encoder/ms-marco-MiniLM-L-6-v2
  • Agentic Steps:    1 iteration(s) | 6 candidate chunks analyzed
-----------------------------------------------------------------
```

---

### Use Case 2: Platform Engineering & Developer Cognitive Load
*Demonstrating the 2-step agentic reflection loop: the LLM detects that the book describes "Accelerators and Paved Roads" rather than the exact term "Golden Path", executing a second retrieval step to provide grounded analysis.*

#### Command:
```powershell
.\.venv\Scripts\python.exe src/cli.py "Explain the Golden Path pattern in Platform Engineering and how it reduces cognitive load"
```

#### Generated Output:
```text
[Info] Using HybridRetriever (Phase 1: ChromaDB + BM25 + Reranker)

🔍 Querying technical library...

=================================================================
💡 Tutor Response:
=================================================================
The engineering literature describes this paradigm through concepts like "Paved Paths" and "Accelerators" aimed at optimizing developer experience and reducing cognitive load.

### Cognitive Load Reduction Mechanisms

1. **Architectural Accelerators & Scaffolding**
   - **Concept**: Automated onboarding kits providing predefined infrastructure templates and automated pipelines.
   - **Effect**: Eliminates the need for application developers to master raw cloud APIs, reducing extraneous cognitive load so they can focus on business logic.
   - **Reference**: "Effective_Platform_Engineering.pdf" (Page 106)

2. **Centralized Documentation & Developer Portals**
   - **Concept**: Unified internal developer portals (IDPs) that serve as single points of truth for infrastructure discovery and documentation.
   - **Effect**: Reduces search friction and context switching.
   - **Reference**: "Effective_Platform_Engineering.pdf" (Pages 104, 105)

3. **Data Democratization & Self-Service**
   - **Concept**: Enabling teams to provision dependencies self-sufficiently without manual ticket queues.
   - **Effect**: Shortens feedback loops and removes operational bottlenecks.
   - **Reference**: "Effective_Platform_Engineering.pdf" (Page 10)

-----------------------------------------------------------------
📖 Consulted Sources:
  • Effective_Platform_Engineering.pdf (Page 106)
  • Effective_Platform_Engineering.pdf (Page 105)
  • Effective_Platform_Engineering.pdf (Page 104)
  • Effective_Platform_Engineering.pdf (Page 10)

🔬 Models & Engine Telemetry:
  • RAG Engine:       Hybrid ChromaDB + BM25 (Phase 1)
  • LLM Model:        qwen2.5:7b (Local Ollama Inference)
  • Embeddings:       sentence-transformers/all-MiniLM-L6-v2
  • Reranker:         cross-encoder/ms-marco-MiniLM-L-6-v2
  • Agentic Steps:    2 iteration(s) | 8 candidate chunks analyzed
-----------------------------------------------------------------
```

---

### Use Case 3: Local Architecture Decision (Fine-Tuning vs RAG)
*Demonstrating technical trade-off evaluation comparing parameter adaptation against retrieval.*

#### Command:
```powershell
.\.venv\Scripts\python.exe src/cli.py "Compare fine-tuning vs RAG for local models"
```

#### Key Technical Takeaways Generated:
- **Fine-Tuning:** Ideal for teaching a model *style, formatting, and behavioral tone* (e.g. strict JSON outputs, domain-specific phrasing, or specialized code conventions). High compute cost; suffers from catastrophic forgetting and cannot be updated dynamically without retraining.
- **RAG (Retrieval-Augmented Generation):** Ideal for injecting *dynamic, factual, and proprietary knowledge* (e.g. thousands of pages of evolving books or internal documentation). Zero retraining cost; immediate updates on ingestion; produces verifiable citations with page numbers.
- **Decision Matrix:** For local workstation deployments, **Hybrid RAG is superior for factual recall and citation integrity**, while small LoRA adapters are reserved for specialized syntax adaptation.

---

### Use Case 4: Direct Lexical Code Extraction via MCP Tool
*Extracting raw, unaltered YAML manifests without generative rewriting via the `buscar_codigo_yaml` tool in `src/mcp_server.py`.*

#### Tool Call:
```python
buscar_codigo_yaml("CompositeResourceDefinition")
```

#### Output:
```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xpostgresqlinstances.database.example.org
spec:
  group: database.example.org
  names:
    kind: XPostgreSQLInstance
    plural: xpostgresqlinstances
  claimNames:
    kind: PostgreSQLInstance
    plural: postgresqlinstances
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              parameters:
                type: object
                properties:
                  storageGB:
                    type: integer
```
*(Exact syntactic match recovered from the books via BM25 in < 25 ms, bypassing the generative LLM to prevent formatting corruption).*

---

### Use Case 5: Multi-MCP Certification Prep Session
*Open WebUI orchestrating `study-cybercirujas` and `rag-tutor` in a single session.*

1. **User Prompt:**  
   *"I'm preparing for the CNCF CKA exam on Network Policies. Give me the official exam objective and exercises from Cybercirujas, and explain the deep pod-selector egress rules with the engineering books."*
2. **Tool 1 (`study-cybercirujas`):**  
   Calls `get_topic("cka", "4.2", "en")` $\rightarrow$ Fetches the official CNCF objective, exam weighting, and the Docker break-and-fix lab.
3. **Tool 2 (`rag-tutor`):**  
   Calls `consultar_libros_manning("Kubernetes NetworkPolicy podSelector egress rules")` $\rightarrow$ Fetches exact architectural explanations and verified YAML manifests from **Core Kubernetes** with exact page numbers.
4. **Synthesis:**  
   The user receives a complete study module: official syllabus context, practical break-and-fix lab, and battle-tested book theory.
