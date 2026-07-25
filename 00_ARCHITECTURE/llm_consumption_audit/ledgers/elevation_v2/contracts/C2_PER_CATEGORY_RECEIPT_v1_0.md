---
contract_id: C2
title: per-category receipt shape
version: 1.0
status: FROZEN
authored_by: RUNWAY session (non-participant, charter M2.4)
grounded_in:
  - platform-mcp/src/lib/completeness_receipt.ts (CompletenessReceipt, emitCompletenessReceipt)
  - platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts:255-296 (fire_reason/catalog_only pattern)
---

# C2 — per-category receipt shape

## Problem this closes
Two receipt-like shapes already exist and disagree: `CompletenessReceipt` in
`completeness_receipt.ts` is **plan-level** (`served`/`empty`/`dark` floor items, one receipt per
vidhi plan run); `get_yoga_dosha.ts` hand-rolls **inline envelope fields**
(`catalog_only_rows_in_page`, `dosha_label_gate`, `catalog_only_note`) with no shared type. Neither
is per-*fact-category*. This contract freezes a shape any capability can emit once per
`fact_category` it touches, without replacing either existing shape (both stay as-is; this is a new
third shape for a new use case: cross-category density transparency, per §N.6).

## Frozen type

```ts
export type CategoryReceipt = {
  fact_category: string;               // matches chart_facts.fact_category values (C3 census)
  confirmed_count: number;              // rows verification_pass_status='pass' or firings-authoritative
  catalog_only_count: number;           // rows fire_reason='requires_pass' / single-pass label matches
  dark_count: number;                   // floor items this category should have covered but didn't
                                         // (0 for categories with no floor obligation)
  receipt_state: CategoryReceiptState;  // see C8 for the enum this must be drawn from
  note?: string;                        // present iff catalog_only_count > 0 or dark_count > 0
                                         // (mirrors existing catalog_only_note convention)
};

export type CategoryReceiptSet = {
  categories: CategoryReceipt[];
  total_confirmed: number;
  total_catalog_only: number;
  total_dark: number;
};
```

## Rules (frozen)
1. `confirmed_count` and `catalog_only_count` are NEVER merged into a single number anywhere in a
   response — this is the same rule CLAUDE.md §N.6 point 1 already states for
   `ganita_yogas_get`/`get_yoga_dosha.ts`; C2 just makes it a reusable shape instead of a one-off.
2. A capability that emits `CategoryReceiptSet` MUST emit one `CategoryReceipt` per distinct
   `fact_category` actually touched by the query — never a single rolled-up total with no
   per-category breakdown.
3. `receipt_state` (see C8) is derived mechanically from the three counts — it is not a free-form
   string. A capability that cannot compute one of the three counts sets it to `0` and adds a
   `note` explaining why (never omits the field).
4. `CategoryReceiptSet` is additive to a response envelope — it does not replace `judgment_flags`,
   `empty_reason`, or the existing `CompletenessReceipt`. A response may carry more than one of
   these three receipt shapes simultaneously if it operates at more than one of the three levels
   (plan / category / envelope).

## Non-goals
- Does NOT retrofit `get_yoga_dosha.ts`'s existing inline fields — those stay as they are; new
  capabilities emit `CategoryReceiptSet` instead of inventing another inline variant.
- Does NOT define `dark_count` computation for categories with no defined floor — mechanism-owning
  streams define that per-domain; C2 only freezes the shape once computed.
