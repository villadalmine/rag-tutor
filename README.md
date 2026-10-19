# Manning Platform Engineering Tutor (rag-tutor)

Tutor de Inteligencia Artificial Local especializado en libros técnicos de Manning (Ingeniería de Plataformas, Kubernetes Internals, Operadores en Go, Crossplane y Arquitecturas Cloud-Native).

Implementa una **arquitectura híbrida (Vectorial + BM25 con Reranker)**, un **loop de razonamiento agéntico liviano** y **exposición dual (Servidor MCP + API REST)**, diseñada de forma desacoplada para evolucionar iterativamente hacia **Omnigraph (GraphRAG)**.

Consulta el documento de decisiones detallado en [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Estructura del Proyecto

```text
rag-tutor/
├── books/                     # Carpeta para colocar tus libros PDF de Manning
│   └── .gitkeep
├── chroma_db/                 # Base de datos vectorial persistente (se genera al indexar)
├── src/
│   ├── __init__.py
│   ├── config.py              # Parámetros centralizados (modelos, rutas, k-neighbors)
│   ├── core.py                # Tutor Core con loop agéntico de auto-reflexión
│   ├── ingest.py              # Ingesta de PDFs, chunking técnico e indexación híbrida
│   ├── mcp_server.py          # Servidor Model Context Protocol (FastMCP)
│   ├── api.py                 # API REST FastAPI para interfaces Web / Open WebUI
│   └── retrievers/
│       ├── __init__.py
│       ├── base.py            # Interfaz abstracta BaseRetriever
│       ├── hybrid.py          # Fase 1: ChromaDB + BM25 + Cross-Encoder Reranker
│       └── omnigraph.py       # Fase 2: Conector para ModernRelay Omnigraph
├── requirements.txt           # Dependencias de Python
├── ARCHITECTURE.md            # Registro de decisiones de arquitectura y roadmap
└── README.md
```

---

## Roadmap Iterativo

1. **Fase 1 (Implementada)**:
   - Ingesta con chunking optimizado para bloques YAML y Go.
   - Búsqueda híbrida (Chroma semántico + BM25 exacto).
   - Reranking local con Cross-Encoder.
   - Agentic RAG loop (evaluación y profundización en máx. 2 pasos).
   - Servidor FastMCP para terminal/Goose/Claude/Antigravity + API FastAPI.
2. **Fase 2 (Próxima iteración)**:
   - Integración con [ModernRelay Omnigraph](https://github.com/ModernRelay/omnigraph) mediante `src/retrievers/omnigraph.py`.
   - Extracción y mapeo ontológico de dependencias de plataforma (CRD ➔ Operador ➔ Webhook).

---

## Requisitos Previos

- **Python**: 3.10 o superior (recomendado 3.11 o 3.12).
- **Ollama**: Instalado localmente con el modelo deseado:
  ```bash
  ollama pull qwen2.5:7b-instruct
  # Opcional si cuentas con RAM suficiente (ej. 256GB):
  # ollama pull qwen2.5:32b-instruct
  ```

---

## Instalación y Configuración

1. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # En Linux / macOS / WSL:
   source venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Colocar tus libros de Manning:**
   - Copia tus archivos `.pdf` dentro del directorio `books/`.

4. **Ejecutar la Ingesta e Indexación:**
   ```bash
   python src/ingest.py
   ```

---

## Guía Detallada de los Modos de Uso

El tutor puede ser utilizado de tres formas complementarias según tu flujo de trabajo:

---

### Modo 1: Consola / CLI Local (`src/cli.py`)

Diseñado para hacer consultas rápidas desde tu terminal sin necesidad de navegadores ni clientes externos.

#### A. Consulta directa por argumento (en una sola línea)
```powershell
.\.venv\Scripts\python.exe src/cli.py "Explica cómo diseñar un Agente de IA reactivo"
```

#### B. Modo Chat interactivo (bucle continuo)
Si ejecutas el script sin argumentos, entrarás a una sesión interactiva continua:
```powershell
.\.venv\Scripts\python.exe src/cli.py
```
```text
=================================================================
 📚 Manning Platform & AI Tutor (Consola Interactiva)
 Escribe tu consulta técnica o 'salir' / 'exit' para terminar.
=================================================================

> Pregunta:
Explica el concepto de Paved Roads en Platform Engineering

[... genera respuesta técnica y fuentes ...]

> Pregunta:
salir
¡Hasta luego!
```

---

### Modo 2: Servidor MCP - Model Context Protocol (`src/mcp_server.py`)

Permite a clientes de IA en terminal o IDE (como **Claude Desktop**, **Goose CLI**, o **Antigravity**) invocar tu biblioteca de libros como herramientas nativas de llamada a funciones (*function calling*).

#### Iniciar el servidor manualmente:
```powershell
.\.venv\Scripts\python.exe src/mcp_server.py
```

#### Herramientas (Tools) que expone el servidor:
1. `consultar_libros_manning(pregunta: str) -> str`:
   - Realiza la búsqueda semántica e híbrida y activa el loop agéntico de auto-reflexión con Ollama para devolver una respuesta fundamentada con citas de páginas.
2. `buscar_codigo_yaml(termino: str) -> str`:
   - Búsqueda léxica directa para recuperar fragmentos exactos de manifiestos YAML, CRDs, comandos de CLI y snippets de Go sin interpretación del LLM.

#### Integración con Claude Desktop / Goose CLI (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "manning-tutor": {
      "command": "C:\\Users\\rino\\Documents\\GitHub\\rag-tutor\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\rino\\Documents\\GitHub\\rag-tutor\\src\\mcp_server.py"
      ]
    }
  }
}
```

---

### Modo 3: API REST con FastAPI (`src/api.py`)

Expone el tutor a través de HTTP estándar, permitiendo conectarlo con interfaces web, extensiones, scripts automatizados o **Open WebUI**.

#### Iniciar la API:
```powershell
.\.venv\Scripts\python.exe src/api.py
```
El servidor arrancará en: `http://localhost:8000`

#### Documentación Interactiva (Swagger UI):
Abre en tu navegador:
```text
http://localhost:8000/docs
```
Podrás probar el endpoint `POST /chat` directamente con un clic desde la interfaz visual.

#### Endpoints Disponibles:
- `GET /health`: Verifica el estado de salud del sistema, ChromaDB, BM25 y el modelo de Ollama.
- `POST /chat`: Envía una consulta y recibe la respuesta con fuentes y estadísticas.

#### Ejemplo de consumo con cURL / PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -ContentType "application/json" -Body '{"question": "¿Qué es Crossplane y cómo se relaciona con Platform Engineering?"}'
```
