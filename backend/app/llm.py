"""LLM Provider 抽象层。

支持 OpenAI / Anthropic / DeepSeek / 本地(OpenAI 兼容) / none(规则降级)。
设计目标：无 API Key 时系统仍可用 —— 各 Agent 先尝试 LLM，失败或未配置则
回退到确定性规则实现，保证离线可跑、可测试。

所有 Agent 通过 `LLMClient.complete_json(prompt, schema_hint)` 获取结构化结果。
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from .config import get_settings

settings = get_settings()

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "deepseek": "deepseek-chat",
    "local": "local-model",
}
_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "local": "http://localhost:11434/v1",  # Ollama OpenAI 兼容
}


class LLMClient:
    def __init__(self) -> None:
        self.provider = (settings.llm_provider or "none").lower()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model or _DEFAULT_MODELS.get(self.provider, "")
        self.base_url = settings.llm_base_url or _DEFAULT_BASE_URLS.get(self.provider, "")
        self.temperature = settings.llm_temperature

    @property
    def available(self) -> bool:
        """是否配置了可用的真实 LLM。"""
        if self.provider in ("", "none"):
            return False
        if self.provider == "local":
            return bool(self.base_url)
        return bool(self.api_key)

    # ---------- 统一入口 ----------
    def complete(self, prompt: str, system: str = "") -> Optional[str]:
        if not self.available:
            return None
        try:
            if self.provider == "anthropic":
                return self._anthropic(prompt, system)
            return self._openai_compatible(prompt, system)
        except Exception:
            return None  # 任何失败都回退规则实现

    def complete_json(self, prompt: str, system: str = "") -> Optional[dict[str, Any]]:
        """请求 LLM 返回 JSON；失败返回 None，由调用方回退规则。"""
        text = self.complete(prompt + "\n\n只输出合法 JSON，不要任何解释。", system)
        if not text:
            return None
        return _extract_json(text)

    # ---------- Provider 实现 ----------
    def _openai_compatible(self, prompt: str, system: str) -> Optional[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    def _anthropic(self, prompt: str, system: str) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": self.temperature,
            "system": system or "You are a helpful assistant.",
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json().get("content", []))


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    """从 LLM 输出中稳健提取第一个 JSON 对象。"""
    if not text:
        return None
    # 去掉 ```json 围栏
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fence.group(1) if fence else None
    if not candidate:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except Exception:
        return None


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
