---
artifact: CLAUDECODE_BRIEF_L3_KA_KALASUTRA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_KALASUTRA
brief_for: ka_kalasutra — Kālasūtra / THE ACTIVATION ARTIFACT (L3 Kāla; the §5.3-C stored asset that fills L2's NULL hooks) [ELEVATE — the keystone correction]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.3 (the A+C model — the ONE artifact-asset), §5.10 (kill the row-per-day precompute timeline), §6 (the L2-reserved NULL hooks — L3 fills them, never writes back into L2), §14.2/§14.5 (ELEVATE ka_kalasutra: activation-artifact NOT daily timeline), §5.12 (the bound predicates from ka_yojaka)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K4
  blocked_by: [ka_yojaka, ka_sangam]   # stores the bound predicates (ka_yojaka) + the memoized windows (ka_sangam)
  blocks: []   # but NOTE: 5 registered downstream assets depend on the ka_kalasutra ID (see §2) — must not break them
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_kalasutra.py   # NEW/REWORK writer (artifact, not daily timeline)
    - platform/supabase/migrations/<next>_kala_kalasutra_rework.sql           # REWORK kala_timeline → bounded activation artifact
    - platform/scripts/seed/asset_registry_seed.ts                            # rewrite ka_kalasutra row (drop row-per-day formula)
  must_not_touch:
    - bodha_msr_signals / any L2 table   # L3 fills L2's NULL hooks via THIS artifact, NEVER by writing L2 (anti-drift)
  parallel_safe_with: []   # the storage keystone; downstream deps make it integration-sensitive
  downstream_id_dependents: [ka_sangam, ka_vighnakara, ka_transit_almanac(retired), ph_muhurta, mi_bhavisya]  # the ka_kalasutra ID is referenced — preserve it
---

# CLAUDECODE BRIEF — ka_kalasutra (The Activation Artifact) [ELEVATE — the keystone correction]

## §0 — What this asset IS
`ka_kalasutra` (Kālasūtra, "the thread of time") is L3's **ONE stored ARTIFACT-asset** (the §5.3-C side of
the A+C model). It stores: (1) the **bound activation predicates** per L2 signal (from `ka_yojaka`), and
(2) the **memoized activation windows** that fill L2's deliberately-reserved NULL hooks for the native
chart. It is the keystone the layer's storage rests on. **This is an ELEVATE — and the single most
important CORRECTION in the reconciliation:** the registered `ka_kalasutra` is today a row-per-day
life-span TIMELINE (the precompute-everything model plan §5.10 REJECTS). This brief reworks it into a
BOUNDED artifact. **The id is preserved (5 downstream assets depend on it); the CONTENT is replaced.**

## §1 — Why it matters / strategic role
- **It is the §5.3-C stored asset** — the one place L3 stores rows (everything else is a service or a
  derived product). Without it, L2's reserved NULL hooks stay empty and the services have no memo.
- **It fills L2's NULL hooks WITHOUT touching L2 (plan §6).** L2 left `signature_class`,
  `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb`, `dasha_activation_proximity_score`
  NULL as the reserved L3-fill surface. `ka_kalasutra` populates them — in an L3 artifact REFERENCING the
  L2 `signal_id`. **L3 NEVER writes back into the sealed L2 tables** (the two-plane seam).
