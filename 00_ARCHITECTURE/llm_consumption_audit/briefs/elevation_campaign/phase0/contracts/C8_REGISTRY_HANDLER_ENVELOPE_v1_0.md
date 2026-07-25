---
contract_id: C8
title: registry handler signature + post-trim envelope shape
version: 1.0
status: FROZEN
authored_by: RUNWAY session (non-participant, charter M2.4)
grounded_in:
  - platform/src/lib/retrieval/registry/types.ts:518-536 (CapabilityHandler, ToolResult, CapabilityContext — FROZEN file, amendment_version 3)
  - platform-mcp/src/lib/response_budget.ts (hardFloor / TrimmableSection trim machinery)
  - platform/src/lib/retrieval/envelope.ts (JUDGMENT_FLAG_CODES closed enum)
  - platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1155-1225 (pivoted-row shape)
  - C2 (CategoryReceipt — this contract defines the receipt_state enum C2 references)
---

# C8 — registry handler signature + post-trim envelope shape

## 1. Registry handler signature (frozen — verbatim from `types.ts:525-528`, unchanged by this contract)

```ts
export type CapabilityHandler = (
  args: Record<string, unknown>,
  context?: CapabilityContext
) => Promise<ToolResult>;

export type ToolResult = { content: string | object; is_error?: boolean; metadata?: Record<string, unknown> };
export type CapabilityContext = { chart_id?: string; request_id?: string };
```

`types.ts` is itself FROZEN (header L7-19, `amendment_version: 3`) — this contract does not amend
it. Any new capability implements exactly this signature; no stream may introduce a second handler
type.

## 2. The four receipt states (frozen, closed enum — mechanically derived, referenced by C2)

```ts
export type CategoryReceiptState =
  | 'CONFIRMED'      // confirmed_count > 0, catalog_only_count === 0, dark_count === 0
  | 'CATALOG_ONLY'    // confirmed_count === 0, catalog_only_count > 0, dark_count === 0
  | 'DARK'            // confirmed_count === 0, catalog_only_count === 0, dark_count > 0
  | 'MIXED';          // any other combination (more than one of the three counts > 0)
```

Derivation is mechanical and total — every `(confirmed_count, catalog_only_count, dark_count)`
triple maps to exactly one state (the `(0,0,0)` triple, meaning the category was never touched, is
not assigned a state — the `CategoryReceipt` for it is simply omitted from `CategoryReceiptSet`,
per C2 rule 2). No handler may invent a fifth state or leave `receipt_state` free-form.

## 3. Pivoted-row shape (frozen — verbatim from `register_d7_channel.ts:1164-1171,1212-1222`)

```ts
export type PivotedFactRow = {
  fact_subject: string;
  fact_category: string;
  [factKey: string]: unknown;          // spread facts, keyed by fact_key
  fact_ids: Record<string, string>;    // fact_key -> chart_facts.fact_id, for traceback (B.3 ledger)
};
```

Any capability offering a `shape='pivoted'` output mode (mirroring `chart_facts_query`) MUST use
this exact shape — `fact_subject`/`fact_category` first, facts spread flat, `fact_ids` last, never
renamed.

## 4. Immune honesty-field set (frozen — fields that survive ANY `budget_kb` trim)

Per §N.6 ("density signaling is data, not narration") and the existing `hardFloor` precedent in
`response_budget.ts` (which protects array *sections* from zeroing), this contract extends the same
guarantee to scalar/flag fields: the following fields, when present on a response envelope, are
**immune to trimming** — `applyResponseBudget`/`finalizeMcpBudget` MUST NEVER remove or truncate
them, regardless of `budget_kb` (C1) or the tool's static ceiling:

```ts
judgment_flags: string[];                 // closed vocab, JUDGMENT_FLAG_CODES (envelope.ts)
empty_reason?: string;                    // present iff the response is a correct-negative (C6 §2)
catalog_only_rows_in_page?: number;       // existing get_yoga_dosha.ts convention
catalog_only_note?: string;
receipt_state?: CategoryReceiptState;     // per-category, when CategoryReceiptSet (C2) is present
budget_kb_applied?: number;               // C1
budget_kb_requested?: number;             // C1
trim_report: TrimReportEntry[] | null;    // existing response_budget.ts output — must itself report
                                           // truthfully, never be trimmed away to hide that trimming happened
```

Rationale: a trimmer that can zero out the very fields that disclose trimming occurred (or that a
result is an honest empty) defeats the purpose of trimming transparently — this is the scalar-field
analogue of the `hardFloor` array-section protection §N.6 already documents, made explicit and
closed so no stream has to guess which fields are safe to drop under pressure.

## Non-goals
- Does NOT change `TrimmableSection`/`hardFloor` array-section behavior — this is additive scope
  (scalar fields), not a rewrite of the existing array-trimming path.
- Does NOT mandate every capability emit every field in the immune set — only that whichever of
  these fields a capability DOES emit are never subsequently trimmed away.
