# S4 Pipeline Correctness & Door Parity — Stage S4 (ScopeTuple | ClarificationRequest → AcharyaPlan)

Investigated: 2026-08-28
Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` only. Native chart
`482012f1-…` never touched, never queried.

Scope note (per charter): "S4" here is **test-plan pipeline stage #4** — what happens to a
produced `ScopeTuple` (or a `ClarificationRequest` in its place) on the way to an `AcharyaPlan`
— not the campaign stream S4 this agent runs under. This is a distinct stage from the sibling
`.s4_scratch/S4_stage_S1_report.md` (which covers the classifier itself, `classifyScope()`).
This report covers what the classifier's OUTPUT does once produced: floor composition
(`compiled_floor_adapter.ts`, `vidhi/compiler.ts`), the completeness receipt, and the
clarification branch.

Code anchors:
- `platform/src/lib/vidhi/scope_classifier.ts` (`ScopeTupleSchema`, `classifyScope`) — the anchor
  named in the brief.
- `platform/src/lib/pipeline/compiled_floor_adapter.ts` (`classifierIntentToCompilerIntent`,
  `classifierTupleToCompilerTuple`, `compileFloorForPlan`) — the ACTUAL function
  `plan_stage.ts` calls.
- `platform/src/lib/vidhi/compiler.ts` (`bandsForDepth`, `compileFloorItems`, `compileContract`)
  — the one place depth has effect, by the module's own docstring (line 94-98).
- `platform/src/lib/pariprashna/pipeline/plan_stage.ts` (lines 244-286) — honest depth disclosure
  + floor adoption, the real production call site.
- `platform/src/lib/pipeline/completeness_wiring.ts` (`buildWebCompletenessReceipt`) +
  `platform/src/lib/pariprashna/pipeline/evidence_stage.ts` (lines 107-116) +
  `platform/src/lib/pariprashna/pipeline/receipt_stage.ts` (lines 61-75) — the reader-visible
  completeness grade.
- `platform/src/lib/pariprashna/honest_controls/flag.ts` — the flag gating the disclosure grade
  (default OFF).
- `platform/src/lib/pipeline/pipeline_planner.ts` (lines 359-424) — clarification branch +
  confirmation that `scope_tuple` is never shown to the LLM planner itself.

Evidence scripts (this lane): `platform/.s4_scratch/depth_effect.test.ts`,
`platform/.s4_scratch/failure_honesty_check.test.ts`, `platform/.s4_scratch/width_check.test.ts`
— all run via `npx vitest run <path>` from `platform/`, all passing, console output captured
below.

---

## Headline answer: does scope depth actually change downstream behavior?

**Yes, mechanically — but with a real, concrete gap in HOW it changes behavior, and this
report reproduces and extends the previously-filed GAP-8/PPR-16 finding (EDIR_V3 E-109/E-110/
E-112) with fresh, dated evidence rather than merely re-asserting it.**

Traced concretely with the classifier's own real `ScopeTuple` shape, through the real
production function `compileFloorForPlan` (the one `plan_stage.ts` line 277 actually calls):

- **`depth: 'standard'`** (the classifier's default — see §1) for `intent: 'yoga_identification'`,
  `domains: ['general']` compiles to **6** retrieval tool_calls.
- **`depth: 'deep'`**, identical tuple otherwise, compiles to **13** retrieval tool_calls — 7 more:
  `marsys://tool/L-TIMING/yoga_activation_by_dasha`, `marsys://tool/L1/get_dasha_lord_capability`,
  `marsys://tool/L2/query_mechanisms`, `marsys://tool/L4/query_prospective_ledger`,
  `marsys://tool/L5/mechanism_retrodiction_get`, `marsys://tool/L5/query_calibration`,
  `query_discoveries`.
- The reader-visible `completeness` grade (`receipt_stage.ts`, unconditional, always emitted)
  changes its denominator from `N/14` to `N/28` — a bare fact about how much of the chart was
  even attempted, visible on the wire regardless of any feature flag.

