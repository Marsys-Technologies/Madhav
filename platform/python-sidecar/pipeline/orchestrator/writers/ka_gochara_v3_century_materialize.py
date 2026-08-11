"""ka_gochara_v3_century_materialize — W3.4/W5.4 Century horizon + slice receipts.

GOCHARA-UTKARSA campaign, wave W3.4 (original) + W5.4 (writer repoint).

Gate: W0.3 PASS (generation schema + utkarsha_builder role in place) +
      W3.2 PASS (interval_solver root-solved threshold crossings) +
      UTK-R1 ADJUDICATOR ruling (W5.4 repoint to kala_gochara_windows generation='3.0').

PURPOSE
-------
Extends the W0.2/W2G materializer concept to a CENTURY-SCALE HEAVY writer
using the gochara_v3 engine (not v1's gochara_intensity grammar). The
unit of work is one (event_class × decade_era_slice) pair — 70 substeps
for 7 event classes × 10 decade slices spanning the native's century from
birth (1984-02-05 to 2084-02-05). (PARIṢKĀRA MR-12: EVENT_CLASSES gained
'business_launch', the first genuinely chain-canonical class this writer
produces temporal_shape='chain' rows for — was 60/6 pre-MR-12.)

Key behaviours:
  1. plan_substeps — returns len(EVENT_CLASSES) x 10 SubStep objects, one per
     (event_class, decade_slice). substep_key = '{event_class}::{era_slice_key}'.
  2. run_substep — for each substep:
       a. Compute a delta fingerprint from (event_class, era_slice_key,
          ENGINE_VERSION, resonance_targets) via MD5.
       b. Check kala_gochara_v2_build_state for a matching stored fingerprint.
       c. If fingerprint unchanged AND rows exist: skip (honest no-op).
       d. Else: call find_threshold_crossings from gochara_v3.interval_solver
          over the decade JD range; DELETE-then-INSERT results into BOTH:
            * kala_gochara_windows_v2 (calibration/staging surface, generation='g3_utkarsha')
            * kala_gochara_windows (production surface, generation='3.0') [W5.4 repoint]
       e. Upsert fingerprint to kala_gochara_v2_build_state.
       f. Log wall-clock time per substep at DEBUG level (AC5 / first SLO
          evidence point).
  3. I2 constraint: ZERO imports from gochara_grammar/*, gochara_intensity/*,
     or ka_gochara_sweep/*. All scoring comes from gochara_v3.interval_solver
     and gochara_v3.engine (AC6).
  4. I4 constraint: empty resonance targets → honest 0 rows for that substep,
     no fabrication (AC7).

TABLES
------
Write target 1: kala_gochara_windows_v2  (calibration/staging surface;
                generation='g3_utkarsha'; never touches v1 rows)
Write target 2: kala_gochara_windows  (production surface; generation='3.0';
                I1 rail: DB trigger protects generation='v1' rows for the two
                canonical charts — generation='3.0' writes pass through safely)
Build state:    kala_gochara_v2_build_state  (substep-keyed fingerprint)

W5.4 REPOINT (UTK-R1)
----------------------
Per ADJUDICATOR ruling UTK-R1, the production writer's FINAL target is
kala_gochara_windows with generation='3.0'. W5.4 adds this production write
while retaining the kala_gochara_windows_v2 calibration write.

I1 INVARIANT
------------
Every DML statement against kala_gochara_windows MUST carry the
generation='3.0' predicate. The mutation-guard test
(test_ka_gochara_v3_mutation_guard.py) enforces this invariant and is
mutation-tested to prove it is a real detector.

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v3_century_materialize')  on a WriterBase subclass
  * HEAVY: plan_substeps(ctx) + run_substep(ctx, step)
  * ctx.db_conn — writer reads/writes on it, NEVER commits or closes it
  * Never writes asset_throughput

IDEMPOTENCY (§N.3)
------------------
Delete-then-INSERT scoped to:
  kala_gochara_windows_v2: (chart_id × event_class × generation='g3_utkarsha' × era_slice_key)
  kala_gochara_windows:    (chart_id × event_class × generation='3.0' × era_slice_key)

I2 STATIC CHECK (for test_w34_century_horizon.py)
---------------------------------------------------
The following import prefixes MUST NOT appear in this module's CODE
(they are named in the module docstring only for documentation):
  - services.gochara_grammar
  - services.gochara_intensity
  - services.ka_gochara_sweep
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)

# gochara_v3 imports only (I2: no gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*)
from services.gochara_v3.interval_solver import (
    find_threshold_crossings, score_chain_milestones, IntervalBoundary, MilestoneScore,
)
from services.gochara_v3.threshold import ThresholdConfig, fetch_base_rate_for_class
from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASSET_ID = "ka_gochara_v3_century_materialize"

# Generation label for the calibration/staging surface (kala_gochara_windows_v2).
GENERATION_V3 = "g3_utkarsha"

# Generation label for the production surface (kala_gochara_windows).
# Per UTK-R1 ADJUDICATOR ruling (W5.4 repoint): every DML statement against
# kala_gochara_windows MUST carry this predicate — enforced by the mutation-guard
# test (test_ka_gochara_v3_mutation_guard.py).
GENERATION_PROD = "3.0"

# Engine version for fingerprinting.  Bumped whenever the scoring engine
# changes in a way that would move a stored window.  gochara_v3/__init__.py
# exports GRAMMAR_VERSION; we use our own constant so this writer's
# fingerprint is stable across internal gochara_v3 refactors that do NOT
# move window positions.
# PARIṢKĀRA MR-12 (Codex C2): bumped v3.0 -> v3.1 because this writer's
# output SHAPE changed (chain-shaped rows are now possible for
# temporal_shape='chain' classes) -- a delta-fingerprint-relevant change per
# compute_substep_fingerprint's own "engine_version bumped when scoring logic
# changes" contract, even though existing point/interval classes' scoring is
# byte-for-byte unchanged.
ENGINE_VERSION = "v3.1"

# The event classes this writer handles (same 6 as W0.2 materializer, plus
# MR-12's business_launch addition -- see _fetch_class_shape/_SHAPE_FALLBACK
# below for why business_launch, not marriage, is the first genuinely
# chain-canonical class this writer produces chain rows for).
EVENT_CLASSES = [
    "career_advancement",
    "major_gain",
    "marriage",
    "illness_acute",
    "chronic_onset",
    "surgery",
    "business_launch",
]

# Julian Day for 1984-02-05 00:00 UTC (native birth date).
# JD = 2445736.5  (standard astronomical reference).
BIRTH_JD: float = 2445736.5

# Birth year for decade-slice labelling.
BIRTH_YEAR: int = 1984

# Number of decade slices in a century build.
DECADE_COUNT: int = 10

# Days per Julian year (standard astronomical).
DAYS_PER_YEAR: float = 365.25

# Table constants.
# Calibration/staging surface (W3.4 original target): kala_gochara_windows_v2.
TABLE = "kala_gochara_windows_v2"
# Production surface (W5.4 repoint, UTK-R1): kala_gochara_windows with generation='3.0'.
# I1 rail: the DB trigger on this table protects generation='v1' rows for the two
# canonical charts (482012f1-… and 1c826d5a-…). generation='3.0' writes are
# explicitly allowed by the generation-aware guard (migration 556).
PROD_TABLE = "kala_gochara_windows"
BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

# INSERT template for kala_gochara_windows_v2 (calibration/staging).
# PARIṢKĀRA MR-14: the 4 W1.5 λ-decomposition columns (migration 559 on this
# table; migration 564 mirrored them onto the production table) are now
# populated from IntervalBoundary (see _build_row) instead of being silently
# omitted — the prior defect this fix closes (register PG-6/PG-7).
INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb,
       %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s,
       %(generation)s, %(era_slice_key)s,
       %(term_breakdown)s::jsonb, %(lambda_v3_ci_low)s, %(lambda_v3_ci_high)s,
       %(ci_source)s)
"""

