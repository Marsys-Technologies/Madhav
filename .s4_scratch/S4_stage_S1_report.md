# S4 Pipeline Correctness & Door Parity — Stage S1 (NormalizedQuery → intent/scope classification)

Investigated: 2026-08-28
Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` only (referenced as a
classifier input for entitlement logic; never queried live). Native chart `482012f1-…` never
touched.

Code anchors:
- MCP door: `platform-mcp/src/tools/intent_scope_classifier.ts` (+ `intent_scope_classifier.test.ts`)
- Portal door: `platform/src/lib/vidhi/scope_classifier.ts` (+ `platform/src/__tests__/lib/vidhi/scope_classifier.test.ts`)
- Real production consumer of S1 for the unified `prashna_ask` flow (BOTH doors):
  `platform/src/lib/pipeline/pipeline_planner.ts` (`callPipelinePlanner`), called from
  `platform/src/app/api/chat/consult/route.ts` (Portal chat) AND
  `platform/src/app/api/mcp/prashna_ask/route.ts` (MCP `prashna_ask` tool) — **both import the
  same `@/lib/pipeline/pipeline_planner` and `@/lib/vidhi/scope_classifier`**, so for the
  `prashna_ask` flow specifically there is no divergence: it's literally the same code.
  Divergence risk is isolated to the **standalone MCP tools** `intent_classify`
  (`platform-mcp/src/tools/l0_brahmagyan.ts`) and `util_intent_classify`
  (`platform-mcp/src/tools/register_p1_aliases.ts`), whose output a caller can pass back into
  `prashna_ask`'s `scope_tuple` hint param (validated by Portal's `ScopeTupleSchema`, then
  **trusted verbatim** — see `pipeline_planner.ts` lines 368–383, the W6.1 "supplied scope tuple
  bypasses clarification" behavior).

---

## 1. Correctness

The MCP classifier (`intent_scope_classifier.ts`) implements deterministic regex-rule
classification for intent (11 intents + unknown), domains (10 life areas + general), and 5
secondary dimensions (width/depth/horizon/intervention/entitlement), plus an Ω4 "earned-narrow"
routing layer (`detectNarrow`) that defaults every query to `depth:deep, width:broad` unless a
query positively earns a pinpoint `narrow` route (single entity + single attribute + no
evaluative verb/domain word/analytical topic/breadth/multi-clause). Portal's `scope_classifier.ts`
implements the same intent/domain rule tables but an **older, pre-Ω4** width/depth model
(keyword-only `WIDTH_BROAD`/`WIDTH_NARROW`/`DEPTH_DEEP`/`DEPTH_SHALLOW`, default `standard`/`standard`)
and lacks the Ω4 apparatus entirely (no `route`, `narrow_confidence`, `depth_available` fields).

**Fixture/corpus honesty**: there is no dedicated classification-accuracy corpus file. The only
accuracy evidence is the unit test suites themselves — MCP: 37 tests (`intent_scope_classifier.test.ts`),
Portal: 10 tests (`scope_classifier.test.ts`). Both are thin (well under 50 labeled examples
combined) and both are asserting the classifier against itself (the same regex tables), so they
prove internal consistency / regression-safety, not measured accuracy against a held-out labeled
set. This is a genuine BASELINE gap, not a defect.

**Existing tests — both pass**:

```
platform-mcp$ npx vitest run src/tools/intent_scope_classifier.test.ts
 ✓ src/tools/intent_scope_classifier.test.ts (37 tests) 9ms
 Test Files  1 passed (1)
      Tests  37 passed (37)

platform$ npx vitest run src/__tests__/lib/vidhi/scope_classifier.test.ts
 Test Files  1 passed (1)
      Tests  10 passed (10)
