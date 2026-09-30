"""routers/yoga_formation_band.py -- NMB-CAND-v1 / NMB-ELIG-v1 serve-time formation band.

Ratified spec: 00_ARCHITECTURE/briefs/nirmana/purna_acceptance/
NEAR_MISS_DOMAIN_PACKET_v1_0.md (OSR-009) as amended by
NEAR_MISS_DOMAIN_PACKET_v1_1.md (OSR-012) and NARROWED by
NEAR_MISS_DOMAIN_PACKET_v1_2.md (OSR-015): `near_miss` is NOT a v1 state. The
dusthana placement gate is not a formation condition in BPHS Ch.41, so the
route serves only present / absent / indeterminate. The producer is a
SERVE-TIME derivation behind this sidecar route. Nothing is persisted; there is no
migration, no registered writer and no writer-digest / layer-pin change. This
module is imported ONLY by `main.py`; no `@register`ed writer imports it, so
every writer's source closure (and therefore every writer digest) is
untouched. `tests/test_yoga_formation_band_route.py` pins that.

For a CLOSED list of six wealth (dhana) yogas the route reports, per
(chart, ayanamsha, served generation), whether the chart satisfies the
formation rule the repository ALREADY ships. It never authors a rule,
tolerance, weight or yoga (packet section 0):

  * "present" is decided only by L1 (`ga_yoga_firings`); this route adds the
    leg-level derivation of NON-firings, with a ledger (B.1, B.3, N.5).
  * Evaluation reuses `ga_yoga_writer.ChartState`, `_lord_of_house`,
    `_house_of_planet`, `_check_house_lord_association` and the real
    `_detect_dhana_yoga_house_lords` detector -- imported, never copied or
    edited.
  * No tolerance: no orb, percentage, one-sided-aspect relaxation or
    `partial_formation_threshold` (which has no authoritative reader).
  * No formation-gap ("near miss") detection is claimed or exposed; the
    response carries `near_miss_capable_candidates: 0` and
    `band_coverage.near_miss: 0` so a consumer can never read a gap finding.
  * The six rows are overlapping candidate STATUSES of one wealth-yoga family,
    not six independent findings (packet v1.2 section 2): see `overlaps`.

Data access (N.5 / N.7 item 2): every `chart_facts` and `ga_yoga_firings`
read is fenced with `build_id = ANY(served_build_ids)` (the caller's validated
UUID list) and every chart_facts selection pins `fact_category` AND `fact_key`
with a total `ORDER BY`. The connection is opened read-only and never
committed. `chart_facts` is read for `graha_position` only: that is the sole
category whose `house_d1` / `sign` keys any registered writer emits
(`ga_positions`); ChartState's legacy `planet_position` / `lagna` /
`ascendant` fallbacks have no producer (CHART_FACTS_SCHEMA.json), so reading
them would only widen the served-generation fence to assets that do not exist.
"""
from __future__ import annotations

import itertools
import json
import logging
import os
import secrets
from typing import Any
from uuid import UUID

import psycopg
import psycopg.rows
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from ga_writers.ga_yoga_writer import (
    DHANA_HOUSE_LORD_HOUSES,
    R6A2_LORD_ASSOCIATION_RELATIONS,
    ChartState,
    _check_house_lord_association,
    _detect_dhana_yoga_house_lords,
    _house_of_planet,
    _lord_of_house,
)

logger = logging.getLogger(__name__)

router = APIRouter()

BAND_VERSION = "NMB-BAND-v1"
CANDIDATE_SET_VERSION = "NMB-CAND-v1"
ELIGIBILITY_RULE_VERSION = "NMB-ELIG-v1"
ENGINE_VERSION = "yoga_formation_band_route_v1"

STATE_PRESENT = "present"
STATE_ABSENT = "absent"
STATE_INDETERMINATE = "indeterminate"
BAND_STATES = (STATE_PRESENT, STATE_ABSENT, STATE_INDETERMINATE)
# Wire-format keys of `band_coverage`: `near_miss` is always 0 (packet v1.2).
COVERAGE_KEYS = ("present", "near_miss", "absent", "indeterminate")
NEAR_MISS_CAPABLE_CANDIDATES = 0

