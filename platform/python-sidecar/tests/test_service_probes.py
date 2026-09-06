"""Service-asset health probes (pipeline.orchestrator.service_probes).

SAMĀPTI B-N8-SWEEPFIX regressions for F-04 and F-06 (CLAUDE.md §N.8 — a status
field must have a real detector behind it, and that detector must be able to
produce a failing result).

F-04 — `_probe_ephemeris_engine` could not return GREEN in ANY environment. Its
Julian Day literal decoded to 1984-01-02, not the 1984-02-05 its comment claimed
(33.77 days off), and both FORENSIC expectations are SIDEREAL LAHIRI signs while
the checks measured TROPICAL positions. The node check therefore failed on every
run, so `asset_runner.py:332` (`if status == "GREEN"` … else `mark_asset_error`)
could only ever mark the ephemeris service asset in error. Either it was never
dispatched — in which case whatever marks that asset healthy does so without
running the probe that gates it — or it was, and an L0 asset sealed as
"provisioned" was permanently unhealthy. Both branches are §N.8 findings.

F-06 — `panchanga_day_runs` was `passed: result is not None` against a callee with
no `return None` path: a field that could not read False. Separately, `status` was
computed from the `failures` list while that check set `passed: False` without
appending to it, so a false check could ship inside a GREEN verdict reading
"All checks passed".

These tests are DB-free and need no network. They DO need `swisseph` and
`panchang_engine`, both of which are sidecar requirements.
"""
from __future__ import annotations

import sys
import pathlib
import os

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import service_probes as sp  # noqa: E402


_PANCHANGA_SPEC = {
    "probe_type": "panchanga_engine",
    "forensic_instant": "1984-02-05T10:43:00",
    "forensic_lat": 20.27,
    "forensic_lon": 85.84,
    "forensic_tz_offset": 330,
    "forensic_expected": {
        "tithi": "Shukla Tritiya",
        "nakshatra": "Purva Bhadrapada",
        "yoga": "Shiva",
        "karana": "Garaja",
        "vara": "Ravivara",
    },
}

_EPHEMERIS_SPEC = {
    "probe_type": "ephemeris_engine",
    "forensic_jd": 2445735.717361111,
    "expected_sun_sign": 10,
    "expected_mean_node_rahu_sign": 2,
    "ayanamsha": "lahiri",
    "node_mode": "mean",
    "allowed_ephemeris_backends": ["swiss_ephemeris_file"],
    "ephemeris_file_sha256": {
        "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
        "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
        "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
    },
}

_GRAHA_SANCARA_SPEC = {
    "probe_type": "graha_sancara_forensic",
    "forensic_birth_instant": "1984-02-05T10:43:00",
    "forensic_ayanamsha": "lahiri",
    "forensic_expected_moon_sign": "Aquarius",
}

_TULANA_SPEC = {
    "probe_type": "tulana_ranking_forensic",
    "forensic_reference_date": "2026-01-01",
    "forensic_window_a": {
        "window_id": "test-window-a",
        "mode": "A",
        "peak_date": "2026-01-01",
        "convergence_score": 0.8,
        "confidence_label": "high",
        "rarity_years": 15.0,
    },
    "forensic_window_b": {
        "window_id": "test-window-b",
        "mode": "A",
        "peak_date": "2026-06-01",
        "convergence_score": 0.5,
        "confidence_label": "moderate",
        "rarity_years": 5.0,
    },
    "forensic_expected_composite_a": 0.795,
    "forensic_expected_composite_b": 0.4234,
    "forensic_expected_winner_window_id": "test-window-a",
    "forensic_expected_decisive_factor": "proximity_factor",
}

_DASHA_KALA_SPEC = {
    "probe_type": "dasha_kala_proxy_integrity",
    "expected_systems": [
        "vimshottari", "yogini", "ashtottari", "chara_karaka",
        "naisargika", "mudda", "kalachakra",
    ],
}

