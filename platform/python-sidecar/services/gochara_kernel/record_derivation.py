"""Independent, COMPLETE derivation of a path's relationship RECORDS (Codex round 10, R10-1).

The inventory verifier re-derives the search OBLIGATIONS and the ledger; `contact_certify` certifies the stored CONTACTS
against an ephemeris reconstruction. Until now nothing derived the RECORDS from those two — the window gate derived its
expected windows from the stored admitted records, so deleting a path's records (and their windows) made expected and
stored emptiness agree. This module closes that: from nothing but

    the verifier-derived obligations  ×  the certified stored contacts  ×  the bound natal chart  ×  the sealed rules,

it derives, for every included materialised path, each record that MUST exist (identity, frame, person, house, operator
role, provenance, ruling, support, every declared prerequisite RESULT and the admission they imply), and compares both
directions with the stored records, including an entirely empty stored path.

It imports nothing from the builder (`evaluator`, `record_store`, `ka_gochara_v5`) and none of the rule modules'
admission code: the roles, rulings, favourable-house sets and frames are this verifier's own tables
(`inventory_verifier`), the admission is the 1155 F5 rule restated, and the P1 period-lord relation is the one rule-module
call the existing P1 verifiers already make.

P1's record SET is certified by `record_verifier.verify_p1_anchors` (expected contacts × anchors, both directions) and its
support / `period_running_at` result by `verify_p1_support`; `verify_p1_results` adds the remaining declared predicates,
the operator role / provenance / ruling and the admission. All-NULL policy (R10-2): every record result field is checked
against the manifest's `result_policy`.

Named limits: the derivation is exactly as independent as the obligations and the certified contacts it stands on; a
record the builder was entitled to withhold for an unreadable operand is not expected (the verifier reads the same L1
facts and refuses `Unverifiable` rather than guess)."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

#: the record result fields the all-NULL policy forbids a number in (and the token an unevaluated record carries)
RESULT_NUMERIC_FIELDS = ("evidence_for_occurrence", "evidence_against_occurrence", "severity")
UNQUALIFIED = "unqualified"

#: ruling carried by the testimony (D-PADMIT) rows and the P1 PD-level readings — the verifier's OWN literals
RULING_PADMIT = "D-PADMIT"
RULING_P1_PD = "ST-P1-PD-TESTIMONY-20261002"

_OBLIGATION_FIELDS = ("event_class", "path", "version", "agent", "relation", "role", "target", "frame", "person")


def parse_obligation(text: str) -> dict:
    parts = text.split("|")
    if len(parts) != len(_OBLIGATION_FIELDS):
        raise ValueError(f"malformed obligation {text!r}")
    return dict(zip(_OBLIGATION_FIELDS, parts))


def _rows(cur) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in cur.fetchall()]


def admission_of(results: Sequence[str]) -> str:
    """1155 F5: any false ⇒ not_admitted; else any unknown/unevaluated ⇒ unqualified; else admitted."""
    if any(r == "false" for r in results):
        return "not_admitted"
    if any(r != "true" for r in results):
        return "unqualified"
    return "admitted"


def _frame_anchor(frame: str, chart: Mapping[str, Any]) -> int | None:
    from .inventory_verifier import _sign_index
    lagna = _sign_index(chart["lagna"])
    if frame == "lagna":
        return lagna
    if frame == "moon":
        return _sign_index(chart["natal"]["moon"])
    if frame.startswith("bhavat_bhavam:"):
        return (lagna + int(frame.split(":", 1)[1]) - 1) % 12
    return None


def _target_sign(target: str) -> int:
    from .inventory_verifier import _sign_index
    kind, arg = target.split(":", 1)
    return int(arg) - 1 if kind == "span" else _sign_index(float(arg))


def _iv_role(path: str, agent: str, relation: str, role: str, house: int | None, polarity: str,
             sealed: tuple[str, str | None]) -> tuple[str, str, str | None]:
    """(operator_role, provenance, ruling): the testimony classes are this verifier's own restatement of the cited
    classification; a SCORED record carries the provenance/ruling of its path as SEALED in the rule registry (F3)."""
    if path == "p3" and role == "maraka_of_house":
        return "testimony", "uncited_extension", RULING_PADMIT
    if path == "p2" and polarity == "adverse" and agent == "saturn" and house in (12, 1, 2):
        # Saturn's 12/1/2 from the Moon are the Sade-Sati PHASE rows (testimony); its 8th is scored
        return "testimony", "uncited_extension", RULING_PADMIT
    return "scored", sealed[0], sealed[1]


def sealed_path_provenance(conn, path_id: str, rule_version: str) -> tuple[str, str | None]:
    rows = _rows(conn.execute("SELECT provenance, ruling_ref FROM public.ka_gochara_rule_path"
                              " WHERE path_id = %s AND rule_version = %s", (path_id, rule_version)))
    if not rows:
        raise RuntimeError(f"{path_id}@{rule_version} is not a sealed rule path")
    return rows[0][0], rows[0][1]


def declared_predicates(conn, path_id: str, rule_version: str) -> list[str]:
    """The path's DECLARED prerequisite membership, from the sealed rule registry (1154) — not from any record."""
    return [r[0] for r in _rows(conn.execute(
        "SELECT predicate_id FROM public.ka_gochara_rule_path_prerequisite WHERE path_id = %s AND rule_version = %s"
        " ORDER BY ordinal", (path_id, rule_version)))]


