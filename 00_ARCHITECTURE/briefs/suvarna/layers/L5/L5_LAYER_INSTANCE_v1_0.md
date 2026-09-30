---
artifact: SUVARNA_L5_LAYER_INSTANCE
canonical_id: SUVARNA_L5_LAYER_INSTANCE
version: "1.1 (first draft, gate review corrections applied)"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L5i (step 2: layer-instance draft)"
layer: "L5 Mīmāṃsā — 15 registry assets: 14 `mi_*` and `lel_events`"
template: "00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3, SEALED), sections in the template's own order (2.6 and 2.7 precede 2.5, as the template prints them; R08)"
inherits: ["tier 1 MADHAV_PRODUCT_DEFINITION_FINAL", "tier 2 MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL (+ its companion asset register, PROPOSED)"]
census_run:
  path: /Users/Dev/suvarna-evidence/census/census_L5.json   # + census_L5.log, SUMMARY.md beside it
  exit_code: 2            # FAIL rows present = MEASURED (SUMMARY.md, row L5)
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57
  generated: "2026-09-30T20:24:11+05:30"
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
tier_gaps: layers/L5/L5_TIER_GAPS_v1_0.md   # TG-L5-001 .. TG-L5-031
inputs_not_authority: "00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/L5_INSTANCE_SKELETON.md and L5_INVENTIONS.md (2026-09-26). Read; nothing copied. Where a figure differs, Part 6 says so."
changelog:
  - "1.1 (2026-09-30): gate review corrections applied (independent Opus review 2026-09-30): 10 defects. Instance side: cell total 300 -> 284 (the six counts sum to 284; census re-tallied: 284); §5.4 test 4 read as [TRANSFERS]-pending (R71/R094) instead of not applicable; mi_bhara error cause restated (CEN Build.history says only timeout:600s; ka_kshetra comes from Build.dep_liveness, link inferred); TG-L5-007 narrowed and TG-L5-017 restated where used; Null and Narr gate rows cite the new TG-L5-031; gap total 30 -> 31. Tier-gap file corrections are in L5_TIER_GAPS v1.1."
  - "1.0 (2026-09-30): first draft. Filled from tiers 1-4, the tier-2 companion register, the change register, census_L5.json and read-only queries. Every hole in the tiers is marked TIER GAP with its row; no clause was invented to fill one. No certification record is written (§5.3)."
---

# L5 Mīmāṃsā — layer definition, strategy and evaluation (instance, first draft)

**Reading rules.** Every figure carries a source label from Appendix A (CEN census, REG live registry, SEED registry seed,
PIN layer pin, DBQ read-only aggregate query, CODE source at the inspector commit, EGATE, INV, DEC). A figure with no label is
a quotation, and its source is named beside it. "Not measured" states its reason. Where two sources disagree the
disagreement is stated, not settled. Quotations from tiers are verbatim.

**Two words used in one sense throughout** (T3 preface): *qualified* (the method's sources, conventions, prerequisites and
exceptions are on record before it is applied) and *earned* (carried by a detector that could have reported otherwise).

**What this layer is, in three lines.** L5 holds what the plane keeps to answer for itself: admitted observations, the
predictions and claim candidates it emitted, their adjudication against those observations, and the qualified
calibration built from that. Its build is complete as a structure and mostly empty of empirical content by design
(CLAUDE.md §E: "sealed in STRUCTURAL mode — empirical calibration values fill in as prediction→outcome data accrues";
SUVARNA_CAMPAIGN_PLAN_v1_5 §1.5: "empirical calibration (L5 fills by design)" is out of scope for the campaign). How the tiers
express that distinction, and where they stop, is in §3.1 and TG-L5-014.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional. The one measured necessity signal is CEN assets[*].blocking_radius (transitive dependents in the registry)
traces_to:   — (this IS the origin)
```

**TIER GAP: TG-L5-001.** T3 §0.1 asks for the P-needs and V-journeys for which L5 is *necessary*. Tiers 1 and 2 map needs to
data obligations (T2 §2) and layers to proofs and questions (T1 §11, T2 §3.1) but never a layer to a need. The table below
is therefore **not** a necessity list. It records only the tier text that names L5's work, with its location, so the
reader can see what the tiers do say.

| tier text (verbatim or near-verbatim) | location | what it says about L5 |
|---|---|---|
| P12 "Which events fit this interpretation, and which do not?" — "Fit, misfit, non-events and unknowns; hindsight is not prospective success." | T1 §2, line 167 | the need a fit/misfit layer serves; no layer is named |
| "Preserve the forecast actually delivered" and "Evaluate without hindsight" | T1 §7.2-§7.3, lines 379-399 | accountability obligations; L5 named only through §8.1/§11 |
| Experience 7 "A truthful history and forecast review" | T1 §9, lines 451-452 | the surface L5's evidence feeds |
| "You predicted a promotion. It did not happen." | T1 §12.3, lines 552-557 | the acceptance sketch that needs a frozen claim and adjudication |
| V06 "Honest history and forecast review" (P12) and V10 "Continuing and portable understanding" (P12-13, P19) | T2 §2, lines 122, 126 | value journeys whose data obligations L5 assets carry |
| "L5 later evaluates the original claim without feeding outcomes into it" | T2 §12.1, line 582 | the financial story's last step |
| "Historical challenge … Route adjudication separately from provider-facing historical explanation" | T2 §12.1, line 586 | the third proving story |

The only measured signal: L5 assets have no dependents outside L5 in the registry (REG: 0 registry rows in any other layer
list an L5 id in `depends_on`), and inside L5 the transitive dependent counts (CEN `blocking_radius.transitive`) are
`mi_jivanaghatana` 9, `mi_kula` 9, `mi_bhavisya` 8, `mi_pramana` 6, `mi_gunanaka` 3, `mi_adhilepa` 2, `mi_pariksha` 2,
`mi_sambandha` 1, and 0 for `lel_events`, `mi_abhilekha`, `mi_bhara`, `mi_darshana`, `mi_sankalpa`, `mi_seva`, `mi_vistara`.
That is registry `depends_on` only: the real readers of `lel_events` are not in it (§0.3, F-01).

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1 (which is itself a gap; see TG-L5-001)
```

- **Owned question** (T2 §3.1, line 144): "What withstands challenge, observation and independent evaluation?"
- **Contribution handed onward** (T2 §3.1): "Preserved claims/outcomes, fit/misfit, admissible performance evidence, study candidates and separately approved future model artifacts."
- **What it must not claim** (T2 §3.1): "Feedback capture as learning, retrospective fit as prediction, evaluation outcomes as serving context."
- **Product responsibility** (T1 §11, line 505): "Challenge, adjudication, scope of validity and qualified learning." **Proof that matters:** "Predictive performance + Operational honesty (§14): preserved failures, independent evidence, correct denominators, leakage-free evaluation." Scored on these two of the ten obligations (T3 §5.1; T1 §14 rows at lines 594 and 596).
- **Layer-specific contribution and prohibition** (T1 §8.1, line 427): valuable use "Adjudication, misfit analysis and qualified calibration"; what must not happen "Outcome leakage into prospective generation, or unqualified learning promotion."

*The distinctions this layer makes earnable* (T3 §0.2 asks for one paragraph; T2 §6.6 supplies it, and this paragraph
restates only that): learning's output is defined as "a visible change to a claim family's scope, confidence or
availability, with the reason stated" (T1 §7.3; T2 §6.6); a family of interpretations "must be able to lose authority after a
fair evaluation"; "ordinary periods, counterexamples, unmatched activations and failures belong in the evaluation
design"; and "neither satisfaction nor a subjective sense that a reading resonates becomes a prediction weight" (T2 §6.6).
What existing software does not do, in the tiers' words, is compute the estate and its relationships (T1 §1); T2 supplies no
L5-specific sentence for that comparison, and this draft writes none (register R101 records the same for L2).

