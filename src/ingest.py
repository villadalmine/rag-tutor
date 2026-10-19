"""Script de ingesta incremental, fragmentación técnica e indexación híbrida (ChromaDB + BM25).

Soporta dos modos:
1. Ingesta Incremental (por defecto): Detecta qué libros ya están en ChromaDB y procesa
   ÚNICAMENTE los PDFs nuevos que se hayan agregado a books/, anexándolos sin duplicar.
2. Ingesta Completa / Reset ('--reset' o '--force'): Borra la base existente y reindexa todo desde cero.
"""

import hashlib
import json
import os
import pickle
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set, Dict, Any

# Configurar encoding UTF-8 en consola de Windows
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config

MANIFEST_PATH = ROOT_DIR / "data" / ".ingestion_manifest.json"


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 content hash of a file for change detection."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_ingestion_manifest() -> Dict[str, Any]:
    """Loads recorded file hashes from the ingestion manifest."""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ingestion_manifest(manifest: Dict[str, Any]):
    """Persists updated file hashes to the ingestion manifest."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


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
    manifest = {} if reset else load_ingestion_manifest()
    if reset:
        print("\n[!] Modo --reset activado: Eliminando índices previos...")
        if config.CHROMA_DIR.exists():
            shutil.rmtree(config.CHROMA_DIR, ignore_errors=True)
        if config.BM25_INDEX_PATH.exists():
            config.BM25_INDEX_PATH.unlink(missing_ok=True)
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink(missing_ok=True)
        already_indexed = set()
    else:
        already_indexed = get_indexed_books(config.CHROMA_DIR)

    # Identificar libros nuevos o modificados mediante hash SHA-256
    books_to_process = []
    unchanged_books = []

    for pdf in pdf_files:
        current_hash = compute_file_sha256(pdf)
        recorded = manifest.get(pdf.name, {})
        if pdf.name in already_indexed and recorded.get("sha256") == current_hash:
            unchanged_books.append((pdf.name, current_hash))
        else:
            books_to_process.append((pdf, current_hash))

    print(f"\n[+] Total de libros encontrados en books/: {len(pdf_files)}")
    if unchanged_books:
        print(f"[✓] Libros ya indexados y sin cambios (SHA-256 verificado, {len(unchanged_books)}):")
        for name, h in unchanged_books:
            print(f"    • {name} (sha256: {h[:12]}...)")

    if not books_to_process:
        print("\n" + "=" * 65)
        print(" ✨ Todos los libros de la carpeta books/ ya están indexados.")
        print(" No hay libros nuevos ni modificaciones que requieran cómputo de embeddings.")
        print(" (Si deseas forzar una reindexación completa desde cero, ejecuta:")
        print("  python src/ingest.py --reset)")
        print("=" * 65)
        return

    print(f"\n[+] Libros a procesar o actualizar ({len(books_to_process)}):")
    for pdf, h in books_to_process:
        status = "Nuevo" if pdf.name not in manifest else "Modificado (SHA-256 cambió)"
        print(f"    ➜ {pdf.name} [{status}]")

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
    book_pages_map = {}
    for pdf, current_hash in books_to_process:
        print(f"\n[+] Extrayendo texto y páginas: {pdf.name}...")
        try:
            loader = PyMuPDFLoader(str(pdf))
            docs = loader.load()
            for d in docs:
                d.metadata["source"] = pdf.name
                d.metadata["sha256"] = current_hash
                if "page" in d.metadata:
                    d.metadata["page"] = int(d.metadata["page"]) + 1
            new_raw_docs.extend(docs)
            book_pages_map[pdf.name] = len(docs)
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

    # ChromaDB tiene un límite interno de 5461 documentos por batch (Rust bindings)
    batch_size = 2000
    vectorstore = Chroma(
        persist_directory=str(config.CHROMA_DIR),
        embedding_function=embeddings,
    )
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i : i + batch_size]
        vectorstore.add_documents(batch)
        print(f"    [Progreso ChromaDB] {min(i + batch_size, len(new_chunks))}/{len(new_chunks)} fragmentos guardados...")

    if already_indexed:
        print(f"[OK] {len(new_chunks)} fragmentos nuevos anexados a ChromaDB exitosamente.")
    else:
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

    # 5. Guardar manifiesto de hashes SHA-256 para futuras ejecuciones incrementales instantáneas
    for pdf, current_hash in books_to_process:
        manifest[pdf.name] = {
            "sha256": current_hash,
            "total_pages": book_pages_map.get(pdf.name, 0),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
    save_ingestion_manifest(manifest)
    print(f"[OK] Manifiesto incremental actualizado en: {MANIFEST_PATH}")

    print(f"[OK] Índice BM25 actualizado con {len(combined_corpus)} fragmentos totales en: {config.BM25_INDEX_PATH}")
    print("\n" + "=" * 65)
    print(" 🎉 Ingesta incremental completada con éxito.")
    print(" Los nuevos libros ya están disponibles para el Tutor en todos los modos.")
    print("=" * 65)


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv or "--force" in sys.argv
    run_ingestion(reset=reset_flag)