def stored_contacts(conn, chart_id: str, generation: str) -> list[dict]:
    return [{"id": r[0], "body": r[1], "relation": r[2], "target": r[3], "t_in": r[4], "t_out": r[5]}
            for r in _rows(conn.execute(
                "SELECT c.contact_id::text, c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out"
                " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
                "   ON o.physical_object_id = c.physical_object_id"
                " WHERE c.chart_id = %s AND c.generation = %s ORDER BY c.contact_id::text", (chart_id, generation)))]


_TRANSIT = ("residence", "aspect", "conjunction")


def derive_path_records(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str,
                        obligations: Sequence[str], chart: Mapping[str, Any], horizon_hi, contacts: Sequence[dict]
                        ) -> list[dict]:
    """The records path `path_id` (P2/P3/P4) MUST hold: one per (obligation × stored contact of its
    (agent, relation, target)) for a transit obligation, one per natal-fact obligation."""
    from .inventory_verifier import _ADVERSE, _FAVOURABLE, _POLARITY
    path = path_id.lower()
    declared = declared_predicates(conn, path_id, rule_version)
    sealed = sealed_path_provenance(conn, path_id, rule_version)
    polarity = _POLARITY.get(event_class, "")
    by_obj: dict[tuple, list[dict]] = {}
    for c in contacts:
        by_obj.setdefault((c["body"], c["relation"], c["target"]), []).append(c)
    expected: list[dict] = []
    for text in obligations:
        ob = parse_obligation(text)
        if ob["path"] != path or ob["version"] != rule_version.lower():
            continue
        agent, relation, role, target, frame = ob["agent"], ob["relation"], ob["role"], ob["target"], ob["frame"]
        anchor = _frame_anchor(frame, chart)
        if relation in _TRANSIT:
            for c in by_obj.get((agent, relation, target), []):
                if anchor is None:
                    continue                                    # no resolvable frame ⇒ no record is minted
                house = (_target_sign(target) - anchor) % 12 + 1
                expected.append({"agent": agent, "relation": relation, "role": role, "target": target,
                                 "frame": frame, "person": ob["person"], "contact": c["id"], "house": house,
                                 "support": [(c["t_in"], c["t_out"] if c["t_out"] is not None else horizon_hi)],
                                 "natal": False})
        else:                                                    # a natal-fact obligation: ONE atemporal record
            expected.append({"agent": agent, "relation": relation, "role": role, "target": target, "frame": frame,
                             "person": ob["person"], "contact": None, "house": None, "support": [], "natal": True})
    # prerequisite results, role/provenance/ruling, admission
    for rec in expected:
        op_role, prov, ruling = _iv_role(path, rec["agent"], rec["relation"], rec["role"], rec["house"], polarity,
                                             sealed)
        rec.update(operator_role=op_role, provenance=prov, ruling=ruling, results={})
    if path == "p4":
        by_agent: dict[str, list[tuple]] = {}
        for rec in expected:
            by_agent.setdefault(rec["agent"], []).extend(rec["support"])
    for rec in expected:
        for pid in declared:
            if pid == "house_from_moon":
                cited = set(_FAVOURABLE.get(rec["agent"], ())) | set(_ADVERSE.get(rec["agent"], ()))
                rec["results"][pid] = ("unknown" if rec["frame"] != "moon" or rec["house"] is None
                                       else ("true" if rec["house"] in cited else "false"))
            elif pid == "p3_contact_house_or_lord":
                rec["results"][pid] = "unknown" if rec["natal"] else "true"      # obligations ARE H ∪ L(H)
            elif pid == "p4_double_transit":
                other = {"jupiter": "saturn", "saturn": "jupiter"}.get(rec["agent"])
                lo, hi = rec["support"][0]
                rec["results"][pid] = ("unknown" if other is None else
                                       ("true" if any(a < hi and lo < b for a, b in by_agent.get(other, [])) else "false"))
            else:                                    # a declared predicate this verifier has no derivation for
                from .inventory_verifier import Unverifiable
                raise Unverifiable(f"{event_class}/{path_id}: declared prerequisite {pid!r} has no independent derivation "
                                   "in the verifier — the path's records cannot be verified")
        rec["admission"] = admission_of([rec["results"][p] for p in declared])
    return expected


