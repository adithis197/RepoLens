"""
GitHub REST/GraphQL API client helpers.
Handles auth, rate limiting, and raw file fetching.
"""
import os
import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"


def _headers():
    return {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}


async def get_file_tree(owner: str, repo: str) -> list:
    """Fetch the recursive file tree for a repo."""
    # TODO: GET /repos/{owner}/{repo}/git/trees/HEAD?recursive=1
    raise NotImplementedError


async def get_file_content(owner: str, repo: str, path: str) -> str:
    """Fetch raw content of a single file."""
    # TODO: GET /repos/{owner}/{repo}/contents/{path}  (decode base64)
    raise NotImplementedError


def parse_repo_url(url: str):
    """Extract (owner, repo) from a GitHub URL."""
    # e.g. https://github.com/owner/repo
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]
