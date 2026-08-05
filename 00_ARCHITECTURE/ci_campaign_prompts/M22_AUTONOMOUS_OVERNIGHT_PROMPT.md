# Claude Code — AUTONOMOUS overnight run: finish the M-22 tail end to end (Madhav)

Run unattended to completion; produce **one report at the end**. No human is watching. That does not
mean "proceed no matter what" — it means **the human gates are replaced by machine gates and a
capable escalation agent, and you halt on genuine trouble instead of waiting for a person.** A run
that halts a stage with a clean diagnosis and nothing unsafe done is a **success**, not a failure.
Forcing a stage through against a failing check is the one outcome that is worse than stopping.

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection). **State the `origin/main` SHA in the report**; the local checkout is stale on
`parishodhana/dark-corpus-remeasure` — never read it. Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md
§6` (nine). Owner (Abhisek) has **pre-authorised** all four former gates: run the backfills, apply
the ~91-category grade change (readings become more honest — the safe direction), run every
production backfill. That authority is real; the safety is in *how* each write is gated, below.

## Environment precondition (check first, once)
`DATABASE_URL` must be present in the environment. **Never print, log, echo, or interpolate its
value.** If it is absent: run everything in dry-run only, write nothing, and HALT at Stage 1 with a
report saying the env was not configured. Do not attempt to source, guess, or reconstruct it.

## The universal write-gate (applies to EVERY production write in this run)
No production write happens except through this sequence:
1. **Dry-run** the exact operation; capture its planned row counts per table/tier.
2. **Independently re-derive** the expected counts read-only (do not trust the script's own numbers).
3. **Compare.** If dry-run and your independent prediction agree within a declared tolerance →
   proceed. If they diverge → **do not write**; escalate (below).
4. **Execute** (`--execute`). Scripts read `DATABASE_URL` from env; idempotent; you never handle the
   value.
5. **Re-verify:** dispatch the standing invariant (workflow `325445415`), read **at check level**
   (rule 1 — job-level conclusion lies for continue-on-error). The tables you just wrote must move
   in the predicted direction. If they don't → escalate; do not continue as if they did.
Any write whose post-state the invariant does not confirm is treated as suspect: stop that stage,
preserve state, escalate.

## Escalation instead of a human (this replaces every gate)
When you hit any of: a dry-run/prediction divergence, a mutation proof that won't fire, an invariant
check that stays red after a write, an ambiguous classification, a served-delta that is NOT purely
"more honest", or anything the brief did not anticipate —
**spawn a fresh high-capability (Opus) sub-agent** via your Task/agent mechanism, give it the full
context and the specific anomaly, and have it do one of exactly two things, with evidence:
- **RESOLVE:** diagnose the cause, prove the fix reaches the code under test (rule 4), and authorise
  continuation — but only for anomalies that are mechanical/verifiable. Record what it found.
- **HALT this stage:** if the anomaly would change user-facing claims in an unexpected direction,
  alter scope, touch rows outside the sanctioned set, or cannot be resolved to certainty — stop the
  stage, leave state clean, and write a full diagnosis to the report. Then continue to later stages
  **only if they are independent of the halted one** (Stage 3 depends on 1+2; Stage 2 depends on 1).
The escalation agent may HALT. It is never required to proceed. "Address the issue" means resolve it
*or* prove it should stop — both are addressing it.

Hard limits the escalation agent may NOT override, ever: no new vocabulary member; no CHECK
migration without it being recommended-not-applied; no handling of secret/`DATABASE_URL` values; no
touching genuinely-earned rows; no fixing `SC-pointer:query_muhurta_lattice` (not M-22); no arming
TAP-6 (needs ≥7 green days on the `two_pass_verified_literal` job, earliest 2026-08-08). If a fix
would require any of these, that is a HALT-and-report, not a proceed.

---

## STAGE 1 — Backfills
Pre-flight both scripts (`drain_prohibited_verification_status.py`,
`backfill_unexamined_dasha_tiers.py`): env-not-arg, dry-run default, idempotent WHERE clauses, tier
targets match the ruling (drain `PASS`/`pass`/`single_pass`→`single`; dasha unexamined→`single`,
membership→`classical_match`; earned rows — mudda 780, narayana 345, native vimshottari 64,
ga_nakshatra computed — untouched), all targets CHECK-legal. Then, through the universal write-gate:
drain first; then `backfill_unexamined_dasha_tiers.py --chart <CANONICAL_CHART_ID>`; then unscoped.
Confirm: prohibited/deprecated values → 0; `chart_dashas` verified count == examined count.

## STAGE 2 — Demote the 392,001 writer rows (`chart_facts` 352,485 + `chart_divisionals` 39,516)
Re-derive (do not inherit) the a/b/c split across `ga_structural`/`ga_vargas`/`ga_sensitive`/
`ga_sade_sati`: (b) no comparison→`single`; (c) approximation→`documented_approximation` **only
where CHECK-legal**, else `single` (it is NOT legal on `chart_divisionals`); (a) genuine→unchanged,
report any. Fix the four writers to emit the honest tier via `verification_vocab.py` constants —
byte-identical emissions except the deliberate tier changes, verified against the writers' tests +
double-build determinism. Backfill through the universal write-gate. **Measure the served delta**
(grounding_score/grade/warranty for one affected chart) and confirm it is purely "more honest" — if
any reading would become *less* accurate, HALT + escalate. Recommend (do not apply) the
`chart_facts` CHECK post-backfill.

## STAGE 3 — The real Vimshottari second pass (re-earn the ~1.36M, don't relabel)
Build an independent verifier: re-derive from the Moon's sidereal longitude **without calling
`compute_vimshottari`**; per row, levels 1–4; compare **lord AND both boundaries** with a stated,
justified JD tolerance; remove the `if chart_id == CANONICAL_CHART_ID` gate (derive each chart's own
starting lord); verdict via `two_pass_verdict(...)`. **Prove discrimination before trusting a green
row:** wrong-lord → fires; boundary beyond tolerance → fires; within tolerance → does not; each
probe confirmed to reach the code (rule 4). Run it; agreements → `two_pass_verified` (through the
write-gate), disagreements → `divergent_flagged` and **reported as real engine defects, not
silently corrected** — if the disagreement rate is 0 across 1.36M, treat as suspicious and say which
of {engine-that-good / comparison-not-biting}, escalating if you cannot tell. Wire the verifier into
the build for future rows.

---

## Recording & report
Append to `CI_EFFICIENCY_AUDIT_v1_0.md §6` as each stage lands; correct stale surfaces in place.
Branch/PR per stage; the queue merges. At the end, one report:
- The `origin/main` SHA; per stage: what was verified, every write-gate's predicted-vs-actual, the
  invariant's check-level result after each write, the served deltas, every escalation (what the
  Opus agent found and whether it resolved or halted).
- Three plain answers: (1) are all prohibited/deprecated values gone and does every `verified=True`
  row estate-wide trace to a real examination — yes/no + counts of any exceptions and why they're
  honestly labelled; (2) how many of the ~1.36M are now honestly `two_pass_verified` by independent
  agreement, and did the second pass expose real engine disagreements; (3) is the standing invariant
  fully green on live `main` — and if not, exactly what remains.
- A **HALT LOG**: every stage or step that stopped, why, the clean state it left, and the smallest
  human action that would unblock it. This is the most valuable section — do not bury it.

End with one line: **how far did the run get autonomously, and is anything in production in a
half-applied or unverified state (it must not be — every write is gated and re-verified; confirm).**
