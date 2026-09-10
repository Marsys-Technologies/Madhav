---
artifact: PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN
version: 1.0
status: READY-TO-RUN — governs the unbounded overnight autonomous closeout of the
  Paripraśna Experience Assurance v3 campaign, from structural prerequisites through
  CG-5 (Operationally Proven), staging a one-click CG-6 acceptance packet for the
  native. Modelled on the six-stream autonomous run that already succeeded.
date: 2026-08-29
authoritative_side: claude
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/STREAM_EXECUTION_HARNESS_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/STREAM_CLOSURE_RUNBOOK_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py
changelog:
  - "1.0 (2026-08-29): initial closeout plan. Covers Phase A (structural pre-
    convergence) → Phase I (roadmap reconnect). Autonomous through CG-5; CG-6 is
    the single reserved native act by design."
---

# Paripraśna — Autonomous Overnight Closeout Plan v1.0

## §0 — Where we are (verified 2026-08-29)

- **P0 control-plane fix LANDED** (#1638, deployed `9aed4cb73`, writer-lease + numeric-
  slot dedup guards firing live in `rejected_events`).
- **All six streams checkpointed and verified** against the live ledger, none closed:
  S1 (10/10), S2 (30/30), S3 (47/60), S4 (54/54), S5 (40/45), S6 (7/31). Each
  `result_packet_accepted = 0` — closure deliberately deferred to convergence.
- **Gates:** CG-0/1/2 CLOSED; CG-3…CG-7 OPEN.
- **Deployment:** production = current `main` HEAD; Cloud Run auto-deploys on merge
  behind the migrate/attestation gate.

## §1 — Operating model

- **Unbounded overnight, fully autonomous, no human gates except one** (CG-6, §3.R).
  Run under `caffeinate -dimsu`; auto-resume on context exhaustion; wake-on-stop.
  Mechanics inherited from `STREAM_EXECUTION_HARNESS_v1_0.md`.
- **The Native Surrogate replaces the human everywhere a decision, clarification, or
  unblock is needed** — it rules, records the ruling as `decision_recorded`, and the
  run proceeds. It never blocks waiting for the real native (except CG-6).
- **"Done" means verified.** No work item is complete until the Independent Verifier
  has adversarially confirmed it against reality and emitted the confirming event. A
  self-reported "done" with no verifier confirmation is not done (§N.8).
- **Parallel where independent, sequential where dependent.** Worktree isolation for
  every lane that mutates files; tracker-only lanes need no worktree.

## §2 — The swarm (roles · model · effort — balanced, no overkill)

| Role | Actor id | Model | Effort | Mandate |
|---|---|---|---|---|
| **Native Surrogate** | `surrogate` | Opus | **high** | Replaces the native at every decision/blockage/clarification. Rules on #1615, B-002, V3-E-016 disposition, scope changes, plan revisions. Emits `decision_recorded` (tagged "SURROGATE — not native acceptance"). MUST NOT emit `native_acceptance`. |
| **Independent Verifier** | `verifier` | Opus | **high** | The single "is-it-really-done" gate. Adversarially re-runs every claim against production/source/ledger. Emits `verification_accepted`, `stream_closure_recommended`. Must differ from finder/fixer of what it verifies. |
| **Programme Integrator / Conductor** | `integrator` | Opus | **medium** | Orchestrates the DAG, drives ceremonies, emits `work_item_accepted`, `result_packet_accepted`, `gate_closed`. The spine. |
| **Security Engineer** | `lead-s5` | Opus | **medium-high** | V3-E-016 leak fix, `cli.py` lease closure, FINDING_FREEZE plan-revision governance — anything touching the control plane or real-data exposure. |
| **Structural Engineers** (×N parallel) | `lead-s1/2/3` | Sonnet | **medium** | Runbook correction, EDIR split, distinct test principals, id reconciliation, `deployed_revision` path. Mechanical-but-careful. |
| **Stream Ceremony Drivers** (×6) | `lead-s1…s6` | Sonnet | **medium** | Run each stream's 7-stage closure ceremony with the corrected vocab (§5). |
| **Integration Analyst** | `lead-s4` | Sonnet | **high** | CG-4 cross-stream reconciliation, the 6 open referrals, one integrated picture. |
| **Ops / Release** | `integrator` | Sonnet | **low-medium** | Merge, push, deploy, prod-sync, worktree/branch cleanup — guardrailed. |

Effort is spent where judgment lives (Surrogate, Verifier, Security = high) and kept
lean on mechanical work. One Verifier confirms all; one Surrogate decides all.

## §3 — Safety rails (NON-NEGOTIABLE — carried from the stream runs)