**Mode.** The layer is sealed in structural mode (above). §3.1 records how the tiers distinguish structural from empirical
content, and that they do not define the terms (TG-L5-014).

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: REG (live asset_registry.depends_on, layer='mimamsa', 15 rows) · SEED (registry seed, 15 entries) · PIN (layer pin, membership only) · CODE (FROM/JOIN scan) · EGATE
traces_to:   0.2
```

**Three sources, stated separately (T3 §0.3).**

| source | what was read | result for L5 |
|---|---|---|
| live registry (REG) | `depends_on` of the 15 `layer = 'mimamsa'` rows | 39 edges: 21 within L5, 18 from L5 to other layers (table below) |
| registry seed (SEED) | `platform/scripts/seed/asset_registry_seed.ts`, block-scoped parse of the 15 L5 entries; path taken from the L0 draft v3.0, line 98, not from a tier | `depends_on` agrees with REG for 15/15. Other fields differ for four assets: `mi_jivanaghatana.scope` (seed `global`, live `per_chart`), `mi_adhilepa.target_table` (seed `mimamsa_signal_adjustment`, live `mimamsa_load_bearing`), `mi_bhara.target_table` (seed `kala_field_weight_versions`, live `kala_field_skill`), `lel_events.catalog_status` (seed `DRAFT`, live `CURRENT`) |
| migration-governed pin (PIN) | `platform/src/generated/nirmana-analysis-layer-pins.json` `layers.L5` and `nirmana-writer-digests.json` | pins **membership**: `asset_prefix mi_`, `receipt_count 15`, `non_writer_assets ["lel_events"]`, 14 writer digests. It carries no `depends_on`. The frozen-manifest `depends_on` that the dispatcher compares (migration 690, lines 9-13) was not located. **TIER GAP: TG-L5-002.** |

**Receives from** (REG edges; the type of each edge is **TIER GAP: TG-L5-005** — the registry has no edge-type column and
no tier says how to type an edge, so none is typed here):

| upstream asset (layer) | consumed by |
|---|---|
| `bg_ghatana` (L0) | `mi_jivanaghatana`, `mi_pramana` |
| `bg_rules`, `bg_class_priors` (L0) | `mi_kula` |
| `bg_formula_constants` (L0) | `mi_pramana`, `mi_gunanaka`, `mi_pariksha` |
| `ga_positions` (L1) | `mi_adhilepa` |
| `bo_laksana` (L2) | `mi_bhavisya`, `mi_adhilepa` |
| `bo_pratijna` (L2) | `mi_darshana` |
| `ka_sangam` (L3, family asset) | `mi_adhilepa` |
| `ka_kshetra` (L3, family asset) | `mi_bhara`, `mi_sankalpa` |
| `ph_pramana`, `ph_nimitta`, `ph_phaladesa` (L4) | `mi_bhavisya` (all three); `ph_nimitta` also `mi_adhilepa` |

`ka_sangam` and `ka_kshetra` are in the L3 family set (TRACK_A_BRIEF §6); their L5 readers are `mi_adhilepa`, `mi_bhara`
and `mi_sankalpa`. Nothing about them is touched here.

**Within L5** (REG, 21 edges): `mi_bhavisya` ← `mi_kula`, `mi_jivanaghatana`; `mi_pramana` ← `mi_bhavisya`,
`mi_jivanaghatana`; `mi_gunanaka` ← `mi_pramana`, `mi_kula`; `mi_pariksha` ← `mi_pramana`, `mi_kula`; `mi_adhilepa` ←
`mi_gunanaka`; `mi_sambandha` ← `mi_pramana`, `mi_pariksha`, `mi_bhavisya`; `mi_darshana` ← `mi_pramana`, `mi_adhilepa`,
`mi_sambandha`, `mi_pariksha`, `mi_gunanaka`, `mi_kula`, `mi_jivanaghatana`; `mi_seva` ← `mi_adhilepa`; `mi_abhilekha` ←
`mi_bhavisya`. `lel_events`, `mi_vistara` declare none.

**Hands onward to.** The registry lists no dependent outside L5 (REG query, 0 rows). The onward consumers are the
retrieval plane's capability modules, which the registry does not model. CEN `Dens.served` and `reach` name them per asset
(§1.4). The `[TRANSFERS]` obligations of T2 §8 (discovery, hydration, delivery) are not L5's to build (T2 §1, lines 83-85).

**What the join needs from it** (T3 §0.3): the fields the reasoning layer reads across. CEN `reach` reports, per asset table,
which columns a capability module selects and which are dark; that is the only measured answer and is in §1.4. Which fields
the acharya rendering needs from L5 is unassigned (TG-L5-009).

**Undeclared reads (a fourth reading, from CODE).** The registry understates what L5 reads. `life_events` is read by
`mi_jivanaghatana.py:215`, `services/mi_bhara/db.py:143`, `services/mi_sankalpa/db.py:64` and L4's `ph_rectification`
(`__init__.py:146`) while `lel_events` has no registry dependents; `brahma_prospective_ledger` is read by
`services/mi_bhara/db.py:177` and referenced by `mi_sankalpa` with no edge. Migration 691 (lines 1447-1451) records
Nirmāṇa's own L5 W1 finding: "32 DAG corrections — 19 undeclared-but-read and 13 declared-but-unread — and NONE is
applied". That figure is quoted, not re-measured here. See F-01.

**Cross-layer gate state (EGATE).** `egate.sql -v layer=L5`, read-only, against the frozen definition revision
`t3-2026-09-11-8b884eac`: all 15 L5 assets read BLOCKED — 13 `BLOCKED-ANCESTORS` (unfrozen ancestors: `mi_jivanaghatana` 1,
`mi_kula` 6, `mi_bhara` 35, `mi_sankalpa` 35, `mi_bhavisya` 57, `mi_abhilekha` 58, `mi_pramana` 59, `mi_gunanaka` 60,
`mi_pariksha` 60, `mi_adhilepa` 61, `mi_sambandha` 61, `mi_seva` 62, `mi_darshana` 64) and 2 `BLOCKED-NO-ROUTE` (`lel_events`,
`mi_vistara`, each with 0 unfrozen ancestors and no W2 analysis/verdict). This is the Nirmāṇa campaign's gate, not
Suvarṇa's; it is recorded because T3 §2.5 names it (TG-L5-029).

### 0.4 · The alignment test

```
inherits:    T3 §0.4
measured_by: author's own pass over this draft
traces_to:   0.1-0.3
```

Every section from Part 1 carries a `traces_to`. Sections that trace to 0.1 inherit that section's gap (TG-L5-001); they
are kept, not struck, because the sealed template requires them and the gap is a tier gap, not an extraneous section. No
section, contract, asset or packet in this draft was added that cannot name what it serves.

---

## Part 1 · VALUE DECOMPOSITION — the layer is the sum of its assets and services

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: REG (asset_registry, layer='mimamsa') · CEN (census_L5.json) · SEED · PIN · DBQ (chart 482012f1) · CODE (writers at 2a78ec64d)
traces_to:   0.3
```

**Population.** REG: 15 rows with `layer = 'mimamsa'`, all `is_active` and not `dead_flag` (the registry holds 129 rows, 127
active). CEN: `population_active 15`, `population_registry_total 15`, `population_excluded_inactive []`, `phantom_registered []`,
`never_exercised_with_writer []`.

**The registered-id anomaly, resolved.** The inspector printed "14 registered ids vs 15 assets" and did not say which asset
lacks one (SUMMARY.md). It is `lel_events`. Four independent readings agree: (a) REG `lel_events.has_writer = f`, all other 14
rows `t`; (b) CODE — 14 files `pipeline/orchestrator/writers/mi_*.py` each carry exactly one `@register(...)` and no
`@register('lel_events')` exists in `platform/python-sidecar`; (c) CEN `registered_ids 14`, `registry_has_writer 14`; (d) PIN
`non_writer_assets ["lel_events"]` and `nirmana-writer-digests.json` lists 14 `mi_*` writers and no `lel_events`.
So 14 registered ids against 15 assets is consistent, not a defect: 14 writer-backed assets plus one declared no-writer
asset (N-14.R236, §1.1.a). Two ids (`mi_bhara`, `mi_sankalpa`) register through a constant, `@register(ASSET_ID)`; the
predecessor skeleton counted 12 for that reason (R43, CLOSED, 12 to 14).

**Table 1 — the 15 assets.** Rows are chart-scoped totals over the asset's registry `count_sql` for chart 482012f1 unless the
basis column says otherwise (CEN `live_rows`, `live_rows_basis`). "Latest run" is CEN `Build.history` / `Build.completion`.

| asset | kind / storage / scope (REG) | catalog | target table (REG) and `count_sql` tables | rows (basis) | cols (target) | latest build record (CEN) |
|---|---|---|---|---|---|---|
| `lel_events` | data / postgres_table / per_chart | CURRENT | none declared; `life_events` | 63 (chart) | — | none: "live=63 and no build record at all" |
| `mi_jivanaghatana` | data / postgres_table / per_chart | CURRENT | `mimamsa_event_provenance` | 63 (chart) | 20 | complete; 2 errors, 4 aborts on record; last run 2026-09-06 |
| `mi_kula` | data / postgres_table / **global** | CURRENT | `mimamsa_signal_families` + `mimamsa_negative_controls` | 15 (11 + 4, whole tables) | 20 | complete; 0 errors, 1 abort; last run 2026-09-06 |
| `mi_bhavisya` | data / postgres_table / per_chart | CURRENT | `mimamsa_predictions` + `mimamsa_manifestation_sets` | 278 (139 + 139) | 21 | error (2026-08-21): blocked on `ph_phaladesa`, `ph_pramana` |
| `mi_pramana` | data / postgres_table / per_chart, has_substeps | CURRENT | `mimamsa_calibration` + `mimamsa_reliability` | 63 (57 + 6) | 20 | error (2026-08-21): blocked on `mi_bhavisya` |
| `mi_gunanaka` | data / postgres_table / per_chart | CURRENT | `mimamsa_multipliers` + `mimamsa_calibration_snapshot` | 13 (9 + 4) | 20 | error (2026-08-21): blocked on `mi_pramana`; rows_written 9 vs live 13 |
| `mi_adhilepa` | data / postgres_table / per_chart | CURRENT | `mimamsa_load_bearing` + `mimamsa_convergence_adjustment` + `mimamsa_anchor_adjustment` + `mimamsa_signal_adjustment` + `mimamsa_fact_adjustment` | 112,270 (4 + 500 + 139 + 50,104 + 61,523) | 6 | error (2026-08-21): blocked on `mi_gunanaka` |
| `mi_pariksha` | data / postgres_table / per_chart, has_substeps | CURRENT | `mimamsa_qa_eval` + `mimamsa_attribution` + `mimamsa_discoveries` | 1,664 (168 + 1,425 + 71) | 8 | error (2026-08-21): blocked on `mi_pramana` |
| `mi_sambandha` | data / postgres_table / per_chart | CURRENT | `mimamsa_manifestation_grammar` | 24 (chart) | 17 | error (2026-08-21): blocked on `mi_bhavisya`, `mi_pariksha`, `mi_pramana` |
| `mi_darshana` | data / **pgvector** / per_chart, has_substeps | CURRENT | `mimamsa_insight_units` + `mimamsa_insight_embeddings` | 115 (115 + 0) | 18 | error (2026-08-21): blocked on five `mi_*` upstreams |
| `mi_vistara` | data / postgres_table / **global** | CURRENT | `mimamsa_export_log` | 0 (whole table) | 12 | complete; 39 complete runs, no error; last run 2026-09-06 |
| `mi_seva` | **service** / service / per_chart | **DRAFT** | `mimamsa_preferences` | 0 (whole table) | 4 | complete; 28 errors, 10 aborts on record |
| `mi_abhilekha` | **service** / service / per_chart | **DRAFT** | `mimamsa_journal` | 0 (chart) | 9 | complete; 26 errors, 9 aborts on record |
| `mi_bhara` | data / postgres_table / per_chart | CURRENT | `kala_field_skill` (a `ka_`-prefixed table) | 7 (chart) | 17 | error (2026-08-21): blocked on an upstream dependency that did not complete within `timeout:600s` (CEN `Build.history`, which does not name the asset); `ka_kshetra` is the one declared dependency not lit, from CEN `Build.dep_liveness` ("0/1 … `ka_kshetra` (error)") — the link between the two readings is inferred |
| `mi_sankalpa` | data / postgres_table / per_chart | CURRENT | `mimamsa_intervention_ledger` | 0 (chart) | 28 | `dormant`; 0 errors, 3 aborts |

Row counts were reproduced by DBQ (`count(*) … WHERE chart_id = 482012f1-…` per table, whole-table for the four tables with no
`chart_id` or `scope = global`); the sums match CEN `live_rows` for all 15 assets. Sources of the remaining columns: catalog and
kind, REG; latest record, CEN; column counts, CEN `Complete.depth` / `reach.columns_built`.