- **It is the precompute boundary made concrete (plan §5.10).** It stores the FINITE, chart-bound things
  (the native's bound predicates + computed windows), NOT the infinite daily timeline.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The OLD table = `kala_timeline`** (the precompute model to RETIRE): `id, chart_id, date,
  active_mahadasha, active_antardasha, transit_highlights jsonb, signal_activations jsonb,
  source_citation` — i.e. ONE ROW PER DATE for the life span (`expected_volume_formula:
  ACTUAL(ga_dashas) + ACTUAL(bg_ephemeris) * TRANSITS_PER_DAY`). **This is exactly the daily-precompute
  §5.10 forbids. Replace it.**
- **The L2 NULL hooks to fill (exact, `bo_laksana.py`):** `dasha_activation_proximity_score` (line 760),
  `signature_class` (787), `active_dasha_periods_jsonb` (792), `activation_predicted_dates_jsonb` (793).
  All written `None` by L2, with the in-code comment "L3 Kāla fills them."
- **CRITICAL — 5 downstream assets reference the `ka_kalasutra` ID** (`asset_registry_seed.ts`):
  `ka_sangam` (1248), `ka_vighnakara` (1265), `ka_transit_almanac`/retired (1282), `ph_muhurta` (1318),
  `mi_bhavisya` (1405), + a downstream pointer (1503). **The id MUST be preserved.** Reworking content is
  fine; renaming/removing the id breaks L4/L5. (Several of these deps will be re-pointed by their own
  briefs, but the id stays.)

## §3 — The build (REWORK the table; fill the hooks via the artifact)
**3.1 — Retire the daily-timeline schema; build the bounded artifact (the migration).** Rework
`kala_timeline` (or create `kala_activation` and re-point + drop the old, surgically). The new artifact
stores, per (chart, ayanamsha, L2 signal_id):
- `signature_class` (from `ka_yojaka` — the classification),
- `bound_predicate_jsonb` (the daśā-eligibility + transit-trigger + strength/affliction predicate),
- `active_dasha_periods_jsonb` (the daśā windows where the signal is eligible — the L2-hook value),
- `activation_predicted_dates_jsonb` (the memoized `ka_sangam` activation windows — the L2-hook value),
- `dasha_activation_proximity_score` (how close the next activation is — the L2-hook value),
- `source_citation`, refs.
**One row per signal (×ayanamsha), NOT one row per day.** Bounded + finite (plan §5.10). Drop the
`TRANSITS_PER_DAY` volume formula; set `target_floor` = achieved signal count (plan §N.4).

**3.2 — Fill the L2 NULL hooks IN THE L3 ARTIFACT (plan §6 — never write L2).** The four hook values live
in `ka_kalasutra`, keyed by `signal_id`. A serve-time JOIN (`bodha_msr_signals` LEFT JOIN ka_kalasutra ON
signal_id) presents the L2 signal WITH its filled hooks — WITHOUT mutating `bodha_msr_signals`. **AC:
grep proves zero writes to any L2 table.** (This is the clean realization of the reserved-surface design.)

**3.3 — Memoize the native's activation windows.** Store the `ka_sangam` activation windows for the
native's own signals (the common, expensive queries) so the typical "when does MY yoga fire" query is an
instant lookup, while arbitrary timing stays a live service (the precompute/on-demand hybrid, plan §5.10
"memoize the native's own patterns").

**3.4 — Re-point the seed row + the dependents' deps.** Rewrite the `ka_kalasutra` seed row (drop the
row-per-day description + formula; new description: "Activation artifact: bound predicates + the
activation windows that fill L2's reserved hooks, per signal"). Where downstream assets had
`depends_on: ['ka_kalasutra']` for the OLD timeline meaning, confirm they still want the artifact (most do
— it's the canonical L3 store). Coordinate with each dependent brief; do NOT silently change another
asset's deps without its brief's knowledge (plan branch-isolation).

## §4 — Asset registration (ELEVATE)
Keep id `ka_kalasutra` + `Kālasūtra`. Change english_name to "Activation artifact" (or keep "Timeline" as
the user prefers — flag); `asset_kind='artifact'`; `target_table` = the reworked table; rewrite
description + drop the row-per-day `expected_volume_formula`; `depends_on: ['ka_yojaka','ka_sangam']`;
chart-scoped count_sql; per-chart delete-then-insert (plan §N.3); ×5 ayanamsha.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: psql_prod]** the reworked table stores ONE row per (signal × ayanamsha), NOT one per day;
   the old row-per-day volume formula is gone; count = signal count (bounded, not ~825k×).
2. **[verify: pytest]** the four L2 hooks (`signature_class`, `active_dasha_periods_jsonb`,
   `activation_predicted_dates_jsonb`, `dasha_activation_proximity_score`) are populated in the artifact,
   keyed by a resolving L2 `signal_id`.
3. **[verify: anti-drift]** grep proves ZERO writes to `bodha_msr_signals` or any L2 table; the
   serve-time JOIN presents the filled hooks WITHOUT mutating L2.
4. **[verify: pytest]** the native's own-signal activation windows are memoized (a repeat "when does MY
   yoga fire" is a lookup, not a recompute — call-counter).
5. **[verify: id-preservation]** the `ka_kalasutra` id still exists; the 5 downstream dependents
   (ka_sangam, ka_vighnakara, ph_muhurta, mi_bhavisya, +) resolve; no dangling refs.
6. **[verify: psql_prod + curl_prod]** elevated artifact registered; cockpit count correct;
   target_floor = achieved; idempotent rebuild; FORENSIC chart unaffected.
7. **[contract]** the writer runs on `ctx.db_conn`, never commits/rolls back (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-kalasutra
# the old precompute table to retire
sed -n '/CREATE TABLE IF NOT EXISTS public.kala_timeline/,/);/p' platform/supabase/migrations/0001_brahma_baseline.sql
# the L2 hooks to fill (exact lines)
sed -n '758,795p' platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py
# who depends on the id (must not break)
grep -n "ka_kalasutra" platform/scripts/seed/asset_registry_seed.ts
# tests
cd platform/python-sidecar && pytest -q services/ka_kalasutra pipeline/orchestrator/writers -k "kalasutra or activation_artifact or hooks"
```
> Branch/merge: Madhav human-gated PR. CAUTION: id is referenced by L4/L5 — coordinate dep changes with
> the dependent briefs; do not break the ka_kalasutra id.

## §7 — Definition of done
- [ ] kala_timeline daily-precompute RETIRED; bounded activation artifact built (1 row/signal, not 1/day).
- [ ] The four L2 NULL hooks filled IN the artifact (keyed by signal_id); zero L2 writes.
- [ ] Native own-signal activation windows memoized.
- [ ] ka_kalasutra id preserved; 5 downstream dependents resolve.
- [ ] Seed row reworked (drop row-per-day formula); registered artifact-kind; idempotent; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Kills the precompute-everything timeline the layer's whole architecture rejects** — the registered
   `ka_kalasutra` was a row-per-day life-span table (~825k× rows), the exact anti-pattern the native's
   "timing = services" principle overturned; this brief replaces it with a bounded, finite artifact,
   making the layer's storage honest at its keystone.
2. **Realizes the two-plane seam cleanly** — it fills L2's deliberately-reserved NULL hooks via an L3
   artifact keyed on signal_id and a serve-time JOIN, so the sealed L2 tables are NEVER mutated; this is
   the textbook payoff of the discipline L2 maintained, proven by a zero-L2-writes assertion.
3. **Preserves a load-bearing id while replacing its meaning** — 5 L4/L5 assets depend on the
   `ka_kalasutra` id; the brief reworks content without breaking the DAG, a delicate ELEVATE that a naive
   "rename it" would have shattered.
4. **Delivers the precompute/on-demand hybrid** — by memoizing the native's OWN-signal activation windows
   while leaving arbitrary timing to the live services, it makes the common query instant without
   re-creating the daily-precompute model, exactly the §5.10 boundary in action.
5. **Gives the layer its single canonical store** — consolidating the bound predicates + the activation
   windows in one artifact means every other L3 asset is a service or a derived product over THIS, keeping
   the storage surface minimal and the data/service taxonomy clean.
6. **Closes the reconciliation's most important correction** — of the 4 elevated placeholders, this is the
   one whose original meaning most directly contradicted the settled architecture; fixing it completes the
   alignment of the registered DAG with the L3 strategy.

---
*End of CLAUDECODE_BRIEF_L3_KA_KALASUTRA v1.0. The thread of time — the keystone activation artifact. The reconciliation's most important correction. THIS IS THE 13TH AND FINAL PER-ASSET BRIEF.*
