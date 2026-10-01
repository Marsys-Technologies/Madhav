---
asset_id: ga_panchanga
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
disposition_proposal_approver: "Steward (G16); a tier upgrade (FD-1) is an output change for SS"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-27, I-21]
ledger_gap_ids: [ga_panchanga-Idem.pattern, ga_panchanga-Earn.build_record, ga_panchanga-Cost.baseline, ga_panchanga-Complete.depth, ga_panchanga-Build.history, ga_panchanga-Carr.detector]
---
# ga_panchanga — Birth-instant pañcāṅga (tithi, vara, nakṣatra, yoga, karaṇa, solar context)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Computes the full A4 pañcāṅga for the native's birth instant with the L0 `panchanga_engine.panchanga_instant()` service and persists atomic rows under `panchanga_*` categories (`ga_writers/ga_panchanga_writer.py:1-25`). A hard FORENSIC gate (`panchanga_forensic_gate`, `:218`) halts on any divergence from Shukla Tṛtīyā / Ravivāra / Śiva / Garaja and the Moon nakṣatra (Pūrva Bhādrapadā). Idempotency is `replace_prior_chart_facts` (`:35`); the verification tier of the anga rows is emitted through `_single_pass_verif()`, which returns the literal `"single_pass"` (`:150-151`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1291` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_panchanga.py:8` (`run`, light); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (partition: `fact_category LIKE 'panchanga%'`; ayanamsha-INVARIANT rows carry `ayanamsha_id = 'INVARIANT'`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 437 / 437 (Δ +0); `asset_throughput` lit / 437; seed floor literal **221** (the live floor was updated to 437 by migration 843; the seed lags) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `bg_panchanga` (live and seed) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 5; census (2026-09-30, pre-1210): direct 5 / transitive 56; seed + 1210 reconstruction names 5 direct dependent(s): `bo_laksana`, `ga_sade_sati`, `ga_structural`, `ka_kshetra`, `ph_muhurta` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_panchanga.ts:103` (declarations `read_evidence`); table-level 34 modules; the writer reads the L0 service `panchanga_engine.panchanga_instant()` | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the FORENSIC pañcāṅga anchors (Tithi = Shukla Tṛtīyā, Vara = Ravivāra, Yoga = Śiva, Karaṇa = Garaja) are owned here; 5 direct / 56 transitive dependents | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 5 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 3001b5ab complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 3001b5ab complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — no module in the serving roots references chart_facts, but it is named outside the scanned serving roots where a served select cannot be ruled out (R51): platform/src/lib/jyotish/asset_names.ts (holds the table and selects FROM a run-time table name) — never the closable N/A (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint NO_DETECTOR; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: the four FORENSIC anchors it owns carry no second-pass tier (Nirmāṇa F-B26) | Carr/Earn | real | every anga row is stamped `single_pass` (a deprecated alias of `single`); the writer's own comment says a second-pass cross-check was never implemented for any anga (`:138-150`). A deterministic second derivation exists in principle (tithi, yoga, karaṇa from the Sun and Moon longitudes in `ga_positions`) but is not run; CF-07 |
| brief: deprecated tier spelling emitted | Vocab/Earn | real | `_single_pass_verif()` returns `"single_pass"` (`:150-151`) and `_row` defaults `verification_pass_status="single"` (`:178`); `single_pass` is a deprecated alias of `single` that still holds 10,836 `chart_facts` rows on the chart (layer instance §2.6). Nirmāṇa W2 §6 deliberately dropped normalisation (aliases resolve through `verification_vocab`), but CLAUDE.md §N.4 requires named constants; CF-17 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared; 81 `citation_human` mentions in the writer; offline: agree PASS, fidelity PARTIAL (1 test file references the declared field in the same test function as a builder call; whether the assertion grades the sentence is not read), lint NO_DETECTOR; CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR (shared table, no per-asset served select attributable); CF-04, CF-18 |
| brief: anga start time not stored | opportunity | opportunity | `end_iso` only: "the true beginning is not in PanchangaInstant" (`:354`); the earlier `arambha_iso` key that stored the END was removed (guard in `tests/test_ga4_writer.py:354-391`, F-B24). Storing the start would need the L0 service to supply it |
| ga_panchanga-Build.history | Build | history | PARTIAL: 0 errors / 5 aborts, latest run complete; CF-10 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_panchanga_writer.py:1315` reached at `:1481` under `owns_conn` (`:1480`); the wrapper passes `conn` (`ga_panchanga.py:20`); CF-14 |
| ga_panchanga-Complete.depth / Earn / Cost / Carr / Idem | Complete, Earn, Cost, Carr, Idem | information / detector / stale | CF-18 / CF-05 / CF-07 / Idem ledger row stale (census PASS) |
| brief: seed floor literal 221 vs live 437 | Count | information | registry truth is the live row (migration 843, cycle 105); the seed literal and `volume_explanation` still read 221; CF-03 |

## 3 · Disposition

**keep (P)** — every applicable census cell is PASS but the history record; the FORENSIC gate and the delegation to the L0 engine are in place, the Nirmāṇa W2 MUST items (F-B24 key rename, F-B31 floor) are on main. The two real gaps are an honest-but-unverified tier on the four anchors and a deprecated spelling; neither is a reason for another disposition.

Approver under Track A brief §10: **Steward (G16); a tier upgrade (FD-1) is an output change for SS**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Earn a second-pass tier for the four FORENSIC angas by re-derivation from `ga_positions` longitudes

- **Answers:** brief gap F-B26; Carr NO_DETECTOR; CF-07, CF-19
- **Change:** for each ayanamsha-invariant anga, derive it a second way from stored Sun and Moon longitudes by the classical rule (tithi = ⌊(Moon − Sun) / 12°⌋ + 1; yoga and karaṇa by their own divisions; vara from the civil weekday) and stamp via `verification_vocab.two_pass_verdict(engine_value, derived_value)` (the sanctioned producer; `verification_vocab.py:268-300`); rows with no second derivation keep `UNVERIFIED_DEFAULT`. Do not stamp from the FORENSIC gate alone: it asserts a native birth fact, not a second derivation (the `_verify_vimshottari` comment, `ga_dashas_writer.py:710-715`, makes the same distinction)
- **Files / declaration / migration:** `ga_writers/ga_panchanga_writer.py` emit functions (`:330-513`) and `_single_pass_verif` (`:150`); a test beside `tests/test_ga4_writer.py`
- **Failing-first test and mutation:** failing-first: a seeded wrong anga must read `divergent_flagged`; the real chart reads `two_pass_verified` for the four anchors; mutation: make both arguments the same expression and the review grep (`verification_vocab.py` comment) must find it
- **Output change:** yes: `verification_pass_status` of four anga partitions rises from `single_pass` to `two_pass_verified`; the L2 salience weight for these rows changes (formulas.py `VERIFICATION_RESCALE` 0.85 vs 1.00 per the writer comment `:147-148`); an output change goes to SS (R5)
- **Blast radius:** 5 direct / 56 transitive dependents read these rows; salience in L2 moves for them (not computed here)
- **Rebuild:** **needs production rebuild** of `ga_panchanga` (437 rows, small): a REVIEW item for SS
- **Gate it moves:** Carr (NO_DETECTOR → a measurable second pass), Earn
- **Fix class:** writer code + output change; **buildable before J1:** tier-dependent: TGH-T3-02/T3-15 (what owes an independent derivation, TG-L1-022)
- **Question for SS:** Is the second derivation from `ga_positions` longitudes accepted as the L1 D3 for pañcāṅga angas, with the tier rise (and the L2 salience change) approved?

### FD-2 · Emit the canonical tier spelling

- **Answers:** brief gap "deprecated spelling"; CF-17
- **Change:** return `verification_vocab.UNVERIFIED_DEFAULT` from `_single_pass_verif` and as the `_row` default; guard test as `ga_positions` FD-1
- **Files / declaration / migration:** `ga_panchanga_writer.py:150,178`
- **Failing-first test and mutation:** guard test fails on a `"single_pass"` literal
- **Output change:** yes, minor: `single_pass` → `single` on the anga rows (the vocabulary treats them as aliases, so consumers resolving through `verification_vocab` see no change; a consumer that string-matches `single_pass` does)
- **Blast radius:** any raw-string reader of `single_pass` (not enumerated here)
- **Rebuild:** needs production rebuild of the asset for stored rows to change (REVIEW)
- **Gate it moves:** Earn, Vocab
- **Fix class:** writer code; **buildable before J1:** tier-independent (CLAUDE.md §N.4)

### FD-3 · Narr golden test naming `citation_human`

- **Answers:** Narr.fidelity_test PARTIAL; CF-15
- **Change:** assert the exact sentences for the four FORENSIC angas ("Tithi ends: …", "Yoga ends: …", and the vara/karaṇa lines) against the gate constants (`FORENSIC_EXPECTED`, `:55`)
- **Files / declaration / migration:** test beside `test_ga4_writer.py`
- **Failing-first test and mutation:** mutation: change a name in a citation and the test fails
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent

### FD-4 · Refresh the seed literals to the live registry

- **Answers:** brief gap "seed floor 221"; CF-03
- **Change:** set the seed `target_floor` 437 and correct `volume_explanation` (migration 843 is the live truth); seed edits never rewrite an existing row, so this is hygiene
- **Files / declaration / migration:** `platform/scripts/seed/asset_registry_seed.ts:1291-1316`
- **Failing-first test and mutation:** `scripts/__tests__/asset_registry_seed_dag_parity.test.ts` and the registry parity gate stay green
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Count (information)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-1: D3 from stored longitudes
- **CF-19** — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8). *This asset:* FD-1: tier honest today (`single_pass`), but unearned upgrades must not be stamped from the FORENSIC gate
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-2: `"single_pass"` literal
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-3: declared
- **CF-03** — Registry correction batch (live registry vs seed literals: floors, edges, status) in one surgical migration plus seed literals. *This asset:* FD-4: seed floor 221
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 0/5: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: `LIKE 'panchanga%'` partition; `natural_key_partition` by migration 873
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories/ayanamshas present in rows (INVARIANT rows included)
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:1315`
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the `panchanga_*` categories; ayanamsha-INVARIANT rows use `ayanamsha_id = 'INVARIANT'` and must be fingerprinted separately from the five per-ayanamsha passes. `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the L0-engine delegation, the FORENSIC gate for Tithi/Vara/Yoga/Karana, the INVARIANT vs per-ayanamsha split.
- **Carriage check chosen (T4 §4.1; one only):** D3 — re-derive tithi/yoga/karaṇa/vara from the stored Sun and Moon longitudes by the classical divisions and compare.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Approve the second derivation from `ga_positions` longitudes as the D3 for the four FORENSIC angas, with the resulting tier rise and L2 salience change (R5)?
2. May the deprecated spelling `single_pass` stop being emitted (stored rows change only on rebuild)?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-16(a) accepted: emit `single`, never the alias `single_pass` (176 canonical rows) (I-27). A-3: the four `set_ephe_path(None)` calls in `panchang_engine` go through the shared helper (I-21).
