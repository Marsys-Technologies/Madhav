---
asset_id: lel_events
layer: L5 Mīmāṃsā (lel_events, no-writer user-data asset)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna (lane track-a-l5)
produced_on: 2026-10-03
plan_item: A.L5 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION). Offline rollup under main REGISTRY_REVISION 16. Live registry, row counts, receipts and fact queries re-read 2026-10-03 (read-only)."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main adb0db29d"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); cross-layer reads and write-path guards to Strategic Suvarṇa (R5)"
risk_class: "medium (people data; writer-code guards only, no data change)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-01, TI-L5-02, TI-L5-03, TI-L5-04]
ledger_gap_ids: ["lel_events-Build.completion", "lel_events-Earn.build_record", "lel_events-Cost.baseline", "lel_events-Carr.detector", "new: lel-N1", "new: lel-N2", "new: lel-N3", "new: lel-N4", "new: lel-N5", "new: lel-N6", "new: lel-N7", "new: lel-N8"]
---

# lel_events — Life Event Log: the native-entered `life_events` table (registered no-writer user-data asset)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `none (registered no-writer asset; decision N-14.R236)`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

Registry: kind `data`, per-chart, `has_writer = f`, no target table; `count_sql` is `SELECT count(*) FROM life_events WHERE chart_id = $1`. The declarations file (1.12.0) types it `user_data` (N-22 principle 6, people-entered, N-46). The table `life_events` holds observation testimony the native entered or confirmed: **63 rows for the canonical chart** (`le_basic`), 57 from the LEL v1.7 seed (stamped `recorded_at = 2000-01-01`, the pre-instrument sentinel) and 6 entered between 2026-07-01 and 2026-08-08 (`le_recorded_hist`: 57 / 5 / 1 by month). Shape 57 `point` / 6 `interval`; `date_confidence` 57 exact / 3 month_known / 3 year_only; `pool_consent` false on 63/63; `outcome_observed` true on 62 and NULL on 1; 8 rows carry `date_tightened_at` (native questionnaire of 2026-07-19). **No other chart has any row** (`le_by_chart`: one chart, 63). It is the outcome ground truth of the L5 loop (T2 section 9.1: observation testimony with channel adapters; `mi_jivanaghatana` is its qualified evidence projection). Per decision N-14.R236 (Strategic Suvarṇa, 2026-09-29, quoted in the layer instance 1.1.a) the asset is classified no-writer with Build/Idem N/A by registry rule; this brief records the justification from its intended source and consumer contract and does not extend the classification to any other asset. L5 is in STRUCTURAL mode by design; the LEL is the data that moves it out of that mode, so nothing in this brief proposes changing or deleting an entered row.

