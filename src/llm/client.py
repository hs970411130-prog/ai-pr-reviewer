"""LLM 客户端 — OpenAI 兼容协议，对接 DeepSeek。

统一管理 LLM 调用和 Prompt 加载。
"""

import logging
from pathlib import Path

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config.settings import (
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    """读取 prompts/<name>.md 文件内容。"""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {path}")
    return path.read_text(encoding="utf-8")


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """延迟初始化 LLM 客户端（单例）。"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_API_BASE,
            timeout=60.0,
        )
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
def chat(prompt: str, system: str = "") -> str:
    """发送请求到 LLM，返回文本响应。网络错误自动重试最多 3 次。"""
    client = _get_client()
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        content = getattr(resp.choices[0].message, "content", "")
        return content or ""
    except IndexError:
        logger.warning("LLM 返回空 choices")
        return ""
