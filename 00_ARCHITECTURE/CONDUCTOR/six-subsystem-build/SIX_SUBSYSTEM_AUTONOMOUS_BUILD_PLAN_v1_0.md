---
artifact: SIX_SUBSYSTEM_AUTONOMOUS_BUILD_PLAN_v1_0.md
canonical_id: SIX_SUBSYSTEM_AUTONOMOUS_BUILD_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: the Sūtradhāra conductor (Claude Code in Antigravity) — FULLY AUTONOMOUS, no human gates
purpose: >
  Fully autonomous, conductor-driven, sub-agent-implemented build of the SIX subsystems (Yoga, Dignity,
  Transit, Medical, Astrovastu, Prashna) — Nakshatra is already building separately. Objective: implementation
  VELOCITY via maximal safe parallelism. No human gates until completion; native reviews ONCE at the end.
governing_inputs:
  - the 6 master plans (YOGA_/DIGNITY_AVASTHA_/TRANSIT_GOCHARA_/MEDICAL_AYURVEDIC_/ASTROVASTU_/PRASHNA_SUBSYSTEM_MASTER_PLAN_v1_0.md)
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§0 the 3-category split; §0.5 enrichment+hard-gate; §8 strategy)
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the 12-role Gate-0→3 swarm)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md (the FROZEN contract every writer conforms to + §5 checklist)
  - AUTONOMY_RESILIENCE_PATTERN_v1_0.md (AUTONOMOUS_MODE rails)
  - feedback-subsystem-embedding-pattern (the 8-step method)
mode: AUTONOMOUS_MODE — no synchronous human gates; agent gate-validators do the human role; halt-and-log only on hard failure.
---

# Six-Subsystem Autonomous Build — Conductor Plan v1.0

## §0 — Objective + the autonomy contract

Build all SIX subsystems to their maximal master-plan depth, fully autonomously, maximizing velocity. The
Sūtradhāra conductor walks the dependency DAG, spawns Śilpī builder sub-agents in isolated worktrees along
independent branches IN PARALLEL, runs the Gate-0→3 swarm per asset, advances, and loops — NO human gates.
The native reviews ONCE at the very end. Halt-and-log ONLY on a hard failure that survives the resilience
pattern's fix attempts.

**Governing rules (inherited, enforced by the swarm, not by a human):**
- Each writer is orchestrator-native (`@register('<id>')` WriterBase, FROZEN contract — ctx.db_conn, never
  commit, sub-steps if heavy). NO orchestrator change (if one seems needed → HALT, native decision).
- The §0.5 maximal-enrichment + the **computed-and-cited HARD GATE** (a datum stored only if deterministically
  computed + classically cited; interpretive content = serve-time). Pramāṇa enforces; an uncited value FAILS
  the gate (floor null+marked, never fabricate).
- The 3-data-category split: static→L0 (ON-CONFLICT), per-chart→L1 (delete-then-insert), time-varying→L0
  SERVICE (compute on demand, nothing stored across time — Transit's bg_transit_engine).
- Validate-as-you-go: each SUBSYSTEM proven (writers build, FORENSIC-gated, cockpit-lit, idempotent) as its
  assets land; LAYERS stay DRAFT/open; sealed ONCE at the very end (separate native-reviewed close).
- Epistemic tiering: Medical = indications-not-diagnosis + disclaimer; Astrovastu remedies = remedial-tradition
  tier; Prashna = own namespace. Pramāṇa verifies tiers are marked.

## §1 — The dependency DAG (decides parallelism = velocity)

```
                       ┌─ YOGA ───────────┐
   (independent) ──────┤                  ├─→ MEDICAL ──┐
                       └─ DIGNITY ─────────┤             ├─→ (subsystem validation)
                                   │       └─ ASTROVASTU ┘
                                   └─→ TRANSIT ──────────────→ PRASHNA
```
- **YOGA** and **DIGNITY** are INDEPENDENT of each other (both pure leverage over existing L1 data) → build
  FULLY IN PARALLEL, two worktrees, from the start.
- **TRANSIT** depends on Dignity (transit-planet condition) → starts when Dignity's L0+L1 land (can overlap
  Yoga).
