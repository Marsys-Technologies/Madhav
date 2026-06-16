---
artifact: CLAUDECODE_BRIEF_COCKPIT_DARK_ASSETS_FIX_v1_0.md
canonical_id: COCKPIT_DARK_ASSETS_FIX_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (Chrome-MCP diagnosis) 2026-06-12
authored_for: Claude Code in Antigravity IDE
diagnosis_method: Chrome MCP against localhost:3000/cockpit — read /api/cockpit/stats + /api/cockpit/registry live
data_plane: ALWAYS prod via Cloud SQL proxy
---

# Cockpit Dark Assets + Build Tracker Error — Fix Brief v1.0

## §0 — What the live diagnosis found (two SEPARATE bugs on /cockpit)

Native reported strength / sensitive / sade-sati / structural "missing" from the progress bar.
Chrome-MCP diagnosis (live, localhost:3000/cockpit) found **two distinct problems**:

### BUG 1 — 4 ga_ assets are `is_active=false` in PROD (seed says true) → stats filters them out
- `/api/cockpit/registry` returns 47 assets INCLUDING ga_strength, ga_sensitive, ga_sade_sati,
  ga_structural — but all four have **`is_active: false`** in prod.
- `/api/cockpit/stats` returns only 35 assets — the four are ABSENT (the stats route filters to
  active assets). So the progress bar can't show them: they're filtered out upstream.
- **The data is FINE** — ga_dashas/vargas show 536k/21k rows lit; the four have real data in
  chart_facts (confirmed prior diagnostics: strength 2,184 / sensitive 8,135 / sade_sati 11,019 /
  structural 74,644). This is purely a **registry-state divergence**: the seed
  (`asset_registry_seed.ts`) defines `ga_structural` `is_active: true`, but PROD has `is_active: false`
  for all four. A migration or partial seed-apply flipped them inactive in prod and the seed was
  never (fully) re-applied.
- **`target_table: null` is CORRECT for these four — do NOT "fix" it.** They write to the SHARED
  `chart_facts` table via category-filtered count_sql, not a dedicated table. Null target_table +
  a count_sql LIKE-filter is the intended design. Leave it.

### BUG 2 — Build Tracker component crashes: "The specified bucket does not exist"
- The cockpit page renders a server-component error: **"Build Tracker error — The specified bucket
  does not exist. digest: 3696286460"**. This is a GCS bucket misconfiguration (wrong bucket name /
  missing env var / deleted bucket) crashing the Build Tracker visual component. SEPARATE from Bug 1
  — even with the assets active, this component would still throw. Likely a `NEXT_PUBLIC`-baked or
  server-side GCS bucket reference pointing at a bucket that doesn't exist in this environment.

## §1 — FIX BUG 1: re-activate the 4 assets (registry-state, not data)
1. **Find what flipped them inactive.** Grep migrations + recent seed diffs for
   `is_active` changes touching ga_strength/ga_sensitive/ga_sade_sati/ga_structural (suspects:
   217_ga_count_sql_reconcile, 220_ga_target_floors, 222_register_ga_tajaka, or a partial seed-apply
   during the PROGRESSBAR_RECONCILE re-run). Identify the regression so it doesn't recur.
2. **Confirm the seed is the source of truth:** all four should be `is_active: true` in
   `asset_registry_seed.ts` (ga_structural already is — verify the other three). If any is false in
   the seed, fix the seed.
3. **Re-apply to prod:** set `is_active = true` for the four in prod (surgical migration or seed
   re-apply, one tracker row). Do NOT touch target_table (null is correct).
4. **[verify-against: prod]** `SELECT asset_id, is_active, target_table FROM asset_registry WHERE
   asset_id IN ('ga_strength','ga_sensitive','ga_sade_sati','ga_structural');` → all `is_active=true`,
   target_table stays null. Then re-check `/api/cockpit/stats` returns 39 assets (35+4) and all four
   appear with their real counts + reconciled state.

## §2 — FIX BUG 2: the Build Tracker GCS bucket error
1. **Locate the failing GCS read** — grep the cockpit/build-tracker server component + its data
   source for the bucket name / `storage.bucket(...)` / `GCS_*`/`*_BUCKET` env usage. The error
   "specified bucket does not exist" names the exact failure class.
2. **Determine the correct bucket** for this environment (localhost reads prod GCS per
   `[[feedback-localhost-codeplane-prod-dataplane]]`). Likely a missing/renamed bucket env var or a
   `NEXT_PUBLIC`-baked stale value (`[[feedback-next-public-build-arg-baking]]` —
   `[[feedback-next-public-needs-dockerfile-arg]]`).
3. **Fail gracefully:** the Build Tracker should not crash the whole cockpit page on a bucket miss —
   it should show a contained "tracker unavailable" state, not a full server-component error
   (no-silent-... inverse: don't let one component's failure take down the page).
4. **[verify]** /cockpit renders without the "bucket does not exist" error; Build Tracker either
   shows data or a contained error.

## §3 — Acceptance [verify-against: prod / localhost:3000]
- [ ] The 4 assets `is_active=true` in prod; appear in /api/cockpit/stats with real counts.
- [ ] Progress bar shows strength / sensitive / sade-sati / structural (no longer missing).
- [ ] target_table stays null for the 4 (correct — shared chart_facts).
- [ ] Root cause of the is_active flip identified + documented (so it doesn't recur).
- [ ] /cockpit renders without the GCS bucket error; Build Tracker fails gracefully if bucket absent.
- [ ] No data rebuild (data was never missing — registry-state + component-config bugs only).

## §4 — Out of scope
No chart_facts rebuild (data is present). No target_table change (null is correct). No count_sql
change (working). This is registry-state reactivation + a GCS bucket-config fix only.

---
*End of COCKPIT_DARK_ASSETS_FIX v1.0. Two separate bugs: (1) 4 ga_ assets is_active=false in prod
(seed says true) → stats filters them → bar hides them, though data is fine — reactivate; (2) Build
Tracker crashes on a missing GCS bucket — fix the bucket ref + fail gracefully. Diagnosed live via
Chrome MCP. No data was lost.*
