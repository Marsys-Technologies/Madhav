"""The generation-bound window verification RESULT and the candidate gate that consumes it (R8-4; migration 1240).

The independent window verifier (`window_verifier`) produces a report. This module (1) derives, a second and
different way from the builder, the EXPECTED window set (the connected union of the admitted scored records'
supports — P4: the intersection of the Jupiter and Saturn unions) in Python, (2) refuses a stored set that omits
an expected window or invents one, (3) persists the result as ONE generation-bound row per window grain with the
verifier-derived qualification provenance, and (4) exposes the gate: `candidate_gate` returns the violations
(missing / not VERIFIED / stale / expected-set mismatch / wrong input identity) and `require_candidate_gate`
refuses on any. The database holds the same checks (`ka_gochara_window_verification_violations`) so a sealer need
not trust this process.

Nothing here commits or locks (the caller's transaction owns both)."""
from __future__ import annotations

import hashlib
import json
from datetime import timezone

VERIFIER_ID = "ka_gochara_window_verifier"
VERIFIER_VERSION = "1.0"
POLICY_VERSION = "window_qualification/1"
_TS = "%Y-%m-%dT%H:%M:%S.%fZ"


class CandidateGateRefused(RuntimeError):
    """The candidate has window-verification violations — it must not be sealed."""


def _fmt(t) -> str:
    return t.astimezone(timezone.utc).strftime(_TS)


def intervals_digest(intervals) -> str:
    """sha256 of the canonical JSON of the ordered [lo, hi) list — the bytes the database digests produce."""
    body = [[_fmt(lo), _fmt(hi)] for lo, hi in sorted(intervals)]
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def verification_available(conn) -> bool:
    """Does the APPLIED schema carry the result table and its digest functions (1240)? Read, never assumed."""
    row = conn.execute(
        "SELECT to_regclass('public.ka_gochara_eval_window_verification') IS NOT NULL"
        " AND to_regprocedure('public.ka_gochara_eval_window_content_digest(uuid,text,text,text,text)') IS NOT NULL"
        " AND to_regprocedure('public.ka_gochara_window_verification_violations(uuid,text)') IS NOT NULL"
    ).fetchone()
    return bool(next(iter(row.values())) if isinstance(row, dict) else row[0])


def can_write_verification(conn) -> bool:
    """Does the RUNNING role hold INSERT on the verification table? The builder deliberately does not (1240: the writer
    cannot verify itself); only a provisioned verifier principal does."""
    row = conn.execute(
        "SELECT has_table_privilege(current_user, 'public.ka_gochara_eval_window_verification', 'INSERT')").fetchone()
    return bool(next(iter(row.values())) if isinstance(row, dict) else row[0])


def _union(spans):
    out: list[list] = []
    for lo, hi in sorted(spans):
        if out and lo <= out[-1][1]:
            if hi > out[-1][1]:
                out[-1][1] = hi
        else:
            out.append([lo, hi])
    return [(a, b) for a, b in out]


def _intersect(xs, ys):
    out, i, j = [], 0, 0
    while i < len(xs) and j < len(ys):
        lo, hi = max(xs[i][0], ys[j][0]), min(xs[i][1], ys[j][1])
        if lo < hi:
            out.append((lo, hi))
        if xs[i][1] <= ys[j][1]:
            i += 1
        else:
            j += 1
    return out


def expected_windows(conn, *, chart_id, generation, event_class, path_id, rule_version) -> list[tuple]:
    """The windows the grain MUST have, derived from the stored records alone (admitted AND scored, with a
    support): one per maximal connected component of the union of their supports; P4 — the intersection of the
    Jupiter and Saturn unions (both must be active). Python sweep; the database recomputes it separately."""
    rows = conn.execute(
        "SELECT r.agent, lower(s.x), upper(s.x) FROM public.ka_gochara_relationship_record r"
        " CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x)"
        " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s AND r.path_id = %s"
        " AND r.rule_version = %s AND r.admission_state = 'admitted' AND r.operator_role = 'scored'",
        (chart_id, generation, event_class, path_id, rule_version)).fetchall()
    rows = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]
    if path_id == "P4":
        by = {"jupiter": [], "saturn": []}
        for agent, lo, hi in rows:
            if agent in by:
                by[agent].append((lo, hi))
        return _intersect(_union(by["jupiter"]), _union(by["saturn"]))
    return _union([(lo, hi) for _a, lo, hi in rows])


def stored_windows(conn, *, chart_id, generation, event_class, path_id, rule_version) -> list[tuple]:
    rows = conn.execute(
        "SELECT lower(interval), upper(interval) FROM public.ka_gochara_eval_window"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s AND rule_version = %s"
        " ORDER BY 1", (chart_id, generation, event_class, path_id, rule_version)).fetchall()
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]


