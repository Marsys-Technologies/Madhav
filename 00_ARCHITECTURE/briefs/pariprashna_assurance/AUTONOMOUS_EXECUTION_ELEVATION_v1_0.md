---
artifact: PARIPRASHNA_AUTONOMOUS_EXECUTION_ELEVATION
version: 1.1
status: CURRENT — the execution layer over the CURRENT master test plan
  (PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md). Governs HOW the
  campaign runs (autonomy, swarm roles, sessions, tracker integration,
  git/worktree law, prior-work absorption); the test plan governs WHAT is
  tested; the campaign dependency law (P0→P1→P2→P3→…) still governs WHEN.
date: 2026-08-27
authoritative_side: claude
authorized_by: >
  Native directive, Claude Code session 2026-08-27 (recorded verbatim in §2):
  run the campaign fully autonomously with an agentic swarm and no human gates
  up to the start of the six P3 streams; run the six streams as six parallel
  sessions; converge into a single closure session; use a Native Surrogate to
  keep decisions flowing; absorb all prior work; build the tracker into the
  campaign so it never goes stale and adapts to plan changes.
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/TEST_PLAN_PROMOTION_DECISION_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P1_CLOSURE_PACKET_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/ELEVATION_PLAN_v1_0.json
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/ELEVATION_RUNBOOK_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/templates/STREAM_CHARTER_TEMPLATE.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/templates/STREAM_RESULT_PACKET_TEMPLATE.md
  - /Users/Dev/Documents/Pariprashna-Handoff/PARIPRASHNA_CODEX_TO_CLAUDE_CODE_HANDOFF_v1_0.md
changelog:
  - "1.1 (2026-08-27, Claude Code wrap-up session): sequencing decision — the
    tracker-elevation build (originally scoped as Session A's own Phase A1,
    §5.1/§7) is pulled OUT of Session A and run instead as its own dedicated
    session BEFORE Session A opens, per native direction 2026-08-27: a clean
    go/no-go checkpoint before committing to an 8h autonomous Session A run,
    rather than discovering a tracker-build failure partway through it. §7's
    phase table now states this as a precondition Session A's A0 VERIFIES
    (PR merge SHA, launchd job confirmation, freshness-proof timestamp,
    plan-revision-2 registration) rather than performs; §5.1 and §5.3.2
    reworded to match (the precondition session registers plan revision 2 for
    its own scope change; Session A's A0 registers plan revision 3 for the
    elevation-onto-registry mapping previously called revision 2); §11.3's
    Session A kickoff prompt gains a 'Tracker precondition' block with
    placeholders for the evidence, to be filled once the precondition session
    closes and hands its result to Session A."
  - "1.0 (2026-08-27, Claude Code / Fable): initial elevation, authored from a
    line-by-line review of test plan v2.1 (§1 findings) under the native's
    autonomy directive."
---

# Paripraśna — Autonomous Execution Elevation v1.0

## 0 — How to read this document

The campaign now has three governing layers, deliberately separated:

| Layer | Artifact | Question it answers |
|---|---|---|
| WHAT to test | `PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md` (CURRENT) | Programmes P-PIPE / P-PORTAL / P-GUIDED, quality/a11y/security/perf batteries, gates G1–G9, deliverables |
| WHEN it may run | Campaign dependency + progress law (handoff §4; tracker plan registry `ELEVATION_PLAN_v1_0.json`) | P0→P1→P2→P3(S1–S6)→P4→P5→P6→P7; evidence-earned progress only |
| HOW it runs | **This document** | Autonomy charter, swarm roles + model/effort, session topology, tracker anti-staleness law, prior-work absorption, git/worktree/deploy/cleanup law, prompt pack |

Nothing here loosens the test plan's proof law (STATIC → REPLAY → INTEGRATION →
LIVE → NATIVE ACCEPTANCE), its test-data law (synthetic chart `1c826d5a` by
default; the native's real chart `482012f1` only under specific authorization),
or the tracker's progress law (no actor submits a percentage; unknown/stale
earns zero). Autonomy changes who takes routine decisions, not what counts as
evidence.

## 1 — Review of test plan v2.1: findings that drive this elevation

A full line-by-line review of the promoted plan was performed 2026-08-27. The
plan is structurally sound and unusually honest — the three-programme design,
per-stage code anchors (§4.1), quantitative optimality criteria (§4.2), the
divergence discipline (§6.2), and the seeded-EDIR start (§6.3) are all kept
unchanged. Ten findings, however, must be resolved by this elevation for the
plan to be executable autonomously. Each carries its disposition here.

