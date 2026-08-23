---
lane: F-126
stream: S3_SATYA (spec) -> S1_DVARA (build)
stage: S — SPEC
author: SATYA-LEAD (S3)
status: DRAFT — awaiting VERIFIER review
tier: TIER4-POLISH
class: CL-08-adjacent tier/confidence honesty
lease_note: |
  F-126's mechanism lives in platform/src/app/api/mcp/primitives/[tool]/route.ts and the
  cross-cutting platform/src/lib/mcp/epistemics.ts helper — S1 DVĀRA's explicit OWNS list
  (plan §2, S1 section: "platform/src/app/api/mcp/primitives/**"), NOT S3's. Per plan §2.1's
  ordered-handoff pattern (the registry_bridge.ts / F-38 precedent: "S3 posts a spec and S2's
  [here: S1's] builder applies it"), this document is written to be executed directly by an
  S1 builder with no prior context from the S3 diagnosis conversation. One touched file
  (query_life_events.ts) is genuinely inside S3's own L5_mimamsa/** lease — S1 may build it
  in the same commit since it is one coherent fix; no re-lease of that file to S1 is implied
  beyond this one spec's scope.
---

# SPEC — F-126: `confidence_band` must not claim 'high' on a zero-result surgical query

## 0. Read this first (for the S1 builder)

You have not seen the diagnosis conversation. Everything you need is below: exact files,
exact line ranges (as of 2026-08-16, `ekv/b-01-dignity-oracle-fix` branch tip — re-verify
against your own checkout before editing, since other lanes may land first), exact diffs,
and an exit test you can paste in and run. Read `00_ARCHITECTURE/briefs/parisesa/lanes/F-126/
DIAGNOSIS.md` for the full reproduction trace if anything below is ambiguous — it is the
Stage-D document this spec is built from.

## 1. Root-cause statement

`buildEpistemicsBlock` and every one of its five call sites treat "the surgical primitive
call dispatched and returned without throwing" (retrieval-**mechanism** success) as
sufficient grounds to stamp `confidence_band: 'high'` (an **evidential** claim about the
content of the result), because no code path anywhere between a capability handler's
honestly-computed result and the final MCP envelope carries a signal for "this result set is
empty" — so the literal-constant `'high'` at `platform/src/app/api/mcp/primitives/[tool]/
route.ts:310` fires unconditionally, even when the query matched zero rows, letting a
zero-result answer (e.g. a marriage-timing LEL query) read to a consumer as a confidmed,
high-confidence negative rather than as "unrecorded."

## 2. Design decision: which of the two options, and why

The task brief posed two options:
(a) `confidence_band` null/absent on empty + a new `empty_reason` field, or
(b) `confidence_band` stays evidential-general + a separate `retrieval_status`/
    `mechanism_status` field carries "ran cleanly."

**Chosen: (a).** Reasoning, grounded in what was actually read in the codebase (not assumed):

- `surgical: true` **already is** the "ran cleanly" / mechanism-status signal option (b) would
  duplicate. `EpistemicsBlock.surgical` (`platform/src/lib/mcp/types.ts:37`) is documented as
  exactly that ("True for surgical primitive calls") and is untouched by this spec — it stays
  `true` for a zero-result LEL call, honestly, because the call DID run cleanly. Adding a
  second `retrieval_status`/`mechanism_status` field would be a second name for a fact
  `surgical` already states — a duplicate field is its own honesty problem (two names, one
  meaning, guaranteed future drift risk under §N.7 item 3's "no wrapper-local constant may
  shadow" doctrine, generalized to "no wrapper-local field may shadow").
- Making `confidence_band` "describe result evidential weight generally" (option b's framing)
  is not buildable honestly at the shared route/envelope layer: `toolResult` there is `unknown`
  (`route.ts:255`) — a `ToolBundle` whose `results: ToolBundleResult[]` (`shared_types.ts:81-95`)
  carries only a stringified `content` blob per tool, with **no common schema** across the ~10
  whitelisted primitives (LEL's JSON has `count`/`total_matching`; `ganita_chart_facts_get`'s
  does not). A route-level function that tried to grade "evidential weight" generically by
  sniffing arbitrary JSON content would have to guess field names per tool — exactly the kind
  of fabricated/unearned signal CLAUDE.md §N.8 forbids ("a signal without such a detector is
  null, not green"). The only place that genuinely KNOWS whether its own result is empty is
  the capability handler itself (`query_life_events.ts` already computes `total_matching`
  correctly, honestly, today).
- Therefore the correct architecture is: **let the capability handler that already knows
  (LEL, for this finding) say so explicitly through the existing `ToolResult` contract, thread
  that signal un-stringified through the one conversion point that currently discards it, and
  have the envelope builder default to `null` instead of fabricating `'high'` whenever a
  handler has positively declared its result empty.** For any of the other ~9 whitelisted
  primitives that have NOT been updated to declare `is_empty` (out of scope for this TIER4
  spec — see §4), behavior is **unchanged** (`'high'` continues to be reported) — this spec
  closes F-126's actual reproduction (LEL) and builds the general mechanism other tools can
  opt into later; it does not silently claim to have graded all ten.

This satisfies CLAUDE.md §N.6 item 4 (`empty_reason` discipline for a `density_contract`-style
surface, the finding's own cited doctrine) and §N.8 (earned signal — `confidence_band: null`
is what a caller sees until a real per-tool detector exists to justify a non-null value).

## 3. Files to change

### 3a. `platform/src/lib/retrieval/registry/types.ts` — `ToolResult` interface (currently
lines 533-537)

Current:
```ts
/** Result type for tool calls */
export interface ToolResult {
  content: string | object
  is_error?: boolean
  metadata?: Record<string, unknown>
}
```

Change to:
```ts
/** Result type for tool calls */
export interface ToolResult {
  content: string | object
  is_error?: boolean
  metadata?: Record<string, unknown>
  /**
   * F-126: set true by a capability handler that has positively determined its own
   * result set is empty (e.g. a row-count query returned 0). Absent/undefined means
   * "this handler does not (yet) declare emptiness" — NOT "non-empty" — callers must
   * not treat a missing `is_empty` as a positive non-empty claim.
   */
  is_empty?: boolean
  /**
   * Human-readable reason for the emptiness, set alongside is_empty: true. Mirrors the
   * empty_reason convention already used elsewhere in the registry (e.g.
   * completeness_wiring.ts, register_d8_assess_domain.ts) — never fabricated by a layer
   * that doesn't know why the result is empty; only the producing handler sets it.
   */
  empty_reason?: string | null
}
```

**Why here:** this is the capability-handler-facing contract (`CapabilityHandler` in the same
file, line ~540, returns `Promise<ToolResult>`) — the only place with real per-tool knowledge
of what "empty" means, per §2's reasoning. Purely additive/optional — no existing handler
breaks.

### 3b. `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts` — the
handler's return (currently lines 208-224)

This file is genuinely inside S3's own lease (`L5_mimamsa/**`); build it in the same commit as
the S1-owned files below — it is one fix, not two lanes.

Current:
```ts
      return {
        content: {
          chart_id,
          events: eventsResult.rows,
          count,
          total_matching,
          has_more,
          filters: { category, domain, significance, start_date, end_date, query: search_query, limit, offset },
          provenance: {
            tables: ['life_events'],
            no_leakage_note:
              'life_events is a calibration corpus only — must not feed prediction generation.',
            source: 'LIFE_EVENT_LOG (user-authored); served chart-scoped.',
          },
        },
        is_error: false,
      }
```

Change to:
```ts
      const is_empty = total_matching === 0
      return {
        content: {
          chart_id,
          events: eventsResult.rows,
          count,
          total_matching,
          has_more,
          filters: { category, domain, significance, start_date, end_date, query: search_query, limit, offset },
          provenance: {
            tables: ['life_events'],
            no_leakage_note:
              'life_events is a calibration corpus only — must not feed prediction generation.',
            source: 'LIFE_EVENT_LOG (user-authored); served chart-scoped.',
          },
        },
        is_error: false,
        is_empty,
        // F-126: total_matching===0 is a genuine "no matching event recorded" for this
        // filter set, never "no such event occurred" — the LEL corpus itself may be
        // populated (chart_id-scoped, non-empty for the canonical chart today); this only
        // says the current filters/search_query matched nothing.
        empty_reason: is_empty
          ? `No life_events rows matched chart_id=${chart_id} with the given filters` +
            (search_query ? ` and text search '${search_query}'` : '') + '.'
          : null,
      }
```
`total_matching` is already computed honestly two lines above (line 202 in the current file) —
this reads it, it does not re-derive it (§N.7 item 1 compliance).

### 3c. `platform/src/lib/retrieval/shared_types.ts` — `ToolBundleResult` interface (currently
lines 81-88)

Current:
```ts
export interface ToolBundleResult {
  content: string
  source_canonical_id?: string
  source_version?: string
  confidence?: number
  significance?: number
  signal_id?: string
}
```

Change to:
```ts
export interface ToolBundleResult {
  content: string
  source_canonical_id?: string
  source_version?: string
  confidence?: number
  significance?: number
  signal_id?: string
  /** F-126: passthrough of ToolResult.is_empty (see tool_name_bridge.ts toToolBundleResults). */
  is_empty?: boolean
  /** F-126: passthrough of ToolResult.empty_reason. */
  empty_reason?: string | null
}
```

### 3d. `platform/src/lib/retrieval/registry/tool_name_bridge.ts` — `toToolBundleResults`
(currently lines 237-265), the single ToolResult branch (lines 256-261)

Current:
```ts
  // Single ToolResult (content: string | object)
  if (typeof content === 'object' && 'content' in content) {
    const inner = (content as Record<string, unknown>)['content']
    const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
    return [{ content: str }]
  }
```

Change to:
```ts
  // Single ToolResult (content: string | object)
  if (typeof content === 'object' && 'content' in content) {
    const inner = (content as Record<string, unknown>)['content']
    const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
    const rec = content as Record<string, unknown>
    // F-126: thread the handler's own is_empty/empty_reason declaration through instead
    // of discarding it during stringification — this is the one conversion point that
    // previously dropped both fields.
    const result: ToolBundleResult = { content: str }
    if (typeof rec['is_empty'] === 'boolean') result.is_empty = rec['is_empty']
    if (rec['empty_reason'] !== undefined) {
      result.empty_reason = rec['empty_reason'] as string | null
    }
    return [result]
  }
```
No other branch of `toToolBundleResults` changes — the array branch and the `results`-array
branch already pass through whatever shape their items have (see §4 for why this is not
extended to those branches).

### 3e. `platform/src/lib/mcp/types.ts` — `EpistemicsBlock` (currently lines 35-50)

Current:
```ts
export interface EpistemicsBlock {
  /** True for surgical primitive calls; false for ask_madhav full-pipeline calls. */
  surgical: boolean
  /** Calibrated confidence band for the answer. */
  confidence_band: 'high' | 'medium' | 'low'
  /**
   * Horizon in days for predictive answers; null for non-predictive.
   * Example: 90 = "this applies within the next ~3 months".
   */
  horizon_days: number | null
  /**
   * The specific condition that would falsify this answer.
   * Required for predictive; null for factual.
   */
  falsifier: string | null
}
```

Change to:
```ts
export interface EpistemicsBlock {
  /** True for surgical primitive calls; false for ask_madhav full-pipeline calls. */
  surgical: boolean
  /**
   * Calibrated confidence band for the answer's CONTENT (not the retrieval mechanism —
   * `surgical` already carries "the call ran cleanly"). F-126: null when the result is
   * known-empty and no calibrated confidence about a genuine negative can be honestly
   * claimed — never fabricated to 'high' just because the call didn't throw.
   */
  confidence_band: 'high' | 'medium' | 'low' | null
  /**
   * Horizon in days for predictive answers; null for non-predictive.
   * Example: 90 = "this applies within the next ~3 months".
   */
  horizon_days: number | null
  /**
   * The specific condition that would falsify this answer.
   * Required for predictive; null for factual.
   */
  falsifier: string | null
  /**
   * F-126: set (non-null) whenever confidence_band is null because the result is
   * known-empty — explains WHY, distinguishing "no matching row recorded" from "corpus
   * empty" per CLAUDE.md §N.6 item 4's empty_reason discipline. Null when confidence_band
   * is non-null, or when emptiness is genuinely unknown (not yet wired for this tool).
   */
  empty_reason: string | null
}
```

### 3f. `platform/src/lib/mcp/epistemics.ts` — `BuildEpistemicsBlockParams` + `buildEpistemicsBlock`
(currently lines 42-74)

Current:
```ts
export interface BuildEpistemicsBlockParams {
  /**
   * True for surgical primitive calls (no B.11 floor enforcement, no synthesis).
   * False for ask_madhav / execute_plan (full pipeline).
   */
  surgical: boolean
  /**
   * Calibrated confidence band. Defaults to 'medium' when not explicitly set.
   * For surgical calls (single fact lookups), 'high' is appropriate.
   * For holistic synthesis, use 'medium' unless there is strong convergence.
   */
  confidence_band?: 'high' | 'medium' | 'low'
  /**
   * Prediction horizon in days. Set for predictive answers; null otherwise.
   */
  horizon_days?: number | null
  /**
   * Specific falsifier condition. Required for predictive; null for factual.
   */
  falsifier?: string | null
}

/**
 * Build the mandatory EpistemicsBlock for any MCP response.
 */
export function buildEpistemicsBlock(params: BuildEpistemicsBlockParams): EpistemicsBlock {
  return {
    surgical: params.surgical,
    confidence_band: params.confidence_band ?? 'medium',
    horizon_days: params.horizon_days ?? null,
    falsifier: params.falsifier ?? null,
  }
}
```

Change to:
```ts
export interface BuildEpistemicsBlockParams {
  /**
   * True for surgical primitive calls (no B.11 floor enforcement, no synthesis).
   * False for ask_madhav / execute_plan (full pipeline).
   */
  surgical: boolean
  /**
   * Calibrated confidence band for the answer's content. Defaults to 'medium' when the
   * param is OMITTED entirely. Pass `null` explicitly (not omit) when the caller has
   * positively determined the result is empty and no evidential claim can be made — see
   * F-126. For surgical calls with a genuine non-empty result, 'high' is appropriate.
   * For holistic synthesis, use 'medium' unless there is strong convergence.
   */
  confidence_band?: 'high' | 'medium' | 'low' | null
  /**
   * Prediction horizon in days. Set for predictive answers; null otherwise.
   */
  horizon_days?: number | null
  /**
   * Specific falsifier condition. Required for predictive; null for factual.
   */
  falsifier?: string | null
  /**
   * F-126: reason the result is empty, when confidence_band is explicitly null.
   */
  empty_reason?: string | null
}

/**
 * Build the mandatory EpistemicsBlock for any MCP response.
 *
 * F-126: confidence_band distinguishes "omitted" (undefined → defaults to 'medium', the
 * pre-existing behavior, unchanged) from "explicitly null" (caller positively knows the
 * result is empty → stays null, never silently promoted to 'medium'). Use `'confidence_band'
 * in params` rather than `??` so `null` is honored instead of defaulted away.
 */
export function buildEpistemicsBlock(params: BuildEpistemicsBlockParams): EpistemicsBlock {
  const confidence_band =
    'confidence_band' in params && params.confidence_band !== undefined
      ? params.confidence_band
      : 'medium'
  return {
    surgical: params.surgical,
    confidence_band,
    horizon_days: params.horizon_days ?? null,
    falsifier: params.falsifier ?? null,
    empty_reason: confidence_band === null ? (params.empty_reason ?? null) : null,
  }
}
```

### 3g. `platform/src/app/api/mcp/primitives/[tool]/route.ts` — the epistemics block (currently
lines 307-313)

Current:
```ts
  // Build surgical epistemics block
  const epistemics = buildEpistemicsBlock({
    surgical: true,
    confidence_band: 'high',
    horizon_days: null,
    falsifier: null,
  })
```

Change to:
```ts
  // Build surgical epistemics block.
  // F-126: 'high' is only honest when the underlying result is non-empty. toolResult is a
  // ToolBundle (results: ToolBundleResult[]); read the FIRST result's is_empty/empty_reason
  // — the passthrough field wired in tool_name_bridge.ts's toToolBundleResults, not a parse
  // of the tool-specific content JSON (which the route cannot interpret generically across
  // the ~10 whitelisted primitives — see SPEC.md §2). A tool that has not been updated to
  // declare is_empty leaves it undefined, and behavior is unchanged ('high').
  const firstResult = (toolResult as { results?: Array<{ is_empty?: boolean; empty_reason?: string | null }> } | undefined)
    ?.results?.[0]
  const resultIsEmpty = firstResult?.is_empty === true
  const epistemics = buildEpistemicsBlock({
    surgical: true,
    confidence_band: resultIsEmpty ? null : 'high',
    horizon_days: null,
    falsifier: null,
    empty_reason: resultIsEmpty ? (firstResult?.empty_reason ?? 'Result set is empty.') : null,
  })
```

### 3h. `platform/src/app/api/mcp/recent/route.ts` — sibling site (currently line ~204)

This endpoint builds its own `queries` array directly from DB rows (see lines ~130-198) — no
`ToolBundle` indirection, so the array-length check is generic and safe here without any of
`is_empty`'s plumbing.

Current (context, `result: { queries }` immediately follows):
```ts
        epistemics: buildEpistemicsBlock({ surgical: true, confidence_band: 'high' }),
        result: { queries },
```

Change to:
```ts
        epistemics: buildEpistemicsBlock({
          surgical: true,
          confidence_band: queries.length === 0 ? null : 'high',
          empty_reason: queries.length === 0
            ? 'No recent MCP queries found for this principal in the lookback window.'
            : null,
        }),
        result: { queries },
```

## 4. Sibling sites covered / excluded

From DIAGNOSIS.md §4's `buildEpistemicsBlock(...)` call-site census (5 sites total):

| Call site | Covered? | Reason |
|---|---|---|
| `primitives/[tool]/route.ts:308` | **YES — §3g** | The finding's own reproduction site. |
| `recent/route.ts:204` | **YES — §3h** | Same unconditional-'high' defect on a genuine list; array length is a safe, generic, non-fabricated emptiness signal at this route (no ToolBundle indirection here — the array is built directly). |
| `trace/[trace_id]/route.ts:134` | **EXCLUDED — does not reproduce.** | `rows.length === 0` already short-circuits to a `404 validation` error envelope at lines 116-125, BEFORE line 134 is ever reached. By construction, every response that reaches line 134 has ≥1 real trace step. `'high'` here is always evidentially grounded; there is no zero-result path into this `confidence_band` assignment. |
| `asset/route.ts:217` | **EXCLUDED — does not reproduce (same shape).** | A failed/missing file read already returns a `500 internal` error envelope at lines 189-202, before line 217. `content` at line 217 is guaranteed to be a successfully-read file's bytes. (Residual, non-blocking, NOT part of this fix: a canonical artifact that exists but is a literal zero-byte file would still read 'high' — judged not worth a defensive check for an artifact-registry file that is never intentionally empty; flag for a future census if it ever occurs.) |
| `writes/[action]/route.ts:247` | **EXCLUDED — different defect class, not this finding's mechanism.** | This call passes no `confidence_band` at all, so it already defaults to `'medium'` (`epistemics.ts` behavior, unchanged by this spec) — not the `'high'`-on-empty conflation F-126 claims. Its real gap (DIAGNOSIS.md §4: a write's outcome — succeeded / partially applied / no-op — is never consulted) needs its own outcome-status model (e.g. `write_outcome: 'applied' \| 'no_op' \| 'partial'`), which is out of proportion for this TIER4 spec and not part of F-126's claim text. Recommend a new, separately-filed finding — do not fold into this build.** |

Additionally, per DIAGNOSIS.md §4's prose finding (not a separate call site, but a real blast-
radius fact): the `primitives/[tool]/route.ts:308` call site serves **all ~10 whitelisted
surgical primitives**, not just `lel_query`/`mimamsa_lel_query`. This spec wires `is_empty`
into exactly one of them — `query_life_events.ts` (§3b), because that is F-126's actual
reproduction and the only handler this spec has read and verified computes emptiness
honestly today. **The other ~9 whitelisted primitives are NOT touched by this spec** and
continue to report `confidence_band: 'high'` unconditionally, exactly as before — §3a/§3c/§3d/
§3e/§3f/§3g build the general mechanism (any handler CAN now declare `is_empty`), but only
§3b actually exercises it. This is an honest partial close, not a claimed full close of
"every surgical primitive now reports accurate confidence" — do not represent it as more than
it is in REVIEW.md or the live evidence file. A follow-up finding/lane extending `is_empty` to
the remaining ~9 handlers (starting with the other 3 per_chart list-returning ones, by the same
`total_matching===0` pattern) is recommended but out of scope here.

## 5. Exit test

New test cases in **`platform/src/lib/__tests__/mcp/primitives.test.ts`** (existing file —
add after the existing `Test 4` block, ~line 241), reusing that file's existing
`buildRequest`/`buildRouteParams`/`mockGetTool` helpers verbatim:

```ts
  it('Test 6 (F-126): zero-result LEL call does NOT claim confidence_band: high', async () => {
    // Simulate query_life_events.ts's honest zero-match return, after tool_name_bridge.ts's
    // toToolBundleResults threads is_empty/empty_reason through (§3d).
    mockGetTool.mockReturnValue({
      name: 'lel_query',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        tool_bundle_id: 'test-bundle',
        tool_name: 'lel_query',
        tool_version: '1.0',
        invocation_params: {},
        results: [
          {
            content: JSON.stringify({ events: [], count: 0, total_matching: 0, has_more: false }),
            is_empty: true,
            empty_reason: 'No life_events rows matched chart_id=482012f1-710e-4a25-994a-93821f5871aa with the given filters and text search \'marriage relationship spouse partner wedding\'.',
          },
        ],
        served_from_cache: false,
        latency_ms: 1,
        result_hash: 'sha256:test',
        schema_version: '1.0',
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('lel_query', {
      params: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', query: 'marriage relationship spouse partner wedding' },
    })
    const res = await POST(req, buildRouteParams('lel_query'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    // THE FIX: not 'high' on a zero-result call.
    expect(body.epistemics.confidence_band).toBeNull()
    expect(body.epistemics.empty_reason).toContain('No life_events rows matched')
    // surgical (mechanism-success) is untouched — the call genuinely ran cleanly.
    expect(body.epistemics.surgical).toBe(true)
  })

  it('Test 7 (F-126 regression guard): non-empty result still reports confidence_band: high', async () => {
    mockGetTool.mockReturnValue({
      name: 'lel_query',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        tool_bundle_id: 'test-bundle-2',
        tool_name: 'lel_query',
        tool_version: '1.0',
        invocation_params: {},
        results: [
          {
            content: JSON.stringify({ events: [{ event_id: 'LEL-001' }], count: 1, total_matching: 1, has_more: false }),
            is_empty: false,
            empty_reason: null,
          },
        ],
        served_from_cache: false,
        latency_ms: 1,
        result_hash: 'sha256:test2',
        schema_version: '1.0',
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('lel_query', { params: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa' } })
    const res = await POST(req, buildRouteParams('lel_query'))
    const body = await res.json()
    expect(body.epistemics.confidence_band).toBe('high')
    expect(body.epistemics.empty_reason).toBeNull()
  })
```

**Today (before this fix):** Test 6 fails — `body.epistemics.confidence_band` is `'high'`
(the hardcoded literal at `route.ts:310`) and `body.epistemics.empty_reason` is `undefined`
(the field does not exist on `EpistemicsBlock` yet — the whole assertion throws a TypeError
on a non-existent property path, or at minimum `toContain` fails against `undefined`). Test 7
passes today already (it is the regression guard, added alongside Test 6 in the same commit,
not a second red test) — it exists so the fix cannot be "always null" as a lazy pass.
**After this fix:** both pass.

Also add two unit-level cases directly to `buildEpistemicsBlock` in
**`platform/src/lib/__tests__/mcp/epistemics.test.ts`** (append inside the existing
`describe('buildEpistemicsBlock', ...)` block, after the existing 3 `it(...)`s):

```ts
  it('F-126: honors an explicit null confidence_band instead of defaulting to medium', () => {
    const block = buildEpistemicsBlock({
      surgical: true,
      confidence_band: null,
      empty_reason: 'No rows matched.',
    })
    expect(block.confidence_band).toBeNull()
    expect(block.empty_reason).toBe('No rows matched.')
  })

  it('F-126: empty_reason is null when confidence_band is set (non-null)', () => {
    const block = buildEpistemicsBlock({ surgical: true, confidence_band: 'high' })
    expect(block.empty_reason).toBeNull()
  })
```
Today: the first case fails to compile/type-check (`confidence_band: null` is not assignable
to the current `'high' | 'medium' | 'low'` param type) and, if the type were loosened without
the `in params` fix, would incorrectly return `'medium'` via the old `??` default — either way
it does not produce `confidence_band === null` today. After the fix: passes.

Finally, add one handler-level case to the existing
**`platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/query_life_events.test.ts`**
(append inside the existing `describe(...)` block):

```ts
  it('F-126: sets is_empty + empty_reason when a text search matches zero rows', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'marriage relationship spouse partner wedding' },
      {},
    )
    expect(result.is_error).toBe(false)
    expect(result.is_empty).toBe(true)
    expect(result.empty_reason).toContain('No life_events rows matched')
  })
```
Today: `result.is_empty` is `undefined` (the field does not exist on the handler's return
today) — `expect(undefined).toBe(true)` fails. After the fix: passes.

## 6. Recurrence guard

Test 7 (§5) is the recurrence guard for the specific regression this fix could introduce
("always null now") — it pins that a genuinely non-empty result still reports `'high'`.
For the broader defect class (a future 5th `buildEpistemicsBlock` call site hardcoding
`'high'` again without consulting emptiness), no static lint is proposed in this spec — the
five call sites are enumerated and finite (§4's table), and `buildEpistemicsBlock`'s own
JSDoc (§3f) now states the discipline inline at the one shared builder every call site must
route through. Recommend, as a follow-up (not blocking this spec): a
`platform/scripts/governance/` grep-based CI guard asserting no `buildEpistemicsBlock(` call
site passes a bare string literal `'high'` without a preceding conditional — mirroring the
`fact-category-pin-lint` pattern (§N.7 item 2) — filed as a new residual, not built here.

## 7. Dependencies and rollback

**Dependencies:** none. No DB migration. No other PARIŚEṢA lane must land first — `types.ts`,
`shared_types.ts`, `tool_name_bridge.ts`, `epistemics.ts`, and the four route files are not
claimed by any other in-flight F-nn lane per the plan's §2 OWNS lists (cross-checked against
§2.1's four listed lease conflicts — none involve these files). §3a/§3c/§3e/§3f/§3g/§3h are
inside S1's `platform/src/app/api/mcp/primitives/**` + shared-MCP-helper scope (this spec's
routing target); §3b is the one S3-owned file, built in the same commit.

**Rollback:** revert the single commit. All changes are additive (new optional interface
fields) or narrowly conditional (the `route.ts`/`recent/route.ts` epistemics-block
construction). No existing caller that ignores `empty_reason` or treats a `null`
`confidence_band` as falsy-and-therefore-absent breaks — `EpistemicsBlock.confidence_band`
was already an optional-shaped field from a consumer's perspective (nothing in the codebase
was found, via `grep -rn "confidence_band" platform/src platform-mcp/src`, to assert
`typeof confidence_band === 'string'` or otherwise reject `null`; VERIFIER should re-run that
grep at review time to confirm no consumer added since this spec was written).

## 8. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element |
|---|---|
| C1: `mimamsa_lel_query` returns `epistemics.confidence_band='high'` on a query that matched zero rows | §3b (LEL handler declares `is_empty`) + §3d (threads it through) + §3g (route reads it, no longer hardcodes `'high'`) + Exit test §5 |
| C2: the LEL corpus is populated for this chart (the empty result is an honest "no matching event recorded," not "no events exist"), so a `'high'` stamp risks being read as an established negative | §3b's `empty_reason` text is explicit that the filters/search matched nothing — never implies the corpus itself is empty or that the underlying life event doesn't exist; §2's design-decision writeup states this is the exact harm being fixed |
| C3: no `empty_reason` (or equivalent) exists anywhere to distinguish "zero rows matched" from "corpus is empty" — the `density_contract`/CLAUDE.md §N.6 item 4 discipline the surface is missing | §3e (adds `empty_reason` to `EpistemicsBlock`) + §3f (adds it to the builder) + §3a/§3c (adds the underlying `is_empty`/`empty_reason` passthrough contract) |
