"""Automated End-to-End Verification Suite WITHOUT an LLM (No Ollama Required).

Demonstrates and validates that:
1. The Universal Metadata Engine deterministically extracts `publication_year`, `domain`, `tags`,
   `sections` (chapter/H2/H3 tree), and `code_lang` without an LLM.
2. Progressive MCP tools (`listar_libros_y_secciones`, `buscar_fragmentos_secciones`,
   `consultar_grafo_kuzu`, `buscar_codigo_yaml`) work with zero LLM dependency and minimal token footprint.
3. SQL-like WHERE filters (`min_year`, `domain`, `tag`, `section`, `code_lang`, `book`) filter
   ChromaDB + BM25 + Cross-Encoder Reranker + KùzuDB GraphRAG accurately.

Usage:
    python tests/test_no_llm_pipeline.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core import AgenticTutorCore
from src.mcp_server import (
    buscar_codigo_yaml,
    buscar_fragmentos_secciones,
    consultar_grafo_kuzu,
    listar_libros_y_secciones,
)
from src.metadata_engine import (
    detect_chunk_syntax,
    load_metadata_registry,
    profile_document,
)


def test_1_deterministic_metadata_engine():
    print("\n=== [TEST 1] Deterministic Metadata Engine (Year, Domain, Sections, Syntax) ===")
    sample_texts = [
        "# Document Overview\n**Title:** Cloud-Native AI Infrastructure Guide\nCopyright © 2026 Technical Press.\n**Publication Date:** 2026-03-10",
        "# Chapter 3. Deploying Models on Kubernetes\n## Serving LLMs with vLLM and Ray\nWe deploy pods with GPU scheduling on Kubernetes clusters using Helm and Prometheus.",
    ]
    profile = profile_document("cloud-native-ai-infrastructure-guide", sample_texts, total_units=22)
    assert profile["publication_year"] == 2026, f"Expected year 2026, got {profile['publication_year']}"
    assert profile["domain"] in ("cloud_native", "mlops", "ai_agents"), f"Unexpected domain: {profile['domain']}"
    assert len(profile["sections"]) >= 1, "Expected at least 1 extracted section"

    chunk_meta = detect_chunk_syntax(
        "## Serving LLMs with vLLM\n```yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: vllm-server\n```"
    )
    assert chunk_meta["has_code"] is True
    assert chunk_meta["code_lang"] == "yaml"
    assert chunk_meta["section_title"] == "Serving LLMs with vLLM"
    print(
        f"  [PASS] Detected Year={profile['publication_year']}, Domain={profile['domain']}, "
        f"Tags={profile['tags']}, Code={chunk_meta['code_lang']}"
    )


def test_2_mcp_catalog_and_sections():
    print("\n=== [TEST 2] MCP Tool: listar_libros_y_secciones (Zero-Token-Burn Index) ===")
    registry = load_metadata_registry()
    catalog = registry.get("catalog", {})
    assert len(catalog) > 0, "Catalog is empty! Run 'python src/ingest.py' before running tests."

    out_all = listar_libros_y_secciones(incluir_secciones=True)
    assert "Technical Book Catalog" in out_all
    assert "Year:" in out_all
    print(f"  [PASS] Catalog summary returned ({len(out_all)} chars, {len(catalog)} book(s) indexed)")

    out_future = listar_libros_y_secciones(min_year=2099)
    assert "No books found" in out_future
    print("  [PASS] WHERE min_year=2099 accurately filtered out older books")


def test_3_where_filtered_retrieval_no_llm():
    print("\n=== [TEST 3] Hybrid + KùzuDB Retrieval & Reranking WITHOUT LLM (WHERE Filters) ===")
    tutor = AgenticTutorCore()

    # 3a. Standard retrieve_only with min_year and domain filter
    res = tutor.retrieve_only(
        "How to deploy and serve LLMs with vLLM on Kubernetes?",
        top_k=3,
        domain="cloud_native",
        min_year=2024,
        tag="kubernetes",
    )
    chunks = res["chunks"]
    assert len(chunks) > 0, "Expected at least 1 chunk for vLLM on Kubernetes"
    top_chunk = chunks[0]
    assert top_chunk.metadata.get("publication_year", 0) >= 2024
    assert top_chunk.metadata.get("domain") == "cloud_native"
    assert "[Related Architecture Topology in Knowledge Graph]:" in top_chunk.content
    print(
        f"  [PASS] retrieve_only (Omnigraph + KùzuDB) returned {len(chunks)} chunks | Top source: {top_chunk.to_citation()} "
        f"| Score: {top_chunk.score:.4f}"
    )

    # 3b. Filter by section title (WHERE section LIKE '%Deploying%')
    res_sec = tutor.retrieve_only(
        "model serving architecture",
        top_k=2,
        section="Chapter",
    )
    assert len(res_sec["chunks"]) > 0, "Expected chunks matching section filter 'Chapter'"
    print(f"  [PASS] WHERE section='Chapter' returned {len(res_sec['chunks'])} chunks")

    # 3c. Negative filter test (WHERE min_year >= 2099)
    res_empty = tutor.retrieve_only("Kubernetes pod", min_year=2099)
    assert len(res_empty["chunks"]) == 0, "Expected 0 chunks for min_year=2099"
    print("  [PASS] WHERE min_year=2099 returned 0 chunks as expected")


def test_4_mcp_fragment_code_and_kuzu_tools_no_llm():
    print("\n=== [TEST 4] MCP Tools: buscar_fragmentos_secciones, consultar_grafo_kuzu & buscar_codigo_yaml ===")
    frag_output = buscar_fragmentos_secciones(
        consulta="vLLM Kubernetes GPU",
        top_k=2,
        domain="cloud_native",
        min_year=2024,
        tag="kubernetes",
    )
    assert "Retrieved Sections" in frag_output
    assert "Year: 2026" in frag_output
    print("  [PASS] buscar_fragmentos_secciones returned grounded fragments with [2026] badge")

    kuzu_output = consultar_grafo_kuzu("kubernetes")
    assert "KùzuDB Knowledge Graph Relationships" in kuzu_output
    assert "EXPLAINS" in kuzu_output or "COVERS_CONCEPT" in kuzu_output
    print("  [PASS] consultar_grafo_kuzu returned Cypher graph relationships from KùzuDB")

    code_output = buscar_codigo_yaml(
        termino="apiVersion kind Deployment",
        code_lang="yaml",
        min_year=2024,
    )
    assert "Matches found" in code_output
    print("  [PASS] buscar_codigo_yaml returned exact YAML code blocks without LLM")


if __name__ == "__main__":
    print("🚀 Running LLM-Free Automated Verification Suite for rag-tutor...")
    test_1_deterministic_metadata_engine()
    test_2_mcp_catalog_and_sections()
    test_3_where_filtered_retrieval_no_llm()
    test_4_mcp_fragment_code_and_kuzu_tools_no_llm()
    print("\n✅ ALL LLM-FREE RAG, KÙZUDB GRAPHRAG & METADATA WHERE-FILTER TESTS PASSED!")
