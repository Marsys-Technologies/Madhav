---
artifact: REVIEW_L0_STRATEGY_v2_0
reviewed: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_0.md (commit 0b9e7eafe)
template: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md
parents: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md · 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md
predecessor_for_cleanse_check_only: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v1_0.md
produced_on: 2026-09-25
mode: independent, read-only, fresh context; every DB figure re-run against production (read-only), every code figure re-grepped at the document's pinned commit 85bf8f14e
verdict: REJECT
---

# Review: L0 Brahmagyan Strategy v2.0

**Verdict: REJECT.** The shape is right and most of the measured core reproduces (rule links 17/3,002; remedy 289 unresolved; synonyms 662/741 with all 79 doṣas empty; Venus 7 vs 10; 2 enum vs 32 free-string parameters; 37/40 integrity detectors; every row count). But nine figures do not reproduce, two of them structural: the entire "seed vs registry" bullet in §0.3 is a parser artefact (the seed agrees with the live registry on all five named assets), and the `bg_muhurta_lattice` "4 of 9 families" finding was closed on 2026-09-04, three weeks before this document declared it "still open". The seam-1 join numbers the document prints (237 / 84 / 22) exceed the catalog row counts (233 / 79 / 20) and the document did not notice: the identity authority holds **11 duplicate `canonical_id`s** (730 distinct of 741), which is the vocabulary's rule 1 failing at the id level, unreported. Derivation of the `bg_ontology` brief needs seven inventions; `bg_vidhi_floors` cannot be derived at all because it traces to nothing in Part 0. The obligation set L0 is scored on is stated three different ways (§0.2, §3.1, §5.1). Two of the five "native rulings" are decisions the parents already assign to this document.

Fixes are mostly deletions and re-measurements; the document should get shorter, not longer.

Line numbers are the file's own.

## Findings

**1. BLOCKER — §0.3 L153–158 "Seed vs registry": none of the five disagreements exist.**
Text: "The seed gives `target_table: None` for `bg_ephemeris`, `bg_rules`, `bg_concordance` (live: `ephemeris_daily`, `sutravali_rules`, `classical_attributions`); gives `bg_ephemeris_engine` a target of `reference_nakshatra` … gives `bg_prashna_rules` a target of `bg_vastu_directions` … Live carries edges the seed lacks: `bg_rules` (3 vs 0), `bg_concordance` (4 vs 0)."
Re-run at `85bf8f14e:platform/scripts/seed/asset_registry_seed.ts`: `bg_ephemeris` L185 `target_table: 'ephemeris_daily'`; `bg_rules` L283 `'sutravali_rules'`, `depends_on: ['bg_texts','bg_yogas','bg_dasha_systems']`; `bg_concordance` L320 `'classical_attributions'`, four deps; `bg_ephemeris_engine` L465 `target_table: null`; `bg_prashna_rules` L622 `target_table: null`. All identical to live. The document's parser matched `upstream_asset_id: 'bg_rules'` / `'bg_ephemeris'` in the volume-coefficient block at L3181–3206 and read the next block's fields. Propagates to §3.1 ("seed disagrees with registry in five places") and W-L0-1 ("seed reconciled to live"). Delete the bullet; replace with: "**Seed vs registry.** Agree on `target_table` and `depends_on` for all 40 (checked at 85bf8f14e)." Remove the five-places clause from §3.1 and the seed item from W-L0-1.

**2. BLOCKER — §1.3 seam 1 and §2.6 rule 1: the identity authority has 11 duplicate ids, printed and not seen.**
Text (L279–284): "`brahma_yoga_catalog.canonical_id` → `brahma_ontology` | 237 | **0**" against a 233-row catalog; doṣa 84 vs 79; daśā 22 vs 20. A join that returns more rows than the left table means the right table has duplicate keys. `SELECT count(DISTINCT canonical_id) FROM brahma_ontology` = **730** of 741. The eleven: `ashtakavarga` (concept+school), `balarishta` (concept+dosha), `daridra` (dosha+yoga), `dhaiya` (concept+dosha), `kemadruma` (dosha+yoga), `kp` (dasha_system+school), `neecha_bhanga_raja_yoga` (concept+yoga), `phaladeepika` (school+text), `sade_sati` (concept+dosha), `sthira_dasha` (concept+dasha_system), `vyatipata` (upagraha+yoga). `resolve_entity.ts` resolves by name/synonym and returns both rows for these. This is DP §4.1 rule 1 ("one canonical id … per thing") failing inside the owner, and it is a `bg_ontology` fidelity FAIL on "identity correct". Add to §1.3 seam 1: "The joins over-count by 4 / 5 / 2 because `brahma_ontology` carries 11 `canonical_id`s in two classes each (730 distinct of 741). Seam 1 is shared but the key is not unique." Add to §2.6 rule 1 state: PARTIAL → "**FAIL on uniqueness**: 11 ids span two classes." Add to W-L0-8 proof (1): "`count(*) = count(DISTINCT canonical_id)` on `brahma_ontology`." Add to §5.3's first `bg_ontology` record: `source_and_domain_fidelity/identity_unique` — verdict FAIL.

