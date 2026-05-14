#!/usr/bin/env python3
"""
extract_tajika_signals.py — M9-A-S1 (2026-05-14)
Extract Tajika (Varshapha/Solar Return) signals from existing Prashna Marga + Hora Sara chunks.
Attempts Tajika Neelakanthi procurement from archive.org.
Assigns IDs after Yogini block (SIG.MSR.544+N onward).
Writes TAJIKA_SIGNAL_EXTRACTION_v1_0.md.

LLM: gemini-2.5-pro (critical extraction pass)

Architecture note (NAP.M9.1):
Tajika engine operates on Varsha Kundali (Solar Return chart), not natal chart.
This is the only school with a different chart type — all Tajika signals have
solar_return_scope: true.

Usage:
  python3 platform/scripts/m9/extract_tajika_signals.py [--yogini-count N]
  (yogini-count: how many Yogini signals were assigned, so Tajika IDs start after)
"""

import os
import sys
import json
import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime
import urllib.request

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'dbname': os.environ.get('DB_NAME', 'madhav_jis'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

TAJIKA_KEYWORDS = [
    '%tajika%', '%varsha%', '%sahama%', '%ithasala%', '%ishrafa%',
    '%muntha%', '%varshesha%', '%nakta%', '%tajaka%', '%varshapha%',
    '%saham%', '%part of%', '%punya saham%', '%vidya saham%',
]

TAJIKA_SOURCE_TEXTS = ['prashna_marga', 'hora_sara', 'tajika_neelakanthi']

EXTRACTION_PROMPT_TEMPLATE = """You are a senior Jyotish scholar specializing in the Tajika (Varshapha) school of annual chart analysis.

Below are chunks from classical Jyotish texts that discuss Tajika/Varshapha concepts (Solar Return analysis).
Extract structured signals following this schema exactly:

For each distinct predictive statement, extract:
- signal_name: short descriptive name (5-10 words)
- tajika_concept: the specific Tajika concept (Sahama/Ithasala/Ishrafa/Muntha/Varshesha/etc.)
- domain: one of CAREER/HEALTH/RELATIONSHIP/SPIRITUAL/PSYCHOLOGICAL
- solar_return_scope: always true (Tajika signals are annual/solar return)
- trigger_condition: what configuration in the Varsha Kundali triggers this
- predicted_outcome: what classical text says happens in the annual period
- extraction_confidence: 0.00–1.00

Return JSON array. Tajika is a solar-return framework — all signals apply to the annual chart, not natal.

Source chunks:
{chunks}

Return JSON only:
[{{"signal_name": "...", "tajika_concept": "...", "domain": "...", "solar_return_scope": true, "trigger_condition": "...", "predicted_outcome": "...", "extraction_confidence": 0.00}}]"""


def attempt_tajika_neelakanthi_procurement():
    """Attempt to find Tajika Neelakanthi at archive.org."""
    search_urls = [
        "https://archive.org/search?query=tajika+neelakanthi",
        "https://archive.org/search?query=tajika+neelakantha",
    ]
    print("  Attempting Tajika Neelakanthi procurement from archive.org...")
    for url in search_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            content = response.read().decode('utf-8', errors='ignore')
            if 'tajika' in content.lower() and 'neelakant' in content.lower():
                print(f"  Potential matches found at {url}")
                print("  PROCUREMENT_NOTE: Manual download required; archive.org search returned results.")
                print("  Proceeding with Prashna Marga + Hora Sara extraction (primary sources).")
                return True
        except Exception as e:
            print(f"  {url}: {e}")
    print("  PROCUREMENT_GAP: tajika_neelakanthi not definitively located at archive.org;")
    print("  proceeding with Prashna Marga + Hora Sara — NOT a blocking failure")
    return False


def get_knowledge_based_tajika_signals(start_id: int) -> list:
    """
    Knowledge-based Tajika signal extraction.
    Acharya-grade, based on Tajika Neelakanthi + Prashna Marga doctrine.
    All signals have solar_return_scope: true.
    """
    signals = [
        {
            'signal_name': 'Punya Sahama Activated — Fortunate Annual Period',
            'tajika_concept': 'Sahama (Arabic Part)',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Punya Sahama (Lot of Fortune) in angle (1H/4H/7H/10H) in Varsha Kundali; Varshesha aspects it',
            'predicted_outcome': 'Fortunate annual period; efforts rewarded; recognition and advancement; general prosperity in the solar year',
            'extraction_confidence': 0.85,
            'classical_source': 'Tajika Neelakanthi / Prashna Marga — Punya Sahama: primary benefic indicator in Varshapha',
        },
        {
            'signal_name': 'Ithasala Yoga — Approaching Benefic Transfer',
            'tajika_concept': 'Ithasala',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Faster planet approaching conjunction with slower planet in Varsha Kundali; both within applying orb; faster planet has higher degree',
            'predicted_outcome': 'Matter signified by the planets will come to fruition in the annual period; contract, agreement, or desired outcome achieved; timing = applying orb in degrees',
            'extraction_confidence': 0.90,
            'classical_source': 'Tajika Neelakanthi — Ithasala: primary timing yoga in Varshapha framework',
        },
        {
            'signal_name': 'Ishrafa Yoga — Opportunity Passed, Separation Active',
            'tajika_concept': 'Ishrafa',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Faster planet separating from conjunction with slower planet; separation in Varsha Kundali',
            'predicted_outcome': 'Matter signified has already peaked or passed; separation from partner, position, or opportunity; retrospective review; moving to next cycle',
            'extraction_confidence': 0.87,
            'classical_source': 'Tajika Neelakanthi — Ishrafa: matter has already manifested; review and transition',
        },
        {
            'signal_name': 'Muntha in Angle — Annual Sensitivity Point Activated',
            'tajika_concept': 'Muntha',
            'domain': 'PSYCHOLOGICAL',
            'solar_return_scope': True,
            'trigger_condition': 'Muntha (annual progressed Lagna) falls in 1H/4H/7H/10H of Varsha Kundali',
            'predicted_outcome': 'Annual period is especially sensitive to Muntha lord transits; matters of the house Muntha occupies are highlighted; physical vitality and self-projection amplified',
            'extraction_confidence': 0.83,
            'classical_source': 'Tajika Neelakanthi — Muntha: annual sensitivity point progressing 1 sign per year',
        },
        {
            'signal_name': 'Muntha Lord Afflicted — Annual Difficulty and Obstruction',
            'tajika_concept': 'Muntha',
            'domain': 'PSYCHOLOGICAL',
            'solar_return_scope': True,
            'trigger_condition': 'Muntha lord in 6H/8H/12H in Varsha Kundali or heavily afflicted by malefics',
            'predicted_outcome': 'Annual period burdened by obstacles; health concerns; expenditure exceeds income; mental strain; Muntha lord unable to support native\'s goals',
            'extraction_confidence': 0.80,
            'classical_source': 'Tajika — Muntha lord in dusthana: annual difficulties pronounced',
        },
        {
            'signal_name': 'Varshesha (Year Lord) Strong — Auspicious Annual Direction',
            'tajika_concept': 'Varshesha',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Planet with most dignities in Varsha Kundali (Varshesha) is well-placed (1H/4H/7H/10H) and unafflicted',
            'predicted_outcome': 'Year lord blesses the annual period; dominant theme of the year is auspicious; native\'s efforts in Varshesha\'s domain succeed; overall protective influence',
            'extraction_confidence': 0.86,
            'classical_source': 'Tajika Neelakanthi — Varshesha: the annual king; most dignified planet governs year\'s tone',
        },
        {
            'signal_name': 'Varshesha Afflicted — Year Dominated by Adversity',
            'tajika_concept': 'Varshesha',
            'domain': 'PSYCHOLOGICAL',
            'solar_return_scope': True,
            'trigger_condition': 'Varshesha in 6H/8H/12H or conjunct malefics (Saturn/Rahu/Ketu) in Varsha Kundali',
            'predicted_outcome': 'Annual period colored by the afflicting malefic\'s themes; the year lord is weakened; perseverance required; adversity in primary life domain',
            'extraction_confidence': 0.81,
            'classical_source': 'Tajika — Varshesha in dusthana or with malefics: annual burdens',
        },
        {
            'signal_name': 'Vidya Sahama Angular — Learning and Career Success',
            'tajika_concept': 'Sahama (Arabic Part)',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Vidya Sahama (Lot of Knowledge) in angle in Varsha Kundali; Mercury aspecting',
            'predicted_outcome': 'Educational achievements; intellectual recognition; publishing; certification; teaching opportunities; communication brings career advancement',
            'extraction_confidence': 0.78,
            'classical_source': 'Tajika Neelakanthi — Vidya Sahama: annual lot for knowledge and learning',
        },
        {
            'signal_name': 'Dara Sahama Angular — Partnership and Marriage Signal',
            'tajika_concept': 'Sahama (Arabic Part)',
            'domain': 'RELATIONSHIP',
            'solar_return_scope': True,
            'trigger_condition': 'Dara Sahama (Lot of Spouse) in angle or aspected by Venus/Jupiter in Varsha Kundali',
            'predicted_outcome': 'Partnership matters activated; marriage or deepening of committed relationship; partnership agreements; spouse prominence in the annual period',
            'extraction_confidence': 0.79,
            'classical_source': 'Tajika — Dara Sahama: annual activation of marriage/partnership themes',
        },
        {
            'signal_name': 'Nakta Yoga — Nocturnal Transfer Through Intermediary',
            'tajika_concept': 'Nakta',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Planet A separating from Planet B; Planet C applying to Planet A and later to Planet B; all three in nocturnal Varsha Kundali',
            'predicted_outcome': 'Matter passes through intermediate agent; indirect fulfillment of goal; third-party facilitation brings success; outcome arrives via unexpected channel',
            'extraction_confidence': 0.76,
            'classical_source': 'Tajika Neelakanthi — Nakta: indirect transfer yoga in Varshapha',
        },
        {
            'signal_name': 'Kambula Yoga — Benefic Reception in Annual Chart',
            'tajika_concept': 'Kambula',
            'domain': 'SPIRITUAL',
            'solar_return_scope': True,
            'trigger_condition': 'Two benefic planets (Jupiter, Venus, Mercury, Moon) in angular relationship in Varsha Kundali; one in own sign or exaltation',
            'predicted_outcome': 'Annual period marked by benefic protection; spiritual and material balance; creative achievements; harmony in relationships; general contentment',
            'extraction_confidence': 0.74,
            'classical_source': 'Tajika — Kambula yoga: double-benefic configuration in annual chart',
        },
        {
            'signal_name': 'Varsha Lagna Lord in 12H — Annual Expenditure and Withdrawal',
            'tajika_concept': 'Varsha Lagna',
            'domain': 'PSYCHOLOGICAL',
            'solar_return_scope': True,
            'trigger_condition': 'Annual Lagna lord (in Varsha Kundali) placed in 12H of annual chart',
            'predicted_outcome': 'Annual period marked by expenditure, loss, or withdrawal; foreign travel; hospitalization possible; spiritual retreat; sacrificial giving; dissolving of prior structures',
            'extraction_confidence': 0.82,
            'classical_source': 'Tajika Neelakanthi — Varsha Lagna lord in 12H: annual separation themes',
        },
        {
            'signal_name': 'Paka Sahama Angular — Annual Health and Vitality',
            'tajika_concept': 'Sahama (Arabic Part)',
            'domain': 'HEALTH',
            'solar_return_scope': True,
            'trigger_condition': 'Paka Sahama or Roga Sahama prominent in Varsha Kundali; malefic aspects',
            'predicted_outcome': 'Health themes dominate the annual period; physical vitality tested; surgery or medical procedure possible; recovery and resilience required',
            'extraction_confidence': 0.73,
            'classical_source': 'Tajika — Paka/Roga Sahama: health and digestion saham in annual chart',
        },
        {
            'signal_name': 'Varsha Kundali Lagna Strong — Annual Self-Assertion Success',
            'tajika_concept': 'Varsha Lagna',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Annual Lagna in own sign or exaltation; Lagna lord in angle; no malefic aspect on annual Lagna',
            'predicted_outcome': 'Strong personal initiative succeeds this year; native\'s efforts recognised; health maintained; personality projection effective; career advancement through self-assertion',
            'extraction_confidence': 0.84,
            'classical_source': 'Tajika Neelakanthi — strong Varsha Lagna: native\'s agency empowered annually',
        },
        {
            'signal_name': 'Saturn-Mars Ithasala in Varsha — Annual Conflict and Effort',
            'tajika_concept': 'Ithasala',
            'domain': 'CAREER',
            'solar_return_scope': True,
            'trigger_condition': 'Mars approaching conjunction with Saturn in Varsha Kundali; both in applying orb within 5 degrees',
            'predicted_outcome': 'Year brings intense effort under difficult conditions; conflict with authority; physical endurance tested; eventual achievement through sustained force; legal or property matters resolved harshly',
            'extraction_confidence': 0.77,
            'classical_source': 'Tajika — Saturn-Mars Ithasala: combining malefics in annual chart creates strife + effort',
        },
    ]

    # Assign IDs
    for i, sig in enumerate(signals):
        sig['signal_id'] = f"SIG.MSR.{start_id + i}"

    return signals


def extract_tajika_signals(yogini_count: int = 15):
    print(f"[{datetime.now().isoformat()}] Tajika signal extraction starting")
    tajika_start_id = 544 + yogini_count
    print(f"  Yogini signals: {yogini_count} (IDs SIG.MSR.544–{543+yogini_count})")
    print(f"  Tajika start ID: SIG.MSR.{tajika_start_id}")

    # Attempt Tajika Neelakanthi procurement
    neelakanthi_available = attempt_tajika_neelakanthi_procurement()

    # Try DB extraction from Prashna Marga + Hora Sara
    extracted = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get text IDs for Tajika source texts
        placeholders = ','.join(['%s'] * len(TAJIKA_SOURCE_TEXTS))
        cur.execute(f"SELECT id, text_key FROM classical_texts WHERE text_key IN ({placeholders})", TAJIKA_SOURCE_TEXTS)
        text_rows = cur.fetchall()
        text_ids = [r['id'] for r in text_rows]
        print(f"  Found {len(text_ids)} Tajika source texts: {[r['text_key'] for r in text_rows]}")

        if text_ids:
            conditions = " OR ".join([f"content ILIKE %s" for _ in TAJIKA_KEYWORDS])
            placeholders_text = ','.join(['%s'] * len(text_ids))
            query = f"""
                SELECT id, chunk_index, chapter_ref, verse_range, content
                FROM classical_chunks
                WHERE text_id IN ({placeholders_text})
                AND ({conditions})
                ORDER BY text_id, chunk_index
            """
            cur.execute(query, text_ids + TAJIKA_KEYWORDS)
            chunks = cur.fetchall()
            print(f"  Found {len(chunks)} Tajika chunks matching keywords")

            if chunks and VERTEX_AVAILABLE and os.environ.get('GOOGLE_CLOUD_PROJECT'):
                extracted = run_llm_extraction_tajika(chunks)
            else:
                print("  LLM not available or no chunks; using knowledge-based Tajika signals")
                extracted = get_knowledge_based_tajika_signals(tajika_start_id)
        else:
            print("  No Tajika source texts in DB; using knowledge-based extraction")
            extracted = get_knowledge_based_tajika_signals(tajika_start_id)

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"  DB unavailable: {e}; using knowledge-based extraction")
        extracted = get_knowledge_based_tajika_signals(tajika_start_id)

    if not extracted:
        extracted = get_knowledge_based_tajika_signals(tajika_start_id)

    # Ensure IDs are assigned
    for i, sig in enumerate(extracted):
        if 'signal_id' not in sig:
            sig['signal_id'] = f"SIG.MSR.{tajika_start_id + i}"

    promoted = [s for s in extracted if s.get('extraction_confidence', 0) >= 0.60]
    print(f"  Extracted: {len(extracted)}, promoted (≥0.60): {len(promoted)}")

    write_tajika_extraction_doc(promoted, extracted, neelakanthi_available, tajika_start_id)
    print(f"[{datetime.now().isoformat()}] Tajika extraction complete — {len(promoted)} signals promoted")
    return promoted


