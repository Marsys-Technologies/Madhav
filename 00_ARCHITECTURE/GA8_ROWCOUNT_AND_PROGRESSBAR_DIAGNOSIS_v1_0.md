---
artifact: GA8_ROWCOUNT_AND_PROGRESSBAR_DIAGNOSIS_v1_0.md
canonical_id: GA8_ROWCOUNT_PROGRESSBAR_DIAGNOSIS
version: 1.0
status: CURRENT — diagnosis + Antigravity verify/fix
authored_by: Cowork (forensic) 2026-06-12
purpose: Answer two native concerns post-GA8-completeness — (1) why ga_structural rows (74,644) fell short of the ~90-120k projection, and (2) why ga_strength/ga_sensitive/ga_sade_sati/ga_structural are not reflecting in the cockpit progress bar.
caveat: Cowork reasons from code; the row counts + progress-bar state are PROD facts — Antigravity confirms with the queries below.
---

# GA8 Row-Count Shortfall + Progress-Bar Diagnosis v1.0

## §1 — ISSUE 1: the row "shortfall" is a PROJECTION ERROR, not a data problem

74,644 is the real deterministic count; my ~90–120k was a back-of-envelope guess, not arithmetic.
Here is the realistic per-family math, so expectations become calculable, not vibes.

**Key facts from the code:**
- `ALL_30_VARGAS` = 30; `CLASSICAL_GRAHAS` = 7; `ALL_GRAHAS` = 9; ayanamshas = 5.
- **Most per-varga relationship families loop `CLASSICAL_GRAHAS` (7), NOT `ALL_GRAHAS` (9).** Verified:
  `_build_varga_relationship_rows`, house-lord, karaka-web, graha-yuddha, special-point, combustion-
  retrograde all iterate `for g_name in CLASSICAL_GRAHAS`. So **Rahu/Ketu were added to the
  enumeration SET but several per-family loops still use the 7-graha list** — this is why the count
  is lower than a 9-graha projection. (THIS IS WORTH CONFIRMING — see §1.1, it may be a partial fix.)

**Why ~120k was wrong (the honest recompute):**
- My projection assumed argala (288 rows) × 30 vargas × 5 ay ≈ 43k PLUS a 9-graha relationship layer.
- Reality: the per-varga relationship layer is ~per-varga-fixed (≈ dignity 7 + aspects 7×3 + vargottama 7
  + dispositor 7 + small variable conjunction/parivartana tail ≈ ~55-65 rows/varga × 30 × 5 ≈ ~9k),
  the argala layer, the 8 new families (each modest, 7-graha-scoped), and the D1-natal-only base (~5k).
  Summed → ~74k. **The projection over-weighted argala-per-varga and assumed 9-graha loops; the real
  build is 7-graha-loop-dominated.** 74,644 is internally consistent with the actual loop structure.

### §1.1 — THE REAL QUESTION HIDING IN ISSUE 1 (flag for Antigravity)
The completeness brief said "add Rahu/Ketu to ALL relationship enumeration." But the per-family loops
still read `CLASSICAL_GRAHAS` (7). **If Rahu/Ketu are only in the top-level varga set but NOT in the
per-family relationship loops, then nodal relationships are UNDER-emitted — a partial completion of
T1.1.** This is exactly the "is the completeness actually complete?" check.
**VERIFY:** `SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-...' AND fact_subject LIKE '%RAH%';`
and `... LIKE '%KET%';` — if these are small relative to a classical graha's count, the nodes are
under-enumerated and the per-family loops need `ALL_GRAHAS`, not `CLASSICAL_GRAHAS`. **This could be a
genuine 40-50% completeness gap, NOT just a projection error.** Settle this first — it determines
whether 74,644 is "correct + my estimate was wrong" or "the build under-emitted the nodes."

**Going forward — make expectations arithmetic:** future row projections = Σ over families of
(graha-or-pair count × offset/state count × varga count × ayanamsha count). No more vibes estimates.

## §2 — ISSUE 2: progress bar not reflecting — almost certainly a COUNT_SQL TIMEOUT, not missing data

