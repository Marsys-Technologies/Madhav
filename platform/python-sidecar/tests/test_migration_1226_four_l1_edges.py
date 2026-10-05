"""
Migration 1226 (four pre-S-L1 L1 `asset_registry.depends_on` edges: ga_dashas/ga_yoga/ga_vargas/ga_sensitive).
The 1224 (chart_grants) tests live in test_migration_1224_chart_grants.py; the two L2 edges are 1253's.

Two tiers:
  * STATIC (always runs, DB-free): file shape, the four edges, seed parity, header ordering rule.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration files to a
    DISPOSABLE cluster this module creates with initdb in a temp dir (own port, trust auth, removed at
    session end). It never connects to anything else. Skipped, loudly, when no `initdb`/`pg_ctl` is
    found (looked up via $PG_BIN, PATH, homebrew, /usr/lib/postgresql/*/bin). Set $PG_BIN to pin a
    version (production is PostgreSQL 15).

What the LIVE tier proves for 1226: the four edges land (existing order preserved, appended in dep order);
no other column and no other row changes; a second run rewrites nothing (xmin unchanged); a direct or an
indirect cycle RAISES and rolls back; a missing / inactive / partial asset set RAISES; an empty registry
is a no-op; a NULL depends_on is treated as empty.
It does NOT prove production state (that is read from production structure after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1226 = _REPO / "platform" / "migrations" / "1226_asset_registry_four_pre_s_l1_edges.sql"
_SEED = _REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"

FOUR_EDGES = [
    ("ga_dashas", "ga_vargas"),
    ("ga_yoga", "ga_vargas"),
    ("ga_vargas", "ga_sensitive"),
    ("ga_dashas", "ga_sensitive"),
]
CONSUMERS = ["ga_dashas", "ga_yoga", "ga_vargas"]
# L2 assets present in the fixture only to prove 1226 neither edits nor stales them (their edges are 1253's)
L2_UNTOUCHED = ["bo_laksana", "bo_upaya", "bo_bimba"]

# Live production `depends_on` (read 2026-10-02 via suvarna_reader) for the assets involved + the one
# neighbour (ga_structural) that closes the ga_yoga -> ga_structural -> {ga_dashas, ga_vargas} paths.
LIVE_BEFORE: dict[str, list[str]] = {
    "bo_laksana": ["bg_rules", "ga_positions", "ga_strength", "ga_sensitive", "ga_panchanga", "ga_sade_sati",
                   "ga_structural", "ga_nakshatra", "ga_condition", "ga_vargas", "ga_vichara"],
    "bo_upaya": ["bo_laksana", "bo_sangati", "ga_structural", "ga_dashas", "bo_cgm_motifs"],
    "ga_dashas": ["ga_positions"],
    "ga_yoga": ["ga_structural", "ga_dashas"],
    "ga_vargas": ["ga_positions"],
    "ga_sensitive": ["ga_positions", "bg_reference"],
    "bo_bimba": ["bo_laksana", "bo_sudarshana", "bo_nakshatra_semantic", "bo_arudha", "bo_special_lagna",
                 "bo_vargottama_dhana"],
    "ga_structural": ["ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions", "ga_sensitive",
                      "ga_strength", "ga_vargas"],
    "ga_positions": [],
}
EXPECTED_AFTER: dict[str, list[str]] = {
    "ga_dashas": ["ga_positions", "ga_sensitive", "ga_vargas"],
    "ga_yoga": ["ga_structural", "ga_dashas", "ga_vargas"],
    "ga_vargas": ["ga_positions", "ga_sensitive"],
}


# ── STATIC tier ──────────────────────────────────────────────────────────────

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _migration_edges() -> list[tuple[str, str]]:
    sql = _M1226.read_text()
    m = re.search(r"INSERT INTO _m1226_edges \(asset_id, dep\) VALUES\s*(.*?);", sql, re.S)
    assert m, "edge VALUES block not found in migration 1226"
    return re.findall(r"\(\s*'([a-z0-9_]+)'\s*,\s*'([a-z0-9_]+)'\s*\)", m.group(1))


def _seed_graph() -> dict[str, list[str]]:
    src = _SEED.read_text()
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"asset_id:\s*'([a-z0-9_]+)'", src):
        nxt = re.search(r"asset_id:\s*'", src[m.end():])
        block = src[m.end(): m.end() + nxt.start()] if nxt else src[m.end():]
        d = re.search(r"^[ \t]+depends_on:\s*\[(.*?)\]", block, re.S | re.M)
        if d:
            out[m.group(1)] = re.findall(r"'([a-z0-9_]+)'", d.group(1))
    return out


def test_1226_is_exactly_the_four_l1_edges():
    edges = _migration_edges()
    assert sorted(edges) == sorted(FOUR_EDGES)
    # the two L2 edges are migration 1253's, never here
    assert not [e for e in edges if e[0].startswith("bo_") or e[1].startswith("bo_")]
    assert len(set(edges)) == 4 and not any(a == b for a, b in edges)


def test_migration_does_not_own_the_transaction_and_has_no_destructive_sql():
    code = _code(_M1226)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert "SET LOCAL lock_timeout = '5s';" in code
    # statement-start match
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|ALTER)\b", code, re.I | re.M)


def test_1226_writes_only_depends_on_and_discloses_ordering_and_consequences():
    sql = _M1226.read_text()
    code = _code(_M1226)
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code, re.I) == ["depends_on"]
    # lock_timeout is the FIRST executable statement, and the header says why
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';"), code.strip()[:80]
    assert "a blocked migrate job must fail fast, not hang a shared deploy" in sql
    for needle in ("ORDERING RULE", "BEFORE S-L1", "NO DATA ROW CHANGES", "compute_upstream_hash",
                   "plan_adaptation_required", "assertManifestMatchesRegistryIdentity", "Trap 103",
                   "PRODUCTION STRUCTURE", "WITH RECURSIVE", "planned/running/paused",
                   "nirmana_registry_receipt_invalidation", "asset_freshness",
                   "APPLY TIMING RULE", "MERGE = APPLY", "S-L1 window", "MIGRATION_1226_EDGES_INTENT_v1_0.md",
                   "No other run may be dispatching or running", "migration 1253", "THREE assets",
                   "exactly those three", "37 min"):
        assert needle in sql, f"1226 header/body no longer states: {needle}"


def test_seed_carries_the_four_edges_only_and_graph_stays_acyclic():
    seed = _seed_graph()
    for a, d in FOUR_EDGES:
        assert d in seed[a], f"seed {a} lacks {d}"
    # migration 1253's two L2 edges ride in the same seed (its own migration and test); 1226 neither adds nor needs them
    assert "ga_yoga" in seed["bo_laksana"] and "bo_bimba" in seed["bo_upaya"]
    # the seed's own acyclicity (iterative DFS)
    colour: dict[str, int] = {}
    for root in seed:
        if colour.get(root):
            continue
        stack = [(root, iter(seed.get(root, [])))]
        colour[root] = 1
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if nxt not in seed:
                    continue
                c = colour.get(nxt, 0)
                assert c != 1, f"cycle through {nxt}"
                if c == 0:
                    colour[nxt] = 1
                    stack.append((nxt, iter(seed[nxt])))
                    break
            else:
                colour[node] = 2
                stack.pop()


# ── LIVE tier: disposable PostgreSQL ─────────────────────────────────────────

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


@pytest.fixture(scope="session")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1226pg"))
    data = root / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={root} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    """A fresh database per test; yields a connect() factory (autocommit off)."""
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, path: Path):
    """Run a migration file the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
    try:
        conn.execute(path.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(connect, sql: str, params=None):
    with connect() as c:
        c.execute(sql, params)


def _q(connect, sql: str, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _make_registry(connect, rows: dict[str, list[str] | None] | None = None, inactive: tuple[str, ...] = ()):
    """asset_registry fixture mirroring the live columns that matter + extra scalar columns that must stay untouched."""
    rows = LIVE_BEFORE if rows is None else rows
    with connect() as c:
        c.execute("""
            CREATE TABLE asset_registry (
                asset_id text PRIMARY KEY,
                layer text NOT NULL,
                depends_on text[],
                is_active boolean NOT NULL DEFAULT true,
                sort_order integer NOT NULL,
                target_floor integer,
                english_name text,
                meta jsonb NOT NULL DEFAULT '{}'::jsonb,
                updated_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z'
            )""")
        for i, (aid, deps) in enumerate(rows.items()):
            c.execute(
                "INSERT INTO asset_registry (asset_id, layer, depends_on, is_active, sort_order, target_floor, "
                "english_name, meta) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",
                (aid, aid.split("_")[0], deps, aid not in inactive, i, 100 + i, aid.upper(), '{"k": %d}' % i))
        c.commit()


def _deps(connect, aid: str):
    return _q(connect, "SELECT depends_on FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _snapshot_without_deps(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r) - 'depends_on' FROM asset_registry r ORDER BY asset_id")


def test_1226_applies_the_four_edges_in_order_and_touches_nothing_else(db):
    _make_registry(db)
    before_other = _snapshot_without_deps(db)
    untouched_before = {a: _deps(db, a) for a in LIVE_BEFORE if a not in CONSUMERS}
    _apply(db, _M1226)
    for aid, want in EXPECTED_AFTER.items():
        assert _deps(db, aid) == want, aid
    for a, d in FOUR_EDGES:
        assert d in _deps(db, a)
    assert _snapshot_without_deps(db) == before_other, "a non-depends_on column changed"
    assert {a: _deps(db, a) for a in untouched_before} == untouched_before, "a non-consumer row changed"


def test_1226_is_idempotent_and_rewrites_nothing_on_second_run(db):
    _make_registry(db)
    _apply(db, _M1226)
    after_first = _q(db, "SELECT asset_id, depends_on, xmin::text FROM asset_registry ORDER BY asset_id")
    _apply(db, _M1226)
    after_second = _q(db, "SELECT asset_id, depends_on, xmin::text FROM asset_registry ORDER BY asset_id")
    assert after_second == after_first, "second run changed a row (depends_on or xmin)"
    for aid, want in EXPECTED_AFTER.items():
        assert _deps(db, aid) == want and len(set(want)) == len(want), aid


def test_1226_only_appends_missing_edges_when_some_are_already_present(db):
    rows = {k: list(v) for k, v in LIVE_BEFORE.items()}
    rows["ga_dashas"] = ["ga_positions", "ga_vargas"]  # edge 1 pre-declared
    rows["ga_yoga"] = rows["ga_yoga"] + ["ga_vargas"]  # edge 2 pre-declared (fully covered row)
    _make_registry(db, rows)
    yoga_xmin = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_yoga'")
    _apply(db, _M1226)
    assert _deps(db, "ga_dashas") == ["ga_positions", "ga_vargas", "ga_sensitive"]
    assert _deps(db, "ga_yoga") == rows["ga_yoga"]
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_yoga'") == yoga_xmin


def test_1226_needs_no_l2_asset_and_never_touches_one(db):
    l1_only = {k: list(v) for k, v in LIVE_BEFORE.items() if k not in L2_UNTOUCHED}
    _make_registry(db, l1_only)
    _apply(db, _M1226)  # must not require bo_* rows (their edges are 1253's)
    for aid, want in EXPECTED_AFTER.items():
        assert _deps(db, aid) == want


def test_1226_treats_null_depends_on_as_empty(db):
    rows = {k: list(v) for k, v in LIVE_BEFORE.items()}
    rows["ga_vargas"] = None  # type: ignore[assignment]
    _make_registry(db, rows)
    _apply(db, _M1226)
    assert _deps(db, "ga_vargas") == ["ga_sensitive"]


@pytest.mark.parametrize("reverse_edge,culprit", [
    (("ga_sensitive", "ga_vargas"), "ga_vargas"),    # direct reverse of edge 3
    (("ga_vargas", "ga_dashas"), "ga_dashas"),       # reverse of edge 1 (ga_dashas -> ga_vargas -> ga_dashas)
    (("ga_sensitive", "ga_dashas"), "ga_dashas"),    # reverse of edge 4
    (("ga_structural", "ga_yoga"), "ga_yoga"),       # the known BACK-READ (ga_yoga -> ga_structural -> ga_yoga)
])
def test_1226_refuses_when_a_cycle_would_result_and_rolls_back(db, reverse_edge, culprit):
    rows = {k: list(v) for k, v in LIVE_BEFORE.items()}
    rows[reverse_edge[0]] = rows[reverse_edge[0]] + [reverse_edge[1]]
    _make_registry(db, rows)
    before = _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1226)
    msg = str(ei.value)
    assert "1226" in msg and "cycle" in msg and culprit in msg, msg
    assert _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id") == before


def test_1226_refuses_an_indirect_cycle_created_by_the_new_edges(db):
    """ga_vargas -> ga_sensitive (edge 3, new) -> zz_mid (sabotage) -> ga_vargas: a 3-node cycle that exists
    only once the migration's own edge is added, through an intermediate asset."""
    rows = {k: list(v) for k, v in LIVE_BEFORE.items()}
    rows["zz_mid"] = ["ga_vargas"]
    rows["ga_sensitive"] = rows["ga_sensitive"] + ["zz_mid"]
    _make_registry(db, rows)
    before = _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1226)
    assert "cycle" in str(ei.value) and "ga_vargas" in str(ei.value), str(ei.value)
    assert _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id") == before


