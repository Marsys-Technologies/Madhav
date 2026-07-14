---
artifact: DOCTRINE_WAVES_CONDUCTOR_PROTOCOL
type: STANDING PROTOCOL (governs every wave conductor D-1.5a → D-4)
version: 1.0
status: CURRENT
authored_by: Fable 5 (Claude Code planning session, 2026-07-15), native-directed
governing_plan: 00_ARCHITECTURE/DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md (v1.1 FINAL)
native_directives:
  - Fully autonomous execution, bypass permissions, NO human gates. Human-intervention questions
    are handled by the Adjudicator agent (§4); certain classes PARK instead (§4.3).
  - Implementation model = Sonnet (cockpit default). Escalation to Opus/Fable per the model
    matrix (§5) is pre-approved by the native (2026-07-15).
  - Every wave: isolated environments → implement → verify → merge → deploy → rebuild →
    MCP-verify through the MARSYS-JIS connector → cleanup → next wave. A wave is DONE only when
    its MCP gate battery is green on the deployed connector (R-5).
---

# Doctrine-Waves Conductor Protocol

## §0 — What this document is

The standing operating system for the D-1.5a → D-4 autonomous campaign. Each wave's conductor is a
FRESH session that reads exactly three things: **this protocol**, **its wave's bound brief**
(BRIEF_D*.md in this directory), and **the previous wave's close report**. No conversation-memory
handoff — artifacts only. The conductor executes the §2 lifecycle deterministically; verification
is structural, not a norm.

## §1 — Roles

| Role | Model | Duty | Hard rule |
|---|---|---|---|
| **Conductor** | Sonnet (cockpit) | Runs the §2 lifecycle; spawns all agents; owns the wave gate | Accepts ONLY verifier receipts. An implementer's "done" is a claim, never an acceptance. Merges nothing unverified |
| **Binder** | **Fable** | At wave open: resolves every BIND-AT-OPEN slot in the brief against live state (fresh MCP probes + prior close report); stamps brief `BOUND` | A wave with unbound slots does not spawn implementers |
| **Implementer** (per lane) | Sonnet | Builds in an isolated worktree; writes unit tests; final message = claim + self-test evidence | Never verifies own lane. Never touches paths outside its lane's `may_touch` |
| **Verifier** (per lane, fresh context) | **Opus** | Phase-1 verification (§3): independent diff review vs lane brief, runs the tests itself, runs the lane's assertion-script subset, runs the scope-warden check | Issues a RECEIPT (§3.2) or a REJECTION with diagnosis. Never edits code |
| **Gate runner** | Opus (D-1.5/D-3/D-4); **floor-model Sonnet for D-2's synthesis gate** | Phase-2 verification (§3): post-deploy, executes the wave's full MCP battery against the deployed connector | Reports the red list plainly. Cannot be overridden by the conductor |
| **Adjudicator** | Fable (doctrine) / Opus (engineering) | Answers questions that would otherwise need the native (§4) | Doctrine rulings recorded as DR-n with delegation provenance |
| **Anti-gaming verifier** (D-3/D-4 only) | Opus | Adversarially checks statistical gates: degenerate curves, base-rate artifacts, threshold gaming vs the negative controls | A statistical gate without an anti-gaming pass is not green |
| **Migration guard** | Opus | Reviews every SQL migration pre-apply: destructive ops, idempotency, numbering (SINGLE directory — `platform/migrations/`; the 434-in-supabase split is the known failure) | A migration without a guard receipt does not apply |

## §2 — Wave lifecycle (deterministic; run in order; no step skippable)

1. **OPEN** — conductor reads protocol + brief + prior close report. Binder resolves all
   BIND-AT-OPEN slots (fresh MCP probes; never trust cached/register state older than the last
   deploy — the estate has changed same-day before). Brief stamped `BOUND`. Rollback pin recorded:
   current deployed image SHA + build_id per chart.
2. **SPAWN** — one worktree + branch per lane (`wave/<wave>/<lane>`); implementers launched in
   parallel per the brief's lane map. Lanes with declared sequencing (e.g. A1→A2 inside one lane)
   run inside a single agent.
3. **IMPLEMENT ∥ VERIFY (per lane)** — implementer claims done → verifier runs Phase-1 (§3.1).
   REJECTION → back to implementer with diagnosis, max **3 attempts**, then the lane PARKS (§4.3)
   and the wave proceeds without it if the gate permits, else the wave reports blocked.
4. **INTEGRATE** — receipted lanes merge to the wave integration branch in the brief's declared
   merge order; conductor runs the full test suite + a Phase-1 assertion sweep on the integrated
   branch (catches cross-lane interference). Regression → the offending lane re-opens (counts
   toward its 3 attempts).
5. **DEPLOY** — integration branch → main → deploy. **Only one wave deploys at a time, ever**
   (parallel tracks 2/3 never touch the deployed estate). Migrations apply only with guard receipts.
