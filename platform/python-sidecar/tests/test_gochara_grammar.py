"""
tests/test_gochara_grammar.py — D-5 Lane G-2 "Configuration grammar" tests.

No DATABASE_URL is set in this sandbox (confirmed at implementation time via
`python3 -c "import os; print('DATABASE_URL' in os.environ)"` -> False), so
every test here runs off either (a) real swisseph ephemeris computation
(`import swisseph as swe` -- confirmed importable, no DB required, same as
`tests/l3/test_transit_search_cache.py`) combined with hand-built
`ResonanceTarget` fixtures, or (b) the primitives' own documented fixture-
injection paths (`fixture_gate_rows`, `fixture_vedha_rows`, `fixture_phases`)
for the two families that need `bg_transit_av_gates` / `bg_transit_rules` /
`chart_facts` rows this sandbox cannot reach live.

Every ResonanceTarget/target anchor used below is EXPLICITLY a synthetic
fixture -- see each test's docstring/comments for how the anchor longitude
was derived (usually: read the real ephemeris position at a chosen jd via
swe directly, then feed that exact value back in as the target so the
primitive is guaranteed to find a contact near that jd -- this proves the
primitive's search machinery works correctly, it does not claim the
longitude is chart 482012f1's real natal position for that target).
"""
from __future__ import annotations

import swisseph as swe
import pytest

from pipeline.transit_search import clear_ephemeris_cache, _get_planet_pos, SIGNS, NAKSHATRAS
from services.gochara_grammar.models import (
    ResonanceTarget,
    ConfigurationSentence,
    CompositionSentence,
    CitationDisciplineError,
)
from services.gochara_grammar import primitives as P
from services.gochara_grammar import composition as CO
from services.gochara_grammar import sarvatobhadra as SBC
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD

CHART_ID = RM.CANONICAL_CHART_ID


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


def _jd(y, m, d, h=0.0):
    return swe.julday(y, m, d, h)


