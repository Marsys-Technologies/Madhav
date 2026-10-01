#!/usr/bin/env python3
"""msr_dangling_signal_refs.py -- read-only dangling-reference detector for MSR signal ids.

F-3 (N-32; migration 1214). The five kala_* foreign keys into bodha_msr_signals.signal_id are
dropped so an L2 regeneration can never delete L3 rows. Without the key a referencing row can
DANGLE: its signal_id no longer exists in bodha_msr_signals (the signal changed identity or
disappeared) or exists for a different chart. This module is the detector that replaces the
key's job of making that visible. It never writes.

Why stable ids make most references survive a regeneration: signal_id = uuid v5 of
(chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb) (bodha_signal_identity,
migration 661). An unchanged signal keeps its id. A signal whose configuration (or varga, type,
ayanamsha) changed IS a different signal and takes a new id: its references dangle here until the
downstream asset rebuilds in its wave.

Reference sites (tier):
  fk_dropped     the five kala tables whose FK migration 1214 drops. A dangling or cross-chart
                 row here FAILS the check (this is the regression the FK used to prevent).
  l2_internal    bodha_contradictions / bodha_signal_embeddings: still FK'd today (owner-path
                 drop pending); reported for the day the FK goes; fail only with --strict.
  unconstrained  kala_activation_predicates / phala_anchors: never had a key; reported, advisory.

Modes
  --self-test          DB-free fixture self-test (clean fixture clean; mutated fixture caught).
  --chart-id UUID      live read-only scan of one chart (needs DATABASE_URL).
  (default)            live read-only scan of every chart.
  --strict             also fail on l2_internal / unconstrained sites.
  --json               machine-readable output.
Exit: 0 clean (a clean result over zero referencing rows is reported as VACUOUS, not as proof),
      1 dangling/cross-chart references (or self-test failure), 2 invocation/environment error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

FK_DROPPED = "fk_dropped"
L2_INTERNAL = "l2_internal"
UNCONSTRAINED = "unconstrained"


@dataclass(frozen=True)
class RefSite:
    table: str
    column: str
    tier: str


REF_SITES: tuple[RefSite, ...] = (
    RefSite("kala_convergence", "signal_id", FK_DROPPED),
    RefSite("kala_activation", "signal_id", FK_DROPPED),
    RefSite("kala_obstruction", "signal_id", FK_DROPPED),
    RefSite("kala_darshana", "signal_id", FK_DROPPED),
    RefSite("kala_bhavishya", "signal_id", FK_DROPPED),
    RefSite("bodha_contradictions", "signal_a_id", L2_INTERNAL),
    RefSite("bodha_contradictions", "signal_b_id", L2_INTERNAL),
    RefSite("bodha_signal_embeddings", "signal_id", L2_INTERNAL),
    RefSite("kala_activation_predicates", "signal_id", UNCONSTRAINED),
    RefSite("phala_anchors", "signal_id", UNCONSTRAINED),
)

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _site_idents(site: RefSite) -> tuple[str, str]:
    """Identifiers are interpolated into SQL, so only a declared site is accepted."""
    if site not in REF_SITES or not _IDENT.match(site.table) or not _IDENT.match(site.column):
        raise ValueError(f"not a declared MSR reference site: {site!r}")
    return site.table, site.column


# ---------------------------------------------------------------------------
# SQL (the live detector's one decision surface; read-only SELECTs)
# ---------------------------------------------------------------------------

def dangling_sql(site: RefSite, *, chart_scoped: bool) -> str:
    """Per-chart counts: referencing rows, dangling (signal absent), cross_chart (signal of
    another chart). A NULL reference is not a reference (the nullable kala columns)."""
    table, col = _site_idents(site)
    scope = "AND k.chart_id = %s" if chart_scoped else ""
    return (
        f"SELECT k.chart_id, count(*) AS referencing, "
        f"count(*) FILTER (WHERE s.signal_id IS NULL) AS dangling, "
        f"count(*) FILTER (WHERE s.signal_id IS NOT NULL AND s.chart_id <> k.chart_id) AS cross_chart "
        f"FROM {table} k LEFT JOIN bodha_msr_signals s ON s.signal_id = k.{col} "
        f"WHERE k.{col} IS NOT NULL {scope} GROUP BY k.chart_id ORDER BY k.chart_id"
    )


def would_orphan_sql(site: RefSite) -> str:
    """Rows that reference signals inside an MSR replacement scope (the scope
    assert_l2_msr_delete_safe locks): params chart_id, producer_asset_id, then each filter
    twice (ayanamsha_ids, signal_type_ids, signal_type_classes; NULL = no filter)."""
    table, col = _site_idents(site)
    return (
        f"SELECT count(*) FROM {table} d JOIN bodha_msr_signals s ON d.{col} = s.signal_id "
        f"WHERE s.chart_id = %s AND s.producer_asset_id = %s "
        f"AND (%s::text[] IS NULL OR s.ayanamsha_id = ANY(%s::text[])) "
        f"AND (%s::text[] IS NULL OR s.signal_type_id = ANY(%s::text[])) "
        f"AND (%s::text[] IS NULL OR s.signal_type_class = ANY(%s::text[]))"
    )


# ---------------------------------------------------------------------------
# Pure core (DB-free, unit-testable, mutation-provable)
# ---------------------------------------------------------------------------

def classify_reference(signal_id: str | None, chart_id: str, msr_index: Mapping[str, str]) -> str:
    """'null_ref' | 'ok' | 'dangling' | 'cross_chart' for one referencing row."""
    if signal_id is None:
        return "null_ref"
    owner_chart = msr_index.get(str(signal_id))
    if owner_chart is None:
        return "dangling"
    if str(owner_chart) != str(chart_id):
        return "cross_chart"
    return "ok"


@dataclass(frozen=True)
class SiteResult:
    table: str
    column: str
    tier: str
    chart_id: str
    referencing: int
    dangling: int
    cross_chart: int

    @property
    def broken(self) -> int:
        return self.dangling + self.cross_chart


def scan_references(site: RefSite, refs: Iterable[tuple[str | None, str]],
                    msr_index: Mapping[str, str]) -> list[SiteResult]:
    """Pure equivalent of dangling_sql over in-memory rows [(signal_id, chart_id)]."""
    per_chart: dict[str, list[int]] = {}
    for signal_id, chart_id in refs:
        verdict = classify_reference(signal_id, chart_id, msr_index)
        if verdict == "null_ref":
            continue
        row = per_chart.setdefault(str(chart_id), [0, 0, 0])
        row[0] += 1
        if verdict == "dangling":
            row[1] += 1
        elif verdict == "cross_chart":
            row[2] += 1
    return [SiteResult(site.table, site.column, site.tier, c, *per_chart[c])
            for c in sorted(per_chart)]


@dataclass(frozen=True)
class RegenEffect:
    kept: int
    disappeared: int
    new: int
    orphaned_refs: int


def regeneration_effect(before_ids: set[str], after_ids: set[str],
                        referenced_ids: Iterable[str]) -> RegenEffect:
    """What a regeneration of one MSR scope does to references: ids present before and after are
    kept (references stay valid); ids only before DISAPPEARED (references into them dangle)."""
    disappeared = before_ids - after_ids
    orphaned = sum(1 for r in referenced_ids if str(r) in disappeared)
    return RegenEffect(len(before_ids & after_ids), len(disappeared),
                       len(after_ids - before_ids), orphaned)


def failing_results(results: Sequence[SiteResult], *, strict: bool) -> list[SiteResult]:
    """Results that fail the check: broken rows at an fk_dropped site always; at the other tiers
    only under --strict."""
    return [r for r in results
            if r.broken > 0 and (strict or r.tier == FK_DROPPED)]


def is_vacuous(results: Sequence[SiteResult]) -> bool:
    """A clean verdict over zero referencing rows proves nothing (CLAUDE.md N.8)."""
    return sum(r.referencing for r in results) == 0


# ---------------------------------------------------------------------------
# Self-test (DB-free hard gate + mutation proof)
# ---------------------------------------------------------------------------

_C1, _C2 = "c1", "c2"
_SITE = REF_SITES[0]


def _fixture(*, mutate: bool) -> tuple[list[tuple[str | None, str]], dict[str, str]]:
    msr = {"s1": _C1, "s2": _C1, "s3": _C2}
    refs: list[tuple[str | None, str]] = [("s1", _C1), ("s2", _C1), (None, _C1), ("s3", _C2)]
    if mutate:
        refs += [("gone", _C1), ("s3", _C1)]  # one dangling, one cross-chart
    return refs, msr


def _run_self_test() -> int:
    refs, msr = _fixture(mutate=False)
    clean = failing_results(scan_references(_SITE, refs, msr), strict=True)
    if clean:
        print("[msr-dangling] SELF-TEST FAIL: clean fixture flagged", file=sys.stderr)
        return 1
    refs, msr = _fixture(mutate=True)
    res = scan_references(_SITE, refs, msr)
    if sum(r.dangling for r in res) != 1 or sum(r.cross_chart for r in res) != 1 \
            or not failing_results(res, strict=False):
        print("[msr-dangling] SELF-TEST FAIL: mutated fixture not caught", file=sys.stderr)
        return 1
    print("[msr-dangling] SELF-TEST PASS: clean fixture clean; one dangling and one "
          "cross-chart reference caught.")
    return 0


# ---------------------------------------------------------------------------
# Live read-only mode
# ---------------------------------------------------------------------------

def _scan_live(chart_id: str | None, tiers: Sequence[str] | None = None
               ) -> tuple[list[SiteResult], list[str]]:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set (use --self-test for the DB-free gate)")
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg not available") from exc
    out: list[SiteResult] = []
    unreadable: list[str] = []
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.read_only = True
        for site in REF_SITES:
            if tiers and site.tier not in tiers:
                continue
            params = (chart_id,) if chart_id else ()
            try:
                rows = conn.execute(
                    dangling_sql(site, chart_scoped=bool(chart_id)), params).fetchall()
            except psycopg.Error as exc:  # an unreadable site is NOT a clean site
                unreadable.append(f"{site.table}.{site.column}: {type(exc).__name__}")
                continue
            for cid, referencing, dangling, cross in rows:
                out.append(SiteResult(site.table, site.column, site.tier, str(cid),
                                      int(referencing), int(dangling), int(cross)))
    return out, unreadable


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--chart-id", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tiers", default=None,
                    help="comma list of tiers to scan (default: all); a site the role cannot "
                         "read is reported and makes the run exit 2, never a silent pass")
    args = ap.parse_args(argv)
    if args.self_test:
        return _run_self_test()
    try:
        results, unreadable = _scan_live(
            args.chart_id, args.tiers.split(",") if args.tiers else None)
    except Exception as exc:  # environment error, not a verdict
        print(f"[msr-dangling] ERROR: {exc}", file=sys.stderr)
        return 2
    for u in unreadable:
        print(f"[msr-dangling] UNREADABLE {u}", file=sys.stderr)
    failing = failing_results(results, strict=args.strict)
    vacuous = is_vacuous(results)
    if args.json:
        print(json.dumps({"results": [asdict(r) | {"broken": r.broken} for r in results],
                          "failing": len(failing), "vacuous": vacuous}, indent=1))
    else:
        for r in results:
            print(f"{r.tier:13} {r.table}.{r.column} chart={r.chart_id} "
                  f"referencing={r.referencing} dangling={r.dangling} cross_chart={r.cross_chart}")
        print(f"[msr-dangling] {'FAIL' if failing else 'PASS'}"
              f"{' (VACUOUS: zero referencing rows)' if vacuous and not failing else ''}: "
              f"{len(failing)} failing site-chart pair(s)")
    if failing:
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
