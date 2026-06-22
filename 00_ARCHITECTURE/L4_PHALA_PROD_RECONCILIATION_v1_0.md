---
artifact: L4_PHALA_PROD_RECONCILIATION_v1_0.md
canonical_id: L4_PHALA_PROD_RECONCILIATION
version: 1.0
status: COMPLETE — all Q1–Q5 and C1–C4 answered; gates GATE B authoring
authored_by: Claude Code 2026-06-21 (DB queries against prod via mcp__postgres__query)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The prod-truth verification gate (GATE A of L4_PHALA_PRE_IMPLEMENTATION_CLOSURE_v1_0.md).
  Answers the five reconciliation questions (Q1–Q5) and four code checks (C1–C4) from live
  prod data + code inspection. All downstream gates (DECIDE, AUTHOR, REGISTER, WIRE, ARM) are
  gated on this document being complete. Resolves all [RECON] tags in the draft briefs.
---

# L4 Phala — Prod Reconciliation v1.0

> Verification method: live SQL queries via `mcp__postgres__query` against the production DB
> + `grep`/file inspection of the codebase. All row counts are prod-true as of 2026-06-21.

---

## Findings Table

| Q/C | Question | Finding | Resolution |
|---|---|---|---|
| **Q1** | Multi-dāśā prod state — how many systems at what levels? | **All 7 systems at level 4 in prod** (see row-count table below). | **U1 = WIRE ONLY** (branch a). No code work. Just consume in L4 + M9. |
| **Q2** | Is the multi-dāśā conflict (L1 seal "536k = Vimśottarī" vs "7-system writer") resolved? | Resolved by Q1 data. All 7 systems exist at L1–L4 in `chart_dashas`. The L1 seal's "536k" was Vimśottarī-only per-row count; it did not mean other systems were absent. | **D16 correction confirmed.** U1 was never a heavy reopen. |
| **Q3** | M9 multi-school state — do persistence tables exist in prod? | `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements` (migrations 057–060) are in `_archive/` and **NOT applied to prod**. No `%school%` table exists in the `public` schema. | **M9 = full activation** (de-hardcode + persist + wire). Tasks A+B+C+D all required. |
| **Q4** | All L4-consumed inputs present? (convergence, obstruction, signals, discoveries, embeddings, cdlm, subsystems) | **All confirmed present** — see row-count table below. One update: `bodha_discoveries` = **1,505** (plan said 1,411 — slightly higher). | **All L4 input dependencies are SATISFIED.** No upstream gaps. |
| **Q5** | Prāṇa / lifetime ceiling — deepest current level? | `chart_dashas` stops at `level_n = 4` (Sūkṣma). `kala_jivana_parva` has **739 rows** but `avg_effective_score = null` throughout (all `parva_quality = 'transitional'`). Scoring has never been applied. | **U2 = score enrichment + lifetime expansion** (not rebuild). Level 5 / Prāṇa is genuinely net-new. |
| **C1** | Multi-dāśā code check — are non-Vimśottarī compute functions real? | `ga_dashas_writer.py` confirmed: `compute_yogini_system` (line 969), `compute_kalachakra_system` (line 1820), etc. — all 7 systems have real compute functions. | Confirms Q1 interpretation. No stubbing. |
| **C2** | M9 hardcoding extent — how hardcoded are the engine `defaultSignals`? | All 8 school files (`parashari_engine.ts`, `jaimini_engine.ts`, `tajika_engine.ts`, `kp_engine.ts`, `nadi_engine.ts`, `bnn_engine.ts`, `yogini_engine.ts`, `types.ts`) reference `ABHISEK_CHART` / `defaultSignals`. | Task A (de-hardcode) is required for all 7 active school engines. This is the main M9 lift. |
| **C3** | Is `school_runner` consumed anywhere? (confirms "dormant") | `grep -r "school_runner\|runFullTriangulation"` across `platform/src` outside `lib/schools/` returns **zero hits**. | **Confirmed dormant.** No callers to update. M9 activation is an additive wiring, not a refactor. |
| **C4** | Are `ga_tajaka` + `ka_gochara` feedable to Tājika/BNN? | `l1_tajik_varsha_year_lords` = **240 rows** in prod for native. `kala_activation` table exists (66,738 rows); `ka_gochara` is a service-layer asset (no persisted `kala_gochara` table — callable as a service). | **Task B feasible.** Both pending flags are resolvable. |

