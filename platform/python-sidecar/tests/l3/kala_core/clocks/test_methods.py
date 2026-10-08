"""K1-1b oracles: sourced methods, shared uncertainty, L1-only scenarios."""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from math import sqrt

import pytest

from services.kala_core import clocks
from services.ka_dasha_kala import KaDashaKalaService

T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AY = "lahiri_chitrapaksha"
PIN = dict(build_id="base", ayanamsha_id=AY, tier="single")


def api(name):
    assert hasattr(clocks, name), f"missing K1-1b F2 API: {name}"
    return getattr(clocks, name)


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class L1:
    """Reject writes and read pins exactly like chart_dashas."""
    def __init__(self, *, system="vimshottari", build="base", shift=timedelta(0), lords=("Sun", "Moon")):
        self.rows = [dict(
            dasha_row_id=f"{build}-{i}", parent_row_id=None, level_n=1,
            lord_graha=lord, start_iso=T0 + timedelta(days=i * 100) + shift,
            end_iso=T0 + timedelta(days=(i + 1) * 100) + shift,
            chart_id=CHART, build_id=build, ayanamsha_id=AY, system_id=system,
            verification_pass_status="single", applies_to_this_chart_flag=True,
            is_truncated_at_window_start=False, is_truncated_at_window_end=False,
        ) for i, lord in enumerate(lords)]

    def execute(self, sql, params):
        assert sql.lstrip().startswith("SELECT")
        assert "build_id = %s" in sql and "verification_pass_status = %s" in sql
        chart, system, build, ay, tier = params
        return Rows([r for r in self.rows if
                     (r["chart_id"], r["system_id"], r["build_id"], r["ayanamsha_id"], r["verification_pass_status"])
                     == (chart, system, build, ay, tier)])


def budget(**kwargs):
    return api("BoundaryUncertainty")(
        sigma_birth_days=kwargs.get("sigma_birth_days", .01),
        sigma_ayanamsha_deg=kwargs.get("sigma_ayanamsha_deg", .2),
        velocity_deg_per_day=kwargs.get("velocity_deg_per_day", 13.),
        days_per_degree=kwargs.get("days_per_degree", 100.),
        birth_ayanamsha_covariance=kwargs.get("birth_ayanamsha_covariance", 0.),
        artifact_id="admitted-L1-uncertainty-v1", fact_ids=("moon-velocity", "birth-sigma", "ayanamsha-spread"),
    )


def test_linearisation_keeps_the_birth_time_cross_term():
    # k=100, v=13: dB=-1299*dT+100*dA; old sqrt((kv*T)^2+T^2+(k*A)^2) fails.
    assert api("boundary_sigma")(budget()).total_seconds() / 86400 == pytest.approx(sqrt(1299**2 * .01**2 + 100**2 * .2**2))


def test_birth_and_ayanamsha_covariance_is_not_dropped():
    assert api("boundary_sigma")(budget(birth_ayanamsha_covariance=.001)).total_seconds() / 86400 == pytest.approx(sqrt(1299**2 * .01**2 + 400 - 259.8))


def test_two_adjacent_boundaries_share_one_shift():
    u = budget()
    delta = api("boundary_shift")(u, birth_shift_days=.001, ayanamsha_shift_deg=.1)
    assert delta.total_seconds() / 86400 == pytest.approx(8.701)
    base = clocks.boundaries(L1(), CHART, "vimshottari", uncertainty=u, **PIN)
    shifted = clocks.boundaries(L1(build="shift", shift=delta), CHART, "vimshottari", uncertainty=u, **(PIN | {"build_id": "shift"}))
    assert [b.instant - a.instant for a, b in zip(base, shifted)] == [timedelta(days=8.701)] * 2


def test_zero_budget_preserves_l1_instants_and_row_ids():
    result = clocks.boundaries(L1(), CHART, "vimshottari", uncertainty=budget(sigma_birth_days=0, sigma_ayanamsha_deg=0), **PIN)
    assert [(r.instant, r.source_row_id, r.sigma) for r in result] == [(T0, "base-0", timedelta(0)), (T0 + timedelta(days=100), "base-1", timedelta(0))]


def test_no_admitted_uncertainty_is_a_null_not_zero_precision():
    assert clocks.period_context(L1(), CHART, T0, "vimshottari", **PIN).sigma_boundary is None


