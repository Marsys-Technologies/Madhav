---
artifact: L0_LAYER_INSTANCE
continues_canonical_id: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY   # v3.0's id; this file continues that artifact line and does not claim the id
tier: 3
kind: instance
version: "3.1-rev1"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L0i (step 2, layer-instance draft; continues and re-measures v3.0)"
layer: "L0 Brahmagyan — 40 active assets, bg_*"
continues: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md   # DRAFT_PENDING_ACCEPTANCE; NOT edited — this file is a new document
template: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md   # tier 3, FINAL/SEALED
parents:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                                 # tier 1
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md        # tier 2
tier_gaps: "L0_TIER_GAPS_v1_0.md (file name kept per arch §12.6; its frontmatter version is 1.1-rev1) — TG-L0-001 … TG-L0-030 are cited below as TG-L0-nnn; 28 are tier gaps, TG-L0-001 is a T1 proposal (not a gap) and TG-L0-028 is withdrawn as a tier gap (a layer finding); see that file's Summary"
census_run:
  path: /Users/Dev/suvarna-evidence/census/census_L0.json     # log beside it: census_L0.log; summary: SUMMARY.md
  exit_code: 2            # FAIL rows present = MEASURED (arch §12.14); no exit 4/5/75, none UNMEASURED
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57   # /Users/Dev/suvarna-census, detached at origin/campaign/nikasha-test
  generated: 2026-09-30T20:21:19+05:30
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
  runtime: 58s
measured_at: "Census as above. Read-only queries as suvarna_reader (127.0.0.1:5433, read-only by privilege, D6) on 2026-09-30 (UTC afternoon, after the census); files read at the census checkout, commit 2a78ec64d. Nothing was written to the database, the registry, a ledger or the checkout."
verdict: "NONE. This is a provisional draft: it may register gaps and may not certify. §5.4 states which acceptance tests are met (2 of 6)."
changelog:
  - "3.1-rev1 (2026-09-30): gate review corrections applied (independent Opus review 2026-09-30): 10 defects. Struck: the three obligations v3.0 added on its own authority (Computational correctness, Delivery fidelity, Operational honesty; §0.2, §3.1, §4.4) because T1 §11 assigns L0 one obligation and T2 §13.3 item 1 forbids a layer naming its own; removed: the PASS verdicts in §2.1 and the five-state results in §2.4, which rested on detectors and rules the draft chose itself (the instance now reports measured facts and assigns no verdict or state until a tier supplies the detector and owner, as the L1 instance does); corrected: '24 of 40 assets reach a served module' to 26 (census reach; 31 modules; Dens.served counts 23), the DP10/DP16 citation (T2 L456-457 names DP10 only; DP16 is in the §7.1 table at L436 and names no layer), the served-surface comparison with L1-L5 (non-test counts: L1 22, L2 7, L4 1, L5 15, L3 0), the pin generation (written in full), the §3.2 evidence for disposition P, and the TG-L0-006, -028 and -004 statements (T2 §9.2 and T4 §0/§1 supply more than the draft credited); labelled as outside the tiers: CLAUDE.md §N.8 (§2.1) and §N.4 (W-L0-6)."
  - "3.1 (2026-09-30, Exec Suvarṇa A.L0i): continues and RE-MEASURES v3.0 (2026-09-26). Method: every v3.0 figure was re-read from the census JSON (CEN-*), a read-only query (Q-*) or a named file (F-*); all 38 inventory counts and floors and the further figures listed in Appendix C reproduce unchanged. Fourteen changes are recorded in 'What changed versus v3.0' (CH-01 … CH-14): nine correct or withdraw a v3.0 statement that did not reproduce or was unsourced (CH-01, 02, 03, 05, 07, 08, 09, 11, 13), five update or extend one (CH-04, 06, 10, 12, 14), each with the measurement that replaced it. The three that change what a reader would conclude: (CH-01) v3.0 said no migration or pin exists for L0 — 28 of 40 L0 ids are named by registry-modifying migrations and an L0 pin exists; (CH-02) v3.0 said the DAG is two levels deep at most — it is four (max depth 3); (CH-03) v3.0 said 19 of 40 assets have a downstream consumer — 26 do (18 across layers). New in 3.1: the census gate cells (Appendix B), the L0-specific records the brief requires (§1.1.1 global scope · §1.1.2 the two other charts with L1+ rows, counts only · §1.1.3 bg_vidhi_floors DRAFT · §1.1.4 the Gochara L0 inputs, R9 · §1.1.5 the 36-versus-34 writer anomaly and bg_sign_medical), the Measurement register (Appendix A), and a TIER GAP mark on every section the tiers do not supply. v3.0's authored judgements (§0.1 P/V rows, §1.3 seams, §3.2 dispositions, §4.2 packets) are carried and marked CARRIED; none is presented as derived."
---

# L0 Brahmagyan — Layer Definition and Strategy (v3.1, provisional, re-measured)

**How to read the marks.** `[RE-MEASURED = v3.0]` the figure reproduces · `[CHANGED — CH-nn]` v3.0 said otherwise (see the
change table) · `[NEW]` not in v3.0 · `[CARRIED]` a v3.0 judgement or figure not re-measured in this pass, kept with its
provenance stated · `[TIER GAP: TG-L0-nnn]` the tiers do not supply the clause this section needs; whatever fills it is the
draft's own and is labelled so. Evidence IDs (`CEN-*`, `Q-*`, `F-*`) resolve in Appendix A. A figure with no ID either
is arithmetic on figures that have one or is marked `not measured`.

**The layer in one line.** L0 is the global foundation: 40 registered assets, every one `scope = global` (Q-01), holding the
tradition's testimony, the controlled vocabulary and the astronomy/calendar substrate that every later layer reads.
Its individual term is fidelity, not ablation (T2 §12.2, L601–607).

## What changed versus v3.0 (measured)

