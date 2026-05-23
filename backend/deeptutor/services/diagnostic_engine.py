from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DIAGNOSTIC_POOL_FILE = DATA_DIR / "diagnostic_pool.json"
SKILL_REGISTRY_FILE = DATA_DIR / "skill_registry.json"
SKILL_CONTRACTS_FILE = DATA_DIR / "skill_contracts.json"


@dataclass(slots=True)
class DiagnosticResult:
    claimed_grade: int
    actual_grade: int
    weak_topics: list[dict[str, Any]] = field(default_factory=list)
    correct_count: int = 0
    total_questions: int = 0
    weak_grades: list[int] = field(default_factory=list)
    grade_stats: dict[int, dict[str, int]] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return self.correct_count / self.total_questions

    @property
    def needs_review(self) -> bool:
        return bool(self.weak_topics)

    def get_learning_path(self) -> dict[str, Any]:
        return {
            "start_grade": self.actual_grade,
            "start_topic_id": self.weak_topics[0]["topic_id"] if self.weak_topics else None,
            "weak_grades": self.weak_grades,
            "weak_topics": self.weak_topics,
            "grade_stats": self.grade_stats,
            "message": self._generate_message(),
        }

    def _generate_message(self) -> str:
        if self.needs_review:
            problems: list[str] = []
            by_grade: dict[int, list[str]] = {}
            for topic in self.weak_topics:
                by_grade.setdefault(int(topic["grade"]), []).append(str(topic["topic"]))
            for grade in sorted(by_grade):
                topics = sorted(set(by_grade[grade]))
                problems.append(f"{grade} класс: {', '.join(topics)}")
            return (
                "🎯 Диагностика завершена!\n\n"
                f"Ты заявил {self.claimed_grade} класс.\n"
                "Обнаружены пробелы:\n"
                f"{chr(10).join('• ' + item for item in problems)}\n\n"
                f"Начнём с {self.actual_grade} класса — с самой базы!"
            )
        return (
            "🎉 Отлично!\n\n"
            f"Ты готов начать с {self.claimed_grade} класса.\n"
            "База выглядит крепкой."
        )


