#!/usr/bin/env python3
"""B3.6 — re-run baseline '3.0' under EVALUATION_PROTOCOL_v2_0 from the pinned extract.
Reads baseline_3_0_extract_v1_0.json (914 rows, IST dates). Registry: EVENT_REGISTRY_v2_0.md.
Deterministic; random controls use seed 482012 and are materialised to random_controls_v1_0.json."""
import json, random, hashlib, datetime as dt, statistics as st
from collections import defaultdict

H0 = dt.date(1998,1,1); H1 = dt.date(2026,4,17)
H = (H1-H0).days + 1  # 10334
CAP = 182

doc = json.load(open("baseline_3_0_extract_v1_0.json"))
rows = doc["rows"]
assert len(rows) == 914
def D(s): return dt.date.fromisoformat(s)

# ---------- registry (from EVENT_REGISTRY_v2_0.md) ----------
# (eid, cls, grain, date-or-(lo,hi))
HELD = [
 ("EVT.1998.02.16.01","romantic_start","exact","1998-02-16"),
 ("EVT.2001.03.XX.01","education_milestone","month","2001-03-15"),
 ("EVT.2003.06.XX.01","education_milestone","month","2003-06-15"),
 ("EVT.2004.01.XX.01","romantic_start","month","2004-01-15"),
 ("EVT.2007.06.XX.01","surgery","month","2007-06-15"),
 ("EVT.2007.06.XX.02","education_milestone","month","2007-06-15"),
 ("EVT.2007.06.10.01","career_entry","exact","2007-06-10"),
 ("EVT.2008.06.09.01","career_change","exact","2008-06-09"),
 ("EVT.2009.06.XX.01","bereavement","interval",("2009-06-01","2009-07-31")),
 ("EVT.2010.12.XX.01","travel_event","month","2010-12-15"),
 ("EVT.2011.01.XX.01","education_milestone","month","2011-01-15"),
 ("EVT.2011.06.XX.01","education_milestone","month","2011-06-15"),
 ("EVT.2012.09.XX.01","achievement_recognition","month","2012-09-15"),
 ("EVT.2012.10.XX.01","romantic_start","month","2012-10-15"),
 ("EVT.2013.03.XX.01","education_milestone","month","2013-03-15"),
 ("EVT.2013.05.XX.01","career_entry","month","2013-05-15"),
 ("EVT.2017.03.XX.01","career_change","month","2017-03-15"),
 ("EVT.2019.05.XX.01","foreign_settlement","month","2019-05-15"),
 ("EVT.2021.01.XX.01","illness_acute","month","2021-01-15"),
 ("EVT.2022.10.XX.01","separation","month","2022-10-15"),
 ("EVT.2023.05.XX.01","relocation","month","2023-05-15"),
 ("EVT.2023.06.XX.01","education_milestone","month","2023-06-15"),
 ("EVT.2023.07.XX.01","business_launch","month","2023-07-15"),
 ("EVT.2024.02.16.01","business_launch","exact","2024-02-16"),
 ("EVT.2025.05.XX.01","financial_deception","month","2025-05-15"),
 ("EVT.2025.07.XX.01","major_gain","month","2025-07-15"),
 ("EVT.2026.03.20.01","major_gain","exact","2026-03-20"),
 # year-grain
 ("EVT.1998.XX.XX.02","spiritual_turn","year","1998-07-01"),
 ("EVT.2000.XX.XX.01","education_milestone","year","2000-07-01"),
 ("EVT.2002.XX.XX.01","chronic_onset","year","2002-07-01"),
 ("EVT.2002.XX.XX.02","spiritual_turn","year","2002-07-01"),
 ("EVT.2004.XX.XX.02","education_milestone","year","2004-07-01"),
 ("EVT.2007.XX.XX.03","chronic_onset","year","2007-07-01"),
 ("EVT.2010.XX.XX.01","major_gain","year","2010-07-01"),
 ("EVT.2010.XX.XX.02","spiritual_turn","year","2010-07-01"),
 ("EVT.2012.XX.XX.02","achievement_recognition","year","2012-07-01"),
 ("EVT.2013.XX.XX.01","parental_event","year","2013-07-01"),
 ("EVT.2016.XX.XX.01","career_setback","year","2016-07-01"),
 ("EVT.2021.XX.XX.02","education_milestone","year","2021-07-01"),
 ("EVT.2021.XX.XX.03","property_acquisition","year","2021-07-01"),
 ("EVT.2022.XX.XX.02","romantic_start","year","2022-07-01"),
 ("EVT.2024.XX.XX.01","spiritual_turn","year","2024-07-01"),
 ("EVT.2025.06.XX.01","spiritual_turn","year","2025-07-01"),
 ("EVT.2025.11.XX.01","spiritual_turn","year","2025-11-15"),
 ("EVT.2025.XX.XX.01","spiritual_turn","year","2025-07-01"),
 ("EVT.2026.01.XX.01","psychological_arc","year","2026-01-15"),
]
assert len(HELD)==46
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
            pk, si = (w[2], w[3]) if abs(w[3]) > abs(p[3]) else (p[2], p[3])
            cur[-1] = (p[0], max(p[1], w[1]), pk, si)
        else:
            cur.append(list(w) if False else (w[0], w[1], w[2], w[3]))
    merged[c] = cur

