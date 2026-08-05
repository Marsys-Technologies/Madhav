# M-22 OVERNIGHT — SWARM EDITION: autonomous, isolated, reviewed at every gate (Madhav)

Fully autonomous overnight run; one report in the morning. Repo `Marsys-Technologies/Madhav`.
Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6` (nine). The three that govern the night:
count what the verifier READ; a check must be able to fail on a PLAUSIBLE wrong value; assertions
outrun evidence in whatever direction the asserter leans — **including each agent's own**.

A halted stage with a clean diagnosis is a SUCCESS. Forcing a stage past a failing gate is the only
outcome worse than stopping.

## Known environment (verified 2026-08-02, not assumption)
- **A parallel campaign — ṢAḌ-DARŚANA — runs nights in this repo.** It merges to `main` repeatedly
  (Night-4 closed 05:00–08:34Z) AND **builds database rows overnight** (`bg_*` writers, e.g.
  f97fc78d). Expect `main` to move and DB counts to drift while you run.
- **DB verified GO on the data side (2026-08-02, read-only):** connection reaches prod `amjis`
  (`madhav-astrology:asia-south1:amjis-postgres`, PG 15.17). Estate totals had already GROWN since
  the census (chart_facts 415,166 · chart_dashas 1,461,165 · chart_divisionals 70,626; ~1.95M total)
  while the STATUS-SPECIFIC counts held exactly (`PASS` 5,428 · `single_pass` 32,614 · chart_dashas
  `two_pass_verified` 1,358,993). **This is the parallel session adding rows — it is exactly why you
  RE-DERIVE every count at runtime and never inherit a number from this brief, including these.**
  Neither backfill has run (both residues intact).
- **The tested dasha chart is `482012f1-710e-4a25-994a-93821f5871aa`** (also the native/canonical
  chart — the one whose vimshottari Pass 2 genuinely ran). Stage 1's first scoped dasha backfill runs
  against THIS id; Stage 3's `CANONICAL_CHART_ID` gate refers to this same id. Do not substitute a
  different "canonical" chart.
- `DATABASE_URL` must be exported in the launch shell (value from Secret Manager
  `amjis-pipeline-db-url`; do not read/print it). Absent → dry-run all, write nothing, HALT Stage 1.
- **Every merge to `main` auto-deploys to Cloud Run.** Minimize merges: ONE PR per stage. The
  "Build & Deploy MCP" smoke failure is pre-existing and NOT yours to fix.
- `DATABASE_URL` must already be in the run environment. Never print/log/echo/interpolate its value.
  Absent → dry-run everything, write nothing, HALT Stage 1 with a clean report.
- TAP-6 arming: not before 2026-08-08, `two_pass_verified_literal` job-level — NOT tonight.
  `SC-pointer:query_muhurta_lattice` red is not yours. Secrets are owner-only, names never values.

## PHASE -1 — Isolation & reconnaissance (before anything else)
1. **Dedicated worktree**: `git fetch origin && git worktree add <path>/m22-night origin/main`
   (fresh, detached from the shared checkout — which sits on `parishodhana/dark-corpus-remeasure`
   and belongs to another campaign; NEVER read or touch it, and never touch any
   `shad-darshana/*` branch or file another campaign owns). All work happens in this worktree;
   branch per stage from current `origin/main`; delete the worktree at the end.
2. Record the starting `origin/main` SHA. **At the start of every stage, re-fetch and re-verify that
   stage's preconditions against CURRENT main** (scripts present, invariant workflow `325445415`
   registered, wording fix present) — plan-time facts expire overnight here.
3. Create **`M22_NIGHT_LEDGER.md`** in the worktree. Append-only; one entry after every gate,
   write, review verdict, and escalation: timestamp, actor agent, evidence hash/counts, verdict.
   All production writes are idempotent scripts, so a crash at any point leaves prod clean and the
   ledger is sufficient to resume. On restart: read the ledger, resume after its last entry.

## SWARM ARCHITECTURE
A lean **Conductor** orchestrates and NEVER executes or reviews. Roles (spawn via your agent/Task
mechanism; where a model is selectable, gate-reviewers and the skeptic use the highest-capability
(Opus-class) model available):
- **Executor(s)** — do the stage's work. May fan out (Stage 2: the four writers audited in
  parallel, one agent each; site classification is parallelizable).
- **Independent Verifier(s)** — re-derive, read-only, every count/claim an Executor produces.
  **Never the same agent as the Executor. No agent validates its own output — ever.** A number
  reaches a gate only when Executor and Verifier agree within stated tolerance; disagreement →
  Gate Reviewer.
- **Gate Reviewer (Opus)** — MANDATORY at every former human gate (listed below), not only on
  anomaly — this campaign's errors all looked fine. Receives the full evidence package
  (Executor's work, Verifier's independent numbers, dry-run output, served-delta text), reviews
  adversarially, and rules **PROCEED / FIX (with proof the fix reaches the code under test) /
  HALT**. Hard limits no reviewer may override: no new vocab member; no CHECK migration applied;
  no touching genuinely-earned rows (mudda 780, narayana 345, native vimshottari 64, ga_nakshatra
  computed); no secret/`DATABASE_URL` value handling; no arming TAP-6; no fixing SC-pointer; no
  writes outside the sanctioned scripts. A fix requiring any of these = HALT.
- **Skeptic (Opus, Stage 3 only)** — adversarial mandate to REFUTE: attack the new verifier's
  independence, its tolerance choice, and its probes.
- **Scribe** — maintains the ledger and drafts §6 subsections as stages land.
Retry cap: two attempts at any failing check, then Gate Reviewer. Stage timebox: if a stage exceeds
its budget or loops, HALT it cleanly and proceed only to stages independent of it (3 needs 1+2;
2 needs 1).

## UNIVERSAL WRITE-GATE (every production write, no exceptions)
1. Executor dry-runs the exact operation; captures planned counts per table/tier.
2. Independent Verifier re-derives expected counts, read-only, from scratch.
3. Compare all three (dry-run, Executor's prediction, Verifier's) — agree → step 4; diverge → Gate
   Reviewer.
4. **TOCTOU re-check** (ṢAḌ-DARŚANA writes overnight): immediately before `--execute`, Verifier
   re-reads the TARGET-TIER counts. Benign drift (other tiers/tables moved) → note and proceed —
   the WHERE clauses are tier-scoped and idempotent. Target-tier drift → re-predict ONCE; drifts
   again → HALT the write (someone else is writing your tiers) → Gate Reviewer.
5. Execute. 6. Dispatch invariant `325445415`; read **at check level** (job `conclusion` lies for
   continue-on-error); written tables must move in the predicted direction, else the write is
   suspect: stop the stage, preserve state, Gate Reviewer.

---

## STAGE 1 — Backfills  *(former human gates 1: pre-authorized, machine-gated)*
Executor pre-flights both scripts on current main (`drain_prohibited_verification_status.py`,
`backfill_unexamined_dasha_tiers.py`): env-not-arg; dry-run default (name the execute flag);
idempotent WHERE clauses; tier targets per the ruling (drain `PASS`/`pass`/`single_pass`→`single`;
dasha unexamined→`single`, membership→`classical_match`; earned rows untouched); all targets
CHECK-legal on every written table. Verifier independently re-derives all counts.
**GATE R1 (Opus review)** → then write-gate: drain; `--chart 482012f1-710e-4a25-994a-93821f5871aa`
(the tested chart); then unscoped.
Confirm: prohibited/deprecated → 0; `chart_dashas` verified == examined.

## STAGE 2 — Demote the 392,001 writer rows  *(former gates 2+3)*
Parallel Executors re-derive (never inherit) the a/b/c split across `ga_structural`/`ga_vargas`/
`ga_sensitive`/`ga_sade_sati`: (b) no comparison→`single`; (c) approximation→
`documented_approximation` ONLY where CHECK-legal, else `single` (NOT legal on
`chart_divisionals`); (a) genuine→unchanged, report any found. Fix the writers to emit honest tiers
via `verification_vocab.py` constants; emissions byte-identical except deliberate tier changes
(writers' tests + double-build determinism). Measure the served delta (grounding_score / grade /
warranty for one chart, as text) — it must be purely MORE honest; anything less accurate → HALT.
**GATE R2 (Opus review — includes the product change: ~91 categories re-grade; pre-authorized, but
the reviewer confirms the delta is exactly the authorized one and nothing else)** → write-gate the
backfill. Recommend (do NOT apply) the `chart_facts` CHECK post-backfill.

## STAGE 3 — The real Vimshottari second pass  *(former gate 4; the riskiest — extra rigor)*
Executor builds the independent verifier: re-derive from the Moon's sidereal longitude **without
calling `compute_vimshottari`**; per row, levels 1–4; compare **lord AND both boundaries** with a
stated, justified JD-rounding tolerance; no `CANONICAL_CHART_ID` gate — each chart's own starting
lord derived; verdicts via `two_pass_verdict(...)`.
Prove discrimination: wrong-lord fires; boundary beyond tolerance fires; within tolerance does NOT;
every probe shown to reach the code (rule 4).
**Skeptic pass:** attack independence (any shared helper with the producer?), tolerance (too loose
to bite? too tight = false divergence?), and probes. Skeptic must either fail to refute — with
specifics — or HALT.
**Sample cross-check:** a DIFFERENT agent recomputes ≥1,000 random rows (spread across charts and
levels) and compares verdicts. Any mismatch between verifier and sample → HALT to Gate Reviewer.
Full run: agreements → re-promote to `two_pass_verified` through the write-gate; disagreements →
`divergent_flagged`, reported as REAL ENGINE DEFECTS in the report, never silently corrected. If
disagreements are exactly 0 across ~1.36M: suspicious by default — the swarm must argue which of
{engine-that-good / comparison-not-biting} with evidence, and the Skeptic must concur, else HALT
the re-promotion (leaving rows honestly at `single` is safe; wrongly re-promoting is not).
Wire the verifier into the build so future rows are earned at write time.

---

## Coexistence etiquette (all night)
Rebase each stage branch onto fresh `origin/main` immediately before opening its PR; re-arm
auto-merge after any queue ejection (a consumed arm reads as "off"); never modify another
campaign's branches, briefs, or ledgers; if `main` moves under an open PR, update once — twice →
note contention in the ledger and keep going (the queue serializes; do not fight it).

## MORNING REPORT (one document)
Starting/ending `main` SHAs · per stage: evidence, every write-gate's predicted-vs-dry-run-vs-actual,
invariant check-level results, served deltas as text · **SWARM LOG** (which agent executed, which
verified, every Gate Reviewer verdict with reasoning, Skeptic findings) · **PARALLEL-SESSION LOG**
(every observed ṢAḌ-DARŚANA merge/drift and how it was handled) · **HALT LOG** — every stop, why,
the clean state left, and the smallest human action to unblock; this is the most valuable section.
Then three answers: (1) all prohibited/deprecated values gone and every `verified=True` row traces
to a real examination — yes/no + exceptions; (2) how many rows honestly re-earned
`two_pass_verified`, and did the second pass expose real engine disagreements; (3) is the standing
invariant fully green on live `main` — if not, exactly what remains.
Final line: **is anything in production half-applied or unverified (it must not be — confirm), and
was the worktree removed.**
