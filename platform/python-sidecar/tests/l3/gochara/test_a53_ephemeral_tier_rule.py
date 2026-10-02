"""A5.3 — AM-4 as a RULE of the enumerator (steward M20261002T000907-c058 (a)).

The Moon is an EPHEMERAL tier: a build stores no Moon-agent contact or record (the database refuses a
Moon record under an `event_class` partition). So no Moon-agent TRANSIT edge may ever enter the stored
enumeration — hence never the inventory, the coverage's searched set, or the record phase. The rule is
asserted exhaustively over every scored class x every implemented path, not per row.
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import inventory as inv
from services.gochara_rules.registry import CLASS_BY_NAME

from .test_a53_inventory import CHART, DASHA, H0, H1, P5_EXCL, SEALED

CLASSES = sorted(c for c in CLASS_BY_NAME if c != "birth_anchor")
PATHS = ("P1", "P2", "P3", "P4", "P5")


@pytest.mark.parametrize("path", PATHS)
def test_no_moon_agent_transit_edge_is_ever_in_the_stored_enumeration(path):
    for cls in CLASSES:
        edges = ev.enumerate_edges(cls, path, CHART)
        assert not [e for e in edges if e.transit and e.agent in ev.EPHEMERAL_TIER_AGENTS], (cls, path)


def test_the_rule_is_the_enumerators_and_the_excluded_edges_are_counted_and_named():
    excluded = ev.ephemeral_tier_edges("marriage", "P3", CHART)
    assert excluded and all(e.transit and e.agent == "moon" for e in excluded)
    stored = ev.enumerate_edges("marriage", "P3", CHART)
    # the two partition the unfiltered enumeration exactly
    assert len(stored) + len(excluded) == len(ev._enumerate_all("marriage", "P3", CHART, None))


def test_natal_moon_facts_are_unaffected_by_the_rule():
    """Only TRANSIT edges are ephemeral; a natal fact about the Moon is a stored L1 fact."""
    natal_all = [e for e in ev._enumerate_all("marriage", "P3", CHART, None) if not e.transit]
    natal_stored = [e for e in ev.enumerate_edges("marriage", "P3", CHART) if not e.transit]
    assert natal_stored == natal_all


@pytest.mark.parametrize("cls", ["marriage", "bereavement", "career_entry", "illness_acute"])
def test_no_obligation_in_the_inventory_names_the_moon_as_an_agent(cls):
    cap = inv.SearchCapability(position_probe=True, arc_index=True)
    plan = inv.plan_class_inventory(
        event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=SEALED, capability=cap,
        path_exclusions={"P5": P5_EXCL}, dasha_rows=DASHA)
    assert plan.obligations
    assert not [o for o in plan.obligations if o.agent == "moon"]


def test_a_p1_period_whose_lord_is_the_moon_is_never_searched_complete():
    """P1's role-token obligations resolve to the period lord at each instant; a MOON period
    resolves to an agent the stored build never searches — missing_inputs, named."""
    moon_md = inv.DashaRow("00000000-0000-0000-0000-000000000099", 1, "moon", H0, H1)
    cap = inv.SearchCapability(position_probe=True, arc_index=True)
    plan = inv.plan_class_inventory(
        event_class="marriage", chart=CHART, horizon=(H0, H1), sealed_paths=[("P1", "1.0.0")],
        capability=cap, path_exclusions={}, dasha_rows=[moon_md])
    md = [iv for iv in plan.intervals if iv.detail and iv.detail.get("resolved_agent") == "moon"]
    assert md and all(iv.state == "missing_inputs" for iv in md)
    assert all(iv.detail.get("tier") == "moon_on_demand (AM-4)" for iv in md)
