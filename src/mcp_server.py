"""Model Context Protocol (MCP) Server for Universal Technical AI Tutor."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer(
        name="Universal Technical RAG Tutor",
        description="MCP server for querying technical engineering books (Kubernetes, Platform Engineering, Databases, Systems Programming, AI Agents).",
    )
except ImportError:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "Universal Technical RAG Tutor",
        description="MCP server for querying technical engineering books (Kubernetes, Platform Engineering, Databases, Systems Programming, AI Agents).",
    )

from src.core import AgenticTutorCore

tutor = AgenticTutorCore()


@mcp.tool()
def consultar_libros_manning(pregunta: str) -> str:
    """Retrieves and synthesizes advanced technical architecture and systems concepts.

    Uses the agentic self-reflection loop over the engineering book library.

    Args:
        pregunta: Technical query formulated by the engineer.

    Returns:
        Detailed technical response with exact book titles and page citations.
    """
    result = tutor.ask(pregunta)
    sources = ", ".join(result["sources"]) if result["sources"] else "No specific sources"

    output = [
        f"### Tutor Response:\n{result['answer']}\n",
        f"**Consulted Sources:** {sources}",
        f"**Models & Engine:** LLM: `{result.get('llm_model')}` | Embeddings: `{result.get('embedding_model')}` | Reranker: `{result.get('reranker_model')}` | Engine: `{result.get('retriever_engine')}`",
        f"*(Agentic steps: {result['iterations']} | Evaluated chunks: {result['retrieved_chunks']})*",
    ]
    return "\n\n".join(output)


@mcp.tool()
def buscar_codigo_yaml(termino: str) -> str:
    """Performs exact lexical retrieval for YAML manifests, CRDs, CLI commands, or Go snippets.

    Args:
        termino: Resource name, CLI flag, APIVersion, or code snippet to search for.

    Returns:
        Raw extracted code chunks without LLM generative alterations.
    """
    chunks = tutor.retriever.retrieve(termino, top_k=3)
    if not chunks:
        return f"No exact matches found for '{termino}'."

    output = [f"### Matches found for '{termino}':\n"]
    for i, c in enumerate(chunks, 1):
        output.append(f"#### Match {i} [{c.to_citation()}]:\n```yaml\n{c.content}\n```")
    return "\n\n".join(output)


if __name__ == "__main__":
    mcp.run()

