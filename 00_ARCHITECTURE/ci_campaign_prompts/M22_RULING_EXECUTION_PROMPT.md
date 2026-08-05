# Claude Code task — execute against the second-pass ruling (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection). Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`. **State the `origin/main` SHA you read
from in your report** — the stale-worktree error cost three retracted claims last pass and the local
tree is still on `parishodhana/dark-corpus-remeasure`.

## The ruling (given, not open)

A check earns `two_pass_verified` only if it **could have failed for a reason other than a bug in
itself** — it must discriminate over the **producer's actual output space**, not the space of all
possible values.

**Operational test:** mutate the producer's output to a *plausible wrong* value (not an impossible
one) and see whether the check fires. Wrong lord with a valid name; correct lord with wrong period
boundaries. If the only mutations it catches are ones the producer could never emit, it is a
tautology over its own input and earns nothing.

**Therefore a set-membership check does NOT count as a second pass.** `chart_dashas` is **not
earned**. Exposure is **~1,366,641 rows**, not ~500,000.

**Exception, to keep the rule honest:** membership checks DO earn credit where the value crosses a
trust boundary (third-party ephemeris, deserialisation seam) and a plausible garbage value could get
through. Apply the same test, different input space.

Precedent — this is the third instance of one class: `pillars_meet_reachability_pass` (tautology),
`lel_zero_leak_pass` (proxy asserts a scan that never runs). Cite them.

---

## Task 1 — Answer the vocabulary question (blocking; nothing else waits on it)

Two homeless concepts now exist, not one. Place both, or show they're already placed.
- **(i)** "computed once, deterministically, from canonical inputs, never independently re-derived"
- **(ii)** "structurally validated (shape/membership) but not independently derived" — created by
  this ruling

Required evidence before any new member is proposed:
- **Quote all 13 `VERIFICATION_PASS_STATUS_VOCAB` `meaning` fields verbatim.**
- For `computed_extension` (14,387 rows), `floored` (8,130), `not_defined_for_nodes`,
  `pending_w3_verification`: what does each mean *in practice*? Read 2–3 real emit sites each, not
  just the docstring.
- Then answer plainly, per concept: **is it already covered? By which member?** If a member covers
  (i) or (ii), the demotion has its tier and **no new member is added**. Only if a genuine gap
  remains do you propose a string — and any new string must sort alphabetically **before**
  `two_pass_verified` (en_US.UTF8) or MV `209:144`'s `MIN()` "all verified" test silently breaks.

This is the "seventh definition" test (#996 declined a new module because the concept had a home).
Deliver the answer; **do not add a member without Abhisek's approval.**

## Task 2 — Prove `divergent_flagged` can fire

Zero rows estate-wide across 1,873,958 claimed verifications. Until it demonstrably fires, every
tier depending on that path is unproven machinery.
- In a test/dev context, inject a divergence into `ga_nakshatra`'s live `two_pass_verdict` path and
  confirm a row lands `divergent_flagged`. Confirm the injection reaches the code under test
  (rule 4).
- If it **cannot** be made to fire, that is a defect in the verifier — report it as such, loudly.
- Report whether the CHECK constraints and the serve layer handle the value correctly when it does
  appear (`isVerifiedPassStatus` → false; grade ladder; warranty sentence; `bo_pramana_mapa`
  percentages — note unknown/unhandled values silently stop those summing).

## Task 3 — Apply the ruling to the `chart_dashas` verifier (code, not data)

**Do not change any row.** Two defects, both in code:
- **The check is a tautology.** Document precisely what `_verify_vimshottari` Pass 2 compares, and
  what it would take to make it real: an independent recomputation of the dasha sequence compared on
  **lords AND period boundaries**. Scope it — do not build it in this task.
- **The native gate.** Pass 2 is wrapped `if chart_id == CANONICAL_CHART_ID`. Quantify: of the
  1,358,993 rows, how many belong to the native chart vs. every other chart. Even a good check helps
  nothing running for one chart; state what removing the gate would cost.

Deliver a scoped plan for a real Vimshottari second pass (approach, effort, what it would catch).
**No implementation, no tier changes, no backfill.**

## Task 4 — Record the ruling as doctrine

New subsection in `CI_EFFICIENCY_AUDIT_v1_0.md §6`: the rule, the operational test, the
membership-check verdict with the trust-boundary exception, the zero-`divergent_flagged` evidence,
and the three-instance precedent. Correct every surface still stating "chart_dashas is earned" or
"~500,000" / "392,001" as the exposure — **in place**, not alongside (the campaign has hit doc-drift
three times). Cross-reference `verification_vocab.py` so the next reader finds the rule from the
code.

---

## Guardrails
- **No production writes.** The drain script (#1016) is Abhisek's to run; do not invoke it, do not
  handle `DATABASE_URL`'s value. Read-only queries only.
- No tier changes to any row. No new vocabulary member without approval. No CHECK migration.
- Do not arm TAP-6 (needs ≥7 consecutive green days; earliest 2026-08-08 — and confirm the run on
  `b627114e` came back green; flag it if not).
- Branch, PR, queue merges; one line to revert where possible.

## Deliverable
Prose. The `origin/main` SHA. Task 1: 13 meanings quoted, plain yes/no per concept, member name or
proposed string with sort-order proof. Task 2: whether `divergent_flagged` fires, and the serve-layer
behaviour when it does. Task 3: what Pass 2 actually compares, the native/non-native row split, and
the scoped plan. Task 4: what §6 now says and which stale surfaces you corrected.

End plainly: **does the estate need a new vocabulary member (yes/no, which), can the disagreement
tier fire (yes/no), and is ~1,366,641 the number the demotion decision should be made against —
or did something in Tasks 1–3 change it again.**
