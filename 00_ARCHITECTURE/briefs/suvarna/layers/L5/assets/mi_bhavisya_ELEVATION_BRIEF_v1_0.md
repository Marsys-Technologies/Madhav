---
asset_id: mi_bhavisya
layer: L5 Mīmāṃsā (mi_*)
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Strategic Suvarṇa (R5: the freeze semantics change what a prediction is)"
risk_class: "high (semantics + output change; people-outcome rows protected)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-12, TI-L5-13, TI-L5-14, TI-L5-15, TI-L5-16]
ledger_gap_ids: ["mi_bhavisya-Build.completion", "mi_bhavisya-Earn.build_record", "mi_bhavisya-Cost.baseline", "mi_bhavisya-Complete.depth", "mi_bhavisya-Build.history", "mi_bhavisya-Build.dep_liveness", "mi_bhavisya-Carr.detector", "new: bhav-N1", "new: bhav-N2", "new: bhav-N3", "new: bhav-N4", "new: bhav-N5", "new: bhav-N6", "new: bhav-N7", "new: bhav-N8", "new: bhav-N10", "new: bhav-N9"]
---

# mi_bhavisya — Prediction bundle: L4 anchors frozen into `mimamsa_predictions` plus manifestation sets

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :56). Reads the chart's `phala_anchors` (:77) and `bodha_msr_signals` (:98), and for each anchor with a window writes one `mimamsa_predictions` row (`pred_{anchor_id}`; claim text composed from `karmic_note` / direction / domain / event_type, :144-153; `observation_window`, `confidence_band` from the anchor's `confidence_low/high`, `magnitude_expected`, `falsifier_jsonb`, `driving_signals` = the top 5 MSR signals of the same domain, `emitted_at = datetime.utcnow()` :123, `frozen_bundle_hash` = SHA-256 of `chart|prediction_id|emitted_at|version` truncated to 32 hex, :30-33) and one default `mimamsa_manifestation_sets` row (`ch_{domain}_verbal`, :202). The docstring calls the bundle 'frozen / immutable'. In the code it is rebuildable: each run deletes the chart's manifestation sets and its `pending` / `due` predictions (:228-231) and re-inserts everything with a fresh `emitted_at`. T2c (quoted in the layer instance 3.2) states the same: 'not frozen issued-claim authority'.

