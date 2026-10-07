"""N-189/N-194 (CLAUDE.md N.7 items 4 and 6, N.8): `bo_anveshana` wrote the literal "low" as
epistemic_jsonb.ayanamsha_fragility on every discovery of every chart, with no detector behind it.
The writer mines each ayanamsha in isolation, so it holds no cross-ayanamsha comparison for a
discovery: the field is NULL with a stated reason code in the same leaf group, never a constant."""
from __future__ import annotations

import ast
import inspect
import json

from pipeline.orchestrator.writers import bo_anveshana as W

_NOW = "2026-10-07T00:00:00+00:00"


def _discovery(**over):
    kw = dict(
        chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1", now=_NOW,
        discovery_class="latent_insight", discovery_subsystem="ga_x",
        non_obviousness=0.5, consequence=0.6,
        constituent_refs=["sig-1"], reasoning_chain=[], why_misses="w", domains=["career"],
        surface="s", depth="d", delta="x", hypothesis="h", cross_subsystem=False,
        cross_subsystem_refs=None, corroborating_methods=["non_obviousness"],
        meaningfulness_basis="classical_form::yoga", surface_salience=0.1, rank=0.5,
    )
    kw.update(over)
    return W._make_discovery(**kw)


def test_discovery_ayanamsha_fragility_is_null_with_a_reason_code_not_a_constant_grade():
    ep = json.loads(_discovery()["epistemic_jsonb"])
    assert ep["ayanamsha_fragility"] is None, ep
    assert ep["ayanamsha_fragility_reason"] == W.AYANAMSHA_FRAGILITY_NOT_ASSESSED
    assert ep["confidence"] == 0.7


def test_every_discovery_class_and_ayanamsha_carries_the_same_honest_null():
    for cls in ("latent_insight", "embedding_outlier", "distributional_anomaly",
                "cross_subsystem_root", "structural_hole"):
        for aya in W.CANONICAL_AYAS:
            ep = json.loads(_discovery(discovery_class=cls, aya=aya)["epistemic_jsonb"])
            assert ep["ayanamsha_fragility"] is None


def test_discovery_identity_is_unchanged_by_the_epistemic_leaf():
    """discovery_id hashes (chart, aya, class, subsystem, refs, hypothesis): the leaf is outside it."""
    assert _discovery()["discovery_id"] == _discovery()["discovery_id"]
    assert _discovery()["discovery_id"] != _discovery(hypothesis="other")["discovery_id"]


def test_no_grade_literal_is_assigned_to_ayanamsha_fragility_anywhere_in_the_writer():
    tree = ast.parse(inspect.getsource(W))
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "ayanamsha_fragility":
                    assert isinstance(v, ast.Constant) and v.value is None, ast.unparse(v)