---

## Q1 — chart_dashas multi-dāśā row counts

| system_id | level_n=1 | level_n=2 | level_n=3 | level_n=4 | total |
|---|---|---|---|---|---|
| vimshottari | 63 | 975 | 9,489 | 40,510 | 51,037 |
| yogini | 175 | 1,365 | 10,840 | 71,360 | 83,740 |
| ashtottari | 65 | 455 | 3,620 | 28,820 | 32,960 |
| chara_karaka | 90 | 1,050 | 12,510 | 124,885 | 138,535 |
| kalachakra | 66 | 748 | 8,894 | 96,341 | 106,049 |
| mudda | 240 | 2,160 | 19,405 | 80,400 | 102,205 |
| naisargika | 40 | 310 | 2,450 | 19,145 | 21,945 |
| **TOTAL** | | | | | **536,471** |

> The 536,471 total matches the L1 seal's headline figure exactly — confirming the seal captured all
> 7 systems, not just Vimśottarī. The "Vimśottarī 536k" attribution in the L1 handoff was misleading.
> U1 resolves to **WIRE ONLY**: consume `dasha_consensus_count` in `ph_nimitta` Axis 6 and M9; no
> schema changes, no build-run, no depth extension needed.

---

## Q4 — L4-consumed input row counts (all for chart_id 482012f1)

| Table | Expected (plan) | Prod actual | Status |
|---|---|---|---|
| `kala_convergence` | 660 | **660** | ✅ exact |
| `kala_obstruction` | 60 | **60** | ✅ exact |
| `kala_bhavishya` | — | **50** | ✅ present |
| `kala_darshana` | — | **300** | ✅ present |
| `kala_jivana_parva` | — | **739** | ✅ present (scores null) |
| `kala_activation` | — | **66,738** | ✅ present |
| `bodha_msr_signals` | 66,738 | **66,738** | ✅ exact |
| `bodha_signal_embeddings` | 66,738 | **66,738** | ✅ exact |
| `bodha_discoveries` | 1,411 | **1,505** | ✅ higher (updated) |
| `bodha_cdlm_cells` | — | **70** | ✅ present |
| `ga_yoga_firings` | — | **5** | ✅ (5 fired yogas for native) |
| `ga_condition_composite` | 45 | **45** | ✅ exact |
| `ga_medical` | 45 | **45** | ✅ exact |
| `ga_vastu_planet_direction_map` | 40 | **40** | ✅ exact |
| `l1_tajik_varsha_year_lords` | 240 | **240** | ✅ exact |

> All L4 inputs are present. bodha_discoveries updated from 1,411 → **1,505**; update [RECON Q4] tags
> in ph_nimitta §1 Axis 4 and the campaign plan accordingly.

---

## A6 — Migration state (CRITICAL)

| Item | Value |
|---|---|
| Max migration applied to prod (`_migrations_applied`) | **325** |
| Total migrations applied | 90 |
| Migrations authored but NOT applied | **326, 327, 328, 329** (in `platform/migrations/`) |
| First safe L4 migration number | **330** (confirming D14) |

### Migrations 326–329 — unapplied (must apply before L4 kickoff)

