"""
services.taranga_service — Kāla Taraṅga service core (L3 D-3 Lane T-2).

Stateless temporal-convolution service. Uniform contract per
DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §5 / BRIEF_D3.md Lane T-2:

    activation(chart, domain|mechanism, t)                    -> single time-point intensity
    curve(chart, domain|mechanism, [t1, t2], resolution)       -> time-series of intensities

Split (design §5):
  - **Chart-static sensitivity substrate**, built ONCE per chart and cached
    (`build_chart_substrate` / the module-level `_SUBSTRATE_CACHE`): natal
    graha longitudes, the Vimśottarī mahādaśā spine, dasha-lord capability
    (`chart_vichara.leverage_index`), domain sensitivity weights (valence +
    weight from `chart_vichara` — the ga_vichara "judged structure" asset,
    CLAUDE.md §N.5 — never restates an L1 value, only references it),
    Mechanism graph-weights (D-2's `bodha_mechanisms` object), and sign-keyed
    Sarvashtakavarga bindus (`chart_facts` category `ashtakavarga_bindu_sign`).
  - **Time-varying kernel**, computed on demand per call: live transit
    positions via `pipeline.transit_search._get_planet_pos` (the same
    ephemeris utility ka_gochara/ka_sangam already rely on for transit
    position + speed lookups — no new ephemeris compute path is introduced),
    cos² orb scoring (`services.ka_sangam.engine.orb_strength_score` — I-17,
    applying ×1.0 / separating ×0.7), and simple additive superposition of
    every simultaneously active current (v1 baseline per design §5 — SIGNED
    suppressive / destructive-interference currents are explicit T-5 scope,
    NOT built here).

T-3 shared-kernel adapter point
--------------------------------
T-3 (parallel lane, not yet merged) is extracting a shared kernel module out
of `services.ka_sangam.engine`. This module imports `orb_strength_score`
from `services.ka_sangam.engine` in EXACTLY ONE place — the
`_orb_strength_score` re-export below. When T-3 ships its shared module,
re-pointing this service is a one-line import change at that single site;
nothing else in this file references `ka_sangam.engine` directly.

CR-87 regression guard
-----------------------
Every public function REQUIRES a `ChartRef` (chart_id) — never defaulted,
never a module-level "native chart" constant. See `tests/test_cr87_native_chart_context.py`
for the sibling two-chart regression pattern this module follows.

CR-41 (register: `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` row CR-41,
"All 4,487 `kala_activation` rows are historical — zero overlap the forward
year... Root-cause the ka_* writer's forward horizon") dissolves by
construction here: `activation()`/`curve()` compute live from the ephemeris
+ chart substrate at call time — there is no writer horizon to run past.
Any `t` (past, present, or decades-forward, bounded only by the sidereal
ephemeris' own valid range) resolves identically.

Evidence write-through (B.3 / CLAUDE.md §N.5)
----------------------------------------------
`activation()` / `curve()` themselves NEVER write to the database — they are
pure reads + computation. Only `record_evidence()` (an explicit, separate,
opt-in call) persists a result, and only when the caller names what cited it
(`cited_by`). Persists into the EXISTING `kala_taranga` table (migration 396
— "Fine grain (daily/hourly) = SERVICE computation, never stored here...
Writer: ka_taranga" — this service IS that fine-grain service the table's own
header comment anticipates) via upsert on its
`(chart_id, month, scope_kind, scope_id)` UNIQUE key, carrying
`formula_version` + `inputs` + `as_of` in `components` JSONB (no schema
change; no new table; no migration in this lane's scope).
"""
from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── T-3 shared-kernel adapter point (see module docstring) ─────────────────
# ONE import site. Swap to T-3's shared kernel module here when it ships.
from services.ka_sangam.engine import orb_strength_score as _orb_strength_score  # noqa: E402

