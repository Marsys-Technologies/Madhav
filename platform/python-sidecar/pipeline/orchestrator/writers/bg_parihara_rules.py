"""
pipeline/orchestrator/writers/bg_parihara_rules.py
L0 Brahmagyan global parihāra graph + activity rule tables + factor census
registry writer — seeds bg_parihara_rules, bg_muhurta_activity_rules,
bg_muhurta_factor_census.

ṢAḌ-DARŚANA campaign, registry item 36-substrate + item 41 ("Muhūrta Factor
Census + corpus-gap register + parihāra rule-table extraction"). SHAD_DARSHANA_
BRIEF_v2_0.md §2 names this writer `bg_parihara_rules.py` — "parihāra graph +
activity rule tables + factor census registry (corpus-extracted, citation-
carrying; L0 reference data)".

THIS IS THE CAMPAIGN'S MOST CITATION-SENSITIVE LANE. Every row this writer
builds either (a) REUSES/JOINS a table this codebase already ingested real
corpus content into (`brahma_dosha_catalog`, `panchang_engine.shastra_tables.
EVENT_TABLES`) — never re-authored or re-ingested — or (b) is the census
registry itself, which HONESTLY DISPOSES factors as computed / not_computed /
not_in_corpus, per B.10 ("a factor without a corpus rule table is not_computed
(corpus gap) and becomes an ingestion work item, never improvised").

THREE TABLES
────────────
1. bg_parihara_rules — the doṣa-cancellation (parihāra) graph.
   Source: `brahma_dosha_catalog.cancellation_conditions` (jsonb), JOINED with
   `classical_texts` for a human-readable citation. STRICT FILTER: only rows
   whose `classical_citations` carries a REAL `text_id` are included — 53 of 79
   `brahma_dosha_catalog` rows cite the literal placeholder string
   `"classical_tradition"` and are correctly EXCLUDED (this was verified via a
   live query against the actual corpus DB before writing this module, not
   assumed). Honest scope disclosure: this content is NATAL dosha-bhanga
   (Manglik/Kāla-Sarpa/Kemadruma/Bāla-ariṣṭa/etc conditions) — the corpus has
   NO muhūrta-specific dosha-cancellation content ("Abhijit cancels most
   doshas", dāna-parihāras) at chapter/verse grain. That gap is recorded
   honestly in `bg_muhurta_factor_census`, never fabricated here.

2. bg_muhurta_activity_rules — per-activity (vivāha/gṛha-praveśa/vyāpāra/yātrā/
   property-purchase/mantra-dīkṣā/upāya-ritual/sādhanā-initiation) muhūrta
   factor-quality rules. Source: `panchang_engine.shastra_tables.EVENT_TABLES`
   — 8 already-real, already-cited, already-tested quality tables (MC/BS/MMP/DP
   per-table citations, documented inline in shastra_tables.py §22.1-§22.8),
   REUSED VERBATIM (imported and materialized, never re-authored).

3. bg_muhurta_factor_census — the census/gap register itself (item 41's other
   half): every named classical timing-factor family from KALA_SUPREME_
   ELEVATION_v1_0.md §9 Stage 2's working register, each disposed with a real
   citation or an honest gap + a named ingestion work item. This is a
   hand-curated register (like shastra_tables.py itself is hand-curated data),
   drawn from concrete, verified research into this codebase's actual
   substrate — not invented. See CENSUS_ROWS below for the full register and
   the evidence behind every disposition.

CORPUS GAPS FOUND AND HONESTLY DISCLOSED (not fabricated — see census for full
detail): mṛtyu-yoga, dagdha-yoga (day-quality), hutāśana-yoga, jvālāmukhī-yoga
(the four brief-named combination-yogas panchang_engine does NOT implement;
Muhurta Chintamani ch.17-18 contains untranslated Devanagari OCR content for
two of the four — a real, verified, but currently unusable corpus fragment,
disclosed as such, not claimed as a working citation); Śiva-vāsa (no rite-
specific vāsa sibling beyond Agni/Chandra/Rāhu/Diśā/Nakṣatra/Bhadra exists);
mṛtyu-bhāga; puṣkara-navāṃśa/bhāga; global gaṇḍānta-span factor (the natal
APPLICABILITY concept exists in brahma_dosha_catalog; the chart-independent
TIMING-SPAN factor does not).

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
§2): uses ctx.db_conn exclusively, returns WriterResult, honours ctx.dry_run.
LIGHT writer (`run(ctx)`) — this is a bounded DB-query + in-memory-constant
materialization, nowhere near the heavy-writer threshold.

L0 idempotency (CLAUDE.md §N.3): global reference data, upsert
(`ON CONFLICT ... DO UPDATE`, not DO NOTHING) — unlike bg_cohort/bg_sky_calendar/
bg_muhurta_lattice's from-scratch deterministic computation, this writer
MIRRORS live upstream tables (brahma_dosha_catalog) that could themselves
change over time; a rebuild should REFRESH content to match the current
upstream state, not just skip existing rows.

ZERO LLM use. Deterministic SQL query + Python-constant materialization.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)

SAMPLING_METHOD_VERSION = "parihara_rules_dosha_activity_census_v1"

# ── Table 1: the parihāra (doṣa-cancellation) graph ──────────────────────────

_DOSHA_QUERY = """
    SELECT canonical_id, name_en, category, cancellation_conditions, classical_citations
    FROM brahma_dosha_catalog
    WHERE cancellation_conditions IS NOT NULL
      AND classical_citations IS NOT NULL
      AND jsonb_typeof(classical_citations) = 'array'
      AND EXISTS (
        SELECT 1 FROM jsonb_array_elements(classical_citations) elem
        WHERE elem->>'text_id' IS NOT NULL AND elem->>'text_id' <> 'classical_tradition'
      )
    ORDER BY canonical_id