def containing(cls, d):
    return [w for w in merged.get(cls,[]) if w[0] <= d <= w[1]]

def in_year(cls, y):
    lo, hi = dt.date(y,1,1), dt.date(y,12,31)
    return [w for w in merged.get(cls,[]) if w[0] <= hi and w[1] >= lo]

def evdate(e):
    if e[2]=="interval": return D(e[3][0])
    return D(e[3])

def hit(e):
    """containing window per grain; returns (window or None, N_in_year, rank_pct_or_None)"""
    cls, grain = e[1], e[2]
    if grain=="interval":
        lo,hi = D(e[3][0]), D(e[3][1])
        cands = [w for w in merged.get(cls,[]) if w[0] <= hi and w[1] >= lo]
        cont = [w for w in cands if w[0] <= hi and w[1] >= lo]
    elif grain=="year":
        y = evdate(e).year
        cands = in_year(cls, y)
        cont = cands  # year overlap = containing for year grain
    else:
        d = evdate(e)
        cands = in_year(cls, d.year)
        cont = [w for w in cands if w[0] <= d <= w[1]]
    N = len(cands)
    if not cont:
        return None, N, None
    ranked = sorted(cands, key=lambda w:-abs(w[3]))
    # average rank for ties
    tgt = max(cont, key=lambda w: abs(w[3]))  # best containing window
    si = abs(tgt[3])
    ranks = [i+1 for i,w in enumerate(ranked) if abs(abs(w[3])-si) < 1e-9]
    r = sum(ranks)/len(ranks)
    pct = 100.0*(r-1)/N
    return tgt, N, pct

# ---------- T-cover ----------
cover_hit, cover_miss = [], []
per_event = []
for e in HELD:
    w,N,pct = hit(e)
    (cover_hit if w else cover_miss).append(e[0])
    per_event.append({"eid":e[0],"cls":e[1],"grain":e[2],"N":N,"hit":bool(w),"pct":pct})
print(f"T-cover: {len(cover_hit)}/{len(HELD)} = {100*len(cover_hit)/len(HELD):.1f}%  misses={len(cover_miss)}")
for m in cover_miss: print("  MISS", m, [e[1] for e in HELD if e[0]==m][0])

# ---------- T-time (5 exact) ----------
errs, misses, uncapped = [], 0, []
for e in HELD:
    if e[2]!="exact": continue
    w,N,_ = hit(e)
    if w is None:
        errs.append(CAP); misses+=1
    else:
        err = abs((w[2]-evdate(e)).days)
        uncapped.append((e[0],err))
        errs.append(min(err,CAP))
