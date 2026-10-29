"""
title: Cloud Native Tri-MCP Tutor
author: Cybercirujas
author_url: https://github.com/villadalmine/rag-tutor
git_url: https://github.com/villadalmine/rag-tutor
description: Queries the Sovereign Tri-MCP Stack (technical engineering books, official CNCF/LPI syllabi, and canonical Kubernetes YAMLs)
version: 1.3.0
license: Apache-2.0
"""

import json
import requests
from typing import Optional, Dict, Any


class Tools:
    def __init__(self):
        # Internal URL reachable from the Open WebUI Docker container
        self.gateway_url = "http://host.docker.internal:8000"

    def query_tri_mcp_tutor(
        self,
        question: str,
        domain: Optional[str] = None,
        min_year: Optional[int] = None,
    ) -> str:
        """
        MANDATORY TOOL: Queries the Sovereign Trifecta (study-cybercirujas + k8s-docs-mcp + rag-tutor).
        Always invoke this tool whenever the user asks about Kubernetes, Pods, Deployments,
        services, platform architecture, AI agents, CNCF syllabi (CKA, CKAD, CKS, CNPE), or YAML syntax.
        :param question: Exact technical question to resolve.
        :param domain: Optional domain filter (e.g. 'cloud_native', 'ai_agents', 'mlops').
        :param min_year: Optional minimum publication year (e.g. 2024 or 2025).
        :return: Grounded technical synthesis with verification badge and cited sources.
        """
        url = f"{self.gateway_url}/chat"
        payload = {
            "question": question,
            "orchestrate_tri_mcp": True,
            "domain": domain,
            "min_year": min_year,
        }
        try:
            resp = requests.post(url, json=payload, timeout=90.0)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                enrichment = data.get("mcp_enrichment", {})

                # Build Visual Tri-MCP Verification Badge
                badge_lines = [
                    "┌──────────────────────────────────────────────────────────────┐",
                    "│ 🛡️  SOVEREIGN MULTI-MCP VERIFICATION (LIVE TELEMETRY)        │",
                    "├──────────────────────────────────────────────────────────────┤",
                ]

                obj = enrichment.get("study_objective") or "General Platform Context"
                badge_lines.append(f"│ 🎯 Study-Cybercirujas: {obj[:46]:<46} │")

                kind = enrichment.get("k8s_kind") or "Core Resource"
                api_chk = enrichment.get("k8s_api_check") or "kubernetes.io canonical spec"
                badge_lines.append(f"│ 🛡️ K8s-Docs-MCP:      {kind} ({api_chk[:30]:<30}) │")

                retriever = data.get("retriever_engine", "omnigraph")
                llm = data.get("llm_model", "local-ollama")
                badge_lines.append(f"│ 📚 RAG-Tutor Engine:  {retriever} ({llm})                     │")
                badge_lines.append("└──────────────────────────────────────────────────────────────┘")

                badge_block = "```text\n" + "\n".join(badge_lines) + "\n```"

                sources_block = ""
                if sources:
                    sources_list = "\n".join([f"- `{s}`" for s in sources])
                    sources_block = f"\n\n### 📖 Consulted Sources:\n{sources_list}"

                return f"{badge_block}\n\n{answer}{sources_block}"
            return f"Error {resp.status_code} querying tutor: {resp.text}"
        except Exception as e:
            return f"Error connecting to RAG Tutor Gateway ({self.gateway_url}): {str(e)}"

    def check_mcp_cluster_status(self) -> str:
        """
        Checks the live connection status of all 3 MCP servers (study-cybercirujas, k8s-docs-mcp, rag-tutor).
        :return: Plain-text status summary of each MCP server.
        """
        url = f"{self.gateway_url}/mcp/status"
        try:
            resp = requests.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                servers = data.get("servers", {})
                status_summary = [
                    f"### Tri-MCP Cluster Status (Operational: {data.get('tri_mcp_operational')})\n"
                ]
                for name, s in servers.items():
                    mode_info = f" (Mode: {s.get('mode')})" if "mode" in s else ""
                    tools_list = ", ".join(s.get("tools", []))
                    status_summary.append(f"- **{name}**: `{s.get('status')}`{mode_info} | Tools: [{tools_list}]")
                return "\n".join(status_summary)
            return f"Error {resp.status_code} querying status: {resp.text}"
        except Exception as e:
            return f"Error connecting to RAG Tutor Gateway: {str(e)}"

    def test_mcp_integration(self, query: str = "pod") -> str:
        """
        Runs a live diagnostic test across all three MCP servers for any technical query or Kubernetes Kind.
        :param query: Test term (e.g., 'pod', 'network policy', 'admission webhooks').
        :return: Technical validation report with matched exam objectives and verified manifests.
        """
        url = f"{self.gateway_url}/mcp/test"
        try:
            resp = requests.post(url, json={"target": "all", "query": query}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json().get("diagnostic_results", {})
                study = data.get("study_cybercirujas", {})
                k8s = data.get("k8s_docs_mcp", {})
                rag = data.get("rag_tutor", {})

                report = [
                    f"### 🧪 Multi-MCP Diagnostic Report for: `{query}`\n",
                    f"- **study-cybercirujas:** {study.get('status')} | Objective: `{study.get('matched_objective')}` ({study.get('certification')})",
                    f"- **k8s-docs-mcp:** {k8s.get('status')} | Kind: `{k8s.get('detected_kind')}` | Verified manifests: {k8s.get('manifests_count')}",
                    f"- **rag-tutor:** {rag.get('status')} | Engine: `{rag.get('retriever_type')}` | Model: `{rag.get('ollama_model')}`",
                ]
                return "\n".join(report)
            return f"Error {resp.status_code} running MCP diagnostic test: {resp.text}"
        except Exception as e:
            return f"Error connecting to RAG Tutor Gateway: {str(e)}"
