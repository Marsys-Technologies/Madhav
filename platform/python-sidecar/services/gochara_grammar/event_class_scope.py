"""
gochara_grammar.event_class_scope — the ONE declaration of which event classes
the gochara sweep grammar covers, and the canonical class → life-domain mirror
it coordinates through.

WHY THIS MODULE EXISTS (ṢAḌ-DARŚANA brief §7 rail: *"ONE canonical domain
vocabulary (shared constant, CI-diffed; the event grammar and any new event
class — item 9 — coordinates through it)"*).

Before item 9 the sweep's scope lived as a bare literal inside
`services/ka_gochara_resonance/writer.py`:

    TARGET_EVENT_CLASSES = ("marriage", "major_gain", "career_advancement")

`gochara_resonance_map` is populated from that tuple; `ka_gochara_sweep`
discovers its substep plan from whatever `gochara_resonance_map` rows exist for
a chart; and the served `coverage.event_classes_covered` /
`coverage.domains_not_covered` (platform-mcp `register_gochara_windows.ts`) are
derived from the same table. So that one tuple silently decided which life
domains the entire forward hazard-scan could ever speak about — and it named no
health-domain class and no adverse-valence class at all. That is DP-4, and DP-4
is the data root of the S4-05 trust-breaking veto (a health question answered
"clean — no adverse window" from a scan structurally incapable of seeing
health). See `tests/l3/test_s4_05_health_adverse_class.py` for the scenario and
its regression suite.

The scope is now declared HERE, once, next to the canonical class→domain
mirror, so that:
  * the resonance writer, the sweep writer's scheduling tiers, and any future
    consumer read the SAME tuple;
  * every member is provably a real `brahma_event_ontology` event_class_id (an
    import-time check below, plus a CI test) — item 9 adds *coverage of* an
    existing canonical class, never a new parallel taxonomy;
  * the domain arithmetic the served `domains_not_covered` performs is
    reproducible offline, in one place.

CANONICAL SOURCE + FALLBACK DISCIPLINE
`brahma_event_ontology` (migrations 388 seed + 456 extension) is the canonical
vocabulary — both the 27 `event_class_id` values and the 13-value `domain`
CHECK universe. `DOMAIN_MAP` below is that table's `domain` column transcribed
verbatim, following exactly the same "live-preferred, documented-fallback,
never silently invented" discipline as its two sibling mirrors,
`gochara_intensity.valence.VALENCE_MAP` and
`gochara_intensity.engine.SHAPE_MAP` (which mirror the same 27 rows'
`evidence_requirements->>'valence'` and `temporal_shape`). `fetch_domain`
prefers a live read whenever a connection is available.
"""
from __future__ import annotations

import logging
from typing import Optional

from services.gochara_intensity._dbutil import savepoint_scope

logger = logging.getLogger(__name__)

# ── The canonical class → life-domain mirror (27 classes) ────────────────────
# Transcribed verbatim from `brahma_event_ontology.domain`:
#   platform/supabase/migrations/388_brahma_ghatana_ontology.sql  (22 classes)
#   platform/supabase/migrations/456_brahma_event_ontology_dr13_shapes.sql (+5)
# Diff-locked to the sibling mirrors by
# tests/l3/test_s4_05_health_adverse_class.py::test_domain_map_is_the_full_27_class_ontology.
DOMAIN_MAP: dict[str, str] = {
    "career_entry": "career",
    "career_advancement": "career",
    "career_change": "career",
    "career_setback": "career",
    "business_launch": "career",
    "education_milestone": "education",
    "exam_outcome": "education",
    "marriage": "relationship",
    "romantic_start": "relationship",
    "separation": "relationship",
    "childbirth": "progeny",
    "parental_event": "family",
    "bereavement": "transition",
    "major_gain": "wealth",
    "major_loss": "wealth",
    "property_acquisition": "residence",
    "relocation": "residence",
    "foreign_settlement": "travel",
    "illness_acute": "health",
    "chronic_onset": "health",
    "surgery": "health",
    "spiritual_turn": "spirituality",
    # ── the 5 classes added by migration 456 ──
    "achievement_recognition": "general",
    "financial_deception": "wealth",
    "psychological_arc": "character",
    "birth_anchor": "transition",
    "travel_event": "travel",
}

# ── Sweep scope ──────────────────────────────────────────────────────────────
# The three classes the D-5 G-1 lane originally built targets for, chosen then
# for richest `bg_transit_rules` (graha x house) coverage —
# GOCHARA_RESONANCE_MAP_SPEC.md §4. Untouched by item 9: the extension is
# strictly additive, and `kala_gochara_windows` rows for these classes are
# untouchable campaign data.
_LEGACY_EVENT_CLASSES: tuple[str, ...] = ("marriage", "major_gain", "career_advancement")

