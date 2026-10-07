"""
tests/l2/test_bo_samskara_fidelity_golden.py -- golden-value fidelity test for bo_samskara

``bodha_signal_embeddings.embedding_input_summary`` is the sentence-like text that is embedded and
stored next to the vector. The writer composes it in the pure function ``_build_input_summary`` as
``' | '``-joined parts: signal_type_class, signal_tradition, signal_type_id, then
``key=value`` for each present key of ("fact_key", "fact_value_text", "graha", "yoga", "dosha") in
that fixed order, then ``domains=`` plus the sorted domains joined by a comma.

The expected strings below are stated by hand from that template, never read from the builder.
Pure function, no database, no embedding model.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_samskara import _build_input_summary


def test_embedding_input_summary_golden() -> None:
    sig = {
        "signal_type_class": "yoga",
        "signal_tradition": "parashari",
        "signal_type_id": "yoga_catalog:gaja_kesari",
        "configuration_jsonb": {
            "graha": "Jupiter",
            "fact_key": "yoga_name",
            "yoga": "gaja_kesari",
            "orb_deg": 3.9,
        },
        "domains_affected_array": ["wealth", "career"],
    }
    embedding_input_summary = _build_input_summary(sig)
    assert embedding_input_summary == (
        "yoga | parashari | yoga_catalog:gaja_kesari"
        " | fact_key=yoga_name | graha=Jupiter | yoga=gaja_kesari"
        " | domains=career,wealth"
    )


def test_embedding_input_summary_drops_absent_parts_golden() -> None:
    sig = {
        "signal_type_class": "panchanga",
        "signal_tradition": None,
        "signal_type_id": "tithi:name",
        "configuration_jsonb": '{"fact_value_text": "Shukla Tritiya"}',
    }
    embedding_input_summary = _build_input_summary(sig)
    assert embedding_input_summary == "panchanga | tithi:name | fact_value_text=Shukla Tritiya"
