from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from deeptutor.services.coverage_runner import CoverageReport, run_coverage


def test_coverage_runner_returns_structure() -> None:
    report = run_coverage()
    assert "total_skills" in report
    assert "complete" in report
    assert "partial" in report
    assert "incomplete" in report
    assert "incomplete_skills" in report
    assert "blocking_gaps" in report
    assert "active_with_gaps" in report
    assert "skills" in report
    assert report["total_skills"] > 0


def test_coverage_runner_golden_chain_checks() -> None:
    report = run_coverage()
    skill_ids = [s["skill_id"] for s in report["skills"]]

    # Golden chain skills must be present
    assert "g1_early_arithmetic_core" in skill_ids
    assert "g2_addition_core" in skill_ids


def test_coverage_runner_detects_missing_contract(tmp_path) -> None:
    """Skill without contract should be flagged as incomplete."""
    registry = {
        "version": "v1",
        "mode": "shadow",
        "skills": [
            {
                "skill_id": "test_no_contract",
                "grade": 1,
                "domain": "test",
                "topic_ids": ["test_t01"],
                "topic_names": ["Test"],
                "prerequisites": [],
                "next_skills": [],
                "contract_id": "test_no_contract.v1",
            }
        ],
    }
    contracts = {"version": "v1", "contracts": []}
    diag_pool = {"items": []}

    with patch.object(CoverageReport, "_load_json") as mock_load:
        mock_load.side_effect = lambda path: {
            "skill_registry.json": registry,
            "skill_contracts.json": contracts,
            "diagnostic_pool.json": diag_pool,
        }.get(path.name, {})

        report = run_coverage()
        skills = {s["skill_id"]: s for s in report["skills"]}
        assert "test_no_contract" in skills
        assert "missing_contract" in skills["test_no_contract"]["blocking_gaps"]


def test_coverage_runner_active_with_gaps_warns() -> None:
    """Active skill with blocking gaps should warn."""
    registry = {
        "version": "v1",
        "mode": "shadow",
        "skills": [
            {
                "skill_id": "test_active_gap",
                "grade": 1,
                "domain": "test",
                "topic_ids": ["test_t01"],
                "topic_names": ["Test"],
                "prerequisites": [],
                "next_skills": [],
                "contract_id": "test_active_gap.v1",
            }
        ],
    }
    contracts = {
        "version": "v1",
        "contracts": [
            {
                "id": "test_active_gap.v1",
                "skill_id": "test_active_gap",
                "coverage": {"status": "partial"},
                "diagnostic": {"required": True, "item_types": ["numeric"]},
                "mode": "active",
                "validation": {
                    "required": True,
                    "required_sections": ["coverage"],
                },
            }
        ],
    }
    diag_pool = {"items": []}

    with patch.object(CoverageReport, "_load_json") as mock_load:
        mock_load.side_effect = lambda path: {
            "skill_registry.json": registry,
            "skill_contracts.json": contracts,
            "diagnostic_pool.json": diag_pool,
        }.get(path.name, {})

        report = run_coverage()
        skills = {s["skill_id"]: s for s in report["skills"]}
        assert "test_active_gap" in skills
        # Active skill with blocking gaps should be in active_with_gaps
        assert "test_active_gap" in report["active_with_gaps"]
