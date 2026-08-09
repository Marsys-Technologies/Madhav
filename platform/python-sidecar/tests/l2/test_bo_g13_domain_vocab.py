"""
test_bo_g13_domain_vocab.py — SAMPURTI · G13/PA-4 (R17)

Per-writer tests asserting that bo_sangati, bo_bimba, and bo_karanajala import
and operate over the canonical 13-domain vocabulary rather than a local 7-domain
list.

Three axes per writer:
  A. The module does NOT define a local KNOWN_DOMAINS variable (local list deleted).
  B. The module imports CANONICAL_DOMAINS from brahmagyan.domain_vocabulary.
  C. Domain-handling logic covers all 13 canonical domains (not just 7).

These tests were written FAILING-FIRST against the un-migrated codebase where all
three writers carried a local `KNOWN_DOMAINS = ["career", "wealth", "health",
"relationship", "spirituality", "character", "general"]` list (7 domains), and
PASS after the G13/PA-4 migration replaces those lists with the canonical import.

Citation: MASTER_PLAN_v1_0.md §G13 + PA-4; adoption-over-addition principle R17.
"""
from __future__ import annotations

import importlib
import inspect
import sys
import pathlib

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS, CANONICAL_DOMAINS_SORTED  # noqa: E402

# ── helpers ───────────────────────────────────────────────────────────────────

_WRITERS_PKG = "pipeline.orchestrator.writers"

_TARGET_WRITERS = [
    "bo_sangati",
    "bo_bimba",
    "bo_karanajala",
]


def _import_writer(name: str):
    """Import a writer module from pipeline.orchestrator.writers."""
    full = f"{_WRITERS_PKG}.{name}"
    if full in sys.modules:
        return sys.modules[full]
    return importlib.import_module(full)


