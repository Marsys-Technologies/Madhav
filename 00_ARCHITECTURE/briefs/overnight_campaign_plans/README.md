---
canonical_id: OVERNIGHT_CAMPAIGN_PLANS_INDEX
version: 1.1
status: ARCHIVAL RECORD
date_landed: 2026-08-22
changelog:
  - v1.1 (2026-08-23): N4 discrepancy RESOLVED as historical/superseded — resolution paragraph
    added to the discrepancy section; ratified briefs/sampurti/REBASE_PLAN_v1_0.md deliberately
    untouched. Native-delegated decision (Fable 5 agent).
  - v1.0 (2026-08-22): initial archival landing.
scope: governing plans, kickoff prompts, and orchestration harness for the overnight swarm campaigns
---

# Overnight campaign plans — archival record

## What this is

The **input** documents for the overnight swarm campaigns — the plans agents were given, the
per-stream kickoff prompts, and the supervisor/gate scripts that drove the runs. Until now the repo
held every campaign's **output** record (close reports, ledgers, evidence under
`briefs/{ekavakyata,parisesa,sampurti,purnata,…}/`) and none of their inputs.

These lived in `~/shad_overnight/`, outside every repo and outside every worktree, alongside ~301 MB
of raw `stream-json` session logs. The logs were discarded (machine transcripts whose outcomes are
already recorded as ledgers and reports); these 75 files were kept. Landed 2026-08-22 during the
worktree/stray-artifact hygiene sweep — see
`CLAUDECODE_BRIEF_WORKTREE_AND_STRAY_ARTIFACT_SWEEP_v1_0.md`.

Filed flat, in one directory, deliberately: assigning each file to an existing campaign folder would
mean 75 filing judgments this landing has no authority to make. Provenance is preserved as-found;
re-file later if a campaign owner wants them under their own tree.

## ⚠ One substantive discrepancy — needs a native decision

**`SAMPURTI_REBASE_PLAN_v1_0.md` here is a SUPERSET of
`briefs/sampurti/REBASE_PLAN_v1_0.md` already in the repo.** The copy landed here carries **10
additional lines the repo copy does not have** — a native ruling:

> `N4 RULED (native, 2026-08-13 00:5x IST): P-G1 CLOSES PER-CLASS.` … the rung's evidence standard
> is met on the 6 built classes (6,708 windows, ~1,300× precision gain); remaining 21 classes
> complete incrementally via `ka_kshetra` checkpoint-resume; the monolithic-single-run requirement
> is retired.

The repo's copy is otherwise byte-identical. **The in-repo `briefs/sampurti/REBASE_PLAN_v1_0.md` was
deliberately NOT modified by this landing** — amending a ratified governance document is a native
decision (CLAUDE.md §L), not a hygiene sweep's call. If the ruling is genuine and should bind, fold
it into the sampurti copy and supersede this one.

**RESOLVED 2026-08-23 — N4 is HISTORICAL, SUPERSEDED; the ratified copy stays untouched**
(native-delegated decision made by a Fable 5 agent on the native's explicit instruction, not by
the native directly). Investigated on live evidence, not asserted:

- **The ruling is genuine and its technical premise is real.** `ka_kshetra` checkpoint-resume
  exists in code (`platform/python-sidecar/services/ka_kshetra/writer.py`: `_RESUME_VERSION`,
  cross-attempt substep resumption via `build_substep_progress` per migration 436, and
  partial-null-class replanning) and was exercised live: the sealed ledger's R10 entry
  (2026-08-13) shows chart2's Run 6 resuming from 79 pre-committed substeps to LIT, and R40
  (2026-08-14) shows "60 stage4 substeps preserved … stage4 SKIPPED entirely."