Other measured facts per asset (CEN unless labelled): every one of the 14 writers has been executed by the orchestrator at
least once (`Build.exercised` PASS 14, N/A 1); the most recent run is an error for the eight assets in the table above;
`target_floor = 0` for all 15, so `Count.floor` is N/A 15/15 ("the registry declares zero rows complete — there is no
floor to breach"). The inspector's `global_runs` is 61 and it printed `global_runs_touching_layer 422`; the meaning of the
second figure against the first is not established here.

#### 1.1.a · `lel_events` — a declared no-writer asset

Decision **N-14.R236** (DEC, 2026-09-29, Strategic Suvarṇa under N-28): "lel_events is classified a no-writer asset with
Build/Idem N/A by registry rule, with the justification recorded in its asset brief from its intended source and consumer
contract; not generalized to other assets." This draft records the classification and **does not extend it**: no other asset
in this instance is treated as no-writer, and no N/A is typed for any other asset.

What was measured. REG: `has_writer = f`, `asset_kind = data`, `target_table` empty, `count_sql = SELECT count(*) FROM
life_events WHERE chart_id = $1`, `integrity_check_sql` present, `expected_volume_formula = EXOGENOUS(native-authored
source corpus, floor 0)`. CEN: Build.registered, Build.contract, Idem.pattern, Build.target, Build.exercised are N/A ("no
writer, and the registry agrees"); Build.dag and Build.count_integrity are PASS; **Build.completion is FAIL** ("live=63 and no
build record at all"). The decision says Build is N/A by registry rule; the inspector at `2a78ec64d` reads one Build check as
FAIL. Reported, not resolved (F-02; TG-L5-016). Register row R236 still reads OPEN in v2.8; DEC shows the decision.

Rows: 63 events for chart 482012f1 (DBQ): 56 `point`/`exact`, 1 `point`/`month_known`, 1 `interval`/`exact`, 2
`interval`/`month_known`, 3 `interval`/`year_only`; `outcome_observed` true on 62; `pool_consent` true on 0; `recorded_at`
ranges 2000-01-01 to 2026-08-08. INV says "57 seed events recoverable from `LEL_CORPUS` / `LIFE_EVENT_LOG_v1_2.md`; MCP-added
events and original `recorded_at` stamps are not"; 63 measured versus 57 in INV is not reconciled here.

Readers found by CODE: `mi_jivanaghatana` (its bridge to `mimamsa_event_provenance`), `mi_bhara` (`services/mi_bhara/db.py`),
`mi_sankalpa` (also an FK `REFERENCES life_events(id)`), and L4 `ph_rectification`. Intended source and consumer contract, as
T3-derived text for the asset brief: the source is "native-authored" (REG `expected_volume_formula`) and intake goes "via
the LEL save API" (SEED description); the tiers state the observation-testimony role at T2 §9.1 (line 491): "`life_events`/
registered `lel_events` hold observation testimony with channel adapters; `mi_jivanaghatana` is its qualified evidence
projection." No tier defines the no-writer kind (TG-L5-016).

#### 1.1.b · Tables that hold people-entered data (N-46) — which of L5's tables are in the non-regenerable inventory

Rule **N-46** (DEC, 2026-09-30): "agents never change or delete information people typed in … Computed data may be rebuilt
freely." **This campaign changes none of the tables below.** Source: INV (`SUVARNA_NON_REGENERABLE_INVENTORY_v1_0.md`, a static
inventory of `origin/main @ 56dba8ac5`; "production presence to be confirmed by a live catalog read"). The rows are chart
482012f1 counts (DBQ) unless marked.

| table | L5 asset (REG) | class in INV | rows | what the L5 writer does to it (CODE) |
|---|---|---|---|---|
| `life_events` | `lel_events` | non-regenerable ("user input, partly from git"; not on the backup list) | 63 | no writer; `mi_jivanaghatana` reads it |
| `mimamsa_intervention_ledger` | `mi_sankalpa` | non-regenerable ("user input, then updated by L5") | 0 | deletes only `study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL`, re-inserting each verbatim; never touches `performed` |
| `mimamsa_predictions` | `mi_bhavisya` | **mixed** ("confirmed/denied/partial outcomes and freeze times are not regenerable") | 139, all `pending` | `mi_bhavisya.py:230` deletes `lifecycle_status IN ('pending','due')` then inserts; `mi_abhilekha.py:70` UPDATEs `lifecycle_status` for `pending` rows from journal answers |
| `mimamsa_calibration_snapshot` | `mi_gunanaka` | **mixed** ("human cosign state") | 4, all `proposed`, `two_key_complete` false | insert only, time-based `snapshot_id` (ratified accretion, F188); never deleted by the writer |
| `mimamsa_snapshot_cosign` | none | non-regenerable (not on backup list) | 0 | no L5 asset owns it (TG-L5-020) |
| `mimamsa_adjudication_log` | none | non-regenerable | 0 | no asset owns it |
| `mimamsa_resonance_feedback` | none | non-regenerable (not on backup list) | 0 | no asset owns it |
| `kala_field_weight_versions` | `mi_bhara` per INV; the registry declares `kala_field_skill` (SEED lists this table as target) | non-regenerable ("append-only version history") | 1 (whole table, `active`) | `services/mi_bhara/db.py:234` INSERT; `:281` UPDATE `status = 'superseded'` |
| `mimamsa_journal` | `mi_abhilekha` | **unclassified; protected by default** ("an L5 input") | 0 | `mi_abhilekha.py` reads it; writes `mimamsa_predictions` |
| `mimamsa_preferences` | `mi_seva` | **unclassified; protected by default** | 0 (whole table) | `mi_seva.py`: no write |

Also named by INV and read (not written) by L5 code: `brahma_prospective_ledger` (18 rows, all `open`) and
`brahma_mimamsa_prediction_ledger` (5 rows: 1 `unverifiable`, 4 `dismissed`) — registry-unowned (TG-L5-006).

Derived L5 outputs that INV lists as regenerable, chart-scoped, rebuilt by the orchestrator: `mimamsa_calibration`,
`_multipliers`, `_reliability`, `_event_provenance`, `*_adjustment`, `_discoveries`, `_qa_eval`, `_signal_families`,
`_negative_controls`, `_manifestation_*`, `_insight_*`, `_load_bearing`. **Tables in L5's namespace that INV names in neither
list:** `mimamsa_export_log` (`mi_vistara`, 0 rows), `mimamsa_attribution` (`mi_pariksha`), `mimamsa_pool_contributions` (no
asset), and the `mi_bhara` writes `kala_field_gof`, `kala_field_weights`, `kala_insights` (covered only by the general
`kala_*` line). These are reported to the coordinator, not classified here. INV also notes, and this pass repeats without
acting: "`mimamsa_calibration` is on the backup list but is fully rebuilt by `mi_pramana`."

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: none — no ablation harness exists (CEN has no ablation criterion)
traces_to:   0.1 (unmeasurable; TG-L5-021)
```

L5 is a chart-product layer (CEN `scoring: contribution`), so the reference-layer fidelity carve-out (T3 §1.2) does not apply.
**Absent instrument** — recorded as such, not as zero. T3 §1.2 says "where no served path exists, state 'unmeasurable — not
reached'". Served paths exist for nine assets (CEN `Dens.served` PASS: `mi_abhilekha`, `mi_adhilepa`, `mi_bhavisya`,
`mi_darshana`, `mi_gunanaka`, `mi_kula`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`); no path exists for `lel_events`,
`mi_bhara`, `mi_jivanaghatana`, `mi_sankalpa`, `mi_seva`, `mi_vistara` (Dens.served N/A, 0 modules). An asset that cannot be
ablated because nothing reads it "has already answered the question" (T1 §14.1), but registry-level absence of readers is not
the same as no reader: `lel_events` and `mi_jivanaghatana`'s table are read by code that CEN's served-module count does not see
(§0.3). No individual term is recorded for any asset.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4, §7, §3.5
measured_by: none — no harness
traces_to:   0.2 (unmeasurable; TG-L5-021)
```

Absent instrument (T3 §1.5 line 249: record a fraction "only where an ablation harness exists"). No fraction is written.
Seam-by-seam observations from CEN and DBQ, recorded as observations and not as the term: the intra-layer DAG has depth 5
(§4.1) and `mi_darshana` reads seven `mi_*` assets; `mi_sambandha.citation_ref` is populated on 47/47 rows (CEN
`Ldgr.source_presence`, the only Ldgr reading at L5); all eight upstream-blocked assets errored on their most recent run
because an upstream did not complete (CEN `Build.history` text), which is a measured coupling but not a value measurement.

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7
measured_by: CEN (reach, Dens.served); verification at the consumer was not run
traces_to:   0.3 (hands onward); TG-L5-022
```

The six states are source-present, qualified, consumed, traceably transformed, served, value evaluated (T2 §11). What CEN
can show is the middle: which capability modules read each asset's tables. It counts modules; it does not verify that a
consumer reads correctly. **No asset has a verified position on the ladder.**

| asset | modules that read the target table (CEN `reach`) | modules declaring a `density_contract` over the asset's tables (CEN `Dens.served`) |
|---|---|---|
| `mi_abhilekha` | `L5_mimamsa/query_journal.ts` | 1 (`query_journal.ts`) |
| `mi_adhilepa` | `L5_mimamsa/query_load_bearing.ts` | 1 |
| `mi_bhara` | `platform-mcp/src/lib/kala_envelope.ts` | 0 (differs from `reach`; reported) |
| `mi_bhavisya` | `prediction_lifecycle_sweep.ts`, `query_predictions.ts` | 4 (adds `query_calibration.ts`, `query_manifestation_sets.ts`) |
| `mi_darshana` | `query_insight_embeddings.ts`, `query_insights.ts` | 2 |
| `mi_gunanaka` | `query_calibration.ts` | 1 |
| `mi_jivanaghatana` | none | 0 |
| `mi_kula` | `query_signal_families.ts` | 1 |
| `mi_pariksha` | `query_calibration.ts` | 3 (adds `query_attribution.ts`, `query_mimamsa_discoveries.ts`) |
| `mi_pramana` | `query_calibration.ts`, `query_insights.ts` | 2 |
| `mi_sambandha` | `query_manifestation_grammar.ts` | 2 (adds `query_manifestation_sets.ts`) |
| `mi_sankalpa`, `mi_seva`, `mi_vistara` | none | 0 |
| `lel_events` | no target table declared (`reach` NOT_GENERIC) | 0 |