def _module_source(mod) -> str:
    """Return the source text of a module (for attribute-name scanning)."""
    try:
        return inspect.getsource(mod)
    except OSError:
        path = pathlib.Path(mod.__file__)
        return path.read_text(encoding="utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════════════════════
# Axis A — no local KNOWN_DOMAINS definition in any of the three writers
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("writer_name", _TARGET_WRITERS)
def test_no_local_KNOWN_DOMAINS_attribute(writer_name: str):
    """G13/PA-4 Axis A: writer module must NOT export a bare KNOWN_DOMAINS attribute.

    Before the migration all three writers defined:
        KNOWN_DOMAINS = ["career", "wealth", "health", "relationship",
                         "spirituality", "character", "general"]
    After the migration that line is deleted; CANONICAL_DOMAINS from brahmagyan is
    used directly. The module may keep a `_KNOWN_DOMAINS` alias (underscore prefix
    marks it as module-private and not part of the public writer contract) — that
    alias is explicitly permitted here because it simply points at CANONICAL_DOMAINS
    and is not a new local vocabulary.
    """
    mod = _import_writer(writer_name)
    # The bare public name must be gone
    assert not hasattr(mod, "KNOWN_DOMAINS"), (
        f"{writer_name}: still exports a public `KNOWN_DOMAINS` attribute — "
        f"delete it and use `from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS` instead."
    )


@pytest.mark.parametrize("writer_name", _TARGET_WRITERS)
def test_local_KNOWN_DOMAINS_alias_if_present_equals_canonical(writer_name: str):
    """G13/PA-4 Axis A (alias guard): if a `_KNOWN_DOMAINS` alias exists, it must
    be exactly CANONICAL_DOMAINS — not a new local set.

    The migration uses `_KNOWN_DOMAINS = CANONICAL_DOMAINS` as a convenience alias.
    This test ensures the alias is never quietly replaced with a new local list.
    """
    mod = _import_writer(writer_name)
    alias = getattr(mod, "_KNOWN_DOMAINS", None)
    if alias is None:
        return  # alias not present — acceptable
    assert alias is CANONICAL_DOMAINS or set(alias) == CANONICAL_DOMAINS, (
        f"{writer_name}: `_KNOWN_DOMAINS` is present but does not equal CANONICAL_DOMAINS. "
        f"Found: {sorted(alias)!r}. Expected: {sorted(CANONICAL_DOMAINS)!r}."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Axis B — module imports CANONICAL_DOMAINS from brahmagyan.domain_vocabulary
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("writer_name", _TARGET_WRITERS)
def test_imports_CANONICAL_DOMAINS(writer_name: str):
    """G13/PA-4 Axis B: writer module must import CANONICAL_DOMAINS from the
    canonical L0 vocabulary module.

    We check two things:
      1. The module has a `CANONICAL_DOMAINS` name in its namespace (directly
         imported or re-bound).
      2. That name equals the real CANONICAL_DOMAINS frozenset (not a shadow).
    """
    mod = _import_writer(writer_name)
    assert hasattr(mod, "CANONICAL_DOMAINS"), (
        f"{writer_name}: `CANONICAL_DOMAINS` not found in module namespace. "
        f"Add `from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS`."
    )
    mod_cd = getattr(mod, "CANONICAL_DOMAINS")
    assert set(mod_cd) == CANONICAL_DOMAINS, (
        f"{writer_name}: module's CANONICAL_DOMAINS ({sorted(mod_cd)!r}) "
        f"does not match the canonical frozenset ({sorted(CANONICAL_DOMAINS)!r})."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Axis C — domain-handling logic covers all 13 canonical domains
# ═══════════════════════════════════════════════════════════════════════════════

def test_bo_sangati_build_convergence_covers_all_13_domains():
    """G13/PA-4 Axis C (bo_sangati): _build_convergence_rows iterates over all 13
    canonical domains, not just the original 7.

    We exercise the function with synthetic signals that span all 13 domains and
    assert that every domain produces a convergence row (when signals are present).
    """
    from pipeline.orchestrator.writers.bo_sangati import _build_convergence_rows

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    # One synthetic signal per canonical domain
    signals = [
        {
            "signal_id":             f"sig-{d}",
            "signal_type_class":     "yoga",
            "signal_tradition":      "parashari",
            "domains_affected_array": [d],
            "computed_salience":     0.5,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":        f"test_yoga_{d}",
        }
        for d in CANONICAL_DOMAINS_SORTED
    ]

    rows = _build_convergence_rows(chart_id, aya, build_id, signals, set(), now)
    produced_domains = {r["domain"] for r in rows}

    missing = CANONICAL_DOMAINS - produced_domains
    assert not missing, (
        f"bo_sangati._build_convergence_rows did not produce convergence rows for "
        f"domains: {sorted(missing)}. Expected coverage of all 13 canonical domains."
    )
    assert produced_domains <= CANONICAL_DOMAINS, (
        f"bo_sangati._build_convergence_rows produced rows for non-canonical domains: "
        f"{sorted(produced_domains - CANONICAL_DOMAINS)}"
    )


def test_bo_sangati_build_cdlm_cells_covers_13_domain_pairs():
    """G13/PA-4 Axis C (bo_sangati): _build_cdlm_cells produces cells for pairs
    from all 13 canonical domains when signals co-occur across them.

    With 13 canonical domains there are C(13,2)=78 possible pairs. We verify the
    function can produce cells for pairs that include the 6 domains absent from
    the old 7-domain list (progeny, education, family, residence, travel, transition).
    """
    from pipeline.orchestrator.writers.bo_sangati import _build_cdlm_cells

    NEW_DOMAINS = {"progeny", "education", "family", "residence", "travel", "transition"}

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    # One signal that spans career + each of the 6 new domains
    signals = [
        {
            "signal_id":              f"sig-career-{d}",
            "signal_type_class":      "yoga",
            "signal_tradition":       "parashari",
            "domains_affected_array": ["career", d],
            "computed_salience":      0.5,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":         f"test_yoga_career_{d}",
        }
        for d in sorted(NEW_DOMAINS)
    ]

    cells = _build_cdlm_cells(chart_id, aya, build_id, signals, set(), now)
    cell_pairs = {(c["domain_row"], c["domain_col"]) for c in cells}

    for d in sorted(NEW_DOMAINS):
        # The pair (career, d) or (d, career) in sorted order should appear
        pair = tuple(sorted(["career", d]))
        assert pair in cell_pairs, (
            f"bo_sangati._build_cdlm_cells did not produce a cell for pair {pair}. "
            f"The 6 domains absent from the old 7-domain list must produce cells now."
        )


def test_bo_sangati_build_triangulation_covers_all_13_domains():
    """G13/PA-4 Axis C (bo_sangati): _build_triangulation_rows iterates over all
    13 canonical domains, not just the original 7.
    """
    from pipeline.orchestrator.writers.bo_sangati import _build_triangulation_rows

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    # One signal per domain, parashari tradition
    signals = [
        {
            "signal_id":              f"sig-{d}",
            "signal_type_class":      "yoga",
            "signal_tradition":       "parashari",
            "domains_affected_array": [d],
            "computed_salience":      0.7,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":         f"test_{d}",
        }
        for d in CANONICAL_DOMAINS_SORTED
    ]

    rows = _build_triangulation_rows(chart_id, aya, build_id, signals, now)
    produced_domains = {r["question_class"] for r in rows}

    missing = CANONICAL_DOMAINS - produced_domains
    assert not missing, (
        f"bo_sangati._build_triangulation_rows did not produce rows for domains: "
        f"{sorted(missing)}. Must cover all 13 canonical domains."
    )


def test_bo_bimba_build_nodes_creates_domain_nodes_for_all_13():
    """G13/PA-4 Axis C (bo_bimba): _build_nodes_for_aya creates one domain node
    per canonical domain — 13 domain nodes total, not 7.
    """
    from pipeline.orchestrator.writers.bo_bimba import _build_nodes_for_aya

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    # Minimal signals — domain node creation doesn't require signals to be present
    # for each domain (it always emits one node per domain)
    signals: list[dict] = []

    nodes = _build_nodes_for_aya(chart_id, aya, build_id, signals, now)
    domain_nodes = [n for n in nodes if n.get("node_type") == "domain"]
    domain_subjects = {n["node_subject"] for n in domain_nodes}

    assert len(domain_nodes) == 13, (
        f"bo_bimba._build_nodes_for_aya produced {len(domain_nodes)} domain nodes; "
        f"expected 13 (one per canonical domain). "
        f"Found: {sorted(domain_subjects)!r}."
    )
    missing = CANONICAL_DOMAINS - domain_subjects
    assert not missing, (
        f"bo_bimba._build_nodes_for_aya missing domain nodes for: {sorted(missing)}. "
        f"All 13 canonical domains must have a CGM node."
    )
    non_canonical = domain_subjects - CANONICAL_DOMAINS
    assert not non_canonical, (
        f"bo_bimba._build_nodes_for_aya produced domain nodes for non-canonical "
        f"domains: {sorted(non_canonical)}."
    )


def test_bo_bimba_domain_salience_accumulates_for_all_13():
    """G13/PA-4 Axis C (bo_bimba): salience accumulation tracks all 13 canonical
    domains. A signal whose domains_affected_array contains a new domain (e.g.
    'progeny') must increase that domain node's strength_score above 0.0.
    """
    from pipeline.orchestrator.writers.bo_bimba import _build_nodes_for_aya

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    NEW_DOMAINS = ["progeny", "education", "family", "residence", "travel", "transition"]

    signals = [
        {
            "signal_id":              f"sig-{d}",
            "signal_type_class":      "yoga",
            "signal_tradition":       "parashari",
            "configuration_jsonb":    None,
            "domains_affected_array": [d],
            "deterministic_strength": 1.0,
            "computed_salience":      0.8,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":         f"test_{d}",
        }
        for d in NEW_DOMAINS
    ]

    nodes = _build_nodes_for_aya(chart_id, aya, build_id, signals, now)
    domain_nodes = {n["node_subject"]: n for n in nodes if n.get("node_type") == "domain"}

    for d in NEW_DOMAINS:
        node = domain_nodes.get(d)
        assert node is not None, (
            f"bo_bimba: no domain node created for '{d}' (one of the 6 new canonical domains)."
        )
        strength = node["strength_score"]
        assert strength > 0.0, (
            f"bo_bimba: domain node '{d}' has strength_score={strength}; "
            f"expected > 0.0 because a signal with salience 0.8 references this domain. "
            f"The salience accumulation loop is not covering the full 13-domain set."
        )


def test_bo_karanajala_contradiction_detection_covers_all_13_domains():
    """G13/PA-4 Axis C (bo_karanajala): _detect_contradictions iterates over all
    13 canonical domains for Class 2 (domain_promise_vs_denial) detection.

    A promise/denial pair in a new domain (e.g. 'progeny') must be detected.
    Before the migration only the original 7 domains were scanned (sorted(KNOWN_DOMAINS)
    in the Class 2 loop at line 1380); after migration the loop uses CANONICAL_DOMAINS_SORTED.
    """
    from pipeline.orchestrator.writers.bo_karanajala import _detect_contradictions

    NEW_DOMAINS = ["progeny", "education", "family", "residence", "travel", "transition"]

    chart_id = "test-chart-g13"
    aya      = "lahiri_chitrapaksha"
    build_id = "build-g13"
    now      = "2026-08-10T00:00:00+00:00"

    for new_domain in NEW_DOMAINS:
        # Create one yoga + one dosha signal in the new domain (no graha keyed by
        # configuration_jsonb → Class 1 graha_yoga_vs_dosha won't fire; Class 2
        # domain_promise_vs_denial fires when both a yoga and dosha exist for a domain).
        yoga_sig = {
            "signal_id":              f"yoga-{new_domain}",
            "signal_type_class":      "yoga",
            "signal_tradition":       "parashari",
            "configuration_jsonb":    None,
            "domains_affected_array": [new_domain],
            "computed_salience":      0.8,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":         f"test_yoga_{new_domain}",
        }
        dosha_sig = {
            "signal_id":              f"dosha-{new_domain}",
            "signal_type_class":      "dosha",
            "signal_tradition":       "parashari",
            "configuration_jsonb":    None,
            "domains_affected_array": [new_domain],
            "computed_salience":      0.6,
            "verification_pass_status": "single_pass",
            "salience_formula_version": "v1.0",
            "signal_type_id":         f"test_dosha_{new_domain}",
        }
        signals = [yoga_sig, dosha_sig]

        rows = _detect_contradictions(chart_id, aya, build_id, signals, now)
        domains_seen: set[str] = set()
        for r in rows:
            domains_seen.update(r.get("domains_affected_array") or [])

        assert new_domain in domains_seen, (
            f"bo_karanajala._detect_contradictions did not detect a contradiction "
            f"in domain '{new_domain}' (one of the 6 new canonical domains). "
            f"Class 2 (domain_promise_vs_denial) must scan all 13 canonical domains."
        )