# INSERT template for kala_gochara_windows (production, W5.4 repoint, UTK-R1).
# Every DML on this table MUST carry generation='3.0' — enforced by the
# mutation-guard test (test_ka_gochara_v3_mutation_guard.py).
# I1 mutation-guard anchor: generation='3.0' (%(generation)s parameter always
# bound to GENERATION_PROD='3.0'; literal here for static-source guard coverage).
# PARIṢKĀRA MR-14: same 4 W1.5 columns as INSERT_SQL above (migration 564
# added them to this table, nullable, additive — see MASTER_REMEDIATION_
# REGISTER_v2_0.md MR-01/MR-14).
INSERT_PROD_SQL = f"""
    INSERT INTO {PROD_TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb,
       %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s,
       %(generation)s, %(era_slice_key)s,
       %(term_breakdown)s::jsonb, %(lambda_v3_ci_low)s, %(lambda_v3_ci_high)s,
       %(ci_source)s)
    -- W5.4 I1 invariant: generation='3.0' only; v1 rows are protected by DB trigger
"""


# ---------------------------------------------------------------------------
# Decade-slice helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecadeSlice:
    """One 10-year era slice in the century build.

    Fields
    ------
    era_slice_key   'g3_{year_start}_{year_end}', e.g. 'g3_1984_1994'.
    start_jd        Julian Day for the start of the decade (birth anniversary).
    end_jd          Julian Day for the end of the decade (next decade's start).
    year_start      Calendar year label for the slice start.
    year_end        Calendar year label for the slice end.
    """
    era_slice_key: str
    start_jd: float
    end_jd: float
    year_start: int
    year_end: int


def build_decade_slices() -> list[DecadeSlice]:
    """Return 10 DecadeSlice objects covering the century from BIRTH_JD.

    Slice boundaries are exact Julian Days computed as:
        start_jd = BIRTH_JD + decade_index × 10 × DAYS_PER_YEAR
        end_jd   = BIRTH_JD + (decade_index + 1) × 10 × DAYS_PER_YEAR

    Labels use calendar years: 'g3_{BIRTH_YEAR + 0}_{BIRTH_YEAR + 10}',
    'g3_{BIRTH_YEAR + 10}_{BIRTH_YEAR + 20}', …

    Returns exactly DECADE_COUNT = 10 slices.
    """
    slices: list[DecadeSlice] = []
    for i in range(DECADE_COUNT):
        year_start = BIRTH_YEAR + i * 10
        year_end = BIRTH_YEAR + (i + 1) * 10
        start_jd = BIRTH_JD + i * 10 * DAYS_PER_YEAR
        end_jd = BIRTH_JD + (i + 1) * 10 * DAYS_PER_YEAR
        era_slice_key = f"g3_{year_start}_{year_end}"
        slices.append(DecadeSlice(
            era_slice_key=era_slice_key,
            start_jd=start_jd,
            end_jd=end_jd,
            year_start=year_start,
            year_end=year_end,
        ))
    return slices


# Module-level constant: the 10 decade slices (built once at import time).
DECADE_SLICES: list[DecadeSlice] = build_decade_slices()


# ---------------------------------------------------------------------------
# Fingerprint computation
# ---------------------------------------------------------------------------

