"""test_n233_carriage_declarations.py: the N-233 carriage declarations (declarations 1.62.0) are TRUE, and the assets that were refused are still refused (SS ruling N-233, task T1).

Eleven assets read Carr.D1 / D2 / D3 `NO_DETECTOR: not measured (applies)` in the final census because they declared no carriage nature. Each now declares the engine's CHECKED closed-list residual:

  unverified_transcription (applies D1; needs a declared K1 source)  bg_nakshatra, bg_reference, bg_prashna_rules, bg_gochara_citation_resolution
  single_derivation        (applies D3; refused where a reviewed D3 method serves the asset)
                                                                      bg_kp_sublord_division, bg_parihara_rules, ga_nakshatra, ga_sensitive, ga_medical, ga_vichara, bo_samvada
  per_witness_values false (Carr.D2 N/A, cause no-per-witness-values) on all ten.

Nothing here is a PASS: the cells read N/A under the declared rules, and the certified list prints the ceiling. Each declaration is anchored to the committed writer / seed source (AST or text anchors, no
code of the writer is trusted), the engine's own `carriage_declared_checks` is run on the committed declaration (the cell values), and every refusal (forgery) the engine makes is shown to bite.
The assets this task REFUSED to declare are pinned too (a later edit that adds a nature to them must come with the evidence this file says is missing).
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

NA, NO_DET, PASS = ac.NA, ac.NO_DET, ac.PASS
DECLS = ac.load_asset_declarations()
ROOT = ac.ROOT

D1 = ["bg_nakshatra", "bg_reference", "bg_prashna_rules", "bg_gochara_citation_resolution"]
D3 = ["bg_kp_sublord_division", "bg_parihara_rules", "ga_nakshatra", "ga_sensitive", "ga_medical", "ga_vichara", "bo_samvada"]
TEN = D1 + D3
JUDG = ["bg_class_priors", "bg_class_lifetime_counts", "bg_formula_constants", "bg_ghatana"]            # N-235 (b): ratified_judgment
REFUSED = {
    "ga_dashas": "an INDEPENDENT Vimshottari verifier runs in the build (ga_writers/_vimshottari_independent_verifier.py): single_derivation would be false for those rows",
    "bg_sarvatobhadra_grid": "not built (no rows): there is nothing to declare a carriage of",
    "bg_ephemeris_engine": "service probe owning no table: no carriage form exists for it",
    "bg_panchanga": "service probe owning no table: no carriage form exists for it",
}


def _e(aid):
    return json.loads(json.dumps(DECLS[aid]))


def _cells(aid, entry=None):
    e = entry or DECLS[aid]
    return ac.carriage_declared_checks(aid, e["carriage"], e.get("read_table") or aid, column_types=None, prose_columns=[], source=e.get("source"))


def _src(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _line(rel, n):
    return _src(rel).splitlines()[n - 1]


# ───────────────────────── the declarations and the cells they give ─────────────────────────

@pytest.mark.parametrize("aid", D1)
def test_the_d1_residual_reads_the_ceiling_cells_and_never_a_pass(aid):
    c = DECLS[aid]["carriage"]
    assert (c["applies"], c["nature"], c["per_witness_values"]) == ("D1", "unverified_transcription", False) and c.get("spec") is None and c.get("citation_state") is None
    got = _cells(aid)
    assert [(k, got[k]["v"], got[k]["cause"]) for k in ("Carr.D1", "Carr.D2", "Carr.D3")] == [("Carr.D1", NA, "transcription-not-verified"), ("Carr.D2", NA, "no-per-witness-values"), ("Carr.D3", NA, "not-the-declared-carriage")]
    assert "K1" in ac.source_kinds(DECLS[aid]["source"])          # the label needs a declared classical citation to be a transcription OF


@pytest.mark.parametrize("aid", D3)
def test_the_d3_residual_reads_the_ceiling_cells_and_never_a_pass(aid):
    c = DECLS[aid]["carriage"]
    assert (c["applies"], c["nature"], c["per_witness_values"]) == ("D3", "single_derivation", False) and c.get("spec") is None
    got = _cells(aid)
    assert [(k, got[k]["v"], got[k]["cause"]) for k in ("Carr.D1", "Carr.D2", "Carr.D3")] == [("Carr.D1", NA, "not-the-declared-carriage"), ("Carr.D2", NA, "no-per-witness-values"), ("Carr.D3", NA, "single-derivation")]
    assert aid not in ac._carriage_d3_served_assets()              # a reviewed D3 method serves neither: the second route would otherwise exist and the check be measured


@pytest.mark.parametrize("aid", TEN)
def test_every_evidence_pointer_is_a_code_line_that_exists_and_names_what_it_is_cited_for(aid):
    ev = DECLS[aid]["carriage"]["evidence"]
    path, line = ev.rsplit(":", 1)
    text = _line(path, int(line))
    assert text.strip() and not text.strip().startswith(("#", "--", '"""', "'''", "@register"))
    if not path.endswith(".py"):
        return                                                                                                  # a migration: the line exists and is not a comment
    tree = ast.parse(_src(path))
    docs = [n.body[0] for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str)]
    assert not any(d.lineno <= int(line) <= d.end_lineno for d in docs), "a docstring is not evidence"


