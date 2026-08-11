#!/usr/bin/env python3
"""
w44_weight_fitting.py -- GOCHARA-UTKARSA W4.4: cross-chart pooled weight fitting.

Fits per-mechanism weights for the 7 admitted Wave-2 scoring mechanisms +
their 3 sub-components, using cross-chart partial pooling across both charts
(native + Abhinandan).

HONESTY CONSTRAINTS (I3):
- Every weight is computed from real data or reported as
  ablation_not_computable_from_corpus.
- No weight is assumed, hardcoded, or fabricated.
- If the DB is unavailable, exit 3 with a clear error.
- The shrinkage prior (k=3) is a calibration choice, explicitly documented,
  not inherited doctrine.

I2: ZERO imports from gochara_grammar/*, gochara_intensity/*, or
    ka_gochara_sweep/*.

TEST SPLIT: NEVER score events >= 2020-01-01.
  - load_train_events() enforces this for native (SealedTestSplitViolation).
  - Abhinandan DB query adds WHERE event_date < '2020-01-01'.

READ-ONLY on kala_gochara_windows_v2: only SELECT, never mutate.
WRITE: fitted weights go to gochara_v3_calibration (migration 561).

Exit codes:
  0 -- report generated successfully
  1 -- computation error (non-DB)
  3 -- DB unavailable / missing DATABASE_URL / psycopg not installed
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

# ── path setup: kala_admission package is in scripts/, sidecar root for services ──
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _SCRIPT_DIR.parent
_SIDECAR_ROOT = _SCRIPTS_DIR.parent

for _p in (str(_SCRIPTS_DIR), str(_SIDECAR_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kala_admission.checks import run_blind_battery_curve  # noqa: E402
from kala_admission.lel import TEST_SPLIT_BOUNDARY, load_train_events, partition_scorable  # noqa: E402

logger = logging.getLogger(__name__)

# ── Chart IDs ────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

# ── Admitted mechanisms (10 with weights; 2 structural-only) ─────────────────

ADMITTED_MECHANISM_IDS: list[str] = [
    "w21_av_gating",
    "w22_moorti_nirnaya",
    "w23_tara_bala",
    "w24_sade_sati",
    "w25_kota_chakra",
    "w26_real_eclipses",
    "w27_annual_stack",
    "w27a_tajaka_year_lord",
    "w27b_tithi_pravesha",
    "w27c_sudarshana",
]

STRUCTURAL_ONLY_IDS: list[str] = [
    "w28_bhava_degrees",
    "w29_citation_resolution",
]

# Registry directory for mechanism YAMLs
_REGISTRY_DIR = (
    _SIDECAR_ROOT / "services" / "gochara_v3" / "mechanisms" / "registry"
)

# Shrinkage prior strength (k=3 effective events, documented calibration choice)
# This regularises per-chart deltas toward the pooled mean when sample sizes
# are small (O(30) events per chart). k=3 is a deliberate conservative choice:
# with n_total=60 events, shrinkage = 60/(60+3) ≈ 0.952 (mild).
# With n_total=10, shrinkage = 10/(10+3) ≈ 0.769 (stronger for sparse charts).
SHRINKAGE_PRIOR_K: int = 3

# ── Bounds (matching run_admission.py's dasha window) ────────────────────────
BOUNDS_START = date(1984, 2, 5)
BOUNDS_END = date(2022, 6, 1)

# Proxy ablation fraction: when term_breakdown is absent, approximate the
# mechanism's contribution as this fraction of abs(signed_intensity).
# Documented lower-bound proxy, not a true ablation.
PROXY_ABLATION_FRACTION = 0.1

# ── Engine-wiring status per admitted mechanism (PARIṢKĀRA MR-14-matching) ────
#
# Traced 2026-08-11 against services/gochara_v3/engine.py (the module that
# ACTUALLY produces term_breakdown/signed_intensity for kala_gochara_windows_v2
# rows). Records whether the mechanism's own
# services/gochara_v3/mechanisms/<toggle_key>.py `compute()` is invoked
# ANYWHERE in that production path.
#
# Finding: it is not. This is a DEEPER root cause than "toggle_keys don't
# literally match term_breakdown's top-level keys" (the prior pass's
# hypothesis, disproven here) -- the 10 admitted Wave-2 mechanisms are
# entirely dormant, standalone modules that engine.py never calls, so there
# is NO key under ANY name in term_breakdown, signed_intensity,
# permission_detail, or quality_gates_detail that legitimately represents
# any of their contributions. Evidence:
#   (a) services/gochara_v3/mechanisms/__init__.py's own module docstring:
#       "Dormant mechanism modules for Wave 2... NOT wired into engine.py
#       yet... Admission into the live scoring path requires ablation
#       evidence and a formal admission ruling."
#   (b) each mechanism module says so explicitly, e.g. w21_av_gating.py:
#       "This module is a CANDIDATE mechanism -- it is NOT wired into
#       engine.py (that wiring is Wave 4 work)."
#   (c) `grep -rn "gochara_v3.mechanisms" services/gochara_v3/*.py` (engine.py,
#       context.py, interval_solver.py, threshold.py) returns ZERO hits --
#       nothing outside services/gochara_v3/mechanisms/ itself imports them.
#   (d) ClassContext (context.py) carries no data fields for 9 of the 10
#       mechanisms' documented data sources (moorti rows, kota_chakra rings,
#       sudarshana placements, tajaka year-lords, tithi_pravesha rows, real
#       eclipse events, tara_bala's natal_moon_nakshatra_id passthrough).
#       Only av_gate_rows exists -- and engine.py's own
#       `_check_av_threshold_from_context` consumes it via a different
#       (boolean, v1-legacy) computation than w21_av_gating.py's own SAV/BAV
#       bindu modifier logic; the two are not the same computation.
#   (e) every mechanism YAML in the registry is still `admission_state:
#       candidate` -- none has ever been promoted past candidacy.
#
# A literal-key remap (e.g. aliasing w23_tara_bala to the pre-existing
# 'nakshatra_ingress_tara' activity_terms primitive it is *meant* to
# eventually enhance) was considered and REJECTED: the raw v1 primitive's
# contribution is not the candidate mechanism's marginal effect (the
# mechanism is a quality MODIFIER layered on top of the primitive, not the
# primitive itself). Aliasing the two would misattribute the base primitive's
# signal as if it were the mechanism's, which is exactly the fabrication I3
# ("no weight is assumed, hardcoded, or fabricated") forbids.
#
# All 10 are correctly False today. Flip an entry to True only in the same
# PR that actually wires that mechanism's compute() into engine.py's
# production lambda_v3 path (Wave 4 work -- see MASTER_REMEDIATION_REGISTER
# MR-14 amendment + this PR's report for the explicit hand-off). Any
# toggle_key not present in this dict defaults to wired=True (`.get(key,
# True)`) -- i.e. only mechanisms we have POSITIVELY confirmed are dormant
# are excluded from term_breakdown/proxy attribution; everything else keeps
# today's behaviour unchanged.
MECHANISM_ENGINE_WIRED: dict[str, bool] = {
    "w21_av_gating": False,
    "w22_moorti_nirnaya": False,
    "w23_tara_bala": False,
    "w24_sade_sati": False,
    "w25_kota_chakra": False,
    "w26_real_eclipses": False,
    "w27_annual_stack": False,
    "w27a_tajaka_year_lord": False,
    "w27b_tithi_pravesha": False,
    "w27c_sudarshana": False,
}


# ═══════════════════════════════════════════════════════════════════════════
# Data models
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MechanismMeta:
    mechanism_id: str
    toggle_key: str
    description: str


@dataclass
class GochaWindow:
    """One row from kala_gochara_windows_v2."""
    event_class: str
    window_start: date
    window_end: date
    signed_intensity: float
    term_breakdown: Optional[dict]  # JSONB, may be None


@dataclass
class ChartEvents:
    chart_id: str
    events: list[tuple[str, date]]  # (event_id, event_date)


@dataclass
class MechanismWeight:
    mechanism_id: str
    toggle_key: str
    delta_native: float
    delta_abhinandan: float
    pooled_delta: float
    pooled_delta_shrunk: float
    final_weight: float
    ablation_method: str  # "term_breakdown" | "proxy_fraction" | "ablation_not_computable" | "mechanism_not_wired"
    admitted: bool = True
    n_train_native: int = 0
    n_train_abhinandan: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# Pure functions (DB-free; testable in isolation)
# ═══════════════════════════════════════════════════════════════════════════

def compute_pooled_delta(
    delta_native: float,
    delta_abhinandan: float,
    n_native: int,
    n_abhinandan: int,
    prior_strength: int = SHRINKAGE_PRIOR_K,
) -> tuple[float, float]:
    """
    Compute the cross-chart weighted-average delta and its shrinkage-adjusted value.

    Pooling: weighted average by sample size.
    Shrinkage: regularise toward 0 using k pseudo-observations at 0.
      pooled_shrunk = pooled * n_total / (n_total + k)

    Returns (pooled_delta, pooled_delta_shrunk).

    With n_native=30, n_abhinandan=30, delta_native=0.1, delta_abhinandan=0.0, k=3:
      pooled = (30*0.1 + 30*0.0) / 60 = 0.05
      shrunk = 0.05 * 60 / 63 ≈ 0.04762
    """
    n_total = n_native + n_abhinandan
    if n_total == 0:
        return 0.0, 0.0
    pooled = (n_native * delta_native + n_abhinandan * delta_abhinandan) / n_total
    shrunk = pooled * n_total / (n_total + prior_strength)
    return pooled, shrunk


def apply_shrinkage(
    pooled_delta: float,
    n_total: int,
    prior_strength: int = SHRINKAGE_PRIOR_K,
) -> float:
    """
    Apply shrinkage toward 0: shrunk = pooled * n_total / (n_total + k).
    This is the same operation as compute_pooled_delta's second return value,
    exposed as a standalone function for testability.
    """
    if n_total + prior_strength == 0:
        return 0.0
    return pooled_delta * n_total / (n_total + prior_strength)


def load_mechanism_registry(
    registry_dir: Optional[Path] = None,
) -> list[MechanismMeta]:
    """
    Load all mechanism YAMLs from the registry directory and return their metadata.

    Reads: mechanism_id, toggle_key, description from each YAML file.
    Returns only the 10 admitted mechanisms (ADMITTED_MECHANISM_IDS) + 2
    structural-only (STRUCTURAL_ONLY_IDS), in admission order.

    I2: no gochara_grammar/gochara_intensity/ka_gochara_sweep imports.
    """
    try:
        import yaml
    except ImportError:
        # yaml not available — fall back to simple line parser
        yaml = None  # type: ignore[assignment]

    dir_path = registry_dir or _REGISTRY_DIR
    if not dir_path.exists():
        raise FileNotFoundError(f"Mechanism registry not found: {dir_path}")

    parsed: dict[str, MechanismMeta] = {}
    for yaml_file in sorted(dir_path.glob("*.yaml")):
        try:
            content = yaml_file.read_text()
            if yaml is not None:
                data = yaml.safe_load(content)
            else:
                data = _simple_yaml_parse(content)
            mid = data.get("mechanism_id", "")
            tk = data.get("toggle_key", mid)
            desc = data.get("description", "")
            parsed[mid] = MechanismMeta(mechanism_id=mid, toggle_key=tk, description=desc)
        except Exception as exc:
            logger.warning("Skipping %s: %s", yaml_file.name, exc)

    result: list[MechanismMeta] = []
    for mid in ADMITTED_MECHANISM_IDS + STRUCTURAL_ONLY_IDS:
        if mid in parsed:
            result.append(parsed[mid])
        else:
            logger.warning("Mechanism %s not found in registry YAML files", mid)
    return result


def _simple_yaml_parse(content: str) -> dict:
    """
    Minimal YAML key:value parser (no yaml dependency required).
    Only handles top-level scalar key: value lines. Used as fallback if
    PyYAML is not installed. Sufficient for our registry YAMLs.
    """
    result: dict = {}
    for line in content.splitlines():
        if ":" not in line or line.startswith("#") or line.startswith(" "):
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"')
        if key and val:
            result[key] = val
    return result


def _ablate_window_intensity(
    window: GochaWindow,
    toggle_key: str,
) -> tuple[float, str]:
    """
    Compute the 'without this mechanism' intensity for one window.

    Strategy 1 (preferred): if term_breakdown JSONB contains a key matching
    toggle_key, subtract that contribution. This is checked FIRST and wins
    unconditionally when it fires -- an explicit, literal key written by
    SOMETHING into this specific window's decomposition is real data,
    regardless of this mechanism's general engine-wiring status recorded in
    MECHANISM_ENGINE_WIRED (that registry is a *default*, not an override of
    actual per-row evidence).

    Strategy 2 (honest null): if no literal key match and MECHANISM_ENGINE_WIRED
    says this toggle_key's mechanism is not invoked anywhere in
    services/gochara_v3/engine.py's production path, there is no legitimate
    signal to ablate -- return the window's intensity UNCHANGED (zero delta)
    rather than fabricating a generic proxy reduction for a mechanism that
    structurally cannot have contributed to this window's signed_intensity.

    Strategy 3 (fallback proxy): mechanism IS wired (or its wiring status is
    unknown -- see MECHANISM_ENGINE_WIRED's `.get(key, True)` default) but
    this window's term_breakdown didn't carry a matching key (e.g. mechanism
    inactive this window). Reduce by PROXY_ABLATION_FRACTION * abs(intensity)
    -- documented lower-bound proxy, not a true ablation.

    Strategy 4 (honest null): if signed_intensity == 0, delta contribution is 0.

    Returns (ablated_intensity, method_used).
    """
    if window.signed_intensity == 0.0:
        return 0.0, "proxy_fraction"

    if window.term_breakdown:
        # Try to find the mechanism's contribution in term_breakdown
        contribution = None
        for key_variant in (toggle_key, toggle_key.replace("_", "-"), toggle_key.upper()):
            if key_variant in window.term_breakdown:
                contribution = window.term_breakdown[key_variant]
                break
        if contribution is not None:
            try:
                ablated = float(window.signed_intensity) - float(contribution)
                return ablated, "term_breakdown"
            except (TypeError, ValueError):
                pass

    # No literal term_breakdown match on this window. Before falling back to
    # the generic proxy heuristic, check whether this mechanism is even
    # wired into the engine that produced this window's signed_intensity. A
    # proxy fraction implies "a real effect exists, we just can't cleanly
    # isolate it" -- untrue for a mechanism whose compute() never runs.
    if not MECHANISM_ENGINE_WIRED.get(toggle_key, True):
        return window.signed_intensity, "mechanism_not_wired"

    # Fallback: proxy fraction
    proxy_reduction = PROXY_ABLATION_FRACTION * abs(window.signed_intensity)
    # For adverse (negative) windows, proxy_reduction reduces magnitude
    if window.signed_intensity > 0:
        ablated = window.signed_intensity - proxy_reduction
    else:
        ablated = window.signed_intensity + proxy_reduction
    return ablated, "proxy_fraction"


def _make_curve_builder_from_windows(
    windows: list[GochaWindow],
    toggle_key: Optional[str] = None,
    ablate: bool = False,
) -> Any:
    """
    Build a CurveBuilder (date, date) -> list[CurvePoint] from v3 windows corpus.

    If ablate=True and toggle_key is given, compute per-window intensity
    with the mechanism's contribution removed (see _ablate_window_intensity).

    The v3 windows already incorporate all admitted mechanisms via signed_intensity.
    We approximate intensity at a date d as: the mean signed_intensity of all
    windows active at d (window_start <= d <= window_end).
    Windows with no overlap return 0.0 (honest empty result, no fabrication).

    This is a coarser proxy than the dasha-confluence curve used by run_admission.py,
    but it is what the v3 corpus provides without requiring live mechanism code.
    """
    from datetime import timedelta

    # Pre-compute ablated intensities if needed
    if ablate and toggle_key:
        intensities_by_window: list[tuple[date, date, float]] = []
        for w in windows:
            ablated_val, _ = _ablate_window_intensity(w, toggle_key)
            intensities_by_window.append((w.window_start, w.window_end, ablated_val))
    else:
        intensities_by_window = [(w.window_start, w.window_end, w.signed_intensity) for w in windows]

    def build_curve(range_start: date, range_end: date):
        from kala_admission.curve import CurvePoint

        out: list[CurvePoint] = []
        d = range_start
        step = 5
        while d <= range_end:
            # Average signed_intensity of all windows covering date d
            covering = [val for (ws, we, val) in intensities_by_window if ws <= d <= we]
            if covering:
                intensity = sum(covering) / len(covering)
            else:
                intensity = 0.0
            out.append(CurvePoint(date=d, intensity=max(0.0, float(intensity))))
            d = d + timedelta(days=step)
        return out

    return build_curve


def compute_hit_rate_from_windows(
    windows: list[GochaWindow],
    events: list[tuple[str, date]],
    toggle_key: Optional[str] = None,
    ablate: bool = False,
    percentile: float = 2.0 / 3.0,
) -> tuple[float, int, int]:
    """
    Run run_blind_battery_curve on the v3 windows corpus (optionally ablated).

    Returns (hit_rate, hit_count, scored_count).

    I4: empty corpus -> honest 0.0 hit_rate (no fabrication).
    """
    if not events:
        return 0.0, 0, 0

    if not windows:
        # I4: empty corpus -> honest 0.0
        return 0.0, 0, 0

    curve_builder = _make_curve_builder_from_windows(windows, toggle_key=toggle_key, ablate=ablate)

    # run_blind_battery_curve expects:
    #   build_curve_for_event: Callable[[str], CurveBuilder]
    #   events: list[tuple[str, date]]
    def build_curve_for_event(_event_id: str):
        # Same curve regardless of event_id — we use the global v3 corpus
        return curve_builder

    result = run_blind_battery_curve(
        build_curve_for_event=build_curve_for_event,
        events=events,
        bounds_start=BOUNDS_START,
        bounds_end=BOUNDS_END,
        percentile=percentile,
    )
    return result.hit_rate, result.hit_count, result.scored_count


def _determine_ablation_method(
    windows: list[GochaWindow],
    toggle_key: str,
) -> str:
    """
    Determine which ablation method will be used for this mechanism.
    Reports 'ablation_not_computable' if no windows are available.

    PARIṢKĀRA MR-14 DISCLOSED FINDING (2026-08-11, PR #1213): the confirmed
    root cause of every all-zero/degenerate W4.4 fit to date was that
    `term_breakdown` was NULL on 100% of gen-3.0 rows (register PG-6/PG-7).
    That NULL-ness is now fixed at the engine/writer level -- see
    `services/gochara_v3/interval_solver.py` and
    `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py`.

    PARIṢKĀRA MR-14-MATCHING FINDING (2026-08-11, this PR, supersedes the
    framing of the disclosure above): fixing term_breakdown's NULL-ness does
    NOT make the "term_breakdown" method reachable for any of the 10
    admitted mechanisms (ADMITTED_MECHANISM_IDS: w21_av_gating,
    w22_moorti_nirnaya, ..., w27a/b/c) -- but the reason is DEEPER than "the
    toggle_key strings don't literally match the decomposition's top-level
    keys" (the prior pass's hypothesis). The real W1.5 term_breakdown shape
    produced by `services/gochara_v3/engine.py` is
    `{promise, permission, activity, quality_gates, lambda_v3, activity_terms,
    formula}` -- and after tracing engine.py, context.py, and every mechanism
    module under `services/gochara_v3/mechanisms/`, NONE of the 10 admitted
    mechanisms' own `compute()` functions are ever invoked anywhere in
    engine.py's production lambda_v3 path. They are dormant, standalone
    candidate modules (confirmed by `mechanisms/__init__.py`'s own docstring,
    each module's own "NOT wired into engine.py" docstring, a zero-hit grep
    for any import of them outside their own package, and ClassContext
    lacking data fields for 9 of the 10 mechanisms' documented inputs -- see
    MECHANISM_ENGINE_WIRED's own comment for the full evidence trail).

    CONSEQUENCE: there is no key, under ANY name, anywhere in term_breakdown
    (top-level or inside activity_terms) that legitimately represents any of
    the 10 mechanisms' contributions -- not because of a naming mismatch
    that remapping could fix, but because the computation that would produce
    such a value never runs. Aliasing a toggle_key to a superficially-related
    v1 primitive already present in activity_terms (e.g. w23_tara_bala <->
    the 'nakshatra_ingress_tara' primitive it is meant to eventually enhance)
    was considered and REJECTED: that would misattribute the primitive's raw
    contribution as the candidate mechanism's marginal effect, a category
    error and a fabrication under I3.

    THE FIX (this function, this PR): `has_term_breakdown` still checks the
    real decomposition's literal top-level keys first (unchanged, and still
    correctly reachable the day any mechanism's contribution IS legitimately
    written into a matching key -- see
    `test_windows_with_matching_breakdown_returns_term_breakdown`). When no
    literal match exists, this function now checks MECHANISM_ENGINE_WIRED
    before falling back to `proxy_fraction`: a mechanism confirmed dormant
    reports the distinct, honest `"mechanism_not_wired"` instead of a
    fabricated proxy that would otherwise look like a real (if crude)
    per-mechanism signal for a mechanism that structurally contributed
    nothing. `build_weight_fitting_report` / `compute_mechanism_weights`
    treat `"mechanism_not_wired"` the same as `"ablation_not_computable"`:
    delta forced to an honest 0.0, never assumed or hardcoded (I3).

    Wiring each of the 10 admitted mechanisms' own contribution into a
    matching, toggle_key-keyed slot of the served decomposition remains
    real, larger, separate work (touching `services/gochara_v3/context.py`,
    `engine.py`, and the 10 mechanism modules) that this lane does not
    attempt -- see the final report / register for the explicit hand-off.
    `test_ablation_method_term_breakdown_currently_unreachable_for_admitted_toggle_keys`
    in this module's test file locks in and documents this current state
    (now asserting `"mechanism_not_wired"`, the honest label, rather than
    `"proxy_fraction"`) so a future session re-discovers it as a known
    finding, not a surprise.
    """
    if not windows:
        return "ablation_not_computable"
    has_term_breakdown = any(
        w.term_breakdown is not None and (
            toggle_key in w.term_breakdown
            or toggle_key.replace("_", "-") in w.term_breakdown
            or toggle_key.upper() in w.term_breakdown
        )
        for w in windows
    )
    if has_term_breakdown:
        return "term_breakdown"
    if not MECHANISM_ENGINE_WIRED.get(toggle_key, True):
        return "mechanism_not_wired"
    return "proxy_fraction"


def compute_dataset_hash(
    native_events: list[tuple[str, date]],
    abhinandan_events: list[tuple[str, date]],
) -> str:
    """
    MD5 of sorted train event_ids from both charts.
    Provides provenance for the fitted weights.
    """
    all_ids = sorted(eid for eid, _ in (native_events + abhinandan_events))
    payload = ",".join(all_ids).encode("utf-8")
    return hashlib.md5(payload).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# DB loading (follows w41_lambda_contenders.py pattern)
# ═══════════════════════════════════════════════════════════════════════════

def _require_psycopg():
    """Import psycopg or exit(3)."""
    try:
        import psycopg
        import psycopg.rows
        return psycopg
    except ImportError as exc:
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        sys.exit(3)


def _require_database_url() -> str:
    """Get DATABASE_URL or exit(3)."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print(
            "ERROR: DATABASE_URL environment variable is required. "
            "Set it to a valid PostgreSQL connection string.",
            file=sys.stderr,
        )
        sys.exit(3)
    return dsn


def load_v3_windows(conn: Any, chart_id: str) -> list[GochaWindow]:
    """
    Load v3 gochara windows for a chart (SELECT only — never mutates).
    Filter: era_slice_key LIKE 'g3_%' to get only v3 windows.
    TEST SPLIT note: we read all windows (window_start is not event-anchored),
    but we only score against TRAIN events (< 2020-01-01), so no test leak.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_class,
                   window_start,
                   window_end,
                   signed_intensity,
                   term_breakdown
              FROM kala_gochara_windows_v2
             WHERE chart_id = %s
               AND era_slice_key LIKE 'g3_%%'
             ORDER BY window_start
            """,
            (chart_id,),
        )
        rows = cur.fetchall()

    windows: list[GochaWindow] = []
    for r in rows:
        if isinstance(r, dict):
            event_class = r["event_class"]
            window_start = r["window_start"]
            window_end = r["window_end"]
            signed_intensity = r["signed_intensity"]
            term_breakdown = r["term_breakdown"]
        else:
            event_class, window_start, window_end, signed_intensity, term_breakdown = r

        # Coerce dates
        if isinstance(window_start, str):
            window_start = date.fromisoformat(window_start)
        if isinstance(window_end, str):
            window_end = date.fromisoformat(window_end)

        # Coerce term_breakdown (JSONB arrives as dict or string)
        if isinstance(term_breakdown, str):
            try:
                term_breakdown = json.loads(term_breakdown)
            except (json.JSONDecodeError, TypeError):
                term_breakdown = None

        windows.append(
            GochaWindow(
                event_class=str(event_class),
                window_start=window_start,
                window_end=window_end,
                signed_intensity=float(signed_intensity) if signed_intensity is not None else 0.0,
                term_breakdown=term_breakdown if isinstance(term_breakdown, dict) else None,
            )
        )
    return windows


