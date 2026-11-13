"""Model Context Protocol (MCP) server for the Universal Technical AI Tutor.

Designed to spend as little model context as possible, for a frontier model and for a small local
one alike:

1. Two-step retrieval. `buscar_fragmentos_secciones` returns POINTERS (id, book, year, section,
   size and a short excerpt). `leer_fragmentos` returns the full text of the ids worth reading,
   merged with their neighbours and capped by a token budget. `formato="completo"` does both in one
   call for models that handle multi-step tool use badly.
2. Every answer has a budget (`max_tokens`) and says how to continue when it is cut.
3. Metadata is used to filter BEFORE retrieving (`min_year`, `domain`, `tag`, `libro`, `seccion`,
   `code_lang`) and only what helps to cite or navigate is printed, once.
4. Plain text out, no structured duplicate, and stable tool definitions (nothing dynamic in the
   descriptions), so prompt/prefix caches keep hitting.

Tools: `listar_libros_y_secciones`, `buscar_fragmentos_secciones`, `leer_fragmentos`,
`buscar_codigo_yaml`, `consultar_grafo_kuzu`, `consultar_libros_manning`.

Environment (deployment-wide caps, e.g. for a small-context local model):
  RAG_TUTOR_DEFAULT_FORMAT   punteros (default) | completo
  RAG_TUTOR_MAX_HITS         hard cap for top_k (default 10)
  RAG_TUTOR_MAX_READ_TOKENS  hard cap for max_tokens (default 4000)
"""

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

_INSTRUCTIONS = (
    "Technical book library. Cheap to expensive: buscar_fragmentos_secciones(consulta) returns "
    "pointers [id] with a short excerpt; leer_fragmentos(ids) returns the full text of the ones "
    "you need. Filter with min_year, domain, libro or code_lang instead of reading more. "
    "listar_libros_y_secciones only when you need to know which books exist. Cite book, year and "
    "section as printed."
)

try:
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer(
        name="Universal Technical RAG Tutor",
        description="Search and read technical engineering books with metadata filters and a token budget.",
        instructions=_INSTRUCTIONS,
    )
except ImportError:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("Universal Technical RAG Tutor", instructions=_INSTRUCTIONS)

from src.core import AgenticTutorCore
from src.kuzu_graph import KuzuGraphEngine
from src.metadata_engine import load_metadata_registry

tutor = AgenticTutorCore()

DEFAULT_FORMAT = os.getenv("RAG_TUTOR_DEFAULT_FORMAT", "punteros").strip().lower()
MAX_HITS = int(os.getenv("RAG_TUTOR_MAX_HITS", "10"))
MAX_READ_TOKENS = int(os.getenv("RAG_TUTOR_MAX_READ_TOKENS", "4000"))

_GRAPH_HEADER = "[Related Architecture Topology in Knowledge Graph]:"
_JUNK_SECTIONS = re.compile(
    r"^(cover|copyright|dedication|title page|(brief )?table of contents.*|contents|index|about the .*|"
    r"colophon|praise for .*|foreword|acknowledg.*)$",
    re.IGNORECASE,
)


def _tool(fn):
    """Registers a tool that returns plain text only (no duplicated structuredContent)."""
    try:
        return mcp.tool(structured_output=False)(fn)
    except TypeError:  # older SDKs without structured_output
        return mcp.tool()(fn)


# --------------------------------------------------------------------------------------------
# Chunk index: stable ids, section of every chunk, neighbours
# --------------------------------------------------------------------------------------------
def _chunk_id(source: str, content: str) -> str:
    """Deterministic id: same book + same text gives the same id after a re-ingestion."""
    return hashlib.sha1(f"{source}\n{content.strip()}".encode("utf-8", "ignore")).hexdigest()[:10]


class _ChunkIndex:
    """Lookup tables over the BM25 corpus, which keeps every chunk in reading order."""

    def __init__(self, corpus: List[Dict[str, Any]]):
        self.corpus = corpus
        self.by_id: Dict[str, int] = {}
        self.ids: List[str] = []
        self.section: List[str] = []
        current, current_file = "", None
        for i, item in enumerate(corpus):
            meta = item.get("metadata") or {}
            cid = _chunk_id(item.get("source", ""), item.get("content", ""))
            self.ids.append(cid)
            self.by_id.setdefault(cid, i)
            file_key = (item.get("source"), meta.get("filename"), meta.get("chapter"))
            if file_key != current_file:
                current, current_file = "", file_key
            if meta.get("section_title"):
                current = str(meta["section_title"])
            self.section.append(current)

    def same_document(self, a: int, b: int) -> bool:
        ia, ib = self.corpus[a], self.corpus[b]
        ma, mb = ia.get("metadata") or {}, ib.get("metadata") or {}
        return ia.get("source") == ib.get("source") and ma.get("filename") == mb.get("filename")


