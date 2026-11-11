"""FastAPI REST API & Tri-MCP Gateway for the Universal Technical RAG Tutor.

Supports two operational modes:
1. Direct retrieval and synthesis over the local technical library (Hybrid RAG + KùzuDB GraphRAG + WHERE filters).
2. Tri-MCP Orchestration (/mcp/status, /mcp/test, and /chat with multi-server enrichment).
"""

import datetime
import json
import os
import re
import sys
import time
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

# Sibling oss-docs-mcp path (versioned docs of AI-infra projects: KServe, llm-d, SGLang, ...)
OSS_DOCS_SRC = ROOT_DIR.parent / "oss-docs-mcp" / "src"
if OSS_DOCS_SRC.exists() and str(OSS_DOCS_SRC) not in sys.path:
    sys.path.insert(0, str(OSS_DOCS_SRC))

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

AUDIT_LOGS: List[Dict[str, Any]] = []


def _record_audit_log(
    endpoint: str,
    query: str,
    details: Dict[str, Any],
    client_ip: str = "unknown",
    latency_ms: float = 0.0,
):
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "endpoint": endpoint,
        "query": query,
        "client_ip": client_ip,
        "latency_ms": round(latency_ms, 2),
        **details,
    }
    AUDIT_LOGS.insert(0, entry)
    if len(AUDIT_LOGS) > 100:
        AUDIT_LOGS.pop()


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

# Import oss-docs-mcp store if available (read-only; no MCP runtime needed in-process)
try:
    from oss_docs_mcp.store import Store as OssDocsStore

    oss_store = OssDocsStore()
    OSS_DOCS_AVAILABLE = oss_store.stats()["chunks"] > 0
except Exception:
    OSS_DOCS_AVAILABLE = False
    oss_store = None

app = FastAPI(
    title="Cloud Native Sovereign RAG & Tri-MCP Gateway API",
    description="REST API for interacting with the Agentic RAG Tutor (with SQL-like WHERE filters and LLM-free mode) and orchestrating the Tri-MCP stack (study-cybercirujas, k8s-docs-mcp, rag-tutor).",
    version="1.3.0",
)

tutor = AgenticTutorCore()


# ----------------------------------------------------------------------
# Pydantic Data Models
# ----------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(..., description="Technical question on architecture, certifications, AI agents, or Kubernetes.")
    orchestrate_tri_mcp: bool = Field(
        True,
        description="If True, automatically queries study-cybercirujas and k8s-docs-mcp to enrich the response with official syllabi and canonical YAMLs.",
    )
    domain: Optional[str] = Field(None, description="Optional domain filter (e.g., 'cloud_native', 'ai_agents', 'mlops').")
    code_lang: Optional[str] = Field(None, description="Optional code language filter (e.g., 'yaml', 'go', 'python', 'bash').")
    book: Optional[str] = Field(None, description="Optional book/source identifier substring filter.")
    min_year: Optional[int] = Field(None, description="Optional minimum publication year filter (e.g., 2024 or 2025).")
    tag: Optional[str] = Field(None, description="Optional topic tag filter (e.g., 'kubernetes', 'vllm', 'cilium').")
    section: Optional[str] = Field(None, description="Optional chapter/section title substring filter.")
    no_llm: bool = Field(False, description="If True, executes deterministic retrieval and reranking without calling Ollama.")
    oss_docs_project: Optional[str] = Field(
        None, description="Force oss-docs-mcp enrichment from this project id (e.g. 'kserve', 'llm-d'). "
                          "By default it is used only when the question names an indexed project.")
    oss_docs_version: Optional[str] = Field(None, description="Pin the oss-docs project version (e.g. '0.20'); default latest.")


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
    target: str = Field("all", description="Target MCP server to test: 'study', 'k8s-docs', 'oss-docs', 'rag', or 'all'")
    query: str = Field("admission controllers", description="Technical term or Kubernetes Kind for the verification test")


# ----------------------------------------------------------------------
# MCP Server Connection Helpers
# ----------------------------------------------------------------------

