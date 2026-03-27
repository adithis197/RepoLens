"""
Orchestrates the full RepoLens pipeline:
  Step 0 → Step 1 → Step 2A → Step 2B → Step 3 → Step 4
"""
from .step0_ingestion.ingestion import ingest_repo
from .step1_parsing.parser import build_dependency_graph
from .step2a_context_inference.inference import infer_repo_context
from .step2b_retrieval.retrieval import select_top_k
from .step3_architecture_gen.generator import generate_architecture
from .step4_output.formatter import format_output


async def run_pipeline(repo_url: str, token_budget: int = 8000):
    # Step 0
    snapshot = await ingest_repo(repo_url)

    # Step 1
    dep_graph = build_dependency_graph(snapshot)

    # Step 2A
    context = await infer_repo_context(snapshot, dep_graph)

    # Step 2B
    top_k_files = select_top_k(snapshot, dep_graph, context, token_budget)

    # Step 3
    raw_output = await generate_architecture(context, top_k_files)

    # Step 4
    return format_output(raw_output)
