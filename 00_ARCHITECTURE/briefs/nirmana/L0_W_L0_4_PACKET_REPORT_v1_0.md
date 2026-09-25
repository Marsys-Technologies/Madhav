---
artifact: L0_W_L0_4_PACKET_REPORT
version: 1.0
status: CURRENT
packet: W-L0-4 (Served surface contract)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md
---

# W-L0-4 Packet Report — Served surface contract

Per-packet report per the execution kickoff. Convention: change → detector before →
detector after → blocks. Executed as ONE sweep across the L0 registry, not per
asset, per the kickoff. This packet needed **no migration** — nothing is held on
the ledger for it. All code below is uncommitted in the worktree at report time.

## Packet scope (strategy §4.2 W-L0-4 exit condition)

> every exported CapabilityDescriptor in the L0 registry declares a
> density_contract (the proof counts descriptors, not files); lattice allowlist
> 9/9 with a test that fails on 8; `ref_graha_reference_get` (or equivalent)
> exists and is exercised.

Also closes correction **C-6** (§7): the presentation-parity probe of §2.2 had
never been run for any L0 capability.

## Measured baseline (worktree HEAD, 2026-09-25)

- **L0 registry** = `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/`:
  **46 capability files, exactly 46 exported descriptors** (one per file; 39
  typed `CapabilityDescriptor`, 7 typed `ToolCapability`/`ResourceCapability`).
  The strategy text says "49" — **stale by 3** against the measured registry;
  this packet counts the measured set, not the prose, and the detector pins the
  measured number.
- **0 of 46** declared `density_contract` on the descriptor literal (verified via
  `git show HEAD:<file> | grep`). A catalog-time backfill
  (`descriptor_defaults.ts deriveDensityContract`) covers every capability at
  `getCatalog()` time — but the exit condition demands explicit declarations,
  and a backfill can silently rot where a literal cannot.
- **Muhurta lattice allowlist: already 9/9** — fixed by PR #1705
  (`7beff69f2`, "L0-W3 IMPLEMENT — land the 3 L0-W2 MUST findings"). The header
  comment in `query_muhurta_lattice.ts` documents the prior 4/9 state. The
  fail-on-8 property already stands: `__tests__/query_muhurta_lattice.test.ts`
  iterates a test-side hardcoded list of all 9 families plus a
  description-count guard. **No further lattice work needed; recorded
  closed-with-evidence.**
- **`reference_planets`** (= producer asset `bg_reference`, 11 rows measured
  live, 14 columns) had **zero served path** — no reader anywhere in
  `platform/src`. Rows: 9 grahas + ascendant + midheaven; the two angles carry
  honest NULL dignity fields; Rahu's citation carries "exaltation debated,
  Taurus per Parasara".

## Changes

1. **`types.ts`** — added the `density_contract` mirror to the `D1Fields`
   mixin (~line 604), with a comment recording that this is NOT a D1 amendment:
   the field already exists on the base `CapabilityDescriptor`; the 7
   narrowed-type files could not otherwise declare it.
2. **Explicit `density_contract` on all 46 pre-existing descriptors** — codemod
   (`/tmp/l0w4_codemod.py`, retained) inserted the declaration plus a 3-line
   provenance comment after each `export const XCapability: T = {` opening
   line. Values follow the `deriveDensityContract` evidence rules verbatim
   (tool_role byte tiers; paginated from pagination param names; facets =
   non-structural input params; `empty_reason` false only for
   orientation_digest/calibration archetypes), so declaration and backfill
   agree by construction.
3. **Defect found and fixed during (2):** the 5 Stream B ephemeris tools
   (`query_planet_position`, `query_planet_transit`,
   `query_current_transit_snapshot`, `query_aspects_at_time`,
   `query_retrograde_periods`) carry JSON-schema-shaped `input_schema`
   (`{type, properties, …}`), so the mechanical derivation had read schema
   keywords as facets. Honest facets were verified by reading each file and
   declared explicitly (e.g. position `['date','planet']`; snapshot
   `['as_of_date']`; all `paginated: false`). The detector (item 4) carries a
   guard that no facet may be a JSON-schema keyword, so this defect class
   cannot re-enter silently.