1. **Synthetic chart `1c826d5a-…` only.** Exceptions, narrow: S3's V3-E-012-authorized
   quality corpus (real chart, that ruling only); leak-DETECTION that sends synthetic
   input and checks for real output (V3-E-016). The real chart `482012f1-…` is never a
   plain input.
2. **Tracker writes via HTTP `127.0.0.1:8787/api/events` only**, Bearer token per actor
   from `/Users/Dev/.pariprashna-assurance-control/p2-credentials.json`. NEVER hand-edit
   the SQLite DB. NEVER use `cli.py` for writes (it bypasses the server lease — see A3).
   NEVER print a token value. Every event carries primary evidence + idempotency key.
3. **Respect the single-writer lease** (#1638): one writer per stream at a time. If a
   lane sees stream events it did not emit, it STOPS and escalates to the Surrogate.
4. **No weakening of any test/CI/auth/safety/watchdog/lease gate.** Strengthening is
   allowed; loosening a working gate is the forbidden move.
5. **Earned-signal only (§N.8).** Every PASS/grade/close has a real detector behind it
   or it is null. Verifier confirmation is that detector for implementation work.
6. **Security fixes**: additive-authz-only, demonstrated-can-fail, adversarially verified.
7. **R — THE ONE RESERVED HUMAN ACT: `native_acceptance` (CG-6).** The Surrogate
   structurally cannot and must not fire it. The run drives to CG-5, stages the CG-6
   packet, and halts CG-6/CG-7 for the morning. Faking native acceptance is the exact
   defect this campaign exists to catch.

## §4 — Phase plan (A → I)

Dependency shape: **A ∥ B** run in parallel → **C** (Surrogate decisions, needs A/B
prep) → **D** (six ceremonies, per-stream parallel, each internally sequential) → **E**
(barrier: integration) → **F** → stage **G** → [native fires CG-6] → **H → I**.

### Phase A — Pre-Convergence Structural Pass (parallel lanes, worktree-isolated)
- **A1 · Runbook correction** (Structural, Sonnet). Replace the phantom
  `remediation_verified` in `STREAM_CLOSURE_RUNBOOK` with the real flow:
  `remediation_proposed → remediation_approved → remediation_implemented →
  verification_accepted`. Verifier confirms the corrected vocab matches `control.py`.
- **A2 · FINDING_FREEZE resolution** (Security/Surrogate, Opus). Design + execute the
  governed plan-revision path so post-freeze findings (V3-E-056 CRITICAL, S5's) become
  first-class tracker records. Surrogate authorizes the revision; Verifier confirms
  V3-E-056 now has a finding + remediation + verification chain.
- **A3 · `cli.py` lease closure** (Security, Opus). Confirm whether the #1638 lease is
  DB-backed (covers `cli.py`) or server-local (bypassable). If bypassable: make the
  lease DB-backed OR restrict `cli.py` to read-only. Failing test first; Verifier proves
  a second direct writer is now rejected.
- **A4 · Distinct test principals** (Structural, Sonnet). Provision per-stream test
  principals (or a re-mint capability) so one stream's security drill can't revoke
  another's session (S2's blocked click-through). Verifier proves two streams can auth
  independently.
- **A5 · EDIR register split/lock** (Structural, Sonnet). Split `EDIR_V3_REGISTER` per
  stream (or introduce a merge-safe structure) to end the recurring conflict class.
  Verifier proves no finding bodies are lost in the migration.
- **A6 · ID reconciliation** (Structural, Sonnet). Resolve the V3-E-016 (S3 CRITICAL vs
  S4 MEDIUM) and V3-E-012 collisions; adopt `S{N}-V3-E-NNN` campaign-wide going forward.
- **A7 · `deployed_revision` update path** (Structural, Sonnet). Add the missing
  post-`work_started` update path so re-proofs can record the true deployed rev.
- **Exit A:** every lane merged to main, CI green, deployed; Verifier-confirmed each.

### Phase B — Open-CRITICAL Disposition (parallel to A)
- **B1 · V3-E-016** (Security, Opus). Re-reproduce on current prod; root-cause the
  generation/context leak; implement a fix; Verifier adversarially confirms real-chart
  data no longer leaks on a synthetic query (demonstrated-can-fail). If a full fix is
  not achievable overnight, the Surrogate records an explicit accepted-risk/defer
  disposition with rationale — never a silent skip.
- **Exit B:** V3-E-016 either fixed-and-verified-live, or Surrogate-dispositioned on the
  ledger with evidence.

### Phase C — Native-Decision Gate (Surrogate acts; needs A2/B1 prep)
- **C1 · PR #1615 reframed** to the data-bearing tables (`pariprashna_safety_decisions`
  319 rows, `mimamsa_predictions` 195 rows), not just empty `audit_log`. Surrogate rules
  merge/extend/defer; if merge, Ops lands it; Verifier proves the grant is revoked live.