def stored_path_records(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str):
    recs = []
    for (rid, agent, relation, role, target, contact, op_role, prov, ruling, adm, house, fkind, farg, person,
         state, supports, ev_for, ev_against, severity, valence) in _rows(conn.execute(
            "SELECT r.record_id::text, r.agent, r.relation, r.object_role, o.canonical_target, r.contact_id::text,"
            " r.operator_role, r.provenance, r.ruling_ref, r.admission_state, r.house_from_frame, r.frame_kind,"
            " r.frame_arg, r.affected_person, r.temporal_support_state, r.temporal_support_intervals,"
            " r.evidence_for_occurrence, r.evidence_against_occurrence, r.severity, r.outcome_valence_for_native"
            " FROM public.ka_gochara_relationship_record r JOIN public.ka_gochara_physical_object o"
            "   ON o.physical_object_id = r.object_id"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s AND r.path_id = %s"
            "   AND r.rule_version = %s ORDER BY r.record_id::text",
            (chart_id, generation, event_class, path_id, rule_version))):
        recs.append({"id": rid, "agent": agent, "relation": relation, "role": role, "target": target,
                     "contact": contact, "operator_role": op_role, "provenance": prov, "ruling": ruling,
                     "admission": adm, "house": house, "frame": fkind if farg is None else f"{fkind}:{farg}",
                     "person": person, "state": state,
                     "support": [(x.lower, x.upper) for x in (supports or [])],
                     "ev_for": ev_for, "ev_against": ev_against, "severity": severity, "valence": valence})
    ids = [r["id"] for r in recs]
    results: dict[str, dict[str, str]] = {}
    if ids:
        for rid, pid, res in _rows(conn.execute(
                "SELECT record_id::text, predicate_id, result FROM public.ka_gochara_record_prerequisite"
                " WHERE record_id = ANY(%s::uuid[])", (ids,))):
            results.setdefault(rid, {})[pid] = res
    for r in recs:
        r["results"] = results.get(r["id"], {})
    return recs


def result_policy_problems(records: Sequence[dict], policy: str | None) -> list[str]:
    """R10-2: the manifest's result policy governs EVERY record result field. Under `all_null_candidate/1` — and, because
    no independent derivation of a record number exists, under `window_qualification/1` as well — a record carries NULL
    evidence/severity and the `unqualified` valence."""
    problems = []
    for r in records:
        bad = [f for f, v in (("evidence_for_occurrence", r["ev_for"]), ("evidence_against_occurrence", r["ev_against"]),
                              ("severity", r["severity"])) if v is not None]
        if bad:
            problems.append(f"record {r['id']}: {'/'.join(bad)} carry a number under result policy {policy!r}")
        if r["valence"] != UNQUALIFIED:
            problems.append(f"record {r['id']}: outcome valence {r['valence']!r} is not {UNQUALIFIED!r} under result "
                            f"policy {policy!r}")
    return problems