| # | File | Purpose |
|---|---|---|
| 326 | `326_l2_bodha_target_floors_cockpit.sql` | L2 Bodha cockpit target floor reconcile |
| 327 | `327_l2_bodha_cockpit_is_active.sql` | L2 Bodha `is_active` flag |
| 328 | `328_ka_transit_almanac_retired.sql` | Expand `catalog_status` constraint to allow 'RETIRED' |
| 329 | `329_ka_transit_almanac_hard_remove.sql` | Hard-remove `ka_transit_almanac` from asset_registry |

> **OPERATOR ACTION REQUIRED (A7 gate):** Apply 326–329 to prod before L4 kickoff. These are L2/L3
> cleanup migrations that should have been applied post-close. The deploy pipeline runs them in numeric
> order; a CI deploy from main after confirming the migrations will apply them. After 329, the
> `kala_timeline` table still exists with 0 rows — migration 330 (first L4) will DROP it (CF.L3.2).

---

## A7 — Prod vs main

- `kala_timeline` table exists in prod with **0 rows** (correct — data cleaned; table structure remains).
- Migration 329 deletes `ka_transit_almanac` from asset_registry and asset_throughput. After 329 applies,
  the asset is cleanly gone from the registry.
- After 329, L3 kala_* assets will all be lit on the cockpit (the ka_transit_almanac orphan row removed).

---

## Resolution of [RECON] tags in draft briefs

| Brief | Tag | Resolution |
|---|---|---|
| U1 | `[RECON Q1/Q2/C1]` | **WIRE ONLY** — all 7 systems at L4 in prod. |
| U2 | `[Q5]` deepest level | Level 4 is the ceiling. U2 adds level 5 + lifetime. `jivana_parva` scores are null → scoring enrichment needed. |
| M9 | `[RECON Q3]` 057–060 tables | **Not applied.** Full Task C (renumber + apply) required. |
| M9 | `[RECON C2]` hardcoding extent | All 7 engines hardcoded. Task A required for all. |
| M9 | `[RECON C3]` school_runner callers | Zero outside `lib/schools/`. Additive wiring only. |
| M9 | `[RECON C4]` ga_tajaka + ka_gochara | Both reachable. Task B feasible. |
| M9 | `[RECON Q1]` yogini dāśā in prod | **YES** — 83,740 rows at L4. Yoginī engine can read live data. |
| ph_nimitta | `[RECON Q4]` convergence/discoveries/embeddings | 660 / 1,505 / 66,738 — confirmed. Update discovery count 1,411→1,505. |
| ph_nimitta | `[RECON Q1]` dāśā consensus | All 7 systems available → `dasha_consensus_count` is REAL. |
| ph_nimitta | `[RECON Q3/D18]` school consensus | M9 not persisted yet → Axis 6 school half is populated AFTER M9 activation (depends_on M9). |
| ph_sankrama | `[RECON Q4]` cdlm_cells | **70 cells** confirmed. |
| ph_sankrama | `[RECON]` migration number | **336** — assigned in the migration pre-allocation (GATE D). |
| ph_pramana | `[RECON]` migration number | **337** — assigned in the migration pre-allocation (GATE D). |

---

## Summary for GATE B (decisions the native must ratify)

All reconciliation questions are now answered. GATE A is COMPLETE. GATE B may open.

The key impact on decisions:
- **U1 scope** (B6/B7 input): U1 is trivial (wire only, no build). This significantly reduces the total
  launch scope and argues for a SINGLE WAVE (U1 wire → U2 build → re-seal → M9 activate → L4 assets).
- **M9 lift** (B7 input): M9 requires full Task A+B+C+D (de-hardcode 7 engines + persist + wire). It
  is the heaviest non-L4 work item.
- **bodha_discoveries updated to 1,505**: update D13 LEDGER and ph_nimitta brief accordingly.
- **jivana_parva scores null**: confirms U2 score-enrichment is genuine new work (not just a re-read).

---
*End of L4_PHALA_PROD_RECONCILIATION v1.0. GATE A COMPLETE. All Q1–Q5 and C1–C4 answered from prod.*
