"""
tests/l2/test_bo_samskara_narr_golden.py -- Narr golden-value test for bo_samskara

Track I item TI-L2-11 (Track A A.L2 brief ``bo_samskara_ELEVATION_BRIEF_v1_0.md``, which exists only on
unmerged PR #2831,
cross-asset fix CF-14): ``bodha_signal_embeddings.embedding_input_summary`` is the text
that is embedded, stored next to the vector, and compared byte-for-byte to decide
whether a prior embedding can be reused. It is composed from stored signal fields by
the pure function ``_build_input_summary``. This test pins that composition on golden
values: every field the summary states is the stored field it was composed from, in a
fixed order, and nothing the signal does not carry is invented.

What this does NOT do: it does not declare ``embedding_input_summary`` under
``evidence.prose_fields`` in ``asset_declarations.json`` (the other half of TI-L2-11;
the declarations file is held while PR #2984 changes it), and it changes no writer, no
stored value and no registry row. It never calls the embedding model.
"""
from __future__ import annotations

import json

from pipeline.orchestrator.writers.bo_samskara import _build_input_summary

SEP = " | "


def _sig(**kw) -> dict:
    base = {
        "signal_type_class": "composite_state",
        "signal_tradition": "parashari",
        "signal_type_id": "graha_dignity_per_varga:dignity_state",
        "configuration_jsonb": {},
        "domains_affected_array": [],
    }
    base.update(kw)
    return base


def test_golden_full_signal() -> None:
    sig = _sig(
        configuration_jsonb={
            "fact_key": "dignity_state",
            "fact_value_text": "exalted",
            "graha": "Jupiter",
        },
        domains_affected_array=["wealth", "career"],
    )
    assert _build_input_summary(sig) == (
        "composite_state | parashari | graha_dignity_per_varga:dignity_state"
        " | fact_key=dignity_state | fact_value_text=exalted | graha=Jupiter"
        " | domains=career,wealth"
    )


def test_golden_yoga_and_dosha_keys_keep_their_fixed_order() -> None:
    sig = _sig(
        signal_type_class="yoga",
        configuration_jsonb={"dosha": "kuja", "yoga": "gaja_kesari", "fact_key": "yoga_name"},
        domains_affected_array=["marriage"],
    )
    assert _build_input_summary(sig) == (
        "yoga | parashari | graha_dignity_per_varga:dignity_state"
        " | fact_key=yoga_name | yoga=gaja_kesari | dosha=kuja | domains=marriage"
    )


def test_absent_fields_are_dropped_not_invented() -> None:
    sig = {"signal_type_class": "panchanga", "signal_tradition": None, "signal_type_id": "tithi:name"}
    out = _build_input_summary(sig)
    assert out == "panchanga | tithi:name"
    assert SEP + SEP not in out and not out.startswith(SEP) and not out.endswith(SEP)
    assert "None" not in out and "domains" not in out and "fact_key" not in out


def test_configuration_as_json_text_is_read_like_a_dict() -> None:
    cfg = {"fact_key": "sign", "graha": "Saturn"}
    as_dict = _build_input_summary(_sig(configuration_jsonb=cfg))
    as_text = _build_input_summary(_sig(configuration_jsonb=json.dumps(cfg)))
    assert as_text == as_dict
    assert as_dict.endswith("fact_key=sign | graha=Saturn")


def test_unparseable_configuration_text_states_nothing_from_it() -> None:
    out = _build_input_summary(_sig(configuration_jsonb="{not json"))
    assert out == "composite_state | parashari | graha_dignity_per_varga:dignity_state"


def test_keys_outside_the_narrated_set_are_not_narrated() -> None:
    out = _build_input_summary(_sig(configuration_jsonb={"graha": "Mars", "orb_deg": 3.9, "salience": "high"}))
    assert "graha=Mars" in out
    assert "orb_deg" not in out and "salience" not in out and "3.9" not in out


def test_domains_are_sorted_so_input_order_cannot_change_the_text() -> None:
    a = _build_input_summary(_sig(domains_affected_array=["wealth", "career", "health"]))
    b = _build_input_summary(_sig(domains_affected_array=["health", "wealth", "career"]))
    assert a == b
    assert a.endswith("domains=career,health,wealth")


def test_configuration_key_order_cannot_change_the_text() -> None:
    a = _build_input_summary(_sig(configuration_jsonb={"graha": "Sun", "fact_key": "sign"}))
    b = _build_input_summary(_sig(configuration_jsonb={"fact_key": "sign", "graha": "Sun"}))
    assert a == b


def test_every_narrated_config_value_is_the_stored_value() -> None:
    cfg = {
        "fact_key": "nakshatra", "fact_value_text": "Rohini",
        "graha": "Moon", "yoga": "vasi", "dosha": "kala_sarpa",
    }
    out = _build_input_summary(_sig(configuration_jsonb=cfg))
    for key, value in cfg.items():
        assert f"{key}={value}" in out
    # and in the documented order
    positions = [out.index(f"{k}=") for k in ("fact_key", "fact_value_text", "graha", "yoga", "dosha")]
    assert positions == sorted(positions)


def test_output_is_capped_at_512_characters() -> None:
    long_domains = [f"domain_{i:03d}" for i in range(200)]
    out = _build_input_summary(_sig(domains_affected_array=long_domains))
    assert len(out) == 512
    assert out.startswith("composite_state | parashari | ")


def test_identical_input_gives_identical_text() -> None:
    sig = _sig(configuration_jsonb={"graha": "Venus"}, domains_affected_array=["relationship"])
    assert _build_input_summary(sig) == _build_input_summary(dict(sig))