# Existing ephemeris position/speed lookup (already relied on by ka_gochara /
# ka_sangam via find_aspect_events) — reused, not reinvented.
from pipeline.transit_search import _get_planet_pos as _live_planet_pos  # noqa: E402
from pipeline.transit_search import _shortest_arc_diff as _shortest_arc_diff  # noqa: E402

FORMULA_VERSION = "taranga_v1"

PLANET_TO_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
}
CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
TRANSIT_PLANETS = CLASSICAL_GRAHAS + ["Rahu", "Ketu"]
SAV_ELIGIBLE_SUBJECTS = {"SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"}

ASPECT_ANGLES: tuple[float, ...] = (0.0, 60.0, 90.0, 120.0, 180.0)
DEFAULT_ORB_DEG = 8.0

# v1 kernel = "dasha-capability step-functions + slow-planet transit pulses +
# SAV potency (3 sources)" (design §5 "Staged kernel"). Relative weights of
# the two non-transit sources against the summed transit-current
# contributions. Transit currents are already individually weighted by the
# target's domain/mechanism sensitivity weight, so these two are flat
# per-source weights, not per-graha.
DASHA_COMPONENT_WEIGHT = 1.0
SAV_COMPONENT_WEIGHT = 0.5

RESOLUTION_STEPS: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}

DOMAIN_NAMES = {"wealth", "career", "marriage", "health", "general"}


# ── CR-87: required chart reference ─────────────────────────────────────────

@dataclass(frozen=True)
class ChartRef:
    """Per-chart handle. `chart_id` is REQUIRED — CR-87 regression guard.
    Never default this, never hardcode a native chart_id here."""
    chart_id: str
    ayanamsha_id: str = "lahiri_chitrapaksha"

    def __post_init__(self) -> None:
        if not self.chart_id:
            raise ValueError(
                "taranga_service.ChartRef: chart_id is REQUIRED (CR-87) — "
                "refusing to construct a chart-less/defaulted reference."
            )


def _require_chart(chart: Any) -> ChartRef:
    if chart is None or not isinstance(chart, ChartRef) or not chart.chart_id:
        raise ValueError(
            "taranga_service: `chart` (a ChartRef with a non-empty chart_id) "
            "is a REQUIRED parameter on every call — CR-87 regression guard. "
            "Never call with chart=None or a defaulted chart_id."
        )
    return chart


# ── DB connection (mirrors brahmagyan.l0_ephemeris._get_conn) ──────────────

def _get_conn():
    import psycopg2  # type: ignore[import]
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("taranga_service: DATABASE_URL not set")
    return psycopg2.connect(url)


def _rows_as_dicts(cur) -> list[dict[str, Any]]:
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ── Chart-static substrate ──────────────────────────────────────────────────

@dataclass
class ChartSubstrate:
    chart_id: str
    ayanamsha_id: str
    graha_natal_longitude: dict[str, float] = field(default_factory=dict)
    dasha_periods: list[dict[str, Any]] = field(default_factory=list)   # [{lord, start: date, end: date}]
    dasha_lord_capability: dict[str, float] = field(default_factory=dict)
    domain_weights: dict[str, dict[str, float]] = field(default_factory=dict)  # domain -> {graha: signed weight}
    graha_valence_sign: dict[str, float] = field(default_factory=dict)         # SUBJECT -> mean D1 valence value_num
    mechanism_index: dict[str, dict[str, Any]] = field(default_factory=dict)   # mechanism_id -> {members, graph_weight, valence, domains_affected}
    sav_bindus: dict[tuple[str, int], int] = field(default_factory=dict)       # (SUBJECT|'SARVA', sign_number) -> bindus
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    known_gaps: list[str] = field(default_factory=list)


_SUBSTRATE_CACHE: dict[tuple[str, str], ChartSubstrate] = {}