# ── R9-2: the digest of EVERYTHING the window derivation depends on (the verifier's own derivation) ─────────────────

def _canon(v) -> str:
    """The canonical JSON of `ka_gochara_canonical_json` (sorted keys by code point, no spaces, UTF-8 unescaped), built
    here — never taken from the database — so the two derivations of the preimage stay independent."""
    from decimal import Decimal
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, Decimal)):
        return format(v, "f") if isinstance(v, Decimal) else str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + _canon(v[k]) for k in sorted(v)) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_canon(x) for x in v) + "]"
    raise TypeError(f"no canonical JSON for {type(v).__name__}")


def _opt(t):
    return None if t is None else _fmt(t)


def derivation_inputs_preimage(conn, *, chart_id, generation, event_class, path_id, rule_version) -> dict:
    """The COMPLETE SEMANTIC DEPENDENCY SET of the grain's window derivation as this verifier reads it (preimage
    'inputs/2'; R9-2, R10-2): every record (identity, roles, provenance, ruling, admission, house, frame, person, anchor,
    target, contact, support state and supports, and EVERY result field — evidence for/against and severity as the text the
    database prints, and the valence), its prerequisite results, EVERY contact of the generation with the fields the geometry
    certification reads (not only those a surviving record references), the snapshot's input identity, the manifest vector
    (digest) and the result policy. Equal to 1240's `ka_gochara_eval_window_inputs_digest` byte for byte."""
    import json as _json
    from decimal import Decimal
    grain = (chart_id, generation, event_class, path_id, rule_version)
    rows = conn.execute(
        "SELECT r.record_id::text, r.agent, r.relation, r.object_kind, r.object_role, r.operator_role, r.provenance,"
        " r.ruling_ref, r.admission_state, r.house_from_frame, r.frame_kind, r.frame_arg, r.affected_person,"
        " r.temporal_support_state, r.period_anchor_lord, r.period_anchor_level, o.canonical_target, r.contact_id::text,"
        " r.evidence_for_occurrence::text, r.evidence_against_occurrence::text, r.severity::text,"
        " r.outcome_valence_for_native, r.temporal_support_intervals"
        " FROM public.ka_gochara_relationship_record r"
        " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
        " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s AND r.path_id = %s"
        " AND r.rule_version = %s ORDER BY r.record_id::text", grain).fetchall()
    rows = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]
    records, ids = [], []
    for (rid, agent, rel, kind, orole, role, prov, ruling, adm, house, fkind, farg, person, sstate, a_lord, a_level,
         target, contact, ev_for, ev_against, severity, valence, supports) in rows:
        ids.append(rid)
        records.append({
            "id": rid, "agent": agent, "relation": rel, "kind": kind, "object_role": orole, "role": role,
            "provenance": prov, "ruling": ruling, "admission": adm, "house": house, "frame_kind": fkind,
            "frame_arg": farg, "person": person, "support_state": sstate, "anchor": [a_lord, a_level],
            "target": target, "contact": contact, "evidence_for": ev_for, "evidence_against": ev_against,
            "severity": severity, "valence": valence,
            "supports": [[_fmt(x.lower), _fmt(x.upper)] for x in sorted(supports or [], key=lambda x: x.lower)]})
    prereqs = []
    if ids:
        prereqs = [list(tuple(r.values()) if isinstance(r, dict) else tuple(r)) for r in conn.execute(
            "SELECT record_id::text, ordinal, predicate_id, predicate_rule_version, result"
            " FROM public.ka_gochara_record_prerequisite WHERE record_id = ANY(%s::uuid[])"
            " ORDER BY record_id::text, ordinal", (ids,)).fetchall()]
    contacts = [[r[0], r[1], r[2], r[3], _opt(r[4]), _opt(r[5]), _opt(r[6]), r[7], r[8], r[9], r[10]] for r in (
        tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
            "SELECT c.contact_id::text, c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out, c.t_exact,"
            " c.solver_method, c.delta_lambda::text, c.delta_t::text, c.precision_regime"
            " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
            "   ON o.physical_object_id = c.physical_object_id"
            " WHERE c.chart_id = %s AND c.generation = %s ORDER BY c.contact_id::text",
            (chart_id, generation)).fetchall())]
    snap = conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot"
                        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    pub = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    vector = None if pub is None else _json.loads(
        next(iter(pub.values())) if isinstance(pub, dict) else pub[0], parse_float=Decimal)
    return {
        "version": "inputs/2",
        "records": records, "prerequisites": prereqs, "contacts": contacts,
        "input": None if snap is None else (next(iter(snap.values())) if isinstance(snap, dict) else snap[0]),
        "manifest": None if vector is None else hashlib.sha256(_canon(vector).encode("utf-8")).hexdigest(),
        "policy": None if vector is None else vector.get("result_policy")}


