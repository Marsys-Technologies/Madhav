---
title: Mars Dignity Error — Full Impact Analysis & Fix Record
canonical_id: MARS_DIGNITY_IMPACT_REPORT
version: 1.0
status: COMPLETE
authored: 2026-05-27
scope: PLN.MARS.DIGNITY.D1 = 'debilitated' factual error — root cause + all downstream impacts
---

# Mars Dignity Error: Full Impact Analysis & Fix Record

## §1 — Error Statement

**Fact:** Mars at 18°31'38" Libra (D1, 7th house) is in an **enemy sign** (śatru-kṣetra).  
- Libra is Venus-owned. Mars and Venus are classical natural enemies.  
- Mars debilitates in **Cancer** (neecha point 28°), NOT Libra.  
- The confusion likely arose from Sun's debilitation being Libra (10°) — a different planet.

**Root cause row:** `chart_facts` table, `fact_id = 'PLN.MARS.DIGNITY.D1'`, `value_text = 'debilitated'` ← **WRONG**  
**Correct value:** `'enemy'`

---

## §2 — Root Cause

**File:** `platform/scripts/data/seed_chart_facts_planet.ts`  
**Lines:** 119–130 (wrong comment + wrong value)

The seed script manually hardcoded `value_text: 'debilitated'` with an incorrect comment
"Libra = Mars debilitation." This was a scripting error — no FORENSIC source ever stated
Mars was debilitated in D1 Libra. The FORENSIC v8.0 §PLN.MARS Special Role reads:
"Avayogi planet; Lagna Lord; conjunct Saturn exalted in 7H (ATT pattern)."
No debilitation label appears.

**Fix:** `value_text: 'debilitated'` → `value_text: 'enemy'`  
**Comment corrected** to: "Libra = Mars enemy sign (Venus-owned; Mars-Venus enemies = śatru-kṣetra)"  
**Status:** Fixed on disk (not yet committed).

---

## §3 — Database Hotfix Required (Human Gate)

The seed script populated the live DB. The file fix only corrects future re-runs.
**Operator must execute:**

```sql
UPDATE chart_facts
SET value_text = 'enemy'
WHERE fact_id = 'PLN.MARS.DIGNITY.D1'
  AND divisional_chart = 'D1';
```

Run via `platform/scripts/start_db_proxy.sh` (port 5433) then psql, or via Supabase SQL editor.
Verify: `SELECT fact_id, value_text FROM chart_facts WHERE fact_id = 'PLN.MARS.DIGNITY.D1';`

---

## §4 — Downstream Impact: Files with Errors Fixed

### 4.1 CGM_v9_0.md — EDGE.DT.MARS dignity_shift
**Location:** ~line 3238, EDGE.DT.MARS node  
**Old:** `dignity_shift: "debilitated → neutral (D1 Libra is Mars debilitation; D9 Pisces is neutral)"`  
**New:** `dignity_shift: "enemy → neutral (D1 Libra is Mars enemy sign — Venus-owned, śatru-kṣetra; D9 Pisces is neutral)"`  
**Status:** Fixed on disk.

### 4.2 CGM_v9_0.md — DVS.D24.MARS node
**Location:** Line 2756–2757, D24 divisional chart Mars node  
**Old:**
```yaml
dignity: debilitated
note: "In Libra (debilitation) joined Rahu and Ketu in D24 6H."
```
**New:**
```yaml
dignity: enemy
note: "In Libra (enemy sign — Venus-ruled, śatru-kṣetra; Mars debilitates in Cancer not Libra) joined Rahu and Ketu in D24 6H. Corrected 2026-05-27."
```
**Notes:** The error in D1 seeded an identical error in the D24 node. Mars in Libra = enemy sign in ALL
divisional charts (debilitation sign is Cancer regardless of varga).  
**Status:** Fixed on disk.

