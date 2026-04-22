"""
LLM client abstraction.
Supports OpenAI-compatible APIs and local Ollama models.
Swap backend via LLM_BACKEND env var: "openai" | "local"
"""
import os
import httpx
import asyncio


async def call_llm(prompt: str, max_tokens: int = 8192) -> str:
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
    payload = {
        "model": llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    last_error = None
    async with httpx.AsyncClient(trust_env=False) as client:
        for attempt in range(5):
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=120)

                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]

                # retry on 429, 500, 502, 503, 504
                if resp.status_code in (429, 500, 502, 503, 504):
                    wait = 2 ** attempt  # 1, 2, 4, 8, 16
                    print(f"[LLM] {resp.status_code} — retrying in {wait}s (attempt {attempt+1}/5)")
                    last_error = f"{resp.status_code}: {resp.text[:200]}"
                    await asyncio.sleep(wait)
                    continue

                # non-retryable error
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

            except httpx.TimeoutException:
                wait = 2 ** attempt
                print(f"[LLM] timeout — retrying in {wait}s")
                last_error = "timeout"
                await asyncio.sleep(wait)
                continue

    raise RuntimeError(f"LLM call failed after 5 retries. Last error: {last_error}")


async def _call_local(prompt: str, max_tokens: int) -> str:
    llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
    llm_base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{llm_base_url}/api/generate",
            json={
                "model": llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": max_tokens},
            },
            timeout=300,
        )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()