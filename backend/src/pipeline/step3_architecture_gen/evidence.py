"""
Builds a lightweight evidence graph from top-K files:
  - routes / endpoints
  - handlers / controllers
  - DB interactions
  - queue interactions
"""
from ..step0_ingestion.ingestion import FileNode


def build_evidence_graph(top_k_files: list[FileNode]) -> dict:
    """
    Scan file contents for route definitions, DB calls, queue calls.
    Returns structured dict used in the architecture generation prompt.
    """
    # TODO: use regex / Tree-sitter to extract:
    #   routes: [(method, path, file, line)]
    #   handlers: [(name, file, line)]
    #   db_calls: [(operation, model, file, line)]
    return {"routes": [], "handlers": [], "db_calls": [], "queue_calls": []}
