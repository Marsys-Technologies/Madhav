#!/usr/bin/env python3
"""B3.8 — re-run baseline '3.0' under EVALUATION_PROTOCOL_v2_1 from the pinned extract.
Reads baseline_3_0_extract_v1_0.json (914 rows, IST dates, sha256 70ba6142... — NOT re-dumped).
Registry: EVENT_REGISTRY_v2_1.md (47 held-out = 30 timing-usable + 17 year-grain).
Changes vs rerun_3_0_v2_0_scorer.py (round-2 rework):
  * registry v2.1 (SPR.D restored; 2025.06/2025.11 month; 2026.01 interval)
  * T-cover month-grain = calendar-month overlap (any shared day); 15th proxy kept for T-time error only
  * T-rank: degeneracy exclusions BEFORE rank (two-horns + peak-diversity per class-year);
    signed-intensity ranking (si descending for gain and adverse alike — extract convention:
    adverse rows carry positive si, disclosed); ties average rank; eligible misses at percentile 100
  * T-FP: single estimand — all-observed-time admitted day-fraction adm/H vs budget 3*n_c*90/H
    (same denominator H both sides); the v2.0 negative-days mask is withdrawn (Codex R2-M02)
  * controls: interval events drawn at interval span (grandfather 61 d; 2026.01 59 d);
    randrange(0, H-span+1) inclusive fix; materialised to random_controls_v1_1.json (seed 482012)
Deterministic."""
import json, random, hashlib, datetime as dt, statistics as st
from collections import defaultdict

H0 = dt.date(1998,1,1); H1 = dt.date(2026,4,17)
H = (H1-H0).days + 1  # 10334
CAP = 182

doc = json.load(open("baseline_3_0_extract_v1_0.json"))
rows = doc["rows"]
assert len(rows) == 914
def D(s): return dt.date.fromisoformat(s)

# ---------- registry (from EVENT_REGISTRY_v2_1.md; hard-coded, disclosed — R2-M06: a
# machine-readable registry is a build-contract item, not a scorer fix for this pinned re-run)
HELD = [
 ("EVT.1998.02.16.01","romantic_start","exact","1998-02-16"),
 ("EVT.2001.03.XX.01","education_milestone","month","2001-03"),
 ("EVT.2003.06.XX.01","education_milestone","month","2003-06"),
 ("EVT.2004.01.XX.01","romantic_start","month","2004-01"),
 ("EVT.2007.06.XX.01","surgery","month","2007-06"),
 ("EVT.2007.06.XX.02","education_milestone","month","2007-06"),
 ("EVT.2007.06.10.01","career_entry","exact","2007-06-10"),
 ("EVT.2008.06.09.01","career_change","exact","2008-06-09"),
 ("EVT.2009.06.XX.01","bereavement","interval",("2009-06-01","2009-07-31")),
 ("EVT.2010.12.XX.01","travel_event","month","2010-12"),
 ("EVT.2011.01.XX.01","education_milestone","month","2011-01"),
 ("EVT.2011.06.XX.01","education_milestone","month","2011-06"),
 ("EVT.2012.09.XX.01","achievement_recognition","month","2012-09"),
 ("EVT.2012.10.XX.01","romantic_start","month","2012-10"),
 ("EVT.2013.03.XX.01","education_milestone","month","2013-03"),
 ("EVT.2013.05.XX.01","career_entry","month","2013-05"),
 ("EVT.2017.03.XX.01","career_change","month","2017-03"),
 ("EVT.2019.05.XX.01","foreign_settlement","month","2019-05"),
 ("EVT.2021.01.XX.01","illness_acute","month","2021-01"),
 ("EVT.2022.10.XX.01","separation","month","2022-10"),
 ("EVT.2023.05.XX.01","relocation","month","2023-05"),
 ("EVT.2023.06.XX.01","education_milestone","month","2023-06"),
 ("EVT.2023.07.XX.01","business_launch","month","2023-07"),
 ("EVT.2024.02.16.01","business_launch","exact","2024-02-16"),
 ("EVT.2025.05.XX.01","financial_deception","month","2025-05"),
 ("EVT.2025.06.XX.01","spiritual_turn","month","2025-06"),
 ("EVT.2025.07.XX.01","major_gain","month","2025-07"),
 ("EVT.2025.11.XX.01","spiritual_turn","month","2025-11"),
 ("EVT.2026.01.XX.01","psychological_arc","interval",("2026-01-01","2026-02-28")),
 ("EVT.2026.03.20.01","major_gain","exact","2026-03-20"),
 # year-grain
 ("EVT.1998.XX.XX.02","spiritual_turn","year",1998),
 ("EVT.2000.XX.XX.01","education_milestone","year",2000),
 ("EVT.2002.XX.XX.01","chronic_onset","year",2002),
 ("EVT.2002.XX.XX.02","spiritual_turn","year",2002),
 ("EVT.2004.XX.XX.02","education_milestone","year",2004),
 ("EVT.2007.XX.XX.03","chronic_onset","year",2007),
 ("EVT.2010.XX.XX.01","major_gain","year",2010),
 ("EVT.2010.XX.XX.02","spiritual_turn","year",2010),
 ("EVT.2012.XX.XX.02","achievement_recognition","year",2012),
 ("EVT.2013.XX.XX.01","parental_event","year",2013),
 ("EVT.2015.XX.XX.01","spiritual_turn","year",2015),
 ("EVT.2016.XX.XX.01","career_setback","year",2016),
 ("EVT.2021.XX.XX.02","education_milestone","year",2021),
 ("EVT.2021.XX.XX.03","property_acquisition","year",2021),
 ("EVT.2022.XX.XX.02","romantic_start","year",2022),
 ("EVT.2024.XX.XX.01","spiritual_turn","year",2024),
 ("EVT.2025.XX.XX.01","spiritual_turn","year",2025),
]
assert len(HELD)==47, len(HELD)
ADVERSE = ["bereavement","career_setback","chronic_onset","financial_deception",
           "illness_acute","parental_event","separation","surgery","major_loss"]

