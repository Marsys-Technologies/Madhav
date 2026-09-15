"""DP-SD-019: Yojaka must preserve L2's signed multi-domain structure.

These fixtures exercise the writer boundary rather than merely checking for new
JSON keys.  The receiving-consumer assertion uses ph_nimitta's real posterior
kernel, which already consumes Yojaka's scalar multi-system confirmation count.
"""

from __future__ import annotations

import json

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter
from services.ph_nimitta.engine import compute_posterior


class _Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.pending = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.pending = []
        if "FROM bodha_msr_signals" in sql:
            self.pending = self.conn.signals
        elif "COUNT(DISTINCT bp.ayanamsha_id)" in sql:
            self.pending = self.conn.confirmations
        elif "FROM bodha_pratijna" in sql:
            self.pending = self.conn.promises
        elif "FROM bodha_cdlm_cells" in sql:
            self.pending = self.conn.cdlm

    def executemany(self, _sql, batch):
        self.conn.inserted.extend(batch)

    def fetchall(self):
        return self.pending


class _Connection:
    def __init__(self, *, signals, promises, confirmations, cdlm):
        self.signals = signals
        self.promises = promises
        self.confirmations = confirmations
        self.cdlm = cdlm
        self.inserted = []

    def cursor(self, *_args, **_kwargs):
        return _Cursor(self)


def _signal(*, domains=None, valence="mixed", contrary=None):
    row = {
        "signal_id": "signal-multidomain",
        "chart_id": "chart-1",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "signal_type_class": "composite_state",
        "signal_type_id": "raja_yoga_kalatra_seventh",
        "configuration_jsonb": {"planet": "Venus"},
        "constituent_facts_array": ["fact-2", "fact-1"],
        "valence": valence,
        "dignity_score": 0.8,
        "shadbala_norm": 1.0,
        "domain_salience_jsonb": {"career": 0.8, "relationship": 0.9},
        "contradicts_signals_array": contrary,
    }
    if domains is not None:
        row["domains_affected_array"] = domains
    return row


def _run(signal):
    promises = [
        {"pratijna_id": f"career-{i}", "domain": "career"}
        for i in range(1, 7)
    ] + [
        {"pratijna_id": f"relationship-{i}", "domain": "relationship"}
        for i in range(1, 4)
    ] + [{"pratijna_id": "career-1", "domain": "career"}]
    conn = _Connection(
        signals=[signal],
        promises=promises,
        confirmations=[
            {"domain": "career", "aya_count": 1},
            {"domain": "relationship", "aya_count": 5},
        ],
        cdlm=[
            {"domain": "career", "avg_strength": 0.4},
            {"domain": "relationship", "avg_strength": 0.8},
        ],
    )
    ctx = ContextSpec(
        asset_id="ka_yojaka",
        build_id="build-1",
        db_conn=conn,
        config={"chart_id": "chart-1"},
    )
    result = KaYojakaWriter().run(ctx)
    assert result.rows_inserted == 1
    row = conn.inserted[0]
    return {
        "dasha": json.loads(row[4]),
        "strength": json.loads(row[6]),
        "ledger": json.loads(row[7]),
    }


def test_multidomain_signed_structure_and_all_promises_reach_output():
    output = _run(
        _signal(
            domains=["career", "relationship", "career"],
            contrary=["signal-z", "signal-a", "signal-z"],
        )
    )
    rule = output["dasha"]
    hook = output["strength"]

    assert rule["domains_affected"] == ["career", "relationship"]
    assert rule["domain_source"] == "bodha_msr_signals.domains_affected_array"
    assert rule["domain_salience_by_domain"] == {
        "career": 0.8,
        "relationship": 0.9,
    }
    assert rule["pratijna_ids_by_domain"] == {
        "career": [f"career-{i}" for i in range(1, 7)],
        "relationship": [f"relationship-{i}" for i in range(1, 4)],
    }
    assert rule["pratijna_ids"] == [
        *[f"career-{i}" for i in range(1, 7)],
        *[f"relationship-{i}" for i in range(1, 4)],
    ]
    assert len(rule["pratijna_ids"]) == 9  # no arbitrary top-five truncation
    assert rule["multi_system_confirmation_by_domain"] == {
        "career": 1,
        "relationship": 5,
    }
    assert rule["multi_system_confirmation_count"] == 5
    assert rule["cdlm_domain_strength_by_domain"] == {
        "career": 0.5,
        "relationship": 1.0,
    }
    assert rule["cdlm_domain_strength"] == 0.5  # accepted legacy inferred-domain scalar
    assert hook["signal_valence"] == "mixed"
    assert hook["contrary_signal_ids"] == ["signal-a", "signal-z"]
    assert hook["contrary_evidence_state"] == "present"


def test_existing_receiving_consumer_gets_a_real_result_distinction():
    rule = _run(_signal(domains=["career", "relationship"]))["dasha"]
    legacy_posterior, _ = compute_posterior(
        base_rate=0.2,
        pratijna_grade=2.0,
        pratijna_status="conditional",
        multi_system_confirmation_count=1,
        av_transit_potency=0.0,
    )
    complete_posterior, _ = compute_posterior(
        base_rate=0.2,
        pratijna_grade=2.0,
        pratijna_status="conditional",
        multi_system_confirmation_count=rule["multi_system_confirmation_count"],
        av_transit_potency=0.0,
    )

    assert rule["multi_system_confirmation_count"] == 5
    assert complete_posterior > legacy_posterior


def test_explicit_unknown_domains_do_not_fabricate_keyword_membership():
    output = _run(_signal(domains=["litigation"]))
    rule = output["dasha"]
    assert rule["domains_affected"] == []
    assert rule["domain_source"] == "bodha_msr_signals.domains_affected_array"
    assert rule["pratijna_ids"] == []
    assert rule["multi_system_confirmation_count"] == 0


def test_missing_legacy_domain_column_uses_documented_keyword_fallback():
    output = _run(_signal(domains=None, contrary=None))
    rule = output["dasha"]
    assert rule["domains_affected"] == ["career"]
    assert rule["domain_source"] == "signal_type_id_keyword_fallback"
    assert output["strength"]["contrary_evidence_state"] == "not_measured"
    assert output["ledger"]["source_context"] == {
        "source_table": "bodha_msr_signals",
        "chart_id": "chart-1",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "signal_id": "signal-multidomain",
        "constituent_fact_ids": ["fact-2", "fact-1"],
    }