**Canonical chart state (read-only, 2026-10-03).** Registry: catalog `CURRENT` live (seed says `DRAFT`, CF-L5-13); no throughput row for the canonical chart; saved Build.completion FAIL ('live=63 and no build record at all'), which N-14.R236 says should read N/A by registry rule — reported, not resolved (layer instance F-02).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2846` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | none: `has_writer = f` (live registry); no `@register('lel_events')` anywhere in `platform/python-sidecar`; intake is by API and tools: `platform/src/lib/mcp/lel_event_writer.ts:136` (`recordLelEvent`), `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py:1236` (seed), `platform/src/app/api/clients/[id]/learning/route.ts` (`lel_entry` action) | writers dir / census `Build.registered` |
| target table(s) (live registry) | `none declared`; count_sql tables: `life_events` | registry / census |
| count_sql (live) | `SELECT count(*) FROM life_events WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 63 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 600s | registry |
| registry build state (canonical chart) | no throughput row for the canonical chart; recent canonical runs: none | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | none | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none in the registry (no active asset lists `lel_events` in `depends_on`; census blocking radius 0/0) — yet read by five code paths in L5 and L4 (next row) | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Undeclared reads (F-01 of the layer instance, same finding as migration 691): `mi_jivanaghatana.py:215`, `services/mi_bhara/db.py:143`, `services/mi_sankalpa/db.py:64`, L4 `ph_pramana.py:190` and L4 `ph_rectification/__init__.py:146` all `SELECT ... FROM life_events`; none declares `lel_events` (live `mi_jivanaghatana.depends_on` is `bg_ghatana` only). One of them is **unscoped**: `ph_pramana.py:190` selects every row of `life_events` with no `chart_id` filter, and its docstring (:164-165) says the table 'carries no chart_id column' (false since migration 423; `chart_id` is NOT NULL with a foreign key to `charts`). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Writers: `mi_jivanaghatana.py:215`, `services/mi_bhara/db.py:143`, `services/mi_sankalpa/db.py:64`, `services/mimamsa/lel_calibration.py:280` (count), L4 `ph_pramana.py:190` and `services/ph_pramana/engine.py:152-231` (`life_event_match` / `life_event_miss`), L4 `ph_rectification/__init__.py:146`, `bodha_writers/formulas.py:739` (comment: pre-embargo LEL rows). Served: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts:204` (tool `mimamsa_lel_query` -> primitive `lel_query`, `platform-mcp/src/tools/register_p1_aliases.ts:2076`), `query_mechanism_retrodiction.ts:245` (tool `mechanism_retrodiction_get`, sealed split `event_date < 2020-01-01` baked into the SQL, :59), `prediction_lifecycle_sweep.ts`, `lel_intake_checklist.ts`, `platform-mcp/src/tools/kala_views/ahead.ts` and `story.ts`, `platform/src/lib/lel/prospective_ledger.ts`, `platform/src/lib/pariprashna/receipt/assemble.ts`. Write paths: `lel_event_writer.ts:171` (INSERT ... ON CONFLICT (chart_id, event_id) DO UPDATE), `brahmagyan/mimamsa/lel_intake.py:1336/1381/1421` (seed, same upsert), `brahmagyan/mimamsa/l5_lel_intake.py:299` (UPDATE of `is_training/is_holdout/anchor_match`: columns absent from the live table, so it cannot have run here), one-off `platform/scripts/d4a/fix_item3_spiritual_arc_correction.mts:113,177`. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_lel_calibration.py`, `tests/test_mimamsa_lel_intake.py`, `tests/test_lel_query_context_stale_filter.py`, `tests/test_lel_event_class_resolver.py`, `platform-mcp/src/__tests__/mimamsa_lel_intake.test.ts`, `L5_mimamsa/__tests__/query_life_events.test.ts`, `lel_intake_checklist.test.ts` | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | none: no writer, so no receipt, no freshness row, no output-digest spec (specs exist for 12 other L5 assets, `asset_output_digest_specs`). Nothing to digest; the table is the source. | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-NO-ROUTE (0 unfrozen ancestors, no W2 analysis/verdict) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.registered | N/A | no writer, and the registry agrees (service or static) |
| Build | Build.contract | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Idem | Idem.pattern † | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Build | Build.target † | N/A | no target_table; asset_kind='data', has_writer=False |
| Build | Build.dag † | PASS | 0 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | live=63 and no build record at all (chart 482012f1) |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=63) |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.exercised | N/A | never run, and it has no writer — consistent |
| Build | Build.history | N/A | never run; check 7 owns this |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** none.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem NO_DETECTOR · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> PARTIAL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| lel_events-Build.completion | Build.completion | stale | measured: live=63 and no build record at all (chart 482012f1) / required: the Build gate's claim |
| lel_events-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 / required: the Earn gate's claim |
| lel_events-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 / required: the Cost gate's claim |
| lel_events-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: lel-N1 | Build.dag | real | five code readers of `life_events` have no declared edge to `lel_events`; a change to the LEL cannot order `mi_jivanaghatana` (and so all of L5) after it (CF-L5-07; layer instance F-01; migration 691) |
| new: lel-N2 | Build.completion | detector | the no-writer N/A is a decision (N-14.R236), not yet a declared `NA_RULE_DECISIONS` rule: the inspector reads FAIL; needs the E6 applicability rule for a `user_data` asset (an Earn rule for `no-registered-writer` exists; Build.completion has none) — SS approval for the rule (CF-L5-12) |
| new: lel-N3 | leakage / scope | real + SS question | L4 `ph_pramana.py:190` loads every `life_events` row with no chart filter and turns each into a `LelEntry` that decides `life_event_match` / `life_event_miss` evidence on L4 anchors (`services/ph_pramana/engine.py:152-231`). Today only one chart has rows (`le_by_chart`), so no contamination is observable, but (a) the read is latent cross-chart and (b) the calibration corpus enters prospective L4 generation, against T1 section 8.1 and T2 section 6.6 (Q-L5-18). Owner: the A.L4 brief; recorded here because it is a consumer of this asset |
| new: lel-N4 | write path (N-46) | real | `brahmagyan/mimamsa/lel_intake.py:1342/1386/1421` and `lel_event_writer.ts:178` are `ON CONFLICT (chart_id, event_id) DO UPDATE SET event_date, description, domain, ...`: re-running the seed, or repeating an API call with the same id, overwrites a row the native has since tightened (8 rows carry `date_tightened_at`; no code checks it). `recorded_at` is protected (never in the SET list), the rest is not |
| new: lel-N5 | identity | real | API-entered ids are `uuid5(chart : event_class : event_date : description)` (`lel_event_writer.ts:124-127`): correcting the date or description through the same call creates a different id and orphans everything that referenced the old one. Observed consequence of some such change: 4 `mimamsa_calibration` rows reference event `5278d97c-e769-529a-b0c2-be1e965c2d6b`, which exists in neither `life_events` nor `mimamsa_event_provenance` (`cal_orphan_event`); the cause was not established here |
| new: lel-N6 | data | information | `recorded_at` is 2000-01-01 on 57/63 rows (a named sentinel, `lel_calibration.py:125`): it means "recorded before any prediction" and says nothing about when the native learned of an event relative to a forecast (T1 section 7.3). The inventory counts 57 seed events; the table holds 63 (layer instance F-11) |
| new: lel-N7 | vocab | real | three event vocabularies on one table (`category` 13 values, compound `domain` slug on 62/63, `event_type`) and no `event_class` column (`prediction_lifecycle_sweep.ts` header says so): `mimamsa_event_provenance.event_class_id` is NULL on 63/63 for this reason (CF-L5-06) |
| new: lel-N8 | Null / Narr | detector | declarations 1.12.0 carries `prose_fields: None`: the free-text `description` is native-typed testimony, not generated prose, so Narr is N/A by cause `no-prose`; propose `prose_fields: []` with that note and Carr N/A by cause (CF-L5-14) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `outcome_observed` | the event's outcome is known | native-entered boolean (62 true, 1 NULL) | earned by source; the NULL is an honest null and is kept |
| `recorded_at = 2000-01-01` | "recorded before any prediction" | seed stamp `PRE_INSTRUMENT_SENTINEL` (`lel_calibration.py:125`) | a named sentinel standing for a fact the system cannot know (disclosure time); acceptable only while downstream treats it as such (it always partitions to training, `lel_calibration.py:148-152`) |
| `pool_consent` | consent to the cross-chart pool | DB default false | honest: false on 63/63; consume side gated by `MIMAMSA_CROSS_CHART_POOL` (`lel_calibration.py:173`) |
| `date_confidence` / `date_tightened_*` | precision of the date and who tightened it | native questionnaire, stored by D-4a lanes | earned by source text; tolerances live in `prospective_ledger.ts` `toleranceDaysFor` (exact +-45d, month_known +-75d per the sweep header) |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- `outcome_observed` NULL on 1 row and `significance` empty on 63/63 are left as entered: correct; no consumer defaults them (checked in `mi_pramana`, which reads `event_magnitude` from provenance, not from here).
- `event_class` does not exist as a column; every consumer that needs a class derives one or declares NULL (`mi_jivanaghatana._lookup_event_class`, :124-169, a documented no-op).

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** Not applicable to this asset (no writer). Its readers pass `chart_id` as a bound SQL parameter; the one UUID-in-JSON failure on record for L5 is the orchestrator's provenance step, recorded under `mi_jivanaghatana`.
- **Outcome-leakage guard:** `life_events` is the calibration corpus: the rule 'must not feed prediction generation' is stated in `lel_intake.py` (docstring) and `mimamsa_outcome.ts` (header). It is enforced inside L5 only by `recorded_at_partition` (`lel_calibration.py:135-157`), which `mi_jivanaghatana` computes in memory and never persists (see that brief), and it is contradicted by L4 `ph_pramana.py:190` (lel-N3). The key-name `calibration_leak_guard.ts` guards served Paripraśna envelopes (a different surface) and does not inspect `life_events` reads; its C4 mutation proof (6/6 contaminated-event mutations) is recorded in `00_ARCHITECTURE/briefs/purnata/PURNATA_CLOSE_REPORT_v1_0.md` section 9.7 (A6) and was not re-run here.
- **People-entered data (N-46) / LEL data contract:** **This is the primary people-entered table** (INV: non-regenerable; not on the backup list). This lane changes nothing in it. The proposed fixes change writers only: a guard so that no write path overwrites a row the native has tightened or corrected, and an id rule that does not change when a correction is made. **No entered row is proposed for change or deletion.** `lel_intake seed` re-applies the markdown source over existing rows: it must not be re-run against a production chart until FD-3 lands.

