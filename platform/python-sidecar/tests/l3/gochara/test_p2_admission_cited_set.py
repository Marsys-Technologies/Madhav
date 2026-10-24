"""P2 `house_from_moon` — the verifier's re-derived result/admission for EVERY record the builder mints agrees with the sealed rule.

Rule (sealed, not a builder detail): `house_from_moon` holds iff the agent's house from the janma-rāśi is in its CITED set —
Phaladīpikā XXVI.2 favourable houses ∪ the D-RQ5 adverse 12/8/1 for Sun/Mars/Jupiter/Saturn (AM-11 pin (c);
`rule_registry.COMPOSITE_PREDICATES["house_from_moon"]`; `gochara_rules.admission.ADVERSE_RESIDENCE_*`). The adverse
SEARCH PLAN (`inventory_verifier._ADVERSE`) is wider — it also searches Saturn's 2nd (the Sade-Sati phase-3 TESTIMONY row,
D-PADMIT) — but a searched house is not thereby a cited one: that row's result is `false` (admission `not_admitted`), as the
builder stores it. Pre-fix the verifier re-derived the cited set from the search plan, so it derived `true`/`admitted` for
that row and `record_derivation.compare` raised "admission stored 'not_admitted', derived 'admitted'" on every adverse class.

The chart below is synthetic (the test asserts a rule, never the native's data)."""
from __future__ import annotations

import pytest

from services.gochara_kernel import evaluator, record_derivation as rd
from services.gochara_rules.favourable_houses import FAVOURABLE_HOUSES_FROM_MOON
from services.gochara_rules.registry import CLASS_UNIVERSE

VERSION = "1.3.0"
MOON = 320.0                                    # synthetic: sign index 10 (the 11th sign)
BUILDER_CHART = {"lagna_deg": 10.0, "natal": {"Moon": MOON}}
VERIFIER_CHART = {"lagna": 10.0, "natal": {"moon": MOON}}
D_RQ5_BODIES = frozenset({"saturn", "sun", "mars", "jupiter"})        # restated here, from the rule's text, not imported
D_RQ5_HOUSES = frozenset({12, 8, 1})


def cited_set(agent: str) -> frozenset[int]:
    """The sealed cited set, restated from Phaladīpikā XXVI.2 (the cited favourable registry) ∪ D-RQ5 12/8/1."""
    fav = FAVOURABLE_HOUSES_FROM_MOON[agent.title()]["houses"]
    return frozenset(fav) | (D_RQ5_HOUSES if agent in D_RQ5_BODIES else frozenset())


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Conn:
    """Answers the two sealed-registry reads `derive_path_records` makes (P2 declares ONE prerequisite: house_from_moon)."""

    def execute(self, sql, params=()):
        if "ka_gochara_rule_path_prerequisite" in sql:
            return _Cur([("house_from_moon",)])
        if "ka_gochara_rule_path" in sql:
            return _Cur([("verse_cited", None)])
        raise AssertionError(sql)


def _house(target: str) -> int:
    return (int(target.split(":")[1]) - 1 - int(MOON // 30)) % 12 + 1


def _derive(event_class: str):
    edges = evaluator.enumerate_p2_edges(event_class, BUILDER_CHART, rule_version=VERSION)
    obligations, contacts = [], []
    for i, e in enumerate(edges):
        tgt = e.obj.canonical_target
        obligations.append("|".join((event_class, "p2", VERSION, e.agent, "residence", "signature_house", tgt, "moon", "native")))
        contacts.append({"id": f"c{i}", "body": e.agent, "relation": "residence", "target": tgt, "t_in": 1, "t_out": 2})
    expected = rd.derive_path_records(_Conn(), chart_id="x", generation="g", event_class=event_class, path_id="P2",
                                      rule_version=VERSION, obligations=obligations, chart=VERIFIER_CHART, horizon_hi=3,
                                      contacts=contacts)
    return edges, expected


def test_sade_sati_phase3_testimony_row_is_not_a_cited_house():
    """CLAIM 1 — Saturn's 2nd from the Moon (the Sade-Sati phase-3 testimony row of an adverse class) is outside the cited set
    {3,6,11} ∪ {12,8,1}: result `false`, admission `not_admitted` — what the builder stores (record_store._house_from_moon)."""
    _, expected = _derive("bereavement")
    row = [r for r in expected if r["agent"] == "saturn" and r["house"] == 2]
    assert len(row) == 1 and row[0]["operator_role"] == "testimony" and row[0]["ruling"] == "D-PADMIT"
    assert row[0]["results"] == {"house_from_moon": "false"}
    assert row[0]["admission"] == "not_admitted"


@pytest.mark.parametrize("event_class", sorted(c["class"] for c in CLASS_UNIVERSE if c["class"] != "birth_anchor"))
def test_every_p2_record_the_builder_mints_derives_the_sealed_cited_set_result(event_class):
    """CLAIM 2 — for every (class, agent, house) the builder enumerates, the verifier's derived result is the sealed rule's
    (house in cited_set(agent)) and the derived admission follows it by the 1155 F5 rule."""
    edges, expected = _derive(event_class)
    assert len(expected) == len(edges)
    by = {(r["agent"], r["house"]): r for r in expected}
    for e in edges:
        h = _house(e.obj.canonical_target)
        want = "true" if h in cited_set(e.agent) else "false"
        got = by[(e.agent, h)]
        assert got["results"] == {"house_from_moon": want}, (event_class, e.agent, h)
        assert got["admission"] == ("admitted" if want == "true" else "not_admitted"), (event_class, e.agent, h)