| # | v3.0 said | Measured now | Evidence | Why it matters |
|---|---|---|---|---|
| CH-01 | §0.3: the migration-governed pin "does not exist for L0. No migration asserts L0 registry rows." | 28 of 40 L0 ids are named by a statement that inserts into or updates `asset_registry` (e.g. migration 599 sets five L0 `depends_on` arrays; 642 rewrites bg_vidhi_floors' description; 644/703 the parihara floor and integrity check); an L0 pin exists (`nirmana-analysis-layer-pins.json`: current generation `l0:d2369b888e76:3dda261170ee`, `receipt_count` 40, 4 non-writer assets, a `definition_bindings.L0` block; a 36-writer digest inventory in `nirmana-writer-digests.json`). Seed↔live: `target_table` and `depends_on` agree for 40/40 (unchanged) but `target_floor` differs for 4 and `catalog_status` for 1. | F-01, F-02, F-03 | v3.0 looked for a `depends_on` pin and concluded there was none; the three-source reading is possible but the template never says which artefact is "the pin" (TG-L0-014). |
| CH-02 | §2.5: "a DAG two levels deep at most". | Depth histogram over the 40 assets: 24 at depth 0, 11 at 1, 4 at 2, 1 at 3 (bg_concordance ← bg_rules ← bg_yogas ← bg_ontology). Four levels, not two. Roots (24), assets with intra-L0 edges (16) and edges outside L0 (0) unchanged; 25 intra-L0 edges. | Q-02 | Order and rollback (§4.1, §4.3) depend on depth. |
| CH-03 | §1.4: "only 19 of 40 `bg_*` assets have any downstream consumer in `depends_on`; 21 have none". | 26 of 40 have ≥1 active dependent in any layer (agrees with the census's own `blocking_radius.transitive > 0` for 26); 18 of 40 have a dependent in another layer; 14 have none. Cross-layer edges: 34 from 22 assets (kala 21, mimamsa 7, ganita 5, bodha 1). The Gaṇita figure (5) reproduces; the 19 does not, and v3.0 stated no population. | Q-02, CEN-R | The "no consumer" set is 14, not 21, before any code read. |
| CH-04 | §1.1 finding 1: `bg_parihara_rules` is 9 below floor, "cause not established". | Established from committed migrations: 644 set the floor to 449 when the components were 61 + 329 + 59; 703 (applied 2026-09-06) deleted 9 orphaned rows (1 from `bg_parihara_rules` → 60; 8 from `bg_muhurta_factor_census` → 51) after the upsert-only writer failed to remove them, and re-pinned the integrity check — but left `target_floor` at 449. Live 60 + 329 + 51 = 440. | F-02, Q-12, Q-15 | The −9 is a stale registry floor, not lost data; it is also the documented instance of the upsert accretion TG-L0-023 records. No action here. |
| CH-05 | §2.6 rule 3: the 289 unresolved remedy ids "differ from resolving ones only by case". | Exact resolution 52 of 341 (unchanged) → 289 unresolved. Of those, 204 resolve case-insensitively; **85 do not** — `classical_tradition` ×80 (the placeholder) and 5 others (Tajaka ×3, nadi_navamsa_patel ×1, bphs_jaimini ×1). | Q-05 | "Normalisation drift" explains 204 of 289, not all. |
| CH-06 | §1.2/§2.1 measured the placeholder citation on doṣas only (53 of 79). | Doṣas 53 of 79 (unchanged); **also 1 of 233 yoga rows** cites `classical_tradition`; 0 of 20 daśā systems. | Q-04 | The placeholder is not confined to one catalogue. |
| CH-07 | §2.4: āyurdāya — "1 ontology concept exists and 0 rules qualify a method". | No `concept` row matches `ayur`/`lifespan`/`longevity`; the ontology holds `domain: longevity` (1), `karaka: karaka_longevity` (1) and `remedy_type: ayurvedic`; 0 of 3,002 rules and 0 of 10,651 chunks (topic tag or topics) match `ayur`. No coverage state is assigned (TG-L0-007); the "1 concept" is not reproduced (population unstated in v3.0). | Q-16 | The thinnest coverage L0 has is thinner than recorded. |
| CH-08 | §2.6 rule 6: "6 candidate sites in `brahmagyan/` alone". | The inspector reports 32 (files under `platform/python-sidecar/brahmagyan`, 125 `.py` files, holding L0–L5 code, that contain a quoted `Sun` followed by `,`/`:` and a quoted `Venus`); 11 are `l0_*` files. Different regex and population; still a heuristic, still **NO DETECTOR** for rule 6. | CEN-H, F-08, F-09 | The two figures are not comparable; neither is a per-class map census (TG-L0-011). |
| CH-09 | §3.2: "P preserve — 29 assets" beside 4 E + 2 Q + 2 I + 2 C = 39 assets; U: "the 21 assets with no declared downstream consumer". | 30 P (40 − 10 others); U is an annotation on the **14** assets with no active dependent, not a second disposition. | Q-02, arithmetic | v3.0 accounted for 39 of 40 assets. |
| CH-10 | §1.1/§5.2: tracker "NO_BRIEF 40/40 · gates certified 0/360" (pre-emission snapshot). | Read from the ledgers at the checkout (the tracker was not re-run): `asset_gaps.jsonl` holds 290 L0 rows (271 open gap, 1 in-progress gap, 18 open opportunity) across all 40 assets; `asset_certs.jsonl` holds its `_schema` line only — **0 certification records** (unchanged). | F-06 | v3.0's own note said this figure would drift; it has. |
| CH-11 | §4.1: "risk = current code − deployed = 0 … L0 is the one layer where nothing is in flight". | **Not measured.** No instrument compares deployed structure with the newest live-head writer (TG-L0-015). The L0 pin was superseded once (DP-SD-018) with seven assets changed — L0 code has moved. | F-03 | An asserted zero is withdrawn, not replaced by another number. |
| CH-12 | §2.3: L0 produces DP01, DP02 and its half of DP05. | Also the clock primitives of **DP07** (ephemeris, sky calendar, muhūrta lattice, gochara arcs) and, as a producer *about itself*, DP10 (T2 L456–457; DP16 is a row of the §7.1 table at L436 whose producer column names no layer, so L0's part in it is the draft's reading). | T2 L418–437 | The contract table was incomplete against T2 (TG-L0-004, narrowed). |
| CH-13 | §5.2: `Build.completion` "already failing … for 3 of the 5 measured on check 6"; §0.3 edge types asserted. | `Build.completion` FAIL for **14 of 40** (8 with `rows_written = 0` against a populated table, 4 whose `rows_written` disagrees with live, 2 with no build record at all). Edge types: no source records them (TG-L0-030) — the v3.0 claim "every outbound edge is edge 1 or 3" is `[CARRIED]`, unsourced. | CEN-M, Q-01 | The build-status surface is honest about being unreliable; edge classification is an assertion. |
| CH-14 | §5.3/§4.4: no explicit statement of the asset-level gate cells. | Applying the plan's own rollup (§1.4) to the census: `Null` and `Narr` have **no census criterion** (80 of 360 cells unreadable); `Earn` NO_DETECTOR 40/40; `Carr` NO_DETECTOR 40/40; `Ldgr` reads 24 of 40. | CEN-M, F-08 | The gate map can be filled at layer level only (§5.2; TG-L0-025). |

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; every P/V cited was checked to exist in the parents under FINAL numbering (T1 L154–179, T2 L115–129). The rows are CARRIED from v3.0 §0.1 and are the analyst's judgement, not a tier derivation. The derived companion below is measured (CEN-R blocking_radius; Q-02).
traces_to:   —  (this IS the origin)
```

**[TIER GAP: TG-L0-003]** No tier assigns P-needs or V-journeys to layers. The twelve rows below are v3.0's authored
judgement of where removing L0 removes the distinction itself; figures inside them are re-measured `[RE-MEASURED = v3.0]`.
Under D5 (R221) the template clause is being re-scoped to a catalog-unit closure; the measured companion after the table is
that closure's L0 slice, computed from the live `depends_on`.

| P / V | the distinction that disappears without this layer |
|---|---|
| P15 "what supports this in the tradition, where do schools disagree" | No source testimony and no school record: 721 attributions in `classical_attributions` (CEN-R), 8 `school` ontology rows (Q-03). |
| P22 "let me read the texts themselves" | The corpus *is* this layer: 15 texts, 10,651 chunks (Q-07). |
| P20 "which form of Jyotish suits my question" | Method identity, scope and applicability are L0 declarations (20 daśā systems — 60 cockpit rows over three tables — and 41 praśna-method rows over five tables, CEN-R, Q-04). |
| P07 / P23 "what does the tradition say about wellbeing / lifespan" | The method, its school and its cancellations are doctrine held here; āyurdāya has no method concept, rule or tagged chunk (§2.4, CH-07). |
| P09 "does this yoga form" | The catalogue definition and its prerequisites are what formation is tested against: 233 yoga and 79 doṣa definitions (Q-04). |
| P11 "when might I initiate something, which practices" | The muhūrta lattice (173,219 rows) and the attributed practice corpus (341 rows) (CEN-R). |
| P13 "does a different convention change this" | The conventions themselves — ayanāṃśa, node, house system, varga construction — are L0 declarations (`reference_*`, `brahma_formula_constants` 17 rows). |
| P16 / P17 exact fact · what have I not asked | The concept map an omission check expands against is the ontology: 741 rows, 16 classes (Q-03). |
| V08 source learning and scholarly depth | Entirely L0: passage, edition, witness, rule qualification. |
| V05 calendar, action and method selection | Calendar substrate (31,081 sky-calendar rows) plus method-eligibility vocabulary. |
| V12 lifespan and constitution | The applicable method and school identity, without which the computation cannot be qualified (thin — CH-07). |
| V01 connected self-understanding | The role vocabulary (77 kāraka + 11 planet ontology rows, Q-03) that keeps natural significator, functional role, lordship and kāraka from collapsing into one word. |

**Measured companion — L0's place in the necessity closure** `[NEW]`. Over the 127 active assets (Q-02): 26 of the 40 L0
assets have at least one transitive active dependent; 14 have none. The ten widest, by `blocking_radius` (CEN-R; direct /
transitive dependents, every layer): bg_ontology 4 / 69 · bg_reference 4 / 62 · bg_texts 8 / 58 · bg_nakshatra 2 / 58 ·
bg_kp_sublord_division 1 / 57 · bg_panchanga 1 / 57 · bg_dasha_systems 1 / 52 · bg_yogas 1 / 52 · bg_rules 3 / 51 ·
bg_ephemeris 6 / 35. The 14 with none are the assets no other asset declares a dependency on (the two Gochara inputs,
the four muhūrta/medical/vastu/parihara tables, bg_compendium_index, bg_concordance, bg_remedies, bg_sign_medical,
bg_sky_calendar, bg_transit_engine, bg_nakshatra_medical, bg_vidhi_floors); the registry understates consumption for at
least the R9 pair (§1.1.4) and bg_muhurta_lattice (read in 30 files, §1.4).

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (L0 row, T1 L500), Data plane §3.1 (L0 row, T2 L139), §6.1 (T2 L347–351)
measured_by: none — definitional
traces_to:   0.1
```

L0 makes every later distinction **attributable**. Conventional software hard-codes a term's meaning in the routine that
uses it; this layer holds meaning as data — one canonical identity per thing, the rule that qualifies it, the passage it
rests on, the convention it assumes and the boundary beyond which it does not apply — so a reasoning layer can read *why*
a computation was legitimate, not only what it produced (T2 §6.1: "a shared language that can be applied"). It hands the
join not answers but the vocabulary and the warrant that make answers checkable.

- **Owned question** (T2 §3.1): what does a term, rule, method or reference quantity mean, and when is it applicable?
- **Handed onward**: canonical identities; source-qualified doctrine; constants; astronomy and calendar foundations;
  method, prerequisite and exception vocabulary.
- **Must not claim**: personal fate; raw private biography as global truth; source count as probability.

**Obligations this layer is scored on.** T1 §11 (L500) names **one**: *Source and domain fidelity* — "canonical identity,
source fidelity, method boundaries". That is the only obligation the tiers assign to L0, and T2 §13.3 item 1 (L662–665) says a layer
plan that "names its own criteria instead of inheriting these is not derived from the product definition". T1 L500 already lists
"ephemeris and calendar foundations" in the L0 row, so the computed substrate is scored under fidelity too. v3.0 §0.2 added three
further obligations on its own authority (Computational correctness, Delivery fidelity, Operational honesty); **they are struck at
rev1** and nothing in this instance is scored on them. The measurements v3.0 attached to them stay where they are used as facts:
computed-substrate row counts (§1.1, §3.1), served-surface counts (§1.4), registry status counts (§1.1, §5.2). Whether T1 §14's
fidelity wording should say what it means for a computed quantity is a **proposal to T1**, recorded as TG-L0-001 (not a gap).

| obligation | scored on | applies to |
|---|---|---|
| Source and domain fidelity (T1 §11, L500; §14, L585) | the layer's one obligation | all 40 assets, including the five computed ones (ephemeris, sky calendar, muhūrta lattice, gochara arcs, cohort) |

**Not scored on** (T2 §13.3 item 1, L662–671): concept and relationship completeness (L2) · temporal integrity (L3) ·
interpretive fidelity, distinctive understanding, consumer understanding (formed above this plane) · predictive
performance (L5). **Domain correctness is excluded (native ruling 11)**; L0's half is carriage, §2.7. Ten obligations, not
eleven — do not correct the count upward.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types, T2 L146–166), §7 (DP contracts)
measured_by: live asset_registry (Q-01, Q-02) · the registry seed, block-scoped parse of all 40 bg_* entries (F-01) · migration statements that modify asset_registry (F-02) · the L0 layer pin (F-03)
traces_to:   0.2
```

- **Receives from:** no layer. All 40 assets have zero non-`bg_*` dependencies (Q-02) `[RE-MEASURED = v3.0]`. L0's inputs are
  external: the text corpus, the Swiss ephemeris (`pyswisseph`, per the seed's `volume_explanation` for bg_ephemeris, F-01) and the
  conventions the native has ruled on.
- **Hands onward to:** L1–L5 and the serving surface. 34 declared cross-layer edges from 22 assets onto 18 of the 40 L0
  assets: kala 21, mimamsa 7, ganita 5, bodha 1 (Q-02) `[CHANGED — CH-03]`. **[TIER GAP: TG-L0-030]** the registry has no
  edge-type column, so the classification of these edges as "definition" (edge 1) or "serving-context" (edge 3) is v3.0's
  assertion and stays `[CARRIED]`, unsourced. Contracts: **DP01 identity/release** and **DP02 rule qualification**; L0's
  half of **DP05** (the catalogue definition formation is tested against); and `[CHANGED — CH-12]` the clock primitives of
  **DP07** (T2 L426, "L0/L1/L3 primitives"), plus DP10 as a producer's obligation about itself (T2 L456–457); DP16 (T2 L436) names no layer in its producer column.
  **[TIER GAP: TG-L0-004, narrowed]** T2 §7.1 names L0 for DP01, DP02, DP05 and DP07 (and "All producers" for DP10); what no tier supplies is the per-asset and consumed-side assignment.
- **What the join needs from it:** the closed alias set that lets one identity render as *Śukra* for the acharya and *Venus*
  for the layperson; the school behind a rule and the fact that authorities disagree; the convention in force; the method
  boundary that says where a rule stops. The alias half is **not yet true for doṣas** (79 of 79 with an empty alias set,
  CEN-M `Vocab.alias`).

**Three-source reconciliation, stated separately as the template requires.** **[TIER GAP: TG-L0-014]** the template does not
name the migration pin, and the seed's own upsert SQL declares `depends_on`, `count_sql`, `target_floor`, `catalog_status`
and `has_writer` migration-governed once a row exists (F-01), so the seed is authoritative only for new rows on those
fields. The table states what each source actually says.

| source | state (population stated) |
|---|---|
| live `asset_registry` | 40 `bg_*` rows, all `is_active`, none `dead_flag` (Q-01) |
| registry seed | 40 `bg_*` blocks in `ASSETS` (F-01) |
| migration statements | 28 of 40 L0 ids are named by `INSERT INTO`/`UPDATE asset_registry` statements across 522 `.sql` files; 12 are not (bg_class_lifetime_counts, bg_class_priors, bg_cohort, bg_concordance, bg_ephemeris_engine, bg_formula_constants, bg_ghatana, bg_gochara_citation_resolution, bg_panchanga, bg_sarvatobhadra_grid, bg_sign_medical, bg_text_index) (F-02; a statement-level regex, not a SQL parse). The five migrations read for this pass (599, 642, 644, 703, 912) are recorded as applied (Q-12). |
| L0 pin | `nirmana-analysis-layer-pins.json` `layers.L0` and `definition_bindings.L0`; 36 `bg_` writers in `nirmana-writer-digests.json`; 4 non-writer assets (F-03). It pins writers and layer membership, not `depends_on`. |

**Seed ↔ live, field by field** (F-01): `target_table` 40/40 agree · `depends_on` 40/40 agree · `target_floor` **4 differ**
(bg_gochara_arcs seed 34,553 / live 33,933; bg_muhurta_lattice 91,477 / 164,575; bg_parihara_rules 439 / 449;
bg_transit_rules 75 / 76) · `catalog_status` **1 differs** (bg_vidhi_primitives seed DRAFT / live CURRENT) · `has_writer`
is set in the seed for one asset only (bg_gochara_citation_resolution, `false`). The seed's `count_sql` was not compared
reliably for 5 assets whose literals are multi-line or template strings (parse limit, disclosed, not a finding). v3.0's
"zero disagreements" held for the two fields it compared and was silent on the rest `[CHANGED — CH-01]`.

### 0.4 · The alignment test

Every section from Part 1 on carries `traces_to:`. Run on this draft: no section was struck; at rev1 the gate review struck three obligation rows inside §0.2 (they traced to no tier clause) and their dependants in §3.1 and §4.4. The L0-specific records the
brief requires (§1.1.1–1.1.5) each name the Part 0 item they serve, and Appendices A–D carry no obligation of their own.
Two v3.0 candidates struck at 3.0 (a governance-cadence subsection, an L0-owned glossary of layer names) stay struck.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2 (T2 L678)
measured_by: asset_registry (Q-01) · each asset's OWN count_sql, as the census ran it (CEN-R live_rows, count_sql_tables) · the census's per-asset criteria (CEN-M) · @register ids counted over platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py (F-04) · asset_throughput, build_runs, build_run_assets, asset_provenance_receipts (Q-10, Q-11) · asset_gaps.jsonl / asset_certs.jsonl (F-06)
traces_to:   0.3
```

**40 assets** (Q-01): 38 `asset_kind = data`, 2 `service` (bg_ephemeris_engine, bg_panchanga); 39 `catalog_status = CURRENT`,
1 `DRAFT`; 38 carry a `count_sql` and 37 an integrity SQL; all 40 `scope = global`; 5 carry `data_disposition =
RETAINED_AS_CAPITAL` (bg_texts, bg_ghatana, bg_cohort, bg_formula_constants, bg_gochara_citation_resolution); 21 carry a
`natural_key_partition`. Registry `has_writer` = 34 true / 6 false; the code registers **36** ids (§1.1.5)
`[RE-MEASURED = v3.0]`. Census scoring mode `fidelity`; population 40 = registry total 40, none excluded (CEN-H).
Census cells over the layer: **FAIL 42 · PARTIAL 24 · NO_DETECTOR 123 · ERRORED 0 · PASS 440 · N/A 68 · NOT_GENERIC 80**
(CEN-S; 777 cells). FAIL by criterion: Dens.served 23 · Build.completion 14 · Build.registered 2 · Build.exercised 1 ·
Count.floor 1 · Vocab.alias 1.

Ledger state (F-06, the checkout's files, not a tracker run) `[CHANGED — CH-10]`: **290 rows** for `bg_*` (271 open gap,
1 in-progress gap, 18 open opportunity), all 40 assets carrying rows; **0 certification records**; 9 × 40 = **360** gate
cells, none certified.

| asset | table set (n) | live (own `count_sql`) | floor | Δ | writer: registry / code | integrity SQL | census non-PASS cells (F fail · P partial · ND no detector) |
|---|---|---:|---:|---:|---|---|---|
| bg_class_lifetime_counts | `brahma_class_priors` | 6 | 6 | +0 | y / y | y | F: Dens.served; P: Build.history |
| bg_class_priors | `brahma_class_priors` | 171 | 171 | +0 | y / y | y | F: Dens.served |
| bg_cohort | `bg_synthetic_cohort` +1 | 110,000 | 110,000 | +0 | y / y | y | F: Build.completion; P: Build.history |
| bg_compendium_index | `brahma_compendium_index` | 9,571 | 9,571 | +0 | y / y | y | F: Dens.served; P: Complete.depth, Build.history |
| bg_concordance | `classical_attributions` | 721 | 721 | +0 | y / y | y | — |
| bg_dasha_systems | `brahma_dasha_systems` +2 | 60 | 60 | +0 | y / y | y | F: Dens.served; P: Build.history |
| bg_dignity_reference | `bg_dignity_reference` +4 | 151 | 151 | +0 | y / y | y | ND: Dens.served |
| bg_doshas | `brahma_dosha_catalog` +2 | 237 | 237 | +0 | y / y | y | F: Dens.served; P: Build.history |
| bg_ephemeris | `ephemeris_daily` | 825,084 | 825,084 | +0 | y / y | y | F: Build.completion, Dens.served |
| bg_ephemeris_engine | — (service) | — | — | — | n / n | n | F: Dens.served |
| bg_formula_constants | `brahma_formula_constants` | 17 | 17 | +0 | y / y | y | F: Build.completion, Dens.served; P: Build.history |
| bg_ghatana | `brahma_event_ontology` +1 | 39 | 39 | +0 | y / y | y | — |
| bg_gochara_arcs | `bg_gochara_arcs` | 33,933 | 33,933 | +0 | y / y | y | P: Build.history |
| bg_gochara_citation_resolution | `bg_gochara_citation_resolution` | 14 | 14 | +0 | n / n | y | F: Build.completion |
| bg_kota_chakra_rings | `bg_kota_chakra_rings` | 27 | 27 | +0 | y / y | y | P: Complete.depth |
| bg_kp_sublord_division | `bg_kp_sublord_division` | 249 | 249 | +0 | y / y | y | P: Build.history |
| bg_medical_mappings | `bg_medical_mappings` | 21 | 21 | +0 | y / y | y | F: Build.completion, Dens.served |
| bg_muhurta_lattice | `bg_muhurta_lattice` | 173,219 | 164,575 | +8644 | y / y | y | F: Build.completion, Dens.served |
| bg_nakshatra | `reference_nakshatra` +2 | 2,857 | 2,857 | +0 | y / y | y | P: Complete.depth |
| bg_nakshatra_medical | `bg_nakshatra_medical` | 27 | 27 | +0 | n / y **≠** | y | F: Build.registered, Dens.served |
| bg_ontology | `brahma_ontology` | 741 | 737 | +4 | y / y | y | F: Build.completion, Vocab.alias, Dens.served |
| bg_panchanga | — (service) | — | — | — | n / n | n | F: Dens.served |
| bg_parihara_rules | `bg_parihara_rules` +2 | 440 | 449 | -9 | y / y | y | F: Count.floor, Dens.served; P: Complete.depth, Build.history |
| bg_phaladeepika_latta | `bg_phaladeepika_latta` | 8 | 8 | +0 | y / y | y | — |
| bg_prashna_rules | `NULL` (5 tables) | 41 | 41 | +0 | y / y | y | — |
| bg_reference | `reference_planets` +10 | 1,242 | 1,242 | +0 | y / y | y | F: Build.completion; P: Build.history |
| bg_remedies | `brahma_remedy_corpus` | 341 | 341 | +0 | y / y | y | F: Dens.served; P: Build.history |
| bg_rules | `sutravali_rules` | 3,002 | 3,002 | +0 | y / y | y | P: Complete.depth |
| bg_sarvatobhadra_grid | `bg_sarvatobhadra_grid` | 0 | 0 | 0 | n / n | n | P: Build.count_integrity; ND: Complete.depth, Vocab.identity |
| bg_sign_medical | `bg_sign_medical` | 12 | 12 | +0 | y / y | y | F: Build.completion, Dens.served, Build.exercised |
| bg_sky_calendar | `bg_sky_calendar` | 31,081 | 31,059 | +22 | y / y | y | F: Build.completion, Dens.served |
| bg_text_index | `classical_text_chunks` | 361 | 361 | +0 | y / y | y | F: Build.completion, Dens.served; P: Idem.pattern, Complete.depth |
| bg_texts | `classical_text_chunks` | 10,651 | 10,651 | +0 | y / y | y | F: Build.completion, Dens.served; P: Complete.depth |
| bg_transit_engine | `bg_transit_engine` | 9 | 9 | +0 | n / y **≠** | y | F: Build.registered, Dens.served |
| bg_transit_rules | `bg_transit_rules` | 76 | 76 | +0 | y / y | y | F: Build.completion, Dens.served |
| bg_vastu_directions | `bg_vastu_directions` +1 | 32 | 32 | +0 | y / y | y | F: Dens.served; P: Complete.depth |
| bg_vedha_malefic_scale | `bg_vedha_malefic_scale` | 5 | 5 | +0 | y / y | y | — |
| bg_vidhi_floors | `vidhi_floor_items` +1 | 423 | 423 | +0 | y / y | y | P: Build.history |
| bg_vidhi_primitives | `vidhi_primitives` | 60 | 60 | +0 | y / y | y | F: Build.completion |
| bg_yogas | `brahma_yoga_catalog` +3 | 784 | 784 | +0 | y / y | y | F: Dens.served; P: Complete.depth, Build.history |

Legend: table set = `target_table` plus the other tables the asset's own `count_sql` sums (66 distinct tables across the
layer, Q-09). Δ = live − floor. `writer: registry / code` = registry `has_writer` / an `@register` id exists in code;
`≠` marks the two ids where they differ. Always-present cells not shown per row: `Earn.build_record`, `Cost.baseline`,
`Carr.detector` (NO_DETECTOR on 40/40), `Reach.fields`, `Complete.width` (NOT_GENERIC on 40/40). The two services
(bg_ephemeris_engine, bg_panchanga) have no table, `count_sql` or integrity SQL by design; the template's storage bullets
assume a table **[TIER GAP: TG-L0-029]**, and both still read `Dens.served` FAIL because modules reference them.