K8S_KIND_SYNONYMS: Dict[str, str] = {
    "pod": "Pod",
    "pods": "Pod",
    "deployment": "Deployment",
    "deployments": "Deployment",
    "deploy": "Deployment",
    "statefulset": "StatefulSet",
    "statefulsets": "StatefulSet",
    "sts": "StatefulSet",
    "daemonset": "DaemonSet",
    "daemonsets": "DaemonSet",
    "ds": "DaemonSet",
    "service": "Service",
    "services": "Service",
    "svc": "Service",
    "ingress": "Ingress",
    "ingresses": "Ingress",
    "ing": "Ingress",
    "configmap": "ConfigMap",
    "configmaps": "ConfigMap",
    "cm": "ConfigMap",
    "secret": "Secret",
    "secrets": "Secret",
    "job": "Job",
    "jobs": "Job",
    "cronjob": "CronJob",
    "cronjobs": "CronJob",
    "cj": "CronJob",
    "networkpolicy": "NetworkPolicy",
    "networkpolicies": "NetworkPolicy",
    "netpol": "NetworkPolicy",
    "validatingadmissionpolicy": "ValidatingAdmissionPolicy",
    "validatingadmissionpolicies": "ValidatingAdmissionPolicy",
    "validatingadmissionpolicybinding": "ValidatingAdmissionPolicyBinding",
    "validatingwebhookconfiguration": "ValidatingWebhookConfiguration",
    "mutatingwebhookconfiguration": "MutatingWebhookConfiguration",
    "horizontalpodautoscaler": "HorizontalPodAutoscaler",
    "hpa": "HorizontalPodAutoscaler",
    "persistentvolume": "PersistentVolume",
    "persistentvolumes": "PersistentVolume",
    "pv": "PersistentVolume",
    "persistentvolumeclaim": "PersistentVolumeClaim",
    "persistentvolumeclaims": "PersistentVolumeClaim",
    "pvc": "PersistentVolumeClaim",
    "customresourcedefinition": "CustomResourceDefinition",
    "crd": "CustomResourceDefinition",
    "serviceaccount": "ServiceAccount",
    "sa": "ServiceAccount",
    "role": "Role",
    "roles": "Role",
    "clusterrole": "ClusterRole",
    "clusterroles": "ClusterRole",
    "rolebinding": "RoleBinding",
    "rolebindings": "RoleBinding",
    "clusterrolebinding": "ClusterRoleBinding",
    "clusterrolebindings": "ClusterRoleBinding",
    "namespace": "Namespace",
    "namespaces": "Namespace",
    "ns": "Namespace",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "how", "what", "which", "where", "who", "when", "why", "can",
    "could", "would", "should", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "i", "you", "we", "they", "it",
    "my", "your", "our", "their", "this", "that", "these", "those", "example",
    "examples", "three", "two", "one", "sample", "samples", "show", "give", "me",
    "tell", "explain", "create", "definition", "theory", "works", "work", "help",
    "understand",
}

K8S_PRIORITY_CERTS = {"cka", "ckad", "cks", "ckne", "kcsa", "cnpe"}


