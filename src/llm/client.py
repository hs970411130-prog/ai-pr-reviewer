"""LLM 客户端 — OpenAI 兼容协议，对接 DeepSeek。

统一管理 LLM 调用和 Prompt 加载。
"""

from pathlib import Path

from openai import OpenAI

from src.config.settings import (
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

# Prompt 文件在 client.py 同级 prompts/ 目录下
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
        )
    return _client


def chat(prompt: str, system: str = "") -> str:
    """发送请求到 LLM，返回文本响应。"""
    client = _get_client()
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )
    return resp.choices[0].message.content or ""
