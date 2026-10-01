---
asset_id: bg_texts
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [bg_texts-Build.completion, bg_texts-Earn.build_record, bg_texts-Cost.baseline, bg_texts-Complete.depth, bg_texts-Dens.served, bg_texts-Carr.detector]
---
# bg_texts — Classical text corpus (15 texts, 10,651 chunks; retained capital)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Indexed verse chunks from the 15 canonical classical texts with immutable source-object generations and preserved supervised translations. Pipeline: GCS PDF (or reviewed DjVu `.txt`) → chunk (≤ 1,500 chars) → embed with Vertex AI `text-multilingual-embedding-002` (768-dim), zero LLM (`platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py:1-60`). The accepted per-text chunk counts are pinned (`ACCEPTED_CHUNK_COUNTS_BY_TEXT`, `:40-57`; e.g. bphs 1,459, nadi_navamsa_patel 1,850) and `bg_texts_source_manifest_v1.json` pins 20 source objects with `md5_base64`, `generation`, `size_bytes`. Rebuild modes: only `additive` (insert texts with no chunks; an already-present text must match its accepted count or the build fails) and `metadata_only` (`:388-396,418-424`), so a rebuild never regenerates existing chunks; `lal_kitab` is removed from `classical_texts` as a DROPPED corpus text (`:435`). ON CONFLICT upsert (`:665`). `data_disposition = RETAINED_AS_CAPITAL`; the non-regenerable inventory lists `classical_texts*` as recoverable only while the GCS bucket survives. The widest dependency in the data plane after the ontology: declared dependents `bg_compendium_index`, `bg_concordance`, `bg_gochara_citation_resolution`, `bg_parihara_rules`, `bg_remedies`, `bg_rules`, `bg_text_index`, `bg_yogas` (census direct 8 / transitive 58). `Complete.depth`: `content_summary` and `cleaned_translation_text` never populated.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:219` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py:402`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `classical_text_chunks`; count_sql tables: `classical_text_chunks` | census CEN-R |
| live rows / floor | 10651 / 10,651 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 8 / transitive 58 (every layer); named: `bg_compendium_index`, `bg_concordance`, `bg_gochara_citation_resolution`, `bg_parihara_rules`, `bg_remedies`, `bg_rules`, `bg_text_index`, `bg_yogas` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `classical_text_chunks`: 40 non-test py/ts/tsx files reference it (13 outside brahmagyan/ and bg_*.py writers): `bo_laksana.py`, `favourable_houses.py`, `w29_citation_resolution.py`, `logic.py`, `route.ts` +8 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_classical_texts.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 2 module(s): query_classical_texts.ts, query_compendium_index.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=10651 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Complete (information, D3) | Complete.depth | PARTIAL | 10651 rows, 26 cols; fully populated 16; NEVER populated ['content_summary', 'cleaned_translation_text'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 10651/10651 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): classical_text_chunks (bg_texts.py:665)); Vocab.identity (declared key (chunk_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_texts.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_texts-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=10651 / required: the Build gate's claim |
| bg_texts-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_texts-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_texts-Complete.depth | Complete | information | columns never populated (D3: information, not a blocker) \| ledger: measured: 10651 rows, 26 cols; fully populated 16; NEVER populated ['content_summary', 'cleaned_translation_text'] / required: the Complete gate's claim |
| bg_texts-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 2 module(s): query_classical_texts.ts, query_compendium_index.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_texts-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the corpus is the source every L0 carriage check rests on and is built to be append-only; the open items are the changed-rows reading (CF-01, by design: additive mode inserts nothing when texts exist), the carriage detector (the manifest makes a strong one possible) and the Dens question.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: converged rerun reports 0 changed rows

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** apply CF-01 option A (or B after the ruling): additive mode inserts only absent texts, so `rows_written = 0` is the designed result on a built corpus (`bg_texts.py:418-424,481-502`)
- **Files / declaration / migration:** `platform/scripts/governance/asset_census.py` (Build.completion) + the asset’s declarations entry; option B instead edits the seed function’s returned counts
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (option A, recommended); option B would write a new record by rebuilding this asset (idempotent, no data change)
- **Gate it moves:** Build (completion)
- **Fix class:** detector/tooling (A) or writer code (B); **buildable before J1:** tier-dependent: T4 §4.2 check 6 wording
- **Question for SS:** CF-01: is a converged-rerun `rows_written = 0` on a declared changed-rows writer a PASS?

### FD-2 · Carr detector — D3 re-chunk from the manifest-pinned source

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for a sample of texts, verify the source object’s `md5_base64`/`generation` against the manifest, re-run the deterministic chunker on the source and compare the chunk text set and count to `classical_text_chunks` and to `ACCEPTED_CHUNK_COUNTS_BY_TEXT` (embeddings are excluded: they are a deterministic transform and need Vertex). Seeded mismatch: edit one stored chunk → must be caught. Needs read access to the GCS source objects, so it is a tooling item, not run in this lane.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Rebuild guard for the corpus

- **Answers:** N-29 (destructive operations need a rebuild plan, a serving guard and a fingerprint); non-regenerable inventory (`classical_texts*`: GCS)
- **Change:** record `rebuild_mode` in the B.L0 impact statement: only `additive`/`metadata_only` are legal, no mode deletes chunks; the pre-rebuild fingerprint is `(text_id, chunk_count, sha256 of ordered content_en)` per text and must be unchanged after. Any future full re-chunk is a different operation and needs SS’s approval.
- **Files / declaration / migration:** the B.L0 impact statement (document) + a fingerprint query
- **Failing-first test and mutation:** pre/post fingerprint equality after a rebuild; mutation: truncate one text → the fingerprint differs
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (rebuild correctness; E5.5)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_texts.py` for any composed text column; declare `[]` expected (stored source text and supervised translations; nothing composed) after reading `bg_texts.py`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `query_classical_texts.ts`, `query_compendium_index.ts`; CF-04
- **Change:** per CF-04: declare `density_contract` where the module paginates or facets, after the applicability ruling
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 + N-22 applicability
- **Question for SS:** Does Dens apply to this reference table at all (it carries no verification tier)?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows, not rows present). *This asset:* additive mode: 0 inserted on a built corpus
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 re-chunk from the manifest
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 2 modules

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `chunk_id` (census, 0 duplicates). Fingerprint per text over `(chunk_id, content_en)` in order, plus `chunk_count`; embeddings excluded (a deterministic transform; compare by model id and dimension). Volatile: `id` (uuid), `created_at`, `topic_tag` (owned by bg_text_index).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 10,651 chunks as ingested, the pinned source generations, the accepted per-text counts and the preserved supervised translations.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derive the chunk set from the manifest-pinned source).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2
