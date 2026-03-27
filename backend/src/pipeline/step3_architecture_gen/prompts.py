"""
Prompt templates for Step 3 architecture generation.
"""
from ..step2a_context_inference.inference import RepoContext
from ..step0_ingestion.ingestion import FileNode


def build_architecture_prompt(
    context: RepoContext, top_k_files: list[FileNode], evidence_graph: dict
) -> str:
    files_str = "\n\n".join(
        f"### {f.path}\n{f.content[:1000]}" for f in top_k_files
    )
    return f"""You are a software architect generating documentation.

## Repo Summary
{context.summary}

## Tech Stack
{", ".join(context.tech_stack)}

## Main Modules
{", ".join(context.main_modules)}

## Selected Source Files
{files_str}

## Evidence Graph (routes / handlers / DB calls found)
{evidence_graph}

## Task
Return a JSON object with:
- architecture_mermaid: a valid Mermaid flowchart diagram string
- flow_mermaid: list of 2-5 Mermaid sequence diagram strings for key flows
- evidence_map: list of objects {{node_id, file, start_line, end_line}}

Rules:
- Only include nodes/edges you can ground to a specific file above
- Assign stable snake_case IDs to each node (used for UI click-through)

Respond ONLY with valid JSON. No markdown fences.
"""
