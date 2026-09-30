"""O-PP-* — permission_per_instant oracles (GOCHARA_DESIGN_SPECS_v1_4 §4,
with the §4.0 pinned reference rows embedded as literal constant data).

Instants are UTC (§4.0 instant rule: an IST calendar date is 00:00:00 IST =
the previous UTC day at 18:30:00Z): the three worked events are
2013-12-10T18:30Z / 2018-11-27T18:30Z / 2022-01-02T18:30Z.
"""
from __future__ import annotations

from services.gochara_rules.permission import (
    AD_ROWS, MD_ROWS, PD_ROWS, applicability, permission,
)

T_MARRIAGE = "2013-12-10T18:30:00Z"   # 2013-12-11 IST
T_FATHER = "2018-11-27T18:30:00Z"     # 2018-11-28 IST
T_TWINS = "2022-01-02T18:30:00Z"      # 2022-01-03 IST

# O-PP-2 named interior instants + the AD boundary (§4.0 half-open)
T1 = "2019-08-01T00:00:00Z"
T2 = "2021-01-01T00:00:00Z"
T_BOUNDARY = "2020-02-14T11:47:23Z"   # Mars→Rahu AD transition


def _lords(ctx):
    return (ctx["md"]["lord"], ctx["ad"]["lord"], ctx["pd"]["lord"])


# ── O-PP-1 (literal) — exact MD/AD/PD at the three event instants ───────────
def test_opp1_three_event_instants(chart):
    # PD lords printed in §4.0: Mercury, Venus, Venus — asserted, not merely
    # present.
    assert _lords(permission(chart, T_MARRIAGE, "marriage")["period_context"]) == \
        ("Mercury", "Ketu", "Mercury")
    assert _lords(permission(chart, T_FATHER, "bereavement")["period_context"]) == \
        ("Mercury", "Moon", "Venus")
    assert _lords(permission(chart, T_TWINS, "childbirth")["period_context"]) == \
        ("Mercury", "Rahu", "Venus")
    # row ids pinned per §4.0
    ctx = permission(chart, T_MARRIAGE, "marriage")["period_context"]
    assert ctx["md"]["row_id"] == "58afa482-4bce-42df-9c0d-0b5a2e02305e"
    assert ctx["ad"]["row_id"] == "133b4500-ad36-4fff-8814-c6b0b253ca05"
    assert ctx["pd"]["row_id"] == "6b843ad2-0759-4e7f-af7d-d39eac8b0325"
    # mutation: a constant or absent PD fails
    pds = {_lords(permission(chart, t, "marriage")["period_context"])[2]
           for t in (T_MARRIAGE, T_FATHER, T_TWINS)}
    assert len(pds) > 1 and None not in pds


def test_opp1_rows_are_half_open():
    # an instant t = end_iso belongs to the NEXT row
    assert MD_ROWS[0]["start_iso"] == "2010-08-18T15:50:23Z"
    ketu = AD_ROWS[0]
    # exactly at AD Ketu's end ⇒ Ketu's AD no longer running
    from services.gochara_rules.permission import _row_at
    assert _row_at(AD_ROWS, ketu["end_iso"], MD_ROWS[0]["row_id"]) is None
    pd_merc = PD_ROWS[0]
    assert _row_at(PD_ROWS, pd_merc["end_iso"], ketu["row_id"]) is None


# ── O-PP-2 (literal) — per-level licences at t1/t2 + boundary ────────────────
def test_opp2_per_level_licences(chart):
    p1 = permission(chart, T1, "marriage")["period_context"]
    p2 = permission(chart, T2, "marriage")["period_context"]
    # interior instants: t1 → MD Mercury / AD Mars / PD Saturn;
    # t2 → MD Mercury / AD Rahu / PD Saturn
    assert _lords(p1) == ("Mercury", "Mars", "Saturn")
    assert _lords(p2) == ("Mercury", "Rahu", "Saturn")
    assert p1["pd"]["row_id"] == "a4cf46db-fcb5-479c-8aab-ca87bcb551ff"
    assert p2["pd"]["row_id"] == "73eea5c0-631f-4b48-8c8f-483c910c6fde"
    # t1: ad.licence = scored (Mars: natal 7th-house occupant, Libra)
    assert p1["ad"]["licence"] == "scored"
    assert p1["ad"]["relation"] == "occupancy"
    # t2: ad.licence = testimony (Rahu: no ownership, no signature-house
    # occupancy, no dṛṣṭi (N-14); the Venus-dispositor chain is testimony-only
    # per D-PADMIT and cannot licence)
    assert p2["ad"]["licence"] == "testimony"
    assert p2["ad"]["relation"] == "dispositorship"
    # mutation: ad.licence = scored at t2 (testimony promoted) fails
    assert p2["ad"]["licence"] != "scored"
    # pd.licence = scored at both (Saturn: occupancy of the 7th)
    assert p1["pd"]["licence"] == p2["pd"]["licence"] == "scored"
    # md.licence identical at both (Mercury)
    assert p1["md"]["licence"] == p2["md"]["licence"]


def test_opp2_class_licence_same_at_both(chart):
    # the class-level licence is the union over levels — SAME at t1 and t2;
    # the oracle asserts on the AD level only
    c1 = permission(chart, T1, "marriage")["class_licence"]
    c2 = permission(chart, T2, "marriage")["class_licence"]
    assert c1 == c2 == "scored"
    # mutation: asserting the class-level licence DIFFERS between t1 and t2
    # (the v1.3 wording) fails
    assert not (c1 != c2)


def test_opp2_boundary_reads_rahu_ad(chart):
    # 2020-02-14T11:47:23Z is the Mars→Rahu AD transition; half-open
    # [start_iso, end_iso): the instant belongs to the Rahu AD
    ctx = permission(chart, T_BOUNDARY, "marriage")["period_context"]
    assert ctx["ad"]["lord"] == "Rahu"
    assert ctx["ad"]["row_id"] == "25a4b815-39bb-4b4a-b922-84a71778bb4f"
    # mutation: licensing at the boundary instant to the Mars AD fails the
    # half-open convention
    assert ctx["ad"]["lord"] != "Mars"
    just_before = "2020-02-14T11:47:22Z"
    assert permission(chart, just_before, "marriage")["period_context"]["ad"]["lord"] == "Mars"


# ── O-PP-3 (literal) — Aṣṭottarī absent, both failed conditions named ───────
def test_opp3_ashtottari_absent(chart):
    result = applicability(chart)
    assert result["system"] == "ashtottari"
    assert result["state"] == "absent"
    # BOTH failed conditions named: Rāhu 8th from lagna lord Mars; day birth
    # in Śukla pakṣa
    assert result["failed_conditions"] == [
        "rahu_8th_from_lagna_lord_mars_not_kendra_trikona",
        "day_birth_shukla_paksha_fails_krishna_reading",
    ]
    # mutation: absent-without-reasons, or a weighted vote, fails
    assert result["failed_conditions"]
    assert "vote" not in result and "weight" not in result