def compute_substep_fingerprint(
    event_class: str,
    era_slice_key: str,
    engine_version: str,
    resonance_targets: list[str],
) -> str:
    """Compute a delta fingerprint for one (event_class, era_slice) substep.

    The fingerprint is an MD5 hex digest of a canonicalized JSON payload
    covering the four inputs that, if changed, would require a rebuild:
      * event_class      — the class being scored.
      * era_slice_key    — the decade window.
      * engine_version   — bumped when scoring logic changes.
      * resonance_targets — sorted list of target_ref strings for this chart×class.

    Inputs are sorted so the fingerprint is stable across row-order changes.

    Returns
    -------
    str — 32-character MD5 hex digest.
    """
    payload = json.dumps(
        {
            "event_class": event_class,
            "era_slice_key": era_slice_key,
            "engine_version": engine_version,
            "resonance_targets": sorted(resonance_targets),
        },
        sort_keys=True,
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _query_fn(conn):
    """Return a callable that executes SQL and returns list[dict]."""
    def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        cur = conn.execute(sql, params or [])
        rows = cur.fetchall()
        return [dict(r) if not isinstance(r, dict) else r for r in rows]
    return query



# ---------------------------------------------------------------------------
# Valence — honest per-event_class derivation (PARIṢKĀRA MR-13, F#1 fix)
# ---------------------------------------------------------------------------
#
# PRIOR DEFECT: _build_row() hardcoded "valence": "favourable" for every
# event_class it serves, including the adverse-natured health classes
# (illness_acute, chronic_onset — canonical valence 'loss' per
# brahma_event_ontology) and surgery (canonical valence 'neutral'). A
# hardcoded favourable default standing in for a real per-class judgment is
# exactly the dishonest-default pattern §N.7/§N.8 exist to close.
#
# FIX: read the canonical valence live from
# brahma_event_ontology.evidence_requirements->>'valence' (migration 456) --
# the SAME field services/gochara_intensity/valence.py::VALENCE_MAP and
# services/gochara_grammar/event_class_scope.py transcribe, but read here via
# a direct SQL query (never an import of those modules -- I2/AC6 forbids
# importing gochara_intensity/gochara_grammar in this writer's code, not a
# read of the shared ontology table this module already reads elsewhere via
# fetch_base_rate_for_class/_fetch_resonance_targets).
#
# Fallback (live read fails / no row / ontology unreachable): a small,
# explicitly documented map covering ONLY the 6 EVENT_CLASSES this writer
# handles, transcribed from the same migration 456 values -- "live-preferred,
# documented fallback, never silently invented" (identical discipline to
# every sibling fetch_* in this codebase). An event_class this writer does
# not know about at all degrades to 'neutral' (the codebase's own
# established unknown-class convention, e.g.
# gochara_intensity.valence.fetch_valence's own default) -- NEVER
# 'favourable'/'gain', which would repeat the exact defect this fix removes.
_VALENCE_FALLBACK: dict[str, str] = {
    "career_advancement": "gain",
    "major_gain": "gain",
    "marriage": "neutral",
    "illness_acute": "loss",
    "chronic_onset": "loss",
    "surgery": "neutral",
}


def _fetch_class_valence(conn, event_class: str) -> tuple[str, bool]:
    """Return (valence, is_adverse) for `event_class`.

    valence is one of the kala_gochara_windows schema's own vocabulary
    values -- 'gain'|'loss'|'neutral'|'mixed' (migration 460) -- read
    directly from brahma_event_ontology, no engine-vocab translation needed
    (unlike ka_gochara.py's v1-engine _VALENCE_MAP, which translates a
    DIFFERENT vocabulary). is_adverse is True iff valence == 'loss' --
    matching gochara_intensity.valence.is_adverse's own sign rule for the
    classes this writer serves (none of EVENT_CLASSES carry the
    psychological_arc 'mixed'-override case).
    """
    try:
        cur = conn.execute(
            "SELECT evidence_requirements->>'valence' AS valence "
            "FROM brahma_event_ontology WHERE event_class_id = %s",
            [event_class],
        )
        row = cur.fetchone()
        if row is not None:
            v = row["valence"] if isinstance(row, dict) else row[0]
            if v:
                v = str(v)
                return v, (v == "loss")
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[%s] brahma_event_ontology valence read failed for "
            "event_class=%s, falling back to documented fixture: %s",
            ASSET_ID, event_class, exc,
        )
    v = _VALENCE_FALLBACK.get(event_class, "neutral")
    return v, (v == "loss")


# ---------------------------------------------------------------------------
# Temporal shape + milestone_template (PARIṢKĀRA MR-12: chain production
# wiring) — honest per-event_class derivation, same "live-preferred,
# documented fallback" discipline as _fetch_class_valence above.
# ---------------------------------------------------------------------------
#
# BRIEF_D5 §3 (migration 460, BINDING): a served row's shape MUST mirror its
# event_class's brahma_event_ontology.temporal_shape -- point/interval/chain,
# never more temporal precision than the ontology declares. This writer was
# already shape-aware for point/interval (both stamped "interval" pre-MR-12,
# unchanged by this fix -- point-row production is a separate, already-closed
# lane, MR-10/MR-11); MR-12 is the first time this writer reads the ontology's
# 'chain' branch and produces milestone_template-shaped output.
#
# HONEST FINDING (MR-12, 2026-08-11 session): the register item's "marriage
# first" framing does NOT match the live ontology. brahma_event_ontology
# (migration 456) declares marriage temporal_shape='point' explicitly, with
# its own note: "a future v2 could split into a chain (engagement -> ceremony
# -> registration) if per-milestone dates become available." It is not a
# chain today, and brahma_event_ontology's own CHECK constraint (migration
# 456, brahma_event_ontology_shape_data_consistency_check) forbids storing a
# chain-shaped row without a real milestone_template of >=2 entries -- so
# marriage cannot honestly produce chain rows without either fabricating an
# ontology override (B.10 violation) or a native-ruled ontology amendment
# (out of this CODE-ONLY session's authority). See PARISHKARA_LEDGER.md
# "MR-12" entry (parishkara/campaign branch) for the full account.
#
# 'business_launch' is the first GENUINELY chain-canonical class this writer
# is wired to produce rows for: temporal_shape='chain', 3-milestone template
# (decision -> registration -> first_revenue), irreversibility_milestone=
# 'first_revenue' -- BRIEF_D4A Lane A-2's own worked example (migration 456).
_SHAPE_FALLBACK: dict[str, dict[str, Any]] = {
    "career_advancement": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "major_gain": {
        "temporal_shape": "interval", "milestone_template": None, "irreversibility_milestone": None,
    },
    "marriage": {
        # Matches live brahma_event_ontology (migration 456) — NOT 'chain'.
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "illness_acute": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "chronic_onset": {
        "temporal_shape": "interval", "milestone_template": None, "irreversibility_milestone": None,
    },
    "surgery": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "business_launch": {
        "temporal_shape": "chain",
        "milestone_template": [
            {"milestone_id": "decision", "name_en": "Decision to found/launch",
             "typical_offset_days_from_first": 0},
            {"milestone_id": "registration", "name_en": "Legal/business registration",
             "typical_offset_days_from_first": 45},
            {"milestone_id": "first_revenue", "name_en": "First revenue booked",
             "typical_offset_days_from_first": 120},
        ],
        "irreversibility_milestone": "first_revenue",
    },
}


def _fetch_class_shape(
    conn, event_class: str,
) -> tuple[str, Optional[list[dict]], Optional[str]]:
    """Return (temporal_shape, milestone_template, irreversibility_milestone)
    for `event_class`.

    Live-reads brahma_event_ontology; falls back to `_SHAPE_FALLBACK` (honest,
    documented fixture) on any DB-shape surprise, identical discipline to
    `_fetch_class_valence`. An event_class absent from BOTH the live table and
    the fallback degrades to temporal_shape='interval' (this writer's
    pre-MR-12 universal behavior) with no milestone_template -- NEVER
    invented as 'chain' (I4: a shape this writer cannot honestly support is
    never guessed into existence).

    milestone_template is returned in the RAW ontology shape
    ({milestone_id, name_en, typical_offset_days_from_first}) — see
    `_normalize_milestone_template` for the adapter into
    `score_chain_milestones`'s expected per-entry shape.
    """
    try:
        cur = conn.execute(
            "SELECT temporal_shape, milestone_template, irreversibility_milestone "
            "FROM brahma_event_ontology WHERE event_class_id = %s",
            [event_class],
        )
        row = cur.fetchone()
        if row is not None:
            d = row if isinstance(row, dict) else dict(
                zip(["temporal_shape", "milestone_template", "irreversibility_milestone"], row)
            )
            shape = d.get("temporal_shape")
            if shape:
                template = d.get("milestone_template")
                if isinstance(template, str):
                    try:
                        template = json.loads(template)
                    except Exception:  # noqa: BLE001
                        template = None
                return str(shape), template, d.get("irreversibility_milestone")
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[%s] brahma_event_ontology shape read failed for event_class=%s, "
            "falling back to documented fixture: %s",
            ASSET_ID, event_class, exc,
        )
    fallback = _SHAPE_FALLBACK.get(event_class)
    if fallback is None:
        return "interval", None, None
    return fallback["temporal_shape"], fallback["milestone_template"], fallback["irreversibility_milestone"]


