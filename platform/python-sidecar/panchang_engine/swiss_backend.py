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
* CORPUS WINDOW (SS ruling): the pinned ``*_18.se1`` files cover 1800-01-01 to
  2400-01-01 only; outside that window the C library silently computes with
  Moshier even when the files are present (measured: Sun/Moon/Mars flag MOSEPH
  from 1799-12-31 and from 2450).  The J2000 probe says nothing about other dates,
  so every entry point that knows its dates passes them in
  (``ensure_swiss_backend(jd, ...)`` / ``backend_name(jd, ...)``) and a jd outside
  ``SWIEPH_WINDOW_JD`` raises ``OutOfCorpusRangeError`` (named ``out_of_corpus_range``,
  a ``SwissBackendError`` AND a ``panchang_engine.OutOfRangeError`` so the existing
  422 handlers disclose it) -- the helper never reports swieph for such a date.
  Decorated writers check the chart's lifetime (birth .. birth + 125 years) before
  their body runs, i.e. before any write.
* Vocabulary note: ``pipeline/orchestrator/service_probes.py`` (L0 registry health
  probe) uses the label ``swiss_ephemeris_file``, probes the Sun only and reads
  ``SWE_EPHE_PATH``; this module uses ``swieph``, Sun + TRUE_NODE and
  ``SE_EPHE_PATH``.  They are deliberately not merged here (editing
  ``service_probes.py`` would move the probe digest and every L0/bg_* digest); with
  ``semo`` missing the probe can pass while writers refuse -- the stricter result is
  the one that gates writes.
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

from .exceptions import OutOfRangeError
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
# JD of 1800-01-01 00:00 and 2400-01-01 00:00: the span of the pinned *_18.se1 files.
SWIEPH_WINDOW_JD = (2378496.5, 2597641.5)
# Writers' chart horizon (dashas 120y, ka_sangam 100y, ka_kshetra 100y, tithi-pravesha 120 rows).
LIFETIME_HORIZON_YEARS = 125


class SwissBackendError(RuntimeError):
    """The Swiss Ephemeris file backend (``swieph``) is not active.

    Deliberately NOT a ``PanchangEngineError`` (those map to client errors):
    a missing/unusable ephemeris corpus is a server-side configuration fault.
    """


class OutOfCorpusRangeError(SwissBackendError, OutOfRangeError):
    """A requested date lies outside the pinned corpus window (``out_of_corpus_range``).

    Also an ``OutOfRangeError`` so the routers' existing ``except (ValidationError,
    OutOfRangeError)`` -> HTTP 422 handlers disclose it to clients.
    """

    code = "out_of_corpus_range"


def _require_in_window(jds: tuple[float, ...]) -> None:
    lo, hi = SWIEPH_WINDOW_JD
    for jd in jds:
        if not (lo <= float(jd) <= hi):
            raise OutOfCorpusRangeError(
                f"out_of_corpus_range: JD {float(jd):.1f} is outside the Swiss Ephemeris file "
                f"window {lo}..{hi} (1800-01-01..2400-01-01); refusing to report swieph for it "
                "(the library would silently use Moshier there)"
            )


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
def ensure_swiss_backend(*jds: float) -> SwissBackend:
    """Point swisseph at the configured ``.se1`` corpus and verify it is serving.

    Reads ``SE_EPHE_PATH`` (required).  Raises ``SwissBackendError`` when the
    variable is unset or the probe shows anything other than ``swieph``, and
    ``OutOfCorpusRangeError`` when any given Julian day lies outside the corpus
    window (see the module docstring: the J2000 probe cannot vouch for other dates).
    Idempotent and cheap enough to call at every entry point; it deliberately
    re-sets the path every time because other code (PyJHora at import, legacy
    writers) mutates the same process-global.
    """
    _require_in_window(jds)
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
def backend_name(*jds: float) -> str:
    """Return ``'swieph'`` iff the process is CURRENTLY serving from ``.se1`` files
    for the given Julian days (none given = the J2000 probe only).

    A real probe of live state (it does not set the path), so a writer that
    records this in its notes is reporting what the process was doing, not what
    it was configured to do.  Raises ``SwissBackendError`` otherwise and
    ``OutOfCorpusRangeError`` for a date outside the corpus window -- it never
    reports swieph for a date the library would serve with Moshier.
    """
    _require_in_window(jds)
    swe = _import_swisseph()

    observed = _observed_backend_name(swe)
    if observed != BACKEND_SWIEPH:
        raise SwissBackendError(
            f"Swiss Ephemeris file backend not active: probe reported {observed!r}"
        )
    return BACKEND_SWIEPH


