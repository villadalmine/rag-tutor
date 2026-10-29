"""Deterministic book classification and chunk-level syntax detection engine.

Implements the Universal Metadata Engine described in METADATA_SYSTEM.md:
1. Macro Level (Document): Deterministic lexical profiling (title, TOC, and chapters)
   assigning `domain`, `secondary_domains`, `tags`, `publication_year`, and `sections`,
   persisted to `metadata_registry.json`.
2. Micro Level (Chunk): Regex-based code block and heading detection
   (`has_code`, `code_lang`, `is_heading`, `section_title`).
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src import config

REGISTRY_PATH = config.BASE_DIR / "metadata_registry.json"

DOMAIN_VOCABULARY: Dict[str, List[str]] = {
    "cloud_native": [
        "kubernetes", "k8s", "pod", "deployment", "kubectl", "helm", "ingress",
        "container", "docker", "crd", "operator", "etcd", "kubelet", "cni", "envoy",
        "istio", "cilium", "ebpf", "hubble", "network policy", "service mesh",
        "cloud-native", "cloud native", "microservice",
    ],
    "platform_engineering": [
        "platform engineering", "internal developer platform", "idp", "golden path",
        "paved road", "self-service", "backstage", "crossplane", "gitops", "argocd",
        "flux", "developer experience", "devex", "cognitive load",
    ],
    "ai_agents": [
        "agent", "agentic", "multi-agent", "react", "langgraph", "langchain", "autogen",
        "crewai", "tool calling", "function calling", "mcp", "model context protocol",
        "prompt engineering", "reasoning", "autonomous", "knowledge graph", "graphrag",
        "agent memory", "agent skills", "sandbox", "sandboxing",
    ],
    "mlops": [
        "mlops", "llm", "large language model", "generative ai", "genai", "fine-tuning",
        "lora", "qlora", "rag", "retrieval-augmented", "embedding", "vector database",
        "inference", "vllm", "ollama", "pytorch", "transformer", "huggingface",
        "kubeflow", "ray", "model serving", "gpu",
    ],
    "databases_and_storage": [
        "sql", "postgresql", "postgres", "mysql", "redis", "mongodb", "acid",
        "transaction", "wal", "btree", "b-tree", "indexing", "replication",
        "sharding", "partitioning", "query planner", "storage engine",
    ],
    "web_and_frontend": [
        "react", "typescript", "javascript", "dom", "html", "css", "next.js",
        "vue", "angular", "frontend", "browser", "component", "usenavigate",
        "useeffect", "usestate", "tailwind", "webpack", "vite",
    ],
    "systems_programming": [
        "rust", "ownership", "borrowing", "lifetime", "cargo", "unsafe",
        "kernel", "syscall", "linux kernel", "ebpf", "c++", "mutex", "thread",
        "concurrency", "memory allocation", "pointer", "assembly",
    ],
    "devsecops_and_security": [
        "security", "vulnerability", "exploit", "owasp", "pentesting", "zero trust",
        "rbac", "tls", "mtls", "cryptography", "jwt", "oauth", "oidc", "cve",
        "supply chain", "sbom", "falco", "kyverno", "opa", "gatekeeper",
    ],
    "distributed_systems": [
        "consensus", "raft", "paxos", "kafka", "event-driven", "event streaming",
        "cap theorem", "eventual consistency", "distributed", "rpc", "grpc",
        "idempotency", "circuit breaker", "saga",
    ],
}

CODE_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+-]+)")

LANGUAGE_ALIASES: Dict[str, str] = {
    "yml": "yaml",
    "yaml": "yaml",
    "golang": "go",
    "go": "go",
    "py": "python",
    "python": "python",
    "python3": "python",
    "sh": "bash",
    "bash": "bash",
    "shell": "bash",
    "zsh": "bash",
    "console": "bash",
    "sql": "sql",
    "postgresql": "sql",
    "psql": "sql",
    "ts": "typescript",
    "tsx": "typescript",
    "typescript": "typescript",
    "js": "typescript",
    "jsx": "typescript",
    "javascript": "typescript",
    "rs": "rust",
    "rust": "rust",
    "hcl": "terraform",
    "terraform": "terraform",
    "tf": "terraform",
    "json": "json",
    "jsonl": "json",
}

SYNTAX_SIGNATURES: List[Tuple[str, re.Pattern]] = [
    ("yaml", re.compile(r"(?:^|\n)\s*(?:apiVersion|kind|metadata|spec):\s+\S+", re.MULTILINE)),
    ("go", re.compile(r"(?:^|\n)\s*(?:package\s+\w+|func\s+(?:\([^)]+\)\s*)?\w+\(|type\s+\w+\s+struct\s*\{)", re.MULTILINE)),
    ("rust", re.compile(r"(?:^|\n)\s*(?:fn\s+\w+|impl(?:<[^>]+>)?\s+\w+|pub\s+struct\s+\w+|let\s+mut\s+\w+)", re.MULTILINE)),
    ("python", re.compile(r"(?:^|\n)\s*(?:def\s+\w+\s*\(|class\s+\w+(?:\([^)]*\))?:|from\s+[\w.]+\s+import\s+)", re.MULTILINE)),
    ("sql", re.compile(r"\b(?:SELECT\s+.+\s+FROM|CREATE\s+TABLE|ALTER\s+TABLE|EXPLAIN\s+ANALYZE)\b", re.IGNORECASE | re.DOTALL)),
    ("terraform", re.compile(r'(?:^|\n)\s*(?:resource|variable|provider|module)\s+"[^"]+"', re.MULTILINE)),
    ("typescript", re.compile(r"(?:^|\n)\s*(?:interface\s+\w+\s*\{|export\s+(?:default\s+)?(?:function|const|class)\s+|const\s+\[\w+,\s*set\w+\]\s*=\s*useState)", re.MULTILINE)),
    ("bash", re.compile(r"(?:^|\n)\s*(?:\$\s+)?(?:kubectl|docker|helm|git|curl|chmod|sudo|apt-get|systemctl)\s+\S+", re.MULTILINE)),
    ("json", re.compile(r'\{\s*"[^"]+"\s*:\s*(?:"[^"]*"|\d+|true|false|\[|\{)', re.MULTILINE)),
]

HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

COPYRIGHT_YEAR_PATTERNS = [
    re.compile(r"\*\*Publication Date:\*\*\s*(20\d{2}|19\d{2})", re.IGNORECASE),
    re.compile(r"(20\d{2}|19\d{2})-\d{2}-\d{2}:\s*(?:First|Second|Third|Fourth|Fifth)\s+Release", re.IGNORECASE),
    re.compile(r"(?:Copyright\s*)?(?:©|\(c\))\s*(?:19\d{2}\s*[-–]\s*)?(20\d{2}|19\d{2})", re.IGNORECASE),
    re.compile(r"Copyright\s+(?:19\d{2}\s*[-–]\s*)?(20\d{2}|19\d{2})", re.IGNORECASE),
    re.compile(r"(?:First|Second|Third|Fourth|Fifth)\s+(?:Edition|Release).*?(20\d{2}|19\d{2})", re.IGNORECASE),
    re.compile(r"(?:Published|Publication|Release)\s*(?:Date|Year)?[:\s]+(?:[A-Za-z]+\s+)?(20\d{2}|19\d{2})", re.IGNORECASE),
]


def extract_publication_year(source_name: str, sample_text: str) -> Optional[int]:
    """Deterministically extracts the book publication year (1990-2026)."""
    # 1. Check filename for an explicit 4-digit year
    m_name = re.search(r"\b(199\d|20[0-2]\d)\b", source_name)
    if m_name:
        return min(int(m_name.group(1)), 2026)

    # 2. Prioritize explicit Copyright / Early Release / Publication Date patterns
    for pat in COPYRIGHT_YEAR_PATTERNS[:5]:
        matches = [min(int(m.group(1)), 2026) for m in pat.finditer(sample_text) if 1990 <= int(m.group(1)) <= 2030]
        if matches:
            return max(matches)

    # 3. Fallback to general release/publication date mentions
    candidates: List[int] = []
    for pat in COPYRIGHT_YEAR_PATTERNS[5:]:
        for m in pat.finditer(sample_text):
            year = int(m.group(1))
            if 1990 <= year <= 2030:
                candidates.append(min(year, 2026))

    if candidates:
        return max(candidates)
    return None


def extract_sections_index(docs: List[Any], max_sections: int = 40) -> List[Dict[str, str]]:
    """Extracts a compact chapter and section (H1/H2/H3) tree for zero-token-burn MCP navigation."""
    sections: List[Dict[str, str]] = []
    seen = set()

    for idx, d in enumerate(docs, 1):
        meta = getattr(d, "metadata", {}) or {}
        content = getattr(d, "page_content", "") or ""
        chapter = meta.get("chapter") or meta.get("section_title") or ""
        page = meta.get("page")

        headings = [m.group(1).strip() for m in re.finditer(r"^#{1,2}\s+(.+)$", content, re.MULTILINE)]
        title = (headings[0] if headings else "") or chapter or f"Section {idx}"
        title_clean = re.sub(r"\s+", " ", title).strip()[:100]

        if not title_clean or title_clean.lower() in seen:
            continue
        seen.add(title_clean.lower())

        subheadings = [
            re.sub(r"\s+", " ", m.group(1)).strip()[:80]
            for m in re.finditer(r"^#{2,3}\s+(.+)$", content, re.MULTILINE)
        ]
        subheadings = [s for s in subheadings if s.lower() != title_clean.lower()][:6]

        entry: Dict[str, Any] = {"section": title_clean}
        if page:
            entry["page"] = page
        if subheadings:
            entry["topics"] = subheadings
        sections.append(entry)
        if len(sections) >= max_sections:
            break

    return sections


def load_metadata_registry() -> Dict[str, Any]:
    """Loads or initializes metadata_registry.json."""
    default_registry = {
        "domains": list(DOMAIN_VOCABULARY.keys()) + ["general_technical"],
        "catalog": {},
    }
    if not REGISTRY_PATH.exists():
        return default_registry
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "catalog" not in data:
                data["catalog"] = {}
            if "domains" not in data:
                data["domains"] = default_registry["domains"]
            return data
    except Exception:
        return default_registry


def save_metadata_registry(registry: Dict[str, Any]) -> None:
    """Persists metadata_registry.json with human-readable formatting."""
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def profile_document(
    source_name: str,
    sample_text: Any,
    total_units: int = 1,
    registry: Optional[Dict[str, Any]] = None,
    docs: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Deterministically profiles a book (domain, secondary_domains, tags, publication_year, and sections).

    If the user manually edited `metadata_registry.json` and set `"auto_generated": false`,
    manual overrides for `domain`, `tags`, and `publication_year` are strictly preserved.
    """
    if registry is None:
        registry = load_metadata_registry()

    if isinstance(sample_text, list):
        if docs is None:
            from types import SimpleNamespace
            docs = [SimpleNamespace(page_content=t, metadata={"page": i + 1}) for i, t in enumerate(sample_text)]
        # Sample the first 3000 characters of each chapter to cover the entire book
        sample_text_str = "\n\n".join(str(t)[:3000] for t in sample_text)
    elif docs:
        sample_text_str = str(sample_text) + "\n\n" + "\n\n".join(getattr(d, "page_content", "")[:2500] for d in docs[:35])
    else:
        sample_text_str = str(sample_text)

    catalog = registry.setdefault("catalog", {})
    existing = catalog.get(source_name)
    if existing and not existing.get("auto_generated", True):
        if docs and not existing.get("sections"):
            existing["sections"] = extract_sections_index(docs)
        return existing

    title_norm = source_name.lower().replace("-", " ").replace("_", " ")
    cleaned_sample = re.sub(r"\.(?:html|xhtml|xml|svg|png|jpg)\b", " ", sample_text_str[:80000].lower())
    text_lower = f"{title_norm}\n{cleaned_sample}"
    domain_scores: Counter = Counter()
    all_matched_keywords: Counter = Counter()

    for domain, keywords in DOMAIN_VOCABULARY.items():
        for kw in keywords:
            # Plural-tolerant regex (agent/agents, llm/llms, pod/pods, container/containers)
            pat = r"\b" + re.escape(kw) + r"s?\b"
            count = len(re.findall(pat, text_lower))
            if count > 0:
                in_title = re.search(pat, title_norm) is not None
                weight = 12 if in_title else 1
                domain_scores[domain] += count * weight
                all_matched_keywords[kw.replace(" ", "_")] += count * (6 if in_title else 1)

    if domain_scores:
        ranked_domains = domain_scores.most_common()
        best_domain, best_score = ranked_domains[0]
        secondary_domains = [
            dom for dom, sc in ranked_domains[1:3] if sc >= max(5, best_score * 0.20)
        ]
    else:
        best_domain, best_score = "general_technical", 0
        secondary_domains = []

    if best_score < 2:
        best_domain = "general_technical"
        words = re.findall(r"\b[a-z][a-z0-9_-]{3,20}\b", text_lower)
        stop = {"chapter", "book", "page", "table", "figure", "section", "introduction", "part", "using", "with", "from", "that", "this"}
        top_words = [w for w, _ in Counter(w for w in words if w not in stop).most_common(6)]
        tags = top_words or ["technical"]
    else:
        tags = [kw for kw, _ in all_matched_keywords.most_common(7)]
        for dom_tag in [best_domain] + secondary_domains:
            if dom_tag not in tags:
                tags.append(dom_tag)

    pub_year = extract_publication_year(source_name, sample_text_str)
    sections = extract_sections_index(docs) if docs else []

    entry = {
        "domain": best_domain,
        "secondary_domains": secondary_domains,
        "publication_year": pub_year,
        "tags": tags,
        "auto_generated": True,
        "pages": total_units,
        "sections": sections,
    }
    catalog[source_name] = entry
    return entry


