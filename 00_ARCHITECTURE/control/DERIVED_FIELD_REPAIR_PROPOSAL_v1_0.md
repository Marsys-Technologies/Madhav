---
canonical_id: DERIVED_FIELD_REPAIR_PROPOSAL
version: 1.0
status: >-
  SUPERSEDED BY EVENTS — corrected 2026-08-23 (M0-T32). Three of the four sub-items this
  document proposed have since been APPLIED by other tasks: 0.5a (layer_index / layer_name)
  by M0-T26, 0.6a (has_substeps) by M0-T20, 0.6b (kind reconciliation) by M0-T21. Only 0.5b
  (SOURCE classification of `lel_events`) is still unapplied — and D-23 has since DEFERRED it
  to R5 outright (reversing D-21), so it is not M0's to apply at all. The MEASUREMENTS and the PROPOSED SQL below are untouched and remain the
  record of what was proposed and why; what changed is that they are no longer a description
  of the live database. See `applied_status` for the per-sub-item live reading.
status_until_2026_08_23: DRAFT — PROPOSAL ONLY, NOTHING APPLIED
authored_by: KĀRAKA (Nirmāṇa autonomous campaign, task M0-T8)
authored_at: 2026-08-23T04:44:44Z
certified_by: null   # I16/H7 — the author does not certify. PARĪKṢAKA verifies; ADHIKĀRIN rules.
branch: campaign/nirmana-autonomous
writes_executed: >-
  NONE BY M0-T8 (scope clarified 2026-08-23 by M0-T32 — the original field read
  "writes_executed: NONE" unqualified). Every figure in this document comes from a read-only
  SELECT run against the live database with `SET default_transaction_read_only = on`. No
  UPDATE, no DDL, no migration authored to disk, no migration applied — by the task that
  authored this document. Writes have since been executed against three of its four
  sub-items by OTHER tasks; see `applied_status`.
applied_status: |
  Measured read-only 2026-08-23T07:25Z; see the §0 status-correction block.
  0.5a layer_index / layer_name — APPLIED by M0-T26 (2026-08-23T06:51Z). C-02 21 -> 1,
    C-03 20 -> 1; the single survivor on each is lel_events, deliberately held NULL
    (DECISIONS D-28 part 1).
  0.5b SOURCE classification of lel_events — NOT APPLIED, AND NO LONGER M0's TO APPLY.
    lel_events still reads asset_kind='data', asset_type='data'; 0 rows in asset_registry
    carry asset_kind='source'. The ruling §3 asked for has returned twice: D-21
    (2026-08-23T05:01:44Z) GRANTED the CHECK widening as an M0 deliverable, and D-23
    (2026-08-23T05:04:21Z) REVERSED D-21 IN FULL — plan §8.4's R5 row assigns "lel_events
    reclassified SOURCE" to R5 by name, a specific assignment governs a general exit
    criterion (D-12), and widening the CHECK in M0 would be pre-building for a later phase.
    So 0.5b is DEFERRED TO R5 and recorded as unmet, not green. §3 below still reads as an
    open question awaiting a ruling; it is not.
  0.6a has_substeps — APPLIED by M0-T20 (2026-08-23T05:48Z). 26 rows now has_substeps=true.
  0.6b kind reconciliation — APPLIED by M0-T21 (2026-08-23T06:03Z). C-14 reads 0 live, but
    the reading is NON-DURABLE: asset_kind and asset_type are both in
    asset_registry_seed.ts's ON CONFLICT DO UPDATE list, and the post-reseed projection in
    m0_exit_scorecard.json puts C-14 back at 8 violations on the next seed run
    (M0_EXIT_SCORECARD_v1_0.md, durability section). The repair is real; its survival is not.
derives_from:
  - NIRMANA_ELEVATION_PLAN_v4_0.md Phase 0.5a / 0.5b / 0.6a / 0.6b
  - ASSET_CATALOGUE_CONTRACT_v1_0.md §4.2, §4.8, §5, §6 (C-02, C-03, C-14, C-23), §7, §10.1
  - DECISIONS.jsonl D-4 (mechanical-backfill standard + mandatory correctness detector), D-9
    (migrate.ts import prohibition; --target pinning)
  - CLAUDE.md §N.1 (locked lexicon), §N.2 (FROZEN writer contract), §N.8 (earned signal)
measurement_baseline: public.asset_registry, 128 rows (127 is_active), measured 2026-08-23
changelog:
  - version: 1.0
    date: 2026-08-23
    change: >
      First authoring. Re-measures Phase 0.5a/0.5b/0.6a/0.6b from the live database and from
      the writer source tree, proposes the repair for each, and states a pre-flight correctness
      detector per backfill in the style D-4 condition 3 requires. Three of the plan's four
      stated figures were found wrong and are corrected here with the query that refutes them.
---

# Derived-field repair proposal — Phase 0.5a / 0.5b / 0.6a / 0.6b

## §0 — What this document is, and the one thing it is not

**Is:** a measurement and a proposal. For each of the four sub-items: what the live state
actually is (query + verbatim output), what the corrected value per affected asset is, the
derivation rule that produces it, the exact SQL that would apply it, and a pre-flight detector
that can tell a correct backfill from an incorrect one *before* it is trusted.

**Is not:** an application, a certification, or an authority to proceed. **EXECUTE NO WRITE**
was this task's constraint and it was honoured *by this task*: nothing in §2–§5 was run **by
M0-T8**. Two of the four sub-items additionally require an ADHIKĀRIN ruling before they may be
run at all (§3 and §5.5), and those are stated as questions, not assumed.

> **STATUS CORRECTION — 2026-08-23 (M0-T32).** The sentence above used to read "nothing in
> §2–§5 has been run," present tense, with no agent attached. That was true when authored and
> is false now: **0.5a, 0.6a and 0.6b have all since been applied** — by M0-T26, M0-T20 and
> M0-T21 respectively, each under its own ruling and its own verification. Only **0.5b**
> (§3, `lel_events` → SOURCE) is still unapplied — but NOT for the reason §3 gives: D-21
> granted it, D-23 reversed D-21 in full and DEFERRED 0.5b to R5 (plan §8.4's R5 row assigns
> "lel_events reclassified SOURCE" to R5 by name). §3 below still reads as a question awaiting
> a ruling. Two rulings have returned; the second is binding.
> Re-scoped to name the agent rather than softened, because the *proposal* genuinely executed
> nothing and that fact should survive; what could not be allowed to survive is a present-tense
> reading of the live database that is 39 rows and three sub-items out of date. The per-sub-item
> live measurement is in the frontmatter's `applied_status`, measured read-only at
> 2026-08-23T07:25Z. **Nothing in §1–§8 below was rewritten** — the figures there are M0-T8's
> measurement of 2026-08-23T04:44:44Z and are left exactly as measured.

**No migration file was authored to disk, deliberately.** D-9 §2 measured the blast radius of
the `migrate.ts` entrypoint hazard as "exactly three unapplied files on disk today, and the
hazard becomes severe the moment any unreviewed migration lands on disk." Adding a fourth
unapplied file — one whose content is gated on rulings that have not returned — would widen that
radius for no gain. The SQL is complete and transcribable in §2.5 / §4.5 / §5.5; whoever is
authorized to apply it authors the numbered file at that moment. If ADHIKĀRIN prefers the file
on disk first, that is a one-line instruction and this author will write it.

---

## §1 — Summary: measured vs. the plan's stated figures

| Sub-item | Plan's figure | Measured here | Verdict |
|---|---|---|---|
| 0.5a `layer_index` | 14 NULL + 6 malformed = **20** | **15 NULL + 6 malformed + 0 mismatch = 21** | plan LOW by 1 |
| 0.5a `layer_name` (implied) | not separately stated | **15 NULL + 5 wrong-spelling = 20** | new figure |
| 0.5b SOURCE blocker | not stated | **CONFIRMED** — CHECK permits only `data\|service\|artifact` | M0-T2's blocker is real |
| 0.6a `has_substeps` | **14** false negatives | **12** false negatives, **0** false positives | plan HIGH by 2 |
| 0.6b kind disagreements | **6** | **6** | plan CORRECT |

Three notes on the discrepancies, because a corrected number with no account of why is just a
different unexplained number:

1. **0.5a is not a contradiction with the M0-T1 census.** `CENSUS_REPORT.md §6` reports
   `layer_index_null — 14`, and it is right *for the class it defines*: its four
   non-conformance classes are mutually exclusive and its own header says they are "kept apart
   on purpose". `lel_events` is counted once, in `unrecognised_prefix`, so it is absent from
   the null class. The **total** number of rows whose `layer_index` is not the contract form is
   21. M0-T2's contract §9 independently reports 15 NULL and agrees with this measurement
   exactly. The plan's "14 null" carried the census *class* count forward as if it were the
   repair-set size; the repair set is larger by one, and that one is the asset whose
   disposition is contested (§3).