| # | Finding | Disposition in this elevation |
|---|---|---|
| R-1 | **Credential blocker (§5.0):** the browser battery's Firebase session for the synthetic chart is marked "NOT provisioned for agent use — native to provision." Under a no-human-gates directive this is the single hardest dependency. | §7 lane A2-CRED: Session A first attempts self-provisioning through EXISTING repo infrastructure (Firebase Admin SDK custom token minting for a test user bound to chart `1c826d5a` only, using credentials already present in the environment — no new secrets). If minting succeeds: scope-prove via cross-chart denial probe, document, proceed. If it genuinely requires a new secret only the native can create: file it as the ONE named native-provisioned input, notify, and degrade P-PORTAL lanes honestly (the historical campaign's correct behavior) rather than fake or bypass. |
| R-2 | **Human-review dependencies (§7 blinded native review, §8.3 moderated usability sessions, G6/AC-15):** three places require literal humans. | §3: G6 native acceptance is the ONE irreducible native gate — Session C prepares the packet and pauses there. §7's "blinded human/native review" is replaced pre-G6 by a blinded multi-model refuter panel labeled `SURROGATE-SCORED — pending native rubric`, feeding the same rubric the native later completes. §8.3 moderated human sessions are PARKED to post-G6 (they cannot be honestly simulated); agent-persona runs may inform findings but are filed as IMPROVEMENT leads, never as usability evidence. |
| R-3 | **Two-week wall-clock windows (§4.2 baseline ratification, §10.2 NFR, G5 canary "seven consecutive green smokes"):** incompatible with session-bounded autonomy. | §9: G5 splits into G5a (in-session: baseline measurement, load/chaos battery, demonstrated-can-fail smoke — closable by Session C) and G5b (calendar evidence: scheduled monitors/cron accumulate the multi-day smoke record; tracker ingests results; G5b closes when the window completes, without a live session babysitting it). SLO targets stay provisional until G5b ratifies them. |
| R-4 | **EDIR location:** the plan's primary output register lives only on the quarantined historical branch (`pariprashna_swarm/…REGISTER_v1_0.md`, 7,944 lines, append-only). New findings need a live register on main; duplicating the old one invites GA.1-class divergence. | §6.4: Session A opens `EDIR_V3_REGISTER_v1_0.md` in this folder — a NEW register, numbered `V3-E-nnn`, whose §0 imports the historical entries BY REFERENCE (id, title, class, severity, status at self-pause) without copying their bodies. Same schema and register law as plan §6.3. Historical entries that reproduce on the current artifact get a fresh V3 entry citing the old id as provenance. |
| R-5 | **Plan predates the campaign structure:** v2.1 speaks G1–G9 and knows nothing of P0–P7/CG-gates or the six streams. | §4 crosswalk table binds them permanently: G1→P2, P-PIPE baselining→P2/P3-S4, G2→S1+S2, G3→S3, G4→S4, G1 security battery→S5, G5→S6+P5, G6→P6, G7–G9→P7. The tracker's registered catalogue (P-PIPE stages S1–S11, journeys J1–J10, lenses) flips from `historical-observation-only` to `current-assurance` via plan revision (§5.3 step 2). |
| R-6 | **No autonomy/decision model:** the plan assumes a native in the loop for triage severity, remediation freezes, and product trade-offs. | §3 Native Surrogate charter with an explicit delegation boundary and a decision ledger (every surrogate decision = tracker event + register row, tagged `SURROGATE DECISION`). |
| R-7 | **No tracker integration:** the plan never mentions the v3 control plane; run it as written and the tracker goes stale on day one — the exact divergence the native flagged. | §5 Tracker Integration Law — the tracker worker lands FIRST (before any campaign work), every lifecycle transition emits an event, freshness budgets are enforced, and any scope change lands as a tracker plan revision BEFORE the work proceeds. Tracker divergence is itself an S1-severity PROCESS defect. |
| R-8 | **Prior work unabsorbed:** ~70 unmerged `origin/pariprashna/*` branches (p2*, p3-preflight-part-a..h, p4-census/g/h/i/j/k, tracker-v2*, governance-close, closeout-*) plus `codex/pariprashna-shadow-sync` (`5f30acf4d`, the elevation worker) are inventoried nowhere current. | §7 lane A3-ABSORB: full branch census with per-branch disposition (SALVAGE via fresh governed PR / SUPERSEDED / EVIDENCE-ONLY / ARCHIVE), filed to the tracker. Nothing merges wholesale; nothing is silently ignored. |
| R-9 | **Stream isolation unspecified:** the plan says what each battery covers but not how six parallel sessions avoid colliding. | §8: one worktree + one branch per stream, disjoint primary file territories, cross-stream referral protocol (a finding in another stream's territory is FILED to that stream via the tracker, never fixed cross-territory), integrator-owned merge ordering at convergence. |
| R-10 | **No self-pause/failure protocol:** autonomy without a stop discipline thrashes. | §10: inherited from the historical campaign's one proven success — on ceiling, irreducible blocker, or safety flag: emit handoff packet + tracker event, freeze state, stop. Never loop on a blocked gate; never widen authority to get unstuck. |

## 2 — Authority: the native directive of 2026-08-27

Recorded as given (lightly punctuated): run the campaign fully autonomously
using an agentic swarm, no human gates, up to the point the six streams begin;
run the six streams as six parallel sessions; then converge back into a single
session and drive it to closure. Within sessions, full autonomy. Assign the
right model and effort level per role — balanced, neither overkill nor
underplayed. At the stop before the six streams, deliver six kickoff prompts
that can run in parallel. Enforce work isolation via worktrees. At appropriate
times commit, merge branches, push to GitHub, keep deployed main and
production in sync and clean, then clean up. Include a Native Surrogate to
take decisions that would otherwise interrupt autonomy. Absorb, review, and
induct all work done so far. Build the existing Paripraśna tracker into the
whole campaign so it keeps full visibility, never goes stale, and adapts to
plan changes as they happen.

This directive is the standing authorization this elevation executes. It
supersedes, for this campaign, the handoff's default reservation of routine
decisions to the native — with the explicit residue in §3.2.

## 3 — Autonomy charter

### 3.1 The Native Surrogate

A dedicated swarm role (model/effort in §Model table) that stands in for the
native on every decision the campaign needs to keep moving. It:

- assigns severity at triage (per plan §6.3 register law — never the finder);
- freezes remediation plans and scope denominators;
- resolves routine product trade-offs and interprets ambiguous requirements
  against the ratified architecture docs;
- authorizes bounded scope changes (which MUST land as tracker plan revisions
  per §5.3 before work proceeds);
- may authorize the E7 tracker cutover (accepted 8787 ← shadow 8788) ONLY if
  the full E7 packet criteria pass — parity window clean, restore parity
  proven, rollback rehearsed and reversible — otherwise 8787 stays
  authoritative and the campaign continues on it;
- records EVERY decision as a tracker event plus an `EDIR_V3` /
  decision-ledger row tagged `SURROGATE DECISION — not native acceptance`.

Every surrogate decision is reviewable and reversible by the native after the
fact; the ledger exists so that review is a read, not an archaeology dig.

### 3.2 Reserved to the native (the irreducible residue)

1. **CG-6 / G6 native acceptance** — definitionally the native's lived
   seven-day verdict; the plan itself forbids surrogate substitution and this
   elevation keeps that. Session C pauses here.
2. **Any use of the native's real chart (`482012f1`)** beyond what the test
   plan's test-data law already permits — no surrogate may authorize it.
3. **Creation of genuinely new external credentials/secrets** (R-1 fallback
   path) — the surrogate may direct use of existing credentials within their
   existing scope, never mint authority the environment doesn't already hold.
4. **Spend beyond ceilings**: each session carries the ceilings in its kickoff
   prompt; the surrogate may reallocate within a ceiling, never raise one.
5. **The P7 release/no-go decision** — prepared autonomously, decided by the
   native (it follows G6 anyway).

Everything else — including P2 `work_started`, blocker remediation approvals,
CG-2 closure, stream dispatch, merge/deploy actions within the git law, and
tracker cutover under §3.1's condition — is delegated.

### 3.3 Independence law (unchanged, now enforced by role separation)

Finder ≠ fixer ≠ verifier for the same item, always separate subagent
instances. Gate closures are recommended by an Independent Verifier and
accepted by the Programme Integrator; neither may be the lane's implementer.
The tracker's actor model (scoped actors, role/stream authorization) is the
enforcement surface: each role registers as its own actor id.

## 4 — Crosswalk: test plan ↔ campaign ↔ streams ↔ tracker

| Test plan element | Campaign phase | Stream owner | Tracker catalogue id |
|---|---|---|---|
| §11.1 Preflight (pin revision, credential, environment) | P2 (Session A) | — | P2 work items |
| §11.2 / §9 G1 safety-integrity battery (E-001/E-002 seeds) | P2 blockers B-001/B-002 → deep battery in S5 | S5 | PPR + EDIR refs |
| §4 P-PIPE stage baselines + boundary contracts | P2 exit criteria (baseline established) → full programme in S4 | S4 | P-PIPE S1–S11 |
| §5 P-PORTAL battery: sidebar/history regions | P3 | S1 | P-PORTAL J1,J7 + regions |
| §5 P-PORTAL battery: viewport/working/dock/composer | P3 | S2 | P-PORTAL J2,J3,J5,J6,J9 |
| §7 reading quality + epistemic corpus (G3) | P3 | S3 | quality dimensions |
| §4.3.6 + J10 door parity (G4) | P3 | S4 | P-PORTAL J10 |
| §9 security/privacy/consent/DR battery | P3 | S5 | PPR security rows |
| §10 performance/resilience/observability (G5a) | P3 | S6 | NFR rows |
| §8.1/§8.2 visual + a11y batteries | P3 | S1+S2 (split by region) | a11y rows |
| §5.2 journeys J4, J8 (sensitive handling, prediction lifecycle) | P3 | S3 (J4 quality/safety language) + S5 (J4 enforcement, J8 integrity) | P-PORTAL J4,J8 |
| §11.4–.7 G2–G5 gate closes + cross-stream regression | P4/P5 (Session C) | integrator | CG-3..CG-5 |
| G5 multi-day canary (G5b) | P5 (calendar evidence, §9 below) | scheduled monitors | CG-5 |
| G6 native acceptance | P6 (native) | — | CG-6 |
| §11.9–.11 G7 hygiene / G8 feedback-dispute / G9 calibration seal | P7 (Session C after G6) | integrator | CG-7 |

## 5 — Tracker Integration Law (anti-staleness, anti-divergence)

The accepted event-sourced tracker (`127.0.0.1:8787`, launchd
`com.marsys.pariprashna-assurance-control`) is the campaign's lifecycle
authority; the shadow elevation service (`127.0.0.1:8788`, `/api/elevation`)
is its observation/reconciliation layer. Both already exist and are running.
The rules:

### 5.1 The tracker comes first, not alongside

A dedicated tracker-elevation precondition session, run BEFORE Session A
opens (2026-08-27 sequencing decision — this was originally scoped as
Session A's own Phase A1; native direction pulled it out as a standalone
go/no-go checkpoint ahead of the 8h autonomous run; see §7 and §12
changelog), completes the tracker's autonomous synchronization: replay the
`elevation_worker.py` candidate (`codex/pariprashna-shadow-sync` @
`5f30acf4d` — 2 files, ~260 lines, zero drift against current main in its
directory as verified 2026-08-27) onto fresh main; failing integration test
first (source age must advance with NO manual API call); protected PR;
attested release; shadow-scoped launchd worker; then a no-manual-refresh
observation window in which every configured source
(codex/github/git-worktree/runtime/tests, EDIR) stays inside its freshness
budget or visibly degrades. Only when the tracker demonstrably cannot go
stale on its own does campaign work begin — Session A's A0 phase VERIFIES
this evidence (§7) rather than re-performing the build. This is the direct
answer to "the tracker generally diverges."

### 5.2 Every lifecycle transition is an event

Emitted via the tracker API by the session's Tracker Ops role, at minimum:
session open/close (with actor + scope), `work_started`/`work_accepted` per
work item, evidence links (PR URL, CI run, EDIR entry, screenshot/transcript
URI) per acceptance, gate open/close recommendations and integrator
acceptances, surrogate decisions, plan revisions, self-pause packets.
Progress is thereby derived, never asserted — the existing progress law does
the math.

### 5.3 Plan changes flow THROUGH the tracker, never around it

The adapt-to-change requirement, made mechanical:

1. Any scope change (add/split/merge/park/reweight a work item; move a
   scenario between streams; a stream discovering its denominator grew) is
   first authorized by the surrogate, then registered as a NEW immutable plan
   revision via the tracker's plan registry (the E4 engine the merged
   foundation already contains), THEN executed. Work against an unregistered
   scope change is invalid work.
