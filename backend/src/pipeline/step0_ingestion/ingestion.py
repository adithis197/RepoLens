import os
from dataclasses import dataclass, field
from typing import Optional
from .github_client import parse_repo_url, get_file_tree, get_file_content

SIGNAL_FILENAMES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "package.json", "requirements.txt", "go.mod", "pom.xml",
    "Cargo.toml", "Makefile", ".env.example", "tsconfig.json",
    "webpack.config.js", "vite.config.js", "setup.py", "pyproject.toml",
}

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
    ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".pdf", ".zip",
    ".lock", ".sum",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt",
}

MAX_FILE_SIZE = 100_000  # 100KB
MAX_SOURCE_FILES = 150   # don't fetch content for every file — too many API calls


@dataclass
class FileNode:
    path: str
    extension: str
    size_bytes: int
    is_signal: bool = False
    content: Optional[str] = None


@dataclass
class RepoSnapshot:
    repo_url: str
    owner: str
    repo: str
    file_tree: list = field(default_factory=list)
    signal_files: dict = field(default_factory=dict)


def _should_skip(path: str) -> bool:
    parts = path.split("/")
    if any(part in SKIP_DIRS for part in parts):
        return True
    ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
    if ext in SKIP_EXTENSIONS:
        return True
    return False


def _get_extension(path: str) -> str:
    return "." + path.rsplit(".", 1)[-1] if "." in path else ""


def _is_signal(path: str) -> bool:
    filename = path.split("/")[-1]
    return filename in SIGNAL_FILENAMES


async def ingest_repo(repo_url: str) -> RepoSnapshot:
    owner, repo = parse_repo_url(repo_url)
    snapshot = RepoSnapshot(repo_url=repo_url, owner=owner, repo=repo)

    # Step 1: get full file tree
    raw_tree = await get_file_tree(owner, repo)

    # Step 2: build FileNode list
    for item in raw_tree:
        path = item.get("path", "")
        size = item.get("size", 0)

        if _should_skip(path):
            continue
        if size > MAX_FILE_SIZE:
            continue

        node = FileNode(
            path=path,
            extension=_get_extension(path),
            size_bytes=size,
            is_signal=_is_signal(path),
        )
        snapshot.file_tree.append(node)

    # Step 3: fetch content for signal files
    for node in snapshot.file_tree:
        if node.is_signal:
            content = await get_file_content(owner, repo, node.path)
            node.content = content
            snapshot.signal_files[node.path] = content

    # Step 4: fetch content for source files (capped at MAX_SOURCE_FILES)
    # prioritise files closer to repo root (shorter path = more likely to be core)
    source_files = [
        n for n in snapshot.file_tree
        if n.extension in SOURCE_EXTENSIONS and not n.is_signal and not n.content
    ]
    source_files.sort(key=lambda n: (n.path.count("/"), n.size_bytes))
    source_files = source_files[:MAX_SOURCE_FILES]

    print(f"[ingestion] fetching content for {len(source_files)} source files...")
    for node in source_files:
        node.content = await get_file_content(owner, repo, node.path)

    print(f"[ingestion] {len(snapshot.file_tree)} files, "
          f"{len(snapshot.signal_files)} signal files, "
          f"{len(source_files)} source files with content")

    return snapshot