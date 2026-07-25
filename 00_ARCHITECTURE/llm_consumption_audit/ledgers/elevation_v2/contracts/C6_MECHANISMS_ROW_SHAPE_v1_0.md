---
contract_id: C6
title: mechanisms row shape + the returns-200 guarantee
version: 1.0
status: FROZEN
authored_by: RUNWAY session (non-participant, charter M2.4)
grounded_in:
  - platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts (full file, esp. L27-33, L131-137, L155-205)
  - platform-mcp/src/tools/register_p1_aliases.ts:975-1012 (bodha_mechanisms_get MCP registration)
---

# C6 — mechanisms row shape + the returns-200 guarantee

## Problem this closes
`bodha_mechanisms_get` already has a stable row shape and an existing "correct negative, not an
error" design — this contract FREEZES both so downstream streams build against a fixed target
instead of the current implementation drifting under them mid-campaign.

## Frozen row shape (verbatim from `query_mechanisms.ts` SQL SELECT, L131-137)

```ts
export type MechanismRow = {
  mechanism_id: string;
  ayanamsha_id: string;
  snapshot_type: string;
  mechanism_name: string;
  mechanism_class: string;
  valence: string;
  member_node_ids_array: string[];
  member_edge_ids_array: string[];
  domains_affected_array: string[];
  edge_strength_avg: number;
  edge_strength_min: number;
  edge_strength_max: number;
  edge_strength_formula_version: string;
  constituent_ga_vichara_ids_array: string[];
  centrality_summary_jsonb: Record<string, unknown>;
  source_motif_id: string;
  verification_pass_status: 'pass';       // frozen: query_mechanisms.ts L27-29 — every
                                            // bodha_mechanisms row is 'pass'; there is NO
                                            // catalog-only/confirmed split in this table.
                                            // Do not add a receipt gate here (see C2 note below).
  citation_ref: string;
  citation_human: string;
  is_chain_circuit: boolean;
};
```

## Frozen envelope shape (verbatim from L180-200)

```ts
export type MechanismsResponse = {
  chart_id: string;
  rows: MechanismRow[];
  count: number;
  total_matching: number;
  more_available: boolean;
  chain_circuit_count: number;
  facets: {
    by_mechanism_class: Record<string, number>;
    by_valence: Record<string, number>;
    chain_circuit_classes: Record<string, number>;
  };
  empty_reason?: string;                   // set iff total_matching === 0; NOT an error
  filters: Record<string, unknown>;
  provenance: Record<string, unknown>;
};
```

## The returns-200 guarantee (frozen behavior)

1. `query_mechanisms.ts` wraps its body in `try { ... } catch (err) { return {content:{error, chart_id}, is_error:true} }`. An in-band `is_error:true` is the ONLY failure signal — there is no HTTP-level failure path this contract can or should introduce (MCP transport always returns 200; `is_error` is the protocol-correct in-band signal, per L155-205).
2. Zero matching rows is explicitly NOT an error: when `total_matching === 0`, `empty_reason` is set to a descriptive string and the response returns with `is_error:false`, `rows:[]` (L174-178). Any stream touching this handler MUST preserve this — an empty mechanism set is a correct answer ("no adverse mechanisms found"), not a failure, and must never be silently converted to an error or a hollow envelope with no `empty_reason`.
3. The outer MCP alias wrapper (`register_p1_aliases.ts:996-1010`) has its own `try/catch` → `errOut('bodha_mechanisms_get', String(err), {chart_id})`, preserving the same two-layer in-band error convention. Any refactor MUST keep both layers — do not collapse them into one, and do not let the outer layer swallow the inner `empty_reason`.

## Non-goals
- Does NOT add a `CategoryReceipt` (C2) gate to this table — `verification_pass_status='pass'` is
  invariant here (L27-29 explicitly documents no catalog-only split exists), so C2's
  confirmed/catalog-only distinction does not apply to `bodha_mechanisms_get`.
- Does NOT change `facets` key names — any stream adding new facets appends new keys, never renames
  `by_mechanism_class`/`by_valence`/`chain_circuit_classes`.
