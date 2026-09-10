#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
MAP_FILE = DATA / "curriculum" / "lesson_runtime_map.json"
CANONICAL_FILE = DATA / "curriculum" / "grade_1_full.json"
LESSONS_FILE = DATA / "lessons" / "grade_1_ru_adapted.json"
DIAGNOSTIC_FILE = DATA / "diagnostic_pool.json"
REGISTRY_FILE = DATA / "skill_registry.json"
CONTRACTS_FILE = DATA / "skill_contracts.json"
DETAILED_DIR = DATA / "curriculum_detailed"
ALLOWED_STATUSES = {"mapped", "review_required", "unmapped"}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: top level must be an object")
    return value


def topic_list(doc: dict) -> list[dict]:
    if isinstance(doc.get("topics"), list):
        return list(doc["topics"])
    result: list[dict] = []
    for key in ("semester_1", "semester_2"):
        section = doc.get(key) or {}
        result.extend(section.get("topics") or [])
    return result


def fail_if_user_state_changed() -> None:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return
    if result.returncode != 0:
        return
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert "backend/data/user_states.json" not in changed, "user_states.json is present in Git diff"


def main() -> None:
    mapping = load(MAP_FILE)
    canonical = load(CANONICAL_FILE)
    lessons = load(LESSONS_FILE)
    diagnostic = load(DIAGNOSTIC_FILE)
    registry = load(REGISTRY_FILE)
    contracts = load(CONTRACTS_FILE)

    canonical_topics = topic_list(canonical)
    lesson_topics = topic_list(lessons)
    assert len(canonical_topics) == 26, f"expected 26 canonical topics, got {len(canonical_topics)}"
    assert len(lesson_topics) == 26, f"expected 26 lesson topics, got {len(lesson_topics)}"

    canonical_by_id = {int(t["id"]): t for t in canonical_topics}
    assert len(canonical_by_id) == 26, "canonical topic ids are not unique"

    source_lessons: dict[str, tuple[int, dict]] = {}
    for topic in lesson_topics:
        topic_id = int(topic["id"])
        assert topic_id in canonical_by_id, f"lesson topic {topic_id} missing from canonical source"
        for lesson in topic.get("lessons") or []:
            lesson_id = str(lesson.get("lesson_id") or "")
            assert lesson_id, f"topic {topic_id} has lesson without lesson_id"
            assert lesson_id not in source_lessons, f"duplicate source lesson_id: {lesson_id}"
            source_lessons[lesson_id] = (topic_id, lesson)
    assert len(source_lessons) == 78, f"expected 78 source lessons, got {len(source_lessons)}"

    rows = mapping.get("mappings") or []
    assert len(rows) == 78, f"expected 78 map rows, got {len(rows)}"
    row_ids = [str(r.get("lesson_id") or "") for r in rows]
    duplicates = sorted(k for k, v in Counter(row_ids).items() if v != 1)
    assert not duplicates, f"lesson ids mapped other than once: {duplicates}"
    assert set(row_ids) == set(source_lessons), "map lesson ids differ from source lesson ids"

    grade1_questions = [q for q in diagnostic.get("questions") or [] if int(q.get("grade", 0)) == 1]
    diagnostic_topics: dict[str, set[str]] = {}
    for q in grade1_questions:
        diagnostic_topics.setdefault(str(q.get("topic_id") or ""), set()).add(str(q.get("item_family") or ""))
    assert diagnostic_topics, "no grade-1 diagnostic topics"

    skills = {
        str(s.get("skill_id")): s
        for s in registry.get("skills") or []
        if int(s.get("grade", 0)) == 1 and s.get("skill_id")
    }
    contracts_by_skill = {
        str(c.get("skill_id")): c
        for c in contracts.get("contracts") or []
        if int(c.get("grade", 0)) == 1 and c.get("skill_id")
    }
    assert set(skills) == set(contracts_by_skill), "grade-1 skills and contracts differ"

    def check_reference(ref: dict, where: str) -> None:
        topic_id = ref.get("diagnostic_topic_id")
        skill_id = ref.get("skill_id")
        family = ref.get("item_family")
        assert topic_id in diagnostic_topics, f"{where}: unknown diagnostic topic {topic_id}"
        assert skill_id in skills, f"{where}: invented/foreign skill {skill_id}"
        assert topic_id in (skills[skill_id].get("topic_ids") or []), f"{where}: topic is not owned by skill"
        assert family in diagnostic_topics[topic_id], f"{where}: family absent from diagnostic topic"
        contract_families = set(((contracts_by_skill[skill_id].get("diagnostic") or {}).get("item_families") or []))
        assert family in contract_families, f"{where}: family absent from skill contract"

    for row in rows:
        lesson_id = row["lesson_id"]
        topic_id, lesson = source_lessons[lesson_id]
        assert int(row.get("canonical_topic_id")) == topic_id, f"{lesson_id}: wrong canonical topic"
        assert row.get("content_version") == lesson.get("content_version"), f"{lesson_id}: content version mismatch"
        status = row.get("status")
        assert status in ALLOWED_STATUSES, f"{lesson_id}: invalid status {status}"
        refs = (row.get("diagnostic_topic_id"), row.get("skill_id"), row.get("item_family"))
        if status == "mapped":
            assert all(refs), f"{lesson_id}: mapped row lacks a runtime reference"
            check_reference(row, lesson_id)
        elif status == "unmapped":
            assert refs == (None, None, None), f"{lesson_id}: unmapped row contains runtime reference"
        else:
            if any(refs):
                assert all(refs), f"{lesson_id}: partial review reference"
                check_reference(row, lesson_id)
            candidates = row.get("candidates") or []
            for index, candidate in enumerate(candidates):
                check_reference(candidate, f"{lesson_id}.candidates[{index}]")

    computed_counts = dict(sorted(Counter(r["status"] for r in rows).items()))
    assert mapping.get("counts") == computed_counts, "stored status counts are stale"
    assert len(mapping.get("review_required") or []) == computed_counts.get("review_required", 0)
    assert len(mapping.get("unmapped") or []) == computed_counts.get("unmapped", 0)

    if DETAILED_DIR.exists():
        detailed = sorted(DETAILED_DIR.glob("grade_1_topic_*.json"))
        ids = sorted(int(p.stem.rsplit("_", 1)[1]) for p in detailed)
        assert ids == list(range(1, 9)), f"legacy detailed snapshot changed: {ids}"

    fail_if_user_state_changed()
    print(
        "OK: 26 canonical topics; 78 lessons exactly once; "
        f"{len(diagnostic_topics)} diagnostic topics; {len(skills)} grade-1 skills; "
        f"status counts {computed_counts}; user_states.json absent from diff"
    )


if __name__ == "__main__":
    main()
