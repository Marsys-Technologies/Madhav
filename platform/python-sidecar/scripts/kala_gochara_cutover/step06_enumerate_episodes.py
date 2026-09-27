#!/usr/bin/env python3
"""step06_enumerate_episodes.py — WP10 step-6 producer: '4.0' episode enumeration.

The driver E-018 (evidence/step06_evidence.md) recorded as missing, authorized
branch-local by ADK-0011(i). It produces the `--episodes-json` /
`--coverage-json` payloads step06_candidate_build.py consumes:

  * reads the chart's targets from `gochara_resonance_map` (WP1_CONTRACTS §2.2:
    the map stores target_resolution_state, NOT longitudes — point longitudes
    and sign spans are re-derived here from L1 chart_facts, reusing the
    resonance writer's own fetch SQL and constants so the two cannot drift),
  * builds the kernel ArcIndex per body over the horizon and calls the kernel
    solve functions (arcs/knots/contacts/episodes/coverage — the kernel stays
    the only solving library),
  * maps kernel Episode objects to the ledger's `_normalize_episode` dict
    shape (the shape precedent is ka_gochara/service.py::_moon_on_demand and
    step06's own synthetic episode),
  * stamps the candidate flags as PARAMETERS (recorded in the build report;
    step06 records them in the input generation vector):
    activity_shape=linear_no_box, orb_max_deg=--orb-deg (candidate 1 = 5.0°,
    brief §12.2), M-3 (Moon excluded from persisted enumeration — R7 serves it
    on demand), N-14 (nodes cast no dṛṣṭi — kernel SPECIAL_DRISHTI_DEG),
    N-15, N-17, N-22, M-8,
  * runs the §12.9 overlay-freshness gate BEFORE enumerating (a candidate must
    not be enumerated on stale overlay rows — the same refusal step06 applies
    at consume time, exit 7), and stamps the current upstream fingerprints
    (logic.upstream_fingerprint / moorti_upstream_fingerprint through the
    writers' own fetch functions) in the build report,
  * dedupes the payload to one row per physical contact (ADK-0020 option (i):
    keyed by the pinned WP1 §3.2 contact_id; highest-weight map row survives,
    weight ties break to the lexicographically smallest target_ref, deeper
    weight ties are surfaced in the report as map defects; per ADK-0021
    option (A) classical_citation follows the surviving weight-selected map
    row — disclosed, with dropped citations recoverable — while divergence in
    any other field refuses the run with exit 5; dropped target_refs and
    citations are recoverable via the `<episodes-out>.dropped_refs.json`
    artifact keyed by contact_id).

Orb regime (disclosed synthesis, recorded in the review packet): WP1 §7's
orb_conj_*/orb_drishti_* values are "practice pending M-1"; M-1 is now
ratified with candidate-1 enumeration orb 5.0° (brief §12.2). Conjunction and
drishti episodes therefore enumerate at --orb-deg (default 5.0) via the
kernel's additive orb_override_deg parameter — the pinned ORB_TABLE is never
mutated and orb_source still names the §7 relation-class row id.
orb_return_* rows are "practice" WITHOUT "pending M-1", so returns enumerate
at the table value (0.5°). Boundary relations are boundary-exact (orb_ingress).

Persisted bodies: the eight non-Moon grahas (M-3/R7). Moon episodes are served
on demand by ka_gochara/service.py::_moon_on_demand with moon_on_demand
coverage; this driver records the moon channel in its report and never
enumerates Moon for persistence.

Relations (WP1 §3.1 vocabulary): conjunction, drishti_contact, sign_ingress,
nakshatra_ingress, kakshya_cell_crossing, return. Point targets (karaka,
dasha_lord_portfolio, lord, yoga_constituent, sensitive_degree-positive) get
conjunction + drishti_contact + return (return only for the target's owning
graha — a return is body X returning to body X's natal longitude; for any
other body the root set is identical to the conjunction's) plus the three
boundary relations attached to the target (the _moon_on_demand precedent).
Interval targets (bhava, arudha, bhava_arudha, mechanism_node, M-6 derived)
get residence spans and sign_ingress via kernel residence_spans — NEVER point
contacts (M-5). mechanism_node intervals are enumerated for the graha the ref
names; M-6 derived intervals for the formula's ruled agent (target_qualifier
'agent:X') only — the verse names the transiting graha.

t_exact is NOT NULL in migration 1081, so kernel episodes WITHOUT an exact
crossing inside the horizon (E8-2 tangencies, knot-edge clips) are NOT
persistable: they are counted in the build report (episodes_without_exact)
and excluded from the payload rather than fabricating an instant. Kernel
'truncated_at_horizon=both' maps to NULL (WP1 §3.1 CHECK).

Usage:
    python3 step06_enumerate_episodes.py --dsn postgresql://... \
        --chart-id <uuid> \
        [--horizon-start 2020-01-01T00:00:00+00:00 \
         --horizon-end 2030-01-01T00:00:00+00:00] \
        [--orb-deg 5.0] [--ephe-path .run/se1] [--no-refine] \
        --episodes-out eps.json --coverage-out cov.json [--evidence]

Exit codes: 0 enumerated; 3 cannot proceed; 4 production refusal (inherited
from common.connect, step 6 -> tranche 2); 5 refused: ADK-0020/ADK-0021
dedupe found a duplicate group diverging beyond target_ref and
classical_citation; 7 refused: the chart's overlay rows are not FRESH
against the reference tables (§12.9).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services.gochara_kernel import arcs as gk_arcs  # noqa: E402
from services.gochara_kernel import contacts as gk_contacts  # noqa: E402
from services.gochara_kernel import convention as gk_convention  # noqa: E402
from services.gochara_kernel import coverage as gk_coverage  # noqa: E402
from services.gochara_kernel import episodes as gk_episodes  # noqa: E402
from services.gochara_kernel import ids as gk_ids  # noqa: E402
from services.gochara_kernel import knots as gk_knots  # noqa: E402
from services.gochara_grammar.derived_points import (  # noqa: E402
    YAMAKANTAKA_FORMULAS,
    difference_sign_num,
    fifth_star_lord,
    mandi_distance_target_sign_num,
    sign_num_of,
)
from services.ka_gochara_resonance import writer as resonance_writer  # noqa: E402

UTC = timezone.utc
LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"

# M-3/R7: the eight non-Moon grahas are enumerated for persistence.
PERSISTED_BODIES: tuple[str, ...] = (
    "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu",
)

POINT_TARGET_TYPES = (
    "karaka", "dasha_lord_portfolio", "lord", "yoga_constituent",
    "sensitive_degree",
)
INTERVAL_TARGET_TYPES = (
    "bhava", "arudha", "bhava_arudha", "mechanism_node",
    "gulika_mandi_distance", "yamakantaka_difference",
)
POINT_RELATIONS = (
    "conjunction", "drishti_contact", "return",
    "sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing",
)
BOUNDARY_RELATIONS = gk_contacts.BOUNDARY_RELATIONS

CANDIDATE_FLAGS = {
    "activity_shape": "linear_no_box",       # M-1 ratified candidate 1 (§12.2)
    "moon_channel": "separate",              # M-3/R7: Moon on demand, never persisted
    "nodal_drishti": "removed",              # N-14
    "sade_sati_mode": "testimony",           # N-15
    "kakshya_bindu_interim": True,           # N-22
    "overlay_stamps": True,                  # N-17
    "vedha_exceptions": "m8_rows",           # M-8
}

_SUBJECT_TO_GRAHA = {v: k for k, v in resonance_writer._KARAKA_FACT_SUBJECT.items()}
_SIGNS = resonance_writer._SIGNS

_FETCH_MAP_ROWS_SQL = """
SELECT event_class, target_type, target_ref, weight, classical_citation,
       uncited_extension, target_resolution_state, target_qualifier
