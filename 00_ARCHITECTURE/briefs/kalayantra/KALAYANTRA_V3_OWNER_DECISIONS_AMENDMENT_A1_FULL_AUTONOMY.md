---
title: KĀLA-YANTRA v3 owner decisions — Amendment A1 (full autonomy)
version: 1.0
status: CURRENT
date: 2026-10-13
amends: KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md (D-6, D-7, D-9), KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md, KALAYANTRA_RELAUNCH_PLAN_v2_7.md (§6, §10, §14–§16)
precedence: where this amendment and any of the amended documents disagree, THIS AMENDMENT GOVERNS. The amended files are left byte-identical on purpose: every packet pins their hashes, and re-pinning every packet would stop the work this amendment exists to start.
changelog:
  - 1.0 (2026-10-13): created on the owner direction of 2026-10-13 ~20:15Z; text = the owner-surrogate ruling, answer 13.
---

## 2026-10-13 (night) — owner direction: full autonomy (native, in chat, 20:15:46Z; recorded verbatim in
## run/PLANNER_STATE.json active.owner_direction_full_autonomy_20261013) and delegated calls D-10…D-15
## (delegate: the persistent owner surrogate, Claude Fable 5.1 high; instruction: "amend them first so that this
## goes without any interruption till the very end")

**Owner direction (native):** fully autonomous to the end; no waiting for the owner; merges by the fleet/cockpit;
whatever infrastructure and resources are needed are allotted; a Fable 5.1 (effort high) owner surrogate
decides on his behalf; governance and security principles that conflict with full autonomy are amended first;
Codex unless Claude is absolutely necessary; highest implementation velocity. Kept by the owner: never read or
print a credential; never `rm -rf` a working copy; never fabricate a review record or receipt; the global HOLD as
the emergency brake; no L0–L2 asset in any Kāla run. Cut by the owner: the final-manifest/final-receipt tool;
rehearsal, coverage and backfill as gate conditions; fixture mode for model jobs; the planner/conductor model
loops (the cockpit session is planner and conductor).

- **D-10 Merges (replaces D-5, D-6 and D-6 revised).** The fleet merges every PR that has an independent ACCEPTED
  verdict at its current head and green required CI (`Kāla DB Tests` where the diff is relevant): the dispatcher's
  MERGE kind submits `gh pr merge --squash --auto --match-head-commit <head>` at once; `run/HOLD_MERGES` is lifted
  and is re-created automatically only by the stop rule in D-14. Every main merge deploys; that is accepted. The
  certification hold no longer blocks merges (Strategic Suvarṇa has completed). Protected-window migrations: the
  surrogate's recorded go/no-go is the approval; the cockpit records it on the pending deployment through the
  GitHub API on the owner's account (`POST repos/{o}/{r}/actions/runs/{run}/pending_deployments`, state
  `approved`, comment = the decision id); no human click is awaited.
- **D-11 Start/resume (replaces D-3 and D-7).** The N-467 resume is this direction. The cockpit writes
  `run/OWNER_RESUME.json` (binding N-467; `decided_by {kind: owner, id: "owner direction 2026-10-13T20:15:46Z,
  PLANNER_STATE active.owner_direction_full_autonomy_20261013"}`; `waiver.final_acceptance: true` citing the same
  direction) as soon as the gate honours the waiver. No veto window; no conductor loop.
- **D-12 Owner-waits and veto classes (amends D-4).** Every owner-wait, including the former veto classes
  (protected-window approval, campaign start/resume, plan-bundle changes, capacity above the configured
  maxima), is decided by the surrogate and is effective at once when recorded (run/DECISIONS_SURROGATE.jsonl
  and the tracker); the 30-minute window is 0; the veto loop is not loaded. The owner may still reverse any
  decision by `veto <id>` or `pause`; an owner `pause` is never undone by the surrogate. Hard stops that
  remain: a FROZEN-contract change (root CLAUDE.md §L/§N.2, the native's own rule, not lifted); production
  data deletion or restore; credentials; `ri02`. Changes to this decisions file after this block are recorded
  as delegated calls under this direction.
- **D-13 Production operations (new).** Authorised in this order and no other: verified backup (create, restore
  into a scratch target, row-count/hash comparison) → the bounded rebuild named in the owner's record of
  2026-10-13 (ka_yojaka → ka_sangam → ka_vighnakara → ka_gochara, ka_gochara_v3_century_materialize,
  ka_gochara_v4_41_candidate, ka_gochara_v5, ka_vedha_gochara → ph_muhurta; ka_avadhi excluded; no L0–L2
  asset) → readback and census recorded. The surrogate gives go/no-go against those conditions; stop at the
  first failure, no retry that writes; the executor is started by the cockpit in the one permitted form
  (D-15); no owner switch. Operations are enabled in the executor table by the surrogate's recorded decision
  once their scripts are built and dry-run verified.
- **D-14 Automatic stops (new).** Without a human in the loop the fleet stops itself on: the global HOLD; a
  REJECTED verdict twice on one item at the same head (the item parks, the surrogate decides rework or
  retirement); required CI red on `main` after a fleet merge (`HOLD_MERGES` is re-created, a fix-forward REWORK
  is dispatched, no further merge until main is green); any production operation failure (HOLD is created, the
  run ends, the surrogate reports); a FROZEN path in a diff (block, never overridden); a credential name in a
  job environment (never launched). Each stop is journalled and notified; none waits for the owner unless it
  is a hard stop of D-12.
- **D-15 The credential rule, operational form (keeps the owner's rule).** The cockpit never reads, prints,
  copies or inspects `~/.config/kalayantra/executor.env`. The only permitted use is starting the executor:
  `bash -c 'source ~/.config/kalayantra/executor.env && exec /Users/Dev/kalayantra/fleet_live/executor.sh up'`
  — the file passes through that shell into the executor process alone; no `env`, `printenv`, `set`, log or
  redirect of that shell; the job environment whitelist stays as built.
- **D-16 Resources (new).** Pools are set to what the machine bears (start 8 builders / 4 verifiers); the
  working-copy ceiling in the dispatcher (`ALL_COPIES_MAX`) is raised to 24 all / 16 own by a reviewed change,
  finished copies of completed campaigns are removed under the owner's own policy (dirty ones bundled to
  /Users/Dev/Archives first), and the owner's policy file is noted as superseded for this campaign's duration.
- **D-9 amended.** Installation still uses an independently accepted, immutable head bound in the receipt; the
  assembly is no longer "never merged": it is merged to main as the first autonomous merge (§2 of answer 13),
  so the campaign checkout tracking origin/main carries the fleet's own code.
