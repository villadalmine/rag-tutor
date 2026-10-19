"""Script de ingesta, fragmentación técnica e indexación híbrida (ChromaDB + BM25)."""

import os
import pickle
from pathlib import Path
from typing import List

from src import config


def run_ingestion():
    """Procesa los PDFs de la carpeta books/ y genera los índices de búsqueda."""
    print("=" * 60)
    print(" Iniciando Ingesta Técnica: Libros de Manning")
    print("=" * 60)

    books_path = Path(config.BOOKS_DIR)
    if not books_path.exists():
        books_path.mkdir(parents=True, exist_ok=True)
        print(f"[!] Directorio creado: {books_path}")
        print("Por favor, copia tus archivos PDF de Manning en esa carpeta y vuelve a ejecutar este script.")
        return

    pdf_files = list(books_path.glob("*.pdf"))
    if not pdf_files:
        print(f"[!] No se encontraron archivos PDF en: {books_path}")
        print("Copia tus libros de Manning (.pdf) en esta carpeta para iniciar.")
        return

    print(f"[+] Se encontraron {len(pdf_files)} libro(s) PDF para procesar:")
    for pdf in pdf_files:
        print(f"    - {pdf.name}")

    try:
        from langchain_community.document_loaders import PyMuPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        from rank_bm25 import BM25Okapi
    except ImportError as e:
        print(f"[Error de dependencias]: {e}")
        print("Asegúrate de instalar los requerimientos con: pip install -r requirements.txt")
        return

    all_raw_docs = []
    for pdf in pdf_files:
        print(f"\n[+] Cargando y extrayendo texto: {pdf.name}...")
        try:
            loader = PyMuPDFLoader(str(pdf))
            docs = loader.load()
            for d in docs:
                # Normalizamos metadatos para trazabilidad
                d.metadata["source"] = pdf.name
                if "page" in d.metadata:
                    d.metadata["page"] = int(d.metadata["page"]) + 1  # 1-indexed para humanos
            all_raw_docs.extend(docs)
            print(f"    Páginas extraídas: {len(docs)}")
        except Exception as e:
            print(f"    [Error procesando {pdf.name}]: {e}")

    if not all_raw_docs:
        print("[!] No se pudo extraer contenido de los PDFs.")
        return

    print(f"\n[+] Total de páginas extraídas: {len(all_raw_docs)}")
    print("[+] Aplicando chunking especializado en código, YAML y teoría...")

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

    chunks = splitter.split_documents(all_raw_docs)
    print(f"[+] Fragmentos técnicos generados: {len(chunks)}")

    # 1. Indexación Vectorial en ChromaDB
    print(f"\n[+] Generando embeddings ({config.EMBEDDING_MODEL_NAME}) e indexando en ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(config.CHROMA_DIR),
    )
    print(f"[✓] ChromaDB guardado exitosamente en: {config.CHROMA_DIR}")

    # 2. Generación e Indexación Léxica BM25
    print("\n[+] Construyendo índice BM25 para coincidencia exacta de código y comandos...")
    corpus_entries = []
    tokenized_corpus = []

    for c in chunks:
        content = c.page_content
        corpus_entries.append({
            "content": content,
            "source": c.metadata.get("source", "Manning"),
            "page": c.metadata.get("page"),
            "metadata": c.metadata,
        })
        tokenized_corpus.append(content.lower().split())

    bm25 = BM25Okapi(tokenized_corpus)
    with open(config.BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "corpus": corpus_entries}, f)

    print(f"[✓] Índice BM25 guardado exitosamente en: {config.BM25_INDEX_PATH}")
    print("\n" + "=" * 60)
    print(" ¡Ingesta completada con éxito!")
    print(" Ahora puedes iniciar el servidor MCP ('python src/mcp_server.py')")
    print(" o la API REST ('python src/api.py').")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()
