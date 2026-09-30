---
artifact: SUVARNA_L1_TIER_GAPS
canonical_id: SUVARNA_L1_TIER_GAPS
version: "1.0"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L1i step 2 (tier-gap file; written before the instance)"
layer: "L1 Gaṇita (19 active assets, ga_*)"
census_run:
  output: /Users/Dev/suvarna-evidence/census/census_L1.json   # + census_L1.log, SUMMARY.md beside it
  exit_code: 2            # 2 = FAIL cells present = MEASURED (arch §12.14); SUMMARY.md
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57
  generated: "2026-09-30T20:22:28+05:30"
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
  login: "suvarna_reader via proxy 127.0.0.1:5433; no --emit-gaps"
tiers_read_at: "/Users/Dev/suvarna-census, detached at 2a78ec64d (origin/campaign/nikasha-test)"
code_read_at: "origin/main e2352f881751deced2dc089451ef676db0aac5d5 (this worktree), platform/python-sidecar"
inputs_checked_not_trusted:
  - 00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/L1_INSTANCE_SKELETON.md
  - 00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/L1_INVENTIONS.md
changelog:
  - "1.0 (2026-09-30): first issue. 23 tier gaps (Part A), 2 L1 layer gaps and 12 measurement findings that are not tier clauses (Part B), and the disposition of every earlier L1 invention row against the tiers (Part C). Written by the Sonnet analyst of lane A.L1i; may register gaps, may not certify."
---

# L1 Gaṇita — tier gaps (A.L1i)

**How to read this file.** A gap row (`TG-L1-nnn`) means: the tier-3 template asks the L1 instance for something, and after
searching tiers 1, 2, 3 and 4 no clause supplies it, so the instance carries "TIER GAP" there instead of an invented
answer. Where the change register (`NIKASHA_CHANGE_REGISTER_v2_0.md` v2.8) already has the row, the gap **cites** it and
adds only what this census run and code read added. Part B holds things that are true of L1 but are not failures of a
tier clause (a code residual, measurement findings); they are here because the brief asks for them, not because a tier
must change. Part C answers the instruction to check each earlier invention row against the tiers.

**Tier assignment** is the tier whose text has to change (or gain a clause) for the gap to close; a "also" names a second
tier the same fix touches. Assignment follows the register's own reopen agenda where the register row states one.

Abbreviations: T1 `MADHAV_PRODUCT_DEFINITION_FINAL.md`; T2 `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`; T3
`LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`; T4 `ASSET_ELEVATION_TEMPLATE_v2_0.md`; "R" = a register row;
"census" = `census_L1.json` (field path `L1.assets[*].measurements["<criterion>"]`).

## Index

| id | clause that failed to provide | tier | register |
|---|---|---|---|
| TG-L1-001 | T3 §0.1 — P/V rows this layer is necessary for | T3 | R221 (open), R85 (closed, tool), R100, R130 |
| TG-L1-002 | T3 §0.2 — "what it computes that existing software does not" | T3 | R101, R131 |
| TG-L1-003 | T3 §0.3/§1.1 — seed, migration pin and live reconciliation | T3 | R86, R102, R132 |
| TG-L1-004 | T3 §1.1/§4.1 — deployed vs current-code baseline | T3 | R87, R104 |
| TG-L1-005 | T3 §1.1 / T2 §7.1 — one table, several producers | T2 | R06, R10, R95 |
| TG-L1-006 | T3 §5.2 Idem row / T4 L1 row — natural key on a shared table | T3 | R96 |
| TG-L1-007 | T4 §0 — `kind` of a writer-backed data asset with no declared target | T4 | R97 |
| TG-L1-008 | T4 §4.2 check 6 — writer-backed asset that is empty | T4 | R99, R126 |
| TG-L1-009 | T3 §1.4/§2.3 — consumer-side verification and declared use | T3 | R106, R109 |
| TG-L1-010 | T3 §2.1 — a detector per correctness rule; the L1 switch rule | T2 | R88 (narrowed), R117 |
| TG-L1-011 | T3 §2.2/§5.4 test 4 vs T2 §1/§12.2 — presentation parity | T3 | R71, R94 |
| TG-L1-012 | T2 §3.4/§13.3 item 6 — which presentation rows L1 carries | T2 | R89 |
| TG-L1-013 | T3 §2.4 / T2 §5 — coverage obligations L1 owns and their universes | T2 | R90, R22, R98 |
| TG-L1-014 | T3 §2.6 / T2 §4.1 — entity classes L1 emits; per-class map census | T2 | R91 |
| TG-L1-015 | T3 §2.7/§4.4 row 13 — per-asset carriage check (a/b/c, D1–D3) | T3 | R09, R92 |
| TG-L1-016 | T3 §2.5 — frozen definition revision, egate.sql, edge list | T3 | R113, R86 |
| TG-L1-017 | T3 §3.2/§4.4 — evidence→disposition rule; the preserved kernel | T3 | R93, R116 |
| TG-L1-018 | T3 §4.4 / T4 §0 — the temporal or manifestation role per asset | T4 | R120 |
| TG-L1-019 | T3 §5.2 gate map — per-asset right-hand column at layer scale | T3 | none — new |
| TG-L1-020 | T2 §3.3 — type every L1 output by epistemic kind | T3 | none — new |
| TG-L1-021 | T3 §5.2 / T4 §4 — the Ldgr claim for a layer that reads no upstream `fact_id` | T3 | none — new |
| TG-L1-022 | T1 §14 — computational correctness "where required", sensitivity, "declared tolerance" | T1 | none — new |
| TG-L1-023 | T3 internal references met while filling (§7, order, "six", "eight-row") | T3 | R08, R65, R67 |

**Count by tier (primary): T1 1 · T2 5 · T3 14 · T4 3 = 23.** New (no register row) 4; duplicates of a register row 19.

---

## Part A — tier gaps

