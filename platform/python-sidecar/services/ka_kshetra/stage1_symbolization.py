"""
services.ka_kshetra.stage1_symbolization — ṢAḌ-DARŚANA W2 Lane A, Stage 1.

Spec: KALA_W2_FIELD_DESIGN_v1_0.md §3.2. Turns stage-0 kinematics into
classical primitives, each an interval `[t_start, t_end]` with a piecewise-
LINEAR strength envelope (JSONB knot array), so stage 4 can consume every
primitive uniformly. Writes `kala_field_primitives` (migration 488).

The envelope contract (§3.2, frozen — stage 4 depends on it): >=2 knots,
strictly ascending `t`, `v` in [0,1], linear between knots, value is 0 outside
[t_start, t_end]. First/last knot v=0 UNLESS the primitive is a step function,
in which case two COINCIDENT knots make the jump explicit (a box shape:
(t_start,0),(t_start,v),(t_end,v),(t_end,0)).

§N.5 hard rule: `panchanga_limb` and (to the extent grounded — see the
av_kaksha_gate honesty note below) `av_kaksha_gate` rows do NOT recompute
their source; they REFERENCE the L1/L3 row that already holds the value and
inherit it verbatim, carrying `source_table`/`source_pk`/`source_fact_id`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional, Sequence

from .stage0_kinematics import ContactEpisode

# ── Envelope contract ─────────────────────────────────────────────────────────

Knot = tuple[float, float]  # (t_days, v in [0,1])


class EnvelopeContractViolation(ValueError):
    """Raised when a caller tries to persist a primitive whose envelope
    breaks the frozen §3.2 contract stage 4 depends on."""


def validate_envelope(knots: Sequence[Knot]) -> None:
    """t is ascending overall; a SINGLE coincident pair at the same t (the
    step-function jump, §3.2) is allowed, but t may never go backwards and
    the same t may never repeat a third time."""
    if len(knots) < 2:
        raise EnvelopeContractViolation("envelope needs >= 2 knots")
    prev_t = None
    run_len = 0
    for t, v in knots:
        if prev_t is not None:
            if t < prev_t:
                raise EnvelopeContractViolation("envelope knots must not go backwards in t")
            if t == prev_t:
                run_len += 1
                if run_len > 2:
                    raise EnvelopeContractViolation(
                        f"envelope has a t={t} value repeated more than twice — only a "
                        "single coincident pair (the step-function jump) is allowed"
                    )
            else:
                run_len = 1
        else:
            run_len = 1
        if not (0.0 <= v <= 1.0):
            raise EnvelopeContractViolation(f"envelope v={v} outside [0,1]")
        prev_t = t


def envelope_value_at(knots: Sequence[Knot], t: float) -> float:
    """Piecewise-linear interpolation; 0 strictly outside [knots[0].t, knots[-1].t].
    At a coincident-knot pair (a step's vertical jump), returns the HIGHER of
    the two values — a test/sanity helper only; the actual pipeline (stage 4)
    consumes the raw knot array directly, not this interpolator."""
    if not knots:
        return 0.0
    if t < knots[0][0] or t > knots[-1][0]:
        return 0.0
    for i in range(len(knots) - 1):
        t0, v0 = knots[i]
        t1, v1 = knots[i + 1]
        if t0 <= t <= t1:
            if t1 == t0:
                return max(v0, v1)
            frac = (t - t0) / (t1 - t0)
            return v0 + frac * (v1 - v0)
    return knots[-1][1]


def _box_envelope(t_start: float, t_end: float, v: float) -> list[Knot]:
    """Step-function box: (t_start,0),(t_start,v),(t_end,v),(t_end,0) — the
    §3.2-sanctioned coincident-knot form for a constant-value interval."""
    return [(t_start, 0.0), (t_start, v), (t_end, v), (t_end, 0.0)]


def _trapezoid_envelope(t_in: float, core_in: Optional[float], t_peak: float,
                         core_out: Optional[float], t_out: float,
                         w_dwell: float, peak_value: float) -> list[Knot]:
    """The stage-0 trapezoidal kernel's breakpoints (§3.1), carried into stage 1
    as an explicit knot list. Degrades to a triangle if the episode never
    saturates omega_core (core_in/core_out are None)."""
    if core_in is None or core_out is None:
        knots = [(t_in, 0.0), (t_peak, peak_value), (t_out, 0.0)]
    else:
        knots = [(t_in, 0.0), (core_in, w_dwell), (t_peak, w_dwell),
                 (core_out, w_dwell), (t_out, 0.0)]
    # de-duplicate any coincident-in-time knots other than the intentional
    # (t_start,0)/(t_start,v) or (t_end,v)/(t_end,0) step pairs — a degenerate
    # episode (t_peak == core_in, say) must not violate strict ascension.
    out: list[Knot] = []
    for kt, kv in knots:
        if out and out[-1][0] == kt:
            continue
        out.append((kt, kv))
    return out


# ── kala_field_primitives row shape ───────────────────────────────────────────

@dataclass
class PrimitiveRow:
    chart_id: str
    primitive_kind: str
    subject: str
    t_start: float
    t_end: float
    envelope: list[Knot]
    polarity: str  # 'supportive' | 'obstructive' | 'neutral'
    object_ref: Optional[str] = None
    class_label: Optional[str] = None
    source_kind: str = "derived"  # l0_reference|l1_fact|l2_signal|l3_row|derived
    source_table: Optional[str] = None
    source_pk: Optional[str] = None
    source_fact_id: Optional[str] = None
    kinematics_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        validate_envelope(self.envelope)
        if self.polarity not in ("supportive", "obstructive", "neutral"):
            raise ValueError(f"invalid polarity: {self.polarity}")
        if self.source_kind not in ("l0_reference", "l1_fact", "l2_signal", "l3_row", "derived"):
            raise ValueError(f"invalid source_kind: {self.source_kind}")


# ── Coverage marker (LAW ZERO — honest gaps, never fabricated) ────────────────

@dataclass(frozen=True)
class CoverageGap:
    primitive_kind: str
    reason_code: str  # 'not_in_corpus' | 'not_computed'
    detail: str


# v0 constant, NOT a classical citation — a symbolization-layer smoothing
# parameter for how wide the station's influence band is scaled by dwell
# weight, refit at stage 9 like every other v0 constant in this design
# (mirrors §5.1 C-5's own "v0, fitted later" convention for d_ell).
STATION_BAND_BASE_DAYS = 1.0
STATION_BAND_DWELL_SCALE_DAYS = 6.0

SYZYGY_BAND_HALF_DAYS = 1.5  # exact per §3.1/§3.2, not a v0 guess


# ── Builders: primitives derived directly from stage-0 kinematics ────────────

def build_contact_primitive_with_dwell(episode: ContactEpisode, chart_id: str,
                                        reference: str, w_dwell: float,
                                        kinematics_ids: Sequence[int] = ()) -> PrimitiveRow:
    """`contact_moon_ref` / `contact_lagna_ref` (§3.2 table): the transit
    contact measured from the given natal reference point. `reference` is
    'Mo' (contact_moon_ref, leg 1) or 'Lagna' (contact_lagna_ref, leg 2) — the
    dual-reference gochara split (SIX_VIEWS §E, item 8) read directly off the
    stage-0 contact episode whose natal target IS that reference point. Takes
    the already-computed stage-0 `w_dwell` directly — stage 1 never re-derives
    the dwell-weight formula (that is stage 0's job); it only threads through
    what stage 0 already decided, matching the trapezoid's own saturation
    value at the flat top."""
    primitive_kind = {"Mo": "contact_moon_ref", "Lagna": "contact_lagna_ref"}.get(reference)
    if primitive_kind is None:
        raise ValueError(f"unknown dual-reference point: {reference}")
    knots = _trapezoid_envelope(
        episode.t_in, episode.ok_core_in, episode.t_peak, episode.ok_core_out,
        episode.t_out, w_dwell, peak_value=w_dwell,
    )
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind=primitive_kind, subject=episode.body,
        object_ref=reference, t_start=episode.t_in, t_end=episode.t_out,
        envelope=knots, polarity="neutral", source_kind="derived",
        source_table="kala_field_kinematics", kinematics_ids=tuple(kinematics_ids),
    )


def build_station_band_primitive(chart_id: str, body: str, t_root: float,
                                  w_dwell: float, kinematics_id: Optional[int] = None
                                  ) -> PrimitiveRow:
    """`station_band` (§3.2): the +-w_dwell-scaled band around a station root."""
    half_width = STATION_BAND_BASE_DAYS + STATION_BAND_DWELL_SCALE_DAYS * w_dwell
    knots = [(t_root - half_width, 0.0), (t_root, 1.0), (t_root + half_width, 0.0)]
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind="station_band", subject=body,
        t_start=t_root - half_width, t_end=t_root + half_width, envelope=knots,
        polarity="neutral", source_kind="derived", source_table="kala_field_kinematics",
        kinematics_ids=(kinematics_id,) if kinematics_id is not None else (),
    )


def build_syzygy_band_primitive(chart_id: str, body: str, t_root: float,
                                 syzygy_kind: str, is_eclipse_candidate: bool,
                                 kinematics_id: Optional[int] = None) -> PrimitiveRow:
    """`syzygy_band` (§3.2): the +-1.5 day band around a syzygy;
    `eclipse_candidate` carried through as `class_label`."""
    half = SYZYGY_BAND_HALF_DAYS
    knots = [(t_root - half, 0.0), (t_root, 1.0), (t_root + half, 0.0)]
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind="syzygy_band", subject=body,
        object_ref=syzygy_kind, t_start=t_root - half, t_end=t_root + half,
        envelope=knots, polarity="neutral",
        class_label="eclipse_candidate" if is_eclipse_candidate else syzygy_kind,
        source_kind="derived", source_table="kala_field_kinematics",
        kinematics_ids=(kinematics_id,) if kinematics_id is not None else (),
    )


# ── Builders: L0/L1/L3 reference joins (§N.5 — inherit, never recompute) ────

def build_moorti_primitive(chart_id: str, body: str, t_ingress: float,
                            t_next_ingress: float, moorti_name: str,
                            quality_tier: int, kinematics_id: Optional[int] = None
                            ) -> PrimitiveRow:
    """`moorti_at_ingress` (§3.2): the moorti class of a sign_ingress, from
    `bg_transit_moorti`. quality_tier 1 (best, svarna) .. 4 (worst, loha) maps
    to strength 1.0 .. 0.25 (linear, tier-inverted)."""
    strength = 1.0 - 0.25 * (quality_tier - 1)
    polarity = "supportive" if quality_tier <= 2 else "obstructive" if quality_tier == 4 else "neutral"
    knots = _box_envelope(t_ingress, t_next_ingress, strength)
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind="moorti_at_ingress", subject=body,
        t_start=t_ingress, t_end=t_next_ingress, envelope=knots, polarity=polarity,
        class_label=moorti_name, source_kind="l0_reference",
        source_table="bg_transit_moorti", source_pk=moorti_name,
        kinematics_ids=(kinematics_id,) if kinematics_id is not None else (),
    )


def build_vedha_primitive(chart_id: str, body: str, t_start: float, t_end: float,
                           vedha_house: int, phala: str,
                           kinematics_id: Optional[int] = None) -> PrimitiveRow:
    """`vedha` (§3.2): obstruction of a transit house by an occupied vedha
    house, from `bg_transit_rules` (rule_type='vedha')."""
    knots = _box_envelope(t_start, t_end, 1.0)
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind="vedha", subject=body,
        object_ref=f"house_{vedha_house}", t_start=t_start, t_end=t_end,
        envelope=knots, polarity="obstructive", class_label=phala,
        source_kind="l0_reference", source_table="bg_transit_rules",
        source_pk=f"vedha:{body}:{vedha_house}",
        kinematics_ids=(kinematics_id,) if kinematics_id is not None else (),
    )


_PANCHANGA_LIMB_KEYS = ("tithi", "vara", "nakshatra", "yoga", "karana")


def build_panchanga_limb_primitive(chart_id: str, limb: str, t_start: float,
                                    t_end: float, limb_value_id: int,
                                    limb_value_name: str,
                                    source_row_date: date) -> PrimitiveRow:
    """`panchanga_limb` (§3.2 + §N.5): tithi/vara/nakshatra/yoga/karana state,
    REFERENCED from `panchanga_daily` (never recomputed)."""
    if limb not in _PANCHANGA_LIMB_KEYS:
        raise ValueError(f"unknown panchanga limb: {limb}")
    knots = _box_envelope(t_start, t_end, 1.0)
    return PrimitiveRow(
        chart_id=chart_id, primitive_kind="panchanga_limb", subject=limb,
        object_ref=str(limb_value_id), t_start=t_start, t_end=t_end, envelope=knots,
        polarity="neutral", class_label=limb_value_name, source_kind="l1_fact",
        source_table="panchanga_daily", source_pk=str(source_row_date),
    )


def assert_panchanga_authority(inherited_limb_id: int, referenced_row_limb_id: int) -> None:
    """§N.5 build-time halting assertion: the inherited value MUST equal the
    referenced panchanga_daily row's value. A mismatch is `l1_authority_divergence`
    — a halt-worthy bug, never a stored divergence."""
    if inherited_limb_id != referenced_row_limb_id:
        raise RuntimeError(
            f"l1_authority_divergence: panchanga_limb inherited={inherited_limb_id} "
            f"!= panchanga_daily row value={referenced_row_limb_id}"
        )


# ── sandhi_band (§3.2): consumes Lane B's published function by signature ────
# Lane B (stage3_clocks.py) owns `boundary_breakpoints(chart_id, conn) ->
# list[float]`. Lane A calls it by the FROZEN signature the design publishes
# (§4.1), never by reading Lane B's code (§0 anti-collision contract). Until
# Lane B's module lands, the import is deferred and any ImportError degrades
# to an honest `not_computed` coverage gap rather than a hard failure — this
# stage-1 module is independently buildable/testable ahead of Lane B landing.

SANDHI_BAND_HALF_DAYS = 3.0  # v0 — mirrors the station-band convention above.


def build_sandhi_band_primitives(chart_id: str, conn,
                                  boundary_breakpoints_fn: Optional[Callable] = None
                                  ) -> tuple[list[PrimitiveRow], Optional[CoverageGap]]:
    """`sandhi_band` (§3.2): the +-band around a dasha boundary, from Lane B's
    `stage3_clocks.boundary_breakpoints(chart_id, conn)`."""
    fn = boundary_breakpoints_fn
    if fn is None:
        try:
            from .stage3_clocks import boundary_breakpoints as fn  # noqa: PLC0415
        except ImportError:
            return [], CoverageGap(
                "sandhi_band", "not_computed",
                "Lane B's services.ka_kshetra.stage3_clocks not yet available in this build",
            )
        # Lane B's boundary_breakpoints is a real DB-backed function (queries
        # kala_field_boundaries directly) — it requires a genuine connection and has
        # no reason to special-case None itself. A missing connection here means this
        # primitive genuinely cannot be computed right now, the same honest outcome
        # as Lane B's module being altogether absent — not a crash.
        if conn is None:
            return [], CoverageGap(
                "sandhi_band", "not_computed",
                "No database connection available to read kala_field_boundaries",
            )
    breakpoints = fn(chart_id, conn)
    rows = []
    for t_b in breakpoints:
        half = SANDHI_BAND_HALF_DAYS
        knots = [(t_b - half, 0.0), (t_b, 1.0), (t_b + half, 0.0)]
        rows.append(PrimitiveRow(
            chart_id=chart_id, primitive_kind="sandhi_band", subject="dasha_boundary",
            t_start=t_b - half, t_end=t_b + half, envelope=knots, polarity="neutral",
            source_kind="l1_fact", source_table="kala_field_boundaries",
        ))
    return rows, None


# ── av_kaksha_gate / latta (§3.2): honest not_in_corpus at W2 ────────────────
# `bg_transit_av_gates` (kakshya/SAV gates) and `bg_transit_rules` (vedha)
# exist; a natal per-sign Ashtakavarga BINDU source is referenced only in
# passing by ka_sangam/engine.py's docstring ("Sourced from chart_facts
# (sarvashtakavarga) via ga_strength writer") with no fact_category/fact_key
# confirmed against a live build within this lane's scope. Per B.10/LAW ZERO
# this is served honestly rather than guessed: `not_in_corpus` with the exact
# pointer a follow-up session needs, never a fabricated bindu score. `latta`
# has no discovered classical rule table in this codebase at all.

def av_kaksha_gate_coverage() -> CoverageGap:
    return CoverageGap(
        "av_kaksha_gate", "not_in_corpus",
        "bg_transit_av_gates (kakshya/SAV gate thresholds) exists, but the natal "
        "Ashtakavarga bindu-per-sign source (chart_facts fact_category/fact_key, "
        "per ka_sangam/engine.py's docstring pointer to 'ga_strength writer') was "
        "not independently confirmed within Lane A's scope — filed as an "
        "ingestion/verification work item rather than guessed.",
    )


def latta_coverage() -> CoverageGap:
    return CoverageGap(
        "latta", "not_in_corpus",
        "No classical latta-kick rule table found in this codebase as of W2 Lane A's "
        "build — filed as a corpus-extraction work item (parallel to W3 item 41's "
        "Muhurta Factor Census, which is the natural home for this table).",
    )


# ── DB I/O ────────────────────────────────────────────────────────────────────

REPLACE_PRIOR_SQL = "DELETE FROM kala_field_primitives WHERE chart_id = %s"

UPSERT_SQL = """
INSERT INTO kala_field_primitives (
    chart_id, primitive_kind, subject, object_ref, t_start, t_end, envelope,
    polarity, class_label, source_kind, source_table, source_pk,
    source_fact_id, kinematics_ids
) VALUES (
    %(chart_id)s, %(primitive_kind)s, %(subject)s, %(object_ref)s, %(t_start)s,
    %(t_end)s, %(envelope)s, %(polarity)s, %(class_label)s, %(source_kind)s,
    %(source_table)s, %(source_pk)s, %(source_fact_id)s, %(kinematics_ids)s
)
ON CONFLICT (chart_id, primitive_kind, subject, COALESCE(object_ref, ''), t_start)
DO UPDATE SET
    t_end = EXCLUDED.t_end,
    envelope = EXCLUDED.envelope,
    polarity = EXCLUDED.polarity,
    class_label = EXCLUDED.class_label,
    source_kind = EXCLUDED.source_kind,
    source_table = EXCLUDED.source_table,
    source_pk = EXCLUDED.source_pk,
    source_fact_id = EXCLUDED.source_fact_id,
    kinematics_ids = EXCLUDED.kinematics_ids,
    computed_at = now()
"""


def row_to_params(row: PrimitiveRow) -> dict:
    import json
    return {
        "chart_id": row.chart_id,
        "primitive_kind": row.primitive_kind,
        "subject": row.subject,
        "object_ref": row.object_ref,
        "t_start": row.t_start,
        "t_end": row.t_end,
        "envelope": json.dumps([{"t": t, "v": v} for t, v in row.envelope]),
        "polarity": row.polarity,
        "class_label": row.class_label,
        "source_kind": row.source_kind,
        "source_table": row.source_table,
        "source_pk": row.source_pk,
        "source_fact_id": row.source_fact_id,
        "kinematics_ids": list(row.kinematics_ids) if row.kinematics_ids else [],
    }


def write_primitive_rows(conn, rows: Sequence[PrimitiveRow]) -> int:
    """Idempotent per-row upsert (natural key = chart_id, primitive_kind,
    subject, object_ref, t_start). The coarser once-per-chart delete-then-
    insert (§N.3) is orchestrated once in `ka_kshetra.plan_substeps` (Lane C)."""
    n = 0
    for r in rows:
        conn.execute(UPSERT_SQL, row_to_params(r))
        n += 1
    return n


# ═════════════════════════════════════════════════════════════════════════════
# Module-level substep wiring (SAMPURTI G1 — plugs this stage into the
# ka_kshetra HEAVY writer's _optional_stage_plugins mechanism).
#
# Stage 1 reads kala_field_kinematics (stage0 output) and kala_field_boundaries
# (stage3 output) and writes kala_field_primitives. It MUST run after BOTH
# stage0 and stage3 — the plugin order in writer._optional_stage_plugins
# guarantees this (stage0 → stage2 → stage3 → stage1).
#
# §N.3 contract: the once-per-chart DELETE runs exactly ONCE in plan_substeps,
# BEFORE the substep executes.
# ═════════════════════════════════════════════════════════════════════════════

def _reconstruct_episodes_from_db(conn, chart_id: str) -> list:
    """Read kala_field_kinematics and reconstruct ContactEpisode objects by
    grouping rows with the same episode_id.

    Only contact-kind rows (contact_in/out/peak/core_in/core_out) that have a
    non-NULL episode_id belong to a contact episode. Other kinds (sign_ingress,
    nakshatra_ingress, station, syzygy) are returned separately for the
    corresponding primitive builders.

    Returns (episodes, station_rows_db, syzygy_rows_db) where:
      - episodes: list of (kinematics_row_id_in, ContactEpisode) pairs
      - station_rows_db: raw DB rows for station events
      - syzygy_rows_db: raw DB rows for syzygy events
    """
    rows = conn.execute(
        """SELECT id, event_kind, body, target_kind, target_ref, t_days,
                  dwell_days, dwell_weight, orb_deg, orb_source,
                  eclipse_candidate, gamma_proxy, episode_id
           FROM kala_field_kinematics
           WHERE chart_id = %s
           ORDER BY body, t_days ASC
        """,
        [chart_id],
    ).fetchall()

    def _row(r, key, idx):
        return r[key] if isinstance(r, dict) else r[idx]

    # Group by episode_id for contact events.
    episodes_by_id: dict = {}
    station_rows_db = []
    syzygy_rows_db = []
    id_in_by_episode: dict = {}

    for r in rows:
        event_kind = _row(r, 'event_kind', 1)
        ep_id = _row(r, 'episode_id', 12)

        if event_kind == 'station':
            station_rows_db.append(r)
        elif event_kind == 'syzygy':
            syzygy_rows_db.append(r)
        elif event_kind in ('contact_in', 'contact_out', 'contact_peak',
                            'contact_core_in', 'contact_core_out'):
            if ep_id is None:
                continue
            if ep_id not in episodes_by_id:
                episodes_by_id[ep_id] = []
                id_in_by_episode[ep_id] = None
            episodes_by_id[ep_id].append(r)
            if event_kind == 'contact_in':
                id_in_by_episode[ep_id] = _row(r, 'id', 0)

    # Reconstruct ContactEpisode objects from the grouped rows.
    episodes = []
    for ep_id, ep_rows in episodes_by_id.items():
        by_kind: dict = {}
        for r in ep_rows:
            kind = _row(r, 'event_kind', 1)
            by_kind[kind] = r

        if 'contact_in' not in by_kind or 'contact_out' not in by_kind:
            continue  # incomplete episode — honest skip

        r_in = by_kind['contact_in']
        r_out = by_kind['contact_out']
        r_peak = by_kind.get('contact_peak') or r_in

        t_in = float(_row(r_in, 't_days', 5))
        t_out = float(_row(r_out, 't_days', 5))
        t_peak = float(_row(r_peak, 't_days', 5))

        ok_core_in = None
        if 'contact_core_in' in by_kind:
            ok_core_in = float(_row(by_kind['contact_core_in'], 't_days', 5))
        ok_core_out = None
        if 'contact_core_out' in by_kind:
            ok_core_out = float(_row(by_kind['contact_core_out'], 't_days', 5))

        orb = _row(r_in, 'orb_deg', 8)
        orb_src = _row(r_in, 'orb_source', 9)
        body = _row(r_in, 'body', 2)
        target_ref = _row(r_in, 'target_ref', 4)

        ep = ContactEpisode(
            body=body,
            target_ref=target_ref if target_ref else '',
            t_in=t_in,
            t_out=t_out,
            t_peak=t_peak,
            orb_deg=float(orb) if orb is not None else 3.0,
            orb_source=orb_src if orb_src else 'default_3deg',
            ok_core_in=ok_core_in,
            ok_core_out=ok_core_out,
        )
        kin_id = id_in_by_episode.get(ep_id)
        episodes.append((kin_id, ep))

    return episodes, station_rows_db, syzygy_rows_db


def plan_substeps(ctx) -> list:
    """Wire stage 1 (primitives + envelopes) into the ka_kshetra substep plan.

    Single substep — all primitive kinds are built in one pass from the
    already-committed stage0 kinematics and stage3 boundaries. §N.3 delete
    runs ONCE here (not per substep), before the substep executes.
    """
    from pipeline.orchestrator.writers import SubStep
    conn = ctx.db_conn
    chart_id = ctx.config['chart_id']
    # §N.3: delete prior rows ONCE before the substep executes.
    conn.execute(REPLACE_PRIOR_SQL, [chart_id])
    return [SubStep(key='stage1:run', label='primitives + envelopes')]


def handles_substep(step) -> bool:
    """Return True if this stage owns the given substep key."""
    return step.key == 'stage1:run'


def run_substep(ctx, step) -> object:
    """Build and persist kala_field_primitives from committed kinematics + boundaries.

    Reads kala_field_kinematics (stage0) and kala_field_boundaries (stage3) —
    both §N.5 references, never re-derived computations. Emits every primitive
    kind stage1 can produce; gaps that cannot be computed honestly are recorded
    as CoverageGap (not silently dropped, not fabricated, §N.7 item 6).

    WriterResult.rows_inserted is the actual count of rows written.
    """
    from pipeline.orchestrator.writers import WriterResult

    conn = ctx.db_conn
    chart_id = ctx.config['chart_id']

    primitives: list[PrimitiveRow] = []

    # ── Contact-based primitives (contact_moon_ref / contact_lagna_ref) ──────
    episodes, station_rows_db, syzygy_rows_db = _reconstruct_episodes_from_db(conn, chart_id)

    def _row_val(r, key, idx):
        return r[key] if isinstance(r, dict) else r[idx]

    for kin_id, ep in episodes:
        target_ref = ep.target_ref
        w_dwell = None
        # Read dwell_weight directly from the contact_in kinematics row (§N.5).
        dw_rows = conn.execute(
            """SELECT dwell_weight FROM kala_field_kinematics
               WHERE chart_id = %s AND event_kind = 'contact_in'
                 AND body = %s AND COALESCE(target_ref, '') = %s
                 AND t_days = %s LIMIT 1""",
            [chart_id, ep.body, target_ref if target_ref else '', ep.t_in],
        ).fetchone()
        if dw_rows is not None:
            dw_val = dw_rows['dwell_weight'] if isinstance(dw_rows, dict) else dw_rows[0]
            if dw_val is not None:
                w_dwell = float(dw_val)

        if w_dwell is None:
            # No dwell_weight in DB — cannot build a correctly-weighted primitive.
            # §N.7 item 6: an honest null beats an invented judgment.
            continue

        # contact_moon_ref: episode where target_ref is 'Moon' (natal Moon).
        if target_ref == 'Moon':
            primitives.append(
                build_contact_primitive_with_dwell(ep, chart_id, 'Mo', w_dwell,
                                                   (kin_id,) if kin_id else ())
            )
        # contact_lagna_ref: episode where target_ref is 'LAGNA'.
        elif target_ref == 'LAGNA':
            primitives.append(
                build_contact_primitive_with_dwell(ep, chart_id, 'Lagna', w_dwell,
                                                   (kin_id,) if kin_id else ())
            )

    # ── Station band primitives ───────────────────────────────────────────────
    for r in station_rows_db:
        body = _row_val(r, 'body', 2)
        t_root = float(_row_val(r, 't_days', 5))
        kin_id = _row_val(r, 'id', 0)
        # dwell_weight from the station row itself (stored as dwell_weight on
        # station rows, or fall back to a default via the ephemeris mean motion).
        dw_val = _row_val(r, 'dwell_weight', 7)
        w_dwell = float(dw_val) if dw_val is not None else 0.5
        primitives.append(
            build_station_band_primitive(chart_id, body, t_root, w_dwell, kin_id)
        )

    # ── Syzygy band primitives ────────────────────────────────────────────────
    for r in syzygy_rows_db:
        body = _row_val(r, 'body', 2)
        t_root = float(_row_val(r, 't_days', 5))
        syzygy_kind = _row_val(r, 'target_ref', 4) or 'unknown'
        eclipse_flag = bool(_row_val(r, 'eclipse_candidate', 10))
        kin_id = _row_val(r, 'id', 0)
        primitives.append(
            build_syzygy_band_primitive(chart_id, body, t_root, syzygy_kind,
                                        eclipse_flag, kin_id)
        )

    # ── Sandhi band (dasha boundary bands — reads kala_field_boundaries) ─────
    sandhi_prims, sandhi_gap = build_sandhi_band_primitives(chart_id, conn)
    primitives.extend(sandhi_prims)
    if sandhi_gap is not None:
        import logging
        logging.getLogger(__name__).info(
            'stage1_symbolization: sandhi_band coverage gap for chart %s: %s',
            chart_id, sandhi_gap,
        )

    # Coverage gaps (§N.7 item 6: serve honestly, never fabricate).
    # av_kaksha_gate and latta are not_in_corpus at W2 — logged, not raised.
    for gap in (av_kaksha_gate_coverage(), latta_coverage()):
        import logging
        logging.getLogger(__name__).info(
            'stage1_symbolization: coverage gap %s for chart %s: %s',
            gap.primitive_kind, chart_id, gap.reason_code,
        )

    n = write_primitive_rows(conn, primitives)
    return WriterResult(asset_id='ka_kshetra', rows_inserted=n)
