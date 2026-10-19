# Real-World Use Cases, Generated Outputs & Setup Guide

This document provides a comprehensive walkthrough of **how the system was built and executed**, along with **unfiltered real-world outputs** produced on local hardware across multiple technical engineering domains.

---

## 1. How I Made It Work: From Zero to Running System

The entire system was designed and verified to run **100% locally on consumer hardware without external API subscriptions or cloud dependencies**.

### Step 1: Virtual Environment & Dependency Installation
Using Python 3.11:
```bash
# Create isolated environment
python -m venv .venv

# Activate environment
source .venv/bin/activate

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
```bash
# The directory is empty by default
ls -la books/
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
```bash
python src/ingest.py
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
```bash
python src/cli.py "Explain what an Admission Controller is in Kubernetes and how it validates resources"
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
```bash
python src/cli.py "Explain the Golden Path pattern in Platform Engineering and how it reduces cognitive load"
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
```bash
python src/cli.py "Compare fine-tuning vs RAG for local models"
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
buscar_codigo_yaml("kind: NetworkPolicy")
```

#### Output:
```yaml
#### Match 1 [Core_Kubernetes.pdf (Page 150)]:
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: web
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - ports:
    - port: 80
```
*(Exact syntactic match recovered from the books via BM25 in < 25 ms, bypassing the generative LLM to prevent formatting corruption).*

---

### Use Case 5: Verified Live Multi-MCP Certification Prep Session
*Live execution connecting `study-cybercirujas` MCP tools with `rag-tutor` in both Phase 1 (Hybrid) and Phase 2 (GraphRAG).*

#### Terminal Execution:
```bash
python test_multi_mcp_live.py
```

#### Real Live Output:
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

---

## 3. Comparative Benchmark: Phase 1 (Hybrid RAG) vs. Phase 2 (GraphRAG / Omnigraph)

This section demonstrates how the engine responds in each operational mode when queried with the exact same architectural question:
> **Question:** *"What is an Internal Developer Platform (IDP) and how does it relate to Self-Service?"*

> [!NOTE]
> **Why `knowledge_graph.json` is tracked in the repository & why you do NOT need this specific data as-is:**
> - **Purpose:** `knowledge_graph.json` is a lightweight (~7 KB) **seed ontology template** demonstrating how Phase 2 GraphRAG models entities (`Discipline`, `System`, `Pattern`, `Architecture`) and relationships (`DELIVERS`, `ENABLES`, `USES`, `RETRIEVES_FROM`).
> - **Zero Copyrighted Book Text:** Unlike `chroma_db/` and `bm25_index.pkl` (which contain extracted text chunks and are properly ignored via `.gitignore`), `knowledge_graph.json` contains only conceptual metadata.
> - **Immediate Out-of-the-Box Execution:** Anyone cloning the repo can test GraphRAG locally via `OmnigraphRetriever` without first provisioning an external database or running manual generation scripts.
> - **Fully Customizable for ANY Domain:** You do **not** need to use this specific ontology. If your library covers Database Internals, Frontend Development, Rust Systems, or Cybersecurity, you can customize entity definitions in [`src/ingest_graph.py`](src/ingest_graph.py) and regenerate `knowledge_graph.json` with `python src/ingest_graph.py`.

---

### Case A: Phase 1 Output (Hybrid ChromaDB + BM25 + Cross-Encoder)

#### Command:
```bash
python src/cli.py "What is an Internal Developer Platform (IDP) and how does it relate to Self-Service?"
```

#### Terminal Output:
```text
[Info] Using HybridRetriever (Phase 1: ChromaDB + BM25 + Reranker)

🔍 Querying technical library...

=================================================================
💡 Tutor Response:
=================================================================
An Internal Developer Platform (IDP) is a critical component in platform engineering, designed to simplify and automate the software development lifecycle for internal development teams. According to the context provided in "Effective Platform Engineering," an IDP serves as a layer between developers and the underlying infrastructure, offering self-service capabilities and abstractions that streamline development and deployment processes.

### Key Characteristics of an IDP