_EPHEMERIS_CORPUS_FILES = tuple(_EPHEMERIS_SPEC["ephemeris_file_sha256"])
_EPHEMERIS_CORPUS_PATH = pathlib.Path(os.environ.get("SWE_EPHE_PATH", "/app/ephe"))
_HAS_PINNED_EPHEMERIS_CORPUS = all(
    (_EPHEMERIS_CORPUS_PATH / name).is_file() for name in _EPHEMERIS_CORPUS_FILES
)


def _probe(kind: str) -> dict:
    if kind == "panchanga_engine":
        spec = _PANCHANGA_SPEC
    elif kind == "ephemeris_engine":
        spec = _EPHEMERIS_SPEC
    elif kind == "graha_sancara_forensic":
        spec = _GRAHA_SANCARA_SPEC
    elif kind == "tulana_ranking_forensic":
        spec = _TULANA_SPEC
    elif kind == "dasha_kala_proxy_integrity":
        spec = _DASHA_KALA_SPEC
    else:
        spec = {"probe_type": kind}
    return sp.run_health_probe("bg_x", spec)


def _check(res: dict, name: str) -> dict:
    matches = [c for c in res["checks"] if c["check"] == name]
    assert matches, f"check {name!r} absent from {[c['check'] for c in res['checks']]}"
    return matches[0]


# ── F-04: the ephemeris probe must be ABLE to return GREEN ────────────────────

@pytest.mark.skipif(
    not _HAS_PINNED_EPHEMERIS_CORPUS,
    reason="requires the production-shaped pinned Swiss Ephemeris corpus",
)
def test_ephemeris_probe_returns_green():
    """The headline F-04 assertion. Pre-fix this returned 'degraded' on every run
    in every environment, so `asset_runner` could only ever mark the asset error."""
    res = _probe("ephemeris_engine")
    assert res["status"] == "GREEN", (
        f"the ephemeris probe must be satisfiable — a gate that is always red is as "
        f"uninformative as one that is always green. Got {res['status']}: {res['message']}"
    )


def test_ephemeris_julian_day_decodes_to_the_forensic_birth_date():
    """The JD is a load-bearing literal: on the wrong one the Sun check passed only
    by accident. Round-trip it through swisseph rather than trusting the comment."""
    swe = pytest.importorskip("swisseph")
    y, m, d, ut = swe.revjul(_EPHEMERIS_SPEC["forensic_jd"], swe.GREG_CAL)
    assert (y, m, d) == (1984, 2, 5), (
        f"registered forensic_jd decodes to {y:04d}-{m:02d}-{d:02d}, not the FORENSIC "
        f"birth date 1984-02-05 (CLAUDE.md §B)"
    )
    # 10:43 IST = 05:13 UT
    assert abs(ut - (5 + 13 / 60.0)) < 1e-3, f"UT component {ut} is not 05:13"


def test_ephemeris_checks_assert_the_forensic_sidereal_signs():
    """Both expectations are sidereal-Lahiri sign equalities against CLAUDE.md §B's
    anchors — not a 60°-wide window that a wrong ayanamsha would still satisfy."""
    res = _probe("ephemeris_engine")
    sun = _check(res, "sidereal_sun_forensic_sign")
    assert sun["sun_sign"] == 10 and sun["expected_sun_sign"] == 10, sun  # Makara
    assert sun["ayanamsha"] == "Lahiri", sun
    node = _check(res, "sidereal_mean_node_rahu_invariant")
    assert node["rahu_sign"] == 2 and node["ketu_sign"] == 8, node       # Vrishabha / Vrischika


def test_ephemeris_sun_check_fails_on_a_wrong_julian_day():
    """CAN-FAIL proof: restore the pre-fix JD literal and the probe must go red."""
    wrong = dict(_EPHEMERIS_SPEC, forensic_jd=2445701.948264)  # 1984-01-02
    res = sp.run_health_probe("bg_ephemeris_engine", wrong)
    assert res["status"] != "GREEN", "a 33-day-wrong Julian Day must not pass"
    assert _check(res, "sidereal_sun_forensic_sign")["passed"] is False


