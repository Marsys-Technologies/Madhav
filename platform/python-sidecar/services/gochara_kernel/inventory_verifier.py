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
import json
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID
from decimal import Decimal
from typing import Any, Mapping, Sequence

from .nd_h_tables import (
    AFFECTED_PERSON as _ndh_AFFECTED_PERSON, EIGHT as _ndh_EIGHT, KARAKATVA as _ndh_KARAKATVA, KARAKA_B_LUMINARY as _ndh_KARAKA_B_LUMINARY, KB_RELATIONS as _ndh_KB_RELATIONS, TIERS as _ndh_TIERS, path_houses as _ndh_path_houses
)

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED as _TWO_PASS_VERIFIED   # the sanctioned vocabulary (TAP-6)

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
    must equal what its float64 carries (`Decimal(repr(float(x))) == x` (exact Decimal equality)),
    else there is no honest identity text to re-derive from — unverifiable, never rounded."""
    if isinstance(num, float):
        return num
    exact = num if isinstance(num, Decimal) else Decimal(str(num))
    value = float(exact)
    if Decimal(repr(value)) != exact:          # exact Decimal equality (.normalize() would round to the context precision and accept a tiny difference)
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


def chart_from_copy(copy: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The natal chart from a snapshot's COPY of the consumed fact rows (G12 route 1): the same subjects and the same exactness guard as
    `read_chart`, read from the stored content instead of live L1. `copy` must have been parsed with `parse_float=Decimal` (see
    `read_chart_snapshot`) so a numeric is never quantised on the way."""
    problems = fact_copy_violations(copy)
    if problems:                                   # a duplicated, foreign or valueless subject is refused by name, never resolved by element order
        raise Unverifiable("the snapshot's fact copy violates the capture contract: " + "; ".join(f"{c} ({d})" for c, d in problems))
    lagna, natal = None, {}
    for e in copy:
        c = e.get("content") or {}
        subj, num = (e.get("key") or {}).get("fact_subject"), c.get("fact_value_num")
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


