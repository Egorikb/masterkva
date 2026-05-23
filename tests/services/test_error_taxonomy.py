from __future__ import annotations

from deeptutor.services.error_taxonomy import error_taxonomy
from deeptutor.services.report_service import build_report
from deeptutor.services.skill_runtime import skill_resolver


def test_error_taxonomy_uses_item_family_for_g1_remediation() -> None:
    resolution = skill_resolver.resolve(topic_id="g1_t05", topic_name="СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5")
    feedback = {"is_correct": False, "topic_id": "g1_t05", "item_family": "number_bond_missing_part"}
    classification = error_taxonomy.classify_practice_error(
        {"topic_id": "g1_t05", "topic": "СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5", "item_family": "number_bond_missing_part"},
        feedback,
        resolution.contract,
    )

    assert classification["error_code"] == "number_bond_missing_part_error"
    assert classification["error_family"] == "number_bond_missing_part"
    assert classification["item_family"] == "number_bond_missing_part"
    assert classification["remediation_path"] == "number_bond"
    assert classification["taxonomy_source"] == "item_family"
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
