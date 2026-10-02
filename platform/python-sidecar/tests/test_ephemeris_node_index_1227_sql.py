"""Migration 1227 (ephemeris_daily node-series unique index), executed against a disposable PostgreSQL.

The SQL is read from the real file platform/migrations/1227_ephemeris_daily_node_series_unique_index.sql and run in one
transaction (psql --single-transaction: the migrate.ts shape). The disposable cluster is built by tests/pg_disposable.py
(initdb into a temp dir, never the project database; skips LOUDLY when no PostgreSQL binaries exist: a skip is NOT a pass,
and the PR must say it was run locally on PG 15 and 17).

What is proved (live catalog read 2026-10-02 as suvarna_reader; the table DDL below is a copy of it):
  * the new key (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT can be built on the live DDL, ACCEPTS today's data
    shape (TRUE Rahu/Ketu rows + NULL-mode rows), REJECTS a second row for the same key including the NULL-mode case, and
    ALLOWS a 'mean' row beside a 'true' row once the old three-column key is gone (migration 1250); until then the old key
    still refuses it;
  * ON CONFLICT (date, body, ayanamsha_id, node_mode) infers the index, NULL-mode rows included; the old target stops
    working when the old key is dropped (so no old-key writer may survive to 1250);
  * the lock is SHARE (reads proceed, writes wait);
  * the amjis_app topology (owner of the table, USAGE only on schema public): neither CREATE INDEX nor ADD CONSTRAINT UNIQUE
    works, so the file refuses (fail closed) when the index is absent and only VERIFIES when the owner path created it;
  * every guard refuses its unexpected state; the file is idempotent and changes no data.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import warnings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, q, pg, requires_pg  # noqa: E402,F401

if not HAVE_PG:
    warnings.warn(
        f"{pathlib.Path(__file__).name}: DB-backed migration tests are SKIPPED, not passed. Reason: {PG_SKIP_REASON}. "
        "PR rule: say 'run locally on PG 15 and 17' and do not claim CI ran them.", UserWarning, stacklevel=1)

REPO = pathlib.Path(__file__).resolve().parents[3]
FILE = "1227_ephemeris_daily_node_series_unique_index.sql"
SQL = (REPO / "platform/migrations" / FILE).read_text(encoding="utf-8")
IDX = "ephemeris_daily_date_body_ayanamsha_node_mode_uq"
OLD_KEY = "ephemeris_daily_date_body_ayanamsha_id_key"

# the live table, copied from pg_catalog (columns, defaults, constraints, indexes) on 2026-10-02
LIVE_DDL = """
CREATE TABLE public.ephemeris_daily (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  date date NOT NULL, body text NOT NULL, ayanamsha_id text NOT NULL DEFAULT 'tropical',
  tropical_longitude numeric NOT NULL, latitude numeric NOT NULL DEFAULT 0.0, speed_dps numeric NOT NULL DEFAULT 0.0,
  is_retrograde boolean NOT NULL DEFAULT false, sign_number smallint, degree_in_sign numeric, nakshatra_number smallint,
  source_citation text NOT NULL DEFAULT 'pyswisseph DE441 + Swiss Ephemeris', computed_at timestamptz NOT NULL DEFAULT now(),
  node_mode text, epoch_convention text,
  CONSTRAINT ephemeris_daily_pkey PRIMARY KEY (id),
  CONSTRAINT ephemeris_daily_date_body_ayanamsha_id_key UNIQUE (date, body, ayanamsha_id),
  CONSTRAINT ephemeris_daily_node_mode_check CHECK (node_mode IS NULL OR node_mode = ANY (ARRAY['true','mean']))
);
CREATE INDEX idx_ephemeris_ayanamsha ON public.ephemeris_daily (ayanamsha_id);
CREATE INDEX idx_ephemeris_body ON public.ephemeris_daily (body);
CREATE INDEX idx_ephemeris_date ON public.ephemeris_daily (date);
CREATE INDEX idx_ephemeris_date_body ON public.ephemeris_daily (date, body);
"""
BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SEED = f"""
INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode, epoch_convention)
SELECT DATE '2000-01-01' + n, b.body, (n * 1.5 + b.i)::numeric,
       CASE WHEN b.body IN ('Rahu', 'Ketu') THEN 'true' END, 'noon_ut'