# ---------- dedup: merge overlapping/abutting same-class windows ----------
by_cls = defaultdict(list)
for r in rows:
    by_cls[r["event_class"]].append((D(r["ws"]), D(r["we"]), D(r["pk"]), float(r["si"])))
merged = {}
for c, ws in by_cls.items():
    ws.sort()
    cur=[]
    for w in ws:
        if cur and w[0] <= cur[-1][1] + dt.timedelta(days=1):
            p = cur[-1]
            pk, si = (w[2], w[3]) if w[3] > p[3] else (p[2], p[3])
            cur[-1] = (p[0], max(p[1], w[1]), pk, si)
        else:
            cur.append((w[0], w[1], w[2], w[3]))
    merged[c] = cur

# ---------- si sign-convention check (disclosed): adverse rows carry positive si ----------
adv_si = [w[3] for c in ADVERSE for w in merged.get(c,[])]
print(f"si convention: adverse-class merged candidates n={len(adv_si)}, "
      f"min si={min(adv_si) if adv_si else 'n/a'}, all>=0: {all(s>=0 for s in adv_si)} "
      f"→ ranking adverse by si descending (disclosed convention)")

def in_year(cls, y):
    lo, hi = dt.date(y,1,1), dt.date(y,12,31)
    return [w for w in merged.get(cls,[]) if w[0] <= hi and w[1] >= lo]

def month_span(y, m):
    lo = dt.date(y, m, 1)
    hi = dt.date(y + (m==12), m%12 + 1, 1) - dt.timedelta(days=1)
    return lo, hi

def ev_span(e):
    """the scored span of the event per grain (T-cover tests overlap with this span)"""
    if e[2]=="exact":
        d = D(e[3]); return d, d
    if e[2]=="month":
        y, m = map(int, e[3].split("-")); return month_span(y, m)
    if e[2]=="interval":
        return D(e[3][0]), D(e[3][1])
    y = e[3]; return dt.date(y,1,1), dt.date(y,12,31)

