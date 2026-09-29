#!/usr/bin/env python3
"""B4.5 — re-run baseline '3.0' under EVALUATION_PROTOCOL_v2_2 from the pinned extract.
Reads baseline_3_0_extract_v1_0.json (914 rows, IST dates, sha256 70ba6142... — NOT re-dumped).
Registry: event_registry_v2_2.json (machine-readable — R2-M06; 47 held-out = 32 timing-usable
+ 15 year-grain; the two multi-year uncertainties are 730-day interval rows).
Changes vs rerun_3_0_v2_1_scorer.py (round-3 rework):
  * registry read from event_registry_v2_2.json (no hard-coded event table)
  * R3-P01: sign-convention adapter on RAW rows — any raw si < 0 => status INPUT_REJECTED,
    machine-readable stop (a diagnostic print is not an assertion). Raw valence domain is
    {gain, loss, mixed, neutral}; the protocol claim is on si sign, not valence labels.
  * R2-M04: merge representative = max si, ties -> earliest peak (stated in prose, protocol
    §4.2); ONE tie tolerance 1e-9 for ranking tie-groups AND the peak-diversity check
  * R2-M03: era_indiscriminate => t_rank.status = "VOID" in rerun_result_v2_2.json; no rank
    median is emitted as a result (diagnostic_only when printed); per-event records carry
    eligibility/void status
  * R2-M05: ONE control experiment — rolling spans at each event's own actual span length in
    days; domain randrange(0, H-span+1); any-shared-day overlap; unweighted; seed 482012;
    materialised random_controls_v1_2.json
  * R2-M01: registry counts validated against the JSON header; any mismatch triggers the
    source-reconciliation halt (documented diff, neither side presumed correct)
  * R2-M07: per-class pre/post-merge dedup table printed from the scorer's own merge block
Deterministic."""
import json, random, hashlib, datetime as dt, statistics as st
from collections import defaultdict, Counter

H0 = dt.date(1998,1,1); H1 = dt.date(2026,4,17)
H = (H1-H0).days + 1  # 10334
CAP = 182
TOL = 1e-9

result = {"artifact": "rerun_result", "version": "2.2", "protocol": "EVALUATION_PROTOCOL_v2_2",
          "registry": "event_registry_v2_2.json", "extract": "baseline_3_0_extract_v1_0.json",
          "extract_sha256": "70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff"}

doc = json.load(open("baseline_3_0_extract_v1_0.json"))
rows = doc["rows"]
assert len(rows) == 914
def D(s): return dt.date.fromisoformat(s)

# ---------- R3-P01: sign-convention adapter on RAW rows (before merging) ----------
raw_valences = Counter(r.get("valence") for r in rows)
bad = [r for r in rows if float(r["si"]) < 0]
print(f"input adapter: raw valence domain {dict(raw_valences)}; raw rows with si < 0: {len(bad)}")
if bad:
    result["input_adapter"] = {"status": "INPUT_REJECTED", "offending_rows": len(bad),
                               "examples": bad[:5]}
    json.dump(result, open("rerun_result_v2_2.json","w"), indent=1)
    raise SystemExit("INPUT_REJECTED: raw rows with si < 0 — see rerun_result_v2_2.json")
result["input_adapter"] = {"status": "PASS", "rule": "all raw si >= 0 (valence domain "
                           "{gain,loss,mixed,neutral} is descriptive; convention is on si sign)"}

# ---------- registry (machine-readable; validated against its header — R2-M01/R2-M06) ----------
reg = json.load(open("event_registry_v2_2.json"))
HELD_RAW = [e for e in reg["events"] if e["tier"] in ("held_out_timing","held_out_year")]
hdr = reg["conventions"]["counts"]
assert len(HELD_RAW) == hdr["held_out"] == 47, (len(HELD_RAW), hdr)
def ev_span(e):
    if e["grain"]=="exact": d=D(e["date"]); return d,d
    if e["grain"]=="month":
        y,m=map(int,e["date"].split("-"))
        lo=dt.date(y,m,1); hi=dt.date(y+(m==12),m%12+1,1)-dt.timedelta(days=1); return lo,hi
    if e["grain"]=="interval": return D(e["span"][0]), D(e["span"][1])
    y=int(e["date"]); return dt.date(y,1,1), dt.date(y,12,31)
n_timing = sum(1 for e in HELD_RAW if e["tier"]=="held_out_timing")
n_year   = sum(1 for e in HELD_RAW if e["tier"]=="held_out_year")
n_exact  = sum(1 for e in HELD_RAW if e["grain"]=="exact")
n_int    = sum(1 for e in HELD_RAW if e["grain"]=="interval")
recon = {"timing": (n_timing, hdr["held_out_timing"]), "year": (n_year, hdr["held_out_year"]),
         "exact": (n_exact, hdr["exact_cohort"]), "interval": (n_int, hdr["interval_grain"])}