def compare(expected: Sequence[dict], stored: Sequence[dict], *, path_id: str, event_class: str) -> list[str]:
    problems: list[str] = []
    key = lambda r: (r["agent"], r["relation"], r["role"], r["target"], r["contact"])           # noqa: E731
    want = {}
    for e in expected:
        want.setdefault(key(e), []).append(e)
    have = {}
    for s in stored:
        have.setdefault(key(s), []).append(s)
    for k in sorted(want, key=str):
        if k not in have:
            problems.append(f"expected record {k} is not stored")
        elif len(have[k]) != len(want[k]):
            problems.append(f"record {k}: {len(have[k])} stored, {len(want[k])} expected")
    for k in sorted(have, key=str):
        if k not in want:
            problems.append(f"stored record {k} ({have[k][0]['id']}) is not a record any obligation × certified contact "
                            "implies")
    for k in sorted(set(want) & set(have), key=str):
        e, s = want[k][0], have[k][0]
        for field, ev, sv in (("house", e["house"], s["house"]), ("operator_role", e["operator_role"], s["operator_role"]),
                              ("provenance", e["provenance"], s["provenance"]), ("ruling", e["ruling"], s["ruling"]),
                              ("frame", e["frame"], s["frame"]), ("person", e["person"], s["person"]),
                              ("admission", e["admission"], s["admission"]), ("results", e["results"], s["results"])):
            if ev != sv:
                problems.append(f"record {k} ({s['id']}): {field} stored {sv!r}, derived {ev!r}")
        want_state = "uncomputed" if e["natal"] else "computed"
        if s["state"] != want_state:
            problems.append(f"record {k} ({s['id']}): support state {s['state']!r}, derived {want_state!r}")
        elif not e["natal"] and sorted(s["support"]) != sorted(e["support"]):
            problems.append(f"record {k} ({s['id']}): stored support {s['support']} != the contact span {e['support']}")
    return problems


def derived_windows(expected: Sequence[dict], path_id: str) -> list[tuple]:
    """The windows the DERIVED admitted scored records imply (never the stored ones): the connected union of their
    supports; P4 — the intersection of the Jupiter and Saturn unions."""
    from .window_gate import _intersect, _union
    spans = [(r["agent"], lo, hi) for r in expected
             if r["admission"] == "admitted" and r["operator_role"] == "scored" for lo, hi in r["support"]]
    if path_id == "P4":
        by = {"jupiter": [], "saturn": []}
        for agent, lo, hi in spans:
            if agent in by:
                by[agent].append((lo, hi))
        return _intersect(_union(by["jupiter"]), _union(by["saturn"]))
    return _union([(lo, hi) for _a, lo, hi in spans])


def verify_path_records(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str,
                        obligations: Sequence[str], chart: Mapping[str, Any], horizon_hi, policy: str | None) -> dict:
    """P2/P3/P4: derive every record that must exist and compare both directions (an empty stored path included).
    Returns the DERIVED windows for the window gate. Raises RuntimeError naming each disagreement."""
    contacts = stored_contacts(conn, chart_id, generation)
    expected = derive_path_records(conn, chart_id=chart_id, generation=generation, event_class=event_class,
                                   path_id=path_id, rule_version=rule_version, obligations=obligations, chart=chart,
                                   horizon_hi=horizon_hi, contacts=contacts)
    stored = stored_path_records(conn, chart_id=chart_id, generation=generation, event_class=event_class,
                                 path_id=path_id, rule_version=rule_version)
    problems = compare(expected, stored, path_id=path_id, event_class=event_class)
    problems += result_policy_problems(stored, policy)
    if problems:
        raise RuntimeError(f"record derivation failed {event_class}/{path_id}@{rule_version}: " + "; ".join(problems))
    return {"records": len(stored), "derived_windows": derived_windows(expected, path_id)}


# ── P1 ───────────────────────────────────────────────────────────────────────────────────────────────

