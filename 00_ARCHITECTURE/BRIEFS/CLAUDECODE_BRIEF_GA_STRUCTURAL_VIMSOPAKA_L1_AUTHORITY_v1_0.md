# ga_structural — vimsopaka + saptavargaja L1-authority fix (last pre-L2 item) — paste into Claude Code

**Read CLAUDE.md §C first + memory `feedback-ga-structural-rebuild-locked-logic`.** ga_structural v2.0 is
sealed (build a712b250, 106,103 rows, 72 categories, all designed categories populated-or-documented). This is
the LAST pre-L2 item: two categories still use a WEAK logical `join_key` reference instead of a resolvable
`fact_value_jsonb.constituent_fact_ids` pointing at real fact_ids — violating L1-authority §N.5 (L2 must be able
to RESOLVE every reference, not parse a string and re-join). Fix both, rebuild, verify, then L2 Bodha can open.

## STANDING RAILS
L1-authority §N.5 (every reference is a resolvable fact_id in `fact_value_jsonb.constituent_fact_ids`; the
column `constituent_facts_array` does NOT exist — `_CF_INSERT_COLS` excludes it, confirmed L5268); the correct
helper already exists — `_get_constituent_fact_ids` (L1434) builds real fact_id lists from GA3-GA7; FROZEN
orchestrator contract (HALT if change seems needed); per-chart delete-then-insert; floor = ACHIEVED (recalibrate
after); verify by resolving the new refs via live JOIN; only 482012f1; FORENSIC 7/7.

---

## THE FINDING (code-verified)

TWO categories use the weak `join_key` pattern (not just vimsopaka — its twin must be fixed too, or we leave an
identical hole):

1. **`vimsopaka_bala_per_graha`** — `_build_vimsopaka_ext_rows` (L1381), value_jsonb at L1402-1404:
   ```python
   "source_table": "chart_divisionals",
   "source_category": "varga_vimsopaka_contribution",
   "join_key": f"chart_id={chart_id},ayanamsha_id={ayanamsha_id},graha={subject}",
   ```
2. **`graha_saptavargaja_bala_component`** — same file ~L1185-1187, IDENTICAL pattern:
   ```python
   "source_table": "chart_divisionals",
   "source_category": "varga_saptavargaja_bala_component",
   "join_key": f"chart_id={chart_id},ayanamsha_id={ayanamsha_id},graha={subject}",
   ```

Both store a stringified join key, NOT a resolvable fact_id. L2 would have to PARSE the string and re-run a join
— fragile, and not the L1-authority guarantee (a stored fact_id that resolves with a single PK lookup).

---

## THE FIX

For BOTH builders, replace the `join_key` string with real `constituent_fact_ids`:
1. Query `chart_facts` for the actual GA-written contribution rows this summary aggregates —
   `varga_vimsopaka_contribution` (for vimsopaka) and `varga_saptavargaja_bala_component` (for saptavargaja) —
   for `(chart_id, ayanamsha_id, graha=subject)`, collecting their real `fact_id` values. Use/extend
   `_get_constituent_fact_ids` (L1434, the existing correct helper) rather than writing a new path.
2. Store the collected fact_ids in `fact_value_jsonb["constituent_fact_ids"]` (the canonical resolvable
   location). KEEP the human-readable `source_category`/`note` for context, but the AUTHORITATIVE reference is
   the fact_id list. REMOVE reliance on the `join_key` string as the reference mechanism (it can stay as a
   debug breadcrumb in the note, but it is not the reference).
3. If the underlying `varga_vimsopaka_contribution` / `varga_saptavargaja_bala_component` rows are NOT in
   chart_facts (GA6 may write them to `chart_divisionals` only) — then CONFIRM where they live. If they're in
   `chart_divisionals` (a different table than chart_facts), the fact_id reference must point at the
   resolvable row identifier in THAT table (chart_divisionals row id), and the verify must show that id
   resolves. If the source genuinely has no per-row resolvable id, HALT and flag — that's a deeper GA6 schema
   question, not a one-line fix. (State which case it is.)

---

## VERIFY (resolve the new refs — don't just assert)
- Both categories rebuilt; `fact_value_jsonb.constituent_fact_ids` now populated for every row.
- **⭐ Resolution proof:** sample a `vimsopaka_bala_per_graha` row and a `graha_saptavargaja_bala_component`
  row; take each `constituent_fact_ids[i]` and JOIN it to the source table (chart_facts or chart_divisionals)
  — confirm it RESOLVES to the real contribution row. Paste the join result. Zero unresolvable refs, zero
  `join_key`-as-sole-reference rows remaining.
- Grep the writer: NO remaining `"join_key":` used as the authoritative reference for any category (confirm
  vimsopaka + saptavargaja were the only two; if a third exists, fix it too — close the class).
- per-category counts unchanged (this is a reference-shape fix, not a row-count change); floor recalibrate only
  if counts shift; FORENSIC 7/7; FROZEN contract untouched; migration for any floor/count_sql touch
  ledger-reconciled.
- Update GA_STRUCTURAL_REBUILD_VERIFY (v2.1 addendum) noting both categories now L1-authority-clean.

**This is the final pre-L2 gate item. When both categories resolve via real fact_ids and zero `join_key`-only
references remain, ga_structural v2.0 is FULLY L1-authority-clean and L2 Bodha can open on the complete,
correct, single-source, fully-resolvable hub.**