**Canonical chart state (read-only, 2026-10-03).** **139 predictions, all `pending`, all `emitted_at = 2026-08-13T01:16:29Z`, 139 distinct hashes, 139 manifestation sets over 7 `ch_<domain>_verbal` channels** (`pred_summary`, `mset_channels`). Domains: transition 50, career 29, wealth 26, relationship 18, spirituality 6, character 5, health 5. Observation windows run from 1990-03-20 to 2052-05-18: 12 ended before the emission date, 8 straddle it, 119 lie wholly after (`pred_window`) — so 20 of the 139 'predictions' were emitted over windows that had already begun. **Only 4 of 139 `source_pramana_id` values resolve to a live `phala_anchors` row**: the chart's anchors are 4 (computed 2026-08-13T01:15:55Z) while `ph_nimitta` throughput still says 139 written; `phala_anchors.convergence_id` references `kala_convergence` ON DELETE CASCADE, and the L3 index records a cascade that emptied Kāla tables when `bo_laksana` replaced the MSR set on 2026-09-08 (L3 INDEX CF-24) — that mechanism is the probable cause but was not traced here. **0 of 695 `driving_signals` references (25 distinct signal ids) resolve** to the current `bodha_msr_signals` (50,678 rows computed 2026-09-11) (`pred_live_anchor`, `facts: driving`).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2904` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py:46` `@register("mi_bhavisya")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_predictions`; count_sql tables: `mimamsa_predictions`, `mimamsa_manifestation_sets` | registry / census |
| count_sql (live) | `SELECT (SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_manifestation_sets WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 278 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 278, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `ph_pramana`, `ph_nimitta`, `ph_phaladesa`, `mi_kula`, `mi_jivanaghatana`, `bo_laksana` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_abhilekha`, `mi_pramana`, `mi_sambandha` (registry); census transitive blocking radius 8 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `ph_pramana`, `ph_nimitta`, `ph_phaladesa`, `mi_kula`, `mi_jivanaghatana`, `bo_laksana`. Actual reads: `phala_anchors` (L4 `ph_nimitta`), `bodha_msr_signals` (L2 `bo_laksana`) and one import: `from ...mi_adhilepa import _signal_family_key` (:23) — a code dependency on a **downstream** L5 asset's helper (data flows the other way). `ph_pramana` and `ph_phaladesa` are declared and not read; `mi_kula` and `mi_jivanaghatana` are declared and not read by this writer (it takes family ids through the imported helper, not from `mimamsa_signal_families`, and no LEL). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | L5 writers `mi_pramana.py:330`, `mi_gunanaka.py:108-119` and `mi_pariksha.py:455` (driving_signals), `mi_sambandha.py:114-121` (manifestation sets); `mi_abhilekha.py:70` UPDATEs its `lifecycle_status`; the sweep `prediction_lifecycle_sweep.ts:348` writes `expired` (dry_run default true). Served: `query_predictions.ts:138` (`marsys://tool/L5/query_predictions`), `query_manifestation_sets.ts`, `query_calibration.ts` (joins `domain`). The six named tools do not expose it directly; `standing_predictions_read` reads a different store (`brahma_prospective_ledger`, 18 open rows). | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_bhavisya_irreplaceable_outcome_guard.py` (3 tests: the DELETE scope, source-text), `L5_mimamsa/__tests__/query_predictions_context_stale.test.ts`, `register_p1_standing_predictions_context_stale.test.ts`; no test of `emitted_at` stability across a rebuild, of the unique-key collision below, or of the default-fallback paths | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T12:56Z); throughput `error` (2026-08-21, BLOCKED on `ph_phaladesa`, `ph_pramana`), last writer execution complete 2026-08-13T01:16Z; `built_against_writer_hash` 'unknown' | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (57) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_manifestation_sets (mi_bhavisya.py:228), mimamsa_predictions (mi_bhavisya.py:230) |
| Build | Build.target † | PASS | target_table=mimamsa_predictions |
| Build | Build.dag † | PASS | 6 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=278, live=278, chart 482012f1) — see Build.history; target_table mimamsa_predictions alone: 195 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=278) |
| Complete (information) | Complete.depth | PARTIAL | 195 rows, 21 cols; fully populated 16; NEVER populated ['base_rate', 'contact_id', 'chart_context_stale_at', 'chart_context_stale_reason', 'chart_context_superseded_by_run_id'] |
| Dens | Dens.served † | PASS | 4 module(s): prediction_lifecycle_sweep.ts, query_calibration.ts, query_manifestation_sets.ts, query_predictions.ts; declaring density_contract: 4 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 27 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) ph_phaladesa, ph_pramana did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 3/6 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_pramana (stale, chart 482012f1)', 'ph_nimitta (stale, chart 482012f1)', 'ph_phaladesa (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved PASS -> PARTIAL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_bhavisya-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=278, live=278, chart 482012f1) — see Build.history; target_table mimams... |
| mi_bhavisya-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_bhavisya-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_bhavisya-Complete.depth | Complete.depth | information | measured: 195 rows, 18 cols; fully populated 16; NEVER populated ['base_rate', 'contact_id'] / required: the Complete gate's claim |
| mi_bhavisya-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 27 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_bhavisya-Build.dep_liveness | Build.dep_liveness | stale | measured: 3/6 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_pramana (stale, chart 482012f1)', 'ph_nimitta (stale, chart 4820... |
| mi_bhavisya-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: bhav-N1 | chronology / Earn | real (T1 section 7.3, SS question) | a rebuild re-stamps `emitted_at` and recomputes `frozen_bundle_hash` (:123, :30-33, :228-231): the claim carries no stable emission time, exactly the chronology reset T1 section 7.3 forbids ("re-stamping emission time turns a frozen claim into a hindsight leak"). With 20 of 139 windows already begun at the stamp and 12 already over, a later rebuild can only move more claims behind the events they are matched against. The authoritative issuance stores are the two `brahma_*` ledgers (18 open, 5 unverifiable/dismissed) which this table does not link to (Q-L5-02) |
| new: bhav-N2 | Earn (frozen_bundle_hash) | real | the hash covers `chart_id | prediction_id | emitted_at | version` only — identifiers and a clock, not the claim, window, confidence or falsifier — so editing a row's content does not change its "frozen" hash. The label asserts content freezing the code does not do (T2c: content-complete issuance snapshot) |
| new: bhav-N3 | idempotency | real (by code reading) | `DELETE ... lifecycle_status IN ('pending','due')` (:230) then an unconditional `INSERT` with no `ON CONFLICT` (:243); the key is `(chart_id, prediction_id)` and `prediction_id = pred_{anchor_id}` is deterministic. Any row that has left `pending` (set to `expired` by the sweep, `confirmed`/`denied` by `mi_abhilekha`, or preserved by `chart_context_stale_at`) survives the delete and collides with its own re-insert while the anchor still exists — the run would fail on `mimamsa_predictions_pkey`. Also `due` is deleted here but is a status no code path writes (statuses written elsewhere: `expired`, `confirmed`, `denied`). Not exercised (no such row exists yet); the guard test checks the DELETE text only |
| new: bhav-N4 | Null / invented defaults | real | missing anchor fields become values: `magnitude_expected = anchor.magnitude or "moderate"` (:159), `eval_date = ... or window_end or date.today()` (:136), `conf_low = float(... or 0.4)` / `conf_high ... or 0.7` (:162-163; a genuine 0.0 is also replaced), domain `"unknown"`, MSR fallback to the first 5 signals of any domain (:168-171). On the canonical chart none of the defaults fired (10 distinct bands, none equal `[0.4,0.7)`; 131 minor / 5 moderate / 3 major) — the paths are unexercised, not safe |
| new: bhav-N5 | selective denominator | real | anchors without a window are skipped silently (`continue`, :140) and the count is not reported; 139 written vs the anchor count at build time cannot be recovered now (the table was cascaded to 4) |
| new: bhav-N6 | Build.dag | real | two declared edges unread (`ph_pramana`, `ph_phaladesa`), two more unread by this writer (`mi_kula`, `mi_jivanaghatana`), and a code import from the downstream `mi_adhilepa` (CF-L5-07) |
| new: bhav-N7 | dangling references | real (stale) | 4/139 live anchors, 0/695 live driving signals (CF-L5-02): the stored bundle describes an L4/L2 state that no longer exists; a coherent rebuild in level order replaces it (CF-L5-01) |
| new: bhav-N8 | vocab | real | claim text is composed ("mixed career career_entry"); the domain vocabulary (`transition`, `wealth`, `spirituality`, `character`) does not match the LEL (`finance`, `spiritual`, `psychological`, ...) and the channel id is a fixed `ch_{domain}_verbal` with `is_literal = true` (CF-L5-06); `contact_id` never populated (census) |
| new: bhav-N10 | integrity coupling (L4 <-> L5) | real (blocks the rebuild chain) | the live `integrity_check_sql` of `mi_bhavisya` requires every prediction's `source_pramana_id` to resolve in `phala_anchors`, and `ph_nimitta`'s integrity SQL carries the same term over `mimamsa_predictions` (global, no chart filter). 135 of the canonical chart's 139 predictions fail it today (`pred_live_anchor`). By the orchestrator's rule (a false post-write check rolls the writer back and errors it, `asset_runner.py:1200-1210`, as cited by A.L4 CF-L4-02(a)) an L4 `ph_nimitta` rebuild cannot be accepted while L5 holds these rows, and an L5 rebuild needs the L4 anchors first: a cycle. A.L4's FD-2 proposes scoping or moving the term to this asset; this brief's FD-5 supplies the L5 half (a stale marker instead of a hard cross-layer integrity term) |
| new: bhav-N9 | Build.history | history | last execution complete 2026-08-13; latest record error 2026-08-21 BLOCKED on `ph_phaladesa`, `ph_pramana` (cascade); 9 aborted / 34 complete / 19 queued rows in `build_run_assets` |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `lifecycle_status = pending` | the claim awaits its window | literal at insert; later written by other assets | earned as an initial state; **rebuild deletes `pending` rows, so the status does not protect them** |
| `frozen_bundle_hash` | the bundle is frozen / immutable | sha256 of ids + clock (:30-33) | **unearned**: covers no content (bhav-N2) and changes on every rebuild (bhav-N1) |
| `emitted_at` | when the claim was issued | `datetime.utcnow()` at build (:123) | **not earned as an issuance time**: a build clock, naive UTC, reset by each rebuild |
| `confidence_band` | the forecast's stated probability range | anchor `confidence_low/high`, default 0.4 / 0.7 (:162-163) | earned when the anchor supplies it (it did, 139/139); the default is an invented value standing in for "unknown" |
| `magnitude_expected` | expected event magnitude | anchor `magnitude`, default `moderate` (:159) | as above |
| `driving_signals` | the signals that drive the claim | top-5 same-domain MSR signals by salience, else first 5 of any (:168-171) | a **selection, not a derivation**: the link from a claim to its drivers is the domain tag, not the anchor's own `signal_id`; and now dangling |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: `base_rate` written NULL (':228' comment 'computed by mi_pramana'; mi_pramana now writes NULL too); no outcome column is written here; the missing-table case raises (A6, :66-72) and the no-anchor case returns zero rows with a note.
- BAD: the four default-fills above turn 'the anchor said nothing' into a number or a word; the stored row cannot tell a default from an anchor value.
- `contact_id`, `chart_context_*` are NULL by design (set by the Jātaka correction flow).

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id: str = ctx.config["chart_id"]` (:59) is annotated `str` but is a `uuid.UUID` on the real orchestrator path (the same path the L2 fix `2aca4bbd9` documents: `ctx.config['chart_id']` is a UUID from `build_runs`). It is used (a) as a SQL parameter and (b) inside an f-string for the bundle hash (:32), which renders a UUID as its canonical string, so the hash is the same for a `str` and a `UUID`. No `json.dumps`/`canonical_json`/`stable_uuid` receives it (the `json.dumps` calls at :192-209 serialise a falsifier dict, the driving list and `{"anchor_id": ...}`, with signal/anchor ids already `str()`-ed at :109, :130). **Not exposed.** (The writer has not run on the post-#1856 provenance path; see mi_jivanaghatana.)
- **Outcome-leakage guard:** This asset is where the emission clock lives, so it is where the chronology control belongs and does not exist (bhav-N1). It writes no outcome. The Paripraśna no-auto-promotion manifest (`no_auto_promotion_manifest.ts`) states `mimamsa_predictions` "has no live INSERT/UPDATE-to-confirmed code path at all" — but `mi_abhilekha.py:67-73` is one (cross-reference); that manifest's scope is the SAMĪKṢĀ ledger, so there is no contradiction, only a different store.
- **People-entered data (N-46) / LEL data contract:** `mimamsa_predictions` is a **mixed** table (INV): rebuildable candidates plus native-verified outcomes and freeze times that are not regenerable. The writer already refuses to delete non-pending rows (:230; test-covered) and keeps `chart_context_stale` rows. The proposals below keep that and add: never delete or re-stamp a row whose status has moved, and never re-insert over it. `mimamsa_manifestation_sets` is deleted whole (:228) including sets of predictions that have moved past `pending` — the sets are derived, but after a status change they are the record of which channel the confirmed claim was filed under (FD-2).

## 3 · Disposition

**qualify (Q)** — the asset does the necessary projection (anchors to a prediction table) but presents a rebuildable candidate store as a frozen issued bundle. Qualify = keep, and either make it a true freeze (insert-if-absent with a content hash) or relabel it as candidates and let the ledgers be the authority (Q-L5-02).

Approver under Track A brief section 10: **Strategic Suvarṇa (R5: the freeze semantics change what a prediction is)**. Risk class: **high (semantics + output change; people-outcome rows protected)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Insert-if-absent: keep the first `emitted_at`, hash the content (R)

- **Answers:** bhav-N1, N2, N3; Q-L5-02
- **Change:** key rows by `(chart_id, prediction_id)`; on rebuild, `INSERT ... ON CONFLICT DO NOTHING` for existing ids (never re-stamp), update only a separate `last_seen_build` column; hash `outcome_claim | observation_window | confidence_band | magnitude_expected | falsifier | driving_signals` with a content-hash column; a changed claim becomes a new `prediction_id` (versioned), the old one `superseded`, never overwritten
- **Files / declaration / migration:** `mi_bhavisya.py:30-33,123,228-260`; additive migration (`content_hash`, `superseded_by`); digest spec re-review
- **Failing-first test and mutation:** failing-first: two consecutive builds leave `emitted_at` and `frozen_bundle_hash` unchanged; a changed anchor creates a new id and supersedes the old; a row in `confirmed` state survives and does not collide. Mutation: restore the unconditional INSERT -> collision test fails
- **Output change:** yes: the stored `frozen_bundle_hash` values change once (content hash) and `emitted_at` stops moving -> SS (R5)
- **Blast radius:** mi_pramana, mi_gunanaka, mi_pariksha, mi_sambandha, mi_abhilekha, the sweep, query_predictions
- **Rebuild:** needs production rebuild (REVIEW); old rows marked stale first (CF-L5-01)
- **Gate it moves:** Earn, Idem
- **Fix class:** data (output change) + writer code + additive migration; **buildable before J1:** tier-independent once SS rules Q-L5-02
- **Track I item:** TI-L5-12

### FD-2 · Keep manifestation sets for moved predictions

- **Answers:** n46 note
- **Change:** scope the manifestation-set delete to the same predicate as the prediction delete (only sets of `pending`/`due` predictions)
- **Files / declaration / migration:** `mi_bhavisya.py:228`
- **Failing-first test and mutation:** failing-first: a set whose prediction is `confirmed` survives a rebuild; mutation: restore the unconditional delete -> FAIL (extends `test_mi_bhavisya_irreplaceable_outcome_guard.py`, whose third test pins the unconditional delete as intended)
- **Output change:** none for current data (all pending)
- **Blast radius:** mi_sambandha reads sets
- **Rebuild:** none
- **Gate it moves:** N-46
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-13

### FD-3 · Do not turn silence into numbers (R)

- **Answers:** bhav-N4, N5; CF-L5-04
- **Change:** store NULL (or a named `unspecified`) for missing `magnitude_expected`, `eval_date`, confidence; require both confidence bounds and treat a genuine 0.0 as a value (`is None`, not `or`); skip-and-count anchors without a window and report the count in the result notes
- **Files / declaration / migration:** `mi_bhavisya.py:136-171`
- **Failing-first test and mutation:** failing-first: an anchor with `confidence_low = 0.0` keeps 0.0; with no confidence it stores NULL; mutation: restore `or 0.4` -> FAIL
- **Output change:** none on current data (defaults did not fire); behaviour change for future anchors -> SS (R5)
- **Blast radius:** columns are NOT NULL? `confidence_band` is read by query_predictions: check before the change
- **Rebuild:** needs rebuild only if defaults had fired (they did not)
- **Gate it moves:** Null, Earn
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-14

### FD-4 · Break the L4 <-> L5 integrity cycle with a stale marker (R)

- **Answers:** bhav-N10; CF-L5-02; A.L4 CF-L4-02(a)
- **Change:** when a prediction's anchor no longer exists, mark the row stale (widen the existing `chart_context_stale_reason` CHECK with `upstream_anchor_missing`, which `mi_pramana`, `mi_gunanaka`, `mi_pariksha` already filter on via `chart_context_stale_at IS NULL`) instead of letting a global integrity term in `ph_nimitta` fail; move the anchor-existence check into this asset's own integrity SQL as 'resolves OR is marked stale'; coordinate with the A.L4 FD-2 migration so the two land together
- **Files / declaration / migration:** `mi_bhavisya` integrity SQL (registry migration); CHECK widening on `mimamsa_predictions` (one additive migration); the stale-marking step in `mi_bhavisya.py` (or the Jātaka staleness flow)
- **Failing-first test and mutation:** failing-first: a prediction whose anchor is deleted in a disposable DB is marked stale and both integrity SQLs hold; mutation: remove the marker -> the L4 integrity term fails
- **Output change:** none to stored claim content; adds a marker to 135 rows -> SS (R5)
- **Blast radius:** mi_pramana / mi_gunanaka / mi_pariksha (already exclude stale rows), query_predictions (context-stale tests exist)
- **Rebuild:** none beyond the marker (a data update on derived rows; REVIEW)
- **Gate it moves:** Build.completion, Build.dag
- **Fix class:** registry/declaration + migration (CHECK) + writer code; **buildable before J1:** tier-dependent: who owns the L5->L4 reference check is the A.L4 question Q-L4-03
- **Track I item:** TI-L5-15

### FD-5 · Declare the real reads; remove the downstream import

- **Answers:** bhav-N6; CF-L5-07
- **Change:** drop the unread edges, move `_signal_family_key` to a shared helper module imported by both `mi_bhavisya` and `mi_adhilepa`, declare `bodha_msr_signals` through `bo_laksana` (already declared)
- **Files / declaration / migration:** `mi_bhavisya.py:23`; `mi_adhilepa.py:36-80`; registry migration
- **Failing-first test and mutation:** failing-first: import graph has no writer -> writer import; mutation: re-import -> FAIL
- **Output change:** none
- **Blast radius:** DAG; writer digests of two assets
- **Rebuild:** none
- **Gate it moves:** Build.dag
- **Fix class:** writer code + registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-16

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — rows built 2026-08-13 from anchors/signals that have since been replaced
- **CF-L5-02** — bhav-N7: 4/139 anchors and 0/695 signals resolve
- **CF-L5-03** — the emission-clock half of the chronology control
- **CF-L5-04** — frozen hash and defaults
- **CF-L5-06** — domain / channel / status vocabularies
- **CF-L5-07** — bhav-N6
- **CF-L5-08** — mixed table: moved rows must survive
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history cascade

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: `prediction_id, source_pramana_id, outcome_claim, domain, observation_window, confidence_band, magnitude_expected, falsifier_jsonb, driving_signals`. Volatile and excluded: `emitted_at`, `created_at`, `frozen_bundle_hash` (until FD-1 makes it content-only), `lifecycle_status` (other assets write it). Pin the anchor set and MSR generation in any comparison.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the anchor-to-prediction projection, the domain-matched driving-signal selection idea, the `pending`-only delete (N-46), the staleness-preserving behaviour, and the A6 raise on a missing L4 table.
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): recompute each prediction's window, band and falsifier from its `phala_anchors` row (requires the anchors to exist: today 4/139 do).
- **Opportunities (never blocking):** link each prediction to its `brahma_prospective_ledger` / `brahma_mimamsa_prediction_ledger` id so the issuance authority and the candidate store are one traceable chain; carry the information cutoff and life-event switch state on the row (T1 section 7.2; F-07).

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-02** — Issuance authority: is `mimamsa_predictions` a rebuildable candidate store (as T2 section 9.1 says) whose first `emitted_at` must be preserved by insert-if-absent and whose hash must cover content, or should calibration read the two `brahma_*` ledgers (18 open + 5 rows) as the issuance authority? Also: a rebuild currently collides with any row that has left `pending` (unique key, no ON CONFLICT). *Recommendation:* Keep the table as candidates with insert-if-absent, content hash and versioned supersession; link each candidate to its ledger id; calibrate only candidates that have a ledger linkage for the "prospective" stratum. (R)
- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-06** — Vocabulary authority: which L0 map joins prediction domains (transition, wealth, spirituality, character, ...) to LEL categories (finance, spiritual, psychological, residential+travel, ...) and channel ids to domains? Class-aware resolvers (L0 Q4 precedent) or a new map? *Recommendation:* One L0 map in `bg_ontology` with class-aware resolvers; unmapped = NULL (not 0). (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
