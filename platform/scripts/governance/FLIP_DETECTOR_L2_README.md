---
artifact: FLIP_DETECTOR_L2_README
version: 1.0
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
decision: SS approved the L2 (Bodha) coverage of the S-L1 flip detector as a separate tooling PR; one independent review (nothing above LOW) and green CI on the exact head are required before arming (N-95)
scope: tooling and tests only. The detector stays read-only and never writes to the database. The existing FLIP_DETECTOR_README.md is NOT edited by this change (it is owned by PR 2984); this file is its companion.
changelog:
  - "1.0 (2026-10-03): first version. L2_EXTENSION_VERSION 1.0; TOOL_VERSION stays 2.3 (the pre-L2 outputs are byte-identical, so the tool version a pre-L2 run records must not move)."
---

# flip_detector.py: L2 (Bodha) extension

`flip_detector.py` compares production with a baseline snapshot and attributes every difference to a lane hook (see `FLIP_DETECTOR_README.md`). Until now it read four L1 tables. This extension lets it also compare the **29 L2 (Bodha) tables** that the L2 data plane manifest (`l2_data_plane_asset_outputs`) declares, so an S-L2 window can be judged the same way as S-L1: every changed row attributed to a lane, every undeclared change a failure, every unread scope a NOT CHECKED line.

It is **opt-in and add-only**. Without `--l2` nothing changes: the snapshot JSON, the compare report JSON, the summary text, the exit codes, the hook-validation messages and the SQL sent to the reader are byte-identical to the pre-L2 tool. `test_flip_detector_l2.py` proves this with a differential test against a vendored copy of the pre-L2 file (`__tests__/fixtures/flip_detector/l2/flip_detector_baseline_v2_3.py.txt`, sha256 `cabb8186...`) on the golden fixtures, the 23 real hooks, 300 randomized states and the CLI.

## Usage

```bash
# baseline (before the S-L2 rebuild): L1 + L2 in the same repeatable-read read-only transaction
python3 flip_detector.py --snapshot native --l2 --out pre_l2.json.gz
# subset of tables
python3 flip_detector.py --snapshot native --l2 --l2-tables bodha_msr_signals,bodha_cgm_edges --out ...
# after the rebuild (reads production read-only, or --against another snapshot offline)
python3 flip_detector.py --compare pre_l2.json.gz --l2 --hooks-dir <hooks> --out report.json
```

* `--l2` is accepted by `--snapshot` and `--compare` only. `--l2-tables` needs `--l2` and takes registry names.
* A `--compare` WITHOUT `--l2` ignores the snapshot's `l2` section (so its output stays identical) and judges every hook entry that names an L2 table **NOT CHECKED**, never absent and never passing.
* The default `FLIP_TIMEOUT_SEC` is 120 s per attempt; the L2 read is larger (about 50k MSR rows, 50k embedding digests, 50k grounding rows). Measured against the live schema, each of the 29 SELECTs ran in 1 to 16 s (the embedding digest is the slowest). Raise `FLIP_TIMEOUT_SEC` if the shared reader is busy.
* A snapshot taken with `--l2` records `meta.l2 = true`, `meta.l2_extension_version`, `meta.l2_tables` and `meta.l2_counts`. `meta.tool_version` stays `2.3`.

## The table registry (`L2_TABLES`)

Adding a table is **one `_l2_reg(...)` call** in `flip_detector.py`; the hook validator, the reader, the diff and the tests pick it up. An entry declares: the FROM clause (alias `t`), the `category`, `subject` and `key` expressions, the generated identity expression, the content columns (label, expression), the continuous score columns, the tier column, the ayanamsha expression, `must_have_rows`, an `unread` text and a `doc` string.

### Row model

Every L2 table is read as chart_facts-shaped rows `[ayanamsha, category, subject, key, text, num, tier]`:

