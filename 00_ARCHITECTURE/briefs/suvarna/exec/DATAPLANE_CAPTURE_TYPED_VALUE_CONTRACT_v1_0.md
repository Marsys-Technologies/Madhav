---
artifact: DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT
version: "1.2"
status: DRAFT_FOR_REVIEW (describes the contract the D6 combined plan would install; nothing is applied; the plan is not frozen)
date: 2026-10-02
lane: suvarna/land/TI-d6-dataplane-capture-fa2-001
decision: owner N-84, option A (the L1 data-plane capture repair); SS conditions (ii): precedence rule and companion marker documented, row_snapshots is the complete record
changelog:
  - "1.2 (2026-10-02): review notes: a floored fact that carries several values gets no companion marker (section 4a); the vichara counts (1,556 sorted, 1,562 unsorted for lahiri)."
  - "1.1 (2026-10-02): section 7 added: the chart_vichara capture identity (item 5, K1): nine trigger arguments, grain plus L1 source-fact provenance set, NOT a natural key."
  - "1.0 (2026-10-02): first version. Written beside the D6 combined plan draft; the plan installs the contract, in condensed form, as COMMENT ON TABLE / COLUMN, so it lives where a reader of the tables will see it."
---

# L1 data plane: what one typed fact value means (contract)

## 1. The two tables, and which one is complete

| table | role | what it holds |
|---|---|---|
| `public.l1_data_plane_row_snapshots` | **the complete record** | One append-only row per producer row. `source_row_jsonb` is the producer row exactly as written, **every column**, including every typed value column (`fact_value_num`, `fact_value_text`, `fact_value_jsonb`). Nothing is ever dropped here. |
| `public.l1_data_plane_fact_snapshots` | **a projection** | One append-only typed fact per `chart_facts` row, with **exactly one** typed value (`value_num` or `value_text` or `value_jsonb`) plus unit, epistemic class, missingness state and reason. |

A reader who needs every value a producer wrote reads `source_row_jsonb`. A reader who needs the one headline value of a fact reads the projection and applies section 2.

## 2. Precedence rule (fixed, in the capture function)

A `chart_facts` row may legitimately carry more than one of `fact_value_num`, `fact_value_text`, `fact_value_jsonb` (examples seen in real writers: an aspect row with a number and its orb in JSON; a house-lord row with a number, a label and a JSON detail; a contradiction pair with text and JSON). The projection table has a CHECK that a present fact carries exactly one typed value, so the capture function keeps **one**, by this fixed precedence:

1. `fact_value_num`, when not NULL;
2. otherwise `fact_value_text`, when not NULL;
3. otherwise `fact_value_jsonb`, when not NULL (a JSON `null` counts as NULL).

The columns that lose are set NULL in the projection (never invented, never merged) and **recorded**, see section 3. The precedence is a presentation choice for the projection, not a statement that the other values are less true: they stay in `source_row_jsonb`.

## 3. Companion marker (when something was dropped)

When more than one typed value was non-NULL, `l1_data_plane_fact_snapshots.grain_jsonb` gains two keys, in addition to the five it always had (`source_table`, `row_identity`, `fact_category`, `fact_subject`, `fact_key`):

| key | value |
|---|---|
| `typed_value_column` | the column kept, one of `fact_value_num`, `fact_value_text`, `fact_value_jsonb` |
| `companion_value_columns` | JSON array of the column names that were dropped, in precedence order |

When nothing was dropped neither key is present: a reader tests `grain_jsonb ? 'companion_value_columns'`. Example: a row with `fact_value_num = 3`, `fact_value_text = 'kendra'`, `fact_value_jsonb = {"h": 3}` yields `value_num = 3`, `value_text = NULL`, `value_jsonb = NULL`, `grain_jsonb.typed_value_column = "fact_value_num"`, `grain_jsonb.companion_value_columns = ["fact_value_text", "fact_value_jsonb"]`; the text and the JSON are in `source_row_jsonb`.

## 4. A row with no typed value at all

A `chart_facts` row whose three value columns are all NULL (a JSON `null` counts as NULL), and whose missingness would otherwise be `present` or `zero`, is recorded with missingness `floored` when the producer's `verification_pass_status` is `floored`, and `unavailable` otherwise. It is **never** recorded as `present`. The reason is the one the function already derived (`fact_value_jsonb.reason`, else `citation_human`, else `source fact carries no typed value`). Rows that already carried an explicit state (`method_inapplicable`, `unqualified_source`, `failed`, `unavailable`, `unexplored`, `floored`) are unchanged.

