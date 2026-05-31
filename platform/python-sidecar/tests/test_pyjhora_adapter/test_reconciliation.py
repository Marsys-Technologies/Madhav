"""Internal-consistency tests for the reconciliation checks."""
from __future__ import annotations

from pyjhora_adapter import houses, positions
from pyjhora_adapter.reconciliation import reconcile


def _build(native_jd):
    grahas = positions.compute_positions(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    asc = houses.compute_ascendant(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    house_list = houses.compute_houses(asc)
    return asc, house_list, grahas


def test_house1_sign_matches_lagna(native_jd):
    asc, house_list, grahas = _build(native_jd)
    recon = reconcile(asc, house_list, grahas)
    assert recon["house1_lagna_consistent"] is True
    assert house_list[0]["sign_id"] == asc["sign_id"]


def test_nodes_opposed(native_jd):
    asc, house_list, grahas = _build(native_jd)
    recon = reconcile(asc, house_list, grahas)
    assert recon["nodes_opposed"] is True


def test_overall_consistent_no_issues(native_jd):
    asc, house_list, grahas = _build(native_jd)
    recon = reconcile(asc, house_list, grahas)
    assert recon["consistent"] is True
    assert recon["issues"] == []
