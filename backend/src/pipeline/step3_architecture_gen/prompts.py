"""
Prompt templates for Step 3 architecture generation.
"""
from ..step2a_context_inference.inference import RepoContext
from ..step0_ingestion.ingestion import FileNode


def build_architecture_prompt(
    context: RepoContext, top_k_files: list[FileNode], evidence_graph: dict
) -> str:
    files_str = "\n\n".join(
        f"### {f.path}\n```\n{f.content or ''}\n```"
        for f in top_k_files
    )
    file_list = "\n".join(f"- {f.path}" for f in top_k_files)

    return f"""You are creating an onboarding architecture diagram for a new developer.
Your goal: a diagram so specific and useful it replaces 2 hours of code reading.

## Repo Summary
{context.summary}

## Domain
{getattr(context, 'domain', 'unknown')}

## Tech Stack
{", ".join(context.tech_stack)}

## Main Modules
{", ".join(context.main_modules)}

## Available Files (USE EXACTLY THESE PATHS)
{file_list}

## Full File Contents
{files_str}

## Evidence Graph (regex-extracted routes/handlers/DB calls)
{evidence_graph}

## Task
Return a JSON object with these keys:

### 1. narrative_summary
A rich 5-7 sentence paragraph for a new developer. Cover:
- What this system does, the main architectural pattern
- How data/control flows from inputs → processing → outputs
- Names of 3-5 KEY FUNCTIONS or CLASSES they will see (from the file contents above)
- Where to start reading

### 2. architecture_mermaid
A Mermaid `graph TD` with 12-16 nodes. MUST be specific — include real function/class names you found in the file contents.

Each node format: `node_id["Concept + Key Function/Class<br/>filename.py"]`

Example of GOOD specificity (bad vs good):
- BAD: `app["Flask App<br/>app.py"]`
- GOOD: `app["Flask App<br/>wsgi_app(), full_dispatch_request()<br/>app.py"]`

Required sections (adapt to repo type):
- **Inputs**: what enters the system (HTTP request, training data, CLI args, etc.)
- **Entry points**: the file/function that first receives input
- **Core processing**: main classes/functions that do the work, with names
- **Data layer**: DB/storage/model files if any
- **Outputs**: what the system produces

Use:
- `subgraph` blocks to group related files
- `-->` for main control/data flow
- `-.->` for optional/indirect flow
- `classDef` for input/output/external node coloring

Example (Flask-like):
```
graph TD
    Client["HTTP Request"]:::input
    subgraph "WSGI Entry"
        Main["__main__.py<br/>main()"]
        App["Flask App<br/>wsgi_app(), __call__()<br/>app.py"]
    end
    subgraph "Request Lifecycle"
        Ctx["Request Context<br/>push(), pop()<br/>ctx.py"]
        Dispatch["Request Dispatch<br/>full_dispatch_request()<br/>app.py"]
        Preprocess["Before Request Hooks<br/>preprocess_request()<br/>app.py"]
        Routing["URL Routing<br/>Werkzeug Map"]
        View["User View Function"]
        Finalize["Response Finalize<br/>finalize_request()<br/>app.py"]
    end
    subgraph "Support"
        Wrappers["Request/Response<br/>Request, Response<br/>wrappers.py"]
        Globals["Thread-Local Globals<br/>current_app, g, request<br/>globals.py"]
        Json["JSON Handling<br/>dumps(), loads()<br/>json/__init__.py"]
    end
    Response["HTTP Response"]:::output

    Client --> Main --> App --> Ctx --> Dispatch
    Dispatch --> Preprocess --> Routing --> View --> Finalize
    Globals -.-> Dispatch
    View -.-> Wrappers
    View -.-> Json
    Finalize --> Response

    classDef input fill:#0d4f3c,stroke:#2ea043,color:#fff
    classDef output fill:#4f3d0d,stroke:#d29922,color:#fff
```

### 3. flow_mermaid
List of 2-3 sequenceDiagram strings for key flows (e.g. "HTTP request lifecycle", "App startup", "Model prediction").
Use real participant names from the code.

### 4. evidence_map
List of 12-16 objects `{{node_id, file, start_line, end_line}}` — one per node.
- node_id MUST match architecture_mermaid exactly
- file MUST be from "Available Files" above
- start_line/end_line should point to the actual function/class the node represents
- For concept nodes (input/output), use the closest relevant file

STRICT VALIDATION:
1. Does each node mention a real function/class name from the code? If no, rewrite.
2. Does the diagram show input → processing → output? If no, rewrite.
3. Does every node_id have an evidence_map entry? If no, add it.
4. Is every file in evidence_map from "Available Files"? If no, fix it.

Return ONLY valid JSON. No markdown fences. No truncation. Close all strings.
"""