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


TOKENS = {
    "bg_cohort": ["bg_synthetic_cohort", "bg_synthetic_cohort_md", "bg_cohort"], "bg_concordance": ["classical_attributions", "bg_concordance"],
    "bo_samskara": ["bodha_signal_embeddings", "bo_samskara"], "bg_reference": ["reference_planets", "bg_reference"], "bg_sarvatobhadra_grid": ["bg_sarvatobhadra_grid"],
    "bg_vidhi_floors": ["vidhi_floor_items", "bg_vidhi_floors"], "bg_vidhi_primitives": ["vidhi_primitives", "bg_vidhi_primitives"],
    "ga_fact_identity": ["chart_fact_identity", "ga_fact_identity"], "bo_grounding": ["bodha_grounding_matches", "bo_grounding"],
    "bg_gochara_citation_resolution": ["bg_gochara_citation_resolution"], "bg_ephemeris": ["ephemeris_daily", "bg_ephemeris"],
    "bg_ephemeris_engine": ["bg_ephemeris_engine"], "bg_panchanga": ["bg_panchanga"],
}
OWNERS = {"bg_class_priors": ("bg_class_lifetime_counts", "brahma_class_priors"), "bg_texts": ("bg_text_index", "classical_text_chunks")}


@pytest.mark.parametrize("aid", sorted(TOKENS))
def test_committed_none_and_reads_declarations_agree_with_the_real_serving_tree(aid):
    decl = ac.load_asset_declarations()[aid]
    cap = ac.capability_scan(ac.CAPS_ROOTS, TOKENS[aid], shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS)
    rec = ac.dens_not_served_record(aid, decl, None, cap, table_shared=False)
    assert rec["v"] == ac.NA, (aid, rec["measured"])
    assert _rollup(rec)["v"] == ac.NA


@pytest.mark.parametrize("aid", sorted(OWNERS))
def test_committed_owner_declarations_name_a_sibling_that_shares_the_table(aid):
    decl = ac.load_asset_declarations()
    owner, table = OWNERS[aid]
    assert decl[aid]["dens_not_served"]["owned_by"] == owner and decl[owner].get("dens_not_served") is None
    rec = ac.dens_not_served_record(aid, decl[aid], table, dict(scanned=True), table_shared=True,
                                    owner_row=dict(target_table=table), owner_entry=decl[owner])
    assert rec["v"] == ac.NA and rec["cause"] == "dens-owned-by-sibling", rec


def test_every_committed_dens_not_served_declaration_is_covered_here():
    decl = ac.load_asset_declarations()
    declared = sorted(a for a, e in decl.items() if e.get("dens_not_served") is not None)
    assert declared == sorted(set(TOKENS) | set(OWNERS)), declared