def test_ephemeris_node_check_fails_on_a_wrong_expected_sign():
    """CAN-FAIL proof for the node invariant, independent of the Sun check."""
    wrong = dict(_EPHEMERIS_SPEC, expected_mean_node_rahu_sign=5)
    res = sp.run_health_probe("bg_ephemeris_engine", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "sidereal_mean_node_rahu_invariant")["passed"] is False


def test_ephemeris_reports_which_ephemeris_backend_served_the_position():
    """The pre-fix code discarded `retflag` (`xx, _ = swe.calc_ut(...)`) — the only
    datum distinguishing the ephemeris files from the Moshier analytic fallback,
    while the check was named `de441_position_query`. The check is now named for
    what it asserts, and the backend is reported as data rather than claimed."""
    sun = _check(_probe("ephemeris_engine"), "sidereal_sun_forensic_sign")
    assert sun["ephemeris_backend"] in {
        "jpl_file", "swiss_ephemeris_file", "moshier_analytic_fallback",
    }, sun


def test_ephemeris_probe_fails_closed_on_missing_registry_contract_fields():
    res = sp.run_health_probe("bg_ephemeris_engine", {"probe_type": "ephemeris_engine"})
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_ephemeris_probe_fails_closed_when_sha_pins_are_missing():
    missing_pins = dict(_EPHEMERIS_SPEC)
    del missing_pins["ephemeris_file_sha256"]
    res = sp.run_health_probe("bg_ephemeris_engine", missing_pins)
    assert res["status"] == "down"
    check = _check(res, "probe_config_valid")
    assert check["passed"] is False
    assert "ephemeris_file_sha256" in check["error"]


def test_ephemeris_probe_enforces_registered_backend_allowlist():
    wrong = dict(_EPHEMERIS_SPEC, allowed_ephemeris_backends=["jpl_file"])
    res = sp.run_health_probe("bg_ephemeris_engine", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "sidereal_sun_forensic_sign")["passed"] is False


def test_ephemeris_probe_fails_when_pinned_corpus_is_missing(monkeypatch, tmp_path):
    pinned = dict(
        _EPHEMERIS_SPEC,
        allowed_ephemeris_backends=["swiss_ephemeris_file"],
        ephemeris_file_sha256={
            "sepl_18.se1": "a" * 64,
            "semo_18.se1": "b" * 64,
            "seas_18.se1": "c" * 64,
        },
    )
    monkeypatch.setenv("SWE_EPHE_PATH", str(tmp_path))
    res = sp.run_health_probe("bg_ephemeris_engine", pinned)
    assert res["status"] != "GREEN"
    assert _check(res, "ephemeris_corpus_sha256")["passed"] is False


# ── F-06: the panchanga probe's third check and its aggregation ───────────────

def test_panchanga_probe_returns_green():
    assert _probe("panchanga_engine")["status"] == "GREEN"


def test_panchanga_probe_fails_closed_on_missing_registry_contract_fields():
    res = sp.run_health_probe("bg_panchanga", {"probe_type": "panchanga_engine"})
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_panchanga_probe_executes_the_registered_forensic_instant():
    wrong_instant = dict(_PANCHANGA_SPEC, forensic_instant="1984-02-06T10:43:00")
    res = sp.run_health_probe("bg_panchanga", wrong_instant)
    assert res["status"] != "GREEN", (
        "the registered forensic instant must drive execution; a hard-coded substitute "
        "would incorrectly preserve GREEN"
    )
    assert _check(res, "forensic_birth_smoke")["passed"] is False


