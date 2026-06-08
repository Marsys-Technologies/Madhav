---
status: COMPLETE
session: W2-EVAL-A
scope: UQE-3-REVISED (precision citation gate) + EVAL-1 (golden test set)
authored: 2026-05-01
round: 1
critical_path: false
blocks: W2-EVAL-B (Round 4) for EVAL-1; W2-INSTRUMENT (Round 3) reads the context_assembly_log field added here
---

# CLAUDECODE_BRIEF — W2-EVAL-A
## Precision Citation Gate + Golden Test Set

Read CLAUDE.md §0 first. Copy this file to the project root as
`CLAUDECODE_BRIEF.md` before opening the session.

---

## Context

Two independent tasks:

**UQE-3-REVISED** replaces the existing blunt citation gate (counts
`SIG.MSR.NNN` patterns) with a two-layer validator: Layer 1 is the existing
heuristic; Layer 2 cross-references each citation ID against the assembled
context to detect training-data leakage. Existing code lives at
`platform/src/lib/synthesis/citation_check.ts`.

**EVAL-1** creates the golden test set: 25 labeled `(query → expected_tool_plan)`
pairs used by W2-EVAL-B (Round 4) to score planner quality with tool_recall
and tool_precision metrics.

---

## Acceptance criteria

### AC.E.1 — UQE-3-REVISED: Two-layer citation validator

#### Layer 1 (existing — preserve)
The current `citation_check.ts` counts `SIG.MSR.NNN` pattern occurrences.
Preserve this as Layer 1 (existence check).

#### Layer 2 (new — cross-reference)
New export in `citation_check.ts`:
```typescript
export interface CitationValidationResult {
  layer1_count: number          // SIG.MSR.NNN pattern count in output text
  layer2_verified: number       // citations found in assembled context JSONB
  layer2_leaked: number         // citations in output but NOT in context
  gate_result: 'PASS' | 'WARN' | 'ERROR'
  gate_reason: string
}

export function validateCitations(
  outputText: string,
  assembledContextJson: string,  // the full context bundle JSON string
): CitationValidationResult
```

Gate logic:
```
verified_citations ≥ 1                              → PASS
verified_citations = 0 AND layer1_count > 0         → WARN  (training-data leak)
verified_citations = 0 AND layer1_count = 0
  AND query is prescriptive                          → ERROR (throw PipelineError)
verified_citations = 0 AND layer1_count = 0
  AND query is NOT prescriptive                     → PASS  (informational query, ok)
```

"Prescriptive" = `queryPlan.query_class` is `'remedial'` or `'predictive'`.

Add `CITATION_GATE_OVERRIDE` feature flag (default `false`). When true, convert
ERROR → WARN (allows admin bypass without code change).

#### Integration into route.ts

In the v2 pipeline path in `route.ts`, after synthesis completes, call
`validateCitations(outputText, assembledContextJsonString)`:
- Store result in `context_assembly_log.verified_citations` (field added by W2-SCHEMA).
  If W2-SCHEMA hasn't run yet, write to a local variable and log — don't block.
- On WARN: log to console; emit trace event `citation_warn`.
- On ERROR (and `CITATION_GATE_OVERRIDE=false`): throw `PipelineError` with
  `validator_name: 'citation_gate_l2'`.

#### feature_flags.ts

Add to FeatureFlag union and DEFAULT_FLAGS:
```typescript
'CITATION_GATE_OVERRIDE'   // default: false
```

#### Tests

New file: `platform/tests/synthesis/citation_check.test.ts`
- Test PASS: output contains SIG.MSR.001, context contains SIG.MSR.001.
- Test WARN: output contains SIG.MSR.001, context does NOT contain it → leak.
- Test ERROR: remedial query, output has no citations, context has no citations.
- Test PASS (non-prescriptive): informational query, output has no citations → PASS.
- Test CITATION_GATE_OVERRIDE converts ERROR to WARN.