def test_1226_ignores_a_preexisting_cycle_that_does_not_pass_through_an_edited_asset(db):
    rows = {k: list(v) for k, v in LIVE_BEFORE.items()}
    rows["zz_a"] = ["zz_b"]
    rows["zz_b"] = ["zz_a"]
    _make_registry(db, rows)
    _apply(db, _M1226)  # must not raise
    for aid, want in EXPECTED_AFTER.items():
        assert _deps(db, aid) == want


@pytest.mark.parametrize("missing", ["ga_sensitive", "ga_yoga", "ga_dashas", "ga_vargas"])
def test_1226_refuses_when_an_involved_asset_is_missing(db, missing):
    rows = {k: list(v) for k, v in LIVE_BEFORE.items() if k != missing}
    _make_registry(db, rows)
    before = _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1226)
    assert "1226" in str(ei.value) and "missing" in str(ei.value) and missing in str(ei.value), str(ei.value)
    assert _q(db, "SELECT asset_id, depends_on FROM asset_registry ORDER BY asset_id") == before


def test_1226_refuses_an_inactive_producer(db):
    _make_registry(db, inactive=("ga_sensitive",))
    with pytest.raises(Exception) as ei:
        _apply(db, _M1226)
    assert "inactive" in str(ei.value) and "ga_sensitive" in str(ei.value), str(ei.value)


