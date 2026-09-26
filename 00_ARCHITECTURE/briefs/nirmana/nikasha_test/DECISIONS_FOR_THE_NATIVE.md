---
artifact: NIKASHA_TEST_DECISIONS_FOR_THE_NATIVE
canonical_id: NIKASHA_TEST_DECISIONS_FOR_THE_NATIVE
version: "1.0"
status: AWAITING_NATIVE — 6 decisions; the implementation plan (NIKASHA_IMPLEMENTATION_PLAN_v1_0.md) continues around every one
produced_on: 2026-09-26
campaign_id: nikasha-test
---

# Decisions for the native — Nikaṣa test campaign, Phase 6

Six decisions only the native can take. Each carries a recommendation and the cost of each option.
Register rows cited are in `NIKASHA_CHANGE_REGISTER_v2_0.md`; evidence paths are under
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/`.

## D1 · Authorize orchestrator behaviour edits for R35, R36, R37, R38

R34 (rate instrumentation) is already authorized (register §4: "native said yes"). R35 (error text
on every failure), R36 (run-killer: a registry change mid-run aborts every asset — 18 assets,
8 runs, including a 10-asset L0 run aborted in full on 2026-09-04), R37 (orphan/guardian noise),
R38 (cascade reporting) are the same class: engine behaviour, never the frozen `WriterBase`
contract.

- **Recommendation: authorize**, sequenced as packets P1 (R34/R35), P2 (R36), P8 (R37/R38, parallel
  with layer elevation, never gating).
- Cost of authorizing: ≈ 26 h of orchestrator work plus regression risk in the runner, mitigated by
  the sandbox harness (the P2 proof replays a mid-run registry change).
- Cost of declining: the from-scratch run has no rate baseline (rows_per_second NULL 268/268 — P6
  measurement), 69% of failed runs are undiagnosable (288/419 silent — P6), and the elevation
  campaign's own runs can be aborted in full by any registry edit landing mid-run (R36 evidence).
  R34's prior authorization is orphaned — a rate with no error text diagnoses nothing.

## D2 · Reopen the sealed tiers for the clause-level batch

The documentation-drift cluster (C7) plus the derivability cluster (C8) require edits to sealed
documents: tier 1 (R01, R72, R76), tier 2 (R06, R73, R75, R85, R88–R91, R109, …), tier 3 (R08,
R09, R65, R67, R68, R71, R74, R117, …). Campaign constraint §2.2: the campaign proposes, the native
reopens by ruling.

- **Recommendation: one bundled reopen per document**, with the register's per-row proposed
  replacement text as the agenda, rather than per-row rulings.
- Cost of bundling: one seal-break event per document; a single re-review scope (~40 clauses across
  three tiers); tier versions bump once.
- Cost of per-row rulings: ~30 separate reopen rulings, each re-establishing context; the C7 rows
  are individually trivial (0.5–2 h) and would cost more to rule than to fix.
- Cost of not reopening: BLOCKS_FREEZE row R71 stands (the [TRANSFERS] contradiction — D3), C-9/R09
  keeps every per-asset carriage check unassignable (confirmed on all five non-reference layers),
  and tier-3 §0.1 stays unfillable (D5). Tier 4, the L0 instance, the pilots and the tracker
  comment are editable without any reopen and proceed regardless.

## D3 · Resolve the [TRANSFERS] contradiction (R71)

Tier 2 §1/§12.2 mark Presentation parity [TRANSFERS] ("a layer plan does not inherit it as its own
work"); tier 3 §5.4 test 4 requires it of a layer instance ("Presentation parity holds for the
layer's served surface"). P4 hit this on three layers (R94, R119, R140, R185).

- **Recommendation: reword tier-3 §5.4 test 4** to the P4 proposal: "run where the surface exists;
  where the owning plane is not built, record [TRANSFERS]-pending — never a pass, never a block."
- Cost of rewording T3: 2 h (R71) + transcription rows; keeps the transfer discipline intact; layer
  instances stop being asked to accept work they cannot execute.
- Cost of un-marking T2 §12.2 instead: every data-plane layer plan inherits a presentation-parity
  obligation against planes (retrieval, conversation) that are not built — an acceptance test that
  can only fail or be faked, i.e. an invented number in verdict form.

## D4 · Choose the ledger namespace (R78–R81)

Eleven measured hand↔census duplicate pairs (`consistency/T5_LEDGER_DRIFT.md` §A) coexist because
the ledger carries two row idioms and `emit_gaps` dedupes by id only.

- **Recommendation: option (a) — hand-style ids as the single namespace**, census becomes a
  detector reference attaching measurements by substance key (asset, criterion-family with alias
  resolution); fold the 11 pairs with `superseded_by`, ledger stays append-only. This is the T5
  proposal verbatim.
- Cost of (a): the census loses its self-contained emission idiom; the alias table
  (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`, `Carr.D1|D2|D3`≡
  `Carr.detector`, `Completeness.*`≡`Complete.*`) must be maintained (R79, 4 h).
