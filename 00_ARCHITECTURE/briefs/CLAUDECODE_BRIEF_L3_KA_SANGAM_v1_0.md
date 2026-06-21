---
artifact: CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_SANGAM
brief_for: ka_sangam — Saṅgam / THE CONVERGENCE ENGINE + its output (L3 Kāla; THE VALUABLE CORE) [ELEVATE]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.1 (the intersection IS the product), §5.7 (the convergence machinery, 3 planes, Mode A+B soft-prior), §5.9 (generator→narrow→ephemeris-last spine), §5.13 (the RIGOR STRATUM A/B/C — scoring/orb/window/rarity/confidence/independence), §14.5.1 (extend kala_convergence, not replace), §14.5.3 (the engine is ka_sangam's writer — implicit), I-16 (convergence function), I-18 (window profile), I-19 (rarity), I-21 (confidence), I-22 (independence discount)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K4
  blocked_by: [ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_muhurta_seva, ka_yojaka]  # consumes ALL services + the bridge
  blocks: [ka_vighnakara, ka_kala_darshana, ka_tulana, ka_bhavishya_lekha]  # the products + stats read its windows
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py   # NEW writer = the convergence engine (implicit, §14.5.3)
    - platform/python-sidecar/services/ka_sangam/**                        # NEW engine module (Mode A+B + rigor)
    - platform/supabase/migrations/<next>_kala_convergence_rigor.sql       # EXTEND kala_convergence (add rigor cols)
    - platform/scripts/seed/asset_registry_seed.ts                         # re-point ka_sangam depends_on; update description
  parallel_safe_with: []   # the integration nexus — runs after all K1–K3; nothing parallel within K4 before it
hard_internal_gate: "PROVE the anti-drift + rigor spine on ka_sangam ALONE (one signal end-to-end) BEFORE the products (K5) fan out — mirrors the L2 bo_laksana spine-first gate."
---

# CLAUDECODE BRIEF — ka_sangam (The Convergence Engine) — THE VALUABLE CORE [ELEVATE]

## §0 — What this asset IS
`ka_sangam` (Saṅgam, "confluence") is **the convergence engine** and its output — the layer's valuable
core. Given an L2 signal's bound predicate (from `ka_yojaka`) and a horizon, it runs **Mode A**
(daśā-prior funnel) + **Mode B** (un-gated anomaly sweep) over the temporal services, applies the
**RIGOR STRATUM** (scoring, continuous orb-strength, window profiling, rarity, confidence, independence
discount), and emits **ranked intersection windows** — each a (time-window, structural-alignment) pair
with its structural reasoning (L2) and temporal proof. **The intersection IS the product (plan §5.1).**
This ELEVATES the registered `ka_sangam` (today a thin "dasha-transit convergence windows") into the
full rigor-scored engine, extending — not replacing — the existing `kala_convergence` table (plan §14.5.1).

## §1 — Why it matters / strategic role
- **It is what every supreme product is built on (plan §5.11.7).** The lifetime catalog, the danger
  engine, prioritization, the macro-narrative — all read `ka_sangam`'s windows. The engine is written
  ONCE; the products are it "run exhaustively + well-presented." So this is the integration nexus.
- **It carries the efficiency spine (plan §5.9.3).** generator → interval-narrowing → ephemeris-LAST,
  so the expensive `ka_gochara` fires a bounded number of times regardless of horizon.
- **It is where soft data becomes computed objects (plan §5.13).** "magnitude" → a convergence FUNCTION;
  "rare" → a MEASURED base rate; "confident" → a CONFIDENCE function that DISCOUNTS correlated evidence.
  This is the mathematical/statistical soul of "supreme."

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The table EXISTS and anticipates the design (`kala_convergence`):** `convergence_id, chart_id,
  window_start, window_end, convergence_score double precision CHECK [0,1], constituent_factors jsonb,
  source_citation NOT NULL`. A `kala_convergence_staging` table + a sequence exist (a staging→main
  pattern is already set up). The table COMMENT documents a ≥3-factor rule (factor_type ∈
  {dasha_transition, transit_conjunction, signal_activation, md_ad_alignment}) and
  `convergence_score = Σweights/(count×1.0)`. **EXTEND this; keep `convergence_score ∈ [0,1]`.**
- **The registered seed row** (`ka_sangam`) currently `depends_on: ['ka_kalasutra']` with a thin
  description. **Re-point** `depends_on` to the engines it actually consumes; rewrite the description.
- **The factor vocabulary is too small.** The existing 4 factor_types are a precursor; L3 needs the full
  set (yoga-lord transit, daśā eligibility incl. cross-daśā, panchāṅga/Tāra Bala, dignity, affliction,
  the §5.9.2 trigger vocabulary). Extend `constituent_factors` accordingly.

## §3 — The build (the engine + the rigor stratum + the schema extension)
**3.1 — The funnel + two modes (plan §5.7.2, §5.9).** Implement the engine module:
- **Mode A:** `ka_dasha_kala` eligibility prior (interval set) → `ka_gochara` transit search INSIDE
  survivors → `ka_muhurta_seva` fine-sieve → knockout vetoes. Daśā is a SOFT PRIOR (scores, never gates).
- **Mode B:** the un-gated hybrid sweep (`ka_gochara.search_long_horizon`) for rare high-magnitude
  confluence; check (not gate) daśā; FLAG off-daśā firings as high-value discoveries (→ `ka_kala_darshana`).
- The unifying spine: generators (daśā tree-walk + trigger predictors) → interval narrowing → ephemeris
  LAST (through `ka_graha_sancara` cache). Bounded ephemeris calls (assert it).

**3.2 — THE RIGOR STRATUM (plan §5.13 — the heart of the elevation).** Each emitted window carries:
- **convergence_score (I-16):** the FORMAL function — MULTIPLICATIVE across NECESSARY conditions (a veto
  → ~0 if a prerequisite is absent, e.g. afflicted lord) and ADDITIVE-WITH-SATURATION across SUPPORTING
  conditions (corroborating currents add with diminishing returns), with interaction terms. Keep ∈ [0,1].
  **The form + weights are native-ratified (I-16/I-7) — PROPOSE with rationale, `[NATIVE-RATIFY]`, HALT.**
- **continuous orb-strength (I-17):** each transit factor contributes f(orb, speed, applying/separating)
  ∈ [0,1] (from `ka_gochara`), not a boolean.
- **window profile (I-18):** the window is a TIME-SERIES (ramp/peak/decay) — store `peak_date` (the
  surgical moment) + the usable `window_start`/`window_end` shoulder (already columns).
- **rarity (I-19):** the MEASURED base rate — extend the §5.9 sweep over a long baseline, count
  occurrences ≥ this magnitude → a `rarity_years` ("1-in-N-year") number.
- **confidence (I-21):** the COMPUTED function f(independent-current count × strengths × rarity ×
  birth-time robustness) → store `confidence_score` + the high/moderate/speculative label (plan §5.11.6).
- **independence discount (I-22):** the independent-current count DISCOUNTS correlated evidence (daśā is
  nakshatra-derived — don't double-count a daśā + nakshatra "agreement"). Store `independent_current_count`.

**3.3 — Extend `kala_convergence` (the migration).** ADD columns (idempotent `ADD COLUMN IF NOT EXISTS`):
`signal_id uuid` (REFERENCES the L2 signal — anti-drift), `mode text CHECK (mode IN ('A','B'))`,
`peak_date date`, `orb_strength double precision`, `rarity_years double precision`,
`confidence_score double precision CHECK [0,1]`, `confidence_label text`,
`independent_current_count smallint`, `is_off_dasha_discovery boolean DEFAULT false`. Keep the existing
columns + the [0,1] + valid-range checks. Use the staging→main pattern that already exists.

**3.4 — Anti-drift (plan §6, N.5).** Each window references the L2 `signal_id` + the L1/ephemeris facts
that produced it (in `constituent_factors` / `source_citation`); it NEVER restates an L1 computed value
as its own truth. `ka_sangam` writes NOTHING into L2 tables. It MAY (optionally) fill the L2-reserved
NULL hooks ONLY via the `ka_kalasutra` artifact (NOT by writing bo_laksana).

**3.5 — The HARD INTERNAL GATE (mirrors L2's bo_laksana-first).** Before any product (K5) fans out,
PROVE the full spine on ONE signal end-to-end: classify (ka_yojaka) → Mode A + Mode B → rigor scores →
a ranked window with peak/rarity/confidence → anti-drift clean. Only after this passes does K5 proceed.

## §4 — Asset registration (ELEVATE)
Update `ka_sangam`: keep id + `Saṅgam` + `kala_convergence`; rewrite english_description to "Rigor-scored
intersection windows (Mode A + Mode B) with convergence/rarity/confidence per window";
`depends_on: ['ka_yojaka','ka_dasha_kala','ka_gochara','ka_muhurta_seva']`; `asset_kind='artifact'` (it
stores rows); keep the chart-scoped count_sql. Per-chart delete-then-insert idempotency (plan §N.3).

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** Mode A produces a ranked window for a known signal; daśā is a SOFT prior (a
   strong off-daśā transit still surfaces via Mode B — assert an off-daśā discovery is found + flagged).
2. **[verify: pytest]** the ephemeris-last spine: a dual-mode horizon search calls `ka_gochara`/
   `ka_graha_sancara` a BOUNDED number of times (call-counter), not per-day.
3. **[verify: pytest]** convergence_score: a missing NECESSARY condition (afflicted lord) drives it ~0
   (multiplicative veto); adding SUPPORTING currents raises it with diminishing returns (saturation).
4. **[verify: pytest]** window profile: `peak_date` is the max-strength instant; shoulder = where
   strength ≥ threshold. rarity_years computed from the baseline sweep for a known configuration.
5. **[verify: pytest]** confidence DISCOUNTS correlated evidence — a daśā+nakshatra "agreement" (which
   are coupled) yields a LOWER independent_current_count than two truly independent currents.
6. **[verify: anti-drift]** every window references a resolving L2 `signal_id`; no write to any L2 table
   (grep the writer → zero L2 writes); constituent facts resolve to L1 fact_ids.
7. **[verify: NATIVE-RATIFY]** the I-16 convergence-function form + weights HALT for native sign-off.
8. **[verify: HARD GATE]** the single-signal end-to-end spine passes BEFORE K5 products start.
9. **[verify: psql_prod + curl_prod]** `kala_convergence` extended; `ka_sangam` elevated; cockpit row
   count correct; idempotent rebuild; FORENSIC chart unaffected.
10. **[contract]** the writer never commits/rolls back `ctx.db_conn` (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-sangam
# the table to EXTEND
sed -n '/CREATE TABLE IF NOT EXISTS public.kala_convergence /,/);/p' platform/supabase/migrations/0001_brahma_baseline.sql
# next migration number
ls platform/supabase/migrations | sort -n | tail -3
# tests
cd platform/python-sidecar && pytest -q services/ka_sangam pipeline/orchestrator/writers -k "sangam or convergence or rigor or mode_b"
```
> Branch/merge: Madhav human-gated PR. NATIVE-RATIFY gate (I-16/I-7 weights) — Conductor HALTS.
> HARD INTERNAL GATE — products (K5) do NOT start until the single-signal spine passes.

## §7 — Definition of done
- [ ] Engine module: Mode A (soft-prior funnel) + Mode B (un-gated anomaly sweep) on the ephemeris-last spine.
- [ ] Rigor stratum per window: convergence_score, orb-strength, window profile (peak+shoulder), rarity, confidence, independence count.
- [ ] kala_convergence extended (signal_id, mode, peak_date, rarity_years, confidence, independent_current_count, off-daśā flag).
- [ ] Anti-drift clean; no L2 writes; NATIVE-RATIFY weight gate honored.
- [ ] HARD GATE: single-signal end-to-end spine proven before K5.
- [ ] ka_sangam elevated + re-pointed; idempotent; FORENSIC-clean; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Turns a thin placeholder into the layer's valuable core** — the registered `ka_sangam` was "dasha-
   transit convergence windows" with a Σweights/count score; this elevates it to the full two-mode,
   rigor-scored intersection engine that IS the product (§5.1).
2. **Implements the rigor stratum where it belongs — once** — convergence function, orb-strength, window
   profile, rarity, confidence, independence discount all live on the windows the products consume, so
   "supreme" is computed at the source, not bolted onto each product.
3. **Makes Mode B a true discovery engine, not a footnote** — by flagging off-daśā firings as high-value
   and feeding them to the catalog, it delivers the native's "when the dasha is gone, Mode B is the only
   path" requirement as real, surfaced output.
4. **Extends, rather than replaces, an anticipatory schema** — the existing `kala_convergence` (with its
   [0,1] score, factors jsonb, staging table) already pointed at this design; the brief adds the rigor
   columns and re-points the deps, avoiding a destructive rebuild and honoring §14.5.1.
5. **Bakes the independence discount in at the scoring layer** — so the apex insight (cross-subsystem
   convergence) is never an echo chamber: a daśā+nakshatra "agreement" is correctly counted as ~one
   piece of evidence, the single most intellectually serious rigor gap (I-22).
6. **Establishes the L2-style spine-first hard gate** — proving one signal end-to-end before the products
   fan out is exactly the discipline that made L2's autonomous build safe; it prevents a rigor or anti-
   drift bug from propagating into five products at once.

---
*End of CLAUDECODE_BRIEF_L3_KA_SANGAM v1.0. The valuable core. NATIVE-RATIFY gate (I-16 weights) + the HARD spine-first gate inside.*
