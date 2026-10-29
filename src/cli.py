"""Interactive and Single-Query CLI for Universal Technical AI Tutor."""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Configure UTF-8 encoding on Windows console
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core import AgenticTutorCore


def print_banner():
    print("=" * 65)
    print(" 📚 Universal Technical AI Tutor (Interactive Console)")
    print(" Type your technical query or 'exit' / 'quit' to exit.")
    print("=" * 65)


def run_single_query(
    tutor: AgenticTutorCore,
    question: str,
    domain: Optional[str] = None,
    code_lang: Optional[str] = None,
    book: Optional[str] = None,
    min_year: Optional[int] = None,
    tag: Optional[str] = None,
    section: Optional[str] = None,
    no_llm: bool = False,
):
    """Executes a single query and prints formatted response and telemetry."""
    filters_info = []
    if domain:
        filters_info.append(f"domain={domain}")
    if code_lang:
        filters_info.append(f"code={code_lang}")
    if book:
        filters_info.append(f"book={book}")
    if min_year:
        filters_info.append(f"min_year>={min_year}")
    if tag:
        filters_info.append(f"tag={tag}")
    if section:
        filters_info.append(f"section={section}")
    if no_llm:
        filters_info.append("mode=no-llm")
    filter_str = f" [{', '.join(filters_info)}]" if filters_info else ""

    print(f"\n🔍 Querying technical library{filter_str}...")
    result = tutor.ask(
        question,
        domain=domain,
        code_lang=code_lang,
        book=book,
        min_year=min_year,
        tag=tag,
        section=section,
        no_llm=no_llm,
    )

    print("\n" + "=" * 65)
    print("💡 Retrieved Context (No-LLM Mode):" if no_llm else "💡 Tutor Response:")
    print("=" * 65)
    print(result["answer"])

    print("\n" + "-" * 65)
    print("📖 Consulted Sources:")
    for src in result["sources"]:
        print(f"  • {src}")

    engine_name = "GraphRAG Omnigraph (Phase 2)" if result.get("retriever_engine") == "omnigraph" else "Hybrid ChromaDB + BM25 (Phase 1)"
    print("\n🔬 Models & Engine Telemetry:")
    print(f"  • RAG Engine:       {engine_name}")
    print(f"  • LLM Model:        {result.get('llm_model')}")
    print(f"  • Embeddings:       {result.get('embedding_model')}")
    print(f"  • Reranker:         {result.get('reranker_model')}")
    print(f"  • Agentic Steps:    {result.get('iterations')} iteration(s) | {result.get('retrieved_chunks')} candidate chunks analyzed")
    print("-" * 65)


def main():
    parser = argparse.ArgumentParser(description="Universal Technical AI Tutor CLI")
    parser.add_argument("question", nargs="*", help="Technical query to ask the tutor")
    parser.add_argument("--domain", type=str, default=None, help="Filter by domain (e.g. cloud_native, databases_and_storage, mlops, ai_agents)")
    parser.add_argument("--code", type=str, default=None, help="Filter by code language (e.g. yaml, go, python, sql, rust, bash, typescript)")
    parser.add_argument("--book", type=str, default=None, help="Filter by specific book name (substring or exact)")
    parser.add_argument("--min-year", type=int, default=None, help="Only search books published on or after this year (e.g. 2024)")
    parser.add_argument("--tag", type=str, default=None, help="Filter by specific topic tag (e.g. kubernetes, vllm, rag, inference)")
    parser.add_argument("--section", type=str, default=None, help="Filter by chapter or section title substring (e.g. 'Deploying Models')")
    parser.add_argument("--no-llm", "--retrieve-only", dest="no_llm", action="store_true", help="Run retrieval, reranking, and KùzuDB graph traversal without invoking Ollama LLM")
    parser.add_argument("--list-books", action="store_true", help="List all indexed books with their domain, publication year, tags, and sections")
    parser.add_argument("--set-book", type=str, default=None, help="Book name to manually update in metadata_registry.json")
    parser.add_argument("--set-domain", type=str, default=None, help="New primary domain for --set-book")
    parser.add_argument("--set-tags", type=str, default=None, help="Comma-separated tags for --set-book (e.g. 'kubernetes,vllm,rag')")
    parser.add_argument("--set-year", type=int, default=None, help="Publication year override for --set-book")
    args = parser.parse_args()

    if args.set_book:
        from src.metadata_engine import update_book_metadata
        tags_list = [t.strip() for t in args.set_tags.split(",")] if args.set_tags else None
        updated = update_book_metadata(
            book_name=args.set_book,
            domain=args.set_domain,
            tags=tags_list,
            publication_year=args.set_year,
        )
        for k, v in updated.items():
            print(f"✅ Metadata updated for '{k}' (auto_generated=False):")
            print(f"   • Domain: {v.get('domain')}")
            print(f"   • Year:   {v.get('publication_year')}")
            print(f"   • Tags:   {v.get('tags')}")
        print("💡 Run 'python src/ingest.py --force' if you want to re-sync ChromaDB/BM25 chunk metadata.")
        return

    if args.list_books:
        from src.mcp_server import listar_libros_y_secciones
        print(listar_libros_y_secciones(domain=args.domain, min_year=args.min_year, tag=args.tag))
        return

    tutor = AgenticTutorCore()

    if args.question:
        question = " ".join(args.question)
        run_single_query(
            tutor,
            question,
            domain=args.domain,
            code_lang=args.code,
            book=args.book,
            min_year=args.min_year,
            tag=args.tag,
            section=args.section,
            no_llm=args.no_llm,
        )
        return

    # If no arguments, launch interactive chat mode
    print_banner()
    while True:
        try:
            print("\n> Question:")
            question = input().strip()
            if not question:
                continue
            if question.lower() in ["salir", "exit", "quit", "q"]:
                print("Goodbye!")
                break
            run_single_query(
                tutor,
                question,
                domain=args.domain,
                code_lang=args.code,
                book=args.book,
                min_year=args.min_year,
                tag=args.tag,
                section=args.section,
                no_llm=args.no_llm,
            )
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


if __name__ == "__main__":
    main()