@pytest.mark.parametrize("kwargs", [{"sigma_birth_days": -1}, {"days_per_degree": float("nan")}, {"birth_ayanamsha_covariance": 1}])
def test_invalid_uncertainty_is_refused(kwargs):
    with pytest.raises(ValueError):
        api("boundary_sigma")(budget(**kwargs))


def fact(value, *ids):
    return api("ClockFact")(value, ids)


def ashtottari(**kwargs):
    return api("AshtottariFacts")(
        rahu_house_from_lagna=fact(kwargs.get("lagna_house", 5), "rahu-sign", "lagna-sign"),
        rahu_house_from_lagna_lord=fact(kwargs.get("lord_house", 6), "rahu-sign", "lagna-lord-sign"),
        daytime=fact(kwargs.get("daytime", True), "birth-daytime"),
        paksha=fact(kwargs.get("paksha", "krishna"), "birth-paksha"),
    )


def test_ashtottari_failed_condition_has_its_fact_ids():
    result = clocks.period_context(L1(system="ashtottari"), CHART, T0, "ashtottari", method_facts=ashtottari(), **PIN)
    assert (result.applicability, result.applicability_detail.failed_conditions) == ("method_inapplicable", ("rahu_kendra_trikona_from_lagna_lord",))
    assert result.applicability_detail.conditions[1].fact_ids == ("rahu-sign", "lagna-lord-sign")


def test_ashtottari_in_lagna_is_a_separate_failure():
    assert api("assess_ashtottari")(ashtottari(lagna_house=1, lord_house=4)).failed_conditions == ("rahu_not_in_lagna",)


def test_ashtottari_time_condition_is_disclosed_as_recommendation():
    # BPHS 46.23 is "advisable", separate from entry rule 46.17-20.
    result = api("assess_ashtottari")(ashtottari(lord_house=4, paksha="shukla"))
    assert (result.state, result.conditions[2].state, result.conditions[2].required) == ("applicable", "failed", False)


def test_true_ashtottari_producer_default_does_not_establish_applicability():
    assert clocks.period_context(L1(system="ashtottari"), CHART, T0, "ashtottari", **PIN).applicability == "unknown"


def test_fact_value_without_a_reference_cannot_qualify_applicability():
    result = api("assess_ashtottari")(replace(ashtottari(lord_house=4), rahu_house_from_lagna_lord=fact(4)))
    assert result.state == "unknown"


def test_mula_is_distinct_from_cara_and_cannot_read_its_rows():
    assert (api("dasha_method")("mula").sources, api("dasha_method")("mula").l1_producer) == (("Saravali PG155",), None)
    with pytest.raises(clocks.ClockUnavailable, match="method_not_built"):
        clocks.boundaries(L1(system="chara_karaka", lords=("Aries", "Taurus")), CHART, "mula", **PIN)


def test_kendradi_cannot_be_an_alias_of_cara():
    assert api("dasha_method")("karaka_kendradi").method_id != api("dasha_method")("chara").method_id


def test_kp_and_yogini_disclose_shared_moon_ancestry():
    assert api("dasha_method")("vimshottari_kp").ancestry_groups == api("dasha_method")("yogini").ancestry_groups == ("moon_nakshatra",)


@pytest.mark.parametrize("direction,lords,deha,jiva", [("savya", ("Aries", "Taurus"), "Aries", "Sagittarius"), ("apasavya", ("Pisces", "Aquarius"), "Pisces", "Cancer")])
def test_kalachakra_reads_direction_and_signs_without_lord_coercion(direction, lords, deha, jiva):
    details = api("KalachakraFacts")(direction, 1, deha, jiva, ("simhavalokana",), ("kc-pada", "kc-deha", "kc-jiva", "kc-gati"))
    result = clocks.period_context(L1(system="kalachakra", lords=lords), CHART, T0, "kalachakra", method_facts=details, **PIN)
    assert (result.lords, result.method_detail.direction, result.method_detail.deha, result.method_detail.jiva) == ({"MD": lords[0]}, direction, deha, jiva)


