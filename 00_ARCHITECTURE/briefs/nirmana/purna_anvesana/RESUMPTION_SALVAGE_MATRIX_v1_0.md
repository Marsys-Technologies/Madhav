---
artifact: PURNA_ANVESANA_RESUMPTION_SALVAGE_MATRIX
version: 1.0
status: PREPARED_NOT_AUTHORIZED_FOR_SOURCE_EXECUTION
date: 2026-09-27
base: 6b26f3ff05ee0aba3cdd964bce62292496ae6b62
---

# Pūrṇa Anveṣaṇa — semantic salvage matrix

## 1. Rule

Nothing is resumed by rebasing or cherry-picking the old integration branch wholesale. Every old
artifact is classified by meaning, revalidated against the current base, and either preserved,
selectively reimplemented, regenerated, or retired. Generated projections and status ledgers are
outputs, never implementation inputs.

Disposition vocabulary:

- **PRESERVE** — retain unchanged as governing intent, history, or evidence.
- **SELECTIVE SALVAGE** — carry the semantic behavior or test, not necessarily the old diff.
- **REVALIDATE** — source has changed since the review; inspect and test before deciding.
- **REGENERATE** — produce from current source after reviewed changes.
- **HISTORICAL ONLY** — retain for audit; never use as current truth.
- **EXCLUDE** — do not carry into the new candidate.

## 2. Governing corpus

| Source | Disposition | Reason / next use |
|---|---|---|
| Product definition and data-plane value architecture on protected main | PRESERVE | Product and layer boundaries remain governing. |
| `PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md` | PRESERVE | Complete lineage, consumer promise, evidence taxonomy, and original acceptance contract. |
| `PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md` | PRESERVE + REVALIDATE findings | Strong diagnosis at its evidence cutoff; individual source/live claims must be refreshed. |
| `PURNA_ANVESANA_CLAUDE_CODE_RESUMPTION_STRATEGY_v1_0.md` | PRESERVE | Governs isolation, preparation, waves, and authority sequence. |
| Existing `CAMPAIGN_DEFINITION.json`, acceptance protocols, empirical protocol | PRESERVE | Do not weaken denominator or hard gates. |
| Existing `CAMPAIGN_STATE.md`, `EVENTS.jsonl`, `LIVE_COMPLETION_MATRIX_v1.json` | HISTORICAL ONLY until regenerated | They contain useful lineage but also stale or refuted blockers/status claims. Append correction only after source execution is authorized. |

## 3. PR #2705 — `34991645b…`

| File/family | Disposition | Instruction |
|---|---|---|
| `CAMPAIGN_STATE.md`, `EVENTS.jsonl`, `LIVE_COMPLETION_MATRIX_v1.json` | HISTORICAL ONLY / REGENERATE | Do not transplant old completion/accounting claims. Rebuild status from the new branch after implementation evidence exists. |
| `platform/scripts/purna/__tests__/capability_coverage.test.ts` | SELECTIVE SALVAGE | Rebase the intended invariant onto the current corpus; do not retain stale counts or hashes. |
| `capability_estate_census.json`, `capability_knowledge.snapshot.json` | REGENERATE | Never cherry-pick generated artifacts. Generate once at packet boundary and review semantic diff. |
| `availability_contracts.test.ts` | SELECTIVE SALVAGE | Retain honest availability-contract coverage after the current proof model is revalidated. |
| `availability_coverage.test.ts` | SELECTIVE SALVAGE | Retain negative controls; update source-line allowlisting to stable pattern/identity matching. |
| `editorial_review.ts` | SELECTIVE SALVAGE | Extract only reviewed semantic rules that remain absent on current main. |
| `source_query_availability.ts` | SELECTIVE SALVAGE | Preserve useful capability proofs, but retype proof by capability kind and remove line-number coupling. |
| D7 classical-attribution unavailable test | SELECTIVE SALVAGE | Preserve fail-closed behavior and bind to the canonical replacement. |
| D7 Sūtrāvalī contract tests | SELECTIVE SALVAGE | Re-run against current D7 registrations before carrying. |
| `register_d7_channel.ts` | SELECTIVE SALVAGE | Port only missing contract/registration semantics. |
| `register_d8_assess_domain.ts` | SELECTIVE SALVAGE | Port only missing composite/availability semantics. |
| `classical_attribution_lookup.ts` | SELECTIVE SALVAGE | Preserve honest unavailable behavior or route to the reviewed canonical citation source. |

PR #2705 remains the principal code salvage library, not the resumption branch. Its old four golden
failures are its own artifact-regeneration inconsistency, not a dependency on PR #2704. Its nine
pinning findings are pre-existing zero-row probes whose exact-line allowlist entries drifted.

## 4. PR #2704 — `889ceaf9b…`

