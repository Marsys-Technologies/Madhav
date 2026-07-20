---
artifact: LANE_D_REPORT.md
lane: D — MCP edge & adaptivity reality (plan §1.4/§1.5, R-4)
governing_brief: RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §E Lane D
audit_subject: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (v1.2) §1.4, §1.5
status: COMPLETE
scope: READ-ONLY on platform/** and platform-mcp/**; no writes, no DB, no deploys
---

# Lane D Report — MCP Edge & Adaptivity Reality

## Per-claim verdicts

### 1. Surface-spec fetched-and-discarded — CONFIRMED

`platform-mcp/src/server.ts:282-304` (M6.2 block):

```
282  // M6.2: Fetch the surface spec for the effective family.
283  // Non-blocking: surface spec is advisory for shaping; failure falls back to serving all tools.
285  let responseFormat: 'minimal' | 'standard' | 'detailed' = 'standard'
287    const surfaceResult = await callPlatformSurfaceSpec(effectiveFamily)
288    if (surfaceResult.status === 200 && surfaceResult.envelope.ok) {
289      const spec = surfaceResult.envelope.result as Record<string, unknown> | null
290      if (spec && typeof spec['response_format'] === 'string') {
...
293          responseFormat = rf
301  // Pass effectiveFamily + responseFormat to tools that accept them.
303  void effectiveFamily
304  void responseFormat
```

The plan's exact line range (287-304) is verified verbatim. `effectiveFamily` and
`responseFormat` are computed, then both are explicitly discarded via `void`
statements — the comment at line 301 ("Pass ... to tools that accept them") is
aspirational, not implemented. Nothing downstream in `server.ts` reads either
variable. **Additional finding not in the plan**: the code reads a
`response_format` key off the surface-spec JSON — but `McpSurfaceSpec` (see
claim 2 below, `platform/src/lib/retrieval/maro/normalizer.ts:340-347`) has no
`response_format` field at all. The plan states this ("It even reads a
`response_format` field the spec never contains") — CONFIRMED exactly.

### 2. `max_tools` non-enforcement — CONFIRMED, with a load-bearing nuance

`grep -rn "max_tools"` across `platform-mcp/` and `platform/src/lib/mcp/` shows
`max_tools` is **only** consumed in
`platform/src/lib/mcp/bundle_adapters.ts` (lines 75-79, 330, 341, 397, 461-462,
514) — and there it caps the **internal sub-tool fan-out of a single composite
bundle call** (e.g. how many of the 8 holistic sub-tools `bodha_domain_reading_get`
fires internally, or how many schools `cross_school_lookup` iterates). It is
never read anywhere that trims the **`tools/list` surface** a client sees.
`platform-mcp/src/server.ts` has no `ListToolsRequestSchema` handler at all —
tool registration is via the SDK's `McpServer.tool(...)` calls
(`registerL0BrahmagyanTools`, etc.), which the SDK auto-lists in full; there is
no code path that slices this list by `max_tools`. **Gap in the plan's framing**:
the plan says "`max_tools` is never enforced" without qualification — reality is
`max_tools` IS enforced, but only for internal bundle fan-out, never for the
tool-list surface. The plan should distinguish these two enforcement points
explicitly (R-4.1 needs both).

### 3. Zero MCP annotations — CONFIRMED

`grep -rn "readOnlyHint\|idempotentHint\|destructiveHint\|openWorldHint"` across
`platform-mcp/` and `platform/src/` returns zero matches. No tool registration
call anywhere passes an `annotations` object to `server.tool(...)`. CONFIRMED
exactly as stated.

### 4. `behavioral_overrides` single use — CONFIRMED

`grep -rn "behavioral_overrides:"` across
`platform/src/lib/retrieval/registry/` (population sites, i.e. object-literal
assignment, not field declarations) returns exactly one hit:
`platform/src/lib/retrieval/registry/layers/dprofiles_registration.ts:99`. The
field is *declared* in the `CapabilityDescriptor` type twice
(`platform/src/lib/retrieval/registry/types.ts:193` and `:381` — two distinct
descriptor interfaces) and *consumed* generically in
`platform/src/lib/retrieval/maro/normalizer.ts:52-72`
(`applyBehavioralOverrides`, a no-op unless a descriptor sets it) — but only
one descriptor in the whole registry ever sets it. Plan's count of 1 is
CONFIRMED. `drill_children` and `output_schema` counts were not directly
re-verified this pass (out of Lane D's core claim list) — flagged
UNVERIFIABLE-NOT-CHECKED, defer to Lane A/B territory (they audit the
registry/envelope surfaces more broadly).

### 5. Description length distribution + native row-count leakage — CONFIRMED, and the instance list is materially larger than the plan states

The plan names three examples (66,738 / 27,554 / 5,566). Direct grep for
description-field-embedded native chart magic numbers across
`platform/src/lib/retrieval/registry/layers/**/*.ts` and
`platform-mcp/src/tools/*.ts` finds **at least 11 distinct instances across 8
files** (excluding tests/comments, `description:`-field hits only):

| # | File:line | Tool/capability | Embedded figure |
|---|---|---|---|
| 1 | `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:770` | `chart_facts_query` | "27,554 rows per chart" |
| 2 | `register_d7_channel.ts:785` (same description array) | `chart_facts_query` | "5,566-subject set" |
| 3 | `platform-mcp/src/tools/registry_bridge.ts:1658` | `query_chart_facts` (MCP tool) | "27,554 rows per chart" |
| 4 | `platform-mcp/src/tools/register_p1_aliases.ts:913` | `ganita_chart_facts_get` (P1 alias) | "5,566 subjects" |
| 5 | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts:208` | `query_signals` | "66,738 signals for the canonical chart" |
| 6 | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:28` | `query_temporal_activation` | "66,738 rows" (×2, both `kala_activation` and `kala_activation_predicates`) |
| 7 | `platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts:31` | `query_activation_waveform` | "~79,728 rows/chart" |
| 8 | `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts:25` | `query_convergence_windows` | "19,482 rows per chart" |
| 9 | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:123` | `get_dashas` | "Contains 601,443 rows for the native" |
| 10 | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_divisionals.ts:19` | `get_divisionals` | "Contains 21,635 rows for the native" |
| 11 | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/ephemeris_cache_native_lifetime.ts:29` | `ephemeris_cache_native_lifetime` (resource) | "~157,266 rows" |

**New finding beyond row counts (elevate to the plan's gap list)**: the same
`ephemeris_cache_native_lifetime.ts` description (lines 24-29) embeds the
native's **full PII** directly in a served resource description string:
`"Native: Abhisek Mohanty, born 1984-02-05 10:43 IST, Bhubaneswar, Odisha,
India."` This is a stronger violation of "chart-agnostic descriptions" than a
row count — it is the native's name, DOB, birth time, and birthplace, verbatim,
in metadata served to every client regardless of chart context. Cross-check
against `CLAUDE.md §B`: this matches Abhisek Mohanty's canonical birth facts
exactly, confirming it is not a placeholder.

**Also flagged (adjacent, weaker case)**: `register_d8_assess_domain.ts:420-426`
embeds a native-derived count ("native chart 0/13,364 dated on lahiri") inside
a served `empty_reason` string (`TEMPORAL_EMPTY_REASON`), not a `description`
field — same class of leak (native-specific figures in machine-readable text
served to every caller) but via a different code path (dynamic empty-reason
construction vs static tool description). Worth the plan's chart-agnostic gate
widening its scan beyond `description:` fields.

**Discrepancy worth flagging to Lane E / GROUND_TRUTH register**: `get_dashas.ts:123`
states "601,443 rows for the native across all systems, levels and
ayanamshas," which does not match `CLAUDE.md §E`'s canonical L1 seal figure
`chart_dashas=536,471`. Either the description is stale (pre-dates a dasha
writer change) or counts a superset (e.g. including a derived view). Not
adjudicated here — flagged as a NEW-GAP for reconciliation, since it is a
second-order finding: not just "native data embedded" but "native data
embedded AND apparently wrong."

Length distribution: spot-measured description strings run 100 bytes (a single
sentence) up to full arrays of 10-20 template-literal-joined strings per tool
(e.g. `chart_facts_query`'s description array in `register_d7_channel.ts` spans
lines 769-792, several hundred bytes to ~1-2KB once joined) — consistent with
the plan's "1-2KB each" characterization. `registry_bridge.ts` (178KB total
file) and `register_d7_channel.ts` (91KB) carry the highest per-file
description density among the files sampled.

### 6. `listCapabilities` filter gap — CONFIRMED, broader than stated

`CapabilityFilter` (`platform/src/lib/retrieval/registry/types.ts:318-326`)
declares seven filterable fields: `type`, `layer`, `name_prefix`, `scope`,
`archetype`, `traversal_level`, `tool_role`. The implementation
(`platform/src/lib/retrieval/registry/index.ts:52-61`) only checks three:

```ts
return all.filter((cap) => {
  if (filter.type && cap.type !== filter.type) return false
  if (filter.layer && cap.layer !== filter.layer) return false
  if (filter.name_prefix && !cap.name.startsWith(filter.name_prefix)) return false
  return true
})
```

`scope`, `archetype`, `traversal_level`, and `tool_role` are silently accepted
by the type signature and silently ignored by the filter body — a caller
passing e.g. `{ archetype: 'orientation_digest' }` gets back the full
unfiltered list with no error, warning, or partial-match flag. Plan names
three of the four ignored fields (`archetype`/`tool_role`/`traversal_level`);
`scope` is a fourth ignored field the plan misses — CORRECTION for the
register.

### 7. Fail-open dev token — CONFIRMED, and it is a repeated pattern (13 files), not a single site

The exact code at the plan's cited `route.ts:34-35` matches
`platform/src/app/api/mcp/asset/route.ts:33-36`:

```ts
33  const expected = process.env.MCP_INTERNAL_TOKEN
34  if (!expected) {
35    if (process.env.NODE_ENV === 'development') return true
36    console.error('[mcp:asset] MCP_INTERNAL_TOKEN not set in production')
```

Mechanism, precisely: the fail-open only fires when `MCP_INTERNAL_TOKEN` is
**unset** in the environment AND `NODE_ENV === 'development'` — at that point
`validateServiceToken` returns `true` unconditionally, i.e. it does not check
the presented token at all (missing header, wrong header, anything passes).
This is a narrower trigger than "any invalid token in dev mode" (a caller
presenting a *wrong* token when `MCP_INTERNAL_TOKEN` IS set still gets
rejected via `token === expected`) — but the plan's framing ("fails open") is
directionally correct: an operator who forgets to set the secret in a
dev-flagged deploy gets zero enforcement, silently.

**Gap the plan doesn't surface**: this exact `if (!expected) { if (NODE_ENV
=== 'development') return true ...}` pattern is duplicated verbatim across at
least 13 route files (grep count of `NODE_ENV === 'development'` inside
`validateServiceToken`-style functions): `asset/route.ts`, `authz/route.ts`,
`session/route.ts`, `recent/route.ts`, `sessions/route.ts`,
`keys/validate/route.ts`, `db/query/route.ts`, `oauth/tokens/route.ts`,
`oauth/codes/route.ts`, `oauth/clients/route.ts`, `my/charts/route.ts`,
`writes/[action]/route.ts`, `trace/[trace_id]/route.ts`,
`primitives/[tool]/route.ts`. The plan's R-0.5 "one-liner" framing understates
the fix surface — this is 13+ copy-pasted call sites, not one. R-0.5 should
either extract a shared `validateServiceToken` helper (killing the
duplication) or explicitly enumerate all sites in its acceptance criteria.

### 8. Plan-surface entitlement bypass — CONFIRMED

`platform-mcp/src/tools/register_vidhi_plan.ts` (`plan_retrieval` tool
handler, lines 61-115): the handler takes `chart_id` as a required UUID
(line 75), calls `buildVidhiPlan({chart_id, question, scope_tuple,
observations})` directly, and returns the compiled plan. `grep -n
"entitle\|authorize"` over this file and over
`platform-mcp/src/resources/vidhi/plan_builder.ts` returns zero hits in either
— no `authorizeChartAccess`/`remoteAuthorize` call anywhere in the
`plan_retrieval` code path. Contrast with `§3.6` of the MCP handoff, which
documents `authorizeChartAccess`/`remoteAuthorize` as the standard per-chart
gate used elsewhere (e.g. `recall_session`) — `plan_retrieval` conspicuously
does not call it. CONFIRMED: any `chart_id` compiles a plan, no entitlement
check. (The `vidhi_plan` *prompt* — the stated primary path — was not
independently re-verified in this pass beyond the tool; the handoff §3.7
describes both as sharing the same `plan_builder.ts`, so the same gap almost
certainly applies to the prompt path too — flagged for Lane F/reconciliation
to confirm against the prompt registration code, which sits outside this
lane's file list.)

### 9. `parity_check` auto-pass — CORRECTED (mechanism is real but the plan's causal claim is imprecise, and the function appears unwired)

`platform/src/lib/retrieval/registry/parity_check.ts:51-61`:

```ts
export async function getMcpExportedUris(): Promise<Set<CapabilityUri>> {
  try {
    const { listMcpCapabilityUris } = await import('./mcp_capability_bridge')
    const uris = await listMcpCapabilityUris()
    return new Set(uris)
  } catch {
    // Bridge not available (standalone mode) — return empty set
    return new Set<CapabilityUri>()
  }
}
```

Confirmed: a failed bridge import returns an **empty** `mcpUris` set — this
part of the plan's claim is exactly right. But tracing `checkParity()`
(lines 69-104): `passed = missing_in_mcp.length === 0 && extra_in_mcp.length
=== 0`. If `mcpUris` is empty while `consumeUris` (the local registry,
normally populated with hundreds of capabilities once all `layers/*.ts` files
are imported) is non-empty, **every** consume URI lands in `missing_in_mcp` —
which makes `passed = false`, i.e. a **hard FAIL**, not an auto-pass. The
described "auto-pass (returns empty set)" behavior is only true in the
degenerate case where **both** sides are empty in that execution context
(e.g. a script that imports `parity_check.ts` without first importing the
layer files that populate `_registry` via `registerCapability` side effects) —
a real but narrower failure mode than "the bridge failing silently green-lights
CI." **Additional and arguably more important finding**: `grep -rln
"runParityCheck\|checkParity"` across the repo (including `.github/` if
present) finds no CI workflow, `package.json` script, or test file that
actually invokes `runParityCheck()` or `checkParity()` — the function has no
test file (`parity_check.test.ts` does not exist) and is not wired into any
CI gate found. `platform/src/scripts/manifest/parity_validator.ts` exists as a
separate, apparently newer manifest-parity mechanism and should be checked by
Lane A as the possible successor/replacement — `parity_check.ts` may be
superseded dead code rather than a live gate with a silent-pass bug. R-0.5's
"hard-fail when its import fails" fix should first confirm whether this file
is even in the enforcement path before patching it.

## Gaps found (summary, not already listed above)

- **G-D1 (new)**: native PII (name, DOB, birth time, birthplace) embedded
  verbatim in `ephemeris_cache_native_lifetime.ts`'s served resource
  description — worse than a row-count leak, and outside the chart-agnostic
  gate's current scan surface (see claim 5).
- **G-D2 (new)**: `get_dashas.ts`'s embedded row count (601,443) conflicts with
  `CLAUDE.md`'s canonical L1 seal figure (536,471) — a stale-or-wrong
  description, independent of the chart-agnostic-leak concern.
- **G-D3 (new)**: the dev-token fail-open is duplicated across 13+ route
  files, not fixable as a true one-liner; R-0.5 should either extract a shared
  helper or enumerate every site.
- **G-D4 (new)**: `parity_check.ts` may be dead/unwired code (no CI caller, no
  test file found) — the plan's R-0.5 fix item for it should first confirm live
  status; `parity_validator.ts` may already be the operative successor
  (Lane A territory to confirm).
- **G-D5 (new)**: `listCapabilities`'s ignored-filter set is four fields
  (`scope` + the plan's three), not three.
- **G-D6 (new)**: `max_tools` enforcement exists but only for internal bundle
  sub-tool fan-out (`bundle_adapters.ts`), never for the `tools/list` surface —
  the plan should track these as two separate enforcement gaps, since R-4.1
  needs a new code path for the surface-list case; the bundle-fan-out
  enforcement already works and should not be re-built.

## Per-family projection feasibility notes

The MCP-edge-facing surface spec (`getMcpSurfaceSpec`,
`platform/src/lib/retrieval/maro/normalizer.ts:340-372`) models exactly four
declared families plus a `universal` fallback (`ModelFamily` type,
`platform/src/lib/retrieval/maro/types.ts:24-29`): `anthropic`, `gemini`,
`openai`, `deepseek`. `McpSurfaceSpec` (lines 350-357) carries **six fields
today**:

| Field | What it holds today |
|---|---|
| `family` | the resolved `ModelFamily` |
| `max_tools` | soft-guidance count (`profile.max_active_tools`; universal fallback = 15) |
| `tool_name_pattern` | one hardcoded cross-family-safe regex (`^[A-Za-z0-9_.]{1,64}$`) — same for every family, not per-family |
| `requires_dual_output` | always `true` (structuredContent + text) |
| `strip_mcp_constructs` | per-family bool (DeepSeek needs MCP-construct stripping) |
| `transport` | `profile.mcp_transport` (`https_only` / `streamable_http` / `streamable_http_or_sse` / `none`) |

This is a materially richer sibling type, `FamilyNormalization`
(`platform/src/lib/retrieval/maro/types.ts:104-145`), used on the chat/bundle
path (not the raw-MCP-tools path) that already carries: `tool_arg_format`,
`tool_result_wire`, `cache_strategy`, `structured_output_format`,
`validate_and_repair`, `context_budget` (worker/mid/premium token tiers),
`reasoning_round_trip` (per-family artifact-passback mode — Anthropic
thinking/redacted_thinking, Gemini thought_signature, OpenAI
encrypted_content/previous_response_id, DeepSeek V4 reasoning_content),
`mcp_transport`, `prompt_structure`, `max_active_tools`,
`requires_json_parse`, `strip_mcp_constructs`, and an optional
`capability_overrides` (the `behavioral_overrides` consumption point, claim 4).

**Feasibility read for the elevation plan's R-4/R-1 amendments**:

- **What's buildable today without new fields**: per-family `max_tools`
  enforcement on the tool-list surface (the spec already carries the number —
  claim 2's gap is a missing consumer, not a missing field), per-family
  transport gating, and a coarse `strip_mcp_constructs` DeepSeek path — all
  already modeled.
- **What R-4's per-family dialect compiler (industry-consult row 4) needs that
  neither type carries today**: (a) a **JSON-Schema dialect enum per family**
  (OpenAI strict `additionalProperties:false`/all-required; Gemini OpenAPI
  subset with `$ref`/`anyOf` avoidance; DeepSeek strict-beta subset without
  `minLength`/`maxLength`) — `structured_output_format` on
  `FamilyNormalization` is the closest existing field but it describes
  *response* shape, not *input tool-schema* dialect; nothing today constrains
  how a tool's `input_schema`/Zod schema gets projected per family. (b) a
  **per-family name-constraint charset** — today one hardcoded
  cross-family-safe pattern is reused for all families (a defensive
  simplification that already avoids the OpenAI/Gemini conflict the
  industry-consult flags, but has no CI assertion — matches the consult's row
  5 "PARTIAL" verdict). (c) **reasoner-capability flags** (industry-consult
  row 17: DeepSeek reasoner can't call tools; R1 quirks) — absent from both
  `McpSurfaceSpec` and `FamilyNormalization`; the closest proxy is
  `mcp_transport: 'none'` for DeepSeek, which signals "no MCP" but not
  "this specific model variant can't call tools at all." (d)
  **`response_format` as a real field** — `server.ts` reads it hopefully from
  the surface-spec response, but it exists nowhere in `McpSurfaceSpec`; if R-4
  wants per-family response verbosity control this needs to be added to the
  type and threaded through, or the `server.ts` read should be deleted as
  dead code.
- **Bottom line**: the per-family dialect compiler is buildable as an
  **extension** of the existing `McpSurfaceSpec`/`FamilyNormalization` split
  (add dialect + reasoner-capability fields to one or both), not a rebuild —
  the family-resolution plumbing (`resolveFamily`, `getProfile`, the
  `x-mcp-model-family` header override in `server.ts:267-274`) already exists
  end-to-end and just needs its outputs consumed and its type surface widened.

## Model/effort ledger

- **Model**: sonnet (this agent), single pass, no sub-scouts spawned — the
  claim set was concrete enough (each claim names a file or a grep target)
  that direct file reads + targeted greps were faster and cheaper than
  fanning out subagents, and kept evidence chains auditable in one place.
- **Effort**: default/medium — mechanical verification throughout (file
  reads, grep, line-range confirmation); no generative judgment calls beyond
  characterizing severity and drafting the feasibility notes.
- **Files/greps touched** (representative, not exhaustive): `platform-mcp/src/server.ts`,
  `platform/src/lib/mcp/bundle_adapters.ts`, `platform/src/lib/retrieval/maro/normalizer.ts`,
  `platform/src/lib/retrieval/maro/types.ts`, `platform/src/lib/retrieval/registry/index.ts`,
  `platform/src/lib/retrieval/registry/types.ts`, `platform/src/lib/retrieval/registry/parity_check.ts`,
  `platform/src/lib/retrieval/registry/mcp_capability_bridge.ts`,
  `platform/src/app/api/mcp/{asset,authz,session,recent,sessions,keys/validate,db/query,oauth/*,my/charts,writes,trace,primitives,surface-spec}/route.ts`,
  `platform-mcp/src/tools/register_vidhi_plan.ts`, `platform-mcp/src/resources/vidhi/plan_builder.ts`,
  `platform-mcp/src/tools/registry_bridge.ts`, `platform-mcp/src/tools/register_p1_aliases.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`,
  `platform/src/lib/retrieval/registry/layers/{L1_ganita,L2_bodha,L3_kala,L0_brahmagyan}/*.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`.
  Zero writes to any of these; report is the only new file, per brief §H.

---
*End of LANE_D_REPORT.md — Lane D, Retrieval Audit Execution (RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0).*
