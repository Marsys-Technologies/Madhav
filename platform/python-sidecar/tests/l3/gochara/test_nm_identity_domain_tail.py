"""Near-miss verifier — a rootless stretch whose station lies BEFORE the identity domain and whose tail runs into the horizon's first days
(SR-NEARMISS-DOMAIN-TAIL; the 12-class TR's Saturn x natal-Venus aspect object: station 1997-12-17, domain opens 1998-01-01, tail ends 1998-01-08).

Claims (each has its own planted reversion, see the last line of each docstring):
  1. such a tail (no station inside the domain) is DISCLOSED, not a generation-failing `near_miss_unresolved`;
  2. a crossing stretch WITH a station inside the domain stays REFUSED (the builder refuses it by name);
  3. a span too short to show a station is never disclosed (never infer absence);
  4. the disclosure is COUNTED in what `verify_generation` returns (and so in the verification report), under the verifier's existing reason name.
Curves are analytic parabolas (Saturn-slow: edge speed ~0.03 deg/day), worked by hand; no database.
"""
from __future__ import annotations

from datetime import timedelta

from services.gochara_kernel import near_miss_verifier as nm
from services.gochara_kernel.near_miss_verifier import utc

DOM = (utc(1998, 1, 1), utc(2085, 1, 1))
STATION_BEFORE = utc(1997, 12, 17)                                  # 15 days before the domain opens
ORB, CENTRE, C = 1.0, 100.0, 0.5
K = (ORB - C) / 22.0 ** 2                                            # the band is left 22 days after the station, i.e. 7 days into the domain
REASON = "rootless_stretch_crosses_identity_domain"


def _derive(station):
    pos = lambda b, t: (CENTRE + C + K * ((t - station).total_seconds() / 86400.0) ** 2) % 360.0      # noqa: E731
    found = nm.derive_near_misses(pos, "saturn", [CENTRE], DOM[0], DOM[0] + timedelta(days=300), orb_deg=ORB)
    (rec,) = [r for r in found if r["clipped"]]
    return pos, nm._follow_domain_edge(pos, "saturn", [CENTRE], ORB, rec, DOM)


def _refused(kept):
    return [x for x in nm.compare_sets(kept, [], junction_source=([], False), expected_orb_deg=ORB, expected_object_id="o") if x.startswith("near_miss_unresolved")]


def test_a_tail_whose_station_precedes_the_domain_is_disclosed_not_refused():
    """Reversion: `split_identity_domain_tails` returns `(derived, [])` -> this fails (the stretch stays in `kept` and is refused)."""
    pos, fol = _derive(STATION_BEFORE)
    assert fol["state"] == "unresolved" and fol["reason"] == REASON and fol["station_in_domain"] is False
    assert fol["t_in"] == DOM[0] and DOM[0] + timedelta(days=6) < fol["t_out"] < DOM[0] + timedelta(days=8)          # the disclosed piece is the clipped one: 1998-01-01 -> 1998-01-08
    kept, tails = nm.split_identity_domain_tails([fol])
    assert kept == [] and tails == [fol]
    assert _refused(kept) == []


def test_a_crossing_stretch_with_a_station_inside_the_domain_stays_refused():
    """Reversion: `_station_in_span` always answers False -> this fails (the in-domain-station stretch would be disclosed instead of refused)."""
    pos, fol = _derive(DOM[0] + timedelta(days=10))                   # the station is inside the domain
    assert fol["reason"] == REASON and fol["station_in_domain"] is True
    kept, tails = nm.split_identity_domain_tails([fol])
    assert tails == [] and kept == [fol]
    assert _refused(kept) and all(REASON in x for x in _refused(kept))


def test_a_span_too_short_to_show_a_station_is_not_disclosed():
    """Reversion: the `n < 3` guard in `_station_in_span` answers False -> this fails."""
    assert nm._station_in_span(lambda b, t: 0.0, "saturn", DOM[0], DOM[0] + timedelta(days=2)) is True


def test_the_disclosure_is_counted_under_the_existing_reason_name():
    """Reversion: `tail_disclosure` reports a constant count (e.g. 0) -> this fails; a new reason string would fail the name assertion."""
    pos, fol = _derive(STATION_BEFORE)
    _, tails = nm.split_identity_domain_tails([fol])
    recs = [nm.tail_record("obj-1", "saturn", "aspect", r) for r in tails]
    out = nm.tail_disclosure(recs)
    assert out["identity_domain_tail_count"] == 1 == len(out["identity_domain_tails"])
    (rec,) = out["identity_domain_tails"]
    assert rec["reason"] == REASON and rec["object_id"] == "obj-1" and rec["body"] == "saturn" and rec["relation"] == "aspect" and rec["station_in_domain"] is False
    assert rec["t_in"].startswith("1998-01-01") and rec["t_out"].startswith("1998-01-0")
    assert nm.tail_disclosure([]) == {"identity_domain_tails": [], "identity_domain_tail_count": 0}              # a measured zero, not an absence
