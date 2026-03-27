"""
Step 3: Evidence-Grounded Architecture Generation (Second LLM Pass)

Input:
  - RepoContext from Step 2A
  - Top-K file contents from Step 2B
  - Lightweight evidence graph (routes, handlers, DB/queue refs)

Output:
  - Mermaid architecture diagram
  - 2-5 representative flow diagrams
  - Evidence map: node_id → (file, start_line, end_line)

Constraint: LLM must only emit nodes/edges backed by evidence.
"""
from ..step2a_context_inference.inference import RepoContext
from ..step0_ingestion.ingestion import FileNode
from ...llm.client import call_llm
from .prompts import build_architecture_prompt
from .evidence import build_evidence_graph


async def generate_architecture(context: RepoContext, top_k_files: list[FileNode]) -> dict:
    """
    Runs the second LLM pass and returns raw structured output.
    """
    evidence_graph = build_evidence_graph(top_k_files)
    prompt = build_architecture_prompt(context, top_k_files, evidence_graph)
    raw = await call_llm(prompt)

    # TODO: parse JSON from raw — extract architecture_mermaid, flow_mermaid, evidence_map
    return {"raw": raw, "evidence_graph": evidence_graph}
