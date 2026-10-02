"""Independent re-derivation of what the window sweep stored (A5.3 design v1.6).

`window_store.verify_grain` already recomputes the connected UNION from SQL. This module checks the
SEMANTICS the sweep claims, from the stored rows alone, with its own small evaluator — it imports
nothing from `window_sweep` (the builder) and reads the stored windows, their stored member records
and the factor rows the path is sealed against:

  * which members are qualified/unqualified (per each factor row's own declaration);
  * qualification PROPAGATES (Codex round 6, R1): a for-channel (or unknown-channel) unqualified
    member makes the objective unqualified — score, peak and `evidence_for` NULL, nothing partial
    stored; the null-state disclosure (`'unqualified'` in `null_states_used` ⇔ some member is);
  * for a window whose qualified members all take a constant value (membership step): the peak —
    the earliest attained maximum of the NAMED objective (P4: max-min of the agents' activity; other
    paths: Σ over roots of the per-root max for-channel value) solved piecewise between support
    endpoints — then `score`, `evidence_for` / `evidence_against` (per-channel Σ over roots of the
    per-root max at the peak, never netted) and the NULL-ness of the against sum;
  * severity is NULL, `peak ∈ interval`, and an unqualified window carries no peak and no evidence.

A window with a non-constant member (an angular kernel) is checked structurally only and reported as
`numeric_reproduced = False` — never claimed as reproduced.
"""
from __future__ import annotations

from datetime import timezone

_TOL = 1e-6                                 # REAL (float4) storage round-trip — NOT the peak tie
_TIE = 1e-9                                 # the frozen measurement contract's peak-tie tolerance
_MAGNITUDE_ONLY = ("higher = stronger", "lower = stronger")
_TITLE = {"sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury", "jupiter": "Jupiter",
          "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu"}


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
    if fid in ("dignity_of_transit_sign", "combustion", "agent_nature", "maitri_compound"):
        if row.get("value_mapping"):
            raise RuntimeError(f"window verifier: {fid} declares a value_mapping it cannot derive from")
        return ("unq", "value_mapping_undeclared")
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
        name, house = _TITLE[rec["agent"]], rec["house"]
        fav = house in favourable_houses.favourable_houses(name)
        adv = name in admission.ADVERSE_RESIDENCE_BODIES and house in admission.ADVERSE_RESIDENCE_HOUSES
        if fav == adv:
            raise RuntimeError(f"window verifier: P2 {name} house {house} has no decidable direction")
        return channel_for("favourable" if fav else "adverse", event_class)
    raise RuntimeError(f"window verifier: path {path_id} has no channel derivation")


def _against_evaluated(path_id: str, factor_rows: list[dict]) -> bool:
    if path_id == "P2":
        return True
    return bool(factor_rows) and all(r.get("direction") in _MAGNITUDE_ONLY for r in factor_rows)


def earliest_max(cands):
    """(max value, earliest instant within the frozen peak-tie tolerance of it)."""
    best = max(v for v, _ in cands)
    return best, min(t for v, t in cands if v >= best - _TIE)


def _pieces(lo, hi, recs):
    """Elementary pieces of [lo, hi): between consecutive clipped support endpoints."""
    cuts = {lo, hi}
    for r in recs.values():
        for a, b in r["supports"]:
            if a < hi and b > lo:
                cuts.update((max(a, lo), min(b, hi)))
    ordered = sorted(cuts)
    return list(zip(ordered, ordered[1:]))


