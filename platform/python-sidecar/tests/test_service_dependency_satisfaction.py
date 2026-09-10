"""D-VR-DATA-CORRECTNESS §3.5 service-dependency exception.

A data asset depending on a service asset (e.g. bg_cohort -> bg_ephemeris_engine)
must be buildable: a service has no data table and thus no data-freshness receipt,
so its readiness is state='service_ok' (a current GREEN probe), never a 'fresh'
data receipt. deps_unsatisfied must treat a service dep as satisfied on
'service_ok'/'lit' without demanding data freshness, while still enforcing full
data-freshness for data deps.
"""
from pipeline.orchestrator.asset_runner import deps_unsatisfied


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return self._rows


def test_service_dep_satisfied_by_service_ok_without_fresh_receipt():
    cur = _Cur([
        {"asset_id": "bg_ephemeris_engine", "asset_kind": "service",
         "state": "service_ok", "freshness_state": "unknown"},
    ])
    assert deps_unsatisfied(cur, None, "bg_cohort", ["bg_ephemeris_engine"]) == []


def test_data_dep_still_requires_fresh_receipt():
    cur = _Cur([
        {"asset_id": "bg_ontology", "asset_kind": "data",
         "state": "lit", "freshness_state": "unknown"},
    ])
    assert deps_unsatisfied(cur, None, "bg_dasha_systems", ["bg_ontology"]) == [
        "bg_ontology(receipt:unknown)"
    ]


def test_service_dep_still_blocked_when_not_ok():
    cur = _Cur([
        {"asset_id": "bg_ephemeris_engine", "asset_kind": "service",
         "state": "error", "freshness_state": None},
    ])
    assert deps_unsatisfied(cur, None, "bg_cohort", ["bg_ephemeris_engine"]) == [
        "bg_ephemeris_engine(error)"
    ]


def test_data_dep_fresh_and_lit_is_satisfied():
    cur = _Cur([
        {"asset_id": "bg_ontology", "asset_kind": "data",
         "state": "lit", "freshness_state": "fresh"},
    ])
    assert deps_unsatisfied(cur, None, "bg_dasha_systems", ["bg_ontology"]) == []
