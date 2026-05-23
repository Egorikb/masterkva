from __future__ import annotations

from deeptutor.services.error_taxonomy import error_taxonomy
from deeptutor.services.report_service import build_report
from deeptutor.services.skill_runtime import skill_resolver


def test_error_taxonomy_maps_g2_addition_to_place_value_error() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")
    feedback = {"is_correct": False, "topic_id": "g2_t01"}
    classification = error_taxonomy.classify_practice_error(
        {"topic_id": "g2_t01", "topic": "Сложение двузначных чисел"},
        feedback,
        resolution.contract,
    )

    assert classification["error_code"] == "place_value_error"
    assert classification["error_family"] == "place_value"
    assert classification["remediation_path"] == "base_ten_blocks"
    assert classification["taxonomy_source"] in {"topic_map", "contract"}


def test_report_includes_error_code_and_remediation_path_when_wrong() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")
    report = build_report(
        {"topic_id": "g2_t01", "topic": "Сложение двузначных чисел"},
        {"is_correct": False, "topic_id": "g2_t01"},
    )

    assert report["practice_result"] == "needs_review"
    assert report["error_code"] == "place_value_error"
    assert report["remediation_path"] == "slow_step_by_step"
    assert report["recommendations"]