STATEMENT_TIMEOUT_MS = 8000
CONNECT_TIMEOUT_S = 5

OVERLAP_NOTE = (
    "Candidate rows are overlapping statuses of one wealth-yoga family, not independent "
    "findings: dhana_yoga_2_5_9_11 subsumes dhana_yoga_2_11, dhana_yoga_5_9 and "
    "dhana_yoga_9_11, and dhana_yoga_house_lords overlaps all of them. Do not sum the rows "
    "into a yoga count. Formation-gap detection is not claimed."
)

# Source honesty (packet v1.2 section 1). The L0 catalogue cites "BPHS Ch.41" with no verse.
# Only the 5th/9th lord pair is directly in Ch.41 sloka 16; the other pair rules rest on
# general Parashari sambandha (conjunction, exchange, mutual aspect).
DIRECT_CH41_CANDIDATES = ("dhana_yoga_5_9",)
DIRECT_CH41_VERSE = "BPHS Ch.41 sloka 16 (5th and 9th lords)"
GENERAL_BASIS = (
    "general Parashari sambandha (conjunction, exchange, mutual aspect between the lords); "
    "not stated in the Ch.41 text"
)
SOURCE_NOTE = (
    "The catalogue citation 'Ch.41 Dhana Yoga adhyaya' carries no verse. Only the 5th/9th lord "
    "pair is directly in BPHS Ch.41 sloka 16; the 2nd/11th, lagna/2nd, 9th/11th and any-pair "
    "candidates rest on general Parashari sambandha (conjunction, exchange, mutual aspect) and "
    "translator's notes, not on Ch.41 text."
)

GATED_CANDIDATE = "dhana_yoga_house_lords"  # the family detector; evaluator of record = the real L1 detector

# The closed candidate set (packet section 2). Order is the emission order.
CANDIDATE_IDS: tuple[str, ...] = (
    "dhana_yoga_house_lords",
    "dhana_yoga_2_11",
    "dhana_yoga_5_9",
    "dhana_yoga_lagna_2",
    "dhana_yoga_9_11",
    "dhana_yoga_2_5_9_11",
)
SIBLING_IDS: tuple[str, ...] = tuple(c for c in CANDIDATE_IDS if c != GATED_CANDIDATE)

# House pairs per candidate, derived from the shipped tables (no new rule).
# Single-pair siblings come from ga_yoga_writer's R6A2 relation table; the
# gated detector iterates (2, 11) x DHANA_HOUSE_LORD_HOUSES exactly like
# `_detect_dhana_yoga_house_lords`; Maha Dhana is any pair among 2/5/9/11
# (`_check_any_lord_pair_association`).
_SIBLING_RELATION = {
    "dhana_yoga_2_11": "association_of_2nd_and_11th_lords",
    "dhana_yoga_5_9": "association_of_5th_and_9th_lords",
    "dhana_yoga_lagna_2": "association_of_lagna_and_2nd_lords",
    "dhana_yoga_9_11": "association_of_9th_and_11th_lords",
}
_MAHA_DHANA_HOUSES: tuple[int, ...] = (2, 5, 9, 11)

SCOPE = {
    "frame": "D1_rashi",
    "house_system": "whole_sign_from_lagna",
    "chandra_frame": False,
    "surya_frame": False,
    "varga": None,
}

# chart_facts (category, key) pairs this route reads, and the registered L1
# assets that produce them. The consumer fences on exactly this list plus
# `ga_yoga` (source of ga_yoga_firings).
FACT_SOURCE_CATEGORY = "graha_position"
FACT_SOURCE_KEYS = ("house_d1", "sign")
FACT_SOURCE_ASSETS = ("ga_positions",)
FIRING_SOURCE_ASSETS = ("ga_yoga",)


