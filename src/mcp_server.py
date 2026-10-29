"""Model Context Protocol (MCP) Server for Universal Technical AI Tutor.

Designed with progressive navigation (Zero-Token-Burn) and publication freshness control:
1. `listar_libros_y_secciones`: Returns the compact catalog with publication year (`publication_year`),
   domain, tags, and chapter/section index without loading full book text.
2. `buscar_fragmentos_secciones`: Returns only the top-K relevant fragments with their publication year,
   section, and code language, supporting SQL-like WHERE filters (`min_year`, `domain`, `tag`, `seccion`, `code_lang`, `libro`).
3. `consultar_grafo_kuzu`: Queries the embedded KùzuDB property graph (Cypher) for architectural relationships
   between books, domains, and technical concepts.
4. `consultar_libros_manning`: Executes the full agentic self-reflection loop with optional freshness filters (`min_year`).
5. `buscar_codigo_yaml`: Performs exact lexical retrieval of code/manifests with freshness filtering (`min_year`).
"""

import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer(
        name="Universal Technical RAG Tutor",
        description="MCP server for querying technical engineering books with publication year freshness filtering, KùzuDB GraphRAG, and section-level retrieval.",
    )
except ImportError:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "Universal Technical RAG Tutor",
        description="MCP server for querying technical engineering books with publication year freshness filtering, KùzuDB GraphRAG, and section-level retrieval.",
    )

from src.core import AgenticTutorCore
from src.kuzu_graph import KuzuGraphEngine
from src.metadata_engine import load_metadata_registry

tutor = AgenticTutorCore()


@mcp.tool()
def listar_libros_y_secciones(
    domain: Optional[str] = None,
    min_year: Optional[int] = None,
    tag: Optional[str] = None,
    incluir_secciones: bool = True,
) -> str:
    """Lists the indexed book catalog with PUBLICATION YEAR, domain, tags, and section tree.

    USE THIS TOOL FIRST to inspect which books exist, what year they were published (to discard
    outdated books), and which chapters/sections they contain, consuming minimal context tokens.

    Args:
        domain: Filter by technical domain (e.g. 'cloud_native', 'mlops', 'ai_agents', 'databases_and_storage').
        min_year: Filter only books published on or after this year (e.g. 2024).
        tag: Filter by specific topic or technology tag (e.g. 'kubernetes', 'vllm', 'rag').
        incluir_secciones: If True, includes the compact chapter/section index for each book.
    """
    registry = load_metadata_registry()
    catalog = registry.get("catalog", {})
    if not catalog:
        return "No books registered in metadata_registry.json. Run 'python src/ingest.py' first."

    lines = ["### 📚 Technical Book Catalog (Compact MCP Index)\n"]
    matched = 0

    for book_name, meta in sorted(catalog.items()):
        b_domain = meta.get("domain", "general_technical")
        b_sec_domains = meta.get("secondary_domains", [])
        b_year = meta.get("publication_year")
        b_tags_list = meta.get("tags", [])
        b_tags = ", ".join(b_tags_list)
        b_units = meta.get("pages", 0)
        sections = meta.get("sections", [])

        if domain and (b_domain != domain and domain not in b_sec_domains and domain not in b_tags_list):
            continue
        if min_year and (not b_year or int(b_year) < int(min_year)):
            continue
        if tag and tag.lower() not in b_tags.lower() and tag.lower() not in book_name.lower():
            continue

        matched += 1
        year_badge = f"📅 Year: **{b_year}**" if b_year else "📅 Year: *Unknown*"
        lines.append(
            f"- **{book_name}** | {year_badge} | Domain: `{b_domain}` | Units: {b_units} | Tags: `{b_tags}`"
        )

        if incluir_secciones and sections:
            sec_names = [s.get("section", "") for s in sections[:20] if s.get("section")]
            lines.append(f"  - **Sections ({len(sections)}):** " + " • ".join(sec_names))

    if matched == 0:
        return f"No books found matching the specified filters (domain={domain}, min_year={min_year}, tag={tag})."

    return "\n".join(lines)