class DiagnosticEngine:
    FAIL_THRESHOLD = 2
    MAX_GRADE = 9

    def __init__(self, pool: dict[str, Any] | None = None):
        self.pool = pool or self._load_pool()
        self.questions: list[dict[str, Any]] = list(self.pool.get("questions", []))
        self.skill_registry = self._load_json_file(SKILL_REGISTRY_FILE, default={"version": "v1", "mode": "shadow", "skills": []})
        self.skill_contracts = self._load_json_file(SKILL_CONTRACTS_FILE, default={"version": "v1", "contracts": []})
        self._skill_index = self._build_skill_index()

    def _load_pool(self) -> dict[str, Any]:
        if DIAGNOSTIC_POOL_FILE.exists():
            try:
                return json.loads(DIAGNOSTIC_POOL_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"questions": []}

    @staticmethod
    def _load_json_file(path: Path, default: dict[str, Any]) -> dict[str, Any]:
        if path.exists():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    return value
            except Exception:
                pass
        return default

    @staticmethod
    def _synthetic_topic_id(grade: int, topic_index: int) -> str:
        return f"g{grade}_t{topic_index:02d}"

    @staticmethod
    def _synthetic_question_id(topic_id: str, question_index: int) -> str:
        return f"{topic_id}_q{question_index:02d}"

    @staticmethod
    def _normalize_key(value: str) -> str:
        return " ".join(str(value).strip().upper().split())

    def _build_skill_index(self) -> dict[str, dict[str, Any]]:
        contracts_by_id: dict[str, dict[str, Any]] = {}
        for contract in list(self.skill_contracts.get("contracts", [])):
            contract_id = str(contract.get("id") or "").strip()
            skill_id = str(contract.get("skill_id") or "").strip()
            if contract_id:
                contracts_by_id[contract_id] = contract
            if skill_id and skill_id not in contracts_by_id:
                contracts_by_id[skill_id] = contract

        index: dict[str, dict[str, Any]] = {}
        for skill in list(self.skill_registry.get("skills", [])):
            skill_id = str(skill.get("skill_id") or "").strip()
            if not skill_id:
                continue
            contract_id = str(skill.get("contract_id") or skill_id).strip()
            contract = contracts_by_id.get(contract_id) or contracts_by_id.get(skill_id) or {}
            entry = {**skill, "contract": contract}
            index[skill_id] = entry

            topic_ids = skill.get("topic_ids") or []
            for topic_id in topic_ids:
                topic_key = self._normalize_key(str(topic_id))
                index.setdefault(topic_key, entry)

            topic_names = skill.get("topic_names") or []
            for topic_name in topic_names:
                topic_key = self._normalize_key(str(topic_name))
                index.setdefault(topic_key, entry)

        return index

    def _skill_for_question(self, question: dict[str, Any]) -> dict[str, Any] | None:
        topic_id = self._normalize_key(str(question.get("topic_id") or ""))
        topic_name = self._normalize_key(str(question.get("topic") or ""))
        skill = self._skill_index.get(topic_id) or self._skill_index.get(topic_name)
        if not skill:
            return None
        contract = dict(skill.get("contract") or {})
        return {
            "skill_id": skill.get("skill_id"),
            "grade": skill.get("grade"),
            "domain": skill.get("domain"),
            "topic_ids": list(skill.get("topic_ids") or []),
            "prerequisites": list(skill.get("prerequisites") or []),
            "next_skills": list(skill.get("next_skills") or []),
            "mode": str(contract.get("mode") or skill.get("mode") or self.skill_registry.get("mode", "shadow")),
            "contract_id": skill.get("contract_id"),
            "coverage_status": ((contract.get("coverage") or {}).get("status") or contract.get("coverage_status") or "partial"),
            "board_policy": contract.get("board_policy"),
            "visual_template": (contract.get("visual_policy") or {}).get("template"),
            "error_model": dict(contract.get("error_model") or {}),
            "mastery_gate": dict(contract.get("mastery_gate") or {}),
        }

    def _enrich_question(self, question: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(question)
        skill = self._skill_for_question(question)
        if skill:
            enriched["skill_id"] = skill["skill_id"]
            enriched["skill_mode"] = skill["mode"]
            enriched["coverage_status"] = skill["coverage_status"]
            enriched["board_policy"] = skill["board_policy"]
            enriched["visual_template"] = skill["visual_template"]
            enriched["error_model"] = skill["error_model"]
            enriched["mastery_gate"] = skill["mastery_gate"]
            enriched["skill_contract_id"] = skill["contract_id"]
        return enriched

    def get_questions_for_grade(self, grade: int) -> list[dict[str, Any]]:
        grade_questions = [q for q in self.questions if int(q.get("grade", 0)) == grade]
        if not grade_questions:
            return []

        topic_order: dict[str, int] = {}
        topic_counts: dict[str, int] = {}
        normalized: list[dict[str, Any]] = []

        for index, question in enumerate(grade_questions, start=1):
            topic_name = str(question.get("topic") or "unknown")
            if topic_name not in topic_order:
                topic_order[topic_name] = len(topic_order) + 1
            topic_index = topic_order[topic_name]
            topic_id = str(question.get("topic_id") or self._synthetic_topic_id(grade, topic_index))
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1
            question_id = str(question.get("id") or self._synthetic_question_id(topic_id, topic_counts[topic_id]))

            normalized.append(
                self._enrich_question(
                {
                    "id": question_id,
                    "fallback_id": f"g{grade}-q{index}",
                    "grade": grade,
                    "topic_id": topic_id,
                    "topic": topic_name,
                    "question": question.get("question", ""),
                    "answer": question.get("answer", ""),
                    "answer_type": question.get("answer_type", "text"),
                    "practice_ref": question.get("practice_ref") or topic_id,
                    "alternatives": list(question.get("alternatives", [])),
                    "difficulty": int(question.get("difficulty", 1)),
                    "CPA": dict(question.get("CPA", {})),
                }
                )
            )
        return normalized

    def build_diagnostic_sequence(self, claimed_grade: int) -> list[dict[str, Any]]:
        sequence: list[dict[str, Any]] = []
        for grade in range(1, min(claimed_grade, self.MAX_GRADE) + 1):
            sequence.extend(self.get_questions_for_grade(grade))
        return sequence

    def calculate_actual_grade(self, claimed_grade: int, answers: list[dict[str, Any]]) -> tuple[int, dict[int, dict[str, int]]]:
        grade_results: dict[int, dict[str, int]] = {}
        for answer in answers:
            q_grade = int(answer.get("grade", 1))
            stats = grade_results.setdefault(q_grade, {"total": 0, "correct": 0, "wrong": 0})
            stats["total"] += 1
            if answer.get("is_correct", False):
                stats["correct"] += 1
            else:
                stats["wrong"] += 1

        for grade in range(1, claimed_grade + 1):
            stats = grade_results.get(grade, {"total": 0, "correct": 0, "wrong": 0})
            if stats["total"] == 0:
                return grade, grade_results
            if stats["wrong"] >= self.FAIL_THRESHOLD:
                return grade, grade_results

        return claimed_grade, grade_results

    def run_diagnostic(self, claimed_grade: int, answers: list[dict[str, Any]]) -> DiagnosticResult:
        actual_grade, grade_stats = self.calculate_actual_grade(claimed_grade, answers)
        weak_topics: list[dict[str, Any]] = []
        weak_grades: list[int] = []
        correct_count = 0

        for answer in answers:
            if answer.get("is_correct", False):
                correct_count += 1
                continue
            weak_grade = int(answer.get("grade", claimed_grade))
            weak_grades.append(weak_grade)
            weak_topics.append(
                {
                    "grade": weak_grade,
                    "topic_id": answer.get("topic_id") or self._synthetic_topic_id(weak_grade, 1),
                    "topic": answer.get("topic") or "Тема",
                    "source_question_id": answer.get("question_id") or answer.get("id") or answer.get("fallback_id"),
                    "skill_id": answer.get("skill_id"),
                    "coverage_status": answer.get("coverage_status"),
                }
            )

        return DiagnosticResult(
            claimed_grade=claimed_grade,
            actual_grade=actual_grade,
            weak_topics=weak_topics,
            correct_count=correct_count,
            total_questions=len(answers),
            weak_grades=weak_grades,
            grade_stats=grade_stats,
        )

    def select_weak_topic(self, result: DiagnosticResult) -> dict[str, Any] | None:
        if result.weak_topics:
            return result.weak_topics[0]
        return self.get_starting_topic(result.actual_grade)

    def get_starting_topic(self, grade: int) -> dict[str, Any]:
        questions = self.get_questions_for_grade(grade)
        if questions:
            first = questions[0]
            return {
                "grade": grade,
                "topic_id": first["topic_id"],
                "topic": first["topic"],
                "source_question_id": first["id"],
            }
        return {
            "grade": grade,
            "topic_id": f"g{grade}_t01",
            "topic": f"Тема {grade}",
            "source_question_id": None,
        }


diagnostic_engine = DiagnosticEngine()