def update_book_metadata(
    book_name: str,
    domain: Optional[str] = None,
    tags: Optional[List[str]] = None,
    publication_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Allows the user to manually override a book's domain, tags, or publication year.

    Sets `auto_generated = False` in `metadata_registry.json` so subsequent runs of
    `python src/ingest.py` strictly respect the user's customization.
    """
    registry = load_metadata_registry()
    catalog = registry.setdefault("catalog", {})

    # Allow exact match or unique substring match
    target_key = book_name
    if target_key not in catalog:
        matches = [k for k in catalog.keys() if book_name.lower() in k.lower()]
        if len(matches) == 1:
            target_key = matches[0]

    entry = catalog.get(
        target_key,
        {
            "domain": "general_technical",
            "secondary_domains": [],
            "publication_year": None,
            "tags": [],
            "auto_generated": False,
            "pages": 0,
            "sections": [],
        },
    )
    if domain:
        entry["domain"] = domain.strip()
        if domain.strip() not in registry.get("domains", []):
            registry.setdefault("domains", []).append(domain.strip())
    if tags is not None:
        entry["tags"] = [t.strip() for t in tags if t.strip()]
    if publication_year is not None:
        entry["publication_year"] = int(publication_year)

    entry["auto_generated"] = False
    catalog[target_key] = entry
    save_metadata_registry(registry)
    return {target_key: entry}


def detect_chunk_syntax(text: str) -> Dict[str, Any]:
    """Detects code blocks, dominant programming language, and Markdown headings in a chunk."""
    code_lang = "none"
    has_code = False

    # 1. Check Markdown code fences (```yaml, ```python, etc.)
    fence_matches = CODE_FENCE_RE.findall(text)
    for raw_lang in fence_matches:
        norm = LANGUAGE_ALIASES.get(raw_lang.lower().strip())
        if norm:
            code_lang = norm
            has_code = True
            break

    # 2. If no explicit fence language, evaluate syntax signatures
    if not has_code:
        for lang, pattern in SYNTAX_SIGNATURES:
            if pattern.search(text):
                code_lang = lang
                has_code = True
                break

    if not has_code and "```" in text:
        has_code = True

    # 3. Detect Markdown heading in chunk
    heading_match = HEADING_RE.search(text)
    is_heading = heading_match is not None
    section_title = heading_match.group(2).strip()[:120] if heading_match else ""

    return {
        "has_code": has_code,
        "code_lang": code_lang,
        "is_heading": is_heading,
        "section_title": section_title,
    }