def _gated_pairs() -> list[tuple[int, int]]:
    return [(h1, h2) for h1 in (2, 11) for h2 in DHANA_HOUSE_LORD_HOUSES if h2 != h1]


def candidate_pairs(candidate_id: str) -> list[tuple[int, int]]:
    if candidate_id == GATED_CANDIDATE:
        return _gated_pairs()
    if candidate_id == "dhana_yoga_2_5_9_11":
        return list(itertools.combinations(_MAHA_DHANA_HOUSES, 2))
    return [tuple(R6A2_LORD_ASSOCIATION_RELATIONS[_SIBLING_RELATION[candidate_id]])]  # type: ignore[list-item]


# ── Pure evaluation ──────────────────────────────────────────────────────────

def _lord_inputs(state: ChartState, house: int) -> dict[str, Any]:
    """Resolve the lord of `house` and the two inputs the association test
    needs (placement house, sign). Any missing input makes the pair
    unevaluable -- an honest indeterminate, never a guessed value."""
    lord = _lord_of_house(state, house)
    if not lord:
        return {"lord": None, "house": None, "sign": None, "missing": [f"lord_of_house_{house}"]}
    placed = _house_of_planet(lord, state)
    sign = state.planet_sign.get(lord)
    missing = []
    if placed is None:
        missing.append(f"house_of:{lord}")
    if sign is None:
        missing.append(f"sign_of:{lord}")
    return {"lord": lord, "house": placed, "sign": sign, "missing": missing}


def analyse_pair(state: ChartState, h1: int, h2: int) -> dict[str, Any]:
    """Leg-level analysis of one lord pair.

    Single leg, no tolerance:
      lords_associate -- `_check_house_lord_association` (distinct lords;
                         conjunction / exchange / mutual Parashari aspect)
    The placement of the meeting is recorded for the ledger only; it never
    changes the state (the dusthana gate is not exposed, packet v1.2).
    """
    a = _lord_inputs(state, h1)
    b = _lord_inputs(state, h2)
    out: dict[str, Any] = {
        "houses_ruled": [h1, h2],
        "lords": [a["lord"], b["lord"]],
        "evaluable": True,
        "missing": [],
        "associated": False,
        "association_mode": None,
        "placement_houses": [],
    }
    if a["lord"] is None or b["lord"] is None:
        out["evaluable"] = False
        out["missing"] = sorted(set(a["missing"] + b["missing"]))
        return out
    if a["lord"] == b["lord"]:
        # Same lord for both houses: never associated
        # (`_check_house_lord_association` returns None for l1 == l2). No
        # placement input is needed to know that.
        return out
    missing = sorted(set(a["missing"] + b["missing"]))
    if missing:
        out["evaluable"] = False
        out["missing"] = missing
        return out
    hit = _check_house_lord_association(state, h1, h2)
    if hit:
        out["associated"] = True
        out["association_mode"] = hit["association_mode"]
        out["placement_houses"] = list(hit["placement_houses"])
    return out


def _pair_fact_ids(
    state: ChartState, sign_fact_ids: dict[str, str], house_fact_ids: dict[str, str],
    lagna_fact_id: str | None, pairs: list[tuple[int, int]],
) -> list[str]:
    ids: set[str] = set()
    if lagna_fact_id:
        ids.add(lagna_fact_id)
    for h1, h2 in pairs:
        for h in (h1, h2):
            lord = _lord_of_house(state, h)
            if not lord:
                continue
            for src in (sign_fact_ids, house_fact_ids):
                fid = src.get(lord)
                if fid:
                    ids.add(fid)
    return sorted(ids)


