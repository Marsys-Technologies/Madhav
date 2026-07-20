---
artifact: PG2_LANE_X-1
lane: X-1 (chart_facts divergence — highest-consequence lane)
version: 1.0
status: COMPLETE
resolves: F-25u
authored_by: PG-2 Diagnostic Bot (Opus 4.8), lane X-1, 2026-07-19
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-1 (branch pg2/X-1) — never left
POTENTIAL_CORRUPTION_FLAG: false
---

# PG-2 Lane X-1 — chart_facts Divergence: Definitive Resolution

## Final-proof answer (verbatim for the wave gate)

**(a) Why does chart_facts diverge?** Because `chart_facts` stores one full ~27,677-row fact set **per ayanamsha** (5 partitions: raman/true_chitra/krishnamurti/lahiri_chitrapaksha/surya_siddhanta_classical) plus a 135-row ayanamsha-invariant partition, so one fully-built chart is **138,519 rows** (= the correct all-ayanamsha total), the two built charts sum to **276,206**, and the sealed **27,554 is the stale v1.0 single-ayanamsha/pre-enrichment figure** — the "divergence" is a scope-labeling mismatch (per-ayanamsha vs all-ayanamsha), not conflation, accretion, duplication, or instability: fact_ids are 100% unique, no natural key spans two build_ids, and the count is byte-identical across three spaced probes with the table's last write two days stale.

## Which number is correct for what scope

| Number | Correct scope | Basis |
|---|---|---|
| **27,554** | per-ayanamsha (single-ayanamsha-equivalent), **stale v1.0/pre-enrichment** | `L1_GANITA_CLOSURE_v1_0.md:94`; v2.0 flags it "now higher post-enrichment — not yet re-measured" |
| **138,519** | **all-ayanamsha total for ONE fully-built chart** (Abhisek `482012f1`) | = 5 ayanamsha partitions (27,618–27,735, mean 27,677) + 135 INVARIANT |
| **276,206** | **all-ayanamsha total across ALL built charts** (2 of 4) | = 138,519 (Abhisek) + 137,687 (Abhinandan `1c826d5a`); Arunima & Kiran unbuilt (0 rows) |

## Probe results table

| Probe | Query | Result |
|---|---|---|
| P1 | `count(*)` all charts | **276,206** |
| P2 | `count(*)` WHERE chart_id=482012f1 | **138,519** |
| P3 | `chart_id, count(*)` GROUP BY | 482012f1=138,519 · 1c826d5a=137,687 · (Arunima/Kiran = 0) — sum **276,206** |
| P4 | `build_id, count(*)` (Abhisek) | b84c3797=112,676 · 45733f22=25,755 · c86ac468=88 — sum **138,519** |
| P5 | `ayanamsha_id, count(*)` (Abhisek) | raman 27,735 · true_chitra 27,691 · krishnamurti 27,670 · lahiri_chitrapaksha 27,670 · surya_siddhanta_classical 27,618 · **INVARIANT 135** — sum **138,519** |
| P6 | `count(*)` vs `count(DISTINCT fact_id)` (Abhisek) | **138,519 = 138,519** → zero duplicate rows |
| P7 | natural keys `(ayanamsha,category,subject,key)` spanning >1 build_id | **0** → build_ids own disjoint sets |
| P8 | fact_category_ownership: rows by owning_asset_id | ga_structural **98,554** (71%) · ga_condition 90 |
| P9 | INVARIANT (135) contents | ayanamsha-independent facts: panchanga calendrical/tithi/vara/karana, naisargika bala, nakshatra_cross_ayanamsha (34 categories) |
| P10 (temporal ×3) | `count(*)`+`now()` (Abhisek) | 138,519 @07:38:00 · 138,519 @07:38:50 · 138,519 @07:42:29 — **identical** |
| P11 | `max(computed_at)` whole table | **2026-07-17T18:58:16Z** (two days stale; no write during session) |

Arithmetic checks: 27,735+27,691+27,670+27,670+27,618 = 138,384 (+135 INVARIANT = 138,519 ✓); 112,676+25,755+88 = 138,519 ✓; 138,519+137,687 = 276,206 ✓; 138,519 / 27,554 = **5.027**.

## Hypotheses — eliminated vs confirmed, and how

