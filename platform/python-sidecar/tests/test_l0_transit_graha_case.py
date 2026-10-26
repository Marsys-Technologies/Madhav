"""SS addition to the L0 data batch: every value of bg_transit_rules.graha is the canonical
lowercase planet name (live defect: 'Jupiter' x5 and 'Saturn' x2 -- migration 397's
double_transit rows -- beside 69 lowercase rows).

Proves
  1. static over the seed: every BG_TRANSIT_RULES graha is a lowercase member of the nine
     canonical grahas; the 7 double_transit seed rows equal migration 397's rows verbatim
     except for the graha case (parsed from the migration file itself, not retyped).
  2. real PostgreSQL (env-gated): the REAL seed_transit_rules against a table holding
     migration 397's title-case rows (a) leaves NO value that is not lowercase canonical,
     (b) keeps all seven ids (gochara_resonance_map.source_rule_id FK-referenced), (c) changes
     only `graha` on those seven rows, (d) inserts no duplicate, (e) is a no-op on rerun,
     (f) refuses to merge a title-case row into an existing lowercase twin (UniqueViolation).
  3. consumer census on the same database: every case-INSENSITIVE consumer query returns the
     same row set before and after; the only consumers whose result can change are exact-
     lowercase comparisons with no rule_type filter, and the test names them.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from brahmagyan import l0_transit as T
from tests._l0d_pg import requires_pg, scratch_schema

GRAHAS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
MIG_397 = Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "397_bg_transit_av_gates.sql"


def _mig397_insert_sql() -> str:
    s = MIG_397.read_text(encoding="utf-8")
    i = s.index("INSERT INTO bg_transit_rules")
    j = s.index("DO NOTHING;", i) + len("DO NOTHING;")
    return s[i:j]


def _mig397_rows() -> list[tuple]:
    sql = _mig397_insert_sql()
    pat = re.compile(
        r"\(\s*'double_transit',\s*'(\w+)',\s*(\d+),\s*NULL,\s*'((?:[^']|'')*)',\s*'((?:[^']|'')*)',\s*(NULL|'(?:[^']|'')*')\s*\)")
    out = []
    for g, h, phala, cit, notes in pat.findall(sql):
        notes = None if notes == "NULL" else notes[1:-1].replace("''", "'")
        out.append((g, int(h), phala.replace("''", "'"), cit.replace("''", "'"), notes))
    return out


# ── 1. static ────────────────────────────────────────────────────────────────

def test_every_seed_graha_is_lowercase_canonical():
    bad = sorted({r["graha"] for r in T.BG_TRANSIT_RULES} - GRAHAS)
    assert bad == [], f"non-canonical graha values in the seed: {bad}"


def test_the_seven_double_transit_seed_rows_equal_migration_397_except_graha_case_and_the_unsourced_marker():
    mig = _mig397_rows()
    assert len(mig) == 7, "parsed migration 397 double_transit rows"
    seed = sorted(((r["graha"], r["primary_house"], r["phala"], r["classical_citation"], r["rule_notes"])
                   for r in T.BG_TRANSIT_RULES if r["rule_type"] == "double_transit"))
    want = sorted(((g.lower(), h, p, c, n) for g, h, p, c, n in mig))
    assert [(a[0], a[1], a[2], a[4]) for a in seed] == [(w[0], w[1], w[2], w[4]) for w in want], "everything but the citation is verbatim"
    # the citation: marked UNSOURCED (review L0A MED-2) with the original kept for the record; BPHS ch.29 flagged refuted
    for (g, h, ph, cit, nt), (_g, _h, _p, orig, _n) in zip(seed, want):
        assert cit.startswith("UNSOURCED") and cit.endswith(orig), (g, h)
        assert ("refuted" in cit) == ("BPHS" in orig)
        assert "does not exist in the served corpus" in cit
    assert {g for g, *_ in mig} == {"Jupiter", "Saturn"}, "the defect the migration carries"


def test_no_double_transit_row_reads_as_sourced_to_the_refuted_bphs_ch29():
    # (the 19 favourable/unfavourable rows that cite it are re-sourced by TI-L0-10, PR #3049)
    for r in T.BG_TRANSIT_RULES:
        if r["rule_type"] != "double_transit":
            continue
        c = r["classical_citation"]
        if re.search(r"BPHS\s*ch\.?\s*29", c, re.I):
            assert c.startswith("UNSOURCED"), (r["graha"], r["rule_type"], r["primary_house"])


def test_seed_total_is_76_and_unique_on_the_table_key():
    keys = [(r["graha"], r["rule_type"], r["primary_house"]) for r in T.BG_TRANSIT_RULES]
    assert len(keys) == 76 and len(set(keys)) == 76


def test_dry_run_reports_the_normalisation_counter():
    out = T.seed_transit_rules(None, dry_run=True)
    assert out["bg_transit_rules"] == 76
    assert "bg_transit_rules_graha_case_normalised" in out


# ── 2/3. real PostgreSQL ─────────────────────────────────────────────────────

DDL = """
CREATE TABLE bg_transit_engine (
  id serial PRIMARY KEY, graha text NOT NULL UNIQUE,
  avg_daily_motion_deg double precision NOT NULL, zodiac_period_days double precision NOT NULL,
  sign_residence_days double precision NOT NULL, classical_citation text NOT NULL);
