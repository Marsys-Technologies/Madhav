"""Record enumeration for the '5.0' writer (Pravāha A5.3, window_evaluator).

Given an (event_class × path_id, rule_version) grain (pin 5 phase 2) and the
chart context, enumerate the grain's record set as pure data — no DB, no
solves. Transit edges carry their §6.1 physical-object identity
(`PhysicalObjectId`); the occurrence ordinal (hence contact_id) binds only at
contact materialisation, which is when DB rows are written (a transit record
FKs its contact ledger row — kgrr_transit_natal_ck). One record is produced
per CONTACT OCCURRENCE at materialisation; this module enumerates the
distinct (agent, relation, object, role) edges.

Binding decisions (fold into the frozen specs' v1.5 at the A5.5 Codex gate,
flagged to the steward):

  E7. record_id: the DB PK is a UUID; records.py's `sha256:` hex string is
      the same canonical natural key. The writer mints uuid8 (substrate
      pin-4 scheme) over records.py's canonical natural-key bytes — same
      input, DB-typed output.
  E8. Object conventions (kgpo vocab: body ∈ 9 grahas; relation_kind ∈
      residence|aspect|conjunction|…; target point:|span:|star:):
        * house-span target of an agent: (agent, residence|aspect,
          span:sign:<sign>) — aspect-to-span is the aspect point's ingress
          into the span;
        * natal-lord point target: (agent, conjunction|aspect,
          point:<λ_natal full precision>) — O-RX-1's own convention
          ('Mars|conjunction|point:198.52');
        * natal occupancy/ownership rows share the occupant/owner graha's
          residence-span object (role aliases share one root, §1.2 inv 3).
      Nodes never get aspect edges (N-14: nodes cast no dṛṣṭi).
  E9. kgrr_citation_ck: verse_cited ⇒ source_page NOT NULL. Where Stream B's
      catalogue carries source_text but no page (P3: Yavana Jātaka ch.45-48),
      source_page falls back to the cited LOCATOR string — flagged, never
      fabricated.

Deferrals:
  D3. P1 non-node dispositorship and association rows: Stream B's
      P1_RELATION_KINDS marks them uncited_extension/testimony WITHOUT a
      ruling_ref ("pending a native ruling"); kgrr_ruling_ck refuses
      uncited_extension without ruling_ref. Not writable until ruled.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from services.gochara_kernel.substrate import (
    PhysicalObjectId,
    _uuid8_of,
    convention_id_for,
)
from services.gochara_rules import registry as rules_registry
from services.gochara_rules.records import NATURAL_KEY_FIELDS
from services.gochara_rules.registry import (
    CLASS_BY_NAME,
    P3_TRUTH_TABLE,
    ROW_MEMBERSHIP,
    RULE_VERSION,
    signature_houses,
    signature_lords,
)
from services.gochara_rules.frames import SIGN_LORDS, Frame

#: Paths whose enumeration machinery has landed in this increment.
IMPLEMENTED_PATHS = ("P2", "P3", "P4")

#: Frame kinds per class row (P3 truth table; bereavement (father) counts
#: from the 9th — spec §2.2). Everything else is lagna-frame.
_CLASS_AFFECTED_PERSON = {"bereavement": "father"}

_NODE_AGENTS = frozenset({"Rahu", "Ketu"})

_OBJECT_KIND = {"span": "house_span", "point": "degree_point"}


@dataclass(frozen=True)
class RecordEdge:
    """One enumerated (agent, relation, object, role) edge of a grain —
    the template from which per-occurrence records are minted at contact
    materialisation (transit) or directly (natal-fact rows)."""

    event_class: str
    affected_person: str
    frame_kind: str
    frame_arg: str | None
    agent: str                      # DB lowercase graha
    relation: str
    obj: PhysicalObjectId
    object_kind: str
    object_role: str
    path_id: str
    rule_version: str
    provenance: str
    operator_role: str
    ruling_ref: str | None
    source_text: str | None
    source_page: str | None
    transit: bool                   # True ⇒ per-occurrence, contact_id bound
                                    # at materialisation; False ⇒ natal fact

    def natural_key(self, *, chart_id: str, generation: str,
                    contact_id: str | None,
                    prerequisites: list[list[str]],
                    source_text: str | None) -> dict:
        key = {
            "chart_id": chart_id,
            "generation": generation,
            "event_class": self.event_class,
            "affected_person": self.affected_person,
            "frame": (self.frame_kind if self.frame_arg is None
                      else f"{self.frame_kind}:{self.frame_arg}"),
            "agent": self.agent,
            "relation": self.relation,
            "object_id": str(self.obj.uuid),
            "object_role": self.object_role,
            "contact_id": contact_id,
            "path_id": self.path_id,
            "rule_version": self.rule_version,
            "prerequisites": prerequisites,
            "source_text": source_text,
        }
        assert set(key) == set(NATURAL_KEY_FIELDS)
        return key


def record_uuid(natural_key: dict):
    """E7: uuid8 over records.py's canonical natural-key bytes (same input,
    DB-typed output — never the WP1 floored-minute scheme)."""
    canonical = json.dumps(natural_key, sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False)
    return _uuid8_of(canonical.encode("utf-8"))


def _span_target(sign: str) -> str:
    return f"span:sign:{sign.lower()}"


def _point_target(lam: float) -> str:
    return f"point:{float(lam)!r}"


def _path_citation(path_id: str) -> tuple[str | None, str | None]:
    src = rules_registry.RULE_PATHS[(path_id, RULE_VERSION)]
    text = src.get("source_text")
    page = src.get("source_page")
    if page is None and path_id == "P3":
        page = "Yavana Jātaka ch.45-48"   # E9 locator fallback — flagged
    return text, page


def _class_frame(event_class: str) -> tuple[str, str | None]:
    row_key = ROW_MEMBERSHIP[event_class]
    row = P3_TRUTH_TABLE.get(row_key) if row_key not in (None, "unknown") else None
    if row and "H_anchor_house" in row:
        return "bhavat_bhavam", str(row["H_anchor_house"])
    return "lagna", None


def enumerate_p3_edges(event_class: str, chart: dict,
                       convention_id: str | None = None) -> list[RecordEdge]:
    """P3 (S-03): per agent, residence + aspect edges on each h ∈ H, and
    conjunction + aspect edges on each ℓ ∈ L(H)'s natal point; plus the
    māraka-of-house TESTIMONY rows (D-PADMIT). H unknown ⇒ [] (the class's
    admission is unqualified, recorded by the caller — never false)."""
    cid = convention_id or convention_id_for()
    if event_class == "birth_anchor":
        raise ValueError("birth_anchor is excluded from enumeration entirely (O-CF-N6)")
    H = signature_houses(event_class, chart)
    if H is None:
        return []
    L = signature_lords(event_class, chart) or frozenset()
    frame_kind, frame_arg = _class_frame(event_class)
    person = _CLASS_AFFECTED_PERSON.get(event_class, "native")
    text, page = _path_citation("P3")
    edges: list[RecordEdge] = []
    natal = chart["natal"]
    for agent, agent_lc in _AGENTS:
        for h in sorted(H):
            for relation in ("residence", "aspect"):
                if relation == "aspect" and agent in _NODE_AGENTS:
                    continue  # N-14: nodes cast no dṛṣṭi
                edges.append(RecordEdge(
                    event_class=event_class, affected_person=person,
                    frame_kind=frame_kind, frame_arg=frame_arg,
                    agent=agent_lc, relation=relation,
                    obj=PhysicalObjectId(
                        body=agent_lc, relation_kind=relation,
                        canonical_target=_span_target(h), convention_id=cid),
                    object_kind="house_span", object_role="signature_house",
                    path_id="P3", rule_version=RULE_VERSION,
                    provenance="verse_cited", operator_role="scored",
                    ruling_ref=None, source_text=text, source_page=page,
                    transit=True))
        for lord in sorted(L):
            lam = natal.get(lord)
            if lam is None:
                continue   # operand missing ⇒ named upstream, never solved
            for relation in ("conjunction", "aspect"):
                if relation == "aspect" and agent in _NODE_AGENTS:
                    continue
                edges.append(RecordEdge(
                    event_class=event_class, affected_person=person,
                    frame_kind=frame_kind, frame_arg=frame_arg,
                    agent=agent_lc, relation=relation,
                    obj=PhysicalObjectId(
                        body=agent_lc, relation_kind=relation,
                        canonical_target=_point_target(lam), convention_id=cid),
                    object_kind="degree_point", object_role="lord",
                    path_id="P3", rule_version=RULE_VERSION,
                    provenance="verse_cited", operator_role="scored",
                    ruling_ref=None, source_text=text, source_page=page,
                    transit=True))
    edges.extend(_maraka_rows(event_class, chart, cid, frame_kind, frame_arg,
                              person))
    return edges


def _maraka_rows(event_class: str, chart: dict, cid: str,
                 frame_kind: str, frame_arg: str | None,
                 person: str) -> list[RecordEdge]:
    """P3 māraka-of-house testimony rows (D-PADMIT): the lords of the class's
    māraka houses, natal-fact rows (relation ownership, role maraka_of_house,
    testimony — never scored)."""
    row_key = ROW_MEMBERSHIP[event_class]
    row = P3_TRUTH_TABLE.get(row_key) if row_key not in (None, "unknown") else None
    if not row:
        return []
    if "maraka_lords_of_offsets" in row:
        anchor = Frame("bhavat_bhavam", row["H_anchor_house"])
        from services.gochara_rules.registry import house_span_sign
        houses = {house_span_sign(off, anchor, chart)
                  for off in row["maraka_lords_of_offsets"]}
    else:
        from services.gochara_rules.registry import house_span_sign
        houses = {house_span_sign(h, Frame("lagna"), chart)
                  for h in row.get("maraka_lords_of", set())}
    text, page = _path_citation("P3")
    out = []
    for sign in sorted(houses):
        lord = SIGN_LORDS[sign]
        out.append(RecordEdge(
            event_class=event_class, affected_person=person,
            frame_kind=frame_kind, frame_arg=frame_arg,
            agent=lord.lower(), relation="ownership",
            obj=PhysicalObjectId(
                body=lord.lower(), relation_kind="residence",
                canonical_target=_span_target(sign), convention_id=cid),
            object_kind="house_span", object_role="maraka_of_house",
            path_id="P3", rule_version=RULE_VERSION,
            provenance="uncited_extension", operator_role="testimony",
            ruling_ref="D-PADMIT", source_text=text, source_page=page,
            transit=False))
    return out


def enumerate_p4_edges(event_class: str, chart: dict,
                       convention_id: str | None = None) -> list[RecordEdge]:
    """P4 (R3-S02): the P3 house/lord contact edges restricted to agents
    Jupiter and Saturn. One rule — union within an agent, AND across agents
    (admission is evaluated over occurrences, not here)."""
    return [e for e in enumerate_p3_edges(event_class, chart, convention_id)
            if e.agent in ("jupiter", "saturn") and e.operator_role == "scored"]


def enumerate_p2_edges(event_class: str, chart: dict,
                       convention_id: str | None = None) -> list[RecordEdge]:
    """P2 (Moon-frame gochara-phala): the PINNED edge set, per O-RP-5a/5b
    and the RQ-5 phase split:

      * SCORED adverse residence (D-RQ5 shape): Sun/Mars/Jupiter in 12/8/1
        from janma-rāśi, and Saturn in the 8th — evidence FOR the adverse
        classes, never attached to gain classes (O-RP-5a);
      * TESTIMONY Sade-Sati phase rows (S-04/R2-S05): Saturn in 12/1/2 from
        the Moon — operator_role testimony, ZERO score effect (O-RP-5b;
        scoring with vs without is bit-identical).

    The per-planet FAVOURABLE-house tables (Phaladīpikā XXVI.1–8, PG321-323)
    are Stream B registry content not yet landed — a named gap, reported to
    the steward; P2 grains for gain classes enumerate empty until then
    (never a fabricated house set). Frame: moon; affected_person: native
    (P2 licenses the native's fortune only)."""
    from services.gochara_rules.frames import Frame, nth_sign_from

    cid = convention_id or convention_id_for()
    if event_class == "birth_anchor":
        raise ValueError("birth_anchor is excluded from enumeration entirely (O-CF-N6)")
    if CLASS_BY_NAME[event_class]["polarity"] != "adverse":
        return []
    text, page = _path_citation("P2")
    moon_frame = Frame("moon")
    # (agent, house, testimony?) — the RQ-5 split.
    plan = [("Sun", h, False) for h in (12, 8, 1)]
    plan += [("Mars", h, False) for h in (12, 8, 1)]
    plan += [("Jupiter", h, False) for h in (12, 8, 1)]
    plan += [("Saturn", 8, False)]
    plan += [("Saturn", h, True) for h in (12, 1, 2)]  # Sade-Sati phases
    edges: list[RecordEdge] = []
    for agent, house, testimony in plan:
        agent_lc = agent.lower()
        sign = nth_sign_from(moon_frame, house, chart)
        edges.append(RecordEdge(
            event_class=event_class, affected_person="native",
            frame_kind="moon", frame_arg=None,
            agent=agent_lc, relation="residence",
            obj=PhysicalObjectId(
                body=agent_lc, relation_kind="residence",
                canonical_target=_span_target(sign), convention_id=cid),
            object_kind="house_span", object_role="signature_house",
            path_id="P2", rule_version=RULE_VERSION,
            provenance=("uncited_extension" if testimony else "verse_cited"),
            operator_role=("testimony" if testimony else "scored"),
            ruling_ref=("D-PADMIT" if testimony else None),
            source_text=text, source_page=page,
            transit=True))
    return edges


def enumerate_edges(event_class: str, path_id: str, chart: dict,
                    convention_id: str | None = None) -> list[RecordEdge]:
    """The grain's edge set. Unimplemented paths refuse LOUDLY — a grain is
    never silently empty (unknown is a state, never an omission)."""
    if event_class not in CLASS_BY_NAME:
        raise ValueError(f"unknown event class {event_class!r}")
    if path_id == "P2":
        return enumerate_p2_edges(event_class, chart, convention_id)
    if path_id == "P3":
        return enumerate_p3_edges(event_class, chart, convention_id)
    if path_id == "P4":
        return enumerate_p4_edges(event_class, chart, convention_id)
    if path_id in ("P1", "P5"):
        raise NotImplementedError(
            f"{path_id} record enumeration lands in a later window_evaluator "
            "increment — never a silent empty grain"
        )
    raise ValueError(f"unknown path {path_id!r}")


_AGENTS = tuple(
    (title, title.lower())
    for title in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                  "Saturn", "Rahu", "Ketu")
)


__all__ = [
    "IMPLEMENTED_PATHS",
    "RecordEdge",
    "enumerate_edges",
    "enumerate_p3_edges",
    "enumerate_p4_edges",
    "record_uuid",
]
