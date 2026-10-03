---
artifact: MI_BHAVISYA_APPEND_ONLY
canonical_id: SUVARNA_L5_MI_BHAVISYA_APPEND_ONLY
version: "1.0"
status: "DRAFT_FOR_REVIEW (writer + tests change; nothing applied to production; no migration)"
produced_on: 2026-10-03
produced_in: "Exec Suvarṇa"
plan_item: "TI-mi-bhavisya-appendonly-001"
layer: L5 (Mīmāṃsā)
asset: mi_bhavisya
ruling_implemented: "SS N-104 (an application of N-46): HARD PRECONDITION of any L5 rebuild. mi_bhavisya must never delete or rewrite an existing prediction row, pending or frozen."
exception_to: "CLAUDE.md §N.3 (L1+ per-chart delete-then-insert) -- for append-only calibration tables only"
files:
  - platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py
  - platform/python-sidecar/tests/test_mi_bhavisya_append_only.py
  - platform/python-sidecar/tests/test_mi_bhavisya_irreplaceable_outcome_guard.py
  - platform/src/generated/nirmana-writer-digests.json
changelog:
  - "1.0 (2026-10-03): first version. Writer made append-only; natural key; tests both ways on a fake and a disposable PostgreSQL; mutation proofs; what the asset's count and integrity read after a rebuild."
---

# mi_bhavisya is append-only (documented exception to §N.3)

## 1. Why this is an exception, not a drift

§N.3 says L1+ writers do per-chart delete-then-insert, so a rebuild REPLACES rather than accretes. That is correct for derived state. `mimamsa_predictions` is not derived state: a row is a claim issued at a time, and the table exists to be compared with what happened afterwards. Three measured facts show what delete-then-insert does to it:

* A routine rebuild deleted every `pending` row (all 139 on the canonical chart; the builder-role trigger `mimamsa_predictions_builder_guard` only refuses non-pending/due deletes).
* `emitted_at` and `frozen_bundle_hash` were re-stamped on every rebuild, so a claim never carried its real issuance time.
* Migration 680 rewrote `source_pramana_id` on 191 of 195 frozen rows; the table has no UPDATE guard, so "frozen" was convention only.

SS N-104 (an application of N-46) rules the table history. This writer is therefore the documented exception: **no DELETE, no UPDATE, no `ON CONFLICT DO UPDATE`, of either table, ever.** The same holds for `mimamsa_manifestation_sets`: it is where the original freeze id of a migration-680 row survives (`citation_ref.anchor_id`), so deleting and re-inserting it would erase that evidence even if every prediction row were kept.

## 2. What changed (before / after)

| | before | after |
|---|---|---|
| `DELETE FROM mimamsa_manifestation_sets WHERE chart_id` | every run | gone |
| `DELETE FROM mimamsa_predictions WHERE chart_id AND lifecycle_status IN ('pending','due')` | every run (executed even when no valid anchor had timing) | gone |
| prediction insert | unconditional `INSERT` (would collide on the PK for any survivor) | read what is frozen; skip an anchor that is already frozen; `INSERT ... ON CONFLICT (chart_id, prediction_id) DO NOTHING` for the rest |
| manifestation-set insert | for every anchor | only for a prediction inserted by this run; `ON CONFLICT (chart_id, prediction_id, channel_id) DO NOTHING` |
| `emitted_at` / `frozen_bundle_hash` | re-stamped on every rebuild | stamped once, when the row is first inserted; existing rows keep their bytes |
| `rows_inserted` | planned count | rows actually added (0 on a no-op rebuild); `rows_skipped` = anchors already frozen |
| `dry_run` | would freeze everything | reports exactly what a real run would add (reads only) |

Unchanged: `@register("mi_bhavisya")` `WriterBase`, `run(ctx) -> WriterResult`, never commits or closes `ctx.db_conn`, no `asset_throughput` write, the A6 raise on a missing `phala_anchors`, the claim composition, the defaults, the driving-signal selection, the hash formula. No edit to `runner.py` or `asset_runner.py`.

## 3. The natural key

The only unique index is the primary key `(chart_id, prediction_id)`, checked against the production catalog (`pg_indexes`, read-only): `mimamsa_predictions_pkey` is the sole unique index. `prediction_id = 'pred_' || anchor_id`. A PK-only rule is not safe, because the anchor id a prediction was frozen under is not the anchor id it points to now:

* Production, read-only, 2026-10-03: for the 60 current anchors across the two charts, **0 match a stored `prediction_id` (`pred_<anchor>`), and all 60 match a stored `source_pramana_id`** (migration 680 re-pointed `source_pramana_id` to the deterministic id and left `prediction_id` alone). A PK-only append would have inserted **60 duplicate predictions** on the first rebuild.