def _target_at_planet_position(
    planet: str, y: int, m: int, d: int, event_class: str = "marriage",
    target_type: str = "karaka", target_ref: str = "test_target",
    citation: str = "TEST FIXTURE — see test module docstring",
    natal_planet: str | None = None,
) -> ResonanceTarget:
    """Build a ResonanceTarget whose target_longitude_deg is EXACTLY where
    `planet` sits at (y, m, d) 00:00 UT -- guarantees the degree-contact-style
    primitives find a real crossing near that date without hardcoding a
    memorized ephemeris value."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd0 = _jd(y, m, d)
    lon, _ = _get_planet_pos(swe, planet, jd0)
    sign = SIGNS[int(lon // 30.0) % 12]
    nak_id = int(lon / (360.0 / 27.0)) % 27 + 1
    return ResonanceTarget(
        chart_id=CHART_ID,
        event_class=event_class,
        target_type=target_type,
        target_ref=target_ref,
        weight=0.8,
        classical_citation=citation,
        target_longitude_deg=lon,
        target_sign=sign,
        target_nakshatra_id=nak_id,
        natal_planet=natal_planet,
    )


# ── models.py citation discipline invariant ─────────────────────────────────

def test_sentence_requires_citation_or_uncited_extension():
    with pytest.raises(CitationDisciplineError):
        ConfigurationSentence(
            primitive="x", chart_id=CHART_ID, event_class="marriage", target_type="bhava",
            target_ref="7", transit_planet="Saturn", secondary_planet=None,
            event_jd=1.0, event_datetime_ist="2020-01-01T00:00:00",
            temporal_shape="point",
            # neither classical_citation nor uncited_extension set
        )


def test_sentence_rejects_both_citation_and_uncited_extension():
    with pytest.raises(CitationDisciplineError):
        ConfigurationSentence(
            primitive="x", chart_id=CHART_ID, event_class="marriage", target_type="bhava",
            target_ref="7", transit_planet="Saturn", secondary_planet=None,
            event_jd=1.0, event_datetime_ist="2020-01-01T00:00:00",
            temporal_shape="point",
            classical_citation="BPHS Ch.29", uncited_extension=True,
        )


def test_sentence_valid_with_citation_only():
    s = ConfigurationSentence(
        primitive="x", chart_id=CHART_ID, event_class="marriage", target_type="bhava",
        target_ref="7", transit_planet="Saturn", secondary_planet=None,
        event_jd=1.0, event_datetime_ist="2020-01-01T00:00:00",
        temporal_shape="point", classical_citation="BPHS Ch.29",
    )
    assert s.classical_citation == "BPHS Ch.29"


def test_sentence_valid_with_uncited_extension_only():
    s = ConfigurationSentence(
        primitive="x", chart_id=CHART_ID, event_class="marriage", target_type="bhava",
        target_ref="7", transit_planet="Saturn", secondary_planet=None,
        event_jd=1.0, event_datetime_ist="2020-01-01T00:00:00",
        temporal_shape="point", uncited_extension=True,
    )
    assert s.uncited_extension is True


def test_resonance_target_requires_citation_discipline_too():
    with pytest.raises(CitationDisciplineError):
        ResonanceTarget(
            chart_id=CHART_ID, event_class="marriage", target_type="bhava",
            target_ref="7", weight=0.5,
        )


# ── resonance_map fixture builder ───────────────────────────────────────────

def test_fixture_targets_are_realistic_and_schema_conformant():
    targets = RM.build_fixture_targets(CHART_ID)
    assert len(targets) >= 3
    for t in targets:
        assert t.chart_id == CHART_ID
        assert t.target_type in (
            "bhava", "lord", "karaka", "mechanism_node", "sensitive_degree",
            "arudha", "yoga_constituent", "dasha_lord_portfolio",
        )
        # citation discipline held at construction time already (ResonanceTarget.__post_init__)


# ── 12 contact-primitive families: each must produce >=1 real sentence ─────

WINDOW_YEARS = 2  # generous window around the anchor date to allow for orb search

def _window(y, m, d):
    return _jd(y - WINDOW_YEARS, 1, 1), _jd(y + WINDOW_YEARS, 12, 31)


def test_primitive_1_degree_contact():
    target = _target_at_planet_position("Jupiter", 2015, 6, 1)
    start_jd, end_jd = _window(2015, 6, 1)
    sentences = P.degree_contact(swe, CHART_ID, target, start_jd, end_jd, planets=["Jupiter"], orb_deg=2.0)
    assert len(sentences) >= 1
    s = sentences[0]
    assert s.primitive == "degree_contact"
    assert s.uncited_extension is True and s.classical_citation is None


def test_primitive_2_drishti_contact():
    # Saturn's 3rd/7th/10th special aspects -- pick a target degree 180deg
    # away from Saturn's actual 2015-01-01 position so the 7th-aspect fires.
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd0 = _jd(2015, 1, 1)
    sat_lon, _ = _get_planet_pos(swe, "Saturn", jd0)
    target_lon = (sat_lon + 180.0) % 360.0
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="bhava",
        target_ref="test", weight=0.7, classical_citation="TEST FIXTURE",
        target_longitude_deg=target_lon, target_sign=SIGNS[int(target_lon // 30) % 12],
    )
    start_jd, end_jd = _window(2015, 1, 1)
    sentences = P.drishti_contact(swe, CHART_ID, target, start_jd, end_jd, planets=["Saturn"], orb_deg=3.0)
    assert len(sentences) >= 1
    assert sentences[0].classical_citation is not None
    assert sentences[0].uncited_extension is False


def test_primitive_3_sign_ingress():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="bhava",
        target_ref="10", weight=0.8, classical_citation="TEST FIXTURE",
        target_sign="Capricorn",
    )
    start_jd, end_jd = _jd(2018, 1, 1), _jd(2022, 1, 1)
    sentences = P.sign_ingress(swe, CHART_ID, target, start_jd, end_jd, planets=["Jupiter", "Saturn"])
    assert len(sentences) >= 1
    assert all(s.classical_citation for s in sentences)


def test_primitive_4_nakshatra_ingress_tara():
    target = _target_at_planet_position("Moon", 2020, 3, 1)
    start_jd, end_jd = _jd(2020, 1, 1), _jd(2020, 6, 1)
    sentences = P.nakshatra_ingress_tara(
        swe, CHART_ID, target, start_jd, end_jd, natal_moon_nakshatra_id=25, planets=["Moon"],
    )
    assert len(sentences) >= 1
    s = sentences[0]
    assert "tara" in s.detail
    assert s.classical_citation is not None


def test_primitive_5_kakshya_cell_crossing_fallback_fixture():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="2", weight=0.6, classical_citation="TEST FIXTURE",
        target_sign="Taurus",
    )
    start_jd, end_jd = _jd(2019, 1, 1), _jd(2021, 1, 1)
    sentences = P.kakshya_cell_crossing(swe, CHART_ID, target, start_jd, end_jd, conn=None, planets=["Moon"])
    assert len(sentences) >= 1
    # conn=None -> fallback path -> honestly uncited
    assert sentences[0].uncited_extension is True
    assert sentences[0].detail["source"] == "equal_eighths_fixture_approximation"


def test_primitive_6_av_threshold_state_fixture_gate():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="11", weight=0.75, classical_citation="TEST FIXTURE",
        target_sign="Pisces",
    )
    start_jd, end_jd = _jd(2019, 1, 1), _jd(2023, 6, 1)
    fixture_gate = [{"graha": "jupiter", "min_sav_score": 28, "effect": "gain amplified",
                      "classical_citation": "Phaladeepika ch.26 §double-gochara"}]
    sentences = P.av_threshold_state(
        swe, CHART_ID, target, start_jd, end_jd, conn=None, fixture_gate_rows=fixture_gate,
    )
    assert len(sentences) >= 1
    assert sentences[0].classical_citation is not None
    assert sentences[0].detail["bindu_count_resolved"] is False


class _FakeCursor:
    """Minimal stand-in for a psycopg cursor -- just needs .fetchall()."""
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _PoisonableConn:
    """Reproduces, WITHOUT a real DB, the exact connection-hygiene hazard the
    live D-5 G-4 incident hit (job brahma-build-pipeline-job-kb4zr,
    2026-07-19T16:29:37Z): `av_threshold_state`'s `_fetch_av_gate_rows` issued
    a genuinely bad query against `bg_transit_av_gates` (an untyped bare
    `%s IS NULL` placeholder -> psycopg `IndeterminateDatatype`), which on a
    real (non-autocommit) Postgres connection leaves the WHOLE transaction in
    "aborted" state -- every later query on that same connection then fails
    with the generic "current transaction is aborted, commands ignored until
    end of transaction block", even for a totally unrelated, individually
    correct query (`kakshya_cell_crossing`'s `chart_facts` read, in the real
    incident).

    This fake models that exact mechanic: `.execute()` on the `bg_transit_av_gates`
    query always raises (the "root cause" query), which sets `poisoned=True`;
    every subsequent `.execute()` call raises the generic aborted-transaction
    error WHILE `poisoned` is still True; `.rollback()` clears it. This lets a
    test assert, without any live DB, that the connection self-heals (the
    fix's `safe_rollback` call inside each primitive's own except block) and a
    later, unrelated primitive is NOT starved of its own honest DB read by an
    earlier primitive's unrelated bug."""

    def __init__(self):
        self.poisoned = False
        self.rollback_called = 0
        self.autocommit = False

    def execute(self, sql, params=None):
        if self.poisoned:
            raise RuntimeError(
                "current transaction is aborted, commands ignored until end of transaction block"
            )
        if "bg_transit_av_gates" in sql:
            self.poisoned = True
            raise RuntimeError("could not determine data type of parameter $1")
        if "ashtakavarga_kakshya_boundary" in sql:
            # Real DB-backed boundary rows -- only reachable if this call was
            # NOT starved by the earlier bg_transit_av_gates failure.
            return _FakeCursor([
                {"fact_subject": "Moon.0", "fact_key": "start_deg", "fact_value_text": None, "fact_value_num": 30.0},
                {"fact_subject": "Moon.0", "fact_key": "lord", "fact_value_text": "Saturn", "fact_value_num": None},
            ])
        return _FakeCursor([])

    def rollback(self):
        self.rollback_called += 1
        self.poisoned = False