def _normalize_milestone_template(
    raw_template: list[dict], irreversibility_milestone: Optional[str],
) -> list[dict]:
    """Adapt brahma_event_ontology's milestone_template entry shape
    ({milestone_id, name_en, typical_offset_days_from_first}) into
    `gochara_v3.interval_solver.score_chain_milestones`'s expected per-entry
    shape ({milestone_id, typical_offset_days, is_irreversibility_milestone}).

    The ontology does NOT carry an is_irreversibility_milestone flag per
    milestone-entry — it names the ONE irreversibility milestone_id (if any)
    at the ontology-row level (the `irreversibility_milestone` column). This
    adapter is the exact wiring gap MR-12 was scoped to find and close:
    score_chain_milestones has existed, tested in isolation
    (test_w32_interval_solver.py), since W3.2 — nothing ever translated real
    ontology JSON into the shape it expects before this fix.
    """
    return [
        {
            "milestone_id": entry.get("milestone_id"),
            "typical_offset_days": entry.get("typical_offset_days_from_first", 0.0),
            "is_irreversibility_milestone": (
                entry.get("milestone_id") is not None
                and entry.get("milestone_id") == irreversibility_milestone
            ),
        }
        for entry in raw_template
    ]


def _build_chain_row(
    chart_id: str,
    event_class: str,
    milestone: MilestoneScore,
    era_slice_key: str,
    *,
    valence: str,
    is_adverse: bool,
    generation: str,
) -> dict[str, Any]:
    """Convert one MilestoneScore (gochara_v3.interval_solver) into a
    kala_gochara_windows(_v2) row dict — the chain-shape sibling of
    `_build_row`. Carries EXACTLY the same key set (verified by
    test_mr12_chain_production.py::test_build_chain_row_same_key_set_as_
    interval_row), so it binds against the SAME INSERT_SQL/INSERT_PROD_SQL
    templates unchanged — no new DML statement is introduced, so the I1
    mutation-guard's static source coverage (test_ka_gochara_v3_mutation_
    guard.py) needs no update for chain support.

    window_start = window_end = peak_date = this milestone's own JD (a
    chain-shaped row is one independently-dateable sub-window per milestone,
    per BRIEF_D5 §3 / migration 460's column comment).
    """
    milestone_date = _jd_to_date(milestone.milestone_jd)
    ir = milestone.intensity_result
    term_breakdown = ir.term_breakdown if ir is not None else None
    ci_low = ir.lambda_v3_ci_low if ir is not None else None
    ci_high = ir.lambda_v3_ci_high if ir is not None else None
    ci_source = ir.ci_source if ir is not None else None
    return {
        "chart_id": chart_id,
        "event_class": event_class,
        "temporal_shape": "chain",
        "window_start": milestone_date,
        "window_end": milestone_date,
        "peak_date": milestone_date,
        "milestone_id": milestone.milestone_id,
        "is_irreversibility_milestone": milestone.is_irreversibility_milestone,
        "signed_intensity": round(float(milestone.lambda_v3), 6),
        "raw_intensity": round(float(milestone.lambda_v3), 6),
        "valence": valence,
        "is_adverse": is_adverse,
        "active_sentences": json.dumps([]),
        "contributing_systems": json.dumps([]),
        "suppression_state": json.dumps({}),
        "peak_basis": "gochara_lambda_v3",
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": ci_low,
        "lambda_v3_ci_high": ci_high,
        "ci_source": ci_source,
    }


def _fetch_resonance_targets(conn, chart_id: str, event_class: str) -> list[str]:
    """Fetch resonance target_refs for this (chart_id, event_class) pair.

    Returns a sorted list of target_ref strings.
    Returns [] when the chart has no resonance targets for this class (I4).
    """
    try:
        cur = conn.execute(
            "SELECT DISTINCT target_ref FROM gochara_resonance_map "
            "WHERE chart_id = %s AND event_class = %s ORDER BY target_ref",
            [chart_id, event_class],
        )
        rows = cur.fetchall()
        return [
            (r["target_ref"] if isinstance(r, dict) else r[0])
            for r in rows
            if (r["target_ref"] if isinstance(r, dict) else r[0]) is not None
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[%s] could not fetch resonance targets for chart=%s event_class=%s: %s "
            "— honest empty (I4).",
            ASSET_ID, chart_id, event_class, exc,
        )
        return []


