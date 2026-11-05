---
asset_id: ga_sade_sati
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
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-11, I-26, I-21]
ledger_gap_ids: [ga_sade_sati-Idem.pattern, ga_sade_sati-Earn.build_record, ga_sade_sati-Cost.baseline, ga_sade_sati-Complete.depth, ga_sade_sati-Build.history, ga_sade_sati-Carr.detector]
---
# ga_sade_sati — Sāḍe-sātī cycles, phases, quarters, dhaiyā periods and overlays (calculation window 1950–2100)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Writes Sāḍe-sātī cycles, phases, quarters, dhaiyā periods, Saturn–Moon configurations, cancellation checks, modifier overlays, concurrent-daśā overlays and downstream cross-references into `chart_facts` (`ga_writers/ga_sade_sati_writer.py:1-45`), atomic-grain, five sanctioned JSONB fields with stated irreducibility, calculation window 1950–2100. The tier discipline is explicit: `R()` defaults to `UNVERIFIED_DEFAULT` and only the cycle/phase start, end and duration keys that `two_pass_verify_cycles()` examines (a ~7.5-year ± 600-day duration invariant and the vis < jan < anu < end ordering) carry `TWO_PASS_VERIFIED` (`:870-907, 940-957`); that check halts the build on failure.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1318` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_sade_sati.py:8` (`run`, light); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (15 categories: `sade_sati_cycle`, `sade_sati_phase`, `sade_sati_phase_quarter`, `dhaiya_period`, the shani-period family, retrograde subset, cancellation check, modifier overlay, concurrent-dasha overlay, downstream cross-reference) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 6,287 / 6,120 (Δ +167); `asset_throughput` lit / 6,287; seed floor literal 6120 (the seed comment reconciles 6,287 as 5 × (240 × 4 + 299) − 8) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `ga_strength`, `ga_panchanga`, `ga_vargas`, `ga_dashas`, `ga_structural`, `ga_nakshatra` (live and seed; seven edges) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 1; census (2026-09-30, pre-1210): direct 1 / transitive 49; seed + 1210 reconstruction names 1 direct dependent(s): `bo_laksana` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_sade_sati.ts:100` (declarations `read_evidence`); table-level 34 modules; 1 direct (`bo_laksana`) / 49 transitive dependents | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the Saturn-transit clock foundation (layer instance §2.4 row 3.10); fixed 1950-01-01..2100-12-31 window (not clock-dependent) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 21 error(s) and 9 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-05): BLOCKED: upstream dependency(ies) ga_dashas, ga_structural did not complete in this run; skipped to avoid building on incomplete data |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run fd08660c complete/skip_no_delta (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run fd08660c complete/skip_no_delta (2026-09-08) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — only a table other assets share (chart_facts) is referenced, by 59 module(s): L0_brahmagyan/query_avastha_schemes.ts, L0_brahmagyan/query_combustion_orbs.ts, L0_brahmagyan/query_motion_state_thresholds.ts (+56 more); the served surface cannot be attributed to chart_facts by code (neve… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PARTIAL; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: is an invariant check a second pass? | Earn/Carr | SS question | the `two_pass_verified` stamp rests on `two_pass_verify_cycles()` examining the same computed values for a duration and an ordering invariant (`:880-892`); it can fail, so it is a real check, but it validates internal consistency rather than a second derivation. The same question as `ga_strength`/`ga_sensitive_degree`; CF-19. The writer's comments are explicit and honest |
| brief: three allowlisted category-only selects | Narr | real | offline Narr.lint PARTIAL: `fact-category-pin` allowlisted violations at `ga_sade_sati_writer.py:1449, 1483, 1636` (CLAUDE.md §N.7 item 2: a reduction to a row needs `fact_key` pinned and a total `ORDER BY`); at `:1445-1452` the select is a prerequisite-existence `COUNT(*)` on `graha_position`/`MOON`, which is the benign case — the other two were not read; CF-15 |
| brief: Narr fidelity (declared `citation_human`; 81 mentions) | Narr | real | declared; offline: agree PASS, fidelity PARTIAL (3 test files reference the declared field in the same test function as a builder call; whether the assertion grades the sentence is not read), lint PARTIAL (above); CF-15 |
| brief: hard prerequisites read `chart_divisionals` (D10) and tier rows | Build | real | GA6 `varga_karya_bhava_per_varga` (D10) is read as a prerequisite (`:40-45`); if the builder role is RLS-blind (CF-16, I-11) the D10 cross-reference degrades or the Step-0 check halts a new build — not verified by running; rebuild only after the access fix |
| ga_sade_sati-Build.history | Build | history | PARTIAL: 21 errors / 9 aborts; latest error 2026-08-05 `BLOCKED: upstream ga_dashas, ga_structural did not complete` (cascade); CF-10 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: only the shared table (`chart_facts`) is referenced, by 59 modules; cannot attribute; CF-04, CF-18 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_sade_sati_writer.py:1876` reached at `:2152` under `owns_conn` (`:2151`); wrapper passes `conn` (`ga_sade_sati.py:20`); CF-14 |
| ga_sade_sati-Complete.depth / Earn / Cost / Carr / Idem | Complete, Earn, Cost, Carr, Idem | information / detector / stale | CF-18, CF-05, CF-07 (D3: Saturn's sign ingress dates by a second root-find); the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — tier discipline is explicit and earned where claimed, the window is fixed, and the W2 floor finding (F-D14: a floor achieved by a since-fixed writer) is resolved on main with a derived reconciliation (6,287 = 5 × (240 × 4 + 299) − 8). The open items are one tier question, a lint allowlist, a Narr test and a sequencing note.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Pin the allowlisted category-only selects

- **Answers:** offline Narr.lint PARTIAL; §N.7 item 2; CF-15
- **Change:** read `ga_sade_sati_writer.py:1483, 1636`; where a select reduces to a row, pin `fact_key` and add a total `ORDER BY`; where it is an existence check (like `:1445-1452`), record that in the allowlist reason; remove the allowlist entries
- **Files / declaration / migration:** `ga_sade_sati_writer.py:1449,1483,1636`; `platform/scripts/governance/fact_category_pin_allowlist.json` entries
- **Failing-first test and mutation:** failing-first: `check_fact_category_pinning.py` fails without the allowlist entry on an unpinned reduction; mutation: remove a pin and it fails
- **Output change:** none
- **Blast radius:** none (read selects)
- **Rebuild:** none
- **Gate it moves:** Narr (lint)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Narr golden test naming `citation_human`

- **Answers:** Narr.fidelity_test PARTIAL; CF-15
- **Change:** assert the exact cycle/phase sentences for the current native cycle (the f-strings at `:880-960`)
- **Files / declaration / migration:** a test beside `test_ga9_writer.py`
- **Failing-first test and mutation:** mutation: change a sign name in the sentence and the test fails
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent

### FD-3 · Carr D3 for the Saturn ingress dates

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** re-derive a sample of cycle start/end dates (Saturn entering the 12th from the natal Moon, and the sign exits) by a second ephemeris root-find and compare within a declared tolerance; report the examined subset (the same keys `two_pass_verify_cycles` stamps)
- **Files / declaration / migration:** Track E inspector tooling
- **Failing-first test and mutation:** a seeded shifted date must be reported
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-19** — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8). *This asset:* the invariant check: earned and explicit; the open question is the tier a consistency invariant earns
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-1/FD-2: declared; lint PARTIAL
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-3: D3
- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* reads `chart_divisionals`: D10 prerequisite; rebuild only after the access fix
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 21/9: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: `natural_key_partition` by migration 871; 15-category `count_sql`
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:1876`
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the 15 categories; the window is fixed (1950-01-01..2100-12-31), so the fingerprint is reproducible across years; volatile columns as `ga_positions`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 15-category atomic-grain cycle/phase/dhaiyā catalogue, the five JSONB irreducibles, the fixed window and the build-halting cycle invariants.
- **Carriage check chosen (T4 §4.1; one only):** D3 — Saturn's ingress/egress dates re-derived by a second root-find.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Does a consistency invariant that can fail (`two_pass_verify_cycles`) earn `two_pass_verified`, or a lower tier (CF-19)?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-03 accepted: `two_pass_verify_cycles` (bounds and ordering invariants) earns `classical_match`, not `two_pass_verified` (320 canonical rows) (I-26). A-3: the three `/usr/share/ephe` calls go through the shared helper (I-21).
