#!/usr/bin/env python3
"""
band_x2_old_vs_new.py -- offline old-vs-new for the I-28 band table and the X2 fallback, on STORED data.

Read-only and DB-free: it reads three JSON dumps made with SELECT-only queries as the read-only
reader (see BAND_X2_LANE_INTENT_v1_0.md section 7 for the exact queries) and imports the
writers' own functions. It writes nothing and connects to nothing.

    cd platform/python-sidecar
    PYTHONPATH=. python3 ../../00_ARCHITECTURE/briefs/suvarna/exec/band_x2/band_x2_old_vs_new.py \
        d_condition.json d_medical.json d_vastu.json

Reports, per chart:
  A. reproduction check: does the OLD function (re-implemented below from the pre-change source,
     ga_medical_writer.py / ga_vastu_writer.py at origin/main 925e96a5d) reproduce the stored labels?
  B. stored label -> NEW label transitions for ga_medical.indication_strength and
     ga_vastu_planet_direction_map.direction_impact, using today's stored condition_score
     (i.e. the effect of the band table ALONE, composite scores unchanged).
  C. X2 scenario: re-derive the composite from the STORED varga_dignity_spread with the writer's own
     (post-F-C8) functions. The reproduction on the canonical chart is the validity check; for the two
     fallback charts it gives the score the S-L1b rebuild would produce IF the divisional rows still
     match the stored spread. This is an OFFLINE REPRODUCTION, not a rebuild result.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from decimal import Decimal

from ga_writers import ga_condition_writer as cond
from ga_writers import ga_medical_writer as med
from ga_writers import ga_vastu_writer as vas

CHARTS = {
    "482012f1": "canonical 482012f1",
    "1c826d5a": "Abhinandan 1c826d5a",
    "cb73cd3d": "third cb73cd3d",
}


def old_medical(s):  # pre-I-28 ga_medical_writer.indication_strength_from_score
    if s is None:
        return "unknown"
    s = float(s)
    if s < 0.4:
        return "strong"
    if s <= 0.6:
        return "moderate"
    return "mild"


def old_vastu(s):  # pre-I-28 ga_vastu_writer.compute_direction_impact (NB: compares the raw Decimal)
    if s is None:
        return "neutral"
    s = Decimal(str(s)) if not isinstance(s, Decimal) else s
    if s < 0.4:
        return "weakened"
    if s < 0.7:
        return "neutral"
    return "strengthened"


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def key(r):
    return (r["chart_id"][:8], r["ayanamsha_id"], r["graha"])


def main(cond_p, med_p, vas_p):
    C, M, V = load(cond_p), load(med_p), load(vas_p)
    cscore = {key(r): r["condition_score"] for r in C}

    print("== counts: composite / medical / vastu rows per chart")
    for pre, name in CHARTS.items():
        print(f"  {name}: composite={sum(1 for r in C if r['chart_id'].startswith(pre))} "
              f"medical={sum(1 for r in M if r['chart_id'].startswith(pre))} "
              f"vastu={sum(1 for r in V if r['chart_id'].startswith(pre))}")

    print("\n== A. reproduction: OLD function over the stored composite score vs the STORED label")
    for label, rows, fn, field in (("ga_medical", M, old_medical, "indication_strength"),
                                   ("ga_vastu", V, old_vastu, "direction_impact")):
        bad = Counter()
        for r in rows:
            if fn(cscore.get(key(r))) != r[field]:
                bad[r["chart_id"][:8]] += 1
        print(f"  {label}: stored label != old function(score) on {sum(bad.values())} rows {dict(bad)}")
    vmis = 0
    for r in V:
        a, b = r["condition_score"], cscore.get(key(r))
        if (a is None) != (b is None) or (a is not None and abs(float(a) - float(b)) > 1e-9):
            vmis += 1
    print(f"  ga_vastu.condition_score copy differs from the composite score on {vmis} rows")

    print("\n== B. band table ALONE (stored scores unchanged): stored label -> NEW label")
    for label, rows, new_fn, field in (
            ("ga_medical.indication_strength", M, med.indication_strength_from_score, "indication_strength"),
            ("ga_vastu.direction_impact", V, vas.compute_direction_impact, "direction_impact")):
        print(f"  {label}")
        for pre, name in CHARTS.items():
            tr = Counter()
            changed = []
            for r in rows:
                if not r["chart_id"].startswith(pre):
                    continue
                new = new_fn(cscore.get(key(r)))
                tr[(r[field], new)] += 1
                if new != r[field]:
                    changed.append((r["ayanamsha_id"], r["graha"], cscore.get(key(r)), r[field], new))
            n_chg = sum(v for (a, b), v in tr.items() if a != b)
            print(f"    {name}: rows={sum(tr.values())} CHANGED={n_chg}  transitions="
                  + str({f'{a}->{b}': v for (a, b), v in sorted(tr.items()) if a != b}))
            for c in sorted(changed, key=str):
                print(f"        {c[0]:>26} {c[1]:<8} score={c[2]} {c[3]} -> {c[4]}")
        nulls = sum(1 for r in rows if cscore.get(key(r)) is None)
        print(f"    rows with a NULL composite score (the old vastu 'neutral' path): {nulls}")

    print("\n== C. X2 scenario: re-derive the composite from the STORED varga_dignity_spread")
    for pre, name in CHARTS.items():
        n = same = diff = skipped = 0
        band_chg = Counter()
        label_chg = Counter()
        for r in C:
            if not r["chart_id"].startswith(pre):
                continue
            n += 1
            bd = r["condition_score_breakdown"] or {}
            spread = r["varga_dignity_spread"]
            if not bd or "deeptaadi_state" not in bd or not spread:
                skipped += 1
                continue
            comp = cond._compute_varga_composite(spread)
            score, _ = cond.compute_condition_score_v1(
                dignity_score=float(r["dignity_score_d1"]) if r["dignity_score_d1"] is not None else None,
                deeptaadi=bd.get("deeptaadi_state"), baladi=bd.get("baladi_state"),
                is_combust=bool(r["is_combust"]), is_deeply_combust=bool(r["is_deeply_combust"]),
                is_retrograde=bool(r["is_retrograde"]), varga_score=comp)
            stored = float(r["condition_score"]) if r["condition_score"] is not None else None
            if score is not None and stored is not None and abs(score - stored) < 1e-6:
                same += 1
            else:
                diff += 1
                band_chg[(cond.score_band(stored), cond.score_band(score))] += 1
                label_chg[("medical", old_medical(stored), med.indication_strength_from_score(score))] += 1
                label_chg[("vastu", old_vastu(stored), vas.compute_direction_impact(score))] += 1
        print(f"  {name}: composite rows={n} reproduced-equal-to-stored={same} "
              f"score-would-change={diff} skipped={skipped}")
        if band_chg:
            print("     band changes (stored band -> re-derived band): "
                  + str({f'{a}->{b}': v for (a, b), v in sorted(band_chg.items(), key=str)}))
            print("     label changes vs STORED labels: "
                  + str({f'{k[0]}:{k[1]}->{k[2]}': v for k, v in sorted(label_chg.items()) if k[1] != k[2]}))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
