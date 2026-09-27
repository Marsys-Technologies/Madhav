---
artifact: NIKASHA_WAVE2_W2-3_C1_REVIEW
packet: W2-3 corrections (C1 / C2 / C3) and the bo_upaya reversal
reviewer: independent reviewer of corrections (fresh context, read-only, never the implementer)
reviewed_on: 2026-09-28
prior_review: W2-3_REVIEW.md (fb7ef7cdd, ACCEPT_WITH_CORRECTIONS, wave2_complete yes)
commits: [af30cfe2b, 3aec11b5b, 55e4981b9, a742900a0]
verdict: ACCEPT_WITH_CORRECTIONS
wave2_ready_to_fold: "yes, with bo_upaya-Idem.pattern withheld by the procedure in §1 (RC-1). That procedure is a condition of the next production emit, not of the fold text."
final_closure_count: "58 = 51 unconditional + 6 chart-conditional (482012f1 only) + 1 withheld (bo_upaya)"
scratch: "<scratchpad>/rev-w2-3b/ (queries q1–q15, FK dump, ledger copies; worktrees wt_head a742900a0 and wt_base 8702ee331, both removed at the end)"
production_ledgers: "asset_gaps.jsonl 7f2257a8d4f0d6a7a21c0648b4101f85 (830 lines), asset_certs.jsonl 514cbdfcf3fa71b3e382f84a978bf369. Read through scratch copies only, never written; identical at start and at close."
db_access: "read-only role (default_transaction_read_only=on). An EXPLAIN DELETE was refused by the role with 'permission denied', so nothing could have been written."
---

# Nikaṣa wave 2 · W2-3 corrections · independent review of the bo_upaya reversal

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.**

- **The bo_upaya reversal is real.** I reproduced it from the code history, the writer, the repo DDL and the live
  catalog (§2). Its current-code rebuild fails a NO ACTION, non-deferrable foreign key on every chart, 482012f1
  included. The original "genuine" hand-check was wrong. The closure must not land.
- **No other landmine.** I ran my own screen: every foreign key in the database, not only the 10 the builder listed
  (§3). No other closure among the 58 has a restrictive child that its rebuild would leave referencing a deleted
  row. bo_upaya is the only one.
- **The numbers are right.** 58 = 51 unconditional + 6 chart-conditional + 1 withheld. All 18 MSR dependent-count
  cells reproduce exactly.
- **C2 and C3 hold.** Spot-checks were read from the code and the database (§4, §5).
- **Scope and regression are clean** (§6).

**One correction, bound to the next production emit (RC-1): the withholding mechanism is not specified well enough
to carry out safely.** The report says "Hand-withhold it, as W2-2's C2 did for ka_kshetra, and leave it OPEN". Three
things are missing:

1. **The precedent was never carried out.** W2-2's C2 hand-withholding was superseded by the C-KSHETRA detector fix
   before any second emit ran (W2-2_REPORT §5.3; STATE.md). No executor has ever hand-withheld a row, so there is
   no procedure to copy.
2. **`emit_gaps()` has no exclusion option.** It appends a CLOSED row for every PASS whose latest row is OPEN or
   IN_PROGRESS (`asset_census.py:2612–2730`). None of the ledger's own states can hold the row off without lying:
   - WITHDRAWN is a terminal human rejection, and it would also block any later re-open;
   - `superseded_by` retires the id permanently;
   - IN_PROGRESS is still closable.