4. **Detector** `__tests__/l0_density_contract.test.ts` (4 tests): pins
   `L0_CAPABILITIES.length` at the measured **47** (46 + the new capability)
   with unique URIs; asserts every descriptor declares an explicit
   `density_contract` — importing `../index` directly, never `getCatalog()`,
   so the catalog backfill cannot mask a missing literal; well-formedness per
   subfield; the schema-keyword facet guard from (3).
5. **New capability** `ref_graha_reference_get.ts` — uri
   `marsys://tool/L0/ref_graha_reference_get`, leaf/flat_fact, global scope,
   optional `planet_id` filter, serves all 12 data columns of
   `reference_planets` including `source_citation`, honest NULLs for the two
   angles, `empty_reason` on no-match, B.10 disclaimer. Registered in
   `index.ts` (import, `L0_CAPABILITIES` entry, re-export).
6. **Exercise test** `__tests__/ref_graha_reference_get.test.ts` — 7 tests
   covering the unfiltered 11-row read, per-planet filter, angle NULL honesty,
   citation presence, empty_reason, and descriptor shape.
7. **Editorial review registration** — added `ref_graha_reference_get` to the
   `planetary_state` family in `knowledge/editorial_review.ts`. The
   `UNREVIEWED_DESCRIPTOR_SEMANTICS` gate refused the new descriptor until
   registered; the gate did its job and the artifact was fixed.
8. **Declared-use register** — `l0_declared_use_register_v1.json`
   `serve_time_reads` 116 → **117**: the W-L0-2 staleness cross-check
   (`scripts/__tests__/l0_declared_dependencies.test.ts`) caught
   `ref_graha_reference_get.ts` reading `reference_planets` with no declared
   use; entry added (`access: direct`, `use_types: ["interpretation"]`).
   Again the gate did its job.
9. **Generated mirrors regenerated** (both refuse to run without explicit
   provenance flags — deliberate discipline, flags supplied):
   - `codegen:capability-estate-census` (`--generated-at` + `--source-revision`)
     → content sha `c41a0abb…`; `:check` OK.
   - `codegen:capability-knowledge` (`--generated-at=2026-09-25T16:38:17Z`)
     → **183 SCUs** (was 182); `:check` OK.
   - Estate pins moved +1 with measured, commented values (`W-L0-4, 2026-09-25`)
     in `knowledge/knowledge.test.ts` (executable_bindings 187; routes 187;
     reviewed_not_exposed 116; reviewed_route_descriptors 187;
     reviewed_nonpublic 116; bindingByUri 183;
     reviewed_pagination_dispositions 187; editorial_scus 183;
     descriptor_metadata_review 174) and `knowledge/w7_semantic_audit.test.ts`
     (scus 183; sourceRefsChecked 357). Pins updated, never weakened;
     `reviewed_exposed` stays 71 and paginated denominators 96/5/91 are
     unchanged — measured against the regenerated snapshot census.

## C-6 — presentation-parity probe (§2.2), first run

Probe `/tmp/l0w4_parity.py` (retained): per-file extraction of SELECT column
lists vs the §2.2 presentation fields (citation / school / alias / convention).
**Totals across 47 capability files: citation 33 | school 6 | alias 11 |
convention 8.** Verified anomalies, classified honestly:

- **Fully carried** — `query_yoga_catalog` / `query_dosha_catalog` use
  `SELECT *` over tables that carry the fields; `query_dasha_systems`,
  `query_classical_texts`, `query_class_priors`, `query_prashna_lagna_methods`
  select the fields explicitly.
