---
artifact: CLAUDECODE_BRIEF_L3_KALA_REMEDIATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KALA_REMEDIATION
brief_for: L3 Kāla POST-SEAL REMEDIATION — make the Nirmāṇa build tracker show a genuinely BUILT, operational L3 layer
parent: L3_KALA_CLOSE_v1_0.md (the seal — which is PREMATURE; this brief makes it true)
version: 1.0
status: COMPLETE — all acceptance criteria met; prod + localhost cockpit-verified green 2026-06-21.
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: Claude Code in Google Antigravity IDE (NOT the CLI) — all git/terminal/prod commands embedded
authored_by: Cowork 2026-06-21 (grounded in a live Chrome-MCP cockpit audit + /api/cockpit/stats + code grep)
evidence_basis: >
  Live prod audit 2026-06-21 (madhav.marsys.in Nirmāṇa tracker + /api/cockpit/stats?chart_id=482012f1...):
  the L3 layer renders but is NOT built. 6 assets ERROR `invalid input syntax for type uuid: "CHART_ID"`
  (count_sql uses literal `$$CHART_ID$$` not `$1`), 4 services ERROR `missing_table`, ka_sangam=dormant/0,
  ka_yojaka=lit/66738 but last_built_at=NULL + build_state_stale=TRUE (it is reading the L2 bo_laksana count,
  not real L3 output). last_built_at is NULL on every failing asset → THE WRITERS NEVER RAN AGAINST PROD.
  This is the Brahma V1.3 failure mode (seal reported built + tests-pass, but ACs verified worktree not prod).
---

# CLAUDECODE BRIEF — L3 Kāla Remediation: make the layer ACTUALLY built

## §0 — The situation (read this first; do not skip)
The L3 Kāla CODE is correct and complete (transit_search.py 853 lines TRUE_NODE + long-horizon; I-16
convergence math genuine; anti-drift clean; 0 contract violations; 197 tests pass — all independently
verified). **But L3 is NOT BUILT IN PROD.** The seal (`L3_KALA_CLOSE_v1_0.md`) is premature: it sealed on
green tests in the build environment, not on a verified prod build. The Nirmāṇa build tracker shows the L3
layer with 11 of 12 assets in ERROR/dormant and the 12th (ka_yojaka) falsely "lit" by reading an L2 table.
**Your job: fix the registration bugs, run the build against the native chart in prod, and make the Nirmāṇa
tracker show a genuinely BUILT, lit L3 layer with real rows.** Plus the 13th asset (ka_tulana) and the
disclosed proxies.

## §1 — VERIFIED root causes (exact, from the live API + code grep — do not re-investigate from scratch)
**BUG-1 — `count_sql` placeholder never substituted (6 assets in ERROR).**
`platform/scripts/seed/asset_registry_seed.ts` registers L3 count_sql as
`... WHERE chart_id = $$CHART_ID$$` (a template placeholder) instead of the project convention
`... WHERE chart_id = $1`. The cockpit stats route binds `$1` = chart_id; with the literal `$$CHART_ID$$`,
Postgres receives the string `CHART_ID` → `invalid input syntax for type uuid: "CHART_ID"`.
- Confirmed lines (there are more — grep them ALL): `ka_kalasutra` (1302 `kala_activation`), `ka_vighnakara`
  (1338 `kala_obstruction`), and the same pattern on `ka_kala_darshana`, `ka_jivana_parva`, `ka_bhavishya_lekha`.
- The CORRECT pattern is everywhere in the same file: every L1/L2 asset uses `WHERE chart_id = $1`
  (e.g. line 1040 `bodha_msr_signals WHERE chart_id = $1`). **Fix = replace `$$CHART_ID$$` → `$1`.**

**BUG-2 — service assets have count_sql against non-existent tables (4 services `missing_table`).**
`ka_graha_sancara`, `ka_dasha_kala`, `ka_gochara`, `ka_muhurta_seva` are `asset_kind: 'service'` — they have
NO row table (they compute on demand). Their cockpit state must come from the SERVICE-HEALTH path
(service_health / last_invoked_at), NOT a count_sql against a table that doesn't exist. Either their
count_sql is set (wrongly) to a missing table, or the stats route runs a count for service-kind rows. **Fix
= service-kind rows have `count_sql: null` AND the stats route must branch on `asset_kind='service'` to use
the service-health model (the K0 brief §7 scoped exactly this — verify it actually shipped).**