def _load_natal_longitudes(conn, chart: ChartRef) -> dict[str, float]:
    out: dict[str, float] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal'
            """,
            (chart.chart_id, chart.ayanamsha_id),
        )
        for row in _rows_as_dicts(cur):
            subj = row["fact_subject"]
            val = row["fact_value_num"]
            if subj and val is not None:
                out[subj] = float(val)
    return out


def _load_dasha_periods(conn, chart: ChartRef) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT lord_graha, start_date, end_date
            FROM chart_dashas
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND system_id = 'vimshottari' AND level_n = 1
            ORDER BY start_date
            """,
            (chart.chart_id, chart.ayanamsha_id),
        )
        for row in _rows_as_dicts(cur):
            start = row["start_date"]
            end = row["end_date"]
            if start is None or end is None:
                continue
            start_d = start.date() if hasattr(start, "date") else start
            end_d = end.date() if hasattr(end, "date") else end
            out.append({"lord": row["lord_graha"], "start": start_d, "end": end_d})
    return out


def _load_leverage_and_valence(conn, chart: ChartRef) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    """domain_weights[domain][graha_subject] = signed leverage_index weight
    (magnitude from chart_vichara.leverage_index, sign from that graha's mean
    D1 valence_pass value_num — both already-computed L1/L2-boundary judged
    values, never re-derived here per §N.5)."""
    leverage: dict[str, dict[str, float]] = {}
    valence_sum: dict[str, float] = {}
    valence_n: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT vichara_family, subject, actor, domain, varga_id, value_num
            FROM chart_vichara
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND vichara_family IN ('leverage_index', 'valence_pass')
            """,
            (chart.chart_id, chart.ayanamsha_id),
        )
        for row in _rows_as_dicts(cur):
            fam = row["vichara_family"]
            if fam == "leverage_index":
                domain = row["domain"]
                subj = row["subject"]
                val = row["value_num"]
                if domain and subj and val is not None:
                    leverage.setdefault(domain, {})[subj] = float(val)
            elif fam == "valence_pass" and row.get("varga_id") == "D1":
                actor = row.get("actor") or row.get("subject")
                val = row["value_num"]
                if actor and val is not None:
                    valence_sum[actor] = valence_sum.get(actor, 0.0) + float(val)
                    valence_n[actor] = valence_n.get(actor, 0) + 1

    graha_valence = {k: valence_sum[k] / valence_n[k] for k in valence_sum}

    domain_weights: dict[str, dict[str, float]] = {}
    for domain, per_graha in leverage.items():
        signed: dict[str, float] = {}
        for subj, magnitude in per_graha.items():
            sign = 1.0
            v = graha_valence.get(subj)
            if v is not None and v < 0:
                sign = -1.0
            signed[subj] = magnitude * sign
        domain_weights[domain] = signed
    return domain_weights, graha_valence


def _load_mechanisms(conn, chart: ChartRef) -> dict[str, dict[str, Any]]:
    """Mechanism graph-weights from D-2's shipped Mechanism object
    (`bodha_mechanisms` — BRIEF_D3.md §F0 "D-2 Mechanism object — SHIPPED").
    graph_weight = edge_strength_avg × pagerank_avg (both already-computed L2
    fields; combined here, not re-derived)."""
    out: dict[str, dict[str, Any]] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT mechanism_id, mechanism_name, mechanism_class, valence,
                   member_node_ids_array, edge_strength_avg, domains_affected_array,
                   centrality_summary_jsonb
            FROM bodha_mechanisms
            WHERE chart_id = %s AND ayanamsha_id = %s
            """,
            (chart.chart_id, chart.ayanamsha_id),
        )
        mech_rows = _rows_as_dicts(cur)

        all_node_ids: set[str] = set()
        for r in mech_rows:
            for nid in (r.get("member_node_ids_array") or []):
                all_node_ids.add(nid)

        node_subject: dict[str, str] = {}
        if all_node_ids:
            cur.execute(
                """
                SELECT node_id, node_subject, node_type
                FROM bodha_cgm_nodes
                WHERE chart_id = %s AND node_id = ANY(%s) AND node_type = 'graha'
                """,
                (chart.chart_id, list(all_node_ids)),
            )
            for row in _rows_as_dicts(cur):
                node_subject[str(row["node_id"])] = row["node_subject"]

        for r in mech_rows:
            members = sorted({
                node_subject[str(nid)]
                for nid in (r.get("member_node_ids_array") or [])
                if str(nid) in node_subject
            })
            if not members:
                continue
            edge_strength = r.get("edge_strength_avg")
            centrality = r.get("centrality_summary_jsonb") or {}
            pagerank_avg = centrality.get("pagerank_avg") if isinstance(centrality, dict) else None
            graph_weight = 0.5  # neutral fallback (documented gap, never invented as 0)
            if edge_strength is not None and pagerank_avg is not None:
                graph_weight = float(edge_strength) * float(pagerank_avg)
            elif edge_strength is not None:
                graph_weight = float(edge_strength)
            out[str(r["mechanism_id"])] = {
                "mechanism_name": r.get("mechanism_name"),
                "mechanism_class": r.get("mechanism_class"),
                "valence": r.get("valence"),
                "members": members,
                "graph_weight": graph_weight,
                "domains_affected": r.get("domains_affected_array") or [],
            }
    return out