## 3 · Disposition

**keep (P)** — the table is the outcome ground truth and is native-entered; nothing in it is proposed for change. The defects are in its readers (undeclared edges, one unscoped L4 read) and in two write paths (overwrite risk, content-derived ids), all code or declaration fixes. Enrichment (E) is limited to declarations and an optional additive learned-at column.

Approver under Track A brief section 10: **Steward (G16); cross-layer reads and write-path guards to Strategic Suvarṇa (R5)**. Risk class: **medium (people data; writer-code guards only, no data change)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the readers' edges; declare the asset's kind

- **Answers:** lel-N1, lel-N2; CF-L5-07
- **Change:** registry migration adding `lel_events` to `depends_on` of `mi_jivanaghatana`, `mi_bhara`, `mi_sankalpa` (this layer); report the `ph_pramana` / `ph_rectification` reads to the A.L4 lane; declare `kind: user_data` with Build/Idem N/A by cause, for SS approval as a rule
- **Files / declaration / migration:** registry migration (CF-L5-07 batch); `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** failing-first: `dag_edge_guard` reads-match reports the three reads as undeclared before, covered after; mutation: remove the edge -> FAIL
- **Output change:** none
- **Blast radius:** DAG order of L5 changes (one more root); the Nirmāṇa manifests of the three readers go stale (not frozen; campaign OFF)
- **Rebuild:** none
- **Gate it moves:** Build.dag, Build.completion
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent in content; a DAG change: own review
- **Track I item:** TI-L5-01

### FD-2 · Scope the L4 read of the LEL (owner A.L4) and decide whether the LEL may feed L4 at all

- **Answers:** lel-N3; Q-L5-18
- **Change:** add `WHERE chart_id = %s` to `ph_pramana._load_lel` and correct the docstring; separately SS decides whether `life_event_match` may use LEL outcomes in prospective L4 posteriors
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:160-200` (A.L4 asset: coordinate, do not edit from here)
- **Failing-first test and mutation:** failing-first: two-chart fixture, chart A's build must not see chart B's events; mutation: remove the filter -> FAIL
- **Output change:** none today (one chart has events); becomes real as soon as a second chart has events
- **Blast radius:** ph_pramana digest only
- **Rebuild:** none now
- **Gate it moves:** Build.dag / leakage
- **Fix class:** writer code (L4); **buildable before J1:** tier-independent
- **Track I item:** TI-L5-02

