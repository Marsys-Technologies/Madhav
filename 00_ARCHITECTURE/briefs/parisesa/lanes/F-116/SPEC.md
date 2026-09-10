---
finding_id: F-116
lane: F-116
stream: S4_VACA
stage: S (SPEC)
class: TIER2-HONESTY (§N.7 narration-fidelity — false conditional preamble served as chart-matched)
author: SPEC_WRITER (coord-wt, par-night run)
status: DRAFT — awaiting VERIFIER review
writer_asset: bo_upaya
data_delta: narrow
---

# SPEC — bo_upaya: conditional preamble in remedy_label_human served without chart-state gating

## 1. Root-cause statement

`bo_upaya.py:1347` embeds each corpus row's `prescription_text` verbatim as `remedy_label_human` without stripping the "For <affliction condition>: " conditional preamble that 12/12 `STOTRA_REMEDIES` rows and ~30+ `DOSHA_REMEDIES`/`DANA_EXPANSION_REMEDIES` rows carry, because `_fetch_remedies_for_graha` (lines 983–994) selects rows by `lower(planet) = %s` only and no post-fetch predicate ever tests whether the named affliction condition holds for the chart being served.

## 2. Files to change

### `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`

**Why this file, not `query_remedies.ts`:** fixing write-side avoids the confirmed line-overlap with F-50 and F-117 §2e on `query_remedies.ts` (diagnosis §Blast Radius). F-117 changes `bo_upaya.py` at lines 837–844, 1175, and 1255 — none of those overlap the lines this spec touches (new helper ~line 982; line 1347–1358). The two lanes are fully independent and can land in either order.

**What — two adjacent edits:**

Insert helper function immediately above `_fetch_remedies_for_graha` (around line 982):
```python
import re as _re
_CONDITIONAL_PREAMBLE_RE = _re.compile(r'^For\s[^:]{5,200}:\s*', _re.IGNORECASE)

def _strip_conditional_preamble(text: str) -> tuple[str, bool]:
    """Strip 'For <affliction clause>: ' preamble from prescription_text.
    Returns (cleaned_text, preamble_was_stripped).
    The preamble states a condition never tested against chart state (F-116)."""
    m = _CONDITIONAL_PREAMBLE_RE.match(text)
    if m:
        remainder = text[m.end():]
        return (remainder[:1].upper() + remainder[1:] if remainder else ""), True
    return text, False
```

In the loop body, **before** the `prescriptions.append({` call at line 1336, insert the two assignment lines:
```python
_raw_pt = str(corpus_row.get("prescription_text") or "")
_label_human, _preamble_stripped = _strip_conditional_preamble(_raw_pt)
```

These assignments must appear in the loop body before `prescriptions.append({` at line 1336 — not inside the dict literal. `_preamble_stripped` is then in scope for the entire `prescriptions.append({...})` call below.

Change line 1347 (inside `prescriptions.append({...})`) from:
```python
"remedy_label_human": str(corpus_row.get("prescription_text") or "")[:200],
```
To:
```python
"remedy_label_human": _label_human[:200],
```

Extend `prescription_detail_jsonb` (line 1348 dict) to add:
```python
"preamble_stripped": _preamble_stripped,  # True = conditional clause removed; False = none present
```
(`_preamble_stripped` is in scope because both assignments occur before `prescriptions.append({` opens.)

## 3. Exit test

**New file:** `platform/python-sidecar/tests/l2/test_bo_upaya_preamble_strip.py`

FAILS today: `_strip_conditional_preamble` does not exist (ImportError on first test). After fix: all tests pass.

