"""Physical noon-UT daily rows for integration tests that invoke Swiss refinement.

The DATE epoch is L0's declared noon convention, not the overlay's civil-date
midnight seam. Both true and mean node rows are actual Swiss results.
"""
from datetime import timedelta
from functools import lru_cache
import os

import swisseph as swe

from brahmagyan.l0_ephemeris import _tropical_to_jd


@lru_cache(maxsize=8)
def real_ephemeris_rows(start, days):
    swe.set_ephe_path(os.environ["SE_EPHE_PATH"])
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    bodies = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS, "Saturn": swe.SATURN,
        "Rahu": swe.TRUE_NODE, "Ketu": swe.TRUE_NODE,
    }
    rows = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        jd = _tropical_to_jd(day)
        for body, code in bodies.items():
            values, retflag = swe.calc_ut(jd, code, flags)
            assert retflag & swe.FLG_SWIEPH, (body, day, retflag)
            node = body in ("Rahu", "Ketu")
            turn = 180.0 if body == "Ketu" else 0.0
            rows.append((day, body, "tropical", (values[0] + turn) % 360.0,
                         values[3], values[3] < 0, "true" if node else None))
            if node:
                mean, retflag = swe.calc_ut(jd, swe.MEAN_NODE, flags)
                assert retflag & swe.FLG_SWIEPH, (body, day, retflag)
                rows.append((day, body, "tropical", (mean[0] + turn) % 360.0,
                             mean[3], mean[3] < 0, "mean"))
    return tuple(rows)
