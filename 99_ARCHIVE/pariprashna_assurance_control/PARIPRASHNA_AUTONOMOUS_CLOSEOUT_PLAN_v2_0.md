---
artifact: PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN
version: 2.0
supersedes: PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN_v1_0 (PR #1647)
status: READY-TO-RUN — the elevated, ground-truthed plan for the unbounded overnight
  autonomous closeout of Paripraśna Experience Assurance v3, from stall-recovery through
  CG-5, staging a one-click CG-6 packet. Every rule below traces to something that
  actually happened in execution — not a fresh idea.
date: 2026-08-29
authoritative_side: claude
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/STREAM_CLOSURE_RUNBOOK_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py
changelog:
  - "2.0 (2026-08-29): significant elevation of v1.0 after a real overnight run. Adds
    §0 Ground-Truth Ledger (18 hard-won realities), §1 Anti-Stall/Liveness Protocol (the
    v1.0 run died silently for ~12h with the CRITICAL leak fix sitting unmerged), §2
    Critical-Fix Fast-Path, resume-awareness (Phase A/B already largely landed),
    corrected ceremony vocab (the phantom remediation_verified is gone), a rate-limit +
    merge-queue playbook, the shared-resource collision matrix, and the deploy-coupling
    protocol. v1.0's phase spine (A→I) is retained and sharpened."
---

# Paripraśna — Autonomous Overnight Closeout Plan v2.0 (elevated, ground-truthed)

## §0 — Ground-Truth Ledger (what execution actually taught us — obey these)

Each item is a real event from this campaign and the operating rule it forces. This
section is the difference between a plan and a *grounded* plan. Read it first; it will
save the run from repeating what already went wrong.

| # | Ground reality (observed) | Rule it forces |
|---|---|---|
| G1 | **The v1.0 overnight run STALLED SILENTLY for ~12h.** Last ledger event 2026-08-28T23:50:59Z; zero events, zero file writes after. Nobody knew until the native asked. | **§1 Anti-Stall Protocol is mandatory.** Heartbeat ≤10 min; durable checkpoints; a stall is a first-class failure, not silence. |
| G2 | When it stalled, **#1655 — the CRITICAL real-chart leak fix — sat OPEN, CI-green, Surrogate-approved, for 12h**, so the leak stayed live in production the whole time. | **§2 Critical-Fix Fast-Path.** A verified + Surrogate-expedited CRITICAL merges+deploys the instant it is green — never batched to the end. |
| G3 | **`remediation_verified` does not exist in the tracker.** v1.0's runbook told S4 to emit a phantom event; S4 correctly refused. | Ceremony vocab is EXACTLY §5. There is no `remediation_verified`. |
| G4 | **`FINDING_FREEZE` (409)** blocks new findings once a stream's remediation plan is frozen. A real, fixed, merged CRITICAL (V3-E-056) could not be filed because of it. | Post-freeze findings need the **governed plan-revision path (A2 / #1651)**. Land that before running ceremonies that must admit late findings. |
| G5 | **A concurrent-writer collision** (two sessions as `lead-s5`) produced a false 45/45 that nearly satisfied a gate. Fixed by #1638 (writer-lease + numeric-slot dedup), now deployed and enforcing. | **One writer per stream, ever.** If a lane sees stream events it did not emit → STOP + escalate to Surrogate. Count DISTINCT numeric slots, never raw event count. |
| G6 | **`cli.py` writes direct to the DB via `EventStore(...)`, bypassing the HTTP server** where the lease lives. A3 investigated and judged the practical bypass not exploitable, but the path exists. | **All tracker writes via HTTP `127.0.0.1:8787/api/events` only.** Never `cli.py` for writes, never hand-edit the SQLite file. |
| G7 | **Shared test principal**: S5's session-revocation drill revoked the cookie S2 needed, blocking S2's live click-through. | Use **distinct per-stream test principals** (A4 / #1650, landed). Never let one stream's security drill break another's auth. |
| G8 | **Shared EDIR register** caused repeated merge conflicts (S1/S2/S3); one near-miss discarded S5 finding bodies before a grep caught it. | Use the **split/restructured EDIR** (A5 / #1654). Always grep-verify no finding bodies were lost after any register edit. |
| G9 | **GitHub secondary rate limit is shared across many bots on this repo** and stalled merges ~20 min. | Serialize merges; REST for status polling, GraphQL + backoff for merge-queue actions; treat 403/secondary-limit as retry-with-backoff, not failure. |
| G10 | **The deploy pipeline is SHARED with Nirmana** through one `migrate → deploy` chain. A Nirmana-campaign migrate-gate failure earlier blocked ALL deploys (Paripraśna security fixes included) for hours. | Judge "is it live?" by **deploy state, not merge state**. Watch the **Apply DB Migrations** job. If it reds, escalate to Surrogate — **NEVER force or weaken it** (it is correctly fail-closed). |
| G11 | Deploy = **Cloud Run**, auto-triggered after "CI — Ganga Quality Gate" on main. Live host: `https://amjis-web-938361928218.asia-south1.run.app` (NOT `amjis-web.run.app` — that fails TLS). | Re-derive the deployed sha each time via `gh run list --workflow=deploy.yml --branch=main --status=success --limit 1 --json headSha`. Probe the real host. |
| G12 | **`public.charts.native_id` is a trap**: all 6 prod rows default to `'abhisek'`, so it cannot be an authz key — keying off it would encode the bug as the fix (§N.8). | Never trust a column that looks like an authz key without checking its actual values. B1's fix used an explicit binding, not the column. |
| G13 | **Stream self-reports were wrong multiple times** and only caught by independent verification: S6 falsely claimed 3 probe files were "fabricated" (they existed on main); S1's "403" was actually a 404 (intentional info-hiding); the false 45/45. | **Verify-before-trust is the meta-principle.** Every "done" is confirmed against live ledger/git/prod by an actor who is not the claimant, before it counts. |
| G14 | **`deployed_revision` had no update path** in the tracker after `work_started`. A7 (#1649, landed) added one. | Re-proofs must record the true deployed rev via the A7 path — don't work around it. |
| G15 | **Merge-queue quirk**: `gh pr merge --squash --delete-branch` FAILS under merge-queue mode. | Merge with **bare `gh pr merge`**; never combine `--squash` with `--delete-branch`. |
| G16 | **EDIR ids collide** when bare (`V3-E-NNN`): S1/S3/Gap all hit `V3-E-012`; V3-E-016 collides (S3 CRITICAL vs S4 MEDIUM). S4's `S{N}-V3-E-NNN` never collided. | All NEW findings use **`S{N}-V3-E-NNN`**. Reconcile the existing bare-id collisions at integration; never silently rename another stream's ids. |
| G17 | **The B1 finding was severe and real**: the native's ~79KB Chart Gestalt Map was injected into EVERY chart's synthesis prompt — 5 of 6 prod charts, 4 of them other real people. Independently reproduced; fix proven RED→GREEN + mutation-tested. | Treat V3-E-016 as the campaign's headline finding. Its fix (#1655) is time-critical (§2). Flag the third-party-exposure disclosure question to the native (not the swarm's call). |
| G18 | **Real chart `482012f1-…` is out of bounds as a query INPUT.** Synthetic `1c826d5a-…` is the default. Narrow exceptions: S3's V3-E-012-authorized quality corpus; leak-DETECTION (synthetic in, check for real out). | Never send the real chart as input. Leak-detection is the only way the real chart legitimately appears — as output being checked for. |

## §1 — Anti-Stall / Liveness Protocol (the #1 elevation — G1/G2)

The v1.0 run's fatal flaw was that it could die and no one would know. v2.0 makes
liveness a hard requirement of the Conductor:

1. **Heartbeat every ≤10 minutes.** The Conductor appends a line to
   `00_ARCHITECTURE/autonomy/state/PARIPRASHNA_CLOSEOUT_HEARTBEAT.jsonl`
   (`{ts, phase, lane, last_action, next_action}`) AND emits a lightweight tracker
   `decision_recorded` heartbeat at each phase boundary. If ≥15 min pass with no
   heartbeat, the run is by definition stalled.
2. **Durable checkpoints.** Every unit of work (a lane, a stage acceptance, a merge) is
   committed/recorded the moment it completes. State lives in the ledger + git, never
   only in the session's head — so a restart loses nothing.
3. **Resume-safe by construction.** On (re)start the Conductor RE-DERIVES all state from
   the ledger + git + deploy status and SKIPS anything already done. It never redoes a
   merged PR or an accepted stage. (Phase A/B are already largely done — see §3.)
4. **Progress-or-escalate.** If a phase makes no forward progress in 20 min, the
   Conductor reroutes the work or has the Surrogate rule an unblock — it does not spin.
5. **External watchdog (recommended companion, set up separately).** A launchd/cron job
   that checks the heartbeat file's mtime every 10 min and, if stale >20 min, re-invokes
   `claude -p "<resume prompt>"`. The repo already runs tracker services under launchd;
   this mirrors that pattern. (Offered as an add-on; the internal protocol above is the
   baseline.)

## §2 — Critical-Fix Fast-Path (G2)

A finding graded CRITICAL that is (a) fixed, (b) independently Verifier-confirmed, and
(c) Surrogate-expedited **merges and deploys immediately** — ahead of all other campaign
work — then gets a live post-deploy re-proof. It is NEVER held for end-of-run batching.
**This run's first substantive act is exactly this for #1655** (see §3).

## §3 — Where the run actually stands (resume state — do NOT redo)

- **Landed & merged:** the plan (#1647), and Phase A/B lanes #1648 (A1 runbook),
  #1649 (A7 deployed_revision path), #1650 (A4 test principals), #1652 (A3 cli.py lease),
  #1653 (A6 id-forensics). #1638 (control-plane P0) landed and is enforcing.
- **OPEN, CI-green, must land first:** **#1655 (B1 V3-E-016 CRITICAL leak fix)** —
  Surrogate already ruled expedite (ledger `surrogate-decision-v3e016-expedite`,
  23:50:59Z). Also **#1651 (A2 FINDING_FREEZE path)** and **#1654 (A5 EDIR split)**.
- **Missing evidence:** the B1 `verification_accepted` event is not yet on the ledger
  (the fix doc has RED→GREEN + mutation proof; the tracker confirmation event is owed).
- **Not started:** Phase C (native-decision gate), D (ceremonies), E–I.
- **Gates:** CG-0/1/2 CLOSED; CG-3…CG-7 OPEN. Completion 33.38%.
- **Stream states (honest denominators):** S1 10/10 · S2 30/30 · S3 47/60 · S4 54/54
  (3/6 stages, closure already recommended) · S5 40/45 · S6 7/31.

## §4 — The swarm (roles · model · effort — balanced, from v1.0, unchanged)

| Role | Actor | Model | Effort | Mandate |
|---|---|---|---|---|
| Native Surrogate | `surrogate` | Opus | high | Replaces the human at every decision/blockage. Rules #1615, B-002, V3-E-016, scope/plan revisions. Emits `decision_recorded` ("SURROGATE — not native acceptance"). MUST NOT emit `native_acceptance`. |
| Independent Verifier | `verifier` | Opus | high | The single "is-it-really-done" gate. Adversarially re-runs claims vs prod/source/ledger. Emits `verification_accepted`, `stream_closure_recommended`. ≠ finder/fixer. |
| Programme Integrator / Conductor | `integrator` | Opus | medium | Orchestrates the DAG + heartbeat; emits `work_item_accepted`, `result_packet_accepted`, `gate_closed`. |
| Security Engineer | `lead-s5` | Opus | medium-high | Anything touching the control plane or real-data exposure. |
| Structural / Stream / Ops Engineers | `lead-s1…s6` | Sonnet | medium | Ceremony driving, integration mechanics, merge/deploy/cleanup (guardrailed). |
| Integration Analyst | `lead-s4` | Sonnet | high | CG-4 cross-stream reconciliation, the 6 open referrals. |

Effort is spent where judgment lives (Surrogate/Verifier/Security = high), lean on
mechanical work. One Verifier confirms all; one Surrogate decides all.

## §5 — Ceremony vocab (CORRECTED — the phantom is gone, G3/G4)

Real events (verified in `control.py`): `finding_discovered`, `finding_triaged`,
`remediation_proposed`, `remediation_approved` (freezes the plan → `FINDING_FREEZE`
after), `remediation_implemented`, `verification_accepted`, `scenario_executed`,
`work_item_accepted`, `stream_closure_recommended`, `result_packet_accepted`,
`gate_closed`, `decision_recorded`, `correction_recorded`, `reproduction_recorded`,
`dependency_resolved`, `integration_baseline_advanced`, `paused`.
**There is NO `remediation_verified`.** A stage is verified by `verification_accepted`
(INDEPENDENT_VERIFIER, ≠ finder/fixer); remediation completeness = every triaged finding
covered by a `remediation_implemented` under the approved plan.

Per-stream order (each `work_item_accepted` by Integrator, linked to a Verifier
`verification_accepted`): `{S}:charter → baseline → triage → remediation → verification
→ regression → closure`. Regression needs DISTINCT-slot `executed == planned` over the
enumerated scope set. `result_packet_accepted` closes the stream.

## §6 — Phase plan (A→I; A/B mostly done — see §3)

- **Phase 0 (FIRST):** stall-recovery + critical fast-path. Land #1655, confirm Cloud Run
  deploys it, live-re-proof the leak closed (§2/G2/G17). Record the owed B1
  `verification_accepted`. Land #1651 + #1654. Re-attest the tracker control-plane
  release (A2/A3/A7 touched `control.py`).
- **Phase C — Native-Decision Gate (Surrogate):** #1615 reframed to the data-bearing
  tables (`pariprashna_safety_decisions` 319 rows, `mimamsa_predictions` 195 rows, not
  empty `audit_log`); B-002 RLS commission-vs-accept-risk; ratify V3-E-016 disposition.
  Three `decision_recorded` on the ledger; any authorized code landed + deployed.
- **Phase D — Convergence / CG-3:** six ceremonies (§5), per-stream parallel, each
  internally sequential. S4 first (furthest: 3/6 + closure recommended) as the template.
  Honest denominators; S3/S6 close on reachable scenarios with Surrogate-dispositioned
  residuals. Integrator closes **CG-3**.
- **Phase E — Integration / CG-4:** reconcile the 6 open cross-stream referrals + the
  bare-id collisions (G16); one integrated assurance picture; no finding stranded.
  Integrator closes **CG-4**.
- **Phase F — CG-5 Operationally Proven:** whole-product LIVE proof against current
  production with trace evidence. Integrator closes **CG-5**.
- **Phase G — CG-6 packet (HALT):** assemble the native-acceptance packet (gate ledger,
  every finding+fix+verification, the three Surrogate rulings, residuals+dispositions,
  the one-click `native_acceptance` instruction + the G17 third-party-disclosure
  question). Post the morning handoff. **STOP.**
- **Phase H — CG-7 (after the native fires CG-6):** Integrator closes CG-6→CG-7, seals
  the campaign, writes the final report.
- **Phase I — Roadmap reconnect:** record how Paripraśna-complete slots into the
  MARSYS-JIS arc; update `CURRENT_STATE_v1_0.md`; note what it unblocks.

## §7 — Safety rails (NON-NEGOTIABLE)

Synthetic chart only (narrow exceptions G18); tracker writes via HTTP only, never
`cli.py`/DB-edit, never print a token (G6); one writer per stream (G5); weaken no
test/CI/auth/safety/lease/migrate gate (G10); earned-signal only — Verifier confirmation
is the detector (§N.8/G13); security fixes additive-authz-only + demonstrated-can-fail;
merge with bare `gh pr merge` (G15); rate-limit = backoff not failure (G9); confirm every
deploy landed, never force the migrate gate (G10). **THE ONE RESERVED ACT:
`native_acceptance` (CG-6) — the Surrogate structurally cannot and must not fire it.**

## §8 — Definition of done (overnight exit)

CG-3, CG-4, CG-5 CLOSED; the CG-6 packet staged + morning handoff posted; #1655 live and
re-proven; production in sync with main; heartbeat current to the end; every closed item
Verifier-confirmed; every decision Surrogate-recorded; tree clean. CG-6/CG-7/roadmap
complete on the native's one acceptance in the morning.
