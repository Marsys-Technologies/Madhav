---
title: KĀLA-YANTRA v3 owner decisions — Amendment A3 (permissions that remove measured blockers)
version: 1.0
status: CURRENT
date: 2026-10-15
amends: KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md, Amendment A1 (D-10, D-14 enforcement), Amendment A2 (D-17 review scope), KALAYANTRA_RELAUNCH_PLAN_v2_7.md (§owns, §8), the fast-lane launcher (cx.sh, cx_post.sh) and COMMON_HEADER, the `main` branch ruleset
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. Amended files stay byte-identical, as A1 and A2 did.
changelog:
  - 1.0 (2026-10-15): created on the owner direction of 2026-10-15 ("Please go ahead, approved") after the re-verified restriction audit of the same day.
---

# Amendment A3 — permissions

**Written for:** the cockpit session, the owner surrogate, every fleet job, and whoever next audits the campaign. Rules are §2–§8; §9 is what was done at once; §10 is how success is measured.

## §1 · Why — the re-verified audit (2026-10-15)

| Finding | Evidence |
|---|---|
| Merges pass alone and fail combined | 4 red `main` runs in 24 h on database or build tests that were green on the branch; `main` red since 10:01Z on one P03 fingerprint shifted by P05; production 10 commits behind; no code item can close while a successful deploy of `main` does not contain it (`v_exact_head_then_deploy_containment`). |
| Agents stop on scope or on an unanswerable question | 9 of 27 blocked jobs cite the owns/allowed-path list; 3 asked for clarification that no one can give mid-job. |
| The cockpit is the serial step after every job | After a job finishes, a quarter of follow-ups wait over 39 min and a fifth over an hour (dead hours excluded). Agents may not commit, push or open PRs. |
| Pure document/plan changes carry full independent review | 5 of 31 merges in three days were documents or plan model only; each took one or more review jobs plus 11 step-evidence jobs. |
| Restrictions enter agent instructions unrecorded | The Docker rule of 12–14 Oct appears in no owner decision. |
| Codex capacity has no overflow | 6 jobs hit capacity limits in three days; 14 ended without a result. |
| Withdrawn | The machine is not saturated (CPU 56% idle on an M5 Max; durations do not rise with concurrency). No agent cap. |

## §2 · D-22 — the merge queue tests the combined result

1. The database and build-test jobs of `CI — Ganga Quality Gate` are **required status checks** on `main` (ruleset 20141220, applied 2026-10-15 12:20–12:35Z; 15 checks in all, up from 6): `Kāla DB Tests (throwaway Postgres)`, `DB Integration Tests (SAMĪKṢĀ, throwaway Postgres)`, `Governance Gochara readback tests (throwaway Postgres)`, `Gochara measuring build - horizon, basis, state guard, fired cap (real runner, throwaway Postgres)`, `Gochara A5.5f - a rebuild replaces the whole candidate chain`, `Gochara A5.5f - test-slice transitions`, `Gochara A5.5f - test-slice round 2 and the real runner`, `Gochara C37 - the small-test dispatch`, `Gochara C38 - the small-test teardown`. Skipped (docs-only) runs satisfy them. **Excluded on purpose:** `C38 … round 2`, `C38 … round 3` and `A5.5f - verifier fixes` are defined in `ci.yml` but no `main` run reports them; a required check that nothing reports blocks every merge, so they stay out until the cockpit shows a `main` run that reports them. Every required name was verified against the jobs the latest `main` runs actually report.
2. Cost accepted by the owner: a merge now waits for the slowest of these (about 30 minutes for the SAMĪKṢĀ suite; the owner was told 10–15 at approval time and the actual figure is recorded here). The merge queue batches up to five PRs per build, so the wait is shared.
3. **A1 D-14 is enforced mechanically in the fast lane:** while the latest `main` push run is red, the cockpit sets `run/HOLD_MERGES`, disables auto-merge on queued PRs, and dispatches one fix-forward job; nothing merges until `main` is green. Document and plan PRs are not exempt (they bury the signal).
4. Required-check names are reconciled against the job names on `main` whenever `ci.yml` renames or removes a job; a required check that no job reports blocks every merge.