def _stored_fingerprint(query, chart_id: str, substep_key: str) -> str | None:
    """Return the stored fingerprint for this substep, or None if absent."""
    rows = query(
        f"SELECT class_fingerprint FROM {BUILD_STATE_TABLE} "
        f"WHERE chart_id = %s AND event_class = %s AND generation = %s",
        [chart_id, substep_key, GENERATION_V3],
    )
    if rows and rows[0].get("class_fingerprint"):
        return rows[0]["class_fingerprint"]
    return None


def _stored_rows_exist(query, chart_id: str, substep_key: str, era_slice_key: str) -> bool:
    """Return True if rows already exist in kala_gochara_windows_v2 for this substep."""
    # substep_key = '{event_class}::{era_slice_key}'; split to get event_class.
    event_class = substep_key.split("::", 1)[0]
    rows = query(
        f"SELECT 1 FROM {TABLE} "
        f"WHERE chart_id = %s AND event_class = %s AND generation = %s AND era_slice_key = %s "
        f"LIMIT 1",
        [chart_id, event_class, GENERATION_V3, era_slice_key],
    )
    return len(rows) > 0


def _upsert_build_state(
    conn,
    chart_id: str,
    substep_key: str,
    fingerprint: str,
    rows_written: int,
    skipped: bool,
    build_id: str,
) -> None:
    """Upsert a fingerprint record into kala_gochara_v2_build_state.

    Uses the existing table schema:
      PRIMARY KEY (chart_id, event_class, generation)
    with:
      event_class = substep_key  (e.g. 'marriage::g3_1984_1994')
      generation  = GENERATION_V3

    Required NOT NULL columns that we fill with honest sentinels:
      grammar_version, arc_engine_version, bodies_scope,
      horizon_start_date, horizon_end_date, horizon_status.
    """
    # Extract event_class and era_slice_key from substep_key for horizon dates.
    parts = substep_key.split("::", 1)
    era_slice_key = parts[1] if len(parts) == 2 else substep_key

    # Derive approximate horizon dates from the era_slice_key label.
    # Format: 'g3_{year_start}_{year_end}'.
    try:
        _, year_start_s, year_end_s = era_slice_key.split("_", 2)
        horizon_start = date(int(year_start_s), 2, 5)
        horizon_end = date(int(year_end_s), 2, 5)
    except Exception:  # noqa: BLE001
        horizon_start = date(1984, 2, 5)
        horizon_end = date(2084, 2, 5)

    skipped_reason = "fingerprint_unchanged" if skipped else None

    conn.execute(
        f"""
        INSERT INTO {BUILD_STATE_TABLE}
          (chart_id, event_class, generation, class_fingerprint,
           grammar_version, arc_engine_version, bodies_scope,
           horizon_start_date, horizon_end_date, horizon_status,
           contacts_evaluated, rows_written, skipped_reason, build_id, computed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (chart_id, event_class, generation) DO UPDATE SET
          class_fingerprint  = EXCLUDED.class_fingerprint,
          grammar_version    = EXCLUDED.grammar_version,
          arc_engine_version = EXCLUDED.arc_engine_version,
          bodies_scope       = EXCLUDED.bodies_scope,
          horizon_start_date = EXCLUDED.horizon_start_date,
          horizon_end_date   = EXCLUDED.horizon_end_date,
          horizon_status     = EXCLUDED.horizon_status,
          contacts_evaluated = EXCLUDED.contacts_evaluated,
          rows_written       = EXCLUDED.rows_written,
          skipped_reason     = EXCLUDED.skipped_reason,
          build_id           = EXCLUDED.build_id,
          computed_at        = now()
        """,
        [
            chart_id,
            substep_key,         # stored in event_class column
            GENERATION_V3,
            fingerprint,
            ENGINE_VERSION,      # grammar_version sentinel
            ENGINE_VERSION,      # arc_engine_version sentinel
            [],                  # bodies_scope (empty array; interval_solver handles bodies)
            horizon_start,
            horizon_end,
            "full_backfill",     # century build covers the full declared slice
            0,                   # contacts_evaluated (interval_solver doesn't expose this count)
            rows_written,
            skipped_reason,
            build_id,
        ],
    )


def _jd_to_date(jd: float) -> date:
    """Convert Julian Day number to a Python date.

    Uses a simple algorithm: JD 2440588.0 = 1970-01-01.
    Accurate to within 1 day across the 1984–2084 range we care about.
    """
    EPOCH_JD = 2440588.0  # JD for Unix epoch 1970-01-01
    days_since_epoch = int(jd - EPOCH_JD)
    return date(1970, 1, 1) + timedelta(days=days_since_epoch)


