"""Tests for Step 2B: hybrid retrieval scoring."""
from src.pipeline.step2b_retrieval.retrieval import _estimate_tokens, _bm25_score
from src.pipeline.step0_ingestion.ingestion import FileNode


def test_estimate_tokens():
    assert _estimate_tokens("a" * 400) == 100


def test_bm25_score_returns_dict():
    files = [
        FileNode(path="src/auth/login.py", extension=".py", size_bytes=100, content="x"),
        FileNode(path="src/payments/checkout.py", extension=".py", size_bytes=100, content="x"),
    ]
    scores = _bm25_score(files, ["auth", "login"])
    assert isinstance(scores, dict)
    assert len(scores) == 2