| column | content |
|---|---|
| ayanamsha | `ayanamsha_id` (`INVARIANT` for a table without one: the scorecard) |
| category | the coarse class a hook names in `categories` (`signal_type_class`, `node_type`, `edge_type`, `path_type`, `motif_class`, ...) |
| subject, key | together with category the **semantic natural key, never a generated id**. Edges, paths and contradictions use their node / signal labels (joined), not node or signal ids |
| text | `id=<generated identity>\|label=value\|label=digest...`: the generated identity first (signal_id, node_id, edge_id, ...), then the content columns that matter. Arrays, jsonb and embedding vectors enter as a 12-hex md5 digest (the content is never copied into a snapshot). **A signal whose generated id moves because its content changed therefore reads as one `value` change, not as an appeared plus a disappeared row** |
| num | up to five continuous scores joined by `,` (an empty part is NULL) |
| tier | `verification_pass_status` (the grounding table uses `grounding_tier`) |

Rows that share a semantic key form an occurrence list (the existing `occurrence_count` mechanism). Before pairing, rows identical on both sides (same identity text and tier) cancel as a multiset, so one moved identity in a large duplicate group (MSR, discoveries, anomalies, embeddings) is one change and does not shift the pairing of the unchanged rows; an `occurrence_count` change still reports the true totals.

### Why the scores are not passed as `num`

The existing `diff_table` compares `num` strictly whenever the text is non-empty, so a score riding in `num` next to an identity text would make every moved score a class change. The L2 diff therefore feeds `occ_map` / `diff_table` the identity text and the tier (the existing code, unchanged) and compares the scores itself as **continuous values** (tolerance as `same_num`): a moved score is counted in `continuous_l2` (`compared`, `changed`, `max_abs_delta`), never a class change, exactly like a non-integral L1 number. A score that becomes NULL is a `value` change (`note: score_lost`), as for L1. Scores are compared only between rows whose identity text is identical on both sides.

### Tables

`must_have_rows`: EMPTY_READ applies only to the tables marked yes (the producing writer raises on zero rows, or the registry `target_floor` is at least 1). Every other table can legitimately be empty for a chart and an empty read of it is not a failure.

| table | must_have_rows | key (after ayanamsha) |
|---|---|---|
| `bodha_msr_signals` | yes | signal_type_class / varga_id + configuration fact_subject + fact_key / signal_type_id |
| `bodha_signal_embeddings` | yes | the embedded signal's class / model + version / the signal's type id (an orphan embedding is `__orphan__`) |
| `bodha_cgm_nodes` | yes | node_type / node_subject / snapshot_type |
| `bodha_cgm_edges` | yes | edge_type / snapshot_type + from-node label / to-node label |
| `bodha_cgm_paths` | yes | path_type / snapshot_type + from-node label / to-node label |
| `bodha_cgm_motifs` | no | motif_class / snapshot_type + motif_name / fingerprint_hash |
| `bodha_cdlm_cells` | yes | snapshot_type / tradition view + dynamic system and lords / domain and subdomain row and column |
| `bodha_triangulation` | no | question_class / (none) / tradition |
| `bodha_contradictions` | no | tension_class / type id of signal A / type id of signal B |
| `bodha_convergence` | no | snapshot_type / dynamic system and lords / domain |
| `bodha_rm_resonances` | yes | snapshot_type / (none) / graha |
| `bodha_mechanisms` | yes | mechanism_class / snapshot_type + name / fingerprint_hash |
| `bodha_discoveries` | no | discovery_class / subsystem / novelty class + affected domains (many rows per key) |
| `bodha_anomalies` | no | anomaly_type / subsystem / metric (many rows per key) |
| `bodha_pratijna` | no | `pratijna` / (none) / event_class_id (status is content) |
| `synthesis_quality_scorecard` | yes | `scorecard` / (none) / `row` (ayanamsha `INVARIANT`) |
| `bodha_cgm_sub_graphs`, `bodha_cgm_chart_topology_summary`, `bodha_cdlm_chart_summary`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters`, `bodha_chart_gestalt`, `bodha_question_lenses`, `bodha_grounding_matches`, `bodha_rm_chart_summary`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies` | no | see the registry entries |
| `bodha_rm_remedy_prescriptions` | yes | remedy_category / snapshot_type + graha + tradition + sub_tradition / remedy_id_g27 |

