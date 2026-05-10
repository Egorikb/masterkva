import re
import uuid
import os
import shutil
from typing import Dict, Optional, TypedDict
from dataclasses import dataclass
from pathlib import Path

from deeptutor.agents.chat.agentic_pipeline import AgenticChatPipeline

class AgentResponse(TypedDict):
    text: str
    audio_url: Optional[str]

@dataclass
class StudentState:
    name: str = "Unknown"
    grade: int = 0
    current_mode: str = "diagnose"
    diagnostic_stage: int = 0

class PandaTutorAgent(AgenticChatPipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = StudentState()
        self.audio_storage_path = Path("/home/egor/ai-agent/workspace/deeptutor_analyzed/audio_storage")
        self.audio_storage_path.mkdir(exist_ok=True)

    # Blacklist: words that are NOT names
    NAME_BLACKLIST = {"привет", "здравствуй", "привета", "hi", "hello", "hey", "хай", "прив", "здрав"}
    
    def _parse_name(self, text: str) -> Optional[str]:
        # Check if input is just a greeting - return None
        text_lower = text.lower().strip()
        if text_lower in self.NAME_BLACKLIST:
            return None
        
        # Also check "привет" is in the text but not a name
        if text_lower == "привет" or text_lower == "здравствуй":
            return None
            
        patterns = [
            r"меня (?:зо|за)вут\s+([а-яА-ЯёЁ]+)",
            r"(?:зо|за)вут\s+([а-яА-ЯёЁ]+)",
            r"зови меня\s+([а-яА-ЯёЁ]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                name = match.group(1).capitalize()
                # Double check not in blacklist
                if name.lower() not in self.NAME_BLACKLIST:
                    return name
        return None

    def _parse_grade(self, text: str) -> Optional[int]:
        # More patterns to catch "в 6", "6", "я в 6 классе"
        patterns = [
            r"в\s+(\d+)\s+классе",      # "в 6 классе"
            r"классе\s*(\d+)",             # "классе 6"
            r"класс\s*(\d+)",              # "класс 6" or "6 класс"
            r"(\d+)\s*класс",              # "6класс"
            r"я\s+в\s+(\d+)",            # "я в 6"
            r"учусь\s+в\s+(\d+)",        # "учусь в 6"
            r"мне\s+(\d+)\s+лет",        # "мне 6 лет" (age, not grade)
            r"(?:^|\s)(\d+)(?:\s|$)",    # standalone "6" or " 6 "
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                grade = int(match.group(1))
                if 1 <= grade <= 11:
                    # Double check it's not age-related
                    if "лет" not in text_lower or "мне" in text_lower:
                        return grade
        
        return None

    def classify_intent(self, user_input: str) -> str:
        user_input = user_input.lower()
        explain_keywords = ["объясни", "что такое", "как ", "расскажи про", "научи", "объяснение"]
        solve_keywords = ["реши", "задача", "помоги решить", "сколько будет", "пример", "посчитай"]
        
        if any(k in user_input for k in explain_keywords):
            return "explain"
        if any(k in user_input for k in solve_keywords):
            return "solve"
        return "diagnose"

    async def _generate_audio(self, text: str) -> Optional[str]:
        try:
            from deeptutor.services.tts.yandex_tts import synthesize_speech
            audio_path = synthesize_speech(text, voice="filipp", emotion="good")
            if audio_path and os.path.exists(audio_path):
                filename = f"audio_{uuid.uuid4().hex[:8]}.ogg"
                dest_path = self.audio_storage_path / filename
                shutil.copy(audio_path, str(dest_path))
                return f"http://localhost:8001/audio_storage/{filename}"
            return None
        except Exception as e:
            print(f"Warning: audio - {e}")
            return None

    async def _prepare_response(self, text: str) -> AgentResponse:
        audio_url = await self._generate_audio(text)
        return {"text": text, "audio_url": audio_url}

    async def diagnose(self, student_input: str) -> AgentResponse:
        intent = self.classify_intent(student_input)
        
        if intent == "explain":
            self.state.current_mode = "explain"
            topic = student_input
            for kw in ["объясни ", "что такое ", "как ", "расскажи про ", "научи "]:
                if kw in student_input.lower():
                    topic = student_input.lower().split(kw)[1].strip()
                    break
            response = "Достаю свиток " + str(self.state.grade) + " класса, сейчас всё разберём! " + topic
            return await self._prepare_response(response)
        
        if intent == "solve":
            self.state.current_mode = "solve"
            response = self.state.name + ", решаю твою задачу! " + student_input
            return await self._prepare_response(response)
        
        self.state.current_mode = "diagnose"
        
        # ===== STEP-BY-STEP FLOW =====
        parsed_name = self._parse_name(student_input)
        parsed_grade = self._parse_grade(student_input)
        
        # STEP 1: Ask for name (name unknown)
        if self.state.name == "Unknown":
            if parsed_name:
                self.state.name = parsed_name
                response = "Отлично, " + self.state.name + "! 🐼\n\nВ каком ты классе?"
            else:
                response = "Привет! Я твой наставник по математике 🐼\n\nКак тебя зовут?"
            return await self._prepare_response(response)
        
        # STEP 2: Ask for grade (name known, grade unknown)
        if self.state.grade == 0:
            if parsed_grade:
                self.state.grade = parsed_grade
                response = f"Приятно познакомиться, {self.state.name}! 🎯\nТы в {self.state.grade} классе.\n\nНапиши 'давай' чтобы начать диагностику!"
            else:
                response = f"Отлично, {self.state.name}! 🐼\n\nВ каком ты классе? (1-9)"
            return await self._prepare_response(response)
        
        # STEP 3: Ready (both known)
        if "давай" in student_input.lower() or "тест" in student_input.lower():
            self.state.diagnostic_stage = 10
            response = f"Отлично! Проверим знания в {self.state.grade} классе! 🐼\n\nГотов к первому вопросу!"
        else:
            self.state.diagnostic_stage += 1
            response = f"{self.state.name}, ты в {self.state.grade} классе. Напиши 'давай' чтобы начать диагностику!"
        
        return await self._prepare_response(response)

    async def explain(self, topic: str) -> AgentResponse:
        self.state.current_mode = "explain"
        response = "Объясняю тему: " + topic + " для " + self.state.name
        return await self._prepare_response(response)

    async def quiz(self, topic: str) -> AgentResponse:
        self.state.current_mode = "quiz"
        response = "Викторина по теме: " + topic
        return await self._prepare_response(response)

    async def solve(self, problem: str) -> AgentResponse:
        self.state.current_mode = "solve"
        response = "Решаю задачу: " + problem
        return await self._prepare_response(response)

    def update_student_info(self, name: str, grade: int):
        self.state.name = name
        self.state.grade = grade

    def get_current_mode(self) -> str:
        return self.state.current_mode

    def reset_state(self):
        self.state = StudentState()