def _live(recs, t):
    return [rid for rid, r in recs.items() if any(a <= t < b for a, b in r["supports"])]


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
    fully_reproduced = 0            # windows whose stored fields were reproduced EXACTLY (incl. the NULL ones)
    unverified: list[str] = []      # windows with a function-valued member: NOT reproduced (R7 [5])
    for wid, lo, hi, peak, score, ev_for, ev_against, severity, null_states in windows:
        recs = by_window.get(wid, {})
        tag = f"window {lo.astimezone(timezone.utc).isoformat()}"
        states = {rid: _record_state(factor_rows, r, drishti_bound, vedha_bound)
                  for rid, r in recs.items()}
        unq_ids = [rid for rid, s in states.items() if s[0] == "unq"]
        qualified = {rid: s for rid, s in states.items() if s[0] != "unq"}
        null_states = list(null_states or [])
        has_fn = any(s[0] == "fn" for s in qualified.values())
        if severity is not None:
            problems.append(f"{tag}: severity {severity} must be NULL")
        if peak is not None and not (lo <= peak < hi):
            problems.append(f"{tag}: peak {peak} outside [{lo}, {hi})")
        # a non-constant member may turn out undeterminable at evaluation time (the sweep then marks
        # it unqualified), which only the builder can know — so with one, only the one-way check holds
        if (unq_ids and "unqualified" not in null_states) or (
                not has_fn and not unq_ids and "unqualified" in null_states):
            problems.append(f"{tag}: null_states_used {null_states} but {len(unq_ids)} unqualified member(s)")

        def chan(rid, must=False):
            try:
                return _channel(event_class, path_id, recs[rid])
            except RuntimeError:
                if must:
                    raise
                return None                      # unknown channel: affects BOTH
        chans = {rid: chan(rid, must=(rid in qualified)) for rid in recs}
        for_unq = [rid for rid in unq_ids if chans[rid] in ("evidence_for_occurrence", None)]
        against_unq = [rid for rid in unq_ids if chans[rid] in ("evidence_against_occurrence", None)]
        if for_unq:
            # R1: the affected channel is NULL and the objective (which maximises it) is unqualified
            if (score, peak, ev_for, ev_against) != (None, None, None, None):
                problems.append(f"{tag}: a for-channel member is unqualified yet score/peak/evidence "
                                "are not all NULL (a partial subtotal was stored)")
            else:
                fully_reproduced += 1
            continue
        if score is None or ev_for is None or peak is None:
            if not has_fn:
                problems.append(f"{tag}: the objective is qualified but score/peak/evidence_for is NULL")
            else:
                unverified.append(tag)      # NULL only the builder can explain (an unknown piece)
            continue
        if not (0.0 <= score <= 1.0 + _TOL):
            problems.append(f"{tag}: score {score} outside [0,1]")
        if not against_ok and ev_against is not None:
            problems.append(f"{tag}: evidence_against is stored but the registry row declares no way to "
                            "evaluate that channel (expected NULL)")
        # UNIVERSAL BOUNDS (hold for any factor value in [0,1], so they bind even where the numbers cannot be
        # reproduced): evidence is a Σ over roots of a per-root max of values ≤ 1, so it cannot exceed the
        # number of roots feeding the channel; the stored score cannot exceed the evidence at the same peak.
        for_roots = {recs[rid]["root"] for rid in qualified if chans[rid] == "evidence_for_occurrence"}
        against_roots = {recs[rid]["root"] for rid in qualified if chans[rid] == "evidence_against_occurrence"}
        if ev_for < -_TOL or ev_for > len(for_roots) + _TOL:
            problems.append(f"{tag}: evidence_for {ev_for} is outside [0, {len(for_roots)}] — {len(for_roots)} "
                            "root(s) feed the channel and every per-root value is ≤ 1")
        if ev_against is not None and (ev_against < -_TOL or ev_against > len(against_roots) + _TOL):
            problems.append(f"{tag}: evidence_against {ev_against} is outside [0, {len(against_roots)}]")
        if score > ev_for + _TOL:
            problems.append(f"{tag}: score {score} exceeds evidence_for {ev_for} at the same peak")
        if has_fn:
            unverified.append(tag)         # numbers NOT reproduced — an explicit UNVERIFIED state, never a pass
            continue
        numeric += 1
        fully_reproduced += 1
        # ── re-derive the objective piecewise (every live member is a constant here) ────────────
        cands = []
        for a, b in _pieces(lo, hi, recs):
            live = [rid for rid in _live(recs, a) if rid in qualified]
            if path_id == "P4":
                act = {}
                for rid in live:
                    act[recs[rid]["agent"]] = max(act.get(recs[rid]["agent"], 0.0), qualified[rid][1])
                if set(act) == {"jupiter", "saturn"}:
                    cands.append((min(act.values()), a))
            else:
                per_root: dict[str, float] = {}
                for rid in live:
                    if chans[rid] == "evidence_for_occurrence":
                        per_root[recs[rid]["root"]] = max(per_root.get(recs[rid]["root"], 0.0),
                                                          qualified[rid][1])
                cands.append((sum(per_root.values()), a))
        if not cands:
            problems.append(f"{tag}: no objective candidate re-derived")
            continue
        best, want_peak = earliest_max(cands)
        live_at_peak = [rid for rid in _live(recs, want_peak) if rid in qualified]
        # the against channel is the per-instant reduction AT THE PEAK: NULL iff the row cannot evaluate
        # it, or a LIVE unqualified member could feed it (a channel-less one feeds both)
        live_unq_against = [rid for rid in _live(recs, want_peak) if rid in unq_ids
                            and chans[rid] in ("evidence_against_occurrence", None)]
        want_against_null = (not against_ok) or bool(live_unq_against)
        if (ev_against is None) != want_against_null:
            problems.append(f"{tag}: evidence_against NULL-ness {ev_against is None} contradicts the "
                            f"registry row / the members live at the peak (expected NULL={want_against_null})")
        sums = {"evidence_for_occurrence": {}, "evidence_against_occurrence": {}}
        for rid in live_at_peak:
            slot = sums[chans[rid]]
            slot[recs[rid]["root"]] = max(slot.get(recs[rid]["root"], 0.0), qualified[rid][1])
        want_for = sum(sums["evidence_for_occurrence"].values())
        if path_id == "P4":
            want_score = best
        else:
            fors = [qualified[rid][1] for rid in live_at_peak if chans[rid] == "evidence_for_occurrence"]
            want_score = max(fors, default=0.0)
        if abs(score - want_score) > _TOL:
            problems.append(f"{tag}: score {score} != re-derived {want_score}")
        if peak != want_peak:
            problems.append(f"{tag}: peak {peak} != re-derived {want_peak}")
        if abs(ev_for - want_for) > _TOL:
            problems.append(f"{tag}: evidence_for {ev_for} != re-derived {want_for}")
        if not want_against_null and ev_against is not None:
            want_against = sum(sums["evidence_against_occurrence"].values())
            if abs(ev_against - want_against) > _TOL:
                problems.append(f"{tag}: evidence_against {ev_against} != re-derived {want_against}")
    if problems:
        raise RuntimeError(
            f"window semantic verification failed {event_class}/{path_id}: " + "; ".join(problems))
    return {"windows": len(windows), "numeric_reproduced": numeric,
            "fully_reproduced": fully_reproduced, "unverified_dynamic": len(unverified),
            "unverified_windows": unverified,
            # VERIFIED only when EVERY window's stored fields were reproduced exactly; a window with a
            # function-valued member was checked against universal bounds and structure only
            "status": "UNVERIFIED_DYNAMIC" if unverified else "VERIFIED"}