def _build_row(
    chart_id: str,
    event_class: str,
    boundary: IntervalBoundary,
    era_slice_key: str,
    *,
    valence: str,
    is_adverse: bool,
    generation: str = GENERATION_V3,
    term_breakdown: Optional[dict] = None,
    lambda_v3_ci_low: Optional[float] = None,
    lambda_v3_ci_high: Optional[float] = None,
    ci_source: Optional[str] = None,
) -> dict[str, Any]:
    """Convert one IntervalBoundary to a kala_gochara_windows(_v2) row dict.

    Parameters
    ----------
    valence
        REQUIRED -- the honest per-event_class valence
        ('gain'|'loss'|'neutral'|'mixed'), from `_fetch_class_valence`.
        No default: every caller must supply an honestly-derived value
        rather than a fixed literal (PARIṢKĀRA MR-13 fix -- this parameter
        used to be a hardcoded "favourable" string inside this function).
    is_adverse
        REQUIRED -- companion boolean from `_fetch_class_valence`.
    generation
        The generation label to stamp on the row.
        * GENERATION_V3 ('g3_utkarsha') → calibration row for kala_gochara_windows_v2
        * GENERATION_PROD ('3.0')       → production row for kala_gochara_windows
    term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source
        PARIṢKĀRA MR-14 fix (register PG-6/PG-7): the W1.5 λ decomposition +
        structural-prior credible interval, sourced from
        `IntervalBoundary.term_breakdown`/`.lambda_v3_ci_low`/`.lambda_v3_ci_high`/
        `.ci_source` (populated by `interval_solver.find_threshold_crossings`
        at the window's peak_jd). Callers pass `boundary.term_breakdown` etc.
        explicitly rather than this function reaching into `boundary` itself,
        matching the existing valence/is_adverse pattern of "every value this
        function serves is an explicit parameter, not silently derived
        in-body." All default None (I4 honest degrade: a boundary whose peak
        evaluation failed carries None here, never a fabricated breakdown).
    """
    window_start = _jd_to_date(boundary.enter_jd)
    window_end = _jd_to_date(boundary.exit_jd)
    peak_date = _jd_to_date(boundary.peak_jd)
    return {
        "chart_id": chart_id,
        "event_class": event_class,
        "temporal_shape": "interval",
        "window_start": window_start,
        "window_end": window_end,
        "peak_date": peak_date,
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "signed_intensity": round(float(boundary.peak_lambda), 6),
        "raw_intensity": round(float(boundary.peak_lambda), 6),
        "valence": valence,
        "is_adverse": is_adverse,
        "active_sentences": json.dumps([]),
        "contributing_systems": json.dumps([]),
        "suppression_state": json.dumps({}),
        "peak_basis": "gochara_lambda_v3",
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": lambda_v3_ci_low,
        "lambda_v3_ci_high": lambda_v3_ci_high,
        "ci_source": ci_source,
    }


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