**Findings the inventory itself produces**

1. **`bg_parihara_rules` is 9 below its floor** — components 60 + 329 + 51 = 440 against 449 (Q-15). `[CHANGED — CH-04]` cause
   now established from migrations 644 and 703; the registry floor is stale, no rows were lost. *Finding, no action.*
2. **`bg_prashna_rules` has `target_table` NULL** while summing five tables `[RE-MEASURED = v3.0]` (Q-01). The template's
   "a *set*, not one pointer" has nowhere to live in the registry (TG-L0-010).
3. **The sum of the 38 `count_sql` outputs is 1,205,713 — a cockpit sum, not a row total** `[RE-MEASURED = v3.0]` (CEN-R).
   Three tables are counted under more than one asset: `brahma_ontology` (4 assets), `brahma_class_priors` (2),
   `classical_text_chunks` (2), and `bg_texts` counts rows while `bg_text_index` counts distinct topic tags over the same
   table — two units. **[TIER GAP: TG-L0-010]**
4. **`Build.completion` disagrees with live for 14 assets** `[NEW]` (CEN-M): `rows_written = 0` against a populated table
   ×8 (bg_ephemeris, bg_muhurta_lattice, bg_ontology, bg_reference, bg_sky_calendar, bg_text_index, bg_texts,
   bg_vidhi_primitives); a non-zero `rows_written` that differs from live ×4 (bg_cohort 10,000 vs 110,000;
   bg_formula_constants 10 vs 17; bg_medical_mappings 60 vs 21; bg_transit_rules 104 vs 76); no build record at all ×2
   (bg_gochara_citation_resolution, bg_sign_medical). For bg_medical_mappings, 60 arithmetically equals the live counts of
   the three registry rows the writer serves (12 + 27 + 21); cause not established. *Findings, no action.*
5. **`asset_throughput.state = 'lit'` is not evidence of a build** `[NEW]` (Q-10): 39 of 40 L0 assets have a row, all `lit`;
   bg_gochara_citation_resolution has none. Four of the 39 (bg_sign_medical, bg_nakshatra_medical, bg_transit_engine,
   bg_sarvatobhadra_grid) have no `build_run_assets` row at all — the CLAUDE.md §N.8 pattern (a status with no detector that
   could read false). *Finding, no action.*

#### 1.1.1 · Global scope `[NEW]`

```
inherits:    Data plane §1 (L0 "remains the global foundation", T2 L58), §3.3 (T2 L174), §4.4 (T2 L317)
measured_by: registry scope (Q-01) · census header (CEN-H) · information_schema over the 66 L0 tables (Q-09) · build_runs / build_run_assets (Q-10)
traces_to:   0.3
```

L0 serves every chart; it is built and read once. Measured: all 40 registry rows are `scope = global` (Q-01); the census's
chart-scoped `count_sql` count is 0 (CEN-H `chart_scoped_count_sql`); none of the 66 tables named by the 40 assets'
`count_sql` or `target_table` has a `chart_id`, `subject_id` or any column matching `chart`/`subject` (Q-09) — so no structural
column of that kind exists (a measured fact; whether it is the detector for "private observations must never become global doctrine" is TG-L0-017, §2.1). Build scope: of 734 recorded
`build_runs`, none has a null `chart_id`; 61 have `scope = 'global'` and **none of those touched an L0 asset** (CEN-H
`global_runs` 61, `global_runs_touching_layer` 0); L0 assets appear in 118 `build_run_assets` rows across 51 runs
(2026-07-04 → 2026-09-07), every one a chart-carrying `asset_set` (50) or `layer` (1) run — 50 against 482012f1, 1
against 1c826d5a (Q-10). **[TIER GAP: TG-L0-009]** no tier defines what an L0 build's scope or generation is; these are
the facts a definition would have to reconcile. The muhūrta lattice is global but not location-free (T2 §4.4, L317).

#### 1.1.2 · The other charts with L1+ rows `[NEW]`

```
inherits:    Data plane §3.3 (T2 L174), §11 (T2 L566–568)
measured_by: read-only per-chart counts over the 86 L1–L5 tables the census names as targets or count tables (Q-13); COUNTS ONLY — no row content of any chart but 482012f1 was read
traces_to:   0.3 (hands onward)
```

The canonical chart is `482012f1-710e-4a25-994a-93821f5871aa` (N-12 decided: canonical only; the other charts are served
from L0 inputs as they stood when built, disclosed per N-33 — campaign rulings, not tier clauses). Two other charts hold L1+
rows and so are affected by any L0 change: **`1c826d5a-41cb-4450-b4dc-59d440e5f75a`** and
**`cb73cd3d-9eba-4220-9902-0de91566e980`** (identified by `chart_facts.chart_id`; the `charts` table is not readable to the
reader login, so no owner or name is recorded). Rows in the 86 tables (82 carry a `chart_id` column; 4 do not —
fact_category_ownership, mimamsa_negative_controls, mimamsa_preferences, mimamsa_signal_families — and are omitted; each of
the 86 tables is assigned to the one layer whose assets name it, none is named by two):

| layer | 482012f1 (canonical, for scale) | 1c826d5a | cb73cd3d |
|---|---:|---:|---:|
| L1 Gaṇita (12 tables) | 636,161 | 620,210 | 652,228 |
| L2 Bodha (20) | 159,884 | 108,300 | 108,003 |
| L3 Kāla (17) | 8,733,480 | 2,934,310 | 150,032 |
| L4 Phala (10) | 1,036 | 1,673 | 0 |
| L5 Mīmāṃsā (23 with a chart column) | 114,560 | 112,667 | 0 |
| **all five** | **9,645,121** | **3,777,160** | **910,263** |
| tables with ≥1 row (of the 82 countable) | 69 | 66 | 37 |

Headline tables (rows per chart, canonical / 1c826d5a / cb73cd3d): `chart_facts` 143,299 / 139,717 / 138,080 ·
`chart_dashas` 483,870 / 471,767 / 505,348 · `bodha_msr_signals` 50,678 / 50,171 / 49,875 · `kala_field` 8,570,075 /
2,412,882 / 0 · `mimamsa_predictions` 139 / 56 / 0. `cb73cd3d` has no L4 or L5 rows; `1c826d5a` has both. The full
per-table counts are Appendix D. These are the populations an L0 wave's impact statement addresses; whether they are
*stale* against a given L0 change is undecidable today because no L0 generation is recorded on them (TG-L0-009).

#### 1.1.3 · `bg_vidhi_floors` — the one DRAFT asset `[RE-MEASURED = v3.0]`

```
inherits:    Data plane §13.3 item 2 (inventory incl. status)
measured_by: registry catalog_status and english_description (Q-01, Q-08) · migration 642 (F-02, Q-12) · census cells (CEN-M)
traces_to:   0.3
```

`bg_vidhi_floors` is the only `catalog_status = DRAFT` among the 40 (Q-01). Its target set is `vidhi_intent_floors` (14) +
`vidhi_floor_items` (409) = **423** rows, floor 423 (Q-08); its dependency `bg_vidhi_primitives` (60) is CURRENT. The
registry description itself states why (migration 642, applied 2026-09-04): DRAFT is intentional — 12 of 14 intent floors
are writer-tagged MANDATORY, `education_deepdive` and `progeny_deepdive` remain CANDIDATE (VIDHI-PURNATA P-2, not yet
ratified); flipping to CURRENT "would be fabricating settledness two floors don't have". The census reads the asset like
its CURRENT siblings: Build.history PARTIAL (1 error, 1 abort on record), every other applicable cell PASS or N/A. The seed
literal for `bg_vidhi_primitives` is DRAFT while live is CURRENT (F-01). **[TIER GAP: TG-L0-024]** no tier says whether a
DRAFT asset can be ELEVATED or what DRAFT blocks; the layer-level reading here is that DRAFT is an honest authority limit
(disposition Q, §3.2), not a defect.

#### 1.1.4 · The Gochara L0 inputs — flagged R9 `[NEW]`

```
inherits:    Data plane §3.2 (T2 L146–166), §7 (DP contracts) — and, outside the tiers, charter R9
measured_by: registry (Q-01, Q-02), census (CEN-M, CEN-R), file-reference counts (F-07), migrations (F-02)
traces_to:   0.3 (hands onward)
```

Charter **R9** (`SUVARNA_AUTONOMY_CHARTER_v1_0.md` §4, L130–131): a change to the Gochara L0 inputs
(`bg_gochara_arcs`, `bg_gochara_citation_resolution`) that alters what Pravāha consumes is analysed and fixed, but the
rebuild waits for a Strategic Suvarṇa decision after notification to Pravāha. Nothing here changes either asset; this is
their measured state.

