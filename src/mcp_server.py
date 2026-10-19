"""Servidor Model Context Protocol (MCP) para el Tutor de Manning."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer(
        name="Manning Platform Engineering Tutor",
        description="Servidor MCP para consultar libros técnicos de Manning (Kubernetes, Platform Engineering, Go, Crossplane).",
    )
except ImportError:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "Manning Platform Engineering Tutor",
        description="Servidor MCP para consultar libros técnicos de Manning (Kubernetes, Platform Engineering, Go, Crossplane).",
    )

from src.core import AgenticTutorCore

tutor = AgenticTutorCore()


@mcp.tool()
def consultar_libros_manning(pregunta: str) -> str:
    """Busca y sintetiza conceptos avanzados de arquitectura, Kubernetes y Cloud-Native.

    Utiliza el loop agéntico de auto-reflexión sobre los libros de Manning.

    Args:
        pregunta: Consulta técnica formulada por el ingeniero.

    Returns:
        Respuesta técnica detallada con citas de los libros y páginas.
    """
    result = tutor.ask(pregunta)
    sources = ", ".join(result["sources"]) if result["sources"] else "Sin fuentes específicas"

    output = [
        f"### Respuesta del Tutor:\n{result['answer']}\n",
        f"**Fuentes consultadas:** {sources}",
        f"**Modelos y Motor:** LLM: `{result.get('llm_model')}` | Embeddings: `{result.get('embedding_model')}` | Reranker: `{result.get('reranker_model')}` | Motor: `{result.get('retriever_engine')}`",
        f"*(Iteraciones agénticas: {result['iterations']} | Fragmentos analizados: {result['retrieved_chunks']})*",
    ]
    return "\n\n".join(output)


@mcp.tool()
def buscar_codigo_yaml(termino: str) -> str:
    """Busca coincidencias léxicas exactas de manifiestos YAML, CRDs, comandos o código Go.

    Args:
        termino: Nombre de recurso, flag, APIVersion o snippet a buscar.

    Returns:
        Fragmentos directos encontrados sin síntesis del LLM.
    """
    chunks = tutor.retriever.retrieve(termino, top_k=3)
    if not chunks:
        return f"No se encontraron fragmentos exactos para '{termino}'."

    output = [f"### Coincidencias encontradas para '{termino}':\n"]
    for i, c in enumerate(chunks, 1):
        output.append(f"#### Coincidencia {i} [{c.to_citation()}]:\n```yaml\n{c.content}\n```")
    return "\n\n".join(output)


if __name__ == "__main__":
    mcp.run()