- Cost of (b) census namespace only: the hand rows' richer `change`/detector text is lost or
  re-transcribed; first-registration of judgement rows (opportunities) has no home (R26 already
  rules the census never emits them).
- Cost of (c) keep both with cross-references: cheapest today, but the duplicate pairs recur on
  every layer — the 11 pairs become ~60 at six layers — and "which row do I close" stays ambiguous.

## D5 · Who authors the P-need/V-journey → layer necessity mapping (R85)

The campaign's largest finding: no tier maps P01–P24 / V01–V13 to layers by *necessity*, so tier-3
§0.1 is unfillable on every layer and 130 P4 invention rows trace here. The mapping is product
judgement — which needs genuinely cannot be answered without a layer — not measurement.

- **Recommendation: the native authors the necessity column** (a per-layer "necessary for P/V"
  table in tier 2 §3.1 or §13.3), with the campaign supplying the mechanical join evidence
  (DP-contract ↔ P/V mapping already present in tier 2); layer instances then narrow, never invent.
  Estimated native effort: a focused review pass over 24 + 13 rows; the register prices the
  documentation mechanics at 12 h (R85) plus transcription.
- Cost of native-authored: native time; the mapping becomes a sealed decision, so changing it later
  is a reopen.
- Cost of machine-derived (data-driven from the DP-contract graph): reproducible, but "necessary"
  is stronger than "reachable through the DAG" — the campaign's own derivation attempts produced
  involvement lists, not necessity sets (that is exactly what the 130 rows record). A derived table
  would still need a native sign-off to be honest.
- Also bound here: whether tier-3 §0.1's "necessary — not involved in, not contributes to" semantics
  stand (recommended: they stand; they are what makes §0.1 falsifiable) or relax to involvement.

## D6 · Align the Earn/Cost verdict scale with tier 4 (surfaces at R55)

Tier 4 §1 records "not instrumented" as a legal value; the census scores `rows_per_second` NULL as
FAIL on every asset (all 19 L1 assets FAIL — `derivations/L1_INVENTIONS.md` observations). Until
R34 lands there is no rate anywhere, so both Earn.build_record and Cost.baseline are constant-FAIL
and carry no signal (R55: they are one detector reading one column).

- **Recommendation: amend the census** — NULL rate reads PARTIAL ("not instrumented — R34 pending")
  rather than FAIL until R34 lands, then FAIL means what it says; and collapse Earn.build_record /
  Cost.baseline into one emitted row citing both gate names, since they cannot disagree (T1-FN4).
- Cost of census-side fix: ~2 h inside packet P4; verdicts become honest during the
  pre-instrumentation window.
- Cost of tier-4-side fix instead (declare NULL a failure by design): every asset of every layer
  carries two FAIL rows until the builder is instrumented — ledger noise that trains operators to
  ignore the gate.
- Cost of neither: after R34 lands the ambiguity resolves itself, but every ledger row emitted
  before then carries a FAIL that means "not yet instrumented", permanently ambiguous in the
  append-only record.

---

*Decisions D1–D3 gate BLOCKS_FREEZE rows (R71 directly; D1/D2 transitively). D4–D6 gate DEGRADES
and BLOCKS_LAYER work. Per the campaign brief §5 Phase 6.4, no packet waits on these: the plan
continues around each, and the packet that needs a ruling names it.*