| | `bg_gochara_arcs` | `bg_gochara_citation_resolution` |
|---|---|---|
| rows / floor | 33,933 / 33,933 live (seed literal 34,553; migrations 599 and 854 modify its registry row, F-02) | 14 / 14 |
| writer | yes, registered (delete-then-insert, `bg_gochara_arcs.py` L149, L156) | **none** — registry `has_writer = false`, no `@register`, listed in the pin's non-writer assets |
| depends on | `bg_ephemeris` | `bg_texts` |
| declared dependents (registry) | **0** (blocking radius 0 / 0) | **0** (0 / 0) |
| code that reads it (F-07b: files of any type under platform/python-sidecar, platform/src, platform-mcp/src whose path does not contain `test`, excluding node_modules; substring match) | `ka_gochara.py`, `services/w2g/{db_source,arcs,equivalence_report,materialize}.py`, `services/ka_gochara/service.py`, the pin/census generated files | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` (a served module: 5 of 9 built columns selected), `platform/src/app/api/mcp/db/query/route.ts`, `nirmana-elevation/definitions.ts` |
| build record | latest run complete (`skip_no_delta`, 2026-09-06); 1 error (2026-09-04, post-write integrity check false) and 1 abort on record; provenance receipt `proven` (Q-11) | **no build record, no `asset_throughput` row, no provenance receipt** (Q-10, Q-11); `Build.completion` FAIL "live=14 and no build record at all" |
| served | 0 capability modules (Dens N/A; census reach width 0.0) | 0 modules in the L0 directory (Dens N/A) but 1 platform-mcp module reads it (census reach: 5 of 9 built columns selected); `density_contract` not declared |
| citations | `Ldgr.source_presence`: no reading (no recognised citation column) | `source_citation` populated 14/14 |

Two findings, *no action*: **(1)** the registry declares no dependent for either R9 asset, yet code reads both — the
declared edges understate exactly the consumption R9 protects (§1.4); **(2)** the L0 assets the registry *does* declare
as inputs of the Gochara-family L3 assets are `bg_ephemeris`, `bg_transit_rules`, `bg_sarvatobhadra_grid`,
`bg_vedha_malefic_scale` and `bg_phaladeepika_latta` (ka_gochara ← bg_ephemeris, bg_transit_rules; ka_vedha_gochara ←
bg_ephemeris, bg_transit_rules, bg_sarvatobhadra_grid, bg_vedha_malefic_scale, bg_phaladeepika_latta; ka_gochara_resonance ←
bg_transit_rules; Q-02) — none of which R9's text names. R9's scope is a charter matter; the instance records that its two
named assets and the family's declared L0 inputs are different sets. Any L0 wave touching them notifies Pravāha first.

#### 1.1.5 · Registry anomaly: 36 registered writer ids against 34 `has_writer = true` `[RE-MEASURED = v3.0; one item NEW]`

```
inherits:    Data plane §3.3 (frozen WriterBase contract, T2 L172); template §5.2 Build gate
measured_by: census header (CEN-H registered_ids 36, registry_has_writer 34, phantom_registered []) · @register census over the 32 bg_*.py writer files (F-04) · Build.registered / Build.exercised cells (CEN-M) · build_run_assets (Q-10) · the pin (F-03)
traces_to:   0.3
```

The 32 writer files register **36** `bg_*` ids (F-04): `bg_medical_mappings.py` registers three
(`bg_sign_medical`, `bg_nakshatra_medical`, `bg_medical_mappings`), `bg_transit_rules.py` two (`bg_transit_rules`,
`bg_transit_engine`), `bg_phaladeepika_vedha.py` two (`bg_phaladeepika_latta`, `bg_vedha_malefic_scale`); no phantom
(every registered id is a registry row). The registry says 34 have a writer. The two ids that differ:
`bg_nakshatra_medical` and `bg_transit_engine` are registered in code while the registry says `has_writer = false` —
`Build.registered` FAIL ×2 (CEN-M). The pin agrees with the code (36 writers, 4 non-writer assets, F-03). The four
non-writer assets the pin and the registry agree on are bg_ephemeris_engine, bg_gochara_citation_resolution,
bg_panchanga, bg_sarvatobhadra_grid.

**`bg_sign_medical` — a writer the orchestrator never ran** `[NEW as a finding]`: it is registered with a writer and the
registry says `has_writer = true`, yet **no `build_run_assets` row exists for it** (`Build.exercised` FAIL, CEN-M;
`never_exercised_with_writer: ["bg_sign_medical"]`, CEN-H; Q-10). Its 12 rows exist and its `asset_throughput` row reads
`lit` (last built 2026-08-07, `rows_written` null). Its sibling registrations ride `bg_medical_mappings.py`, which the
orchestrator did run three times (2026-09-04, Q-10) — so the 12 rows plausibly came from a sibling's run, but that is an
inference; the census records only that the asset itself was never dispatched. Five L0 assets in all have never been
dispatched: bg_sign_medical, bg_nakshatra_medical, bg_transit_engine, bg_sarvatobhadra_grid,
bg_gochara_citation_resolution (CEN-M `Build.exercised`: 1 FAIL + 4 N/A "never run, and it has no writer — consistent") —
unchanged from R84's "5/40". **Finding, no action.** T4's `kind` and Producer vocabulary already has a place for an id that rides
a sibling's writer (`rider (producer_covered)`, T4 L74; "or the asset it rides on", T4 L129); what remains is the
registry-versus-code contradiction for two of the three ids, a layer finding (C-12). v3.1 recorded this as TG-L0-028; it is
withdrawn as a tier gap at rev1.

### 1.2 · Individual contribution — fidelity, not ablation

```
inherits:    Product §14.1, Data plane §12.2 (reference-layer carve-out, T2 L601–607), template §1.2 reference-layer clause
measured_by: per asset, the four fidelity dimensions T3 §1.2 names (identity correct · source present and qualified · method boundary stated · provenance carried) — by the named query at 2026-09-30; NOT MEASURED where no query exists. The census contributes one instrument (Ldgr.source_presence) and one identity instrument (Vocab.identity).
traces_to:   0.1
```

**[TIER GAP: TG-L0-012]** no tier defines a detector or scale for the four dimensions, or maps them to the carriage checks
of §2.7. What follows is the measurement that exists.

| asset | fidelity | measured result |
|---|---|---|
| bg_ontology | **identity PASS under the declared key · alias FAIL (one class)** `[RE-MEASURED = v3.0]` | 741 rows, 741 distinct `(entity_class, canonical_id)` — constraint `brahma_ontology_canonical_unique` — 730 distinct `canonical_id` alone (11 ids appear in two classes by design: a school and a concept, a doṣa and a yoga). Alias sets: 15 of 16 classes complete; **`dosha` 79 of 79 empty** (Q-03; CEN-M `Vocab.alias`). The across-classes detector in T2 §4.1 rule 1 as originally worded would have reported FAIL on this data; T2 was amended 2026-09-26 (R03, DONE) to the declared-key detector. Residual defect: consumers that resolve on `canonical_id` alone. |
| bg_rules | **source present PASS · linkage WEAK** `[RE-MEASURED = v3.0]` | 3,002 rules, all with `verse_ref`, across 14 texts; **17** carry `yoga_canonical_id` (17 resolve to `brahma_yoga_catalog`), 0 carry `dasha_system_id`; `confidence` has 3 distinct values and equals `quality_score` on 3,002 of 3,002 rows (Q-06). The census's `Ldgr.source_presence` has no reading for this asset (its citation column is `verse_ref`). |
| bg_doshas | **PARTIAL (qualification)** `[RE-MEASURED = v3.0]` | 79 rows, all with a citation; **53 cite the placeholder `classical_tradition`** (Q-04). The census's `Ldgr.source_presence` reads PASS 79/79 — a *presence* reading, not qualification. |
| bg_yogas | **PARTIAL (qualification) `[NEW]`** | 233 rows, all with a citation; **1** cites `classical_tradition` (Q-04). |
| bg_remedies | **PARTIAL (provenance)** `[CHANGED — CH-05]` | 341 of 341 carry `source_canonical_id`; **289 do not resolve** to a `text` row; 204 resolve case-insensitively; **85 do not** (`classical_tradition` ×80, 5 others) (Q-05). |
| bg_ephemeris | **grid complete; vocabulary mismatch** `[RE-MEASURED = v3.0, pilot 3]` | 825,084 rows = 91,676 days × 9 bodies, 1900-01-01…2150-12-31, no missing cell; `body` is stored capitalised (`Jupiter`) against the ontology's lowercase `jupiter` (Q-14). |
| bg_sarvatobhadra_grid | **PASS by abstention** `[CARRIED]` | 0 rows by ruling (ADJUDICATION-11; registry `target_floor` 0); `Vocab.identity` and `Complete.depth` read NO_DETECTOR (empty table); it has a downstream dependent (ka_vedha_gochara) and a proven provenance receipt for the empty state (migration 912; Q-11). |
| the other 33 | **NOT MEASURED** for fidelity | `Ldgr.source_presence` reads PASS on 24 of the 40 assets (citation column populated N/N: e.g. bg_ontology 741/741, bg_reference 11/11, bg_texts 10,651/10,651, bg_ephemeris 825,084/825,084) and has no reading for 16 (CEN-M). Presence is not "qualified". No census criterion exists for method boundary or authenticity. |

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4, §7, §3.5 (T2 L207–241)
measured_by: seam by seam — the join each seam depends on, with its key uniqueness checked first; no ablation harness exists, so no fraction is computed
traces_to:   0.2
```

**[TIER GAP: TG-L0-013]** T2 §3.5 names four plane-level seams; no tier names L0's own. The three joins below are v3.0's
choice `[CARRIED]`, re-measured.

| seam | measured | state |
|---|---|---|
| **A · catalogue → identity** — every yoga, doṣa and daśā-system id resolves to one ontology row | 233 yoga + 79 doṣa + 20 daśā-system catalogue rows against 741 ontology rows keyed `UNIQUE (entity_class, canonical_id)` — unique under the declared key, 730 distinct on `canonical_id` alone (Q-03, Q-04) | **REAL, and UNDECLARED** `[RE-MEASURED = v3.0]`. Each catalogue seeds its own identity rows into the ontology; none references it by a declared contract. A consumer joining on `canonical_id` alone over-counts for 11 ids. |
| **B · rules → concepts** | 17 of 3,002 rules carry a concept id (Q-06) | **EFFECTIVELY ABSENT** (0.6%) `[RE-MEASURED = v3.0]` |
| **C · remedies → source identity** | 52 of 341 resolve exactly; 256 with case folded (Q-05) | **UNNORMALISED** `[CHANGED — CH-05]` |

**Synergistic fraction: absent instrument.** No harness exists (T3 L249–251 forbids a fraction), so none is recorded; the
seam readings above are the value of this term. Building the harness is packet W-L0-7 `[CARRIED]`.

### 1.4 · Cross-layer handoff — what it produces downstream

```
inherits:    Data plane §11 (six evidence states, T2 L572), §7 (DP01, DP02, DP07 produced)
measured_by: registry depends_on (Q-02) for declared edges · file-reference counts over platform/python-sidecar, platform/src, platform-mcp/src (F-07) for actual reads · the L0 served surface by directory listing and grep (F-05) · census reach and blocking_radius (CEN-R)
traces_to:   0.3 (hands onward)
```

The registry understates the term (unchanged conclusion). **Declared:** 34 cross-layer edges onto 18 of the 40 L0 assets, 26
of 40 with any active dependent, 14 with none `[CHANGED — CH-03]`. **Actual:** the same tables are read in dozens of files
each — word-match counts over all files under the three roots, tests and generated snapshots included (the population
that reproduces v3.0): `ephemeris_daily` 71, `bg_transit_rules` 68, `classical_text_chunks` 59, `brahma_remedy_corpus` 48,
`brahma_dosha_catalog` 32, `brahma_ontology` 30, `bg_muhurta_lattice` 30, `sutravali_rules` 29, `brahma_yoga_catalog` 27;
restricted to `.py/.ts/.tsx` non-test files the same tables read 44, 34, 38, 21, 12, 17, 14, 13, 13 (F-07)
`[RE-MEASURED = v3.0]`. The R9 pair (§1.1.4) shows the sharpest gap: 0 declared dependents, several code readers. This is
why no L0 asset may be dispositioned R on registry evidence alone.

