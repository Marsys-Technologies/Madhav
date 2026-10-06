"""Golden-value fidelity test for bo_pramana_mapa narration (notes).

synthesis_quality_scorecard.notes is json.dumps of one document: engine_version, the nine row counts
under "counts", the constituent-linkage tally under "constituent_linkage" (orphan_pct is
round(100 * orphaned / total, 2)), and under "n8_detectors" the per-term breakdown of every detector
(pass/count, terms, error), in that key order, with the default json.dumps separators. The fake
connection answers every query the writer runs with fixed numbers and records the scorecard INSERT;
the expected string is stated by hand from that template and those numbers, never read from the
builder.
"""
from __future__ import annotations

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD = "00000000-0000-4000-8000-000000000002"

EXPECTED_NOTES = (
    '{"engine_version": "bo_pramana_mapa_v1.0", '
    '"counts": {"msr": 100, "cdlm": 40, "nodes": 30, "edges": 25, "resonances": 12, '
    '"prescriptions": 9, "embeddings": 100, "convergence": 7, "contradictions": 3}, '
    '"constituent_linkage": {"total_refs": 200, "orphaned_refs": 50, "orphan_pct": 25.0, '
    '"trap1_missing_array_count": 2}, '
    '"n8_detectors": {'
    '"lel_zero_leak_pass": {"pass": true, "terms": {"lel_origin_signals": 0, '
    '"non_l1_source_provenance": 0, "lel_payload_keys_in_configuration": 0, "total_leaks": 0, '
    '"scanned_payload_keys": ["milestone_event_ids", "life_event_ids", "lel_event_ids", '
    '"event_id", "event_date", "outcome_observed"]}, "error": null}, '
    '"pillars_meet_reachability_pass": {"pass": true, "terms": {"pillars_present": '
    '{"msr_signals": true, "cdlm_cells": true, "cgm_nodes": true, "cgm_edges": true, '
    '"rm_resonances": true}, "orphan_cgm_edge_endpoints": 0, '
    '"orphan_cgm_edge_signal_refs": 0}, "error": null}, '
    '"msr_no_threshold_drop_flag": {"pass": true, "terms": {"msr_signal_count": 100, '
    '"weak_tail_salience_threshold": 0.3, "weak_tail_signal_count": 11}, "error": null}, '
    '"trap2_narration_leak_count": {"count": 0, "terms": {"markers_scanned": ["wait:", '
    '"but wait", "re-reading", "rereading", "corrected:", "correction:", "invalidated", '
    '"reconciliation:", "let me ", "i think ", "on reflection", "this requires care", '
    '"to be verified", "needs verification", "todo", "fixme", "chart\'s primary finding", '
    '"the native who", "working against the chart", "this is the chart\'s", "in my view", '
    '"arguably "], "fields_scanned": ["signal_summary_text", "signal_headline_text", '
    '"configuration_jsonb"], "detector_class": "lexical_marker_scan"}, "error": null}, '
    '"divergent_flagged_count": {"count": 3, "terms": {"tier_ranks": {"two_pass_verified": 3, '
    '"classical_match": 2, "single_pass": 2, "pass": 2, "documented_approximation": 1, '
    '"single": 1, "divergent_flagged": 0}, "explicitly_stamped_divergent": 2, '
    '"l1_verification_tier_inversion": 1}, "error": null}, '
    '"l2_contract_integrity": {'
    '"no_pre_answer": {"pass": true, "violation_count": 0, "error": null}, '
    '"ledger_independence_and_duplicate_root": {"pass": true, "violation_count": 0, "error": null}, '
    '"discovery_grounding": {"pass": true, "violation_count": 0, "error": null}, '
    '"signed_relation_and_cancellation": {"pass": true, "violation_count": 0, "error": null}'
    '}}}'
)

# (needle in the whitespace-normalised SQL, the single value the query returns); first match wins
_ANSWERS = [
    ("WITH RECURSIVE declared_upstream", (0,)),
    ("valence IS NULL", (0,)),
    ("FROM bodha_question_lenses", (0,)),
    ("shared_factor_keys_jsonb IS NULL", (0,)),
    ("FROM bodha_discoveries", (0,)),
    ("lel_origin IS TRUE", (0,)),
    ("source_l1_asset NOT LIKE", (0,)),
    ("configuration_jsonb::text ~*", (0,)),
    ("NOT EXISTS (SELECT 1 FROM bodha_cgm_nodes", (0,)),
    ("count(DISTINCT e.edge_id)", (0,)),
    ("computed_salience < %s", (11,)),
    ("LIKE ANY", (0,)),
    ("WITH rank_map", (1,)),
    ("verification_pass_status = 'divergent_flagged'", (2,)),
    ("total_refs", (200, 50)),
    ("SELECT salience_formula_version", ("salience_v2",)),
    ("SELECT linkage_formula_version", ("linkage_v1",)),
    ("SELECT resonance_score_formula_version", ("resonance_v1",)),
    ("SELECT convergence_formula_version", ("convergence_v1",)),
    ("verification_pass_status = 'two_pass_verified'", (60,)),
    ("verification_pass_status = 'documented_approximation'", (15,)),
    ("citation_ref IS NOT NULL", (80,)),
    ("constituent_facts_array IS NULL OR array_length", (2,)),
    ("SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s", (100,)),
    ("SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = %s", (40,)),
    ("SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = %s", (30,)),
    ("SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = %s", (25,)),
    ("SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = %s", (12,)),
    ("SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = %s", (9,)),
    ("SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = %s", (100,)),
    ("SELECT count(*) FROM bodha_convergence WHERE chart_id = %s", (7,)),
    ("SELECT count(*) FROM bodha_contradictions WHERE chart_id = %s", (3,)),
]


class _Result:
    def __init__(self, row=None):
        self._row = row
        self.rowcount = 0

    def fetchone(self):
        return self._row


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, _sql, _params=None):
        return None

    def fetchall(self):
        return [{"source_l1_asset": "ga_positions"}, {"source_l1_asset": "ga_strength"}]


class FakeConn:
    """Answers every query the scorecard writer runs and records the scorecard INSERT."""

    def __init__(self):
        self.inserted = []

    def cursor(self, *_a, **_k):
        return _Cursor()

    def execute(self, sql, params=None):
        text = " ".join(sql.split())
        if text.startswith(("SET LOCAL", "DELETE", "REFRESH")):
            return _Result()
        if text.startswith("INSERT INTO public.synthesis_quality_scorecard"):
            self.inserted.append(params)
            return _Result()
        for needle, answer in _ANSWERS:
            if needle in text:
                return _Result(answer)
        raise AssertionError(f"unanswered query: {text[:120]}")


def test_scorecard_notes_states_counts_linkage_and_detector_terms() -> None:
    conn = FakeConn()
    ctx = ContextSpec(
        asset_id="bo_pramana_mapa",
        build_id=BUILD,
        db_conn=conn,
        config={"chart_id": CHART},
    )
    BoPramanaMapa.run(BoPramanaMapa(), ctx)
    row = conn.inserted[0]
    assert row["notes"] == EXPECTED_NOTES
