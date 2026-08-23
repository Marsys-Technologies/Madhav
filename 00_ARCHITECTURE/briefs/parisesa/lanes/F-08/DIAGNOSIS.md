---
lane: F-08
stream: S5 MŪLA
campaign: PARIŚEṢA
class: CL-03 no-op params
sibling_of: F-10 (exemplar lane, parallel)
severity: TIER2-HONESTY
status: CONFIRMED-LIVE
worktree: .claude/worktrees/par-s5-lead (clean cut from origin/main @ 5ff46c2a0)
stage: D (DIAGNOSE) — documents only, no code edits
---

# F-08 DIAGNOSIS — `phala_mitigation_get`'s `domain` parameter is a no-op

## 1. Live reproduction

Called `mcp__marsys-jis-direct__phala_mitigation_get` against the canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`, with and without `domain: 'career'`. Raw responses saved
to `lanes/F-08/repro_raw.json`.

| call | `result_hash` | `latency_ms` |
|---|---|---|
| `{chart_id}` (no domain) | `sha256:abbd452f1d8000a64259ea989f13fc56bd7e2feee92f139414f64890650a4d02` | 44 |
| `{chart_id, domain:'career'}` | `sha256:abbd452f1d8000a64259ea989f13fc56bd7e2feee92f139414f64890650a4d02` | 15 |

**Hashes are identical.** Matches the audit corpus's cited hash exactly. **NOT ALREADY-FIXED — confirmed live and current on `main`.**

## 2. Claim decomposition

| # | Assertion | Verdict | Evidence |
|---|---|---|---|
| (a) | `domain` accepted by the MCP alias's own schema | TRUE | `register_p1_aliases.ts:1741` — Zod schema literally declares `domain: z.string().optional()` |
| (b) | Never read at the primitive boundary | TRUE | `query_phala_calibration.ts`'s `queryRemedyProgramCapability` — see §3 |
| (c) | Byte-identical results with/without it | TRUE (confirmed live) | §1 above |
| (d) | No disclosure to the caller that domain was ignored | TRUE | Handler's own `filters` echo field (`query_phala_calibration.ts:419`) reports only `{ intensity_tier, limit, offset }` — `domain` is silently absent, not even echoed back as ignored. No warning in `warnings: []`, no `judgment_flags`-equivalent on this tool. |

## 3. Mechanism — file:line, current code (corrects two line numbers from the audit corpus)

**`platform-mcp/src/tools/register_p1_aliases.ts:1738–1749`** (corpus said 1739–1747; server.tool() call itself opens at 1738, closes 1749 — both in range, no correction needed to the cited span):

```ts
server.tool(
  'phala_mitigation_get',
  '[Phase-1 alias] L4 mitigation map — dosha/challenge mitigation paths (same as mitigation_map).',
  { chart_id: z.string().uuid().describe('Chart UUID'), domain: z.string().optional() },
  async ({ chart_id, domain }) => {
    if (!chart_id) return errOut('phala_mitigation_get', 'chart_id is required')
    try {
      const data = await callPlatformPrim('mitigation_map', { chart_id, domain }, principal)
      return dualOutput(data, 'phala_mitigation_get')
    } catch (err) { return errOut('phala_mitigation_get', String(err), { chart_id }) }
  }
)
```
This is correct — it forwards `{chart_id, domain}` in full. `callPlatformPrim` (same file, line 98–120) POSTs `JSON.stringify({ params })` verbatim to `/api/mcp/primitives/<tool>` — no schema-stripping in transit. **`domain` reaches the server intact.**

**`platform/src/lib/retrieval/registry/tool_name_bridge.ts:573`** (corpus said 565 — off by 8, corrected here):
```ts
// F-016: mitigation_map → query_remedy_program (L4 Phala phala_mitigation retrieval tool)
mitigation_map: 'query_remedy_program',
```
Pure name mapping, no param handling — not implicated.

**`platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`** — `queryRemedyProgramCapability` (corpus said 334–421; actual capability descriptor spans 334–427, `input_schema` 357–365, `handler` 369–426 — corrected here):

```ts
input_schema: {                                    // lines 357-365
  chart_id:       { type: 'string', ... required: true },
  intensity_tier: { type: 'string', ... },
  limit:  { type: 'number', ... },
  offset: { type: 'number', ... },
  // NOTE: no `domain` field declared at all
},
async handler(args: Record<string, unknown>, _ctx: unknown) {   // line 369
  const chart_id = args['chart_id'] as string
  const intensity_tier = args['intensity_tier'] as string | undefined
  const limit  = ...
  const offset = ...
  // `args['domain']` is never read anywhere in the 369-426 handler body
  const conds: string[] = ['chart_id = $1']
  if (intensity_tier) { conds.push(`intensity_tier = $${p++}`); params.push(intensity_tier) }
  // SQL WHERE clause has no domain predicate
  ...
  filters: { intensity_tier, limit, offset },        // line 419 — domain not even echoed
```

**Exactly which file drops it:** `query_phala_calibration.ts`. Not a schema-vs-handler mismatch within
that file (the § N.7-style "declared but unread" pattern) — `domain` isn't declared in this
primitive's own `input_schema` at all. The drop is a **cross-file contract mismatch**: the outer MCP
alias (`register_p1_aliases.ts`) promises a `domain` filter the inner primitive
(`query_phala_calibration.ts`) never agreed to accept. SQL, handler, and schema all agree with each
other — they just don't agree with the alias one hop up.

## 4. Sibling census

**Within L4_phala** (`platform/src/lib/retrieval/registry/layers/L4_phala/*.ts`): scripted check for
input_schema-declared-but-handler-unread fields across all 5 capability files (`query_domain_result.ts`,
`query_muhurat.ts`, `query_phala_calibration.ts`, `query_predictive_anchors.ts`,
`query_prospective_ledger.ts`) — **zero** within-file matches. Expected: F-08's defect isn't that
shape (see §3) — it's cross-file (alias schema vs. primitive schema), which a single-file grep can't
catch.

**Confirmed same-class sibling found by tracing every `callPlatformPrim(...)` call site in
`register_p1_aliases.ts` against its target primitive's own `input_schema`:**

- **`mimamsa_calibration_get`** — `register_p1_aliases.ts:1844–1857` — alias forwards
  `{chart_id, domain, limit, offset}` to primitive `query_calibration`
  (`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`). That capability's
  `input_schema` (lines 27–43) declares only `chart_id`, `include_held_out`, `promoted_only` — no
  `domain`, `limit`, or `offset` — and its handler (lines 64–139) never reads any of the three. Same
  defect class, same alias file, same forwarding pattern as F-08.

Other `callPlatformPrim` call sites in `register_p1_aliases.ts` (vector_search, query_remedies*,
lel_query, record_outcome, etc.) were spot-checked; their forwarded params were declared in the target
primitive's own `input_schema`. An initial broader regex sweep of the file also flagged ~46
candidates using non-`callPlatformPrim` call helpers (`callRegistryCap`, `callSidecarPath`), but a
spot-check (`catalog_assets_list`) showed those are false positives — the params ARE forwarded
correctly, my extraction pattern just didn't match those call sites' multi-line/nested-brace shape.
Not reporting that batch as confirmed findings.

**Sibling count: 1 confirmed same-class sibling** (`mimamsa_calibration_get` / `query_calibration.ts`),
plus the exhaustive `L4_phala/*.ts` internal check coming back clean.

## 5. Blast radius — lease determination

- **Fix point is `query_phala_calibration.ts`** (`queryRemedyProgramCapability`'s `input_schema` +
  handler + SQL) — under `platform/src/lib/retrieval/registry/layers/L4_phala/`, which per this
  campaign's assignment is **S3's lease (CL-13 disclosure lanes)**.
  → **`PAR-F-08-NEEDS-LEASE platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`**
- `register_p1_aliases.ts` and `tool_name_bridge.ts` (S5/S1 territory) are **not** the fix point —
  both already behave correctly (forward the param faithfully / map the name faithfully). No S5-owned
  change closes this finding on its own.
- The confirmed sibling (`query_calibration.ts`, under `L5_mimamsa/`) is a **second, separate lease
  question** — not L4_phala, ownership unconfirmed from this lane's brief. Flagging for the
  coordinator to route: **`PAR-F-08-SIBLING-NEEDS-LEASE platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`** (mimamsa_calibration_get domain/limit/offset no-op).
