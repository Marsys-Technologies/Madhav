"""Canonical ephemeris backend: Swiss Ephemeris ``.se1`` files (``swieph``).

SS ruling N-28 (TI-ephemeris-fix-001): the canonical backend is the Swiss
Ephemeris file corpus; Moshier is a fallback and must NEVER be silent.

pyswisseph never fails when its data files are missing: ``set_ephe_path``
accepts any string and ``calc_ut`` silently substitutes the built-in Moshier
analytic ephemeris, reporting the substitution ONLY in the returned flag.
Rows persisted under that substitution would still cite "Swiss Ephemeris"
(see INVESTIGATION_EPHEMERIS_BACKEND_v1_0: stored L1 / panchanga values were
bit-exact Moshier).  This module makes the backend an explicit, verified
precondition instead of ambient process state.

* ``SE_EPHE_PATH`` is the one variable the Swiss C library itself honours
  (``set_ephe_path(None)`` consults only it), so it is the single source of
  truth here.  ``SWE_EPHE_PATH`` (read by other, older code) is NOT consulted.
* The helpers are ``@serialized_swiss_state`` boundaries: the path is set and
  probed under ``SWISS_STATE_LOCK`` (the one process-wide lock in
  ``swiss_state.py``).
* Probe choice: two ``calc_ut`` calls with ``FLG_SWIEPH`` at J2000 -- the Sun
  (needs ``sepl_*.se1``) and TRUE_NODE (computed from the Moon, so it needs
  ``semo_*.se1``).  The returned flag, not the numeric value, is the
  discriminator: it carries exactly one of SEFLG_SWIEPH / SEFLG_MOSEPH /
  SEFLG_JPLEPH.  Why not the Moon itself (measured, pyswisseph 2.10.3.2): with
  ``semo`` missing, ``calc_ut(MOON)`` silently computes the Moshier Moon but
  STILL returns the SWIEPH flag -- the Moon's flag lies, TRUE_NODE's does not.
  Why not MEAN_NODE: it is analytic and reports SWIEPH under every path.  Two
  bodies because a directory holding only one of the two files must not pass.
  No SEFLG_SIDEREAL is requested, so the probe never depends on (or touches)
  the process's sidereal mode.
* Measured caveat: when ``SE_EPHE_PATH`` is in the process environment the C
  library ALSO searches it after ``set_ephe_path(<other dir>)``, so with the
  variable set (as in both images) the files are found from any path state.
  The explicit set + probe remain the defence for environments where it is not
  set or is wrong, and make the backend recorded, not assumed.
* Anything other than ``swieph`` raises ``SwissBackendError`` -- never a silent
  fallback.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, NamedTuple

from .swiss_state import serialized_swiss_state

_log = logging.getLogger(__name__)

# SHA-256 pins of the corpus (identical to Dockerfile / Dockerfile.pipeline); used only by
# the `python -m panchang_engine.swiss_backend` probe below.
_PINNED_SHA256 = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}

SE_EPHE_PATH_ENV = "SE_EPHE_PATH"
BACKEND_SWIEPH = "swieph"
_PROBE_JD_J2000 = 2451545.0


class SwissBackendError(RuntimeError):
    """The Swiss Ephemeris file backend (``swieph``) is not active.

    Deliberately NOT a ``PanchangEngineError`` (those map to client errors):
    a missing/unusable ephemeris corpus is a server-side configuration fault.
    """


class SwissBackend(NamedTuple):
    name: str
    path: str


def _import_swisseph() -> Any:
    try:
        import swisseph as swe
    except ImportError as exc:
        raise SwissBackendError(
            f"swisseph not available in this container: {exc}"
        ) from exc
    return swe


@serialized_swiss_state
def _observed_backend_name(swe: Any) -> str:
    """Probe the CURRENT process state; return the backend that actually served."""
    seen: set[str] = set()
    for body in (swe.SUN, swe.TRUE_NODE):
        _xx, retflag = swe.calc_ut(_PROBE_JD_J2000, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
        if retflag & swe.FLG_JPLEPH:
            seen.add("jpleph")
        elif retflag & swe.FLG_MOSEPH:
            seen.add("moseph")
        elif retflag & swe.FLG_SWIEPH:
            seen.add(BACKEND_SWIEPH)
        else:
            seen.add("unknown")
    return BACKEND_SWIEPH if seen == {BACKEND_SWIEPH} else "+".join(sorted(seen))


@serialized_swiss_state
def ensure_swiss_backend() -> SwissBackend:
    """Point swisseph at the configured ``.se1`` corpus and verify it is serving.

    Reads ``SE_EPHE_PATH`` (required).  Raises ``SwissBackendError`` when the
    variable is unset or the probe shows anything other than ``swieph``.
    Idempotent and cheap enough to call at every entry point; it deliberately
    re-sets the path every time because other code (PyJHora at import, legacy
    writers) mutates the same process-global.
    """
    swe = _import_swisseph()

    path = os.environ.get(SE_EPHE_PATH_ENV, "").strip()
    if not path:
        raise SwissBackendError(
            f"{SE_EPHE_PATH_ENV} is not set; refusing to run on the implicit "
            "Moshier fallback (Swiss .se1 files are the canonical ephemeris). "
            "Point it at a directory holding the three SHA-pinned .se1 files "
            "(sepl_18, semo_18, seas_18; see Dockerfile.pipeline); in tests set "
            "MARSYS_TEST_SE1_DIR or SWE_EPHE_PATH to that directory"
        )
    swe.set_ephe_path(path)
    observed = _observed_backend_name(swe)
    if observed != BACKEND_SWIEPH:
        raise SwissBackendError(
            f"Swiss Ephemeris file backend not active for {SE_EPHE_PATH_ENV}={path!r}: "
            f"probe reported {observed!r}; refusing the silent fallback"
        )
    return SwissBackend(BACKEND_SWIEPH, path)


@serialized_swiss_state
def backend_name() -> str:
    """Return ``'swieph'`` iff the process is CURRENTLY serving from ``.se1`` files.

    A real probe of live state (it does not set the path), so a writer that
    records this in its notes is reporting what the process was doing, not what
    it was configured to do.  Raises ``SwissBackendError`` otherwise.
    """
    swe = _import_swisseph()

    observed = _observed_backend_name(swe)
    if observed != BACKEND_SWIEPH:
        raise SwissBackendError(
            f"Swiss Ephemeris file backend not active: probe reported {observed!r}"
        )
    return BACKEND_SWIEPH


def backend_note() -> str:
    """Uniform ``WriterResult.notes`` fragment: ``ephemeris_backend=swieph``."""
    return f"ephemeris_backend={backend_name()}"


def records_swiss_backend(cls):
    """Class decorator for a registered ``WriterBase`` subclass that computes
    with swisseph: assert the ``.se1`` backend before the body runs and record
    the PROBED backend in ``WriterResult.notes`` after it.

    Stays inside the FROZEN orchestrator contract: it only wraps the writer's
    own ``run`` / ``run_substep`` and appends to the ``notes`` the writer already
    returns -- no orchestrator, ``asset_runner`` or receipt change.  A backend
    that is not ``swieph`` at either end raises ``SwissBackendError`` (the build
    fails closed rather than recording rows computed on the Moshier fallback).
    """

    def wrap(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def guarded(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
            ensure_swiss_backend()
            result = method(self, ctx, *args, **kwargs)
            note = backend_note()
            result.notes = f"{result.notes}; {note}" if result.notes else note
            # The orchestrator does not persist WriterResult.notes, so the probed
            # backend is also LOGGED (INFO, visible in the Cloud Run job logs) -- the
            # observable trace that a decorated writer ran on swieph.
            _log.info("%s ephemeris_backend=%s path=%s", getattr(cls, "asset_id", cls.__name__),
                      BACKEND_SWIEPH, os.environ.get(SE_EPHE_PATH_ENV, ""))
            return result

        return guarded

    for name in ("run", "run_substep"):
        method = cls.__dict__.get(name)
        if method is not None:
            setattr(cls, name, wrap(method))
    cls.records_swiss_backend = True
    return cls


def _probe_main() -> int:
    """`python -m panchang_engine.swiss_backend`: print one JSON line proving the
    backend of THIS image/process (read-only; no DB, no network).  Exit 0 only when
    the backend is swieph AND all three corpus files match their SHA-256 pins."""
    out: dict[str, Any] = {"se_ephe_path": os.environ.get(SE_EPHE_PATH_ENV, "")}
    ok = False
    try:
        got = ensure_swiss_backend()
        out["backend"] = got.name
        files = {}
        for name, pin in _PINNED_SHA256.items():
            digest = hashlib.sha256((Path(got.path) / name).read_bytes()).hexdigest()
            files[name] = {"sha256": digest, "pinned": digest == pin}
        out["files"] = files
        ok = all(f["pinned"] for f in files.values())
    except Exception as exc:  # report, then fail closed via the exit code
        out["backend"] = None
        out["error"] = f"{type(exc).__name__}: {exc}"
    swe = _import_swisseph()
    out["swisseph_version"] = swe.version
    out["ok"] = ok
    print(json.dumps(out, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_probe_main())