2. **0.6a's plan figure includes two writers the source refutes.** The plan's 14 are the 12
   below plus `bg_reference` and `bo_laksana_rerank`. Neither implements `plan_substeps` or
   `run_substep`; both implement `run(ctx)` only, and neither sets `has_substeps = True` on its
   class. `bg_reference.py` is 51 lines and contains no occurrence of the string
   `plan_substeps` at all. Evidence in §4.2.
3. **0.6b's plan figure is exactly right and the six named assets match** the contract's C-14
   list asset-for-asset.

---

## §2 — Sub-item 0.5a: layer position (`layer_index`, `layer_name`)

### 2.1 The measurement

`layer_index` distribution (Q1), verbatim:

```sql
SELECT coalesce(layer_index,'<NULL>') AS layer_index, count(*) AS n
FROM asset_registry GROUP BY 1 ORDER BY 1;
```
```
        0 | 1
        1 | 2
        2 | 1
        3 | 2
       L0 | 37
       L1 | 16
       L2 | 10
       L3 | 21
       L4 | 9
       L5 | 14
   <NULL> | 15
```

`layer_name` distribution by layer (Q3), verbatim:

```sql
SELECT layer, coalesce(layer_name,'<NULL>') AS layer_name, count(*) AS n
FROM asset_registry GROUP BY 1,2 ORDER BY 1,2;
```
```
 bodha       | Bodha       | 11
 bodha       | <NULL>      | 11
 brahmagyan  | Brahmagyan  | 38
 brahmagyan  | <NULL>      | 2
 ganita      | Ganita      | 2
 ganita      | Gaṇita      | 16
 ganita      | <NULL>      | 1
 kala        | Kala        | 3
 kala        | Kāla        | 20
 mimamsa     | Mīmāṃsā     | 14
 mimamsa     | <NULL>      | 1
 phala       | Phala       | 9
```

NULL-overlap (Q5) — the two columns are NULL on **exactly the same 15 rows**, never one without
the other:

```sql
SELECT count(*) FILTER (WHERE layer_index IS NULL) AS li_null,
       count(*) FILTER (WHERE layer_name IS NULL)  AS ln_null,
       count(*) FILTER (WHERE layer_index IS NULL AND layer_name IS NULL) AS both_null,
       count(*) FILTER (WHERE layer_index IS NULL AND layer_name IS NOT NULL) AS li_only,
       count(*) FILTER (WHERE layer_name IS NULL AND layer_index IS NOT NULL) AS ln_only
FROM asset_registry;
```
```
 li_null | ln_null | both_null | li_only | ln_only
   15    |   15    |    15     |    0    |    0   
```

That matters for the repair: it means the 15 NULLs are a single event (rows registered by a
migration that never wrote the two derived columns), not two independent drifts.

### 2.2 C-02 violations — all 21, enumerated

Query = ASSET_CATALOGUE_CONTRACT §8 rule C-02, unchanged, with the defect class labelled:

```sql
SELECT asset_id, layer, coalesce(layer_index,'<NULL>') AS layer_index_now,
       (CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1'
                   WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3'
                   WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END) AS layer_index_expected,
       CASE WHEN layer_index IS NULL THEN 'NULL'
            WHEN layer_index !~ '^L[0-5]$' THEN 'MALFORMED'
            ELSE 'MISMATCH' END AS defect_class
FROM asset_registry
WHERE layer_index IS NULL
   OR layer_index !~ '^L[0-5]$'
   OR layer_index <> (CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1'
                                 WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3'
                                 WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END)
ORDER BY defect_class, asset_id;
```

Verbatim result — **21 rows**:

| # | asset_id | layer | layer_index now | proposed | defect class |
|--:|---|---|---|---|---|
| 1 | `bg_sign_medical` | brahmagyan | `0` | `L0` | MALFORMED |
| 2 | `bo_pratijna` | bodha | `2` | `L2` | MALFORMED |
| 3 | `ga_ayurdaya` | ganita | `1` | `L1` | MALFORMED |
| 4 | `ga_sensitive_degree` | ganita | `1` | `L1` | MALFORMED |
| 5 | `ka_avadhi` | kala | `3` | `L3` | MALFORMED |
| 6 | `ka_taranga` | kala | `3` | `L3` | MALFORMED |
| 7 | `bg_vidhi_floors` | brahmagyan | `<NULL>` | `L0` | NULL |
| 8 | `bg_vidhi_primitives` | brahmagyan | `<NULL>` | `L0` | NULL |
| 9 | `bo_arudha` | bodha | `<NULL>` | `L2` | NULL |
| 10 | `bo_cdlm_summary` | bodha | `<NULL>` | `L2` | NULL |
| 11 | `bo_cgm_motifs` | bodha | `<NULL>` | `L2` | NULL |
| 12 | `bo_cgm_paths` | bodha | `<NULL>` | `L2` | NULL |
| 13 | `bo_chart_gestalt` | bodha | `<NULL>` | `L2` | NULL |
| 14 | `bo_laksana_rerank` | bodha | `<NULL>` | `L2` | NULL |
| 15 | `bo_nakshatra_semantic` | bodha | `<NULL>` | `L2` | NULL |
| 16 | `bo_special_lagna` | bodha | `<NULL>` | `L2` | NULL |
| 17 | `bo_sudarshana` | bodha | `<NULL>` | `L2` | NULL |
| 18 | `bo_vargottama_dhana` | bodha | `<NULL>` | `L2` | NULL |
| 19 | `bo_yantra_mechanism` | bodha | `<NULL>` | `L2` | NULL |
| 20 | `ga_vichara` | ganita | `<NULL>` | `L1` | NULL |
| 21 | `lel_events` | mimamsa | `<NULL>` | **(HELD — §3)** | NULL |

**MISMATCH count is 0.** No row's `layer_index` names a *different* layer than its `layer`
column; every defect is an absence or a format error. That is a materially weaker defect than
"the layer is wrong", and it is stated separately so the repair is not described as bigger than
it is.

### 2.3 C-03 violations — all 20, enumerated

```sql
SELECT asset_id, layer, coalesce(layer_name,'<NULL>') AS layer_name_now,
       (CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita'
                   WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla'
                   WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END) AS layer_name_expected,
       CASE WHEN layer_name IS NULL THEN 'NULL' ELSE 'WRONG_SPELLING' END AS defect_class
FROM asset_registry
WHERE layer_name IS DISTINCT FROM
      (CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita'
                  WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla'
                  WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END)
ORDER BY defect_class, asset_id;
```

Verbatim result — **20 rows**:

| # | asset_id | layer | layer_name now | proposed | defect class |
|--:|---|---|---|---|---|
| 1 | `bg_vidhi_floors` | brahmagyan | `<NULL>` | `Brahmagyan` | NULL |
| 2 | `bg_vidhi_primitives` | brahmagyan | `<NULL>` | `Brahmagyan` | NULL |
| 3 | `bo_arudha` | bodha | `<NULL>` | `Bodha` | NULL |
| 4 | `bo_cdlm_summary` | bodha | `<NULL>` | `Bodha` | NULL |
| 5 | `bo_cgm_motifs` | bodha | `<NULL>` | `Bodha` | NULL |
| 6 | `bo_cgm_paths` | bodha | `<NULL>` | `Bodha` | NULL |
| 7 | `bo_chart_gestalt` | bodha | `<NULL>` | `Bodha` | NULL |
| 8 | `bo_laksana_rerank` | bodha | `<NULL>` | `Bodha` | NULL |
| 9 | `bo_nakshatra_semantic` | bodha | `<NULL>` | `Bodha` | NULL |
| 10 | `bo_special_lagna` | bodha | `<NULL>` | `Bodha` | NULL |
| 11 | `bo_sudarshana` | bodha | `<NULL>` | `Bodha` | NULL |
| 12 | `bo_vargottama_dhana` | bodha | `<NULL>` | `Bodha` | NULL |
| 13 | `bo_yantra_mechanism` | bodha | `<NULL>` | `Bodha` | NULL |
| 14 | `ga_vichara` | ganita | `<NULL>` | `Gaṇita` | NULL |
| 15 | `lel_events` | mimamsa | `<NULL>` | **(HELD — §3)** | NULL |
| 16 | `ga_ayurdaya` | ganita | `Ganita` | `Gaṇita` | WRONG_SPELLING |
| 17 | `ga_sensitive_degree` | ganita | `Ganita` | `Gaṇita` | WRONG_SPELLING |
| 18 | `ka_avadhi` | kala | `Kala` | `Kāla` | WRONG_SPELLING |
| 19 | `ka_gochara_v3_century_materialize` | kala | `Kala` | `Kāla` | WRONG_SPELLING |
| 20 | `ka_taranga` | kala | `Kala` | `Kāla` | WRONG_SPELLING |

