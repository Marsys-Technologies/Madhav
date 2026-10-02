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

from . import boundary_match as bm

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


#: R8-6: a record with a STATE-valued operand (a dṛṣṭi source, a vedha overlay) is solved piecewise between the
#: instants the operand's state changes, so those instants must be known COMPLETELY — otherwise it is unqualified.
#: The verifier's own statement of what the substrate can supply: a dṛṣṭi record's changes are the body's sign
#: ingresses, complete only where the class's coverage partition completed the whole support; NO source of vedha
#: overlay edges exists, so any record carrying a vedha factor is incomplete. (The builder's SweepRecord asserts the
#: same through `state_boundaries_complete`; these are two derivations.)
_STATE_VALUED = ("graduated_drishti", "vedha_attenuation")
STATE_BOUNDARIES_REASON = "state_boundaries_incomplete"


def _completed_horizon(conn, grain):
    row = conn.execute(
        "SELECT completed_horizon FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s"
        " AND partition_kind = 'event_class' AND partition_key = %s", (grain[0], grain[1], grain[2])).fetchone()
    return None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])


def _boundaries_complete(relation, supports, completed) -> bool:
    if relation != "aspect" or completed is None or not supports:
        return False
    return all(completed.lower <= a and b <= completed.upper for a, b in supports)


def _record_state(factor_rows, rec, drishti_bound, vedha_bound):
    states = [_row_state(r, rec, drishti_bound, vedha_bound) for r in factor_rows]
    if any(s[0] == "unq" for s in states):
        return ("unq", sorted({s[1] for s in states if s[0] == "unq"}))
    state_valued_fn = any(s[0] == "fn" and r["factor_id"] in _STATE_VALUED for s, r in zip(states, factor_rows))
    if state_valued_fn and not rec.get("boundaries_complete"):
        return ("unq", [STATE_BOUNDARIES_REASON])
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


#: the frozen qualification policy this verifier implements (R8-4) — the builder's `window_sweep.draft_windows`
#: documents the same table; the two are separate code and the DB gate binds the version
POLICY_VERSION = "window_qualification/1"
#: R9-1: the OTHER named policy and its reason — this verifier's OWN literals (the builder's live in `result_policy`;
#: a test asserts equality, so drift is visible, never imported). `all_null_candidate/1`: every numerical result
#: field NULL for every path and channel composition, peak absent, valence `unqualified`.
ALL_NULL_POLICY = "all_null_candidate/1"
ALL_NULL_REASON = "all_null_candidate_policy"
POLICIES = (ALL_NULL_POLICY, POLICY_VERSION)


