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

WHAT IT CAN VOUCH FOR (honestly): P1 (role-token form, AM-11 pin e), P3 and P4 are derived
from the spec text (S-03 / R3-S02 / §2.2); an `excluded` pin is verified against the rulings
the verifier is GIVEN (never read back from the pin it is checking); the interval ledger's
daśā cuts and resolved agents are re-derived from the snapshot's consumed rows. P2's and P5's
enumerations are not yet independently derivable here: asking for them raises `Unverifiable` —
a class that includes them gets NO verification row, so it cannot seal. A verifier that cannot derive a
path must not vouch for it.

The named residual stays named: if this module and the builder share a misreading of the
doctrine, nothing here (or in SQL) can detect it.
"""
from __future__ import annotations

import hashlib
from decimal import Decimal
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
# AM-4 / AM-14 / R9-10: which bodies the stored tier never holds as a TRANSITING agent is read from the
# generation's MANIFEST scope and passed down to every derivation that enumerates bodies (the expected
# obligation set here, the expected P1 contact set in record_verifier) — there is no hard-coded exclusion at
# the point of use. This table is the verifier's OWN (nothing imported from the builder): scope → the bodies
# the stored tier never holds as a transiting agent. It says nothing about natal targets, the Moon frame, or
# anchor lords — the Moon in those roles stays. An unknown scope is not guessed: the verifier refuses.
SCOPE_EXCLUDED_AGENTS: dict[str, tuple[str, ...]] = {
    "stored_non_moon": ("moon",),
}


def excluded_agents_of_scope(scope: str) -> tuple[str, ...]:
    if scope not in SCOPE_EXCLUDED_AGENTS:
        raise Unverifiable(f"stored_scope {scope!r} is not a scope this verifier knows — it cannot say which "
                           "transiting bodies the stored tier is expected to hold")
    return SCOPE_EXCLUDED_AGENTS[scope]


def bound_excluded_agents(conn: Any, chart_id: str, generation: str) -> tuple[str, ...]:
    """The excluded transiting agents of the generation's BOUND manifest vector (`stored_scope`)."""
    import json
    row = conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if row is None:
        raise Unverifiable(f"generation {generation} has no bound manifest to take the expected bodies from")
    vector = row["input_generation_vector"] if isinstance(row, dict) else row[0]
    vector = vector if isinstance(vector, dict) else json.loads(vector)
    scope = vector.get("stored_scope")
    if not scope:
        raise Unverifiable(f"the manifest vector of generation {generation} states no stored_scope — the "
                           "expected bodies cannot be taken from it")
    return excluded_agents_of_scope(scope)


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

# P2 (spec §2.2; Phaladīpikā XXVI.1–8): the verifier's OWN tables — the class polarity (protocol §2) and the cited
# favourable houses from the janma-rāśi (Rāhu and Ketu take the Sun's set by the śl.2 equivalence clause); asserted
# equal to the rule modules' in a test so drift is visible, never imported.
_POLARITY = {
    "achievement_recognition": "gain", "bereavement": "adverse", "birth_anchor": "anchor",
    "business_launch": "gain", "career_advancement": "gain", "career_change": "gain", "career_entry": "gain",
    "career_setback": "adverse", "childbirth": "gain", "chronic_onset": "adverse",
    "education_milestone": "gain", "exam_outcome": "gain", "financial_deception": "adverse",
    "foreign_settlement": "gain", "illness_acute": "adverse", "major_gain": "gain", "major_loss": "adverse",
    "marriage": "gain", "parental_event": "adverse", "property_acquisition": "gain",
    "psychological_arc": "non-adverse", "relocation": "gain", "romantic_start": "gain", "separation": "adverse",
    "spiritual_turn": "non-adverse", "surgery": "adverse", "travel_event": "gain"}
_FAVOURABLE = {"sun": (3, 6, 10, 11), "moon": (1, 3, 6, 7, 10, 11), "mars": (3, 6, 11),
               "mercury": (2, 4, 6, 8, 10, 11), "jupiter": (2, 5, 7, 9, 11),
               "venus": (1, 2, 3, 4, 5, 8, 9, 11, 12), "saturn": (3, 6, 11),
               "rahu": (3, 6, 10, 11), "ketu": (3, 6, 10, 11)}