```

**Ambiguity → ClarificationRequest, not a guessed tuple**: confirmed at the production-consumer
level. `pipeline_planner.ts` (`callPipelinePlanner`, lines 359–408) runs `classifyScope(query)`
BEFORE any LLM call; if `classification.fallback_recommended` is true, it returns
`buildClarificationFromScope(classification)` — a real `ClarificationRequest` (`outcome:
'clarification_needed'`) — and **never** proceeds to plan/execute on a guessed tuple. This is
consumed identically by both `/api/chat/consult` (line 563) and `/api/mcp/prashna_ask` (line 413,
417). One caveat: a caller-supplied `scope_tuple` param with a resolved intent (`suppliedScopeTuple`)
**bypasses** this clarification gate unconditionally (`fallbackRecommended = false` at line 382) —
this is an intentional W6.1 design (explicit out-of-band scope trusted over the text guess), but it
means a caller who pre-classifies via the divergent MCP `intent_classify` tool and feeds the result
back can force a route the Portal classifier itself would have flagged for clarification. See §5.

**Adversarial phrasing that should NOT auto-resolve** — tested directly against both classifiers:
`'tell me about it'`, `'what about the thing we discussed'`, `'is it good or bad'`, `'more please'`,
`'yes'`, `'go on'`. All six resolve to `intent: 'unknown'`, `confidence: 0`,
`fallback_recommended: true` on BOTH doors — no false-confident guess. Evidence in
`.s4_scratch/s1_run_output.txt` ("ADVERSARIAL AMBIGUITY PROBE" section).

---

## 2. Optimality (measured baseline)

| Metric | Value | How measured |
|---|---|---|
| MCP classifier latency (mean) | 0.0047 ms | `performance.now()` around 200 direct calls of `classifyScope` (`intent_scope_classifier.ts`), 5-call warmup, cycling through the 19-query parity set. Script: `.s4_scratch/s1_parity_and_bench.ts`. |
| MCP classifier latency p50 | 0.0044 ms | same run |
| MCP classifier latency p95 | 0.0082 ms | same run |
| MCP classifier latency max | 0.0139 ms | same run |
| Portal classifier latency (mean) | 0.0032 ms | same methodology, `scope_classifier.ts` |
| Portal classifier latency p50 | 0.0028 ms | same run |
| Portal classifier latency p95 | 0.0054 ms | same run |
| Portal classifier latency max | 0.0106 ms | same run |
| Classification-accuracy corpus size | 37 (MCP) / 10 (Portal) hand-written unit-test cases, self-referential (asserted against the classifier's own regex tables, not an independent labeled set) | count of `it(...)` cases in each `.test.ts` file |
| Clarification-trigger precision — positive (should ask) | 5/5 correct, both doors | `.s4_scratch/s1_parity_and_bench.ts` "CLARIFICATION-TRIGGER PRECISION" section, run against 5 genuinely ambiguous queries |
| Clarification-trigger precision — negative (should NOT ask) | 5/5 correct, both doors | same script, 5 clearly-classifiable queries |
| Cross-door parity divergence rate | 19/19 (100%) of the 19 representative queries diverged on at least one scope_tuple field | `.s4_scratch/s1_parity_and_bench.ts` "PARITY CHECK" section |

Both classifiers are effectively free (sub-hundredth-of-a-millisecond, pure regex over a short
string) — latency is not a real risk for this stage on either door. The clarification-precision
numbers are clean (10/10 both directions) but the fixture set (10 queries) is small — this is an
honest baseline, not a comprehensive accuracy claim.

The standout finding is the **100% parity divergence rate** — see §5.

---

## 3. Failure-honesty

Forced a degraded/low-confidence classification (empty query, gibberish, pronoun-only phrasing)
against both classifiers. Both surface it visibly:

- `confidence: 0`
- `fallback_recommended: true`
- `scope_tuple.intent: 'unknown'`

Exact code path (MCP, `intent_scope_classifier.ts` lines 437–457, empty-query branch; lines
540/548 for the general low-confidence branch: `const fallback_recommended = !intentMatched ||
confidence < 0.5`). Portal mirrors this at `scope_classifier.ts` lines 205–218 and line 299.

At the production-consumer level (`pipeline_planner.ts` line 385: `if (fallbackRecommended) {
... return buildClarificationFromScope(classification) }`), a low-confidence classification never
silently proceeds to plan/execute — it always surfaces as a `ClarificationRequest` to the caller.
This is honest failure surfacing, not a silent guess-and-proceed.

**One caveat worth flagging as a lens note, not a stage-S1 defect per se**: the
`suppliedScopeTuple` bypass (pipeline_planner.ts lines 375–383) means a low-confidence classifier
signal CAN be overridden and the clarification gate skipped, if the caller supplies its own tuple
with a resolved intent. That's a deliberate design (trust an explicit caller declaration over a
text guess) but it is a place where "did the safeguard fire" depends on caller behavior, not
purely on the classifier.

---

## 4. Demonstrated-can-fail

Wrote and ran a scratch vitest test
(`platform/src/__tests__/lib/vidhi/s4_scratch_s1_parity.test.ts`, deleted after evidence capture —
not a permanent test-suite addition) asserting that the MCP classifier should resolve the query
`"What is my career direction and its timing over the next few years?"` to
`intent: 'domain_assessment'` with `fallback_recommended: false`, mirroring what the Portal
classifier already does (and what Portal's own test suite documents as a fix for a real,
native-directed live E2E defect — see `scope_classifier.test.ts` lines 91–102, "W6.1 fix-cycle",
citing trace `6d1eb827-8c9c-4e98-b77e-7f5b5d689fbc`).

**Actual run output (RED)**:

```
 ❯ |node| src/__tests__/lib/vidhi/s4_scratch_s1_parity.test.ts (2 tests | 1 failed) 7ms
     × MCP twin SHOULD also resolve to domain_assessment for door parity (PPR-30) — currently RED 4ms

 FAIL  src/__tests__/lib/vidhi/s4_scratch_s1_parity.test.ts > ... > MCP twin SHOULD also resolve to domain_assessment for door parity (PPR-30) — currently RED