### 4.3 platform-mcp/src/resources/chart_snapshot.ts — Planetary Positions Table
**Location:** Line 76  
**Old:** `| Mars | 7 | Libra | 18°31′38″ | Debilitated | Swati | Rahu | — |`  
**New:** `| Mars | 7 | Libra | 18°31′38″ | Enemy Sign | Swati | Rahu | — |`  
**Notes:** Hardcoded static table. Not read from chart_facts DB at runtime — independent bug same root error.  
**Status:** Fixed on disk.

---

## §5 — Additional Errors Discovered in chart_snapshot.ts (Out-of-Scope but Fixed)

During the Mars audit, two additional dignity errors were found in the same hardcoded table:

### 5.1 Jupiter dignity — Aquarius
**Old:** `| Jupiter | 11 | Aquarius | 24°01′41″ | Debilitated | Purva Bhadrapada | Jupiter | — |`  
**New:** `| Jupiter | 11 | Aquarius | 24°01′41″ | Enemy Sign | Purva Bhadrapada | Jupiter | — |`  
**Reason:** Jupiter debilitates in Capricorn (not Aquarius). Aquarius is Saturn-ruled; Jupiter-Saturn are enemies → enemy sign.  
**FORENSIC confirmation:** PLN.JUPITER — Aquarius 24°01'41", House 11.

### 5.2 Saturn — wrong house, sign, degree, dignity
**Old:** `| Saturn | 6 | Virgo | 18°02′10″ | Neutral | Hasta | Moon | — |`  
**New:** `| Saturn | 7 | Libra | 22°27′04″ | Exalted | Vishakha | Jupiter | — |`  
**Reason:** Saturn at Libra 22°27'04" House 7 per FORENSIC v8.0 §PLN.SATURN. Saturn exalts in Libra. Saturn
conjunct Mars in 7H is the ATT pattern — the snapshot was missing this entire conjunction.  
**FORENSIC confirmation:** `PLN.SATURN | Saturn | Libra | 22°27′04″ | Vishakha | 1 | 202.45 | 7 | 7`  
**Status:** Fixed on disk.

---

## §6 — Files Audited — Confirmed Correct (No Changes Required)

