"""A synthetic sky for the vedha unit tests (SR-VEDHA-RESIDENCE-SOURCE): residence rows `(body, "span:<sign>", t_in, t_out | None)` become the
position source the builder (`position_at(body, t)`) and the verifier (`longitude_at(graha, t)`) now derive their residence from.

A body is at the middle of its sign while a row says so. The ephemeris "cannot answer" where no row covers the instant AFTER the last row ends
(the earliest row extends backwards without limit, a row with no end forwards): that is how a test makes a stretch of unknown residence.
Nothing here is a stand-in for the Swiss ephemeris' behaviour; the real-ephemeris oracles are in `test_od1_vedha_residence.py`."""
from __future__ import annotations

from services.gochara_kernel import vedha_verifier as vv


def _spans(rows):
    per: dict[str, list] = {}
    for body, target, a, b in rows:
        per.setdefault(body.lower(), []).append((a, b, int(str(target).split(":")[1])))
    for spans in per.values():
        spans.sort(key=lambda s: s[0])
    return per


def _lookup(per, body: str, t):
    spans = per.get(body.lower(), [])
    for i, (a, b, sign) in enumerate(spans):
        if (i == 0 or a <= t) and (b is None or t < b):
            return (sign - 1) * 30.0 + 15.0
    return None


def position_at_for(rows):
    """The builder's `position_at(body, t)`."""
    per = _spans(rows)
    calls: list = []

    def position_at(body, t):
        calls.append(body)
        lon = _lookup(per, body, t)
        if lon is None:
            raise RuntimeError(f"synthetic sky: {body} cannot be answered at {t.isoformat()}")
        return lon
    position_at.calls = calls
    return position_at


def longitude_at_for(rows):
    """The verifier's `longitude_at(graha, t)`."""
    per = _spans(rows)

    def longitude_at(graha, t):
        lon = _lookup(per, graha, t)
        if lon is None:
            raise vv.EphemerisUnavailable(f"synthetic sky: {graha} cannot be answered at {t.isoformat()}")
        return lon
    longitude_at.max_speed_dps = 3600.0       # a synthetic body jumps from sign to sign: the leap-frog must step in minutes, not months
    return longitude_at
