"""
tests/l2/test_bo_cgm_paths_narr_golden.py -- Narr golden-value test for bo_cgm_paths

Track I item TI-L2-11 (Track A A.L2 brief ``bo_cgm_paths_ELEVATION_BRIEF_v1_0.md`` FD-2,
cross-asset fix CF-14): ``bodha_cgm_paths.path_label_human`` is narration. It is the
sentence a reader sees for a dispositor chain, and ``is_final_dispositor`` is the
structured fact next to it. A passing build says nothing about whether the two agree
(CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on the pure function ``_build_dispositor_chains`` (no database):

  * the label names exactly the nodes of ``node_chain``, in order, joined by the hop
    separator, so the number of arrows equals ``path_length`` (= ``len(node_chain) - 1``)
    and ``len(edge_chain)``;
  * ``"final dispositor"`` appears in the label if and only if ``is_final_dispositor``
    is True (a looped or unfinished chain must never be narrated as final);
  * a zero-hop self-ruling graha is narrated as such;
  * where a node has several dispositor edges, the label follows the strongest edge
    (the edge actually taken), not an alternative;
  * the label uses ``node_label_human`` and falls back to ``node_subject``.

What this does NOT do: it does not declare ``path_label_human`` under
``evidence.prose_fields`` in ``asset_declarations.json`` (that is the other half of
TI-L2-11; the declarations file is held while PR #2984 changes it), and it changes
no writer, no stored value and no registry row.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cgm_paths import _build_dispositor_chains

FINAL_SUFFIX = "(final dispositor)"
SELF_RULING_LABEL = "(self-ruling / final dispositor)"


def _node(node_id: str, subject: str, sign: str, label: str | None = None) -> dict:
    return {
        "node_id": node_id,
        "node_subject": subject,
        "node_label_human": label,
        "position_in_chart_jsonb": {"sign": sign},
    }


def _edge(edge_id: str, src: str, dst: str, strength: float | None = 1.0) -> dict:
    return {
        "edge_id": edge_id,
        "from_node_id": src,
        "to_node_id": dst,
        "edge_type": "dispositor",
        "relationship_basis": "dispositor",
        "computed_strength": strength,
    }


def _run(nodes: list[dict], edges: list[dict]) -> dict[str, dict]:
    by_from: dict[str, list[dict]] = {}
    for e in edges:
        by_from.setdefault(e["from_node_id"], []).append(e)
    node_by_id = {n["node_id"]: n for n in nodes}
    chains = _build_dispositor_chains(nodes, by_from, node_by_id)
    return {c["from_node_id"]: c for c in chains}


def _assert_label_matches_structure(chain: dict, node_label: dict[str, str]) -> None:
    """The invariant every chain must satisfy, whatever the graph."""
    label = chain["label"]
    # "final dispositor" is narrated iff the structured flag says so.
    assert ("final dispositor" in label) == chain["is_final_dispositor"], label
    if len(chain["node_chain"]) == 1:
        # zero-hop: only the self-ruling form exists
        assert chain["is_final_dispositor"] is True
        assert chain["edge_chain"] == []
        assert label == f"{node_label[chain['node_chain'][0]]} {SELF_RULING_LABEL}"
        return
    body = label[: -len(" " + FINAL_SUFFIX)] if chain["is_final_dispositor"] else label
    assert body.split(" → ") == [node_label[n] for n in chain["node_chain"]], label
    assert body.count(" → ") == len(chain["node_chain"]) - 1 == len(chain["edge_chain"])
    if chain["is_final_dispositor"]:
        assert label.endswith(" " + FINAL_SUFFIX), label
    else:
        assert FINAL_SUFFIX not in label, label


# -- golden values -----------------------------------------------------------

def test_two_hop_chain_to_a_self_ruling_node_is_narrated_final() -> None:
    # Moon in Taurus -> Venus; Venus in Gemini -> Mercury; Mercury in Gemini rules it.
    nodes = [
        _node("n-moon", "moon", "taurus", "Moon"),
        _node("n-venus", "venus", "gemini", "Venus"),
        _node("n-merc", "mercury", "gemini", "Mercury"),
    ]
    edges = [_edge("e1", "n-moon", "n-venus"), _edge("e2", "n-venus", "n-merc")]
    chains = _run(nodes, edges)

    moon = chains["n-moon"]
    assert moon["node_chain"] == ["n-moon", "n-venus", "n-merc"]
    assert moon["edge_chain"] == ["e1", "e2"]
    assert moon["is_final_dispositor"] is True
    assert moon["label"] == "Moon → Venus → Mercury (final dispositor)"

    venus = chains["n-venus"]
    assert venus["label"] == "Venus → Mercury (final dispositor)"
    # Mercury is self-ruling: a zero-hop chain, narrated as such.
    assert chains["n-merc"]["label"] == "Mercury (self-ruling / final dispositor)"
    assert chains["n-merc"]["node_chain"] == ["n-merc"]


def test_sun_in_capricorn_to_saturn_in_aquarius_is_final() -> None:
    nodes = [
        _node("n-sun", "sun", "capricorn", "Sun"),
        _node("n-sat", "saturn", "aquarius", "Saturn"),
    ]
    chains = _run(nodes, [_edge("e1", "n-sun", "n-sat")])
    assert chains["n-sun"]["label"] == "Sun → Saturn (final dispositor)"
    assert chains["n-sun"]["is_final_dispositor"] is True


def test_looped_chain_is_never_narrated_final() -> None:
    # Jupiter in Cancer -> Moon; Moon in Sagittarius -> Jupiter (a mutual loop; neither
    # sits in a sign it rules).
    nodes = [
        _node("n-jup", "jupiter", "cancer", "Jupiter"),
        _node("n-moon", "moon", "sagittarius", "Moon"),
    ]
    edges = [_edge("e1", "n-jup", "n-moon"), _edge("e2", "n-moon", "n-jup")]
    chains = _run(nodes, edges)
    assert chains["n-jup"]["label"] == "Jupiter → Moon"
    assert chains["n-moon"]["label"] == "Moon → Jupiter"
    for chain in chains.values():
        assert chain["is_final_dispositor"] is False
        assert "final dispositor" not in chain["label"]
        # the closing hop back to the start is not narrated
        assert len(chain["node_chain"]) == 2


def test_unfinished_chain_is_not_narrated_final() -> None:
    # Mars in Capricorn -> Saturn, but Saturn's own dispositor edge is absent and Saturn
    # sits in Gemini (not a sign it rules): the chain stops, with no final claim.
    nodes = [
        _node("n-mars", "mars", "capricorn", "Mars"),
        _node("n-sat", "saturn", "gemini", "Saturn"),
    ]
    chains = _run(nodes, [_edge("e1", "n-mars", "n-sat")])
    assert chains["n-mars"]["label"] == "Mars → Saturn"
    assert chains["n-mars"]["is_final_dispositor"] is False
    assert "n-sat" not in chains  # Saturn has no hop and is not self-ruling: no chain


def test_label_follows_the_strongest_dispositor_edge() -> None:
    nodes = [
        _node("n-mars", "mars", "taurus", "Mars"),
        _node("n-ven", "venus", "taurus", "Venus"),  # Venus rules Taurus: final
        _node("n-sat", "saturn", "gemini", "Saturn"),
    ]
    edges = [
        _edge("weak", "n-mars", "n-sat", 0.2),
        _edge("strong", "n-mars", "n-ven", 0.9),
    ]
    mars = _run(nodes, edges)["n-mars"]
    assert mars["edge_chain"] == ["strong"]
    assert mars["label"] == "Mars → Venus (final dispositor)"
    assert "Saturn" not in mars["label"]


def test_label_falls_back_to_node_subject_when_no_human_label() -> None:
    nodes = [_node("n-sun", "sun", "capricorn", None), _node("n-sat", "saturn", "aquarius", None)]
    chain = _run(nodes, [_edge("e1", "n-sun", "n-sat")])["n-sun"]
    assert chain["label"] == "sun → saturn (final dispositor)"


def test_edge_to_a_node_missing_from_the_graph_is_not_narrated() -> None:
    nodes = [_node("n-moon", "moon", "taurus", "Moon")]
    chains = _run(nodes, [_edge("e1", "n-moon", "n-ghost")])
    assert chains == {}  # no hop was taken, no chain, no phantom node in any label


# -- the invariant over a mixed graph ---------------------------------------

def test_label_agrees_with_structure_on_every_chain_of_a_mixed_graph() -> None:
    nodes = [
        _node("n-sun", "sun", "capricorn", "Sun"),
        _node("n-moon", "moon", "taurus", "Moon"),
        _node("n-mars", "mars", "cancer", "Mars"),
        _node("n-merc", "mercury", "gemini", "Mercury"),
        _node("n-jup", "jupiter", "cancer", "Jupiter"),
        _node("n-ven", "venus", "gemini", "Venus"),
        _node("n-sat", "saturn", "aquarius", "Saturn"),
    ]
    edges = [
        _edge("e-sun", "n-sun", "n-sat"),
        _edge("e-moon", "n-moon", "n-ven"),
        _edge("e-ven", "n-ven", "n-merc"),
        _edge("e-mars", "n-mars", "n-moon"),      # Mars in Cancer -> Moon -> Venus -> Mercury
        _edge("e-jup", "n-jup", "n-mars"),
        _edge("e-merc", "n-merc", "n-ven"),       # Mercury is self-ruling: stops before this
    ]
    chains = _run(nodes, edges)
    node_label = {n["node_id"]: n["node_label_human"] for n in nodes}
    assert chains, "the mixed graph must produce chains"
    for chain in chains.values():
        _assert_label_matches_structure(chain, node_label)
    # the longest chain narrates all five nodes
    assert chains["n-jup"]["label"] == (
        "Jupiter → Mars → Moon → Venus → Mercury (final dispositor)"
    )