def test_panchanga_day_check_asserts_the_sunrise_forensic_angas(monkeypatch):
    """CAN-FAIL proof: the check must fail on a wrong anga. The pre-fix expression
    (`result is not None`) could not — `panchanga_day` is annotated `-> Panchang`
    and has no `return None` path, so no input could falsify it."""
    import panchang_engine
    from datetime import date as _date

    _BIRTH = _date(1984, 2, 5)

    class _WrongDay:
        date = _BIRTH
        vara = "Somavara"            # FORENSIC says Ravivara
        tithi = "Shukla Tritiya"
        nakshatra = "Purva Bhadrapada"
        yoga = "Shiva"

    monkeypatch.setattr(panchang_engine, "panchanga_day", lambda *a, **k: _WrongDay())
    res = _probe("panchanga_engine")
    assert res["status"] != "GREEN"
    chk = _check(res, "panchanga_day_forensic_sunrise_angas")
    assert chk["passed"] is False
    assert any("vara" in m for m in chk["mismatches"]), chk


def test_verdict_cannot_be_green_while_a_reported_check_is_false():
    """F-06 part 2. `status` used to be derived from the `failures` list alone while
    check 3 set `passed: False` without appending to it — so a false check could
    ship inside a GREEN verdict whose message read 'All checks passed', and
    `asset_runner.py:332` would promote the asset to 'lit' on it."""
    res = sp._aggregate([{"check": "a", "passed": True},
                         {"check": "b", "passed": False}], [])
    assert res["status"] != "GREEN", (
        "a verdict must not contradict the checks it ships in the same payload"
    )
    assert res["message"] != "All checks passed"


# ── ka_graha_sancara probe (NIRMĀṆA L3-W4, F-L3-15) ───────────────────────────

def test_graha_sancara_probe_returns_green():
    res = _probe("graha_sancara_forensic")
    assert res["status"] == "GREEN", (
        f"got {res['status']}: {res['message']}"
    )


def test_graha_sancara_probe_calls_get_ephemeris_with_force_live_and_no_db_conn(monkeypatch):
    """CAN-FAIL proof for the force_live=True argument itself. This probe is
    deliberately DB-free (db_conn=None always), which already makes PATH-A
    (day-grade ephemeris_daily, 12:00 UT — wrong sign for this birth instant,
    L3-W3 M3) unreachable regardless of force_live's value — so asserting the
    RESULT's `source` field cannot fail on a dropped force_live=True (nothing
    to regress to with db_conn=None). Assert the actual call arguments instead:
    this fails if force_live is ever silently removed or a db_conn is added."""
    from pipeline.orchestrator import service_probes as module
    import services.ka_graha_sancara.engine as engine_module

    captured: dict = {}
    real_get_ephemeris = engine_module.get_ephemeris  # capture BEFORE patching

    def spy(*args, **kwargs):
        captured.update(kwargs)
        captured["args"] = args
        return real_get_ephemeris(*args, **kwargs)

    monkeypatch.setattr(engine_module, "get_ephemeris", spy)
    # _probe_graha_sancara imports get_ephemeris fresh inside the function body,
    # so patching the module attribute it re-imports from is what takes effect.
    res = module.run_health_probe("ka_graha_sancara", _GRAHA_SANCARA_SPEC)

    assert captured.get("db_conn") is None
    assert captured.get("force_live") is True
    check = _check(res, "forensic_moon_sign")
    assert check["moon_sign"] == "Aquarius"


def test_graha_sancara_probe_fails_closed_on_missing_registry_contract_fields():
    res = sp.run_health_probe("ka_graha_sancara", {"probe_type": "graha_sancara_forensic"})
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_graha_sancara_probe_fails_on_wrong_expected_moon_sign():
    """CAN-FAIL proof: a wrong expected sign must not be swallowed."""
    wrong = dict(_GRAHA_SANCARA_SPEC, forensic_expected_moon_sign="Pisces")
    res = sp.run_health_probe("ka_graha_sancara", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "forensic_moon_sign")["passed"] is False


def test_graha_sancara_probe_rejects_a_non_lahiri_ayanamsha():
    """The live-compute path only supports lahiri (engine constraint) — a probe
    contract claiming otherwise must fail closed, not silently coerce."""
    wrong = dict(_GRAHA_SANCARA_SPEC, forensic_ayanamsha="raman")
    res = sp.run_health_probe("ka_graha_sancara", wrong)
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_graha_sancara_probe_reports_nine_grahas_present():
    check = _check(_probe("graha_sancara_forensic"), "nine_grahas_present")
    assert check["passed"] is True
    assert check["graha_count"] == 9