def test_bad_query_does_not_poison_subsequent_query_on_same_connection():
    """Regression test for the D-5 G-4 live incident (job
    brahma-build-pipeline-job-kb4zr, chart 482012f1, 2026-07-19T16:29:37Z):
    `av_threshold_state`'s DB read genuinely fails (bad SQL against
    `bg_transit_av_gates`) and must degrade to an honest [] AND self-heal the
    shared connection (via `safe_rollback`) rather than leaving it poisoned
    for whatever primitive runs next on the same `conn` -- exactly the shape
    `ka_gochara_sweep.sweep` shares one connection across many primitive
    calls per grid point."""
    conn = _PoisonableConn()

    av_target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="11", weight=0.75, classical_citation="TEST FIXTURE",
        target_sign="Pisces",
    )
    start_jd, end_jd = _jd(2019, 1, 1), _jd(2023, 6, 1)

    # 1) The bad query. Must degrade honestly (empty, not a crash) AND reset
    #    the connection's transaction state -- not just log-and-return.
    sentences = P.av_threshold_state(swe, CHART_ID, av_target, start_jd, end_jd, conn=conn)
    assert sentences == []
    assert conn.rollback_called == 1, (
        "av_threshold_state's except block must call safe_rollback so a bad "
        "query doesn't poison the connection for the next primitive."
    )
    assert conn.poisoned is False

    # 2) A SUBSEQUENT, unrelated primitive on the SAME connection -- the exact
    #    cascade the live incident hit (kakshya_cell_crossing's independently
    #    correct chart_facts read failing only because of the EARLIER
    #    av_threshold_state failure). If the connection were still poisoned,
    #    this call's `conn.execute` would raise the generic aborted-transaction
    #    error and the primitive would silently fall back to the uncited
    #    equal-eighths fixture -- masking the fact that real DB data existed.
    kakshya_target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="2", weight=0.6, classical_citation="TEST FIXTURE",
        target_sign="Taurus",
    )
    kakshya_sentences = P.kakshya_cell_crossing(
        swe, CHART_ID, kakshya_target, start_jd, end_jd, conn=conn, planets=["Moon"],
    )
    assert len(kakshya_sentences) >= 1
    s = kakshya_sentences[0]
    assert s.uncited_extension is False, (
        "kakshya_cell_crossing should have reached its REAL chart_facts boundary "
        "read on this call -- if it fell back to the uncited fixture, the "
        "connection was still poisoned from the earlier av_threshold_state failure."
    )
    assert s.detail["source"] == "chart_facts.ashtakavarga_kakshya_boundary"