## §3 · D-23 — agents decide and continue

1. A packet's owns/allowed-path list is the expected footprint, not a wall. When the fix requires a file outside it, the agent edits it minimally and lists each path with a reason under `out_of_owns` in `result.json`. The reviewer judges the excursion. FROZEN paths, other campaigns' in-flight files and L0–L2 assets stay untouchable.
2. Where the plan does not decide, the agent decides, marks the choice `(I) INTERPRETATION`, lists it with its alternative under `interpretations`, and continues. No job ends `blocked` on an open question or on scope alone; `blocked` is for a missing tool, a missing input or a severe-risk finding (A2 D-17.2).
3. Applied in COMMON_HEADER on 2026-10-15 (backup `COMMON_HEADER.md.bak-20261015-a3`).

## §4 · D-24 — the launcher commits, pushes and opens the PR

1. When a fast-lane job ends with `status: done` and a `commit_message`, the launcher (`cx_post.sh`, outside the sandbox, as the user) commits the working copy, pushes the branch and opens the PR, or updates the existing one. The agent still never runs git writes or `gh`.
2. It refuses on: a detached review copy, `main`/`master`/`shared/*`, a FROZEN path in the diff, a job that is not `done`, or no commit message. Every outcome is written to `post.json` in the job folder; refusals leave the copy for the cockpit exactly as the agent left it.
3. Independent review, acceptance and merge stay with the cockpit and the dispatcher (A1 D-10, A2 D-17).

## §5 · D-25 — review proportionate to the change

1. A PR whose diff is confined to Markdown documents and `00_ARCHITECTURE/control/**/plan_model.json` merges on green required checks without an independent review job; the cockpit's own read is the review and is noted on the PR.
2. Tooling code (the fleet under `briefs/kalayantra/fleet/**`, dashboards, scripts) keeps independent review: it runs with credentials.
3. Plan-model step evidence is taken from the PR diff and CI logs by the cockpit; a separate "step review" agent job is launched only when the diff cannot show the step.

## §6 · D-26 — restrictions are decisions

Any new prohibition or narrowing added to COMMON_HEADER, a task template, a card or a packet "Do not" list is recorded the same day in `run/DECISIONS_SURROGATE.jsonl` with its reason and its expected cost in agent time, and named in the next owner report. A restriction not so recorded is not binding on agents.

## §7 · D-27 — Claude as overflow

When Codex answers "at capacity" or 429 on the third attempt of a job, the launcher may run the same task with a Claude agent at the same sandbox posture. The job records which engine produced the result. Independent review stays engine-agnostic.

## §8 · Kept owner rules

Unchanged and not relaxed by A3: never read or print a credential; never `rm -rf` a working copy; never fabricate a review record or receipt; the global HOLD; no L0–L2 asset in any Kāla run; root CLAUDE.md §N; the FROZEN orchestrator contract.

## §9 · Done at once (2026-10-15, owner's analysis session)

| Step | State |
|---|---|
| D-22.1 ruleset: 9 database/build jobs added as required checks (15 total); every name verified against the jobs the latest `main` runs report; 3 unreported job names excluded | done |
| D-23 COMMON_HEADER scope and ambiguity rules | done |
| D-24 `cx_post.sh` written, tested on a scratch repository, wired into `cx.sh` | done (see §10 proof) |
| D-22.3 hold-merges enforcement, D-25, D-26, D-27 | handed to the cockpit |

## §10 · Success measures (48 hours)

| Measure | Target |
|---|---|
| Red `main` push runs after a fleet merge | 0 (combined result tested before merge) |
| Jobs ending `blocked` on scope or an open question | 0 |
| Follow-up launch gap after a job finishes, p75 | under 15 min |
| Independent review jobs on document/plan-only PRs | 0 |
| Unrecorded restrictions found in agent instructions | 0 |
