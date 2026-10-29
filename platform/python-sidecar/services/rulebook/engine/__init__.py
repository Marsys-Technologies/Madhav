"""Rule Book engine — packets E3/E4: evaluator, day atom, unit manifest, date-range driver.

Pure Python (stdlib only at import time). Database access lives in ``dbload`` and is
read-only; Swiss Ephemeris is reached only through ``calendar.PanchangEngineSunrise``
(the repo's own panchang_engine), imported lazily.

Nothing here scores, ranks, weights, nulls or tests anything: the yardstick scorer
and its matched-random nulls are held (SUR-RB-1).
"""

from __future__ import annotations

ENGINE_PACKAGE = "services.rulebook.engine"
