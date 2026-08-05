# Claude Code task — finish the M-22 tail, in sequence (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection). **State the `origin/main` SHA at the top of every report** — the local checkout is stale
on `parishodhana/dark-corpus-remeasure`; never read it. Standing rules
`CI_EFFICIENCY_AUDIT_v1_0.md §6` (nine). Governing ones here:
- Count what the verifier **read**, not what its verdict was attached to.
- A check earns `two_pass_verified` only if it could have failed on a **plausible wrong** value.
- Assertions outrun evidence in whatever direction the asserter leans — including yours.

This runs **three stages in order**. Each has a **HUMAN GATE** you cannot cross yourself. At a gate:
finish everything up to it, deliver the stage report, and **STOP** — do not proceed, do not simulate
the owner action, do not silently widen scope. You resume when Abhisek confirms. **No production
writes by you, ever. No secret or `DATABASE_URL` value handled by you, ever.** Read-only against
prod except a tested backfill whose production run is handed to Abhisek.

If any stage's verification contradicts this brief, STOP and report — a finding that halts the
sequence is a success.

---

## STAGE 1 — Backfills: verify → [GATE: Abhisek runs] → confirm

**1a. Pre-flight (do now).** Re-read both scripts on `main`, quoting lines:
`platform/scripts/backfill/drain_prohibited_verification_status.py` and
`backfill_unexamined_dasha_tiers.py`. Confirm each: (i) `DATABASE_URL` from env, never an arg or
log; (ii) dry-run is the default, name the `--execute` flag; (iii) idempotent — read the WHERE
clauses, a second run is a no-op; (iv) tier targets match the ruling — drain
`PASS`/`pass`/`single_pass`→`single`; dasha unexamined/broadcast→`single`, membership→
`classical_match`; genuinely-earned rows (mudda 780, narayana 345, native vimshottari 64,
ga_nakshatra computed) untouched; (v) every target tier is CHECK-legal on every table each script
writes; (vi) **independently re-derive** the counts the dry-run will report — if yours disagree,
STOP.

Deliver a one-line go/no-go per script with evidence, and the exact commands + order for Abhisek:
drain first, then `backfill_unexamined_dasha_tiers.py --chart <CANONICAL_CHART_ID>`, then unscoped —
with what each dry-run should print.

**→ HUMAN GATE 1:** Abhisek runs the two backfills. STOP here until he confirms.

**1c. Confirm (after his confirmation).** Read-only: `PASS`/`pass`/`single_pass` → zero;
`chart_dashas` verified count now == examined count (not 1.36M). Dispatch invariant `325445415`,
read **at check level** — claim-vs-evidence + vocabulary conformance now PASS for the
drained/backfilled tables; any table still failing is Stage 2 scope, name it. One-page served delta
(grounding_score/grade/warranty) for one chart; confirm the new wording is honest.

---

## STAGE 2 — Demote the 392,001 writer rows: analyse → [GATE: Abhisek's product go] → fix → [GATE: run] → close

Scope: 352,485 `chart_facts` + 39,516 `chart_divisionals` rows carrying `two_pass_verified` from
`ga_structural`/`ga_vargas`/`ga_sensitive`/`ga_sade_sati`, whose `_verify_*` are row-set hygiene,
never engine-vs-derived. These are the last rows failing claim-vs-evidence. Writer-side twin of the
#1029 broadcast fix.

**2a. Re-confirm the classification (do now, regardless of gate).** Re-read every emit site; do NOT
inherit the prior a=0/b=102/c=2 — re-derive it. (b) no comparison → `single`; (c) approximation →
`documented_approximation` **only where CHECK-legal** (it is NOT in the `chart_divisionals` 4-value
set → there the honest legal tier is `single`; say so, use it); (a) genuine comparison → unchanged,
report any found. Quote every (c) and (a).

**→ HUMAN GATE 2:** this re-grades ~91 fact_categories and changes the user-visible warranty
sentence — Abhisek's product call. Deliver 2a and the projected served delta; STOP until he gives an
explicit, recorded go.

