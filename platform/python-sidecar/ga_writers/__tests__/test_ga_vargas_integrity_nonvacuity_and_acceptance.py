"""Migration 1222's non-vacuity clause and the S-L1 acceptance script (F-A2, Q-L1-01, SS direction on #2858).

`ga_vargas.integrity_check_sql` had four conjuncts, all `NOT EXISTS`-shaped, so a table the
builder could not read (RLS with no policy) or an emptied table passed it (CLAUDE.md N.8; incident
review F1). Migration 1222 adds ONE conjunct, (e) non-vacuity: every declared (ayanamsha, varga) of
the canonical chart holds its nine varga_position/sign rows. SS dropped the key-grain numbers from
the integrity check; they are S-L1 ACCEPTANCE CRITERIA checked by
`s_l1_ga_vargas_acceptance_check.sql` (read-only, run by SS as suvarna_reader after the rebuild).

Two layers:
 * text-shape tests (always run);
 * behaviour tests against a real PostgreSQL (opt-in: set F_A2_PG_DSN to a DISPOSABLE database;
   the tests create their own tables in a scratch schema and never touch anything else).
"""
from __future__ import annotations

import os
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[4]
# Migration 1222's canonical file lives in PR #2943 (S-L1 W1), NOT here (SS ruling: this PR carries no migration
# file; two different copies under one filename would collide in the migrate.ts checksum). The text-shape and
# behaviour tests below read a BYTE-IDENTICAL vendored copy, pinned by sha256; the drift guard compares it with the
# real file as soon as that file exists in the tree (after W1). Post-W1 item: delete the fixture and point
# MIGRATION at CANONICAL_MIGRATION.
CANONICAL_MIGRATION = REPO / "platform/migrations/1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql"
CANONICAL_NAME = "1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql"
MIGRATION_FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "migration_1222_canonical_from_pr2943.sql"
MIGRATION_FIXTURE_SHA256 = "10b6aac633287d10d13049baacc650a223f5f481f13417a02e02e167c87e3212"
MIGRATION = MIGRATION_FIXTURE
ACCEPTANCE = REPO / "00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/s_l1_ga_vargas_acceptance_check.sql"
BASE_884 = REPO / "platform/migrations/884_nirmana_l1_ga_vargas_integrity_check_scope.sql"
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


def _new_sql() -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", MIGRATION.read_text(encoding="utf-8"), re.S).group(1)


def _old_sql() -> str:
    return re.search(r"\$SQL\$(.*?)\$SQL\$", BASE_884.read_text(encoding="utf-8"), re.S).group(1)


def test_vendored_migration_fixture_is_the_pinned_canonical_copy() -> None:
    """The fixture must be byte-identical to PR #2943's 1222 (sha256 pinned), and -- once the real migration file
    exists in the tree (after W1) -- byte-identical to it: any drift between the copy these tests read and the file
    migrate.ts applies fails here, loudly."""
    import hashlib
    data = MIGRATION_FIXTURE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == MIGRATION_FIXTURE_SHA256
    if CANONICAL_MIGRATION.exists():
        assert CANONICAL_MIGRATION.read_bytes() == data, (
            "platform/migrations/1222 exists now: the vendored fixture must equal it byte-for-byte; "
            "delete the fixture and point MIGRATION at CANONICAL_MIGRATION"
        )


def test_migration_is_a_routine_guarded_asset_registry_update() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert CANONICAL_NAME == "1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql"
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", text, re.M | re.I), "transaction ownership belongs to migrate.ts"
    for needle in ("SET LOCAL lock_timeout", "$pre$", "$post$", "WHERE asset_id = 'ga_vargas'",
                   "MERGE = APPLY"):
        assert needle in text
    # touches asset_registry and nothing else: no DDL, no other table
    assert not re.search(r"\b(ALTER|CREATE|DROP|GRANT|REVOKE|TRUNCATE|DELETE)\b", re.sub(r"--[^\n]*", "", text.split("$ck$")[0]
                                                                                       + text.split("$ck$")[-1]), re.I)
    # exactly ONE UPDATE statement (count on the comment-stripped text: the canonical header mentions it in prose)
    assert len(re.findall(r"UPDATE asset_registry", re.sub(r"--[^\n]*", "", text))) == 1