def test_exactly_these_eleven_assets_gained_a_nature_and_the_refused_ones_still_have_none():
    have = sorted(a for a, e in DECLS.items() if isinstance(e.get("carriage"), dict) and e["carriage"].get("nature"))
    assert len(have) == 79 and set(TEN) <= set(have) and set(JUDG) <= set(have)
    for aid in REFUSED:
        assert not DECLS[aid]["carriage"].get("nature"), (aid, REFUSED[aid])


# ───────────────────────── anchors in the committed source (each says why the nature is TRUE) ─────────────────────────

def test_bg_nakshatra_is_a_hand_typed_literal_with_chapter_citations_and_no_passage_spec():
    import brahmagyan.l0_nakshatra as N
    assert len(N.NAKSHATRAS_ENRICHED) == 28 and len(N.PADAS) == 108
    assert all(str(r["classical_source"]).strip() for r in N.NAKSHATRAS_ENRICHED)                      # the declared K1 source column is populated by the literal itself
    assert _line("platform/python-sidecar/brahmagyan/l0_nakshatra.py", 30).startswith("NAKSHATRAS_ENRICHED")
    assert "ZERO LLM" in _src("platform/python-sidecar/brahmagyan/l0_nakshatra.py")


def test_bg_reference_is_a_hand_typed_literal_set_and_its_source_column_is_in_every_planet_row():
    import brahmagyan.l0_reference as R
    assert (len(R.PLANETS), len(R.SIGNS), len(R.GLOSSARY), len(R.TOPIC_TAGS)) == (11, 12, 364, 481)
    assert all(str(p["source_citation"]).strip() for p in R.PLANETS)
    assert _line("platform/python-sidecar/brahmagyan/l0_reference.py", 49).startswith("PLANETS")


def test_bg_prashna_rules_every_seed_rule_carries_a_classical_citation_and_the_source_declaration_is_the_target_tables_column():
    import brahmagyan.l0_prashna as P
    total = 0
    for name in ("PRASHNA_LAGNA_METHODS", "TAJIK_YOGAS", "SIGNIFICATORS", "FRUCTIFICATION_RULES", "SPECIAL_TECHNIQUES"):
        rows = getattr(P, name)
        total += len(rows)
        assert rows and all(isinstance(r, dict) and str(r.get("classical_citation") or "").strip() for r in rows), name
    assert total == 41
    s = DECLS["bg_prashna_rules"]["source"]
    assert ac.source_declaration_problem(s, DECLS["bg_prashna_rules"], "bg_prashna_rules") is None and s["columns"] == [{"column": "classical_citation", "kinds": ["K1"]}] and s["citation_state"] == "sourced"
    assert "All rules carry classical citations" in _src("platform/python-sidecar/brahmagyan/l0_prashna.py")


