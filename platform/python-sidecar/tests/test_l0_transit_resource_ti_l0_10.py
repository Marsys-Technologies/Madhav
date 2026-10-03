"""TI-L0-10 (SS Q3): the 19 refuted "BPHS Ch.29" transit citations and the 5 chapter-only
"Phaladeepika Ch.26" citations are re-sourced row by row to the Phaladipika Adh. XXVI
result slokas the served corpus actually contains.

What this file proves
  1. static: no seed row still carries the refuted / chapter-only value; every re-sourced
     row cites the (sloka, page) pair in an independently written golden table; the
     valence (rule_type) of every touched row is unchanged; Ketu 12th stays FAVOURABLE and
     says plainly it is unsourced and contradicted (no invented citation, B.10 / N.7 item 6).
  2. real PostgreSQL (env-gated, see _l0d_pg.py): the REAL seed_transit_rules run against a
     table holding the old citations changes exactly the 24 classical_citation cells, keeps
     every id (gochara_resonance_map.source_rule_id FK-referenced), touches no other column,
     and a second run is a no-op.

Golden table provenance: every (sloka, pages) pair below was read in the served corpus
(classical_text_chunks, text_id='phaladeepika', verse_ref PG321/PG324..PG331:C1) on
2026-10-03; the quoted fragment is the OCR text of the chunk. verse_ref is page-based here.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from brahmagyan import l0_transit as T
from tests._l0d_pg import requires_pg, scratch_schema

OLD_BPHS = "BPHS Ch.29 (Gochara Phala — Transit Results)"
OLD_PD = "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"
ED = "(Sastri trans. 1950)"

# (graha, house) -> (rule_type, old citation, sloka, pages, corpus fragment)
GOLDEN = {
    ("sun", 1): ("unfavourable", OLD_BPHS, 9, "PG324:C1", "fatigue and loss of wealth"),
    ("sun", 5): ("unfavourable", OLD_BPHS, 10, "PG324:C1", "Mental agitation, ill-health"),
    ("sun", 8): ("unfavourable", OLD_BPHS, 10, "PG324:C1-PG325:C1", "8th house, the native will suffer from fear, and diseases"),
    ("moon", 8): ("unfavourable", OLD_BPHS, 12, "PG325:C1", "(8) untoward events"),
    ("mars", 1): ("unfavourable", OLD_BPHS, 13, "PG326:C1", "dejection of the mind"),
    ("mars", 4): ("unfavourable", OLD_BPHS, 13, "PG326:C1", "loss of position, disease of the belly"),
    ("mars", 8): ("unfavourable", OLD_BPHS, 15, "PG326:C1-PG327:C1", "In the 8th house, the native will suffer from fever"),
    ("jupiter", 4): ("unfavourable", OLD_BPHS, 18, "PG328:C1", "3rd house ... When Jupiter transits the 4th house, there will be sorrow through relations"),
    ("jupiter", 8): ("unfavourable", OLD_BPHS, 19, "PG328:C1", "In the 8th house ... unlucky, suffer loss of money"),
    ("saturn", 1): ("unfavourable", OLD_PD, 22, "PG330:C1", "Janmarasi, the native will suffer from disease"),
    ("saturn", 4): ("unfavourable", OLD_BPHS, 22, "PG330:C1", "4th house, there will be loss of wife, relation and wealth"),
    ("saturn", 8): ("unfavourable", OLD_BPHS, 22, "PG330:C1", "8th house, there will be loss in children, cattle, friends and wealth"),
    ("rahu", 1): ("unfavourable", OLD_BPHS, 24, "PG331:C1", "(1) sickness or death"),
    ("rahu", 2): ("unfavourable", OLD_BPHS, 24, "PG331:C1", "(2) loss oi wealth"),
    ("rahu", 4): ("unfavourable", OLD_BPHS, 24, "PG331:C1", "(4) sorrow"),
    ("rahu", 7): ("unfavourable", OLD_PD, 24, "PG331:C1", "(7) loss"),
    ("rahu", 8): ("unfavourable", OLD_BPHS, 24, "PG331:C1", "8) danger to life"),
    ("rahu", 12): ("unfavourable", OLD_PD, 24, "PG331:C1", "(12) expenditure"),
}
KETU_EQUIV = {("ketu", 1): OLD_BPHS, ("ketu", 4): OLD_BPHS, ("ketu", 8): OLD_BPHS,
              ("ketu", 2): OLD_PD, ("ketu", 7): OLD_PD}
KETU_12 = ("ketu", 12)


def _rows():
    return {(r["graha"], r["primary_house"]): r for r in T.BG_TRANSIT_RULES if r["rule_type"] != "double_transit"}


def expected_citation(sloka: int, pages: str) -> str:
    return f"Phaladipika Adh. XXVI, Sloka {sloka} — phaladeepika:{pages} {ED}"


# ── 1. static ────────────────────────────────────────────────────────────────

def test_no_seed_row_keeps_the_refuted_or_chapter_only_citation():
    bad = [(k, r["classical_citation"]) for k, r in _rows().items()
           if r["classical_citation"] in (OLD_BPHS, OLD_PD)]
    assert bad == [], f"rows still cite the refuted/chapter-only value: {bad}"


@pytest.mark.parametrize("key", sorted(GOLDEN))
def test_each_resourced_row_cites_its_golden_sloka_and_page(key):
    rt, _old, sloka, pages, _frag = GOLDEN[key]
    row = _rows()[key]
    assert row["rule_type"] == rt, "valence (rule_type) of a re-sourced row must not change"
    assert row["classical_citation"] == expected_citation(sloka, pages)


def test_golden_table_is_exactly_the_18_directly_stated_rows():
    assert len(GOLDEN) == 18
    assert set(T.PD_RESULT_CITATION) == set(GOLDEN)


@pytest.mark.parametrize("key", sorted(KETU_EQUIV))
def test_ketu_rows_cite_the_equivalence_as_an_equivalence(key):
    row = _rows()[key]
    assert row["rule_type"] == "unfavourable"
    c = row["classical_citation"]
    assert "Sloka 2" in c and "PG321:C1" in c and "PG331:C1" in c
    assert "BY STATED EQUIVALENCE" in c and "not a Ketu-specific sloka" in c


def test_ketu_12_stays_favourable_and_says_it_is_unsourced_and_contradicted():
    row = _rows()[KETU_12]
    assert row["rule_type"] == "favourable", "valence is an acharya decision; this PR must not change it"
    c = row["classical_citation"]
    assert c.startswith("UNSOURCED") and "refuted" in c and "points the other way" in c
    assert "BPHS Ch.29 (" not in c


def test_node_vedha_rows_keep_their_honest_unsourced_marker():
    n = sum(1 for r in T.BG_TRANSIT_RULES if r["classical_citation"] == T.RAHU_KETU_HOUSE_VEDHA_UNSOURCED)
    assert n == 6


def test_every_citation_that_names_a_sloka_names_a_page_anchor():
    for key, r in _rows().items():
        c = r["classical_citation"]
        if "Sloka " in c and not c.startswith("UNSOURCED"):
            assert re.search(r"phaladeepika:PG\d+:C1", c), (key, c)


def test_only_citation_strings_differ_from_the_old_bindings():
    # the touched row set is exactly 24 = 19 (BPHS Ch.29) + 5 (chapter-only)
    touched = set(GOLDEN) | set(KETU_EQUIV) | {KETU_12}
    assert len(touched) == 24
    old = [v[1] for v in GOLDEN.values()] + list(KETU_EQUIV.values()) + [OLD_BPHS]
    assert old.count(OLD_BPHS) == 19 and old.count(OLD_PD) == 5


# ── 2. real PostgreSQL ───────────────────────────────────────────────────────

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

MIG_397 = Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "397_bg_transit_av_gates.sql"


def _migration_397_double_transit_insert() -> str:
    s = MIG_397.read_text(encoding="utf-8")
    i = s.index("INSERT INTO bg_transit_rules")
    j = s.index("DO NOTHING;", i) + len("DO NOTHING;")
    return s[i:j]


def _snapshot(conn):
    return {r["id"]: r for r in conn.execute("SELECT * FROM bg_transit_rules ORDER BY id")}


@requires_pg
def test_real_writer_changes_exactly_the_24_citation_cells_and_keeps_every_id():
    with scratch_schema(DDL) as conn:
        # pre-state: the writer's own rows, then the old citations put back, plus migration 397's
        # seven double_transit rows executed verbatim from the migration file.
        T.seed_transit_rules(conn)
        # live shape: the seven double_transit rows are migration 397's (whatever the seed also carries
        # of them is replaced), so this test holds with or without the SS case-fix PR (TI-l0data-35).
        conn.execute("DELETE FROM bg_transit_rules WHERE rule_type='double_transit'")
        conn.execute(_migration_397_double_transit_insert())
        for (g, h), (_rt, old, *_r) in GOLDEN.items():
            conn.execute("UPDATE bg_transit_rules SET classical_citation=%s WHERE graha=%s AND primary_house=%s",
                         (old, g, h))
        for (g, h), old in KETU_EQUIV.items():
            conn.execute("UPDATE bg_transit_rules SET classical_citation=%s WHERE graha=%s AND primary_house=%s",
                         (old, g, h))
        conn.execute("UPDATE bg_transit_rules SET classical_citation=%s WHERE graha='ketu' AND primary_house=12", (OLD_BPHS,))
        ids = [r["id"] for r in conn.execute("SELECT id FROM bg_transit_rules WHERE graha IN ('sun','rahu','ketu') ORDER BY id")]
        for rid in ids[:6]:
            conn.execute("INSERT INTO gochara_resonance_map(source_rule_id,target_ref) VALUES (%s,'x')", (rid,))
        conn.commit()
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules").fetchone()["n"] == 76
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules WHERE classical_citation=%s", (OLD_BPHS,)).fetchone()["n"] == 19
        assert conn.execute("SELECT count(*) AS n FROM bg_transit_rules WHERE classical_citation=%s", (OLD_PD,)).fetchone()["n"] == 5
        before = _snapshot(conn)

        T.seed_transit_rules(conn)
        conn.commit()
        after = _snapshot(conn)

        assert set(before) == set(after), "ids must be stable (gochara_resonance_map FK)"
        diff = []
        for rid in before:
            if before[rid]["rule_type"] == "double_transit":
                continue            # the double_transit rows belong to the graha-case change, not to this one
            b, a = before[rid], after[rid]
            cols = [c for c in b if b[c] != a[c]]
            if cols:
                diff.append((rid, b["graha"], b["primary_house"], cols, b["classical_citation"], a["classical_citation"]))
        assert all(d[3] == ["classical_citation"] for d in diff), "only classical_citation may change"
        assert len(diff) == 24
        assert sum(1 for r in after.values() if r["classical_citation"] in (OLD_BPHS, OLD_PD)) == 0
        assert conn.execute("SELECT count(*) AS n FROM gochara_resonance_map").fetchone()["n"] == 6

        out = os.environ.get("L0D_EVIDENCE_OUT")
        if out:
            Path(out).write_text(json.dumps(
                [{"id": d[0], "graha": d[1], "house": d[2], "old": d[4], "new": d[5]} for d in diff],
                ensure_ascii=False, indent=1), encoding="utf-8")

        # converged: a second run changes nothing
        T.seed_transit_rules(conn)
        conn.commit()
        assert _snapshot(conn) == after
