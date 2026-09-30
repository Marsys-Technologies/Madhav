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
from services.gochara_kernel.ids import independence_group as _kernel_independence_group
from services.gochara_kernel.overlays import date_to_jd as _date_to_jd

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
            # A SOURCE-BOUND ledger identity for the primary residence, when
            # the writer carried one (`primary_contact_ledger`: the contacts
            # ledger's independence_group / contact_id / t_exact for this
            # residence). The current writer is date-grain and carries none.
            "ledger_contact": (d.get("primary_contact_ledger")
                               if isinstance(d.get("primary_contact_ledger"), dict) else None),
            "precision_regime": _get(r, "precision_regime") or d.get("precision_regime"),
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
            "primary_sign_idx": d.get("primary_sign_idx"),
            "primary_sign_name": d.get("primary_sign_name"),
            "vedha_house": d.get("vedha_house"), "phala": d.get("phala"),
            "coverage": {"start": c_start, "end": c_end, "state": cov.get("state"),
                         "grain": cov.get("grain")},
            "intervals": parsed_ivs,
        })
    return {"rows": rows, "annotations": annotations, "horizons": horizons,
            "legacy_rows": legacy, "rows_total": len(vedha_rows)}


def primary_contact_identity(row: dict) -> dict:
    """The PRIMARY CONTACT's identity (§6.1; ASTRA v1.2 P1-2, corrected per
    v1.3 amendment 2): TRUTHFUL, never reconstructed.

    The contacts ledger keys a residence by the family's scheme
    (gochara_kernel.ids.independence_group over body, 'residence', the span
    degree and the OBSERVED INGRESS INSTANT, minute-floored). The overlay row
    is date-grain (the writer's precision_regime is `date_grain`): it knows
    the residence's calendar dates, not the ingress instant, so a hash of
    its midnight date is NOT the ledger's identity (the reviewer's probe:
    ledger `sha256:04886a…` vs a midnight reconstruction `sha256:92cbf5…`).

    Therefore: when the writer carried a source-bound ledger identity
    (`detail.primary_contact_ledger`), it is passed through verbatim with
    `identity_resolution: 'ledger'`; otherwise the identity is persisted as
    EXPLICITLY UNRESOLVED — `independence_group` and `ledger_contact_id`
    are None, `identity_resolution: 'unresolved'`, with the reason — and
    only the overlay's own descriptive residence key is carried, labelled
    as such. No occurrence ordinal is built (`occurrence_ordinal: None`)."""
    graha = row.get("graha")
    sign_name = row.get("primary_sign_name")
    convention = f"kala_vedha_gochara:{row.get('formula_version') or 'unversioned'}"
    base = {
        "body": graha, "relation_kind": "residence",
        "canonical_target": f"span:{sign_name}" if sign_name else None,
        "convention_id": convention, "occurrence_ordinal": None,
        "t_in": row.get("window_start"), "t_out": row.get("window_end"),
        # the overlay's OWN descriptive key — explicitly not a ledger identity
        "overlay_residence_key": (
            f"{graha}|residence|span:{sign_name}|{convention}|{row.get('window_start')}"
            if sign_name else None),
        "ordinal_note": "overlay rows carry no occurrence ordinal; none is built",
    }
    ledger = row.get("ledger_contact") or {}
    group = ledger.get("independence_group")
    contact_id = ledger.get("contact_id")
    if group or contact_id:
        return {**base, "identity_resolution": "ledger",
                "independence_group": group, "ledger_contact_id": contact_id,
                "ledger_t_exact": ledger.get("t_exact"),
                "ledger_source": ledger.get("source") or "contacts_ledger"}
    return {**base, "identity_resolution": "unresolved",
            "independence_group": None, "ledger_contact_id": None,
            "ledger_t_exact": None, "ledger_source": None,
            "reason": ("overlay residence is date-grain (precision_regime="
                       f"{row.get('precision_regime') or 'date_grain'}); the contacts ledger keys "
                       "a residence by its observed ingress instant, which the overlay does "
                       "not carry — no reconstructed (midnight-date) identifier is presented "
                       "as the ledger's")}


def rule_identity(row: dict) -> dict:
    """The rule the row restates: citation, formula_version (the writer's
    rule version), provenance/ruling, and the (primary house → vedha house)
    pair the Phaladīpikā table keys on."""
    return {
        "classical_citation": row.get("classical_citation"),
        "formula_version": row.get("formula_version"),
        "provenance": row.get("provenance"), "ruling_ref": row.get("ruling_ref"),
        "primary_house": row.get("primary_house"), "vedha_house": row.get("vedha_house"),
        "phala": row.get("phala"),
        "canonical": (f"{row.get('classical_citation')}|{row.get('formula_version')}|"
                      f"primary_house={row.get('primary_house')}|vedha_house={row.get('vedha_house')}"),
    }


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
                "primary_contact_identity": primary_contact_identity(row),
                "rule": rule_identity(row),
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


def persistable_summary(gate_result: dict) -> dict:
    """The gate result reduced to what a persisted row must carry so the
    three evaluator states (unavailable / clear / obstructed) remain
    distinguishable after serialisation (ASTRA v1.2 P1-2): state, nullable
    factor, null_state, coverage, the fired entries with their primary-
    contact and rule identities, testimony annotations, scoped application,
    ignored legacy rows. Pure JSON-serialisable."""
    fired = []
    for f in gate_result.get("fired") or []:
        fired.append({
            "primary_graha": f.get("primary_graha"), "vedha_kind": f.get("vedha_kind"),
            "primary_contact_identity": f.get("primary_contact_identity"),
            "rule": f.get("rule"), "operator_role": f.get("operator_role"),
            "intervals": f.get("fired"), "factor": f.get("factor"),
        })
    annotations = []
    for a in gate_result.get("annotations") or []:
        entry = {k: a.get(k) for k in (
            "primary_graha", "graha", "vedha_kind", "operator_role",
            "primary_contact", "primary_contact_identity", "rule",
            "window_start", "window_end", "classical_citation", "formula_version", "note")}
        # ASTRA v1.3 amendment 2: testimony keeps its OBSTRUCTION EVIDENCE —
        # the obstructor, the fired interval(s) and the root — so a Saturn
        # Jan–Jun obstruction and a Mars Jan 15–Mar 1 obstruction on the same
        # Moon residence persist as different objects.
        entry["intervals"] = a.get("fired")
        entry["factor"] = a.get("factor")
        annotations.append(entry)
    return {
        "contract": gate_result.get("contract"),
        "state": gate_result.get("state"),
        "factor": gate_result.get("factor"),
        "null_state": gate_result.get("null_state"),
        "factor_by_body": gate_result.get("factor_by_body") or {},
        "coverage": gate_result.get("coverage"),
        "coverage_horizons": gate_result.get("coverage_horizons"),
        "reason": gate_result.get("reason"),
        "scale": gate_result.get("scale"),
        "fired": fired,
        "annotations": annotations,
        "scoped_application": gate_result.get("scoped_application") or [],
        "legacy_shape_rows_ignored": gate_result.get("legacy_shape_rows_ignored"),
        "vedha_rows_total": gate_result.get("vedha_rows_total"),
    }


__all__ = ["GATE_CONTRACT", "NULL_STATE", "ANNOTATION_KINDS", "parse_overlay_rows",
           "make_gate", "apply_scoped_factors", "primary_contact_identity",
           "rule_identity", "persistable_summary"]