def ev_year(e):
    if e[2]=="year": return e[3]
    return ev_span(e)[0].year

def proxy_date(e):
    """error-proxy date: exact day, 15th of month, interval midpoint, July 1 of year"""
    if e[2]=="exact": return D(e[3])
    if e[2]=="month":
        y, m = map(int, e[3].split("-")); return dt.date(y, m, 15)
    if e[2]=="interval":
        lo, hi = D(e[3][0]), D(e[3][1]); return lo + (hi-lo)//2
    return dt.date(e[3],7,1)

def hit(e):
    """overlap per grain; returns (best overlapping window or None, N_in_year, rank_pct_or_None)"""
    cls = e[1]
    lo, hi = ev_span(e)
    cands = in_year(cls, ev_year(e))
    cont = [w for w in cands if w[0] <= hi and w[1] >= lo]
    N = len(cands)
    if not cont:
        return None, N, None
    ranked = sorted(cands, key=lambda w: -w[3])  # signed intensity, descending (both valences)
    tgt = max(cont, key=lambda w: w[3])
    si = tgt[3]
    ranks = [i+1 for i,w in enumerate(ranked) if abs(w[3]-si) < 1e-9]
    r = sum(ranks)/len(ranks)
    pct = 100.0*(r-1)/N
    return tgt, N, pct

def days_in(w):
    lo,hi = max(w[0],H0), min(w[1],H1)
    return max(0,(hi-lo).days+1)

# ---------- degeneracy (run BEFORE any endpoint) ----------
cls_list = sorted(merged)
base = {c: 100*sum(days_in(w) for w in merged[c])/H for c in cls_list}
horn = {c: ("high" if base[c] > 95 else "low" if base[c] < 0.5 else None) for c in cls_list}
same=0; pairs=0
for i in range(len(cls_list)):
    for j in range(i+1,len(cls_list)):
        pairs+=1
        if [(w[0],w[1]) for w in merged[cls_list[i]]] == [(w[0],w[1]) for w in merged[cls_list[j]]]:
            same+=1
era_indiscriminate = (100*same/pairs) >= 50
print(f"degeneracy: identical boundary class-pairs {same}/{pairs} = {100*same/pairs:.1f}% "
      f"→ era-fingerprint {'TRIPPED (class-indiscriminate; T-rank void)' if era_indiscriminate else 'clear'}")

def peak_diverse(cls, y):
    """v1.1 §B.1: <50% of in-year windows sharing one si value → diverse"""
    ws = in_year(cls, y)
    if not ws: return True
    from collections import Counter
    top = Counter(round(w[3],6) for w in ws).most_common(1)[0][1]
    return top/len(ws) < 0.5

# ---------- T-cover ----------
cover_hit, cover_miss, per_event = [], [], []
for e in HELD:
    w,N,pct = hit(e)
    (cover_hit if w else cover_miss).append(e[0])
    per_event.append({"eid":e[0],"cls":e[1],"grain":e[2],"N":N,"hit":bool(w),"pct":pct})
print(f"\nT-cover: {len(cover_hit)}/{len(HELD)} = {100*len(cover_hit)/len(HELD):.1f}%  misses={len(cover_miss)}")
for m in cover_miss: print("  MISS", m, [e[1] for e in HELD if e[0]==m][0])
inst_cls = ["education_milestone","career_change","business_launch","foreign_settlement","separation"]
inst = [p for p in per_event if p["cls"] in inst_cls]
print(f"instant classes: {sum(1 for p in inst if not p['hit'])}/{len(inst)} events miss; "
      f"hits: {[p['eid'] for p in inst if p['hit']]}")

# ---------- T-time (5 exact) ----------
errs, misses, uncapped = [], 0, []
for e in HELD:
    if e[2]!="exact": continue
    w,N,_ = hit(e)
    if w is None:
        errs.append(CAP); misses+=1
    else:
        err = abs((w[2]-proxy_date(e)).days)
        uncapped.append((e[0],err))
        errs.append(min(err,CAP))