FROM generate_series(0, 29) n,
     (VALUES {", ".join(f"('{b}', {i})" for i, b in enumerate(BODIES))}) b(body, i);
"""
ROLES = """
DO $r$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_schema_owner') THEN CREATE ROLE data_plane_schema_owner NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN CREATE ROLE amjis_app NOLOGIN; END IF;
END $r$;
"""
# the live topology: schema public owned by data_plane_schema_owner, amjis_app has USAGE only, amjis_app owns the table
TOPOLOGY = """
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO amjis_app;
ALTER TABLE public.ephemeris_daily OWNER TO amjis_app;
"""


def _code(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def _run(port: int, db: str, sql: str, role: str | None = None):
    """Run `sql` in ONE transaction (the migrate.ts shape), optionally as `role` (SET ROLE inside the transaction)."""
    import tempfile
    f = pathlib.Path(tempfile.mkdtemp(prefix="m1227_")) / "t.sql"
    f.write_text((f"SET ROLE {role};\n" if role else "") + sql, encoding="utf-8")
    return psql(port, db, file=f, single_transaction=True)


def _err(r) -> str:
    return (r.stderr or "") + (r.stdout or "")


def _fresh(port: int, *, seed: bool = True, topology: bool = False) -> str:
    db = new_db(port)
    q(port, db, ROLES)
    q(port, db, LIVE_DDL)
    if seed:
        q(port, db, SEED)
    if topology:
        q(port, db, TOPOLOGY)
    return db


def _insert(port, db, date, body, mode, role=None):
    mode_sql = "NULL" if mode is None else f"'{mode}'"
    return _run(port, db, f"INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) "
                          f"VALUES ('{date}', '{body}', 1, {mode_sql});", role)


def _drop_old_key(port, db):
    q(port, db, f"ALTER TABLE public.ephemeris_daily DROP CONSTRAINT {OLD_KEY}")


# ── static ───────────────────────────────────────────────────────────────────────────────────────

def test_file_is_the_only_1227_and_has_the_required_shape():
    assert sorted(p.name for p in (REPO / "platform/migrations").glob("1227_*")) == [FILE]
    assert not list((REPO / "platform/supabase/migrations").glob("1227_*"))
    code = [ln.strip() for ln in _code(SQL).splitlines() if ln.strip()]
    assert code[0] == "SET LOCAL lock_timeout = '5s';"                      # first statement, fails fast
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", SQL, re.M | re.I)       # migrate.ts owns the transaction
    assert not re.search(r"\bCONCURRENTLY\b", _code(SQL), re.I)              # impossible inside the migrate transaction
    flat = re.sub(r"\s*\n--\s*", " ", SQL)
    for needle in ("ORDERING RULE", "PRECEDES the series write", "NO DATA CHANGE", "STAYS until migration 1250",
                   "VERIFIED BY PRODUCTION STRUCTURE", "merge = apply", "CANNOT CREATE THE INDEX", "DO NOT MERGE before the D6 step",
                   "fail closed", "SHARE on the table", "Trap 103"):
        assert needle in flat, needle
    # nothing but the one index is ever touched
    c = _code(SQL)
    assert not re.search(r"\b(UPDATE|DELETE|INSERT|ALTER|DROP|TRUNCATE)\b", c, re.I)
    assert c.count("CREATE UNIQUE INDEX") == 1


# ── executed: the index itself ───────────────────────────────────────────────────────────────────

@requires_pg
def test_builds_on_the_live_ddl_accepts_todays_data_and_changes_nothing_else(pg):
    db = _fresh(pg)
    before = q(pg, db, "SELECT count(*), md5(string_agg(id::text || tropical_longitude::text, ',' ORDER BY id)) FROM public.ephemeris_daily")
    r = _run(pg, db, SQL)
    assert r.returncode == 0, _err(r)
    row = q(pg, db, f"SELECT i.indisunique, i.indisvalid, i.indisready, i.indnullsnotdistinct, am.amname, pg_get_indexdef(i.indexrelid) "
                    f"FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid JOIN pg_am am ON am.oid = c.relam WHERE c.relname = '{IDX}'")
    assert row.startswith("t|t|t|t|btree|CREATE UNIQUE INDEX " + IDX)
    assert "(date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT" in row
    assert q(pg, db, "SELECT count(*), md5(string_agg(id::text || tropical_longitude::text, ',' ORDER BY id)) FROM public.ephemeris_daily") == before
    # the old three-column key STAYS
    assert q(pg, db, f"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = '{OLD_KEY}'") == "UNIQUE (date, body, ayanamsha_id)"
    assert q(pg, db, "SELECT count(*) FROM pg_indexes WHERE tablename = 'ephemeris_daily'") == "7"   # 6 live + the new one


@requires_pg
def test_idempotent_second_run_is_a_noop(pg):
    db = _fresh(pg)
    assert _run(pg, db, SQL).returncode == 0
    oid = q(pg, db, f"SELECT '{IDX}'::regclass::oid")
    assert _run(pg, db, SQL).returncode == 0
    assert q(pg, db, f"SELECT '{IDX}'::regclass::oid") == oid                        # not rebuilt
    assert q(pg, db, "SELECT count(*) FROM pg_indexes WHERE tablename = 'ephemeris_daily'") == "7"


@requires_pg
def test_before_1250_the_old_key_still_refuses_a_mean_row_and_the_new_index_refuses_exact_duplicates(pg):
    db = _fresh(pg)
    assert _run(pg, db, SQL).returncode == 0
    r = _insert(pg, db, "2000-01-05", "Rahu", "mean")                                 # mean beside true: old key still refuses
    assert r.returncode != 0 and OLD_KEY in _err(r)
    r = _insert(pg, db, "2000-01-05", "Rahu", "true")                                 # same key incl. node_mode
    assert r.returncode != 0 and "duplicate key" in _err(r)
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily") == str(len(BODIES) * 30)


@requires_pg
def test_after_the_old_key_is_dropped_new_index_rejects_dups_incl_null_and_allows_mean_beside_true(pg):
    db = _fresh(pg)
    assert _run(pg, db, SQL).returncode == 0
    _drop_old_key(pg, db)                                                             # what migration 1250 does
    # accepts: a MEAN Rahu/Ketu row beside the TRUE one, for the same (date, body, ayanamsha_id)
    for body in ("Rahu", "Ketu"):
        assert _insert(pg, db, "2000-01-05", body, "mean").returncode == 0
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily WHERE date = '2000-01-05' AND body IN ('Rahu','Ketu')") == "4"
    # rejects: a second row for the same (date, body, ayanamsha_id, node_mode), 'true', 'mean' and NULL alike
    for body, mode in (("Rahu", "true"), ("Rahu", "mean"), ("Ketu", "mean"), ("Sun", None), ("Saturn", None)):
        r = _insert(pg, db, "2000-01-05", body, mode)
        assert r.returncode != 0 and IDX in _err(r), (body, mode, _err(r))
    # a different date is fine; the 7 non-node bodies still carry one NULL-mode row per date
    assert _insert(pg, db, "2000-02-15", "Sun", None).returncode == 0
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily WHERE date = '2000-01-05'") == "11"


@requires_pg
def test_a_plain_four_column_unique_would_not_dedupe_the_null_rows_which_is_why_nulls_not_distinct(pg):
    db = _fresh(pg)
    _drop_old_key(pg, db)
    q(pg, db, "CREATE UNIQUE INDEX plain_four ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode)")
    assert _insert(pg, db, "2000-01-05", "Sun", None).returncode == 0                # duplicate NULL-mode Sun slips through
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily WHERE date = '2000-01-05' AND body = 'Sun'") == "2"
    q(pg, db, "DELETE FROM public.ephemeris_daily WHERE ctid = (SELECT ctid FROM public.ephemeris_daily WHERE date = '2000-01-05' AND body = 'Sun' LIMIT 1)")
    q(pg, db, "DROP INDEX plain_four")
    assert _run(pg, db, SQL).returncode == 0                                          # the real index closes the hole
    assert _insert(pg, db, "2000-01-05", "Sun", None).returncode != 0


UPSERT = ("INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2000-01-05', '{b}', 99, {m}) "
          "ON CONFLICT {t} DO UPDATE SET tropical_longitude = EXCLUDED.tropical_longitude;")


@requires_pg
def test_on_conflict_inference_four_column_target_incl_null_mode_and_the_old_target_after_1250(pg):
    db = _fresh(pg)
    assert _run(pg, db, SQL).returncode == 0
    four = "(date, body, ayanamsha_id, node_mode)"
    # conflicts on the NULL-mode row and on the 'true' row: both upsert in place (no duplicate, no error)
    assert _run(pg, db, UPSERT.format(b="Sun", m="NULL", t=four)).returncode == 0
    assert _run(pg, db, UPSERT.format(b="Rahu", m="'true'", t=four)).returncode == 0
    assert q(pg, db, "SELECT tropical_longitude::text FROM public.ephemeris_daily WHERE date = '2000-01-05' AND body IN ('Sun','Rahu') ORDER BY body") == "99\n99"
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily WHERE date = '2000-01-05'") == "9"
    # the old three-column target still infers the old key while it exists, and ceases to once 1250 drops it
    assert _run(pg, db, UPSERT.format(b="Sun", m="NULL", t="(date, body, ayanamsha_id)")).returncode == 0
    _drop_old_key(pg, db)
    r = _run(pg, db, UPSERT.format(b="Sun", m="NULL", t="(date, body, ayanamsha_id)"))
    assert r.returncode != 0 and "no unique or exclusion constraint matching the ON CONFLICT" in _err(r)
    # a MEAN upsert now inserts a new row for Rahu and a second one conflicts with it
    assert _run(pg, db, UPSERT.format(b="Rahu", m="'mean'", t=four)).returncode == 0
    assert _run(pg, db, UPSERT.format(b="Rahu", m="'mean'", t=four)).returncode == 0
    assert q(pg, db, "SELECT count(*) FROM public.ephemeris_daily WHERE date = '2000-01-05' AND body = 'Rahu'") == "2"


@requires_pg
def test_lock_is_share_reads_proceed_writes_wait(pg):
    """The migration's table lock is SHARE (conflicts with ROW EXCLUSIVE = writes, not with ACCESS SHARE = reads): the only
    writers of ephemeris_daily are the L0 bg_ephemeris rebuild, so a deploy-time apply waits for or fails fast on a build."""
    db = _fresh(pg)
    script = SQL + ("\nSELECT 'MODES:' || string_agg(mode, ',' ORDER BY mode) FROM pg_locks "
                    "WHERE relation = 'public.ephemeris_daily'::regclass AND pid = pg_backend_pid();\n")
    r = _run(pg, db, script)
    assert r.returncode == 0, _err(r)
    modes = re.search(r"MODES:(\S+)", r.stdout).group(1).split(",")
    assert "ShareLock" in modes
    assert not {"AccessExclusiveLock", "ExclusiveLock", "ShareRowExclusiveLock", "RowExclusiveLock"} & set(modes), modes


# ── executed: the amjis_app topology (the reason the live index is created by the D6 owner path) ──────────────

@requires_pg
def test_amjis_app_owns_the_table_but_cannot_create_an_index_or_a_unique_constraint(pg):
    db = _fresh(pg, topology=True)
    assert q(pg, db, "SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')") == "f"
    assert q(pg, db, "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname = 'ephemeris_daily'") == "amjis_app"
    for ddl in (f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT",
                f"ALTER TABLE public.ephemeris_daily ADD CONSTRAINT {IDX} UNIQUE NULLS NOT DISTINCT (date, body, ayanamsha_id, node_mode)"):
        r = _run(pg, db, ddl, role="amjis_app")
        assert r.returncode != 0 and "permission denied for schema public" in _err(r), (ddl, _err(r))


@requires_pg
def test_file_fails_closed_for_amjis_app_when_the_index_is_absent_and_verifies_when_the_owner_path_created_it(pg):
    db = _fresh(pg, topology=True)
    r = _run(pg, db, SQL, role="amjis_app")
    assert r.returncode != 0 and "no CREATE on schema public" in _err(r) and "D6 owner-path executor" in _err(r)
    assert q(pg, db, f"SELECT to_regclass('public.{IDX}') IS NULL") == "t"            # nothing was created, nothing recorded
    # the D6 owner path (a role with ownership AND CREATE) builds it; the routine runner then only verifies
    q(pg, db, f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT")
    oid = q(pg, db, f"SELECT '{IDX}'::regclass::oid")
    r = _run(pg, db, SQL, role="amjis_app")
    assert r.returncode == 0, _err(r)
    assert q(pg, db, f"SELECT '{IDX}'::regclass::oid") == oid


@requires_pg
def test_d6_owner_path_shape_membership_gives_ownership_and_schema_create_in_one_transaction(pg):
    """The executor's mechanism, proved on PG: an admin (CREATEROLE, not superuser, like the Cloud SQL postgres) holds temporary
    membership of amjis_app and data_plane_schema_owner inside ONE transaction, builds the index, and revokes: the committed
    state differs only by the new index (no membership, ACL or ownership change)."""
    db = _fresh(pg, topology=True)
    q(pg, db, "DO $r$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='d6_admin') THEN CREATE ROLE d6_admin LOGIN CREATEROLE; END IF; END $r$")
    q(pg, db, "GRANT CONNECT ON DATABASE %s TO d6_admin" % db)
    snap = ("SELECT (SELECT count(*) FROM pg_auth_members WHERE member = 'd6_admin'::regrole), "
            "(SELECT nspacl::text FROM pg_namespace WHERE nspname = 'public'), "
            "(SELECT relacl::text || relowner::regrole::text FROM pg_class WHERE relname = 'ephemeris_daily')")
    before = q(pg, db, snap)
    # every statement runs AS the CREATEROLE admin (not the superuser that started the session)
    r = _run(pg, db, f"""
