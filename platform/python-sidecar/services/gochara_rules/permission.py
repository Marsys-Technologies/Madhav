"""permission_per_instant (GOCHARA_DESIGN_SPECS_v1_4 §4, with the §4.0 daśā
read contract and its pinned literal rows).

Half-open [start_iso, end_iso) intervals throughout: an instant t = end_iso
belongs to the NEXT row. MD/AD/PD per-level licence ∈ {scored, testimony,
none} states whether P1 prerequisite (2) holds for that level's lord and with
which operator role; class licence = union over levels (licensed iff some
level scored); levels are never collapsed into one boolean. Aṣṭottarī is
absent on this chart with both failed conditions named (O-PP-3, D-RQ7).

Reference rows below are literal constant data, source =
"GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]" (verified 2026-09-30, tier
two_pass_verified, build 75524b3e-102a-43ec-8cee-3f57fee752c3 — RE-PINNED at SETTLED-1 (S-L1, 2026-10-04) from the first pin, build
1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb verified 2026-09-30: lords and row counts unchanged, every boundary shifted by about 6993 s).
"""
from __future__ import annotations

from .frames import Frame, SIGN_LORDS, frame_sign, house_of, sign_of
from .records import RelationshipRecord
from . import registry as _registry
from .registry import RULE_VERSION, signature_houses

# The tier value comes from the sanctioned vocabulary module — the literal in
# an emit position outside brahmagyan/verification_vocab.py is a TAP-6 gate
# violation (M-22). Here it is a source label on pinned [L] data, not an
# emitted verification status.
from brahmagyan.verification_vocab import TWO_PASS_VERIFIED

DASHA_READ_CONTRACT = {
    "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
    "ayanamsha_id": "lahiri_chitrapaksha",
    "system_id": "vimshottari",
    "build_id": "75524b3e-102a-43ec-8cee-3f57fee752c3",
    "tier": TWO_PASS_VERIFIED,
    "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]",
}