- **MEDICAL** depends on Dignity + Yoga (+ Nakshatra, already building) → starts when those land.
- **ASTROVASTU** depends on Dignity (weak-planet join) → small; starts when Dignity lands; can run parallel
  to Medical.
- **PRASHNA** depends on ALL (it reuses every subsystem on the prashna chart) → LAST, but its L0
  `bg_prashna_rules` (static horary rules) is independent and can be authored/built EARLY in parallel; only
  ga_prashna (which reuses everything) waits.

**Velocity strategy:** open Yoga + Dignity + Prashna-L0-rules in parallel immediately (3 worktrees). As
Dignity completes, fan out Transit + Astrovastu. As Yoga+Dignity complete, Medical. Prashna's ga_ asset last.
Peak parallelism ~4-5 concurrent worktrees.

## §2 — Worktree structure (isolation = parallel safety)

Per the Śilpī pattern (charter §E.4): one worktree per subsystem, each on its own branch off main, so
builders never collide. (Branch-isolation-per-stream — [[feedback-two-stream-branch-policy]].)
```
/Users/Dev/Vibe-Coding/Apps/MadhavYoga       feature/subsystem-yoga
/Users/Dev/Vibe-Coding/Apps/MadhavDignity    feature/subsystem-dignity
/Users/Dev/Vibe-Coding/Apps/MadhavTransit    feature/subsystem-transit
/Users/Dev/Vibe-Coding/Apps/MadhavMedical    feature/subsystem-medical
/Users/Dev/Vibe-Coding/Apps/MadhavAstrovastu feature/subsystem-astrovastu
/Users/Dev/Vibe-Coding/Apps/MadhavPrashna    feature/subsystem-prashna
```
Each subsystem's assets share its worktree (its L0 ref + L1 writer + L2 extensions build together). A
subsystem's PR merges to main when its assets pass Gate 0-3; downstream subsystems rebase on main to pick up
their dependency (e.g. Transit rebases after Dignity merges, to get ga_condition).

**Cross-subsystem dependency handling:** a downstream worktree's writer references an upstream asset
(Medical→ga_condition). The conductor gates the downstream START on the upstream's MERGE-to-main (not just
build) so the dependency is real, not worktree-local ([[feedback-ac-must-verify-target-environment]] — the
seal-vs-prod lesson: depend on merged+built, never worktree-only).

## §3 — The per-subsystem build loop (Gate 0 → 3, autonomous)

For each subsystem, the conductor runs the charter's gate sequence, all by sub-agents:

**GATE 0 — Assess & Author (Nirīkṣaka + Racayitā):**
- Nirīkṣaka audits current state (what exists vs the master plan — esp. what to REUSE not rebuild:
  ga_condition, nakshatra body-parts, aspect_tajik, etc.).
- **Racayitā AUTHORS the per-asset execution briefs FROM the master plan** (this is the key autonomy move —
  briefs are generated by the agent from the maximal master plan + the §0.5 standard, not hand-written by
  Cowork). Each brief: the asset's full scope, the computed-and-cited gate, the conformance checklist
  (ORCHESTRATOR_CONVERGENCE_CLOSE §5), FORENSIC assertions, idempotency, reuse-don't-recompute references.

**GATE 1 — Code (Śilpī builders, parallel):**
- Śilpī sub-agents build each asset in the worktree per its Racayitā brief: the L0 reference writer
  (deterministic cited tables), the L1 per-chart writer (PyJHora, orchestrator-native @register), the
  migrations, the seed/registry entries, the unit tests. Heavy assets use sub-steps.
- Sourcing (the texts for the hard gate) — Racayitā/Śilpī check bg_texts first, source-gap into bg_texts via
  l0_texts ingestion, cite every datum.

**GATE 2 — Deploy:**
- The subsystem's PR → CI green → merge-verify → deploy (the deploy machinery is proven; the orchestrator job
  image includes the writers). Migrations applied surgically (never deploy.yml-auto / bulk migrate.ts —
  [[feedback-deploy-migrations-silent-noop]], [[feedback-migrate-runner-untracked-legacy]]).