def satisfies_gate(report: dict) -> bool:
    """The window verification can satisfy a gate (PC-5 / a class seal) ONLY when it is fully VERIFIED."""
    return report.get("status") == "VERIFIED" and not report.get("unverified_windows")


_KIND_TARGET = {"sign_span": r"^span:([1-9]|1[0-2])$", "house_span": r"^span:([1-9]|1[0-2])$",
                "star": r"^star:([1-9]|1[0-9]|2[0-7])$", "degree_point": r"^point:", "derived_point": r"^point:",
                "saham": r"^point:", "house_lord": r"^point:"}


def verify_member_support(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                          rule_version: str) -> dict:
    """The members' SUPPORT checked against the SOURCE GEOMETRY (Codex round 7 [5]): for every window
    member, the stored support must equal the contact's own span clipped to its partition's horizon (P1's
    prerequisite-restricted support is `record_verifier`'s), and the physical object's canonical target
    must have the form its object kind requires — the verifier's own table, never trusting the
    record's kind/support declarations."""
    grain = (chart_id, generation, event_class, path_id, rule_version)
    rows = conn.execute(
        "SELECT r.record_id::text, r.object_kind, o.canonical_target,"
        " COALESCE((SELECT range_agg(x) FROM unnest(r.temporal_support_intervals) x), '{}'::tstzmultirange)"
        "   = tstzrange(c.t_in, COALESCE(c.t_out, upper(cov.completed_horizon)), '[)')::tstzmultirange AS eq"
        " FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
        " LEFT JOIN public.ka_gochara_contact c ON (c.chart_id, c.generation, c.contact_id)"
        "                                      = (r.chart_id, r.generation, r.contact_id)"
        " LEFT JOIN public.kala_gochara_coverage cov ON (cov.chart_id, cov.generation, cov.partition_kind,"
        "          cov.partition_key) = (r.chart_id, r.generation, r.coverage_partition_kind, r.coverage_partition_key)"
        " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s AND m.path_id = %s"
        " AND m.rule_version = %s", grain).fetchall()
    import re
    problems = []
    for rid, kind, target, eq in rows:
        pattern = _KIND_TARGET.get(kind)
        if pattern is not None and not re.match(pattern, target):
            problems.append(f"record {rid}: object kind {kind!r} but canonical target {target!r}")
        if path_id != "P1" and eq is not True:
            problems.append(f"record {rid}: stored support is not the contact span clipped to the partition horizon")
    if problems:
        raise RuntimeError(f"member support verification failed {event_class}/{path_id}: " + "; ".join(problems))
    return {"members": len(rows)}