@mcp.tool()
def buscar_fragmentos_secciones(
    consulta: str,
    top_k: int = 4,
    domain: Optional[str] = None,
    code_lang: Optional[str] = None,
    libro: Optional[str] = None,
    min_year: Optional[int] = None,
    tag: Optional[str] = None,
    seccion: Optional[str] = None,
) -> str:
    """Retrieves only the relevant sections/fragments without loading full books or invoking Ollama.

    Ideal for MCP agents (Claude, Cursor, Antigravity) needing ultra-fast, low-token context
    using SQL-like WHERE filters (`min_year`, `domain`, `tag`, `seccion`, `code_lang`, `libro`).

    Args:
        consulta: Concept, section, or technical term to search for.
        top_k: Maximum number of chunks to return (default 4, recommended max 6).
        domain: Filter by domain (e.g. 'cloud_native', 'mlops', 'ai_agents').
        code_lang: Filter by code language (e.g. 'yaml', 'go', 'python', 'bash', 'sql', 'rust').
        libro: Filter by a specific book name (or substring).
        min_year: Ignore books published before this year (e.g. 2024 or 2025 to avoid deprecated APIs).
        tag: Filter by a specific topic tag (e.g. 'kubernetes', 'vllm', 'prometheus').
        seccion: Filter by chapter or section title substring (e.g. 'Deploying Models', 'Chapter 3').
    """
    top_k = max(1, min(int(top_k), 10))
    chunks = tutor.retriever.retrieve(
        consulta,
        top_k=top_k,
        domain=domain,
        code_lang=code_lang,
        book=libro,
        min_year=min_year,
        tag=tag,
        section=seccion,
    )
    if not chunks:
        return f"No fragments found for '{consulta}' with the applied filters."

    output = [f"### 🎯 Retrieved Sections ({len(chunks)} chunks, token-efficient):\n"]
    for i, c in enumerate(chunks, 1):
        meta = c.metadata or {}
        year = meta.get("publication_year", "N/A")
        sec = meta.get("section_title") or meta.get("chapter") or "General"
        lang = meta.get("code_lang", "none")
        tags = meta.get("tags", "")
        output.append(
            f"#### [{i}] {c.to_citation()} | 📅 Year: {year} | 📑 Section: {sec} | 🏷️ Tags: {tags} | 💻 Code: {lang}\n"
            f"{c.content}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def consultar_grafo_kuzu(concepto: str) -> str:
    """Queries the embedded KùzuDB Knowledge Graph (Cypher) for ontological relationships and books explaining a concept.

    Args:
        concepto: Concept ID or name to inspect in the KùzuDB graph (e.g. 'kubernetes', 'rag', 'ai-agent', 'fine-tuning').
    """
    kuzu_engine = KuzuGraphEngine()
    if not kuzu_engine.available or not kuzu_engine.is_populated():
        return "KùzuDB graph is not initialized. Run 'python src/ingest.py' first."

    concept_key = concepto.strip().lower().replace(" ", "-")
    rows = kuzu_engine.get_related_concepts(concept_key)
    if not rows:
        # Try case-insensitive substring search in KùzuDB via Cypher
        cypher = """
        MATCH (a:Concept)-[r:RelatesTo]->(b:Concept)
        WHERE lower(a.name) CONTAINS $q OR lower(b.name) CONTAINS $q OR lower(a.id) CONTAINS $q OR lower(b.id) CONTAINS $q
        RETURN a.id AS src_id, a.name AS src_name, r.relation AS relation, b.id AS tgt_id, b.name AS tgt_name
        LIMIT 25
        """
        rows = kuzu_engine.query_cypher(cypher, {"q": concepto.strip().lower()})

    if not rows:
        return f"No ontological relationships found in KùzuDB for '{concepto}'."

    lines = [f"### 🕸️ KùzuDB Knowledge Graph Relationships for `{concepto}` ({len(rows)} edges):\n"]
    for r in rows[:25]:
        lines.append(f"- `({r['src_name']})` ──[**{r['relation']}**]──► `({r['tgt_name']})`")
    return "\n".join(lines)


@mcp.tool()
def consultar_libros_manning(
    pregunta: str,
    domain: Optional[str] = None,
    code_lang: Optional[str] = None,
    libro: Optional[str] = None,
    min_year: Optional[int] = None,
) -> str:
    """Retrieves and synthesizes advanced technical architecture and systems concepts.

    Uses the agentic self-reflection loop over the engineering book library.

    Args:
        pregunta: Technical query formulated by the engineer.
        domain: Optional domain filter (e.g. 'cloud_native', 'mlops').
        code_lang: Optional code language filter (e.g. 'yaml', 'go', 'python').
        libro: Optional specific book title/filename filter.
        min_year: Optional minimum publication year (e.g. 2024) to exclude outdated books.

    Returns:
        Detailed technical response with exact book titles, publication years, and section/page citations.
    """
    result = tutor.ask(
        pregunta,
        domain=domain,
        code_lang=code_lang,
        book=libro,
        min_year=min_year,
    )
    sources = ", ".join(result["sources"]) if result["sources"] else "No specific sources"

    output = [
        f"### Tutor Response:\n{result['answer']}\n",
        f"**Consulted Sources:** {sources}",
        f"**Models & Engine:** LLM: `{result.get('llm_model')}` | Embeddings: `{result.get('embedding_model')}` | Reranker: `{result.get('reranker_model')}` | Engine: `{result.get('retriever_engine')}`",
        f"*(Agentic steps: {result['iterations']} | Evaluated chunks: {result['retrieved_chunks']})*",
    ]
    return "\n\n".join(output)


@mcp.tool()
def buscar_codigo_yaml(
    termino: str,
    code_lang: Optional[str] = None,
    min_year: Optional[int] = None,
) -> str:
    """Performs exact lexical retrieval for YAML manifests, CRDs, CLI commands, or code snippets.

    Args:
        termino: Resource name, CLI flag, APIVersion, or code snippet to search for.
        code_lang: Optional code language filter ('yaml', 'go', 'python', 'bash', 'rust', 'sql').
        min_year: Optional minimum publication year (e.g. 2024) to avoid deprecated APIs.

    Returns:
        Raw extracted code chunks with book publication year without LLM generative alterations.
    """
    chunks = tutor.retriever.retrieve(
        termino, top_k=3, code_lang=code_lang, min_year=min_year
    )
    if not chunks:
        return f"No exact matches found for '{termino}'."

    output = [f"### Matches found for '{termino}':\n"]
    for i, c in enumerate(chunks, 1):
        lang = (c.metadata or {}).get("code_lang", "yaml")
        fence = lang if lang != "none" else "yaml"
        output.append(f"#### Match {i} [{c.to_citation()}]:\n```{fence}\n{c.content}\n```")
    return "\n\n".join(output)


if __name__ == "__main__":
    mcp.run()
