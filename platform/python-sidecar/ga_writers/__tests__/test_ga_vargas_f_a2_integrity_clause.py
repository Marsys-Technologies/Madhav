"""The F-A2 draft migration's integrity clauses must FAIL on empty / collapsed data.

`ga_vargas.integrity_check_sql` had four conjuncts, all `NOT EXISTS`-shaped, so a
table the builder could not read (RLS with no policy) or an emptied table passed it
(CLAUDE.md N.8; incident review F1; decision sheet Q-L1-01). The draft adds
  (e) non-vacuity: every declared (ayanamsha, varga) of the canonical chart holds
      its nine varga_position/sign rows,
  (f) key-grain completeness: house lords 12 / ashtakavarga 96 per (ayanamsha, varga),
      D30 lords 60 per ayanamsha.

Two layers:
 * text-shape tests (always run): the draft file is where the plan says, is NOT in a
   migration directory, carries the pre/post guards, and does not number itself;
 * a behaviour test against a real PostgreSQL (opt-in: set F_A2_PG_DSN to a
   DISPOSABLE database; the test creates and drops its own tables in a scratch
   schema and never touches anything else).
"""
from __future__ import annotations

import os
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[4]
DRAFT_DIR = REPO / "00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening"
DRAFT = DRAFT_DIR / "DRAFT_f_a2_key_widening.sql"
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


def _new_sql() -> str:
    text = DRAFT.read_text(encoding="utf-8")
    return re.search(r"\$ck\$(.*)\$ck\$", text, re.S).group(1)


def test_draft_is_a_draft_outside_every_migration_directory() -> None:
    assert DRAFT.is_file()
    assert "platform/migrations" not in str(DRAFT) and "supabase/migrations" not in str(DRAFT)
    assert not re.match(r"\d+_", DRAFT.name), "SS allocates the migration number"
    text = DRAFT.read_text(encoding="utf-8")
    assert "do NOT number or apply" in text
    for needle in ("SET LOCAL lock_timeout", "$pre$", "$post$", "WHERE asset_id = 'ga_vargas'"):
        assert needle in text


def test_new_check_keeps_the_four_original_conjuncts_and_adds_e_and_f() -> None:
    sql = _new_sql()
    for tag in ("(a) sign / sign_number", "(b) vargottama correctness", "(c) §N.5 D1 authority".replace("§", ""),
                "(d) identity range guard"):
        assert tag.split(")")[0] in sql
    assert "(e) NON-VACUITY" in sql and "(f) KEY-GRAIN COMPLETENESS" in sql
    assert sql.rstrip().endswith("AS integrity_passed")
    assert "< 9" in sql and "<> 12" in sql and "<> 96" in sql and "<> 60" in sql


# ---------------------------------------------------------------------------
# behaviour (opt-in, disposable PostgreSQL only)
# ---------------------------------------------------------------------------

DSN = os.environ.get("F_A2_PG_DSN")
needs_pg = pytest.mark.skipif(not DSN, reason="set F_A2_PG_DSN to a disposable PostgreSQL to run")

COLS = ("chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key", "fact_subject",
        "sign", "sign_number", "vargottama")
SUBJ = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER", "Jupiter": "JUP",
        "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN"}
AYAS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")


def _build_rows() -> list[dict]:
    """Real writer rows for the canonical chart, five ayanamshas, no database."""
    from ga_writers import ga_vargas_writer as w
    from ga_writers.__tests__.test_ga_vargas_key_widening import FakeDB, BIRTH, BUILD
    w._SHASHTIAMSHA_CACHE = {i: {"quality": "soumya", "deity_name": f"D{i}"} for i in range(1, 61)}
    db = FakeDB()
    w.build_ga_vargas(CANON, BUILD, conn=db, birth_params=BIRTH, ayanamsha_subset=list(AYAS))
    return list(db.rows.values())


