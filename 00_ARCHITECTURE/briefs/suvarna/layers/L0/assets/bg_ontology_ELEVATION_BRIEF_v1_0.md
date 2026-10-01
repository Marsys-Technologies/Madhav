---
asset_id: bg_ontology
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "enrich (E)"
disposition_proposal_approver: "Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-01, TI-L0-03, TI-L0-11, TI-L0-12, TI-L0-13, TI-L0-14, TI-L0-15]
ledger_gap_ids: [bg_ontology-G01, bg_ontology-G02, bg_ontology-G03, bg_ontology-G04, bg_ontology-G05, bg_ontology-G06, bg_ontology-G07, bg_ontology-G08, bg_ontology-G09, bg_ontology-G10, bg_ontology-O1, bg_ontology-O2, bg_ontology-O3, bg_ontology-O4, bg_ontology-O5, bg_ontology-O6, bg_ontology-Idem.pattern, bg_ontology-Build.completion, bg_ontology-Earn.build_record, bg_ontology-Cost.baseline, bg_ontology-Vocab.alias, bg_ontology-Dens.served, bg_ontology-Carr.detector, bg_ontology-Earn.build_record, bg_ontology-G02, bg_ontology-Vocab.alias, bg_ontology-G07, bg_ontology-Dens.served, bg_ontology-G10, bg_ontology-Carr.D1, bg_ontology-G05, bg_ontology-Carr.detector]
---
# bg_ontology — Controlled vocabulary and identity authority (741 rows, 16 classes)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

