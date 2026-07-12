#!/usr/bin/env python3
"""msr_referential_integrity.py — permanent §N.5 constituent-resolution guard.

WP-2.4 / LCA-9b-5. The durable CI enforcement of CLAUDE.md §N.5:

    "The `constituent_facts_array` in MSR signals resolves back to
     chart_facts.fact_id — these MUST resolve."

Every entry in every `bodha_msr_signals.constituent_facts_array` MUST be a real
`chart_facts.fact_id`. A signal citing a fact_id that resolves to nothing is a
referential-integrity break (the register-documented 9b-5 defect: 220 dosha
signals cited 10 constituent ids that resolved to NOTHING) and a halt-worthy
§N.5 violation, never a stored divergence.

Modes
-----
  --self-test        Run the bundled synthetic fixtures. Exit 0 iff the CLEAN
                     fixture produces zero violations AND the MUTATED fixture
                     (one constituent broken) produces at least one violation.
                     DB-free — this is the hard CI gate (CI has no database).

  --chart-id UUID    Live-DB mode (requires DATABASE_URL). Loads that chart's
                     signals + real fact_id set and reports every unresolved
                     constituent. Used at W3 rebuild verification.

  (default)          Live-DB mode over ALL charts (requires DATABASE_URL).

Exit codes
----------
  0  clean (no unresolved constituents / self-test pass)
  1  unresolved constituents found (or self-test failed)
  2  invocation / environment error
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Core (pure, DB-free, unit-testable, mutation-provable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Violation:
    signal_id: str
    signal_type_id: str
    unresolved: tuple[str, ...]


def find_unresolved_constituents(
    signals: Iterable[dict],
    valid_fact_ids: set[str],
) -> list[Violation]:
    """Return one Violation per signal that cites a constituent fact_id absent
    from `valid_fact_ids` (the authoritative chart_facts.fact_id set).

    A signal with an empty/None constituent array is NOT a violation (it cites
    nothing that could fail to resolve). This is the single source of truth for
    both the self-test and the live-DB scan.
    """
    violations: list[Violation] = []
    for sig in signals:
        arr = sig.get("constituent_facts_array") or []
        if not isinstance(arr, (list, tuple)):
            arr = []
        unresolved = tuple(str(f) for f in arr if str(f) not in valid_fact_ids)
        if unresolved:
            violations.append(Violation(
                signal_id=str(sig.get("signal_id", "?")),
                signal_type_id=str(sig.get("signal_type_id", "?")),
                unresolved=unresolved,
            ))
    return violations


# ---------------------------------------------------------------------------
# Self-test fixtures (DB-free hard gate + mutation proof)
# ---------------------------------------------------------------------------

def _clean_fixture() -> tuple[list[dict], set[str]]:
    valid = {"fa11", "fa22", "fa33", "fa44"}
    signals = [
        {"signal_id": "s1", "signal_type_id": "dosha_label:dosha_name",
         "constituent_facts_array": ["fa11"]},
        {"signal_id": "s2", "signal_type_id": "yoga_label:yoga_name",
         "constituent_facts_array": ["fa22", "fa33"]},
        {"signal_id": "s3", "signal_type_id": "aspect_jaimini_per_varga:aggregate_D1",
         "constituent_facts_array": ["fa11", "fa44"]},
        # empty constituents — legal, not a violation
        {"signal_id": "s4", "signal_type_id": "navamsha_d9_cross_check:sun",
         "constituent_facts_array": []},
    ]
    return signals, valid


def _mutated_fixture() -> tuple[list[dict], set[str]]:
    """Exactly the clean fixture with ONE constituent broken (fa22 -> ghostXX).
    This is the mutation proof: the validator MUST catch it."""
    signals, valid = _clean_fixture()
    signals[1] = dict(signals[1])
    signals[1]["constituent_facts_array"] = ["ghostXX", "fa33"]  # ghostXX ∉ valid
    return signals, valid


def _run_self_test() -> int:
    clean_signals, clean_valid = _clean_fixture()
    clean_v = find_unresolved_constituents(clean_signals, clean_valid)
    if clean_v:
        print("[msr-ri] SELF-TEST FAIL: clean fixture produced violations:",
              file=sys.stderr)
        for v in clean_v:
            print(f"  {v.signal_id} {v.signal_type_id} unresolved={v.unresolved}",
                  file=sys.stderr)
        return 1

    mut_signals, mut_valid = _mutated_fixture()
    mut_v = find_unresolved_constituents(mut_signals, mut_valid)
    if not mut_v:
        print("[msr-ri] SELF-TEST FAIL: mutated fixture (one broken constituent) "
              "was NOT caught — the guard is inert.", file=sys.stderr)
        return 1

    print("[msr-ri] SELF-TEST PASS: clean fixture clean; mutated fixture caught "
          f"({len(mut_v)} violation(s), e.g. {mut_v[0].signal_type_id} "
          f"unresolved={mut_v[0].unresolved}).")
    return 0


# ---------------------------------------------------------------------------
# Live-DB mode (W3 verification)
# ---------------------------------------------------------------------------

def _run_db(chart_id: str | None) -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("[msr-ri] DATABASE_URL not set — cannot run live-DB mode. "
              "(Use --self-test for the DB-free CI gate.)", file=sys.stderr)
        return 2
    try:
        import psycopg  # psycopg3
    except ImportError:
        try:
            import psycopg2 as psycopg  # type: ignore
        except ImportError:
            print("[msr-ri] neither psycopg nor psycopg2 available.", file=sys.stderr)
            return 2

    where = "WHERE chart_id = %s" if chart_id else ""
    params: Sequence = (chart_id,) if chart_id else ()

    total_violations = 0
    with psycopg.connect(dsn) as conn:  # type: ignore[attr-defined]
        with conn.cursor() as cur:
            # valid fact_id set (optionally scoped to the chart)
            fid_where = "WHERE chart_id = %s" if chart_id else ""
            cur.execute(f"SELECT fact_id FROM chart_facts {fid_where}", params)
            valid_fact_ids = {str(r[0]) for r in cur.fetchall()}

            cur.execute(
                f"SELECT signal_id, signal_type_id, constituent_facts_array "
                f"FROM bodha_msr_signals {where}",
                params,
            )
            signals = [
                {"signal_id": r[0], "signal_type_id": r[1],
                 "constituent_facts_array": r[2]}
                for r in cur.fetchall()
            ]

    violations = find_unresolved_constituents(signals, valid_fact_ids)
    total_violations = len(violations)
    scope = f"chart {chart_id}" if chart_id else "ALL charts"
    if total_violations:
        print(f"[msr-ri] FAIL ({scope}): {total_violations} signal(s) cite "
              f"constituents that resolve to nothing (§N.5 break):", file=sys.stderr)
        for v in violations[:50]:
            print(f"  {v.signal_id} [{v.signal_type_id}] unresolved={v.unresolved}",
                  file=sys.stderr)
        if total_violations > 50:
            print(f"  … and {total_violations - 50} more.", file=sys.stderr)
        return 1

    print(f"[msr-ri] PASS ({scope}): {len(signals)} signals — "
          f"100% of constituent_facts_array entries resolve to chart_facts.fact_id.")
    return 0


# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="Run DB-free fixture self-test (the CI hard gate).")
    ap.add_argument("--chart-id", default=None,
                    help="Live-DB mode scoped to one chart_id (needs DATABASE_URL).")
    args = ap.parse_args(argv)

    if args.self_test:
        return _run_self_test()
    return _run_db(args.chart_id)


if __name__ == "__main__":
    sys.exit(main())