def _decide(
    cid: str, l1_fired: bool, l1_row: dict[str, Any] | None, evaluator_fires: bool,
    analyses: list[dict[str, Any]], *, l1_rows_seen: int,
) -> dict[str, Any]:
    """State machine (packet v1.2). Precedence: present, indeterminate, absent.
    `l1_rows_seen` is the number of ga_yoga_firings rows of the served build (any
    yoga); zero means ga_yoga's output for this build was not observed, so a
    non-firing proves nothing."""
    res: dict[str, Any] = {
        "candidate_id": cid,
        "analyses": analyses,
        "l1_firing_ids": [l1_row["id"]] if l1_row and l1_row.get("id") is not None else [],
        "l1_bhanga_active": (l1_row.get("bhanga_active") if l1_row else None),
        "contradicting_present_siblings": [],
        "disagreement": None,
        "reason": None,
    }
    if l1_fired and evaluator_fires:
        res["state"] = STATE_PRESENT
        res["reason"] = "l1_firing_and_evaluator_agree"
        return res
    disagreement = (
        {"l1_fired": l1_fired, "evaluator_fired": evaluator_fires} if l1_fired != evaluator_fires else None
    )
    unevaluable = [a for a in analyses if not a["evaluable"]]
    if unevaluable:
        # An unevaluable pair makes the evaluator's "no fire" untrustworthy, so
        # missing input is the honest reason even when it also disagrees with L1.
        res["state"] = STATE_INDETERMINATE
        missing = sorted({m for a in unevaluable for m in a["missing"]})
        res["reason"] = "missing_input:" + ",".join(missing)
        res["disagreement"] = disagreement
        return res
    if l1_rows_seen == 0:
        res["state"] = STATE_INDETERMINATE
        res["reason"] = "no_l1_firing_rows_seen"
        res["disagreement"] = disagreement
        return res
    if disagreement:
        res["state"] = STATE_INDETERMINATE
        res["reason"] = "l1_evaluator_disagreement"
        res["disagreement"] = disagreement
        return res
    res["state"] = STATE_ABSENT
    res["reason"] = "no_pair_associated" if not any(a["associated"] for a in analyses) else "no_formation"
    return res


def candidate_overlaps() -> dict[str, list[str]]:
    """Static overlap/subsumption map derived from the candidates' house pairs
    (packet v1.2 section 2). Two candidates overlap when they share an unordered
    house pair; the family detector `dhana_yoga_house_lords` is declared to overlap
    every sibling (it is the any-lord-pair family detector)."""
    keys = {cid: {frozenset(p) for p in candidate_pairs(cid)} for cid in CANDIDATE_IDS}
    out: dict[str, list[str]] = {}
    for cid in CANDIDATE_IDS:
        others = []
        for other in CANDIDATE_IDS:
            if other == cid:
                continue
            if GATED_CANDIDATE in (cid, other) or keys[cid] & keys[other]:
                others.append(other)
        out[cid] = others
    return out


def evaluate_candidates(
    state: ChartState, firings: dict[str, dict[str, Any]], l1_rows_seen: int,
) -> dict[str, dict[str, Any]]:
    """`firings` maps canonical_id -> {"id", "fired", "bhanga_active"} from
    ga_yoga_firings; an absent key means no L1 row for that yoga in the served
    generation. `l1_rows_seen` counts ALL ga_yoga_firings rows of the served build."""
    results: dict[str, dict[str, Any]] = {}

    def l1(cid: str) -> tuple[bool, dict[str, Any] | None]:
        row = firings.get(cid)
        return bool(row and row.get("fired")), row

    for cid in SIBLING_IDS:
        analyses = [analyse_pair(state, h1, h2) for h1, h2 in candidate_pairs(cid)]
        evaluator_fires = any(a["associated"] for a in analyses)
        l1_fired, row = l1(cid)
        results[cid] = _decide(cid, l1_fired, row, evaluator_fires, analyses, l1_rows_seen=l1_rows_seen)

    analyses = [analyse_pair(state, h1, h2) for h1, h2 in candidate_pairs(GATED_CANDIDATE)]
    # The real L1 detector is the evaluator of record for "formation holds".
    evaluator_fires = _detect_dhana_yoga_house_lords(state, {}) is not None
    l1_fired, row = l1(GATED_CANDIDATE)
    results[GATED_CANDIDATE] = _decide(
        GATED_CANDIDATE, l1_fired, row, evaluator_fires, analyses, l1_rows_seen=l1_rows_seen,
    )

    # Record, on every non-present row, the present candidates it overlaps: the rows are
    # overlapping statuses, so a present overlapping row is context, never an independent finding.
    overlaps = candidate_overlaps()
    for cid, res in results.items():
        if res["state"] == STATE_PRESENT:
            continue
        res["contradicting_present_siblings"] = sorted(
            o for o in overlaps[cid] if results[o]["state"] == STATE_PRESENT
        )
    return results


