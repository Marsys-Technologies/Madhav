"""Behavioral replacement-safety contracts for W2 writers and inert KA-3a dispatch."""
from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED

import pipeline.orchestrator.writers.ka_avadhi as avadhi
import pipeline.orchestrator.writers.ka_yojaka as yojaka
import services.ka_gochara_resonance.writer as resonance
import services.ka_kota_chakra.writer as kota
import services.ka_moorti_nirnaya.writer as moorti
import services.ka_sudarshana_varsha.writer as sudarshana
import services.ka_tithi_pravesha.writer as tithi
import services.ka_vedha_gochara.writer as vedha


class RecordingCursor:
    def __init__(self, conn: "RecordingConnection") -> None:
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.conn.calls.append(("execute", str(sql), params))

    def executemany(self, sql, params):
        self.conn.calls.append(("executemany", str(sql), list(params)))

    def fetchall(self):
        return self.conn.results.pop(0) if self.conn.results else []

    def fetchone(self):
        return self.conn.results.pop(0) if self.conn.results else None


class RecordingConnection:
    def __init__(self, results=None) -> None:
        self.results = list(results or [])
        self.calls: list[tuple[str, str, object]] = []

    def cursor(self, *_args, **_kwargs):
        return RecordingCursor(self)

    @property
    def mutations(self):
        return [
            call for call in self.calls
            if call[0] == "executemany"
            or call[1].lstrip().upper().startswith(("DELETE", "INSERT", "UPDATE"))
        ]


# a decorated (@records_swiss_backend) per-chart writer needs a checkable birth window (finding 3)
_BIRTH = {"datetime_iso": "1984-02-05T10:43:00+05:30"}


def _ctx(conn, *, birth_params=None):
    config = {"chart_id": "chart-1"}
    if birth_params is not None:
        config["birth_params"] = birth_params
    return SimpleNamespace(db_conn=conn, config=config, dry_run=False)


def _daily(start: date, end: date, value=0.0):
    return [
        (start + timedelta(days=offset), value)
        for offset in range((end - start).days + 1)
    ]


def _run(harness):
    conn, writer = harness()
    result = writer.run(_ctx(conn))
    return conn, result


def test_gochara_requires_every_event_class_before_replacement(monkeypatch):
    conn = RecordingConnection()
    first = resonance.TARGET_EVENT_CLASSES[0]
    monkeypatch.setattr(
        resonance,
        "_fetch_event_class_rows",
        lambda _conn, _chart, event, **_kw: [{"event_class_id": event}] if event == first else [],
    )

    result = resonance.KaGocharaResonanceWriter().run(_ctx(conn))

    assert result.rows_inserted == 0
    assert "incomplete event-class coverage" in result.notes
    assert conn.mutations == []


def test_gochara_replaces_only_after_all_event_classes_are_ready(monkeypatch):
    conn = RecordingConnection()
    def _stub_rows(_conn, _chart, event, report=None, **_kw):
        if report is not None:
            report.setdefault("sensitive_degree", {"kept": 0, "dropped_negative": 0,
                                                   "dropped_unknown_value": 0,
                                                   "kept_subjects": set()})
            report.setdefault("arudha", {"rows": 0, "invalid_sign_value": 0})
            report.setdefault("bhava_arudha", {"rows": 0, "unavailable": 0})
            report.setdefault("yoga_constituent", {"validated_ids": set(), "constituents": {}})
            report.setdefault("roots", {"discarded": 0, "details": []})
        return [{"event_class_id": event, "target_type": "sensitive_degree",
                 "target_ref": "ABHIJIT"}]

    monkeypatch.setattr(resonance, "_fetch_event_class_rows", _stub_rows)

    result = resonance.KaGocharaResonanceWriter().run(_ctx(conn))

    # One stub row per event class, plus the M-6 derived rows the writer
    # always emits (honest state, never dropped) for the M-6 classes
    # present in TARGET_EVENT_CLASSES: 1 gulika_mandi_distance + 4
    # yamakantaka_difference per M-6 class.
    m6_classes_present = [c for c in resonance.TARGET_EVENT_CLASSES
                          if c in resonance.M6_EVENT_CLASSES]
    expected = len(resonance.TARGET_EVENT_CLASSES) + 5 * len(m6_classes_present)
    assert result.rows_inserted == expected
    assert [call[0] for call in conn.mutations] == ["execute", "executemany"]
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE")


