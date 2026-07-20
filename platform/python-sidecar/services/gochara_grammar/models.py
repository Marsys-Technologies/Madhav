"""
gochara_grammar.models — shared dataclasses for the G-2 configuration grammar.

`ResonanceTarget` is G-2's READ-SIDE contract against G-1's `gochara_resonance_map`
schema (sibling lane, binding contract per the D-5 wave brief §1 row G-1):

    CREATE TABLE gochara_resonance_map (
      id BIGSERIAL PRIMARY KEY,
      chart_id UUID NOT NULL,
      event_class TEXT NOT NULL,
      target_type TEXT NOT NULL,   -- 'bhava'|'lord'|'karaka'|'mechanism_node'|
                                    -- 'sensitive_degree'|'arudha'|'yoga_constituent'|
                                    -- 'dasha_lord_portfolio'
      target_ref TEXT NOT NULL,
      weight NUMERIC NOT NULL,
      classical_citation TEXT,
      uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
      source_rule_id INTEGER,
      computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(chart_id, event_class, target_type, target_ref)
    );

G-2 does not own natal-position resolution (target_ref -> longitude/sign/nakshatra);
that is a thin enrichment step the caller performs from `chart_facts` before handing
a `ResonanceTarget` to a primitive. The `target_longitude_deg` / `target_sign` /
`target_nakshatra_id` / `natal_planet` fields are therefore Optional and primitives
degrade honestly (return `[]` with a documented reason in `extra`, never crash) when
the specific anchor a primitive needs is unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

VALID_TARGET_TYPES = (
    "bhava",
    "lord",
    "karaka",
    "mechanism_node",
    "sensitive_degree",
    "arudha",
    "yoga_constituent",
    "dasha_lord_portfolio",
)

VALID_TEMPORAL_SHAPES = ("point", "interval", "chain")


class CitationDisciplineError(ValueError):
    """Raised when a sentence is constructed with neither a classical_citation
    nor an explicit uncited_extension=True flag, or with BOTH set at once.

    B.10 hard rule (CLAUDE.md §N; restated BRIEF_D5 §6): every primitive/
    composition's output sentence carries EITHER a classical_citation OR an
    explicit uncited_extension=True flag. Zero silent gaps -- a primitive
    with neither is a lane-failing defect, not a style note. This exception
    makes that invariant a *mechanical* guarantee (construction-time), not a
    convention callers must remember to honor.
    """


@dataclass
class ResonanceTarget:
    """One row (or fixture-equivalent) from `gochara_resonance_map`, optionally
    enriched with a resolved natal longitude/sign/nakshatra for the geometry
    primitives to scan against."""

    chart_id: str
    event_class: str
    target_type: str
    target_ref: str
    weight: float
    classical_citation: Optional[str] = None
    uncited_extension: bool = False
    source_rule_id: Optional[int] = None

    # Resolved astronomical anchors -- populated by the caller from natal
    # chart_facts (G-2 consumes, does not compute, natal positions).
    target_longitude_deg: Optional[float] = None
    target_sign: Optional[str] = None
    target_nakshatra_id: Optional[int] = None  # 1..27
    natal_planet: Optional[str] = None  # graha this target resolves to, if applicable

    def __post_init__(self) -> None:
        if self.target_type not in VALID_TARGET_TYPES:
            raise ValueError(
                f"target_type must be one of {VALID_TARGET_TYPES}, got {self.target_type!r}"
            )
        if not self.classical_citation and not self.uncited_extension:
            raise CitationDisciplineError(
                f"ResonanceTarget chart_id={self.chart_id!r} event_class={self.event_class!r} "
                f"target_ref={self.target_ref!r} carries neither classical_citation nor "
                "uncited_extension=True -- violates the same B.10 discipline G-1's own table "
                "enforces (gochara_resonance_map schema note, G-1 verifier column)."
            )


def _check_citation_discipline(
    classical_citation: Optional[str], uncited_extension: bool, context: str
) -> None:
    if not classical_citation and not uncited_extension:
        raise CitationDisciplineError(
            f"{context}: carries neither classical_citation nor uncited_extension=True "
            "-- B.10 citation discipline violation (CLAUDE.md §N / BRIEF_D5 §6)."
        )
    if classical_citation and uncited_extension:
        raise CitationDisciplineError(
            f"{context}: sets BOTH classical_citation AND uncited_extension=True -- these are "
            "mutually exclusive (a sentence is either genuinely cited, or honestly flagged as an "
            "uncited extension; never both at once, which would be citation-gaming)."
        )


@dataclass
class ConfigurationSentence:
    """One grounded configuration event emitted by a G-2 contact primitive.

    `fact_ids` carries whatever grounding references the primitive resolved
    (resonance-map row id, chart_facts fact_id(s) for the natal anchor, and/or
    a synthetic-fixture marker when running off a hand-built test fixture --
    see `extra['fixture']` in that case).
    """

    primitive: str
    chart_id: str
    event_class: Optional[str]
    target_type: Optional[str]
    target_ref: Optional[str]
    transit_planet: Optional[str]
    secondary_planet: Optional[str]
    event_jd: Optional[float]
    event_datetime_ist: Optional[str]
    temporal_shape: str
    fact_ids: list = field(default_factory=list)
    classical_citation: Optional[str] = None
    uncited_extension: bool = False
    detail: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.temporal_shape not in VALID_TEMPORAL_SHAPES:
            raise ValueError(
                f"temporal_shape must be one of {VALID_TEMPORAL_SHAPES}, got {self.temporal_shape!r}"
            )
        _check_citation_discipline(
            self.classical_citation,
            self.uncited_extension,
            f"ConfigurationSentence(primitive={self.primitive!r}, target_ref={self.target_ref!r})",
        )


@dataclass
class CompositionSentence:
    """One grounded composition event emitted by a G-2 composition operator,
    combining ≥1 member ConfigurationSentence (or, for dasha-coincidence,
    member sentences plus a dasha-period reference)."""

    operator: str
    chart_id: str
    event_jd: Optional[float]
    event_datetime_ist: Optional[str]
    temporal_shape: str
    member_sentences: list = field(default_factory=list)
    classical_citation: Optional[str] = None
    uncited_extension: bool = False
    detail: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.temporal_shape not in VALID_TEMPORAL_SHAPES:
            raise ValueError(
                f"temporal_shape must be one of {VALID_TEMPORAL_SHAPES}, got {self.temporal_shape!r}"
            )
        _check_citation_discipline(
            self.classical_citation,
            self.uncited_extension,
            f"CompositionSentence(operator={self.operator!r})",
        )


__all__ = [
    "VALID_TARGET_TYPES",
    "VALID_TEMPORAL_SHAPES",
    "CitationDisciplineError",
    "ResonanceTarget",
    "ConfigurationSentence",
    "CompositionSentence",
]