2. The tracker-elevation precondition session (§5.1, §7) registers **plan
   revision 2** at its own open, covering its own scope change (the A1
   sequencing pull-out itself, plus the tracker-fix work). Session A's A0
   VERIFIES revision 2 is live (§7) and then registers **plan revision 3** at
   its own open: mapping this elevation onto the registry — the P2 blocker
   denominator as work items, S1–S6 charters as stream scopes, the
   P-PIPE/P-PORTAL/P-GUIDED catalogues flipped from
   `historical-observation-only` to `current-assurance`, G5 split into
   G5a/G5b, and the G→CG crosswalk of §4.
3. Displayed completion is allowed to DROP when a revision honestly grows the
   denominator; hiding that is the named anti-pattern.
4. Old revisions stay replayable; no revision rewrites history.

### 5.4 Freshness budgets and the staleness alarm

Per-source budgets (registered in revision 2; defaults: git/GitHub 15 min
during active sessions, runtime identity 30 min, tests/evidence 60 min, EDIR
60 min). A source outside budget renders as degraded on the dashboard AND
raises an alert observation; two consecutive breaches file an automatic
PROCESS defect in EDIR_V3. A completed session must never present as a
stale-running warning (the known liveness defect — its fix is part of A1's
acceptance).

### 5.5 The one-register rule