FROM gochara_resonance_map
WHERE chart_id = %s
ORDER BY event_class, target_type, target_ref
"""

_FETCH_POSITIONS_SQL = """
SELECT fact_subject, fact_key, fact_value_num, fact_value_text, fact_id
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
  AND fact_key IN ('longitude_sidereal', 'sign')
"""

_FETCH_ARUDHA_SIGNS_SQL = """
SELECT fact_id, fact_subject, fact_value_text
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'arudha_pada'
  AND fact_key = 'sign'
"""

_FETCH_SENSITIVE_CHECKS_SQL = """
SELECT fact_id, fact_subject
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'sensitive_degree_check'
"""

_FETCH_YOGA_FIRINGS_SQL = """
SELECT yoga_canonical_id, constituent_fact_ids
FROM ga_yoga_firings
WHERE chart_id = %s AND ayanamsha_id = %s AND fired = true
"""

_FETCH_FACT_LONGITUDES_SQL = """
SELECT fact_id, fact_subject, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal'
"""


# ── target resolution (WP1_CONTRACTS §2.2) ───────────────────────────────────


@dataclass
class ResolvedTarget:
    """One enumeration target: a point longitude or a whole-sign interval."""
    event_class: str
    target_type: str
    target_ref: str
    qualifier: str | None
    classical_citation: str | None
    uncited_extension: bool
    state: str                        # resolved | unavailable | unqualified
    kind: str | None = None           # 'point' | 'interval'
    longitude_deg: float | None = None
    span_deg: tuple[float, float] | None = None
    target_sign: str | None = None
    owner_graha: str | None = None    # return-relation gate (point targets)
    agent: str | None = None          # body restriction (interval targets)
    target_fact_id: str | None = None
    weight: float | None = None       # source map row's weight (ADK-0020 dedupe)


@dataclass
class ResolutionFacts:
    """The L1 inputs target resolution reads. Built by
    fetch_resolution_facts(conn, chart_id); unit tests build it by hand
    (mirroring fixtures/wp1_target_resolution.json case inputs)."""
    positions: dict = field(default_factory=dict)          # subject -> {longitude, sign, fact_id}
    graha_sign_nums: dict = field(default_factory=dict)    # subject -> 1-based sign_num
    sign_lords: dict | None = None                         # {1..12: lord} or None
    arudha_signs_by_fact: dict = field(default_factory=dict)    # fact_id -> sign name
    arudha_signs_by_subject: dict = field(default_factory=dict) # subject -> sign name
    sensitive_checks: dict = field(default_factory=dict)   # check fact_id -> fact_subject
    yoga_firings: dict = field(default_factory=dict)       # yoga id -> [constituent fact ids]
    fact_longitudes: dict = field(default_factory=dict)    # fact_id -> longitude
    fact_subjects: dict = field(default_factory=dict)      # fact_id -> subject
    gulika_mandi_signs: dict = field(default_factory=dict) # MANDI/GULIKA/YAMAKANTAKA -> sign
    moon_nakshatra_id: int | None = None


def fetch_resolution_facts(conn, chart_id: str) -> ResolutionFacts:
    """Live reads for the resolution pass — the same tables/queries the
    resonance writer resolves against (writer._fetch_chart_resolution_context
    / _fetch_m6_context reused verbatim where the shape matches)."""
    import psycopg.rows

    ctx = resonance_writer._fetch_chart_resolution_context(conn, chart_id)
    m6 = resonance_writer._fetch_m6_context(conn, chart_id)
    facts = ResolutionFacts(
        graha_sign_nums=m6["graha_sign_nums"],
        sign_lords=ctx["sign_lords"],
        gulika_mandi_signs=m6["gulika_mandi_signs"],
        moon_nakshatra_id=m6["moon_nakshatra_id"],
    )
    ay = resonance_writer._CANONICAL_AYANAMSHA
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_POSITIONS_SQL, (chart_id, ay))
        for r in cur.fetchall():
            slot = facts.positions.setdefault(str(r["fact_subject"]), {})
            if r["fact_key"] == "longitude_sidereal":
                slot["longitude"] = float(r["fact_value_num"])
                slot["fact_id"] = str(r["fact_id"])
            else:
                slot["sign"] = str(r["fact_value_text"] or "").strip()
        cur.execute(_FETCH_ARUDHA_SIGNS_SQL, (chart_id, ay))
        for r in cur.fetchall():
            sign = str(r["fact_value_text"] or "").strip()
            facts.arudha_signs_by_fact[str(r["fact_id"])] = sign
            facts.arudha_signs_by_subject[str(r["fact_subject"])] = sign
        cur.execute(_FETCH_SENSITIVE_CHECKS_SQL, (chart_id, ay))
        for r in cur.fetchall():
            facts.sensitive_checks[str(r["fact_id"])] = str(r["fact_subject"])
        cur.execute(_FETCH_YOGA_FIRINGS_SQL, (chart_id, ay))
        for r in cur.fetchall():
            facts.yoga_firings[str(r["yoga_canonical_id"])] = [
                str(f) for f in (r["constituent_fact_ids"] or [])
            ]
        cur.execute(_FETCH_FACT_LONGITUDES_SQL, (chart_id, ay))
        for r in cur.fetchall():
            facts.fact_longitudes[str(r["fact_id"])] = float(r["fact_value_num"])
            facts.fact_subjects[str(r["fact_id"])] = str(r["fact_subject"])
    return facts


def _sign_span(sign_num: int) -> tuple[tuple[float, float], str]:
    """Whole-sign span [30*(n-1), 30*n) and the sign name (M-5)."""
    lo = 30.0 * (int(sign_num) - 1)
    return (lo, lo + 30.0), _SIGNS[int(sign_num) - 1]


def _house_sign_num(lagna_sign_num: int, house_n: int) -> int:
    return ((int(lagna_sign_num) - 1) + (int(house_n) - 1)) % 12 + 1


def _base(row: dict) -> dict:
    return {
        "event_class": row["event_class"],
        "target_type": row["target_type"],
        "target_ref": row["target_ref"],
        "qualifier": row.get("target_qualifier"),
        "classical_citation": row.get("classical_citation"),
        "uncited_extension": bool(row.get("uncited_extension")),
        "weight": (None if row.get("weight") is None else float(row["weight"])),
    }


def _graha_point_target(row: dict, facts: ResolutionFacts, graha: str,
                        state: str = "resolved") -> ResolvedTarget:
    """Point target at `graha`'s stored sidereal longitude (§2.2 items 1-2)."""
    subject = resonance_writer._KARAKA_FACT_SUBJECT.get(graha)
    pos = facts.positions.get(subject) if subject else None
    if pos is None or pos.get("longitude") is None:
        state = "unavailable"
    out = ResolvedTarget(
        **_base(row), state=state, kind="point" if state == "resolved" else None,
        owner_graha=graha,
    )
    if state == "resolved":
        out.longitude_deg = float(pos["longitude"])
        out.target_sign = pos.get("sign")
        out.target_fact_id = pos.get("fact_id")
    return out