**Served state** (F-05, CEN-R): the L0 capability directory holds 47 non-test `.ts` files (46 excluding `index.ts`) and 3 test
entries; 39 files declare a `CapabilityDescriptor` (the pattern is stated in F-05); **0 declare a `density_contract`** `[RE-MEASURED = v3.0]` — against, on the same non-test basis (paths containing `test` excluded, recomputed at rev1, F-05), L1 22 files, L2 7, L4 1, L5 15, L3 0 (v3.1 compared L0's non-test count with test-inclusive counts for the others, L1 25, L2 9, L4 2; those are not comparable). The census reads `Dens.served` FAIL for 23 assets, NO_DETECTOR for 1
(bg_dignity_reference — its modules mention it only in comments) and N/A for 16; 26 assets are read by ≥1 module (table
basis) through 31 distinct modules; mean column width selected 0.509 over 37 assets, 11 at 0, 252 dark columns
`[NEW]`. **[TIER GAP: TG-L0-016]** no consumer-side probe exists for the six evidence states.

Evidence states reached (six-state scale): `source-present` and `method-qualified` for all 40 *as far as a populated
citation column shows* (qualification is weaker, §1.2); `consumed` demonstrable for the nine tables above; `traceably
transformed` and `served` demonstrable through the modules; **`value evaluated` reached by none** — no ablation has been run.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

> **L0 value = Σ fidelity + Σ synergistic + Σ cross-layer handoff**

- **Fidelity:** 7 assets characterised — bg_ontology (identity PASS, alias FAIL), bg_rules (source present, linkage weak),
  bg_doshas, bg_yogas and bg_remedies (PARTIAL: placeholder or unresolved citations), bg_ephemeris (grid complete,
  vocabulary mismatched), bg_sarvatobhadra_grid (PASS by abstention); **33 not measured** beyond a presence reading.
- **Synergistic:** one seam real but undeclared, two effectively absent or unnormalised. No fraction — absent instrument.
- **Cross-layer:** real and dominant, unquantified; nothing has reached `value evaluated`.
- **Shortfall against 0.2:** the objective is that every later distinction be *attributable*. Today a claim can be traced to
  an L0 row, but that row's id may resolve to two things (seam A), its rule may have no concept link (seam B), and its
  citation may name a placeholder (53 doṣas, 1 yoga) or fail to resolve (289 remedy ids). **The delta is attribution that
  breaks at the join**, not missing content — unchanged from v3.0.

Per the reference-layer rule, no asset is a candidate for **R** on a zero score: retirement requires failed fidelity, never a
missing reader. **[TIER GAP: TG-L0-012]** "failed fidelity" has no detector, so the rule cannot currently fire either way.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

Section order follows the template file as written (2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 2.5) `[CARRIED]`; the template places 2.5
last and defines no corrections section (**TG-L0-021**, R08).

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (L0 row, T1 L422), §13; Data plane §9.2 (T2 L493–517)
measured_by: the detector each rule needs; none is supplied by any tier for L0 (TG-L0-017, TG-L0-006), so the table reports measured facts and gives NO verdict
traces_to:   0.2
```

Rev1: v3.1 graded three of these rows PASS using a detector the draft chose itself and a fourth PARTIAL on the draft's own three-part test.
Those verdicts are removed. A verdict needs a detector and an owner a tier supplies (T3 §2.1: "A rule with no detector is a wish"); until then
the instance states what was measured and stops, as the L1 instance does.

| rule | source | measured fact (no verdict) | detector |
|---|---|---|---|
| **Private observations must never become global doctrine or reference truth** | T1 §8.1, L0 row, verbatim | 0 of 66 tables named by the 40 assets' `count_sql` or target carry `chart_id`, `subject_id` or any column matching `chart`/`subject` (Q-09) `[RE-MEASURED = v3.0, population widened from 40 assets to 66 tables]` | **none supplied — TIER GAP: TG-L0-017**; the column test is the draft's own choice and is not offered as the detector |
| **Switch ON** — L0 may supply shared event vocabulary, precision and provenance definitions | T2 §9.2, ON row (L500: "L0 event vocabulary") | `brahma_event_ontology` (27 rows) and `brahma_activity_ontology` (12 rows; together bg_ghatana's 39) hold vocabulary; neither has a per-subject column (Q-09, Q-15) | none supplied — TG-L0-006 (narrowed to the detector), TG-L0-017 |
| **Switch OFF** — nothing derived from life events, anywhere | T2 §9.2, OFF row (L501) and storage separation (L510–512) | the same tables carry no per-subject column (Q-09); v3.0 argued OFF is therefore a selection, which is an argument, not a measurement | none supplied — TG-L0-006 (narrowed), TG-L0-017 |
| **No invented computation, source, detector, confidence or score** | T1 §13, L566 | 53 doṣa rows and 1 yoga row cite the placeholder `classical_tradition` (Q-04) and 80 remedy rows cite it as `source_canonical_id` (Q-05); the abstaining grid `bg_sarvatobhadra_grid` holds 0 rows by ruling; `assert_legal()` on the verification vocabulary is `[CARRIED, not re-measured]` | none supplied — TG-L0-017 |
| **A status is earned or null** (CLAUDE.md §N.8 — **outside the tiers**: it is not a T1 §8.1/§13 or T2 §9.2 rule, and is kept because the project's own doctrine names it) | CLAUDE.md §N.8 | 38/40 `count_sql`, 37/40 integrity SQL (Q-01) `[RE-MEASURED = v3.0]`; the two services and the abstaining grid lack integrity, and their absence is by design. `Earn.build_record` is NO_DETECTOR on 40/40 (instrument absent, migration 1094; CEN-M); `asset_throughput.state = 'lit'` carries no detector (§1.1 finding 5) | `Earn.build_record` (census) — NO_DETECTOR |

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (T2 L178–205)
measured_by: presentation-parity test (T2 §12.2) — NOT RUN: no harness found
traces_to:   0.1
```

**[TIER GAP: TG-L0-005]** T2 §3.4 assigns no rows to layers; v3.0 chose the three L0 carries `[CARRIED]`.

| §3.4 row | L0's part | carried? |
|---|---|---|
| method and school a finding rests on, and where authorities disagree | DP02: school/tradition, unresolved alternatives, the witness behind each variant | **PARTIAL** — `classical_attributions` holds 721 attributions and `sutravali_rules` no `school` column; no detector proves a disagreement is carried rather than flattened |
| conventions in force — ayanāṃśa, node, house system, varga construction | DP01: the released convention set | carried as data (`reference_*`, `brahma_formula_constants` 17); **no release id exists** (TG-L0-008) |
| one identity rendering two ways (*Śukra* / Venus) | the closed alias set per T2 §4.1 | **PARTIAL** — 15 of 16 classes complete; doṣa has no alias set (79/79, CEN-M) |

Parity test state: **NOT RUN** (TG-L0-022). Recorded as an unmet acceptance test in §5.4, not as a pass.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01–DP17), §7.1 (common envelope, T2 L412–416)
measured_by: fields present in the producer table and read at the consumer, both ends — the consumer end is NOT MEASURED (TG-L0-016)
traces_to:   0.3
```

**Produced** `[CHANGED — CH-12]` **[TIER GAP: TG-L0-004]**:

| contract | consumer | fields | grain | state |
|---|---|---|---|---|
| **DP01 identity/release** | every layer, adapter and writer | canonical id, alias set, entity class, unit, release | one row per thing | live; identity key `(entity_class, canonical_id)` unique; **no release id** (TG-L0-008); alias set missing for doṣa |
| **DP02 rule qualification** | L1 formation, L2 interpretation, L3 activation, investigator | rule clauses, method, school, prerequisites and exceptions to be tested, unresolved alternatives, executable scope | one row per rule | live for clauses and verse; school/disagreement PARTIAL; **executable scope not a column** (`sutravali_rules` columns, Q-06) |
| **DP05 (L0's half)** | L2 via L1 | the catalogue definition formation is tested against | one row per configuration definition | live (233 yoga, 79 doṣa; `bhanga_rules_jsonb`, `partial_formation_threshold`, `strength_formula_ref`, `result_class` never populated on `brahma_yoga_catalog`, CEN-M `Complete.depth`) |
| **DP07 primitives** `[NEW]` | L3 temporal integrators | ephemeris (`ephemeris_daily`), sky calendar, muhūrta lattice, gochara arcs — actual boundaries, geometry, reference frame | per body×day / per event / per factor×interval / per arc | live; consumers declared: bg_ephemeris ← 5 ka_* assets + bg_gochara_arcs (Q-02); the lattice is global but reference-location bound (T2 L317) |
| **DP10 (about itself; T2 L456–457) / DP16 (T2 L436, no layer named in its producer column)** `[NEW]` | registry / investigator; dependent products | capability metadata, honest gaps; stale marking | — | DP10: 0 of the L0 modules declare a `density_contract`; DP16: no L0 generation to mark (TG-L0-009) |

**Consumed:** none from any layer — 0 of 40 assets declare a non-`bg_*` dependency (Q-02) `[RE-MEASURED = v3.0]`. L0's inputs
are external (corpus, ephemeris, native rulings), which is why its Part 2 has no consumed-contract table with declared uses.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3, Data plane §5 (T2 L325–339)
measured_by: presence counts only (Q-03, CEN-R). The five states per obligation (applied / inapplicable-with-reason / unavailable / unqualified / unresolved) are NOT assigned: no tier assigns an obligation to L0 or declares its universe (TG-L0-007)
traces_to:   0.1
```

Rev1: v3.1 gave each row one of the five states using a "meaning half versus chart half" rule of its own. Assigning a state without a tier
clause for ownership and a declared universe would be an invented result, so the state column is removed and the presence figures stay.
The "L0's half" column is the draft's own halving rule `[CARRIED]`, not a tier statement; the census width is NOT_GENERIC on 40/40 (no declared universe).

| data plane §5 obligation | L0's half (the draft's own halving rule) | measured presence (state: **not assigned**, TG-L0-007) |
|---|---|---|
| Graha contextual roles | role vocabulary: natural, functional, lordship, kāraka kept distinct | 77 kāraka + 11 planet ontology rows |
| Rāśi / bhāva / lord / kāraka | reference frames and significator vocabulary | 12 sign + 12 house rows |
| Bala / dignity / avasthā | dignity reference and units | 151 cockpit rows over five tables (bg_dignity_reference) |
| Sambandha | typed relation vocabulary, aspect school and orb | 13 aspect-type rows |
| Bhāvat Bhāvam | the derived-house doctrine and its limits | concept `bhavat_bhavam` resolves in the ontology; 0 of 3,002 rules mention it (Q-16) `[RE-MEASURED = v3.0]` |
| Varga and reference perspectives | varga method identity and domain | 30 varga rows |
| Yoga / doṣa / bhaṅga | catalogue definitions, participants, cancellation conditions | definitions present; 53 of 79 doṣa and 1 of 233 yoga rows cite a placeholder `[CHANGED — CH-06]` |
| Nakshatra / KP | pada relationships, sub-lord division | 2,857 nakshatra-family + 249 KP rows |
| Present interval (P24) | none, by the draft's halving rule: the interval set is L3's and its expression L4's | — |
| Kāla | transit rule vocabulary, arcs, calendar substrate | 76 + 33,933 + 31,081 rows |
| Praśna / Muhūrta / calendar | method eligibility and constraint vocabulary | lattice 173,219; praśna methods 41; the lattice is reference-location bound |
| Āyurdāya and constitution | method and school identity, inputs, cancellations | no method concept, 0 rules, 0 tagged chunks (Q-16) `[CHANGED — CH-07]` |
| Voluntary practice and wider tradition | attributed practice, scope, burden, evidence class | 341 rows; provenance PARTIAL (289 unresolved ids) |

### 2.6 · Vocabulary conformance — **L0 owns the set**

```
inherits:    Data plane §4.1 (six rules, each with a detector, T2 L245–289)
measured_by: per rule — uniqueness and alias census over brahma_ontology (Q-03) · independent-map candidates (CEN-H, F-08, F-09) · parity-test file listing (F-10) · interface-parameter census NOT RUN
traces_to:   0.2
```

For L0 the section inverts: it does not conform to the vocabulary, it *is* the vocabulary (T3 L326–328).

| §4.1 rule | state | measured |
|---|---|---|
| 1 · one canonical id, one closed alias set per thing | **identity PASS under the declared key · alias FAIL** `[RE-MEASURED = v3.0]` | 741 rows / 741 composite keys / 730 `canonical_id`; `brahma_ontology_canonical_unique`; `dosha` 79/79 empty alias sets (Q-03; CEN-M `Vocab.identity` PASS on 36 of 40, NO_DETECTOR on bg_sarvatobhadra_grid (empty), no reading on 3 (the two services and bg_prashna_rules)) |
| 2 · the set is the only permitted surface; an unlisted name is raised | **PARTIAL** `[CARRIED]` | `resolve_entity` resolves by name and synonym; for the 11 duplicated ids it returns two rows (v3.0 pilot 1); not re-run |
| 3 · resolution one-directional, normalisation declared once | **FAIL** `[CHANGED — CH-05]` | remedy `source_canonical_id`s: 52 exact, +204 case-only, 85 unresolvable even case-folded; `ephemeris_daily.body` capitalised against lowercase ontology ids (Q-05, Q-14); normalisation is not declared at the authority. **[TIER GAP: TG-L0-008]** no release carries it. |
| 4 · code-side snapshots generated, pinned, parity-tested | **PARTIAL** | 10 vocabulary/parity test files at the top of `python-sidecar/tests` (F-10) `[RE-MEASURED = v3.0]`; whether every snapshot has one is **NOT MEASURED** (no snapshot inventory exists — TG-L0-011) |
| 5 · external inputs typed to the set | **NOT MEASURED** | the per-parameter census was not run |
| 6 · independent maps counted, permitted count one per class | **NO DETECTOR** `[CHANGED — CH-08]` | inspector heuristic 32 files (CEN-H) vs v3.0's 6; neither is per-class (TG-L0-011) |

Sixteen classes confirmed and exactly the sixteen T2 §4.1 names (Q-03): planet 11 · sign 12 · house 12 · nakshatra 27 ·
varga 30 · karaka 77 · aspect_type 13 · upagraha 11 · yoga 233 · dosha 79 · dasha_system 20 · domain 45 · concept 136 ·
remedy_type 12 · text 15 · school 8 `[RE-MEASURED = v3.0]`. **The authority's releases: none exist** — the ontology has no
release or version column (Q-09) **[TIER GAP: TG-L0-008]**.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11 (L0 source-and-domain fidelity), Data plane §12.2 (T2 L611–613), §4.3, §5
measured_by: the three checks below, per owned obligation; PASS / FAIL / PARTIAL / NO DETECTOR
traces_to:   0.1
```

Carriage is L0's half of the question; the doctrinal verdict is formed above the plane (ruling 11). **[TIER GAP: TG-L0-018]**
no tier assigns a–c to assets; CEN-M `Carr.detector` reads NO_DETECTOR on 40/40.

| check | applies to (v3.0 assignment, `[CARRIED]`) | state |
|---|---|---|
| **a · source correspondence** | bg_rules (3,002), bg_yogas (233), bg_doshas (79), bg_remedies (341) | **NO DETECTOR.** Nothing compares an encoding to its cited passage. The 53 + 1 placeholder citations and 289 unresolved remedy ids are what a detector would surface first. L0's single largest gap: a corrupted copy here is invisible at every later layer. |
| **b · witness carriage** | bg_concordance (721), bg_rules | **PARTIAL.** Attributions are stored; no detector proves a disagreement is carried rather than settled. |
| **c · independent re-derivation** | bg_ephemeris, bg_sky_calendar, bg_muhurta_lattice, bg_gochara_arcs, bg_cohort | **NO DETECTOR at L0.** The two-pass verification that exists lives on L1 `chart_facts`. |

Three of three checks are gaps; packets W-L0-3 and W-L0-4 close a and c `[CARRIED]`.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological read of live depends_on over the 40 bg_* rows (Q-02); cycle check (depth computed without recursion failure); cross-layer gate state (F-03)
traces_to:   0.3
```

