---
asset_id: ga_sensitive
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 at the base commit (7 on origin/main 066c58587: the revision note names a NA_CAUSES addition for Carr; the criterion bodies were not diffed beyond that) and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); the tier fix (FD-1) is an output change for SS"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-12, I-26, I-21]
ledger_gap_ids: [ga_sensitive-Idem.pattern, ga_sensitive-Earn.build_record, ga_sensitive-Cost.baseline, ga_sensitive-Complete.depth, ga_sensitive-Build.history, ga_sensitive-Carr.detector]
---
# ga_sensitive — Sensitive points (30 A5 categories: upagrahas, Sphuṭas, KP, Nāḍī, Lāl Kitāb, Yogi system)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Writes all 30 A5 sensitive-point categories to `chart_facts` (`ga_writers/ga_sensitive_writer.py:1-30`): ~2,600 rows per ayanamsha, universal Section-B enrichment on every row (`tolerance_arcsec`, boundary flags, `vargottama_flag_at_point`, `formula_provenance_text`, `cross_ayanamsha_divergence_arcsec`), absent prerequisites floored to null-and-marked (no fabrication). The header states a two-pass design (upagraha: Swiss Ephemeris vs BPHS formula ≤10″; KP exact match; others: primary vs independent algebraic re-derivation) and claims "every row two-pass verified". Idempotency is `replace_prior_chart_facts` (`:44`); the S7 ruling (CLAUDE.md §N.4) relaxed the build-fatal single-tier guard to a logged warning (`:3082-3092`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1188` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_sensitive.py:14` (heavy: substeps per ayanamsha); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (partition: the 30 A5 sensitive-point categories incl. `esoteric_point_%`, `sensitive_point_gulika_mandi`, `special_lagna`, `nakshatra_pada_sensitive`; count_sql precedence fixed by migration 877) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 8,775 / 8,775 (Δ +0); `asset_throughput` lit / 8,775; seed floor literal 8775 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `bg_reference` (live and seed) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 4; census (2026-09-30, pre-1210): direct 4 / transitive 58; seed + 1210 reconstruction names 4 direct dependent(s): `bo_laksana`, `bo_special_lagna`, `ga_structural`, `ga_tajaka` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_sensitive_points.ts:114` (declarations `read_evidence`), `reading_checklist.ts`, `register_d9_judgment.ts`; `tolerance_arcsec` is non-null on 8,775 `chart_facts` rows on the chart (layer instance §2.7), a figure equal to this asset's row count (attribution not verified); 4 direct / 58 transitive dependents | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the Sphuṭa/upagraha/ārūḍha-adjacent point set (layer instance §2.4 row 3.9); feeds `ga_structural`, `ga_tajaka`, `bo_laksana` | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-08): orphaned_by_crash: prior orchestrator terminated while asset was in-flight |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 3ea96f6a complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 3ea96f6a complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 2 module(s) reach it by code: reading_checklist.ts, register_d9_judgment.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint NO_DETECTOR; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: `two_pass_verified` is the row builder's DEFAULT and is asserted by literal on rows with no second derivation | Earn/Carr | real | `_make_row(..., verification_pass_status: str = TWO_PASS_VERIFIED, tolerance_arcsec: float = 0.0, …)` (`:373-374`): any emitter that does not pass a status inherits the strongest tier with tolerance 0.0; the Yogi/Dagdha rows pass the literal `"two_pass_verified"` (`:2657-2678`) while the code shows one evaluation of Sun + Moon + 93°20′ and a table lookup (`DAGDHA_RASHI_BY_VARA`). `verification_vocab.two_pass_verdict` — "the ONLY sanctioned producer of `two_pass_verified`" (its docstring) — is called nowhere in this module. The module header ("Every row two-pass verified (zero single, zero divergent_flagged)", `:9`) is stale since the S7 ruling (CLAUDE.md §N.4): `single` is a permitted tier and `:3082-3089` and `:3215-3222` already tolerate it, so defaulting the row builder to `UNVERIFIED_DEFAULT` is consistent with policy Whether each of the 30 emitters earns the tier was not read here (3,251 lines); the stored distribution for this partition was not measured (no DB). CLAUDE.md §N.8: a PASS needs a detector that can read false; CF-19 |
| brief: dual authority for the Yogi point | Vocab/Ldgr | SS question | `esoteric_point_yogi_system` here and `sensitive_point_yogi` in `ga_sensitive_degree` (`ga_sensitive_degree_writer.py:86`) both compute Sun + Moon + 93°20′; the latter runs a genuine two-pass function (`_yogi_point_two_pass`, `:427`); which category is the authority, and do both survive? (§N.5) |
| brief: verification-tier literals | Earn | real | 17 quoted tier strings in the module (emission and comparison not separated; indicative regex count) incl. `"floored"` and `"two_pass_verified"` (`:2657-2678`); CF-17 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared; offline: agree PASS, fidelity PARTIAL, lint NO_DETECTOR; CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: referenced by code, no served SELECT attributable to the partition; CF-04, CF-18 |
| ga_sensitive-Build.history | Build | history | PARTIAL: 3 errors / 7 aborts; latest error 2026-08-08 `orphaned_by_crash`; the latest run completed; CF-10 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_sensitive_writer.py:3038` reached at `:3240` under `owns_conn` (`:3239`); wrapper passes `conn` (`ga_sensitive.py:44`); CF-14 |
| ga_sensitive-Carr / Earn / Cost / Complete.depth / Idem | Carr, Earn, Cost, Complete, Idem | detector / information / stale | a D3 pass exists in code for some categories but the census cannot read it; CF-07, CF-05, CF-18; the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — the asset is large, sourced and load-bearing (4 direct / 58 transitive dependents) and its census cells are PASS except the history record; the open item is an earned-signal defect in the row builder (a default tier), which is a fix design, with an output consequence, not a different disposition.

Approver under Track A brief §10: **Steward (G16); the tier fix (FD-1) is an output change for SS**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make `two_pass_verified` earned in `_make_row` and the Yogi/Dagdha emitters

- **Answers:** brief gap "default two_pass_verified"; CF-19; CLAUDE.md §N.7 item 4, §N.8
- **Change:** (1) change the `_make_row` default to `verification_vocab.UNVERIFIED_DEFAULT` with `tolerance_arcsec` = None where no second derivation ran; (2) every emitter that really compares two derivations sets the status from `two_pass_verdict(primary, independent)`; (3) table lookups and relays (Dagdha-Rāśi by vara) use `CLASSICAL_MATCH` ("relay fidelity, not re-derivation", `verification_vocab.py:278-282`); (4) first, a read-only census of the stored tier by `fact_category` for this partition, to know how many rows change. Do not change any computed value.
- **Files / declaration / migration:** `ga_writers/ga_sensitive_writer.py:373-374, 2657-2678` and each emitter that relies on the default (not enumerated here); a regression test that fails if any row builder defaults to a verified tier
- **Failing-first test and mutation:** failing-first: a row built without an explicit status must read `single`; a seeded wrong second derivation must read `divergent_flagged`; mutation: restore the default and the test fails. Layer-level: no `two_pass_verified` row has `tolerance_arcsec = 0.0` by default
- **Output change:** yes: `verification_pass_status` (and likely `tolerance_arcsec`) change on the rows that were stamped by default; L2 salience derived from the tier (`formulas.py` `VERIFICATION_RESCALE`) moves for them; W2 §6 recorded that normalising tier spellings ahead of the alias fix would have demoted 10,316 rows 0.85 → 0.60 as a "cosmetic cleanup" — SS must see the count first (R5)
- **Blast radius:** 4 direct / 58 transitive dependents read these rows; `bo_laksana`, `ga_structural`, `ga_tajaka` read these rows (whether each consumes the tier was not read); no computed value moves
- **Rebuild:** **needs production rebuild** of `ga_sensitive` (8,775 rows) after the census and the SS decision: REVIEW
- **Gate it moves:** Earn (the emitted tier gains a detector that can read false), Carr
- **Fix class:** writer code + output change; **buildable before J1:** tier-independent for the read-only census; the stored-tier change waits on SS
- **Question for SS:** After the read-only tier census, may the row-builder default and the literal stamps be corrected, accepting the L2 salience movement?

### FD-2 · Decide the Yogi-point authority

- **Answers:** brief gap "dual authority"; CLAUDE.md §N.5
- **Change:** declare one category the authority (the `ga_sensitive_degree` `sensitive_point_yogi` rows carry the earned second pass) and make the other reference it by fact_id or be removed; a parity check that the two agree to the arcsecond is the interim detector
- **Files / declaration / migration:** both writers + a parity query
- **Failing-first test and mutation:** the two categories agree on the canonical chart for all five ayanamshas; mutation: perturb one and the parity check fails
- **Output change:** none
- **Blast radius:** readers of `esoteric_point_yogi_system` (not enumerated)
- **Rebuild:** needs production rebuild of both producers if one is removed (REVIEW)
- **Gate it moves:** Vocab, Ldgr
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: TGH-T2 identity/duplicate rules
- **Question for SS:** Which category is the Yogi-point authority?

### FD-3 · Tier literals → named constants and the Narr test

- **Answers:** CF-17, CF-15
- **Change:** as `ga_positions` FD-1 and FD-2 for this writer (note `"floored"` has no named constant)
- **Files / declaration / migration:** `ga_sensitive_writer.py`; a test beside the writer tests
- **Failing-first test and mutation:** as ga_positions
- **Output change:** none
- **Blast radius:** none for data
- **Rebuild:** none
- **Gate it moves:** Earn, Narr
- **Fix class:** writer code + test; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-19** — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8). *This asset:* FD-1: the clearest instance in the layer so far
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-3: 17 quoted tier strings
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-3: declared
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D3 in code: upagraha Swiss-Ephemeris vs BPHS formula (≤10″) and `tolerance_arcsec` stored on 8,775 rows — a reader can use them
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 3/7: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: `natural_key_partition` by migration 874; count_sql precedence by 877
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:3038`
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the 30 categories; volatile: as `ga_positions`, plus `tolerance_arcsec` is a measurement and may move with the engine version (include it in the fingerprint only with a declared tolerance). `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 30-category catalogue with its cited formulas and prerequisite flooring (no fabrication), the Section-B enrichment on every row, and the FORENSIC gate.
- **Carriage check chosen (T4 §4.1; one only):** D3 — the second derivations the header describes (upagraha swisseph vs BPHS; KP exact match; algebraic re-derivation), read through `tolerance_arcsec`; lookup tables (Dagdha-Rāśi) are `classical_match` only.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. After the read-only stored-tier census, may the row-builder default and literal `two_pass_verified` stamps be corrected (output change, L2 salience effect)?
2. Which Yogi-point category is the authority: `esoteric_point_yogi_system` (here) or `sensitive_point_yogi` (`ga_sensitive_degree`)?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-03 accepted (R): `_make_row` defaults to `UNVERIFIED_DEFAULT`; the 1,780 zero-tolerance default rows are `single`; `two_pass_verified` only for an independent re-derivation compared through `two_pass_verdict`; per-emitter audit of the 6,970 positive-tolerance rows (emitter, rows, second path yes/no, resulting tier) goes to SS BEFORE S-L1. Yogi authority `esoteric_point_yogi` `formula_id = bphs_93_20`; `alt_96_40` a named variant. Track I: I-26.
- A-3: backend recorded; "Swiss" provenance strings corrected (I-21).
