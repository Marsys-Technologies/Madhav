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

   PARIHĀRA-GRAPH ENRICHMENT (2026-08-04): MUHURTA_CHINTAMANI_TRANSLATION_
   REPORT_v1_0.md (2026-08-03) translated 66 doṣa-parihāra-topic
   muhurta_chintamani chunks (previously content_en=content_sa, untranslated
   Devanagari). This pass read all 66 directly against their live content_en
   (not the report's summary) and added 9 new `parihara_scope` CENSUS_ROWS
   entries citing real chunk_ids + verbatim excerpts, plus corrected/confirmed
   the pre-existing `jvalamukhi_yoga` row on the now-translated evidence.
   Every finding was activity-class-, region-, sub-window-, or wildcard-
   conditional (never a clean unconditional cancellation matching an existing
   dosha_canonical_id/lattice factor_key), so — per the exact discipline the
   pre-existing `vishti_conditional_undertaking_exception` row below already
   established — NONE were added to MUHURTA_PARIHARA_ROWS (Table 1b stays
   exactly the ADJUDICATION-10 Part 1 single row; see its own test,
   `test_muhurta_parihara_rows_is_exactly_one_row`). See the `parihara_scope`
   rows below for the full findings, and the task's own final report for the
   chunk-by-chunk usable/skipped accounting.

CORPUS GAPS FOUND AND HONESTLY DISCLOSED (not fabricated — see census for full
detail): mṛtyu-yoga, dagdha-yoga (day-quality), hutāśana-yoga, viṣa-yoga,
yamaghaṇṭa-yoga, utpāta-yoga, kāṇa-yoga — panchang_engine does NOT implement
any of these seven combination-yogas, but (COMBINATION-YOGA ENRICHMENT,
ṢAḌ-DARŚANA T4, 2026-08-05) real, structured, citable Muhūrta Chintāmaṇi ch.1
tables now exist for all seven in the translated `classical_text_chunks`
corpus (MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md §3(c), 21 chunks) — each
disposed `not_computed`, not `not_in_corpus`, with the exact verse/chunk_id
cited (see census rows below). jvālāmukhī-yoga alone was re-investigated on
this same translated evidence and CONFIRMED to remain `not_in_corpus` (the
chunk names a place, not the yoga doctrine). The Amṛta-siddhi row's own
tithi-level exception layer (vv.20-22) and the Ānandādi 28-yoga system's
operational starting-nakṣatra chart (vv.23-25, illegible in this scan) are
two further, distinct findings from the same enrichment pass — see the
`amrit_siddhi_tithi_exceptions` and `ananda_yoga_28fold` census rows. Śiva-
vāsa (no rite-specific vāsa sibling beyond Agni/Chandra/Rāhu/Diśā/Nakṣatra/
Bhadra exists); mṛtyu-bhāga; puṣkara-navāṃśa/bhāga; global gaṇḍānta-span
factor (the natal APPLICABILITY concept exists in brahma_dosha_catalog; the
chart-independent TIMING-SPAN factor does not).

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
    # The orchestrator connection's default row_factory is dict_row
    # (pipeline/orchestrator/db.py:26) — rows MUST be indexed by column name,
    # never numerically (see bo_pramana_mapa.py's note on this exact trap).
    # Numeric indexing here (`row[0]`/`row[1]`) is the KeyError: 1 that crashed
    # the 2026-08-02 L0 global build (run 6fd72ed9). row_factory is pinned
    # explicitly (neighboring-writer convention, e.g. mi_adhilepa/ph_muhurta)
    # so the function is also correct on a tuple-row test connection.
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
    # ── Combination-yoga enrichment (ṢAḌ-DARŚANA T4, 2026-08-05): the three
    # rows immediately below (mrityu_yoga, dagdha_yoga, hutasana_yoga) were
    # `not_in_corpus` on "untranslated Devanagari" evidence gathered
    # 2026-07-30. MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md §3(c)
    # (2026-08-03) translated the 21 combination_yoga-topic chunks that
    # evidence pointed at; this pass re-read all 21 directly against their
    # live content_en (platform/scripts/corpus/data/
    # muhurta_chintamani_translations.json, priority_topic='combination_yoga')
    # rather than trusting the report's own summary. FALSIFIED: real,
    # structured, citable vāra×tithi and vāra×nakṣatra tables exist for all
    # three, plus FOUR genuinely new combination-yogas sharing the same two
    # source verses (Viṣa, Yamaghaṇṭa, and the Utpāta/Kāṇa members of the
    # Utpāta-Mṛtyu-Kāṇa-Siddhi tetrad — "Siddhi" here is the tetrad's own 4th
    # member, a DIFFERENT classical concept from the already-computed
    # `siddha_yoga` row above; not registered as its own row to avoid a false
    # merge with that unrelated name). Disposition moves to `not_computed`
    # (not `computed`): the corpus tables now exist and are cited, but no
    # panchang_engine detector implements the vāra×tithi/vāra×nakṣatra lookup
    # — an ingestion/implementation work item, not yet materialized in
    # bg_muhurta_lattice.
    ("combination_yoga", "mrityu_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.30 (ṭīkā), chunk muhurta_chintamani_pg0024_c01 "
     "(translated 2026-08-03, re-read live 2026-08-05): 'On Sunday, the four "
     "nakshatras reckoned from Vishakha are in order the Utpata, Mrityu, Kana "
     "and Siddhi yogas... In the same way the said four yogas arise on Monday "
     "from Purvashadha, on Tuesday from Dhanishtha, on Wednesday from Revati, "
     "on Thursday from Rohini, on Friday from Pushya, and on Saturday from "
     "Uttaraphalguni.' Mrityu is the 2nd of each weekday's four-nakshatra run "
     "(e.g. Sunday: Vishakha=Utpata, Anuradha=Mrityu, Jyeshtha=Kana, "
     "Mula=Siddhi). DISTINCT from Amrit-Siddhi's own separately-cited "
     "'death-yoga override (MC 5.17)' blocking condition (see "
     "amrit_siddhi_tithi_exceptions row below) — that blocks a different "
     "yoga's formation; this IS a standalone day-quality yoga in its own "
     "right, not a blocking rule. Verse 31's taxonomy (same chunk, fully "
     "legible per its own OCR note) classifies this as a nakshatra x vara "
     "combination-dosha. Work item: implement the 7-weekday x 4-nakshatra "
     "lookup as a bg_muhurta_lattice combination_yoga emitter.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0024_c01, "
     "ch.1 v.30, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "dagdha_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.8 (mula + tika), chunks muhurta_chintamani_pg0017_c02 + "
     "pg0018_c01 (translated 2026-08-03, re-read live 2026-08-05): 'The twelfth on "
     "Sunday, the eleventh on Monday, the fifth on Tuesday, the third on "
     "Wednesday, the sixth on Thursday, the eighth on Friday, the ninth on "
     "Saturday — these form the Dagdha yoga.' A complete 7-weekday x 1-tithi "
     "table, verse-numeral-confirmed against the tika's own day-by-day "
     "enumeration (OCR conf 0.85). CORRECTS the prior 'content_en=content_sa "
     "untranslated' finding (2026-07-30) — that was accurate THEN; the "
     "2026-08-03 pass translated exactly this chunk range. Distinct from the "
     "L1 CHART-BOUND 'Dagdha Rashi' concept in ga_sensitive_writer.py (a "
     "different, sign-based, per-chart computation) — do not conflate the "
     "two. Parihara noted in the same tika (region-conditional per some "
     "authorities, benefic-in-kendra/trikona cancels per others, day-only per "
     "Vasishtha) — conditional, so per the vishti_conditional_undertaking_"
     "exception precedent this is NOT encoded as an unconditional "
     "bg_parihara_rules row. Work item: implement the 7-weekday x 1-tithi "
     "lookup as a bg_muhurta_lattice combination_yoga emitter.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0017_c02, "
     "ch.1 v.8, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "hutasana_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.8 (mula + tika), chunks muhurta_chintamani_pg0017_c02 + "
     "pg0018_c01 (translated 2026-08-03, re-read live 2026-08-05): 'The sixth "
     "on Monday, the seventh on Tuesday, the eighth on Wednesday, the ninth "
     "on Thursday, the tenth on Friday, the eleventh on Saturday — these form "
     "the Hutashana yoga' (Sunday's own entry — the twelfth — is given in the "
     "verse itself, pg0017_c02). Co-located with dagdha_yoga/visha_yoga in "
     "the same two chunks, same verse 8. CORRECTS the prior 'content_en="
     "content_sa untranslated' finding (2026-07-30) on the same evidence as "
     "dagdha_yoga. Work item: same lookup emitter as dagdha_yoga/visha_yoga.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0018_c01, "
     "ch.1 v.8, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "visha_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.8 (mula + tika), chunk muhurta_chintamani_pg0017_c02 "
     "(translated 2026-08-03, re-read live 2026-08-05): 'The fourth on "
     "Sunday, the sixth on Monday, the seventh on Tuesday, the second on "
     "Wednesday, the eighth on Thursday, the ninth on Friday, the seventh on "
     "Saturday — these form the Visha yoga.' Full 7-weekday x 1-tithi table, "
     "same verse as dagdha_yoga/hutasana_yoga (co-registered there was never "
     "possible before this pass — this is a GENUINELY NEW census row, not a "
     "correction). Distinct from the already-computed `day_part/visha_ghati` "
     "row (a ghati-grained kalam window, a different classical concept "
     "sharing only the 'visha' name) — do not conflate the two. Work item: "
     "same lookup emitter as dagdha_yoga/hutasana_yoga.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0017_c02, "
     "ch.1 v.8, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "yamaghanta_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.9 (mula + tika), chunk muhurta_chintamani_pg0018_c01 "
     "(translated 2026-08-03, re-read live 2026-08-05, OCR conf 0.4 overall "
     "chunk but this specific tika enumeration is the SECURE reading per its "
     "own OCR note): 'Magha on Sunday, Vishakha on Monday, Ardra on Tuesday, "
     "Mula on Wednesday, Krittika on Thursday, Rohini on Friday, Hasta on "
     "Saturday — these form the Yamaghanta yoga.' Full 7-weekday x "
     "1-nakshatra table. The same tika states this and dagdha/visha/hutasana "
     "'are to be shunned in auspicious work, and must without fail be "
     "avoided for setting out on a journey' — parihara conditions given "
     "(region-conditional, benefic-in-kendra/trikona, day-only per "
     "Vasishtha) are conditional, so NOT encoded as an unconditional "
     "bg_parihara_rules row (same discipline as dagdha_yoga). Work item: "
     "implement the 7-weekday x 1-nakshatra lookup as a bg_muhurta_lattice "
     "combination_yoga emitter.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0018_c01, "
     "ch.1 v.9, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "utpata_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.30 (mula + tika), chunk muhurta_chintamani_pg0024_c01 "
     "(translated 2026-08-03, re-read live 2026-08-05): the SAME "
     "Utpata-Mrityu-Kana-Siddhi tetrad table as the mrityu_yoga row above — "
     "Utpata is the 1st of each weekday's four-nakshatra run (e.g. Sunday: "
     "Vishakha=Utpata). See mrityu_yoga for the full 7-weekday starting-point "
     "table and the citation of verse 31's fully-legible tithi x vara / "
     "tithi x nakshatra / nakshatra x vara / all-three taxonomy. Work item: "
     "same lookup emitter as mrityu_yoga/kana_yoga (one table, four named "
     "results).",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0024_c01, "
     "ch.1 v.30, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "kana_yoga", "not_computed",
     "Muhurta Chintamani ch.1 v.30 (mula + tika), chunk muhurta_chintamani_pg0024_c01 "
     "(translated 2026-08-03, re-read live 2026-08-05): the SAME "
     "Utpata-Mrityu-Kana-Siddhi tetrad table as the mrityu_yoga/utpata_yoga "
     "rows — Kana is the 3rd of each weekday's four-nakshatra run (e.g. "
     "Sunday: Jyeshtha=Kana). See mrityu_yoga for the full table. The "
     "tetrad's 4th member ('Siddhi') is DELIBERATELY not given its own "
     "combination_yoga row here — it is a different classical concept from "
     "the already-computed `siddha_yoga` row above and registering a "
     "same-named row risks a false merge; this note is the disclosure "
     "instead. Work item: same lookup emitter as mrityu_yoga/utpata_yoga.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0024_c01, "
     "ch.1 v.30, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "amrit_siddhi_tithi_exceptions", "not_computed",
     "Muhurta Chintamani ch.1 vv.20-22 (mula + tika), chunk "
     "muhurta_chintamani_pg0021_c01 (translated 2026-08-03, re-read live "
     "2026-08-05, OCR conf 1.0 — the cleanest chunk in the whole "
     "combination_yoga set): 'The Amritasiddhi yogas that arise from the "
     "vara and nakshatra combination become inauspicious through their "
     "conjunction with certain tithis. Thus Hasta on a Sunday is a siddhi "
     "combination, but if it falls on the fifth tithi it is contrary.' Four "
     "more tithi-keyed exceptions follow (Asvini-Tuesday/7th, "
     "Mrigashira-Monday/6th, Anuradha-Wednesday/8th, Revati-Friday/10th, "
     "Pushya-Thursday/9th, Rohini-Saturday/11th), PLUS three activity-class "
     "rejections (v.22: Bhauma-Ashvini rejected for griha-pravesha, "
     "Shani-Rohini for yatra, Guru-Pushya for marriage, despite all three "
     "being Amrita-siddhi combinations generally). This is a REAL ACCURACY "
     "GAP on the ALREADY-`computed` amrit_siddhi row above: panchang_engine."
     "special_yogas.detect_all_special_yogas implements only the base "
     "vara x nakshatra Amrita-siddhi table (Muhurta Chintamani MC 5.17's "
     "already-known death-yoga override, per the pre-existing mrityu_yoga "
     "row's note) with NO tithi-level exception layer and NO activity-class "
     "rejection layer. amrit_siddhi itself is NOT re-disposed here (§N.5: "
     "the writer's existing computed claim for the base table is correct and "
     "unchanged) — this row discloses, separately and honestly, that the "
     "computed claim does not cover the corpus's own exception layer. Work "
     "item: extend the Amrita-siddhi detector with the tithi-exception and "
     "activity-class-rejection tables above.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0021_c01, "
     "ch.1 vv.20-22, translated 2026-08-03, content_en re-read live 2026-08-05, structured table confirmed)", None),
    ("combination_yoga", "ananda_yoga_28fold", "not_in_corpus",
     "GENUINE NEGATIVE FINDING (mirrors the jvalamukhi_yoga/Kota-Chakra "
     "precedent): Muhurta Chintamani ch.1 vv.23-24, chunk "
     "muhurta_chintamani_pg0021_c01 (OCR conf 1.0), gives the full 28 "
     "Ananda-adi yoga NAMES with their numbers (Ananda 1 ... Vardhamana 28) — "
     "citable and translated. But the starting-nakshatra correlation chart "
     "actually needed to COMPUTE which of the 28 falls on a given "
     "weekday+nakshatra pair is explicitly illegible in this scan: chunk "
     "muhurta_chintamani_pg0022_c01 (v.25, conf 0.4) states outright 'The "
     "printed chart correlating the 28 yogas with vara and nakshatra is "
     "wholly illegible in the scan; no row could be reconstructed', and only "
     "gives 6 of 7 weekdays' starting points before breaking off mid-line; "
     "chunk muhurta_chintamani_pg0024_c01 separately confirms 'The printed "
     "table of the Cara, Dagdha, Mrtyu, Siddhi, Utpata and Amritasiddhi "
     "yogas is fragmented and illegible in the scan'. A different partial "
     "vara x nakshatra listing DOES appear at pg0023_c02 (conf 1.0, 'success "
     "in every object' / sarvartha-siddhi combinations) but is NOT "
     "self-identified as the Ananda-adi chart and cannot be safely mapped "
     "onto the 28 names without guessing — not attempted (B.10). Disposition "
     "stays not_in_corpus for the OPERATIONAL rule, on a fully translated, "
     "no-longer-ambiguous evidentiary basis. Ingestion work item: source a "
     "second edition/manuscript of Muhurta Chintamani ch.1 with a legible "
     "Ananda-adi chart, or a secondary published compilation, if the "
     "operational rule is ever wanted.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0021_c01, "
     "ch.1 vv.23-25 + pg0022_c01 + pg0024_c01, translated 2026-08-03, content_en re-read live "
     "2026-08-05, names citable / correlation chart illegible in source)", None),
    ("combination_yoga", "jvalamukhi_yoga", "not_in_corpus",
     "CONFIRMED (parihāra-graph enrichment pass, 2026-08-04): chunk "
     "muhurta_chintamani_pg0033_c01 was translated in the 2026-08-03 "
     "Muhūrta-Cintāmaṇi translation pass (MUHURTA_CHINTAMANI_TRANSLATION_"
     "REPORT_v1_0.md) and re-read directly against the live "
     "classical_text_chunks.content_en for this row. The earlier ambiguous "
     "Devanagari-only hit is now RESOLVED: the chunk is the twofold Guru-"
     "Makara (Jupiter-in-debilitation) regional-exemption passage (verse 52 "
     "ṭīkā), whose river-bounded geography lists 'Delhi (Indraprastha), "
     "Agra, Mathurā, Nadīnātha, Jvālāmukhī and so on up to the northern "
     "Himālaya' as places where the doṣa does NOT hold. This confirms the "
     "prior finding: 'Jvālāmukhī' here is the place name (Himachal Pradesh, "
     "on the Śoṇa river's northern-exemption side), not the Jvālāmukhī-yoga "
     "muhūrta doctrine — no yoga content is present in this chunk. No other "
     "of the 66 newly-translated parihāra-topic chunks names this yoga "
     "either (checked directly against their content_en, not re-derived from "
     "the report's summary alone). Disposition remains not_in_corpus (no "
     "usable STRUCTURED rule exists either way) — now on a fully translated, "
     "no-longer-ambiguous evidentiary basis rather than a homographic OCR "
     "guess. See also the 'jupiter_simha_makara_marriage_regional_dosha' "
     "parihara_scope row below, which extracts the genuine parihāra content "
     "this same chunk cluster (pg0031_c02..pg0034_c01) DOES carry.",
     "classical_text_chunks (text_id='muhurta_chintamani', chunk_id=muhurta_chintamani_pg0033_c01, ch.33 [pg0033, marriage/Vivaha section v.52], translated 2026-08-03, content_en re-read live 2026-08-04, confirmed place-name not yoga-doctrine)", None),

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

    # ── Parihāra-graph enrichment (2026-08-04): the 66 doṣa-parihāra-topic
    # muhurta_chintamani chunks translated by MUHURTA_CHINTAMANI_TRANSLATION_
    # REPORT_v1_0.md (2026-08-03), read directly against live content_en (not
    # paraphrased from the report's summary). Every row below traces to a real
    # chunk_id whose translated text was read in full. Same discipline as the
    # vishti_conditional_undertaking_exception row above: genuine, cited,
    # muhūrta-scope parihāra content that is NOT encoded as an unconditional
    # bg_parihara_rules row, because (per the exact reasoning that row already
    # established) kala_lattice_query.ts's matchingPariharas() cancels
    # unconditionally on a dosha_canonical_id match, and every finding below
    # carries a condition — an undertaking class, a region, a sub-window of an
    # existing doṣa span, or a doctrinal 'destroys ALL doṣas' claim the schema
    # has no wildcard for — that bg_parihara_rules cannot yet represent without
    # over-cancelling. Most of the 66 chunks were reviewed and are NOT
    # represented here at all: many are too fragmentary/OCR-corrupt to support
    # a citable rule (see each chunk's own low_confidence_flag/ocr_review_note),
    # and a large share of the "doṣa-parihāra" topic tag turned out to be
    # procedural muhūrta election material (dohada food lists, journey
    # conveyance-by-direction, gemstone/dakṣiṇā tables, avasthā-reckoning
    # method) rather than doṣa-cancellation content proper — skipped rather
    # than smoothed into a shape that doesn't fit (B.10).
    ("parihara_scope", "mrityu_krakaca_dagdha_hutasana_yoga_apavada", "not_computed",
     "A real, translated, threefold apavāda (exception) to the Mṛtyu, Krakaca, "
     "Dagdha (Vāradagdha) and Hutāśana yogas, verbatim from chunk "
     "muhurta_chintamani_pg0028_c02 (v.41): 'When the Moon is well-disposed, "
     "[the authorities] have declared the Mṛtyu, Krakaca, Dagdha and similar "
     "[yogas] to be auspicious. Some [hold that the doṣa ceases] after the "
     "first yāma; and others [hold that] they are censured only in yātrā (a "
     "journey).' The ṭīkā (chunk muhurta_chintamani_pg0029_c01, on v.42) "
     "confirms and extends this to Viṣa-yoga: 'the said malefic yogas carry no "
     "doṣa (affliction) after the first prahara... the said yogas are shunned "
     "in yātrā (a journey) only, and not in [other] undertakings.' This is "
     "activity-class-conditional (yātrā only, per one opinion) and further "
     "conditioned on Moon-disposition or time-elapsed-since-sunrise — none of "
     "which bg_parihara_rules or matchingPariharas() can evaluate. It does NOT "
     "resolve the pre-existing 'dagdha_yoga'/'mrityu_yoga'/'hutasana_yoga' "
     "not_in_corpus rows above (those cite a DIFFERENT, still-untranslated "
     "ch.17-18 tithi×vāra detection table for the yogas themselves — this "
     "finding is their apavāda clause, not their detector, and the two must "
     "not be conflated). Work item: same as vishti — an "
     "applies_to_activity_classes qualifier plus a time-elapsed/Moon-"
     "disposition condition mechanism, neither of which exists yet.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0028_c02', v.41, "
     "low_confidence_flag=false; chunk_id='muhurta_chintamani_pg0029_c01', "
     "v.42 ṭīkā, low_confidence_flag=true) — translated 2026-08-03, read live "
     "2026-08-04; schema gap: no activity-class qualifier, no Moon-disposition/"
     "elapsed-time condition mechanism", None),
    ("parihara_scope", "dagdha_tithi_saura_madhyadesha_restriction", "not_computed",
     "A complete, self-contained dagdha-tithi (burnt lunar-day) rule, keyed to "
     "the Sun's zodiac sign, found translated at chunk "
     "muhurta_chintamani_pg0109_c01 (v.66, Chapter 6/Vivāha section): 'When "
     "[the Sun] stands in Cāpa (Dhanus) or the last sign (Mīna), in Go (Vṛṣa) "
     "or Ghaṭa (Kumbha), in Karka or Aja (Meṣa), in Strī (Kanyā) or Mithuna, "
     "in Siṃha or Ali (Vṛścika), in Nakra (Makara) or Tulā — the even tithis "
     "(lunar days) beginning with the second are dagdha (burnt).' The ṭīkā "
     "gives the mapping explicitly (2nd/4th/6th/8th/10th/12th tithi per solar "
     "sign-pair) and states the built-in regional parihāra verbatim: 'These "
     "māsa-dagdha tithis are prohibited in Madhyadeśa alone [and not "
     "elsewhere].' No dagdha-tithi table of ANY kind exists in panchang_engine "
     "(grep-verified: zero matches for 'dagdha' across panchang_engine/*.py) "
     "— disposed not_computed (the doctrine IS now in-corpus and translated; "
     "no detector has been built), not not_in_corpus, mirroring the "
     "'gandanta'/degree_sensitive row's own computed/not_computed distinction "
     "above. This is a DIFFERENT dagdha-tithi formulation (solar-ingress-"
     "keyed) from the tithi×vāra table the pre-existing 'dagdha_yoga' row "
     "cites at ch.17-18 (still untranslated) — the two are not the same table "
     "and this finding does not resolve that row's gap. Even if implemented, "
     "the regional (Madhyadeśa-only) restriction is a schema gap "
     "bg_parihara_rules cannot represent (no region qualifier).",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0109_c01', v.66 "
     "mula+ṭīkā, low_confidence_flag=true but the ṭīkā's dagdha-tithi table "
     "and regional restriction are the review note's UNFLAGGED portion) — "
     "translated 2026-08-03, read live 2026-08-04; "
     "panchang_engine/shastra_tables.py + panchang_engine/timings.py "
     "(grep-verified: no dagdha table anywhere)", None),
    ("parihara_scope", "bhadra_mukha_puccha_subwindow", "not_computed",
     "The classical mukha (mouth)/puccha (tail) subdivision of Bhadrā "
     "(Viṣṭi karaṇa) — a genuine sub-window parihāra bg_muhurta_lattice's "
     "existing 'bhadra' factor (factor_family=combination_yoga) does not "
     "implement, since that emitter materializes the WHOLE Bhadrā span "
     "undifferentiated. Verbatim, chunk muhurta_chintamani_pg0029_c02 (v.44): "
     "'in the yāmas the last three ghaṭīs are the tail (puccha), which is "
     "auspicious. Likewise, by day the Viṣṭi born in the latter half of a "
     "tithi (lunar day) is auspicious, while by night it is the one born in "
     "the former half [that is auspicious].' The ṭīkā (chunk "
     "muhurta_chintamani_pg0030_c01) confirms: 'This puccha-Bhadrā is not "
     "malefic — that is, it is acceptable for auspicious work... a Bhadrā "
     "belonging to the latter half of a tithi is auspicious by day, and one "
     "belonging to the former half of a tithi is auspicious by night.' A "
     "further world-bound parihāra follows at v.45 (chunk "
     "muhurta_chintamani_pg0030_c02): Bhadrā's fruit occurs only in whichever "
     "world (mortal/heaven/nether, keyed to the Moon's sign) she dwells that "
     "day — 'there alone does she give her fruit, and not in another world — "
     "and this too is precisely a parihāra.' NOT encoded as a bg_parihara_rules "
     "row: the engine's blunt dosha_canonical_id match would, if seeded "
     "against 'bhadra', report the doṣa-bearing MUKHA portion as cancelled "
     "too — the exact over-cancellation failure mode the vishti row already "
     "refused. Ingestion work item: split the bg_muhurta_lattice bhadra "
     "emitter into mukha (doṣa) / puccha (non-doṣa) sub-spans using this "
     "verse's own ghaṭī arithmetic, before any parihāra row can safely cite "
     "it.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0029_c02', v.44, "
     "low_confidence_flag=true; chunk_id='muhurta_chintamani_pg0030_c01', "
     "v.44 ṭīkā-continued + v.45, low_confidence_flag=true; chunk_id="
     "'muhurta_chintamani_pg0030_c02', v.45 ṭīkā-concluded, "
     "low_confidence_flag=true) — translated 2026-08-03, read live "
     "2026-08-04; bg_muhurta_lattice.py's 'bhadra' factor_key (combination_"
     "yoga) does not sub-divide the span", None),
    ("parihara_scope", "jupiter_simha_makara_marriage_regional_dosha", "not_computed",
     "A rich, multiply-conditional pair of regional/degree/activity-class "
     "exemptions for Jupiter-in-Siṃha and Jupiter-in-Makara (his sign of "
     "debilitation), found translated across chunks "
     "muhurta_chintamani_pg0031_c02 through pg0034_c01 (v.48-53, Chapter 5/"
     "Vivāha section). Verbatim, v.49 (chunk pg0032_c01): 'When Jupiter is in "
     "Siṃha and in the Siṃha [navāṃśa], marriage is inauspicious; and [the "
     "doṣa holds] north of the Godāvarī and on the southern bank of the "
     "Bhāgīrathī — [it is] a doṣa there alone, not in another country, nor "
     "even when the Sun is in Meṣa.' The ṭīkā narrows further: applies to "
     "marriage only (by another opinion also upanayana), only the Siṃha "
     "navāṃśa of Siṃha (13°20′-16°40′, not the whole sign-transit), and not "
     "at all when the Sun is in Meṣa. v.52 (chunk pg0033_c01) states the "
     "mirror-image Makara rule: 'East of the Revā, west of the Gaṇḍakī, and "
     "north and south of the Śoṇa, Jupiter in his debilitation is not to be "
     "shunned; but in Koṅkaṇa, in Magadha, in Gauḍa and in Sindhu he is to be "
     "shunned in auspicious [undertakings]' — geographically INVERTED from "
     "the Siṃha rule (doṣa in named tracts, not doṣa across most of the named "
     "river-defined heartland), with a further Makara-navāṃśa-only narrowing "
     "and a 60-day exception for countries outside both named divisions. v.53 "
     "(chunk pg0034_c01) adds the separate lupta-saṃvatsara (lost-year) "
     "exception, itself region-bound to the Revā-Gaṅgā tract only. Every "
     "layer here (activity-class, navāṃśa-degree range, named-river "
     "geography, specific solar-sign exclusion) is a condition "
     "bg_parihara_rules' single free-text cancellation_condition_text field "
     "could HOLD but the engine cannot EVALUATE — encoding any one row here "
     "would misrepresent a five-way-conditional doctrine as a flat "
     "dosha_canonical_id match. See also the 'jvalamukhi_yoga' combination_"
     "yoga row above, whose CONFIRMED place-name (not yoga) finding comes "
     "from this same chunk cluster (pg0033_c01's geography list).",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0031_c02' through "
     "'muhurta_chintamani_pg0034_c01', v.48-53 mula+ṭīkā, all "
     "low_confidence_flag=true) — translated 2026-08-03, read live "
     "2026-08-04; schema gap: no navāṃśa-degree, region, or solar-sign "
     "qualifier columns", None),
    ("parihara_scope", "ravi_yoga_and_godhuli_sarva_dosha_nasha", "not_computed",
     "Two independent 'destroys/needs-no-consideration-of ALL doṣas' claims, "
     "the same wildcard-schema-gap ADJUDICATION-10 Part 1 already named for "
     "the Abhijit row (bg_parihara_rules has no all-doṣa/wildcard "
     "dosha_canonical_id convention — narrowing either of these to one "
     "representative doṣa, the way ADJUDICATION-10 narrowed Abhijit to "
     "rahu_kalam, is a deliberate campaign-level adjudication call this data "
     "pass does not have standing to make unilaterally). (1) Ravi-yoga, "
     "chunk muhurta_chintamani_pg0023_c01 (v.27): 'When, counted from the "
     "Sun's nakṣatra, the Moon['s nakṣatra] falls at [a distance] measured by "
     "4, [9], [6], 10 (dik), 13 (viśva) or 20 (nakha), the Ravi-yogas arise, "
     "and they destroy all doṣas (afflictions).' The ṭīkā: 'It is auspicious "
     "for every undertaking, and it destroys the whole mass of the doṣas "
     "stated above.' No 'ravi_yoga' factor_family/factor_key exists anywhere "
     "in bg_muhurta_lattice — genuinely not_computed, not merely un-encoded. "
     "(2) Godhūli, chunk muhurta_chintamani_pg0119_c01 (v.100-101): 'In it "
     "there is no nakṣatra..., no tithi..., no consideration of the lagna at "
     "all, nor vāra, ... nor any discussion of the muhūrta; nor yoga, nor the "
     "house of death (the eighth), nor yāmitra-doṣa at all. That godhūli has "
     "been declared by the sages to be commended for one's every "
     "undertaking,' with a three-season definition (Sun's disc congealed in "
     "Hemanta / half-set in the hot season / fully set in the rains). UNLIKE "
     "Ravi-yoga, 'godhuli' already IS a materialized bg_muhurta_lattice kalam "
     "factor_key (see the 'godhuli' day_part row above) — but its "
     "implementation (panchang_engine/timings.py: a fixed 24-minute window "
     "before/after sunset, year-round) does NOT reproduce this verse's "
     "three-season method, and carries no citation for either the window "
     "definition or the 'no doṣa whatsoever' claim. Left as "
     "computed_uncited_convention on the existing row rather than upgraded, "
     "because citing this verse there would overclaim: the verse's specific "
     "seasonal method is not what the current emitter computes (§N.7 — a "
     "citation must match what is actually computed, not merely be "
     "topically related).",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0023_c01', v.27 "
     "mula+ṭīkā, low_confidence_flag=true; chunk_id="
     "'muhurta_chintamani_pg0119_c01', v.100-101, low_confidence_flag=false) "
     "— translated 2026-08-03, read live 2026-08-04; panchang_engine/"
     "timings.py:compute_extended_auspicious (godhuli: fixed sunset±24min, "
     "no seasonal method, uncited)", None),
    ("parihara_scope", "regional_dosha_cluster_madhyadesha_gauda_malava_hunabanga", "not_computed",
     "A cluster of muhūrta doṣas this text itself discloses as regionally "
     "self-cancelling outside three named tracts, found translated at chunk "
     "muhurta_chintamani_pg0020_c01 (v.18-19): 'those tithis that are "
     "month-void, and likewise those lagnas that are declared void — they "
     "are to be shunned in Madhyadeśa [alone]; among other [peoples/regions] "
     "they do not vitiate... The lame (paṅgu), blind (andha) and one-eyed "
     "(kāṇa) lagnas, and the month-void rāśis (signs), are to be avoided in "
     "Gauḍa and Mālava; in another country they are not censured' — TWO "
     "separate regional carve-outs in one chunk (māsa-śūnya tithi/lagna → "
     "Madhyadeśa only; paṅgu/andha/kāṇa lagnas + māsa-śūnya rāśi → Gauḍa/"
     "Mālava only). Chunk muhurta_chintamani_pg0025_c01 (v.31 ṭīkā) adds a "
     "third tract for the compound tithi×vāra / tithi×nakṣatra / vāra×"
     "nakṣatra / triple-combination doṣas (the Hasta-Arka example among "
     "them): 'to be shunned in the Hūṇa country (Baṅga), in Bengal, and in "
     "Uttarakhaṇḍa (Khāndeś); in other countries they are not prohibited.' "
     "The underlying māsa-śūnya nakṣatra TABLE itself is illegible in this "
     "corpus's scan (chunk pg0020_c01's own note: 'the printed table of "
     "month-wise śūnya nakṣatras is broken up and illegible — not "
     "rendered') — so even the base doṣa this regional parihāra would cancel "
     "cannot itself be computed from this corpus; only the meta-rule (which "
     "regions the whole doṣa-family binds in) is legible. Region is not a "
     "qualifier bg_parihara_rules' schema carries.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0020_c01', v.17-"
     "19 mula+ṭīkā, low_confidence_flag=true; chunk_id="
     "'muhurta_chintamani_pg0025_c01', v.31 ṭīkā-completing, "
     "low_confidence_flag=true) — translated 2026-08-03, read live "
     "2026-08-04; base māsa-śūnya-nakṣatra table illegible in the scan "
     "(pg0020_c01), so not_computed rather than not_in_corpus is honest for "
     "the meta-rule only, not for the underlying doṣa", None),
    ("parihara_scope", "holashtaka_regional_marriage_dosha", "not_computed",
     "Holāṣṭaka (the 8 days preceding the Holikā/Phālguna-full-moon "
     "festival) — a well-defined, self-contained doṣa with a built-in "
     "regional parihāra, found translated at chunk "
     "muhurta_chintamani_pg0028_c01 (v.40): '[On the banks of the Vipāśā and "
     "the Irāvatī, on the bank of the Śatadru] and in Tripuṣkara, the eight "
     "days preceding the Holikā [festival] are never [fit] for marriage and "
     "other auspicious [acts].' The ṭīkā confirms the region-bound scope "
     "explicitly: 'In other countries these carry no doṣa.' Unlike most "
     "findings in this cluster, this ONE is close to self-contained (no "
     "activity-class narrowing beyond 'marriage and other auspicious acts', "
     "no degree-range) — the sole schema gap is the region qualifier itself. "
     "Flagged not_computed rather than encoded as a bg_parihara_rules row: "
     "region is not representable, and (per the vishti/mrityu-krakaca-dagdha "
     "precedent above) a row with no region qualifier would read as "
     "unconditionally cancelled everywhere the underlying Holāṣṭaka doṣa is "
     "detected — which the source explicitly does not license.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0028_c01', v.40 "
     "mula+ṭīkā, low_confidence_flag=true — the parihāra passage itself is "
     "the review note's explicitly-clean portion) — translated 2026-08-03, "
     "read live 2026-08-04; schema gap: no region qualifier column", None),
    ("parihara_scope", "pratishukra_venus_facing_apavada", "not_computed",
     "A cluster of activity-class and lineage (gotra) exceptions to the "
     "pratiśukra (Venus-facing/adverse-Venus) doṣa for dvirāgamana (a bride's "
     "formal second homecoming), found translated at chunks "
     "muhurta_chintamani_pg0123_c01, pg0123_c02 and pg0124_c01 (v.2-4, "
     "Chapter 8). Verbatim, v.3 (chunk pg0123_c01): 'On entering a city; in a "
     "calamity such as [invasion of] the territory; at a marriage (\"the "
     "seizing of the hand\"); on a pilgrimage to the gods or to a tīrtha; on "
     "[?]; and at the entry of a newly-wed bride — Bhārgava confronting does "
     "not become a producer of doṣa at all.' v.4 (chunk pg0124_c01) adds a "
     "puberty-timing exception and a full gotra exemption: 'If, while still "
     "in her father's house, the flowering of the breasts has occurred in "
     "women, there is no doṣa arising from the pratiśukra; likewise in the "
     "lineage of Bhṛgu, Aṅgiras, Vatsa, Vasiṣṭha, Kaśyapa, Atri and the sage "
     "Bharadvāja.' A named-undertaking-class list (city-entry, calamity, "
     "marriage, pilgrimage, bride's-entry) plus a gotra qualifier is exactly "
     "the shape bg_parihara_rules cannot hold — an activity-class list, not a "
     "single class, and a lineage condition with no analogue anywhere in the "
     "schema.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0123_c01', v.2-3 "
     "mula+ṭīkā, low_confidence_flag=true; chunk_id="
     "'muhurta_chintamani_pg0123_c02', v.3 ṭīkā-continued, "
     "low_confidence_flag=true; chunk_id='muhurta_chintamani_pg0124_c01', "
     "v.4 mula+ṭīkā, low_confidence_flag=true) — translated 2026-08-03, read "
     "live 2026-08-04; schema gap: no activity-class-list or lineage/gotra "
     "qualifier", None),
    ("parihara_scope", "vivaha_synastry_kuta_dosha_bhanga_scope_gap", "not_computed",
     "A genuinely THIRD category of parihāra content — synastry/compatibility "
     "doṣa-cancellation between a groom's and bride's charts (bhakūṭa, "
     "nāḍī-kūṭa, gaṇa-kūṭa, graha-maitrī, aṣṭama-rāśi/lagna) — that fits "
     "neither of bg_parihara_rules.scope's two CHECK-constrained values: not "
     "'natal' (a single chart's own dosha-bhaṅga, e.g. Maṅglik/Kāla-Sarpa) "
     "and not 'muhurta' (a chart-independent timing-window doṣa, e.g. Rāhu "
     "Kālam/Bhadrā) — it is a two-chart RELATIONAL doṣa, computed at "
     "matchmaking time from both nativities together. Rich, well-translated "
     "content exists: e.g. chunk muhurta_chintamani_pg0096_c01 (v.32, on the "
     "evil bhakūṭa): 'if one and the same planet lords the signs of groom "
     "and bride... the marriage is auspicious. It is likewise auspicious "
     "when the rāśi-lords are friends, provided there is nāḍī-śuddhi... and "
     "if the lords of the aṃśas... are mutually friendly and are also "
     "strong... then the doṣa (affliction) of enmity between the planets "
     "does not arise' — five distinct named cancellation mechanisms "
     "(ekādhipatya, rāśi-lord friendship, aṃśa-lord friendship, tārā-"
     "śuddhi, rāśi-vaśyatā), each independently sufficient. Chunk "
     "muhurta_chintamani_pg0116_c01/c02 (v.89-91) adds a general-purpose "
     "doṣa-quenching rule keyed to Mercury/Jupiter/Venus strength in kendra/"
     "koṇa. None of this is encodable in bg_parihara_rules without either "
     "misusing scope='natal' (wrong — this is not a single-chart condition) "
     "or scope='muhurta' (wrong — this is not a timing-window condition, and "
     "the doṣas named — bhakūṭa/nāḍī/gaṇa — are not bg_muhurta_lattice "
     "factor_keys and never will be, being relational, not temporal). "
     "Flagged here as a genuine schema-scope gap for the campaign to decide "
     "whether a third scope value or a wholly separate synastry-parihāra "
     "table is the right shape — a bigger design decision than a data-"
     "enrichment pass has standing to make.",
     "classical_text_chunks (chunk_id='muhurta_chintamani_pg0096_c01', v.31-"
     "33, low_confidence_flag=true; chunk_id='muhurta_chintamani_pg0096_c02', "
     "v.33-34, low_confidence_flag=true; chunk_id="
     "'muhurta_chintamani_pg0097_c01', v.34, low_confidence_flag=true; "
     "chunk_id='muhurta_chintamani_pg0116_c01', v.89-91, "
     "low_confidence_flag=true; chunk_id='muhurta_chintamani_pg0116_c02', "
     "v.91 ṭīkā-continued, low_confidence_flag=true) — translated 2026-08-03, "
     "read live 2026-08-04; schema gap: bg_parihara_rules.scope CHECK allows "
     "only ('natal','muhurta'), neither of which fits a two-chart relational "
     "doṣa", None),

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
        except Exception:
            # §N.8 Earned-Signal: returning a success-shaped
            # WriterResult(rows_inserted=0, notes="failed: ...") here is the
            # documented no-op-completion defect class — the orchestrator
            # treats any non-raising run() as OK and lights the asset while
            # all three tables sit empty (exactly what production run
            # 6fd72ed9 did on 2026-08-02). Log for context, then re-raise so
            # the runner's savepoint rollback + error-state path fires.
            logger.exception("[bg_parihara_rules] computation failed")
            raise

        try:
            with conn.cursor() as cur:
                rows_written += self._upsert_parihara(cur, parihara_rows)
                rows_written += self._upsert_activity_rules(cur, activity_rows)
                rows_written += self._upsert_census(cur, census_rows)
        except Exception:
            # §N.8: same re-raise discipline as the computation branch — a
            # partial insert must surface as an error state (the orchestrator's
            # savepoint rolls the partial write back), never as a
            # success-shaped "partial" WriterResult that lights the asset.
            logger.exception(
                "[bg_parihara_rules] insert failed after %d rows", rows_written,
            )
            raise

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