**3. MAJOR — §1.3 seam 5 L309–311 and §3.2 L569: the lattice allowlist finding is stale.**
Text: "`FACTOR_FAMILIES` allowlist covers 4 of 9 families the writer produces — ~72,580 of ~165K rows unreachable by explicit filter (W2 MUST-1, still open)."
At 85bf8f14e `query_muhurta_lattice.ts` L46–49 lists all nine (`agnivasa, combination_yoga, kalam, ghati_muhurta, hora, vara, nakshatra, tithi, lagna`); landed in #1705 on 2026-09-04. Production has exactly those nine families, 173,219 rows (exact count; §1.1 says ~172,330 and §1.3 says ~165K — two figures for one table). Delete from seam 5, §3.1 delivery row, §3.2, §3.3 and W-L0-4's "9/9" proof. Seam 5 keeps only the `density_contract` 0/49 finding.

**4. MAJOR — §1.3 seam 3 L294–301: the remedy column is one identity space with spelling drift, not two spaces.**
Text: "345 non-null values of which **289 do not resolve** … They resolve to nothing there because they are *source-work names* — `BPHS` (193), `classical_tradition` (80), `Phaladeepika` (11), `Tajaka` (3) — not entity identities."
Re-run: non-null = **341** (every row), not 345; 289 unresolved reproduced. But the 52 that *do* resolve are also source-work names — `brihat_samhita` 17, `bphs` 7, `hora_sara` 6, `muhurta_chintamani` 5 … — resolving because `text` and `school` are ontology classes (`bphs/text`, `phaladeepika/text`, `tajaka/school`). The column is uniformly a source-work id; `BPHS` fails where `bphs` passes. That is rule 3 (normalization declared once) failing, not a second identity space, and it removes the W-L0-6 ruling "whether the remedy identity space merges into the ontology or stays a separate registry". Replace the seam-3 paragraph with: "**Seam 3 — remedies → source identity: UNNORMALIZED.** `source_canonical_id` is populated on 341/341 rows with text/school ids. 52 resolve to `brahma_ontology` (`text`/`school` classes); 289 do not, because they are the same ids spelled outside the closed set (`BPHS`×193 vs `bphs`, `Phaladeepika`×11 vs `phaladeepika`, `Tajaka`×3 vs `tajaka`) or a non-id (`classical_tradition`×80, `bphs_jaimini`×1, `nadi_navamsa_patel`×1 — the last two are `text_id`s in `classical_text_chunks` absent from the ontology). Fix: normalize to the ontology's text/school ids; make `classical_tradition` an explicit `unattributed` state; add the two missing texts to the `text` class." Replace §3.3's `bg_remedies` line and W-L0-3's rename proof accordingly.

**5. MAJOR — §0.2, §3.1, §5.1 state three different obligation sets; §5.3 scores on a fourth.**
§0.2 L94–99 names source-and-domain fidelity + computational correctness + delivery fidelity. §3.1 adds "Concept and relationship completeness" and "Operational honesty" rows. §5.1 L717 names four (adds operational honesty, drops concept completeness). §5.3 writes an `operational_honesty/declared_consumers` record for `bg_ontology`. Template §5.1: "A layer scores on the subset its 0.2 row names." Product §11 gives L0 one; DP §13.3 item 1: "A layer plan that names its own criteria instead of inheriting these is not derived." The additions may be reasoned, but in one place. Replace §0.2's "Scored on" paragraph with the full set and the reason for each addition: "source and domain fidelity (product §11 row, all 40); computational correctness (the five computed substrate assets — a computed table cannot be scored on source fidelity alone); delivery fidelity (product §14 row names both presentation modes; the 47-file served surface is where L0 is rendered); operational honesty (L0 is the registry's root — a registry description that asserts a provenance the table lacks, migration 1079's class, is an L0 defect). Not scored on: concept and relationship completeness — that is L2's row; the L0 question of which relation vocabularies exist as data is §2.4's." Delete the §3.1 "Concept and relationship completeness" row (its content already sits in §2.4). Make §5.1 cite §0.2 instead of re-listing.

