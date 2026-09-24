---
artifact: L0_REPAIR_ANALYSIS_REPIN_DECISION_ADDENDUM
canonical_id: L0_REPAIR_ANALYSIS_REPIN_DECISION_ADDENDUM
version: "1.0"
status: ADDENDUM_TO_L0_REPAIR_REPIN_APPROVED
decision_id: NATIVE-2026-09-24-L0-REPAIR-REPIN
date: 2026-09-24
amends: 00_ARCHITECTURE/briefs/nirmana/L0_REPAIR_ANALYSIS_REPIN_DECISION_v1_0.md
recorded_by: "Claude Code session (scribe)"
---

# Addendum — corrected source commit and re-anchored baseline

The decision brief is byte-pinned by the pins tool (sha256 in `AUTHORITY_BINDINGS`),
so it is left exactly as recorded. This addendum records two facts that differ
from what the brief states, so neither is hidden.

## 1. The approved state and the pinned source commit are different commits

The brief anchors the approval to `101171f76517fa3c6b0b44fa9d1cc46358612eee` and
says the successors use the same commit as their source. That could not be kept.

The writer-digest inventory committed at `101171f76` was **stale**: it was
regenerated in `0ff9a32b2`, and `2d3b25fb2` then edited comments in
`l0_phaladeepika_vedha.py` and `service_probes.py`. A writer digest hashes file
bytes, so comment-only edits still moved 25 writers (`bg_phaladeepika_latta`,
`bg_vedha_malefic_scale`, 23 `bo_`) and the probe digest. The session did not
notice, and `provenance_inventory --check` failed from `2d3b25fb2` onward. The
approval was given against that state.

A successor's source commit must carry an inventory equal to the live one, so no
commit at or before `101171f76` can be a valid source. The corrected inventory is
committed in `7d40f8c706406ee8187eadb5c3930553800a1a4a`, which is now the pinned
source and convergence commit. `101171f76` stays the approval identity
(`authority_commit`).

**Nothing the approval covered changed.**
`git diff 101171f76 7d40f8c70 -- platform/python-sidecar` is empty: the writer
sources are byte-identical. The changed-asset set is unchanged (38 assets: 9 L0,
23 L2, 6 L3, each already inside the approved scope). Only the digest values of
those 25 writers differ, being the values that were always the true ones.

## 2. The protected baseline moved

The brief names `954d6c119` as the protected baseline. `main` advanced to
`0dcf28d6d8617a270660efd7799176e73e07a859` (three docs-only commits, none touching
the pins, the writers, the tool, or any file this PR edits). The tool requires each
newly archived predecessor to name the baseline current at merge as its historical
snapshot, so the successors were re-admitted against `0dcf28d6d`. The brief
anticipated this (§5.4). The re-admission changed only the three
`historical_snapshot_commit` references.

If `main` advances again before merge, the same re-admission applies; the decision
is unchanged.

## 3. What this does not change

Approval text, scope (L0/L2/L3 only), classifications, and the standing conditions
in the brief's §5 (notably: do not rebuild L3 until the `uncited_extension` hazard
is fixed) all stand as recorded.
