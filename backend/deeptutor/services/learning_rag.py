from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LEARNING_SOURCE_DIRS = (
    DATA_DIR / "lessons",
    DATA_DIR / "curriculum",
    DATA_DIR / "curriculum_detailed",
)
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")


@dataclass(slots=True)
class LearningChunk:
    grade: int
    source_file: str
    source_type: str
    title: str
    topic_id: str | None
    text: str
    tokens: frozenset[str]

    @property
    def label(self) -> str:
        topic = self.topic_id or "без topic_id"
        return f"{self.source_type} · {self.title} · {topic}"

    @property
    def snippet(self) -> str:
        cleaned = " ".join(self.text.split())
        return cleaned[:260] + ("…" if len(cleaned) > 260 else "")


class LearningRAG:
    def __init__(self, source_dirs: Iterable[Path] | None = None) -> None:
        self.source_dirs = tuple(source_dirs or LEARNING_SOURCE_DIRS)
        self._chunks: list[LearningChunk] | None = None

    def _load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _tokenize(text: str) -> frozenset[str]:
        tokens = {token.lower() for token in TOKEN_RE.findall(text)}
        return frozenset(token for token in tokens if token)

    @staticmethod
    def _safe_grade(path: Path, payload: Any) -> int:
        if isinstance(payload, dict):
            try:
                return int(payload.get("grade") or payload.get("class") or 0)
            except Exception:
                return 0
        match = re.search(r"grade_(\d+)", path.name)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _append_text(parts: list[str], value: Any, prefix: str | None = None) -> None:
        if value is None:
            return
        if isinstance(value, str):
            text = value.strip()
            if text:
                parts.append(f"{prefix}: {text}" if prefix else text)
            return
        if isinstance(value, (int, float, bool)):
            parts.append(f"{prefix}: {value}" if prefix else str(value))
            return
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            if items:
                rendered = ", ".join(items)
                parts.append(f"{prefix}: {rendered}" if prefix else rendered)
            return
        if isinstance(value, dict):
            nested: list[str] = []
            for key in (
                "title",
                "student_prompt",
                "task",
                "question",
                "expected_answers",
                "answer",
                "solution",
                "description",
                "pages",
                "skills",
                "examples",
                "visual",
                "cpa_objects",
            ):
                if key in value:
                    LearningRAG._append_text(nested, value.get(key), prefix=key)
            if nested:
                parts.extend(nested)
            return

    def _build_chunk_text(self, payload: dict[str, Any], *, fallback_title: str, source_type: str) -> str:
        parts: list[str] = [f"Источник: {source_type}"]
        for key in (
            "title",
            "name",
            "description",
            "pages",
            "skills",
            "review_topic",
            "topic",
            "student_prompt",
            "task",
            "question",
            "expected_answers",
            "solution",
            "answer",
        ):
            if key in payload:
                self._append_text(parts, payload.get(key), prefix=key)
        for key in ("lessons", "topics", "semester_1", "semester_2", "skill_index"):
            if key in payload:
                self._append_text(parts, payload.get(key), prefix=key)
        if len(parts) == 1:
            parts.append(fallback_title)
        return "\n".join(parts)

    def _chunk_from_topic(self, path: Path, grade: int, source_type: str, topic: dict[str, Any], extra_title: str = "") -> LearningChunk:
        title = str(topic.get("title") or topic.get("name") or extra_title or path.stem)
        topic_id = None
        if "id" in topic:
            topic_id = str(topic.get("id"))
        elif "topic_id" in topic:
            topic_id = str(topic.get("topic_id"))
        text = self._build_chunk_text(topic, fallback_title=title, source_type=source_type)
        tokens = self._tokenize(text)
        return LearningChunk(
            grade=grade,
            source_file=path.name,
            source_type=source_type,
            title=title,
            topic_id=topic_id,
            text=text,
            tokens=tokens,
        )

    def _extract_chunks_from_payload(self, path: Path, payload: Any) -> list[LearningChunk]:
        grade = self._safe_grade(path, payload)
        source_type = path.parent.name or "learning"
        chunks: list[LearningChunk] = []

        if not isinstance(payload, dict):
            text = f"Источник: {source_type}\n{payload}"
            chunks.append(
                LearningChunk(
                    grade=grade,
                    source_file=path.name,
                    source_type=source_type,
                    title=path.stem,
                    topic_id=None,
                    text=text,
                    tokens=self._tokenize(text),
                )
            )
            return chunks

        if "semester_1" in payload or "semester_2" in payload:
            for semester_name in ("semester_1", "semester_2"):
                semester = payload.get(semester_name)
                if not isinstance(semester, dict):
                    continue
                for topic in semester.get("topics", []):
                    if isinstance(topic, dict):
                        title = f"{payload.get('title', path.stem)} · {semester_name}"
                        chunks.append(self._chunk_from_topic(path, grade, source_type, topic, extra_title=title))
            if chunks:
                return chunks

        topics = payload.get("topics")
        if isinstance(topics, list) and topics:
            topic_like = [topic for topic in topics if isinstance(topic, dict)]
            if topic_like:
                if any("lessons" in topic for topic in topic_like):
                    for topic in topic_like:
                        topic_title = str(topic.get("title") or topic.get("name") or path.stem)
                        lesson_texts: list[str] = []
                        for lesson in topic.get("lessons", []):
                            if isinstance(lesson, dict):
                                lesson_texts.append(self._build_chunk_text(lesson, fallback_title=topic_title, source_type=source_type))
                        merged_topic = dict(topic)
                        if lesson_texts:
                            merged_topic["lesson_bundle"] = lesson_texts
                        chunks.append(self._chunk_from_topic(path, grade, source_type, merged_topic))
                    return chunks
                for topic in topic_like:
                    chunks.append(self._chunk_from_topic(path, grade, source_type, topic))
                return chunks

        title = str(payload.get("title") or payload.get("name") or path.stem)
        text = self._build_chunk_text(payload, fallback_title=title, source_type=source_type)
        chunks.append(
            LearningChunk(
                grade=grade,
                source_file=path.name,
                source_type=source_type,
                title=title,
                topic_id=str(payload.get("topic_id")) if payload.get("topic_id") is not None else None,
                text=text,
                tokens=self._tokenize(text),
            )
        )
        return chunks

    def _build_index(self) -> list[LearningChunk]:
        chunks: list[LearningChunk] = []
        for source_dir in self.source_dirs:
            if not source_dir.exists():
                continue
            canonical_curriculum_names = self._canonical_curriculum_names(source_dir)
            for path in sorted(source_dir.glob("*.json")):
                if canonical_curriculum_names and path.name not in canonical_curriculum_names:
                    continue
                try:
                    payload = self._load_json(path)
                except Exception:
                    continue
                chunks.extend(self._extract_chunks_from_payload(path, payload))
        return chunks

    @staticmethod
    def _canonical_curriculum_names(source_dir: Path) -> set[str]:
        if source_dir.name != "curriculum":
            return set()
        manifest_path = source_dir / "canonical_curriculum.json"
        if not manifest_path.exists():
            return set()
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        grades = payload.get("grades") if isinstance(payload, dict) else None
        if not isinstance(grades, dict):
            return set()
        return {str(file_name) for file_name in grades.values() if str(file_name).strip()}

    @property
    def chunks(self) -> list[LearningChunk]:
        if self._chunks is None:
            self._chunks = self._build_index()
        return self._chunks

    def retrieve(self, *, grade: int, query: str, topic_id: str | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if topic_id:
            query_tokens = query_tokens | self._tokenize(topic_id)
        ranked: list[tuple[float, LearningChunk]] = []
        for chunk in self.chunks:
            if chunk.grade != grade:
                continue
            overlap = len(query_tokens & chunk.tokens)
            if overlap == 0 and topic_id and chunk.topic_id == topic_id:
                overlap = 3
            if overlap == 0:
                continue
            score = float(overlap)
            if topic_id and chunk.topic_id == topic_id:
                score += 5.0
            if query_tokens & self._tokenize(chunk.title):
                score += 1.5
            if query_tokens & self._tokenize(chunk.source_file):
                score += 0.5
            ranked.append((score, chunk))

        if not ranked:
            fallback = [chunk for chunk in self.chunks if chunk.grade == grade]
            ranked = [(0.1, chunk) for chunk in fallback[:top_k]]

        ranked.sort(key=lambda item: (-item[0], item[1].source_file, item[1].title))
        selected = [chunk for _, chunk in ranked[:top_k]]
        return [
            {
                "grade": chunk.grade,
                "source_file": chunk.source_file,
                "source_type": chunk.source_type,
                "title": chunk.title,
                "topic_id": chunk.topic_id,
                "snippet": chunk.snippet,
                "text": chunk.text,
            }
            for chunk in selected
        ]

    @staticmethod
    def format_context(results: list[dict[str, Any]]) -> str:
        if not results:
            return "Учебный контекст не найден, поэтому берём материал из базовой программы класса."
        lines = ["Учебный контекст из наших материалов:"]
        for item in results:
            topic = item.get("topic_id") or "без topic_id"
            lines.append(f"• {item.get('title')} ({topic}): {item.get('snippet')}")
        return "\n".join(lines)


learning_rag = LearningRAG()


@lru_cache(maxsize=128)
def retrieve_learning_context(grade: int, query: str, topic_id: str | None = None, top_k: int = 3) -> tuple[dict[str, Any], ...]:
    return tuple(learning_rag.retrieve(grade=grade, query=query, topic_id=topic_id, top_k=top_k))
