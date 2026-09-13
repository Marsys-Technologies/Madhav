"""Shared process boundary for Swiss Ephemeris mutable global state.

Swiss Ephemeris stores sidereal mode and ephemeris path in process-global C
state. Every in-process L0 service must hold this re-entrant lock across mode
selection and all dependent calculations, not merely around ``set_sid_mode``.
"""
from __future__ import annotations

from functools import wraps
from threading import RLock
from typing import Callable, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")

SWISS_STATE_LOCK = RLock()


def serialized_swiss_state(fn: Callable[P, R]) -> Callable[P, R]:
    """Serialize a complete Swiss-state-dependent operation."""

    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        with SWISS_STATE_LOCK:
            return fn(*args, **kwargs)

    setattr(wrapped, "__swiss_state_serialized__", True)
    return wrapped
