"""test_r79_deterministic_criterion_lookup.py — R79 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 re-scope).

Originally "substance-key dedupe with alias resolution"; D4 (§D4, adopted 2026-09-27) re-scopes it,
not withdraws it: "deterministic lookup on (asset, scope, registered criterion)". The four family
aliases (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`,
`Carr.D1|D2|D3`≡`Carr.detector`, `Completeness.*`≡`Complete.*`) become one-time crosswalk entries
consumed only by the R81 migration script — never a runtime alias table here. `gap_id_for` derives
the `<asset>-<Gate>.<check>` id (with an optional scope suffix); `lookup_criterion` is the
deterministic (asset, scope, criterion) -> (gap_id, registry entry) resolution, returning None for
an unregistered criterion rather than inventing one.

Fails without the fix: `gap_id_for` / `lookup_criterion` do not exist.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


def test_gap_id_for_matches_the_census_own_pre_existing_form():
    assert ac.gap_id_for("bg_ontology", "Earn.build_record") == "bg_ontology-Earn.build_record"


def test_gap_id_for_appends_a_scope_suffix_when_chart_scoped():
    assert ac.gap_id_for("ga_prashna", "Build.completion", "482012f1") == "ga_prashna-Build.completion@482012f1"


def test_lookup_criterion_is_deterministic_on_asset_scope_and_criterion():
    result = ac.lookup_criterion("bg_ontology", None, "Earn.build_record")
    assert result is not None
    gap_id, entry = result
    assert gap_id == "bg_ontology-Earn.build_record"
    assert entry["gate"] == "Earn" and entry["check"] == "build_record"
    # Same inputs -> same output, every time (no hidden state, no aliasing table consulted).
    assert ac.lookup_criterion("bg_ontology", None, "Earn.build_record") == result


def test_lookup_criterion_returns_none_for_an_unregistered_criterion_rather_than_inventing_one():
    assert ac.lookup_criterion("bg_x", None, "Nonexistent.criterion") is None


def test_no_runtime_family_alias_resolution_specific_and_generic_are_never_conflated():
    """D4: the four family aliases are migration-time crosswalk entries only. At runtime,
    Completeness.depth.dasha_link and Complete.depth (its generic placeholder) must resolve to two
    DIFFERENT gap ids for the same asset — lookup_criterion must never silently redirect one onto the
    other. (The Carr.D1/Carr.detector pair this test used was retired at REGISTRY_REVISION 8; a retired
    criterion resolves to None, asserted in test_e6_i_*.)"""
    d1 = ac.lookup_criterion("bg_ontology", None, "Completeness.depth.dasha_link")
    generic = ac.lookup_criterion("bg_ontology", None, "Complete.depth")
    assert d1 is not None and generic is not None
    assert d1[0] != generic[0], "the specific and the generic criterion must not resolve to the same gap_id"
    assert d1[1] is not generic[1]


def test_family_alias_source_criteria_from_r79_s_original_description_are_themselves_unregistered():
    """The ORIGINAL alias names (Vocab.rule1.alias, Dens.density_contract) are not registered
    criteria in their own right — R79's crosswalk resolves them to their canonical registered form
    (Vocab.alias, Dens.served) only inside the one-time R81 migration script, never here."""
    assert ac.registered_criterion("Vocab.rule1.alias") is None
    assert ac.registered_criterion("Dens.density_contract") is None
    assert ac.lookup_criterion("bg_ontology", None, "Vocab.rule1.alias") is None
    assert ac.lookup_criterion("bg_ontology", None, "Dens.density_contract") is None
