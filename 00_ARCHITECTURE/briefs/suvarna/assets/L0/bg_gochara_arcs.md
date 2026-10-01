---
asset_id: bg_gochara_arcs
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
ledger_gap_ids: [bg_gochara_arcs-Idem.pattern, bg_gochara_arcs-Earn.build_record, bg_gochara_arcs-Cost.baseline, bg_gochara_arcs-Carr.detector, bg_gochara_arcs-Build.history]
---
# bg_gochara_arcs — Gochara monotone-arc substrate (R9 input; 33,933 arcs)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Registry description: 'Chart-independent decomposition of every graha's ecliptic-longitude history over the stored 1900–2150 ephemeris epoch into MONOTONE ARCS: maximal intervals on which longitude is strictly monotone in time and confined to a single 360° band, cut at real stations'. Heavy-shape writer (`plan_substeps` one per body, 9, + `run_substep`; both entry points declared, `platform/python-sidecar/pipeline/orchestrator/writers/bg_gochara_arcs.py:1-40`), delete-then-insert at `:149,156`; 33,933 rows (seed literal 34,553; migrations 599 and 854 modify its registry row). Depends on `bg_ephemeris`. **Charter R9** names it (with `bg_gochara_citation_resolution`) as a Gochara L0 input: a change that alters what Pravāha consumes is analysed and fixed, but the rebuild waits for a Strategic Suvarṇa decision after notification to Pravāha (`SUVARNA_AUTONOMY_CHARTER_v1_0.md` §4 R9). Registry shows 0 declared dependents, but code reads it: `ka_gochara.py`, `services/w2g/{db_source,arcs,equivalence_report,materialize}.py`, `services/ka_gochara/service.py`. The table carries `arc_fingerprint`, `substrate_version`, `engine_version`, `build_id` and `computed_at` (all populated).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1055` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_gochara_arcs.py:15`, `platform/python-sidecar/pipeline/orchestrator/writers/bg_gochara_arcs.py:89`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_gochara_arcs`; count_sql tables: `bg_gochara_arcs` | census CEN-R |
| live rows / floor | 33933 / 33,933 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ephemeris` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_gochara_arcs`: 8 non-test py/ts/tsx files reference it (7 outside brahmagyan/ and bg_*.py writers): `ka_gochara.py`, `db_source.py`, `arcs.py`, `materialize.py`, `equivalence_report.py` +2 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 25b9bb90 complete/skip_no_delta (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-04): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 25b9bb90 complete/skip_no_delta (2026-09-06) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: bg_gochara_arcs (bg_gochara_arcs.py:149), bg_gochara…); Vocab.identity (declared key (substrate_version, body, arc_index): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (4 executed run(s) of 5 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.registered (@register in bg_gochara_arcs.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_gochara_arcs-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_gochara_arcs-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_gochara_arcs-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_gochara_arcs-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_gochara_arcs-Build.history | Build | history | CF-10: a record of past errors/aborts; the latest run completed \| ledger: measured: latest run complete, but 1 error(s) and 1 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — no non-detector census gap except the history record; the asset is already the cleanest example of deterministic L0 derivation. R9: analysis only here; any rebuild is SS's after notifying Pravāha.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D3 recomputation of the arcs from `ephemeris_daily`

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** the arcs are a pure function of the stored daily longitudes (maximal strictly-monotone runs cut at stations): recompute the decomposition from the ephemeris rows and compare `(body, arc_index, start_jd, end_jd, direction, wrap_index)` to the stored arcs; also compare the stored `arc_fingerprint` to a fresh one. A seeded one-arc mutation must be caught. Deterministic, no oracle.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declared-versus-actual consumers (R9 evidence)

- **Answers:** layer instance §1.1.4 finding 1; no census cell
- **Change:** the registry declares 0 dependents while code reads the table; record the actual readers in the impact statement R9 requires, and (for Pravāha/SS, not designed here) the edge from the Gochara family assets to `bg_gochara_arcs`. Edges on family assets are Pravāha’s; this brief does not propose them.
- **Files / declaration / migration:** the B.L0 impact statement (document), not a registry change
- **Failing-first test and mutation:** n/a (document)
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (dag reads-match, when the reads scan covers the family)
- **Fix class:** registry/declaration only (document); **buildable before J1:** tier-independent
- **Question for SS:** Notification: has Pravāha been told that any change to this asset’s inputs (bg_ephemeris, bg_texts) reaches it? (R9 is SS’s to route.)

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_gochara_arcs.py` for any composed text column; declare `[]` expected (numeric arcs)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `engine_version` / `substrate_version` (provenance columns; the table has no citation column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no citation column
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 error (integrity check, 2026-09-04) and 1 abort; latest run complete (`skip_no_delta` 2026-09-06)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(substrate_version, body, arc_index)` (census, 0 duplicates); the table carries `arc_fingerprint` per arc. Volatile columns excluded: `build_id`, `computed_at`, `engine_version` if it records only a software label. Delete-then-insert: a rebuild must reproduce identical `(start_jd, end_jd, direction, wrap_index)`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the monotone-arc definition and the cut-at-real-stations rule; the 9-body substep structure; `arc_fingerprint`.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation from the ephemeris).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. R9: confirm the notify-Pravāha path before any wave touches `bg_ephemeris` (its input) — SS routes it.
