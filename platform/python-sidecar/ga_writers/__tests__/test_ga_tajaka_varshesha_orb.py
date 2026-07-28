"""
ŚUDDHA-VĀCA P0-9 (lane:ga-tajaka) — Varshesha (year-lord) candidate-scoring
aspect test used a hardcoded flat 7-degree orb instead of each graha's own
classical deeptamsa orb, even though the SAME file already fixed this exact
defect class for a sibling check (`_tajik_yogas`'s mutual-aspect precondition,
line ~384) under the M-13 fix: "the flat 7 degree orb previously used here
ignored this per-graha spread". The Varshesha `aspects_lagna` test at line 530
was never updated to match — it kept the flat 7 degree constant this file's
own DEEPTAMSA table exists specifically to replace.

Deeptamsa (orb of "light"/influence) is a fixed classical constant per graha
(Tajika Nilakanthi tradition) — it does not vary per chart, so there is no
per-chart L1 chart_facts fact to fetch here (unlike e.g. required_rupa); the
correct fix is consistency with this file's own already-established DEEPTAMSA
table (§N.7.3 — no wrapper-local constant may shadow the correct value; here
the correct classical value already lives in this same module and this one
call site simply never got updated to use it).

Practical effect: at a 10-degree separation from the Varsha-Lagna, the flat 7
degree orb wrongly excludes Sun (real deeptamsa 15) from "aspects the Lagna" —
potentially flipping which graha is selected as Varshesha under the
Tajik-classical method (`_tc_winner`), which grades the entire annual
(varshaphal) chart.
"""
from __future__ import annotations

import ga_writers.ga_tajaka_writer as sut


def test_sun_at_10deg_separation_aspects_lagna_under_its_own_15deg_deeptamsa():
    """Sun's classical deeptamsa is 15deg. A 10deg separation from the Varsha-Lagna
    IS within Sun's own orb and must count as aspecting — the flat 7deg orb this
    replaces would wrongly say no (10 > 7)."""
    assert sut.DEEPTAMSA["Sun"] == 15.0
    assert sut._aspects_lagna("Sun", full_long=100.0, varsha_lagna_long=90.0) is True


def test_saturn_at_10deg_separation_does_not_aspect_lagna_under_its_own_9deg_deeptamsa():
    """Saturn's classical deeptamsa is 9deg — narrower than the flat 7deg this
    replaces would have (coincidentally) rejected too, but for the wrong reason;
    confirm the real per-graha value (9), not 7, is what's actually applied."""
    assert sut.DEEPTAMSA["Saturn"] == 9.0
    assert sut._aspects_lagna("Saturn", full_long=100.0, varsha_lagna_long=90.0) is False


def test_saturn_at_8deg_separation_aspects_lagna_under_its_own_9deg_orb_but_not_the_old_flat_7():
    """The decisive differentiator: 8deg is OUTSIDE the old flat 7deg orb but
    INSIDE Saturn's real 9deg deeptamsa — this must now read as aspecting."""
    assert sut._aspects_lagna("Saturn", full_long=98.0, varsha_lagna_long=90.0) is True


def test_mercury_at_7point5deg_separation_does_not_aspect_lagna_regression_check():
    """Mercury's own deeptamsa (7.0) happens to equal the old flat constant —
    confirms the fix doesn't silently change behavior for grahas whose classical
    orb happens to coincide with 7."""
    assert sut.DEEPTAMSA["Mercury"] == 7.0
    assert sut._aspects_lagna("Mercury", full_long=97.5, varsha_lagna_long=90.0) is False