def test_add_check_makes_a_silent_false_structurally_impossible():
    """The single append point is the mechanism behind the guarantee above."""
    checks: list[dict] = []
    failures: list[str] = []
    sp._add_check(checks, failures, "x", False, "x blew up")
    assert failures == ["x blew up"]
    sp._add_check(checks, failures, "y", True)
    assert len(failures) == 1 and len(checks) == 2
    assert sp._aggregate(checks, failures)["status"] == "degraded"


# ── ka_tulana probe (NIRMĀṆA L3-W3, F-L3-15 third slice) ─────────────────────

def test_tulana_probe_returns_green():
    res = _probe("tulana_ranking_forensic")
    assert res["status"] == "GREEN", (
        f"got {res['status']}: {res['message']}"
    )


def test_tulana_probe_fails_closed_on_missing_registry_contract_fields():
    res = sp.run_health_probe("ka_tulana", {"probe_type": "tulana_ranking_forensic"})
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_tulana_probe_fails_on_wrong_expected_composite():
    """CAN-FAIL proof: a wrong pinned composite score must not be swallowed."""
    wrong = dict(_TULANA_SPEC, forensic_expected_composite_a=0.5)
    res = sp.run_health_probe("ka_tulana", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "forensic_composite_and_rank_order")["passed"] is False


def test_tulana_probe_fails_on_wrong_expected_winner():
    """CAN-FAIL proof: window-b is a valid window_id (passes config
    validation) but is not the real winner — must fail at the verdict check,
    not be silently accepted."""
    wrong = dict(_TULANA_SPEC, forensic_expected_winner_window_id="test-window-b")
    res = sp.run_health_probe("ka_tulana", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "probe_config_valid")["passed"] is True
    assert _check(res, "forensic_compare_verdict")["passed"] is False


def test_tulana_probe_fails_on_wrong_expected_decisive_factor():
    """CAN-FAIL proof: compare()'s decisive_factor is independently checked
    from rank_windows()'s composite scores — a wrong pin here must not be
    swallowed even when the composite/rank-order check above passes."""
    wrong = dict(_TULANA_SPEC, forensic_expected_decisive_factor="rarity_years")
    res = sp.run_health_probe("ka_tulana", wrong)
    assert res["status"] != "GREEN"
    assert _check(res, "forensic_composite_and_rank_order")["passed"] is True
    assert _check(res, "forensic_compare_verdict")["passed"] is False


def test_tulana_probe_rejects_a_malformed_window():
    wrong = dict(_TULANA_SPEC)
    wrong["forensic_window_a"] = {"window_id": "test-window-a"}  # missing fields
    res = sp.run_health_probe("ka_tulana", wrong)
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


# ── ka_dasha_kala probe (D-CND-34 ruling, #2071 — F-L3-15's fourth slice) ────

def test_dasha_kala_probe_returns_green():
    res = _probe("dasha_kala_proxy_integrity")
    assert res["status"] == "GREEN", (
        f"got {res['status']}: {res['message']}"
    )


def test_dasha_kala_probe_every_check_discloses_proxy_scope():
    """The ruling's own required condition: no check may omit the scope
    disclosure, so a caller reading a single check in isolation still sees
    that this measured importability + constant-set identity only, never
    live-DB correctness."""
    res = _probe("dasha_kala_proxy_integrity")
    for check in res["checks"]:
        assert "scope" in check, f"check {check['check']!r} missing scope disclosure"
        assert "PROXY" in check["scope"]