def test_nakshatra_crossing_reads_coupled_l1_ladders_without_changing_cara():
    scenario = api("ClockScenario")("crossing", "crossed", AY, "single", "moon_star", "L1-birth-shift", ("moon-nakshatra-after",))
    observed = []
    for system, before, after in [("vimshottari", ("Sun", "Moon"), ("Moon", "Mars")), ("yogini", ("Mangala", "Pingala"), ("Pingala", "Dhanya")), ("chara_karaka", ("Aries", "Taurus"), ("Aries", "Taurus"))]:
        conn = L1(system=system, lords=before)
        conn.rows += L1(system=system, build="crossed", lords=after).rows
        base = clocks.period_context(conn, CHART, T0, system, **PIN)
        variant = api("scenario_set")(conn, CHART, T0, system, scenarios=(scenario,))[0]
        observed.append((base.lords["MD"], variant.context.lords["MD"]))
        assert variant.boundaries[0].source_row_id == "crossed-0"
    assert observed == [("Sun", "Moon"), ("Mangala", "Pingala"), ("Aries", "Aries")]


def test_nakshatra_crossing_with_real_l1_producer_rows(monkeypatch):
    """An upstream compute fixture, not two hand-written anticipated ladders.

    Birth shifts by .001 day while the measured Moon crosses Ashwini/Bharani.
    F2 receives only the emitted chart_dashas rows; no source is persisted.
    """
    from ga_writers import ga_dashas_writer as producer
    chart = "11111111-1111-4111-8111-111111111111"
    # This isolated synthetic chart needs no natal karaka attachment for F2.
    monkeypatch.setitem(producer._KARAKA_ROLE_CACHE, (chart, AY), {})
    observed = []
    for compute, system in [(producer.compute_vimshottari, "vimshottari"), (producer.compute_yogini_system, "yogini")]:
        before = compute(360 / 27 - .01, 2460310.5, AY, chart, "base")
        after = compute(360 / 27 + .01, 2460310.501, AY, chart, "crossed")
        conn = L1()
        conn.rows = before + after
        as_of = T0 + timedelta(days=.002)  # after both birth instants
        base = clocks.period_context(conn, chart, as_of, system, **PIN)
        variant = api("ClockScenario")("crossing", "crossed", AY, "single", "moon_star", "L1-birth-shift", ("moon-before", "moon-after"))
        shifted = api("scenario_set")(conn, chart, as_of, system, scenarios=(variant,))[0]
        observed.append((base.lords["MD"], shifted.context.lords["MD"]))
    assert observed == [("Ketu", "Venus"), ("Mangala", "Pingala")]


def test_lagna_start_sensitivity_does_not_become_a_cara_variant():
    scenario = api("ClockScenario")("lagna", "variant", AY, "single", "lagna_star", "L1-lagna-start", ("lagna-nakshatra",))
    with pytest.raises(ValueError, match="nakshatra"):
        api("scenario_set")(L1(), CHART, T0, "chara", scenarios=(scenario,))


@pytest.mark.parametrize("start", ["lagna_star", "satyacharya"])
def test_kalachakra_does_not_inherit_alternate_starts_from_its_moon_ancestry(start):
    scenario = api("ClockScenario")("variant", "base", AY, "single", start, "L1-start", ("nakshatra",))
    with pytest.raises(ValueError, match="nakshatra"):
        api("scenario_set")(L1(system="kalachakra", lords=("Aries", "Taurus")), CHART, T0, "kalachakra", scenarios=(scenario,))


def test_scenario_cannot_silently_reuse_the_baseline_build():
    scenario = api("ClockScenario")("absent", "missing", AY, "single", "moon_star", "L1-shift", ("moon-nakshatra",))
    with pytest.raises((LookupError, clocks.ClockUnavailable)):
        api("scenario_set")(L1(), CHART, T0, "vimshottari", scenarios=(scenario,))


@pytest.mark.parametrize("field", ["score", "agreement", "eligibility_score", "cross_dasha_agreement"])
def test_scored_f2_row_is_rejected(field):
    with pytest.raises(ValueError, match="F2"):
        api("validate_f2_row")({"method_id": "vimshottari", field: .5})


def test_facade_reads_core_clock_without_legacy_scoring():
    result = KaDashaKalaService(L1()).period_context(CHART, T0, "vimshottari", **PIN)
    assert (result.lords, result.method.method_id.value, result.build_id) == ({"MD": "Sun"}, "vimshottari", "base")
    api("validate_f2_row")(asdict(result))


def test_legacy_query_remains_an_explicit_compatibility_shim():
    assert callable(getattr(KaDashaKalaService(L1()), "legacy_query", None))
