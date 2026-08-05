# Claude Code task B — demote the 392,001 writer-emitted unearned rows (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated. **State the `origin/main` SHA.** Standing
rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`.

**GATE — do not start until both hold, and verify both yourself:**
1. Task A's backfills have run (`PASS`/`pass`/`single_pass` = 0; chart_dashas verified==examined).
2. **Abhisek has given an explicit go on the user-visible grade change.** This demotion re-grades
   ~91 fact_categories `ganita_fact` → a lower grade and changes the warranty sentence for real
   reads. It is his product call. If you are running without that recorded go, STOP and ask.

If either is unmet, deliver Part 1 (analysis) only and hold.

## What this is

The 392,001 rows in `chart_facts` (352,485) + `chart_divisionals` (39,516) carry
`two_pass_verified` from four writers — `ga_structural`, `ga_vargas`, `ga_sensitive`,
`ga_sade_sati` — whose `_verify_*` functions are row-set hygiene, never engine-vs-derived
(established: a=0, b=102, c=2). These are the last rows failing the invariant's claim-vs-evidence
check. This is the writer-side twin of the dasha broadcast fix (#1029).

## Part 1 — Re-confirm the classification (do regardless of the gate)

Re-read the emit sites; do not inherit the 104/(a=0,b=102,c=2) split — re-derive it. For each site:
- **(b) no comparison** → demote to `single`.
- **(c) known approximation** (e.g. `ga_structural_writer.py:3349` baladi proxy, `:3582`
  lagna-sign-conditional) → `documented_approximation`, **but** verify that value is CHECK-legal on
  the target table first (it is NOT in the `chart_divisionals`/`chart_dashas` 4-value set — for
  those tables the honest legal tier is `single`; say so and use it).
- **(a) genuine comparison** → unchanged. Report if you find any (the prior pass found none).
Quote the site for every (c) and every (a).

## Part 2 — Fix the writers (code), then backfill (data) — atomic, ordered

1. **Writers:** the four writers emit the honest tier via `brahmagyan/verification_vocab.py`
   constants, never a literal. A row the verifier did not examine must not receive
   `two_pass_verified`. No new vocab member; no CHECK migration.
2. **Backfill:** extend the Task-A backfill pattern (or a sibling script) — `DATABASE_URL` from env,
   dry-run default, idempotent, **test against one chart**, hand the production run to Abhisek. Do
   not run it.
3. **Every row-tier change listed in the PR body**, per category: old→new, count, and the
   (b)/(c) rationale. These are data-honesty changes; none silent.
4. **Emissions byte-identical except the deliberate tier changes.** Verify with the writers' tests
   and the double-build determinism standard these writers carry.

## Part 3 — Prove it closed

- After the backfill (Abhisek's run), dispatch invariant `325445415`; claim-vs-evidence must now
  PASS for `chart_facts` and `chart_divisionals`. Read at check level (rule 1).
- Served delta for one affected chart: `grounding_score`/grade/warranty before vs after. This is
  the change Abhisek approved; show it as text.
- **Recommend the `chart_facts` CHECK now** (after the backfill it will pass; before it it would
  fail on the very rows this fixes) — the absence of that CHECK is why `PASS` survived two campaigns.
  Recommend, don't apply, unless Abhisek approves in-task.

## Guardrails
No production writes by you. No new vocab member. Byte-identical emissions except listed tier
changes. Branch per phase; queue merges.

## Deliverable
Prose. The re-derived (a/b/c) split with quoted sites; the writer diff; the tested one-chart
before/after; the served delta; the invariant check-level result after the backfill. End plainly:
**does every `verified=True` row in `chart_facts` and `chart_divisionals` now trace to a real
examination — yes or no — and is the standing invariant now fully green except for rows the real
Vimshottari second pass (Task C) will re-earn.**
