---
artifact: KALA_W4_UPAYA_DESIGN (Wave W4 — UPĀYA / YAJÑA / the Intervention Ledger: build-precise design for the three Phase-5b lanes)
canonical_id: KALA_W4_UPAYA_DESIGN
version: 1.0
status: DESIGN — Phase-5a output of the ṢAḌ-DARŚANA campaign. DESIGN-ONLY: this pass wrote no
  production code, no migration, no ledger edit. It is the build contract the three Phase-5b
  lanes execute from.
created: 2026-08-01
author: `w4-design` lane (Opus, §B.3 mandatory-Opus for the W4 design pass)
campaign: ṢAḌ-DARŚANA v2 · Wave W4 ("the intervention wave", flagship)
trigger: >
  Brief §3-item-triggered: Phase 5a starts the moment items 36+41 land. Both landed —
  item 41 (Muhūrta Factor Census + `bg_muhurta_lattice` / `bg_parihara_rules` substrate) on
  Night 2 as PR #930; item 36's query-time engine (`platform-mcp/src/lib/kala_lattice_query.ts`)
  as PR #1004 on `shad-darshana/integration`, tip `b14d41e4`. This document was written against
  that exact tip.
authority_order: >
  KALA_SUPREME_ELEVATION_v1_0.md (v1.2, "the Elevation") > KALA_SIX_VIEWS_DESIGN_v2_0.md >
  KALA_SIX_VIEWS_DESIGN_v1_0.md > SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md (BINDING rulings,
  ADJUDICATION-8 and -10 in particular) > SHAD_DARSHANA_BRIEF_v2_0.md (execution contract) >
  THIS DOCUMENT. This document is a BUILD SPECIFICATION, not a design authority: where it
  appears to conflict with any of the above, they win and this document is the thing that gets
  fixed. Where they say WHAT and this says HOW/IN-WHICH-FILE/PROVE-IT, this is binding on the
  three W4 builder lanes.
supersedes: nothing
scope: >
  Wave W4 ONLY (brief §3 W4). Registry items **26** (UPĀYA-SETU full), **37-full**
  (ritual-resonance mapping + paddhati profile live), **38's W4 half** (ELECT ritual-pairing —
  the half that closes the item), **40** (`kala_ritual_get` Modes 1–2 REAL), **42** (Unified
  Intervention Ledger, `mi_sankalpa`), plus the E6 slices that land here (UPĀYA efficacy
  reporting; Mode-1 opportunities joining the AHEAD 90-day digest, the D4 clause gated here
  because Mode 1 first exists here).
  **NOT in scope:** W2G sub-day precision (item 19), W3K KP (item 18), W2's remaining field
  integration (the N_e blocker), W3's other new computations, W5 planner wiring (item 35/40's
  wiring half), W6 cutover. Per brief §4, **no lane here may be built to REQUIRE sub-day transit
  precision** — every transit-edge constraint this design emits is `day_grade` and says so.
  Note the corollary that matters for the W4 fixture: pāñcāṅgika and day-part limbs are
  *intrinsically* sub-day and are honestly `intra_day` TODAY (Elevation §8 precision-regime
  honesty) — that is not a sub-day-transit dependency and does not make W4 hostage to W2G.
---

# KALA W4 — UPĀYA · YAJÑA · the Intervention Ledger: build-precise design

---

## §0 — How to read this document (lane assignment + the anti-collision contract)

W4 is built by **three parallel lanes**. Each lane owns a disjoint set of files and a disjoint
set of tables. Lane boundaries are **file ownership + published TypeScript/SQL contracts**, both
frozen by this document. A lane never edits another lane's *file*; it consumes another lane's
*published contract* (an exported type, a table, or an HTTP action). If a lane believes it needs
a boundary changed, it **stops and raises with the Conductor** — it does not negotiate
bilaterally and it does not "just add one line" to a sibling's file. This mirrors
`KALA_W2_FIELD_DESIGN_v1_0.md §0`, which is the precedent this table is written against, and it
exists because Night 1 alone cost three manual conflict resolutions on shared kala files.

### 0.1 The lane table

| Lane | Items | Owns (files — exclusive write) | Owns (tables / schema) |
|---|---|---|---|
| **U** — UPĀYA-SETU | 26 (full) + E6 efficacy reporting | `platform-mcp/src/tools/kala_views/upaya.ts` · `upaya.test.ts` · NEW `platform-mcp/src/lib/kala_upaya_diagnosis.ts` (+ `.test.ts`) | **none** (serving-only lane: it computes over existing L2/L4/L0 rows and creates no table) |
| **R** — YAJÑA-SETU + paddhati + pairing | 37-full · 40 · 38's W4 half · digest ritual rows | `platform-mcp/src/tools/kala_views/ritual.ts` · `ritual.test.ts` · `platform-mcp/src/tools/kala_views/elect.ts` · `elect.test.ts` · `platform-mcp/src/tools/kala_views/ahead.ts` · NEW `platform-mcp/src/lib/kala_sky_pattern.ts` · NEW `platform-mcp/src/lib/kala_ritual_resonance.ts` (+ tests) · `platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py` · `bg_parihara_rules.py` (census rows only) · NEW `platform/scripts/census/shad_darshana_gates/yajna_mode2_fixture_gate.ts` · NEW `platform-mcp/test/fixtures/yajna_mode2_gate.json` · `.github/workflows/shad-darshana-ci-skeletons.yml` | `bg_muhurta_lattice` (**extended**, see §3.1) · `bg_muhurta_factor_census` (rows only) · NEW `kala_paddhati_profile` |
| **S** — Intervention Ledger | 42 | NEW `platform/python-sidecar/pipeline/orchestrator/writers/mi_sankalpa.py` (+ `writers/tests/test_mi_sankalpa.py`) · NEW `platform/python-sidecar/services/mi_sankalpa/*` · NEW `platform-mcp/src/lib/intervention_filing.ts` (+ `.test.ts`) · `platform-mcp/src/client.ts` · `platform/scripts/seed/asset_registry_seed.ts` | NEW `mimamsa_intervention_ledger` |

### 0.2 Shared, owned by NOBODY (frozen for the duration of W4)

- **`platform-mcp/src/lib/kala_envelope.ts` — FROZEN.** No W4 lane edits it. Every W4 response
  is assembled through the existing `makeKalaEnvelope` / `computedCoverage` /
  `honestEmptyCoverage` / `notInCorpusCoverage` / `pointerTo` / `noLeverPointer` surface. If a
  lane believes the envelope needs a new field, that is a cross-lane PR raised with the
  Conductor, never a unilateral edit. (Two of the three lanes touch every envelope field; an
  edit here is a guaranteed three-way conflict.)
- **`platform-mcp/src/lib/kala_lattice_query.ts` — FROZEN, and this is a RAIL, not a
  convenience.** Brief §7's **ONE-ENGINE RULE**: ELECT and YAJÑA-SETU share the single
  lattice/adjudication/grading engine; *a second implementation of any of the three is a build
  error*. Lane R's Mode-2 compiler **calls** `fetchLatticeSubstrate` + `adjudicateCandidates`;
  it does not fork, re-implement, or copy them. See §3.4 for what Lane R is allowed to build
  beside the engine and why that is not a second engine.
- **`platform-mcp/src/lib/kala_grading.ts`** — read-only for W4. It is the W1 lite-v0 grader
  (`convention_id: 'lite_v0_*'`); item 36 supersedes it at the ledger level, and W4 does not
  re-litigate that.
- **`platform/scripts/census/shad_darshana_gates/completeness_census_seed.ts`** — the per-item
  `disposition` fields for items 26/37/38/40/42 are updated **once, by the Conductor, in the
  W4 gate-close PR**. No lane edits it (three lanes each bumping one row in one array is the
  collision this rule prevents).
- **`platform-mcp/src/tools/kala_views/register_all.ts`** — untouched. W4 adds **no new MCP
  tool**: items 26 and 40 are fill-ins of the already-registered `kala_upaya_get` and
  `kala_ritual_get` W0 shells. This is worth stating because it removes the single worst
  historical collision surface from this wave entirely.

### 0.3 Sequencing (the only hard ordering constraint between lanes)

Lanes U, R, S are otherwise fully parallel. One ordering constraint exists:

> **Lane S ships a SPINE PR first** — `platform-mcp/src/lib/intervention_filing.ts` plus the
> one-line widening of `callPlatformWrites`'s action union in `platform-mcp/src/client.ts`
> (§4.4) — **before** its writer PR, because Lanes U and R both consume it for falsifier
> auto-filing. Until that spine PR merges, Lanes U and R build against the published type and
> serve `filing_state: 'filing_path_not_yet_available'` — an honest, named state, never a
> silent omission and never a fabricated `filed: true`.

Everything else is concurrent. In particular: Lane R's fixture gate needs Lane R's own lattice
extension and nothing from U or S; Lane U's diagnosis needs nothing from R or S; Lane S's writer
needs nothing from U or R.

---

## §1 — Standing rails this design is built to satisfy (read before writing code)

1. **§N.5 / B.10 — the lower layer is the authority.** No W4 surface ever *restates* a value
   owned by L1 (`chart_facts`), L2 (`bodha_rm_*`), L4 (`phala_mitigation`, `phala_anchors`), or
   L0 (`brahma_remedy_corpus`, `bg_muhurta_lattice`). It **references** the row and inherits its
   value. A W4-derived value that disagrees with the row it cites is a **halt-worthy bug**, not
   a stored divergence. This rail has teeth in this wave specifically because item 26 sits on
   top of three pre-existing remedy surfaces (§2.1) and the temptation to recompute is real.
2. **B.10 — nothing fabricates a ritual prescription.** Every rite, mantra, dāna, or vrata this
   wave serves is a **row that already exists** in `brahma_remedy_corpus` /
   `bodha_rm_remedy_prescriptions` / `phala_mitigation.program_jsonb`, selected and cited. A
   rite composed at serve time by concatenating a graha, a deity, and an action is a fabricated
   prescription and a build error, even when every component is individually real.
3. **Honest-empty always (LAW ZERO).** Every gap is served with a reason via the envelope's
   existing three-state `CoverageState` (`computed` / `honest_empty` / `not_in_corpus`). Zero
   candidates with no reason is a FAIL in this wave's own gate, not a quiet pass.