def test_new_check_is_the_old_check_plus_exactly_conjunct_e() -> None:
    new, old = _new_sql(), _old_sql()
    for tag in ("(a) sign / sign_number", "(b) vargottama correctness", "(d) identity range guard"):
        assert tag in new and tag in old
    assert "(e) NON-VACUITY" in new and "(e) NON-VACUITY" not in old
    assert "(f)" not in new, "SS dropped the key-grain clause; those numbers are acceptance criteria"
    assert not re.search(r"<> *(12|96|60)\b", new), "no bare count pins in integrity_check_sql"
    assert new.rstrip().endswith("AS integrity_passed")
    assert "< 9" in new


def test_the_md5_guards_match_the_texts() -> None:
    import hashlib
    text = MIGRATION.read_text(encoding="utf-8")
    assert hashlib.md5(_old_sql().encode()).hexdigest() == "255af7c5194553e19f7009c1e8774d8a"
    code = re.sub(r"--[^\n]*", "", text)  # executable SQL only; the canonical header also documents the md5s in prose
    new_md5 = hashlib.md5(_new_sql().encode()).hexdigest()
    # canonical (PR #2943) shape: the pre-check names the new md5 once (idempotent skip) and the post-check once
    assert code.count(new_md5) == 2, "the pre-check (idempotent skip) and the post-check name the new text's md5"
    assert "IF v_md5 IS DISTINCT FROM '%s'" % new_md5 in code, "the post-check compares against the new md5"
    assert text.count("255af7c5194553e19f7009c1e8774d8a") >= 2, "the pre-check and the header name the base md5"


def test_acceptance_script_is_a_single_read_only_select() -> None:
    sql = ACCEPTANCE.read_text(encoding="utf-8")
    code = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|ALTER|CREATE|DROP|GRANT|TRUNCATE|SET)\b", code, re.I)
    assert code.strip().lower().startswith("with") and code.strip().endswith(";")
    for n in ("38596", "7718", "12", "96", "60"):
        assert n in code


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
SIX = ("chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key")


@pytest.fixture(scope="module")
def built_rows() -> list[dict]:
    """Real writer rows for the canonical chart, five ayanamshas, real D60 reference, no database."""
    from ga_writers import ga_vargas_writer as w
    from ga_writers.__tests__.test_ga_vargas_key_widening import FakeDB, BIRTH, BUILD, real_deity_cache
    saved = w._SHASHTIAMSHA_CACHE
    w._SHASHTIAMSHA_CACHE = real_deity_cache()
    try:
        db = FakeDB()
        w.build_ga_vargas(CANON, BUILD, conn=db, birth_params=BIRTH, ayanamsha_subset=list(AYAS))
        return list(db.rows.values())
    finally:
        w._SHASHTIAMSHA_CACHE = saved


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


def _acceptance(cur) -> dict[str, str]:
    cur.execute(ACCEPTANCE.read_text(encoding="utf-8"))
    return {row[1].split(" ")[0]: row[4] for row in cur.fetchall()}


def _collapse(rows: list[dict], cols: tuple[str, ...]) -> list[dict]:
    seen: dict[tuple, dict] = {}
    for r in rows:
        seen.setdefault(tuple(r.get(c) for c in cols), r)
    return list(seen.values())


