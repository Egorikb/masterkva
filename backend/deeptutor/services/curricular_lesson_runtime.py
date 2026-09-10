"""Fail-closed runtime for curated curricular lessons.

B1 intentionally enables one reviewed lesson/version pair. The runtime keeps
mapping evidence server-side and exposes only the current child-facing prompt.
It never writes mastery or student progression.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deeptutor.services.lesson_assessment import assess_lesson, validate_assessment

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LESSONS_FILE = DATA_DIR / "lessons" / "grade_1_ru_adapted.json"
RUNTIME_MAP_FILE = DATA_DIR / "curriculum" / "lesson_runtime_map.json"
DIAGNOSTIC_POOL_FILE = DATA_DIR / "diagnostic_pool.json"
SKILL_REGISTRY_FILE = DATA_DIR / "skill_registry.json"
SKILL_CONTRACTS_FILE = DATA_DIR / "skill_contracts.json"

PILOT_LESSON_ID = "g1-t12-l01"
PILOT_CONTENT_VERSION = "2.0"
PILOT_DIAGNOSTIC_TOPIC_ID = "g1_t07"
PILOT_SKILL_ID = "g1_compose_decompose_10"
PILOT_ITEM_FAMILY = "addition_within_10_part_whole"
SUPPORTED_LESSONS = frozenset({(PILOT_LESSON_ID, PILOT_CONTENT_VERSION)})


class CurriculumResolutionError(ValueError):
    """A stable fail-closed curriculum resolution error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class ResolvedCurricularLesson:
    lesson_id: str
    content_version: str
    lesson: dict[str, Any]
    mapping: dict[str, Any]

    @property
    def assessment_kind(self) -> str:
        return str(self.lesson["assessment"]["kind"])

    @property
    def part_count(self) -> int:
        if self.assessment_kind == "rubric":
            return 1
        return len(self.lesson["assessment"]["parts"])