# the adverse-class plan: scored Sun/Mars/Jupiter in 12/8/1 and Saturn in the 8th, plus the Sade-Sati phase
# rows (Saturn in 12/1/2 — testimony, still SEARCHED: an obligation does not depend on the role)
_ADVERSE = {"sun": (12, 8, 1), "mars": (12, 8, 1), "jupiter": (12, 8, 1), "saturn": (8, 12, 1, 2)}

# P1 (spec §2.2; Phaladīpikā XX.34-38): each of the seven grahas' TRANSIT content names its
# own, exaltation and debilitation signs; Sun and Jupiter additionally ride EVERY graha's
# exaltation sign. Nodes: no cited transit residence. The verifier's own classical table.
_OWN = {"sun": ("leo",), "moon": ("cancer",), "mars": ("aries", "scorpio"),
        "mercury": ("gemini", "virgo"), "jupiter": ("sagittarius", "pisces"),
        "venus": ("taurus", "libra"), "saturn": ("capricorn", "aquarius")}
_EXALT = {"sun": "aries", "moon": "taurus", "mars": "capricorn", "mercury": "virgo",
          "jupiter": "cancer", "venus": "pisces", "saturn": "libra"}
_DEBIL = {"sun": "libra", "moon": "scorpio", "mars": "cancer", "mercury": "pisces",
          "jupiter": "capricorn", "venus": "virgo", "saturn": "aries"}
_ROLE_LEVEL = {"md": 1, "ad": 2, "pd": 3}


def _uuidv8(text: str) -> str:
    b = bytearray(hashlib.sha256(text.encode("utf-8")).digest()[:16])
    b[6] = (b[6] & 0x0F) | 0x80
    b[8] = (b[8] & 0x3F) | 0x80
    h = b.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _point(lam: float) -> str:
    text = repr(float(lam) % 360.0)
    if "e" in text or "E" in text:
        text = format(Decimal(text), "f")
    return f"point:{text}"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── facts: straight from chart_facts by the snapshot's consumed ids ──────────

def _exact_float(num: Any, subject: str) -> float:
    """The F-3 §3 round-trip guard, derived independently of `targets`: a stored L1 numeric
    must equal what its float64 carries (`Decimal(repr(float(x))) == x.normalize()`),
    else there is no honest identity text to re-derive from — unverifiable, never rounded."""
    if isinstance(num, float):
        return num
    exact = num if isinstance(num, Decimal) else Decimal(str(num))
    value = float(exact)
    if Decimal(repr(value)) != exact.normalize():
        raise Unverifiable(
            f"graha_position {subject} = {num!r} is not exactly representable as a float64: "
            "the identity text would be quantised — refusing to re-derive (F-3 §3)")
    return value


def read_chart(conn: Any, fact_ids: Sequence[str]) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT fact_subject, fact_value_num FROM public.chart_facts"
        " WHERE fact_id = ANY(%s::text[])", (list(fact_ids),)).fetchall()
    lagna, natal = None, {}
    for subj, num in rows:
        if num is None:
            continue
        if subj == "LAGNA":
            lagna = _exact_float(num, subj)
        elif subj in _FACT_SUBJECT:
            natal[_FACT_SUBJECT[subj]] = _exact_float(num, subj)
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


def _p1_obligation_bytes(event_class: str, rule_version: str) -> list[str]:
    """P1 under AM-11 pin (e): the period-role agent is the ROLE token; the qualified
    geometry is the TRANSIT residence on the signs P1's content names (natal-fact rows are
    not admission-bearing — pin b — so they are not obligations)."""
    signs: set[str] = set()
    for g in _OWN:
        signs.update(_OWN[g])
        signs.add(_EXALT[g])
        signs.add(_DEBIL[g])
    signs.update(_EXALT.values())          # Sun and Jupiter: every graha's exaltation sign
    _frame, person = _frame_person(event_class)
    role_token = {"|".join((event_class, "p1", rule_version.lower(), f"period_lord:{role}", "residence",
                            "period_lord", f"span:{_SIGNS.index(sg) + 1}", "dasha_lord",
                            person)) for role in _ROLE_LEVEL for sg in signs}
    # XX.38 delivery searches (steward M…053914): the Sun and Jupiter transiting ANOTHER graha's exaltation sign, and
    # the Sun another's debilitation sign, are CONCRETE-agent searches (the agent is not the period lord, so the role
    # tokens above do not cover them). Anchor-free: the anchor is the record's property (record_verifier.verify_p1_anchors).
    delivery: set[str] = set()
    for agent in ("sun", "jupiter"):
        targets = {_EXALT[g] for g in _EXALT if g != agent}
        if agent == "sun":
            targets |= {_DEBIL[g] for g in _DEBIL if g != "sun"}
        delivery |= {"|".join((event_class, "p1", rule_version.lower(), agent, "residence", "period_lord",
                               f"span:{_SIGNS.index(sg) + 1}", "dasha_lord", person)) for sg in targets}
    return sorted(role_token | delivery)


