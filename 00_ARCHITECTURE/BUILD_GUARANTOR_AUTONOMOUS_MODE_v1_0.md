---
artifact: BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md
canonical_id: BUILD_GUARANTOR_AUTONOMOUS_MODE
version: 1.0
status: CURRENT (operating mode — native-authorized full autonomy, 2026-06-03)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-03
authored_for: native (Abhisek Mohanty) — the architect
amends: BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md §J (standing constraints) + §D (gate model)
decision: >
  Native directive 2026-06-03: the build runs FULLY AUTONOMOUSLY with NO human in the loop. The
  swarm self-decides every gate (code / deploy / runtime, including production and destructive
  operations). The architect supplies the plan; the system builds, deploys, runs, tests, and
  fixes everything. Human approval is removed. Safety is AUTOMATED (reversibility + verify-before-
  promote + bounded retries + budget ceilings), not human.
---

# Build-Guarantor Swarm — Autonomous Mode v1.0

## §A — Mandate (what changes)

The swarm runs **unattended**. The architect provides the plan (Contract Registry + session queue);
the system does everything else — author, build, review, deploy (incl. production), run, verify, and
**fix-until-green** — with **no human approval at any gate**. This replaces the charter's human-gated
model (§J) with autonomous self-decision plus automated safety rails (§C). The architect's role is
reduced to: author the plan, and (optionally) watch the live feed (§G). Nothing waits on a human.

## §B — The gate-decision rule (the swarm decides)

At every gate (Gate 1 Code · Gate 2 Deploy · Gate 3 Runtime), the swarm evaluates the unit's
machine-checkable **acceptance test** and decides by itself:

- **PASS → advance.** Mark the asset green; the Conductor releases the next dependency-satisfied asset.
- **FAIL → bounded auto-fix loop.** Spawn a fix agent (Racayitā delta-brief → Śilpī patch → re-review →
  re-gate). Repeat up to `MAX_FIX_ATTEMPTS` (default **5**). Each attempt must be a *distinct* fix
  (no identical retry); the loop records what it changed.
- **STILL FAIL after the cap → PARK, don't loop.** Mark the asset `parked`, record the failure +
  every attempted fix, and **continue with other independent assets**. Parked assets are retried in a
  later pass and surfaced in the run report. This is what makes "fix until resolved" safe — it never
  burns unbounded spend on an unfixable unit.

No human approval is requested at any point. Production deploys and destructive operations are decided
by the same rule, under the §C rails.

## §C — Automated safety rails (no human — the system self-protects)

These are **not** tripwires (they page no one); they are how an unattended system runs irreversible
operations and self-heals. They are mandatory by default.

1. **Reversibility-by-construction.** Before any irreversible/destructive action (schema drop, data
   wipe, resource delete, secret rotation, prod migration), the executor takes an **automated
   snapshot/backup** first (DB export, resource config snapshot, git tag). If the action's post-step
   verification fails, it **auto-rolls-back** from that snapshot. A wrong autonomous decision self-heals.
2. **Verify-before-promote (canary path).** Build → deploy to a **non-prod / revision-pinned canary** →
   run the asset's acceptance test there → **auto-promote to 100% prod only if green**; auto-rollback
   the revision on red. Prod never receives unverified output.
3. **Bounded retries (§B).** `MAX_FIX_ATTEMPTS=5` → park. No infinite loops.
4. **Budget + time ceilings (set 2026-06-03 — generous, completion-first).** On breach: halt that unit,
   continue others, log it. Self-limiting; no runaway cost.
   - `MAX_RUN_BUDGET` = **$5,000** — the whole-instrument backstop. This is a *catastrophic-runaway ceiling,
     not the expected spend*: with Gemini (primary) + DeepSeek (fallback) — no Anthropic — the realistic full
     L0→L5 build is far lower (order $1–2k). $5k is deliberate headroom so the build never halts on budget.
   - `MAX_SPEND_PER_ASSET` = **$300** — the real runaway-catcher. A single stuck auto-fix loop halts at $300
     and parks the asset, so no one bug can silently drain the run total. **Exception:** the rule-extraction
     asset (`brahmagyan.rules`, 0.6) processes the whole classical canon — its sub-cap is **$1,000**.
   - `MAX_WALLCLOCK_PER_ASSET` = **6 hours** → park (time seatbelt against a hung step).
   - Spend is reported live (the budget ledger, §G); if a *legitimate* asset approaches its cap, the figure
     is raised explicitly rather than the asset being wrongly parked. All four numbers are tunable.
