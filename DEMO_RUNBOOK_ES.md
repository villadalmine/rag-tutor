# 🚀 Guía de Demostración: Plataforma Cloud Native Soberana & Modelo Tri-MCP

> **Runbook Completo de Demostración y Despliegue en Vivo**  
> Guía paso a paso para ejecutar, presentar y orquestar **study-cybercirujas**, **k8s-docs-mcp**, **rag-tutor**, **Ollama** y **Open WebUI** en un entorno 100% local, soberano y sin dependencias cloud.

---

## 🧭 Resumen Ejecutivo: La Trifecta Cloud Native

La capacitación moderna en ingeniería de plataformas requiere tres capas soberanas y complementarias:

```
                      ┌────────────────────────────────────────┐
                      │             USUARIO / CLIENTE          │
                      │  Open WebUI / Claude Desktop / Cursor  │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
     ┌────────────────────────┐┌────────────────────────┐┌────────────────────────┐
     │   study-cybercirujas   ││      k8s-docs-mcp      ││       rag-tutor        │
     │     (Servidor MCP)     ││     (Servidor MCP)     ││  (Gateway REST + MCP)  │
     ├────────────────────────┤├────────────────────────┤├────────────────────────┤
     │ "El Temario y los Labs"││ "La Verdad de la API"  ││ "La Arquitectura RAG"  │
     │                        ││                        ││                        │
     │ • 38 Certificaciones   ││ • Docs kubernetes.io   ││ • Libros Manning       │
     │ • 726 Objetivos Examen ││ • OpenAPI v3 Specs     ││ • KùzuDB GraphRAG      │
     │ • Labs Break/Fix       ││ • YAMLs Canónicos      ││ • Loop Agéntico        │
     │ • Sin Tokens de Pago   ││ • Cero Alucinaciones   ││ • Reranker CrossEncoder│
     └────────────────────────┘└────────────────────────┘└────────────────────────┘
                  ▲                       ▲                       ▲
                  └───────────────────────┼───────────────────────┘
                                          │ Inferencia Local y Ejecución Offline
                                          ▼
                               ┌────────────────────────┐
                               │      MOTOR OLLAMA      │
                               │  qwen2.5:7b / bge-m3   │
                               │ (100% Soberano en GPU) │
                               └────────────────────────┘
```

