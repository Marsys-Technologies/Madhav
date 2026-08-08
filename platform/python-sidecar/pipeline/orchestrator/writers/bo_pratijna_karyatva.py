"""
bo_pratijna_karyatva — Classical Significator Maps for Promise Engine v3
========================================================================
Per-class karyatva (significator) factor sets drawn from BPHS, Phaladeepika,
and Jaimini Sutram. R13: these are drawn from classical rules ONLY, never
adjusted for any native's known outcomes.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KaryatvaMap:
    """Factor set for one event class."""
    event_class_id: str
    primary_bhava: list[int]          # Houses that are primary evidence
    karaka_grahas: list[str]          # Natural significators (planet names as in chart_facts)
    dusthana_required: bool = False   # True for separation-type: occurrence requires dusthana involvement
    divisional: str | None = None     # Relevant varga chart (D7, D9, D10, etc.)
    yoga_keywords: list[str] = field(default_factory=list)  # Keywords to match yoga-related signals
    condition_malefic_grahas: list[str] = field(default_factory=list)  # Malefics whose involvement = condition evidence
    citations: list[str] = field(default_factory=list)  # Classical text citations
    provisional: bool = False         # True for DR-13 classes that use domain fallback


# The 27-class karyatva map, one entry per event_class_id (brahma_event_ontology).
# R13 MANDATE: every entry drawn from classical rules with citations.
# No weight or threshold traces to any native's known outcomes.
KARYATVA_REGISTRY: dict[str, KaryatvaMap] = {
    "marriage": KaryatvaMap(
        event_class_id="marriage",
        primary_bhava=[7],
        karaka_grahas=["Venus", "Jupiter"],
        dusthana_required=False,
        divisional="D9",
        yoga_keywords=["darakaraka", "upapada", "kalatra"],
        condition_malefic_grahas=["Saturn", "Rahu", "Ketu"],
        citations=["BPHS ch.19 (vivaha-vicara)", "BPHS ch.28 (karaka-adhyaya)", "BPHS ch.6 (navamsha)", "Jaimini Sutram 1.3.1 (upapada)"],
    ),
    "separation": KaryatvaMap(
        event_class_id="separation",
        primary_bhava=[7, 6, 8, 12],
        karaka_grahas=["Saturn", "Ketu"],
        dusthana_required=True,  # KEY DIFFERENCE from marriage
        divisional="D9",
        yoga_keywords=["kuja_dosha", "manglik", "6L-7L"],
        condition_malefic_grahas=["Mars", "Rahu"],
        citations=["BPHS ch.19 (vivaha-vicara)", "BPHS ch.12 (dusthana)", "BPHS ch.28"],
    ),
    "childbirth": KaryatvaMap(
        event_class_id="childbirth",
        primary_bhava=[5],
        karaka_grahas=["Jupiter"],
        dusthana_required=False,
        divisional="D7",
        yoga_keywords=["putra", "santana"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.16 (santana-vicara)", "BPHS ch.28", "BPHS ch.6 (saptamsha)"],
    ),
    "surgery": KaryatvaMap(
        event_class_id="surgery",
        primary_bhava=[6, 8],
        karaka_grahas=["Mars"],
        dusthana_required=False,
        divisional="D30",
        yoga_keywords=["shastra", "vrana"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.12 (shastra-vrana)", "Phaladeepika ch.6"],
    ),
    "relocation": KaryatvaMap(
        event_class_id="relocation",
        primary_bhava=[4, 12],
        karaka_grahas=["Moon", "Rahu"],
        dusthana_required=False,
        divisional="D4",
        yoga_keywords=["pravasa", "desa"],
        condition_malefic_grahas=["Saturn", "Ketu"],
        citations=["BPHS ch.11 (sukha-bhava)", "BPHS ch.12 (vyaya)", "BPHS ch.28"],
    ),
    "foreign_settlement": KaryatvaMap(
        event_class_id="foreign_settlement",
        primary_bhava=[12, 9, 7],
        karaka_grahas=["Rahu"],
        dusthana_required=False,
        divisional="D9",
        yoga_keywords=["videsh", "pravasa"],
        condition_malefic_grahas=["Saturn", "Ketu"],
        citations=["BPHS ch.12 (videsh)", "BPHS ch.28"],
    ),
    "romantic_start": KaryatvaMap(
        event_class_id="romantic_start",
        primary_bhava=[5, 7],
        karaka_grahas=["Venus"],
        dusthana_required=False,
        divisional="D9",
        yoga_keywords=["kalatra", "prema"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.5 (putra-bhava)", "BPHS ch.19 (vivaha)"],
    ),
    "career_entry": KaryatvaMap(
        event_class_id="career_entry",
        primary_bhava=[10],
        karaka_grahas=["Sun", "Saturn"],
        dusthana_required=False,
        divisional="D10",
        yoga_keywords=["karma", "rajya"],
        condition_malefic_grahas=["Rahu", "Ketu"],
        citations=["BPHS ch.10 (karma-bhava)", "BPHS ch.28"],
    ),
    "career_change": KaryatvaMap(
        event_class_id="career_change",
        primary_bhava=[10, 3, 9],
        karaka_grahas=["Rahu"],
        dusthana_required=False,
        divisional="D10",
        yoga_keywords=["parivartana", "vrtti_badal"],
        condition_malefic_grahas=["Saturn", "Ketu"],
        citations=["BPHS ch.10 (karma-bhava)", "BPHS ch.3 (parakrama, initiative-of-change)", "BPHS ch.9 (labha of 9th, fortune-of-change)", "BPHS ch.28 (Rahu karakatva for sudden/foreign-influenced change)"],
    ),
    "career_advancement": KaryatvaMap(
        event_class_id="career_advancement",
        primary_bhava=[10, 11],
        karaka_grahas=["Sun", "Jupiter"],
        dusthana_required=False,
        divisional="D10",
        yoga_keywords=["rajya", "labha"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.10", "BPHS ch.11 (labha)", "BPHS ch.28"],
    ),
    "career_setback": KaryatvaMap(
        event_class_id="career_setback",
        primary_bhava=[10, 6, 8],
        karaka_grahas=["Saturn"],
        dusthana_required=True,
        divisional="D10",
        yoga_keywords=["karma", "roga"],
        condition_malefic_grahas=["Mars", "Rahu"],
        citations=["BPHS ch.10", "BPHS ch.12 (dusthana)", "BPHS ch.28"],
    ),
    "business_launch": KaryatvaMap(
        event_class_id="business_launch",
        primary_bhava=[7, 10, 11],
        karaka_grahas=["Mercury", "Jupiter"],
        dusthana_required=False,
        divisional="D10",
        yoga_keywords=["vanijya", "labha"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.10", "BPHS ch.11 (labha)", "BPHS ch.28"],
    ),
    "education_milestone": KaryatvaMap(
        event_class_id="education_milestone",
        primary_bhava=[4, 5, 9],
        karaka_grahas=["Mercury", "Jupiter"],
        dusthana_required=False,
        divisional="D24",
        yoga_keywords=["vidya", "buddhi", "guru"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.4 (vidya)", "BPHS ch.5 (buddhi)", "BPHS ch.24", "BPHS ch.28"],
    ),
    "exam_outcome": KaryatvaMap(
        event_class_id="exam_outcome",
        primary_bhava=[4, 5],
        karaka_grahas=["Mercury", "Jupiter"],
        dusthana_required=False,
        divisional="D24",
        yoga_keywords=["vidya", "buddhi"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.4", "BPHS ch.5", "BPHS ch.28"],
    ),
    "illness_acute": KaryatvaMap(
        event_class_id="illness_acute",
        primary_bhava=[6],
        karaka_grahas=["Mars"],
        dusthana_required=False,
        divisional="D30",
        yoga_keywords=["roga", "vyadhi"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.12 (roga)", "Phaladeepika ch.6"],
    ),
    "chronic_onset": KaryatvaMap(
        event_class_id="chronic_onset",
        primary_bhava=[6, 8],
        karaka_grahas=["Saturn"],
        dusthana_required=False,
        divisional="D30",
        yoga_keywords=["roga", "deergha"],
        condition_malefic_grahas=["Rahu", "Ketu"],
        citations=["BPHS ch.12 (roga/randhra)", "Phaladeepika ch.6"],
    ),
    "major_gain": KaryatvaMap(
        event_class_id="major_gain",
        primary_bhava=[2, 11],
        karaka_grahas=["Jupiter", "Mercury"],
        dusthana_required=False,
        divisional="D2",
        yoga_keywords=["dhana", "labha"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.2 (dhana)", "BPHS ch.11 (labha)", "BPHS ch.28"],
    ),
    "major_loss": KaryatvaMap(
        event_class_id="major_loss",
        primary_bhava=[2, 12],
        karaka_grahas=["Saturn"],
        dusthana_required=True,
        divisional="D2",
        yoga_keywords=["dhana", "vyaya"],
        condition_malefic_grahas=["Rahu", "Ketu"],
        citations=["BPHS ch.2 (dhana)", "BPHS ch.12 (vyaya)", "BPHS ch.28"],
    ),
    "property_acquisition": KaryatvaMap(
        event_class_id="property_acquisition",
        primary_bhava=[4],
        karaka_grahas=["Mars", "Venus"],
        dusthana_required=False,
        divisional="D4",
        yoga_keywords=["grha", "kshetra", "bhumi"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.11 (sukha-bhava)", "BPHS ch.28"],
    ),
    "bereavement": KaryatvaMap(
        event_class_id="bereavement",
        primary_bhava=[8, 12, 2],
        karaka_grahas=["Saturn", "Ketu"],
        dusthana_required=False,
        divisional="D8",
        yoga_keywords=["marana", "maraka"],
        condition_malefic_grahas=["Mars", "Rahu"],
        citations=["BPHS maraka-sthana (2nd/7th lords + occupants as maraka)", "BPHS ch.12 (8th bhava, ayus/marana-vicara)", "BPHS ch.11 (12th bhava, vyaya/loss)", "BPHS ch.6 (ashtamamsha)"],
    ),
    "parental_event": KaryatvaMap(
        event_class_id="parental_event",
        primary_bhava=[4, 9],
        karaka_grahas=["Moon", "Sun"],
        dusthana_required=False,   # non-death parental events; bereavement (death) stays the separate, dusthana-eligible class
        divisional="D12",
        yoga_keywords=["matru", "pitru"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=["BPHS ch.4 (mother)", "BPHS ch.9 (father)", "BPHS ch.6 (dwadashamsha)"],
    ),
    "spiritual_turn": KaryatvaMap(
        event_class_id="spiritual_turn",
        primary_bhava=[9, 12, 5],
        karaka_grahas=["Jupiter", "Ketu"],
        dusthana_required=False,
        divisional="D20",
        yoga_keywords=["dharma", "moksha", "purva_punya"],
        condition_malefic_grahas=["Rahu"],
        citations=["BPHS ch.24 (dharma)", "BPHS ch.12 (moksha)", "BPHS ch.28"],
    ),
    # DR-13 provisional classes: domain-matching fallback
    "achievement_recognition": KaryatvaMap(
        event_class_id="achievement_recognition",
        primary_bhava=[10, 11],
        karaka_grahas=["Sun", "Jupiter"],
        provisional=True,
        citations=["DR-13 provisional"],
    ),
    "financial_deception": KaryatvaMap(
        event_class_id="financial_deception",
        primary_bhava=[8, 12],
        karaka_grahas=["Rahu"],
        provisional=True,
        citations=["DR-13 provisional"],
    ),
    "psychological_arc": KaryatvaMap(
        event_class_id="psychological_arc",
        primary_bhava=[5, 8, 12],
        karaka_grahas=["Moon", "Ketu"],
        provisional=True,
        citations=["DR-13 provisional"],
    ),
    "birth_anchor": KaryatvaMap(
        event_class_id="birth_anchor",
        primary_bhava=[1],
        karaka_grahas=["Sun"],
        provisional=True,
        citations=["DR-13 provisional"],
    ),
    "travel_event": KaryatvaMap(
        event_class_id="travel_event",
        primary_bhava=[3, 9, 12],
        karaka_grahas=["Moon", "Rahu"],
        provisional=True,
        citations=["DR-13 provisional"],
    ),
}


def get_karyatva(event_class_id: str) -> KaryatvaMap | None:
    """Return the karyatva map for an event class, or None if not mapped."""
    return KARYATVA_REGISTRY.get(event_class_id)