# ── Loading (build-fenced, pinned, total order) ──────────────────────────────

_FACTS_SQL = """
SELECT fact_id::text AS fact_id, fact_category, fact_subject, fact_key,
       fact_value_text, fact_value_num, fact_value_jsonb
  FROM chart_facts
 WHERE chart_id = %s::uuid AND ayanamsha_id = %s
   AND build_id = ANY(%s::uuid[])
   AND fact_category = 'graha_position'
   AND fact_key IN ('house_d1', 'sign')
 ORDER BY fact_subject, fact_key, fact_id::text
"""

_FIRINGS_SQL = """
SELECT id, yoga_canonical_id, fired, bhanga_active
  FROM ga_yoga_firings
 WHERE chart_id = %s::uuid AND ayanamsha_id = %s
   AND build_id = ANY(%s::uuid[])
 ORDER BY yoga_canonical_id, id
"""

_CATALOG_SQL = """
SELECT canonical_id, name_en, formation_text, classical_citations
  FROM brahma_yoga_catalog
 WHERE canonical_id = ANY(%s)
 ORDER BY canonical_id
"""


def _rows(conn: Any, sql: str, params: list) -> list[dict]:
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def _norm_subject(raw: str) -> str:
    low = (raw or "").lower()
    return ChartState._SUBJECT_NORM.get(low, low)


def _fact_value(f: dict) -> Any:
    if f.get("fact_key") == "house_d1":
        num = f.get("fact_value_num")
        return None if num is None else float(num)
    return (f.get("fact_value_text") or "").lower() or None


def _dedupe_facts(facts: list[dict]) -> tuple[list[dict], list[dict]]:
    """Collapse rows of one served generation to one fact per (subject, key).
    Identical values across builds keep the first row in the total order; a
    (subject, key) holding DIFFERENT values is ambiguous and is dropped from the
    evaluation (surfacing as a missing input) and reported, never guessed."""
    grouped: dict[tuple[str, str], list[dict]] = {}
    for f in facts:
        grouped.setdefault((_norm_subject(f.get("fact_subject") or ""), f.get("fact_key") or ""), []).append(f)
    kept: list[dict] = []
    ambiguous: list[dict] = []
    for (subj, key), rows in sorted(grouped.items()):
        values = {json.dumps(_fact_value(r)) for r in rows}
        if len(values) > 1:
            ambiguous.append({"fact_subject": subj, "fact_key": key, "fact_ids": [r["fact_id"] for r in rows]})
            continue
        kept.append(rows[0])
    return kept, ambiguous


def _index_fact_ids(facts: list[dict]) -> tuple[dict[str, str], dict[str, str], str | None]:
    """planet -> sign fact_id, planet -> house_d1 fact_id, lagna sign fact_id.
    Read from the same rows ChartState parses (no extra query, no re-derivation)."""
    sign_ids: dict[str, str] = {}
    house_ids: dict[str, str] = {}
    lagna_id: str | None = None
    for f in facts:
        key = f.get("fact_key") or ""
        subj = _norm_subject(f.get("fact_subject") or "")
        fid = f.get("fact_id")
        if fid is None:
            continue
        if key == "sign" and (f.get("fact_value_text") or ""):
            sign_ids[subj] = str(fid)
            if subj == "lagna":
                lagna_id = str(fid)
        elif key == "house_d1" and f.get("fact_value_num") is not None:
            house_ids[subj] = str(fid)
    return sign_ids, house_ids, lagna_id


