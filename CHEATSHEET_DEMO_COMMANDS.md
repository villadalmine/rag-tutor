# 🚀 Cheatsheet de Comandos & Guía de Demostración: Tri-MCP Sovereign Stack

Esta guía práctica contiene todos los comandos, endpoints de verificación, llamadas `curl`, validaciones de hardware (GPU vs CPU) y pasos operativos para realizar la demostración completa del ecosistema soberano local **Tri-MCP**.

---

## 📑 Índice de Navegación Rápida
1. [Mapa de Servicios, Puertos & Enlaces Web](#1-mapa-de-servicios-puertos--enlaces-web)
2. [Verificación de Hardware: GPU AMD Radeon vs CPU Dell](#2-verificación-de-hardware-gpu-amd-radeon-vs-cpu-dell)
3. [Cheatsheet de Comandos cURL & PowerShell](#3-cheatsheet-de-comandos-curl--powershell)
   - [3.1 Healthchecks de Infraestructura](#31-healthchecks-de-infraestructura)
   - [3.2 Monitoreo del Clúster Tri-MCP (/mcp/status)](#32-monitoreo-del-clúster-tri-mcp-mcpstatus)
   - [3.3 Pruebas de Diagnóstico en Vivo (/mcp/test)](#33-pruebas-de-diagnóstico-en-vivo-mcptest)
   - [3.4 Consulta Agéntica Tri-MCP (/chat)](#34-consulta-agéntica-tri-mcp-chat)
4. [Guía de Integración con Open WebUI](#4-guía-de-integración-con-open-webui)
5. [Guía para VS Code, Cursor y OpenCode / opencodev2](#5-guía-para-vs-code-cursor-y-opencode--opencodev2)
6. [Cómo Arrancar Todo desde Cero (Cold Start)](#6-cómo-arrancar-todo-desde-cero-cold-start)

---

## 1. Mapa de Servicios, Puertos & Enlaces Web

| Servicio | Puerto Local | URL Interactiva | Función Principal |
| :--- | :--- | :--- | :--- |
| **Open WebUI** | `:3000` | [http://localhost:3000](http://localhost:3000) | Interfaz web de usuario y chat con modelos locales y herramientas Python. |
| **RAG Tutor Gateway API** | `:8000` | [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger) | Orquestador Tri-MCP, Hybrid RAG (ChromaDB + BM25 + Reranker) y GraphRAG KùzuDB. |
| **Study Cybercirujas** | `:8080` | [http://localhost:8080](http://localhost:8080) / [Catalog API](http://localhost:8080/api/catalog) | 42 temarios oficiales (CKA, CKAD, CKS, CNPE), laboratorios interactivos y syllabus. |
| **Ollama LLM Engine** | `:11434` | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | Motor de inferencia local ejecutado sobre GPU AMD Radeon RX 6800. |

---

## 2. Verificación de Hardware: GPU AMD Radeon vs CPU Dell

En tu entorno conviven la CPU host del equipo Dell y una GPU dedicada **AMD Radeon RX 6800 con 16 GB de VRAM**. La inferencia de los LLMs corre **100% acelerada por hardware en la GPU**, liberando a la CPU para atender tareas I/O de red y orquestación del sistema operativo.

### Comando para verificar en qué procesador corre Ollama:

#### En Linux / macOS / Git Bash / WSL:
```bash
curl -s http://localhost:11434/api/ps | jq '.models[] | {name, size_vram, runner}'
```

#### En Windows PowerShell:
```powershell
(Invoke-RestMethod -Uri "http://localhost:11434/api/ps").models | Select-Object name, size_vram, runner | Format-Table -AutoSize
```

### Salida esperada y confirmada en vivo (100% GPU):

Al consultar `ollama ps`:
```text
NAME             ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL
qwen3:4b-fast    dc0292753ff4    5.1 GB    100% GPU     16384      llamacpp    4 minutes from now
qwen2.5:7b       845dbda0ea48    6.6 GB    100% GPU     32768      llamacpp    4 minutes from now
```

> [!NOTE]
> - **`qwen3:4b-fast`**: Creado con ventana de contexto optimizada de 16k tokens ([Modelfile.qwen3-fast](Modelfile.qwen3-fast)). Ocupa solo 5.1 GB de VRAM y alcanza una velocidad de **101.8 tokens/segundo** en la **AMD Radeon RX 6800**.
> - **`qwen2.5:7b`**: Modelo de 7B de alta solidez arquitectónica, con ventana de 32k tokens. Ocupa 6.6 GB de VRAM y corre también en 100% GPU.
> - **Ambos modelos en simultáneo**: 5.1 GB + 6.6 GB = 11.7 GB, conviviendo holgadamente dentro de los 16 GB de VRAM de la placa de video sin hacer swap a la CPU Dell.

---

## 3. Cheatsheet de Comandos cURL & PowerShell

### 3.1 Healthchecks de Infraestructura

#### Verificar RAG Tutor Gateway (:8000):
```bash
# cURL
curl -s http://localhost:8000/health | jq

# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json
```
*Salida esperada:*
```json
{
  "status": "online",
  "service": "rag-tutor",
  "retriever_type": "hybrid",
  "ollama_model": "qwen2.5:7b",
  "chroma_dir_exists": true,
  "bm25_index_exists": true,
  "knowledge_graph_exists": true
}
```

#### Verificar Study Cybercirujas (:8080):
```bash
# cURL
curl -s http://localhost:8080/api/catalog | jq '.[0:3]'

# PowerShell
(Invoke-RestMethod -Uri "http://localhost:8080/api/catalog")[0..2] | ConvertTo-Json
```

#### Verificar Open WebUI (:3000):
```bash
curl -s http://localhost:3000/health
# Retorna: {"status": true}
```

---

### 3.2 Monitoreo del Clúster Tri-MCP (`/mcp/status`)

Inspecciona en tiempo real el estado de los 3 servidores MCP, herramientas disponibles y métricas de índices:

```bash
# cURL
curl -s http://localhost:8000/mcp/status | jq
```

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/mcp/status" | ConvertTo-Json -Depth 5
```

*Salida esperada:*
```json
{
  "tri_mcp_operational": true,
  "active_architecture": "The Cloud Native Trifecta (Study + K8s-Docs + RAG-Tutor)",
  "servers": {
    "study_cybercirujas": {
      "status": "online",
      "mode": "local",
      "url": "http://127.0.0.1:8080",
      "total_certifications": 42,
      "tools": ["list_certs", "get_syllabus", "get_topic", "search_topics"]
    },
    "k8s_docs_mcp": {
      "status": "online",
      "store_populated": true,
      "total_doc_sections": 7,
      "total_manifests": 9,
      "tools": ["search_k8s_docs", "get_canonical_manifest", "check_api_version"]
    },
    "rag_tutor": {
      "status": "online",
      "retriever_engine": "hybrid",
      "vector_db": "ChromaDB",
      "lexical_index": "BM25",
      "graph_rag": "KùzuDB Cypher",
      "tools": ["search_books", "kuzu_graph_traversal", "agentic_reasoning"]
    }
  }
}
```

---

### 3.3 Historial y Logs de Auditoría en Vivo (`/mcp/logs`)

Inspecciona en tiempo real las consultas que recibe el Gateway, qué herramientas se ejecutaron, la IP del cliente (Docker o localhost), y la latencia exacta en milisegundos:

```bash
# cURL
curl -s http://localhost:8000/mcp/logs | jq
```

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/mcp/logs" | ConvertTo-Json -Depth 5
```

---

### 3.4 Pruebas de Diagnóstico en Vivo (`/mcp/test`)

El endpoint `/mcp/test` implementa **extracción determinística de Kinds de Kubernetes** y **filtrado de stop words conversacionales**, permitiendo ingresar preguntas en lenguaje natural tanto en inglés como en español.

#### Caso 1: Consulta de Lenguaje Natural con Extracción de Múltiples Manifiestos de Pod
Prueba cómo el sistema ignora las palabras de relleno (*three*, *example*, *how*, *create*, *theory*, *works*), extrae el Kind `Pod`, valida la apiVersion `v1`, devuelve 3 manifiestos canónicos de `kubernetes.io` y enlaza el objetivo de examen `CKA 3.5`.

```bash
# cURL
curl -s -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{
    "target": "all",
    "query": "three example how i can create a pod yaml definition and a theory how works"
  }' | jq
```

```powershell
# PowerShell
$body = @{
  target = "all"
  query = "three example how i can create a pod yaml definition and a theory how works"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/mcp/test" -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

*Salida obtenida:*
```json
{
  "target": "all",
  "query": "three example how i can create a pod yaml definition and a theory how works",
  "diagnostic_results": {
    "study_cybercirujas": {
      "status": "SUCCESS",
      "detected_kind": "Pod",
      "matched_objective": "CKA 3.5 - Configure Pod admission and scheduling (limits, node affinity, etc.)",
      "certification": "Certified Kubernetes Administrator (CKA)",
      "domain": "3 - Workloads and Scheduling",
      "weight": 2.5,
      "has_lab": true
    },
    "k8s_docs_mcp": {
      "status": "SUCCESS",
      "detected_kind": "Pod",
      "api_version_check": [
        "### Authoritative Kubernetes API Check: `Pod`",
        "- **Current Stable apiVersion:** `v1`",
        "- **Status:** `STABLE`"
      ],
      "manifest_found": true,
      "manifests_count": 3,
      "manifest_preview": [
        "### Canonical Kubernetes Manifest(s) for Kind: `Pod`",
        "#### Manifest 1: `nginx-pod-single` (v1) [Probes + Resources]",
        "#### Manifest 2: `multi-container-sidecar-pod` (v1) [Sidecar Pattern]",
        "#### Manifest 3: `pod-with-config-and-secret` (v1) [ConfigMap/Secret Env]"
      ]
    },
    "rag_tutor": {
      "status": "SUCCESS",
      "test_term": "pod",
      "retriever_type": "hybrid",
      "ollama_model": "qwen2.5:7b",
      "pipeline_status": "Vector DB & Hybrid Reranking ready"
    }
  }
}
```

#### Caso 2: Diagnóstico Específico de Políticas de Admisión (CEL)
```bash
# cURL
curl -s -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{"target": "all", "query": "validating admission policy cel"}' | jq
```

#### Caso 3: Diagnóstico de Redes y Políticas de Red
```bash
# cURL
curl -s -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{"target": "all", "query": "network policy default deny"}' | jq
```

---

### 3.4 Consulta Agéntica Tri-MCP (`/chat`)

Ejecuta el ciclo agéntico completo:
1. Consulta **`study-cybercirujas`** para inyectar temario oficial y laboratorios.
2. Consulta **`k8s-docs-mcp`** para inyectar apiVersion y manifiesto YAML verificado sin alteraciones del LLM.
3. Consulta **`rag-tutor`** recuperando literatura especializada (libros Manning) y relaciones del grafo KùzuDB.
4. Sintetiza la respuesta en el modelo local `qwen2.5:7b` corriendo en la GPU Radeon.

```bash
# cURL
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explícame cómo funciona etcd en Kubernetes y cómo se comunica con los demás componentes del control plane",
    "orchestrate_tri_mcp": true
  }' | jq
```

```powershell
# PowerShell
$body = @{
  question = "Explícame cómo funciona etcd en Kubernetes y cómo se comunica con los demás componentes del control plane"
  orchestrate_tri_mcp = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

---

## 4. Guía de Integración con Open WebUI

La integración no requiere configurar servidores OpenAPI complejos; se realiza mediante una clase estándar de Python en Open WebUI.

### Paso 1: Crear la Herramienta en Open WebUI
1. Abre tu navegador en [http://localhost:3000](http://localhost:3000).
2. Ve a: **Espacio de Trabajo (Workspace) ➔ Herramientas (Tools) ➔ `+` (Crear Herramienta)**.
3. Copia y pega el código del archivo [openwebui_tool_tri_mcp.py](openwebui_tool_tri_mcp.py):

```python
"""
title: Cloud Native Tri-MCP Tutor
author: Cybercirujas
version: 1.2.0
"""
import requests

class Tools:
    def __init__(self):
        # URL interna resoluble desde el contenedor Docker de Open WebUI
        self.gateway_url = "http://host.docker.internal:8000"

    def query_tri_mcp_tutor(self, question: str) -> str:
        """Consulta al Tutor Soberano Cloud Native (rag-tutor + study-cybercirujas + k8s-docs-mcp)."""
        url = f"{self.gateway_url}/chat"
        payload = {"question": question, "orchestrate_tri_mcp": True}
        try:
            resp = requests.post(url, json=payload, timeout=90.0)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "")
                sources = "\n".join([f"- {s}" for s in data.get("sources", [])])
                enrichment = data.get("mcp_enrichment", {})
                parts = [answer]
                if sources:
                    parts.append(f"\n\n### 📖 Fuentes Oficiales Consultadas:\n{sources}")
                if enrichment.get("study_objective"):
                    parts.append(f"\n- 🎯 **Objetivo de Certificación:** `{enrichment['study_objective']}`")
                if enrichment.get("k8s_api_check"):
                    parts.append(f"\n- 🛡️ **Verificación API K8s:** `{enrichment['k8s_api_check']}`")
                return "\n".join(parts)
            return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"Error de conexión con RAG Tutor Gateway: {str(e)}"

    def check_mcp_cluster_status(self) -> str:
        """Verifica el estado de conexión de los 3 servidores MCP."""
        url = f"{self.gateway_url}/mcp/status"
        try:
            resp = requests.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                servers = data.get("servers", {})
                res = [f"### Estado de la Trifecta MCP (Operativo: {data.get('tri_mcp_operational')})\n"]
                for name, s in servers.items():
                    res.append(f"- **{name}**: `{s.get('status')}` | Tools: [{', '.join(s.get('tools', []))}]")
                return "\n".join(res)
            return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"Error de conexión: {str(e)}"

    def test_mcp_integration(self, query: str = "pod") -> str:
        """Ejecuta un diagnóstico en vivo sobre los tres MCP."""
        url = f"{self.gateway_url}/mcp/test"
        try:
            resp = requests.post(url, json={"target": "all", "query": query}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json().get("diagnostic_results", {})
                study = data.get("study_cybercirujas", {})
                k8s = data.get("k8s_docs_mcp", {})
                rag = data.get("rag_tutor", {})
                return f"Diagnóstico `{query}`:\n- Study: {study.get('status')} ({study.get('matched_objective')})\n- K8s Docs: {k8s.get('status')} (Kind: {k8s.get('detected_kind')}, Manifests: {k8s.get('manifests_count')})\n- RAG Tutor: {rag.get('status')} ({rag.get('retriever_type')})"
            return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"Error de conexión: {str(e)}"
```
4. Haz clic en **Guardar**.

### Paso 2: Crear el Modelo en Open WebUI
1. Ve a: **Espacio de Trabajo (Workspace) ➔ Modelos (Models) ➔ `+` (Crear Modelo)**.
2. Completa los campos:
   - **Nombre:** `Tutor Cloud Native (Tri-MCP)`
   - **Modelo Base (desde):** `qwen2.5:7b` (o `qwen3:4b`).
   - **Descripción:** `Tutor de Arquitectura Cloud Native fundamentado en temarios CNCF, specs de kubernetes.io y libros de ingeniería.`
   - **Prompt del sistema:**
     ```text
     Eres un Arquitecto de Plataformas Senior e Instructor Cloud Native.
     Tienes acceso a la herramienta 'Cloud Native Tri-MCP Tutor'.
     Siempre que el usuario consulte sobre Kubernetes, certificaciones (CKA, CKAD, CKS, CNPE),
     arquitectura o manifiestos YAML, invoca 'query_tri_mcp_tutor' para validar tu respuesta
     con fuentes oficiales y evitar cualquier alucinación de API.
     ```
   - **Herramientas:** Tilda la casilla de **`Cloud Native Tri-MCP Tutor`**.
3. Guarda el modelo y abre un nuevo chat seleccionándolo.

---

## 5. Guía para VS Code, Cursor y OpenCode / opencodev2

El archivo de configuración [mcp_servers_config.json](mcp_servers_config.json) ya define los 3 servidores para herramientas asistidas por IA:

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
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "."
    }
  }
}
```

- **En Cursor:** Pega este bloque en `.cursor/mcp.json`.
- **En VS Code (con Cline / Roo Code / Continue):** Agrega las 3 entradas en la pestaña *MCP Servers Settings*.
- **En OpenCode / opencodev2:** Apunta la configuración MCP a este JSON.

---

## 6. Cómo Arrancar Todo desde Cero (Cold Start)

Si reinicias tu máquina o deseas arrancar los servicios en otra terminal, sigue este orden:

```bash
# 1. Asegurar Ollama activo con el modelo en GPU
ollama run qwen2.5:7b ""

# 2. Levantar study-cybercirujas en puerto 8080 (en su propio repo)
cd /path/to/study-cybercirujas
python -m uvicorn teach.api:app --host 0.0.0.0 --port 8080

# 3. Levantar RAG Tutor Gateway en puerto 8000
cd /path/to/rag-tutor
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# 4. Levantar contenedor Docker de Open WebUI (si no está corriendo)
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -e WEBUI_AUTH=False \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name open-webui ghcr.io/open-webui/open-webui:main
```

---

## 📚 Documentación Complementaria en el Repositorio
- [DEMO_RUNBOOK_ES.md](DEMO_RUNBOOK_ES.md): Guía paso a paso en español para la presentación y audiencia.
- [DEMO_RUNBOOK_EN.md](DEMO_RUNBOOK_EN.md): Runbook técnico completo en inglés.
- [DEMO_RUNBOOK_STUDY_OPENWEBUI.md](DEMO_RUNBOOK_STUDY_OPENWEBUI.md): Alias directo de DEMO_RUNBOOK_EN.md.
- [HOW_TO_MULTI_MCP_101.md](HOW_TO_MULTI_MCP_101.md): Explicación pedagógica de cómo el agente decide a qué servidor consultar sin colisiones.
- [RESEARCH_AND_LESSONS_LEARNED.md](RESEARCH_AND_LESSONS_LEARNED.md): Arquitectura detallada, superación de cuellos de botella y diseño determinístico.
