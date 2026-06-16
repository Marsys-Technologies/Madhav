---
artifact: CLAUDECODE_BRIEF_PRE_GA8_CLOSURE_v1_0.md
canonical_id: PRE_GA8_CLOSURE_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
purpose: Close 3 cheap, independent loose ends BEFORE the big GA8+ga_strength completeness amendment, so the rebuild lands on clean ground.
data_plane: ALWAYS prod via Cloud SQL proxy
blocks: CLAUDECODE_BRIEF_GA8_GASTRENGTH_COMPLETENESS (the amendment runs after this)
---

# Pre-GA8 Closure — 3 Deck-Clearers — Execution Brief v1.0

## §1 — Item 1: Apply the Phase-E seed correction (NEVER EXECUTED — overdue)

`CLAUDECODE_BRIEF_BODHA_P0E_SEED_CORRECTION_v1_0` was authored but never applied. Verified 2026-06-12:
`asset_registry_seed.ts` still has `bo_samvada` = "Resonance map (RM)" → `bodha_rm_resonances` — the
exact mis-wiring it was meant to fix. Apply the 4 corrections from that brief now:

1. **`bo_samvada` → UCD / Option-A (NOT a writer):** english_name → "Unified Chart Digest (UCD)";
   `storage_type: 'view'`; `target_table: 'vw_chart_digest'`; `count_sql: null`; `size_sql: null`.
   It writes NO table; remove the `bodha_rm_resonances` pointer and the resonance framing.
2. **`bo_upaya` owns BOTH RM tables** incl. `bodha_rm_resonances` (primary) + summed count_sql across
   all 6 RM tables (per L2_BODHA_BUILD_CAMPAIGN §14 + the seed-correction brief §1 Fix 2).
3. **Summed count_sql** on all multi-table assets (`bo_sangati`, `bo_karanajala`, `bo_upaya`) — see the
   seed-correction brief §1 Fix 3 for the exact SQL.
4. **`bo_pramana_mapa`** (global) — drop the `WHERE chart_id = $1` from its count_sql.

Apply to `asset_registry_seed.ts` + seed to prod. **[verify-against: prod]** `SELECT asset_id,
english_name, target_table, count_sql FROM asset_registry WHERE asset_id IN ('bo_samvada','bo_upaya',
'bo_pramana_mapa');` — bo_samvada shows UCD/null, bo_upaya owns rm_resonances + summed, global un-filtered.

## §2 — Item 2: Mercury vargottama prod query (read-only verification)

Native knows Mercury is vargottama; confirm it's recorded post-#274. Run + report results:

```sql
-- Q1 — classical D1↔D9 vargottama (the primary definition):
SELECT fact_subject, fact_value_text, ayanamsha_id FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category='graha_special_state_rollup' AND fact_key='is_vargottama'
  AND fact_subject LIKE '%MER%' ORDER BY ayanamsha_id;
-- Q2 — which vargas Mercury repeats its D1 sign in:
SELECT fact_value_jsonb->>'varga' AS varga, fact_value_text, ayanamsha_id FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category='vargottama_per_varga' AND fact_subject LIKE '%MER%'
  AND fact_value_text='vargottama' ORDER BY ayanamsha_id, varga;
```
**Report the rows.** If Q1='true' → confirmed, done. If Q1='false'/empty across all 5 ayanamshas →
flag for investigation (code computes vargottama = D1-sign==D9-sign; check whether native's Mercury
vargottama is by a different pairing, or an ayanamsha-specific split).

## §3 — Item 3: Retire `bg_signal_type_registry` (G52) — dormant asset cleanup

The G52 `signal_type_registry` was the "500–700 predicate FIRING registry." The architecture decision
(`L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0`) DROPPED the predicate-firing model — ga_structural
enumerates exhaustively and labels from `brahma_yoga_catalog`, referencing `signal_type_registry` ZERO
times. So the asset is DORMANT (wired to nothing). **Native lean: RETIRE it** to prevent the firing-
model creeping back + avoid future "what's this 500–700 registry for?" confusion.

Retire cleanly (do NOT just delete blind — reverse-citation gate first,
`[[feedback-destructive-brief-reverse-citation-gate]]`):
1. **Grep for live readers:** `grep -rn "signal_type_registry" platform/src platform/platform-mcp
   platform/python-sidecar` — confirm nothing live reads it (expected: only the seed + the dormant
   adapter). If anything live cites it, STOP and report (don't drop).
2. If clean: mark `bg_signal_type_registry` `is_active=false` / remove its asset_registry row + the
   `@register('bg_signal_type_registry')` adapter + the seed file, and drop the `signal_type_registry`
   table via a surgical migration (tracker row). The `bodha_writers/signal_type_registry_seed.py` is
   retired with it.
3. Keep `brahma_yoga_catalog` / `brahma_dosha_catalog` — those are the LIVE label source, untouched.
**[verify-against: prod]** `SELECT to_regclass('public.signal_type_registry');` → NULL after retirement;
ga_structural build still passes (it never used it).

## §4 — Acceptance (all 3) [verify-against: prod]
- [ ] bo_samvada = UCD/null; bo_upaya owns rm_resonances + summed count_sql; global un-filtered.
- [ ] Mercury vargottama Q1+Q2 results reported.
- [ ] signal_type_registry retired (reverse-citation clean) OR halted-with-reason if a live reader found.

## §5 — Out of scope
The GA8+ga_strength completeness amendment (separate brief, runs AFTER this). Do not start it here.

---
*End of PRE_GA8_CLOSURE v1.0. Three deck-clearers: apply the overdue Phase-E seed correction, read
Mercury's vargottama, retire the dormant G52 registry. Clears the ground before the big L1-relationship
completeness amendment.*