SET LOCAL ROLE d6_admin;
GRANT amjis_app TO d6_admin;
GRANT data_plane_schema_owner TO d6_admin;
{SQL}
REVOKE amjis_app FROM d6_admin;
REVOKE data_plane_schema_owner FROM d6_admin;
""")
    if r.returncode != 0 and "permission denied to grant role" in _err(r):
        import pytest
        pytest.skip("PostgreSQL >= 16: a CREATEROLE-only admin cannot GRANT an arbitrary role (run as a superuser admin)")
    assert r.returncode == 0, _err(r)
    assert q(pg, db, snap) == before
    assert q(pg, db, f"SELECT indisvalid FROM pg_index WHERE indexrelid = '{IDX}'::regclass") == "t"


# ── executed: every guard refuses its unexpected state ────────────────────────────────────────────────────────

@requires_pg
def test_guard_missing_table(pg):
    db = new_db(pg)
    r = _run(pg, db, SQL)
    assert r.returncode != 0 and "does not exist" in _err(r)


@requires_pg
def test_guard_missing_or_wrong_typed_key_column(pg):
    db = new_db(pg)
    q(pg, db, "CREATE TABLE public.ephemeris_daily (id uuid PRIMARY KEY, date date NOT NULL, body text NOT NULL, ayanamsha_id text NOT NULL)")
    r = _run(pg, db, SQL)
    assert r.returncode != 0 and "lacks date date / body text / ayanamsha_id text / node_mode text" in _err(r)
    db = new_db(pg)
    q(pg, db, "CREATE TABLE public.ephemeris_daily (id uuid PRIMARY KEY, date text, body text, ayanamsha_id text, node_mode text)")
    assert "found 3 of 4" in _err(_run(pg, db, SQL))


@requires_pg
def test_guard_not_a_plain_table(pg):
    db = new_db(pg)
    q(pg, db, "CREATE TABLE public.ephemeris_daily (id uuid, date date, body text, ayanamsha_id text, node_mode text) PARTITION BY RANGE (date)")
    r = _run(pg, db, SQL)
    assert r.returncode != 0 and "not a plain table" in _err(r)


@requires_pg
def test_guard_mean_rows_already_present(pg):
    db = _fresh(pg)
    _drop_old_key(pg, db)
    q(pg, db, "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2000-01-01', 'Rahu', 1, 'mean')")
    r = _run(pg, db, SQL)
    assert r.returncode != 0 and "ordering rule" in _err(r) and "mean" in _err(r)
    assert q(pg, db, f"SELECT to_regclass('public.{IDX}') IS NULL") == "t"


@requires_pg
def test_guard_duplicates_when_the_old_key_is_absent(pg):
    db = _fresh(pg)
    _drop_old_key(pg, db)
    q(pg, db, "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2000-01-01', 'Sun', 1, NULL)")
    r = _run(pg, db, SQL)
    assert r.returncode != 0 and "duplicate (date, body, ayanamsha_id, node_mode) rows exist" in _err(r)


@requires_pg
def test_guard_a_different_object_or_a_different_index_by_that_name_refuses(pg):
    for ddl in (f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode)",                       # plain, not NNDistinct
                f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id) NULLS NOT DISTINCT",              # three columns
                f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (body, date, ayanamsha_id, node_mode) NULLS NOT DISTINCT",   # wrong order
                f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode DESC) NULLS NOT DISTINCT",
                f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT WHERE body <> 'Sun'",
                f"CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body text_pattern_ops, ayanamsha_id, node_mode) NULLS NOT DISTINCT",  # opclass
                f'CREATE UNIQUE INDEX {IDX} ON public.ephemeris_daily (date, body COLLATE "C", ayanamsha_id, node_mode) NULLS NOT DISTINCT',      # collation
                f"CREATE INDEX {IDX} ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode)",                              # non-unique
                f"CREATE TABLE public.{IDX} (x int)"):                                                                               # a table by that name
        db = _fresh(pg)
        q(pg, db, ddl)
        r = _run(pg, db, SQL)
        assert r.returncode != 0 and "not the expected unique btree" in _err(r), (ddl, _err(r))


@requires_pg
def test_verify_only_path_reads_no_data_so_a_later_mean_row_cannot_block_it(pg):
    """The index already exists (D6 step): a mean row (the series, written later) or a missing old key must not make a
    late-applied 1227 fail; only the structure is verified."""
    db = _fresh(pg)
    assert _run(pg, db, SQL).returncode == 0
    _drop_old_key(pg, db)                                                             # 1250
    assert _insert(pg, db, "2000-01-05", "Rahu", "mean").returncode == 0               # the series
    r = _run(pg, db, SQL)
    assert r.returncode == 0, _err(r)
    flat = re.sub(r"\s*\n--\s*", " ", SQL)
    for needle in ("BLAST RADIUS", "MANUAL REVERT", "DROP INDEX public." + IDX, "A from-scratch replay is out of scope"):
        assert needle in flat, needle


@requires_pg
def test_postcondition_old_key_missing_is_not_required_and_a_fresh_database_without_it_still_builds(pg):
    db = _fresh(pg)
    _drop_old_key(pg, db)
    assert _run(pg, db, SQL).returncode == 0
    assert q(pg, db, f"SELECT indnullsnotdistinct FROM pg_index WHERE indexrelid = '{IDX}'::regclass") == "t"
