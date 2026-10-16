"""KA-3a candidate-only orchestrator adapter (pre-build, SR-A4-01).

Normal dispatch is inert until a follow-on gate supplies a typed candidate
payload. Legacy DATE rows and readers are preserved; there is no legacy write
fallback, publication, registry/count switch, commit or connection close.
Historical pure/fetch helpers remain for existing legacy readers and oracles.
Candidate computation is in candidate.py; guarded storage is in storage.py.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.w2g.node_series import NODE_SERIES_PREDICATE, assert_one_row_per_date
from services.ka_graha_sancara.engine import ALL_GRAHAS, NAKSHATRAS, NAK_SIZE_DEG, SIGNS
from services.ka_vedha_gochara.logic import (
    D_PG353_REMOVAL,
    HOUSE_VEDHA,
    LATTA,
    NATURAL_MALEFICS,
    SARVATOBHADRA,
    STATE_ACTIVE,
    STATE_CANCELLED_VIPAREETA,
    build_obstruction_intervals,
    carve_vipareeta,
    corpus_verifiable_for,
    detect_sign_runs,
    exception_for_pair,
    house_from_moon,
    house_vedha_uncited_extension,
    is_mutual_exclusion,
    latta_nakshatra_idx,
    overlap_window,
    sign_from_house,
    source_qualification_for,
    upstream_fingerprint,
)
from services.gochara_grammar.sarvatobhadra import _vedha_pairs_from_db, opposite_nakshatra_id
from services.gochara_grammar import citations as C
from services.gochara_kernel.ids import independence_group as _kernel_independence_group
from services.gochara_kernel.overlays import date_to_jd as _date_to_jd

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_vedha_gochara_v1.1"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

SIGN_SIZE_DEG = 30.0

# Scanned horizon around "now" at build time — matches ka_kota_chakra/
# ka_moorti_nirnaya's own convention exactly (day-grade, not a W2G sub-day
# precision claim).
HORIZON_BACK_DAYS = 60
HORIZON_FORWARD_DAYS = 400

SARVATOBHADRA_CITATION = C.SARVATOBHADRA_VEDHA_PRASNA_MARGA

_FETCH_JANMA_MOON_SQL = """
SELECT fact_id, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'longitude_sidereal'
"""

# Legacy freshness consumers still identify the natal operand explicitly.
L1_OPERANDS = (("graha_position", "MOON", "longitude_sidereal"),)

_FETCH_VEDHA_RULES_SQL = """
SELECT graha, primary_house, vedha_house, phala, classical_citation
FROM bg_transit_rules
WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
"""

_FETCH_EPHEMERIS_RANGE_SQL = f"""
SELECT date, body, tropical_longitude
FROM ephemeris_daily
WHERE ayanamsha_id = 'tropical' AND date BETWEEN %s AND %s AND body = ANY(%s)
  AND {NODE_SERIES_PREDICATE}
ORDER BY body, date
"""

# ADJUDICATION-11 additions ───────────────────────────────────────────────────

_FETCH_GRID_VEDHA_PAIR_SQL = """
SELECT cell_value, school_tag
FROM bg_sarvatobhadra_grid
WHERE cell_kind = 'vedha_pair' AND cell_index = %s
ORDER BY table_version DESC
LIMIT 1
"""

_FETCH_LATTA_RULES_SQL = """
SELECT graha, count_from_graha, direction, effect_description, affliction_condition, source_citation
FROM bg_phaladeepika_latta
"""

_FETCH_MALEFIC_SCALE_SQL = """
SELECT malefic_count, effect_grade, effect_description, source_citation
FROM bg_vedha_malefic_scale
"""

# M-8 (c): retrograde flag per body per day, for the
# detail.intensity_qualifier='retrograde_malefic' stamp on obstructed rows.
_FETCH_RETROGRADE_SQL = f"""
SELECT date, body
FROM ephemeris_daily
WHERE ayanamsha_id = 'tropical' AND date BETWEEN %s AND %s AND body = ANY(%s)
  AND {NODE_SERIES_PREDICATE}
  AND is_retrograde
