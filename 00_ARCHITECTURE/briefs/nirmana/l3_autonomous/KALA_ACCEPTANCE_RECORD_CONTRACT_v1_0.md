---
artifact: KALA_ACCEPTANCE_RECORD_CONTRACT
canonical_id: KALA_ACCEPTANCE_RECORD_CONTRACT
version: "1.0"
status: CURRENT
date: 2026-09-24
decided_by: "L3 Kāla strategic session (madhav-fc), under the native's delegation — KALA_DELEGATED_DECISIONS D-H"
mirrors: "MADHAV_DATA_PLANE_L2_PRODUCER_READY_ACCEPTANCE_v1_0.md (frontmatter shape)"
---

# Acceptance records for `CONSUMER_INTEGRATED` and `VALUE_EVALUATED`

The data-plane ladder is not an enum. Each state is earned by an **acceptance record**: a markdown
artifact whose frontmatter pins what was accepted, on which commit, under which authority. The
records for `PRODUCER_READY` exist for L0, L1 and L2. None exist for the two states the Kāla
headline's first number depends on. This contract defines them in the same shape, so the headline
can move without any code change.

## Common frontmatter (identical to the existing records)

```yaml
artifact: MADHAV_DATA_PLANE_L3_<ASSET>_<STATE>_ACCEPTANCE
version: "1.0"
status: <STATE>_ACCEPTED            # CONSUMER_INTEGRATED_ACCEPTED | VALUE_EVALUATED_ACCEPTED
authority: DP-SD-0NN
execution_base: <sha>               # main at acceptance
strategy_content_pin: <sha>
strategy_approval_pin: <sha>
implementation_commits: [<sha>, …]
accepted_by: "<session or person>, NOT the packet's author"
next_stage_hold: "<what the next state still waits on>"
```

## `CONSUMER_INTEGRATED` — evidence that must be in the body, or the record is void

1. **A named receiving operator** (an L3-U packet or a serving capability) with its **live call
   path** as `file:line`, verified on `execution_base`.
2. **An L3-owned sentinel test** that fails if the operator stops reading the field. A green test
   that could not go red is not evidence (§N.8).
3. The **object** consumed (§3.1 of the blueprint) and the **fields** read, by name.
4. The honest gap: any consumer question (L3-Q) the integration does *not* yet serve.

## `VALUE_EVALUATED` — evidence that must be in the body, or the record is void

1. The **frozen baseline** run (`KALA_BASELINE_v1_0.md`) before and after, on the same thirteen
   questions, three proving cases and ordinary period.
2. The **distinction named** (Product §1.3, F03) and the **ablation** showing which asset earned it.
3. The **added error and burden counted** (Product §14).
4. The evaluator, who is not the author, and the exact commands a reader runs to reproduce.

## Rules

- A record with a missing evidence item is not "partial"; it does not exist. Write the gap, not
  the record.
- `Delivered N/22` counts only assets with **both** records plus `DEPLOYED_ACCEPTED`.
- Never relabel or rewrite an accepted record. A correction is a new version with the old retained.