def test_primitive_7_gochara_vedha_pair_cancellation_check():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="bhava",
        target_ref="10", weight=0.8, classical_citation="TEST FIXTURE",
        target_sign="Capricorn",
    )
    start_jd, end_jd = _jd(2018, 1, 1), _jd(2022, 1, 1)
    fixture_vedha = [{"graha": "saturn", "vedha_house": 4, "phala": "test phala",
                       "classical_citation": "Phaladeepika Ch.26 — Gochara Vedha"}]
    sentences = P.gochara_vedha_pair(
        swe, CHART_ID, target, start_jd, end_jd, conn=None, fixture_vedha_rows=fixture_vedha,
    )
    assert len(sentences) >= 1
    s = sentences[0]
    assert s.classical_citation is not None
    assert "cancelled" in s.detail  # cancellation check ran (True or False)


def test_primitive_8_sarvatobhadra_vedha():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="marriage", target_type="karaka",
        target_ref="Moon_natal", weight=0.9, classical_citation="TEST FIXTURE",
        target_nakshatra_id=25,  # Purva Bhadrapada -- FORENSIC natal Moon nakshatra
    )
    start_jd, end_jd = _jd(2024, 1, 1), _jd(2026, 12, 31)
    sentences = SBC.find_sarvatobhadra_vedha_states(
        swe, CHART_ID, target, start_jd, end_jd, transit_planets=["Saturn", "Jupiter", "Rahu", "Ketu"],
    )
    assert len(sentences) >= 1
    s = sentences[0]
    assert s.temporal_shape == "interval"
    assert s.uncited_extension is True and s.classical_citation is None
    assert s.detail["vedha_pair_source"] == "algorithmic_opposition_approximation"