def _patch_daily_writer_dependencies(monkeypatch, module, daily_by_body):
    if module is kota:
        monkeypatch.setattr(module, "_fetch_janma_nakshatra_idx", lambda *_: (0, "fact-1"))
        monkeypatch.setattr(module, "_fetch_ring_assignments", lambda *_: ({}, "citation"))
        monkeypatch.setattr(module, "_fetch_daily_nak_idx_by_graha", lambda *_: daily_by_body)
    elif module is moorti:
        monkeypatch.setattr(module, "_fetch_janma_nakshatra_idx", lambda *_: (0, "fact-1"))
        monkeypatch.setattr(
            module,
            "_fetch_moorti_table",
            lambda *_: {1: {"moorti_name": "gold", "quality_tier": "high", "phala_brief": "fixture", "classical_citation": "fixture"}},
        )
        monkeypatch.setattr(module, "_fetch_daily_sidereal_by_body", lambda *_: daily_by_body)
        # This fixture is a constant 0.0° series (every body on the Aries seam
        # every day) — not a motion Swiss can ever bracket. These tests assert
        # delete/insert ORDERING, not the kernel solver; the writer used to pass
        # here only because a blanket `except Exception` turned the kernel's
        # "lost its bracket" error into silently-unrefined roots (A5.4 removed
        # that swallow). The kernel solver is covered in
        # test_ka_moorti_nirnaya_writer.py::TestIngressSolverMethodRecorded.
        monkeypatch.setattr(module, "KERNEL_INSTANT_GRADING", False)
    if module is moorti:
        # P06 fingerprints read node-series and natal identities; the fake
        # connection here tests replacement ordering, not the digest SQL.
        monkeypatch.setattr(
            module, "node_series_identity",
            lambda conn: {"mode": "true", "n_rows": 2, "digest": "d" * 64})
        monkeypatch.setattr(
            module, "l1_operand_identity",
            lambda conn, cid, ay, ops: {"operands": [], "digest": "e" * 64})
    monkeypatch.setattr(module, "_compute_ayanamsha_offset", lambda *_: 0.0)


@pytest.mark.parametrize(
    ("module", "bodies", "writer_class"),
    [
        (kota, kota.ALL_GRAHAS, kota.KaKotaChakraWriter),
        (moorti, moorti.MOORTI_GRAHAS + ("Moon",), moorti.KaMoortiNirnayaWriter),
    ],
)
def test_daily_writers_reject_gaps_duplicates_and_truncation(
    monkeypatch, module, bodies, writer_class,
):
    today = date.today()
    start = today - timedelta(days=module.HORIZON_BACK_DAYS)
    end = today + timedelta(days=module.HORIZON_FORWARD_DAYS)
    complete = _daily(start, end)
    bad_series = {
        "missing": complete[:-1],
        "duplicate": complete[:-1] + [complete[-2]],
        "out_of_order": complete[:1] + list(reversed(complete[1:])),
    }
    for broken in bad_series.values():
        daily = {body: list(complete) for body in bodies}
        daily[bodies[0]] = broken
        _patch_daily_writer_dependencies(monkeypatch, module, daily)
        conn = RecordingConnection()

        result = writer_class().run(_ctx(conn))

        assert result.rows_inserted == 0
        assert "incomplete daily ephemeris coverage" in result.notes
        assert conn.mutations == []


@pytest.mark.parametrize(
    ("module", "bodies", "writer_class"),
    [
        (kota, kota.ALL_GRAHAS, kota.KaKotaChakraWriter),
        (moorti, moorti.MOORTI_GRAHAS + ("Moon",), moorti.KaMoortiNirnayaWriter),
    ],
)
def test_daily_writers_delete_only_after_complete_horizon(
    monkeypatch, module, bodies, writer_class,
):
    today = date.today()
    start = today - timedelta(days=module.HORIZON_BACK_DAYS)
    end = today + timedelta(days=module.HORIZON_FORWARD_DAYS)
    daily = {body: _daily(start, end) for body in bodies}
    _patch_daily_writer_dependencies(monkeypatch, module, daily)
    run = {
        "sign_idx": 0,
        "nakshatra_idx": 0,
        "start_date": start,
        "end_date": end,
        "start_truncated": False,
        "end_truncated": False,
    }
    if module is kota:
        monkeypatch.setattr(module, "detect_ring_runs", lambda *_args, **_kwargs: [run])
        monkeypatch.setattr(module, "count_from_janma", lambda *_: 1)
        monkeypatch.setattr(module, "ring_for_count", lambda *_: "STAMBHA")
        monkeypatch.setattr(
            module,
            "attack_defence_reading",
            lambda *_: {"is_natural_malefic": False, "posture": "defence", "severity": "low"},
        )
    else:
        monkeypatch.setattr(module, "detect_sign_runs", lambda *_args, **_kwargs: [run])
    conn = RecordingConnection()

    result = writer_class().run(_ctx(conn))

    assert result.rows_inserted > 0
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE")
    assert conn.mutations[-1][0] == "executemany"