- **24 roots** (depth 0), **16 with intra-L0 edges** (25 edges), **0 with edges outside L0** `[RE-MEASURED = v3.0]`. **No cycles.**
  `[CHANGED — CH-02]` depth is four levels, not two:
  - depth 0 (24): bg_class_priors, bg_dignity_reference, bg_ephemeris, bg_ephemeris_engine, bg_formula_constants, bg_ghatana, bg_kota_chakra_rings, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra, bg_nakshatra_medical, bg_ontology, bg_panchanga, bg_phaladeepika_latta, bg_prashna_rules, bg_sarvatobhadra_grid, bg_sign_medical, bg_sky_calendar, bg_texts, bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_vedha_malefic_scale, bg_vidhi_primitives
  - depth 1 (11): bg_class_lifetime_counts, bg_cohort, bg_dasha_systems, bg_doshas, bg_gochara_arcs, bg_gochara_citation_resolution, bg_kp_sublord_division, bg_reference, bg_remedies, bg_vidhi_floors, bg_yogas
  - depth 2 (4): bg_compendium_index, bg_parihara_rules, bg_rules, bg_text_index
  - depth 3 (1): bg_concordance
- **Intra-L0 edges** (asset ← its dependencies, Q-02):
  - `bg_class_lifetime_counts` ← bg_ghatana
  - `bg_cohort` ← bg_ephemeris_engine
  - `bg_compendium_index` ← bg_reference, bg_texts
  - `bg_concordance` ← bg_reference, bg_rules, bg_text_index, bg_texts
  - `bg_dasha_systems` ← bg_ontology
  - `bg_doshas` ← bg_ontology
  - `bg_gochara_arcs` ← bg_ephemeris
  - `bg_gochara_citation_resolution` ← bg_texts
  - `bg_kp_sublord_division` ← bg_nakshatra
  - `bg_parihara_rules` ← bg_doshas, bg_texts
  - `bg_reference` ← bg_ontology
  - `bg_remedies` ← bg_texts
  - `bg_rules` ← bg_dasha_systems, bg_texts, bg_yogas
  - `bg_text_index` ← bg_reference, bg_texts
  - `bg_vidhi_floors` ← bg_vidhi_primitives
  - `bg_yogas` ← bg_ontology, bg_texts
- **Edge type:** no source records it (TG-L0-030); v3.0's "every outbound edge is edge 1 or edge 3" is `[CARRIED]`.
  L0 has no computational edge *inbound*, which is what makes it rebuildable without any chart.
- **Cross-layer gate state / frozen definition revision.** **[TIER GAP: TG-L0-026]** T3 names `egate.sql` scoped to "the
  CURRENT frozen definition revision" without defining it for L0. The pin file carries `definition_bindings.L0`
  (`membership_sha256` e136c56d…139bbd, `snapshot_commit` 5142109f…, F-03) — a candidate the tiers do not name. 0 of 40
  L0 assets carry a certification record (F-06), so no gate has been evaluated under any revision; nothing to carry or
  invalidate.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised
traces_to:   0.2
```

### 3.1 · Per obligation

Ten obligations exist; L0 is scored on the one T1 §11 assigns, **Source and domain fidelity** (§0.2). T2 §13.3 item 1 forbids adding
others; the three v3.0 added on its own authority (Computational correctness, Delivery fidelity, Operational honesty) are struck at rev1.

| obligation | where L0 stands, measured | what closes the gap |
|---|---|---|
| **Source and domain fidelity** | 3,002 rules all carry a verse reference across 14 texts; 721 attributions stored. Against that: 53 doṣa + 1 yoga rows cite a placeholder, 289 remedy source ids do not resolve (85 not even case-folded), and no detector compares any encoding to its cited passage. The computed substrate T1 L500 lists under this obligation: 5 computed assets (825,084 · 173,219 · 33,933 · 31,081 · 110,000 rows), no independent re-derivation detector at L0 (§2.7 c), ephemeris grid complete (Q-14) | W-L0-3 · W-L0-4 · W-L0-5 |

Facts v3.0 filed under the struck obligations are kept where they are used, as facts and not as scores: build-status counts (38/40 `count_sql`, 37/40 integrity SQL,
1 DRAFT, `Build.completion` FAIL on 14, `lit` without a build on 4, 0 gates certified; §1.1, §5.2) and served-surface counts (46 modules, 0 declaring a density contract;
parity never run; §1.4).

### 3.2 · Per asset — disposition

`[CARRIED]` — the dispositions are v3.0's judgement; **[TIER GAP: TG-L0-019]** no rule maps census evidence to a disposition;
**[TIER GAP: TG-L0-002]** the vocabulary here is T2 §10.1's P/I/E/Q/C/H/R/U (P = "keep" in the campaign's wording). Corrected
counts `[CHANGED — CH-09]`. **No asset receives R.**

| disposition | assets | evidence |
|---|---|---|
| **P** preserve | **30** — every asset not listed below `[CARRIED]` | at or above floor except the stale parihara registry floor; integrity SQL present except the two services and the empty grid, where absence is by design (§2.1); fidelity was measured for only one of the 30, **bg_yogas**, which is PARTIAL (1 placeholder citation, §1.2) and appears under must-add in §3.3, so the P assignment for it is v3.0's judgement and is left to the A.L0 dispositions file (Track A brief §5), not settled here |
| **E** enrich/correct | **bg_ontology** (doṣa alias sets; a declared release), **bg_remedies** (normalise 289 ids), **bg_doshas** (replace 53 placeholder citations), **bg_rules** (concept linkage beyond 17/3,002; an executable-scope field) | §1.2, §1.3 |
| **Q** qualify/limit authority | **bg_sarvatobhadra_grid** — keep the abstention visible; **bg_vidhi_floors** — DRAFT is the honest authority limit until 2 floors are ratified | ADJUDICATION-11; §1.1.3 |
| **I** integrate | **bg_prashna_rules** (declare its table set), **bg_text_index** (its 361 is a distinct-tag measure sharing a table with bg_texts — one declared grain) | §1.1 findings 2–3 |
| **C** consolidation candidate | **bg_class_priors / bg_class_lifetime_counts** — two assets, one table (`brahma_class_priors`, 177 rows: 171 + 6), two partitions; trace callers first (bg_class_priors ← mi_kula; bg_class_lifetime_counts ← ka_kshetra) | §1.1 finding 3, Q-02, Q-15 |
| **H** historical / **R** retire | none | R forbidden without failed fidelity |
| **U** (annotation) | the **14** assets with no active dependent: bg_compendium_index, bg_concordance, bg_gochara_arcs, bg_gochara_citation_resolution, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra_medical, bg_parihara_rules, bg_remedies, bg_sign_medical, bg_sky_calendar, bg_transit_engine, bg_vastu_directions, bg_vidhi_floors | CEN-R; §1.4 — "no consumer" is an unmeasured state, not a verdict; two of them are the R9 pair |

Registry corrections that the census implies but the draft does not disposition (they belong to the registry, not an asset's
content): `has_writer` for bg_nakshatra_medical and bg_transit_engine; `target_floor` for bg_parihara_rules (449 → its
current 440); `bg_sign_medical` dispatch status. Recorded as Part 6 items; none is an action here.

### 3.3 · Per asset — what it must add

`[CARRIED]` from v3.0, with census additions marked.

| asset | must add |
|---|---|
| bg_ontology | an alias set for all 79 doṣa rows; the normalisation rule and a **release id/digest** declared at the authority `[NEW — TG-L0-008]`; class-aware resolution at consumers |
| bg_rules | `yoga_canonical_id` (or an equivalent concept link) beyond 17 rows; an executable-scope field (DP02) |
| bg_doshas / bg_yogas | a real citation for the 53 doṣa and 1 yoga placeholder rows, or an explicit `unattributed` state that does not read as a citation |
| bg_remedies | normalised `source_canonical_id`s; the missing texts admitted to the `text` class; `classical_tradition` made an explicit unattributed state |
| bg_prashna_rules | a declared target-table set |
| bg_concordance | a detector that a recorded disagreement is carried, not flattened |
| the 5 computed assets | a second-derivation check with a declared tolerance |
| served modules | a `density_contract` declaration where a module paginates or facets |
| all 40 | a tier-4 brief and the nine-gate map filled |

### 3.4 · Intra-layer interplay

The matrix is thin by design — 24 of 40 assets are roots and there are 25 intra-L0 edges (§2.5) — and its value sits in the
three joins named in §1.3: catalogue → identity (real, undeclared), rules → concepts (17/3,002), remedies → source identity
(52/341 exact). The boundary with L1 is the DP01/DP02 handoff, where the registry declares 5 Gaṇita edges (ga_nakshatra ←
bg_nakshatra, bg_kp_sublord_division; ga_panchanga ← bg_panchanga; ga_prashna ← bg_prashna_rules; ga_sensitive ←
bg_reference; Q-02) while code reads L0 tables in dozens of files. **This is where L0's synergistic term is found missing.**

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG (Q-02); the three-way baseline per asset (deployed / current code / target)
traces_to:   0.2
```

Identity first, because every other seam resolves through it `[CARRIED]`: (1) bg_ontology — alias sets and a release;
(2) the three seams; (3) the carriage detectors, source correspondence first; (4) the served surface — density declarations
and the first parity run; (5) briefs and gates, in the DAG order of §2.5 (depth 0 → 3). bg_concordance, the only depth-3
asset, is last of its chain.

**Three-way baseline.** `deployed` = the production figures in §1.1 (Q-01, CEN-R). `current code` = **not measured**
`[CHANGED — CH-11]`, **[TIER GAP: TG-L0-015]**: no instrument compares deployed structure with the newest live-head
writer, and v3.0's asserted zero is withdrawn; what exists is the pin's writer-digest inventory (36 writers) and the
history of the L0 pin generation (F-03). `target` = Part 3. So the delta (target − current code) is stated and the risk
(current code − deployed) is **not measured**.

### 4.2 · Work packets

`[CARRIED]` from v3.0 §4.2 — the packets are the analyst's, each closing a named delta item; packet 6's proof changes
because its cause is established. Scheduling belongs to the campaign plan, not to any tier.

| packet | closes | proof (fails if not landed) |
|---|---|---|
| **W-L0-1** fidelity census for the 33 unmeasured assets | §1.2 | a per-asset fidelity record exists for 40/40, each naming its query (needs TG-L0-012 answered first) |
| **W-L0-2** first tier-4 briefs | §4.4 (derivable briefs), §5.2 (gate map per asset) | the ledger's L0 rows carry a brief per asset; the nine-gate map filled per brief |
| **W-L0-3** source-correspondence detector | §2.7a | runs over bg_rules/bg_yogas/bg_doshas/bg_remedies and reports a non-zero mismatch count it can also report as zero |
| **W-L0-4** independent re-derivation on the computed five | §2.7c | a second derivation with a declared tolerance, and a seeded mismatch the check catches |
| **W-L0-5** identity and normalisation repair | §1.2, §1.3, §2.6 rules 1 and 3 | `count(*) = count(DISTINCT (entity_class, canonical_id))` holds; 79/79 doṣa alias sets; remedy unresolved 289 → 0 |
| **W-L0-6** the parihara −9 `[CHANGED — CH-04]` | §1.1 finding 1 | `live ≥ floor` for all 40 — by correcting the registry floor to the achieved count (CLAUDE.md §N.4, outside the tiers), since migration 703 established the rows were deliberately removed |
| **W-L0-7** L0 ablation harness (cross-layer flavour only) | §1.3, §1.5 | a seam can be broken and the served reading measured |
| **W-L0-8** density declarations and first parity run | §2.2, §1.4 | `density_contract` on every module that paginates or facets; one parity run recorded |
| **W-L0-9** rule 5 and rule 6 censuses | §2.6 | per-parameter typing census and per-class independent-map census exist and can fail (needs TG-L0-011 answered first) |

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4 (T2 L311–317), DP16 (T2 L436)
measured_by: the generation pins each consumer records; the invalidation path exercised, not described — NEITHER MEASURED
traces_to:   2.1
```

- L0 revisions classify per T2 §4.4: display/alias correction · identity mapping · semantic rule change · constant/method
  change · provenance correction · evaluation qualification change.
- An alias addition must not recompute a chart: the doṣa alias work is an alias-class change (additive). Adding a unique
  key or a release id is not (it may split one id into two: an identity-mapping change with a real invalidation path).
- **Generation.** **[TIER GAP: TG-L0-008, TG-L0-009]** there is no L0 release id; 24 of 66 L0 tables carry a
  version/build/digest-like column (Q-09) but not the ontology or the reference tables; a provenance-receipt ledger holds
  37 global L0 rows (35 proven, 2 unknown; four L0 assets have none — bg_gochara_citation_resolution, bg_nakshatra_medical,
  bg_sign_medical, bg_transit_engine; Q-11). What a consumer chart records of the L0 it consumed is **not measured**.
- **Invalidation path: described, not exercised.** No L0 change has been pushed through consumer invalidation and
  measured at the consumer.
- **Rollback** `[CARRIED, corrected]`: a re-seed. L0's convention is upsert (28 of 36 writers), so a re-seed restores rows
  but does not remove rows a shrunk source no longer produces — 7 writers delete-then-insert, 1 updates in place (CEN-M
  `Idem.pattern`); migration 703 is the recorded case of accretion. Rollback is therefore per-asset and convention-
  dependent **[TIER GAP: TG-L0-023]**. No chart is involved either way.

### 4.4 · What each asset brief inherits from this instance

```
inherits:    Product §16 (T1 L649–651); Data plane §13.3 (T2 L686)
measured_by: derivability — a brief author fills these from this instance alone
traces_to:   0.1
```

Every tier-4 L0 brief receives, without inventing it: its P-needs and V-journeys (§0.1, narrowed — `[TIER GAP: TG-L0-003]`) ·
the obligation it is scored on (§0.2; the one tier-assigned obligation, none may be added) · its correctness rules and switch behaviour
(§2.1; measured facts only, no verdict; TG-L0-006, TG-L0-017) · its presentation fields (§2.2; TG-L0-005) · its produced contracts (§2.3;
TG-L0-004) · its coverage states (§2.4; TG-L0-007) · its position in the order (§2.5, §4.1; depth listed) and baseline
(current-code half **not measured**, TG-L0-015) · its disposition and must-add (§3.2, §3.3; TG-L0-019) · its fidelity,
synergistic and cross-layer terms (§1.2–§1.4; TG-L0-012/013/016) · its role (`neither`: L0 supplies the vocabulary both
manifestation and time rest on `[CARRIED]`; TG-L0-020) · the **preserved kernel** and the **relevant Jyotish concepts with the
carriage check each invites** — the two rows this instance **cannot fill** for any asset (TG-L0-019, TG-L0-018; v3.0 C-9).
A brief that must invent any of these has found a defect in this instance; the two rows above are those defects, recorded.

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: fidelity per asset; cross-layer ablation at the consumer
traces_to:   0.2
```

