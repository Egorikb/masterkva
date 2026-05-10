"""Analytics for parents - JSON response after each lesson."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class LessonAnalytics:
    """Analytics to send to parents after each lesson."""
    
    # Идентификация
    student_name: str
    student_grade: int
    lesson_date: str  # ISO format
    
    # Прогресс
    topic: str  # Тема урока
    textbook_page: int  # Страница учебника
    progress_status: str  # "completed", "in_progress", "needs_repeat"
    
    # Анализ
    strong_points: list  # ["Хорошо решает примеры", "Понимает геометрию"]
    weak_points: list  # ["Трудности с переходом через десяток"]
    
    # Метрики
    correct_answers: int
    total_exercises: int
    energy_qi: int  # Текущая Энергия Ци
    belt_level: str  # "Белый", "Желтый", "Оранжевый", "Зеленый", "Синий", "Черный"
    
    # Эмоции
    emotional_state: str  # "confident", "struggling", "frustrated", "motivated"
    notes_for_parent: str  # Дополнительные заметки
    
    def to_json(self) -> dict:
        """Convert to JSON for API response."""
        return {
            "student": {
                "name": self.student_name,
                "grade": self.student_grade
            },
            "lesson": {
                "date": self.lesson_date,
                "topic": self.topic,
                "textbook_page": self.textbook_page,
                "status": self.progress_status
            },
            "analysis": {
                "strong_points": self.strong_points,
                "weak_points": self.weak_points
            },
            "metrics": {
                "correct": self.correct_answers,
                "total": self.total_exercises,
                "accuracy_percent": round(self.correct_answers / self.total_exercises * 100, 1) if self.total_exercises > 0 else 0,
                "energy_qi": self.energy_qi,
                "belt_level": self.belt_level
            },
            "emotional": {
                "state": self.emotional_state,
                "notes": self.notes_for_parent
            },
            "disclaimer": "Ваш ребенок сейчас на уровне 2-го класса по китайской системе, что соответствует 3-му классу стандартной программы."
        }

def calculate_belt_level(energy_qi: int) -> str:
    """Calculate belt level based on Energy Qi."""
    if energy_qi < 20:
        return "Белый пояс"
    elif energy_qi < 50:
        return "Желтый пояс"
    elif energy_qi < 100:
        return "Оранжевый пояс"
    elif energy_qi < 200:
        return "Зеленый пояс"
    elif energy_qi < 500:
        return "Синий пояс"
    else:
        return "Черный пояс"

def create_lesson_analytics(
    student_name: str,
    student_grade: int,
    topic: str,
    textbook_page: int,
    correct_answers: int,
    total_exercises: int,
    strong_points: list,
    weak_points: list,
    emotional_state: str = "confident"
) -> LessonAnalytics:
    """Create analytics for a lesson."""
    
    energy_qi = correct_answers * 5
    belt = calculate_belt_level(energy_qi)
    
    # Определяем статус
    if total_exercises == 0:
        status = "in_progress"
    elif correct_answers == total_exercises:
        status = "completed"
    elif correct_answers >= total_exercises * 0.7:
        status = "in_progress"
    else:
        status = "needs_repeat"
    
    # Заметки для родителя
    if emotional_state == "struggling":
        note = "Ребенок испытывает трудности, рекомендуем дополнительную практику."
    elif emotional_state == "frustrated":
        note = "Ребенок расстроен. Важно поддержать его и похвалить за усилия!"
    elif emotional_state == "motivated":
        note = "Отличная мотивация! Ребенок готов к новым вызовам."
    else:
        note = "Хорошая работа! Продолжаем учиться."
    
    return LessonAnalytics(
        student_name=student_name,
        student_grade=student_grade,
        lesson_date=datetime.now().isoformat(),
        topic=topic,
        textbook_page=textbook_page,
        progress_status=status,
        strong_points=strong_points,
        weak_points=weak_points,
        correct_answers=correct_answers,
        total_exercises=total_exercises,
        energy_qi=energy_qi,
        belt_level=belt,
        emotional_state=emotional_state,
        notes_for_parent=note
    )