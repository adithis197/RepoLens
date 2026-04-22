import os
import base64
import httpx
from urllib.parse import urlparse

BASE_URL = "https://api.github.com"


def _headers():
    token = os.getenv("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def parse_repo_url(url: str):
    url = url.strip().rstrip("/")
    if not url:
        raise ValueError("Empty repository URL")
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Not a GitHub URL: {url}")
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        owner, repo = parts[0], parts[1]
    else:
        parts = [p for p in url.split("/") if p]
        if len(parts) != 2:
            raise ValueError(f"Invalid repository identifier '{url}'.")
        owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


async def get_default_branch(client, owner, repo):
    resp = await client.get(
        f"{BASE_URL}/repos/{owner}/{repo}",
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["default_branch"]


async def get_file_tree(owner: str, repo: str) -> tuple[list, str]:
    """Returns (tree_items, default_branch)."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        branch = await get_default_branch(client, owner, repo)
        resp = await client.get(
            f"{BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}",
            headers=_headers(),
            params={"recursive": "1"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            item for item in data.get("tree", [])
            if item.get("type") == "blob"
        ], branch


async def get_file_content(owner: str, repo: str, path: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=_headers(),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return ""
        except Exception:
            return ""