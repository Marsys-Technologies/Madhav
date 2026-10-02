"""Shared helper: bind Stream B's ACTUAL 1.1.0 successor rows (#2897 / #2901 / #2907) beside the 1.0.0
rows, exactly as a deliberate edit of the binder's explicit reference tuples would — nothing synthetic.

The production default (`BOUND_PATH_REFS`) stays @1.0.0 until the 1.1.0 rows are accepted; these tests run the
ACTUAL rows through binding, SQL read-back, inventory and record evaluation without changing that default.
"""
from __future__ import annotations

from services.gochara_kernel import rule_registry as rr

SUCCESSOR_PATHS = (("P2", "1.1.0"), ("P3", "1.1.0"), ("P4", "1.1.0"), ("P5", "1.1.0"))
SUCCESSOR_FACTORS = (("activity_kernel", "1.1.0"), ("graduated_drishti", "1.1.0"),
                     ("vedha_attenuation", "1.1.0"))


def bind_successors(monkeypatch) -> None:
    monkeypatch.setattr(rr, "BOUND_PATH_REFS", rr.BOUND_PATH_REFS + SUCCESSOR_PATHS)
    monkeypatch.setattr(rr, "BOUND_FACTOR_REFS", rr.BOUND_FACTOR_REFS + SUCCESSOR_FACTORS)
