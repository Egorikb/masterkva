from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DIAGNOSTIC_POOL_FILE = DATA_DIR / "diagnostic_pool.json"


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

    def _load_pool(self) -> dict[str, Any]:
        if DIAGNOSTIC_POOL_FILE.exists():
            try:
                return json.loads(DIAGNOSTIC_POOL_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"questions": []}

    @staticmethod
    def _synthetic_topic_id(grade: int, topic_index: int) -> str:
        return f"g{grade}_t{topic_index:02d}"

    @staticmethod
    def _synthetic_question_id(topic_id: str, question_index: int) -> str:
        return f"{topic_id}_q{question_index:02d}"

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
