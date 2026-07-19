---
artifact: REPORT_PG-2
type: WAVE CLOSE REPORT (BRIEF_PG-2 §C)
wave: PG-2 — Paripraśna Open-Question Diagnostic
status: closed
authored_by: Claude Code (Sonnet 5), conductor session, 2026-07-19
governing: BRIEF_PG-2 v1.0, CONDUCTOR_PROTOCOL.md v1.4, ESCALATION_POLICY_v1_0.md v1.1, ADJUDICATOR_CHARGE_v1_0.md v1.1
predecessor: PG-1 (REPORT_PG-1.md, PR #613 still unmerged at this wave's close)
---

# REPORT_PG-2 — Wave Close

## Status: **CLOSED — GATE GREEN (11/11)**

## Summary

PG-2 diagnosed every open question PG-1 left. 6 lanes ran in **enforced isolated
worktrees** (the corrective discipline this wave exists partly to demonstrate — PG-1's
shared-checkout deviation caused a real scope-warden false positive; PG-2 had zero
such incidents across 6 lanes), producing 44 evidenced diagnostic findings. All 6
lanes reached Opus-floor Phase-1 ACCEPT on the first attempt (one lane, Z-2, needed a
transient-API-error retry that lost no committed work — protocol §6.4, not counted as
an attempt). The §G gate (11 assertions) ran twice — mechanically, then by an
independent fresh-context Opus gate runner performing its own adversarial anti-gaming
pass — and closed **GREEN on all 11**, including all 7 integrity assertions, after two
carried items (a stale coverage-arithmetic claim, a missing governing-brief import)
were fixed post-gate-review.

## Both central questions, answered from probes this wave ran

**(a) Why does `chart_facts` diverge?** *Resolved, benign.* `chart_facts` stores one
full ~27,677-row fact set **per ayanamsha** (5 partitions) plus 135 ayanamsha-invariant
rows, so one fully-built chart is 138,519 rows; the two built charts sum to 276,206
exactly. The sealed 27,554 is the stale v1.0 **single-ayanamsha** figure — the
"divergence" is a per-ayanamsha-vs-all-ayanamsha **scope mismatch**, not conflation,
accretion, duplication, or instability. All 6 hypotheses were driven to a definitive
conclusion: H1 (per-ayanamsha ×5) and H2 (legitimate structural growth) CONFIRMED; H3
(build_id accretion), H4 (chart conflation), H5 (active write), H6 (non-determinism)
all REFUTED with direct evidence. **PG-1's own "unstable across probes" claim is
itself resolved as a category error** — it compared an unfiltered all-charts count
against a chart-scoped filtered count, not a repeated identical query.

**(b) Does the chat engine work?** *Resolved: NO.* `/api/chat/consult` fails
deterministically with HTTP 500 on every invocation, at the bundle-hydration stage,
before any planning synthesis or streaming begins. Root cause, code- and
manifest-confirmed: `bundle_hydrator.ts:25` hardcodes `FLOOR_ASSET_IDS =
['FORENSIC','CGM']` and throws if a listed asset is absent from
`CAPABILITY_MANIFEST.json`; `FORENSIC` was deleted from the manifest in PR #187
(Legacy Teardown) and never removed from this hardcoded list — the same failure class
as the prior LCA-2 regression, one layer downstream. Confirmed via two live,
Firebase-authenticated invocations against the native's own account and chart,
byte-identical 3.5 minutes apart (steady-state, not cold-start). This also resolves
why the prediction detector never fires (wired correctly, structurally unreachable —
no turn ever completes) and reframes the empty conversation store honestly: not "no
traffic," but "every request crashes before it can write a reading."

## Lanes table

| lane | verdict | commit | headline |
|---|---|---|---|
| X-1 | ACCEPT | `15fc1cf8` | chart_facts divergence resolved benign |
| X-2 | ACCEPT | `e9cd798d` | chat engine fails; root cause found, live-confirmed |
| X-3 | ACCEPT | `22f3407f`, `1a57181e` (hygiene fix) | coverage → 133/139 (~96%); Bearer-key mystery resolved (stale key, not broken auth) |
| X-4 | ACCEPT | `bee74479` | all 8 unverifiables/unaudited items closed |
| X-5 | ACCEPT | `1fd2e076` | OT-11: 3 ledgers not 2, both options costed, no choice made |
| M-1 | ACCEPT | `0f3a2ad5` | **PG-1's gate ruled VALID**, 6 correction-worthy defects found, none voiding |
| Z-2 | ACCEPT | `fa3ed5dd`, `91cd2d57`, `a446cc36`, `34df999d` | synthesis: 5 deliverables + CURRENT_STATE |

Full machine-checkable receipts: `state/VERIFICATION_RECEIPTS.md`. Every lane operated
in its own isolated worktree/branch (`pg2/<lane>` at `Madhav-pg2-<lane>`) — verified
via `git worktree list` before dispatch (B-3 hard gate) and via clean per-lane
`git diff --stat pg2/wave...HEAD` after merge (zero cross-lane touches, zero commit
races — the exact defect class PG-1 introduced last wave did not recur).

## M-1's meta-audit of PG-1 — the wave's second most important result

**Top-line: PG-1's gate result is VALID.** M-1 attacked it adversarially (per its
explicit charge, "do not defend the predecessor") and it held under both M-1's own
re-derivation and this wave's independent Phase-1 verifier's re-re-derivation. Six
correction-worthy defects were found, applied as `[CORRECTED 2026-07-19 / PG-2]`
blocks to PG-1's sealed artifacts (originals preserved, not rewritten):

