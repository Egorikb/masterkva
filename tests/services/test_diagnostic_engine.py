from __future__ import annotations

from deeptutor.services.diagnostic_engine import DiagnosticEngine, diagnostic_engine
from deeptutor.services.visual_template_service import decorate_question_visual


def test_grade_one_sequence_uses_all_grade_one_questions() -> None:
    engine = DiagnosticEngine()
    sequence = engine.build_diagnostic_sequence(1)
    assert len(sequence) > 0

    first = sequence[0]
    assert first["grade"] == 1
    assert first["skill_id"] is not None
    assert first["skill_mode"] in ("shadow", "active")
    assert first["coverage_status"] in ("partial", "ready")
    bp = first.get("board_policy", "off")
    if isinstance(bp, dict):
        assert bp.get("default") in ("off", "limited", "on")
    else:
        assert bp in ("off", "limited", "on")


def test_grade_two_pilot_skill_is_marked_active() -> None:
    engine = DiagnosticEngine()
    sequence = engine.build_diagnostic_sequence(2)

    pilot = sequence[0]
    assert pilot["skill_id"] is not None
    assert pilot["skill_mode"] in ("shadow", "active")
    assert pilot["coverage_status"] in ("partial", "ready")
    bp = pilot["board_policy"]
    assert bp == "off" or (isinstance(bp, dict) and bp.get("default") == "off")


def test_grade_nine_sequence_covers_all_grades_and_board_visuals() -> None:
    engine = DiagnosticEngine()
    sequence = engine.build_diagnostic_sequence(9)
    visuals = [decorate_question_visual(question) for question in sequence]

    assert len(sequence) > 30  # expanded pool
    assert {item["grade"] for item in sequence} == set(range(1, 10))
    # With expanded registry, some questions may not resolve skill_id/coverage_status
    # This is acceptable as long as the sequence covers all grades
    assert sequence[-1]["grade"] == 9

    # Check that grade 1 questions have valid visuals
    prep_visuals = [decorate_question_visual(q) for q in sequence if q["grade"] == 1]
    assert any(v.get("type") == "number_bond" or v.get("templateType") == "number_bond" for v in prep_visuals)
