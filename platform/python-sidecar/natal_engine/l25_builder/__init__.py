"""
natal_engine.l25_builder — deterministic L1→L2.5 transform.

Pure module. NO LLM imports. NO Postgres I/O. NO fixture reads.

Takes the engine output dict (from natal_engine.compute_chart) plus a stable
`chart_id` (operator-assigned, e.g. 'abhisek_mohanty_native_v1') and produces
the row-shaped dicts for the L2.5 stores:

    build_chart_facts(chart_output, chart_id) -> list[dict]
    build_l25_msr_signals(chart_output, chart_id) -> list[dict]
    build_l25_cdlm_links(chart_output, chart_id) -> list[dict]
    build_l25_cgm_nodes(chart_output, chart_id) -> list[dict]
    build_l25_cgm_edges(chart_output, chart_id) -> list[dict]
    build_l25_rm_resonances(chart_output, chart_id) -> list[dict]
    build_l25_ucn_sections(chart_output, chart_id) -> list[dict]

Plus a single all-in-one:

    build_all(chart_output, chart_id) -> dict[str, list[dict]]

The MSR coefficient is decomposed into THREE columns
(`deterministic_strength`, `verification_certainty`, `computed_salience`) —
NO fused score (Gemini keeper).

Determinism contract: identical engine output + identical chart_id ⇒
byte-identical JSONL across two runs. Verified by 2a's determinism check.
"""

from __future__ import annotations

from .build import (
    build_all,
    build_chart_facts,
    build_l25_cdlm_links,
    build_l25_cgm_edges,
    build_l25_cgm_nodes,
    build_l25_msr_signals,
    build_l25_rm_resonances,
    build_l25_ucn_sections,
    canonical_jsonl,
    compute_ucn_signature,
)

__all__ = [
    "build_all",
    "build_chart_facts",
    "build_l25_msr_signals",
    "build_l25_cdlm_links",
    "build_l25_cgm_nodes",
    "build_l25_cgm_edges",
    "build_l25_rm_resonances",
    "build_l25_ucn_sections",
    "canonical_jsonl",
    "compute_ucn_signature",
]
