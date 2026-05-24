"""
MasterKva — Curriculum Graph (Phase E)

Строит граф образовательных зависимостей:
  - Узлы: темы (topics) из skill_registry
  - Рёбра: prerequisites → topic (что нужно знать ДЕСЯТЫЕ темы)
  - Межклассовые зависимости

Валидация:
  - Нет циклических зависимостей
  - Нет «висячих» next_skills (все next существуют в графе)
  - Все темы достижимы от начальных (grade 1)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SKILL_REGISTRY_FILE = DATA_DIR / "skill_registry.json"


class CurriculumNode:
    """Single topic/skill node in the curriculum graph."""

    def __init__(
        self,
        skill_id: str,
        skill_name: str | None = None,
        grade: int | None = None,
        topic_ids: list[str] | None = None,
        prerequisites: list[str] | None = None,
        next_skills: list[str] | None = None,
        domain: str | None = None,
        mode: str | None = None,
    ):
        self.skill_id = skill_id
        self.skill_name = skill_name or skill_id
        self.grade = grade
        self.topic_ids = topic_ids or []
        self.prerequisites = prerequisites or []  # skill_ids that must come BEFORE
        self.next_skills = next_skills or []       # skill_ids that come AFTER
        self.domain = domain or ""
        self.mode = mode or "shadow"

    def __repr__(self) -> str:
        return f"CurriculumNode({self.skill_id}, grade={self.grade}, prereq={self.prerequisites}, next={self.next_skills})"


class CurriculumGraph:
    """
    Directed acyclic graph of curriculum dependencies.

    Nodes: skills/topics from skill_registry
    Edges: prerequisite → skill (skill depends on prerequisite)
    """

    def __init__(self, nodes: dict[str, CurriculumNode] | None = None):
        self.nodes: dict[str, CurriculumNode] = nodes or {}

    @classmethod
    def from_skill_registry(cls, registry_path: Path | None = None) -> CurriculumGraph:
        """Build graph from skill_registry.json."""
        path = registry_path or SKILL_REGISTRY_FILE
        if not path.exists():
            return cls()

        raw = json.loads(path.read_text(encoding="utf-8"))
        skills = raw.get("skills", [])

        nodes: dict[str, CurriculumNode] = {}
        for skill in skills:
            skill_id = str(skill.get("skill_id") or "").strip()
            if not skill_id:
                continue
            nodes[skill_id] = CurriculumNode(
                skill_id=skill_id,
                skill_name=skill.get("name"),
                grade=skill.get("grade"),
                topic_ids=skill.get("topic_ids") or [],
                prerequisites=skill.get("prerequisites") or [],
                next_skills=skill.get("next_skills") or [],
                domain=skill.get("domain"),
                mode=skill.get("mode"),
            )

        graph = cls(nodes)
        # Derive next_skills from prerequisites (bidirectional)
        graph._derive_edges()
        return graph

    def _derive_edges(self) -> None:
        """Ensure bidirectionality: if A.prerequisites contains B, then B.next_skills should contain A."""
        for skill_id, node in self.nodes.items():
            for prereq_id in node.prerequisites:
                if prereq_id in self.nodes:
                    prereq_node = self.nodes[prereq_id]
                    if skill_id not in prereq_node.next_skills:
                        prereq_node.next_skills.append(skill_id)

    # ---- Graph queries ----

    def get_node(self, skill_id: str) -> CurriculumNode | None:
        return self.nodes.get(skill_id)

    def get_prerequisites(self, skill_id: str) -> list[CurriculumNode]:
        """Get direct prerequisites for a skill."""
        node = self.nodes.get(skill_id)
        if not node:
            return []
        return [self.nodes[pid] for pid in node.prerequisites if pid in self.nodes]

    def get_all_prerequisites(self, skill_id: str) -> list[str]:
        """Get transitive closure of prerequisites (all ancestors)."""
        visited: set[str] = set()
        stack = list(self.nodes.get(skill_id, CurriculumNode("")).prerequisites)
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            node = self.nodes.get(current)
            if node:
                stack.extend(node.prerequisites)
        return sorted(visited)

    def get_next_skills(self, skill_id: str) -> list[CurriculumNode]:
        """Get direct next skills (children)."""
        node = self.nodes.get(skill_id)
        if not node:
            return []
        return [self.nodes[sid] for sid in node.next_skills if sid in self.nodes]

    def get_learning_path(self, from_skill: str, to_skill: str) -> list[str]:
        """Find shortest learning path between two skills (BFS)."""
        if from_skill not in self.nodes or to_skill not in self.nodes:
            return []

        visited: set[str] = {from_skill}
        queue: list[list[str]] = [[from_skill]]

        while queue:
            path = queue.pop(0)
            current = path[-1]
            if current == to_skill:
                return path
            node = self.nodes.get(current)
            if node:
                for next_id in node.next_skills:
                    if next_id not in visited and next_id in self.nodes:
                        visited.add(next_id)
                        queue.append(path + [next_id])

        return []  # No path found

    def get_roots(self) -> list[CurriculumNode]:
        """Get nodes with no prerequisites (starting points)."""
        return [n for n in self.nodes.values() if not n.prerequisites]

    def get_leaves(self) -> list[CurriculumNode]:
        """Get nodes with no next skills (terminal)."""
        return [n for n in self.nodes.values() if not n.next_skills]

    def get_by_grade(self, grade: int) -> list[CurriculumNode]:
        """Get all nodes for a specific grade."""
        return [n for n in self.nodes.values() if n.grade == grade]

    # ---- Validation ----

    def validate(self) -> dict[str, Any]:
        """
        Validate the curriculum graph.

        Returns dict with:
          - valid: bool
          - errors: list[str]
          - warnings: list[str]
          - stats: dict
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 1. No cycles
        cycles = self._detect_cycles()
        if cycles:
            for cycle in cycles:
                errors.append(f"Cyclic dependency detected: {' → '.join(cycle)}")

        # 2. No dangling next_skills
        for skill_id, node in self.nodes.items():
            for next_id in node.next_skills:
                if next_id not in self.nodes:
                    errors.append(f"Dangling next_skill: {skill_id} → {next_id} (not in graph)")

        # 3. No dangling prerequisites
        for skill_id, node in self.nodes.items():
            for prereq_id in node.prerequisites:
                if prereq_id not in self.nodes:
                    warnings.append(f"Dangling prerequisite: {skill_id} requires {prereq_id} (not in graph)")

        # 4. All topics reachable from roots
        unreachable = self._find_unreachable()
        if unreachable:
            warnings.append(f"Unreachable skills: {unreachable}")

        # 5. Grade ordering: prerequisites should be <= current grade
        for skill_id, node in self.nodes.items():
            if node.grade is None:
                continue
            for prereq in self.get_prerequisites(skill_id):
                if prereq.grade is not None and prereq.grade > node.grade:
                    warnings.append(
                        f"Grade ordering: {skill_id} (grade {node.grade}) depends on "
                        f"{prereq.skill_id} (grade {prereq.grade})"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": self._stats(),
        }

    def _detect_cycles(self) -> list[list[str]]:
        """Detect cycles using DFS."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node_id: str) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            node = self.nodes.get(node_id)
            if node:
                for next_id in node.next_skills:
                    if next_id not in visited:
                        dfs(next_id)
                    elif next_id in rec_stack:
                        # Found cycle
                        cycle_start = path.index(next_id)
                        cycles.append(path[cycle_start:] + [next_id])

            path.pop()
            rec_stack.remove(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)

        return cycles

    def _find_unreachable(self) -> list[str]:
        """Find nodes not reachable from any root."""
        roots = self.get_roots()
        if not roots:
            return list(self.nodes.keys())

        reachable: set[str] = set()
        stack = [r.skill_id for r in roots]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            node = self.nodes.get(current)
            if node:
                stack.extend(node.next_skills)

        return [sid for sid in self.nodes if sid not in reachable]

    def _stats(self) -> dict[str, Any]:
        """Graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "roots": len(self.get_roots()),
            "leaves": len(self.get_leaves()),
            "grades": sorted(set(n.grade for n in self.nodes.values() if n.grade)),
            "domains": sorted(set(n.domain for n in self.nodes.values() if n.domain)),
        }

    # ---- Export ----

    def to_dict(self) -> dict[str, Any]:
        """Export graph as serializable dict."""
        return {
            "nodes": {
                sid: {
                    "skill_id": n.skill_id,
                    "skill_name": n.skill_name,
                    "grade": n.grade,
                    "topic_ids": n.topic_ids,
                    "prerequisites": n.prerequisites,
                    "next_skills": n.next_skills,
                    "domain": n.domain,
                    "mode": n.mode,
                }
                for sid, n in self.nodes.items()
            },
            "stats": self._stats(),
        }

    def to_mermaid(self) -> str:
        """Export graph as Mermaid flowchart."""
        lines = ["flowchart TD"]
        for sid, node in self.nodes.items():
            label = node.skill_name.replace(" ", "_")
            grade_label = f"[G{node.grade}]" if node.grade else ""
            lines.append(f'    {sid}["{label} {grade_label}"]')
        for sid, node in self.nodes.items():
            for next_id in node.next_skills:
                if next_id in self.nodes:
                    lines.append(f"    {sid} --> {next_id}")
        return "\n".join(lines)


# --- Singleton ---
_curriculum_graph: CurriculumGraph | None = None


def get_curriculum_graph() -> CurriculumGraph:
    """Get or build the curriculum graph singleton."""
    global _curriculum_graph
    if _curriculum_graph is None:
        _curriculum_graph = CurriculumGraph.from_skill_registry()
    return _curriculum_graph


def refresh_curriculum_graph() -> CurriculumGraph:
    """Force rebuild of the curriculum graph."""
    global _curriculum_graph
    _curriculum_graph = CurriculumGraph.from_skill_registry()
    return _curriculum_graph
