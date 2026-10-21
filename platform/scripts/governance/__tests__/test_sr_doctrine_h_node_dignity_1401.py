"""test_sr_doctrine_h_node_dignity_1401.py: migration 1401 (SR-DOCTRINE-H) applied to REAL tables on a throw-away PostgreSQL.

The static pins of the SQL against the doctrine and the seeds are `python-sidecar/tests/test_migration_1401_l0_node_dignity.py`. This file shows what only a
database can: that 1401 turns the migration-250 rows into the BPHS ch.47 / BPHS 3.55-note rows, changes NOTHING else, replays to the same rows, refuses a
table that is not in the shape it corrects, and that the REAL L0 writer (`BgDignityReferenceWriter`) rebuilds to exactly the migrated rows (a migration
alone would be undone by the next rebuild, the reason the seeds carry the same values).

Doctrine (served texts, quoted in ANSWERS.md v2.1 B.5 / H and the static test): BPHS ch.47 (chunks bphs:PG573:C2 to bphs:PG574:C1): Rahu moolatrikona Gemini,
own Aquarius; Ketu moolatrikona Sagittarius, own Scorpio. BPHS 3.55 translator note (bphs:PG40:C1): Rahu's enemies Sun, Moon, Mars, friends Jupiter, Venus,
Saturn, neutral Mercury; Ketu's enemies the luminaries, friends Mars, Venus, Saturn, neutral Mercury and Jupiter.

The migration file is placed under platform/migrations by the cockpit; until then set L0_MIGRATION_1401_PATH. A missing file FAILS (never skips).
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

T1, T2, T3, T4, T5 = "bg_dignity_reference", "bg_graha_naisargika_friendship", "bg_avastha_schemes", "bg_motion_state_thresholds", "bg_combustion_orbs"
TABLES = [T1, T2, T3, T4, T5]
RUN = "11111111-1111-4111-8111-111111111111"
MIG_1401 = pathlib.Path(os.environ.get("L0_MIGRATION_1401_PATH") or fs.MIG / "1401_l0_node_dignity_friendship.sql")

# doctrine, independent of the seeds: (graha) -> (moolatrikona, own_signs)
NODE_DIGNITY = {"Rahu": ("Gemini", "{Aquarius}"), "Ketu": ("Sagittarius", "{Scorpio}")}
# migration-250 relation -> BPHS 3.55 note relation, for exactly the five disputed pairs
FIVE_PAIRS = {("Rahu", "Mercury"): ("friend", "neutral"), ("Rahu", "Mars"): ("neutral", "enemy"), ("Rahu", "Jupiter"): ("neutral", "friend"),
              ("Ketu", "Sun"): ("neutral", "enemy"), ("Ketu", "Moon"): ("neutral", "enemy")}


def _insert_statement(table: str) -> str:
    """The migration-250 `INSERT INTO <table> ... ON CONFLICT ... ;` statement, verbatim (the migration also creates tables and registry rows this database does not have)."""
    txt = (fs.MIG / "250_bg_dignity_reference.sql").read_text(encoding="utf-8")
    m = re.search(r"INSERT INTO " + re.escape(table) + r"\b.*?ON CONFLICT[^;]*;", txt, re.DOTALL)
    assert m, table
    return m.group(0)


def _seed_migration_250(pg) -> None:
    fs.drop_tables(pg, *TABLES)
    for t in TABLES:
        fs.psql(pg, fs.create_table_ddl(fs.MIG / "250_bg_dignity_reference.sql", t))
    fs.psql(pg, "ALTER TABLE bg_dignity_reference ADD COLUMN IF NOT EXISTS variant_traditions JSONB DEFAULT NULL")            # migration 330
    fs.psql(pg, _insert_statement(T1))
    fs.psql(pg, _insert_statement(T2))


def _run_1401(pg) -> subprocess.CompletedProcess:
    assert MIG_1401.is_file(), f"migration 1401 not found at {MIG_1401} (place it under platform/migrations or set L0_MIGRATION_1401_PATH)"
    return subprocess.run([str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(MIG_1401)], capture_output=True, text=True, timeout=180)


def _apply_1401(pg) -> None:
    p = _run_1401(pg)
    assert p.returncode == 0, p.stderr.strip()[:600]


def _dig(pg, graha):
    return fs.psql(pg, f"SELECT moolatrikona_sign, COALESCE(moolatrikona_from::text,'-'), COALESCE(moolatrikona_to::text,'-'), COALESCE(own_signs::text,'-') FROM {T1} WHERE graha='{graha}'").strip().split("|")


def _fr(pg, g, o):
    return fs.psql(pg, f"SELECT relation FROM {T2} WHERE graha='{g}' AND other_graha='{o}'").strip()


def _rest_snapshot(pg) -> str:
    """Every column of every row EXCEPT the seven rows 1401 is allowed to write (ids excluded: they are execution-only)."""
    return fs.psql(pg, f"""
      SELECT 'D', md5(string_agg(t::text, '|' ORDER BY graha)) FROM (SELECT graha, exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree, moolatrikona_sign,
        moolatrikona_from, moolatrikona_to, own_signs, classical_citation, notes, variant_traditions FROM {T1} WHERE graha NOT IN ('Rahu','Ketu')) t
      UNION ALL SELECT 'DX', md5(string_agg(t::text, '|' ORDER BY graha)) FROM (SELECT graha, exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree, variant_traditions
        FROM {T1} WHERE graha IN ('Rahu','Ketu')) t
      UNION ALL SELECT 'F', md5(string_agg(t::text, '|' ORDER BY graha, other_graha)) FROM (SELECT graha, other_graha, relation, classical_citation FROM {T2}
        WHERE (graha, other_graha) NOT IN (('Rahu','Mercury'),('Rahu','Mars'),('Rahu','Jupiter'),('Ketu','Sun'),('Ketu','Moon'))) t""")


def _full_snapshot(pg, variants: bool = True) -> str:
    """Both tables, every semantic column. `variants=False` leaves out variant_traditions: migration 330 only adds that column, the writer populates it, so a 250-seeded database holds NULL there until a rebuild."""
    vt = ", variant_traditions" if variants else ""
    return fs.psql(pg, f"""
      SELECT 'D', md5(string_agg(t::text, '|' ORDER BY graha)) FROM (SELECT graha, exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree, moolatrikona_sign,
        moolatrikona_from, moolatrikona_to, own_signs, classical_citation, notes{vt} FROM {T1}) t
      UNION ALL SELECT 'F', md5(string_agg(t::text, '|' ORDER BY graha, other_graha)) FROM (SELECT graha, other_graha, relation, classical_citation FROM {T2}) t""")


@pytest.fixture()
def db(disposable_pg):
    _seed_migration_250(disposable_pg)
    yield disposable_pg
    fs.drop_tables(disposable_pg, *TABLES)


def test_before_1401_the_database_holds_the_migration_250_shape(db):
    for g in ("Rahu", "Ketu"):
        assert _dig(db, g)[0] == "" and _dig(db, g)[3] == "{}", g
    assert {p: _fr(db, *p) for p in FIVE_PAIRS} == {p: old for p, (old, _new) in FIVE_PAIRS.items()}


def test_1401_writes_the_bphs_47_signs_without_inventing_a_degree_range(db):
    _apply_1401(db)
    for g, (mt, own) in NODE_DIGNITY.items():
        assert _dig(db, g) == [mt, "-", "-", own], g
    cite = fs.psql(db, f"SELECT classical_citation FROM {T1} WHERE graha='Rahu'")
    assert "bphs:PG573:C2 to bphs:PG574:C1" in cite and "The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively." in cite


def test_1401_writes_the_bphs_3_55_note_relations_for_exactly_the_five_pairs(db):
    _apply_1401(db)
    assert {p: _fr(db, *p) for p in FIVE_PAIRS} == {p: new for p, (_old, new) in FIVE_PAIRS.items()}
    cites = fs.psql(db, f"SELECT DISTINCT classical_citation FROM {T2} WHERE graha IN ('Rahu','Ketu') AND classical_citation LIKE '%bphs:PG40:C1%'").strip().split("\n")
    assert len(cites) == 2 and all("SR-DOCTRINE-H" in c for c in cites)


def test_1401_changes_nothing_else_exaltation_debilitation_variants_other_grahas_other_pairs(db):
    before = _rest_snapshot(db)
    _apply_1401(db)
    assert _rest_snapshot(db) == before
    assert fs.psql(db, f"SELECT count(*) FROM {T1}").strip() == "9" and fs.psql(db, f"SELECT count(*) FROM {T2}").strip() == "72"


def test_1401_replayed_leaves_the_same_rows(db):
    _apply_1401(db)
    once = _full_snapshot(db)
    _apply_1401(db)
    assert _full_snapshot(db) == once


@pytest.mark.parametrize("breakage, needle", [
    (f"UPDATE {T1} SET exaltation_sign = 'Gemini' WHERE graha = 'Rahu'", "bg_dignity_reference rows are not in the migration-250 or migration-1401 shape"),
    (f"UPDATE {T1} SET own_signs = ARRAY['Virgo']::text[] WHERE graha = 'Ketu'", "bg_dignity_reference rows are not in the migration-250 or migration-1401 shape"),
    (f"UPDATE {T2} SET relation = 'enemy' WHERE graha = 'Rahu' AND other_graha = 'Jupiter'", "node-friendship pairs are not in the migration-250 or migration-1401 shape"),
    (f"DELETE FROM {T2} WHERE graha = 'Sun' AND other_graha = 'Moon'", "bg_graha_naisargika_friendship has 71 rows"),
])
def test_1401_refuses_by_name_and_changes_nothing_when_the_tables_are_not_in_the_shape_it_corrects(db, breakage, needle):
    fs.psql(db, breakage)
    before = _full_snapshot(db)
    p = _run_1401(db)
    assert p.returncode != 0 and needle in p.stderr, p.stderr[:500]
    assert _full_snapshot(db) == before


def test_the_real_writer_rebuilds_exactly_the_rows_1401_wrote(db):
    """A migration alone would be undone by the next L0 rebuild: after 1401, running the real writer must leave the dignity and friendship tables byte-identical."""
    psycopg = pytest.importorskip("psycopg")
    _apply_1401(db)
    migrated = _full_snapshot(db, variants=False)
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_dignity_reference import BgDignityReferenceWriter
    conn = psycopg.connect(db.url, autocommit=True)
    try:
        res = BgDignityReferenceWriter().run(ContextSpec(asset_id=T1, build_id=RUN, db_conn=conn, config={}))
    finally:
        conn.close()
    assert res.rows_inserted == 151, res.notes
    assert _full_snapshot(db, variants=False) == migrated
    for g, (mt, own) in NODE_DIGNITY.items():
        assert _dig(db, g) == [mt, "-", "-", own], g
    assert {p: _fr(db, *p) for p in FIVE_PAIRS} == {p: new for p, (_old, new) in FIVE_PAIRS.items()}