For L0 the individual flavour is **fidelity** (§1.2) and only the **cross-layer** flavour of ablation runs — to verify
consumers use the knowledge correctly, never to judge whether an asset earns its place. The synergistic flavour is defined
but has no harness (W-L0-7). No ablation of any flavour has been run against L0. **[TIER GAP: TG-L0-012]** the fidelity score
has no scale.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6–N.8 (outside the tiers)
measured_by: asset_certs.jsonl for gates (F-06: 1 line, the _schema line; 0 certification records) · the census's per-criterion cells (CEN-M) rolled up as the plan's §1.4 states — informational, not certification
traces_to:   4.4
```

**Nine gates × 40 assets = 360 cells. Certified: 0.** `[RE-MEASURED = v3.0]` The gate map below is T3's (§5.2) with its
right-hand column filled for L0; the last column is the census reading under the plan §1.4 rule ("worst applicable check
wins; a gate with no registered check is NO_DETECTOR"), applied to the 40 assets' census cells — **not** a certification and not
the E6.2 rollup, which is not yet coded. Counts are assets (of 40).

| gate | section a brief author reads | what this instance supplies for L0 | census reading (assets) |
|---|---|---|---|
| **Ldgr** | §2.3 | L0 is the root: no upstream `fact_id`s (0 non-`bg_` edges); the gate reads as source presence. Sources are citations, not upstream facts. | PASS 24 · no reading 16 (TG-L0-025) — while 53 doṣa + 1 yoga rows cite a placeholder and 289 remedy ids do not resolve |
| **Idem** | §2.5, §4.1 | convention: upsert 28 · delete-then-insert 7 · update-in-place 1 · no writer 4; natural key: registry `natural_key_partition` on 21 of 40 (TG-L0-023, TG-L0-027) | PASS 35 · PARTIAL 1 (bg_text_index) · N/A 4 — a PASS does not test accretion (migration 703) |
| **Earn** | §2.4 | the emitted states that are claims: `lit`, `count_sql`, integrity SQL, floor; each needs a detector that can read false | NO_DETECTOR 40 (`Earn.build_record`; instrument absent) |
| **Null** | §2.4, §1.4 | L0's convention for an underivable value: abstention (bg_sarvatobhadra_grid, 0 rows by ruling), `target_floor` NULL for services | **no census criterion** 40 (TG-L0-025) |
| **Vocab** | §2.6 | L0 owns 16 classes, authority bg_ontology, composite key; *inverts* for L0 | PASS 35 · FAIL 1 (bg_ontology alias) · NO_DETECTOR 1 · no reading 3 |
| **Carr** | §2.7, §4.4 row 13 | per-asset (concept, check) **unassigned** (TG-L0-018); layer-level: a NO DETECTOR, b PARTIAL, c NO DETECTOR | NO_DETECTOR 40 |
| **Narr** | §2.2 | prose-bearing columns exist (`formation_text`, `effects_text`, `significations_text`, `prescription_text`, `content_en`) but no census measure says which assets emit prose (R194) | **no census criterion** 40 |
| **Dens** | §2.2, §3.4 | served: 26 of 40 assets reach ≥1 module (census reach; 31 distinct modules), while `Dens.served` counts a registry-attributed module for 23; 0 declare a `density_contract` | FAIL 23 · NO_DETECTOR 1 · N/A 16 |
| **Build** | §2.5, §1.1, §4.3 | writer and registered id, target, edges, build record: the §1.1 table and §1.1.5 | FAIL 16 · PARTIAL 11 · PASS 13 |

Gate/opportunity boundary (T3 L523–527): a passing gate writes a certification record and no ledger row; ledger rows come
only from FAIL / PARTIAL / NO_DETECTOR and inherited must-adds. Fixes go in the asset or the registry, never in the frozen
orchestrator.

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson — 90 assets' freezes evaporated when a campaign definition re-froze
measured_by: the certification record itself (F-06: none)
traces_to:   —
```