Column width (CEN `reach.width`, reported and not graded): highest `mi_darshana` 0.9412, `mi_abhilekha` 0.8889, `mi_sambandha`
0.8824, `mi_kula` 0.875, `mi_adhilepa` 0.8333, `mi_bhavisya` 0.8125, `mi_pariksha` 0.75; lowest `mi_gunanaka` 0.5789,
`mi_pramana` 0.2778, `mi_bhara` 0.125, and 0.0 for `mi_jivanaghatana`, `mi_sankalpa`, `mi_seva`, `mi_vistara`. The table columns
`mi_pramana` leaves dark include `score_falsifier`, `score_manifestation`, `evidence_admissibility`, `leakage_status`,
`base_rate`, `brier_vs_null` (CEN `reach.dark`); `mi_gunanaka` leaves dark `held_out_validity`, `confidence_high`,
`neg_control_clear`, `audit_trail`.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

**layer value = Σ individual + Σ synergistic + Σ cross-layer handoff.** The accounting cannot be closed: 1.2 and 1.3 are
absent instruments and 1.4 has no consumer-verified position, so the shortfall against 0.2 is **not computed**. No fraction is
recorded. The only layer-level facts the tiers allow this draft to state as the elevation delta's shape are structural and
come from the census, not from value: 10 of 15 assets read FAIL on `Build.completion`, 10 on `Build.dep_liveness`, 8 on
`Build.history` (Part 3). Candidates for disposition R or H (T3 §1.5) cannot be nominated: no asset can be shown to be zero on
all three terms with these instruments; T3 §1.5's warning applies ("lack of a caller in a bounded search is not redundancy").

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (L5 row), §13; Data plane §9.2
measured_by: none — no detector exists in CEN for any rule below; code-side checks named by filename only
traces_to:   0.2 — the value is real only if these hold
```

The rules, verbatim from their tiers:

1. T1 §8.1 (line 427): L5 "must not" allow "Outcome leakage into prospective generation, or unqualified learning promotion."
2. T1 §13 (lines 566-572): "No invented computation, source, detector, confidence, empirical score, or claim of exhaustive
   coverage. Every number traces to a real calculation and every status to a detector that could have reported otherwise."
   "No outcome laundering into prospective generation — a result known after the fact must not re-enter as though it were
   foreseen."
3. T1 §7.3 (lines 390-393): "A rebuild must not reset chronology: re-stamping emission time turns a frozen claim into a
   hindsight leak. An observation reported after the person has seen the forecast is not automatically independent."
4. T2 §6.6 (line 406): L5 "must not feed the observed outcome, a derived personal multiplier, rectification selection or
   cached retrospective narrative back into the prospective generation being evaluated."
5. T4 §"Adapting per layer", L5 row (line 509): "the firewall — admitted outcomes never enter provider synthesis; a rebuild never
   re-stamps emission time".
6. T2 §9.2 (lines 514-517), surviving any switch state: "biography must never alter a chart fact; a biography-dependent support
   must never be presented as event-free chart structure."

**Detectors: NO DETECTOR for every rule in the census.** CEN's criteria are Build.*, Idem.pattern, Earn.build_record,
Cost.baseline, Count.floor, Dens.served, Complete.*, Carr.detector, Reach.fields, Vocab.identity and Ldgr.source_presence; none
measures leakage, chronology or the firewall (TG-L5-008). Code-side checks found by filename, **not** registered as detectors and
**not** run here: `pipeline/orchestrator/writers/tests/test_mi_adhilepa_leakage.py`,
`platform/src/lib/pariprashna/no_leakage/calibration_leak_guard.ts`, `platform/src/lib/pipeline/no_leakage_filter.ts`. A rule
with no detector is a wish (T3 §2.1); the instance says so.

**The life-event switch (T2 §9.2; T3 §2.1).** T2 states the plane's two states and "no third". **TIER GAP: TG-L5-007** (narrowed) —
T2 §9.2 line 500 names L5's ON role ("L5 adjudication of frozen claims against admitted observations") and line 501 ("Nothing derived from life events, anywhere") binds L5 when OFF; what no tier states is which L5 tables are event-conditioned overlays and which are event-free, i.e. the per-table storage separation that makes OFF a selection (T2 lines 510-512 give the principle and name no L5 table). What was measured:
no life-event switch identifier exists in the searched code (every `switch_state` hit is `kill_switch_state`, a claim-family
kill switch); the three prediction tables (`mimamsa_predictions`, `brahma_prospective_ledger`,
`brahma_mimamsa_prediction_ledger`) have no column named for switch state or information cutoff, although T1 §7.2 (line 382)
requires the emission record to carry "information cutoff, **life-event switch state (§8)**"; a jsonb column may carry them and
was not searched; a differently named mechanism (`lel_capable`, `types.ts:180`) was not assessed. Recorded as F-07 (layer
finding), not as a tier gap.

**Storage separation (T2 §9.2).** Whether event-conditioned overlays are stored apart from event-free products, so that OFF is
a selection and not a rebuild, was not measured for L5.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4
measured_by: none — the presentation-parity test is [TRANSFERS] (T2 §12.2)
traces_to:   0.1
```

**TIER GAP: TG-L5-009.** T2 §3.4 maps every acharya-rendering row to DP01-DP09; none maps to L5, and T3 §2.2 requires this
section to name "which §3.4 fields this layer must retain and hand onward". No rows are assigned here. The parity test (T3 §5.4
test 4) is marked [TRANSFERS] by T2 §12.2 (line 614), which T3 does not reconcile (R094). What the census does show is a
material fact for any later assignment: `mi_pramana` leaves dark 13 of its 18 built columns to capability modules (§1.4), among
them the falsifier and manifestation scores and the leakage and admissibility labels.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1
measured_by: T2c (companion register, PROPOSED) for the DP ids; REG for edges; the fields and grain at both ends were not verified
traces_to:   0.3
```

**Produced.** T2 §7.1 names L5 only in DP15b ("Already-protected claim + eligible observation revision → protected L5") and
separately defines DP13 (observation intake), DP14 (historical comparison), DP15a (claim issuance protection, "Required before
a forecast is exposed as a completed issued claim") and DP16 (version/correction) without naming a layer for them. The per-layer index is
**TIER GAP: TG-L5-003**. T2c §7 assigns receiving contracts per asset; the ids are shown below as the companion's, marked
provisional, with its two defects (TG-L5-004): it cites DP18, which T2 FINAL eliminated, in 10 of 15 rows, and it cites an
unsplit DP15 where T2 FINAL has DP15a and DP15b.

| asset | T2c receiving contracts (as printed) | note |
|---|---|---|
| `lel_events` | DP13/16 | |
| `mi_jivanaghatana` | DP13/14/15 | |
| `mi_bhavisya` | DP09/15/16 | T2 §9.1: "rebuildable candidates, not protected issuance history" |
| `mi_abhilekha` | DP15 | |
| `mi_pramana` | DP15/18 | DP18 not in T2 FINAL |
| `mi_kula` | DP01/15/18 | DP18 not in T2 FINAL |
| `mi_gunanaka` | DP18 | DP18 not in T2 FINAL |
| `mi_adhilepa` | DP16/18 | DP18 not in T2 FINAL |
| `mi_pariksha` | DP14/17/18 | DP18 not in T2 FINAL |
| `mi_sambandha` | DP09/15/18 | DP18 not in T2 FINAL |
| `mi_darshana` | DP10/14/18 | DP18 not in T2 FINAL |
| `mi_seva` | DP10/18 | DP18 not in T2 FINAL |
| `mi_vistara` | DP12/16 | |
| `mi_bhara` | DP15/18 | DP18 not in T2 FINAL |
| `mi_sankalpa` | DP13/15/18 | DP18 not in T2 FINAL |

Field, grain, identity and generation per produced contract: **not supplied** (TG-L5-003). The T2 §7.1 common envelope (line
414) is the checklist a brief must fill; this draft fills none of it.

**Consumed.** The 39 registry edges of §0.3 are the consumed set. **TIER GAP: TG-L5-010** — "Every consumed input declares its
use — calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation, evaluation. A
citation with no declared use is not a contract." No source in the tiers, the registry or the census records a declared use, so
none is declared here and none of the 39 edges is a contract by T3's own definition until it is.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: none; CEN Complete.width is NOT_GENERIC 15/15 ("no declared universe for this asset")
traces_to:   0.1
```

**TIER GAP: TG-L5-011.** T3 §2.4 asks which coverage obligations L5 owns, each ending in one of five states (applied /
inapplicable with reason / unavailable / unqualified / unresolved). T2 §5's table assigns halves to L3 and L4 in one row
(line 335) and names no L5 obligation. No obligation is claimed for L5 here, and none is given a state; "unresolved" is not
used as a filler because that state is itself a coverage claim.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (six rules with detectors)
measured_by: CEN local_map_candidates (-1, not measured); CEN Vocab.identity; DBQ for the labels below
traces_to:   0.2
```

**Not measured:** the independent-map census per class (`local_map_candidates = -1`) and the interface-parameter census.
**TIER GAP: TG-L5-012** — T3 §2.6 counts sixteen entity classes; L5's own vocabularies are not among them. What L5 emits,
found by column and value, with the class question left open:

| vocabulary | where | values found (DBQ, chart 482012f1 unless whole table) |
|---|---|---|
| domain | `mimamsa_predictions.domain`, `mimamsa_manifestation_sets.domain`, `mimamsa_event_provenance.domain_primary`, `life_events.domain` | a listed §4.1 class ("domains") |
| event class | `mimamsa_intervention_ledger.event_class`, `kala_field_skill.event_class`, `mimamsa_event_provenance.event_class_id` | governed by §4.1 line 247 yet not among the sixteen; `event_class_id` is never populated (CEN `Complete.depth`, `mi_jivanaghatana`) |
| prediction lifecycle | `mimamsa_predictions.lifecycle_status` | `pending` 139 |
| adjudication verdict | `mimamsa_calibration.composite_verdict` | CONFIRMED 2, PARTIAL 23, REFUTED 7, UNRESOLVED 25 |
| evidence grade | `mimamsa_reliability.evidence_grade`; `mimamsa_insight_units.evidence_grade` | reliability {empirical 4, prior_only 2}; insight units {empirical 31, prior_only 53, structural 31}, not one shared set |
| study arm | `mimamsa_intervention_ledger.study_arm` | 0 rows |

Identity keys declared (CEN `Vocab.identity`, 0 duplicates each where measurable): `(chart_id, event_id)` [`mi_jivanaghatana`],
`(family_id)` [`mi_kula`], `(chart_id, prediction_id)` [`mi_bhavisya`], `(chart_id, match_id)` [`mi_pramana`],
`(chart_id, weight_id)` [`mi_gunanaka`], `(chart_id, conclusion_id, signal_id)` [`mi_adhilepa`], `(chart_id, check_id)`
[`mi_pariksha`], `(chart_id, origin_kind, origin_ref, channel_id)` [`mi_sambandha`], `(chart_id, insight_id)`
[`mi_darshana`], `(id)` [`mi_bhara`]; vacuous on empty tables for `mi_abhilekha`, `mi_sankalpa`, `mi_seva`, `mi_vistara`
(NO_DETECTOR). Vocab.identity: PASS 10, NO_DETECTOR 4; not run for `lel_events`.

### 2.7 · Source carriage and reproduction — did we transmit it faithfully?

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: CEN Carr.detector, Ldgr.source_presence; the applicability conditions of T3 §5.2's carriage menu applied to measured columns
traces_to:   0.1
```

