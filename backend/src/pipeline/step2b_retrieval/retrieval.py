"""
Step 2B: Hybrid Retrieval & Importance Scoring (Token-Budgeted)

Selects top-K files/chunks that fit within the token budget using:
  1. Dependency graph centrality (PageRank)
  2. BM25 keyword matching against Step 2A keywords
  3. (Optional) CodeBERT embedding similarity

Non-selected areas get compressed into folder/module-level summaries.
"""
import networkx as nx
from rank_bm25 import BM25Okapi

from ..step0_ingestion.ingestion import RepoSnapshot, FileNode
from ..step2a_context_inference.inference import RepoContext


def select_top_k(
    snapshot: RepoSnapshot,
    dep_graph: nx.DiGraph,
    context: RepoContext,
    token_budget: int,
) -> list[FileNode]:
    """
    Returns a list of FileNodes whose combined token count fits the budget.
    """
    candidates = [f for f in snapshot.file_tree if f.content]

    centrality_scores = nx.pagerank(dep_graph)
    bm25_scores = _bm25_score(candidates, context.keywords)

    ranked = _hybrid_rank(candidates, centrality_scores, bm25_scores)

    selected, used_tokens = [], 0
    for file_node in ranked:
        tokens = _estimate_tokens(file_node.content or "")
        if used_tokens + tokens > token_budget:
            break
        selected.append(file_node)
        used_tokens += tokens

    return selected


def compress_remaining(snapshot: RepoSnapshot, selected: list[FileNode]) -> dict[str, str]:
    """
    For files NOT in `selected`, produce folder/module-level summaries.
    Returns dict: folder_path -> summary_string.
    """
    # TODO: group unselected files by top-level folder,
    # produce a one-line summary per folder
    raise NotImplementedError


def _bm25_score(candidates: list[FileNode], keywords: list[str]) -> dict[str, float]:
    corpus = [f.path.replace("/", " ").replace(".", " ").split() for f in candidates]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(keywords)
    return {f.path: float(scores[i]) for i, f in enumerate(candidates)}


def _hybrid_rank(candidates, centrality, bm25, alpha=0.5):
    """Combine centrality + BM25 with weight alpha."""
    def score(f):
        c = centrality.get(f.path, 0.0)
        b = bm25.get(f.path, 0.0)
        return alpha * c + (1 - alpha) * b
    return sorted(candidates, key=score, reverse=True)


def _estimate_tokens(text: str) -> int:
    return len(text) // 4  # rough 4-chars-per-token heuristic