| File | Finding |
|------|---------|
| `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | Consistently uses "enemy sign" for Mars in Libra throughout. Multiple explicit statements. ✓ |
| `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | Line 190 explicitly: "Libra enemy-sign (Mars debilitation is Cancer; Libra is Mars's enemy-sign Venus-ruled)". ✓ |
| `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | Multiple correct statements. Line 5385: "enemy's sign (not debilitation)". Line 12358 falsifier correctly states Cancer as Mars debilitation. Imprecise language at line 12355 ("PK debilitated in terms of Mars's own strength") is colloquial weakness, not a factual sign-assignment error. ✓ |
| `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | No Mars debilitation references. ✓ |
| `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` — SGN.CANCER node | `debilitation: PLN.MARS` is CORRECT (Cancer IS Mars's debilitation sign). ✓ |
| `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` — DVS.D45.MARS | `D45 Mars — Cancer H10 (debilitated)` is CORRECT (Mars in Cancer = debilitated). ✓ |
| `platform/python-sidecar/pipeline/ephemeris_derivations.py` | `DIGNITY_TABLE` maps `mars.debilitated = 'Cancer'`. `compute_dignity('mars', 'Libra', ...)` returns `'neutral'` (correct — no 'enemy' category in live engine vocabulary). ✓ |
| `platform/src/lib/retrieve/cross_varga_dignity_query.ts` | `deriveDignity('mars', 'Libra')` → `'neutral'` (fallthrough after exalted/debilitated/own checks). Does NOT read `PLN.MARS.DIGNITY.D1` value_text. Not propagating the DB error. ✓ |
| `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | No Mars dignity error references. ✓ |
| `platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py` | `test_mars_debilitated_in_cancer()` asserts Cancer=debilitated. Correct. ✓ |

---

## §7 — Vocabulary Note: 'enemy' vs 'neutral' in the live engine

`compute_dignity()` in `ephemeris_derivations.py` has 5 return values: `exalted`, `debilitated`, `own_sign`, `mooltrikona`, `neutral`. There is no `'enemy'` category — all non-special signs fall through to `'neutral'`.

The `chart_facts` seed uses free-text `value_text` fields. Setting `value_text = 'enemy'` in chart_facts is correct for this static record and matches the FORENSIC/classical framing. This does NOT conflict with the live engine (which is correct for runtime computation and has a different vocabulary).

Any downstream code that reads `chart_facts` `PLN.MARS.DIGNITY.D1` and uses `dignityFromValueJson` or string-contains checks should handle `'enemy'` as a valid value for "weakened/śatru-kṣetra" placement.

---

## §8 — Commit Instructions

All four file edits above are pending git commit. Git HEAD.lock may need clearing first.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# If .git/HEAD.lock exists from a prior aborted commit:
rm -f .git/HEAD.lock

# Stage the four changed files:
git add platform/scripts/data/seed_chart_facts_planet.ts
git add 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md
git add platform-mcp/src/resources/chart_snapshot.ts

git commit -m "fix(data): correct PLN.MARS.DIGNITY.D1 debilitated→enemy + cascade fixes

Root cause: seed_chart_facts_planet.ts hardcoded 'debilitated' for Mars in Libra.
Mars debilitates in Cancer (28°), not Libra. Libra is Venus-owned; Mars-Venus are
classical enemies → śatru-kṣetra (enemy sign).

Files fixed:
- seed_chart_facts_planet.ts: value_text 'debilitated'→'enemy', comment corrected
- CGM_v9_0.md EDGE.DT.MARS: dignity_shift corrected (2 locations)
- CGM_v9_0.md DVS.D24.MARS: dignity + note corrected
- chart_snapshot.ts: Mars row dignity corrected

Additional fixes in chart_snapshot.ts (same session, same hardcoded table):
- Jupiter Aquarius: 'Debilitated'→'Enemy Sign' (debilitation=Capricorn)
- Saturn: wrong house/sign/degree/dignity → Libra H7 22°27'04\" Exalted (per FORENSIC)

DB hotfix still required (human gate):
  UPDATE chart_facts SET value_text = 'enemy'
  WHERE fact_id = 'PLN.MARS.DIGNITY.D1' AND divisional_chart = 'D1';

FORENSIC source: §PLN.MARS — no debilitation label; Mars at 18°31'38\" Libra H7.
Closes: Mars dignity data error found 2026-05-27."

git push origin main
```

Then deploy amjis-mcp to pick up chart_snapshot.ts fix:
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_TAG=$(git rev-parse --short HEAD) \
  --project madhav-astrology
```

---

## §9 — Summary of Changes

| # | File | Change | Status |
|---|------|--------|--------|
| 1 | `platform/scripts/data/seed_chart_facts_planet.ts` | PLN.MARS.DIGNITY.D1 'debilitated'→'enemy' | On disk |
| 2 | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` (EDGE.DT.MARS) | dignity_shift corrected | On disk |
| 3 | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` (DVS.D24.MARS) | dignity + note corrected | On disk |
| 4 | `platform-mcp/src/resources/chart_snapshot.ts` | Mars dignity 'Debilitated'→'Enemy Sign' | On disk |
| 5 | `platform-mcp/src/resources/chart_snapshot.ts` | Jupiter dignity 'Debilitated'→'Enemy Sign' | On disk |
| 6 | `platform-mcp/src/resources/chart_snapshot.ts` | Saturn H/sign/deg/dignity corrected per FORENSIC | On disk |
| 7 | `chart_facts` DB row | UPDATE value_text 'debilitated'→'enemy' | **Pending — human gate** |
| 8 | amjis-mcp Cloud Run | Re-deploy to pick up chart_snapshot.ts fix | **Pending — after commit** |