def reconstruct_qualification(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                              rule_version: str, factor_rows: list[dict],
                              drishti_bound: bool = False, vedha_bound: bool = False) -> dict:
    """{window_id: {affected_channels, reasons: {record_id: [reason...]}}} — the qualification a window
    carries, RECONSTRUCTED from its stored members and the bound factor rows (1156 has no column for it;
    persistence is not required, reconstruction is). Serving reads this; a channel is affected when an
    unqualified member feeds it (a channel-less one feeds both)."""
    grain = (chart_id, generation, event_class, path_id, rule_version)
    rows = conn.execute(
        "SELECT m.window_id::text, r.record_id::text, r.relation, r.object_kind, r.agent, r.house_from_frame"
        " FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s AND m.path_id = %s"
        " AND m.rule_version = %s ORDER BY 1, 2", grain).fetchall()
    out: dict[str, dict] = {}
    for wid, rid, rel, kind, agent, house in rows:
        rec = {"relation": rel, "kind": kind, "agent": agent, "house": house}
        slot = out.setdefault(wid, {"affected_channels": set(), "reasons": {}})
        state = _record_state(factor_rows, rec, drishti_bound, vedha_bound)
        if state[0] != "unq":
            continue
        slot["reasons"][rid] = list(state[1])
        try:
            slot["affected_channels"].add(_channel(event_class, path_id, rec))
        except RuntimeError:                        # channel unknown: it feeds BOTH
            slot["affected_channels"].update(("evidence_for_occurrence", "evidence_against_occurrence"))
    return {wid: {"affected_channels": sorted(v["affected_channels"]), "reasons": v["reasons"]}
            for wid, v in out.items()}


__all__ = ["reconstruct_qualification", "satisfies_gate", "verify_member_support", "verify_window_semantics"]
