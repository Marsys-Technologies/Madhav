---
artifact: BETA_T_LEDGER
canonical_id: BETA_T_LEDGER
version: 1.0
status: OPEN — lane β.T (Elevation Campaign v2.1, Stream β GAṆITA, Lane T: timing residuals)
  substantially worked this session; one sub-item PARKED-HONEST blocked on lane β.D, one
  multi-hour dispatch PARKED-HONEST with a stated ETA (Cloud Run job continues autonomously
  after this session ends).
owner: Lane β.T builder (Sonnet, autonomous, Native-Proxy per charter §10)
scope: >
  ELEVATION_CAMPAIGN_CHARTER_v2_1.md §5 "β.T — Timing residuals · EL-15, 17, CR-131,
  gochara env [bounded]". Out of scope (per charter, not attempted): EL-16/D-6
  GOCHARA-SWEEP-2.0 architecture rebuild; the Darpana S3 re-run itself.
branch: elev/beta-T-gochara-timing (flattened from charter's `elev/beta/T-gochara-timing`
  per the same D/F-conflict ruling lane β.D2 already recorded in ~/elev-v2-shared/proxy/beta.md
  — `refs/heads/elev/beta` is a real branch/file, so a nested `elev/beta/T-...` ref cannot
  coexist; PR base remains `elev/beta`)
chart_scope: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek) ONLY — this lane never writes
  1c826d5a or any other chart.
---

# β.T Ledger — Timing residuals (gochara env, sweep completion, CR-131, EL-15/17)

## Verifier protocol note

Every item below ran G0 (live reproduce against prod, before any change) per charter §9.
Four dispositions used: `VERIFIED-CLOSED` · `PREPARED-FOR-NATIVE` · `NOT-REPRODUCED` ·
`PARKED-HONEST`. This session found the DATABASE_URL sub-item already fixed pre-campaign
(NOT-REPRODUCED, evidence bar met per §9.2 — committed regression test +
this ledger's payload excerpts, since `ELEVATION_V2_BASELINE.md` never captured a raw
gochara payload at Phase-0 baseline time — the tools were dark, tracked only by CR-131's
symptom text, not a payload). The sweep-completion and EL-17 sub-items are genuinely
unfinished real work, parked honest with exact state and (where applicable) an ETA — not
claimed complete.

---

## G0 — DATABASE_URL ground truth (CR-131 sub-item, charter §5 β.T / brief starting-context)

**disposition: `NOT-REPRODUCED`** (MCP-served read path) + one narrower, inert, out-of-scope
residual disclosed (not fixed).

**Before (documented, CURRENT_STATE_v1_0.md v6.41, 2026-07-24, PRE-DARPANA READINESS pass):**
> "...the gochara serving tools have a second, separate gap — `DATABASE_URL not set` in
> their execution path..." — `gochara_activation_get`/`gochara_forecast_get`/
> `gochara_election_avoidance_get` (`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`)
> held a self-contained `pg.Pool` reading `process.env['DATABASE_URL']`, never set on the
> `amjis-mcp` Cloud Run service (no DB attachment there) — every call failed / returned
> `backing_data_reachable:false`.

**Root cause + fix (already merged, confirmed via `git blame` and `git log`):**
- PR #732, commit `74752e20` (2026-07-24T01:53:34+05:30, i.e. before this campaign's Phase 0
  at 2026-07-25T05:53Z), `fix(sarva-siddhi/T-1): route gochara serving tools through platform
  DB proxy`.