print(f"T-time: capped median over {len(errs)} exact = {st.median(errs):.0f} d; misses={misses}; uncapped hits={uncapped}")

# ---------- T-rank ----------
timing = [p for p in per_event if p["grain"] in ("exact","month","interval")]
eligible = [p for p in timing if p["N"]>=3]
pcts = [p["pct"] if p["pct"] is not None else 100.0 for p in eligible]
print(f"T-rank: events reaching N>=3 (post-dedup): {len(eligible)} / 27 (floor 14)")
if eligible:
    print(f"  median rank percentile = {st.median(pcts):.1f}")
else:
    print("  RANK-UNPROVEN (no eligible events)")

# ---------- degeneracy: era-boundary fingerprint ----------
cls_list = sorted(merged)
same=0; pairs=0
for i in range(len(cls_list)):
    for j in range(i+1,len(cls_list)):
        a=[(w[0],w[1]) for w in merged[cls_list[i]]]
        b=[(w[0],w[1]) for w in merged[cls_list[j]]]
        pairs+=1
        if a==b: same+=1
print(f"degeneracy: identical boundary class-pairs {same}/{pairs} = {100*same/pairs:.1f}%")

# ---------- base rates + T-FP ----------
def days_in(w):
    lo,hi = max(w[0],H0), min(w[1],H1)
    return max(0,(hi-lo).days+1)
print("\nbase rates & T-FP (adverse classes):")
tfp = {}
for c in ADVERSE:
    ws = merged.get(c,[])
    adm = sum(days_in(w) for w in ws)
    # hit days: days of true events of class c covered by a containing window (approx: 1 day per hit event)
    evs = [e for e in HELD if e[1]==c]
    hitdays = sum(1 for e in evs if hit(e)[0])
    neg = H - hitdays
    burden = max(0, adm - hitdays)/neg*100
    n_c = len(evs)
    budget = min(1.0, 3*max(n_c,1)*90/H)*100
    tfp[c]=(100*adm/H, burden, budget)
    print(f"  {c:20s} base={100*adm/H:6.2f}%  burden={burden:6.2f}%  budget={budget:5.2f}%  {'PASS' if burden<=budget else 'FAIL'}")
gainbase = {c:100*sum(days_in(w) for w in merged.get(c,[]))/H for c in cls_list if c not in ADVERSE}
print("gain-class base rates (two-horns 0.5–40%):")
for c,b in sorted(gainbase.items()):
    flag = "ok" if 0.5<=b<=40 else "DEGENERATE"
    print(f"  {c:24s} {b:6.2f}%  {flag}")

# ---------- random controls (seed 482012, materialised) ----------
rng = random.Random(482012)
ctrl = []
for e in HELD:
    d0 = evdate(e)
    span = 1 if e[2]=="exact" else 30 if e[2]=="month" else 365
    hits_c = 0
    dates=[]
    for _ in range(20):
        off = rng.randrange(0, H-span)
        cd = H0 + dt.timedelta(days=off)
        dates.append(cd.isoformat())
        lo, hi = cd, cd+dt.timedelta(days=span-1)
        if any(w[0] <= hi and w[1] >= lo for w in merged.get(e[1],[])):
            hits_c += 1
    ctrl.append({"eid":e[0],"cls":e[1],"span_days":span,"control_hits":hits_c,"dates":dates})
tot = sum(c["control_hits"] for c in ctrl)
print(f"\nrandom controls: {tot}/{20*len(HELD)} = {100*tot/(20*len(HELD)):.1f}% of control intervals admitted (diagnostic)")
json.dump({"seed":482012,"controls":ctrl}, open("random_controls_v1_0.json","w"), indent=1)
h = hashlib.sha256(open("random_controls_v1_0.json","rb").read()).hexdigest()
print("random_controls_v1_0.json sha256:", h)
json.dump(per_event, open("rerun_per_event_v1_0.json","w"), indent=1)
