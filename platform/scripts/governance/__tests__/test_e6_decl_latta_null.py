"""test_e6_decl_latta_null.py: DECL-LATTA-NULL (declarations 1.11.0): bg_phaladeepika_latta declares its `null_convention`.

The convention: effect_description is the one nullable column (reserved empty EXACTLY on Mars and Saturn: the passage gives them no effect clause); four constant
columns (table_version, affliction_condition, source_citation, verse_ref) declared constant WITHOUT pinned values (the live values are read, so the corrected rebuild
passes); created_at a declared write-time stamp column (NOT NULL timestamptz, one shared value allowed, sentinels FAIL), never a constant claim; no allowed_literals.

Part 1 validator and pinned evidence lines. Part 2 REAL detectors on a disposable Postgres built from the 8 corpus rows: PASS with the earned lift only, the mutation
tests (a NULL effect on a non-reserved graha, a populated Mars/Saturn, a placeholder, a varying constant, a sentinel/nullable stamp), the live-values tests, the
ELEVATED reader's lift check through the real `null_lift_earned`, and the cell diff across ALL L0 assets of the saved census."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_decl_latta as dl  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_e6_s1_elevation_reader as rd  # noqa: E402
from test_e6_s1_elevation_reader import real_registry  # noqa: E402,F401  (its autouse fixture: the reader tests' real registry)
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

AID, COLS, ROWS = dl.AID, dl.COLS, dl.ROWS
PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
SD, BR = "Null.schema_default", "Null.blank_rows"
DECL, ENTRY, NC = dl.DECL, dl.ENTRY, dl.ENTRY["null_convention"]
ROOT = ac.ROOT
MIG = "platform/supabase/migrations/528_bg_phaladeepika_vedha.sql"
WRITER = "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py"
TYPES = {"table_version": "text", "graha": "text", "count_from_graha": "smallint", "direction": "text", "effect_description": "text", "affliction_condition": "text",
         "source_citation": "text", "verse_ref": "text", "created_at": "timestamp with time zone"}
TEXT_COLS = ["table_version", "graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref"]
R = dict(target_table=AID, count_sql=f"SELECT count(*) FROM {AID}")
CAT = dict(exists={AID}, cols={AID: COLS}, keys={AID: [["table_version", "graha"]]}, views=set(), types={AID: TYPES}, defaults={AID: {"created_at": "now()"}}, types_error=None)
SAVED = dl.SAVED
OTHER_CITATION = "[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG338-339"


def _doc(mutate):
    d = copy.deepcopy(DECL)
    mutate(d["assets"][AID]["null_convention"])
    return d


def _refused(mutate, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(mutate))


def _line(ptr_or_path, n=None):
    rel, ln = (ptr_or_path.rsplit(":", 1) if n is None else (ptr_or_path, n))
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()[int(ln) - 1]


# ───────────────────────── Part 1: the entry ─────────────────────────

def test_the_file_is_1_11_0_the_validator_accepts_it_and_only_this_asset_changed_its_entry_and_the_description_names_it():
    assert DECL["version"] == "1.11.0"
    ac.validate_declarations(DECL)
    sentence = DECL["description"].split("Version 1.11.0 (DECL-LATTA-NULL)", 1)[1]
    assert "bg_phaladeepika_latta's entry ONLY" in sentence and "no other asset or structure changed" in sentence
    assert [a for a, e in DECL["assets"].items() if "null_convention" in e] == [AID]


def test_the_convention_is_what_the_strategist_ruled():
    assert NC["table"] == AID and "allowed_literals" not in NC
    n, = NC["nullable"]
    assert n["column"] == "effect_description" and "Mars and Saturn" in n["means"] and "reserved empty" in n["means"]
    assert n["scope"] == {"key_column": "graha", "null_for": ["Mars", "Saturn"], "mode": "exactly"}
    assert [c["column"] for c in NC["constants"]] == ["table_version", "affliction_condition", "source_citation", "verse_ref"]
    assert all("value" not in c for c in NC["constants"])                  # live values are read, never pinned: the corrected rebuild must pass
    assert [c["column"] for c in NC["stamp_columns"]] == ["created_at"]
    st = NC["stamp_columns"][0]["why"]
    assert "write time" in st and "one seed transaction" in st and "not a constant claim" in st
    assert "created_at" not in [c["column"] for c in NC["constants"]] and "created_at" != n["column"]
    assert "Ketu has no row" in NC["why"] and "Mars and Saturn" in NC["why"]
    for word in ("verbatim", "accurate", "exact"):
        assert not any(word in t.lower() for t in dl._reasons(NC)), word


def test_every_evidence_pointer_and_supporting_line_is_pinned_to_its_content():
    assert NC["evidence"] == f"{MIG}:109" and re.match(r"\s*effect_description\s+TEXT,", _line(NC["evidence"]))          # the one nullable column
    for n, tok in ((105, "table_version"), (106, "graha"), (110, "affliction_condition"), (111, "source_citation"), (112, "verse_ref")):
        assert re.match(rf"\s*{tok}\s+TEXT\s+NOT NULL", _line(MIG, n)), n                                              # the constants and the key are NOT NULL text
    assert re.match(r"\s*created_at\s+TIMESTAMPTZ NOT NULL DEFAULT now\(\)", _line(MIG, 113))                          # the stamp: NOT NULL timestamptz
    assert re.match(r"\s*count_from_graha\s+SMALLINT\s+NOT NULL", _line(MIG, 107))
    assert '"Mars"' in _line(WRITER, 124) and _line(WRITER, 124).rstrip().endswith("None),")                           # the reserved-empty rows of the writer
    assert '"Saturn"' in _line(WRITER, 126) and _line(WRITER, 126).rstrip().endswith("None),")
    assert "LATTA_ROWS" in _line(WRITER, 122)


@pytest.mark.parametrize("mutate, match", [
    (lambda nc: nc["constants"].append(dict(column="created_at", why="one shared write time for every row of the set")), "stamp column AND"),
    (lambda nc: nc["nullable"].append(dict(column="created_at", means="the write time is not recorded for this row")), "stamp column AND"),
    (lambda nc: nc["stamp_columns"][0].__setitem__("why", ""), "stamp_columns"),
    (lambda nc: nc["stamp_columns"][0].__setitem__("why", "placeholder timestamp for the seed"), "stamp_columns"),
    (lambda nc: nc["stamp_columns"][0].__setitem__("column", "created at"), "stamp_columns"),
    (lambda nc: nc["stamp_columns"].append(dict(column="created_at", why="the write time of the seed transaction")), "twice"),
    (lambda nc: nc["constants"][0].__setitem__("why", ""), "constants"),
    (lambda nc: nc["constants"][2].__setitem__("why", "TBD later maybe"), "constants"),
    (lambda nc: nc.__setitem__("why", "short"), "null_convention.why"),
    (lambda nc: nc.__setitem__("evidence", "TBD"), "evidence"),
    (lambda nc: nc.__setitem__("evidence", f"{MIG}:99999"), "line 99999"),
    (lambda nc: nc.__setitem__("evidence", "platform/supabase/migrations/no_such.sql:1"), "evidence"),
    (lambda nc: nc["nullable"][0].__setitem__("means", "N/A"), "means"),
    (lambda nc: nc["nullable"][0].__setitem__("means", ""), "means"),
    (lambda nc: nc["nullable"][0]["scope"].__setitem__("mode", "sometimes"), "mode"),
    (lambda nc: nc["nullable"][0]["scope"].__setitem__("key_column", "effect_description"), "key_column"),
    (lambda nc: nc.__setitem__("allowed_literals", [dict(column="effect_description", values=["None"], why="a real value of the column")]), "nullable"),
])
def test_a_malformed_convention_is_refused(mutate, match):
    _refused(mutate, match)


# ───────────────────────── Part 2: REAL detectors on a disposable Postgres ─────────────────────────

def _measure(monkeypatch, pg, extra=(), ddl=(), entry=None):
    """Null.schema_default / Null.blank_rows (and the convention block) measured by the REAL glue on the 8 corpus rows; `ddl` runs before the rows are loaded, `extra` after."""
    setup = dl._setup()
    s3._real(monkeypatch, pg, setup[:1] + list(ddl) + setup[1:] + list(extra))
    return ac._measure_prose(AID, entry or ENTRY, R, None, CAT, [], set(), (), set())


def _text(m, crit=BR):
    return m[crit]["measured"]


def test_REAL_the_eight_corpus_rows_read_pass_on_both_checks_with_the_earned_lift_only(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg)
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS
    for c in (SD, BR):
        blk = m[c]["null_convention"]
        assert blk["declared"] is True and blk["verified"] is True and blk["v"] == PASS and blk["table"] == AID
        assert blk["columns"] == ["effect_description"] and blk["stamp_columns"] == ["created_at"]
        assert blk["schema_default_clean"] is True and blk["blank_rows_clean"] is True and "PASS earned by the declared null convention" in m[c]["measured"]
        assert ac.null_lift_problem(m[c]) is None
    assert ac.null_lift_earned(SD, m[SD], m) and ac.null_lift_earned(BR, m[BR], m)
    cell = ac.rollup_asset("L0", m)["Null"]
    assert cell["v"] == PASS and all(c.get("null_convention_verified") is True for c in cell["checks"])
    msr = m[BR]["measured"]
    assert "NULL only in the declared nullable column(s) effect_description" in msr and "NULL exactly on Mars, Saturn" in msr
    assert "stamp columns (write-time, constant test exempted" in msr and "4 declared constant column(s) constant, no other column constant" in msr


def test_REAL_the_all_text_column_fallback_test_ran_on_the_real_rows_and_the_numeric_count_is_not_a_sentinel_target(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, dl._setup())
    own = {AID: (COLS, TYPES, {"created_at": "now()"})}
    conv = ac.null_convention_check(NC, own, {AID}, ac._table_scope(AID, R, own, set()))
    assert conv["v"] == PASS
    blk = conv["convention"]
    assert sorted(blk["fallback_checked_columns"]) == sorted(TEXT_COLS)                 # table_version, graha, direction, effect_description, affliction_condition, source_citation, verse_ref
    assert blk["fallbacks"] == {} and blk["undeclared_nulls"] == {} and blk["undeclared_constants"] == [] and blk["constant_violations"] == []
    assert blk["fallback_not_applicable"] == ["count_from_graha"] and blk["allowed_literals_in_force"] == [] and blk["stamp_nulls"] == {} and blk["stamp_sentinels"] == {}
    assert blk["scope_violations"] == {} and blk["unscoped_null_columns"] == []
    s = ac.NULL_NUMERIC_TYPES      # smallint NOT NULL is not declared-nullable: the 0 sentinel never applies to it
    assert "smallint" in s and not ac._null_fb_possible("num", False)


def test_REAL_no_real_value_collides_with_a_placeholder_so_no_allowed_literals_are_needed(monkeypatch, disposable_pg):
    for r in ROWS:
        for c in TEXT_COLS:
            if r[c] is not None:
                assert not ac._null_placeholder_text(r[c]) and r[c].strip(), (r["graha"], c)
    assert "allowed_literals" not in NC and _measure(monkeypatch, disposable_pg)[BR]["v"] == PASS


# ── (c) a NULL effect on a graha that is not reserved ──

@pytest.mark.parametrize("graha", ["Sun", "Venus", "Rahu", "Moon", "Jupiter", "Mercury"])
def test_REAL_MUTATION_a_null_effect_on_a_non_reserved_graha_fails_null(monkeypatch, disposable_pg, graha):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = NULL WHERE graha = '{graha}';"])
    assert m[BR]["v"] == FAIL and ac.rollup_asset("L0", m)["Null"]["v"] == FAIL
    assert "declared null convention violated" in _text(m) and f"effect_description: NULL outside the declared keys on 1 row(s) (keys: {graha})" in _text(m)
    assert not ac.null_lift_earned(BR, m[BR], m) and not ac.null_lift_earned(SD, m[SD], m)


def test_REAL_MUTATION_the_exact_failure_text_for_sun(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = NULL WHERE graha = 'Sun';"])
    assert ("breaks its declared null convention: effect_description: NULL outside the declared keys on 1 row(s) (keys: Sun)") in _text(m)


# ── (d) a reserved graha populated, mode exactly ──

@pytest.mark.parametrize("graha", ["Mars", "Saturn"])
def test_REAL_MUTATION_a_populated_reserved_graha_fails_never_a_silent_pass(monkeypatch, disposable_pg, graha):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = 'Misery.' WHERE graha = '{graha}';"])
    assert m[BR]["v"] == FAIL and ac.rollup_asset("L0", m)["Null"]["v"] == FAIL
    assert f"effect_description: a value on reserved-NULL key(s) {graha} (1 row(s); mode exactly)" in _text(m)
    assert not ac.null_lift_earned(BR, m[BR], m)


def test_REAL_MUTATION_both_reserved_populated_and_a_null_for_venus_together_name_every_defect(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = 'Misery.' WHERE graha IN ('Mars','Saturn');",
                                                f"UPDATE {AID} SET effect_description = NULL WHERE graha = 'Venus';"])
    t = _text(m)
    assert m[BR]["v"] == FAIL and "NULL outside the declared keys on 1 row(s) (keys: Venus)" in t and "a value on reserved-NULL key(s) Mars, Saturn (2 row(s); mode exactly)" in t


def test_REAL_MUTATION_a_placeholder_in_effect_description_fails(monkeypatch, disposable_pg):
    for lit in ("N/A", "none", " ", "TBD", "-", "unknown"):
        m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = '{lit}' WHERE graha = 'Sun';"])
        assert m[BR]["v"] == FAIL and "literal fallback" in _text(m) and "effect_description (1 row(s))" in _text(m), lit
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET effect_description = '' WHERE graha = 'Mars';"])        # an empty string on a reserved row: a fallback AND a valued reserved key
    assert m[BR]["v"] == FAIL


def test_REAL_MUTATION_a_placeholder_in_any_other_text_column_fails(monkeypatch, disposable_pg):
    for col in ("affliction_condition", "source_citation", "verse_ref", "table_version", "graha"):
        m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET {col} = 'N/A' WHERE graha = 'Sun';"])
        assert m[BR]["v"] == FAIL and "literal fallback" in _text(m), col


# ── the constants ──

def test_REAL_MUTATION_table_version_varying_across_rows_fails_the_constant(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET table_version = 'phaladeepika_vedha_v02' WHERE graha = 'Sun';"])
    assert m[BR]["v"] == FAIL and "declared constant column table_version varies (2 distinct value(s), 0 NULL)" in _text(m)


def test_REAL_MUTATION_source_citation_varying_across_rows_fails_the_constant(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET source_citation = '{OTHER_CITATION}' WHERE graha IN ('Sun','Moon');"])
    assert m[BR]["v"] == FAIL and "declared constant column source_citation varies (2 distinct value(s), 0 NULL)" in _text(m)
    for col in ("affliction_condition", "verse_ref"):
        m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET {col} = {col} || ' x' WHERE graha = 'Venus';"])
        assert m[BR]["v"] == FAIL and f"declared constant column {col} varies" in _text(m), col


# ── (e) LIVE VALUES: the constants are read, not pinned ──

def test_REAL_LIVE_VALUES_a_corrected_single_source_citation_and_verse_ref_still_read_pass(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET source_citation = '{OTHER_CITATION}', verse_ref = 'Adh.XXVI PG338-339 Slokas 42-46';"])
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS and ac.null_lift_earned(BR, m[BR], m)
    assert ac.rollup_asset("L0", m)["Null"]["v"] == PASS
    assert all("value" not in c for c in NC["constants"])                      # nothing in the declaration pins today's text


def test_REAL_LIVE_VALUES_every_constant_may_change_to_another_single_value(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET affliction_condition = 'If the natal star falls on the Latta star, sickness and anguish follow.', "
                                                f"table_version = 'phaladeepika_vedha_v02', source_citation = '{OTHER_CITATION}';"])
    assert m[BR]["v"] == PASS


# ── the stamp column ──

def test_REAL_created_at_is_one_value_on_all_rows_and_that_is_allowed_only_because_it_is_a_declared_stamp(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg)
    assert m[BR]["v"] == PASS and len({r["created_at"] for r in ROWS}) == 1
    no_stamp = copy.deepcopy(ENTRY)
    del no_stamp["null_convention"]["stamp_columns"]                           # without the declaration the same rows FAIL (the reason option C waited for pin 15)
    m2 = _measure(monkeypatch, disposable_pg, entry=no_stamp)
    assert m2[BR]["v"] == FAIL and "created_at hold one value on every row" in _text(m2)


@pytest.mark.parametrize("value", ["infinity", "-infinity", "epoch", "1970-01-01 00:00:00+00", "1970-01-01 12:00:00+00", "0001-01-01 00:00:00+00"])
def test_REAL_MUTATION_a_sentinel_created_at_fails(monkeypatch, disposable_pg, value):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET created_at = '{value}'::timestamptz;"])
    assert m[BR]["v"] == FAIL and "sentinel timestamp" in _text(m) and "created_at (8 row(s))" in _text(m)


def test_REAL_MUTATION_a_real_later_created_at_on_some_rows_is_fine_it_is_a_stamp(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET created_at = created_at + interval '2 days' WHERE graha IN ('Sun','Moon');"])
    assert m[BR]["v"] == PASS


def test_REAL_MUTATION_created_at_nullable_is_refused_by_the_catalog_never_a_pass(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, ddl=[f"ALTER TABLE {AID} ALTER COLUMN created_at DROP NOT NULL;"])
    note = m[BR]["null_convention"]
    assert m[BR]["v"] != PASS and note["verified"] is False and note["v"] == NO_DET and "stamp column" in note["measured"] and "NOT NULL" in note["measured"]
    assert not ac.null_lift_earned(BR, m[BR], m)
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS


def test_REAL_MUTATION_a_null_created_at_fails(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, ddl=[f"ALTER TABLE {AID} ALTER COLUMN created_at DROP NOT NULL;"], extra=[f"UPDATE {AID} SET created_at = NULL WHERE graha = 'Sun';"])
    assert m[BR]["v"] != PASS


def test_REAL_MUTATION_a_zero_count_does_not_change_the_null_reading_which_is_the_d1_s_job(monkeypatch, disposable_pg):
    m = _measure(monkeypatch, disposable_pg, [f"UPDATE {AID} SET count_from_graha = 0 WHERE graha = 'Sun';"])
    assert m[BR]["v"] == PASS                                                   # a NOT NULL smallint: the 0 sentinel applies only to a declared-nullable numeric; D1 catches a wrong count


def test_REAL_MUTATION_a_duplicate_free_extra_row_with_a_null_effect_for_an_unlisted_graha_fails(monkeypatch, disposable_pg):
    ketu = ", ".join(dl._lit(v) for v in [ROWS[0]["table_version"], "Ketu", 9, "backward", None, ROWS[0]["affliction_condition"], ROWS[0]["source_citation"], ROWS[0]["verse_ref"]])
    m = _measure(monkeypatch, disposable_pg, [f"INSERT INTO {AID} (table_version, graha, count_from_graha, direction, effect_description, affliction_condition, source_citation, verse_ref) VALUES ({ketu});"])
    assert m[BR]["v"] == FAIL and "(keys: Ketu)" in _text(m)


# ── the schema_default and blank_rows siblings: each blocks the lift on its own ──

def test_REAL_a_schema_default_on_the_nullable_column_keeps_the_cap(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, dl._setup())
    cat = dict(CAT, defaults={AID: {"created_at": "now()", "effect_description": "'N/A'::text"}})
    m = ac._measure_prose(AID, ENTRY, R, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS and not ac.null_lift_earned(SD, m[SD], m)


# ───────────────────────── the ELEVATED reader: a Null PASS counts only via the earned lift ─────────────────────────

def test_REAL_the_elevated_reader_counts_the_null_pass_only_through_the_earned_lift(monkeypatch, disposable_pg, tmp_path):
    m = _measure(monkeypatch, disposable_pg)
    ms = {SD: copy.deepcopy(m[SD]), BR: copy.deepcopy(m[BR])}
    assert rd.satisfied(rd.world(tmp_path / "earned", ms)) == [True, True]
    plain = {c: {k: v for k, v in rec.items() if k != "null_convention"} for c, rec in ms.items()}          # the same PASS records without the verified block: the cap
    assert all(r["v"] == PASS for r in plain.values()) and rd.satisfied(rd.world(tmp_path / "plain", plain)) == [False, False]
    one_sided = copy.deepcopy(ms)
    one_sided[BR].pop("null_convention")
    assert rd.satisfied(rd.world(tmp_path / "one", one_sided)) == [False, False]
    forged2 = copy.deepcopy(ms)
    forged2[BR]["null_convention"]["stamp_columns"] = []
    assert not ac.null_lift_earned(SD, forged2[SD], forged2) and not ac.null_lift_earned(BR, forged2[BR], forged2)


# ───────────────────────── (a) the cell diff across ALL L0 assets of the saved census ─────────────────────────

@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_REAL_only_the_latta_null_cell_changes_across_every_l0_asset(monkeypatch, disposable_pg):
    assets = json.loads((SAVED / "census_L0.json").read_text(encoding="utf-8"))["L0"]["assets"]
    # BEFORE = main after #2991 (declarations 1.10.0): the saved measurements with the latta's three declared blocks measured (carriage, vocab_alias, ldgr_source)
    s3._real(monkeypatch, disposable_pg, dl._setup())
    three = {}
    three.update(ac.carriage_declared_checks(AID, ENTRY["carriage"], AID, False))
    three.update(ac.vocab_alias_declared_check(AID, ENTRY["vocab_alias"], AID, COLS))
    three.update(ac.ldgr_source_declared_check(AID, ENTRY["ldgr_source"], AID, COLS, [["table_version", "graha"]]))
    nul = _measure(monkeypatch, disposable_pg)
    before, after = {}, {}
    for a in assets:
        base = dict(a["measurements"])
        if a["asset_id"] == AID:
            base = {k: v for k, v in base.items() if k not in ("Ldgr.source_presence", "Vocab.alias")}
            base.update(three)
        before[a["asset_id"]] = ac.rollup_asset("L0", base)
        new = dict(base)
        if a["asset_id"] == AID:
            new.update({SD: nul[SD], BR: nul[BR]})
        after[a["asset_id"]] = ac.rollup_asset("L0", new)
    diff = [(aid, g, before[aid][g]["v"], after[aid][g]["v"]) for aid in before for g in before[aid] if before[aid][g]["v"] != after[aid][g]["v"]]
    assert len(before) == len(assets) == 40
    assert diff == [(AID, "Null", NO_DET, PASS)]
    # the checks inside every other cell are identical too (not only the cell verdicts)
    other = [(aid, g) for aid in before for g in before[aid] if aid != AID and before[aid][g] != after[aid][g]]
    assert other == []
    b, af = before[AID], after[AID]
    assert {g: (b[g]["v"], af[g]["v"]) for g in b if g in ("Narr", "Earn", "Dens")} == {"Narr": (NO_DET, NO_DET), "Earn": (NO_DET, NO_DET), "Dens": (NO_DET, NO_DET)}
    assert {c["criterion"]: c["v"] for c in af["Narr"]["checks"] if c["criterion"].startswith("Narr.")} == {c: NO_DET for c in ac.NARR_CHECKS}
    assert next(c for c in af["Earn"]["checks"] if c["criterion"] == "Earn.build_record")["v"] == NO_DET
    assert next(c for c in af["Null"]["checks"] if c["criterion"] == SD).get("null_convention_verified") is True
