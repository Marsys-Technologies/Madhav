"""A1 — control-matching check (analysis-only, no rebuild, no re-run of the gate).
Re-scores the EXISTING §G run's saved data (lel_events.json, pooled_activations.json)
with the shuffled-birth control constrained to identical coverage and identical
scorable-event N as the real chart run. Reuses score_g.py's exact scoring functions
verbatim (imported, not reimplemented) so the algorithm is unchanged -- only the
event subset changes.
"""
import json, sys
sys.path.insert(0, "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/d6aa9c91-2f4f-4044-8214-8432b8934686/scratchpad")
import score_g as SG

SCR = SG.SCR
events = json.load(open(f"{SCR}/lel_events.json"))
activations = json.load(open(f"{SCR}/pooled_activations.json"))

scorable, excluded = [], []
for e in events:
    ok, reasons = SG.classify_scorability(e)
    (scorable if ok else excluded).append({**e, "reasons": reasons})

COVERAGE_START = "2010-08-18"
COVERAGE_END = "2032-07-01"

blind_inputs_all = []
for e in scorable:
    catdom = SG.CATEGORY_TO_DOMAIN.get(e["category"], "general")
    served_domain = SG.CATDOM_TO_SERVED.get(catdom, None)
    blind_inputs_all.append({"event_id": e["event_id"], "date": SG.parse(e["event_date"]),
                              "served_domain": served_domain, "category": e["category"],
                              "event_date_str": e["event_date"]})

blind_inputs_covered = [b for b in blind_inputs_all if COVERAGE_START <= b["event_date_str"] < COVERAGE_END]

print(f"ALL scorable N={len(blind_inputs_all)}")
print(f"COVERAGE-MATCHED (>={COVERAGE_START}, <{COVERAGE_END}) N={len(blind_inputs_covered)}")
print(f"Dropped (outside coverage window) N={len(blind_inputs_all)-len(blind_inputs_covered)}")

def score_set(acts, inputs):
    r = SG.run_blind_battery(acts, inputs)
    return r["hit_rate"], r["hit_count"], r["scored_count"]

# Real chart, coverage-matched
real_rate, real_hits, real_n = score_set(activations, blind_inputs_covered)
real_rate_all, real_hits_all, real_n_all = score_set(activations, blind_inputs_all)

print(f"\n--- REAL CHART ---")
print(f"All-N (original §G number):        {real_hits_all}/{real_n_all} = {real_rate_all:.4f}")
print(f"Coverage-matched N:                 {real_hits}/{real_n} = {real_rate:.4f}")

# Shuffled control, BOTH on all-N (original) and coverage-matched-N (using the SAME
# blind_inputs_covered subset applied to each shifted activation set)
total_days = (SG.BOUNDS_END - SG.BOUNDS_START).days
shuffled_all, shuffled_covered = [], []
for i in range(1, SG.SHUFFLE_COUNT + 1):
    shift = round((total_days / (SG.SHUFFLE_COUNT + 1)) * i)
    shifted = SG.circular_shift(activations, shift)
    rate_all, _, _ = score_set(shifted, blind_inputs_all)
    rate_cov, _, _ = score_set(shifted, blind_inputs_covered)
    shuffled_all.append(rate_all)
    shuffled_covered.append(rate_cov)

mean_all = sum(shuffled_all) / len(shuffled_all)
mean_cov = sum(shuffled_covered) / len(shuffled_covered)

gap_all = real_rate_all - mean_all
gap_cov = real_rate - mean_cov

print(f"\n--- SHUFFLED CONTROL ---")
print(f"All-N shuffled mean (original):     {mean_all:.4f}  (per-shift: {[round(x,3) for x in shuffled_all]})")
print(f"Coverage-matched shuffled mean:      {mean_cov:.4f}  (per-shift: {[round(x,3) for x in shuffled_covered]})")

print(f"\n--- CONTROL GAP ---")
print(f"ORIGINAL gap (as reported in §G):    {gap_all:+.4f} ({gap_all*100:+.1f}pp)")
print(f"COVERAGE-MATCHED gap:                {gap_cov:+.4f} ({gap_cov*100:+.1f}pp)")

out = {
    "coverage_window": [COVERAGE_START, COVERAGE_END],
    "all_n": real_n_all, "covered_n": real_n, "dropped_n": real_n_all - real_n,
    "real_hit_rate_all": real_rate_all, "real_hit_rate_covered": real_rate,
    "shuffled_mean_all": mean_all, "shuffled_mean_covered": mean_cov,
    "shuffled_per_shift_all": shuffled_all, "shuffled_per_shift_covered": shuffled_covered,
    "control_gap_original": gap_all, "control_gap_coverage_matched": gap_cov,
    "beats_control_original": gap_all > 0, "beats_control_coverage_matched": gap_cov > 0,
}
json.dump(out, open(f"{SCR}/coverage_matched_result.json", "w"), indent=2)
print("\nWritten to coverage_matched_result.json")