def reassert_swiss_backend_nowait() -> bool:
    """Best-effort re-assert for use at MODULE IMPORT time (``pyjhora_adapter._jhora``).

    Never blocks and never raises: a module body runs while the interpreter holds the
    module's import lock, so waiting for ``SWISS_STATE_LOCK`` there can deadlock with a
    thread that holds the Swiss lock and is waiting to import the same module
    (lock-order inversion).  If the lock is busy the re-assert is skipped (and logged);
    that thread's own ``ensure_swiss_backend()`` at use re-pins the path.  Returns True
    only if the path was re-asserted and probed as swieph.
    """
    if not os.environ.get(SE_EPHE_PATH_ENV, "").strip():
        _log.warning(
            "%s is not set: PyJHora left swisseph pointed at its .se1-free wheel directory "
            "(Moshier fallback); writers and endpoints refuse to run until it is set",
            SE_EPHE_PATH_ENV,
        )
        return False
    from .swiss_state import SWISS_STATE_LOCK

    if not SWISS_STATE_LOCK.acquire(blocking=False):
        _log.warning("Swiss state lock busy at import time; deferring the .se1 re-assert to first use")
        return False
    try:
        ensure_swiss_backend()
        return True
    except SwissBackendError as exc:
        _log.error(
            "%s is set but the Swiss file backend is not usable (%s); writers and endpoints "
            "will refuse to run until it is fixed", SE_EPHE_PATH_ENV, exc,
        )
        return False
    finally:
        SWISS_STATE_LOCK.release()


def backend_note(*jds: float) -> str:
    """Uniform ``WriterResult.notes`` fragment: ``ephemeris_backend=swieph``."""
    return f"ephemeris_backend={backend_name(*jds)}"


def _chart_lifetime_jds(ctx: Any) -> tuple[float, ...]:
    """(birth_jd, birth_jd + LIFETIME_HORIZON_YEARS) from ``ctx.config['birth_params']``
    when present and parseable, else ``()`` (a writer without birth params, or a unit
    test's stub context, is simply not date-checked here)."""
    try:
        from datetime import datetime

        bp = ctx.config.get("birth_params")
        iso = bp["datetime_iso"] if isinstance(bp, dict) else None
        if not isinstance(iso, str):
            return ()
        dt = datetime.fromisoformat(iso)
    except Exception:
        return ()
    swe = _import_swisseph()
    birth = swe.julday(dt.year, dt.month, dt.day, 12.0)
    return (birth, birth + LIFETIME_HORIZON_YEARS * 365.25)


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
            # Before the body, hence before any write: backend + the chart's whole
            # lifetime must be inside the corpus window.
            jds = _chart_lifetime_jds(ctx)
            ensure_swiss_backend(*jds)
            result = method(self, ctx, *args, **kwargs)
            note = backend_note(*jds)
            rows = int(getattr(result, "rows_inserted", 0) or 0) + int(getattr(result, "rows_updated", 0) or 0)
            # A no-op return (nothing computed or written) does not claim a backend in notes.
            if rows > 0:
                result.notes = f"{result.notes}; {note}" if result.notes else note
            # WriterResult.notes is NOT persisted by the orchestrator (in-memory only), so the
            # probed backend is also LOGGED at INFO (Cloud Run job logs): the observable trace.
            _log.info("%s %s rows=%d path=%s", getattr(cls, "asset_id", cls.__name__), note, rows,
                      os.environ.get(SE_EPHE_PATH_ENV, ""))
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