So depth is NOT inert — it demonstrably gates whether an entire machine-band tier of tools
(dasha activation, mechanism CGM reads, prospective-ledger, LEL retrodiction, tail-divergence,
statistical context — 14 primitives) is even eligible to run. **But** the gap this stage's crux
question (GAP-8/PPR-16) actually names is real too: (a) depth never reaches the LLM planner's
own prompt at all — it is a purely POST-hoc floor-injection input, so the planner's own
tool-selection reasoning is depth-blind; (b) the floor-injection only ADDS a tool when the
planner's own plan didn't already request it (`plan_stage.ts` line 279:
`if (!toolsAuthorized.includes(tc.tool_name))`), so the effect is conditional/probabilistic in
practice, not a guaranteed content difference; (c) the classifier's own INTENT selection
(`classifierIntentToCompilerIntent`, compiled_floor_adapter.ts:86-95) collapses `standard` and
`deep` to the identical floor FAMILY — only the internal band composition within that family
differs; and (d) the one artifact that would make deep-only synthesis behavior qualitatively
different in the actual reading prose — `llm_extension_note` / the E-7 INSIGHT MANDATE
(`compiler.ts` lines 300-314) — is **computed and then discarded**: `compileFloorForPlan`
(compiled_floor_adapter.ts:262-309) returns only `{compilerIntent, toolCalls, mappedPrimitives,
unmappedPrimitives, compileFailed}` — `contract.llm_extension_note` is never read. See Finding
F-S4-4 below; this is the mechanism-level explanation for why "deep dive" so often reads to a
native as no different from "standard" even though the floor composition genuinely differs.

---

## 1. Correctness