5. **Idempotency + determinism.** Every step is safely re-runnable; deterministic assets rebuild
   identically (hash-checked), so a re-run can't corrupt a green asset.
6. **Provenance + audit.** Every autonomous decision (pass/fail/fix/deploy/rollback) is logged with its
   evidence to Smṛti, so the full unattended run is auditable after the fact.

*(Tunable: the architect may widen or strip any rail. Stripping rail 1 or 2 means an autonomous wrong
decision on prod has no automatic recovery — kept ON by default for exactly that reason.)*

## §D — Self-chaining driver (unattended across batches)

The context budget (~20 sub-agents per orchestrator chat) is the only thing that previously required a
human re-kick. Autonomous mode removes it with a **driver**:

- A **scheduled re-kick** (Cloud Run Job / scheduled task, e.g. every N minutes) starts a fresh
  Conductor batch that **resumes from Smṛti** (the disk-of-record build state) and continues the queue.
- **Praharī (watchdog)** detects a stalled/timed-out batch and triggers an immediate re-kick.
- The run ends autonomously when the queue is drained (all assets green or parked) — then it emits the
  final report and stops re-kicking.

This converts "you babysit a chat" into "it runs to completion on its own."

## §E — Credentials & security (the real enabler)

Full autonomy means the swarm acts on prod without a human, so it needs scoped authority — and that
authority must be **least-privilege and project-isolated**:

- A dedicated **bot identity** (CI service account / GitHub app) with exactly: merge-to-main (under
  branch protection that admits the bot), Cloud Run deploy, Cloud SQL ops, Secret Manager access,
  scoped to the **Brahma project only**.
- Branch protection: the bot may merge **only** when CI is green (the gates ARE the approval now).
- Secrets: the bot reads what the build needs; rotation is one of the §C-rail-1 backed operations.
- Blast-radius isolation: the bot cannot touch non-Brahma projects; budget caps bound cost.

This is the one genuinely new security surface — an agent with unsupervised prod rights. The rails (§C)
+ least-privilege + project isolation are what make that acceptable.

## §F — Charter amendment (records the policy change)

`BUILD_GUARANTOR_SWARM_CHARTER §J` is amended for Brahma: **"PR-to-main / prod deploy / prod DB ops /
secret rotation / flag flips are human-gated"** → **"fully autonomous; the swarm self-decides all gates
including production and destructive operations; safety is automated per AUTONOMOUS_MODE §C, not human."**
Authorized by the native (architect) 2026-06-03. The other §J constraints (no Anthropic in prod; only
computed facts; verification = internal consistency) remain in force.

## §G — The architect's window (watch, don't gate)

Even with zero gates, the system stays observable so you can *choose* to look (never required):

- a **live build feed** (the Layer-Tower view over the swarm's progress);
- **per-layer completion reports** (assets green/parked, fixes applied, spend, rollbacks);
- a **parked-asset log** + a **budget ledger** + the **decision audit** (Smṛti).

You can intervene at any time, but the run never blocks waiting for you.

## §H — Rollout

Per the native's directive, autonomous mode is enabled **across all layers from the start**. (Lower-risk
option, available if ever wanted: prove it on L0/Brahmagyan first, then widen — not taken here.)

## §I — Failure semantics (what "autonomous" does at each failure)

- asset gate fails → bounded auto-fix → park + continue (never blocks the run).
- destructive-op verification fails → auto-rollback from the §C-1 snapshot → mark parked.
- canary verification fails → auto-rollback the revision; prod untouched.
- budget/time breach → self-limit the unit, continue others.
- batch stalls → Praharī re-kick.
- queue drained → final report, stop.

---

*End of BUILD_GUARANTOR_AUTONOMOUS_MODE v1.0 — native-authorized full autonomy, 2026-06-03. The swarm
builds/deploys/runs/tests/fixes with no human in the loop; safety is automated (reversibility +
verify-before-promote + bounded retries + budget ceilings). Amends the charter §J. Implemented in
Antigravity (driver + bot identity + the §J flip); the architect supplies the plan and the system does
the rest.*