**Layer result: `Carr.detector` = NO_DETECTOR for 15 of 15 assets** ("no D1/D2/D3 detector exists for this asset; which check
applies is per-asset semantics"). **TIER GAP: TG-L5-013** — the per-asset assignment (a source correspondence, b witness
carriage, c independent re-derivation) is not supplied. This section states only which menu condition is met by a measured
fact, as **candidates, not assignments**:

- D1 (source correspondence, "the asset restates a cited classical source"): `mi_kula` — `mimamsa_signal_families` carries
  `citation_refs` and `soundness_basis`, and 7 of 11 families are `evidence_tier = CLASSICAL_CITED` (DBQ, whole table); the other
  four are 2 `MARSYS_DERIVED_CITED` and 2 `NEGATIVE_CONTROL`. `mi_sambandha` — `citation_ref` populated on 47/47 rows is
  source **presence** (Ldgr), not correspondence.
- D3 (independent re-derivation, "the value is computable a second way"): the reliability bins of `mi_pramana` are recomputable
  from `mimamsa_calibration` (the writer's own comment records a bin-boundary defect found by exactly that recomputation,
  `mi_pramana.py:503-518`); not run here.

`Ldgr` is measured for one asset only (`mi_sambandha` PASS, 47/47); T4's gate table reads `Ldgr` "always", so 14 assets have no
reading (an inspector gap, not a tier gap; E6).