4. **§N.6 Serving Density.** Cited prescriptions and uncited/placeholder corpus rows are
   **counted and served separately**, never flattened into one array. This is not abstract:
   `brahma_remedy_corpus` is 266 rows of which ~102 are placeholder-shaped and ~164 carry real
   citations (recorded live by item 41's own census work). A caller must never be able to read
   a raw row count as "N attested remedies". Same discipline as `kala_lattice_query.ts`'s
   `convention_only_factors` / `convention_only_factor_count`, which is the in-repo precedent.
5. **§N.7/§N.8 Earned-Signal.** Every PASS, tier, flag, or `computed` coverage state this wave
   emits names the detector that computes it **and** the code path that would make it correctly
   read `false`. The live precedent and the live counter-example are both in `elect.ts`: its
   `hora_ladder` coverage was an unconditional `computed` for a field the response never carried
   (PARĪKṢAKA found it), and the fix was to make the check ask the actual question. Every new
   coverage entry in this wave is written the fixed way.
6. **§N.2 FROZEN orchestrator contract.** `mi_sankalpa` is a `@register('mi_sankalpa')`
   `WriterBase` subclass on `ctx.db_conn`; it never commits/rolls back/closes, never writes
   `asset_throughput`, and reads `chart_id` from `ctx.config`. If it seems to need a contract
   change → STOP and raise.
7. **§N.3 idempotency + the status-preserving variant.** Per-chart delete-then-insert scoped to
   `(chart_id × natural key)` — **except** that adjudicated/native-attested rows are
   irreplaceable and are excluded from the delete, exactly as `mi_bhavisya` already does
   (`DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN
   ('pending','due')`). §4.3 specifies the exact predicate for `mi_sankalpa`.
8. **ONE-ENGINE RULE** (brief §7) — see §0.2.
9. **MODE-3 ROUTING RULE** (Elevation §8, brief §7) — `kala_elect_get` is the sole server of
   Mode 3; `kala_ritual_get` redirects and never passes through. **This rule survives W4
   unchanged and gets *stronger*, not weaker** (§3.5). The existing source-level rail in
   `ritual.test.ts` — a regex scan asserting `ritual.ts` contains no `fetch(`,
   `callSidecarPath(`, `callPlatformPrim*(`, `callRegistryCap*(`, `/api/compute/`, or
   `muhurta_finder` — is a real trap for this wave and is handled explicitly in §3.5.2.
10. **Untouchables** (brief §7): `kala_gochara_windows` data, `build_substep_progress`, the
    sealed evaluator harness, root `CLAUDECODE_BRIEF.md`. Nothing in W4 goes near any of them.
11. **Ethical Framework** (`MACRO_PLAN_v2_0.md` §3.5.A–H). Binding on this wave more than any
    other, because this is the wave that tells a human being to *do something*. §5 states the
    concrete serving constraints.
12. **CIRCULARITY GUARD.** W4 touches the LEL only at the two sanctioned entry points
    (stage-9 calibration, and biographical joins at serving time). Nothing in this wave feeds a
    value back into a field input. Lane S reads the prospective ledger; it never writes into the
    field.

---

## §2 — Lane U: UPĀYA-SETU, full (item 26)

### 2.0 What already exists — read this before designing anything

`kala_upaya_get` is **not a new tool**. `platform-mcp/src/tools/kala_views/upaya.ts` is a live
W0 facade shell, registered through `register_all.ts`, serving an honest not-computed ledger
with exactly three named coverage concepts:

```
pact_link_diagnosis · alternate_routing_search · efficacy_tiers
```

Item 26 is the fill-in of those three concepts. The coverage-concept strings are **stable
identifiers** — the completeness census and the specificity gate both key off them — so Lane U
keeps all three names and flips their state, rather than renaming them.

The wire is already in place at the other end too: `kala_explain_get`
(`platform-mcp/src/tools/kala_views/explain.ts`) already emits a tri-plane pointer to
`kala_upaya_get` when the PACT chain is denied or pending. Lane U lands *on* that wire; it does
not lay a new one.

### 2.1 The three pre-existing remedy surfaces — and the non-duplication ruling

This is the highest duplication risk in the wave. Three remedy surfaces are already live:

| Surface | Table(s) | Grain | What it already has |
|---|---|---|---|
| **L4 `phala_mitigation`** (`ph_pratikara`; served by `phala_mitigation_get` → `query_remedy_program`) | `phala_mitigation` | per obstruction, **600+ rows/chart** | ordered `program_jsonb` with prerequisites · `tradition_options_jsonb` · `cross_tradition_corroboration` (0–6) · `intensity_tier` (light/moderate/intensive) + `proportionality_basis` · `initiation_muhurta_ref` (FK `phala_muhurta`) · `window_start`/`window_end`/`re_evaluation_date` · **`outcome_hook_jsonb`** · `classical_citation` · `derivation_ledger_jsonb` |
| **L2 `bodha_rm_*`** (`bo_upaya`; served by `bodha_remedies_get`) | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions` (+4) | per graha | `resonance_score` / `weakness_score` / `remedy_priority_class` · per-prescription `classical_sources_jsonb`, `classical_strength_rating`, `feasibility_score`, `ritual_complexity_class`, `requires_acharya_review_flag`, `phase_sequence_class` |
| **L0 `brahma_remedy_corpus`** (served by `ref_remedies_get`, `ref_remedy_get`, `ref_tantric_remedies_get`, …) | `brahma_remedy_corpus` | per remedy | `remedy_type`, `deity`, `prescription_text`, `mantra_*`, `timing_rules_jsonb`, `confidence`, `source_canonical_id`, `source_citation`, `classical_ref`, `classical_attestation_text`, `cost_tier`, `contraindications`, `scaffold_status` |

> **DESIGN RULING U-1 (binding on Lane U; reversible — it is a serving-composition choice, no
> schema, no data).** UPĀYA-SETU **creates no fourth remedy store and recomputes no remedy
> ranking.** Its product is the **diagnosis** — which link in the PACT chain failed — and the
> **routing of already-computed remedy rows to that link**. Concretely: item 26 is a
> *selector plus an argument*, not a generator. Where an existing surface already answers a
> sub-question (proportionality → `phala_mitigation.proportionality_basis`; per-graha priority
> → `bodha_rm_resonances.remedy_priority_class`; classical attestation →
> `brahma_remedy_corpus.source_citation`/`classical_ref`), Lane U **cites and inherits** it
> (§N.5). Any row Lane U serves carries `source_surface` + the row's own primary key, so a
> reader can always get back to the authority.

**Two concrete sourcing rails that fall straight out of the inventory:**

- **Never source a prescription through `ref_remedies_by_planet_get` or `ref_mantras_get`.**
  Their underlying primitives (`query_remedies_by_planet`, `query_mantras` in
  `platform/src/lib/retrieve/remedy_tools.ts`) do **not** select `source_citation`. A
  prescription served without a retrievable citation violates B.3 and rail §1.2. Use
  `query_remedies` / `read_remedy` (which do select it), or `bodha_remedies_get` /
  `phala_mitigation_get`.
- **`scaffold_status` and citation-presence are the density split.** A `brahma_remedy_corpus`
  row whose `source_citation` **and** `classical_ref` **and** `classical_attestation_text` are
  all null/blank is a *catalog row*, not an attested prescription. Serve it (B.10 forbids
  silently dropping data) but in its own field with its own count — mirroring
  `kala_lattice_query.ts`'s `convention_only_factors` shape exactly:
  `uncited_remedy_rows` / `uncited_remedy_row_count` / `uncited_remedy_note`.

### 2.2 The diagnosis: which link failed

The PACT chain is already implemented, with a closed vocabulary, at
`platform/src/lib/retrieval/registry/layers/register_d10_pact.ts` (capability
`marsys://tool/L-PACT/pact_query`, MCP tool `pact_query`). Lane U **calls it** — it does not
re-walk the chain.

Closed vocabularies Lane U binds to verbatim (copying them is what makes the diagnosis
machine-checkable rather than prose):

- stages: `PROMISE` · `CONFIRMATION` · `ACTIVATION` · `TRIGGER`
- `pact_stage` (pointer-scoped, lowercase): `promise` · `confirmation` · `activation` · `trigger`
- `pact_status`: `denied_at_promise` · `denied_at_confirmation` · `denied_at_activation` ·
  `chain_pending_activation` · `chain_incomplete_infra` · `chain_complete`

The Six-Views v2 §C.2 diagnosis taxonomy maps onto that vocabulary **1:1**, which is the point:

| `pact_status` | Diagnosed failing link | Remedy class routed to it (§C.2 step 2) |
|---|---|---|
| `denied_at_promise` | promise absent/weak at L2 | *promise-side*: targeted strengthening of the weak significator (`bodha_rm_*` rows for that graha, **not** the generic weakest-graha) **+ alternate-routing search** (§2.3) |
| `denied_at_confirmation` | promised in rāśi, denied in the operative varga | *promise-side*, varga-scoped; and the honest statement that the rāśi-level promise does not survive divisional confirmation |
| `denied_at_activation` | promised + confirmed, but no daśā eligibility in the horizon | *eligibility-side*: the least-opposed windows (§2.4) — explicitly "best available, still weak" |
| `chain_pending_activation` | eligible, activation not yet reached | *eligibility-side* + the wait statement; this is the case where honest advice is often "wait", and the instrument must be willing to say so |
| `chain_complete` | nothing failed | **`no_lever` is the correct answer.** The tri-plane `intervention_ref` is an honest `noLeverPointer('the chain is complete — there is no failing link to repair')`. Manufacturing a remedy for a complete chain is the Offer-Law failure this wave must not commit. |
| `chain_incomplete_infra` | the chain could not be walked | `honest_empty` with the infra reason **inherited verbatim** from `pact_query` — never re-worded into something that sounds like an astrological finding |

The suppression-side branch (vighna) of §C.2 is served from `phala_mitigation`'s
`obstruction_id` / `afflicting_graha` / `obstruction_severity` rows joined to the diagnosed
link — again by selection, not recomputation.

The decision-side branch (a praśna cast at the moment of intent) is **served as a pointer only**
(`prashna_ask` exists as a live tool). Elevation §13 keeps praśna-at-every-query deliberately
un-elevated; W4 does not auto-cast.

Coverage concept `pact_link_diagnosis` flips to `computed` **iff** `pact_query` returned a
`pact_status` from the closed set above **and** the response carries the resulting
`failing_link` field. Detector that could make it read false: `pact_query` erroring, or
returning a status outside the set (both produce `honest_empty` with the reason).

### 2.3 Alternate-routing search

§C.2's "your 2nd-house channel is weak, but an 11th-lord channel exists via X" — a path search
over the chart's own promise graph for a *different mechanism* reaching a similar outcome.

**Substrate:** the L2 mechanism/graph layer already served by `bodha_graph_traverse_get` /
`bodha_graph_subgraph_get` / `bodha_mechanisms_get`, plus `brahma_activity_ontology`'s
`significators` JSONB (`{strengthen_grahas, strengthen_houses, strengthen_varga, avoid}`) and
its FK to `brahma_event_ontology.event_class_id`.

**Honest bound, stated up front:** W2's `kala_field_promise_nodes` / `kala_field_promise_edges` /
`kala_field_routes` (Lane A's "ALTERNATE ROUTINGS" stage-2 output) are the *designed* home for
this search — and they are **empty in production**, because `ka_kshetra` correctly writes zero
field rows until the N_e lifetime-count priors are seeded (ADJUDICATION-2). Therefore:

> **DESIGN RULING U-2 (reversible).** Lane U's alternate-routing search runs over the **L2
> graph** (`bodha_graph_*`) as its primary substrate, and reads `kala_field_routes` as an
> **optional enrichment** when non-empty. The coverage entry `alternate_routing_search`
> reports which substrate actually answered — `computed (basis: bodha_graph)` vs
> `computed (basis: bodha_graph + kala_field_routes)` — and is `honest_empty` when neither
> yields a route. **W4 must not be blocked on the N_e critical path**, and building it to
> require `kala_field_routes` would make the flagship wave hostage to a different wave's
> blocker. The enrichment path is a single `if (routes.length > 0)` branch; when W2 unblocks,
> nothing in Lane U changes.

Every returned route carries: the mechanism's own id, the constituent `fact_id`s it rests on
(§N.5 — these MUST resolve against `chart_facts`), and an explicit statement of what makes it a
*different* mechanism rather than a restatement of the blocked one. A route whose significator
set is a subset of the blocked route's is not an alternate route and is filtered out with the
reason recorded.

### 2.4 Eligibility-side: least-opposed windows via ELECT

§C.2's eligibility branch is "argmax of the weak promise's λ, honestly labeled *best available,
still weak*". λ is the field's — and the field is empty (above). So:

> **DESIGN RULING U-3 (reversible).** The least-opposed-window search is served through
> **`kala_elect_get`'s existing candidate stack** (the `muhurta_finder` score/veto engine plus
> item 36's judgment ledger), with `for_intervention` naming the diagnosed link, **not** by
> Lane U computing a window of its own. This is not a convenience: brief §7's **SINGLE TEMPORAL
> AUTHORITY** rail (item 44) makes "a serving path that computes its own window" a *build
> error*, not a divergence to classify. Lane U therefore emits `authority_basis` naming the
> ELECT candidate id it inherited, and computes no window.

**Cross-lane contract (U → R):** the `for_intervention` parameter is an **edit to `elect.ts`,
which Lane R owns**. Lane U publishes the contract; Lane R implements it. Contract:

```ts
// added to KalaElectInputShape (elect.ts) — Lane R implements, Lane U consumes
for_intervention: z.object({
  failing_link: z.enum(['promise', 'confirmation', 'activation', 'trigger']),
  event_class:  z.string(),            // brahma_event_ontology.event_class_id
  upaya_ref:    z.string().optional(), // the UPĀYA diagnosis id being acted on
}).optional()
```
Its only effects on ELECT: (a) `undertaking` defaults to `remedial_ritual` when absent —
already a member of `muhurta_finder`'s closed `action_type` enum; (b) the frontier statement and
the composed thesis are phrased in the "best available, still weak" register when
`failing_link` is `promise` or `confirmation`; (c) each candidate gains
`intervention_context: { failing_link, event_class }`. **No change to scoring, vetoes, or the
judgment ledger** — that would be a second engine by the back door.

### 2.5 Efficacy tiers (the `efficacy_tiers` coverage concept)

Elevation §C.3: every intervention carries `classically_attested (citation)` / `traditional` /
`speculative_extension`, and the framing is receptivity, never guarantee.

**There is no `efficacy` column anywhere in the schema** — this is net-new, and it must be
*derived from citation facts*, never asserted. The tier function is deterministic and its inputs
are all existing columns:

| Tier | Assigned iff |
|---|---|
| `classically_attested` | the row carries a resolvable classical citation — `brahma_remedy_corpus.source_citation` or `.classical_ref` non-blank, **or** `bodha_rm_remedy_prescriptions.classical_sources_jsonb` carries a non-empty `citations[]`/`text_chunk_ids[]`, **or** `phala_mitigation.classical_citation` non-blank |
| `traditional` | the row exists in a live corpus surface (`scaffold_status='live'`) but carries no retrievable classical citation — attested by practice-record, not by text |
| `speculative_extension` | the row is reached only by an inference this wave made (e.g. a deity correspondence assembled from `NAKSHATRA_DEITIES` rather than read from a corpus row) |

> **RAIL:** `speculative_extension` is a **serving label on a real row**, never a licence to
> synthesize a rite. A rite that does not exist as a row is not `speculative_extension`; it is
> not served at all (rail §1.2).

`efficacy_tiers` reads `computed` iff every served intervention row carries a tier **and** the
response carries the tier histogram. The detector that makes it read false: any served row with
a null tier.

**E6 efficacy *reporting*** — "windows with intervention outperformed prior: 3 of 4" — is served
from Lane S's ledger by a read-only join (§4.5). At n=0 it is `honest_empty` with
`reason: 'no resolved intervention outcomes recorded yet'`, and the envelope's existing
`calibration_maturity` block carries the zeros. A percentage before calibration is a LAW ZERO
violation (Elevation §13); no efficacy rate is ever served with n < the threshold Lane S's
ledger publishes alongside it.

### 2.6 Auto-filed falsifiers (the self-calibration half)

Elevation §C.3: "each adopted intervention auto-files a falsifiable prospective entry."

The sanctioned write path already exists end-to-end and Lane U uses it unchanged:
`POST /api/mcp/writes/prospective_ledger_file` → `fileProspectivePrediction()`
(`platform/src/lib/lel/prospective_ledger.ts`) → `brahma_prospective_ledger`, with `filed_by`
stamped from the resolved principal and `filing_method='explicit_filing_tool'` enforced by a DB
CHECK. `falsifier` is mandatory; `confidence` must be in the open interval (0,1); the
`claim_shape` must match the event class's `temporal_shape` (a BEFORE-INSERT trigger enforces
it); `generator_class='engine'` on an adverse-valence class trips DR-16's five-property
disclosure gate.

> **DESIGN RULING U-4 (reversible; and see §7 OQ-1 — this is one of the two questions that
> genuinely wants ANTARYĀMIN).** Filing happens **only** on an explicit adoption act:
> `kala_upaya_get` gains `adopt_intervention: { intervention_id, confidence, falsifier }` (all
> three required together). A plain read **never files**. Rationale: §11's governance text is
> "explicit filing only; chat is never mined" — a read-triggered file would mine reads. An
> explicit `adopt_intervention` parameter *is* an explicit filing action, and `filed_by` carries
> the principal, so provenance survives. The response reports `filing_state` from a closed set:
> `not_requested` · `filed` (+ `prediction_id`) · `filing_path_not_yet_available` ·
> `filing_refused_adverse_class` (§5.3) · `filing_failed` (+ the verbatim error).

### 2.7 Lane U's response shape (additions to the existing envelope)

```ts
export interface KalaUpayaResponse extends KalaEnvelope {
  tool: 'kala_upaya_get'
  chart_id: string
  event_class: string | null
  diagnosis: {
    pact_status: PactStatus            // the closed set, inherited verbatim
    failing_link: 'promise'|'confirmation'|'activation'|'trigger'|null
    statement: string                  // template-composed (B.10), never generative
    authority_basis: string | null     // item 44 — the pact_query stage id / ELECT candidate id
  }
  interventions: UpayaIntervention[]   // each: {id, class, source_surface, source_pk,
                                       //  efficacy_tier, citation, targets_link, feasibility}
  intervention_count: number
  uncited_remedy_rows: UpayaIntervention[]   // §N.6 density split — NEVER merged into the above
  uncited_remedy_row_count: number
  uncited_remedy_note: string | null
  alternate_routes: AlternateRoute[]   // each carries fact_ids that MUST resolve
  efficacy_report: EfficacyReport | null       // §2.5 / §4.5; null ⇒ coverage says why
  filing_state: UpayaFilingState
  filed_prediction_id: string | null
  disclosure: DisclosureBlock          // §5
  composed_text: string
}
```

`composed_text` is assembled by the existing `composeArgument` from
`platform-mcp/src/lib/argument_composer.ts` — the shared deterministic prose engine. **No
generative call in any serving path** (brief §7 B.10 prose rule). The receptivity framing
("upāya prepares the vessel; it does not command the rain") is a template constant in the
composer's verdict slot, not an LLM sentence.

---

## §3 — Lane R: ritual-resonance, paddhati live, YAJÑA-SETU Modes 1–2, Mode-3 pairing, digest

### 3.1 R1 — extending the lattice (the load-bearing, easily-missed prerequisite)

**The finding.** `bg_muhurta_lattice` as landed by PR #930 carries a hard CHECK constraint:

```sql
factor_family TEXT NOT NULL
  CHECK (factor_family IN ('agnivasa', 'combination_yoga', 'kalam', 'ghati_muhurta'))
```

Four families, ~91,477 rows. Now score the canned W4 Mode-2 fixture's six constraints against
what is actually *in* the lattice:

| Fixture constraint | Lattice-resident today? | Evidence |
|---|---|---|
| `agnivasa = favorable` | **YES** — `factor_family='agnivasa'`, `detail.element` ∈ {Prithvi, Jala, Vayu, Akasha} | census row `rite_residence/agni_vasa` → `bg_muhurta_lattice (factor_family=agnivasa)` |
| `karana NOT IN (viṣṭi/bhadrā)` | **YES** — `factor_family='combination_yoga'`, `factor_key='bhadra'` | census row `panchangika/karana_bhadra_vishti` → same |
| `outside rāhu-kālam` | **YES** — `factor_family='kalam'`, `factor_key='rahu_kalam'` | census row `day_part/rahu_kalam` → same |
| `hora_lord = Guru` | **NO** | census row `day_part/hora_lord` is `computed`, but its `evidence_pointer` is `panchang_engine/timings.py:compute_hora` — **the function, not the table** |
| `vara = Guru-vāra` | **NO** | no `vara` family exists; vāra appears only inside `combination_yoga` interaction detail |
| `tara_bala NOT IN (…)` | **NO** — and correctly so | census row `panchangika/nakshatra_tara_bala` is `not_computed`, reason: *"Chart-personal by construction… out of THIS global lane's scope"* — it needs the chart's own janma-nakṣatra, and a global table cannot hold it |

So **three of six fixture constraints have no lattice atoms to search over**, and one of those
three (tārā-bala) must *never* live in the global table.

**The doctrinal reason this matters more than "just call panchanga at query time":** Elevation
§9 Stage 1 makes coverage a **property of the construction** — the horizon is partitioned by
*every* boundary event of *every* factor, so "no sampling interval exists inside which a
90-minute window could hide." A Mode-2 search that samples panchanga per candidate reintroduces
exactly the sampling interval that guarantee exists to abolish. And the census itself already
says a lattice boundary source it does not annotate is a build error.

> **DESIGN RULING R-1 (binding on Lane R; reversible — additive rows + one widened CHECK).**
> Lane R **extends `bg_muhurta_lattice` with three new chart-independent factor families**:
> `hora`, `vara`, `nakshatra`. It does so by (a) a migration widening the CHECK to
> `('agnivasa','combination_yoga','kalam','ghati_muhurta','hora','vara','nakshatra')`, (b) new
> emitters in `bg_muhurta_lattice.py` over the same rolling horizon, same
> `reference_location_key`/`ayanamsha_key` conventions, same `ON CONFLICT (factor_family,
> factor_key, start_utc) DO NOTHING` idempotency (§N.3 L0), and (c) updating the three census
> rows' `evidence_pointer`s in `bg_parihara_rules.py` to point at the lattice where they now
> genuinely resolve — `day_part/hora_lord` and the new `panchangika/vara`,
> `panchangika/nakshatra` rows.
> **`nakshatra_tara_bala` stays `not_computed` in the global census** — that disposition is
> *correct* and must not be "fixed". Tārā-bala is evaluated **at query time** against the
> chart's own janma-tārā (§3.4), and Mode 2's own coverage block reports it as
> `computed (chart-relative, at query time)` citing the janma-nakṣatra `fact_id` it used.
> Two dispositions, two scopes, both honest — and a session that conflates them has broken
> §N.5.

**Row-volume sanity (so the L0 rebuild is a known quantity, not a surprise):** over a ~5-year
rolling horizon, `hora` ≈ 24/day ≈ 43.8k rows, `vara` ≈ 1.83k, `nakshatra` ≈ 1.9k — roughly
+48k on a 91.5k base. Cheap. Per §N.4 (**floors are aspirational, never fabricated**), the
migration sets `bg_muhurta_lattice.target_floor` to the **achieved** count after the rebuild,
never to a predicted one; the numbers above are sizing, not targets.

**Two non-negotiable consequences (brief §2.5.2):**
1. `bg_muhurta_lattice` is a `bg_*` L0 global asset built **only** by explicit super-admin L0
   trigger. The extended lattice must be **built in production BEFORE** the Mode-2 fixture gate
   runs, or the gate honestly fails on missing atoms — which is correct behaviour but is not a
   discharge.
2. Optional-but-recommended in the same migration, because it is the same generator loop and it
   is what makes Stage-1 completeness genuinely true rather than nearly true: `tithi`,
   `nityayoga`, `karana` families. **If Lane R defers them, the census must say so by name**
   and the Mode-2 coverage block must list them as `not_computed (lattice family not
   materialized)`. Deferring them does not block the fixture; pretending they are covered does.

**One honesty disclosure that is a property of the substrate, not a W4 regression:**
`bg_muhurta_lattice` is computed at a single reference location (`reference_location_key
= 'bhubaneswar'`, with explicit `reference_lat`/`reference_lon`/`reference_tz_offset_minutes`).
Sunrise-derived boundaries — horā, vāra, every kālam — are location-dependent. Every Mode-1/2
candidate therefore carries `reference_location_key` and, where the chart's own location
diverges, an explicit `location_divergence_note`. **Bind-time validation V-R1:** confirm both
canonical charts' birth locations against the lattice reference; if they diverge, the divergence
is **served as data (Law 4)**, never silently reconciled and never quietly dropped from the
precision claim.

### 3.2 R2 — `kala_paddhati_profile` (item 37's storage home), per ADJUDICATION-8

ADJUDICATION-8 is BINDING and gives both the schema shape and the seed content. The table does
not exist anywhere in the tree today — no migration, no writer, no type; it exists only as
design prose in the Elevation (§9) and in ADJUDICATION-8 itself.

```sql
CREATE TABLE IF NOT EXISTS kala_paddhati_profile (
    id                          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id                    UUID        NOT NULL,
    factor_family               TEXT        NOT NULL,      -- e.g. 'agnivasa'
    convention_id               TEXT        NOT NULL,      -- e.g. 'agnivasa_tithi_element_prithvi'
    school_tag                  TEXT        NOT NULL,      -- e.g. 'corpus_default'
    constraint_role             TEXT        NOT NULL
        CHECK (constraint_role IN ('hard', 'soft', 'informational')),
    convention_status           TEXT        NOT NULL DEFAULT 'computed'
        CHECK (convention_status IN ('computed', 'declared_not_computed')),
    provenance                  TEXT        NOT NULL,
    corpus_gap_ref              TEXT,
    native_confirmed            BOOLEAN     NOT NULL DEFAULT FALSE,
    awaiting_native_confirmation BOOLEAN    NOT NULL DEFAULT TRUE,
    version                     TEXT        NOT NULL,      -- 'paddhati_v01' — ZERO-PADDED
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kala_paddhati_profile_natural_key
        UNIQUE (chart_id, factor_family, convention_id, version)
);
```

**Seeded by the migration, not by a writer** — it is versioned *config data*, exactly like the
weights-v0 seed (brief §2.5.4), and ADJUDICATION-8's stated reversibility ("`paddhati_v02`
supersedes `v01` by insert; no code, no schema, no rebuild") only holds if it is config rather
than build output. **Consequence: no `asset_registry` seed row, no `count_sql`, no DAG edge, no
new writer.** Do not invent one.

Seed rows for `482012f1`, verbatim from ADJUDICATION-8 parts (1)–(3):

| field | row A (the operative convention) | row B (the declared divergence slot) |
|---|---|---|
| `factor_family` | `agnivasa` | `agnivasa` |
| `convention_id` | `agnivasa_tithi_element_prithvi` | `agnivasa_muhurta_chintamani_arithmetic` |
| `school_tag` | `corpus_default` | `muhurta_chintamani` |
| `constraint_role` | **`hard`** — an unfavourable-Agnivāsa candidate is **eliminated**, not down-scored, and appears in the gap report with Agnivāsa named as the eliminating constraint | `hard` |
| `convention_status` | `computed` | **`declared_not_computed`** |
| `provenance` | `L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)` | — |
| `corpus_gap_ref` | — | the Muhūrta-Chintāmaṇi translation work item |
| `native_confirmed` / `awaiting_native_confirmation` | `FALSE` / `TRUE` | `FALSE` / `TRUE` |
| `version` | `paddhati_v01` | `paddhati_v01` |

Version selection is `ORDER BY version DESC LIMIT 1` — a **string** sort, so the zero-padding is
mandatory (`paddhati_v10` would otherwise sort below `paddhati_v2`). This is the same trap
ADJUDICATION-2 called out for `ne_v01`; it is repeated here because it bites per-table.

**The three rails ADJUDICATION-8 attaches, restated as build requirements:**
1. Row A is served as the **operative** rule **and simultaneously as an unconfirmed one**. The
   coverage census states, verbatim: *"agnivāsa convention = corpus default (tithi-element,
   pṛthvī-favourable); the native's lineage convention is not on record."*