# ── Item 9: the health / adverse-valence extension (closes DP-4) ─────────────
# EXACTLY the ontology's `domain = 'health'` set — not a hand-picked subset.
# Partial health coverage would be its own quiet misrepresentation: coverage
# would report the health domain as covered while a whole limb of it (chronic
# onset, say) was never swept, and a "nothing on the health side" answer would
# again be broader than the scan behind it.
#
# All three are grounded, not plausible-sounding (LAW ZERO):
#   illness_acute  houses 6,8 · lords 6L,8L · karakas Mars,Saturn  · shape point
#                  · valence loss · ARRAY['BPHS ch.6 (roga-bhava)','Phaladeepika ch.6']
#   chronic_onset  houses 6,8 · lords 6L,8L · karaka Saturn        · shape interval
#                  · valence loss · ARRAY['BPHS ch.6,8; Sade-Sati rules']
#   surgery        houses 6,8 · lords 6L,8L · karaka Mars          · shape point
#                  · valence neutral · ARRAY['BPHS ch.6 (shastra-vrana)',
#                                            'Phaladeepika on Mars aspects']
# (`surgery`'s canonical valence is 'neutral' — a scheduled procedure is not
# itself a loss event. It is swept because the health DOMAIN is what a health
# question asks about; the two adverse-valence health classes above are what
# make the `is_adverse = true` hazard surface non-vacuous. The valence is read
# from the ontology, never overridden here.)
HEALTH_ADVERSE_EVENT_CLASSES: tuple[str, ...] = (
    "illness_acute",
    "chronic_onset",
    "surgery",
)

# The full sweep scope. Order is stable and legacy-first so an existing chart's
# substep plan keeps its historical ordering prefix.
SWEEP_EVENT_CLASSES: tuple[str, ...] = _LEGACY_EVENT_CLASSES + HEALTH_ADVERSE_EVENT_CLASSES

# Not swept, and honestly so: the ontology's remaining adverse-valence classes
# (career_setback, separation, major_loss, bereavement, financial_deception,
# psychological_arc). Each additional class costs a full birth->birth+100y
# substep column (101 substeps/chart). They are a follow-on scope decision, NOT
# a claim that they are covered — `coverage.domains_not_covered` continues to
# report every domain they would have covered as structurally dark, which is
# the truthful state.
KNOWN_UNSWEPT_ADVERSE_EVENT_CLASSES: tuple[str, ...] = (
    "career_setback",
    "separation",
    "major_loss",
    "bereavement",
    "financial_deception",
    "psychological_arc",
)


def sweep_domains() -> set[str]:
    """The life domains the sweep's event-class universe can speak about at
    all. The served `coverage.domains_not_covered` is the canonical domain
    universe MINUS this set (see `register_gochara_windows.ts`
    `computeGocharaCoverage`); reproduced here so the arithmetic is testable
    offline and lives beside the scope it depends on."""
    return {DOMAIN_MAP[ec] for ec in SWEEP_EVENT_CLASSES}


def fetch_domain(conn, event_class: str) -> Optional[str]:
    """Live-read `brahma_event_ontology.domain` for `event_class`; falls back
    to `DOMAIN_MAP` (honest, documented fixture) on ANY DB-shape surprise —
    identical discipline to `gochara_intensity.valence.fetch_valence`. Returns
    None for a class that is in neither, rather than guessing a domain."""
    if conn is not None:
        try:
            with savepoint_scope(conn, "event_domain"):
                cur = conn.execute(
                    "SELECT domain FROM brahma_event_ontology WHERE event_class_id = %s",
                    [event_class],
                )
                row = cur.fetchone()
                if row is not None:
                    v = row["domain"] if isinstance(row, dict) else row[0]
                    if v:
                        return str(v)
        except Exception as exc:  # noqa: BLE001
            logger.info(
                "[gochara_grammar.event_class_scope] brahma_event_ontology live read "
                "failed for event_class=%s, falling back to DOMAIN_MAP: %s",
                event_class, exc,
            )
    return DOMAIN_MAP.get(event_class)


# Import-time guard: the scope may only ever name canonical ontology classes.
# A typo or an invented "health_adverse"-style class fails the import loudly
# here rather than producing a silently-empty sweep column later.
_unknown = [ec for ec in SWEEP_EVENT_CLASSES if ec not in DOMAIN_MAP]
if _unknown:  # pragma: no cover - guard
    raise ValueError(
        "gochara sweep scope names non-canonical event classes "
        f"{_unknown}; every member must be a brahma_event_ontology "
        "event_class_id (ONE-VOCABULARY rail)"
    )

__all__ = [
    "DOMAIN_MAP",
    "SWEEP_EVENT_CLASSES",
    "HEALTH_ADVERSE_EVENT_CLASSES",
    "KNOWN_UNSWEPT_ADVERSE_EVENT_CLASSES",
    "sweep_domains",
    "fetch_domain",
]