### FD-3 · Write-path guards for entered rows (N-46)

- **Answers:** lel-N4, lel-N5; Q-L5-15
- **Change:** make `lel_event_writer.ts` and `lel_intake.py` leave a row alone (return 'exists') when the existing row has `date_tightened_at` set or differs by a native correction; derive a corrected row's id from the original id, not from the mutable fields; no seed re-run against a populated chart without an explicit flag
- **Files / declaration / migration:** `platform/src/lib/mcp/lel_event_writer.ts:124-190`; `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py:1336-1440`
- **Failing-first test and mutation:** failing-first: a row with `date_tightened_at` is byte-identical after a re-seed and after a same-id call; mutation: drop the guard -> the row changes
- **Output change:** none for existing data
- **Blast radius:** LEL intake only; no consumer reads the write path
- **Rebuild:** none
- **Gate it moves:** N-46 / honesty
- **Fix class:** writer code (TS + Python); **buildable before J1:** tier-independent
- **Track I item:** TI-L5-03

### FD-4 · Declarations: user data, not generated prose

- **Answers:** lel-N8; CF-L5-14
- **Change:** `prose_fields: []` with a note that `description` is native-typed; Carr N/A by cause `user_data` (SS approval for the rule); keep `read_evidence`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; Narr cells move NO_DETECTOR -> N/A by cause
- **Output change:** none
- **Blast radius:** registry rows only
- **Rebuild:** none
- **Gate it moves:** Null, Narr, Carr
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent; the N/A rule is SS-approved only
- **Track I item:** TI-L5-04

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-06** — three event vocabularies, no `event_class` column
- **CF-L5-07** — FD-1: five undeclared readers
- **CF-L5-08** — FD-3: write-path overwrite and id derivation
- **CF-L5-12** — Build.completion for a no-writer asset; Earn/Cost instrument absent
- **CF-L5-13** — seed `DRAFT` vs live `CURRENT`
- **CF-L5-14** — prose_fields / Carr declarations

