from dataclasses import dataclass, field
from typing import Optional
from .github_client import parse_repo_url, get_file_tree, get_file_content

SIGNAL_FILENAMES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "package.json", "requirements.txt", "go.mod", "pom.xml",
    "Cargo.toml", "Makefile", ".env.example", "tsconfig.json",
    "webpack.config.js", "vite.config.js", "setup.py", "pyproject.toml",
    "setup.cfg", "Pipfile", "Pipfile.lock", "poetry.lock",
    "README.md",
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

ALWAYS_FETCH_FILENAMES = {
    "applications.py", "routing.py", "api.py", "core.py",
    "app.py", "main.py", "server.py", "cli.py",
    "__main__.py", "__init__.py", "wsgi.py", "asgi.py", "manage.py", "run.py",
    "index.js", "index.ts", "server.js", "server.ts",
    "app.js", "app.ts", "main.go", "main.rs",
    "train.py", "predict.py", "inference.py", "pipeline.py", "model.py",
}

MAX_FILE_SIZE = 300_000
MAX_SOURCE_FILES = 150


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

    raw_tree = await get_file_tree(owner, repo)

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

    for node in snapshot.file_tree:
        if node.is_signal:
            content = await get_file_content(owner, repo, node.path)
            node.content = content
            snapshot.signal_files[node.path] = content

    source_files = [
        n for n in snapshot.file_tree
        if n.extension in SOURCE_EXTENSIONS and not n.is_signal and not n.content
    ]

    pinned = [
        n for n in source_files
        if n.path.split("/")[-1].lower() in ALWAYS_FETCH_FILENAMES
    ]

    pinned.sort(key=lambda n: (n.path.count("/"), n.size_bytes))

    normal = [n for n in source_files if n not in pinned]
    normal.sort(key=lambda n: (n.path.count("/"), n.size_bytes))

    remaining_slots = max(0, MAX_SOURCE_FILES - len(pinned))
    selected = pinned[:MAX_SOURCE_FILES] + normal[:remaining_slots]

    print(f"[ingestion] fetching content for {len(selected)} source files...")
    for node in selected:
        node.content = await get_file_content(owner, repo, node.path)

    print(f"[ingestion] {len(snapshot.file_tree)} files, "
          f"{len(snapshot.signal_files)} signal files, "
          f"{len(selected)} source files with content")

    return snapshot