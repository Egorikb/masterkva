from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from deeptutor.services.visual_template_service import CANONICAL_VISUAL_TYPES

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

LEGACY_SKILL_IDS = {"g1_early_arithmetic_core", "g5_rational_numbers"}

TEACHER_ONLY_RE = re.compile(
    "|".join(
        re.escape(pattern)
        for pattern in (
            "Для темы",
            "Если ребён",
            "Если ученик",
            "Если шаг",
            "Попроси ребёнка",
            "Попроси ученика",
            "дай ему",
            "Дай ему",
            "Используй опору",
            "После ответа",
            "Закрепи правило",
            "Схема нужна",
            "Сначала сделай",
            "Попроси объяснить",
        )
    ),
    re.IGNORECASE,
)

DUPLICATE_INSTRUCTION_PHRASES = (
    "Сначала реши по шагам, потом кратко объясни ход решения.",
    "Сначала запиши ход решения, затем кратко проверь, почему он верен.",
    "Сначала покажи решение на черновике, потом объясни логику словами.",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _topic_key(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


class MaterialQA:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self.issues: list[dict[str, str]] = []

    def _issue(self, severity: str, code: str, path: Path, message: str) -> None:
        self.issues.append(
            {
                "severity": severity,
                "code": code,
                "path": str(path.relative_to(self.data_dir)),
                "message": message,
            }
        )

    def run(self) -> dict[str, Any]:
        registry = _load_json(self.data_dir / "skill_registry.json")
        contracts = _load_json(self.data_dir / "skill_contracts.json")
        diagnostic_pool = _load_json(self.data_dir / "diagnostic_pool.json")

        self._check_legacy_ids()
        self._check_canonical_curriculum()
        self._check_skill_graph(registry)
        self._check_diagnostic_alignment(registry, contracts, diagnostic_pool)
        self._check_contract_visuals(contracts)
        self._check_visual_topic_map()
        self._check_lessons()
        self._check_detailed_curriculum()
        self._check_golden_chains(registry, contracts)

        blocking = [issue for issue in self.issues if issue["severity"] == "error"]
        return {
            "ok": not blocking,
            "summary": {
                "errors": len(blocking),
                "warnings": sum(1 for issue in self.issues if issue["severity"] == "warning"),
                "issues": len(self.issues),
            },
            "issues": self.issues,
        }

    def _check_legacy_ids(self) -> None:
        for path in self.data_dir.rglob("*.json"):
            text = path.read_text(encoding="utf-8")
            for legacy_id in LEGACY_SKILL_IDS:
                if legacy_id in text:
                    self._issue("error", "legacy_skill_id", path, f"Legacy skill id is still present: {legacy_id}")

    def _check_canonical_curriculum(self) -> None:
        manifest_path = self.data_dir / "curriculum" / "canonical_curriculum.json"
        if not manifest_path.exists():
            self._issue("error", "missing_canonical_curriculum", manifest_path, "Canonical curriculum manifest is missing")
            return
        manifest = _load_json(manifest_path)
        grades = manifest.get("grades") if isinstance(manifest, dict) else None
        if not isinstance(grades, dict):
            self._issue("error", "invalid_canonical_curriculum", manifest_path, "Manifest must contain a grades map")
            return
        for grade in range(1, 10):
            file_name = grades.get(str(grade))
            if not file_name:
                self._issue("error", "missing_canonical_grade", manifest_path, f"Missing canonical file for grade {grade}")
                continue
            path = self.data_dir / "curriculum" / str(file_name)
            if not path.exists():
                self._issue("error", "missing_canonical_file", path, f"Canonical file for grade {grade} does not exist")

    def _check_skill_graph(self, registry: dict[str, Any]) -> None:
        path = self.data_dir / "skill_registry.json"
        skills = list(registry.get("skills") or [])
        skill_ids = {str(skill.get("skill_id")) for skill in skills}
        for skill in skills:
            skill_id = str(skill.get("skill_id") or "")
            for field in ("prerequisites", "next_skills"):
                for ref in skill.get(field) or []:
                    if ref not in skill_ids:
                        self._issue("error", "dangling_skill_ref", path, f"{skill_id}.{field} references missing skill {ref}")

    def _check_diagnostic_alignment(
        self,
        registry: dict[str, Any],
        contracts: dict[str, Any],
        diagnostic_pool: dict[str, Any],
    ) -> None:
        diagnostic_path = self.data_dir / "diagnostic_pool.json"
        contract_path = self.data_dir / "skill_contracts.json"
        questions = list(diagnostic_pool.get("questions") or [])
        registry_topics: dict[str, str] = {}
        topic_families: dict[str, set[str]] = {}
        for skill in registry.get("skills") or []:
            skill_id = str(skill.get("skill_id") or "")
            for topic_id in skill.get("topic_ids") or []:
                registry_topics[str(topic_id)] = skill_id
                topic_families.setdefault(str(topic_id), set())

        for item in questions:
            topic_id = str(item.get("topic_id") or "")
            if topic_id not in registry_topics:
                self._issue("error", "diagnostic_topic_not_in_registry", diagnostic_path, f"Diagnostic topic is not in registry: {topic_id}")
                continue
            family = str(item.get("item_family") or "")
            if family:
                topic_families.setdefault(topic_id, set()).add(family)

        diagnostic_topics = {str(item.get("topic_id") or "") for item in questions}
        for topic_id in registry_topics:
            if topic_id not in diagnostic_topics:
                self._issue("error", "registry_topic_without_diagnostic", diagnostic_path, f"Registry topic has no diagnostic questions: {topic_id}")

        families_by_skill: dict[str, set[str]] = {}
        for topic_id, skill_id in registry_topics.items():
            families_by_skill.setdefault(skill_id, set()).update(topic_families.get(topic_id, set()))

        for contract in contracts.get("contracts") or []:
            skill_id = str(contract.get("skill_id") or "")
            expected = sorted(families_by_skill.get(skill_id, set()))
            actual = sorted((contract.get("diagnostic") or {}).get("item_families") or [])
            if expected != actual:
                self._issue(
                    "error",
                    "contract_item_families_mismatch",
                    contract_path,
                    f"{skill_id} contract item_families={actual}, expected={expected}",
                )

    def _check_contract_visuals(self, contracts: dict[str, Any]) -> None:
        path = self.data_dir / "skill_contracts.json"
        canonical = {item["visual_type"] for item in CANONICAL_VISUAL_TYPES}
        for contract in contracts.get("contracts") or []:
            skill_id = str(contract.get("skill_id") or contract.get("id") or "")
            template = str((contract.get("visual_policy") or {}).get("template") or "")
            if template and template not in canonical:
                self._issue("error", "unknown_contract_visual", path, f"{skill_id} uses unknown visual template {template}")
            for family, target in ((contract.get("remediation") or {}).get("targets") or {}).items():
                if target not in canonical and target != "slow_step_by_step":
                    self._issue("error", "unknown_remediation_visual", path, f"{skill_id}.{family} targets unknown visual {target}")

    def _check_visual_topic_map(self) -> None:
        path = self.data_dir / "visual_topic_map.json"
        visual_map = _load_json(path)
        canonical = {item["visual_type"] for item in CANONICAL_VISUAL_TYPES}
        full_topics_by_grade: dict[int, set[str]] = {}
        for grade in range(1, 10):
            grade_path = self.data_dir / "curriculum" / f"grade_{grade}_full.json"
            payload = _load_json(grade_path)
            full_topics_by_grade[grade] = {_topic_key(topic.get("title")) for topic in payload.get("topics") or []}

        visual_topics_by_grade: dict[int, set[str]] = {}
        for entry in visual_map:
            grade = int(entry.get("grade") or 0)
            topic = _topic_key(entry.get("topic"))
            visual_topics_by_grade.setdefault(grade, set()).add(topic)
            visual_type = str(entry.get("visual_type") or "")
            if visual_type not in canonical:
                self._issue("error", "unknown_visual_topic_type", path, f"{grade}:{topic} uses unknown visual {visual_type}")
            if topic not in full_topics_by_grade.get(grade, set()):
                self._issue("error", "visual_topic_not_in_canonical_curriculum", path, f"{grade}:{topic} is not in grade_{grade}_full.json")

        for grade, full_topics in full_topics_by_grade.items():
            missing = sorted(full_topics - visual_topics_by_grade.get(grade, set()))
            for topic in missing:
                self._issue("error", "canonical_topic_without_visual", path, f"Grade {grade} canonical topic has no visual mapping: {topic}")

    def _check_lessons(self) -> None:
        for path in sorted((self.data_dir / "lessons").glob("grade_*_ru_adapted.json")):
            payload = _load_json(path)
            self._walk_lesson_node(path, payload)

    def _walk_lesson_node(self, path: Path, node: Any) -> None:
        if isinstance(node, dict):
            if "task" in node:
                task = str(node.get("task") or "")
                student_prompt = str(node.get("student_prompt") or "")
                if not student_prompt:
                    self._issue("error", "missing_student_prompt", path, "Lesson task must expose student_prompt")
                if student_prompt and task != student_prompt:
                    self._issue("error", "task_student_prompt_mismatch", path, "task and student_prompt must match after normalization")
                if TEACHER_ONLY_RE.search(task) or TEACHER_ONLY_RE.search(student_prompt):
                    self._issue("error", "teacher_text_in_student_task", path, task[:140])
                has_answerish = any(key in node for key in ("answer", "answers", "solution"))
                if has_answerish and not isinstance(node.get("expected_answers"), list):
                    self._issue("error", "missing_expected_answers", path, "Lesson answer fields must be normalized to expected_answers")
            for value in node.values():
                self._walk_lesson_node(path, value)
        elif isinstance(node, list):
            for item in node:
                self._walk_lesson_node(path, item)

    def _check_detailed_curriculum(self) -> None:
        for path in sorted((self.data_dir / "curriculum_detailed").glob("grade_*_topic_*.json")):
            payload = _load_json(path)
            for section in ("exercises", "problems"):
                for item in payload.get(section) or []:
                    question = str(item.get("question") or "")
                    for phrase in DUPLICATE_INSTRUCTION_PHRASES:
                        if question.count(phrase) > 1:
                            self._issue("error", "duplicate_instruction_suffix", path, question[:180])

    def _check_golden_chains(self, registry: dict[str, Any], contracts: dict[str, Any]) -> None:
        registry_by_id = {str(skill.get("skill_id") or ""): skill for skill in registry.get("skills") or []}
        contract_by_skill = {str(contract.get("skill_id") or ""): contract for contract in contracts.get("contracts") or []}
        for path in sorted((self.data_dir / "golden_chains").glob("*.json")):
            payload = _load_json(path)
            skill_ids = [str(item.get("skill_id") or "") for item in payload.get("skills") or []]
            for skill_id in skill_ids:
                if skill_id not in registry_by_id:
                    self._issue("error", "golden_chain_skill_missing_registry", path, f"Missing registry skill: {skill_id}")
                if skill_id not in contract_by_skill:
                    self._issue("error", "golden_chain_skill_missing_contract", path, f"Missing contract for skill: {skill_id}")
            for item in payload.get("skills") or []:
                skill_id = str(item.get("skill_id") or "")
                required_mode = item.get("required_mode")
                expected_contract_mode = item.get("expected_contract_mode")
                if required_mode and registry_by_id.get(skill_id, {}).get("mode") != required_mode:
                    self._issue("error", "golden_chain_registry_mode_mismatch", path, f"{skill_id} registry mode does not match {required_mode}")
                if expected_contract_mode and contract_by_skill.get(skill_id, {}).get("mode") != expected_contract_mode:
                    self._issue("error", "golden_chain_contract_mode_mismatch", path, f"{skill_id} contract mode does not match {expected_contract_mode}")


def run_material_qa(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    return MaterialQA(data_dir).run()
