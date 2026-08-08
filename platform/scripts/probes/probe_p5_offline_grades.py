#!/usr/bin/env python3
"""
probe_p5_offline_grades.py — PRATIJÑĀ v4 Proof Ladder, Rung P5 (the v4
engine LIBRARY acceptance gate — BLOCKING).

Per PRATIJNA_V4_STATE.md / MASTER_PLAN_v1_0.md §10: run the engine AS A
LIBRARY (no DB writes, no writer involved) against live chart 482012f1 AND
1c826d5a, print all 27 classes x occurrence/condition, and assert:

  1. No status monoculture (not every class returns the same occurrence
     band).
  2. No occurrence >= 0.95 without a cited near-maximal factor set (never
     silently produce an implausibly-perfect score).
  3. marriage != separation with genuinely distinct evidence (the exact
     defect v4 exists to fix) — occurrence AND condition both differ, AND
     the underlying karaka evidence differs, not just the final number.
  4. condition > 0 somewhere (the engine is not universally returning zero
     affliction).
  5. REPRODUCES RUNG_P3's hand-worked numbers EXACTLY: marriage 0.321/5.83,
     separation 0.505/8.75, childbirth 0.593/7.50.

R19: read-only. This probe never writes to any DB table.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
sys.path.insert(0, str(SIDECAR))

from brahmagyan.chart_reader_v4 import ChartReaderV4, connect  # noqa: E402
from pipeline.orchestrator.writers.bo_pratijna_karyatva import KARYATVA_REGISTRY  # noqa: E402
from pipeline.orchestrator.writers.bo_pratijna_v4_engine import PratijnaV4Engine  # noqa: E402

CHARTS = {
    "482012f1": "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
}
AYANAMSHA = "lahiri_chitrapaksha"

RUNG_P3_EXPECTED = {
    "marriage": (0.321, 5.83),
    "separation": (0.505, 8.75),
    "childbirth": (0.593, 7.50),
}


def get_dburl() -> str:
    if os.environ.get("DBURL"):
        return os.environ["DBURL"]
    raise SystemExit("DBURL not set — see probe_p1_identity.py header for the resolution one-liner.")


def main() -> int:
    dburl = get_dburl()
    conn = connect(dburl)
    overall_pass = True

    try:
        for chart_label, chart_id in CHARTS.items():
            print(f"\n{'=' * 70}\nCHART {chart_label} ({chart_id})\n{'=' * 70}")
            reader = ChartReaderV4(conn, ayanamsha=AYANAMSHA)
            engine = PratijnaV4Engine(reader)
            scores = engine.score_all(chart_id)

            print(f"{'class':<24}{'status':<12}{'occurrence':<12}{'occ_label':<14}{'condition':<12}{'cond_label'}")
            for event_class_id in sorted(scores):
                r = scores[event_class_id]
                if r.status != "scored":
                    print(f"{event_class_id:<24}{r.status:<12}{'-':<12}{'-':<14}{'-':<12}{'-'}")
                    continue
                print(
                    f"{event_class_id:<24}{r.status:<12}{r.occurrence:<12}{r.occurrence_label:<14}"
                    f"{r.condition:<12}{r.condition_label}"
                )

            occurrence_labels = {r.occurrence_label for r in scores.values() if r.status == "scored"}
            condition_labels = {r.condition_label for r in scores.values() if r.status == "scored"}

            # ── Assertion 1: no status monoculture ──────────────────────
            check1 = len(occurrence_labels) > 1
            print(f"\n[ASSERTION 1] No occurrence-band monoculture: "
                  f"{'PASS' if check1 else 'FAIL'} — distinct bands seen: {sorted(occurrence_labels)}")
            overall_pass &= check1

            # ── Assertion 2: no occurrence >= 0.95 without near-maximal cited factors ──
            near_perfect = [
                (ec, r) for ec, r in scores.items()
                if r.status == "scored" and r.occurrence is not None and r.occurrence >= 0.95
            ]
            check2 = True
            for ec, r in near_perfect:
                near_maximal = all(
                    (f.get("band") is None or f["band"] >= 0.80)
                    for f in r.factor_ledger
                    if f["slot"] in ("house_lord", "karaka", "divisional")
                )
                if not near_maximal:
                    check2 = False
                    print(f"  ! {ec} occurrence={r.occurrence} >= 0.95 WITHOUT a near-maximal cited factor set")
            print(f"[ASSERTION 2] No unsupported near-1.0 occurrence: "
                  f"{'PASS' if check2 else 'FAIL'} — {len(near_perfect)} class(es) >= 0.95 checked")
            overall_pass &= check2

            # ── Assertion 3: marriage != separation, genuinely distinct evidence ──
            marriage, separation = scores["marriage"], scores["separation"]
            occ_differ = marriage.occurrence != separation.occurrence
            cond_differ = marriage.condition != separation.condition
            m_karakas = {f["graha"] for f in marriage.factor_ledger if f["slot"] == "karaka"}
            s_karakas = {f["graha"] for f in separation.factor_ledger if f["slot"] == "karaka"}
            evidence_differs = m_karakas != s_karakas
            check3 = occ_differ and cond_differ and evidence_differs
            print(
                f"[ASSERTION 3] marriage != separation (genuinely distinct evidence): "
                f"{'PASS' if check3 else 'FAIL'} — "
                f"occ {marriage.occurrence} vs {separation.occurrence} (differ={occ_differ}), "
                f"cond {marriage.condition} vs {separation.condition} (differ={cond_differ}), "
                f"karakas {sorted(m_karakas)} vs {sorted(s_karakas)} (differ={evidence_differs})"
            )
            overall_pass &= check3

            # ── Assertion 4: condition > 0 somewhere ────────────────────
            any_condition_positive = any(
                r.condition is not None and r.condition > 0 for r in scores.values() if r.status == "scored"
            )
            print(f"[ASSERTION 4] condition > 0 somewhere: {'PASS' if any_condition_positive else 'FAIL'}")
            overall_pass &= any_condition_positive

            # ── Assertion 5: RUNG_P3 exact reproduction (this chart only) ──
            if chart_label == "482012f1":
                check5 = True
                for event_class_id, (exp_occ, exp_cond) in RUNG_P3_EXPECTED.items():
                    r = scores[event_class_id]
                    ok = (r.occurrence == exp_occ) and (r.condition == exp_cond)
                    print(
                        f"[ASSERTION 5] {event_class_id}: engine={r.occurrence}/{r.condition} "
                        f"vs RUNG_P3={exp_occ}/{exp_cond} — {'PASS' if ok else 'FAIL'}"
                    )
                    check5 &= ok
                overall_pass &= check5

        print(f"\n{'=' * 70}\nOVERALL: {'PASS' if overall_pass else 'FAIL'}\n{'=' * 70}")
        return 0 if overall_pass else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
