import pytest
from ..staleness import compute_downstream_ids

# Linear chain: ga_positions -> bo_laksana -> bo_bimba -> ph_result
REGISTRY = [
    {'asset_id': 'ga_positions', 'depends_on': []},
    {'asset_id': 'bo_laksana',   'depends_on': ['ga_positions']},
    {'asset_id': 'bo_bimba',     'depends_on': ['bo_laksana']},
    {'asset_id': 'ph_result',    'depends_on': ['bo_bimba']},
]

def test_compute_downstream_root():
    """Root asset: all others are downstream."""
    result = compute_downstream_ids('ga_positions', REGISTRY)
    assert result == {'bo_laksana', 'bo_bimba', 'ph_result'}

def test_compute_downstream_mid_chain():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert result == {'bo_bimba', 'ph_result'}

def test_compute_downstream_leaf():
    """Leaf asset: no downstream."""
    result = compute_downstream_ids('ph_result', REGISTRY)
    assert result == set()

def test_compute_downstream_does_not_include_self():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert 'bo_laksana' not in result

def test_compute_downstream_diamond():
    """Diamond dep: A -> B, A -> C, B -> D, C -> D. Downstream of A = {B, C, D}."""
    diamond = [
        {'asset_id': 'A', 'depends_on': []},
        {'asset_id': 'B', 'depends_on': ['A']},
        {'asset_id': 'C', 'depends_on': ['A']},
        {'asset_id': 'D', 'depends_on': ['B', 'C']},
    ]
    result = compute_downstream_ids('A', diamond)
    assert result == {'B', 'C', 'D'}
    # D must not appear twice (set dedup)
    assert len(result) == 3

def test_compute_downstream_isolated():
    """Asset with no dependents returns empty set."""
    result = compute_downstream_ids('ga_positions', [
        {'asset_id': 'ga_positions', 'depends_on': []},
    ])
    assert result == set()
