"""Independent re-derivation of what the window sweep stored (A5.3 design v1.6).

`window_store.verify_grain` already recomputes the connected UNION from SQL. This module checks the
SEMANTICS the sweep claims, from the stored rows alone, with its own small evaluator — it imports
nothing from `window_sweep` (the builder) and reads the stored windows, their stored member records
and the factor rows the path is sealed against:

  * which members are qualified/unqualified (per each factor row's own declaration);
  * `score IS NULL` ⇔ no qualified member; the null-state disclosure — `'unqualified'` is in
    `null_states_used` ⇔ some member is unqualified — and therefore the LOWER-BOUND marker
    (`score IS NOT NULL AND 'unqualified' = ANY(null_states_used)`, the only encoding 1156 allows
    without DDL) reproduces from the records;
  * for a window whose qualified members all take a constant value (membership step): score, peak
    (earliest instant of the for-channel max), `evidence_for` / `evidence_against` (per-channel Σ over
    roots of the per-root max at the peak, never netted) and the NULL-ness of the against sum;
  * severity is NULL, `peak ∈ interval`, and an unqualified window carries no peak and no evidence.

A window with a non-constant member (an angular kernel) is checked structurally only and reported as
`numeric_reproduced = False` — never claimed as reproduced.
"""
from __future__ import annotations

from datetime import timezone

_TOL = 1e-6                                 # REAL (float4) storage
_MAGNITUDE_ONLY = ("higher = stronger", "lower = stronger")


def _row_state(row: dict, rec: dict, drishti_bound: bool, vedha_bound: bool):
    """('na',) | ('const', v) | ('fn',) | ('unq', reason) for one factor on one record."""
    fid, ap = row["factor_id"], row.get("applicability")
    if fid == "activity_kernel":
        if not ap:
            return ("unq", "applicability_undeclared")
        span, ang = ap.get("span") or {}, ap.get("angular") or {}
        if rec["kind"] in (span.get("object_kinds") or ()):
            return ("const", float(span["inside"]))
        if rec["kind"] in (ang.get("object_kinds") or ()):
            return ("unq", "orb_not_ratified") if ang.get("orb_deg") is None else ("fn",)
        return ("unq", "object_kind_not_covered_by_applicability")
    if fid == "graduated_drishti":
        if not ap:
            return ("unq", "applicability_undeclared")
        if rec["relation"] not in (ap.get("relations") or ()):
            return ("na",)
        return ("fn",) if drishti_bound else ("unq", "graduated_drishti_source_not_landed")
    if fid == "vedha_attenuation":
        return ("fn",) if vedha_bound else ("unq", "vedha_overlay_not_bound")
    raise RuntimeError(f"window verifier: factor {fid!r} has no verifier derivation")


def _record_state(factor_rows, rec, drishti_bound, vedha_bound):
    states = [_row_state(r, rec, drishti_bound, vedha_bound) for r in factor_rows]
    if any(s[0] == "unq" for s in states):
        return ("unq", sorted({s[1] for s in states if s[0] == "unq"}))
    if any(s[0] == "fn" for s in states):
        return ("fn", None)
    value = 1.0
    for s in states:
        if s[0] == "const":
            value *= s[1]
    return ("const", value)


def _channel(event_class: str, path_id: str, rec: dict) -> str:
    if path_id in ("P3", "P4"):
        return "evidence_for_occurrence"
    if path_id == "P2":
        from services.gochara_rules import admission, favourable_houses
        from services.gochara_rules.score import channel_for
        name, house = rec["agent"].title(), rec["house"]
        fav = house in favourable_houses.favourable_houses(name)
        adv = name in admission.ADVERSE_RESIDENCE_BODIES and house in admission.ADVERSE_RESIDENCE_HOUSES
        if fav == adv:
            raise RuntimeError(f"window verifier: P2 {name} house {house} has no decidable direction")
        return channel_for("favourable" if fav else "adverse", event_class)
    raise RuntimeError(f"window verifier: path {path_id} has no derivation")


def _against_evaluated(path_id: str, factor_rows: list[dict]) -> bool:
    if path_id == "P2":
        return True
    return bool(factor_rows) and all(r.get("direction") in _MAGNITUDE_ONLY for r in factor_rows)


