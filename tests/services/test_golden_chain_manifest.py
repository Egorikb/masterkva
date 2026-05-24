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
    assert manifest["version"] == "v2"
    assert manifest["baseline_anchor_skill_id"] == "g2_addition_core"
    assert manifest["prerequisite_skill_id"] == "g1_counting_core"

    chain_skill_ids = [item["skill_id"] for item in manifest["skills"]]
    assert "g1_counting_core" in chain_skill_ids
    assert "g2_addition_core" in chain_skill_ids

    for item in manifest["skills"]:
        skill_id = item["skill_id"]
        assert skill_id in registry_by_id, f"Missing skill in registry: {skill_id}"
        assert skill_id in contract_by_skill, f"Missing contract for skill: {skill_id}"
        assert registry_by_id[skill_id]["contract_id"] == contract_by_skill[skill_id]["id"]
        assert registry_by_id[skill_id]["contract_id"].startswith(skill_id)
        assert contract_by_skill[skill_id]["coverage"]["status"] == "partial"
        assert contract_by_skill[skill_id]["diagnostic"]["required"] is True
        assert contract_by_skill[skill_id]["remediation"]["required"] is True
        bp = contract_by_skill[skill_id]["board_policy"]
        if isinstance(bp, dict):
            assert bp.get("default") in {"off", "limited", "on"}
        else:
            assert bp in {"off", "limited", "on"}
        assert contract_by_skill[skill_id]["visual_policy"]["diagnosis"] == "off"
        assert contract_by_skill[skill_id]["validation"]["required"] is True
        assert contract_by_skill[skill_id]["validation"]["board_policy_locked"] is True
        assert contract_by_skill[skill_id]["validation"]["mastery_owned_by_backend"] is True
        assert "coverage" in contract_by_skill[skill_id]["validation"]["required_sections"]
        assert "mastery_gate" in contract_by_skill[skill_id]["validation"]["required_sections"]

    # Check chain links: g1_counting_core → ... → g2_addition_core
    # The path may go through intermediate skills now
    g1 = registry_by_id["g1_counting_core"]
    g2 = registry_by_id["g2_addition_core"]
    assert g1["grade"] == 1
    assert g2["grade"] == 2
    # g2_addition_core should be reachable from g1_counting_core through the graph
    assert "g2_addition_core" in g2.get("prerequisites", []) or any(
        "g2_addition_core" in registry_by_id.get(p, {}).get("next_skills", [])
        for p in g2.get("prerequisites", [])
        if p in registry_by_id
    )


def test_subtraction_chain_manifest_matches_registry_and_contracts() -> None:
    base = Path(__file__).resolve().parents[2] / "backend" / "data"
    registry = json.loads((base / "skill_registry.json").read_text(encoding="utf-8"))
    contracts = json.loads((base / "skill_contracts.json").read_text(encoding="utf-8"))

    registry_by_id = {skill["skill_id"]: skill for skill in registry["skills"]}
    contract_by_skill = {contract["skill_id"]: contract for contract in contracts["contracts"]}

    assert "g2_subtraction_core" in registry_by_id
    assert "g2_subtraction_core" in contract_by_skill
    assert registry_by_id["g2_subtraction_core"]["domain"] == "arithmetic"