**6. MAJOR — Part 0 does not trace 14 of the 40 assets; §4.4 then cannot narrow them.**
`bg_nakshatra`, `bg_class_priors`, `bg_class_lifetime_counts`, `bg_cohort`, `bg_transit_engine`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_sarvatobhadra_grid`, `bg_kota_chakra_rings`, `bg_gochara_citation_resolution`, `bg_prashna_rules`, `bg_vastu_directions`, `bg_vidhi_primitives`, `bg_vidhi_floors` appear in no §0.1 row. §4.4 L689: a brief takes "its P/V rows from 0.1 (narrowed to the asset)" — for these the narrowing is empty. Under ruling 3 the assets are not struck; Part 0 is incomplete. Add rows to §0.1's second table:
"| the Kāla method substrates — `bg_transit_engine`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_kota_chakra_rings`, `bg_sarvatobhadra_grid` | P09, P10, P24 (every L3 clock reads a reference scale or geometry) | 6 `ka_*` registered consumers |
| nakshatra geometry — `bg_nakshatra` | P09, P21, and every KP reading (P20) | `ga_nakshatra` registered; 8 writer files |
| the investigation floors — `bg_vidhi_primitives`, `bg_vidhi_floors` | P17, P18 (the omission check and the question compass, DP11) | 1 writer + 3 serving files each |
| horary method — `bg_prashna_rules` | P20 (method selection) and the Praśna horizon (product §15) | `ga_prashna` |
| research capital, served to no P directly — `bg_class_priors`, `bg_class_lifetime_counts`, `bg_cohort` | engineering baselines for `ka_kshetra` / `mi_kula`; H by design | 3 registered consumers |
| citation resolution and spatial doctrine — `bg_gochara_citation_resolution` (P15), `bg_vastu_directions` (P08, testimony) | — | 4 / 5 serving files |"

**7. MAJOR — §1.2's fidelity table is six dimensions with example assets, not a per-asset score.**
Text (L249–256) lists "passes" and "fails / partial" by example; "Declared count truthful — most". Of 40 × 6 cells, roughly 40 are stated. `bg_ontology` itself appears only under "Alias set present"; its "identity correct" cell (FAIL — finding 2), "source present" cell (PASS — `source_citation` null on 0/741) and "method boundary" cell are unstated. §1.5 then concludes "Nothing fails fidelity outright", which the table cannot support. Two rows are not fidelity of the knowledge: "Integrity detector present" and "Declared count truthful" are operational honesty and belong in §3.1. Replace the table with a 40-row matrix, four columns (identity · source · method boundary · alias set), each cell PASS / FAIL / N/A, and one line above it naming the detector per column (`canonical_id` join + distinctness; witness column non-null count; a `scope`/`boundary` text present; `cardinality(synonyms)>0`). Rows this review can already fill: `bg_ontology` FAIL/PASS/N/A/PARTIAL; `bg_rules` PASS/PASS/FAIL/N/A; `bg_remedies` FAIL(normalization)/PASS/PASS/N/A; `bg_vidhi_floors` N/A/FAIL/FAIL/N/A; `bg_vidhi_primitives` N/A/FAIL/FAIL/N/A. The rest are one query each.

**8. MAJOR — §1.2 L255 and §3.1 L548: the `bg_class_priors` count finding compares a partition to its whole table.**
Text: "`bg_class_priors` — 171 / 165 / 164 declared vs 177 live; `brahma_formula_constants` 18 declared vs 17 live".
Registry `count_sql` is `WHERE prior_version='1.0'` → **171**, which is live for the asset; seed floor 171; the 2026-09-04 snapshot 171. 177 is the shared table including `bg_class_lifetime_counts`'s six `ne_v01` rows — the partition the document itself describes two paragraphs earlier. 165 is the writer docstring and 164 a seed comment (W1 batch D L105–108): stale comments, not declarations. For formula constants: registry, seed, snapshot and live all say 17; no source says 18. Replace with: "`bg_class_priors`: registry, seed and live agree at 171; the writer docstring (165) and a seed comment (164) are stale — delete the comments." Delete the formula-constants clause.

**9. MAJOR — §1.1 L221–226: two "registry defects" are false; a third is untraced.**
Text: "duplicate `@register` decorations for `bg_reference` (in `__init__.py`) and `bg_gochara_arcs` (twice in its own file) — last-registration-wins behaviour unverified".
`__init__.py` L172 is the usage example in `register()`'s docstring; `bg_gochara_arcs.py` L15 is the module docstring; L89 is the only decoration. `register()` (L176–185) raises on a genuine conflict. Delete. "`sort_order` collides at 68 … and 69" reproduces but serves no Part 0 item and no obligation in §0.2 — strike under §0.4, or keep only if operational honesty is adopted per finding 5 (then it stays as one clause). Also L217: "All 40 are `lit` in `asset_throughput`" — 39; `bg_gochara_citation_resolution` has no `asset_throughput` row at all (consistent with `static`). Replace with "39 of 40 are `lit`; the static asset has no throughput row."

