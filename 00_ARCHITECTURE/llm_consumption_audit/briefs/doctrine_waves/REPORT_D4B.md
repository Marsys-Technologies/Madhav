---
artifact: REPORT_D4B
type: WAVE CLOSE REPORT (protocol §7 — "the D-1 lesson: a wave without a close report did not
  close") — B-6 REAL CLOSE PASS, mode=GATED (explicitly NOT a full campaign close)
wave: D-4b — Calibration Ignition + Grand Bakeoff (campaign close lane B-6)
status: OPEN — GATED. Headline: the wave still does NOT close this pass. Both of B-1's named
  defects are now fixed on `main` (F-1 + F-2), but no B-1 re-run has been merged, opened, or even
  completed — b1.merged=false. B-2/B-3 remain correctly SKIPPED (hard-gated on B-1's adjudication
  receipt). This report is the REAL close attempt for this pass and SUPERSEDES the version merged
  via PR #695 (`wave/D-4b/B6-close`) — that version is preserved in git history, not deleted; this
  file replaces it going forward as the current record.
opened: 2026-07-21 (formal open, PR #686)
supersedes: REPORT_D4B.md as merged by PR #695 (2026-07-21T23:34:17Z, `wave/D-4b/B6-close`)
this_pass: 2026-07-22, wave/D-4b/B6-real-close, mode=GATED (orchestrator-specified)
conductor: Claude Code (Sonnet 5), B-6 REAL close pass
governing: BRIEF_D4B.md v1.0, CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md,
  ADJUDICATOR_CHARGE_v1_0.md
---

# REPORT_D4B — D-4b Wave, B-6 REAL Close Pass (GATED)

## §0 — Headline (read this first)

**The D-4b wave is still NOT closing this pass.** `CLAUDECODE_BRIEF.md`'s `current_wave` remains
`D-4b (OPEN)` — it is NOT set to `CAMPAIGN-CLOSED`.

**What changed since the PR #695 GATED pass (2026-07-22, earlier the same day):** both of B-1's
two named defects are now fixed and merged to `main`:

1. `gochara_resonance_map` `event_class` mapping gap — fixed by **F-1, PR #699, MERGED
   2026-07-22T11:07:19Z** (confirmed this pass via `gh pr list --repo amonty84/madhav`).
2. `curve_controls.ts` `circularShiftCurve()` wraparound non-resort — fixed by **F-2, PR #697,
   MERGED 2026-07-22T07:03:12Z** (already merged at the time of the PR #695 pass; unchanged, cited
   here for completeness).

F-1's merge carries a documented deviation: `NATIVE_PROXY_LEDGER_D4B.md` NP-D4B-006 (PR #701,
merged) records that F-1's fresh-context Opus verifier stalled on repeated dispatch (agent-
infrastructure instability), and the native authorized conductor-as-verifier as a last resort —
every probe executed live, none taken from the PR's self-report — with a **binding mitigation**:
"a retroactive fresh-context Opus verifier must run against the now-merged state as soon as agent
infrastructure stabilizes." That retroactive pass is reported (by the orchestrating session that
dispatched this one, not re-run independently by this pass) as **VERDICT: ACCEPT** — every claim in
NP-D4B-006 reproduced independently against `origin/main` at `25e0dc4a`, including the live
`permission_curve` probe (`event_class="marriage"`, `guru_shani_double_transit`: `target_count=23`,
19/19 points active, bracketing the true 2013-12-11 marriage date) and the negative control
(`event_class="family"`: `target_count=0`, 19/19 inactive). **This pass records that verdict as
reported upstream and does not re-derive it from scratch; NP-D4B-006's mitigation obligation is
DISCHARGED on that basis** — this is an attribution, not this pass's own independent re-verification
of every probe in that retroVerify.

**The exact blocker, named plainly: B-1 has not been re-run.** Both fixes sit on `main`,
unexercised. Live-verified this pass:

- `gh pr list --repo amonty84/madhav --head wave/D-4b/B1-full-rerun --state all` → **empty**. No PR
  — merged, open, or closed — exists for a B-1 re-run.
