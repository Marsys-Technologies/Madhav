"""
ka_dasha_kala — Orchestrator adapter for the Dasa-Eligibility service (L3 Kala).

This thin adapter registers the writer from
`services/ka_dasha_kala/writer.py` with the orchestrator registry.
The actual self-test + health-update logic lives in the service package.

Asset kind: service (no data rows written to chart_dashas).
"""
from services.ka_dasha_kala.writer import KaDashaKalaWriter  # noqa: F401 — side-effect import

source_paths = ["platform/python-sidecar/services/ka_dasha_kala/"]