def test_primitive_9_station_retro_loop():
    # Mars retrogrades roughly every ~2 years; scan a wide window and target
    # near wherever a station actually lands so the near_orb_deg check passes.
    start_jd, end_jd = _jd(2018, 1, 1), _jd(2020, 12, 31)
    from pipeline.transit_search import find_station_events
    stations = find_station_events(swe, "Mars", start_jd, end_jd)
    assert len(stations) >= 1, "expected >=1 Mars station in this 3-year window"
    anchor = stations[0]
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="bhava",
        target_ref="test", weight=0.7, classical_citation="TEST FIXTURE",
        target_longitude_deg=anchor.exact_longitude_deg,
    )
    sentences = P.station_retro_loop(swe, CHART_ID, target, start_jd, end_jd, planets=["Mars"], near_orb_deg=2.0)
    assert len(sentences) >= 1
    assert sentences[0].classical_citation is not None


def test_primitive_10_eclipse_degree():
    # Rahu/Sun conjunction (eclipse-proximity) exists reliably within any
    # ~18-year Rahu cycle window; use a wide scan and target that exact degree.
    start_jd, end_jd = _jd(2015, 1, 1), _jd(2020, 1, 1)
    from pipeline.transit_search import find_eclipse_proximity_events
    conjs = find_eclipse_proximity_events(swe, "Rahu", "Sun", 2.0, start_jd, end_jd)
    assert len(conjs) >= 1, "expected >=1 Rahu-Sun eclipse-proximity conjunction in this window"
    anchor = conjs[0]
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="major_loss", target_type="sensitive_degree",
        target_ref="test", weight=0.6, classical_citation="TEST FIXTURE",
        target_longitude_deg=anchor.exact_longitude_deg,
    )
    sentences = P.eclipse_degree(swe, CHART_ID, target, start_jd, end_jd, orb_deg=3.0,
                                  node_luminary_pairs=[("Rahu", "Sun")])
    assert len(sentences) >= 1
    assert sentences[0].uncited_extension is True


def test_primitive_11_planetary_return():
    target = _target_at_planet_position("Jupiter", 2010, 1, 1, natal_planet="Jupiter")
    start_jd, end_jd = _jd(2008, 1, 1), _jd(2012, 1, 1)  # Jupiter's ~12yr period; not guaranteed a full return in 4yr, so widen
    start_jd, end_jd = _jd(2000, 1, 1), _jd(2024, 1, 1)
    sentences = P.planetary_return(swe, CHART_ID, target, start_jd, end_jd, orb_deg=1.5)
    assert len(sentences) >= 1
    assert sentences[0].uncited_extension is True


def test_primitive_12_sade_sati_phase_fixture():
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="psychological_arc", target_type="bhava",
        target_ref="12", weight=0.65, classical_citation="TEST FIXTURE",
    )
    fixture_phases = [
        {"cycle_id": "SS1", "phase_name": "JANMA", "phase_start_iso": "2003-06-01T00:00:00+00:00",
         "phase_end_iso": "2005-08-01T00:00:00+00:00"},
    ]
    sentences = P.sade_sati_phase(CHART_ID, target, conn=None, fixture_phases=fixture_phases)
    assert len(sentences) == 1
    assert sentences[0].classical_citation is not None
    assert sentences[0].temporal_shape == "interval"


# ── DB reachability probe (documents the live-DB attempt, does not fail if absent) ─

def test_db_reachability_probe_and_sarvatobhadra_2025_05_live_attempt():
    """
    Attempts a live DB connection (DATABASE_URL) to (a) confirm whether this
    sandbox can reach the real chart_facts / l1_sarvatobhadra_vedha data for
    chart 482012f1, and (b) if so, run the Sarvatobhadra primitive live
    against the 2025-05 window (the wave's named specimen). If unreachable,
    this test PASSES with an explicit skip reason instead of failing --
    per the task brief: "if you cannot reach the DB ... say so plainly and
    note it as a live-integration-time check instead of faking a result."
    """
    import os
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        pytest.skip(
            "DATABASE_URL not set in this sandbox -- live DB reachability and the "
            "2025-05 Sarvatobhadra specimen against real chart 482012f1 data are "
            "confirmed NOT reachable from this environment. This is a documented "
            "live-integration-time check (G-3/G-4/gate time), not faked here."
        )
    try:
        import psycopg
        conn = psycopg.connect(db_url, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"DATABASE_URL set but connection failed: {exc}")
        return

    try:
        target = ResonanceTarget(
            chart_id=CHART_ID, event_class="marriage", target_type="karaka",
            target_ref="Moon_natal", weight=0.9, classical_citation="LIVE DB PROBE",
            target_nakshatra_id=25,
        )
        start_jd, end_jd = _jd(2025, 4, 1), _jd(2025, 6, 30)
        sentences = SBC.find_sarvatobhadra_vedha_states(
            swe, CHART_ID, target, start_jd, end_jd, conn=conn,
        )
        print(f"[LIVE DB] Sarvatobhadra 2025-05 specimen: {len(sentences)} vedha-state sentence(s) found.")
        assert isinstance(sentences, list)
    finally:
        conn.close()


