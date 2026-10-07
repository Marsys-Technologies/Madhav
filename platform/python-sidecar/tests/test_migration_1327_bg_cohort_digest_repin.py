"""Migration 1327 (Suvarna routine migration; companion item (b) of the delta review of PR #3215, SS ruling N-190): bg_cohort's
registered integrity_check_sql keeps its (already content-only) whole-table digest DEFINITION and gets the NEW PIN the L0 rebuild
will produce once PR #3215 has landed (Ketu retrograde flag mirrors Rahu, sampling_method v2 -> v3).

Migration 626 pinned sha256(string_agg(jsonb_build_array(synthetic_id, birth_datetime_utc, birth_lat, birth_lon, ayanamsha_key,
positions, sampling_method, source_citation)::text, E'\\n' ORDER BY synthetic_id)) = 921b0f62...; that digest excludes build_id /
computed_at / id (the run-identity columns), so the only thing a rebuild that changes content invalidates is the pinned VALUE.

Two tiers:
  * STATIC (always runs, pure Python): the committed fixture is the 10,000 stored production rows (each row exactly as PostgreSQL's
    own jsonb_build_array(...)::text rendered it, read 2026-10-07). Hashing it reproduces 921b0f62 (method proof against production).
    Applying the PR's two changes to those rows (Ketu flag := Rahu flag; sampling_method v3) hashes to c516b597...; the change is
    exactly one JSON path in 7,475 rows plus the method label in all 10,000; isolation digests for each change alone. The migration's
    literals equal this test's independently spelled ones; NEW text = OLD text with exactly the one 64-hex literal replaced.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration to a DISPOSABLE cluster (initdb in a temp dir, own
    port, trust auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found. It loads the 10,000 rows into a table
    with the production column types and evaluates the REAL digest conjunct of the OLD and NEW registry text: OLD true / NEW false on
    today's rows (the accepted window), OLD false / NEW true on the post-rebuild content, NEW false on a Ketu-only or method-only
    change and on any content mutation, NEW unaffected by build_id / computed_at / id (content-only), plus guard/idempotency/
    serving-effect/silent-no-op behaviour of the migration. It does NOT prove production state (read from production structure after
    deploy; Trap 103) and does not prove the rebuild reproduces the projection (replay evidence is in the migration header).
"""
from __future__ import annotations

import copy
import glob
import gzip
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1327 = _REPO / "platform" / "migrations" / "1327_bg_cohort_integrity_digest_repin.sql"
_M626 = _REPO / "platform" / "supabase" / "migrations" / "626_nirmana_l0_cohort_exact_contract.sql"
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bg_cohort_1327" / "stored_rows_pre1327_2026-10-07.jsonl.gz"

OLD_MD5 = "391d0f02482c1a669400a895286103f5"
NEW_MD5 = "c9fa9795e24ed65843026adf3ba74252"
TEXT_LEN = 1959
OLD_PIN = "921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa"
NEW_PIN = "c516b597165e2e248b918a4001dce6fd77f137468f9ed8a029d5488613a7c844"
METHOD_ONLY = "d1c4c6142bc09b9d320fe131289b651c40e89abe802fc5847d433301699d8e0e"
KETU_ONLY = "32653c6cd644e3d29bb25c9e1357b66811b8a7310df96b872e96f03421b5c7f0"
V2 = "uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v2"
V3 = "uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v3"


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


# OLD text = the $check$ literal of migration 626 (never edited after apply); it is the live production text.
OLD_TEXT = re.search(r"\$check\$(.*?)\$check\$", _M626.read_text(encoding="utf-8"), re.S).group(1)
NEW_TEXT = OLD_TEXT.replace(OLD_PIN, NEW_PIN)

CANON = "482012f1-710e-4a25-994a-93821f5871aa"


# -- jsonb text rendering (verified against PostgreSQL: zero round-trip mismatches over the 10,000 rows) ----------------------

def _ser(o) -> str:
    if isinstance(o, bool):
        return "true" if o else "false"
    if o is None:
        return "null"
    if isinstance(o, Decimal):
        return format(o, "f") if "E" in str(o).upper() else str(o)
    if isinstance(o, int):
        return str(o)
    if isinstance(o, str):
        return json.dumps(o, ensure_ascii=False)
    if isinstance(o, list):
        return "[" + ", ".join(_ser(x) for x in o) + "]"
    if isinstance(o, dict):
        keys = sorted(o, key=lambda k: (len(k.encode()), k.encode()))
        return "{" + ", ".join(json.dumps(k, ensure_ascii=False) + ": " + _ser(o[k]) for k in keys) + "}"
    raise TypeError(type(o))