The domain verdict is out of scope: T1 §14 discharges it above the plane; no L5 asset is scored on it.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of REG depends_on (this pass); cycle check; EGATE (§0.3)
traces_to:   0.3
```

**Cycle check:** none among the 39 edges. **Topological order within L5** (level = 1 + the highest in-layer dependency):

| level | assets |
|---|---|
| 0 | `lel_events`, `mi_bhara`, `mi_jivanaghatana`, `mi_kula`, `mi_sankalpa`, `mi_vistara` |
| 1 | `mi_bhavisya` |
| 2 | `mi_abhilekha`, `mi_pramana` |
| 3 | `mi_gunanaka`, `mi_pariksha` |
| 4 | `mi_adhilepa`, `mi_sambandha` |
| 5 | `mi_darshana`, `mi_seva` |

Edge types: not typed (TG-L5-005). Cross-layer gates: EGATE, all 15 blocked, against `t3-2026-09-11-8b884eac` (§0.3).
CEN `Build.dep_liveness` reads whether declared dependencies are lit at chart 482012f1: FAIL 10 (`mi_abhilekha`, `mi_adhilepa`,
`mi_bhara`, `mi_darshana`, `mi_gunanaka`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`, `mi_sankalpa`, `mi_seva`), PARTIAL 1
(`mi_bhavisya`, three L4 upstreams stale), PASS 2 (`mi_jivanaghatana`, `mi_kula`), N/A 2 (`lel_events`, `mi_vistara`). Not-live or stale
declared dependencies per asset (CEN `Build.dep_liveness` text): `mi_abhilekha` — `mi_bhavisya` (error); `mi_adhilepa` —
`mi_gunanaka` (error), stale `ka_sangam` and `ph_nimitta`; `mi_bhara` — `ka_kshetra` (error); `mi_bhavisya` — stale `ph_pramana`,
`ph_nimitta`, `ph_phaladesa`; `mi_darshana` — `mi_pramana`, `mi_adhilepa`, `mi_sambandha`, `mi_pariksha`, `mi_gunanaka` (all
error), stale `bo_pratijna`; `mi_gunanaka` — `mi_pramana` (error); `mi_pariksha` — `mi_pramana` (error); `mi_pramana` —
`mi_bhavisya` (error); `mi_sambandha` — `mi_pramana`, `mi_pariksha`, `mi_bhavisya` (all error); `mi_sankalpa` — `ka_kshetra`
(error); `mi_seva` — `mi_adhilepa` (error). Root causes upstream of L5 are not read here.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised — which cannot be computed (§1.5); the itemisation below is census-derived
traces_to:   0.2
```

### 3.1 · Per obligation

L5 is scored on two obligations (T1 §11; T3 §5.1). "Ten, not eleven, and deliberately" (T3 §3.1): domain correctness is not
scored here. For each, where the layer stands, measured, and what T1 §14 requires.

**Predictive performance.** T1 §14 (line 594): "Frozen claims, valid baselines, observation coverage, discrimination and
calibration without leakage or selective denominators."

*Where it stands, measured.* No census detector measures it (TG-L5-026). The data that exists (DBQ, chart 482012f1): 139
candidate predictions in `mimamsa_predictions`, all `pending`, all sharing one `emitted_at` (2026-08-13) and each carrying a
`frozen_bundle_hash`; 63 events, of which 13 `held_out` and 50 not, all `admissible_clean`, `disclosure_timing = 'unknown'`
on 63/63; 57 rows of `mimamsa_calibration` (all `leakage_status = clean`), which match candidates to events inside each
prediction's window; 6 reliability bins, 4 graded `empirical` (`held_out_validity pass`) and 2 `prior_only`
(`insufficient_n`); 4 calibration snapshots all `proposed`, none `two_key_complete`; 18 filed rows in
`brahma_prospective_ledger`, all `open`; 5 in `brahma_mimamsa_prediction_ledger`. `kala_field_skill`: 7 rows all
`skill_state = underpowered`, `n_prospective` 0 and `n_backfill` 14 in total, `skill_prospective` never populated.
`mi_pramana` reads `mimamsa_predictions` (`SELECT *`, `mi_pramana.py:324`) and `mimamsa_event_provenance` rows with
`admissible_clean = true AND held_out = false` (`:333`); it does not read either `brahma_*` ledger (grep). Whether that is
the "frozen forecast probability against independent outcome" that DP15b and T2 §9.3 (line 525) require is **not assessed
here** — it is a layer finding recorded as F-06.

*What closes the gap.* T3 §3.1 asks for it; the tiers supply no closing definition, only the required evidence in T1 §14.
Packets that the tiers do name are W08 and W09 (§4.2). No closing steps beyond those are written.

**Operational honesty.** T1 §14 (line 596): "Earned statuses, recovery under failure, actual cost and reliability; no
operational metric misrepresented as astrological value."

*Where it stands, measured.* CEN: `Build.completion` FAIL 10 / PARTIAL 3 / PASS 2; `Build.history` FAIL 8 / PARTIAL 5 / PASS 1 /
N/A 1; `Build.dep_liveness` FAIL 10 / PARTIAL 1 / PASS 2 / N/A 2; `Idem.pattern` PASS 11 / PARTIAL 3 / N/A 1; `Earn.build_record`
and `Cost.baseline` NO_DETECTOR 15/15 (instrument absent, migration 1094). Status labels that read as measured but rest on a
threshold: `mi_pramana.py:535-536` sets `held_out_validity = "pass"` and `evidence_grade = "empirical"` when a bin holds five
or more rows (`n >= 5`) and `insufficient_n` / `prior_only` otherwise — a count, not a check that the rows are frozen,
eligible or independent (F-05). On "No invented … confidence" (T1 §13): the writer at `2a78ec64d` documents explicit nulls
(`base_rate` and `brier_vs_null` NULL, `ece` NULL; `mi_pramana.py` header and `:82-110`, findings A-F-24 and A-F-30), **but the deployed
rows differ from that code**: DBQ shows `mimamsa_calibration.base_rate = 0.1` on 57 of 57 rows (one distinct value) with
`brier_vs_null` non-null on 57 of 57, all scored 2026-08-13; the code's own docstring records that this is the earlier
hardcoded default it removed ("ALL 57 with base_rate = 0.10 (1 distinct value)"). `mimamsa_reliability.ece` is NULL on 6 of 6, as the
code says. This is the deployed-versus-current-code risk of T3 §4.1 in one measured case (F-12).

#### How the tiers express "structural" versus "empirical" (recorded, not resolved)

| where | words used | what is defined |
|---|---|---|
| T1 §5.2 (lines 324-326) | "deterministic fact, structural prior, classical prior, empirically calibrated claim and unresolved interpretation" | five kinds to "keep … distinct" — no definitions, no detector |
| T2 §6.6 (line 402) | "stored evidence, structural estimates, actual measured performance and service readiness" | four things to "differentiate" — a different list, no definitions, no detector |
| T2 §12.2 (line 626) | "Empirical performance: Separately admitted frozen eligible claims, appropriate baselines, observation denominators, held-out/prospective evaluation and uncertainty; engineering fixtures are not real-life evidence." | the test, not a state |
| T2 §11 (line 572) | "Service/source-only assets need applicable service/source proofs, not fabricated row floors." | how to treat assets with no rows |
| T3 §5.1, §5.2; T4 §4 | none | no state vocabulary |
| CLAUDE.md §E; plan §1.5 | "STRUCTURAL mode"; "L5 fills by design" | the campaign's own statement of intent, outside the tiers |

How L5's rows carry it today (DBQ, chart 482012f1): `mimamsa_reliability.evidence_grade` ∈ {empirical, prior_only};
`mimamsa_insight_units.evidence_grade` ∈ {empirical, prior_only, structural}; `mimamsa_multipliers.promotion_status` ∈
{promoted 2, prior_only 7}; `mimamsa_signal_families.calibration_status` = `prior_only` on 11 of 11 (whole table);
`mimamsa_qa_eval.status` includes `structural_proxy` (10) and `not_implemented` (4); `mimamsa_calibration_snapshot.publication_status`
= `proposed` (4). **TIER GAP: TG-L5-014.** This draft maps none of these labels to a tier category; the tiers give no mapping.

### 3.2 · Per asset — disposition

```
inherits:    Data plane §10.1 (eight dispositions)
measured_by: T2c §7 for the provisional code and delta text; CEN for the evidence pointer; no evidence-to-disposition rule exists
traces_to:   0.2
```

**TIER GAP: TG-L5-023.** T3 §3.2 asks for one of P/I/E/Q/C/H/R/U per asset "with the evidence from Part 1 that justifies it"; no
tier gives a rule from evidence to disposition, and Part 1 has no contribution terms (§1.5). T2c §7 (status PROPOSED; written
against parent v2.0; "no row is an authorized implementation or reopening instruction") supplies provisional codes. They are
reproduced as **provisional, unevidenced**; no code is adopted, and none is R, C or U.

| asset | T2c provisional code | T2c "provisional delta" (near-verbatim) — a candidate for §3.3 | census pointer |
|---|---|---|---|
| `lel_events` | P/E/I/Q | reconcile intake, revisions, provenance/precision/purpose and testimony identity | Build.completion FAIL (no build record); readers not in registry |
| `mi_jivanaghatana` | P/E/I/Q | remove unscoped legacy fallback; retain unknown/empty; knowledge time must be claim/revision-specific | completion PASS; 6 columns never populated; 0 modules |
| `mi_bhavisya` | P/I/Q | not frozen issued-claim authority; content-complete issuance snapshot and claim linkage | history FAIL; deps stale |
| `mi_abhilekha` | P/E/I/Q | structured explicit adjudication instead of substring outcomes; unknown/partial/disputed/unobserved retained | DRAFT; 0 rows; dep FAIL |
| `mi_pramana` | P/E/I/Q | match-score-derived verdict is not independent forecast calibration; frozen probability, outcomes and denominator contract | completion FAIL; 13 of 18 columns dark |
| `mi_kula` | P/I/Q | preserve global ownership; family membership/version is not validation or personal truth | completion PASS |
| `mi_gunanaka` | P/Q/H | retain proposal snapshots; sample count / not_assessed input does not qualify serving or held-out validity | completion FAIL; snapshot accretion (F-04) |
| `mi_adhilepa` | P/I/Q/H | approved immutable snapshot/model admission required; mutable multipliers/kill-switch not enough | history FAIL; 112,270 rows chart |
| `mi_pariksha` | P/E/Q/H | enforce actual declared cutoffs before blind claims; structural labels preserved; no autonomous research activation | history FAIL |
| `mi_sambandha` | P/I/Q | retain NULL for unmeasured attribution; qualify coverage and frozen channel definitions | Ldgr.source_presence PASS 47/47; history FAIL |
| `mi_darshana` | P/I/Q | purpose/exposure partition before common retrieval; no embeddings claimed from this writer | 0 embedding rows; 8 deps, 5 not live |
| `mi_seva` | P/E/Q | four-table existence check proves only that; require actual authorized service and consumer-effect proof later | DRAFT; 0 rows |
| `mi_vistara` | P/E/I/Q | verify exporter wiring, payload identity/scope and delivered artifact; no artificial chart build rows | history PASS; 0 rows; 0 modules |
| `mi_bhara` | P/Q/H | current orchestrator explicitly does not refit while basis columns pending; preserve research kernel; no claim of active personal tuning | completion FAIL; writes 5 tables (F-03) |
| `mi_sankalpa` | P/I/Q/H | retain explicit-filing FK / native attestation; observational arms are not randomized or causal-efficacy proof | dormant; 0 rows; 0 modules |

### 3.3 · Per asset — what it must add

```
inherits:    Data plane §13.3 item 6 (contract, presentation, coverage fields)
measured_by: T2c provisional deltas (above); nothing else is supplied
traces_to:   0.2
```

The contract fields (2.3), presentation fields (2.2) and coverage states (2.4) each asset must add cannot be listed:
2.2 and 2.4 are gaps (TG-L5-009, -011) and 2.3's declared uses are absent (TG-L5-010). The provisional deltas in §3.2 are
the only supplied "must add" text and are **candidates** for a brief, not obligations. Census-derived facts that any
brief for the asset will meet, stated as facts: Build.completion / history / dep_liveness readings (§3.1); never-populated
columns (CEN `Complete.depth`: `mi_bhara.skill_prospective`; `mi_bhavisya.base_rate`, `contact_id`, three
`chart_context_*` columns; `mi_darshana.horizon`; `mi_gunanaka.domain`; `mi_jivanaghatana` `shaped_predictor_refs`,
`disclosure_date`, `domain_secondary`, `event_magnitude`, `lel_file_sha`, `event_class_id`; `mi_kula` `data_source_pin`,
`apply_point`, `interaction_value`, `interaction_status`; `mi_pramana` `manifestation_channel`, `base_rate_adjusted_skill`).

### 3.4 · Intra-layer interplay

```
inherits:    Data plane §13.3 item 3
measured_by: REG edges; CODE FROM/JOIN scan (regex over each writer file and, for mi_bhara and mi_sankalpa, their service package)
traces_to:   0.3, 1.3
```

Tables named in SQL text by each L5 writer (static scan; may miss dynamic SQL; `mi_seva` names none — its docstring describes an
existence check). "Declared use" is TG-L5-010 and is left blank.

| asset | tables read or written (CODE) | in `depends_on` (REG) |
|---|---|---|
| `mi_abhilekha` | `mimamsa_journal`; updates `mimamsa_predictions` (`:70`) | `mi_bhavisya` |
| `mi_adhilepa` | `bodha_msr_signals`, `chart_facts`, `kala_convergence`, `mimamsa_multipliers`, `phala_anchors` (writes 5 overlay tables) | `mi_gunanaka`, `bo_laksana`, `ka_sangam`, `ph_nimitta`, `ga_positions` |
| `mi_bhara` | `brahma_prospective_ledger`, `kala_field`, `kala_field_null`, `kala_field_weight_versions`, `kala_insights`, `life_events`; writes `kala_field_skill`, `_gof`, `_weights`, `_weight_versions`, `kala_insights` | `ka_kshetra` |
| `mi_bhavisya` | `bodha_msr_signals`, `phala_anchors`, `mimamsa_predictions`, `mimamsa_manifestation_sets` | `ph_pramana`, `ph_nimitta`, `ph_phaladesa`, `mi_kula`, `mi_jivanaghatana`, `bo_laksana` |
| `mi_darshana` | `bodha_contradictions`, `bodha_msr_signals`, `bodha_pratijna`, `bodha_triangulation`, `brahma_event_ontology`, `mimamsa_discoveries`, `_insight_embeddings`, `_insight_units`, `_load_bearing`, `_manifestation_grammar`, `_reliability` | eight, incl. `bo_pratijna` |
| `mi_gunanaka` | `brahma_formula_constants`, `mimamsa_calibration`, `_multipliers`, `_predictions`, `_signal_families`; inserts `_calibration_snapshot` | `mi_pramana`, `mi_kula`, `bg_formula_constants` |
| `mi_jivanaghatana` | `brahma_event_ontology`, `life_events`, `mimamsa_event_provenance` | `bg_ghatana` |
| `mi_kula` | `brahma_class_priors`, `mimamsa_negative_controls`, `mimamsa_signal_families` | `bg_rules`, `bg_class_priors` |
| `mi_pariksha` | `bodha_msr_signals`, `phala_anchors`, `brahma_formula_constants`, five `mimamsa_*` incl. `_predictions`, `_event_provenance`, `_calibration`, `_negative_controls`, `_signal_families` | `mi_pramana`, `mi_kula`, `bg_formula_constants` |
| `mi_pramana` | `brahma_formula_constants`, `mimamsa_predictions`, `_event_provenance`, `_manifestation_sets`, `_calibration`, `_reliability` | `mi_bhavisya`, `mi_jivanaghatana`, `bg_ghatana`, `bg_formula_constants` |
| `mi_sambandha` | `mimamsa_calibration`, `_manifestation_grammar`, `_manifestation_sets` | `mi_pramana`, `mi_pariksha`, `mi_bhavisya` |
| `mi_sankalpa` | `life_events`, `mimamsa_intervention_ledger` (FK to `brahma_prospective_ledger` per its header) | `ka_kshetra` |
| `mi_seva`, `mi_vistara` | none / `mimamsa_export_log` | `mi_adhilepa` / none |

Reads with no matching declared edge include `mi_gunanaka` → `mimamsa_predictions` (owner `mi_bhavisya`), `mi_pariksha` →
`bodha_msr_signals` and `phala_anchors`, `mi_adhilepa` → `chart_facts`, `mi_bhara`/`mi_sankalpa`/`mi_jivanaghatana` →
`life_events`. This scan is offered as evidence for the declared-versus-actual comparison (T4 §1, "the gap between the two is a
finding"); it is not the migration-691 measurement and does not replace it.

The synergistic term (1.3) is neither built nor found missing by this section: no harness exists to say which.

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG of §2.5; the three-way baseline per asset
traces_to:   0.2
```

Upstream before downstream within L5, cross-layer gates honoured (T3 §4.1). Order: §2.5's levels 0 to 5. Within a level, "chosen
for learning value, not alphabet": no tier states a learning-value criterion for L5 and none is invented. Cross-layer constraint
(measured): `mi_bhavisya` waits on L4 (`ph_nimitta`, `ph_phaladesa`, `ph_pramana`), `mi_adhilepa` on L3 `ka_sangam` and L4
`ph_nimitta`, and `mi_bhara` and `mi_sankalpa` on L3 `ka_kshetra` — the family assets are Track F's (R8/P11, not touched).