```python
"""
Exit test for F-116 (PARISESA S4_VACA, TIER2-HONESTY):
bo_upaya remedy_label_human embeds conditional-affliction preambles from
brahma_remedy_corpus verbatim. See SPEC.md §1.
FAILS today: ImportError (_strip_conditional_preamble absent).
PASSES after: helper strips preamble, helper-level and integration assertions hold.
"""
import pytest
from pipeline.orchestrator.writers.bo_upaya import _strip_conditional_preamble

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"


def test_strip_removes_stotra_preamble_sun():
    """Confirmed-false Sun preamble from DIAGNOSIS.md live repro."""
    raw = (
        "For afflicted Sun (combust, debilitated in Libra, or in 6/8/12): "
        "recite Aditya Hridayam (from Valmiki Ramayana, Yuddha Kanda Ch.107) "
        "in full at sunrise facing east, daily during Sun dasha/antardasha."
    )
    cleaned, stripped = _strip_conditional_preamble(raw)
    assert stripped is True
    assert not cleaned.lower().startswith("for "), f"Preamble not stripped: {cleaned!r}"
    assert "aditya hridayam" in cleaned.lower(), f"Prescription body lost: {cleaned!r}"


def test_strip_removes_stotra_preamble_jupiter():
    raw = (
        "For afflicted Jupiter (debilitated in Capricorn, Guru Chandal dosha, "
        "retrograde in dasha): recite Vishnu Sahasranama once daily on Thursdays."
    )
    cleaned, stripped = _strip_conditional_preamble(raw)
    assert stripped is True
    assert not cleaned.lower().startswith("for ")
    assert "vishnu sahasranama" in cleaned.lower()


def test_strip_leaves_unconditional_text():
    """Text without 'For <condition>: ' is returned unchanged, stripped=False."""
    raw = "Recite Aditya Hridayam once daily at sunrise."
    cleaned, stripped = _strip_conditional_preamble(raw)
    assert stripped is False
    assert cleaned == raw


def test_live_corpus_rows_are_strippable(db_conn):
    """Integration: brahma_remedy_corpus rows opening with 'For ...' exist today.
    After fix, _strip_conditional_preamble correctly strips every one."""
    rows = db_conn.execute(
        "SELECT prescription_text FROM brahma_remedy_corpus "
        "WHERE scaffold_status = 'live' AND prescription_text ILIKE 'For %' LIMIT 20"
    ).fetchall()
    assert rows, "No 'For ...' rows found in brahma_remedy_corpus — corpus changed or query wrong"
    for row in rows:
        raw = row[0] if isinstance(row, (tuple, list)) else row["prescription_text"]
        cleaned, stripped = _strip_conditional_preamble(raw)
        assert stripped is True, f"Helper did not strip: {raw[:80]!r}"
        assert not cleaned.lower().startswith("for "), f"Strip incomplete: {cleaned[:60]!r}"


def test_stored_remedy_label_human_has_no_conditional_preamble(db_conn):
    """After rebuild: bodha_upaya_prescriptions for the canonical chart contains
    no remedy_label_human starting with 'For '.
    TODAY (pre-rebuild): this test is skipped if the table is stale (pre-fix build).
    AFTER REBUILD: must pass — zero rows match the condition."""
    rows = db_conn.execute(
        "SELECT target_graha, remedy_label_human FROM bodha_upaya_prescriptions "
        "WHERE chart_id = %s AND ayanamsha_id = %s AND remedy_label_human ILIKE 'For %%'",
        [CHART_ID, AYA],
    ).fetchall()
    assert rows == [], (
        f"Found {len(rows)} prescription(s) with unchecked conditional preamble "
        f"after rebuild: {[(r[0], r[1][:60]) for r in rows]}"
    )
```

## 4. Sibling sites covered

All sibling sites share the same fix path — `_strip_conditional_preamble` is called at line 1347, which is the single output point for ALL corpus rows regardless of source bucket:

| Bucket | Conditional preambles | Covered? |
|---|---|---|
| `STOTRA_REMEDIES` (lines 2216–2475) | **12/12** — all 9 classical grahas; every entry read directly in diagnosis | Yes — all route through `_fetch_remedies_for_graha` → line 1347 |
| `DOSHA_REMEDIES` (lines 410–1296) | ~30+ ("For Mangala Dosha…", "For Kala Sarpa Dosha…", etc.) — spot-confirmed in diagnosis | Yes — same path |
| `DANA_EXPANSION_REMEDIES` (lines 2478–2858) | Several ("For Venus-related…", "For Kuja (Mangala) Dosha…") — spot-confirmed | Yes — same path |
| `LEGACY_REMEDIES` | No preamble pattern confirmed in diagnosis | Covered; helper returns `stripped=False`, no change |
| `YANTRA_SPEC_REMEDIES` | No preamble pattern confirmed in diagnosis | Covered; helper returns `stripped=False`, no change |