2. Row B is **never computed and never enters a candidate's grading.** It exists so the
   divergence surface is real rather than decorative. A `declared_not_computed` convention that
   silently participates in scoring is the exact failure the status exists to prevent.
3. What is on record is the native's **practice**, not his lineage's **convention content**.
   No builder may pin invented convention content and label it "the native's lineage."

Both canonical charts get the same seed shape; `1c826d5a`'s rows are seeded identically
(same corpus default, same `native_confirmed=FALSE`).

### 3.3 R3 — ritual-resonance mapping (item 37's other half)

Configuration → rite, per chart, via the remedy/deity ontology. **Substrate, in authority
order:**

1. **`brahma_activity_ontology`** — 12 activity classes, `significators` JSONB
   (`{strengthen_grahas, strengthen_houses, strengthen_varga, avoid}`), `fructification_rules`
   (`{timing_anchor, panchanga_rules, classical_source}`), `citations TEXT[]`, and an FK
   `related_event_class → brahma_event_ontology.event_class_id`. **This is the spine** — it is
   the only existing table that maps a rite class to grahas *with citations* and links to the
   event ontology the field and the ledger both key on.
2. **`brahma_remedy_corpus`** — `planet` + `deity` + `remedy_type` + `timing_rules_jsonb`: the
   only in-DB graha→deity→rite triple.
