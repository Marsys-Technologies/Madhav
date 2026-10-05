---
version: 1.0
status: CURRENT
lane: TI-i-fl2-002
item: TI-L2-18 (Q-L2-04 trace)
branch: suvarna/land/TI-i-fl2-002
basis: origin/main adb0db29d (code read); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.0 -- trace of the 14 yoga_label rows that store source_corroboration_count_by_text = 2. Evidence only; no code, data, registry or declaration change.
---

# TI-L2-18: where do the 14 `yoga_label` rows with `source_corroboration_count_by_text = 2` come from?

Track A A.L2 item TI-L2-18 (SS ruling Q-L2-04, N-59): "trace the 14 `yoga_label` rows that
store `source_corroboration_count_by_text = 2` (source not traced in the sheet); treat them like
the three constant sites if uncomputed". This is the trace. Nothing in the repository other than
this note and its query file changes.

## Answer

**The 14 rows are computed, not hand-set.** Their count is the number of distinct classical texts
in the row's own `classical_sources_jsonb.citations`, produced by
`_corroboration_count_by_text` (`platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:1644`,
called from the row builder at `:2513`). The contingency "treat them like the three sites if
uncomputed" does not apply: TI-L2-28 should NULL the constant sites only and leave these 14 rows
(and the 20 `yoga_label` rows with count 1, and the 6 dosha rows with count 1) as they are.

## What was measured (canonical chart, production, 2026-10-03)

Every `bodha_msr_signals` row of the chart with a non-NULL `source_corroboration_count_by_text`
(94 of 50,678), compared with the number of distinct text ids derived from its own citations
(`split_part(citation, ':', 1)` over `classical_sources_jsonb->'citations'`, plus `'_pg'`-prefix
of `text_chunk_ids`):

| signal_type_class | signal_type_id | rows | stored count | distinct texts in own citations | `classical_sources_jsonb` | formula version | verdict |
|---|---|---|---|---|---|---|---|
| yoga | `yoga_label:yoga_name` | 14 | 2 | 2 (`bphs`+`saravali`) | present | v2.0 | computed (equal on all 14) |
| yoga | `yoga_label:yoga_name` | 20 | 1 | 1 (`bphs:35`) | present | v2.0 | computed (equal on all 20) |
| dosha | `dosha_label:dosha_name` | 6 | 1 | 1 | present | v2.0 | computed (equal on all 6) |
| varga_pattern | `navamsha_d9_cross_check:<graha>` | 45 | 2 | n/a | NULL | **v1.0** | **hand-set constant** |
| varga_ratification_divergence | `varga_ratification_divergence:SAT:<domain>` | 9 | 2 | n/a | NULL | v2.0 | **hand-set constant** |

All 94 are produced by `bo_laksana`. The other 50,584 rows of the chart (all seven producers)
store NULL.

The 14 rows by catalogue id: vasi x5 (`bphs:30`, `saravali:41`), anapha x4 (`bphs:30`,
`saravali:38`), sasa x5 (`bphs:75`, `saravali:27`); each carries two different text ids, so the
stored 2 is the true distinct-text count. The 20 count-1 rows are gola / yuga_nabhasa / kedara /
shoola with the single citation `bphs:35`.

## The three constant sites (TI-L2-28) and what each contributes to the live chart

| site | emits | live rows on 482012f1 |
|---|---|---|
| `bo_laksana.py:1423` (`varga_ratification_divergence` row builder) | `"source_corroboration_count_by_text": 2` | 9 |
| `bo_laksana.py:2969` (`navamsha_d9_cross_check` row builder, `signal_type_id` at `:2895`) | `"source_corroboration_count_by_text": 2` | 45 |
| `bodha_writers/bhavat_bhavam_amplifier.py:345` | `"source_corroboration_count_by_text": 2` | **0** (the chart has no `bhavat_bhavam_amplifier` signal class; the 18 live classes were listed) |

So TI-L2-28's NULL change touches 54 live rows (45 + 9), and the amplifier site is a dormant
constant on this chart.

## Observations carried forward (not acted on)

* The 45 `navamsha_d9_cross_check` rows are stamped `salience_formula_version = 'v1.0'` while every
  other `bo_laksana` row carrying a count is `v2.0`; all were computed 2026-09-08. TI-L2-28's
  "stamp hand-set rows `classification_weight_v1`" will therefore re-stamp rows that currently
  read as v1.0, not v2.0. Worth one line in the J1 reviewers' list item (the weight table).
* The two hand-set sites also store `classical_sources_array = NULL` and `classical_sources_jsonb`
  NULL: there is no citation to count, which is the strongest reason the honest value is NULL
  (CLAUDE.md N.7 item 6).
* Row counts are a live reading and will move at the next rebuild; the queries are in
  `ti_l2_18_queries.sql` next to this note (reader-only SELECT).

## What is NOT done

No writer change, no stored-value change, no `salience_formula_version` change, no declaration or
registry edit, no rebuild. TI-L2-28 itself (writer code, rebuild, J1 weight table) is unchanged and
still batched.