def _p2_obligation_bytes(event_class: str, chart: Mapping[str, Any], rule_version: str, *,
                         excluded_agents: Sequence[str]) -> list[str]:
    """P2 (Moon frame): per the class polarity, the agent × house residences counted from the janma-rāśi —
    gain: the cited favourable houses of every STORED agent; adverse: the pinned plan; anchor/non-adverse: none.
    Frame `moon`, person `native` (P2 licenses the native's fortune only); the Moon is an on-demand tier, never
    a stored transit agent."""
    polarity = _POLARITY[event_class]
    table = _FAVOURABLE if polarity == "gain" else _ADVERSE if polarity == "adverse" else {}
    moon_sign = _sign_index(chart["natal"]["moon"])
    out = set()
    for agent, houses in table.items():
        if agent in excluded_agents:
            continue
        for h in houses:
            out.add("|".join((event_class, "p2", rule_version.lower(), agent, "residence", "signature_house",
                              f"span:{(moon_sign + h - 1) % 12 + 1}", "moon", "native")))
    return sorted(out)


def _p3_obligation_bytes(event_class: str, chart: Mapping[str, Any],
                         path: str, rule_version: str, *, excluded_agents: Sequence[str]) -> list[str]:
    """Every (agent, relation, role, target) the spec's P3 predicate names, for `path`
    ('p3' or 'p4'; P4 = P3's Jupiter/Saturn scored obligations as P4's own)."""
    h_signs, lords, lagna_sign, anchor_sign = _h_and_lords(event_class, chart)
    frame, person = _frame_person(event_class)
    agents = (tuple(g for g in _GRAHAS if g not in excluded_agents)
              if path == "p3" else ("jupiter", "saturn"))
    out = []

    def ob(agent, relation, role, target):
        out.append("|".join((event_class, path, rule_version.lower(), agent, relation, role, target,
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


# ── P1 prerequisite (2): the verifier's OWN period-lord relation (R11-2) ───────────────────────────────────

def period_lord_relation(lord: str, event_class: str, chart: Mapping[str, Any]) -> dict[str, str]:
    """The natal bhāva relationship of a period lord to the event class (spec §2.2 relation-kind table; Phaladīpikā
    XX.34–38), derived HERE from this verifier's own class table and sign lordships — it shares NO code with the builder's
    `gochara_rules.permission.period_lord_relation` (a defect there must not make builder and verifier agree; an import test
    holds the line). Returns {relation, licence} with licence ∈ {scored, testimony, none}:

      * H unknown for the class ⇒ relation `unknown`, licence `none`;
      * the lord OCCUPIES a signature house, or (a non-node) OWNS one ⇒ scored;
      * its DISPOSITOR (the lord of its natal sign) occupies a signature house, or (a non-node dispositor) owns one ⇒
        testimony (annotates, never licenses); otherwise `none`."""
    if event_class in _UNKNOWN_H or event_class not in _CLASS:
        return {"relation": "unknown", "licence": "none"}
    h_signs = set(_h_and_lords(event_class, chart)[0])
    natal = chart["natal"]
    if lord in natal and _sign_index(natal[lord]) in h_signs:
        return {"relation": "occupancy", "licence": "scored"}
    owned = {_SIGN_LORD[_SIGNS[i]] for i in h_signs}
    if lord not in _NODES and lord in owned:
        return {"relation": "ownership", "licence": "scored"}
    disp = _SIGN_LORD[_SIGNS[_sign_index(natal[lord])]]
    if (disp in natal and _sign_index(natal[disp]) in h_signs) or (disp not in _NODES and disp in owned):
        return {"relation": "dispositorship", "licence": "testimony"}
    return {"relation": "none", "licence": "none"}


# ── pins and the digest preimage (1206 / draft §AM-5 item 3) ─────────────────

def derive_path_pin(event_class: str, chart: Mapping[str, Any], path_id: str,
                    rule_version: str, *, excluded_agents: Sequence[str],
                    path_exclusions: Mapping[str, Mapping[str, str | None]],
                    h_unknown_exclusion: Mapping[str, str | None] | None) -> dict[str, Any]:
    """One pin as the verifier derives it. `path_exclusions` / `h_unknown_exclusion`
    are the verifier's OWN rulings ({reason, basis, ruling_ref}) — never read back from
    the stored pin under test."""
    p = path_id.lower()
    e = _exclusion_of(p, rule_version.lower(), path_exclusions)
    if e is not None:
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
    if p not in ("p1", "p2", "p3", "p4"):
        raise Unverifiable(f"{event_class}/{p}: no independent derivation of this path's "
                           "obligations exists in the verifier yet — refusing to vouch")
    obs = (_p1_obligation_bytes(event_class, rule_version) if p == "p1"
           else _p2_obligation_bytes(event_class, chart, rule_version, excluded_agents=excluded_agents) if p == "p2"
           else _p3_obligation_bytes(event_class, chart, p, rule_version, excluded_agents=excluded_agents))
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


#: The verifier's OWN copy of the approved supersessions (R8-2): `(path, older) -> successor`. Not imported from
#: the builder's inventory module or the registry — it is told what the amendments approved (AM-13: P3/P4/P5;
#: AM-18: P2) independently of the code it checks.
_SUPERSEDED = {("p2", "1.0.0"): "1.1.0", ("p3", "1.0.0"): "1.1.0",
               ("p4", "1.0.0"): "1.1.0", ("p5", "1.0.0"): "1.1.0"}


def _supersession_basis(path: str, old: str, new: str) -> str:
    anchor = "AM-18" if path == "p2" else "AM-13"
    return f"spec:GOCHARA_SPECS_V1_5_AMENDMENTS@1.5#{anchor}-{path}-{old}-superseded-by-{new}"


def _exclusion_of(path: str, version: str, path_exclusions: Mapping) -> Mapping | None:
    return path_exclusions.get((path, version)) or path_exclusions.get(path)


def derive_class_pins(event_class: str, chart: Mapping[str, Any], sealed_paths: Sequence[tuple[str, str]], *,
                      excluded_agents: Sequence[str],
                      selected_versions: Mapping[str, str] | None,
                      path_exclusions: Mapping[Any, Mapping[str, str | None]],
                      h_unknown_exclusion: Mapping[str, str | None] | None) -> list[dict[str, Any]]:
    """Every sealed `(path, version)` accounted, at most ONE `included` per path (R8-2), derived independently of
    the builder. A non-selected version is excluded/computed_empty exactly as it would be if searched; one that
    WOULD be included is `superseded_by_version` only when the selected version is its approved successor AND is
    itself included; otherwise it is unverifiable (a withheld version needs its own composite ruling).
    `selected_versions` None ⇒ derived: the single sealed version, or the one that is included."""
    by_path: dict[str, list[str]] = {}
    for pid, ver in sealed_paths:
        by_path.setdefault(pid.lower(), []).append(ver.lower())
    selected = {k.lower(): v.lower() for k, v in (selected_versions or {}).items()}
    out: list[dict[str, Any]] = []
    for path in sorted(by_path):
        versions = sorted(by_path[path])
        pins = {v: derive_path_pin(event_class, chart, path, v, excluded_agents=excluded_agents,
                                   path_exclusions=path_exclusions,
                                   h_unknown_exclusion=h_unknown_exclusion) for v in versions}
        if path in selected:
            if selected[path] not in versions:
                raise Unverifiable(f"{event_class}/{path}: selected {selected[path]!r} is not sealed")
            chosen = selected[path]
        elif len(versions) == 1:
            chosen = versions[0]
        else:
            included = [v for v in versions if pins[v]["disposition"] == "included"]
            if len(included) > 1:
                raise Unverifiable(f"{event_class}/{path}: {included} would all be included and no selection "
                                   "was given — nothing to verify against")
            chosen = included[0] if included else versions[-1]
        for v in versions:
            pin = pins[v]
            if v != chosen and pin["disposition"] == "included":
                if pins[chosen]["disposition"] == "included" and _SUPERSEDED.get((path, v)) == chosen:
                    pin = {"path": path, "version": v, "disposition": "excluded",
                           "reason": "superseded_by_version", "ruling": "",
                           "basis": _supersession_basis(path, v, chosen), "obligations": []}
                else:
                    raise Unverifiable(f"{event_class}/{path}@{v}: neither selected ({chosen}), superseded by "
                                       "an included approved successor, nor excluded by a composite ruling")
            out.append(pin)
    return out


def stored_selection(conn: Any, *, chart_id: str, generation: str, event_class: str) -> dict[str, str]:
    """The ORIGINAL selection of a stored class inventory — the `included` version of each path (historical
    replay reuses it; it never re-selects under today's configuration)."""
    rows = conn.execute(
        "SELECT lower(path_id), rule_version FROM public.ka_gochara_search_path_pin"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s AND disposition = 'included'",
        (chart_id, generation, event_class)).fetchall()
    return {r[0]: r[1] for r in rows}


def rederive_inventory_digest(
    conn: Any, *, chart_id: str, generation: str, event_class: str,
    sealed_paths: Sequence[tuple[str, str]],
    path_exclusions: Mapping[Any, Mapping[str, str | None]],
    h_unknown_exclusion: Mapping[str, str | None] | None = None,
    selected_versions: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Re-derive one class's inventory and its digest from the sealed paths, the
    snapshot and the consumed L1 facts. Raises `Unverifiable` rather than guess.
    `selected_versions` is the selection the verifier is TOLD (None ⇒ derived from the single sealed version
    or the included one — never from today's configuration)."""
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
    chart = read_chart(conn, snap[1])           # every class: P2 needs the natal Moon even where H is unknown
    pins = derive_class_pins(event_class, chart, sealed_paths,
                             excluded_agents=bound_excluded_agents(conn, chart_id, generation),   # R9-10: the manifest's scope
                             selected_versions=selected_versions,
                             path_exclusions=path_exclusions, h_unknown_exclusion=h_unknown_exclusion)
    pre = inventory_preimage(convention_id=snap[0], horizon=(hdr[0], hdr[1]),
                             input_digest=snap[2], pins=pins)
    obligations = sorted(o for p in pins for o in p["obligations"])
    return {"digest": _sha(pre), "preimage": pre, "pins": pins, "obligations": obligations}


def _utc_ts(t) -> str:
    return t.astimezone(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rederive_ledger_digest(
    conn: Any, *, chart_id: str, generation: str, event_class: str,
    obligations: Sequence[str], capability: Mapping[str, bool],
) -> str:
    """Re-derive the interval LEDGER digest: SQL stores and recomputes it but cannot
    check that the cuts and resolved agents are the RIGHT ones — this is that check (a
    process residual named in AM-11 pin e). `capability` = {position_probe, arc_index, aspect_span_solver} as
    the verifier was independently told."""
    # the consumed population must BE the §4.0 population before any row of it is trusted (R7 [2])
    validate_consumed_dasha_population(conn, chart_id=chart_id, generation=generation)
    snap = conn.execute(
        "SELECT consumed_dasha_row_ids, input_digest FROM"
        " public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchone()
    hdr = conn.execute(
        "SELECT lower(horizon), upper(horizon) FROM public.ka_gochara_search_inventory"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s",
        (chart_id, generation, event_class)).fetchone()
    lo, hi = hdr
    rows = conn.execute(
        "SELECT level_n, start_iso, end_iso, lower(lord_graha) FROM public.chart_dashas"
        " WHERE chart_id = %s AND dasha_row_id = ANY(%s::uuid[]) ORDER BY level_n, start_iso",
        (chart_id, [str(x) for x in snap[0]])).fetchall()
    lines = []
    for ob in obligations:
        agent, relation = ob.split("|")[3], ob.split("|")[4]
        transit = relation in ("residence", "aspect", "conjunction")
        if relation == "residence":
            state = "searched_complete" if capability["position_probe"] else "missing_inputs"
        elif relation == "aspect" and ob.split("|")[6].startswith("span:"):
            # aspect-to-span (the aspect point's ingress into a house span) is not a point root
            state = ("searched_complete" if (capability.get("aspect_span_solver", False)
                                             and capability["position_probe"])
                     else "missing_inputs")
        elif relation in ("conjunction", "aspect"):
            state = "searched_complete" if capability["arc_index"] else "missing_inputs"
        else:
            state = "searched_complete"        # an atemporal natal fact
        oid = _uuidv8(ob)
        if agent.startswith("period_lord:"):
            level = _ROLE_LEVEL[agent.split(":")[1]]
            cursor = lo
            for lv, a, b, lord in rows:
                if lv != level:
                    continue
                a2, b2 = max(a, lo), min(b, hi)
                if not a2 < b2:
                    continue
                if a2 > cursor:
                    lines.append(f"{oid}|{_utc_ts(cursor)}|{_utc_ts(a2)}|missing_inputs|{snap[1]}")
                # a Moon period lord resolves to an agent the stored build never searches (AM-4)
                # (AM-14: with the schema's Moon-domain accounting the portion is EXCLUDED from the
                # stored tier — told to this verifier independently, like the other capabilities)
                piece_state = (("excluded_moon_tier" if capability.get("moon_scope_domain", False)
                                else "missing_inputs") if lord == "moon" else state)
                lines.append(f"{oid}|{_utc_ts(a2)}|{_utc_ts(b2)}|{piece_state}|{snap[1]}")
                cursor = max(cursor, b2)
            if cursor < hi:
                lines.append(f"{oid}|{_utc_ts(cursor)}|{_utc_ts(hi)}|missing_inputs|{snap[1]}")
        else:
            lines.append(f"{oid}|{_utc_ts(lo)}|{_utc_ts(hi)}|{state}|{snap[1]}")
    # 1206 v1.1 (accepted): the preimage starts with `input=<input_digest>` so an EMPTY ledger is
    # input-bound too; the sorted interval rows (byte order — 'C' collation) follow, one per line.
    return _sha(f"input={snap[1]}" + ("\n" + "\n".join(sorted(lines)) if lines else ""))


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


__all__ = ["period_lord_relation", "Unverifiable", "SCOPE_EXCLUDED_AGENTS", "excluded_agents_of_scope", "bound_excluded_agents", "VERIFIER_ID", "VERIFIER_VERSION", "derive_path_pin",
           "inventory_preimage", "read_chart", "rederive_inventory_digest",
           "rederive_ledger_digest",
           "write_verification"]


# ── aspect-to-span occurrences, re-derived by SAMPLING + BISECTION (no shared code) ──────────────
#
# The builder derives an aspect-to-span occurrence from the body's residence spans over the aspect
# SOURCE signs (crossing events + midpoint probes + contiguity merging). This is the independent
# second reading: it never reads a crossing, a residence span or the builder's source-sign table. It
# samples the body's longitude on a fixed grid, asks the plain geometric question "does any of the
# body's aspect points lie in the target sign at t?", and bisects every change of that answer down to
# `tol_seconds`. Disagreement between the two readings (a span the builder minted that sampling
# cannot see, or one it missed) fails the build.

#: the special-dṛṣṭi angles, BPHS ch.26 (bphs_vol1_rsanthanam_djvu.txt:16496-16505); N-14: the nodes
#: cast none. Written out again here — this module imports nothing from the builder.
_DRISHTI_DEG = {"sun": (180.0,), "moon": (180.0,), "mercury": (180.0,), "venus": (180.0,),
                "mars": (90.0, 180.0, 210.0), "jupiter": (120.0, 180.0, 240.0),
                "saturn": (60.0, 180.0, 270.0), "rahu": (), "ketu": ()}


def rederive_aspect_span_runs(
    position_at, *, body: str, target_sign_index: int, lo, hi,
    step_hours: float = 6.0, tol_seconds: float = 1.0,
) -> list[tuple[Any, Any]]:
    """Maximal runs `[t_in, t_out)` inside `[lo, hi)` during which some aspect point of `body` lies in
    the 0-based target sign. `t_in == lo` / `t_out == hi` where the run touches the window edge.
    `position_at(body, t)` is the injected sidereal-longitude probe."""
    from datetime import timedelta
    angles = _DRISHTI_DEG[body.lower()]
    if not angles:
        return []

    def aspected(t) -> bool:
        lon = position_at(body, t)
        return any(int(((lon + a) % 360.0) // 30.0) == target_sign_index for a in angles)

    def bisect(a, b, fa):
        """The instant in (a, b] at which `aspected` first differs from `fa` (monotone in [a, b])."""
        while (b - a).total_seconds() > tol_seconds:
            mid = a + (b - a) / 2
            if aspected(mid) == fa:
                a = mid
            else:
                b = mid
        return b

    step = timedelta(hours=step_hours)
    runs: list[tuple[Any, Any]] = []
    t = lo
    state = aspected(t)
    start = lo if state else None
    while t < hi:
        nxt = min(t + step, hi)
        s2 = aspected(nxt) if nxt < hi else state     # the last sample IS the window end: no probe at hi
        if nxt < hi and s2 != state:
            edge = bisect(t, nxt, state)
            if state:
                runs.append((start, edge))
                start = None
            else:
                start = edge
            state = s2
        t = nxt
    if state and start is not None:
        runs.append((start, hi))
    return runs


# ── the consumed daśā POPULATION, validated against the §4.0 read contract (Codex round 7 [2]) ──────────
#
# Hashing rows does not make them authoritative: a Moon row of an inadmissible build or system, once
# consumed, would be "accounted" by every derivation that reads the supplied ids. So the verifier checks
# the CONSUMED set itself against the contract it is TOLD (its own constants, not the builder's):
#   * every consumed row is of this chart, ayanāṃśa, system and tier, levels 1–3, and — for the canonical
#     chart — the FROZEN pinned build (any other chart: one build, shared by every consumed row);
#   * no consumed row lies wholly outside the horizon (an EXTRA), and no pinned-build row overlapping the
#     horizon is missing (an OMITTED);
#   * no two pinned rows conflict on the same (level, parent, start) with different contract fields.

_C_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
_C_BUILD = "1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb"
_C_AYANAMSHA, _C_SYSTEM, _C_TIER = "lahiri_chitrapaksha", "vimshottari", "two_pass_verified"
_C_LEVELS = (1, 2, 3)


def check_dasha_population(consumed: Sequence[Mapping[str, Any]], pinned: Sequence[Mapping[str, Any]], *,
                           chart_id: str, horizon: tuple, consumed_ids: Sequence[str]) -> list[str]:
    """Pure: the violations (empty = the population is the §4.0 population). `consumed` are the rows the
    snapshot's ids resolve to for this chart; `pinned` the rows the contract selects (ayanāṃśa, system,
    tier, build, levels) — both with level_n, start_iso, end_iso, lord_graha, build_id, system_id,
    ayanamsha_id, verification_pass_status, parent_row_id, dasha_row_id."""
    lo, hi = horizon
    out: list[str] = []
    found = {str(r["dasha_row_id"]) for r in consumed}
    for rid in consumed_ids:
        if str(rid) not in found:
            out.append(f"consumed id {rid} resolves to no row of this chart")
    builds = {str(r["build_id"]) for r in consumed}
    for r in consumed:
        rid = r["dasha_row_id"]
        if r["ayanamsha_id"] != _C_AYANAMSHA or r["system_id"] != _C_SYSTEM:
            out.append(f"row {rid}: ayanāṃśa/system {r['ayanamsha_id']}/{r['system_id']} is not "
                       f"{_C_AYANAMSHA}/{_C_SYSTEM}")
        if r["verification_pass_status"] != _C_TIER:
            out.append(f"row {rid}: tier {r['verification_pass_status']!r} is not {_C_TIER}")
        if int(r["level_n"]) not in _C_LEVELS:
            out.append(f"row {rid}: level {r['level_n']} is not MD/AD/PD")
        if not (r["start_iso"] < hi and r["end_iso"] > lo):
            out.append(f"row {rid}: lies wholly outside the horizon (an extra row)")
    if str(chart_id) == _C_CHART:
        wrong = sorted(b for b in builds if b != _C_BUILD)
        if wrong:
            out.append(f"canonical chart: consumed build(s) {wrong} are not the frozen {_C_BUILD}")
    elif len(builds) > 1:
        out.append(f"several builds {sorted(builds)} consumed — an unpinned read")
    want = {str(r["dasha_row_id"]) for r in pinned if r["start_iso"] < hi and r["end_iso"] > lo}
    for rid in sorted(want - found):
        out.append(f"pinned row {rid} overlaps the horizon but was NOT consumed (omitted)")
    seen: dict[tuple, Mapping[str, Any]] = {}
    for r in pinned:
        key = (r["level_n"], str(r["parent_row_id"]), r["start_iso"])
        prev = seen.setdefault(key, r)
        if prev is not r and (prev["end_iso"], prev["lord_graha"]) != (r["end_iso"], r["lord_graha"]):
            out.append(f"conflicting pinned rows at {key}")
    return out


def validate_consumed_dasha_population(conn: Any, *, chart_id: str, generation: str) -> dict:
    snap = conn.execute(
        "SELECT consumed_dasha_row_ids FROM public.ka_gochara_search_input_snapshot"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if snap is None:
        raise Unverifiable("no search-input snapshot to validate the consumed daśā population against")
    ids = [str(x) for x in snap[0]]
    horizon = conn.execute(
        "SELECT min(lower(horizon)), max(upper(horizon)) FROM public.ka_gochara_search_inventory"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if horizon is None or horizon[0] is None:
        raise Unverifiable("no inventory horizon to validate the consumed daśā population against")
    cols = ("dasha_row_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id, system_id,"
            " ayanamsha_id, verification_pass_status")

    def rows(sql, params):
        names = [c.strip() for c in cols.split(",")]
        return [dict(zip(names, r)) for r in conn.execute(sql, params).fetchall()]
    # G6 (verifier's OWN query, builder code not imported): every Vimśottarī / lahiri row of the chart — all tiers, all levels — is ONE build,
    # and for the canonical chart the frozen one
    builds = sorted(str(r[0]) for r in conn.execute(
        "SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s",
        (chart_id, _C_SYSTEM, _C_AYANAMSHA)).fetchall())
    if len(builds) > 1:
        raise RuntimeError(f"dasha_builds_mixed: chart {chart_id} carries Vimśottarī rows of {len(builds)} builds {builds} (every tier) — "
                           "a mixed L1 state is not verifiable")
    if builds and str(chart_id) == _C_CHART and builds[0] != _C_BUILD:
        raise RuntimeError(f"dasha_build_not_pinned: the canonical chart's only Vimśottarī build is {builds[0]}, the frozen contract pins {_C_BUILD}")
    consumed = rows(f"SELECT {cols} FROM public.chart_dashas WHERE chart_id = %s"
                    " AND dasha_row_id = ANY(%s::uuid[])", (chart_id, ids))
    build = _C_BUILD if str(chart_id) == _C_CHART else None
    pinned = rows(f"SELECT {cols} FROM public.chart_dashas WHERE chart_id = %s AND ayanamsha_id = %s"
                  " AND system_id = %s AND verification_pass_status = %s AND level_n = ANY(%s)"
                  " AND (%s::uuid IS NULL OR build_id = %s::uuid)",
                  (chart_id, _C_AYANAMSHA, _C_SYSTEM, _C_TIER, list(_C_LEVELS), build, build))
    problems = check_dasha_population(consumed, pinned, chart_id=chart_id,
                                      horizon=(horizon[0], horizon[1]), consumed_ids=ids)
    if problems:
        raise RuntimeError("consumed daśā population violates the §4.0 read contract: " + "; ".join(problems))
    return {"consumed": len(consumed), "pinned_overlapping": sum(
        1 for r in pinned if r["start_iso"] < horizon[1] and r["end_iso"] > horizon[0])}


__all__ += ["check_dasha_population", "validate_consumed_dasha_population"]
