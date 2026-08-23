---
artifact: F-06_DIAGNOSIS
lane: F-06
stream: S5 MULA
class: CL-03 (no-op params)
severity: TIER2-HONESTY
status: CONFIRMED-LIVE
updated: 2026-08-16
---

# F-06 — DIAGNOSIS: `ref_remedies_chart_get` is not chart-specific

## 1. Live reproduction

Called `mcp__marsys-jis-direct__ref_remedies_chart_get({affliction:'Saturn', top_k:5})`.
Raw JSON saved to `lanes/F-06/repro_raw.json`.

- **Call 1** (`{affliction:'Saturn', top_k:5}`) — succeeds, returns 5 rows from the global
  `brahma_remedy_corpus` (planet/domain `ILIKE 'Saturn'`). Response `provenance.note` reads
  *"No audience_tier gating — serve-time only"* — no chart scoping anywhere in
  `invocation_params`, `result`, or `provenance`.
- **Call 2** (same args + `chart_id: '482012f1-710e-4a25-994a-93821f5871aa'`, the canonical
  chart) — **hard rejected** before it reaches the server:
  `MCP error -32602: ... "unrecognized_keys", "keys": ["chart_id"], "message": "Unrecognized key: \"chart_id\""`.
  The Zod schema fetched for this tool is `additionalProperties: false` with only
  `{affliction: string (required), top_k: integer (optional)}` — `chart_id` isn't silently
  dropped, it's structurally impossible to send.

**Verdict: CONFIRMED-LIVE.** Not already fixed. Checked for an in-flight fix first (session
memory surfaced a "PR #829 remedy chart scope fix" note) — traced it to
`35aecdccc` / branch `origin/parishodhana/b1-remedy-chart-scope`, which only touches
`bodha_remedies_get` (tradition/remedy_category OR-match, `platform/.../L2_bodha/query_remedies.ts`)
— a different tool entirely, unrelated to `ref_remedies_chart_get` / `query_remedies_for_chart`.
No branch or commit touches `register_d7_channel.ts:1437-1526` or the alias at
`register_p1_aliases.ts:1563-1573`.

## 2. Claim decomposition

| # | Assertion | Verified |
|---|---|---|
| a | Tool description promises chart-specific scoping | TRUE — `register_p1_aliases.ts:1565`: `'[Phase-1 alias] Chart-specific remedy suggestions (same as query_remedies_for_chart).'` |
| b | MCP-facing schema doesn't expose `chart_id` at all | TRUE — schema is `{affliction, top_k}` only; live probe confirms hard rejection, not silent drop |
| c | Underlying primitive's optional `chart_id` isn't used in the SQL WHERE clause (provenance-only) | TRUE — see mechanism below; `chart_id` only ever lands in the response object for logging, never in a query parameter |

## 3. Mechanism (file:line, current — matches audit corpus)

**MCP alias** — `platform-mcp/src/tools/register_p1_aliases.ts:1563-1573`:
```ts
server.tool(
  'ref_remedies_chart_get',
  '[Phase-1 alias] Chart-specific remedy suggestions (same as query_remedies_for_chart).',
  { affliction: z.string().describe('Planet name or domain keyword'), top_k: z.number().int().optional() },
  async ({ affliction, top_k }) => {
    try {
      const data = await callPlatformPrim('query_remedies_for_chart', { affliction, top_k }, principal)
      return dualOutput(data)
    } catch (err) { return errOut('ref_remedies_chart_get', String(err)) }
  }
)
```
Line numbers confirmed exact (audit said 1563-1573; matches). The Zod input object literally has
no `chart_id` key, and the destructured handler args (`{ affliction, top_k }`) can't forward one
even if a caller found a way to smuggle it past `additionalProperties:false`.

**Server-side capability/handler** — `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1437-1526`
(`queryRemediesForChartCapability`, backs `query_remedies_for_chart`):
- `input_schema` (1453-1468) — `chart_id` declared but explicitly documented as decorative:
  ```ts
  chart_id: {
    type: 'string',
    description: 'Chart UUID (<chart_uuid>). Optional — used for provenance logging only, not for data filtering.',
    required: false,
  },
  ```
  (line 1454-1458; audit's "1453-1468" range matches — this sub-block starts at 1454 inside the
  1453-1468 `input_schema` span)
- `required_inputs: ['affliction']` (1470) — chart_id isn't even in the required set, consistent
  with "optional, decorative."