**Three-way baseline** (T3 §4.1): *deployed* — REG table list and row counts of §1.1 (production schema, read 2026-09-30);
*current code* — the inspector checkout `2a78ec64d` only; the newest code on any live head, including unmerged, is **not
measured** (TG-L5-025); *target* — the brief's, not yet written. The delta is target minus current code and the risk is current
code minus deployed; only deployed is measured. One measured instance of the risk: F-12 (`mi_pramana` base rate).

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x — every packet closes a named delta item
```

The tiers name two L5 packets. This draft adds none.

| packet (T2 §13.1) | text (verbatim) | delta item it closes | proof detector |
|---|---|---|---|
| W08 Observation/history slice (line 644) | "Canonical intake/revision ownership, purpose/chronology, one historical comparison/protected review." Depends on/exit: "Own intake/firewall contracts; can be designed in parallel, no automatic future conditioning." | TG-L5-006 (ownership), TG-L5-007 (overlay separation), F-01, F-07 | none defined (TG-L5-008) |
| W09 L5 challenge and value (line 645) | "Frozen comparison sets, independently adjudicated outcomes, misfit/unknowns, explanatory and empirical tests; qualified future artifact procedure." Depends on/exit: "DP15a already protected at issuance; DP15b evaluates later. No dormant fitting/service activation without existing gates and separate authority." | §3.1 predictive performance; TG-L5-014, -026, -027 | none defined |

W06 (L4) carries "DP15a issuance/eligibility/firewall proof before forecast cutover" (line 642) and is not L5's. Packets
Suvarṇa itself will need (rebuild, fix designs, semantic detectors) belong to Tracks A/I/E and are outside this instance.

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: DBQ (chart_context_* columns; emitted_at), CODE (delete scopes), INV; the invalidation path was not exercised
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

- **Rebuild replaces its own rows** (T4 §6): true of 11 assets by CEN `Idem.pattern` PASS. Exceptions and refinements that no tier
  reconciles with the never-accretes rule (T2 line 402, DP15a and T1 §7.3 preserve such records): `mi_gunanaka` snapshot accretion (ratified, F188); `mi_bhara` append-only versions plus a status update;
  `mi_sankalpa` and `mi_bhavisya` scoped deletes; `mi_kula` deletes both its global tables entirely (`mi_kula.py:312-313`);
  three assets write no row of their own table (`mi_abhilekha`, `mi_seva`, `mi_vistara`, `Idem.pattern` PARTIAL "nothing to
  replace") (TG-L5-017, -018).
- **Chronology.** All 139 `mimamsa_predictions` rows share one `emitted_at`, 2026-08-13, i.e. the last rebuild stamped the
  whole set, consistent with T2 §9.1 (candidates are "rebuildable, not protected issuance history"). The protected
  issuance authorities named by T2 (`brahma_prospective_ledger`, `brahma_mimamsa_prediction_ledger`) are not L5 assets.
- **Stale marking (DP16).** `mimamsa_predictions`, `mimamsa_calibration_snapshot` and both `brahma_*` ledgers carry
  `chart_context_stale_at`/`_reason`/`_superseded_by_run_id`; on `mimamsa_predictions` they are never populated (CEN
  `Complete.depth`; 0 of 139 rows stale-marked, DBQ). Whether the path works was not exercised.
- **Rollback and history.** Non-regenerable tables are listed in §1.1.b; no rollback of them is contemplated by this
  campaign (N-46).

### 4.4 · What each asset brief inherits

```
inherits:    Product §16; Data plane §13.3 (asset brief sentence)
measured_by: derivability — can a brief author fill each row from this instance alone
traces_to:   0.1
```

Fill status of the thirteen rows for L5 (T3 §4.4; T4 §0.1). A row that cannot be filled is a hole in this instance, and
the brief author must not invent it.

| # | row | fillable from this instance? | basis |
|---|---|---|---|
| 1 | P/V the asset serves | no | TG-L5-001 |
| 2 | obligations scored on | yes, layer-uniform | predictive performance + operational honesty (§0.2); per-asset weighting not stated (R118) |
| 3 | correctness rules and switch | partial | six rules quoted (§2.1); switch ON/OFF stated at plane level (T2 §9.2 lines 500-501), per-table overlay separation TG-L5-007; detectors TG-L5-008 |
| 4 | presentation fields | no | TG-L5-009 |
| 5 | contracts with declared use | partial | T2c ids, provisional and with a removed id (§2.3); uses TG-L5-010; field/grain TG-L5-003 |
| 6 | coverage obligations and states | no | TG-L5-011 |
| 7 | position in order, three-way baseline | partial | order measured (§2.5); deployed measured (§1.1); current code and target not (TG-L5-025) |
| 8 | disposition and must-add | partial | T2c provisional only (§3.2); no evidence rule (TG-L5-023) |
| 9 | individual term | absent instrument | TG-L5-021 |
| 10 | synergistic term | absent instrument | TG-L5-021 |
| 11 | cross-layer term, evidence state | partial | modules per asset (§1.4); verified state not run (TG-L5-022) |
| 12 | preserved kernel | no | TG-L5-023; T2c gives kernels in prose only (§3.2) |
| 13 | Jyotish concepts and carriage check | no | TG-L5-013 |

Also required by T4 §0 and not supplied: the asset's `role` (manifestation / temporal / neither) — TG-L5-024. Row 2 is the only
fully filled row; rows 3, 5, 7, 8 and 11 are partly filled; the remainder are holes. **A brief for any L5 asset written now
would invent the majority of its inheritance.** This draft therefore fails T3 §5.4 test 1 by construction (§5.4).

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: none — no harness (§1.2-1.3)
traces_to:   0.2
```

Individual, synergistic and cross-layer flavours are all absent instruments for L5. L5 scores on two of the ten
obligations (predictive performance, operational honesty). No ablation delta is recorded.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-§N.8
measured_by: CEN measurements grouped under the nine gates; the certification ledger is not written by this draft
traces_to:   4.4
```

**The nine gates for L5, as the census reads them** (cells are assets, 15 per criterion; a criterion with no census row for a
gate is stated as such). Verdicts are CEN's, unadjusted; nothing here is a certification.

| gate | census criteria feeding it | L5 reading (of 15 assets) |
|---|---|---|
| Ldgr | Ldgr.source_presence | 1 PASS (`mi_sambandha`); no reading for 14 |
| Idem | Idem.pattern | PASS 11 · PARTIAL 3 (`mi_abhilekha`, `mi_seva`, `mi_vistara`: nothing to replace) · N/A 1 (`lel_events`) |
| Earn | Earn.build_record (with Cost.baseline) | NO_DETECTOR 15 (instrument absent, migration 1094) |
| Null | none | no census criterion (E6 builds generic detectors before J1; plan §2.1); per-asset convention TG-L5-031 |
| Vocab | Vocab.identity | PASS 10 · NO_DETECTOR 4 · no reading for `lel_events` |
| Carr | Carr.detector | NO_DETECTOR 15 |
| Narr | none (conditional on the asset emitting prose) | no census criterion; which L5 assets emit prose is unassigned (TG-L5-009) |
| Dens | Dens.served (conditional on a served surface) | PASS 9 · N/A 6 |
| Build | Build.registered, .contract, .target, .dag, .count_integrity, .completion, .exercised, .history, .dep_liveness | .registered/.contract/.target PASS 14, N/A 1 · .dag PASS 15 · .count_integrity PASS 15 · .completion FAIL 10, PARTIAL 3, PASS 2 · .exercised PASS 14, N/A 1 · .history FAIL 8, PARTIAL 5, PASS 1, N/A 1 · .dep_liveness FAIL 10, PARTIAL 1, PASS 2, N/A 2 |

Cell totals: FAIL 28, PARTIAL 19, NO_DETECTOR 53, PASS 125, N/A 29, NOT_GENERIC 30 (284 cells), tallied from CEN and matching
SUMMARY.md row L5. The 28 FAILs are Build.completion 10, Build.dep_liveness 10, Build.history 8. Non-gate criteria (Cost,
Count, Complete, Reach) are information, never blockers (D3): Count.floor N/A 15; Complete.width NOT_GENERIC 15; Reach.fields
NOT_GENERIC 15; Complete.depth PASS 3, PARTIAL 7, NO_DETECTOR 4.

**The gate map, filled** (T3 §5.2: the instance fills the right-hand column and reports any row it cannot fill).

| gate | section a brief author reads | what the instance supplies for L5 |
|---|---|---|
| Ldgr | §2.3 contracts, with declared use | **cannot fill** — upstream `fact_id` sources are not named for any asset (TG-L5-010); one source-presence reading exists (`mi_sambandha`) |
| Idem | §2.5 edges and order; §4.1 order and baseline | natural keys per §2.6 (10 declared; `lel_events` `(chart_id, event_id)` per its `integrity_check_sql`; `mi_seva` `(user_id, channel_id)`; `mi_vistara` `(export_id)`; `mi_kula` `(family_id)`; `mi_abhilekha` `(chart_id, journal_id)`; `mi_sankalpa` `(chart_id, intervention_class, rite_or_activity_class, elected_window)`); rebuild-scope exceptions in §4.3 (TG-L5-017, -018) |
| Earn | §2.4 coverage obligations and their states | **cannot fill** — coverage states are unassigned (TG-L5-011); labels that are claims are listed in §3.1 (`evidence_grade`, `held_out_validity`, `promotion_status`, `leakage_status`, `calibration_status`, `publication_status`, `skill_state`) with no falsifier defined by any tier |
| Null | §2.4 (state vocabulary); §1.4 | **cannot fill** (TG-L5-031) — no asset's own convention for an underivable value is supplied; observed nulls are recorded as facts (§3.1, §3.3) |
| Vocab | §2.6 | classes as far as §2.6 goes; authority per class unassigned (TG-L5-012) |
| Carr | §2.7; §4.4 row 13 | **cannot fill** per asset (TG-L5-013); candidates only |
| Narr | §2.2 presentation fields | **cannot fill** — whether each asset emits prose is not stated (TG-L5-031) |
| Dens | §2.2; §3.4 served boundary | modules per asset (§1.4); nine assets serve, six do not |
| Build | §2.5; §1.1; §4.3 | writer file and registered id, target, edges, build record per asset in §1.1 and §2.5; `lel_events` declared no-writer (§1.1.a) |

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson; asset_certs.jsonl `_schema`
measured_by: none — this draft writes no certification record
traces_to:   —
```

No record is written to any ledger by this draft (Track A boundary; status PROVISIONAL). No N/A is typed for any asset. The
`lel_events` N/A of N-14.R236 is recorded as a decision and a census disagreement (§1.1.a), not as a verdict.

### 5.4 · Acceptance of the instance itself

```
inherits:    T3 §5.4
measured_by: author's pass; independent review not performed
traces_to:   —
```

| test | status |
|---|---|
| 1 · Derivability (a fresh-context reader derives one brief with zero inventions) | **not met and not run.** §4.4 shows, of 13 inheritance rows, 5 holes, 2 absent instruments, 5 partial and 1 filled; TG-L5-001 to -031 |
| 2 · Alignment (every section names `traces_to`) | done by the author; the reviewer's strike-pass is pending |
| 3 · Measured, not inherited (every figure names its `measured_by`) | done via the source labels of Appendix A; a reviewer re-run is pending |
| 4 · Presentation parity | [TRANSFERS]-pending (R71/R094): T2 §12.2 line 614 marks parity [TRANSFERS], T3 line 628 does not, and the register row is open; the draft carries no L5 presentation rows (TG-L5-009) |
| 5 · The gate map exists | yes, §5.2 (five of nine rows cannot be filled) |
| 6 · Independent review, fresh context | **not done.** This is a provisional draft; it may register gaps and may not certify. No verdict is claimed |