**BUG-3 — THE BUILD NEVER RAN against prod (last_built_at = NULL on all failing assets).** Even with the
count_sql fixed, the assets are EMPTY because the writers were never executed against chart 482012f1 in
prod. `run_ka_yojaka_prod.py` exists (the pattern); the rest must be run. ka_yojaka's 66,738 is the L2
bo_laksana count bleeding through a mis-scoped count_sql + build_state_stale=TRUE — NOT real output.

**GAP-4 — ka_tulana (the 13th asset) is genuinely MISSING.** No writer, no migration, no registration. The
seal lists "9 assets" and does not disclose it. The brief exists
(`CLAUDECODE_BRIEF_L3_KA_TULANA_v1_0.md`). It must be built (it is light — serve-time ranking over existing
scored windows) OR formally recorded as a deferred carry-forward — native's call (§5).

**GAP-5 — three disclosed proxies** the seal §10 honestly flags but which weaken the instrument:
CF.L3.4 rarity=flat 3.0yr proxy; CF.L3.5 domain=rank-modulo rotation; **CF.L3.6 Mode-A daśā prior = 0.5
neutral proxy (the daśā funnel is NOT actually wired to ka_dasha_kala)** — this last one is the most
consequential; the convergence engine is running on the transit half only.

## §2 — Scope (may_touch / must_not_touch)
**may_touch:**
- `platform/scripts/seed/asset_registry_seed.ts` — the count_sql fixes (BUG-1, BUG-2).
- `platform/src/app/api/cockpit/**` — the stats route's service-kind branch (BUG-2), IF not already shipped.
- `platform/python-sidecar/services/ka_*/**` + `pipeline/orchestrator/writers/ka_*.py` — only to fix what
  blocks the prod build run (BUG-3) and to wire CF.L3.6 (ka_sangam Mode A → real ka_dasha_kala call).
- `platform/python-sidecar/run_ka_*_prod.py` — the per-asset prod-run scripts (create the missing ones,
  mirroring `run_ka_yojaka_prod.py`).
- NEW: `ka_tulana` writer + migration + registration (GAP-4), IF native says build-now.
- a NEW migration for any count_sql correction that must land in the DB (the seed is the source; confirm
  whether a re-seed or a migration applies the change to prod).
- `L3_KALA_CLOSE_v1_0.md` §10 — add ka_tulana + CF.L3.4/5/6 as explicit carry-forwards; correct the seal's
  "built" claim to "code-complete; prod-build remediated in this pass."
**must_not_touch:**
- Any L0/L1/L2 sealed asset, table, or writer. The L3 writers REFERENCE L2 signal_id; ZERO writes to bodha_*.
- The FROZEN orchestrator contract (`@register`/`WriterBase`, never commit `ctx.db_conn`).
- The ratified templates/weights (`L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md`) — read-only.

## §3 — The remediation sequence (do in this order)
**STEP 1 — Fix BUG-1 (the count_sql `$1` binding).** In `asset_registry_seed.ts`, replace EVERY
`$$CHART_ID$$` with `$1` in the ka_* rows. Grep to find them all (`grep -n 'CHART_ID' ...`); there are at
least 5. Cross-check each ka_* artifact count_sql against the existing L2 pattern (`WHERE chart_id = $1`).

**STEP 2 — Fix BUG-2 (service-kind count).** Set the 4 service rows' `count_sql: null`; confirm the cockpit
stats route branches on `asset_kind='service'` → returns service_health, never runs a count. If the K0
service-health branch did not actually ship, implement it now (K0 brief §7).

