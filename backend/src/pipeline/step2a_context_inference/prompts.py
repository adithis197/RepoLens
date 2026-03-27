"""
Prompt templates for Step 2A context inference.
"""
from ..step0_ingestion.ingestion import RepoSnapshot


def build_context_inference_prompt(snapshot: RepoSnapshot, central_contents: dict) -> str:
    file_tree_str = "\n".join(f.path for f in snapshot.file_tree[:200])
    signal_str = "\n\n".join(
        f"### {path}\n{content}" for path, content in snapshot.signal_files.items()
    )
    central_str = "\n\n".join(
        f"### {path}\n{content[:500]}" for path, content in list(central_contents.items())[:10]
    )

    return f"""You are a senior software architect analyzing an unfamiliar codebase.

## File Tree (first 200 files)
{file_tree_str}

## Signal Files
{signal_str}

## High-Centrality Files (excerpts)
{central_str}

## Task
Return a JSON object with:
- summary: one-sentence plain-English description of the repo
- tech_stack: list of frameworks/languages/tools
- domain: e.g. "e-commerce", "auth service", "analytics dashboard"
- main_modules: list of major functional areas
- entry_points: likely route/handler/main files
- keywords: useful retrieval terms

Respond ONLY with valid JSON. No markdown fences.
"""