- **C2 · B-002 RLS** — Surrogate rules commission-8-step-build vs record-accepted-risk;
  records the disposition so it stops being re-discovered.
- **C3 · V3-E-016 disposition** ratified (from B1).
- **Exit C:** three `decision_recorded` rulings on the ledger; any authorized code landed.

### Phase D — Convergence / CG-3 Stream Complete (six ceremonies, per-stream parallel)
For each stream, run the 7-stage ceremony (§5) with corrected vocab: drive stage work
items in order, Integrator accepts each `work_item_accepted` linked to a Verifier
`verification_accepted` (verifier ≠ finder/fixer), regression requires
`executed == planned` over the enumerated set, then `stream_closure_recommended`, then
`result_packet_accepted`. S4 is furthest (3/6 stages, closure already recommended) → run
first as the template. Honest denominators only (S3 47/60, S6 7/31 close on what's
reachable + Surrogate-dispositioned residuals).
- **Exit D:** six `result_packet_accepted`; Integrator closes **CG-3**.

### Phase E — Integration / CG-4 Integrated Assurance (barrier after D)
- Integration Analyst reconciles the 6 open cross-stream referrals, dedupes findings,
  produces one integrated assurance picture; Verifier confirms no finding is stranded.
- **Exit E:** Integrator closes **CG-4**.

### Phase F — CG-5 Operationally Proven
- Whole-product live operational proof against current production (the converged authz
  fixes, history/state/quality/security/perf behaviours) with trace evidence.
- **Exit F:** Verifier-confirmed operational proof; Integrator closes **CG-5**.

### Phase G — CG-6 Acceptance Packet (STAGED, not fired)
- Assemble the complete native-acceptance packet: gate ledger, every finding+fix+
  verification, the three Surrogate rulings, residuals + dispositions, the one-click
  `native_acceptance` instruction. **HALT here.** The run posts a clear "morning
  handoff" summary and waits.

### Phase H — CG-7 Release Closed *(after native fires CG-6)*
- On the real native's `native_acceptance`, Integrator closes CG-6→CG-7, seals the
  campaign, writes the final report.

### Phase I — Roadmap Reconnect *(after CG-7)*
- Record how Paripraśna-complete slots back into the MARSYS-JIS product arc and what it
  unblocks next; update `CURRENT_STATE`.

## §5 — Ceremony reference (CORRECTED vocab — the phantom is removed)

Real control-plane event vocabulary (verified in `control.py`): `finding_discovered`,
`finding_triaged`, `remediation_proposed`, `remediation_approved` (freezes plan →
`FINDING_FREEZE` after), `remediation_implemented`, `verification_accepted`,
`scenario_executed`, `work_item_accepted`, `stream_closure_recommended`,
`result_packet_accepted`, `gate_closed`, `decision_recorded`, `correction_recorded`.
**There is no `remediation_verified`.** A stage is verified via `verification_accepted`
(INDEPENDENT_VERIFIER), and remediation completeness via `remediation_implemented`
covering every triaged finding in the approved plan.

Stage order per stream (each `work_item_accepted` by Integrator, linked to a Verifier
`verification_accepted`, verifier ≠ finder/fixer):
`{S}:charter → baseline → triage → remediation → verification → regression → closure`.

## §6 — Git / deploy / cleanup discipline

- One lane = one worktree = one branch = one PR. Protected PR → CI green → merge (merge
  queue: bare `gh pr merge`, never `--squash --delete-branch` together).
- Merge to main auto-deploys via Cloud Run behind the migrate/attestation gate; Ops
  confirms each deploy lands green (prod == main). If the migrate gate reds, escalate to
  Surrogate — do not force.
- Cleanup at phase boundaries: remove merged worktrees/branches; the run leaves the tree
  clean. Never delete an unmerged branch with unlanded work.

## §7 — Escalation

Any blockage, ambiguity, or failed gate → escalate to the **Native Surrogate**, which
rules and records `decision_recorded`, and the run continues. The Surrogate never stalls
the run waiting on the real human. The only thing it cannot resolve is CG-6 (§3.R).

## §8 — Definition of done (exit of the overnight run)

CG-3, CG-4, CG-5 CLOSED; the CG-6 acceptance packet staged and the morning handoff
posted; production in sync with main; tree clean; every closed item Verifier-confirmed;
every decision Surrogate-recorded. CG-6/CG-7/roadmap complete on the native's one
acceptance in the morning.