@pytest.fixture()
def pg():
    import psycopg
    conn = psycopg.connect(DSN, autocommit=False)
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS f_a2_scratch")
    cur.execute("SET LOCAL search_path = f_a2_scratch, pg_catalog")
    cur.execute("""
        CREATE TABLE chart_divisionals (
          chart_id text, graha text, ayanamsha_id text, varga text, fact_category text, fact_key text,
          fact_subject text, sign text, sign_number int, vargottama boolean)""")
    cur.execute("""
        CREATE TABLE chart_facts (
          chart_id text, ayanamsha_id text, fact_category text, fact_key text, fact_value_text text, fact_subject text)""")
    cur.execute("CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text)")
    yield conn, cur
    conn.rollback()
    conn.close()


def _load(cur, rows: list[dict]) -> None:
    cur.execute("TRUNCATE chart_divisionals, chart_facts")
    cur.executemany(
        f"INSERT INTO chart_divisionals ({', '.join(COLS)}) VALUES ({', '.join('%(' + c + ')s' for c in COLS)})",
        [{c: r.get(c) for c in COLS} for r in rows],
    )
    # conjunct (c): the canonical D1 signs must equal chart_facts' own
    cur.executemany(
        "INSERT INTO chart_facts VALUES (%s,%s,'graha_position','sign',%s,%s)",
        [(r["chart_id"], r["ayanamsha_id"], r["sign"], SUBJ[r["graha"]]) for r in rows
         if r["varga"] == "D1" and r["fact_category"] == "varga_position" and r["fact_key"] == "sign"
         and r["graha"] in SUBJ],
    )


def _verdict(cur) -> bool:
    cur.execute(_new_sql())
    return cur.fetchone()[0]


def _collapse(rows: list[dict], cols: tuple[str, ...]) -> list[dict]:
    seen: dict[tuple, dict] = {}
    for r in rows:
        seen.setdefault(tuple(r.get(c) for c in cols), r)
    return list(seen.values())


@needs_pg
def test_check_fails_when_empty_or_collapsed_and_passes_when_complete(pg) -> None:
    conn, cur = pg
    full = [r for r in _build_rows() if r["ayanamsha_id"] != "INVARIANT"]

    _load(cur, [])
    assert _verdict(cur) is False, "an empty (or unreadable) table must not pass"

    _load(cur, full)
    assert _verdict(cur) is True, "the complete, widened-grain data must pass"

    legacy = _collapse(full, ("chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key"))
    assert len(legacy) < len(full)
    _load(cur, legacy)
    assert _verdict(cur) is False, "data collapsed by the six-column key must fail (f)"

    # too few: one ayanamsha x varga loses one position row
    victim = next(r for r in full if r["fact_category"] == "varga_position" and r["fact_key"] == "sign"
                  and r["varga"] == "D9" and r["ayanamsha_id"] == "raman" and r["graha"] == "Ketu")
    _load(cur, [r for r in full if r is not victim])
    assert _verdict(cur) is False, "too few rows for one (ayanamsha, varga) must fail (e)"

    # rows for another chart do not satisfy the canonical chart
    _load(cur, [dict(r, chart_id="00000000-0000-0000-0000-000000000001") for r in full])
    assert _verdict(cur) is False


@needs_pg
def test_draft_migration_applies_once_and_refuses_a_second_run(pg) -> None:
    conn, cur = pg
    old_body = re.search(
        r"\$SQL\$(.*?)\$SQL\$",
        (REPO / "platform/migrations/884_nirmana_l1_ga_vargas_integrity_check_scope.sql").read_text(encoding="utf-8"),
        re.S,
    ).group(1)
    cur.execute("INSERT INTO asset_registry VALUES ('ga_vargas', %s)", (old_body,))
    body = DRAFT.read_text(encoding="utf-8").replace("BEGIN;", "", 1).replace("COMMIT;", "")
    cur.execute(body)
    cur.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_vargas'")
    assert "(e) NON-VACUITY" in cur.fetchone()[0]
    import psycopg
    with pytest.raises(psycopg.errors.RaiseException, match="not the text this migration was written against"):
        cur.execute("SAVEPOINT s")
        cur.execute(body)
