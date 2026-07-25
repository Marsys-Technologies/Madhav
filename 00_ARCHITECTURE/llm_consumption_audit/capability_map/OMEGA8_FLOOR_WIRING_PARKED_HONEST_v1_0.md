---
artifact: OMEGA8_FLOOR_WIRING_PARKED_HONEST
version: "1.0"
status: PARKED_HONEST
blocked_on: alpha (cross-manifest — the floor CONSUMER is outside γ's file manifest)
lane: "Ω8 (Elevation Campaign v2.1, Stream γ / PŪRṆA) — floor reconciliation"
generated_at: "2026-07-25"
---

# Ω8 floor regeneration — cross-manifest wiring handoff (PARKED-HONEST, blocked-on-α)

## What γ/Ω8 produced (in-manifest, complete)

- `REGENERATED_FLOORS_v1_0.json` — the correct, TCI-derived floor for each of the 7 domain
  deepdive intents (wealth, career, marriage, health, spirituality, education, progeny),
  mechanically enumerated from the TCI slice + Ω2's relevance map. **Never hand-curated.**
- `FLOOR_COVERAGE_ACCOUNTING_v1_0.json` — the CI-gate artifact: every (domain × chart) floor's
  own TCI-derived slice accounted into the SAME five Ω3/C7 states, 14/14 PASS at 100% accounting.
- `platform/scripts/census/generate_floor_regeneration.mjs` — the regenerator.
- `platform/scripts/census/check_floor_coverage.mjs` — the CI gate (exit 1 on any non-pass;
  verified to fail on injected accounting-mismatch and dead-floor-item).

## What is PARKED (cross-manifest — α or a later pass must wire it in)

The floor **CONSUMER** is outside γ's manifest and MUST NOT be edited by this lane:

- **`platform/src/lib/vidhi/registry_data.ts`** — `VIDHI_PRIMITIVES` + `VIDHI_INTENT_FLOORS`.
  This is the hand-authored TS mirror the compiler reads.
- Its DB seed: **`vidhi_primitives` / `vidhi_intent_floors` / `vidhi_floor_items`** (migration 440,
  seeded by `bg_vidhi_primitives.py` / `bg_vidhi_floors.py`). The TS file and DB seed are
  hand-synchronized; both must land the same regenerated content.

This is the same shape as Lane E's `rank_vocabulary.ts` park: γ's in-manifest deliverable (the
correct floor DATA + the generator + the CI gate) is complete; only the cross-file wire-in is parked.

## Exact edits α needs to make in `registry_data.ts`

The floors today are hand-curated with **thin, single-varga, D1-only, partial-lagna** coverage.
Replace the hand-curated per-domain varga / AV / lagna lists with the TCI-derived set from
`REGENERATED_FLOORS_v1_0.json`. Concretely, per domain floor (`*_DEEPDIVE_ITEMS`):

1. **`divisional_facts`** — currently one or two hand-picked vargas (e.g. wealth = `D2` only;
   marriage = `D9` only). Replace with `floor_vargas` from the artifact:
   - wealth → **D1, D2, D9, D11** (was: D2)
   - career → **D1, D9, D10** (was: D9, D10)
   - marriage → **D1, D9** (was: D9)
   - health → **D1, D6, D9, D30** (was: D6)
   - spirituality → **D1, D9, D20** · education → **D1, D9, D24** · progeny → **D1, D7, D9**
   Rule = universal {D1, D9} ∪ Ω2-`primary` vargas for the domain (NOT hardcoded — read from Ω2).

2. **`ashtakavarga_scan`** — currently `ganita_chart_facts_get(category: 'ashtakavarga')`, **D1-only**.
   Add per-varga AV: the item must cover the full `ashtakavarga_*` family incl.
   `ashtakavarga_bindu_per_varga` and `ashtakavarga_pinda_sarva_per_varga` (all divisional charts).
   504 concepts/domain are floor-guaranteed by this item. Add to every AV-relevant domain floor
   (all 7 already carry `ashtakavarga_scan`).

3. **`special_lagna_read`** — currently `lagnas: ['indu', 'sree']` (wealth) — a 2-lagna subset.
   Replace with the **full lagna + saham set**: 7 special lagnas
   (Indu, Sree, Ghati, Hora, Bhava, Varnada, Vighati) + 70 sahams + Upapada = 78 concepts.
   (This is where wealth's **Indu Lagna** floor requirement is satisfied.)

4. **New floor primitives** to register in `VIDHI_PRIMITIVES` and splice into each domain floor
   where domain-relevant (all resolve to live tools, post the Ω8 serving_args fixup):
   - **`argala_read`** → `ganita_chart_facts_get(category ∈ {argala_natal_matrix,
     virodha_argala_natal_matrix, net_argala_per_varga})` — 1044 concepts/domain.
   - **`dispositor_closure_read`** → `ganita_chart_facts_get` (composite_dispositor_strength …)
     + `bodha_mechanisms_get(mechanism_class ∈ {convergent_dispositor_chain, dispositor_cycle})`
     — 607 concepts/domain.
   - **`mechanism_read`** already exists (`bodha_mechanisms_get`) — ensure the 10 classes are the
     floor-guaranteed set. NB CMN-1: the TCI row_count for these is ayanamsha-summed
     (`is_ayanamsha_summed: true`), and 6/10 are honest empty-for-corpus gaps (`not_computed_globally`).
   - **`cross_ayanamsha_agreement`** → `ganita_positions_get` over the `meta:chart_facts(ayanamsha_id)`
     axis — 6 concepts, **domain-agnostic universal** (accounted in the artifact's
     `agnostic_universal_counts` bucket, not the domain slice).

## Acceptance the wire-in must preserve

After α wires the regenerated floors into `registry_data.ts` + the DB seed, re-running
`node platform/scripts/census/generate_floor_regeneration.mjs && node platform/scripts/census/check_floor_coverage.mjs`
must still print **14/14 PASS** and exit 0. The generator is the source of truth; the TS/DB floor
is its compiled projection — the two must not drift (add the gate to CI so they can't).
