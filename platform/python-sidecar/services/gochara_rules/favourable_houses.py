"""P2 per-planet FAVOURABLE house sets counted from janma-rāśi (the natal
Moon sign) — cited registry content for the P2 rule path
(GOCHARA_DESIGN_SPECS_v1_4 §2; registry row "P2", frame="moon").

Source: Phaladīpikā Adh. XXVI śl.1–8 as served in the campaign corpus
(`classical_text_chunks`, text_id='phaladeepika'), read verbatim 2026-10-01:

  PG321:C1 (śl.1–2) — śl.1: Moon-lagna primacy for gochara-phala; śl.2, the
      per-planet favourable table: "the Sun gives good results when he is in
      the 6th, 3rd and 10th houses (counted from the Moon), the Moon in the
      3rd, 10th, 6th, 7th and 1st; Jupiter in the 7th, 9th, 2nd and 5th;
      Mars and Saturn in the 6th and 3rd; Mercury in the 6th, 2nd, 4th, 10th
      and 8th; all planets in the 11th; Venus in all places other than the
      10th, 7th and 6th. Rāhu and Ketu are similar to the Sun."
  PG322:C1 (śl.3–5) and PG323:C1 (śl.6–8) — the same sets restated with
      their vedha correspondences; every set in this module is corroborated
      verbatim by its vedha śloka.

Every entry is legible and explicit in the served text, so every entry is
'cited'; none is 'unresolved' (B.10 — nothing filled from memory). Venus is
the text's own complement: "all places other than the 10th, 7th and 6th"
with "all planets in the 11th" ⇒ {1,2,3,4,5,8,9,11,12}. Rāhu and Ketu take
the Sun's set by the śl.2 equivalence clause — including the 10th, which the
legacy `brahmagyan/l0_transit.py` rows omit for the nodes (recorded
deviation; that table is Stream A's lane to reconcile).

Vedha is NOT duplicated here: the house-pair correspondences already live in
`bg_transit_rules` (seeded by `brahmagyan/l0_transit.py`, verified against
śl.3–8 on 2026-10-01 — all seven planets' pairs match the served text
verbatim), and the O-VI-3 exception pairs (Sun↔Saturn, Moon↔Mercury) plus
vipareeta carve-out live in `vedha.py`. This module references both.
"""
from __future__ import annotations

FRAME = "moon"  # janma-rāśi — Phaladīpikā XXVI.1 (PG321:C1)
PROVENANCE = "verse_cited"

_CITE_2 = "Phaladīpikā XXVI.2 (PG321:C1)"
_CITE_SUN = (_CITE_2, "Phaladīpikā XXVI.3 (PG322:C1)")
_CITE_MOON = (_CITE_2, "Phaladīpikā XXVI.4 (PG322:C1)")
_CITE_MARS_SATURN = (_CITE_2, "Phaladīpikā XXVI.5 (PG322:C1)")
_CITE_MERCURY = (_CITE_2, "Phaladīpikā XXVI.6 (PG323:C1)")
_CITE_JUPITER = (_CITE_2, "Phaladīpikā XXVI.7 (PG323:C1)")
_CITE_VENUS = (_CITE_2, "Phaladīpikā XXVI.8 (PG323:C1)")
_NODE_EQUIVALENCE = "Rāhu and Ketu are similar to the Sun (XXVI.2, PG321:C1)"

FAVOURABLE_HOUSES_FROM_MOON: dict[str, dict] = {
    "Sun": {"houses": frozenset({3, 6, 10, 11}), "state": "cited",
            "citations": _CITE_SUN},
    "Moon": {"houses": frozenset({1, 3, 6, 7, 10, 11}), "state": "cited",
             "citations": _CITE_MOON},
    "Mars": {"houses": frozenset({3, 6, 11}), "state": "cited",
             "citations": _CITE_MARS_SATURN},
    "Mercury": {"houses": frozenset({2, 4, 6, 8, 10, 11}), "state": "cited",
                "citations": _CITE_MERCURY},
    "Jupiter": {"houses": frozenset({2, 5, 7, 9, 11}), "state": "cited",
                "citations": _CITE_JUPITER},
    "Venus": {"houses": frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
              "state": "cited", "citations": _CITE_VENUS,
              "note": "the text's complement: all places other than the "
                      "10th, 7th and 6th; the 11th is already inside it"},
    "Saturn": {"houses": frozenset({3, 6, 11}), "state": "cited",
               "citations": _CITE_MARS_SATURN},
    "Rahu": {"houses": frozenset({3, 6, 10, 11}), "state": "cited",
             "citations": _CITE_SUN, "note": _NODE_EQUIVALENCE},
    "Ketu": {"houses": frozenset({3, 6, 10, 11}), "state": "cited",
             "citations": _CITE_SUN, "note": _NODE_EQUIVALENCE},
}

# Reference only — never a copy. Pairs: bg_transit_rules (brahmagyan/
# l0_transit.py); exceptions + vipareeta: vedha.py.
VEDHA_PAIRS_REF = ("bg_transit_rules", "brahmagyan/l0_transit.py")
VEDHA_EXCEPTIONS_REF = "gochara_rules.vedha.EXCEPTION_PAIRS"


def favourable_houses(graha: str) -> frozenset[int]:
    """The cited favourable house set (from janma-rāśi) for a graha.
    An 'unresolved' entry would raise rather than return a guess (B.10);
    at present every graha is 'cited'."""
    row = FAVOURABLE_HOUSES_FROM_MOON[graha]
    if row["state"] != "cited":
        raise ValueError(f"{graha}: favourable set {row['state']}, not usable")
    return row["houses"]


def is_favourable(graha: str, house_from_moon: int) -> bool:
    return house_from_moon in favourable_houses(graha)