_index: Optional[_ChunkIndex] = None


def _get_index() -> _ChunkIndex:
    global _index
    if _index is None:
        hybrid = getattr(tutor.retriever, "hybrid_fallback", tutor.retriever)
        _index = _ChunkIndex(getattr(hybrid, "_bm25_corpus", None) or [])
    return _index


# --------------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------------
def _tokens(text: str) -> int:
    """Cheap estimate (about 4 characters per token); good enough to hold a budget."""
    return max(1, len(text) // 4)


def _clean(content: str) -> str:
    """Removes the knowledge-graph header some retrievers prepend, and inline images."""
    if content.startswith(_GRAPH_HEADER):
        content = content.split("\n\n", 1)[1] if "\n\n" in content else ""
    return re.sub(r"!\[[^\]]*\]\([^)]*\)\s*", "", content).strip()


def _label(source: str, meta: Dict[str, Any], section: str = "") -> str:
    """`book (year) > chapter > section`, each part printed once."""
    year = meta.get("publication_year")
    parts = [f"{source} ({year})" if year else source]
    chapter = str(meta.get("chapter") or "").strip()
    section = (section or str(meta.get("section_title") or "")).strip()
    if chapter:
        parts.append(chapter)
    if section and section != chapter:
        parts.append(section)
    if meta.get("page"):
        parts.append(f"p.{meta['page']}")
    if meta.get("timestamp"):
        parts.append(f"@{meta['timestamp']}")
    return " > ".join(parts)


def _excerpt(content: str, query: str, width: int = 220) -> str:
    """One-line excerpt centred on the first query term found in the chunk."""
    flat = re.sub(r"\s+", " ", re.sub(r"[#*`>|]+", " ", content)).strip()
    low = flat.lower()
    pos = -1
    for term in sorted(set(re.findall(r"[a-z0-9_]{4,}", query.lower())), key=lambda t: (-len(t), t)):
        pos = low.find(term)
        if pos >= 0:
            break
    start = max(0, pos - width // 3) if pos > 0 else 0
    cut = flat[start : start + width].strip()
    return ("…" if start > 0 else "") + cut + ("…" if start + width < len(flat) else "")


def _clamp(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(int(value), high))
    except (TypeError, ValueError):
        return default


def _parse_ids(ids: Any) -> List[str]:
    """Accepts a list, or a string such as "[a1b2c3d4e5] 0f9e8d7c6b, 12ab34": small models improvise."""
    raw = " ".join(str(x) for x in ids) if isinstance(ids, (list, tuple)) else str(ids or "")
    seen, out = set(), []
    for tok in re.findall(r"[0-9a-fA-F]{6,10}", raw):
        tok = tok.lower()
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def _merge_overlap(prev: str, nxt: str, window: int = 300) -> str:
    """Drops from `nxt` the text already present at the end of `prev` (splitter overlap)."""
    tail = prev[-window:]
    for size in range(min(len(tail), len(nxt)), 20, -1):
        if tail.endswith(nxt[:size]):
            return nxt[size:].lstrip()
    return nxt


def _hit(chunk) -> Tuple[str, Optional[int]]:
    """→ (id, position in the corpus or None) for a retrieved chunk."""
    raw = chunk.content
    if raw.startswith(_GRAPH_HEADER):
        raw = raw.split("\n\n", 1)[1] if "\n\n" in raw else ""
    cid = _chunk_id(chunk.source, raw)
    return cid, _get_index().by_id.get(cid)


def _retrieve(query: str, top_k: int, **filters) -> list:
    """Asks for one spare candidate (the retriever already reranks ~4x top_k) and drops repeated text."""
    pool = top_k + 2
    chunks = tutor.retriever.retrieve(query, top_k=pool, **filters)
    seen, out = set(), []
    for c in chunks:
        cid, _ = _hit(c)
        if cid in seen or not _clean(c.content):
            continue
        if _JUNK_SECTIONS.match(str((c.metadata or {}).get("chapter") or "").strip()):
            continue  # back-of-book index, table of contents, cover: keyword-dense, no content
        seen.add(cid)
        out.append(c)
        if len(out) >= top_k:
            break
    return out


def _read_blocks(positions: List[int], max_tokens: int) -> Tuple[List[str], List[str]]:
    """Renders corpus positions as merged blocks within the budget → (blocks, ids left unread).

    Positions keep the order given (relevance); neighbours in the same document are merged.
    """
    idx = _get_index()
    order: List[int] = []
    for p in positions:
        if p not in order:
            order.append(p)
    groups: List[List[int]] = []
    for p in order:
        for g in groups:
            if idx.same_document(g[0], p) and (p == g[-1] + 1 or p == g[0] - 1):
                g.append(p)
                g.sort()
                break
        else:
            groups.append([p])

    blocks, pending, used = [], [], 0
    for group in groups:
        if pending:
            pending.extend(idx.ids[p] for p in group)
            continue
        first = idx.corpus[group[0]]
        meta = first.get("metadata") or {}
        text = ""
        for p in group:
            piece = _clean(idx.corpus[p].get("content", ""))
            text = piece if not text else text + "\n\n" + _merge_overlap(text, piece)
        ids = " ".join(idx.ids[p] for p in group)
        head = f"[{ids}] {_label(first.get('source', ''), meta, idx.section[group[0]])}"
        room = max_tokens - used - _tokens(head)
        if _tokens(text) > room:
            if blocks and room < 150:
                pending.extend(idx.ids[p] for p in group)
                continue
            keep = text[: max(room, 150) * 4]
            if "\n\n" in keep[200:]:
                keep = keep[: keep.rfind("\n\n")]
            text = keep.rstrip() + "\n[cut here: budget reached]"
            if len(group) > 1:
                pending.extend(idx.ids[p] for p in group[1:])
        blocks.append(f"{head}\n{text}")
        used += _tokens(head) + _tokens(text)
    return blocks, pending


def _pending_line(pending: List[str], budget: int) -> str:
    return f"Not shown (budget of {budget} tokens): leer_fragmentos(ids=\"{' '.join(pending)}\")"


# --------------------------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------------------------
@_tool
def listar_libros_y_secciones(
    domain: Optional[str] = None,
    min_year: Optional[int] = None,
    tag: Optional[str] = None,
    libro: Optional[str] = None,
    incluir_secciones: bool = False,
) -> str:
    """Book catalog: one line per book (year, domain, tags). Pass `libro` to get its chapter list.

    Args:
        domain: e.g. 'cloud_native', 'mlops', 'ai_agents', 'databases_and_storage'.
        min_year: only books published in or after this year.
        tag: topic tag or word in the title, e.g. 'kubernetes', 'vllm', 'rag'.
        libro: book name or part of it; prints that book's sections.
        incluir_secciones: print sections for every listed book (large; prefer `libro`).
    """
    catalog = load_metadata_registry().get("catalog", {})
    if not catalog:
        return "No books registered in metadata_registry.json. Run 'python src/ingest.py' first."

    lines, books = [], 0
    for name, meta in sorted(catalog.items()):
        tags = meta.get("tags", [])
        year = meta.get("publication_year")
        if domain and domain != meta.get("domain") and domain not in meta.get("secondary_domains", []) and domain not in tags:
            continue
        if min_year and (not year or int(year) < int(min_year)):
            continue
        if tag and tag.lower() not in ", ".join(tags).lower() and tag.lower() not in name.lower():
            continue
        if libro and libro.lower() not in name.lower():
            continue
        sections = [s.get("section", "").strip() for s in meta.get("sections", [])]
        sections = [s for s in sections if s and not _JUNK_SECTIONS.match(s)]
        kind = "video" if meta.get("content_type") == "video_course" else "book"
        labs = " | labs" if meta.get("has_exercises") else ""
        books += 1
        lines.append(
            f"- {name} | Year: {year or 'unknown'} | {meta.get('domain', 'general_technical')} | {kind}{labs} | "
            f"{len(sections)} sections | tags: {', '.join(tags[:5])}"
        )
        if (libro or incluir_secciones) and sections:
            shown = sections[:60] if libro else sections[:12]
            more = f" (+{len(sections) - len(shown)} more: pass libro=)" if len(sections) > len(shown) else ""
            lines.append("  sections: " + " • ".join(shown) + more)

    if not lines:
        return f"No books found matching the specified filters (domain={domain}, min_year={min_year}, tag={tag}, libro={libro})."
    return f"Technical Book Catalog ({books} books)\n" + "\n".join(lines)


@_tool
def buscar_fragmentos_secciones(
    consulta: str,
    top_k: int = 5,
    formato: Optional[str] = None,
    max_tokens: int = 1500,
    domain: Optional[str] = None,
    code_lang: Optional[str] = None,
    libro: Optional[str] = None,
    min_year: Optional[int] = None,
    tag: Optional[str] = None,
    seccion: Optional[str] = None,
) -> str:
    """Searches the books (semantic + keyword + reranker). Returns pointers `[id] book > section` with
    a short excerpt; read the useful ones with leer_fragmentos(ids). No LLM involved.

    Args:
        consulta: concept, term or question. Keywords in the language of the books work best.
        top_k: number of results (default 5).
        formato: 'punteros' (ids + excerpt, cheap) or 'completo' (full text in this same call).
        max_tokens: budget for the answer when formato='completo'.
        domain: 'cloud_native', 'mlops', 'ai_agents'…
        code_lang: only chunks with code in 'yaml', 'go', 'python', 'bash', 'sql', 'rust'.
        libro: book name or part of it.
        min_year: skip books older than this year (avoids deprecated APIs).
        tag: topic tag, e.g. 'kubernetes', 'vllm'.
        seccion: part of a chapter or section title.
    """
    top_k = _clamp(top_k, 1, MAX_HITS, 5)
    fmt = (formato or DEFAULT_FORMAT).strip().lower()
    chunks = _retrieve(
        consulta, top_k, domain=domain, code_lang=code_lang, book=libro, min_year=min_year, tag=tag, section=seccion
    )
    if not chunks:
        return f"No fragments found for '{consulta}' with the applied filters. Try fewer filters or other keywords."

    idx = _get_index()
    hits = [(c, *_hit(c)) for c in chunks]

    if fmt.startswith("comp"):
        budget = _clamp(max_tokens, 200, MAX_READ_TOKENS, 1500)
        known = [pos for _, _, pos in hits if pos is not None]
        blocks, pending = _read_blocks(known, budget) if known else ([], [])
        if not blocks:  # corpus not loaded: fall back to the retrieved text
            blocks = [f"[{cid}] {_label(c.source, c.metadata or {})}\n{_clean(c.content)}" for c, cid, _ in hits]
        out = [f"Retrieved Sections ({len(blocks)} blocks)"] + blocks
        if pending:
            out.append(_pending_line(pending, budget))
        return "\n\n".join(out)

    lines = [f"Retrieved Sections ({len(hits)} pointers). Full text: leer_fragmentos(ids=\"id id\")"]
    for c, cid, pos in hits:
        meta = c.metadata or {}
        content = _clean(c.content)
        section = idx.section[pos] if pos is not None else ""
        lang = meta.get("code_lang")
        code = f" · code:{lang}" if lang and lang != "none" else ""
        lines.append(f"[{cid}] {_label(c.source, meta, section)} · ~{_tokens(content)} tok{code}\n  {_excerpt(content, consulta)}")
    return "\n".join(lines)


@_tool
def leer_fragmentos(ids: str, max_tokens: int = 1500, vecinos: int = 0) -> str:
    """Returns the full text of fragments found with buscar_fragmentos_secciones.

    Args:
        ids: one or more ids, separated by spaces or commas (e.g. "a1b2c3d4e5 0f9e8d7c6b").
        max_tokens: budget for the answer (default 1500). If it is cut, the ids left are listed.
        vecinos: also read this many fragments before and after each id (0-3), for more context.
    """
    idx = _get_index()
    if not idx.corpus:
        return "Chunk index not available. Run 'python src/ingest.py' first."
    wanted = _parse_ids(ids)
    if not wanted:
        return "No valid ids. Pass the ids printed in brackets by buscar_fragmentos_secciones, e.g. ids=\"a1b2c3d4e5\"."
    budget = _clamp(max_tokens, 200, MAX_READ_TOKENS, 1500)
    spread = _clamp(vecinos, 0, 3, 0)

    positions, unknown = [], []
    for cid in wanted:
        pos = idx.by_id.get(cid)
        if pos is None and len(cid) < 10:  # tolerate a truncated id when it is unambiguous
            matches = {full for full in idx.by_id if full.startswith(cid)}
            pos = idx.by_id[matches.pop()] if len(matches) == 1 else None
        if pos is None:
            unknown.append(cid)
            continue
        for p in range(pos - spread, pos + spread + 1):
            if 0 <= p < len(idx.corpus) and idx.same_document(pos, p):
                positions.append(p)

    if not positions:
        return f"Unknown ids: {' '.join(unknown)}. Search again with buscar_fragmentos_secciones."
    blocks, pending = _read_blocks(positions, budget)
    out = list(blocks)
    if pending:
        out.append(_pending_line(pending, budget))
    if unknown:
        out.append(f"Unknown ids skipped: {' '.join(unknown)}")
    return "\n\n".join(out)


@_tool
def buscar_codigo_yaml(
    termino: str,
    code_lang: Optional[str] = None,
    min_year: Optional[int] = None,
    max_tokens: int = 1200,
) -> str:
    """Finds manifests, CRDs, CLI commands or code in the books and returns them verbatim.

    Args:
        termino: resource kind, apiVersion, CLI flag or code to look for.
        code_lang: 'yaml', 'go', 'python', 'bash', 'rust', 'sql'.
        min_year: skip books older than this year (avoids deprecated APIs).
        max_tokens: budget for the answer.
    """
    chunks = _retrieve(termino, 3, code_lang=code_lang, min_year=min_year)
    if not chunks:
        return f"No exact matches found for '{termino}'."
    budget = _clamp(max_tokens, 200, MAX_READ_TOKENS, 1200)
    known = [pos for pos in (_hit(c)[1] for c in chunks) if pos is not None]
    blocks, pending = _read_blocks(known, budget) if known else ([], [])
    if not blocks:
        blocks = [f"[{_hit(c)[0]}] {_label(c.source, c.metadata or {})}\n{_clean(c.content)}" for c in chunks]
    out = [f"Matches found for '{termino}' ({len(blocks)} blocks)"] + blocks
    if pending:
        out.append(_pending_line(pending, budget))
    return "\n\n".join(out)


@_tool
def consultar_grafo_kuzu(concepto: str, limite: int = 12) -> str:
    """Knowledge graph: which concepts relate to this one and which books explain it.

    Args:
        concepto: concept name or id, e.g. 'kubernetes', 'rag', 'ai-agent', 'fine-tuning'.
        limite: maximum number of relations (default 12).
    """
    kuzu_engine = KuzuGraphEngine()
    if not kuzu_engine.available or not kuzu_engine.is_populated():
        return "KùzuDB graph is not initialized. Run 'python src/ingest.py' first."

    rows = kuzu_engine.get_related_concepts(concepto.strip().lower().replace(" ", "-"))
    if not rows:
        cypher = """
        MATCH (a:Concept)-[r:RelatesTo]->(b:Concept)
        WHERE lower(a.name) CONTAINS $q OR lower(b.name) CONTAINS $q OR lower(a.id) CONTAINS $q OR lower(b.id) CONTAINS $q
        RETURN a.id AS src_id, a.name AS src_name, r.relation AS relation, b.id AS tgt_id, b.name AS tgt_name
        LIMIT 25
        """
        rows = kuzu_engine.query_cypher(cypher, {"q": concepto.strip().lower()})
    if not rows:
        return f"No ontological relationships found in KùzuDB for '{concepto}'."

    limit = _clamp(limite, 1, 25, 12)
    seen, lines = set(), []
    for r in rows:
        line = f"- {r['src_name']} --{r['relation']}--> {r['tgt_name']}"
        if line not in seen:
            seen.add(line)
            lines.append(line)
    more = f"\n(+{len(lines) - limit} more: raise limite)" if len(lines) > limit else ""
    head = f"KùzuDB Knowledge Graph Relationships for '{concepto}' ({min(len(lines), limit)} of {len(lines)})"
    return head + "\n" + "\n".join(lines[:limit]) + more


@_tool
def consultar_libros_manning(
    pregunta: str,
    domain: Optional[str] = None,
    code_lang: Optional[str] = None,
    libro: Optional[str] = None,
    min_year: Optional[int] = None,
) -> str:
    """Answers a question with the tutor's own LLM (retrieval + self-reflection), with citations.
    Slower, and needs that LLM configured. Prefer buscar_fragmentos_secciones when you can read
    the sources yourself.

    Args:
        pregunta: the technical question.
        domain: optional domain filter.
        code_lang: optional code language filter.
        libro: optional book name filter.
        min_year: optional minimum publication year.
    """
    result = tutor.ask(pregunta, domain=domain, code_lang=code_lang, book=libro, min_year=min_year)
    if "none" in str(result.get("llm_model", "none")):
        # No LLM answered (not configured or unreachable): do not dump the raw context here.
        return (
            "The tutor's own LLM is not available (set LLM_BASE_URL + LLM_MODEL for any OpenAI-compatible "
            "endpoint, or run Ollama). Use buscar_fragmentos_secciones and leer_fragmentos and answer from the sources."
        )
    sources = ", ".join(result["sources"]) if result.get("sources") else "no specific sources"
    return (
        f"{result['answer']}\n\nSources: {sources}\n"
        f"(LLM {result.get('llm_model')}, {result.get('iterations')} step(s), {result.get('retrieved_chunks')} chunks evaluated)"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="rag-tutor MCP server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "streamable-http", "sse"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
