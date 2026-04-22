"""
Step 3: Evidence-Grounded Architecture Generation (Second LLM Pass)
"""
from ..step2a_context_inference.inference import RepoContext
from ..step0_ingestion.ingestion import FileNode
from ...llm.client import call_llm
from .prompts import build_architecture_prompt
from .evidence import build_evidence_graph


async def generate_architecture(context: RepoContext, top_k_files: list[FileNode]) -> dict:
    evidence_graph = build_evidence_graph(top_k_files)
    prompt = build_architecture_prompt(context, top_k_files, evidence_graph)

    # Bigger max_tokens — we want rich diagrams + 12-16 evidence entries + narrative
    raw = await call_llm(prompt, max_tokens=4000)

    return {"raw": raw, "evidence_graph": evidence_graph}