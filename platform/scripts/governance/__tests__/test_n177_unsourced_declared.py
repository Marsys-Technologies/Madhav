"""test_n177_unsourced_declared.py: the closed-list residual UNSOURCED_DECLARED of Ldgr.source_presence (SS N-177, 2026-10-07; registry Ldgr.source_presence revision 6).

Rows with no traceable source take the HONEST-LABEL form instead of FAIL: an asset whose declared row-level source (one K1 column, citation_state `unsourced`) DECLARES `residual: UNSOURCED_DECLARED` reads
Ldgr.source_presence as N/A under the ruled cause unsourced-declared (the repo's CEILING convention, like the Carr ceilings: a certified-at-a-ceiling reading printed as 'Ldgr: unsourced (declared)'), ONLY where the
detector CHECKS it on the live rows. Never a PASS, never a silent N/A, and no asset takes the label without the check: a row that carries a source refuses it (the cell reads as measured and names the contradiction).

Real SQL on a DISPOSABLE PostgreSQL: the three shapes the committed declarations use (bg_class_priors: source_ref NULL on every judged row, the lifetime rows excepted by prior_version; bg_kota_chakra_rings: every row's
citation says it is not traced; a mix), the contradiction, the excepted / empty / cancelled reads, the declaration validation, the rollup guard, the committed declarations.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n151_ldgr_source as n  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
LDGR = "Ldgr.source_presence"
TIMEOUT = "ERROR:  canceling statement due to statement timeout"
MARKER = "NOT YET traced to a primary ingested classical text"
RULE = "Ldgr.source_presence#measured:unsourced-declared"
WHY = "the rows are seeded literals that name no traceable source; the declaration says so on purpose"
EV = "platform/scripts/governance/asset_census.py:1"


def _decl(column="source_ref", marker=None, except_when=None, **kw):
    e = dict(column=column, kinds=["K1"])
    if except_when:
        e["except_when"] = except_when
    d = dict(level="row", columns=[e], citation_state="unsourced", residual=ac.UNSOURCED_DECLARED, why=WHY, evidence=EV)
    if marker:
        d["untraced_marker"] = marker
    d.update(kw)
    return d


def _mk(pg, monkeypatch, table, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} (id int PRIMARY KEY, {ddl})")
    for i, r in enumerate(rows):
        ac.psql(f"INSERT INTO {table} VALUES ({i + 1}, {r})")


def _check(src, table, cols, keys=(("id",),), **kw):
    return ac.source_declared_check("x", src, table, list(cols), keys=[list(k) for k in keys], **kw)[LDGR]


# ───────────────────────── the closed list ─────────────────────────

def test_the_closed_list_holds_exactly_unsourced_declared_and_its_ceiling_label_matches_the_postprocessor():
    import census_postprocess as cp
    assert ac.LDGR_RESIDUALS == ("UNSOURCED_DECLARED",) and ac.UNSOURCED_DECLARED == "UNSOURCED_DECLARED"
    assert ac.LDGR_RESIDUAL_CAUSE == {"UNSOURCED_DECLARED": "unsourced-declared"} and "unsourced-declared" in ac.NA_CAUSES[LDGR]
    assert ac.LDGR_RESIDUAL_CEILING["UNSOURCED_DECLARED"] == "Ldgr: unsourced (declared)"
    assert cp.CEILING_RULES[RULE] == ac.LDGR_RESIDUAL_CEILING["UNSOURCED_DECLARED"]                  # ONE label, pinned across the two modules
    assert RULE in ac.NA_RULE_DECISIONS and ac.NA_RULE_DECISIONS[RULE].startswith("N-177")
    assert cp.CEILING_RULES["Carr.D3#measured:single-derivation"] == "Carr: single-derivation" and cp.CEILING_RULES["Carr.D1#measured:transcription-not-verified"] == "D1: unverified transcription"
    ac.validate_na_rule_decisions()
    assert ac.CITATION_STATES == ("sourced", "sourced_ocr_unverified", "unsourced", "refuted") and ac.CITATION_CAPPED_STATES == ("unsourced", "refuted")      # the shared vocabulary is untouched


# ───────────────────────── the declaration form ─────────────────────────

@pytest.mark.parametrize("mut,why", [
    (dict(residual="SOMETHING_ELSE"), "residual must be null or one of"),
    (dict(citation_state="sourced"), "stands only on citation_state 'unsourced'"),
    (dict(level="table", kind="K1", citation="BPHS", locus="3.12", columns=None), "row-level declaration"),
    (dict(columns=[dict(column=c, kinds=["K1"]) for c in "abcde"]), "one to 4 entries"),          # N-235: a declared SET of up to 4 columns, no more
    (dict(columns=[dict(column="a", kinds=["K2"])]), "row-level source column(s)"),
    (dict(columns=[dict(column="a", kinds=["K1"]), dict(column="b", kinds=["K1"])], untraced_marker="NOT YET traced to a primary text"), "takes no untraced_marker"),
    (dict(untraced_marker="tbd"), "untraced_marker"),
    (dict(untraced_marker="x" * 201), "untraced_marker"),
])
def test_a_malformed_residual_declaration_is_refused(mut, why):
    d = _decl()
    d.update(mut)
    if d.get("columns") is None:
        d.pop("columns")
    bad = ac.source_declaration_problem(d)
    assert bad and why in bad, bad


def test_a_marker_without_a_residual_is_refused_and_a_sound_declaration_validates():
    d = _decl(marker=MARKER)
    assert ac.source_declaration_problem(d) is None and "untraced_marker" in ac.SOURCE_DECL_FIELDS and "residual" in ac.SOURCE_DECL_FIELDS
    d2 = dict(d)
    d2.pop("residual")
    d2["citation_state"] = "sourced"
    assert "untraced_marker is a field of a residual declaration" in ac.source_declaration_problem(d2)
    na = dict(na="no_data", why=WHY, evidence=EV, residual=ac.UNSOURCED_DECLARED)
    assert ac.source_declaration_problem(na) and "must be absent" in ac.source_declaration_problem(na)


def test_the_declarations_file_documents_the_new_fields():
    raw = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))
    assert raw["source_declaration_fields"] == list(ac.SOURCE_DECL_FIELDS)


# ───────────────────────── real SQL: the label is CHECKED on the rows ─────────────────────────

def test_REAL_SQL_every_judged_row_lacks_a_source_and_the_other_tiers_rows_are_excepted_so_the_label_stands(monkeypatch, disposable_pg):
    """bg_class_priors' shape: source_ref NULL on every seed row; the lifetime rows (prior_version ne_v01) carry a source and are excepted by declaration."""
    t = "n177_priors"
    _mk(disposable_pg, monkeypatch, t, "prior_version text, source_ref text, citation text",
        ["'1.0', NULL, 'BPHS yoga chapters'", "'1.0', NULL, 'Alias for configuration'", "'1.0', '', NULL", "'ne_v01', 'Publisher · 2021 · https://example.org/x', 'raw_figure: 1'"])
    try:
        rec = _check(_decl(except_when=dict(column="prior_version", equals="ne_v01")), t, ["id", "prior_version", "source_ref", "citation"])
        assert rec["v"] == NA and rec["cause"] == "unsourced-declared" and rec["declared"] is True and rec["citation_state"] == "unsourced"
        b = rec["unsourced_declared"]
        assert b["checked"] is True and b["verified"] is True and b["residual"] == "UNSOURCED_DECLARED" and b["carrying_a_source"] is False and b["judged_rows_exist"] is True and b["some_lacking"] is True
        assert "rows were not counted" in rec["measured"] and "Never a PASS" in rec["measured"] and "CHECKED on the live table" in rec["measured"]
        c = ac._check_contribution(LDGR, "L0", rec, None)
        assert c["v"] == NA and c["rule_id"] == RULE and c["decision"].startswith("N-177") and ac._na_released(LDGR, rec)
        # WITHOUT the exception the lifetime row (it carries a source) refuses the label: the rows decide, not the declaration
        rec2 = _check(_decl(), t, ["id", "prior_version", "source_ref", "citation"])
        assert rec2["v"] == NO_DET and rec2["declaration_disagreements"][0]["field"] == "source.residual" and "CONTRADICTED" in rec2["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_every_row_states_it_is_not_traced_so_the_marker_form_stands(monkeypatch, disposable_pg):
    """bg_kota_chakra_rings' shape: the citation column is populated on every row but each says NOT YET traced to a primary text."""
    t = "n177_kota"
    cite = "'Kota-Chakra ring table (Stambha 4/11/18/25th) — tier-(iii) secondary-source transcription; NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed.'"
    _mk(disposable_pg, monkeypatch, t, "citation text", [cite, cite, cite])
    try:
        assert _check(_decl(column="citation"), t, ["id", "citation"])["v"] == NO_DET                       # WITHOUT the marker the populated citation reads as a source: the label is not earned
        rec = _check(_decl(column="citation", marker=MARKER), t, ["id", "citation"])
        assert rec["v"] == NA and rec["unsourced_declared"]["some_marked"] is True and rec["unsourced_declared"]["some_lacking"] is False and MARKER in rec["measured"]
        up = _check(_decl(column="citation", marker=MARKER.upper()), t, ["id", "citation"])                  # the marker is matched case-insensitively
        assert up["v"] == NA
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_lacking_rows_and_marked_rows_may_mix(monkeypatch, disposable_pg):
    t = "n177_mix"
    _mk(disposable_pg, monkeypatch, t, "citation text", ["NULL", f"'x; {MARKER}'", "'not traced'", "'UNSOURCED - none'", "''"])
    try:
        rec = _check(_decl(column="citation", marker=MARKER), t, ["id", "citation"])
        assert rec["v"] == NA and rec["unsourced_declared"]["some_lacking"] is True and rec["unsourced_declared"]["some_marked"] is True
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_one_row_that_carries_a_source_refuses_the_label_and_the_cell_reads_as_measured(monkeypatch, disposable_pg):
    t = "n177_carry"
    _mk(disposable_pg, monkeypatch, t, "citation text", ["NULL", f"'x; {MARKER}'", "'Brihat Parashara Hora Shastra 3.12'", "NULL"])
    try:
        rec = _check(_decl(column="citation", marker=MARKER), t, ["id", "citation"])
        assert rec["v"] == NO_DET and rec["v"] != NA                                                      # the capped citation_state `unsourced` is never a PASS: NO_DETECTOR, never the residual
        d = rec["declaration_disagreements"][0]
        assert d["field"] == "source.residual" and d["declared"] == "UNSOURCED_DECLARED" and "at least 1 judged row carries a traceable source" in d["measured"] and '"id": 3' in d["measured"]
        assert "CONTRADICTED" in rec["measured"] and "unsourced_declared" not in rec
        assert not ac._na_released(LDGR, rec) and ac._check_contribution(LDGR, "L0", rec, None)["v"] == NO_DET
        # the same rows under an honest K1 declaration (state sourced) are measured as before: PARTIAL, the label hid nothing
        honest = dict(level="row", columns=[dict(column="citation", kinds=["K1"])], citation_state="sourced", why=WHY, evidence=EV)
        assert _check(honest, t, ["id", "citation"])["v"] == PARTIAL
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_table_whose_rows_all_carry_a_source_is_measured_never_labelled(monkeypatch, disposable_pg):
    """bg_class_lifetime_counts' shape: every judged row names its published statistic in source_ref: a sourced K1 reads PASS, and the residual form on the same rows is refused."""
    t = "n177_life"
    _mk(disposable_pg, monkeypatch, t, "prior_version text, source_ref text",
        ["'ne_v01', 'Demographic & Health Surveys · FR375 · 2021 · SP.DYN · all women 15-49 · https://dhsprogram.com/pubs/pdf/FR375/FR375.pdf'", "'ne_v01', 'WHO · 2019 · ind-7 · adults · doi:10.1097/JS9.0000000000001024'", "'1.0', NULL"])
    try:
        honest = dict(level="row", columns=[dict(column="source_ref", kinds=["K1"], except_when=dict(column="prior_version", equals="1.0"))], citation_state="sourced", why=WHY, evidence=EV)
        rec = _check(honest, t, ["id", "prior_version", "source_ref"])
        assert rec["v"] == PASS and rec["citation_state"] == "sourced" and rec["source"]["rows"] == 2 and rec["source"]["lacking"] == 0
        bad = _check(_decl(except_when=dict(column="prior_version", equals="1.0")), t, ["id", "prior_version", "source_ref"])
        assert bad["v"] == NO_DET and bad["declaration_disagreements"][0]["field"] == "source.residual"        # the label is never taken by rows that carry a source
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_every_row_excepted_or_no_row_at_all_is_vacuous_no_detector(monkeypatch, disposable_pg):
    t = "n177_vac"
    _mk(disposable_pg, monkeypatch, t, "prior_version text, source_ref text", ["'ne_v01', 'x 1'", "'ne_v01', NULL"])
    try:
        ex = dict(column="prior_version", equals="ne_v01")
        rec = _check(_decl(except_when=ex), t, ["id", "prior_version", "source_ref"])
        assert rec["v"] == NO_DET and "no judged row" in rec["measured"] and rec["v"] != NA
        ac.psql(f"DELETE FROM {t}")
        rec = _check(_decl(), t, ["id", "prior_version", "source_ref"])
        assert rec["v"] == NO_DET and "no judged row" in rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_marker_on_a_non_text_column_cannot_be_checked(monkeypatch, disposable_pg):
    t = "n177_arr"
    _mk(disposable_pg, monkeypatch, t, "citation text[]", ["ARRAY[]::text[]"])
    try:
        rec = _check(_decl(column="citation", marker=MARKER), t, ["id", "citation"])
        assert rec["v"] == NO_DET and "cannot be checked" in rec["measured"]
        ok = _check(_decl(column="citation"), t, ["id", "citation"])                                       # without a marker an empty array lacks a source: the label stands
        assert ok["v"] == NA
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────── the read is bounded and fails closed ─────────────────────────

def test_the_residual_statement_is_one_bounded_existence_read():
    sql = ac.unsourced_declared_sql("big_t", ac._ldgr_lacking("c", "text"), "c", MARKER, ["id"], "COALESCE((\"t\")::text = 'x', false)")
    assert "count(" not in sql and "ORDER BY" not in sql.upper() and "GROUP BY" not in sql.upper()
    assert sql.count('FROM "big_t"') == sql.count("LIMIT") == 4 and f"LIMIT {ac.LDGR_SAMPLE_LIMIT}) s" in sql and "EXISTS" in sql


class Fake:
    def __init__(self, answer=None, error=None):
        self.answer, self.error = answer, error

    def __call__(self, q):
        if "pg_attribute" in q:
            return json.dumps({"c": "text", "id": "integer"})
        if self.error:
            raise self.error
        return self.answer


def _fake_chk(monkeypatch, fake, src=None):
    monkeypatch.setattr(ac, "scalar", fake)
    monkeypatch.setattr(ac, "psql", lambda *a, **k: [])
    return _check(src or _decl(column="c"), "t", ["id", "c"])


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)")])
def test_a_cancelled_read_is_no_detector_with_the_cause_never_errored_never_the_label(monkeypatch, err):
    rec = _fake_chk(monkeypatch, Fake(error=err))
    assert rec["v"] == NO_DET and rec["v"] not in (ERRORED, NA, PASS) and "exceeded the statement timeout" in rec["measured"] and "neither a PASS nor a FAIL" in rec["measured"]


