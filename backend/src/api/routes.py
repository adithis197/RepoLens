from fastapi import APIRouter
from pydantic import BaseModel
import traceback
from fastapi import HTTPException
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
    # Ingestion
    snapshot = await ingest_repo(req.repo_url)

    # Dependency graph
    graph = build_dependency_graph(snapshot)
    top_files = get_high_centrality_files(graph, top_n=10)

    # LLM-based context inference
    context = await infer_repo_context(snapshot, graph)
    top_k = select_top_k(snapshot, graph, context, token_budget=8000)
    compressed = compress_remaining(snapshot, [f.path for f in top_k])

    raw = await generate_architecture(context, top_k)
    result = format_output(raw, context)

    return result

    return {
        # Repository metadata
        "total_files": len(snapshot.file_tree),
        "signal_files": list(snapshot.signal_files.keys()),

        # Dependency graph
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "top_central_files": top_files,

        # LLM-generated context
        "repo_summary": context.summary,
        "tech_stack": context.tech_stack,
        "domain": context.domain,
        "main_modules": context.main_modules,
        "entry_points": context.entry_points,
        "keywords": context.keywords,

        "selected_files": [f.path for f in top_k],
        "total_selected": len(top_k),
        "estimated_tokens": sum(len(f.content or "") // 4 for f in top_k),
        "compressed_folders": compressed,
    }
   except Exception as e:
        print("ERROR IN /analyze:")
        traceback.print_exc()   # ← prints full stack trace in terminal
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/ingestion")
async def test_ingestion(req: AnalyzeRequest):
    """Quick test endpoint — runs only Step 0 ingestion and returns snapshot stats."""
    snapshot = await ingest_repo(req.repo_url)
    return {
        "total_files": len(snapshot.files),
        "signal_files": [f.path for f in snapshot.files if f.is_signal],
        "sample_paths": [f.path for f in snapshot.files[:10]],
    }

@router.get("/health")
def health():
    return {"status": "ok"}