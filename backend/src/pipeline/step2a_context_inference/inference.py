from dataclasses import dataclass, field
from typing import List
import json
import networkx as nx

from ..step0_ingestion.ingestion import RepoSnapshot
from ..step1_parsing.parser import get_high_centrality_files, is_noise_path
from ...llm.client import call_llm
from .prompts import build_context_inference_prompt


@dataclass
class RepoContext:
    summary: str = ""
    tech_stack: List[str] = field(default_factory=list)
    domain: str = ""
    main_modules: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


IMPORTANT_HINTS = [
    "main", "app", "cli", "route", "routing", "application",
    "api", "server", "openapi", "security", "dependency",
    "request", "response", "views", "models", "schemas", "core"
]

ENTRY_FILE_NAMES = {
    "main.py", "app.py", "cli.py", "server.py", "manage.py", "run.py",
    "index.js", "index.ts", "server.js", "server.ts",
    "main.go", "main.rs", "main.java",
    "main.c", "main.cc", "main.cpp", "main.cxx",
    "program.cs",
}

FRAMEWORK_CORE_NAMES = {
    "applications.py", "routing.py", "api.py", "core.py",
    "router.py", "server.py", "wsgi.py", "asgi.py",
    "urls.py", "handlers.py",
}

VALID_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rb", ".php",
    ".c", ".cc", ".cpp", ".cxx", ".cs", ".rs"
)

STARTUP_SIGNALS = [
    'if __name__ == "__main__"',
    "if __name__ == '__main__'",
    "app.listen(",
    "createserver(",
    "express(",
    "fastapi(",
    "flask(",
    "typer(",
    "click.command",
    "argparse",
    "int main(",
    "public static void main",
    "package main",
    "func main(",
]

def _clean_llm_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return text


def _score_context_file(path: str) -> int:
    path_lower = path.lower()
    filename = path_lower.split("/")[-1]
    score = 0

    if is_noise_path(path):
        return -100

    for hint in IMPORTANT_HINTS:
        if hint in path_lower:
            score += 2

    if filename in ENTRY_FILE_NAMES:
        score += 4

    if filename in FRAMEWORK_CORE_NAMES:
        score += 6

    if filename == "__init__.py":
        score += 1

    return score


def _score_entry_point(path: str, content: str = "") -> int:
    path_lower = path.lower()
    filename = path_lower.split("/")[-1]
    content_lower = content.lower()
    score = 0

    if is_noise_path(path):
        return -100

    if not path_lower.endswith(VALID_EXTENSIONS):
        return -100

    if filename in ENTRY_FILE_NAMES:
        score += 8

    if filename in FRAMEWORK_CORE_NAMES:
        score += 6

    if any(token in filename for token in ["main", "app", "server", "cli", "manage", "run", "index"]):
        score += 3

    if filename == "__init__.py":
        score -= 3

    for sig in STARTUP_SIGNALS:
        if sig in content_lower:
            score += 6

    return score


def _is_valid_entry_point(path: str, content: str = "") -> bool:
    path_lower = path.lower()
    filename = path_lower.split("/")[-1]

    if is_noise_path(path):
        return False

    if path_lower.endswith((".md", ".rst", ".toml", ".txt", ".yml", ".yaml", ".json")):
        return False

    if not path_lower.endswith(VALID_EXTENSIONS):
        return False

    if filename == "__init__.py":
        return _score_entry_point(path, content) >= 6

    return True


def _select_context_files(snapshot: RepoSnapshot, dep_graph: nx.DiGraph, top_n: int = 15) -> List[str]:
    central_files = get_high_centrality_files(dep_graph, top_n=30)
    all_paths = [node.path for node in snapshot.file_tree if not is_noise_path(node.path)]

    candidates = set(central_files)

    for path in all_paths:
        if _score_context_file(path) >= 3:
            candidates.add(path)

    ranked = sorted(candidates, key=_score_context_file, reverse=True)
    return ranked[:top_n]


def _fallback_entry_points(snapshot: RepoSnapshot, selected_paths: List[str]) -> List[str]:
    path_to_node = {node.path: node for node in snapshot.file_tree}
    candidates = []

    for path in selected_paths:
        node = path_to_node.get(path)
        content = node.content if node and node.content else ""
        if _is_valid_entry_point(path, content):
            score = _score_entry_point(path, content)
            if score >= 4:
                candidates.append((score, path))

    if not candidates:
        for node in snapshot.file_tree:
            content = node.content if node.content else ""
            if _is_valid_entry_point(node.path, content):
                score = _score_entry_point(node.path, content)
                if score >= 5:
                    candidates.append((score, node.path))

    candidates.sort(reverse=True)
    return [path for _, path in candidates[:5]]


def _clean_main_modules(modules: List[str]) -> List[str]:
    cleaned = []

    for m in modules:
        if not isinstance(m, str):
            continue
        m = m.strip()
        if not m:
            continue
        if "/" in m:
            continue
        if m.endswith(VALID_EXTENSIONS):
            continue
        cleaned.append(m)

    seen = set()
    result = []
    for m in cleaned:
        if m not in seen:
            seen.add(m)
            result.append(m)

    return result[:8]