### The tuple's structure (confirmed by reading `scope_classifier.ts`)
`ScopeTupleSchema` (lines 71-79) = `{ intent, domains, width, depth, horizon, intervention,
entitlement }`. `depth` is one of `'shallow' | 'standard' | 'deep'` (line 58-59). Default is
`'standard'` (line 263) unless `DEPTH_DEEP`/`DEPTH_SHALLOW` regex fires (lines 180-181, 264-265)
— a purely keyword-gated default, contradicting the DEPTH-DEFAULT DOCTRINE the compiler's own
docstring states is BINDING (`compiler.ts` lines 100-106: "Deepdive is the default state of the
instrument... an unclassifiable question resolves to general_synthesis at `deepdive`, never
trimmed"). This doctrine lives in the MCP-side `scope_resolver.ts`
(`platform-mcp/src/resources/vidhi/scope_resolver.ts`), a module the WEB door (`scope_classifier.ts`)
does not import or call — confirmed by directory search; no cross-reference exists. This is the
exact mechanism EDIR E-112 already names ("the web classifier the Portal actually uses defaults
to `standard` — costing the entire 15-item machine band on an ordinary question"); this report's
`depth_effect.test.ts` test 2 independently reproduces it with an exact count (0 machine_band
items at `standard` vs a 14-item elevation tail at `deep`, `compiler.ts` output, run 2026-08-28).

### Does depth demonstrably change downstream behavior? Traced end to end.

1. **`classifierIntentToCompilerIntent`** (compiled_floor_adapter.ts:86-95) — depth is checked
   ONLY as step 4 of 5 (`if (tuple.depth === 'shallow') return 'retrieval_only'`); `standard` and
   `deep` are NOT distinguished at this step at all — both fall through to whatever intent/domain/
   width already resolved (usually `general_synthesis` or a domain deepdive). **Confirmed by test**
   (`depth_effect.test.ts` test 1): `classifierIntentToCompilerIntent(standard) ===
   classifierIntentToCompilerIntent(deep)` for an identical tuple.
2. **`DEPTH_MAP`** (compiled_floor_adapter.ts:97-101) maps the classifier's 3-value depth to the
   compiler's 3-value `ScopeDepth` (`retrieval`/`structure`/`deepdive`) — total, 1:1, no collapse
   here.
3. **`bandsForDepth`** (compiler.ts:93-117) — "the one place `depth` has effect" (verbatim
   docstring, line 94-95): `retrieval` → acharya floor, structural-category items only, no machine
   band; `structure` → full acharya floor, no machine band; `deepdive` → full acharya floor +
   machine band. **This is real and confirmed by test** (`depth_effect.test.ts` test 2):
   identical floor (18 items) at `standard` vs `deep`, but machine_band goes from 0 to 14 items.
4. **`compileFloorForPlan`** (compiled_floor_adapter.ts:262-309) — the function `plan_stage.ts`
   line 277 actually calls — maps the compiled contract's floor+machine_band primitives through
   `resolveLiveTool()` to web-executable retrieval tool names, and returns them as `toolCalls`.
   **Confirmed by test** (`depth_effect.test.ts` test 3): 6 tool_calls at `standard`, 13 at `deep`
   — see the headline section above for the exact tool list.
5. **`plan_stage.ts`** (lines 276-284) merges `compiledFloor.toolCalls` into `plan.tool_calls`,
   but ONLY for tool names not already in `toolsAuthorized` (line 279). This means the depth
   effect from step 4 is a **conditional addition**, not a guaranteed one — if the LLM planner's
   own JSON output already requested `marsys://tool/L5/query_calibration` for unrelated reasons,
   the `deep`-only floor injection is a no-op for that tool. The planner itself never sees
   `scope_tuple` at all (`pipeline_planner.ts` lines 416-424: the LLM `userPayload` carries only
   `native_id`, `manifest`, `history`, `query` — no scope_tuple/depth field), so the planner's own
   tool selection is depth-blind by construction; only the POST-hoc floor merge is depth-aware.
6. **`buildWebCompletenessReceipt`** (completeness_wiring.ts:75-153) recompiles the SAME contract
   from `plan.scope_tuple` independently (line 82) to build the reader-facing completeness grade.
   **Confirmed by test** (`depth_effect.test.ts` test 4): `floor_item_total` 14 (standard) vs 28
   (deep) for the identical tuple. `receipt_stage.ts` (lines 61-75) emits this UNCONDITIONALLY (no
   feature flag) as `em.grade({subject: 'completeness', grade: '\${served}/\${floor_item_total}'})`
   — so the depth-driven denominator change is real, always-on, reader-visible wire content, even
   though nothing else about it is gated by `PARIPRASHNA_HONEST_CONTROLS_ENABLED`.
7. **The one place depth SHOULD qualitatively change the synthesis prose** — `llm_extension_note`
   (compiler.ts:310-314, the E-7 INSIGHT MANDATE, present only at `deepdive`) — is computed inside
   `compileContract` but **discarded** by `compileFloorForPlan`, whose return shape
   (`CompiledFloorResult`, compiled_floor_adapter.ts:241-252) has no field for it. Grepped the
   whole `src/` tree for `llm_extension_note` consumers: only `floor_cache.ts` reads it, and
   `floor_cache.ts` itself has **zero production importers** (only its own test file imports it —
   confirmed by `grep -rn "from '@/lib/vidhi/floor_cache'"`). So the INSIGHT MANDATE that is
   supposed to be the actual qualitative difference of a deep-dive answer never reaches the
   synthesis prompt on the web/Paripraśna path at all.
8. **The reader-facing disclosure label** (`plan_stage.ts` lines 244-260,
   `READING_DEPTH_RECEIVED_LABEL`) — emits `em.grade({subject: 'reading_depth_received', ...})`
   derived honestly from `plan.scope_tuple.depth` (not from the composer's separate depth
   picker/`length_tier`, which is a DIFFERENT dimension entirely — confirmed by grep: `length_tier`
   comes from `body.length_tier` in `safety_gate.ts`, never from `scope_tuple.depth`). This grade
   is gated behind `isHonestControlsEnabled()`, which is **default OFF**
   (`honest_controls/flag.ts` line 23: `// Default OFF`) — so in production-default configuration,
   the one honest per-turn depth disclosure this lane built is dark.

### Failure-honesty (dimension 3) — the ClarificationRequest branch, traced

`pipeline_planner.ts` `callPipelinePlanner` (lines 359-408): `classifyScope(query)` runs BEFORE
any LLM call; `if (fallbackRecommended) { ...; return buildClarificationFromScope(classification)
}` — a hard early return, confirmed no silent fallthrough to a guessed plan. This branch is real
and correctly wired: ambiguous scope genuinely halts at a `ClarificationRequest`
(`buildClarificationFromScope`, lines 317-343), never silently defaults to a best-guess tuple that
then gets executed.

**However** — reproducing two already-filed defects on the ambiguity DETECTOR itself (not the
branch mechanics, which are sound):

- **E-104's dead disjunct, reproduced**: `fallback_recommended = !intentMatched || confidence <
  0.5` (scope_classifier.ts:299). Since `intentMatched` alone contributes `+0.6` to confidence
  (line 293) and nothing else can push confidence below that floor when `intentMatched` is true,
  `confidence < 0.5` can NEVER be true while `intentMatched` is true — the second disjunct is
  structurally unreachable. Confirmed by test (`failure_honesty_check.test.ts`,
  `'What is my current dasha period?'` → `confidence: 0.6`, well clear of 0.5, and every
  intent-matched query in the existing test suite clears 0.6 the same way).
- **E-105's false-positive clarifications, reproduced verbatim, same three queries, fresh run
  2026-08-28**: `'Will I get married?'`, `'Where is my Moon?'`, `'Am I going to be rich?'` each
  classify to `intent: 'unknown', confidence: 0, fallback_recommended: true` — every one of these
  is an ordinary, answerable astrological question that would be bounced back as a clarification
  instead of answered. Console evidence in `platform/.s4_scratch/failure_honesty_check.test.ts`
  run output.

---

## 2. Optimality

**No dedicated question→expected-scope-tuple accuracy corpus exists on the web door** (confirmed
by grep across `src/` and `tests/` for `expected_tuple`/`fixture`; the only hits are unrelated
corpus-dimension modules). The only classification-accuracy evidence is
`src/__tests__/lib/vidhi/scope_classifier.test.ts` (10 hand-written cases) — these assert the
classifier against its OWN regex tables, not an independent labeled set, so this is a
regression-safety suite, not a measured accuracy baseline. **Stating this honestly per the
brief's dimension-2 instruction: no measured accuracy baseline is possible for `depth`
specifically** — there is no fixture anywhere in the repo that pairs a question with an expected
`depth` value; the closest artifacts (`DEPTH_DEEP`/`DEPTH_SHALLOW` regexes) are the specification
being tested, not ground truth against real queries.

Adjacent corroboration of the sibling `width` dimension (not this lane's crux, but discovered
while tracing the same `classifierIntentToCompilerIntent` function, so recorded for completeness
and cross-reference to EDIR E-109): for `intent: 'domain_assessment', domains: ['wealth'],
depth: 'deep'`, `width: 'standard'` compiles **42** floor+machine_band items (`wealth_deepdive`),
while `width: 'broad'` on the SAME domain compiles only **8** (`panoramic_breadth`) — a
counter-intuitive "asking for MORE breadth compiles a SMALLER floor" result, reproducing E-109's
already-filed finding independently (`platform/.s4_scratch/width_check.test.ts`, run
2026-08-28).

---

## 3. Failure-honesty

Covered above under "Failure-honesty (dimension 3)". Summary: the BRANCH mechanics are correctly
wired (ambiguous scope → real `ClarificationRequest`, never a silent guessed default) — this part
of S4 is sound. The DETECTOR feeding that branch has two independently-reproduced defects
(E-104's dead disjunct, E-105's false-positive triggers on ordinary questions), both of which
were already filed and are corroborated here with fresh 2026-08-28 evidence rather than being new
findings.

---

## 4. Demonstrated-can-fail

Built and ran `platform/.s4_scratch/depth_effect.test.ts` — five tests, all passing, constructing
`ScopeTuple` pairs identical in every field except `depth`, run through the REAL production
functions (`classifierIntentToCompilerIntent`, `compileFloorForPlan`, `compileContract`,
`buildWebCompletenessReceipt`). All five demonstrate a real, measurable difference **at the
floor-composition / completeness-receipt layer**:

```
machine_band primitive_ids (deep only): [
  'dasha_spine_lord_capability','gochara_activation_read','gochara_forecast_read',
  'election_read','yoga_activation_scan','standing_predictions_read','lel_retrodiction',
  'contradiction_scan','tail_divergence_read','mechanism_read','statistical_context',
  'now_read','ahead_read','priority_read'
]
standard toolCalls (6): get_yoga_firings, marsys://tool/L1/chart_facts_query,
  marsys://tool/L1/get_positions, marsys://tool/L1/get_sensitive_degrees,
  marsys://tool/L1/get_strength, marsys://tool/L2/query_signals
deep toolCalls (13): [standard's 6] + marsys://tool/L-TIMING/yoga_activation_by_dasha,
  marsys://tool/L1/get_dasha_lord_capability, marsys://tool/L2/query_mechanisms,
  marsys://tool/L4/query_prospective_ledger, marsys://tool/L5/mechanism_retrodiction_get,
  marsys://tool/L5/query_calibration, query_discoveries
standard receipt coverage: { floor_item_total: 14, served: 0, empty: 14, dark: 0 }
deep receipt coverage:     { floor_item_total: 28, served: 0, empty: 25, dark: 3 }
```

This is a real, reproducible, code-level effect — depth is not inert. But it is NOT a proof that
a live reading's PROSE differs, because (a) the floor injection is conditional on the LLM
planner's own plan not already covering the same tool names, and (b) the qualitative signal that
was meant to differentiate deep-dive prose (`llm_extension_note` / INSIGHT MANDATE) never reaches
`compileFloorForPlan`'s output at all (Finding F-S4-4). The demonstrated-can-fail rung this lane
reached is **INTEGRATION** (real production functions, real inputs, real assertions, run and
captured) — not **LIVE** (an actual end-to-end turn on the synthetic chart showing two prose
outputs differ only by depth). A LIVE proof would require executing the full pariprashna route
twice against the synthetic chart with a supplied `scope_tuple` differing only in `depth`
(`prashna_ask`'s `scope_tuple` param, `suppliedScopeTuple` path, `pipeline_planner.ts` lines
375-383) and diffing the resulting envelopes — out of this lane's time budget but a concrete next
step if a LIVE rung is required.

---

## Findings (EDIR_V3-shaped; do not edit the register — proposed for the next EDIR pass)

### F-S4-1 — `compileFloorForPlan` discards `llm_extension_note`, so the E-7 INSIGHT MANDATE never reaches the web/Paripraśna synthesis prompt at any depth
- **Class**: DEFECT
- **Proposed severity**: S2 (proposed) — this is the mechanism-level explanation for why "deep
  dive" reads as no qualitatively different from "standard" to a native even on turns where the
  floor genuinely differs; it directly explains part of GAP-8's symptom.
- **Lens(es)**: correctness, demonstrated-can-fail
- **Pipeline stage**: S4 / ScopeTuple → floor compilation
- **Expected**: per `compiler.ts`'s own docstring (lines 20-32, 294-314), a `deepdive`-depth
  contract's `llm_extension_note` should reach the synthesis system prompt so the answerer is
  directed "past fact-gathering to the non-obvious" — the qualitative payoff of asking for more
  depth.
- **Observed** (2026-08-28, `depth_effect.test.ts` test 2 + static trace):
  `compileContract(...).llm_extension_note` differs correctly between `standard` and `deep`
  (confirmed: `deep` contains `'INSIGHT MANDATE'`, `standard` does not). But
  `compileFloorForPlan` (compiled_floor_adapter.ts:262-309), the function `plan_stage.ts` line
  277 calls, returns `CompiledFloorResult` (lines 241-252) which has no
  `llm_extension_note`/`adaptive_expansions` field — both are computed and thrown away. The only
  consumer of `llm_extension_note` anywhere in `src/` is `floor_cache.ts`, which itself has zero
  production importers (grep-confirmed).
- **Code anchor**: `platform/src/lib/pipeline/compiled_floor_adapter.ts:241-309` (return shape +
  function body); `platform/src/lib/vidhi/compiler.ts:375-384` (where the field is produced and
  discarded downstream).
- **Proposed fix class**: plumb `contract.llm_extension_note` (and optionally
  `adaptive_expansions`) through `CompiledFloorResult` into `plan.synthesis_guidance` in
  `plan_stage.ts`, so the depth-derived instruction actually reaches the synthesis system prompt.
- **Rung achieved**: INTEGRATION (real function, real inputs, assertion + console evidence).
- **Provenance**: this is a NEW finding, not previously in EDIR_V3, though it is the concrete
  mechanism behind the family of symptoms E-109/E-110/E-112 already describe at a higher level —
  reproduces/extends GAP-8/PPR-16.

### F-S4-2 — `scope_tuple` is never passed to the LLM planner; depth only affects a POST-hoc, conditional floor merge
- **Class**: DEFECT (or DOC, depending on whether this is intentional — not adjudicated here)
- **Proposed severity**: S3 (proposed)
- **Lens(es)**: correctness
- **Pipeline stage**: S4 / ScopeTuple consumption
- **Expected**: unclear from any doctrine document found whether the planner LLM is meant to see
  the depth signal directly (vs. only having its output floor-augmented afterward) — flagging as
  a genuine open question rather than asserting a specific expectation.
- **Observed** (2026-08-28, static trace): `pipeline_planner.ts` lines 416-424 build the LLM
  `userPayload` from `native_id`, `manifest`, `history`, `query` only — `classification`/
  `scopeTuple` is computed at line 364-365 but never included in what the LLM planner reads.
  Depth's only effect on the actual executed tool set is the conditional merge at `plan_stage.ts`
  line 279 (`if (!toolsAuthorized.includes(tc.tool_name))`), which is a no-op for any tool the
  LLM planner already independently requested.
- **Code anchor**: `platform/src/lib/pipeline/pipeline_planner.ts:416-424`;
  `platform/src/lib/pariprashna/pipeline/plan_stage.ts:276-284`.
- **Proposed fix class**: either (a) confirm this is intentional (floor = deterministic safety
  net, planner = independent judgment) and document it as such, or (b) surface `scope_tuple` in
  the planner's own prompt context so depth informs its OWN tool selection, not only the
  after-the-fact floor.
- **Rung achieved**: STATIC (code reading, no test needed — the payload shape is directly
  inspectable).
- **Provenance**: NEW finding, adjacent to GAP-8/PPR-16 but not previously filed under that name
  in EDIR_V3 as far as this lane found.

### F-S4-3 — the reader-facing `reading_depth_received` disclosure grade ships dark (flag default OFF)
- **Class**: DEFECT (disclosure gap)
- **Proposed severity**: S3 (proposed) — reader-visible but non-blocking; the underlying floor
  effect (F-S4-1/completeness grade) is real regardless of this flag.
- **Lens(es)**: correctness, failure-honesty
- **Pipeline stage**: S4 / ScopeTuple disclosure
- **Expected**: per the lane's own header comment (`plan_stage.ts` lines 44-55), the honest depth
  disclosure exists specifically to close PPR-09/16 ("What the reader is TOLD they got should be
  what the planner's own `scope_tuple` actually resolved to").
- **Observed** (2026-08-28): `isHonestControlsEnabled()` reads `PARIPRASHNA_HONEST_CONTROLS_ENABLED`,
  documented as `// Default OFF` (`honest_controls/flag.ts` lines 22-23,
  `feature_flags.ts` line 312: "Default false: ships dark"). In default configuration, the grade
  this lane exists to emit is never sent.
- **Code anchor**: `platform/src/lib/pariprashna/honest_controls/flag.ts:22-27`;
  `platform/src/lib/pariprashna/pipeline/plan_stage.ts:253-260`.
- **Proposed fix class**: not necessarily a bug (may be an intentional staged rollout) — flag for
  triage to confirm current production flag state and whether flip is scheduled.
- **Rung achieved**: STATIC.
- **Provenance**: adjacent to GAP-8/PPR-16 (this is the disclosure half of the same lane); not
  previously filed under this specific angle (flag-off-ness) as far as this lane found — E-110
  already covers the DIFFERENT-INPUTS mismatch; this finding is about the flag gating the fix
  being off by default.

### F-S4-4 (corroboration, not new) — `standard` depth (the classifier's real-world default) permanently excludes the entire machine_band tier
- **Class**: DEFECT
- **Proposed severity**: S2 (per EDIR E-112's existing proposal — corroborated, not re-proposed)
- **Lens(es)**: correctness, demonstrated-can-fail
- **Pipeline stage**: S4 / floor compilation
- **Expected**: per `compiler.ts`'s own BINDING doctrine comment (lines 100-106, "Deepdive is the
  default state of the instrument"), depth should default to deep, not standard.
- **Observed** (2026-08-28, fresh reproduction): `scope_classifier.ts` line 263 defaults
  `depth: Depth = 'standard'`; the MCP-side doctrine module implementing the deepdive-default LAW
  (`platform-mcp/src/resources/vidhi/scope_resolver.ts`) is never imported by the web door.
  Confirmed via `bandsForDepth`/`compileContract`: `standard` compiles 0 machine_band items,
  `deep` compiles 14, for an identical intent/domain/width/horizon/intervention/entitlement tuple.
- **Code anchor**: `platform/src/lib/vidhi/scope_classifier.ts:262-265`;
  `platform/src/lib/vidhi/compiler.ts:93-117`.
- **Proposed fix class**: see E-112's own proposed close rung (REPLAY — both doors resolve the
  same depth for the same class of question).
- **Rung achieved**: INTEGRATION (this lane's independent reproduction, `depth_effect.test.ts`
  test 2/3, 2026-08-28).
- **Provenance**: **this reproduces/confirms EDIR_V3 E-112 (and the related E-109/E-110) —
  GAP-8/PPR-16.** Not a new finding; recorded here as fresh dated corroborating evidence with
  exact tool-name-level detail (the prior register entries state the effect at a summary level
  only; this lane adds the concrete 6-vs-13-toolCall and 14-vs-28-floor-item numbers).

### F-S4-5 (corroboration, not new) — `fallback_recommended`'s `confidence < 0.5` disjunct is dead code; three ordinary questions false-positive into clarification
- **Class**: DEFECT
- **Proposed severity**: per EDIR E-104 (S3) / E-105 (S2) — corroborated, not re-proposed.
- **Lens(es)**: failure-honesty
- **Pipeline stage**: S4 (upstream classifier feeding the S4 branch)
- **Observed** (2026-08-28, fresh reproduction, `failure_honesty_check.test.ts`): confirmed by
  direct arithmetic (`intentMatched` alone contributes 0.6, the disjunct's threshold is 0.5) and
  by direct classifier calls: `'Will I get married?'`, `'Where is my Moon?'`, `'Am I going to be
  rich?'` all resolve `intent: 'unknown', confidence: 0, fallback_recommended: true` — each would
  be bounced to `ClarificationRequest` instead of answered.
- **Code anchor**: `platform/src/lib/vidhi/scope_classifier.ts:289-299`.
- **Rung achieved**: INTEGRATION (fresh reproduction with the exact E-105 query set).
- **Provenance**: **reproduces/confirms EDIR_V3 E-104 and E-105** with a fresh dated run.

---

## Existing-test regression check (sanity, not a new finding)

Ran the full existing suites this stage touches — all pass, no regressions introduced by this
investigation (read-only; no production file was modified):

```
platform$ npx vitest run src/__tests__/lib/vidhi/scope_classifier.test.ts \
  src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts \
  src/lib/vidhi/__tests__/compiler.test.ts
 Test Files  3 passed (3)
      Tests  49 passed (49)
```