def _manifest_policy(conn, grain) -> str | None:
    """The policy the generation's MANIFEST selected, read by this verifier's own SQL (None = no manifest row)."""
    row = conn.execute(
        "SELECT input_generation_vector ->> 'result_policy' FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (grain[0], grain[1])).fetchone()
    if row is None:
        return None
    value = next(iter(row.values())) if isinstance(row, dict) else row[0]
    if value not in POLICIES:
        raise RuntimeError(f"window verifier: the manifest selects result_policy {value!r}, not one of {POLICIES}")
    return value
#: the named switch (R8-4/R8-6): a window with a qualified function-valued member is unqualified until a solver
#: with a stated global-maximum guarantee exists
DYNAMIC_SWITCH_REASON = "dynamic_objective_solver_guarantee_not_available"
#: every governed stored field of a window this verifier reproduces (VERIFIED requires all of them)
GOVERNED_FIELDS = ("interval", "peak_instant", "score", "evidence_for", "evidence_against",
                   "outcome_valence_for_native", "severity", "null_states_used", "membership",
                   "objective", "objective_value", "qualification")


def _expected_valence(event_class, ev_for, ev_against, reason):
    """The valence the stored evidence implies — Stream B's `valence.compute_valence` (the rule authority) CALLED
    with the verifier's own derived arguments; never the builder's draft."""
    from services.gochara_rules import valence as _v
    return _v.compute_valence(event_class, ev_for, ev_against, reason).outcome_valence_for_native


def verify_window_semantics(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                            rule_version: str, factor_rows: list[dict],
                            drishti_bound: bool = False, vedha_bound: bool = False,
                            dynamic_enabled: bool = False, policy: str | None = None) -> dict:
    grain = (chart_id, generation, event_class, path_id, rule_version)
    # R9-1: the policy is the MANIFEST's. An explicit `policy` is only for a generation without a manifest row (the
    # solver's own fixtures); against a manifest it must agree — it never overrides it.
    manifest_policy = _manifest_policy(conn, grain)
    if policy is None:
        policy = manifest_policy
    elif manifest_policy is not None and policy != manifest_policy:
        raise RuntimeError(f"window verifier: policy {policy!r} != the manifest's {manifest_policy!r}")
    if policy not in POLICIES:
        raise RuntimeError(f"window verifier: no result policy selected (the generation has no manifest row)")
    prov_cols = conn.execute(
        "SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_eval_window'::regclass"
        " AND attname IN ('objective', 'objective_value', 'qualification') AND NOT attisdropped").fetchone()
    has_prov = (next(iter(prov_cols.values())) if isinstance(prov_cols, dict) else prov_cols[0]) == 3
    windows = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
        "SELECT window_id::text, lower(interval), upper(interval), peak_instant, score,"
        " evidence_for, evidence_against, severity, null_states_used, outcome_valence_for_native,"
        + (" objective, objective_value, qualification" if has_prov else " NULL, NULL, NULL") +
        " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND path_id = %s AND rule_version = %s ORDER BY 2", grain).fetchall()]
    # R9-2: the COMPLETE expected membership, derived here from the grain's own records — not read back from the stored
    # links. Every admitted scored record whose support overlaps a window is a member; no other record is; no admitted
    # record with a support sits in no window. The numeric derivation below runs over the EXPECTED members.
    record_rows = conn.execute(
        "SELECT r.record_id::text, COALESCE(r.contact_id, r.object_id)::text,"
        " r.relation, r.object_kind, r.agent, r.house_from_frame, lower(s.x), upper(s.x)"
        " FROM public.ka_gochara_relationship_record r"
        " CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x)"
        " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s AND r.path_id = %s"
        " AND r.rule_version = %s AND r.admission_state = 'admitted' AND r.operator_role = 'scored'", grain).fetchall()
    grain_records: dict[str, dict] = {}
    for rid, root, rel, kind, agent, house, lo, hi in record_rows:
        rec = grain_records.setdefault(rid, {"root": root, "relation": rel, "kind": kind, "agent": agent,
                                             "house": house, "supports": []})
        rec["supports"].append((lo, hi))
    stored_links: dict[str, set] = {}
    for wid, rid in conn.execute(
            "SELECT window_id::text, record_id::text FROM public.ka_gochara_eval_window_record"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s AND rule_version = %s",
            grain).fetchall():
        stored_links.setdefault(wid, set()).add(rid)
    by_window: dict[str, dict[str, dict]] = {}
    membership_problems: list[str] = []
    in_some_window: set[str] = set()
    for (wid, wlo, whi, *_rest) in windows:
        expected_ids = {rid for rid, rec in grain_records.items()
                        if any(a < whi and wlo < b for a, b in rec["supports"])}
        by_window[wid] = {rid: grain_records[rid] for rid in sorted(expected_ids)}
        in_some_window |= expected_ids
        have = stored_links.get(wid, set())
        if have != expected_ids:
            membership_problems.append(
                f"window {wlo.astimezone(timezone.utc).isoformat()}: membership omits {sorted(expected_ids - have)} "
                f"and includes unexpected {sorted(have - expected_ids)}")
    orphans = sorted(rid for rid, rec in grain_records.items() if rec["supports"] and rid not in in_some_window)
    if orphans:
        membership_problems.append(f"admitted scored record(s) {orphans} overlap no stored window")
    for wid in stored_links:
        if wid not in by_window:
            membership_problems.append(f"membership links point at an unknown window {wid}")
    completed = _completed_horizon(conn, grain)
    for recs_ in by_window.values():
        for rec_ in recs_.values():
            rec_["boundaries_complete"] = _boundaries_complete(rec_["relation"], rec_["supports"], completed)
    against_ok = _against_evaluated(path_id, factor_rows)
    problems: list[str] = list(membership_problems)
    numeric = 0
    fully_reproduced = 0            # windows whose stored fields were reproduced EXACTLY (incl. the NULL ones)
    unverified: list[str] = []      # windows with a function-valued member while the solver is enabled
    detail: list[dict] = []         # the lossless qualification provenance, DERIVED here (1156 has no column)

    def expect_null_window(tag, stored, reason):
        """The window must carry no numeric result: NULL score/peak/evidence and the unqualified valence."""
        score, peak, ev_for, ev_against, valence = stored
        if (score, peak, ev_for, ev_against) != (None, None, None, None):
            problems.append(f"{tag}: the objective is unqualified ({reason}) yet score/peak/evidence are not all "
                            "NULL (a partial subtotal was stored)")
            return False
        want = _expected_valence(event_class, 0.0, 0.0, reason)
        if valence != want:
            problems.append(f"{tag}: outcome valence {valence!r} != {want!r} implied by the unqualified window")
            return False
        return True

    def check_provenance(tag, row, qualified_members, s_objective, s_value, s_qual):
        """R8-4 (1240): the PERSISTED objective name / value / qualification provenance must equal what this verifier
        derives from the members and the bound factor rows (never read back and trusted)."""
        if not has_prov:
            return
        if s_objective is None or s_qual is None:
            problems.append(f"{tag}: the window carries no objective/qualification provenance")
            return
        if s_objective != row["objective"]:
            problems.append(f"{tag}: objective {s_objective!r} != re-derived {row['objective']!r}")
        want_v = row["objective_value"]
        if (s_value is None) != (want_v is None) or (s_value is not None and abs(s_value - want_v) > _TOL):
            problems.append(f"{tag}: objective_value {s_value} != re-derived {want_v}")
        want_q = {"policy": policy, "unqualified_reason": row["unqualified_reason"], "unresolved": row["unresolved"],
                  "affected_channels": row["affected_channels"], "members": row["members"],
                  "qualified_members": qualified_members}
        if s_qual != want_q:
            problems.append(f"{tag}: qualification {s_qual} != re-derived {want_q}")

    for (wid, lo, hi, peak, score, ev_for, ev_against, severity, null_states, valence,
         s_objective, s_objective_value, s_qualification) in windows:
        recs = by_window.get(wid, {})
        tag = f"window {lo.astimezone(timezone.utc).isoformat()}"
        states = {rid: _record_state(factor_rows, r, drishti_bound, vedha_bound) for rid, r in recs.items()}
        unq_ids = [rid for rid, s in states.items() if s[0] == "unq"]
        qualified = {rid: s for rid, s in states.items() if s[0] != "unq"}
        null_states = list(null_states or [])
        has_fn = any(s[0] == "fn" for s in qualified.values())
        if severity is not None:
            problems.append(f"{tag}: severity {severity} must be NULL")
        if peak is not None and not (lo <= peak < hi):
            problems.append(f"{tag}: peak {peak} outside [{lo}, {hi})")
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
        reasons: dict[str, int] = {}
        for rid in unq_ids:
            for r in states[rid][1]:
                reasons[r] = reasons.get(r, 0) + 1
        for_unq = [rid for rid in unq_ids if chans[rid] in ("evidence_for_occurrence", None)]
        against_unq = [rid for rid in unq_ids if chans[rid] in ("evidence_against_occurrence", None)]
        affected = sorted({c for rid in unq_ids for c in (
            ("evidence_for_occurrence", "evidence_against_occurrence") if chans[rid] is None else (chans[rid],))})
        row = {"window": lo.astimezone(timezone.utc).isoformat(), "members": len(recs),
               "objective": "max_min_agent_activity" if path_id == "P4" else "evidence_for_per_root_sum",
               "objective_value": None, "unqualified_reason": None, "unresolved": dict(sorted(reasons.items())),
               "affected_channels": affected}
        stored = (score, peak, ev_for, ev_against, valence)

        # ── R9-1: the all-NULL candidate policy — decided before ANY objective is derived ───────────────────
        if policy == ALL_NULL_POLICY:
            row["unqualified_reason"] = ALL_NULL_REASON
            ok_null = expect_null_window(tag, stored, ALL_NULL_REASON)
            if s_objective_value is not None:
                problems.append(f"{tag}: objective_value {s_objective_value} must be NULL under {ALL_NULL_POLICY}")
                ok_null = False
            check_provenance(tag, row, len(qualified), s_objective, s_objective_value, s_qualification)
            if ok_null and severity is None:
                fully_reproduced += 1
            detail.append(row)
            continue

        # ── policy 1: an unqualified member whose channel is `for` or unknown ⇒ everything NULL ────────────
        if for_unq:
            reason = sorted(reasons)[0]
            row["unqualified_reason"] = reason
            ok_null = expect_null_window(tag, stored, reason)
            check_provenance(tag, row, len(qualified), s_objective, s_objective_value, s_qualification)
            if ok_null:
                fully_reproduced += 1
            detail.append(row)
            continue
        # ── policy 2: the dynamic switch ────────────────────────────────────────────────────────────────────
        if has_fn and not dynamic_enabled:
            row["unqualified_reason"] = DYNAMIC_SWITCH_REASON
            row["unresolved"] = {**row["unresolved"], DYNAMIC_SWITCH_REASON: sum(
                1 for s in qualified.values() if s[0] == "fn")}
            ok_null = expect_null_window(tag, stored, DYNAMIC_SWITCH_REASON)
            check_provenance(tag, row, len(qualified), s_objective, s_objective_value, s_qualification)
            if ok_null:
                fully_reproduced += 1
            detail.append(row)
            continue
        if has_fn:                                   # the solver is enabled: numbers NOT reproduced here
            detail.append(row)
            unverified.append(tag)
            # UNIVERSAL BOUNDS (hold for any factor value in [0,1], so they bind where numbers cannot be
            # reproduced): evidence is a Σ over roots of a per-root max of values ≤ 1; the score is a unit value
            if score is not None and not (0.0 <= score <= 1.0 + _TOL):
                problems.append(f"{tag}: score {score} outside [0,1]")
            for_roots = {recs[rid]["root"] for rid in qualified if chans[rid] == "evidence_for_occurrence"}
            against_roots = {recs[rid]["root"] for rid in qualified if chans[rid] == "evidence_against_occurrence"}
            if ev_for is not None and (ev_for < -_TOL or ev_for > len(for_roots) + _TOL):
                problems.append(f"{tag}: evidence_for {ev_for} is outside [0, {len(for_roots)}] — {len(for_roots)} "
                                "root(s) feed the channel and every per-root value is ≤ 1")
            if ev_against is not None and (ev_against < -_TOL or ev_against > len(against_roots) + _TOL):
                problems.append(f"{tag}: evidence_against {ev_against} is outside [0, {len(against_roots)}]")
            if not against_ok and ev_against is not None:
                problems.append(f"{tag}: evidence_against is stored but the registry row declares no way to "
                                "evaluate that channel (expected NULL)")
            continue
        # ── policy 3–5: every live member is a constant — re-derive piecewise ─────────────────────────────
        if peak is None or ev_for is None:
            problems.append(f"{tag}: the objective is qualified but peak/evidence_for is NULL")
            detail.append(row)
            continue
        if not against_ok and ev_against is not None:
            problems.append(f"{tag}: evidence_against is stored but the registry row declares no way to "
                            "evaluate that channel (expected NULL)")
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
                        per_root[recs[rid]["root"]] = max(per_root.get(recs[rid]["root"], 0.0), qualified[rid][1])
                cands.append((sum(per_root.values()), a))     # no for-channel member live ⇒ the objective is 0
        if not cands:
            problems.append(f"{tag}: no objective candidate re-derived")
            detail.append(row)
            continue
        best, want_peak = earliest_max(cands)
        row["objective_value"] = best
        check_provenance(tag, row, len(qualified), s_objective, s_objective_value, s_qualification)
        live_now = [rid for rid in _live(recs, want_peak)]
        live_q = [rid for rid in live_now if rid in qualified]
        live_unq_against = [rid for rid in live_now if rid in unq_ids
                            and chans[rid] in ("evidence_against_occurrence", None)]
        want_against_null = (not against_ok) or bool(live_unq_against)
        sums = {"evidence_for_occurrence": {}, "evidence_against_occurrence": {}}
        for rid in live_q:
            slot = sums[chans[rid]]
            slot[recs[rid]["root"]] = max(slot.get(recs[rid]["root"], 0.0), qualified[rid][1])
        want_for = sum(sums["evidence_for_occurrence"].values())
        if path_id == "P4":
            want_score = best
        elif any(rid in unq_ids for rid in live_now):
            want_score = None                         # a live unqualified member's product is unknown
        else:
            want_score = max((qualified[rid][1] for rid in live_q), default=0.0)
        ok = True
        if (score is None) != (want_score is None) or (
                score is not None and abs(score - want_score) > _TOL):
            problems.append(f"{tag}: score {score} != re-derived {want_score}")
            ok = False
        if want_score is not None and not (0.0 <= want_score <= 1.0 + _TOL):
            problems.append(f"{tag}: re-derived score {want_score} outside [0,1]")
            ok = False
        if peak != want_peak:
            problems.append(f"{tag}: peak {peak} != re-derived {want_peak}")
            ok = False
        if abs(ev_for - want_for) > _TOL:
            problems.append(f"{tag}: evidence_for {ev_for} != re-derived {want_for}")
            ok = False
        if (ev_against is None) != want_against_null:
            problems.append(f"{tag}: evidence_against NULL-ness {ev_against is None} contradicts the "
                            f"registry row / the members live at the peak (expected NULL={want_against_null})")
            ok = False
        elif ev_against is not None:
            want_against = sum(sums["evidence_against_occurrence"].values())
            if abs(ev_against - want_against) > _TOL:
                problems.append(f"{tag}: evidence_against {ev_against} != re-derived {want_against}")
                ok = False
        # the valence the stored evidence implies (B's rule, the verifier's own arguments)
        if not want_against_null:
            want_valence = _expected_valence(event_class, want_for, sums_total(sums), None)
        else:
            why = ("evidence_against_channel_unqualified" if against_unq
                   else "evidence_against_channel_not_evaluated")
            want_valence = _expected_valence(event_class, want_for, 0.0, why)
        if valence != want_valence:
            problems.append(f"{tag}: outcome valence {valence!r} != {want_valence!r} implied by the evidence")
            ok = False
        if ok:
            numeric += 1
            fully_reproduced += 1
        detail.append(row)
    if problems:
        raise RuntimeError(
            f"window semantic verification failed {event_class}/{path_id}: " + "; ".join(problems))
    return {"windows": len(windows), "numeric_reproduced": numeric,
            "fully_reproduced": fully_reproduced, "unverified_dynamic": len(unverified),
            "unverified_windows": unverified, "policy_version": policy,
            "fields_verified": list(GOVERNED_FIELDS), "windows_detail": detail,
            # VERIFIED only when EVERY window's stored fields were reproduced exactly
            "status": "UNVERIFIED_DYNAMIC" if unverified else "VERIFIED"}