# ── 6 composition operators: each must fire on >=1 constructed scenario ────

def _mk_sentence(primitive, target_ref, event_jd, transit_planet, chart_id=CHART_ID,
                  citation="TEST FIXTURE", uncited=False, detail=None, temporal_shape="point",
                  event_dt="2013-12-11T00:00:00+05:30"):
    return ConfigurationSentence(
        primitive=primitive, chart_id=chart_id, event_class="marriage", target_type="karaka",
        target_ref=target_ref, transit_planet=transit_planet, secondary_planet=None,
        event_jd=event_jd, event_datetime_ist=event_dt, temporal_shape=temporal_shape,
        fact_ids=[f"fixture:{primitive}:{transit_planet}:{event_jd}"],
        classical_citation=None if uncited else citation, uncited_extension=uncited,
        detail=detail or {},
    )


def test_composition_1_simultaneity():
    sentences = [
        _mk_sentence("degree_contact", "venus_natal", 2456637.5, "Jupiter", uncited=True),
        _mk_sentence("sign_ingress", "venus_natal", 2456637.7, "Saturn"),
    ]
    out = CO.simultaneity(sentences, window_days=1.0)
    assert len(out) >= 1
    assert out[0].operator == "simultaneity"
    assert out[0].uncited_extension is True


def test_composition_2_double_transit_marriage_specimen():
    """
    The wave's named double-transit specimen: two grahas' drishti/contact on
    one natal target simultaneously, near 2013-12-11 (chart 482012f1's
    marriage event per BRIEF_D5 §2). event_jd/event_dt below are pinned to
    2013-12-11 exactly (jd 2456637.5 = swe.julday(2013,12,11,0.0), confirmed
    via `python3 -c "import swisseph as swe; print(swe.julday(2013,12,11,0.0))"`
    at implementation time) -- the member sentences are hand-built
    ConfigurationSentence fixtures (two different grahas contacting the same
    target_ref on that date), demonstrating the OPERATOR's pairing/detection
    logic. This is NOT a live re-derivation against chart 482012f1's real
    natal Venus/7th-lord degree (no DB reachable in this sandbox -- see
    test_db_reachability_probe_and_sarvatobhadra_2025_05_live_attempt) --
    that live re-derivation is a G-3/G-4/gate-time integration check.
    """
    jd_marriage = swe.julday(2013, 12, 11, 0.0)
    sentences = [
        _mk_sentence("drishti_contact", "venus_natal", jd_marriage, "Jupiter",
                     detail={"signed_offset_from_target_deg": 2.1}),
        _mk_sentence("drishti_contact", "venus_natal", jd_marriage + 0.3, "Saturn",
                     detail={"signed_offset_from_target_deg": -1.4}),
    ]
    out = CO.double_transit(sentences, window_days=1.0)
    assert len(out) >= 1
    pair_planets = {out[0].detail["planet_a"], out[0].detail["planet_b"]}
    assert pair_planets == {"Jupiter", "Saturn"}
    # Jupiter+Saturn pairing -> the one double-transit combination this
    # codebase has a live cited bg_transit_rules row for (migration 397).
    assert out[0].uncited_extension is False
    assert out[0].classical_citation is not None


def test_composition_3_kartari():
    sentences = [
        _mk_sentence("degree_contact", "t1", 100.0, "Mars", uncited=True,
                     detail={"signed_offset_from_target_deg": 3.0}),
        _mk_sentence("degree_contact", "t1", 100.2, "Venus", uncited=True,
                     detail={"signed_offset_from_target_deg": -2.5}),
    ]
    out = CO.kartari(sentences, window_days=1.0)
    assert len(out) >= 1
    assert out[0].operator == "kartari"
    assert out[0].uncited_extension is True


