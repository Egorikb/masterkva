from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str


def get_llm_config() -> LLMConfig:
    provider = os.getenv("LLM_BINDING") or os.getenv("OPENAI_BINDING") or "openai"
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base_url = os.getenv("LLM_HOST") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    return LLMConfig(provider=provider, model=model, api_key=api_key, base_url=base_url)
