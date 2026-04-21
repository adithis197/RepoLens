"""
Builds a lightweight evidence graph from top-K files:
  - routes / endpoints
  - handlers / controllers
  - DB interactions
  - queue interactions
"""
from ..step0_ingestion.ingestion import FileNode
import re
def build_evidence_graph(top_k_files: list[FileNode]) -> dict:
    """
    Scan file contents for route definitions, DB calls, queue calls.
    Returns structured dict used in the architecture generation prompt.
    """
    # TODO: use regex / Tree-sitter to extract:
    #   routes: [(method, path, file, line)]
    #   handlers: [(name, file, line)]
    #   db_calls: [(operation, model, file, line)]
    routes = []
    handlers = []
    db_calls = []

    for f in top_k_files:
        if not f.content:
            continue

        # --- Flask routes: @app.route('/path') ---
        for match in re.finditer(r"@\w+\.route\([\"'](.+?)[\"']\)", f.content):
            routes.append({"path": match.group(1), "file": f.path})

        # --- FastAPI routes: @router.get/post/put/delete('/path') ---
        for match in re.finditer(
            r"@\w+\.(get|post|put|delete|patch)\([\"'](.+?)[\"']\)", f.content
        ):
            routes.append({
                "method": match.group(1).upper(),
                "path": match.group(2),
                "file": f.path,
            })

        # --- Function / class definitions ---
        for match in re.finditer(r"^(?:async )?def (\w+)\(", f.content, re.MULTILINE):
            handlers.append({"name": match.group(1), "file": f.path})

        for match in re.finditer(r"^class (\w+)", f.content, re.MULTILINE):
            handlers.append({"name": match.group(1), "file": f.path})

        # --- DB calls: db.Model.query / session.* / ORM patterns ---
        for match in re.finditer(
            r"(db\.\w+|Model\.query|session\.\w+|\.objects\.\w+)", f.content
        ):
            db_calls.append({"call": match.group(1), "file": f.path})

    return {
        "routes": routes[:20],
        "handlers": handlers[:20],
        "db_calls": db_calls[:20],
    }
