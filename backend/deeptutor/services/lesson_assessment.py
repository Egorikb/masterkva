"""Pure, bounded assessment for curated lesson responses."""

from __future__ import annotations

import ast
import re
from decimal import Decimal, InvalidOperation
from typing import Any


_KINDS = {"exact", "ordered", "rubric"}
_NUMBER = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
_ARITHMETIC_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Constant)


def _normalise(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _safe_expression(expression: str) -> bool:
    try:
        tree = ast.parse(expression.replace(",", "."), mode="eval")
    except (SyntaxError, ValueError):
        return False
    return all(
        isinstance(node, _ARITHMETIC_NODES)
        and not (isinstance(node, ast.Constant) and (isinstance(node.value, bool) or not isinstance(node.value, (int, float))))
        for node in ast.walk(tree)
    )


def validate_assessment(assessment: Any) -> list[str]:
    """Return schema errors without changing a lesson or any student state."""
    if not isinstance(assessment, dict):
        return ["assessment must be a dictionary"]
    kind = assessment.get("kind")
    if kind not in _KINDS:
        return ["kind must be exact, ordered, or rubric"]
    errors: list[str] = []
    if kind == "rubric":
        criteria = assessment.get("criteria")
        if not isinstance(criteria, list) or not criteria or any(not isinstance(item, str) or not item.strip() for item in criteria):
            errors.append("rubric assessment needs non-empty criteria")
        return errors
    parts = assessment.get("parts")
    if not isinstance(parts, list) or not parts:
        return ["parts must be a non-empty list"]
    if kind == "exact" and len(parts) != 1:
        return ["exact assessment requires one part"]
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            errors.append(f"part {index} must be a dictionary")
            continue
        if not isinstance(part.get("prompt"), str) or not part["prompt"].strip():
            errors.append(f"part {index} needs a prompt")
        expected = part.get("expected")
        if not isinstance(expected, list) or not expected or any(not isinstance(item, str) or not item.strip() for item in expected):
            errors.append(f"part {index} needs non-empty expected variants")
        expression = part.get("expression")
        if expression is not None and (not isinstance(expression, str) or not _safe_expression(expression)):
            errors.append(f"part {index} has an unsafe expression")
    return errors


def _matches(response: str, expected: str) -> bool:
    answer, target = _normalise(response), _normalise(expected)
    if answer == target:
        return True
    # Decimal equivalence applies only to bare numbers; units remain semantic.
    if _NUMBER.fullmatch(answer) and _NUMBER.fullmatch(target):
        if answer.startswith(("+", "-")) != target.startswith(("+", "-")):
            return False
        try:
            return Decimal(answer.replace(",", ".")) == Decimal(target.replace(",", "."))
        except InvalidOperation:
            return False
    return False


def _responses(response: str | list[str], count: int) -> list[str] | None:
    if isinstance(response, str):
        values = response.split(";") if ";" in response else [response]
    elif isinstance(response, list) and all(isinstance(item, str) for item in response):
        values = response
    else:
        return None
    if len(values) != count or any(not value.strip() for value in values):
        return None
    return values


def assess_lesson(lesson: dict, response: str | list[str]) -> dict:
    """Assess one response only; this function deliberately has no progression writes."""
    assessment = lesson.get("assessment") if isinstance(lesson, dict) else None
    errors = validate_assessment(assessment)
    if errors:
        return {"status": "invalid_input", "errors": errors}

    kind = assessment["kind"]
    if kind == "rubric":
        valid_response = (
            isinstance(response, str) and bool(response.strip())
        ) or (
            isinstance(response, list) and bool(response) and all(isinstance(item, str) and item.strip() for item in response)
        )
        return {"status": "needs_review"} if valid_response else {"status": "invalid_input", "errors": ["response is required"]}

    parts = assessment["parts"]
    answers = _responses(response, len(parts))
    if answers is None:
        return {"status": "invalid_input", "errors": ["response count does not match assessment parts"]}

    correct = all(any(_matches(answer, expected) for expected in part["expected"]) for answer, part in zip(answers, parts))
    return {"status": "correct" if correct else "incorrect"}