def _fallback_keywords(central_contents: dict[str, str], selected_paths: List[str]) -> List[str]:
    text = " ".join(central_contents.values()).lower()
    path_text = " ".join(selected_paths).lower()

    candidate_terms = [
        "api", "application", "routing", "request", "response", "cli",
        "security", "authentication", "authorization", "openapi",
        "validation", "dependencies", "models", "serialization",
        "http", "server", "client", "parser", "build", "database"
    ]

    found = [term for term in candidate_terms if term in text or term in path_text]

    if not found:
        found = ["api", "application", "routing", "request", "response", "cli"]

    seen = set()
    result = []
    for term in found:
        if term not in seen:
            seen.add(term)
            result.append(term)

    return result[:12]


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def _normalize_entry_point_path(path: str, existing_paths: set[str]) -> str | None:
    if not isinstance(path, str):
        return None

    candidate = path.strip().lstrip("./")
    if not candidate:
        return None

    # 1. exact match
    if candidate in existing_paths:
        return candidate

    # 2. common Python src-layout recovery
    src_candidate = f"src/{candidate}"
    if src_candidate in existing_paths:
        return src_candidate

    # 3. unique suffix match
    suffix_matches = [p for p in existing_paths if p.endswith(candidate)]
    if len(suffix_matches) == 1:
        return suffix_matches[0]

    # 4. unique filename match
    filename = candidate.split("/")[-1]
    filename_matches = [p for p in existing_paths if p.split("/")[-1] == filename]
    if len(filename_matches) == 1:
        return filename_matches[0]

    return None


def _normalize_entry_points(paths: List[str], existing_paths: set[str]) -> List[str]:
    normalized = []

    for path in paths:
        mapped = _normalize_entry_point_path(path, existing_paths)
        if mapped:
            normalized.append(mapped)

    return _dedupe(normalized)

async def infer_repo_context(snapshot: RepoSnapshot, dep_graph: nx.DiGraph) -> RepoContext:
    selected_paths = _select_context_files(snapshot, dep_graph, top_n=15)
    path_to_node = {node.path: node for node in snapshot.file_tree}

    print("\n[DEBUG] selected_paths sent to prompt:")
    for path in selected_paths:
        print(" ", path)

    central_contents = {}
    for path in selected_paths:
        node = path_to_node.get(path)
        if node and node.content:
            central_contents[path] = node.content[:800]

    print("\n[DEBUG] central_contents keys:")
    for path in central_contents.keys():
        print(" ", path)

    prompt = build_context_inference_prompt(snapshot, central_contents)

    raw = await call_llm(prompt)
    cleaned = _clean_llm_json(raw)
    parsed = json.loads(cleaned)

    print("\n[DEBUG] RAW LLM OUTPUT:\n", raw)
    print("\n[DEBUG] CLEANED LLM JSON:\n", cleaned)
    print("\n[DEBUG] parsed entry_points:", parsed.get("entry_points", []))
    print("[DEBUG] parsed main_modules:", parsed.get("main_modules", []))

    summary = parsed.get("summary", "")
    tech_stack = parsed.get("tech_stack", [])
    domain = parsed.get("domain", "")
    main_modules = parsed.get("main_modules", [])
    entry_points = parsed.get("entry_points", [])
    keywords = parsed.get("keywords", [])

    if not isinstance(summary, str):
        summary = ""
    if not isinstance(tech_stack, list):
        tech_stack = []
    if not isinstance(domain, str):
        domain = ""
    if not isinstance(main_modules, list):
        main_modules = []
    if not isinstance(entry_points, list):
        entry_points = []
    if not isinstance(keywords, list):
        keywords = []

    main_modules = _clean_main_modules(main_modules)

    existing_paths = {node.path for node in snapshot.file_tree}
    normalized_entry_points = _normalize_entry_points(entry_points, existing_paths)

    print("[DEBUG] normalized entry_points:", normalized_entry_points)

    filtered_entry_points = []

    for path in normalized_entry_points:
        node = path_to_node.get(path)
        content = node.content if node and node.content else ""
        if _is_valid_entry_point(path, content):
            score = _score_entry_point(path, content)
            if score >= 4:
                filtered_entry_points.append((score, path))

    filtered_entry_points.sort(reverse=True)
    entry_points = [path for _, path in filtered_entry_points]

    print("\n[DEBUG] filtered_entry_points:", filtered_entry_points)

    if not entry_points:
        entry_points = _fallback_entry_points(snapshot, selected_paths)
        print("[DEBUG] fallback entry_points:", entry_points)

    if not keywords:
        keywords = _fallback_keywords(central_contents, selected_paths)

    if not main_modules:
        main_modules = [
            "application setup",
            "routing",
            "request handling",
            "response handling",
            "CLI",
        ]

    return RepoContext(
        summary=summary,
        tech_stack=_dedupe(tech_stack),
        domain=domain,
        main_modules=_dedupe(main_modules),
        entry_points=_dedupe(entry_points)[:5],
        keywords=_dedupe(keywords)[:12],
    )