def _sha(rows: list[str]) -> str:
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def stored_lines() -> list[str]:
    with gzip.open(_FIXTURE, "rt", encoding="utf-8") as f:
        return f.read().split("\n")[:-1]


@pytest.fixture(scope="module")
def stored_objs(stored_lines):
    return [json.loads(l, parse_float=Decimal) for l in stored_lines]


def _project(o, *, ketu=True, method=True):
    o = copy.deepcopy(o)
    if ketu:
        o[5]["Ketu"]["is_retrograde"] = o[5]["Rahu"]["is_retrograde"]
    if method:
        assert o[6] == V2
        o[6] = V3
    return o


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_old_text_is_the_live_production_text_and_carries_the_pin_once():
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == TEXT_LEN
    assert OLD_TEXT.count(OLD_PIN) == 1 and NEW_PIN not in OLD_TEXT


def test_static_new_text_is_the_old_text_with_exactly_the_one_literal_replaced():
    assert _md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == TEXT_LEN
    head, tail = OLD_TEXT.split(OLD_PIN)
    assert NEW_TEXT == head + NEW_PIN + tail
    # the digest DEFINITION (columns, ordering, casting) and the md digest conjunct are untouched
    assert "'1f9e7fcf96941e891462ba1acd46b6c053f58d72d0dcb243a65d16a818c4decd'" in NEW_TEXT
    assert "synthetic_id,birth_datetime_utc,birth_lat,birth_lon,ayanamsha_key,\n      positions,sampling_method,source_citation" in NEW_TEXT
    assert "build_id" not in NEW_TEXT and "computed_at" not in NEW_TEXT


def test_static_fixture_reproduces_the_production_pin_method_proof(stored_lines):
    assert len(stored_lines) == 10000
    assert _sha(stored_lines) == OLD_PIN


def test_static_serializer_matches_postgres_rendering_on_every_row(stored_lines, stored_objs):
    assert [_ser(o) for o in stored_objs] == stored_lines
    assert [o[0] for o in stored_objs] == list(range(1, 10001))


def test_static_post_rebuild_projection_digest_is_the_new_pin_and_is_explained(stored_objs):
    assert _sha([_ser(_project(o)) for o in stored_objs]) == NEW_PIN
    assert _sha([_ser(_project(o, ketu=False)) for o in stored_objs]) == METHOD_ONLY
    assert _sha([_ser(_project(o, method=False)) for o in stored_objs]) == KETU_ONLY
    changed_paths, rows_changed, other = set(), 0, 0
    for o in stored_objs:
        n = _project(o)
        other += sum(1 for i in (0, 1, 2, 3, 4, 7) if o[i] != n[i])
        if o[5] != n[5]:
            rows_changed += 1
            for g in o[5]:
                for k in o[5][g]:
                    if o[5][g][k] != n[5][g][k]:
                        changed_paths.add((g, k))
    assert rows_changed == 7475 and changed_paths == {("Ketu", "is_retrograde")} and other == 0
    assert sum(1 for o in stored_objs if o[5]["Rahu"]["is_retrograde"]) == 7475
    assert not any(o[5]["Ketu"]["is_retrograde"] for o in stored_objs)
    assert {o[6] for o in stored_objs} == {V2}


def test_static_migration_literals_equal_the_independently_spelled_ones():
    sql = _M1327.read_text()
    for lit in (f"c_old_md5 constant text := '{OLD_MD5}'", f"c_new_md5 constant text := '{NEW_MD5}'",
                f"c_old_pin constant text := '{OLD_PIN}'", f"c_new_pin constant text := '{NEW_PIN}'"):
        assert lit in sql, lit


def test_static_one_guarded_update_of_integrity_check_sql_only_lock_timeout_first():
    code = _code(_M1327)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    assert "AND md5(integrity_check_sql) = c_old_md5;" in code
    assert "replace(integrity_check_sql, c_old_pin, c_new_pin)" in code
    assert code.count("WHERE asset_id = 'bg_cohort'") >= 2
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code.replace("BEGIN\n", ""))
    assert not re.search(r"^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b", code, re.I | re.M)
    assert code.count("RAISE EXCEPTION") == 1 and "update did not take" in code
    assert "is not the text this migration was written against" in code and "NO-OP" in code


