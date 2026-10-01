#!/usr/bin/env python3
"""msr_rebuild_order_guard.py -- F-3 rebuild-plan invariant (until migration 1214 is deployed).

INVARIANT (per chart): every asset that regenerates bodha_msr_signals runs in a STRICTLY EARLIER wave than
every asset whose rows reference those signals, and no MSR writer rebuilds that chart again in the same
window (from the first such dependent's start until the wave ends).

Why: until the kala_*.signal_id foreign keys are dropped (migration 1214), an MSR regeneration CASCADE-deletes
the Kala rows (and, through kala_convergence, the Phala rows). After 1214 the same ordering keeps references
valid instead of merely un-deleted: dependents rebuilt AFTER the MSR set see the final ids.

MSR producers are the six assets in bodha_msr_signals_producer_asset_check (migration 1036), which are also
exactly the writers under pipeline/orchestrator/writers that INSERT INTO bodha_msr_signals.

Modes
  --manifest FILE   plan to check: a build_runs.plan_manifest JSON object with `waves` (list of lists of
                    asset ids) or a bare list of lists. Exit 1 on any violation.
  --require-nonvacuous  exit 1 when the plan orders nothing (no MSR writer or no dependent in it).
  --verify-map      DATABASE_URL: re-derive the signal-bearing columns from the live catalog; fail if the
                    dependents map (msr_signal_bearing_tables.json) is missing one.
  --self-test       DB-free fixtures.
  --chart-id UUID   with DATABASE_URL, run the read-only SQL checks. PRE-wave: PF-1 (no in-flight run for the
                    chart) fails the run; PF-2 (dependents built before the last MSR regeneration) is reported
                    only, because that is the expected state before the wave. POST-wave (--post-wave): PF-2
                    fails too -- after the wave every dependent must postdate the last MSR regeneration.
Exit: 0 ok, 1 violation, 2 invocation/environment error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Sequence

MSR_PRODUCERS = frozenset({
    "bo_laksana", "bo_arudha", "bo_special_lagna", "bo_sudarshana", "bo_vargottama_dhana",
    "bo_nakshatra_semantic",
})
# Dependents are DERIVED, not hand-listed: msr_signal_bearing_tables.json maps every table that holds
# bodha_msr_signals.signal_id values (live catalog, 2026-10-01) to the assets that write it; tests re-derive
# both halves from the migrations and the writers, and --verify-map re-reads the live catalog.
_MAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "msr_signal_bearing_tables.json")))
# Assets of the five tables whose foreign keys migration 1214 drops.
DIRECT_DEPENDENTS = frozenset(a for t in _MAP["tables"] if t["keyed"] == "fk_dropped" for a in t["assets"])
# Every asset whose target table carries MSR signal ids (the five above, ka_yojaka, ph_nimitta, the L2
# consumers that store ids or id arrays).
SIGNAL_BEARING_DEPENDENTS = frozenset(a for t in _MAP["tables"] for a in t["assets"])
# Rows reached through kala_convergence's / phala_anchors' own CASCADE / SET NULL keys.
TRANSITIVE_DEPENDENTS = frozenset(a for _t, a in _MAP["transitive_cascade"]["tables"])
DEPENDENTS = SIGNAL_BEARING_DEPENDENTS | TRANSITIVE_DEPENDENTS

DERIVE_SQL = (
    "SELECT c.relname || '.' || a.attname FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
    "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relkind IN ('r','p') "
    "AND a.attnum > 0 AND NOT a.attisdropped AND a.attname ~ 'signal' "
    "AND format_type(a.atttypid, a.atttypmod) IN ('uuid','uuid[]') AND c.relname !~ '__ssv_' "
    "AND c.relname <> 'bodha_msr_signals' ORDER BY 1")


def mapped_columns() -> set[str]:
    return {f"{t['table']}.{c}" for t in _MAP["tables"] for c in t["columns"]}


def unmapped_columns(live: set[str]) -> list[str]:
    """Live signal-bearing columns the dependents map does not know (each is an unlisted dependent)."""
    return sorted(live - mapped_columns())


@dataclass(frozen=True)
class Violation:
    code: str
    msr_producer: str
    dependent: str
    msr_wave: int
    dependent_wave: int

    def __str__(self) -> str:
        return (f"{self.code}: MSR writer {self.msr_producer} (wave {self.msr_wave}) is not strictly before "
                f"dependent {self.dependent} (wave {self.dependent_wave})")


def plan_vacuity(waves: Sequence[Sequence[str]]) -> list[str]:
    """Why the order check proves nothing for this plan ([] = it orders something)."""
    present = {a for w in waves for a in w}
    why = []
    if not MSR_PRODUCERS & present:
        why.append("no MSR writer in the plan")
    if not DEPENDENTS & present:
        why.append("no MSR-dependent asset in the plan")
    return why


def parse_waves(doc) -> list[list[str]]:
    waves = doc["waves"] if isinstance(doc, dict) else doc
    if not isinstance(waves, list) or not all(isinstance(w, list) for w in waves):
        raise ValueError("plan must be a list of waves (lists of asset ids)")
    return [[str(a) for a in w] for w in waves]


def check_plan_order(waves: Sequence[Sequence[str]]) -> list[Violation]:
    """Violations of the invariant inside one plan. Same-wave assets run in parallel, so a producer and a
    dependent in the SAME wave is a violation; a producer in a LATER wave than a dependent is a violation
    (the window rule: nothing regenerates MSR after a dependent has started)."""
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    for w, assets in enumerate(waves, start=1):
        for a in assets:
            first.setdefault(a, w)
            last[a] = w
    out: list[Violation] = []
    for p in sorted(MSR_PRODUCERS & first.keys()):
        for d in sorted(DEPENDENTS & first.keys()):
            if last[p] >= first[d]:
                out.append(Violation("MSR_NOT_BEFORE_DEPENDENT", p, d, last[p], first[d]))
    return out


# --- live pre-flight (read-only SELECTs; params: chart_id) -----------------------------------------------
PF1_ACTIVE_RUN_SQL = (
    "SELECT id::text, state FROM build_runs WHERE chart_id = %s::uuid "
    "AND state IN ('planned','running','paused')")
PF2_ORDER_STATE_SQL = (
    "SELECT t.asset_id, t.last_built_at, m.last_msr_end FROM asset_throughput t "
    "CROSS JOIN (SELECT max(a.ended_at) AS last_msr_end FROM build_run_assets a "
    "JOIN build_runs r ON r.id = a.run_id WHERE r.chart_id = %s::uuid AND a.state = 'complete' "
    "AND a.asset_id = ANY(%s::text[])) m "
    "WHERE t.chart_id = %s::uuid AND t.asset_id = ANY(%s::text[]) ORDER BY t.asset_id")


def stale_against_msr(rows: Sequence[tuple]) -> list[str]:
    """Dependents whose last build is older than the last MSR regeneration (their rows predate, and under
    the cascade were erased by, that regeneration). A dependent never built is not 'stale against MSR'."""
    return [a for a, built, msr_end in rows
            if built is not None and msr_end is not None and built < msr_end]


def _run_self_test() -> int:
    ok = [["bo_laksana", "bo_arudha"], ["ka_sangam"], ["ka_kalasutra", "ph_nimitta"]]
    same = [["bo_laksana", "ka_sangam"]]
    late = [["ka_sangam"], ["bo_special_lagna"]]
    if check_plan_order(ok) or not check_plan_order(same) or not check_plan_order(late):
        print("[msr-order] SELF-TEST FAIL", file=sys.stderr)
        return 1
    print("[msr-order] SELF-TEST PASS: ordered plan clean; same-wave and later-wave MSR writers caught.")
    return 0


def _preflight(chart_id: str, post_wave: bool) -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("[msr-order] DATABASE_URL not set", file=sys.stderr)
        return 2
    import psycopg
    msr, dep = sorted(MSR_PRODUCERS), sorted(DEPENDENTS)
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.read_only = True
        active = conn.execute(PF1_ACTIVE_RUN_SQL, [chart_id]).fetchall()
        rows = conn.execute(PF2_ORDER_STATE_SQL, [chart_id, msr, chart_id, dep]).fetchall()
    stale = stale_against_msr(rows)
    print(f"PF-1 in-flight runs for chart: {len(active)} {active}")
    print(f"PF-2 dependents built before the last MSR regeneration: {stale}")
    return 1 if active or (post_wave and stale) else 0


def _verify_map() -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("[msr-order] DATABASE_URL not set", file=sys.stderr)
        return 2
    import psycopg
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.read_only = True
        live = {r[0] for r in conn.execute(DERIVE_SQL).fetchall()}
    missing = unmapped_columns(live)
    print(f"[msr-order] verify-map: {len(live)} live signal-bearing columns; not in the map: {missing}")
    return 1 if missing else 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--chart-id")
    ap.add_argument("--post-wave", action="store_true")
    ap.add_argument("--require-nonvacuous", action="store_true",
                    help="exit 1 when the plan orders nothing (no MSR writer, or no dependent, in it)")
    ap.add_argument("--verify-map", action="store_true",
                    help="DATABASE_URL: re-derive the signal-bearing columns from the live catalog and "
                         "fail if one is missing from msr_signal_bearing_tables.json")
    a = ap.parse_args(argv)
    if a.self_test:
        return _run_self_test()
    rc = 0
    if a.manifest:
        try:
            waves = parse_waves(json.load(open(a.manifest)))
            viol = check_plan_order(waves)
            planned = sorted(MSR_PRODUCERS & {x for w in waves for x in w})
            why = plan_vacuity(waves)
        except (OSError, ValueError, KeyError) as exc:
            print(f"[msr-order] ERROR: {exc}", file=sys.stderr)
            return 2
        for v in viol:
            print(f"[msr-order] {v}", file=sys.stderr)
        note = f" VACUOUS ({'; '.join(why)}): this check ordered nothing." if why else ""
        print(f"[msr-order] plan order: {'FAIL' if viol else 'PASS'} ({len(viol)} violation(s));"
              f" MSR writers in plan: {planned}.{note}")
        rc = 1 if viol or (why and a.require_nonvacuous) else 0
    if a.chart_id:
        rc = max(rc, _preflight(a.chart_id, a.post_wave))
    if a.verify_map:
        rc = max(rc, _verify_map())
    if not a.manifest and not a.chart_id and not a.verify_map:
        ap.print_usage(sys.stderr)
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