def sums_total(sums) -> float:
    return sum(sums["evidence_against_occurrence"].values())


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


# ── R8-4: member support against INDEPENDENT geometry ────────────────────────────────────────────────────

#: the verifier's OWN statement of the contact geometry (spec §6.2 / WP1 contract): the admission orb per point
#: relation (the slow-body rows of the convention) and the forward dṛṣṭi angles per graha (Mars 4th/8th, Jupiter
#: 5th/9th, Saturn 3rd/10th, every graha the 7th; nodes cast none — N-14). A test asserts both equal the kernel's.
_POINT_ORB_DEG = {"conjunction": 1.0, "aspect": 1.0}
_ASPECT_ANGLES = {"sun": (180.0,), "moon": (180.0,), "mercury": (180.0,), "venus": (180.0,),
                  "mars": (90.0, 180.0, 210.0), "jupiter": (120.0, 180.0, 240.0),
                  "saturn": (60.0, 180.0, 270.0), "rahu": (), "ketu": ()}
_SIGN = {"sign_span": r"^span:([1-9]|1[0-2])$", "house_span": r"^span:([1-9]|1[0-2])$"}


def _angdiff(a: float, b: float) -> float:
    d = (a - b + 180.0) % 360.0 - 180.0
    return abs(d)


def _probe_contact(position_at, body, relation, target, t_in, t_out, open_start, open_end, margin):
    """Probe the contact geometry from the EPHEMERIS (never the stored span): the body must be in the geometry just
    inside both ends and — unless that end is the horizon's own edge (a truncated span) — just outside it.
    Returns a list of problems."""
    from datetime import timedelta
    dt = timedelta(seconds=margin)
    problems = []
    if relation == "residence":
        want = int(target.split(":", 1)[1]) - 1
        inside = lambda t: int((position_at(body, t) % 360.0) // 30.0) == want          # noqa: E731
        label = f"{body} in sign {want + 1}"
        ray_of = None
    elif relation == "aspect" and target.startswith("span:"):
        # aspect-to-span: the body aspects the target sign while it stands in the sign (target − angle/30) for
        # one of its dṛṣṭi angles (forward count, spec §6.2 inv 6)
        n = int(target.split(":", 1)[1]) - 1
        signs = [(n - int(a // 30.0)) % 12 for a in _ASPECT_ANGLES[body]]
        sign_at = lambda t: int((position_at(body, t) % 360.0) // 30.0)                 # noqa: E731
        inside = lambda t: sign_at(t) in signs                                          # noqa: E731
        label = f"{body} aspecting {target} from signs {[x + 1 for x in signs]}"
        ray_of = sign_at
    elif relation in ("conjunction", "aspect"):
        lam = float(target.split(":", 1)[1]) % 360.0
        orb = _POINT_ORB_DEG[relation]
        angles = (0.0,) if relation == "conjunction" else _ASPECT_ANGLES[body]
        levels = [(lam - a) % 360.0 for a in angles]
        best = lambda t: min(range(len(levels)), key=lambda i: _angdiff(position_at(body, t), levels[i]))  # noqa: E731
        inside = lambda t: _angdiff(position_at(body, t), levels[best(t)]) <= orb       # noqa: E731
        label = f"{body} {relation} {target} (orb {orb}°)"
        ray_of = best
    else:
        return [f"{body} {relation}: no independent geometry for this relation"]
    t0 = t_in + dt
    t1 = t_out - dt
    if not inside(t0):
        problems.append(f"{label}: not in the geometry just inside the stored start {t_in.isoformat()}")
    if not inside(t1):
        problems.append(f"{label}: not in the geometry just inside the stored end {t_out.isoformat()}")
    if not open_start:
        before = t_in - dt
        if relation == "residence":
            outside = not inside(before)
        elif target.startswith("span:"):
            outside = ray_of(before) != ray_of(t0)
        else:
            i = ray_of(t0)
            outside = _angdiff(position_at(body, before), levels[i]) > orb
        if not outside:
            problems.append(f"{label}: still in the geometry just before the stored start {t_in.isoformat()}")
    if not open_end:
        after = t_out + dt
        if relation == "residence":
            outside = not inside(after)
        elif target.startswith("span:"):
            outside = ray_of(after) != ray_of(t1)
        else:
            i = ray_of(t1)
            outside = _angdiff(position_at(body, after), levels[i]) > orb
        if not outside:
            problems.append(f"{label}: still in the geometry just after the stored end {t_out.isoformat()}")
    return problems


def _probe_contact_derived(position_at, body, relation, target, t_in, t_out, open_start, open_end, accuracy_deg,
                           floor_seconds):
    """`_probe_contact` with margins DERIVED per end (see `boundary_match`): inside/outside probes sit `2 x` the time
    tolerance from the stored edge (never closer than `floor_seconds`, never more than a quarter of the span); an end where
    no time tolerance exists (a station) is verified in angle: the stored boundary must lie within the stated accuracy of an
    edge of the geometry."""
    span = (t_out - t_in).total_seconds()
    problems = []
    margins = []
    for t, is_open in ((t_in, open_start), (t_out, open_end)):
        tol = bm.time_tolerance_seconds(position_at, body, t, accuracy_deg)
        if tol is None:
            # a station: no time margin means anything. If the body IS at an edge of the geometry the boundary is
            # genuine in ANGLE and the time probes are skipped for this end; if it is not at an edge the stored end is
            # not a crossing at all and the ordinary probes (floor margin) say which side is wrong
            at_edge = bm.edge_distance_degrees(position_at, body, relation, target, t) <= 2 * accuracy_deg
            margins.append(None if (at_edge or is_open) else max(floor_seconds, min(60.0, span / 4.0)))
        else:
            margins.append(max(floor_seconds, min(2.0 * tol, span / 4.0)))
    m = [x for x in margins if x is not None]
    if not m:
        return problems
    return problems + _probe_contact(position_at, body, relation, target, t_in, t_out,
                                     open_start or margins[0] is None, open_end or margins[1] is None,
                                     min(max(m), span / 4.0))


def verify_member_geometry(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                           rule_version: str, position_at, probe_seconds: float = 1.0) -> dict:
    """The window members' CONTACT SPANS checked against the ephemeris itself (R8-4: `verify_member_support` compares
    the record's support with the builder-written contact span, which is not independent). For every distinct contact
    of a member: the body is in the geometry (a sign; a point within orb of its ray level) just inside the stored start
    and end, and outside just beyond each end that is not the horizon's own edge. `position_at(body, t)` is the Swiss
    longitude probe — no arc index, no substrate, no solver. A span that is not the physical one fails the build."""
    grain = (chart_id, generation, event_class, path_id, rule_version)
    rows = conn.execute(
        "SELECT DISTINCT c.contact_id::text, c.body, c.relation_kind, c.t_in, c.t_out, c.t_exact, o.canonical_target,"
        " lower(cov.completed_horizon), upper(cov.completed_horizon), c.delta_lambda"
        " FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " JOIN public.ka_gochara_contact c ON (c.chart_id, c.generation, c.contact_id)"
        "                                  = (r.chart_id, r.generation, r.contact_id)"
        " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id"
        " JOIN public.kala_gochara_coverage cov ON (cov.chart_id, cov.generation, cov.partition_kind,"
        "          cov.partition_key) = (r.chart_id, r.generation, r.coverage_partition_kind, r.coverage_partition_key)"
        " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s AND m.path_id = %s"
        " AND m.rule_version = %s ORDER BY 1", grain).fetchall()
    problems: list[str] = []
    probed = 0
    for row in rows:
        cid, body, relation, t_in, t_out, t_exact, target, h_lo, h_hi, delta_lambda = (
            tuple(row.values()) if isinstance(row, dict) else tuple(row))
        end = t_out if t_out is not None else h_hi
        open_start = t_exact is None and t_in <= h_lo          # a span truncated at the horizon's start
        open_end = t_out is None or t_out >= h_hi              # truncated at (or open to) the horizon's end
        if (end - t_in).total_seconds() <= 0:
            problems.append(f"contact {cid}: an empty span")
            continue
        rel = "residence" if relation in ("residence", "sign_ingress") else relation
        # R9-9: the probe margin is DERIVED from the contact's stated angular accuracy and the body's speed at each end —
        # a fixed 1 s margin rejected correct contacts on the real sky (the solver is accurate to 1 arcsecond: ≈ 24 s for
        # the Sun, ≈ 12 min for Saturn). At a station (no usable time tolerance) the end is checked in ANGLE instead.
        acc = bm.accuracy_degrees(delta_lambda)
        problems.extend(f"contact {cid}: {p}" for p in _probe_contact_derived(
            position_at, body, rel, target, t_in, end, open_start, open_end, acc, probe_seconds))
        probed += 1
    if problems:
        raise RuntimeError(f"member geometry verification failed {event_class}/{path_id}: " + "; ".join(problems))
    return {"contacts": probed}


def reconstruct_qualification(conn, *, chart_id: str, generation: str, event_class: str, path_id: str,
                              rule_version: str, factor_rows: list[dict],
                              drishti_bound: bool = False, vedha_bound: bool = False) -> dict:
    """{window_id: {affected_channels, reasons: {record_id: [reason...]}}} — the qualification a window
    carries, RECONSTRUCTED from its stored members and the bound factor rows (1156 has no column for it;
    persistence is not required, reconstruction is). Serving reads this; a channel is affected when an
    unqualified member feeds it (a channel-less one feeds both)."""
    grain = (chart_id, generation, event_class, path_id, rule_version)
    rows = conn.execute(
        "SELECT m.window_id::text, r.record_id::text, r.relation, r.object_kind, r.agent, r.house_from_frame,"
        " (SELECT array_agg(ARRAY[lower(x)::text, upper(x)::text]) FROM unnest(r.temporal_support_intervals) x)"
        " FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s AND m.path_id = %s"
        " AND m.rule_version = %s ORDER BY 1, 2", grain).fetchall()
    completed = _completed_horizon(conn, grain)
    out: dict[str, dict] = {}
    for wid, rid, rel, kind, agent, house, sup in rows:
        from datetime import datetime as _dt
        supports = [(_dt.fromisoformat(a), _dt.fromisoformat(b)) for a, b in (sup or [])]
        rec = {"relation": rel, "kind": kind, "agent": agent, "house": house,
               "boundaries_complete": _boundaries_complete(rel, supports, completed)}
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


__all__ = ["GOVERNED_FIELDS", "POLICY_VERSION", "reconstruct_qualification", "satisfies_gate",
           "verify_member_geometry", "verify_member_support", "verify_window_semantics"]