**10. MAJOR — DP §4.3's rule states are a parent obligation with no section, and v1.0 carried them.**
DP §4.3: "Distinguish supported, readable-but-not-executable, disputed, unsupported and method-inapplicable rules." DP02: "executable scope". v1.0 L0-C04 / §7 item 4 named `READABLE_NOT_EXECUTABLE`, `QUALIFIED_EXECUTABLE`, `UNQUALIFIED_SOURCE`, `UNSUPPORTED_SCOPE`, `METHOD_INAPPLICABLE`, and they exist in code (`brahmagyan/l0_resource_config_slice.py`, `ga_writers/data_plane_contracts.py`). v2.0 mentions only that "executable status is not a column" (§1.2) and §3.3's `bg_rules` must-add omits the state entirely. Add to §3.3 `bg_rules`: "a `qualification_state` column over the five DP §4.3 states, populated per rule (the vocabulary already exists in `l0_resource_config_slice.py`); `unlinked_reason` becomes one value of it." Add the state to W-L0-3's proof.

**11. MAJOR — §1.1 omits an L0 producer artifact that exists: the resource-config slice.**
v1.0 §7's first producer slice was built — `platform/python-sidecar/brahmagyan/l0_resource_config_slice_v1.json`, `l0_resource_config_slice.py`, `tests/test_l0_resource_config_slice.py`. It is not registered, not in §1.1, not in §2.6's release inventory (it is a second release-shaped artifact beside `l0_semantic_release_v1.json`). Template §1.1: "Every asset and service the layer owns: registered, writer-backed, service, residual, shared, historical." Add one row under a "residual / unregistered" heading and one line in §2.6 rule 4 stating whether it is joined to the ontology (it is not).

**12. MAJOR — §0.3 L150–152 / §4.3: "a change to `bg_ontology` stales nothing" is false.**
Text: "a change to `bg_ontology` stales *nothing* through the orchestrator, because nothing declares it." Live `depends_on`: `bg_reference`, `bg_yogas`, `bg_doshas`, `bg_dasha_systems` declare `bg_ontology`; `bg_texts` has 8 declared L0 consumers. The "0 registered" figure holds only for consumers outside L0 (the instrument is not stated anywhere — see re-run table). Replace with: "`bg_ontology` has 4 declared consumers, all inside L0, and 0 outside; a change stales the four catalogs and nothing in L1–L5, where 18 files read it." Same correction at §1.1 (row and column heading → "reg. cross-layer consumers"), §3.2, §3.4, §4.1 item 1, §5.3.

**13. MAJOR — W-L0-6: three of five "rulings" are decisions the parents assign to this document or the registry already records.**
(a) "`bg_vidhi_floors` status" — the live `english_description` reads: "catalog_status=DRAFT is intentional, not stale: 12/14 intent floors are writer-tagged [MANDATORY] … education_deepdive and progeny_deepdive remain writer-tagged [CANDIDATE] … Re-verify against the writer source before flipping to CURRENT." Decided; strike. (b) "whether sambandha typing / Bhāvat Bhāvam scope / varga construction become L0 data" — DP §4.1: "The L0 plan must decide the exact authority boundary from producer/consumer evidence"; DP §4.2 already places "varga construction" and "node and house convention" in L0's calculation-convention family, and rule 1 makes every relation type a thing needing an id. The document is the deciding instrument. State the decision in §2.4: "sambandha relation types and BB scope → `bg_ontology` `concept` class + a `bg_rules` scope column; varga construction conventions → `bg_formula_constants` rows. The operator code stays in L1/L2 (v1.0 §7 invariant)." (c) the remedy identity-space ruling dissolves under finding 4. Keep (d) `bg_sarvatobhadra_grid` school and (e) `bg_prashna_rules` facility activation — both are doctrine/horizon calls the parents reserve to the native.

**14. MAJOR — §2.6 rule 4 L442: `graha_labels.ts` is not "hand-extracted … pinned, not generated".**
Text: "`graha_labels.ts` is hand-extracted from `address_resolver.ts` and pins the release id — pinned, not generated."
`graha_labels.ts` L34 imports `l0_semantic_release_v1.json` and builds `RELEASED_IDENTITY_BY_ID` from `semanticRelease.entities` with `normalize("NFC").trim().toLocaleLowerCase()` — it is generated at build time from the release, with the release's own normalization. The real gap is one level up (the release is not generated from `brahma_ontology`) and one level sideways: TypeScript now has *two* resolvers with different normalization — `graha_labels.ts` (NFC + casefold, release-backed) and `resolve_entity.ts` (`$1 = ANY(synonyms)`, DB-backed). Rewrite the rule-4 cell's second sentence: "`graha_labels.ts` derives from the release at build time and pins its id and digest; the release itself derives from nothing — no test joins it to `brahma_ontology`." Add to rule 3: "TS carries two resolvers with different normalization (release-backed NFC/casefold vs DB-backed exact-array match)."

