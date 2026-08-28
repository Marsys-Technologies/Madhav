# S4 Pipeline Correctness & Door Parity — Stage S11: TurnProvenance + AcharyaReadingReceipt

Lane: S4 (Pipeline Correctness & Door Parity), stage S11 ONLY.
Chart under test: synthetic `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Native's real chart never touched.
Code anchors: `platform/src/lib/pariprashna/receipt/{assemble,schema,validate,hash,store}.ts`,
`platform/src/lib/pariprashna/pipeline/{persistence_stage.ts,receipt_stage.ts}`,
`platform/src/lib/pariprashna/provenance/stamp.ts`,
`platform/src/lib/pariprashna/interpretation/worker.ts` (interpretation_sets sub-field),
`platform/src/lib/pariprashna/confidence/{type_claim,activation_gate}.ts` (confidence_typing sub-field).

---

## 1. §N.8 field-by-field audit (CLAUDE.md §N.8 Earned-Signal Principle)

Test: "what code path would have to run — and fail — for this signal to correctly read
false/unavailable? If no such path exists, or it checks a proxy instead of the claim, the signal
is null-worthy, not earned."

| Field | Verdict | How checked |
|---|---|---|
| `receipt_schema_version`, `turn_id`, `conversation_id`, `chart_id`, `generated_at` | EARNED | Verbatim caller inputs / `now.toISOString()`; no derivation. |
| `coverage.*` | EARNED | Verbatim pass-through of `WebCompletenessReceipt.coverage` (real object from `buildWebCompletenessReceipt`); `unavailable` only when that receipt genuinely didn't build (`assemble.ts:154-177`). Its own upstream correctness is a different lane's scope. |
| `facts_consumed` | EARNED | Direct map of `citationsFound` (`DetectedCitationRow[]`), a detector that always runs deterministically; empty array is an honest zero, never null. |
| `derivation_chains[].pass_id` | EARNED | Regex-parsed from the real block id (`blk-<pass>-<n>`); null on genuine parse miss, never guessed. |
| `derivation_chains[].fact_refs` | EARNED | Bracket-exact-substring match of `[${index}]` against the block's own committed text on the rewriter path, or a regex re-scan on the legacy path; verified non-false-positive across adjacent indices (`[1]` vs `[10]`) by an existing repo test (`assemble.test.ts:181`). |
| `cross_domain.*` | EARNED | Verbatim `plan.domains`; `unavailable` only when the planner genuinely never populated it. |
| `evidence_grades.*` | EARNED | Grade tally over `resolvedCitations` (only when the live rewriter ran) + `hallucination_count` passed through from `TurnCitationStream.hallucinationCount`; honestly `unavailable` when the rewriter flag was off (regex fallback carries no per-citation grade). |
| `honest_gaps.*` | EARNED | Direct map of `WebCompletenessReceipt.empty[]`/`.dark[]`, each already carrying its own real reason; **scope caveat** — see Failure-honesty §3 below: this can only report gaps the *floor-item* completeness model already knows about, not an uncited *prose* claim. |
| `safety_decision.*` | EARNED | Verbatim `SafetyDecision` fields; `audit_written` specifically traced to `safety/gate.ts:300` (`const written = await appendSafetyDecision(db, decision)`) — a real DB-write-result boolean, not an assumed-true flag. `enforced:false` correctly modeled as MEASURED, not unavailable (a real, distinct fact). |
| `calibration_disclosure.consulted` / `.consulted_tool_names` | EARNED (turn-scoped, disclosed) | Checks `validToolResults[].tool_name` membership in `CALIBRATION_BEARING_TOOL_NAMES`. Confirmed the anti-laundering path in `tool_name_bridge.ts:293-303` converts any handler-returned `is_error:true` into a **thrown** error, which `evidence_stage.ts`'s per-tool `try/catch` turns into `null` and excludes from `validToolResults` — so a *failed* calibration query cannot masquerade as "consulted". Caveat: this is a whole-turn "was the tool called and did it succeed" check, not a per-citation "does THIS claim rest on calibration data" check — that turn-vs-claim scoping gap is explicitly self-disclosed in `type_claim.ts`'s own doc comment, not hidden. |
| `calibration_disclosure.disclosure_note` | EARNED | One of two fixed, doctrinally-sourced strings selected by the above real boolean — never a computed claim about specific numbers. |
| `prose_binding.blocks[].block_id/role/char_count` | EARNED | Verbatim from `committedBlocks`. |
| `prose_binding.blocks[].semantic_kind/semantic_role` | EARNED | Reused (not re-derived) from `OpenBlock.semantic`, itself set only when G2-A semantic-block classification ran; null otherwise. |
| `prose_binding.accumulated_text_sha256/char_count` | EARNED | Real `sha256(accumulatedText)` / `.length`, computed fresh, not carried from elsewhere. |
| `provenance.*` | EARNED | Verbatim wrap of `TurnProvenanceStamp` (`provenance/stamp.ts`), itself wrapping the live `computeCurrentPinValues` (`build_id` from `build_runs`, `priors_version` from a live constant, `ranking_config` a live composite-ranker constant, `now_context_date` genuine wall-clock). `formula_versions.salience_formula_ver` is an honestly-disclosed `null` placeholder (no such column exists yet) — correctly modeled as a value, not a fabricated string. **Note:** `provenance/stamp.ts` has zero dedicated unit tests in the repo (no `provenance/__tests__/` directory) — its correctness rests entirely on `assemble.test.ts`'s one pass-through assertion plus the reused `retrieval/provenance_stamp.ts` module's own tests. Traced the call chain (`persistence_stage.ts:245` → `receipt_stage.ts:38-59`) and confirmed `getLastTurnStamp` runs *before* the current turn's DB write, so it genuinely reads the prior turn, not a self-referential read — no ordering bug found, but flagging the coverage gap. |
| `interpretation_sets.status` (unavailable path) | EARNED | Honest `unavailable` default with a real reason when the flag was off or the caller supplied nothing. |
| `interpretation_sets.sets[].status: 'waived'` | EARNED | Every waiver traces to a real failure mode (`coerceEntry` returning null, the LLM call throwing twice, a missing judgment_id) — never a fabricated waiver. |
| `interpretation_sets.sets[].status: 'generated'` | **UNEARNED-SUSPECT (confirmed live)** | See §4(b) below. The status is meant to certify ">=3 genuinely DISTINCT candidate readings" (the system prompt's own words, `worker.ts:162-165`). The only structural guard is `hasNearDuplicateCandidates`, a lexical token-overlap heuristic (`worker.ts:279-299`) whose own doc comment concedes it is a "floor-raise... not a semantic guarantee" that "cannot guarantee every near-duplicate candidate set is caught." A live test (below) constructed three candidates that are pure synonym-paraphrases of one identical reading and confirmed they pass the real `generateInterpretationSets` pipeline as `status: 'generated'` — i.e. the field reads as if genuine distinctness were verified when the actual claim (semantic distinctness) has no detector behind it at all, only a disclosed proxy (lexical overlap). This is the same defect *class* §N.8 exists to catch, though — credit where due — the code's own comments already disclose the proxy is imperfect; nothing here is silently claimed as complete. |
| `interpretation_sets.sets[].selected_rationale/falsifier` (generated) | UNEARNED-SUSPECT (same root cause) | Guarded only by non-empty + `isVacuousFalsifier`'s denylist/min-word-count (`worker.ts:236-261`), also self-disclosed as a structural, non-semantic floor-raise. A fluent-but-circular falsifier that isn't one of the 5 denylisted phrases and clears 5 words would pass. |
| `interpretation_sets.detected_count/covered_count/truncated_count/waived_count` | EARNED | Arithmetic invariants enforced structurally by `validate.ts` V6/V7 (covered+truncated=detected, sets.length=covered_count, actual waived count matches). |
| `confidence_typing.entries[].confidence_type` | EARNED | Priority-ordered real detectors per `type_claim.ts:116-133` (L1 layer tag → deterministic_fact; calibration consulted AND gate open → empirically_calibrated; classical tool consulted → classical_prior; L2.5 tag → structural_prior; else → unresolved, the honest fallback). `validate.ts` V8b additionally enforces as code that `empirically_calibrated` cannot appear unless `activation_gate.gate_open === true` — a receipt violating this fails validation and is never persisted. |
| `confidence_typing.activation_gate.*` | EARNED | `evaluateEmpiricalCalibrationGate` never returns `gate_open:true` on a null/sub-threshold sample size (`activation_gate.ts:88-104`); threshold is honestly disclosed as a placeholder (`threshold_is_placeholder:true`), not presented as a sourced doctrine value. |
| `confidence_typing.precision_flags[]` | EARNED | T-8 precision scan reads real parsed numeric fields from the actual tool payload shapes (`extractCalibrationPrecisionCandidates`), each paired with its own row-level sample size, never a borrowed/aggregate one. |
| `receipt_hash` | EARNED | `computeReceiptHash` = sha256 of key-sorted canonical JSON over every other field; `validate.ts` V1 recomputes it and fails the receipt if it disagrees. Confirmed stable across two full `assembleAcharyaReadingReceipt` calls on identical logical input (§4a). |

**Summary:** 27 of 29 audited field-groups are EARNED (several with an honestly self-disclosed
scope caveat, not a hidden gap). Two field-groups — `interpretation_sets.sets[].status:
'generated'` and its paired `selected_rationale`/`falsifier` — are UNEARNED-SUSPECT and were
**confirmed live** (not just argued) to pass a semantically-non-distinct candidate set through as
if distinctness were verified. Zero fields were COULD-NOT-DETERMINE; every field traced to a
concrete source in this worktree.

---

## 2. Optimality — receipt-assembly latency

`assembleAcharyaReadingReceipt` is a pure, synchronous, in-memory function (no I/O — the docblock
at `assemble.ts:6-9` states this explicitly and the trace confirms it: every argument is already
computed by the caller). Instrumented directly with `process.hrtime.bigint()`, N=20 runs (+3
untimed warm-up runs) on a realistic-size input: 6 committed prose blocks, 12 citations
found/resolved (mixed L1/L2.5), 2 calibration-bearing tool bundles with real payload shapes,
`typedConfidenceEnabled: true`.

```
p50 = 0.046 ms
p95 = 0.068 ms
max = 0.068 ms
```

Assembly cost is negligible relative to the pipeline's DB/LLM-bound stages. No optimization
finding here — this is not a bottleneck.

---

## 3. Failure-honesty — prose ↔ receipt grounding agreement

Constructed a synthesized turn with two committed prose blocks:
1. An **uncited** claim: *"Saturn's Mahadasha begins in early 2027 and will bring five years of
   career stability and a confirmed promotion by 2029."* — a specific, falsifiable, time-indexed
   predictive assertion with no `[n]` citation marker.
2. A cited claim referencing `[1]` (a real resolved L1 citation).

Ran the real `assembleAcharyaReadingReceipt` (rewriter path, `citationRewriteEnabled: true`) over
this input. Result:

- `facts_consumed` = exactly 1 entry (the cited claim only).
- `derivation_chains` entry for the uncited block: `fact_refs: []`.
- `honest_gaps.gaps` = only the two floor-items the fixture's `WebCompletenessReceipt` already
  knew about (`p3` empty, `p4` dark) — **no entry for the uncited prose claim**, because
  `honest_gaps` is sourced from the floor-item completeness model, which has no visibility into
  prose content at all.
- `validateAcharyaReadingReceipt` reports **zero violations** for this receipt.

**Concrete finding:** the receipt is honest about what it captured (§N.5: never restates,
correctly empty rather than fabricated) but provides **no mechanism at all** to flag an
un-cited, substantive, time-indexed predictive claim in rendered prose. A reader (or auditor)
inspecting only the receipt would see a clean, fully-coherent, validation-passing document and
have no way to know the turn's prose asserted a specific 2027–2029 career-timing prediction that
the receipt's grounding inventory is entirely silent about. This is a genuine scope gap in what
"prose_binding" + "facts_consumed" together imply they cover (binding to the *exact text*, but not
auditing *coverage* of that text's claims) versus what an acharya-grade audit trail would need.

---

## 4. Demonstrated-can-fail

### 4(a) Hash stability — CONFIRMED (integration rung, vitest)

Called `assembleAcharyaReadingReceipt(args)` twice with byte-identical logical input (same fixed
injected `now`, same committed blocks/citations/tool bundles/provenance stamp):

```
r1.receipt_hash === r2.receipt_hash → true
fa9c9b74b1e82efdb1e124afed092990f91225218a1c3845afcb3670f33b7c32
```

Also confirmed sensitivity (a genuinely different logical input changes the hash) — proving the
hash is neither a constant nor accidentally order-dependent. Note the pre-existing repo test suite
(`hash.test.ts`) already covers key-order independence and content-sensitivity at the
`computeReceiptHash` function level, but had no test calling `assembleAcharyaReadingReceipt` twice
end-to-end — that gap is now closed by this run (test not retained in the tree per lane scope; see
`.s4_scratch/S4_S11_scratch_hash_latency_honesty.test.ts.txt` for the exact reproducer).

### 4(b) UNEARNED-SUSPECT field forced FALSE, still reads TRUE — CONFIRMED (integration rung, vitest)

Target: `interpretation_sets.sets[].status: 'generated'`, which is meant to certify ">=3 genuinely
DISTINCT candidate readings" per `worker.ts`'s own system prompt.

Constructed 3 candidates that are pure synonym-paraphrases of **one** identical underlying reading
("career growth → a position of authority → via sustained hard work"), using near-fully disjoint
vocabulary so the real `hasNearDuplicateCandidates` lexical-overlap check (threshold 0.8, Jaccard-
like ratio over the smaller token set) stays well below its trigger:

- C1: *"The native will achieve significant career growth and rise into a leadership position
  through consistent hard work."*
- C2: *"Professional advancement is likely, with promotion to a position of authority resulting
  from sustained diligent effort."*
- C3: *"Expect vocational success: the individual will attain a managerial role thanks to
  persistent industrious dedication."*

Fed this payload through the **real, unmocked** `generateInterpretationSets` (only the network-call
seam `InterpretationLlmCaller` was injected — `coerceEntry`, `hasNearDuplicateCandidates`,
`isVacuousFalsifier`, and every structural check ran for real). Result:

```
entry.status = 'generated'   (claims genuine 3-way distinctness)
entry.candidates.length = 3
```

The underlying condition the status claims to certify (genuine interpretive distinctness) is FALSE
by construction — all three "candidates" assert the identical claim — yet the field reads exactly
as it would for a genuinely distinct 3-candidate set, because no detector for semantic distinctness
exists; only the disclosed lexical-overlap proxy does, and it does not catch synonym substitution.
This is a live, reproducible instance of the §N.8 defect class. Reproducer saved at
`.s4_scratch/S4_S11_scratch_ndup_defect_demo.test.ts.txt`.

---

## EDIR_V3 candidate entries (not filed — for the coordinating agent)

### Finding S11-1
- **Title:** `interpretation_sets[].status:'generated'` claims genuine candidate distinctness on a
  lexical-overlap proxy that does not detect synonym-paraphrased near-duplicates
- **Class:** §N.8 Earned-Signal Principle violation (proxy detector standing in for the claimed
  condition), partially self-disclosed in code comments but not surfaced to the receipt's actual
  claim consumers
- **Proposed severity (proposed):** S2 — not safety/grounding-critical on its own (interpretation
  sets are an additive PPR-02 extension, not the core L1-fact grounding chain), but it is a
  confirmed instance of a receipt field asserting more certainty than its detector earns, in a
  field whose entire purpose is auditable epistemic honesty.
- **Lens(es):** Correctness, Demonstrated-can-fail
- **Pipeline stage:** S11 (AcharyaReadingReceipt, `interpretation_sets` sub-object)
- **Expected vs observed:** Expected — `status:'generated'` implies the system verified >=3
  genuinely distinct interpretive conclusions (per the worker's own system prompt). Observed
  (2026-08-28, integration test, synthetic chart `1c826d5a-...`) — three synonym-paraphrased
  restatements of one claim pass through as `status:'generated'` with no flag or degraded
  confidence.
- **Code anchor:** `platform/src/lib/pariprashna/interpretation/worker.ts:279-299`
  (`hasNearDuplicateCandidates`/`overlapRatio`), `worker.ts:322-356` (`coerceEntry`)
- **Proposed fix class:** either (a) strengthen the distinctness check with an embedding-similarity
  comparison instead of raw token overlap (the codebase already has embedding infrastructure
  elsewhere in L5), or (b) if a full semantic check is out of scope, surface the proxy's own
  disclosed limitation AS A RECEIPT FIELD (e.g. a `distinctness_check: 'lexical_only'` tag) so a
  downstream consumer can see the certification is partial rather than reading `'generated'` as
  fully earned.
- **Rung achieved:** INTEGRATION (vitest, real `generateInterpretationSets`, only the LLM network
  seam mocked)

### Finding S11-2
- **Title:** `AcharyaReadingReceipt` has no mechanism to flag a substantive, uncited, time-indexed
  predictive claim in rendered prose
- **Class:** Failure-honesty / scope gap (not a fabrication — an honest absence with no signal
  pointing at it)
- **Proposed severity (proposed):** S2, escalating to S1 if this pattern occurs in production
  predictive-timing claims (career/health/marriage timing assertions are exactly the
  safety/calibration-adjacent class CLAUDE.md's Ethical Framework cares about) — recommend the
  coordinating agent check production receipts for real instances before finalizing severity.
- **Lens(es):** Failure-honesty, Correctness
- **Pipeline stage:** S11 (`facts_consumed`, `derivation_chains`, `honest_gaps`)
- **Expected vs observed:** Expected — an acharya-grade audit receipt should let an auditor
  distinguish "every substantive claim in this prose has grounding" from "this prose asserts things
  the receipt is silent about." Observed (2026-08-28, integration test) — an uncited claim asserting
  a specific 2027 Mahadasha onset and a 2029 promotion produces zero footprint anywhere in the
  receipt, and `validateAcharyaReadingReceipt` reports the receipt fully coherent (0 violations).
- **Code anchor:** `platform/src/lib/pariprashna/receipt/assemble.ts:510-536`
  (`factRefsForBlock`/`buildFactsConsumed`), `assemble.ts:217-234` (`buildHonestGaps`)
- **Proposed fix class:** add an uncited-substantive-claim detector (even a coarse one — e.g. flag
  a committed prose block whose `fact_refs` is empty but whose text matches a
  numeric/date/predictive-language heuristic) surfaced as a new honest field (e.g.
  `uncited_claim_blocks: string[]`) rather than silence; this is squarely the kind of "an honest
  null beats an invented judgment... but a genuine gap still needs a flag" case CLAUDE.md §N.7/§N.8
  already establish doctrine for elsewhere in this codebase.
- **Rung achieved:** INTEGRATION (vitest, real `assembleAcharyaReadingReceipt` +
  `validateAcharyaReadingReceipt`)

### Note (not filed as a finding — informational)
`platform/src/lib/pariprashna/provenance/stamp.ts` (the "TurnProvenance" half of S11) has no
dedicated `__tests__/` coverage in the repo; correctness rests on one pass-through assertion in
`receipt/__tests__/assemble.test.ts` plus the reused `retrieval/provenance_stamp.ts` module's own
tests. No live defect found — call-ordering was traced and confirmed correct (`getLastTurnStamp`
genuinely reads the prior turn, not a self-read) — but the coverage gap itself is worth the
coordinating agent's awareness for prioritizing future hardening passes.

---

## Reproducers

Both scratch test files (removed from the tracked worktree after the run, per lane scope) are
preserved for reproducibility at:
- `.s4_scratch/S4_S11_scratch_hash_latency_honesty.test.ts.txt` (items 2, 3, 4a)
- `.s4_scratch/S4_S11_scratch_ndup_defect_demo.test.ts.txt` (item 4b)

To re-run: copy either file into `platform/src/lib/pariprashna/{receipt,interpretation}/__tests__/`
with a `.test.ts` extension and run `npx vitest run <path>` from `platform/`.