6. **REBUILD** — both charts (482012f1 Abhisek, 1c826d5a Abhinandan) rebuilt via the orchestrator;
   build-health check (assets lit, FORENSIC 7/7, 0 orphan refs, row-count census sane).
7. **GATE** — gate runner executes the wave's full MCP battery against the deployed connector,
   plus the wave's final proof. Red list → conductor triages: lane re-open (→ step 3) or PARK +
   report. **The wave closes only on all-green** (parked items must be explicitly excluded by the
   brief's gate as non-blocking, else the wave stays open).
8. **CLOSE + CLEANUP** (verified like any lane) — worktrees/branches removed; brief stamped
   `COMPLETE` (or left `ACTIVE` with the red list — never falsely stamped); close report written
   (template §6); SESSION_LOG entry; register status updates; CURRENT_STATE pointer; rollback pin
   advanced. A wave without a close report did not close (the D-1 lesson).

## §3 — Two-phase verification (the fix for D-1's failure)

**Phase 1 — pre-merge, per lane (verifier agent):**
(a) diff review against the lane brief's deliverables; (b) verifier runs the test suite itself —
implementer-reported test results are not evidence; (c) runs the lane's subset of the wave's
**executable assertion harness** (see D-1.5a Lane A-0 — assertions are scripts hitting the MCP/
serving layer, never prose); (d) **scope-warden**: `git diff --stat` touches only the lane's
`may_touch` globs — any stray path is an automatic REJECTION regardless of code quality.

**Phase 2 — post-deploy, per wave (gate runner):** the full battery on the DEPLOYED connector
after rebuild. Phase 1 merges a lane; only Phase 2 closes a wave. Three of D-1's four failures
lived in the deploy/wiring layer that Phase-1-style checks can never see.

**§3.2 Receipt format (machine-checkable, attached to the merge):**
`{lane, verifier_model, diff_reviewed: sha, tests: {run, passed, failed}, assertions: {script, green: [...], red: [...]}, scope_warden: pass|fail, verdict: ACCEPT|REJECT, diagnosis?}`

## §4 — Adjudicator (the human-proxy)

**§4.1 Routing:** doctrine-class questions (valence semantics, classical rules, interpretation,
anything citing śāstra) → **Fable**, recorded as `DR-n (Fable by native delegation, <date>)` in the
DISAGREEMENT_REGISTER, queued for native ratification at campaign close. Engineering trade-offs
(schema shape, retry strategy, sequencing, library choice) → **Opus**, recorded in the wave close
report. When in doubt about which class → Fable.

**§4.2 Contract:** the asking lane provides the question + options + its recommendation; the
adjudicator answers with a ruling + one-paragraph rationale; the ruling binds for the campaign.

**§4.3 PARK classes — never auto-adjudicated, no exceptions:**
1. FROZEN orchestrator contract changes (CLAUDE.md §N.2 — "STOP and raise with the native").
2. Destructive/irreversible data operations outside the idempotent delete-then-insert pattern.
3. Anything inside a brief's `must_not_touch`.
4. A lane at 3 failed verification attempts.
PARK = lane branch preserved, diagnosis written to the close report's PARKED section, wave routes
around it. Parked items are the FIRST agenda item of the next native session.

## §5 — Model matrix + circuit breakers

**Models:** Sonnet = implementation, conductor. Opus = all verifiers, gate runners, migration guard,
adjudicator-engineering, hard debugging (an implementer stuck twice may be respawned as Opus — this
counts as escalation, not a new attempt-counter). Fable = binder, adjudicator-doctrine, and D-2's
brief-slot design work. **D-2 synthesis gate runs on Sonnet deliberately** (floor-model rule: if the
weakest production model reaches 6/6 from served surfaces, the instrument — not the model — is
doing the work).

**Circuit breakers:** per-lane: 3 verification attempts, then PARK. Per-wave: if >50% of lanes park,
the wave halts and reports (the brief was probably mis-bound — re-run the Binder). Deploy: any
build-health failure (step 6) → immediate rollback to the pinned image + report; no forward-fixing
on a corrupted estate. Time/budget ceilings per the brief's frontmatter. The one unbreakable rule:
**a red gate is reported red. A half-passed gate stamped complete is the exact failure this
protocol exists to prevent.**

## §6 — Close report template

`{wave, brief_version_bound, lanes: [{lane, verdict, receipt_ref}], parked: [{lane, diagnosis}],
gate: {assertions_green, assertions_red, final_proof}, deploy: {image_sha, build_ids}, adjudications:
[DR-n / eng], register_updates, rollback_pin, next_wave_bind_notes}` — written to this directory as
`CLOSE_<wave>.md`, appended to SESSION_LOG.

---
*Changelog: v1.0 (2026-07-15) — initial protocol per native directives (autonomous, swarm-verified,
Sonnet-primary with pre-approved escalation).*