**15. MINOR — §5.2 L739 "The 31 criteria apply unchanged" — the template has 32 since the Vocab addition it credits to this instance (§6 item 6).** Replace "31" with "32".

**16. MINOR — §0.1 L59 and §1.1: "14 texts" — `classical_text_chunks` has 15 distinct `text_id`s (`bphs_jaimini` is the fifteenth); 14 is `sutravali_rules`' distinct-text count.** Replace with "15 texts".

**17. MINOR — "49 capability files" (§0.1, §1.3, W-L0-4) counts two `.test.ts` files and `index.ts`.** 47 non-test `.ts`; 46 excluding `index.ts`. Replace with 46 and make W-L0-4's proof "grep = number of exported `CapabilityDescriptor`s", not a file count.

**18. MINOR — §2.4 omits DP §5's "Present interval (P24)" row.** Template §2.4: "the five states, never a blank." Add: "| Present interval (P24) | no L0 half | inapplicable with reason — the row's data is L3/L4; L0 supplies only the clock vocabulary already covered under Kāla |".

**19. MINOR — §6 numbering runs 1,2,3,4,5,7,6; §4.2 L668 "It It is named last"; §2.6 is placed before §2.5 (copied from the template).** Fix the three.

**20. MINOR — §1.1 `bg_vidhi_floors` row lists one table; the asset is two.** `count_sql` sums `vidhi_intent_floors` (14) + `vidhi_floor_items` (409). Add the header table; the "no provenance column" finding applies to both.

**21. MINOR — §1.3 seam 6 / §2.6 rule 5: "which it has since fixed by importing the SSoT" (`gochara_intensity/enrichment.py`)** — L93 still declares `_GRAHA_NAMES = {"Sun", "Moon", …, "Venus", …}` as a literal set. Replace "since fixed" with "partly fixed; a literal graha set remains at L93".

## Derivability test

**`bg_ontology`, from this instance + tiers 1–2, via §4.4's list and template §5.2's 32 criteria.** Inventions required:

1. **Which obligations it is scored on.** §0.2 says three; §5.3 writes an `operational_honesty` record for it. (Finding 5.)
2. **Its presentation fields.** §2.2 lists every table in "carried fully / partially / not carried" except `brahma_ontology`. A brief author must decide whether the ontology owes school (no), witness (`source_citation`, populated 741/741 — measured here, not in the instance), convention (no), aliases (yes), alternatives (ambiguity list — in the release, not the DB).
3. **DP01 fields and grain.** §2.3 says the producer-side envelope "is also absent for L0" and sends it to W-L0-2; the brief still cannot state what `bg_ontology` hands to `bg_reference`/`bg_yogas` or to `list_entities`. Declared gap, but an invention all the same.
4. **Its fidelity verdicts.** Identity (FAIL — 11 duplicates), source (PASS), method boundary (unstated) are not in §1.2. (Finding 7.)
5. **Its declared consumers.** §3.2 says "declare its 18 actual readers"; four are already declared. The brief inherits a wrong baseline. (Finding 12.)
6. **T1-D data sufficiency, T1-G efficiency, T1-H reliability, T2 knowledge-time, T3 synergy binding, T3 serving contract.** No section of the instance feeds these; §4.4 does not map criteria to sections. For `bg_ontology`, "sufficiency" would be "16 classes present vs DP §4.1's 16 named" — derivable from the parent, not stated here.
7. **Preserved kernel and relevant Jyotish concepts** (product §16 requires both of every brief). Absent from §4.4 and from the template's §4.4.

Derivable without invention: P/V rows (all 24 — trivially); correctness rules and switch behaviour (§2.1); coverage rows (§2.4); order and baseline (§4.1); disposition P/I/E and must-add list (§3.3); manifestation/temporal role (none). **Seven inventions. Fail.**

**`bg_vidhi_floors`.** §0.1: not present. §0.3 / §1.4 / §2.3: no contract. §2.4: no row. §1.1: one table where the asset has two. §1.2: one FAIL cell. §3.2: Q, gated on a ruling the registry already records. §3.3: "a provenance column set" — provenance of what, for a compiled intent floor (the writer's ratification? the primitive's source?) — unspecified. The brief author gets a disposition and a defect and nothing to trace either to. **Not enough to work with.** Findings 6, 13(a) and 20 are the minimum.

## Measurement re-run

