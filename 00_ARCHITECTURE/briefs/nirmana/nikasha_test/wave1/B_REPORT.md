---
artifact: NIKASHA_WAVE1_LANE_B_REPORT
canonical_id: NIKASHA_WAVE1_LANE_B_REPORT
version: "2.0"
status: SUBMITTED — corrections after gate REJECT (packet_commit 4e586118d, reviewed 2026-09-27)
produced_on: 2026-09-26/27 (v1.0) / 2026-09-27 (v2.0 corrections)
lane: B (the catalog names its producers) — R85, D5 rev. 2.1
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4
builder: Claude (Sonnet), Lane B sub-agent
gate_review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW.md (verdict REJECT; corrections C-1..C-6 in its §3)
---

# Nikaṣa wave 1 — Lane B report (the catalog names its producers)

**This version (2.0) states only what reproduces as of the corrections below.** The
original submission (packet_commit `4e586118d`) was REJECTED at the gate
(`B_REVIEW.md`). Every figure in this document was re-verified against the
POST-CORRECTION pipeline this session, not carried over from the rejected v1.0 text —
where a v1.0 figure changed as a side effect of a correction (not just a rewording), that
is stated explicitly.

## 0 — Scope discipline note (read before anything else)

The root `CLAUDECODE_BRIEF.md` in this worktree (`/Users/Dev/madhav-nikasha`) governs a
DIFFERENT, unrelated, still-ACTIVE campaign ("L3 Kāla data-plane elevation", authored
2026-09-20). Per `CLAUDE.md` §C item 0 its `may_touch`/`must_not_touch` would normally
override all other scope guidance for this session. It does not name this Nikaṣa wave-1
task, the D5/R85 provenance work, or any file this lane touches — the branch's own commit
history shows this worktree has in fact been running the Nikaṣa campaign for many
cycles, so the root brief reads as a stale pointer left over from a different
worktree/branch context, not a live constraint on this work. I did not edit it (editing
`CLAUDECODE_BRIEF.md` is itself gated and out of my lane). I proceeded with the explicit,
detailed, native-authorized Lane B assignment (`NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md`)
and, for this corrections pass, the gate's own `B_REVIEW.md`. **Registering this, not
fixing it or the brief file** — a native/executor call on which governing-scope pointer
is live in this worktree is outside my lane.

## 1 — Files touched, and why

| File | Status | Reason |
|---|---|---|
| `platform/scripts/governance/catalog_provenance.py` | modified (6 commits) | C-1..C-6 corrections, each below. |
| `platform/scripts/governance/__tests__/test_catalog_provenance.py` | modified (6 commits) | New/rewritten tests per correction, each with recorded mutation evidence. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json` | regenerated | B-1 output, re-derived after every correction. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/CLOSURE_REPORT.md` | regenerated | B-2 output, re-derived after every correction. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/BUILD_DEPENDENCIES_READER_SCAN.md` | regenerated | B-3 output; now excludes this lane's own wave1/ prose (C-5). |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REPORT.md` | rewritten (this file) | v2.0, corrections pass. |