Campaign findings live in exactly one current register (`EDIR_V3_REGISTER`,
§6.4) and are LINKED from tracker events — the tracker holds lifecycle and
pointers, the register holds finding bodies. At every session close, a parity
check (register row counts by status vs. tracker projection) runs; divergence
is an S1 PROCESS defect filed before the session may close.

## 6 — Prior-work absorption and induction (lane A3-ABSORB)

### 6.1 Inputs

- The ~70 unmerged `origin/pariprashna/*` branches (2026-08-19..23): the
  `p2`/`p2-final`/`p2-close-*`/`p2-epistemic` family, `p3-preflight-part-a..h(+close)`,
  `p4-census/g/h/i/j/k`, `tracker-v2*` (10 branches), `governance-close`,
  `register-closeout`, `closeout-*`, `audit-*`, `dd-*`, `g1-*`, `hs4-fix`,
  `citation-leak-fix`, `probe-harness`, `ledger-fold`, `overnight-close`.
- The unmerged `codex/pariprashna-*` branches (shadow-sync worker, shadow-deploy,
  p0b-option-b, p1 family — the p1 family is closed history, likely ARCHIVE).
- The historical worktree ledgers (`DECISIONS.jsonl` 77 D-PP ids,
  `OBLIGATIONS.jsonl` 53 active, `VERDICTS.jsonl` 53 current, EDIR 115
  findings) — already classified by P1's inventory manifest; consumed as
  evidence, re-derived fresh, never imported as state.
