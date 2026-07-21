---
artifact: REPORT_D4B
type: WAVE CLOSE REPORT (protocol §7 — "the D-1 lesson: a wave without a close report did not
  close") — B-6 CAMPAIGN-CLOSE PASS, mode=GATED (explicitly NOT a full campaign close)
wave: D-4b — Calibration Ignition + Grand Bakeoff (campaign close lane B-6)
status: OPEN — GATED. Headline: the wave does NOT close this pass. B-1's Grand Bakeoff is
  BLOCKED-ON-DEFECT (two named, evidence-backed defects, not a data gap and not a fabricated
  green); B-2/B-3 are correctly SKIPPED (hard-gated on B-1); B-4/B-5 are done and merged clean.
  This report performs B-6's governance duties (parked-items review, DR ratification sweep,
  register sweep, A-5 gate-record correction) honestly against that partial state. It does NOT
  run the mode=FULL three-point baseline diff (BRIEF_D4B §1 B-6 item 4) — that is conditioned on
  a completed calibration loop this pass does not have.
opened: 2026-07-21 (formal open, PR #686)
this_pass: 2026-07-22, wave/D-4b/B6-close, mode=GATED (orchestrator-specified)
conductor: Claude Code (Sonnet 5), B-6 lane
governing: BRIEF_D4B.md v1.0, CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md,
  ADJUDICATOR_CHARGE_v1_0.md
---

# REPORT_D4B — D-4b Wave, B-6 Campaign-Close Pass (GATED)

## §0 — Headline (read this first)

**The D-4b wave is NOT closing this pass.** Per the orchestrating session's own mode=GATED
instruction, this report states the honest partial status plainly rather than manufacturing a
close. `CLAUDECODE_BRIEF.md`'s `current_wave` remains `D-4b (OPEN)` — it is NOT set to
`CAMPAIGN-CLOSED`.

**The exact blocker:** B-1 (Grand Bakeoff, the wave's empirical centerpiece) ran real, live,
end-to-end scoring for the first time at real scale (14 contenders × 31 TRAIN-eligible events,
434 harness calls, zero call errors) and found **two genuine, reproduced, previously-undiscovered
defects** that block a trustworthy champion or no-winner certification:

1. `gochara_resonance_map` has only 3 populated `event_class` rows for chart 482012f1
   (`career_advancement`, `major_gain`, `marriage`); this run's `category`→`event_class` mapping
   matched none of them, degrading all 12 PERMISSION-system contenders to fallback behavior.
2. `curve_controls.ts`'s `circularShiftCurve()` does not re-sort its output by date after modular
   wraparound, corrupting `proper_scoring.ts`'s CRPS integral for every contender's control side —
   observed directly as mathematically-impossible negative mean CRPS values in this run's own real
   output.

Both are named with root cause, reproduction steps, and a concrete fix direction in
`bakeoff_results/B1_NARROWED_STATUS_v1_0.md` §5 (PR #694, open, not merged). **B-2 (one-shot
backfill) and B-3 (hierarchical calibration) are correctly SKIPPED** — both are hard-gated on
B-1's adjudication receipt per `BRIEF_D4B.md` §1, and were never dispatched (no branch, no
worktree exists for either). This report does not fabricate a champion to unblock them.

**Next action for the wave to close:** (a) a small, reviewable `curve_controls.ts` date-sort fix
(one-line candidate identified) + re-run (cheap — N=1000 controls are pure date-shifts of
already-fetched curves, no new sidecar calls); (b) an A-2 event_class-to-resonance-map mapping
lane before PERMISSION-contender numbers can be trusted; (c) a fresh B-1 run over the full
56/54-event set (the sealed test split stays gate-runner/anti-gaming-verifier territory only);
(d) THEN B-2/B-3 dispatch against B-1's real adjudication receipt.

## §1 — What actually ran this campaign-close pass (B-6's own scope)

Per the orchestrating session's dispatch: (1) A-5 gate-record correction, (2) parked-items review,
(3) DR ratification sweep, (4) register final sweep, (5) mode=FULL baseline diff — **skipped, see
§0** — (6) this report + STATE_D4B.md.

### 1a — A-5 gate-record correction: LANDED

`wave/D-4b/a5-reconciliation` (PR #692, open, not merged) investigated the claim that D-4a's
`REPORT_D-4A.md` §3 gate table row 5 ("Dry-run complete: PASS") might be either (a)
PLUMBING-DRIFT (a working `curve()` implementation existed and was later lost) or (b) a
gate-record-integrity finding. **Verdict: (b), narrowly scoped.** (a) is definitively ruled out:
`model_interface.ts` and `curve.ts` each have exactly one commit in their entire `--follow`
history, and both were already stubbed/complete at creation — there is no predecessor plumbing to
have drifted from. The actual defect: `REPORT_D-4A.md` §3's gate table marked criterion 5 a bare
`PASS` against `BRIEF_D4A.md` §G item 5's literal text ("3 models scored end-to-end") — not met
(only `pratyantar_lord` was scored; `midpoint_triangle`/`transit_kernel` are honestly-reported
gaps, never hidden — the surrounding narrative in the same report, `BIND_D-4A.md` §5e, and
`artifacts/D-4a/A-5/RESULTS_v1_0.md` §1 all state the 1-of-3 fact plainly). Unlike gate item 7,
which got an explicit Binder reconciliation ruling, item 5 never did.

**Landed this pass** (not merely drafted): `REPORT_D-4A.md` §3 row 5 now reads
`PASS — scope-corrected 2026-07-22, see §10`; a new §10 explains the correction verbatim per the
investigation's own drafted text; `STATE_D-4A.md`'s frontmatter carries a one-line discoverability
pointer. The investigation file `D4A_A5_GATE_RECONCILIATION_v1_0.md` is copied into this
directory (its home branch, PR #692, is not itself merged) so the citation resolves. D-4a's
overall `GATE GREEN 7/7` status is NOT reversed — the substance behind item 5 was real and was
accurately narrated elsewhere; this is a precision fix to one table cell so a reader consulting
only the summary table is not misled.

### 1b — Live materialization check (B-6's own serving-assertion gate, BRIEF_D4B §0 RECONCILIATION)

Per §0's reconciled text, full-horizon `ka_gochara_sweep` materialization no longer gates B-1's
event-driven scoring, but it DOES gate B-6's own serving assertions. Checked live this pass
(read-only, aggregate-only, no event-content query):

```sql
SELECT count(*) FROM build_substep_progress
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- 165  (planned: 3 event_classes x 100 years = 300; 55%)

SELECT state, last_error, last_built_at FROM asset_throughput
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- state='error'; last_built_at=2026-07-21T22:25:23Z
-- last_error="BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run;
--             skipped to avoid building on incomplete data"
```

The most recent full-asset dispatch (`build_run c9d722d5-2a06-4f4a-a4a2-18009894fe11`, the one
BRIEF_D4B §0 names as "legitimate progress toward the forward-span/serving goal") ran for exactly
6h00m05s (2026-07-21T16:25:23Z → 22:25:28Z) and hit the writer's own 21600s (6h) timeout budget
before completing — the raised timeout (1800s → 21600s, per the pre-D-4b readiness pass's own
throughput fix) is itself insufficient for a full 300-substep sweep in one dispatch window. **Not
fixed here** — `ka_gochara_sweep`'s internal computation is explicitly must-not-touch source logic
for this lane; this is named as a B-6 finding for the next Cloud-Run-job dispatch, not patched.
One additional, minor, CR-113-pattern finding: `build_runs` row `0a3f15e2-…` (started
2026-07-21T07:57:49Z) still reads `state='running'` with no `ended_at`, more than 20 hours after
start and after a LATER run (`c9d722d5`) already completed and failed — plausibly a stale row the
orphan-watchdog has not yet reconciled. Not reconciled by this session (no destructive DB write
performed); named for a future session's watchdog pass, same remedy as CR-113
(`POST /api/cockpit/watchdog`).

**Consequence for B-6's own serving claims:** any D-4b close report that asserted "the forward
gochara sweep is fully materialized" would be false. This report does not make that claim.

## §2 — Parked-items review vs `BRIEF_D4B.md` §2

| Item | BRIEF_D4B §2 text | Live disposition this pass |
|---|---|---|
| Gate Ś #8 (D-1.6) | narrow yoga-signal-class timing residual, authoritative firing surface unaffected | Re-verified as still carried, still non-blocking (`ganita_yoga_firings_get` unaffected per its original disposition). No D-4b lane touched yoga-firing surfaces; no new evidence contradicts the original non-blocking finding. |
| D-2 carried finding #1 — `leverage_index` `subject=venus` false-empty | owner: B-4 | **CLOSED.** B-4 (PR #689) re-verified LIVE against the deployed connector: `ganita_vichara_get(subject=venus)` returns 5 rows, `subject_alias_resolved: {input: "venus", resolved_code: "VEN"}`. The D-4a A-1 alias-resolution fix is confirmed live and working — not assumed. |
| D-2 carried finding #4 — `judgment_query` v3 oversize baseline | Binder re-reads REPORT_D-2.md fresh | **STILL OPEN.** `REPORT_D-2.md` §6 item 4: trimmed 73KB→23KB (consumable) but still self-flags `response_still_over_12kb_budget_after_full_trim`. Carried through D-3 (not touched) and D-4a (`REPORT_D-4A.md` §6, owner D-4b) to here. No D-4b lane (B-1 through B-5) touched `judgment_query`'s response-budget path. Remains an open item, correctly not silently dropped — no future wave has picked it up yet. Flagged again here. |
| D-4a carried findings | per `BRIEF_D4A.md`'s close report | Two items from `REPORT_D-4A.md` §6 besides #4 above: (a) the primary-vs-secondary metric disagreement (pratyantar_lord underperforms shuffled-birth on CRPS/skill but beats/matches on hit-rate) — this is exactly what B-1's DR-12 adjudication exists to resolve; NOT resolved this pass, since B-1 itself is BLOCKED-ON-DEFECT (§0). (b) `midpoint_triangle`/`transit_kernel` unimplemented — confirmed still true this pass (B-1-narrowed's own feasibility audit independently re-confirmed zero working implementation of either, see §2.2 of the A-5 reconciliation investigation). (c) orphaned `build_runs` row `372b5cfa…` — this is CR-113, already closed at D-5 open (re-confirmed zero non-terminal `build_runs` rows of THAT specific vintage; see §1b above for a DIFFERENT, newly-observed stale row this pass found). |
| CR-113 (orphaned `build_runs` row) | CLOSED | Confirmed still closed (the row this brief names, `372b5cfa…`, is not the same row flagged in §1b above — no regression). |
| CR-114 (mcp/sidecar images stale) | rely on standing `deploy.yml` per-path trigger; re-confirm still configured | **Re-confirmed live and working, positively.** `wave/D-4b/permission-bridge` (PR #693) merged, and its own bind-time assertion log shows the exact CR-114 mechanism firing correctly: the merge triggered `CI — Ganga Quality Gate` → SUCCESS → `deploy.yml`'s `workflow_run` trigger → `Build & Deploy Sidecar` → SUCCESS, with the new `permission_curve` route live in `openapi.json` within the same session. This is real, positive, live evidence the standing trigger still works — not merely "unchanged since D-5." |
| This readiness pass's own A.0 register rows | materialization-completeness-precedes-gate-scoring assertion class | Superseded/reconciled by `BRIEF_D4B` §0's own RECONCILIATION note (event-driven scoring model) — not re-litigated. See §1b above for the LIVE, current materialization state under that reconciled model. |
| Orchestrator-core robustness candidate (`mark_asset_error` non-defensive rollback) | FROZEN, never touched in-lane, flagged for native review | Untouched this pass, correctly — `asset_runner.py` is hard must_not_touch for every B-lane. Still flagged, still open, still native-review-only. |
| Marriage-specimen residual (D-5 gate_run_3, RE-EXAMINED at pre-D-4b readiness) | B-3's residual-pair mining re-derives this fresh against the FULLY materialized sweep before treating it as confirmed either way | **Not formally re-derived by B-3 (B-3 never ran, §0).** But B-1-narrowed's own §5a direct re-test independently corroborates the pre-D-4b readiness pass's finding: re-querying the marriage specimen with the resonance-map-aligned `event_class="marriage"` (vs this run's raw `"family"` mapping) returns `target_count: 23` and `guru_shani_double_transit` active at every point 2013-10-12→2013-12-31, bracketing the true 2013-12-11 marriage date. This is corroborating evidence, not B-3's own formal residual-pair mining — the doctrine-correct disposition still requires B-3 against the fully materialized sweep, which per §1b is at 55%, not 100%. Carried forward, not closed. |
| NEW this pass — `ga_vichara_writer.py` leverage_index dasha-runway sub-field wrong | (not in BRIEF_D4B §2 — surfaced during B-4) | B-4 (PR #689) found `chart_vichara.leverage_index` (subject=VEN, wealth) embeds `years_to_start: 0, dasha_runway_found: true` implying Venus's Mahadasha is already running, while the SAME build's `chart_dashas` shows Venus's next Mahadasha starting 2034-08-18 (~8.08y out) — a real data-quality defect in an L1/L2 writer. Not fixed (out of B-4's `may_touch`); B-4's own remedy join re-derives the dasha-runway factor fresh from `chart_dashas` rather than propagate the wrong value (regression-guarded by its own unit test). **Named here as a new open item, owner: a future `ga_vichara_writer.py` lane.** |
| NEW this pass — B-1 defects | (not in BRIEF_D4B §2 — the wave's own centerpiece finding) | See §0. Owner: a small `curve_controls.ts` fix lane + an A-2 event_class-mapping lane, both named with concrete fix directions. |
| NEW this pass — stale `build_runs` row `0a3f15e2-…` | (not in BRIEF_D4B §2) | See §1b. Owner: a future watchdog-reconciliation pass, same remedy as CR-113. |

## §3 — DR ratification sweep — compiled for native ratification, NOT self-ratified

Per `ADJUDICATOR_CHARGE`/`ESCALATION_POLICY`, this session is not the native and does not ratify
its own or any prior session's provisional doctrine. The table below is a compiled batch for the
native's own review — status is reported as found, not upgraded.

### 3a — DR-6 through DR-19 (`DISAGREEMENT_REGISTER_v1_0.md` DIS.019–DIS.030)

| DR | DIS | Subject | Status as found (live, this pass) |
|---|---|---|---|
| DR-6 | DIS.019 | V-5 signal-class priors (nakshatra_semantic/arudha/special_lagna/vargottama/dhana_axis) | `resolved (binding for D-2; native ratification QUEUED at campaign close)` — **still queued.** Presented here for native ratification. |
| DR-7 | DIS.020 | V-4 mechanism edge-strength formula | `resolved (binding for D-2; native ratification QUEUED at campaign close)` — **still queued.** Presented here for native ratification. |
| DR-8 | DIS.021 | CR-28 `intent_classify` contract redesign | `resolved (binding for D-2; native ratification QUEUED at campaign close)` — **still queued.** Presented here for native ratification. |
| DR-9 | DIS.022 | Valence computation doctrine (D-16/CR-54/CR-83 lineage root) | RATIFIED (native, 2026-07-16/17, Part A + Part B). Already closed. |
| DR-10 | DIS.023 | Within-period peak model (pratyantar-lord default) | RATIFIED (native, 2026-07-17). Already closed. |
| DR-11 | DIS.024 | T-0 retrodiction-gate thresholds + anti-gaming rule | RATIFIED (native, 2026-07-17). Already closed. |
| DR-12 | DIS.025 | D-4 peak-model adjudication hook | RATIFIED (native, 2026-07-17), forward-binding on D-4b's B-1 — **not yet DISCHARGED**, since B-1 has not produced a scored comparison to adjudicate (§0). |
| DR-13 | DIS.026 | Event-scoring semantics (shape/tolerance/control-mirroring) | RATIFIED (native, 2026-07-18). Already closed. |
| DR-14 | DIS.027 | Timing-system plurality (dasha non-exclusivity) | RATIFIED (native, 2026-07-19). Already closed. |
| DR-15 | DIS.028 | Ensemble first-class + proper scoring | RATIFIED (native, 2026-07-19). Already closed. |
| DR-16 | DIS.029 | Adverse-window disclosure (honest-clarity principle) | RATIFIED (native, 2026-07-19; review waived with refinement folded in). Already closed. |
| DR-17/18 | *(no DIS row yet)* | Graded Manifestation Acceptance / Knowledge-Utilization Census | `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md` frontmatter: "NATIVE-RATIFIED IN SUBSTANCE (D-5 gate_run_2 native disposition)" but no formal `DIS.0NN` row exists yet — `DIS.030`'s own note flags this as "open work for a future session, not silently skipped." **Still open this pass** — not authored here (out of this pass's `may_touch`; a register-formalization task, not a B-6 documentation task). Flagged again for the next session that touches the register. |
| DR-19 | DIS.030 | "An open is a repo state, not a message" | RATIFIED (native, 2026-07-21). Already closed. Exercised correctly by this pass's own DR-19 check (see §5 below) and by NP-D4B-004's third precedent instance. |

### 3b — NP-D4B-001 through NP-D4B-005 (`NATIVE_PROXY_LEDGER_D4B.md`)

Every entry's own frontmatter states these are "provisional... subject to native batch
ratification at campaign close (B-6 DR ratification sweep)" — this section is that sweep. None
are upgraded to RATIFIED by this pass; they are compiled for the native's review.

| Entry | Subject | Provisional ruling (unchanged, not re-litigated here) |
|---|---|---|
| NP-D4B-001 | DR-17 grading weights: verbatim consumption by B-1 | RATIFIED VERBATIM (provisional). B-1 may consume all six weights (peak/sub_peak/elevated/neutral/contra/anti-hit) exactly as proposed; not yet exercised (DR-17 grading harness confirmed unbuilt, `B1_NARROWED_STATUS_v1_0.md` §8). |
| NP-D4B-002 | "Cheaper-null" circular time-shift control | Refused as primary; admissible only as a pre-registered, non-gate-bearing diagnostic. Not exercised this pass (no packet version bump registering it). |
| NP-D4B-003 | §4 tie-band widths (±3d/±7d/±45d/±180d) | ADOPTED as this run's operational constants, with a mandatory DR-13(d)-width sensitivity check. Not yet exercised at scale (B-1's certified run has not happened). |
| NP-D4B-004 | Control sample design (N=1000, coverage-matching, seed scheme) | ADOPTED as committed. **Exercised live this campaign**: B-1-narrowed's real run used exactly N=1000 coverage-matched shuffled-birth controls per event/model, condition (e)'s measured-cost logging discharged (434 real calls, zero errors, wall-clock logged in `B1_NARROWED_TRAIN_RUNLOG_v1_0.txt`) — the ruling held up under real use. |
| NP-D4B-005 | Native, direct (not proxy-issued) — B-5 aggregate `COUNT(*)` near the sealed-split boundary | REVIEWED — NO BREACH, one-time carve-out, zero-tolerance for any future row-level read. Already a direct native ruling, not queued for further ratification. |

**This pass's own rulings:** none. This B-6 pass made no new provisional doctrine rulings — its
job was compilation, correction-landing, and honest status reporting, not adjudication.

## §4 — Register final sweep

- **`DISAGREEMENT_REGISTER_v1_0.md`**: read in full for the DR-6..DR-19 range (§3a above); no
  desync found between its `campaign_ref` fields and `NATIVE_PROXY_LEDGER_D4B.md`'s own DR
  numbering. One gap confirmed still open: DR-17/18 lack a formal `DIS.0NN` row (§3a). No new
  entry opened by this pass (compilation only, per this pass's own scope — opening a new DIS row
  is a register-owning action this documentation pass did not take unilaterally).
- **`NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`**: checked — `status: LIVING`, no open ND item names
  D-4a or D-4b by number; ND.1 (Mirror Discipline) remains RETIRED. No cross-check failure.
- **`CAPABILITY_MANIFEST.json`**: checked — `generated_at: 2026-06-27T18:27:38Z` (predates this
  entire doctrine-waves-D-4a/D-5/D-4b arc). This is expected, not drift: the manifest catalogs
  CANONICAL_ARTIFACTS-class governance documents (CLAUDE.md, PROJECT_ARCHITECTURE, etc.), not
  per-wave doctrine artifacts under `doctrine_waves/` — none of this pass's edits (REPORT_D-4A.md,
  STATE_D-4A.md, this report, STATE_D4B.md) touch a canonical_id the manifest tracks. No
  regeneration triggered by this pass's changes.
- **`CURRENT_STATE_v1_0.md`**: not edited by this pass (out of `may_touch` for a B-lane per
  `CONDUCTOR_PROTOCOL`'s convention — `CURRENT_STATE` updates are a conductor/native-facing action
  at a real wave close, which this pass explicitly is not). `CLAUDECODE_BRIEF.md`'s own
  `current_wave` block carries this pass's honest status instead (§0 above).

## §5 — DR-19 check performed first, this pass

Verified live before any work: `git fetch origin main`; worktree
`.claude/worktrees/wave-D-4b-B6-close` on branch `wave/D-4b/B6-close`, fast-forward-merged to
`origin/main` (no divergent local history). `CLAUDECODE_BRIEF.md` frontmatter: `status: ACTIVE`,
`current_wave: D-4b (OPEN)`. `BRIEF_D4B.md` frontmatter: `status: OPENED — native kickoff via
Cowork 2026-07-21`. No branch/campaign mismatch — correct campaign, correct wave, in-scope lane
(B-6, campaign close, explicitly listed in `BRIEF_D4B.md` §1).

## §6 — Ground-rule compliance (B.10, DR-16, DR-19)

No numerical chart value, score, count, or DB row was fabricated by this pass. Every number cited
above (materialization counts, build_run states/timestamps, PR numbers, DR/NP-D4B statuses) is
either quoted verbatim from a committed artifact already in the repo, or a live, read-only,
aggregate query result cited with its exact SQL (§1b) — never recomputed or invented.
`asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`, the leakage firewall, raw LEL
event data, prior gate/regression surfaces, and `gochara_grammar`/`gochara_intensity` source logic
were not modified (the two live queries in §1b touched `build_substep_progress`/`build_runs`/
`asset_throughput` only — build-orchestration metadata tables, never `life_events` or any
sealed-split content). No event row on or after 2020-01-01 was queried by this pass. This pass
performed no destructive DB write (the stale `build_runs` row found in §1b was reported, not
reconciled).

## §7 — Next

`current_wave` stays `D-4b (OPEN)`. This wave does not close until B-1's two named defects are
fixed and re-run to a certified disposition (§0), after which B-2 → B-3 → B-4/B-5 (already done)
→ B-6 (a real close pass, including the mode=FULL three-point baseline diff this pass explicitly
did not run) can proceed in the merge order `BRIEF_D4B.md` §4 specifies.
