---
artifact: PARIKSHA/README.md
version: 1.0
status: LIVE
authored_by: Cowork (planning)
authored_at: 2026-05-31
role: Operator playbook for the Pariksha autonomous QA + remediation swarm.
---

# Pariksha · परीक्षा · The Examination Swarm

Multi-agent system that observes every new client's build end-to-end,
diagnoses issues, fixes blockers on the fly, and produces a per-build
quality report. Runs automatically for every guest's first build.

## Quick start (operator)

```
1. Open a fresh Antigravity Claude Code window.
2. Paste contents of kickoffs/KICKOFF_PARIKSHA_ORCHESTRATOR.md
3. Provide a chart_id (or "spawn-new-guest" to have the orchestrator
   create a synthetic guest)
4. Walk away. The orchestrator spawns child agents, walks the build,
   diagnoses + fixes blockers, produces a final report.
5. Read 00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/REPORT.md
```

## What's in this directory

```
PARIKSHA/
├── README.md                          ← you are here
├── PARIKSHA_MASTER_PLAN_v1_0.md       ← architecture, agent roles, lifecycle
├── ISSUE_LEDGER_SCHEMA.md             ← issue YAML schema (shared across agents)
├── EXPECTED_ROW_COUNTS.yaml           ← per-asset row count spec (Pramana reads)
├── ASSET_REGISTRY.md                  ← detailed spec for each of 28 assets
├── RESUME_PROTOCOL.md                 ← break-recovery: kick off from same screen
├── REMEDIATION_PROTOCOL.md            ← on-the-fly fix scoping + safety rails
├── briefs/
│   ├── DRASHTA_v1_0.md                ← P1: front-end walker
│   ├── PRAMANA_DRASHTA_v1_0.md        ← P1: internal-consistency oracle
│   ├── AAPTI_DRASHTA_v1_0.md          ← P2: form/API/DB watcher (placeholder)
│   ├── YANTRA_DRASHTA_v1_0.md         ← P2: cockpit + SSE watcher (placeholder)
│   ├── TANTRA_DRASHTA_v1_0.md         ← P3: pipeline watcher (placeholder)
│   ├── SAMBANDHA_DRASHTA_v1_0.md      ← P3: dependency watcher (placeholder)
│   ├── PRATISAMHITA_v1_0.md           ← P4: reconciler (placeholder)
│   ├── VAIDYA_v1_0.md                 ← P4: fix agents (placeholder)
│   └── NAYA_PARIKSHA_v1_0.md          ← P5: re-runner (placeholder)
├── kickoffs/
│   ├── KICKOFF_PARIKSHA_ORCHESTRATOR.md
│   ├── KICKOFF_DRASHTA.md
│   └── KICKOFF_PRAMANA.md
└── builds/                             ← per-build artifact directories
    └── <chart_id>/
        ├── manifest.yaml               ← guest metadata + agent roster
        ├── issues.yaml                 ← live issue ledger
        ├── resume_state.yaml           ← Drashta walk progress + checkpoint
        ├── REPORT.md                   ← final per-build report
        └── screenshots/                ← Drashta's visual evidence
```

## Phase rollout

| Phase | Adds | Time | Outcome |
|---|---|---|---|
| **P1** | Drashta + Pramana + ledger | 1 day | First per-build report on any guest |
| **P2** | Aapti + Yantra | +1 day | Backend correlation with UI symptoms |
| **P3** | Tantra + Sambandha + per-build hook | +1.5 days | Permanent fixture; every new guest auto-Pariksha'd |
| **P4** | Pratisamhita + Vaidya (fix-on-fly) | +1.5 days | Wake to PRs queued for top blockers |
| **P5** | Naya-Pariksha closed loop | +0.5 day | Regression-catch after each Vaidya merge |

This README + MASTER_PLAN + the P1 briefs ship now. P2-P5 briefs are
placeholders that get fleshed when their phase opens.

## Safety rails (always on)

- All Drashtas read-only. Only Vaidya writes code, and only via PR (no auto-merge).
- Vaidya respects strict `may_touch` scopes per issue. Cross-issue conflicts halt.
- A file `00_ARCHITECTURE/PARIKSHA/STOP` halts all agents within 60s.
- No prod DB writes from agents. All DB changes flow through migrations + auto-deploy.
- Per-arc session budget (default 50). Coordinator stops spawning when hit.
- Per-issue Vaidya retry budget (default 2). Then halt + escalate to native review.