- **Partially carried** — citation yes, `school` absent (the column does not
  yet exist on the underlying tables — that is W-L0-5's migration 1124, HELD):
  the 17 W2b refs, `query_transit_vedha`, `query_parihara_graph`,
  `query_remedy_corpus` (its COMPACT_COLUMNS include `source_canonical_id` +
  `source_citation`; the table has no school column), and this packet's
  `ref_graha_reference_get` (table has no school column).
- **n/a** — compute/sidecar tools and infrastructure tools with no §2.2 fields
  in scope.

**Handover item for the migration-1124 rollout (not this packet):** when 1124
applies and `school` exists on `bg_transit_rules` / `bg_parihara_rules` /
sutravali_rules, the SELECT lists of `query_transit_vedha` and
`query_parihara_graph` (and the d7 sutravali capabilities in
`register_d7_channel.ts`, outside this packet's directory) must add `school`,
or the served-surface parity gap persists after the table carries the column.
Recorded here; execution belongs to the 1124 rollout.

## Detector / gate results

| Gate | Before | After |
|---|---|---|
| Explicit `density_contract` literals in L0 registry | 0 / 46 | **47 / 47** (incl. new capability) |
| Muhurta lattice allowlist | 9/9 (PR #1705) | 9/9 — unchanged, closed with evidence |
| Served path for `reference_planets` | none | `ref_graha_reference_get`, exercised (7 tests) |
| serve_time_reads register coverage | 116 | 117 — staleness cross-check green |
| C-6 parity probe | never run | run; totals 33/6/11/8, anomalies classified |

- `npx vitest run src/lib/retrieval/registry` — **1966 passed / 178 skipped
  (2144), 0 failed**.
- Campaign L0 layer tests (incl. the 2 new files) — **47 passed**.
- Campaign scripts/migration tests (`l0_declared_dependencies`,
  `l0_description_truthfulness`, `l0_registry_parity`,
  `l0_rules_link_accountability`, `l0_provenance_completion`,
  `nirmana_l0_prashna_integrity_contract`, `list_entities_honesty_wp15`) —
  **33 passed / 15 skipped** (skips are the fixture-gated migration-apply
  tests; migrations 1120–1124 remain HELD as previously reported).
- `npx eslint` on the L0 registry + `types.ts` + `knowledge` — **0 errors**,
  15 warnings, all the pre-existing `_ctx` unused-parameter pattern in resolve
  handlers (verified untouched by this packet's diff).
- `npx tsc --noEmit` — exit 0. Vidhi parity gate — 3 passed.
  Chart-agnostic gate — PASS. Census + knowledge `:check` — OK.
- `pytest tests/l0/ -q` — **129 passed** (nothing python-side changed in this
  packet).

## Findings carried (not this packet's scope)

**F-W-L0-4-1 — `tests/test_u2_lifetime_convergence.py` is red at branch HEAD,
independent of this packet.** 10 of 13 tests fail on the pristine branch tip
(`0411c5a46`, verified in a detached worktree with zero uncommitted changes)
and pass identically on pristine `origin/main`. Mechanism: the branch lineage
carries the sangam-stage3 commits (notably `a55e1b941` "R-3(b) fail-loud
lagna"), whose `_build_house_lord_map` issues a
`chart_facts … fact_subject='LAGNA'` lookup that the DB-free mocked cursor in
the test does not route; the writer then correctly refuses the Aries fallback
(CR-87/R-3(b)) and raises. The writer's behaviour is the ruled behaviour; the
test fixture is what is stale. This is L3 ka_sangam territory — outside L0
scope, not touched, reported here for the strategy session. The remaining full
python suite: 6889 passed / 255 skipped / 3 xfailed besides these 10.

## Blocks

None for this packet. No migration required; nothing waits on the ledger.

## Exit-condition accounting (strategy §4.2 W-L0-4)

- *Every exported CapabilityDescriptor in the L0 registry declares a
  density_contract; proof counts descriptors, not files* — **met**: 47/47
  explicit literals; standing detector counts descriptors via `L0_CAPABILITIES`
  and bypasses the catalog backfill.
- *Lattice allowlist 9/9 with a test that fails on 8* — **met prior** (PR
  #1705); verified and recorded.
- *`ref_graha_reference_get` (or equivalent) exists and is exercised* —
  **met**: capability exists, registered, 7-test exercise suite green.
- *C-6 parity probe run* — **met**: first full run, anomalies classified,
  one handover item recorded for the 1124 rollout.
