---
artifact: W3-1_REPORT
canonical_id: W3-1_REPORT
version: "1.1"
status: CORRECTIONS_APPLIED_PENDING_FOLD
produced_on: 2026-09-28
authority: NIKASHA_WAVE3_EXECUTION_PROMPT_v1_0.md
campaign_id: nikasha-wave3
runs_in: /Users/Dev/madhav-nikasha (branch campaign/nikasha-test)
reviewed_by: W3-1_REVIEW.md (d5fd6aed1, ACCEPT_WITH_CORRECTIONS)
changelog: >
  v1.1 (2026-09-28, gate-review corrections): C1-C5 + F6-F9 applied per W3-1_REVIEW.md §10 — see
  §7 "Corrections after gate review". R99 and R81 register statuses corrected PARTIAL (were
  implied CLOSED); R15/R29's hand/machine discriminator fixed (a real defect, C2); five report
  factual errors corrected (R218 cause/count, ASSET_ELEVATION_TEMPLATE fingerprint framing,
  bg_sarvatobhadra_grid finding status, criterion count, R81 fold-count); the _schema line-1
  rewrite disclosed as a precedented exception, not doc-text-scoped; two non-blocking doc/test
  fixes (F7, F8+F9) folded in as cheap. v1.0 (2026-09-28): original wave-3 packet report.
---

# Nikaṣa wave 3 — W3-1 report

Ledger crosswalk (P6), inspector leftovers (R60/R99), doc/tracker cleanup (P5 non-sealed subset),
and the planner P-need test (R218). One commit per row (§2 below), each with its own behavioural
test and a recorded mutation run. 22 commits total (17 rows + 5 proof-phase / follow-up commits,
named below).

## §1 — Per-row commit, diff summary, test, mutation evidence

### R63 — T4 "eight gates" → "nine gates" (4 places)
Commit `f7521f2ec`. `ASSET_ELEVATION_TEMPLATE_v2_0.md` lines 13/211/214/499. Test:
`test_r63_t4_nine_gates.py`. Mutation: reverted to "eight gates" → 2/3 red; byte-identical
restore; 3/3 green.

### R64 — T4 §4.2 "the six checks" → "the nine checks" (heading + Build-row cross-reference)
Commit `63608ad71`. Lines 232/241. Test: `test_r64_t4_nine_checks_heading.py`. Mutation: 2/3 red
on revert; byte-identical restore; 3/3 green.

### R66 — tracker GATES comment "Eight, not thirty-three" → "Nine, not thirty-three"
Commit `8290df39b`. `asset_elevation_tracker.py:43`. Test:
`test_r66_tracker_nine_not_thirtythree.py`. Mutation: 1/2 red on revert (the independent
GATES-length assertion stays green, proving it targets the comment specifically); byte-identical
restore; 2/2 green.

### R65 (tracker half only) — Build gate description "six static checks" → "nine static checks"
Commit `11b76578c`. `asset_elevation_tracker.py:73`. T3 §5.2/changelog half explicitly NOT
touched (D2 reopen work, sealed tier 3). Test: `test_r65_tracker_build_check_count.py`. Mutation:
2/2 red on revert; byte-identical restore; 2/2 green.

