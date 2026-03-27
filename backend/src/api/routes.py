"""
API route definitions.
"""
from fastapi import APIRouter
from .schemas import AnalyzeRequest, AnalyzeResponse
from ..pipeline import run_pipeline

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(req: AnalyzeRequest):
    """
    Main endpoint: accepts a GitHub repo URL and returns
    the architecture diagram + evidence map + repo summary.
    """
    result = await run_pipeline(req.repo_url, req.token_budget)
    return result


@router.get("/health")
def health():
    return {"status": "ok"}