1. **Self-Service Capabilities**: IDPs provide developers with self-service interfaces, enabling them to manage applications and environments independently. For example, a developer can deploy a new microservice using a self-service portal with minimal interaction with the operations team. This reduces dependency on other teams and minimizes context switching, allowing developers to focus on building features rather than navigating complex systems.

2. **Standardization and Automation**: IDPs enforce standardization through templates and policies, promoting best practices and compliance. Automation is a core aspect, with workflows streamlined through CI/CD integration and automated provisioning. This minimizes manual intervention and ensures consistency and accuracy in the development process.

3. **Governance and Compliance**: IDPs are designed to ensure that development activities adhere to organizational standards and compliance requirements. They provide a structured approach to governance, helping to maintain high engineering quality and operational resiliency.

4. **Enhanced Productivity and Satisfaction**: By providing a centralized hub for documentation, APIs, tooling, and collaboration resources, IDPs reduce the time developers spend on administrative tasks. This leads to increased productivity and job satisfaction.

### Relation to Self-Service

Self-service is a fundamental principle of IDPs. The term "self-service" in this context refers to the ability of developers to manage their applications and environments independently, without the need for extensive interaction with other teams. This is achieved through the provision of intuitive and user-friendly interfaces, such as the self-service portal mentioned in the context.

For instance, when a developer needs to deploy a new microservice, they can use the self-service portal to configure and deploy it with a few clicks. This process is automated and standardized, ensuring that the deployment adheres to best practices and organizational policies. The self-service nature of IDPs not only enhances developer productivity but also aligns with the broader goals of DevOps and platform engineering, which emphasize agility, efficiency, and collaboration.

### Example from Epetech

The context from Epetech illustrates the benefits of an IDP in a real-world scenario. Epetech's engineering platform, known as LaunchPad, provided self-service capabilities for deploying applications and managing environments. This unified platform empowered developers, reducing dependency on other teams and accelerating the development process. As a result, developers could focus on building features rather than navigating complex systems or searching for information, enhancing productivity and satisfaction.

In summary, an IDP is a self-service platform that simplifies and automates the software development lifecycle, enabling developers to manage applications and environments independently while adhering to organizational standards and best practices. The self-service aspect is crucial in reducing dependency on other teams and streamlining the development process, ultimately leading to increased productivity and satisfaction.

-----------------------------------------------------------------
📖 Consulted Sources:
  • Effective_Platform_Engineering.pdf (Page 402)
  • Effective_Platform_Engineering.pdf (Page 386)
  • Effective_Platform_Engineering.pdf (Page 379)
  • Effective_Platform_Engineering.pdf (Page 2)

🔬 Models & Engine Telemetry:
  • RAG Engine:       Hybrid ChromaDB + BM25 (Phase 1)
  • LLM Model:        qwen2.5:7b (Local Ollama Inference)
  • Embeddings:       sentence-transformers/all-MiniLM-L6-v2
  • Reranker:         cross-encoder/ms-marco-MiniLM-L-6-v2
  • Agentic Steps:    1 iteration(s) | 6 candidate chunks analyzed
-----------------------------------------------------------------
```

---

### Case B: Phase 2 Output (GraphRAG / Omnigraph Engine)

In Phase 2, the engine detects entities from the ontology (`internal-developer-platform` and `self-service`), traverses `knowledge_graph.json`, extracts the ontological edge `(Internal Developer Platform (IDP)) ──[ENABLES]──► (Self-Service)`, applies a score bonus to topologically connected chunks, and injects the relational topology into the LLM context.

#### Command:
```bash
RETRIEVER_TYPE="omnigraph" python src/cli.py "What is an Internal Developer Platform (IDP) and how does it relate to Self-Service?"
```

#### Terminal Output:
```text
[Info] Using OmnigraphRetriever (Phase 2: GraphRAG)

🔍 Querying technical library...

=================================================================
💡 Tutor Response:
=================================================================
An Internal Developer Platform (IDP) is a critical component in platform engineering, designed to simplify and automate the software development lifecycle. According to the context from "Effective Platform Engineering" (Page 402), an IDP provides self-service interfaces to tools and services for infrastructure, deployment, security, observability, and governance. This platform is built to reduce the complexity that developers face, particularly in mastering technologies like Kubernetes, and to enable them to focus on building features rather than managing infrastructure details.

