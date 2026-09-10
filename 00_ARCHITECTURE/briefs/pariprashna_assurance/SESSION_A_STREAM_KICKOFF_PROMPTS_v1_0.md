---
artifact: PARIPRASHNA_SESSION_A_STREAM_KICKOFF_PROMPTS
version: "1.0"
status: READY — six paste-ready prompts, pinned. Session A's A6 deliverable.
date: 2026-08-27
session: "Paripraśna Experience Assurance v3, Session A (autonomous pre-stream session) — resumed, A2 through A6 complete"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md (§8, §11.2)
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S1_v1_0.md through S6
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
---

# Session A — six ready-to-paste stream kickoff prompts (A6)

**To the native:** these are the six prompts elevation §11.1's directive asked for at the
stop before the streams begin. Each is self-contained and pastes directly into a fresh
Claude Code session. Run all six in parallel, in separate worktrees, per the elevation's
own isolation law (§8.1). **Session A does not dispatch these itself** — that action is
reserved to you.

Before pasting: skim "What Session A actually did" below once — it names the two things
worth knowing before you launch: the B-002 finding that stays honestly open, and the
unrelated Nirmana deploy blocker each stream needs to re-check.

---

## What Session A actually did (context for you, not part of the pasted prompts)

- **A2 (credential):** resolved by genuine self-provisioning, no new secrets. Detail:
  `A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`.
- **A3 (absorption):** 81/81 unmerged branches dispositioned. Detail: `EDIR_V3_REGISTER_v1_0.md`.
- **A4 (P2 blockers):** B-001, B-004, B-007, B-008 CLOSED (fixed, independently verified,
  merged; B-001 has a full LIVE deployed re-proof, B-007/B-008's deployed re-proof is
  deferred — see below). B-002's underlying finding stays **honestly OPEN** — a live fix
  was assessed too risky for one session (162 files, no existing session-context
  plumbing); a test-only "narrowed proof" documents the gap instead
  (`B002_NARROWED_PROOF_v1_0.md`). B-003/B-005 closed as superseded (dead, never-merged
  infrastructure). B-006 correctly untouched, parked to P6. **Two CRITICAL findings
  (B-007, B-008) were discovered collaterally, not from the original intake** — any
  authenticated user could destructively wipe another user's (or your real chart's)
  build data via `cockpit/clear`/`cockpit/runs`/`atlas/sample`; both are now fixed and
  merged. A further ~30-route candidate list of the same defect family was deliberately
  **not** chased in Session A and is filed to stream S5 as its top-priority lead
  (`EDIR_V3_REGISTER_v1_0.md` V3-E-011) — a bounded-scope decision, not an oversight.
- **The Nirmana deploy blocker:** the `amjis-web` deploy pipeline has been failing since
  PR #1601 (a **different**, unrelated autonomous campaign's own database-ownership
  preflight step), stuck at `cafa894ee7c` while `origin/main` has advanced to
  `3686772b7` (includes B-007/B-008). This is **not a Paripraśna defect** and outside this
  campaign's authority to fix. Every stream charter tells its stream to re-check the
  deployed image tag at its own open — if it's still stale, LIVE-rung claims on the
  cockpit/chart-authorization surface should wait or be flagged, not fabricated.
- **A5 (CG-2 + charters):** CG-2 (Safe to Test) is CLOSED on the tracker
  (`http://127.0.0.1:8787`, gate_closed event `031e03fc-7685-4c17-af34-bba115318246`).
  Six charters frozen (`charters/STREAM_CHARTER_S1_v1_0.md`…`S6`), registered as tracker
  plan revision 4 (`http://127.0.0.1:8788/api/elevation`, confirmed active).

**Session ceiling used:** well under the 8h wall-clock budget. No self-pause was needed —
every phase closed on its own evidence.

---

## S1 — Navigation, Shell & History