def test_1226_is_a_noop_on_an_empty_registry(db):
    _make_registry(db, {"unrelated_asset": ["ga_positions"]})
    before = _q(db, "SELECT * FROM asset_registry")
    _apply(db, _M1226)
    assert _q(db, "SELECT * FROM asset_registry") == before


_TRIGGER_DDL = """
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, is_active ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""


def test_1226_registry_trigger_marks_exactly_the_three_edited_assets_stale_once(db):
    """Verifies the header's CONSEQUENCES 1 (migration 596's trigger, copied from production's function body)."""
    _make_registry(db)
    _exec(db, _TRIGGER_DDL)
    chart = "00000000-0000-4000-8000-0000000000ab"
    with db() as c:
        for a in LIVE_BEFORE:
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s,%s,'fresh')",
                      (a, chart))
        c.commit()
    _apply(db, _M1226)
    rows = dict(_q(db, "SELECT asset_id, freshness_state FROM asset_freshness"))
    assert {a for a, st in rows.items() if st == "stale"} == {"ga_vargas", "ga_dashas", "ga_yoga"}
    assert all(rows[a] == "fresh" for a in LIVE_BEFORE if a not in CONSUMERS)
    # the producer and the L2 assets (1253's) are NOT staled by 1226
    assert all(rows[a] == "fresh" for a in ["ga_sensitive", *L2_UNTOUCHED])
    reasons = _q(db, "SELECT reasons::text FROM asset_freshness WHERE asset_id='ga_vargas'")[0][0]
    assert "registry_changed" in reasons
    snap = _q(db, "SELECT asset_id, freshness_state, reasons::text, observed_at FROM asset_freshness ORDER BY 1")
    _apply(db, _M1226)  # idempotent: the trigger must not fire again
    assert _q(db, "SELECT asset_id, freshness_state, reasons::text, observed_at FROM asset_freshness ORDER BY 1") == snap


def test_1226_cycle_guard_has_teeth_it_is_the_guard_not_the_fixture(db):
    """Same fixture, no sabotage -> passes; with the reverse edge -> fails. Proves the RAISE comes from Guard 3."""
    _make_registry(db)
    _apply(db, _M1226)
    _exec(db, "UPDATE asset_registry SET depends_on = depends_on || 'ga_vargas'::text WHERE asset_id='ga_sensitive'")
    # The migration is idempotent on edges, so a second apply on the now-cyclic graph must still refuse.
    with pytest.raises(Exception) as ei:
        _apply(db, _M1226)
    assert "cycle" in str(ei.value)
