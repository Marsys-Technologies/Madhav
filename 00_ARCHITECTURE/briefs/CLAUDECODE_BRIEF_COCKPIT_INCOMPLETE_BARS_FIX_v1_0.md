---
artifact: CLAUDECODE_BRIEF_COCKPIT_INCOMPLETE_BARS_FIX_v1_0.md
canonical_id: COCKPIT_INCOMPLETE_BARS_FIX_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (Chrome-MCP live diagnosis) 2026-06-12
authored_for: Claude Code in Antigravity IDE
diagnosis_method: Chrome MCP live against localhost:3000/cockpit + /cockpit/atlas + /api/cockpit/stats (canonical chart 482012f1)
data_plane: ALWAYS prod via Cloud SQL proxy
key_finding: The L0/L1 "incompleteness" messages are NOT missing data. Every bg_/ga_ asset has rows + error:null. The bars mislead because the §N.4 reconcile (added in PROGRESSBAR_RECONCILE) overrides DORMANT/absent throughput but NOT `building` or `stale` states. Plus the /cockpit grid still crashes on the GCS bucket error (its try/catch fix isn't live here).
---

# Cockpit "Incomplete" Bars (L0/L1) — Fix Brief v1.0

## §0 — Live diagnosis (3 distinct issues, ZERO missing data)
From /api/cockpit/stats (canonical chart) — all assets have rows + `error:null`:

**Issue 1 — STUCK `building` state (the real bug), 4 L0 assets:**
`bg_concordance` (720), `bg_remedies` (266), `bg_text_index` (361), `bg_yogas` (175) show
`state:"building"` despite full data and NO active build. Their `asset_throughput` record never
flipped `building → lit` (orphaned/interrupted run; watchdog didn't reap). The bar/Atlas renders
`building` as "empty/building" → looks incomplete.

**Issue 2 — STALE flags (cascade aftermath), 9 assets:**
`bg_dasha_systems, bg_doshas, bg_ephemeris, bg_ontology, bg_reference, bg_rules, bg_texts` (L0) +
`ga_dashas, ga_vargas` (L1) are `state:"lit"` + full data but `build_state_stale:true` from the
ga_strength/ga_structural rebuild cascade. Data complete; build-state just flags "upstream changed."
Shows as incomplete.

**Issue 3 — /cockpit grid STILL crashes on GCS:**
The main /cockpit page renders only "Build Tracker error — The specified bucket does not exist
(digest 3696286460)". The try/catch fix from COCKPIT_DARK_ASSETS_FIX Bug 2 is NOT live in this
environment (not deployed, or BUILD_STATE_GCS_BASE still points at a missing bucket). The Atlas
renders fine; the /cockpit grid does not.

## §1 — ROOT CAUSE (unifying Issues 1 & 2)
The §N.4 reconcile (deriveState, added in PROGRESSBAR_RECONCILE) makes `count_sql > 0` win over
`dormant`/absent throughput — but it does NOT override `building` or `stale`. So an asset with full
data but a stuck `building` or a stale flag still displays incomplete. The reconcile is too narrow.

## §2 — FIX (display-layer first — NO data rebuild needed)

### Fix A — extend the reconcile to cover building + stale (fixes Issues 1 & 2 in one stroke)
In `deriveState()` (the AssetNode/stats reconcile), the rule should be: **if `count_sql` returns
rows > 0 AND rows ≈ target_floor (within tolerance), the asset is effectively LIT regardless of
whether throughput says `building`, `stale`, or `dormant`.** Specifically:
- `building` + count>0 ≈ target → **lit** (with optional "build-state stale" badge so the orphaned
  record is visible, not hidden — no-silent).
- `stale` + count>0 ≈ target → **lit** (badge "upstream changed" if you want to signal the cascade,
  but it's NOT incomplete — the data is there).
- count=0 + no/dormant throughput → **dormant** (genuinely unbuilt — correct).
- count_sql errors → **error** shown explicitly.
The authoritative signal for "does this asset have its data" is count_sql/chart_facts, per CLAUDE.md
§N.4. throughput.state is build-HISTORY, not the data-presence truth. Apply this in BOTH the Atlas
and the main /cockpit grid (they should share the same deriveState).

### Fix B — reap the 4 orphaned `building` throughput records (state hygiene)
Independently of the display fix, the 4 stuck records SHOULD be corrected at the source: update their
`asset_throughput.state` from `building` → `lit` (they're done; data present). Confirm the watchdog
(`/api/cockpit/watchdog`) reaps orphaned `building` rows going forward so this doesn't recur. (Fix A
makes the DISPLAY correct immediately; Fix B corrects the underlying record + prevents recurrence.)

### Fix C — make the /cockpit GCS try/catch actually live here
COCKPIT_DARK_ASSETS_FIX wrapped `fetchBuildState()` in try/catch. Confirm that change is on this
branch + deployed to the environment the native is viewing (localhost). If `BUILD_STATE_GCS_BASE`
points at a non-existent bucket, the graceful "Build Tracker data unavailable" notice must show
instead of the page crashing. Verify /cockpit renders the asset grid (not just the error boundary).

## §3 — Acceptance [verify on localhost:3000 + prod]
- [ ] /cockpit renders the asset grid (no GCS crash; Build Tracker fails gracefully if bucket absent).
- [ ] All 12 L0 (bg_) assets show lit/correct — the 4 stuck-`building` now lit; the 7 stale now lit.
- [ ] All L1 (ga_) assets lit (ga_dashas, ga_vargas no longer showing incomplete from stale).
- [ ] deriveState: count>0≈target wins over building AND stale AND dormant; count=0 → dormant; error → error.
- [ ] The 4 orphaned throughput records corrected to lit at source; watchdog reaps future orphans.
- [ ] No data rebuild performed (data was never missing — confirmed every asset has rows + error:null).
- [ ] Atlas + /cockpit grid share the SAME deriveState (consistent state across both surfaces).

## §4 — Out of scope
No chart_facts rebuild. No count_sql changes (working, fast). No re-running of the assets (data is
present; this is a state-display + orphaned-record fix). The cascade `stale` flags are correct
build-history — we're not clearing them, just making the bar treat "stale + data present" as lit.

---
*End of COCKPIT_INCOMPLETE_BARS_FIX v1.0. The L0/L1 incomplete bars = stuck `building` (4) + cascade
`stale` (9) + the /cockpit GCS crash — NOT missing data (every asset has rows). Fix = extend
deriveState so count_sql>0≈target wins over building/stale/dormant (§N.4 data-is-truth), reap the 4
orphaned building records, and make the GCS try/catch live. No rebuild.*
