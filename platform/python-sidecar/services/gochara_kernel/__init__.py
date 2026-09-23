"""Gochara kernel — deterministic contact-episode geometry (WP3a).

Executes GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4.2 under WP1_CONTRACTS.md.

One-way dependency (R2): this package imports ONLY numpy / scipy / pyswisseph
plus the Python standard library. Nothing here imports services.w2g, pipeline,
ka_kshetra, ka_kshetra, or any database driver, and nothing in production code
imports this package (WP3a exit gate: it stays unadopted until WP7).

ADOPTED, NOT IMPORTED (plan §2.2): the proven arc-decomposition and contact
solver functions of services/w2g/ (arcs.py, crossings.py, solver.py) are
re-homed here with attribution comments. The re-homed version fixes the three
known S0/w2g defect classes (E8, evidence_gochara/E8_astra_counterexamples_rerun.py):

  E8-1 close-station coalescing — services/w2g/arcs.py merges derivative roots
      within STATION_MERGE_DAYS = 0.25 d, which silently deletes genuine small
      retrograde loops (E8 measured: 2 real stations at 1.4/1.6 d -> 1 retained,
      3 expected roots -> 1 found). NOT carried over: every sign-confirmed
      derivative root is a station boundary. The sign-change confirmation alone
      (no merge window) still rejects spline-noise tangencies.
  E8-2 0/360 wrap tangency — an in-orb interval around 0/360 whose body never
      reaches the exact degree (turns back inside the orb) produced ZERO
      contacts in w2g because contacts were enumerated from exact roots only.
      The episode layer here also emits no-exact episodes (t_exact=None,
      exact_crossing=False) whenever the in-orb interval overlaps the horizon.
  E8-3 start/end-inside episodes dropped — episodes whose orb overlaps the
      horizon edge but whose exact crossing lies outside it (or whose orb exit
      lies beyond it) were dropped. Here they are emitted with
      truncated_at_horizon in {'start','end'} and exact_crossing=False.

Frame discipline (D-1, F-07): knots are converted to sidereal with Swiss's own
sidereal mode (FLG_SIDEREAL + SIDM_LAHIRI) BEFORE arc-building — sidereal arcs
are built sidereal from the start, never by adjusting a tropical arc after the
fact. Node model (N-4/N-4a(b″)): Rāhu/Ketu positions are swe.MEAN_NODE under
FLG_SIDEREAL; the nodes cast NO dṛṣṭi at all (N-14) but remain full agents and
targets for conjunction / ingresses / kakṣyā / return.

Epoch (F-15): knot abscissa is noon UT (swe.julday(y, m, d, 12.0)) — matching
the ephemeris_daily substrate.
"""
from __future__ import annotations

METHOD_VERSION = "1.0.0"

from .convention import (  # noqa: F401
    KAKSHYA_LORD_ORDER,
    ORB_TABLE,
    SE1_CHECKSUMS,
    SPECIAL_DRISHTI_DEG,
    TOLERANCE_TABLE,
    canonical_convention_id,
    declared_tolerance,
    drishti_angles,
)
from .knots import EphemerisBackendError, KnotSeries, sample_knots  # noqa: F401
from .arcs import ArcIndex, MonotoneArc, build_arc_index  # noqa: F401
from .contacts import ContactRoot, find_boundary_roots, find_roots  # noqa: F401
from .episodes import Episode, solve_episodes  # noqa: F401
from .coverage import CoverageRecord, build_coverage  # noqa: F401
from .ids import contact_id, floor_to_minute_utc_iso, independence_group  # noqa: F401
from .lifecycle import ArcIndexRegistry  # noqa: F401

__all__ = [
    "METHOD_VERSION",
    "ArcIndex",
    "ArcIndexRegistry",
    "ContactRoot",
    "CoverageRecord",
    "Episode",
    "EphemerisBackendError",
    "KAKSHYA_LORD_ORDER",
    "KnotSeries",
    "MonotoneArc",
    "ORB_TABLE",
    "SE1_CHECKSUMS",
    "SPECIAL_DRISHTI_DEG",
    "TOLERANCE_TABLE",
    "build_arc_index",
    "build_coverage",
    "canonical_convention_id",
    "contact_id",
    "declared_tolerance",
    "drishti_angles",
    "find_boundary_roots",
    "find_roots",
    "floor_to_minute_utc_iso",
    "independence_group",
    "sample_knots",
    "solve_episodes",
]
