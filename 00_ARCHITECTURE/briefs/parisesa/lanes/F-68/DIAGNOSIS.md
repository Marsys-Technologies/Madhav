---
lane: F-68
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA-LEAD (sonnet)
verdict: BOARD MISCLASSIFICATION — flagging for conductor correction, NOT landing as-is
---

# F-68 — phala_predictive_anchors_get numeric leak under non-calibrated tag

## 0. Board correction (read first)

BOARD.md / LEASES.json / the S3 kickoff brief all classify F-68 as `BRANCH-EXISTS (adopt
ekv/b-07-nimitta-tag)`, with the instruction to rebase and land. **I read the branch's actual
commit before adopting it, per plan §3 Stage-D discipline ("mechanism to file:line, read and
quoted"), and it does not close F-68's claim.** Recommend BOARD.md's F-68 row move from
`BRANCH-EXISTS (adopt)` back to `OPEN (full pipeline)`, crediting `ekv/b-07-nimitta-tag`'s single
commit (`8f9a1197b`) as a **partial, non-blocking, orthogonal prerequisite** (vocabulary hygiene)
rather than the fix. Not landing `ekv/b-07-nimitta-tag` myself; leaving it for the conductor/
PRATINIDHI to decide whether to still merge it (it's harmless, §N.4-compliant, TDD'd, 128/128
green) independent of F-68's real remediation.

## 1. What the branch's one on-topic commit actually does

`ekv/b-07-nimitta-tag` is 23 ahead / 6 behind `main`, but only ONE commit (`8f9a1197b`, "ekv(b-07):
confidence_basis named constants — no bare literals in emission sites") is F-68-labeled; the other
22 commits are the rest of the `ekv/lead-shastra` Stream-B ancestry (B-01..B-05, unrelated to S3's
lease — dignity oracle, bundle_adapters, tool_name_bridge, prospective_ledger — touches S1's and
S2's files, not mine to touch or land).

Commit `8f9a1197b` itself (verified via `git show --stat`, 6 files, 157/-7 lines): introduces
`brahmagyan/phala/confidence_vocab.py` with `STRUCTURAL_NOT_YET_EMPIRICAL` / `CALIBRATED_EMPIRICAL`
named constants and swaps three emission sites (`ph_nimitta/engine.py`, `ph_sankrama/engine.py`,
`ph_sodhana/engine.py`) from a bare string literal to the constant. This is a real, correctly-TDD'd
§N.4 vocabulary-hygiene fix — but §N.4 (no bare literals) is a **different defect class** than
F-68's actual claim.

## 2. F-68's actual claim (re-read from corpus, decomposed)

- **C1** — `phala_predictive_anchors_get` serves precise numeric `posterior` (4-decimal),
  `confidence_low`/`confidence_high`, and lift-decomposition factors (`base_rate_value`,
  `promise_lift_value`, `activation_lift`, `trigger_lift`, `ayanamsha_robustness_modifier`).
- **C2** — every anchor sampled (both canonical charts) carries `confidence_basis:
  'structural_not_yet_empirical'` with NO exception — the tag is never conditionally overridden.
- **C3** — this is the identical defect class the project's own P3-b tier-suppression principle
  (ka_kshetra shape_only/calibrated split) exists to prevent, applied one layer over in L4 Phala,
  and F-68 claims L4 implements none of P3-b's suppression discipline.

The `ekv/b-07` commit addresses none of C1/C2/C3 — it only renames the string that trips C2. Numeric
suppression (the actual fix C1/C3 require) is untouched.

## 3. Mechanism — verified directly in `ekv/b-07-nimitta-tag`'s own tree (post-commit state)

`platform/python-sidecar/services/ph_nimitta/engine.py`:
- **Line ~418** — `AnchorRecord.confidence_basis: str = STRUCTURAL_NOT_YET_EMPIRICAL` (dataclass
  default, now a named constant post-`8f9a1197b`, but still **unconditional** — no code path in
  this file ever sets it to `CALIBRATED_EMPIRICAL`; grepped, zero assignments other than the
  default).
- **Line ~472, ~579, ~685** (three separate `derive_anchor_from_*` builder functions) — each calls
  `compute_posterior(base_rate=..., pratijna_grade=..., ...)` and attaches the resulting
  `posterior`/`lift` to the `AnchorRecord` **unconditionally**, with no branch gating the
  attachment on `confidence_basis`. Since `confidence_basis` is always
  `STRUCTURAL_NOT_YET_EMPIRICAL` (per C2 above), every served anchor gets full numeric
  posterior/lift/confidence-band data despite being permanently tagged non-calibrated.

Confirms the finding's claim is still live post-`8f9a1187b` (verified by reading the file at the
branch's own HEAD, not main — so this is not a stale read).

## 4. Comparison pattern (the fix should mirror) — P3-b in `ka_kshetra`

Not yet located in this pass (would require reading `platform/python-sidecar` L3 Kāla
`ka_kshetra` writer for the shape_only/calibrated split cited in the finding as precedent) —
flagging for SPEC stage rather than guessing at the exact function; SPEC author should grep
`shape_only` / `calibrated` in the L3 Kāla writers before designing F-68's suppression predicate,
so the L4 fix reuses the same shape rather than inventing a second vocabulary for one epistemic
distinction (this is exactly F-68's own complaint about L4 vs P3-b).

## 5. Sibling census

`compute_posterior()` / `AnchorRecord` pattern is local to `ph_nimitta/engine.py`'s three
`derive_anchor_from_*` functions (bhavishya, convergence, discovery) — all three share the identical
unconditional-attach defect (see §3, three line numbers = three call sites, one root cause: no
suppression predicate exists yet, not three independent bugs). `ph_sankrama/engine.py` and
`ph_sodhana/engine.py` (also touched by `8f9a1197b`'s vocab rename) were NOT checked in this pass
for the same numeric-unconditional-attach pattern — recommend as part of SPEC's sibling coverage
per §3 Stage-S requirement 4, since they share the same confidence_vocab.py import and are in the
same OWNS path (`platform/python-sidecar/services/ph_nimitta/**` is explicitly in S3's lease;
`ph_sankrama`/`ph_sodhana` are not, but the shared vocab file means a suppression predicate added
to `confidence_vocab.py` would be visible to them — worth a cross-stream note, not a lease grab).

## 6. Blast radius

- `ekv/b-07-nimitta-tag`'s 22 non-F-68 commits (Stream B ancestry) are explicitly out of scope —
  not evaluated here, not to be merged as a side effect of adopting F-68.
- F-68 is TIER1-CORRECTNESS — highest-value lane in the S3 set; recommend it get SPEC priority
  alongside F-34 rather than waiting behind the CL-13 exemplar queue.
