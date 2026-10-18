---
artifact: DECISION_TESTING_STANDARD_v1_0.md
version: "1.0"
status: ACTIVE
authority: owner, 2026-10-16
recorded_on: 2026-10-16
decision_id: D-OWNER-TESTS-20261016
changelog:
  - "1.0 (2026-10-16): records the owner's campaign-wide optimum testing standard and supersedes conflicting testing and review-round rules."
---

# KĀLA-YANTRA — optimum testing standard

The owner directed on 2026-10-16 (~16:03Z): "adopt this testing strategy for the entire campaign … make this an authoritative decision and amend any rules that exist."

## Authoritative standard (verbatim)

TESTING STANDARD (owner decision D-OWNER-TESTS-20261016, AUTHORITATIVE and campaign-wide; replaces "every reversion must fail" and A2 D-17's two-round cap). Tests are optimum, not extraneous.
A step / review is MET iff: (i) its oracles pass at the pinned merged head; (ii) the REVIEWER — not the author — enumerates every DISTINCT production claim from the item's brief, packet and cited classical rules, writes the list into the verdict, and shows each claim has at least one doctrine-grounded oracle (classical source cited; B.3/B.10) whose SINGLE planted reversion actually FAILS at that head; (iii) every reversion that exposes a real defect is fixed (fail-on-revert test) — known real defects are fixed regardless. Plant at most ONE reversion per claim; no combinatorial variants. A surviving reversion that is a variant of an already-covered claim, or that changes no production behaviour, is non_blocking and never blocks MET. Never golden-capture current output; never ask for an oracle per mutant. One bounded review round; non_blocking findings never trigger another round; a second round only for a BLOCKING finding. Unchanged: N.8 (each claim measured by a detector that can read false), N.7.6 honest nulls, SR-A4-01 strict ordered completion, A1, personal-data handling.

## Supersession and retained safeguards

This decision governs every KĀLA-YANTRA builder, reviewer, step and packet. It supersedes the blanket “every reversion must fail” requirement, per-mutant oracle demands and A2 D-17's two-round cap / automatic acceptance after round two, including A4's reference to that cap. A2's fail-on-revert proof for every fixed finding remains required. Known real defects are fixed regardless; non_blocking variants do not earn more review rounds.

Unchanged: root CLAUDE.md §N.8 (a detector that can read false), §N.7.6 (honest nulls), SR-A4-01 (strict ordered completion), Amendment A1 and personal-data handling. Neither root CLAUDE.md nor the FROZEN orchestrator contract is amended.

## Evidence and compatibility

The reviewer records the pinned merged head and the complete distinct-claim list derived from the brief, packet and cited classical rules. Each claim maps to a source-cited oracle, its passing command/exit at that head and its single planted reversion's failing command/exit. Builder results are inputs; the reviewer owns enumeration and verification. Builders supply one doctrine-grounded oracle per distinct claim and a fail-on-revert proof per fixed finding, without mutant variants or captured-current-output goldens.

Step receipts retain their existing shape, including `mutation_verified:true`: it now attests that every reviewer-enumerated claim's single planted reversion failed at the pinned merged head and real defects were fixed. Detector types, paths and regex patterns are unchanged. This record authorizes no receipt, MET verdict or completion by itself.
