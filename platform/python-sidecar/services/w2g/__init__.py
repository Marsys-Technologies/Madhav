"""W2G — GOCHARA-2.0 engine (ṢAḌ-DARŚANA wave W2G, item 19).

The 2.0 substrate, built BESIDE v1 per the strangler rail. `kala_gochara_windows`
DATA is an untouchable: v1 rows are never updated or deleted, here or ever, and
2.0 rows arrive generation-stamped beside them (ADJUDICATION-6, migration 527).

WHAT THIS PACKAGE IS
────────────────────
  `arcs`        monotone-arc decomposition of a body's longitude history
  `crossings`   contact solving (entry / exact / exit) on a single arc
  `solver`      the constant-read contact solver over many bodies x targets
  `tiers`       ADJUDICATION-14's three-tier materialization policy
  `fingerprint` delta-aware, per-class + per-body invalidation identity
  `db_source`   the global arc builder + the two-query per-chart read path

WHAT IT IS NOT: any astrology. Grammar, orbs, aspect sets, target selection,
weighting and valence all remain v1's, frozen per design §5 — "2.0 changes HOW,
never WHAT".

THE MEASURED PREMISE, stated once, in the place the code lives:
v1's dominant cost is ~110-120ms per contact-primitive call, not ephemeris
computation (that premise was falsified by clean A/B measurement, 2026-08-04 —
SHAD_DARSHANA_STATE.md lane (a)). The fix is not a faster call; it is an
architecture with no per-primitive call to make. Global tables, one join, pure
CPU root-finding thereafter.

MEASURED, live against production data, 2026-08-05 (read-only), chart
482012f1 at its real resonance-map size (76 target refs), full 1900-2150 epoch:

    global arc build, ONCE, shared by every chart ........... 36.8s
    per-chart solve, Tier A only ............ 17,191 contacts in  1.95s
    per-chart solve, Tier A+B ............... 79,949 contacts in  8.69s
    per-chart solve, all nine bodies ....... 334,959 contacts in 37.26s

~111 MICROseconds per contact, against v1's ~110-120 MILLIseconds per
contact-primitive call. This is the contact stream only — scoring, grammar and
shape assembly still layer on top, and the ≤15-minute onboarding SLO is not
discharged until those are measured too.
"""
from __future__ import annotations

from .arcs import (
    ARCSEC_PER_DEG,
    DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
    MonotoneArc,
    angular_delta_deg,
    arcs_covering_degree,
    build_arcs,
    unwrap_degrees,
)
from .crossings import (
    ContactEvent,
    ContactWindow,
    count_contacts,
    find_contacts,
    solve_contact_window,
    solve_crossing_jd,
)
from .db_source import (
    ARC_TABLE,
    DbArcSource,
    build_arcs_for_body,
    fetch_body_series,
    noon_ut_jd,
)
from .fingerprint import (
    ARC_ENGINE_VERSION,
    arc_fingerprint,
    class_fingerprint,
    classes_needing_rebuild,
)
from .solver import ArcSource, ContactSolver, InMemoryArcSource, SolveStats
from .tiers import (
    BODY_TIERS,
    TIER_CONDITIONAL,
    TIER_EAGER,
    TIER_LAZY,
    MaterializationPolicy,
    body_tier,
    eager_bodies,
    lazy_bodies,
    materialization_policy,
)

__all__ = [
    "ARCSEC_PER_DEG",
    "ARC_ENGINE_VERSION",
    "ARC_TABLE",
    "ArcSource",
    "BODY_TIERS",
    "ContactEvent",
    "ContactSolver",
    "ContactWindow",
    "DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC",
    "DbArcSource",
    "InMemoryArcSource",
    "MaterializationPolicy",
    "MonotoneArc",
    "SolveStats",
    "TIER_CONDITIONAL",
    "TIER_EAGER",
    "TIER_LAZY",
    "angular_delta_deg",
    "arc_fingerprint",
    "arcs_covering_degree",
    "body_tier",
    "build_arcs",
    "build_arcs_for_body",
    "class_fingerprint",
    "classes_needing_rebuild",
    "count_contacts",
    "eager_bodies",
    "fetch_body_series",
    "find_contacts",
    "lazy_bodies",
    "materialization_policy",
    "noon_ut_jd",
    "solve_contact_window",
    "solve_crossing_jd",
    "unwrap_degrees",
]