### TG-L1-001 — the per-layer necessity set over P and V
- **Clause:** T3 §0.1 (lines 99–116): "List the P-needs and V-journeys for which this layer is necessary — not 'involved in', … but cannot be answered without."
- **Needed:** the P/V rows L1 is necessary for, one line each. Searched T1 §2 (P01–P24), §11 (line 501), T2 §2 (V01–V13), §3.1 (line 140), §5, §7.1: **no table maps any P or V to a layer.** Tiers name L1 explicitly for only these: T1 §11 (the whole-layer proof row), T2 §5 "Graha contextual roles" (line 327, "L1 computed roles/placements") and "Ayurdaya and constitution" (line 338, "L1 ayurdaya computed under each applicable school", which serves V12/P23), T2 §12.1 (line 582, "L1 supplies actual positions, conditions, divisions, formation and clocks"), T2 §9.2 (line 500, "L1 separate event-time context"). The instance lists only those.
- **Evidence:** registry `asset_registry.depends_on`, read 2026-09-30: 25 active non-L1 assets (L2 9, L3 14, L4 1, L5 1) declare a direct edge to at least one `ga_*` asset (46 edges); census `L1.assets[*].blocking_radius`: 13 of 19 L1 assets have downstream dependents and 6 have 0/0 (`ga_ayurdaya`, `ga_medical`, `ga_prashna`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vastu`). That is a build-graph reach, not a necessity statement.
- **Tier:** T3 (the clause). **Register:** R221 (T3 §0.1 re-scoped to catalog units and the necessity closure, OPEN on the T3 agenda; the sealed text this run read is unchanged), R85 (the closure tool, CLOSED); the same clause for other layers is R100, R130.

### TG-L1-002 — "what it computes that existing software does not"
- **Clause:** T3 §0.2 (line 126): "Name what it computes that existing software does not."
- **Needed:** an L1-specific statement. T1 §1 (lines 51–56) and T2 §1 (lines 62–67) state the contrast at product/plane level ("a varga when asked for it, a daśā table when asked for it … Madhav computes the whole estate and … the relationships between its parts"); T2 §3.1 (line 140) gives L1's contribution and its "must not claim". The instance quotes these. What no tier supplies is any way to establish that a given L1 computation is one "existing software does not" produce: there is no baseline, no software named, and T1 §13 forbids an invented claim.
- **Evidence:** searched T1–T4 for a competitor baseline or an instrument for it; none. Census has no field for it.
- **Tier:** T3. **Register:** R101 (L2) and R131 (L3) are the same clause; there is no L1 row, so this cites them.

### TG-L1-003 — three-way reconciliation of the dependency graph
- **Clause:** T3 §0.3 (lines 133–145) and §1.1 (lines 161–175): "registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three."
- **Needed:** the seed reading and the migration-pin reading beside the live one. Searched T1–T4: T3 §0.3 and §1.1 (line 165, "the registry seed · the migration-governed pin") **name** them; no tier says where either lives or how it is read. The census emits only the live edge counts (`Build.dag`).
- **Evidence:** live registry read 2026-09-30: 45 edges among the 19 assets (40 inside L1, 5 to L0). Partial code reading only: writer classes declare `depends_on` for 2 of 19 (`pipeline/orchestrator/writers/ga_vichara.py:46`, agrees with the registry; `ga_structural.py:21`, `['ga_nakshatra']` where the live registry carries seven edges and the file's own comment defers to the registry). Migration history for one edge is visible: 416 added `ga_structural → ga_condition`, 419 removed it; the live registry has no such edge. No seed/pin comparison was made for the other 18 assets: **not measured** (would need replaying 176 registry-touching migrations).
- **Tier:** T3. **Register:** R86 (L1's own row, OPEN), R102 (L2), R132 (L3).

### TG-L1-004 — the deployed-vs-current-code half of the baseline
- **Clause:** T3 §1.1 (lines 172–175) and §4.1 (lines 431–435): "whether current code on any live head differs from what is deployed"; delta = target − current code, risk = current code − deployed.
- **Needed:** per asset, the deployed structure, the newest code "on any live head, including unmerged", and their difference. Neither T3 nor T4 §1 defines "live head", and the census has no code-head field.
- **Evidence:** this run read one head (origin/main e2352f881). Another head holds relevant L1-adjacent work: commit 8edba0533 ("engine A1", the register's R34 fix) is contained in `origin/campaign/nirmana-engine` and not in `origin/main` (`git branch -a --contains 8edba0533`); migration 1094, which the census names as the absent instrument (`Earn.build_record` text), is not in `origin/main`'s migration directory. So the current-code side differs by head and the instance can state only the main-head reading.
- **Tier:** T3. **Register:** R87 (L1's row, OPEN), R104 (L2).

### TG-L1-005 — one table, several producers
- **Clause:** T3 §1.1 (lines 161–175) — "target table(s) — a set, not one pointer, for multi-table assets" (many tables per asset; nothing for many assets per table); T2 §7.1 (line 410 onward) has no clause for a shared table's producers either.
- **Needed:** for `chart_facts` (declared target of seven L1 assets; also written by three more), who owns the count, how `count_sql` is scoped per producer, and which asset's Build check answers for the table.
- **Evidence (registry and queries at chart 482012f1, 2026-09-30):** `asset_registry.target_table = 'chart_facts'` for 7 assets (`ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`), each with a `natural_key_partition` text and a partition-scoped `count_sql` (census `live_rows`: 130 / 2,847 / 437 / 1,205 / 6,287 / 8,775 / 335); `ga_strength` and `ga_structural` have `target_table` NULL but write `chart_facts` (registry `count_sql`); `ga_condition` writes `chart_facts` and `ga_condition_composite`. `chart_facts` holds 143,299 rows for the chart. `fact_category_ownership` (67 category rows) names only three owners: `ga_structural` 64, `ga_ayurdaya` 1, `ga_condition` 2; joined to the chart's rows it owns 102,037 + 130 + 90 rows and leaves **41,042 rows with no owner row**. Overlap: the `ga_strength` `count_sql` predicate matches 420 rows that `fact_category_ownership` assigns to `ga_structural` (and `ga_condition`'s `count_sql` claims 2,925 `chart_facts` rows where the ownership table gives it 90). Whether the partitions are disjoint and complete over the 143,299 rows is **not measured**. The census's `Complete.depth`, `Ldgr.source_presence` and `Vocab.identity` cells for these assets are still computed over the whole table (421,096 rows, all charts), see MF-L1-002.
- **Tier:** T2 (R06 puts the clause in T2 §7.1 or §13.3; also T3 §1.1). **Register:** R06, R10, R95.

### TG-L1-006 — the natural key on a shared table (Idem)
- **Clause:** T3 §5.2 gate map, Idem row (line 575, "the asset's natural key, so 'replaces its own rows' is decidable"); T4 "Adapting per layer", L1 row (line 505, "`Idem` is delete-then-insert on chart × natural key").
- **Needed:** the natural key per asset and, for `chart_facts`, each writer's delete scope. No tier states either.
- **Evidence:** code, not tier: `ga_writers/_idempotency.py` lines 3–6 record that the tables' unique keys **include `build_id`** (`chart_facts`: chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id; `chart_dashas`: chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id), so replacement is done by the writer's delete, scoped by categories/systems/vargas *present in the rows about to be written* (lines 44–105). Census `Idem.pattern` = PASS for 19/19 (static pattern check). The earlier skeleton's PARTIAL for `ga_nakshatra` (ON CONFLICT) is gone at inspector 2a78ec64d. See MF-L1-004 for what the static check cannot see.
- **Tier:** T3 (also T4). **Register:** R96.

### TG-L1-007 — the `kind` of a writer-backed data asset with no declared target
- **Clause:** T4 §0 (line 74): `kind: data | service (no table by design) | multi-table | rider (producer_covered) | static (migration-seeded)`.
- **Needed:** a kind for `ga_strength` (writes a partition of `chart_facts`, target NULL) and `ga_structural` (target NULL, `count_sql` over two tables). Neither fits `data`-with-target, `multi-table` as a declared set, nor `rider`.
- **Evidence:** registry `target_table` NULL for both (query above); census `Build.target` now reads PASS for both with explanatory text ("no target_table: writes a partition of chart_facts…", "a multi-table asset whose count_sql declares the 2 tables it produces"): the engine's rule was fixed (R53 CLOSED) but the vocabulary in T4 §0 was not.
- **Tier:** T4. **Register:** R97, R14.

### TG-L1-008 — a writer-backed asset that is empty
- **Clause:** T4 §4.2 check 6 (line 277) — covers "a populated table" and "a service"; the empty writer-backed data table is a third case no clause covers, and no tier provides "empty by design" as a declarable state.
- **Needed:** a verdict rule for `ga_prashna` (state `lit`, `rows_written` 0, 0 chart rows) and for `ga_vargas` (state `lit`, `rows_written` 24,400, **0 chart rows now**).
- **Evidence:** census `ga_prashna`: `Build.completion` ERRORED (see MF-L1-001), `Count.floor` N/A (`target_floor=0`), `Complete.depth` and `Vocab.identity` NO_DETECTOR (table empty), `Dens.served` N/A (0 modules); registry `data_disposition = RETAINED_AS_CAPITAL`. `ga_vargas`: `Build.completion` FAIL and `Count.floor` FAIL (live 0, floor 22,092); `asset_throughput` for the chart says `lit` / 24,400 (LG-L1-002).
- **Tier:** T4. **Register:** R99 (PARTIAL: the by-design detector and ga_prashna's case carried), R126 (L2's same case).

### TG-L1-009 — consumer-side verification of produced contracts, and declared use as data
- **Clause:** T3 §1.4 (lines 215–226, "verified at the consumer, not asserted by the producer") and §2.3 (lines 288–299, "A citation with no declared use is not a contract"); T2 §7.1 (line 416).
- **Needed:** for each contract L1 produces, the evidence-state position at the consumer, and for each consumed input its declared use. No tier assigns L1 assets to DP contracts; the registry has no `produces_contracts`/`consumes_contracts` field; the census measures producer-side presence and capability-module reach (`Reach.fields`, `Dens.served`), not consumer reads.
- **Evidence:** registry columns (list read from `information_schema`) carry `depends_on` only; census `Reach.fields` is NOT_GENERIC ×19 ("reported, not graded"). The instance's asset-to-contract mapping is by asset name and is labelled as such.
- **Tier:** T3. **Register:** R106, R109.

### TG-L1-010 — a detector per correctness rule; the L1 switch rule
- **Clause:** T3 §2.1 (lines 261–272): "**For each rule, the detector.** A rule with no detector is a wish."
- **Needed:** a detector for T1 §8.1's L1 row ("Altering birth facts or chart calculations to fit biography") and for the T1 §13 / T2 §6.2 rules. **Narrowed from R88:** T2 §9.2 (lines 493–517) *does* supply the switch — its ON row lists "L1 separate event-time context", the OFF row "nothing derived from life events", and lines 510–512 the storage separation; T2 §6.2 (line 359) adds "separate context identities". What no tier supplies is (a) a detector for the §8.1 rule and (b) what an event-time context's identity is.
- **Evidence:** census has no criterion for it; the instrument named for the neighbouring rule is not the same claim: FORENSIC anchor gates exist in code (`forensic_gate(` in `ga_positions_writer.py:635`, `ga_strength_writer.py:1808`, `ga_structural_writer.py:6802,8040`, `ga_sensitive_writer.py:2709,3153`, `panchanga_forensic_gate` in `ga_panchanga_writer.py:1385`, `forensic_gate_vargas` at `ga_vargas_writer.py:2790`) but they test that birth anchors reproduce, not that no biography touched a fact. Whether any registered L1 asset writes an event-time context: **not measured** (the 19 registry assets are natal or method services; none is named as event-time).
- **Tier:** T2 (also T3 §2.1). **Register:** R88 (its "T2 §9.2 gains a per-layer table" text is partly already satisfied), R117 (a detector registry per layer rule).

### TG-L1-011 — presentation parity: own work or [TRANSFERS]
- **Clause:** T3 §2.2 `measured_by` (line 279) and §5.4 test 4 (line 628) against T2 §1 (lines 83–85) and §12.2 (line 614).
- **Needed:** whether L1's instance owns the parity test. T3 demands it before acceptance; T2 says a layer plan does not inherit a [TRANSFERS] obligation as its own work.
- **Evidence:** both texts unchanged in the sealed files this run read.
- **Tier:** T3 (also T2's tag). **Register:** R71 (remedy fixed by ruling D3, not yet applied), R94.

### TG-L1-012 — which presentation rows L1 carries
- **Clause:** T2 §13.3 item 6 (line 682): "including which §3.4 presentation rows this layer carries and which fields it hands onward for them."
- **Needed:** an assignment of the eight §3.4 rows to layers. T2 §3.4 (lines 188–197) maps rows to contracts and T2 §7.1 maps contracts to producers; the instance derives L1's rows by joining the two (labelled as a join, not a statement). The join is clean for conventions (DP01 L0 / DP03 L1), intermediate quantities (DP03/DP04) and dignity/strength components (DP04). It is **not** clean for DP05 ("L0+L1 → L2") and DP07 ("L0/L1/L3 primitives"): which fields are L1's is unstated.
- **Evidence:** T2 §7.1 lines 421–426.
- **Tier:** T2. **Register:** R89.

### TG-L1-013 — coverage obligations L1 owns, and their declared universes
- **Clause:** T3 §2.4 (lines 301–311); T4 §1.1 (lines 145–162, "declare the universe first").
- **Needed:** the list of obligations L1 owns, each with the five-state result, and for each width/depth a declared universe. T1 §3 names substance (graha roles, bala, varga, nakshatra/KP, ārūḍha, daśā, pañcāṅga…); T2 §5's obligation table names L1 in two rows only (lines 327, 338). Ownership by layer is unstated.
- **Evidence:** census `Complete.width` = NOT_GENERIC for 19/19 ("no declared universe for this asset — declaring one is the first width gap"); `Complete.depth` is measured but over the whole table for the 8 chart-table assets.
- **Tier:** T2 (also T4 §1.1: who declares a universe, layer or brief). **Register:** R90, R22, R98.

### TG-L1-014 — entity classes L1 emits, and the independent-map census
- **Clause:** T3 §2.6 (lines 313–328); T2 §4.1 rules 1, 5, 6 (lines 259–266).
- **Needed:** which of the sixteen classes (T2 §4.1 "Scope", lines 268–271: planets, signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems, domains, concepts, remedy types, texts, schools) L1 emits or accepts; alias coverage; independent maps per class.
- **Evidence:** census `local_map_candidates` = **-1** (top-level field of `census_L1.json`: the instrument returned a non-result); `Vocab.identity` measures only declared-key duplicates (15 PASS, 2 NO_DETECTOR on empty tables, no cell for 2 assets), which is rule 1(i) alone; rule 1(ii) alias sets, rule 4 parity tests and rule 5 interface enums have no L1 cell. In code, `brahmagyan/verification_vocab.py` is a real controlled vocabulary for one field (`verification_pass_status`, 13 members, `single_pass` a deprecated alias of `single`), which shows the mechanism exists for that field only.
- **Tier:** T2. **Register:** R91.

### TG-L1-015 — the carriage check per asset
- **Clause:** T3 §2.7 (lines 330–363, "For each obligation the layer owns (§2.4), state which of a–c applies") and §4.4 row 13 (line 478); T4 L1 row (line 505): "`Carr` D3 dominates".
- **Needed:** per asset, the Jyotish concept and the one carriage check (D1 source correspondence, D2 witness carriage, D3 independent re-derivation). The tier supplies a layer-level hint only, and it does not cover every L1 asset: T2 §5 (line 338) makes āyurdāya a matter of "the disagreement between authorities" (D2), and T2 §3.3 (line 176) says L1 includes "specialized rule applications" (D1). Assigning a check per asset is content, not derivable from a hint.
- **Evidence:** census `Carr.detector` NO_DETECTOR for 19/19 ("which check applies is per-asset semantics"). Existing code that is a D3-shaped check but is not in the census: `ga_writers/_vimshottari_independent_verifier.py` (1,483 lines, an independent Vimshottari levels 1–4 re-derivation for `ga_dashas`).
- **Tier:** T3. **Register:** R09 (C-9, confirmed on all five layers), R92.

### TG-L1-016 — the frozen definition revision and the edge list
- **Clause:** T3 §2.5 (lines 365–375): "cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision"; "State the frozen definition revision the gate was evaluated against".
- **Needed:** a definition revision and an egate reading. `egate.sql` exists (`platform/scripts/nirmana/egate.sql`) but reads `nirmana_evidence.nirmana_elevation_campaign_definitions` (the Nirmāṇa campaign's frozen manifest); the Suvarṇa plan v1.5 and architecture v1.5 do not carry a "frozen definition revision" concept (searched by phrase). Not run: it is the superseded campaign's gate.
- **Evidence:** intra-L1 order was computed from the live registry (no cycle; six levels 0–5, see instance §2.5); the census reports only edge counts.
- **Tier:** T3. **Register:** R113 (L2's row for the same clause), R86.

### TG-L1-017 — the rule from evidence to disposition, and the preserved kernel
- **Clause:** T3 §3.2 (lines 396–406) and §4.4 (line 477); T2 §10.1 (lines 531–544); T4 §0.1 row 12.
- **Needed:** T2 §10.1 gives the eight-letter hierarchy and "smallest sufficient change"; T3 §3.2 asks for "the evidence from Part 1 that justifies it". No tier maps census evidence to a letter, and no tier says where the "preserved kernel" ("what must survive any rebuild unchanged") is declared. The Track A brief (§5) places dispositions in a separate `L1_DISPOSITIONS_v1_0.md` (A.L1), so the instance records evidence per asset and leaves the letter to that file.
- **Evidence:** registry columns `natural_key_partition` and `data_disposition` exist (among the 19 `ga_*` rows: 7 and 1 non-null values respectively) but are not a kernel declaration.
- **Tier:** T3. **Register:** R93, R116.

### TG-L1-018 — the temporal or manifestation role per asset
- **Clause:** T3 §4.4 (line 476, "its manifestation or temporal role"); T4 §0 (line 76, `role: manifestation | temporal | neither`).
- **Needed:** a role per L1 asset. T2 §6.2 (line 355) supplies it for four names ("Daśā, transit-anchor, pañcāṅga, Tājaka and specialized services provide time and method-specific foundations") and T2 §7.1 DP07 for clocks; nothing assigns the other assets.
- **Tier:** T4 (also T3 §4.4). **Register:** R120 (L2's form of the row).

### TG-L1-019 — the gate map's right-hand column, at layer scale
- **Clause:** T3 §5.2 (lines 567–585) and §5.4 test 5 (line 629): the instance "fills the right-hand column" of a nine-row map (natural key, upstream `fact_id` sources, emitted claims, null convention, classes, concepts, prose emission, served surface, build record) and "reports any row it cannot fill".
- **Needed:** clarity on whether the instance carries those cells **per asset** (19 × 9 = 171 cells) or per gate. T3 says "the asset's …" in every row, which is per asset; the instance is a layer document, and T4 §0.1 says each brief inherits from instance §4.4.
- **Evidence:** the instance fills the cells the census, registry and code supply (Build, Idem, Dens, Ldgr partly) and marks the rest per gate with this row.
- **Tier:** T3. **Register:** none (R65, R67 concern only the row count).

### TG-L1-020 — typing every L1 output by epistemic kind
- **Clause:** T2 §3.3 (line 176): L1 outputs are to be typed as "astronomical calculation, classical-rule application, engineered/native judgment, approximation, observation or empirical/model result. Being in L1 does not make every field an equally verified numerical fact."
- **Needed:** a per-asset (or per-field) type and a home for it in the layer template. T3 has no section that receives it (nearest: §2.7 and §4.4). T2 itself names one case (`ga_vichara`, "judged structure") and says "specialized rule applications and temporal products" exist; it assigns no other asset.
- **Evidence (code, not tier):** `ga_writers/data_plane_contracts.py:48–55` defines an `EpistemicClass` of seven members (`astronomical`, `deterministic_derivation`, `rule_derived`, `judged`, `documented_approximation`, `engineering_fixture`, `restricted_scholarly`) that differs from T2's six named kinds (`observation` and `empirical/model result` are absent from it; `deterministic_derivation`, `engineering_fixture`, `restricted_scholarly` are absent from T2). Grep of `platform/python-sidecar` (tests excluded) finds `epistemic_class` only in `data_plane_contracts.py` (fields at 224 and 291) and `data_plane_resource_config_slice.py:92` (built from a fixture spec); none of the `ga_*_writer.py` files assigns one.
- **Tier:** T3 (T2 §3.3 is the demand). **Register:** none — searched R-rows for "epistemic", "engineered", "approximation": no match.

### TG-L1-021 — the Ldgr claim for a layer whose inputs are birth parameters and L0, not `fact_id`s
- **Clause:** T3 §5.2 Ldgr row (line 531): "every derived value names the upstream `fact_id` it reads, and those ids resolve"; T4 §4 Ldgr row (line 224): the same, "for a reference layer, every row names its *source*".
- **Needed:** what an L1 root asset names. `ga_positions` has `depends_on = {}` (registry); its inputs are birth parameters and L0 constants, not fact rows. Neither T3 nor T4 gives a third form of the claim for a computed layer whose root has no upstream `fact_id`.
- **Evidence:** `chart_facts` has no column that holds upstream fact identifiers (25 columns read from `information_schema.columns`: `citation_ref`, `citation_human`, `source_calculation`, `formula_id`, `formula_provenance_text` are the provenance columns); the only Ldgr cell in the census is `Ldgr.source_presence` (`citation_ref`/`source_citation` populated), which is the **reference-layer form**, PASS for 13 of 19 and **absent (no cell at all)** for `ga_condition`, `ga_prashna`, `ga_strength`, `ga_structural`, `ga_transit_anchors`, `ga_vargas`. `ga_writers/data_plane_runtime.py` shows a generation-and-partition ledger exists in code (migration 1035, tables `l1_data_plane_*`), but the reader login cannot read it (MF-L1-012).
- **Tier:** T3 (also T4 §4). **Register:** none for the claim; R128 records only that L2 verdict cells are silently missing.

### TG-L1-022 — computational correctness: "independent verification where required", sensitivity and "declared tolerance"
- **Clause:** T1 §14 (line 588): Computational correctness — "Authoritative inputs, reproducible calculations, units and conventions, sensitivity, independent verification where required"; T3 §2.7 check c (line 356): "beyond a declared tolerance"; T2 §12.2 (line 612, 613, 629): thresholds are "predeclared" by layer/asset briefs.
- **Needed:** for L1's one scored obligation, which outputs *require* an independent verification, what sensitivity is owed, and who declares the tolerance. T3's own rule ("derivable from tiers 1–2 without inventing a criterion", lines 28–31) means an instance may not declare them; T2 delegates them to the briefs; T1 leaves "where required" open.
- **Evidence (chart 482012f1, 2026-09-30):** `chart_facts.verification_pass_status`: `single` 115,807 · `single_pass` 10,836 (a deprecated alias of `single`) · `two_pass_verified` 9,320 (6.5% of 143,299) · `computed_extension` 3,855 · `floored` 2,365 · `documented_approximation` 1,020 · `pending_w3_verification` 50 · `not_defined_for_nodes` 32 · `classical_match` 14. `chart_dashas`: `single` 437,474 · `two_pass_verified` 46,009 (9.5% of 483,870) · `classical_match` 386 · `scope_cap_sentinel` 1. `tolerance_arcsec` is populated on 8,775 of 143,299 `chart_facts` rows (6.1%; the count equals `ga_sensitive`'s live rows, an equality this run did not trace to cause); rows flagged near a sign boundary 725, near a nakshatra boundary 657. The vocabulary's own rule (`brahmagyan/verification_vocab.py`): only `two_pass_verified` counts as grounding. Census `Carr.detector` is NO_DETECTOR ×19.
- **Tier:** T1 (T1 §14 says "where required"; T2 §12.2 and T3 §2.7 depend on it). **Register:** none — searched for "where required", "sensitivity", "second derivation", "independent verification": no match (R55 concerns a different "sensitivity direction").

### TG-L1-023 — internal references in T3 that a filler trips over
- **Clause:** T3 line 585 ("Report unfillable rows in §7", a section T3 does not have); §2.6 and §2.7 are ordered before §2.5; line 539 ("six static checks") vs T4 §4.2 (nine); line 629 ("eight-row map") vs the nine-row table at lines 572–582; line 522 ("9 × 129 assets") vs 127 active assets measured (SUMMARY.md: L0 40 · L1 19 · L2 23 · L3 21 · L4 9 · L5 15).
- **Effect on this draft:** the instance carries its unfillable rows in a closing "Corrections with gates" section (as the L0 v3.0 draft did, its own addition) and writes a nine-row gate map. For L1 the asset count (19) agrees with the registry; only the cross-layer figure differs.
- **Tier:** T3. **Register:** R08 (§7 and the order), R65 ("six" checks), R67 ("eight-row"); the 129-vs-127 figure is R220's (active population 127).

---

## Part B — L1 layer gaps and measurement findings (not tier clauses)

### LG-L1-001 — the eight `ga_*` call sites that still go through `ga_writers/_telemetry.py` (R34 residual)
Register R34 (CLOSED_ON_BRANCH; residual OPEN): "the legacy `ga_writers/_telemetry.py` path — 8 `ga_*` call sites (ga_dashas, ga_panchanga, ga_positions, ga_strength, ga_sade_sati, ga_sensitive, ga_tajaka, ga_structural) still write NULL". Found by grep of `platform/python-sidecar` (tests excluded) for calls to `update_asset_throughput(`, at origin/main e2352f881. There are exactly eight direct call sites, one per named writer:

| # | asset | direct call to `update_asset_throughput` | caller that reaches it | guard at the caller | orchestrator wrapper hands the writer `conn=` |
|---|---|---|---|---|---|
| 1 | ga_dashas | `ga_writers/ga_dashas_writer.py:3078` (inside `_update_asset_throughput`, def at 3067) | `:3307` and `:3575` | `:3307` under `if owns_conn` (3306); `:3575` inside `build_ga_dashas` (def 3492), the CLI-shaped entry the wrapper's comment at `ga_dashas.py:50` names as the CLI path | `pipeline/orchestrator/writers/ga_dashas.py:47,54,60` `conn=ctx.db_conn` |
| 2 | ga_panchanga | `ga_writers/ga_panchanga_writer.py:1315` | `:1481` | `if owns_conn` (1480) | `writers/ga_panchanga.py:20` |
| 3 | ga_positions | `ga_writers/ga_positions_writer.py:693` | `:668` | `if owns_conn` (667); comment 665–666 "only the legacy standalone CLI (owns_conn) writes it here via _telemetry" | `writers/ga_positions.py:33` |
| 4 | ga_sade_sati | `ga_writers/ga_sade_sati_writer.py:1876` | `:2152` | `if owns_conn` (2151) | `writers/ga_sade_sati.py:20` |
| 5 | ga_sensitive | `ga_writers/ga_sensitive_writer.py:3038` | `:3240` | `if owns_conn` (3239) | `writers/ga_sensitive.py:44` |
| 6 | ga_strength | `ga_writers/ga_strength_writer.py:1961` | `:1941` | `if owns_conn` (1940) | `writers/ga_strength.py:20` |
| 7 | ga_structural | `ga_writers/ga_structural_writer.py:8143` | `:6896` | `if owns_conn` (6895); comment 6893–6894 as for ga_positions | `writers/ga_structural.py:39` |
| 8 | ga_tajaka | `ga_writers/ga_tajaka_writer.py:835` (direct) | — | `if owns_conn` (833); import line 48 comment "legacy CLI path only; orchestrator never calls this" | `writers/ga_tajaka.py:20` |

What this run found that the register row does not say: (a) **every one of the eight is on the legacy standalone path** (`owns_conn`, i.e. no connection passed); the orchestrated wrappers pass `conn=ctx.db_conn`, so by reading the code the eight sites do not execute under the orchestrator (no run was made); (b) `_telemetry.update_asset_throughput` (file lines 40–60) writes `state`, `rows_written`, `last_measured_build_id` and timestamps and **does not write `rows_per_second` or any duration** — it does not time anything, so "still time through" is not what the file does; (c) the NULL rate is therefore explained by the absence of engine timing on this head, not by these sites: `rows_per_second` is written nowhere in `platform/python-sidecar/pipeline/`, only defined in migration 169 (`grep`), and the engine's A1 commit is off `main` (TG-L1-004); (d) `asset_throughput.rows_per_second` for the chart is NULL on 19 of 19 L1 rows (query 2026-09-30); (e) a ninth definition, `ga_vargas_writer.py:2779` `_update_asset_throughput`, is a documented no-op that does not import `_telemetry`. The eight are still a residual against §N.2's "orchestrator is the sole `asset_throughput` writer" for the legacy path; whether they should be removed or kept as the CLI's is a design question for A.L1's briefs, not decided here.

### LG-L1-002 — `ga_vargas`: build record says `lit` with 24,400 rows, the chart holds 0
Census `ga_vargas`: `Build.completion` FAIL ("empty: live=0 … target_floor=22092; build record rows_written=24400"), `Count.floor` FAIL (live 0, floor 22,092, delta -22,092), `Complete.depth` and `Vocab.identity` NO_DETECTOR. Query 2026-09-30: `chart_divisionals` has 0 rows for chart 482012f1; `asset_throughput` for the chart reads `state = lit`, `rows_written = 24400`, last built 2026-09-07. Build history for the chart (`build_run_assets` ⋈ `build_runs`, by `build_runs.created_at`): the newest run that touched `ga_vargas` is 2026-09-07 11:02 (asset_set, rebuild, `complete`); the run before it, 10:57, errored ("post-write integrity check failed: integrity_check_sql → False"); earlier runs (August) include `aborted` global rebuilds and one `queued` asset_set build. No run after 2026-09-07 touched it. Why the rows are absent now was **not determined here**. It matters because `ga_vargas` has blocking radius 6 direct / 61 transitive (census) and four registered L1 dependents (`ga_condition`, `ga_strength`, `ga_sade_sati`, `ga_structural`) plus two L2 assets. This is the §N.8 defect class (a `lit` status without a detector for the claim it makes) observed on one asset, not a tier clause.

### MF-L1-001 — the ERRORED census cell: `ga_prashna` `Build.completion`
Census cell: `L1.assets[ga_prashna].measurements["Build.completion"] = {v: ERRORED, measured: "check errored: ERROR: permission denied for table ga_prashna_lagna"}`; SUMMARY.md lists it among 7 permission errors for `suvarna_reader` (a grant gap, not an inspector fault). It is **unmeasured, not PASS**: the layer's log counts it as 1 errored check (`census_L1.log`: "1 check(s) errored (R41: degraded, not layer-aborting)"). Consequences in the same asset: `live_rows` is null in the census, and `Count.floor` reads N/A because `target_floor` is 0. Follow-up read by this run, ten minutes after the census (2026-09-30 15:02 UTC vs census 14:52 UTC): `has_table_privilege(current_user, 'public.ga_prashna_lagna', 'SELECT')` is true, and `count(*)` over `ga_prashna_lagna` and over `ga_prashna_judgment` for the chart is 0 for each. That is this run's own query, **not the inspector's verdict**: the census cell stays ERRORED, and the instance neither substitutes a verdict for it nor infers one (the completion-honesty rule for an empty asset is TG-L1-008). Whether a grant was added after the census or the census ran under different state is not determined.

### MF-L1-002 — the census measures shared tables at two different populations
For the seven `chart_facts` producers, `Count.floor` and `Build.completion` use chart-scoped, partition-scoped `count_sql` (e.g. `ga_positions` live 1,205), while `Complete.depth` ("421096 rows, 25 cols; fully populated 17"), `Ldgr.source_presence` ("citation_ref populated on 421096/421096 rows"), `Vocab.identity`, `Reach.fields` (13 of 24 columns) and `Dens.served` (34 modules, "declaring density_contract: 19") are computed over the whole `chart_facts` table (all charts) and attributed identically to each producer. Same for `chart_dashas` (`Complete.depth` over 1,460,985 rows; chart-scoped live 483,870), `ga_condition_composite` (135 rows whole-table; 45 for the chart) and `l1_tajik_varsha_year_lords` (780 whole-table; 240 chart). The template's own warning (T3 lines 76–86: a count must say what it counted over) is what this trips; the census output does not state the population per cell. Related register rows: R95, R128.

### MF-L1-003 — silent absence of verdict cells (six Ldgr, two Vocab/Depth, one Reach basis)
`Ldgr.source_presence` has no cell for `ga_condition`, `ga_prashna`, `ga_strength`, `ga_structural`, `ga_transit_anchors`, `ga_vargas`; `Complete.depth` and `Vocab.identity` have no cell for `ga_strength` and `ga_structural` (no `target_table`); `Reach.fields` reads "no target_table declared" for those two. An absent cell is not a verdict. Register R128 records the same shape for L2 (the inspector should emit every gate row, N/A-with-reason included); it is cited, not restated.

### MF-L1-004 — what `Idem.pattern` PASS (19/19) does and does not show
The census cell is a static reading that a `DELETE FROM` the asset's own table precedes the insert (with file:line), not a rebuild-twice test. Two code facts it cannot express: (a) the delete scope is built from the categories, systems or vargas **present in the rows about to be written** (`_idempotency.py` lines 44–105: `if not rows: return 0`, categories taken from the rows), so a rebuild that stops emitting a category leaves that category's earlier rows in place; (b) `ga_vargas` reads PASS while the chart holds 0 of its rows (LG-L1-002). Neither is a tier clause; both bear on how much the Idem gate can be trusted as a detector (§N.8). No rebuild was run.

### MF-L1-005 — `Build.completion` FAIL on three multi-source assets is a basis difference, not a shortfall in every case
`ga_condition`: `rows_written` 45 vs live 2,970 (count over `ga_condition_composite` 45 + 2,925 `chart_facts` rows); register R42 already records "ga_condition FAILs are basis mismatches, not data disagreements". `ga_strength`: `rows_written` 13,715 vs live 14,141 (+426); `ga_structural`: `rows_written` 106,707 vs live 102,037 (-4,670). For the latter two the census gives both numbers and no cause; whether they are basis differences (overlapping `count_sql` predicates, MF/TG-L1-005: 420 `ga_strength`-matched rows are owned by `ga_structural` in `fact_category_ownership`) or real losses is **not determined here**. `ga_positions` `Build.history` is FAIL for a different reason: the most recent run aborted (2026-09-19).

### MF-L1-006 — L0 tables the code queries that `depends_on` does not declare
Registry: 5 edges from L1 to L0 (`ga_nakshatra` → `bg_nakshatra`, `bg_kp_sublord_division`; `ga_panchanga` → `bg_panchanga`; `ga_prashna` → `bg_prashna_rules`; `ga_sensitive` → `bg_reference`). Code read (grep of `ga_writers/ga_*.py` for the registry's L0 `target_table` names; comment matches are possible, queries confirmed by line for four): `ga_condition_writer.py:615` reads `bg_dignity_reference`; `ga_medical_writer.py:172` reads `bg_medical_mappings` (and names `bg_nakshatra_medical`); `ga_yoga_writer.py:166` reads `brahma_yoga_catalog`; `ga_sensitive_degree_writer.py:415` reads `reference_nakshatra`; `ga_structural_writer.py` names `brahma_dosha_catalog` and `brahma_yoga_catalog`. None of `ga_condition`, `ga_medical`, `ga_yoga`, `ga_sensitive_degree`, `ga_structural` declares an L0 edge. T4 §4.2 check 4 asks that "the declared edges match what the asset actually reads"; the census `Build.dag` checks only that declared edges resolve. Related: R86, R113.

### MF-L1-007 — `Earn.build_record` and `Cost.baseline` are one absent instrument
Both read NO_DETECTOR for 19 of 19 ("instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 781d6e28 complete/build (2026-09-07)" on `ga_ayurdaya`). The earlier skeleton read FAIL for both; at inspector 2a78ec64d they are NO_DETECTOR (T4 §1, line 142, says "not instrumented" is a legal value, so the two documents now agree). Note the census's "Earn" name covers rate instrumentation, not T3's Earn claim ("every status, grade or PASS the asset emits has a detector"); the plan (v1.5 §2.1, "Today's gap") says no `Null.*` or `Narr.*` criterion exists either, and the L1 census indeed has none. Register: R55 (the two are one detector), R34.

### MF-L1-008 — the L1 gate suite is wired only into the legacy runner
`ga_writers/gates.py` defines `run_all_gates` (FORENSIC_7_7, no_narration_linter, G7_only_facts, atomic grain, drift). Grep of `platform/python-sidecar` (tests excluded): `run_all_gates` is called only from `ga_writers/build_runner.py:46`, and `build_runner` is imported only by `scripts/run_l1_ganita_build.py`; nothing under `pipeline/orchestrator` calls it. Inline `forensic_gate(` calls do sit inside five writers (TG-L1-010 evidence), whether they execute on the orchestrated path was not traced. Bearing: the no-narration linter is the only L1 narration check found, and it is not on the orchestrated path by this reading.

### MF-L1-009 — `Dens.served` and `Reach` for the chart_facts producers are table-level; `ga_strength` is unattributable
Seven producers show the identical "34 module(s) … density_contract: 19"; `ga_strength` reads NO_DETECTOR ("no capability module's code references ga_strength; named in comments only in: get_dasha_lord_capability.ts — the served surface cannot be attributed by code"), although its `count_sql` is 14,141 rows and its blocking radius is 5/56. Served attribution by fact category was not attempted.

### MF-L1-010 — `Count.floor` FAIL on `ga_yoga`
live 53, floor 63, delta -10 (census); `asset_throughput` also reads 53. `ga_yoga` `Complete.depth` PARTIAL ("NEVER populated ['partial_formation_pct', 'activation_dasha_periods']", over the 202-row whole table). Floors are information under D3 (plan §1.1), so this is recorded, not a blocker.

### MF-L1-011 — census figures that differ from the earlier skeleton (both cited)
`L1_INSTANCE_SKELETON.md` (census `L1_prod_20260926.json`, whole-table counts) vs this run (`census_L1.json`, chart-scoped): `chart_facts` 421,096 under each of seven assets → per-partition live 130 / 2,847 / 437 / 1,205 / 6,287 / 8,775 / 335; `ga_condition` 135 → 2,970 (basis change, MF-L1-005); `ga_dashas` 1,460,985 → 483,870; `ga_tajaka` 780 → 240; `ga_vichara` 25,011 → 8,524; `ga_yoga` 202 → 53; `ga_strength`/`ga_structural` "not countable" → 14,141 / 102,037; `ga_nakshatra` Idem PARTIAL → PASS; `Earn.build_record`/`Cost.baseline` FAIL → NO_DETECTOR; `ga_prashna` "table empty … 51 runs" → 37 executed runs of 48 `build_run_assets` rows and `Build.completion` ERRORED. The register's own R95 wording ("identical 421,096-row figure under each") is superseded for the count cells and still true for the depth and provenance cells.

### MF-L1-012 — generation-history tables exist and are unreadable to the reader login
All 19 L1 writers carry `@l1_producer_contract` (grep: 19 of 19 files under `pipeline/orchestrator/writers/ga_*.py`; `CONTRACTED_L1_ASSETS` in `ga_writers/data_plane_runtime.py` lists the same 19), which opens a generation partition in `l1_data_plane_generations` (migration 1035). `pg_class` shows the tables exist in production; `SELECT` on `l1_data_plane_generations` and `l1_data_plane_generation_heads` returns "permission denied" for `suvarna_reader` (2026-09-30). The generation pins each consumer records (T3 §4.3; T2 §11) are therefore **not measured**, and the census has no cell for them.

---

## Part C — the earlier invention rows, checked against the tiers

`L1_INVENTIONS.md` lists 15 rows (its footer claims 17; INV-L1-09 and -15 were never used). Each was re-checked against the tier text, not carried over.

| earlier row | finding on re-check | now |
|---|---|---|
| INV-L1-01 necessity set | confirmed: no P/V→layer table (T1 §2, §11; T2 §2, §3.1, §5) | TG-L1-001 (R221, R85) |
| INV-L1-02 seed/pin | confirmed: named, never defined | TG-L1-003 (R86) |
| INV-L1-03 deployed vs code | confirmed | TG-L1-004 (R87) |
| INV-L1-04 switch behaviour | **partly supplied by a tier:** T2 §9.2 lines 493–517 and §6.2 line 359 state L1's ON and OFF roles and the storage separation; the skeleton's own text says §9.2's content "was not available to the fresh reader", a reader limitation. Remaining: the detector and the event-context identity | TG-L1-010 (narrowed; R88) |
| INV-L1-05 presentation rows | **derivable by a join** of T2 §3.4 and §7.1 except DP05/DP07 shares | TG-L1-012 (narrowed; R89) |
| INV-L1-06 coverage obligations | confirmed (T2 §5 names L1 in two rows) | TG-L1-013 (R90) |
| INV-L1-07 classes and maps | confirmed; census still `local_map_candidates = -1` | TG-L1-014 (R91) |
| INV-L1-08 carriage per asset | confirmed; T4's L1 hint "D3 dominates" does not cover āyurdāya (D2) or rule applications (D1) | TG-L1-015 (R09, R92) |
| INV-L1-10 disposition, kernel | confirmed | TG-L1-017 (R93, R116) |
| INV-L1-11 parity vs [TRANSFERS] | confirmed, text unchanged | TG-L1-011 (R71, R94) |
| INV-L1-12 shared table | confirmed; census counts are now partitioned, depth/provenance cells are not | TG-L1-005 (R95) |
| INV-L1-13 shared natural key | tier gap stands; the census reading it rested on (`ga_nakshatra` PARTIAL) **no longer holds** at 2a78ec64d | TG-L1-006 (R96) |
| INV-L1-14 kind with no target | tier gap stands; the census N/A it rested on is now a PASS with explanation | TG-L1-007 (R97) |
| INV-L1-16 varṣaphala universe | confirmed (falls under the universe clause) | TG-L1-013 (R98) |
| INV-L1-17 empty data asset | confirmed; ga_prashna's cells changed (ERRORED, N/A, NO_DETECTOR) | TG-L1-008 (R99) |

Four gaps the earlier pass did not record are new here: TG-L1-019, -020, -021, -022.