def verify_window_semantics(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                            rule_version: str, factor_rows: list[dict],
                            drishti_bound: bool = False, vedha_bound: bool = False) -> dict:
    grain = (chart_id, generation, event_class, path_id, rule_version)
    windows = conn.execute(
        "SELECT window_id::text, lower(interval), upper(interval), peak_instant, score,"
        " evidence_for, evidence_against, severity, null_states_used"
        " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND path_id = %s AND rule_version = %s ORDER BY 2", grain).fetchall()
    member_rows = conn.execute(
        "SELECT m.window_id::text, r.record_id::text, COALESCE(r.contact_id, r.object_id)::text,"
        " r.relation, r.object_kind, r.agent, r.house_from_frame, lower(s.x), upper(s.x)"
        " FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x)"
        " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s AND m.path_id = %s"
        " AND m.rule_version = %s", grain).fetchall()
    by_window: dict[str, dict[str, dict]] = {}
    for wid, rid, root, rel, kind, agent, house, lo, hi in member_rows:
        rec = by_window.setdefault(wid, {}).setdefault(
            rid, {"root": root, "relation": rel, "kind": kind, "agent": agent, "house": house,
                  "supports": []})
        rec["supports"].append((lo, hi))
    against_ok = _against_evaluated(path_id, factor_rows)
    problems: list[str] = []
    numeric = 0
    for wid, lo, hi, peak, score, ev_for, ev_against, severity, null_states in windows:
        recs = by_window.get(wid, {})
        tag = f"window {lo.astimezone(timezone.utc).isoformat()}"
        states = {rid: _record_state(factor_rows, r, drishti_bound, vedha_bound)
                  for rid, r in recs.items()}
        qualified = {rid: s for rid, s in states.items() if s[0] != "unq"}
        unq = len(recs) - len(qualified)
        null_states = list(null_states or [])
        if severity is not None:
            problems.append(f"{tag}: severity {severity} must be NULL")
        if peak is not None and not (lo <= peak < hi):
            problems.append(f"{tag}: peak {peak} outside [{lo}, {hi})")
        has_fn = any(s[0] == "fn" for s in qualified.values())
        # a non-constant member may turn out undeterminable at evaluation time (the sweep then marks
        # it unqualified), which only the builder can know — so with one, only the one-way check holds
        if (unq and "unqualified" not in null_states) or (
                not has_fn and not unq and "unqualified" in null_states):
            problems.append(f"{tag}: null_states_used {null_states} but {unq} unqualified member(s)")
        if not qualified:
            if (score, peak, ev_for, ev_against) != (None, None, None, None):
                problems.append(f"{tag}: no qualified member yet score/peak/evidence are not NULL")
            continue
        if score is None or ev_for is None:
            problems.append(f"{tag}: {len(qualified)} qualified member(s) but score/evidence_for NULL")
            continue
        if not (0.0 <= score <= 1.0 + _TOL):
            problems.append(f"{tag}: score {score} outside [0,1]")
        if (ev_against is not None) != against_ok:
            problems.append(f"{tag}: evidence_against NULL-ness {ev_against is None} contradicts the "
                            f"registry row (evaluated={against_ok})")
        if has_fn:
            continue                                   # structural only — not claimed as reproduced
        numeric += 1
        chan = {rid: _channel(event_class, path_id, recs[rid]) for rid in qualified}
        fors = [(qualified[rid][1], min(a for a, _ in recs[rid]["supports"]))
                for rid in qualified if chan[rid] == "evidence_for_occurrence"]
        if fors:
            best = max(v for v, _ in fors)
            want_peak = min(t for v, t in fors if v >= best - _TOL)
        else:
            best, want_peak = 0.0, lo
        if abs(score - best) > _TOL:
            problems.append(f"{tag}: score {score} != re-derived {best}")
        if peak != want_peak:
            problems.append(f"{tag}: peak {peak} != re-derived {want_peak}")
        sums = {"evidence_for_occurrence": {}, "evidence_against_occurrence": {}}
        for rid, s in qualified.items():
            if any(a <= want_peak < b for a, b in recs[rid]["supports"]):
                slot = sums[chan[rid]]
                slot[recs[rid]["root"]] = max(slot.get(recs[rid]["root"], 0.0), s[1])
        want_for = sum(sums["evidence_for_occurrence"].values())
        if abs(ev_for - want_for) > _TOL:
            problems.append(f"{tag}: evidence_for {ev_for} != re-derived {want_for}")
        if against_ok and ev_against is not None:
            want_against = sum(sums["evidence_against_occurrence"].values())
            if abs(ev_against - want_against) > _TOL:
                problems.append(f"{tag}: evidence_against {ev_against} != re-derived {want_against}")
    if problems:
        raise RuntimeError(
            f"window semantic verification failed {event_class}/{path_id}: " + "; ".join(problems))
    return {"windows": len(windows), "numeric_reproduced": numeric,
            "structural_only": len(windows) - numeric}


__all__ = ["verify_window_semantics"]