A fact whose explicit state is `floored` (a `{state: floored}` structured value) and that nevertheless carries several values keeps **no** value in the projection and therefore gets **no** companion marker: for any state other than `present` or `zero` the capture sets all three projected values to NULL, and the full row stays in `source_row_jsonb`. The companion marker exists only for `present` and `zero` facts that carried more than one value.

## 4a. What does not change

Row identity, `row_snapshots` content, semantic digest, the generation and partition lifecycle, `ga_condition_composite`, `ga_yoga_firings` and every other table's projection, owner, SECURITY DEFINER, `search_path`, ACL of the function, and every append-only guard. Rows that carried exactly one typed value are projected exactly as before (the `grain_jsonb` of such a row is byte-identical to the pre-change value).

## 5. How the plan installs this

The D6 combined plan (`exec/f_a2_key_widening/D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md`) replaces the capture function with hunks H1, H2, H3a and H3b (this contract) plus the F-A2 hunk, and sets `COMMENT ON TABLE` on both tables and `COMMENT ON COLUMN` on `row_snapshots.source_row_jsonb` and on `fact_snapshots.grain_jsonb`, `value_num`, `value_text`, `value_jsonb` with a condensed statement of sections 1 to 4. The comments are part of the plan's EXPECTED_DIFF (2 table comments replaced, 5 column comments added) and are removed by the rollback (the 1035 table comments are restored, the column comments set to NULL).

## 6. How this is proved (disposable PostgreSQL 15 and 17, never a real system)

An 18-shape probe inserts one `chart_facts` row per value shape and verification tier as `data_plane_builder` inside a really opened generation (real guard trigger, real capture function): before the plan the multi-value and the all-null shapes abort the capture; after the plan all 18 pass, the kept column follows the precedence, the marker lists the dropped columns, an all-null row is `floored` or `unavailable`, and the guard still refuses an unowned category. After the rollback the old shapes fail again. See `tests/test_capture_shapes.py`.

## 7. chart_vichara capture identity (item 5, K1): grain plus L1 source-fact provenance set, NOT a natural key

`public.chart_vichara` has **no natural key**: its only unique constraint is its serial primary key, and its writer deletes the (chart, ayanamsha) scope and plainly inserts (legitimate row multiplicity per actor and target across vargas, migration 747). The capture trigger nevertheless needs a row identity, because `complete_l1_data_plane_partition` compares the writer's reported row count with the number of DISTINCT row identities captured. The identity is built by `l1_data_plane_capture_row()` as `k=v|...` over the trigger's arguments.

| | arguments | meaning |
|---|---|---|
| before | `chart_id, ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version` (8) | the grain. Rows that differ only in WHICH L1 facts they rest on collapse to one identity (about 836 identities for about 1,706 rows per ayanamsha on the canonical chart, per the read-only investigation; **1,556** rows are whole-row-distinct once the fact lists are sorted, while the unsorted lists as stored give 1,562 for lahiri, because set order is nondeterministic, which still fails closed) |
| after | the same eight plus `constituent_fact_ids` (9) | **grain plus L1 source-fact provenance set**. `constituent_fact_ids` is the set of `chart_facts.fact_id` values (deterministic per fact: category, subject, key, chart, ayanamsha) the row derives from, written sorted; it is part of the row's identity because two rows resting on different source facts are different rows. It is **not** a uniqueness rule and not a natural key: nothing is declared unique, no index is created, and `chart_vichara` stays free of a natural key |

Properties: the change is arguments only (the capture function is not edited for it); only the `chart_vichara` row of `l1_data_plane_trigger_attestations` is re-attested; `fact_id` is deterministic, so the identity of a row is stable across generations; the update guard reads real unique indexes, not the capture arguments, so it is unaffected. The two halves fail closed in either order: the owner half alone, given exact duplicates, stops at completion ("reported N rows but protected capture contains N-1"); the writer half alone (sorted fact ids, whole-row dedupe), under the old eight arguments, stops at completion ("reported 1556, capture about 836"). The writer half (sort `constituent_fact_ids`, whole-row exact dedupe, a collision assertion, the acceptance SQL) is a separate lane and is not part of this plan.
