"""
title: Cloud Native Tri-MCP Tutor
author: Cybercirujas
author_url: https://github.com/villadalmine/rag-tutor
git_url: https://github.com/villadalmine/rag-tutor
description: Consulta la Trifecta soberana (libros técnicos Manning, temarios oficiales CNCF/LPI y YAMLs canónicos de Kubernetes)
version: 1.2.0
license: Apache-2.0
"""

import json
import requests
from typing import Optional, Dict, Any


class Tools:
    def __init__(self):
        # URL interna accesible desde el contenedor Docker de Open WebUI
        self.gateway_url = "http://host.docker.internal:8000"

    def query_tri_mcp_tutor(self, question: str) -> str:
        """
        HERRAMIENTA OBLIGATORIA: Consulta la Trifecta Soberana (study-cybercirujas + k8s-docs-mcp + rag-tutor).
        Debes invocar esta herramienta SIEMPRE que el usuario pregunte sobre Kubernetes, Pods, Deployments,
        servicios, arquitectura de plataformas, temarios CNCF (CKA, CKAD, CKS, CNPE) o sintaxis YAML.
        :param question: La consulta técnica exacta a resolver.
        :return: Síntesis técnica con tarjeta de verificación y fuentes oficiales citadas.
        """
        url = f"{self.gateway_url}/chat"
        payload = {
            "question": question,
            "orchestrate_tri_mcp": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=90.0)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                enrichment = data.get("mcp_enrichment", {})
                
                # Construir Tarjeta Visual de Verificación Tri-MCP
                badge_lines = [
                    "┌──────────────────────────────────────────────────────────────┐",
                    "│ 🛡️  VERIFICACIÓN MULTI-MCP SOBERANA (TELEMETRÍA EN VIVO)     │",
                    "├──────────────────────────────────────────────────────────────┤",
                ]
                
                obj = enrichment.get("study_objective") or "General Platform Context"
                badge_lines.append(f"│ 🎯 Study-Cybercirujas: {obj[:46]:<46} │")
                
                kind = enrichment.get("k8s_kind") or "Core Resource"
                api_chk = enrichment.get("k8s_api_check") or "kubernetes.io canonical spec"
                badge_lines.append(f"│ 🛡️ K8s-Docs-MCP:      {kind} ({api_chk[:30]:<30}) │")
                
                retriever = data.get("retriever_engine", "hybrid")
                llm = data.get("llm_model", "local-ollama")
                badge_lines.append(f"│ 📚 RAG-Tutor Engine:  {retriever} ({llm}) on AMD Radeon GPU  │")
                badge_lines.append("└──────────────────────────────────────────────────────────────┘")
                
                badge_block = "```text\n" + "\n".join(badge_lines) + "\n```"

                # Fuentes formateadas
                sources_block = ""
                if sources:
                    sources_list = "\n".join([f"- `{s}`" for s in sources])
                    sources_block = f"\n\n### 📖 Fuentes Oficiales Consultadas:\n{sources_list}"

                return f"{badge_block}\n\n{answer}{sources_block}"
            return f"Error {resp.status_code} al consultar el tutor: {resp.text}"
        except Exception as e:
            return f"Error al conectar con RAG Tutor Gateway ({self.gateway_url}): {str(e)}"

    def check_mcp_cluster_status(self) -> str:
        """
        Verifica el estado de conexión de los 3 servidores MCP (study-cybercirujas, k8s-docs-mcp, rag-tutor).
        :return: Resumen en texto del estado de cada servidor.
        """
        url = f"{self.gateway_url}/mcp/status"
        try:
            resp = requests.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                servers = data.get("servers", {})
                status_summary = [
                    f"### Estado de la Trifecta MCP (Operativo: {data.get('tri_mcp_operational')})\n"
                ]
                for name, s in servers.items():
                    mode_info = f" (Modo: {s.get('mode')})" if "mode" in s else ""
                    tools_list = ", ".join(s.get("tools", []))
                    status_summary.append(f"- **{name}**: `{s.get('status')}`{mode_info} | Tools: [{tools_list}]")
                return "\n".join(status_summary)
            return f"Error {resp.status_code} al consultar estado: {resp.text}"
        except Exception as e:
            return f"Error al conectar con RAG Tutor Gateway: {str(e)}"

    def test_mcp_integration(self, query: str = "pod") -> str:
        """
        Ejecuta una prueba diagnóstica en vivo sobre los tres MCP con cualquier consulta técnica o Kind.
        :param query: Término de prueba (ej: 'pod', 'network policy', 'admission webhooks').
        :return: Reporte de validación técnica con objetivos de examen y manifiestos encontrados.
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
                    f"### 🧪 Diagnóstico Multi-MCP para: `{query}`\n",
                    f"- **study-cybercirujas:** {study.get('status')} | Objetivo: `{study.get('matched_objective')}` ({study.get('certification')})",
                    f"- **k8s-docs-mcp:** {k8s.get('status')} | Kind: `{k8s.get('detected_kind')}` | Manifiestos verificados: {k8s.get('manifests_count')}",
                    f"- **rag-tutor:** {rag.get('status')} | Motor: `{rag.get('retriever_type')}` | Modelo: `{rag.get('ollama_model')}`"
                ]
                return "\n".join(report)
            return f"Error {resp.status_code} al ejecutar test MCP: {resp.text}"
        except Exception as e:
            return f"Error al conectar con RAG Tutor Gateway: {str(e)}"