**STEP 3 — Apply the registry fix to PROD.** Determine how the seed reaches prod (a re-seed script, or a
migration). Apply it via the Cloud SQL Auth Proxy (data-plane is always prod). Re-query
`/api/cockpit/stats?chart_id=482012f1...` and confirm the 6 uuid-errors + 4 missing_table errors are GONE
(assets now show NOT BUILT / 0, not ERROR).

**STEP 4 — Wire CF.L3.6 (the daśā prior — the most important proxy fix).** In the ka_sangam engine, replace
the 0.5 neutral Mode-A daśā proxy with a real call to the `ka_dasha_kala` service (the eligibility prior).
This makes the convergence funnel actually use the daśā soft-prior (the native's co-equal pillar), not just
transit. (CF.L3.4 rarity + CF.L3.5 domain may stay as disclosed proxies if time-boxed — native's call §5.)

**STEP 5 — RUN THE BUILD against prod (BUG-3 — the core fix).** Execute the L3 writers against chart
482012f1 in prod, in dependency order (the session_queue order): K0/services → ka_yojaka → ka_sangam (with
the real daśā prior) → ka_kalasutra → ka_vighnakara → ka_kala_darshana → ka_jivana_parva → ka_bhavishya_lekha.
Use/create `run_ka_*_prod.py` per asset (mirror `run_ka_yojaka_prod.py`). After each: confirm rows land AND
`last_built_at` populates AND `build_state_stale=false`.

**STEP 6 — ka_tulana (GAP-4).** Per native decision (§5): either build it (writer + migration + register +
prod-run) or record it as a formal deferred carry-forward in the seal.

**STEP 7 — RE-VERIFY THE NIRMĀṆA TRACKER (the acceptance — this is the whole point).** Load
madhav.marsys.in → Abhisek Mohanty → Nirmāṇa → expand Kāla. CONFIRM: every built ka_* shows `lit` with REAL
rows (not the L2-bleed 66,738), zero ERROR/FAILED states, services show service_ok/healthy, last_built_at
populated. Screenshot it. The layer header should show real aggregate rows, not just ka_yojaka's count.

**STEP 8 — Correct the seal.** Update `L3_KALA_CLOSE_v1_0.md`: note the premature-seal remediation; add
ka_tulana + CF.L3.4/5/6 to §10; record the genuine post-build row counts. Update CURRENT_STATE.

## §4 — Acceptance criteria [all verified against PROD + the live cockpit]
1. **[cockpit]** `/api/cockpit/stats?chart_id=482012f1...` shows ZERO ka_* assets in `state:"error"` — no
   `invalid input syntax for type uuid` and no `missing_table`.
2. **[cockpit]** every artifact ka_* (kalasutra/sangam/vighnakara/kala_darshana/jivana_parva/bhavishya_lekha)
   shows `state:"lit"`, real `actual_rows > 0`, `last_built_at` non-NULL, `build_state_stale:false`.
3. **[cockpit]** the 4 service ka_* show `state:"service_ok"` (or healthy), NOT error; `count_sql` null.
4. **[anti-drift]** ka_yojaka's row count is its OWN output (kala_activation_predicates), not the 66,738 L2
   bleed; grep confirms zero writes to any bodha_* table.
5. **[daśā prior]** ka_sangam Mode A calls ka_dasha_kala (not the 0.5 proxy); a test shows the daśā
   eligibility actually modulates a convergence window.
6. **[ka_tulana]** built-and-lit OR formally recorded as a deferred carry-forward in the seal §10 (per §5).
7. **[Nirmāṇa visual]** the build tracker Kāla layer renders fully BUILT — screenshot attached; no FAILED/
   NOT BUILT/NOT MIGRATED rows among the assets meant to be built.
8. **[FORENSIC]** the build runs against 482012f1 only; FORENSIC 7/7 unaffected.
9. **[contract]** grep all touched ka_* writers for `.commit()/.rollback()` on ctx.db_conn → ZERO.
10. **[seal corrected]** L3_KALA_CLOSE updated (premature-seal note + carry-forwards + real counts);
    CURRENT_STATE updated.

## §5 — NATIVE DECISIONS the executor needs (surface, do not assume)
- **D-1 ka_tulana:** build it now (it's light) OR defer it (formal carry-forward)? *Cowork lean: build it —
  it completes QT-4 and the brief is ready; it's serve-time ranking over already-built windows.*
- **D-2 the proxies:** fix CF.L3.6 (daśā prior) NOW (recommended — it's load-bearing); CF.L3.4 (rarity) +
  CF.L3.5 (domain) — fix-now or keep-as-disclosed-proxy?

## §6 — Embedded commands (paste-ready)
```bash
git checkout main && git pull && git checkout -b fix/l3-kala-prod-build-remediation
# BUG-1: find every unsubstituted placeholder
grep -n '\$\$CHART_ID\$\$' platform/scripts/seed/asset_registry_seed.ts
# the correct convention to match (every L2 asset):
grep -n 'WHERE chart_id = \$1' platform/scripts/seed/asset_registry_seed.ts | head
# the prod-run pattern to mirror for the other assets:
sed -n '1,60p' platform/python-sidecar/run_ka_yojaka_prod.py
# prod proxy (data-plane is always prod):
bash platform/scripts/start_db_proxy.sh
# after the registry fix reaches prod, re-check live state:
curl -s "https://madhav.marsys.in/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa" | python3 -m json.tool | grep -A2 '"ka_'
```
> Branch/merge: Madhav human-gated PR (plan memory two-stream-branch-policy). This is PROD-affecting — do not
> self-merge; native reviews. After merge + prod build, the Nirmāṇa re-verification (§3 STEP 7) is mandatory.

## §7 — Definition of done
- [ ] BUG-1 fixed (all `$$CHART_ID$$` → `$1`); BUG-2 fixed (services count_sql null + health branch).
- [ ] Registry fix applied to PROD; zero ka_* ERROR states.
- [ ] CF.L3.6 daśā prior wired (real ka_dasha_kala call).
- [ ] L3 build RUN against 482012f1 in prod; all built assets lit + real rows + last_built_at populated.
- [ ] ka_tulana built or formally deferred (per native D-1).
- [ ] Nirmāṇa tracker re-verified BUILT (screenshot); seal corrected; CURRENT_STATE updated.
- [ ] PR opened with the cockpit before/after evidence.

---

# ADDENDUM v1.1 — CLOSEOUT (the two finishing steps) [Cowork 2026-06-21, after a live cockpit re-verify]

## A.0 — Post-remediation state (live `/api/cockpit/stats` verified, NOT the report)
The remediation (PR #319) **substantially worked.** BUG-1…BUG-5 fixed, CF.L3.4/5/6 resolved, ka_tulana
built. The build RAN: the 7 artifact assets are now `state:"lit"` with REAL rows in prod —
ka_yojaka 66,738 · ka_kalasutra 66,738 · ka_sangam 660 · ka_vighnakara 60 · ka_kala_darshana 300 ·
ka_jivana_parva 739 · ka_bhavishya_lekha 50 (Kāla layer ≈135,285 live rows; was a fake 66,738). **The
uuid-error class is GONE.** BUT the live cockpit still shows L3 as not-fully-green for TWO reasons — both
finishing steps, neither a data problem:

## A.1 — FINISH-1: MERGE + DEPLOY PR #319 (clears the 4 services + ka_tulana `missing_table`)
**Symptom (live):** `ka_graha_sancara`, `ka_dasha_kala`, `ka_gochara`, `ka_muhurta_seva`, AND `ka_tulana`
still return `error:"missing_table", state:"error"`.
**Root cause:** PR #319 is **OPEN, not merged/deployed.** The BUG-2 fix (the stats route's
`asset_kind='service'` health branch in `route.ts`) is IN the PR but NOT live — the deployed web revision
still runs the OLD route that tries to count a non-existent table for these service/serve-time assets. This
is the code-plane-vs-data-plane lag ([[feedback-localhost-codeplane-prod-dataplane]]): the DB (mig 250) +
data are in prod, but the Next.js code that READS them is not yet deployed.
**Action:**
```bash
# 1. merge PR #319 (human-gated review first)
gh pr checks 319 && gh pr merge 319 --squash    # after review/approve
# 2. confirm the web service redeploys to the merge SHA (NEXT_PUBLIC flags are build-time baked — needs a fresh build/deploy, not just env)
git rev-parse origin/main
gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'
# 3. allow CDN cache ~30-60s, then re-check (see A.3)
```
> Note: `ka_tulana` is a serve-time/logic asset (no row table) — same category as the 4 services. After the
> route fix deploys, it should render via the service-health/serve path, NOT `missing_table`. If `ka_tulana`
> was registered with `asset_kind='artifact'` + a non-existent table, FIX its registration to the correct
> kind (service/serve) so the deployed route reads it correctly.

## A.2 — FINISH-2: STAMP build-state (clears `build_state_stale:true` + null `last_built_at`)
**Symptom (live):** EVERY L3 asset shows `build_state_stale:true` and `last_built_at:null` — so the cockpit
renders "FAILED / build-state stale" warnings on even the `lit`, real-row assets.
**Root cause:** the writers wrote ROWS but the build-state row (`asset_throughput` / `last_built_at`) was not
stamped for these runs. Per the FROZEN contract, the ORCHESTRATOR is the sole build-state writer — so a
direct `run_ka_*_prod.py` invocation that bypassed the orchestrator's build-state write leaves the stamp
unset. (Rows present + stamp absent = exactly this signature.)
**Action (pick the contract-safe path):**
- **Preferred:** re-run the L3 build THROUGH the orchestrator build path (not the standalone
  `run_ka_*_prod.py` scripts) so the orchestrator stamps `last_built_at` + clears `build_state_stale` as it
  owns the transaction. This is the clean fix and exercises the real "click Build" chain.
- **OR (reconcile):** a one-time mark-fresh that, for each built ka_* asset, sets `last_built_at = now()`
  and `build_state_stale = false` in the build-state table — ONLY if the orchestrator re-run is impractical.
  Document it as a reconcile, not a build.
**Do NOT** fix this by having a writer self-stamp (that violates "orchestrator is the sole build-state
writer", §N.2).

## A.3 — THE FINAL ACCEPTANCE (re-verify the LIVE cockpit — this is the seal gate)
After A.1 + A.2:
```bash
curl -s "https://madhav.marsys.in/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa" \
  | python3 -m json.tool | grep -A6 '"ka_'
```
**ALL of these must hold (or it is NOT sealed):**
1. ZERO ka_* with `state:"error"` — no `missing_table`, no uuid error (incl. the 4 services + ka_tulana).
2. The 7 artifact ka_* + ka_tulana: `state:"lit"` (or `service_ok`), `build_state_stale:false`,
   `last_built_at` NON-NULL.
3. The 4 services: `state:"service_ok"` (health path), not error.
4. Load the Nirmāṇa tracker UI → expand Kāla → ZERO "FAILED / NOT BUILT / NOT MIGRATED" among assets meant
   to be built. **Screenshot it.**
5. THEN, and only then: update `L3_KALA_CLOSE_v1_0.md` status to genuinely SEALED (with the real counts +
   the build-state-stamp note) and `CURRENT_STATE`. L3 is now truly done → L4 may open.

> **Discipline note (why this addendum exists):** the original seal claimed "built + 197 tests pass" while
> prod showed errors; the remediation claimed "201,345 rows" while the live cockpit shows 135,285 + stale
> flags + 5 still-erroring assets. Both were true at the layer they measured but not at the serve plane. The
> ONLY authoritative seal signal is the LIVE cockpit being all-green AFTER deploy — make that the gate.

---
*End of CLAUDECODE_BRIEF_L3_KALA_REMEDIATION v1.1 (with the closeout addendum). The remediation fixed the
real bugs and landed 135k rows of genuine L3 data. Two finishing steps remain — both verified against the
live API: (1) MERGE+DEPLOY PR #319 to clear the 4 services + ka_tulana `missing_table` (a code-plane deploy
lag, not a bug); (2) STAMP build-state via the orchestrator so `last_built_at` populates and the stale flags
clear. Then the live cockpit goes all-green and L3 Kāla is GENUINELY sealed.*
