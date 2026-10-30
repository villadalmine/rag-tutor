"""Multi-mode Incremental Ingestion Script (PDF, Markdown, TXT, JSON, JSONL),
Deterministic Auto-Profiling (Universal Metadata Engine), and Hybrid + Graph Indexing
(ChromaDB + BM25 + KùzuDB GraphRAG).

Supports placing inside `books/`:
- Individual files: `.pdf`, `.md`, `.markdown`, `.txt`, `.json`, `.jsonl`
- Book folders: e.g., `books/my-book/` containing `.md` or `.txt` chapters inside

Execution modes:
1. Incremental (default): checks 3-layer deduplication (SHA-256 + normalized book ID) and processes only new or modified books.
2. Full reset (`--reset` or `--force`): rebuilds all indices from scratch.
"""

import hashlib
import json
import os
import pickle
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure UTF-8 encoding on console
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.ingest_graph import sync_graph_and_kuzu
from src.metadata_engine import (
    detect_chunk_syntax,
    load_metadata_registry,
    profile_document,
    save_metadata_registry,
)

MANIFEST_PATH = ROOT_DIR / "data" / ".ingestion_manifest.json"
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt", ".json", ".jsonl", ".vtt", ".srt"}


@dataclass
class BookSource:
    """Represents a book unit in `books/` (single file or multi-chapter directory)."""

    name: str
    path: Path
    source_type: str  # "pdf" | "markdown" | "text" | "json" | "jsonl" | "folder_markdown" | "folder_mixed"
    files: List[Path]
    sha256: str


