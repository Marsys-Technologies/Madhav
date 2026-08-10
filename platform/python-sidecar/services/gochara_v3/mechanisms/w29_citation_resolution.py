"""
gochara_v3.mechanisms.w29_citation_resolution — Wave 2.9 candidate mechanism.

LANE W2.9 [mech]: Citation resolution table.

Context
-------
Windows carry citation strings from three sources:

  1. services/gochara_grammar/citations.py — 14 named constants (its full __all__).
     Each constant is a verbatim copy of a citation string already present elsewhere
     in this codebase (migration comments, l0_reference.py rows, ga_*_writer.py
     docstrings). Provenance is recorded per constant in citations.py's own comments.

  2. services/gochara_grammar/primitives.py — inline classical_citation= assignments.
     Some are bound to citations.py constants (imported as `C`); others are None
     (uncited_extension=True families: #1 degree_contact, #10 eclipse_degree,
     #11 planetary_return). The distinct *resolved* strings used by primitives.py
     are a subset of citations.py constants; the None / uncited_extension cases
     are cataloged here honestly as "uncited_extension".

  3. bg_transit_rules.classical_citation — live DB rows. The gochara_vedha_pair
     primitive inherits the citation verbatim from the matched rule row, or falls
     back to C.PHALADEEPIKA_VEDHA_26 when the row's own field is NULL. The
     av_threshold_state primitive similarly inherits from bg_transit_av_gates rows
     or falls back to C.ASHTAKAVARGA_AV_GATES. These DB-sourced strings are not
     enumerable statically; they are cataloged here by their *fallback* constant
     and disclosed as "db_inherited" source.

Nothing in the current codebase resolves any of these citation strings to actual
classical_text_chunks verse_refs. This module builds the honest baseline catalog:
status="resolved" entries carry placeholder verse_ref stubs (to be populated by
the Wave 5 seeding job against the real classical_text_chunks table); status=
"unresolved" entries mark citation strings where no verse_ref mapping has been
attempted yet.

Mechanism contract
------------------
- MECHANISM_ID / TOGGLE_KEY: "w29_citation_resolution"
- compute() modifier is always 1.0 — this mechanism annotates, never gates lambda.
- compute() returns sentences describing citation resolution status for the
  active event_class context (counts resolved vs. unresolved, exposes the catalog).
- get_all_citations() returns the full catalog dict for use by migration seeding
  (Wave 5 work — this module is the catalog source, not the seeder).

I2 compliance: this module READ-ONLY imports from gochara_grammar.citations
(for the constant values). It does NOT modify gochara_grammar/* in any way.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# I2: read-only import of citations.py constants for catalog enumeration.
# We import the module (not individual names) so the catalog is driven by
# the module's own __all__ list — if citations.py gains a new constant,
# re-running get_all_citations() will include it automatically.
import services.gochara_grammar.citations as _C

MECHANISM_ID = "w29_citation_resolution"
TOGGLE_KEY = "w29_citation_resolution"


# ---------------------------------------------------------------------------
# Catalog helpers
# ---------------------------------------------------------------------------

@dataclass
class MechanismResult:
    """Return type for compute()."""
    mechanism_id: str
    modifier: float                   # always 1.0 for W2.9
    sentences: list[dict]             # annotation sentences
    detail: dict = field(default_factory=dict)


def _citations_py_catalog() -> dict[str, dict]:
    """
    Enumerate every name in citations.__all__ and build a catalog entry.

    Each entry shape:
      {
        "status": "resolved" | "unresolved",
        "source": "citations_py",
        "constant_name": str,           # the Python constant name
        "verse_refs": list[str],        # populated by Wave 5 seeding; [] baseline
        "note": str,                    # provenance note from citations.py
      }

    The baseline has status="unresolved" and empty verse_refs for all entries —
    the honest starting point before Wave 5 seeding runs against the real
    classical_text_chunks table.
    """
    catalog: dict[str, dict] = {}
    for name in _C.__all__:
        value: str = getattr(_C, name)
        catalog[value] = {
            "status": "unresolved",
            "source": "citations_py",
            "constant_name": name,
            "verse_refs": [],
            "note": (
                f"citations.py constant {name!r}; provenance documented in "
                "citations.py per-constant comment. Verse-ref mapping pending "
                "Wave 5 classical_text_chunks seeding."
            ),
        }
    return catalog


def _primitives_py_catalog() -> dict[str, dict]:
    """
    Catalog the citation behavior of each of the 12 primitive families in
    primitives.py.  Three cases:

      a) Families that assign a citations.py constant → already in the
         citations_py catalog; record the usage here with source="primitives_py"
         so the serving layer can see which primitive uses which citation.

      b) Families where classical_citation=None / uncited_extension=True →
         cataloged with status="uncited_extension" (not "unresolved" — there
         is no citation to resolve; the primitive's own docstring explains why).

      c) Families that inherit citation from a DB row (gochara_vedha_pair,
         av_threshold_state) → cataloged with source="db_inherited" pointing
         to the fallback constant.

    Returns entries keyed by citation string (same key space as the citations_py
    catalog); entries that duplicate a citations_py key add a "primitives_py_usage"
    note but do NOT replace the primary entry.
    """
    # Primitive families and their citation disposition per primitives.py module
    # docstring §per-family citation-or-uncited decision (lines 20-56).
    primitives_citation_map = [
        # (primitive_name, citation_string_or_None, status, source, note)
        (
            "degree_contact",
            None,
            "uncited_extension",
            "primitives_py",
            "Family #1: grammar's own tight-orb decomposition of general BPHS Ch.29 "
            "gochara-to-a-point idea; no codebase-attested citation names 'exact degree "
            "contact' as its own technique (primitives.py docstring #1).",
        ),
        (
            "drishti_contact_point",
            _C.GRAHA_DRISHTI_BPHS_26,
            "unresolved",
            "primitives_py",
            "Family #2 (point path): classical graha drishti (BPHS Ch.26, l0_reference.py). "
            "Uses citations.py constant GRAHA_DRISHTI_BPHS_26.",
        ),
        (
            "drishti_contact_rasi",
            _C.GRAHA_DRISHTI_RASI_BPHS_26,
            "unresolved",
            "primitives_py",
            "Family #2 (rasi/span path): whole-sign special aspect, BPHS Ch.26 rasi drishti "
            "rendering. Uses citations.py constant GRAHA_DRISHTI_RASI_BPHS_26 (D-5 RED-D fix).",
        ),
        (
            "sign_ingress",
            _C.GOCHARA_PHALA_BPHS_29,
            "unresolved",
            "primitives_py",
            "Family #3: BPHS Ch.29 Gochara Phala, base sign-transit-result technique. "
            "Uses citations.py constant GOCHARA_PHALA_BPHS_29.",
        ),
        (
            "sign_occupation",
            _C.GOCHARA_PHALA_BPHS_29,
            "unresolved",
            "primitives_py",
            "sign_occupation (RED-D addendum, not a numbered family): same BPHS Ch.29 "
            "citation as sign_ingress — occupancy of a house by a transiting graha IS "
            "the base Gochara Phala doctrine. Uses GOCHARA_PHALA_BPHS_29.",
        ),
        (
            "nakshatra_ingress_tara",
            _C.TARA_BALA_MUHURTA_CHINTAMANI,
            "unresolved",
            "primitives_py",
            "Family #4: Muhurta Chintamani / BPHS / Jataka Parijata Tara Bala "
            "(tara_bala.py module docstring). Uses citations.py constant "
            "TARA_BALA_MUHURTA_CHINTAMANI.",
        ),
        (
            "kakshya_cell_crossing_db",
            _C.KAKSHYA_BPHS_66,
            "unresolved",
            "primitives_py",
            "Family #5 (DB-sourced boundaries path): BPHS Ch.66 when real "
            "ashtakavarga_kakshya_boundary chart_facts rows are used. "
            "Uses citations.py constant KAKSHYA_BPHS_66.",
        ),
        (
            "kakshya_cell_crossing_fallback",
            None,
            "uncited_extension",
            "primitives_py",
            "Family #5 (equal-eighths fallback path): uncited_extension when falling back "
            "to the equal-eighths fixture approximation (no live boundary data reachable). "
            "Disclosed via detail['source']='equal_eighths_fixture_approximation'.",
        ),
        (
            "av_threshold_state",
            _C.ASHTAKAVARGA_AV_GATES,
            "unresolved",
            "db_inherited",
            "Family #6: BPHS Ch.66-68 + Phaladeepika Ch.26 when a real bg_transit_av_gates "
            "row is matched (migration 397). Citation is INHERITED from the gate row's own "
            "classical_citation field; ASHTAKAVARGA_AV_GATES is the fallback when the DB "
            "row's field is NULL. uncited_extension on sub-claim when SAV data unreachable.",
        ),
        (
            "gochara_vedha_pair",
            _C.PHALADEEPIKA_VEDHA_26,
            "unresolved",
            "db_inherited",
            "Family #7: BPHS Ch.29 + Phaladeepika Ch.26, INHERITED verbatim from the "
            "matched bg_transit_rules.classical_citation row. PHALADEEPIKA_VEDHA_26 is the "
            "fallback when the rule row's own field is NULL. "
            "(primitives.py docstring #7: 'inherited from bg_transit_rules.classical_citation')",
        ),
        (
            "station_retro_loop",
            _C.VAKRA_RETROGRADE_BPHS_27,
            "unresolved",
            "primitives_py",
            "Family #9: BPHS Ch.27 (Vakra/cheshta bala, l0_reference.py). "
            "Uses citations.py constant VAKRA_RETROGRADE_BPHS_27.",
        ),
        (
            "eclipse_degree",
            None,
            "uncited_extension",
            "primitives_py",
            "Family #10: uncited_extension — no codebase-attested classical citation for "
            "eclipse-degree-to-natal-point contact as a named technique (primitives.py docstring #10).",
        ),
        (
            "planetary_return",
            None,
            "uncited_extension",
            "primitives_py",
            "Family #11: uncited_extension — no codebase-attested citation for "
            "planetary-return-to-own-natal-degree as a named technique (primitives.py docstring #11).",
        ),
        (
            "sade_sati_phase",
            _C.SADE_SATI_BPHS_71,
            "unresolved",
            "primitives_py",
            "Family #12: BPHS Ch.71, INHERITED from the matched chart_facts sade_sati row's "
            "citation_human when available (ga_sade_sati_writer.py); falls back to "
            "SADE_SATI_BPHS_71 constant when unavailable. Uses citations.py constant SADE_SATI_BPHS_71.",
        ),
    ]

    catalog: dict[str, dict] = {}
    for primitive_name, citation_str, status, source, note in primitives_citation_map:
        if citation_str is None:
            # uncited_extension: key by primitive name so the entry is unique
            key = f"_uncited:{primitive_name}"
        else:
            key = citation_str

        if key not in catalog:
            catalog[key] = {
                "status": status,
                "source": source,
                "primitive_families": [primitive_name],
                "verse_refs": [],
                "note": note,
            }
        else:
            # Merge additional primitive usage into existing entry
            existing = catalog[key]
            if primitive_name not in existing.get("primitive_families", []):
                existing.setdefault("primitive_families", []).append(primitive_name)

    return catalog


def _bg_transit_rules_catalog() -> dict[str, dict]:
    """
    Catalog citation strings sourced from bg_transit_rules.classical_citation
    and bg_transit_av_gates.classical_citation (third source).

    These are live DB columns — the static set of citation strings they carry
    is not enumerable here without a DB query, which violates the no-DB
    constraint for a mechanism module. We catalog the KNOWN fallbacks (which
    are citations.py constants) and record the dynamic nature honestly.

    The Wave 5 seeding job will query bg_transit_rules.classical_citation
    DISTINCT values and update this catalog's verse_refs.
    """
    return {
        "_bg_transit_rules:dynamic": {
            "status": "unresolved",
            "source": "bg_transit_rules",
            "verse_refs": [],
            "note": (
                "bg_transit_rules.classical_citation is a live DB column; its distinct "
                "value set is not enumerable statically. The gochara_vedha_pair primitive "
                "inherits citation verbatim from the matched rule row, falling back to "
                "PHALADEEPIKA_VEDHA_26 when NULL. Wave 5 seeding will query DISTINCT "
                "values and map them to verse_refs. Fallback constant is already cataloged "
                "under source='db_inherited' in the primitives_py section."
            ),
        },
        "_bg_transit_av_gates:dynamic": {
            "status": "unresolved",
            "source": "bg_transit_rules",
            "verse_refs": [],
            "note": (
                "bg_transit_av_gates.classical_citation is a live DB column (migration 397). "
                "The av_threshold_state primitive inherits citation from the gate row, falling "
                "back to ASHTAKAVARGA_AV_GATES when NULL. Wave 5 seeding will query DISTINCT "
                "values. Fallback constant is already cataloged under source='db_inherited'."
            ),
        },
    }


def _build_catalog() -> dict[str, dict]:
    """
    Merge all three source catalogs into the unified CITATION_CATALOG.

    Merge strategy:
    - citations_py entries are the primary record (source='citations_py').
    - primitives_py entries whose key already exists (same citation string as a
      citations_py constant) add 'primitive_families' AND merge 'usage_sources'
      so that both 'citations_py' and the incoming source (e.g. 'db_inherited')
      are visible on the merged entry. This preserves the fact that a constant
      is used as a DB-inherited fallback, without creating a duplicate key.
    - Fully new keys from primitives_py (uncited_extension families keyed
      '_uncited:<name>') are inserted as-is.
    - bg_transit_rules entries are distinct keys (always new).
    """
    catalog: dict[str, dict] = {}

    # Source 1: citations.py constants (primary)
    for key, entry in _citations_py_catalog().items():
        catalog[key] = entry

    # Source 2: primitives.py usage — merge into existing entries or add new ones
    for key, entry in _primitives_py_catalog().items():
        if key in catalog:
            # Same citation string as a citations_py constant — merge metadata.
            existing = catalog[key]
            # Accumulate primitive_families
            for pf in entry.get("primitive_families", []):
                existing.setdefault("primitive_families", [])
                if pf not in existing["primitive_families"]:
                    existing["primitive_families"].append(pf)
            # Record that this entry is ALSO used as a db_inherited fallback, so
            # source='citations_py' entries that double as db-inherited fallbacks
            # carry that information explicitly.
            incoming_source = entry.get("source")
            if incoming_source and incoming_source != existing.get("source"):
                existing.setdefault("usage_sources", [existing["source"]])
                if incoming_source not in existing["usage_sources"]:
                    existing["usage_sources"].append(incoming_source)
        else:
            # New key: uncited_extension families (_uncited:<name>) or any
            # db_inherited fallback constant not present in citations_py.
            catalog[key] = entry

    # Source 3: bg_transit_rules dynamic entries (always new keys)
    for key, entry in _bg_transit_rules_catalog().items():
        if key not in catalog:
            catalog[key] = entry

    return catalog


# ---------------------------------------------------------------------------
# Module-level catalog (built once at import time, statically)
# ---------------------------------------------------------------------------

CITATION_CATALOG: dict[str, dict] = _build_catalog()


def get_all_citations() -> dict[str, dict]:
    """
    Returns the full CITATION_CATALOG for use by migration seeding (Wave 5).

    The catalog covers all three citation sources:
      - citations.py constants (source='citations_py')
      - primitives.py inline usage, including uncited_extension families
        (source='primitives_py' or 'db_inherited')
      - bg_transit_rules / bg_transit_av_gates dynamic DB columns
        (source='bg_transit_rules', status='unresolved', keyed as '_bg_transit_*')

    Verse_refs are empty in all entries at baseline — Wave 5 populates them
    by querying classical_text_chunks and seeding migration-528 style.
    """
    return CITATION_CATALOG


def _count_by_status(catalog: dict[str, dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in catalog.values():
        s = entry.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


def _count_by_source(catalog: dict[str, dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in catalog.values():
        s = entry.get("source", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# compute()
# ---------------------------------------------------------------------------

def compute(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """
    Annotate the active context with citation resolution status.

    This mechanism does NOT modify lambda — its modifier is always 1.0.
    Its sentences report how many citation strings in the catalog are resolved
    vs. unresolved vs. uncited_extension, scoped to the active event_class.

    When enabled=False, returns zero sentences and modifier=1.0 (toggle-safe).
    """
    if not enabled:
        return MechanismResult(
            mechanism_id=MECHANISM_ID,
            modifier=1.0,
            sentences=[],
            detail={"enabled": False},
        )

    catalog = CITATION_CATALOG
    counts = _count_by_status(catalog)
    source_counts = _count_by_source(catalog)

    event_class = getattr(context, "event_class", None) if context is not None else None

    sentences = [
        {
            "mechanism_id": MECHANISM_ID,
            "type": "citation_resolution_summary",
            "event_class": event_class,
            "total_catalog_entries": len(catalog),
            "resolved_count": counts.get("resolved", 0),
            "unresolved_count": counts.get("unresolved", 0),
            "uncited_extension_count": counts.get("uncited_extension", 0),
            "source_breakdown": source_counts,
            "note": (
                "Baseline catalog — verse_refs empty pending Wave 5 "
                "classical_text_chunks seeding. Modifier is 1.0 (this "
                "mechanism annotates, never gates lambda)."
            ),
        }
    ]

    return MechanismResult(
        mechanism_id=MECHANISM_ID,
        modifier=1.0,
        sentences=sentences,
        detail={
            "enabled": True,
            "catalog_size": len(catalog),
            "status_counts": counts,
            "source_counts": source_counts,
        },
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "CITATION_CATALOG",
    "MechanismResult",
    "get_all_citations",
    "compute",
]