| Content | Disposition | Instruction |
|---|---|---|
| L3 campaign state/notice/dual-plan edits | EXCLUDE | L3-owned history; no Pūrṇa implementation dependency. |
| `CLAUDECODE_BRIEF.md` from L3 branch | EXCLUDE | Wrong campaign/worktree authority. |
| migration-dispatch changes and L3 dasha wrapper test | EXCLUDE from Pūrṇa salvage | Reconcile only through current main or explicit L3 coordination. |
| generated census/snapshot | REGENERATE | L3-bound hashes are not valid Pūrṇa outputs. |
| Beyond-Ācārya and route-port goldens | REVALIDATE, then REGENERATE if needed | The diff is semantic, not hash-only. Do not bless or transplant it mechanically. |

PR #2704 stays based on `codex/madhav-l3-claude-code`. Preparation makes no request to merge,
retarget, close, or modify it.

## 5. Dirty residuals

| Residual | Disposition | Instruction |
|---|---|---|
| Modified `register_d9_judgment.integration.test.ts` | SELECTIVE SALVAGE — TEST ONLY | Use as a statement of the desired served-array contract after the near-miss domain packet is ratified. |
| Untracked `register_d9_judgment.near_miss_contract.test.ts` | SELECTIVE SALVAGE — RED-FIRST TEST | Preserve the rejection of permanent `not_computed`; do not make it green by fabricating data. |
| `2026-09-17-purna-anvesana-focused-completion.md` | HISTORICAL ONLY | Superseded by the independent review and resumption strategy; useful for lineage only. |

The original dirty files remain in place and content-addressed copies exist under the preparation
preservation root. Do not apply either test before the candidate-set and eligibility decision is
recorded.

## 6. Independent-review root causes, refreshed against current main

| Review item | 2026-09-27 classification | Resumption action |
|---|---|---|
| RC-1 chart-wide latest-build proxy | **CONFIRMED IN SOURCE** | Replace with one shared per-asset generation resolver; generation tables exist in Supabase migrations 1035/1036 but population/live state requires fresh proof. |
| RC-2 orphan-row replacement fence | **CONFIRMED DEFECT SHAPE IN SOURCE; LIVE COUNT NOT REFRESHED** | Fix terminal-run semantics and add exact red/green tests; keep any repair migration separate and authority-gated. |
| RC-3 `ga_strength` receipt/rebuild | **LIVE STATE NOT REFRESHED** | Read-only verify current receipt/spec first; dispatch requires separate production authority and lease. |
| RC-4 near-miss producer absent | **CONFIRMED IN SOURCE** | Ratify candidate set and deterministic eligibility; then produce and consume honest absence signals. |
| RC-5 deep model/reasoning | **PARTLY SUPERSEDED** | Current main now selects `planner_deep`, supplies deep model overrides, and passes reasoning policy. Re-test provider/runtime propagation; do not rewrite blindly. |
| RC-5 adaptive continuation | **PARTLY SUPERSEDED / REVALIDATE** | Current compiler supports evidence-discovered frontiers and successors. Prove new-capability widening and multi-page managed exhaustion end-to-end before deciding a delta. |
| RC-6 fact register/delivery | **SOURCE HAS EVOLVED; REVALIDATE** | Current main emits accountability in MCP and Paripraśna persistence. Test that synthesis saw every registered fact and every managed door enforces delivery; repair only proven gaps. |
| RC-7 proof typing | **UNRESOLVED** | Type availability proof by capability kind and prove semantic presence, not mere reachability. |
| RC-8 idle control loop | **CONFIRMED HISTORICALLY** | Replace heartbeat-as-work with a runnable packet queue and event-driven waits. |
| RC-9 #2705/#2704 coupling | **CONFIRMED MISDIAGNOSIS** | Reconcile #2705 against current main; regenerate its own artifacts; leave #2704 with L3. |
| RC-10 web/MCP revision split | **STRUCTURAL, NOT AUTOMATIC DEFECT** | Prove protocol compatibility; demand same revision only if acceptance explicitly requires it. |

## 7. Preserve the architecture; replace only failed abstractions

Always preserve:

- federated SCUs and generated capability knowledge;
- deterministic Inquiry Contract and server-owned lifecycle;
- chart/build overlay, manifest bindings, immutable acceptance cases, and hard failure gates;
- managed Portal and managed MCP channels plus a conforming raw-client protocol;
- fail-closed evidence admission, pagination continuity, citations, and auditable accountability;
- the five original cases, 34 route obligations, 30 product scenarios, and empirical evaluator.

Replace or elevate:

1. the chart-level latest-completed-build proxy with per-asset served-generation truth;
2. replacement fencing that mistakes terminal orphan rows for active work;
3. permanent `not_computed` near-miss output with a ratified deterministic producer;
4. any remaining planner/continuation/delivery gaps proven on current main;
5. source-type availability with capability-kind proof;
6. heartbeat repetition with packet-completion execution control.

## 8. Integration rule

For every salvaged behavior, record: old source SHA, current-base comparison, selected semantic
invariant, new tests, affected generated outputs, and why the new implementation is smaller or safer.
If that record cannot be written, the content is not ready to enter the resumption branch.
