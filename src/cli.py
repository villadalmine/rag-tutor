"""CLI interactivo y de comandos para el Tutor de Manning."""

import sys
from pathlib import Path

# Configurar encoding UTF-8 en consola de Windows
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
    print(" 📚 Manning Platform & AI Tutor (Consola Interactiva)")
    print(" Escribe tu consulta técnica o 'salir' / 'exit' para terminar.")
    print("=" * 65)


def run_single_query(tutor: AgenticTutorCore, question: str):
    """Ejecuta una consulta individual y muestra la respuesta formateada."""
    print(f"\n🔍 Consultando biblioteca técnica...")
    result = tutor.ask(question)

    print("\n" + "=" * 65)
    print("💡 Respuesta del Tutor:")
    print("=" * 65)
    print(result["answer"])

    print("\n" + "-" * 65)
    print("📖 Fuentes consultadas:")
    for src in result["sources"]:
        print(f"  • {src}")

    engine_name = "GraphRAG Omnigraph (Fase 2)" if result.get("retriever_engine") == "omnigraph" else "Híbrido ChromaDB + BM25 (Fase 1)"
    print("\n🔬 Modelos y Motor Utilizados en la Investigación:")
    print(f"  • Motor RAG:        {engine_name}")
    print(f"  • Modelo LLM:       {result.get('llm_model')} (Inferencia Local Ollama)")
    print(f"  • Embeddings:       {result.get('embedding_model')}")
    print(f"  • Reranker:         {result.get('reranker_model')}")
    print(f"  • Pasos Agénticos:  {result.get('iterations')} iteración(es) | {result.get('retrieved_chunks')} fragmentos técnicos analizados")
    print("-" * 65)


def main():
    tutor = AgenticTutorCore()

    # Si se pasa la pregunta como argumento de línea de comandos:
    # Ejemplo: python src/cli.py "Explica cómo diseñar un agente de IA reactivo"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_single_query(tutor, question)
        return

    # Si no hay argumentos, iniciar modo chat interactivo
    print_banner()
    while True:
        try:
            print("\n> Pregunta:")
            question = input().strip()
            if not question:
                continue
            if question.lower() in ["salir", "exit", "quit", "q"]:
                print("¡Hasta luego!")
                break
            run_single_query(tutor, question)
        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada.")
            break


if __name__ == "__main__":
    main()
