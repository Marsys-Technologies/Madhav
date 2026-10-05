"""Independent derivation of the P1 prerequisite-restricted SUPPORT (Codex round 7 [3]).

A P1 transit record's admitted support is its contact span restricted to the periods the agent RUNS. The
builder computes it by calling Stream B's `period_running_at` predicate over the L1 rows it read; this
verifier derives the same thing a different way — entirely in Postgres, from the SNAPSHOT-BOUND daśā rows
(`consumed_dasha_row_ids`, levels 1–3, the agent's lord) with multirange arithmetic — and compares it with
what was stored, and the stored `period_running_at` result with what that support implies:

  anchor with running rows : stored support == contact ∩ D(anchor lord, anchor level); result == true iff non-empty
  anchor with NO rows      : stored support == the contact span (unrestricted);        result == 'unknown'

where D(X, ℓ) = the union of the half-open `[start, end)` intervals of the snapshot-bound level-ℓ rows whose lord is X
and the ANCHOR (X, ℓ) is the record's own `period_anchor_lord` / `period_anchor_level` (AM-21 part 2) — NOT the transiting
agent's periods and not every level. For Phaladīpikā XX.38 (the Sun/Jupiter entering a bhukti lord's sign) the two differ.

It imports nothing from the builder. A support that is wider than the permission (admitting a period
gap), narrower (discarding a valid later portion) or on the wrong pieces fails the build.
"""
from __future__ import annotations

_SQL = """
WITH snap AS (
  SELECT s.consumed_dasha_row_ids AS ids FROM public.ka_gochara_search_input_snapshot s
  WHERE s.chart_id = %(chart)s AND s.generation = %(gen)s),
runs AS (
  SELECT lower(d.lord_graha) AS lord, d.level_n,
         range_agg(tstzrange(d.start_iso, d.end_iso, '[)')) AS m
  FROM public.chart_dashas d, snap
  WHERE d.chart_id = %(chart)s AND d.dasha_row_id = ANY (snap.ids) AND d.level_n IN (1, 2, 3)
  GROUP BY 1, 2),
rec AS (
  SELECT r.record_id, r.period_anchor_lord AS lord,
         CASE r.period_anchor_level WHEN 'md' THEN 1 WHEN 'ad' THEN 2 WHEN 'pd' THEN 3 END AS level_n,
         r.temporal_support_state AS state,
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
FROM rec LEFT JOIN runs ON (runs.lord, runs.level_n) = (rec.lord, rec.level_n)
"""


def _scalar(row) -> int:
    return 0 if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])


def _anchor_columns(conn) -> bool:
    return _scalar(conn.execute(
        "SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_relationship_record'::regclass"
        " AND attname IN ('period_anchor_lord', 'period_anchor_level') AND NOT attisdropped").fetchone()) == 2


def verify_p1_support(conn, *, chart_id: str, generation: str, event_class: str) -> dict:
    if not _anchor_columns(conn):                      # no 1233: no P1 record can exist (minting is gated)
        n = conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
                         " AND chart_id = %s AND generation = %s AND event_class = %s",
                         (chart_id, generation, event_class)).fetchone()
        if _scalar(n):
            raise RuntimeError("P1 records exist on a schema without the period-anchor columns (1233)")
        return {"records": 0, "restricted": 0}
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


# ── AM-20 (revised): the P1 `house_from_frame` DESCRIPTOR, counted from the LAGNA ──────────────────────────

_HOUSE_SQL = """
SELECT r.record_id::text, o.canonical_target, r.house_from_frame, r.frame_kind, r.frame_arg
FROM public.ka_gochara_relationship_record r
JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id
WHERE r.chart_id = %(chart)s AND r.generation = %(gen)s AND r.event_class = %(cls)s
  AND r.path_id = 'P1' AND r.contact_id IS NOT NULL
ORDER BY r.record_id
"""