class CurricularLessonRuntime:
    """Resolve and assess only explicitly reviewed curricular bindings."""

    @staticmethod
    def _load_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError) as exc:
            raise CurriculumResolutionError(f"invalid_source:{path.name}") from exc

    @staticmethod
    def _one(items: list[dict[str, Any]], missing: str, duplicate: str) -> dict[str, Any]:
        if not items:
            raise CurriculumResolutionError(missing)
        if len(items) != 1:
            raise CurriculumResolutionError(duplicate)
        return dict(items[0])

    def _find_lesson(self, lesson_id: str, content_version: str) -> dict[str, Any]:
        data = self._load_json(LESSONS_FILE)
        try:
            lessons = [
                lesson
                for semester in (data["semester_1"], data["semester_2"])
                for topic in semester["topics"]
                for lesson in topic["lessons"]
            ]
        except (KeyError, TypeError) as exc:
            raise CurriculumResolutionError("invalid_source:grade_1_ru_adapted.json") from exc
        matches = [
            item
            for item in lessons
            if str(item.get("lesson_id") or "") == lesson_id
            and str(item.get("content_version") or "") == content_version
        ]
        return self._one(matches, "lesson_not_found", "duplicate_lesson")

    def _find_mapping(self, lesson_id: str, content_version: str) -> dict[str, Any]:
        data = self._load_json(RUNTIME_MAP_FILE)
        if not isinstance(data, dict) or str(data.get("reference_version") or "") != PILOT_CONTENT_VERSION:
            raise CurriculumResolutionError("invalid_runtime_map_version")
        mappings = data.get("mappings")
        if not isinstance(mappings, list):
            raise CurriculumResolutionError("invalid_source:lesson_runtime_map.json")
        matches = [
            item
            for item in mappings
            if isinstance(item, dict)
            and str(item.get("lesson_id") or "") == lesson_id
            and str(item.get("content_version") or "") == content_version
        ]
        return self._one(matches, "mapping_not_found", "duplicate_mapping")

    def _validate_binding(self, lesson: dict[str, Any], mapping: dict[str, Any]) -> None:
        if mapping.get("status") != "mapped":
            raise CurriculumResolutionError("mapping_not_approved")
        if (
            str(mapping.get("diagnostic_topic_id") or "") != PILOT_DIAGNOSTIC_TOPIC_ID
            or str(mapping.get("skill_id") or "") != PILOT_SKILL_ID
            or str(mapping.get("item_family") or "") != PILOT_ITEM_FAMILY
        ):
            raise CurriculumResolutionError("binding_not_allowlisted")
        if int(mapping.get("canonical_topic_id") or 0) != int(lesson.get("source_topic_id") or -1):
            raise CurriculumResolutionError("canonical_topic_mismatch")

        errors = validate_assessment(lesson.get("assessment"))
        if errors:
            raise CurriculumResolutionError("invalid_lesson_assessment")

        presentation = lesson.get("presentation")
        if not isinstance(presentation, dict) or presentation.get("mode") != "sequential_text":
            raise CurriculumResolutionError("unsupported_presentation")
        prompts = presentation.get("prompts")
        assessment = lesson["assessment"]
        expected_part_count = 1 if assessment["kind"] == "rubric" else len(assessment["parts"])
        if not isinstance(prompts, list) or len(prompts) != expected_part_count:
            raise CurriculumResolutionError("presentation_part_mismatch")
        if any(not isinstance(prompt, str) or not prompt.strip() for prompt in prompts):
            raise CurriculumResolutionError("invalid_presentation_prompt")

        pool = self._load_json(DIAGNOSTIC_POOL_FILE)
        questions = pool.get("questions") if isinstance(pool, dict) else None
        if not isinstance(questions, list):
            raise CurriculumResolutionError("invalid_source:diagnostic_pool.json")
        exact_questions = [
            item
            for item in questions
            if isinstance(item, dict)
            and str(item.get("topic_id") or "") == PILOT_DIAGNOSTIC_TOPIC_ID
            and str(item.get("item_family") or "") == PILOT_ITEM_FAMILY
        ]
        if not exact_questions:
            raise CurriculumResolutionError("diagnostic_binding_missing")

        registry = self._load_json(SKILL_REGISTRY_FILE)
        skills = registry.get("skills") if isinstance(registry, dict) else None
        if not isinstance(skills, list):
            raise CurriculumResolutionError("invalid_source:skill_registry.json")
        skill = self._one(
            [item for item in skills if isinstance(item, dict) and item.get("skill_id") == PILOT_SKILL_ID],
            "skill_binding_missing",
            "duplicate_skill_binding",
        )
        if PILOT_DIAGNOSTIC_TOPIC_ID not in list(skill.get("topic_ids") or []):
            raise CurriculumResolutionError("skill_topic_mismatch")

        contracts_data = self._load_json(SKILL_CONTRACTS_FILE)
        contracts = contracts_data.get("contracts") if isinstance(contracts_data, dict) else None
        if not isinstance(contracts, list):
            raise CurriculumResolutionError("invalid_source:skill_contracts.json")
        contract_id = str(skill.get("contract_id") or PILOT_SKILL_ID)
        contract_matches = [
            item
            for item in contracts
            if isinstance(item, dict)
            and str(item.get("id") or "") == contract_id
            and str(item.get("skill_id") or "") == PILOT_SKILL_ID
        ]
        contract = self._one(contract_matches, "skill_contract_missing", "duplicate_skill_contract")
        item_families = ((contract.get("diagnostic") or {}).get("item_families") or [])
        if PILOT_ITEM_FAMILY not in item_families:
            raise CurriculumResolutionError("skill_family_mismatch")

    def resolve(self, lesson_id: str, content_version: str) -> ResolvedCurricularLesson:
        normalized_id = str(lesson_id or "").strip()
        normalized_version = str(content_version or "").strip()
        if not normalized_id or not normalized_version:
            raise CurriculumResolutionError("lesson_identity_required")
        if (normalized_id, normalized_version) not in SUPPORTED_LESSONS:
            raise CurriculumResolutionError("lesson_not_allowlisted")

        lesson = self._find_lesson(normalized_id, normalized_version)
        mapping = self._find_mapping(normalized_id, normalized_version)
        self._validate_binding(lesson, mapping)
        return ResolvedCurricularLesson(
            lesson_id=normalized_id,
            content_version=normalized_version,
            lesson=lesson,
            mapping=mapping,
        )

    @staticmethod
    def _validate_part_index(resolved: ResolvedCurricularLesson, part_index: int) -> int:
        if isinstance(part_index, bool) or not isinstance(part_index, int):
            raise CurriculumResolutionError("invalid_part_index")
        if part_index < 0 or part_index >= resolved.part_count:
            raise CurriculumResolutionError("part_out_of_range")
        return part_index

    def child_part(self, resolved: ResolvedCurricularLesson, part_index: int) -> dict[str, Any]:
        index = self._validate_part_index(resolved, part_index)
        prompt = resolved.lesson["presentation"]["prompts"][index]
        return {
            "id": f"{resolved.lesson_id}:v{resolved.content_version}:part:{index}",
            "lesson_id": resolved.lesson_id,
            "content_version": resolved.content_version,
            "part_index": index,
            "part_number": index + 1,
            "part_count": resolved.part_count,
            "question": prompt,
            "prompt": prompt,
            "requires_image": bool(resolved.lesson["presentation"].get("requires_image", False)),
            "source": "curriculum",
        }

    def assess_part(
        self,
        resolved: ResolvedCurricularLesson,
        part_index: int,
        response: str,
    ) -> dict[str, Any]:
        index = self._validate_part_index(resolved, part_index)
        assessment = resolved.lesson["assessment"]
        if assessment["kind"] == "rubric":
            return assess_lesson(resolved.lesson, response)
        isolated_lesson = {
            "assessment": {
                "kind": "exact",
                "parts": [assessment["parts"][index]],
            }
        }
        return assess_lesson(isolated_lesson, response)

    def hint(self, resolved: ResolvedCurricularLesson, part_index: int) -> str:
        self._validate_part_index(resolved, part_index)
        hint = resolved.lesson.get("hint")
        if not isinstance(hint, str) or not hint.strip():
            raise CurriculumResolutionError("hint_unavailable")
        return hint.strip()


curricular_lesson_runtime = CurricularLessonRuntime()
