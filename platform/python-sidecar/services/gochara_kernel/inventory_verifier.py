"""AM-5 INDEPENDENT inventory verifier (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5 §AM-5
item 4; new oracle O-RP-9).

The seal requires, per class, a verification row whose digest equals the stored
`inventory_digest`. SQL checks only presence and equality; that the inventory is the RIGHT
one is THIS module's job: a SEPARATE derivation path that re-derives the class's inventory
from the spec text and the snapshot's L1 facts and computes the preimage/digest itself.

INDEPENDENCE RULES (a process property — reviewed, not provable in SQL):
  * imports NOTHING from the builder: not inventory.py, evaluator.py, inventory_store.py,
    substrate.py, targets.py or record_store.py, and no `gochara_rules` function;
  * carries its OWN copy of the spec §2.2 class table, sign/graha vocabulary, target
    grammar and UUIDv8 — so a misreading in either path surfaces as a digest mismatch
    instead of being copied from one into the other;
  * reads facts straight from `chart_facts` by the snapshot's consumed ids.

WHAT IT CAN VOUCH FOR (honestly): P3 and P4 are derived from the spec's explicit Boolean
form (S-03 / R3-S02); an `excluded` pin is verified against the rulings the verifier is
GIVEN (never read back from the pin it is checking). P1, P2 and P5's enumerations are not
yet independently derivable here: asking for them raises `Unverifiable` — a class that
includes them gets NO verification row, so it cannot seal. A verifier that cannot derive a
path must not vouch for it.

The named residual stays named: if this module and the builder share a misreading of the
doctrine, nothing here (or in SQL) can detect it.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

VERIFIER_ID = "ka_gochara_inventory_verifier"
VERIFIER_VERSION = "1.0"


class Unverifiable(RuntimeError):
    """The verifier has no independent derivation for this class/path — it refuses to
    vouch (no verification row is written)."""


# ── the verifier's OWN vocabulary (spec §2.2; not imported) ──────────────────

_SIGNS = ("aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
          "sagittarius", "capricorn", "aquarius", "pisces")
_SIGN_LORD = {"aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
              "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
              "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
              "pisces": "jupiter"}
_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
_NODES = ("rahu", "ketu")      # agents and targets, but they cast no dṛṣṭi (N-14)
_FACT_SUBJECT = {"SUN": "sun", "MOON": "moon", "MAR": "mars", "MER": "mercury",
                 "JUP": "jupiter", "VEN": "venus", "SAT": "saturn",
                 "RAH_MEAN": "rahu", "KET_MEAN": "ketu"}

# spec §2.2 per-class table: (house numbers of H, anchor house or None, māraka-lord
# houses). With an anchor, the numbers count FROM that house (bhavat_bhavam).
_CLASS = {
    "marriage": ({7}, None, {2, 7}), "romantic_start": ({7}, None, {2, 7}),
    "separation": ({7, 12, 6}, None, {2, 7}),
    "bereavement": ({1, 2, 7, 8}, 9, {2, 7}),
    "childbirth": ({5}, None, set()),
    "career_entry": ({10, 6}, None, set()), "career_advancement": ({10, 6}, None, set()),
    "career_change": ({10, 6}, None, set()), "career_setback": ({10, 6}, None, set()),
    "education_milestone": ({4, 5}, None, set()), "exam_outcome": ({4, 5}, None, set()),
    "major_gain": ({11, 2}, None, set()), "major_loss": ({12, 8}, None, set()),
    "relocation": ({4, 12, 9}, None, set()), "travel_event": ({4, 12, 9}, None, set()),
    "illness_acute": ({6, 8, 12}, None, set()), "chronic_onset": ({6, 8, 12}, None, set()),
    "surgery": ({6, 8, 12}, None, set()),
}
_UNKNOWN_H = frozenset({"achievement_recognition", "business_launch",
                        "financial_deception", "foreign_settlement", "parental_event",
                        "property_acquisition", "psychological_arc", "spiritual_turn"})
_H_DEPENDENT = ("p1", "p3", "p4")


def _uuidv8(text: str) -> str:
    b = bytearray(hashlib.sha256(text.encode("utf-8")).digest()[:16])
    b[6] = (b[6] & 0x0F) | 0x80
    b[8] = (b[8] & 0x3F) | 0x80
    h = b.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _point(lam: float) -> str:
    from decimal import Decimal
    text = repr(float(lam) % 360.0)
    if "e" in text or "E" in text:
        text = format(Decimal(text), "f")
    return f"point:{text}"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── facts: straight from chart_facts by the snapshot's consumed ids ──────────

def read_chart(conn: Any, fact_ids: Sequence[str]) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT fact_subject, fact_value_num FROM public.chart_facts"
        " WHERE fact_id = ANY(%s::text[])", (list(fact_ids),)).fetchall()
    lagna, natal = None, {}
    for subj, num in rows:
        if num is None:
            continue
        if subj == "LAGNA":
            lagna = float(num)
        elif subj in _FACT_SUBJECT:
            natal[_FACT_SUBJECT[subj]] = float(num)
    missing = [s for s in ("lagna",) if lagna is None] + [g for g in _GRAHAS if g not in natal]
    if missing:
        raise Unverifiable(f"the snapshot's consumed facts lack {missing}: nothing to derive from")
    return {"lagna": lagna, "natal": natal}


def _sign_index(lon: float) -> int:
    return int((lon % 360.0) // 30.0)


def _house_sign(house: int, anchor_sign: int) -> int:
    return (anchor_sign + house - 1) % 12


# ── derivation of P3 / P4 (spec §2.2, S-03, R3-S02) ──────────────────────────

def _h_and_lords(event_class: str, chart: Mapping[str, Any]):
    houses, anchor, _maraka = _CLASS[event_class]
    lagna_sign = _sign_index(chart["lagna"])
    anchor_sign = lagna_sign if anchor is None else _house_sign(anchor, lagna_sign)
    h_signs = sorted({_house_sign(h, anchor_sign) for h in houses})
    lords = sorted({_SIGN_LORD[_SIGNS[s]] for s in h_signs})
    return h_signs, lords, lagna_sign, anchor_sign


def _frame_person(event_class: str) -> tuple[str, str]:
    return ("bhavat_bhavam:9", "father") if event_class == "bereavement" else ("lagna", "native")


def _p3_obligation_bytes(event_class: str, chart: Mapping[str, Any],
                         path: str) -> list[str]:
    """Every (agent, relation, role, target) the spec's P3 predicate names, for `path`
    ('p3' or 'p4'; P4 = P3's Jupiter/Saturn scored obligations as P4's own)."""
    h_signs, lords, lagna_sign, anchor_sign = _h_and_lords(event_class, chart)
    frame, person = _frame_person(event_class)
    agents = _GRAHAS if path == "p3" else ("jupiter", "saturn")
    out = []

    def ob(agent, relation, role, target):
        out.append("|".join((event_class, path, "1.0.0", agent, relation, role, target,
                             frame, person)))

    for agent in agents:
        for s in h_signs:
            ob(agent, "residence", "signature_house", f"span:{s + 1}")
            if agent not in _NODES:
                ob(agent, "aspect", "signature_house", f"span:{s + 1}")
        for lord in lords:
            ob(agent, "conjunction", "lord", _point(chart["natal"][lord]))
            if agent not in _NODES:
                ob(agent, "aspect", "lord", _point(chart["natal"][lord]))
    if path == "p3":
        _h, _a, maraka_houses = _CLASS[event_class]
        m_signs = sorted({_house_sign(h, anchor_sign) for h in maraka_houses})
        for s in m_signs:
            ob(_SIGN_LORD[_SIGNS[s]], "ownership", "maraka_of_house", f"span:{s + 1}")
    return sorted(set(out))


# ── pins and the digest preimage (1206 / draft §AM-5 item 3) ─────────────────

def derive_path_pin(event_class: str, chart: Mapping[str, Any], path_id: str,
                    rule_version: str, *,
                    path_exclusions: Mapping[str, Mapping[str, str | None]],
                    h_unknown_exclusion: Mapping[str, str | None] | None) -> dict[str, Any]:
    """One pin as the verifier derives it. `path_exclusions` / `h_unknown_exclusion`
    are the verifier's OWN rulings ({reason, basis, ruling_ref}) — never read back from
    the stored pin under test."""
    p = path_id.lower()
    if p in path_exclusions:
        e = path_exclusions[p]
        return {"path": p, "version": rule_version.lower(), "disposition": "excluded",
                "reason": e["reason"], "ruling": e.get("ruling_ref") or "",
                "basis": e["basis"], "obligations": []}
    if p in _H_DEPENDENT and event_class in _UNKNOWN_H:
        if h_unknown_exclusion is None:
            raise Unverifiable(f"{event_class}/{p}: H is unknown and the verifier was given no "
                               "ruling for the degrading exclusion it would have to verify")
        e = h_unknown_exclusion
        return {"path": p, "version": rule_version.lower(), "disposition": "excluded",
                "reason": e["reason"], "ruling": e.get("ruling_ref") or "",
                "basis": e["basis"], "obligations": []}
    if p not in ("p3", "p4"):
        raise Unverifiable(f"{event_class}/{p}: no independent derivation of this path's "
                           "obligations exists in the verifier yet — refusing to vouch")
    obs = _p3_obligation_bytes(event_class, chart, p)
    if obs:
        return {"path": p, "version": rule_version.lower(), "disposition": "included",
                "reason": "", "ruling": "", "basis": "", "obligations": obs}
    return {"path": p, "version": rule_version.lower(), "disposition": "computed_empty",
            "reason": "", "ruling": "",
            "basis": f"spec:GOCHARA_DESIGN_SPECS@1.4#2.2-{p}-empty-qualified-set",
            "obligations": []}


def inventory_preimage(*, convention_id: str, horizon: tuple[str, str], input_digest: str,
                       pins: Sequence[Mapping[str, Any]]) -> str:
    """The pinned preimage: `convention=` · `horizon=[lo,hi)` · `input=` · one `pin=` per
    pin (sorted by lowercased path, version; committed ids comma-joined sorted as text) ·
    one `ob=` per obligation (sorted bytewise); joined by single newlines."""
    lines = [f"convention={convention_id}", f"horizon=[{horizon[0]},{horizon[1]})",
             f"input={input_digest}"]
    all_obs: list[str] = []
    for pin in sorted(pins, key=lambda x: (x["path"], x["version"])):
        ids = sorted(_uuidv8(o) for o in pin["obligations"])
        lines.append("pin=" + "|".join((pin["path"], pin["version"], pin["disposition"],
                                       pin["reason"], pin["ruling"], pin["basis"],
                                       ",".join(ids))))
        all_obs.extend(pin["obligations"])
    lines.extend("ob=" + o for o in sorted(all_obs))
    return "\n".join(lines)


def rederive_inventory_digest(
    conn: Any, *, chart_id: str, generation: str, event_class: str,
    sealed_paths: Sequence[tuple[str, str]],
    path_exclusions: Mapping[str, Mapping[str, str | None]],
    h_unknown_exclusion: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    """Re-derive one class's inventory and its digest from the sealed paths, the
    snapshot and the consumed L1 facts. Raises `Unverifiable` rather than guess."""
    if event_class not in _CLASS and event_class not in _UNKNOWN_H:
        raise Unverifiable(f"{event_class}: not a scored class")
    snap = conn.execute(
        "SELECT convention_id, consumed_fact_ids, input_digest"
        " FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchone()
    hdr = conn.execute(
        "SELECT to_char(lower(horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'),"
        "       to_char(upper(horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"
        " FROM public.ka_gochara_search_inventory"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s",
        (chart_id, generation, event_class)).fetchone()
    if snap is None or hdr is None:
        raise Unverifiable("no snapshot / inventory header to verify against")
    chart = read_chart(conn, snap[1]) if event_class in _CLASS else {"lagna": 0.0, "natal": {}}
    pins = [derive_path_pin(event_class, chart, pid, ver, path_exclusions=path_exclusions,
                            h_unknown_exclusion=h_unknown_exclusion)
            for pid, ver in sealed_paths]
    pre = inventory_preimage(convention_id=snap[0], horizon=(hdr[0], hdr[1]),
                             input_digest=snap[2], pins=pins)
    obligations = sorted(o for p in pins for o in p["obligations"])
    return {"digest": _sha(pre), "preimage": pre, "pins": pins, "obligations": obligations}


def write_verification(conn: Any, *, chart_id: str, generation: str, event_class: str,
                       rederived_digest: str) -> None:
    """The verification row (the caller holds the chart lock and the global SHARED key)."""
    conn.execute(
        "INSERT INTO public.ka_gochara_search_inventory_verification"
        " (chart_id, generation, event_class, verifier_id, verifier_version,"
        "  rederived_inventory_digest) VALUES (%s,%s,%s,%s,%s,%s)"
        " ON CONFLICT (chart_id, generation, event_class, verifier_id, verifier_version)"
        " DO NOTHING",
        (chart_id, generation, event_class, VERIFIER_ID, VERIFIER_VERSION, rederived_digest))
    row = conn.execute(
        "SELECT rederived_inventory_digest FROM public.ka_gochara_search_inventory_verification"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s"
        " AND verifier_id = %s AND verifier_version = %s",
        (chart_id, generation, event_class, VERIFIER_ID, VERIFIER_VERSION)).fetchone()
    if row is None or row[0] != rederived_digest:
        raise RuntimeError("a verification row already exists with a DIFFERENT digest — a "
                           "changed inventory replaces the chain (verification included)")


__all__ = ["Unverifiable", "VERIFIER_ID", "VERIFIER_VERSION", "derive_path_pin",
           "inventory_preimage", "read_chart", "rederive_inventory_digest",
           "write_verification"]