def verify_p1_results(conn, *, chart_id: str, generation: str, event_class: str, rule_version: str, chart: Mapping[str, Any],
                      policy: str | None) -> dict:
    """R11-2: every stored P1 record against an independent derivation of ALL its semantic fields. The record SET with its exact
    CARDINALITY (per contact, the multiset of (anchor lord, level)) is certified by `verify_p1_anchors`; the support and the
    `period_running_at` result by `verify_p1_support`; here, per record: agent, relation, target and contact identity (the
    record states exactly its contact's body / relation / object), affected PERSON, object ROLE and KIND, frame, anchor,
    EXACTLY the declared prerequisites (no missing, no extra, no duplicate row), every prerequisite's truth, the admission
    they imply, and the operator role / provenance / ruling — against values this verifier derives with its OWN period-lord
    relation (`inventory_verifier.period_lord_relation`: no `gochara_rules.permission` code, an import test holds the line)."""
    from .inventory_verifier import Unverifiable, _frame_person, period_lord_relation
    declared = declared_predicates(conn, "P1", rule_version)
    stored = stored_path_records(conn, chart_id=chart_id, generation=generation, event_class=event_class,
                                 path_id="P1", rule_version=rule_version)
    meta = {r[0]: r[1:] for r in _rows(conn.execute(
        "SELECT r.record_id::text, r.period_anchor_lord, r.period_anchor_level, r.object_kind,"
        " (SELECT count(*) FROM public.ka_gochara_record_prerequisite p WHERE p.record_id = r.record_id)"
        " FROM public.ka_gochara_relationship_record r WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
        " AND r.path_id = 'P1' AND r.rule_version = %s", (chart_id, generation, event_class, rule_version)))}
    problems = result_policy_problems(stored, policy)
    contacts = {c["id"]: c for c in stored_contacts(conn, chart_id, generation)}
    frame, person = _frame_person(event_class)
    for r in stored:
        lord, level, kind, n_prereq = meta.get(r["id"], (None, None, None, 0))
        c = contacts.get(r["contact"])
        if c is None:
            problems.append(f"record {r['id']}: its contact {r['contact']} is not a stored contact")
        elif (r["agent"], r["relation"], r["target"]) != (c["body"], c["relation"], c["target"]):
            problems.append(f"record {r['id']}: states ({r['agent']}, {r['relation']}, {r['target']}) but its contact is "
                            f"({c['body']}, {c['relation']}, {c['target']})")
        elif r["relation"] != "residence":
            problems.append(f"record {r['id']}: P1 records are transit RESIDENCE readings, not {r['relation']!r}")
        for field, got, want in (("affected person", r["person"], person), ("object role", r["role"], "period_lord"),
                                 ("object kind", kind, "house_span"), ("frame", r["frame"], "dasha_lord")):
            if got != want:
                problems.append(f"record {r['id']}: {field} {got!r}, derived {want!r}")
        if lord is None or level not in ("md", "ad", "pd"):
            problems.append(f"record {r['id']}: anchor ({lord!r}, {level!r}) is not an anchor")
        rel = period_lord_relation(str(lord), event_class, chart)
        want = {"natal_bhava_relationship": ("unknown" if rel["relation"] == "unknown"
                                             else ("true" if rel["licence"] in ("scored", "testimony") else "false")),
                "transit_relation": "true" if c is not None else "false"}
        got = r["results"]
        if n_prereq != len(declared) or sorted(got) != sorted(declared):
            problems.append(f"record {r['id']}: prerequisite rows {n_prereq} / predicates {sorted(got)} are not exactly the "
                            f"declared {sorted(declared)}")
        for pid in declared:
            if pid == "period_running_at":
                continue                                            # verify_p1_support's (derived from the daśā rows)
            if pid not in want:
                raise Unverifiable(f"P1: declared prerequisite {pid!r} has no independent derivation in the verifier")
            if got.get(pid) != want[pid]:
                problems.append(f"record {r['id']}: {pid} stored {got.get(pid)!r}, derived {want[pid]!r}")
        results = [got.get(p, "unknown") if p == "period_running_at" else want.get(p, "unknown") for p in declared]
        if r["admission"] != admission_of(results):
            problems.append(f"record {r['id']}: admission {r['admission']!r}, the results imply {admission_of(results)!r}")
        pd = level == "pd"
        want_role = ("testimony", "uncited_extension", RULING_P1_PD) if pd else ("scored", "verse_cited", None)
        if (r["operator_role"], r["provenance"], r["ruling"]) != want_role:
            problems.append(f"record {r['id']}: role/provenance/ruling {(r['operator_role'], r['provenance'], r['ruling'])}"
                            f" != derived {want_role} (anchor level {level})")
    if problems:
        raise RuntimeError(f"P1 record-result verification failed {event_class}: " + "; ".join(problems))
    return {"records": len(stored)}


__all__ = ["RESULT_NUMERIC_FIELDS", "UNQUALIFIED", "admission_of", "compare", "declared_predicates", "derive_path_records",
           "derived_windows", "parse_obligation", "result_policy_problems", "stored_contacts", "stored_path_records",
           "verify_p1_results", "verify_path_records"]
