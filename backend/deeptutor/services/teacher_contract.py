"""Structured contract for adaptive teacher responses."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PedagogicalMove(str, Enum):
    PRAISE = "praise"
    HINT = "hint"
    EXPLAIN = "explain"
    REPHRASE = "rephrase"
    ANALOGY = "analogy"
    STEP_BY_STEP = "step_by_step"
    VISUALIZE = "visualize"
    REMEDIATE = "remediate"
    TRANSITION = "transition"
    PAUSE = "pause"


ALLOWED_VISUAL_TYPES = {
    "number_bond",
    "ten_frame",
    "bar_model",
    "number_line",
    "base_ten_blocks",
    "place_value_chart",
    "part_part_whole_bar",
    "area_model_grid",
    "array_matrix",
    "bar_model_strip_diagram",
    "ratio_table",
    "double_number_line",
    "fraction_circle_region",
    "percent_grid_10x10",
    "coordinate_plane_plot",
    "algebra_tiles",
    "balance_scale_equation",
    "function_table",
    "cartesian_graph",
    "clock_face",
    "fraction_bars",
    "division_groups",
    "geoboard_dynamic",
    "net_of_solid",
}


class VisualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    needed: bool = False
    type: str | None = None
    focus: str | None = Field(default=None, max_length=120)
    values: list[int | float | str] = Field(default_factory=list, max_length=12)
    labels: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_visual(self) -> "VisualRequest":
        if not self.needed:
            self.type = None
            self.values = []
            self.labels = []
            return self
        if self.type not in ALLOWED_VISUAL_TYPES:
            raise ValueError("visual type is not allowed")
        return self


class TeacherResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = "v1"
    teacher_text: str = Field(min_length=1, max_length=600)
    pedagogical_move: PedagogicalMove
    hint_level: int = Field(default=0, ge=0, le=3)
    visual_request: VisualRequest = Field(default_factory=VisualRequest)
    safety_flags: list[str] = Field(default_factory=list, max_length=12)
    needs_human_review: bool = False
    source: Literal["llm", "fallback", "safety"] = "llm"

    @field_validator("teacher_text")
    @classmethod
    def compact_text(cls, value: str) -> str:
        return " ".join(value.split()).strip()


def requested_pedagogical_move(message: str, stage: str) -> PedagogicalMove:
    text = str(message or "").casefold()
    if any(token in text for token in ("не понял", "не поняла", "объясни иначе", "другими словами", "проще")):
        return PedagogicalMove.REPHRASE
    if any(token in text for token in ("покажи", "картин", "схем", "нарисуй", "наглядно")):
        return PedagogicalMove.VISUALIZE
    if any(token in text for token in ("намек", "намёк", "подскажи", "подсказ")):
        return PedagogicalMove.HINT
    if any(token in text for token in ("по шагам", "пошагово")):
        return PedagogicalMove.STEP_BY_STEP
    if stage == "practice_result":
        return PedagogicalMove.PRAISE
    if stage == "remediation":
        return PedagogicalMove.REMEDIATE
    return PedagogicalMove.EXPLAIN


def answer_is_leaked(text: str, correct_answer: Any | None) -> bool:
    answer = str(correct_answer or "").strip()
    if not answer or len(answer) > 32:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(answer)}(?!\w)", str(text or ""), re.IGNORECASE))