print(f"\nT-time: capped median over {len(errs)} exact = {st.median(errs):.0f} d; misses={misses}; uncapped hits={uncapped}")

# ---------- T-rank (degeneracy exclusions before rank) ----------
timing = [p for p in per_event if p["grain"] in ("exact","month","interval")]
eligible, excluded = [], []
for p in timing:
    e = next(x for x in HELD if x[0]==p["eid"])
    if horn.get(p["cls"]):
        excluded.append((p["eid"], p["cls"], f"two-horns {horn[p['cls']]}")); continue
    if not peak_diverse(p["cls"], ev_year(e)):
        excluded.append((p["eid"], p["cls"], "peak-diversity")); continue
    if p["N"] >= 3:
        eligible.append(p)
pcts = [p["pct"] if p["pct"] is not None else 100.0 for p in eligible]
floor = len(timing)//2 + 1
print(f"\nT-rank: timing-usable {len(timing)} (floor {floor}); degenerate-excluded {len(excluded)}: {excluded}")
print(f"  events reaching N>=3 (post-dedup, non-degenerate): {len(eligible)} / {len(timing)}")
if len(eligible) >= floor:
    print(f"  median rank percentile = {st.median(pcts):.1f} (misses entered at 100)")
else:
    print("  RANK-UNPROVEN (below floor) — blocks the flip")

# ---------- base rates + T-FP (single estimand: admitted day-fraction adm/H) ----------
print("\nbase rates & T-FP (adverse classes; burden = admitted days / H; budget = 3*n_c*90/H):")
for c in ADVERSE:
    ws = merged.get(c,[])
    adm = sum(days_in(w) for w in ws)
    burden = 100*adm/H
    n_c = sum(1 for e in HELD if e[1]==c)
    budget = min(1.0, 3*max(n_c,1)*90/H)*100
    print(f"  {c:20s} base=burden={burden:6.2f}%  budget={budget:5.2f}%  {'PASS' if burden<=budget else 'FAIL'}")
print("gain-class base rates (two-horns 0.5–40%):")
high=low=ok=0
for c in cls_list:
    if c in ADVERSE: continue
    b = base[c]
    flag = "ok" if 0.5<=b<=40 else ("DEGENERATE-high" if b>95 else "DEGENERATE-low")
    high += flag=="DEGENERATE-high"; low += flag=="DEGENERATE-low"; ok += flag=="ok"
    print(f"  {c:24s} {b:6.2f}%  {flag}")
print(f"gain-class tally: {high} high / {low} low / {ok} in-band (of {len(cls_list)-len([c for c in cls_list if c in ADVERSE])} gain classes; all 27 classes incl. birth_anchor shown)")

# ---------- random controls (seed 482012, matched resolutions, materialised) ----------
rng = random.Random(482012)
ctrl = []
for e in HELD:
    lo, hi = ev_span(e)
    span = (hi-lo).days + 1
    hits_c = 0; dates=[]
    for _ in range(20):
        off = rng.randrange(0, H-span+1)
        cd = H0 + dt.timedelta(days=off)
        dates.append(cd.isoformat())
        chi = cd + dt.timedelta(days=span-1)
        if any(w[0] <= chi and w[1] >= cd for w in merged.get(e[1],[])):
            hits_c += 1
    ctrl.append({"eid":e[0],"cls":e[1],"span_days":span,"control_hits":hits_c,"dates":dates})
tot = sum(c["control_hits"] for c in ctrl)
print(f"\nrandom controls: {tot}/{20*len(HELD)} = {100*tot/(20*len(HELD)):.1f}% of control intervals admitted (diagnostic)")
json.dump({"seed":482012,"registry":"EVENT_REGISTRY_v2_1.md","controls":ctrl},
          open("random_controls_v1_1.json","w"), indent=1)
print("random_controls_v1_1.json sha256:", hashlib.sha256(open("random_controls_v1_1.json","rb").read()).hexdigest())
json.dump(per_event, open("rerun_per_event_v2_1.json","w"), indent=1)