CREATE TABLE bg_transit_rules (
  id serial PRIMARY KEY, rule_type text NOT NULL, graha text NOT NULL,
  primary_house integer NOT NULL, vedha_house integer, phala text NOT NULL,
  classical_citation text NOT NULL, rule_notes text,
  CONSTRAINT bg_transit_rules_graha_type_house_unique UNIQUE (graha, rule_type, primary_house),
  CONSTRAINT bg_transit_rules_primary_house_check CHECK (primary_house BETWEEN 1 AND 12),
  CONSTRAINT bg_transit_rules_rule_type_check CHECK (rule_type IN ('favourable','unfavourable','vedha','double_transit')),
  CONSTRAINT bg_transit_rules_vedha_house_check CHECK (vedha_house BETWEEN 1 AND 12));
CREATE TABLE bg_transit_moorti (
  nakshatra_offset integer PRIMARY KEY CHECK (nakshatra_offset BETWEEN 1 AND 27),
  moorti_name text NOT NULL CHECK (moorti_name IN ('swarna','rajata','tamra','loha')),
  quality_tier integer NOT NULL CHECK (quality_tier BETWEEN 1 AND 4),
  phala_brief text NOT NULL, classical_citation text NOT NULL, rule_notes text);
CREATE TABLE gochara_resonance_map (
  id serial PRIMARY KEY, source_rule_id integer REFERENCES bg_transit_rules(id), target_ref text);
"""

# The consumer queries, copied from the repo (file:line in the PR body). Each is run against the
# before-state and the after-state of the same database.
CASE_INSENSITIVE = {
    "ka_gochara_resonance/writer.py _FETCH_TRANSIT_RULES_SQL":
        "SELECT id FROM bg_transit_rules WHERE lower(graha) = ANY(ARRAY['jupiter','saturn','sun']) "
        "AND primary_house = ANY(ARRAY[2,4,5,7,8,9,11]) ORDER BY id",
    "platform-mcp register_p1_reference.ts ref_transit_rules_get (graha=Jupiter)":
        "SELECT id FROM bg_transit_rules WHERE LOWER(graha) = LOWER('Jupiter') ORDER BY id",
    "R1_R6 runbook / resonance_rebuild_backup_sql lower(btrim(r.graha)) join":
        "SELECT id FROM bg_transit_rules r WHERE lower(btrim(r.graha)) IN ('jupiter','saturn') ORDER BY id",
}
FILTERED_BY_RULE_TYPE = {
    "ka_vedha_gochara/writer.py _FETCH_VEDHA_RULES_SQL":
        "SELECT id FROM bg_transit_rules WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL ORDER BY id",
    "gochara_grammar/primitives.py _fetch_vedha_rules":
        "SELECT id FROM bg_transit_rules WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL ORDER BY id",
    "phala/muhurta.py _fetch_gochara_rules":
        "SELECT id FROM bg_transit_rules WHERE rule_type IN ('favourable','unfavourable') ORDER BY id",
    "gochara_rules/vedha_derive.py _PAIRS_SQL":
        "SELECT id FROM bg_transit_rules WHERE vedha_house IS NOT NULL ORDER BY id",
}
EXACT_LOWERCASE_UNFILTERED = {  # these CAN gain rows; the test asserts the gain is exactly the 7 double_transit ids
    "any exact `graha = 'jupiter'` / `'saturn'` with no rule_type filter":
        "SELECT id FROM bg_transit_rules WHERE graha IN ('jupiter','saturn') ORDER BY id",
}


def a_cit_ok(new: str, old: str) -> bool:
    return new.startswith("UNSOURCED") and new.endswith(old)


def _ids(conn, sql):
    return [r["id"] for r in conn.execute(sql)]


def _prestate(conn):
    """The live shape: 69 lowercase writer rows + migration 397's 7 title-case rows."""
    T.seed_transit_rules(conn)
    conn.execute("DELETE FROM bg_transit_rules WHERE rule_type='double_transit'")
    conn.execute(_mig397_insert_sql())
    conn.commit()


