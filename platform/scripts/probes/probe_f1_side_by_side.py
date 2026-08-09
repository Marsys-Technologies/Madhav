#!/usr/bin/env python3
"""
probe_f1_side_by_side.py — F1 AMENDMENT CYCLE, Stage 2: the offline,
read-only side-by-side comparison of the v4.0 engine (amendments unset)
against the v4.1 variant (amendments={'F1'}, AMENDMENT_F1_SPEC_v1_0.md's
dispositor-conjunction exception), run against BOTH live canonical charts
(482012f1, 1c826d5a), all 27 `bo_pratijna_karyatva` classes.

This is the campaign's payoff artifact's raw data source. It prints a
per-chart, per-class table (occurrence/condition, v4.0 vs v4.1, deltas) and,
for every class where ANY cell moved, traces the exact dispositor-conjunction
factor-ledger entry that fired (graha, sign, D1 house, dispositor) so every
delta in F1_SIDE_BY_SIDE_v1_0.md is auditable astrology, not a diff.

R19: read-only. Never writes to any DB table, never writes to
`bo_pratijna_karyatva.py` or the v4 engine. R13: this probe is Stage 2, run
AFTER the amendment's engine implementation was already committed and
PARĪKṢAKA-reviewed (Stage 1) — no band/weight/rule was touched to shape
these numbers.

Usage: DBURL=postgresql://... python3 probe_f1_side_by_side.py [--json OUT]
"""
from __future__ import annotations

import argparse
import json
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


def get_dburl() -> str:
    if os.environ.get("DBURL"):
        return os.environ["DBURL"]
    raise SystemExit("DBURL not set — see probe_p1_identity.py header for the resolution one-liner.")


def f1_triggers(score) -> list[dict]:
    """Extract every factor_ledger entry where AMENDMENT F1 fired, for the
    auditable-trigger trace F1_SIDE_BY_SIDE_v1_0.md requires."""
    return [f for f in score.factor_ledger if "AMENDMENT F1" in (f.get("detail") or "")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=str, default=None, help="also write full raw comparison as JSON")
    args = ap.parse_args()

    dburl = get_dburl()
    conn = connect(dburl)
    all_rows: list[dict] = []

    try:
        for chart_label, chart_id in CHARTS.items():
            print(f"\n{'=' * 100}\nCHART {chart_label} ({chart_id})\n{'=' * 100}")
            reader_40 = ChartReaderV4(conn, ayanamsha=AYANAMSHA)
            reader_41 = ChartReaderV4(conn, ayanamsha=AYANAMSHA)
            engine_40 = PratijnaV4Engine(reader_40)
            engine_41 = PratijnaV4Engine(reader_41, amendments=frozenset({"F1"}))

            scores_40 = engine_40.score_all(chart_id)
            scores_41 = engine_41.score_all(chart_id)

            header = (
                f"{'class':<24}{'occ v4.0':<10}{'label v4.0':<14}{'occ v4.1':<10}{'label v4.1':<14}"
                f"{'Δocc':<9}{'cond v4.0':<11}{'cond v4.1':<11}{'Δcond':<8}{'moved'}"
            )
            print(header)
            moved_classes: list[str] = []

            for event_class_id in sorted(KARYATVA_REGISTRY):
                r40 = scores_40[event_class_id]
                r41 = scores_41[event_class_id]
                if r40.status != "scored" or r41.status != "scored":
                    print(f"{event_class_id:<24}NOT SCORED (status={r40.status}/{r41.status})")
                    continue

                d_occ = round(r41.occurrence - r40.occurrence, 6)
                d_cond = round(r41.condition - r40.condition, 6)
                moved = (d_occ != 0.0) or (d_cond != 0.0)
                band_crossed = r40.occurrence_label != r41.occurrence_label
                if moved:
                    moved_classes.append(event_class_id)

                print(
                    f"{event_class_id:<24}{r40.occurrence:<10}{r40.occurrence_label:<14}"
                    f"{r41.occurrence:<10}{r41.occurrence_label:<14}{d_occ:<9}"
                    f"{r40.condition:<11}{r41.condition:<11}{d_cond:<8}"
                    f"{'YES' + (' [BAND-CROSS]' if band_crossed else '') if moved else 'no'}"
                )

                triggers = f1_triggers(r41)
                row = {
                    "chart": chart_label,
                    "chart_id": chart_id,
                    "event_class_id": event_class_id,
                    "v40_occurrence": r40.occurrence,
                    "v40_occurrence_label": r40.occurrence_label,
                    "v41_occurrence": r41.occurrence,
                    "v41_occurrence_label": r41.occurrence_label,
                    "delta_occurrence": d_occ,
                    "band_crossed": band_crossed,
                    "v40_condition": r40.condition,
                    "v40_condition_label": r40.condition_label,
                    "v41_condition": r41.condition,
                    "v41_condition_label": r41.condition_label,
                    "delta_condition": d_cond,
                    "moved": moved,
                    "f1_triggers": [
                        {
                            "slot": t.get("slot"),
                            "graha": t.get("graha") or t.get("lord"),
                            "band_v41": t.get("band"),
                            "detail": t.get("detail"),
                        }
                        for t in triggers
                    ],
                }
                all_rows.append(row)

            print(f"\n-- {len(moved_classes)}/27 classes moved on {chart_label}: {sorted(moved_classes)}")
            unmoved = sorted(set(KARYATVA_REGISTRY) - set(moved_classes))
            print(f"-- {len(unmoved)}/27 classes UNMOVED (v4.0 == v4.1 exactly): {unmoved}")

            print(f"\n-- Trigger trace for moved classes on {chart_label}:")
            for row in all_rows:
                if row["chart"] != chart_label or not row["moved"]:
                    continue
                print(f"   {row['event_class_id']}:")
                if row["f1_triggers"]:
                    for t in row["f1_triggers"]:
                        print(f"      [{t['slot']}] {t['graha']}: {t['detail']}")
                else:
                    print(
                        "      (no F1 factor-ledger entry — moved via a downstream propagation, "
                        "e.g. a denial-config deduction whose input dignity changed; see denials in JSON)"
                    )

        print(f"\n{'=' * 100}\nDONE — {len(all_rows)} rows across {len(CHARTS)} charts x 27 classes.")
        if args.json:
            with open(args.json, "w") as fh:
                json.dump(all_rows, fh, indent=2, default=str)
            print(f"Raw comparison written to {args.json}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