def test_bg_kp_sublord_division_is_derived_once_by_exact_arithmetic_and_only_the_star_lord_is_cross_checked():
    from fractions import Fraction
    import brahmagyan.l0_kp_sublord_division as K
    rows = K.build_divisions()
    assert len(rows) == 249
    assert abs(sum(float(r["end_longitude_deg"]) - float(r["start_longitude_deg"]) for r in rows) - 360.0) < 1e-8
    assert Fraction(120, 9) == sum(Fraction(y, 9) for y in (7, 20, 6, 10, 7, 18, 16, 19, 17))           # the nine sub spans of one nakshatra: the Vimshottari table over 9
    src = _src("platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py")
    assert _line("platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py", 196).startswith("def build_divisions(")            # the evidence is the sub-boundary derivation itself
    assert DECLS["bg_kp_sublord_division"]["carriage"]["evidence"].endswith("l0_kp_sublord_division.py:196")
    assert _line("platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py", 404).strip() == "verdict = verify_star_lords_against_reference(conn)"
    assert "star_lord" in src and src.count("verify_star_lords_against_reference(") == 2            # its def and its one call: the only cross-check, and it is of the star lord


def test_bg_parihara_rules_rows_are_joined_from_stored_rows_and_imported_tables_not_re_derived():
    rel = "platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py"
    src = _src(rel)
    assert "brahma_dosha_catalog" in src and "EVENT_TABLES" in src and _line(rel, 145).startswith("def fetch_parihara_rows")
    mods = {a.name.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}
    assert not ({"swisseph", "jhora", "pyjhora"} & mods), mods                                           # it imports no ephemeris: the rows come from stored rows


def test_ga_nakshatra_re_derivation_is_the_same_floor_division_so_the_writers_own_docstring_denies_independence():
    rel = "platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py"
    assert _line(rel, 113).strip() == "nak = int(lon // _NAK_ARC_DEG) + 1"
    src = _src(rel)
    assert "NOT an independent" in src and "WHY `single`, NOT `classical_match` or `two_pass_verified`" in src


def test_ga_sensitive_two_pass_exists_only_in_the_solar_upagraha_branch_and_every_other_row_is_stored_single():
    rel = "platform/python-sidecar/ga_writers/ga_sensitive_writer.py"
    src = _src(rel)
    calls = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "two_pass_verdict"]
    assert len(calls) == 1 and "upagraha_agree" in src                                                   # ONE call site: the upagraha branch
    assert _line(rel, 3193).strip().startswith("single = [r for r in rows if r.get(\"verification_pass_status\") == UNVERIFIED_DEFAULT]")
    assert "`single` is a permitted tier for" in src or "permitted tier" in src
    c = DECLS["ga_sensitive"]["carriage"]
    assert "EXCEPT the five solar upagraha" in c["why"] and "ARE independently re-derived" in c["why"] and "NOT claimed" in c["why"] and "does not measure" in c["why"]      # the exception is stated first, and single-derivation is disclaimed for those rows
    assert _line(rel, 675).strip() == "verdict = two_pass_verdict(True, upagraha_agree)" and c["evidence"].endswith("ga_sensitive_writer.py:675")


def test_ga_medical_reads_stored_condition_scores_and_the_l0_mapping_and_computes_no_position():
    src = _src("platform/python-sidecar/ga_writers/ga_medical_writer.py")
    mods = {a.name.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}
    assert "ga_condition_composite" in src and "bg_medical_mappings" in src and not ({"swisseph", "jhora", "pyjhora"} & mods), mods
    assert _line("platform/python-sidecar/ga_writers/ga_medical_writer.py", 350).strip() == '"indication_strength": indication_strength,'


def test_ga_vichara_imports_no_ephemeris_so_it_has_no_sky_route_to_re_derive_from():
    rel = "platform/python-sidecar/ga_writers/ga_vichara_writer.py"
    tree = ast.parse(_src(rel))
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not ({"swisseph", "jhora", "pyjhora", "panchang_engine"} & mods), mods
    assert "No new astronomical/positional computation (B.10)" in _src(rel)