@register(ASSET_ID)
class GocharaV3CenturyMaterializeWriter(WriterBase):
    """W3.4 Century-horizon writer using gochara_v3 engine + decade-slice substeps.

    See module docstring for the full spec contract.
    """

    asset_id = ASSET_ID
    has_substeps = True

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: plan_substeps
    # ------------------------------------------------------------------

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Return len(EVENT_CLASSES) x 10 SubStep objects (70 as of MR-12).

        Each SubStep has:
          key   = '{event_class}::{era_slice_key}'  e.g. 'marriage::g3_1984_1994'
          label = human-readable description

        The plan is STATIC — it does not query the DB. The event classes
        and 10 decade slices are fixed by the campaign spec. An empty
        resonance-target set for a given substep is handled honestly in
        run_substep (I4: 0 rows, not a plan failure).
        """
        steps: list[SubStep] = []
        for event_class in EVENT_CLASSES:
            for decade in DECADE_SLICES:
                key = f"{event_class}::{decade.era_slice_key}"
                label = (
                    f"W3.4 century: {event_class} "
                    f"{decade.year_start}–{decade.year_end}"
                )
                steps.append(SubStep(key=key, label=label))
        return steps

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: run_substep
    # ------------------------------------------------------------------

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        """Materialize one (event_class, decade_slice) pair.

        Steps:
          1. Parse substep_key → (event_class, era_slice_key, decade).
          2. Fetch resonance targets for this chart×class.
          3. If no targets: honest 0-row result (I4).
          4. Compute delta fingerprint.
          5. Check stored fingerprint — if unchanged and rows exist: skip.
          6. call find_threshold_crossings over the decade JD range.
          7. DELETE-then-INSERT into kala_gochara_windows_v2.
          8. Upsert fingerprint to kala_gochara_v2_build_state.
          9. Log wall-clock time at DEBUG.
        """
        t0 = time.time()
        chart_id = ctx.config["chart_id"]
        substep_key = step.key
        conn = ctx.db_conn
        query = _query_fn(conn)

        # 1. Parse substep_key.
        parts = substep_key.split("::", 1)
        if len(parts) != 2:
            logger.error(
                "[%s] malformed substep_key=%r — expected 'event_class::era_slice_key'",
                ASSET_ID, substep_key,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"malformed substep_key={substep_key!r}",
            )
        event_class, era_slice_key = parts

        # Find the matching DecadeSlice.
        decade = next(
            (d for d in DECADE_SLICES if d.era_slice_key == era_slice_key), None
        )
        if decade is None:
            logger.error(
                "[%s] unknown era_slice_key=%r in substep_key=%r",
                ASSET_ID, era_slice_key, substep_key,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"unknown era_slice_key={era_slice_key!r}",
            )

        # 2. Fetch resonance targets.
        target_refs = _fetch_resonance_targets(conn, chart_id, event_class)

        # 3. I4: empty resonance targets → honest 0 rows.
        if not target_refs:
            elapsed = time.time() - t0
            logger.debug(
                "[%s] substep=%r chart=%s: no resonance targets — honest 0 rows (I4). "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: honest empty — no resonance targets for "
                    f"chart={chart_id} event_class={event_class} (I4)"
                ),
            )

        # 4. Compute delta fingerprint.
        fingerprint = compute_substep_fingerprint(
            event_class, era_slice_key, ENGINE_VERSION, target_refs,
        )

        # 5. Delta skip: if fingerprint unchanged AND rows exist → no-op.
        stored_fp = _stored_fingerprint(query, chart_id, substep_key)
        rows_exist = _stored_rows_exist(query, chart_id, substep_key, era_slice_key)
        if stored_fp is not None and stored_fp == fingerprint and rows_exist and not ctx.dry_run:
            elapsed = time.time() - t0
            logger.debug(
                "[%s] substep=%r chart=%s: fingerprint unchanged (%s) — skip. "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, fingerprint, elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: skipping — fingerprint unchanged ({fingerprint}), "
                    f"rows already present"
                ),
            )

        # 6. Find threshold crossings over the decade JD range.
        #    We need a ThresholdConfig to gate window emission.  For the
        #    century build we use a structural-prior threshold: the v3 engine
        #    is bounded in [0,1], so we gate at 0.0 (emit all active intervals)
        #    as the honest structural prior before per-class calibration.
        #    This is a deliberate design choice for W3.4 — the full
        #    self-normalizing threshold (W1.4) is applied at serve time.
        #
        #    §N.8: fallback_used must be derived from a real DB lookup, not
        #    bound to a literal — the lookup result (True iff the class has no
        #    base_rate row in brahma_event_ontology) is the earned signal.
        #    base_rate_cited and age_band_used are also populated from the
        #    lookup; lambda_thresh stays 0.0 per the structural-prior design.
        try:
            _base_rate_cited, _age_band_used, _fallback_used = fetch_base_rate_for_class(
                conn, event_class,
            )
        except Exception:  # noqa: BLE001
            _base_rate_cited, _age_band_used, _fallback_used = 0.0, "band_41_60", True

        threshold_config = ThresholdConfig(
            percentile_used=0.0,
            lambda_thresh=0.0,
            implied_density=0.0,
            base_rate_cited=_base_rate_cited,
            age_band_used=_age_band_used,
            density_flag="no_base_rate" if _fallback_used else "ok",
            fallback_used=_fallback_used,
            sample_count=0,
        )

        # PARIṢKĀRA MR-12: shape-aware dispatch. BRIEF_D5 §3 (BINDING) requires
        # a served row's shape to mirror brahma_event_ontology.temporal_shape.
        # is_chain gates the milestone-scoring path below; a chain-shaped
        # class with no usable milestone_template degrades to an honest
        # skip (I4), never a fabricated row.
        _shape, _raw_milestone_template, _irreversibility_milestone = _fetch_class_shape(
            conn, event_class,
        )
        is_chain = _shape == "chain"
        chain_milestone_template: list[dict] = []
        if is_chain and _raw_milestone_template:
            chain_milestone_template = _normalize_milestone_template(
                _raw_milestone_template, _irreversibility_milestone,
            )

        if is_chain and not chain_milestone_template:
            # I4 honest gap: the ontology declares this class chain-shaped but
            # carries no usable milestone_template (or the live read failed
            # and no documented fallback template exists for this class).
            # Mirrors the "no resonance targets" early-return above: return
            # BEFORE any DELETE/INSERT is issued, no fingerprint upsert —
            # never a fabricated row (I4).
            elapsed = time.time() - t0
            note = (
                f"{substep_key}: skipped — event_class={event_class} is "
                f"chain-shaped (brahma_event_ontology.temporal_shape='chain') "
                f"but milestone_template is empty/unavailable — honest gap "
                f"(I4), no rows fabricated"
            )
            logger.warning("[%s] %s", ASSET_ID, note)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=note,
            )

        # Import swisseph lazily (matches pattern in existing writers).
        try:
            import swisseph as swe  # type: ignore[import]
        except Exception as exc:
            elapsed = time.time() - t0
            logger.error("[%s] swisseph unavailable: %s", ASSET_ID, exc)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=f"swisseph unavailable: {exc}",
            )

        # Build a ClassContext: the one-shot DB fetch that makes batched
        # lambda_v3 evaluation possible (zero per-JD DB access after fetch).
        # ClassContext is imported at module level so tests can monkeypatch it.
        try:
            context = ClassContext.fetch(
                conn=conn,
                chart_id=chart_id,
                event_class=event_class,
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - t0
            logger.warning(
                "[%s] substep=%r chart=%s: ClassContext.fetch failed: %s — 0 rows.",
                ASSET_ID, substep_key, chart_id, exc,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: ClassContext unavailable ({exc}) — honest 0 rows"
                ),
            )

        # PARIṢKĀRA MR-15: AV (Ashtakavarga) gating is a flagship gochara_v3
        # mechanism. A degraded av_gate_rows fetch inside ClassContext.fetch
        # used to be indistinguishable from "this chart genuinely has no AV
        # data" — swallowed at INFO with zero build-report visibility (the
        # exact defect the only production build to date silently shipped
        # with). getattr(..., None) is deliberate: existing tests stub
        # ClassContext.fetch to return a bare object() with no attributes at
        # all, and that must keep degrading gracefully, not raise.
        av_gate_fetch_error = getattr(context, "av_gate_fetch_error", None)
        av_gate_note = ""
        if av_gate_fetch_error:
            logger.error(
                "[%s] substep=%r chart=%s: AV (Ashtakavarga) gating degraded "
                "this substep — %s",
                ASSET_ID, substep_key, chart_id, av_gate_fetch_error,
            )
            av_gate_note = f"AV_GATE_DEGRADED: {av_gate_fetch_error}; "

        intervals: list[IntervalBoundary] = find_threshold_crossings(
            swe=swe,
            context=context,
            start_jd=decade.start_jd,
            end_jd=decade.end_jd,
            threshold_config=threshold_config,
            coarse_step_days=7.0,
        )

        if ctx.dry_run:
            elapsed = time.time() - t0
            if is_chain:
                would_produce = len(intervals) * len(chain_milestone_template)
                logger.debug(
                    "[%s] DRY RUN substep=%r chart=%s: %d chain episodes x %d "
                    "milestones = %d rows would be served. wall_clock_s=%.3f",
                    ASSET_ID, substep_key, chart_id, len(intervals),
                    len(chain_milestone_template), would_produce, elapsed,
                )
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    rows_skipped=would_produce,
                    duration_seconds=elapsed,
                    notes=(
                        f"{av_gate_note}DRY RUN {substep_key}: chain-shaped, "
                        f"{len(intervals)} episodes x {len(chain_milestone_template)} "
                        f"milestones = {would_produce} rows would be served "
                        f"in {decade.year_start}–{decade.year_end} — nothing written"
                    ),
                )
            logger.debug(
                "[%s] DRY RUN substep=%r chart=%s: %d intervals would be served. "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, len(intervals), elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                rows_skipped=len(intervals),
                duration_seconds=elapsed,
                notes=(
                    f"{av_gate_note}DRY RUN {substep_key}: {len(intervals)} intervals found "
                    f"in {decade.year_start}–{decade.year_end} — nothing written"
                ),
            )

        # 7. DELETE-then-INSERT (§N.3 replace-not-accrete).
        #    Scoped to (chart_id, event_class, generation, era_slice_key) so
        #    a resubmit of this decade slice does not touch other slices.
        #
        #    W5.4 repoint (UTK-R1): write to BOTH tables.
        #      (a) kala_gochara_windows_v2 — calibration/staging (generation='g3_utkarsha')
        #      (b) kala_gochara_windows    — production           (generation='3.0')
        #    Every DML on kala_gochara_windows MUST carry generation='3.0'.
        #    The I1 rail (DB trigger) allows generation='3.0'; it only blocks 'v1'.

        # (a) Calibration/staging table: kala_gochara_windows_v2
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} "
                f"WHERE chart_id = %s AND event_class = %s "
                f"AND generation = %s AND era_slice_key = %s",
                [chart_id, event_class, GENERATION_V3, era_slice_key],
            )

        # (b) Production table: kala_gochara_windows with generation='3.0'
        #     I1 mutation-guard invariant: this DELETE carries generation='3.0'.
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {PROD_TABLE} "
                f"WHERE chart_id = %s AND event_class = %s "
                f"AND generation = '3.0' AND era_slice_key = %s",
                [chart_id, event_class, era_slice_key],
            )

        # Honest per-event_class valence (PARIṢKĀRA MR-13, F#1 fix): computed
        # ONCE per substep (all boundaries in this substep share the same
        # event_class) and passed to every _build_row call below -- never a
        # hardcoded "favourable" literal.
        class_valence, class_is_adverse = _fetch_class_valence(conn, event_class)

        inserted = 0
        if is_chain:
            # PARIṢKĀRA MR-12: chain production. Each detected episode
            # (IntervalBoundary from find_threshold_crossings, reused here as
            # the episode ANCHOR, not the final row) is expanded into one row
            # per milestone_template entry via score_chain_milestones — the
            # W3.2 machinery that has existed, tested in isolation, since
            # before this fix but was never wired to a real caller.
            for boundary in intervals:
                milestone_scores = score_chain_milestones(
                    swe, context, boundary.enter_jd, chain_milestone_template,
                    threshold_config,
                )
                for ms in milestone_scores:
                    # (a) Insert into calibration/staging table.
                    row_v2 = _build_chain_row(
                        chart_id, event_class, ms, era_slice_key,
                        valence=class_valence, is_adverse=class_is_adverse,
                        generation=GENERATION_V3,
                    )
                    try:
                        conn.execute(INSERT_SQL, row_v2)
                        inserted += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "[%s] substep=%r v2 chain row insert failed "
                            "(milestone_id=%s, peak_date=%s): %s",
                            ASSET_ID, substep_key, ms.milestone_id,
                            _jd_to_date(ms.milestone_jd), exc,
                        )

                    # (b) Insert into production table (generation='3.0').
                    #     I1 mutation-guard invariant: row carries generation='3.0'.
                    row_prod = _build_chain_row(
                        chart_id, event_class, ms, era_slice_key,
                        valence=class_valence, is_adverse=class_is_adverse,
                        generation=GENERATION_PROD,
                    )
                    try:
                        conn.execute(INSERT_PROD_SQL, row_prod)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "[%s] substep=%r prod chain row insert failed "
                            "(milestone_id=%s, peak_date=%s): %s",
                            ASSET_ID, substep_key, ms.milestone_id,
                            _jd_to_date(ms.milestone_jd), exc,
                        )
        else:
            for boundary in intervals:
                # (a) Insert into calibration/staging table.
                row_v2 = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_V3,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                )
                try:
                    conn.execute(INSERT_SQL, row_v2)
                    inserted += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "[%s] substep=%r v2 row insert failed (peak_date=%s): %s",
                        ASSET_ID, substep_key,
                        _jd_to_date(boundary.peak_jd), exc,
                    )

                # (b) Insert into production table (generation='3.0').
                #     I1 mutation-guard invariant: row carries generation='3.0'.
                row_prod = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_PROD,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                )
                try:
                    conn.execute(INSERT_PROD_SQL, row_prod)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "[%s] substep=%r prod row insert failed (peak_date=%s): %s",
                        ASSET_ID, substep_key,
                        _jd_to_date(boundary.peak_jd), exc,
                    )

        # 8. Upsert fingerprint.
        _upsert_build_state(
            conn=conn,
            chart_id=chart_id,
            substep_key=substep_key,
            fingerprint=fingerprint,
            rows_written=inserted,
            skipped=False,
            build_id=ctx.build_id,
        )

        # 9. Log wall-clock time at DEBUG (AC5 — first SLO evidence point).
        elapsed = time.time() - t0
        logger.debug(
            "[%s] substep=%r chart=%s: %d intervals inserted. wall_clock_s=%.3f",
            ASSET_ID, substep_key, chart_id, inserted, elapsed,
        )

        if is_chain:
            notes = (
                f"{av_gate_note}{substep_key}: {len(intervals)} chain episodes found "
                f"({len(chain_milestone_template)} milestones/episode, temporal_shape=chain), "
                f"{inserted} rows inserted into {TABLE} (generation={GENERATION_V3}) "
                f"and {PROD_TABLE} (generation={GENERATION_PROD}), "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}"
            )
        else:
            notes = (
                f"{av_gate_note}{substep_key}: {len(intervals)} intervals found, "
                f"{inserted} rows inserted into {TABLE} (generation={GENERATION_V3}) "
                f"and {PROD_TABLE} (generation={GENERATION_PROD}), "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}"
            )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=elapsed,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # CLI / direct-use fallback (drives own substeps; no orchestrator heartbeat)
    # ------------------------------------------------------------------

    def run(self, ctx: ContextSpec) -> WriterResult:
        """CLI path: drive all substeps (len(EVENT_CLASSES) x 10) sequentially."""
        t0 = time.time()
        total_inserted = 0
        notes: list[str] = []
        for step in self.plan_substeps(ctx):
            result = self.run_substep(ctx, step)
            total_inserted += result.rows_inserted
            if result.notes:
                notes.append(result.notes)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=" | ".join(notes),
        )


__all__ = [
    "ASSET_ID",
    "DECADE_SLICES",
    "ENGINE_VERSION",
    "EVENT_CLASSES",
    "GENERATION_V3",
    "GENERATION_PROD",
    "PROD_TABLE",
    "TABLE",
    "GocharaV3CenturyMaterializeWriter",
    "build_decade_slices",
    "compute_substep_fingerprint",
    "_fetch_class_valence",
    "_fetch_class_shape",
    "_normalize_milestone_template",
    "_build_chain_row",
]