```text
You are the Stream Lead for Paripraśna assurance stream S1 — Navigation, Shell & History,
one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S1_v1_0.md
(tracker plan revision 4). Recommended session model: Sonnet.

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s1-nav-shell-history; declare may_touch/must_not_touch from your
charter's territory; register tracker actor lead-s1 (token already provisioned in
p2-credentials.json on the live control plane at 127.0.0.1:8787 -- read the CURRENT
tracker contract from origin/main's tracker/control.py + cli.py before emitting, the same
way Session A did, since any local worktree copy may be stale); emit session-open via
work_started on stream S1 with a frozen planned_scenarios count you derive from your
charter's scope section. CG-2 is closed (event 031e03fc-7685-4c17-af34-bba115318246);
your entry gate is satisfied -- do not re-litigate it.

FIRST ACTION: re-check `gcloud run services describe amjis-web --format="value(spec.template.spec.containers[0].image)"`
against 3686772b7000cf9e1d391b97eccc008ef167b8d0 -- your charter documents why it may
still be stale (an unrelated Nirmana-campaign deploy blocker, not yours to fix) and what
to do if so.

Scope: charter's full scope section -- test plan section 5.1 sidebar/history rows,
sections 8.1-8.2 for shell regions, journeys J1 and J7, plus the cross-chart-denial
LIVE-rung re-proof, large-history, and device-return scenarios named in your charter.
Credential status: RESOLVED (A2) -- see 00_ARCHITECTURE/briefs/pariprashna_assurance/A2_CREDENTIAL_LANE_OUTCOME_v1_0.md
for the mint recipe. Synthetic chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a ONLY; the
native's real chart 482012f1-710e-4a25-994a-93821f5871aa is out of bounds beyond a
denial-probe target (status/headers only, never response body).

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1). Full autonomy within your charter: the Native Surrogate
(spawn per section 11.1) takes triage/severity/remediation-freeze/trade-off decisions;
section 3.2 residue goes to self-pause, never improvisation. Every divergence -> EDIR_V3
entry (00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md, already
open with 11 entries) + tracker event before session close. Cross-territory findings ->
referral (section 8.3), never fixes. Merges to main only per section 8.1's two
exceptions; all else queues for convergence.
Ceilings: 8h wall-clock / spend by judgment. On ceiling or irreducible blocker:
self-pause protocol (section 10). Close: result packet per
00_ARCHITECTURE/briefs/pariprashna_assurance/templates/STREAM_RESULT_PACKET_TEMPLATE.md,
independent-verifier recommendation, integrator acceptance, tracker events, STOP.
```

## S2 — Conversation & Reading Experience

```text
You are the Stream Lead for Paripraśna assurance stream S2 — Conversation & Reading
Experience, one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S2_v1_0.md
(tracker plan revision 4). Recommended session model: Sonnet.

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s2-conversation-reading; declare may_touch/must_not_touch from
your charter's territory; register tracker actor lead-s2 (token in p2-credentials.json;
read the CURRENT tracker contract from origin/main first); emit session-open via
work_started on stream S2 with a frozen planned_scenarios count from your charter's scope.
CG-2 is closed (event 031e03fc-7685-4c17-af34-bba115318246) -- do not re-litigate it.

FIRST ACTION: re-check the deployed amjis-web image tag against
3686772b7000cf9e1d391b97eccc008ef167b8d0 per your charter's pin note (an unrelated
Nirmana-campaign deploy blocker may still be in effect).

Scope: charter's full scope section -- test plan section 5.1 viewport/working/dock/
composer rows, section 8 for these regions, journeys J2, J3, J5, J6, J9, and the
progress-cadence check (section 4.3 item 5). Credential status: RESOLVED (A2) --
see 00_ARCHITECTURE/briefs/pariprashna_assurance/A2_CREDENTIAL_LANE_OUTCOME_v1_0.md.
Synthetic chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a ONLY; native's real chart
482012f1-710e-4a25-994a-93821f5871aa out of bounds.

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1). Full autonomy within your charter: the Native Surrogate
takes triage/severity/remediation-freeze/trade-off decisions; section 3.2 residue goes to
self-pause. Every divergence -> EDIR_V3 entry + tracker event before session close.
Cross-territory findings -> referral (section 8.3), never fixes. Merges to main only per
section 8.1's two exceptions.
Ceilings: 8h wall-clock / spend by judgment. On ceiling or irreducible blocker:
self-pause protocol (section 10). Close: result packet, independent-verifier
recommendation, integrator acceptance, tracker events, STOP.
```

## S3 — Answer Quality & Epistemic Trust

