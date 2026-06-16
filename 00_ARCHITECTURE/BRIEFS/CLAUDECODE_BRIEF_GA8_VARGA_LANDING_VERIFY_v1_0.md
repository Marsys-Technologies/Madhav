---
artifact: CLAUDECODE_BRIEF_GA8_VARGA_LANDING_VERIFY_v1_0.md
canonical_id: GA8_VARGA_LANDING_VERIFY
version: 1.0
status: CURRENT — verification + conditional fix
authored_by: Cowork (forensic) 2026-06-12
authored_for: Claude Code in Antigravity (data-plane verification — Cowork cannot query prod)
severity: HIGH if confirmed — the multi-varga leverage fix may not have actually landed
---

# GA8 v2.0 — Multi-Varga Landing Verification + Conditional Fix

## §0 — The red flag

GA8 v2.0's whole purpose was to enumerate aspects/conjunctions/dispositors across **all 16 shodasha
vargas × 5 ayanamshas** (fixing the ~5% D1-only leverage). But prod reports **6,754 total rows ≈ the
old D1-only count (~6,075)**. If 16 vargas were truly enumerated (45 aspect-pairs + conjunctions +
dispositors each), the count should be a LARGE MULTIPLE of D1-only, not ~equal. **Strong signal the
multi-varga enumeration is silently NOT landing.**

## §1 — The suspected mechanism (code-plane diagnosis, verified by Cowork)

- `_build_varga_aspect_rows` (ga_structural_writer.py:2972) loops `for varga in SHODASHA_VARGAS`.
- For D2–D60 it calls `_load_varga_positions(conn, chart_id, ayanamsha_id, varga)` (line 2976).
- **If that returns empty, line 2977–2979 does `continue` — silently skips the varga** (logs only at
  `debug`, not warning). So if the loader query doesn't match what GA6 wrote, 15 of 16 vargas vanish
  with no error, and GA8 output collapses to D1-only — exactly the symptom.
- The loader (line 626–639) queries `chart_divisionals` WHERE `fact_category = 'varga_position'` AND
  a column **`varga = %s`** (label like 'D9') AND `fact_key IN ('sign','sign_id','house','degree_in_sign')`.
- GA6 (`ga_vargas_writer.py:720`) writes via `_fact_id(vid, body, "varga_position", key, ...)` — the
  varga identity is `vid`. **It is UNCONFIRMED that `chart_divisionals` has a column literally named
  `varga` populated with 'D9'-style labels matching the loader.** If GA6 stores the varga in a
  different column (e.g. `varga_id`, or encoded in `fact_subject`), or uses a different label format
  ('D9' vs 'navamsa' vs '9' vs the `vid`), the loader returns empty → silent skip → drop.

## §2 — VERIFY (Antigravity, against prod via Cloud SQL proxy)

```sql
-- V-A: does chart_divisionals have a `varga` column, and what labels/categories does it hold?
\d chart_divisionals
SELECT DISTINCT fact_category FROM chart_divisionals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' LIMIT 30;
SELECT DISTINCT varga FROM chart_divisionals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' LIMIT 40;  -- if column exists

-- V-B: does the EXACT loader query return rows for D9? (reproduce _load_varga_positions)
SELECT graha,
  MAX(CASE WHEN fact_key='sign' THEN fact_value_text END) AS sign,
  MAX(CASE WHEN fact_key='house' THEN fact_value_num END) AS house
FROM chart_divisionals
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id='lahiri'
  AND varga='D9' AND fact_category='varga_position' AND graha IS NOT NULL
GROUP BY graha;
-- EXPECTED: 9-10 rows. IF 0 ROWS → the loader is mismatched → bug confirmed.

-- V-C: GA8 row count BY varga — proves whether multi-varga landed
SELECT fact_value_jsonb->>'varga' AS varga, count(*)
FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category LIKE 'aspect%' OR fact_category LIKE 'conjunction%'
GROUP BY 1 ORDER BY 2 DESC;
-- EXPECTED if healthy: ~16 distinct vargas each with rows. IF only D1 → bug confirmed.
```

## §3 — FIX (apply only if V-B/V-C confirm the drop)

1. **Correct `_load_varga_positions`** to match GA6's actual storage shape (the real column name +
   label format for the varga + the real `fact_category`/`fact_key`s GA6 writes). Align the query to
   what `\d chart_divisionals` + V-A reveal. This is the load-bearing fix.
2. **Turn the silent skip LOUD (no-silent-drop principle):** ga_structural_writer.py:2977–2979 — change
   the `continue` so a missing expected varga logs a WARNING and is counted; if a shodasha varga GA6
   was supposed to produce is absent, the build should HALT or emit a flagged `varga_missing` row, not
   silently skip. A core principle of this rebuild is that absence is never silent.
3. **Re-run GA8 for the native** and re-check: row count should jump to a large multiple (tens of
   thousands+), with V-C showing all ~16 vargas populated.
4. **Update target_floor** = the new achieved count (floors aspirational).

## §4 — Acceptance (post-fix) [verify-against: prod]
- [ ] V-B returns 9–10 rows for D9 (loader matches GA6 storage).
- [ ] V-C shows all 16 shodasha vargas with aspect/conjunction rows (not D1-only).
- [ ] Total GA8 rows is a large multiple of the old ~6,075 D1-only count.
- [ ] No silent varga skips — any missing varga logs WARNING/halts.
- [ ] FORENSIC 7/7 still passes; two-pass still true; argala/labels unchanged.

## §5 — If V-B/V-C show it DID land
Then 6,754 is genuinely the correct count (e.g. GA6's chart_divisionals only has D1 positions for
this native, or the varga set is thinner than assumed) — in which case the finding is the row-count
expectation was wrong, not the code. Report which, with the V-C breakdown, so we update the expected-
volume understanding. Either way, the by-varga breakdown (V-C) is the definitive answer.

---
*End of GA8_VARGA_LANDING_VERIFY v1.0. The 6,754 ≈ D1-only count is a strong signal the multi-varga
enumeration silently isn't landing (loader/label mismatch → silent continue → 15 vargas dropped).
Verify with the by-varga breakdown (V-C); fix the loader + make the skip loud if confirmed.*
