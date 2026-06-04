---
artifact: PARIKSHA_MASTER_PLAN_v1_0.md
version: 1.0
status: LIVE
authored_at: 2026-05-31
role: Authoritative architecture for the Pariksha QA + remediation swarm.
---

# Pariksha Master Plan v1.0

## Mission

For every new guest, autonomously verify the entire chart-build workflow
(stages 1-6 from intake through live build observation), diagnose any
break, fix workflow-blocking issues on the fly, and produce a per-build
quality report. The system must work for ANY guest — no per-user reference
data, no JH oracle, no preconfigured truth set.

**Out of scope.** Stage 7 (consume) — Prashna is a separate function with
its own quality concerns; Pariksha treats build completion as its terminal
event. A separate Prashna-Pariksha may be authored later.

## Scope summary — 6 stages

| Stage | Sanskrit | What | Surface |
|---|---|---|---|
| 1 | Aapti · आप्ति | Identity capture | `/clients/new` → `/api/clients/create` → charts row |
| 2 | Prarambha · प्रारम्भ | Build initiation | `/clients/<id>/build` → click Build → Cloud Run Job execute |
| 3 | Adhara nirmana · आधार निर्माण | L1 foundation build | 8 L1 writers × 5 ayanamshas |
| 4 | Sambandha nirmana · सम्बन्ध निर्माण | L2.5 synthesis build | 5 L2.5 writers per ayanamsha, after L1 complete |
| 5 | Sutra nirmana · सूत्र निर्माण | L3 meta-thread build | 8 L3 writers per ayanamsha, after L2.5 complete |
| 6 | Drishti · दृष्टि | Live observation | SSE accretion + cockpit progress + telemetry |

## Agent roster — 6 watchers + 3 meta

### Watchers

1. **Drashta** — front-end walker. Drives portal as guest. Logs UX issues.
2. **Aapti-Drashta** — Stage 1: form → API → DB contract + integrity.
3. **Yantra-Drashta** — Stages 2, 6: cockpit render + SSE + state machine.
4. **Tantra-Drashta** — Stages 3, 4, 5: per-writer row-count + schema + determinism.
5. **Sambandha-Drashta** — Stages 3, 4, 5: DAG order + edge coverage + layer-completion gates.
6. **Pramana-Drashta** — post-build internal-consistency battery. **No external parity oracle, ever.**

### Meta

7. **Pratisamhita** — reconciler. Dedupes + ranks issues across watcher signals.
8. **Vaidya** — fix agents. Conductor-pattern. PR-only.
9. **Naya-Pariksha** — re-runner. Closes the loop after each Vaidya PR merges.

## Coordination — Issue Ledger

All agents write to `00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/issues.yaml`.
Schema in `ISSUE_LEDGER_SCHEMA.md`. Race-resolved via git push.

## Per-build lifecycle (the new requirement)

Pariksha activates automatically when a new chart is created:

```
1. POST /api/clients/create → new charts row → triggers Pariksha hook
2. Hook spawns Pariksha-Sutradhara (orchestrator) for this chart_id
3. Sutradhara creates 00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/
   with manifest.yaml + empty issues.yaml + empty resume_state.yaml
4. Sutradhara activates the 6 watcher agents, all bound to this chart_id
5. Watchers observe in parallel as guest progresses through stages
6. Pratisamhita reconciles every 60s; Vaidya may fire mid-walk for blockers
7. On build_complete event, Pramana runs the internal-consistency battery
8. Sutradhara writes the final REPORT.md
9. Cockpit shows a "Pariksha pass/fail" pill linked to the report
```

**Hook mechanism (P3+).** Synchronous webhook from `/api/clients/create`
that spawns the Pariksha arc. Until P3, manual operator invocation
(paste KICKOFF_PARIKSHA_ORCHESTRATOR.md).

## Resume protocol (new requirement)

If the Drashta walk breaks mid-flow (auth expires, browser crashes, network
drops), the next Pariksha invocation must resume from the break point, not
restart. Full spec in `RESUME_PROTOCOL.md`. Key idea:

- Every Drashta step writes a checkpoint to `resume_state.yaml`
- Each checkpoint records: stage reached, screenshot path, page URL, last
  successful action, next expected action, recoverable state to restore
- A new Drashta invocation reads `resume_state.yaml`, navigates to the
  checkpoint URL, restores state (re-fills the form if mid-fill, re-auths
  if needed), and continues from the next expected action
- Resume is also surfaced in the cockpit: a small "Pariksha resume" banner
  on the same screen the break occurred on, with a "Continue" button

## Investigate-and-fix-on-fly (new requirement)

For `workflow_blocking` severity issues, Vaidya activates mid-walk:

```
Drashta hits a workflow-blocking issue
    │
    ├── Drashta pauses, writes resume_state.yaml checkpoint
    │
    ├── Pratisamhita ranks issue as workflow_blocking
    │
    ├── Vaidya activates with a tight remediation scope
    │   (see REMEDIATION_PROTOCOL.md for fix scoping rules)
    │
    ├── Vaidya authors patch, opens PR
    │
    ├── For high-confidence single-file fixes, Vaidya may auto-merge after
    │   green CI (operator pre-authorizes per arc; see REMEDIATION §safety)
    │
    ├── Wait for auto-deploy
    │
    ├── Naya-Pariksha re-runs the walk from the checkpoint
    │
    └── If issue resolved → continue. If recurs → escalate to native review.
```

The cockpit's "Pariksha resume" banner shows "Fix in flight (PR #N)" during
this loop. Operator can watch live.

## Data asset quality (new requirement)

Per-asset quality criteria documented in `ASSET_REGISTRY.md`. Pramana-Drashta
reads this registry and verifies each asset against:
- Expected row count per ayanamsha (deterministic per spec)
- Schema compliance (NOT NULL, CHECK, FK)
- Cross-asset structural invariants (e.g., A9 MSR signal IDs referenced by
  A10 CGM edges must exist in A9's signal table)
- Determinism (rebuild produces byte-identical output)
- Layer-completion gate (L1 done before L2.5 starts)

`EXPECTED_ROW_COUNTS.yaml` is the machine-readable side of the registry.
Pramana queries it directly.

## Operator authorization tiers

Per-arc, operator declares one of:

- **Observe only** — agents log issues, no fixes attempted (P1-P2 default)
- **PR-only fixes** — Vaidya opens PRs, operator reviews + merges (P3-P4 default)
- **Auto-merge low-risk fixes** — single-file diffs ≤30 LOC with green CI auto-merged; everything else PR-only (P5 default)

Always: operator can `touch 00_ARCHITECTURE/PARIKSHA/STOP` to halt all agents.

## File hygiene

- Build artifacts under `builds/<chart_id>/` are NOT committed to main
  (in `.gitignore`). They're per-run ephemeral state.
- The final REPORT.md IS committed if the operator wants persistent audit
  trail (P3+ convention).
- Screenshots compressed + cleaned at arc close to stay under repo size limits.

## Open questions for native (resolve before P1 kickoff)

These are the 8 forks the prior session enumerated:

1. P1 or jump deeper? (recommend P1)
2. Drashta walk scope: minimum vs extended? (recommend minimum first)
3. Vaidya merge policy: PR-only vs auto-merge under threshold? (recommend PR-only)
4. Arc-mode vs persistent per-build hook? (recommend arc-mode P1-P2, persistent P3+)
5. Antigravity vs Cloud Run Job? (recommend Antigravity for MVP)
6. Severity floor for auto-fix? (recommend workflow_blocking only)
7. Pramana blocking behavior on fail? (recommend FLAG only at P1, BLOCK later)
8. Hook mechanism: Cloud Scheduler vs synchronous webhook? (recommend synchronous webhook from /api/clients/create at P3)

Operator answer to (3) and (6) determines what scope Vaidya can take in P1's
investigate-and-fix-on-fly behavior. If "observe only," skip Vaidya entirely.
