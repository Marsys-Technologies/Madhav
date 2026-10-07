---
artifact: NATIVE_DIRECT_RULINGS_20261006
version: "1.0"
status: RECORDED_NATIVE_DIRECTION
date: 2026-10-06
recorded_at: 2026-10-06T20:16:15+00:00
campaign_id: kalayantra
item: B-5
recorder: ADHIKARIN
ruling_id: NR-KALA-AUTONOMY-20261006
governing_charter: 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md
changelog:
  - "1.0: Record the native's existing delegation, absorbed-writer quiescence, stream registration and preservation evidence. No new campaign decision."
---

# Pravāha ownership hand-over to KĀLA-YANTRA

## Native direction

The following is the native's wording as recorded in the KĀLA-YANTRA campaign
charter §1, under `NR-KALA-AUTONOMY-20261006`:

> "the plan for me is to execute this Kāla strategy plan … I want to do it in a way that it is successfully implemented without fail. … in a different work tree so that it does not impact the other work … high throughput, running in parallel wherever possible and sequentially wherever essential … optimise the entire development and CI/CD deployment. Very importantly, I want to cut the governance and security-related overwork to only the essential and minimal … fully autonomous … a complete agentic swarm … The Gochara 5 has been mostly implemented, if not completely. It should be fully absorbed. We should not lose that work. There should be no human gates, no approval from humans. Have an owner surrogate or a native surrogate to address any requirements so that the execution can happen fully autonomously. … implement this very focussedly, without digressions, without idle time, with high throughput, targeting the completion of all the assets and the campaign. Don't bother with other digressions which exist."

The steward role and the reserved Pravāha decisions pass to **ADHIKĀRIN** under
charter §2.3 and surrogate-charter G5–G8 / standing ruling KYD-6. This document
records that existing delegation; it does not issue a new KYD, decide a pending
item or lift any hold during bootstrap. Evidence gates, frozen contracts and
human-reserved credential/IAM, budget and HOLD powers remain as specified by
the governing charter.

The native's later direction `NR-KALA-DIRECTION-20261007`, already recorded in
charter §1, governs the eventual flip: evaluation results are run and recorded
as a tuning baseline; engineering correctness still gates publication. This
hand-over authorizes no dispatch, teardown, publication or out-of-phase merge.

## Writer exclusion and retained state

Observed at `2026-10-06T20:15:29.986922+00:00`:

- `pgrep -f 'pravaha_tracker\.(runner|steward_watch)( |$)'` returned 1 with no
  PID. `launchctl list` had the Pravāha tracker only, no runner/steward service.
- A successful `lsof` cwd probe across 107 candidate Kimi/Claude/Codex/Pravāha
  processes found no process rooted in the absorbed Pravāha or Gochara
  worktrees. This is a local-writer observation, not a claim that remote jobs
  have finished.
- `RUNNER_STOP_A`, `RUNNER_STOP_B`, `RUNNER_STOP_C` remain present. The retired
  runner C launchd plist remains in `run/retired/`. Runner logs end on October 1
  (A/B) and October 4 (C); their tails and hashes are in the evidence record.
- The original event-log prefix (5,354 events), 269 unacknowledged messages,
  item owners, STOP/quota state, runner logs and dirty-worktree inventories were
  recorded before mutation. No event is rewritten or acknowledged; no item is
  reassigned or completed. Existing job identifiers remain in their original
  append-only event records. The final prefix comparison and message receipts
  are in the evidence record.
- Dirty work remains in place: 11 status entries in `gochara-wp0-7`, 65 in
  `pravaha`, none in `pravaha-a` or `pravaha-b`. Only the explicitly authorized,
  previously untracked live Pravāha `plan_model.json` is edited there.

One KĀLA-YANTRA worker at a time may subsequently own an inherited item. Its
registered branch and claim identify that writer. Old A/B sessions and runner C
remain stopped; their retained tracker states are not evidence of a live writer
or permission to restart one. J-0 inventories and assigns inherited work only
after B-7, with the twelve landing phases in charter §2.3 binding every PR.

## Stream registration and measurements

Both stream definitions retain their previous worktrees and accept all ten
KĀLA-YANTRA lane worktrees, `kalayantra/j-*` branches and `pravaha/*` branches.
The existing A `l3/gochara-*` and B `campaign/pravaha` branches still match.
Only `streams[*].worktrees` and `streams[*].branch_pattern` change. All 102
items, their owners, detectors, dependencies and decisions are unchanged.

The committed model and live tracker model at
`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/control/pravaha/plan_model.json`
have identical SHA-256:
`39c10735591a686bffcc897990367c886bc74027b6873191befca6f9a958e7ee`.

Measured locally:

- `pytest .../test_pravaha.py::TestModelChecker`: **2 passed**, including
  `test_real_model_is_clean`.
- Live `pravaha preflight --stream A` and `--stream B`: **exit 0** from this
  lane on local branch `kalayantra/j-b5-preflight`. No commit or push was made
  on that branch; the worktree returned to `kalayantra/n-b5` immediately.
- Counterexample: remove this lane's registration in a temporary model and
  repeat both preflights with a temporary event log: both **exit 4**, reporting
  the unregistered worktree. The failing probes never write the live event log.

These are author checks, not independent acceptance. `v1` must accept the exact
review head, and SŪTRADHĀRA integrates this branch into the bootstrap PR.

## Preservation and hand-off evidence

`../run_records/2026-10-07/B5_HANDOVER_EVIDENCE.json` contains the observations,
before/after preservation assertions, model hashes, live preflight results,
negative probes, archive inventory and steward-to-A/B message receipts.

The tracker package, model, measuring-build contract, review records and admitted
run records inherited from B-1a remain tracked. The two secret-scan exclusions
stay on their original disk locations and are not read or copied by this item.
Full live event/snapshot/runner-log/backup archival remains J-8a's close duty.

Bootstrap delivery is `kalayantra/n-b5`; review is requested through
`/Users/Dev/kalayantra/run/bootstrap/B-5.request.json` only after the checks
complete. A legacy detector showing DONE is advisory and never merge authority.
