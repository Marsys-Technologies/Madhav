"""routers/yoga_formation_band.py -- NMB-CAND-v1 / NMB-ELIG-v1 serve-time formation band.

Ratified spec: 00_ARCHITECTURE/briefs/nirmana/purna_acceptance/
NEAR_MISS_DOMAIN_PACKET_v1_0.md (OSR-009) as amended by
NEAR_MISS_DOMAIN_PACKET_v1_1.md (OSR-012): the producer is a SERVE-TIME
derivation behind this sidecar route. Nothing is persisted; there is no
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
  * `near_miss` exists ONLY for the gated detector `dhana_yoga_house_lords`:
    at least one lord pair is associated and the dusthana placement gate is
    its sole failing leg. "Association missing" is never a near-miss.

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
    DUSTHANAS,
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
STATE_NEAR_MISS = "near_miss"
STATE_ABSENT = "absent"
STATE_INDETERMINATE = "indeterminate"
BAND_STATES = (STATE_PRESENT, STATE_NEAR_MISS, STATE_ABSENT, STATE_INDETERMINATE)

GATED_CANDIDATE = "dhana_yoga_house_lords"

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

    Legs (both mandatory, no optional legs, no tolerance):
      lords_associate             -- `_check_house_lord_association` (distinct
                                     lords; conjunction / exchange / mutual
                                     Parashari aspect)
      association_not_in_dusthana -- meeting placement houses avoid 6/8/12
                                     (applies only to the gated detector)
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
        "gate_failed": False,
    }
    if a["lord"] is None or b["lord"] is None:
        out["evaluable"] = False
        out["missing"] = sorted(set(a["missing"] + b["missing"]))
        return out
    if a["lord"] == b["lord"]:
        # Same lord for both houses: never associated, never a near-miss
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
        out["gate_failed"] = any(h in DUSTHANAS for h in hit["placement_houses"])
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
    analyses: list[dict[str, Any]], *, near_miss_capable: bool,
) -> dict[str, Any]:
    """State machine per packet section 4. Precedence: present, indeterminate,
    near_miss, absent."""
    res: dict[str, Any] = {
        "candidate_id": cid,
        "analyses": analyses,
        "near_miss_capable": near_miss_capable,
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
    unevaluable = [a for a in analyses if not a["evaluable"]]
    if unevaluable:
        # An unevaluable pair makes the evaluator's "no fire" untrustworthy, so
        # missing input is the honest reason even when it also disagrees with L1.
        res["state"] = STATE_INDETERMINATE
        missing = sorted({m for a in unevaluable for m in a["missing"]})
        res["reason"] = "missing_input:" + ",".join(missing)
        if l1_fired != evaluator_fires:
            res["disagreement"] = {"l1_fired": l1_fired, "evaluator_fired": evaluator_fires}
        return res
    if l1_fired != evaluator_fires:
        res["state"] = STATE_INDETERMINATE
        res["reason"] = "l1_evaluator_disagreement"
        res["disagreement"] = {"l1_fired": l1_fired, "evaluator_fired": evaluator_fires}
        return res
    if near_miss_capable and any(a["associated"] and a["gate_failed"] for a in analyses):
        res["state"] = STATE_NEAR_MISS
        res["reason"] = "gate_only_failure:association_in_dusthana"
        return res
    res["state"] = STATE_ABSENT
    res["reason"] = "no_pair_associated" if not any(a["associated"] for a in analyses) else "no_formation"
    return res


def evaluate_candidates(
    state: ChartState, firings: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """`firings` maps canonical_id -> {"id", "fired", "bhanga_active"} from
    ga_yoga_firings; an absent key means no L1 row in the served generation."""
    results: dict[str, dict[str, Any]] = {}

    def l1(cid: str) -> tuple[bool, dict[str, Any] | None]:
        row = firings.get(cid)
        return bool(row and row.get("fired")), row

    # Siblings first: the gated candidate's contradiction record needs them.
    for cid in SIBLING_IDS:
        analyses = [analyse_pair(state, h1, h2) for h1, h2 in candidate_pairs(cid)]
        evaluator_fires = any(a["associated"] for a in analyses)
        l1_fired, row = l1(cid)
        results[cid] = _decide(cid, l1_fired, row, evaluator_fires, analyses, near_miss_capable=False)

    analyses = [analyse_pair(state, h1, h2) for h1, h2 in candidate_pairs(GATED_CANDIDATE)]
    # The real L1 detector is the evaluator of record for "formation holds".
    evaluator_fires = _detect_dhana_yoga_house_lords(state, {}) is not None
    l1_fired, row = l1(GATED_CANDIDATE)
    gated = _decide(GATED_CANDIDATE, l1_fired, row, evaluator_fires, analyses, near_miss_capable=True)
    if gated["state"] == STATE_NEAR_MISS:
        near_keys = {frozenset(a["houses_ruled"]) for a in analyses if a["associated"] and a["gate_failed"]}
        contradicting = []
        for cid in SIBLING_IDS:
            sib = results[cid]
            if sib["state"] != STATE_PRESENT:
                continue
            sib_keys = {frozenset(a["houses_ruled"]) for a in sib["analyses"] if a["associated"]}
            if sib_keys & near_keys:
                contradicting.append(cid)
        gated["contradicting_present_siblings"] = sorted(contradicting)
    results[GATED_CANDIDATE] = gated
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
   AND yoga_canonical_id = ANY(%s)
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
    """Ledger of the per-pair legs. `met` is True/False/None (None =
    unevaluable, or gate not reached because the association leg failed)."""
    legs: list[dict[str, Any]] = []
    for a in result["analyses"]:
        associated: bool | None = a["associated"] if a["evaluable"] else None
        legs.append({
            "houses_ruled": a["houses_ruled"], "lords": a["lords"], "leg": "lords_associate",
            "met": associated, "association_mode": a["association_mode"],
        })
        if result["near_miss_capable"]:
            legs.append({
                "houses_ruled": a["houses_ruled"], "lords": a["lords"],
                "leg": "association_not_in_dusthana",
                "met": (None if not associated else not a["gate_failed"]),
                "placement_houses": a["placement_houses"],
            })
    return legs


def _pair_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "houses_ruled": a["houses_ruled"], "lords": a["lords"], "evaluable": a["evaluable"],
            "missing": a["missing"], "associated": a["associated"],
            "association_mode": a["association_mode"], "placement_houses": a["placement_houses"],
            "gate_failed": a["gate_failed"],
        }
        for a in result["analyses"]
    ]


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

    firing_rows = _rows(conn, _FIRINGS_SQL, [chart_id, ayanamsha_id, build_ids, list(CANDIDATE_IDS)])
    firings: dict[str, dict[str, Any]] = {}
    for r in firing_rows:
        # UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id): one row each.
        firings[str(r["yoga_canonical_id"])] = {
            "id": r.get("id"), "fired": bool(r.get("fired")), "bhanga_active": r.get("bhanga_active"),
        }
    catalog = {str(r["canonical_id"]): r for r in _rows(conn, _CATALOG_SQL, [list(CANDIDATE_IDS)])}

    results = evaluate_candidates(state, firings)

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
            "near_miss_capable": result["near_miss_capable"],
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

    return {
        "band_version": BAND_VERSION,
        "candidate_set_version": CANDIDATE_SET_VERSION,
        "eligibility_rule_version": ELIGIBILITY_RULE_VERSION,
        "engine_version": ENGINE_VERSION,
        "tolerance": "none",
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
    conn = psycopg.connect(_db_url(), row_factory=psycopg.rows.dict_row)
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