```text
You are the Stream Lead for Paripraśna assurance stream S3 — Answer Quality & Epistemic
Trust, one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S3_v1_0.md
(tracker plan revision 4). Recommended session model: Opus (epistemic-judgment density
per elevation section 11.1).

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s3-answer-quality; declare may_touch/must_not_touch from your
charter's territory; register tracker actor lead-s3 (token in p2-credentials.json; read
the CURRENT tracker contract from origin/main first); emit session-open via work_started
on stream S3 with a frozen planned_scenarios count (minimum 5 fixtures x 11 work classes
= 55 at floor, per your charter). CG-2 is closed (event 031e03fc-7685-4c17-af34-bba115318246).

Scope: charter's full scope section -- test plan section 7's full corpus (11 work
classes, minimum 5 fixtures each), all eight scoring dimensions scored SEPARATELY, J4's
language half (enforcement is S5's), the refuter-panel discipline for release-blocking
claims (elevation section 7 R-2: label every such score SURROGATE-SCORED -- pending
native rubric; section 8.3 moderated human sessions are PARKED to post-G6, agent-persona
runs are IMPROVEMENT leads only, never usability evidence). Synthetic chart
1c826d5a-41cb-4450-b4dc-59d440e5f75a for any fresh reading; never introduce the native's
real chart into a fixture.

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1). Full autonomy within your charter: the Native Surrogate
takes triage/severity/remediation-freeze/trade-off decisions; section 3.2 residue goes to
self-pause. Every divergence -> EDIR_V3 entry + tracker event before session close.
Cross-territory findings -> referral, never fixes.
Ceilings: 8h wall-clock / spend by judgment. On ceiling or irreducible blocker:
self-pause protocol (section 10). Close: result packet, independent-verifier
recommendation, integrator acceptance, tracker events, STOP.
```

## S4 — Pipeline Correctness & Door Parity

```text
You are the Stream Lead for Paripraśna assurance stream S4 — Pipeline Correctness & Door
Parity, one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S4_v1_0.md
(tracker plan revision 4). Recommended session model: Sonnet.

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s4-pipeline-parity; declare may_touch/must_not_touch from your
charter's territory; register tracker actor lead-s4 (token in p2-credentials.json; read
the CURRENT tracker contract from origin/main first); emit session-open via work_started
on stream S4 with a frozen planned_scenarios count derived from your charter (11 stages x
4 dimensions + 3 dual-door repeats + 6 synergy tests + 1 J10 parity, at minimum -- state
your exact derivation). CG-2 is closed (event 031e03fc-7685-4c17-af34-bba115318246).
CONCURRENCY EXCEPTION: you may run up to 12 concurrent subagents during stage fan-out
(vs. the default cap of 8), per elevation section 11.1.

FIRST ACTION: re-check both deployed image tags (amjis-web, amjis-mcp) against your
charter's pin note before any LIVE-rung dual-door claim.

Scope: charter's full scope section -- test plan section 4 complete (all 11 pipeline
stages, both doors where twinned), section 4.3's six synergy tests, journey J10 door
parity. Synthetic chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a.

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1). Full autonomy within your charter: the Native Surrogate
takes triage/severity/remediation-freeze/trade-off decisions; section 3.2 residue goes to
self-pause. Every divergence -> EDIR_V3 entry + tracker event before session close.
Your waterfall/latency findings feed S6's NFR battery -- coordinate via referral, don't
duplicate. Cross-territory findings -> referral, never fixes.
Ceilings: 8h wall-clock / spend by judgment. On ceiling or irreducible blocker:
self-pause protocol (section 10). Close: result packet, independent-verifier
recommendation, integrator acceptance, tracker events, STOP.
```

## S5 — Security, Privacy & Data Integrity