- Handler (1486-1525): `chart_id` is read at 1487 with an inline comment `// optional —
  provenance only`, then used ONLY at 1518/1522 to echo it back into the response/error object —
  never passed into the `query()` call's parameter array.
- SQL at 1495-1504 — confirmed no `chart_id` predicate:
  ```sql
  SELECT remedy_id, planet, domain, category, deity,
         prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
         cost_tier, contraindications, source_canonical_id, source_citation,
         classical_attestation_text
  FROM brahma_remedy_corpus
  WHERE planet ILIKE $1 OR domain ILIKE $1
  ORDER BY confidence DESC NULLS LAST, cost_tier ASC
  LIMIT $2
  ```
  Only two bind params (`$1` = `%affliction%`, `$2` = topK) — `chart_id` never appears as a bind
  var. `brahma_remedy_corpus` is itself a global (L0/Brahmagyan) reference table with no
  `chart_id` column, so there is no per-chart row to scope to even in principle — this is a
  design-level mismatch between the tool's name/description and its actual (correctly global)
  L0 corpus lookup, not a one-line bug.

Audit's mechanism description is accurate; no line-number corrections needed on either file.

## 4. Sibling census

Searched both files for the same defect shape: **`chart_id` declared "for provenance only" /
optional-and-decorative, with no corresponding `WHERE chart_id = ...` predicate.**

- `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts` — grepped every
  `chart_id` occurrence (46 hits) and every "provenance only" comment (3 hits, all inside
  `queryRemediesForChartCapability`, lines 1448/1456/1487). **Result: 0 siblings.** Every other
  `chart_id` in this file (the signal-corroboration handler ~641-741, the `chart_facts_query`
  handler ~793-1423) is genuinely required (`required_inputs: ['chart_id', ...]`) and is bound
  into real `WHERE chart_id = $1` predicates (lines 979, 1039, 1061, 1072, 1188, 1190, 1250-1251,
  1294). `queryRemediesForChartCapability` (1437-1526) is the **only** capability in this file
  with the provenance-only pattern.
- `platform-mcp/src/tools/register_p1_aliases.ts` — grepped `provenance` (3 hits, all unrelated:
  R5.1 C2 posterior-provenance / edge_strength provenance, not chart_id) and `chart-specific`
  case-insensitively (1 hit — line 1565, this tool). No other alias in this file's remedy block
  (`ref_remedies_get`, `ref_remedies_by_category_list`, `ref_remedy_get`,
  `ref_tantric_remedies_get`, `ref_remedies_by_planet_get`, `ref_mantras_get`,
  `ref_remedies_search`) claims chart-specificity or accepts a decorative `chart_id` — they're
  all correctly-described global corpus lookups.

**Sibling count: 0.** F-06 is an isolated, singleton defect (one tool's description overclaims;
the underlying capability + alias are both internally consistent about being global — only the
description lies).

**Description-string check (item 4 of the contract):** confirmed — `register_p1_aliases.ts:1565`
literally reads `'[Phase-1 alias] Chart-specific remedy suggestions (same as query_remedies_for_chart).'`.
This is the one and only "chart-specific" claim found in either file, and it is the false one.

## 5. Blast radius

- `register_p1_aliases.ts` is currently **leased to S1** (CL-11 `dualOutput` sweep, ~19 sites)
  per `LEDGER_S5.md`. Any fix touching the alias registration at lines 1563-1573 — e.g. removing
  the "Chart-specific" claim from the description, or (if a real chart-scoped remedy join is ever
  wanted) adding a genuine `chart_id` param — must wait for `PAR-register_p1_aliases-RELEASE`
  before S5 can edit it. Diagnosis-only per this lane's contract; no edit attempted.
- `register_d7_channel.ts` is not under a lease noted in `LEDGER_S5.md` — the capability-side fix
  (correcting the `input_schema` description at 1456-1458 to stop implying data-filtering, and/or
  dropping the decorative `chart_id` param entirely since `brahma_remedy_corpus` has no per-chart
  column) is independently actionable once specced, no cross-stream wait needed there.
- **Two independent remediation shapes** worth flagging to the spec stage: (1) minimal/honest fix
  — reword both the alias description and the capability description to state plainly this is a
  global corpus lookup, drop the decorative `chart_id` field from the capability schema entirely
  (it does nothing); (2) build-out fix — if chart-specific remedies are actually wanted (e.g.
  joining against the chart's afflicted planets/houses from `chart_facts` or `bodha_*` signals),
  that's new scope, not a no-op-param cleanup, and should be raised as a separate finding/backlog
  item rather than folded into this CL-03 fix.