- The merged-but-unintegrated foundation (PR #1550's AdapterRunner et al.).

### 6.2 Disposition classes (every branch gets exactly one, filed to tracker)

| Class | Meaning | Action |
|---|---|---|
| SALVAGE | Contains a fix/test/doc worth landing on current main | Cherry-pick/replay onto a fresh lane branch → failing test where applicable → PR → CI → merge. Credit flows to the CURRENT work item it satisfies. |
| SUPERSEDED | Its intent is already satisfied on main or by a newer branch | Record the superseding evidence; no code action. |
| EVIDENCE-ONLY | Valuable as diagnosis/precedent (e.g. `dd-credential-misdiagnosis` for P2-B-004/005) | Cite from the relevant work item; no merge. |
| ARCHIVE | Closed-history or abandoned | Record reason; branch deleted only in Session C cleanup (never before dispositions are accepted). |

Rule inherited from the handoff: historical material is a LEAD, never a
source to merge wholesale, cite as done, or use to skip reproduction on the
current artifact. A P2 blocker with a SALVAGE-class fix sitting in an old
branch still gets reproduced on current main before the fix lands.

### 6.3 Priority order within A3

`p2`-family and `g1-*`/`hs4-fix`/`citation-leak-fix` first (they bear
directly on P2 blockers), `tracker-v2*` second (against the A1 worker lane),
`p3-preflight-*`/`p4-*` third (they pre-shape stream charters), closeout/
governance branches last (ARCHIVE candidates).

### 6.4 EDIR V3

Session A opens `EDIR_V3_REGISTER_v1_0.md` (this folder) with: the plan
§6.3 schema verbatim; entry ids `V3-E-nnn`; §0 reference-import table of all
historical EDIR entries (id, title, class, proposed severity, status at
self-pause — one line each, bodies stay on the historical branch); the
register law (close only at named rung with dated evidence; RETRACTED keeps
history; severity at triage by the surrogate; never self-certifies a gate).
Historical findings reproduced on the current artifact get fresh V3 entries
with `provenance: E-nnn`.

## 7 — Session A: the autonomous pre-stream campaign session

One session, model per §Model table, running the swarm internally with
parallel lanes where dependencies allow. No human gates. Session A opens
only after the precondition below is satisfied.

**Precondition — tracker-elevation build (satisfied by a separate, dedicated
session run BEFORE Session A opens; originally scoped as this session's own
Phase A1, pulled out 2026-08-27 as a standalone go/no-go checkpoint ahead of
the 8h autonomous run — see §5.1, §5.3.2, §12 changelog):** §5.1 in full —
worker replay → failing test → PR → CI → merge → attested release → launchd
worker → no-manual-refresh freshness proof → completed-session liveness
defect fixed → snapshot/restore re-proof; E7 packet assembled; cutover
decision per §3.1 (either way, recorded); plan revision 2 registered
(§5.3.2). Exit evidence Session A's A0 must confirm: a PR merge SHA, launchd
job (`com.marsys.pariprashna-assurance-control`) confirmation, a
freshness-proof timestamp, and the plan-revision-2 registration.

| Phase | Content | Exit |
|---|---|---|
| **A0 — Open** | Repo session law (fresh worktree from origin/main; AGENTS.md + CLAUDE.md handshake; may_touch/must_not_touch declared). Re-derive live truth: main SHA, both tracker states, worktree/branch inventory, deployed revision. **Verify the tracker-elevation precondition** (above): confirm the PR merge SHA, launchd job confirmation, freshness-proof timestamp, and plan-revision-2 registration are all live and consistent with what this session observes; if any is missing, stale, or contradicted, self-pause (§10) rather than proceed — do NOT perform the tracker build inline. Register tracker plan revision 3, mapping this elevation onto the registry (§5.3.2). Emit session-open event. | Precondition verified (not built); truth re-derived and evented; revision 3 live. |
| **A2 — CRED** | R-1 credential lane: attempt self-provisioning via existing infra; scope-prove with cross-chart denial; else file the named native input and mark P-PORTAL lanes degraded-honest. | Credential working+scope-proven, or honestly degraded with the single ask documented. |
| **A3 — ABSORB** | §6 census and dispositions; SALVAGE lanes landed through PRs; EDIR_V3 opened and seeded. | Every branch dispositioned in tracker; V3 register live. |
| **A4 — P2 clearance** | `work_started` on P2. Freeze blocker denominator (intake's B-001..B-006 ± absorption-surfaced additions via plan revision). Per blocker: reproduce on current artifact → smallest governed fix → independent verify at named rung → PR/CI/merge → deployed re-proof. B-006 stays parked to P6 per its own boundary. Exposure/authz/consent first (B-001, B-002), then B-003/B-004/B-005. | Every required blocker independently accepted. |
| **A5 — CG-2 + charters** | Integrator closes CG-2 (evented). Define "safe to test" record. Freeze six stream charters from the template (baseline SHA, deployed revision pin, scenario denominators from the §4 crosswalk, ceilings, territories per §8.2, credential status, EDIR_V3 seeds). Register charters in a plan revision. | CG-2 CLOSED; six charters frozen and registered. |
| **A6 — Stop + prompt emission** | Fill the six §11.2 prompt templates with pinned values. Emit session-close + handoff packet. **STOP. Do not dispatch streams.** | Six ready-to-paste prompts delivered to the native. |

Ceilings: 8h wall-clock (historical precedent), self-pause per §10 if hit.
Sequencing note: the tracker-elevation precondition blocks Session A from
opening at all (tracker first, now outside the session, verified not built
at A0); within Session A, A2/A3 may run as parallel lanes once A0 clears;
A4 consumes A3's P2-relevant dispositions; A5–A6 are sequential.

## 8 — The six stream sessions (P3)

### 8.1 Common frame

Each stream = one separate session, own worktree + branch
(`pariprashna/v3-s<N>-<slug>`), own charter, own tracker actor, 7.5 campaign
points, the handoff's stream lifecycle (charter/preflight 10% →
frozen-baseline investigation 25% → finding freeze + surrogate triage 10% →
approved remediation 25% → independent verification 20% → stream regression
7% → closure packet 3%). Inside a stream: parallelize investigation fan-out
and independent verifications; keep remediation sequential per file territory.
Every finding lands in EDIR_V3 + tracker before session close (plan §6.2's
"no divergence noted for later"). Streams do NOT merge to main mid-flight
except: (a) S1-severity security fixes (S5 may fast-track through the git
law with integrator + surrogate sign-off), (b) fixes their verifier accepted
that touch ONLY their own territory and pass full CI — everything else queues
for Session C's ordered integration.

### 8.2 Streams, territories, and postures

| Stream | Assurance question (plan §) | Primary file territory (indicative, frozen precisely in charter) | Posture |
|---|---|---|---|
| **S1 — Navigation, Shell & History** (§5.1 sidebar/history rows, §8.1–8.2 for its regions, J1/J7) | Orient, move, return, recover — no confusion, no leakage | `platform/src/components/pariprashna/` shell+sidebar, history routes | Browser-heavy; moderate code tracing |
| **S2 — Conversation & Reading Experience** (§5.1 viewport/working/dock/composer rows, §8 for its regions, J2/J3/J5/J6/J9) | Asking, waiting, reading, recovering — coherent and calm | answer/stream components, reducer, working-region, dock, composer | Browser + replay-fixture heavy |
| **S3 — Answer Quality & Epistemic Trust** (§7 all dimensions, J4-language) | Correct, useful, honestly uncertain, trustworthy | quality corpus, rubric harness, synthesis prompts/policies | Judgment-heavy; corpus mechanics |
| **S4 — Pipeline Correctness & Door Parity** (§4 complete, §4.3, J10) | Every stage earns its claim, on both doors | `pipeline/` stages per §4.1 anchor map, `platform-mcp` twins | Trace/harness-heavy, highest volume |
| **S5 — Security, Privacy & Data Integrity** (§9 complete, J4-enforcement, J8) | Authorized, private, safe, durable, auditable | auth/RLS/audit/consent/prediction-lifecycle surfaces | Adversarial; Opus-led |
| **S6 — Performance, Resilience & Observability** (§10, G5a) | Fast enough, recoverable, operationally truthful | telemetry, SSE/outbox/replay, load-chaos harness | Measurement-heavy |

### 8.3 Cross-stream referral

A finding in another stream's territory: file it in EDIR_V3 tagged with the
owning stream + a tracker referral event; never fix it cross-territory. The
integrator (polled by each stream at its triage and closure points) routes
referrals. Overlap findings (e.g., a11y in the dock: S2 surface vs S1 shell)
resolve by territory, not topic.

### 8.4 Stream closure

Result packet per the existing template, independent-verifier
recommendation, integrator acceptance evented as that stream's CG-3
contribution. The stream session then STOPS — convergence work belongs to
Session C.

## 9 — Session C: convergence and closure

Opens when all six streams closed (or a stream self-paused and the surrogate
rules it non-blocking with recorded rationale — a paused stream's points stay
unearned). Phases: **C0** open/re-derive/event. **C1 (P4)**: ordered
integration of queued stream fixes (integrator sequences by territory
dependency), full cross-stream regression + the ten journeys re-run on ONE
protected integrated revision; CG-3 (all streams) and CG-4 closes. **C2
(P5/G5a)**: baseline+load+chaos battery on the integrated deployed revision;
demonstrated-can-fail post-deploy smoke; install the G5b scheduled monitors
(cron/routine) whose results the tracker ingests; CG-5 closes when G5b's
window completes clean — Session C may close CG-5 conditionally-scheduled and
hand the watch to the tracker. **C3 (P6)**: assemble the native acceptance
packet (seven daily rubric cards pre-structured, evidence index, EDIR_V3
open-items honest list) — **pause for the native**. **C4 (P7, after
verdict)**: G7 hygiene sweep (plan-named GAP-15/GAP-17 + open DOC entries),
G8 feedback/dispute, G9 calibration seal, release decision record
(native-decided), residual-risk register, evidence index seal, **cleanup**:
delete merged campaign branches, remove campaign worktrees, disposition
ARCHIVE-class branches from §6, retire/hand over scheduled monitors, tracker
archive closure per its own runbook. Deployed-production sync check (deployed
revision == main HEAD, clean) is a C1, C2, and C4 exit criterion each time.

## 10 — Self-pause protocol (all sessions)

Triggers: wall-clock/spend ceiling; irreducible blocker (needs §3.2 residue,
or a dependency that cannot be satisfied from inside the session); safety
flag (anything touching the native's real data unexpectedly, a credential
behaving beyond its declared scope, a destructive-operation ambiguity).
Action: freeze work mid-lane cleanly (commit WIP to the lane branch, never to
main), emit a handoff packet (state, evidence, exact resume point, open
decisions), emit tracker self-pause event, STOP. Never: retry-loop a blocked
gate, widen authority, fake a degraded capability, or leave the tracker
unaware. The historical campaign's self-pause is the proven reference
behavior.

## 11 — Model & effort assignments and the prompt pack

### 11.1 Balanced model/effort table

Session main loops: **Session A and Session C on Fable** (integrator-heavy,
long-horizon judgment) · **S3 and S5 on Opus** (epistemic judgment;
adversarial security) · **S1, S2, S4, S6 on Sonnet** (high-volume
tool-driven investigation). Subagent roles within any session:

| Role | Model | Effort | Why balanced |
|---|---|---|---|
| Native Surrogate | Opus | high | Low call volume, judgment-dense; consistency across sessions matters |
| Programme Integrator (when subagent, e.g. polled by streams) | inherit session | high | Gate/dependency law enforcement |
| Independent Verifier — default | Sonnet | high | Must actively falsify, moderate volume |
| Independent Verifier — S1-severity, security-class, gate closures | Opus | high | Highest-stakes acceptances |
| Finder/Investigator (code tracing, stage harness) | Sonnet | medium | High volume; escalates to guided mode on anomaly |
| Browser journey driver (Playwright/CDP) | Sonnet | medium | Tool-heavy, procedural |
| Adversarial refuter panel (release-blocking claims, §7 scoring) | Opus | high | Small panel (3), only where the plan demands refutation |
| Mechanical: census, evidence filing, screenshot collation, grep sweeps | Haiku 4.5 | low | Deterministic, cheap, plentiful |
| Tracker Ops (event emission, freshness checks) | Haiku 4.5 | low | API calls against fixed schemas |
| Quality-corpus scorer (deterministic dimensions) | Sonnet | medium | Rubric application at volume |

Concurrency: default cap 8 concurrent subagents per session; S4 may run 12
during stage fan-out. No swarm member impersonates a governed role it wasn't
registered as (tracker actor ids enforce).

### 11.2 Prompt pack

**The Session A kickoff prompt is maintained in §11.3 below** — it is the
one the native pastes next. The six stream prompts are TEMPLATES here;
Session A Phase A6 emits them with `{{pins}}` filled (baseline SHA, deployed
revision, tracker plan revision + charter ids, credential status, EDIR_V3
seed list, ceilings) — a template pasted un-pinned is invalid.

Template skeleton (identical frame for S1–S6; the stream-specific block
varies):

```text
You are the Stream Lead for Paripraśna assurance stream {{S# — name}}, one of six
parallel stream sessions of the autonomous campaign governed by:
  00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md  (HOW)
  00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md  (WHAT)
Read both in full, then your frozen charter: {{charter_path}} (tracker plan revision {{rev}}).
Recommended session model: {{model}}.

Session law: work ONLY in a fresh worktree from origin/main @ {{baseline_sha}} on branch
pariprashna/v3-s{{n}}-{{slug}}; declare may_touch/must_not_touch from your charter territory;
register tracker actor {{actor_id}}; emit session-open. CG-2 is closed ({{cg2_evidence}});
your entry gate is satisfied — do not re-litigate it.

Scope: {{stream-specific battery — plan § references, journey ids, scenario denominator,
      code territory, evidence rungs required per scenario}}.
Credential status: {{cred_state}}. Deployed revision pin: {{deploy_pin}}.

Run the stream lifecycle (elevation §8.1) with the swarm roles and model/effort table
(elevation §11.1). Full autonomy within your charter: the Native Surrogate (spawn per
§11.1) takes triage/severity/remediation-freeze/trade-off decisions; §3.2 residue goes
to self-pause, never improvisation. Every divergence → EDIR_V3 entry + tracker event
before session close. Cross-territory findings → referral (§8.3), never fixes.
Merges to main only per §8.1's two exceptions; all else queues for convergence.
Ceilings: {{wall_clock}} / {{spend}}. On ceiling or irreducible blocker: self-pause
protocol (§10). Close: result packet per template, independent-verifier recommendation,
integrator acceptance, tracker events, STOP.
```

Stream-specific blocks (summary; Session A expands from §4 + §8.2):
- **S1**: plan §5.1 sidebar/history rows + §8.1–8.2 for shell regions; J1, J7; cross-chart denial re-proof at LIVE rung; large-history and device-return scenarios.
- **S2**: §5.1 viewport/working/dock/composer rows + §8 for its regions; J2, J3, J5, J6, J9; settled-block stability, live-tail, caret/scroll, reduced-motion/zoom.
- **S3**: §7 full corpus (≥5 fixtures × 12 work classes before qualification), all eight dimensions scored separately; J4 language; refuter panel on release-blocking claims; `SURROGATE-SCORED` labeling per elevation R-2.
- **S4**: §4 complete — per-stage correctness/optimality/failure-honesty/demonstrated-can-fail on all 11 stages, both doors; §4.3 six synergy tests; J10 whole-receipt parity; waterfall feeds S6.
- **S5**: §9 complete — E-001/E-002 lineage re-verification post-P2, hard-stop corpus, injection, plan-closure, RLS/roles/grants, consent lifecycle, audit immutability, prediction lifecycle (J8), J4 enforcement path, restore drill (within authority).
- **S6**: §10 complete — metrics collection live, G5a baselines, load/chaos battery, reconnect/replay TTL cases, cost ceilings, silent-degradation prevention; installs nothing long-running (that's Session C's G5b).

### 11.3 Session A kickoff prompt (paste-ready)

```text
You are the Programme Integrator opening Session A — the autonomous pre-stream session of
the Paripraśna Experience Assurance campaign (v3). Recommended model: Fable; this session
runs with NO human gates under the native's standing directive of 2026-08-27.

Governing documents — read IN FULL, in order, before any substantive action:
1. AGENTS.md, then CLAUDE.md (repo session law; emit the session-open handshake with
   may_touch/must_not_touch).
2. 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md —
   this session IS its §7 (phases A0–A6). Follow it exactly.
3. 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md.
4. 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md and
   P1_CLOSURE_PACKET_v1_0.md.
5. /Users/Dev/Documents/Pariprashna-Handoff/PARIPRASHNA_CODEX_TO_CLAUDE_CODE_HANDOFF_v1_0.md
   (state map; its authority boundaries are superseded ONLY where elevation §2/§3 says so).

Tracker precondition (2026-08-27 sequencing decision, elevation §5.1/§7/§12) — verify this at
A0 BEFORE proceeding to A2; do NOT perform the tracker build yourself, it runs as its own
dedicated session before this one:
- PR merge SHA (tracker worker landing): {{tracker_precondition_pr_merge_sha}}
- launchd job confirmation (com.marsys.pariprashna-assurance-control loaded and running):
  {{tracker_precondition_launchd_confirmation}}
- Freshness-proof timestamp (no-manual-refresh observation window result):
  {{tracker_precondition_freshness_proof_timestamp}}
- Plan-revision-2 registration id (tracker plan registry):
  {{tracker_precondition_plan_revision_2_id}}
If any placeholder above is unfilled, missing, or contradicted by what you observe live at A0,
self-pause per elevation §10 (packet, event, STOP) rather than proceeding or attempting the
build inline.

Hard frame:
- Work exclusively in fresh worktrees cut from current origin/main. Never build in
  /Users/Dev/Vibe-Coding/Apps/Madhav's shared checkout, campaign/nirmana-autonomous, or any
  historical Paripraśna worktree. A clean prepped worktree exists and may be fast-forwarded and
  reused: .clone/worktrees/pariprashna-assurance-p2 (Phase A4); its .claude/KICKOFF_BRIEF.md
  carries verified context. (.clone/worktrees/pariprashna-tracker-elevation-worker was the
  precondition session's own worktree, not Session A's — do not build in it.)
- Tracker precondition already satisfied (above) — verify, do not rebuild. The accepted tracker
  is 127.0.0.1:8787; shadow is 127.0.0.1:8788.
- Spawn the swarm per elevation §11.1 (Native Surrogate on Opus/high for all decisions the
  elevation delegates; verifiers independent of finders/fixers; Haiku for mechanical lanes).
  Register distinct tracker actors per role.
- Synthetic chart 1c826d5a only. The native's real chart 482012f1 is out of bounds (§3.2).
- Every phase exit, decision, PR, and finding → tracker event; findings → EDIR_V3 (open it
  in Phase A3). Scope changes → tracker plan revision BEFORE execution (§5.3).
- Ceilings: 8h wall-clock for this session. On ceiling/irreducible blocker/safety flag:
  self-pause protocol (elevation §10) — packet, event, STOP.

Execute phases A0→A6. At A6: freeze the six stream charters, fill the six stream prompt
templates (elevation §11.2) with pinned values, present all six prompts to the native,
emit session-close, and STOP. Do NOT dispatch any stream yourself.
```

### 11.4 Session C kickoff prompt (paste-ready, use after all six streams close)

```text
You are the Programme Integrator opening Session C — convergence and closure of the
Paripraśna Experience Assurance campaign (v3). Recommended model: Fable. Read, in order:
AGENTS.md, CLAUDE.md (handshake), AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md (§9 is this
session), the six stream result packets ({{paths — from tracker}}), EDIR_V3_REGISTER, and
the tracker's current projection. Verify all six streams are integrator-accepted (or
surrogate-ruled non-blocking with points unearned). Fresh worktree from origin/main; swarm
per §11.1; tracker events throughout; plan revisions for any scope change. Execute C0→C4:
ordered integration + full regression (CG-3/CG-4), G5a battery + G5b scheduled monitors
(CG-5 per §9), assemble the native acceptance packet and PAUSE at P6 for the native's
seven-day verdict — that gate is never yours. After the verdict: G7–G9, release decision
record (native-decided), cleanup per §9 C4, tracker archive closure, final session-close.
```

## 12 — Change handling for this document

This elevation is itself under B.8 versioning: material changes bump the
version with a changelog entry AND land as a tracker plan revision (§5.3).
The test plan v2.1 body stays untouched by this document; if a stream's
evidence shows the test plan itself needs revision, that is a v2.2 proposal
through its own governed path, filed by the integrator with surrogate
authorization.

*End AUTONOMOUS_EXECUTION_ELEVATION v1.0.*