def _resolve_lord(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    """§2.2 item 3 (R-4): same chain as writer._resolve_lord_ref, then the
    lord graha's stored longitude becomes the point."""
    ref = row["target_ref"]
    lagna = facts.graha_sign_nums.get("LAGNA")
    match = resonance_writer._re.fullmatch(r"(\d+)L", str(ref))
    if not match or lagna is None:
        return ResolvedTarget(**_base(row), state="unavailable")
    house_n = int(match.group(1))
    if not 1 <= house_n <= 12:
        return ResolvedTarget(**_base(row), state="unavailable")
    sign_num = _house_sign_num(lagna, house_n)
    if not facts.sign_lords or sign_num not in facts.sign_lords:
        return ResolvedTarget(**_base(row), state="unqualified")
    return _graha_point_target(row, facts, facts.sign_lords[sign_num])


def _resolve_sensitive_degree(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    """§5.3 row 8: the check row's subject graha's OWN longitude. R-1 already
    removed negative-result rows at the resonance layer, so a stored row
    names a positive check; the subject is recovered through the check
    fact_id (target_ref)."""
    subject = facts.sensitive_checks.get(str(row["target_ref"]))
    graha = _SUBJECT_TO_GRAHA.get(subject or "")
    if graha is None:
        return ResolvedTarget(**_base(row), state="unavailable")
    return _graha_point_target(row, facts, graha)


def _resolve_yoga(row: dict, facts: ResolutionFacts) -> list[ResolvedTarget]:
    """§5.3 row 7 (R-3): one point target per live constituent fact id."""
    constituents = facts.yoga_firings.get(str(row["target_ref"]))
    if not constituents:
        return [ResolvedTarget(**_base(row), state="unavailable")]
    out = []
    for fid in constituents:
        lon = facts.fact_longitudes.get(fid)
        subject = facts.fact_subjects.get(fid)
        graha = _SUBJECT_TO_GRAHA.get(subject or "")
        if lon is None or graha is None:
            out.append(ResolvedTarget(**_base(row), state="unavailable",
                                      target_fact_id=fid))
            continue
        out.append(ResolvedTarget(
            **_base(row), state="resolved", kind="point",
            longitude_deg=float(lon), owner_graha=graha, target_fact_id=fid,
        ))
    return out


def _interval_target(row: dict, facts: ResolutionFacts, sign_num: int | None,
                     state_if_missing: str = "unavailable",
                     agent: str | None = None) -> ResolvedTarget:
    if sign_num is None:
        return ResolvedTarget(**_base(row), state=state_if_missing, agent=agent)
    span, sign_name = _sign_span(sign_num)
    return ResolvedTarget(
        **_base(row), state="resolved", kind="interval", span_deg=span,
        target_sign=sign_name, agent=agent,
    )


def _resolve_bhava(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    lagna = facts.graha_sign_nums.get("LAGNA")
    try:
        house_n = int(row["target_ref"])
    except (TypeError, ValueError):
        house_n = None
    if lagna is None or house_n is None or not 1 <= house_n <= 12:
        return ResolvedTarget(**_base(row), state="unavailable")
    return _interval_target(row, facts, _house_sign_num(lagna, house_n))


def _resolve_arudha(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    """R-2: the sign fact's VALUE names the interval; the sibling cusp
    longitude is never read (F-20)."""
    sign = facts.arudha_signs_by_fact.get(str(row["target_ref"]), "")
    return _interval_target(row, facts, sign_num_of(sign))


def _resolve_bhava_arudha(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    subject = str(row["target_ref"]).replace("BHAVA_ARUDHA_", "ARUDHA_", 1)
    sign = facts.arudha_signs_by_subject.get(subject, "")
    return _interval_target(row, facts, sign_num_of(sign))


def _resolve_mechanism_node(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    match = resonance_writer._re.fullmatch(
        r"([a-z]+):([a-z_]+):h(\d+)", str(row["target_ref"]).strip().lower())
    lagna = facts.graha_sign_nums.get("LAGNA")
    if not match or lagna is None:
        return ResolvedTarget(**_base(row), state="unavailable")
    graha = match.group(1).capitalize()
    agent = graha if graha in resonance_writer._KARAKA_FACT_SUBJECT else None
    return _interval_target(row, facts, _house_sign_num(lagna, int(match.group(3))),
                            agent=agent)


def _m6_operand_sign_num(role: str, facts: ResolutionFacts):
    """Same roles/states as writer._build_m6_derived_rows._operand_sign_num.
    Returns (sign_num|None, state_when_missing)."""
    lagna = facts.graha_sign_nums.get("LAGNA")

    def _house_lord_occupied(house_n: int):
        if lagna is None:
            return None, "unavailable"
        sign_num = _house_sign_num(lagna, house_n)
        if not facts.sign_lords or sign_num not in facts.sign_lords:
            return None, "unqualified"
        subject = resonance_writer._KARAKA_FACT_SUBJECT.get(facts.sign_lords[sign_num])
        occupied = facts.graha_sign_nums.get(subject) if subject else None
        return (int(occupied) if occupied is not None else None), "unavailable"

    if role == "lagna_lord":
        return _house_lord_occupied(1)
    if role == "eighth_lord":
        return _house_lord_occupied(8)
    if role == "yamakantaka":
        return sign_num_of(facts.gulika_mandi_signs.get("YAMAKANTAKA", "")), "unavailable"
    if role == "mandi":
        return sign_num_of(facts.gulika_mandi_signs.get("MANDI", "")), "unavailable"
    if role == "fifth_star_lord":
        if facts.moon_nakshatra_id is None:
            return None, "unavailable"
        lord = fifth_star_lord(facts.moon_nakshatra_id)
        subject = resonance_writer._KARAKA_FACT_SUBJECT.get(lord)
        occupied = facts.graha_sign_nums.get(subject) if subject else None
        return (int(occupied) if occupied is not None else None), "unavailable"
    subject = resonance_writer._KARAKA_FACT_SUBJECT.get(role)
    occupied = facts.graha_sign_nums.get(subject) if subject else None
    return (int(occupied) if occupied is not None else None), "unavailable"


def _m6_state(*operands) -> str:
    missing = [st for sign_num, st in operands if sign_num is None]
    if not missing:
        return "resolved"
    return "unqualified" if "unqualified" in missing else "unavailable"


def _resolve_m6(row: dict, facts: ResolutionFacts) -> ResolvedTarget:
    """§2.2 items 9-10: sign-grain spans; the agent is the formula's ruled
    transit graha (target_qualifier 'agent:X')."""
    qualifier = row.get("target_qualifier") or ""
    agent = qualifier.split(":", 1)[1] if qualifier.startswith("agent:") else None
    ref = str(row["target_ref"])
    if ref == "mandi_sign_distance_from_8L":
        eighth = _m6_operand_sign_num("eighth_lord", facts)
        mandi = _m6_operand_sign_num("mandi", facts)
        state = _m6_state(eighth, mandi)
        if state != "resolved":
            return ResolvedTarget(**_base(row), state=state, agent=agent)
        return _interval_target(
            row, facts,
            mandi_distance_target_sign_num(eighth[0], mandi[0]), agent=agent)
    formula = next((f for f in YAMAKANTAKA_FORMULAS if f["ref"] == ref), None)
    if formula is None:
        return ResolvedTarget(**_base(row), state="unavailable", agent=agent)
    minuend = _m6_operand_sign_num(formula["minuend"], facts)
    subtrahend = _m6_operand_sign_num(formula["subtrahend"], facts)
    state = _m6_state(minuend, subtrahend)
    if state != "resolved":
        return ResolvedTarget(**_base(row), state=state, agent=agent)
    return _interval_target(
        row, facts,
        difference_sign_num(minuend[0], subtrahend[0]), agent=agent)


def resolve_targets(rows: list[dict], facts: ResolutionFacts) -> list[ResolvedTarget]:
    """Re-derive every stored resonance-map row's geometry from L1 facts
    (WP1_CONTRACTS §2.2). States are re-derived honestly; a row the facts
    cannot support keeps an honest unavailable/unqualified, never a guess."""
    out: list[ResolvedTarget] = []
    for row in rows:
        tt = row["target_type"]
        if tt in ("karaka", "dasha_lord_portfolio"):
            out.append(_graha_point_target(row, facts, str(row["target_ref"])))
        elif tt == "lord":
            out.append(_resolve_lord(row, facts))
        elif tt == "sensitive_degree":
            out.append(_resolve_sensitive_degree(row, facts))
        elif tt == "yoga_constituent":
            out.extend(_resolve_yoga(row, facts))
        elif tt == "bhava":
            out.append(_resolve_bhava(row, facts))
        elif tt == "arudha":
            out.append(_resolve_arudha(row, facts))
        elif tt == "bhava_arudha":
            out.append(_resolve_bhava_arudha(row, facts))
        elif tt == "mechanism_node":
            out.append(_resolve_mechanism_node(row, facts))
        elif tt in ("gulika_mandi_distance", "yamakantaka_difference"):
            out.append(_resolve_m6(row, facts))
        else:
            # A target_type this driver was never taught to resolve is an
            # honest null, never a silent skip or a guessed geometry.
            out.append(ResolvedTarget(**_base(row), state="unavailable"))
    return out


# ── enumeration ───────────────────────────────────────────────────────────────


def jd_to_dt(jd: float) -> datetime:
    """JD(UT) -> tz-aware UTC datetime (B1: naive instants are rejected at write)."""
    import swisseph as swe

    y, m, d, h = swe.revjul(jd)
    total_us = int(round(h * 3600.0 * 1e6))
    if total_us >= 86_400_000_000:  # float spill into the next day
        base = datetime(y, m, d, tzinfo=UTC) + timedelta(days=1)
        return base
    hour, rem = divmod(total_us, 3_600_000_000)
    minute, rem = divmod(rem, 60_000_000)
    sec, micro = divmod(rem, 1_000_000)
    return datetime(y, m, d, hour, minute, sec, micro, tzinfo=UTC)


def _episode_to_dict(ep: gk_episodes.Episode, target: ResolvedTarget,
                     backend: dict) -> dict:
    """kernel Episode -> the ledger `_normalize_episode` dict shape
    (precedent: ka_gochara/service.py::_moon_on_demand; step06's synthetic)."""
    truncated = ep.truncated_at_horizon
    if truncated not in ("start", "end"):
        truncated = None  # kernel 'both' -> NULL (WP1 §3.1 CHECK)
    return {
        "independence_group": gk_ids.independence_group(
            body=ep.body, relation=ep.relation, aspect_deg=ep.aspect_deg,
            target_deg=ep.target_deg, t_exact_jd=ep.t_exact, t_fallback_jd=ep.t_in,
        ),
        "body": ep.body,
        "relation": ep.relation,
        "aspect_deg": float(ep.aspect_deg) if ep.relation == "drishti_contact" else 0,
        "target_type": target.target_type,
        "target_ref": target.target_ref,
        "target_fact_id": target.target_fact_id,
        "target_resolution_state": "resolved",
        "target_longitude_deg": (
            target.longitude_deg if target.kind == "point" else None
        ),
        "t_in": jd_to_dt(ep.t_in),
        "t_exact": jd_to_dt(ep.t_exact) if ep.t_exact is not None else None,
        "t_out": jd_to_dt(ep.t_out),
        "bracket_seconds": ep.bracket_seconds,
        "tolerance_arcsec": ep.tolerance_arcsec,
        "truncated_at_horizon": truncated,
        "branch": ep.branch,
        "station_flag": ep.station_flag,
        "exact_crossing": ep.exact_crossing,
        "orb_max_deg": ep.orb_max_deg,
        "orb_source": ep.orb_source,
        "dwell_days": ep.dwell_days,
        "epistemic_class": "observed_event",
        "completeness_state": ep.completeness_state,
        "operator_role": "kernel",
        "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": dict(backend),
        "evidence_fact_ids": [],
        "classical_citation": target.classical_citation,
        "uncited_extension": target.uncited_extension,
        "corpus_verifiable": None,
        # ADK-0020 dedupe bookkeeping; stripped from the payload before write.
        "_map_weight": target.weight,
    }


def enumerate_body(
    index: gk_arcs.ArcIndex,
    body: str,
    targets: list[ResolvedTarget],
    horizon_jd: tuple[float, float],
    orb_deg: float,
    backend: dict,
    ephe_path: str | None = None,
    refine: bool = True,
) -> tuple[list[dict], dict]:
    """Enumerate one body's episodes over the resolved target set.

    Returns (episode_dicts, stats). stats carries episodes_without_exact
    (kernel episodes with t_exact=None are NOT persistable — 1081 t_exact
    NOT NULL — so they are counted and excluded, never fabricated) and the
    searched-relation sets per target_type for coverage."""
    out: list[dict] = []
    stats = {"episodes_without_exact": 0, "searched": {}}

    def _note(target_type: str, relations) -> None:
        stats["searched"].setdefault(target_type, set()).update(relations)

    def _emit(eps, target) -> None:
        for e in eps:
            if e.t_exact is None:
                stats["episodes_without_exact"] += 1
                continue
            out.append(_episode_to_dict(e, target, backend))

    for t in targets:
        if t.state != "resolved":
            continue
        if t.kind == "point":
            lon = float(t.longitude_deg)
            _emit(gk_episodes.solve_episodes(
                index, body, "conjunction", lon, horizon_jd, "orb_conj_slow",
                ephe_path=ephe_path, refine=refine, orb_override_deg=orb_deg), t)
            if gk_convention.drishti_angles(body):  # N-14: nodes cast none
                _emit(gk_episodes.solve_episodes(
                    index, body, "drishti_contact", lon, horizon_jd,
                    "orb_drishti_slow", ephe_path=ephe_path, refine=refine,
                    orb_override_deg=orb_deg), t)
            if t.owner_graha == body:
                # A return is body X reaching body X's natal longitude; for
                # any other body the root set duplicates the conjunction's.
                _emit(gk_episodes.solve_episodes(
                    index, body, "return", lon, horizon_jd, "orb_return_slow",
                    ephe_path=ephe_path, refine=refine), t)
            boundary_searched = []
            for rel in BOUNDARY_RELATIONS:
                boundary_searched.append(rel)
                _emit(gk_episodes.solve_boundary_episodes(
                    index, body, rel, horizon_jd, ephe_path=ephe_path,
                    refine=refine), t)
            relations = ["conjunction", "drishti_contact", *boundary_searched]
            if t.owner_graha == body:
                relations.append("return")
            _note(t.target_type, relations)
        elif t.kind == "interval":
            if t.agent is not None and t.agent != body:
                continue  # mechanism_node / M-6: the named transit agent only
            spans = gk_episodes.residence_spans(
                index, body, t.span_deg, horizon_jd, t.target_type,
                ephe_path=ephe_path, refine=refine)
            for span in spans:
                _emit([span.ingress_episode], t)
            _note(t.target_type, ["sign_ingress"])
    out.sort(key=lambda d: (d["t_in"], d["body"], d["relation"]))
    stats["searched"] = {k: sorted(v) for k, v in stats["searched"].items()}
    return out, stats


# ── ADK-0020 dedupe: one ledger row per physical contact (WP1 §3.3 H-6) ──────


class DedupeRefusal(Exception):
    """A duplicate group the ruled survival rule cannot decide honestly —
    divergence in a field BEYOND target_ref (handled by the survival rule)
    and classical_citation (ADK-0021 option (A): the surviving row's citation
    follows, with disclosure). Refuse and escalate; no merge rule is invented
    (ADK-0020 §N.7; ADK-0021 narrows, never removes, this refusal)."""


# Fields the survival rule legitimately resolves (selection inputs/outputs);
# every OTHER payload field must be identical inside a duplicate group or the
# run refuses. _map_weight is the selection input itself.
_SURVIVAL_FIELDS = frozenset({"target_ref", "classical_citation", "_map_weight"})


def _contact_id_of(ep: dict, chart_id: str, convention_id: str,
                   method_version: str) -> str:
    """The pinned WP1 §3.2 id, exactly as the ledger will compute it."""
    t_exact = ep["t_exact"]
    t_exact_jd = t_exact.timestamp() / 86400.0 + 2440587.5
    return gk_ids.contact_id(
        chart_id=chart_id, convention_id=convention_id,
        body=ep["body"], target_type=ep["target_type"],
        relation=ep["relation"],
        aspect_deg=float(ep.get("aspect_deg") or 0.0),
        t_exact_jd=t_exact_jd,
        target_fact_id=ep.get("target_fact_id"),
        target_ref=ep.get("target_ref"),
        method_version=method_version,
    )


def dedupe_episodes(
    episodes: list[dict],
    *,
    chart_id: str,
    convention_id: str,
    method_version: str,
    dropped_refs_path: str | None = None,
) -> tuple[list[dict], dict]:
    """ADK-0020 option (i): the driver emits per (map row × level); the pinned
    §3.2 contact_id identities per PHYSICAL contact and H-6 says one physical
    contact counts ONCE. Dedupe the payload, keyed by the pinned contact_id,
    before it is written.

    Survival rule (deterministic, disclosed): the row from the highest-weight
    map row wins; weight ties break to the lexicographically smallest
    target_ref; a tie beyond that (same weight AND same target_ref) is a map
    defect — surfaced in the report, never silently resolved. Citations
    (ADK-0021 option (A)): classical_citation follows the surviving
    weight-selected map row — it is that row's event-class provenance, not a
    synthesis of the duplicate group; groups with divergent non-null
    citations are counted and disclosed, and dropped citations are
    recoverable in the dropped-refs artifact keyed by contact_id. Divergence
    in any OTHER field refuses the whole run (DedupeRefusal, exit 5) — the
    ADK-0020 refusal's residual domain. Dropped target_refs are recoverable
    via the dropped-refs artifact keyed by contact_id (dropped_refs_path).
    """
    groups: dict[str, list[dict]] = {}
    for ep in episodes:
        cid = _contact_id_of(ep, chart_id, convention_id, method_version)
        groups.setdefault(cid, []).append(ep)

    # Residual refusal: divergence beyond target_ref / classical_citation.
    divergent: list[dict] = []
    for cid, group in groups.items():
        if len(group) < 2:
            continue
        by_field: dict[str, set] = {}
        all_keys = set().union(*(e.keys() for e in group)) - _SURVIVAL_FIELDS
        for e in group:
            for k in all_keys:
                # missing-vs-present is divergence too
                by_field.setdefault(k, set()).add(
                    json.dumps(e.get(k), sort_keys=True, default=str)
                    if k in e else "<ABSENT>")
        bad = sorted(k for k, vals in by_field.items() if len(vals) > 1)
        if bad:
            divergent.append({
                "contact_id": cid,
                "relation": group[0]["relation"],
                "target_refs": sorted({str(e["target_ref"]) for e in group}),
                "divergent_fields": bad,
            })
    if divergent:
        raise DedupeRefusal(
            f"{len(divergent)} duplicate group(s) diverge beyond target_ref / "
            f"classical_citation — ADK-0020/ADK-0021 invent no merge rule for "
            f"other fields: {json.dumps(divergent[:5], default=str)}"
        )

    divergent_citation_groups = 0

    survivors: list[dict] = []
    per_relation: dict[str, int] = {}
    per_tier = {"weight": 0, "weight_tie_lexicographic": 0, "deeper_tie": 0}
    deeper_tie_groups: list[dict] = []
    multi_ig = 0
    dropped_refs: dict[str, dict] = {}
    dropped_total = 0

    for cid, group in groups.items():
        if len(group) == 1:
            survivors.append(group[0])
            continue
        if len({e["independence_group"] for e in group}) > 1:
            multi_ig += 1
        # tier 1: highest map-row weight (None sorts below every number)
        def _w(e: dict) -> float:
            w = e.get("_map_weight")
            return float("-inf") if w is None else float(w)
        top_w = max(_w(e) for e in group)
        top = [e for e in group if _w(e) == top_w]
        if len(top) == 1:
            survivor, tier = top[0], "weight"
        else:
            # tier 2: lexicographically smallest target_ref
            top.sort(key=lambda e: str(e["target_ref"]))
            min_ref = str(top[0]["target_ref"])
            tied = [e for e in top if str(e["target_ref"]) == min_ref]
            if len(tied) == 1:
                survivor, tier = top[0], "weight_tie_lexicographic"
            else:
                # deeper tie: same weight AND same ref — a map defect;
                # deterministic pick, surfaced in the report
                tied.sort(key=lambda e: json.dumps(e, sort_keys=True, default=str))
                survivor, tier = tied[0], "deeper_tie"
                deeper_tie_groups.append({
                    "contact_id": cid,
                    "relation": survivor["relation"],
                    "target_ref": survivor["target_ref"],
                    "weight": None if top_w == float("-inf") else top_w,
                    "rows": len(tied),
                })
        per_tier[tier] += 1
        dropped = [e for e in group if e is not survivor]
        dropped_total += len(dropped)
        rel = survivor["relation"]
        per_relation[rel] = per_relation.get(rel, 0) + len(dropped)
        citations = {str(e["classical_citation"])
                     for e in group if e.get("classical_citation")}
        if len(citations) > 1:
            divergent_citation_groups += 1
        refs = sorted({str(e["target_ref"]) for e in dropped})
        if refs:
            dropped_refs[cid] = {
                "survivor_target_ref": str(survivor["target_ref"]),
                "survivor_citation": survivor.get("classical_citation"),
                "dropped_target_refs": refs,
                "dropped_citations": sorted(
                    {str(e["classical_citation"]) for e in dropped
                     if e.get("classical_citation")}),
                "dropped_rows": len(dropped),
            }
        survivors.append(survivor)

    for ep in survivors:
        ep.pop("_map_weight", None)
    survivors.sort(key=lambda d: (d["t_in"], d["body"], d["relation"]))

    artifact = None
    if dropped_refs and dropped_refs_path:
        Path(dropped_refs_path).write_text(
            json.dumps(dropped_refs, indent=2, default=str) + "\n")
        artifact = dropped_refs_path

    report = {
        "rule": "ADK-0020 option (i): pinned WP1 §3.2 contact_id; highest-weight "
                "map row survives; weight ties -> lexicographically smallest "
                "target_ref; deeper weight ties surfaced as map defects; "
                "divergence beyond target_ref/classical_citation refuses "
                "(residual ADK-0020 domain)",
        "citation_rule": (
            "ADK-0021 option (A): classical_citation follows the surviving "
            "weight-selected map row; it is that row's event-class provenance, "
            "not a synthesis of the duplicate group; "
            f"{divergent_citation_groups} groups had divergent non-null "
            "citations; dropped citations are recoverable in "
            ".dropped_refs.json keyed by contact_id"),
        "groups_with_divergent_citations": divergent_citation_groups,
        "episodes_before": len(episodes),
        "episodes_after": len(survivors),
        "rows_dropped": dropped_total,
        "duplicate_groups": sum(1 for g in groups.values() if len(g) > 1),
        "per_relation_dropped": dict(sorted(per_relation.items())),
        "per_survival_tier": per_tier,
        "deeper_tie_groups": deeper_tie_groups,
        "groups_with_multiple_independence_groups": multi_ig,
        "dropped_refs_artifact": artifact,
        "dropped_refs_contacts": len(dropped_refs),
    }
    return survivors, report


def build_body_index(body: str, start: date, end: date,
                     ephe_path: str | None) -> tuple:
    """kernel knots + arc index for one body over [start, end] (the caller
    pads the horizon by a day on each side). Returns (index, backend)."""
    ks = gk_knots.sample_knots(body, start, end, ephe_path=ephe_path)
    tol = gk_convention.declared_tolerance(body, "conjunction")["tolerance_arcsec"]
    index = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg,
                                    tolerance_arcsec=tol)
    return index, ks.ephemeris_backend


def build_coverage_rows(chart_id: str, generation: str,
                        targets: list[ResolvedTarget],
                        searched: dict[str, dict[str, list[str]]],
                        horizon_text: str, convention_id: str,
                        backend: dict) -> list[dict]:
    """One coverage partition per (body, target_type) actually searched —
    kernel build_coverage enforces the WP1 §4 invariants; the emitted dict is
    the ledger write_coverage shape (full state counts incl. resolved)."""
    by_type: dict[str, list[ResolvedTarget]] = {}
    for t in targets:
        by_type.setdefault(t.target_type, []).append(t)
    rows: list[dict] = []
    for body, type_relations in searched.items():
        tol = gk_convention.declared_tolerance(body, "conjunction")["tolerance_arcsec"]
        for target_type, relations in sorted(type_relations.items()):
            pool = by_type.get(target_type, [])
            if target_type in INTERVAL_TARGET_TYPES:
                pool = [t for t in pool if t.agent is None or t.agent == body]
            states: dict[str, int] = {}
            for t in pool:
                states[t.state] = states.get(t.state, 0) + 1
            rec = gk_coverage.build_coverage(
                chart_id, generation, "body_target",
                f"{body.lower()}:{target_type}",
                (0.0, 0.0), (0.0, 0.0),  # horizon carried as text below
                tol, tuple(relations), states,
                convention_id=convention_id, ephemeris_backend=backend,
            )
            rows.append({
                "partition_kind": rec.partition_kind,
                "partition_key": rec.partition_key,
                "requested_horizon": horizon_text,
                "completed_horizon": horizon_text,
                "resolution": rec.resolution_arcsec,
                "relations_searched": list(rec.relations_searched),
                "targets_requested": rec.targets_requested,
                "target_resolution_state_counts": {
                    "resolved": rec.targets_resolved,
                    **rec.target_resolution_state_counts,
                },
                "unavailable_inputs": rec.unavailable_inputs,
                "unsearched_reason": rec.unsearched_reason,
            })
    rows.sort(key=lambda r: r["partition_key"])
    return rows


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = step_parser(6, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    parser.add_argument("--horizon-start", default="2020-01-01T00:00:00+00:00")
    parser.add_argument("--horizon-end", default="2030-01-01T00:00:00+00:00")
    parser.add_argument("--orb-deg", type=float, default=5.0,
                        help="M-1 ratified candidate-1 enumeration orb "
                             "(linear_no_box × 5.0°, brief §12.2) for "
                             "conjunction/drishti; returns keep the §7 table value")
    parser.add_argument("--ephe-path", default=str(SIDECAR.parent.parent / ".run" / "se1"))
    parser.add_argument("--no-refine", action="store_true",
                        help="keep spline-stage instants (synthetic-curve use "
                             "only — never for a real enumeration)")
    parser.add_argument("--episodes-out", required=True)
    parser.add_argument("--coverage-out", required=True)
    args = parser.parse_args(argv)

    import swisseph as swe

    h_start = datetime.fromisoformat(args.horizon_start)
    h_end = datetime.fromisoformat(args.horizon_end)
    if h_start.tzinfo is None or h_end.tzinfo is None:
        print("ERROR: horizon bounds must be tz-aware (B1)", file=sys.stderr)
        return 3
    if h_end <= h_start:
        print("ERROR: horizon end must be after start", file=sys.stderr)
        return 3

    def _jd(dt: datetime) -> float:
        utc = dt.astimezone(UTC)
        return float(swe.julday(utc.year, utc.month, utc.day,
                                utc.hour + utc.minute / 60.0
                                + (utc.second + utc.microsecond / 1e6) / 3600.0))

    horizon_jd = (_jd(h_start), _jd(h_end))
    horizon_text = f"[{args.horizon_start},{args.horizon_end})"

    conn = connect(args.dsn, step=6, autocommit=False)
    try:
        # §12.9 gate — BEFORE any enumeration (the same refusal step06 applies
        # at consume time; a candidate must not be built on stale overlay rows).
        from services.ka_vedha_gochara.freshness import (
            check_overlay_freshness, gate_allows_overlays)
        reports = check_overlay_freshness(conn, args.chart_id)
        conn.rollback()  # the checks only read; leave no open transaction
        if not gate_allows_overlays(reports):
            detail = "; ".join(f"{name}: {r.summary()}" for name, r in reports.items())
            print(f"REFUSED (§12.9): {detail}. Enumeration on stale overlay rows "
                  "would build the candidate on unverified citation state — rebuild "
                  "ka_vedha_gochara and ka_moorti_nirnaya first.", file=sys.stderr)
            conn.close()
            return 7
        fingerprints = {
            "house_vedha": reports["house_vedha"].current,
            "moorti": reports["moorti"].current,
        }

        with conn.cursor() as cur:
            cur.execute(_FETCH_MAP_ROWS_SQL, (args.chart_id,))
            map_rows = [
                {
                    "event_class": r[0], "target_type": r[1], "target_ref": r[2],
                    "weight": r[3], "classical_citation": r[4],
                    "uncited_extension": r[5], "target_resolution_state": r[6],
                    "target_qualifier": r[7],
                }
                for r in cur.fetchall()
            ]
        facts = fetch_resolution_facts(conn, args.chart_id)
        conn.rollback()
    finally:
        conn.close()

    if not map_rows:
        print(f"ERROR: no gochara_resonance_map rows for chart {args.chart_id} "
              "— run ka_gochara_resonance first", file=sys.stderr)
        return 3

    targets = resolve_targets(map_rows, facts)
    state_counts: dict[str, int] = {}
    for t in targets:
        state_counts[t.state] = state_counts.get(t.state, 0) + 1

    convention_id = gk_convention.canonical_convention_id()
    start_pad = h_start.date() - timedelta(days=1)
    end_pad = h_end.date() + timedelta(days=1)

    episodes: list[dict] = []
    searched: dict[str, dict[str, list[str]]] = {}
    backends: dict[str, dict] = {}
    no_exact_total = 0
    for body in PERSISTED_BODIES:
        index, backend = build_body_index(body, start_pad, end_pad, args.ephe_path)
        backends[body] = backend
        eps, stats = enumerate_body(
            index, body, targets, horizon_jd, args.orb_deg, backend,
            ephe_path=args.ephe_path, refine=not args.no_refine)
        episodes.extend(eps)
        no_exact_total += stats["episodes_without_exact"]
        searched[body] = stats["searched"]

    coverage = build_coverage_rows(
        args.chart_id, args.generation, targets, searched, horizon_text,
        convention_id, backends.get("Saturn", {}))

    # ADK-0020: dedupe to one row per physical contact BEFORE the payload is
    # written — the ledger keys on the pinned §3.2 contact_id and refuses
    # duplicates at insert (the 2026-09-28 Link 2 halt).
    from step06_candidate_build import CONVENTION_VECTOR
    try:
        episodes, dedupe_report = dedupe_episodes(
            episodes,
            chart_id=args.chart_id,
            convention_id=convention_id,
            method_version=CONVENTION_VECTOR["method_version"],
            dropped_refs_path=args.episodes_out + ".dropped_refs.json",
        )
    except DedupeRefusal as exc:
        print(f"REFUSED (ADK-0020): {exc}", file=sys.stderr)
        return 5

    Path(args.episodes_out).write_text(
        json.dumps(episodes, indent=2, default=str) + "\n")
    Path(args.coverage_out).write_text(
        json.dumps(coverage, indent=2, default=str) + "\n")

    report = {
        "driver": "step06_enumerate_episodes",
        "chart_id": args.chart_id, "generation": args.generation,
        "convention_id": convention_id,
        "horizon": horizon_text,
        "candidate_flags": {**CANDIDATE_FLAGS, "orb_max_deg": args.orb_deg},
        "bodies_enumerated": list(PERSISTED_BODIES),
        "moon_channel": "separate: Moon served on demand with moon_on_demand "
                        "coverage (M-3/R7); never persisted by this driver",
        "resonance_rows": len(map_rows),
        "targets": len(targets),
        "target_resolution_state_counts": state_counts,
        "episodes_emitted": len(episodes),
        "episodes_without_exact_excluded": no_exact_total,
        "dedupe": dedupe_report,
        "coverage_partitions": len(coverage),
        "upstream_fingerprints": fingerprints,
        "ephemeris_backends": backends,
        "refine": not args.no_refine,
        "build_id": f"wp10-step6-enum-{int(time.time())}",
    }
    print(json.dumps(report, indent=2, default=str))
    if args.evidence:
        write_evidence(6, "ENUMERATION",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