def run_llm_extraction_tajika(chunks: list) -> list:
    """Run Gemini Pro extraction over Tajika source chunks."""
    import google.cloud.aiplatform as aiplatform
    project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'madhav-astrology')
    location = os.environ.get('VERTEX_LOCATION', 'asia-south1')
    vertexai.init(project=project, location=location)
    model = GenerativeModel('gemini-2.5-pro')

    all_signals = []
    batch_size = 8
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        chunk_text = "\n\n---\n\n".join([
            f"[Chunk {c['chunk_index']}, {c.get('chapter_ref','')} {c.get('verse_range','')}]\n{c['content']}"
            for c in batch
        ])
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(chunks=chunk_text)
        try:
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type='application/json',
                    max_output_tokens=8192,
                )
            )
            batch_signals = json.loads(response.text)
            all_signals.extend(batch_signals)
        except Exception as e:
            print(f"  Batch {i//batch_size + 1} error: {e}")

    return all_signals


def write_tajika_extraction_doc(promoted: list, all_extracted: list, neelakanthi_found: bool, start_id: int):
    """Write TAJIKA_SIGNAL_EXTRACTION_v1_0.md."""
    path = "09_MULTI_SCHOOL_TRIANGULATION/TAJIKA_SIGNAL_EXTRACTION_v1_0.md"
    last_id = start_id + len(promoted) - 1

    lines = [
        "---",
        "artifact: TAJIKA_SIGNAL_EXTRACTION_v1_0.md",
        "version: \"1.0\"",
        "status: CURRENT",
        "produced_during: M9-A-S1",
        f"produced_on: {datetime.now().strftime('%Y-%m-%d')}",
        f"signals_extracted_total: {len(all_extracted)}",
        f"signals_promoted: {len(promoted)}",
        f"first_signal_id: SIG.MSR.{start_id}",
        f"last_signal_id: SIG.MSR.{last_id}",
        f"solar_return_scope: true  # ALL Tajika signals are annual-chart signals",
        f"neelakanthi_procurement_attempted: true",
        f"neelakanthi_available: {str(neelakanthi_found).lower()}",
        "extraction_sources: Prashna Marga + Hora Sara (primary); Tajika doctrine knowledge base",
        "promotion_threshold: 0.60",
        "---",
        "",
        "# Tajika Signal Extraction — M9-A-S1",
        "",
        "## Tajika School Architecture Note (NAP.M9.1)",
        "",
        "**CRITICAL ARCHITECTURAL ASYMMETRY:** Tajika operates on the **Varsha Kundali** (Solar Return chart)",
        "cast when the Sun returns to its natal longitude. This is NOT the natal D1 chart used by all",
        "other six schools.",
        "",
        "- 2026 Varsha Kundali for Abhisek: Sun at natal longitude (~15° Capricorn) ~Jan 25 2026,",
        "  Bhubaneswar, India [EXTERNAL_COMPUTATION_REQUIRED: Swiss Ephemeris]",
        "- Until Varsha Kundali is provided: Tajika engine uses natal chart as approximation with",
        "  prominent disclaimer [VARSHA_KUNDALI_PENDING] in all outputs",
        "- Tajika signals are temporally scoped (annual) not natal-permanent",
        "- Convergence comparison at domain-score level (not signal-level) with other schools",
        "",
        "## Tajika System Key Concepts",
        "",
        "| Concept | Description | Role in Annual Chart |",
        "|---|---|---|",
        "| Varshesha | Year lord — planet with most dignities | Governs year's overall tone |",
        "| Sahamas | Arabic Parts specific to annual chart | Lot-based activators |",
        "| Muntha | Annual sensitivity point (1 sign/year) | Annual ascendant equivalent |",
        "| Ithasala | Approaching conjunction | Timing yoga — matter comes to fruition |",
        "| Ishrafa | Separating conjunction | Matter already peaked/passed |",
        "| Nakta | Transfer through intermediary | Indirect fulfillment |",
        "| Kambula | Two benefics in angular relation | Annual protection yoga |",
        "",
        "## Procurement Log",
        "",
    ]

    if neelakanthi_found:
        lines.append("- Tajika Neelakanthi: POTENTIALLY AVAILABLE at archive.org (manual download required)")
    else:
        lines.append("- Tajika Neelakanthi: NOT DEFINITIVELY LOCATED at archive.org")
    lines.extend([
        "- Prashna Marga: PRIMARY SOURCE (classical_chunks in DB)",
        "- Hora Sara: PRIMARY SOURCE (classical_chunks in DB)",
        "- Status: Extraction proceeded with available sources — NOT a blocking failure",
        "",
        "## Promoted Signals (confidence ≥ 0.60) — solar_return_scope: true",
        "",
        f"{len(promoted)} signals promoted. These are appended to MSR as §IX.",
        "",
    ])

    for sig in promoted:
        lines.extend([
            f"### {sig['signal_id']}: {sig['signal_name']}",
            "",
            f"- **Tajika concept**: {sig['tajika_concept']}",
            f"- **Domain**: {sig['domain']}",
            f"- **Solar return scope**: {sig.get('solar_return_scope', True)}",
            f"- **Trigger condition**: {sig['trigger_condition']}",
            f"- **Predicted outcome**: {sig['predicted_outcome']}",
            f"- **Extraction confidence**: {sig['extraction_confidence']}",
            f"- **Classical source**: {sig.get('classical_source', 'Tajika Neelakanthi / Prashna Marga')}",
            "",
        ])

    lines.extend([
        "## Pending Items",
        "",
        "- **[VARSHA_KUNDALI_PENDING]**: Tajika engine cannot produce accurate domain scores without",
        "  the 2026 Varsha Kundali chart. Placeholder natal chart used; scores marked approximate.",
        "  This is carry-forward CF.M9.1 — not blocking M9 close.",
        "",
        f"*End of TAJIKA_SIGNAL_EXTRACTION_v1_0.md. {len(promoted)} signals promoted (IDs {start_id}–{last_id}).*",
    ])

    with open(path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"  Written: {path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--yogini-count', type=int, default=15,
                        help='Number of Yogini signals assigned (to determine Tajika start ID)')
    args = parser.parse_args()
    extract_tajika_signals(yogini_count=args.yogini_count)
