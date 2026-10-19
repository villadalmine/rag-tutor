"""Script de ingesta incremental, fragmentación técnica e indexación híbrida (ChromaDB + BM25).

Soporta dos modos:
1. Ingesta Incremental (por defecto): Detecta qué libros ya están en ChromaDB y procesa
   ÚNICAMENTE los PDFs nuevos que se hayan agregado a books/, anexándolos sin duplicar.
2. Ingesta Completa / Reset ('--reset' o '--force'): Borra la base existente y reindexa todo desde cero.
"""

import os
import pickle
import shutil
import sys
from pathlib import Path
from typing import List, Set

# Configurar encoding UTF-8 en consola de Windows
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config


def get_indexed_books(chroma_dir: Path) -> Set[str]:
    """Obtiene instantáneamente los nombres de libros ya indexados sin cargar modelos en RAM."""
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
        print(f"[Aviso] No se pudo leer el estado previo de ChromaDB: {e}")
        return set()


def run_ingestion(reset: bool = False):
    """Ejecuta la ingesta técnica de libros con detección incremental automática."""
    print("=" * 65)
    print(" 📚 Ingesta Técnica de Libros de Manning (Modo Incremental)")
    print("=" * 65)

    books_path = Path(config.BOOKS_DIR)
    if not books_path.exists():
        books_path.mkdir(parents=True, exist_ok=True)
        print(f"[!] Directorio creado: {books_path}")
        print("Copia tus archivos PDF de Manning en esa carpeta y vuelve a ejecutar este script.")
        return

    pdf_files = sorted(list(books_path.glob("*.pdf")), key=lambda p: p.name)
    if not pdf_files:
        print(f"[!] No se encontraron archivos PDF en: {books_path}")
        print("Copia tus libros de Manning (.pdf) en esta carpeta para iniciar.")
        return

    # Si se solicitó reset explícito, borrar índices existentes
    if reset:
        print("\n[!] Modo --reset activado: Eliminando índices previos...")
        if config.CHROMA_DIR.exists():
            shutil.rmtree(config.CHROMA_DIR, ignore_errors=True)
        if config.BM25_INDEX_PATH.exists():
            config.BM25_INDEX_PATH.unlink(missing_ok=True)
        already_indexed = set()
    else:
        already_indexed = get_indexed_books(config.CHROMA_DIR)

    # Identificar libros nuevos
    books_to_process = [pdf for pdf in pdf_files if pdf.name not in already_indexed]

    print(f"\n[+] Total de libros encontrados en books/: {len(pdf_files)}")
    if already_indexed:
        print(f"[✓] Libros ya indexados previamente ({len(already_indexed)}):")
        for name in sorted(already_indexed):
            print(f"    • {name}")

    if not books_to_process:
        print("\n" + "=" * 65)
        print(" ✨ Todos los libros de la carpeta books/ ya están indexados.")
        print(" No hay libros nuevos que requieran procesamiento.")
        print(" (Si deseas forzar una reindexación completa desde cero, ejecuta:")
        print("  python src/ingest.py --reset)")
        print("=" * 65)
        return

    print(f"\n[+] Nuevos libros detectados para procesar ({len(books_to_process)}):")
    for pdf in books_to_process:
        print(f"    ➜ {pdf.name}")

    try:
        from langchain_community.document_loaders import PyMuPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        from rank_bm25 import BM25Okapi
    except ImportError as e:
        print(f"[Error de dependencias]: {e}")
        print("Instala los requerimientos con: pip install -r requirements.txt")
        return

    # 1. Extracción de los NUEVOS libros únicamente
    new_raw_docs = []
    for pdf in books_to_process:
        print(f"\n[+] Extrayendo texto y páginas: {pdf.name}...")
        try:
            loader = PyMuPDFLoader(str(pdf))
            docs = loader.load()
            for d in docs:
                d.metadata["source"] = pdf.name
                if "page" in d.metadata:
                    d.metadata["page"] = int(d.metadata["page"]) + 1
            new_raw_docs.extend(docs)
            print(f"    Páginas extraídas: {len(docs)}")
        except Exception as e:
            print(f"    [Error procesando {pdf.name}]: {e}")

    if not new_raw_docs:
        print("[!] No se pudo extraer contenido de los nuevos libros.")
        return

    # 2. Chunking especializado
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=[
            "\n## ",
            "\n### ",
            "\n```yaml",
            "\n```go",
            "\n```bash",
            "\n```",
            "\n\n",
            "\n",
            " ",
        ],
    )
    new_chunks = splitter.split_documents(new_raw_docs)
    print(f"\n[+] Nuevos fragmentos técnicos generados: {len(new_chunks)}")

    # 3. Anexar a ChromaDB
    print(f"[+] Generando embeddings ({config.EMBEDDING_MODEL_NAME}) y guardando en ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

    if already_indexed and config.CHROMA_DIR.exists():
        # Anexar sin reprocesar los libros anteriores
        vectorstore = Chroma(
            persist_directory=str(config.CHROMA_DIR),
            embedding_function=embeddings,
        )
        vectorstore.add_documents(new_chunks)
        print(f"[OK] {len(new_chunks)} fragmentos nuevos anexados a ChromaDB exitosamente.")
    else:
        # Creación inicial
        vectorstore = Chroma.from_documents(
            documents=new_chunks,
            embedding=embeddings,
            persist_directory=str(config.CHROMA_DIR),
        )
        print(f"[OK] ChromaDB creado con éxito en: {config.CHROMA_DIR}")

    # 4. Actualizar índice léxico BM25
    print("[+] Actualizando índice BM25...")
    existing_corpus = []
    if config.BM25_INDEX_PATH.exists() and not reset:
        try:
            with open(config.BM25_INDEX_PATH, "rb") as f:
                data = pickle.load(f)
                existing_corpus = data.get("corpus", [])
        except Exception as e:
            print(f"[Aviso] No se pudo leer el índice BM25 previo: {e}")

    new_corpus_entries = []
    for c in new_chunks:
        new_corpus_entries.append({
            "content": c.page_content,
            "source": c.metadata.get("source", "Manning"),
            "page": c.metadata.get("page"),
            "metadata": c.metadata,
        })

    combined_corpus = existing_corpus + new_corpus_entries
    combined_tokens = [item["content"].lower().split() for item in combined_corpus]
    updated_bm25 = BM25Okapi(combined_tokens)

    with open(config.BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": updated_bm25, "corpus": combined_corpus}, f)

    print(f"[OK] Índice BM25 actualizado con {len(combined_corpus)} fragmentos totales en: {config.BM25_INDEX_PATH}")
    print("\n" + "=" * 65)
    print(" 🎉 Ingesta incremental completada con éxito.")
    print(" Los nuevos libros ya están disponibles para el Tutor en todos los modos.")
    print("=" * 65)


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv or "--force" in sys.argv
    run_ingestion(reset=reset_flag)