def test_bo_samvada_is_a_view_definition_over_earlier_bodha_rows():
    rel = "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py"
    src = _src(rel)
    assert _line(rel, 62).startswith("_CREATE_VIEW_CLEAN") and "bodha_msr_signals" in src and "shadbala" in src.lower() and "preserved, not recreated" in src


# ───────────────────────── forgeries the engine must refuse or read red ─────────────────────────

def _validate(aid, mutate):
    e = _e(aid)
    mutate(e)
    return ac.validate_declarations(dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: e}))


@pytest.mark.parametrize("aid", D3)
def test_FORGERY_per_witness_values_true_a_spec_or_the_wrong_check_is_refused_on_a_d3_residual(aid):
    for mutate, msg in ((lambda e: e["carriage"].__setitem__("per_witness_values", True), "per_witness_values"), (lambda e: e["carriage"].__setitem__("spec", {"method": "x"}), "carries no `spec`"),
                        (lambda e: e["carriage"].__setitem__("applies", "D1"), "requires applies")):
        with pytest.raises(ac.DeclarationsError, match=msg):
            _validate(aid, mutate)


@pytest.mark.parametrize("aid", D3)
def test_FORGERY_a_d3_residual_on_an_asset_a_reviewed_method_serves_is_refused(aid, monkeypatch):
    monkeypatch.setattr(ac, "_carriage_d3_served_assets", lambda: {aid: "swisseph_sidereal_positions_v1"})
    e = _e(aid)
    with pytest.raises(ac.DeclarationsError, match="serves it"):
        ac.validate_declarations(dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: e}))
    got = ac.carriage_declared_checks(aid, e["carriage"], aid, column_types=None, prose_columns=[], source=e.get("source"))
    assert all(got[c]["v"] == NO_DET for c in ("Carr.D1", "Carr.D2", "Carr.D3"))               # and the measurement reads red, never the waiver


@pytest.mark.parametrize("aid", D1)
def test_FORGERY_unverified_transcription_without_a_k1_source_is_refused_and_reads_no_detector(aid):
    def drop(e):
        e["source"] = {"level": "table", "kind": "K2", "decision_id": "N-156", "why": "ratified rows of a decision", "evidence": "platform/scripts/governance/asset_census.py:1"}
    with pytest.raises(ac.DeclarationsError, match="unverified_transcription"):
        _validate(aid, drop)
    e = _e(aid)
    got = ac.carriage_declared_checks(aid, e["carriage"], aid, column_types=None, prose_columns=[], source={"level": "table", "kind": "K2", "decision_id": "N-156"})
    assert got["Carr.D1"]["v"] == NO_DET and got["Carr.D1"].get("declaration_disagreements")


@pytest.mark.parametrize("aid", TEN)
def test_FORGERY_an_evidence_pointer_that_does_not_exist_is_refused(aid):
    with pytest.raises(ac.DeclarationsError, match="evidence"):
        _validate(aid, lambda e: e["carriage"].__setitem__("evidence", "platform/python-sidecar/brahmagyan/no_such_file_n233.py:1"))


def test_the_closed_list_labels_these_residuals_print_in_the_certified_list():
    import census_postprocess as cp
    assert cp.CEILING_RULES["Carr.D3#measured:single-derivation"] == "Carr: single-derivation"
    assert cp.CEILING_RULES["Carr.D1#measured:transcription-not-verified"] == "D1: unverified transcription"
    for rid in ("Carr.D2#measured:no-per-witness-values", "Carr.D3#measured:single-derivation", "Carr.D1#measured:transcription-not-verified"):
        assert "N-156" in ac.NA_RULE_DECISIONS[rid]


# ───────────────────────── real SQL: the declared K1 source of bg_prashna_rules is TRUE on the rows its real seed writes ─────────────────────────

