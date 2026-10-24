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

# ── ephemeris-path change counter (SR-EPHE-PATH-ONCE) ───────────────────────
# ``swe.set_ephe_path`` closes the library's open ephemeris files, so re-issuing it before EVERY probe costs
# ≈75 µs against ≈0.24 µs for the probe itself.  A caller that wants to set the path once per thread therefore
# needs to know whether ANY caller in the process has set it since: this counter is bumped by every
# ``swe.set_ephe_path`` call made through the module attribute (the tracker below wraps it once, idempotently).
# It carries no path and no policy — each caller keeps its own memo and compares counters; ``set_sid_mode`` is
# deliberately NOT tracked (it is ≈0.1 µs, and callers keep re-setting it on every probe).
_EPHE_PATH_GENERATION = 0


def ephe_path_generation() -> int:
    """How many times ``swe.set_ephe_path`` has been called in this process (any thread, any caller)."""
    return _EPHE_PATH_GENERATION


def _install_ephe_path_tracker() -> None:
    try:
        import swisseph as swe
    except ImportError:          # pragma: no cover - the sidecar always has pyswisseph
        return
    original = swe.set_ephe_path
    if getattr(original, "__ephe_path_tracked__", False):
        return

    @wraps(original)
    def tracked_set_ephe_path(*args, **kwargs):
        global _EPHE_PATH_GENERATION
        try:
            return original(*args, **kwargs)
        finally:
            _EPHE_PATH_GENERATION += 1

    tracked_set_ephe_path.__ephe_path_tracked__ = True  # type: ignore[attr-defined]
    swe.set_ephe_path = tracked_set_ephe_path


_install_ephe_path_tracker()


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
