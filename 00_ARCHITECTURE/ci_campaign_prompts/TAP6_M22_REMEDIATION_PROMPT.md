# Claude Code task — TAP-6 red on `main`: remediate the M-22 detector, not the exemplar (Madhav)

Repo: `Marsys-Technologies/Madhav`, `main` queue-gated (open PRs; the queue merges). Standing rules
from `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6` apply; the ones that dominate here:
- A detector's description is not evidence about the code. Read the code the hit points at.
- Impossible/wrong instructions get recorded, not worked around. This brief reverses a prior
  session's diagnosis — re-verify the reversal too before acting on it.
- Prefer honestly red over silently green — **and honestly green over permanently red.** A red
  advisory check that everyone merges over trains people to ignore red.

## The corrected diagnosis (RE-VERIFY each claim before building on it)

A prior report called `ga_nakshatra.py:125` "a real M-22 violation — verification status assigned
as a string literal." Reading the code says otherwise:

1. **Line 125 is a computed verdict, not an assertion.**
   `per_claim[claim] = "two_pass_verified" if agrees else "divergent_flagged"`, where `agrees`
   compares an independent re-derivation (`_derive_nakshatra_pada(lon)`) against the engine value.
   This *is* M-22 compliance — the docstring records it as the 2026-07-30 fix for the blanket
   `"PASS"` literal (SAMĀPTI A7-N8-AUDIT F-11, DVA Ruling 13). Verify by reading
   `platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py` around lines 100–150.
2. **TAP-6's pattern cannot see the difference.** `tap6_method_grep.ts` pattern
   `two_pass_verified_literal` = `/(=|:)\s*['"]two_pass_verified['"]/` — fires on asserted and
   computed alike. The check's description ("must be computed, never passed as a literal") claims
   more than the regex measures. That is the §N.8 earned-signal defect in a red signal.
3. **`ga_nakshatra.py` has no baseline entry**, so its one hit is NEW → FAIL. The M-22 *fix*
   is what turned `main` red. The detector is anti-correlated with code health.
4. **The baseline itself documents the precision failure**: `tap6_baseline.json` notes say e.g.
   "identical trimmed line text appears at ~95 OTHER emit sites... genuinely-computed... correct
   as-is" — quarantined-but-innocent, because line-hash keys on trimmed text, so identical text at
   many sites shares one fate.
5. **Stale entries exist**: `ga_dashas_writer.py` has 2 baseline entries under
   `two_pass_verified_literal` but zero current matches (`git grep` confirms). Reproduce the full
   TAP-6 run to get the exact NEW/QUARANTINED/stale sets — read the script's own hashing code (a
   quick grep for `createHash` missed it; read the file) rather than reimplementing from memory.
6. **Open question to settle while you're in there:** `CHART_FACTS_SCHEMA.json` contains 592
   textual matches of the pattern, yet the reported red named only ga_nakshatra + stale entries —
   so the script presumably filters to `.py` (or similar). Verify what it actually scans and state
   it; if `.json` IS scanned, stop and report, because the diagnosis above is then incomplete.

## Remediation — PR 1: make `main` green honestly (single PR, all four pieces together)

