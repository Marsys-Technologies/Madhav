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
T_BOUNDARY = "2020-02-14T13:43:56Z"   # Mars→Rahu AD transition


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
    assert ctx["md"]["row_id"] == "1d1a80c0-53c6-5ff7-930a-52ff0f306cae"
    assert ctx["ad"]["row_id"] == "2103a226-b814-5ec7-b987-dffb421d5288"
    assert ctx["pd"]["row_id"] == "65e30373-9db8-5606-a2bb-7c540114e135"
    # mutation: a constant or absent PD fails
    pds = {_lords(permission(chart, t, "marriage")["period_context"])[2]
           for t in (T_MARRIAGE, T_FATHER, T_TWINS)}
    assert len(pds) > 1 and None not in pds


def test_opp1_rows_are_half_open():
    # an instant t = end_iso belongs to the NEXT row
    assert MD_ROWS[0]["start_iso"] == "2010-08-18T17:46:56Z"
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
    assert p1["pd"]["row_id"] == "d4d08aca-8995-51f3-a8ba-f9238a5311b3"
    assert p2["pd"]["row_id"] == "f72e343c-b877-516b-a089-54494031aa2d"
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
    # md.licence = testimony at both (Mercury: no direct 7th relation; its
    # dispositor Saturn occupies Libra, the 7th from the Aries lagna —
    # non-node dispositorship is testimony per the spec C5 relation-kind
    # table: no clause found in Phaladīpikā XX.34–38, PG249:C1/PG250:C1)
    assert p1["md"]["licence"] == p2["md"]["licence"] == "testimony"
    assert p1["md"]["relation"] == p2["md"]["relation"] == "dispositorship"
    # the testimony names the dispositor relation and its record id, and is
    # identical at t1 and t2 (same MD row, same natal relation)
    assert "Saturn" in p1["md"]["detail"] and "7th" in p1["md"]["detail"]
    assert "sha256:" in p1["md"]["detail"]
    assert p1["md"] == p2["md"]
    # mutation: md.licence = none (the defect) or scored fails
    assert p1["md"]["licence"] not in ("none", "scored")


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
    # 2020-02-14T13:43:56Z is the Mars→Rahu AD transition; half-open
    # [start_iso, end_iso): the instant belongs to the Rahu AD
    ctx = permission(chart, T_BOUNDARY, "marriage")["period_context"]
    assert ctx["ad"]["lord"] == "Rahu"
    assert ctx["ad"]["row_id"] == "a91faefa-f0d9-5a5d-950c-0adafb276fc7"
    # mutation: licensing at the boundary instant to the Mars AD fails the
    # half-open convention
    assert ctx["ad"]["lord"] != "Mars"
    just_before = "2020-02-14T13:43:55Z"
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