### AC.E.2 — EVAL-1: Golden test set

New file: `platform/tests/eval/golden_test_set.json`

Create 25 labeled query→plan pairs. Each entry:
```json
{
  "id": "GT.001",
  "query": "...",
  "query_class": "remedial | interpretive | predictive | ...",
  "expected_tools": ["msr_sql", "remedial_codex_query"],
  "required_tools": ["remedial_codex_query"],  // must appear; subset of expected
  "forbidden_tools": [],                        // must NOT appear
  "notes": "Why this example is in the set"
}
```

Distribution across 25 entries (minimum):
- 6 remedial queries (planets, gemstones, mantras)
- 6 interpretive queries (chart reading, house analysis, yoga identification)
- 4 predictive queries (timing, dasha, transit)
- 4 holistic queries (multi-domain synthesis)
- 3 planetary queries (single-planet deep dive)
- 2 edge cases (very short query, ambiguous query)

Each `expected_tools` list must reflect what a correct LLM-first planner
should select — derived from the tool descriptions in CAPABILITY_MANIFEST.json,
not from the current classify() output.

The queries should be realistic questions a native asks about their chart.
Do NOT use generic astrology questions — all 25 must be grounded in the
MARSYS-JIS subject (Abhisek Mohanty, born 1984-02-05, Bhubaneswar) or be
chart-agnostic questions that would work for any native.

New file: `platform/tests/eval/README.md`
- Explains the golden test set format.
- Documents the scoring formula: `tool_recall = |predicted ∩ expected| / |expected|`,
  `tool_precision = |predicted ∩ expected| / |predicted|`.
- States acceptance thresholds for W2-EVAL-B: recall ≥ 0.80, precision ≥ 0.90.

### AC.E.3 — tsc clean + commit

`npx tsc --noEmit` clean on all new/changed files.

```
feat(w2-eval-a): two-layer citation gate + golden test set (UQE-3-REVISED + EVAL-1)

- citation_check.ts: Layer 2 cross-ref validator; WARN on leak, ERROR on zero-verified remedial
- feature_flags: CITATION_GATE_OVERRIDE (default false)
- route.ts: integrate citation validation post-synthesis; emit citation_warn trace event
- golden_test_set.json: 25 labeled query→plan pairs across 6 query classes
- tests/eval/README.md: scoring formula + acceptance thresholds
```

---

## may_touch

```
platform/src/lib/synthesis/citation_check.ts
platform/src/lib/config/feature_flags.ts
platform/src/app/api/chat/consume/route.ts       (add validateCitations call post-synthesis)
platform/tests/synthesis/citation_check.test.ts   (new)
platform/tests/eval/golden_test_set.json           (new)
platform/tests/eval/README.md                      (new)
```

## must_not_touch

```
platform/src/lib/router/**
platform/src/lib/retrieve/**
platform/src/lib/pipeline/**
platform/src/lib/models/**
platform/src/hooks/**
platform/src/components/**
platform/migrations/**
00_ARCHITECTURE/CAPABILITY_MANIFEST.json
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
```

---

## Hard constraints

- Layer 1 of citation_check.ts must remain backward compatible. Do not remove
  the existing `checkCitations()` function — wrap it or extend it.
- The golden test set (EVAL-1) must be grounded in real Jyotish query patterns.
  Do not invent fictitious astrological concepts. Consult
  `chart_facts` DB table (via `forensic_render.ts`; FORENSIC v8.0 chart data — md archived at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md`) for chart context.
- B.10: Do not fabricate expected_tools values. Each entry's expected_tools
  must be derived from what the tool actually retrieves per its description
  in the codebase and CAPABILITY_MANIFEST.json.
- EVAL-1 is data only — no runner code. The smoke test runner is EVAL-2 (Round 4).

---

*W2-EVAL-A · authored 2026-05-01 · unblocks W2-EVAL-B (Round 4)*