def test_any_other_failure_is_errored_and_a_malformed_answer_too(monkeypatch):
    assert _fake_chk(monkeypatch, Fake(error=ac.Unknown('ERROR:  relation "t" does not exist')))["v"] == ERRORED
    assert _fake_chk(monkeypatch, Fake(answer="not json"))["v"] == ERRORED
    assert _fake_chk(monkeypatch, Fake(answer=json.dumps(dict(judged=True))))["v"] == ERRORED


def test_a_verified_answer_reads_na_a_carrying_answer_does_not(monkeypatch):
    ok = json.dumps(dict(judged=True, carrying=[], lacking=True, marked=False, has_keys=True))
    assert _fake_chk(monkeypatch, Fake(answer=ok))["v"] == NA
    carry = json.dumps(dict(judged=True, carrying=[{"id": 4}], lacking=True, marked=False, has_keys=True))
    rec = _fake_chk(monkeypatch, Fake(answer=carry))
    assert rec["v"] != NA


# ───────────────────────── the rollup guard: a label is never taken without its verified block ─────────────────────────

def _na_rec(**block):
    b = dict(checked=True, verified=True, residual="UNSOURCED_DECLARED", judged_rows_exist=True, carrying_a_source=False, citation_state="unsourced")
    b.update(block)
    return dict(v=NA, cause="unsourced-declared", measured="x", declared=True, citation_state="unsourced", unsourced_declared=b)