"""

_DELETE_SQL = "DELETE FROM kala_vedha_gochara WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_vedha_gochara (
    chart_id, ayanamsha_id, vedha_kind, graha,
    window_start, window_end, start_truncated, end_truncated,
    janma_reference_fact_id, classical_citation, uncited_extension,
    grid_basis, grid_school_tag,
    source_qualification, precision_regime, corpus_verifiable,
    detail, formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(vedha_kind)s, %(graha)s,
    %(window_start)s, %(window_end)s, %(start_truncated)s, %(end_truncated)s,
    %(janma_reference_fact_id)s, %(classical_citation)s, %(uncited_extension)s,
    %(grid_basis)s, %(grid_school_tag)s,
    %(source_qualification)s, %(precision_regime)s, %(corpus_verifiable)s,
    %(detail)s::jsonb, %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, vedha_kind, graha, window_start) DO NOTHING
"""


def _has_complete_daily_series(
    rows: list[tuple[date, float]], horizon_start: date, horizon_end: date,
) -> bool:
    """Require one and only one ordered row for every inclusive horizon day."""
    expected_count = (horizon_end - horizon_start).days + 1
    if len(rows) != expected_count:
        return False
    return all(
        observed_date == horizon_start + timedelta(days=offset)
        for offset, (observed_date, _value) in enumerate(rows)
    )


def _fetch_janma_moon(conn: Any, chart_id: str) -> tuple[int, int, str] | None:
    """Returns (moon_sign_idx 0-11, moon_nak_idx 0-26, fact_id) for the natal
    Moon, or None if the L1 dependency (ga_positions) has not produced this
    fact — honest absence, never fabricated (B.10)."""
    # DB9b: the orchestrator connection uses dict_row factory; a bare cursor()
    # inherits it, making positional row[0]/row[1] access raise KeyError.
    # Pin dict_row explicitly and read by column name.
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_JANMA_MOON_SQL, (chart_id, CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if not row or row["fact_value_num"] is None:
        return None
    lon = float(row["fact_value_num"])
    sign_idx = int(lon // SIGN_SIZE_DEG) % 12
    nak_idx = int(lon // NAK_SIZE_DEG) % 27
    return sign_idx, nak_idx, str(row["fact_id"])


def _compute_ayanamsha_offset(reference_date: date) -> float:
    from brahmagyan.l0_ephemeris import _tropical_to_jd, derive_sidereal

    jd = _tropical_to_jd(reference_date)
    return derive_sidereal(0.0, jd, CANONICAL_AYANAMSHA)["ayanamsha_offset"]


def _config_horizon_date(value: Any) -> date | None:
    """Parse an optional caller-passed horizon bound (date or ISO string)."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _vedha_independence_group(
    *, body: str, relation: str, target_deg: float, window_start: date,
) -> str:
    """A08 / H-6: one physical obstruction root attenuates once. The group is
    computed by the family's single identity scheme
    (gochara_kernel.ids.independence_group) from the PHYSICAL root only — the
    obstructing body, the obstruction relation, the obstructed degree and the
    window-start instant — never from the rule that surfaced it, so several
    rows rooted in the same physical occupancy share one group."""
    return _kernel_independence_group(
        body=body,
        relation=relation,
        aspect_deg=0.0,
        target_deg=target_deg,
        t_exact_jd=None,
        t_fallback_jd=_date_to_jd(window_start),
    )


def _fetch_vedha_rules(conn: Any) -> dict[tuple[str, int], dict[str, Any]]:
    """Returns {(graha_lower, primary_house): {vedha_house, phala,
    classical_citation}} — REAL, cited bg_transit_rules rows, read verbatim
    (§N.5)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_VEDHA_RULES_SQL)
        rows = cur.fetchall()
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for r in rows:
        key = (str(r["graha"]).lower(), int(r["primary_house"]))
        out[key] = dict(r)
    return out


def _fetch_school_tagged_vedha_pair(conn: Any, nakshatra_id_1based: int) -> tuple[int, str] | None:
    """ADJUDICATION-11 Part 2: tries `bg_sarvatobhadra_grid` (school-tagged,
    deliberately empty as of this writing — migration 529) for a
    `cell_kind='vedha_pair'` row. Returns (paired_nakshatra_id_1based,
    school_tag), or None if the table has no matching row (the honest, only
    -currently-possible outcome). A future native-approved, source-verified
    school's grid activates this path with zero code change."""
    # DB9b: pin dict_row and read by column name — bare cursor() inherits the
    # orchestrator connection's dict_row factory, making row[0]/row[1] fail.
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_GRID_VEDHA_PAIR_SQL, (nakshatra_id_1based,))
        row = cur.fetchone()
    if not row or row["cell_value"] is None:
        return None
    try:
        return int(row["cell_value"]), str(row["school_tag"])
    except (TypeError, ValueError):
        return None


def _fetch_latta_rules(conn: Any) -> dict[str, dict[str, Any]]:
    """Returns {graha: {count_from_graha, direction, effect_description,
    affliction_condition, source_citation}} — REAL, cited
    bg_phaladeepika_latta rows (ADJUDICATION-11 Part 4), read verbatim
    (§N.5). Ketu is deliberately absent from the table (see
    brahmagyan/l0_phaladeepika_vedha.py) — this dict simply will not have a
    'Ketu' key, and the writer's Latta loop below naturally skips it."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_LATTA_RULES_SQL)
        rows = cur.fetchall()
    return {str(r["graha"]): dict(r) for r in rows}


def _fetch_malefic_scale(conn: Any) -> dict[int, dict[str, Any]]:
    """Returns {malefic_count: {effect_grade, effect_description,
    source_citation}} — REAL, cited bg_vedha_malefic_scale rows
    (ADJUDICATION-11 Part 4, Phaladeepika PG353), read verbatim (§N.5)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_MALEFIC_SCALE_SQL)
        rows = cur.fetchall()
    return {int(r["malefic_count"]): dict(r) for r in rows}


