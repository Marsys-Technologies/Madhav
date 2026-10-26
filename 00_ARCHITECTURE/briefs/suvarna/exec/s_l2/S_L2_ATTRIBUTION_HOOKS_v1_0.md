---
artifact: S_L2_ATTRIBUTION_HOOKS
version: "1.0-DRAFT"
status: DRAFT_FOR_REVIEW (nothing executed against any real system; the rehearsal confirms every entry before the window)
date: 2026-10-03
lane: suvarna/land/TI-s-l2-prep-001
produced_by: exec-suvarna worker bo-uuid-fix (S-L2 prep, coordinator widening N-96)
scope: docs, hook files and tests only. No production write, no migration, no change to flip_detector.py (the L2 coverage of the detector is PR #3035, a separate tooling PR).
changelog:
  - "1.0-DRAFT (2026-10-03): first version. Six hook files (one L1 tripwire, five L2 lanes), derivation module, tests with mutation proofs."
---

# S-L2 attribution hooks (flip detector): design, derivations, and what the rehearsal must confirm

## 1. What this is and how it is used

The S-L1 window was judged by `flip_detector.py`: production is compared with a baseline snapshot, every changed row must be attributed to a lane hook, every undeclared change is a failure, every unread scope is a NOT CHECKED line. S-L2 (the Bodha rebuild: 23 `bo_*` assets) is judged the same way. Two things are needed and both are here:

1. **An L1 non-regression tripwire** (`s_l2_l1_untouched.json`, top level). S-L2 rewrites `bodha_*` tables only. The four L1 tables the detector reads must be exactly what S-L1 left. The lane is a set of explicit zero claims; compared with a snapshot taken at S-L1 CLOSE, any change in any of the four tables is a failure. It is loadable by the detector on main today.
2. **Five L2 lanes** (`l2/*.json`) for the 29 L2 tables the extension (PR #3035, `--l2`) compares: MSR, embeddings and grounding, the Bodha graph, CDLM and Sangati, remedies, pratijna, discoveries, anomalies and the scorecard. They cannot be loaded by main's detector: its table allow-list does not contain the L2 tables and it reads top-level files only, hence the sub-folder.

**Running the window comparison (after #3035 is on main):**

```bash
# 0. at S-L1 CLOSE, before any bo_* build: the baseline carries L1 and L2 in one repeatable-read transaction
python3 platform/scripts/governance/flip_detector.py --snapshot native --l2 --out /Users/Dev/suvarna-evidence/S_L2/baseline_slice_close.json.gz
# 1. a run folder holding the tripwire and the five lanes side by side (the detector reads top-level *.json only)
mkdir -p $RUN/hooks && cp 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_attribution_hooks/s_l2_l1_untouched.json 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_attribution_hooks/l2/*.json $RUN/hooks/
# 2. after the S-L2 rebuild
python3 platform/scripts/governance/flip_detector.py --compare /Users/Dev/suvarna-evidence/S_L2/baseline_slice_close.json.gz --l2 --hooks-dir $RUN/hooks --out $RUN/report.json
```

Raise `FLIP_TIMEOUT_SEC` if the shared reader is busy (the embedding digest read is the slowest). A compare WITHOUT `--l2` reads every L2 entry as NOT CHECKED, never as passing. The verdict is never PASS in production (the standing NOT CHECKED registry is never empty, including `l2.generation_ledger`: the reader cannot see the generation heads, so head promotion must be confirmed with a privileged login).

## 2. What a count means (row model in one paragraph)

The detector reads each L2 table as rows `[ayanamsha, category, subject, key, text, num, tier]`. `category` is the coarse class a hook names; `subject`+`key` are the semantic natural key and never a generated id. `text` begins with the generated identity (`id=<signal_id>`...) followed by content columns, arrays/jsonb/vectors as 12-hex md5 digests. A signal whose id or cited-id array moved therefore reads as ONE `value` change on the same key, not as an appeared plus a disappeared row. Scores (`num`) are compared as continuous values and are never a class change. An entry's `expected_count` bounds the number of changes of the declared kinds in the declared categories. `appeared`/`disappeared` mean the semantic key is new/gone; `occurrence_count` means the multiplicity of a repeated key changed; `tier` means only the tier column moved.

## 3. Rules and the derivation of every number

Every number is read once from production on 2026-10-03 (read-only login, one SELECT each; BASE in `platform/scripts/governance/s_l2_hook_rules.py`), or is the largest effect a declared S-L1 hook can have (DELTAS), or is a structural fact about a writer (the rules below). None is a measured count plus a safety margin. The module writes the hook files (`python3 platform/scripts/governance/s_l2_hook_rules.py --write`); the tests fail if a file and the derivation disagree.

### 3.0 The rules

- **R1. A cited fact id is content.** `constituent_facts_array` is part of an MSR signal's text. Every `chart_facts.fact_id` except the ga_positions generation's is re-keyed once by S-L1 (142,094 of 143,299 ids; the stored ids still hash `build_id`). A signal that cites at least one re-keyed fact therefore changes its cites digest on rebuild and reads as a `value` change, whether or not its value moved.
- **R2. Stable-cite signals.** `sudarshana_agreement` (45) and `dhana_axis` (10) cite only ga_positions `graha_position` facts and hold discrete configuration values: cites and identity do not move; only the `bo_laksana_rerank` enrichment digests (system convergence, consensus, contradicts, node contribution) can. 1,066 of the 37,694 composite signals are of the same kind.
- **R3. Declared S-L1 deltas map to a few classes.** `bo_laksana._signal_type_class` sends every declared appeared/disappeared fact category to `composite_state`, `karaka_alignment` or `parivartana`; no declared change adds or removes a fact projected into any other class on this chart (the ephemeris move has no class flip here; the vichara dedupe touches only `varga_ratification_divergence`). An appeared fact yields AT MOST one new signal (collapse by identity can only lower it).
- **R4. No derivable bound.** Multiplicity of repeated keys (`occurrence_count`) and the 9 `varga_ratification_divergence` signals depend on the identity collapse and on the ga_vichara dedupe (8,524 to 7,774 rows); they are declared as attribution only (`min` 0, no `max`, `optional`).
- **R5. Tier.** `verification_pass_status` follows the cited facts' tiers; at most one tier change per row.
- **R6. Signal ids are cited.** Tables that store signal-id arrays (embeddings, grounding, cells, convergence, triangulation, lenses, gestalt, contradictions, discoveries, anomalies, aspect edges) change by `value` only where a cited signal's id or content moves; the bound is the row count, never a derived subset, because which ids move depends on the ephemeris and value movement the rehearsal measures.
- **R7. Yoga firings.** `ga_yoga_firings` is not read by the detector and is re-created by the L1 rebuild; the 53 firing matches in grounding have no derivable bound.
- **R8. Finite sets and zero claims.** Where the row set is physically fixed (9 grahas, 12 bhavas, 13 domains, 12 question types, one summary per ayanamsha, a fixed template list), `appeared`/`disappeared` are explicit `exact 0` claims; where the set depends on MSR yoga (74) and dosha (26) membership, it is zero because R3 says that membership cannot change on this chart. Node, edge, path and motif identities are derived from semantic keys, never from signal or fact ids, so they are stable.
- **R9. Arrays of L1 ids.** The 754 edges and 605 of 615 mechanisms that cite `chart_vichara.id` all change (every post-S-L1 vichara row has a new id, S-L1 hooks section 8); the 330 edges that cite `chart_facts` ids also change. These give the only non-zero lower bounds in the graph lane.
- **R10. Finite grids.** CDLM cells are ordered domain pairs (13 x 13 x 5 ayanamshas), convergence and rollups are one row per domain per ayanamsha, triangulation is question class x tradition per ayanamsha (12 x 4 x 5): the number of rows that can ever exist is the grid, whatever S-L1 does. `appeared` is bounded by grid minus current rows; `disappeared` by the current rows. The grid sizes are structural upper bounds; the current occupation is smaller.
- **R11. Tombstone.** `bo_upaya` deletes `bodha_rm_dasha_windowed_prescriptions` (`replace_prior_rm_dasha_windowed`) and the producer raises: the 5 legacy rows disappear exactly, nothing else ever writes it.
- **R12. Pratijna.** 27 event classes x 5 ayanamshas = 135 rows always exist; the status is part of the key, so a status flip is one disappeared plus one appeared. The derivation digest carries `chart_divisionals` ids (all regenerated by the F-A2 rebuild) and `chart_facts` ids.
- **R13. Discoveries and anomalies.** Data-dependent lists with no natural key over the MSR set; their ids embed signal ids; counts are not rule-bounded.

### 3.1 MSR (`s_l2_msr_projection`)

Production classes (rows): composite_state 37,694; karaka_alignment 6,156; sade_sati 2,871; varga_pattern 1,400; tradition_specific 1,169; panchanga 590; annual 315; configuration 150; parivartana 75; yoga 74; nakshatra_semantic 45; sudarshana_agreement 45; dosha 26; arudha 25; special_lagna 20; dhana_axis 10; varga_ratification_divergence 9; vargottama_amplification 4. Total 50,678.

| entry | bound | derivation |
|---|---|---|
| 13 classes, `value` | exact 6,764 | R1: all cite a re-keyed fact; R3: none appears or disappears; survivors = before = 315+150+26+590+1,169+1,400+74+25+45+20+4+2,871+75 |
| composite_state `value` | 36,388 to 37,694 | R1: 36,628 cite a re-keyed fact (1,066 cite ga_positions only); minus the 240 that may vanish; max all |
| karaka_alignment `value` | 6,121 to 6,156 | R1: all cite; minus the 35 STRIKARAKA rows that vanish |
| sudarshana_agreement, dhana_axis `value` | 0 to 55 | R2 |
| composite_state `appeared` | 0 to 4,081 | R3 (section 3.2) |
| composite_state `disappeared` | 0 to 240 | sun_required_rupa removes 240 graha_in_house_composite_strength facts |
| karaka_alignment `appeared` / `disappeared` | 0 to 1,340 / 0 to 35 | section 3.2 |
| parivartana `appeared` / `disappeared` | 0 to 15 / exact 0 | parivartana_pairs, optional on this chart |
| 14 other classes `appeared`/`disappeared` | exact 0 | R3 |
| every class `tier` | 0 to 50,678 | R5 |

### 3.2 The appeared bounds (the largest effect of the declared S-L1 hooks)

composite_state: argala_graha_natal 156 + ashtakavarga_bindu_contributor 3,360 + dasha_scope_cap 1 x 5 ayanamshas + sensitive_point_gulika_mandi 35 + geometry categories 45+30+315+85 (optional on this chart) + graha_gandanta twin rows 50 = **4,081**. karaka_alignment: karaka_chara_position PUTRAKARAKA 35 + strikaraka_alias 5 + karaka_web_per_varga up to 1,300 = **1,340**. parivartana: **15**. Largest total of new signals A_TOTAL = **5,436**; largest total removed D_TOTAL = 240 + 35 = **275**. These are ceilings, not predictions: collapse by identity only lowers them (a prior estimate for ashtakavarga_bindu_contributor is about +10, not 3,360).

### 3.3 Embeddings and grounding (`s_l2_embeddings_grounding`)

One embedding per signal (R6) and one grounding match per signal plus one per fired yoga/dosha (R7). Both follow the signal set: `appeared` 0 to 5,436, `disappeared` 0 to 275, `value` 0 to 50,678 (embeddings; grounding msr_signal also 50,678). The embedding table carries no tier (declared zero). The 53 firing matches are attribution only.

### 3.4 Bodha graph (`s_l2_cgm_graph`)

Nodes 385 (arudha 95, bhava 60, domain 65, dosha 16, graha 45, special_lagna 35, yoga 69): `appeared`/`disappeared` exact 0 (R8); `value` 0 to 385. Edges 849: types other than argala `appeared`/`disappeared` exact 0; argala `appeared` 0 to 120 (the writer caps argala edges at 24 per ayanamsha) and `disappeared` 0 to 119; `value` **635 to 849** (R9: 754 vichara-citing edges, less the 119 argala edges that may vanish; max every edge). Paths (45), motifs (600), sub-graph `value`: exact 0 (stable ids, discrete content). Topology: `value` 0 to 5 (hub scores in the jsonb). Mechanisms (615): `value` **605 to 615** (R9). Contradictions (15): set exact 0 (R3), `value` 0 to 15 (R6).

### 3.5 CDLM and Sangati (`s_l2_cdlm_sangati`)

R10 grids: cells `appeared` 0 to 565 (845 - 280), convergence and rollups `appeared` 0 to 5 (65 - 60), triangulation `appeared` 0 to 45 (240 - 195); `disappeared` up to the current rows; `value` up to the current rows. Chart summary, lenses (12 x 5 = 60) and gestalt: set exact 0. Pattern clusters: attribution only for the set (graph clustering).

### 3.6 Remedies, pratijna, discoveries, anomalies, scorecard (`s_l2_remedy_discovery_misc`)

Resonances (9 x 5 = 45) and the remedy summary: set exact 0 (R8); prescription, bundle and pattern-remedy sets: attribution only (match-score thresholds, active-dosha set). **Dasha-windowed prescriptions: `disappeared` exact 5, nothing else** (R11). Pratijna: `value`, `appeared`, `disappeared` each 0 to 135, tier and multiplicity exact 0 (R12). Discoveries and anomalies: R13. Scorecard: set exact 0 (one row), `value` 0 to 1.

## 4. What the hooks cannot see (carried as NOT CHECKED rows by the detector)

- The L2 data-plane generation ledger (producer generations, heads, partitions, run intents, row snapshots): the reader role cannot read it, so a promoted head, a stuck `building` generation and the row-snapshot append are confirmed by a privileged login (runbook gate G-12).
- Columns outside each registry entry (`l2.unread_columns`): summary and headline texts, jsonb detail, embedding vectors beyond a 12-hex digest.
- Scores move continuously and are never a class change; a lane that declares only score movement cannot be observed.
- `bo_samvada` writes nothing (a view); nothing is hooked for it.
- A first-generation active-table replacement has no in-database rollback (previous head NULL); the hooks judge the outcome, they do not restore it.

## 5. Tests (offline: no database, no network)

`platform/scripts/governance/__tests__/test_s_l2_hooks_expected_state.py`:

- **Part A** (needs the detector on main): the L1 tripwire. Unchanged L1 passes with no failure class; every kind of change in every compared L1 table fails; weakening the exact-0 claim makes the same change pass (so the claim is load-bearing); a dasha start shift is DASHA_SHIFT_UNDECLARED.
- **Part B1** (no detector needed): each L2 file is byte-identical to the derivation's output; a mutation of any derivation input (20 of them: class counts, appeared/disappeared ceilings, grid sizes, citing counts, caps) changes the output of the expected lanes.
- **Part B2**: the files validate with the L2-aware validator, cover exactly the 29 L2 tables, name exactly the production categories, every bound is internally consistent, and every rule label cited in a note is defined here.
- **Part B3**: an ORACLE written by hand in the test file (a second derivation; the arithmetic is in its comments, nothing imported from the derivation module) lists 96 (table, category, kind) rows with counts that must be accepted and counts that must be refused, run through the real detector (`compare_states`). 24 hook mutations (widen or narrow a cap, raise a floor, open a cap, drop an entry, drop a kind or a category, relax a zero claim) must each be caught by the oracle.
- **Part B4**: without `--l2` every L2 entry is NOT CHECKED; a change in an L1 table fails with the L2 lanes loaded; an in-bound L2 change raises no attribution failure.

Part B needs the L2-aware detector (PR #3035). On a tree without it the detector-dependent tests skip and B1 plus the doc checks still run; point `FLIP_DETECTOR_PATH` at a copy that has it. Counts above 6,000 are judged with the detector's own expectation rule on the entry bound instead of a 50,000-row diff (CI time).

## 6. What the rehearsal must confirm (each is a measurement, not an assumption)

1. **R1/R9 minimums**: after the rehearsal rebuild, the number of MSR `value` changes equals 6,764 for the 13 classes (exact) and lies in the composite/karaka ranges; the edge `value` count lies in 635 to 849 and the mechanism count in 605 to 615. A count below the floor means a cited id did NOT re-key (a writer reading stale facts).
2. **R3**: zero appeared/disappeared in the 14 classes and in every zero-claim table; the argala edge set stays inside its cap.
3. **R10**: the grid-bound entries are ceilings; record the real appeared/disappeared counts.
4. **R11**: exactly 5 dasha-windowed rows disappear.
5. **R2**: the enrichment-only changes of the 55 stable-cite signals.
6. The strict count check in `bo_laksana` (B7: `inserted != len(signal_rows)` raises "refusing a partial root generation") may fail on current L1 content because about 59% of per-aya rows collapse by identity; if it raises, S-L2 needs a decision (dedupe before the check, add the discriminating subject to the configuration, or relax the check), and every choice moves signal ids and counts. This changes the MSR lane, not the method.

## 7. Things for SS

1. Merge PR #3035 (the L2 extension) before the window; until then Part B skips and the L2 lanes cannot be loaded.
2. Where the five L2 lane files live at the window: the detector reads top-level files only. The runbook copies them next to the tripwire into a run folder; the alternative is to move them up one level when #3035 is on main.
3. The baseline for S-L2 is the S-L1 CLOSE snapshot taken with `--l2` (L1 and L2 in one transaction), not the pre-S-L1 snapshot.
4. The N-91 statement that "1,340 signal_ids move" is a LOWER BOUND (1,340 MSR signals embed the random `chart_divisionals.id`; every other embedded value that moves in the L1 rebuild moves its signal id too). The between-state disclosure text and the runbook say so.
5. These hooks declare nothing for the S-L1 hook directory (23 hooks, `hooks_real`): they do not touch it.