print("source-reconciliation check (scorer-derived vs registry header):", recon)
if any(a != b for a,b in recon.values()):
    result["source_reconciliation"] = {"status": "MISMATCH", "detail": recon}
    json.dump(result, open("rerun_result_v2_2.json","w"), indent=1)
    raise SystemExit("SOURCE-RECONCILIATION HALT: scorer-derived counts differ from the "
                     "registry header — documented diff required (protocol §9.2)")
result["source_reconciliation"] = {"status": "MATCH", "detail": recon}
HELD = [(e["eid"], e["class"], e["grain"], e.get("date") or tuple(e["span"]), e["tier"]) for e in HELD_RAW]
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
            # merge representative: max si; ties -> earliest peak (protocol §4.2)
            if w[3] > p[3] + TOL: pk, si = w[2], w[3]
            elif abs(w[3]-p[3]) <= TOL: pk, si = min(p[2], w[2]), p[3]
            else: pk, si = p[2], p[3]
            cur[-1] = (p[0], max(p[1], w[1]), pk, si)
        else:
            cur.append((w[0], w[1], w[2], w[3]))
    merged[c] = cur

# ---------- R2-M07: dedup table from the scorer's own merge block ----------
print("\ndedup table (raw rows -> merged candidates, scorer's own merge):")
dedup_table = {c: [len(by_cls[c]), len(merged[c])] for c in sorted(by_cls)}
for c,(pre,post) in dedup_table.items():
    print(f"  {c:24s} {pre:4d} -> {post:3d}")
result["dedup_table"] = dedup_table

def in_year(cls, y):
    lo, hi = dt.date(y,1,1), dt.date(y,12,31)
    return [w for w in merged.get(cls,[]) if w[0] <= hi and w[1] >= lo]

def ev_year(e):
    return int(e[3]) if e[2]=="year" else ev_span_raw(e)[0].year
def ev_span_raw(e):
    src = next(x for x in HELD_RAW if x["eid"]==e[0])
    return ev_span(src)
def proxy_date(e):
    if e[2]=="exact": return D(e[3])
    if e[2]=="month":
        y,m = map(int, e[3].split("-")); return dt.date(y,m,15)
    if e[2]=="interval":
        lo,hi = D(e[3][0]), D(e[3][1]); return lo + (hi-lo)//2
    return dt.date(int(e[3]),7,1)

def hit(e):
    cls = e[1]
    lo, hi = ev_span_raw(e)
    cands = in_year(cls, ev_year(e))
    cont = [w for w in cands if w[0] <= hi and w[1] >= lo]
    N = len(cands)
    if not cont: return None, N, None
    ranked = sorted(cands, key=lambda w: -w[3])
    tgt = max(cont, key=lambda w: w[3])
    si = tgt[3]
    ranks = [i+1 for i,w in enumerate(ranked) if abs(w[3]-si) < TOL]
    r = sum(ranks)/len(ranks)
    return tgt, N, 100.0*(r-1)/N

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
print(f"\ndegeneracy: identical boundary class-pairs {same}/{pairs} = {100*same/pairs:.1f}% "
      f"→ era-fingerprint {'TRIPPED (class-indiscriminate; T-rank VOID — machine-readable)' if era_indiscriminate else 'clear'}")

def peak_diverse(cls, y):
    """protocol §8.3: <50% of in-year windows sharing one si value (1e-9 tolerance) → diverse"""
    ws = in_year(cls, y)
    if not ws: return True
    top = Counter(round(w[3],9) for w in ws).most_common(1)[0][1]
    return top/len(ws) < 0.5

# ---------- T-cover ----------
cover_hit, cover_miss, per_event = [], [], []
for e in HELD:
    w,N,pct = hit(e)
    (cover_hit if w else cover_miss).append(e[0])
    per_event.append({"eid":e[0],"cls":e[1],"grain":e[2],"tier":e[4],"N":N,"hit":bool(w),"pct":pct})
t_cover = {"hits": len(cover_hit), "total": len(HELD), "misses": cover_miss}
print(f"\nT-cover: {len(cover_hit)}/{len(HELD)} = {100*len(cover_hit)/len(HELD):.1f}%  misses={len(cover_miss)}")
for m in cover_miss: print("  MISS", m, [e[1] for e in HELD if e[0]==m][0])
inst_cls = ["education_milestone","career_change","business_launch","foreign_settlement","separation"]
inst = [p for p in per_event if p["cls"] in inst_cls]
print(f"instant classes: {sum(1 for p in inst if not p['hit'])}/{len(inst)} events miss; "
      f"hits: {[p['eid'] for p in inst if p['hit']]}")
t_cover["bar"] = "32/47"; t_cover["pass"] = len(cover_hit) >= 32

# ---------- T-time (5 exact) ----------
errs, misses, uncapped = [], 0, []
for e in HELD:
    if e[2]!="exact": continue
    w,N,_ = hit(e)
    if w is None: errs.append(CAP); misses+=1
    else:
        err = abs((w[2]-proxy_date(e)).days)
        uncapped.append((e[0],err)); errs.append(min(err,CAP))
t_time = {"capped_median_days": st.median(errs), "misses": misses, "uncapped_hits": uncapped,
          "n_exact": len(errs), "bar_days": 45, "pass": st.median(errs) <= 45}