def _load_sav_bindus(conn, chart: ChartRef) -> dict[tuple[str, int], int]:
    out: dict[tuple[str, int], int] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category = 'ashtakavarga_bindu_sign' AND fact_key = 'bindus'
            """,
            (chart.chart_id, chart.ayanamsha_id),
        )
        for row in _rows_as_dicts(cur):
            subj = row["fact_subject"] or ""
            if "-SIGN_" not in subj:
                continue
            graha_part, sign_part = subj.split("-SIGN_", 1)
            try:
                sign_number = int(sign_part)
            except ValueError:
                continue
            val = row["fact_value_num"]
            if val is not None:
                out[(graha_part, sign_number)] = int(val)
    return out


def build_chart_substrate(chart: ChartRef, *, conn=None, force_rebuild: bool = False) -> ChartSubstrate:
    """Build (or return the cached) chart-static sensitivity substrate.

    Expensive (several DB queries) — built ONCE per (chart_id, ayanamsha_id)
    and cached in-process. Call with force_rebuild=True to invalidate (e.g.
    after a rebuild that changed ga_vichara/bodha_mechanisms rows)."""
    chart = _require_chart(chart)
    cache_key = (chart.chart_id, chart.ayanamsha_id)
    if not force_rebuild and cache_key in _SUBSTRATE_CACHE:
        return _SUBSTRATE_CACHE[cache_key]

    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True
    try:
        graha_lon = _load_natal_longitudes(conn, chart)
        dasha_periods = _load_dasha_periods(conn, chart)
        domain_weights, graha_valence = _load_leverage_and_valence(conn, chart)
        mechanisms = _load_mechanisms(conn, chart)
        sav_bindus = _load_sav_bindus(conn, chart)

        # dasha_lord_capability: reuse leverage_index magnitude, averaged
        # across domains the lord participates in (a graha's overall
        # "capability" for the dasha-step-function component — distinct from
        # its per-domain SIGNED weight used for the transit-current pass).
        capability_sum: dict[str, float] = {}
        capability_n: dict[str, int] = {}
        for domain, per_graha in domain_weights.items():
            for subj, signed in per_graha.items():
                capability_sum[subj] = capability_sum.get(subj, 0.0) + abs(signed)
                capability_n[subj] = capability_n.get(subj, 0) + 1
        dasha_lord_capability = {
            k: capability_sum[k] / capability_n[k] for k in capability_sum
        }

        known_gaps: list[str] = []
        if not graha_lon:
            known_gaps.append("no graha_position/longitude_sidereal chart_facts found")
        if not dasha_periods:
            known_gaps.append("no level_n=1 chart_dashas rows found")
        if not domain_weights:
            known_gaps.append("no chart_vichara.leverage_index rows found")
        if not mechanisms:
            known_gaps.append("no bodha_mechanisms rows found")

        substrate = ChartSubstrate(
            chart_id=chart.chart_id,
            ayanamsha_id=chart.ayanamsha_id,
            graha_natal_longitude=graha_lon,
            dasha_periods=dasha_periods,
            dasha_lord_capability=dasha_lord_capability,
            domain_weights=domain_weights,
            graha_valence_sign=graha_valence,
            mechanism_index=mechanisms,
            sav_bindus=sav_bindus,
            known_gaps=known_gaps,
        )
        _SUBSTRATE_CACHE[cache_key] = substrate
        return substrate
    finally:
        if close_conn:
            conn.close()


def clear_substrate_cache(chart: Optional[ChartRef] = None) -> None:
    """Test/ops helper: drop the cached substrate for one chart, or all."""
    if chart is None:
        _SUBSTRATE_CACHE.clear()
        return
    _SUBSTRATE_CACHE.pop((chart.chart_id, chart.ayanamsha_id), None)


# ── Time-varying kernel ──────────────────────────────────────────────────────

def _subject_to_planet_name(subj: str) -> Optional[str]:
    for planet, s in PLANET_TO_SUBJECT.items():
        if s == subj:
            return planet
    return None


def _resolve_target_weights(substrate: ChartSubstrate, target: str) -> tuple[dict[str, float], dict[str, Any]]:
    """Returns ({SUBJECT: signed weight}, meta) for a domain or mechanism
    target key. Raises ValueError for an unresolvable target (fail loud,
    B.10 — never silently substitute another target's weights)."""
    if target in substrate.domain_weights:
        return substrate.domain_weights[target], {"target_kind": "domain", "target": target}
    if target in DOMAIN_NAMES:
        # Known domain name but no leverage_index rows resolved for this
        # chart (honest gap, not a silent zero-substitution).
        return {}, {
            "target_kind": "domain", "target": target,
            "known_gap": f"no chart_vichara.leverage_index rows for domain={target!r}",
        }
    mech = substrate.mechanism_index.get(target)
    if mech is not None:
        gw = mech["graph_weight"]
        weights = {subj: gw for subj in mech["members"]}
        return weights, {
            "target_kind": "mechanism", "target": target,
            "mechanism_name": mech.get("mechanism_name"),
            "mechanism_class": mech.get("mechanism_class"),
            "mechanism_valence": mech.get("valence"),
            "graph_weight": gw,
        }
    raise ValueError(
        f"taranga_service: unresolvable domain_or_mechanism target {target!r} for "
        f"chart {substrate.chart_id} — not a known domain "
        f"({sorted(DOMAIN_NAMES)}) and not a mechanism_id present in "
        f"bodha_mechanisms for this chart."
    )


def _to_jd(t: datetime) -> float:
    import swisseph as swe
    t_utc = t.astimezone(timezone.utc) if t.tzinfo else t.replace(tzinfo=timezone.utc)
    return swe.julday(
        t_utc.year, t_utc.month, t_utc.day,
        t_utc.hour + t_utc.minute / 60.0 + t_utc.second / 3600.0,
    )


def _best_aspect_orb(transit_lon: float, natal_lon: float) -> tuple[float, float]:
    """Return (aspect_angle, orb_deg) for the closest of the 5 classical
    aspect angles (0/60/90/120/180) — the tightest aspect governs."""
    sep = abs(_shortest_arc_diff(transit_lon, natal_lon))
    best_angle, best_orb = ASPECT_ANGLES[0], abs(sep - ASPECT_ANGLES[0])
    for ang in ASPECT_ANGLES[1:]:
        orb = abs(sep - ang)
        if orb < best_orb:
            best_angle, best_orb = ang, orb
    return best_angle, best_orb


def _applying_or_separating(transit_planet: str, jd: float, target_lon: float) -> str:
    import swisseph as swe
    delta = 0.01  # days — matches pipeline.transit_search's own epsilon
    lon_before, _ = _live_planet_pos(swe, transit_planet, jd - delta)
    lon_after, _ = _live_planet_pos(swe, transit_planet, jd + delta)
    arc_before = abs(_shortest_arc_diff(lon_before, target_lon))
    arc_after = abs(_shortest_arc_diff(lon_after, target_lon))
    if arc_after < arc_before:
        return "applying"
    return "separating"


# Simple in-process memoization for repeated (planet, jd) lookups within a
# single curve() sweep — NOT a new persistent/DB caching layer, just avoids
# redundant swisseph calls for the same instant inside one request.
_POSITION_MEMO: dict[tuple[str, float], tuple[float, float]] = {}
_POSITION_MEMO_MAX = 4096


def _transit_position(transit_planet: str, jd: float) -> tuple[float, float]:
    key = (transit_planet, round(jd, 6))
    cached = _POSITION_MEMO.get(key)
    if cached is not None:
        return cached
    import swisseph as swe
    lon, speed = _live_planet_pos(swe, transit_planet, jd)
    if len(_POSITION_MEMO) > _POSITION_MEMO_MAX:
        _POSITION_MEMO.clear()
    _POSITION_MEMO[key] = (lon, speed)
    return lon, speed


def _transit_currents(substrate: ChartSubstrate, weights: dict[str, float], jd: float) -> list[dict[str, Any]]:
    currents: list[dict[str, Any]] = []
    for transit_planet in TRANSIT_PLANETS:
        t_lon, _t_speed = _transit_position(transit_planet, jd)
        for subj, weight in weights.items():
            if weight == 0.0:
                continue
            natal_lon = substrate.graha_natal_longitude.get(subj)
            if natal_lon is None:
                continue
            aspect_angle, orb_deg = _best_aspect_orb(t_lon, natal_lon)
            if orb_deg > DEFAULT_ORB_DEG:
                continue
            appsep = _applying_or_separating(transit_planet, jd, natal_lon)
            orb_score = _orb_strength_score(orb_deg, DEFAULT_ORB_DEG, appsep)
            contribution = orb_score * weight
            if contribution == 0.0:
                continue
            currents.append({
                "transit_planet": transit_planet,
                "natal_subject": subj,
                "aspect_angle_deg": aspect_angle,
                "orb_deg": round(orb_deg, 4),
                "applying_separating": appsep,
                "orb_score": round(orb_score, 4),
                "weight": round(weight, 4),
                "contribution": round(contribution, 6),
            })
    return currents


def _dasha_component(substrate: ChartSubstrate, t: datetime) -> tuple[float, dict[str, Any]]:
    d = t.date() if hasattr(t, "date") else t
    for period in substrate.dasha_periods:
        if period["start"] <= d <= period["end"]:
            lord = period["lord"]
            cap = substrate.dasha_lord_capability.get(lord)
            if cap is None:
                return 0.5, {"dasha_lord": lord, "dasha_capability": 0.5, "known_gap": "no leverage_index capability for this lord"}
            return cap, {"dasha_lord": lord, "dasha_capability": round(cap, 4)}
    return 0.0, {"dasha_lord": None, "dasha_capability": 0.0, "known_gap": "t is outside the computed dasha spine"}


def _sav_component(substrate: ChartSubstrate, jd: float) -> tuple[float, dict[str, Any]]:
    if not substrate.sav_bindus:
        return 0.0, {"known_gap": "no ashtakavarga_bindu_sign chart_facts found"}
    scores: list[float] = []
    detail: dict[str, Any] = {}
    for planet in CLASSICAL_GRAHAS:
        subj = PLANET_TO_SUBJECT[planet]
        lon, _speed = _transit_position(planet, jd)
        sign_number = int(lon // 30.0) + 1
        bindus = substrate.sav_bindus.get((subj, sign_number))
        if bindus is None:
            continue
        score = min(1.0, bindus / 8.0)
        scores.append(score)
        detail[planet] = {"sign_number": sign_number, "bindus": bindus, "score": round(score, 4)}
    avg = sum(scores) / len(scores) if scores else 0.0
    return avg, {"per_planet": detail, "avg_sav_potency": round(avg, 4)}


def _evaluate(substrate: ChartSubstrate, target: str, t: datetime) -> dict[str, Any]:
    weights, target_meta = _resolve_target_weights(substrate, target)
    jd = _to_jd(t)
    currents = _transit_currents(substrate, weights, jd) if weights else []
    transit_sum = sum(c["contribution"] for c in currents)
    dasha_cap, dasha_meta = _dasha_component(substrate, t)
    sav_score, sav_meta = _sav_component(substrate, jd)

    # v1 additive superposition (design §5: "start with simple
    # summation/superposition" — SIGNED destructive interference is T-5
    # scope, not built here).
    intensity = transit_sum + DASHA_COMPONENT_WEIGHT * dasha_cap + SAV_COMPONENT_WEIGHT * sav_score

    return {
        "target": target,
        "target_meta": target_meta,
        "t": t.isoformat() if hasattr(t, "isoformat") else str(t),
        "activation": round(intensity, 6),
        "components": {
            "transit_currents": currents,
            "transit_sum": round(transit_sum, 6),
            "dasha": dasha_meta,
            "sav": sav_meta,
            "superposition_model": "additive_v1",
        },
        "formula_version": FORMULA_VERSION,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def activation(chart: ChartRef, domain_or_mechanism: str, t: datetime, *, conn=None) -> dict[str, Any]:
    """Single time-point activation intensity for (chart, domain|mechanism, t).

    CR-41 note: `t` may be ANY instant — past, present, or arbitrarily far in
    the future (bounded only by the sidereal ephemeris' own valid range,
    ~1900-2150 for this deployment) — there is no writer horizon; this is
    computed live from the chart-static substrate + a live transit kernel.
    """
    chart = _require_chart(chart)
    if not domain_or_mechanism:
        raise ValueError("taranga_service.activation: domain_or_mechanism is required")
    if t is None:
        raise ValueError("taranga_service.activation: t is required")
    substrate = build_chart_substrate(chart, conn=conn)
    result = _evaluate(substrate, domain_or_mechanism, t)
    result["chart_id"] = chart.chart_id
    result["ayanamsha_id"] = chart.ayanamsha_id
    return result


def curve(
    chart: ChartRef,
    domain_or_mechanism: str,
    t_start: datetime,
    t_end: datetime,
    resolution: str = "daily",
    *,
    conn=None,
) -> dict[str, Any]:
    """Time series of activation intensities over [t_start, t_end] at the
    given resolution ('daily' | 'weekly' | 'monthly').

    CR-41 note: t_end may extend arbitrarily far past any batch writer's
    precomputed horizon — every point is computed live, on demand.
    """
    chart = _require_chart(chart)
    if not domain_or_mechanism:
        raise ValueError("taranga_service.curve: domain_or_mechanism is required")
    if t_start is None or t_end is None:
        raise ValueError("taranga_service.curve: t_start and t_end are required")
    if t_end < t_start:
        raise ValueError("taranga_service.curve: t_end must be >= t_start")
    step = RESOLUTION_STEPS.get(resolution)
    if step is None:
        raise ValueError(
            f"taranga_service.curve: unknown resolution {resolution!r} — "
            f"expected one of {sorted(RESOLUTION_STEPS)}"
        )

    substrate = build_chart_substrate(chart, conn=conn)
    points: list[dict[str, Any]] = []
    t = t_start
    while t <= t_end:
        point = _evaluate(substrate, domain_or_mechanism, t)
        points.append({
            "t": point["t"],
            "activation": point["activation"],
            "components_summary": {
                "transit_sum": point["components"]["transit_sum"],
                "dasha_capability": point["components"]["dasha"].get("dasha_capability"),
                "sav_potency": point["components"]["sav"].get("avg_sav_potency"),
                "n_transit_currents": len(point["components"]["transit_currents"]),
            },
        })
        t = t + step

    return {
        "chart_id": chart.chart_id,
        "ayanamsha_id": chart.ayanamsha_id,
        "target": domain_or_mechanism,
        "resolution": resolution,
        "t_start": t_start.isoformat(),
        "t_end": t_end.isoformat(),
        "points": points,
        "formula_version": FORMULA_VERSION,
    }


def _month_start(t: datetime) -> date:
    d = t.date() if hasattr(t, "date") else t
    return date(d.year, d.month, 1)


def record_evidence(
    chart: ChartRef,
    domain_or_mechanism: str,
    t: datetime,
    *,
    cited_by: str,
    result: Optional[dict[str, Any]] = None,
    conn=None,
) -> dict[str, Any]:
    """Explicit, OPT-IN evidence write-through (B.3 / CLAUDE.md §N.5).

    Only call this when an `activation()`/`curve()` result is CITED in a
    reading or consumed by L5 — routine/exploratory calls must NOT persist
    anything. `cited_by` is REQUIRED and names the consumer (a reading id,
    an L5 job id, etc.) so every persisted row is traceable to why it was
    kept.

    Persists into the EXISTING `kala_taranga` table (see module docstring)
    via upsert on (chart_id, month, scope_kind, scope_id). `scope_kind` is
    'domain' for domain targets and 'event_class' for mechanism targets (the
    table's CHECK constraint only allows those two values today — a
    dedicated 'mechanism' scope_kind would need a migration, out of this
    lane's scope; mechanism evidence is stored under 'event_class' with
    scope_id = mechanism_id, flagged via `components.target_kind`).
    """
    chart = _require_chart(chart)
    if not cited_by:
        raise ValueError(
            "taranga_service.record_evidence: cited_by is REQUIRED — "
            "write-through must name what consumed this evidence (B.3); "
            "never call this for a routine/exploratory activation() call."
        )
    if result is None:
        result = activation(chart, domain_or_mechanism, t, conn=conn)

    target_kind = result.get("target_meta", {}).get("target_kind", "domain")
    scope_kind = "domain" if target_kind == "domain" else "event_class"
    month = _month_start(t)
    as_of = datetime.now(timezone.utc).isoformat()

    components_payload = {
        "formula_version": result["formula_version"],
        "inputs": {
            "target": domain_or_mechanism,
            "target_kind": target_kind,
            "t": result["t"],
        },
        "as_of": as_of,
        "cited_by": cited_by,
        "detail": result["components"],
    }

    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kala_taranga
                    (chart_id, month, scope_kind, scope_id, activation, components, formula_version, computed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (chart_id, month, scope_kind, scope_id) DO UPDATE SET
                    activation = EXCLUDED.activation,
                    components = EXCLUDED.components,
                    formula_version = EXCLUDED.formula_version,
                    computed_at = NOW()
                RETURNING taranga_id
                """,
                (
                    chart.chart_id, month, scope_kind, domain_or_mechanism,
                    result["activation"],
                    json.dumps(components_payload),
                    result["formula_version"],
                ),
            )
            taranga_id = cur.fetchone()[0]
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()

    return {
        "taranga_id": str(taranga_id),
        "chart_id": chart.chart_id,
        "month": month.isoformat(),
        "scope_kind": scope_kind,
        "scope_id": domain_or_mechanism,
        "activation": result["activation"],
        "cited_by": cited_by,
        "as_of": as_of,
    }
