"""
Diagnostic Engine for Master Kwat
=================================

Контрольные работы по каждому классу (1-9).
Каждая работа включает ВСЕ темы учебника.

АЛГОРИТМ:
1. Ученик заявляет класс N
2. Проверяем ПО ПОРЯДКУ: 1 → 2 → 3 → ... → N
3. На каждый класс — контрольная работа (4 задания)
4. Порог провала: ≥ 2 ошибки в классе
5. Первый класс с ≥ 2 ошибками = стартовый
6. Если все классы пройдены с < 2 ошибок = старт с заявленного
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

# Load diagnostic pool
DIAGNOSTIC_POOL_FILE = Path(__file__).parent.parent.parent / "data" / "diagnostic_pool.json"

diagnostic_pool = {"questions": []}
if DIAGNOSTIC_POOL_FILE.exists():
    with open(DIAGNOSTIC_POOL_FILE, encoding='utf-8') as f:
        diagnostic_pool = json.load(f)


@dataclass
class DiagnosticResult:
    """Результат диагностики"""
    claimed_grade: int
    actual_grade: int
    weak_topics: List[Dict] = field(default_factory=list)
    correct_count: int = 0
    total_questions: int = 0
    weak_grades: List[int] = field(default_factory=list)
    grade_stats: Dict[int, Dict] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return self.correct_count / self.total_questions
    
    @property
    def needs_review(self) -> bool:
        return self.actual_grade < self.claimed_grade
    
    def get_learning_path(self) -> Dict:
        return {
            "start_grade": self.actual_grade,
            "start_topic_id": 1,
            "weak_grades": self.weak_grades,
            "weak_topics": self.weak_topics,
            "grade_stats": self.grade_stats,
            "message": self._generate_message()
        }
    
    def _generate_message(self) -> str:
        if self.needs_review:
            weak_topics_by_grade = {}
            for wt in self.weak_topics:
                g = wt["grade"]
                if g not in weak_topics_by_grade:
                    weak_topics_by_grade[g] = []
                weak_topics_by_grade[g].append(wt["topic"])
            
            problems = []
            for g in sorted(weak_topics_by_grade.keys()):
                topics = list(set(weak_topics_by_grade[g]))
                problems.append(f"{g} класс: {', '.join(topics)}")
            
            return (
                f"🎯 Диагностика завершена!\n\n"
                f"Ты заявил {self.claimed_grade} класс.\n"
                f"Я проверил знания по порядку: 1 → {self.claimed_grade} класс.\n\n"
                f"Обнаружены пробелы:\n"
                f"{chr(10).join('• ' + p for p in problems)}\n\n"
                f"Начнём с {self.actual_grade} класса — с самых основ!\n"
                f"Это не страшно, даже мастера возвращаются к базе 🥋"
            )
        else:
            return (
                f"🎉 Отлично! Я проверил все классы от 1 до {self.claimed_grade}.\n"
                f"У тебя крепкая база! Начнём с {self.claimed_grade} класса 🚀"
            )


class DiagnosticEngine:
    """Движок диагностики с контрольными работами"""
    
    # В full-coverage mode количество вопросов зависит от класса и темы.
    # Параметр оставлен без жёсткой константы, чтобы не вводить в заблуждение.
    
    # Порог провала (≥ = провал)
    FAIL_THRESHOLD = 2
    
    # Максимальный класс
    MAX_GRADE = 9
    
    def __init__(self):
        self.questions = diagnostic_pool.get("questions", [])
    
    def get_questions_for_grade(self, grade: int) -> List[Dict]:
        """Получает все вопросы для конкретного класса"""
        grade_questions = [q for q in self.questions if q.get("grade") == grade]
        return [{
            "id": q.get("id"),
            "grade": grade,
            "topic": q.get("topic"),
            "question": q.get("question"),
            "answer": q.get("answer"),
            "alternatives": q.get("alternatives", []),
            "difficulty": q.get("difficulty", 1),
            "CPA": q.get("CPA", {})
        } for q in grade_questions]
    
    def build_diagnostic_sequence(self, claimed_grade: int) -> List[Dict]:
        """
        Строит последовательность вопросов ПО ПОРЯДКУ классов.
        
        Структура:
        [1.1, ..., 1.8,    // 1 класс (8 вопросов)
         2.1, ..., 2.8,    // 2 класс (8 вопросов)
         ...]
        """
        sequence = []
        
        for grade in range(1, min(claimed_grade + 1, self.MAX_GRADE + 1)):
            grade_qs = self.get_questions_for_grade(grade)
            sequence.extend(grade_qs)
        
        return sequence
    
    def calculate_actual_grade(self, claimed_grade: int, answers: List[Dict]) -> Tuple[int, Dict[int, Dict]]:
        """
        Определяет реальный класс для начала обучения.
        
        Логика:
        1. Группируем ответы по классам
        2. Проверяем каждый класс по порядку
        3. Первый класс с ≥ 2 ошибками = стартовый
        4. Если все ОК → стартуем с заявленного
        """
        # Группируем
        grade_results = {}
        for ans in answers:
            q_grade = ans.get("grade", 1)
            if q_grade not in grade_results:
                grade_results[q_grade] = {"total": 0, "correct": 0, "wrong": 0}
            grade_results[q_grade]["total"] += 1
            if ans.get("is_correct", False):
                grade_results[q_grade]["correct"] += 1
            else:
                grade_results[q_grade]["wrong"] += 1
        
        # Проверяем по порядку
        for grade in range(1, claimed_grade + 1):
            stats = grade_results.get(grade, {"total": 0, "correct": 0, "wrong": 0})
            
            if stats["total"] == 0:
                return grade, grade_results
            
            if stats["wrong"] >= self.FAIL_THRESHOLD:
                return grade, grade_results
        
        # Все классы пройдены успешно
        return claimed_grade, grade_results
    
    def run_diagnostic(self, claimed_grade: int, answers: List[Dict]) -> DiagnosticResult:
        """Запускает диагностику"""
        weak_topics_list = []
        correct_count = 0
        weak_grades = set()
        
        for ans in answers:
            if not ans.get("is_correct", False):
                q = next((q for q in self.questions if q.get("id") == ans.get("question_id")), None)
                if q:
                    weak_topics_list.append({
                        "grade": q.get("grade", 1),
                        "topic": q.get("topic", "unknown"),
                        "question": q.get("question", ""),
                        "user_answer": ans.get("user_answer", "")
                    })
                    weak_grades.add(q.get("grade", 1))
            else:
                correct_count += 1
        
        actual_grade, grade_stats = self.calculate_actual_grade(claimed_grade, answers)
        
        return DiagnosticResult(
            claimed_grade=claimed_grade,
            actual_grade=actual_grade,
            weak_topics=weak_topics_list,
            correct_count=correct_count,
            total_questions=len(answers),
            weak_grades=sorted(weak_grades),
            grade_stats=grade_stats
        )
    
    def get_starting_topic(self, grade: int) -> Dict:
        """Возвращает Тему 1 для указанного класса"""
        curriculum_file = Path(__file__).parent.parent.parent / "data" / "curriculum" / f"grade_{grade}.json"
        
        if not curriculum_file.exists():
            return {"grade": grade, "topic_id": 1, "title": "Начало обучения"}
        
        with open(curriculum_file, encoding='utf-8') as f:
            curriculum = json.load(f)
        
        topics = curriculum.get("topics", [])
        if topics:
            first_topic = topics[0]
            return {
                "grade": grade,
                "topic_id": first_topic.get("id", 1),
                "title": first_topic.get("title", "Тема 1"),
                "pages": first_topic.get("pages", ""),
                "skills": first_topic.get("skills", [])
            }
        
        return {"grade": grade, "topic_id": 1, "title": "Начало обучения"}
    
    def get_exam_for_grade(self, grade: int) -> List[Dict]:
        """Возвращает контрольную работу для класса"""
        return self.get_questions_for_grade(grade)
    
    def get_curriculum_summary(self, grade: int) -> str:
        """Возвращает сводку по учебнику класса"""
        curriculum_file = Path(__file__).parent.parent.parent / "data" / "curriculum" / f"grade_{grade}.json"
        
        if not curriculum_file.exists():
            return f"{grade} класс"
        
        with open(curriculum_file, encoding='utf-8') as f:
            curriculum = json.load(f)
        
        topics = [t["title"] for t in curriculum.get("topics", []) if not t.get("is_review")]
        return f"{grade} класс: {', '.join(topics[:3])}..."


# Singleton
diagnostic_engine = DiagnosticEngine()


def get_engine() -> DiagnosticEngine:
    return diagnostic_engine