- **But its operative content was discharged inside the same campaign, which then closed on
  broader terms.** The per-class closure N4 authorized is recorded de facto in the sealed ledger
  (R10 reconciliation: "R1 COMPLETE … 6,708 field windows"; Measurement #4: 6 event classes),
  and the incremental completion it prescribed ran to its end two days later: the A8 27-class
  build COMPLETED 2026-08-15 (snapshot `kfs_e23ba1ab`, 31,350 windows, 25 of 27 classes
  populated; FIELD-INTEGRATED posted at `db77e48da`), and the arc sealed ARC-COMPLETE at
  R44–R47. The campaign's record of record is the sealed `briefs/sampurti/SAMPURTI_STATE.md`
  (status CLOSED, landed to main at `eccf15abc`), whose terminal-state tables restate the
  field's closure on terms broader than GREEN-PER-CLASS(6/27). PARIŚEṢA F-78 (PR #1392) later
  corrected `kala_field_snapshots.event_classes` disclosure (ATTEMPTED, not BUILT) on the same
  terrain.
- **Therefore:** retro-amending the ratified `briefs/sampurti/REBASE_PLAN_v1_0.md` now would
  insert a spent, transient 6/27-era ruling into a CLOSED campaign's plan of record as if it
  were the final disposition. The 10 lines in the copy here stand as the historical record of
  the ruling; the superseding documents are the sealed `SAMPURTI_STATE.md` (R44–R47 terminal
  state) and `briefs/sampurti/MEASUREMENT_4_BASELINE_v1_0.md`.

## What was excluded as duplicate

Verified byte-identical (modulo trailing whitespace) to documents already in the repo, so not landed:

| Scratch file | Already in repo as |
|---|---|
| `GAP_REMEDIATION_MASTER_PLAN.md` | `briefs/sampurti/MASTER_PLAN_v1_0.md` |
| `MASTER_PLAN_IDENTITY_AND_PROMISE.md` | `briefs/adhisthana/MASTER_PLAN_v1_0.md` |

## Contents

**Campaign plans / specs / audits (15)** — `ALPHA_DAY_PLAN_v1_0` · `DHARA_ENGINE_SPEC_v1_0` ·
`EKAVAKYATA_EXECUTION_PLAN_v1_0` · `PARIPURNA_AUDIT_PLAN_v1_0` · `PARIPURNA_2_AUDIT_PLAN_v2_0` ·
`PARISESA_EXECUTION_PLAN_v1_0` · `PARISESA_INTERACTIVE_PROMPT` · `PURNA_GROUNDING_REPORT_v1_0` ·
`PURNA_KSHETRA_PLAN_v1_0`/`v1_1` · `SAMPURTI_AUDIT_v1_0` · `SAMPURTI_ELEVATED_PLAN_v2_0` ·
`SAMPURTI_IMPLEMENTATION_PLAN_v1_0` · `SAMPURTI_INVESTIGATION_v1_0` · `SAMPURTI_REBASE_PLAN_v1_0` (see warning above)

**Kickoff / stream prompts** — `shad_darshana_kickoff` (ṢAḌ-DARŚANA, 32 K, the largest) ·
`ekv_*` (conductor, morning, pratinidhi, sentinel, streams A–E) · `parisesa_*` (conductor,
integrator, pratinidhi, verifier, streams S1–S6) · `dh1`/`dh2`/`dh3_kickoff` ·
`sm_alpha`/`beta`/`gamma_kickoff` + `sm_common_rails` · `pp_kickoff` · `pp2_kickoff` ·
`sampurti_overnight_kickoff`

**Orchestration harness** — gates (`audit_gate.py`, `ekv_gate.py`, `parisesa_gate.py`) ·
supervisors and launchers (`ekv_supervisor.sh`, `ekv_launch_streams.sh`, `parisesa_launch.sh`,
`run_dh_d*.sh`, `run_pp2.sh`, `run_paripurna.sh`) · monitoring (`ekv_dashboard.py`,
`ekv_terminal_check.py`, `ekv_watch_events.sh`)

Scripts reference the DB via `gcloud secrets versions access latest --secret=amjis-pipeline-db-url`
— runtime fetch by name, no embedded credential. Secret-scanned before landing.