The goal is lexical separation: make the honest path *distinguishable by grep*, then let the grep
be exact. Not: baseline the exemplar (adds another innocent inmate). Not: teach the regex to parse
conditionals (a conditional isn't proof — `"two_pass_verified" if True else ...` asserts too).

a. **Create one sanctioned module** — e.g.
   `platform/python-sidecar/pipeline/verification.py` (pick the path that fits the package layout;
   both `pipeline/` and `ga_writers/` code must be able to import it). It owns the status
   vocabulary and an evidence-demanding constructor:
   ```python
   TWO_PASS_VERIFIED = "two_pass_verified"
   DIVERGENT_FLAGGED = "divergent_flagged"

   def two_pass_verdict(engine_value, derived_value) -> str:
       """The ONLY sanctioned producer of two_pass_verified. Callers must present
       both values; the comparison happens here (M-22 / CLAUDE.md §N.8)."""
       return TWO_PASS_VERIFIED if engine_value == derived_value else DIVERGENT_FLAGGED
   ```
   Match the existing `int()` coercion semantics of ga_nakshatra's comparison — either coerce in
   the caller before passing, or provide for it explicitly; do not silently change what "agrees"
   means. Preserve the divergence WARNING log at the call site (it names subject/claim/values —
   the helper doesn't have that context).
b. **Refactor `ga_nakshatra.py:125`** to use the helper. Its emitted values must be byte-identical
   for identical inputs — verify with the writer's tests (and note: this writer had a
   double-build determinism standard; keep it).
c. **Make TAP-6's claim equal its measurement**: exempt exactly the one sanctioned module file
   from the `two_pass_verified_literal` pattern (a file-level exemption, not a directory), and
   rewrite the pattern's `description` to say precisely what it now measures: "the literal
   assigned outside the sanctioned verification module." Add a companion note (comment or a
   second low-cost pattern) for the known residual: `two_pass_verdict(x, x)`-style fraud is
   still possible and still greppable later — name it, don't solve it here.
d. **Delete the stale baseline entries** you verified in (5) — the ratchet's own protocol
   ("the fixing lane deletes the baseline entry when it lands").

Acceptance: dispatch/observe a TAP-6 run on the PR branch → 0 NEW failures, quarantined count =
baseline entries that still match real lines, and `main` green after merge. If anything in the
verification of claims 1–6 contradicts this plan, stop and report instead of proceeding.

## PR 2 (separate lane — scope, don't execute unless trivial): drain the baseline

Migrate writer emit sites to the constants/helper file-by-file (`ga_structural_writer.py` alone
has 81 textual matches; the baseline notes admit most are correct-as-is), deleting each file's
baseline entries as it lands. This is how the ~95-innocent-sites-one-hash problem dissolves and
how the baseline returns to its intended meaning: *only* register-tracked open defects. Deliver a
per-file inventory (site count, asserted-vs-computed split from the baseline notes, effort guess)
so Abhisek can schedule it — do not bundle this migration into PR 1.

## Decision 3 — reserved for Abhisek, prepare but do not act

Once PR 1 lands and `main` is green-when-healthy: should TAP-6 (or the
`two_pass_verified_literal` pattern minimally) become a **required check**? Post-fix, any new hit
is a genuine unsanctioned literal — unlike `absence_lint` (whose survivors were non-defects), so
arming here is sound in a way it wasn't there. Present the recommendation with the first week's
run history; do not change branch protection or the ruleset yourself.

## Housekeeping in the same PR 1
- The prior audit prose (§6 and any doc that repeated "real M-22 violation at ga_nakshatra:125")
  gets a correcting subsection: the red was a detector-precision failure over the M-22 *fix*;
  a false red is the same §N.8 disease as a false green. Reconcile every surface that states the
  old diagnosis (the campaign already hit doc-drift twice; don't leave a third).
- The 5 consecutive failed `main` runs become explainable history — link the correcting
  subsection from the PR body.

## Guardrails
- Do not modify what any writer *emits* (values byte-identical for identical inputs) — this is a
  provenance/detector fix, not a data change.
- No new baseline entries for code you believe is correct. If you find a hit that IS a genuine
  assertion (not computed), that's a real M-22 defect: file it, baseline it with a register row,
  report it separately — don't fix it silently in this PR.
- Branch per PR; queue merges; every change one line to revert where possible.

## Deliverable
Prose. The re-verified truth of claims 1–6 (quote the hashing code and the scan filter); what PR 1
changed and the TAP-6 before/after counts (NEW/quarantined/stale); the PR-2 inventory; the arming
recommendation left as a decision. End plainly: **is `main` green, and is every remaining
quarantined entry a genuine tracked defect — yes or no.**