So an anchor is treated as already frozen when, for the same chart, `prediction_id = 'pred_<anchor_id>'` (freeze-time key) **or** `source_pramana_id = '<anchor_id>'` (current anchor reference) exists. `ON CONFLICT (chart_id, prediction_id) DO NOTHING` stays as a belt for a row that appears between the read and the insert. Measured effect on production: **0 rows would be inserted on either chart.**

Deliberately not used: a content key such as `(domain, window, falsifier)`. A prediction carries only four of the ten fields of the anchor identity tuple (migration 680), so such a key can collapse distinct claims; the L5 reference-resolution ledger design (PR #3023) rejects it for the same reason and treats it as a labelled, weaker `superseded` evidence class. That ledger is the place for "this stored claim's anchor moved or vanished"; this writer does not interpret it, it only declines to rewrite.

## 4. Consequences a reviewer should expect

1. **A moved anchor adds a new prediction and leaves the old one.** If `ph_nimitta` changes an anchor's event tuple (a new deterministic id), the next rebuild inserts a new prediction for the new id; the old row stays, dangling, for the ledger to record. Calibration then holds both, by design.
2. **A stale-marked prediction still blocks a fresh one for the same anchor.** `chart_context_stale_at` rows are kept (that is history too). If the anchor id is unchanged after a chart-details change, no fresh prediction is inserted for it; the count of such rows is reported in the result notes. Whether staleness should supersede an anchor is a ruling, not something to do by rewriting the row.
3. **`emitted_at` is now an issuance time for inserted rows only.** It is still `datetime.utcnow()` (naive, inserted into a `timestamptz`, so session TimeZone applies); that and `frozen_bundle_hash` covering only ids and a clock are separate findings (brief bhav-N1/N2), untouched.
4. **Registry text that is now stale.** Migration 991's `natural_key_partition` (and 990's comments) justify the manifestation-set digest by the writer's "idempotent DELETE ... exactly the current run's row set exists". That reasoning no longer holds (the set is now cumulative). Applied migrations are not edited; correcting the registry string needs a new migration, which this change does not author. The digest itself is unaffected: it keys on `(chart_id, prediction_id, channel_id)` and excludes `frozen_at`, so a no-op rebuild yields an identical digest (`output_changed` false), and an insert changes it.
5. **The existing DELETE-scope guard test is replaced.** `test_mi_bhavisya_irreplaceable_outcome_guard.py` pinned the old `pending/due` DELETE and the unconditional set DELETE as intended behaviour; it now pins their absence.

## 5. What the asset reads after a rebuild

Measured on a disposable PostgreSQL 17 with the production table shape, with the live `integrity_check_sql` text (`/Users/Dev/suvarna-evidence/S_L1/mi_bhavisya_live_check.txt`) and the 1259 variant (that text minus the global dangling-anchor term); evidence `mib_integrity_probe_out.txt`:

| state | count_sql | integrity, live text | integrity, 1259 text |
|---|---:|---|---|
| empty, 4 anchors | 0 | true | true |
| after first rebuild (4 predictions + 4 sets added, `rows_inserted` 8) | 8 | true | true |
| after a second rebuild (`rows_inserted` 0, `rows_skipped` 4) | 8 | true | true |
| plus one prediction citing a vanished anchor | 10 | **false** | true |
| after a rebuild over it (row left alone, `rows_inserted` 0) | 10 | **false** | true |

* `count_sql` reads the tables, not `WriterResult`, so it does not drop and is not inflated. `rows_written` on the build record is the rows added this run; the orchestrator's no-op-completion logic (`asset_runner.py`, `target_floor` is 0 for this asset) lets a 0-row rebuild finish `lit`. On production both are unchanged by a rebuild: canonical 139 + 139 = 278.
* The live integrity text still carries the global dangling-anchor term; production has 135 predictions whose anchor is gone. **Until migration 1259 (HELD) lands, a rebuild of this asset on production is still rejected by its own post-write integrity check** (rolled back, errored). This change makes the rebuild safe to attempt; it does not make that check true. With the 1259 text the check is true over a state that includes dangling rows.
* L5 data-plane capture/partition: `capture_and_persist_receipt` takes `output_digest` from the asset's digest spec (migration 990: `mimamsa_manifestation_sets` only, `where_equals` the canonical chart id) and the partition declaration (migration 991). Neither needs a changed reported count; the receipt does not read `rows_inserted`.

## 5a. Manifestation sets: what depends on them, and what changes if anchors changed