- Repoints the three tools onto `platform/src/app/api/mcp/db/query/route.ts`'s existing
  read-only DB-proxy (the same invariant every other MCP tool honors: "the MCP server does
  not hold a direct DB connection"). `ALLOWED_TABLES` whitelist gained `kala_gochara_windows`
  + `brahma_remedy_corpus` (both present on `main` HEAD `43116c42`, confirmed by direct file
  read this session).
- The stale, unmerged branch `fix/sarva-siddhi-t1-gochara-db-proxy` (diverged from an old base
  predating the elevation charter's own docs) contains an IDENTICAL 13-line diff to the same
  file — same PR content squash-merged under a different SHA on `main`. That local branch is
  an orphan leftover; not touched by this lane (not in β.T's file ownership, and re-merging it
  would be a no-op / conflict against already-landed content).

**Live G0 re-probe this session (fresh, independent of the PRE_DARPANA claims):**

`gochara_activation_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa)`, 2026-07-25T05:19:14Z:
```json
{"windows":[],"provenance_envelope":{"backing_data_reachable":true,"window_count":0,
"empty_reason":"no kala_gochara_windows row spans this date for this chart/event_class filter — an honest zero-activation result, not a fabricated one"}}
```

`gochara_forecast_get(chart_id=482012f1-..., date_range={2026-08-01,2026-09-30})`,
2026-07-25T05:20Z: `backing_data_reachable:true`, `window_count:15`, 115,614-character payload
(real data — saved to session transcript, excerpted here: `backing_data_reachable":true`,
`window_count":15`).

**Evidence bar (§9.2):** committed regression test at
`platform/python-sidecar/tests/test_cr131_gochara_db_reachability.py` —
(a) DB-free static assertion that `ALLOWED_TABLES` in `route.ts` still whitelists
`kala_gochara_windows` + `brahma_remedy_corpus` (regression guard against the fix being
silently reverted); (b) `@pytest.mark.integration` live check that `kala_gochara_windows`
itself is reachable and non-empty for 482012f1 (the data-layer half of the original
symptom). Both pass on current head (`python3 -m pytest tests/test_cr131_gochara_db_reachability.py -v -m "not integration"` → 1 passed).
Payload diff vs baseline: `ELEVATION_V2_BASELINE.md` never captured a gochara payload (dark
at Phase-0 time, tracked only by symptom text) — this ledger's live payloads above ARE the
first captured post-fix reference; the pre-fix reference is the CURRENT_STATE v6.41 quote
above (a documented connection-error state, not a payload, since the tools 500'd/errored
before producing one).

**Narrower residual found, disclosed, NOT fixed (out of bounded scope):**
`platform/scripts/dispatch_d5_redc_redd_rebuild.py` — an older, ALREADY-SPENT one-off D-5
RED-C/RED-D dispatch script (its single build_run completed months before this campaign) —
reads `os.environ["DATABASE_URL"]` directly with no `.env.local` fallback (would `KeyError`
if re-run today without the var exported in-shell). This is almost certainly the "Monitor
script missing DATABASE_URL... configuration available in .env.local" memory trail in this
lane's brief. Left as-is: it is inert (nothing re-invokes a completed one-off dispatch),
outside this lane's file-ownership rationale for editing an existing script, and fixing dead
tooling would be scope-creep under §0's tie-breaker doctrine (disclosed, not hidden — not
fixed). Every dispatch script this lane authored or ran DOES carry the `.env.local` fallback
(`dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py`,
`dispatch_sarva_siddhi_cr66_cr73_rebuild.py`, this lane's own
`dispatch_elev_beta_t_gochara_resume.py`).

Native-Proxy ruling logged: `~/elev-v2-shared/proxy/beta.md` `[LANE-T]` 2026-07-25.

---

## `ka_gochara_sweep` resume — CR-131 / CURRENT_STATE A-3 (charter §5 β.T)

**disposition: `PARKED-HONEST`** (dispatched + monitored + live progress confirmed; genuinely
incomplete; stated ETA, not claimed done).

**Live state at dispatch time (re-checked, NOT trusted from the stale "165/300" brief text):**
- `asset_throughput`: `state='error'`, `rows_written=3213`,
  `last_error="BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run; skipped to avoid building on incomplete data"`.
  `ka_gochara_resonance` (the sole real `depends_on` entry) has been `state='lit'` (80 rows)
  since 2026-07-20 — this message is the outer Cloud Run job's own 21600s (6h) wall-clock
  ceiling surfacing generically on the run, not a genuinely blocked dependency.
- `build_substep_progress` count: **174/303** at dispatch time (NOT 165/300 — CURRENT_STATE's
  figure is stale; 303 = 3 event classes (`career_advancement` 86, `major_gain` 44, `marriage`
  44 done so far) × 101 years, the T-2 correct-span replan size per
  `PRE_DARPANA_READINESS_v2_0.md` W-1/T-2, which extended the horizon and fixed the
  `_derive_birth_year` bug — NOT the pre-T-2-fix "300" figure).
- Most recent prior dispatch: `build_run 8fd6bcf7` (`uat-darpana-stage4-t2-span-scoped-gochara-rebuild`),
  created 2026-07-24T22:45:38Z, `state='failed'` — hit the 6h Cloud Run ceiling.

**Rate measurement (this session, SQL over `build_substep_progress` timestamps, excluding 2
run-restart gaps > 10 min):** median substep-to-substep delta ≈ **4.1–4.65 min/substep**
(175 deltas sampled). This directly falsifies a "~600x faster post-memoization" resume
estimate that was in circulation — the real speedup over the pre-T-2-fix baseline is the
charter's own framing, **~6x, not 600x**. 129 remaining substeps × ~4.3 min ≈ **~8.9h
projected** — exceeds one 6h Cloud Run dispatch and a sane single-lane overnight budget.

**Action taken:**
1. Acquired `~/elev-v2-shared/locks/db-rebuild` (mkdir + holder.json, `stream:beta lane:T`).
2. Authored `platform/scripts/dispatch_elev_beta_t_gochara_resume.py` (new file, this lane's
   ownership — follows the exact `asset_throughput`-dormant-reset +
   `build_runs`/`build_run_assets`-insert shape of
   `dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py`; `build_substep_progress`, the real
   resumption ledger, untouched — the writer's own idempotent replan resumes from there).
3. Ran it: `build_run b458d112-ff28-4443-910a-183d69373c44` created.
4. `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 --args=--run-id,b458d112-ff28-4443-910a-183d69373c44 --async`
   → execution `brahma-build-pipeline-job-lb675`.
5. Confirmed genuinely running (not just queued): execution `startTime` set
   (2026-07-25T05:39:49Z) AND `build_substep_progress` count advancing (174 → 179 → 180 across
   three checks over ~5 minutes).
6. Released the lock once the dispatch was confirmed live (see Native-Proxy log for the
   "lock held only for the active dispatch+confirm window, not the full multi-hour runtime"
   rationale — the sweep now runs autonomously on Cloud Run, independent of this session；
   holding a cross-lane shared lock idle for hours would needlessly block any other β lane).

**State at session end: 180/303 substeps done (rising).** This dispatch will hit its own
21600s ceiling again at approximately **2026-07-25T11:40Z**, projected to bank roughly
50–60 more substeps (≈230–235/303) before stopping — still short of completion. **At least
one further resume dispatch is required** (same script, `python3 scripts/dispatch_elev_beta_t_gochara_resume.py`
then `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 --args=--run-id,<new-id>`)
to reach 303/303. Estimated **2 further dispatches** total (≈8.9h ÷ 6h ≈ 1.5, rounds up) to
reach completion from this session's start state.

**Not claimed:** sweep completion. **Not claimed:** a definite single remaining-dispatch count
(depends on actual throughput, which varies run to run — 4.1 vs 4.65 min/substep spans a real
range).

---

## EL-17 — CR-66 (phala domain anchors) + CR-37 (activation dating) re-verification

**disposition: `PARKED-HONEST (blocked-on-beta:D-rebuild)`** for BOTH sub-items, per this
lane's explicit brief: "This is a hard dependency" on lane β.D's chart rebuild landing.
Checked `~/elev-v2-shared/implementations/` (empty — no `.live` records for any β.D contract)
and searched for `BETA_D.md` across every worktree (`.worktrees/*`, `.claude/worktrees/*`,
repo root) — **not found; β.D has not produced its ledger yet.** `~/elev-v2-shared/heartbeat/beta.hb`
shows `status:"running"` as of the last check this session (2026-07-25T05:40:06Z) — the
stream is active but β.D specifically has not signalled completion. Per M2.5's binding rule
("a consuming lane may not be dispositioned VERIFIED-CLOSED while any contract/dependency it
consumes lacks a live record — it is PARKED-HONEST"), both sub-items park here rather than
close, even though the live evidence gathered below is strong for CR-37 specifically.

**G0 live probes run anyway** (required regardless of final disposition; also the honest
record in case β.D never lands in this campaign's window):

### CR-66 — phala domain anchors

**Prior state (PRE_DARPANA_READINESS_v2_0.md T-4, 2026-07-24):** "CODE-CLOSED, DATA-PENDING."
PR #739 (commit `7c312f4b`, 2026-07-24T11:00:33+05:30) fixed 3 stacked `ph_nimitta` bugs
(domain-vocabulary mismatch collapsing wealth/spirituality/character to `transition`; a
`LIMIT 200` convergence selection starving future-dated windows; a `horizon_tier` mislabel).
A live re-derivation query at the time predicted "290 real rows across all 6 domains, wealth
0→~26 distinct windows" — but the report explicitly flagged the physical `phala_anchors`
table had NOT yet been rebuilt (still showing the old 8 rows, wealth=0).

**Rebuild since then:** `build_run 42720d15` (`sarva-siddhi-stage2-cr66-cr73-rebuild`),
created 2026-07-24T10:41:18Z, **`state='completed'`** — dispatched via the pre-existing
`platform/scripts/dispatch_sarva_siddhi_cr66_cr73_rebuild.py` (49-asset transitive-dependents
closure seeded at `{ga_structural, ph_nimitta}`, computed live via a recursive CTE over
`asset_registry.depends_on`; includes `ph_nimitta` AND `ka_yojaka` in its `TARGET_ASSETS`).
This predates the CURRENT elevation campaign (started 2026-07-25T05:53Z) — it is NOT lane
β.D's rebuild, it is the earlier SARVA-SIDDHI campaign's own already-completed data refresh.

**Live re-probe this session (2026-07-25T05:41Z), independent of the PRE_DARPANA claims:**
- `SELECT domain, count(*) FROM phala_anchors WHERE chart_id='482012f1-...' GROUP BY domain`:
  `career:26, character:3, general:3, health:6, relationship:4, spirituality:22`. **64 total —
  more than the pre-fix 8, but WEALTH IS STILL ZERO.** The `general`/`health`/`relationship`
  rows are also far short of the 290-row prediction.
- `phala_predictive_anchors_get(domain=wealth)` → `anchor_count:0`,
  `known_gap:"CR-66"` (still flagged), `empty_reason:"phala_anchors has 64 anchor(s) for this
  chart, but none match the requested filter (domain=wealth...)" — an honest, correctly-disclosed
  filter-miss (§N.6 disclosure machinery working as designed), but the underlying data gap is real.
- Bounded follow-up check (NOT a full root-cause fix — out of this lane's "re-verify" mandate
  and file-ownership scope; ph_nimitta's per-domain writer logic is dense enough that a real
  fix needs its own lane): `bodha_convergence` for this chart HAS 5 wealth-domain rows —
  exact parity with every other domain (`career:5, character:5, health:5, relationship:5,
  spirituality:5, wealth:5`). So the upstream convergence source is NOT empty for wealth; the
  zero-anchors outcome is a residual specific to `ph_nimitta`'s anchor-materialization path
  for the wealth domain, beyond the 3 bugs PR #739 already fixed.

**Finding, disclosed per §0's honesty doctrine (NEW residual — NATIVE TO CONFIRM/assign a CR
number on next pass, matching the register's own existing convention for EL-17's fix
direction text):** CR-66 is genuinely NOT closed for the wealth domain even after the
completed pre-campaign rebuild. This needs its own follow-up (either as part of β.D's rebuild
if it happens to touch `ph_nimitta`'s dependency chain, or a dedicated fix lane) — not
something this bounded re-verification lane fixed itself.

### CR-37 — activation dating

**Prior state (PRE_DARPANA_READINESS_v2_0.md T-3, 2026-07-24):** "CLOSED, live-verified."
PR #742 (commit `5307885b`, 2026-07-24T11:36:06+05:30) fixed `ka_yojaka`/`ka_kalasutra` to
resolve real forming-graha lords from L1 `ga_yoga_firings.constituent_planets` /
kāla-sarpa nodal axis / `graha_position` constituent facts, instead of the binder's old
fact-id-hash fallback. Author-reported before/after: native 482012f1 YOGA 12/74→161/207,
DOSHA 203/422→926/1059 (not independently reproduced by that session's own W-5 verifier due
to a connector-cache limitation).

**Live re-probe this session (2026-07-25T05:41:16Z), fully independent, fresh MCP call:**
`kala_yoga_activation_get(chart_id=482012f1-..., limit=25)` over the next 3 years
(2026-07-25→2029-07-24) returned 16 activated yogas with **real dasha-derived windows**:
- Sasa Yoga → Saturn antardasha **2024-12-08 → 2027-08-18** (peak 2026-04-13) — exactly
  matches PRE_DARPANA's cited example verbatim.
- Anapha Yoga → Mercury mahadasha 2010-08-18→2027-08-18 (plus 7 antardasha sub-windows,
  each with `source:"chart_dashas"`, `match_kind:"exact_lord"`).
- Vasi Yoga → 8 real Venus/Sun antardasha windows, including a `clipped_to_birth:true` entry
  correctly bounding the natal window at 1984-02-05.
- Yuga/Shoola/Kedara/Gola Yoga → correctly left **undated** with
  `always_on_reason:"distribution_yoga_sankhya"` (the honest §N.6 discriminator CR-37 added,
  distinguishing structurally-always-on Nabhasa/saṅkhyā yogas from genuinely-missing windows)
  — NOT a bare null, exactly as PR #742 specified.
- Response summary fields: `total_count:16, undated_activation_count:8,
  structurally_always_on_count:2, undated_pending_window_count:6`.
- `provenance.defect_001`: a live-derived check this session found "0/17
  `constituent_facts_array` references orphaned (0%)" for this chart — DEFECT-001 (a
  previously-known §N.5 resolution-integrity concern) does not reproduce here.

**Assessment:** CR-37's live behavior is strong, independently reproduced evidence of correct
operation — real dasha-derived windows for bounded-set yogas, honest `always_on_reason`
disclosure for distribution yogas, zero orphaned constituent-fact references. Its mechanism
(dasha-period matching over `ka_yojaka`/`ka_kalasutra`) does not obviously overlap β.D's
declared scope (EL-30 arudha houses, EL-40 `composite_dispositor_strength`, EL-47 divisional
houses, EL-38 argala zeros — all house-convention / dispositor-strength concerns, not
yoga/dosha activation timing). **Nonetheless dispositioned `PARKED-HONEST
(blocked-on-beta:D-rebuild)` per this lane's explicit brief and M2.5's binding rule**, not
`VERIFIED-CLOSED` — the charter names this as a hard dependency and this lane does not
unilaterally waive that. If a follow-up session confirms β.D has landed with no material
touch to `ka_yojaka`'s inputs, this can be re-dispositioned `VERIFIED-CLOSED` on the existing
evidence above without re-running the probe.

---

## PRE_DARPANA v2.0 Stage-2 residuals, pulled forward explicitly (per this lane's brief)

Both residuals are named in `PRE_DARPANA_READINESS_v2_0.md`'s "Exit — what unlocks it" §1 as
ONE bounded build-dispatch item; they are recorded here as the two distinct register items
they actually are, so neither is silently lost:

1. **CR-66 / T-4 — `phala_anchors` data-refresh.** Code fix PR #739 merged 2026-07-24T05:30:33Z
   (UTC). A rebuild (`build_run 42720d15`, completed 2026-07-24T10:41:18Z) DID run after the
   code fix landed. **Live re-verification this session shows the refresh only PARTIALLY
   succeeded**: `phala_anchors` grew from 8→64 rows across 6 domains (career, character,
   general, health, relationship, spirituality) but **wealth remains at 0**, despite
   `bodha_convergence` holding wealth-domain source rows at parity with every other domain (5
   each). This is a genuine, currently-open residual — worse than PRE_DARPANA v2.0 believed
   ("DATA-PENDING" implied a clean rebuild would close it; it did not, for wealth
   specifically). See CR-66 section above for full live evidence.
2. **CR-73 / D-3 — `dosha_label` (kemadruma kendra-support bhaṅga) data-refresh.** Code fix
   PR #735 merged (`_cancel_kemadruma` kendra-support ground, BPHS-cited). The SAME completed
   `build_run 42720d15` includes `ga_structural` (the writer that emits `dosha_label`/kemadruma
   bhaṅga) in its 49-asset closure — so this residual's rebuild ALSO ran. **Not independently
   re-verified live by this lane** (out of β.T's charter-declared scope — CR-73 belongs to
   β.D's D-3 lane, not β.T's EL-15/17/CR-131 charge; documented here per the brief's explicit
   "pull the two residuals into the register" instruction, not re-verified here to avoid
   scope creep into another lane's item). **Recommend β.D or a dedicated follow-up
   live-re-probe** `kemadruma` firing status for 482012f1 (PRE_DARPANA v2.0 D-3's own last
   live check, pre-rebuild, showed `fire_reason:"requires_pass"` still — status post-rebuild
   unknown until re-probed).

---

## Summary table

| id | item | disposition | evidence |
|---|---|---|---|
| CR-131 (serving) | gochara MCP tools' DATABASE_URL gap | `NOT-REPRODUCED` | live re-probe + committed regression test `test_cr131_gochara_db_reachability.py` |
| CR-131 (sweep) | `ka_gochara_sweep` 482012f1 completion | `PARKED-HONEST` | dispatched, live-progress-confirmed (174→180/303), ETA ~2 more 6h dispatches |
| EL-17 / CR-66 | phala domain anchors, wealth specifically | `PARKED-HONEST (blocked-on-beta:D-rebuild)` | live probe: wealth=0/64, `known_gap:CR-66` still set; NEW residual beyond PR #739's 3 fixed bugs, native to confirm/assign CR # |
| EL-17 / CR-37 | yoga/dosha activation dating | `PARKED-HONEST (blocked-on-beta:D-rebuild)` | live probe: real dasha windows, correct `always_on_reason` disclosure, 0% orphaned constituent-facts — strong independent evidence, held pending the charter's explicit β.D gate |
| PRE_DARPANA residual 1 | CR-66 `phala_anchors` refresh | documented, partially-successful, wealth open | see CR-66 above |
| PRE_DARPANA residual 2 | CR-73 `dosha_label` refresh | documented, not re-probed (β.D's item) | see above |

## Files touched by this lane

- `platform/scripts/dispatch_elev_beta_t_gochara_resume.py` (new)
- `platform/python-sidecar/tests/test_cr131_gochara_db_reachability.py` (new)
- `00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_T.md` (this file, new)

No writer-code changes were made (the two DB gaps this lane investigated were both already
fixed pre-campaign; the two residual data-only gaps found — wealth=0 anchors, and the
sweep's remaining substeps — are DATA state, not code, and out of this lane's bounded
"re-verify + resume" mandate to fix outright). FORENSIC 7/7 not re-checked: this lane's only
write action (the sweep dispatch) touches `kala_gochara_windows` only, per the brief's own
note that FORENSIC re-check is not required after a gochara-sweep-only resume.
