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
   doshas", dāna-parihāras) at chapter/verse grain, WITH ONE NAMED EXCEPTION:
   ṢAḌ-DARŚANA ADJUDICATION-10 Part 1 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md)
   ruled that one genuinely muhūrta-scope, universal-cancellation rule DOES
   exist in the ingested corpus — `bphs_jaimini` (Jaimini Sutras, trans. B.
   Suryanarain Rao 1949) PG213, chunk `bphs_jaimini_pg0213_c01`: "...the time
   goes under the special name of Abhijin Moohurta, and Abhijit Sarva
   Doshaghnam or that noon time which cuts and cures all evil influences."
   Verified read-only against production `classical_text_chunks` before this
   row was added (see PR body). See `MUHURTA_PARIHARA_ROWS` below — ONE
   hand-curated row (the writer's existing CENSUS_ROWS pattern for
   verified-but-not-SQL-derivable content), honestly labelled
   `extraction_context='translator_gloss_in_narrative'` per the ruling: this
   is B. Suryanarain Rao's own translator's doctrinal gloss embedded in
   narrative prose (an autobiographical aside at PG213), NOT a mūla-sūtra
   verse — seeding it unmarked as a sūtra citation would be citation
   inflation. Every OTHER muhūrta-scope cancellation (Guru-Puṣya,
   Sarvārtha-Siddhi strong-lagna overrides, dāna-parihāras) remains
   genuinely not_in_corpus and is registered by name in the factor census,
   never invented to match this one exception.

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
    with conn.cursor() as cur:
        cur.execute(_TEXT_TITLES_QUERY)
        for row in cur.fetchall():
            text_titles[row[0]] = row[1]

    rows: list[dict[str, Any]] = []
    with conn.cursor() as cur:
        cur.execute(_DOSHA_QUERY)
        cols = [d[0] for d in cur.description]
        for raw in cur.fetchall():
            rec = dict(zip(cols, raw))
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
                    # Honest null (§N.7 item 6): whether each of these 79
                    # brahma_dosha_catalog-derived conditions is itself a
                    # mūla-sūtra verse or a translator/commentary gloss was
                    # not individually re-verified when this column was
                    # added (migration 524) — classifying all of them now
                    # would be an invented judgment, not a migration's job.
                    "extraction_context": None,
                    "build_id": build_id,
                })
    return rows


# ── Table 1b: the ONE hand-curated muhūrta-scope row (ADJUDICATION-10) ───────
# ṢAḌ-DARŚANA ADJUDICATION-10 Part 1 ruled this clause MET by extracting the
# one muhūrta-scope, universal-cancellation rule genuinely present in the
# ingested corpus, rather than amending the W3 gate criterion or reaching for
# a NATAL bhaṅga rule (which would be a §N.5 authority inversion — a natal
# cancellation applied to a muhūrta doṣa is a fabricated cancellation).
#
# `dosha_canonical_id='rahu_kalam'`: the source text states the cancellation
# UNQUALIFIED ("Abhijit Sarva Doshaghnam... cuts and cures all evil
# influences" — no doṣa-class restriction anywhere in the passage). But
# `bg_parihara_rules.dosha_canonical_id` is a single NOT NULL matching key
# (no wildcard/all-doṣa convention exists anywhere in this schema or in the
# `kala_lattice_query.ts` engine's `matchingPariharas` join, which matches a
# lattice doṣa's `factor_key` against this column by case-insensitive
# equality) — the schema FORCES a per-doṣa row. `rahu_kalam` is chosen as
# the one concrete, real, cited (`corpus_status=computed_cited`), commonly
# co-occurring inauspicious `kalam` factor_key to demonstrate the rescue
# mechanism against (see `bg_muhurta_lattice.py`'s `KALAM_CITATIONS`). This
# NARROWS the row's practical reach to one doṣa key without narrowing what
# `cancellation_condition_text` actually asserts — the text below transcribes
# the source's unqualified claim verbatim; the narrowing is a schema/engine
# limitation, disclosed here and in the PR body, not a doctrinal qualification
# invented into the passage (ADJUDICATION-10 Part 1 forbids inventing weekday
# exceptions or doṣa-class qualifications — none are added).
MUHURTA_PARIHARA_ROWS: list[dict[str, Any]] = [
    {
        "dosha_canonical_id": "rahu_kalam",
        "dosha_name_en": "Rahu Kalam",
        "dosha_category": "muhurta_kalam",
        "cancellation_index": 1,
        "cancellation_condition_text": (
            "...the time goes under the special name of Abhijin Moohurta, and "
            "Abhijit Sarva Doshaghnam or that noon time which cuts and cures "
            "all evil influences."
        ),
        "net_standing": "cancelled",
        "scope": "muhurta",
        "source_text_id": "bphs_jaimini",
        "source_chapter": 213,  # PG213 — a page number in this text's chunking convention, not a verse chapter.
        "source_citation": (
            "Jaimini Sutras (bphs_jaimini), trans. B. Suryanarain Rao, 1949, "
            "PG213 [chunk bphs_jaimini_pg0213_c01]"
        ),
        "extraction_context": "translator_gloss_in_narrative",
    },
]


