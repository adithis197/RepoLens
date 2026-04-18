"""
LLM client abstraction.
Supports OpenAI-compatible APIs and local Ollama models.
Swap backend via LLM_BACKEND env var: "openai" | "local"
"""
import os
import httpx


async def call_llm(prompt: str, max_tokens: int = 4096) -> str:
    """
    Send a prompt to the configured LLM and return the raw text response.
    """
    llm_backend = os.getenv("LLM_BACKEND", "openai")

    if llm_backend == "openai":
        return await _call_openai_compatible(prompt, max_tokens)
    elif llm_backend == "local":
        return await _call_local(prompt, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {llm_backend}")


async def _call_openai_compatible(prompt: str, max_tokens: int) -> str:
    llm_api_key = os.getenv("LLM_API_KEY", "")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")

    url = f"{llm_base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(
            url,
            headers=headers,
            json={
                "model": llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            },
            timeout=60,
        )

    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def _call_local(prompt: str, max_tokens: int) -> str:
    """
    Call a local Ollama model.
    """
    llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
    llm_base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{llm_base_url}/api/generate",
            json={
                "model": llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": max_tokens,
                },
            },
            timeout=300,
        )

    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()