@pytest.mark.parametrize("dry_run", [False, True])
def test_vedha_unbound_dispatch_preserves_legacy_rows(dry_run):
    # KA-3a replaced the rolling-day writer with an explicitly bound candidate
    # provider. Without a payload dispatch must not read or mutate legacy data.
    conn = RecordingConnection()
    ctx = _ctx(conn)
    ctx.dry_run = dry_run

    result = vedha.KaVedhaGocharaWriter().run(ctx)

    assert result.rows_inserted == 0
    assert "provider binding/activation pending" in result.notes
    assert conn.calls == []


def test_avadhi_preserves_published_rows_without_build_candidate():
    conn = RecordingConnection()
    result = avadhi.KaAvdhiWriter().run(_ctx(conn))

    assert result.asset_id == "ka_avadhi"
    assert result.rows_inserted == 0
    assert "published rows preserved" in result.notes
    assert conn.calls == []
    assert conn.mutations == []


@pytest.mark.parametrize(
    ("tier", "row_build", "error_type", "message"),
    [
        (TWO_PASS_VERIFIED, "f2-build", RuntimeError,
         "pinned chart_dashas row has a non-positive period"),
        ("L1", "f2-build", avadhi.clocks.ClockUnavailable, "tier_unavailable"),
        (TWO_PASS_VERIFIED, "other-build", avadhi.clocks.ClockUnavailable, "build_not_pinned"),
    ],
    ids=["invalid-period", "unsupported-tier-first", "wrong-build-first"],
)
def test_avadhi_preserves_candidate_if_pinned_period_is_invalid(tier, row_build, error_type, message, monkeypatch):
    # This oracle starts with F2 projection rows and exercises admission of
    # their tier/build/interval before output mutation, after settlement.
    from tests.l3._dasha_projection import emulated_projection
    monkeypatch.setattr(avadhi, "execute_governed_dasha_query", emulated_projection)
    pins = {
        "f2": {"build_id": "f2-build", "ayanamsha_id": "lahiri",
               "tier": tier, "systems": ["vimshottari"]},
        "natal": {"build_id": "natal-build", "ayanamsha_id": "lahiri", "tier": TWO_PASS_VERIFIED},
        "node_model": "mean",
    }
    invalid = {"system_id": "vimshottari", "level_n": 1,
               "dasha_row_id": "period-1", "start_iso": "2027-01-01T00:00:00Z",
               "end_iso": "2026-01-01T00:00:00Z",
               "build_id": row_build, "ayanamsha_id": "lahiri",
               "verification_pass_status": TWO_PASS_VERIFIED}
    conn = RecordingConnection([
        [{"generation": "candidate-1", "state": "building", "conventions": pins}],
        [], [invalid], [], [],
    ])
    ctx = _ctx(conn)
    ctx.build_id = "candidate-build"

    # (I) INTERPRETATION: admit the F2 tier/build before inspecting its
    # intervals (ALGO v1.1 §3.1). A malformed admitted row is rejected by
    # the clock reader before the writer can construct its index or mutate.
    with pytest.raises(error_type, match=f"^{message}$"):
        avadhi.KaAvdhiWriter().run(ctx)

    assert conn.mutations == []


def test_computed_writers_preserve_partition_when_candidate_build_interrupts(monkeypatch):
    conn = RecordingConnection()
    monkeypatch.setattr(
        tithi,
        "_birth_dt_and_params_from_config",
        lambda *_: (SimpleNamespace(), {}),
    )
    monkeypatch.setattr(tithi, "_fetch_natal_moon_longitude", lambda *_: (0.0, "fact-1"))
    monkeypatch.setattr(tithi, "DEFAULT_MAX_PRAVESHA_YEAR", 2)
    monkeypatch.setattr(tithi, "_compute_one_year", lambda *_: (_ for _ in ()).throw(RuntimeError("interrupted")))
    with pytest.raises(RuntimeError, match="interrupted"):
        tithi.KaTithiPraveshaWriter().run(_ctx(conn, birth_params=_BIRTH))
    assert conn.mutations == []

    conn = RecordingConnection()
    monkeypatch.setattr(sudarshana, "_birth_date_from_config", lambda *_: date(1990, 1, 1))
    monkeypatch.setattr(
        sudarshana,
        "_fetch_natal_reference_signs",
        lambda *_: {key: {"sign_idx": 0, "fact_id": key} for key in ("LAGNA", "MOON", "SUN")},
    )
    monkeypatch.setattr(sudarshana, "DEFAULT_MAX_VARSHA_YEAR", 2)
    monkeypatch.setattr(sudarshana, "compute_tri_lagna_year", lambda *_: (_ for _ in ()).throw(RuntimeError("interrupted")))
    with pytest.raises(RuntimeError, match="interrupted"):
        sudarshana.KaSudarshanaVarshaWriter().run(_ctx(conn))
    assert conn.mutations == []


