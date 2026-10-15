"""Read-only scoped parihāra evaluation (U1:19–27; U11:36).

Consumes L0-M's explicit targets/predicates, never prose or a key-match verdict.
Sky facts are chart-free, exact-instant Kala sky answers, not natal L1 claims.
Three samples detect changes; they do not attest interval continuity or split it.
The typed L0-M schema/rows/reseal must be accepted before consumer integration.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from math import isfinite
from typing import Any

from brahmagyan.dignity_oracle import classify_dignity
from brahmagyan.l0_formula_constants import CONSTANTS
from ga_writers.ga_condition_writer import SIGN_LORDS, dignity_d1_from_sign, compute_combustion_arc
from ga_writers.ga_vargas_writer import _compute_d9_navamsa
from pyjhora_adapter._names import SIGN_NAMES
from services.gochara_kernel.substrate import JD_UNIX_EPOCH
from services.kala_core.sky.ephemeris import (
    CivilTime, GeoLocation, SkyConvention, ephemeris_at, lagna_at,
    EPHE_FLAGS, EPHE_FLAG_NAMES, LAGNA_FLAGS, LAGNA_FLAG_NAMES,
)

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
EVALUATOR_VERSION = "1"
REFERENCE_LOCATION = {"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330}
# Read the L0 seed shared with its writer; no wrapper-local orb constants.
_COMBUSTION = next(c for c in CONSTANTS if c["constant_id"] == "combustion_orbs")
_METADATA = ("dosha_canonical_id", "scope", "source_citation", "source_chunk_id", "source_verse",
             "conjunction_reading", "tika_extension", "priority_rank", "net_standing", "extraction_context")
_V88 = {"tika_commentary": "muhurta_chintamani_pg0116_c01",
        "mula_reconstructed": "muhurta_chintamani_pg0115_c02"}
# (I) INTERPRETATION NB01-I1: the prepared L0-M contract carries source_verse
# as a positive integer within the cited chunk/context, separate from display
# citation spelling. Source admission/reseal must supply it; never parse prose.
# The commentary chunk also contains vv.89–91, so chunk identity alone is unsafe.


def scopes_for(undertaking: str) -> tuple[str, ...]:
    """Undertaking is deliberately not an event-class alias/inference."""
    return (undertaking, "general") if undertaking in ("marriage", "upanayana") else ("general",)


def load_rules(conn, undertaking: str, dosas_present: list[str]) -> list[dict]:
    """Only parameterized SELECT; missing schema is an error, not an empty set."""
    return list(conn.execute("""
        SELECT id, dosha_canonical_id, scope, source_citation, source_chunk_id, source_verse,
               predicate, conjunction_reading, tika_extension, priority_rank,
               net_standing, extraction_context
          FROM public.bg_parihara_rules
         WHERE scope = ANY(%s) AND dosha_canonical_id = ANY(%s)
         ORDER BY dosha_canonical_id, cancellation_index, id
    """, (list(scopes_for(undertaking)), dosas_present)).fetchall())


def candidate_times(candidate: dict) -> tuple[datetime, datetime, datetime]:
    start, end = (datetime.fromisoformat(candidate[k].replace("Z", "+00:00"))
                  for k in ("start_utc", "end_utc"))
    if any(t.tzinfo is None or t.utcoffset().total_seconds() != 0 for t in (start, end)):
        raise ValueError("candidate times must be aware UTC")
    if end <= start:
        raise ValueError("candidate end must follow start")
    return start, start + (end-start)/2, end


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _valid_sky(result, jd: float, convention: SkyConvention, *, local: bool) -> bool:
    """Coverage alone cannot verify that a backend answered this exact sample."""
    if not result.available or not result.coverage.complete or len(result.values) != 1:
        return False
    a = result.values[0]
    backend = "swiss_houses" if local else "swieph"
    if (a.jd != jd or a.time_scale != "UT" or a.backend != backend
            or result.coverage.backend != backend
            or a.ayanamsha_id != convention.ayanamsha_id or a.node_model != convention.node_model
            or a.convention_id != convention.convention_id
            or result.coverage.convention_id != convention.convention_id
            or result.coverage.requested != (jd, jd) or not isfinite(a.ayanamsha_deg)):
        return False
    if local:
        return (isfinite(a.longitude_deg) and 0 <= a.longitude_deg < 360
                and a.flags == LAGNA_FLAGS and a.flag_names == LAGNA_FLAG_NAMES)
    names = [p.body for p in a.positions]
    return (a.path == "swiss_instant" and a.flags == EPHE_FLAGS and a.flag_names == EPHE_FLAG_NAMES
            and len(names) == len(set(names)) and set(PLANETS) <= set(names)
            and all(isfinite(p.longitude_deg) and 0 <= p.longitude_deg < 360
                    and isfinite(p.speed_deg_per_day) for p in a.positions))


def _sample(t: datetime, location: dict, convention: SkyConvention) -> dict:
    jd = t.timestamp()/86400.0 + JD_UNIX_EPOCH
    geo = GeoLocation(location["lat"], location["lon"])
    civil = CivilTime("UTC", location["tz_offset_minutes"])
    ephe = ephemeris_at(jd, convention, bodies=PLANETS)
    try:
        rising = lagna_at(jd, geo, civil, convention)
    except (RuntimeError, ValueError):
        # Swiss houses may refuse polar geometry. No alternate frame is invented.
        rising = None
    ephe_ok = _valid_sky(ephe, jd, convention, local=False)
    lagna_ok = rising is not None and _valid_sky(rising, jd, convention, local=True)
    if lagna_ok:
        lagna_ok = rising.values[0].location == geo and rising.values[0].civil_time == civil
    coverage = {"at": _iso(t), "jd": jd, "complete": bool(ephe_ok and lagna_ok),
                "ephemeris": asdict(ephe.coverage),
                "lagna": asdict(rising.coverage) if rising is not None else None}
    facts: dict[str, Any] = {"at": _iso(t), "jd": jd, "coverage": coverage}
    if ephe_ok:
        a = ephe.values[0]
        facts["ephemeris"] = {k: v for k, v in asdict(a).items() if k != "positions"}
        facts["positions"] = {p.body: {"longitude_deg": p.longitude_deg,
                                      "speed_deg_per_day": p.speed_deg_per_day} for p in a.positions}
    if lagna_ok:
        facts["lagna"] = asdict(rising.values[0])
    return facts


def _term_value(term: dict, sample: dict) -> tuple[bool | None, str | None, dict]:
    """Strict allowlist: an unrecognized key never silently drops a condition."""
    keys = set(term)
    details: dict = {}
    p = term.get("planet")
    if "role" in keys:
        role = term["role"]
        if role == "dosha_agents" and keys == {"role", "each_any_of"}:
            return None, "dosha_agents_unknown", details
        if role not in ("lagna_lord", "navamsa_lagna_lord") or keys != {"role", "house_from_lagna"}:
            return None, "predicate_not_encoded", details
        if not sample["coverage"]["complete"]:
            return None, "sky_coverage_gap", details
        lon = sample["lagna"]["longitude_deg"]
        sign = int(lon/30) if role == "lagna_lord" else _compute_d9_navamsa(lon)
        p = SIGN_LORDS[SIGN_NAMES[sign]]
        details["resolved_planet"] = p
    elif p not in PLANETS:
        return None, "predicate_not_encoded", details
    if keys == {"planet", "strength"} and term["strength"] == "strong":
        return None, "strength_undefined", details
    if "house_from_lagna" in keys and keys in ({"planet", "house_from_lagna"}, {"role", "house_from_lagna"}):
        houses = term["house_from_lagna"]
        if not isinstance(houses, list) or not houses or any(type(h) is not int or not 1 <= h <= 12 for h in houses):
            return None, "predicate_not_encoded", details
        kind = "house"
    elif keys == {"planet", "vargottama"} and p == "Moon" and term["vargottama"] is True:
        kind = "vargottama"
    elif keys == {"planet", "dignity", "varga"} and term["dignity"] in ("debilitated", "enemy_sign", "combust") and term["varga"] in ("rasi", "navamsa"):
        if term["dignity"] == "combust" and term["varga"] == "navamsa":
            return None, "predicate_not_encoded", details
        kind = "dignity"
    else:
        return None, "predicate_not_encoded", details
    if not sample["coverage"]["complete"]:
        return None, "sky_coverage_gap", details
    lon = sample["positions"][p]["longitude_deg"]
    sign = int(lon/30)
    details.update(planet=p, rasi_sign=SIGN_NAMES[sign])
    if kind == "house":
        house = 1 + (sign-int(sample["lagna"]["longitude_deg"]/30)) % 12
        details["house_from_lagna"] = house
        return house in houses, None, details
    d9 = _compute_d9_navamsa(lon)
    details["navamsa_sign"] = SIGN_NAMES[d9]
    if kind == "vargottama":
        return sign == d9, None, details
    if term["dignity"] == "combust":
        if p == "Sun":
            return False, None, details
        speed = sample["positions"][p]["speed_deg_per_day"]
        orb = _COMBUSTION["value_jsonb"][p]["retrograde" if speed < 0 else "direct"]
        arc = compute_combustion_arc(lon, sample["positions"]["Sun"]["longitude_deg"])
        details.update(arc_deg=arc, orb_deg=orb, orb_source={"constant_id": _COMBUSTION["constant_id"],
                       "citation": _COMBUSTION["citation_or_ratification"]})
        return arc <= orb, None, details
    v_sign = d9 if term["varga"] == "navamsa" else sign
    # D9's degree within sign is the same cyclic 9x longitude convention.
    degree = (lon*9) % 30 if term["varga"] == "navamsa" else lon % 30
    classifier = classify_dignity if term["dignity"] == "debilitated" else dignity_d1_from_sign
    dignity = classifier(p, SIGN_NAMES[v_sign], degree)
    details.update(dignity=dignity, varga=term["varga"])
    return dignity == term["dignity"], None, details


def _predicate(node, samples: list[dict], *, top: bool = True) -> tuple[bool | None, str | None, list]:
    if not isinstance(node, dict) or not node:
        return None, "predicate_not_encoded", []
    node = dict(node)
    if "clause" in node:
        if not top or node.pop("clause") != "sarva_dosha":
            return None, "predicate_not_encoded", []
    if "op" in node:
        if (set(node) != {"op", "terms"} or node["op"] not in ("all_of", "any_of")
                or not isinstance(node["terms"], list) or not node["terms"]):
            return None, "predicate_not_encoded", []
        results = [_predicate(t, samples, top=False) for t in node["terms"]]
        terms = [term for result in results for term in result[2]]
        reasons = [reason for _, reason, _ in results if reason]
        if reasons:
            # Even a fixed OR cannot erase a changing/undefined constituent.
            reason = "predicate_changes_within_candidate" if "predicate_changes_within_candidate" in reasons else reasons[0]
            return None, reason, terms
        values = [v for v, _, _ in results]
        return (all(values) if node["op"] == "all_of" else any(values)), None, terms
    values, reasons, facts = [], [], []
    for sample in samples:
        value, reason, detail = _term_value(node, sample)
        values.append(value)
        reasons.append(reason)
        facts.append(dict(sample, derived=detail))
    term = {"term": node, "observed": [{"at": s["at"], "value": v} for s, v in zip(samples, values)], "facts": facts}
    if True in values and False in values:
        return None, "predicate_changes_within_candidate", [term]
    if any(reasons):
        return None, next(r for r in reasons if r), [term]
    return values[0], None, [term]


def _rule(row: dict, samples: list[dict]) -> dict:
    out = {"rule_id": row["id"], **{k: row.get(k) for k in _METADATA}}
    if not row.get("source_citation") or not row.get("source_chunk_id"):
        return dict(out, result="unassessable", reason="predicate_not_encoded", terms=[])
    if type(row.get("source_verse")) is not int or row["source_verse"] <= 0:
        return dict(out, result="unassessable", reason="source_locator_invalid", terms=[])
    if row.get("net_standing") == "never_cancelled":
        return dict(out, result="does_not_apply", reason="never_cancelled_by_text", terms=[])
    value, reason, terms = _predicate(row.get("predicate"), samples)
    if not all(s["coverage"]["complete"] for s in samples):
        value, reason = None, "sky_coverage_gap"
    return dict(out, result="unassessable" if value is None else "applies" if value else "does_not_apply",
                reason=reason, terms=terms)


def _dosha(dosha: str, rules: list[dict]) -> dict:
    out = {"dosha_canonical_id": dosha, "by_rules": [r["rule_id"] for r in rules]}
    if any(r["reason"] == "never_cancelled_by_text" for r in rules):
        return dict(out, state="residual", reason="never_cancelled_by_text")
    # An unidentified verse could be the conflicting reading. It cannot be
    # bypassed by another applies row; a sourced never-cancelled row still wins.
    if any(r["reason"] == "source_locator_invalid" for r in rules):
        return dict(out, state="cancellation_unassessed", reason="source_locator_invalid")
    readings = [
        r for r in rules
        if r["extraction_context"] in _V88
        and _V88[r["extraction_context"]] == r["source_chunk_id"]
        and r["source_verse"] == 88
    ]
    contexts = {r["extraction_context"] for r in readings}
    if len(contexts) == 2:
        results = {r["result"] for r in readings}
        if "applies" in results and "does_not_apply" in results:
            return dict(out, state="cancellation_unassessed", reason="readings_disagree")
        if "unassessable" in results:
            return dict(out, state="cancellation_unassessed", reason=next(r["reason"] for r in readings if r["result"] == "unassessable"))
    if any(r["result"] == "applies" for r in rules):
        return dict(out, state="cancelled", reason=None)
    if rules and all(r["result"] == "does_not_apply" for r in rules):
        return dict(out, state="residual", reason=None)
    return dict(out, state="cancellation_unassessed", reason=next((r["reason"] for r in rules if r["reason"]), "no_sourced_rule_in_scope"))


def evaluate_candidate(*, candidate: dict, undertaking: str, location: dict,
                       dosas_present: list[str], rules: list[dict], location_basis: str = "caller") -> dict:
    """Project explicit source rules and sky evidence; never write/materialize."""
    if location is None:
        raise ValueError("location_missing")
    if location_basis not in ("caller", "lattice_reference_location"):
        raise ValueError("invalid location_basis")
    if location_basis == "lattice_reference_location" and location != REFERENCE_LOCATION:
        raise ValueError("reference location does not match disclosed lattice origin")
    times = candidate_times(candidate)
    convention = SkyConvention()
    samples = [_sample(t, location, convention) for t in times]
    targets = list(dict.fromkeys(dosas_present))
    selected = [r for r in rules if r["scope"] in scopes_for(undertaking) and r["dosha_canonical_id"] in targets]
    assessed = [_rule(r, samples) for r in selected]
    return {"evaluator_version": EVALUATOR_VERSION, "ayanamsha": "lahiri",
            "house_system": "whole_sign_from_rising_sign", "location": dict(location),
            "location_basis": location_basis, "evaluated_at": dict(zip(("start", "mid", "end"), map(_iso, times))),
            "sky_coverage": {"basis": "start_mid_end_samples", "complete": all(s["coverage"]["complete"] for s in samples),
                             "samples": [s["coverage"] for s in samples]},
            "rules": assessed, "dosas": [_dosha(d, [r for r in assessed if r["dosha_canonical_id"] == d]) for d in targets]}