- **H1 (per-ayanamsha ×5, native 2026-07-12) — CONFIRMED (principal cause).** P5 returned exactly the ledger's predicted shape: ~5 roughly-equal groups (27,618–27,735) + a small invariant remainder. This is the `REMEDIATION_RUN_LEDGER_v1_0.md:115` verification, run, and it passed "benign."
- **H2 (legitimate growth, zero dup, ga_structural combinatorial) — CONFIRMED & strengthened.** P6 (zero dup fact_ids) + P8 (ga_structural = 98,554 = 71%) independently reproduce `REPORT_D-1.6.md:48`. The three historical totals (135,645 / 138,279 / 138,519) are successive rebuild states across days, not one number moving.
- **H3 (build_ids accreting) — REFUTED as a bug.** P4 shows 3 build_ids, but P7 shows **0** natural keys span >1 build_id → disjoint scope-limited-rebuild provenance under N.3 delete-then-insert, no duplication.
- **H4 (chart conflation) — REFUTED.** P3: only 2 charts, summing exactly to 276,206. Independently confirms BIND §B-5.
- **H5 (active write during session) — REFUTED.** P11: last write 2 days ago; table static.
- **H6 (non-deterministic / mid-rebuild read) — REFUTED.** P10: three spaced probes byte-identical.

## Prior-investigation assessment (mandatory)

- **`llm_consumption_audit/REMEDIATION_RUN_LEDGER_v1_0.md:115`** (H1 source): quotes native's per-ayanamsha hypothesis and prescribes the `GROUP BY ayanamsha_id` verification. **HOLDS.** I ran exactly that query; the predicted "~5 roughly-equal groups → benign" outcome is confirmed. (Its cited figure 135,645 was an earlier rebuild state; the mechanism it names is correct.)
- **`REPORT_D-1.6.md:48`** (H2 source): "chart_facts growth (27,554→138,279) … zero duplicate rows, clean build_id separation — ga_structural's correct combinatorial output, not an accumulation bug." **HOLDS.** Reproduced independently (zero dup fact_ids; ga_structural 71%). Only nuance: its exact endpoint 138,279 is a slightly earlier rebuild than the current 138,519 — successive builds, not a discrepancy.

## PG-1 "unstable across probes" — BIND hypothesis: CONFIRMED as a category error

PG-1 read the gap between an **unfiltered** all-charts count (276,206) and a **chart-scoped** filtered count (138,519) as intra-session instability. It is not: P10 shows the chart-scoped count is byte-stable across three probes and P11 shows the table is two days static. 276,206 and 138,519 are two *different queries* (all-charts vs one-chart), not one query drifting. BIND's hypothesis about PG-1's own reporting is **confirmed**.

## Cockpit reconciliation (asset_registry.count_sql)

None of the `ga_*` `count_sql` expressions filter by `ayanamsha_id`, so the live cockpit counts `chart_facts` in **all-ayanamsha scope (~138K)**, never 27,554. `ga_structural`'s own count_sql (fact_category_ownership join) returns **98,554** for Abhisek. Therefore the cockpit agrees with **138,519-scope**, and the canonical 27,554 in `L1_GANITA_CLOSURE` is expressed in a *different scope than the instrument itself reports* — the crux of the confusion.

## Recommendation for L1_GANITA_CLOSURE_v2_0.md (RECOMMEND ONLY — must_not_touch)

Express the canonical `chart_facts` figure as a **per-chart, all-ayanamsha total**:
> `chart_facts = 138,519 rows per fully-built chart = 5 ayanamsha partitions (~27,677 each) + 135 ayanamsha-invariant rows; zero duplicate fact_ids; ga_structural contributes ~98,554 (71%). Legacy 27,554 is a v1.0 single-ayanamsha/pre-enrichment measurement and must not be cited as the all-ayanamsha total. Multiple build_ids per chart are benign scope-limited-rebuild provenance (disjoint natural-key sets).`

This matches what the live cockpit `count_sql` (no ayanamsha filter) actually reports and closes the OBS-1 divergence permanently. v2.0 already half-acknowledges this ("now higher post-enrichment — not yet re-measured"); the recommendation is to re-measure and restate.

## Residual unknown (PC-1 honesty)

I cannot measure the v1.0 build state, so I cannot *prove* whether 27,554 was literally a single-ayanamsha count or an early all-ayanamsha total that later grew ~5× by enrichment. The near-exact match (27,554 vs current per-ayanamsha ~27,677) favors the former. Either way, **138,519 is the correct, non-anomalous all-ayanamsha total** — the resolution does not depend on disambiguating this.

## Worktree confirmation

All work performed inside `/Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-1`. Prior-work files (`REMEDIATION_RUN_LEDGER_v1_0.md`, `REPORT_D-1.6.md`) were present in-worktree — read directly, no `cd` into any sibling worktree. No corruption found (POTENTIAL_CORRUPTION_FLAG: false).
