from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from deeptutor.services.skill_runtime import SkillResolver, skill_resolver


def _load_data():
    base = Path(__file__).resolve().parents[2] / "backend" / "data"
    registry = json.loads((base / "skill_registry.json").read_text(encoding="utf-8"))
    contracts = json.loads((base / "skill_contracts.json").read_text(encoding="utf-8"))
    return registry, contracts


def test_skill_resolver_marks_g2_addition_core_active() -> None:
    resolver = SkillResolver()
    resolution = resolver.resolve(topic_id="g2_addition_core")
    assert resolution.skill_id == "g2_addition_core"
    assert resolution.contract is not None


def test_skill_summary_exposes_validation_contract_layer() -> None:
    resolver = SkillResolver()
    resolution = resolver.resolve(topic_id="g2_addition_core")
    summary = resolver.skill_summary(resolution)
    contract_summary = summary["contract_summary"]
    assert contract_summary["validation"]["required"] is True
    assert contract_summary["validation"]["board_policy_locked"] is True
    assert contract_summary["validation"]["mastery_owned_by_backend"] is True


def test_skill_resolver_keeps_g1_shadow() -> None:
    resolver = SkillResolver()
    resolution = resolver.resolve(topic_id="g1_counting_core")
    assert resolution.skill_id == "g1_counting_core"
    assert resolution.mode == "shadow"


def test_apply_board_policy_for_phase() -> None:
    resolver = SkillResolver()
    resolution = resolver.resolve(topic_id="g2_addition_core")
    assert resolver.apply_board_policy_for_phase(resolution, "diagnostic") == "off"
    assert resolver.apply_board_policy_for_phase(resolution, "learning") == "on"
    assert resolver.apply_board_policy_for_phase(resolution, "remediation") == "limited"
