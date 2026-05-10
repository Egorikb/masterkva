from __future__ import annotations

from pathlib import Path


def test_panda_chat_has_no_legacy_code_after_final_return_marker() -> None:
    source = Path("deeptutor/api/routers/plugins_api.py").read_text(encoding="utf-8")
    assert "# === NEW USER WITH GRADE, ASK FOR PATH ===" not in source
