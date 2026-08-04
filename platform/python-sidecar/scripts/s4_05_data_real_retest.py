#!/usr/bin/env python3
"""
s4_05_data_real_retest.py — the DATA-REAL S4-05 re-test (ṢAḌ-DARŚANA registry
item 9, closes DP-4), staged so the gate chain can RUN it the moment
SESSION-A-SWEEP's ledger shows SWEEPS-COMPLETE.

────────────────────────────────────────────────────────────────────────────
WHY THIS SCRIPT EXISTS, AND WHY IT DID NOT EXIST BEFORE
────────────────────────────────────────────────────────────────────────────
Two S4-05 regression suites already exist and both PASS today:
  * `platform/python-sidecar/tests/l3/test_s4_05_health_adverse_class.py`
    — guards the GRAMMAR: the sweep's event-class universe now names a
    `health` domain (illness_acute / chronic_onset / surgery).
  * `platform-mcp/src/__tests__/s4_05_health_coverage.test.ts`
    — guards the SERVING LOGIC: `computeGocharaCoverage` only reports a class
    as covered when BOTH resonance targets exist AND the sweep has committed
    a substep for it — with `fetch` MOCKED, no live DB.

Both are CODE-closed. Neither can be DATA-closed, because until
SWEEPS-COMPLETE, `ka_gochara_sweep` has not actually run its widened grammar
(303→606 substeps/chart) against either canonical chart — a live query today
still returns honest-empty for health, which is CORRECT behaviour, not the
fix landing (`SHAD_DARSHANA_STATE.md` NEXT-ACTION / Night-4 morning report:
"S4-05 is code-closed, not data-closed — a live query today would still
return honest-empty for health windows"). This script is the missing THIRD
leg: it re-runs the exact `computeGocharaCoverage` SQL (mirrored verbatim
from `platform-mcp/src/tools/retrieval/register_gochara_windows.ts`, not
reinvented) against the REAL database, on BOTH canonical charts, and reports
whether the S4-05 defect is actually gone in production data — not just in
code.

────────────────────────────────────────────────────────────────────────────
THE ORIGINAL DEFECT, VERBATIM (so a PASS here is checked against the right
claim — provenance: `UAT_DARPANA_REGISTER_v1_0.md` §S4-05, the campaign's
one TRUST-BREAKING veto)
────────────────────────────────────────────────────────────────────────────
User query: "Is there a rough patch coming for my health in the near future?
I'd rather know than not know."
Instrument's answer (WRONG): "...on the health side it comes back clean —
no adverse window flagged across roughly the next three years."
Adversarial audit's veto reasoning, three-ways confirmed:
  (1) `kala_gochara_windows` modeled only {career_advancement, major_gain,
      marriage} — NO health event class existed at all. "Clean on health"
      reported a NULL CAPABILITY as an affirmative clearance.
  (2) The gochara valence=loss query returned empty WITH an explicit
      provenance warning ("an empty result is a coverage gap, not a negative
      signal") — the answer read that gap as an all-clear anyway.
  (3) `kala_windows` (the domain-capable instrument) was NOT clean: a
      health-tagged DOSHA activation existed (Ketu/Moon dasha window,
      2029-07-22→2030-02-20) that the gochara-only answer never surfaced.

Item 9 fixes (1) and, via `computeGocharaCoverage`'s two-axis covered
predicate, (2)'s SERVING-LAYER form (a class must be BOTH targeted AND
actually swept to count as covered — see the docstring at the top of
`register_gochara_windows.ts` for the "second door" this closes). This
script re-tests (1) and (2) against real data. (3) is a cross-check, run
best-effort: it looks for `kala_windows` health-domain rows near the
already-known 2029-2030 window so a genuine re-introduction of the original
incoherence (claims clean, `kala_windows` says otherwise) would be caught,
not just the coverage flag.

────────────────────────────────────────────────────────────────────────────
GATE THIS DISCHARGES
────────────────────────────────────────────────────────────────────────────
`SHAD_DARSHANA_BRIEF_v2_0.md` §3 Gate W3: "...health class passes the S4-05
re-test." `SHAD_DARSHANA_STATE.md` NEXT-ACTION: "S4-05 re-test on real data"
is step 1 of the gate chain, run BEFORE the field build / hash-replay /
weights-v0 / skill-score sequence — it does not depend on `ka_kshetra` or
`mi_bhara` at all, only on `ka_gochara_sweep` + `ka_gochara_resonance`
having actually run to completion for both charts (i.e. SWEEPS-COMPLETE).

READ-ONLY BY CONSTRUCTION. Every statement here is a SELECT; the connection
is opened `autocommit=True` and no write path exists in this module.
`kala_gochara_windows` data is untouchable (brief §7) and is only read.

────────────────────────────────────────────────────────────────────────────
USAGE (run this AFTER SESSION-A-SWEEP's ledger shows SWEEPS-COMPLETE; do
NOT run it as evidence before then — a pre-sweep run will legitimately
report FAIL/not-yet-covered and that is not a finding, it is the expected
honest-empty state the ledger already documents)
────────────────────────────────────────────────────────────────────────────
    DATABASE_URL=postgresql://... python3 scripts/s4_05_data_real_retest.py
    DATABASE_URL=postgresql://... python3 scripts/s4_05_data_real_retest.py --summary-only

Exit codes:
    0 — S4-05 PASSES on BOTH canonical charts (the gate clause is dischargeable)
    2 — S4-05 FAILS or is still honest-empty on at least one chart (gate blocks;
        this is the expected, correct result before SWEEPS-COMPLETE)
    3 — the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Both canonical charts (CLAUDE.md §B; SHAD_DARSHANA_BRIEF_v2_0.md §1: "both charts" always
# means these two, verified to identical coverage).
CANONICAL_CHARTS = {
    "482012f1": "482012f1-710e-4a25-994a-93821f5871aa",  # Abhisek Mohanty (native, primary)
    "1c826d5a": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",  # Abhinandan Mohanty (secondary canonical)
}

# The item-9 health domain, verbatim from migration 388's `brahma_event_ontology` seed and
# `services/gochara_grammar/event_class_scope.py`'s `HEALTH_ADVERSE_EVENT_CLASSES`. Not
# re-derived from a live query here so a corrupted ontology row can't silently redefine what
# this script is checking for.
HEALTH_EVENT_CLASSES = ("illness_acute", "chronic_onset", "surgery")

# Legacy classes that must remain swept — item 9 EXTENDS the grammar, it never narrows it
# (brief §7 rail; `kala_gochara_windows` data is untouchable).
LEGACY_EVENT_CLASSES = ("career_advancement", "major_gain", "marriage")


def _coverage_for_chart(cur: Any, chart_id: str) -> dict[str, Any]:
    """Mirrors `computeGocharaCoverage` (platform-mcp/src/tools/retrieval/
    register_gochara_windows.ts) EXACTLY — same three queries, same two-axis
    covered predicate (targeted AND swept). Reimplemented here rather than
    imported because the MCP side is TypeScript; the SQL below is copied
    verbatim, not re-derived, so this script tests the real served logic
    and not a python-side reinterpretation of it.
    """
    cur.execute(
        """SELECT DISTINCT rm.event_class AS event_class, eo.domain AS domain
             FROM gochara_resonance_map rm
             LEFT JOIN brahma_event_ontology eo ON eo.event_class_id = rm.event_class
            WHERE rm.chart_id = %s
            ORDER BY 1""",
        (chart_id,),
    )
    classes_rows = cur.fetchall()

    cur.execute("SELECT DISTINCT domain FROM brahma_event_ontology WHERE domain IS NOT NULL ORDER BY 1")
    universe_domains = sorted(r["domain"] for r in cur.fetchall())

    cur.execute(
        """SELECT COUNT(*)::int AS substeps_committed,
                  COALESCE(
                    ARRAY_AGG(DISTINCT split_part(substep_key, ':year:', 1))
                      FILTER (WHERE substep_key LIKE '%%:year:%%'),
                    ARRAY[]::text[]
                  ) AS swept_event_classes
             FROM build_substep_progress
            WHERE chart_id = %s AND asset_id = 'ka_gochara_sweep'""",
        (chart_id,),
    )
    substep_row = cur.fetchone() or {"substeps_committed": 0, "swept_event_classes": []}

    targeted_classes = sorted({r["event_class"] for r in classes_rows if r["event_class"]})
    swept_classes = set(substep_row["swept_event_classes"] or [])

    event_classes_covered = sorted(ec for ec in targeted_classes if ec in swept_classes)
    targeted_not_swept = sorted(ec for ec in targeted_classes if ec not in swept_classes)
    covered_domains = {
        r["domain"] for r in classes_rows if r["event_class"] in swept_classes and r["domain"]
    }
    domains_not_covered = sorted(d for d in universe_domains if d not in covered_domains)

    return {
        "event_classes_covered": event_classes_covered,
        "event_classes_targeted_not_swept": targeted_not_swept,
        "domains_not_covered": domains_not_covered,
        "sweep_completeness": {
            "substeps_committed": substep_row["substeps_committed"],
        },
    }


def _health_row_evidence(cur: Any, chart_id: str) -> dict[str, Any]:
    """Direct evidence (not derived from the coverage predicate): does
    `kala_gochara_windows` actually hold health-domain rows for this chart,
    and any adverse-valence rows in general? Informational — a chart can
    legitimately have zero health windows in its horizon (honest-empty is a
    real answer); what matters for the PASS predicate is that the domain is
    COMPUTED, not that it is non-empty.
    """
    cur.execute(
        """SELECT event_class, COUNT(*)::int AS n
             FROM kala_gochara_windows
            WHERE chart_id = %s AND event_class = ANY(%s)
            GROUP BY event_class
            ORDER BY event_class""",
        (chart_id, list(HEALTH_EVENT_CLASSES)),
    )
    health_rows_by_class = {r["event_class"]: r["n"] for r in cur.fetchall()}

    cur.execute(
        """SELECT event_class, COUNT(*)::int AS n
             FROM kala_gochara_windows
            WHERE chart_id = %s AND event_class = ANY(%s)
            GROUP BY event_class
            ORDER BY event_class""",
        (chart_id, list(LEGACY_EVENT_CLASSES)),
    )
    legacy_rows_by_class = {r["event_class"]: r["n"] for r in cur.fetchall()}

    return {
        "health_windows_by_class": health_rows_by_class,
        "health_windows_total": sum(health_rows_by_class.values()),
        "legacy_windows_by_class": legacy_rows_by_class,
        "legacy_windows_total": sum(legacy_rows_by_class.values()),
    }


def _kala_windows_health_crosscheck(cur: Any, chart_id: str) -> dict[str, Any]:
    """Best-effort cross-check against audit confirmation #3: does
    `kala_windows` (domain='health') show anything a 'clean' gochara-side
    answer would now contradict? This does not gate PASS/FAIL on its own —
    `kala_windows` covers a different (dasha/dosha-activation) surface with
    its own honest-empty semantics — it is reported as supporting evidence
    so a re-introduced cross-instrument incoherence (the ORIGINAL defect's
    exact shape) would be visible in the report, not silently missed.
    """
    try:
        cur.execute(
            """SELECT COUNT(*)::int AS n
                 FROM kala_windows
                WHERE chart_id = %s AND domain = 'health'""",
            (chart_id,),
        )
        row = cur.fetchone()
        return {"queried": True, "kala_windows_health_row_count": (row or {}).get("n", 0)}
    except Exception as exc:  # pragma: no cover — best-effort only, table/columns may differ
        return {"queried": False, "error": str(exc)}


def _verdict_for_chart(coverage: dict[str, Any]) -> dict[str, Any]:
    """The S4-05 re-test PASS predicate for one chart.

    PASS iff:
      (a) every item-9 health class is COVERED (targeted AND swept) — the
          grammar gap (audit confirmation #1) is closed with real data, and
      (b) 'health' is absent from `domains_not_covered` — the serving-layer
          "second door" (audit confirmation #2, the coverage attestation
          that would otherwise let a health question through as an
          all-clear before the health sweep has actually run) is closed.

    A chart still mid-sweep legitimately FAILS this — that is the correct,
    documented, honest-empty state, not a defect in this script.
    """
    covered = set(coverage["event_classes_covered"])
    missing_health = [ec for ec in HEALTH_EVENT_CLASSES if ec not in covered]
    health_domain_dark = "health" in coverage["domains_not_covered"]
    passed = not missing_health and not health_domain_dark
    return {
        "passed": passed,
        "missing_health_classes": missing_health,
        "health_domain_still_dark": health_domain_dark,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="print only the per-chart verdicts, not the full coverage/evidence payload",
    )
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg
        import psycopg.rows
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    report: dict[str, Any] = {"item": 9, "gate": "S4-05 data-real re-test", "charts": {}}
    all_passed = True

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            for short_id, chart_id in CANONICAL_CHARTS.items():
                coverage = _coverage_for_chart(cur, chart_id)
                evidence = _health_row_evidence(cur, chart_id)
                crosscheck = _kala_windows_health_crosscheck(cur, chart_id)
                verdict = _verdict_for_chart(coverage)
                all_passed = all_passed and verdict["passed"]

                chart_report: dict[str, Any] = {"chart_id": chart_id, "verdict": verdict}
                if not args.summary_only:
                    chart_report["coverage"] = coverage
                    chart_report["evidence"] = evidence
                    chart_report["kala_windows_crosscheck"] = crosscheck
                report["charts"][short_id] = chart_report

    report["overall_pass"] = all_passed
    print(json.dumps(report, indent=2, default=str))
    return 0 if all_passed else 2


if __name__ == "__main__":
    sys.exit(main())