3. **It has to recur.** The detector still grades bo_upaya PASS (the builder's `emit_c3.log` closes the same 58). So
   **every** emit will re-close it until either (a) the owner fix lands and a real rebuild is observed, or (b) the
   FK-children detector row the report proposes lands. The report says "the next production emit" only.

**Required fold text for RC-1** (the executor records it with the fold; no code change is needed):

> For every production `--emit-gaps` run, until bo_upaya's FK is resolved (owner) or the FK-children detector row
> lands (Nikaṣa):
> 1. Run it with `NIKASHA_CONTROL_DIR` pointing at a scratch copy of `00_ARCHITECTURE/control/`.
> 2. Diff the appended lines against the production ledger.
> 3. Delete exactly one appended line: `"gap_id": "bo_upaya-Idem.pattern"` with `"state": "CLOSED"`.
> 4. Check that the remaining appended set is exactly what the census predicts. For the next emit on today's
>    ledger that is 57 CLOSED `Idem.pattern` + 11 OPEN `Complete.depth`, 0 re-opened.
> 5. Only then copy the result over the production ledger.
>
> Never run the emit directly on the production ledger while this hold stands. The row stays OPEN, with its
> existing OPEN row as its latest.

The six MSR-family scope annotations need the same kind of statement. The emitted CLOSED row has no `chart_scope`
field, and the ledger `_schema` names a fixed field set. So the annotation belongs in the register fold (R20's
closure text). It must not be written into ledger rows unless the executor also records that this extends the
schema.

**Acceptance statement for the executor's fold of all of wave 2.** Wave 2 (W2-1, W2-2, W2-3) is ready to fold, with
these conditions:
- **R20 / R241 / R240 / R242 / R21 / R23 fold as built.**
- **The 69-PARTIAL resolution folds as 51 unconditional PASS + 6 chart-conditional PASS + 1 withheld (bo_upaya) +
  11 PARTIAL + 0 FAIL.**
  - The six are bo_arudha, bo_laksana, bo_nakshatra_semantic, bo_special_lagna, bo_sudarshana and
    bo_vargottama_dhana. Their scope: `482012f1 only; refused on 1c826d5a, cb73cd3d via
    public.assert_l2_msr_delete_safe` (bo_laksana: refused on 1c826d5a only).
  - The native ruling on "DB interlock = hold?" stays queued.
- **`bo_upaya-Idem.pattern` stays OPEN**, withheld on every emit by the RC-1 procedure.
  - Owner action: bo_upaya must clear or re-point its legacy `bodha_rm_dasha_windowed_prescriptions` children
    before it replaces prescriptions. This conflicts with DP-SD-015's "legacy rows preserved", so it is a ruling,
    not a mechanical fix (§7 F-2).
  - A Nikaṣa detector row is opened to read the replaced tables' RESTRICT / NO ACTION children from
    `pg_constraint` and grade un-cleared referencing children as a FAIL.
- **C2's blind-spot list and C3's 19-dark-table figure fold as reported.**

## §2 — bo_upaya: independent verification

### §2.1 The writer change (code history)

- **Before.** At `aa26d83bb` (#2529, the code of the last real builds on 2026-09-09), `bo_upaya.py:2200–2204` read:
  ```
  # B-4's windowed rows FK-reference bodha_rm_remedy_prescriptions —
  # delete them BEFORE the prescriptions they reference are replaced.
  replace_prior_rm_dasha_windowed(conn, chart_id, aya)
  replace_prior_rm_prescriptions(conn, chart_id, aya, SNAPSHOT_TYPE)
  replace_prior_rm_resonances(conn, chart_id, aya, SNAPSHOT_TYPE)
  ```
- **The change.** `fa9857f00` (#2607, 2026-09-16, "feat(data-plane): deliver governed L0-L3 source execution") is
  an ancestor of HEAD. It removes the `replace_prior_rm_dasha_windowed` import and call, and the B-4 window builder.
  In their place it adds "DP-SD-015: do not delete or append the legacy daśā-window table. Existing history remains
  readable".
- **At HEAD.** `bo_upaya.py:1904–1986` `run()` does the following:
  - deletes the three chart-scoped rollups (:1933–1935);
  - then, per ayanamsha in `CANONICAL_AYAS` (lahiri_chitrapaksha, raman, krishnamurti, surya_siddhanta_classical,
    true_chitra), calls `replace_prior_rm_prescriptions(conn, chart_id, aya, 'static_natal')` (:1945) and then
    `replace_prior_rm_resonances` (:1946).
  - It never calls `replace_prior_rm_dasha_windowed`. The helper still exists at `bodha_writers/_idempotency.py:455`
    with no caller in the tree.
  - The prescriptions DELETE is `_idempotency.py:445`:
    `DELETE FROM public.bodha_rm_remedy_prescriptions WHERE chart_id=%s AND ayanamsha_id=%s AND snapshot_type=%s`.
- **Nothing else in the rebuild path clears the legacy table.** I grepped the whole tree. The only other DELETE is
  the cockpit "Clear" op (`platform/src/lib/cockpit/assetClearSpec.ts:98`). It runs only on `clear_before: true`;
  the runs route defaults to `false` (`api/cockpit/runs/route.ts:115`). There is no DB trigger or rule that
  cascades it either (§2.2).

### §2.2 The FK and the rows (live catalog, read-only; `q1`–`q4`)

| check | result |
|---|---|
| FKs onto `bodha_rm_remedy_prescriptions` | exactly one: `bodha_rm_dasha_windowed_prescriptions_base_prescription_id_fkey`, `FOREIGN KEY (base_prescription_id) REFERENCES bodha_rm_remedy_prescriptions(prescription_id)` |
| `confdeltype` / `condeferrable` / `condeferred` / `convalidated` | `a` (NO ACTION) / false / false / true: checked at the end of each DELETE statement; not CASCADE, not SET NULL |
| repo DDL | `platform/migrations/325_l2_bodha_enriched_schema.sql:782`: `base_prescription_id UUID NOT NULL REFERENCES bodha_rm_remedy_prescriptions(prescription_id)` (NOT NULL too, so SET NULL is not even available as a re-point) |
| referencing rows, 482012f1 | **5**: one per ayanamsha, all `static_natal` parents, all build `fcdcd284` |
| referencing rows, 1c826d5a | **9** (2+2+2+1+2), build `51eaa05c` |
| referencing rows, cb73cd3d | **6** (1+1+2+1+1), build `d47f0e98` |
| total legacy rows / NULL base | 20 / 0 |
| triggers on both tables | only `l2_data_plane_mutation_guard` (BEFORE, per row) and `l2_data_plane_capture` (AFTER INSERT/UPDATE); nothing deletes children; no rewrite rules |
| last bo_upaya attempts (`build_run_assets`) | latest started 2026-09-09 23:57 (`fcdcd284`, complete, disposition build); none since #2607 (2026-09-16). The failure has never been exercised. |
| data-plane generation runs for bo_upaya | 0 (`l2_data_plane_generation_runs` is empty) |

**The failure, constructed without writing (`q4`).** I mirrored the writer's first DELETE as a SELECT on 482012f1.
- Every ayanamsha's DELETE predicate matches 27 prescription rows. Exactly one of them is still referenced by a
  legacy row that no statement in the rebuild removes.
- With a NO ACTION, non-deferrable FK, the very first DELETE (lahiri_chitrapaksha) raises `23503
  foreign_key_violation` at statement end. The orchestrator's savepoint then rolls the substep back.
- So the rebuild neither replaces nor accretes. It errors.
- (An `EXPLAIN DELETE` was refused by the read-only role, "permission denied". This confirms nothing could have
  been written.)

**Conclusion: confirmed real, and exactly as the report states.** On 482012f1, 1c826d5a and cb73cd3d, the next
current-code rebuild of bo_upaya fails. `Idem.pattern` PASS is not earned on any chart.

### §2.3 Was the original hand-check wrong, and was the gap forgivable?

**Yes, it was wrong.** The v1.0 row credited `replace_prior_rm_resonances` / `_prescriptions`
(`_idempotency.py:425–455`) and "no populated refusal". The gate review (fb7ef7cdd §7.2) repeated the same blind
spot: it recorded only "bo_upaya helpers carry no DB assert", looking for asserts and not for FKs.

**My ruling: a process finding, not a forgivable "DB constraints are outside a Python read" gap.** A careful
Python-and-repo read had five signals within reach, and none of them needed the database:

1. **The comment beside the credited DELETE.** It sits directly above the line both readers credited
   (`bo_upaya.py:1942–1944`) and says a sibling table's rows are now kept: "do not delete … the legacy daśā-window
   table. Existing history remains readable".
2. **The helper that is no longer called.** The cited range `_idempotency.py:425–455` ends on the `def` line of
   `replace_prior_rm_dasha_windowed`, and nothing calls it.
3. **The writer's own result note** says "legacy rows preserved".
4. **The FK is in repo DDL**, not only in the catalog: `migrations/325…sql:782`.
5. **The cockpit clear spec states the chain.** `assetClearSpec.ts:95–97`: "rm chain: resonances ←
   remedy_prescriptions ← dasha_windowed_prescriptions. Delete deepest child first."

**Mitigation.** The builder found and retracted this unprompted, beyond the gate review. The class is not new:
W2-2's ka_kshetra and C1's six MSR assets are the same "hold below the Python" shape.

**Process rule for every future DELETE-based closure** (fold it into the hand-verify discipline):
- enumerate the NO ACTION / RESTRICT children of each deleted table (`pg_constraint`, or repo DDL);
- for each, show one of: the rebuild path deletes or re-points the referencing children first; the children
  provably cannot reference the deleted scope; or the live count is 0.

This is the detector row the report proposes, and it should be built, not only recorded.

## §3 — "Any other landmine": my own screen (`q6`–`q11`)

**Method.** I did not start from the builder's `c1_restrict_fks.txt`.

1. **Every foreign key.** I dumped all 158 FKs in `public`: 39 NO ACTION, 34 RESTRICT, 16 SET NULL, 68 CASCADE.
   Cross-schema FKs onto `public` tables: none (the only two non-public FKs are internal to `nirmana_evidence`).
2. **The closure tables.** I took the 58 closed ids from `next_emit_transitions_final.txt` and every
   counted/replaced table from `idem_r20b.json`. That gives 69 distinct tables. The builder's "68" leaves out
   `fact_category_ownership` (ga_structural), which its PASS text does not credit; it has no FK children, so the
   result is the same.
3. **Parents that any writer deletes.** I grepped all of `platform/python-sidecar` for `DELETE FROM` / `TRUNCATE`
   on each of the 34 restrictive parent tables, including dynamic `DELETE FROM {table}` helpers. I also searched
   `pg_proc` bodies for DELETEs on those parents. The only hits were planner-inquiry functions, unrelated to any
   writer.

**Result: the restrictive (a/r) edges onto closure tables are exactly the builder's 10.** No RESTRICT-type parent is
a closure table, which is why the builder's list shows only `a`.

| parent (closure) | child | writer's DELETE on the parent | live verdict |
|---|---|---|---|
| bodha_rm_remedy_prescriptions (bo_upaya) | bodha_rm_dasha_windowed_prescriptions | yes, child not cleared | **FAILS: 5 / 9 / 6 rows** |
| bodha_rm_resonances (bo_upaya) | bodha_rm_remedy_prescriptions | yes, after its prescriptions DELETE in the same scope | safe: 0 prescriptions outside the (chart, aya, static_natal) scope reference an in-scope resonance; only `static_natal` exists (405 / 135 rows) |
| reference_nakshatra (bg_nakshatra) | reference_nakshatra_pada | `l0_nakshatra.py:1395–1397` deletes matrix, then pada, then nakshatra | safe (children first) |
| bg_transit_rules (bg_transit_rules) | gochara_resonance_map.source_rule_id | `l0_transit.py:982`, stale owned ids only | **safe today.** I ran the writer's own `compute_stale_rule_ids` on the live rows: 1 stale id (569), **0** children reference it (196 child rows point at 46 other ids). A rebuild retires 569 cleanly. |
| bg_vastu_directions | bg_vastu_direction_remedials | none (`ON CONFLICT (direction) DO UPDATE`, `l0_vastu_directions.py:305`) | safe |
| brahma_event_ontology (bg_ghatana) ×5 children | activity_ontology, bodha_pratijna, prospective_ledger, gochara_resonance_map, intervention_ledger | none (`l0_ghatana.py:887/928`, ON CONFLICT) | safe |

**Other checks.**
- **CASCADE chains from closure tables.** These go to bodha_msr_signals → kala_* / contradictions / embeddings,
  brahma_yoga_catalog → reference_yogas / source_chunks, and chart_facts → chart_fact_identity. None of them
  reaches a NO ACTION / RESTRICT grandchild, so there is no hidden failure through a cascade.
- **Restrictive parents deleted by assets outside the 58**, same class, not blocking:
  - ph_rectification deletes `phala_rectification_best` before `phala_rectification` (safe);
  - bg_texts' full delete-first path is quarantined (upsert only);
  - bg_vidhi_primitives retires unlisted `vidhi_primitives` under a RESTRICT child. That is unexamined here and
    noted as §7 F-4.

**Conclusion: bo_upaya is the only closure with a live restrictive-FK landmine. The builder's screen claim is
confirmed.**

## §4 — C2: empty-upstream reclassification, spot-checked (`q13`–`q15`)

**The builder's claim.** 24 writers skip their replacement on empty input, and all of them read PASS. 18 of those
are W2-3 closures: bg_concordance, bg_rules, 9 ga_*, 6 bo_*, mi_bhara.

**What I checked.**
- **Does the skip keep stale rows alive today?** It does only if a chart (or the global L0 table) currently holds
  prior output while its upstream is empty.
- **Can a surviving row carry a stale reference?** That is bo_upaya's failure class.

| spot-check | code | today |
|---|---|---|
| **bg_concordance (L0)** | `bg_concordance.py:86/108` return a normal `WriterResult` ("HALT: …", 0 rows) when `reference_topic_tags` or tagged chunks are empty; the full `DELETE FROM classical_attributions` (:207) is deliberately reached only after the desired projection is computed ("keeps upstream failure non-destructive") | upstream 481 topic tags, 7,010 tagged chunks → the replacement runs; `classical_attributions` has no FK to anything (no DB landmine) |
| **ga_vichara (L1)** | `ga_vichara_writer.py:963/969` return before `_delete_prior_vichara_rows` (:1016 → :161–168) on empty facts or constants | every chart × aya with `chart_vichara` rows has chart_facts (15/15); `brahma_vichara_constants` = 7 → the replacement runs |
| **bo_grounding (L2)** | `bo_grounding.py:159` `if not rows: continue` before `replace_prior_grounding_matches` | only 482012f1 has rows. Each aya has 10–11 fired yogas and ~10.1k signals → it replaces. **Stale-reference probe:** 50,678/50,678 `msr_signal` targets and 53/53 `yoga_dosha_firing` targets resolve to live rows; `target_id` is TEXT with no FK |
| **mi_bhara (L5)** | `mi_bhara.py:159` `if not lel_events:` records the LEL-absent note. The replacement `replace_prior_skill_and_gof` (`services/mi_bhara/db.py:204–220`) is scoped to (chart × weights_version × field_snapshot), a versioned natural key §N.3 permits | only 482012f1 has 7 `kala_field_skill` rows; `kala_field_skill` / `kala_field_gof` are not FK parents |

**Ruling.**
- **PASS is the right grade for this shape.** On a populated input it replaces. No chart is in the empty-upstream
  state today for any of the four, so "a state no chart is in today" is true where I measured it.
- **None of the 24 owns a restrictive-FK parent with children.** §3 covers every closure table. The six
  pre-existing PASS writers (ka_avadhi, ka_bhavishya_lekha, ka_yojaka, mi_bhavisya, mi_gunanaka, mi_pariksha) own
  no table in the restrictive-parent list.
- **The residual is disclosed correctly.** If an upstream ever empties, the prior rows survive a "successful"
  0-row rebuild. That breaks §N.3's "rebuild REPLACES", although it is not accretion.
- **Precise wording to fold.** bg_concordance's skip returns success, not a raise. On an emptied upstream the
  build would read complete while serving the previous projection. The residual is disclosed, not detected, and
  its §N.8 aspect belongs to the Build criteria, not to Idem. This is not a new blocker.

## §5 — C3: dark-table spot-checks

| table | claimed reader | verified |
|---|---|---|
| ga_prashna_judgment | `platform-mcp/src/tools/register_p1_synthesis.ts:1011` | ✓ `FROM ga_prashna_judgment gj WHERE gj.chart_id = $1`, a real `platformQuery` in the synthesis tool; the module is imported by `server.ts` / `registry_bridge.ts` |
| reference_nakshatra | `tools/register_p1_reference.ts:549` | ✓ `FROM reference_nakshatra n` (it also reads `reference_nakshatra_pada` in a subselect) |
| bg_gochara_citation_resolution | `tools/retrieval/register_gochara_windows.ts:734` | ✓ a concatenated query: `` `SELECT citation_string, … ` + `FROM bg_gochara_citation_resolution ` + … ``. This is exactly the form the SELECT-literal fix makes readable. |
| kala_field_skill | `platform-mcp/src/lib/kala_envelope.ts:553/556` | ✓ `FROM kala_field_skill` (twice); see note below |

**Minor.** The report says `kala_envelope.ts` is "imported by five `tools/kala_views/*` tools". I count 10
non-test importers (shared, priority, explain, upaya, elect, ahead, now, ritual, dasha_sandhi, story). This is an
understatement only. `lib/**` is scanned as a root either way, so no figure changes.

**Still genuinely dark (my own search of `platform-mcp/src/lib/**`, `platform-mcp/src/tools/**` and
`platform/src/**`).**
- **`kala_field`**: every occurrence is inside comments or string literals. Examples are
  `lib/kala_ritual_resonance.ts:494–507` ("no registry capability exists over any kala_field* table") and
  `tools/kala_views/ahead.ts:740`. No query reads it.
- **`bodha_signal_embeddings`**: there is no SQL read anywhere.
  - `L2_bodha/query_signals.ts` describes pgvector search over it (:4, :19, :319) but always takes the salience
    fallback (:478 "vertex embedding not available at query time").
  - `coverage_matrix.ts:709` maps it to `marsys://tool/L2/get_signal_embeddings`, a tool that does not exist
    (§7 F-3).

**C3 ruling.** C3 holds: 26 → 19 dark tables. The code change only widens the scan (`CAPS_ROOTS`) and keeps
SELECT-only literals. The census diff shows 0 verdict changes (§6).

## §6 — Scope and regression

- **Files touched by the 4 commits** (`git show --stat`):
  - `platform/scripts/governance/asset_census.py` (+27/−5), `__tests__/test_w2_3_deeper_detectors.py` (+58);
  - `nikasha_test/wave2/W2-3_REPORT.md` and `w2-3_evidence/**`.
  - Nothing else: no writer, migration, orchestrator, register or ledger.
- **Production ledgers.** `asset_gaps.jsonl` md5 `7f2257a8d4f0d6a7a21c0648b4101f85` (830 lines) and
  `asset_certs.jsonl` `514cbdfcf3fa71b3e382f84a978bf369`, unchanged. The latest `bo_upaya-Idem.pattern` row is
  OPEN (2026-09-27T21:28:25).
- **Offline suite at `a742900a0`** (temporary worktree, no DB env): 351 = **325 passed · 24 skipped · 2 failed**.
  The 2 failures are the pre-existing `test_drift_detector_h35_h38.py` pair. This matches the report. I did not
  re-run the 9-minute live suite; the report's 349/2 is taken from `suite_c3_live_tail.txt`.
- **Manifest:** `manifest_fingerprint.py --check`: 141/141, declared = observed `1847709eec2bad52`, **MATCH**.
- **Drift:** exit **3**, 1 LOW `a3_category_not_yet_populated` (pre-existing). Run without DB credentials it adds
  two environmental `*_db_unreachable` LOWs, still exit 3.
- **Census diff `8702ee331` vs `a742900a0`**, six layers, read-only, scratch control dir; both sides ran against the live DB a few minutes apart.
  - **Result:** **0 verdict changes attributable to the commits.** Idem.pattern at HEAD: 110 PASS · 11 PARTIAL · 1
    FAIL · 5 N/A, with bo_upaya still PASS as the detector reads it.
  - **Text-only changes are exactly the report's 10 `Reach.fields`:** bg_dignity_reference, bg_ghatana,
    bg_gochara_citation_resolution, bg_nakshatra, bg_remedies, bg_transit_rules, ga_prashna, ka_gochara,
    ka_gochara_resonance, mi_bhara.
  - **One environmental artefact, excluded.** On the base run, ph_phaladesa's `Complete.depth` ERRORED on a
    transient `psql … timeout expired`. That dropped one dependent check (2,445 vs 2,446) and changed its Reach
    text. It is not caused by any commit: ph_phaladesa is untouched and the error is a connection timeout.
  - Evidence: `rev-w2-3b/census_diff_review.txt`.

## §7 — Remaining findings (none blocks the fold except RC-1's emit condition)

| id | finding | severity | binds to |
|---|---|---|---|
| **RC-1** | The withholding mechanism is under-specified: the ka_kshetra precedent was never carried out; `emit_gaps` has no exclusion; the re-close recurs on every emit. The procedure in §1 must be recorded with the fold. | medium | **every production emit** until the bo_upaya FK is resolved or the FK-children detector row lands |
| F-1 | Process: DELETE-based closures need an FK-children check (§2.3). Both the builder's and the gate review's hand-checks missed a repo-visible FK. | low (process) | the hand-verify discipline; the proposed detector row |
| F-2 | The owner fix for bo_upaya is a ruling, not a mechanical fix. Restoring the legacy DELETE contradicts DP-SD-015's "existing history remains readable". The FK is NOT NULL, so SET NULL needs a column change. Dropping or re-pointing the FK changes the schema. Related stale text: migration 1013's natural_key_partition still says "all six deleted-then-inserted per (chart_id, ayanamsha_id)"; the 1012/1017 digest specs still list the legacy table as a bo_upaya component; `cr_status.ts:171` says "rebuild now writes 5 windowed rows". | medium (owner) | bo_upaya owner / DP-SD-015 authority. Also a cross-campaign heads-up: any Nirmana L2 step that needs an observed accepted bo_upaya rebuild will hit the same FK error. |
| F-3 | `bodha_signal_embeddings` is advertised as a pgvector search source (`query_signals.ts:319`), but the code always falls back, and `coverage_matrix.ts:709` points at a non-existent tool. An §N.8-class description/behaviour mismatch. | low | OS-3 dispatch |
| F-4 | Out of the 58: bg_vidhi_primitives retires unlisted `vidhi_primitives` rows under a RESTRICT child (`vidhi_floor_items`). Not examined. It falls under the proposed detector row. | low | the detector row |
| F-5 | Wording: `aa26d83bb` line cite `:2203–2204` should be `:2202–2203` (windowed then prescriptions); "68 tables" is 69 counted (see §3); "five" kala_envelope importers is 10. | trivial | report errata |

## §8 — Fact spot-check

| # | claim (report v1.1) | my measurement | ✓/✗ |
|---|---|---|---|
| 1 | FK `base_prescription_id` → prescriptions is NO ACTION, NOT DEFERRABLE | `confdeltype=a`, `condeferrable=f`, `condeferred=f` | ✓ |
| 2 | Legacy rows 5 / 9 / 6 on 482012f1 / 1c826d5a / cb73cd3d, all `static_natal` parents | 5 / 9 / 6 | ✓ |
| 3 | The 482012f1 rows come from build `fcdcd284`, same as their parents | `fcdcd284` for both | ✓ |
| 4 | #2607 = `fa9857f00`, 2026-09-16, removed the windowed delete, kept the prescriptions DELETE (`bo_upaya.py:1945`) | diff and HEAD read | ✓ |
| 5 | Old order at `aa26d83bb` `:2203–2204` | windowed :2202, prescriptions :2203 | ~ (off by one) |
| 6 | bo_upaya has not run since #2607; last attempt 2026-09-09 | `build_run_assets` max `started_at` 2026-09-09 23:57 | ✓ |
| 7 | All 18 MSR dependent cells (§0.1 table), 482012f1 = 0 for all six | reproduced, cell for cell | ✓ |
| 8 | Restrictive FKs onto the closure tables = the 10 in `c1_restrict_fks.txt` | identical 10 (independent full dump) | ✓ |
| 9 | bg_transit_rules "retires only stale rows; fails loudly if one is referenced" | code ✓; live: stale {569}, 0 references | ✓ |
| 10 | 58 = 51 + 6 + 1 | 58 closed ids; 6 MSR; 1 bo_upaya | ✓ |
| 11 | 24 empty-upstream writers, 18 of them W2-3 closures | 17 bg/ga/bo + mi_bhara = 18, all in the closed-58 | ✓ |
| 12 | `register_p1_synthesis.ts:1011` reads ga_prashna_judgment | `:1011 FROM ga_prashna_judgment gj` | ✓ |
| 13 | kala_field and bodha_signal_embeddings genuinely dark | no SQL read in MCP or `platform/src` | ✓ |
| 14 | Offline 351 (325 / 24 / 2); manifest MATCH; drift exit 3, 1 LOW | identical | ✓ |
| 14a | Census diff `8702ee331`→`af30cfe2b`: 0 verdict changes, 10 `Reach.fields` text-only | same 10 and 0 verdict changes (after excluding one transient DB-timeout artefact on ph_phaladesa) | ✓ |
| 15 | Ledger md5s unchanged, 830 lines | identical | ✓ |
| 16 | "Hand-withhold, as W2-2's C2 did for ka_kshetra" | W2-2's C2 was never executed (superseded by C-KSHETRA) | ✗ (RC-1) |