def load_abhinandan_train_events(conn: Any, chart_id: str) -> list[tuple[str, date]]:
    """
    Load TRAIN events for Abhinandan chart from DB.

    TEST SPLIT: WHERE event_date < '2020-01-01' — hard-coded in the query.
    Returns list of (event_id, event_date).

    Tries life_events table (the real LEL table) first.
    Falls back to lel_event_class_resolution or other tables if found.
    If none found: returns [] and logs the missing table.
    """
    # Check what tables exist
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
              FROM information_schema.tables
             WHERE table_schema = 'public'
               AND table_name IN ('life_events', 'lel_event_class_resolution', 'lel_events')
             ORDER BY table_name
            """
        )
        found_tables = {r[0] if not isinstance(r, dict) else r["table_name"] for r in cur.fetchall()}

    if "life_events" in found_tables:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_id,
                       event_date
                  FROM life_events
                 WHERE chart_id = %s
                   AND event_date < '2020-01-01'
                 ORDER BY event_date
                """,
                (chart_id,),
            )
            rows = cur.fetchall()
        events: list[tuple[str, date]] = []
        for r in rows:
            if isinstance(r, dict):
                eid = str(r["event_id"])
                edate = r["event_date"]
            else:
                eid, edate = str(r[0]), r[1]
            if isinstance(edate, str):
                edate = date.fromisoformat(edate)
            # Double-check TEST split (belt and suspenders)
            if edate < TEST_SPLIT_BOUNDARY:
                events.append((eid, edate))
        return events

    logger.warning(
        "life_events table not found for Abhinandan chart %s. "
        "Found tables: %s. Cross-chart pooling will use native-only result as prior.",
        chart_id,
        found_tables,
    )
    return []


