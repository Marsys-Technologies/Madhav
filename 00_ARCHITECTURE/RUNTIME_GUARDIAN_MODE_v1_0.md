---
artifact: RUNTIME_GUARDIAN_MODE_v1_0.md
canonical_id: RUNTIME_GUARDIAN_MODE
version: 1.0
status: CURRENT (operating mode — native-authorized runtime guardianship, 2026-06-03)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-03
extends: BUILD_GUARANTOR_SWARM_CHARTER_v1_0 (§B workflow scope, §E roles) + BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0 (rails, budgets)
decision: >
  Native directive 2026-06-03: run the swarm as a RUNTIME GUARANTOR of the live chart-build workflow.
  The native (or Drashta) drives the real portal; the swarm watches the data flow form → L0 → L1 → … → L5,
  and autonomously detects + fixes ANY defect anywhere in the chain (UI/UX, workflow, execution, deploy,
  continuity) in real time, fixing-and-continuing until the chart's data exists end-to-end. No human gate.
---

# Build-Guarantor Swarm — Runtime-Guardian Mode v1.0

## §A — Mandate
The swarm guarantees a **live chart build flowing through the real product** (`madhav.marsys.in`), not a
queue of code-build sessions. The watched path is the whole workflow — birth-data form → save → Build →
L0 check/bootstrap → L1 generation → cascade L2→L3→L4→L5 → consume-ready. Any defect at any stage is
detected and fixed at runtime, and the build resumes from the failure point. The native supplies the chart;
the system makes the data flow all the way up.

## §B — The watched path + the gate at each stage
| Stage | What must happen | Guardian role |
|---|---|---|
| Birth-data **form** | opens, validates, saves a chart | Drashta (UI walk) |
| **Save** | chart persists, appears on dashboard | Drashta + Pramāṇa |
| **Build** trigger | the button fires a real build job (not a no-op) | Drashta + Pratiṣṭhā |
| **L0 / Brahmagyan** | global data present; **if empty → bootstrap it, then proceed** | Sambandha + Pramāṇa |
| **L1 Gaṇita** | engine runs on the chart → real facts (positions, dashas…) land | Pramāṇa |
| **L2→L5 cascade** | each layer derives real data from the layer below, in dependency order | Sambandha + Pramāṇa |
| **Cockpit / consume** | the Layer Tower shows live progress; consume answers on real data | Darpaṇa |

## §C — Roles at runtime (every defect class has an owner)
- **Drashta** — browser automation against the live portal: drives the form, clicks Build, reads the cockpit; owns **UI/UX + workflow** defects.
- **Pramāṇa** — verifies each layer's generated data as it lands (real rows, correct values); owns **execution/data** defects.
- **Sambandha** — asserts each layer's dependencies actually produced data before the next runs; owns **continuity** defects (no silent skips).
- **Darpaṇa** — asserts the cockpit/consume surfaces render what was computed; owns **render** defects.
- **Pratiṣṭhā** — confirms any mid-run redeploy is actually live; owns **deployment** defects.
- **Praharī** — watchdog: stalls/timeouts → resume; owns **liveness**.
- **Racayitā · Śilpī · Sūtradhāra** — the fix-and-continue engine: draft fix → patch → redeploy → resume.

## §D — The defect → fix → continue loop (event-driven)
When any role flags a runtime defect: Racayitā drafts a targeted fix → Śilpī patches the code → CI green →
Pratiṣṭhā confirms the redeploy live → the build **resumes from the failure point** (not from scratch; Smṛti
holds the live-build state). Bounded retries (`MAX_FIX_ATTEMPTS=5`) → **park** the defect + log to
`DATA_CORRECTNESS_BACKLOG`, and continue with everything still buildable. The run ends when L5 holds real data
and consume answers on the chart — or when the remaining defects are all parked.

## §E — Honest data gates (the difference between real and hollow)
"Reached L5" must mean **real data reached L5**, not "gates relaxed until it passed." So the data gates stay
strict: **positions verified vs Swiss Ephemeris / JPL (astronomical ground-truth — NOT FORENSIC values);
dashas canonical PyJHora (not FORENSIC dates); signals actually grounded + cited to rules.** A plumbing defect
(unwired button, missing table, stale deploy) is fixed in place; a *data* gap that can't be made correct is
parked to the backlog, not faked green.

## §F — Safety rails (inherited from AUTONOMOUS_MODE)
Backup-before-destructive + auto-rollback; verify-before-promote (canary); idempotent re-runs; bounded
retries → park; budgets `MAX_RUN_BUDGET=$5000` / `MAX_SPEND_PER_ASSET=$300` (rules $1000). No human in the loop.

## §G — Completion + report
Emit: the live-build trace (each stage that broke + how it was fixed), per-layer **real** row counts, the
positions/dashas ground-truth result, parked/backlog items, and a final **"form → L5 verified on the native's
chart"** status (plus whether consume answers on it).

---

*End of RUNTIME_GUARDIAN_MODE v1.0 — native-authorized 2026-06-03. The swarm guards a live chart build through
the real portal, fixing every UI/workflow/execution/deploy/continuity defect at runtime until the data exists
end-to-end. Extends the charter + autonomous mode; the native drives the form, the system does the rest.*