Not touched: any writer, the orchestrator, `editorial.ts`, `compiler.ts`, the
register/plan/decisions/STATE files, `asset_census.py`, `asset_elevation_tracker.py`,
`00_ARCHITECTURE/control/*.jsonl`, `nikasha_test/harness/**`, `wave1/A_REPORT.md`,
`wave1/a2_t3_proof/**` (Lane A's territory).

## 2 — Corrections after gate review (C-1 … C-6)

Each correction below maps to one commit on `campaign/nikasha-test`, its own test(s), and
a recorded mutation run (the mutation applied, the exact tests that failed under it, then
reverted and reconfirmed green). C-2 and C-4 share one commit because they are the same
underlying code fix (`resolve_segment_text`'s out-of-range honesty) reached from two
different gate-blocking findings; every other correction is its own commit.

| # | commit | what it fixes | test(s) | mutation run |
|---|---|---|---|---|
| C-1 | `a4fef0f7c` | Removed the catch-all NO_DETECTOR fallback in `derive_all`; `--check` now reads the committed `producer_provenance.derived.json` via new `validate_derived_artifact()` against a closed `NO_DETECTOR_REASON_CLASSES` set, instead of re-deriving in memory. | `test_producer_output_requirement_with_no_claims_gets_an_exact_reason_not_a_catchall`, `test_derive_all_leaves_a_genuinely_unclassified_scu_without_a_fabricated_reason` (superseded by C-5's rename below), `test_classify_no_detector_reason_is_a_closed_set`, `test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry` | Restored the catch-all (`"; ".join(...) or "NO_DETECTOR — no source_query requirement"`) → 1 failed, 12 passed (the constructed route_evidence_only orphan regressed to a fabricated generic reason). Reverted; 13 passed. |
| C-2 + C-4 | `6fa514fc5` | `resolve_segment_text` now returns `(text, out_of_range_reason)` distinguishing missing-file / out-of-bounds / genuinely-resolved. New `source_ref_out_of_range` reason class, taking priority over "resolved, no relation" even when another segment in the same `source_ref` did resolve. New `compute_segment_resolution_counts()` recounts every source_query SCU's declared pieces bounds-checked. | `test_unresolvable_range_yields_no_detector_with_reason` (rewritten to assert 3 distinct exact classes), `test_compute_segment_resolution_counts_distinguishes_full_partial_none` | Removed the bounds-check guard (`if a < 1 or b > n or a > b: return None, ...`) → 2 failed ( both tests above), 12 passed. Reverted; 14 passed. |
| C-3 | `91658a6a9` | (a) `one_hop_helper_texts` skips any call match immediately preceded by `def`/`function` — a definition header is not a call. (b)/(c) new `classify_segment_kind()` excludes migration- and writer-path segments from producing relation candidates (they still count toward "resolved" for out-of-range purposes, never toward producers). Producer gained `via_helper` for auditability. | `test_one_hop_follower_skips_a_definition_header_not_a_call`, `test_migration_segment_is_never_a_producer_source`, `test_writer_segment_input_read_is_never_a_producer_source` | Removed the def-prefix guard → 1 failed, 16 passed (`ga_decoy` reappeared via `via_helper='unrelated_function'`). Removed the segment-kind exclusion → 2 failed, 15 passed (`bg_decoy`/`bg_texts`/`bg_text_index` reappeared). Reverted each; 17 passed. |
| C-5 | `f1e244c09` | New `get_non_reviewed_producer_output_claims()` carries a claim whose disposition is anything other than `reviewed_output` (today: `route_evidence_only` for `ka_kalasutra`) through `derive_all` under its OWN disposition — never dropped, never relabeled. New `WAVE1_DIR` exclusion in the reader scan, alongside the existing `PROVENANCE_DIR` one. | `test_producer_output_claim_with_non_reviewed_disposition_is_carried_through` (renamed/rewritten from C-1's interim test), `test_reader_scan_excludes_its_own_wave1_report_and_review` | Removed the non-reviewed carry-through loop → 1 failed, 16 passed (regressed to `producers=[]`). Removed the `WAVE1_DIR` exclusion → 1 failed, 17 passed (20 synthetic prose lines reappeared as hits). Reverted each; 18 passed. |
| C-6 | `875809a7b` | New `_domain_stem()` + `compute_closure_report`'s `reason_class_and_text()`: a still-outside asset sharing a domain stem with a `relation_unowned_by_registry` table now reports `table_unregistered (<tables>)`, distinct from the generic `no_unit_names_it`. | `test_still_outside_asset_with_a_same_domain_unowned_table_reads_table_unregistered` | Removed the `table_unregistered` branch → 1 failed, 18 passed (`bg_prashna_rules` misreported as the generic reason). Reverted; 19 passed. |

Final state: **19/19 tests pass** (`python -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -v`).

## 3 — B-1: the derivation (post-corrections)

### 3.1 — Read-only DB verification

```
$ source .../pgenv.sh   # pre-resolved read-only DSN, port 5433
$ psql -Atc "SHOW default_transaction_read_only"
on
```

### 3.2 — Population (R220), unchanged from v1.0

`SELECT count(*) FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE` → **127**.
`dead_flag` is `NULL` on every row today, so the literal `is_active AND NOT dead_flag`
reads **0** (three-valued-logic trap; `dead_flag IS NOT TRUE` is correct and is what
`active_population()` uses throughout). Registered as a finding, not fixed outside this
lane's files.

### 3.3 — `--derive` against production

```
$ python3 platform/scripts/governance/catalog_provenance.py --derive
[B-1] 107/182 SCUs have a named producer -> .../provenance/producer_provenance.derived.json
```

```json
{
  "total_scus": 182,
  "scus_with_producers": 107,
  "scus_no_detector": 75,
  "no_detector_reason_counts": {
    "no_contract": 28,
    "relation_unowned_by_registry": 28,
    "no_relation_in_range": 11,
    "source_ref_out_of_range": 7,
    "derived_kind_no_source_query": 1
  }
}
```

**107, not 108** (v1.0's figure). The one SCU that moved is
`scu.catalog.query_graha_naisargika_friendship`, whose only v1.0 producer
(`bg_dignity_reference`) was a false positive from a migration segment (C-3(b)); it now
correctly reports `NO_DETECTOR — relation_unowned_by_registry` (its handler's actual read,
`bg_graha_naisargika_friendship`, is a real but unregistered table). Every other SCU
affected by C-3 still has ≥1 producer, just fewer/correct ones — the named-SCU count only
moves by the one SCU that lost its sole (wrong) producer.

Reason classes, exactly as C-2/C-4 and C-3 leave them:

- **28 `no_contract`** — no availability_contracts entry at all, no reviewed claim.
  Honest: nothing to derive from.
- **28 `relation_unowned_by_registry`** (the "29-class" from v1.0's own recount, now
  net-adjusted by C-3's fixes — see §3.5 for the reconciliation) — a real relation name
  was found, exists in `information_schema.tables`, but no `asset_registry` row claims it
  as `target_table`. **27 distinct tables** (not "~20" — v1.0's figure was a rough
  estimate; C-5(iv) computes it exactly by parsing every `relation_unowned_by_registry`
  message: `asset_registry`, `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_graha_dik`,
  `bg_graha_naisargika_friendship`, `bg_motion_state_thresholds`,
  `bg_prashna_fructification_rules`, `bg_prashna_lagna_methods`, `bg_prashna_significators`,
  `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_shashtiamsha_deities`,
  `bg_transit_av_gates`, `bg_transit_moorti`, `bg_transit_vedha`,
  `bg_vastu_direction_remedials`, `bodha_rm_chart_summary`,
  `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`,
  `bodha_rm_pattern_remedies`, `bodha_rm_remedy_prescriptions`, `bodha_triangulation`,
  `brahma_vichara_constants`, `ga_prashna_lagna`, `kala_paddhati_profile`,
  `mimamsa_attribution`, `mimamsa_discoveries`).
- **11 `no_relation_in_range`** (down from 16 in v1.0) + **7 `source_ref_out_of_range`**
  (new class) — v1.0's single "resolved source range(s) contain no relation name" bucket
  of 16 conflated two different causes; C-2/C-4 split it. The 7 that moved to
  `source_ref_out_of_range` are exactly: `get_aspects` (declared 55-91, file has 86
  lines), `get_avasthas` (71-100, 91 lines), `get_dignity` (78-108, 104 lines),
  `get_eclipse_flags` (38-62, 60 lines), `get_ashtakavarga`, `get_panchanga`,
  `get_structural` (each loses its one handler segment to an out-of-bounds ref while a
  migration segment happens to still resolve). The remaining 11 are real limits of the
  method (six remedy handlers whose range holds no SQL; `query_cdlm_summary`'s
  `FROM ${table}` via a `TIER_TABLE` map; `call_dasha_eligibility`'s annotation gap).
- **1 `derived_kind_no_source_query`** — `scu.catalog.query_current_transit_snapshot`,
  correctly routed by spec.

### 3.4 — `source_ref` resolution recount (C-4, replaces v1.0's 125/11/1)

v1.0 reported "125 fully resolved / 11 partial" under the definition "file exists, range
in-bounds" — but that 125 was actually the SHAPE-VALID count (137 − 12 non-numeric-range
citations), never bounds-checked. `compute_segment_resolution_counts()` now resolves
EVERY declared `|`-joined piece of every `source_query` SCU's `source_ref` and checks
bounds on each:

```
113 full (every declared piece is a real, in-bounds range)
 23 partial (some pieces in-bounds, at least one stale/OOB or non-numeric)
  1 none (scu.catalog.query_classical_texts — both its pieces are #anchor/:name citations)
```

**12 SCUs carry at least one stale (out-of-bounds) or missing numeric piece** — registered
here as an outside-scope finding for whoever owns `source_query_availability.ts`'s
annotations; none of these 12 refs were edited by this lane:

`get_ashtakavarga`, `get_aspects`, `get_avasthas`, `get_database_schema`, `get_dignity`,
`get_eclipse_flags`, `get_medical_indications`, `get_panchanga`, `get_structural`,
`get_vastu_directions`, `query_contradictions`, `query_question_lenses`.

(7 of these — `get_ashtakavarga`, `get_aspects`, `get_avasthas`, `get_dignity`,
`get_eclipse_flags`, `get_panchanga`, `get_structural` — are the ones whose stale segment
actually changes their NO_DETECTOR reason class, per §3.3; the other 5 have a working
segment elsewhere in the same `source_ref` and are unaffected in outcome, only in this
stricter count.)

### 3.5 — The 4 false producers (C-3), and the closure impact

| SCU | wrong producer (v1.0) | cause | now |
|---|---|---|---|
| `scu.catalog.get_ayurdaya` | `ga_dashas` / `chart_dashas` | C-3(a): one-hop follower matched `def replace_prior_chart_dashas(` (a definition header, the LAST line of the `_idempotency.py:54-78` range) as a call, then ingested that function's body | producer removed; `ga_ayurdaya`/`chart_facts` (the handler's real query) unaffected |
| `scu.catalog.get_sensitive_degrees` | `ga_dashas` / `chart_dashas` | same cause, same shared helper file | producer removed; the 7 real `chart_facts` co-producers unaffected |
| `scu.catalog.query_compendium_index` | `bg_texts`/`bg_text_index` / `classical_text_chunks` | C-3(c): the writer's own INPUT read (`bg_compendium_index.py` reading `classical_text_chunks` to build its index) was taken as the SCU's query | producers removed; `bg_compendium_index`/`brahma_compendium_index` (the handler's real query) unaffected |
| `scu.catalog.query_graha_naisargika_friendship` | `bg_dignity_reference` | C-3(b): migration 606's own unrelated integrity-check SQL was taken as the SCU's query | now correctly `NO_DETECTOR — relation_unowned_by_registry` (the handler's real read, `bg_graha_naisargika_friendship`, is unregistered) |

**Closure headline does not move**: `bg_dignity_reference` was never load-bearing for the
111 figure (reached via another path already) — confirmed by re-running `--closure` after
the fix and getting the same 111/127.

An incidental, positive side effect noticed while verifying: `scu.catalog.get_chart_header`
previously reported ALL 7 `ga_*` co-producers of `chart_facts` as `shared: true`, because
`query_pins` extraction was reading pin literals out of excluded migration segments too,
diluting the real pin. With migration/writer segments excluded from literal extraction,
the handler's own `fact_category = 'graha_position'` pin now correctly narrows this SCU to
its single real owner, `ga_positions` (plus the equally-real `ga_dashas`/`chart_dashas`
producer from the SAME handler's own `chart_dashas` query — a genuine read, not a false
positive, verified by reading `chart_header.ts:72-94` directly).

## 4 — B-2: the necessity closure

```
$ python3 platform/scripts/governance/catalog_provenance.py --closure
[B-2] necessary before=63, after=111 (of 127) -> .../provenance/CLOSURE_REPORT.md
```

**Before** (14 reviewed-seed assets — unchanged from v1.0 and from the D5 ruling's own
baseline): **63/127** necessary, 64 not reachable, split 21 brahmagyan / 4 bodha / 6
ganita / 9 kala / **24** phala+mimamsa (9 phala + 15 mimamsa — the ruling's own stated "23"
undercounts by one; the ruling's total of 64 is only internally consistent with 24, not
23; registered, not corrected in `DECISIONS_RECOMMENDATIONS_v2_0.md`).

**After** (all reviewed ∪ derived ∪ route-evidence producer assets): **94 distinct named
assets** (not 95 — one fewer than v1.0's figure, because `bg_dignity_reference` no longer
appears anywhere in the seed set once C-3 removed its one false-positive citation) →
**111/127** necessary, **16** not reachable. This is unchanged from v1.0 — the closure
headline does not move on any of the six corrections.

The 16 still outside, now split by C-6's two distinct reason classes:

| reason class | count | assets |
|---|---|---|
| `table_unregistered` | 2 | `bg_prashna_rules`, `ga_prashna` — both share the `prashna` domain stem with 6 unregistered tables (`bg_prashna_fructification_rules`, `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `ga_prashna_lagna`) that real catalog SCUs (`query_prashna_*`, `get_prashna_lagna`) DO query. These two assets likely DO produce a unit; the registry, not the catalog, has the gap. Under D5 part 3 this is a merge/retire candidate, never a true closure failure. Honest limit: the stem heuristic correlates by shared domain word, not by parsing each writer's actual `INSERT`/`COPY` targets, so it lists all 6 same-domain tables as candidates for BOTH assets rather than asserting a precise 1:1 assignment. |
| `no_unit_names_it` | 14 | `bg_cohort`, `bg_concordance`, `bg_gochara_arcs`, `bg_gochara_citation_resolution`, `bg_vidhi_floors`, `bg_vidhi_primitives`, `bo_grounding`, `ka_kshetra`, `ka_tulana`, `lel_events`, `mi_bhara`, `mi_sankalpa`, `mi_seva`, `mi_vistara` |

**Phala, corrected (C-5(v)):** zero phala assets are outside the closure — but NOT
"chiefly via service_probe-derived chains reaching L4" as v1.0 wrongly stated. Verified
directly from the regenerated artifact: all 9 `ph_*` assets
(`ph_muhurta`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`, `ph_pratikara`,
`ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`) are **direct**
`derived_from_source_query` producers of some catalog SCU. No service_probe chain is
involved, and an L0 service probe could not pull an L4 asset into the seed set that way in
any case (L4 depends on lower layers, not the reverse).

**The yoga SCU's timing route (C-5(v)):** `scu.kala.temporal_activation`'s `source_query`
requirement resolves to `kala_activation` (via `ka_kalasutra`), **not**
`kala_gochara_windows` as v1.0 stated. Verified directly from the regenerated artifact —
the producer entry's `table` field reads `kala_activation`. `scu.yoga.firing_and_cancellation`
(the SCU that carries BOTH the `producer_output` claim for `ga_yoga` and, separately, a
`source_query` route through `bo_laksana`/`ka_kalasutra`) is unaffected by this correction;
only the table name in the narrative was wrong.

## 5 — B-3: `build_dependencies` reader scan

```
$ python3 platform/scripts/governance/catalog_provenance.py --reader-scan
[B-3] build_dependencies reader scan: 76 hits -> .../provenance/BUILD_DEPENDENCIES_READER_SCAN.md
```

**76, stable (C-5(iv))** — not 80, and not the 81 the gate review found on re-running
v1.0's script. v1.0 already excluded `PROVENANCE_DIR` (this lane's own generated JSON/MD
output) after finding a 67→144 self-referential runaway; what it did NOT exclude was
`wave1/` (this lane's own `B_REPORT.md`/`B_REVIEW.md`), which discuss
"build_dependencies" at length while describing the scan itself — a real, if
non-runaway, source of drift (observed 80→81 the moment `B_REPORT.md` gained one line).
`WAVE1_DIR` is now excluded the same way `PROVENANCE_DIR` is, and the figure is now stable
across repeated runs (confirmed twice consecutively).

Same 37 files, same conclusion as v1.0: the only LIVE code that actually queries the
table is `platform/python-sidecar/pipeline/dispatcher.py` (`_load_dep_graph()` /
`rebuild_asset()`), and `pipeline.dispatcher` is imported nowhere else in the repo —
observed fact, not a recommendation to drop anything (B-3 is read-only; the table is
untouched). Everything else is comments on already-repointed TS routes, historical
migrations, governance docs, and one unapplied teardown script.

## 6 — B-4: `--check`

```
$ python3 platform/scripts/governance/catalog_provenance.py --check
[B-4] --check PASS: all 182 SCUs in .../provenance/producer_provenance.derived.json have a valid producer or a no_detector reason from the closed reason set.
```

**Now a real gate (C-1):** `--check` reads the committed JSON artifact directly via
`validate_derived_artifact()` — it never re-derives. A `derived_from_source_query`
producer must carry a non-null `table` AND a range-shaped `source_ref`; a
`reviewed_output`/`derived_from_service_probe`/`route_evidence_only` producer is a
declared exemption from that (each already carries its own evidence citation) but must
still carry a non-empty `source_ref`; a `no_detector` reason must classify into the closed
`NO_DETECTOR_REASON_CLASSES` set via `classify_no_detector_reason()` — anything that
doesn't match a named pattern comes back `"unclassified"`, which is deliberately NOT a
member of that set. The gate review's own constructed cases (an SCU with only an
unreviewed `producer_output` requirement; a stale/hand-edited artifact entry) now both
correctly fail when they should.

```
$ python -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -v
======================== 19 passed in 0.05s ========================
```

Full test list and per-correction mutation evidence: §2 above.

## 7 — Honest limits (every reason class, with counts) — post-corrections

Of 182 SCUs: **107 have a named producer** (12 reviewed SCUs / 14 reviewed assets + **95**
derived-only SCUs / **80** derived-only assets = **94** distinct assets total, not the
v1.0 figures of "14+94=108 SCUs" / "14+81=95 assets" — both corrected downward by exactly
the one false-producer SCU C-3 removed). **75 are `NO_DETECTOR`** (up from 74 — the same
one SCU), broken down exactly as in §3.3.

**The `producer_output` requirement count is 11 SCUs, not 12** (C-5(iv)) — 12 is the
requirement COUNT (`scu.finance.prosperity_assessment` carries two, one per co-producer),
11 is the distinct-SCU count.

**"15 assets" is not an off-by-one (C-5(i)) — both 14 and 15 are correct, for different
sets.** `{c['asset_id'] for scu in scus for c in scu['producer_output_claims']}` (every
claim, any disposition) → **15**, because `ka_kalasutra` enters via
`scu.kala.temporal_activation`'s `route_evidence_only` claim. Filtering to
`disposition == 'reviewed_output'` only → **14**. The D5 ruling counted claims ("naming 15
assets"); v1.0 counted only reviewed claims and then wrongly called the ruling's 15 an
off-by-one. **v1.0's "the 63/127 calibration corroborates 14" claim is retracted**: seeding
the closure with the 15-asset set (adding `ka_kalasutra`) also gives 63, because
`ka_kalasutra` is already upstream of `ka_yojaka`/`ka_bhavishya_lekha` — the baseline
cannot distinguish 14 from 15 seeds, so it corroborates neither over the other.

**A third disposition, `derived_from_service_probe` (C-5(ii)):** 9 rows, `table: null`,
an anchor (`service_probe:...` or the requirement's own `source_ref`) instead of a numeric
range. These are read directly off a `kind: service_probe` requirement's own `asset_id` —
no SQL parsing attempted or needed. `validate_derived_artifact` treats this disposition as
a declared exemption from the table+range requirement, same as `reviewed_output` and
`route_evidence_only`.

**The `route_evidence_only` claim is carried, not dropped (C-5(iii)):**
`scu.kala.temporal_activation` now carries `ka_kalasutra` twice in its `producers[]` — once
via the carried `route_evidence_only` claim (evidence: "query_temporal_activation handler
reads kala_activation") and once via the independently-derived `derived_from_source_query`
route (table `kala_activation`) — both correct at once, neither overwrites the other.

**Calibration set:** unchanged in substance from v1.0 — 5 of 12 reviewed SCUs are directly
comparable (carry a `source_query` contract); 3 agree (2 as an honest superset via a
correctly-flagged shared table), 2 "disagree" (one genuinely unresolvable, one covering a
different producing route than the reviewed claim — both correct, nothing lost in the
merged output).

## 8 — Findings outside scope (registered, not fixed)

1. `dead_flag` is `NULL` on every production row; `is_active AND NOT dead_flag` silently
   reads 0 rows. `dead_flag IS NOT TRUE` is correct. (§3.2)
2. The D5 ruling's per-layer "23 Phala/Mīmāṃsā" sums to 24 by direct count (9 phala + 15
   mimamsa); the ruling's own total of 64 is internally consistent only with 24. (§4)
3. 12 SCUs carry a stale (out-of-bounds) or non-numeric `source_ref` piece — named
   individually in §3.4 — a `source_query_availability.ts` annotation-drift finding, not a
   derivation bug. None of the 12 refs were edited by this lane.
4. **27** real, queried tables have no owning `asset_registry` row at all (§3.3's full
   list) — a genuine registry-coverage gap. Two of them (the `bg_prashna_*` family and
   `ga_prashna_lagna`) are flagged `table_unregistered` in the closure report (§4) because
   they share a domain stem with a still-outside asset; the other 25 have no such
   correlated asset and are registered here as a flat list.
5. `pipeline/dispatcher.py` (the one live reader of `build_dependencies`) is imported
   nowhere else in the repo — may itself be dead code, independent of the
   `build_dependencies` retirement question.
6. The `table_unregistered` correlation (C-6) is a same-domain-stem heuristic, not a
   parse of each writer's actual `INSERT`/`COPY` targets — it lists candidate tables, not
   a precise 1:1 assignment. Stated in §4, not hidden.
7. `producer_provenance.derived.json` records `via_helper` (C-3) but does not separately
   report an aggregate "N producers found via helper vs. directly" count — a future pass
   could add this if the provenance is valuable at that granularity.

None of these were fixed silently; all are visible in this report and the generated
artifacts.

## 9 — Stop conditions

Not triggered, in either the original pass or this corrections pass. No writer,
orchestrator, or sealed-tier change was needed; no production write occurred; no
migration was applied. §0 (the stale `CLAUDECODE_BRIEF.md` pointer) was registered rather
than treated as a stop condition, per the reasoning given there.

## 10 — Not in this lane (confirmed untouched)

`compiler.ts` was not read or modified. `editorial.ts` was read only, never edited. Lane
A's files (`asset_census.py`, `asset_elevation_tracker.py`, `00_ARCHITECTURE/control/
*.jsonl`, `nikasha_test/harness/**`, `wave1/A_REPORT.md`, `wave1/a2_t3_proof/**`) were
neither staged nor reverted at any point in this corrections pass.

## 11 — Governance checks (constraint §2.7)

```
$ python3 platform/scripts/governance/manifest_fingerprint.py --check
entries: 141 (declared 141)
fingerprint declared: f484f581767ad641
fingerprint observed: f484f581767ad641
MATCH
```
No rotation needed — `catalog_provenance.py` and its test file are not registered in
`CAPABILITY_MANIFEST.json`.

```
$ source .../pgenv.sh
$ python3 platform/scripts/governance/drift_detector.py --session-id nikasha-wave1-laneB-corrections
drift_detector: 1 findings; exit=3
```
Exit **3** (sanctioned: "exit 0 or 3 only"). The one finding is the same pre-existing,
unrelated one v1.0 reported: `a3_category_not_yet_populated`, LOW severity — 73
`CHART_FACTS_SCHEMA.json` categories not yet written to `chart_facts` by any writer (a
soft check; writers are expected to be added incrementally). Nothing this lane touched
(`asset_registry`, `chart_facts`, any writer) caused or could cause this finding.

## 12 — What is NOT done

Nothing from the six corrections is left undone. All of C-1 through C-6 are committed
(commit hashes in §2), each with its own passing test and recorded mutation evidence, and
the full pipeline (`--derive --closure --reader-scan --check`, then the test suite) has
been re-run against production after the LAST correction, not just after each individual
one. `compiler.ts` wiring remains explicitly out of this lane's scope, per the wave1
prompt's own "Not in this lane" line — unchanged from v1.0, not a gap this corrections
pass was asked to close.