- `gh pr list --repo amonty84/madhav --state open` → the only open PR in the entire repo is an
  unrelated pre-existing item (#446, `docs/ba-phase-3-fixes-rerun-report`). No B-1 work is even in
  review.
- The local worktree `.claude/worktrees/wave-D-4b-B1-full-rerun` (base commit `25e0dc4a`, current
  `origin/main` at the time it was created) carries only **uncommitted** work-in-progress: a new
  `platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/dr17_grading.ts` implementation
  plus its test file, and an incidental `pnpm-lock.yaml` diff. No scoring run output, no results
  JSON, no preregistration-packet version bump exists there or anywhere else in the repo.

Per this session's own dispatch terms: **`b1={"merged": false}`; `b2={"skipped": true}`;
`b3={"skipped": true}`** — all three independently reproduced against live repo state, not taken
on the dispatching session's word. A genuine merge failure (not a red/no-winner result — no B-1
result of any kind exists yet to be red or green) is exactly the condition that forces GATED rather
than a FULL close, per this session's own ground rules. This report does not fabricate a champion,
a no-winner verdict, or a B-1 re-run to unblock B-2/B-3.

**Next action for the wave to close** (updated from the PR #695 pass, narrower now that both fixes
land): (a) finish and commit the B-1 full re-run against the F-1+F-2-repaired substrate over the
full 56/54-event set (the sealed test split stays gate-runner/anti-gaming-verifier territory only)
— the `dr17_grading.ts` scaffold already sitting in the WIP worktree suggests this was started;
(b) certify a champion or the pre-committed no-winner branch, honestly, from that run;
(c) THEN B-2/B-3 dispatch against B-1's real adjudication receipt; (d) a future B-6 pass runs the
mode=FULL three-point baseline diff, which neither this pass nor the PR #695 pass has run.

## §1 — What actually ran this REAL close pass (B-6's own scope, mode=GATED)

Per this session's dispatch: verify the full campaign state independently (not assume the
orchestrating session's probes), write the honest GATED status with the exact blocker named, and
produce four artifacts — this report, `STATE_D4B.md`, a `NATIVE_PROXY_LEDGER_D4B.md` compiled
summary section, and a `PROMISE_LEDGER_D4B.md` cross-check against every `BRIEF_D4B.md` §1
commitment. Per mode=GATED, the mode=FULL items (master-regression-suite wiring confirmation,
three-point baseline diff, standing-live-loop declaration, `CLAUDECODE_BRIEF.md` current_wave →
`CAMPAIGN-CLOSED`) are explicitly NOT actioned this pass — named here as still open, not silently
dropped.

### 1a — DR-19 compliance check, performed first

