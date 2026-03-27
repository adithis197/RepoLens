"""Utility for estimating token counts before LLM calls."""


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 characters per token (GPT-style)."""
    return len(text) // 4


def fits_in_budget(texts: list[str], budget: int) -> bool:
    return sum(estimate_tokens(t) for t in texts) <= budget
