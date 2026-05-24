"""
Tests for Curriculum Graph (Phase E).

Covers:
- Graph construction from skill_registry
- Node queries: prerequisites, next_skills, roots, leaves
- Path finding (BFS)
- Validation: cycles, dangling refs, reachability, grade ordering
- Export: dict, mermaid
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from deeptutor.services.curriculum_graph import (
    CurriculumGraph,
    CurriculumNode,
    get_curriculum_graph,
    refresh_curriculum_graph,
)


@pytest.fixture
def sample_registry(tmp_path: Path) -> Path:
    """Create a minimal skill registry for testing."""
    registry = {
        "version": "v1",
        "mode": "shadow",
        "skills": [
            {
                "skill_id": "g1_early_arithmetic_core",
                "name": "Ранняя арифметика",
                "grade": 1,
                "domain": "arithmetic",
                "topic_ids": ["g1_t01", "g1_t02", "g1_t03"],
                "prerequisites": [],
                "next_skills": ["g2_addition_core"],
                "mode": "shadow",
            },
            {
                "skill_id": "g2_addition_core",
                "name": "Сложение",
                "grade": 2,
                "domain": "arithmetic",
                "topic_ids": ["g2_t01"],
                "prerequisites": ["g1_early_arithmetic_core"],
                "next_skills": ["g2_subtraction_core"],
                "mode": "shadow",
            },
            {
                "skill_id": "g2_subtraction_core",
                "name": "Вычитание",
                "grade": 2,
                "domain": "arithmetic",
                "topic_ids": ["g2_t02"],
                "prerequisites": ["g2_addition_core"],
                "next_skills": ["g3_time_measurement_core"],
                "mode": "shadow",
            },
            {
                "skill_id": "g3_time_measurement_core",
                "name": "Время",
                "grade": 3,
                "domain": "measurement",
                "topic_ids": ["g3_t01"],
                "prerequisites": ["g2_subtraction_core"],
                "next_skills": [],
                "mode": "shadow",
            },
        ],
    }
    path = tmp_path / "skill_registry.json"
    path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def graph(sample_registry: Path) -> CurriculumGraph:
    return CurriculumGraph.from_skill_registry(sample_registry)


class TestCurriculumNode:
    def test_creation(self):
        node = CurriculumNode("test_skill", grade=1, prerequisites=["prereq1"])
        assert node.skill_id == "test_skill"
        assert node.grade == 1
        assert node.prerequisites == ["prereq1"]

    def test_repr(self):
        node = CurriculumNode("test", grade=2)
        assert "test" in repr(node)


class TestGraphConstruction:
    def test_from_registry(self, graph):
        assert len(graph.nodes) == 4

    def test_nodes_loaded(self, graph):
        assert "g1_early_arithmetic_core" in graph.nodes
        assert "g2_addition_core" in graph.nodes

    def test_derive_edges(self, graph):
        g1 = graph.get_node("g1_early_arithmetic_core")
        assert g1 is not None
        assert "g2_addition_core" in g1.next_skills

    def test_roots(self, graph):
        roots = graph.get_roots()
        assert len(roots) == 1
        assert roots[0].skill_id == "g1_early_arithmetic_core"

    def test_leaves(self, graph):
        leaves = graph.get_leaves()
        assert len(leaves) == 1
        assert leaves[0].skill_id == "g3_time_measurement_core"

    def test_by_grade(self, graph):
        g1 = graph.get_by_grade(1)
        assert len(g1) == 1
        g2 = graph.get_by_grade(2)
        assert len(g2) == 2


class TestGraphQueries:
    def test_get_prerequisites(self, graph):
        prereqs = graph.get_prerequisites("g2_addition_core")
        assert len(prereqs) == 1
        assert prereqs[0].skill_id == "g1_early_arithmetic_core"

    def test_get_all_prerequisites(self, graph):
        all_prereqs = graph.get_all_prerequisites("g3_time_measurement_core")
        assert "g1_early_arithmetic_core" in all_prereqs
        assert "g2_addition_core" in all_prereqs
        assert "g2_subtraction_core" in all_prereqs

    def test_get_next_skills(self, graph):
        next_skills = graph.get_next_skills("g1_early_arithmetic_core")
        assert len(next_skills) == 1
        assert next_skills[0].skill_id == "g2_addition_core"

    def test_learning_path(self, graph):
        path = graph.get_learning_path("g1_early_arithmetic_core", "g3_time_measurement_core")
        assert path == [
            "g1_early_arithmetic_core",
            "g2_addition_core",
            "g2_subtraction_core",
            "g3_time_measurement_core",
        ]

    def test_learning_path_no_path(self, graph):
        path = graph.get_learning_path("g3_time_measurement_core", "g1_early_arithmetic_core")
        assert path == []

    def test_learning_path_not_found(self, graph):
        path = graph.get_learning_path("nonexistent", "g1_early_arithmetic_core")
        assert path == []


class TestValidation:
    def test_valid_graph(self, graph):
        result = graph.validate()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_no_cycles(self, graph):
        result = graph.validate()
        cycles = [e for e in result["errors"] if "Cyclic" in e]
        assert len(cycles) == 0

    def test_all_reachable(self, graph):
        result = graph.validate()
        unreachable = [w for w in result["warnings"] if "Unreachable" in w]
        assert len(unreachable) == 0

    def test_dangling_next_skill(self, tmp_path):
        registry = {
            "skills": [
                {
                    "skill_id": "a",
                    "grade": 1,
                    "prerequisites": [],
                    "next_skills": ["nonexistent"],
                },
            ],
        }
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        g = CurriculumGraph.from_skill_registry(path)
        result = g.validate()
        assert result["valid"] is False
        assert any("Dangling" in e for e in result["errors"])

    def test_cycle_detection(self, tmp_path):
        registry = {
            "skills": [
                {"skill_id": "a", "next_skills": ["b"]},
                {"skill_id": "b", "next_skills": ["c"]},
                {"skill_id": "c", "next_skills": ["a"]},
            ],
        }
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        g = CurriculumGraph.from_skill_registry(path)
        result = g.validate()
        assert result["valid"] is False
        assert any("Cyclic" in e for e in result["errors"])

    def test_stats(self, graph):
        result = graph.validate()
        stats = result["stats"]
        assert stats["total_nodes"] == 4
        assert stats["roots"] == 1
        assert stats["leaves"] == 1


class TestExport:
    def test_to_dict(self, graph):
        d = graph.to_dict()
        assert "nodes" in d
        assert "stats" in d
        assert len(d["nodes"]) == 4

    def test_to_mermaid(self, graph):
        mermaid = graph.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "g1_early_arithmetic_core" in mermaid
        assert "-->" in mermaid


class TestRealRegistry:
    def test_load_real_registry(self):
        from deeptutor.services.curriculum_graph import DATA_DIR, SKILL_REGISTRY_FILE
        if SKILL_REGISTRY_FILE.exists():
            graph = CurriculumGraph.from_skill_registry()
            assert len(graph.nodes) > 0
        else:
            pytest.skip("skill_registry.json not found")

    def test_real_validation(self):
        from deeptutor.services.curriculum_graph import SKILL_REGISTRY_FILE
        if not SKILL_REGISTRY_FILE.exists():
            pytest.skip("skill_registry.json not found")
        graph = CurriculumGraph.from_skill_registry()
        result = graph.validate()
        assert all("Cyclic" not in e for e in result["errors"])
