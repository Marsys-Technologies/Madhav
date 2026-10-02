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


def record_verification(conn, *, chart_id, generation, event_class, path_id, rule_version, report: dict,
                        input_digest: str) -> dict:
    """Refuse a stored window set that is not the independently expected one, then persist the generation-bound
    result (delete-then-insert for this verifier — a candidate rebuild REPLACES it)."""
    grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id,
                 rule_version=rule_version)
    expected, stored = expected_windows(conn, **grain), stored_windows(conn, **grain)
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
    detail = report["windows_detail"]
    if len(detail) != len(stored):
        raise RuntimeError(f"window verification {event_class}/{path_id}: the report carries {len(detail)} "
                           f"provenance entries for {len(stored)} stored windows")
    content = conn.execute(
        "SELECT public.ka_gochara_eval_window_content_digest(%s::uuid, %s, %s, %s, %s)",
        (chart_id, generation, event_class, path_id, rule_version)).fetchone()
    content = next(iter(content.values())) if isinstance(content, dict) else content[0]
    digest = intervals_digest(stored)
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
        " input_digest, windows_detail) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",
        (chart_id, generation, event_class, path_id, rule_version, VERIFIER_ID, VERIFIER_VERSION,
         report["status"], report["policy_version"], len(expected), len(stored), report["fully_reproduced"],
         report["unverified_dynamic"], intervals_digest(expected), digest, content,
         list(report["fields_verified"]), input_digest, json.dumps(detail, sort_keys=True)))
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
           "expected_windows", "intervals_digest", "record_verification", "require_candidate_gate",
           "stored_windows", "verification_available"]
