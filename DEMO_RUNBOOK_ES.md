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

### Parte 3: Conexión con Open WebUI y Ollama

Open WebUI ofrece una interfaz soberana para modelos locales, herramientas OpenAPI y agentes sin telemetría externa.

#### 3.1 Verificación del Motor Ollama
Ollama corre localmente en el puerto `11434`. Puedes verificarlo en tu navegador o terminal:
- **API de Tags de Ollama:** [http://localhost:11434/api/tags](http://localhost:11434/api/tags)

```bash
curl -s http://localhost:11434/api/tags | jq '.models[].name'
```
Modelos activos:
- `qwen2.5:7b` (Razonamiento general y código técnico)
- `qwen3:4b` / `llama3.2:3b` (Modelos ultraligeros)
- `bge-m3:latest` (Embeddings densos multilingües)

#### 3.2 Acceder a Open WebUI
Haz clic para abrir la interfaz:  
👉 **[Abrir Open WebUI (http://localhost:3000)](http://localhost:3000)**

- Está configurado con `WEBUI_AUTH=False` (acceso directo sin login para facilitar presentaciones).
- Detecta automáticamente los modelos de Ollama a través de `http://host.docker.internal:11434`.

#### 3.3 Importar `rag-tutor` como Herramienta OpenAPI en Open WebUI
1. En Open WebUI, ve a: **Workspace ➔ Tools ➔ `+` (Create Tool)**.
2. Haz clic en los tres puntos `...` arriba a la derecha y selecciona **Import from OpenAPI**.
3. Ingresa la URL interna del contenedor:
   ```text
   http://host.docker.internal:8000/openapi.json
   ```
4. Guarda la herramienta. Ahora cualquier modelo en Open WebUI puede invocar las funciones del tutor RAG y la orquestación Tri-MCP directamente desde la ventana de chat.

---

### Parte 4: La API Gateway Tri-MCP de `rag-tutor`

Para evitar que la API REST sea solo un buscador de libros, `rag-tutor` implementa un **Gateway Unificado de Control Tri-MCP**:

#### 4.1 Monitorear Estado de los 3 Servidores (`GET /mcp/status`)
Abre en tu navegador o ejecuta con cURL:  
👉 **[Ver Estado Tri-MCP (http://localhost:8000/mcp/status)](http://localhost:8000/mcp/status)**  
👉 **[Swagger UI Interactivo (http://localhost:8000/docs)](http://localhost:8000/docs)**

Respuesta en vivo que muestra los tres servidores sincronizados:
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
      "total_doc_sections": 5,
      "total_manifests": 5,
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

#### 4.2 Probar Diagnósticos en Vivo (`POST /mcp/test`)
Desde la documentación Swagger o con PowerShell/cURL, puedes disparar tests contra los servidores:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/mcp/test" -Method POST -ContentType "application/json" -Body '{"target": "all", "query": "admission"}' | ConvertTo-Json -Depth 5
```

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