def test_computed_writers_delete_only_after_complete_candidate(monkeypatch):
    conn = RecordingConnection()
    monkeypatch.setattr(tithi, "_birth_dt_and_params_from_config", lambda *_: (SimpleNamespace(), {}))
    monkeypatch.setattr(tithi, "_fetch_natal_moon_longitude", lambda *_: (0.0, "fact-1"))
    monkeypatch.setattr(tithi, "DEFAULT_MAX_PRAVESHA_YEAR", 1)
    monkeypatch.setattr(
        tithi,
        "_compute_one_year",
        lambda *_: {"verification_pass_status": "passed", "graha_positions_jsonb": {}, "ephemeris_audit_jsonb": {}},
    )
    result = tithi.KaTithiPraveshaWriter().run(_ctx(conn, birth_params=_BIRTH))
    assert result.rows_inserted == 1
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE")

    conn = RecordingConnection()
    monkeypatch.setattr(sudarshana, "_birth_date_from_config", lambda *_: date(1990, 1, 1))
    monkeypatch.setattr(
        sudarshana,
        "_fetch_natal_reference_signs",
        lambda *_: {key: {"sign_idx": 0, "fact_id": key} for key in ("LAGNA", "MOON", "SUN")},
    )
    monkeypatch.setattr(sudarshana, "DEFAULT_MAX_VARSHA_YEAR", 1)
    monkeypatch.setattr(
        sudarshana,
        "compute_tri_lagna_year",
        lambda *_: {"jl_active_sign_idx": 0, "cl_active_sign_idx": 0, "sl_active_sign_idx": 0, "tri_lagna_convergence": True},
    )
    monkeypatch.setattr(sudarshana, "varsha_window", lambda *_: (date(2026, 1, 1), date(2026, 12, 31)))
    result = sudarshana.KaSudarshanaVarshaWriter().run(_ctx(conn))
    assert result.rows_inserted == 1
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE")


def test_yojaka_legacy_fixture_empty_input_preserves_partition():
    conn = RecordingConnection([[]])
    # The historical template is retained for regression evidence; production
    # candidate F1 replacement is exercised by the K2-1b database oracles.
    ctx = _ctx(conn)
    ctx.config["candidate_generation"] = "candidate:CODEX-w2"
    result = yojaka.KaYojakaWriter().legacy_testimony_fixture(ctx)
    assert result.asset_id == "ka_yojaka"
    assert result.rows_inserted == 0
    assert conn.mutations == []


def test_yojaka_legacy_fixture_deletes_only_after_complete_candidate(monkeypatch):
    signal = {
        "signal_id": "signal-1",
        "chart_id": "chart-1",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "signal_type_class": "fixture",
        "signal_type_id": "fixture",
        "configuration_jsonb": {},
        "constituent_facts_array": [],
        "valence": "neutral",
        "dignity_score": None,
        "shadbala_norm": None,
    }
    conn = RecordingConnection([[signal], [], []])
    for name in (
        "_fetch_cgm_pagerank", "_fetch_cdlm_domain_strength", "_fetch_house_lord_map",
        "_fetch_yoga_firing_planets", "_fetch_activation_source_facts",
    ):
        monkeypatch.setattr(yojaka.KaYojakaWriter, name, lambda *_: {})
    monkeypatch.setattr(yojaka, "classify_signal", lambda *_: "FIXTURE")
    monkeypatch.setattr(
        yojaka,
        "build_predicate",
        lambda *_: {
            "dasha_eligibility_rule": {"constituent_lords": []},
            "transit_trigger": {},
            "strength_affliction_hook": {},
            "derivation_ledger": {},
        },
    )
    monkeypatch.setattr(yojaka, "extract_lords_from_config", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(yojaka, "_extract_primary_graha", lambda *_: None)
    monkeypatch.setattr(yojaka, "_infer_signal_domain", lambda *_: "general")

    ctx = _ctx(conn)
    ctx.config["candidate_generation"] = "candidate:CODEX-w2"
    result = yojaka.KaYojakaWriter().legacy_testimony_fixture(ctx)

    assert result.asset_id == "ka_yojaka"
    assert result.rows_inserted == 1
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE")
    assert conn.mutations[0][2] == ("chart-1", "candidate:CODEX-w2")
    assert conn.mutations[-1][0] == "executemany"
