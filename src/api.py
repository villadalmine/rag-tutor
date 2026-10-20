"""API REST FastAPI para el Tutor de Manning (compatible con Web UIs y Open WebUI).

Soporta dos modalidades:
1. Búsqueda directa sobre el corpus de libros técnicos (RAG híbrido + KùzuDB GraphRAG).
2. Orquestación Tri-MCP (/mcp/status, /mcp/test y /chat con enriquecimiento multi-servidor).
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Sibling k8s-docs-mcp path
K8S_DOCS_SRC = ROOT_DIR.parent / "k8s-docs-mcp" / "src"
if K8S_DOCS_SRC.exists() and str(K8S_DOCS_SRC) not in sys.path:
    sys.path.insert(0, str(K8S_DOCS_SRC))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src import config
from src.core import AgenticTutorCore
from src.retrievers.base import RetrievedChunk

# Import k8s-docs-mcp tools if available
try:
    from k8s_docs_mcp.server import (
        check_api_version as k8s_check_api,
        get_canonical_manifest as k8s_get_manifest,
        search_k8s_docs as k8s_search_docs,
        store as k8s_store,
    )
    K8S_DOCS_AVAILABLE = True
except Exception:
    K8S_DOCS_AVAILABLE = False
    k8s_store = None

app = FastAPI(
    title="Cloud Native Sovereign RAG & Tri-MCP Gateway API",
    description="API REST para interactuar con el Tutor RAG Agéntico y orquestar la Trifecta de servidores MCP (study-cybercirujas, k8s-docs-mcp, rag-tutor).",
    version="1.2.0",
)

tutor = AgenticTutorCore()


# ----------------------------------------------------------------------
# Modelos de Datos (Pydantic Schemas)
# ----------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(..., description="Pregunta técnica sobre arquitectura, certificaciones o Kubernetes.")
    orchestrate_tri_mcp: bool = Field(
        True,
        description="Si es True, consulta automáticamente study-cybercirujas y k8s-docs-mcp para enriquecer la respuesta con el temario oficial y YAMLs canónicos.",
    )


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    iterations: int
    retrieved_chunks: int
    retriever_engine: str
    llm_model: str
    embedding_model: str
    reranker_model: str
    mcp_enrichment: Dict[str, Any]


class McpTestRequest(BaseModel):
    target: str = Field("all", description="Servidor MCP objetivo a probar: 'study', 'k8s-docs', o 'all'")
    query: str = Field("admission controllers", description="Término técnico o Kind para la prueba de verificación")


# ----------------------------------------------------------------------
# Helpers de Conexión a Servidores MCP
# ----------------------------------------------------------------------

def _fetch_study_search(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Consulta la API de búsqueda de study-cybercirujas con fallback de términos."""
    base_urls = [
        os.getenv("STUDY_API_URL", "http://127.0.0.1:8080"),
        "https://study.cybercirujas.club",
    ]
    candidates = [query.strip()]
    tokens = [w for w in re.sub(r"([A-Z]+)", r" \1", query).strip().lower().split() if len(w) > 3]
    for t in tokens:
        if t not in candidates:
            candidates.append(t)

    for term in candidates:
        for base in base_urls:
            try:
                resp = requests.get(
                    f"{base}/api/search",
                    params={"q": term, "limit": limit},
                    headers={"User-Agent": "rag-tutor-api/1.2"},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    hits = resp.json().get("hits", [])
                    if hits:
                        return hits
            except Exception:
                continue
    return []


def _fetch_study_topic(cert: str, topic_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """Obtiene el contenido detallado de un objetivo de examen en study-cybercirujas."""
    base_urls = [
        os.getenv("STUDY_API_URL", "http://127.0.0.1:8080"),
        "https://study.cybercirujas.club",
    ]
    for base in base_urls:
        try:
            resp = requests.get(
                f"{base}/api/certs/{cert}/topics/{topic_id}",
                params={"lang": lang},
                headers={"User-Agent": "rag-tutor-api/1.2"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            continue
    return None


def _check_study_health() -> Dict[str, Any]:
    """Verifica si study-cybercirujas está activo y responde."""
    base_urls = [
        ("local", os.getenv("STUDY_API_URL", "http://127.0.0.1:8080")),
        ("remote_mirror", "https://study.cybercirujas.club"),
    ]
    for mode, base in base_urls:
        try:
            resp = requests.get(
                f"{base}/api/catalog",
                headers={"User-Agent": "rag-tutor-api/1.2"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                catalog = resp.json()
                return {
                    "status": "online",
                    "mode": mode,
                    "url": base,
                    "total_certifications": len(catalog),
                    "tools": ["list_certs", "get_syllabus", "get_topic", "search_topics"],
                }
        except Exception:
            continue
    return {
        "status": "offline",
        "mode": "unreachable",
        "error": "Ni el servidor local (:8080) ni el mirror remoto están disponibles.",
        "tools": ["list_certs", "get_syllabus", "get_topic", "search_topics"],
    }


# ----------------------------------------------------------------------
# Endpoints de la API
# ----------------------------------------------------------------------

@app.get("/health", tags=["Sistema"])
def health_check() -> Dict[str, Any]:
    """Estado de salud del servicio local y sus índices."""
    return {
        "status": "online",
        "service": "rag-tutor",
        "retriever_type": config.RETRIEVER_TYPE,
        "ollama_model": config.OLLAMA_MODEL,
        "embedding_model": config.EMBEDDING_MODEL_NAME,
        "reranker_model": config.RERANKER_MODEL_NAME,
        "chroma_dir_exists": config.CHROMA_DIR.exists(),
        "bm25_index_exists": config.BM25_INDEX_PATH.exists(),
        "knowledge_graph_exists": config.GRAPH_DATA_PATH.exists(),
    }


@app.get("/mcp/status", tags=["Tri-MCP Gateway"])
def mcp_status() -> Dict[str, Any]:
    """Inspecciona y monitorea el estado de conexión de los 3 servidores MCP."""
    # 1. Study Cybercirujas
    study_info = _check_study_health()

    # 2. k8s-docs-mcp
    if K8S_DOCS_AVAILABLE and k8s_store:
        try:
            with k8s_store._get_connection() as conn:
                c = conn.cursor()
                docs_count = c.execute("SELECT COUNT(*) FROM docs_fts").fetchone()[0]
                manifests_count = c.execute("SELECT COUNT(*) FROM manifests").fetchone()[0]
            k8s_info = {
                "status": "online",
                "store_populated": k8s_store.is_populated(),
                "total_doc_sections": docs_count,
                "total_manifests": manifests_count,
                "tools": ["search_k8s_docs", "get_canonical_manifest", "check_api_version"],
            }
        except Exception as e:
            k8s_info = {
                "status": "degraded",
                "error": str(e),
                "tools": ["search_k8s_docs", "get_canonical_manifest", "check_api_version"],
            }
    else:
        k8s_info = {
            "status": "offline",
            "error": "Módulo k8s-docs-mcp no encontrado en el PATH relativo.",
            "tools": ["search_k8s_docs", "get_canonical_manifest", "check_api_version"],
        }

    # 3. RAG Tutor (Local Literature)
    rag_info = {
        "status": "online",
        "retriever_engine": config.RETRIEVER_TYPE,
        "vector_db": "ChromaDB" if config.CHROMA_DIR.exists() else "None",
        "lexical_index": "BM25" if config.BM25_INDEX_PATH.exists() else "None",
        "graph_rag": "KùzuDB Cypher" if config.GRAPH_DATA_PATH.exists() else "None",
        "tools": ["search_books", "kuzu_graph_traversal", "agentic_reasoning"],
    }

    all_ready = (study_info["status"] == "online") and (k8s_info["status"] == "online")
    return {
        "tri_mcp_operational": all_ready,
        "active_architecture": "The Cloud Native Trifecta (Study + K8s-Docs + RAG-Tutor)",
        "servers": {
            "study_cybercirujas": study_info,
            "k8s_docs_mcp": k8s_info,
            "rag_tutor": rag_info,
        },
    }


@app.post("/mcp/test", tags=["Tri-MCP Gateway"])
def mcp_test(payload: McpTestRequest) -> Dict[str, Any]:
    """Ejecuta una prueba de diagnóstico en vivo sobre los servidores MCP."""
    results: Dict[str, Any] = {}

    # Probar study-cybercirujas
    if payload.target in ("study", "all"):
        hits = _fetch_study_search(payload.query, limit=2)
        if hits:
            top = hits[0]
            topic_detail = _fetch_study_topic(top["cert"], top["id"])
            results["study_cybercirujas"] = {
                "status": "SUCCESS",
                "test_query": payload.query,
                "matched_objective": f"{top['cert'].upper()} {top['id']} - {top['title']}",
                "certification": top.get("cert_name", top["cert"]),
                "weight": top.get("weight"),
                "has_lab": "break_fix.sh" in (topic_detail.get("content", "") if topic_detail else ""),
            }
        else:
            results["study_cybercirujas"] = {
                "status": "NO_HITS",
                "message": f"No se encontraron objetivos para '{payload.query}'",
            }

    # Probar k8s-docs-mcp
    if payload.target in ("k8s-docs", "all"):
        if K8S_DOCS_AVAILABLE:
            try:
                # Intentar API check y búsqueda de manifest
                api_check = k8s_check_api(payload.query)
                manifest = k8s_get_manifest(payload.query)
                results["k8s_docs_mcp"] = {
                    "status": "SUCCESS",
                    "test_target": payload.query,
                    "api_version_check": api_check.split("\n")[0:3],
                    "manifest_found": "Canonical Kubernetes Manifest" in manifest,
                    "manifest_preview": manifest.split("\n")[0:6],
                }
            except Exception as e:
                results["k8s_docs_mcp"] = {"status": "ERROR", "error": str(e)}
        else:
            results["k8s_docs_mcp"] = {"status": "UNAVAILABLE", "error": "k8s_docs_mcp import failed"}

    return {
        "target": payload.target,
        "query": payload.query,
        "diagnostic_results": results,
    }


@app.post("/chat", response_model=QueryResponse, tags=["Chat & Orquestación"])
def chat_endpoint(payload: QueryRequest):
    """Endpoint principal de consulta.
    
    Si `orchestrate_tri_mcp` es True, consulta automáticamente:
    1. `study-cybercirujas` para obtener el contexto del syllabus y labs.
    2. `k8s-docs-mcp` para validar la versión de la API y extraer YAMLs oficiales.
    3. `rag-tutor` para sintetizar con los libros de arquitectura y el grafo KùzuDB.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    extra_chunks: List[RetrievedChunk] = []
    enrichment_metadata: Dict[str, Any] = {
        "study_objective": None,
        "k8s_api_check": None,
        "k8s_manifest_injected": False,
    }

    if payload.orchestrate_tri_mcp:
        # 1. Enriquecer con study-cybercirujas
        try:
            hits = _fetch_study_search(payload.question, limit=1)
            if hits:
                top = hits[0]
                topic_data = _fetch_study_topic(top["cert"], top["id"])
                content = topic_data.get("content", "") if topic_data else ""
                if content:
                    enrichment_metadata["study_objective"] = f"{top['cert'].upper()} {top['id']} - {top['title']}"
                    extra_chunks.append(
                        RetrievedChunk(
                            content=content[:3000],
                            source=f"study-cybercirujas MCP: {top['cert'].upper()} Topic {top['id']} ({top['title']})",
                            page=None,
                            score=10.0,
                            metadata={"type": "official_syllabus", "cert": top["cert"]},
                        )
                    )
        except Exception as e:
            enrichment_metadata["study_error"] = str(e)

        # 2. Enriquecer con k8s-docs-mcp si aplica
        if K8S_DOCS_AVAILABLE:
            try:
                # Detectar posibles Kinds de k8s en la pregunta
                potential_kinds = [
                    "ValidatingAdmissionPolicy", "NetworkPolicy", "Ingress",
                    "StatefulSet", "Deployment", "Pod", "Service", "ConfigMap",
                    "MutatingWebhookConfiguration", "ValidatingWebhookConfiguration"
                ]
                matched_kind = None
                for k in potential_kinds:
                    if k.lower() in payload.question.lower():
                        matched_kind = k
                        break

                if matched_kind:
                    api_check = k8s_check_api(matched_kind)
                    manifest = k8s_get_manifest(matched_kind)
                    enrichment_metadata["k8s_api_check"] = api_check.split("\n")[1] if "\n" in api_check else api_check
                    enrichment_metadata["k8s_manifest_injected"] = True

                    extra_chunks.append(
                        RetrievedChunk(
                            content=f"{api_check}\n\n{manifest}",
                            source=f"k8s-docs-mcp MCP: kubernetes.io ({matched_kind} Canonical Spec)",
                            page=None,
                            score=9.5,
                            metadata={"type": "canonical_spec", "kind": matched_kind},
                        )
                    )
            except Exception as e:
                enrichment_metadata["k8s_docs_error"] = str(e)

    # Ejecutar loop agéntico de RAG Tutor con los chunks combinados
    result = tutor.ask(payload.question, extra_chunks=extra_chunks if extra_chunks else None)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        iterations=result["iterations"],
        retrieved_chunks=result["retrieved_chunks"],
        retriever_engine=result["retriever_engine"],
        llm_model=result["llm_model"],
        embedding_model=result["embedding_model"],
        reranker_model=result["reranker_model"],
        mcp_enrichment=enrichment_metadata,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
