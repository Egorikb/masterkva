from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str


_DOTENV_LOADED = False


def _candidate_env_files() -> list[Path]:
    project_root = Path(__file__).resolve().parents[3]
    return [
        project_root / ".env",
        Path.home() / ".hermes" / ".env",
    ]


def _load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("export "):
                if line.startswith("export "):
                    line = line[len("export "):].strip()
                else:
                    continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


def _load_dotenv_defaults() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    for path in _candidate_env_files():
        _load_env_file(path)
    _DOTENV_LOADED = True


def get_llm_config() -> LLMConfig:
    _load_dotenv_defaults()
    provider = os.getenv("LLM_BINDING") or os.getenv("OPENAI_BINDING") or "openai"
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base_url = os.getenv("LLM_HOST") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    return LLMConfig(provider=provider, model=model, api_key=api_key, base_url=base_url)