# -- LIVE tier: disposable PostgreSQL -------------------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1327pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m27", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off -c timezone=UTC"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"t{_n}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")
        c.execute(f"ALTER DATABASE {name} SET timezone = 'UTC'")

    def connect():
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


_REGISTRY_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type,
                scope, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""

# bg_synthetic_cohort with the production column types (information_schema, read 2026-10-07).
_COHORT_DDL = """
CREATE TABLE bg_synthetic_cohort (
    id bigserial, synthetic_id integer PRIMARY KEY, birth_datetime_utc timestamptz NOT NULL, birth_lat numeric(7,4) NOT NULL,
    birth_lon numeric(7,4) NOT NULL, ayanamsha_key text NOT NULL, positions jsonb NOT NULL, sampling_method text NOT NULL,
    source_citation text NOT NULL, build_id uuid NOT NULL DEFAULT '00000000-0000-4000-8000-000000000001',
    computed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z');
CREATE TABLE stage_rows (a jsonb);
"""


def _setup(connect, text: str = OLD_TEXT, with_row: bool = True):
    with connect() as c:
        c.execute(_REGISTRY_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql, target_table, scope, has_writer) "
                      "VALUES ('bg_cohort','brahmagyan',%s,'bg_synthetic_cohort','global',true)", (text,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql) VALUES ('bg_other','brahmagyan','SELECT true')")
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES "
                      "('bg_cohort', %s, 'fresh'), ('bg_other', %s, 'fresh')", (CANON, CANON))
        c.commit()


def _load_cohort(connect, stored_lines):
    with connect() as c:
        c.execute(_COHORT_DDL)
        with c.cursor().copy("COPY stage_rows (a) FROM STDIN") as cp:
            for l in stored_lines:
                cp.write_row((l,))
        c.execute("INSERT INTO bg_synthetic_cohort (synthetic_id, birth_datetime_utc, birth_lat, birth_lon, ayanamsha_key, "
                  "positions, sampling_method, source_citation) SELECT (a->>0)::int, (a->>1)::timestamptz, (a->>2)::numeric, "
                  "(a->>3)::numeric, a->>4, a->5, a->>6, a->>7 FROM stage_rows")
        c.commit()


def _apply_rebuild_content(connect):
    """What the rebuild stores (PR #3215): Ketu flag := Rahu flag; sampling_method v3; build_id / computed_at / id are run identity."""
    with connect() as c:
        c.execute("UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Ketu,is_retrograde}', positions#>'{Rahu,is_retrograde}'),"
                  " sampling_method = %s", (V3,))
        c.commit()


