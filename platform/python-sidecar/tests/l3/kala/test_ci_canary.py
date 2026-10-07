"""Collected by the required Governance Gates py-sidecar discovery command."""


def test_kala_governance_gates_canary(request):
    assert "KĀLA-YANTRA CI CANARY".startswith("KĀLA-YANTRA")
    request.config.pluginmanager.get_plugin("terminalreporter").write_line(
        "KĀLA-YANTRA CI CANARY PASSED"
    )