### R68 (T4 half only) — bare "NA" → closed-set "N/A" in T4's history check
Commit `2289778be`. `ASSET_ELEVATION_TEMPLATE_v2_0.md` history-check row. T3 :359/:520
("NO DETECTOR" spacing) explicitly NOT touched (D2 reopen work). Test:
`test_r68_t4_na_spelling.py` (isolates the history-check row so the doc's own already-correct
verdict-vocabulary sentence can't mask a regression). Mutation: 1/1 red on revert; byte-identical
restore; 1/1 green.

### R69 — L0 v3.0 "0/320 gates" (4 places) → 0/360
Commit `51eb7436f`. `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`. Test:
`test_r69_l0v3_0_360_gates.py`. Mutation: 2/3 red on revert; byte-identical restore; 3/3 green.

### R70 — L0 v3.0 §1.1/pilot-ledger stale figures date-stamped as pre-census-emission
Commit `05ef67651`. Chose "date-stamp" over "restate" (a restated figure goes stale on the very
next census run); historical figures kept verbatim, qualified with an explicit pointer to
re-measure from the live ledger. Test: `test_r70_l0v3_stale_figures_datestamped.py`. Mutation:
2/3 red on revert; byte-identical restore; 3/3 green.

### R77 — all five L0 pilot briefs gain the missing Build (ninth) gate row
Commit `c903cff9b`. Each brief's Build row is a REAL measurement (live, read-only
`asset_census.py --layer L0` run, 2026-09-28), not invented text: bg_ontology FAIL (completion
fails, same fact as existing G02), bg_ephemeris FAIL (same fact as G03), bg_panchanga PASS
(service, honest N/A dispositions — its own "six of eight" recomputed to "six of nine"),
bg_rules PASS (clean), bg_sarvatobhadra_grid PARTIAL (a new finding: `integrity_check_sql`
absent — noted, not registered as a ledger row, out of this row's scope). Test:
`test_r77_l0_pilot_briefs_build_row.py`. Mutation: all 5 briefs reverted via a tagged, captured-
SHA git stash (`stash apply`, never bare pop); 4/4 red; restored byte-identical (diffed against
saved post-fix copies); stash entry dropped; 4/4 green.

### R60 — `Ldgr.source_presence` gains the singular `classical_citation` column
Commit `2d83e32b4`. `asset_census.py`. Measured 2026-09-28 (information_schema): at least a
dozen L0 tables carry the singular form and got no Ldgr check at all. Test:
`test_r60_ldgr_source_presence_singular_citation.py`, runs the REAL `measure()` end to end
offline (same `_stub_layer` harness as `test_a4_gate_corrections.py`). Mutation: 1/2 red on
revert (a regression guard on the pre-existing plural/other names stays green, proving the fix
is additive); byte-identical restore; 2/2 green.

### R99 — the empty-table-with-agreeing-build-record third case (ga_prashna)
**Corrected after gate review (C3) — see "Corrections after gate review" below: this row folds as
PARTIAL, not CLOSED.** Commit `95a5fdfc4` (+ follow-up `a1272b79c`, updating the pre-existing R52
test whose own assertion this row's intended behaviour change legitimately supersedes).
`has_writer` is the one existing registry signal (no new field invented) distinguishing a
*no-writer* asset (bg_sarvatobhadra_grid: PASS, unchanged) from a *writer-backed* one — it moves a
former blanket PASS to the honest PARTIAL for any writer-backed, persistently-empty asset
(ga_prashna: 51 runs, 0 rows; plus 3 L5 assets the census independently surfaced: mi_abhilekha,
mi_seva, mi_vistara). **It does not, and the row does not claim to, distinguish a *legitimately*
empty writer-backed asset from a *broken* one** — both still read the identical PARTIAL sentence
(the reviewer demonstrated this: ga_prashna's emptiness is explainable by one query against
`prashna_charts`, 0 rows for the canonical chart; mi_abhilekha's emptiness is an upstream build
failure, 26 errors — both PARTIAL, same text). That finer distinction — "empty by design is a
layer-instance claim with its own detector" — was not built this wave; it is a named, carried
finding for a future row (§3). Tests:
`test_r99_empty_table_agreeing_build_record.py` (3 tests, both shapes + a non-empty regression
guard) — mutation 2/3 red, byte-identical restore, 3/3 green; the R52 test file's own update was
independently mutation-tested too (documented in its own commit).

### R78 — the declarative criterion registry (D4 ruling re-scope)
Commit `64b7310bb`. `CRITERION_REGISTRY` in `asset_census.py`: all 21 criteria `measure()`
actually assigns (cross-checked by parsing the source, not a second hardcoded list) plus 5 new
hand-only criteria (`Carr.D1`/`D2`/`D3`, `Completeness.depth.dasha_link`, `Earn.service_state`)
registered with `detector: "NONE"`. Honest scope note recorded in the commit and repeated below
(§3): four pre-existing criteria — `Cost.baseline`, `Count.floor`, `Complete.depth`/`.width`,
`Reach.fields` — use a gate prefix outside T4's nine (Cost/Count/Complete/Reach); this registry
catalogs that pre-existing fact rather than silently correcting it. Test:
`test_r78_criterion_registry.py`, 6 tests. Mutation: 6/6 red on removing the whole registry
block; byte-identical restore; 6/6 green.

### R79 — deterministic (asset, scope, registered criterion) lookup (D4 ruling re-scope)
Commit `08f554e02`. `gap_id_for` / `lookup_criterion`, built on R78. A specific criterion
(`Carr.D1`) and its generic placeholder (`Carr.detector`) resolve to two distinct gap ids for the
same asset — never conflated at runtime. Test: `test_r79_deterministic_criterion_lookup.py`, 6
tests. Mutation: 6/6 red on removing both functions; byte-identical restore; 12/12 green
(together with R78's own suite).

### R80 — `superseded_by` documented in the `_schema` row (retained per D4)
Commit `d198bb069`. `ledger_r81_migration.py`'s `add_superseded_by_to_schema_doc` /
`migrate_schema_line` — proven on a copy (never touching the real file in this commit).
`emit_gaps()` already read/enforced `superseded_by` at runtime before this row; R80 is
documentation catching up. Test: `test_r80_schema_superseded_by_field.py`. Mutation: a
simulated no-op regression → 2/6 red; byte-identical restore; 6/6 green.

### R81 — the 11 hand↔census overlap pairs (D4 ruling re-scope) — the ledger crosswalk
Four commits: `a6353ac23` (fold logic, proven on a copy), `7df67413a` (drop an undocumented
field), `7cec6241e` (the real-write CLI script, proven end to end on a copy),
**`67d5d1aa2` — the one authorized real write**, and `ddfc8ea8b` (test follow-up, below). Each of
the 11 pairs is re-keyed to a registered, derived `<asset>-<Gate>.<check>` criterion id (never a
hand G-numbered id kept as survivor): 5 pairs preserve the census's own already-derived id
(same criterion, or a family-alias match — folded, enriched); 6 mint a genuinely new derived id
from the hand row's own more specific, now-registered criterion (5 specific-vs-generic pairs +
group 8's partial overlap). **10 of the 11 pairs fold the other side's `measured:` reading into
the surviving row's `what`; group 8 (bg_panchanga) folds none** — its hand row `G01` is re-keyed
to its own criterion `Earn.service_state` and, per D4's explicit instruction, is never folded onto
a timing id; its two census siblings (`Earn.build_record`, `Cost.baseline`) are left untouched and
unsuperseded, each still its own live row.

**The real write** (`67d5d1aa2`): before 830 lines, md5 `7f2257a8d4f0d6a7a21c0648b4101f85`; after
857 lines, md5 `f6b1d3c5eeff7ec5d56d45448df69d80`; delta +27 lines (11 content + 16 superseding),
1 line (the `_schema` row) replaced in place, every other line preserved byte-for-byte. Verified
post-write: every line parses as JSON (857/857); re-running `--apply` against the now-migrated
real file is a confirmed live no-op (0 new rows, unchanged md5) — the idempotency proof repeated
against the real file itself, not only the copies used to develop it.

**C4 (gate review correction): the `_schema` line-1 rewrite is a disclosed, precedented exception
to strict append-only, not a claim of full append-only purity.** 829 of 830 pre-existing lines are
byte-identical and in the same position — every actual `kind=gap`/`kind=opportunity` data row is
untouched, and every fold is an appended line, never an edit or a deletion. Line 1 (the `_schema`
documentation row) is the one line this migration rewrites in place, changing only its `_doc`
field's text (the field list gains `superseded_by`; a clause is appended) — its keys are
unchanged, and its original bytes survive verbatim in git history and in
`_r81_pre_migration_fixture.PRE_MIGRATION_SCHEMA_ROW`. This is not new: commit `a72cdf460` already
rewrote this same line in place once before, to add `kind` to the field list — the same mechanism,
disclosed the same way, is used again here. The apply script's own docstring previously claimed
this in-place rewrite was authorized "per the `_schema` doc's own text" (implying the doc itself
carves out an exception); the `_schema` row's `_doc` field contains no such carve-out — it says
only "Append-only" — so that phrasing was the builder's own reading stated as a quotation. Fixed
in the docstring itself (a separate commit, `apply_r80_r81_ledger_migration.py`): the real
justification is precedent (`a72cdf460`), not doc text, and is now stated as such.

Test: `test_r81_ledger_overlap_fold.py` (13 tests: synthetic same-criterion / distinct-criterion /
partial-overlap / idempotency / missing-row cases; a FROZEN pre-migration fixture
(`_r81_pre_migration_fixture.py`, transcribed verbatim from T5_LEDGER_DRIFT.md §A) proving the
algorithm's real shape — 27 rows, 11 content + 16 superseding — independent of the real ledger's
mutable current state; and genuine post-migration confirmations against the real, now-migrated
ledger) + `test_r81_apply_script.py` (5 tests, the CLI script's own `main()` end to end against a
synthetic pre-migration copy, plus one dry-run-only confirmation against the real file). Mutation:
a simulated `superseded_by`-omission regression → 7/10 red (fold logic); 15/24 red across all
three R81-related test files when `OVERLAP_PAIRS` is renamed. Byte-identical restores confirmed
throughout; full suites green after restore.

### R15 + R29 — the hand/machine rule: hand rows carry `census_run_id`
Commit `02182bf2c` (+ gate-review correction `68044d4c8`, C2 — see below). Documents (comment in
`asset_census.py`, at `generated`'s assignment) that the census's own `generated` ISO timestamp IS
the census_run_id — no second identifier invented. Enforces (`hand_row_provenance.py`):
`missing_census_run_id(rows)` flags hand-written, judgemental rows missing the field, scoped to
`ts >= CUTOFF_TS` (2026-09-29, the day AFTER this wave) — the same grandfather pattern the
ledger's own `_schema` doc already uses for `kind`. R81's own 22 hand-owned migration rows (`ts` =
this wave's date) are honestly grandfathered rather than either silently exempt forever or falsely
flagged, since retroactively adding `census_run_id` to them would need a second real write this
wave's hard constraint forbids. Test: `test_r15_r29_hand_row_census_run_id.py`, 8 tests (9 after
C2) including a real-ledger packet-proof (zero violations against all 857 current rows). Mutation:
2/8 red on an always-empty regression; byte-identical restore; 8/8 green.

**C2 correction (commit `68044d4c8`):** the landed `is_hand_written()` keyed on `owner !=
"asset_census"`, but `emit_gaps()` deliberately carries a hand-owned id's `owner` forward onto its
own machine-written CLOSED/RE-OPENED transition rows (R81 made five census-derived ids hand-owned
this way). The independent reviewer demonstrated this misreads a census-written transition row as
hand-written from 2026-09-29 onward. Fixed to discriminate on `detector` (every row `emit_gaps`
itself writes sets `detector="asset_census.py --layer … (…)"`, regardless of the carried owner).
New test `test_owner_only_discriminator_would_have_flagged_a_census_transition_on_a_hand_owned_id`
reproduces the reviewer's exact fixture. Mutation: reverting to the owner-only check → 1/9 red
(isolates exactly this scenario); byte-identical restore; 9/9 green.

### R218 — the planner P-need test (D5 rev. 2.1)
Commit `48efa19ea`. D5 rev. 2.1 replaced the withdrawn static necessity matrix with a live
behavioural test: run P01–P24 through the REAL planner projection
(`buildPlannerCapabilityKnowledgeProjection`, `platform/src/lib/retrieval/registry/knowledge/
planner_projection.ts` — the function `platform/src/lib/retrieval/adapters/agentic_loop/`'s
planning path and Pariprāśna's synthesis path actually call; **not** a re-implemented search, and
**not** the `plan_retrieval` MCP tool, which is a separate, fixed-floor "Vidhi Engine (D-2)
fallback path" per its own tool description — D5 rev. 2.1's own dependency line names
`planner_projection.ts` as authority for what "the planner searching the SCU snapshot" means).
Full per-P-need results in §4 below. Test:
`platform/src/lib/retrieval/registry/knowledge/__tests__/r218_p_need_check.test.ts`, 5 tests
(vitest) — mutation: an always-pass regression → 3/5 red; byte-identical restore; 5/5 green.
Wider check: `npx vitest run src/lib/retrieval` — 227 files, 2517 tests, unaffected.

## §2 — Rows NOT done, and why

None. All 17 rows in scope (R78, R79, R80, R81, R15, R29, R60, R99, R63, R64, R65 tracker-half,
R66, R68 T4-half, R69, R70, R77, R218) were completed. No row was stopped for touching a sealed
tier — the sealed-tier halves explicitly excluded by the register itself (R65 T3-half, R68
T3-half) were the ones scoped out from the start, per the wave prompt's own condensed pointer;
they were never attempted.

## §3 — Out-of-scope findings, named but not fixed

1. **T4's own residual "six static checks" line** (`ASSET_ELEVATION_TEMPLATE_v2_0.md`, §4.2's
   `measured_by:` line: "six static checks over the writer, the registry and the build record —
   all read-only; plus the runtime state below") contradicts the same file's own "All nine checks
   run read-only" text a few lines below. Not named by R63, R64 or R65 in the register (R65 names
   only T3 §5.2/changelog and the tracker comment as the "six" side; it treats T4 as "already
   nine"), so left untouched rather than assumed in scope.
2. **R78's gate-taxonomy quirk**: `Cost.baseline`, `Count.floor`, `Complete.depth`/`.width`,
   `Reach.fields` use a gate prefix (Cost/Count/Complete/Reach) outside T4's nine
   (Ldgr/Idem/Earn/Null/Vocab/Carr/Narr/Dens/Build). Cataloged as-is by the new registry, not
   reconciled — that would be a taxonomy change, not a registration of what exists.
3. **bg_sarvatobhadra_grid's missing `integrity_check_sql`** (surfaced by R77's real Build-gate
   measurement: Build.count_integrity reads PARTIAL). **Corrected after gate review (C1c) — this
   is NOT a new finding.** `bg_sarvatobhadra_grid-Build.count_integrity` ("count_sql=yes,
   integrity_check_sql=no") has been a live, `OPEN` census ledger row since 2026-09-26 (pre-write
   ledger line 183, predating this wave entirely) — R77's Build row simply reports a pre-existing,
   already-registered gap, correctly, not a new one. No new ledger identity was needed or minted.
4. **T5_LEDGER_DRIFT.md's own proposed register rows L4/L5** (rotate `ASSET_ELEVATION_TEMPLATE`'s
   fingerprint; dispose the two `schema_db_unreachable` LOWs) are not part of this wave's named
   row list (R78–R81, R15, R29, R60, R99, R63/64/65/66/68/69/70/77, R218) and were not actioned.
5. **F6 (W3-1_REVIEW.md §2, demonstrated on a copy): superseding a *generic* census criterion
   permanently mutes it for that asset.** Once `bg_rules-Carr.detector` (or any of the four other
   Carr-superseded assets' generic ids) is superseded onto a specific id (`bg_rules-Carr.D1`), a
   FUTURE regression on the generic criterion — e.g. `bg_rules-Complete.depth` newly FAILing on a
   *different* column than the one folded — is never recorded: the gid is `ever_superseded` and
   `emit_gaps` skips it, uncounted, forever. This is the designed effect of the D4 crosswalk
   (§N.8's "the honest form" for a specific criterion superseding its generic placeholder), not a
   builder defect, but it is a real coverage loss the native should see before relying on the
   generic criteria for the five superseded assets going forward. Raised as a D4 follow-up, not
   fixed this wave.
6. **F7 (W3-1_REVIEW.md §7): L0 v3.0 line 526 ("5. **Briefs and gates** — 40 briefs, **320
   gates**") is the same "0/320" self-contradiction R69 fixed at 4 other locations, missed at this
   fifth one.** Fixed in this correction pass — see "Corrections after gate review" below.

## §4 — R218 per-P-need report

PASS criterion: the TOP-RANKED resolved capability (the planner's primary resolution) carries a
named producer. Full aggregate (`producer_coverage`) reported per need so a reviewer can judge
the interpretation independently. 17 of 24 PASS.

| P-need | verdict | top-ranked resolution | producer coverage | reason |
|---|---|---|---|---|
| P01 | FAIL | `scu.catalog.assess_career` | 19/32 | no named producer |
| P02 | PASS | `scu.catalog.query_vastu_directions` | 20/32 | `bg_vastu_directions` |
| P03 | PASS | `scu.catalog.list_remedies_by_category` | 22/32 | `bg_remedies` |
| P04 | PASS | `scu.bodha.mechanism.network` | 22/32 | `bo_yantra_mechanism` |
| P05 | FAIL | `scu.catalog.assess_marriage` | 20/32 | no named producer |
| P06 | PASS | `scu.yoga.firing_and_cancellation` | 20/32 | `ga_yoga, bo_laksana, ka_kalasutra` |
| P07 | FAIL | `scu.catalog.compose_large_n` | 18/32 | no named producer |
| P08 | PASS | `scu.bodha.mechanism.network` | 20/32 | `bo_yantra_mechanism` |
| P09 | PASS | `scu.finance.prosperity_assessment` | 21/32 | `bo_cdlm_summary, bo_vargottama_dhana` |
| P10 | PASS | `scu.finance.prosperity_assessment` | 23/32 | `bo_cdlm_summary, bo_vargottama_dhana` |
| P11 | PASS | `scu.catalog.query_moorti_nirnaya` | 22/32 | `ka_moorti_nirnaya` |
| P12 | PASS | `scu.catalog.get_yoga_dosha` | 19/32 | `ga_sensitive, ga_sade_sati, ga_panchanga, ga_positions, ga_ayurdaya, ga_sensitive_degree, ga_nakshatra, ga_yoga` |
| P13 | FAIL | `scu.catalog.graha_portrait` | 20/32 | no named producer |
| P14 | PASS | `scu.bodha.mechanism.network` | 21/32 | `bo_yantra_mechanism` |
| P15 | PASS | `scu.finance.prosperity_assessment` | 20/32 | `bo_cdlm_summary, bo_vargottama_dhana` |
| P16 | PASS | `scu.bodha.mechanism.network` | 21/32 | `bo_yantra_mechanism` |
| P17 | PASS | `scu.catalog.query_question_lenses` | 21/32 | `bo_drishti` |
| P18 | FAIL | `scu.catalog.assess_career` | 22/32 | no named producer |
| P19 | PASS | `scu.catalog.query_manifestation_sets` | 22/32 | `mi_sambandha` |
| P20 | PASS | `scu.catalog.get_dispositors` | 17/32 | `ga_sensitive, ga_sade_sati, ga_panchanga, ga_positions, ga_ayurdaya, ga_sensitive_degree, ga_nakshatra` |
| P21 | FAIL | `scu.catalog.call_priority_ranking` | 20/32 | no named producer |
| P22 | PASS | `scu.finance.prosperity_assessment` | 22/32 | `bo_cdlm_summary, bo_vargottama_dhana` |
| P23 | FAIL | `scu.catalog.compose_large_n` | 18/32 | no named producer |
| P24 | PASS | `scu.finance.prosperity_assessment` | 23/32 | `bo_cdlm_summary, bo_vargottama_dhana` |

**Corrected after gate review (C1a) — this paragraph was wrong on both count and editorial
status; see below.** All 7 FAILs resolve to exactly **5** distinct capabilities — `assess_career`
(P01, P18), `assess_marriage` (P05), `compose_large_n` (P07, P23), `graha_portrait` (P13),
`call_priority_ranking` (P21) — and every one of the 5 is measured **`editorial: true`** (reviewed,
served capabilities), not `editorial: false` routing stubs. The real cause, per Lane B's
`producer_provenance.derived.json`: `assess_career`, `assess_marriage`, `compose_large_n` and
`graha_portrait` each carry `NO_DETECTOR — no_contract: no availability_contracts requirement and
no reviewed_output claim` — they are composite orchestrators (`assess_career`'s own description:
"Orchestrates query_domain_reading … query_temporal_activation … query_contradictions"), and their
real producers sit one composition hop away that the current provenance derivation does not
traverse. `call_priority_ranking` carries `NO_DETECTOR — no_relation_in_range` — it is a service
wrapper (`ka_tulana`) with no table in the resolved source range. This is a real, consistent
finding (the same 5 reviewed capabilities account for all 7 FAILs), naming a concrete future
worklist — "producer provenance through composition and service edges" — not "review 3 unreviewed
stubs".

## §5 — Packet proof (§4 of the wave prompt)

1. **Six-layer census, HEAD vs wave-2 close (`31b3e1024`).** Live, read-only census run at both
   revisions (the old `asset_census.py` checked out from `31b3e1024` and run standalone against
   the SAME production DB, chart 482012f1), diffed verdict-by-verdict across all six layers.
   **15 verdict-level changes total, every one attributable to R60 or R99, nothing else moved:**
   - **11 changes are R60** (`Ldgr.source_presence` newly firing PASS/PARTIAL where it was
     previously absent — the singular `classical_citation` column now recognised):
     `bg_dignity_reference`, `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_sign_medical`,
     `bg_transit_engine`, `bg_transit_rules`, `bg_vastu_directions` (L0); `ga_medical`,
     `ga_vastu` (L1); `ka_gochara_resonance`, `ka_vedha_gochara` (L3).
   - **4 changes are R99** (`Build.completion` PASS → PARTIAL for a writer-backed, persistently-
     empty asset under a `target_floor=0` declaration): `ga_prashna` (L1, R99's own named case),
     `mi_abhilekha`, `mi_seva`, `mi_vistara` (L5 — the same defect class, independently
     confirmed present in L5 too).
   - Zero changes in any criterion R60/R99 did not touch; zero changes from R78/R79/R80/R81/R15/
     R29 (none of which alter `measure()`'s verdict logic — R78/R79 add a registry alongside it,
     R80/R81 touch only the ledger file, R15/R29 add a separate, non-measure()-touching check).
2. **Ledger crosswalk proof.** Covered in full under R78–R81/R15/R29 above; the real R81
   migration's before/after state: 830→857 lines, md5 `7f2257a8d4f0d6a7a21c0648b4101f85` →
   `f6b1d3c5eeff7ec5d56d45448df69d80`.
3. **`emit_gaps` dry run on a fresh copy.** Real ledger copied to scratch (`NIKASHA_CONTROL_DIR`
   override), `asset_census.py --layer L0 --emit-gaps` run twice: first run appended 0, closed 26
   (all `Idem.pattern` — genuine re-measurement drift unrelated to any code this wave touched,
   confirmed by inspecting every closed gap_id), 0 re-opened; second run on the same copy: 0
   appended, 0 closed, 0 re-opened — confirmed idempotent. No row of any criterion this wave
   touched (`Ldgr.source_presence`, `Build.completion`) was silently reclassified. Real ledger
   untouched throughout (md5 unchanged).
4. **R218 planner-test report.** §4 above.
5. **Full suite + manifest + drift + ledger md5.**
   - Governance test suite: 421 collected (395 passed, 24 skipped, 2 failed — both
     `test_drift_detector_h35_h38.py`, confirmed pre-existing by re-running against a temporarily
     stashed-out `asset_census.py`, i.e. unrelated to any file this wave touched). Baseline at
     wave-2 close (`31b3e1024`): 351 tests. +70 new tests this wave (17 new test files + 1 file
     extended).
   - `manifest_fingerprint.py --check`: `entries: 141 (declared 141)`, fingerprint MATCH.
   - `drift_detector.py`: exit **2** (not the packet's stated 0/3 floor) — **explained, not
     silent**: 2 HIGH `fingerprint_mismatch` findings, both *expected* consequences of this
     wave's own legitimate content edits, not caught by anything this wave broke:
     - `ASSET_ELEVATION_TEMPLATE` (edited by R63/R64/R66/R68/R77). **Corrected after gate review
       (C1b) — this finding is NEW this wave, not pre-existing.** By base commit `c8cdc0242` the
       row's declared fingerprint (`4927436c…`) already MATCHED the file's own sha256 at base —
       the earlier, v1.1→v2.0-era mismatch T5_LEDGER_DRIFT.md documented (declared `bb341cc1…`)
       had already been rotated and closed before this wave opened. This wave's own R63/R64/R66/
       R68/R77 edits are what produced the new mismatch (observed `ff911384…` at HEAD).
     - `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY` (edited by R69/R70) — also new this wave, same
       cause: a legitimate content edit whose `CANONICAL_ARTIFACTS` fingerprint row has not been
       rotated. Fingerprint rotation is explicitly the executor's job at fold-time, not the
       builder's (CLAUDE.md §D / wave prompt §5: "fingerprints rotated last"), so both HIGHs are
       expected to persist until the executor folds this wave's rows — named here, not fixed.
     - The 1 LOW (`a3_category_not_yet_populated`) is a pre-existing, unrelated soft check.
   - Production ledger (`asset_gaps.jsonl`) md5: unchanged at `7f2257a8d4f0d6a7a21c0648b4101f85`
     for the entire wave except the one named, isolated R81 real-write commit (`67d5d1aa2`),
     after which it is `f6b1d3c5eeff7ec5d56d45448df69d80` — confirmed unchanged by every commit
     before and after that one.

## §6 — Honest limits

- R218's PASS criterion (top-ranked resolution must carry a producer) is this harness's own
  explicit interpretation of R218's prose, not a native ruling — reported alongside the full
  producer-coverage aggregate specifically so a reviewer can judge or overrule it. F8 (gate
  review): the criterion is semantically weak in places (several PASSes resolve through a few
  catch-all SCUs — `finance.prosperity_assessment` alone accounts for P09/P10/P15/P22/P24's
  PASS), and the live test's `summary.failed > 0` assertion is an anti-invariant: it will turn red
  the day the 5 provenance gaps this wave found are fixed and all 24 pass, encoding today's known
  defect as if it were a permanent property. Neither blocks this packet; both are recorded here so
  17/24 is read as a snapshot of today's producer-provenance coverage, not as a stable ceiling, and
  so a future session updates the test's assertion deliberately rather than being surprised by it.
  F9 (cosmetic): P16's transcribed question text is a faithful paraphrase merging two of T1's
  quoted phrasings, not a verbatim single quote.
- **R81's register status is PARTIAL, not CLOSED, against D4's full re-scope — and that is by this
  wave's own explicit, committed design, not a shortfall.** T5_LEDGER_DRIFT.md §A measured exactly
  11 hand↔census overlap pairs; that is the entire overlap set T5 ever found or claimed. The
  register's D4 re-scope (register v2.6, R81's status column) separately describes a broader
  ambition — "a reviewed migration table over all 30 hand gap rows across the five pilots" (10
  ontology + 8 rules + 6 ephemeris + 4 panchanga + 2 sarvatobhadra) — because D4's identity rule
  ("hand-written gap rows use a registered criterion") implies every hand row, not only the 11
  that happen to overlap a census row, should eventually resolve through a registered criterion.
  **This wave's own execution prompt (§3, the R81 bullet) explicitly narrows the wave's committed
  scope to the 11 T5-measured pairs, not the register's fuller 30-row ambition** — so R81 is
  **COMPLETE against what this wave committed to**, and **PARTIAL (11 of 30) against the
  register's full D4 re-scope**, both true at once. The independent reviewer's own §5 measurement
  confirms the gap concretely: 42 criterion strings still in live use by hand rows are
  unregistered (e.g. `Earn.count_sql_scope`, `Completeness.universe_blocked`, `Vocab.future_gate`,
  `Synergy.*`, `Architecture.*`) — the remaining ~19 hand rows (30 minus the 11 folded) and this
  42-string tail are named here as a future row's worklist, not silently treated as done.
- Four out-of-scope findings named in §3 are real and worth a future row, not silently fixed.

## §7 — Corrections after gate review (v1.1)

Independent review: `W3-1_REVIEW.md` (commit `d5fd6aed1`, reviewer Claude Opus 5.5, fresh context,
read-only). Verdict: **ACCEPT_WITH_CORRECTIONS**. Every correction below is named, committed and
mutation-tested (where the correction is a behaviour, not a document statement) exactly as the
review required. Nothing here required a second write to the real ledger.

| # | correction | commit(s) | test | mutation evidence |
|---|---|---|---|---|
| **C2** | The hand/machine discriminator (`is_hand_written`) keyed on `owner`, which `emit_gaps()` deliberately carries forward onto its own machine-written CLOSED/RE-OPENED transition rows — a census-driven transition on one of R81's five newly hand-owned ids misread as a hand row from 2026-09-29 onward. Fixed to key on `detector` (every row `emit_gaps` writes sets a fixed `asset_census.py …` prefix, regardless of carried owner). **The substantive fix.** | `68044d4c8` | `test_r15_r29_hand_row_census_run_id.py` (+1 test, 9 total) | Reverted `is_hand_written` to the owner-only check → 1/9 red (isolates exactly the new reproducing test); byte-identical restore; 9/9 green |
| **C1** | Report factual corrections: (a) R218 FAIL cause was "3 `editorial=false` stubs", corrected to 5 `editorial=true` reviewed capabilities with a named Lane-B-provenance cause (`no_contract` ×4, `no_relation_in_range` ×1); (b) the ASSET_ELEVATION_TEMPLATE fingerprint mismatch was called pre-existing/unrotated, corrected to NEW this wave (it matched at base `c8cdc0242`); (c) bg_sarvatobhadra_grid's missing `integrity_check_sql` was called a new finding, corrected to a pre-existing OPEN ledger row since 2026-09-26; (d) "20 criteria" corrected to 21; (e) R81's "each … folding" corrected to 10 of 11 (group 8 folds none, by D4 design) | `2f00a6b45` | — (report text) | — (no behaviour changed; each correction independently re-verified against the live snapshot/provenance/ledger/git history before being written, per §1 above) |
| **C3** | R99's register status corrected from (implied) CLOSED to **PARTIAL**: `has_writer` separates no-writer from writer-backed, full stop — it does not distinguish a legitimately-empty writer-backed asset (ga_prashna) from a broken one (mi_abhilekha), both of which read the identical PARTIAL sentence today. The finer "empty by design, its own detector" half of R99's register text was not built; named as a carried finding for a future row, not implied as solved | `2f00a6b45` (same commit as C1, the R99 paragraph serves both) | — (report text; code unchanged — this is the reviewer's own sanctioned fallback: "if that's a larger change than fits here, leave the code as-is and just correct the report") | — |
| **C4** | The `_schema` line-1 in-place rewrite was justified in the apply script's docstring as authorized "per the `_schema` doc's own text" — the doc contains no such carve-out. Corrected to the real justification: precedent (commit `a72cdf460` already rewrote the same line once, to add `kind`), disclosed plainly as the one exception to strict append-only (data rows are, and remain, append-only; only the one documentation line is ever rewritten in place) | `5fcc0989e` | `test_r81_apply_script.py` re-run (docstring-only change) | 5/5 green, unchanged (no behaviour change) |
| **C5** | R81's register status corrected from (implied) CLOSED to **PARTIAL (11 of D4's 30 hand rows)** — confirmed against T5_LEDGER_DRIFT.md (which measured exactly these 11 pairs, its entire overlap set) and the register's D4 re-scope (which separately ambitions all 30). This wave's own execution prompt explicitly committed to only the 11 — so R81 is COMPLETE against this wave's commitment and PARTIAL against D4's fuller scope, both stated | `8c279e23e` | — (report text) | — |
| **F6** (non-blocking) | Recorded: superseding a generic census criterion (e.g. `bg_rules-Complete.detector`→`Complete.depth`) permanently mutes future regressions on that criterion for that asset — the designed effect of the D4 crosswalk, raised as a follow-up, not fixed | `2f00a6b45` | — | — |
| **F7** (non-blocking) | L0 v3.0 line 526's missed fifth "320 gates" occurrence (R69 fixed 4, missed this one) — fixed to 360 | `04a9e8c93` | `test_f7_l0v3_line526_320_gates.py` (new) | 2/2 red on revert; byte-identical restore; 2/2 green |
| **F8+F9** (non-blocking) | R218's live test asserts `failed > 0`, a snapshot-in-time anti-invariant that will itself go red once the 5 provenance gaps are fixed — annotated in place so that is read as progress, not regression. P16's harness text was a paraphrase, not verbatim — corrected to T1's exact quoted text (re-verified: same 17/24 result, same P16 resolution) | `383053e9c` | `r218_p_need_check.test.ts` re-run | 5/5 green, unchanged (no behaviour change) |

**Re-verification after all corrections (this section):**
- Six-layer census, HEAD (post-corrections) vs wave-2 close (`31b3e1024`): re-run in full; still
  exactly 15 verdict changes, still all attributable to R60/R99 alone — no correction commit
  touches `asset_census.py`'s `measure()` logic (C2 touches `hand_row_provenance.py` only; F7 is a
  doc-only fix; F8/F9 touch TS test/lib files only), so this result is structurally guaranteed
  unchanged and was re-confirmed live. **Disclosed anomaly, diagnosed and resolved:** the first
  re-run attempt (run concurrently with the `emit_gaps` re-run and `drift_detector.py` below)
  returned 43 verdict changes, 28 of them spurious `ERRORED`/`None` readings on unrelated L2
  `bo_*` assets. Root cause, read directly from the `measured:` text: `psql: FATAL: remaining
  connection slots are reserved for non-replication superuser connections` — the read-only DB's
  connection pool was exhausted by running this census alongside other concurrent DB-touching
  processes in the same session, not any change in the codebase or production data. A clean,
  isolated second re-run (nothing else touching the DB concurrently) reproduced the original,
  correct 15-change result exactly. Named here rather than silently discarded, per §N.8: an
  anomaly gets a real diagnosis, not a re-roll assumed clean.
- `emit_gaps` dry run, re-run on a fresh copy of the (still 857-line, still
  `f6b1d3c5eeff7ec5d56d45448df69d80`) real ledger: first run 0 appended / 184 present / 26 closed
  (all `Idem.pattern`) / 0 re-opened; second run 0 / 183 / 0 / 0 — idempotent, identical to the
  original proof. Real ledger md5 confirmed unchanged throughout.
- Governance test suite: **424 collected = 398 passed + 24 skipped + 2 failed** (the same 2
  pre-existing `test_drift_detector_h35_h38.py` failures; +3 tests over the original 421: +1 from
  C2, +2 from F7).
- `npx vitest run src/lib/retrieval`: 227 files, 2517 tests, unaffected by C2/F8/F9 (none of which
  touch production TS source — C2 is Python-only; F8/F9 touch only the R218 test/lib pair already
  counted in that 2517).
- `manifest_fingerprint.py --check`: `entries: 141 (declared 141)`, MATCH — unchanged.
- `drift_detector.py`: exit **2**, unchanged in kind — the same 2 HIGH `fingerprint_mismatch`
  findings (ASSET_ELEVATION_TEMPLATE, MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY; the latter's
  observed hash shifted again after F7's own edit to that file, still unrotated either way) plus
  the same 1 LOW. **Expected and correct per the review (§8): fingerprint rotation is the
  executor's job at fold-time — not performed here.**
- Production ledger (`asset_gaps.jsonl`) md5: confirmed unchanged at
  `f6b1d3c5eeff7ec5d56d45448df69d80` across every correction commit in this section — no
  correction touched the real ledger; the one authorized write (R81, commit `67d5d1aa2`) remains
  the only commit in this wave's entire history that ever did.

**Not done, with the exact reason:** nothing from C1–C5 was left undone. The one item the review
offered a choice on — C3's "add the one-query by-design distinction" vs. "leave the code as-is and
correct the report" — took the report-only path, per the review's own explicit sanction, because
building a genuinely correct per-asset by-design detector (distinct from the "by-design" gloss the
review itself flagged as an invented judgement on `bg_sarvatobhadra_grid`, §3) is real design work
warranting its own row and mutation-tested implementation, not a same-session bolt-on.
