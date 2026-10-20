"""P06 landing gate for the P06b suites that run on P06's migration chain (1305 / 1306 / 1308) and its builder module.

P06b was prepared before P06 landed (00_ARCHITECTURE/briefs/kalayantra/packets/P06B_PREBUILD_v1_0.md, "Source custody and landing order": P06 must
land before P06b's final integration). Until then the P06-dependent tests cannot build their world, and a hard error would say nothing about P06b.
The gate is computed, never switched by hand (§N.8):

  * every P06 prerequisite absent  -> skip, naming each missing item (visible with `-rs`);
  * every prerequisite present     -> the suites run unconditionally;
  * only some present              -> FAIL: a half-landed P06 is a defect, not a reason to skip.
"""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import pytest

MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
P06_MIGRATIONS = ("1305_*.sql", "1306_gochara_expected_class_census.sql", "1308_gochara_near_miss_storage.sql")


def prerequisites() -> dict[str, bool]:
    """Presence of each P06 artifact the P06b suites consume."""
    from . import test_a53_inventory as base
    present = {f"migration {pattern}": bool(list(MIGRATIONS.glob(pattern))) for pattern in P06_MIGRATIONS}
    present["module services.gochara_kernel.near_miss"] = importlib.util.find_spec("services.gochara_kernel.near_miss") is not None
    present["create_am5_database(apply_1305=...)"] = "apply_1305" in inspect.signature(base.create_am5_database).parameters
    return present


def classify(present: dict[str, bool]) -> str:
    """'absent' | 'partial' | 'complete' for a presence map."""
    have = sum(1 for ok in present.values() if ok)
    return "complete" if have == len(present) else "absent" if have == 0 else "partial"


def require_p06(*, module_level: bool = False) -> None:
    """Call before building a P06-dependent world (`module_level=True` at import time): returns when P06 has landed, skips while it is wholly absent,
    fails when only partly present."""
    present = prerequisites()
    state = classify(present)
    if state == "complete":
        return
    missing = [name for name, ok in present.items() if not ok]
    if state == "partial":
        pytest.fail("P06 is only partly present, missing: " + "; ".join(missing))
    pytest.skip("NOT_RUN: P06 has not landed on this base (P06B_PREBUILD_v1_0 landing order); missing: " + "; ".join(missing), allow_module_level=module_level)
