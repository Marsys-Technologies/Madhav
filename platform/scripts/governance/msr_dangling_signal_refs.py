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
Exit: 0 PASS (no broken row and no vacuous site), 1 broken references (or --require-nonvacuous with a
      vacuous site, or self-test failure), 2 invocation/environment error (unknown --tiers value, an
      unreadable site, no DATABASE_URL), 3 INCONCLUSIVE (clean, but a scanned site has zero referencing
      rows, so nothing was proven for it; --allow-vacuous turns that into 0).

Limits stated so the check cannot overclaim: it sees a row that EXISTS and points at nothing. A referencing
row that was DELETED (what the old CASCADE did) leaves no trace in the table; that is caught by the
before-state row counts / digests (PF-2 in the rebuild plan), not by this detector. A row with a NULL
chart_id that references a live signal is reported as unattributable. Array-valued references (the L2
bodha_* *_signal_ids_array columns) are not scanned.
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
ALL_TIERS = frozenset({FK_DROPPED, L2_INTERNAL, UNCONSTRAINED})


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

NULL_CHART = "<NULL chart_id>"
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
    another chart), unattributable (the row's own chart_id is NULL but it references a live
    signal, so no chart can be held to account). A NULL reference is not a reference (the
    nullable kala columns). Chart-scoped mode takes two params (chart_id twice) and also sees
    NULL-chart rows that reference a signal of that chart; a NULL-chart row whose signal is
    absent is visible only in the global scan. A DELETED referencing row is invisible to any
    query over the table itself: that is the before-state count/digest comparison (PF-2)."""
    table, col = _site_idents(site)
    scope = ("AND (k.chart_id = %s OR (k.chart_id IS NULL AND s.chart_id = %s))"
             if chart_scoped else "")
    return (
        f"SELECT k.chart_id, count(*) AS referencing, "
        f"count(*) FILTER (WHERE s.signal_id IS NULL) AS dangling, "
        f"count(*) FILTER (WHERE s.signal_id IS NOT NULL AND k.chart_id IS NOT NULL "
        f"AND s.chart_id IS DISTINCT FROM k.chart_id) AS cross_chart, "
        f"count(*) FILTER (WHERE s.signal_id IS NOT NULL AND k.chart_id IS NULL) AS unattributable "
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

def classify_reference(signal_id: str | None, chart_id: str | None,
                       msr_index: Mapping[str, str]) -> str:
    """'null_ref' | 'ok' | 'dangling' | 'cross_chart' | 'unattributable' for one referencing row."""
    if signal_id is None:
        return "null_ref"
    owner_chart = msr_index.get(str(signal_id))
    if owner_chart is None:
        return "dangling"
    if chart_id is None:
        return "unattributable"
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
    unattributable: int = 0

    @property
    def broken(self) -> int:
        return self.dangling + self.cross_chart + self.unattributable


def scan_references(site: RefSite, refs: Iterable[tuple[str | None, str | None]],
                    msr_index: Mapping[str, str]) -> list[SiteResult]:
    """Pure equivalent of dangling_sql over in-memory rows [(signal_id, chart_id)]."""
    per_chart: dict[str, list[int]] = {}  # chart label -> [referencing, dangling, cross, unattrib]
    for signal_id, chart_id in refs:
        verdict = classify_reference(signal_id, chart_id, msr_index)
        if verdict == "null_ref":
            continue
        row = per_chart.setdefault(NULL_CHART if chart_id is None else str(chart_id), [0, 0, 0, 0])
        row[0] += 1
        if verdict == "dangling":
            row[1] += 1
        elif verdict == "cross_chart":
            row[2] += 1
        elif verdict == "unattributable":
            row[3] += 1
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


def vacuous_sites(results: Sequence[SiteResult], scanned: Sequence[RefSite]) -> list[RefSite]:
    """Scanned sites with ZERO referencing rows: for those the check proved nothing (CLAUDE.md N.8).
    Judged PER SITE: a clean total over one populated site must not vouch for an empty one."""
    populated = {(r.table, r.column) for r in results if r.referencing > 0}
    return [s for s in scanned if (s.table, s.column) not in populated]


def parse_tiers(raw: str | None) -> tuple[str, ...] | None:
    """None -> every tier. An unknown or empty tier name is an error, never 'scan nothing'."""
    if raw is None:
        return None
    names = tuple(t.strip() for t in raw.split(","))
    unknown = [t for t in names if t not in ALL_TIERS]
    if not names or unknown:
        raise ValueError(f"unknown tier(s) {unknown or ['<empty>']}; valid: {sorted(ALL_TIERS)}")
    return names


EXIT_PASS, EXIT_FAIL, EXIT_ERROR, EXIT_INCONCLUSIVE = 0, 1, 2, 3


def decide(results: Sequence[SiteResult], scanned: Sequence[RefSite], unreadable: Sequence[str], *,
           strict: bool, require_nonvacuous: bool, allow_vacuous: bool) -> tuple[str, int]:
    """(label, exit code). Broken rows fail; an unreadable site is an error; a vacuous site is
    INCONCLUSIVE (exit 3) unless --require-nonvacuous (exit 1) or --allow-vacuous (pass)."""
    if failing_results(results, strict=strict):
        return "FAIL", EXIT_FAIL
    if unreadable:
        return "ERROR", EXIT_ERROR
    if vacuous_sites(results, scanned):
        if require_nonvacuous:
            return "FAIL (vacuous site, --require-nonvacuous)", EXIT_FAIL
        return ("PASS (vacuous sites allowed)", EXIT_PASS) if allow_vacuous \
            else ("INCONCLUSIVE", EXIT_INCONCLUSIVE)
    return "PASS", EXIT_PASS


# ---------------------------------------------------------------------------
# Self-test (DB-free hard gate + mutation proof)
# ---------------------------------------------------------------------------

_C1, _C2 = "c1", "c2"
_SITE = REF_SITES[0]


def _fixture(*, mutate: bool) -> tuple[list[tuple[str | None, str]], dict[str, str]]:
    msr = {"s1": _C1, "s2": _C1, "s3": _C2}
    refs: list[tuple[str | None, str]] = [("s1", _C1), ("s2", _C1), (None, _C1), ("s3", _C2)]
    if mutate:
        refs += [("gone", _C1), ("s3", _C1), ("s1", None)]  # dangling, cross-chart, unattributable
    return refs, msr


def _run_self_test() -> int:
    refs, msr = _fixture(mutate=False)
    clean = failing_results(scan_references(_SITE, refs, msr), strict=True)
    if clean:
        print("[msr-dangling] SELF-TEST FAIL: clean fixture flagged", file=sys.stderr)
        return 1
    refs, msr = _fixture(mutate=True)
    res = scan_references(_SITE, refs, msr)
    if (sum(r.dangling for r in res), sum(r.cross_chart for r in res),
            sum(r.unattributable for r in res)) != (1, 1, 1) or not failing_results(res, strict=False):
        print("[msr-dangling] SELF-TEST FAIL: mutated fixture not caught", file=sys.stderr)
        return 1
    print("[msr-dangling] SELF-TEST PASS: clean fixture clean; dangling, one "
          "cross-chart and one unattributable reference caught.")
    return 0


# ---------------------------------------------------------------------------
# Live read-only mode
# ---------------------------------------------------------------------------

def _scan_live(chart_id: str | None, tiers: Sequence[str] | None = None
               ) -> tuple[list[SiteResult], list[str], list[RefSite]]:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set (use --self-test for the DB-free gate)")
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg not available") from exc
    out: list[SiteResult] = []
    unreadable: list[str] = []
    scanned: list[RefSite] = []
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.read_only = True
        for site in REF_SITES:
            if tiers and site.tier not in tiers:
                continue
            scanned.append(site)
            params = (chart_id, chart_id) if chart_id else ()
            try:
                rows = conn.execute(
                    dangling_sql(site, chart_scoped=bool(chart_id)), params).fetchall()
            except psycopg.Error as exc:  # an unreadable site is NOT a clean site
                unreadable.append(f"{site.table}.{site.column}: {type(exc).__name__}")
                continue
            for cid, referencing, dangling, cross, unattrib in rows:
                out.append(SiteResult(site.table, site.column, site.tier,
                                      NULL_CHART if cid is None else str(cid),
                                      int(referencing), int(dangling), int(cross), int(unattrib)))
    return out, unreadable, scanned


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--chart-id", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tiers", default=None,
                    help="comma list of tiers to scan (default: all); an unknown tier is an error "
                         "(exit 2); a site the role cannot read makes the run exit 2")
    vac = ap.add_mutually_exclusive_group()
    vac.add_argument("--require-nonvacuous", action="store_true",
                     help="exit 1 when ANY scanned site has zero referencing rows (post-wave use)")
    vac.add_argument("--allow-vacuous", action="store_true",
                     help="treat vacuous sites as a pass (default: INCONCLUSIVE, exit 3)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _run_self_test()
    try:
        tiers = parse_tiers(args.tiers)
        results, unreadable, scanned = _scan_live(args.chart_id, tiers)
    except Exception as exc:  # environment/invocation error, not a verdict
        print(f"[msr-dangling] ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    for u in unreadable:
        print(f"[msr-dangling] UNREADABLE {u}", file=sys.stderr)
    label, code = decide(results, scanned, unreadable, strict=args.strict,
                         require_nonvacuous=args.require_nonvacuous, allow_vacuous=args.allow_vacuous)
    vac_sites = [f"{v.table}.{v.column}" for v in vacuous_sites(results, scanned)]
    if args.json:
        print(json.dumps({"results": [asdict(r) | {"broken": r.broken} for r in results],
                          "verdict": label, "exit": code, "vacuous_sites": vac_sites,
                          "unreadable": list(unreadable)}, indent=1))
    else:
        for r in results:
            print(f"{r.tier:13} {r.table}.{r.column} chart={r.chart_id} referencing={r.referencing} "
                  f"dangling={r.dangling} cross_chart={r.cross_chart} unattributable={r.unattributable}")
        for v in vac_sites:
            print(f"VACUOUS       {v}: zero referencing rows, nothing was proven for this site")
        print(f"[msr-dangling] {label}")
    return code


if __name__ == "__main__":
    sys.exit(main())