AssertionError: expected 'unknown' to be 'domain_assessment' // Object.is equality

Expected: "domain_assessment"
Received: "unknown"

 Test Files  1 failed (1)
      Tests  1 failed | 1 passed (2)
```

(Full output: `.s4_scratch/s1_demonstrated_can_fail_output.txt`.) This proves the MCP classifier
genuinely still exhibits the original defect the Portal-side W6.1 fix closed: a query that names a
real life-domain but doesn't happen to trip `domain_assessment`'s own trigger words falls through
to `intent: 'unknown'` and `fallback_recommended: true` — i.e. today, an MCP-side caller of
`intent_classify`/`util_intent_classify` on this exact query class gets an unnecessary
clarification prompt where the Portal path (and the unified `prashna_ask` flow, which uses Portal's
classifier for both doors) does not.

---

## 5. Cross-door parity (PPR-30)

Ran the same 19-query representative set through both classifiers directly (unit-level function
calls — `.s4_scratch/s1_parity_and_bench.ts`, full output in `.s4_scratch/s1_run_output.txt`).
**19/19 queries diverged on at least one `scope_tuple` field.**

Two divergence classes, by severity:

**Class A — universal, structural (all 19 queries), width/depth doctrine mismatch.** MCP defaults
non-earned-narrow queries to `width:'broad', depth:'deep'` (Ω4 doctrine: "deepdive is the default
posture, narrow must be earned"); Portal defaults to `width:'standard', depth:'standard'`
(pre-Ω4 keyword-only model) unless an explicit broad/deep keyword is present. This is the dominant
and most consequential divergence — it means the SAME query, classified by the two doors' standalone
tools, produces materially different depth/width routing signals. (Not observed in the unified
`prashna_ask` flow itself, since both doors route through the same Portal `pipeline_planner.ts` —
this affects only the standalone `intent_classify`/`util_intent_classify` MCP tools and any caller
that threads their output back into `prashna_ask`'s `scope_tuple` param.)

**Class B — real intent/domain resolution divergence (3 of 19 queries)**, more concerning because
it changes the *decision*, not just a secondary tuning field:
1. `"What is my career direction and its timing over the next few years?"` — MCP: `intent=unknown,
   fallback_recommended=true` (asks for clarification); Portal: `intent=domain_assessment,
   fallback_recommended=false` (answers directly). Root cause: Portal's "domain-inferred intent
   fallback" (W6.1 fix, `scope_classifier.ts` lines 241–254) was never ported to MCP's
   `intent_scope_classifier.ts`.
2. `"Are there any surgeries indicated for my health?"` — same pattern (MCP `unknown`/clarify vs.
   Portal `domain_assessment`/answer) — MCP's own plural-safe DOMAIN_RULES fix (F-24, comment at
   `intent_scope_classifier.ts` line 178) correctly detects `domains:['health']` but MCP still lacks
   the W6.1 fallback that would use that domain match to resolve intent, so it falls through to
   `unknown` anyway.
3. `"What is my finances outlook?"` / `"What are my relationships prospects?"` — inverse direction:
   MCP detects the correct domain (`wealth`/`marriage`, via its F-24 plural-safe regex fix); Portal
   still uses the older singular-only `DOMAIN_RULES` (e.g. `/\bfinance\b/` does not match
   "finances") and falls back to `domains:['general']`. Both resolve the same `intent` here
   (`domain_assessment` fires on "outlook"/"prospects" regardless), so this doesn't flip the
   clarification outcome, but it does silently under-scope the domain on the Portal side.

**Root cause, module-docstring contradiction**: `scope_classifier.ts`'s own header (lines 1–27)
states it is a "faithful port… do not diverge" of the MCP source, explicitly enumerating the
things that must stay identical (INTENTS/DOMAINS vocabulary, INTENT_RULES/DOMAIN_RULES + ordering,
confidence formula, verbatim template). In practice, three independent fix waves (Ω4 elevation
campaign, F-24 plural-safety, W6.1 domain-inferred-fallback) each landed on only one side, and the
"do not diverge" contract has silently broken. Both `.test.ts` suites pass in isolation because
each only asserts its own file's current behavior — nothing in the test suite asserts cross-door
equality, so this divergence has no CI tripwire today.

---

## Findings (for stream-lead EDIR_V3 filing — proposed only, not final)

### Finding S1-F1 — Cross-door scope-classifier divergence (width/depth doctrine)
- **Class**: DEFECT
- **Proposed severity**: S2 (proposed) — structural, affects every query through the standalone
  MCP classifier tools vs. the Portal/unified path; does not corrupt data but changes routing
  behavior silently against the module's own "must not diverge" contract.
- **Lens(es)**: Pipeline Correctness, Door Parity (PPR-30)
- **Pipeline stage**: S1
- **Expected**: `intent_scope_classifier.ts` (MCP) and `scope_classifier.ts` (Portal) compute
  identical `scope_tuple.width`/`depth` for identical input, per the Portal file's own docstring
  ("faithful port… do not diverge", `scope_classifier.ts` lines 1–27).
- **Observed** (2026-08-28): 19/19 representative queries diverge on `width`/`depth` — MCP
  implements the Ω4 "earned-narrow, default-deep" doctrine; Portal still implements the pre-Ω4
  keyword-only model, default `standard`/`standard`. Evidence:
  `.s4_scratch/s1_parity_and_bench.ts`, output in `.s4_scratch/s1_run_output.txt`.
- **Code anchor**: `platform-mcp/src/tools/intent_scope_classifier.ts:212-350` (Ω4 apparatus:
  `detectNarrow`, `Route`, `narrow_confidence`, `depth_available`) has no counterpart in
  `platform/src/lib/vidhi/scope_classifier.ts` (entire file — no `route`/`narrow_confidence`/
  `depth_available` fields, no `detectNarrow` equivalent; width/depth logic at lines 256–265).
- **Proposed fix class**: either (a) port the Ω4 doctrine to Portal's `scope_classifier.ts` so both
  doors agree, or (b) if Ω4 was deliberately MCP-only, update the Portal docstring to stop claiming
  parity and document the intentional split — plus add a cross-door parity test so future drift is
  caught by CI.
- **Verification rung achieved**: REPLAY/INTEGRATION (direct unit-level function calls, real code
  paths, real regex tables — no mocks).

### Finding S1-F2 — MCP classifier missing the W6.1 domain-inferred-intent fix (real clarification-outcome divergence)
- **Class**: DEFECT
- **Proposed severity**: S2 (proposed) — this is the same defect class Portal's own test suite
  documents as having caused a real, native-directed live E2E incident (trace
  `6d1eb827-8c9c-4e98-b77e-7f5b5d689fbc`) before the Portal-side fix; it is confirmed still present
  on the MCP standalone classifier tools today.
- **Lens(es)**: Pipeline Correctness, Door Parity (PPR-30), Failure-honesty (over-triggers
  clarification, a usability/correctness regression rather than a silent-wrong-answer one)
- **Pipeline stage**: S1
- **Expected**: A query that names a real life-domain (e.g. "career", "health") but doesn't use
  one of `domain_assessment`'s own trigger words should resolve to `intent: 'domain_assessment'`
  with `fallback_recommended: false` — this is what Portal's `scope_classifier.ts` lines 241–254
  do, per the W6.1 fix.
- **Observed** (2026-08-28): MCP's `intent_scope_classifier.ts` has no equivalent fallback; the
  same query class still resolves to `intent: 'unknown'`, `fallback_recommended: true`.
  Demonstrated with a real, run vitest test — see §4 above for full RED output.
- **Code anchor**: missing counterpart to `platform/src/lib/vidhi/scope_classifier.ts:241-254`
  ("2b. Domain-inferred intent fallback") in `platform-mcp/src/tools/intent_scope_classifier.ts`
  (would slot in after the domain-rules loop, around line 478).
- **Proposed fix class**: port the W6.1 domain-inferred-intent fallback block verbatim to the MCP
  classifier, honoring its existing `matched_rules` audit-trail convention.
- **Verification rung achieved**: REPLAY/INTEGRATION (real vitest run against real source, RED
  output pasted above; test deleted after capture per scratch-test convention, not left in the
  permanent suite).

### Finding S1-F3 — Portal DOMAIN_RULES lacks the F-24 plural-safety fix (domain under-detection)
- **Class**: DEFECT
- **Proposed severity**: S3 (proposed) — silent domain under-scoping (`domains: ['general']`
  instead of the correct specific domain), not a routing-outcome flip in the cases tested, but a
  real accuracy loss that could affect domain-scoped retrieval downstream.
- **Lens(es)**: Pipeline Correctness, Door Parity (PPR-30)
- **Pipeline stage**: S1
- **Expected**: Per the "faithful port, do not diverge" contract, Portal's `DOMAIN_RULES` should
  match MCP's plural-safe vocabulary (F-24 fix, e.g. `moneys?`, `finances?`, `incomes?`, `wi(fe|ves)`,
  `spouses?`, `relationships?`, `diseases?`, `surg(ery|eries)`, `debts?`, `loans?`).
- **Observed** (2026-08-28): `"What is my finances outlook?"` → MCP: `domains:['wealth']`; Portal:
  `domains:['general']`. Same for `"What are my relationships prospects?"` → MCP:
  `domains:['marriage']`; Portal: `domains:['general']`. Evidence: `.s4_scratch/s1_run_output.txt`.
- **Code anchor**: `platform-mcp/src/tools/intent_scope_classifier.ts:182-193` (F-24-fixed
  `DOMAIN_RULES`) vs. `platform/src/lib/vidhi/scope_classifier.ts:164-175` (unfixed, singular-only).
- **Proposed fix class**: port the F-24 plural-safe `DOMAIN_RULES` regex set to Portal verbatim.
- **Verification rung achieved**: REPLAY/INTEGRATION.

### Finding S1-F4 — No independent classification-accuracy corpus (thin/self-referential test fixtures)
- **Class**: BASELINE / IMPROVEMENT
- **Proposed severity**: S3 (proposed)
- **Lens(es)**: Optimality
- **Pipeline stage**: S1
- **Expected/baseline note**: a classifier this central to routing would ideally be measured
  against an independently-labeled corpus (even a modest 50–100 query set spanning all 11 intents
  × ambiguous/adversarial cases) with a tracked accuracy number over time.
- **Observed** (2026-08-28): the only "accuracy" evidence is 37 (MCP) / 10 (Portal) hand-written
  unit-test cases, each asserting the classifier's output against itself (no independent ground
  truth). Honest baseline recorded in §2's table above.
- **Code anchor**: `platform-mcp/src/tools/intent_scope_classifier.test.ts`,
  `platform/src/__tests__/lib/vidhi/scope_classifier.test.ts`.
- **Proposed fix class**: author a small independently-labeled fixture corpus (e.g. JSON file of
  {query, expected_intent, expected_domains}) checked in and run in CI as a standing accuracy gate,
  separate from the regex-table unit tests.
- **Verification rung achieved**: REPLAY (test-suite inspection + count).

---

## Artifacts

- `.s4_scratch/s1_parity_and_bench.ts` — parity/bench/precision script (run via `npx tsx` from `platform/`)
- `.s4_scratch/s1_run_output.txt` — full captured stdout of the above (parity table, adversarial probe, latency bench, precision report)
- `.s4_scratch/s1_demonstrated_can_fail_output.txt` — full captured RED vitest output for the demonstrated-can-fail test (test file itself was deleted after capture, per scratch-test convention — not left in the permanent suite)