| # | figure (section) | claimed | re-run (2026-09-25) | result |
|---|---|---|---|---|
| 1 | zero registered downstream consumers (§0.3, §1.1, §1.3 seam 4) | 21 of 40 / 19 with ≥1 | consumers outside L0: **21 / 19**; all consumers: 13 / 27; `bg_ontology` 0 cross-layer, 4 intra-L0 | REPRODUCED only under an unstated cross-layer restriction; "stales nothing" false (finding 12) |
| 2 | 40 of 40 read by code (§0.3, §1.1) | per-table writer/serving file counts | every table grepped has ≥1 reader; counts vary ±1–4 with exclusion rules (`brahma_ontology` 11/6 vs 12/6; `sutravali_rules` 8/9 vs 10/5; `brahma_event_ontology` 31/21 exact; `ephemeris_daily` 28/14 exact; `bg_transit_rules` 26/9 exact) | REPRODUCED in kind; instrument under-specified (substring vs word match, exclusion globs) |
| 3 | `sutravali_rules` links (§1.3 seam 2) | 3,002 total; 3,002 `text_id`; 14 texts; 17 `yoga_canonical_id` | 3,002 / 3,002 / 14 / 17 (`dasha_system_id`: 0) | REPRODUCED |
| 4 | remedy `source_canonical_id` (§1.3 seam 3) | 345 non-null; 289 unresolved; BPHS 193 / classical_tradition 80 / Phaladeepika 11 / Tajaka 3 | **341** non-null (all rows); 289 unresolved; those four values exact, plus `bphs_jaimini` 1, `nadi_navamsa_patel` 1; the 52 resolving values are also text/school names | 289 REPRODUCED; 345 NOT; characterisation wrong (finding 4) |
| 5 | `brahma_ontology` synonyms (§2.6 rule 1) | 741 entities, 16 classes, 662 populated, 79 empty = all doṣas; Venus `{shukra,sukra,Venus,Bhargava,usana,VEN,VENUS}`; domain class 45 | 741 / 16 / 662 / `dosha=79` only; Venus row identical; domain 45; **730 distinct `canonical_id`** | REPRODUCED; duplicate ids unreported (finding 2) |
| 6 | interface-parameter census (§2.6 rule 5) | 2 enum, 32 free-string | 2 `z.enum`, 32 `z.string` on `planet*`/`graha*` params in registry + MCP | REPRODUCED |
| 7 | Venus alias disagreement (§1.3 seam 6, §2.6) | DB 7, release 10; `venus`, `VE`, `śukra` release-only | release `venus` entity: `[VEN, VENUS, venus, Venus, VE, shukra, śukra, sukra, Bhargava, usana]` = 10; DB 7; release-only exactly those three | REPRODUCED |
| 8 | seam-1 joins (§1.3) | 237 / 84 / 22 / 60, 0 orphans | 237 / 84 / 22 / 60, 0 orphans; left tables 233 / 79 / 20 / 60 | REPRODUCED; over-count unremarked (finding 2) |
| 9 | lattice allowlist (§1.3 seam 5, §3.2) | 4 of 9 families; ~72,580 of ~165K unreachable; open | 9 of 9 at 85bf8f14e (since #1705, 2026-09-04); DB has 9 families, 173,219 rows | NOT REPRODUCED (finding 3) |
| 10 | seed vs registry (§0.3) | 5 target/edge disagreements | 0 — seed at 85bf8f14e matches live on all five | NOT REPRODUCED (finding 1) |
| 11 | `asset_throughput` (§1.1) | all 40 `lit` | 39 `lit`; `bg_gochara_citation_resolution` has no row | NOT REPRODUCED (finding 9) |
| 12 | duplicate `@register` (§1.1) | `bg_reference`, `bg_gochara_arcs` | both are docstrings; one decoration each | NOT REPRODUCED (finding 9) |
| 13 | declared counts (§1.2, §3.1) | priors 171/165/164 vs 177 live; constants 18 vs 17 | priors: registry, seed, snapshot, live partition all 171; 177 = whole shared table; 165/164 are comments. Constants 17 everywhere; no source says 18 | NOT REPRODUCED (finding 8) |
| 14 | `density_contract` (§1.3 seam 5) | 0 of 49 | 0; 49 `.ts` incl. 2 tests + `index.ts` | 0 REPRODUCED; 49 mis-counted (finding 17) |
| 15 | registry hygiene (§1.1) | 37/40 integrity; `sort_order` 68 ×2, 69 ×2; `bg_vidhi_floors` DRAFT only; `bg_prashna_rules` NULL target with `postgres_table`; `reference_nakshatras` present | 37 (`bg_panchanga`, `bg_ephemeris_engine`, `bg_sarvatobhadra_grid` without); 68: `bg_vidhi_primitives`+`bg_formula_constants`; 69: `bg_sky_calendar`+`bg_vidhi_floors`; DRAFT only; NULL/postgres_table; `to_regclass` non-null | REPRODUCED |
| 16 | evidence ledger (§1.1, §2.5) | `asset_frozen` 40 under t0, 0 under t3; 3 `producer_covered`, 1 `static`, 1 `empty`, 2 `probe` | identical; t3 definition row exists; no bg_* event under any revision but t0 | REPRODUCED |
| 17 | release contents (§2.6 rule 4) | id `l0.semantic.2026-09-13.1`; 12 entities; catalogues 3/2/1/2/1/1; `LOCAL_EXECUTION_ONLY`; `unicode_nfc_trim_casefold` | identical | REPRODUCED |
| 18 | `graha_labels.ts` "hand-extracted, pinned not generated" (§2.6 rule 4) | — | imports the release JSON, derives its map from it, NFC-normalizes | NOT REPRODUCED (finding 14) |
| 19 | `resolve_entity.ts` normalization (§2.6 rule 3) | `$1 = ANY(synonyms) OR lower(name)` | L67–69 exactly that | REPRODUCED |
| 20 | Venus literal carriers (§2.6 rule 2) | 130 py / 42 ts / `"Venus"` ×952 | 126 / 42 / 967 | approximately REPRODUCED |
| 21 | row counts (§0.1, §1.1) | 741, 11, 28, 10,651, 9,571, 721, 3,002, 233, 79, 20, 341, 60, 27, 177, 17, 9, 249, ~824,543, ~33,933, ~31,059, 76, 9, 5, 8, 0, 27, 14, 8, 21, 27, 12, 60, 409, ~10,000 | all identical (estimates via `reltuples`) | REPRODUCED |
| 22 | "14 texts" (§0.1) | 14 | 15 distinct `text_id` | NOT REPRODUCED (finding 16) |
| 23 | pin instrument "L3-only" (§0.3, §6 item 1) | absent for L0 | `asset_registry_seed_dag_parity.test.ts` pins `bg_ephemeris`, `bg_rules`, `bg_transit_rules` as upstream ends of `ka_*` edges; no bg_* asset's own `depends_on` is pinned | PARTIAL — say "pins bg_* only as upstream ends of L3 edges" |

Nine NOT REPRODUCED; one partial; the rest hold.

## Alignment test

Every section from Part 1 on carries a `traces_to:` and all of them are real except: §1.1's "Registry defects" paragraph (sort_order, duplicate `@register`, legacy table) traces to operational honesty, which §0.2 does not name — resolve via finding 5 or strike; §3.4 traces to 0.2 but restates §1.3 seam 4 and §1.1's reader counts verbatim — strike the section, keep its one new sentence ("Within L0 itself the interplay is real where the catalogs meet the ontology…") in §1.3. The 14 untraced assets (finding 6) are the alignment test failing at asset granularity, which the template does not operationalise (template defect e below).

## Parent conformance

- Product §11 L0 row — contradicted by three obligation sets (finding 5).
- Product §8.1 L0 row, §13 — present in §2.1, verbatim. ✓
- Product §16 (every brief states preserved kernel, Jyotish concepts) — no corresponding §4.4 item (derivability item 7; template defect c).
- DP §3.1 L0 row — verbatim. ✓ DP §4.1 — §2.6, six rules matched. ✓ (content errors: findings 2, 14.)
- DP §4.3 rule states — no section (finding 10).
- DP §5 "L0 meaning" column — §2.4, 12 of 13 rows (finding 18).
- DP §6.1 "Enrich only where a named consumer needs an absent qualified clause" — §3.3's enrichments name no consumer. Under ruling 3, naming the fidelity dimension suffices; say so in one line above §3.3: "Each addition below closes a §1.2 fidelity cell; a consumer is named where one drives it."
- DP §13.3 items 1, 1a, 2–8 — all present; item 2 incomplete (finding 11).

## The fidelity score (§1.2)

Six dimensions are the right ones and match the template's clause. It is not yet a score: cells are illustrated, not filled (finding 7); two of the six rows ("Integrity detector present", "Declared count truthful") measure the registry, not the knowledge, and belong under operational honesty; the one conclusion drawn from it ("Nothing fails fidelity outright") is false on the identity dimension (finding 2). Nothing in it is an ablation or contribution judgement in disguise — the "Reachability, recorded as context" paragraph is correctly quarantined. The rewrite is mechanical: one matrix, four columns, one detector per column.

## §2.6 vocabulary

Six-rule scorecard matches DP §4.1 rule for rule. "Three authorities" (DB ontology · Python release · domain module) is supported; `graha_labels.ts` is downstream of the release, not a fourth. Wrong or missing: rule 1 misses the 11 duplicate ids (finding 2); rule 4 mischaracterises `graha_labels.ts` and rule 3 misses that TypeScript itself has two resolvers with different normalization (finding 14); rule 5's "since fixed" is partial (finding 21); rule 6 correctly names the two escaping tuples (`panchang_engine/planets.py`, `brahmagyan/ganita/l1_positions.py` — both exist, neither imports the release). The closing paragraph "Where the plane actually stands" and the "correction to §1.1's reader table" paragraph are cuttable — fold the correction into §1.1.

## Template defects

§6's seven, confirmed or refuted:

1. Pin absent for L0 — **partly real**: the seed-DAG parity test pins bg_* as upstream ends only. Keep, reworded.
2. Root layer consumes nothing internal — **real**.
3. Ablation-as-proxy clause — **superseded** by item 7's repair; delete from §6.
4. T1-E / T5 differ at a root layer — **real**.
5. Synergistic fraction impossible without ablation — **real and unrepaired**: template §1.5 still reads "Record the synergistic term as a fraction of the total."
6. Vocabulary conformance missing — **real**, repaired.
7. Ablation wrong for a reference layer — **real**, repaired; but the template's §1.2 `measured_by:` line still reads "ablation of the single asset against the layer's served reading" above the reference-layer clause that overrides it.

Worked around silently, to fix in the template before L1:

a. **§5.2's 32 criteria are not mapped to §4.4's inheritance list.** T1-D/G/H, T2 Eff/KTime, T3 Bind/Srv, T5 have no feeding section, so every brief author invents them (derivability item 6). Add a column to §5.2: "fed by instance §".
b. **§4.4 omits product §16's "preserved kernel" and "relevant Jyotish concepts."** Add both bullets.
c. **§2.6 is numbered after §2.5 and placed before it.** Renumber.
d. **Part 3's four subsections carry no three-line header**, against "Every section carries three lines." Add them or say Part-level headers suffice for 3.x.
e. **The alignment test has no asset-granularity rule.** §0.4 strikes sections; nothing requires every §1.1 asset to appear in a §0.1 row. Add to §0.4: "and every asset in 1.1 appears in a 0.1 row, or 0.1 is incomplete."
f. **§1.1 demands "last build" and "contract fields live" per asset**; the instance dropped both columns without saying so. Either the template drops them or the instance carries them.
g. **§5.1 says a layer scores "on the subset its 0.2 row names" but §0.2's `inherits:` names only product §11**, with no rule for adding an obligation with reasoning. Add one sentence: "0.2 may add an obligation from product §14 with the reason stated; 3.1 and 5.1 cite 0.2 and never re-list."
h. **§2.4 says five states; product §5.1 has six** (adds "contradictory") and DP §5 uses "unresolved" for the fifth. Pick one list, cite it.
i. **The `measured_by:` convention has no rule for stating the instrument's scope** (what counts as a "consumer", a "reader", a "capability file"). Three of this instance's headline figures went wrong there (re-run rows 1, 2, 14). Add: "a count names its population and its exclusions."

## The rulings queue (W-L0-6)

Genuine native decisions: `bg_sarvatobhadra_grid` school (doctrine); `bg_prashna_rules` facility (horizon activation, product §15). Pushed up to avoid making them: `bg_vidhi_floors` status (registry already records the answer and the flip condition); sambandha/BB/varga as L0 data (DP §4.1–4.2 assign the boundary decision to this document and already place varga construction in L0's convention family); remedy identity-space merge (dissolves under finding 4). See finding 13 for the replacement text.

## What the cleanse may have cost

Two essentials were lost; everything else in v1.0 is absorbed or superseded.

1. **The rule qualification-state vocabulary** (v1.0 L0-C04, §7 item 4) — a DP §4.3/DP02 obligation, already in code, absent from v2.0's must-add for `bg_rules`. Without it "executable scope" has no values and W-L0-3's proof cannot be written. Restore as finding 10 states; do not restore the surrounding slice prose.
2. **The built resource-config slice** (v1.0 §7) — an existing L0 artifact that v2.0's inventory does not know about (finding 11). Restore as one inventory row and one §2.6 line, nothing more.

Not essential, correctly dropped: the L0-Q01–Q12 question list (absorbed into §0.1/§2.4), L0-C01–C10 (absorbed into §2.3/§1.4), §6.1's adjacent-authority scope table (belongs in the tier-4 briefs' `must_not_touch`), §6.2's DP applicability matrix (§0.2's must-not-claim carries the prohibitions that matter), §8–§10 (superseded by Part 4).

## What does not earn its place

Cut without losing a derivation or a measurement (≈900 words):

- §3.4 entire (restates §1.3 seam 4 and §1.1) — keep one sentence in §1.3.
- §0.1 second table's "measured reach" column (duplicates §1.1).
- §1.1 "Registry defects" — the two false items; the seed-disagreement clause; the `sort_order` clause unless finding 5 adopts operational honesty.
- §1.2 "Reachability, recorded as context" — keep the two asset names, drop the three sentences of framing.
- §2.6 closing paragraph "Where the plane actually stands" and the "correction to §1.1" paragraph.
- §4.2 the trailing W-L0-7 paragraph (its row already says it).
- §5.1 first paragraph (repeats §1.2's opening); keep the second.
- §6 item 3.
- Frontmatter `not_measured` and §5.4 item 3 say the same thing; keep the frontmatter.
