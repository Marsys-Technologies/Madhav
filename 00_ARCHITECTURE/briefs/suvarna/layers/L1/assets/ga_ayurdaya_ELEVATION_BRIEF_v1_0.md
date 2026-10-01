---
asset_id: ga_ayurdaya
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "enrich (E)"
disposition_proposal_approver: "Strategic Suvarṇa (output change, R5); the enrichment waits on SS"
ledger_gap_ids: [ga_ayurdaya-Idem.pattern, ga_ayurdaya-Earn.build_record, ga_ayurdaya-Cost.baseline, ga_ayurdaya-Complete.depth, ga_ayurdaya-Build.history, ga_ayurdaya-Carr.detector]
---
# ga_ayurdaya — Āyurdāya under three classical methods (method-attributed, not adjudicated)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Āyurdāya (longevity) for each (chart × ayanamsha): all three classical methods (Piṇḍāyu, Nisargāyu, Aṃśāyu) method-attributed, with the classical applicability rule served alongside (the stronger of Lagna/Sun/Moon selects the governing method) and no autonomous adjudication of the doctrinal dispute (`ga_writers/ga_ayurdaya_writer.py:1-37`, binding ruling §7.2). Base ayus and the per-method full-longevity constants are delegated to PyJHora's shipped `jhora.horoscope.dhasa.graha.aayu` (`:134-137`, `apply_haranas=False`, Aṃśāyu `method=2`); the reductive haranas (astangata / śatru-kṣetra / cakrapāta / krūrodaya) are explicitly deferred and every method total carries `harana_status: base_only_haranas_deferred_to_w3` (`:224,:242`). Idempotency: `replace_prior_chart_facts` scoped to the `ayurdaya` category.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1271` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_ayurdaya.py:8` (heavy: `build_ga_ayurdaya_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (partition: `fact_category = 'ayurdaya'`; `fact_category_ownership` names `ga_ayurdaya` as owner of 1 category) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 130 / 130 (Δ +0); `asset_throughput` lit / 130; seed floor literal 130 (migration 650: measured minimum across the three built charts) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions` | layer instance §2.5 |
| blast radius | census (pre-1210): direct 0 / transitive 0; seed + migration 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry in either direction) |
| code readers / served surface | `get_ayurdaya.ts:85` (declarations `read_evidence`); census table-level modules 34 (not per-asset); declared dependents 0 / 0 (no L2+ asset declares an edge to it) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the one L1 asset a tier text names for a journey: V12 / P07, P23 (lifespan and constitution; T2 §2 line 128, §5 line 338) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 4 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 781d6e28 complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 781d6e28 complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L1/rollup_saved_L1.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — only a table other assets share (chart_facts) is referenced, by 59 module(s): L0_brahmagyan/query_avastha_schemes.ts, L0_brahmagyan/query_combustion_orbs.ts, L0_brahmagyan/query_motion_state_thresholds.ts (+56 more); the served surface cannot be attributed to chart_facts by code (neve… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`/Users/Dev/suvarna-evidence/A_L1/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: cancellations (haranas) not applied | tier text V12 | real | T2 V12 / §5 line 338 asks for āyurdāya "with its inputs, cancellations, inter-authority disagreement and uncertainty, not a bare figure" (layer instance §0.1 row 1); the writer computes base ayus only and flags the haranas as a deferred refinement on each total (`ga_ayurdaya_writer.py:24-27, 224, 242`). The three-method attribution and the applicability rule are present |
| brief: `prose_fields` undeclared although `citation_human` is composed | Null, Narr | real | declarations `prose_fields: null`; `_row(...)` writes `citation_human` (`:189-199`, INSERT `:290-307`); candidate `["citation_human"]` (composition sites not individually read); CF-06 |
| brief: tier written through `provenance="single"` default | Earn | real | `_row(..., provenance="single")` (`:189`): a literal default; CF-17 |
| ga_ayurdaya-Complete.depth | Complete | information | `salience_formula_ver` never populated over the whole `chart_facts`; CF-18 |
| ga_ayurdaya-Build.history | Build | history | PARTIAL: 0 errors / 4 aborts, latest run complete; CF-10 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: only the shared table `chart_facts` is referenced; cannot attribute (offline Dens re-scan, §1); saved rev-1 PASS was table-level (34 modules); CF-04, CF-18 |
| ga_ayurdaya-Carr.detector | Carr | detector | D2 applies (T2 §5: "the disagreement between authorities"): CF-07 |
| ga_ayurdaya-Idem.pattern / Earn / Cost | Idem, Earn, Cost | stale / detector | Idem ledger row is stale (census reads PASS); CF-05, CF-12 |

## 3 · Disposition

**enrich (E)** — the asset is the only L1 asset the tiers name for a journey (V12) and it is built on a cited delegation, so it is not retired or consolidated; the shortfall is against T2's own wording for āyurdāya: cancellations. Applying the haranas is an output change that needs consumption of L1 facts (combustion, dignity, śatru-kṣetra) rather than re-derivation (§N.5), which means new `depends_on` edges — SS's call. The remaining gaps are declarations and detectors.

Approver under Track A brief §10: **Strategic Suvarṇa (output change, R5); the enrichment waits on SS**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Apply the haranas from L1 facts (the enrichment)

- **Answers:** brief gap "cancellations"; T2 V12
- **Change:** compute the four reductive haranas per method from stored L1 facts (combustion and dignity from `ga_structural`/`ga_condition`/`ga_strength` categories, śatru-kṣetra from the sign-lordship facts) and emit method totals "with haranas" beside the existing base totals (never replacing them), flagging each applied harana; do not re-derive positions or dignities (§N.5)
- **Files / declaration / migration:** `ga_writers/ga_ayurdaya_writer.py` (new rows, `harana_status` values), registry `depends_on` of `ga_ayurdaya` (new edges to the producer assets whose facts are read), `count_sql`/floor refresh; PyJHora `_pindayu(..., apply_haranas=True)` exists in the delegated library but takes combustion and benefic/malefic context the writer deliberately does not recompute (`:24-27`) — which of its inputs L1 can supply was not checked here
- **Failing-first test and mutation:** failing-first: for the canonical chart the with-haranas total is ≤ the base total for each method and each applied harana is named; mutation: drop a harana input and the total must equal the base; the existing rows must be unchanged (fingerprint of the base partition)
- **Output change:** yes (new fact keys; additive; existing keys unchanged) — SS approval (R5)
- **Blast radius:** no declared dependents (0/0); the serving surface `get_ayurdaya.ts` would show more keys; new edges move the asset from level 1 to a later level (it would wait on `ga_structural`, level 3), and its upstream hash
- **Rebuild:** **needs production rebuild** of `ga_ayurdaya` (130 rows, small): a REVIEW item for SS
- **Gate it moves:** Carr (the V12 cancellation claim becomes checkable), Count (floor refresh)
- **Fix class:** data (output change) + writer code + registry; **buildable before J1:** tier-dependent: T2 V12 wording and the declared-use contract (TG-L1-009)
- **Question for SS:** Is the harana enrichment in the first L1 wave, and which L1 producers may it read (new edges)?

### FD-2 · Declare `prose_fields` for `citation_human`

- **Answers:** Null/Narr NO_DETECTOR; CF-06
- **Change:** declare `["citation_human"]` after reading each `_row(...)` call site's `citation` argument (`ga_ayurdaya_writer.py:189`); where a site passes a constant, the entry still lists the column
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation as CF-06
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Carr D2: the three methods stay three rows and the applicability rule is served

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** a D2 check per (chart × ayanamsha): three method totals exist as separate rows, none is an average of the others, and the applicability row names the governing method; PASS only if all hold (the disagreement is carried, not resolved)
- **Files / declaration / migration:** Track E inspector tooling
- **Failing-first test and mutation:** a seeded copy with the three totals collapsed into one must FAIL
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02 per-asset assignment (D2 is T4's own example for āyurdāya disagreement)

### FD-4 · Tier literal default

- **Answers:** brief gap "provenance default"; CF-17
- **Change:** default `provenance` to `verification_vocab.UNVERIFIED_DEFAULT`
- **Files / declaration / migration:** `ga_ayurdaya_writer.py:189`
- **Failing-first test and mutation:** guard test as ga_positions FD-1
- **Output change:** none
- **Blast radius:** none (string identical)
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** writer code; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-2: undeclared
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-3 (D2): three methods
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-4: default literal
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: partition-scoped `count_sql` (`fact_category='ayurdaya'`); `fact_category_ownership` names it for 1 category (130 rows)
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 0/4: history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: category present in rows
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition (`fact_category = 'ayurdaya'`); `fact_id` is a semantic hash that excludes `build_id` (`_fact_id`, `ga_ayurdaya_writer.py:183-186`), so it is the stable identity; volatile: `build_id`, `computed_at`; after the enrichment the base-partition rows must be byte-identical.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the three-method attribution with the applicability rule and no adjudication (binding ruling §7.2); the delegation to PyJHora's cited implementation (B.10).
- **Carriage check chosen (T4 §4.1; one only):** D2 — two or three admitted authorities cover the same claim (the three methods), so the check is that the disagreement is carried as separate rows.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Is the harana enrichment in scope for the first L1 wave, and may it read `ga_structural`/`ga_condition` facts through new `depends_on` edges?
2. Is `verification_pass_status = single` the honest tier for the delegated PyJHora result, or should the three methods be cross-checked as a second derivation (D3)?