def test_the_rollup_releases_the_label_only_with_the_verified_block():
    assert ac._check_contribution(LDGR, "L0", _na_rec(), None)["v"] == NA
    for bad in (dict(checked=False), dict(verified=False), dict(residual="OTHER"), dict(judged_rows_exist=False), dict(carrying_a_source=True), dict(citation_state="sourced")):
        c = ac._check_contribution(LDGR, "L0", _na_rec(**bad), None)
        assert c["v"] == NO_DET and "UNSOURCED_DECLARED" in c["reason"], bad
    bare = _na_rec()
    bare.pop("unsourced_declared")
    assert ac._check_contribution(LDGR, "L0", bare, None)["v"] == NO_DET
    assert ac._check_contribution(LDGR, "L0", dict(_na_rec(), citation_state=None), None)["v"] == NO_DET
    assert not ac._na_released(LDGR, bare) and ac._na_released(LDGR, _na_rec())


def test_the_label_is_a_ceiling_never_a_pass_in_the_cell():
    cells = ac.rollup_asset("L0", {LDGR: _na_rec()})
    ck = next(c for c in cells["Ldgr"]["checks"] if c["criterion"] == LDGR)
    assert cells["Ldgr"]["v"] == NA and ck["v"] == NA and ck["rule_id"] == RULE and ck["v"] != PASS


