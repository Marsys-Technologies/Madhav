"""Knot ingestion + D-1 sidereal conversion (plan §4.1, §4.2; N-4/N-4a(b″)).

Knots are sampled DIRECTLY in the sidereal frame: `swe.calc_ut` with
`FLG_SWIEPH | FLG_SIDEREAL` after `swe.set_sid_mode(SIDM_LAHIRI)` — Swiss's own
sidereal mode (D-1). The F-07 defect class (tropical arcs joined to sidereal
targets) is fixed by construction: arcs are built on these sidereal knots, and
never on tropical knots minus ayanāṃśa (the two frames differ by nutation in
longitude of date, +16.516″ on 2020-01-01 — WP0 pin).

Epoch (F-15): every knot's abscissa is NOON UT (`swe.julday(y, m, d, 12.0)`),
matching the ephemeris_daily substrate convention. A midnight abscissa shifts
the Moon by ~27,544″ (WP2 case 05).

Node model (N-4a(b″)): Rāhu = `swe.MEAN_NODE` under the same flags; Ketu =
(Rāhu + 180) mod 360. TRUE node is never used for contact geometry (its
excursion under the mean-node convention reaches 1.76° = 6351″ in 2026 — WP2
case 02, three orders of magnitude above every §9 tolerance).

Ephemeris backend (F-14): recorded FROM THE RETURNED retflag of every
calc_ut call — `swieph` iff retflag & 2, `moshier` iff retflag & 4 — never
from the requested flag. A Moshier fallback raises EphemerisBackendError; a
gate run on Moshier is Moshier-vs-Moshier and cannot fail, so callers must
treat it as NOT_RUN, never a pass.

The Moon's flag is NOT proof (SS N-28, measured on pyswisseph 2.10.3.2): with the
Moon file `semo_*.se1` missing, `calc_ut(MOON)` silently computes the Moshier Moon
but STILL returns the SWIEPH flag. TRUE_NODE is computed from the Moon file and its
flag does not lie, so every Moon calc is gated by a file-level TRUE_NODE probe at
the same instant (see `_assert_moon_file_backend`) — uncached, so each call proves its own
instant. The other bodies' flags are
honest (planets come from `sepl_*.se1`; the mean node is analytic and is never
read for the backend).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import swisseph as swe

from panchang_engine.swiss_state import serialized_swiss_state

EPHE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

# swe planet ids for the nine grahas. Rāhu/Ketu both resolve to MEAN_NODE
# (N-4a(b″)); Ketu's longitude is Rāhu + 180.
GRAHA_TO_SWE = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": swe.MEAN_NODE,
}

NINE_GRAHAS = tuple(GRAHA_TO_SWE)


class EphemerisBackendError(RuntimeError):
    """A calc_ut fell back to Moshier (retflag & 4) or otherwise failed the
    SWIEPH gate. Gate-grade comparisons must report NOT_RUN, never pass.

    `detail` (optional) names a gate other than the per-call flag — the Moon's
    file-level probe — so the message says what actually failed; `retflag` is
    always the flag of the call that proved the backend is not SWIEPH."""

    def __init__(self, body: str, retflag: int, detail: str | None = None):
        super().__init__(
            f"{body}: {detail} Comparison is NOT_RUN, not PASS (F-14)."
            if detail else
            f"{body}: retflag {retflag} — ephemeris backend is not SWIEPH "
            f"(retflag & 2 failed). Comparison is NOT_RUN, not PASS (F-14)."
        )
        self.body = body
        self.retflag = retflag


class NodeModelError(RuntimeError):
    """A Rāhu/Ketu calc was attempted with a non-mean-node swe id.

    N-4a(b″) pins both nodes to swe.MEAN_NODE; the convention vector's
    node_model='mean' is the only admitted model. A per-call assertion (not
    just a mapping invariant) so a mutated/patched GRAHA_TO_SWE cannot
    silently produce true-node longitudes.
    """


@dataclass(frozen=True)
class KnotSeries:
    """Noon-UT sidereal knots for one body over a closed date range."""

    body: str
    start_date: date
    end_date: date
    knot_jds: tuple[float, ...]           # noon-UT Julian days
    longitudes_deg: tuple[float, ...]     # sidereal (Lahiri), wrapped [0, 360)
    ephemeris_backend: dict[str, Any] = field(default_factory=dict)
    # ephemeris_backend: {backend, retflag, swe_version} — retflag of the LAST
    # probe calc (all calcs in one series share the backend in practice; a
    # mixed-backend series cannot happen with one .se1 set present).

    @property
    def body_is_moon(self) -> bool:
        return self.body == "Moon"


def _check_retflag(body: str, retflag: int) -> str:
    if retflag & 4:
        raise EphemerisBackendError(body, retflag)
    if not (retflag & 2):
        raise EphemerisBackendError(body, retflag)
    return "swieph"


# ── Moon file-level backend probe (SS N-28) ─────────────────────────────────
# NO CACHE (ASTRA A2.5 v1.2 R3). A success cache keyed on a calendar-year block and a
# directory stamp cannot be made sound: Swiss file coverage is not the calendar block
# (semo_18.se1 ends in January 2400, measured), and directory metadata is not file identity
# (contents or a symlink target can change under an unchanged stamp). The probe is a single
# TRUE_NODE calc at the call's own instant — the file that serves the Moon at that jd is the
# file proven — so it runs on EVERY Moon calc. Cost, measured on the real checksum-pinned
# files over the 4.1 scored horizon (10,334 daily Moon knots), against TWO different baselines:
#   (a) the Moon sampler with vs without the probe: sample_knots 1.07 s → 1.27 s (+0.20 s, ≈19 %);
#       per call a probe is 6.3 µs against 2.8 µs for the bare Moon calc;
#   (b) the full `calc_sidereal_lon` wrapper path (SWISS_STATE_LOCK + ephemeris path + sid-mode,
#       ≈40 µs per call): the probe adds ≈4.6 µs (≈11 %), and a whole-horizon Moon sampling run
#       takes 0.44 s against 0.38 s for the Sun through the same wrapper.
# The figures are not comparable across baselines; the conclusion is the same: cheap, trivially correct.


@serialized_swiss_state
def _assert_moon_file_backend(jd_ut: float, ephe_path: str | None) -> None:
    """Fail closed unless the Moon at `jd_ut` is served from the .se1 files.

    A serialized Swiss-state owner in its own right (re-entrant: its only caller,
    calc_sidereal_lon, already holds SWISS_STATE_LOCK with the ephemeris path
    set — the DP-SD-010 inventory requires every direct calc_ut to be owned).
    TRUE_NODE at the same instant needs the same `semo_*.se1`, and — unlike the
    Moon's — its returned flag reports the substitution (SS N-28 measurement).
    Nothing is remembered between calls: every call proves its own instant."""
    _xx, retflag = swe.calc_ut(jd_ut, swe.TRUE_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)
    if (retflag & 4) or not (retflag & 2):
        raise EphemerisBackendError(
            "Moon", int(retflag),
            detail=(
                f"file-level probe failed (TRUE_NODE at jd {jd_ut}: retflag {int(retflag)}, "
                f"needs semo_*.se1) — the Moon's own flag cannot prove the Swiss "
                f"backend (SS N-28)."
            ),
        )


@serialized_swiss_state
def calc_sidereal_lon(body: str, jd_ut: float, ephe_path: str | None) -> tuple[float, int]:
    """One sidereal longitude probe. Returns (longitude_deg, retflag).

    The caller asserts `retflag & 2` (F-14); this function is the single seam
    through which every Swiss call in the kernel passes. DP-SD-010: the seam
    is serialized under SWISS_STATE_LOCK so process-wide Swiss state
    (sid mode / ephe path) cannot interleave across threads.
    """
    if ephe_path is not None:
        swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    swe_id = GRAHA_TO_SWE[body]
    if body in ("Rahu", "Ketu") and swe_id != swe.MEAN_NODE:
        raise NodeModelError(
            f"{body}: swe id {swe_id} is not MEAN_NODE — node_model='mean' "
            f"is the only admitted model (N-4a(b″)); refusing the calc."
        )
    if body == "Moon":
        _assert_moon_file_backend(jd_ut, ephe_path)
    out, retflag = swe.calc_ut(jd_ut, swe_id, EPHE_FLAGS)
    lon = float(out[0])
    if body == "Ketu":
        lon = (lon + 180.0) % 360.0
    return lon, int(retflag)


def sample_knots(
    body: str,
    start_date: date,
    end_date: date,
    ephe_path: str | None = None,
) -> KnotSeries:
    """Noon-UT sidereal knots for `body` over [start_date, end_date] inclusive.

    Every calc asserts the SWIEPH backend via the returned retflag (F-14):
    `retflag & 4` raises EphemerisBackendError (NOT_RUN), `retflag & 2` passes.
    """
    if end_date < start_date:
        raise ValueError(f"{body}: end_date {end_date} before start_date {start_date}")
    jds: list[float] = []
    lons: list[float] = []
    backend = ""
    retflag = 0
    d = start_date
    one = timedelta(days=1)
    while d <= end_date:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        lon, retflag = calc_sidereal_lon(body, jd, ephe_path)
        backend = _check_retflag(body, retflag)
        jds.append(float(jd))
        lons.append(lon)
        d += one
    if len(jds) < 4:
        raise ValueError(
            f"{body}: need at least 4 knots for a cubic spline, got {len(jds)} "
            f"over {start_date}..{end_date}"
        )
    return KnotSeries(
        body=body,
        start_date=start_date,
        end_date=end_date,
        knot_jds=tuple(jds),
        longitudes_deg=tuple(lons),
        ephemeris_backend={
            "backend": backend,
            "retflag": retflag,
            "swe_version": getattr(swe, "__version__", "unknown"),
        },
    )
