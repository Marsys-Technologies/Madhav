---
asset_id: bg_kota_chakra_rings
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
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-06, TI-L0-25]
ledger_gap_ids: [bg_kota_chakra_rings-Idem.pattern, bg_kota_chakra_rings-Earn.build_record, bg_kota_chakra_rings-Cost.baseline, bg_kota_chakra_rings-Complete.depth, bg_kota_chakra_rings-Carr.detector]
---
# bg_kota_chakra_rings — Kota-Chakra ring partition table (27 rows, versioned)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

ADJUDICATION-9: the Kota-Chakra fort-chakra ring partition (stambha, durgantara, prākāra, bāhya; 1-indexed distance from the janma nakshatra), moved from an inline writer-code dict to a versioned L0 global reference table; a tier-(iii) secondary-source transcription (seed description). ON CONFLICT upsert (`platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:154`); 27 rows; columns include `citation`, `corpus_status`, `ratified_by`, `table_version`; `dvara_assignment` is never populated. Declared dependent `ka_kota_chakra` (census 1 / 1); no L0 registry module serves it.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:909` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_kota_chakra_rings.py:28`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_kota_chakra_rings`; count_sql tables: `bg_kota_chakra_rings` | census CEN-R |
| live rows / floor | 27 / 27 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 1 (every layer); named: `ka_kota_chakra` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_kota_chakra_rings`: 7 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `ka_kota_chakra.py`, `w25_kota_chakra.py`, `logic.py`, `writer.py`, `producer_editorial_review.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Complete (information, D3) | Complete.depth | PARTIAL | 27 rows, 9 cols; fully populated 8; NEVER populated ['dvara_assignment'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_kota_chakra_rings (brahmagyan/l0_kota_chakra_…); Vocab.identity (declared key (table_version, ring_position): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_kota_chakra_rings.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_kota_chakra_rings-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_kota_chakra_rings-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_kota_chakra_rings-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_kota_chakra_rings-Complete.depth | Complete | information | `dvara_assignment` never populated (27 rows, 9 cols); a depth opportunity, not a blocker (D3) \| ledger: measured: 27 rows, 9 cols; fully populated 8; NEVER populated ['dvara_assignment'] / required: the Complete gate's claim |
| bg_kota_chakra_rings-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — a clean reference table; census has no FAIL. `corpus_status` records whether the corpus holds the passage, which is the honest limit on carriage.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1 on the corpus-held rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for rows whose `corpus_status` says the passage is in the corpus, resolve `citation` and test the ring assignment’s anchor terms; rows marked secondary-source/not-in-corpus are reported as unverifiable, not passed.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 1 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_kota_chakra_rings.py` for any composed text column; declare `[]` expected (literal rows)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 1 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `citation` (column present, dark in the saved reach record) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 1 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 on corpus-held rows
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* `citation`
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(table_version, ring_position)` (census, 0 duplicates). Upsert; fingerprint over `(ring_position, ring_index, ring_name, citation, corpus_status, ratified_by)`; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the ring partition and its versioning; the secondary-source disclosure in `corpus_status`.
- **Carriage check chosen (T4 §4.1; one only):** D1 (only where the passage is in the corpus).
- **Opportunities (never blocking):** `dvara_assignment` (a declared-null reason or a sourced value).

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
2. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

**Track I items arising (see INDEX section 8):** TI-L0-06, TI-L0-25.
