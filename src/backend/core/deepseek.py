"""DeepSeek API 全功能 SDK：同步/流式/重试/速率限制。"""
import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from .config import settings

# === 速率限制：简单 token bucket ===
class RateLimiter:
    def __init__(self, rpm: int = 30):
        self.rpm = rpm
        self._last_call = 0.0

    async def wait(self):
        now = time.monotonic()
        min_interval = 60.0 / self.rpm
        wait_time = min_interval - (now - self._last_call)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._last_call = time.monotonic()

rate_limiter = RateLimiter(rpm=30)


# === 客户端工厂 ===
def get_deepseek_client(timeout: float = 120.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.deepseek_base_url,
        headers={
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(timeout),
    )


# === 同步调用 ===
async def deepseek_chat(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    max_retries: int = 3,
    stream: bool = False,
) -> Dict[str, Any]:
    """通用 DeepSeek Chat Completions 调用（同步或流式）。"""

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }

    await rate_limiter.wait()

    last_error = None

    for attempt in range(max_retries):
        client = get_deepseek_client()
        try:
            response = await client.post("/v1/chat/completions", json=payload)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            continue
        except httpx.RequestError as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            continue
        finally:
            await client.aclose()

    raise RuntimeError(f"DeepSeek API failed after {max_retries} retries. Last error: {last_error}")


# === 流式调用 ===
async def deepseek_chat_stream(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> AsyncGenerator[str, None]:
    """流式 DeepSeek Chat Completions，逐 token yield delta content。"""

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    await rate_limiter.wait()

    last_error = None

    for attempt in range(max_retries):
        client = get_deepseek_client(timeout=300.0)
        try:
            async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                return  # Stream ended without [DONE] — treat as success
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        finally:
            await client.aclose()

    raise RuntimeError(f"DeepSeek stream failed after {max_retries} retries. Last error: {last_error}")


# === JSON 模式调用 ===
async def deepseek_chat_json(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """调用 DeepSeek 并强制解析 JSON 响应。"""

    result = await deepseek_chat(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        stream=False,
    )

    content = result["choices"][0]["message"]["content"]

    # 尝试提取 JSON 块
    content = content.strip()
    if content.startswith("```"):
        # 去掉 markdown 代码块标记
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"DeepSeek 返回内容无法解析为 JSON: {content[:200]}")
