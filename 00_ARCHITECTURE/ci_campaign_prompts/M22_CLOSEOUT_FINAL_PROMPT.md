# Claude Code task — CLOSE OUT M-22: fix, drain, and make recurrence detectable (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection). **State the `origin/main` SHA you read from** — the local checkout is still on
`parishodhana/dark-corpus-remeasure`; never read from it.

This is the closing task. Four campaigns have each declared completion and each was followed by a
deeper layer. **Do not declare completion — deliver the state and let the invariant declare it.**

Standing rules: `CI_EFFICIENCY_AUDIT_v1_0.md §6` (nine). The two that govern here:
- **Count what the verifier READ, not what its verdict was attached to.**
- Assertions outrun evidence *in whatever direction the asserter leans* — including yours and mine.

**If you find a fifth layer: report it, do not absorb it and do not silently widen scope.** A finding
that stops this task is a success, not a failure.

---

## Phase 0 — Verify the ground you're standing on

1. `origin/main` SHA; confirm the drain script (#1016) has **not** been run against production
   (query for surviving `PASS`/`pass`/`single_pass` counts — if they're gone, Abhisek ran it; adjust
   and say so).
2. TAP-6 status **at the job/law level**, not the workflow: is `two_pass_verified_literal` green?
   Report the `SC-pointer:query_muhurta_lattice` failure separately — it is not M-22's and must not
   be fixed here; just name it and its owner-facing state.
3. Re-confirm the headline numbers before acting on them: rows by tier per table, the
   examined-vs-stamped split for `chart_dashas`. **Do not inherit ~1,749,805 — re-derive it.**

## Phase 1 — The atomic fix (order is not optional)

All three land before any backfill. Together they are one change; separately they each create a
window where the estate lies differently.

**1a. Serve-layer wording first (safe alone, honest under any tier state).**
`envelope.ts:929-930` renders every non-verified row as *"single-pass **candidates**, not
confirmations."* "Candidate" is editorial and false for a deterministic computation. Rewrite so the
sentence reports what the tier actually means — `single`'s own vocab meaning ("no second derivation
ran, so nothing could have contradicted the value") is the source of truth for the wording. Add a
form for a page that is deterministic-but-not-cross-verified. Update the grade ladder only if the
wording change requires it — **do not invent a new grade**. Regenerate the codegen mirror; confirm
`codegen:check` passes.

**1b. Stop the broadcast.** `:3047-3048` stamps one L1 verdict onto every row at every level.
Rows a verifier never examined must carry the honest tier, not an inherited one. Fix so a verdict
applies **only to rows the verifier actually read**. Unexamined rows → `single`.

**1c. Fix the `vimshottari_kp` filter mismatch.** 17,910 rows are stamped by a verifier whose input
filter (`kp_sublevel is None`) excludes them — a verdict about rows the check never saw. This is a
distinct bug from the broadcast; fix the filter or stop the stamping, and say which.

Writer emit sites use the sanctioned constants from `brahmagyan/verification_vocab.py`. Target
tiers, **no new member and no CHECK migration** (both are already permitted by both constraints):
- unearned / unexamined / no comparison → **`single`**
- membership- or reference-table-validated (relay fidelity, not re-derivation) → **`classical_match`**
- genuinely earned (mudda 780, narayana 345, native vimshottari 64, and `ga_nakshatra`'s computed
  verdicts) → **unchanged**

## Phase 2 — Backfill existing rows

- Extend or write alongside `drain_prohibited_verification_status.py`; same discipline —
  `DATABASE_URL` from env, never an argument, never a value you handle.
- **Test against one chart**, publish before/after counts per table and per tier.
- **Hand the production invocation to Abhisek.** Do not run it. No destructive rebuilds.
- State plainly what a served reading looks like before and after for one affected page:
  `grounding_score`, grade, warranty sentence. That is the user-visible delta and he should see it
  as text, not as a number.

## Phase 3 — The standing invariant (this is the actual close)

Everything above fixes today's state. This is what stops a fifth layer being *discovered* rather
than *reported*. Build a check that runs on a schedule (dispatch + cron; **not** a required PR
check) and fails loudly when the estate drifts:

1. **Claim-vs-evidence:** for every table carrying `verification_pass_status`, compare rows claiming
   a `verified=True` tier against rows a verifier demonstrably examined. Divergence beyond a
   declared tolerance = FAIL, naming table and delta. *This is the query nobody had written; the
   broadcast survived because of that.*
2. **Vocabulary conformance:** any value in the data outside `ALL_STATUSES`, or any deprecated
   alias, = FAIL with counts. *`PASS` survived two campaigns because nothing watched the data.*
3. **Detector liveness:** assert `divergent_flagged` remains reachable — a periodic proof, not an
   assumption. If a verifier can no longer disagree, that is the defect appearing again.
4. Emit a short report every run — counts by tier by table — so drift is visible as a trend, not
   only as a threshold breach.

**Mutation-prove each of the three** (rule 4: confirm the probe reaches the code under test). A
watchdog that cannot fail is the exact defect this campaign is about, and building one here would be
the fifth layer.

## Phase 4 — Close the record

- **Arm `two_pass_verified_literal`** as a required check **only** when: ≥7 consecutive green days
  **on that job/law specifically** (my earlier workflow-level condition was misspecified — an
  unrelated gate reset a streak meant to measure one detector), AND Phase 1 has landed. If the
  streak isn't there yet, record the start date and the earliest arming date. Do not arm early.
- Recommend (do not apply) a `CHECK` on `chart_facts` **after** the backfill — its absence is why
  `PASS` survived unnoticed.
- Restate the three unset secrets by exact name (`TAP_MCP_SERVER_URL`,
  `TAP_MCP_SMOKE_BEARER_TOKEN`, `TAP7_API_BASE_URL`) — owner-only, names never values.
- **Scope but do NOT build** the real Vimshottari second pass (re-derive from Moon's sidereal
  longitude; compare lords AND both boundaries per row at every level; ~1 focused day; boundary
  tolerance is the hard part because dates are JD-rounded). It would re-earn ~1.36M rows honestly.
  That is the *next* piece of work, deliberately outside this close-out.
- §6 final subsection: the broadcast, the corrected exposure, the three Claude errors already logged,
  the standing invariant and what each of its three checks watches. Correct every stale surface
  **in place**.

## Guardrails
- No production writes by you. No new vocabulary member. No CHECK migration. No new grade.
- Do not fix `SC-pointer:query_muhurta_lattice`.
- Emissions byte-identical for identical inputs **except** the deliberate tier changes, each listed.
- Branch per phase; queue merges.

## Deliverable
Prose. Phase 0's re-derived numbers (and any disagreement with this brief). Phase 1: the three fixes,
the wording before/after verbatim. Phase 2: tested before/after counts and the one-page served
delta. Phase 3: the invariant's three checks and their mutation proofs. Phase 4: arming state,
recommendations, what §6 records.

End with two plain statements:
1. **Does every `verified=True` row in the estate now trace to a verifier that actually examined
   it — yes or no**, and if no, exactly how many don't and why they're honestly labelled instead.
2. **What would the standing invariant have caught, had it existed six months ago** — name the
   specific defects from this campaign it would have surfaced, and any it still would not.