`mimamsa_manifestation_sets` is covered by the same rule (no DELETE, no UPDATE, insert-if-absent by its primary key `(chart_id, prediction_id, channel_id)`), and a set is added only together with a prediction inserted in the same run. Tests: byte-for-byte unchanged and count not dropping in `existing` and `anchor_moved`; the statement audit covers both tables; mutants for a set DELETE, a `citation_ref` UPDATE, a set `DO UPDATE` and sets-for-skipped-predictions are all caught.

Readers that depend on the sets:

* `mi_pramana` reads `(prediction_id, channel_id)` for the chart to score the manifestation dimension of each prediction/event match; a matched prediction with no set scores against an empty channel list.
* `mi_sambandha` counts one "opportunity" per set row (joined to `mimamsa_calibration` for verdict and fired channel) to seed channel propensities.
* Served: `query_manifestation_sets` (retrieval) and the `source_query_availability` count.
* The integrity SQL requires a set for every prediction and a prediction for every set (FULL JOIN), so a set may never exist without its prediction nor the reverse.

What a rebuild used to do: delete every set and re-create one per CURRENT anchor, so after the anchors collapsed to 4, the set table would have shrunk from 139 to 4 and `citation_ref` (the only place the original freeze id of a migration-680 row survives) would have been overwritten with the current anchor id. What it does now: nothing to existing sets. Consequences if anchors changed since the freeze: the historical sets stay (so `mi_sambandha`'s opportunity counts keep counting every frozen prediction, 139 on the canonical chart, not 4); a re-identified anchor adds one new prediction and one new set while the old pair stays, so one event can appear as two opportunities until the reference-resolution ledger marks the old one superseded; `mi_pramana` keeps finding the channels of old predictions that still match events.

Not done, on purpose: adding a missing set for an EXISTING prediction. Its `citation_ref` would have to name the current anchor, not the freeze-time one, which is exactly the overwrite this ruling forbids; production has 139/139 and 56/56, so nothing is missing today.

Found, not changed (a second delete path outside the writer): `platform/src/lib/cockpit/assetClearSpec.ts` lists `DELETE FROM mimamsa_manifestation_sets WHERE chart_id = $1` and `DELETE FROM mimamsa_predictions ... lifecycle_status IN ('pending','due')` as the cockpit "clear" for `mi_bhavisya`. That is a web-side action, not this writer, and it carries the same hazard N-104 closes; it needs its own ruling and change.

## 6. Verification

* `tests/test_mi_bhavisya_append_only.py`: scenarios `existing` (pending, due, confirmed, stale-marked and a 680-shape row: counts do not drop, every column of every row byte-identical, `rows_inserted` 0), `empty` (full set inserted, second run a byte-identical no-op), `partial` (exactly the absent keys, plus their sets), `notiming` (no window / no anchors deletes nothing), `anchor_moved` (an anchor re-identified since the freeze: the old prediction and its set stay byte-identical, one new of each is added), `dry_run`, `race`, and a statement audit (no DELETE/UPDATE/TRUNCATE/`DO UPDATE`, every insert `DO NOTHING`). Run on an in-memory fake (always) and on disposable PostgreSQL 15 and 17 (real DDL: migration 347 + the stale columns/constraints/trigger read from the production catalog), the latter also as a role holding only `SELECT, INSERT` on the two tables.
* 16 mutants (reintroduced prediction/set DELETE, unscoped delete, `emitted_at` and hash re-stamps, a `citation_ref` UPDATE and a set `DO UPDATE`, weaker natural keys, no existing check, `DO UPDATE`, no `ON CONFLICT`, planned-count reporting, dry-run writes, sets for skipped predictions, a commit) are all caught; each mutation asserts its target text exists exactly once.
* Known weak spot, stated honestly: the mutant that drops the `prediction_id` half of the key is behaviourally covered by `ON CONFLICT DO NOTHING` and is caught only through `rows_skipped`.

## 7. Other `mi_*` writers that delete or rewrite rows (listed, not changed)

`mi_pramana` (`mimamsa_calibration`, `mimamsa_reliability`: per-chart delete-then-insert of values computed from the predictions and outcomes), `mi_gunanaka` (`mimamsa_multipliers`), `mi_adhilepa` (five overlay tables), `mi_pariksha` (`mimamsa_discoveries`, `mimamsa_qa_eval` by check type, `mimamsa_attribution`), `mi_darshana` (insight units/embeddings), `mi_jivanaghatana` (`mimamsa_event_provenance`), `mi_sambandha` (`mimamsa_manifestation_grammar`), `mi_kula` (global negative controls / signal families). Service paths: `mi_abhilekha` UPDATEs `mimamsa_predictions.lifecycle_status` (pending to confirmed/denied, the sanctioned outcome write; no re-stamp), `mi_sankalpa` deletes only its own unresolved `elected_pending` ledger rows and reclassifies `study_arm`. Whether any of the calibration-value tables should also be history is a ruling for SS.
