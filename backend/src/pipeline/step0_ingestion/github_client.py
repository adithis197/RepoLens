import os
import base64
import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def parse_repo_url(url: str):
    """Extract (owner, repo) from a GitHub URL."""
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]


async def get_file_tree(owner: str, repo: str) -> list:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(
            f"{BASE_URL}/repos/{owner}/{repo}/git/trees/HEAD",
            headers=_headers(),
            params={"recursive": "1"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            item for item in data.get("tree", [])
            if item.get("type") == "blob"
        ]


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