def verify_p1_house_descriptor(conn, *, chart_id: str, generation: str, event_class: str) -> dict:
    """AM-20 (revised; Phaladīpikā XX.34 "the Bhava it represents when counted from the Lagna", XX.59):
    every minted P1 transit record's `house_from_frame` is the inclusive whole-sign count FROM THE LAGNA (the
    snapshot-bound L1 lagna) to the sign of the contact; the stored frame is the arg-less `dasha_lord`. A
    descriptor only — this checks it says what AM-20 says it says, never that anything depends on it. A count
    from the period lord's natal sign (the superseded first reading) fails."""
    from .inventory_verifier import Unverifiable, read_chart
    rows = conn.execute(_HOUSE_SQL, {"chart": chart_id, "gen": generation, "cls": event_class}).fetchall()
    if not rows:
        return {"records": 0}              # nothing minted ⇒ nothing to verify (no natal read needed)
    snap = conn.execute(
        "SELECT consumed_fact_ids FROM public.ka_gochara_search_input_snapshot"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if snap is None:
        raise Unverifiable("no snapshot to read the lagna from")
    lagna = int(read_chart(conn, snap[0])["lagna"] // 30)
    problems: list[str] = []
    for rid, target, house, fkind, farg in rows:
        if (fkind, farg) != ("dasha_lord", None):
            problems.append(f"record {rid}: frame {fkind}:{farg} is not the arg-less dasha_lord")
            continue
        want = (int(target.split(":", 1)[1]) - 1 - lagna) % 12 + 1
        if house != want:
            problems.append(f"record {rid}: house_from_frame {house}, the count from the lagna is {want}")
    if problems:
        raise RuntimeError(f"P1 house-descriptor verification failed {event_class}: " + "; ".join(problems))
    return {"records": len(rows)}


# ── AM-21 part 2 / R9-2 (iii): the ANCHOR set of every P1 CONTACT, from the EXPECTED contact set ────────────

_GRAHAS7 = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
_LEVELS = ("md", "ad", "pd")
#: R9-5 (this verifier's OWN literals): the PD level has no verse; its readings are authorised TESTIMONY
PD_LIMITATION = "p1_pd_level_no_source"
PD_RULING = "ST-P1-PD-TESTIMONY-20261002"


def expected_p1_anchors(agent: str, sign_index: int) -> set[tuple[str, str]]:
    """Every (anchor lord, level) a P1 transit of `agent` through the sign (0 = Aries) must be read under —
    the verifier's own table (nothing imported from the builder or the rule modules):
      XX.34–35 / XX.37: the agent's OWN transit through its own / exaltation / depression sign — anchor = the agent,
          at MD, AD and PD (the PD level is the specification's flagged extension);
      XX.38: the Sun or Jupiter entering ANOTHER graha's exaltation sign, and the Sun entering another graha's
          depression sign — anchor = that bhukti lord, at AD."""
    from .inventory_verifier import _DEBIL, _EXALT, _OWN, _SIGNS
    sign = _SIGNS[sign_index]
    out: set[tuple[str, str]] = set()
    if sign in _OWN.get(agent, ()) or sign in (_EXALT.get(agent), _DEBIL.get(agent)):
        out |= {(agent, lv) for lv in _LEVELS}
    if agent in ("sun", "jupiter"):
        out |= {(g, "ad") for g in _GRAHAS7 if g != agent and _EXALT.get(g) == sign}
    if agent == "sun":
        out |= {(g, "ad") for g in _GRAHAS7 if g != "sun" and _DEBIL.get(g) == sign}
    return out


def _testimony_lords(natal: dict, lagna: float, event_class: str) -> set[str]:
    """The period lords whose natal relation to the class is `testimony` — from THIS verifier's own relation
    (`inventory_verifier.period_lord_relation`, R11-2): no shared code with the builder's `permission` module."""
    from .inventory_verifier import period_lord_relation
    chart = {"lagna": lagna, "natal": natal}
    return {g for g in _GRAHAS7 if period_lord_relation(g, event_class, chart)["licence"] == "testimony"}


def expected_p1_contacts(position_at, lo, hi, *, excluded_agents) -> list[dict]:
    """The COMPLETE expected P1 contact set over [lo, hi): for every STORED graha and every sign P1 reads it in, the
    maximal in-sign intervals reconstructed from the ephemeris alone (`contact_reconstruct`), each with the anchor set
    it must carry. Independent of the builder's ledger, supports and records. `excluded_agents` is the set of bodies
    the generation's manifest scope says the stored tier never holds as a transiting agent (R9-10: read from the
    manifest by the caller, never a hard-coded exclusion here); the Moon as an ANCHOR lord of another agent's period
    (`expected_p1_anchors`) is unaffected."""
    from . import contact_reconstruct as cr
    out = []
    for agent in _GRAHAS7:
        if agent in excluded_agents:
            continue
        needed = {i: expected_p1_anchors(agent, i) for i in range(12)}
        needed = {i: a for i, a in needed.items() if a}
        if not needed:
            continue
        intervals = cr.cached_residence_intervals(position_at, agent, lo, hi)
        for idx, anchors in needed.items():
            for t_in, t_out in intervals[idx]:
                out.append({"agent": agent, "target": f"span:{idx + 1}", "t_in": t_in, "t_out": t_out,
                            "anchors": anchors})
    return out


def verify_p1_anchors(conn, *, chart_id: str, generation: str, event_class: str, position_at,
                      excluded_agents=None) -> dict:
    """Start from the EXPECTED CONTACT SET (R9-2 iii), not from the records: every P1 contact the ephemeris says exists
    over the class's inventory horizon must be in the ledger and must carry exactly the derived anchor set (minus the
    anchor lords whose period-lord relation is `testimony`, D3). A contact with EVERY anchored record omitted, a contact
    the ledger never wrote, an invented one, an omitted/extra anchor and a wrong level each fail — and a class with
    contacts but no P1 records at all (zero output) fails too. Incomplete geometry evidence (no ephemeris) raises
    `GeometryUnavailable`: no complete-search claim is made.

    `excluded_agents`: None (default; the verification JOB and every other caller) reads the excluded bodies from the generation's
    BOUND manifest scope and refuses an unknown scope (`bound_excluded_agents`); an explicit value is TOLD to the verifier by the
    writer's in-build self-check of a TEST SLICE (whose stored scope is deliberately unknown to every vocabulary), which holds a
    validated marker and passes the DEFAULT scope's exclusion."""
    from . import contact_reconstruct as cr
    from .inventory_verifier import Unverifiable, read_chart
    if position_at is None:
        raise cr.GeometryUnavailable("no ephemeris position source: the complete P1 contact set cannot be certified")
    if not _anchor_columns(conn):
        return {"contacts": 0}                       # the support verifier refuses if P1 records exist here
    hdr = conn.execute("SELECT lower(horizon), upper(horizon) FROM public.ka_gochara_search_inventory"
                       " WHERE chart_id = %s AND generation = %s AND event_class = %s",
                       (chart_id, generation, event_class)).fetchone()
    if hdr is None:
        raise Unverifiable(f"{event_class}: no inventory horizon to certify the contact set over")
    lo, hi = (tuple(hdr.values()) if isinstance(hdr, dict) else tuple(hdr))
    from .inventory_verifier import bound_excluded_agents
    excluded = (bound_excluded_agents(conn, chart_id, generation)    # the bodies come from the MANIFEST's scope
                if excluded_agents is None else tuple(excluded_agents))
    snap = conn.execute(
        "SELECT consumed_fact_ids FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchone()
    if snap is None:
        raise Unverifiable("no snapshot to read the natal positions from")
    natal = read_chart(conn, snap[0] if not isinstance(snap, dict) else next(iter(snap.values())))
    testimony = _testimony_lords(natal["natal"], natal["lagna"], event_class)

    stored = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
        "SELECT c.contact_id::text, c.body, o.canonical_target, c.t_in, c.t_out, c.delta_lambda"
        " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
        "   ON o.physical_object_id = c.physical_object_id"
        " WHERE c.chart_id = %s AND c.generation = %s AND c.relation_kind = 'residence'"
        "   AND o.canonical_target LIKE 'span:%%'", (chart_id, generation)).fetchall()]
    from collections import Counter
    by_contact: dict[str, Counter] = {}
    role_problems: list[str] = []
    for cid, lord, level, role, prov, ruling in (tuple(r.values()) if isinstance(r, dict) else tuple(r)
                                                 for r in conn.execute(
            "SELECT contact_id::text, period_anchor_lord, period_anchor_level, operator_role, provenance, ruling_ref"
            " FROM public.ka_gochara_relationship_record"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = 'P1'"
            "   AND contact_id IS NOT NULL", (chart_id, generation, event_class)).fetchall()):
        by_contact.setdefault(cid, Counter())[(lord, level)] += 1       # R11-2: a MULTISET — a duplicate record counts
        # R9-5: the PD level is explicitly authorised TESTIMONY (own literals); MD and AD are the verse's scored readings
        want = (("testimony", "uncited_extension", PD_RULING) if level == "pd" else ("scored", "verse_cited", None))
        if (role, prov, ruling) != want:
            role_problems.append(f"record on contact {cid} ({lord}, {level}): stored (role, provenance, ruling) "
                                 f"{(role, prov, ruling)} != {want}")

    from . import boundary_match as bm

    def clipped(t_in, t_out):
        return max(t_in, lo), (hi if t_out is None else min(t_out, hi))

    expected = expected_p1_contacts(position_at, lo, hi, excluded_agents=excluded)
    problems: list[str] = []
    matched: set[str] = set()
    for e in expected:
        want = Counter({a: 1 for a in e["anchors"] if a[0] not in testimony})
        hit = None
        for cid, body, target, t_in, t_out, dl in stored:
            if body == e["agent"] and target == e["target"]:
                a, b = clipped(t_in, t_out)
                # the tolerance is DERIVED (R9-9): the contact's own stated accuracy and the body's speed there
                if bm.intervals_agree(position_at, body, (a, b), (e["t_in"], e["t_out"]), bm.accuracy_degrees(dl), lo, hi):
                    hit = cid
                    break
        label = f"{e['agent']} {e['target']} [{e['t_in'].isoformat()}, {e['t_out'].isoformat()})"
        if hit is None:
            problems.append(f"expected contact {label} is not in the ledger (omitted, or its support differs)")
            continue
        matched.add(hit)
        have = by_contact.get(hit, Counter())
        if have != want:
            problems.append(f"contact {label}: anchored records stored {sorted(have.elements())} != derived "
                            f"{sorted(want.elements())} (exact cardinality; a duplicate or missing record fails)")
    for cid in sorted(set(by_contact) - matched):          # P1 records on a contact the ephemeris does not reconstruct
        problems.append(f"contact {cid} carries P1 records but is not a reconstructed in-sign interval")
    problems.extend(role_problems)
    if problems:
        raise RuntimeError(f"P1 anchor verification failed {event_class}: " + "; ".join(problems))
    return {"contacts": len(expected), "reconstructed_contacts": len(expected),
            "guarantee_assumption": cr.GUARANTEE_ASSUMPTION, "named_limit": cr.NAMED_LIMIT,
            "limitations": [PD_LIMITATION]}


__all__ = ["PD_LIMITATION", "PD_RULING", "expected_p1_anchors", "verify_p1_anchors", "verify_p1_support", "verify_p1_house_descriptor"]
