"""_formgap_support.py: the shared fixtures of the FORM-GAP tests (SS N-191 / N-192, 2026-10-07): the real DDL of the migrations on a DISPOSABLE PostgreSQL, a measure() stand-in that runs the engine's own
`_measure_prose` (catalog read, writer scope, closure SQL, form reads, `prose_checks`) on it, and the two-chart helper. Offline apart from the throw-away loopback cluster (deleted at exit)."""
from __future__ import annotations

import copy
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import point_psql_at  # noqa: E402

REPO = HERE.parents[3]
MIG = REPO / "platform" / "migrations"
SMIG = REPO / "platform" / "supabase" / "migrations"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"          # the measured (canonical) chart
CHART_B = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"          # another chart (never the dead phantom)
RUN_1 = "11111111-1111-4111-8111-111111111111"
RUN_2 = "22222222-2222-4222-8222-222222222222"
NA, FAIL, NO_DET, PARTIAL, PASS = ac.NA, ac.FAIL, ac.NO_DET, ac.PARTIAL, ac.PASS
CELLS = ac.NARR_CHECKS + ac.NULL_CHECKS
EV = "platform/scripts/governance/asset_census.py:1"
WHY = "the reviewed reason this declaration is true"


def psql(pg, sql=None, path=None):
    args = [str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-v", "ON_ERROR_STOP=1"] + (["-f", str(path)] if path is not None else ["-c", sql])
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    assert p.returncode == 0, (path or sql, p.stderr.strip()[:400])
    return p.stdout


def create_table_ddl(path, table):
    """The CREATE TABLE statement of `table` in a migration file (balanced parentheses, comments dropped): those files also INSERT registry rows / create triggers this database does not have."""
    txt = re.sub(r"--[^\n]*", "", pathlib.Path(path).read_text(encoding="utf-8"))
    i = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?" + re.escape(table) + r"\s*\(", txt).start()
    j, depth = txt.index("(", i), 0
    for k in range(j, len(txt)):
        depth += (txt[k] == "(") - (txt[k] == ")")
        if depth == 0:
            return txt[i: k + 1] + ";"
    raise AssertionError(f"unbalanced CREATE TABLE {table}")


def install_run_tables(pg):
    """The REAL build_runs / build_run_assets (supabase migration 171) and asset_provenance_receipts (596) DDL, with the two parents they reference stubbed (charts, asset_registry)."""
    for t in ("asset_provenance_receipts", "build_run_assets", "build_runs", "charts", "asset_registry"):
        psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    psql(pg, "CREATE TABLE charts (id uuid PRIMARY KEY)")
    psql(pg, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY)")
    psql(pg, create_table_ddl(SMIG / "171_build_runs.sql", "build_runs"))
    psql(pg, create_table_ddl(SMIG / "171_build_runs.sql", "build_run_assets"))
    psql(pg, create_table_ddl(SMIG / "596_nirmana_provenance_receipts.sql", "asset_provenance_receipts"))
    for c in (CHART_A, CHART_B):
        psql(pg, f"INSERT INTO charts VALUES ('{c}')")


def add_run(pg, run_id, asset_id, chart_id=CHART_A, state="complete", receipt=False):
    psql(pg, f"INSERT INTO build_runs (id, chart_id, scope, action, plan, triggered_by) VALUES ('{run_id}', '{chart_id}', 'asset', 'build', '[]'::jsonb, 'test') ON CONFLICT DO NOTHING")
    psql(pg, f"INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ('{run_id}', '{asset_id}', 1, '{state}') ON CONFLICT DO NOTHING")
    if receipt:
        psql(pg, f"INSERT INTO asset_registry VALUES ('{asset_id}') ON CONFLICT DO NOTHING")
        psql(pg, f"INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id) VALUES ('{asset_id}', NULL, 'p', 'v1', 'proven', '{run_id}')")


def drop_tables(pg, *tables):
    for t in tables:
        psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def decl_with(prose_none, **kw):
    d = {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": dict(why=WHY, closed_columns=[], **prose_none)}
    d.update(kw)
    return d


def measure(aid, db, monkeypatch, files, target, tables, decl, scope=None, registry=None):
    """What `measure()` does for one prose-declared asset: the catalog of the produced tables, the writer scope, the closure SQL and the FORM-GAP reads, through `_measure_prose` itself. `scope` installs the
    measured-chart read scope ({table: {where, label}}) for the duration of the call."""
    point_psql_at(db, monkeypatch)
    cat = ac.catalog(list(dict.fromkeys([target] + list(tables))))
    decls = {a: {"prose_fields": None} for a in ()}
    vocab = ac.prose_vocabulary({aid: decl}, {aid: set(tables) | {target}})
    ac.set_read_scope(scope or {})
    try:
        return ac._measure_prose(aid, decl, dict(registry or {}, target_table=target), files, cat, list(tables), {}, (), vocab)
    finally:
        ac.set_read_scope(None)


def all_na(got):
    assert sorted(got) == sorted(CELLS), sorted(got)
    bad = {c: (v["v"], v["measured"][:400]) for c, v in got.items() if v["v"] != NA}
    assert not bad, bad
    for c in CELLS:
        b = got[c]["prose_none"]
        assert b["checked"] is True and b["open"] == [] and b["contradicted"] == [] and b["unread"] == [], (c, b)
        assert ac.prose_none_na_problem(c, got[c]) is None


def verdicts(got):
    return {c: got[c]["v"] for c in CELLS}


def clone(d):
    return copy.deepcopy(d)
