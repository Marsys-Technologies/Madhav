---
artifact: CLAUDECODE_BRIEF_GA8_VERIFY_BEFORE_FIX_v1_0.md
canonical_id: GA8_VERIFY_BEFORE_FIX_BRIEF
version: 1.0
status: CURRENT — VERIFY ONLY (no fixes until results reported)
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (prod read-only diagnostics)
diagnosis_source: GA8_ROWCOUNT_AND_PROGRESSBAR_DIAGNOSIS_v1_0.md
critical: This brief is DIAGNOSTIC ONLY. Run the queries, REPORT the results, do NOT fix/rebuild anything yet. The fix depends on what the results show — and rebuilding data that already exists would be wasted + risky.
---

# GA8 — Verify Before Fix (two open concerns) — Diagnostic Brief v1.0

Two native concerns after the GA8 completeness amendment (74,644 rows): (1) row count fell short of
the ~90-120k projection — is that just a bad estimate, or are the NODES under-enumerated? (2)
ga_strength / ga_sensitive / ga_sade_sati / ga_structural not reflecting in the cockpit progress bar
— missing data, or a count-query timeout? Settle BOTH with reads before deciding any fix.

## CHECK 1 — Are Rahu/Ketu actually enumerated in the per-family relationships? (the real half of Issue 1)

Code shows the new per-family loops (`_build_varga_relationship_rows`, house-lord, karaka-web,
graha-yuddha, special-point, combustion-retrograde) iterate `CLASSICAL_GRAHAS` (7), even though
`ALL_GRAHAS` (9) was added to the varga set. If nodes are in the varga set but NOT the per-family
loops, nodal relationships are UNDER-emitted — a real partial-completeness gap.

```sql
-- C1a: node vs classical-graha row counts as relationship SUBJECTS
SELECT
  count(*) FILTER (WHERE fact_subject LIKE '%RAH%') AS rahu_rows,
  count(*) FILTER (WHERE fact_subject LIKE '%KET%') AS ketu_rows,
  count(*) FILTER (WHERE fact_subject LIKE '%SAT%') AS saturn_rows,   -- a classical graha for comparison
  count(*) FILTER (WHERE fact_subject LIKE '%MER%') AS mercury_rows
FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- INTERPRET: if rahu/ketu << saturn/mercury (e.g. <30% of a classical graha's count), the nodes are
-- UNDER-enumerated → the per-family loops need ALL_GRAHAS not CLASSICAL_GRAHAS (a real fix, est. adds
-- meaningful rows). If rahu/ketu ≈ comparable, nodes are fine and Issue 1 = projection error only.
```

```sql
-- C1b: which fact_categories DO include nodes vs which don't (pinpoints WHICH loops to fix)
SELECT fact_category,
  count(*) FILTER (WHERE fact_subject LIKE '%RAH%' OR fact_subject LIKE '%KET%') AS node_rows,
  count(*) AS total_rows
FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY fact_category HAVING count(*) > 0 ORDER BY fact_category;
-- INTERPRET: any relationship category with node_rows=0 but total_rows>0 is a loop still on
-- CLASSICAL_GRAHAS → that's the exact function to switch to ALL_GRAHAS.
```

## CHECK 2 — Is the progress bar dark because data is MISSING, or because the COUNT times out?

The stats route runs count_sql under `SET LOCAL statement_timeout = '2s'`. chart_facts is now huge;
multi-pattern `LIKE` counts may exceed 2s → blank bar. Confirm data exists + time the count.

```sql
-- C2a: do the rows actually EXIST for the 4 "dark" assets? (if YES → it's a display/timeout bug)
SELECT
  count(*) FILTER (WHERE fact_category LIKE 'graha_shadbala_%' OR fact_category LIKE '%vimsopaka%' OR fact_category LIKE 'ashtakavarga_%') AS strength,
  count(*) FILTER (WHERE fact_category LIKE '%saham%' OR fact_category LIKE '%arudha%' OR fact_category LIKE 'upagraha%' OR fact_category LIKE '%hadda%') AS sensitive,
  count(*) FILTER (WHERE fact_category LIKE 'sade_sati%') AS sade_sati,
  count(*) FILTER (WHERE fact_category LIKE 'aspect_%' OR fact_category LIKE '%argala_natal_matrix') AS structural
FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- INTERPRET: all four > 0 → data is present → the bar is a DISPLAY bug, NOT missing data. Do NOT rebuild.

-- C2b: TIME the actual count_sql for ga_structural (and ga_strength) — does it exceed 2000ms?
\timing on
-- paste ga_structural's exact count_sql from asset_registry_seed.ts, $1 = '482012f1-710e-4a25-994a-93821f5871aa'
-- repeat for ga_strength, ga_sensitive, ga_sade_sati
-- INTERPRET: any > 2000ms → confirmed: the 2s statement_timeout is killing the count → blank bar.

-- C2c: total chart_facts size (the cause of the slow scans)
SELECT count(*) AS total_chart_facts FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
```

```
-- C2d: is the bar reading count_sql OR asset_throughput? (different root cause)
-- Check what the cockpit progress component actually reads. If it reads asset_throughput build-state:
SELECT asset_id, state, last_built_at, rows_written FROM asset_throughput
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('ga_strength','ga_sensitive','ga_sade_sati','ga_structural') ORDER BY asset_id;
-- INTERPRET: if these show stale/old state or low rows_written, the bar is reading build-state and
-- those assets weren't RE-RUN in the last build (only ga_structural+ga_strength were touched by the
-- amendment) → the fix is a re-run/throughput-refresh, not a count fix. Distinguish this from C2b.
```

## REPORT BACK (do not fix yet)
Report the results of C1a, C1b, C2a, C2b, C2c, C2d. Then the fix is determined:
- **If C1 shows nodes under-enumerated** → switch the flagged per-family loops to `ALL_GRAHAS` + rebuild
  (a real completeness fix).
- **If C2a shows data present + C2b shows >2s** → DISPLAY/timeout bug: fix the COUNTER, not the data —
  index `chart_facts(chart_id, fact_category)` + raise stats timeout + optionally cache counts at
  build-time. NO data rebuild.
- **If C2d shows stale asset_throughput** → those assets need a re-run / throughput refresh, not a
  count-query fix.
These are independent — it may be BOTH (nodes under-enumerated AND a count timeout). Report all
results so we scope the right fix(es).

## OUT OF SCOPE
No code changes, no rebuilds, no index creation in THIS brief. Diagnose + report only. Fixes follow in
a scoped brief once the results are in.

---
*End of GA8_VERIFY_BEFORE_FIX v1.0. Two reads: (C1) are Rahu/Ketu in the per-family relationship loops
or only the varga set — the real half of the "shortfall"; (C2) is the dark progress bar a count_sql
2s-timeout / stale throughput, or actual missing data. Report before any fix — don't rebuild data
that's already there.*