**Excluded (with written reason):** Filtering corpus rows by `dosha_target` (a corpus column not in the current SELECT) as a secondary gate. Diagnosis §3 flags this as a follow-up extension; `dosha_target` filtering would carry a dependency on F-117 §2a landing first (to make `dosha_by_graha` reliable for 7/9 grahas). Deferred — the preamble-strip fix is a complete §N.7.6 resolution without it.

## 5. Recurrence guard

**Primary guard:** `test_bo_upaya_preamble_strip.py::test_strip_removes_stotra_preamble_sun` fails on ImportError if `_strip_conditional_preamble` is removed, and `test_stored_remedy_label_human_has_no_conditional_preamble` fails if any future edit re-introduces verbatim preamble embedding at line 1347.

**Recommended follow-up CI lint (flag to conductor, out of this spec's build scope):** Add a script under `platform/scripts/governance/` asserting `SELECT count(*) FROM bodha_upaya_prescriptions WHERE remedy_label_human ILIKE 'For %'` returns 0 for the canonical chart after any `bo_upaya` rebuild — same model as `check_fact_category_pinning.py`. This closes the gap between unit-testing the helper and verifying the DB field doesn't regress silently.

## 6. Dependencies and rollback

- **Lane dependencies:** None. The preamble strip operates on `prescription_text` as fetched and does not require `dosha_by_graha` to be correct. F-116 and F-117 can land in either order.
- **Migration:** None. `remedy_label_human` and `prescription_detail_jsonb` are existing columns; only the stored values change.
- **Rebuild required:** Yes — `bo_upaya` is a delete-then-insert writer (§N.3). Takes effect on the next G3 scoped rebuild for chart `482012f1`. Per PROTOCOL.md rebuild policy, this rebuild should be batched with F-117 (both in G3) after all G3 lane fixes are merged.
- **Rollback:** Single `git revert`. No schema change; rollback simply re-embeds the unchecked preambles on the next rebuild.
- **Downstream stale assets:** `bodha_upaya_prescriptions.remedy_label_human` is consumed as a passthrough field in `query_remedies.ts:542`. No other L2/L3/L4/L5 writer depends on this field. Stale impact: narrow, serving-only.

## 7. Coverage table

| Diagnosis sub-claim | Determination | Spec element |
|---|---|---|
| (a) Jupiter preamble FALSE — own sign Sagittarius, not debilitated | Root cause confirmed; fix covers this row | §1, §2, §3 (Jupiter test) |
| (b) Sun preamble FALSE — FORENSIC anchor Capricorn, not debilitated | Root cause confirmed | §1, §2, §3 (Sun test) |
| (c) Venus preamble FALSE — Sagittarius, not Virgo or 6H/12H | Root cause confirmed | §1, §2 |
| (d) Architectural — same join-only predicate, all corpus rows | Confirmed; single call-site fix covers all buckets | §2, §4 |
| Mechanism: `_fetch_remedies_for_graha` — planet-only WHERE clause | Confirmed (read live at lines 983–994); no SQL change needed for this fix path | §1 |
| Mechanism: `dosha_by_graha` available but unused for gating | Confirmed; noted as out-of-scope extension (dosha-target filtering) in §4 | §4 exclusion note |
| Mechanism: serve-time passthrough `query_remedies.ts:542` | Confirmed; write-side fix makes passthrough safe — no TS change needed | §2 (fix-locus decision) |
| Sibling census: 12/12 STOTRA_REMEDIES, ~30+ DOSHA, several DANA rows | All covered by single call-site fix | §4 |
| F-50 / F-116 blast-radius overlap in `query_remedies.ts` | Avoided by fixing write-side | §2 collision check |
| F-117 line-overlap in `bo_upaya.py` | Zero overlap; confirmed lines differ | §2 collision check |
