# GLOSSARY.md Maintenance Rule

Whenever an agent or developer performs any of the following actions in this repository:
1. Adds, removes, or updates libraries in `requirements.txt` or `pyproject.toml`.
2. Introduces a new service, database, search engine, or communication protocol.
3. Modifies or adds a Large Language Model (LLM), embedding model, or Cross-Encoder reranker in `src/config.py` or Ollama.

**You MUST immediately update [`GLOSSARY.md`](../../GLOSSARY.md)** ensuring each entry includes:
- **Everyday Analogy**: An accessible real-world comparison for non-technical readers.
- **Technical Definition**: What the tool or algorithm does at the engineering level.
- **Official Link**: URL to the official website or upstream repository.
- **Why It Is Used in This Project**: Concrete benefit for data sovereignty, token efficiency, performance, or hallucination mitigation.