def _extract_k8s_kind(text: str) -> Optional[str]:
    """Deterministically detects the mentioned Kubernetes resource Kind (plural/acronym tolerant)."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    for token in cleaned.split():
        if token in K8S_KIND_SYNONYMS:
            return K8S_KIND_SYNONYMS[token]
    if "network policy" in cleaned or "network policies" in cleaned:
        return "NetworkPolicy"
    if "admission policy" in cleaned or "validating admission" in cleaned:
        return "ValidatingAdmissionPolicy"
    if "admission webhook" in cleaned or "validating webhook" in cleaned:
        return "ValidatingWebhookConfiguration"
    if "persistent volume claim" in cleaned:
        return "PersistentVolumeClaim"
    if "persistent volume" in cleaned:
        return "PersistentVolume"
    if "service account" in cleaned:
        return "ServiceAccount"
    if "config map" in cleaned:
        return "ConfigMap"
    return None


def _clean_search_tokens(query: str) -> List[str]:
    """Extracts substantive keywords while ignoring conversational stop words."""
    raw_tokens = re.sub(r"[^\w\s-]", " ", query.lower()).split()
    return [t for t in raw_tokens if t not in STOP_WORDS and len(t) >= 3]


def _fetch_study_search(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Queries the study-cybercirujas search API with entity extraction and stop-word filtering."""
    base_urls = [
        os.getenv("STUDY_API_URL", "http://127.0.0.1:8080"),
        "https://study.cybercirujas.club",
    ]
    detected_kind = _extract_k8s_kind(query)
    clean_tokens = _clean_search_tokens(query)

    candidates: List[str] = []
    if detected_kind:
        candidates.append(detected_kind.lower())
    if clean_tokens:
        candidates.append(" ".join(clean_tokens))
        for tok in clean_tokens:
            if tok not in candidates:
                candidates.append(tok)
    if not candidates:
        candidates.append(query.strip())

    is_k8s_context = detected_kind is not None or any(
        k in query.lower() for k in ("k8s", "kubernetes", "pod", "container", "cluster", "yaml")
    )

    for term in candidates:
        for base in base_urls:
            try:
                resp = requests.get(
                    f"{base}/api/search",
                    params={"q": term, "limit": 10},
                    headers={"User-Agent": "rag-tutor-api/1.3"},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    hits = resp.json().get("hits", [])
                    if hits:
                        if is_k8s_context:
                            hits = sorted(
                                hits,
                                key=lambda h: (h.get("cert") in K8S_PRIORITY_CERTS, h.get("score", 0)),
                                reverse=True,
                            )
                        return hits[:limit]
            except Exception:
                continue
    return []


def _fetch_study_topic(cert: str, topic_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """Fetches detailed exam objective content from study-cybercirujas."""
    base_urls = [
        os.getenv("STUDY_API_URL", "http://127.0.0.1:8080"),
        "https://study.cybercirujas.club",
    ]
    for base in base_urls:
        try:
            resp = requests.get(
                f"{base}/api/certs/{cert}/topics/{topic_id}",
                params={"lang": lang},
                headers={"User-Agent": "rag-tutor-api/1.3"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            continue
    return None


def _check_study_health() -> Dict[str, Any]:
    """Checks whether study-cybercirujas is reachable."""
    base_urls = [
        ("local", os.getenv("STUDY_API_URL", "http://127.0.0.1:8080")),
        ("remote_mirror", "https://study.cybercirujas.club"),
    ]
    for mode, base in base_urls:
        try:
            resp = requests.get(
                f"{base}/api/catalog",
                headers={"User-Agent": "rag-tutor-api/1.3"},
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
        "error": "Neither the local server (:8080) nor the remote mirror is reachable.",
        "tools": ["list_certs", "get_syllabus", "get_topic", "search_topics"],
    }


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Health status of the local service and its retrieval indices."""
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


def _oss_project_aliases() -> Dict[str, str]:
    """alias (lowercase) → project id, built from the oss-docs index (id, name, parenthesised aka)."""
    aliases: Dict[str, str] = {}
    if not (OSS_DOCS_AVAILABLE and oss_store):
        return aliases
    for row in oss_store.projects():
        pid, name = row["id"], (row["name"] or "")
        names = {pid, pid.replace("-", ""), pid.replace("-", " "), name.lower()}
        names |= {n.strip().lower().removeprefix("ex ").strip() for n in re.findall(r"\(([^)]+)\)", name)}
        names |= {re.sub(r"\s*\(.*\)", "", name).strip().lower()}
        for n in names:
            if len(n) >= 4:
                aliases[n] = pid
    return aliases


def _detect_oss_project(text: str) -> Optional[str]:
    lowered = f" {re.sub(r'[^a-z0-9 -]', ' ', text.lower())} "
    for alias, pid in sorted(_oss_project_aliases().items(), key=lambda kv: -len(kv[0])):
        if f" {alias} " in lowered:
            return pid
    return None


def _oss_docs_enrich(question: str, project: Optional[str], version: Optional[str], limit: int = 2):
    """Top oss-docs sections for the question, as RetrievedChunks with version-pinned citations."""
    project = project or _detect_oss_project(question)
    if not (OSS_DOCS_AVAILABLE and oss_store and project):
        return [], {"oss_docs_project": None}
    terms = " ".join(_clean_search_tokens(question)) or question
    hits = oss_store.search(terms, project=project, version=version, limit=limit, require_all=True) \
        or oss_store.search(terms, project=project, version=version, limit=limit)
    rows = oss_store.chunks_by_id([h.chunk_id for h in hits])
    chunks = [
        RetrievedChunk(
            content=f"# {r['heading']}\n\n{r['content'][:2500]}",
            source=f"oss-docs-mcp: {r['project']}@{r['version']} — {r['heading']} "
                   f"({r['url']}{'#' + r['anchor'] if r['anchor'] else ''})",
            page=None,
            score=9.5,
            metadata={"type": "official_project_docs", "project": r["project"], "version": r["version"],
                      "url": r["url"], "commit": r["commit_sha"][:10]},
        )
        for r in rows
    ]
    meta = {"oss_docs_project": project,
            "oss_docs_version": rows[0]["version"] if rows else oss_store.resolve_version(project, version),
            "oss_docs_hits": [f"{r['project']}@{r['version']} · {r['heading']}" for r in rows]}
    return chunks, meta


@app.get("/mcp/status", tags=["Tri-MCP Gateway"])
def mcp_status() -> Dict[str, Any]:
    """Inspects and monitors the live connection status of all 3 MCP servers."""
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
            "error": "k8s-docs-mcp module not found in relative PATH.",
            "tools": ["search_k8s_docs", "get_canonical_manifest", "check_api_version"],
        }

    # 3. oss-docs-mcp (versioned AI-infra project docs)
    if OSS_DOCS_AVAILABLE and oss_store:
        try:
            oss_info = {
                "status": "online",
                **oss_store.stats(),
                "projects": {r["id"]: r["all_versions"] for r in oss_store.projects()},
                "tools": ["search_docs", "read_chunks", "get_page_outline", "list_versions", "whats_new"],
            }
        except Exception as e:
            oss_info = {"status": "degraded", "error": str(e)}
    else:
        oss_info = {"status": "offline", "error": "oss-docs-mcp not found next to rag-tutor or index empty "
                                                  "(run `uv run oss-docs sync` or `oss-docs pull` there)."}

    # 4. RAG Tutor (Local Technical Library + KùzuDB GraphRAG)
    rag_info = {
        "status": "online",
        "retriever_engine": config.RETRIEVER_TYPE,
        "vector_db": "ChromaDB" if config.CHROMA_DIR.exists() else "None",
        "lexical_index": "BM25" if config.BM25_INDEX_PATH.exists() else "None",
        "graph_rag": "KùzuDB Cypher" if config.GRAPH_DATA_PATH.exists() else "None",
        "tools": [
            "listar_libros_y_secciones",
            "buscar_fragmentos_secciones",
            "consultar_grafo_kuzu",
            "consultar_libros_manning",
            "buscar_codigo_yaml",
        ],
    }

    all_ready = (study_info["status"] == "online") and (k8s_info["status"] == "online")
    return {
        "tri_mcp_operational": all_ready,
        "active_architecture": "The Cloud Native Trifecta (Study + K8s-Docs + RAG-Tutor)",
        "servers": {
            "study_cybercirujas": study_info,
            "k8s_docs_mcp": k8s_info,
            "oss_docs_mcp": oss_info,
            "rag_tutor": rag_info,
        },
    }


@app.get("/mcp/logs", tags=["Tri-MCP Gateway"])
def get_mcp_logs(limit: int = 30) -> Dict[str, Any]:
    """Live audit log of queries, invoked tools, and latency telemetry."""
    return {
        "total_recorded_events": len(AUDIT_LOGS),
        "recent_events": AUDIT_LOGS[:limit],
    }


@app.post("/mcp/test", tags=["Tri-MCP Gateway"])
def mcp_test(payload: McpTestRequest, request: Request) -> Dict[str, Any]:
    """Executes a live diagnostic test across the connected MCP servers."""
    t0 = time.time()
    client_ip = request.client.host if request.client else "unknown"
    results: Dict[str, Any] = {}
    detected_kind = _extract_k8s_kind(payload.query)
    clean_tokens = _clean_search_tokens(payload.query)

    # 1. Test study-cybercirujas
    if payload.target in ("study", "all"):
        hits = _fetch_study_search(payload.query, limit=2)
        if hits:
            top = hits[0]
            topic_detail = _fetch_study_topic(top["cert"], top["id"])
            has_lab = bool(
                topic_detail
                and (topic_detail.get("break_fix") or "break_fix.sh" in topic_detail.get("content", ""))
            )
            results["study_cybercirujas"] = {
                "status": "SUCCESS",
                "test_query": payload.query,
                "detected_kind": detected_kind,
                "matched_objective": f"{top['cert'].upper()} {top['id']} - {top['title']}",
                "certification": top.get("cert_name", top["cert"]),
                "domain": top.get("domain", ""),
                "weight": top.get("weight"),
                "has_lab": has_lab,
                "lab_status": topic_detail.get("lab_status") if topic_detail else None,
            }
        else:
            results["study_cybercirujas"] = {
                "status": "NO_HITS",
                "message": f"No exam objectives found for '{payload.query}'",
            }

    # 2. Test k8s-docs-mcp
    if payload.target in ("k8s-docs", "all"):
        if K8S_DOCS_AVAILABLE:
            try:
                if detected_kind:
                    api_check = k8s_check_api(detected_kind)
                    manifest = k8s_get_manifest(detected_kind, limit=3)
                    concept_docs = k8s_search_docs(f"{detected_kind} architecture overview", limit=2)
                    manifest_count = manifest.count("#### Manifest")
                    results["k8s_docs_mcp"] = {
                        "status": "SUCCESS",
                        "test_target": payload.query,
                        "detected_kind": detected_kind,
                        "api_version_check": [line for line in api_check.split("\n") if line.strip()][:3],
                        "manifest_found": "Canonical Kubernetes Manifest" in manifest,
                        "manifests_count": manifest_count,
                        "manifest_preview": [line for line in manifest.split("\n") if line.strip()][:12],
                        "concept_docs_snippet": [line for line in concept_docs.split("\n") if line.strip()][:4] if concept_docs else [],
                    }
                else:
                    search_term = " ".join(clean_tokens) if clean_tokens else payload.query
                    concept_docs = k8s_search_docs(search_term, limit=2)
                    results["k8s_docs_mcp"] = {
                        "status": "SUCCESS",
                        "test_target": payload.query,
                        "detected_kind": None,
                        "search_mode": "conceptual_documentation",
                        "doc_results": [line for line in concept_docs.split("\n") if line.strip()][:8],
                    }
            except Exception as e:
                results["k8s_docs_mcp"] = {"status": "ERROR", "error": str(e)}
        else:
            results["k8s_docs_mcp"] = {"status": "UNAVAILABLE", "error": "k8s_docs_mcp import failed"}

    # 3. Test oss-docs-mcp
    if payload.target in ("oss-docs", "all"):
        if OSS_DOCS_AVAILABLE and oss_store:
            project = _detect_oss_project(payload.query)
            terms = " ".join(clean_tokens) if clean_tokens else payload.query
            hits = oss_store.search(terms, project=project, limit=3)
            results["oss_docs_mcp"] = {
                "status": "SUCCESS" if hits else "NO_HITS",
                "detected_project": project,
                "hits": [f"[{h.chunk_id}] {h.project}@{h.version} · {h.heading} — {h.url}" for h in hits],
            }
        else:
            results["oss_docs_mcp"] = {"status": "UNAVAILABLE", "error": "oss_docs_mcp import failed or index empty"}

    # 4. Test rag-tutor
    if payload.target in ("rag", "all"):
        test_term = clean_tokens[0] if clean_tokens else payload.query
        retriever_ready = tutor.retriever is not None
        results["rag_tutor"] = {
            "status": "SUCCESS" if retriever_ready else "DEGRADED",
            "test_query": payload.query,
            "test_term": test_term,
            "retriever_type": config.RETRIEVER_TYPE,
            "ollama_model": config.OLLAMA_MODEL,
            "chroma_dir_exists": config.CHROMA_DIR.exists(),
            "knowledge_graph_exists": config.GRAPH_DATA_PATH.exists(),
            "pipeline_status": "Vector DB, BM25, Cross-Encoder & KùzuDB GraphRAG ready",
        }

    duration = (time.time() - t0) * 1000.0
    _record_audit_log(
        endpoint="/mcp/test",
        query=payload.query,
        details={
            "target": payload.target,
            "detected_kind": detected_kind,
            "study_matched": results.get("study_cybercirujas", {}).get("matched_objective"),
            "k8s_manifests": results.get("k8s_docs_mcp", {}).get("manifests_count", 0),
        },
        client_ip=client_ip,
        latency_ms=duration,
    )

    return {
        "target": payload.target,
        "query": payload.query,
        "diagnostic_results": results,
    }


@app.post("/chat", response_model=QueryResponse, tags=["Chat & Orchestration"])
def chat_endpoint(payload: QueryRequest, request: Request):
    """Primary query endpoint supporting SQL-like WHERE filters, LLM-free retrieval, and Tri-MCP orchestration."""
    t0 = time.time()
    client_ip = request.client.host if request.client else "unknown"

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    extra_chunks: List[RetrievedChunk] = []
    enrichment_metadata: Dict[str, Any] = {
        "study_objective": None,
        "k8s_kind": None,
        "k8s_api_check": None,
        "k8s_manifest_injected": False,
    }

    if payload.orchestrate_tri_mcp and not payload.no_llm:
        # 1. Enrich with study-cybercirujas
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

        # 2. Enrich with k8s-docs-mcp if applicable
        if K8S_DOCS_AVAILABLE:
            try:
                matched_kind = _extract_k8s_kind(payload.question)
                if matched_kind:
                    api_check = k8s_check_api(matched_kind)
                    manifest = k8s_get_manifest(matched_kind, limit=3)
                    concept_docs = k8s_search_docs(f"{matched_kind} overview architecture", limit=2)
                    enrichment_metadata["k8s_kind"] = matched_kind
                    enrichment_metadata["k8s_api_check"] = api_check.split("\n")[1] if "\n" in api_check else api_check
                    enrichment_metadata["k8s_manifest_injected"] = True

                    extra_chunks.append(
                        RetrievedChunk(
                            content=f"{api_check}\n\n{manifest}\n\n{concept_docs}",
                            source=f"k8s-docs-mcp MCP: kubernetes.io ({matched_kind} Canonical Spec & Docs)",
                            page=None,
                            score=9.8,
                            metadata={"type": "canonical_spec", "kind": matched_kind},
                        )
                    )
                else:
                    clean_terms = " ".join(_clean_search_tokens(payload.question))
                    if clean_terms:
                        concept_docs = k8s_search_docs(clean_terms, limit=2)
                        if "Official Kubernetes Documentation" in concept_docs and len(concept_docs) > 80:
                            extra_chunks.append(
                                RetrievedChunk(
                                    content=concept_docs[:2500],
                                    source="k8s-docs-mcp MCP: kubernetes.io (Conceptual Docs)",
                                    page=None,
                                    score=8.5,
                                    metadata={"type": "official_k8s_docs"},
                                )
                            )
            except Exception as e:
                enrichment_metadata["k8s_docs_error"] = str(e)

        # 3. Enrich with oss-docs-mcp when the question names an indexed project (or one is forced)
        try:
            oss_chunks, oss_meta = _oss_docs_enrich(payload.question, payload.oss_docs_project, payload.oss_docs_version)
            extra_chunks.extend(oss_chunks)
            enrichment_metadata.update(oss_meta)
        except Exception as e:
            enrichment_metadata["oss_docs_error"] = str(e)

    # Execute RAG Tutor retrieval / agentic loop with WHERE filters
    result = tutor.ask(
        payload.question,
        extra_chunks=extra_chunks if extra_chunks else None,
        domain=payload.domain,
        code_lang=payload.code_lang,
        book=payload.book,
        min_year=payload.min_year,
        tag=payload.tag,
        section=payload.section,
        no_llm=payload.no_llm,
    )
    duration = (time.time() - t0) * 1000.0

    _record_audit_log(
        endpoint="/chat",
        query=payload.question,
        details={
            "orchestrate_tri_mcp": payload.orchestrate_tri_mcp,
            "domain": payload.domain,
            "min_year": payload.min_year,
            "tag": payload.tag,
            "no_llm": payload.no_llm,
            "study_objective": enrichment_metadata.get("study_objective"),
            "k8s_kind": enrichment_metadata.get("k8s_kind"),
            "manifest_injected": enrichment_metadata.get("k8s_manifest_injected", False),
            "oss_docs_project": enrichment_metadata.get("oss_docs_project"),
            "sources_count": len(result.get("sources", [])),
            "retrieved_chunks": result.get("retrieved_chunks", 0),
        },
        client_ip=client_ip,
        latency_ms=duration,
    )

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