---

## Part 6 · Corrections, findings and inputs reconciled

*The template's §5.2 sends unfillable rows to "§7 as corrections with gates", but the template defines no §7 (R08, TG-L5-028).
This section is that place. It separates **document-level** findings (defects in this draft or its inputs, to be fixed in the
document) from **layer-level** findings (correctly recorded, work for later packets). Each layer finding names the gate it
bears on. None is fixed by this pass.*

### 6.1 · Measured figures that differ from an earlier document

| earlier document | says | measured (source) |
|---|---|---|
| L5 skeleton (`L5_INSTANCE_SKELETON.md`, 2026-09-26) | 14 assets; 12 `@register` ids found; `mi_bhara` and `mi_sankalpa` "registry says writer, code has none (Build.registered FAIL)" | 15 assets (REG, CEN `population_active`); 14 registered ids (CEN, CODE); both `mi_bhara` and `mi_sankalpa` register via `@register(ASSET_ID)` and Build.registered is PASS 14 (R43 closed the inspector defect) |
| L5 skeleton, §1.1 table | per-asset counts such as `mi_adhilepa` 9, `mi_bhavisya` 195, `mi_darshana` 150, `mi_pariksha` 174, `mi_pramana` 57, `mi_sambandha` 47 | target-table counts (whole table, all charts) versus CEN chart-scoped totals over each asset's `count_sql`: `mi_adhilepa` 112,270, `mi_bhavisya` 278, `mi_darshana` 115, `mi_pariksha` 1,664, `mi_pramana` 63, `mi_sambandha` 24. Different bases, not a data conflict; CEN's own `Build.completion` text states the whole-table target-only figure beside the compared one |
| SUMMARY.md (census run) | "L5: 14 registered ids vs 15 assets … which asset lacks a registered id was not identified" | `lel_events`; 14 = 14 `has_writer = true` (§1.1) |
| T2c §7 | "14 writers and one source asset" | agrees with REG/CEN (14 + 1 = 15) |
| INV | `life_events` "57 seed events recoverable" | 63 events for chart 482012f1 (DBQ); not reconciled |
| Decision N-14.R236 | Build/Idem N/A by registry rule for `lel_events` | CEN reads Idem N/A but Build.completion FAIL |
| Register R236 (v2.8) | OPEN — native/data-plane decision | decided (DEC, 2026-09-29); register row not folded |

### 6.2 · Layer-level findings (gate each bears on)

- **F-01 `lel_events` is read by four writers and has no dependents in the registry** (blocking radius 0/0). CODE readers:
  `mi_jivanaghatana.py:215`, `services/mi_bhara/db.py:143`, `services/mi_sankalpa/db.py:64`, L4 `ph_rectification`. Migration 691
  (line 164) already records that `depends_on('mi_jivanaghatana')` omits `lel_events` and that the L5 W1 found 32 DAG corrections,
  none applied. *Bears on:* Build (DAG resolvable, check 4) and the first L5 rebuild.
- **F-02 The inspector reads Build.completion FAIL for `lel_events` where N-14.R236 says Build is N/A.** Seed catalog status is `DRAFT`,
  live `CURRENT`. *Bears on:* Build gate for `lel_events`; needs the E6 applicability rule (N-13/N-22).
- **F-03 `mi_bhara` declares one table and writes five** (`kala_field_skill`, `_gof`, `_weights`, `_weight_versions`, `kala_insights`), one
  of them append-only and in INV; the seed's target differs from the live registry's; CEN `reach` lists one capability module
  while `Dens.served` lists none. *Bears on:* Build (count/integrity, completion honesty) and Idem.
- **F-04 `mi_gunanaka` inserts an accreting table by ratified exception (F188); CEN's Idem PASS cites only the multipliers delete.**
  *Bears on:* Idem.
- **F-05 `evidence_grade = 'empirical'` and `held_out_validity = 'pass'` in `mimamsa_reliability` are set by `n >= 5` bin size**
  (`mi_pramana.py:535-536`). *Bears on:* Earn (a status with a detector that measures a proxy, §N.8).
- **F-06 `mi_pramana` calibrates against `mimamsa_predictions` candidates**, not the protected ledgers T2 names as issuance authority
  (`brahma_prospective_ledger` 18 rows, `brahma_mimamsa_prediction_ledger` 5), and all 139 candidates are `pending`. Whether this
  matches DP15b is not assessed. *Bears on:* Earn, and the W09 packet.
- **F-07 The emission record lacks named columns for information cutoff and switch state** (T1 §7.2), across the three prediction tables;
  jsonb was not searched. *Bears on:* Earn/Null and W08.
- **F-08 Eight assets' most recent run is an upstream-blocked error**, with roots in L4 (`ph_phaladesa`, `ph_pramana`), L3 (`ka_kshetra`) and within L5
  (`mi_bhavisya`, `mi_pramana`). Roots were not read here. *Bears on:* Build (history, dep_liveness) for the whole layer.
- **F-09 `mi_abhilekha.run()` updates `mimamsa_predictions.lifecycle_status` from a journal answer by substring test (`"yes"` or
  `"confirmed"` in the lowercased answer; else `denied`)** (`mi_abhilekha.py:61-73`). T2c already flags "substring outcomes". *Bears on:* Earn and
  N-46 (a derived status on a mixed table).
- **F-10 `mi_darshana` (storage `pgvector`) has 0 rows in `mimamsa_insight_embeddings` for the canonical chart** (DBQ); T2c: "no embeddings claimed from this writer."
  *Bears on:* Build completion honesty and Dens.
- **F-11 Data-content observations:** `disclosure_timing = 'unknown'` on 63/63 event provenance rows; `event_magnitude`, `event_class_id`,
  `lel_file_sha` never populated (CEN); `life_events.recorded_at` minimum 2000-01-01 (a knowledge clock earlier than the system;
  reason not established). *Bears on:* T1 §7.3 ("an observation reported after the person has seen the forecast is not
  automatically independent") and W08.

- **F-12 Deployed `mimamsa_calibration` rows carry a base rate the checkout's code no longer emits.** `base_rate = 0.1` on 57/57 chart
  rows, `brier_vs_null` derived from it, scored 2026-08-13 (DBQ); `mi_pramana.py:82-110` documents that value as the earlier invented
  default (A-F-24, #1738) and the current code writes NULL. Also from that docstring: `event_class_id` NULL on 64/64 provenance rows
  at the time (63 rows now, all never-populated, CEN). Which code produced the deployed rows was not established. *Bears on:* Null and
  Earn (T1 §13, T3 §4.1 risk = current code minus deployed).

### 6.3 · Document-level findings

- The tier-2 companion register (T2c) is PROPOSED, written against parent v2.0 and cites a removed contract (TG-L5-004). This draft
  uses it only for provisional dispositions and DP ids and marks them so; whether a T2 companion counts as "tier" for gap
  purposes is a question for the coordinator (the common instructions list T1-T4 only).
- The template's structure (§2.5 after §2.7; §5.2 cites an undefined §7) forced Part 6 (TG-L5-028).
- Nothing in this file was measured on another chart (N-12: canonical chart only). Global tables were counted whole-table only
  where they have no `chart_id` or `scope = global`.

---

## Appendix A · Instruments and populations (T3 preface: an instrument names its population)

| label | instrument | population and revision |
|---|---|---|
| CEN | `/Users/Dev/suvarna-evidence/census/census_L5.json` (+ `.log`, SUMMARY.md) | inspector `2a78ec64d88e59438bd6527b4c99826432102c57`; generated 2026-09-30T20:24:11+05:30; layer L5; 15 assets = the active registry population; chart 482012f1-710e-4a25-994a-93821f5871aa; exit 2 |
| REG | read-only `psql -X` over `asset_registry` (login `suvarna_reader`, proxy 127.0.0.1:5433), 2026-09-30 | `layer = 'mimamsa'`, 15 rows (129 in the table, 127 active); columns `target_table`, `count_sql`, `depends_on`, `scope`, `catalog_status`, `asset_kind`, `has_writer`, `natural_key_partition`, `expected_volume_formula` |
| SEED | `platform/scripts/seed/asset_registry_seed.ts` at `2a78ec64d` | block-scoped regex parse of the 15 L5 entries; fields `depends_on`, `target_table`, `scope` compared for all 15; `catalog_status` compared only where the seed entry sets it (`lel_events`) |
| PIN | `platform/src/generated/nirmana-analysis-layer-pins.json` `layers.L5`; `nirmana-writer-digests.json` `writers.*` at `2a78ec64d` | L5 membership only |
| DBQ | read-only aggregate queries over public tables (`count(*)`, `count(distinct …)`, `group by` state columns), `WHERE chart_id = 482012f1-…`, or whole table for `mimamsa_signal_families`, `_negative_controls`, `_preferences`, `_export_log`, `kala_field_weight_versions` (no `chart_id` or global) | run 2026-09-30; no row content read; no other chart |
| CODE | files under `/Users/Dev/suvarna-census/platform/python-sidecar` at `2a78ec64d`: `pipeline/orchestrator/writers/mi_*.py`, `services/mi_bhara/`, `services/mi_sankalpa/`; the FROM/JOIN scan is a regex over non-comment lines | static text; not a parse |
| EGATE | `platform/scripts/nirmana/egate.sql -v layer=L5` (its header: read-only) | frozen definition revision `t3-2026-09-11-8b884eac` |
| INV | `SUVARNA_NON_REGENERABLE_INVENTORY_v1_0.md` (`/Users/Dev/suvarna-exec/00_ARCHITECTURE/briefs/suvarna/`) | a static sweep of `origin/main @ 56dba8ac5`; presence in production "to be confirmed by a live catalog read" |
| DEC | `DECISIONS.jsonl` (read at `/Users/Dev/suvarna/run/DECISIONS.jsonl`): N-14.R236, N-46 | as recorded |
| MIG | `platform/migrations/690_nirmana_l5_w3_registry_accuracy.sql`, `691_nirmana_l5_w3_integrity_contracts.sql` at `2a78ec64d` | comment text quoted; figures not re-measured |

*Not measured, with reasons:* the independent-map census per class (`local_map_candidates = -1`, inspector); ablation and synergy
(no harness); consumer-verified evidence states (no probe); current-code-on-live-head baseline (single-branch checkout);
the frozen-manifest `depends_on` pin (not located); the interface-parameter census; any figure on another chart (N-12);
whether any jsonb column carries switch state or cutoff; the root causes of upstream errors in L3/L4.
