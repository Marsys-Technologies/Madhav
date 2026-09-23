"""M-3 (L3 §4.8) exit-gate fixture — `moon_channel` split flag.

When moon_channel='separate':
  - Moon-body contacts are absent from the century λ's activity term;
  - find_episodes(..., moon=True) serves Moon contacts on demand and
    writes a 'moon_on_demand' coverage partition, even for a zero-answer
    search;
  - the Moon channel carries no Sade-Sati testimony.

Synthetic chart data only (no real chart, no person).
"""
from __future__ import annotations

import pytest

from services.gochara_grammar.models import ConfigurationSentence
from services.gochara_v3 import engine


CHART_ID = "00000000-0000-4000-8000-0000000004a8"  # synthetic, non-person
T_JD = 2460000.0


def _sentence(body: str, orb_strength: float) -> ConfigurationSentence:
    return ConfigurationSentence(
        primitive="degree_contact",
        chart_id=CHART_ID,
        event_class="synthetic_m3",
        target_type="synthetic",
        target_ref="syn:target",
        transit_planet=body,
        secondary_planet=None,
        event_jd=T_JD,
        event_datetime_ist=None,
        uncited_extension=True,
        temporal_shape="point",
        detail={"orb_strength": orb_strength},
    )


class _StubContext:
    chart_id = CHART_ID


def test_blended_legacy_moon_in_activity():
    sentences = [_sentence("Saturn", 0.5), _sentence("Moon", 0.5)]
    activity, detail, _ = engine._compute_activity_v3(
        sentences, {"syn:target": 1.0},
    )
    # noisy-OR over two 0.5 contributions: 1 - 0.5*0.5 = 0.75
    assert activity == 0.75
    bodies = {c["transit_planet"] for c in detail["contributions"]}
    assert "Moon" in bodies
    assert "moon_channel" not in detail  # byte-identical legacy detail


def test_separate_moon_absent_from_century_lambda():
    sentences = [_sentence("Saturn", 0.5), _sentence("Moon", 0.5)]
    activity, detail, _ = engine._compute_activity_v3(
        sentences, {"syn:target": 1.0}, moon_channel="separate",
    )
    assert activity == 0.5  # only Saturn's contribution remains
    bodies = {c["transit_planet"] for c in detail["contributions"]}
    assert "Moon" not in bodies
    assert detail["moon_channel"] == "separate"
    assert detail["moon_sentences_excluded"] == 1


def test_find_episodes_moon_writes_coverage_partition(monkeypatch):
    sentences = [_sentence("Saturn", 0.5), _sentence("Moon", 0.5)]
    monkeypatch.setattr(
        engine, "_gather_sentences_no_db",
        lambda swe, context, targets, start, end: sentences,
    )
    result = engine.find_episodes(
        None, _StubContext(), ["syn:target"], T_JD - 5.0, T_JD + 5.0,
        moon=True, generation="syn-gen",
    )
    assert [s.transit_planet for s in result["episodes"]] == ["Moon"]
    coverage = result["coverage"]
    assert coverage is not None
    assert coverage.partition_kind == "moon_on_demand"
    assert coverage.targets_requested == coverage.targets_resolved
    # no Sade-Sati testimony in the Moon channel
    assert "sade_sati" not in result
    assert all("sade_sati" not in s.detail for s in result["episodes"])


def test_find_episodes_moon_zero_contacts_still_writes_coverage(monkeypatch):
    monkeypatch.setattr(
        engine, "_gather_sentences_no_db",
        lambda swe, context, targets, start, end: [_sentence("Saturn", 0.5)],
    )
    result = engine.find_episodes(
        None, _StubContext(), ["syn:target"], T_JD - 5.0, T_JD + 5.0,
        moon=True,
    )
    assert result["episodes"] == []
    coverage = result["coverage"]
    assert coverage is not None
    assert coverage.partition_kind == "moon_on_demand"
    assert coverage.relations_searched == ()
    assert coverage.unsearched_reason is None  # search DID run (H-3)


def test_flag_off_byte_identical():
    sentences = [_sentence("Saturn", 0.5), _sentence("Moon", 0.5)]
    a_default, d_default, tb_default = engine._compute_activity_v3(
        sentences, {"syn:target": 1.0},
    )
    a_blended, d_blended, tb_blended = engine._compute_activity_v3(
        sentences, {"syn:target": 1.0}, moon_channel="blended",
    )
    assert a_default == a_blended
    assert d_default == d_blended
    assert tb_default == tb_blended


def test_invalid_channel_rejected():
    with pytest.raises(ValueError, match="moon_channel"):
        engine._evaluate_single_from_context(
            None, None, 0.0, [], moon_channel="not_a_channel",
        )
