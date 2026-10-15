"""test_dens_not_served_committed.py — SS N-211: the committed `dens_not_served` declarations agree with the real serving tree (a future served select of a declared-unserved table, or a
change to a declared internal read, breaks this test and the census cell reads FAIL).

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_not_served_committed.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


def _rollup(rec):
    return ac.rollup_asset("L0", {"Dens.served": rec})["Dens"]


# asset -> (tokens the census scans, table or None, registry asset_kind): the tokens are the asset's target table, count_sql tables and id
TOKENS = {
    "bg_cohort": (["bg_synthetic_cohort", "bg_synthetic_cohort_md", "bg_cohort"], "bg_synthetic_cohort", "data"),
    "bg_concordance": (["classical_attributions", "bg_concordance"], "classical_attributions", "data"),
    "bo_samskara": (["bodha_signal_embeddings", "bo_samskara"], "bodha_signal_embeddings", "data"),
    "bg_reference": (["reference_planets", "bg_reference"], "reference_planets", "data"),
    "bg_vidhi_floors": (["vidhi_floor_items", "bg_vidhi_floors"], "vidhi_floor_items", "data"),
    "bg_vidhi_primitives": (["vidhi_primitives", "bg_vidhi_primitives"], "vidhi_primitives", "data"),
    "ga_fact_identity": (["chart_fact_identity", "ga_fact_identity"], "chart_fact_identity", "data"),
    "bo_grounding": (["bodha_grounding_matches", "bo_grounding"], "bodha_grounding_matches", "data"),
    "bg_ephemeris_engine": (["bg_ephemeris_engine"], None, "service"),
    "bg_panchanga": (["bg_panchanga"], None, "service"),
}
OWNERS = {}          # the review (finding 5) removed the one owned_by declaration (bg_texts -> bg_text_index): bg_text_index selects fewer rows than bg_texts, so the pair is refused


@pytest.mark.parametrize("aid", sorted(TOKENS))
def test_committed_none_declarations_agree_with_the_real_serving_tree_under_the_strict_probe(aid):
    """The same scan measure() runs for a dens_not_served asset: the STRICT outside probe (no knowledge/ carve-out, table names passed to calls), JavaScript included. A new reaching
    occurrence anywhere, in any form, breaks this test and reads NO_DETECTOR in the census."""
    toks, table, kind = TOKENS[aid]
    decl = ac.load_asset_declarations()[aid]
    cap = ac.capability_scan(ac.CAPS_ROOTS, toks, shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS, service=(kind == "service"),
                             outside_exclude=ac.DENS_STRICT_EXCLUDE, table_tokens=[t for t in toks if t != aid])
    rec = ac.dens_not_served_record(aid, decl, table, cap, table_shared=False, asset_kind=kind)
    assert rec["v"] == ac.NA, (aid, rec["measured"])
    assert _rollup(rec)["v"] == ac.NA
    assert sorted(f"{p}:{n}#{h}" for p, n, h in cap["reach_at"]) == sorted(decl["dens_not_served"]["reaches"])


def test_the_assets_the_review_rejected_declare_nothing():
    decl = ac.load_asset_declarations()
    for aid in ("bg_class_priors", "bg_gochara_citation_resolution", "bg_ephemeris", "bg_texts"):
        assert decl[aid].get("dens_not_served") is None, aid


def test_every_committed_dens_not_served_declaration_is_covered_here():
    decl = ac.load_asset_declarations()
    declared = sorted(a for a, e in decl.items() if e.get("dens_not_served") is not None)
    assert declared == sorted(set(TOKENS) | set(OWNERS)), declared
