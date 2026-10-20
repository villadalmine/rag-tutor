# 📖 Glosario Tecnológico del Ecosistema Soberano (Tri-MCP)

> **Guía Didáctica de Referencia para Personas Técnicas y No Técnicas**  
> Este documento explica cada una de las tecnologías, librerías, protocolos y herramientas utilizadas en el ecosistema (**`rag-tutor`**, **`study-cybercirujas`** y **`k8s-docs-mcp`**).  
> Cada concepto incluye una **analogía sencilla del mundo cotidiano**, su **definición formal**, el **enlace oficial** y el **motivo exacto por el cual fue elegido**.

---

## 📑 Índice de Tecnologías
1. [Inteligencia Artificial, RAG y Razonamiento](#1-inteligencia-artificial-rag-y-razonamiento)
   - [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
   - [LLM (Large Language Model / Modelo de Lenguaje)](#llm-large-language-model)
   - [Embeddings (Incrustaciones Semánticas)](#embeddings-incrustaciones-semánticas)
   - [Cross-Encoder Reranker (Re-clasificador Estricto)](#cross-encoder-reranker)
   - [GraphRAG (RAG Basado en Grafos)](#graphrag-rag-basado-en-grafos)
   - [Ventana de Contexto (Context Window / KV Cache)](#ventana-de-contexto-context-window--kv-cache)
2. [Protocolos, Conectividad e Integración](#2-protocolos-conectividad-e-integración)
   - [Model Context Protocol (MCP)](#model-context-protocol-mcp)
   - [REST API & OpenAPI / Swagger](#rest-api--openapi--swagger)
   - [FastAPI & Uvicorn](#fastapi--uvicorn)
3. [Bases de Datos y Motores de Búsqueda](#3-bases-de-datos-y-motores-de-búsqueda)
   - [ChromaDB](#chromadb)
   - [Rank-BM25](#rank-bm25)
   - [KùzuDB](#kùzudb)
   - [SQLite con FTS5](#sqlite-con-fts5)
4. [Hardware, Inferencia Local y Soberanía](#4-hardware-inferencia-local-y-soberanía)
   - [Ollama](#ollama)
   - [Familia Qwen (Qwen 2.5 / Qwen 3)](#familia-qwen-qwen-25--qwen-3)
   - [AMD ROCm & llamacpp](#amd-rocm--llamacpp)
   - [Docker & Aislamiento de Procesos](#docker--aislamiento-de-procesos)
5. [Herramientas de Lenguaje, Empaquetado y Documentación](#5-herramientas-de-lenguaje-empaquetado-y-documentación)
   - [uv (Astral)](#uv-astral)
   - [PyMuPDF (fitz)](#pymupdf-fitz)
   - [Pydantic](#pydantic)
   - [Open WebUI](#open-webui)
6. [Reglas de Mantenimiento para Desarrolladores y Agentes de IA](#6-reglas-de-mantenimiento-para-desarrolladores-y-agentes-de-ia)

---

## 1. Inteligencia Artificial, RAG y Razonamiento

### RAG (Retrieval-Augmented Generation)
- **Analogía cotidiana:** Es como rendir un examen a *libro abierto*. En lugar de que el alumno intente recordar de memoria millones de datos (arriesgándose a inventar lo que no sabe), primero va a la biblioteca, busca la página exacta que habla del tema y redacta su respuesta mirando el libro real.
- **¿Qué es técnicamente?** Una arquitectura de IA que divide el proceso en dos fases: primero recupera (*Retrieval*) fragmentos de documentos relevantes desde una base de datos local y luego se los entrega al modelo (*Generation*) como evidencia fundamentada para que redacte la respuesta.
- **Enlace oficial:** [AWS What is RAG?](https://aws.amazon.com/what-is/retrieval-augmented-generation/) | [Research Paper (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401)
- **¿Por qué se usa en este proyecto?** Para **eliminar las alucinaciones** en temas críticos de infraestructura. En ingeniería de software no se puede adivinar la sintaxis de un comando o una política de seguridad; RAG obliga al modelo a citar la página del libro o el párrafo del manual oficial.

---

### LLM (Large Language Model)
- **Analogía cotidiana:** Es un redactor increíblemente elocuente y rápido que ha leído miles de textos, pero que si no tiene fuentes a la vista, puede sonar muy convincente diciendo algo completamente falso.
- **¿Qué es técnicamente?** Una red neuronal basada en la arquitectura *Transformer*, entrenada para predecir la siguiente palabra más probable según el contexto numérico recibido.
- **Enlace oficial:** [Qwen Official Website](https://qwenlm.github.io/) | [Hugging Face LLM Concepts](https://huggingface.co/docs)
- **¿Por qué se usa en este proyecto?** Modelos abiertos como `qwen2.5:7b` o `qwen3:4b` se encargan de leer los fragmentos de libros recuperados, comprender la pregunta del usuario y sintetizar una explicación técnica clara en lenguaje natural.

---

### Embeddings (Incrustaciones Semánticas)
- **Analogía cotidiana:** Imagina que a cada frase le asignas una ubicación GPS en un mapa conceptual tridimensional. Frases como *"el pod falló por falta de memoria"* y *"el contenedor murió por OOMKilled"* no comparten casi ninguna palabra exacta, pero en el mapa GPS terminan paradas en la misma esquina porque significan lo mismo.
- **¿Qué es técnicamente?** La transformación de un texto en un vector denso (una lista de números, ej: 384 o 1024 dimensiones) mediante un modelo matemático especializado como `sentence-transformers/all-MiniLM-L6-v2` o `bge-m3`. La similitud semántica se calcula midiendo la distancia matemática (similitud del coseno) entre dos vectores.
- **Enlace oficial:** [Hugging Face Sentence-Transformers](https://sbert.net/)
- **¿Por qué se usa en este proyecto?** Permite encontrar respuestas conceptuales en los libros aunque el usuario pregunte con palabras distintas a las que usó el autor.

---

### Cross-Encoder Reranker
- **Analogía cotidiana:** Un filtro rápido (la secretaria) junta los 20 mejores currículums según palabras clave. Luego, el jefe de contratación (el examinador estricto) lee esos 20 currículums completos en detalle junto con el perfil del puesto y los califica del 1 al 10 para quedarse solo con los 3 mejores.
- **¿Qué es técnicamente?** Un modelo que toma en simultáneo la pregunta y un fragmento de texto (`[CLS] Pregunta [SEP] Texto`) y procesa toda la atención cruzada entre cada palabra de ambos textos, produciendo una puntuación de relevancia mucho más exacta que la distancia vectorial inicial.
- **Enlace oficial:** [SBERT Cross-Encoder Documentation](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- **¿Por qué se usa en este proyecto?** Evita el fenómeno de la **dilución del contexto**. Al recuperar 6 fragmentos, el reranker filtra el ruido y le pasa al LLM únicamente los 3 párrafos de mayor calidad, evitando confundirlo.

---

### GraphRAG (RAG Basado en Grafos)
- **Analogía cotidiana:** Si preguntas *"¿Por qué etcd afecta a los deployments?"*, un buscador común solo buscará textos que tengan ambas palabras. Un mapa conceptual (grafo) te muestra la cadena de relaciones: `Deployment ➔ crea ReplicaSet ➔ crea Pods ➔ se guardan en API Server ➔ se persisten en etcd`.
- **¿Qué es técnicamente?** La combinación de bases de datos vectoriales con bases de datos de grafos de propiedades (como KùzuDB). Los nodos representan entidades (Pod, Servicio, Kubelet) y las aristas representan relaciones (`MANAGES`, `COMMUNICATES_WITH`, `DEPENDS_ON`), consultables con lenguaje declarativo Cypher.
- **Enlace oficial:** [Microsoft Research GraphRAG](https://www.microsoft.com/en-us/research/project/graphrag/) | [KùzuDB](https://kuzudb.com/)
- **¿Por qué se usa en este proyecto?** Para responder dudas de arquitectura compleja de sistemas distribuidos donde la respuesta depende de navegar cómo los componentes se conectan entre sí.

---

### Ventana de Contexto (Context Window / KV Cache)
- **Analogía cotidiana:** Es la memoria de trabajo o el tamaño del escritorio sobre el cual la persona puede apoyar papeles abiertos al mismo tiempo. Si el escritorio es de 16k tokens, caben unas 30 páginas a la vez. Si intentas poner 262k tokens (500 páginas), el escritorio se satura y se te acaba el espacio en la habitación (se llena la memoria RAM/VRAM).
- **¿Qué es técnicamente?** La cantidad máxima de tokens (palabras o piezas de palabras) que el modelo de lenguaje puede procesar en una sola interacción. Para recordar las palabras anteriores sin recalcularlas desde cero, el modelo almacena los vectores de claves y valores (*KV Cache*) en la memoria de la placa de video (VRAM) o en la RAM del sistema.
- **¿Por qué se usa y cómo se calibró en este proyecto?** Modelos como `qwen3:4b` tienen por defecto 256k tokens, lo cual exige más de 40 GB de memoria y hace que la GPU desborde hacia la CPU host. Limitándolo a 16k o 32k tokens, el modelo cabe 100% en la placa de video **AMD Radeon RX 6800**, alcanzando máxima velocidad de generación.

---

## 2. Protocolos, Conectividad e Integración

### Model Context Protocol (MCP)
- **Analogía cotidiana:** Es el conector **USB-C universal** de la inteligencia artificial. Antes de USB-C, cada cámara y teléfono tenía un cable diferente. MCP permite que cualquier modelo de IA (Claude Desktop, Cursor, Open WebUI) se conecte a cualquier fuente de datos (Kubernetes, libros, temarios) usando un solo estándar idéntico.
- **¿Qué es técnicamente?** Un protocolo de comunicación abierto y de estándar industrial impulsado por Anthropic y la Linux Foundation. Define una especificación cliente-servidor mediante JSON-RPC sobre transporte Stdio o Server-Sent Events (SSE) para exponer recursos (*Resources*), herramientas (*Tools*) y plantillas (*Prompts*).
- **Enlace oficial:** [Model Context Protocol Specification](https://modelcontextprotocol.io/) | [MCP Python SDK en GitHub](https://github.com/modelcontextprotocol/python-sdk)
- **¿Por qué se usa en este proyecto?** Permite separar limpiamente los 3 repositorios:
  - `study-cybercirujas` expone las herramientas de temarios y laboratorios de examen.
  - `k8s-docs-mcp` expone las herramientas de validación de sintaxis y YAMLs oficiales.
  - `rag-tutor` expone la búsqueda profunda en libros técnicos.

---

### REST API & OpenAPI / Swagger
- **Analogía cotidiana:** Un menú plastificado de restaurante con precios, fotos e ingredientes claros. El mozo (la API) te muestra exactamente qué platos puedes pedir y en qué formato te los va a entregar, evitando confusiones en la cocina.
- **¿Qué es técnicamente?** Un conjunto de reglas de diseño sobre HTTP (GET, POST, PUT, DELETE) documentado formalmente bajo la especificación **OpenAPI 3.0**. La interfaz web interactiva generada se llama **Swagger UI**.
- **Enlace oficial:** [OpenAPI Initiative](https://www.openapis.org/) | [Swagger UI](https://swagger.io/tools/swagger-ui/)
- **¿Por qué se usa en este proyecto?** El endpoint interactivo en [http://localhost:8000/docs](http://localhost:8000/docs) permite a cualquier desarrollador, auditor o plataforma (como Open WebUI) probar las funciones con un solo clic desde el navegador web.

---

### FastAPI & Uvicorn
- **Analogía cotidiana:** FastAPI es el chef experto que cocina a alta velocidad, y Uvicorn es la cinta transportadora ultrarrápida que entrega los platos a las mesas sin demoras.
- **¿Qué es técnicamente?** **FastAPI** es un framework moderno y asíncrono para construir APIs web en Python 3.10+ con validación estricta de tipos. **Uvicorn** es un servidor web ASGI (Asynchronous Server Gateway Interface) ultraligero y de alto rendimiento basado en `uvloop` y `httptools`.
- **Enlace oficial:** [FastAPI Documentation](https://fastapi.tiangolo.com/) | [Uvicorn](https://www.uvicorn.org/)
- **¿Por qué se usa en este proyecto?** Proporciona tiempos de respuesta de milisegundos para los endpoints de salud (`/health`), estado del clúster (`/mcp/status`), diagnóstico (`/mcp/test`) y chat (`/chat`).

---

## 3. Bases de Datos y Motores de Búsqueda

### ChromaDB
- **Analogía cotidiana:** Una biblioteca mágica donde los libros no están ordenados por orden alfabético, sino por **afinidad de ideas**. Si buscas *"cómo aislar procesos"*, la biblioteca te acerca automáticamente los libros de contenedores y namespaces de Linux aunque no tengan esa frase textual.
- **¿Qué es técnicamente?** Una base de datos vectorial de código abierto (*Vector Database*) incrustada (*in-process*), diseñada para almacenar documentos junto con sus representaciones vectoriales densas e índices de búsqueda por proximidad (HNSW - Hierarchical Navigable Small World).
- **Enlace oficial:** [ChromaDB Official Site](https://www.trychroma.com/) | [ChromaDB en GitHub](https://github.com/chroma-core/chroma)
- **¿Por qué se usa en este proyecto?** Es el motor de almacenamiento de la Fase 1 de RAG Tutor para guardar y consultar más de 23.000 fragmentos de libros técnicos sin necesidad de instalar servidores de bases de datos pesados.

---

### Rank-BM25
- **Analogía cotidiana:** Es el clásico `Ctrl + F` de tu teclado, pero potenciado. Si buscas una palabra rara o muy específica (como `ValidatingAdmissionPolicy`), este motor encuentra exactamente los párrafos donde aparece esa palabra técnica precisa, sin inventar nada.
- **¿Qué es técnicamente?** Una implementación del algoritmo probabilístico de recuperación léxica **Okapi BM25** (Best Matching 25), que evalúa la frecuencia de aparición de términos (*TF*) penalizando aquellos términos que aparecen en demasiados documentos (*IDF*).
- **Enlace oficial:** [rank_bm25 en PyPI](https://pypi.org/project/rank-bm25/) | [Wikipedia Okapi BM25](https://en.wikipedia.org/wiki/Okapi_BM25)
- **¿Por qué se usa en este proyecto?** En Kubernetes, los nombres de recursos (`Pod`, `Deployment`, `Ingress`, `CEL`) son palabras técnicas exactas. Los modelos de lenguaje a veces diluyen estas palabras; BM25 garantiza que si buscas un término exacto, el fragmento sea recuperado sin perderse.

---

### KùzuDB
- **Analogía cotidiana:** Es como un tablero de detectives con hilos rojos que unen personas, lugares y pistas. Te permite seguir el camino de cómo una cosa se conecta con otra a través de múltiples saltos.
- **¿Qué es técnicamente?** Una base de datos de grafos de propiedades incrustada (*embedded property graph database*) optimizada para almacenamiento en disco y consultas analíticas ultra veloces mediante el lenguaje declarativo estándar **Cypher**.
- **Enlace oficial:** [KùzuDB Official Site](https://kuzudb.com/) | [KùzuDB GitHub](https://github.com/kuzudb/kuzu)
- **¿Por qué se usa en este proyecto?** Permite realizar GraphRAG en milisegundos directamente en el mismo proceso de Python, trazando relaciones entre arquitecturas de microservicios sin latencia de red.

---

### SQLite con FTS5
- **Analogía cotidiana:** Un archivo de oficina compacto que cabe en un pendrive, pero que tiene un índice al final del libro que te dice en qué página y renglón está cada palabra en menos de un segundo.
- **¿Qué es técnicamente?** SQLite es el motor de base de datos relacional en un solo archivo más utilizado del mundo. **FTS5** (Full-Text Search 5) es su módulo nativo de búsqueda de texto completo con soporte para tokenización Porter y consultas booleanas complejas.
- **Enlace oficial:** [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
- **¿Por qué se usa en este proyecto?** Es el motor que utiliza **`k8s-docs-mcp`** para almacenar y buscar en toda la documentación oficial de `kubernetes.io` y los manifiestos YAML canónicos de forma rápida, portable y sin dependencias externas.

---

## 4. Hardware, Inferencia Local y Soberanía

### Ollama
- **Analogía cotidiana:** Es como el reproductor multimedia (tipo VLC) de los modelos de inteligencia artificial. Así como VLC reproduce cualquier video `.mp4`, Ollama toma cualquier modelo abierto y lo ejecuta en tu computadora de forma transparente.
- **¿Qué es técnicamente?** Una plataforma y servicio en segundo plano que gestiona el ciclo de vida, la descarga, la cuantización (GGUF) y la ejecución de modelos de lenguaje en hardware local, exponiendo una API REST compatible en el puerto `11434`.
- **Enlace oficial:** [Ollama Official Website](https://ollama.com/) | [Ollama en GitHub](https://github.com/ollama/ollama)
- **¿Por qué se usa en este proyecto?** Permite operar en modo **100% soberano**: ni un solo byte de tus preguntas o libros sale de tu máquina hacia la nube de terceros.

---

### Familia Qwen (Qwen 2.5 / Qwen 3)
- **Analogía cotidiana:** Es la mente del asistente. Desarrollada por Alibaba Cloud y publicada con licencias abiertas, es reconocida mundialmente por su precisión en matemáticas, programación y seguimiento estricto de instrucciones en varios idiomas.
- **¿Qué es técnicamente?** Modelos de lenguaje de pesos abiertos (*open-weights*). Versiones utilizadas:
  - `qwen2.5:7b`: Modelo de 7 mil millones de parámetros de altísima solidez sintáctica y precisión para razonamiento técnico.
  - `qwen3:4b`: Modelo de nueva generación de 4 mil millones de parámetros optimizado para razonamiento profundo (*extended thinking*).
- **Enlace oficial:** [QwenLM en GitHub](https://github.com/QwenLM/Qwen2.5) | [Alibaba Cloud AI](https://www.alibabacloud.com/)
- **¿Por qué se usa en este proyecto?** Ofrece el mejor balance entre consumo de memoria (VRAM) y precisión para interpretar código YAML y conceptos de sistemas distribuidos.

---

### AMD ROCm & llamacpp
- **Analogía cotidiana:** La CPU es como un profesor universitario genial que resuelve problemas complejos de a uno por vez. La GPU (placa de video) es como un batallón de 5.000 soldados que hacen millones de sumas y multiplicaciones simples al mismo tiempo. ROCm es la orden que pone a trabajar al batallón.
- **¿Qué es técnicamente?** **AMD ROCm** (Radeon Open Compute) es la plataforma abierta de computación paralela de AMD (equivalente a NVIDIA CUDA). **llamacpp** es el motor en C++ que ejecuta las operaciones tensoriales del modelo directamente en los núcleos de cómputo de la tarjeta gráfica **AMD Radeon RX 6800**.
- **Enlace oficial:** [AMD ROCm Platform](https://www.amd.com/en/products/software/rocm.html) | [llama.cpp en GitHub](https://github.com/ggerganov/llama.cpp)
- **¿Por qué se usa en este proyecto?** Permite offloadear más de 14 GB de memoria a la tarjeta de video dedicada, logrando inferencia a alta velocidad sin congelar la CPU Dell de tu máquina.

---

### Docker & Aislamiento de Procesos
- **Analogía cotidiana:** Una habitación prefabricada que viene con sus propios muebles, enchufes y pintura. La instalas en tu casa y funciona idéntica sin importar si el resto de tu casa es de ladrillo o de madera.
- **¿Qué es técnicamente?** Una plataforma de virtualización a nivel de sistema operativo basada en contenedores de Linux (namespaces y cgroups) que empaqueta una aplicación y todas sus dependencias.
- **Enlace oficial:** [Docker Official Site](https://www.docker.com/)
- **¿Por qué se usa en este proyecto?** Corre **Open WebUI** en un entorno aislado sin requerir instalar Node.js ni paquetes web en tu sistema host.

---

## 5. Herramientas de Lenguaje, Empaquetado y Documentación

### uv (Astral)
- **Analogía cotidiana:** Si `pip` era una carreta que tardaba minutos en instalar paquetes, `uv` es un tren bala programado en Rust que resuelve e instala dependencias en milisegundos.
- **¿Qué es técnicamente?** Un administrador de paquetes, entornos virtuales y dependencias de Python extremadamente rápido desarrollado por Astral en Rust. Reemplaza a `pip`, `pip-tools` y `virtualenv`.
- **Enlace oficial:** [Astral uv Documentation](https://docs.astral.sh/uv/) | [uv en GitHub](https://github.com/astral-sh/uv)
- **¿Por qué se usa en este proyecto?** Es el empaquetador moderno elegido en **`k8s-docs-mcp`** y en el ecosistema para garantizar instalaciones determinísticas mediante `uv.lock`.

---

### PyMuPDF (fitz)
- **Analogía cotidiana:** Una fotocopiadora de alta velocidad con visor láser que abre libros de 800 páginas en una fracción de segundo y extrae el texto respetando los números de página exactos.
- **¿Qué es técnicamente?** Un enlace de Python de alto rendimiento para la biblioteca de renderizado en C **MuPDF**, especializada en análisis, extracción de texto y metadatos de documentos PDF y EPUB.
- **Enlace oficial:** [PyMuPDF Documentation](https://pymupdf.readthedocs.io/) | [MuPDF](https://mupdf.com/)
- **¿Por qué se usa en este proyecto?** Ingiere colecciones completas de libros técnicos extrayendo el contenido sin perder el número de página de referencia para las citas bibliográficas obligatorias.

---

### Pydantic
- **Analogía cotidiana:** Un inspector de aduanas implacable en la puerta de la ciudad. Si alguien intenta ingresar un paquete sin etiqueta o con el formato incorrecto, lo rechaza al instante antes de que cause problemas adentro.
- **¿Qué es técnicamente?** La librería de validación de datos y gestión de configuraciones más utilizada en Python, basada en anotaciones de tipos estándar de Python.
- **Enlace oficial:** [Pydantic Documentation](https://docs.pydantic.dev/)
- **¿Por qué se usa en este proyecto?** Garantiza que todas las solicitudes a la API (`McpTestRequest`, `QueryRequest`, `QueryResponse`) sean válidas y seguras antes de que toquen la lógica del tutor o los motores de búsqueda.

---

### Open WebUI
- **Analogía cotidiana:** La pantalla táctil del tablero del auto. No necesitas saber cómo funciona la inyección electrónica ni los frenos ABS; desde la pantalla manejas todo de forma intuitiva y visual.
- **¿Qué es técnicamente?** Una interfaz de usuario web avanzada y extensible para interactuar con modelos locales de Ollama y APIs compatibles con OpenAI, con soporte para gestión de usuarios, subida de documentos, prompts compartidos y ejecución de herramientas personalizadas escritas en Python.
- **Enlace oficial:** [Open WebUI Official Website](https://openwebui.com/) | [Open WebUI en GitHub](https://github.com/open-webui/open-webui)
- **¿Por qué se usa en este proyecto?** Es el front-end visual en [http://localhost:3000](http://localhost:3000) donde los usuarios interactúan con el **Tutor Cloud Native (Tri-MCP)**.

---

## 6. Reglas de Mantenimiento para Desarrolladores y Agentes de IA

Este glosario es un **documento vivo del repositorio**. Todo agente de IA o desarrollador que modifique la base de código debe seguir estas tres directivas:

1. **Si agregas una nueva dependencia a `pyproject.toml` o `requirements.txt`:**
   - Añade una entrada en este documento indicando: qué es (con analogía cotidiana), su enlace oficial y **por qué se incorporó al proyecto**.
2. **Si cambias o reemplazas un modelo de lenguaje o embedding en `src/config.py`:**
   - Actualiza la sección [Familia Qwen](#familia-qwen-qwen-25--qwen-3) o crea una nueva subsección documentando el modelo, el tamaño de sus pesos y la ventana de contexto asignada.
3. **Mantén el lenguaje accesible:**
   - Conserva siempre el formato de **Analogía Cotidiana** + **Definición Técnica**. Cualquier persona interesada en educación abierta debe poder comprender el valor de la tecnología sin sentirse excluida por la jerga.