| Motor | Rol Principal | Material de Origen | Protocolo | Puerto / Transporte |
| :--- | :--- | :--- | :--- | :--- |
| **`study-cybercirujas`** | Autoridad de Temarios y Labs | Syllabi oficiales CNCF/LPI/LF + labs break-fix | REST + Stdio MCP | [http://localhost:8080](http://localhost:8080) / `teach.mcp_server` |
| **`k8s-docs-mcp`** | Autoridad de Especificación | Upstream kubernetes/website + OpenAPI v3 | Stdio MCP | `k8s_docs_mcp.server` |
| **`rag-tutor`** | Autoridad de Arquitectura & Gateway | Libros técnicos Manning + Grafo KùzuDB | REST + KùzuDB Cypher | [http://localhost:8000](http://localhost:8000) / `src.api:app` |
| **`Open WebUI`** | Interfaz Unificada Soberana | Chat multi-agente, Herramientas OpenAPI y RAG | Web / HTTP | [http://localhost:3000](http://localhost:3000) |
| **`Ollama`** | LLM Local y Embeddings | Pesos locales (`qwen2.5:7b`, `bge-m3`) | REST API | [http://localhost:11434](http://localhost:11434) |

---

## ⚡ Dashboard de Servicios en Vivo (Pre-Inicializados)

Todos los servicios requeridos se encuentran **activos en segundo plano** y listos para la demo:

| Servicio | Enlace Directo / URL | Endpoint de Salud | Estado |
| :--- | :--- | :--- | :--- |
| **Plataforma Web Study** | [http://localhost:8080](http://localhost:8080) | [http://localhost:8080/healthz](http://localhost:8080/healthz) | **ACTIVO (200 OK)** |
| **Swagger API de Study** | [http://localhost:8080/docs](http://localhost:8080/docs) | [http://localhost:8080/api/catalog](http://localhost:8080/api/catalog) | **ACTIVO (200 OK)** |
| **RAG Tutor Gateway API** | [http://localhost:8000](http://localhost:8000) | [http://localhost:8000/health](http://localhost:8000/health) | **ACTIVO (200 OK)** |
| **Panel de Estado Tri-MCP** | [http://localhost:8000/mcp/status](http://localhost:8000/mcp/status) | [http://localhost:8000/docs](http://localhost:8000/docs) | **ACTIVO (200 OK)** |
| **Open WebUI (Chat UI)** | [http://localhost:3000](http://localhost:3000) | [http://localhost:3000/api/config](http://localhost:3000/api/config) | **ACTIVO (200 OK)** |
| **Ollama Local Engine** | [http://localhost:11434](http://localhost:11434) | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | **ACTIVO (200 OK)** |

---

## 📋 Guía Paso a Paso de la Demostración

### Parte 1: Recorrido por `study-cybercirujas` (Plataforma Educativa)

`study-cybercirujas` es una plataforma self-service de certificaciones IT basada en un corpus puro de Markdown/YAML, con seguimiento automatizado de cambios en los temarios oficiales, soporte multi-idioma (ES, EN, FR, DE, ZH, JA, PT) y laboratorios prácticos break/fix.
Repositorio en GitHub: [https://github.com/villadalmine/study-cybercirujas](https://github.com/villadalmine/study-cybercirujas)

#### 1.1 Abrir la Plataforma Web Interactiva
Haz clic en el enlace para abrirla directamente en tu navegador:  
👉 **[Abrir Study Cybercirujas (http://localhost:8080)](http://localhost:8080)**

- **Puntos clave a mostrar en la demo:**
  1. **Catálogo de 38 Certificaciones:** Organizadas por categorías:
     - Cloud Native: `CKA`, `CKAD`, `CKS`, `KCNA`, `KCSA`, `CNPE`
     - Linux & Sistemas: `LPI 010-160`, `LPIC-1`, `LPIC-2`, `LPIC-3`
     - Infraestructura como Código: `Terraform Associate (004)`, `Terraform Advanced`
     - IA & Protocolos: `Model Context Protocol Associate (MCPA)`, `NVIDIA NCA/NCP`
  2. **Exploración de Temas:** Entra a **CKA** o **CNPE** y selecciona un tema (ej. *Domain 3.4 - Using Policy Engines and Admission Controllers*).
  3. **Laboratorios Break/Fix On-Demand:** Muestra que cada tema cuenta con un escenario de incidente real y un script bash reproducible (`break_fix.sh --break` y `--check`) listo para inyectar y verificar en clusters locales.

#### 1.2 Probar los Endpoints REST de la Plataforma
Puedes hacer clic directamente en estos enlaces o probarlos con cURL:
- **Catálogo Completo:** [http://localhost:8080/api/catalog](http://localhost:8080/api/catalog)
- **Búsqueda por palabra clave (ej. admission):** [http://localhost:8080/api/search?q=admission](http://localhost:8080/api/search?q=admission)
- **Detalle de Objetivo (CNPE 3.4 en inglés):** [http://localhost:8080/api/certs/cnpe/topics/3.4?lang=en](http://localhost:8080/api/certs/cnpe/topics/3.4?lang=en)
- **Documentación Interactiva Swagger:** [http://localhost:8080/docs](http://localhost:8080/docs)

```bash
# Consultar catálogo
curl -s http://localhost:8080/api/catalog | jq 'keys'

# Buscar temas en los 726 objetivos
curl -s "http://localhost:8080/api/search?q=admission" | jq '.hits[0:2]'
```

---

### Parte 2: El Servidor MCP de `study-cybercirujas` (`teach.mcp_server`)

La plataforma expone todo su corpus mediante el protocolo estándar **Model Context Protocol (MCP)** a través de `teach.mcp_server`.

#### 2.1 El Contrato MCP (Cuatro Herramientas Soberanas)
1. `list_certs()`: Lista todas las 38 certificaciones y el estado de sus objetivos.
2. `get_syllabus(cert)`: Devuelve el temario completo con ponderaciones de examen.
3. `get_topic(cert, topic, lang)`: Entrega teoría verificada, fuentes oficiales y scripts de labs.
4. `search_topics(query, cert)`: Búsqueda léxica rápida en títulos, dominios y objetivos.

#### 2.2 Configuración en Claude Desktop o Cursor
Agrega el siguiente bloque a tu archivo `claude_desktop_config.json` o `.cursor/mcp.json`:

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

### Parte 3: Conexión con Open WebUI, Ollama y Hardware (GPU vs CPU)

Open WebUI ofrece una interfaz soberana para modelos locales, herramientas en Python y flujos multi-agente sin telemetría externa.

#### 3.1 Dónde corre Ollama: ¿GPU Radeon o CPU Dell?
En tu equipo conviven dos procesadores: la CPU del sistema Dell y una GPU dedicada **AMD Radeon RX 6800 (16 GB VRAM)**.

Ollama se ejecuta **100% acelerado por hardware en la GPU AMD Radeon RX 6800** mediante **AMD ROCm**:
* **Memoria VRAM asignada:** ~14.19 GB offloaded directamente a la memoria de la placa de video (`size_vram: 14190452407`).
* **Velocidad de generación:** ~11 tokens por segundo sobre modelos de 4B y 7B (`runner: llamacpp`).
* **Rol de la CPU:** La CPU Dell únicamente atiende llamadas I/O de red y orquestación del sistema operativo, liberando completamente el cómputo de inferencia a la GPU.

Puedes verificarlo en vivo ejecutando:
```bash
curl -s http://localhost:11434/api/ps | jq '.models[] | {name, size_vram, runner}'
```
Salida verificada:
```json
{
  "name": "qwen3:4b",
  "size_vram": 14190452407,
  "runner": "llamacpp"
}
```

#### 3.2 Acceder a Open WebUI
Haz clic para abrir la interfaz:  
👉 **[Abrir Open WebUI (http://localhost:3000)](http://localhost:3000)**

- Está configurado con `WEBUI_AUTH=False` (acceso directo sin login para facilitar presentaciones).
- Detecta automáticamente los modelos de Ollama a través de `http://host.docker.internal:11434`.

---

#### 3.3 Cómo conectar la Herramienta (Tool) en Open WebUI como Código Python

En Open WebUI las herramientas personalizadas se crean como **clases de Python** con funciones documentadas (no requiriendo esquemas JSON manuales). Ya dejamos el código listo en el repositorio: [openwebui_tool_tri_mcp.py](openwebui_tool_tri_mcp.py).

##### Paso A: Crear la Herramienta en Open WebUI
1. En el menú lateral izquierdo, ve a **Espacio de Trabajo (Workspace) ➔ Herramientas (Tools)**.
2. Haz clic en el botón **`+` (Crear Herramienta)**.
3. Copia y pega el contenido completo del archivo [openwebui_tool_tri_mcp.py](openwebui_tool_tri_mcp.py):

```python
"""
title: Cloud Native Tri-MCP Tutor
author: Cybercirujas
description: Consulta la Trifecta soberana (libros técnicos Manning, temarios oficiales CNCF y YAMLs de Kubernetes)
version: 1.2.0
"""
import requests

class Tools:
    def __init__(self):
        self.gateway_url = "http://host.docker.internal:8000"

    def query_tri_mcp_tutor(self, question: str) -> str:
        """
        Consulta al Tutor Soberano Cloud Native (rag-tutor + study-cybercirujas + k8s-docs-mcp).
        Responde dudas técnicas, arquitectónicas y de certificación con citas oficiales y YAMLs canónicos.
        :param question: La pregunta técnica sobre Kubernetes, Linux o Platform Engineering.
        :return: La respuesta fundamentada y sintetizada con citas de fuentes oficiales.
        """
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
                    parts.append(f"\n\n### 📖 Fuentes Oficiales:\n{sources}")
                if enrichment.get("study_objective"):
                    parts.append(f"\n- 🎯 **Objetivo de Examen:** `{enrichment['study_objective']}`")
                if enrichment.get("k8s_api_check"):
                    parts.append(f"\n- 🛡️ **API Kubernetes:** `{enrichment['k8s_api_check']}`")
                return "\n".join(parts)
            return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"Error de conexión con RAG Tutor Gateway: {str(e)}"

    def check_mcp_cluster_status(self) -> str:
        """
        Verifica el estado de conexión de los 3 servidores MCP (study-cybercirujas, k8s-docs-mcp, rag-tutor).
        :return: Resumen en texto del estado de cada servidor.
        """
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
            return f"Error de conexión con Gateway: {str(e)}"

    def test_mcp_integration(self, query: str = "pod") -> str:
        """
        Ejecuta un diagnóstico en vivo sobre los tres MCP con cualquier consulta técnica o Kind.
        :param query: Término técnico o prompt en lenguaje natural (ej: 'pod', 'admission', 'network policy').
        :return: Resumen estructurado del test de interoperabilidad.
        """
        url = f"{self.gateway_url}/mcp/test"
        try:
            resp = requests.post(url, json={"target": "all", "query": query}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json().get("diagnostic_results", {})
                study = data.get("study_cybercirujas", {})
                k8s = data.get("k8s_docs_mcp", {})
                rag = data.get("rag_tutor", {})

                report = [
                    f"### 🧪 Diagnóstico Multi-MCP para: `{query}`\n",
                    f"- **study-cybercirujas:** {study.get('status')} | Objetivo: `{study.get('matched_objective')}` ({study.get('certification')})",
                    f"- **k8s-docs-mcp:** {k8s.get('status')} | Kind: `{k8s.get('detected_kind')}` | Manifiestos verificados: {k8s.get('manifests_count')}",
                    f"- **rag-tutor:** {rag.get('status')} | Motor: `{rag.get('retriever_type')}` | Modelo: `{rag.get('ollama_model')}`"
                ]
                return "\n".join(report)
            return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"Error de conexión con Gateway: {str(e)}"
```
4. Haz clic en **Guardar**. Verás la herramienta listada como **`Cloud Native Tri-MCP Tutor`**.

##### Paso B: Asignar la Herramienta a tu Modelo Personalizado
Ahora configuramos el modelo que estabas creando en Open WebUI:
1. Ve a **Espacio de Trabajo (Workspace) ➔ Modelos (Models) ➔ `+` (Crear Modelo)**.
2. Completa los campos:
   - **Nombre:** `Tutor Cloud Native (Tri-MCP)`
   - **Modelo Base (desde):** Selecciona `qwen2.5:7b` o `qwen3:4b`.
   - **Descripción:** `Asistente especializado en arquitectura de plataformas, temarios CNCF y sintaxis oficial de Kubernetes.`
   - **Prompt del sistema:**
     ```text
     Eres un Arquitecto de Plataformas e Instructor Senior Cloud Native.
     Tienes a tu disposición la herramienta 'Cloud Native Tri-MCP Tutor'.
     Siempre que el usuario haga preguntas sobre Kubernetes, certificaciones (CKA, CKAD, CKS, CNPE),
     manifiestos YAML, arquitectura o ingeniería de plataformas, invoca 'query_tri_mcp_tutor'
     para fundamentar tu respuesta en los temarios oficiales, las especificaciones de kubernetes.io
     y los libros de ingeniería de plataformas.
     ```
   - **Herramientas (Tools):** Haz clic donde dice **Ninguno** y tilda la casilla **`Cloud Native Tri-MCP Tutor`** (la herramienta que guardaste en el Paso A).
3. Haz clic en **Guardar**.
4. ¡Listo! Al abrir un nuevo chat y elegir el modelo **`Tutor Cloud Native (Tri-MCP)`**, el modelo invocará automáticamente a la Trifecta para responder.

---

### Parte 4: Cómo Mostrar el Multi-MCP en 3 Entornos Diferentes

Puedes demostrar la coordinación de los 3 servidores MCP en cualquiera de estos 3 entornos:

#### Opción 1: Desde la Terminal (Demostración Determinística Rápida)
1. **Ejecutar la sesión interactiva en vivo:**
   ```bash
   python test_multi_mcp_live.py
   ```
   *Muestra en consola cómo el script consulta `study-cybercirujas` (temario CNPE 3.4), `k8s-docs-mcp` (validación de API y YAML de kubernetes.io) y `rag-tutor` (libros Manning + KùzuDB GraphRAG).*

2. **Inspeccionar el Gateway Tri-MCP por cURL o Swagger:**
   - **Estado de conexión:** [http://localhost:8000/mcp/status](http://localhost:8000/mcp/status)
   - **Test de diagnóstico con lenguaje natural e inferencia determinística:**
     ```powershell
     $body = @{
       target = "all"
       query = "three example how i can create a pod yaml definition and a theory how works"
     } | ConvertTo-Json

     Invoke-RestMethod -Uri "http://localhost:8000/mcp/test" -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
     ```
     *Observa cómo el sistema:*
     1. Extrae automáticamente el recurso `Pod` e ignora stop words conversacionales (*three*, *example*, *how*, *create*, *theory*, *works*).
     2. Valida la apiVersion oficial `v1` (STABLE) y extrae 3 manifiestos canónicos de `kubernetes.io` (Pod individual con probes, Pod multi-contenedor sidecar y Pod con ConfigMap/Secret).
     3. Prioriza el temario CNCF coincidiendo con `CKA 3.5 (Configure Pod admission and scheduling)` con lab de práctica asociado (`has_lab: true`).
     4. Valida el motor RAG de libros y grafo KùzuDB.
   - **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) (permite hacer clic en *Try it out* y ejecutar diagnósticos desde el navegador).

#### Opción 2: Desde la UI Web (Open WebUI)
1. Abre [http://localhost:3000](http://localhost:3000).
2. Selecciona tu modelo personalizado **`Tutor Cloud Native (Tri-MCP)`**.
3. Escribe en el chat:
   > *"¿Cómo implemento una ValidatingAdmissionPolicy en Kubernetes y qué ventajas tiene frente a un webhook tradicional?"*
4. **Lo que ve la audiencia:** Verán el indicador de ejecución de la herramienta `query_tri_mcp_tutor`, extrayendo el contexto del temario de certificación y el YAML oficial, seguido de la respuesta con fuentes citadas.

#### Opción 3: Desde Visual Studio Code, Cursor y OpenCode / opencodev2
El repositorio incluye el archivo de configuración unificada [mcp_servers_config.json](mcp_servers_config.json) para clientes de desarrollo asistido por IA.

Para conectar los 3 servidores en simultáneo:
* **En Cursor:** Copia el contenido de [mcp_servers_config.json](mcp_servers_config.json) dentro de `.cursor/mcp.json`.
* **En VS Code (con extensiones como Cline, Roo Code o Continue):** Ve a la configuración de MCP en la extensión y agrega los 3 servidores:
  ```json
  {
    "mcpServers": {
      "study-cybercirujas": {
        "command": "python",
        "args": ["-m", "teach.mcp_server"],
        "cwd": "/path/to/study-cybercirujas"
      },
      "k8s-docs-mcp": {
        "command": "uv",
        "args": ["--directory", "/path/to/k8s-docs-mcp", "run", "k8s-docs-mcp"]
      },
      "rag-tutor": {
        "command": "python",
        "args": ["-m", "src.mcp_server"],
        "cwd": "/path/to/rag-tutor"
      }
    }
  }
  ```
* **En OpenCode Interpreter / opencodev2:** Apunta a la misma lista de servidores MCP. El asistente en el IDE tendrá a su disposición las herramientas de temarios (`list_certs`, `get_syllabus`), documentación oficial (`search_k8s_docs`, `get_canonical_manifest`) y literatura técnica (`consultar_libros_manning`).

Resultado verificado:
- **`study_cybercirujas`:** Localiza el objetivo `CKA 3.5 (Configure Pod admission and scheduling)`.
- **`k8s_docs_mcp`:** Valida la versión de API y recupera el YAML canónico de kubernetes.io.

#### 4.3 Consultas con Enriquecimiento Tri-MCP (`POST /chat`)
Cuando envías una consulta a `/chat` con `"orchestrate_tri_mcp": true`, el servidor:
1. Consulta `study-cybercirujas` para extraer el temario oficial de la certificación.
2. Consulta `k8s-docs-mcp` para validar la versión actual de la API y el manifiesto YAML.
3. Cruza todo con los libros técnicos de Manning mediante RAG híbrido y KùzuDB GraphRAG.
4. Genera una respuesta soberana con **cero alucinaciones de sintaxis**.

---

### Parte 5: Ejecución de la Sesión Tri-MCP en Vivo

En tu terminal, corre el script de orquestación en tiempo real:

```bash
python test_multi_mcp_live.py
```

#### Salida en Tiempo Real Esperada:
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

## 🎤 Guion para el Presentador (Demo de 3 Minutos)

Si tienes 3 minutos para presentar ante tu equipo o audiencia:

1. **Minuto 1: El Problema y la Plataforma Web ([http://localhost:8080](http://localhost:8080))**
   - *"Cuando los ingenieros estudian para certificaciones CNCF (como CKA, CKS o CNPE), se enfrentan a documentación dispersa y ejemplos desactualizados.*
   - *Aquí tienen [study-cybercirujas](https://github.com/villadalmine/study-cybercirujas): una plataforma 100% soberana con 38 certificaciones y más de 700 temas acompañados de labs prácticos break/fix que corren en sus propias máquinas sin costo de nube."*

2. **Minuto 2: El Gateway de Control Tri-MCP ([http://localhost:8000/docs](http://localhost:8000/docs))**
   - *"Para que un LLM no alucine sintaxis obsoleta, creamos una Trifecta de servidores MCP.*
   - *En lugar de aislar los servidores, `rag-tutor` expone un panel de control: con `/mcp/status` vemos en tiempo real que los 3 motores están conectados; con `/mcp/test` verificamos su respuesta; y con `python test_multi_mcp_live.py` vemos cómo el agente consulta el temario oficial, extrae el YAML canónico de Kubernetes y lo fundamenta con los libros de arquitectura de Manning."*

3. **Minuto 3: Chat Soberano en Open WebUI ([http://localhost:3000](http://localhost:3000))**
   - *"Finalmente, todo esto está integrado en [Open WebUI](http://localhost:3000) conectado al motor local Ollama con Qwen 2.5.*
   - *El estudiante o ingeniero interactúa con un asistente que tiene acceso a las especificaciones oficiales, temarios de examen y libros de referencia con 100% de privacidad y cero costos operativos."*

---

## 🛠️ Comandos de Mantenimiento y Operación

| Acción | Comando |
| :--- | :--- |
| **Verificar Puertos Activos** | `Get-NetTCPConnection -LocalPort 3000, 8000, 8080, 11434` |
| **Reiniciar Open WebUI** | `docker restart open-webui` |
| **Ver Logs de Open WebUI** | `docker logs open-webui -f` |
| **Reiniciar Study Cybercirujas** | `uvicorn teach.api:app --host 0.0.0.0 --port 8080` (en `study-cybercirujas`) |
| **Reiniciar RAG Tutor Gateway** | `uvicorn src.api:app --host 0.0.0.0 --port 8000` (en `rag-tutor`) |
| **Re-ejecutar Test Tri-MCP** | `python test_multi_mcp_live.py` (en `rag-tutor`) |