def test_REAL_WRITER_the_prashna_source_declaration_reads_pass_on_the_rows_the_seed_writes_and_fails_when_a_rule_loses_its_citation(disposable_pg, monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    import _formgap_support as fs
    point_psql_at(disposable_pg, monkeypatch)
    tables = ["bg_prashna_lagna_methods", "bg_prashna_tajik_yogas", "bg_prashna_significators", "bg_prashna_fructification_rules", "bg_prashna_special_techniques"]
    for t in tables:
        fs.psql(disposable_pg, f"DROP TABLE IF EXISTS {t} CASCADE")
        fs.psql(disposable_pg, fs.create_table_ddl(fs.MIG / "261_bg_prashna_rules_schema.sql", t))
    from brahmagyan.l0_prashna import seed_prashna_rules
    conn = psycopg.connect(disposable_pg.url, autocommit=True, row_factory=dict_row)
    try:
        counts = seed_prashna_rules(conn)
    finally:
        conn.close()
    assert counts["total_rules"] == 41
    src = DECLS["bg_prashna_rules"]["source"]
    cols = ["id", "classical_citation"]

    def check():
        return ac.source_declared_check("bg_prashna_rules", src, "bg_prashna_tajik_yogas", cols, rows=16, owned=["bg_prashna_tajik_yogas"], keys=[["yoga_id"]])["Ldgr.source_presence"]
    rec = check()
    assert rec["v"] == PASS and rec["citation_state"] == "sourced", rec["measured"]
    fs.psql(disposable_pg, "UPDATE bg_prashna_tajik_yogas SET classical_citation = '' WHERE yoga_id = (SELECT min(yoga_id) FROM bg_prashna_tajik_yogas)")
    rec = check()
    assert rec["v"] != PASS and rec["v"] in (ac.PARTIAL, ac.FAIL, NO_DET), rec["measured"]       # one rule lost its citation: the declaration no longer reads true
    for t in tables:
        fs.psql(disposable_pg, f"DROP TABLE IF EXISTS {t} CASCADE")


# ───────────────────────── N-235 (b): the four judgment seeds ─────────────────────────

@pytest.mark.parametrize("aid", JUDG)
def test_the_judgment_seeds_declare_ratified_judgment_under_n235_and_say_what_they_are(aid):
    c = DECLS[aid]["carriage"]
    assert c["nature"] == "ratified_judgment" and c["ruling"] == "N-235" and c["per_witness_values"] is False and "applies" not in c and c.get("spec") is None
    assert "system-authored" in c["why"] and "no second derivation" in c["why"] and "N-235" in c["why"]
    got = _cells(aid)
    assert [(k, got[k]["v"], got[k]["cause"]) for k in ("Carr.D1", "Carr.D2", "Carr.D3")] == [(k, NA, "ratified_judgment") for k in ("Carr.D1", "Carr.D2", "Carr.D3")]


@pytest.mark.parametrize("aid", JUDG)
def test_FORGERY_a_judgment_declaration_without_a_ruling_or_with_a_check_is_refused(aid):
    for mutate, msg in ((lambda e: e["carriage"].pop("ruling"), "ruling"), (lambda e: e["carriage"].__setitem__("ruling", "N-235 maybe"), "ruling"),
                        (lambda e: e["carriage"].__setitem__("applies", "D1"), "declares no check"), (lambda e: e["carriage"].__setitem__("evidence", "unverified:somewhere in the seed"), "evidence")):
        with pytest.raises(ac.DeclarationsError, match=msg):
            _validate(aid, mutate)


def test_ratified_judgment_is_a_released_na_now_that_the_engine_registers_its_rule():
    """N-235 (SS): the engine registers Carr.D1/D2/D3#measured:ratified_judgment (engine branch #3306), so a declared ratified_judgment seed citing N-235 reads ruled N/A and is released."""
    got = _cells("bg_formula_constants")
    assert all(ac._na_released(k, got[k]) for k in ("Carr.D1", "Carr.D2", "Carr.D3"))
    assert {r for r in ac.NA_RULE_DECISIONS if r.endswith("#measured:ratified_judgment")} == {"Carr.D1#measured:ratified_judgment", "Carr.D2#measured:ratified_judgment", "Carr.D3#measured:ratified_judgment"}
