# Guía de Integración: Open WebUI + MCP Multi-Server (RAG Tutor + Study Cybercirujas)

Esta guía explica cómo conectar **Open WebUI** con dos servidores MCP simultáneos para crear el **"Tutor Mágico de Certificaciones y Arquitectura"**, 100% local, soberano y sin costo de APIs:

1. 📚 **RAG Tutor MCP (`rag-tutor`):** Base de conocimiento profunda con 22 libros técnicos, recuperación híbrida (Chroma + BM25), reranking con Cross-Encoder y citas exactas de páginas.
2. 🎯 **Study Cybercirujas MCP (`study-cybercirujas`):** Plataforma abierta de certificaciones IT (CKA, CKAD, CKS, LPIC, etc.) con syllabus oficial de vendors, ejercicios y laboratorios de rotura/reparación (*break-and-fix labs*).

---

## 1. Arquitectura del Sistema Multi-MCP

```mermaid
flowchart TD
    User["Estudiante / Ingeniero"] -->|1. 'Prepárame para el objetivo 2.1 de CKA sobre Admission Controllers'| UI["Open WebUI / Claude Desktop\n(Orquestador MCP y UI de Chat)"]
    
    subgraph Orquestación de Herramientas MCP
        UI -->|Tool Call: get_topic('cka', '2.1')| MCP_CYBER["MCP Server: study-cybercirujas\n(teach.mcp_server)"]
        UI -->|Tool Call: consultar_libros_manning('Admission Controllers')| MCP_RAG["MCP Server: rag-tutor\n(src/mcp_server.py)"]
        
        MCP_CYBER -->|Devuelve Syllabus oficial + Ejercicios + Lab break-fix| UI
        MCP_RAG -->|Devuelve Teoría profunda + Manifiestos YAML + Páginas de libros| UI
    end
    
    UI -->|Inferencia combinada con Ollama qwen2.5:7b| LLM["Modelo Local (Ollama)"]
    LLM -->|3. Respuesta Integral: Temario + Ejercicio + Fundamento de Libros| User
```

---

## 2. Herramientas Expuestas por Ambos Servidores MCP

Ambos servidores están construidos con el SDK oficial `mcp` (v2.x `MCPServer`) y se comunican a través del protocolo estándar `stdio`:

### Servidor 1: `study-cybercirujas` (Certificaciones & Labs)
- `list_certs()`: Lista las 28+ certificaciones disponibles (CKA, CKAD, CKS, LPIC-1, KCNA, etc.).
- `get_syllabus(cert: str)`: Devuelve los objetivos oficiales del vendor con ponderaciones en el examen.
- `get_topic(cert: str, topic: str, lang: str)`: Obtiene la teoría oficial, ejercicios prácticos y el script del laboratorio break-and-fix.
- `search_topics(query: str)`: Búsqueda cruzada de objetivos en todas las certificaciones.

### Servidor 2: `rag-tutor` (Base de Conocimiento de Libros & Código)
- `consultar_libros_manning(pregunta: str, dominio: str, solo_codigo: bool)`: Búsqueda híbrida y razonamiento agéntico sobre los 22 libros con citas de página.
- `buscar_codigo_yaml(termino: str)`: Extracción léxica directa de manifiestos YAML y código sin interpretación del LLM.

---

## 3. Configuración Paso a Paso en Open WebUI y Clientes MCP

### Opción A: Configuración en Claude Desktop o Goose CLI (`claude_desktop_config.json`)
Copia esta configuración en `%APPDATA%\Claude\claude_desktop_config.json`:

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
      "cwd": "C:\\ruta\\a\\study-cybercirujas"
    }
  }
}
```

### Opción B: Integración en Open WebUI
En **Open WebUI**, puedes conectar los servidores de dos formas:
1. **Vía Open WebUI MCPO / Pipes:** Habilitando la conexión a servidores MCP en la sección *Workspace -> Tools* de Open WebUI.
2. **Vía API REST de RAG Tutor:** Conectando `http://localhost:8000/chat` como un conector OpenAPI nativo en Open WebUI.

---

## 4. Ejemplo Real de Simulación: "Tutor Mágico para Certificar"

### Consulta del Usuario en Open WebUI:
> *"Quiero estudiar el tema de Admission Controllers para la certificación CKA. Dame el objetivo oficial, el ejercicio de práctica de Cybercirujas y explícame en detalle con los libros cómo implementarlo con código YAML y OPA Gatekeeper."*

### Flujo de Ejecución Interno (Comprobado):
1. **Llamada 1 (Cybercirujas):** Open WebUI invoca `get_topic("cka", "2.1", "es")`.
   - Recupera el objetivo oficial de CNCF: *"Understand Admission Controllers and Webhooks"*.
   - Recupera el ejercicio práctico de laboratorio.
2. **Llamada 2 (RAG Tutor):** Open WebUI invoca `consultar_libros_manning("Admission Controllers validación y OPA Gatekeeper")`.
   - Recupera los fragmentos de los libros de Kubernetes Core y Platform Engineering (Pág. 286 de Core K8s y Págs. 122, 127 de Platform Engineering).
   - Extrae el manifiesto YAML de configuración del webhook y el flujo de `image.sha`.
3. **Respuesta Sintetizada del Modelo Local:**
   - Presenta el temario oficial del examen.
   - Entrega el ejercicio y escenario de rotura para practicar.
   - Enseña la arquitectura exacta fundamentada con la cita del libro y el YAML verificado.
