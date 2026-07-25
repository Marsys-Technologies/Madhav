---
contract_id: C7
title: accounting invariant (Ω3 completeness contract, CI-assertable form)
version: 1.0
status: FROZEN
authored_by: γ (elev/gamma), per charter M2.4 (γ-owned, deadline T0+4h — see PROXY-RULED-002 in
  proxy/gamma.md for the honest deadline-overrun note)
grounded_in:
  - ELEVATION_CAMPAIGN_CHARTER_v2_1.md §0 (served ∪ explicitly-accounted-for = 100%)
  - ELEVATION_CAMPAIGN_CHARTER_v2_1.md §2/§5.γ Ω3 (the five-state completeness contract)
  - contracts/C2_PER_CATEGORY_RECEIPT_v1_0.md (per-fact_category receipt shape this extends)
  - contracts/C3_SCHEMA_MAP_OUTPUT_v1_0.md (the TCI seed C7 accounts against)
---

# C7 — accounting invariant

## Problem this closes

§0's mandate ("served ∪ explicitly-accounted-for = 100% of the domain-relevant corpus; a silent
omission is a BUILD FAILURE") and Ω3's five-state completeness contract are prose in the charter.
Nothing yet defines a machine-checkable assertion α's CI (K1 receipt gate) and γ's own
`elev-depth-gates.yml` can both evaluate identically. C7 freezes that assertion's shape and the rule
for when it is satisfied, so both gates compute the same answer from the same inputs.

## The invariant (frozen)

For a given `(chart_id, domain)` pair, let `S` be the domain's TCI slice — the subset of
`TOTAL_CONCEPT_INVENTORY_v1_0.json` entries whose `DOMAIN_RELEVANCE_MAP_v1_0.json` classification for
`domain` is not `excluded`. Every `concept_id ∈ S` MUST be assigned to **exactly one** of five
disjoint accounting states for that `chart_id`:

```ts
export type AccountingState =
  | "served"                 // concept_id appeared in at least one response for this chart_id,
                              // traceable to a specific tool call + fact_id(s)/row(s)
  | "empty_for_this_chart"   // concept_id's serving query ran and returned zero rows for this
                              // chart_id specifically (e.g. a yoga that doesn't fire natally) —
                              // NOT the same as never having been queried
  | "not_computed_globally"  // the underlying L1-L5 asset has not been built/populated for this
                              // chart_id at all (distinct from empty: the computation never ran)
  | "superseded_by_aggregate" // concept_id's information is strictly subsumed by another served
                              // concept_id in the same response (e.g. a per-varga AV row subsumed
                              // by a served cross-varga AV summary that cites it) — the subsuming
                              // concept_id must be named in `superseded_by`
  | "excluded_by_named_rule"; // concept_id was excluded from S entirely by Ω2's domain relevance
                              // map, carrying `{domain, rule_id, reason}` — this state only appears
                              // when auditing the FULL TCI, never when auditing a domain's slice S
                              // (S already excludes these by construction)

export type ConceptAccountingRow = {
  concept_id: string;                 // matches TOTAL_CONCEPT_INVENTORY_v1_0.json concept_id
  chart_id: string;
  domain: string;
  state: AccountingState;
  evidence: {
    tool?: string;                    // required when state === "served"
    fact_ids?: string[];              // required when state === "served" or "empty_for_this_chart"
    superseded_by?: string;           // required when state === "superseded_by_aggregate"
    rule_id?: string;                 // required when state === "excluded_by_named_rule"
  };
};

export type AccountingInvariantResult = {
  chart_id: string;
  domain: string;
  slice_size: number;                 // |S|, from the TCI × relevance map, computed fresh — never cached stale
  rows: ConceptAccountingRow[];       // length MUST equal slice_size
  unaccounted: string[];              // concept_ids in S with no row — MUST be empty for PASS
  pass: boolean;                      // true iff unaccounted.length === 0 AND rows.length === slice_size
};
```

## The assertion (what CI actually checks)