Each generated SELECT was executed against the live schema as `suvarna_reader` (single SELECT through the read-only helper) and returned exactly the table's row count for the canonical chart. The registry text carries the per-table justification in its `doc` and `unread` fields.

## Hooks

`HOOK_TABLES` gains the 29 L2 names (additive; the `'table' must be one of ...` message still lists the original five so the pre-L2 validation output stays byte-identical). A hook entry on an L2 table uses the L2 `category` value in `categories` and may narrow with `fact_keys` (the `key` column), `ayanamsha_ids`, `change_types` (`appeared`, `disappeared`, `value`, `occurrence_count`, `tier`) and `expected_count`, with the same absence rules as any other entry. A hook that declares only continuous-score movement cannot be observed (scores are not class changes): such an entry reads DECLARED_BUT_ABSENT or needs `optional`.

## NOT CHECKED rows added in an L2 run

| id | when | meaning |
|---|---|---|
| `<lane>[<i>]` | a hook entry names an L2 table that was not compared (no `--l2`, a table missing from the snapshot, or outside `--l2-tables`) | the entry cannot be observed; never absent, never passing |
| `l2.not_compared` | `--l2` was given but a snapshot (or the `--against` snapshot) lacks the section or some tables | names the tables; a real L2 change in them would read as no change |
| `l2.unread_columns` | always in an L2 run | the columns outside each registry entry (per-table text under `l2_unread` in the report); embedding vectors, jsonb and arrays are compared by a 12-hex md5 digest only |
| `l2.generation_ledger` | always in an L2 run | the L2 data-plane generation ledger (producer generations, heads, partitions, run intents, row snapshots) is not readable by the reader role; the detector sees the active tables only, never the generation that produced them |

In an L2 run the two L1-era standing rows that say `bodha_msr_signals` / `bodha_rm_resonances` are "table not read by the detector" are dropped for the tables that ARE compared (they would be false). The verdict is still never PASS in production.

## Report additions (L2 runs only)

`compared.l2` (list of tables compared), `l2_extension_version`, `continuous_l2` (per table: `compared`, `changed`, `to_null`, `max_abs_delta`, `keys_appeared`, `keys_disappeared`, `keys_both`), `l2_unread`, `meta.flags.l2` and `meta.flags.l2_tables`. The L2 changes are appended to `changes` after the L1 and dasha changes, so the L1 ordering is unchanged. The summary prints `l2 (Bodha) tables compared: N of 29` and a `continuous (l2 <table>)` line for tables whose scores moved.

## Limits

* Scores are compared only for rows whose identity text is unchanged; a row whose identity moved is reported as a value change and its score movement is not separately counted.
* The cancel-then-pair rule pairs the leftovers of a duplicate-key group by sorted identity text, so two simultaneous identity moves in one group may pair crosswise (still two `value` changes).
* Content outside the registry entries is invisible (see `l2.unread_columns`); extend the entry when a lane's change lives in an unread column.
* The reader cannot see the generation heads: confirm head promotion with a privileged login (`l2.generation_ledger`).
* The EMPTY_READ rule cannot tell an unbuilt chart from a blocked reader for must-have tables: a chart without an L2 build fails `--l2` snapshots by design.

## Tests

`__tests__/test_flip_detector_l2.py` (222 offline tests: per-table before/after for appeared / disappeared / value / occurrence_count / tier, continuous scores, attribution, NOT CHECKED paths, EMPTY_READ, the differential add-only proof, end-to-end snapshot and compare through a fake `FLIP_READER`, a new golden file `fixtures/flip_detector/l2/golden_flip_detector_l2_expected.json`) and `__tests__/test_flip_detector_l2_mutations.py` (22 mutations of the new code, each caught). Regenerate the L2 golden only with `FLIP_DETECTOR_REGEN_GOLDEN=1` after reading the diff.