def compute_sha256_for_files(files: List[Path]) -> str:
    """Computes a deterministic SHA-256 hash across one or multiple files."""
    hasher = hashlib.sha256()
    for fp in sorted(files, key=lambda p: str(p)):
        hasher.update(fp.name.encode("utf-8"))
        with open(fp, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    return hasher.hexdigest()


def _normalize_book_id(name: str) -> str:
    """Normalizes a book name (strips extension, '_chunks'/'_book' suffixes, lowercase alphanumeric)
    to detect if the same book was already loaded in another format or filename.
    """
    stem = Path(name).stem.lower()
    stem = re.sub(r"(_chunks|-chunks|_book|-book)$", "", stem)
    return re.sub(r"[^a-z0-9]+", "", stem)


def discover_book_sources(books_dir: Path) -> List[BookSource]:
    """Discovers all books in `books/` (standalone files or book subdirectories)."""
    sources: List[BookSource] = []

    for entry in sorted(books_dir.iterdir(), key=lambda p: p.name):
        if entry.name.startswith("."):
            continue

        if entry.is_file():
            ext = entry.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            stype = {
                ".pdf": "pdf",
                ".md": "markdown",
                ".markdown": "markdown",
                ".txt": "text",
                ".json": "json",
                ".jsonl": "jsonl",
                ".vtt": "vtt",
                ".srt": "srt",
            }[ext]
            sources.append(
                BookSource(
                    name=entry.name,
                    path=entry,
                    source_type=stype,
                    files=[entry],
                    sha256=compute_sha256_for_files([entry]),
                )
            )

        elif entry.is_dir():
            # Search first for Markdown chapters inside the book directory (including .htm inside Markdown/)
            md_files = sorted(
                [
                    p
                    for p in entry.rglob("*")
                    if p.is_file()
                    and (
                        p.suffix.lower() in {".md", ".markdown"}
                        or (p.suffix.lower() == ".htm" and "markdown" in [ part.lower() for part in p.parts ])
                    )
                    and p.name.lower() != "readme.md"
                ]
            )
            if not md_files:
                md_files = sorted(
                    [p for p in entry.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".markdown"}]
                )

            if md_files:
                sources.append(
                    BookSource(
                        name=entry.name,
                        path=entry,
                        source_type="folder_markdown",
                        files=md_files,
                        sha256=compute_sha256_for_files(md_files),
                    )
                )
                continue

            # If no Markdown files exist, check for PDFs, JSONL, JSON, or TXT inside the folder
            other_files = sorted(
                [p for p in entry.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
            )
            if other_files:
                sources.append(
                    BookSource(
                        name=entry.name,
                        path=entry,
                        source_type="folder_mixed",
                        files=other_files,
                        sha256=compute_sha256_for_files(other_files),
                    )
                )

    return sources


def load_ingestion_manifest() -> Dict[str, Any]:
    """Loads the previously indexed SHA-256 ingestion manifest."""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ingestion_manifest(manifest: Dict[str, Any]):
    """Persists the SHA-256 ingestion manifest."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_indexed_books(chroma_dir: Path) -> Set[str]:
    """Instantly retrieves book names already indexed in ChromaDB."""
    if not chroma_dir.exists():
        return set()

    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = [c.name for c in client.list_collections()]
        if "langchain" not in collections:
            return set()
        col = client.get_collection("langchain")
        metadatas = col.get(include=["metadatas"]).get("metadatas", [])
        return {m.get("source") for m in metadatas if m and "source" in m}
    except Exception as e:
        print(f"[Warning] Could not read previous state from ChromaDB: {e}")
        return set()


def _extract_markdown_title(text: str, fallback: str) -> str:
    """Extracts the first H1/H2 title from a Markdown file."""
    m = re.search(r"^#{1,2}\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def _format_vtt_time(hours_prefix: Optional[str], mm_ss: str) -> str:
    """Formats subtitle hours and minutes into clean MM:SS or H:MM:SS."""
    if not hours_prefix:
        return mm_ss
    h = hours_prefix.rstrip(":")
    if h == "00" or h == "0":
        return mm_ss
    return f"{int(h)}:{mm_ss}"


def _parse_vtt_or_srt(text: str) -> str:
    """Universal parser that converts WebVTT (.vtt) and SubRip (.srt) subtitles
    into clean, timestamped text paragraphs with [MM:SS - MM:SS] format for RAG.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues = []
    current_ts = ""
    current_lines = []

    time_re = re.compile(
        r"(?:(\d{1,2}:)?(\d{2}:\d{2})[.,](\d{3}))\s*-->\s*(?:(\d{1,2}:)?(\d{2}:\d{2})[.,](\d{3}))"
    )

    for line in lines:
        line_str = line.strip()
        if not line_str or line_str.upper() == "WEBVTT" or line_str.isdigit():
            continue
        m = time_re.search(line_str)
        if m:
            if current_ts and current_lines:
                cues.append((current_ts, " ".join(current_lines)))
                current_lines = []
            start = _format_vtt_time(m.group(1), m.group(2))
            end = _format_vtt_time(m.group(4), m.group(5))
            current_ts = f"[{start} - {end}]"
        else:
            clean_line = re.sub(r"<[^>]+>", "", line_str).strip()
            if clean_line:
                current_lines.append(clean_line)

    if current_ts and current_lines:
        cues.append((current_ts, " ".join(current_lines)))

    paragraphs = []
    buf_ts_start = ""
    buf_ts_end = ""
    buf_text = []

    for ts, text_content in cues:
        ts_clean = ts.strip("[]")
        parts = ts_clean.split(" - ")
        start_part = parts[0] if parts else ""
        end_part = parts[1] if len(parts) > 1 else start_part
        if not buf_ts_start:
            buf_ts_start = start_part
        buf_ts_end = end_part
        buf_text.append(text_content)

        if sum(len(t) for t in buf_text) >= 280 or len(buf_text) >= 5:
            paragraphs.append(f"**[{buf_ts_start} - {buf_ts_end}]** " + " ".join(buf_text))
            buf_ts_start = ""
            buf_ts_end = ""
            buf_text = []

    if buf_text:
        paragraphs.append(f"**[{buf_ts_start} - {buf_ts_end}]** " + " ".join(buf_text))

    return "\n\n".join(paragraphs) if paragraphs else text


def extract_documents_from_source(source: BookSource) -> List[Any]:
    """Extracts LangChain Document objects from PDF, Markdown, TXT, JSON, JSONL, or folder."""
    from langchain_core.documents import Document

    docs: List[Document] = []

    for fp in source.files:
        ext = fp.suffix.lower()

        if ext == ".pdf":
            from langchain_community.document_loaders import PyMuPDFLoader

            loader = PyMuPDFLoader(str(fp))
            loaded = loader.load()
            for d in loaded:
                d.metadata["source"] = source.name
                d.metadata["sha256"] = source.sha256
                if "page" in d.metadata:
                    d.metadata["page"] = int(d.metadata["page"]) + 1
            docs.extend(loaded)

        elif ext in {".md", ".markdown", ".txt", ".htm"}:
            text = fp.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            chapter_title = _extract_markdown_title(text, fp.stem)
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": source.name,
                        "chapter": chapter_title,
                        "filename": fp.name,
                        "sha256": source.sha256,
                    },
                )
            )

        elif ext == ".json":
            raw = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
            if isinstance(raw, dict) and "chapters" in raw:
                book_title = raw.get("metadata", {}).get("title") or source.name
                for i, ch in enumerate(raw.get("chapters", []), 1):
                    content = ch.get("content", "").strip()
                    if not content:
                        continue
                    docs.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": book_title,
                                "chapter": ch.get("title", f"Chapter {i}"),
                                "page": i,
                                "sha256": source.sha256,
                            },
                        )
                    )
            else:
                docs.append(
                    Document(
                        page_content=json.dumps(raw, ensure_ascii=False, indent=2),
                        metadata={"source": source.name, "sha256": source.sha256},
                    )
                )

        elif ext == ".jsonl":
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    content = item.get("content") or item.get("text") or ""
                    if not content.strip():
                        continue
                    docs.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": item.get("book_title") or source.name,
                                "chapter": item.get("chapter_title") or item.get("title") or f"Chunk {line_idx}",
                                "sha256": source.sha256,
                            },
                        )
                    )

        elif ext in {".vtt", ".srt"}:
            raw_text = fp.read_text(encoding="utf-8", errors="replace").strip()
            if not raw_text:
                continue
            parsed_text = _parse_vtt_or_srt(raw_text)
            title = _extract_markdown_title(parsed_text, fp.stem.replace("_", " ").title())
            docs.append(
                Document(
                    page_content=f"# {title}\n\n**Lesson Type:** Video Lecture\n\n## Video Transcript (Timestamped)\n\n{parsed_text}",
                    metadata={
                        "source": source.name,
                        "chapter": title,
                        "filename": fp.name,
                        "sha256": source.sha256,
                        "content_type": "video_course",
                    },
                )
            )

    return docs