The identity authority for everything later: 741 rows in `brahma_ontology` over exactly the 16 classes T2 §4.1 names (planet 11, sign 12, house 12, nakshatra 27, varga 30, karaka 77, aspect_type 13, upagraha 11, yoga 233, dosha 79, dasha_system 20, domain 45, concept 136, remedy_type 12, text 15, school 8), unique under the declared key `(entity_class, canonical_id)` (constraint `brahma_ontology_canonical_unique`; 730 distinct on `canonical_id` alone because 11 ids appear in two classes by design). The writer owns the classes outside `CO_WRITER_ENTITY_CLASSES = {yoga, dosha, dasha_system}` (`platform/python-sidecar/brahmagyan/l0_ontology.py:1066-1068`); those three are seeded by their own writers and written here DO NOTHING (332 of 741 rows by class count: yoga 233 + dosha 79 + dasha_system 20; the ledger row `bg_ontology-G01` says 327, which does not match its own class counts). Owned classes use a conditional upsert (`DO UPDATE … WHERE ROW(…) IS DISTINCT FROM ROW(…)`, `:1117-1145`) and PRUNE owned-class rows no longer in `ENTITIES` (`:1160-1173`), so it does not accrete; it reports `inserted = changed + deleted` (`:1183-1190`). Floor 737 against live 741. Declared dependents: `bg_dasha_systems`, `bg_doshas`, `bg_reference`, `bg_yogas` (census direct 4 / transitive 69, the widest in L0). Served by `list_entities.ts` and `resolve_entity.ts`. `source_citation` 741/741. The release/normalisation clause has no home today: the table has no release or version column (layer instance §2.6; TGH-T2-12).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:245` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py:15`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_ontology`; count_sql tables: `brahma_ontology` | census CEN-R |
| live rows / floor | 741 / 737 (Δ +4) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 4 / transitive 69 (every layer); named: `bg_dasha_systems`, `bg_doshas`, `bg_reference`, `bg_yogas` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_ontology`: 17 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `parity_check.ts`, `source_query_availability.ts`, `l0_brahmagyan.ts`, `kala_sky_pattern.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `list_entities.ts`, `resolve_entity.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Vocab | Vocab.alias | FAIL | 16 class(es); 79/741 row(s) lack an alias set (10.7%); empty alias sets: dosha 79/79 |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 2 module(s): list_entities.ts, resolve_entity.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=741 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = [] (declared no generated prose) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 741/741 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_ontology (brahmagyan/l0_ontology.py:1143 …); Vocab.identity (declared key (entity_class, canonical_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_ontology.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab FAIL · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_ontology-G01 | Earn | real (registry: count_sql credits co-writer rows) | 332 of 741 rows (233 yoga + 79 dosha + 20 dasha_system; the ledger says 327, not reconciled) are produced by `l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py`; CF-02 \| ledger: measured: count_sql returns 741, of which 327 rows are produced by l0_yogas.py, l0_doshas.py and l0_dasha_systems.py / required: the cockpit credits an asset with its ow… |
| bg_ontology-G02 | Build | real (T4 check 6); cause established as the changed-rows convention | rows_written = 0 on a converged rerun is what `l0_ontology.py:1183-1190` returns when nothing changed; the ledger’s "instrument the seeder" is not needed; CF-01 |
| bg_ontology-G03 | Vocab | stale (resolved by T2 amendment R03, 2026-09-26) | the rule-1 detector now tests the declared composite key; saved census Vocab.identity reads PASS (741 rows, 0 duplicates); closing needs the detector pass recorded, not an asset change \| ledger: measured: data plane 4.1 rule 1's detector is count(*) = count(DISTINCT canonical_id) ACROSS classes, which reports FAIL against data satisfying its own live constraint … |
| bg_ontology-G04 | Vocab | real (served surface) | `resolve_entity.ts` has `LIMIT 1` and returns `rows[0]` (`:68-71,92`): for the 11 ids present in two classes it silently picks ONE row (the ledger text says it returns two; the code returns one) by a hard-coded `ORDER BY (entity_class='varga') DESC` preference whose cited example (navamsa) exists in one class only; CF-09 \| ledger: measured: resolve_entity.ts returns two rows for the 11 ids present in two classes and applies a hard-coded ORDER BY (entity_class='varga') DESC preference — whose cited… |
| bg_ontology-G05 | Carr | detector | no D1 detector; CF-07 |
| bg_ontology-G06 | Dens/Earn | real (served assertion) | `list_entities.ts:23-41,109-115` states that `yoga` has no top-level class and omits `dosha` from `VALID_ENTITY_CLASSES`, against 233 and 79 live rows of those classes; a served reason that is false (CLAUDE.md §N.7 item 6) \| ledger: measured: list_entities returns empty_reason stating entity_class='yoga' has no top-level class in brahma_ontology, against 233 live rows with exactly that class; dosha … |
| bg_ontology-G07 | Vocab | real | 79/79 dosha alias sets empty; the code that writes them is `l0_doshas.py:2002` (bg_doshas); CF-09 \| ledger: measured: 79 of 79 dosha rows carry an empty synonyms array; the other 15 classes are complete / required: a non-empty closed alias set per entity |
| bg_ontology-G08 | Vocab | real | normalisation is not declared at the authority; 289 of 341 remedy source ids do not resolve exactly; CF-09 \| ledger: measured: normalisation is not declared at the authority; BPHS vs bphs is why 289 of 341 remedy source ids do not resolve / required: the normalisation rule declared onc… |
| bg_ontology-G09 | Complete / Vocab | real (reconciliation) | `text` class and corpus both hold 15 and differ by 3 each way (ontology-only: bhrigu_samhita, jaimini_sutram, lal_kitab_text; corpus-only: bhrigu_nandi_nadi, bphs_jaimini, nadi_navamsa_patel); no declared universe for 11 of 16 classes \| ledger: measured: no declared universe for 11 of 16 classes; the text class and the corpus both hold 15 members and differ by 3 in EACH direction (ontology-only: bhrigu_samhita,… |
| bg_ontology-G10 | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | 0 of 2 modules declare a density_contract; CF-04 \| ledger: measured: 0 of 2 capability modules serving this asset declare a density_contract (0 of 46 layer-wide) / required: declared where the capability paginates or facets |
| bg_ontology-O1 | NONE | opportunity | one resolvable identity for all 741 rows (three options a/b/c) \| ledger: the distinction added: one resolvable identity for all 741 rows, removing the defect class behind G03, G04 and the layer instance's mis-stated finding permanently |
| bg_ontology-O2 | NONE | opportunity | one producer per class, or declare multi-producer \| ledger: removes the provenance ambiguity behind G01: the identity authority currently has four writers |
| bg_ontology-O3 | NONE | opportunity | make yoga/dosha reachable (same as G06) \| ledger: makes 312 built rows reachable and declared (233 yoga + 79 dosha) — 58% -> 100% of rows reachable-and-declared |
| bg_ontology-O4 | NONE | opportunity | cost baseline \| ledger: a real cost baseline where none exists: rows_written=0 today for a 741-row table |
| bg_ontology-O5 | NONE | opportunity | derive the text class from the corpus \| ledger: fewer inputs and no drift: the text class duplicates what classical_text_chunks already knows, and the two have drifted by 3 in each direction |
| bg_ontology-O6 | NONE | opportunity | an identity contract between the ontology and the three catalogues \| ledger: one provable join instead of four assumed ones: bg_yogas, bg_doshas and bg_dasha_systems each seed identity rows here and keep their own catalogues |
| bg_ontology-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_ontology-Build.completion | Build | real (T4 check 6); same as G02 | CF-01 \| ledger: measured: build record says rows_written=0 against live=741 / required: the Build gate's claim |
| bg_ontology-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_ontology-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_ontology-Vocab.alias | Vocab | real | census FAIL: dosha 79/79 empty alias sets; same as G07 \| ledger: measured: 16 class(es); empty alias sets: dosha 79/79 / required: the Vocab gate's claim |
| bg_ontology-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | duplicate of G10 after folding (R81) \| ledger: measured: 2 module(s): list_entities.ts, resolve_entity.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_ontology-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_ontology-Carr.D1 | Carr | detector | same as G05 (folded) |

## 3 · Disposition

**enrich (E)** — agreed with the layer instance: the identity key is sound (Vocab.identity PASS under the declared key; T2 was amended by R03) but the authority still has an empty alias class, no declared normalisation, an unreconciled `text` class and two served-surface defects that make the vocabulary unreachable or ambiguous. The preserved kernel is the 741-row identity set; the changes are additive except the `text` reconciliation (an identity-mapping change).

Approver under Track A brief §10: **Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make the served vocabulary true and reachable (list_entities)

- **Answers:** ledger `bg_ontology-G06` / O3; layer instance exposure census (429/741 reachable-and-declared)
- **Change:** in `list_entities.ts` delete the false `UNBACKED_CLASSES` branch for `yoga`, add `yoga` and `dosha` to `VALID_ENTITY_CLASSES`, and correct the `empty_reason` text; keep `karana` unbacked only if it is (read the live class list first).
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/list_entities.ts:23-41,109-115`; the honesty test `list_entities_honesty_wp15.integration.test.ts` is updated in the same change
- **Failing-first test and mutation:** failing-first: a request for `entity_class=yoga` returns 233 rows and `dosha` 79 (fails today with `empty_reason`); mutation: restore the unbacked branch → test fails
- **Output change:** additive: two classes become listable (312 rows reachable)
- **Blast radius:** consumers of `list_entities` see more rows for two class filters; none identified that depend on the empty answer
- **Rebuild:** none (TypeScript serving surface)
- **Gate it moves:** Dens/Earn (a served assertion that can now read true), Reach
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent

### FD-2 · Class-aware resolution (resolve_entity)

- **Answers:** ledger `bg_ontology-G04` / O1(a)
- **Change:** resolve on the declared composite key: make `resolve_entity` accept and return an `entity_class` and, when a bare `canonical_id` is ambiguous (11 ids), return both rows explicitly (not an ordering that picks one by a hard-coded varga preference). Option (a) of the ledger’s O1 is the cheapest and matches the live constraint; (b) renames 11 ids, (c) adds a generated `global_id`. **Decided (SS 2026-10-01, Q4): take option (a); if it changes any served id, REVIEW to SS before landing.**
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts:50-70` and the consumers that join on `canonical_id` alone (found by the join census)
- **Failing-first test and mutation:** failing-first join census: every consumer join returns exactly one row for all 741 identities (11 are ambiguous today and are resolved by the silent varga-first preference); mutation: drop the class from a join → census FAIL
- **Output change:** none
- **Blast radius:** a read-path change in `resolve_entity.ts` (and any consumer joining on `canonical_id` alone, found by the join census). It changes served output only for the 11 two-class ids (today one row is picked silently); no data change; REVIEW to SS if any served id changes (Q4).
- **Rebuild:** none (TS) for option (a); (b) needs production rebuild of bg_ontology and its referrers
- **Gate it moves:** Vocab (rule 2)
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: Vocab rule wording / T2 §4.1 (TGH-T2-12 if a release id is added)
- **Decision:** ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.

### FD-3 · Normalisation rule in the bg_ontology writer; release id if cheap

- **Answers:** ledger `bg_ontology-G08`; layer instance §3.3 must-add (release id/digest); CF-09 (b)
- **Change:** decided (SS 2026-10-01, Q4): the normalisation rule (case/diacritic, ambiguous-alias list) lives in the `bg_ontology` writer, the one authority, and consumers (`bg_remedies`, `ephemeris_daily.body`) resolve through it with no stored-id rewrite; a vocabulary release (id + content digest) goes in the first wave if it is cheap, otherwise it is deferred. A release is additive metadata.
- **Files / declaration / migration:** the `bg_ontology` writer (`brahmagyan/l0_ontology.py`) holds the rule; consumers’ resolver; `bg_remedies` and `ephemeris_daily.body` are the first consumers (CF-09)
- **Failing-first test and mutation:** failing-first: remedy unresolved count 289 → the number the declared rule predicts (stated in advance: 52 exact + 204 case-only resolve = 256 resolved, 85 remain until the text class is reconciled); mutation: change the rule → the predicted count moves
- **Output change:** none
- **Blast radius:** a writer change in bg_ontology: the rebuild reproduces the same 741 ids (the normalisation rule and release are additive metadata). Consumers resolve through the rule: `bg_remedies` source ids, `ephemeris_daily.body` (46 non-test files read the table; they are not changed), `resolve_entity.ts`. The four declared dependents (`bg_dasha_systems`, `bg_doshas`, `bg_reference`, `bg_yogas`) rebuild only if a release column is added to a table they own.
- **Rebuild:** needs production rebuild of bg_ontology (additive release/declaration; no stored-id change), then dependents by level only if a release column is added
- **Gate it moves:** Vocab (rule 3)
- **Fix class:** data (output change) + registry/declaration; **buildable before J1:** tier-dependent: TGH-T2-12 (no tier defines a vocabulary release)
- **Decision:** ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.

### FD-4 · Reconcile the `text` class with the corpus

- **Answers:** ledger `bg_ontology-G09` / O5; CF-09 (c)
- **Change:** decided (SS 2026-10-01, Q4): derive the `text` class from the corpus at seed time (`l0_ontology.py:656-…`); add the 3 corpus-only ids (bhrigu_nandi_nadi, bphs_jaimini, nadi_navamsa_patel); for the ontology-only ids (bhrigu_samhita, jaimini_sutram, lal_kitab_text) keep any that has a consumer (a referrer census first) and remove the rest.
- **Files / declaration / migration:** `brahmagyan/l0_ontology.py` (text entries) ; `bg_texts` source manifest as the input
- **Failing-first test and mutation:** failing-first: the 1.1 cross-check returns 0 in both directions; mutation: add a text to the corpus only → the check reports it
- **Output change:** text class membership changes (+3 / ± 3)
- **Blast radius:** changes the `text` rows of `brahma_ontology` (owned by bg_ontology): +3 corpus-only ids and the ontology-only ids kept or removed. No DB foreign key REFERENCES `brahma_ontology` was found in either migrations directory; readers resolve at read time: `resolve_entity.ts`, `list_entities.ts` (text class), `platform-mcp/src/tools/l0_brahmagyan.ts`, `parity_check.ts`, `kala_sky_pattern.ts`. Beneficiaries: `bg_remedies` (5 source ids) and `bg_rules` (2 text_ids). Removing an ontology-only id changes `list_entities(text)` and anything resolving that id: the referrer census over those readers comes first (Q4: keep any with a consumer).
- **Rebuild:** needs production rebuild: bg_ontology (identity-mapping class); downstream `bg_remedies` and `bg_rules` text ids then resolve (they are the beneficiaries)
- **Gate it moves:** Vocab (rules 1, 3), Complete
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: TGH-T2-12
- **Decision:** ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.

### FD-5 · Producer attribution (count_sql scope)

- **Answers:** ledger `bg_ontology-G01` / O2; CF-02
- **Change:** scope the asset’s count_sql to the classes it owns (409 rows: 741 − 332) or declare the table multi-producer with a per-class producer map; the declarations file already marks the co-writer classes through `CO_WRITER_ENTITY_CLASSES`, so the map is derivable from code.
- **Files / declaration / migration:** registry row via a surgical migration + `asset_registry_seed.ts` literal
- **Failing-first test and mutation:** failing-first: per-class producer census; count_sql equals the writer’s declared row count (409); mutation: add a yoga row by the wrong writer → census FAIL
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 4 / transitive 69 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Earn (count_sql scope), Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent; vocabulary tier-dependent (TGH-T2-05)

### FD-6 · Build.completion: declare the changed-rows convention (CF-01 option A, R)

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** decided (SS 2026-10-01, Q1, R, PROVISIONAL until the J1 review): declare the changed-rows convention for this writer (the changed-rows convention is documented in `l0_ontology.py:1115-1145` and returned at `:1183-1190`); Build.completion then reads PASS only if the convention is declared AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
- **Files / declaration / migration:** `asset_declarations.json` entry (convention + writer `file:line`); the verdict rule is `platform/scripts/governance/asset_census.py` (E6 detector work); no writer change
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 4 / transitive 69 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration + detector rule; no rebuild)
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided; the criterion change is provisional until the J1 review)

### FD-7 · Carr detector — D1 on the cited rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** where a row’s `source_citation` names a corpus text, test the anchor terms (canonical name / Sanskrit name) against the cited chunk; rows citing non-corpus sources are reported unverifiable, not passed.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 4 / transitive 69 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-8 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `list_entities.ts`, `resolve_entity.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 4 / transitive 69 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows): option A decided (R). *This asset:* rows_written = 0 on a converged rerun
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* co-writer rows in count_sql
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* the identity/normalisation reconciliation lives here
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 2 modules; declared `[]` prose already

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(entity_class, canonical_id)` (census, 0 duplicates). Fingerprint over `(entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms, description, source_citation)` for the 409 owned rows; the co-writer classes (332) are fingerprinted by their own assets. Volatile: `created_at`. A release id, if added, is excluded from the fingerprint it identifies.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 741 identities with their composite key, the declared 16 classes and the co-writer arrangement; every id a downstream `fact_id` or consumer already resolves through.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence of the cited rows).
- **Opportunities (never blocking):** the six ledger opportunities `bg_ontology-O1…O6` (single resolvable identity; one producer per class; reachable yoga/dosha; cost baseline; derive the text class; an identity contract with the three catalogues).

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.
2. ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
3. CF-02: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch. ANSWERED by SS 2026-10-01 (Q19): scope `count_sql` to the primary table and declare the asset multi-table.
4. CF-09: ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
5. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
6. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

**Track I items arising (see INDEX section 8):** TI-L0-01, TI-L0-03, TI-L0-11, TI-L0-12, TI-L0-13, TI-L0-14, TI-L0-15.