print(f"\nT-time: capped median over {len(errs)} exact = {st.median(errs):.0f} d; misses={misses}; uncapped hits={uncapped}")

# ---------- T-rank (degeneracy exclusions before rank; machine-readable void) ----------
timing = [p for p in per_event if p["grain"] in ("exact","month","interval")]
eligible, excluded = [], []
for p in timing:
    e = next(x for x in HELD if x[0]==p["eid"])
    if era_indiscriminate:
        excluded.append((p["eid"], p["cls"], "era-fingerprint (generation-wide VOID)")); p["rank_status"]="void_era"; continue
    if horn.get(p["cls"]):
        excluded.append((p["eid"], p["cls"], f"two-horns {horn[p['cls']]}")); p["rank_status"]="excluded_two_horns"; continue
    if not peak_diverse(p["cls"], ev_year(e)):
        excluded.append((p["eid"], p["cls"], "peak-diversity")); p["rank_status"]="excluded_peak_diversity"; continue
    if p["N"] >= 3:
        eligible.append(p); p["rank_status"]="eligible"
    else:
        p["rank_status"]="ineligible_N_lt_3"
floor = len(timing)//2 + 1
print(f"\nT-rank: timing-usable {len(timing)} (floor {floor}); degenerate-excluded {len(excluded)}")
print(f"  events reaching N>=3 (post-dedup, non-degenerate): {len(eligible)} / {len(timing)}")
if era_indiscriminate:
    t_rank = {"status": "VOID", "reason": f"era-fingerprint {100*same/pairs:.1f}% >= 50%",
              "eligible": len(eligible), "floor": floor, "timing_usable": len(timing)}
    diag = [p["pct"] if p["pct"] is not None else 100.0 for p in timing if p["N"] and p["N"]>=1]
    print("  T-rank VOID (machine-readable) — no rank median emitted as a result")
    if diag: print(f"  [diagnostic_only] median of per-event percentiles over timing-usable with N>=1 = {st.median(diag):.1f}")
elif len(eligible) >= floor:
    pcts = [p["pct"] if p["pct"] is not None else 100.0 for p in eligible]
    t_rank = {"status": "VALID", "median_percentile": st.median(pcts), "bar": 25,
              "pass": st.median(pcts) <= 25, "eligible": len(eligible), "floor": floor}
    print(f"  median rank percentile = {st.median(pcts):.1f} (misses entered at 100)")
else:
    t_rank = {"status": "RANK-UNPROVEN", "eligible": len(eligible), "floor": floor,
              "blocks_flip": True}
    print("  RANK-UNPROVEN (below floor) — blocks the flip")

# ---------- base rates + T-FP ----------
print("\nbase rates & T-FP (adverse classes; burden = admitted days / H; budget = 3*n_c*90/H):")
t_fp = {}
for c in ADVERSE:
    ws = merged.get(c,[])
    adm = sum(days_in(w) for w in ws)
    burden = 100*adm/H
    n_c = sum(1 for e in HELD if e[1]==c)
    budget = min(1.0, 3*max(n_c,1)*90/H)*100
    t_fp[c] = {"burden_pct": round(burden,4), "budget_pct": round(budget,4), "pass": burden<=budget}
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
result["degeneracy"] = {"era_indiscriminate": era_indiscriminate, "identical_pairs": [same,pairs],
                        "two_horns": {c:v for c,v in horn.items() if v},
                        "gain_tally": {"high":high,"low":low,"ok":ok}}

# ---------- random controls (ONE frozen experiment; seed 482012; materialised v1_2) ----------
rng = random.Random(482012)
ctrl = []
for e in HELD:
    lo, hi = ev_span_raw(e)
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
json.dump({"seed":482012,"registry":"event_registry_v2_2.json",
           "experiment":"rolling spans at each event's own actual span length in days; domain "
                        "randrange(0, H-span+1) inclusive; any-shared-day overlap; unweighted",
           "controls":ctrl}, open("random_controls_v1_2.json","w"), indent=1)
print("random_controls_v1_2.json sha256:", hashlib.sha256(open("random_controls_v1_2.json","rb").read()).hexdigest())

# ---------- machine-readable result ----------
result.update({"t_cover": t_cover, "t_time": t_time, "t_rank": t_rank, "t_fp": t_fp,
               "t_honesty": {"status": "UNVERIFIABLE",
                             "reason": "no computation-coverage manifest exists for '3.0' "
                                       "(manifest is a build requirement for future generations)"},
               "random_controls": {"file": "random_controls_v1_2.json", "seed": 482012,
                                   "total_hits": tot, "total_draws": 20*len(HELD)},
               "per_event": per_event})
json.dump(result, open("rerun_result_v2_2.json","w"), indent=1)
json.dump(per_event, open("rerun_per_event_v2_2.json","w"), indent=1)
print("\nrerun_result_v2_2.json + rerun_per_event_v2_2.json written "
      f"(t_rank.status = {t_rank['status']})")
