"""Migration 1289: the real file, executed against a disposable local PostgreSQL built with materialized views of the
PRODUCTION SHAPE (read from pg_matviews on 2026-10-05): thirteen views owned by amjis_app, reading chart_facts /
chart_divisionals (tables owned by data_plane_l1_owner, SELECT granted to amjis_app) and, for one, another view; ten carry
a unique index (CONCURRENTLY-able), three do not (mv_cross_ayanamsha_consensus, mv_sensitive_points_cross_ayanamsha,
mv_chart_aspect_matrix: plain REFRESH only).

Proves: a stale set is fully refreshed (definition-exact EXCEPT diff = 0) with the dependent view seeing its parent's NEW
content; idempotent; no-op (NOTICE) when views are absent, whole or in part; an unpopulated view is populated by the plain
form; CONCURRENTLY is the form used where a unique index exists (an open reader on the view does not block the file); a
non-owner is refused and the whole file rolls back; lock_timeout makes a blocked file fail fast and ROLL BACK every earlier
refresh; no table row, grant, owner or index changes. Skipped loudly when no server binaries exist (tests/pg_disposable.py).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import time
import warnings

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, PSQL, new_db, psql, q, pg, requires_pg  # noqa: E402,F401

if not HAVE_PG:
    warnings.warn(f"{pathlib.Path(__file__).name}: DB-backed migration tests are SKIPPED, not passed. Reason: {PG_SKIP_REASON}.",
                  UserWarning, stacklevel=1)

REPO = pathlib.Path(__file__).resolve().parents[3]
FILE = REPO / "platform/migrations/1289_refresh_other_l1_materialized_views_after_s_l1.sql"
SQL = FILE.read_text(encoding="utf-8")

# name -> (reads, definition after "AS", unique index columns or None). Order = the migration's order.
FACTS = "chart_facts"
VIEWS: dict[str, tuple[str, str | None]] = {
    "mv_chart_planet_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'planet' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_shadbala_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'shadbala' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_ashtakavarga_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'av' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_bhava_bala_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'bhava' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_cross_ayanamsha_consensus": ("SELECT chart_id, fact_key, count(*) AS n FROM chart_facts GROUP BY 1, 2", None),
    "mv_chart_panchanga_birth_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'panchanga' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_sensitive_points_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'sensitive' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_sensitive_points_cross_ayanamsha": ("SELECT chart_id, sum(n) AS total FROM mv_chart_sensitive_points_summary GROUP BY 1", None),
    "mv_chart_vargas_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_divisionals GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_aspect_matrix": ("SELECT chart_id, count(*) AS n FROM chart_facts WHERE fact_category = 'aspect' GROUP BY 1", None),
    "mv_chart_super_vargottama_bodies": ("SELECT chart_id, build_id, count(*) AS n FROM chart_divisionals WHERE varga = 'D9' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_t1_composite_strengths": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 't1' GROUP BY 1, 2", "chart_id, build_id"),
    "mv_chart_yogas_fired_summary": ("SELECT chart_id, build_id, count(*) AS n FROM chart_facts WHERE fact_category = 'yoga' GROUP BY 1, 2", "chart_id, build_id"),
}
UNIQUE = [v for v, (_, u) in VIEWS.items() if u]
PLAIN_ONLY = [v for v, (_, u) in VIEWS.items() if not u]
CATS = ["planet", "shadbala", "av", "bhava", "panchanga", "sensitive", "aspect", "t1", "yoga"]
B1, B2 = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _roles(port: int) -> None:
    for r in ("amjis_app", "data_plane_l1_owner", "data_plane_builder"):
        psql(port, "postgres", f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{r}') THEN CREATE ROLE {r} LOGIN; END IF; END $$;")


def _tables(port: int, db: str) -> None:
    q(port, db, "CREATE TABLE chart_facts (chart_id uuid, build_id uuid, fact_category text, fact_key text, v int);"
                "CREATE TABLE chart_divisionals (chart_id uuid, build_id uuid, varga text, v int);"
                "ALTER TABLE chart_facts OWNER TO data_plane_l1_owner; ALTER TABLE chart_divisionals OWNER TO data_plane_l1_owner;"
                "GRANT SELECT ON chart_facts, chart_divisionals TO amjis_app;")


def _seed(port: int, db: str, build: str, n: int = 2) -> None:
    rows = ",".join(f"('{CHART}','{build}','{c}','k{i}',{i})" for c in CATS for i in range(n))
    q(port, db, f"INSERT INTO chart_facts VALUES {rows};")
    q(port, db, f"INSERT INTO chart_divisionals VALUES " + ",".join(f"('{CHART}','{build}','{v}',{i})" for v in ("D1", "D9") for i in range(n)) + ";")


def _create_views(port: int, db: str, names=None, populated: bool = True) -> None:
    sql = []
    for v, (defn, uniq) in VIEWS.items():
        if names is not None and v not in names:
            continue
        sql.append(f"CREATE MATERIALIZED VIEW public.{v} AS {defn} {'' if populated else 'WITH NO DATA'};")
        if uniq and populated:
            sql.append(f"CREATE UNIQUE INDEX {v}_uq ON public.{v} ({uniq});")
        elif uniq:
            sql.append(f"CREATE UNIQUE INDEX {v}_uq ON public.{v} ({uniq});")
        else:
            sql.append(f"CREATE INDEX {v}_ix ON public.{v} (chart_id);")
        sql.append(f"ALTER MATERIALIZED VIEW public.{v} OWNER TO amjis_app;")
        sql.append(f"GRANT SELECT ON public.{v} TO data_plane_builder;")
    q(port, db, "".join(sql))


@pytest.fixture()
def shaped(pg):
    """A fresh database of the production shape, views created after build B1 and then made STALE by build B2."""
    _roles(pg)
    db = new_db(pg)
    _tables(pg, db)
    _seed(pg, db, B1)
    _create_views(pg, db)
    _seed(pg, db, B2, n=3)          # the "S-L1 rebuild": new rows the views have not seen
    return pg, db


def _apply(port: int, db: str, role: str = "amjis_app", sql: str = SQL, timeout: int = 120):
    wrapper = pathlib.Path(tempfile.mkdtemp(prefix="m1289_")) / "apply.sql"
    wrapper.write_text(f"SET ROLE {role};\n{sql}", encoding="utf-8")     # migrate.ts shape: one transaction, owner role
    return psql(port, db, file=wrapper, single_transaction=True)


def _diff(port: int, db: str, view: str) -> int:
    d = "(" + q(port, db, f"SELECT rtrim(pg_get_viewdef('public.{view}'::regclass), ';')") + ")"
    return int(q(port, db, f"SELECT count(*) FROM ((TABLE public.{view} EXCEPT {d}) UNION ALL ({d} EXCEPT TABLE public.{view})) z"))


def _stale_views(port: int, db: str) -> list[str]:
    present = set(q(port, db, "SELECT matviewname FROM pg_matviews").split())
    return [v for v in VIEWS if v in present and _diff(port, db, v) != 0]


def _fingerprint(port: int, db: str) -> str:
    """Everything that is NOT view content: table data, owners, ACLs and index names (a no-DDL, no-grant, no-data witness)."""
    return q(port, db,
             "SELECT md5(string_agg(x, '|' ORDER BY x)) FROM ("
             " SELECT 'f:' || md5(t::text) AS x FROM chart_facts t UNION ALL SELECT 'd:' || md5(t::text) FROM chart_divisionals t"
             " UNION ALL SELECT 'c:' || relname || ':' || relkind::text || ':' || relowner::regrole::text || ':' || coalesce(relacl::text, '')"
             "   FROM pg_class WHERE relnamespace = 'public'::regnamespace"
             " UNION ALL SELECT 'i:' || indexname || ':' || indexdef FROM pg_indexes WHERE schemaname = 'public') s")


# ── static, always run ────────────────────────────────────────────────────────

def test_file_lists_exactly_the_thirteen_views_in_dependency_order():
    import re
    listed = re.findall(r"'(mv_[a-z_0-9]+)'", SQL.split("DO $mv$")[1])
    assert listed == list(VIEWS)
    assert "mv_chart_sade_sati_lifetime_summary" not in SQL.split("DO $mv$")[1]     # 1256's, not repeated
    assert listed.index("mv_chart_sensitive_points_summary") < listed.index("mv_sensitive_points_cross_ayanamsha")


# ── executed ─────────────────────────────────────────────────────────────────

@requires_pg
def test_the_fixture_is_really_stale_and_the_migration_refreshes_every_view_to_the_exact_definition(shaped):
    port, db = shaped
    stale = set(_stale_views(port, db))
    assert stale and "mv_chart_planet_summary" in stale and "mv_chart_vargas_summary" in stale and "mv_sensitive_points_cross_ayanamsha" not in stale
    before = _fingerprint(port, db)
    r = _apply(port, db)
    assert r.returncode == 0, r.stderr
    assert _stale_views(port, db) == []                                  # definition-exact: 0 differing rows in all thirteen
    assert _fingerprint(port, db) == before                              # no table row, owner, grant or index changed
    assert int(q(port, db, "SELECT total FROM mv_sensitive_points_cross_ayanamsha")) == 2 + 3     # the dependent saw the parent's NEW content


@requires_pg
def test_idempotent_second_run_changes_nothing(shaped):
    port, db = shaped
    assert _apply(port, db).returncode == 0
    snap = q(port, db, "SELECT string_agg(v || '=' || n::text, ',' ORDER BY v) FROM (" +
             " UNION ALL ".join(f"SELECT '{v}' AS v, count(*) AS n FROM public.{v}" for v in VIEWS) + ") s")
    fp = _fingerprint(port, db)
    assert _apply(port, db).returncode == 0
    assert q(port, db, "SELECT string_agg(v || '=' || n::text, ',' ORDER BY v) FROM (" +
             " UNION ALL ".join(f"SELECT '{v}' AS v, count(*) AS n FROM public.{v}" for v in VIEWS) + ") s") == snap
    assert _fingerprint(port, db) == fp and _stale_views(port, db) == []


@requires_pg
def test_no_op_when_every_view_is_absent(pg):
    _roles(pg)
    db = new_db(pg)
    _tables(pg, db)
    r = _apply(pg, db)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT count(*) FROM pg_matviews") == "0"          # nothing created, nothing touched
    # RAISE NOTICE goes to stderr: one per view
    assert sum(1 for v in VIEWS if f"public.{v} does not exist" in r.stderr) == len(VIEWS)


@requires_pg
def test_partial_presence_refreshes_what_exists_and_notices_the_rest(pg):
    _roles(pg)
    db = new_db(pg)
    _tables(pg, db)
    _seed(pg, db, B1)
    keep = ["mv_chart_planet_summary", "mv_chart_sensitive_points_summary", "mv_sensitive_points_cross_ayanamsha"]
    _create_views(pg, db, names=keep)
    _seed(pg, db, B2, n=3)
    r = _apply(pg, db)
    assert r.returncode == 0, r.stderr
    assert sorted(x for x in q(pg, db, "SELECT matviewname FROM pg_matviews").split()) == sorted(keep)
    assert _stale_views(pg, db) == []
    assert r.stderr.count("does not exist in this database") == len(VIEWS) - len(keep)


@requires_pg
def test_an_unpopulated_view_gets_the_plain_refresh_and_ends_populated(pg):
    _roles(pg)
    db = new_db(pg)
    _tables(pg, db)
    _seed(pg, db, B1)
    _create_views(pg, db, populated=False)
    assert q(pg, db, "SELECT count(*) FROM pg_matviews WHERE ispopulated") == "0"
    r = _apply(pg, db)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT count(*) FROM pg_matviews WHERE ispopulated") == str(len(VIEWS))
    assert _stale_views(pg, db) == []


@requires_pg
def test_concurrently_is_used_where_a_unique_index_exists_an_open_reader_does_not_block_the_file(shaped):
    port, db = shaped
    # A reader holding ACCESS SHARE on a unique-indexed view: CONCURRENTLY (EXCLUSIVE lock) is compatible, a plain REFRESH
    # (ACCESS EXCLUSIVE) would wait out the 10 s lock_timeout and fail.
    holder = subprocess.Popen([PSQL, "-X", "-q", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", db, "-c",
                               "BEGIN; SELECT count(*) FROM public.mv_chart_planet_summary; SELECT pg_sleep(25); COMMIT;"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        t0 = time.time()
        r = _apply(port, db)
        assert r.returncode == 0, r.stderr
        assert time.time() - t0 < 9.0, "the file waited on the reader: a plain REFRESH was used on a unique-indexed view"
    finally:
        holder.kill()
        holder.wait()
    assert UNIQUE and PLAIN_ONLY == ["mv_cross_ayanamsha_consensus", "mv_sensitive_points_cross_ayanamsha", "mv_chart_aspect_matrix"]


@requires_pg
def test_a_non_owner_is_refused_and_the_whole_file_rolls_back(shaped):
    port, db = shaped
    before = _stale_views(port, db)
    r = _apply(port, db, role="data_plane_builder")        # SELECT on the views, but not their owner: the real S-L1 job's role
    assert r.returncode != 0 and ("must be owner of materialized view" in r.stderr or "permission denied for materialized view" in r.stderr)   # PG15 / PG17 wording
    assert _stale_views(port, db) == before                # the first refresh attempt already failed; nothing changed


@requires_pg
def test_lock_timeout_fails_fast_and_rolls_back_every_earlier_refresh(shaped):
    port, db = shaped
    assert _stale_views(port, db)
    # Hold ACCESS EXCLUSIVE on a LATE view (LOCK TABLE is refused on materialized views; ALTER ... OWNER TO the same owner takes the lock) (mv_chart_yogas_fired_summary is last): the ten-plus earlier views refresh inside
    # the file's transaction first, then the file blocks and must roll all of them back.
    holder = subprocess.Popen([PSQL, "-X", "-q", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", db, "-c",
                               "BEGIN; ALTER MATERIALIZED VIEW public.mv_chart_yogas_fired_summary OWNER TO amjis_app; SELECT pg_sleep(40); COMMIT;"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            if q(port, db, "SELECT count(*) FROM pg_locks WHERE mode = 'AccessExclusiveLock' AND granted AND relation = 'public.mv_chart_yogas_fired_summary'::regclass") == "1":
                break
            time.sleep(0.2)
        t0 = time.time()
        r = _apply(port, db)
        elapsed = time.time() - t0
    finally:
        holder.kill()
        holder.wait()
    assert r.returncode != 0 and "lock timeout" in r.stderr, r.stderr
    assert 8.0 < elapsed < 25.0, elapsed                   # ~10 s: bounded, not a hang
    assert "mv_chart_planet_summary" in _stale_views(port, db)           # an EARLIER view was rolled back with the file
    assert set(_stale_views(port, db)) >= {"mv_chart_planet_summary", "mv_chart_vargas_summary"}
    # and a re-run once the lock is gone completes (safe to re-run)
    assert _apply(port, db).returncode == 0 and _stale_views(port, db) == []