def store_calibration_results(
    conn: Any,
    fit_run_id: str,
    weights: list[MechanismWeight],
    provenance: dict,
) -> None:
    """
    Write fitted weights to gochara_v3_calibration table.

    Uses ON CONFLICT DO UPDATE for idempotency per (fit_run_id, toggle_key).
    This is the ONLY write operation in this script; everything else is SELECT.
    """
    for w in weights:
        per_chart_hit_rates = {
            "native": {
                "n_train": w.n_train_native,
            },
            "abhinandan": {
                "n_train": w.n_train_abhinandan,
            },
        }
        fit_prov = {
            **provenance,
            "ablation_method": w.ablation_method,
        }
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gochara_v3_calibration (
                    fit_run_id,
                    wave,
                    mechanism_id,
                    toggle_key,
                    weight_value,
                    pooled_delta_hit_rate,
                    delta_native,
                    delta_abhinandan,
                    n_train_events_native,
                    n_train_events_abhinandan,
                    per_chart_hit_rates,
                    fit_provenance
                ) VALUES (
                    %s, 'W4.4', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (fit_run_id, toggle_key) DO UPDATE SET
                    weight_value              = EXCLUDED.weight_value,
                    pooled_delta_hit_rate     = EXCLUDED.pooled_delta_hit_rate,
                    delta_native              = EXCLUDED.delta_native,
                    delta_abhinandan          = EXCLUDED.delta_abhinandan,
                    n_train_events_native     = EXCLUDED.n_train_events_native,
                    n_train_events_abhinandan = EXCLUDED.n_train_events_abhinandan,
                    per_chart_hit_rates       = EXCLUDED.per_chart_hit_rates,
                    fit_provenance            = EXCLUDED.fit_provenance,
                    fitted_at                 = NOW()
                """,
                (
                    fit_run_id,
                    w.mechanism_id,
                    w.toggle_key,
                    w.final_weight,
                    w.pooled_delta,
                    w.delta_native,
                    w.delta_abhinandan,
                    w.n_train_native,
                    w.n_train_abhinandan,
                    json.dumps(per_chart_hit_rates),
                    json.dumps(fit_prov),
                ),
            )


# ═══════════════════════════════════════════════════════════════════════════
# Pure fit core (DB-free) — Stages A(hit-rate)/B/C
# ═══════════════════════════════════════════════════════════════════════════

# Ablation methods that mean "no legitimate signal in this corpus for this
# mechanism" — delta is forced to an honest 0.0 rather than computed via a
# hit-rate comparison. "ablation_not_computable" (empty corpus) and
# "mechanism_not_wired" (PARIṢKĀRA MR-14-matching: mechanism confirmed not
# invoked anywhere in engine.py's production path) are DIFFERENT reasons —
# both honest nulls, kept as distinct labels in ablation_method — sharing
# only this delta=0.0 short-circuit so neither one fabricates a proxy signal.
_NO_SIGNAL_ABLATION_METHODS = ("ablation_not_computable", "mechanism_not_wired")


def compute_mechanism_weights(
    admitted_metas: list[MechanismMeta],
    native_windows: list[GochaWindow],
    abhinandan_windows: list[GochaWindow],
    native_train_pairs: list[tuple[str, date]],
    abhinandan_train_pairs: list[tuple[str, date]],
    n_native: int,
    n_abhinandan: int,
    abhinandan_available: bool,
) -> tuple[list[MechanismWeight], float, float]:
    """
    Pure (DB-free) core of W4.4 Stages A(hit-rate)/B/C: compute per-mechanism
    weights from already-loaded windows + events.

    This IS the production fit computation — `build_weight_fitting_report`
    calls this function directly after its own DB-bound loads (mechanism
    registry YAML, live v3 windows, live TRAIN events); the PARIṢKĀRA
    MR-14-matching golden test also calls this function directly with a
    hand-constructed synthetic corpus, exercising the exact same code that
    runs in production rather than a re-implementation or a mock of it.

    Returns (mechanism_weights, hit_rate_full_native, hit_rate_full_abhinandan).
    """
    # Stage A: full hit_rate (all mechanisms included)
    hit_rate_full_native, _, _ = compute_hit_rate_from_windows(
        native_windows, native_train_pairs, ablate=False
    )
    if abhinandan_available:
        hit_rate_full_abhinandan, _, _ = compute_hit_rate_from_windows(
            abhinandan_windows, abhinandan_train_pairs, ablate=False
        )
    else:
        hit_rate_full_abhinandan = hit_rate_full_native  # treat native as prior

    logger.info("Stage A — hit_rate_full native=%.4f abhinandan=%.4f",
                hit_rate_full_native, hit_rate_full_abhinandan)

    # ── Stage B: Per-mechanism ablation ─────────────────────────────────────
    mechanism_weights: list[MechanismWeight] = []

    for meta in admitted_metas:
        toggle_key = meta.toggle_key
        logger.info("Stage B — ablating %s", toggle_key)

        ablation_method_native = _determine_ablation_method(native_windows, toggle_key)
        ablation_method_abhinandan = (
            _determine_ablation_method(abhinandan_windows, toggle_key)
            if abhinandan_available else "ablation_not_computable"
        )

        # If no windows at all -> honest delta=0
        if not native_windows:
            delta_native = 0.0
            ablation_method = "ablation_not_computable"
        else:
            if ablation_method_native in _NO_SIGNAL_ABLATION_METHODS:
                # I4/§N.8: cannot compute a real signal from this corpus for
                # this mechanism — honest 0, never a fabricated proxy.
                delta_native = 0.0
                ablation_method = ablation_method_native
            else:
                hit_rate_without_native, _, _ = compute_hit_rate_from_windows(
                    native_windows, native_train_pairs,
                    toggle_key=toggle_key, ablate=True,
                )
                delta_native = hit_rate_full_native - hit_rate_without_native
                ablation_method = ablation_method_native

        if abhinandan_available and abhinandan_windows:
            if ablation_method_abhinandan in _NO_SIGNAL_ABLATION_METHODS:
                delta_abhinandan = 0.0
                if ablation_method == "proxy_fraction":
                    ablation_method = "proxy_fraction"
            else:
                hit_rate_without_abhinandan, _, _ = compute_hit_rate_from_windows(
                    abhinandan_windows, abhinandan_train_pairs,
                    toggle_key=toggle_key, ablate=True,
                )
                delta_abhinandan = hit_rate_full_abhinandan - hit_rate_without_abhinandan
                if ablation_method_abhinandan == "term_breakdown" and ablation_method == "term_breakdown":
                    ablation_method = "term_breakdown"
                elif ablation_method not in _NO_SIGNAL_ABLATION_METHODS:
                    ablation_method = "proxy_fraction"
        else:
            # Approximate: treat native delta as prior for abhinandan.
            # (n_eff_abh, computed just below from the same abhinandan_available
            # condition, is what actually reaches compute_pooled_delta as
            # n_abhinandan=0 — weight 0 in pooling. A separate
            # `n_effective_abhinandan = 0` local used to be assigned here and
            # never read; removed as dead code, PARIṢKĀRA MR-14 cleanup.)
            delta_abhinandan = delta_native

        # ── Stage C: Cross-chart partial pooling + shrinkage ─────────────────
        # When Abhinandan is unavailable, n_effective_abhinandan=0 means the
        # pooled result equals delta_native (no actual pooling, native-only).
        n_eff_abh = n_abhinandan if abhinandan_available else 0
        pooled_delta, pooled_delta_shrunk = compute_pooled_delta(
            delta_native=delta_native,
            delta_abhinandan=delta_abhinandan,
            n_native=n_native,
            n_abhinandan=n_eff_abh,
            prior_strength=SHRINKAGE_PRIOR_K,
        )

        # Non-negative weight: a mechanism that doesn't help pooled score gets 0
        final_weight = max(0.0, pooled_delta_shrunk)

        mechanism_weights.append(
            MechanismWeight(
                mechanism_id=meta.mechanism_id,
                toggle_key=toggle_key,
                delta_native=round(delta_native, 6),
                delta_abhinandan=round(delta_abhinandan, 6),
                pooled_delta=round(pooled_delta, 6),
                pooled_delta_shrunk=round(pooled_delta_shrunk, 6),
                final_weight=round(final_weight, 6),
                ablation_method=ablation_method,
                admitted=True,
                n_train_native=n_native,
                n_train_abhinandan=n_eff_abh,
            )
        )

        logger.info(
            "  %s: delta_native=%.4f delta_abh=%.4f pooled=%.4f shrunk=%.4f weight=%.4f method=%s",
            toggle_key, delta_native, delta_abhinandan,
            pooled_delta, pooled_delta_shrunk, final_weight, ablation_method,
        )

    return mechanism_weights, hit_rate_full_native, hit_rate_full_abhinandan


# ═══════════════════════════════════════════════════════════════════════════
# Main build function
# ═══════════════════════════════════════════════════════════════════════════

def build_weight_fitting_report(conn: Any) -> dict:
    """
    Build the W4.4 weight fitting report using the provided DB connection.

    Implements Stages A, B, C per the spec:
      A -- Cross-chart baseline hit_rate (all mechanisms included)
      B -- Per-mechanism ablation (excluded one at a time)
      C -- Cross-chart partial pooling + shrinkage

    Stages A(hit-rate)/B/C are delegated to `compute_mechanism_weights` (pure,
    DB-free) — this function's own job is the DB-bound loading around it.

    Returns the full JSON report dict. Caller is responsible for printing/storing.

    The connection must be dict_row enabled (psycopg.rows.dict_row) or compatible.
    """
    fit_run_id = str(uuid.uuid4())
    logger.info("W4.4 fit_run_id: %s", fit_run_id)

    # ── Load mechanism registry ──────────────────────────────────────────────
    mechanism_registry = load_mechanism_registry()
    admitted_metas = [m for m in mechanism_registry if m.mechanism_id in ADMITTED_MECHANISM_IDS]
    structural_metas = [m for m in mechanism_registry if m.mechanism_id in STRUCTURAL_ONLY_IDS]

    logger.info("Mechanism registry: %d admitted, %d structural-only",
                len(admitted_metas), len(structural_metas))

    # ── Stage A: Load events and v3 windows ─────────────────────────────────
    # Native TRAIN events (via lel.py cache — enforces TEST split)
    native_lel_events = load_train_events()  # raises SealedTestSplitViolation if contaminated
    native_scorable, _excluded = partition_scorable(native_lel_events)
    native_train_pairs: list[tuple[str, date]] = [
        (e.event_id, e.event_date) for e in native_scorable
    ]
    for _eid, edate in native_train_pairs:
        assert edate < TEST_SPLIT_BOUNDARY, "unreachable — load_train_events already enforces this"

    # Abhinandan TRAIN events (from DB, WHERE event_date < '2020-01-01')
    abhinandan_train_pairs = load_abhinandan_train_events(conn, ABHINANDAN_CHART_ID)
    abhinandan_available = len(abhinandan_train_pairs) > 0
    if not abhinandan_available:
        logger.warning(
            "Abhinandan train events not available. "
            "Cross-chart pooling approximated: native result treated as prior."
        )

    n_native = len(native_train_pairs)
    n_abhinandan = len(abhinandan_train_pairs)

    logger.info("Native TRAIN scorable events: %d", n_native)
    logger.info("Abhinandan TRAIN events: %d", n_abhinandan)

    # Load v3 windows (SELECT only)
    native_windows = load_v3_windows(conn, NATIVE_CHART_ID)
    abhinandan_windows = load_v3_windows(conn, ABHINANDAN_CHART_ID) if abhinandan_available else []

    logger.info("Native v3 windows: %d rows", len(native_windows))
    logger.info("Abhinandan v3 windows: %d rows", len(abhinandan_windows))

    # ── Stages A(hit-rate)/B/C: delegate to the pure fit core ────────────────
    mechanism_weights, hit_rate_full_native, hit_rate_full_abhinandan = compute_mechanism_weights(
        admitted_metas=admitted_metas,
        native_windows=native_windows,
        abhinandan_windows=abhinandan_windows,
        native_train_pairs=native_train_pairs,
        abhinandan_train_pairs=abhinandan_train_pairs,
        n_native=n_native,
        n_abhinandan=n_abhinandan,
        abhinandan_available=abhinandan_available,
    )

    # ── Dataset hash for provenance ──────────────────────────────────────────
    dataset_hash = compute_dataset_hash(native_train_pairs, abhinandan_train_pairs)

    # ── Store results in gochara_v3_calibration ──────────────────────────────
    provenance = {
        "harness": "w44_weight_fitting",
        "wave": "W4.4",
        "fit_run_id": fit_run_id,
        "native_chart_id": NATIVE_CHART_ID,
        "abhinandan_chart_id": ABHINANDAN_CHART_ID,
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "n_train_events_native": n_native,
        "n_train_events_abhinandan": n_abhinandan,
        "abhinandan_events_not_available_in_db": not abhinandan_available,
        "shrinkage_prior_k": SHRINKAGE_PRIOR_K,
        "proxy_ablation_fraction": PROXY_ABLATION_FRACTION,
        "dataset_hash": dataset_hash,
        "hit_rate_full_native": round(hit_rate_full_native, 6),
        "hit_rate_full_abhinandan": round(hit_rate_full_abhinandan, 6),
        "native_v3_windows_count": len(native_windows),
        "abhinandan_v3_windows_count": len(abhinandan_windows),
    }

    store_calibration_results(conn, fit_run_id, mechanism_weights, provenance)
    conn.commit()

    # ── Build output JSON ────────────────────────────────────────────────────
    report = {
        "harness": "w44_weight_fitting",
        "wave": "W4.4",
        "chart_ids": {
            "native": NATIVE_CHART_ID,
            "abhinandan": ABHINANDAN_CHART_ID,
        },
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "n_train_events_native": n_native,
        "n_train_events_abhinandan": n_abhinandan,
        "abhinandan_events_not_available_in_db": not abhinandan_available,
        "hit_rate_full_native": round(hit_rate_full_native, 6),
        "hit_rate_full_abhinandan": round(hit_rate_full_abhinandan, 6),
        "native_v3_windows_count": len(native_windows),
        "abhinandan_v3_windows_count": len(abhinandan_windows),
        "shrinkage_prior_k": SHRINKAGE_PRIOR_K,
        "shrinkage_prior_documented": (
            "k=3 is a calibration choice: with n_total=60, shrinkage=60/63≈0.952 (mild); "
            "with n_total=10, shrinkage=10/13≈0.769 (stronger for sparse charts). "
            "Not inherited doctrine — chosen to reflect O(30) events per chart uncertainty."
        ),
        "proxy_ablation_fraction_documented": (
            f"When term_breakdown is absent, mechanism contribution is approximated as "
            f"{PROXY_ABLATION_FRACTION} * abs(signed_intensity). "
            "This is a conservative lower-bound proxy, not a true ablation."
        ),
        "mechanism_weights": [
            {
                "mechanism_id": w.mechanism_id,
                "toggle_key": w.toggle_key,
                "delta_native": w.delta_native,
                "delta_abhinandan": w.delta_abhinandan,
                "pooled_delta": w.pooled_delta,
                "pooled_delta_shrunk": w.pooled_delta_shrunk,
                "final_weight": w.final_weight,
                "ablation_method": w.ablation_method,
                "admitted": w.admitted,
            }
            for w in mechanism_weights
        ],
        "structural_only": STRUCTURAL_ONLY_IDS,
        "fit_run_id": fit_run_id,
        "dataset_hash": dataset_hash,
    }
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    dsn = _require_database_url()
    psycopg = _require_psycopg()

    try:
        with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row) as conn:
            report = build_weight_fitting_report(conn)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: weight fitting failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