# ───────────────────────── the committed declarations ─────────────────────────

def test_the_three_assets_declare_what_their_rows_are_and_validate():
    d = ac.load_asset_declarations()
    for aid in ("bg_class_priors", "bg_kota_chakra_rings"):
        s = d[aid]["source"]
        assert s["residual"] == "UNSOURCED_DECLARED" and s["citation_state"] == "unsourced" and ac.source_declaration_problem(s) is None, aid
    assert d["bg_kota_chakra_rings"]["source"]["untraced_marker"] == MARKER and d["bg_kota_chakra_rings"]["source"]["columns"] == [dict(column="citation", kinds=["K1"])]
    assert d["bg_class_priors"]["source"]["columns"] == [dict(column="source_ref", kinds=["K1"], except_when=dict(column="prior_version", equals="ne_v01"))]
    life = d["bg_class_lifetime_counts"]["source"]
    assert "residual" not in life and life["citation_state"] == "sourced" and life["columns"][0]["except_when"] == dict(column="prior_version", equals="1.0") and ac.source_declaration_problem(life) is None
    kota = ac._load_sidecar_module("brahmagyan/l0_kota_chakra_rings.py", "_t_kota")
    assert MARKER in kota.CITATION                                                                        # the marker is the writer's own disclosure (the CITATION it binds to every row), not an invention
    assert 'PRIOR_VERSION = "ne_v01"' in (ac.SIDECAR / "brahmagyan" / "l0_class_lifetime_counts.py").read_text(encoding="utf-8")
    assert 'PRIOR_VERSION = "1.0"' in (ac.SIDECAR / "brahmagyan" / "l0_class_priors.py").read_text(encoding="utf-8")


def test_no_other_asset_declares_the_residual():
    d = ac.load_asset_declarations()
    assert sorted(a for a, e in d.items() if isinstance(e.get("source"), dict) and e["source"].get("residual")) == ["bg_class_priors", "bg_kota_chakra_rings", "bo_pratijna"]      # N-235 (3): bo_pratijna, over its two ledger columns (test_n233b_decl2)