### How an IDP Relates to Self-Service

The relationship between an IDP and self-service is central to the platform's design and functionality. The context explicitly states that an IDP "ENABLES" self-service (Page 402). This means that the IDP provides a user-friendly interface and tools that allow developers to manage their applications and environments independently, without needing to rely on other teams. This self-service capability is a key feature that enhances developer productivity and satisfaction.

#### Key Components of Self-Service in an IDP

1. **Self-Service Interfaces**: The IDP offers a centralized hub for documentation, APIs, tooling, and collaboration resources. This hub serves as a self-service portal where developers can find and use the necessary tools and services they need to develop and deploy applications.

2. **Automated Workflows**: The IDP includes automated application workflows and integrated CI/CD pipelines. These automated processes reduce the need for manual intervention, allowing developers to deploy new services or update existing ones with minimal effort.

3. **Standardized Service Templates**: Preconfigured setups for common microservices ensure best practices are followed across teams. These templates reduce setup time and provide a solid foundation for new services, making it easier for developers to get started.

4. **User-Friendly Interface**: An intuitive portal for managing services, environments, and other resources ensures that developers can easily navigate and use the platform. This user-friendly design minimizes the learning curve and enhances the overall developer experience.

#### Example from Epetech (Page 379)

Epetech’s LaunchPad, an internal developer platform, exemplifies the self-service capabilities of an IDP. Developers can use LaunchPad’s self-service portal to configure and deploy new microservices with a few clicks, without involving the operations team. This example highlights how an IDP can significantly reduce the time and effort required for deployment, thereby increasing developer productivity.

### Conclusion

In summary, an Internal Developer Platform (IDP) is a key enabler of self-service in the software development lifecycle. By providing self-service interfaces, automated workflows, standardized service templates, and a user-friendly interface, an IDP simplifies the development process and enhances developer productivity. The relationship between an IDP and self-service is thus fundamental, as the IDP's primary goal is to empower developers to manage their applications and environments independently, accelerating the development process and improving overall efficiency.

**References:**
- Effective Platform Engineering, Chankramath, Cheneweth, Oliver, Alvarez, Foreword by Kief Morris, ISBN-13: 978-1-63343-649-7, pp. 363, 379, 402.

-----------------------------------------------------------------
📖 Consulted Sources:
  • Effective_Platform_Engineering.pdf (Page 402)
  • Effective_Platform_Engineering.pdf (Page 386)
  • Effective_Platform_Engineering.pdf (Page 363)
  • Effective_Platform_Engineering.pdf (Page 379)

🔬 Models & Engine Telemetry:
  • RAG Engine:       GraphRAG Omnigraph (Phase 2)
  • LLM Model:        qwen2.5:7b (Local Ollama Inference)
  • Embeddings:       sentence-transformers/all-MiniLM-L6-v2
  • Reranker:         cross-encoder/ms-marco-MiniLM-L-6-v2
  • Agentic Steps:    1 iteration(s) | 6 candidate chunks analyzed
-----------------------------------------------------------------
```

---

### Comparative Takeaway

| Dimension | Phase 1: Hybrid Retrieval | Phase 2: GraphRAG / Omnigraph |
| :--- | :--- | :--- |
| **Retrieval Strategy** | Vector cosine similarity + BM25 lexical tokens + Cross-Encoder rerank. | Entity recognition + BFS ontology traversal + Vector + BM25 + Topology Header. |
| **Relational Awareness** | Unaware of abstract relationships; relies purely on textual co-occurrence in chunks. | Directly aware of directional relationships (`IDP ──[ENABLES]──► Self-Service`). |
| **Response Framing** | Descriptive synthesis of text passages. | Structured architectural analysis explaining exact relationship mechanics. |
| **Dependencies** | Requires ChromaDB and local embedding/reranking weights. | Runs either via local in-memory graph (`knowledge_graph.json`) or remote Omnigraph container. |

