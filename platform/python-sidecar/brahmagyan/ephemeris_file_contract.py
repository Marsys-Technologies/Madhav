"""Brahmagyan's exact file-backed ephemeris preconditions.

The shared Swiss-state decorator retains the existing process lock. Callers
retain their own ordering of backend and file checks. The explicit digest map
supports the historical bg_sky_calendar mutable-global compatibility wrapper;
registered consumers use the canonical default map.
"""
from __future__ import annotations
from typing import Any
from panchang_engine.swiss_state import serialized_swiss_state

EPHEMERIS_FILE_SHA256: dict[str, str] = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}

@serialized_swiss_state
def require_swiss_file_backend(swe: Any, ephe_path: str) -> None:
    """Configure the exact file-backed ephemeris contract or fail closed.

    ``swe.set_ephe_path`` does not fail when files are missing: ``calc_ut``
    silently substitutes Moshier and exposes the substitution only in its
    return flags.  A writer that persisted those rows with the DE441/Swiss-file
    citation would manufacture provenance, so a real position probe is part of
    the write precondition.
    """
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    probe_jd = swe.julday(2000, 1, 1, 0.0)
    _position, retflag = swe.calc_ut(
        probe_jd,
        swe.SUN,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED,
    )
    file_backed = bool(retflag & swe.FLG_SWIEPH)
    moshier = bool(retflag & swe.FLG_MOSEPH)
    if not file_backed or moshier:
        raise RuntimeError(
            "Swiss Ephemeris file backend was not active for bg_sky_calendar; "
            "refusing the silent Moshier analytic fallback"
        )

def require_pinned_ephemeris_files(
    ephe_path: str, *, expected_digests: dict[str, str] | None = None
) -> None:
    """Verify the exact ephemeris bytes whose provenance the rows claim."""
    import hashlib
    from pathlib import Path

    root = Path(ephe_path)
    pins = EPHEMERIS_FILE_SHA256 if expected_digests is None else expected_digests
    for filename, expected_digest in pins.items():
        path = root / filename
        try:
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise RuntimeError(
                f"Swiss Ephemeris file is unavailable for digest verification: {path}"
            ) from exc
        if actual_digest != expected_digest:
            raise RuntimeError(
                "Swiss Ephemeris file digest mismatch for "
                f"{filename}: expected {expected_digest}, observed {actual_digest}"
            )
