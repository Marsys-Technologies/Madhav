"""Independent derivation of the P1 prerequisite-restricted SUPPORT (Codex round 7 [3]).

A P1 transit record's admitted support is its contact span restricted to the periods the agent RUNS. The
builder computes it by calling Stream B's `period_running_at` predicate over the L1 rows it read; this
verifier derives the same thing a different way — entirely in Postgres, from the SNAPSHOT-BOUND daśā rows
(`consumed_dasha_row_ids`, levels 1–3, the agent's lord) with multirange arithmetic — and compares it with
what was stored, and the stored `period_running_at` result with what that support implies:

  agent with running rows : stored support  == contact ∩ ⋃(running periods);  result == true iff non-empty
  agent with NO rows      : stored support  == the contact span (unrestricted);  result == 'unknown'

It imports nothing from the builder. A support that is wider than the permission (admitting a period
gap), narrower (discarding a valid later portion) or on the wrong pieces fails the build.
"""
from __future__ import annotations

_SQL = """
WITH snap AS (
  SELECT s.consumed_dasha_row_ids AS ids FROM public.ka_gochara_search_input_snapshot s
  WHERE s.chart_id = %(chart)s AND s.generation = %(gen)s),
runs AS (
  SELECT lower(d.lord_graha) AS agent,
         range_agg(tstzrange(d.start_iso, d.end_iso, '[)')) AS m
  FROM public.chart_dashas d, snap
  WHERE d.chart_id = %(chart)s AND d.dasha_row_id = ANY (snap.ids) AND d.level_n IN (1, 2, 3)
  GROUP BY 1),
rec AS (
  SELECT r.record_id, r.agent, r.temporal_support_state AS state,
         COALESCE((SELECT range_agg(x) FROM unnest(r.temporal_support_intervals) x), '{}'::tstzmultirange) AS stored,
         tstzrange(c.t_in, COALESCE(c.t_out, upper(cov.completed_horizon)), '[)')::tstzmultirange AS contact,
         (SELECT p.result FROM public.ka_gochara_record_prerequisite p
           WHERE p.record_id = r.record_id AND p.predicate_id = 'period_running_at') AS result
  FROM public.ka_gochara_relationship_record r
  JOIN public.ka_gochara_contact c
    ON (c.chart_id, c.generation, c.contact_id) = (r.chart_id, r.generation, r.contact_id)
  JOIN public.kala_gochara_coverage cov
    ON (cov.chart_id, cov.generation, cov.partition_kind, cov.partition_key)
     = (r.chart_id, r.generation, r.coverage_partition_kind, r.coverage_partition_key)
  WHERE r.chart_id = %(chart)s AND r.generation = %(gen)s AND r.event_class = %(cls)s
    AND r.path_id = 'P1' AND r.contact_id IS NOT NULL)
SELECT rec.record_id::text, rec.stored::text,
       (CASE WHEN runs.m IS NULL THEN rec.contact ELSE rec.contact * runs.m END)::text AS expected_text,
       rec.stored = (CASE WHEN runs.m IS NULL THEN rec.contact ELSE rec.contact * runs.m END) AS equal,
       isempty(CASE WHEN runs.m IS NULL THEN rec.contact ELSE rec.contact * runs.m END) AS expected_empty,
       rec.result, runs.m IS NOT NULL AS has_rows
FROM rec LEFT JOIN runs ON runs.agent = rec.agent
"""


def verify_p1_support(conn, *, chart_id: str, generation: str, event_class: str) -> dict:
    rows = conn.execute(_SQL, {"chart": chart_id, "gen": generation, "cls": event_class}).fetchall()
    problems: list[str] = []
    restricted = 0
    for rid, stored, expected, equal, expected_empty, result, has_rows in rows:
        if not equal:
            problems.append(f"record {rid}: stored support {stored} != the contact restricted to the running "
                            f"periods {expected}")
        want = ("unknown" if not has_rows else ("false" if expected_empty else "true"))
        if result != want:
            problems.append(f"record {rid}: period_running_at stored {result!r}, the support implies {want!r}")
        restricted += 1 if has_rows else 0
    if problems:
        raise RuntimeError(f"P1 support verification failed {event_class}: " + "; ".join(problems))
    return {"records": len(rows), "restricted": restricted}


# ── AM-20: the P1 `house_from_frame` DESCRIPTOR, re-derived from the verifier's OWN classical table ────────

_HOUSE_SQL = """
SELECT r.record_id::text, r.agent, o.canonical_target, r.house_from_frame, r.frame_kind, r.frame_arg
FROM public.ka_gochara_relationship_record r
JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id
WHERE r.chart_id = %(chart)s AND r.generation = %(gen)s AND r.event_class = %(cls)s
  AND r.path_id = 'P1' AND r.contact_id IS NOT NULL
ORDER BY r.record_id
"""


def expected_p1_anchor(agent: str, sign_index: int) -> str:
    """The period lord anchoring a P1 transit record on the sign (0 = Aries): the agent when the sign is its
    own / exaltation / debilitation sign, else (Sun/Jupiter only) the graha whose exaltation sign it is.
    The verifier's own table — nothing is imported from the builder."""
    from .inventory_verifier import _DEBIL, _EXALT, _OWN, _SIGNS
    sign = _SIGNS[sign_index]
    if sign in _OWN.get(agent, ()) or sign in (_EXALT.get(agent), _DEBIL.get(agent)):
        return agent
    owners = [g for g, s in _EXALT.items() if s == sign]
    if agent not in ("sun", "jupiter") or len(owners) != 1:
        raise ValueError(f"{agent} on {sign} is not a P1 content sign — no anchoring period lord")
    return owners[0]


def verify_p1_house_descriptor(conn, *, chart_id: str, generation: str, event_class: str) -> dict:
    """AM-20: every minted P1 transit record's `house_from_frame` equals the inclusive whole-sign count from
    the NATAL sign of its anchoring period lord (L1 natal positions of the snapshot's consumed facts) to the
    sign of the contact; the stored frame is the arg-less `dasha_lord`. A descriptor only — this checks that
    it says what AM-20 says it says, never that anything depends on it."""
    from .inventory_verifier import Unverifiable, read_chart
    rows = conn.execute(_HOUSE_SQL, {"chart": chart_id, "gen": generation, "cls": event_class}).fetchall()
    if not rows:
        return {"records": 0}              # nothing minted ⇒ nothing to verify (no natal read needed)
    snap = conn.execute(
        "SELECT consumed_fact_ids FROM public.ka_gochara_search_input_snapshot"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if snap is None:
        raise Unverifiable("no snapshot to read the natal positions from")
    natal = read_chart(conn, snap[0])["natal"]
    problems: list[str] = []
    for rid, agent, target, house, fkind, farg in rows:
        if (fkind, farg) != ("dasha_lord", None):
            problems.append(f"record {rid}: frame {fkind}:{farg} is not the arg-less dasha_lord")
            continue
        sign = int(target.split(":", 1)[1]) - 1
        try:
            lord = expected_p1_anchor(agent, sign)
        except ValueError as exc:
            problems.append(f"record {rid}: {exc}")
            continue
        want = (sign - int(natal[lord] // 30)) % 12 + 1
        if house != want:
            problems.append(f"record {rid}: house_from_frame {house}, the count from {lord}'s natal sign is {want}")
    if problems:
        raise RuntimeError(f"P1 house-descriptor verification failed {event_class}: " + "; ".join(problems))
    return {"records": len(rows)}


__all__ = ["verify_p1_support", "verify_p1_house_descriptor", "expected_p1_anchor"]