3. **`bodha_rm_resonances`** — the chart's own per-graha `resonance_score` / `weakness_score` /
   `remedy_priority_class`: the "that graha's load-bearing role in THIS chart" factor.
4. **`bg_muhurta_activity_rules`** — 329 rows, `activity_class` ∈ {vivah, griha_pravesh,
   vyapara, yatra, property_purchase, **mantra_initiation**, **upaya_ritual**,
   sadhana_initiation} × `factor_type` ∈ {tithi, nakshatra, vara} × `factor_id` (integer) →
   `quality_score` + `source_citation`.

> **The `bg_muhurta_activity_rules` blocker, and how R-1 unblocks it.** The item-36 engine
> explicitly **excludes** its `rite_specific_resonance` Pareto axis, with the disclosed reason
> that the table keys on integer `factor_id` while candidates carry limb *names*, and the
> name→id map was (correctly) refused as invented data. ADJUDICATION-10 accepted that exclusion
> **on condition** that it stays explicit and visible (`axes_evaluated` minus the axis, with
> `reason='pending_items_6_7_activity_id_mapping'`), is never imputed, and is never silently
> dropped from the axis count.
> **R-1 makes the map real rather than invented:** the new `nakshatra`, `vara` (and, if taken,
> `tithi`) lattice families carry the limb's canonical **id** in `detail` alongside its name,
> because the emitter reads it from `panchang_engine`'s own numbered tables — the same source
> `bg_muhurta_activity_rules.factor_id` was populated from. The join then rests on one
> deterministic source, not on a hand-written correspondence.
> **RAIL:** Lane R may enable the `rite_specific_resonance` axis **only** if the emitter
> genuinely carries the id from `panchang_engine`. If for any reason it does not, the axis stays
> excluded with ADJUDICATION-10's exact disclosure, unchanged. Enabling it on a hand-mapped
> correspondence is a B.10 violation and a gate failure.

**Resonance scoring — Mode 1's four factors** (Elevation §8), each named with its source and its
honest-absent behaviour:

| Factor | Source | When unavailable |
|---|---|---|
| **Structural resonance** | `brahma_activity_ontology.significators` × `brahma_remedy_corpus.deity/planet` × `bodha_rm_resonances` for THIS chart | `honest_empty` naming which of the three was missing |
| **Temporal intensity** | the field's λ for the rite's domain — `kala_field_windows` | **empty in production today** (N_e blocker) ⇒ the factor is reported `not_computed (field empty — ka_kshetra has written no rows; see the N_e critical path)` and is **dropped from the product with renormalisation over present factors** (Elevation §6.1 / the ADJUDICATION-10 precedent), never imputed and never silently zero-filled |
| **Election quality** | the lattice + `adjudicateCandidates`' `judgment_ledger` | `honest_empty` |
| **Rarity** | cohort-scored scarcity via `bg_cohort` | `not_computed` if the cohort asset is dormant |

The renormalisation clause is what keeps Mode 1 **shippable while the field is empty** — the
same reasoning as U-2/U-3, applied to the score vector. The served vector always states which
factors were present; a caller can never mistake a 3-factor score for a 4-factor one.

### 3.4 R4 — `kala_ritual_get` Modes 1–2 REAL (item 40) + the sky-pattern compiler

Two new libraries, both owned by Lane R, both *beside* the frozen engine and neither a second
copy of it:

**`platform-mcp/src/lib/kala_sky_pattern.ts`** — the Mode-2 constraint compiler + coarse-to-fine
searcher.

- Input: `sky_pattern_spec v1`, versioned from Elevation §8's v0 sketch. Constraint kinds,
  frozen: `planet_state` · `mutual_configuration` · `chart_relative` · `panchanga` ·
  `panchanga_not` · `residence` · `kalam_not` · `transit_contact` · `natal_yoga_activation`.
  **Every kind maps 1:1 to a lattice/census factor family**; a spec naming a factor the census
  marks `not_in_corpus` triggers the drop-and-report precedence rule (§6.2), never a silent skip.
- Search: coarse-to-fine over the lattice atoms — year/month pruning on the coarse families,
  then day-grade, then the intra-day atom set. Because every factor is piecewise-constant on the
  atoms, evaluation is exact per atom and **no sampling interval exists**.
- Chart-relative constraints (`tara_bala`, `chandrashtama`, transit-over-natal-point) are applied
  as a **post-filter over atoms**, reading the chart's own values from `chart_facts` by
  `fact_id` — never recomputed (§N.5). The janma-nakṣatra `fact_id` used is carried in the
  response.
- Output: `SkyPatternSearchResult { candidates, gap_report, coverage, precision }`.

> **Why `SkyPatternGapReport` is a distinct type from the engine's `LatticeGapReport`, and why
> that is NOT a second engine.** They answer different questions. `LatticeGapReport` (frozen,
> in `kala_lattice_query.ts`) answers *"which factor families did the census not cover?"* and
> its `next_occurrence` is hard-`null` by deliberate design — the engine refuses to invent a
> date. `SkyPatternGapReport` answers *"which constraint eliminated this horizon, and when does
> the declared pattern next occur?"* — a question only the Mode-2 searcher can answer, because
> only it holds the spec. It **composes** the lattice report (embeds it verbatim under
> `census: LatticeGapReport`) rather than reimplementing any of it, and it computes
> `next_occurrence` by continuing the same coarse scan past the horizon until first
> satisfaction or a stated scan ceiling. **This is required by fixture PASS condition 1** (§6.2),
> which cannot be discharged on an empty result without a next-occurrence answer.

```ts
export interface SkyPatternGapReport {
  statement: string
  eliminating_constraint: { kind: string; key: string; detail: string } | null
  constraints_evaluated: SkyPatternConstraintDisposition[]   // one per spec constraint
  next_occurrence: { start_utc: string; end_utc: string } | null
  next_occurrence_state: 'found' | 'not_within_scan_ceiling' | 'not_searched'
  scan_ceiling_utc: string | null
  census: LatticeGapReport            // embedded verbatim from the frozen engine
}
```

`next_occurrence_state` exists so an absent date is never ambiguous between "does not occur" and
"we stopped looking" — the §N.8 Earned-Signal discipline applied to a nullable field.

**`platform-mcp/src/lib/kala_ritual_resonance.ts`** — Mode 1's four-factor scorer (§3.3), the
configuration→rite mapping, and the paddhati-profile reader. It exposes the resolved convention
set to the compiler so `residence` constraints resolve `per: 'paddhati_profile'` correctly.

**Both modes end at `adjudicateCandidates`.** The candidate intervals the searcher produces are
handed to the **frozen** engine, which returns the `JudgmentLedger` and the `LatticeAdjudication`
block. ELECT does exactly this today. That shared terminal call **is** the one-engine rule made
concrete, and the CI detector for it is a source-level assertion (§6.3 D-ONE-ENGINE).

**Precision regime.** Every candidate carries:
```ts
precision_regime: 'intra_day' | 'day_grade'
precision_basis: string      // names the coarsest binding factor family
```
`intra_day` iff **every** binding constraint is pāñcāṅgika or day-part (both intrinsically
sub-day astronomical instants). The moment a `transit_contact` or `mutual_configuration`
constraint binds, the candidate degrades to `day_grade` **and says which constraint did it** —
that is Elevation §8's honesty applied in the correct direction. Conservatively labelling a
purely-pāñcāṅgika candidate `day_grade` is applying it *backwards* and is an explicit FAIL of
fixture PASS condition 2.

### 3.5 R5 — Mode-3 pairing in ELECT (item 38's closing half) — and the trap