def _citations(catalog_row: dict | None) -> list[str]:
    if not catalog_row:
        return []
    raw = catalog_row.get("classical_citations")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            raw = None
    out: list[str] = []
    if isinstance(raw, list):
        for c in raw:
            if not isinstance(c, dict) or not c.get("text_id"):
                continue
            chapter = c.get("chapter")
            out.append(f"{c['text_id']}:{chapter}" if chapter is not None else str(c["text_id"]))
    return out


def _leg_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Ledger of the per-pair association leg. `met` is True/False/None
    (None = unevaluable). There is no second leg (packet v1.2)."""
    return [
        {
            "houses_ruled": a["houses_ruled"], "lords": a["lords"], "leg": "lords_associate",
            "met": a["associated"] if a["evaluable"] else None,
            "association_mode": a["association_mode"],
        }
        for a in result["analyses"]
    ]


def _pair_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "houses_ruled": a["houses_ruled"], "lords": a["lords"], "evaluable": a["evaluable"],
            "missing": a["missing"], "associated": a["associated"],
            "association_mode": a["association_mode"], "placement_houses": a["placement_houses"],
        }
        for a in result["analyses"]
    ]


def _source_basis(cid: str) -> dict[str, Any]:
    direct = cid in DIRECT_CH41_CANDIDATES
    return {
        "directly_in_bphs_ch41": direct,
        "verse": DIRECT_CH41_VERSE if direct else None,
        "basis": ("BPHS Ch.41 sloka 16" if direct else GENERAL_BASIS),
    }


def build_yoga_band(
    conn: Any, chart_id: str, ayanamsha_id: str, served_build_ids: list[str],
) -> dict[str, Any]:
    """Return the six-candidate band for one (chart, ayanamsha, served set).
    Reads only; never commits. Exactly six candidate rows are always returned."""
    build_ids = [str(b) for b in served_build_ids]
    raw_facts = _rows(conn, _FACTS_SQL, [chart_id, ayanamsha_id, build_ids])
    facts, ambiguous = _dedupe_facts(raw_facts)
    state = ChartState(facts)
    sign_ids, house_ids, lagna_id = _index_fact_ids(facts)

    # ALL firing rows of the served build (ga_yoga writes one row per fired yoga): any row proves
    # ga_yoga's output for this build was observed; zero rows proves nothing (`no_l1_firing_rows_seen`).
    firing_rows = _rows(conn, _FIRINGS_SQL, [chart_id, ayanamsha_id, build_ids])
    firings: dict[str, dict[str, Any]] = {}
    for r in firing_rows:
        if str(r["yoga_canonical_id"]) not in CANDIDATE_IDS:
            continue
        # UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id): one row each.
        firings[str(r["yoga_canonical_id"])] = {
            "id": r.get("id"), "fired": bool(r.get("fired")), "bhanga_active": r.get("bhanga_active"),
        }
    catalog = {str(r["canonical_id"]): r for r in _rows(conn, _CATALOG_SQL, [list(CANDIDATE_IDS)])}

    results = evaluate_candidates(state, firings, len(firing_rows))
    overlaps = candidate_overlaps()

    candidates: list[dict[str, Any]] = []
    consumed: set[str] = set()
    for cid in CANDIDATE_IDS:
        result = results[cid]
        if result["reason"] == "l1_evaluator_disagreement":
            logger.warning(
                "[yoga_formation_band] l1_evaluator_disagreement chart=%s aya=%s candidate=%s %s",
                chart_id, ayanamsha_id, cid, result["disagreement"],
            )
        fact_ids = _pair_fact_ids(state, sign_ids, house_ids, lagna_id, candidate_pairs(cid))
        consumed.update(fact_ids)
        cat = catalog.get(cid)
        candidates.append({
            "candidate_id": cid,
            "yoga_name": (cat or {}).get("name_en"),
            "formation_text": (cat or {}).get("formation_text"),
            "classical_citations": _citations(cat),
            "citation_carries_verse": False,
            "source_basis": _source_basis(cid),
            "overlaps": overlaps[cid],
            "state": result["state"],
            "reason": result["reason"],
            "legs": _leg_records(result),
            "pairs": _pair_records(result),
            "l1_firing_ids": result["l1_firing_ids"],
            "l1_bhanga_active": result["l1_bhanga_active"],
            "contradicting_present_siblings": result["contradicting_present_siblings"],
            "disagreement": result["disagreement"],
            "constituent_fact_ids": fact_ids,
            "scope": dict(SCOPE, ayanamsha_id=ayanamsha_id),
        })
    if len(candidates) != len(CANDIDATE_IDS):  # pragma: no cover - structural guard
        raise RuntimeError(f"expected {len(CANDIDATE_IDS)} band candidates, built {len(candidates)}")

    coverage = {k: 0 for k in COVERAGE_KEYS}
    for c in candidates:
        coverage[c["state"]] += 1
    return {
        "band_version": BAND_VERSION,
        "candidate_set_version": CANDIDATE_SET_VERSION,
        "eligibility_rule_version": ELIGIBILITY_RULE_VERSION,
        "engine_version": ENGINE_VERSION,
        "tolerance": "none",
        "near_miss_capable_candidates": NEAR_MISS_CAPABLE_CANDIDATES,
        "band_coverage": coverage,
        "overlap_note": OVERLAP_NOTE,
        "overlaps": overlaps,
        "classical_sources": {
            "catalog_citation_carries_verse": False,
            "directly_in_bphs_ch41_sloka_16": list(DIRECT_CH41_CANDIDATES),
            "note": SOURCE_NOTE,
        },
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "served_build_ids": sorted(build_ids),
        "scope": dict(SCOPE, ayanamsha_id=ayanamsha_id),
        "ledger": {
            "consumed_fact_ids": sorted(consumed),
            "fact_source": {
                "table": "chart_facts", "fact_category": FACT_SOURCE_CATEGORY,
                "fact_keys": list(FACT_SOURCE_KEYS), "producing_assets": list(FACT_SOURCE_ASSETS),
            },
            "firing_source": {"table": "ga_yoga_firings", "producing_assets": list(FIRING_SOURCE_ASSETS)},
            "fact_rows_read": len(raw_facts),
            "ambiguous_facts": ambiguous,
            "l1_firing_rows_seen": len(firing_rows),
            "l1_candidate_firing_rows_seen": len(firings),
            "evaluators": [
                "ChartState", "_lord_of_house", "_house_of_planet",
                "_check_house_lord_association", "_detect_dhana_yoga_house_lords",
            ],
        },
        "candidates": candidates,
    }


# ── HTTP surface ─────────────────────────────────────────────────────────────

class YogaBandRequest(BaseModel):
    chart_id: UUID
    ayanamsha_id: str = Field(pattern=r"^[A-Za-z0-9_\-]{1,64}$")
    served_build_ids: list[UUID] = Field(min_length=1, max_length=64)


def _authenticate(x_api_key: str = Header(default="")) -> None:
    """Fail-closed: this route reads chart data, so an unconfigured server key is
    unavailable, never anonymous (same posture as routers/nirmana_probe.py)."""
    expected = os.environ.get("PYTHON_SIDECAR_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="sidecar credential not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key)
        if val:
            return val
    raise RuntimeError("no database URL configured")


def _connect() -> Any:
    conn = psycopg.connect(
        _db_url(), row_factory=psycopg.rows.dict_row,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}", connect_timeout=CONNECT_TIMEOUT_S,
    )
    conn.read_only = True
    return conn


@router.post("/yoga_formation_band", dependencies=[Depends(_authenticate)])
def yoga_formation_band(req: YogaBandRequest) -> dict[str, Any]:
    try:
        with _connect() as conn:
            return build_yoga_band(
                conn, str(req.chart_id), req.ayanamsha_id, sorted({str(b) for b in req.served_build_ids}),
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("[yoga_formation_band] evaluation failed chart=%s", req.chart_id)
        raise HTTPException(status_code=503, detail="yoga formation band unavailable") from None
