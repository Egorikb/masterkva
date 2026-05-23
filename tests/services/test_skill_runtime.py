from __future__ import annotations

from deeptutor.services.skill_runtime import skill_resolver


def test_skill_resolver_marks_g2_addition_core_active() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")

    assert resolution.skill_id == "g2_addition_core"
    assert resolution.source == "registry"
    assert resolution.mode == "active"
    assert resolution.next_skills == ["g3_time_measurement_core"]
    assert resolution.contract.get("mode") == "active"


def test_skill_summary_exposes_validation_contract_layer() -> None:
    resolution = skill_resolver.resolve(topic_id="g1_t05", topic_name="СЛОЖЕНИЕ И ВЫЧИТАНИЕ ДО 5")
    summary = skill_resolver.skill_summary(resolution)

    assert summary["contract_summary"]["validation"]["required"] is True
    assert summary["contract_summary"]["validation"]["board_policy_locked"] is True
    assert summary["contract_summary"]["validation"]["mastery_owned_by_backend"] is True
    assert "coverage" in summary["contract_summary"]["validation"]["required_sections"]
    assert summary["contract_summary"]["remediation_default_path"] == "number_bond"
    assert summary["contract_summary"]["remediation_targets"]["number_bond_missing_part"] == "number_bond"
    assert "number_bond_missing_part" in summary["contract_summary"]["diagnostic_item_families"]


def test_skill_resolver_keeps_g1_shadow() -> None:
    resolution = skill_resolver.resolve(topic_id="g1_t02", topic_name="Следующее число")

    assert resolution.skill_id == "g1_early_arithmetic_core"
    assert resolution.source == "registry"
    assert resolution.mode == "shadow"
    assert resolution.contract.get("mode") == "shadow"
