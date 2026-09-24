"""N-15 (L3 §4.10) exit-gate fixture — `sade_sati_mode` testimony flag.

When sade_sati_mode='testimony':
  - sade_sati leaves the PERMISSION weight set entirely (total_weight
    renormalised; never a zero-weight row);
  - the phase is reported as typed testimony (epistemic_class='testimony',
    corpus_verifiable=False, citations PG1333/PG1334/PG1339/PG1340/PG1342
    at MEDIUM provenance per N-21 — the corrected §7.6 list; PG786 resolves
    to zero rows and is dropped);
  - the global permission lift is a first-class delta
    (sade_sati_permission_lift).

Default 'permission_weight' is byte-identical.

Synthetic chart data only (no real chart, no person).
"""
from __future__ import annotations

import pytest

from services.gochara_v3 import engine
from services.gochara_intensity.permission import DASHA_SYSTEM_IDS


class _Swe:
    pass


class _Ctx:
    chart_id = "00000000-0000-4000-8000-0000000004a10"  # synthetic, non-person


T_JD = 2460000.0


def _patch_generators(monkeypatch, *, sade_sati_active: bool):
    monkeypatch.setattr(engine, "_jd_to_ist_iso", lambda swe, jd: "syn-iso")
    monkeypatch.setattr(
        engine, "_dasha_contributions_from_context",
        lambda context, t_iso: {
            sid: {"active": sid == "vimshottari", "detail": {}}
            for sid in DASHA_SYSTEM_IDS
        },
    )
    monkeypatch.setattr(
        engine, "_check_sade_sati_from_context",
        lambda context, t_iso: (sade_sati_active, {"phase": "syn"}),
    )
    monkeypatch.setattr(
        engine, "_check_guru_shani_from_context",
        lambda *a, **k: (False, {}),
    )
    monkeypatch.setattr(
        engine, "_check_av_threshold_from_context",
        lambda *a, **k: (False, {}),
    )
    monkeypatch.setattr(
        engine, "_check_planetary_return_from_context",
        lambda *a, **k: (False, {}),
    )


def test_testimony_mode_renormalises_and_reports_lift(monkeypatch):
    _patch_generators(monkeypatch, sade_sati_active=False)
    legacy_permission, legacy_detail = engine._compute_permission_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"],
    )
    assert abs(legacy_permission - 0.16) < 1e-9  # vimshottari only, /1.0
    assert "sade_sati_testimony" not in legacy_detail

    permission, detail = engine._compute_permission_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"], sade_sati_mode="testimony",
    )
    assert abs(permission - 0.16 / 0.9) < 1e-9
    lift = detail["sade_sati_permission_lift"]
    assert lift["legacy_permission"] == legacy_permission
    assert lift["testimony_permission"] == permission
    assert abs(lift["delta"] - (0.16 / 0.9 - 0.16)) < 1e-9

    system_ids = [s["system_id"] for s in detail["systems"]]
    assert "sade_sati" not in system_ids
    assert all(s["weight"] > 0.0 for s in detail["systems"])
    assert "sade_sati" not in detail["systems_considered"]

    testimony = detail["sade_sati_testimony"]
    assert testimony["active"] is False
    assert testimony["epistemic_class"] == "testimony"
    assert testimony["corpus_verifiable"] is False
    refs = {c["ref"] for c in testimony["citations"]}
    assert refs == {"PG1333", "PG1334", "PG1339", "PG1340", "PG1342"}
    assert all(c["provenance"] == "MEDIUM" for c in testimony["citations"])
    assert "[U]" in testimony["note"]


def test_testimony_mode_with_sade_sati_active(monkeypatch):
    _patch_generators(monkeypatch, sade_sati_active=True)
    permission, detail = engine._compute_permission_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"], sade_sati_mode="testimony",
    )
    # legacy would have been (0.16 + 0.10) / 1.0 = 0.26
    lift = detail["sade_sati_permission_lift"]
    assert abs(lift["legacy_permission"] - 0.26) < 1e-9
    assert abs(permission - 0.16 / 0.9) < 1e-9
    assert abs(lift["delta"] - (0.16 / 0.9 - 0.26)) < 1e-9
    assert detail["sade_sati_testimony"]["active"] is True
    assert detail["sade_sati_testimony"]["detail"] == {"phase": "syn"}


def test_flag_off_byte_identical(monkeypatch):
    _patch_generators(monkeypatch, sade_sati_active=True)
    p_default, d_default = engine._compute_permission_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"],
    )
    p_explicit, d_explicit = engine._compute_permission_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"], sade_sati_mode="permission_weight",
    )
    assert p_default == p_explicit
    assert d_default == d_explicit


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match="sade_sati_mode"):
        engine._compute_permission_from_context(
            None, None, 0.0, [], sade_sati_mode="not_a_mode",
        )