@requires_pg
def test_real_writer_normalises_in_place_and_every_value_is_lowercase_canonical():
    with scratch_schema(DDL) as conn:
        _prestate(conn)
        dt_before = {r["id"]: r for r in conn.execute("SELECT * FROM bg_transit_rules WHERE rule_type='double_transit' ORDER BY id")}
        assert sorted({r["graha"] for r in dt_before.values()}) == ["Jupiter", "Saturn"]
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules WHERE graha <> lower(graha)").fetchone()["n"] == 7
        referenced = sorted(dt_before)[:6]
        for rid in referenced:
            conn.execute("INSERT INTO gochara_resonance_map(source_rule_id,target_ref) VALUES (%s,'t')", (rid,))
        conn.commit()
        before_sets = {k: _ids(conn, q) for k, q in {**CASE_INSENSITIVE, **FILTERED_BY_RULE_TYPE, **EXACT_LOWERCASE_UNFILTERED}.items()}
        others_before = {r["id"]: r for r in conn.execute("SELECT * FROM bg_transit_rules WHERE rule_type<>'double_transit'")}

        out = T.seed_transit_rules(conn)
        conn.commit()
        assert out["bg_transit_rules_graha_case_normalised"] == 7

        # (a) the column invariant
        assert conn.execute(
            "SELECT count(*) AS n FROM bg_transit_rules WHERE graha <> lower(graha) OR graha <> ALL(%s)",
            (sorted(GRAHAS),)).fetchone()["n"] == 0
        # (b) ids stable, FK intact
        dt_after = {r["id"]: r for r in conn.execute("SELECT * FROM bg_transit_rules WHERE rule_type='double_transit' ORDER BY id")}
        assert set(dt_after) == set(dt_before)
        assert conn.execute("SELECT count(*) AS n FROM gochara_resonance_map m JOIN bg_transit_rules r ON r.id=m.source_rule_id").fetchone()["n"] == 6
        # (c) only graha changed on those rows
        for rid, b in dt_before.items():
            changed = [c for c in b if b[c] != dt_after[rid][c]]
            assert changed == ["graha", "classical_citation"], (rid, changed)
            assert a_cit_ok(dt_after[rid]["classical_citation"], b["classical_citation"])
            assert dt_after[rid]["graha"] == b["graha"].lower()
        # (d) no duplicate / no other row touched
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules").fetchone()["n"] == 76
        others_after = {r["id"]: r for r in conn.execute("SELECT * FROM bg_transit_rules WHERE rule_type<>'double_transit'")}
        assert others_after == others_before
        # (e) converged
        snap = list(conn.execute("SELECT * FROM bg_transit_rules ORDER BY id"))
        out2 = T.seed_transit_rules(conn)
        conn.commit()
        assert out2["bg_transit_rules_graha_case_normalised"] == 0
        assert list(conn.execute("SELECT * FROM bg_transit_rules ORDER BY id")) == snap

        # (3) consumer census: before/after row sets
        after_sets = {k: _ids(conn, q) for k, q in {**CASE_INSENSITIVE, **FILTERED_BY_RULE_TYPE, **EXACT_LOWERCASE_UNFILTERED}.items()}
        for k in {**CASE_INSENSITIVE, **FILTERED_BY_RULE_TYPE}:
            assert after_sets[k] == before_sets[k], f"consumer result changed: {k}"
        for k in EXACT_LOWERCASE_UNFILTERED:
            assert set(after_sets[k]) - set(before_sets[k]) == set(dt_before), k
            assert set(before_sets[k]) <= set(after_sets[k])


@requires_pg
def test_real_writer_refuses_to_merge_into_an_existing_lowercase_twin():
    import psycopg
    with scratch_schema(DDL) as conn:
        _prestate(conn)
        conn.execute(
            "INSERT INTO bg_transit_rules(rule_type,graha,primary_house,phala,classical_citation) "
            "VALUES ('double_transit','jupiter',2,'twin','x')")
        conn.commit()
        with pytest.raises(psycopg.errors.UniqueViolation):
            T.seed_transit_rules(conn)
        conn.rollback()
        # nothing was merged or lost
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules WHERE graha='Jupiter'").fetchone()["n"] == 5
