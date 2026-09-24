"""G-9 (remainder §8.4): migration 1085 bg_transit_rules vedha repair — verified
against the disposable remainder Postgres only.

The fixture reproduces the spec's printed before-state
(KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md §1–§5) with explicit ids: the three wrong
Venus rows (35, 44, 45), their two transposition twins (33, 179), the rest of
the Venus nine, the five Mercury rows (21–25), six Rāhu/Ketu rows
(187–189, 196–198), and one row per remaining classical graha for the re-cite
count. The migration is then applied verbatim and the spec's after-state
SELECTs are asserted. The table DDL is migration 266's own
``CREATE TABLE bg_transit_rules`` (copied; 266's asset_registry seeding is out
of scope for this verification).

NOT_RUN (skip with reason) when the disposable DB is unreachable — never a
fallback to any other DSN.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import psycopg
import pytest

DSN = os.environ.get(
    "GOCHARA_REMAINDER_DSN", "postgresql://wp6:disposable@localhost:55434/wp6"
)

MIGRATION_1085 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1085_nirmana_l0_bg_transit_rules_vedha_repair.sql"
)

BPHS_CIT = "BPHS Ch.29 (Gochara Phala — Transit Results)"
PD_CH26_CIT = "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"

DDL = """
DROP TABLE IF EXISTS bg_transit_rules;
CREATE TABLE bg_transit_rules (
    id                 SERIAL PRIMARY KEY,
    rule_type          TEXT NOT NULL
                       CHECK (rule_type IN ('favourable', 'unfavourable', 'vedha')),
    graha              TEXT NOT NULL,
    primary_house      INTEGER NOT NULL
                       CHECK (primary_house BETWEEN 1 AND 12),
    vedha_house        INTEGER
                       CHECK (vedha_house BETWEEN 1 AND 12),
    phala              TEXT NOT NULL,
    classical_citation TEXT NOT NULL,
    rule_notes         TEXT,
    CONSTRAINT bg_transit_rules_graha_type_house_unique
        UNIQUE (graha, rule_type, primary_house)
);
"""

# (id, graha, primary_house, vedha_house, citation)
FIXTURE_ROWS = [
    (1, "sun", 3, 9, BPHS_CIT),
    (7, "moon", 1, 5, BPHS_CIT),
    (15, "mars", 3, 12, BPHS_CIT),
    (21, "mercury", 2, 5, BPHS_CIT),
    (22, "mercury", 4, 3, BPHS_CIT),
    (23, "mercury", 6, 9, BPHS_CIT),
    (24, "mercury", 10, 8, BPHS_CIT),
    (25, "mercury", 11, 12, BPHS_CIT),
    (26, "jupiter", 2, 12, BPHS_CIT),
    (33, "venus", 1, 8, BPHS_CIT),
    (34, "venus", 2, 7, BPHS_CIT),
    (35, "venus", 3, 11, BPHS_CIT),
    (36, "venus", 4, 10, BPHS_CIT),
    (37, "venus", 5, 9, BPHS_CIT),
    (44, "venus", 8, 1, BPHS_CIT),
    (45, "venus", 9, 2, BPHS_CIT),
    (179, "venus", 11, 3, BPHS_CIT),
    (180, "venus", 12, 6, BPHS_CIT),
    (46, "saturn", 3, 12, BPHS_CIT),
    (187, "rahu", 3, 9, BPHS_CIT),
    (188, "rahu", 6, 12, BPHS_CIT),
    (189, "rahu", 11, 5, PD_CH26_CIT),
    (196, "ketu", 3, 9, BPHS_CIT),
    (197, "ketu", 6, 12, BPHS_CIT),
    (198, "ketu", 11, 5, PD_CH26_CIT),
]

VENUS_TEXT_PAIRS = {
    (1, 8), (2, 7), (3, 1), (4, 10), (5, 9),
    (8, 5), (9, 11), (11, 3), (12, 6),
}


@pytest.fixture()
def db():
    try:
        conn = psycopg.connect(DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable remainder database unreachable ({exc})")
    with conn.cursor() as cur:
        cur.execute(DDL)
        for row_id, graha, primary, vedha, cit in FIXTURE_ROWS:
            cur.execute(
                """
                INSERT INTO bg_transit_rules
                    (id, rule_type, graha, primary_house, vedha_house,
                     phala, classical_citation, rule_notes)
                VALUES (%s, 'favourable', %s, %s, %s, %s, %s, %s)
                """,
                (
                    row_id, graha, primary, vedha,
                    "fixture phala", cit, f"Vedha from {vedha}th nullifies result",
                ),
            )
        cur.execute(
            "SELECT setval(pg_get_serial_sequence('bg_transit_rules','id'), "
            "(SELECT max(id) FROM bg_transit_rules))"
        )
    yield conn
    conn.close()


def _apply_migration(conn) -> None:
    sql = MIGRATION_1085.read_text()
    up = sql.split("-- DOWN (manual rollback):")[0]
    with conn.cursor() as cur:
        cur.execute(up)


def _rows(conn, query, args=()):
    with conn.cursor() as cur:
        cur.execute(query, args)
        return cur.fetchall()


def test_g9_before_state_matches_spec(db):
    pairs = {
        r[0]: (r[1], r[2])
        for r in _rows(
            db,
            "SELECT id, primary_house, vedha_house FROM bg_transit_rules "
            "WHERE id IN (35,44,45,33,179)",
        )
    }
    assert pairs == {35: (3, 11), 44: (8, 1), 45: (9, 2), 33: (1, 8), 179: (11, 3)}
    assert _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules WHERE graha='mercury' "
        "AND rule_type='favourable' AND vedha_house IS NOT NULL",
    )[0][0] == 5
    assert _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules "
        "WHERE classical_citation LIKE %s",
        ("%BPHS Ch.29%",),
    )[0][0] == 23


def test_g9_after_state_matches_spec(db):
    _apply_migration(db)

    # §2 — the three Venus rows updated to the text; twins untouched.
    pairs = {
        r[0]: (r[1], r[2])
        for r in _rows(
            db,
            "SELECT id, primary_house, vedha_house FROM bg_transit_rules "
            "WHERE id IN (35,44,45,33,179)",
        )
    }
    assert pairs == {35: (3, 1), 44: (8, 5), 45: (9, 11), 33: (1, 8), 179: (11, 3)}

    # §2 — the Venus set is exactly the text's nine pairs.
    venus = set(
        _rows(
            db,
            "SELECT primary_house, vedha_house FROM bg_transit_rules "
            "WHERE graha='venus' AND rule_type='favourable' "
            "AND vedha_house IS NOT NULL",
        )
    )
    assert venus == VENUS_TEXT_PAIRS

    # §3 — Mercury gains the (8,1) pair with the PG323:C1 citation and the
    # śl.17 phala; count is six.
    merc = _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules WHERE graha='mercury' "
        "AND rule_type='favourable' AND vedha_house IS NOT NULL",
    )[0][0]
    assert merc == 6
    inserted = _rows(
        db,
        "SELECT vedha_house, phala, classical_citation FROM bg_transit_rules "
        "WHERE graha='mercury' AND rule_type='favourable' AND primary_house=8",
    )
    assert inserted == [
        (1, "Gain of wealth and birth of children",
         "Phaladīpikā Adh. XXVI śl. 6 — phaladeepika:PG323:C1")
    ]

    # §1 — every favourable+vedha row of a classical graha is re-cited at page
    # grain to the right chunk; no "BPHS Ch.29" string survives anywhere (G-8).
    assert _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules "
        "WHERE classical_citation LIKE %s",
        ("%BPHS Ch.29%",),
    )[0][0] == 0
    recited = dict(
        _rows(
            db,
            "SELECT graha, count(*) FROM bg_transit_rules "
            "WHERE rule_type='favourable' AND vedha_house IS NOT NULL "
            "AND graha IN ('sun','moon','mars','mercury','jupiter','venus','saturn') "
            "GROUP BY graha",
        )
    )
    for graha, n in recited.items():
        expected_chunk = (
            "PG322:C1" if graha in ("sun", "moon", "mars", "saturn") else "PG323:C1"
        )
        bad = _rows(
            db,
            "SELECT count(*) FROM bg_transit_rules "
            "WHERE rule_type='favourable' AND vedha_house IS NOT NULL "
            "AND graha=%s AND classical_citation NOT LIKE %s",
            (graha, f"%{expected_chunk}"),
        )[0][0]
        assert bad == 0, f"{graha}: {bad} of {n} rows not re-cited to {expected_chunk}"

    # §5 — six nodal rows marked uncited_extension with the N-14 note; the two
    # Phaladeepika-cited rows keep their string; nothing deleted.
    nodal = _rows(
        db,
        "SELECT count(*), count(*) FILTER (WHERE uncited_extension), "
        "count(*) FILTER (WHERE rule_notes LIKE '%%disposition follows N-14%%') "
        "FROM bg_transit_rules "
        "WHERE graha IN ('rahu','ketu') AND rule_type='favourable' "
        "AND vedha_house IS NOT NULL",
    )[0]
    assert nodal == (6, 6, 6)
    kept = _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules "
        "WHERE graha IN ('rahu','ketu') "
        "AND classical_citation = %s",
        (PD_CH26_CIT,),
    )[0][0]
    assert kept == 2


def test_g9_migration_is_idempotent(db):
    _apply_migration(db)
    snapshot = _rows(
        db,
        "SELECT id, rule_type, graha, primary_house, vedha_house, phala, "
        "classical_citation, rule_notes, uncited_extension "
        "FROM bg_transit_rules ORDER BY id",
    )
    _apply_migration(db)
    again = _rows(
        db,
        "SELECT id, rule_type, graha, primary_house, vedha_house, phala, "
        "classical_citation, rule_notes, uncited_extension "
        "FROM bg_transit_rules ORDER BY id",
    )
    # The §4 note append is deliberately once-only: the guarded WHERE on
    # (primary_house, vedha_house) plus uncited_extension re-set is stable, but
    # rule_notes concatenation would repeat — assert it does not.
    assert snapshot == again


def test_g9_down_block_reverses(db):
    _apply_migration(db)
    sql = MIGRATION_1085.read_text()
    down = sql.split("-- DOWN (manual rollback):")[1]
    down = re.sub(r"^-- ?", "", down, flags=re.MULTILINE)
    down = "\n".join(
        line for line in down.splitlines() if not set(line.strip()) <= {"="}
    )
    with db.cursor() as cur:
        cur.execute(down)
    pairs = {
        r[0]: (r[1], r[2])
        for r in _rows(
            db,
            "SELECT id, primary_house, vedha_house FROM bg_transit_rules "
            "WHERE id IN (35,44,45,33,179)",
        )
    }
    assert pairs == {35: (3, 11), 44: (8, 1), 45: (9, 2), 33: (1, 8), 179: (11, 3)}
    assert _rows(
        db,
        "SELECT count(*) FROM bg_transit_rules WHERE graha='mercury' "
        "AND rule_type='favourable' AND vedha_house IS NOT NULL",
    )[0][0] == 5
    cols = _rows(
        db,
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_name='bg_transit_rules' AND column_name='uncited_extension'",
    )[0][0]
    assert cols == 0
