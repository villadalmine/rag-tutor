"""Interactive and Single-Query CLI for Universal Technical AI Tutor."""

import sys
from pathlib import Path

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


def run_single_query(tutor: AgenticTutorCore, question: str):
    """Executes a single query and prints formatted response and telemetry."""
    print(f"\n🔍 Querying technical library...")
    result = tutor.ask(question)

    print("\n" + "=" * 65)
    print("💡 Tutor Response:")
    print("=" * 65)
    print(result["answer"])

    print("\n" + "-" * 65)
    print("📖 Consulted Sources:")
    for src in result["sources"]:
        print(f"  • {src}")

    engine_name = "GraphRAG Omnigraph (Phase 2)" if result.get("retriever_engine") == "omnigraph" else "Hybrid ChromaDB + BM25 (Phase 1)"
    print("\n🔬 Models & Engine Telemetry:")
    print(f"  • RAG Engine:       {engine_name}")
    print(f"  • LLM Model:        {result.get('llm_model')} (Local Ollama Inference)")
    print(f"  • Embeddings:       {result.get('embedding_model')}")
    print(f"  • Reranker:         {result.get('reranker_model')}")
    print(f"  • Agentic Steps:    {result.get('iterations')} iteration(s) | {result.get('retrieved_chunks')} candidate chunks analyzed")
    print("-" * 65)


def main():
    tutor = AgenticTutorCore()

    # If question passed via command line argument:
    # Example: python src/cli.py "Explain how to design a reactive AI Agent"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_single_query(tutor, question)
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
            run_single_query(tutor, question)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


if __name__ == "__main__":
    main()

