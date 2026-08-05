# Claude Code task A — verify the two backfills before Abhisek runs them, confirm after (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated. **State the `origin/main` SHA you read from**
(local checkout is stale on `parishodhana/dark-corpus-remeasure` — never read it). Standing rules
`CI_EFFICIENCY_AUDIT_v1_0.md §6`.

This task does **not run** either backfill. Abhisek runs them (`DATABASE_URL` from his environment).
You verify they are safe *before*, and confirm the estate moved as intended *after*. Read-only
against production throughout.

## Part 1 — Pre-flight (do now)

Re-read both scripts on `main` and confirm each, quoting the lines:
`platform/scripts/backfill/drain_prohibited_verification_status.py` and
`backfill_unexamined_dasha_tiers.py`.

1. **Env, not argument:** `DATABASE_URL` is read from the environment; no credential is ever a CLI
   arg or logged. Confirm.
2. **Dry-run default:** running with no `--execute` (or equivalent) writes nothing and prints the
   plan. Confirm the exact flag.
3. **Idempotent:** running twice produces the same end state — a second run is a no-op, not a double
   application. Confirm by reading the WHERE clauses (they must select only rows still in the source
   tier).
4. **Tier targets match the ruling:** drain → `PASS`/`pass`/`single_pass` → `single`; dasha →
   unexamined/broadcast rows → `single`, membership-validated → `classical_match`. Genuinely-earned
   rows (mudda 780, narayana 345, native vimshottari 64, ga_nakshatra computed) are **not** touched.
   Confirm the scripts exclude them.
5. **CHECK-legal:** every target tier is permitted by the live CHECK on every table each script
   writes (`chart_dashas`/`chart_divisionals` allow only the 4-value set — `single` and
   `classical_match` are both in it). Confirm no write would raise a CheckViolation.
6. **Re-derive the row counts** the dry-run will report, independently, read-only. If your numbers
   disagree with the script's dry-run expectation, STOP and report — do not tell Abhisek to run a
   script whose own count you can't reproduce.

Deliver a one-line go/no-go per script with the evidence. If any check fails, that script does not
get run until fixed.

## Part 2 — Hand-off (state, don't do)

Give Abhisek the exact commands and order: drain first (label-only, zero claim change), then
`backfill_unexamined_dasha_tiers.py --chart <CANONICAL_CHART_ID>` (one chart), then unscoped. Tell
him what each dry-run should print so he can eyeball it before `--execute`.

## Part 3 — Post-run confirmation (after he says he's run them)

Read-only:
1. `PASS`/`pass`/`single_pass` counts → **zero**. `single_pass` fully canonicalised.
2. `chart_dashas` claim-vs-evidence: rows claiming `two_pass_verified` now == rows a verifier
   examined (≈844 earned + whatever the real second pass later re-earns), not 1.36M. Report the
   number.
3. **Dispatch the standing invariant** (workflow `325445415`) once and read it **at check level**:
   claim-vs-evidence and vocabulary conformance should now PASS for the drained/backfilled tables;
   any table still failing is the demotion's remaining scope (Task B), not a regression — name it.
4. One-page served delta: for one affected chart, `grounding_score` / grade / warranty sentence
   before vs after. Confirm the new wording reads honestly (no "candidate" for deterministic rows).

## Deliverable
Prose. Pre-flight go/no-go with quoted evidence and your independently re-derived counts; the exact
hand-off commands; and — after his run — the post-run confirmation with the invariant's check-level
result. End plainly: **is every prohibited/deprecated value gone and does chart_dashas' verified
count now equal its examined count — yes or no — and which tables (if any) still fail the invariant,
i.e. remain for Task B.**