**GATE 3 — Runtime (Pramāṇa + Sambandha + FORENSIC):**
- Build the subsystem's assets for the native (482012f1) VIA THE ORCHESTRATOR (`POST /api/cockpit/runs`),
  NOT hand-run. Pramāṇa verifies: computed-and-cited gate (zero uncited stored values), two-pass, atomic
  grain, epistemic tiers marked. FORENSIC where applicable. Sambandha verifies cross-subsystem refs resolve
  (ga_medical→ga_condition fact_ids resolve). Cockpit tile lit + bar fills. Idempotency double-run.
- ONLY when Gate 3 passes is the subsystem "validated" (the validate-as-you-go guardrail). Layer stays DRAFT.

## §4 — The conductor queue (session_queue.yaml — the DAG as entries)

`00_ARCHITECTURE/CONDUCTOR/six-subsystem-build/session_queue.yaml`: one entry per subsystem, with
`depends_on` (the §1 DAG), `worktree`, `branch`, `master_plan`, and the Gate-0→3 acceptance. The conductor
walks it like the L1 queue (the proven template), but with PARALLEL dispatch (multiple worktrees in flight)
governed by `depends_on` + `parallel: true`. AUTONOMOUS_MODE: no `requires_human_approval` on any entry.

## §5 — AUTONOMOUS_MODE rails + resilience (no human gates)

- **MAX_FIX_ATTEMPTS** per the resilience pattern (AUTONOMY_RESILIENCE_PATTERN): a failing gate triggers
  automated fix-retry up to the cap before HALT. Context-decay protection: per-batch Smṛti re-kick.
- **Halt-and-log ONLY on:** a frozen-contract change appearing necessary (native decision), a FORENSIC miss
  that survives fixes, a computed-and-cited gate failure that can't be sourced (the datum gets floored, not
  faked — only a STRUCTURAL block halts), a cross-subsystem dependency that can't resolve, or context budget.
- **Smṛti** logs every subsystem's pass to `six-subsystem-build/smriti/<subsystem>-pass.md`.
- **Praharī watchdog** ensures no worktree hangs; reaper-safe (heavy writers heartbeat per the frozen
  contract's sub-step model).
- Native reviews ONCE at the end (the §6 close), not synchronously.

## §6 — Completion + the single end-review

When all 6 subsystems pass Gate 3 (validated, merged, cockpit-lit), the conductor:
- Runs an IS.8(b) red-team across the 6 (Vimarśaka) — full-instrument adversarial pass.
- Emits a `SIX_SUBSYSTEM_BUILD_CLOSE.md` with per-subsystem evidence (assets, row counts, gate results,
  hard-gate compliance, tier markings).
- **Does NOT seal the layers** (L0/L1 seal once at the very end of the whole program, after Nakshatra + these
  6, per the strategy) — it reports each subsystem validated + the layers' readiness.
- Presents to the native for the SINGLE end-review.

## §7 — Velocity summary
- Parallel from the start: Yoga ∥ Dignity ∥ Prashna-L0. Fan-out: +Transit +Astrovastu (post-Dignity), +Medical
  (post-Yoga+Dignity). Prashna-ga last. ~4-5 concurrent worktrees at peak.
- Racayitā auto-authors briefs from the master plans (no Cowork hand-authoring per asset) — the autonomy
  accelerator.
- Each subsystem self-validates at Gate 3; no synchronous human gates; one end-review.

## §8 — Rails (the non-negotiables the swarm enforces)
Orchestrator-native + frozen contract (HALT if a change seems needed); computed-and-cited hard gate (uncited
→ floor, never fake); 3-category split (service for transit, nothing stored across time); reuse-don't-recompute
(Sambandha verifies); surgical migrations only; only 482012f1; merge-verify before any "done"; branch-isolation
per worktree; build via orchestrator not hand-run; FORENSIC-gated; epistemic tiers marked; validate-as-you-go,
seal-layers-once-at-end. Native review ONCE, at completion.

---

*End. Six subsystems, fully autonomous, conductor-driven, sub-agent-built, maximal-parallel across isolated
worktrees, Racayitá-authored briefs, Gate-0→3 swarm, AUTONOMOUS_MODE, validate-as-you-go. Velocity via the
Yoga∥Dignity∥Prashna-L0 parallel start + dependency-gated fan-out. One native review at the very end.*
