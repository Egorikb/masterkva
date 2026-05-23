from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SKILL_REGISTRY_FILE = DATA_DIR / "skill_registry.json"
SKILL_CONTRACTS_FILE = DATA_DIR / "skill_contracts.json"
DIAGNOSTIC_POOL_FILE = DATA_DIR / "diagnostic_pool.json"
PRACTICE_ENGINE_FILE = Path(__file__).resolve().parent / "practice_engine.py"


class CoverageReport:
    """Generate coverage report for skills in the registry."""

    def __init__(self) -> None:
        self.registry = self._load_json(SKILL_REGISTRY_FILE)
        self.contracts = self._load_json(SKILL_CONTRACTS_FILE)
        self.diagnostic_pool = self._load_json(DIAGNOSTIC_POOL_FILE)
        self._contract_index = {
            str(c.get("skill_id") or "").strip(): c
            for c in self.contracts.get("contracts", [])
        }
        self._diagnostic_skill_ids: set[str] = set()
        for item in self.diagnostic_pool.get("items", []):
            skill_id = str(item.get("skill_id") or "").strip()
            if skill_id:
                self._diagnostic_skill_ids.add(skill_id)

        # Build topic_id -> skill_id mapping from registry
        self._topic_to_skill: dict[str, str] = {}
        for skill in self.registry.get("skills", []):
            sid = str(skill.get("skill_id") or "").strip()
            for tid in skill.get("topic_ids") or []:
                self._topic_to_skill[str(tid).strip()] = sid

        # Also index diagnostic pool items by topic_id
        self._diagnostic_topic_ids: set[str] = set()
        for item in self.diagnostic_pool.get("items", []):
            tid = str(item.get("topic_id") or "").strip()
            if tid:
                self._diagnostic_topic_ids.add(tid)
                # Map topic_id -> skill_id
                skill_id = self._topic_to_skill.get(tid, "")
                if skill_id:
                    self._diagnostic_skill_ids.add(skill_id)

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def check_skill(self, skill_id: str) -> dict[str, Any]:
        """Check coverage for a single skill."""
        skill = None
        for s in self.registry.get("skills", []):
            if str(s.get("skill_id") or "").strip() == skill_id:
                skill = s
                break

        if not skill:
            return {"skill_id": skill_id, "error": "missing_from_registry"}

        contract = self._contract_index.get(skill_id, {})
        validation = contract.get("validation", {})

        checks: dict[str, Any] = {
            "skill_id": skill_id,
            "grade": skill.get("grade"),
            "mode": contract.get("mode", "missing"),
            "coverage": {},
            "warnings": [],
            "blocking_gaps": [],
        }

        # Check contract exists
        if not contract:
            checks["blocking_gaps"].append("missing_contract")
            return checks

        # Check validation sections
        required_sections = list(validation.get("required_sections") or [])
        for section in required_sections:
            has_section = section in contract and contract[section]
            checks["coverage"][section] = "present" if has_section else "missing"
            if not has_section:
                checks["blocking_gaps"].append(f"missing_section:{section}")

        # Check diagnostic coverage
        has_diagnostic = bool(contract.get("diagnostic", {}))
        has_diagnostic_items = bool(
            contract.get("diagnostic", {}).get("item_types")
            or contract.get("diagnostic", {}).get("item_families")
        )
        checks["coverage"]["diagnostic_shape"] = (
            "complete" if (has_diagnostic and has_diagnostic_items) else "incomplete"
        )
        if not has_diagnostic:
            checks["blocking_gaps"].append("missing_diagnostic")
        elif not has_diagnostic_items:
            checks["warnings"].append("diagnostic_shape_incomplete")

        # Check error model
        has_error_model = bool(contract.get("error_model", {}))
        checks["coverage"]["error_model"] = "present" if has_error_model else "missing"
        if not has_error_model:
            checks["warnings"].append("missing_error_model")

        # Check remediation
        has_remediation = bool(contract.get("remediation", {}))
        checks["coverage"]["remediation"] = "present" if has_remediation else "missing"
        if not has_remediation:
            checks["blocking_gaps"].append("missing_remediation")

        # Check visual policy
        has_visual = bool(contract.get("visual_policy", {}))
        checks["coverage"]["visual_policy"] = "present" if has_visual else "missing"
        if not has_visual:
            checks["warnings"].append("missing_visual_policy")

        # Check board policy
        board_policy = str(contract.get("board_policy") or "").strip()
        checks["coverage"]["board_policy"] = board_policy if board_policy else "missing"
        if not board_policy:
            checks["warnings"].append("missing_board_policy")

        # Check mastery gate
        has_mastery_gate = bool(contract.get("mastery_gate", {}))
        checks["coverage"]["mastery_gate"] = "present" if has_mastery_gate else "missing"
        if not has_mastery_gate:
            checks["blocking_gaps"].append("missing_mastery_gate")

        # Check diagnostic pool items
        has_pool_items = skill_id in self._diagnostic_skill_ids
        checks["coverage"]["diagnostic_pool"] = "present" if has_pool_items else "missing"
        if not has_pool_items:
            checks["warnings"].append("no_diagnostic_pool_items")

        # Check prerequisites
        prerequisites = list(skill.get("prerequisites") or [])
        next_skills = list(skill.get("next_skills") or [])
        checks["coverage"]["prerequisites"] = prerequisites
        checks["coverage"]["next_skills"] = next_skills

        # Active gate: if mode is active, coverage must not have blocking gaps
        if contract.get("mode") == "active" and checks["blocking_gaps"]:
            checks["warnings"].append(
                f"active_skill_has_blocking_gaps: {', '.join(checks['blocking_gaps'])}"
            )

        # Overall status
        if checks["blocking_gaps"]:
            checks["status"] = "incomplete"
        elif checks["warnings"]:
            checks["status"] = "partial"
        else:
            checks["status"] = "complete"

        return checks

    def run(self) -> dict[str, Any]:
        """Run coverage check for all skills in registry."""
        results = []
        blocking_gaps: dict[str, list[str]] = {}
        incomplete_skills: list[str] = []
        active_with_gaps: list[str] = []

        for skill in self.registry.get("skills", []):
            skill_id = str(skill.get("skill_id") or "").strip()
            if not skill_id:
                continue
            report = self.check_skill(skill_id)
            results.append(report)

            if report.get("status") == "incomplete":
                incomplete_skills.append(skill_id)
                blocking_gaps[skill_id] = report.get("blocking_gaps", [])

            if report.get("mode") == "active" and report.get("blocking_gaps"):
                active_with_gaps.append(skill_id)

        return {
            "total_skills": len(results),
            "complete": sum(1 for r in results if r.get("status") == "complete"),
            "partial": sum(1 for r in results if r.get("status") == "partial"),
            "incomplete": sum(1 for r in results if r.get("status") == "incomplete"),
            "incomplete_skills": incomplete_skills,
            "blocking_gaps": blocking_gaps,
            "active_with_gaps": active_with_gaps,
            "skills": results,
        }


def run_coverage() -> dict[str, Any]:
    """Entry point for coverage-run."""
    reporter = CoverageReport()
    return reporter.run()