**What lands:** `kala_elect_get` serves the act-time slate **and** the paired preparatory rite
with its own best time, as one answer. The `ritual_pairing` coverage entry in `elect.ts` —
today an unconditional `notInCorpusCoverage('ritual_pairing', "…is not yet wired; this response
serves the act-time slate only.")` — flips to a genuinely-conditioned `computed` /
`honest_empty`.

Mechanically: for each surviving act-time candidate, Lane R runs the Mode-1 resonance scorer
(§3.3) scoped to the undertaking's `related_event_class`, over a **preparatory horizon ending at
the act-time candidate's start**, and returns the best-scoring rite window as
`candidate.paired_rite: { rite_id, rite_class, window, score_vector, judgment_ledger,
efficacy_tier, citation } | null`. A `null` with a reason is a legal and frequent answer.

**The Mode-3 rule gets STRONGER here, not weaker.** ELECT gaining the rite half is exactly what
makes `kala_ritual_get`'s redirect *correct* rather than merely *disciplined* — the redirect now
points at a surface that genuinely answers the whole question. Lane R must re-run
`mode3_single_route_gate.ts` after this change and record the result.

#### 3.5.2 The `ritual.test.ts` source-scan trap (read this before touching `ritual.ts`)

`ritual.test.ts` contains a **source-text regex rail** asserting that `ritual.ts` matches none
of: `\bfetch\(` · `callSidecarPath\(` · `callPlatformPrim\w*\(` · `callRegistryCap\w*\(` ·
`/muhurta_finder/i` · `\/api\/compute\/`. At W0 that was exactly right: the file computed
nothing, so *any* I/O was a passthrough. At W4 the file must genuinely read the lattice — which
means `callPlatformPrimitive` appears in its dependency graph — and a builder who takes the
shortest path to green will delete the rail. **That would silently retire the campaign's
strongest Mode-3 guarantee.**

