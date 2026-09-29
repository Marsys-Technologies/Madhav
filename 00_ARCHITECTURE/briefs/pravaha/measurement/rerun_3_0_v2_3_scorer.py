#!/usr/bin/env python3
"""B4.5b — re-run baseline '3.0' under EVALUATION_PROTOCOL_v2_3 (D-PROTO conditions 1-5).
Reads baseline_3_0_extract_v1_0.json (914 rows, IST dates, sha256 70ba6142... — NOT re-dumped).
Registry: event_registry_v2_3.json (machine-readable; 47 held-out = 32 timing-usable
+ 15 year-grain; the two multi-year uncertainties are 731/730-day interval rows).
Changes vs rerun_3_0_v2_2_scorer.py (D-PROTO_DECISION_v1_0 §6 conditions 1-5):
  * C4: extract sha256 COMPUTED at load and compared to the declared pin (INPUT_REJECTED on
    mismatch — measured, not asserted); extract classes validated against the 27-class
    universe (INPUT_REJECTED on any unknown class)
  * C2: candidate set = merged windows of the event's class overlapping the calendar years
    its scored span touches, clipped to the observation mask — one set for N, hit and rank
    (changes only the two two-year rows and the two 2026 rows; '3.0' figures must not move)
  * C1: gain-class 0.5-40% band ENFORCED — t_fp_gain block with burden_pct/pass for every
    non-adverse, non-anchor class with scored rows; generation T-FP verdict requires every
    adverse AND every gain entry to pass; band-label logic fixed (F8)
  * C3: t_honesty carries pass=false whenever status is not PASS; consequences in prose
  * C5: peak-diversity uses the SAME 1e-9 grouping as ranking (sorted values, cut at gaps
    >= 1e-9) instead of round(.,9) bucketing
v2.2 changes (retained):
  * registry read from the machine-readable registry JSON (no hard-coded event table)
  * R3-P01: sign-convention adapter on RAW rows — any raw si < 0 => status INPUT_REJECTED,
    machine-readable stop (a diagnostic print is not an assertion). Raw valence domain is
    {gain, loss, mixed, neutral}; the protocol claim is on si sign, not valence labels.
  * R2-M04: merge representative = max si, ties -> earliest peak (stated in prose, protocol
    §4.2); ONE tie tolerance 1e-9 for ranking tie-groups AND the peak-diversity check
  * R2-M03: era_indiscriminate => t_rank.status = "VOID" in the result file; no rank
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

PIN_SHA = "70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff"
CLASSES_27 = ["achievement_recognition","bereavement","birth_anchor","business_launch",
 "career_advancement","career_change","career_entry","career_setback","childbirth",
 "chronic_onset","education_milestone","exam_outcome","financial_deception",
 "foreign_settlement","illness_acute","major_gain","major_loss","marriage","parental_event",
 "property_acquisition","psychological_arc","relocation","romantic_start","separation",
 "spiritual_turn","surgery","travel_event"]
result = {"artifact": "rerun_result", "version": "2.3", "protocol": "EVALUATION_PROTOCOL_v2_3",
          "decision": "decisions/D-PROTO_DECISION_v1_0.md (ACCEPT_WITH_CONDITIONS)",
          "registry": "event_registry_v2_3.json", "extract": "baseline_3_0_extract_v1_0.json"}

raw_bytes = open("baseline_3_0_extract_v1_0.json","rb").read()
measured_sha = hashlib.sha256(raw_bytes).hexdigest()
result["extract_sha256"] = {"declared_pin": PIN_SHA, "measured": measured_sha,
                            "match": measured_sha == PIN_SHA}
print(f"extract integrity: measured sha256 {measured_sha[:16]}… == declared pin: {measured_sha == PIN_SHA}")
if measured_sha != PIN_SHA:
    result["input_adapter"] = {"status": "INPUT_REJECTED",
                               "reason": "extract sha256 differs from the declared pin"}
    json.dump(result, open("rerun_result_v2_3.json","w"), indent=1)
    raise SystemExit("INPUT_REJECTED: extract hash mismatch — see rerun_result_v2_3.json")

doc = json.loads(raw_bytes)
rows = doc["rows"]
assert len(rows) == 914
unknown_cls = sorted({r["event_class"] for r in rows} - set(CLASSES_27))
print(f"class-universe check: extract classes ⊆ 27-class table: {not unknown_cls} {unknown_cls or ''}")
if unknown_cls:
    result["input_adapter"] = {"status": "INPUT_REJECTED",
                               "reason": f"extract classes outside the 27-class universe: {unknown_cls}"}
    json.dump(result, open("rerun_result_v2_3.json","w"), indent=1)
    raise SystemExit("INPUT_REJECTED: unknown class — see rerun_result_v2_3.json")
def D(s): return dt.date.fromisoformat(s)

# ---------- R3-P01: sign-convention adapter on RAW rows (before merging) ----------
raw_valences = Counter(r.get("valence") for r in rows)
bad = [r for r in rows if float(r["si"]) < 0]
print(f"input adapter: raw valence domain {dict(raw_valences)}; raw rows with si < 0: {len(bad)}")
if bad:
    result["input_adapter"] = {"status": "INPUT_REJECTED", "offending_rows": len(bad),
                               "examples": bad[:5]}
    json.dump(result, open("rerun_result_v2_3.json","w"), indent=1)
    raise SystemExit("INPUT_REJECTED: raw rows with si < 0 — see rerun_result_v2_3.json")
result["input_adapter"] = {"status": "PASS", "rule": "all raw si >= 0 (valence domain "
                           "{gain,loss,mixed,neutral} is descriptive; convention is on si sign)"}

# ---------- registry (machine-readable; validated against its header — R2-M01/R2-M06) ----------
reg = json.load(open("event_registry_v2_3.json"))
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
    json.dump(result, open("rerun_result_v2_3.json","w"), indent=1)
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

def cand_set(e):
    """C2: merged windows of the event's class overlapping the calendar years its scored
    span touches, clipped to the observation mask [H0, H1]. One set for N, hit and rank."""
    cls = e[1]
    lo, hi = ev_span_raw(e)
    years = range(lo.year, hi.year + 1)
    out = []
    for y in years:
        out.extend(in_year(cls, y))
    seen = set(); uniq = []
    for w in out:
        if w not in seen: seen.add(w); uniq.append(w)
    return [w for w in uniq if w[1] >= H0 and w[0] <= H1]  # mask clip (drops fully post-mask rows)

def hit(e):
    lo, hi = ev_span_raw(e)
    cands = cand_set(e)
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
    """protocol §8.3: <50% of in-year windows sharing one si value → diverse. Same 1e-9
    grouping as ranking (C5): sort si, cut groups at gaps >= 1e-9, largest group is the plateau."""
    ws = in_year(cls, y)
    if not ws: return True
    vals = sorted(w[3] for w in ws)
    groups, cur = 1, 1
    best = 1
    for a, b in zip(vals, vals[1:]):
        cur = cur + 1 if abs(b-a) < TOL else 1
        best = max(best, cur)
    return best/len(ws) < 0.5

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
print("gain-class base rates (band 0.5–40% ENFORCED — C1):")
t_fp_gain = {}
high=low=ok=0
for c in cls_list:
    if c in ADVERSE or c == "birth_anchor": continue
    b = base[c]
    flag = "ok" if 0.5<=b<=40 else ("out-of-band-high" if b>40 else "out-of-band-low")
    high += flag=="out-of-band-high"; low += flag=="out-of-band-low"; ok += flag=="ok"
    t_fp_gain[c] = {"burden_pct": round(b,4), "band": "0.5-40%", "pass": 0.5<=b<=40}
    print(f"  {c:24s} {b:6.2f}%  {flag}  {'PASS' if flag=='ok' else 'FAIL'}")
print(f"gain-class tally: {high} high / {low} low / {ok} in-band (of {len(t_fp_gain)} non-adverse, "
      f"non-anchor classes with scored rows; birth_anchor excluded from all endpoints)")
t_fp_overall = all(v["pass"] for v in t_fp.values()) and all(v["pass"] for v in t_fp_gain.values())
print(f"T-FP generation verdict (every adverse AND every gain entry must pass — C1): {'PASS' if t_fp_overall else 'FAIL'}")
result["degeneracy"] = {"era_indiscriminate": era_indiscriminate, "identical_pairs": [same,pairs],
                        "two_horns": {c:v for c,v in horn.items() if v},
                        "gain_tally": {"high":high,"low":low,"ok":ok}}
result["t_fp_gain"] = t_fp_gain
result["t_fp_overall"] = {"pass": t_fp_overall,
                          "rule": "every adverse entry (t_fp) AND every gain entry (t_fp_gain) must pass"}

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
json.dump({"seed":482012,"registry":"event_registry_v2_3.json",
           "experiment":"rolling spans at each event's own actual span length in days; domain "
                        "randrange(0, H-span+1) inclusive; any-shared-day overlap; unweighted",
           "controls":ctrl}, open("random_controls_v1_3.json","w"), indent=1)
print("random_controls_v1_3.json sha256:", hashlib.sha256(open("random_controls_v1_3.json","rb").read()).hexdigest())
assert tot == 638, f"controls moved: {tot} != 638 — STOP and report (figures must not move)"

# ---------- machine-readable result ----------
result.update({"t_cover": t_cover, "t_time": t_time, "t_rank": t_rank, "t_fp": t_fp,
               "t_honesty": {"status": "UNVERIFIABLE", "pass": False,
                             "consequence": "UNVERIFIABLE on a candidate generation means not "
                                            "flip-eligible (protocol v2.3 §6.5b)",
                             "reason": "no computation-coverage manifest exists for '3.0' "
                                       "(manifest is a build requirement for future generations)"},
               "random_controls": {"file": "random_controls_v1_3.json", "seed": 482012,
                                   "total_hits": tot, "total_draws": 20*len(HELD)},
               "per_event": per_event})
json.dump(result, open("rerun_result_v2_3.json","w"), indent=1)
json.dump(per_event, open("rerun_per_event_v2_3.json","w"), indent=1)
print("\nrerun_result_v2_3.json + rerun_per_event_v2_3.json written "
      f"(t_rank.status = {t_rank['status']}, t_fp_overall.pass = {t_fp_overall})")
