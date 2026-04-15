from fastapi import APIRouter
from .schemas import AnalyzeRequest
from ..pipeline.step0_ingestion.ingestion import ingest_repo
from ..pipeline.step1_parsing.parser import build_dependency_graph, get_high_centrality_files

router = APIRouter()


@router.post("/analyze")
async def analyze_repo(req: AnalyzeRequest):
    return {"status": "not implemented yet — waiting for Person 2"}


@router.post("/test/ingestion")
async def test_ingestion(req: AnalyzeRequest):
    snapshot = await ingest_repo(req.repo_url)
    graph = build_dependency_graph(snapshot)
    top_files = get_high_centrality_files(graph, top_n=10)

    # Build readable edge list: "file_a → file_b"
    edges = [
        {"from": u, "to": v}
        for u, v in list(graph.edges)[:50]  # show first 50 edges
    ]

    # Build adjacency: for each top file, show what it imports
    adjacency = {}
    for f in top_files:
        imports = list(graph.successors(f))
        imported_by = list(graph.predecessors(f))
        adjacency[f] = {
            "imports": imports,
            "imported_by": imported_by,
        }

    return {
        "total_files": len(snapshot.file_tree),
        "signal_files": list(snapshot.signal_files.keys()),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "top_central_files": top_files,
        "adjacency": adjacency,
        "edges_sample": edges,
    }


@router.get("/health")
def health():
    return {"status": "ok"}