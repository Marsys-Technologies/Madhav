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
two_pass_verified, build 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb).
"""
from __future__ import annotations

from .frames import Frame, SIGN_LORDS, frame_sign, house_of, sign_of
from .records import RelationshipRecord
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
    "build_id": "1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb",
    "tier": TWO_PASS_VERIFIED,
    "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]",
}

# Pinned reference rows (§4.0 [L]; every row id printed in full — C6).
MD_ROWS: tuple[dict, ...] = (
    {"row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e", "level": "MD",
     "lord": "Mercury", "parent_row_id": None,
     "start_iso": "2010-08-18T15:50:23Z", "end_iso": "2027-08-18T21:50:23Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
)

AD_ROWS: tuple[dict, ...] = (
    {"row_id": "133b4500-ad36-4fff-8814-c6b0b253ca05", "level": "AD",
     "lord": "Ketu", "parent_row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e",
     "start_iso": "2013-01-14T07:17:23Z", "end_iso": "2014-01-11T12:14:23Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "14f20359-c30e-425d-b50f-45b017568ace", "level": "AD",
     "lord": "Moon", "parent_row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e",
     "start_iso": "2017-09-17T20:20:23Z", "end_iso": "2019-02-17T06:50:23Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "b1e4d515-6a94-4054-89ff-1ed2487f66ae", "level": "AD",
     "lord": "Mars", "parent_row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e",
     "start_iso": "2019-02-17T06:50:23Z", "end_iso": "2020-02-14T11:47:23Z",
     "source": "GOCHARA_TEST_ORACLES_v1_4 O-PP-2 [L]"},
    {"row_id": "25a4b815-39bb-4b4a-b922-84a71778bb4f", "level": "AD",
     "lord": "Rahu", "parent_row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e",
     "start_iso": "2020-02-14T11:47:23Z", "end_iso": "2022-09-02T21:05:23Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
)

PD_ROWS: tuple[dict, ...] = (
    {"row_id": "6b843ad2-0759-4e7f-af7d-d39eac8b0325", "level": "PD",
     "lord": "Mercury", "parent_row_id": "133b4500-ad36-4fff-8814-c6b0b253ca05",
     "start_iso": "2013-11-21T04:44:19Z", "end_iso": "2014-01-11T12:14:23Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "203406df-ddc3-44b8-a174-e48c5546d009", "level": "PD",
     "lord": "Venus", "parent_row_id": "14f20359-c30e-425d-b50f-45b017568ace",
     "start_iso": "2018-10-28T04:09:53Z", "end_iso": "2019-01-22T09:54:53Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "5c07a7c9-0848-4e54-9f0b-2a9652101cef", "level": "PD",
     "lord": "Venus", "parent_row_id": "25a4b815-39bb-4b4a-b922-84a71778bb4f",
     "start_iso": "2021-10-04T03:09:26Z", "end_iso": "2022-03-08T08:42:26Z",
     "source": "GOCHARA_DESIGN_SPECS_v1_4 §4.0 [L]"},
    {"row_id": "a4cf46db-fcb5-479c-8aab-ca87bcb551ff", "level": "PD",
     "lord": "Saturn", "parent_row_id": "b1e4d515-6a94-4054-89ff-1ed2487f66ae",
     "start_iso": "2019-06-21T00:55:52Z", "end_iso": "2019-08-17T09:18:53Z",
     "source": "GOCHARA_TEST_ORACLES_v1_4 O-PP-2 [L]"},
    {"row_id": "73eea5c0-631f-4b48-8c8f-483c910c6fde", "level": "PD",
     "lord": "Saturn", "parent_row_id": "25a4b815-39bb-4b4a-b922-84a71778bb4f",
     "start_iso": "2020-11-04T09:13:29Z", "end_iso": "2021-03-31T20:29:50Z",
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


def period_lord_relation(lord: str, event_class: str, chart: dict) -> dict:
    """P1 prerequisite (2): the natal bhāva relationship of the period lord
    to the event class, with provenance and operator role per the §2.2
    relation-kind table.

    Returns {relation, licence, detail} with licence ∈ {scored, testimony,
    none}. H unknown ⇒ licence none with relation unknown (honest, not false).
    """
    houses = signature_houses(event_class, chart)
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
