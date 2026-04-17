"""
Prompt templates for Step 2A context inference.
"""
from ..step0_ingestion.ingestion import RepoSnapshot


def build_context_inference_prompt(snapshot: RepoSnapshot, central_contents: dict) -> str:
    file_tree_str = "\n".join(f.path for f in snapshot.file_tree[:250])

    signal_str = "\n\n".join(
        f"### {path}\n{content[:1200]}"
        for path, content in snapshot.signal_files.items()
    )

    central_str = "\n\n".join(
        f"### {path}\n{content[:800]}"
        for path, content in list(central_contents.items())[:15]
    )

    return f"""You are a senior software architect analyzing an unfamiliar codebase.

Your job is to infer the repository's purpose and structure for downstream retrieval and architecture generation.

## Repository File Tree (first 250 files)
{file_tree_str}

## Signal Files
{signal_str}

## Important Source Files (excerpts)
{central_str}

## Task
Analyze this repository and return a structured JSON object.

Use ONLY the information provided.
Do NOT invent files, APIs, frameworks, tools, or architecture components that are not supported by the repository content.

Reason about the repository as a whole:
- Use the file tree to understand the overall structure
- Use signal files to infer packaging, tooling, dependencies, and repo identity
- Use important source files to infer core behavior and architecture
- Prefer repository-level purpose over narrow helper-module details

For example, do not describe the repo primarily by one helper module unless the evidence clearly shows that helper module defines the repository's main purpose.

## Entry Point Selection Rules
When identifying entry_points, use evidence from THIS repository only.

An entry point is a real file that serves as one or more of the following:
- CLI bootstrap or command entry
- application or server startup
- top-level orchestration
- public package bootstrap
- primary API surface
- central routing, dispatch, or command-definition layer

Requirements for entry_points:
- Only return file paths that definitely exist in the Repository File Tree above
- Every path must exactly match a path shown in the Repository File Tree
- Do NOT guess, rewrite, shorten, or infer paths
- Do NOT convert filesystem paths into package-style paths
- If a path appears as src/black/__init__.py, return exactly src/black/__init__.py
- It is better to return fewer correct entry_points than to include incorrect ones

Selection guidance:
- Prefer files that define startup behavior, public interfaces, command registration, routing, dispatch, or top-level orchestration
- Use filename patterns like main.py, app.py, cli.py, server.py, __main__.py, or __init__.py only as supporting hints, not as the main reason for selection
- Do NOT rely on generic assumptions like "main.py is always the entry point"
- Do NOT include docs, tests, examples, benchmarks, CI/action files, config files, migrations, or small helper utilities
- Do NOT include __init__.py unless it clearly functions as a real public bootstrap, exposed package entry, or top-level interface in this repository

## Output Requirements
Return valid JSON with these exact keys:
- summary
- tech_stack
- domain
- main_modules
- entry_points
- keywords

## Field Definitions

- summary:
  One sentence describing what the repository does in plain English.
  Make it concrete, repository-specific, and focused on the overall purpose of the repository.

- tech_stack:
  A list of programming languages, frameworks, libraries, and major tools clearly supported by the provided files.
  Prefer technologies that appear to matter to the repository as a whole, not incidental implementation details.

- domain:
  A short category such as "web framework", "API framework", "browser extension", "ML library", "data pipeline", "CLI tool", "systems library", or "developer tooling".
  Choose the category that best matches the repository's primary purpose.

- main_modules:
  A list of 4 to 8 concrete functional subsystems or architectural areas.
  These should be repository-specific conceptual areas such as routing, parsing, formatting, rendering, request handling, storage, orchestration, CLI execution, dependency injection, compiler passes, training, or build orchestration.
  Do NOT return file paths, filenames, or directories.
  Each item should be a short conceptual phrase, not a source file.
  Prefer concepts that reflect major architectural responsibilities in this repository.

- entry_points:
  A list of 1 to 5 real file paths representing the main starting points or public bootstrap surfaces of the repository.
  Only include paths that you are certain exist in the Repository File Tree above.

- keywords:
  A list of 8 to 15 technical search terms useful for downstream retrieval and ranking.
  Prefer repository-specific and architecture-specific terms over generic words.
  Include important concepts, APIs, protocols, module areas, tool names, and technical terms that are clearly supported by the provided files.

## Additional Rules
- Prefer repository-level understanding over narrow file-level overfitting
- Prefer concrete and technical module names over generic labels like "utilities"
- Prefer retrieval-friendly keywords such as APIs, protocols, framework concepts, tool names, and architectural terms
- Do not include duplicate items
- Be concise but specific

Respond ONLY with valid JSON.
Do not use markdown fences.
Do not include any explanation outside the JSON.
"""