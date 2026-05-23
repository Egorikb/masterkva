from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SKILL_REGISTRY_FILE = DATA_DIR / "skill_registry.json"
SKILL_CONTRACTS_FILE = DATA_DIR / "skill_contracts.json"


@dataclass(slots=True)
class SkillResolution:
    skill_id: str | None
    skill_version: str | None
    topic_id: str | None
    lesson_id: str | None
    contract: dict[str, Any]
    source: str
    mode: str
    warnings: list[str]


class SkillResolver:
    def __init__(self) -> None:
        self.registry = self._load_json(SKILL_REGISTRY_FILE, default={"version": "v1", "mode": "shadow", "skills": []})
        self.contracts = self._load_json(SKILL_CONTRACTS_FILE, default={"version": "v1", "contracts": []})
        self._contract_index = self._build_contract_index()
        self._topic_index = self._build_topic_index()

    @staticmethod
    def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return default

    @staticmethod
    def _norm(value: str | None) -> str:
        return " ".join(str(value or "").strip().upper().split())

    def _build_contract_index(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for contract in list(self.contracts.get("contracts", [])):
            contract_id = str(contract.get("id") or "").strip()
            skill_id = str(contract.get("skill_id") or "").strip()
            if contract_id:
                index[contract_id] = contract
            if skill_id and skill_id not in index:
                index[skill_id] = contract
        return index

    def _build_topic_index(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for skill in list(self.registry.get("skills", [])):
            skill_id = str(skill.get("skill_id") or "").strip()
            if not skill_id:
                continue
            contract_id = str(skill.get("contract_id") or skill_id).strip()
            contract = self._contract_index.get(contract_id) or self._contract_index.get(skill_id) or {}
            entry = {**skill, "contract": contract}
            index[self._norm(skill_id)] = entry
            for topic_id in skill.get("topic_ids") or []:
                index.setdefault(self._norm(str(topic_id)), entry)
            for topic_name in skill.get("topic_names") or []:
                index.setdefault(self._norm(str(topic_name)), entry)
        return index

    def resolve(self, *, topic_id: str | None = None, topic_name: str | None = None, lesson_id: str | None = None) -> SkillResolution:
        warnings: list[str] = []
        lookup_keys = [self._norm(topic_id), self._norm(topic_name), self._norm(lesson_id)]
        skill = None
        for key in lookup_keys:
            if key:
                skill = self._topic_index.get(key)
                if skill:
                    break
        if not skill:
            warnings.append("fallback_used")
            return SkillResolution(
                skill_id=None,
                skill_version=self.registry.get("version", "v1"),
                topic_id=topic_id,
                lesson_id=lesson_id,
                contract={},
                source="fallback",
                mode="shadow",
                warnings=warnings,
            )

        contract = dict(skill.get("contract") or {})
        mode = str(contract.get("mode") or skill.get("mode") or self.registry.get("mode", "shadow")).strip().lower()
        if mode not in {"shadow", "active"}:
            mode = "shadow"
        return SkillResolution(
            skill_id=str(skill.get("skill_id") or "") or None,
            skill_version=str(contract.get("version") or skill.get("version") or self.registry.get("version", "v1")),
            topic_id=topic_id or (skill.get("topic_ids") or [None])[0],
            lesson_id=lesson_id,
            contract=contract,
            source="registry",
            mode=mode,
            warnings=warnings,
        )

    def apply_board_policy(self, resolution: SkillResolution, default: str = "off") -> str:
        board_policy = str(resolution.contract.get("board_policy") or default).strip().lower()
        if board_policy in {"off", "limited", "on"}:
            return board_policy
        visual_policy = resolution.contract.get("visual_policy") or {}
        visual_mode = str(visual_policy.get("learning") or "").strip().lower()
        if visual_mode == "on":
            return "on"
        if visual_mode == "limited":
            return "limited"
        return default

    def skill_summary(self, resolution: SkillResolution) -> dict[str, Any]:
        return {
            "skill_id": resolution.skill_id,
            "skill_version": resolution.skill_version,
            "source": resolution.source,
            "mode": resolution.mode,
            "topic_id": resolution.topic_id,
            "lesson_id": resolution.lesson_id,
            "warnings": list(resolution.warnings),
            "contract_summary": {
                "coverage_status": (resolution.contract.get("coverage") or {}).get("status") or resolution.contract.get("coverage_status") or "partial",
                "board_policy": resolution.contract.get("board_policy") or "off",
                "mastery_gate": dict(resolution.contract.get("mastery_gate") or {}),
                "visual_template": (resolution.contract.get("visual_policy") or {}).get("template"),
                "mode": resolution.mode,
            },
        }


skill_resolver = SkillResolver()