"""

_TEXT_TITLES_QUERY = "SELECT text_id, title_en FROM classical_texts"


def _extract_conditions(cancellation_conditions: dict[str, Any]) -> list[str]:
    """
    cancellation_conditions is a jsonb dict whose value is either a list[str]
    (the common 'bhanga' key shape) or a single str (the 'applies' key shape
    seen on a couple of self-referential bhanga-record rows). Normalize to a
    flat list of condition strings, in stable key order.
    """
    conditions: list[str] = []
    for _key, value in cancellation_conditions.items():
        if isinstance(value, list):
            conditions.extend(str(v) for v in value)
        elif isinstance(value, str):
            conditions.append(value)
    return conditions


def _build_citation(classical_citations: list[dict[str, Any]], text_titles: dict[str, str]) -> tuple[str, str, int | None]:
    """Return (source_citation, source_text_id, source_chapter) from the first
    real (non-placeholder) citation entry."""
    for cite in classical_citations:
        text_id = cite.get("text_id")
        if not text_id or text_id == "classical_tradition":
            continue
        chapter = cite.get("chapter")
        title = text_titles.get(text_id, text_id)
        citation = f"{title} ({text_id})" + (f", ch.{chapter}" if chapter is not None else "")
        return citation, text_id, chapter
    # Should not happen given the SQL filter, but fail honestly rather than crash.
    return "uncited (filtered defensively — should not occur)", "unknown", None


def fetch_parihara_rows(conn: Any, build_id: str) -> list[dict[str, Any]]:
    """
    Query brahma_dosha_catalog for real-cited cancellation conditions and
    flatten into one row per (dosha, cancellation condition). Read-only query
    on ctx.db_conn (no commit/close — caller owns the connection).
    """
    text_titles: dict[str, str] = {}
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_TEXT_TITLES_QUERY)
        for row in cur.fetchall():
            text_titles[row["text_id"]] = row["title_en"]

    rows: list[dict[str, Any]] = []
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_DOSHA_QUERY)
        for rec in cur.fetchall():
            conditions = _extract_conditions(rec["cancellation_conditions"])
            citation, text_id, chapter = _build_citation(rec["classical_citations"], text_titles)
            for idx, condition_text in enumerate(conditions, start=1):
                rows.append({
                    "dosha_canonical_id": rec["canonical_id"],
                    "dosha_name_en": rec["name_en"],
                    "dosha_category": rec["category"],
                    "cancellation_index": idx,
                    "cancellation_condition_text": condition_text,
                    "net_standing": "cancellable_by_condition",
                    "scope": "natal",
                    "source_text_id": text_id,
                    "source_chapter": chapter,
                    "source_citation": citation,
                    "build_id": build_id,
                })
    return rows


# ── Table 2: per-activity muhūrta rule tables (reused verbatim) ──────────────

# Citation strings verbatim from panchang_engine/shastra_tables.py §22.1-§22.8's
# own inline "Source:" header comments (read directly from source before writing
# this map — never invented).
ACTIVITY_CITATIONS: dict[str, str] = {
    "vivah": "Muhurta Chintamani 3.2 (tithis), 3.5 (nakshatras); classical vara preference",
    "griha_pravesh": "Muhurta Chintamani 4.1 (tithis), 4.3 (nakshatras); Muhurta Martanda (Nrisimha Daivajna) Griha Pravesh chapter",
    "vyapara": "Muhurta Chintamani 5.1 (tithis); Muhurta Martanda Vyapara chapter; Drik Panchang convention",
    "yatra": "Muhurta Chintamani 6.1 (tithis); Brihat Samhita Yatra chapter; Muhurta Martanda Yatra chapter; Drik Panchang convention",
    "property_purchase": "Muhurta Chintamani 7.1; Muhurta Martanda Property chapter; Drik Panchang convention",
    "mantra_initiation": "Muhurta Chintamani 8.1 (diksha muhurta); Brihat Samhita Diksha chapter; Drik Panchang convention",
    "upaya_ritual": "Muhurta Chintamani Upaya chapter; Brihat Parasara Hora Sastra Upaya Shastra chapter; Drik Panchang convention",
    "sadhana_initiation": "Muhurta Chintamani Diksha + Upaya chapters; Yoga Shastra tradition; Drik Panchang convention",
}


def build_activity_rule_rows(build_id: str) -> list[dict[str, Any]]:
    """
    Materialize panchang_engine.shastra_tables.EVENT_TABLES verbatim — no
    re-authoring, no re-derivation. Pure in-memory transform (no DB query).
    """
    from panchang_engine.shastra_tables import EVENT_TABLES

    rows: list[dict[str, Any]] = []
    for activity_class, quality_table in EVENT_TABLES.items():
        citation = ACTIVITY_CITATIONS.get(
            activity_class, "panchang_engine.shastra_tables.EVENT_TABLES (citation not mapped — see writer TODO)"
        )
        for factor_type, factor_map in quality_table.items():
            if factor_type not in ("tithi", "nakshatra", "vara"):
                continue  # defensive: only the three documented keys are materialized
            for factor_id, quality_score in factor_map.items():
                rows.append({
                    "activity_class": activity_class,
                    "factor_type": factor_type,
                    "factor_id": int(factor_id),
                    "quality_score": round(float(quality_score), 3),
                    "source_citation": citation,
                    "build_id": build_id,
                })
    return rows


# ── Table 3: the Muhūrta Factor Census (item 41's gap register) ─────────────
# Hand-curated register — the disposition of every named factor family from
# KALA_SUPREME_ELEVATION_v1_0.md §9 Stage 2's working register, drawn from
# concrete verified research into this codebase's actual substrate (grep +
# live-DB queries performed during this writer's construction, cited in each
# note). (factor_family, factor_name, disposition, citation_or_gap_note,
# evidence_pointer, school_tag)
CENSUS_ROWS: list[tuple[str, str, str, str, str, str | None]] = [
    # ── Pāñcāṅgika ──
    ("panchangika", "tithi", "computed",
     "panchang_engine.angas.compute_tithi (real bisection search over Sun/Moon "
     "sidereal longitude). Source: Muhurta Chintamani §1; Brihat Samhita §2.",
     "panchang_engine/angas.py:compute_tithi", None),
    ("panchangika", "vara", "computed",
     "panchang_engine.angas.compute_vara. Source: Vishnu Smriti; Muhurta Chintamani §1.",
     "panchang_engine/angas.py:compute_vara", None),
    ("panchangika", "nakshatra", "computed",
     "panchang_engine.angas.compute_nakshatra. Source: Muhurta Chintamani §4; Brihat Samhita §2.",
     "panchang_engine/angas.py:compute_nakshatra", None),
    ("panchangika", "nakshatra_tara_bala", "not_computed",
     "Chart-personal by construction (needs the native's own janma-nakshatra) — "
     "out of THIS global lane's scope per brief §2. Computed per-chart via "
     "panchang_engine.tara_bala.compute_tara_bala_score; not duplicated here.",
     "panchang_engine/tara_bala.py (chart-bound; see also w1-flags PR #892)", None),
    ("panchangika", "nityayoga", "computed",
     "panchang_engine.angas.compute_yoga (27-fold nitya-yoga). Source: Muhurta Chintamani §4; Brihat Samhita §2.",
     "panchang_engine/angas.py:compute_yoga", None),
    ("panchangika", "nityayoga_vyatipata_vaidhriti_special_status", "not_computed",
     "compute_yoga returns the standard 27-fold nitya-yoga id/name only; no "
     "distinct Vyatipata/Vaidhriti inauspicious-flagging rule (beyond ordinary "
     "yoga-id lookup) was found as its own table in source. Ingestion work "
     "item: confirm whether MC/BS treat these two yogas as independently "
     "doshic beyond the base yoga identity, and table the rule if so.",
     "panchang_engine/angas.py (gap — grep-verified, no VYATIPATA/VAIDHRITI-specific table found)", None),
    ("panchangika", "karana_bhadra_vishti", "computed",
     "panchang_engine.special_yogas.detect_bhadra. Source: Muhurta Chintamani §2; Brihat Samhita §2.",
     "bg_muhurta_lattice (factor_family=combination_yoga, factor_key=bhadra)", None),

    # ── Combination-yogas (muhūrta election, per Elevation §9 working register) ──
    ("combination_yoga", "sarvartha_siddhi", "computed",
     "Muhurta Chintamani §10 (5.16); Drik Panchang published convention.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "amrit_siddhi", "computed",
     "Muhurta Chintamani §10 (5.17); Drik Panchang published convention.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "ravi_pushya", "computed",
     "Muhurta Chintamani §10; Drik Panchang 'Ravi Pushya Yoga' dedicated page.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "guru_pushya", "computed",
     "Muhurta Chintamani §10; Drik Panchang 'Guru Pushya Nakshatra Yoga' dedicated page.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "tripushkar", "computed",
     "Muhurta Chintamani §11; Drik Panchang published convention.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "dwipushkar", "computed",
     "Muhurta Chintamani §11; Drik Panchang published convention.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "siddha_yoga", "computed",
     "Muhurta Chintamani §10; Brihat Samhita §3; Drik Panchang published table.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "panchaka", "computed",
     "Brihat Samhita §3; Drik Panchang 'Panchaka' dedicated page.",
     "bg_muhurta_lattice (factor_family=combination_yoga)", "drik_panchang"),
    ("combination_yoga", "mrityu_yoga", "not_in_corpus",
     "No standalone Mrityu-yoga day-quality detector/table found anywhere in "
     "the codebase (grep-verified: 'mrityu'/'mrutyu' + 'yoga' across "
     "panchang_engine and brahma_* modules). Amrit-Siddhi's own docstring "
     "mentions a 'death-yoga override (MC 5.17)' that can BLOCK Amrit Siddhi, "
     "but that is a blocking condition, not an implemented Mrityu-yoga "
     "detector in its own right. Ingestion work item: OCR-translate + "
     "structurally table Muhurta Chintamani ch.17-18 (untranslated Devanagari "
     "content confirmed present — see dagdha_yoga row) and implement MC "
     "5.17's blocking rule.",
     "classical_text_chunks (text_id='muhurta_chintamani', untranslated)", None),
    ("combination_yoga", "dagdha_yoga", "not_in_corpus",
     "classical_text_chunks (text_id='muhurta_chintamani') ch.17-18 contains "
     "untranslated Devanagari Dagdha-yoga tithi x vara tables (confirmed via "
     "direct corpus query: chunks matching Devanagari dagdha/hutasana tokens "
     "in that chapter range). CORRECTED (Opus corpus-citation review, "
     "2026-07-30): 'content_en NULL on all 274 chunks' was WRONG -- "
     "content_en is NOT NULL on any of the 274 rows; it is byte-IDENTICAL to "
     "content_sa (the raw Devanagari was copied into the English column, "
     "never actually translated) -- live-verified: 0/274 NULL on content_en, "
     "274/274 equal to content_sa. Only cleaned_translation_text is genuinely "
     "NULL on all 274 rows. Net effect is the same (no usable English "
     "translation exists, so this table is not queryable/citable at verse "
     "grain), but the evidence must be stated accurately: content_en holds "
     "untranslated Devanagari, not NULL. Distinct from the L1 CHART-BOUND "
     "'Dagdha Rashi' concept in ga_sensitive_writer.py (a different, "
     "sign-based, per-chart computation) — do not conflate the two. "
     "Ingestion work item: OCR-cleanup pass + structured table extraction "
     "for Muhurta Chintamani ch.17-18.",
     "classical_text_chunks (text_id='muhurta_chintamani', ch.17-18, content_en=content_sa untranslated)", None),
    ("combination_yoga", "hutasana_yoga", "not_in_corpus",
     "Same untranslated-corpus evidence as dagdha_yoga (co-located in Muhurta "
     "Chintamani ch.17-18's Devanagari OCR). Ingestion work item: same OCR-"
     "cleanup pass.",
     "classical_text_chunks (text_id='muhurta_chintamani', ch.17-18, untranslated)", None),
    ("combination_yoga", "jvalamukhi_yoga", "not_in_corpus",
     "CORRECTED (Opus corpus-citation review, 2026-07-30): the earlier claim "
     "'no corpus evidence found even in untranslated form' was WRONG -- a "
     "direct query found exactly 1 muhurta_chintamani chunk "
     "(chunk_id='muhurta_chintamani_pg0033_c01', ch.33, verse 1) whose "
     "content_sa contains the Devanagari string 'ज्वालामुखी'. Inspecting the "
     "surrounding untranslated text: it occurs in a Makara-Guru "
     "dosha-exception passage listing GEOGRAPHIC/pilgrimage place names "
     "(alongside Delhi/Agra/Mathura) -- i.e. it reads as the place name "
     "Jvalamukhi (Himachal Pradesh), not clearly the Jvalamukhi-yoga "
     "muhurta doctrine itself. Because the term is untranslated and "
     "homographic with the place name, doctrinal content cannot be ruled "
     "out from this one hit alone, and no OTHER chunk in the corpus was "
     "found naming this yoga. Disposition remains not_in_corpus (no usable "
     "STRUCTURED rule exists either way) but the note is corrected to state "
     "the real, ambiguous finding rather than a false zero. Ingestion work "
     "item: OCR-translate ch.33 and re-scan the full text once translated "
     "to confirm whether the yoga doctrine appears anywhere.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0033_c01, ch.33, untranslated, ambiguous place-name-vs-yoga hit)", None),

    # ── Rite-specific residences ──
    ("rite_residence", "agnivasa", "computed",
     "Convention A: panchang_engine.shastra_tables.AGNI_VASA_TABLE (tithi-keyed, "
     "4-element: Prithvi/Jala/Vayu/Akasha). No inline per-row classical citation "
     "in source (Drik Panchang module-level fallback only) — disclosed as "
     "computed_uncited_convention on the row itself, not upgraded to a specific "
     "verse citation. The native-confirmed lineage practice (W4 hard-constraint "
     "runs on this convention per ADJUDICATION-16).",
     "bg_muhurta_lattice (factor_family=agnivasa, factor_key=agni_vasa)", None),
    ("rite_residence", "agnivasa_mc_arithmetic", "computed",
     "Convention B: Muhūrta-Cintāmaṇi verse 36 (MC 1.36), Rāma Daivajña. "
     "Formula: (tithi_id + 1 + vara_id) mod 4 → {0,3}:Prithvi(auspicious) | "
     "1:Akasha(inauspicious) | 2:Patala(inauspicious). Source: "
     "chunk_id=muhurta_chintamani_pg0048_c01, machine_translated_supervised + "
     "independently verified 2026-08-03 (88/88 verified). Status upgraded from "
     "'declared_not_computed' to 'computed' by ADJUDICATION-16 "
     "(SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md). NOT the "
     "native-confirmed lineage practice — stored as comparison/research data.",
     "bg_muhurta_lattice (factor_family=agnivasa, factor_key=agni_vasa_mc_arithmetic)", "muhurta_chintamani_rama_daivajna"),
    ("rite_residence", "shiva_vasa", "not_in_corpus",
     "No Siva-vasa (or any other rite-specific vasa sibling beyond Agni/"
     "Chandra/Rahu/Disha/Nakshatra/Bhadra vasa) table found in "
     "panchang_engine (grep-verified across shastra_tables.py). Directly "
     "relevant to Rudra-yajna muhurta election (campaign item 37/W4 use "
     "case). Ingestion work item: source and implement a Siva-vasa rule "
     "table for fire-rite election.",
     "not found (grep-verified)", None),

    # ── Day-part ──
    ("day_part", "hora_lord", "computed",
     "panchang_engine.timings.compute_hora. Source: Vishnu Smriti; Hora Sara (Prithuyashas).",
     "panchang_engine/timings.py:compute_hora", None),
    ("day_part", "abhijit", "computed",
     "Muhurta Chintamani §5 (excluded Wednesdays).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=abhijit)", None),
    ("day_part", "brahma_muhurta", "computed",
     "Drik Panchang convention (96-48 min before sunrise).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=brahma_muhurta)", None),
    ("day_part", "gulika_mandi_kalam", "computed",
     "Drik Panchang published index tables (GULIKA_INDEX).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=gulika_kalam)", None),
    ("day_part", "rahu_kalam", "computed",
     "Drik Panchang published index tables (RAHU_KALAM_INDEX).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=rahu_kalam)", None),
    ("day_part", "yamaganda", "computed",
     "Drik Panchang published index tables (YAMAGANDAM_INDEX).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=yamaganda)", None),
    ("day_part", "durmuhurta", "computed",
     "CORRECTED (Opus corpus-citation review, 2026-07-30): 'Brihat Samhita "
     "§2' was fabricated -- it does not appear anywhere in source for this "
     "table. The two REAL citations that DO appear (in two different source "
     "files, for the same DUR_MUHURTA_TABLE): Muhurta Chintamani §9 (per "
     "panchang_engine.timings' compute_inauspicious_timings docstring) and "
     "Drik Panchang published Dur Muhurta times (per shastra_tables.py's own "
     "§15 table comment).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=durmuhurta)", None),
    ("day_part", "amrita_ghati_amrit_kalam", "computed",
     "Muhurta Chintamani §7; Drik Panchang convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=amrit_kalam)", None),
    ("day_part", "visha_ghati", "computed",
     "No inline classical citation found in source (shastra_tables.py's "
     "VISHA_GHATI_TABLE carries no 'Source:' comment, unlike the numbered "
     "§1-§24 tables) — disclosed as computed_uncited_convention on the "
     "lattice row itself, not upgraded to a specific citation.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=visha_ghati)", None),
    ("day_part", "varjyam", "computed",
     "Muhurta Chintamani §8; Drik Panchang convention (shastra_tables.py's "
     "§14 VARJYAM_TABLE comment).",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=varjyam)", None),
    ("day_part", "yamakantaka", "computed",
     "No inline classical citation found in source (YAMAKANTAKA_INDEX, in "
     "shastra_tables.py's uncited 'Rich output contract additions' section) "
     "— disclosed as computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=yamakantaka)", None),
    ("day_part", "krakaca", "computed",
     "No inline classical citation found in source (KRAKACA_INDEX, same "
     "uncited section as yamakantaka) — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=krakaca)", None),
    ("day_part", "sashtighati", "computed",
     "No inline classical citation found in source (SASHTIGHATI_GHATIKAS, "
     "same uncited section) — disclosed as computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=sashtighati)", None),
    ("day_part", "pratah_sandhya", "computed",
     "No inline classical citation found in source (compute_extended_"
     "auspicious's own Sandhya-type windows carry no per-type 'Source:' "
     "comment) — disclosed as computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=pratah_sandhya)", None),
    ("day_part", "madhyahna_sandhya", "computed",
     "No inline classical citation found in source — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=madhyahna_sandhya)", None),
    ("day_part", "vijaya", "computed",
     "No inline classical citation found in source — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=vijaya)", None),
    ("day_part", "godhuli", "computed",
     "No inline classical citation found in source — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=godhuli)", None),
    ("day_part", "sayam_sandhya", "computed",
     "No inline classical citation found in source — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=sayam_sandhya)", None),
    ("day_part", "nishita", "computed",
     "No inline classical citation found in source — disclosed as "
     "computed_uncited_convention.",
     "bg_muhurta_lattice (factor_family=kalam, factor_key=nishita)", None),
    ("day_part", "disha_shula", "computed",
     "panchang_engine.shastra_tables.DISHA_SHUL_TABLE (vara-keyed travel-"
     "direction avoidance); already served via kala_now_get per w1-flags PR "
     "#892. No inline classical-source comment found for this specific table "
     "in shastra_tables.py — disclosed honestly as an uncited convention, not "
     "upgraded to a specific citation.",
     "panchang_engine/shastra_tables.py:DISHA_SHUL_TABLE (uncited in source)", None),

    # ── Degree-sensitive ──
    ("degree_sensitive", "mrityu_bhaga", "not_in_corpus",
     "No mrityu-bhaga (degree-sensitive sensitive-point) table found in "
     "panchang_engine or any brahma_* reference table (grep-verified for "
     "'mrityu_bhaga'/'mrutyu_bhaga'/'mrityubhaga'). Ingestion work item.",
     "not found (grep-verified)", None),
    ("degree_sensitive", "gandanta", "not_computed",
     "gandanta_dosha EXISTS as a real, cited NATAL dosha in "
     "brahma_dosha_catalog (canonical_id='gandanta_dosha', BPHS ch.9, real "
     "cancellation conditions — see bg_parihara_rules) — but no chart-"
     "independent GANDANTA-SPAN table (the degree-sensitive junction zones "
     "themselves, e.g. last/first degree of water/fire sign pairs at "
     "nakshatra boundaries) was found as a standalone GLOBAL timing factor. "
     "The natal APPLICABILITY concept exists; the timing-SPAN factor is "
     "derivable from existing sign/nakshatra boundary arithmetic but not yet "
     "built as its own table — flagged not_computed (derivable), not "
     "not_in_corpus (the underlying doctrine IS in the corpus).",
     "brahma_dosha_catalog (canonical_id=gandanta_dosha, natal only); global span not built", None),
    ("degree_sensitive", "pushkara_navamsha_bhaga", "not_in_corpus",
     "No pushkara-navamsha/bhaga table found (grep-verified across "
     "panchang_engine and brahma_* tables). Ingestion work item.",
     "not found (grep-verified)", None),
    ("degree_sensitive", "sandhi_zones", "not_computed",
     "Sign/nakshatra sandhi (junction) zones are computable in principle "
     "from existing sign-boundary/nakshatra-boundary data (pure degree "
     "arithmetic) but no dedicated global sandhi-zone table exists yet in "
     "this codebase. Flagged not_computed (derivable, not yet built), not "
     "not_in_corpus.",
     "derivable from existing sign/nakshatra boundary computations; not yet built", None),

    # ── Ghaṭī-muhūrta (the 30-fold day+night boundary family) ──
    ("ghati_muhurta", "ghati_muhurta_30fold", "computed",
     "panchang_engine.timings.compute_day_muhurtas — 30-fold day+night "
     "ghati-muhurta naming (Rudra..Bhaga day; Girisha..Samudram night), a "
     "well-known classical convention (cf. the cited Dur Muhurta subset, "
     "MC §9), but no inline per-row classical citation was found in source "
     "for this exact list — disclosed as computed_uncited_convention. Also "
     "note (Opus corpus-citation review, 2026-07-30): the day/night "
     "boundary this function uses is an ARITHMETIC MIDPOINT of sunrise-to-"
     "next-sunrise, not the chart's true computed sunset — see "
     "bg_muhurta_lattice's module docstring family-4 correction note.",
     "bg_muhurta_lattice (factor_family=ghati_muhurta)", None),

    # ── Chart-personal (explicitly out of this global lane's scope) ──
    ("chart_personal", "janma_tithi_vara_nakshatra_resonance", "not_computed",
     "Chart-personal by definition (reads a specific native's own birth "
     "tithi/vara/nakshatra) — out of THIS global lane's scope per brief §2 "
     "('per-chart contact joins are NOT this lane's job'). Already computed "
     "per-chart elsewhere: kala_now_get's chandrashtama/janma-resonance "
     "fields (w1-flags PR #892), reading L1 chart_facts per CLAUDE.md §N.5.",
     "kala_now_get (w1-flags PR #892); chart-bound, not this asset", None),

    # ── Structural-ritual ──
    ("structural_ritual", "deity_graha_correspondence", "computed",
     "brahma_remedy_corpus (planet-domain-remedy mapping) joined with "
     "panchang_engine.shastra_tables.NAKSHATRA_DEITIES (Source: Brihat "
     "Samhita §2; Taittiriya Brahmana). CORRECTED (Opus corpus-citation "
     "review, 2026-07-30): the earlier claim '221 of 266 rows real-cited' "
     "was wrong -- that number came from a narrower check (source_"
     "canonical_id = 'classical_tradition' literal match only, 45 "
     "placeholder / 221 real). Live-verified against production with the "
     "correct, broader placeholder definition (source_citation OR "
     "classical_ref ILIKE '%classical tradition%', which also catches "
     "domain-specific-but-non-verse-cited variants like 'classical "
     "tradition (navagraha vrata)'): 266 total, 102 placeholder-like, "
     "164 real-cited (mostly BPHS Ch.88-94 Upaya-adhyaya + Phaladeepika). "
     "Served via existing ref_remedies_by_planet_get.",
     "brahma_remedy_corpus + panchang_engine/shastra_tables.py:NAKSHATRA_DEITIES", None),

    # ── Astronomical ──
    ("astronomical", "eclipse_proximity", "computed",
     "bg_sky_calendar (this campaign's Night-1 sibling L0 asset, PR #888) "
     "computes real global eclipse timing via pyswisseph's own eclipse-"
     "finding functions.",
     "bg_sky_events (event_type IN eclipse_solar, eclipse_lunar)", None),
    ("astronomical", "combustion", "computed",
     "panchang_engine.planets._is_combust (per-planet combustion-orb check). "
     "Source: shastra_tables.py §12 Combustion Orbs.",
     "panchang_engine/planets.py:_is_combust", None),
]


def build_census_rows(build_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for factor_family, factor_name, disposition, note, evidence_pointer, school_tag in CENSUS_ROWS:
        rows.append({
            "factor_family": factor_family,
            "factor_name": factor_name,
            "disposition": disposition,
            "citation_or_gap_note": note,
            "evidence_pointer": evidence_pointer,
            "school_tag": school_tag,
            "build_id": build_id,
        })
    return rows


@register("bg_parihara_rules")
class BgPariharaRulesWriter(WriterBase):
    """
    Seeds bg_parihara_rules, bg_muhurta_activity_rules, and
    bg_muhurta_factor_census — see module docstring for full methodology.

    LIGHT writer: bounded DB query (brahma_dosha_catalog) + in-memory constant
    materialization (panchang_engine.shastra_tables.EVENT_TABLES) + a
    hand-curated census register. No heavy per-day loop (contrast with
    bg_muhurta_lattice).
    """

    asset_id = "bg_parihara_rules"
    _BATCH_SIZE = 500

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_parihara_rules] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        conn = ctx.db_conn
        rows_written = 0

        try:
            parihara_rows = fetch_parihara_rows(conn, ctx.build_id)
            activity_rows = build_activity_rule_rows(ctx.build_id)
            census_rows = build_census_rows(ctx.build_id)
        except Exception as exc:
            logger.error("[bg_parihara_rules] computation failed: %s", exc)
            raise RuntimeError(str(exc)) from exc

        try:
            with conn.cursor() as cur:
                rows_written += self._upsert_parihara(cur, parihara_rows)
                rows_written += self._upsert_activity_rules(cur, activity_rows)
                rows_written += self._upsert_census(cur, census_rows)
        except Exception as exc:
            logger.error(
                "[bg_parihara_rules] insert failed after %d rows: %s", rows_written, exc,
            )
            raise RuntimeError(str(exc)) from exc

        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_parihara_rules] complete — parihara=%d activity=%d census=%d in %.1fs",
            len(parihara_rows), len(activity_rows), len(census_rows), elapsed,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_written,
            duration_seconds=elapsed,
            notes=(
                f"parihara_rules={len(parihara_rows)}; "
                f"activity_rules={len(activity_rows)}; "
                f"census={len(census_rows)}"
            ),
        )

    @staticmethod
    def _upsert_parihara(cur: Any, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cur.executemany(
            """
            INSERT INTO bg_parihara_rules
              (dosha_canonical_id, dosha_name_en, dosha_category,
               cancellation_index, cancellation_condition_text, net_standing,
               scope, source_text_id, source_chapter, source_citation,
               build_id, computed_at)
            VALUES
              (%(dosha_canonical_id)s, %(dosha_name_en)s, %(dosha_category)s,
               %(cancellation_index)s, %(cancellation_condition_text)s,
               %(net_standing)s, %(scope)s, %(source_text_id)s,
               %(source_chapter)s, %(source_citation)s, %(build_id)s, NOW())
            ON CONFLICT (dosha_canonical_id, cancellation_index) DO UPDATE SET
              dosha_name_en = EXCLUDED.dosha_name_en,
              dosha_category = EXCLUDED.dosha_category,
              cancellation_condition_text = EXCLUDED.cancellation_condition_text,
              source_text_id = EXCLUDED.source_text_id,
              source_chapter = EXCLUDED.source_chapter,
              source_citation = EXCLUDED.source_citation,
              build_id = EXCLUDED.build_id,
              computed_at = NOW()
            """,
            rows,
        )
        return cur.rowcount

    @staticmethod
    def _upsert_activity_rules(cur: Any, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cur.executemany(
            """
            INSERT INTO bg_muhurta_activity_rules
              (activity_class, factor_type, factor_id, quality_score,
               source_citation, build_id, computed_at)
            VALUES
              (%(activity_class)s, %(factor_type)s, %(factor_id)s,
               %(quality_score)s, %(source_citation)s, %(build_id)s, NOW())
            ON CONFLICT (activity_class, factor_type, factor_id) DO UPDATE SET
              quality_score = EXCLUDED.quality_score,
              source_citation = EXCLUDED.source_citation,
              build_id = EXCLUDED.build_id,
              computed_at = NOW()
            """,
            rows,
        )
        return cur.rowcount

    @staticmethod
    def _upsert_census(cur: Any, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        cur.executemany(
            """
            INSERT INTO bg_muhurta_factor_census
              (factor_family, factor_name, disposition, citation_or_gap_note,
               evidence_pointer, school_tag, build_id, computed_at)
            VALUES
              (%(factor_family)s, %(factor_name)s, %(disposition)s,
               %(citation_or_gap_note)s, %(evidence_pointer)s, %(school_tag)s,
               %(build_id)s, NOW())
            ON CONFLICT (factor_family, factor_name) DO UPDATE SET
              disposition = EXCLUDED.disposition,
              citation_or_gap_note = EXCLUDED.citation_or_gap_note,
              evidence_pointer = EXCLUDED.evidence_pointer,
              school_tag = EXCLUDED.school_tag,
              build_id = EXCLUDED.build_id,
              computed_at = NOW()
            """,
            rows,
        )
        return cur.rowcount