> **DESIGN RULING R-2 (binding; reversible).** The rail is **narrowed, never deleted**, and the
> narrowing is justified in the test file itself:
> - **KEPT, verbatim and permanently:** `/muhurta_finder/i` and `\/api\/compute\//`. These are
>   the act-time-slate substrate. `ritual.ts` naming either of them *is* the Mode-3 passthrough
>   the rule forbids, at W4 or ever.
> - **KEPT:** a new assertion that `ritual.ts` exports no symbol and returns no field matching
>   `/slate|act_time|undertaking_window/` — the *outcome* rail, which is what actually matters
>   and is stronger than the I/O proxy it replaces.
> - **KEPT:** `isMode3ShapedRequest` and `buildMode3WrongViewResponse` remain synchronous and
>   pure — structurally incapable of awaiting I/O. The detector still runs FIRST,
>   unconditionally, before any Mode-1/2 code path.
> - **NARROWED:** the generic I/O ban is replaced by an **allowlist** — `ritual.ts` may reach
>   the lattice **only** through `fetchLatticeSubstrate` (the frozen engine's own fetcher) and
>   through Lane R's two new libs. A direct `callPlatformPrimitive` call in `ritual.ts` remains
>   a FAIL; the allowed path is one hop through the shared engine, which is also what enforces
>   the one-engine rule at the import graph level.
>
> The narrowing is recorded in the test file's header with this ruling's id, so a future reader
> sees a deliberate, argued change rather than a weakened gate.

### 3.6 R6 — Mode-1 opportunities in the AHEAD 90-day digest (the D4 clause)

`ahead.ts` already has the digest and already carries an explicit, honest placeholder:

```ts
export interface AheadDigestItem {
  kind: 'temporal_window' | 'probabilistic_projection' | 'gulika_kalam'
      | 'recurrence_ladder_point' | 'mudda_dasha_varsha'
  …
}
const RITUAL_OPPORTUNITIES_NOTE =
  'Ritual-opportunity rows (kala_ritual_get Mode 1) are not included in this digest — that ' +
  'computation lands at wave W4 …'
```

Lane R adds `'ritual_opportunity'` to the `kind` union, populates it from the Mode-1 scorer
bounded to the digest's own `[as_of_date, digest_to_date]` window, and **replaces the note's
semantics** — it becomes either an empty string (rows present) or an honest-empty statement
**naming the horizon actually searched**, which is what the W4 gate asserts. The digest stays a
*selection* over already-computed rows (its stated discipline: "SELECTING, never computing") —
Mode 1 is computed by the ritual path and joined, not recomputed inside `ahead.ts`.

---

## §4 — Lane S: the Unified Intervention Ledger (item 42, `mi_sankalpa`)

### 4.1 The three-store problem, and the ruling that resolves it

Item 42 says: *extends standing-predictions machinery, **NO parallel store***. There are, today,
**three** stores that could be meant:

| Store | Written by | Character |
|---|---|---|
| `brahma_prospective_ledger` | `fileProspectivePrediction()` (TS) only; `filing_method` CHECK = `'explicit_filing_tool'`; falsifier mandatory; shape-vs-`temporal_shape` trigger; DR-16 adverse gate | the **governance-sealed pre-registration** store (§3.5.E: "locked at emission… never modifiable") |
| `mimamsa_predictions` | `mi_bhavisya` (Python), status-preserving delete | the **engine's own forecast output**, rebuilt each build |
| `mimamsa_calibration` / `mimamsa_reliability` | `mi_pramana` | scoring/calibration outputs |

> **DESIGN RULING S-1 (reversible — an FK choice, no data destroyed either way).** The
> Intervention Ledger's prediction spine is **`brahma_prospective_ledger`**, by
> `prediction_id` FK. It is the store with pre-registration semantics, a mandatory falsifier,
> and an enforced explicit-filing provenance — which is precisely what a three-armed study of
> *election itself* requires. `mimamsa_predictions` is a rebuildable engine artifact and would
> lose the pre-registration seal on every rebuild.
> **`mi_sankalpa` therefore NEVER inserts into `brahma_prospective_ledger`** — it could not
> anyway (the `filing_method` CHECK is a deliberate governance wall against exactly this), and
> it must not try. Filing happens at serve time through the sanctioned HTTP action (§4.4); the
> writer records the intervention and **references** the prediction. That is "extends, no
> parallel store" satisfied literally: one prediction store, one new intervention table that
> points at it.

### 4.2 `mimamsa_intervention_ledger` — the table

Elevation §10's entry, made concrete, with the three-armed study fields:

```sql
CREATE TABLE IF NOT EXISTS mimamsa_intervention_ledger (
    intervention_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                UUID        NOT NULL,
    -- WHAT
    intent                  TEXT        NOT NULL CHECK (length(trim(intent)) > 0),
    intervention_class      TEXT        NOT NULL
        CHECK (intervention_class IN ('upaya', 'yajna', 'elected_activity')),
    rite_or_activity_class  TEXT        NOT NULL,
    event_class             TEXT        REFERENCES brahma_event_ontology(event_class_id),
    -- WHEN
    elected_window          TSTZRANGE   NOT NULL,
    precision_regime        TEXT        NOT NULL
        CHECK (precision_regime IN ('intra_day', 'day_grade')),
    precision_basis         TEXT        NOT NULL,
    -- WHY (the adjudication record at election time — frozen, never recomputed)
    adjudication_record     JSONB       NOT NULL,   -- the JudgmentLedger verbatim
    score_vector            JSONB       NOT NULL,   -- the 4-factor vector + which factors were present
    efficacy_tier           TEXT        NOT NULL
        CHECK (efficacy_tier IN ('classically_attested','traditional','speculative_extension')),
    source_citation         TEXT        NOT NULL CHECK (length(trim(source_citation)) > 0),
    paddhati_version        TEXT        NOT NULL,   -- the convention set that produced it
    -- THE PREDICTION (spine; §4.1 S-1)
    predicted_differential  TEXT        NOT NULL,   -- "this window vs baseline", stated
    prediction_id           UUID        REFERENCES brahma_prospective_ledger(prediction_id),
    -- THE THREE-ARMED STUDY
    study_arm               TEXT        NOT NULL DEFAULT 'elected_pending'
        CHECK (study_arm IN ('elected_pending','acted_with_election',
                             'acted_without_election','elected_not_acted')),
    performed               BOOLEAN,                -- NULL = not yet attested; native-attested only
    performed_at            TIMESTAMPTZ,
    performed_attested_by   TEXT,
    outcome_event_id        UUID        REFERENCES life_events(id),
    outcome_linked_at       TIMESTAMPTZ,
    -- PROVENANCE
    authority_basis         TEXT,                   -- item 44: the field window-id / ELECT candidate id
    filed_by                TEXT        NOT NULL,
    engine_version          TEXT        NOT NULL,
    build_id                UUID,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mimamsa_intervention_ledger_natural_key
        UNIQUE (chart_id, intervention_class, rite_or_activity_class, elected_window)
);
```

Indexes: `(chart_id, study_arm)`, `(event_class)`, `(prediction_id)`, GIST on `elected_window`.

**`performed` is nullable on purpose.** `NULL` means *not yet attested* — distinct from `FALSE`
(attested not-performed, which is study arm `elected_not_acted` and is real evidence). A boolean
that cannot say "I don't know" would silently convert absence into a negative observation and
corrupt the study. `performed` is **native-attested only**, exactly like LEL entries
(brief §7: "LEL entries native-only").

### 4.3 The writer

```python
@register("mi_sankalpa")
class MiSankalpaWriter(WriterBase):
    asset_id = "mi_sankalpa"
    has_substeps = False          # LIGHT writer — run(ctx) -> WriterResult
```

Conventions taken from the live L5 layer (`mi_bhara.py` is the newest and best-documented
precedent; `mi_vistara.py` is the minimal light-writer template):

- `chart_id = ctx.config["chart_id"]`, raising if absent (per-chart asset).
- Runs on `ctx.db_conn`; **never** commits/rolls back/closes; never writes `asset_throughput`.
- Registration is automatic — `writers/__init__.py` auto-discovers by `pkgutil` walk. There is
  no index file to edit and no manual registration list.
- **Idempotency (§N.3, the status-preserving variant — this is load-bearing).** Adjudicated and
  native-attested rows are irreplaceable; only unresolved rows are this writer's rebuildable
  output:

```sql
DELETE FROM mimamsa_intervention_ledger
 WHERE chart_id = %s
   AND study_arm = 'elected_pending'
   AND performed IS NULL
   AND outcome_event_id IS NULL;
```

  This is `mi_bhavisya`'s exact pattern (`… AND lifecycle_status IN ('pending','due')`),
  transposed. **A blanket `DELETE … WHERE chart_id = %s` here destroys native-attested outcome
  data and is a data-loss defect, not a style choice.**
- **Honest degradation, named** (the `mi_bhara` `NOTE_*` precedent): `NOTE_NO_INTERVENTIONS`
  (`'no_filed_interventions'`), `NOTE_FIELD_ABSENT` (`'kala_field_absent'` — the predicted
  differential's λ baseline is unavailable while `ka_kshetra` writes zero rows; the row is
  written with `predicted_differential` stated in structural terms and the note recorded),
  `NOTE_LEDGER_TABLE_ABSENT`. Each returns an honest zero/partial `WriterResult(notes=…)`
  rather than raising — following `mi_bhavisya`'s `_table_exists` guard.
- **Falsifier resolution first.** `mi_bhara`'s stated ordering — *"score the LEL against every
  open prospective ledger entry BEFORE any weight moves, so a refit cannot change what counted
  as a hit"* — binds here identically: `mi_sankalpa` resolves `outcome_event_id` links and
  `study_arm` transitions **before** it computes any aggregate. Reuse
  `services/mi_bhara/living_lel.py`'s `score_predictions_against_event()` rather than writing a
  second matcher.

**Study-arm assignment (deterministic, and it must be able to say "unknown"):**

| Arm | Assigned when |
|---|---|
| `elected_pending` | filed, no attestation yet (`performed IS NULL`) |
| `acted_with_election` | `performed = TRUE` and `performed_at` falls inside `elected_window` |
| `elected_not_acted` | `performed = FALSE`, attested |
| `acted_without_election` | a LEL event of the same class with no matching ledger row inside its window — this arm is **derived from the LEL**, and its row is written with `prediction_id = NULL` and a `derived_from_lel` marker in `adjudication_record`, because there was no election to record |

The fourth arm is what makes it a *study* rather than a log, and it is the only arm the writer
originates rather than records.

### 4.4 The filing spine (`intervention_filing.ts` + the client widening)

`platform-mcp/src/client.ts` exposes `callPlatformWrites(action, params, principal)` with the
action type **narrowed to a three-member union**: `'log_prediction' | 'record_outcome' |
'flag_disagreement'`. The route it targets (`platform/src/app/api/mcp/writes/[action]/route.ts`)
**already implements `prospective_ledger_file`** — the gap is purely the TS union.

Lane S's spine PR:
1. widens that union to include `'prospective_ledger_file'` (one line, one file — declared here
   because `client.ts` is shared and this is the only W4 edit to it);
2. adds `platform-mcp/src/lib/intervention_filing.ts` exposing one function used by all three
   lanes:

```ts
export type FilingState =
  | 'not_requested' | 'filed' | 'filing_path_not_yet_available'
  | 'filing_refused_adverse_class' | 'filing_failed'

export async function fileInterventionFalsifier(
  input: {
    chart_id: string
    intervention_class: 'upaya' | 'yajna' | 'elected_activity'
    event_class: string
    claim: string
    falsifier: string            // MANDATORY — the route rejects a blank one
    confidence: number           // strictly in (0,1) — the route rejects the endpoints
    window: { start: string; end: string }
    source_citation: string
    model: string
    formula_version: string
  },
  principal: Principal,
): Promise<{ state: FilingState; prediction_id: string | null; detail: string | null }>
```

It **adds no validation of its own** beyond the adverse-class refusal (§5.3) — every other rule
(`claim_shape` vs `temporal_shape`, DR-16's five-property adverse gate, `filed_by` stamping) is
already enforced server-side, and duplicating a validator is how two copies drift.

### 4.5 Efficacy reporting (the E6 read-back that Lane U consumes)

One read-only aggregate over the ledger, exposed as a helper Lane U calls:

```
per (chart_id, intervention_class, rite_or_activity_class):
  n_elected_and_acted · n_acted_without_election · n_elected_not_acted
  · n_outcome_linked · n_resolved_prospective_hits
```

Served with **no rate and no percentage** until the resolved count crosses the threshold the
ledger publishes alongside it. Below threshold the block is
`honest_empty(reason: 'n_resolved = <k>, below the reporting threshold; a rate here would be a
LAW ZERO violation')`. The count is always served; the *rate* is what is withheld. This is
Elevation §13's "no percentages before calibration", applied literally.

---

## §5 — The ethical / disclosure contract for remedy serving (MACRO_PLAN §3.5)

This is the wave that tells a human to act. Every rule below is a build requirement with a named
detector, not an aspiration.

### 5.1 Framing and calibration disclosure (§3.5.A.1–2, §3.5.G)

- Every intervention response carries the receptivity framing in the verdict slot — *"upāya
  prepares the vessel; it does not command the rain."* A template constant in
  `argument_composer.ts`'s existing verdict template, never a generative sentence.
- `verdict.tier` is `structural_prior` while `calibration_maturity.n_events = 0`. It may only
  read `calibrated_provisional` / `calibrated` when the maturity block's own numbers support it.
  The envelope already carries `calibration_maturity`; W4 populates it from Lane S's ledger
  rather than leaving `noLelCalibrationMaturity()`'s zeros in place when real numbers exist.
- **§3.5.G is a hard validity rule**, not advice: an output without a calibration band is not a
  valid output. Concretely, a served intervention row must carry `efficacy_tier` (the method's
  own honesty band), `source_surface` + `source_pk` (the method pointer), and — when a rate is
  served at all — its `n`. A row missing any of these is dropped with the reason recorded,
  never served bare.

### 5.2 Disclosure tier is stated, not assumed (§3.5.B)

Every W4 response carries a `disclosure` block:

```ts
interface DisclosureBlock {
  audience_tier: 'native_self' | 'cohort_subject' | 'acharya_reviewer' | 'public_redacted'
  basis: string                      // how the tier was resolved for this principal
  constraints_applied: string[]      // e.g. ['adverse_class_filing_refused']
}
```

Both canonical charts resolve to `native_self` (full output, full calibration disclosure,
unfiltered) — but the tier is **resolved and stated**, never defaulted silently. A tool that
assumes the most permissive tier is one principal-resolution bug away from serving a
non-consenting subject.

### 5.3 The self-harm guardrail (§3.5.C) — the one hard exclusion in this wave

§3.5.C is absolute and this wave must honour it mechanically, not by good intentions:

1. **No individualized mortality window, under any audience tier.** No W4 surface accepts, or
   diagnoses over, a mortality-class event.
2. **Suicide-adjacent output is disallowed under all tiers.** A hard exclusion list, evaluated
   before any computation runs — the same detector-first shape as `isMode3ShapedRequest`.
3. **Health-crisis and mental-health output require double red-team + explicit native sign-off.**
   In W4 this becomes: a diagnosis whose `event_class` resolves in `brahma_event_ontology` to
   `domain='health'` with `magnitude_floor IN ('major','life_altering')` is served **only** with
   `disclosure.constraints_applied` naming the requirement, and:

> **DESIGN RULING S-2 / U-5 (see §7 OQ-2 — the second question that genuinely wants
> ANTARYĀMIN).** For such classes, `fileInterventionFalsifier` returns
> `filing_refused_adverse_class` and files nothing. The falsifier is still *stated* in the
> response text (so the claim remains falsifiable and honest), but it is not auto-filed into the
> pre-registration ledger. Rationale: auto-filing a machine-generated adverse health prediction
> is exactly the case DR-16's five-property adverse-disclosure gate exists to slow down, and
> §3.5.C requires native sign-off *before any output leaves a session* — which an autonomous
> lane cannot obtain. Refusing to file is the conservative, reversible posture; the native can
> file manually at any time through the same sanctioned route.

### 5.4 Pre-registration integrity (§3.5.E)

A filed falsifier is **locked at emission**. `brahma_prospective_ledger` already enforces this
structurally. W4 adds one rule of its own: **`mi_sankalpa` never updates
`adjudication_record`, `score_vector`, `predicted_differential`, or `paddhati_version` on an
existing row.** The adjudication record is a *snapshot of the judgment at election time*; a
rebuild that "refreshes" it destroys the evidence the three-armed study exists to collect. If
the convention set changes, that is a **new row under a new `paddhati_version`**, never an
in-place edit — which is also exactly what ADJUDICATION-8's reversibility claim depends on.

---

## §6 — The canned W4 Mode-2 fixture: the discharge path, condition by condition

The fixture is authoritative (brief §3 W4). **The Conductor discharges it exactly and does not
substitute an easier query.** This section maps every clause to a concrete artifact.

### 6.1 Where the fixture lives, and the path correction

The brief writes `tests/fixtures/yajna_mode2_gate.json`. **That directory does not exist**, and
neither does `platform-mcp/tests/` — the MCP package's convention is `test/` (singular), included
by `vitest.config.ts` as `test/**/*.test.ts`. The only fixtures directory under the package is
`platform-mcp/test/accuracy/fixtures/`.

> **DESIGN RULING R-3 (reversible — a path, nothing more).** The fixture lands at
> **`platform-mcp/test/fixtures/yajna_mode2_gate.json`**, and the brief's literal string is
> recorded in the file's own `_source` field plus in this ruling, so the divergence is
> deliberate and traceable rather than a silent relocation. Matching the package's real layout
> beats matching a path that has never existed.

The fixture file is the **first committed instance of `sky_pattern_spec v1`** (Elevation §8:
"the W4 fixture is its first committed instance"), so its shape is also the schema's worked
example:

```json
{
  "_source": "SHAD_DARSHANA_BRIEF_v2_0.md §3 W4 — CANNED W4 MODE-2 TEST FIXTURE (authoritative). Brief path string: tests/fixtures/yajna_mode2_gate.json; actual path per KALA_W4_UPAYA_DESIGN_v1_0.md ruling R-3.",
  "spec_version": "sky_pattern_spec_v1",
  "all": [
    { "planet_state":   { "body": "Guru", "in": { "hora_lord": true } } },
    { "panchanga":      { "vara": "guru-vara" } },
    { "residence":      { "kind": "agnivasa", "state": "favorable", "per": "paddhati_profile" } },
    { "panchanga_not":  { "karana": ["vishti"] } },
    { "chart_relative": { "kind": "tara_bala", "not_in": ["vadha", "vipat", "pratyak"] } },
    { "kalam_not":      ["rahu_kalam"] }
  ],
  "horizon": { "months": 24 }
}
```

The gate script `platform/scripts/census/shad_darshana_gates/yajna_mode2_fixture_gate.ts`
follows the directory's established conventions exactly: `_mcp_client.ts` for the live call,
`_report.ts` for `GateResult`/`printGateReport` (exit 0 unless a live FAIL; SKIPPED when the
tool is unreachable — **never weakened to force green**), PLAN/LIVE split on `MCP_SERVER_URL`.
It is added to `.github/workflows/shad-darshana-ci-skeletons.yml` alongside the existing gates.

### 6.2 The four PASS conditions → four detectors

**PASS 1 — non-empty, or honestly-empty.**
Detector: `candidates.length >= 1` **OR** (`candidates.length === 0` **AND**
`gap_report.eliminating_constraint !== null` **AND** `gap_report.next_occurrence_state !==
'not_searched'`). An unexplained empty result FAILS — and note that without §3.4's
`SkyPatternGapReport`, an empty result is *structurally* undischargeable, because the frozen
engine's `next_occurrence` is hard-`null`. That is why R4 builds the Mode-2 gap report.
Expected shape per ADJUDICATION-8's own arithmetic: Guru-vāra (~104 days in 24 months) ×
Pṛthvī tithi (7 of 30 ≈ 23%) × non-viṣṭi × tārā-bala (excluding 3 of 9) ≈ **10–16 candidate
day-hours before the Guru-horā and rāhu-kālam intra-day cuts** — narrow, non-empty. The gate
asserts the PASS condition, **not** the predicted count; a count assertion would be fitting the
test to the prediction.

**PASS 2 — precision labels correct.**
Detector: every candidate has `precision_regime === 'intra_day'` **and** a non-blank
`precision_basis` naming a pāñcāṅgika or day-part family. This fixture is pāñcāṅgika-bound
throughout, so `day_grade` here is a **FAIL** — it would mean §8's precision-regime honesty is
being applied backwards. Second assertion: no constraint in the fixture is of kind
`transit_contact` or `mutual_configuration`, so nothing in it can legitimately degrade the label
(this asserts the *reason* the label is right, not just the label — §N.8).

**PASS 3 — judgment ledger present.**
Detector: every candidate carries a `judgment_ledger` with all of `dosas_present`,
`pariharas_applied`, `residual_dosas`, `net_standing` (from the frozen engine's `JudgmentLedger`
type), **and** the response carries the paddhati divergence block. Per ADJUDICATION-8, the
honest value today is exactly:

```json
"paddhati_divergence": {
  "state": "none_computed",
  "reason": "one convention computable; agnivasa_muhurta_chintamani_arithmetic is declared_not_computed pending muhurta_chintamani translation"
}
```

That is a **genuine divergence block reporting a genuine gap** — not a substitution, and it does
not require inventing a second rule table. The gate asserts the block's presence and that its
`state` is drawn from the closed set `{'none_computed','diverges','agrees'}`.

Note on cancellations: every `bg_parihara_rules` row is `scope='natal'` except the one
muhūrta-scope Abhijit row ADJUDICATION-10 authorises. So `pariharas_applied` will usually be
empty and residuals will be reported **uncancelled with the gap named** — which is correct, and
the gate must not treat an empty `pariharas_applied` as a defect. Pressing a natal-scope
cancellation into muhūrta service is a fabricated cancellation and a §N.5 authority inversion
(ADJUDICATION-10 Part 2, affirmed).

**PASS 4 — census honesty.**
Detector: the coverage block enumerates **all six** constraints, each with a state from
`{computed, honest_empty, not_in_corpus}` and, for the non-computed ones, a reason. After R-1's
lattice extension, all six are expected `computed` — with `tara_bala` explicitly labelled
*computed chart-relative at query time* and citing the janma-nakṣatra `fact_id`, **not** claimed
against the global census row (which correctly stays `not_computed`). The gate asserts six
entries, one per constraint, no more and no fewer.

**Precedence between (1) and (4)** — copied from the brief so the Conductor never has to judge:
a `not_in_corpus` constraint is **dropped from the conjunction** and the search runs on the
remaining five. If the reduced search returns candidates, (1) is satisfied normally and the
fixture is **PARKED-HONEST** solely on the missing rule table. If it returns zero, (1) still
requires the gap report to name the eliminating constraint. **An empty result with neither a
`not_in_corpus` flag nor a gap report is a FAIL in every case** — "it returned nothing" is never
itself an explanation.

### 6.3 The both-charts clause — with a detector that cannot be faked

The fixture is mirrored on `1c826d5a` with its own janma-tārā and paddhati profile, and **the two
charts must return *different* candidate sets. Identical output across charts FAILS.**

A naive inequality assertion is weak (it passes for the wrong reasons — nondeterminism, a
timestamp, a differing row order). The detector is therefore **two-part**:

1. `setOf(candidate_ids | 482012f1) !== setOf(candidate_ids | 1c826d5a)` — the brief's own clause.
2. **The difference must trace to the chart-relative constraints.** Re-run both charts with the
   `chart_relative`/`tara_bala` constraint removed from the conjunction; the two candidate sets
   must then **coincide**. If they still differ, something other than the chart is varying the
   answer — nondeterminism, or a leak — and the gate FAILS with that diagnosis.

Part 2 is what makes this an earned signal rather than an inequality that happens to hold.

`D-ONE-ENGINE` (a separate, always-on assertion): a source-level test that `ritual.ts`'s Mode-1/2
path and `elect.ts` both import `adjudicateCandidates` from `../../lib/kala_lattice_query.js`,
and that no second definition of `adjudicateCandidates`, `buildLedger`, or a Pareto `dominates`
exists anywhere under `platform-mcp/src`. Two implementations would eventually disagree about
the same Tuesday.

---

## §7 — Migration-number reservation: the procedure (do NOT hardcode a range)

**Every prior ranged reservation in this campaign went stale and forced a renumber** — 467–476,
then 474–483, then 472–495. The ledger's own conclusion is now doctrine: *"any future
ṢAḌ-DARŚANA migration should re-verify the actual combined max fresh rather than assume that
range is still free or still reserved."* This document therefore reserves **no range** and
specifies a procedure instead.

**The rule** (`MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §3, and `migration_number_guard.ts`'s own
implementation): `next = max(highest in platform/migrations/, highest in
platform/supabase/migrations/) + 1`. **Both directories share one global sequence** and the
runner de-dupes by *filename*, not by number — so a duplicate number is not caught by the
runner and must be caught by the guard. New migrations land in **`platform/supabase/migrations/`**
(the observed-current convention, per that directory's own README).

**Run it, don't compute it:**

```bash
cd platform && npm run migration:next          # the guard's own allocator
cd platform && npm run guard:migration-numbers # E1–E4 collision checks
```

**Then widen the check past `origin/main`, because sibling lanes are the real hazard:**

```bash
git fetch origin --prune
# (a) max on origin/main — the protocol's stated read-point
git ls-tree -r --name-only origin/main -- platform/migrations platform/supabase/migrations \
  | sed 's|.*/||' | grep -oE '^[0-9]+' | sort -n | tail -1
# (b) max claimed by ANY ref, incl. unmerged shad-darshana/* branches
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin refs/heads); do
  git ls-tree -r --name-only "$b" -- platform/migrations platform/supabase/migrations 2>/dev/null \
    | sed 's|.*/||' | grep -oE '^[0-9]+'
done | sort -n | tail -1
# (c) UNCOMMITTED claims in sibling worktrees — where this campaign's live collisions actually are
ls .worktrees/*/platform/supabase/migrations .worktrees/*/platform/migrations 2>/dev/null \
  | grep -oE '^[0-9]+' | sort -n | tail -1
```

**Two reads, not one.** The number is allocated **at MERGE-LOCK time**, not when the builder
writes the file, and (a)+(b)+(c) are re-run then. Write the number in **both** the filename and
the `-- Migration NNN:` header and keep them in sync through any renumber.

**Observed state at the time this design was written (2026-08-01, integration tip `b14d41e4`) —
recorded as evidence that the procedure is necessary, NOT as a reservation:**

- `origin/main` combined max: **499**. `platform/migrations/` tops out at **474**.
- `shad-darshana/integration` and three sibling branches: **521** (`520_kala_kota_chakra.sql`,
  `521_kala_sudarshana_varsha.sql`, PR #999).
- **500–519 is unclaimed anywhere.**
- **522 is DOUBLE-CLAIMED right now**, in two uncommitted worktrees:
  `522_brahma_class_lifetime_counts.sql` (`shad-darshana-l0-ne-priors`) and
  `522_kala_moorti_nirnaya.sql` (`shad-darshana-w3-moorti-vedha`).
- **523 is double-claimed**: `523_bg_kota_chakra_rings.sql` and `523_kala_vedha_gochara.sql`.
- **524** is claimed by a committed-but-unpushed local branch
  (`shad-darshana/w3-abhijit-parihara`: `524_bg_parihara_rules_muhurta_extraction_context.sql`).
- Highest claimed **anywhere**: **524**. Highest **pushed** to any remote: **521**.

A lane that had trusted the last written reservation (472–495) would have collided immediately.
A lane that reads only `origin/main` would have taken 500 and collided with PR #999. A lane that
reads only pushed refs would have taken 522 and collided with two uncommitted siblings. **Run
(a), (b) and (c).**

> ⚠️ **The `/create-migration` skill at `.claude/skills/create-migration/SKILL.md` is stale and
> wrong** — it reads one directory (`platform/migrations/`, the legacy one) and writes there.
> That is precisely the defect `migration_number_guard.ts` exists to kill. Do not follow it;
> use `npm run migration:next`.

**W4's migration inventory (three files, numbers allocated at merge-lock):**

| Lane | Migration | Contents |
|---|---|---|
| R | `NNN_bg_muhurta_lattice_panchangika_families.sql` | widen `factor_family` CHECK to add `hora`, `vara`, `nakshatra` (+ optionally `tithi`, `nityayoga`, `karana`); `UPDATE asset_registry` `target_floor` to the **achieved** count after rebuild |
| R | `NNN_kala_paddhati_profile.sql` | the §3.2 table + the `paddhati_v01` seed rows for both canonical charts |
| S | `NNN_mimamsa_intervention_ledger.sql` | the §4.2 table + indexes + the `mi_sankalpa` `asset_registry` row |

Each is `CREATE TABLE IF NOT EXISTS` / `ALTER … IF NOT EXISTS`, `INSERT … ON CONFLICT DO UPDATE`
for registry rows, with an explicit DOWN block in a trailing comment (house style, see migration
460). Surgical, migration-guard reviewed, and **verified applied** — §N.4's re-scoped rule: the
deploy-time bulk runner is fine and intended; *blindly trusting it without verification* is not.

---

## §8 — Nirmāṇa build-tracker contract (brief §2.5)

### 8.1 What is and is not a new asset

| Thing | New `asset_registry` row? | Why |
|---|---|---|
| `mi_sankalpa` | **YES** — same PR as the writer | new `@register` data writer (§2.5.1) |
| `kala_paddhati_profile` | **NO** | versioned config seeded by migration, no writer (weights-v0 precedent, §2.5.4) |
| `bg_muhurta_lattice` extension | **NO** (existing row; `target_floor` updated) | extends an existing asset |
| Lane U's surfaces | **NO** | serving-only; creates no table |

### 8.2 The `mi_sankalpa` seed row (`platform/scripts/seed/asset_registry_seed.ts`)

```ts
{
  asset_id: 'mi_sankalpa',
  layer: 'mimamsa', sort_order: 14,              // mi_bhara is 13, the current highest
  sanskrit_name: 'Saṅkalpa',
  english_name: 'Intervention Ledger',
  english_description:
    'Unified intervention ledger — every elected act (upāya · yajña · elected activity) with '
    + 'its adjudication record, predicted differential, performance attestation and outcome '
    + 'linkage; the three-armed study of election itself',
  storage_type: 'postgres_table',
  target_table: 'mimamsa_intervention_ledger',
  count_sql: 'SELECT count(*) FROM mimamsa_intervention_ledger WHERE chart_id = $1',
  size_sql: "SELECT pg_total_relation_size('mimamsa_intervention_ledger')",
  target_floor: null,          // set to the ACHIEVED count after first build (§N.4)
  expected_volume_formula: null,
  expected_volume_inputs: null,
  volume_explanation:
    'Accumulates as interventions are elected and attested — not a deterministic target',
  depends_on: ['ka_kshetra'],
  scope: 'per_chart', is_active: true, estimated_seconds: null,
}
```

**Two CI traps, both real and both cheap to avoid:**

1. **`depends_on` must resolve INSIDE this same file.** `catalog_reconciliation.test.ts` builds
   its id set purely from the `ASSETS` array, never from the DB — an edge to an asset that
   exists only via a migration turns CI red. `ka_kshetra` was added to the seed file as a
   mirror of migration 494 (with `depends_on: []`, a documented divergence). **Lane S verifies
   `ka_kshetra` is present in the seed array at write time**; if it is not, the edge is
   `depends_on: []` with the reason recorded, and never a dangling id.
2. **The catalog-reconciliation check and `test_has_writer_completeness.py` must be green in the
   SAME PR as the writer.** A writer without a seed row is invisible to Nirmāṇa ⇒ the wave gate
   fails (§2.5.1).

**Why `ka_kshetra` and not `mi_bhavisya`:** brief §2.5.3 and `KALA_W2_FIELD_DESIGN §9.1` both
specify `mi_sankalpa.depends_on = ['ka_kshetra']`. The edge is L3→L5, acyclic. And per §2.5.4's
acyclicity rule, **`ka_kshetra` never lists `mi_sankalpa`** — the ledger flows forward only.

### 8.3 L0 gating (§2.5.2) and the rolling horizon (§2.5.6)

`bg_muhurta_lattice` is a `bg_*` global asset built **only** by explicit super-admin L0 trigger,
never auto-pulled into a user's chart build. A per-chart build whose L0 upstream is dormant shows
the dependent as **blocked** — correct behaviour, not a defect. So the W4 gate requires:

> **the extended lattice is rebuilt in PRODUCTION before the first Mode-1/2 serving verification
> and before the fixture gate runs.** Otherwise the fixture fails on missing atoms, which is
> honest but is not a discharge.

The lattice's ~5-year rolling horizon ages. Its refresh cadence is recorded in the state ledger,
and the envelope's freshness attestation serves a stale horizon **as a flag, never silently**
(`buildKalaFreshness` already carries `stale` / `stale_reason`, and `stale` is deliberately
`boolean | null` so "not evaluable" is distinguishable from "fresh").

### 8.4 Item 44 (`authority_basis`) — reported here, HARD-gated at W6

`authority_basis` exists **nowhere** in `platform-mcp/src` today; `kala_envelope.ts`'s header
says so explicitly, and `authority_basis_census_seed.ts` honestly scores every path at zero. W4
does not fix that globally — but every W4 surface that makes a temporal claim **emits
`authority_basis`** naming the id it inherited (an ELECT candidate id, a lattice atom key, a
`pact_query` stage id, or a field window-id once the field is non-empty), and **computes no
window of its own** (rulings U-3, R-1). Lane R runs the census seed after its changes and records
the delta in the W4 close note. A W4 surface that computes its own window is a **build error**,
not a divergence to classify (brief §7).

---

## §9 — Gate W4 battery: every brief §3 W4 criterion → a concrete verification

Brief §3 W4's gate, clause by clause. Every row names an artifact that produces evidence; nothing
here is discharged by inspection or by a builder's self-report. Per §B.4, acceptance is by the
Opus Verifier against **LIVE production post-deploy**, on **BOTH** canonical charts, with four
dispositions and no "passed with caveats".

| # | Gate clause (brief §3 W4) | Discharged by | Detector that could make it read FALSE |
|---|---|---|---|
| **G1** | on `482012f1`: a weakly-promised event class returns **correct link diagnosis** | live `kala_upaya_get` call on an event class whose `pact_query` returns `denied_at_promise`/`denied_at_confirmation`; assert `diagnosis.failing_link` equals the stage `pact_query` itself halted at | a mismatch between `pact_status` and `failing_link`; a `failing_link` outside the closed set |
| **G2** | …+ **honestly-tiered non-empty ledger** | same call; assert `interventions.length >= 1`, every row carries `efficacy_tier` from the closed set + a resolvable citation, and `uncited_remedy_rows` is a **separate** array with its own count (§N.6) | any served row with a null tier; any uncited row appearing in `interventions` |
| **G3** | …+ **filed prospective entry** | second call with `adopt_intervention`; assert `filing_state === 'filed'` and `filed_prediction_id` resolves in `brahma_prospective_ledger` with `filing_method='explicit_filing_tool'` and a non-blank `falsifier` | a plain read that files (⇒ FAIL); a `filed` state with an unresolvable id |
| **G4** | **"pressure without delivery"** verified on an un-promised window | live call on an event class with no natal promise; assert the Six-Views §C.1 graded-gate language is served (window **served, not suppressed**, labelled *"temporal pressure without strong natal promise"*), and that a lever is still offered or an honest `no_lever` given | a suppressed window (silently absent) — the failure the amendment exists to prevent |
| **G5** | **Mode 1 returns ranked (window, rite) pairs with 4-factor score vectors** | live `kala_ritual_get` Mode-1 call; assert each pair carries `{structural_resonance, temporal_intensity, election_quality, rarity}` with **each factor's own state**, and that any absent factor is `not_computed` with a reason and renormalised out — never zero-filled | a 4-factor vector with an imputed value; a score with no factor-state breakdown |
| **G6** | **Mode 2 discharges the CANNED FIXTURE** | `yajna_mode2_fixture_gate.ts`, PASS conditions 1–4 (§6.2) + the two-part both-charts detector (§6.3) | each of the four conditions has its own named detector; §6.3 part 2 catches a difference that does not trace to the chart |
| **G7** | **an elected act files a complete Intervention Ledger entry** | live ELECT-with-pairing call, then a DB read of `mimamsa_intervention_ledger`; assert every NOT NULL column populated, `adjudication_record` equals the served `judgment_ledger` **byte-for-byte**, `study_arm='elected_pending'`, `performed IS NULL` | a row whose `adjudication_record` diverges from what was served (⇒ the snapshot is not a snapshot) |
| **G8** | **AHEAD digest carries ≥1 Mode-1 ritual-opportunity row, or an explicit honest-empty naming the horizon searched** | live `kala_ahead_get`; assert `digest_90d.items` contains ≥1 `kind:'ritual_opportunity'` **OR** `ritual_opportunities_note` names the exact horizon searched (dates, not "the horizon") | the W1 placeholder note surviving unchanged (it names W4 as future work — its presence post-W4 is itself the FAIL) |
| **G9** | **item 38 closes** — ELECT serves act-time + rite-time as one answer | assert `elect.ts`'s `ritual_pairing` coverage is no longer an unconditional `not_in_corpus`, and that ≥1 candidate carries a non-null `paired_rite` on ≥1 of the two charts (a `null` with a reason is legal per-candidate, not for every candidate on both charts) | an unconditional `computed` with no `paired_rite` ever populated — the `hora_ladder` inversion class, repeated |
| **G10** | **Mode-3 routing rule still holds** (brief §7, CI-asserted) | re-run `mode3_single_route_gate.ts` **and** the narrowed `ritual.test.ts` rail (§3.5.2) | `ritual.ts` naming `muhurta_finder` or `/api/compute/`; any slate-shaped field on a ritual response |
| **G11** | **ONE-ENGINE RULE** | `D-ONE-ENGINE` source assertion (§6.3) | a second `adjudicateCandidates`/`buildLedger`/Pareto `dominates` anywhere under `platform-mcp/src` |
| **G12** | **Nirmāṇa**: the wave's new data asset appears with DB-true counts on both charts (§2.5.1, implicit in every wave gate) | cockpit/stats read of `mi_sankalpa`'s `count_sql` on both charts; `catalog_reconciliation.test.ts` + `test_has_writer_completeness.py` green in the writer's own PR | a seed row missing ⇒ invisible to Nirmāṇa ⇒ gate fails |
| **G13** | **Both charts, identical coverage** (standing rail) | every clause above re-run on `1c826d5a`; coverage **concept sets** must be identical even where values differ | a concept present on one chart and absent on the other |
| **G14** | **Ethical framework respected** (§5) | assert every response carries a `disclosure` block with a resolved `audience_tier`; assert an adverse/health-class adoption returns `filing_refused_adverse_class` and files nothing | a defaulted tier; an adverse-class row appearing in `brahma_prospective_ledger` |
| **G15** | **W2G retro-clause** (brief §3 W2G) | if W2G closes **after** W4, the Mode-2 fixture is **re-run** and its precision-regime assertions must still pass; if W2G closed first, the clause is discharged retroactively at W4 | a fixture that only passes at one precision regime |

**Standing negatives re-verified at this gate (E8, the non-elevations register):** no generative
LLM call in any serving path · no percentage before calibration · no sub-day *transit* precision
claimed · legacy writers untouched and still serving · `kala_gochara_windows` data, the sealed
harness and `build_substep_progress` unmodified.

---

## §10 — Open questions this design deliberately does NOT decide

Two of these genuinely want ANTARYĀMIN, precisely because each touches a governance rail rather
than an engineering choice. The other two are recorded as in-design rulings that a Verifier or
the native may overturn cheaply; neither blocks a lane.

### OQ-1 (ANTARYĀMIN) — does an explicit `adopt_intervention` MCP call satisfy §11's explicit-filing governance?

`brahma_prospective_ledger` enforces `filing_method = 'explicit_filing_tool'` by DB CHECK, and
`prospective_ledger.ts`'s governance text is *"explicit filing only; chat is never mined."*
Ruling U-4 reads an explicit `adopt_intervention: {intervention_id, confidence, falsifier}`
parameter as an explicit filing action, with `filed_by` stamped from the resolved principal.

**The question is narrow and worth ruling deliberately:** the `filed_by` stamp becomes the *MCP
principal* rather than the native personally, and the *claim text* is engine-composed rather than
native-authored. Is that within `filing_method='explicit_filing_tool'`, or does item 26's
"auto-files a falsifiable prospective entry" require a distinct, native-visible confirmation step
(a portal action rather than a tool parameter)?

**Consequence either way — and note the lane is not blocked by this.** If ANTARYĀMIN rules for
the tool-parameter reading, U-4 stands as written. If it rules for a native-visible confirmation,
Lane U emits a **filing-ready payload** and `filing_state: 'awaiting_native_confirmation'`
instead of calling the route — the precedent already exists in `muhurta_finder.ts`, which emits a
prospective-ledger-shaped `prediction_filing` payload it deliberately does not persist. **Lane U
builds the payload either way**; only the final call is gated. Fully reversible; no schema.

### OQ-2 (ANTARYĀMIN) — may an adverse/health-class intervention auto-file at all?

Ruling U-5/S-2 refuses auto-filing for `brahma_event_ontology` classes with `domain='health'` and
`magnitude_floor IN ('major','life_altering')`, on §3.5.C ("health-crisis output requires double
red-team **and explicit native sign-off before any output leaves a session**") plus DR-16's
five-property adverse-disclosure gate. An autonomous lane cannot obtain native sign-off, so it
refuses to file and states the falsifier in text only.

**The question:** is refusal the right conservative posture, or does it under-serve the native's
own chart (audience tier `native_self`, where §3.5.B grants *full output, unfiltered*)? These two
clauses point in opposite directions for exactly this case, and the tension is real rather than
an oversight — §3.5.C is written as an absolute and §3.5.B as a tier grant.

**Recorded position:** refusal, because it is the reversible direction (a refusal can be
converted into a filing later; an adverse machine-generated prediction, once pre-registered
under §3.5.E's "locked at emission" seal, **cannot be unfiled**). But the ruling should be the
adjudicator's, not a builder's, because it narrows a chartered item-26 behaviour for a named
class of events.

### OQ-3 (in-design ruling; Conductor confirms, not adjudication-grade) — extending an item-36/41 asset

R-1 widens `bg_muhurta_lattice`'s `factor_family` CHECK and adds emitters to a writer that a
different lane landed three days earlier (PR #930). The change is additive, required by the
fixture, and doctrinally mandated by Elevation §9's completeness-by-construction. It changes the
asset's `target_floor` and re-points three census `evidence_pointer`s. **Recorded for the
Conductor's awareness, not as a blocker** — but if the item-36/41 lane is still live when Lane R
starts, the two must not both edit `bg_muhurta_lattice.py`.

### OQ-4 (in-design ruling) — the ledger's prediction FK

Ruling S-1 picks `brahma_prospective_ledger` over `mimamsa_predictions`. Recorded here because a
reader who knows only the phrase "extends standing-predictions machinery" could reasonably read
it the other way, and because three prediction-shaped stores exist. Reversible: the FK is one
column.

---

## §11 — What this design deliberately does NOT build

Stated so a builder does not helpfully add it, and so the W4 gate is not judged against it:

1. **No new MCP tool.** Items 26 and 40 fill in existing registered shells. `register_all.ts`
   and `registry_bridge.ts` are untouched by all three lanes.
2. **No Mode-3 anything in `kala_ritual_get`** — at W4 or ever (Elevation §8 clause 2).
3. **No praśna auto-cast.** Elevation §13 reserves praśna-at-every-query; W4 serves a pointer to
   `prashna_ask`, never an ambient cast.
4. **No second grading engine.** `kala_grading.ts` (W1 lite-v0) stays as-is; item 36's ledger is
   the depth layer; W4 adds neither a third convention nor a re-tuning of either.
5. **No field-dependent behaviour that blocks on the N_e critical path.** Temporal intensity is
   one factor of four, honestly `not_computed` and renormalised out while `ka_kshetra` is empty
   (rulings U-2, U-3, and §3.3's factor table).
6. **No sub-day transit precision.** Transit-edge constraints stay `day_grade` and say so. The
   `intra_day` label the fixture requires is earned by pāñcāṅgika/day-part limbs, which are
   intrinsically sub-day today — not by anticipating W2G.
7. **No second Agnivāsa convention table.** ADJUDICATION-8 part (3):
   `agnivasa_muhurta_chintamani_arithmetic` is registered `declared_not_computed` with a
   `corpus_gap_ref`, and **never enters a candidate's grading**. Transcribing a second rule table
   from memory is exactly what the ruling forbids.
8. **No muhūrta-scope cancellation invented from a natal rule.** ADJUDICATION-10 Part 2: a
   natal-scope cancellation applied to a muhūrta doṣa is a fabricated cancellation and a §N.5
   authority inversion. Empty `pariharas_applied` with the gap named is the correct output.

---

*W4 in one line: the diagnosis becomes the product — which link in the chain failed, and which
already-attested rite reaches it; the lattice grows the pāñcāṅgika families that make a declared
sky-pattern searchable exactly rather than approximately; the paddhati profile makes lineage
variation data instead of an argument; and every elected act files one accountable row, so that
election itself finally becomes a thing that can be measured and found wanting.*
