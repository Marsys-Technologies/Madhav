"""
pipeline.orchestrator.dag_edge_guard
====================================

Edge-completeness guard for the build DAG.

INVARIANT: every per-chart producer TABLE a writer reads must be produced by an
asset that is in the reading asset's transitive `depends_on` closure. If a writer
reads asset X's output table but X is not (transitively) declared, the scheduler
can run the writer before X completes -> build on incomplete/missing data. The
serial build hides this via sort-order luck; the wave-parallel scheduler does not.

This automates, as a CI gate, the manual reads-vs-declared audit that produced
migration 365. It catches drift the moment a writer adds an undeclared cross-asset
read.

Two tiers:
  * HARD  — reads of a table owned by exactly ONE per_chart asset (1:1). A missing
            transitive edge is a FAILURE. Covers all cross-layer drift.
  * SOFT  — reads of `chart_facts` (a shared table written by ~8 L1 assets,
            partitioned by fact_category). Static fact_category resolution is
            imperfect, so these are reported as WARNINGS, not failures.

Globals / L0 (always-present bedrock: bg_*, reference_*, ephemeris_daily, etc.)
and external ingest tables (life_event*) are never gated.

Run as a script:  python -m pipeline.orchestrator.dag_edge_guard   (exit 1 on hard violation)
Used by:          pipeline/__tests__/test_dag_edge_guard.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .db import connect

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
    with connect() as conn:
        reg = _load_registry(conn)
        real_tables = _load_real_tables(conn)
    items = [
        (str(p.relative_to(_SIDECAR)), p.read_text(encoding="utf-8", errors="ignore"))
        for p in _writer_files()
    ]
    return evaluate(reg, real_tables, items)


def main() -> int:
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
    print("[dag_edge_guard] OK — no hard edge-completeness violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