def _fetch_daily_sidereal_by_body(
    conn: Any, horizon_start: date, horizon_end: date, offset: float, bodies: tuple[str, ...],
) -> dict[str, list[tuple[date, float]]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_EPHEMERIS_RANGE_SQL, (horizon_start, horizon_end, list(bodies)))
        rows = cur.fetchall()
    assert_one_row_per_date(rows, context="ka_vedha_gochara._fetch_daily_sidereal_by_body")

    by_body: dict[str, list[tuple[date, float]]] = {b: [] for b in bodies}
    for r in rows:
        body = r["body"]
        if body not in by_body:
            continue
        sid_lon = (float(r["tropical_longitude"]) - offset) % 360.0
        by_body[body].append((r["date"], sid_lon))
    return by_body


def _fetch_retrograde_dates(
    conn: Any, horizon_start: date, horizon_end: date, bodies: tuple[str, ...],
) -> dict[str, set[date]]:
    """{body: {dates is_retrograde within the horizon}} — M-8 (c). Kept
    separate from _fetch_daily_sidereal_by_body so that function's signature
    (mirrored in tests) is unchanged."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_RETROGRADE_SQL, (horizon_start, horizon_end, list(bodies)))
        rows = cur.fetchall()
    assert_one_row_per_date(rows, context="ka_vedha_gochara._fetch_retrograde_dates")
    retro: dict[str, set[date]] = {}
    for r in rows:
        retro.setdefault(str(r["body"]), set()).add(r["date"])
    return retro


def _build_house_vedha_intervals(
    *,
    graha: str,
    run: dict,
    vedha_sign_idx: int,
    effective: list[tuple[str, dict]],
    sign_runs_by_graha: dict[str, list[dict]],
    retro_dates: dict[str, set[date]],
) -> list[dict]:
    """T0-8: the per-(primary residence, obstructor) obstruction-interval
    relations for one primary sign-run. Pure (no DB) — unit-mirrored against
    oracles O-VI-2/3/4.

    `effective` is [(obstructor_body, inclusive-overlap {"start","end"})] with
    the M-8 mutual-exclusion pairs ALREADY removed (exceptions first). Dates
    are converted to the §5 half-open convention: an inclusive day-range
    [s, e] becomes [s, e+1d), so the day after an obstruction's last day is
    clean (O-VI-2's boundary day). Vipareeta is then carved from EVERY
    companion joining the primary's sign during the obstruction (not
    first-only — N4), and the retrograde-malefic intensity qualifier and the
    independence group are stamped per interval.
    """
    day = timedelta(days=1)
    residence = (run["start_date"], run["end_date"] + day)
    intervals = build_obstruction_intervals(
        residence[0], residence[1],
        [(body, ov["start"], ov["end"] + day) for body, ov in effective],
    )
    if not intervals:
        return intervals

    companion_windows: list[tuple[str, date, date]] = []
    for comp_graha, comp_runs in sign_runs_by_graha.items():
        if comp_graha == graha:
            continue
        for r in comp_runs:
            if r["sign_idx"] == run["sign_idx"]:
                companion_windows.append(
                    (comp_graha, r["start_date"], r["end_date"] + day))

    for iv in intervals:
        companions = carve_vipareeta(iv, companion_windows)
        iv["vipareeta_companions"] = companions
        iv["intensity_qualifier"] = (
            "retrograde_malefic"
            if iv["obstructor_body"] in NATURAL_MALEFICS
            and any(
                iv["t_in"] <= d < iv["t_out"]
                for d in retro_dates.get(iv["obstructor_body"], ())
            )
            else None
        )
        iv["independence_group"] = _vedha_independence_group(
            body=iv["obstructor_body"],
            relation="vedha_obstruction",
            target_deg=vedha_sign_idx * SIGN_SIZE_DEG,
            window_start=iv["t_in"],
        )
    return intervals


def _house_vedha_detail(
    *,
    upstream_fp: dict,
    graha: str,
    run: dict,
    house: int,
    vedha_house: int,
    vedha_sign_idx: int,
    rule: dict,
    uncited: bool,
    intervals: list[dict],
    excepted: list[str],
    horizon_start: date,
    horizon_end: date,
) -> dict:
    """The full jsonb detail payload for one house_vedha row (T0-8 shape).
    Pure and JSON-safe — unit-mirrored without a DB."""
    provenance = "uncited_extension" if uncited else "verse_cited"
    ruling_ref = "N-14/F-29" if uncited else None
    # S-04: Moon-channel (P6) operators are testimony — Moon-primary vedha
    # annotates; it never weights, gates, or admits.
    operator_role = "scored"
    if graha == "Moon":
        operator_role = "testimony"
        ruling_ref = "S-04"

    interval_details = []
    for iv in intervals:
        companions = iv.get("vipareeta_companions") or []
        carved = [
            {"start": s["start"].isoformat(), "end": s["end"].isoformat()}
            for s in iv["segments"] if s["state"] == STATE_CANCELLED_VIPAREETA
        ]
        interval_details.append({
            "obstructor_body": iv["obstructor_body"],
            "t_in": iv["t_in"].isoformat(),
            "t_out": iv["t_out"].isoformat(),
            "half_open": True,
            "state": iv["state"],
            "segments": [
                {"start": s["start"].isoformat(), "end": s["end"].isoformat(),
                 "state": s["state"]}
                for s in iv["segments"]
            ],
            "exception": iv["exception"],
            "independence_group": iv["independence_group"],
            "intensity_qualifier": iv.get("intensity_qualifier"),
            "vipareeta": (
                {"applied": True,
                 "source_qualification": "translator_commentary",
                 "companions": companions,
                 "carved": carved}
                if companions else None
            ),
            "provenance": provenance,
            "operator_role": operator_role,
        })

    obstruction_active = any(iv["state"] == STATE_ACTIVE for iv in intervals)
    fully_cancelled = bool(intervals) and all(
        iv["state"] == STATE_CANCELLED_VIPAREETA for iv in intervals)
    obstructing_grahas: list[str] = []
    for iv in intervals:
        if iv["obstructor_body"] not in obstructing_grahas:
            obstructing_grahas.append(iv["obstructor_body"])
    malefic_occupants = [g for g in obstructing_grahas if g in NATURAL_MALEFICS]
    # Row-level independence group is an aggregate projection for the overlays
    # kernel: present exactly when ONE physical root obstructs (the per-interval
    # groups are authoritative when several roots obstruct at once).
    row_group = (
        intervals[0]["independence_group"] if len(intervals) == 1 else None)

    return {
        "upstream_fingerprint": upstream_fp,
        "primary_house": house,
        "primary_sign_idx": run["sign_idx"],
        "primary_sign_name": SIGNS[run["sign_idx"]],
        "vedha_house": vedha_house,
        "vedha_sign_idx": vedha_sign_idx,
        "vedha_sign_name": SIGNS[vedha_sign_idx],
        "phala": rule.get("phala"),
        "provenance": provenance,
        "operator_role": operator_role,
        "ruling_ref": ruling_ref,
        "obstruction_active": obstruction_active,
        "obstructing_grahas": obstructing_grahas,
        "vedha_intervals": interval_details,
        "independence_group": row_group,
        # Aggregate cancellation projection (the per-interval segments are
        # authoritative): True only when EVERY interval was fully carved by
        # vipareeta. suppression_factor=1.0 on a fully-cancelled row preserves
        # the disclosed "searched and classically cancelled — not no data"
        # semantics; no numeric suppression is served otherwise (D-PG353).
        "cancelled": fully_cancelled,
        "suppression_factor": 1.0 if fully_cancelled else None,
        "malefic_obstructing_grahas": malefic_occupants,
        "malefic_count": len(malefic_occupants),
        # D-PG353 (native, 2026-09-29): the PG353 battle scale is NOT a general
        # grade source — the grade application is removed; the keys are served
        # as explicit nulls and the removal is recorded as data.
        "malefic_effect_grade": None,
        "malefic_effect_description": None,
        "malefic_scale_citation": None,
        "d_pg353": dict(D_PG353_REMOVAL),
        "attenuation": {
            "requires_state": STATE_ACTIVE,
            "state_at_build": (
                "obstructed" if obstruction_active
                else ("cancelled_vipareeta" if intervals else "clear")
            ),
            "factor": None,
            "note": "no attenuation without an active obstruction (#17); "
                    "no cited numeric suppression scale is served (D-PG353)",
        },
        "coverage": {
            "state": "computed",
            "grain": "date",
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": horizon_end.isoformat(),
        },
        "interval_representation": (
            "interval relations served in jsonb detail pending the §5.1 "
            "vedha_interval table (separate schema-owning item); see writer.py "
            "docstring dated 2026-09-30"
        ),
        # M-8: recorded when an excluded-partner occupancy coexisted with an
        # effective obstruction (the all-excluded case emits no row — it is in
        # the writer's coverage notes instead).
        "vedha_exception": (
            {"pair_with": sorted(set(excepted)),
             "searched": True, "exception_applied": True}
            if excepted else None
        ),
    }


@register("ka_vedha_gochara")
class KaVedhaGocharaWriter(WriterBase):
    """Candidate-only vedha adapter. LIGHT writer; activation pending."""

    asset_id = "ka_vedha_gochara"

    def run(self, ctx) -> WriterResult:
        """SR-A4-01: pre-built provider stays inert until explicit binding.

        No legacy mutation, rolling fallback, publication or production input
        binding. Follow-on activation must supply a candidate-bound payload.
        """
        from services.ka_vedha_gochara.candidate import VedhaPayload
        from services.ka_vedha_gochara.storage import replace_candidate

        payload = ctx.config.get("vedha_candidate_payload")
        if payload is None or ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="KA-3a pre-build: provider binding/activation pending")
        if not isinstance(payload, VedhaPayload):
            raise TypeError("candidate dispatch requires a typed VedhaPayload")
        count = replace_candidate(ctx, payload)
        return WriterResult(asset_id=self.asset_id, rows_inserted=count,
                            notes="candidate-only vedha intervals; no publication")
