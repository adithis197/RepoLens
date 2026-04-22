from fastapi import APIRouter, HTTPException
import traceback
from .schemas import AnalyzeRequest
from ..pipeline.step0_ingestion.ingestion import ingest_repo
from ..pipeline.step1_parsing.parser import (
    build_dependency_graph,
    get_high_centrality_files,
)
from ..pipeline.step2a_context_inference.inference import infer_repo_context
from ..pipeline.step2b_retrieval.retrieval import select_top_k, compress_remaining
from ..pipeline.step3_architecture_gen.generator import generate_architecture
from ..pipeline.step4_output.formatter import format_output

router = APIRouter()


@router.post("/analyze")
async def analyze_repo(req: AnalyzeRequest):
    try:
        # Step 0: Ingestion
        snapshot = await ingest_repo(req.repo_url)

        # Step 1: Dependency graph
        graph = build_dependency_graph(snapshot)
        top_files = get_high_centrality_files(graph, top_n=10)

        # Step 2A: LLM-based context inference
        context = await infer_repo_context(snapshot, graph)

        # Step 2B: Ranking + token-budgeted retrieval
        top_k = select_top_k(snapshot, graph, context, token_budget=8000)
        compressed = compress_remaining(snapshot, [f.path for f in top_k])

        # Step 3: Architecture generation
        raw = await generate_architecture(context, top_k)

        # Step 4: Format final output
        result = format_output(raw, context)

        # Merge all fields into one response — popup reads all of these
        result.update({
            # Person 1 — repo snapshot stats
            "total_files": len(snapshot.file_tree),
            "signal_files": list(snapshot.signal_files.keys()),
            "graph_nodes": graph.number_of_nodes(),
            "graph_edges": graph.number_of_edges(),
            "top_central_files": top_files,

            # Person 2 — extra context fields
            "domain": getattr(context, "domain", ""),

            # Person 3 — retrieval stats
            "selected_files": [f.path for f in top_k],
            "total_selected": len(top_k),
            "estimated_tokens": sum(len(f.content or "") // 4 for f in top_k),
            "compressed_folders": compressed,

            # Repo metadata for click-through
            "repo_owner": snapshot.owner,
            "repo_name": snapshot.repo,
            "default_branch": snapshot.default_branch,
        })

        return result

    except Exception as e:
        print("ERROR IN /analyze:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/ingestion")
async def test_ingestion(req: AnalyzeRequest):
    """Quick test endpoint — runs only Step 0 + Step 1."""
    snapshot = await ingest_repo(req.repo_url)
    graph = build_dependency_graph(snapshot)
    top_files = get_high_centrality_files(graph, top_n=10)
    return {
        "total_files": len(snapshot.file_tree),
        "signal_files": list(snapshot.signal_files.keys()),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "top_central_files": top_files,
    }


@router.get("/health")
def health():
    return {"status": "ok"}