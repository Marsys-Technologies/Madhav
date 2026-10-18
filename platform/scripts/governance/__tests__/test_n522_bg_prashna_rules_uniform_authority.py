"""test_n522_bg_prashna_rules_uniform_authority.py: bg_prashna_rules declares uniform_authority WITHOUT `tables` (SS N-522).

bg_prashna_rules has a target table (bg_prashna_tajik_yogas), so the table-less form (`uniform_authority.tables`, only for an asset with NO target table) is refused by
asset_census.uniform_authority_measure_problem and Dens.served read NO_DETECTOR (census run 2). The declaration now has the shape of the precedents bg_yogas and bg_ghatana
(why + evidence only). Offline, no database: the real declarations file, the real validator / measure-time problem function and the real capability scan over the real serving roots.

  * the committed declaration carries no `tables` and passes the validator and the measure-time check;
  * the old shape (tables re-added) is refused with the table-less message and reads NO_DETECTOR through the same grading measure() runs (the mutation proof);
  * the real serving modules earn the structural uniform-authority PASS, which measure() then keeps only while the same run's Ldgr.source_presence reads PASS."""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

AID = "bg_prashna_rules"
TBL = "bg_prashna_tajik_yogas"
OWNED = ["bg_prashna_lagna_methods", "bg_prashna_tajik_yogas", "bg_prashna_significators", "bg_prashna_fructification_rules", "bg_prashna_special_techniques"]
TBL_COLUMNS = sorted(["id", "yoga_id", "yoga_name", "yoga_name_sa", "judgment_meaning", "formation_rule", "formation_rule_jsonb", "classical_citation", "is_fructification_indicator"])   # census run 2: target_columns (no tier column)
PRECEDENTS = ("bg_yogas", "bg_ghatana")


def _decl() -> dict:
    decls = ac.load_asset_declarations()
    return copy.deepcopy(decls.get("assets", decls)[AID])


def _grade(entry: dict, ldgr_v: str = ac.PASS) -> dict:
    """The Dens.served grading measure() runs for this asset (asset_census.py measure(): capability_scan, uniform_authority_measure_problem, _grade_dens, the NO_DETECTOR override, the Ldgr gate)."""
    cap = ac.capability_scan(ac.CAPS_ROOTS, list(dict.fromkeys([TBL] + OWNED + [AID])), shared=(), columns={TBL: TBL_COLUMNS}, outside_roots=ac.DENS_OUTSIDE_ROOTS)
    bad = ac.uniform_authority_measure_problem(entry, TBL, TBL_COLUMNS, AID, owned=OWNED, owned_columns={t: (TBL_COLUMNS if t == TBL else None) for t in OWNED})
    d = ac._grade_dens(cap, TBL, uniform_authority=(entry.get("uniform_authority") is not None and not bad))
    if bad:
        d = dict(v=ac.NO_DET, measured=f"NO_DETECTOR — the declared uniform_authority is refused ({bad}); never PASS (graded without it: {d['v']})")
    return ac.dens_uniform_authority_gate(d, dict(v=ldgr_v))


def test_the_committed_declaration_has_no_tables_key():
    ua = _decl()["uniform_authority"]
    assert "tables" not in ua and sorted(ua) == ["evidence", "why"], ua


def test_the_committed_declaration_is_sound_and_has_the_precedent_shape():
    entry = _decl()
    assert ac.uniform_authority_problem(entry, AID) is None
    assert ac.uniform_authority_measure_problem(entry, TBL, TBL_COLUMNS, AID, owned=OWNED, owned_columns={TBL: TBL_COLUMNS}) is None
    decls = ac.load_asset_declarations()
    decls = decls.get("assets", decls)
    for pid in PRECEDENTS:
        assert sorted(decls[pid]["uniform_authority"]) == ["evidence", "why"], pid


def test_the_old_shape_with_tables_is_refused_for_an_asset_with_a_target_table():
    """Mutation proof: re-adding `tables` (the pre-N-522 declaration) makes the measure-time check refuse it."""
    entry = _decl()
    entry["uniform_authority"]["tables"] = list(OWNED)
    bad = ac.uniform_authority_measure_problem(entry, TBL, TBL_COLUMNS, AID, owned=OWNED, owned_columns={TBL: TBL_COLUMNS})
    assert bad and "table-less form" in bad and "target table" in bad, bad
    d = _grade(entry)
    assert d["v"] == ac.NO_DET and "refused" in d["measured"] and "table-less form" in d["measured"], d


def test_dens_served_reads_the_structural_uniform_authority_pass_with_the_declaration_as_committed():
    d = _grade(_decl())
    assert d["v"] == ac.PASS and d.get("via") == "uniform_authority", d
    assert "uniform_authority declared" in d["measured"] and "no tier column required" in d["measured"], d
    assert "query_prashna_tajik_yogas.ts" in d["measured"], d       # the serving capability of the target table is among the credited modules


def test_the_pass_is_withheld_to_partial_unless_the_same_runs_source_presence_reads_pass():
    d = _grade(_decl(), ldgr_v=ac.PARTIAL)
    assert d["v"] == ac.PARTIAL and "PASS WITHHELD" in d["measured"], d