# Pinned reference rows (§4.0 [L]; every row id printed in full — C6).
MD_ROWS: tuple[dict, ...] = (
    {"row_id": "1d1a80c0-53c6-5ff7-930a-52ff0f306cae", "level": "MD",
     "lord": "Mercury", "parent_row_id": None,
     "start_iso": "2010-08-18T17:46:56Z", "end_iso": "2027-08-18T23:46:56Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
)

AD_ROWS: tuple[dict, ...] = (
    {"row_id": "2103a226-b814-5ec7-b987-dffb421d5288", "level": "AD",
     "lord": "Ketu", "parent_row_id": "1d1a80c0-53c6-5ff7-930a-52ff0f306cae",
     "start_iso": "2013-01-14T09:13:56Z", "end_iso": "2014-01-11T14:10:56Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "68789a8d-85ae-5eb5-8d88-a8743b23073c", "level": "AD",
     "lord": "Moon", "parent_row_id": "1d1a80c0-53c6-5ff7-930a-52ff0f306cae",
     "start_iso": "2017-09-17T22:16:56Z", "end_iso": "2019-02-17T08:46:56Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "c4821baa-f4b0-51d5-b035-28ba2bd36a78", "level": "AD",
     "lord": "Mars", "parent_row_id": "1d1a80c0-53c6-5ff7-930a-52ff0f306cae",
     "start_iso": "2019-02-17T08:46:56Z", "end_iso": "2020-02-14T13:43:56Z",
     "source": "GOCHARA_TEST_ORACLES_v1_4 O-PP-2 [L]"},
    {"row_id": "a91faefa-f0d9-5a5d-950c-0adafb276fc7", "level": "AD",
     "lord": "Rahu", "parent_row_id": "1d1a80c0-53c6-5ff7-930a-52ff0f306cae",
     "start_iso": "2020-02-14T13:43:56Z", "end_iso": "2022-09-02T23:01:56Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
)

PD_ROWS: tuple[dict, ...] = (
    {"row_id": "65e30373-9db8-5606-a2bb-7c540114e135", "level": "PD",
     "lord": "Mercury", "parent_row_id": "2103a226-b814-5ec7-b987-dffb421d5288",
     "start_iso": "2013-11-21T06:40:51Z", "end_iso": "2014-01-11T14:10:56Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "91980ae7-4081-5373-8781-c8a31b03d4ef", "level": "PD",
     "lord": "Venus", "parent_row_id": "68789a8d-85ae-5eb5-8d88-a8743b23073c",
     "start_iso": "2018-10-28T06:06:26Z", "end_iso": "2019-01-22T11:51:26Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "48338f36-94c3-5495-b946-68f7f6e512bc", "level": "PD",
     "lord": "Venus", "parent_row_id": "a91faefa-f0d9-5a5d-950c-0adafb276fc7",
     "start_iso": "2021-10-04T05:05:59Z", "end_iso": "2022-03-08T10:38:59Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "d4d08aca-8995-51f3-a8ba-f9238a5311b3", "level": "PD",
     "lord": "Saturn", "parent_row_id": "c4821baa-f4b0-51d5-b035-28ba2bd36a78",
     "start_iso": "2019-06-21T02:52:24Z", "end_iso": "2019-08-17T11:15:26Z",
     "source": "GOCHARA_TEST_ORACLES_v1_4 O-PP-2 [L]"},
    {"row_id": "f72e343c-b877-516b-a089-54494031aa2d", "level": "PD",
     "lord": "Saturn", "parent_row_id": "a91faefa-f0d9-5a5d-950c-0adafb276fc7",
     "start_iso": "2020-11-04T11:10:02Z", "end_iso": "2021-03-31T22:26:23Z",
     "source": "GOCHARA_TEST_ORACLES_v1_4 O-PP-2 [L]"},
)

_LEVEL_ROWS = {"MD": MD_ROWS, "AD": AD_ROWS, "PD": PD_ROWS}

NODES = frozenset({"Rahu", "Ketu"})


def _row_at(rows: tuple[dict, ...], t: str, parent_row_id: str | None) -> dict | None:
    """Half-open [start_iso, end_iso) lookup, parent-linked (§4.0: an AD row
    is valid only under its MD row; linkage by parent row id, never by
    timestamp overlap alone). ISO-8601 UTC strings compare lexicographically."""
    for r in rows:
        if r["parent_row_id"] != parent_row_id:
            continue
        if r["start_iso"] <= t < r["end_iso"]:
            return r
    return None


def period_lord_relation(lord: str, event_class: str, chart: dict, *,
                         rule_version: str = RULE_VERSION, level: str | None = None,
                         affected_person: str | None = None) -> dict:
    """P1 prerequisite (2): the natal bhāva relationship of the period lord
    to the event class, with provenance and operator role per the §2.2
    relation-kind table.

    Returns {relation, licence, detail} with licence ∈ {scored, testimony,
    none}. H unknown ⇒ licence none with relation unknown (honest, not false).

    `rule_version` selects the H table AND the relation-kind table read (FB-44; the default is the 1.0.0
    behaviour, byte-for-byte). From the ruling's version on, ND-P2-20261005 rule 4 adds one kind: a class
    kāraka running as the MD or AD ANCHOR lord is `karakatva`, licence scored (a ruled extension). `level`
    is the record's anchor level when the caller has one: the rule reaches MD and AD only, so a PD anchor
    gets no kārakatva (it stays whatever the cited kinds make it — and a PD record is testimony by its own
    ruling either way). Checked AFTER the two cited scored kinds (a kāraka that also occupies or owns H is
    reported by its cited relation) and BEFORE the testimony-only dispositorship kind.
    """
    houses = signature_houses(event_class, chart, rule_version)
    if houses is None:
        return {"relation": "unknown", "licence": "none",
                "detail": "H unknown for this class — admission unqualified, "
                          "never licensed (§2.2 truth table)"}
    natal = chart["natal"]

    # occupancy of a signature house — [D] scored.
    if lord in natal and sign_of(natal[lord]) in houses:
        return {"relation": "occupancy", "licence": "scored",
                "detail": f"{lord} occupies {sign_of(natal[lord])} ∈ H"}

    # ownership of a signature house — [D] scored. Nodes own nothing (N-14).
    if lord not in NODES and any(SIGN_LORDS[s] == lord for s in houses):
        return {"relation": "ownership", "licence": "scored",
                "detail": f"{lord} owns a signature house of {sorted(houses)}"}

    # kārakatva (ND-P2-20261005 rule 4): a class kāraka as the MD/AD anchor lord — ruled, scored.
    kind = next((k for k in _registry.p1_relation_kinds(rule_version)
                 if k["relation"] == _registry.KARAKATVA_RELATION), None)
    # unknown-input behaviour PRESERVED: a lord whose natal position is unreadable is not licensed here — it
    # falls through to the lookup below, which raises for the caller to store an explicit `unknown`
    if (kind is not None and lord in natal and (level is None or level in kind["levels"])
            and lord in _registry.karakatva_karakas(event_class, rule_version, affected_person)):
        return {"relation": kind["relation"], "licence": kind["operator_role"],
                "provenance": kind["provenance"], "ruling_ref": kind["ruling_ref"],
                "detail": f"{lord} is a kāraka of {event_class} running as the "
                          f"{'/'.join(kind['levels']).upper()} anchor lord ({kind['ruling_ref']} rule 4)"}

    # dispositorship: the lord's dispositor (its natal sign's lord) relates to
    # the class. Node case: testimony-only per D-PADMIT. Non-node case: no
    # clause found in Phaladīpikā XX.34–38 (PG249:C1/PG250:C1) — testimony
    # pending a native ruling (spec C5 relation-kind table,
    # P1_RELATION_KINDS). Testimony annotates and never licences.
    disp = SIGN_LORDS[sign_of(natal[lord])]
    disp_house = None
    if disp in natal and sign_of(natal[disp]) in houses:
        disp_house = house_of(natal[disp], Frame("lagna"), chart)
        rec = RelationshipRecord(
            chart_id=chart.get("chart_id", DASHA_READ_CONTRACT["chart_id"]),
            generation=chart.get("generation", "5.0"),
            event_class=event_class, affected_person="native",
            frame="lagna", agent=disp, relation="occupancy",
            object_id=f"obj:sign:{sign_of(natal[disp])}",
            object_kind="sign_span", object_role="signature_house",
            contact_id=None, path_id="P1", rule_version=RULE_VERSION,
            prerequisites=[], provenance="verse_cited",
            operator_role="scored")
        rel_ref = (f"dispositorship → {disp}/{disp_house}th "
                   f"(record {rec.record_id})")
    elif disp not in NODES and any(SIGN_LORDS[s] == disp for s in houses):
        rel_ref = f"dispositorship → {disp} owns a signature house"
    else:
        rel_ref = None
    if rel_ref is not None:
        if lord in NODES:
            caveat = ("node-dispositor chain is testimony-only per D-PADMIT "
                      "and cannot licence")
        else:
            caveat = ("non-node dispositorship: no clause found in PG249:C1/"
                      "PG250:C1 (śl. 34–39) — testimony pending a native "
                      "ruling (P1_RELATION_KINDS)")
        return {"relation": "dispositorship", "licence": "testimony",
                "detail": f"{rel_ref}; {caveat}"}

    return {"relation": "none", "licence": "none",
            "detail": f"no natal relationship of {lord} to {event_class}"}


def permission(chart: dict, t: str, event_class: str) -> dict:
    """§4.1 schema: permission(chart_id, t, event_class). Computed per
    instant; levels never collapsed into one boolean."""
    md = _row_at(MD_ROWS, t, None)
    ad = _row_at(AD_ROWS, t, md["row_id"]) if md else None
    pd = _row_at(PD_ROWS, t, ad["row_id"]) if ad else None

    period_context = {"system": DASHA_READ_CONTRACT["system_id"],
                      "build_id": DASHA_READ_CONTRACT["build_id"]}
    licences = []
    for level, row in (("md", md), ("ad", ad), ("pd", pd)):
        if row is None:
            period_context[level] = {"lord": None, "row_id": None,
                                     "licence": "none", "relation": "none"}
            continue
        rel = period_lord_relation(row["lord"], event_class, chart)
        period_context[level] = {"lord": row["lord"], "row_id": row["row_id"],
                                 "licence": rel["licence"],
                                 "relation": rel["relation"],
                                 "detail": rel["detail"]}
        licences.append(rel["licence"])

    # Composition: class licence = union over levels — licensed iff some
    # level's licence = scored; testimony annotates and never licenses (§0).
    class_licence = ("scored" if "scored" in licences
                     else "testimony" if "testimony" in licences else "none")
    admitted_paths = ["P1"] if class_licence == "scored" else []
    return {
        "admitted_paths": admitted_paths,
        "period_context": {**period_context, "applicability": applicability(chart)},
        "class_licence": class_licence,
    }


def applicability(chart: dict) -> dict:
    """Aṣṭottarī applicability (§4.1, D-RQ7): absent on this chart — BOTH
    failed conditions named (O-PP-3): Rāhu 8th from lagna lord Mars; day
    birth in Śukla pakṣa (the Kṛṣṇa reading fails; pakṣa wording OCR-degraded,
    recorded per CORPUS_READS §6 / S-06)."""
    natal = chart["natal"]
    lagna_lord = SIGN_LORDS[sign_of(chart["lagna_deg"])]
    ll_frame = Frame("graha", lagna_lord)
    rahu_house = house_of(natal["Rahu"], ll_frame, chart)

    failed = []
    if rahu_house not in (1, 4, 5, 7, 9):  # kendra/trikoṇa from lagna lord
        failed.append(f"rahu_{rahu_house}th_from_lagna_lord_{lagna_lord.lower()}"
                      "_not_kendra_trikona")
    if chart.get("day_birth") and chart.get("paksha") == "Shukla":
        failed.append("day_birth_shukla_paksha_fails_krishna_reading")
    if failed:
        return {"system": "ashtottari", "state": "absent",
                "failed_conditions": failed}
    return {"system": "ashtottari", "state": "applicable",
            "failed_conditions": []}