def snapshot_copies(conn: Any, chart_id: str, generation: str) -> dict[str, Any] | None:
    """The snapshot's COPIES of its consumed L1 rows, numerics kept EXACT (`Decimal`): {"facts": [...], "dashas": [...],
    "fact_ids": [...], "dasha_row_ids": [...]} — or None when the generation has no snapshot. `facts` / `dashas` are None for a LEGACY snapshot
    (written before migration 1305: ids only; not self-contained)."""
    import json
    row = conn.execute(
        "SELECT consumed_fact_ids, consumed_dasha_row_ids FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchone()
    if row is None:
        return None
    ids = tuple(row.values()) if isinstance(row, dict) else tuple(row)
    out: dict[str, Any] = {"fact_ids": list(ids[0]), "dasha_row_ids": [str(x) for x in ids[1]], "facts": None, "dashas": None}
    has_copy = conn.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
        " AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows')").fetchone()
    if int(next(iter(has_copy.values())) if isinstance(has_copy, dict) else has_copy[0]) == 2:
        cp = conn.execute(
            "SELECT consumed_fact_rows::text, consumed_dasha_rows::text FROM public.ka_gochara_search_input_snapshot"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
        cp = tuple(cp.values()) if isinstance(cp, dict) else tuple(cp)
        if cp[0] is not None and cp[1] is not None:
            out["facts"] = json.loads(cp[0], parse_float=Decimal)
            out["dashas"] = json.loads(cp[1], parse_float=Decimal)
    return out


def read_chart_snapshot(conn: Any, chart_id: str, generation: str) -> dict[str, Any]:
    """The natal chart the generation was built from: read from the snapshot's own COPY (so it exists after any later L1 rebuild); a LEGACY
    snapshot is read by id from live L1, as before."""
    snap = snapshot_copies(conn, chart_id, generation)
    if snap is None:
        raise Unverifiable("no search-input snapshot to read the natal chart from")
    if snap["facts"] is None:
        return read_chart(conn, snap["fact_ids"])
    return chart_from_copy(snap["facts"])


def _sign_index(lon: float) -> int:
    return int((lon % 360.0) // 30.0)


def _house_sign(house: int, anchor_sign: int) -> int:
    return (anchor_sign + house - 1) % 12


# ── derivation of P3 / P4 (spec §2.2, S-03, R3-S02) ──────────────────────────

def _h_and_lords(event_class: str, chart: Mapping[str, Any], rule_version="1.0.0", path="p3"):
    houses, anchor, _maraka = _CLASS.get(event_class, (None, None, set()))
    if rule_version == "1.2.0" and event_class in _ndh_EIGHT:
        houses = _ndh_path_houses(event_class, path.upper())
        anchor = None  # verifier table already resolves the father frame to lagna houses
    lagna_sign = _sign_index(chart["lagna"])
    anchor_sign = lagna_sign if anchor is None else _house_sign(anchor, lagna_sign)
    h_signs = sorted({_house_sign(h, anchor_sign) for h in houses})
    lords = sorted({_SIGN_LORD[_SIGNS[s]] for s in h_signs})
    return h_signs, lords, lagna_sign, anchor_sign


def _frame_person(event_class: str, rule_version="1.0.0") -> tuple[str, str]:
    father = event_class == "bereavement" or (rule_version == "1.2.0" and event_class == "parental_event")
    return ("bhavat_bhavam:9", "father") if father else ("lagna", "native")


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
    _frame, person = _frame_person(event_class, rule_version)
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
    h_signs, lords, lagna_sign, anchor_sign = _h_and_lords(event_class, chart, rule_version, path)
    frame, person = _frame_person(event_class, rule_version)
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
    if rule_version == "1.2.0" and event_class in _ndh_KARAKA_B_LUMINARY:
        luminary = _ndh_KARAKA_B_LUMINARY[event_class]
        for agent in agents:
            for relation in _ndh_KB_RELATIONS.get(agent, ()):
                ob(agent, relation, "karaka", _point(chart["natal"][luminary]))
    if path == "p3":
        _h, _a, maraka_houses = _CLASS.get(event_class, (None, None, set()))
        m_signs = sorted({_house_sign(h, anchor_sign) for h in maraka_houses})
        for s in m_signs:
            ob(_SIGN_LORD[_SIGNS[s]], "ownership", "maraka_of_house", f"span:{s + 1}")
    return sorted(set(out))



def final_rule_edge_tiers(event_class, path_id, chart):
    """FB-34/35: independent identity -> tier map (CORE subsumes DVI)."""
    if event_class not in _ndh_EIGHT or path_id not in ('P3', 'P4'):
        return {}, []
    tier = _ndh_TIERS[event_class]
    lagna = _sign_index(chart['lagna'])
    agents = _GRAHAS if path_id == 'P3' else ('jupiter', 'saturn')
    tables = {}
    for name, houses in [('core', tier.core), ('dvi', tier.dvi if path_id == 'P4' else ())]:
        keys = set()
        signs = {_house_sign(h, lagna) for h in houses}
        lords = {_SIGN_LORD[_SIGNS[s]] for s in signs}
        for agent in agents:
            for sign in signs:
                for rel in ('residence', 'aspect') if agent not in _NODES else ('residence',):
                    keys.add('|'.join((agent, rel, f'span:{sign + 1}', 'signature_house')))
            for lord in lords:
                if lord not in chart['natal']:
                    raise Unverifiable(f'final_rule_natal_lord_missing: {lord}')
                for rel in ('conjunction', 'aspect') if agent not in _NODES else ('conjunction',):
                    keys.add('|'.join((agent, rel, _point(chart['natal'][lord]), 'lord')))
        tables[name] = keys
    absorbed = sorted(tables['core'] & tables['dvi'])
    return {**dict.fromkeys(tables['dvi'], 'dvi'), **dict.fromkeys(tables['core'], 'core')}, absorbed


def derive_final_rule_context(event_class, path_id, chart, rule_version):
    """Ruling 18 §§1–2, verifier-owned data, independent of the enumerator."""
    if rule_version != '1.2.0' or event_class not in _ndh_EIGHT:
        return None
    _, absorbed = final_rule_edge_tiers(event_class, path_id, chart)
    return {'dvi_absorbed_by_core': absorbed, 'ruling_ref': 'SURROGATE_ANSWER_18',
            'support': {'state': 'annotation_unstored', 'ruling_ref': 'SURROGATE_ANSWER_18'}}

# ── P1 prerequisite (2): the verifier's OWN period-lord relation (R11-2) ───────────────────────────────────

def period_lord_relation(lord: str, event_class: str, chart: Mapping[str, Any], *,
                         rule_version="1.0.0", level=None, affected_person=None) -> dict[str, str]:
    """The natal bhāva relationship of a period lord to the event class (spec §2.2 relation-kind table; Phaladīpikā
    XX.34–38), derived HERE from this verifier's own class table and sign lordships — it shares NO code with the builder's
    `gochara_rules.permission.period_lord_relation` (a defect there must not make builder and verifier agree; an import test
    holds the line). Returns {relation, licence} with licence ∈ {scored, testimony, none}:

      * H unknown for the class ⇒ relation `unknown`, licence `none`;
      * the lord OCCUPIES a signature house, or (a non-node) OWNS one ⇒ scored;
      * its DISPOSITOR (the lord of its natal sign) occupies a signature house, or (a non-node dispositor) owns one ⇒
        testimony (annotates, never licenses); otherwise `none`."""
    if (event_class in _UNKNOWN_H or event_class not in _CLASS) and not (rule_version == "1.2.0" and event_class in _ndh_EIGHT):
        return {"relation": "unknown", "licence": "none"}
    h_signs = set(_h_and_lords(event_class, chart, rule_version, "p1")[0])
    natal = chart["natal"]
    if lord in natal and _sign_index(natal[lord]) in h_signs:
        return {"relation": "occupancy", "licence": "scored"}
    owned = {_SIGN_LORD[_SIGNS[i]] for i in h_signs}
    if lord not in _NODES and lord in owned:
        return {"relation": "ownership", "licence": "scored"}
    if rule_version == "1.2.0" and lord in natal and level in (None, "md", "ad"):
        person = _ndh_AFFECTED_PERSON.get(event_class, "native") if affected_person is None else affected_person
        if lord in _ndh_KARAKATVA.get((event_class, person), ()):
            return {"relation": "karakatva", "licence": "scored"}
    disp = _SIGN_LORD[_SIGNS[_sign_index(natal[lord])]]
    if (disp in natal and _sign_index(natal[disp]) in h_signs) or (disp not in _NODES and disp in owned):
        return {"relation": "dispositorship", "licence": "testimony"}
    return {"relation": "none", "licence": "none"}


# ── pins and the digest preimage (1206 / draft §AM-5 item 3) ─────────────────

def derive_path_pin(event_class: str, chart: Mapping[str, Any], path_id: str,
                    rule_version: str, *, excluded_agents: Sequence[str],
                    path_exclusions: Mapping[str, Mapping[str, str | None]],
                    h_unknown_exclusion: Mapping[str, str | None] | None,
                    selected_versions: Mapping[str, str] | None = None) -> dict[str, Any]:
    """One pin as the verifier derives it. `path_exclusions` / `h_unknown_exclusion`
    are the verifier's OWN rulings ({reason, basis, ruling_ref}) — never read back from
    the stored pin under test."""
    p = path_id.lower()
    e = _exclusion_of(p, rule_version.lower(), path_exclusions)
    if e is not None:
        return {"path": p, "version": rule_version.lower(), "disposition": "excluded",
                "reason": e["reason"], "ruling": e.get("ruling_ref") or "",
                "basis": e["basis"], "obligations": []}
    if (rule_version == "1.2.0" and p in _H_DEPENDENT and event_class not in _ndh_EIGHT
            and selected_versions is not None and selected_versions.get(p) != rule_version):
        return {"path": p, "version": rule_version, "disposition": "excluded",
                "reason": "not_applicable_to_class", "ruling": "", "basis": "ruling:ND-H-20261005", "obligations": []}
    if p in _H_DEPENDENT and event_class in _UNKNOWN_H and not (rule_version == "1.2.0" and event_class in _ndh_EIGHT):
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
    final_parent = (event_class == "parental_event" and p == "p2"
                    and (selected_versions or {}).get("p3") == "1.2.0")
    if final_parent:
        return {"path": p, "version": rule_version.lower(), "disposition": "excluded",
                "reason": "not_applicable_to_class", "ruling": "", "basis": "ruling:ND-H-20261005", "obligations": []}
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


def _supersession_basis(path: str, old: str, new: str, event_class=None) -> str:
    if new == "1.2.0":
        return "ruling:ND-P2-20261005" if event_class == "bereavement" else "ruling:ND-H-20261005"
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
                                   h_unknown_exclusion=h_unknown_exclusion, selected_versions=selected) for v in versions}
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
            final_supersession = (v == "1.0.0" and chosen == "1.2.0" and path in ("p1", "p3", "p4")
                                  and (event_class in _ndh_EIGHT or (event_class == "bereavement" and path in ("p3", "p4"))))
            if final_supersession and pins[chosen]["disposition"] == "included":
                pin = {"path": path, "version": v, "disposition": "excluded",
                       "reason": "superseded_by_version", "ruling": "",
                       "basis": _supersession_basis(path, v, chosen, event_class), "obligations": []}
            if v != chosen and pin["disposition"] == "included":
                if pins[chosen]["disposition"] == "included" and (
                        _SUPERSEDED.get((path, v)) == chosen or
                        (chosen == "1.2.0" and v == "1.0.0" and path in ("p1", "p3", "p4"))):
                    pin = {"path": path, "version": v, "disposition": "excluded",
                           "reason": "superseded_by_version", "ruling": "",
                           "basis": _supersession_basis(path, v, chosen, event_class), "obligations": []}
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
    excluded_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Re-derive one class's inventory and its digest from the sealed paths, the
    snapshot and the consumed L1 facts. Raises `Unverifiable` rather than guess.
    `selected_versions` is the selection the verifier is TOLD (None ⇒ derived from the single sealed version
    or the included one — never from today's configuration).
    `excluded_agents` is the transiting bodies the stored tier never holds: None (the default, and what the verification JOB, the
    seal flow and serving always use) reads them from the generation's BOUND manifest scope and refuses an unknown scope; an
    explicit value is TOLD to the verifier by a caller that holds a validated, narrower authority than the manifest scope — the
    writer's in-build self-check of a TEST SLICE, whose stored scope is deliberately unknown to every vocabulary."""
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
    chart = read_chart_snapshot(conn, chart_id, generation)           # every class: P2 needs the natal Moon even where H is unknown (the snapshot's COPY, G12)
    pins = derive_class_pins(event_class, chart, sealed_paths,
                             excluded_agents=(bound_excluded_agents(conn, chart_id, generation)       # R9-10: the manifest's scope
                                              if excluded_agents is None else tuple(excluded_agents)),
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
    copies = snapshot_copies(conn, chart_id, generation)
    if copies is not None and copies["dashas"] is not None:         # G12: the rows the snapshot OWNS, not live L1
        from datetime import datetime as _dt, timezone as _tz
        rows = sorted((int(e["key"]["level_n"]), _dt.fromisoformat(e["key"]["start_iso"]).astimezone(_tz.utc),
                       _dt.fromisoformat(e["content"]["end_iso"]).astimezone(_tz.utc), str(e["content"]["lord_graha"]).lower())
                      for e in copies["dashas"])
    else:
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
#     chart — the single settled build selected by this verifier's own all-tier query;
#   * no consumed row lies wholly outside the horizon (an EXTRA) unless its whole (lord, level) group of the pinned
#     build is consumed — the P1 builder judges period_running_at from every row of an anchor (lord, level), so those
#     rows are ledgered whole (J-2a-P1L, B.3) — and no pinned-build row overlapping the horizon is missing (an OMITTED);
#   * no two pinned rows conflict on the same (level, parent, start) with different contract fields.

_C_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
_C_AYANAMSHA, _C_SYSTEM, _C_TIER = "lahiri_chitrapaksha", "vimshottari", _TWO_PASS_VERIFIED
_C_LEVELS = (1, 2, 3)


_SETTLEMENT_PATH = Path(__file__).with_name("dasha_settlement.json")


class SettlementRefused(Unverifiable):
    """Typed independent settlement refusal; no verification is earned."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def _load_dasha_settlement(chart_id: str) -> dict:
    """Verifier's own parser of the reviewed authority, with no reader imports."""
    try:
        source = _SETTLEMENT_PATH.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise SettlementRefused("settlement_malformed", "governed settlement is not UTF-8") from exc
    except OSError as exc:
        raise SettlementRefused("settlement_missing", "cannot read governed settlement") from exc
    try:
        doc = json.loads(source)
        if not isinstance(doc, dict) or doc["schema"] != "gochara_dasha_settlement/1":
            raise ValueError("settlement schema")
        if not isinstance(doc["header_comment"], str) or "reviewed PR" not in doc["header_comment"]:
            raise ValueError("review policy")
        tokens = doc["line"].split(" ")
        names = ["utc", "pos_build", "dash_build", "natal_fp", "vim13_fp", "vim13_rows", "dash_all_fp"]
        if tokens[:2] != ["L1_SETTLED", "v1"] or len(tokens) != 9:
            raise ValueError("settlement line format")
        fields = {}
        for name, token in zip(names, tokens[2:]):
            key, value = token.split("=")
            if key != name:
                raise ValueError("settlement line keys")
            fields[key] = value
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", fields["utc"]):
            raise ValueError("settlement timestamp")
        datetime.strptime(fields["utc"], "%Y-%m-%dT%H:%M:%SZ")
        for name in ("pos_build", "dash_build", "natal_fp", "vim13_fp", "dash_all_fp"):
            if not re.fullmatch(r"[0-9a-f]{8}", fields[name]):
                raise ValueError("settlement hex field")
        if not re.fullmatch(r"[0-9]+", fields["vim13_rows"]):
            raise ValueError("settlement row count")
        fields["vim13_rows"] = int(fields["vim13_rows"])
        if type(doc["vim13_rows"]) is not int or doc["vim13_rows"] <= 0:
            raise ValueError("settlement row count type")
        if fields != {name: doc[name] for name in names}:
            raise ValueError("line differs from stored settlement fields")
        if any(str(UUID(doc[name])) != doc[name] for name in ("run_id", "chart_id")):
            raise ValueError("settlement UUID")
        if doc["run_id"].split("-")[0] != fields["dash_build"]:
            raise ValueError("settlement run prefix")
        origin = doc["provenance"]
        if (not isinstance(origin, dict)
                or origin["source"] != "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
                or not re.fullmatch(r"[0-9a-f]{40}", origin["commit"])
                or origin["heading"] != "L1_SETTLED v1"
                or not isinstance(origin["release_receipt"], str) or not origin["release_receipt"]
                or origin["rebuild_run"] != doc["run_id"]):
            raise ValueError("settlement provenance")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise SettlementRefused("settlement_malformed", "invalid governed settlement shape or line") from exc
    if doc["chart_id"] != str(chart_id):
        raise SettlementRefused("chart_not_settled", f"chart {chart_id} has no settlement entry")
    return doc


def _group_wholly_consumed(row: Mapping[str, Any], pinned: Sequence[Mapping[str, Any]], consumed_ids: set) -> bool:
    """Is every pinned-build row of `row`'s (lord, level) in the consumed set? The only way a row outside the horizon is
    a consulted anchor row rather than an extra: the builder reads an anchor's rows whole, never a part."""
    key = (str(row["lord_graha"]).lower(), int(row["level_n"]))
    group = [str(p["dasha_row_id"]) for p in pinned if (str(p["lord_graha"]).lower(), int(p["level_n"])) == key]
    return bool(group) and all(g in consumed_ids for g in group)


def check_dasha_population(consumed: Sequence[Mapping[str, Any]], pinned: Sequence[Mapping[str, Any]], *,
                           chart_id: str, horizon: tuple, consumed_ids: Sequence[str]) -> list[str]:
    """Pure: the violations (empty = the population is the §4.0 population). `consumed` are the rows the
    snapshot's ids resolve to for this chart; `pinned` the rows the contract selects (ayanāṃśa, system,
    tier, build, levels) — both with level_n, start_iso, end_iso, lord_graha, build_id, system_id,
    ayanamsha_id, verification_pass_status, parent_row_id, dasha_row_id. This is the check of a LEGACY snapshot (ids only, written before migration
    1305); a snapshot that OWNS a copy is judged by `copy_contract_violations` (the capture contract, the database's own codes)."""
    lo, hi = horizon
    out: list[str] = []
    found = {str(r["dasha_row_id"]) for r in consumed}
    for rid in consumed_ids:
        if str(rid) not in found:
            out.append(f"consumed id {rid} resolves to no row of this chart")
    # Validate both sides: supplied consumed rows cannot assert a different build
    # from the population selected by our own guarded query.
    population = list(consumed) + list(pinned)
    # Validate admitted input before horizon clipping or PostgreSQL range
    # aggregation can erase a zero-length/reversed period (J4P-B4). This is
    # the verifier's own detector; do not import the reader's validation.
    for r in population:
        start, end = r.get("start_iso"), r.get("end_iso")
        if (not isinstance(start, datetime) or not isinstance(end, datetime)
                or start.tzinfo is None or end.tzinfo is None or end <= start):
            out.append(f"row {r['dasha_row_id']}: invalid period (expected positive timezone-aware bounds)")
    if out:
        return out
    builds = {str(r["build_id"]) for r in population if r["build_id"] is not None}
    if any(r["build_id"] is None for r in population):
        out.append("dasha_build_null: a daśā row carries a NULL build_id")
    if len(builds) > 1:
        out.append(f"several builds {sorted(builds)} consumed/selected — an unpinned read")
    if str(chart_id) == _C_CHART and not pinned:
        out.append("dasha_build_unsettled: no two_pass_verified Vimśottarī population")
    for r in consumed:
        rid = r["dasha_row_id"]
        if r["ayanamsha_id"] != _C_AYANAMSHA or r["system_id"] != _C_SYSTEM:
            out.append(f"row {rid}: ayanāṃśa/system {r['ayanamsha_id']}/{r['system_id']} is not "
                       f"{_C_AYANAMSHA}/{_C_SYSTEM}")
        if r["verification_pass_status"] != _C_TIER:
            out.append(f"row {rid}: tier {r['verification_pass_status']!r} is not {_C_TIER}")
        if int(r["level_n"]) not in _C_LEVELS:
            out.append(f"row {rid}: level {r['level_n']} is not MD/AD/PD")
        if not (r["start_iso"] < hi and r["end_iso"] > lo) and not _group_wholly_consumed(r, pinned, found):
            out.append(f"row {rid}: lies wholly outside the horizon (an extra row)")
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


# ── the CAPTURE CONTRACT of a copy-bearing snapshot (G12 route 1, round 6) ───────────────────────────────────────────────────────────────────────────────
# An INDEPENDENT Python statement of the contract the database states in `ka_gochara_search_copy_violations` (migration 1305): same codes, one violation per
# offending element, judged over a COPY and nothing else (no connection is taken). The two implementations are run over the same shapes by
# tests/l3/gochara/test_g12_snapshot_copy.py and must agree code for code. Invariant (R1): what is validated is exactly what is stored — the object judged is the
# stored jsonb value, never the upstream rows it was built from. Invariant (R2): with `eligibility=False` nothing here reads a tier or a build.

_C_FACT_SUBJECTS = ("LAGNA",) + tuple(_FACT_SUBJECT)
_C_FACT_CATEGORY, _C_FACT_KEY = "graha_position", "longitude_sidereal"


def _well_formed(e: Any) -> bool:
    return isinstance(e, Mapping) and all(isinstance(e.get(block), Mapping) for block in ("key", "content", "metadata"))


def _key_text(key: Any) -> str:
    import json
    return json.dumps(key, sort_keys=True, default=str)


def fact_copy_violations(copy: Any) -> list[tuple[str, str]]:
    """The fact half of the contract: every element is a natal longitude of the canonical ayanāṃśa for one of the ten subjects; each subject exactly once; each
    with a numeric value. Returns (code, detail) pairs; [] = satisfied."""
    out: list[tuple[str, str]] = []
    if not isinstance(copy, (list, tuple)):
        out.append(("copy_malformed", "the fact copy is not a JSON array"))
        copy = []                                  # ... and it therefore holds none of the required members (reported below, as the database does)
    counts = {s: 0 for s in _C_FACT_SUBJECTS}
    for i, e in enumerate(copy, 1):
        if not _well_formed(e):
            out.append(("copy_malformed", f"fact element {i} is not {{key, content, metadata}}"))
            continue
        k = e["key"]
        if not (k.get("ayanamsha_id") == _C_AYANAMSHA and k.get("fact_category") == _C_FACT_CATEGORY and k.get("fact_key") == _C_FACT_KEY
                and k.get("fact_subject") in counts):
            out.append(("fact_out_of_scope", f"fact {_key_text(k)} is not a natal longitude of the canonical ayanamsha for a required subject"))
            continue
        counts[k["fact_subject"]] += 1
        num = e["content"].get("fact_value_num")
        if isinstance(num, bool) or not isinstance(num, (int, float, Decimal)):
            out.append(("fact_value_missing", f"fact {_key_text(k)} has no numeric value"))
    for subject, n in counts.items():
        if n == 0:
            out.append(("required_fact_missing", f"subject {subject}"))
        elif n > 1:
            out.append(("required_fact_duplicate", f"subject {subject} has {n} rows (natural key not unique)"))
    return out


def _ts(value: Any):
    from datetime import datetime as _dt, timezone as _tz
    if value is None:
        return None
    if isinstance(value, _dt):
        return value.astimezone(_tz.utc)
    return _dt.fromisoformat(str(value)).astimezone(_tz.utc)


def _period_of_element(e: Mapping[str, Any]) -> dict[str, Any]:
    """One copy element as the flat record the period contract reads (identity from key/content, ids, build and tier from metadata)."""
    k, c, m = e["key"], e["content"], e["metadata"]
    return {"key": _key_text(k), "ay": k.get("ayanamsha_id"), "sy": k.get("system_id"), "lv": None if k.get("level_n") is None else int(k["level_n"]),
            "st": _ts(k.get("start_iso")), "kp": k.get("kp_sublevel") or "", "en": _ts(c.get("end_iso")), "lord": c.get("lord_graha"),
            "plv": None if c.get("parent_level_n") is None else int(c["parent_level_n"]), "pst": _ts(c.get("parent_start_iso")), "lpath": c.get("lord_path"),
            "id": None if m.get("dasha_row_id") is None else str(m["dasha_row_id"]), "pid": None if m.get("parent_row_id") is None else str(m["parent_row_id"]),
            "build": None if m.get("build_id") is None else str(m["build_id"]), "tier": m.get("verification_pass_status")}


def period_contract_violations(periods: Sequence[Mapping[str, Any]], horizon: tuple, *, eligibility: bool) -> list[tuple[str, str]]:
    """The period half of the contract over flat period records (see `_period_of_element`): scope, horizon, positive length, unique row ids; each level MD/AD/PD
    present, unique by start, contiguous (no gap, no overlap) and covering the horizon; the HIERARCHY (every AD/PD: its natural parent pointer names a period of
    the population at the level above, that period's row id is the row's parent_row_id, it contains the row, and the lord path is the parent's plus the row's
    lord); and, only with `eligibility`, the population's OWN tier and build (two_pass_verified, a build on every row, one build)."""
    lo, hi = horizon
    out: list[tuple[str, str]] = []
    scope = [p for p in periods if p["ay"] == _C_AYANAMSHA and p["sy"] == _C_SYSTEM and p["lv"] in _C_LEVELS]
    for p in periods:
        if not (p["ay"] == _C_AYANAMSHA and p["sy"] == _C_SYSTEM and p["lv"] in _C_LEVELS):
            out.append(("period_out_of_scope", f"period {p['key']} is not a Vimśottarī MD/AD/PD of the canonical ayanamsha"))
    d = [p for p in scope if p["st"] is not None and p["en"] is not None and p["st"] < hi and p["en"] > lo]
    inside = {id(p) for p in d}
    for p in scope:
        if id(p) not in inside:
            out.append(("period_outside_horizon", f"period {p['key']} ending {p['en']} does not overlap the horizon {lo}..{hi}"))
    for p in d:
        if not p["en"] > p["st"]:
            out.append(("period_not_positive", f"level {p['lv']} period starting {p['st']} ends {p['en']} (not after its start)"))
    seen: dict[Any, int] = {}
    for p in periods:
        seen[p["id"]] = seen.get(p["id"], 0) + 1
    for rid, n in seen.items():
        if n > 1 or rid is None:
            out.append(("period_row_id_duplicate", f"row id {rid} is carried by {n} elements"))
    if eligibility:
        for p in periods:
            if p["tier"] != _C_TIER:
                out.append(("period_tier_ineligible", f"period {p['key']} (row {p['id']}) carries tier {p['tier']}, not {_C_TIER}"))
            if p["build"] is None:
                out.append(("period_build_missing", f"period {p['key']} (row {p['id']}) carries no build id"))
        builds = sorted({p["build"] for p in periods if p["build"] is not None})
        if len(builds) > 1:
            out.append(("dasha_builds_mixed", f"the copy holds rows of {len(builds)} builds: {', '.join(builds)}"))
    for level in _C_LEVELS:
        rows = sorted((p for p in d if p["lv"] == level), key=lambda p: (p["st"], p["en"], p["id"] or ""))
        if not rows:
            out.append(("required_level_missing", f"level {level} has no period overlapping the horizon"))
            continue
        for prev, nxt in zip(rows, rows[1:]):
            if nxt["st"] == prev["st"]:
                out.append(("required_period_duplicate", f"level {level} start {nxt['st']} (another period of the level shares the start)"))
            if nxt["st"] > prev["st"] and nxt["st"] < prev["en"]:
                out.append(("required_period_overlap", f"level {level} period starting {nxt['st']} begins before the previous ends ({prev['en']})"))
            if nxt["st"] > prev["en"]:
                out.append(("required_period_gap", f"level {level} period starting {nxt['st']} begins after the previous ends ({prev['en']})"))
        if min(p["st"] for p in rows) > lo:
            out.append(("required_horizon_start_uncovered", f"level {level} first period starts {min(p['st'] for p in rows)} after the horizon start {lo}"))
        if max(p["en"] for p in rows) < hi:
            out.append(("required_horizon_end_uncovered", f"level {level} last period ends {max(p['en'] for p in rows)} before the horizon end {hi}"))
    for c in d:
        if c["lv"] == 1:
            if c["lpath"] != c["lord"]:
                out.append(("lord_path_inconsistent", f"level 1 period starting {c['st']} carries lord path {c['lpath']}, which is not its own lord"))
            if c["pid"] is not None or c["plv"] is not None or c["pst"] is not None:          # a ROOT has no parent, of this or of any other chart, ayanamsha or system
                out.append(("root_has_parent", f"level 1 period starting {c['st']} carries a parent (row {c['pid']}, level {c['plv']}): a Mahādaśā is a root"))
            continue
        parents = [p for p in d if p["ay"] == c["ay"] and p["sy"] == c["sy"] and p["lv"] == c["lv"] - 1 and c["plv"] == p["lv"] and c["pst"] == p["st"]]
        if not parents:
            out.append(("required_parent_missing", f"level {c['lv']} period starting {c['st']} has no parent present at level {c['lv'] - 1} of the same ayanamsha and system"))
            continue
        if c["pid"] is None or not any(p["id"] == c["pid"] for p in parents):
            out.append(("required_parent_id_mismatch", f"level {c['lv']} period starting {c['st']} hangs under row {c['pid']}, which is not the row the copy holds at its parent's natural key"))
        if any(not (c["st"] >= p["st"] and c["en"] <= p["en"]) for p in parents):
            out.append(("required_parent_not_containing", f"level {c['lv']} period {c['st']} .. {c['en']} is not inside its parent"))
        if not any(c["lpath"] == (None if p["lpath"] is None or c["lord"] is None else f"{p['lpath']}/{c['lord']}") for p in parents):
            out.append(("lord_path_inconsistent", f"level {c['lv']} period starting {c['st']} carries lord path {c['lpath']}, which is not its parent's path plus its own lord"))
    return out


def dasha_copy_violations(copy: Any, horizon: tuple, *, eligibility: bool = True) -> list[tuple[str, str]]:
    """The period half of the contract over a daśā COPY (the stored jsonb array of {key, content, metadata})."""
    out: list[tuple[str, str]] = []
    if not isinstance(copy, (list, tuple)):
        out.append(("copy_malformed", "the daśā copy is not a JSON array"))
        copy = []
    periods = []
    for i, e in enumerate(copy, 1):
        if not _well_formed(e):
            out.append(("copy_malformed", f"daśā element {i} is not {{key, content, metadata}}"))
        else:
            periods.append(_period_of_element(e))
    return out + period_contract_violations(periods, horizon, eligibility=eligibility)


def copy_contract_violations(facts: Any, dashas: Any, horizon: tuple, *, eligibility: bool = True) -> list[tuple[str, str]]:
    """The whole capture contract over a snapshot's two copies — the Python twin of `public.ka_gochara_search_copy_violations(facts, dashas, horizon, eligibility)`."""
    return fact_copy_violations(facts) + dasha_copy_violations(dashas, horizon, eligibility=eligibility)


def _periods_of_live_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Flat period records derived by THIS verifier from live `chart_dashas` rows (the natural parent pointer and the lord path are computed here from the
    rows' own parent ids, never read from the database's copy functions): the independent side of the capture comparison."""
    by_id = {str(r["dasha_row_id"]): r for r in rows}
    out = []
    for r in rows:
        parent = by_id.get(str(r["parent_row_id"])) if r["parent_row_id"] is not None else None
        lords, cur, depth = [], r, 0
        while cur is not None and depth < 8:
            lords.append(str(cur["lord_graha"]).lower())
            cur = by_id.get(str(cur["parent_row_id"])) if cur["parent_row_id"] is not None else None
            depth += 1
        key = {"ayanamsha_id": r["ayanamsha_id"], "system_id": r["system_id"], "level_n": int(r["level_n"]), "start_iso": _ts(r["start_iso"]).isoformat(),
               "kp_sublevel": r.get("kp_sublevel") or ""}
        out.append({"key": _key_text(key), "ay": r["ayanamsha_id"], "sy": r["system_id"], "lv": int(r["level_n"]), "st": _ts(r["start_iso"]),
                    "kp": r.get("kp_sublevel") or "", "en": _ts(r["end_iso"]), "lord": str(r["lord_graha"]).lower(),
                    "plv": None if parent is None else int(parent["level_n"]), "pst": None if parent is None else _ts(parent["start_iso"]),
                    "lpath": "/".join(reversed(lords)), "id": str(r["dasha_row_id"]), "pid": None if r["parent_row_id"] is None else str(r["parent_row_id"]),
                    "build": None if r["build_id"] is None else str(r["build_id"]), "tier": r["verification_pass_status"]})
    return out


_COMPARED = ("ay", "sy", "lv", "st", "kp", "en", "lord", "plv", "pst", "lpath", "pid", "build", "tier")


def _manifest_horizon(conn: Any, chart_id: str, generation: str) -> tuple:
    row = conn.execute("SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                       (chart_id, generation)).fetchone()
    row = None if row is None else (tuple(row.values()) if isinstance(row, dict) else tuple(row))
    if row is None or row[0] is None or row[1] is None:
        raise Unverifiable("no bound, finite manifest horizon to judge the consumed population against")
    return row[0], row[1]


def _dasha_settlement_of(conn: Any, chart_id: str) -> dict:
    # The verifier imports nothing from the builder (test_the_verifier_imports_nothing_from_the_builder), so the rehearsal
    # connection is recognised by a marker on its CLASS, not by an import; a raw or mocked connection never carries it.
    if getattr(type(conn), "synthetic_settlement_authority", False) is True:
        return conn.settlement(chart_id)
    return _load_dasha_settlement(chart_id)


def validate_consumed_dasha_population(conn: Any, *, chart_id: str, generation: str, against_live: bool = False) -> dict:
    """The §4.0 population contract.

    A snapshot that OWNS a copy (G12 route 1) is judged ON ITS STORED COPY, by `copy_contract_violations` (both copies, the bound manifest horizon, eligibility
    on): no live L1 is read, so the verification of a generation never depends on what a later rebuild did upstream. The comparison with live L1 after capture
    is the drift REPORT (`staleness`) and the database gate, never a failure to verify.

    `against_live=True` is the CAPTURE-TIME check the writer runs once, right after the snapshot is taken: in addition to the above, this verifier derives the
    upstream scope ITSELF from live `chart_dashas` (every Vimśottarī / lahiri MD, AD, PD row overlapping the horizon, EVERY tier and build), judges it by the
    same contract, and requires the stored copy to be exactly that scope, row for row and field for field. The governed settlement pin is enforced there, at capture
    time, where it belongs. (I) INTERPRETATION: settlement governs capture and legacy reads; an owned copy remains verifiable after a later rebuild. A LEGACY snapshot (no copy) keeps the 1206-era check against live L1."""
    settlement = _dasha_settlement_of(conn, chart_id) if against_live else None
    snap = conn.execute(
        "SELECT consumed_dasha_row_ids FROM public.ka_gochara_search_input_snapshot"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if snap is None:
        raise Unverifiable("no search-input snapshot to validate the consumed daśā population against")
    ids = [str(x) for x in snap[0]]
    copies = snapshot_copies(conn, chart_id, generation)
    has_copy = copies is not None and copies["dashas"] is not None
    cols = ("dasha_row_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id, system_id,"
            " ayanamsha_id, verification_pass_status, kp_sublevel")

    def rows(sql, params):
        names = [c.strip() for c in cols.split(",")]
        return [dict(zip(names, r)) for r in conn.execute(sql, params).fetchall()]

    if has_copy:
        horizon = _manifest_horizon(conn, chart_id, generation)
        problems = copy_contract_violations(copies["facts"], copies["dashas"], horizon, eligibility=True)
        if problems:
            raise Unverifiable("consumed daśā population (the snapshot's copy) violates the capture contract: " + "; ".join(f"{c} ({d})" for c, d in problems))
        stored = [_period_of_element(e) for e in copies["dashas"]]
        if not against_live:
            return {"consumed": len(stored), "pinned_overlapping": len(stored), "source": "snapshot_copy"}
    else:
        horizon = conn.execute(
            "SELECT min(lower(horizon)), max(upper(horizon)) FROM public.ka_gochara_search_inventory"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
        if horizon is None or horizon[0] is None:
            raise Unverifiable("no inventory horizon to validate the consumed daśā population against")
    settlement = settlement or _dasha_settlement_of(conn, chart_id)
    # G6 (verifier's OWN query, builder code not imported): every Vimśottarī / lahiri row of the chart — all tiers, all levels — is ONE build,
    # the governed settled-build rule is independent of the builder's contract code
    builds = sorted(str(r[0]) for r in conn.execute(
        "SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s",
        (chart_id, _C_SYSTEM, _C_AYANAMSHA)).fetchall())
    if len(builds) > 1:
        raise SettlementRefused("settled_build_ambiguous", f"chart {chart_id} carries several builds {builds} (every tier)")
    if builds == ["NULL"]:
        raise Unverifiable(f"dasha_build_null: chart {chart_id} carries a NULL Vimśottarī build_id — refusing")
    eligible = sorted(str(r[0]) for r in conn.execute(
        "SELECT DISTINCT build_id::text FROM public.chart_dashas WHERE chart_id = %s AND system_id = %s"
        " AND ayanamsha_id = %s AND verification_pass_status = %s AND level_n = ANY(%s)",
        (chart_id, _C_SYSTEM, _C_AYANAMSHA, _C_TIER, list(_C_LEVELS))).fetchall())
    if len(eligible) > 1:
        raise SettlementRefused("settled_build_ambiguous", f"several eligible builds {eligible}")
    build = settlement["run_id"]
    if eligible != [build]:
        raise SettlementRefused("settled_build_absent", f"named build {build} is not eligible for chart {chart_id}")
    if has_copy:
        live = _periods_of_live_rows(rows(f"SELECT {cols} FROM public.chart_dashas WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = %s"
                                          " AND level_n = ANY(%s)", (chart_id, _C_AYANAMSHA, _C_SYSTEM, list(_C_LEVELS))))
        lo, hi = horizon
        scope = [p for p in live if p["st"] < hi and p["en"] > lo]                      # the upstream scope: EVERY tier and build
        problems = [f"upstream {c} ({d})" for c, d in period_contract_violations(scope, horizon, eligibility=True)]
        mine, theirs = {p["id"]: p for p in stored}, {p["id"]: p for p in scope}
        for rid in sorted(set(theirs) - set(mine)):
            problems.append(f"upstream_row_not_in_copy (row {rid} {theirs[rid]['key']} tier {theirs[rid]['tier']} build {theirs[rid]['build']} is in the "
                            "required scope but the snapshot's copy does not hold it)")
        for rid in sorted(set(mine) - set(theirs), key=str):
            problems.append(f"copy_row_not_in_upstream_scope (row {rid} {mine[rid]['key']} is in the snapshot's copy but not in the upstream scope)")
        for rid in sorted(set(mine) & set(theirs)):
            fields = [f for f in _COMPARED if mine[rid][f] != theirs[rid][f]]
            if fields:
                problems.append(f"copy_row_differs_from_upstream (row {rid} {mine[rid]['key']}: {fields})")
        if problems:
            raise Unverifiable("consumed daśā population violates the capture contract against live L1: " + "; ".join(problems))
        result = {"consumed": len(stored), "pinned_overlapping": len(scope), "source": "snapshot_copy_and_live"}
        if settlement.get("synthetic") is True:
            result.update(synthetic_settlement=True, production_acceptance=False)
        return result
    consumed = rows(f"SELECT {cols} FROM public.chart_dashas WHERE chart_id = %s"
                    " AND dasha_row_id = ANY(%s::uuid[])", (chart_id, ids))
    pinned = rows(f"SELECT {cols} FROM public.chart_dashas WHERE chart_id = %s AND ayanamsha_id = %s"
                  " AND system_id = %s AND verification_pass_status = %s AND level_n = ANY(%s)"
                  " AND build_id = %s::uuid",
                  (chart_id, _C_AYANAMSHA, _C_SYSTEM, _C_TIER, list(_C_LEVELS), build))
    problems = check_dasha_population(consumed, pinned, chart_id=chart_id,
                                      horizon=(horizon[0], horizon[1]), consumed_ids=ids)
    if problems:
        raise Unverifiable("consumed daśā population violates the §4.0 read contract: " + "; ".join(problems))
    result = {"consumed": len(consumed), "pinned_overlapping": sum(
        1 for r in pinned if r["start_iso"] < horizon[1] and r["end_iso"] > horizon[0])}
    if settlement.get("synthetic") is True:
        result.update(synthetic_settlement=True, production_acceptance=False)
    return result


__all__ += ["check_dasha_population", "validate_consumed_dasha_population", "copy_contract_violations", "fact_copy_violations",
            "dasha_copy_violations", "period_contract_violations"]


# Snapshot-bound record verification SQL; deliberately independent of the builder.
#: the pins of the "held" probe below (the verifier's own §4.0 literals: ayanāṃśa, system, tier)
RECORD_SUPPORT_PINS = {"ayan": _C_AYANAMSHA, "system": _C_SYSTEM, "tier": _C_TIER}
# J-2a run 1: the SNAPSHOT binds only the daśā rows OVERLAPPING the horizon, so it fixes the running intervals `m` (a contact
# is clipped to the horizon, so a row wholly outside it cannot change contact ∩ m) but it CANNOT say whether L1 holds a
# row for an anchor (lord, level) at all. "No rows" (⇒ unrestricted + `unknown`, A5_3 brief v1.27) means no pinned row
# for that (lord, level) ANYWHERE in the settled build — `held` probes exactly that; a lord that is held but not running
# in the horizon has an empty running set (`false`), never `unknown` (§N.8: has_rows must measure its own claim).
# (I) INTERPRETATION (merge of main's J-2a with this PR's G12 copy): the `held` probe of a LEGACY snapshot (ids, no copy)
# is main's live probe; for a snapshot WITH a copy the statement must not even NAME the live relation (the G12 claim), so
# `held` there is read from the snapshot ALONE: the copy's rows UNION `consumed_dasha_held`, the (lord, level) pairs the
# build holds that the database recorded at capture (the copy carries only horizon-overlapping rows, so on its own it
# cannot tell "held, running outside the horizon" from "absent"). The copy-reading builder
# (`make_period_rows_for_snapshot(...).holds`) reads the same two things, so builder and verifier agree on what "no rows"
# means for a copy snapshot. A snapshot captured before that record existed (`consumed_dasha_held` NULL) falls back to the
# copy alone — the pre-record behaviour, which cannot see a held-but-outside lord.
RECORD_SUPPORT_SQL_TEMPLATE = """
WITH snap AS (
  SELECT s.consumed_dasha_row_ids AS ids,
         (to_jsonb(s) -> 'consumed_dasha_rows') AS copy,     -- the snapshot's COPY (1305, G12); JSON null / absent for a legacy snapshot
         (to_jsonb(s) -> 'consumed_dasha_held') AS held_rec  -- the (lord, level) pairs the pinned build HOLDS, recorded at capture; JSON null / absent before that record existed
  FROM public.ka_gochara_search_input_snapshot s
  WHERE s.chart_id = %(chart)s AND s.generation = %(gen)s),
src AS (
  SELECT lower(e.value #>> '{content,lord_graha}') AS lord, (e.value #>> '{key,level_n}')::int AS level_n,
         (e.value #>> '{key,start_iso}')::timestamptz AS s, (e.value #>> '{content,end_iso}')::timestamptz AS e
  FROM snap, jsonb_array_elements(snap.copy) AS e(value)
  WHERE jsonb_typeof(snap.copy) = 'array'@@LEGACY_ARM@@),
runs AS (
  SELECT lord, level_n, range_agg(tstzrange(s, e, '[)')) AS m
  FROM src WHERE level_n IN (1, 2, 3)
  GROUP BY 1, 2),
@@HELD@@rec AS (
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
       (CASE WHEN held.lord IS NULL THEN rec.contact ELSE rec.contact * COALESCE(runs.m, '{}'::tstzmultirange) END)::text AS expected_text,
       rec.stored = (CASE WHEN held.lord IS NULL THEN rec.contact ELSE rec.contact * COALESCE(runs.m, '{}'::tstzmultirange) END) AS equal,
       isempty(CASE WHEN held.lord IS NULL THEN rec.contact ELSE rec.contact * COALESCE(runs.m, '{}'::tstzmultirange) END) AS expected_empty,
       rec.result, held.lord IS NOT NULL AS has_rows
FROM rec LEFT JOIN held ON (held.lord, held.level_n) = (rec.lord, rec.level_n)
         LEFT JOIN runs ON (runs.lord, runs.level_n) = (rec.lord, rec.level_n)
"""

# A snapshot WITH a copy (1305, G12) is read from the copy ALONE: the statement must not even NAME the live relation (so it runs with live L1 gone, and
# without privileges on it). Only a LEGACY snapshot (ids, no copy) keeps the live arm, as before.
RECORD_SUPPORT_LEGACY_ARM = """
  UNION ALL
  SELECT lower(d.lord_graha), d.level_n, d.start_iso, d.end_iso
  FROM public.chart_dashas d, snap
  WHERE (snap.copy IS NULL OR jsonb_typeof(snap.copy) <> 'array')                -- LEGACY snapshot: read by id from live L1, as before
    AND d.chart_id = %(chart)s AND d.dasha_row_id = ANY (snap.ids)"""
RECORD_SUPPORT_HELD_LIVE = """held AS (
  SELECT DISTINCT lower(d.lord_graha) AS lord, d.level_n
  FROM public.chart_dashas d
  WHERE d.chart_id = %(chart)s AND d.ayanamsha_id = %(ayan)s AND d.system_id = %(system)s
    AND d.verification_pass_status = %(tier)s AND d.level_n IN (1, 2, 3)
    AND d.build_id IN (SELECT x.build_id FROM public.chart_dashas x, snap WHERE x.chart_id = %(chart)s
                       AND x.dasha_row_id = ANY (snap.ids))),
"""
RECORD_SUPPORT_HELD_COPY = """held AS (
  SELECT DISTINCT lord, level_n FROM src
  UNION                                                           -- a lord the build holds but that runs wholly outside the horizon is held, not absent
  SELECT lower(e.value ->> 'lord'), (e.value ->> 'level_n')::int
  FROM snap, jsonb_array_elements(snap.held_rec) AS e(value)
  WHERE jsonb_typeof(snap.held_rec) = 'array'),
"""
RECORD_SUPPORT_SQL_COPY = RECORD_SUPPORT_SQL_TEMPLATE.replace("@@LEGACY_ARM@@", "").replace("@@HELD@@", RECORD_SUPPORT_HELD_COPY)
RECORD_SUPPORT_SQL = RECORD_SUPPORT_SQL_TEMPLATE.replace("@@LEGACY_ARM@@", RECORD_SUPPORT_LEGACY_ARM).replace("@@HELD@@", RECORD_SUPPORT_HELD_LIVE)
