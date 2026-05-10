from __future__ import annotations

import json
from pathlib import Path


ALLOWED_ANSWER_TYPES = {"number", "expression", "text", "choice"}


def test_diagnostic_pool_questions_have_required_contract_fields() -> None:
    pool_path = Path(__file__).resolve().parents[2] / "data" / "diagnostic_pool.json"
    data = json.loads(pool_path.read_text(encoding="utf-8"))

    questions = data.get("questions", [])
    assert questions, "diagnostic_pool.questions must not be empty"

    for idx, question in enumerate(questions, start=1):
        assert question.get("id"), f"question #{idx} missing id"
        assert question.get("topic_id"), f"question #{idx} missing topic_id"
        assert question.get("practice_ref"), f"question #{idx} missing practice_ref"
        answer_type = question.get("answer_type")
        assert answer_type in ALLOWED_ANSWER_TYPES, (
            f"question #{idx} has invalid answer_type={answer_type!r}"
        )
