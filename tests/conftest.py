from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def isolate_llm_configuration(monkeypatch):
    from deeptutor.services import config

    # Ordinary regression tests must not load personal .env files or spend API credits.
    monkeypatch.setattr(config, "_candidate_env_files", lambda: [])
    monkeypatch.setattr(config, "_DOTENV_LOADED", False)
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")


@pytest.fixture(autouse=True)
def isolate_student_state(tmp_path, monkeypatch):
    from deeptutor.api.routers import plugins_api
    from deeptutor.services import student_profile_store

    state_file = tmp_path / "user_states.json"
    monkeypatch.setattr(plugins_api, "STATE_FILE", state_file)
    monkeypatch.setattr(student_profile_store, "STATE_FILE", state_file)
    return state_file