Note `ka_gochara_v3_century_materialize`: its `layer_index` is already `L3` and correct, and it
appears **only** in the C-03 list. A repair that fills NULLs but does not normalise the
diacritics leaves this row wrong. §2.6's detector is built to catch exactly that.

### 2.4 The derivation rule

`layer` is `text NOT NULL` with `CHECK (layer = ANY (ARRAY['brahmagyan','ganita','bodha','kala',
'phala','mimamsa']))` (verbatim in §3.1). It is therefore total and closed over six values, and
the map to the locked external lexicon (CLAUDE.md §N.1) is 1:1:

| `layer` | `layer_index` | `layer_name` |
|---|---|---|
| `brahmagyan` | `L0` | `Brahmagyan` |
| `ganita` | `L1` | `Gaṇita` |
| `bodha` | `L2` | `Bodha` |
| `kala` | `L3` | `Kāla` |
| `phala` | `L4` | `Phala` |
| `mimamsa` | `L5` | `Mīmāṃsā` |

**The input is `layer`, never `layer_index`, never the `asset_id` prefix, never `sort_order`.**
This mirrors D-4's rung-follows-`layer` reasoning and closes the circularity the task names:
M0-T2 derived `rung` from `layer` *because* `layer_index` is untrustworthy; this repair is what
makes `layer_index` trustworthy, and it must not take its input from the column it is repairing.
Judgment-free and total: no row is left NULL by the rule itself.

The one row the rule is **not** applied to is `lel_events` — see §3. That hold is a disposition
decision, not a failure of the rule.

### 2.5 The exact SQL

```sql
-- 0.5a — layer position repair. 20 layer_index rows + 19 layer_name rows.
-- lel_events is EXCLUDED pending the §10.1 SOURCE ruling (see §3).
BEGIN;

UPDATE asset_registry SET layer_index = CASE layer
        WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1' WHEN 'bodha' THEN 'L2'
        WHEN 'kala' THEN 'L3' WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END
WHERE asset_id <> 'lel_events'
  AND layer_index IS DISTINCT FROM (CASE layer
        WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1' WHEN 'bodha' THEN 'L2'
        WHEN 'kala' THEN 'L3' WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END);
-- EXPECTED: UPDATE 20

UPDATE asset_registry SET layer_name = CASE layer
        WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita' WHEN 'bodha' THEN 'Bodha'
        WHEN 'kala' THEN 'Kāla' WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END
WHERE asset_id <> 'lel_events'
  AND layer_name IS DISTINCT FROM (CASE layer
        WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita' WHEN 'bodha' THEN 'Bodha'
        WHEN 'kala' THEN 'Kāla' WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END);
-- EXPECTED: UPDATE 19

COMMIT;
```

The `IS DISTINCT FROM` guard makes both statements idempotent and makes the row count itself an
assertion: a second run must report `UPDATE 0`. A run that reports a number other than 20 / 19
is a signal to stop, not a number to record.

**Encoding hazard, stated because it is the way this specific backfill fails silently.**
`Gaṇita`, `Kāla` and `Mīmāṃsā` carry combining/precomposed diacritics. `Gaṇita` is
`G a U+1E47 i t a`; `Kāla` is `K U+0101 l a`; `Mīmāṃsā` is `M U+012B m U+0101 U+1E43 s U+0101`.
If the SQL is transported through anything that normalises or transliterates, the backfill will
run clean and write the wrong strings — and C-03 will then report a *different* nonzero count
rather than zero, which is the honest failure. §2.6 detector D-4 pins the exact codepoints.

### 2.6 Pre-flight correctness detector (D-4 style)

D-4 condition 3's standard: name specific assets whose correct values are known *independently
of the backfill's own derivation*, so that "the backfill succeeded" is checked against something.

**The independent source used here is the `asset_id` prefix.** CLAUDE.md §N.1 locks
`bg_`→L0 · `ga_`→L1 · `bo_`→L2 · `ka_`→L3 · `ph_`→L4 · `mi_`→L5. The prefix is a *different*
column from `layer` and was written by a different mechanism (the asset's own naming, migration
224), so prefix-derived expectation and `layer`-derived output agreeing is genuine corroboration
rather than a tautology. `CENSUS_REPORT.md §6` measured `layer_contradiction — 0`, i.e. the two
sources already agree on all 127 rows that have a recognised prefix.

Run **before** trusting the backfill, and expect the stated value:

```sql
-- D-1  PREFIX CROSS-CHECK: layer_index derived from the asset_id PREFIX must equal the
--       backfilled value, on all 127 rows with a recognised prefix. EXPECT 0 rows.
SELECT asset_id, left(asset_id,3) AS prefix, layer, layer_index
FROM asset_registry
WHERE left(asset_id,3) IN ('bg_','ga_','bo_','ka_','ph_','mi_')
  AND layer_index IS DISTINCT FROM (CASE left(asset_id,3)
        WHEN 'bg_' THEN 'L0' WHEN 'ga_' THEN 'L1' WHEN 'bo_' THEN 'L2'
        WHEN 'ka_' THEN 'L3' WHEN 'ph_' THEN 'L4' WHEN 'mi_' THEN 'L5' END);

-- D-2  CONTRACT RULES: C-02 and C-03 must both be 0 except for the one held row.
--       EXPECT exactly 1 row each, and that row must be lel_events.
--       (C-02 / C-03 SQL verbatim from ASSET_CATALOGUE_CONTRACT §8.)

-- D-3  NAMED SPOT CHECKS. Each of these is a value known independently; each discriminates a
--       specific WRONG backfill. EXPECT exactly these 6 rows, exactly these values.
SELECT asset_id, layer_index, layer_name FROM asset_registry WHERE asset_id IN
 ('ka_gochara_v3_century_materialize','bg_sign_medical','bo_arudha','ga_vichara','bg_reference','ph_pramana')
ORDER BY asset_id;
```

| asset | must read after | what a wrong value would prove |
|---|---|---|
| `ka_gochara_v3_century_materialize` | `L3` · `Kāla` | `layer_index` was ALREADY `L3`; only `layer_name` changes. If it still reads `Kala`, the backfill filled NULLs only and skipped diacritic normalisation. |
| `bg_sign_medical` | `L0` · `Brahmagyan` | `layer_index` was the bare digit `0`; `layer_name` was already correct. If `layer_index` still reads `0`, the backfill matched on `IS NULL` instead of `IS DISTINCT FROM` and missed all 6 malformed rows. |
| `bo_arudha` | `L2` · `Bodha` | both were NULL. If still NULL, the backfill did not run or its WHERE excluded the null class. |
| `ga_vichara` | `L1` · `Gaṇita` | both were NULL **and** the correct name carries a diacritic. `Ganita` here proves an encoding loss in transport, not a logic error — a distinct failure from the row above. |
| `bg_reference` | `L0` · `Brahmagyan` | was already correct on both. Any change here proves the backfill rewrote conforming rows — the `UPDATE 20 / 19` counts would also be wrong. |
| `ph_pramana` | `L4` · `Phala` | Phala is the only layer with **zero** violations in either class (9/9 rows already conforming). It is the negative control: this row must be untouched. |

```sql
-- D-4  CODEPOINT PIN. The three diacritic spellings must be byte-exact. EXPECT 3 rows,
--       and the three lengths must read 6 / 4 / 7 with the octet lengths shown.
SELECT DISTINCT layer_name, length(layer_name) AS chars, octet_length(layer_name) AS bytes
FROM asset_registry WHERE layer IN ('ganita','kala','mimamsa') ORDER BY 1;
--   Gaṇita   chars=6  bytes=8    (U+1E47 is 3 bytes)
--   Kāla     chars=4  bytes=5    (U+0101 is 2 bytes)
--   Mīmāṃsā  chars=7  bytes=12   (U+012B, U+0101 x2, U+1E43)
-- A row reading chars=bytes for any of these is ASCII-folded and WRONG.
```

D-4 is the detector this backfill would otherwise lack: C-02/C-03 compare against a CASE
expression written in the *same* file as the UPDATE, so an encoding loss that damages both
damages them identically and both read clean. The codepoint pin is checked against a constant
stated here in this document, not against the migration.

---

## §3 — Sub-item 0.5b: `SOURCE` classification of `lel_events`

### 3.1 The blocker — CONFIRMED, not refuted