def derivation_inputs_digest(conn, **grain) -> str:
    return hashlib.sha256(_canon(derivation_inputs_preimage(conn, **grain)).encode("utf-8")).hexdigest()


def record_verification(conn, *, chart_id, generation, event_class, path_id, rule_version, report: dict,
                        input_digest: str, expected=None) -> dict:
    """Refuse a stored window set that is not the independently expected one, then persist the generation-bound
    result (delete-then-insert for this verifier — a candidate rebuild REPLACES it)."""
    grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id,
                 rule_version=rule_version)
    # R10-1: `expected` — when the caller derived the records independently (record_derivation) — is the windows THOSE
    # derived records imply; only without it do we fall back on the stored records (P1: verified-complete beforehand)
    expected = sorted(expected) if expected is not None else expected_windows(conn, **grain)
    stored = stored_windows(conn, **grain)
    if expected != stored:
        omitted = [w for w in expected if w not in stored]
        invented = [w for w in stored if w not in expected]
        raise RuntimeError(
            f"window verification failed {event_class}/{path_id}@{rule_version}: the stored windows are not the "
            f"expected ones — omitted {[(_fmt(a), _fmt(b)) for a, b in omitted]}, "
            f"invented {[(_fmt(a), _fmt(b)) for a, b in invented]}")
    from .window_verifier import satisfies_gate
    if (report["status"] == "VERIFIED") != satisfies_gate(report):         # the one gate predicate, now CALLED
        raise RuntimeError(f"window verification {event_class}/{path_id}: status {report['status']!r} contradicts "
                           "the gate predicate on the same report")
    if len(report["windows_detail"]) != len(stored):
        raise RuntimeError(f"window verification {event_class}/{path_id}: the report carries "
                           f"{len(report['windows_detail'])} provenance entries for {len(stored)} stored windows")
    content = conn.execute(
        "SELECT public.ka_gochara_eval_window_content_digest(%s::uuid, %s, %s, %s, %s)",
        (chart_id, generation, event_class, path_id, rule_version)).fetchone()
    content = next(iter(content.values())) if isinstance(content, dict) else content[0]
    digest = intervals_digest(stored)
    inputs_digest = derivation_inputs_digest(conn, **grain)             # R9-2: bound into the stored verification
    conn.execute(
        "DELETE FROM public.ka_gochara_eval_window_verification WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND path_id = %s AND rule_version = %s AND verifier_id = %s"
        " AND verifier_version = %s",
        (chart_id, generation, event_class, path_id, rule_version, VERIFIER_ID, VERIFIER_VERSION))
    conn.execute(
        "INSERT INTO public.ka_gochara_eval_window_verification ("
        " chart_id, generation, event_class, path_id, rule_version, verifier_id, verifier_version, status,"
        " policy_version, windows_expected, windows_stored, windows_reproduced, windows_unverified,"
        " expected_windows_digest, stored_windows_digest, windows_content_digest, fields_verified,"
        " input_digest, derivation_inputs_digest) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (chart_id, generation, event_class, path_id, rule_version, VERIFIER_ID, VERIFIER_VERSION,
         report["status"], report["policy_version"], len(expected), len(stored), report["fully_reproduced"],
         report["unverified_dynamic"], intervals_digest(expected), digest, content,
         list(report["fields_verified"]), input_digest, inputs_digest))
    return {"status": report["status"], "windows": len(stored), "content_digest": content}


def candidate_gate(conn, chart_id: str, generation: str, event_class: str | None = None) -> list[dict]:
    """The window-verification violations (all classes, or one) — empty iff the candidate may proceed."""
    rows = conn.execute(
        "SELECT event_class, path_id, rule_version, violation, detail"
        " FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (chart_id, generation)).fetchall()
    out = [dict(zip(("event_class", "path_id", "rule_version", "violation", "detail"),
                    tuple(r.values()) if isinstance(r, dict) else tuple(r))) for r in rows]
    return [v for v in out if event_class is None or v["event_class"] == event_class]


def require_candidate_gate(conn, chart_id: str, generation: str, event_class: str | None = None) -> None:
    violations = candidate_gate(conn, chart_id, generation, event_class)
    if violations:
        raise CandidateGateRefused(
            "candidate gate refused (window verification): "
            + "; ".join(f"{v['event_class']}/{v['path_id']}@{v['rule_version']} {v['violation']} ({v['detail']})"
                        for v in violations))


__all__ = ["CandidateGateRefused", "POLICY_VERSION", "VERIFIER_ID", "VERIFIER_VERSION", "candidate_gate",
           "derivation_inputs_digest", "derivation_inputs_preimage",
           "can_write_verification", "expected_windows", "intervals_digest", "record_verification", "require_candidate_gate",
           "stored_windows", "verification_available"]
