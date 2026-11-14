"""The withdrawn command surface stays unavailable; its separate compatibility API refuses.

Original exporter source and mocked comparison fixtures remain at main commit
c5a0ffe2baee40014e3e8e80fbbde4ba3357d79d. These tests assert current runtime
resolution and refusal, not historical provider or vector-output equivalence.
"""
import importlib.util
import sys
from types import ModuleType

import pytest


@pytest.mark.parametrize("name", [
    "brahmagyan.bodha.bo_2-7",
    "brahmagyan.mimamsa.export_to_bigquery",
])
def test_withdrawn_command_cannot_resolve_in_the_runtime_package(name):
    assert importlib.util.find_spec(name) is None


@pytest.mark.parametrize("entrypoint", ["run_export", "export_to_bigquery"])
def test_disabled_compatibility_does_not_delegate_to_the_withdrawn_exporter(monkeypatch, entrypoint):
    legacy = ModuleType("brahmagyan.mimamsa.export_to_bigquery")

    def forbidden(*args, **kwargs):
        raise AssertionError("withdrawn exporter must not be invoked")

    legacy.run_export = forbidden
    legacy.export_table = forbidden
    monkeypatch.setitem(sys.modules, legacy.__name__, legacy)
    from brahmagyan.mimamsa import l5_bigquery_export

    with pytest.raises(l5_bigquery_export.BigQueryExportDisabled):
        getattr(l5_bigquery_export, entrypoint)(object())