def test_composition_4_cancellation():
    vedha_sentence = ConfigurationSentence(
        primitive="gochara_vedha_pair", chart_id=CHART_ID, event_class="career_advancement",
        target_type="bhava", target_ref="10", transit_planet="Saturn", secondary_planet="Mars",
        event_jd=100.0, event_datetime_ist="2020-01-01T00:00:00",
        temporal_shape="interval", classical_citation="Phaladeepika Ch.26 — Gochara Vedha",
        detail={"cancelled": True, "cancelling_occupants": ["Mars"], "vedha_house": 4},
    )
    out = CO.cancellation([vedha_sentence])
    assert len(out) == 1
    assert out[0].classical_citation == vedha_sentence.classical_citation
    assert out[0].detail["cancelled"] is True


def test_composition_5_amplification():
    sentences = [
        _mk_sentence("degree_contact", "t2", 200.0, "Jupiter", uncited=True),
        _mk_sentence("drishti_contact", "t2", 200.1, "Venus"),
        _mk_sentence("sign_ingress", "t2", 200.3, "Mercury"),
    ]
    out = CO.amplification(sentences, window_days=1.0, min_stack=3)
    assert len(out) >= 1
    assert out[0].detail["stack_count"] == 3


def test_composition_6_dasha_coincidence():
    sentences = [_mk_sentence("degree_contact", "t3", 2456637.5, "Venus", uncited=True,
                               event_dt="2013-12-11T00:00:00+00:00")]
    periods = DD.build_fixture_dasha_periods(CHART_ID)
    out = CO.dasha_coincidence(sentences, periods, require_systems=2)
    assert len(out) >= 1
    assert out[0].detail["system_count"] >= 2
    assert set(out[0].detail["systems_coinciding"]) <= {"vimshottari", "yogini"}
    assert out[0].uncited_extension is True


# ── Citation-or-uncited-extension invariant across a full realistic run ────

def test_citation_invariant_holds_across_all_primitives_and_compositions():
    """Aggregate check: run every primitive + composition over a shared
    fixture scenario and assert EVERY emitted sentence satisfies the B.10
    citation-or-uncited-extension invariant (this is also mechanically
    enforced at construction time by models.py, but this test additionally
    proves no primitive/operator silently swallows an exception that would
    hide a would-be violation)."""
    all_sentences: list[ConfigurationSentence] = []

    target_bhava = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="bhava",
        target_ref="10", weight=0.8, classical_citation="TEST FIXTURE", target_sign="Capricorn",
    )
    start_jd, end_jd = _jd(2018, 1, 1), _jd(2022, 1, 1)

    all_sentences += P.sign_ingress(swe, CHART_ID, target_bhava, start_jd, end_jd, planets=["Jupiter", "Saturn"])
    all_sentences += P.gochara_vedha_pair(
        swe, CHART_ID, target_bhava, start_jd, end_jd, conn=None,
        fixture_vedha_rows=[{"graha": "saturn", "vedha_house": 4, "phala": "x",
                              "classical_citation": "Phaladeepika Ch.26 — Gochara Vedha"}],
    )
    all_sentences += P.kakshya_cell_crossing(swe, CHART_ID, target_bhava, start_jd, end_jd, conn=None, planets=["Moon"])

    assert len(all_sentences) >= 3
    for s in all_sentences:
        has_citation = bool(s.classical_citation)
        has_uncited = bool(s.uncited_extension)
        assert has_citation != has_uncited or (has_citation and not has_uncited) or (has_uncited and not has_citation), \
            f"sentence {s.primitive}/{s.target_ref} violates citation-or-uncited invariant"
        assert has_citation or has_uncited, f"sentence {s.primitive}/{s.target_ref} has NEITHER citation nor uncited flag"
        assert not (has_citation and has_uncited), f"sentence {s.primitive}/{s.target_ref} has BOTH citation and uncited flag"

    composed = CO.simultaneity(all_sentences, window_days=3650.0, min_primitives=2)
    for c in composed:
        assert bool(c.classical_citation) != bool(c.uncited_extension) or bool(c.uncited_extension)
        assert bool(c.classical_citation) or bool(c.uncited_extension)