def test_dasha_kala_probe_fails_closed_on_missing_registry_contract_fields():
    res = sp.run_health_probe("ka_dasha_kala", {"probe_type": "dasha_kala_proxy_integrity"})
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_dasha_kala_probe_rejects_duplicate_expected_systems():
    wrong = dict(_DASHA_KALA_SPEC, expected_systems=["vimshottari", "vimshottari"])
    res = sp.run_health_probe("ka_dasha_kala", wrong)
    assert res["status"] == "down"
    assert _check(res, "probe_config_valid")["passed"] is False


def test_tulana_probe_detects_a_broken_composite_formula(monkeypatch):
    """The 'un-floor' contract for this probe: if the I-11 weighted-sum
    formula ever regressed to an unweighted average (or any other wrong
    formula), the pinned composite scores would stop matching — this proves
    the check actually re-derives the math rather than trusting whatever
    rank_windows() returns."""
    import services.ka_tulana.ranker as ranker_module

    def broken_composite(w, reference_date):
        # Unweighted average instead of the real I-11 weighted sum.
        fb = ranker_module._composite(w, reference_date)
        n = 4
        avg = (fb.convergence_score + fb.rarity_norm + fb.confidence_score + fb.proximity_factor) / n
        return ranker_module.FactorBreakdown(
            convergence_score=fb.convergence_score, rarity_norm=fb.rarity_norm,
            confidence_score=fb.confidence_score, proximity_factor=fb.proximity_factor,
            composite=round(avg, 4),
        )

    monkeypatch.setattr(ranker_module, "_composite", broken_composite)
    res = sp.run_health_probe("ka_tulana", _TULANA_SPEC)
    assert res["status"] != "GREEN"
    assert _check(res, "forensic_composite_and_rank_order")["passed"] is False


def test_dasha_kala_probe_fails_on_a_missing_system():
    """CAN-FAIL proof: dropping one of the 7 documented systems from the
    expected set must not be swallowed."""
    six_only = [s for s in _DASHA_KALA_SPEC["expected_systems"] if s != "kalachakra"]
    wrong = dict(_DASHA_KALA_SPEC, expected_systems=six_only)
    res = sp.run_health_probe("ka_dasha_kala", wrong)
    assert res["status"] != "GREEN"
    check = _check(res, "seven_system_constant_set_intact")
    assert check["passed"] is False
    assert "kalachakra" in check["actual_systems"]


def test_dasha_kala_probe_fails_on_an_extra_system(monkeypatch):
    """CAN-FAIL proof: an 8th, undocumented system silently added to the
    LIVE constant set must be caught, not tolerated as 'at least these 7'
    (an exact-set match, not a subset check)."""
    import services.ka_dasha_kala.tree_walk as tree_walk_module

    with_extra = frozenset(tree_walk_module.ALL_DASHA_SYSTEMS) | {"an_undocumented_8th_system"}
    monkeypatch.setattr(tree_walk_module, "ALL_DASHA_SYSTEMS", with_extra)
    res = sp.run_health_probe("ka_dasha_kala", _DASHA_KALA_SPEC)
    assert res["status"] != "GREEN"
    check = _check(res, "seven_system_constant_set_intact")
    assert check["passed"] is False
    assert "an_undocumented_8th_system" in check["actual_systems"]


def test_dasha_kala_probe_detects_a_renamed_system(monkeypatch):
    """The 'un-floor' contract for this probe: if one of the 7 canonical
    system names were ever silently renamed in tree_walk.py, this must be
    caught rather than the probe reporting GREEN on an accidental 7-out-of-7
    count that no longer matches the documented set."""
    import services.ka_dasha_kala.tree_walk as tree_walk_module

    renamed = frozenset(
        {"vimshottari_v2" if s == "vimshottari" else s for s in tree_walk_module.ALL_DASHA_SYSTEMS}
    )
    monkeypatch.setattr(tree_walk_module, "ALL_DASHA_SYSTEMS", renamed)
    res = sp.run_health_probe("ka_dasha_kala", _DASHA_KALA_SPEC)
    assert res["status"] != "GREEN"
    assert _check(res, "seven_system_constant_set_intact")["passed"] is False
