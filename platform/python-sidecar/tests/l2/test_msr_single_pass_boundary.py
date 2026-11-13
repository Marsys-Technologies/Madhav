"""Synthetic checks of the MSR status projection and its tier comparator."""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from brahmagyan.verification_tiers import SINGLE
from brahmagyan.verification_vocab import canonical, is_verified

SIDECAR = Path(__file__).resolve().parents[2]
WRITERS = SIDECAR / "pipeline/orchestrator/writers"


def _node_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.FunctionDef):
        return node.name
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _load(source: Path, nodes: list[ast.stmt], scope: dict) -> dict:
    tree = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(tree, str(source), "exec"), scope)
    return scope


def load_projection(source: Path):
    """Use the exact status/lineage assignments and returned expressions without running a writer."""
    tree = ast.parse(source.read_bytes())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    full = functions["_build_signal_row"]
    [lineage] = [i for i, node in enumerate(full.body) if _node_name(node) == "constituent_facts"]
    [mirror] = [node for node in full.body if _node_name(node) == "epistemic_jsonb"]
    [returned] = [node.value for node in full.body if isinstance(node, ast.Return)]
    assert isinstance(returned, ast.Dict)
    field_names = {
        "constituent_facts_array", "epistemic_tier", "epistemic_jsonb",
        "verification_method", "verification_pass_status",
    }
    fields = [(key, value) for key, value in zip(returned.keys, returned.values)
              if isinstance(key, ast.Constant) and key.value in field_names]
    assert {key.value for key, _ in fields} == field_names
    keys, values = zip(*fields)
    [project] = ast.parse("def project(fact_row, ayanamsha_override=None, valid_fact_ids=None): pass").body
    project.body = full.body[:lineage + 1] + [
        mirror, ast.Return(value=ast.Dict(keys=list(keys), values=list(values))),
    ]
    return _load(source, [functions["_required_fact_text"], project], {
        "json": json, "SINGLE": SINGLE, "canonical": canonical,
    })["project"]


def load_detector(source: Path) -> dict:
    names = {
        "_count_one", "_VERIFICATION_TIER_RANKS", "_EXPLICIT_DIVERGENT_SQL",
        "_TIER_INVERSION_SQL", "count_divergent_signals",
    }
    nodes = [node for node in ast.parse(source.read_bytes()).body if _node_name(node) in names]
    assert {_node_name(node) for node in nodes} == names
    return _load(source, nodes, {"Any": Any, "logger": logging.getLogger(__name__)})


@pytest.mark.parametrize(("stored_tier", "emitted_tier"), [
    ("single_pass", "single"),
    ("single", "single"),
    ("classical_match", "classical_match"),
    ("two_pass_verified", "two_pass_verified"),
    ("divergent_flagged", "divergent_flagged"),
    ("documented_approximation", "documented_approximation"),
    ("computed_extension", "computed_extension"),
    ("pass", "pass"),
    ("PASS", "PASS"),
    ("fixture_unknown", "fixture_unknown"),
    (None, "documented_approximation"),
    ("", "documented_approximation"),
])
def test_only_the_new_verification_field_canonicalizes_the_known_alias(stored_tier, emitted_tier):
    project = load_projection(WRITERS / "bo_laksana.py")
    row = project({
        "fact_id": "fixture-primary",
        "fact_category": "fixture-category",
        "fact_key": "fixture-key",
        "verification_pass_status": stored_tier,
        "fact_value_jsonb": {"constituent_fact_ids": ["fixture-other", "fixture-unresolved"]},
    }, valid_fact_ids={"fixture-primary", "fixture-other"})
    assert row["verification_pass_status"] == emitted_tier
    assert row["verification_method"] == "L1_fact_projection"
    assert row["constituent_facts_array"] == ["fixture-primary", "fixture-other"]
    assert row["epistemic_tier"] == (stored_tier or "documented_approximation")
    assert json.loads(row["epistemic_jsonb"])["epistemic_tier"] == row["epistemic_tier"]
    assert is_verified(row["verification_pass_status"]) is (stored_tier == "two_pass_verified")


def test_detector_binds_both_spellings_at_the_canonical_rank_to_the_shared_map():
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")

    class FixtureConnection:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params):
            self.calls.append((sql, params))
            return self

        def fetchone(self):
            return (0,)

    conn = FixtureConnection()
    result = scope["count_divergent_signals"](conn, "fixture-chart")
    expected = [
        ("two_pass_verified", 3), ("classical_match", 2), ("single_pass", 1), ("pass", 2),
        ("documented_approximation", 1), ("single", 1), ("divergent_flagged", 0),
    ]
    assert result["count"] == 0 and result["error"] is None
    assert result["terms"]["tier_ranks"] == dict(expected)
    assert conn.calls[0] == (scope["_EXPLICIT_DIVERGENT_SQL"], ["fixture-chart"])
    sql, params = conn.calls[1]
    assert sql == scope["_TIER_INVERSION_SQL"]
    assert params == [[tier for tier, _ in expected], [rank for _, rank in expected], "fixture-chart"]
    assert "LEFT JOIN rank_map fr ON fr.status = cf.verification_pass_status" in sql
    assert "LEFT JOIN rank_map sr ON sr.status = s.verification_pass_status" in sql
