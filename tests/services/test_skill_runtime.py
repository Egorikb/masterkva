from __future__ import annotations

from deeptutor.services.skill_runtime import skill_resolver


def test_skill_resolver_marks_g2_addition_core_active() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_t01", topic_name="Сложение двузначных чисел")

    assert resolution.skill_id == "g2_addition_core"
    assert resolution.source == "registry"
    assert resolution.mode == "active"
    assert resolution.contract.get("mode") == "active"


def test_skill_resolver_keeps_g1_shadow() -> None:
    resolution = skill_resolver.resolve(topic_id="g1_t02", topic_name="Следующее число")

    assert resolution.skill_id == "g1_early_arithmetic_core"
    assert resolution.source == "registry"
    assert resolution.mode == "shadow"
    assert resolution.contract.get("mode") == "shadow"
