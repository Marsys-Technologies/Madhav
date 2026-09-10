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