M0-T2 reported that `asset_kind` has no `'source'` value. That is correct. Verbatim, from
`pg_constraint`:

```sql
SELECT con.conname, pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace ns ON ns.oid = rel.relnamespace
WHERE ns.nspname='public' AND rel.relname='asset_registry' AND con.contype='c'
ORDER BY con.conname;
```
```
 asset_registry_asset_kind_check
   CHECK ((asset_kind = ANY (ARRAY['data'::text, 'service'::text, 'artifact'::text])))
 asset_registry_asset_type_check
   CHECK ((asset_type = ANY (ARRAY['data'::text, 'service'::text])))
 asset_registry_catalog_status_check
   CHECK ((catalog_status = ANY (ARRAY['CURRENT'::text, 'DRAFT'::text, 'RETIRED'::text])))
 asset_registry_layer_check
   CHECK ((layer = ANY (ARRAY['brahmagyan'::text, 'ganita'::text, 'bodha'::text, 'kala'::text, 'phala'::text, 'mimamsa'::text])))
 asset_registry_scope_check
   CHECK ((scope = ANY (ARRAY['global'::text, 'per_chart'::text])))
 asset_registry_service_health_check
   CHECK ((service_health = ANY (ARRAY['healthy'::text, 'degraded'::text, 'unhealthy'::text, 'unknown'::text])))
 asset_registry_storage_type_check
   CHECK ((storage_type = ANY (ARRAY['postgres_table'::text, 'pgvector'::text, 'postgres_view'::text, 'gcs_jsonl'::text, 'bigquery'::text, 'tool_only'::text, 'service'::text])))
```

`asset_registry_asset_kind_check` permits `data`, `service`, `artifact`. It does **not** permit
`source`. An `UPDATE asset_registry SET asset_kind='source' WHERE asset_id='lel_events'` would
be rejected by the constraint — it would fail loudly, not corrupt anything, but it cannot
succeed.

**Therefore: YES, a constraint change is required.** Specifically an
`ALTER TABLE asset_registry DROP CONSTRAINT asset_registry_asset_kind_check` followed by an
`ADD CONSTRAINT ... CHECK (asset_kind = ANY (ARRAY['data','service','artifact','source']))`.

### 3.2 Why this is not mine to make, stated precisely

Two independent gates, and both must open:

1. **Charter P5 — schema changes outside the migrations this plan names.** D-4 read P5's bar as
   "the plan names the migration, not that it numbers one", and found the `domain`/`rung`
   columns named in substance three times including in M0's own acceptance criterion. **The
   `asset_kind` constraint widening does not clear that bar on the same evidence.** M0's
   acceptance criterion names `domain` and `rung`; it does not name `source`, and M0 is
   *achievable* without the constraint change (`lel_events` can remain `asset_kind='data'` and
   be reported as an open disposition). The plan places the reclassification in **R5**
   (§8.4's R5 row: "`lel_events` reclassified `SOURCE`"), not in M0. A change M0 does not need,
   for a rung that is not open, is P5 territory. **This is ADHIKĀRIN's question, and I do not
   answer it.**
2. **Charter G1 — reclassify as `SOURCE`** is an explicitly granted power, but bounded: *"Only
   assets in the current rung."* `CAMPAIGN_STATE.json` has no rung open, and `lel_events` sits
   at R5, the last one. Even with the constraint widened, the reclassification is not available
   under G1 today.

**A KĀRAKA does not widen a CHECK constraint on the strength of a spec paragraph. Nothing in
this sub-item was executed and no migration for it was authored.**

### 3.3 The evidence a ruling would rest on

`lel_events`, verbatim (Q7):

```sql
SELECT asset_id, layer, layer_index, layer_name, asset_kind, asset_type, storage_type,
       catalog_status, is_active, scope, target_table, count_sql IS NOT NULL AS has_count_sql,
       target_floor, has_substeps, depends_on, sort_order,
       health_probe IS NOT NULL AS has_health_probe, provides_apis IS NOT NULL AS has_provides_apis,
       service_health, volume_explanation
FROM asset_registry WHERE asset_id='lel_events';
```
```
 asset_id             = 'lel_events'
 layer                = 'mimamsa'
 layer_index          = None
 layer_name           = None
 asset_kind           = 'data'
 asset_type           = 'data'
 storage_type         = 'postgres_table'
 catalog_status       = 'DRAFT'
 is_active            = True
 scope                = 'per_chart'
 target_table         = None
 has_count_sql        = True
 target_floor         = 0
 has_substeps         = False
 depends_on           = []
 sort_order           = 0
 has_health_probe     = False
 has_provides_apis    = False
 service_health       = None
 volume_explanation   = None
```

Corroborating facts measured this task:

- **No registered writer exists for `lel_events`.** The AST census (§4.1) resolved 123
  `@register(...)` sites across the whole sidecar tree — including four that a literal-only
  scan misses — and `lel_events` is not among them. It is registered as a buildable `data`
  asset that nothing can build, which is the §7 finding verbatim.
- **Nothing depends on it.** `SELECT asset_id FROM asset_registry WHERE 'lel_events' = ANY(depends_on)`
  returned **0 rows**. Retiring or reclassifying it breaks no `depends_on` edge. (This is not
  the same as "no consumer" — MCP/API consumers are the M0-T6 consumer map's job, not this
  query's, and I did not measure them.)
- It carries `target_floor = 0` with `volume_explanation` NULL, i.e. it is *also* a C-21
  violation today. Not repaired here; it is the same disposition question.

### 3.4 The per-asset G1 disposition this raises

**`lel_events` — `layer_index` and `layer_name` HELD NULL, not backfilled.** The mechanical rule
in §2.4 would give it `L5` / `Mīmāṃsā`, and that is what the contract's §5.2 derivation does for
`rung`. But contract §4.2's per-kind matrix marks `layer`, `layer_index`, `layer_name`
**"exempt (outside L0–L5)"** for `source`. So the correct value for these two columns is
*conditional on the unresolved §10.1 ruling*:

| if ADHIKĀRIN rules… | correct `layer_index` / `layer_name` |
|---|---|
| `lel_events` becomes `asset_kind='source'` | **NULL / NULL** — exempt, outside the ladder |
| `lel_events` stays `asset_kind='data'` | `L5` / `Mīmāṃsā` |

A value that is right under one ruling and wrong under the other is not mechanically derivable.
Per D-4 condition 2 and H6 it is left NULL and reported here rather than guessed. This follows
M0-T2's own precedent: it left `data_disposition` NULL on the one RETIRED asset rather than
write the value it thought probable.

**Recommendation, offered as a recommendation and not acted on:** hold. The reclassification is
scheduled for R5 by the plan's own §8.4; doing the constraint change now buys M0 nothing it
needs and spends a P5 ruling early.

---

## §4 — Sub-item 0.6a: `has_substeps`

### 4.0 Why this one is load-bearing

`has_substeps` is not a cockpit label. It is the switch on the §N.8 substep-plan-completeness
gate, and it is read **from the registry**, not from the writer class. `asset_runner.py:616-644`
(the `SELECT has_substeps` is line 620), verbatim from the live source:

```python
            # For writers with a real substep plan (has_substeps=true), require
            # the writer's OWN plan_substeps(ctx) to confirm nothing remains
            # before promoting. has_substeps=false/NULL (light writers, no real
            # plan) skip this check entirely — behaves exactly as before.
            cur.execute(
                "SELECT has_substeps FROM asset_registry WHERE asset_id = %s",
                (asset_id,),
            )
            hs_row = cur.fetchone()
            has_substeps = bool((hs_row or {}).get("has_substeps")) if isinstance(hs_row, dict) else False

            plan_complete = True
            remaining_count = 0
            if has_substeps:
                cur.execute("SAVEPOINT noop_completeness_probe")
                try:
                    remaining = writer.plan_substeps(ctx)
                    ...
```

`plan_complete` is **initialised `True`** and is only ever recomputed inside `if has_substeps:`.
So for an asset whose registry row reads `false` while its writer really plans substeps, the
promotion path is:

> writer reports 0 rows this run → `final_state == 'dormant'` → data rows are present →
> `has_substeps` reads `false` → the `plan_substeps()` re-probe **never runs** →
> `plan_complete` stays at its `True` initialiser → the asset is promoted **`lit`**.

That is the exact defect §N.8 instance 4 was created to close (SATYA-DĪPA's authorized freeze
exception), reopened one column over: the detector exists and is correct, and a wrong metadata
value routes around it. A partial build of any of the 12 assets in §4.3 can be promoted to green
today, and nothing would say so. This is why the sub-item is worth measuring from source rather
than trusting the plan's count.

The same column gates two more surfaces: `platform/src/app/api/cockpit/watchdog/route.ts`
(`has_substeps=true` → `withhold-incomplete`, i.e. the watchdog refuses to reap) and
`platform/src/app/api/cockpit/stats/deriveState.ts:79` (`partial` badge instead of `error`).
Both currently read `false` for the 12 and behave as if the asset had no plan.

### 4.1 How the truth was derived — AST, not regex

`00_ARCHITECTURE/control/writer_substep_census.py` (committed with this proposal, re-runnable,
writes `writer_substep_census.json` beside itself) parses every `.py` under
`platform/python-sidecar` with `ast.parse`, excluding `venv`/`site-packages`/`node_modules`/
`.clone`/`tests`/`__tests__`. **No module is imported and no module-level code is executed** —
which also keeps D-9's `migrate.ts` prohibition satisfied by construction, since nothing is
imported at all.

For every `ClassDef` it records the decorator list, the base classes, the methods defined in the
class body, and the class-level `has_substeps` / `asset_id` assignments. It then resolves each
registered class's inherited method set by walking its bases through the collected class graph.

Result:

```
files_scanned=579 parse_errors=0 registrations=123 distinct_asset_ids=123 dupes=[]
UNRESOLVED @register args: []
HEAVY (plan_substeps+run_substep) n=26
non-standard shapes: {}
unresolved bases: {}
```

**Two traps this hit and had to be fixed, recorded because they are the same class of defect
M0-T1 warned about:**

1. **The first AST pass found only 119 registrations, missing four real writers**, because it
   accepted `@register('literal')` and silently dropped `@register(ASSET_ID)` where `ASSET_ID`
   is a module-level constant. The four missed:
   `ka_kshetra` (`services/ka_kshetra/writer.py:245`),
   `ka_gochara_v3_century_materialize`, `mi_bhara`, `mi_sankalpa`. Two of those four are HEAVY.
   AST alone is not the safeguard — *refusing to silently drop an unresolved decorator argument*
   is. The script now collects module-level string constants, resolves them, and emits any
   still-unresolved `@register` argument in an `UNRESOLVED @register args` list that must be
   empty. It is empty.
2. **Writers live in two trees.** 111 under `pipeline/orchestrator/writers/` and 12 under
   `python-sidecar/services/*/writer.py`. A scan of the `writers/` directory alone misses
   `ka_kshetra`, `ka_muhurta_seva`, `ka_dasha_kala`, `ka_tulana` and eight more.

The rule applied, from the FROZEN contract (`writers/__init__.py`, `WriterBase` docstring):

> • **LIGHT** writer: implement `run(ctx)`.
> • **HEAVY** writer: override **BOTH** `plan_substeps(ctx)` and `run_substep(ctx, step)`.

so `has_substeps := (defines plan_substeps) AND (defines run_substep)`, inherited overrides
counting. Of 123 writers: **26 HEAVY, 97 LIGHT, 0 in any other shape** — no writer defines one
of the pair without the other, so the rule has no ambiguous cases to adjudicate.

### 4.2 The registry-vs-source diff

```
 registry rows                        128
 registered writers (AST)             123
 registry rows with NO writer           5   ['bg_ephemeris_engine', 'bg_gochara_citation_resolution', 'bg_panchanga', 'bg_sarvatobhadra_grid', 'lel_events']
 writers with no registry row           0
 HEAVY writers (source truth)          26
 registry has_substeps = true          14
 AGREE true                            14
 AGREE false                           97
 FALSE NEGATIVES (reg false, HEAVY)    12
 FALSE POSITIVES (reg true, LIGHT)      0
```

**The plan's two extra assets, refuted from source:**

| plan claims false-negative | `plan_substeps`? | `run_substep`? | `run`? | class attr `has_substeps` | verdict |
|---|---|---|---|---|---|
| `bg_reference` (`writers/bg_reference.py:19`, class `ReferenceWriter`) | no | no | **yes** (L22) | not set | **LIGHT — plan is wrong.** The file is 51 lines and `grep -n 'plan_substeps\|run_substep\|SubStep'` returns nothing. |
| `bo_laksana_rerank` (`writers/bo_laksana.py:3402`, class `BoLaksanaRerankWriter`) | no | no | **yes** (L3408) | not set | **LIGHT — plan is wrong.** Its docstring: *"UPDATE-only; never deletes or re-inserts `bodha_msr_signals` rows."* |

`bo_laksana_rerank` is almost certainly a file-granularity artefact: `bo_laksana.py` contains
**two** registered classes — `BoLaksanaWriter` at L2975, which *is* HEAVY, and
`BoLaksanaRerankWriter` at L3402, which is not. A finding attributed per-file tags both. This is
the same shape as M0-T1's regex counting docstring mentions, and it is what §4.4's detector D-1
is built to catch.

### 4.3 The 12 false negatives, with the source that proves each

| # | asset_id | layer | kind | status | writer class | file:line | class attr `has_substeps` |
|--:|---|---|---|---|---|---|---|
| 1 | `bg_muhurta_lattice` | brahmagyan | data | CURRENT | `BgMuhurtaLatticeWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py:530` | `True` |
| 2 | `bo_laksana` | bodha | data | CURRENT | `BoLaksanaWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:2975` | `True` |
| 3 | `bo_samskara` | bodha | data | CURRENT | `BoSamskaraWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_samskara.py:190` | `True` |
| 4 | `ga_ayurdaya` | ganita | data | CURRENT | `GaAyurdayaWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_ayurdaya.py:22` | `True` |
| 5 | `ga_nakshatra` | ganita | data | CURRENT | `NakshatraWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py:389` | `True` |
| 6 | `ga_sensitive` | ganita | data | CURRENT | `GaSensitiveWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_sensitive.py:14` | `True` |
| 7 | `ga_sensitive_degree` | ganita | data | CURRENT | `GaSensitiveDegreeWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_sensitive_degree.py:22` | `True` |
| 8 | `ga_structural` | ganita | data | CURRENT | `GaStructuralWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py:12` | `True` |
| 9 | `ka_sangam` | kala | artifact | DRAFT | `KaSangamWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py:225` | `True` |
| 10 | `mi_darshana` | mimamsa | data | DRAFT | `MiDarshanaWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:170` | `True` |
| 11 | `mi_pariksha` | mimamsa | data | DRAFT | `MiParikshaWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py:91` | `True` |
| 12 | `mi_pramana` | mimamsa | data | DRAFT | `MiPramanaWriter` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py:250` | `True` |

All 12 are proposed `has_substeps = true`.

**Eight of the twelve are `CURRENT`** — `bg_muhurta_lattice`, `bo_laksana`, `bo_samskara`,
`ga_ayurdaya`, `ga_nakshatra`, `ga_sensitive`, `ga_sensitive_degree`, `ga_structural`. The other
four (`ka_sangam`, `mi_darshana`, `mi_pariksha`, `mi_pramana`) are `DRAFT`. The eight CURRENT
ones are the live exposure: those are assets a real build can promote to `lit` past a gate that
never ran.

**Zero false positives.** Every registry row that reads `true` has a HEAVY writer behind it,
including the two whose registration a literal-only scan would have missed
(`ka_kshetra`, `ka_gochara_v3_century_materialize`) and the RETIRED `ka_gochara_sweep`.

### 4.4 The derivation rule

```
has_substeps := TRUE  iff the @register'd writer class for that asset_id defines (or inherits
                      from a non-WriterBase ancestor) BOTH plan_substeps AND run_substep
                FALSE iff it defines run(ctx) and not that pair
                NOT DERIVABLE iff no @register'd writer exists for the asset_id
```

The column is `boolean NOT NULL DEFAULT false`, so "not derivable" cannot be expressed as NULL
in the schema as it stands. See §4.7 for the five assets this affects and the disposition it
raises.

### 4.5 The exact SQL

The values are not derivable *in SQL* — the truth source is the Python AST — so the repair is a
literal VALUES list, not a CASE expression. That is deliberate: an explicit list is auditable
row by row, and it cannot quietly widen if the writer tree changes between authoring and
application.

```sql
-- 0.6a — has_substeps repair. 12 rows, all false -> true.
-- Truth source: AST census of @register'd WriterBase subclasses, 2026-08-23.
-- Each asset listed here defines BOTH plan_substeps and run_substep (FROZEN contract,
-- CLAUDE.md §N.2). Verified against each class's own has_substeps class attribute: 12/12 agree.
BEGIN;

UPDATE asset_registry SET has_substeps = true
WHERE asset_id IN (
  'bg_muhurta_lattice',   -- writers/bg_muhurta_lattice.py:530  BgMuhurtaLatticeWriter
  'bo_laksana',           -- writers/bo_laksana.py:2975         BoLaksanaWriter
  'bo_samskara',          -- writers/bo_samskara.py:190         BoSamskaraWriter
  'ga_ayurdaya',          -- writers/ga_ayurdaya.py:22          GaAyurdayaWriter
  'ga_nakshatra',         -- writers/ga_nakshatra.py:389        NakshatraWriter
  'ga_sensitive',         -- writers/ga_sensitive.py:14         GaSensitiveWriter
  'ga_sensitive_degree',  -- writers/ga_sensitive_degree.py:22  GaSensitiveDegreeWriter
  'ga_structural',        -- writers/ga_structural.py:12        GaStructuralWriter
  'ka_sangam',            -- writers/ka_sangam.py:225           KaSangamWriter
  'mi_darshana',          -- writers/mi_darshana.py:170         MiDarshanaWriter
  'mi_pariksha',          -- writers/mi_pariksha.py:91          MiParikshaWriter
  'mi_pramana'            -- writers/mi_pramana.py:250          MiPramanaWriter
) AND has_substeps IS DISTINCT FROM true;
-- EXPECTED: UPDATE 12

-- NOTE: bo_laksana_rerank and bg_reference are DELIBERATELY ABSENT. The plan lists them;
-- their source refutes it (§4.2). Adding them would disable no gate but would make the
-- registry claim a substep plan that plan_substeps() cannot deliver, and the orchestrator
-- would then re-probe a writer that returns its single default SubStep — turning every
-- no-op completion for those two assets into a permanent 'dormant'. Wrong in the other
-- direction, and worse.

COMMIT;
```

### 4.6 Pre-flight correctness detector (D-4 style)

The strongest available check is that **two independent signals in the same source tree agree
123/123**: the method-override truth (what the class implements) and the class-level
`has_substeps` attribute (what the class *declares*). They are written in different places by
different conventions and neither is derived from the other.

```
LIGHT writers with class_attr has_substeps=True:  []      <- must be empty
HEAVY writers with class_attr has_substeps=True:  26/26   <- must be total
```

If those two ever disagree, the census is wrong and the backfill must not run — that is the
detector, and it is re-runnable by re-executing the census script.

**Named discriminating assets — each catches a specific wrong backfill:**

| asset | must read after | what a wrong value would prove |
|---|---|---|
| `bo_laksana` | **true** | flipped by this repair. The primary case. |
| `bo_laksana_rerank` | **false** | *the killer test.* Both classes live in **the same file**, `writers/bo_laksana.py`. A file-granularity backfill flips both. If this reads `true`, the repair was file-scoped, not class-scoped, and every other value it wrote is suspect. |
| `ka_kshetra` | **true** (unchanged) | registers via `@register(ASSET_ID)`, a module constant, in `services/ka_kshetra/writer.py` — **outside** the `writers/` tree. A backfill built on a literal-only scan of `writers/` sees "no writer" here. If this reads `false`, the census under it missed two trees and one decorator form. |
| `ka_gochara_v3_century_materialize` | **true** (unchanged) | same module-constant form, inside `writers/`. Discriminates the decorator-form bug from the directory bug. |
| `bg_reference` | **false** (unchanged) | the plan says flip it; the source says do not. If it reads `true`, the backfill was driven from the plan document rather than from the writer tree — which is the H6 shape, a figure taken from a document standing in for a measurement. |
| `ga_dashas` | **true** (unchanged) | the canonical heavy writer, named in the FROZEN-contract docstring itself ("ga_dashas: ~40 min, 35 chunks"). Negative control on the already-correct set. |
| `mi_bhara`, `mi_sankalpa` | **false** (unchanged) | the other two module-constant registrations; both LIGHT. Catches a backfill that resolved the decorator form but then set every newly-discovered writer to `true`. |

```sql
-- D-1  EXPECT exactly these 8 rows, exactly these values.
SELECT asset_id, has_substeps FROM asset_registry WHERE asset_id IN
 ('bo_laksana','bo_laksana_rerank','ka_kshetra','ka_gochara_v3_century_materialize',
  'bg_reference','ga_dashas','mi_bhara','mi_sankalpa') ORDER BY asset_id;
--  bg_reference                       f
--  bo_laksana                         t
--  bo_laksana_rerank                  f     <- file-granularity trap
--  ga_dashas                          t
--  ka_gochara_v3_century_materialize  t     <- module-const trap (inside writers/)
--  ka_kshetra                         t     <- module-const trap (services/ tree)
--  mi_bhara                           f
--  mi_sankalpa                        f

-- D-2  TOTALS. EXPECT true=26, false=102.
SELECT has_substeps, count(*) FROM asset_registry GROUP BY 1 ORDER BY 1;
--  before: f=114  t=14
--  after:  f=102  t=26

-- D-3  RE-RUN THE CENSUS AND DIFF. The only honest full check: re-run
--      writer_ast_census.py and assert every asset_id's registry value equals
--      writer_truth_has_substeps, for all 123 assets that have a writer.
--      EXPECT: 0 disagreements. This is a script, not a SQL query, and it is
--      the one that would actually catch an error the named cases miss.
```

### 4.7 Not mechanically derivable — per-asset G1 dispositions

Five registry rows have **no** `@register`'d writer, so `has_substeps` has no writer class to be
derived from. All five currently read `false`, and the column is `NOT NULL` so NULL is not
available as the honest value:

| asset_id | kind | status | active | why there is no writer | proposed |
|---|---|---|---|---|---|
| `bg_ephemeris_engine` | data | CURRENT | True | service asset — routes to the legacy `health_probe` path, not a writer (§5) | leave `false`, flag |
| `bg_gochara_citation_resolution` | data | CURRENT | True | **CURRENT with no writer** — the v3.0 §3.6 finding, unresolved | leave `false`, flag |
| `bg_panchanga` | data | CURRENT | True | service asset — same (§5) | leave `false`, flag |
| `bg_sarvatobhadra_grid` | data | CURRENT | True | **CURRENT with no writer** — same class, not previously named | leave `false`, flag |
| `lel_events` | data | DRAFT | True | ingested SOURCE candidate — nothing builds it (§3) | leave `false`, flag |

**Proposal: leave all five at `false` and change nothing, but do not read that `false` as
derived.** For the three that are service/source-shaped, contract §4.8 independently requires
`false`, so the value is right for a reason that does not depend on a writer census — that is a
sound `false`, not an unearned one.

For `bg_gochara_citation_resolution` and `bg_sarvatobhadra_grid` the `false` is **unearned**:
they are `CURRENT`, `is_active`, `asset_kind='data'`, they name a real `target_table`, and
nothing can build them. Their `has_substeps` is not "false", it is "undefined", and the schema
cannot say so. **G1 disposition for ADHIKĀRIN:** these are the §7 "never leave a CURRENT asset
that nothing can build" class. `bg_gochara_citation_resolution` is already named in v3.0 §3.6;
**`bg_sarvatobhadra_grid` appears not to be, and is surfaced here as a new instance of the same
class** (it also carries `target_floor = 0` with `volume_explanation` NULL, so it is a C-21
violation as well). Both are R0 assets and no rung is open. Not touched. Reported.

---

## §5 — Sub-item 0.6b: kind reconciliation

### 5.1 The measurement

All (`asset_kind`, `asset_type`, `storage_type`) triples present in the table (Q9):

```sql
SELECT asset_kind, asset_type, storage_type, count(*) AS n
FROM asset_registry GROUP BY 1,2,3 ORDER BY 1,2,3;
```
```
 asset_kind | asset_type | storage_type    | n
 artifact  | data       | postgres_table  | 16
 data      | data       | pgvector        | 4
 data      | data       | postgres_table  | 99
 data      | data       | postgres_view   | 1
 data      | service    | service         | 2
 service   | data       | service         | 4
 service   | service    | service         | 2
```

Five of the seven triples are coherent under contract C-14's permitted pairs. Two are not, and
they account for the six disagreeing rows: `(data, service, service)` ×2 and
`(service, data, service)` ×4.

### 5.2 The six disagreements, enumerated

C-14 SQL verbatim from contract §8, with the deciding evidence columns joined on:

```sql
SELECT asset_id, layer, asset_kind, asset_type, storage_type, catalog_status,
       target_table, count_sql IS NOT NULL AS has_count_sql, target_floor,
       health_probe IS NOT NULL AS has_health_probe,
       provides_apis IS NOT NULL AS has_provides_apis, service_health
FROM asset_registry
WHERE (asset_kind, asset_type) NOT IN
      (('data','data'), ('artifact','data'), ('service','service'), ('source','data'))
ORDER BY asset_id;
```

Verbatim result — **6 rows**:

| asset_id | kind | type | storage | status | target_table | count_sql | floor | probe | apis | service_health |
|---|---|---|---|---|---|---|---|---|---|---|
| `bg_ephemeris_engine` | data | service | service | CURRENT | — | no | — | yes | yes | — |
| `bg_panchanga` | data | service | service | CURRENT | — | no | — | yes | yes | — |
| `ka_graha_sancara` | service | data | service | DRAFT | — | no | — | no | no | unhealthy |
| `ka_muhurta_seva` | service | data | service | DRAFT | — | no | — | no | no | healthy |
| `mi_abhilekha` | service | data | service | DRAFT | mimamsa_journal | yes | 0 | no | no | — |
| `mi_seva` | service | data | service | DRAFT | mimamsa_preferences | yes | 0 | no | no | — |

### 5.3 Per-asset: which value the evidence supports, and why

**All six resolve to `service`.** But they do *not* all resolve by "`asset_kind` is
authoritative" — two of them have the wrong `asset_kind`, and applying that principle blindly
would corrupt them. This is the sub-item's real content.

#### `bg_ephemeris_engine` — evidence says **service**; `asset_kind='data'` is the wrong value

- `storage_type = 'service'`, `health_probe` NOT NULL, `provides_apis` NOT NULL — the three
  fields contract §4.10 marks REQUIRED-for-service and MUST-BE-NULL-for-every-other-kind are
  all populated. On the contract's own matrix this row cannot be `data`.
- `target_table` NULL, `count_sql` NULL, `target_floor` NULL — every field §4.5/§4.6 require of
  a `data` asset is absent. It is C-04 and C-05's violation precisely *because* it is
  misclassified.
- **No `@register`'d writer exists** (AST census, §4.1). A `data` asset with no writer cannot be
  built; a `service` asset with a `health_probe` does not need one. `asset_runner.py:917,926-928`
  routes exactly this shape to the legacy `_run_service_health_probe(...,
  registry_row.get("health_probe"))` path.
- **Proposed:** `asset_kind := 'service'` (change), `asset_type := 'service'` (already),
  `storage_type := 'service'` (already).

#### `bg_panchanga` — identical shape, identical reasoning

Same six indicators, same verdict. **Proposed:** `asset_kind := 'service'`.

#### `ka_graha_sancara` — evidence says **service**; `asset_type='data'` is the wrong value

- `storage_type='service'`; `target_table`, `count_sql`, `target_floor` all NULL.
- It **has** a registered writer (`writers/ka_graha_sancara.py:48`, `KaGrahaSancaraWriter`,
  LIGHT) — and the orchestrator names this asset explicitly as the intended shape:
  > `asset_runner.py:918-921` — *"Service assets with a registered WriterBase writer (e.g.
  > `ka_graha_sancara`, `ka_muhurta_seva`) use the writer's `run()` for their self-test — they
  > are 'service writers', not legacy health-probe-spec services."*
  The orchestrator, in a comment naming this asset, treats it as a service. That is stronger
  evidence than either column.
- **Proposed:** `asset_type := 'service'` (change), `asset_kind` stays `'service'`.
- *Carried note, not repaired here:* it holds `service_health='unhealthy'` with `health_probe`
  NULL — contract C-17. That is a §N.8/H4 issue about a status with no detector; it is a
  separate item and I did not touch it.

#### `ka_muhurta_seva` — same; named in the same orchestrator comment

Writer at `services/ka_muhurta_seva/writer.py:73` (LIGHT). **Proposed:** `asset_type := 'service'`.
- *Carried note:* `service_health='healthy'` with `health_probe` NULL — C-17, and charter **H4**
  in its most literal form: a green health status that no probe produced. Flagged, not fixed.

#### `mi_abhilekha` — evidence says **service**; `asset_type='data'` is the wrong value

- Its writer's own docstring settles it (`writers/mi_abhilekha.py:1-14`), verbatim:
  > *"Service handler: re-syncs prediction outcomes … **This writer creates NO build-time rows.**
  > It registers as an asset so the orchestrator can verify its readiness state and count
  > journal entries. GLOBAL scope (service handler)."*
- `storage_type='service'`.
- **Proposed:** `asset_type := 'service'`.
- *Contradicting evidence, stated rather than suppressed:* it carries `target_table =
  'mimamsa_journal'`, a non-null `count_sql`, and `target_floor = 0` — fields contract §4.5/§4.6
  say a service MUST NOT have, and it is one of C-07's four live violations. The writer
  docstring resolves the contradiction: `mimamsa_journal` is a table it **reads and counts**,
  not one it builds. The registry borrowed the data-asset fields to make the row countable. So
  the kind is `service` and the three data fields are a *separate* C-07 repair. **This proposal
  does not null them** — that is the C-07 item's call, and nulling `count_sql` would blank the
  cockpit row for this asset as a side effect of a kind repair.

#### `mi_seva` — same shape, same docstring pattern

`writers/mi_seva.py:1-13`, verbatim: *"Service handler: applies calibration overlays at serve
time … **This writer creates NO build-time rows.** It is invoked by the retrieval layer at serve
time, not by the orchestrator build. GLOBAL scope (service handler — no DELETE/INSERT at build
time)."* Its `run()` body only checks `information_schema` for four tables' existence.
**Proposed:** `asset_type := 'service'`. Same C-07 carve-out as above (`target_table =
'mimamsa_preferences'`).

### 5.4 The derivation rule, and the honest limit on it

Two rules were available. Both give the same answer on all six rows, and the difference between
them matters.

**Rule A (mechanical, weak on its own): majority of the three classification columns.**
Every one of the six has `storage_type='service'`; three-column majority therefore returns
`service` in all six cases. `storage_type='service'` selects exactly 8 rows and is a superset of
both `asset_kind='service'` (6) and `asset_type='service'` (4) — it is the only one of the three
columns that disagrees with no one. But majority-of-three is a voting rule, not an authority
argument: three columns that were all copied from one bad source would vote unanimously and be
unanimously wrong. It is used here only as a *cross-check*.

**Rule B (the one actually relied on): the asset's own artefacts.**
For each row, the writer source (or its absence), the writer's docstring, the orchestrator's
routing code, and the populated/absent field pattern. This is what §5.3 argues from, per asset.
It is not a single SQL expression, which is why §5.5's SQL is an explicit list.

Rules A and B agree 6/6. That agreement is the finding; neither alone would be enough.

**On "`asset_kind` becomes authoritative":** as a *going-forward* rule it is right, and it is
what the plan (§1162) and contract §1 specify. As a *repair* rule it is wrong for two of the six
rows — `bg_ephemeris_engine` and `bg_panchanga` have the wrong `asset_kind` today. Making
`asset_kind` authoritative **first** and then repairing from it would write `data` over a
correct `service` in both. **Order matters: repair the values, then make the column
authoritative.** Stated because this is the kind of ordering error that reads as correct in a
plan and is destructive in execution.

### 5.5 The exact SQL

```sql
-- 0.6b — kind reconciliation. 6 rows. Post-condition: C-14 returns 0 and all 8
-- storage_type='service' rows read asset_kind='service' AND asset_type='service'.
BEGIN;

-- (a) asset_kind repair — 2 rows whose asset_kind is the WRONG one of the three.
--     Evidence per asset: §5.3. Both have health_probe + provides_apis NOT NULL,
--     target_table/count_sql/target_floor NULL, and NO registered writer.
UPDATE asset_registry SET asset_kind = 'service'
WHERE asset_id IN ('bg_ephemeris_engine','bg_panchanga')
  AND asset_kind IS DISTINCT FROM 'service';
-- EXPECTED: UPDATE 2

-- (b) asset_type repair — 4 rows whose legacy asset_type disagrees with a correct asset_kind.
UPDATE asset_registry SET asset_type = 'service'
WHERE asset_id IN ('ka_graha_sancara','ka_muhurta_seva','mi_abhilekha','mi_seva')
  AND asset_type IS DISTINCT FROM 'service';
-- EXPECTED: UPDATE 4

-- storage_type: NO CHANGE. All 6 already read 'service'; all 8 service-shaped rows do.

COMMIT;
```

**Behaviour-preservation note, because a kind change that silently re-routes a build would be
the worse defect.** Both live consumers read the two columns as an OR, so all six rows are
*already* treated as services today:

- `asset_runner.py:884-885` — `is_service = (asset_kind == 'service' or asset_type == 'service')`
- `deriveState.ts:66` — `if (asset.asset_type === 'service' || asset.asset_kind === 'service') return 'service_ok'`

For the four `(service, data, …)` rows the `asset_kind` limb is already true; for the two
`(data, service, …)` rows the `asset_type` limb is. Setting both columns to `'service'` leaves
every one of those six branches evaluating exactly as it does now, and removes the dependence on
the OR — which is what lets the OR be narrowed to `asset_kind` alone later without a behaviour
change. **This repair is a no-op at runtime today and a prerequisite for the collapse.**

### 5.6 Pre-flight correctness detector (D-4 style)

```sql
-- D-1  C-14 must return 0 rows (contract §8 SQL verbatim).

-- D-2  THE THREE-COLUMN CLOSURE. EXPECT exactly 8 rows, all three columns 'service'.
SELECT asset_id, asset_kind, asset_type, storage_type FROM asset_registry
WHERE 'service' IN (asset_kind, asset_type, storage_type) ORDER BY asset_id;
--  bg_ephemeris_engine  service service service
--  bg_panchanga         service service service
--  ka_dasha_kala        service service service
--  ka_graha_sancara     service service service
--  ka_muhurta_seva      service service service
--  ka_tulana            service service service
--  mi_abhilekha         service service service
--  mi_seva              service service service
-- A 9th row means the repair widened past its six.

-- D-3  NAMED DISCRIMINATING ASSETS. EXPECT exactly these values.
SELECT asset_id, asset_kind, asset_type FROM asset_registry WHERE asset_id IN
 ('bg_ephemeris_engine','ka_graha_sancara','bo_cdlm_summary','ka_sangam','ph_pramana','lel_events')
ORDER BY asset_id;
```

| asset | must read after | what a wrong value would prove |
|---|---|---|
| `bg_ephemeris_engine` | `service` / `service` | *the key case.* If it reads `data`/`data`, the repair applied "asset_kind is authoritative" as a repair rule and overwrote the correct `asset_type='service'` with the wrong `asset_kind='data'` (§5.4). This single row distinguishes a correct repair from the plausible wrong one. |
| `ka_graha_sancara` | `service` / `service` | the mirror case — here `asset_kind` *was* right. If it reads `data`/`data`, the repair ran the other direction and made `asset_type` authoritative instead. Together these two rows pin the direction per asset rather than globally. |
| `bo_cdlm_summary` | `data` / `data` | untouched control from the largest cohort (99 rows). |
| `ka_sangam` | `artifact` / `data` | *the artifact trap.* 16 rows carry `asset_kind='artifact'` with `asset_type='data'` — a **permitted** pair. A "collapse to one authoritative kind" that normalised `asset_type` onto `asset_kind` would write `artifact` into `asset_type`, violating `asset_registry_asset_type_check` (which permits only `data\|service`) — it would fail loudly. A collapse in the other direction would write `data` over `artifact` and silently destroy the artifact classification on 16 rows. Either way this row detects it. |
| `ph_pramana` | `artifact` / `data` | second artifact control, different layer. |
| `lel_events` | `data` / `data` | must be **untouched** by 0.6b. Its reclassification is §3's blocked question; if this row changed, 0.6b reached into 0.5b's territory. |

```sql
-- D-4  TOTALS. EXPECT: data=104, artifact=16, service=8  (from data=106/artifact=16/service=6).
SELECT asset_kind, count(*) FROM asset_registry GROUP BY 1 ORDER BY 1;
SELECT asset_type, count(*) FROM asset_registry GROUP BY 1 ORDER BY 1;
-- asset_type EXPECT: data=120, service=8  (from data=124/service=4)
```

---

## §6 — Everything left NULL / unrepaired, as per-asset G1 dispositions

Per D-4 condition 2 and H6: a value that is not mechanically derivable is left alone and
reported, never guessed.

| # | asset_id | field(s) | why not derivable | ADHIKĀRIN power |
|--:|---|---|---|---|
| 1 | `lel_events` | `layer_index`, `layer_name` | correct value is NULL-if-`source`, `L5`/`Mīmāṃsā`-if-`data`; the §10.1 ruling decides which (§3.4) | G1 (blocked on P5 constraint question) |
| 2 | `lel_events` | `asset_kind` → `source` | CHECK constraint forbids the value; widening it is a schema change M0 does not require and the plan schedules for R5 (§3.2) | **P5 — park** |
| 3 | `bg_gochara_citation_resolution` | `has_substeps` (and its buildability) | CURRENT + active + `target_table` set + **no writer**. `false` is the schema default, not a measurement (§4.7) | G1 |
| 4 | `bg_sarvatobhadra_grid` | `has_substeps` (and its buildability) | same class, **not previously named in v3.0 §3.6** — new instance surfaced here. Also `target_floor=0` with no `volume_explanation` (C-21) | G1 |
| 5 | `mi_abhilekha`, `mi_seva` | `target_table`, `count_sql`, `target_floor` | service rows carrying data-asset fields (C-07). Nulling them is right by the contract and would blank their cockpit counts; that trade is a decision, not a derivation (§5.3) | G1 |
| 6 | `ka_muhurta_seva` | `service_health='healthy'` with `health_probe` NULL | a green status with no detector — charter **H4** and C-17. Not repairable by this task; the honest value is `unknown` or NULL and setting it is a status write | G1 / H4 |
| 7 | `ka_graha_sancara` | `service_health='unhealthy'` with `health_probe` NULL | same defect class, opposite colour | G1 / H4 |

Items 5–7 are outside 0.5/0.6 and are recorded here only because this task's queries surfaced
them; they are also written to `mailbox/to_conductor/` as findings and are **not** fixed.

---

## §7 — What was NOT done

- **No write of any kind was executed.** The measurement session ran with
  `SET default_transaction_read_only = on`. No UPDATE, no DDL, no `ALTER`, no migration applied.
- **No migration file was authored to disk** (§0, reason stated).
- **Nothing was imported from `platform/scripts/migrate.ts`** (D-9) **or from
  `asset_registry_seed.ts`.** The seed file was not read, parsed or executed by this task at all
  — the truth sources used were the live database and `ast.parse` over the writer tree.
- **The `asset_kind` CHECK constraint was not changed** and no attempt to write
  `asset_kind='source'` was made.
- **No consumer map was computed.** §3.3's "nothing depends on it" is a `depends_on` statement
  only; MCP/API/retrieval consumers are M0-T6's measurement and I did not duplicate it.
- **C-07, C-17, C-21 violations were not repaired**, only reported.
- **`writer_timeout_seconds`, `estimated_seconds`, `integrity_check_sql`** were not touched;
  they are other M0 items.
- **DATABASE_URL was never printed, echoed, logged or committed** (P4). It was read from
  `platform/.env.local` inside the script exactly as `measure_assets.py` does.
- **This document certifies nothing** (I16/H7). The counts are observations; whether the
  proposed repair is correct is PARĪKṢAKA's finding and whether it may be applied is
  ADHIKĀRIN's ruling.

## §8 — Uncertainties, stated plainly

1. **The AST census resolves `@register(NAME)` only for module-level string constants.** It
   reports any unresolved decorator argument and currently reports none, so there is no *known*
   gap — but a registration built from, say, an f-string or a dict lookup would be surfaced as
   unresolved rather than resolved, and someone would have to extend the resolver. I would rather
   it fail loudly there than guess.
2. **Base-class resolution matches by simple class name**, preferring a same-module candidate.
   No writer in this tree has an ambiguous base (`unresolved bases: {}`, and no non-`WriterBase`
   ancestor defines `plan_substeps`/`run_substep`), so it did not matter here. It would matter
   in a tree with two same-named base classes.
3. **`bo_laksana_rerank` and `bg_reference`:** I am confident from source that both are LIGHT.
   I am *not* certain why the plan lists them; the same-file hypothesis explains
   `bo_laksana_rerank` well and does not explain `bg_reference` at all. If the plan's list came
   from a source I have not found, that source and this measurement disagree and someone should
   say which is right before the backfill runs.
4. **The two `mi_*` service assets' `count_sql`** — I concluded from the writer docstrings that
   their `target_table` is read, not built. I did not run their `count_sql` and did not verify
   that no other writer builds those tables. A co-writer census (contract §4.9) would settle it;
   there is no column for it.
5. **`bg_sarvatobhadra_grid`.** I searched for a writer by `@register` only. It is possible it
   is built by something outside the writer contract entirely (a script, a migration seed). I
   found none, but "I did not find one" is a weaker claim than "there is none."
6. **The layer-position repair is stated as 20 + 19 rows.** That count is correct only if
   `lel_events` is held back. If ADHIKĀRIN rules that it stays `data`, the counts become 21 + 20
   and the detector's "expect exactly 1 remaining C-02/C-03 row" flips to "expect 0". The SQL
   would need its `asset_id <> 'lel_events'` guard removed — which is an edit, and if the
   migration has been applied by then, H5 forbids editing it. **Get the ruling before writing
   the file, not after.**
