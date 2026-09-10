---
artifact: PARIPRASHNA_TRACKER_ELEVATION_RUNBOOK
version: 1.0
status: SHADOW_ONLY
authority: Native decision required for any accepted-runtime cutover
---

# Paripraśna tracker elevation runbook

The accepted record remains the loopback P0B/P1 control-plane runtime. The elevation is a separate SQLite shadow ledger and loopback dashboard; it must never read, write, restart, or replace the accepted runtime in place.

## Authority boundary

- The plan registry carries P0–P7, S1–S6 and a catalogue for P-PIPE, P-PORTAL, P-GUIDED, PPR and EDIR.
- Historical v2 sources are observations only. Their SELF_PAUSED state, countersigned-gate absence, P-PORTAL halt, EDIR entries and historic verdicts cannot create active progress, evidence, gate or native-acceptance credit.
- A Native Surrogate may register a candidate and record impact dispositions. Only an independent verifier can classify an observed artifact as evidence. Neither operation closes a gate or permits cutover.
- A green test, GitHub merge, CI result, adapter response, or attested candidate release is not a cutover decision.

## Shadow adapters and freshness

The shadow dashboard has named adapters for Codex tasks, GitHub PR/CI/merge queue, Git/worktrees, deployed runtime identity, tests/evidence, and EDIR. Each keeps its own cursor, observed timestamp and freshness budget. Unconfigured, stale, invalid or retrying sources appear as `UNKNOWN`, `STALE`, or quarantined; they do not render green.

## Operations

`elevation_operations.py` produces three **shadow-label-only** launchd job specifications: continuous adapter synchronization/watchdog, daily immutable snapshots with a minimum 7-day retention floor, and weekly restore verification. Its snapshot and restore routines create private shadow SQLite copies and compare an isolated restored projection; they do not touch the accepted runtime. Launchd installation, source-probe credentials, alert delivery and retention deletion remain deployment work until an immutable release, protected merge/CI and deployment authorization are evidenced.

## Cutover packet

Before any accepted-runtime change, publish an independently reviewed packet containing:

1. frozen plan revision and impact dispositions;
2. source-by-source freshness, quarantines and contradictions;
3. accepted-runtime versus shadow projection comparison;
4. attested immutable candidate release and protected-PR/CI evidence;
5. snapshot, restart, restore and rollback results; and
6. independent deployed verification.

The code fails closed unless all packet conditions are present. The final live-runtime swap remains a native decision; this runbook does not pre-authorize it.
