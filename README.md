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

## Formas de Ejecución

### Opción A: Como Servidor MCP (para Claude Desktop, Goose CLI, etc.)
```bash
python src/mcp_server.py
```
Herramientas expuestas:
- `consultar_libros_manning(pregunta)`: Búsqueda y síntesis agéntica sobre los libros.
- `buscar_codigo_yaml(termino)`: Búsqueda exacta léxica de manifiestos, CRDs y comandos.

### Opción B: Como API REST (FastAPI)
```bash
python src/api.py
```
Acceso a Swagger UI en: `http://localhost:8000/docs`
Endpoint principal: `POST http://localhost:8000/chat`