`git fetch origin main`; found `.claude/worktrees/wave-D-4b-B6-real-close` already existed
(branch `wave/D-4b/B6-real-close`) but **12 commits behind** `origin/main` — merged
`origin/main` into it this pass (`git merge origin/main --no-edit`, clean, no conflicts) before
any substantive work, per DR-19's "check the branch belongs to the campaign and is current before
starting." `CLAUDECODE_BRIEF.md` frontmatter (post-merge): `status: ACTIVE`, `current_wave: D-4b
(OPEN — NOT CAMPAIGN-CLOSED …)`. `BRIEF_D4B.md` frontmatter: `status: OPENED — native kickoff via
Cowork 2026-07-21`. Branch name matches the dispatched campaign (`wave/D-4b/B6-real-close`) and the
wave (D-4b). No branch/campaign mismatch.

### 1b — Live re-verification of the orchestrating session's own probes

Per this pass's own ground rules ("never claim unverified success"; DR-19), every material claim
handed to this pass was independently reproduced against live repo/DB state rather than trusted:

| Claim (as handed to this pass) | Independent reproduction this pass | Result |
|---|---|---|
| F-1 (PR #699) merged | `gh pr list --repo amonty84/madhav --search "..."` | CONFIRMED: `mergedAt: "2026-07-22T11:07:19Z"` |
| F-2 (PR #697) merged | Same `gh pr list` call | CONFIRMED: `mergedAt: "2026-07-22T07:03:12Z"` (unchanged from prior pass) |
| B-1 full re-run not merged | `gh pr list --head wave/D-4b/B1-full-rerun --state all` | CONFIRMED empty; also confirmed no other open PR anywhere in the repo touches B-1 |
| B-2/B-3 skipped | `gh pr list` search for B-2/B-3/backfill/calibration head refs | CONFIRMED: none found beyond what was already on record |
| `mimamsa_multipliers` still at 0 observations (structural mode unchanged) | Live SQL: `SELECT count(*), count(*) FILTER (WHERE n_observations>0), max(n_observations) FROM mimamsa_multipliers WHERE chart_id='482012f1-…'` | CONFIRMED: `total_rows=9, rows_with_obs=0, max_obs=0` |
| `ka_gochara_sweep` materialization unchanged at 165/300 | Live SQL against `build_substep_progress` + `asset_throughput` (same two queries as the PR #695 pass) | CONFIRMED byte-identical: `165` substeps, `state='error'`, same `last_built_at=2026-07-21T22:25:23.308Z` — no new dispatch has run since |

No claim in this report rests solely on the dispatching session's word without an independent
citation of its own.

## §2 — Parked-items review vs `BRIEF_D4B.md` §2 — spot-check, not a full re-run

The PR #695 pass (`REPORT_D4B.md` as merged by PR #695, preserved in git history) performed the
full parked-items review, DR ratification sweep, and register sweep in detail. This pass spot-
checked the items most likely to have moved given the F-1/F-2 delta, and found:

| Item | Prior pass disposition | This pass's spot-check |
|---|---|---|
| B-1's two named defects | Both named, one merged (F-2), one open (F-1) | **F-1 now also merged.** No other change. |
| CR-113 (orphaned `build_runs` row) | Confirmed closed | Unchanged — not re-queried this pass (no new evidence would move it; flagged as carried, not re-asserted as freshly verified). |
| CR-114 (deploy trigger) | Re-confirmed working via PR #693's own deploy | Unchanged — PR #699/#697/#701's own merges each imply the same `deploy.yml` `workflow_run` path fired again (each shows as `MERGED` with normal CI), but this pass did not re-inspect the workflow run logs individually; not claimed as freshly re-verified. |
| Marriage-specimen residual (D-5 gate_run_3 / DR-17 type-specimen pair) | Corroborated by B-1-narrowed's own re-test, not yet formally closed by B-3 | **Strengthened, not closed.** The retroVerify probe reported to this pass reproduced the same `guru_shani_double_transit` corroboration live against the F-1-merged state (target_count=23, 19/19 active). Still not B-3's own formal residual-pair mining against the fully-materialized sweep (still 55%, per §1b) — carried forward, not closed, exactly as before. |
| `ga_vichara_writer.py` leverage_index dasha-runway sub-field defect | OPEN, new at PR #695 pass | Unchanged this pass — no lane has touched `ga_vichara_writer.py`. |
| CR-120/CR-121 (midpoint-triangle / transit-kernel `NotImplementedModelError` stubs) | Not yet formally registered at the PR #695 pass | **Now formally registered** — `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` v3.10 (2026-07-22, `wave/D-4b/permission-bridge` lane, PR #693): both dispositioned NOT-EVALUABLE (coverage gap, not retirement); midpoint-triangle's mandatory-baseline role formally reassigned to the shuffled-birth control; transit-kernel deferred to a named D-6-era candidate ("2.0 sweep engine"). This closes an ambiguity the PR #695 pass's own follow-on work had flagged as needing a citation. |

All other §2 items from the PR #695 pass are unchanged and are not re-litigated here — see that
report (preserved in git history at the PR #695 merge commit) for the full original review.

## §3 — DR ratification sweep — spot-check, compiled for native ratification, NOT self-ratified

Per `ADJUDICATOR_CHARGE`/`ESCALATION_POLICY`, this session does not ratify its own or any prior
session's provisional doctrine.

- `DISAGREEMENT_REGISTER_v1_0.md`: highest entry is still `DIS.030` (grep, this pass). DR-6/7/8
  (`DIS.019`–`021`) still read `status: resolved ... native ratification queued at campaign close`
  — **still queued**, unchanged. DR-17/18 still lack a formal `DIS.0NN` row — `DIS.030`'s own note
  still names this as open work for a future session, unchanged.
- `NATIVE_PROXY_LEDGER_D4B.md`: now has a sixth entry, **NP-D4B-006** (2026-07-22, native ruling,
  direct via Cowork, PR #701 merged) — the conductor-verified-under-infrastructure-duress F-1
  deviation record, with its retroactive-verifier mitigation. See the compiled summary section
  appended to that file this pass for the full NP-D4B-001 through 006 rollup, including this
  pass's disposition of NP-D4B-006's mitigation obligation (DISCHARGED, per §0 above).
- No new provisional ruling is issued by this pass. This pass's own job is compilation and honest
  status reporting, not adjudication — same discipline as the PR #695 pass.

## §4 — Register final sweep — spot-check

- `CAPABILITY_MANIFEST.json`: `generated_at` has advanced to `2026-07-22T06:50:04.573Z` (was
  `2026-06-27T18:27:38Z` at the PR #695 pass) — a regeneration has happened since, from work
  unrelated to this pass's own edits. No D-4b doctrine-wave artifact is a `canonical_id` the
  manifest tracks, so this is noted for completeness, not treated as drift against this wave.
- `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`: unchanged — `status: LIVING`, ND.1 still RETIRED, no
  open ND item names D-4b by number.
- `CURRENT_STATE_v1_0.md`: not edited by this pass, same as the PR #695 pass's own convention —
  `CURRENT_STATE` updates are a conductor/native-facing action at a real wave close, which this
  pass explicitly is not.

## §5 — Live materialization + calibration state (B-6's own serving-assertion gate, unchanged)

Per `BRIEF_D4B.md` §0's RECONCILIATION, full-horizon `ka_gochara_sweep` materialization gates only
B-6's own serving assertions, not B-1's event-driven scoring. Re-checked live this pass:

```sql
SELECT count(*) FROM build_substep_progress
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- 165  (planned: 300; 55% — byte-identical to the PR #695 pass, no new dispatch since)

SELECT state, last_error, last_built_at FROM asset_throughput
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- state='error'; last_built_at=2026-07-21T22:25:23.308Z
-- last_error="BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run;
--             skipped to avoid building on incomplete data"

SELECT count(*) AS total_rows,
       count(*) FILTER (WHERE n_observations > 0) AS rows_with_obs,
       max(n_observations) AS max_obs
  FROM mimamsa_multipliers WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- total_rows=9, rows_with_obs=0, max_obs=0 — structural mode confirmed unchanged
```

No new rebuild has been dispatched since the PR #695 pass. This report makes no claim of full
materialization and no claim that calibration has left structural mode.

## §6 — Ground-rule compliance (B.10, DR-16, DR-19)

No numerical chart value, score, count, or DB row was fabricated by this pass. Every number cited
above (PR merge timestamps, materialization counts, `mimamsa_multipliers` aggregates, `gh pr list`
results) is either quoted verbatim from a live `gh`/SQL query issued this pass (with its exact
command/SQL shown) or attributed explicitly to the orchestrating session's retroVerify report
(§0, clearly marked as reported-not-rederived, per honesty discipline — this pass does not claim
credit for probes it did not itself run). `asset_runner.py`, `runner.py`'s
`execute_dag`/`_schedule_parallel`, the leakage firewall, raw LEL event data, prior gate/regression
surfaces, and `gochara_grammar`/`gochara_intensity` source logic were not modified — this pass's
only DB reads touched `build_substep_progress`, `asset_throughput`, and `mimamsa_multipliers`
(build/calibration metadata tables, never `life_events` or any sealed-split content), and its only
file writes are the four governance artifacts named in §0/§1. No event row on or after 2020-01-01
was queried by this pass. No destructive DB write was performed.

## §7 — Next

`current_wave` stays `D-4b (OPEN)`. This wave does not close until a B-1 full re-run (over the
repaired F-1+F-2 substrate) is completed, committed, and certifies either a champion or the
pre-committed no-winner branch; B-2 and B-3 then dispatch against that real receipt; B-4/B-5 remain
done; and a future B-6 pass runs the full campaign-close checklist this pass explicitly does not —
including the mode=FULL three-point baseline diff, the master-regression-suite standing-status
confirmation, and the standing-live-loop declaration.
