"""Shared process boundary for Swiss Ephemeris mutable global state.

Swiss Ephemeris stores sidereal mode and ephemeris path in process-global C
state. Every in-process L0 service must hold this re-entrant lock across mode
selection and all dependent calculations, not merely around ``set_sid_mode``.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from inspect import iscoroutinefunction
from typing import Iterator
from threading import RLock
from typing import Callable, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")

SWISS_STATE_LOCK = RLock()


@contextmanager
def swiss_state_scope() -> Iterator[None]:
    """Hold the one process-wide Swiss Ephemeris critical section.

    This explicit scope is for operations whose state selection and dependent
    calculations span helper calls.  The same ``RLock`` backs the decorator,
    so nested public and low-level entry points remain re-entrant.
    """

    with SWISS_STATE_LOCK:
        yield


def serialized_swiss_state(fn: Callable[P, R]) -> Callable[P, R]:
    """Serialize a complete Swiss-state-dependent operation."""

    if iscoroutinefunction(fn):
        @wraps(fn)
        async def async_wrapped(*args: P.args, **kwargs: P.kwargs):
            with SWISS_STATE_LOCK:
                return await fn(*args, **kwargs)

        setattr(async_wrapped, "__swiss_state_serialized__", True)
        setattr(async_wrapped, "__swiss_state_lock__", SWISS_STATE_LOCK)
        return async_wrapped  # type: ignore[return-value]

    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        with SWISS_STATE_LOCK:
            return fn(*args, **kwargs)

    setattr(wrapped, "__swiss_state_serialized__", True)
    setattr(wrapped, "__swiss_state_lock__", SWISS_STATE_LOCK)
    return wrapped
