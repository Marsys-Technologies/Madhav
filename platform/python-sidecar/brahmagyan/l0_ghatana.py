"""
brahmagyan.l0_ghatana — bg_ghatana L0 global seed.

Populates brahma_event_ontology (22 life-event classes) and
brahma_activity_ontology (12 electional activity classes).

Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §5–§6.
Idempotency: L0 = ON CONFLICT DO UPDATE (global, not per-chart).
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Event ontology (22 life-event classes) ────────────────────────────────────

EVENT_CLASSES: list[dict] = [
    {
        "event_class_id": "career_entry",
        "name_en": "Career Entry",
        "domain": "career",
        "lel_category": "career",
        "signature_model": {
            "houses": ["10", "6", "1"], "lords": ["10L", "6L"],
            "karakas": ["Sun", "Saturn"], "vargas": ["D10"],
            "dasha_rules": "MD/AD of 10th-related",
            "transit_triggers": "Jupiter/Saturn transit to 10th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["career_change"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.55, "band_26_40": 0.20, "band_41_60": 0.05, "band_60_plus": 0.01},
        "citations": ["BPHS ch.10 (karma-bhava)", "Phaladeepika ch.10"],
    },
    {
        "event_class_id": "career_advancement",
        "name_en": "Career Advancement",
        "domain": "career",
        "lel_category": "career",
        "signature_model": {
            "houses": ["10", "11"], "lords": ["10L", "11L"],
            "karakas": ["Sun"], "vargas": ["D10"],
            "dasha_rules": "benefic transit to 10th",
            "transit_triggers": "Jupiter to 10th/11th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["career_entry"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.45, "band_41_60": 0.35, "band_60_plus": 0.05},
        "citations": ["BPHS ch.10", "Phaladeepika ch.10"],
    },
    {
        "event_class_id": "career_change",
        "name_en": "Career Change",
        "domain": "career",
        "lel_category": "career",
        "signature_model": {
            "houses": ["10", "3", "9"], "lords": ["10L"],
            "karakas": ["Rahu"], "vargas": ["D10"],
            "dasha_rules": "dasha-sandhi; parivartana periods",
            "transit_triggers": "Rahu transit to 10th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["career_entry", "transition"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.20, "band_26_40": 0.45, "band_41_60": 0.30, "band_60_plus": 0.05},
        "citations": ["BPHS ch.10", "standard Rahu transit rules"],
    },
    {
        "event_class_id": "career_setback",
        "name_en": "Career Setback",
        "domain": "career",
        "lel_category": "career",
        "signature_model": {
            "houses": ["10", "6", "8", "12"], "lords": ["10L afflicted"],
            "karakas": ["Saturn", "Rahu"], "vargas": ["D10"],
            "dasha_rules": "adverse 6/8/12 dasha",
            "transit_triggers": "adverse Saturn transit to 10th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["career_change"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.10, "band_26_40": 0.35, "band_41_60": 0.35, "band_60_plus": 0.15},
        "citations": ["BPHS dusthana chapter"],
    },
    {
        "event_class_id": "business_launch",
        "name_en": "Business Launch",
        "domain": "career",
        "lel_category": "career",
        "signature_model": {
            "houses": ["7", "10", "11"], "lords": ["7L", "10L", "11L"],
            "karakas": ["Mercury", "Jupiter"], "vargas": ["D10"],
            "dasha_rules": "strong 7/10/11 dasha",
            "transit_triggers": "Jupiter to 10th or 11th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["career_entry"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.50, "band_41_60": 0.30, "band_60_plus": 0.05},
        "citations": ["BPHS ch.7,10,11"],
    },
    {
        "event_class_id": "education_milestone",
        "name_en": "Education Milestone",
        "domain": "education",
        "lel_category": "education",
        "signature_model": {
            "houses": ["4", "5", "9"], "lords": ["4L", "5L", "9L"],
            "karakas": ["Mercury", "Jupiter"], "vargas": ["D24"],
            "dasha_rules": "benefic 4/5/9 dasha",
            "transit_triggers": "Jupiter transit to 5th or 9th",
        },
        "magnitude_floor": "moderate",
        "adjacency": [],
        "base_rate_by_age": {"band_0_12": 0.10, "band_13_25": 0.70, "band_26_40": 0.25, "band_41_60": 0.05, "band_60_plus": 0.01},
        "citations": ["BPHS ch.4,5,9", "Jaimini Sutram (vidya-karaka)"],
    },
    {
        "event_class_id": "exam_outcome",
        "name_en": "Exam Outcome",
        "domain": "education",
        "lel_category": "education",
        "signature_model": {
            "houses": ["5", "9"], "lords": ["5L"],
            "karakas": ["Mercury"], "vargas": ["D24"],
            "dasha_rules": "5th lord period",
            "transit_triggers": "transit to 5th",
        },
        "magnitude_floor": "trivial",
        "adjacency": ["education_milestone"],
        "base_rate_by_age": {"band_0_12": 0.15, "band_13_25": 0.75, "band_26_40": 0.20, "band_41_60": 0.03, "band_60_plus": 0.01},
        "citations": ["BPHS ch.5"],
    },
    {
        "event_class_id": "marriage",
        "name_en": "Marriage",
        "domain": "relationship",
        "lel_category": "relationship",
        "signature_model": {
            "houses": ["7", "2"], "lords": ["7L"],
            "karakas": ["Venus"], "vargas": ["D9"],
            "dasha_rules": "7th-lord or Venus dasha/antardasha",
            "transit_triggers": "Jupiter/Saturn transit to 7th; Jaimini DK activation",
        },
        "magnitude_floor": "significant",
        "adjacency": ["partnership_formed"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.45, "band_26_40": 0.45, "band_41_60": 0.10, "band_60_plus": 0.02},
        "citations": ["BPHS ch.7 (vivaha)", "Phaladeepika kalatra-bhava", "Jaimini Sutram DK"],
    },
    {
        "event_class_id": "romantic_start",
        "name_en": "Romantic Relationship Start",
        "domain": "relationship",
        "lel_category": "relationship",
        "signature_model": {
            "houses": ["5", "7"], "lords": ["5L", "7L"],
            "karakas": ["Venus"], "vargas": ["D9"],
            "dasha_rules": "Venus/5th-lord period",
            "transit_triggers": "benefic transit to 5th or 7th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["marriage"],
        "base_rate_by_age": {"band_0_12": 0.05, "band_13_25": 0.55, "band_26_40": 0.35, "band_41_60": 0.10, "band_60_plus": 0.02},
        "citations": ["BPHS ch.5,7"],
    },
    {
        "event_class_id": "separation",
        "name_en": "Separation",
        "domain": "relationship",
        "lel_category": "relationship",
        "signature_model": {
            "houses": ["6", "8", "12"], "lords": ["7L afflicted"],
            "karakas": ["Rahu", "Saturn", "Mars"], "vargas": ["D9"],
            "dasha_rules": "adverse dasha for 7th",
            "transit_triggers": "adverse Saturn/Rahu transit to 7th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["marriage"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.40, "band_41_60": 0.30, "band_60_plus": 0.10},
        "citations": ["BPHS ch.7 (vivaha-vighna)"],
    },
    {
        "event_class_id": "childbirth",
        "name_en": "Childbirth",
        "domain": "progeny",
        "lel_category": "family",
        "signature_model": {
            "houses": ["5", "1"], "lords": ["5L"],
            "karakas": ["Jupiter"], "vargas": ["D7"],
            "dasha_rules": "5th-lord or Jupiter dasha",
            "transit_triggers": "Jupiter transit to 5th",
        },
        "magnitude_floor": "significant",
        "adjacency": [],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.30, "band_26_40": 0.60, "band_41_60": 0.08, "band_60_plus": 0.00},
        "citations": ["BPHS ch.5 (putra-bhava)", "Jaimini Sutram putra-karaka"],
    },
    {
        "event_class_id": "parental_event",
        "name_en": "Parental Event",
        "domain": "family",
        "lel_category": "family",
        "signature_model": {
            "houses": ["4", "9"], "lords": ["4L", "9L"],
            "karakas": ["Moon", "Sun"], "vargas": ["D12"],
            "dasha_rules": "4th/9th lord dasha",
            "transit_triggers": "Saturn/Ketu transit to 4th or 9th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["bereavement"],
        "base_rate_by_age": {"band_0_12": 0.05, "band_13_25": 0.20, "band_26_40": 0.35, "band_41_60": 0.35, "band_60_plus": 0.20},
        "citations": ["BPHS ch.4 (matru-bhava), ch.9 (pitru-bhava)"],
    },
    {
        "event_class_id": "bereavement",
        "name_en": "Bereavement",
        "domain": "transition",
        "lel_category": "loss",
        "signature_model": {
            "houses": ["8", "12", "2"], "lords": ["8L", "maraka lords (2L/7L)"],
            "karakas": ["Saturn", "Ketu"], "vargas": ["D8"],
            "dasha_rules": "maraka dasha",
            "transit_triggers": "adverse Saturn/Ketu transit to 1st or 8th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["parental_event"],
        # JL-009 (native glance 2026-07-07): bereavement re-weighted to rise with
        # elder-cohort mortality; ontology → v1.1 (migration 421). Kept in sync here so a
        # re-seed does not revert the ratified edit via ON CONFLICT DO UPDATE.
        "base_rate_by_age": {"band_0_12": 0.10, "band_13_25": 0.15, "band_26_40": 0.30, "band_41_60": 0.35, "band_60_plus": 0.40},
        "citations": ["BPHS ch.8,2 (maraka/nidhan)"],
    },
    {
        "event_class_id": "major_gain",
        "name_en": "Major Financial Gain",
        "domain": "wealth",
        "lel_category": "finance",
        "signature_model": {
            "houses": ["2", "11"], "lords": ["2L", "11L"],
            "karakas": ["Jupiter", "Mercury"], "vargas": ["D2"],
            "dasha_rules": "dhana-yoga dasha",
            "transit_triggers": "Jupiter transit to 2nd or 11th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["property_acquisition"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.20, "band_26_40": 0.40, "band_41_60": 0.30, "band_60_plus": 0.10},
        "citations": ["BPHS ch.2,11 (dhana-bhava)"],
    },
    {
        "event_class_id": "major_loss",
        "name_en": "Major Financial Loss",
        "domain": "wealth",
        "lel_category": "loss",
        "signature_model": {
            "houses": ["2", "11", "12"], "lords": ["2L/11L afflicted", "12L active"],
            "karakas": ["Saturn", "Rahu"], "vargas": ["D2"],
            "dasha_rules": "adverse dasha for 2nd",
            "transit_triggers": "adverse Saturn/Rahu transit to 2nd",
        },
        "magnitude_floor": "significant",
        "adjacency": ["career_setback"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.40, "band_41_60": 0.30, "band_60_plus": 0.15},
        "citations": ["BPHS ch.12 (vyaya)"],
    },
    {
        "event_class_id": "property_acquisition",
        "name_en": "Property Acquisition",
        "domain": "residence",
        "lel_category": "finance",
        "signature_model": {
            "houses": ["4"], "lords": ["4L"],
            "karakas": ["Mars"], "vargas": ["D4"],
            "dasha_rules": "4th-lord dasha",
            "transit_triggers": "benefic transit to 4th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["major_gain", "relocation"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.50, "band_41_60": 0.30, "band_60_plus": 0.05},
        "citations": ["BPHS ch.4 (bhumi-bhava)"],
    },
    {
        "event_class_id": "relocation",
        "name_en": "Relocation",
        "domain": "residence",
        "lel_category": "residential",
        "signature_model": {
            "houses": ["4", "3", "12"], "lords": ["4L", "3L"],
            "karakas": ["Moon", "Rahu"], "vargas": ["D4"],
            "dasha_rules": "dasha-change or 4L in transit to dusthana",
            "transit_triggers": "Rahu transit to 4th or 12th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["property_acquisition", "foreign_settlement"],
        "base_rate_by_age": {"band_0_12": 0.05, "band_13_25": 0.30, "band_26_40": 0.40, "band_41_60": 0.20, "band_60_plus": 0.05},
        "citations": ["BPHS ch.4,12"],
    },
    {
        "event_class_id": "foreign_settlement",
        "name_en": "Foreign Settlement",
        "domain": "travel",
        "lel_category": "travel",
        "signature_model": {
            "houses": ["12", "9", "7"], "lords": ["12L", "9L"],
            "karakas": ["Rahu"], "vargas": ["D9", "D12"],
            "dasha_rules": "Rahu dasha; 12L period",
            "transit_triggers": "Rahu transit to 9th or 12th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["relocation"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.35, "band_26_40": 0.45, "band_41_60": 0.15, "band_60_plus": 0.02},
        "citations": ["BPHS ch.12 (videsh)"],
    },
    {
        "event_class_id": "illness_acute",
        "name_en": "Acute Illness",
        "domain": "health",
        "lel_category": "health",
        "signature_model": {
            "houses": ["6", "8"], "lords": ["6L", "8L"],
            "karakas": ["Mars", "Saturn"], "vargas": ["D30"],
            "dasha_rules": "adverse transit to lagna or 6th",
            "transit_triggers": "Mars/Saturn adverse transit to 6th or 1st",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["surgery", "chronic_onset"],
        "base_rate_by_age": {"band_0_12": 0.15, "band_13_25": 0.20, "band_26_40": 0.25, "band_41_60": 0.30, "band_60_plus": 0.40},
        "citations": ["BPHS ch.6 (roga-bhava)", "Phaladeepika ch.6"],
    },
    {
        "event_class_id": "chronic_onset",
        "name_en": "Chronic Illness Onset",
        "domain": "health",
        "lel_category": "health",
        "signature_model": {
            "houses": ["6", "8"], "lords": ["6L", "8L"],
            "karakas": ["Saturn"], "vargas": ["D30"],
            "dasha_rules": "Sade-Sati; Saturn dasha",
            "transit_triggers": "Saturn transit to 1st, 4th, or 8th",
        },
        "magnitude_floor": "significant",
        "adjacency": ["illness_acute"],
        "base_rate_by_age": {"band_0_12": 0.02, "band_13_25": 0.08, "band_26_40": 0.20, "band_41_60": 0.35, "band_60_plus": 0.45},
        "citations": ["BPHS ch.6,8; Sade-Sati rules"],
    },
    {
        "event_class_id": "surgery",
        "name_en": "Surgery",
        "domain": "health",
        "lel_category": "health",
        "signature_model": {
            "houses": ["6", "8"], "lords": ["6L", "8L"],
            "karakas": ["Mars"], "vargas": ["D30"],
            "dasha_rules": "Mars/Ketu dasha-transit",
            "transit_triggers": "Mars transit to 6th or 8th with simultaneous Ketu aspect",
        },
        "magnitude_floor": "significant",
        "adjacency": ["illness_acute"],
        "base_rate_by_age": {"band_0_12": 0.05, "band_13_25": 0.10, "band_26_40": 0.20, "band_41_60": 0.30, "band_60_plus": 0.35},
        "citations": ["BPHS ch.6 (shastra-vrana)", "Phaladeepika on Mars aspects"],
    },
    {
        "event_class_id": "spiritual_turn",
        "name_en": "Spiritual Turn",
        "domain": "spirituality",
        "lel_category": "spiritual",
        "signature_model": {
            "houses": ["9", "12", "5"], "lords": ["9L", "12L"],
            "karakas": ["Jupiter", "Ketu"], "vargas": ["D20"],
            "dasha_rules": "Ketu or Jupiter dasha",
            "transit_triggers": "Jupiter transit to 9th or 12th",
        },
        "magnitude_floor": "moderate",
        "adjacency": ["transition"],
        "base_rate_by_age": {"band_0_12": 0.00, "band_13_25": 0.15, "band_26_40": 0.25, "band_41_60": 0.35, "band_60_plus": 0.45},
        "citations": ["BPHS ch.9 (dharma), ch.12 (moksha)", "Jaimini Sutram moksha-karaka"],
    },
]

# ── Activity ontology (12 electional classes) ─────────────────────────────────

ACTIVITY_CLASSES: list[dict] = [
    {
        "activity_class_id": "marriage",
        "name_en": "Marriage",
        "significators": {
            "strengthen_grahas": ["Venus", "Jupiter"],
            "strengthen_houses": ["7"],
            "strengthen_varga": "D9",
            "avoid": ["6th/8th/12th afflicting 7th", "Bhadra tithi", "Venus/Jupiter combust"],
        },
        "fructification_rules": {
            "timing_anchor": "tara+candra-bala",
            "panchanga_rules": "Venus and Jupiter dignified; avoid Ritu-sandhya",
            "classical_source": "Muhurta-Chintamani ch.4",
        },
        "related_event_class": "marriage",
        "citations": ["Muhurta-Chintamani ch.4", "BPHS muhurta chapter"],
    },
    {
        "activity_class_id": "business_start",
        "name_en": "Business Start",
        "significators": {
            "strengthen_grahas": ["Mercury", "Jupiter", "Sun"],
            "strengthen_houses": ["10", "11"],
            "strengthen_varga": "D10",
            "avoid": ["8th lord hora", "Rahu-kala", "weak 10L"],
        },
        "fructification_rules": {
            "timing_anchor": "strong lagna+10th at election",
            "panchanga_rules": "waxing Moon; avoid Krishna-paksha",
            "classical_source": "Muhurta-Chintamani ch.7",
        },
        "related_event_class": "business_launch",
        "citations": ["Muhurta-Chintamani ch.7"],
    },
    {
        "activity_class_id": "contract_signing",
        "name_en": "Contract Signing",
        "significators": {
            "strengthen_grahas": ["Mercury"],
            "strengthen_houses": ["3", "11"],
            "strengthen_varga": "D1",
            "avoid": ["Mercury combust/retrograde", "void Moon"],
        },
        "fructification_rules": {
            "timing_anchor": "Mercury dignified; waxing Moon",
            "panchanga_rules": "avoid Panchami/Saptami (vyatipata)",
            "classical_source": "standard Jyotish muhurta texts",
        },
        "related_event_class": None,
        "citations": ["Standard muhurta texts"],
    },
    {
        "activity_class_id": "travel_journey",
        "name_en": "Travel Journey",
        "significators": {
            "strengthen_grahas": ["Moon", "Mercury"],
            "strengthen_houses": ["3", "9", "12"],
            "strengthen_varga": "D1",
            "avoid": ["durmuhurta", "Moon in 8th from janma-rashi"],
        },
        "fructification_rules": {
            "timing_anchor": "favorable candra-bala; disha-shul clear",
            "panchanga_rules": "Moon in 3/6/10/11 from birth Moon; avoid Bharani/Krittika/Ashlesha on travel day",
            "classical_source": "Muhurta-Chintamani ch.8",
        },
        "related_event_class": "relocation",
        "citations": ["Muhurta-Chintamani ch.8"],
    },
    {
        "activity_class_id": "property_purchase",
        "name_en": "Property Purchase",
        "significators": {
            "strengthen_grahas": ["Mars", "Saturn"],
            "strengthen_houses": ["4"],
            "strengthen_varga": "D4",
            "avoid": ["4L weak", "adverse Saturn transit", "Mangal in 4th from lagna"],
        },
        "fructification_rules": {
            "timing_anchor": "4th lord strong; Mars dignified",
            "panchanga_rules": "avoid Shraddha-paksha; avoid Krishna-8th",
            "classical_source": "Muhurta-Chintamani ch.10",
        },
        "related_event_class": "property_acquisition",
        "citations": ["Muhurta-Chintamani ch.10"],
    },
    {
        "activity_class_id": "medical_procedure",
        "name_en": "Medical Procedure",
        "significators": {
            "strengthen_grahas": ["controlled Mars"],
            "strengthen_houses": ["6", "8"],
            "strengthen_varga": "D30",
            "avoid": ["Krishna-chaturdashi", "afflicted lagna", "Moon in surgery-site rashi"],
        },
        "fructification_rules": {
            "timing_anchor": "benefic lagna; Moon away from affected body part",
            "panchanga_rules": "avoid Bharani/Krittika/Moola nakshatra for elective surgery",
            "classical_source": "BPHS muhurta + surgical nakshatra rules",
        },
        "related_event_class": "surgery",
        "citations": ["BPHS muhurta", "surgical nakshatra rules"],
    },
    {
        "activity_class_id": "education_start",
        "name_en": "Education Start",
        "significators": {
            "strengthen_grahas": ["Mercury", "Jupiter"],
            "strengthen_houses": ["4", "5"],
            "strengthen_varga": "D24",
            "avoid": ["Mercury combust", "weak 5L"],
        },
        "fructification_rules": {
            "timing_anchor": "Vasanta-panchami-type windows; dignified Mercury/Jupiter",
            "panchanga_rules": "Pushya/Hasta/Ashwini nakshatra favored",
            "classical_source": "standard Vidyarambha muhurta",
        },
        "related_event_class": "education_milestone",
        "citations": ["Vidyarambha muhurta tradition"],
    },
    {
        "activity_class_id": "spiritual_initiation",
        "name_en": "Spiritual Initiation",
        "significators": {
            "strengthen_grahas": ["Jupiter", "Ketu"],
            "strengthen_houses": ["9", "12"],
            "strengthen_varga": "D20",
            "avoid": ["broadly permissive"],
        },
        "fructification_rules": {
            "timing_anchor": "Jupiter/Moon strong; auspicious tithi/nakshatra",
            "panchanga_rules": "Ekadashi/Purnima/auspicious solar ingress",
            "classical_source": "Diksha-vidhi tradition",
        },
        "related_event_class": "spiritual_turn",
        "citations": ["Diksha-vidhi tradition", "BPHS ch.9"],
    },
    {
        "activity_class_id": "vehicle_purchase",
        "name_en": "Vehicle Purchase",
        "significators": {
            "strengthen_grahas": ["Venus"],
            "strengthen_houses": ["4"],
            "strengthen_varga": "D4",
            "avoid": ["Venus combust", "4L weak"],
        },
        "fructification_rules": {
            "timing_anchor": "Venus dignified; benefic Moon",
            "panchanga_rules": "avoid Rahu-kala; Rohini/Mrigashira favored",
            "classical_source": "Muhurta-Chintamani ch.10",
        },
        "related_event_class": None,
        "citations": ["Muhurta-Chintamani ch.10"],
    },
    {
        "activity_class_id": "financial_investment",
        "name_en": "Financial Investment",
        "significators": {
            "strengthen_grahas": ["Jupiter", "Mercury"],
            "strengthen_houses": ["2", "11"],
            "strengthen_varga": "D2",
            "avoid": ["8th lord periods", "void Moon"],
        },
        "fructification_rules": {
            "timing_anchor": "dhana-yoga active; waxing Moon",
            "panchanga_rules": "avoid Panchami/Chaturdashi; Pushya favored",
            "classical_source": "standard dhana muhurta",
        },
        "related_event_class": "major_gain",
        "citations": ["Standard dhana muhurta tradition"],
    },
    {
        "activity_class_id": "griha_pravesh",
        "name_en": "Griha Pravesh (Home Entry)",
        "significators": {
            "strengthen_grahas": ["Moon", "Jupiter"],
            "strengthen_houses": ["4"],
            "strengthen_varga": "D4",
            "avoid": ["Chaturmasya prohibitions", "weak Moon"],
        },
        "fructification_rules": {
            "timing_anchor": "classical griha-pravesha nakshatras (Rohini/Hasta/Pushya/Anuradha)",
            "panchanga_rules": "Shukla-paksha; avoid Shunya tithi; benefic lagna",
            "classical_source": "Griha-pravesha-paddhati",
        },
        "related_event_class": "property_acquisition",
        "citations": ["Griha-pravesha-paddhati", "BPHS muhurta"],
    },
    {
        "activity_class_id": "ceremony_naming",
        "name_en": "Naming Ceremony",
        "significators": {
            "strengthen_grahas": ["Jupiter", "Moon"],
            "strengthen_houses": ["5"],
            "strengthen_varga": "D1",
            "avoid": ["durmuhurta", "Rikta tithi (4/9/14)"],
        },
        "fructification_rules": {
            "timing_anchor": "benefic Moon-nakshatra; Shukla-paksha",
            "panchanga_rules": "Namakarana muhurta: day 10-12 after birth; Pushya/Hasta/Shravana favored",
            "classical_source": "Namakarana-paddhati",
        },
        "related_event_class": "childbirth",
        "citations": ["Namakarana-paddhati"],
    },
]


def seed_ghatana(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Upsert EVENT_CLASSES + ACTIVITY_CLASSES into brahma_event_ontology
    and brahma_activity_ontology.

    Returns {"brahma_event_ontology": N, "brahma_activity_ontology": M}.

    autocommit: if False, caller owns the transaction (pass False from asset_runner).
    """
    if dry_run:
        logger.info("[L0/ghatana] dry_run — would upsert %d events + %d activities",
                    len(EVENT_CLASSES), len(ACTIVITY_CLASSES))
        return {
            "brahma_event_ontology": len(EVENT_CLASSES),
            "brahma_activity_ontology": len(ACTIVITY_CLASSES),
        }

    with conn.cursor() as cur:
        for table in ("brahma_event_ontology", "brahma_activity_ontology"):
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
            if cur.fetchone()["count"] == 0:
                raise RuntimeError(
                    f"{table} table does not exist — apply migration 388 first."
                )

        # ── brahma_event_ontology ─────────────────────────────────────────────
        for ec in EVENT_CLASSES:
            cur.execute(
                """
                INSERT INTO brahma_event_ontology
                  (event_class_id, name_en, domain, lel_category,
                   signature_model, magnitude_floor, adjacency,
                   base_rate_by_age, citations, version)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s, '1.1')
                ON CONFLICT (event_class_id)
                DO UPDATE SET
                    signature_model  = EXCLUDED.signature_model,
                    magnitude_floor  = EXCLUDED.magnitude_floor,
                    adjacency        = EXCLUDED.adjacency,
                    base_rate_by_age = EXCLUDED.base_rate_by_age,
                    citations        = EXCLUDED.citations,
                    version          = EXCLUDED.version
                """,
                (
                    ec["event_class_id"],
                    ec["name_en"],
                    ec["domain"],
                    ec["lel_category"],
                    json.dumps(ec["signature_model"]),
                    ec["magnitude_floor"],
                    json.dumps(ec.get("adjacency") or []),
                    json.dumps(ec["base_rate_by_age"]),
                    ec.get("citations"),
                ),
            )

        # ── brahma_activity_ontology ──────────────────────────────────────────
        for ac in ACTIVITY_CLASSES:
            cur.execute(
                """
                INSERT INTO brahma_activity_ontology
                  (activity_class_id, name_en, significators,
                   fructification_rules, related_event_class, citations, version)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, '1.0')
                ON CONFLICT (activity_class_id)
                DO UPDATE SET
                    significators        = EXCLUDED.significators,
                    fructification_rules = EXCLUDED.fructification_rules,
                    citations            = EXCLUDED.citations
                """,
                (
                    ac["activity_class_id"],
                    ac["name_en"],
                    json.dumps(ac["significators"]),
                    json.dumps(ac["fructification_rules"]),
                    ac["related_event_class"],
                    ac.get("citations"),
                ),
            )

    if autocommit:
        conn.commit()

    logger.info("[L0/ghatana] upserted %d events + %d activities",
                len(EVENT_CLASSES), len(ACTIVITY_CLASSES))
    return {
        "brahma_event_ontology": len(EVENT_CLASSES),
        "brahma_activity_ontology": len(ACTIVITY_CLASSES),
    }