@needs_pg
def test_nonvacuity_fails_when_empty_or_short_and_passes_when_complete(pg, built_rows) -> None:
    conn, cur = pg
    full = built_rows

    _load(cur, [])
    assert _verdict(cur) is False, "an empty (or unreadable) table must not pass"

    _load(cur, full)
    assert _verdict(cur) is True, "complete data must pass"

    # too few: one ayanamsha x varga loses one position row
    victim = next(r for r in full if r["fact_category"] == "varga_position" and r["fact_key"] == "sign"
                  and r["varga"] == "D9" and r["ayanamsha_id"] == "raman" and r["graha"] == "Ketu")
    _load(cur, [r for r in full if r is not victim])
    assert _verdict(cur) is False, "too few rows for one (ayanamsha, varga) must fail"

    # an entire declared varga missing for one ayanamsha
    _load(cur, [r for r in full if not (r["ayanamsha_id"] == "true_chitra" and r["varga"] == "D2700")])
    assert _verdict(cur) is False

    # rows for another chart do not satisfy the canonical chart
    _load(cur, [dict(r, chart_id="00000000-0000-0000-0000-000000000001") for r in full])
    assert _verdict(cur) is False


@needs_pg
def test_nonvacuity_alone_does_not_pin_the_key_grain(pg, built_rows) -> None:
    """SS dropped the grain numbers from integrity_check_sql: data collapsed by the six-column key still
    passes the integrity check (it is the acceptance script's job to catch it)."""
    conn, cur = pg
    _load(cur, _collapse(built_rows, SIX))
    assert _verdict(cur) is True


@needs_pg
def test_acceptance_script_passes_complete_data_and_names_what_failed(pg, built_rows) -> None:
    conn, cur = pg
    _load(cur, built_rows)
    res = _acceptance(cur)
    assert res["C1"] == res["C2"] == res["C3"] == res["C4"] == res["C5"] == res["C6"] == res["C7"] == "PASS", res
    assert res["ACCEPTED"] == "PASS"

    legacy = _collapse(built_rows, SIX)
    _load(cur, legacy)
    res = _acceptance(cur)
    assert [k for k in ("C1", "C2", "C3", "C4", "C5", "C6") if res[k] == "FAIL"] == ["C1", "C2", "C3", "C4", "C5", "C6"]
    assert res["C7"] == "PASS" and res["ACCEPTED"] == "FAIL"

    _load(cur, [])
    assert _acceptance(cur)["ACCEPTED"] == "FAIL"

    # one D30 row short per ayanamsha: only C1/C2/C6 move
    drop = {(r["ayanamsha_id"]) for r in built_rows}
    short = [r for r in built_rows if not (r["fact_category"] == "varga_d30_lord_per_amsa" and r["fact_subject"] == "D30.S12"
                                           and r["fact_key"].startswith("Venus"))]
    _load(cur, short)
    res = _acceptance(cur)
    assert res["C6"] == "FAIL" and res["C4"] == "PASS" and res["C5"] == "PASS" and res["ACCEPTED"] == "FAIL"
    assert drop


@needs_pg
def test_migration_applies_once_is_idempotent_and_refuses_an_unexpected_text(pg) -> None:
    """Canonical 1222 (PR #2943): apply once; a second run is a no-op (the new text is already in place);
    any OTHER text (neither the base nor the new one) is refused and left untouched."""
    import psycopg
    conn, cur = pg
    cur.execute("INSERT INTO asset_registry VALUES ('ga_vargas', %s)", (_old_sql(),))
    body = MIGRATION.read_text(encoding="utf-8")
    cur.execute(body)
    cur.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_vargas'")
    assert cur.fetchone()[0] == _new_sql()
    cur.execute(body)  # second run: idempotent no-op, must not raise and must not change the text
    cur.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_vargas'")
    assert cur.fetchone()[0] == _new_sql()
    cur.execute("UPDATE asset_registry SET integrity_check_sql = 'SELECT true AS integrity_passed' WHERE asset_id='ga_vargas'")
    with pytest.raises(psycopg.errors.RaiseException, match="not the text this migration was written against"):
        cur.execute("SAVEPOINT s")
        cur.execute(body)