def _digest_conjunct(text: str) -> str:
    """The text's own whole-table digest conjunct for bg_synthetic_cohort, as a standalone SELECT (the REAL text, not a copy)."""
    start = text.index("AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(\n    jsonb_build_array(\n      synthetic_id,birth_datetime_utc")
    end = text.index("FROM bg_synthetic_cohort)", start) + len("FROM bg_synthetic_cohort)")
    return "SELECT " + text[start + len("AND "):end]


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _conj(connect, text: str) -> bool:
    return _q(connect, _digest_conjunct(text))[0][0]


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1327.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _txt(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_cohort'")[0][0]


def test_live_digest_conjunct_reproduces_the_production_pin_on_todays_rows(db, stored_lines):
    _setup(db)
    _load_cohort(db, stored_lines)
    assert _q(db, "SELECT count(*), min(synthetic_id), max(synthetic_id) FROM bg_synthetic_cohort") == [(10000, 1, 10000)]
    assert _conj(db, OLD_TEXT) is True, "the OLD pin must hold on the stored rows (method proof in PostgreSQL)"
    assert _conj(db, NEW_TEXT) is False, "accepted window: before the rebuild the NEW pin reads false on today's rows"


def test_live_post_rebuild_content_passes_new_and_fails_old(db, stored_lines):
    _setup(db)
    _load_cohort(db, stored_lines)
    _apply_rebuild_content(db)
    assert _q(db, "SELECT count(*) FILTER (WHERE positions#>>'{Ketu,is_retrograde}'='true') FROM bg_synthetic_cohort") == [(7475,)]
    assert _conj(db, NEW_TEXT) is True
    assert _conj(db, OLD_TEXT) is False, "the defect: the 626 pin would fail the rebuild"


def test_live_a_partial_rebuild_does_not_pass_new(db, stored_lines):
    _setup(db)
    _load_cohort(db, stored_lines)
    with db() as c:
        c.execute("UPDATE bg_synthetic_cohort SET sampling_method = %s", (V3,))
        c.commit()
    assert _conj(db, NEW_TEXT) is False, "method v3 without the Ketu flips is not the rebuild's content"
    with db() as c:
        c.execute("UPDATE bg_synthetic_cohort SET sampling_method = %s", (V2,))
        c.execute("UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Ketu,is_retrograde}', positions#>'{Rahu,is_retrograde}')")
        c.commit()
    assert _conj(db, NEW_TEXT) is False, "the Ketu flips without the v3 label is not the rebuild's content"


def test_live_digest_is_content_only_run_identity_columns_do_not_move_it(db, stored_lines):
    _setup(db)
    _load_cohort(db, stored_lines)
    _apply_rebuild_content(db)
    assert _conj(db, NEW_TEXT) is True
    with db() as c:  # what a second rebuild writes: new build_id, new computed_at; ids/surrogates differ
        c.execute("UPDATE bg_synthetic_cohort SET build_id = gen_random_uuid(), computed_at = now(), id = id + 100000")
        c.commit()
    assert _conj(db, NEW_TEXT) is True, "a rebuild that reproduces the same content must pass without a re-pin"
    # but any content mutation bites
    for name, sql in {
        "lat": "UPDATE bg_synthetic_cohort SET birth_lat = birth_lat + 0.0001 WHERE synthetic_id = 77",
        "moon_longitude": "UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Moon,sidereal_longitude}', '1.5') WHERE synthetic_id = 5",
        "rahu_flag": "UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Rahu,is_retrograde}', "
                     "to_jsonb(NOT (positions#>>'{Rahu,is_retrograde}')::boolean)) WHERE synthetic_id = 9",
        "source_citation": "UPDATE bg_synthetic_cohort SET source_citation = source_citation || '.' WHERE synthetic_id = 10000",
        "row_deleted": "DELETE FROM bg_synthetic_cohort WHERE synthetic_id = 4242",
    }.items():
        with db() as c:
            c.execute("SAVEPOINT m")
            c.execute(sql)
            assert c.execute(_digest_conjunct(NEW_TEXT)).fetchone()[0] is False, f"mutant {name} was not caught"
            c.execute("ROLLBACK TO SAVEPOINT m")
            assert c.execute(_digest_conjunct(NEW_TEXT)).fetchone()[0] is True, f"fixture not restored after {name}"


def test_live_apply_installs_the_new_text_and_the_installed_text_judges_like_the_file(db, stored_lines):
    _setup(db)
    _load_cohort(db, stored_lines)
    _apply_rebuild_content(db)
    assert _conj(db, _txt(db)) is False
    _apply(db)
    assert _md5(_txt(db)) == NEW_MD5 and len(_txt(db)) == TEXT_LEN and _txt(db) == NEW_TEXT
    assert _conj(db, _txt(db)) is True


def test_live_apply_touches_only_integrity_check_sql_and_stales_only_bg_cohort(db):
    _setup(db)
    before = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_other'")[0][0] == "SELECT true"
    fr = {a: (s, r) for a, s, r in _q(db, "SELECT asset_id, freshness_state, reasons::text FROM asset_freshness")}
    assert fr["bg_cohort"][0] == "stale" and "registry_changed" in fr["bg_cohort"][1]
    assert fr["bg_other"] == ("fresh", "[]")


def test_live_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _setup(db)
    _apply(db)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_cohort'")
    with db() as c:
        c.execute("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]' WHERE asset_id='bg_cohort'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_cohort'") == x1
    assert any("already carries the post-#3215 content digest pin" in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness WHERE asset_id='bg_cohort'")} == {"fresh"}


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = OLD_TEXT + "\n-- edited by hand\n"
    _setup(db, text=foreign)
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n and _md5(foreign) in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness")} == {"fresh"}


def test_live_null_text_is_a_noop_not_a_failure(db):
    _setup(db)
    with db() as c:
        c.execute("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='bg_cohort'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) is None and any("NO-OP" in n for n in notes)


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no bg_cohort registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bg_cohort' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _txt(db) == OLD_TEXT
