---
asset_id: bg_rules
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
ledger_gap_ids: [bg_rules-G01, bg_rules-G02, bg_rules-G03, bg_rules-G04, bg_rules-G05, bg_rules-G06, bg_rules-G07, bg_rules-G08, bg_rules-O1, bg_rules-O2, bg_rules-O3, bg_rules-O4, bg_rules-Idem.pattern, bg_rules-Earn.build_record, bg_rules-Cost.baseline, bg_rules-Complete.depth, bg_rules-Carr.detector, bg_rules-Carr.D1, bg_rules-G03, bg_rules-Carr.detector, bg_rules-Completeness.depth.dasha_link, bg_rules-G06, bg_rules-Complete.depth]
---
# bg_rules — Classical rule extraction (`sutravali_rules`, 3,002 rules)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Regex extraction of classical rules from `classical_text_chunks` into `sutravali_rules`: about 14 pattern families, a deterministic `rule_id` (UUID5 of `text_id|verse_ref|sha256[:16]`), a quality score from five deterministic criteria (≥ 0.6 live), `extracted_by = python_regex_v2`, zero LLM, `ON CONFLICT (rule_id) DO NOTHING` (`platform/python-sidecar/brahmagyan/l0_rules.py:1-20,1608`; the module also deletes at `:1559`). 3,002 rules over 14 of the 15 corpus texts, every rule with a `verse_ref`. Depends on `bg_dasha_systems`, `bg_texts`, `bg_yogas`; declared dependents `bg_concordance`, `mi_kula` and one not identified offline (census direct 3 / transitive 51). Measured by the layer instance (Q-06) and the ledger pilot (`bg_rules-G01…G08`, `O1…O4`): rules per chunk range 2.34 (saravali) to 0.08 (bphs) to 0 (tajaka_neelakanthi, 290 chunks → 0 rules); `confidence` has 3 distinct values and equals `quality_score` on 3,002/3,002 rows; 17 rules carry `yoga_canonical_id`, 0 carry `dasha_system_id`; 2 of 14 rule `text_id`s (bhrigu_nandi_nadi, bphs_jaimini) have no ontology identity; the rules are absent from all 46 L0 registry capability modules and exposed only through `platform-mcp/src/tools/l0_brahmagyan.ts` (`ref_rules_search`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:283` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_rules.py:25`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `sutravali_rules`; count_sql tables: `sutravali_rules` | census CEN-R |
| live rows / floor | 3002 / 3,002 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_dasha_systems`, `bg_texts`, `bg_yogas` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 3 / transitive 51 (every layer); named: `bg_concordance`, `mi_kula` (named 2 of 3 direct; the rest not identified offline) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `sutravali_rules`: 13 non-test py/ts/tsx files reference it (9 outside brahmagyan/ and bg_*.py writers): `sutravali.py`, `bo_grounding.py`, `bo_laksana.py`, `grounding_matcher.py`, `citation_resolver.ts` +4 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `register_d7_channel.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 74b9a283 complete/skip_no_delta (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 74b9a283 complete/skip_no_delta (2026-09-06) |
| Complete (information, D3) | Complete.depth | PARTIAL | 3002 rows, 14 cols; fully populated 12; NEVER populated ['dasha_system_id'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): sutravali_rules (brahmagyan/l0_rules.py:1608 via…); Vocab.identity (declared key (rule_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.history; Build.registered (@register in bg_rules.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PASS.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_rules-G01 | Complete (width) | information / opportunity | yield spread 29×; a declared per-text yield or reason is a width question (D3), the extraction improvement is O1 (output change) \| ledger: measured: rules per corpus chunk ranges 2.34 (saravali, 471 chunks -> 1101 rules) to 0.08 (bphs, 1459 -> 112) to 0.00 (tajaka_neelakanthi, 290 -> 0) — a 29x spread, with… |
| bg_rules-G02 | Earn | real (a signal with no discrimination) | `confidence` has 3 values and equals `quality_score` on every row; a status claim that cannot read differently; CLAUDE.md §N.8 \| ledger: measured: confidence has 3 distinct values (0.600/0.800/1.000) across 3,002 rows, 2,770 of them 1.000; and confidence = quality_score on 3,002 of 3,002 rows / required: … |
| bg_rules-G03 | Carr | detector | no D1 compares a rule to its verse; CF-07 |
| bg_rules-G04 | Synergy (seam B) | real | 17 of 3,002 rules name the concept they qualify; 0 name a daśā system \| ledger: measured: 17 of 3,002 rules carry yoga_canonical_id; 0 of 3,002 carry dasha_system_id / required: a rule names the concept it qualifies |
| bg_rules-G05 | Dens / Reach | real (served surface) | exposed only through the MCP tool surface; absent from the 46 L0 retrieval-registry modules \| ledger: measured: exposed through the MCP tool surface (platform-mcp/src/tools/l0_brahmagyan.ts, ref_rules_search) and absent from all 46 L0 retrieval-registry capability module… |
| bg_rules-G06 | Complete (depth) | real or column removal: SS question | `dasha_system_id` populated on 0 of 3,002 rows \| ledger: measured: dasha_system_id populated on 0 of 3,002 rows — a column never used / required: populated where the rule is daśā-conditioned, or the column removed |
| bg_rules-G07 | Complete (width) | real | 14 of 15 texts yield rules; `tajaka_neelakanthi` yields 0 from 290 chunks without a stated reason \| ledger: measured: 14 of 15 corpus texts yield rules; tajaka_neelakanthi yields 0 from 290 chunks / required: every ingested text either yields rules or carries a stated reason i… |
| bg_rules-G08 | Vocab | real | 2 of 14 rule `text_id`s have no ontology identity; CF-09 \| ledger: measured: 2 of 14 rule text_ids (bhrigu_nandi_nadi, bphs_jaimini) have no identity in brahma_ontology's text class / required: every text_id resolves through the control… |
| bg_rules-O1 | NONE | opportunity | per-text extraction (the largest value increase available in L0) \| ledger: the largest single value increase available in L0: at saravali's yield BPHS alone would produce ~3,400 rules, more than the entire corpus holds today |
| bg_rules-O2 | NONE | opportunity | one honest signal instead of two identical ones \| ledger: one honest signal instead of two identical ones |
| bg_rules-O3 | NONE | opportunity | rule → concept linkage for L2 \| ledger: L2 could find the doctrine behind a structural claim without re-parsing prose |
| bg_rules-O4 | NONE | opportunity | a rate baseline \| ledger: a rate where none exists; O1's cost delta is unmeasurable without it |
| bg_rules-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_rules-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_rules-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_rules-Complete.depth | Complete | information | `dasha_system_id` never populated \| ledger: measured: 3002 rows, 14 cols; fully populated 12; NEVER populated ['dasha_system_id'] / required: the Complete gate's claim |
| bg_rules-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_rules-Carr.D1 | Carr | detector | same as G03 (folded) |
| bg_rules-Completeness.depth.dasha_link | Complete (depth) | real or column removal: SS question | same as G06 \| ledger: measured: dasha_system_id populated on 0 of 3,002 rows — a column never used / required: populated where the rule is daśā-conditioned, or the column removed \|\| folded ce… |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**enrich (E)** — agreed with the carried E: the extraction works and cites every verse, but rule→concept linkage is effectively absent (seam B: 17/3,002), the confidence signal does not discriminate and one text yields nothing. The additions are columns/links, not removal. Output changes need SS.

Approver under Track A brief §10: **Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1 per rule against its verse

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** the extraction is regex, so the check is a re-run of the rule’s own pattern family against the cited chunk: for each rule, re-match the family on `(text_id, verse_ref)` and assert the stored clause is what the pattern yields; report matched/unmatched per family. Because rule ids are deterministic, a seeded corrupted clause is detectable. This is the carriage check the layer instance names its single largest L0 gap (§2.7 a).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Rule → concept linkage (seam B)

- **Answers:** ledger `bg_rules-G04` / O3; layer instance §1.3
- **Change:** populate `yoga_canonical_id` (and, where the rule is daśā-conditioned, `dasha_system_id`) from the pattern family’s own match (the family that extracts a yoga formation already knows the yoga name) and resolve it through the ontology; rows with no determinable concept stay NULL with the reason (honest null). An additive output change.
- **Files / declaration / migration:** `brahmagyan/l0_rules.py` (pattern families + INSERT) ; depends on the ontology identity (CF-09)
- **Failing-first test and mutation:** failing-first: the count of rules with a concept id rises from 17 to the number the pattern families can resolve (stated in advance by a dry run) and every populated id resolves to the ontology (`brahma_yoga_catalog`); mutation: break a family’s name capture → the id count drops
- **Output change:** concept-id columns populated on a larger subset of rules
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild: bg_rules (note `ON CONFLICT (rule_id) DO NOTHING` does not UPDATE existing rows, so the writer needs `DO UPDATE` for the new columns or a one-time backfill migration)
- **Gate it moves:** Vocab/Synergy (seam B)
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: TGH-T3-13 (no synergy seams defined) and DP02 clause wording
- **Question for SS:** Backfill by migration or change the conflict clause to `DO UPDATE`?

### FD-3 · Honest confidence

- **Answers:** ledger `bg_rules-G02` / O2; CLAUDE.md §N.7 item 6, §N.8
- **Change:** either emit a graded signal that can discriminate or collapse `confidence` into an explicitly named quality tier and drop the duplicate (`confidence = quality_score` on all rows); never present two identical values as two signals.
- **Files / declaration / migration:** `brahmagyan/l0_rules.py` (scoring) + consumers of `confidence`
- **Failing-first test and mutation:** failing-first: `confidence` and `quality_score` are not identical on every row, or the column is declared a tier; mutation: set both equal → test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild: bg_rules (see the conflict-clause note)
- **Gate it moves:** Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent
- **Question for SS:** Drop/rename `confidence`, or build a discriminating score?

### FD-4 · Serve the rules from the L0 registry

- **Answers:** ledger `bg_rules-G05`
- **Change:** add an L0 capability module for `sutravali_rules` (the data is reachable only through the MCP tool) so the retrieval registry, Dens and Reach can see it; additive.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` (new `query_sutravali_rules.ts`) + descriptor; the MCP tool is unchanged
- **Failing-first test and mutation:** a response-shape test and a registry-reconciliation test; mutation: remove the module → reach reads 0
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens/Reach
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: retrieval plane is [TRANSFERS] (T2 §8)

### FD-5 · `tajaka_neelakanthi` yields 0 rules

- **Answers:** ledger `bg_rules-G07`
- **Change:** state why (no pattern family matches the text’s verse form) as a declared reason, or add a family; the latter is the O1 extraction improvement. Do not backfill rules without a check that each cites a verse.
- **Files / declaration / migration:** `brahmagyan/l0_rules.py` (families) or the declarations (reason)
- **Failing-first test and mutation:** a yield table per text with a reason for any zero
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** declaration: none; a new family: needs production rebuild of bg_rules
- **Gate it moves:** Complete (width)
- **Fix class:** registry/declaration only or data; **buildable before J1:** tier-independent

### FD-6 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_rules.py` for any composed text column; declare `[]` expected (the stored clause is a slice of source text; confirm there is no composed field)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-7 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `verse_ref` (with `text_id`; the table’s citation pair) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration) / needs production rebuild only if a column is added
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* two rule text_ids lack ontology identity
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 per rule
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* `verse_ref`/`text_id`
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `rule_id` (deterministic UUID5 of `text_id|verse_ref|sha256[:16]`; census, 0 duplicates). Fingerprint over `(rule_id, clause, pattern family, quality_score, yoga_canonical_id, dasha_system_id)`; volatile: `created_at`. Because the writer is `DO NOTHING`, a rebuild reproduces only rows not yet present; a fingerprint comparison must use a clean-room extraction.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 3,002 extracted rules with their verse references and deterministic ids; the regex families as the extraction contract.
- **Carriage check chosen (T4 §4.1; one only):** D1 (re-match each rule against its cited verse with its own family).
- **Opportunities (never blocking):** `bg_rules-O1…O4` (per-text extraction; one honest signal; rule→concept linkage; rate baseline).

## 7 · Questions for Strategic Suvarṇa

1. Concept backfill: migration or `DO UPDATE`?
2. `confidence`: drop/rename or a discriminating score?
3. `dasha_system_id`: populate or remove the column?
