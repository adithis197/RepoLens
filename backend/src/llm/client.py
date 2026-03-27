"""
LLM client abstraction.
Supports local Qwen2.5-Coder and OpenAI-compatible APIs.
Swap backend via LLM_BACKEND env var: "openai" | "local"
"""
import os
import httpx

LLM_BACKEND = os.getenv("LLM_BACKEND", "openai")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")


async def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send a prompt to the configured LLM and return the raw text response.
    """
    if LLM_BACKEND == "openai":
        return await _call_openai_compatible(prompt, max_tokens)
    elif LLM_BACKEND == "local":
        return await _call_local(prompt, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {LLM_BACKEND}")


async def _call_openai_compatible(prompt: str, max_tokens: int) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_local(prompt: str, max_tokens: int) -> str:
    # TODO: implement local HuggingFace inference
    raise NotImplementedError
