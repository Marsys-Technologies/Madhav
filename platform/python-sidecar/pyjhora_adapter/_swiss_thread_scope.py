"""Per-thread Swiss Ephemeris scope: select the sidereal mode AND the ephemeris path on the CALLING thread.

Why this exists (SWE_THREAD_AUDIT, 2026-10-03; ``panchang_engine/swiss_backend.py`` DESIGN RULE):
on LINUX pyswisseph keeps the sidereal mode (``set_sid_mode``) and the ephemeris path
(``set_ephe_path``) PER THREAD.  A fresh thread starts at the library default (Fagan-Bradley, no
path); a reused orchestrator pool thread keeps whatever ayanamsha the PREVIOUS task on it left.  A
function that calls ``swe.calc_ut(..., FLG_SIDEREAL)`` / ``drik.*`` and merely relies on a mode that
ANOTHER function set earlier therefore computes under the wrong ayanamsha as soon as it is reached
on a thread that did not run that other function (reordering, a substep resumed on a new thread, a
direct call).  macOS keeps the state process-wide, so it can never show the problem; the tests in
``tests/test_swiss_thread_scope.py`` run real threads and are meaningful on Linux (CI).

``with_sidereal_mode`` is the one reviewed idiom: put it INSIDE the function that does the raw
sidereal computation, so the mode holds on every path.  It

* holds the process-wide Swiss lock (``swiss_state_scope``, an RLock: re-entrant under the
  ``@serialized_swiss_state`` decorators) for the whole ``with`` body, so the mode and the
  calculations that depend on it are one critical section;
* pins and verifies the ephemeris path on this thread through the existing fail-closed helper
  (``panchang_engine.swiss_backend.ensure_swiss_backend``, TI-ephemeris-fix-001 / #2860): it raises
  ``SwissBackendError`` when ``SE_EPHE_PATH`` is unset or the probe is not ``swieph``, and
  ``OutOfCorpusRangeError`` for a JD outside the corpus window -- never a silent Moshier fallback.
  The path is pinned BEFORE the mode is set, so a failed pin leaves the thread's mode untouched;
* selects the sidereal mode on the calling thread: ``swe.set_sid_mode`` for a raw-swisseph caller, or
  (``via_jhora=True``) ``drik.set_ayanamsa_mode`` for a PyJHora caller, which makes the identical
  ``swe.set_sid_mode`` call AND records PyJHora's own ambient default exactly as every adapter entry
  point already does.

It does NOT restore the previous mode on exit: the repository convention is "every entry point sets
its own mode"; restoring would only re-create ambient state for the next order-dependent reader.
Idempotent: when the thread already holds the requested mode the values are byte-identical.

Placement: ``pyjhora_adapter`` (not ``ga_writers``) because ``ga_writers`` already imports
``pyjhora_adapter`` and the adapter must never import the writers above it; this module imports only
``panchang_engine`` and the sibling ``_ayanamsha`` map (PyJHora is imported lazily, only for
``via_jhora=True``), so there is no import cycle for either consumer.  It deliberately lives outside
``panchang_engine/`` and ``services/gochara_v3/``.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from panchang_engine.swiss_backend import (
    OutOfCorpusRangeError,
    SwissBackend,
    SwissBackendError,
    WindowUncheckedError,
    ensure_swiss_backend,
)
from panchang_engine.swiss_state import swiss_state_scope

from ._ayanamsha import resolve_mode

# The ephemeris-BACKEND failures: an unset ``SE_EPHE_PATH``, a probe that is not ``swieph``, a JD outside
# the corpus window, an unchecked window.  They mean "the INFRASTRUCTURE cannot compute", never "this
# value is not defined", so a per-subject / per-value handler must let them propagate and fail the build
# instead of turning them into a floored / null / default row (SS ruling, 2026-10-03).  The subclass
# relations (``WindowUncheckedError`` and ``OutOfCorpusRangeError`` are ``SwissBackendError``) mean the
# first member alone would catch all three; the tuple names each so the intent survives a refactor of
# the hierarchy.  Use it as ``except BACKEND_FAILURE_ERRORS: raise`` BEFORE any broad ``except Exception``.
# (``services.gochara_kernel.knots.EphemerisBackendError`` is deliberately NOT here: it is raised only by
# the Kala kernel's own ``calc_ut`` wrappers, which no L1 writer calls; importing it would couple L1 to Kala.)
BACKEND_FAILURE_ERRORS: tuple[type[BaseException], ...] = (
    SwissBackendError,
    OutOfCorpusRangeError,
    WindowUncheckedError,
)


@contextmanager
def with_sidereal_mode(
    ayanamsha_id: str | None = "lahiri",
    *jds: float,
    via_jhora: bool = False,
) -> Iterator[SwissBackend]:
    """Pin the ``.se1`` path and select ``ayanamsha_id``'s sidereal mode on THIS thread for the body.

    ``ayanamsha_id``: any id ``pyjhora_adapter._ayanamsha.resolve_mode`` knows (``None`` = lahiri);
    an unknown id raises ``ValueError`` BEFORE any Swiss state is touched.
    ``jds``: the Julian days the body will compute at; forwarded to ``ensure_swiss_backend`` so an
    out-of-corpus date raises instead of being served by Moshier.
    ``via_jhora``: select the mode through ``drik.set_ayanamsa_mode`` (PyJHora callers) instead of
    ``swe.set_sid_mode`` (raw swisseph callers).
    """
    mode_name, sidm = resolve_mode(ayanamsha_id)
    with swiss_state_scope():
        backend = ensure_swiss_backend(*jds)
        if via_jhora:
            from ._jhora import drik

            drik.set_ayanamsa_mode(mode_name)
        else:
            import swisseph as swe

            swe.set_sid_mode(sidm)
        yield backend