def build_muhurta_parihara_rows(build_id: str) -> list[dict[str, Any]]:
    """The one ADJUDICATION-10 Part 1 hand-curated muhūrta-scope row, stamped
    with this build's build_id. Pure function, no DB access — mirrors
    build_census_rows' pattern for verified-but-not-SQL-derivable content."""
    rows: list[dict[str, Any]] = []
    for row in MUHURTA_PARIHARA_ROWS:
        rows.append({**row, "build_id": build_id})
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
    # W4 ruling R-1 (2026-08-02): the three rows below were `computed` with an
    # evidence_pointer naming a panchang_engine FUNCTION rather than a lattice
    # atom. KALA_W4_UPAYA_DESIGN §3.1 found that this made three of the canned
    # Mode-2 fixture's six constraints unsearchable — the disposition was true
    # ("the codebase computes this") but the pointer did not resolve to anything
    # a Mode-2 search could scan. Migration 530 + bg_muhurta_lattice.py's new
    # emitters materialize them as real lattice families; the pointers below now
    # resolve where the design says they must.
    ("panchangika", "tithi", "computed",
     "panchang_engine.angas.compute_tithi (real bisection search over Sun/Moon "
     "sidereal longitude). Source: Muhurta Chintamani §1; Brihat Samhita §2. "
     "MATERIALIZED as a lattice family by W4 ruling R-1 (migration 530): "
     "detail.factor_id carries compute_tithi(...).id (1..30), the same id space "
     "bg_muhurta_activity_rules.factor_id (factor_type='tithi') uses — that "
     "shared provenance is what makes the item-6 join deterministic rather than "
     "hand-mapped (B.10).",
     "bg_muhurta_lattice (factor_family=tithi; detail.factor_id from panchang_engine/angas.py:compute_tithi)", None),
    ("panchangika", "vara", "computed",
     "panchang_engine.angas.compute_vara. Source: Vishnu Smriti; Muhurta Chintamani §1. "
     "MATERIALIZED as a lattice family by W4 ruling R-1 (migration 530): "
     "detail.factor_id carries compute_vara(...).id (1..7, the shastra_tables §7 "
     "VARA_NAMES key), the same id space bg_muhurta_activity_rules.factor_id "
     "(factor_type='vara') uses. This is the atom the canned W4 Mode-2 fixture's "
     "`panchanga {vara: guru-vara}` constraint searches over; before R-1 no vara "
     "family existed and vara appeared only inside combination_yoga detail.",
     "bg_muhurta_lattice (factor_family=vara; detail.factor_id from panchang_engine/angas.py:compute_vara)", None),
    ("panchangika", "nakshatra", "computed",
     "panchang_engine.angas.compute_nakshatra. Source: Muhurta Chintamani §4; Brihat Samhita §2. "
     "MATERIALIZED as a lattice family by W4 ruling R-1 (migration 530): "
     "detail.factor_id carries compute_nakshatra(...).id (1..27), the same id "
     "space bg_muhurta_activity_rules.factor_id (factor_type='nakshatra') uses.",
     "bg_muhurta_lattice (factor_family=nakshatra; detail.factor_id from panchang_engine/angas.py:compute_nakshatra)", None),
    ("panchangika", "nakshatra_tara_bala", "not_computed",
     "Chart-personal by construction (needs the native's own janma-nakshatra) — "
     "out of THIS global lane's scope per brief §2. Computed per-chart via "
     "panchang_engine.tara_bala.compute_tara_bala_score; not duplicated here. "
     "RE-AFFIRMED at W4 (KALA_W4_UPAYA_DESIGN §3.1, verbatim: 'that disposition "
     "is correct and must not be fixed'). W4's Mode-2 searcher evaluates "
     "tara-bala as a CHART-RELATIVE post-filter over lattice atoms, reading the "
     "chart's own janma-nakshatra by fact_id from chart_facts and citing that "
     "fact_id in the response — and reports it in its own coverage block as "
     "'computed (chart-relative, at query time)'. Two dispositions, two scopes, "
     "both honest: this GLOBAL census row stays not_computed because a global "
     "table cannot hold a chart-personal value, and a session that conflates the "
     "two has broken §N.5.",
     "panchang_engine/tara_bala.py (chart-bound; see also w1-flags PR #892); "
     "query-time evaluation in platform-mcp/src/lib/kala_sky_pattern.ts (chart_relative constraint kind)", None),

    # ── W4 ruling R-1: the two lattice families deliberately NOT materialized ──
    # The ruling's own text: "Optional-but-recommended … If Lane R defers them,
    # the census must say so by name and the Mode-2 coverage block must list them
    # as `not_computed (lattice family not materialized)`. Deferring them does not
    # block the fixture; pretending they are covered does." These are those rows.
    ("panchangika", "nityayoga_lattice_family", "not_computed",
     "lattice family not materialized. The 27-fold nitya-yoga IS computed "
     "(panchang_engine.angas.compute_yoga — see the sibling 'nityayoga' row, "
     "disposition computed) but was NOT emitted as its own bg_muhurta_lattice "
     "factor_family at W4. Named deferral per KALA_W4_UPAYA_DESIGN §3.1's own "
     "clause. Consequence, stated plainly: a Mode-2 sky_pattern_spec constraint "
     "naming nitya-yoga has no atom to search over and triggers the "
     "drop-and-report precedence rule (design §6.2), never a silent skip. No W4 "
     "fixture constraint names it. Work item: add a `nityayoga` emitter to "
     "bg_muhurta_lattice.py (same generator loop as vara/nakshatra/tithi) and "
     "widen the factor_family CHECK.",
     "panchang_engine/angas.py:compute_yoga (computed, not emitted to bg_muhurta_lattice)", None),
    ("panchangika", "karana_lattice_family", "not_computed",
     "lattice family not materialized. The karana pair IS computed "
     "(panchang_engine.angas.compute_karana_pair) and the ONE karana the W4 "
     "fixture cares about — Vishti/Bhadra — is ALREADY a searchable lattice atom "
     "under factor_family=combination_yoga, factor_key='bhadra' (see the "
     "'karana_bhadra_vishti' row). The remaining ten karanas were not emitted as "
     "their own family at W4. Named deferral per KALA_W4_UPAYA_DESIGN §3.1. The "
     "fixture's `panchanga_not {karana: [vishti]}` clause resolves against the "
     "bhadra span and is NOT affected by this deferral. Work item: add a "
     "`karana` emitter for the full 11-karana set.",
     "panchang_engine/angas.py:compute_karana_pair (computed; only the vishti/bhadra "
     "member is emitted, as bg_muhurta_lattice factor_family=combination_yoga factor_key=bhadra)", None),
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
     "panchang_engine.shastra_tables.AGNI_VASA_TABLE (tithi-keyed). No inline "
     "per-row classical citation in source (Drik Panchang module-level "
     "fallback only) — disclosed as computed_uncited_convention on the row "
     "itself, not upgraded to a specific verse citation.",
     "bg_muhurta_lattice (factor_family=agnivasa, factor_key=agni_vasa)", None),
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
     "panchang_engine.timings.compute_hora. Source: Vishnu Smriti; Hora Sara (Prithuyashas). "
     "MATERIALIZED as a lattice family by W4 ruling R-1 (migration 530): 24 rows "
     "per sunrise→next-sunrise cycle, factor_key='hora_<planet>', detail.lord = "
     "the Chaldean-sequence hora lord read from panchang_engine's own "
     "HORA_CYCLE/VARA_HORA_START tables. Before R-1 this row was `computed` with "
     "an evidence_pointer naming the FUNCTION, not the table — true, but the "
     "canned W4 Mode-2 fixture's `planet_state {body: Guru, in: {hora_lord}}` "
     "constraint had nothing to search over (KALA_W4_UPAYA_DESIGN §3.1).",
     "bg_muhurta_lattice (factor_family=hora; from panchang_engine/timings.py:compute_hora)", None),
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

    # ── Muhūrta-lagna (registry item 7, ṢAḌ-DARŚANA W4 Lane R) ────────────────
    ("muhurta_lagna", "rising_sign_span", "computed",
     "Registry item 7's substrate. The 12 rising-sign spans per day at the fixed "
     "reference location, found by REAL BISECTION (1-second tolerance) over "
     "panchang_engine.lagna.compute_lagna's ascendant_sign_id — not by assuming a "
     "2-hour sign length, which is false away from the equator. Each row carries "
     "detail.sign_id, detail.lord (shastra_tables §8 SIGN_LORDS; Source, inline: "
     "Brihat Samhita §1; Brihat Parasara Hora Sastra), detail.lord_sign_id, "
     "detail.lord_retrograde and detail.graha_sign_ids (all nine grahas' sidereal "
     "sign at span start). compute_lagna itself carries NO inline classical "
     "citation (it is a swisseph Placidus-cusp computation) — the SPAN is an "
     "astronomical quantity, so the lattice row is stored "
     "corpus_status='computed_uncited_convention', not upgraded to a verse "
     "citation this codebase does not hold.",
     "bg_muhurta_lattice (factor_family=lagna; from panchang_engine/lagna.py:compute_lagna)", None),
    ("muhurta_lagna", "lagna_lord_strength", "computed",
     "Registry item 7's strength half, evaluated AT QUERY TIME, not stored. The "
     "lattice row carries only FACTS (sign ids, lord name, graha sign ids); the "
     "dignity verdict is resolved against bg_dignity_reference "
     "(exaltation/debilitation/moolatrikona/own_signs, BPHS-cited, 9 rows, "
     "migration 250) and the drishti verdict against BPHS Ch.26 "
     "(brahma_constants special_aspect_mars/jupiter/saturn = 4,8 / 5,9 / 3,10 "
     "plus the universal 7th). Storing a verdict on the lattice row would be a "
     "SECOND COPY of those two authorities and could drift from either — §N.5 "
     "forbids it, so detail.strength_verdict is deliberately NULL with a note "
     "saying why (§N.7 item 6: an honest null beats an invented judgment).",
     "bg_dignity_reference (dignity authority) + brahma_constants special_aspect_* (BPHS Ch.26); "
     "query-time join in platform-mcp/src/lib/kala_ritual_resonance.ts", None),
    ("muhurta_lagna", "lagna_shuddhi_rules", "not_in_corpus",
     "The classical muhurta-lagna DOCTRINE — which lagna suits which rite, "
     "lagna-suddhi (ascendant-purification) rules, the lagna-tyajya degrees — is "
     "NOT held in this codebase at verse grain. Corpus-verified 2026-08-02 "
     "against the live classical_text_chunks table: the primary source is "
     "Muhurta Chintamani (text_id='muhurta_chintamani', 274 chunks) whose "
     "content_en is byte-identical to content_sa on all 274 rows (untranslated "
     "Devanagari OCR copied into the English column — the same finding the "
     "dagdha_yoga row records) and whose cleaned_translation_text is NULL "
     "throughout. Brihat Samhita Adh. C (chunks brihat_samhita_pg0769..0771) "
     "carries real, translated ELECTION rules that mention the rising sign "
     "(e.g. sl.7-8, marriage: 'when Mithuna, Kanya or Tula is rising') but no "
     "systematic lagna-suddhi table. Ingestion work item: OCR-translate Muhurta "
     "Chintamani's lagna chapters. NOTHING is asserted here in the meantime.",
     "classical_text_chunks (text_id='muhurta_chintamani', untranslated: content_en=content_sa "
     "on 274/274 rows, cleaned_translation_text NULL on 274/274) — live-verified 2026-08-02", None),

    # ── Rite-specific activity rules (registry item 6, ṢAḌ-DARŚANA W4 Lane R) ──
    ("rite_specific", "activity_rule_id_join", "computed",
     "Registry item 6. bg_muhurta_activity_rules (329 rows, 8 activity classes x "
     "factor_type in {tithi,nakshatra,vara} x integer factor_id) was EXCLUDED "
     "from the item-36 lattice engine's rite_specific_resonance Pareto axis "
     "because lattice candidates carried limb NAMES while the rule table keys on "
     "integer factor_id, and a hand-written name->id map was correctly refused as "
     "invented data (ADJUDICATION-10, accepting the exclusion on condition it "
     "stay explicit). W4 ruling R-1 makes the map REAL rather than invented: the "
     "new vara/nakshatra/tithi lattice families carry detail.factor_id read "
     "directly from panchang_engine (compute_vara/compute_nakshatra/compute_tithi "
     ".id), which is the SAME source bg_muhurta_activity_rules.factor_id was "
     "populated from (shastra_tables.EVENT_TABLES, materialized verbatim by this "
     "writer's build_activity_rule_rows). The join therefore rests on ONE "
     "deterministic source. RAIL (design §3.3, binding): if any future edit makes "
     "these ids anything other than a direct read from panchang_engine, this row "
     "reverts to not_computed and the axis must be re-excluded — enabling it on a "
     "hand-mapped correspondence is a B.10 violation and a gate failure.",
     "bg_muhurta_activity_rules.factor_id <-> bg_muhurta_lattice.detail->>'factor_id' "
     "(both from panchang_engine's own numbered tables); consumed by "
     "platform-mcp/src/lib/kala_ritual_resonance.ts", None),
    ("rite_specific", "activity_rule_pareto_axis_in_frozen_engine", "not_computed",
     "HONEST PARTIAL, disclosed rather than claimed. The DATA-LAYER join above is "
     "live and deterministic, so Mode 1's rite-specific resonance factor is real. "
     "The item-36 engine's own rite_specific_resonance PARETO AXIS is still "
     "listed in kala_lattice_query.ts's EXCLUDED_AXES, because that file is "
     "FROZEN for W4 (KALA_W4_UPAYA_DESIGN §0.2, a RAIL not a convenience) and "
     "exposes no injection point for enabling an excluded axis — EXCLUDED_AXES is "
     "a module-private `const`, not a parameter. Lane R therefore STOPPED and "
     "reported rather than editing a frozen file, per its own instruction. The "
     "axis's disclosed exclusion reason in that file still reads "
     "'wiring the id path is item 6/7 W3 work' — now stale: the id path IS wired, "
     "at the data layer. Work item for the Conductor: one-line unfreeze PR "
     "removing rite_specific_resonance from EXCLUDED_AXES and adding the axis to "
     "AxisVector, once the freeze lifts.",
     "platform-mcp/src/lib/kala_lattice_query.ts:EXCLUDED_AXES (FROZEN for W4; "
     "module-private const, no injection mechanism)", None),

    # ── Parihāra scope (muhūrta-scope cancellation corpus findings) ────────────
    ("parihara_scope", "vishti_conditional_undertaking_exception", "not_computed",
     "A REAL, translated, in-corpus muhurta-scope Vishti/Bhadra exception was "
     "found and verified live 2026-08-02, and is deliberately NOT encoded as a "
     "bg_parihara_rules row. Source, transcribed verbatim from chunk "
     "brihat_samhita_pg0768_c01 (Brihat Samhita, Adh. C 'On the Qualities of the "
     "Karanas', Slokas 3-4, trans. V. Subrahmanya Sastri 1946): 'Nothing done in "
     "Vishti leads to beneficial results, but attacking enemies; administering "
     "poison and such other things do succeed.' This is a genuine, cited, "
     "muhurta-scope narrowing of the Bhadra/Vishti dosa — but it is CONDITIONAL "
     "ON THE UNDERTAKING CLASS, and bg_parihara_rules has no undertaking-class "
     "qualifier column, while kala_lattice_query.ts's matchingPariharas() cancels "
     "unconditionally on a dosha_canonical_id match. Encoding it as a row would "
     "therefore make the engine report Bhadra 'fully_cancelled' for a WEDDING — a "
     "cancellation the source explicitly does not license, and a §N.5 authority "
     "inversion. Same discipline as ADJUDICATION-10 Part 1's refusal to invent a "
     "wildcard match the schema does not support, applied in the other direction: "
     "the finding is recorded with its exact chunk_id and verbatim text, not "
     "forced into a schema that would misrepresent it. Work item: add an "
     "`applies_to_activity_classes TEXT[]` qualifier to bg_parihara_rules and an "
     "undertaking-aware branch to matchingPariharas(), then seed this row. "
     "extraction_context if/when seeded: mula_sutra_citation (numbered-sloka "
     "translation of Varahamihira's verse, not a translator's narrative aside — "
     "unlike the ADJUDICATION-10 Abhijit row, which is "
     "translator_gloss_in_narrative).",
     "classical_text_chunks (chunk_id='brihat_samhita_pg0768_c01', Adh. C sl.3-4, "
     "translated, low_confidence_flag=false) — live-verified 2026-08-02; "
     "schema gap: bg_parihara_rules has no activity-class qualifier column", "vedic:parashari"),

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
            parihara_rows = fetch_parihara_rows(conn, ctx.build_id) + build_muhurta_parihara_rows(ctx.build_id)
            activity_rows = build_activity_rule_rows(ctx.build_id)
            census_rows = build_census_rows(ctx.build_id)
        except Exception as exc:
            logger.error("[bg_parihara_rules] computation failed: %s", exc)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, notes=f"failed: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        try:
            with conn.cursor() as cur:
                rows_written += self._upsert_parihara(cur, parihara_rows)
                rows_written += self._upsert_activity_rules(cur, activity_rows)
                rows_written += self._upsert_census(cur, census_rows)
        except Exception as exc:
            logger.error(
                "[bg_parihara_rules] insert failed after %d rows: %s", rows_written, exc,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=rows_written,
                notes=f"partial: {exc}", duration_seconds=round(time.time() - t0, 2),
            )

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
               extraction_context, build_id, computed_at)
            VALUES
              (%(dosha_canonical_id)s, %(dosha_name_en)s, %(dosha_category)s,
               %(cancellation_index)s, %(cancellation_condition_text)s,
               %(net_standing)s, %(scope)s, %(source_text_id)s,
               %(source_chapter)s, %(source_citation)s,
               %(extraction_context)s, %(build_id)s, NOW())
            ON CONFLICT (dosha_canonical_id, cancellation_index) DO UPDATE SET
              dosha_name_en = EXCLUDED.dosha_name_en,
              dosha_category = EXCLUDED.dosha_category,
              cancellation_condition_text = EXCLUDED.cancellation_condition_text,
              net_standing = EXCLUDED.net_standing,
              scope = EXCLUDED.scope,
              source_text_id = EXCLUDED.source_text_id,
              source_chapter = EXCLUDED.source_chapter,
              source_citation = EXCLUDED.source_citation,
              extraction_context = EXCLUDED.extraction_context,
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
