"""
Step 2A: Repo Context Inference (First LLM Pass)

Input:
  - Repo snapshot (file tree + signal files)
  - Top high-centrality file contents (from Step 1)

Output:
  - RepoContext: human-readable summary + structured fields
    (tech_stack, domain, main_modules, entry_points, keywords)

This output drives:
  - User-facing onboarding summary
  - Query keywords for Step 2B retrieval
"""
from dataclasses import dataclass, field
from typing import List
import networkx as nx

from ..step0_ingestion.ingestion import RepoSnapshot
from ..step1_parsing.parser import get_high_centrality_files
from ...llm.client import call_llm
from .prompts import build_context_inference_prompt


@dataclass
class RepoContext:
    summary: str = ""
    tech_stack: List[str] = field(default_factory=list)
    domain: str = ""
    main_modules: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


async def infer_repo_context(snapshot: RepoSnapshot, dep_graph: nx.DiGraph) -> RepoContext:
    """
    Build the prompt from snapshot + central files, call LLM, parse response.
    """
    central_files = get_high_centrality_files(dep_graph, top_n=15)

    # Gather content for central files that were already fetched
    central_contents = {
        f: snapshot.file_tree[i].content
        for i, f in enumerate(central_files)
        if snapshot.file_tree[i].content
    }

    prompt = build_context_inference_prompt(snapshot, central_contents)
    raw = await call_llm(prompt)

    # TODO: parse structured JSON from raw LLM response
    return RepoContext(summary=raw)
