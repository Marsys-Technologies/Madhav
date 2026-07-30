"""
pipeline.orchestrator.dag_edge_guard
====================================

Edge-completeness guard for the build DAG.

INVARIANT: every per-chart producer TABLE a writer reads must be produced by an
asset that is in the reading asset's transitive `depends_on` closure. If a writer
reads asset X's output table but X is not (transitively) declared, the scheduler
can run the writer before X completes -> build on incomplete/missing data. The
serial build hides this via sort-order luck; the wave-parallel scheduler does not.

This automates the manual reads-vs-declared audit that produced migration 365.

HOW IT IS ACTUALLY INVOKED — read this before citing the guard as an enforcement
mechanism (SAMĀPTI B-N8-SWEEPFIX, F-02). The previous version of this docstring
said the guard runs "as a CI gate" and "catches drift the moment a writer adds an
undeclared cross-asset read". Neither was true, and downstream governance prose
repeated the claim (`BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md:82`,
`ORCHESTRATOR_WAVE_PARALLEL_SCHEDULER_v1_0.md:64`). Its only automated caller was
`tests/test_dag_edge_guard.py`'s live check, which carries
`@pytest.mark.skipif(not DATABASE_URL)`; push/PR CI provides no database, so that
test skipped on every run and no mutation to any writer could turn the guard red.
The project's own record confirms the consequence: 3 real HARD violations were
found by a HUMAN running it during an audit, not by CI.

What runs now, and what each run actually proves:
  * `--self-test` — DB-free mutation proof of the DETECTOR: a synthetic writer with
    an undeclared cross-asset read must be FLAGGED, and the same writer with the
    edge declared must come back CLEAN. Wired as a hard gate in
    `.github/workflows/ci.yml`, so a change that breaks the detection logic fails
    the PR. It proves the detector; it says NOTHING about the live DAG.
  * live scan (`python -m pipeline.orchestrator.dag_edge_guard`, exit 1 on any HARD
    violation) — needs `DATABASE_URL`. Wired into
    `.github/workflows/fresh_chart_smoke.yml` immediately after that job restores a
    production schema snapshot and applies the branch's migrations, which is the
    only automated context in this repo with a real registry to scan. That workflow
    is scheduled + `workflow_dispatch`, NOT per-commit.
  * Therefore: undeclared-read drift is caught on the fresh-chart-smoke cadence and
    by manual invocation — NOT "the moment" it is introduced. Do not describe this
    guard as a per-commit gate.
  * A scan that resolves fewer than `--min-assets` writer assets EXITS 1 rather than
    printing OK. A live scan that checked nothing is a broken scan, not a clean DAG.

Known detection bound (unchanged by the above): `_reads()` regex-matches literal
`FROM`/`JOIN <table>` in writer source. A query assembled from a variable table
name is invisible to it. The guard does not claim to cover dynamic SQL.

Two tiers:
  * HARD  — reads of a table owned by exactly ONE per_chart asset (1:1). A missing
            transitive edge is a FAILURE. Covers all cross-layer drift.
  * SOFT  — reads of `chart_facts` (a shared table written by ~8 L1 assets,
            partitioned by fact_category). Static fact_category resolution is
            imperfect, so these are reported as WARNINGS, not failures.

Globals / L0 (always-present bedrock: bg_*, reference_*, ephemeris_daily, etc.)
and external ingest tables (life_event*) are never gated.

Run as a script:  python -m pipeline.orchestrator.dag_edge_guard   (exit 1 on hard violation)
                  python -m pipeline.orchestrator.dag_edge_guard --self-test
Used by:          tests/test_dag_edge_guard.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# NOTE: `.db` (and its psycopg dependency) is imported lazily inside analyze() —
# NOT at module level. The `--self-test` path is a DB-free CI hard gate whose job
# (`governance-gates` in .github/workflows/ci.yml) installs only pyyaml + pytest;
# a module-level DB import would make that step die with ModuleNotFoundError at
# import time, before running a single check. Keep this import deferred.

# Writer source roots scanned for reads (relative to python-sidecar/).
_SIDECAR = Path(__file__).resolve().parents[2]
_WRITER_ROOTS = [
    _SIDECAR / "ga_writers",
    _SIDECAR / "bodha_writers",
    _SIDECAR / "pipeline" / "orchestrator" / "writers",
    _SIDECAR / "services",
]

# Tables that are never gated (always-present bedrock or external ingest).
_UNGATED_PREFIXES = ("bg_", "reference_", "brahma_", "sutravali_", "classical_")
_UNGATED_EXACT = {"ephemeris_daily"}
_EXTERNAL_TABLES = {"life_event_log", "life_events"}
_SHARED_SOFT_TABLES = {"chart_facts"}  # multi-producer -> best-effort warn only

_REGISTER_RE = re.compile(r"@register\(\s*['\"]([a-z0-9_]+)['\"]")
_READ_RE = re.compile(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)", re.IGNORECASE)
_FROM_IN_SQL_RE = re.compile(r"\bFROM\s+([a-z_][a-z0-9_]*)", re.IGNORECASE)


def _load_registry(conn):
    rows = conn.execute(
        """SELECT asset_id, COALESCE(depends_on,'{}') AS depends_on, scope,
                  target_table, count_sql, asset_kind, asset_type
           FROM asset_registry WHERE is_active = true"""
    ).fetchall()
    return {r["asset_id"]: r for r in rows}


def _load_real_tables(conn) -> set[str]:
    """Actual public tables — used to reject regex matches on SQL keywords/comments
    (e.g. 'FROM the ...' in prose) and on CTE/subquery aliases."""
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    return {r["table_name"].lower() for r in rows}


def _strip_sql_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", " ", sql)


def _producer_tables(reg: dict, real_tables: set[str]) -> dict[str, set[str]]:
    """asset_id -> set of REAL tables it PRODUCES (target_table + tables named in count_sql)."""
    out: dict[str, set[str]] = {}
    for aid, r in reg.items():
        if r["scope"] != "per_chart":
            continue
        tables: set[str] = set()
        if r["target_table"] and r["target_table"].lower() in real_tables:
            tables.add(r["target_table"].lower())
        if r["count_sql"]:
            tables.update(t.lower() for t in _FROM_IN_SQL_RE.findall(_strip_sql_comments(r["count_sql"]))
                          if t.lower() in real_tables)
        if tables:
            out[aid] = tables
    return out


def _transitive_closure(reg: dict, aid: str) -> set[str]:
    seen: set[str] = set()
    stack = list(reg.get(aid, {}).get("depends_on") or [])
    while stack:
        d = stack.pop()
        if d in seen:
            continue
        seen.add(d)
        stack.extend(reg.get(d, {}).get("depends_on") or [])
    return seen


def _writer_files() -> list[Path]:
    files: list[Path] = []
    for root in _WRITER_ROOTS:
        if root.exists():
            files.extend(p for p in root.rglob("*.py")
                         if "__pycache__" not in p.parts and not p.name.startswith("test_"))
    return files


def _asset_for_file(text: str) -> str | None:
    m = _REGISTER_RE.search(text)
    return m.group(1) if m else None


def _reads(text: str) -> set[str]:
    """All table names appearing after FROM/JOIN, lowercased (over-approximates; filtered later).

    Strips SQL/Python comment lines first — a commented-out query or an
    explanatory `# reads old_table` note otherwise reads as a real dependency
    and produces a false-positive HARD violation (or masks the real gap by
    satisfying the closure check on a table the writer no longer actually reads).
    """
    stripped = _strip_sql_comments(text)
    stripped = re.sub(r"#.*", " ", stripped)
    return {t.lower() for t in _READ_RE.findall(stripped)}


def evaluate(reg: dict, real_tables: set[str], writer_items: list[tuple[str, str]]) -> dict:
    """Pure core (no I/O): given the registry, the real-table set, and a list of
    (relpath, source_text) writer items, return {hard, soft, checked_assets}.
    Separated from analyze() so the detection logic is unit-testable without a DB."""
    prod_tables = _producer_tables(reg, real_tables)
    table_owners: dict[str, set[str]] = {}
    for aid, tables in prod_tables.items():
        for t in tables:
            table_owners.setdefault(t, set()).add(aid)

    # A table is HARD-checkable iff exactly one per_chart asset owns it and it isn't a shared/soft table.
    hard_table_producer = {
        t: next(iter(owners))
        for t, owners in table_owners.items()
        if len(owners) == 1 and t not in _SHARED_SOFT_TABLES
    }

    hard: list[str] = []
    soft: list[str] = []
    checked = 0

    for rel, text in writer_items:
        aid = _asset_for_file(text)
        if aid is None or aid not in reg:
            continue
        checked += 1
        closure = _transitive_closure(reg, aid)
        own_tables = prod_tables.get(aid, set())

        for tbl in _reads(text):
            if tbl not in real_tables:
                continue  # CTE alias / SQL keyword / prose match — not a real table
            if (tbl.startswith(_UNGATED_PREFIXES) or tbl in _UNGATED_EXACT
                    or tbl in _EXTERNAL_TABLES or tbl in own_tables):
                continue
            if tbl in _SHARED_SOFT_TABLES:
                producers = table_owners.get(tbl, set())
                if producers and not (producers & closure):
                    soft.append(f"{aid} ({rel}): reads {tbl} but no chart_facts producer in closure")
                continue
            producer = hard_table_producer.get(tbl)
            if producer is None or producer == aid:
                continue
            if producer not in closure:
                hard.append(
                    f"{aid} ({rel}): reads {tbl} (produced by {producer}) "
                    f"but {producer} is NOT in depends_on closure"
                )

    return {"hard": sorted(set(hard)), "soft": sorted(set(soft)), "checked_assets": checked}


def analyze() -> dict:
    """Return {hard, soft, checked_assets} against the live registry + writer files."""
    from .db import connect  # deferred: keeps --self-test free of the psycopg dependency

    with connect() as conn:
        reg = _load_registry(conn)
        real_tables = _load_real_tables(conn)
    items = [
        (str(p.relative_to(_SIDECAR)), p.read_text(encoding="utf-8", errors="ignore"))
        for p in _writer_files()
    ]
    return evaluate(reg, real_tables, items)


# ── DB-free self-test (the CI hard gate) ──────────────────────────────────────

# Kept deliberately small and readable: this fixture IS the gate's specification.
_SELF_TEST_REGISTRY = {
    "ka_sangam": {
        "asset_id": "ka_sangam", "scope": "per_chart",
        "target_table": "kala_convergence",
        "count_sql": "SELECT count(*) FROM kala_convergence",
        "depends_on": [],
    },
    "ph_pratikara": {
        "asset_id": "ph_pratikara", "scope": "per_chart",
        "target_table": "phala_mitigation",
        "count_sql": "SELECT count(*) FROM phala_mitigation",
        "depends_on": [],          # the seeded defect: ka_sangam NOT declared
    },
}
_SELF_TEST_TABLES = {"kala_convergence", "phala_mitigation"}
_SELF_TEST_SRC = (
    "@register('ph_pratikara')\n"
    "SQL = 'SELECT * FROM kala_convergence WHERE chart_id=%s'\n"
)


def run_self_test() -> int:
    """Prove the detector by mutation, with no database.

    Exits 0 iff BOTH hold:
      (a) a writer reading a producer table whose asset is NOT in its depends_on
          closure is FLAGGED as a HARD violation;
      (b) the same writer, with the edge declared, comes back CLEAN.
    (b) is what stops a degenerate "always flag everything" detector from passing;
    (a) is what stops the degenerate "always return []" detector — which is the
    failure mode a gate that never runs is indistinguishable from.

    Honest bound: this proves `evaluate()`'s logic against a synthetic fixture. It
    proves NOTHING about the live registry — that is `analyze()`, which needs
    DATABASE_URL. See the module docstring for where the live scan runs.
    """
    import copy

    broken = copy.deepcopy(_SELF_TEST_REGISTRY)
    res_broken = evaluate(broken, _SELF_TEST_TABLES, [("ph_pratikara.py", _SELF_TEST_SRC)])
    ok_broken = any(
        "ph_pratikara" in h and "kala_convergence" in h and "ka_sangam" in h
        for h in res_broken["hard"]
    )

    declared = copy.deepcopy(_SELF_TEST_REGISTRY)
    declared["ph_pratikara"]["depends_on"] = ["ka_sangam"]
    res_declared = evaluate(declared, _SELF_TEST_TABLES, [("ph_pratikara.py", _SELF_TEST_SRC)])
    ok_declared = res_declared["hard"] == []

    print(f"[dag_edge_guard --self-test] undeclared cross-asset read -> "
          f"{len(res_broken['hard'])} HARD (expected >=1 naming ph_pratikara/"
          f"kala_convergence/ka_sangam): {'PASS' if ok_broken else 'FAIL'}")
    print(f"[dag_edge_guard --self-test] same read, edge declared -> "
          f"{len(res_declared['hard'])} HARD (expected 0): "
          f"{'PASS' if ok_declared else 'FAIL'}")
    if ok_broken and ok_declared:
        print("[dag_edge_guard --self-test] OK — the detector fires on a missing "
              "edge and clears when it is declared")
        return 0
    print("[dag_edge_guard --self-test] FAILED — the detector does not "
          "discriminate; it cannot be relied on as a gate")
    return 1


# A live scan resolving fewer than this many writer assets is a broken scan (a
# missing writer root, an empty registry, a bad checkout) — not a clean DAG.
# Matches the floor the live integration test has always asserted.
_MIN_CHECKED_ASSETS = 50


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAG edge-completeness guard")
    ap.add_argument("--self-test", action="store_true",
                    help="Run the DB-free fixture mutation self-test (the CI hard gate).")
    ap.add_argument("--min-assets", type=int, default=_MIN_CHECKED_ASSETS,
                    help="Fail if the live scan resolved fewer writer assets than this.")
    args = ap.parse_args(argv)
    if args.self_test:
        return run_self_test()

    res = analyze()
    print(f"[dag_edge_guard] checked {res['checked_assets']} writer assets")
    if res["soft"]:
        print(f"[dag_edge_guard] {len(res['soft'])} SOFT (chart_facts, review):")
        for s in res["soft"]:
            print(f"  ~ {s}")
    if res["hard"]:
        print(f"[dag_edge_guard] {len(res['hard'])} HARD violation(s):")
        for h in res["hard"]:
            print(f"  ✗ {h}")
        return 1
    # F-02: a scan that resolved nothing must not print a pass. Zero violations
    # over zero assets is the absence of a measurement, not a clean result.
    if res["checked_assets"] < args.min_assets:
        print(f"[dag_edge_guard] INCONCLUSIVE — only {res['checked_assets']} writer "
              f"assets resolved (floor {args.min_assets}). The scan did not cover the "
              f"DAG; this is NOT a pass. Check the writer roots and the registry.")
        return 1
    print(f"[dag_edge_guard] OK — no hard edge-completeness violations across "
          f"{res['checked_assets']} writer assets (HARD tier: 1:1-owned per_chart "
          f"tables; chart_facts reads are SOFT/warn-only; dynamic-SQL reads are "
          f"outside this guard's detection)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
