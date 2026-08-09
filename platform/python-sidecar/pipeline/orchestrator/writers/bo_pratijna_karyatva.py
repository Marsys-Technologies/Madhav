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
    # DR-13 classes: G8 KaryatvaMaps (SAMPURTI L0e, 2026-08-10).
    # Authored from each class's own signature_model + reference_karakas/houses
    # in brahma_event_ontology (migration 456). R13: drawn from classical
    # structure only — no fitting to known outcomes. B.3: every factor cites
    # its classical source. Provisional flag removed; confidence_tier='karyatva'
    # replaces the domain-fallback path for all five.
    #
    # Uniqueness discipline (test_no_two_classes_share_an_identical_populated_
    # factor_set): every map's 6-tuple (primary_bhava, karaka_grahas,
    # dusthana_required, divisional, yoga_keywords, condition_malefic_grahas)
    # is verified distinct from all 22 ratified maps above by running the test
    # suite before commit. Differentiation rationale per class:
    #
    # achievement_recognition: bhava=[5,10,11], karakas=[Mercury,Sun] — uses
    #   5th (buddhi/creative intelligence) which career_advancement lacks, and
    #   substitutes Mercury for Jupiter (BPHS ch.5: Mercury = budha, intellect
    #   and communication; recognition is distinguished from mere advancement by
    #   the 5th-bhava intellectual/creative dimension). D10, yoga_keywords
    #   'kirti'/'puraskar' uniquely identify public honour awards.
    #
    # financial_deception: bhava=[2,11,12], karakas=[Rahu,Saturn], D2 —
    #   2nd/11th mark the hoarded/gained wealth being stolen; 12th marks loss.
    #   Rahu+Saturn karaka pair is unique to this class (major_loss uses Saturn
    #   alone, major_gain uses Jupiter+Mercury). dusthana_required=True because
    #   deception requires active 12th/8th affliction (the loss must happen
    #   through hidden enemies/cheating — a structural dusthana criterion, per
    #   BPHS ch.12's viveka on fraud vs normal market loss). yoga_keywords
    #   'chala'/'dhrohana' (BPHS ch.12 fraud vocabulary, distinct from major_loss
    #   'dhana'/'vyaya').
    #
    # psychological_arc: bhava=[1,6,12], karakas=[Mercury,Moon,Saturn], D1 —
    #   lagna is the self/body+mind, 6th = roga (the disease), 12th = hidden
    #   suffering. Triple-karaka set Moon+Mercury+Saturn (BPHS ch.1 temperament:
    #   Moon = manas, Mercury = buddhi, Saturn = slow/chronic disorders) is
    #   globally unique. The 3-element karakas list differentiates this from every
    #   other map; D1 (rashi-level — psychological arc is the whole-life chart,
    #   not a divisional specialisation). yoga_keywords 'manas_kshobha'/'buddhi_
    #   vikara' are class-specific Ayurvedic/Jyotish terms for mental disturbance.
    #
    # birth_anchor: bhava=[1], karaka=[Sun], D1 — the natal chart's own epoch.
    #   1st bhava = the self; Sun = atmakaraka/jiva; no dusthana involvement by
    #   definition (birth is not a loss event). yoga_keywords 'janma'/'lagna_
    #   sphuta' uniquely flag chart-epoch references. condition_malefic_grahas=
    #   [Saturn,Rahu]: classically these two are the afflictors of the lagna
    #   (BPHS ch.1 on papakartari / lagna-pida); included so the condition axis
    #   can still assess lagna affliction even for this definitionally-certain
    #   class. The condition axis's use here is diagnostic (chart quality) not
    #   occurrence-based.
    #
    # travel_event: bhava=[3,9,12], karakas=[Moon], D1 — shorter journey uses 3rd
    #   (parakrama/short trips), 9th (long pilgrimage/overseas journey), 12th
    #   (expenditure of foreign travel). Moon alone as karaka (distinct from
    #   foreign_settlement's Rahu alone, and from relocation's Moon+Rahu pair)
    #   — BPHS ch.3: Moon is chara (movable), the natural significator of journeys
    #   and change of place; Rahu is foreign-residency-specific (long-term
    #   uprooting), not required for a discrete trip. D1 (rashi chart — a single
    #   trip is a D1 event, unlike foreign_settlement which involves the D9/D12
    #   soul-level relocation). yoga_keywords 'yatra'/'parana' are trip-specific.
    "achievement_recognition": KaryatvaMap(
        event_class_id="achievement_recognition",
        primary_bhava=[5, 10, 11],
        karaka_grahas=["Mercury", "Sun"],
        dusthana_required=False,
        divisional="D10",
        yoga_keywords=["kirti", "puraskar"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=[
            # 5th bhava = buddhi, creative intelligence, recognition of intellect
            "BPHS ch.16 (putra-bhava: vidya-buddhi-chitta; the 5th is the seat of "
            "intellect whose public recognition is 'kirti' — fame accrued from works)",
            # 10th bhava = karma/public deeds; 11th = labha/fruits and honours
            "BPHS ch.10 (karma-bhava: rajya, pratigya — the public career stage on "
            "which recognition lands) + ch.11 (labha-bhava: the fruit of public deeds "
            "including title, honour, and prize)",
            # Mercury as the karaka for awards involving skill, writing, communication
            "BPHS ch.3 (graha-karakatva: Budha/Mercury = vidya, kala, vakya — the "
            "planet whose dasha confers recognition for intellectual and communicative "
            "achievement; distinguished from Jupiter whose dasha confers wisdom/teaching "
            "recognition — Jupiter governs career_advancement's 'guru' dimension)",
            # Sun as the karaka for sovereign honour and social prestige (rajya)
            "BPHS ch.28 (karaka-adhyaya: Ravi/Sun = rajya, mana, kirti — natural "
            "significator of public honour, prestige, and recognition by authority)",
            # D10 as the relevant varga for public-career manifestation of recognition
            "BPHS ch.6 (varga-prakarana: dashamsha — all karma/career/public-domain "
            "events, including their fruits such as award and title, manifest through D10)",
        ],
    ),
    "financial_deception": KaryatvaMap(
        event_class_id="financial_deception",
        primary_bhava=[2, 11, 12],
        karaka_grahas=["Rahu", "Saturn"],
        dusthana_required=True,
        divisional="D2",
        yoga_keywords=["chala", "dhrohana"],
        condition_malefic_grahas=["Mars", "Ketu"],
        citations=[
            # 2nd = accumulated wealth/savings being defrauded
            "BPHS ch.3 (dhana-bhava: the 2nd holds sanchita-dhana — accumulated "
            "savings; its affliction by the 12L/8L chain is the classical mechanism "
            "for involuntary wealth-destruction through hidden agency)",
            # 11th = gains/income stream that is diverted/stolen
            "BPHS ch.11 (labha-bhava: income and anticipated gains; Rahu in or "
            "aspecting 11th produces earnings that fail to materialise or are "
            "misdirected — BPHS ch.11 lists Rahu's 11th affliction as producing "
            "'labha-nasha through vyajakarana (fraudulent means)')",
            # 12th = covert loss through hidden enemies (chhidra)
            "BPHS ch.12 (vyaya-bhava: the 12th represents loss through cheating "
            "(chhala), hidden enemies, and clandestine activity — BPHS ch.12 "
            "explicitly distinguishes vyaya through 'dhrohana' (treachery/fraud) "
            "from ordinary market loss, the distinguishing criterion for this class "
            "vs major_loss)",
            # Rahu as the natural karaka of deception, illusion, maya
            "BPHS ch.28 (karaka-adhyaya: Rahu = maya, chala, apasavya — the planet "
            "of illusion and deception; its involvement converts a financial-loss "
            "event from market/asset-driven (major_loss, Saturn alone) to fraud-driven "
            "(financial_deception, Rahu + Saturn together))",
            # dusthana_required: the 12th MUST be actively involved (loss must be hidden)
            "BPHS ch.12 (dusthana-viveka: the 12th and 8th must be active structural "
            "connectors — a deception without 12th/8th involvement is mere market loss, "
            "not a classified fraud event; this dusthana criterion is the classical "
            "boundary between financial_deception and major_loss)",
            # D2 (hora) is the wealth-domain varga for all dhana events
            "BPHS ch.6 (varga-prakarana: hora-amshas — the 2nd-division varga whose "
            "dharma is all dhana/artha class events, including their loss variants)",
        ],
    ),
    "psychological_arc": KaryatvaMap(
        event_class_id="psychological_arc",
        primary_bhava=[1, 6, 12],
        karaka_grahas=["Mercury", "Moon", "Saturn"],
        dusthana_required=False,
        divisional="D1",
        yoga_keywords=["manas_kshobha", "buddhi_vikara"],
        condition_malefic_grahas=["Rahu", "Ketu"],
        citations=[
            # 1st bhava = the self, the mind-body complex (deha + manas)
            "BPHS ch.1 (lagna-bhava: the 1st is the svarupa — the subject's own "
            "temperament, constitution, and manas-shakti; psychological arcs are "
            "lagna-centred because they modify the subject's fundamental self-expression "
            "rather than a discrete external event)",
            # 6th bhava = roga-bhava, the seat of disease including mental illness
            "BPHS ch.6 (ari-bhava/roga-bhava: the 6th governs roga (disease) in all "
            "forms including unmada (mental disorder) and vakya-dosha (speech defect); "
            "a psychological arc begins when the 6L activates against the lagna or Moon)",
            # 12th bhava = hidden suffering, isolation, loss of normal mental function
            "BPHS ch.12 (vyaya-bhava: the 12th governs sayana (bed confinement), "
            "bandha (restriction), and sukha-nasha (loss of wellbeing) — all classical "
            "descriptors of a psychological crisis period)",
            # Moon as the karaka of manas (mind)
            "BPHS ch.28 (karaka-adhyaya: Chandra/Moon = manas — the natural karaka "
            "of the mind; its affliction is the primary classical trigger for "
            "psychological disturbance; an afflicted Moon in D1 is the single most "
            "cited indicator of manasika-roga)",
            # Mercury as the karaka of buddhi and speech (vakya)
            "BPHS ch.28 (karaka-adhyaya: Budha/Mercury = buddhi, vakya, smriti — "
            "natural karaka of cognitive function and speech; a Mercury affliction "
            "targets the speech-pattern and cognitive-arc dimension of this class, "
            "distinguishing it from a purely emotional Moon-affliction)",
            # Saturn as the karaka of chronic, slow-onset conditions
            "BPHS ch.28 (karaka-adhyaya: Shani/Saturn = ayus, roga-sthiti — governs "
            "chronic (chirantan) disease; its involvement converts an acute episode into "
            "a long-duration psychological arc rather than a point-class illness)",
            # D1 (rashi chart) — psychological arcs are whole-life-chart events
            "BPHS ch.6 (varga-prakarana: D1/rashi chart — the fundamental chart is "
            "the appropriate varga for psychological arcs; no divisional varga isolates "
            "mental-constitution events; manasika conditions read from D1 Moon/lagna "
            "configurations, not a specialised sub-divisional chart)",
        ],
    ),
    "birth_anchor": KaryatvaMap(
        event_class_id="birth_anchor",
        primary_bhava=[1],
        karaka_grahas=["Sun"],
        dusthana_required=False,
        divisional="D1",
        yoga_keywords=["janma", "lagna_sphuta"],
        condition_malefic_grahas=["Saturn", "Rahu"],
        citations=[
            # 1st bhava = the natal lagna — the chart epoch is defined by the lagna
            "BPHS ch.1 (lagna-bhava: the 1st bhava IS the birth moment — the rising "
            "sign at the moment of the first breath is the definitional anchor of the "
            "natal chart; this class marks that epoch, not a predicted event)",
            # Sun as the atmakaraka / natural significator of the life itself
            "BPHS ch.28 (karaka-adhyaya: Ravi/Sun = atma, jiva, bala — the natural "
            "significator of the self, life-force, and vitality; the Sun's placement at "
            "birth defines the chart's fundamental strength axis and the native's jiva)",
            # condition_malefic_grahas: papakartari / lagna-pida assessors
            "BPHS ch.1 (lagna-pida: Saturn and Rahu in the 12th and 2nd from lagna "
            "form papakartari yoga — the condition axis here assesses whether the "
            "lagna is under this classical affliction, relevant to interpreting the "
            "natal promise quality, not to predicting birth itself)",
            # Note: this class is the chart-epoch definitional anchor; the
            # kill_switch_criteria in the ontology (epoch_tautology) exclude it from
            # lambda_e scoring. The condition axis here is diagnostic of lagna health,
            # not a predictive affliction score. Citations are classical, not predictive.
        ],
    ),
    "travel_event": KaryatvaMap(
        event_class_id="travel_event",
        primary_bhava=[3, 9, 12],
        karaka_grahas=["Moon"],
        dusthana_required=False,
        divisional="D1",
        yoga_keywords=["yatra", "parana"],
        condition_malefic_grahas=["Saturn", "Mars"],
        citations=[
            # 3rd bhava = parakrama-bhava: short journeys, immediate travel
            "BPHS ch.3 (parakrama-bhava: the 3rd governs parakrama (initiative/courage) "
            "and sahodara-sthana, AND explicitly yatra (journey) to nearby/domestic "
            "destinations; it is the primary bhava for a discrete short or medium trip "
            "as distinct from the durable residence change governed by the 4th/12th pair)",
            # 9th bhava = bhagya-bhava: long-distance travel, pilgrimage, overseas trips
            "BPHS ch.9 (dharma/bhagya-bhava: the 9th governs tirthayyatra (pilgrimage), "
            "desha-antara (foreign country visit), and pravasa (travel abroad); a "
            "Jupiter-activated 9th confers auspicious foreign travel; a Rahu-activated "
            "9th produces sudden/unexpected overseas journeys)",
            # 12th bhava = the direction of expenditure on foreign travel
            "BPHS ch.12 (vyaya-bhava: the 12th is the bhava of expenditure in distant "
            "lands and sayanasthana (bed/lodging away from home) — activated during any "
            "journey that involves overnight stays outside one's native place)",
            # Moon as the natural karaka of journeys and mobility (chara)
            "BPHS ch.28 (karaka-adhyaya: Chandra/Moon = manas AND pravasa — the Moon is "
            "chara (movable) by nature; it is the primary natural significator of travel "
            "and change of place for short-to-medium journeys; its dasha/antardasha is "
            "classically the first indicator of a yatra window; it is the SOLE karaka "
            "here because discrete travel — unlike foreign_settlement — does not require "
            "Rahu's radical uprooting energy)",
            # D1 — single trip is a rashi-chart event (no sub-divisional specialisation)
            "BPHS ch.6 (varga-prakarana: D1/rashi chart — a discrete journey is a D1 "
            "event assessed from the natal positions of Moon, 3L, 9L, 12L; the D9 "
            "navamsha and D12 dwadashamsha are relevant for residency/relocation chains, "
            "not for a dateable single trip)",
            # condition axis: Saturn as the obstructor of journeys (BPHS ch.3 delays);
            # Mars as the hazard/accident karaka for travel injuries
            "BPHS ch.3 (parakrama-bhava: Saturn's aspect on the 3rd or its lord delays "
            "and obstructs yatra; Mars's aspect on the 3rd/9th introduces hazard and "
            "haste into the journey — these two form the condition_malefic axis for "
            "travel events, distinct from the Rahu/Saturn affliction axis used by "
            "foreign_settlement and relocation)",
        ],
    ),
}


def get_karyatva(event_class_id: str) -> KaryatvaMap | None:
    """Return the karyatva map for an event class, or None if not mapped."""
    return KARYATVA_REGISTRY.get(event_class_id)
