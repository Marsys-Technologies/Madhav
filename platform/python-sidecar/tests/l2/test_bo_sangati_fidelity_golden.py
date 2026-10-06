"""Golden-value fidelity test for bo_sangati narration (citation_human).

Rules, read from the writer:
  * CDLM cell citation: "CDLM cell: <row_domain>×<col_domain>, <N> shared signals",
    row domain alphabetically before the column domain, N = number of distinct signals
    carrying BOTH domains.
  * Convergence citation: "Convergence: <domain> — <N> signals", N = number of signals
    carrying that domain.
Expected sentences are written by hand from the inputs below: three signals, two of
which carry both career and wealth, one carrying career only.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_sangati import (
    _build_cdlm_cells,
    _build_convergence_rows,
)


def _sig(signal_id: str, domains: list[str], salience: float) -> dict:
    return {
        "signal_id": signal_id,
        "domains_affected_array": domains,
        "computed_salience": salience,
        "signal_tradition": "parashari",
        "constituent_facts_array": [f"fact-{signal_id}"],
    }


def test_cdlm_cell_and_convergence_citation_human_state_hand_counted_signals() -> None:
    signals = [
        _sig("s1", ["career", "wealth"], 0.8),
        _sig("s2", ["career", "wealth"], 0.5),
        _sig("s3", ["career"], 0.4),
    ]
    now = "2026-01-01T00:00:00+00:00"

    cells = _build_cdlm_cells("chart-1", "lahiri", "build-1", signals, set(), now)
    cell = [c for c in cells if c["domain_row"] == "career" and c["domain_col"] == "wealth"][0]
    citation_human = cell["citation_human"]
    assert citation_human == "CDLM cell: career×wealth, 2 shared signals"

    convergence = _build_convergence_rows("chart-1", "lahiri", "build-1", signals, set(), now)
    by_domain = {r["domain"]: r for r in convergence}
    assert by_domain["career"]["citation_human"] == "Convergence: career — 3 signals"
    assert by_domain["wealth"]["citation_human"] == "Convergence: wealth — 2 signals"