**Mechanism (verified in `platform/src/app/api/cockpit/stats/route.ts`):**
- Line 97: the stats route runs each asset's count_sql under `SET LOCAL statement_timeout = '2s'`.
- ga_strength / ga_sensitive / ga_sade_sati / ga_structural ALL write to the SAME shared `chart_facts`
  table, and each one's count_sql is a `WHERE fact_category LIKE '...' OR ...` multi-pattern scan.
- After the GA8 amendment, `chart_facts` ballooned (ga_structural alone = 74,644; total chart_facts is
  now likely several hundred thousand rows). A multi-pattern `LIKE` count over that big a table,
  unindexed on fact_category, **easily exceeds 2 seconds → times out → the route returns error/blank →
  the progress bar shows nothing.**
- **This explains WHY these specific four:** they're exactly the shared-`chart_facts` assets whose
  count scans got slow together when the table grew. ga_positions/ga_panchanga (smaller category sets)
  may still squeak under 2s. The data is present; the COUNTER is choking.

**VERIFY (Antigravity, prod):**
```sql
-- A: do the rows actually exist? (if YES → it's a display/timeout bug, not missing data)
SELECT
  count(*) FILTER (WHERE fact_category LIKE 'graha_shadbala_%') AS strength,
  count(*) FILTER (WHERE fact_category LIKE '%saham%' OR fact_category LIKE '%arudha%' OR fact_category LIKE 'upagraha%') AS sensitive,
  count(*) FILTER (WHERE fact_category LIKE 'sade_sati%') AS sade_sati,
  count(*) FILTER (WHERE fact_category LIKE 'aspect_%') AS structural_aspects
FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- B: time the actual count_sql — does it exceed 2s?
\timing on
<paste ga_structural's count_sql with $1=482012f1>;   -- if > 2000ms → confirmed timeout
-- C: total chart_facts size
SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
```
If A shows rows present + B shows > 2s → **confirmed: display/timeout bug, data is fine.**

**FIX options (do NOT touch the data):**
1. **Index** `chart_facts (chart_id, fact_category)` (or a fact_category prefix/GIN index) so the LIKE
   counts are fast — the proper fix; helps every asset's count + the Atlas + retrieval.
2. Raise the stats-route `statement_timeout` for count_sql (e.g. 2s → 10s) — quick mitigation.
3. Cache the count at build-time (write the achieved count to asset_throughput/a counts table; the bar
   reads the cached number instead of live-counting a huge table) — most robust at scale.
Recommend #1 (index) + #3 (build-time cached count) together; #2 as the immediate unblock.

**ALSO CHECK — is it count_sql OR asset_throughput?** The bar may read build-state (asset_throughput)
not count_sql. If these four assets weren't RE-RUN in the last build (only ga_structural + ga_strength
were touched by the amendment; ga_sensitive/ga_sade_sati may not have re-run), their throughput rows
could be stale → bar shows old/empty state even though chart_facts has the data. Confirm whether the
bar reads count_sql (then it's the timeout) or asset_throughput (then it's a stale-build-state).

## §3 — Verdict
- **Issue 1:** 74,644 is correct for the actual loop structure; my projection was wrong (over-weighted
  argala, assumed 9-graha loops). BUT verify §1.1 — the per-family loops use CLASSICAL_GRAHAS (7), so
  the NODES may be under-enumerated (a real partial-completeness gap, fixable by switching those loops
  to ALL_GRAHAS). This is the one that could be a genuine 40-50% shortfall, distinct from the estimate
  error.
- **Issue 2:** almost certainly NOT missing data — a count_sql timeout (2s) over the now-huge shared
  chart_facts table, affecting exactly the four shared-table assets. Fix = index + cached count + raise
  timeout. Confirm with the §2 queries before any rebuild (don't rebuild data that's already there).

---
*End of GA8_ROWCOUNT_AND_PROGRESSBAR_DIAGNOSIS v1.0. Issue 1 = projection error + a real node-under-
enumeration check (per-family loops still 7-graha). Issue 2 = count_sql 2s-timeout on the ballooned
shared chart_facts table, not lost data. Verify both with the prod queries; fix the counter (index/
cache), and switch per-family loops to ALL_GRAHAS if §1.1 confirms nodes under-emitted.*
