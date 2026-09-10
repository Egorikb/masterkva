"""Quality gate for the authored grade-one reference corpus."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from deeptutor.services.lesson_assessment import assess_lesson, validate_assessment


LESSON_ID = re.compile(r"g1-t(\d{2})-l(\d{2})$")
PAGE_RANGE = re.compile(r"\d+(?:-\d+)?$")
NUMBER = re.compile(r"[+-]?\d+(?:[.,]\d+)?(?:/[+-]?\d+)?$")


def _read(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: cannot read JSON: {exc}")
        return {}


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _fraction(value: Any) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("non-numeric constant")
    return Fraction(str(value))


def _calculate(expression: str) -> Fraction:
    tree = ast.parse(expression.replace(",", "."), mode="eval")

    def visit(node: ast.AST) -> Fraction:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant):
            return _fraction(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        raise ValueError(f"unsupported expression node {type(node).__name__}")

    return visit(tree)


def _expected_number(value: str) -> Fraction:
    text = value.strip().replace(",", ".")
    if not NUMBER.fullmatch(text):
        raise ValueError("expected answer is not a bare number")
    return Fraction(text)


def _lessons(payload: dict[str, Any]) -> list[tuple[int, int, dict[str, Any], dict[str, Any]]]:
    result = []
    for semester_number, key in ((1, "semester_1"), (2, "semester_2")):
        for topic in payload.get(key, {}).get("topics", []):
            if isinstance(topic, dict):
                for index, lesson in enumerate(topic.get("lessons", []), 1):
                    if isinstance(lesson, dict):
                        result.append((semester_number, index, topic, lesson))
    return result


def validate_reference(data_dir: Path, *, verify_sources: bool = False) -> list[str]:
    """Return deterministic corpus errors; never mutate the reference data."""
    errors: list[str] = []
    lessons_payload = _read(data_dir / "lessons/grade_1_ru_adapted.json", errors)
    curriculum = _read(data_dir / "curriculum/grade_1_full.json", errors)
    manifest = _read(data_dir / "curriculum/grade_1_sources.json", errors)
    if errors:
        return errors

    if not lessons_payload.get("reference_version"):
        errors.append("grade-one lessons: missing reference_version")
    curriculum_topics = {str(topic.get("id")): topic for topic in curriculum.get("topics", []) if isinstance(topic, dict)}
    mappings = manifest.get("topic_mapping", {})
    books = manifest.get("books", {})
    if not isinstance(mappings, dict):
        errors.append("source manifest: topic_mapping must be a dictionary")
        mappings = {}
    if not isinstance(books, dict):
        errors.append("source manifest: books must be a dictionary")
        books = {}

    rows = _lessons(lessons_payload)
    topics = {str(topic.get("id")) for _, _, topic, _ in rows}
    if len(rows) != 78:
        errors.append(f"grade-one lessons: expected 78 lessons, found {len(rows)}")
    if len(topics) != 26:
        errors.append(f"grade-one lessons: expected 26 topics, found {len(topics)}")

    seen_ids: set[str] = set()
    for semester, index, topic, lesson in rows:
        topic_id = str(topic.get("id"))
        location = str(lesson.get("lesson_id") or f"topic {topic_id} lesson {index}")
        teaching = topic.get("teaching")
        if not isinstance(teaching, dict):
            errors.append(f"topic {topic_id}: missing teaching contract")
        else:
            prerequisites = teaching.get("prerequisite_topic_ids")
            current_id = int(topic_id) if topic_id.isdigit() else 0
            if (
                not isinstance(prerequisites, list)
                or any(isinstance(item, bool) or not isinstance(item, int) or str(item) not in curriculum_topics or item >= current_id for item in prerequisites)
            ):
                errors.append(f"topic {topic_id}: prerequisites must reference earlier topics")
            for field in ("goal", "common_mistake", "completion_policy"):
                if not isinstance(teaching.get(field), str) or not teaching[field].strip():
                    errors.append(f"topic {topic_id}: teaching.{field} is required")
            if not _nonempty_strings(teaching.get("delivery")):
                errors.append(f"topic {topic_id}: teaching.delivery is required")
            worked = teaching.get("worked_example")
            if (
                not isinstance(worked, dict)
                or not isinstance(worked.get("prompt"), str)
                or not worked["prompt"].strip()
                or not _nonempty_strings(worked.get("solution_steps"))
            ):
                errors.append(f"topic {topic_id}: teaching.worked_example is incomplete")
        expected_id = f"g1-t{int(topic_id):02d}-l{index:02d}" if topic_id.isdigit() else ""
        if not LESSON_ID.fullmatch(str(lesson.get("lesson_id") or "")) or lesson.get("lesson_id") != expected_id:
            errors.append(f"{location}: unstable lesson_id, expected {expected_id}")
        if lesson.get("lesson_id") in seen_ids:
            errors.append(f"{location}: duplicate lesson_id")
        seen_ids.add(lesson.get("lesson_id"))

        prompts = lesson.get("presentation", {}).get("prompts") if isinstance(lesson.get("presentation"), dict) else None
        joined = " ".join(prompts) if _nonempty_strings(prompts) else None
        if joined is None or lesson.get("task") != joined or lesson.get("student_prompt") != joined:
            errors.append(f"{location}: task and student_prompt must equal joined presentation prompts")
        for field in ("hint", "teacher_note"):
            if not isinstance(lesson.get(field), str) or not lesson[field].strip():
                errors.append(f"{location}: missing {field}")
        for field in ("solution_steps", "lesson_skills"):
            if not _nonempty_strings(lesson.get(field)):
                errors.append(f"{location}: missing {field}")

        assessment = lesson.get("assessment")
        for error in validate_assessment(assessment):
            errors.append(f"{location}: assessment {error}")
        if isinstance(assessment, dict):
            kind = assessment.get("kind")
            parts = assessment.get("parts", [])
            expected_mode = "open" if kind == "rubric" else "exact"
            if lesson.get("answer_mode") != expected_mode:
                errors.append(f"{location}: answer_mode must be {expected_mode} for {kind} assessment")
            if kind == "ordered" and (not isinstance(parts, list) or len(parts) <= 1):
                errors.append(f"{location}: ordered assessment requires more than one part")
            if kind == "rubric":
                compatible = []
                if lesson.get("acceptance_criteria") != assessment.get("criteria"):
                    errors.append(f"{location}: rubric acceptance_criteria must equal assessment criteria")
            elif isinstance(parts, list) and parts and all(isinstance(part, dict) and _nonempty_strings(part.get("expected")) for part in parts):
                compatible = [part["expected"][0] for part in parts]
                if [part.get("prompt") for part in parts] != prompts:
                    errors.append(f"{location}: assessment part prompts must equal presentation prompts")
                response: str | list[str] = compatible[0] if kind == "exact" else compatible
                if assess_lesson(lesson, response).get("status") != "correct":
                    errors.append(f"{location}: canonical assessment answers do not pass assessor")
            else:
                compatible = None
            if compatible is not None and lesson.get("expected_answers") != compatible:
                errors.append(f"{location}: expected_answers is incompatible with assessment")
            if isinstance(parts, list):
                for part_index, part in enumerate(parts, 1):
                    if not isinstance(part, dict) or "expression" not in part:
                        continue
                    try:
                        calculated = _calculate(part["expression"])
                        expected = _expected_number(part["expected"][0])
                    except (ArithmeticError, AttributeError, IndexError, KeyError, SyntaxError, TypeError, ValueError) as exc:
                        errors.append(f"{location}: part {part_index} bad arithmetic expression/answer: {exc}")
                    else:
                        if calculated != expected:
                            errors.append(f"{location}: part {part_index} arithmetic mismatch: {part['expression']} != {part['expected'][0]}")

        source = lesson.get("source")
        mapping = mappings.get(topic_id)
        if not isinstance(mapping, dict):
            errors.append(f"{location}: missing source mapping for topic {topic_id}")
        else:
            expected_source = dict(mapping)
            expected_source["kind"] = "authored_adaptation"
            if source != expected_source:
                errors.append(f"{location}: source does not exactly match topic mapping")
            verification = mapping.get("verification")
            pages = mapping.get("printed_pages")
            if verification == "unverified" and pages != "":
                errors.append(f"source topic {topic_id}: unverified mapping must have empty printed_pages")
            elif verification == "unit_verified" and (not isinstance(pages, str) or not PAGE_RANGE.fullmatch(pages)):
                errors.append(f"source topic {topic_id}: verified mapping needs a numeric printed_pages range")
            elif verification not in {"unit_verified", "unverified"}:
                errors.append(f"source topic {topic_id}: invalid verification")
            curriculum_topic = curriculum_topics.get(topic_id, {})
            if topic.get("source") != mapping:
                errors.append(f"topic {topic_id}: source does not equal manifest mapping")
            if curriculum_topic.get("source_status") != verification:
                errors.append(f"topic {topic_id}: curriculum source_status does not equal verification")
            if lesson.get("source_pages") != pages or curriculum_topic.get("pages") != pages:
                errors.append(f"{location}: source_pages, mapping printed_pages, and curriculum pages must match")
            if lesson.get("source_topic_id") != topic.get("id") or lesson.get("semester") != semester or lesson.get("lesson_index") != index:
                errors.append(f"{location}: topic/semester/lesson indices are out of sync")
            if lesson.get("skills") != curriculum_topic.get("skills"):
                errors.append(f"{location}: skills are out of sync with curriculum")

    if set(mappings) != set(curriculum_topics):
        errors.append("source manifest topic_mapping keys must match curriculum topic ids")
    for book_key, book in books.items():
        if not isinstance(book, dict):
            errors.append(f"source book {book_key}: must be a dictionary")
            continue
        local_path = book.get("local_path")
        verification = book.get("verification")
        if local_path is None:
            if verification != "missing":
                errors.append(f"source book {book_key}: absent file must be marked missing")
            continue
        if verification != "local_verified" or not book.get("sha256"):
            errors.append(f"source book {book_key}: local source needs sha256 and local_verified")
        if verify_sources:
            path = data_dir / str(local_path)
            if not path.is_file():
                errors.append(f"source book {book_key}: local file is missing")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != book.get("sha256"):
                errors.append(f"source book {book_key}: sha256 mismatch")
    for topic_id, mapping in mappings.items():
        if isinstance(mapping, dict) and mapping.get("book_id") not in books:
            errors.append(f"source topic {topic_id}: unknown book_id")
            continue
        if not isinstance(mapping, dict):
            continue
        book = books.get(mapping.get("book_id"), {})
        if mapping.get("verification") == "unit_verified":
            if not isinstance(book, dict) or book.get("verification") != "local_verified" or not book.get("local_path"):
                errors.append(f"source topic {topic_id}: unit_verified requires a local_verified book")
                continue
            pages = mapping.get("printed_pages", "")
            if PAGE_RANGE.fullmatch(str(pages)):
                bounds = [int(value) for value in str(pages).split("-")]
                start, end = bounds[0], bounds[-1]
                if start < 1 or start > end:
                    errors.append(f"source topic {topic_id}: printed_pages range is invalid or reversed")
                pdf_pages, offset = book.get("pdf_pages"), book.get("printed_to_pdf_1based_offset", 0)
                if isinstance(pdf_pages, int) and isinstance(offset, int) and end > pdf_pages - offset:
                    errors.append(f"source topic {topic_id}: printed_pages exceed local book bounds")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=BACKEND / "data")
    parser.add_argument("--verify-sources", action="store_true")
    args = parser.parse_args()
    errors = validate_reference(args.data_dir, verify_sources=args.verify_sources)
    if errors:
        print("\n".join(errors))
        return 1
    manifest = _read(args.data_dir / "curriculum/grade_1_sources.json", [])
    mappings = manifest.get("topic_mapping", {})
    books = manifest.get("books", {})
    unit_verified = sum(item.get("verification") == "unit_verified" for item in mappings.values())
    unverified = sum(item.get("verification") == "unverified" for item in mappings.values())
    missing = sum(item.get("verification") == "missing" for item in books.values())
    print("grade 1 authored reference: OK")
    print(f"source coverage: unit_verified={unit_verified}; unverified={unverified}; missing_books={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
