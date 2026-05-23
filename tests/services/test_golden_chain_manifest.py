from __future__ import annotations

import json
from pathlib import Path


def test_golden_chain_manifest_matches_registry_and_contracts() -> None:
    base = Path(__file__).resolve().parents[2] / "backend" / "data"
    manifest = json.loads((base / "golden_chains" / "g1_to_g2_addition.json").read_text(encoding="utf-8"))
    registry = json.loads((base / "skill_registry.json").read_text(encoding="utf-8"))
    contracts = json.loads((base / "skill_contracts.json").read_text(encoding="utf-8"))

    registry_by_id = {skill["skill_id"]: skill for skill in registry["skills"]}
    contract_by_skill = {contract["skill_id"]: contract for contract in contracts["contracts"]}

    assert manifest["chain_id"] == "g1_to_g2_addition"
    assert manifest["version"] == "v1"
    assert manifest["baseline_anchor_skill_id"] == "g2_addition_core"
    assert manifest["prerequisite_skill_id"] == "g1_early_arithmetic_core"

    chain_skill_ids = [item["skill_id"] for item in manifest["skills"]]
    assert chain_skill_ids == ["g1_early_arithmetic_core", "g2_addition_core"]

    for item in manifest["skills"]:
        skill_id = item["skill_id"]
        assert skill_id in registry_by_id, f"Missing skill in registry: {skill_id}"
        assert skill_id in contract_by_skill, f"Missing contract for skill: {skill_id}"
        assert registry_by_id[skill_id]["contract_id"] == contract_by_skill[skill_id]["id"]
        assert registry_by_id[skill_id]["contract_id"].startswith(skill_id)
        assert contract_by_skill[skill_id]["coverage"]["status"] == "partial"
        assert contract_by_skill[skill_id]["diagnostic"]["required"] is True
        assert contract_by_skill[skill_id]["remediation"]["required"] is True
        assert contract_by_skill[skill_id]["board_policy"] in {"off", "limited", "on"}
        assert contract_by_skill[skill_id]["visual_policy"]["diagnosis"] == "off"

    assert registry_by_id["g1_early_arithmetic_core"]["next_skills"] == ["g2_addition_core"]
    assert registry_by_id["g2_addition_core"]["prerequisites"] == ["g1_early_arithmetic_core"]
    assert contract_by_skill["g1_early_arithmetic_core"]["mode"] == "shadow"
    assert contract_by_skill["g2_addition_core"]["mode"] == "active"
    assert manifest["promotion_rule"]["owner"] == "backend_state_machine"
    assert manifest["promotion_rule"]["mastery_gate_owner"] == "backend_mastery_evaluator"
    assert manifest["promotion_rule"]["requires_mastery_gate"] is True
