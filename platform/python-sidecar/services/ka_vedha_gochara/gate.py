"""The §5 vedha interval GATE — the one evaluator of the ka_vedha_gochara
writer's T0-8 payload (GOCHARA_DESIGN_SPECS_v1_4 §5; FABLE #16/#17/#25, N4;
D-PG353; ASTRA_REVIEW_A5_4 v1.1 P1-3).

Consumed by every scoring path that reads kala_vedha_gochara rows: the '4.0'
projection (scripts/kala_gochara_cutover/step06b_windows_projection.py) and
the shared v3 evaluator (services/gochara_v3/engine.py, the
ka_gochara_v3_century_materialize path). Both delegate here so the semantics
cannot drift:

  * attenuation only where an ACTIVE segment covers the instant (half-open;
    cancelled_vipareeta / inactive segments never attenuate — #17, O-VI-1/2/4);
  * coverage is the UNION OF EACH ROW'S computed horizon — an instant in a
    gap between two horizons is `unavailable` (never a clean 1.0; #25,
    O-VI-5); no T0-8 rows at all ⇒ `unavailable`;
  * one physical root attenuates once (independence_group; §5.1), min per
    root across rows, product per primary graha;
  * NO generalised PG353 number (D-PG353): an active obstruction is
    `obstructed` structure with factor None unless a CITED scale is
    supplied; the factor's null_state is `omit` (§2.1) — the λ product is
    unchanged and the state, fired intervals, primary-contact identity and
    rule identity are disclosed;
  * scoped to the PRIMARY transit: a row for graha G in its residence
    [window_start, window_end) qualifies G's own contacts inside that
    residence, never the class λ (§5.2 inv 1) — `factor_by_body` plus the
    fired entries' `primary_contact`;
  * Moon-primary rows are P6 testimony (S-04): never a factor; annotations
    for day rows only (the caller filters by tier);
  * `latta` / `sarvatobhadra` rows carry no interval relations and no cited
    suppression scale — reported as annotations when their window covers
    the date, never a factor;
  * pre-T0-8 house_vedha rows (no detail.vedha_intervals) are counted and
    ignored — never the retired PG353 multiplier.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from services.ka_vedha_gochara import logic as VL

GATE_CONTRACT = "vedha_interval_relation (GOCHARA_DESIGN_SPECS_v1_4 §5)"
NULL_STATE = "omit"  # §2.1 factor null_state for an unresolved qualifier
ANNOTATION_KINDS = frozenset({"latta", "sarvatobhadra"})


def _date_or_none(v):
    if v is None:
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


def _get(row: Any, key: str, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def parse_overlay_rows(vedha_rows: list) -> dict:
    """The overlay rows (dicts or VedhaRow-like objects) as the gate
    consumes them. Returns {"rows": [T0-8 house_vedha rows], "annotations":
    [latta/sarvatobhadra rows], "horizons": [(start, end)], "legacy_rows": n,
    "rows_total": n}."""
    rows, annotations, horizons = [], [], []
    legacy = 0
    for r in vedha_rows:
        d = _get(r, "detail") or {}
        if not isinstance(d, dict):
            d = {}
        kind = _get(r, "vedha_kind")
        ws, we = _get(r, "window_start"), _get(r, "window_end")
        identity = {
            "graha": _get(r, "graha"), "vedha_kind": kind,
            "window_start": str(ws), "window_end": str(we),
            "classical_citation": _get(r, "classical_citation"),
            "formula_version": _get(r, "formula_version"),
            "operator_role": d.get("operator_role"),
            "provenance": d.get("provenance"), "ruling_ref": d.get("ruling_ref"),
        }
        if kind in ANNOTATION_KINDS:
            annotations.append({**identity,
                                "window": (_date_or_none(ws), _date_or_none(we)),
                                "detail": d})
            continue
        intervals = d.get("vedha_intervals")
        cov = d.get("coverage") or {}
        if intervals is None or not cov.get("horizon_start") or not cov.get("horizon_end"):
            legacy += 1
            continue
        c_start, c_end = _date_or_none(cov["horizon_start"]), _date_or_none(cov["horizon_end"])
        horizons.append((c_start, c_end))
        parsed_ivs = []
        for iv in intervals:
            parsed_ivs.append({
                "obstructor_body": iv.get("obstructor_body"),
                "t_in": _date_or_none(iv.get("t_in")),
                "t_out": _date_or_none(iv.get("t_out")),
                "state": iv.get("state"),
                "exception": iv.get("exception"),
                "independence_group": iv.get("independence_group"),
                "segments": [{"start": _date_or_none(sg.get("start")),
                              "end": _date_or_none(sg.get("end")),
                              "state": sg.get("state")}
                             for sg in (iv.get("segments") or [])],
                "operator_role": iv.get("operator_role"),
                "provenance": iv.get("provenance"),
            })
        rows.append({
            **identity,
            "primary_house": d.get("primary_house"),
            "primary_sign_name": d.get("primary_sign_name"),
            "vedha_house": d.get("vedha_house"), "phala": d.get("phala"),
            "coverage": {"start": c_start, "end": c_end, "state": cov.get("state"),
                         "grain": cov.get("grain")},
            "intervals": parsed_ivs,
        })
    return {"rows": rows, "annotations": annotations, "horizons": horizons,
            "legacy_rows": legacy, "rows_total": len(vedha_rows)}


def _covered(horizons: list[tuple], d: date) -> bool:
    return any(s <= d < e for s, e in horizons)


def make_gate(vedha_rows: list, *, cited_scale=None):
    """gate(d: date) -> the §5 qualifier at d, scoped per primary graha."""
    parsed = parse_overlay_rows(vedha_rows)
    cache: dict[str, dict] = {}

    def gate(d: date) -> dict:
        d = _date_or_none(d)
        key = d.isoformat()
        if key in cache:
            return cache[key]
        base = {"contract": GATE_CONTRACT,
                "evaluator": "services.ka_vedha_gochara.gate (logic.attenuation_at)",
                "date": key, "null_state": NULL_STATE,
                "vedha_rows_total": parsed["rows_total"],
                "legacy_shape_rows_ignored": parsed["legacy_rows"],
                "coverage_horizons": [[s.isoformat(), e.isoformat()]
                                      for s, e in parsed["horizons"]],
                "scale": ("cited" if cited_scale is not None
                          else "none_cited (D-PG353: no generalised PG353 attenuation)")}
        # annotation-only kinds covering the date (never a factor)
        kind_annotations = [
            {k: v for k, v in a.items() if k not in ("window", "detail")}
            | {"note": "no interval relation and no cited suppression scale — annotation only"}
            for a in parsed["annotations"]
            if a["window"][0] is not None and a["window"][1] is not None
            and a["window"][0] <= d <= a["window"][1]]
        if not _covered(parsed["horizons"], d):
            out = {**base, "state": "unavailable", "factor": None,
                   "factor_by_body": {}, "fired": [],
                   "annotations": kind_annotations,
                   "coverage": {"overlay": "kala_vedha_gochara",
                                "computed": bool(parsed["horizons"]),
                                "covers_instant": False},
                   "reason": ("no T0-8 overlay rows" if not parsed["horizons"]
                              else "instant outside every computed horizon (gap)")}
            cache[key] = out
            return out
        fired, annotations = [], list(kind_annotations)
        groups_by_body: dict[str, dict[str, float]] = {}
        for row in parsed["rows"]:
            res = VL.attenuation_at(d, row["intervals"], coverage=row["coverage"],
                                    scale=cited_scale)
            if res["state"] != "obstructed":
                continue
            entry = {
                "primary_graha": row["graha"], "vedha_kind": row["vedha_kind"],
                "primary_contact": {
                    "graha": row["graha"], "primary_house": row["primary_house"],
                    "primary_sign_name": row["primary_sign_name"],
                    "residence": [row["window_start"], row["window_end"]]},
                "rule": {"classical_citation": row["classical_citation"],
                         "formula_version": row["formula_version"],
                         "provenance": row["provenance"],
                         "ruling_ref": row["ruling_ref"],
                         "vedha_house": row["vedha_house"], "phala": row["phala"]},
                "operator_role": row["operator_role"],
                "fired": [{**f, "t_in": f["t_in"].isoformat(),
                           "t_out": f["t_out"].isoformat()} for f in res["fired"]],
                "factor": res["factor"],
            }
            if row["operator_role"] == "testimony":
                entry["note"] = ("P6 Moon-channel vedha — testimony (S-04): "
                                 "annotates day rows only, never weights")
                annotations.append(entry)
                continue
            fired.append(entry)
            if cited_scale is not None:
                by_group = groups_by_body.setdefault(row["graha"], {})
                for iv in row["intervals"]:
                    if iv.get("state") != VL.STATE_ACTIVE:
                        continue
                    if not any(sg["state"] == VL.STATE_ACTIVE
                               and sg["start"] <= d < sg["end"]
                               for sg in iv["segments"]):
                        continue
                    g = iv.get("independence_group") or iv["obstructor_body"]
                    by_group[g] = min(by_group.get(g, 1.0), float(cited_scale(iv)))
        factor_by_body = {}
        for body, groups in groups_by_body.items():
            fac = 1.0
            for v in groups.values():
                fac *= v
            factor_by_body[body] = fac
        out = {**base,
               "state": "obstructed" if fired else "clear",
               "factor": (None if (fired and cited_scale is None)
                          else (min(factor_by_body.values()) if factor_by_body else 1.0)),
               "factor_by_body": factor_by_body,
               "fired": fired, "annotations": annotations,
               "coverage": {"overlay": "kala_vedha_gochara", "computed": True,
                            "covers_instant": True}}
        cache[key] = out
        return out

    return gate


def apply_scoped_factors(sentences: list, factor_by_body: dict[str, float]) -> tuple[list, list]:
    """Scope a cited attenuation to the primary graha's own sentences: for a
    sentence whose transit_planet has a factor, return a COPY with its
    detail['orb_strength'] multiplied (an unorbed sentence takes the
    legacy 0.5 fallback × factor). Returns (sentences, applied)."""
    import dataclasses
    if not factor_by_body:
        return list(sentences), []
    out, applied = [], []
    for s in sentences:
        body = getattr(s, "transit_planet", None)
        f = factor_by_body.get(body)
        if f is None or f == 1.0:
            out.append(s)
            continue
        detail = dict(getattr(s, "detail", {}) or {})
        before = detail.get("orb_strength")
        if before is None:
            od = detail.get("orb_degrees")
            before = (1.0 - min(abs(float(od)) / 5.0, 1.0)) if od is not None else 0.5
        detail["orb_strength"] = float(before) * f
        detail["vedha_scoped_factor"] = f
        out.append(dataclasses.replace(s, detail=detail) if dataclasses.is_dataclass(s)
                   else s)
        applied.append({"transit_planet": body, "target_ref": getattr(s, "target_ref", None),
                        "factor": f, "orb_strength_before": float(before)})
    return out, applied


__all__ = ["GATE_CONTRACT", "NULL_STATE", "ANNOTATION_KINDS", "parse_overlay_rows",
           "make_gate", "apply_scoped_factors"]