def sync_external_markdown_folders(external_output_dir: Path, books_dir: Path) -> int:
    """Syncs only the `Markdown/` subdirectories from an external export directory into `books/`,
    ignoring heavy binary archives (`.epub`) and raw asset folders (`OEBPS/`).
    """
    if not external_output_dir.exists():
        print(f"[Warning] External source directory not found at: {external_output_dir}")
        return 0

    books_dir.mkdir(parents=True, exist_ok=True)
    synced_count = 0
    for entry in sorted(external_output_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        md_src = entry / "Markdown"
        if not md_src.exists():
            continue
        dest_dir = books_dir / entry.name / "Markdown"
        if not dest_dir.exists():
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(md_src, dest_dir, dirs_exist_ok=True)
            synced_count += 1
        else:
            # Copy any new .md files added later
            shutil.copytree(md_src, dest_dir, dirs_exist_ok=True)
    return synced_count


def run_ingestion(reset: bool = False, sync_source_dir: Optional[Path] = None):
    """Executes multi-mode technical ingestion with 3-layer deduplication and auto-profiling."""
    print("=" * 65)
    print(" 📚 Multi-Mode Technical Ingestion (PDF, Markdown, TXT, JSON, JSONL)")
    print("=" * 65)

    books_path = Path(config.BOOKS_DIR)
    if sync_source_dir is not None:
        print(f"[+] Syncing Markdown chapters from: {sync_source_dir}")
        newly_synced = sync_external_markdown_folders(sync_source_dir, books_path)
        print(f"[OK] Synced Markdown folders ({newly_synced} newly added book directories).")
    if not books_path.exists():
        books_path.mkdir(parents=True, exist_ok=True)
        print(f"[!] Directory created: {books_path}")
        print("Place your books (.pdf, .md, .txt, .json, .jsonl or folders) in books/ and run again.")
        return

    discovered_sources = discover_book_sources(books_path)
    if not discovered_sources:
        print(f"[!] No compatible books found in: {books_path}")
        print("Supported formats in books/: .pdf, .md, .txt, .json, .jsonl or folders with .md chapters")
        return

    manifest = {} if reset else load_ingestion_manifest()
    registry = load_metadata_registry()

    if reset:
        print("\n[!] --reset mode enabled: Removing previous indices...")
        if config.CHROMA_DIR.exists():
            shutil.rmtree(config.CHROMA_DIR, ignore_errors=True)
        if config.BM25_INDEX_PATH.exists():
            config.BM25_INDEX_PATH.unlink(missing_ok=True)
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink(missing_ok=True)
        already_indexed = set()
    else:
        already_indexed = get_indexed_books(config.CHROMA_DIR)

    books_to_process: List[BookSource] = []
    unchanged_books: List[Tuple[BookSource, str]] = []

    existing_hashes = {
        meta.get("sha256"): b_name
        for b_name, meta in manifest.items()
        if meta.get("sha256") and b_name in already_indexed
    }
    existing_norm_names = {_normalize_book_id(b_name): b_name for b_name in already_indexed}
    seen_batch_norms: Dict[str, str] = {}
    seen_batch_hashes: Dict[str, str] = {}

    for src in discovered_sources:
        recorded = manifest.get(src.name, {})
        norm_id = _normalize_book_id(src.name)

        # 1. Exact match by source name and SHA-256 hash
        if src.name in already_indexed and recorded.get("sha256") == src.sha256:
            unchanged_books.append((src, f"Identical SHA-256 ({src.sha256[:10]}...)"))
            continue

        # 2. Exact content SHA-256 match under a different filename/folder
        if src.sha256 in existing_hashes and existing_hashes[src.sha256] != src.name:
            unchanged_books.append((src, f"Duplicate content of '{existing_hashes[src.sha256]}'"))
            continue
        if src.sha256 in seen_batch_hashes:
            unchanged_books.append((src, f"Duplicate content in batch of '{seen_batch_hashes[src.sha256]}'"))
            continue

        # 3. Normalized book title match across formats (e.g. PDF vs Markdown folder)
        if norm_id in existing_norm_names and existing_norm_names[norm_id] != src.name:
            unchanged_books.append((src, f"Title already indexed as '{existing_norm_names[norm_id]}'"))
            continue
        if norm_id in seen_batch_norms:
            unchanged_books.append((src, f"Title already in batch as '{seen_batch_norms[norm_id]}'"))
            continue

        seen_batch_norms[norm_id] = src.name
        seen_batch_hashes[src.sha256] = src.name
        books_to_process.append(src)

    print(f"\n[+] Total sources discovered in books/: {len(discovered_sources)}")
    if unchanged_books:
        print(f"[✓] Sources automatically skipped to prevent duplicates ({len(unchanged_books)}):")
        for src, reason in unchanged_books:
            print(f"    • {src.name} [{src.source_type}] ➜ Skipped ({reason})")

    if not books_to_process:
        print("\n" + "=" * 65)
        print(" ✨ All books in books/ are already indexed.")
        print(" (To force a full re-index from scratch, run:")
        print("  python src/ingest.py --reset)")
        print("=" * 65)
        return

    print(f"\n[+] Sources to process or update ({len(books_to_process)}):")
    for src in books_to_process:
        status = "New" if src.name not in manifest else "Modified (SHA-256 changed)"
        print(f"    ➜ {src.name} ({src.source_type}, {len(src.files)} file(s)) [{status}]")

    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from rank_bm25 import BM25Okapi
    except ImportError as e:
        print(f"[Dependency Error]: {e}")
        print("Install requirements with: pip install -r requirements.txt")
        return

    # 1. Extraction and Deterministic Auto-Profiling (Universal Metadata Engine)
    new_raw_docs = []
    book_units_map: Dict[str, int] = {}

    for src in books_to_process:
        print(f"\n[+] Extracting content: {src.name} ({src.source_type})...")
        try:
            docs = extract_documents_from_source(src)
            if not docs:
                print(f"    [Warning] No extractable text found in {src.name}")
                continue

            # Prioritize copyright/titlepage/readme files + first and last chapters
            priority_docs = [
                d
                for d in docs
                if any(
                    k in str(d.metadata.get("filename", "")).lower()
                    for k in ("copyright", "title", "colophon", "preface", "readme")
                )
            ]
            sample_docs = priority_docs + docs[:8] + (docs[-5:] if len(docs) > 8 else [])
            sample_text = "\n".join(d.page_content for d in sample_docs)
            profile = profile_document(src.name, sample_text, len(docs), registry, docs=docs)
            domain = profile["domain"]
            pub_year = profile.get("publication_year")
            tags_str = ", ".join(profile.get("tags", []))
            content_type = profile.get("content_type", "book")

            for d in docs:
                d.metadata["source"] = src.name
                d.metadata["domain"] = domain
                d.metadata["tags"] = tags_str
                d.metadata["content_type"] = content_type
                if pub_year:
                    d.metadata["publication_year"] = int(pub_year)

            new_raw_docs.extend(docs)
            book_units_map[src.name] = len(docs)
            year_label = f" | Year: {pub_year}" if pub_year else " | Year: N/A"
            type_label = f" | Type: {content_type}"
            print(f"    Units/chapters: {len(docs)}{type_label}{year_label} | Domain: {domain} | Tags: [{tags_str}]")
        except Exception as e:
            print(f"    [Error processing {src.name}]: {e}")

    if not new_raw_docs:
        print("[!] Could not extract content from the new sources.")
        return

    save_metadata_registry(registry)
    print(f"\n[OK] Metadata catalog updated at: {config.BASE_DIR / 'metadata_registry.json'}")

    # 2. Specialized chunking preserving Markdown headings and fenced code blocks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=[
            "\n# ",
            "\n## ",
            "\n### ",
            "\n#### ",
            "\n```yaml",
            "\n```go",
            "\n```python",
            "\n```rust",
            "\n```sql",
            "\n```bash",
            "\n```",
            "\n\n",
            "\n",
            " ",
        ],
    )
    new_chunks = splitter.split_documents(new_raw_docs)

    # Detect code syntax, section headings, universal video timestamps, and exercises per chunk
    code_chunks_count = 0
    video_ts_chunks_count = 0
    exercise_chunks_count = 0
    for ch in new_chunks:
        syntax_meta = detect_chunk_syntax(ch.page_content)
        ch.metadata["has_code"] = syntax_meta["has_code"]
        ch.metadata["code_lang"] = syntax_meta["code_lang"]
        ch.metadata["is_heading"] = syntax_meta["is_heading"]
        if syntax_meta["section_title"] and "section_title" not in ch.metadata:
            ch.metadata["section_title"] = syntax_meta["section_title"]
        if syntax_meta.get("timestamp"):
            ch.metadata["timestamp"] = syntax_meta["timestamp"]
            video_ts_chunks_count += 1
        if syntax_meta.get("has_exercise"):
            ch.metadata["has_exercise"] = True
            exercise_chunks_count += 1
        if syntax_meta["has_code"]:
            code_chunks_count += 1

    print(
        f"[+] New technical chunks generated: {len(new_chunks)} "
        f"({code_chunks_count} with code, {video_ts_chunks_count} with video timestamps, {exercise_chunks_count} with exercises)"
    )

    # 3. Append to ChromaDB
    print(f"[+] Generating embeddings ({config.EMBEDDING_MODEL_NAME}) and saving to ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

    batch_size = 2000
    vectorstore = Chroma(
        persist_directory=str(config.CHROMA_DIR),
        embedding_function=embeddings,
    )
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i : i + batch_size]
        vectorstore.add_documents(batch)
        print(
            f"    [ChromaDB Progress] {min(i + batch_size, len(new_chunks))}/{len(new_chunks)} chunks saved..."
        )

    print(f"[OK] ChromaDB updated at: {config.CHROMA_DIR}")

    # 4. Update lexical BM25 index
    print("[+] Updating BM25 index...")
    existing_corpus = []
    if config.BM25_INDEX_PATH.exists() and not reset:
        try:
            with open(config.BM25_INDEX_PATH, "rb") as f:
                data = pickle.load(f)
                existing_corpus = data.get("corpus", [])
        except Exception as e:
            print(f"[Warning] Could not read previous BM25 index: {e}")

    new_corpus_entries = []
    for c in new_chunks:
        new_corpus_entries.append(
            {
                "content": c.page_content,
                "source": c.metadata.get("source", "Technical Book"),
                "page": c.metadata.get("page"),
                "metadata": c.metadata,
            }
        )

    combined_corpus = existing_corpus + new_corpus_entries
    combined_tokens = [item["content"].lower().split() for item in combined_corpus]
    updated_bm25 = BM25Okapi(combined_tokens)

    with open(config.BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": updated_bm25, "corpus": combined_corpus}, f)

    print(
        f"[OK] BM25 index updated with {len(combined_corpus)} total chunks at: {config.BM25_INDEX_PATH}"
    )

    # 5. Synchronize Ontological Graph and KùzuDB (Phase 2 GraphRAG)
    print("[+] Synchronizing Ontological Graph and KùzuDB engine (Phase 2 GraphRAG)...")
    try:
        kg = sync_graph_and_kuzu(corpus=combined_corpus, catalog=registry.get("catalog", {}))
        print(
            f"[OK] Graph updated ({len(kg.nodes)} nodes, {len(kg.edges)} edges) at: {config.GRAPH_DATA_PATH}"
        )
    except Exception as e:
        print(f"[Warning] Could not synchronize ontological graph: {e}")

    # 6. Save SHA-256 ingestion manifest
    for src in books_to_process:
        manifest[src.name] = {
            "sha256": src.sha256,
            "source_type": src.source_type,
            "total_units": book_units_map.get(src.name, 0),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
    save_ingestion_manifest(manifest)
    print(f"[OK] Incremental manifest updated at: {MANIFEST_PATH}")

    print("\n" + "=" * 65)
    print(" 🎉 Incremental ingestion completed successfully.")
    print(" New books are now available across all Tutor modes (CLI, MCP, GraphRAG).")
    print("=" * 65)


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv or "--force" in sys.argv
    sync_dir: Optional[Path] = None
    for flag in ("--sync-dir", "--sync-markdown"):
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
                sync_dir = Path(sys.argv[idx + 1]).resolve()
    run_ingestion(reset=reset_flag, sync_source_dir=sync_dir)