1. **87-vs-98 finding-count discrepancy**: PG-1's sealed report says 87 in ≥4 places
   while the raw `pg1_findings.jsonl` has 98 lines (87 lane findings + 11 machine-
   readability addendum rows added post-close to fix gate assertion G.1). The report
   is a stale pre-addendum snapshot. **Corrected: 98 is authoritative.**
2. **Critical-severity count off by one** (report says 5, file has 6 —
   `PG1-Q1-0007` is correctly named in the report's prose but the count itself was
   wrong). **Corrected.**
3. **The G.1 addendum is genuine, not post-hoc fabrication** — independently proven
   via git commit-timestamp forward-causality (the audit report commit is single-file
   and was never modified after; the addendum commit, made later, touched only the
   jsonl shards) by M-1, then independently re-proven from scratch by both this
   wave's Phase-1 verifier and its gate runner. **This is the single most important
   integrity finding of the wave**: had it gone the other way, PG-1's entire gate
   result would have been void.
4. **10/10 of M-1's spot-verified PG-1 findings hold**, with one (NO-LEAKAGE)
   actually **understated** by PG-1 (worse in reality than PG-1 reported) and one
   (F-25u's "unstable" framing) confirmed imprecise for the exact reason X-1
   independently found.
5. **PG-1's own protocol deviations** (shared checkout despite its own §4 mandate;
   D-3's commit riding inside R-1's; wave branch cut from local not origin main;
   G.9's check modified mid-wave) were assessed as commit-hygiene issues that do
   **not** compromise the reliability of any specific finding — a judgment
   independently reached by M-1, this wave's own verifier, and the gate runner.
6. **The uncited-prior-work pattern is not universal but does extend beyond
   `chart_facts`**: a third prior document, `ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md`
   (2026-06-28), had already partially diagnosed the divergence as "multi-build
   idempotency residue," which PG-1 also failed to cite. Reconciled with X-1's fuller
   resolution (see `PG2_DIAGNOSTIC_REPORT_v1_0.md` §2) — both can be true: multiple
   `build_id`s legitimately exist (X-1 confirmed zero natural-key overlap between
   them), and an earlier session correctly flagged them as worth investigating
   without that investigation reaching X-1's definitive per-ayanamsha resolution.

## Gate result

**GREEN on all 11 assertions**, confirmed twice independently (mechanical script, then
fresh-context Opus gate runner + its own adversarial anti-gaming pass on itself). Two
items the gate runner flagged as needing conductor-level correction before the gate
could be called clean were fixed post-review, not silently absorbed:

1. **`RETRIEVAL_SYSTEM_TRUTH_v2_0.md`'s coverage arithmetic did not reconcile**
   (claimed "133/139 combined, two remain unexercised" — 139−133=6, not 2). Corrected
   in place: the true unaccounted set (0–4 additional tools beyond the two named) is
   recorded as genuinely unknown pending a programmatic set-difference, rather than
   asserting a precision the wave's evidence didn't support (PC-1).
2. **The governing brief `CLAUDECODE_BRIEF_PG2_DIAGNOSTIC_v1_0.md` was never
   committed to `origin/main`** (same class of gap PG-1 hit with its own artifacts) —
   the gate runner could not cross-verify report structure against the brief's exact
   language. Imported into `pg2/wave` and stamped closed.

Both fixes are conductor-level, mechanical, evidence-preserving corrections — neither
required re-running a lane or re-verifying content, consistent with how PG-1's
analogous R-1 scope-warden fix was handled (a process-layer correction, not a
content-layer one).

**Final proof: PASS.** Both one-sentence answers (quoted above) are supported by
probes this wave ran — DB queries independently re-executed by two separate verifiers
for (a); two live authenticated HTTP invocations plus source-code and manifest
confirmation, independently re-verified, for (b).

## Process notes — the corrective discipline held

The brief's central process correction — enforced worktree isolation — worked exactly
as intended. Zero commit races, zero scope-warden false positives, zero lane requiring
a corrective re-attempt this wave (contrast PG-1's R-1/D-3 incident). The one real
process wrinkle this wave hit was structural, not disciplinary: PG-1's own PR (#613)
remains unmerged to `origin/main`, so PG-2's branch (correctly cut from fetched
`origin/main` per B-1) had none of PG-1's artifacts available for M-1 to audit or Z-2
to correct. Resolved via a surgical file-content import (`git checkout origin/pg1/wave
-- <paths>`, NOT a branch merge — a full merge was attempted first and produced
conflicts, traced to an unrelated ~50-commit D-3-closeout chain also sitting on
`origin/pg1/wave`'s history, discovered and avoided). This import (`c561bb01`) will
need reconciliation once #613 eventually merges — recorded as a known follow-up for
whichever wave opens next, not deferred silently.

## Parked items

None. No lane hit a 3-attempt PARK; no circuit breaker tripped; no §2 halt-and-report
class was reached. §0.3's one PG-2-specific escalation class (active data corruption)
was explicitly checked for by X-1 (`POTENTIAL_CORRUPTION_FLAG: false`) and not found —
the chart_facts divergence is legitimate scope-labeling, not corruption.

## Native disposition items (for async review, per ESCALATION_POLICY §3)

1. **OT-11 (prediction ledger)** — both merge and document options fully costed by
   X-5; genuinely a native-level design decision (PC-8), not resolved by this wave.
2. **The `bundle_hydrator.ts` FORENSIC bug** — a one-line fix (drop `'FORENSIC'` from
   the hardcoded `FLOOR_ASSET_IDS` array) that unblocks the entire chat engine. Not
   fixed by this wave (§F2 read-only), but flagged as the highest-leverage single
   change available: cheap, isolated, and a hard prerequisite for any future
   streaming-protocol work (C-2's original 6-9 week shim estimate stands unrevised —
   the streaming layer was never reached by X-2's probe, so C-2's analysis is
   untouched; this bug sits strictly upstream of it).
3. **The residual coverage-arithmetic gap** — 0 to 4 MCP tools may remain genuinely
   unexercised beyond the 2 X-3 named; a programmatic set-difference (not a manual
   tally) would close this definitively.
4. **PG-1's PR #613 remains unmerged** — both this wave's substrate-import
   (`c561bb01`) and its own eventual PR will need rebasing once #613 lands.
5. Two new/updated architecture-doc items from Z-2's synthesis: OT-11 (costed, open),
   and §16.8's consolidated new-defect append (A-14 mislabel/inversion, citation-shape
   clarification, chart_agnostic_gate confirmation, two-vs-three-ledger correction).

## What transfers forward

PG-1's original 10 recommended fixes, reprioritized with this wave's findings —
**the `bundle_hydrator.ts` FORENSIC fix is now the clear first item** (it single-
handedly unblocks the wave's second-most-consequential open question), ahead of
`codegen:check` CI-wiring (PG-1's original #1, still valid, now #2). Full list in
`PG2_DIAGNOSTIC_REPORT_v1_0.md`.

## Rollback pin

Not applicable — PG-2 is read-only on application source with one authorized fenced
write (X-2's chat probe, confined and recorded per §F2.2). G.11 confirmed zero
product-path touches across the entire wave.

## Deliverables sealed

- `00_ARCHITECTURE/PG2_DIAGNOSTIC_REPORT_v1_0.md`
- `00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v2_0.md` (v1.0 retained, superseded)
- `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` → v0.7
- `00_ARCHITECTURE/pg1_audit/REPORT_PG-1.md`, `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md`
  — both carry `[CORRECTED 2026-07-19 / PG-2]` blocks
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2.3 — PG-1 + PG-2 pointers (completes the
  one §C item PG-1 left undone)
- `00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings.jsonl` (44 findings)
- This report.