```
PASS(chart_id, domain) ⟺
     rows.length === slice_size
  ∧  unaccounted.length === 0
  ∧  every row.state ∈ AccountingState
  ∧  every row carries the evidence fields required for its state (see table above)
```

`unaccounted` is illegal in the sense the charter uses the word: a concept_id present in the TCI
slice with **no** `ConceptAccountingRow` at all is a build failure, not a warning, **when the
`(tool, domain)` pair is inside `ledgers/contracts/C7_ENFORCED_SCOPE.json`** (see Scope below). This
mirrors C2's `CategoryReceipt` at the concept-level rather than the fact_category-level — C7 is a
strict refinement of C2 for the specific purpose of Ω3/Ω8's gates, not a replacement for it.

## Scope (gate scoping, per Ω3)

`ledgers/contracts/C7_ENFORCED_SCOPE.json` — default `{"tools": []}` — an allowlist of `{tool,
domain}` pairs. Outside the allowlist, `PASS(...)` is computed and reported but **never blocks CI**
(report-only). Inside the allowlist, `pass === false` fails the build. The gate as a whole is
**warn-only in its entirety** until `contracts/C7.frozen` exists (see Freeze condition below) — this
lets α's CI scaffold include the check from T0 without γ's still-in-progress accounting work
red-lining every stream's builds overnight.

γ commits (PROXY-RULED-003, proxy/gamma.md) to bringing **wealth** and **career** into the allowlist
before signalling stream completion. A domain that cannot reach `pass: true` is `PARKED-HONEST` and
stays out of the allowlist — the number is never lowered, and an out-of-allowlist domain never blocks
α's or β's builds (M2.9).

## Freeze condition for `contracts/C7.frozen`

`contracts/C7.frozen` (a zero-content sentinel file, existence-checked only) is written by γ once:
(a) `generate_tci.ts` (Ω1) has produced a real, DB-derived TCI for at least one canonical chart, (b)
the accounting-row generator has run end-to-end for wealth against that TCI with `pass: true`, and
(c) the independent Verifier's Ω1 sanity gate (distinct `fact_category` count ≥ prod, full coverage
of mechanisms classes/dasha systems/vargas/ayanamshas) has passed. Until then the gate stays
warn-only campaign-wide, per §7.2's general stub-and-build-on rule — this is the one narrow place C7
itself is allowed to be provisional even though Ω1's TCI underneath it may never be.

## Rules (frozen)

1. `rows.length` MUST equal `slice_size` exactly — padding with a placeholder state, or silently
   dropping a concept_id from `rows` to make counts match, both violate the invariant and must fail
   `pass` even if `unaccounted` is coincidentally empty (a row-count check is separate from the
   unaccounted-list check by design, to catch a generator that fabricates rows).
2. `excluded_by_named_rule` rows never appear when auditing a domain's slice `S` — by construction,
   Ω2 already removed them before computing `S`. If the generator emits one, that's a bug (S was
   computed wrong), not a valid accounting state for that context.
3. A `served` row's `fact_ids` must resolve back to real `chart_facts.fact_id` values (or the
   equivalent PK for L2+ derived tables) — this reuses CLAUDE.md §N.5's resolution rule; a
   non-resolving fact_id fails `pass` regardless of state correctness.
4. This contract does not itself compute `slice_size` or classify any concept — it only fixes the
   shape and the pass/fail rule. Ω1 computes the TCI, Ω2 computes the relevance map (hence `S`), Ω3's
   generator computes `rows`. C7 is the seam between them and α's/γ's CI.

## Non-goals

- Does not replace C2's `CategoryReceiptSet` (fact_category-level, response-envelope-scoped) — C7
  operates at concept-id level and campaign-audit scope, not per-response.
- Does not define how `superseded_by_aggregate` subsumption is detected (that's an Ω3 generator
  implementation decision) — only the shape once decided.
- Does not itself decide which domains are in `C7_ENFORCED_SCOPE.json` at any given moment — that's
  Ω3/Ω8's operational decision, updated as domains reach 100%.