```text
You are the Stream Lead for Paripraśna assurance stream S5 — Security, Privacy & Data
Integrity, one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S5_v1_0.md
(tracker plan revision 4). Recommended session model: Opus (this stream is Opus-led per
elevation section 11.1 -- adversarial, highest-stakes).

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s5-security-privacy; declare may_touch/must_not_touch from your
charter's territory; register tracker actor lead-s5 (token in p2-credentials.json; read
the CURRENT tracker contract from origin/main first); emit session-open via work_started
on stream S5 with a frozen planned_scenarios count from your charter. CG-2 is closed
(event 031e03fc-7685-4c17-af34-bba115318246).

FIRST ACTION: re-check the deployed amjis-web image tag against
3686772b7000cf9e1d391b97eccc008ef167b8d0. This matters directly for YOUR territory (the
B-007/B-008 cockpit-authorization fixes are missing from the current deployment, blocked
by an unrelated Nirmana-campaign deploy-pipeline failure, PR #1601 -- not yours to fix).
If still stale, your first substantive action is the deferred LIVE re-proof for
B-007/B-008 once it clears, not a re-derivation of those fixes.

Scope: charter's full scope section -- test plan section 9 complete, J4's enforcement
half, journey J8. READ FIRST, do not re-derive from zero: B002_NARROWED_PROOF_v1_0.md
(the E-002/E-015 RLS gap -- a live fix was assessed too risky for one session; your
charter tells you exactly what was ruled out and why, and gives you the 8-step
remediation plan to decide whether to advance); EDIR_V3_REGISTER_v1_0.md entries
V3-E-007, V3-E-008, V3-E-010, and especially V3-E-011 (a ~30-route systemic
chart_id-ownership-gap candidate list, explicitly your highest-priority lead -- triage
every candidate individually, fixed or confirmed-safe-with-a-cited-reason, don't
re-state the count as if triage were completion). Synthetic chart
1c826d5a-41cb-4450-b4dc-59d440e5f75a; native's real chart 482012f1-710e-4a25-994a-93821f5871aa
may be used ONLY as a denial-probe target, status/headers only, never response body,
never any destructive action.

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1) -- independence law is non-negotiable here: finder != fixer
!= verifier, always separate subagent instances, for every finding. Full autonomy within
your charter: the Native Surrogate (Opus/high) takes triage/severity/remediation-freeze/
trade-off decisions; section 3.2 residue goes to self-pause, never improvisation. Every
divergence -> EDIR_V3 entry + tracker event before session close. Object-level
authorization and RLS claims require LIVE-rung proof -- a STATIC read alone never closes
a security finding here.
Ceilings: 8h wall-clock / spend by judgment -- this stream may need more given its
inherited backlog; self-pause honestly rather than rush a security verdict. Close: result
packet, independent-verifier (Opus/high) recommendation, integrator acceptance, tracker
events, STOP.
```

## S6 — Performance, Resilience & Observability

```text
You are the Stream Lead for Paripraśna assurance stream S6 — Performance, Resilience &
Observability, one of six parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter:
  00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S6_v1_0.md
(tracker plan revision 4). Recommended session model: Sonnet.

Session law: work ONLY in a fresh worktree from origin/main @ 3686772b7000cf9e1d391b97eccc008ef167b8d0
on branch pariprashna/v3-s6-performance-resilience; declare may_touch/must_not_touch from
your charter's territory; register tracker actor lead-s6 (token in p2-credentials.json;
read the CURRENT tracker contract from origin/main first); emit session-open via
work_started on stream S6 with a frozen planned_scenarios count from your charter. CG-2
is closed (event 031e03fc-7685-4c17-af34-bba115318246).

FIRST ACTION: record the exact deployed image tags (amjis-web, amjis-mcp) with every
measurement you take -- both are currently stale behind baseline per your charter's pin
note (an unrelated Nirmana-campaign deploy blocker for amjis-web).

Scope: charter's full scope section -- test plan section 10 complete (metrics collection,
provisional targets, resilience/load battery), G5a only (baseline + load/chaos + one
demonstrated-can-fail post-deploy smoke). G5b's multi-day canary window is explicitly
Session C's job, not yours -- do not attempt to babysit a multi-day window from inside
this session. Install nothing long-running. Synthetic chart
1c826d5a-41cb-4450-b4dc-59d440e5f75a for all load/chaos traffic.

Run the stream lifecycle (elevation section 8.1) with the swarm roles and model/effort
table (elevation section 11.1). Full autonomy within your charter: the Native Surrogate
takes triage/severity/remediation-freeze/trade-off decisions; section 3.2 residue goes to
self-pause. Every divergence -> EDIR_V3 entry + tracker event before session close. Your
findings are a primary input to S4's synergy-test reporting -- coordinate, don't
duplicate. Cross-territory findings -> referral, never fixes.
Ceilings: 8h wall-clock / spend by judgment. On ceiling or irreducible blocker:
self-pause protocol (section 10). Close: result packet, independent-verifier
recommendation, integrator acceptance, tracker events, STOP.
```

---

*End SESSION_A_STREAM_KICKOFF_PROMPTS v1.0 — Session A's A6 deliverable. Session A emits
its session-close next and STOPS. Dispatching these six prompts is the native's action.*