## 5 · Semantic fingerprint contract (for E5.5)

No writer, never rebuilt. For E5.5 hash the stable columns (`chart_id, event_id, event_date, category, description, domain, shape, date_confidence, interval_start, interval_end, chain_parent_event_id, milestone_label, outcome_observed`) and exclude `id`, `recorded_at` (insertion clock), `date_tightened_at`, `build_id`, `provenance`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** Every entered row, its `event_id`, `recorded_at` and the native's wording; the sealed-split convention (`event_date < 2020-01-01`) used by `mechanism_retrodiction_get`.
- **Carriage check chosen (T4 §4.1; one only):** Carr N/A by cause `user_data`: people-entered, no derivation to transmit (N-22 principle 6). Proposed as a rule for SS approval; D3 not applicable.
- **Opportunities (never blocking):** an additive, nullable `learned_at` / `disclosed_at` column would let the T1 section 7.3 independence test be computed instead of assumed; an explicit `event_class` column would remove the declared null in `mi_jivanaghatana`. Both are native-optional additions; neither is proposed now.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-07** — One holdout rule: the hash split `md5(event_id) mod 10 >= 8` (13 events, not chronological), the sealed date split `event_date < 2020-01-01` used by `mechanism_retrodiction_get`, and the `recorded_at` partition exist side by side. Which is THE pre-registered holdout? *Recommendation:* The sealed date split; the hash split is retired or renamed `sample_split`. (R)
- **Q-L5-15** — LEL write-path guards (N-46): `lel_intake seed` and `lel_event_writer` use ON CONFLICT DO UPDATE over event_date / description; ids are content-derived. Accept code-only guards (never overwrite a tightened/corrected row; correction ids derived from the original id; no seed re-run on a populated chart without a flag), with no data change? *Recommendation:* Yes. No entered row is changed or deleted by this lane or by the proposed fixes.
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-18** — L4 `ph_pramana.py:190` loads every `life_events` row, unscoped, to emit `life_event_match` / `life_event_miss` evidence on anchors. Is the LEL (outcome ground truth) allowed to feed prospective L4 posteriors at all (T1 section 8.1, T2 section 6.6)? If yes, scope it to the chart; if no, remove the read. *Recommendation:* Owner is the A.L4 brief; recommend scoping now and a doctrine ruling on whether outcome evidence may enter L4. (R)
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