One record per (asset, criterion) in the shape `asset_certs.jsonl`'s `_schema` line uses: `asset · criterion ·
criterion_version · detector · evidence · verdict · verified_by · verified_on`, verdict ∈ {PASS | FAIL | PARTIAL |
NO_DETECTOR | N/A}. L0 has 0 records, so nothing to lose to a revision yet; this draft **may not certify** (provisional).

### 5.4 · Acceptance of this instance

```
inherits:    template §5.4 (T3 L618–668)
measured_by: the six acceptance tests, each stated met or unmet
traces_to:   —
```

| test | state |
|---|---|
| 1 · Derivability — a fresh reader derives one asset brief with zero inventions | **UNMET / untested in this pass.** v3.0's five pilots reached 12–13 of 13 rows; the two rows this instance cannot fill (preserved kernel; carriage check per asset) are recorded as TG-L0-019 and TG-L0-018. |
| 2 · Alignment — every section names its `traces_to:` | **MET** (self-check of this draft; nothing struck). |
| 3 · Measured, not inherited — every figure names a re-runnable `measured_by:` | **MET**, with the disclosed exceptions marked `[CARRIED]` / NOT MEASURED, which claim nothing. |
| 4 · Presentation parity holds for the served surface | **UNMET** — never run (TG-L0-022). |
| 5 · The gate map exists | **MET at layer level** (§5.2, right-hand column filled); **UNMET per asset** — no brief carries it. |
| 6 · Independent review, fresh context, findings folded | **UNMET.** Acceptance of the L0 instance is a Strategic Suvarṇa decision after revalidation against the re-sealed tiers (A.L0v → N-7.L0), not this session's. |

**No verdict is stamped.** 2 of 6 tests are met.

---

## Part 6 · Corrections with gates

The template's §5.2 tells an instance to "report unfillable rows in §7"; it defines no §6 or §7 (TG-L0-021, R08). This
Part is kept from v3.0. **Document-level** findings are fixed in this document (marked CH-nn above); **layer-level** findings
are recorded and become packets — none is acted on here.

| # | correction | about | gate it blocks | state at 3.1 |
|---|---|---|---|---|
| C-1 | 33 assets have no fidelity measurement beyond a presence reading (was 34) | document | the first asset brief | OPEN; needs TG-L0-012 answered |
| C-2 | §2.6 rules 4 and 5 not measured; rule 6 has no detector | document | layer certification | OPEN |
| C-3 | `bg_ontology`: doṣa alias sets empty; no release id; declared-key resolution not enforced at consumers | **layer** | W-L0-5; every Vocab gate | OPEN (identity half resolved by T2 amendment, R03) |
| C-4 | no source-correspondence detector | **layer** | every Carr gate | OPEN |
| C-5 | parihara −9 | **layer** | W-L0-6 | **cause established** (migration 703; stale floor) — correction is registry-side |
| C-6 | parity never run; invalidation path never exercised | **layer** | Dens; first consumer cutover | OPEN |
| C-7 | template defines no §6/§7; §2.5 ordered after §2.7 | **template** | the L1 instance | OPEN — R08, T3 reopen agenda (TG-L0-021) |
| C-8 | T2 §4.1 rule 1's detector | **sealed tier 2** | every Vocab gate | **DONE** — R03, T2 amended 2026-09-26 |
| C-9 | row 13 (carriage check per asset) cannot be filled | document + template | the next asset brief | OPEN — R09 (TG-L0-018) |
| C-10 | §1.1 cannot express a shared table with several producers | document + layer | the first asset certification | OPEN — R06/R10 (TG-L0-010) |
| C-11 | v3.0 statements corrected at 3.1 (CH-01 … CH-14) | document | this instance's acceptance | **fixed here** |
| C-12 | registry says `has_writer = false` for bg_nakshatra_medical and bg_transit_engine while code registers writers | **layer** (registry) | every Build gate for those two | OPEN — recorded, no action (R61 records the cascade a fix opens) |
| C-13 | `bg_sign_medical` registered with a writer the orchestrator never dispatched | **layer** | Build.exercised for that asset | OPEN — recorded, no action |
| C-14 | `bg_parihara_rules.target_floor` 449 against 440 (rows removed by migration 703) | **layer** (registry) | Count.floor for that asset | OPEN — recorded, no action |
| C-15 | `asset_throughput.state = 'lit'` on 4 assets with no `build_run_assets` row; `Build.completion` FAIL on 14 | **layer** | Build gate; §N.8 | OPEN — recorded, no action |
| C-16 | R9 pair: 0 declared dependents, code readers exist; the family's declared L0 inputs differ from R9's named set | **layer** + charter wording | any L0 wave touching them (notify Pravāha first) | OPEN — recorded, no action |

---

## Appendix A · Measurement register

Every figure above resolves here. "Population" is stated because a count without one cannot be re-run (T3 L76–86).

**Census (read from the JSON, no re-derivation).**
CEN-H — header keys of `census_L0.json` → `L0`: `n_assets` 40, `population_active` 40, `population_registry_total` 40,
`population_excluded_inactive` [], `chart_scope` 482012f1…, `chart_scoped_count_sql` 0, `global_runs` 61,
`global_runs_touching_layer` 0, `never_exercised_with_writer` [bg_sign_medical], `registered_ids` 36, `registry_has_writer`
34, `phantom_registered` [], `local_map_candidates` 32.
CEN-M — `assets[].measurements[<criterion>].{v, measured}` (21 criteria; 40 assets).
CEN-R — `assets[].{live_rows, count_sql_tables, target_table, has_writer, writer_files, catalog_status, reach, blocking_radius}`.
CEN-S — `/Users/Dev/suvarna-evidence/census/SUMMARY.md` and `census_L0.log` (cell tallies; the FAIL-by-criterion list).

**Read-only queries (suvarna_reader; default_transaction_read_only = on; 2026-09-30).**

| ID | what | population / query shape |
|---|---|---|
| Q-01 | L0 registry rows | `asset_registry WHERE layer = 'brahmagyan'` (40 rows): asset_kind, storage_type, has_writer, catalog_status, target_floor, scope, data_disposition, natural_key_partition, depends_on, count_sql, integrity_check_sql is not null; column list from `information_schema.columns` |
| Q-02 | dependency graph | `asset_registry WHERE is_active AND NOT coalesce(dead_flag,false)` (127 rows: brahmagyan 40, bodha 23, kala 21, ganita 19, mimamsa 15, phala 9): `asset_id, layer, depends_on`; edges 337; depth by recursion over `depends_on` |
| Q-03 | ontology | `brahma_ontology`: count, count(distinct (entity_class, canonical_id)), count(distinct canonical_id), per-class count and empty-`synonyms` count; `pg_constraint` for the table |
| Q-04 | catalogues | `brahma_dosha_catalog.classical_citations` (jsonb array) grouped; `::text ilike '%classical_tradition%'` on `brahma_dosha_catalog`, `brahma_yoga_catalog`, `brahma_dasha_systems`; row counts 79 / 233 / 20 |
| Q-05 | remedies | `brahma_remedy_corpus.source_canonical_id` against `brahma_ontology` `entity_class='text'`: exact, lower-cased both sides, per-value counts |
| Q-06 | rules | `sutravali_rules`: count, count(verse_ref), count(distinct text_id), count(yoga_canonical_id), count(dasha_system_id), count(distinct confidence), count(confidence = quality_score); yoga links resolving to `brahma_yoga_catalog` |
| Q-07 | corpus | `classical_text_chunks`: count 10,651, count(distinct text_id) 15 |
| Q-08 | vidhi | `vidhi_intent_floors` 14, `vidhi_floor_items` 409, `vidhi_primitives` 60; `asset_registry.english_description` of bg_vidhi_floors |
| Q-09 | schema reads | `information_schema` over the 66 tables named by the L0 assets' `count_sql_tables` ∪ `target_table` (CEN-R): columns named chart_id/subject_id/…, matching `chart`/`subject`; columns matching `build_id|release|generation|version|digest|sha256|fingerprint` (24 tables); tables named `release`/`vocab` (none) |
| Q-10 | build state | `build_runs` (734; scope × action), `build_run_assets` (`asset_id like 'bg\_%'`: 118 rows, 51 runs, 2026-07-04 → 2026-09-07; chart split 482012f1 ×50, 1c826d5a ×1), `asset_throughput` (39 L0 rows, all `lit`) |
| Q-11 | receipts | `asset_provenance_receipts WHERE asset_id like 'bg\_%'`: 37 rows, 36 assets, chart_id null, scope `__global__`, 35 proven / 2 unknown |
| Q-12 | migrations | `_migrations_applied` for 599, 642, 644, 703, 912 (all present) |
| Q-13 | per-chart counts | for each of the 86 tables named in `census_L1..L5.json` (`count_sql_tables` ∪ `target_table`): `count(*) … WHERE chart_id::text IN (482012f1…, 1c826d5a…, cb73cd3d…) GROUP BY chart_id`; 82 tables have a `chart_id` column; counts only |
| Q-14 | ephemeris | `ephemeris_daily`: count, distinct body, min/max date, distinct date; per-body counts; ontology `planet` ids |
| Q-15 | components | `bg_parihara_rules` 60, `bg_muhurta_activity_rules` 329, `bg_muhurta_factor_census` 51; `brahma_class_priors` 177; `brahma_event_ontology` 27, `brahma_activity_ontology` 12 |
| Q-16 | coverage | ontology rows matching `ayur|bhavat|longevity|lifespan` in `canonical_id` or `canonical_name_en`; `sutravali_rules` json columns and `yoga_canonical_id` matching `ayur`/`bhavat`; chunks whose `topic_tag`/`topics` match `ayur` |

**Files (census checkout `/Users/Dev/suvarna-census`, commit 2a78ec64d).**

| ID | what | population / method |
|---|---|---|
| F-01 | seed | `platform/scripts/seed/asset_registry_seed.ts`, `ASSETS` array split on `\n  {\n` (129 blocks, 40 `bg_`); fields compared with live: target_table, depends_on, target_floor, catalog_status, asset_kind, has_writer; `ASSET_REGISTRY_UPSERT_SQL` read for which fields are migration-governed |
| F-02 | migrations | 522 `.sql` in `platform/migrations`: statements matching `insert into asset_registry` / `update asset_registry … ;` that name an L0 id (28 of 40); headers of 599, 642, 644, 703, 912 read |
| F-03 | pins | `platform/src/generated/nirmana-analysis-layer-pins.json` (`layers.L0`, `history.L0`, `definition_bindings.L0`) and `nirmana-writer-digests.json` (123 writers, 36 `bg_`) |
| F-04 | writers | `platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py` (32 files); `@register('…')` ids counted (36) |
| F-05 | served surface | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` (47 non-test `.ts` incl. `index.ts`; 3 test entries); `CapabilityDescriptor` and `density_contract` greps per layer directory, non-test paths only (paths containing `test` excluded; recomputed at rev1: `density_contract` L0 0, L1 22, L2 7, L3 0, L4 1, L5 15). "39 declare a descriptor" counts files matching `const <name>: CapabilityDescriptor`; a bare-word `grep -rlw CapabilityDescriptor` finds 41 non-test files in the L0 directory, 40 excluding `index.ts` |
| F-06 | ledgers | `00_ARCHITECTURE/control/asset_gaps.jsonl` (857 rows; 290 for `bg_`), `asset_certs.jsonl` (1 line: `_schema`) |
| F-07 | file references | word-match `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src`, excluding `node_modules`; all file types (reproduces v3.0) and `.py/.ts/.tsx` non-test |
| F-07b | Gochara readers | `grep -rl 'bg_gochara_arcs'` and `'bg_gochara_citation_resolution'` over the same three roots, any file type, paths containing `test` excluded (used only in §1.1.4) |
| F-08 | inspector | `platform/scripts/governance/asset_census.py`: `CRITERION_REGISTRY` (gate mapping), `local_map_candidates()` |
| F-09 | local maps | the same regex re-run over `platform/python-sidecar/brahmagyan/**/*.py` (125 files → 32; 31 non-test; 11 `l0_*`) |
| F-10 | tests | files under `platform` whose name matches `parity|vocab` and `test` (37); the 10 at `python-sidecar/tests` top level |
| F-11 | charter | `/Users/Dev/suvarna-exec/00_ARCHITECTURE/briefs/suvarna/SUVARNA_AUTONOMY_CHARTER_v1_0.md` §4 R9 (L130–131) |

## Appendix B · Census gate cells under the plan's rollup (informational)

Assets (of 40) per gate, applying plan §1.4 ("worst applicable check wins: FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS; a gate
with no registered check is NO_DETECTOR") to the census cells; criteria feeding each gate are `CRITERION_REGISTRY` (F-08).
`Cost`, `Count`, `Complete`, `Reach` are not gates and are information (D3). Not a certification; the coded rollup (E6.2) does
not exist yet.

| gate | criteria feeding it | FAIL | PARTIAL | NO_DETECTOR | PASS | N/A | no reading |
|---|---|---:|---:|---:|---:|---:|---:|
| Ldgr | Ldgr.source_presence | 0 | 0 | 0 | 24 | 0 | 16 |
| Idem | Idem.pattern | 0 | 1 | 0 | 35 | 4 | 0 |
| Earn | Earn.build_record | 0 | 0 | 40 | 0 | 0 | 0 |
| Null | — none registered | 0 | 0 | 0 | 0 | 0 | 40 |
| Vocab | Vocab.identity, Vocab.alias | 1 | 0 | 1 | 35 | 0 | 3 |
| Carr | Carr.detector | 0 | 0 | 40 | 0 | 0 | 0 |
| Narr | — none registered | 0 | 0 | 0 | 0 | 0 | 40 |
| Dens | Dens.served | 23 | 0 | 1 | 0 | 16 | 0 |
| Build | Build.registered/contract/target/dag/count_integrity/completion/exercised/history/dep_liveness | 16 | 11 | 0 | 13 | 0 | 0 |

## Appendix C · v3.0 figures that reproduce unchanged (no re-statement needed)

All 38 inventory `live` counts (CEN-R) and 38 floors (registry `target_floor`, Q-01) against v3.0 §1.1, compared
programmatically, 0 differences; the 1,205,713 cockpit sum; 36 registered ids / 34 `has_writer`; 5 of 40 never dispatched; 1 DRAFT; 38
`count_sql` / 37 integrity SQL; 24 roots / 16 with intra-L0 edges / 0 outside L0; 5 Gaṇita cross-layer edges; ontology
741 / 741 / 730 and the 16 class counts; `dosha` 79/79 empty alias sets; 53 placeholder doṣa citations; rules 3,002 /
verse_ref 3,002 / 14 texts / 17 concept links / `confidence` = `quality_score` 3,002 of 3,002 with 3 distinct values;
remedies 341 with 52 exact resolutions; 10,651 chunks / 15 texts; ephemeris 825,084 = 91,676 × 9 with capitalised `body`;
46 non-test modules, 39 descriptors, 0 `density_contract` in the L0 directory; the nine file-reference counts (71, 68,
59, 48, 32, 30, 30, 29, 27); 32 writer files; 10 vocabulary/parity test files; 0 certification records; 360 gate cells;
`bg_vidhi_floors` DRAFT with 423 rows; the parihara components 60 + 329 + 51.

## Appendix D · Per-chart counts for the two other charts (counts only)

`[NEW]` Q-13. The layer is that of the asset(s) naming the table in `census_L1..L5.json`; `n/a` = the table has no `chart_id`
column. `chart_divisionals` holds 0 rows in total; `vw_chart_digest` is a view.

| layer | table | 482012f1 (canonical) | 1c826d5a | cb73cd3d |
|---|---|---:|---:|---:|
| L1 | chart_dashas | 483,870 | 471,767 | 505,348 |
| L1 | chart_divisionals | 0 | 0 | 0 |
| L1 | chart_facts | 143,299 | 139,717 | 138,080 |
| L1 | chart_vichara | 8,524 | 8,247 | 8,240 |
| L1 | fact_category_ownership | n/a | n/a | n/a |
| L1 | ga_condition_composite | 45 | 45 | 45 |
| L1 | ga_medical | 45 | 45 | 45 |
| L1 | ga_prashna_judgment | 0 | 0 | 0 |
| L1 | ga_prashna_lagna | 0 | 0 | 0 |
| L1 | ga_transit_anchors | 45 | 45 | 45 |
| L1 | ga_vastu_planet_direction_map | 40 | 40 | 40 |
| L1 | ga_yoga_firings | 53 | 69 | 80 |
| L1 | l1_tajik_varsha_year_lords | 240 | 235 | 305 |
| L2 | bodha_anomalies | 3,276 | 3,666 | 3,931 |
| L2 | bodha_cdlm_cells | 280 | 75 | 75 |
| L2 | bodha_cdlm_chart_summary | 5 | 5 | 5 |
| L2 | bodha_cgm_edges | 849 | 838 | 830 |
| L2 | bodha_cgm_motifs | 600 | 606 | 605 |
| L2 | bodha_cgm_nodes | 385 | 356 | 360 |
| L2 | bodha_cgm_paths | 45 | 45 | 45 |
| L2 | bodha_chart_gestalt | 5 | 5 | 5 |
| L2 | bodha_discoveries | 1,161 | 1,243 | 1,291 |
| L2 | bodha_grounding_matches | 50,731 | 0 | 0 |
| L2 | bodha_mechanisms | 615 | 633 | 620 |
| L2 | bodha_msr_signals | 50,678 | 50,171 | 49,875 |
| L2 | bodha_pratijna | 135 | 135 | 135 |
| L2 | bodha_question_lenses | 60 | 60 | 60 |
| L2 | bodha_rm_remedy_prescriptions | 135 | 135 | 135 |
| L2 | bodha_rm_resonances | 45 | 45 | 45 |
| L2 | bodha_signal_embeddings | 50,678 | 50,171 | 49,875 |
| L2 | bodha_triangulation | 195 | 105 | 105 |
| L2 | synthesis_quality_scorecard | 1 | 1 | 1 |
| L2 | vw_chart_digest | 5 | 5 | 5 |
| L3 | gochara_resonance_map | 765 | 753 | 77 |
| L3 | kala_activation | 0 | 336,093 | 1,055 |
| L3 | kala_activation_predicates | 50,678 | 50,171 | 49,875 |
| L3 | kala_avadhi | 1,169 | 1,160 | 1,291 |
| L3 | kala_bhavishya | 0 | 100 | 0 |
| L3 | kala_convergence | 0 | 17,957 | 2,540 |
| L3 | kala_darshana | 0 | 750 | 0 |
| L3 | kala_field | 8,570,075 | 2,412,882 | 0 |
| L3 | kala_gochara_windows | 17,211 | 20,239 | 2,667 |
| L3 | kala_jivana_parva | 100 | 100 | 109 |
| L3 | kala_kota_chakra | 585 | 585 | 0 |
| L3 | kala_moorti_nirnaya | 74 | 74 | 0 |
| L3 | kala_obstruction | 0 | 741 | 6 |
| L3 | kala_sudarshana_varsha | 120 | 0 | 0 |
| L3 | kala_taranga | 92,412 | 92,412 | 92,412 |
| L3 | kala_tithi_pravesha | 120 | 120 | 0 |
| L3 | kala_vedha_gochara | 171 | 173 | 0 |
| L4 | phala_anchors | 4 | 56 | 0 |
| L4 | phala_mitigation | 536 | 741 | 0 |
| L4 | phala_muhurta | 134 | 49 | 0 |
| L4 | phala_phaladesa | 13 | 13 | 0 |
| L4 | phala_pramana | 4 | 56 | 0 |
| L4 | phala_rectification | 185 | 185 | 0 |
| L4 | phala_rectification_best | 1 | 1 | 0 |
| L4 | phala_sankrama | 155 | 475 | 0 |
| L4 | phala_sodhana | 0 | 41 | 0 |
| L4 | phala_suddha_sodhana | 4 | 56 | 0 |
| L5 | kala_field_skill | 7 | 0 | 0 |
| L5 | life_events | 63 | 0 | 0 |
| L5 | mimamsa_anchor_adjustment | 139 | 56 | 0 |
| L5 | mimamsa_attribution | 1,425 | 0 | 0 |
| L5 | mimamsa_calibration | 57 | 0 | 0 |
| L5 | mimamsa_calibration_snapshot | 4 | 1 | 0 |
| L5 | mimamsa_convergence_adjustment | 500 | 500 | 0 |
| L5 | mimamsa_discoveries | 71 | 0 | 0 |
| L5 | mimamsa_event_provenance | 63 | 0 | 0 |
| L5 | mimamsa_export_log | 0 | 0 | 0 |
| L5 | mimamsa_fact_adjustment | 61,523 | 61,749 | 0 |
| L5 | mimamsa_insight_embeddings | 0 | 0 | 0 |
| L5 | mimamsa_insight_units | 115 | 35 | 0 |
| L5 | mimamsa_intervention_ledger | 0 | 0 | 0 |
| L5 | mimamsa_journal | 0 | 0 | 0 |
| L5 | mimamsa_load_bearing | 4 | 5 | 0 |
| L5 | mimamsa_manifestation_grammar | 24 | 23 | 0 |
| L5 | mimamsa_manifestation_sets | 139 | 56 | 0 |
| L5 | mimamsa_multipliers | 9 | 9 | 0 |
| L5 | mimamsa_negative_controls | n/a | n/a | n/a |
| L5 | mimamsa_predictions | 139 | 56 | 0 |
| L5 | mimamsa_preferences | n/a | n/a | n/a |
| L5 | mimamsa_qa_eval | 168 | 6 | 0 |
| L5 | mimamsa_reliability | 6 | 0 | 0 |
| L5 | mimamsa_signal_adjustment | 50,104 | 50,171 | 0 |
| L5 | mimamsa_signal_families | n/a | n/a | n/a |

## Appendix E · Carried from v3.0's pilots (not re-measured, except where marked)

`[CARRIED]` — five pilot briefs (bg_ontology, bg_rules, bg_ephemeris, bg_panchanga, bg_sarvatobhadra_grid) tested the asset
template against v3.0. Their headline findings, with this pass's status: bg_ontology — identity FAIL was a wrong detector,
not wrong data (**re-measured, holds**, Q-03); the `text` class and the corpus both hold 15 members and differ by 3 in each
direction (not re-measured); 233 of 741 rows unreachable through `list_entities` (not re-measured). bg_rules — extractor
yield varies 29× across texts (not re-measured); `confidence` = `quality_score` (**re-measured, holds**, Q-06).
bg_ephemeris — grid complete, vocabulary wrong (**re-measured, holds**, Q-14). bg_panchanga — a table-less service can be
dispositioned without inventing a row; `rows_written = 0` reads the same for a healthy service and a writer that produced
nothing (holds structurally: both services have `rows_written` 0 and state `lit`, Q-10). bg_sarvatobhadra_grid —
abstention is expressible as fidelity (**holds**: floor 0, rows 0, a proven provenance receipt for the empty state, Q-11).
Template results carried: C-9 confirmed (now on all six layers per the register: R92, R112, R144, R190, R204), §1's storage
bullets assume a table (R14), `N/A — inapplicable` vs `NO_DETECTOR` is load-bearing.
