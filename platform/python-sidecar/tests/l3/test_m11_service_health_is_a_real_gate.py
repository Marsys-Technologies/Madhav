"""
NIRMĀṆA L3-W3 finding M11 (§N.8) — a degraded service must not build green.

THE DEFECT. `asset_registry.service_health` was written by every L3 service self-test and read
as a gate by nothing. Worse, two of the writers computed a verdict and threw it away:
`ka_graha_sancara` had a literal `status = "success" if health == "healthy" else "error"` that
was assigned and never read. Because the orchestrator treats ANY returned `WriterResult` as
success regardless of its `notes`, an unhealthy self-test still left the asset promoted to
'lit'. Measured before the fix: `ka_graha_sancara` was `state='lit'` WHILE its
`service_health` was `'unhealthy'` — a green build signal with no detector behind it, which is
exactly the class §N.8 exists to eliminate.

THE FIX. Raise, so `_run_data_writer` catches it and calls `mark_asset_error`. That is the only
signal path that prevents promotion. `ka_muhurta_seva` already did this correctly and documents
why; these tests hold all four services to that one standard.

These tests FAIL against the pre-fix writers, which returned a WriterResult in the unhealthy
branch instead of raising.
"""
from __future__ import annotations

import types

import pytest


class _Ctx:
    """Minimal ContextSpec stand-in: the writers touch only dry_run, db_conn and config."""

    def __init__(self) -> None:
        self.dry_run = False
        self.db_conn = None
        self.config: dict = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}


def _no_health_write(*_args, **_kwargs) -> None:
    """The registry write is a side effect, not the subject; neutralise it."""
    return None


def test_ka_tulana_raises_when_its_selftest_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.ka_tulana import writer as mod

    monkeypatch.setattr(mod, "_run_selftest", lambda: (False, "synthetic failure"))
    monkeypatch.setattr(mod, "_update_registry_health", _no_health_write)

    w = mod.KaTulanaWriter()
    with pytest.raises(RuntimeError, match="ka_tulana self-test failed"):
        w.run(_Ctx())


def test_ka_tulana_returns_normally_when_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard must be selective: a healthy self-test still returns a WriterResult."""
    from services.ka_tulana import writer as mod

    monkeypatch.setattr(mod, "_run_selftest", lambda: (True, "all checks passed"))
    monkeypatch.setattr(mod, "_update_registry_health", _no_health_write)

    result = mod.KaTulanaWriter().run(_Ctx())
    assert result.rows_inserted == 0
    assert "service_health=healthy" in (result.notes or "")


def test_ka_dasha_kala_raises_when_its_selftest_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.ka_dasha_kala import writer as mod

    monkeypatch.setattr(mod, "_run_selftest", lambda _conn: (False, "synthetic failure"))
    monkeypatch.setattr(mod, "_update_registry_health", _no_health_write)

    with pytest.raises(RuntimeError, match="ka_dasha_kala self-test failed"):
        mod.KaDashaKalaWriter().run(_Ctx())


def test_ka_dasha_kala_returns_normally_when_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.ka_dasha_kala import writer as mod

    monkeypatch.setattr(mod, "_run_selftest", lambda _conn: (True, "all checks passed"))
    monkeypatch.setattr(mod, "_update_registry_health", _no_health_write)

    result = mod.KaDashaKalaWriter().run(_Ctx())
    assert result.rows_inserted == 0
    assert "service_health=healthy" in (result.notes or "")


def test_ka_graha_sancara_raises_when_unhealthy(monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.orchestrator.writers import ka_graha_sancara as mod

    w = mod.KaGrahaSancaraWriter()
    monkeypatch.setattr(
        w, "_run_selftest",
        lambda _ctx: ("unhealthy", {"checks": [], "errors": ["ephemeris computation failed: 0"]}),
    )
    monkeypatch.setattr(w, "_write_health", lambda *_a, **_k: None)

    with pytest.raises(RuntimeError, match="ka_graha_sancara self-test"):
        w.run(_Ctx())


def test_ka_graha_sancara_returns_normally_when_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.orchestrator.writers import ka_graha_sancara as mod

    w = mod.KaGrahaSancaraWriter()
    monkeypatch.setattr(w, "_run_selftest", lambda _ctx: ("healthy", {"checks": [1, 2], "errors": []}))
    monkeypatch.setattr(w, "_write_health", lambda *_a, **_k: None)

    result = w.run(_Ctx())
    assert result.rows_inserted == 0
    assert "healthy" in (result.notes or "")


def test_no_l3_service_writer_computes_a_verdict_and_discards_it() -> None:
    """
    The specific shape of the original defect: a status/verdict variable assigned from the
    health outcome and then never read. Guarding the shape, not just the instance, because
    the same pattern is what let it survive review the first time.
    """
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    suspects = [
        root / "pipeline/orchestrator/writers/ka_graha_sancara.py",
        root / "services/ka_tulana/writer.py",
        root / "services/ka_dasha_kala/writer.py",
        root / "services/ka_muhurta_seva/writer.py",
    ]
    for path in suspects:
        # Strip comments first: ka_graha_sancara.py deliberately QUOTES the removed line in the
        # comment explaining what was fixed, and that documentation is worth keeping. The guard
        # is about executable code, so it must not match prose about the defect.
        source = "\n".join(
            line.split("#", 1)[0] for line in path.read_text().splitlines()
        )
        assert 'status = "success" if health' not in source, (
            f"{path.name}: a health verdict is computed into `status` and never read — the M11 "
            "defect. Raise on the unhealthy branch instead."
        )
