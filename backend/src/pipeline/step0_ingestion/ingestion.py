"""
Step 0: Repo Ingestion & Snapshot

Builds a lightweight repo snapshot:
  - file tree (paths, extensions, sizes)
  - signal files (Dockerfile, docker-compose, CI configs, k8s manifests)
  - raw file content cache for high-centrality files (populated later)

Does NOT read all file contents — only metadata + signal files upfront.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


SIGNAL_FILES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", "k8s", "kubernetes",
    "package.json", "requirements.txt", "go.mod", "pom.xml", "Cargo.toml",
    ".env.example", "Makefile",
}


@dataclass
class FileNode:
    path: str
    extension: str
    size_bytes: int
    is_signal: bool = False
    content: Optional[str] = None  # populated selectively


@dataclass
class RepoSnapshot:
    repo_url: str
    file_tree: List[FileNode] = field(default_factory=list)
    signal_files: Dict[str, str] = field(default_factory=dict)  # path -> content


async def ingest_repo(repo_url: str) -> RepoSnapshot:
    """
    Main entrypoint for Step 0.
    Fetches file tree from GitHub API and reads signal file contents.
    """
    # TODO: implement GitHub API calls (use GITHUB_TOKEN from env)
    # 1. GET /repos/{owner}/{repo}/git/trees/HEAD?recursive=1
    # 2. Filter signal files and fetch their raw content
    # 3. Build FileNode list from the tree response
    raise NotImplementedError