**2b. Fix + backfill (after his go).** The four writers emit the honest tier via
`brahmagyan/verification_vocab.py` constants, never a literal — a row the verifier didn't examine
never gets `two_pass_verified`. No new vocab member, no CHECK migration. Emissions byte-identical
except the deliberate tier changes; verify against the writers' tests + double-build determinism.
Write the backfill (env `DATABASE_URL`, dry-run default, idempotent, one chart tested). Every
row-tier change listed in the PR body: category, old→new, count, (b)/(c) rationale.

**→ HUMAN GATE 3:** Abhisek runs the Stage-2 backfill. STOP until confirmed.

**2c. Close (after his confirmation).** Dispatch `325445415`; claim-vs-evidence must now PASS for
`chart_facts` + `chart_divisionals` (check level). Recommend — do not apply — the `chart_facts`
CHECK now (it passes post-backfill; its absence is why `PASS` survived two campaigns). Served delta
for one chart, shown as text.

---

## STAGE 3 — The real Vimshottari second pass: build → prove → [GATE: run] → re-earn

The constructive inverse: honestly re-earn the ~1.36M `chart_dashas` rows Stages 1–2 demoted to
`single`, by an independent re-derivation that actually agreed. **Earn, do not relabel.**

**3a. Build.** (i) Re-derive the sequence from the Moon's sidereal longitude **without calling
`compute_vimshottari`** — a shared code path proves nothing; (ii) per row, every level 1–4, not one
broadcast row; (iii) compare **lord AND both boundaries** — lord-only is a membership check and
earns nothing; boundaries need a stated, justified tolerance (dates are JD-rounded); (iv) remove the
`if chart_id == CANONICAL_CHART_ID` gate — derive each chart's own expected starting lord; (v)
honest per-row verdict via `two_pass_verdict(...)`: agree→`two_pass_verified`,
disagree→`divergent_flagged`+WARNING, not-computable→`single`.

**3b. Prove it discriminates (before trusting one green row).** Mutate a lord to valid-but-wrong →
must fire; a boundary beyond tolerance → must fire; a boundary within tolerance → must NOT fire;
each probe confirmed to reach the code under test (rule 4). Report the full-run disagreement rate —
if exactly zero across 1.36M, be suspicious and say which: genuinely-that-good (state confidence) or
comparison-not-biting. A second verifier that never disagrees is the defect this campaign exists to
kill; hold yourself to the standard you enforced on everyone else.

**→ HUMAN GATE 4:** Abhisek runs the re-promotion backfill (env, dry-run default, one chart first).
STOP until confirmed.

**3c. Re-earn + close.** Rows that agree return to `two_pass_verified`; disagreements stay
`divergent_flagged` and are **reported to Abhisek as real engine defects, not silently corrected**.
Wire the verifier into the build so future rows are earned at write time. Confirm the invariant's
detector-liveness sees `divergent_flagged` populated if any real divergence exists.

---

## Recording (each stage)
Append to `CI_EFFICIENCY_AUDIT_v1_0.md §6` as each stage lands; correct every stale surface **in
place** (the campaign hit doc-drift three times). Note in passing but do NOT fix:
`SC-pointer:query_muhurta_lattice` (real red on `main`, not M-22, needs an owner); TAP-6 arming not
before 2026-08-08 measured against the `two_pass_verified_literal` job.

## Deliverable (final, after Stage 3)
Prose, per stage: the verifications, the human-gate hand-offs, the check-level invariant results,
the served deltas. End with three plain statements:
1. Are all prohibited/deprecated values gone and does every `verified=True` row across the estate
   trace to a verifier that actually examined it — yes/no, with the count of any that don't and why
   they're honestly labelled.
2. How many of the ~1.36M rows are now honestly `two_pass_verified` because an independent
   re-derivation agreed — and did the second pass surface real disagreements the native-only check
   had hidden.
3. Is the standing invariant now fully green on live `main` — and if not, exactly what remains and
   whether it needs a human.
