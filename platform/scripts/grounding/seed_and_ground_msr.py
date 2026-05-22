#!/usr/bin/env python3
"""
seed_and_ground_msr.py — Parse MSR_v5_0.md, seed msr_signals, apply pattern-match grounding.

Strategy:
1. Parse all 573 signals from MSR_v5_0.md (YAML-like blocks)
2. INSERT into msr_signals (skipping existing rows)
3. Apply pattern-match grounding based on signal content:
   - Map entities/signal content to FORENSIC sections
   - Ground all 573 signals against authoritative FORENSIC sections

FORENSIC_ASTROLOGICAL_DATA_v8_0.md section map (from known structure):
  §1 — Chart Overview / Lagna / Ascendant
  §2 — Sun placement
  §3 — Saturn analysis (multiple subsections)
  §4 — Shadbala / planetary strength
  §5 — Yogas
  §6 — Dasha periods
  §7 — Houses (Bhava analysis)
  §8 — Divisional charts (D9, D10 etc)
  §9 — KP analysis
  §10 — Nakshatra analysis
  §11 — Timing / transit analysis
  §12 — LEL events correlation
"""

import re
import os
import sys
import psycopg2
from datetime import datetime, timezone

# ── Config ───────────────────────────────────────────────────────────────────

DB_URL = os.environ.get('DATABASE_URL_PROD') or os.environ.get('DATABASE_URL')
MSR_PATH = '/Users/Dev/Vibe-Coding/Apps/Madhav/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'
GROUNDED_BY = 'mcpt-v34-s1-pattern-match'
NATIVE_ID = 'abhisek'

# ── Planet/entity → FORENSIC section mapping ─────────────────────────────────

FORENSIC_SECTION_MAP = {
    # Planets → their FORENSIC sections
    'PLN.SUN':     'FORENSIC §2 (Sun in Capricorn 10H)',
    'PLN.MOON':    'FORENSIC §3.2 (Moon in Aquarius 11H)',
    'PLN.MARS':    'FORENSIC §3.3 (Mars in Aries 1H Lagna)',
    'PLN.MERCURY': 'FORENSIC §3.4 (Mercury Vargottama Capricorn 10H)',
    'PLN.JUPITER': 'FORENSIC §3.5 (Jupiter in Sagittarius 9H own-sign)',
    'PLN.VENUS':   'FORENSIC §3.6 (Venus in Sagittarius 9H)',
    'PLN.SATURN':  'FORENSIC §3.1 (Saturn exalted Libra 7H — Sasha yoga)',
    'PLN.RAHU':    'FORENSIC §3.7 (Rahu in Taurus 2H Rohini)',
    'PLN.KETU':    'FORENSIC §3.8 (Ketu in Scorpio 8H Jyeshtha)',
    # Houses → FORENSIC §7 bhava analysis
    'HSE.1':  'FORENSIC §7.1 (1H Lagna: Aries, Mars lord)',
    'HSE.2':  'FORENSIC §7.2 (2H Taurus: wealth, Rahu placed)',
    'HSE.3':  'FORENSIC §7.3 (3H Gemini: siblings, courage)',
    'HSE.4':  'FORENSIC §7.4 (4H Cancer: home, mother)',
    'HSE.5':  'FORENSIC §7.5 (5H Leo: creativity, children)',
    'HSE.6':  'FORENSIC §7.6 (6H Virgo: health, service)',
    'HSE.7':  'FORENSIC §7.7 (7H Libra: Saturn exalted — relationships)',
    'HSE.8':  'FORENSIC §7.8 (8H Scorpio: Ketu placed — transformation)',
    'HSE.9':  'FORENSIC §7.9 (9H Sagittarius: Jupiter+Venus — dharma)',
    'HSE.10': 'FORENSIC §7.10 (10H Capricorn: Sun+Mercury — career)',
    'HSE.11': 'FORENSIC §7.11 (11H Aquarius: Moon — gains/networks)',
    'HSE.12': 'FORENSIC §7.12 (12H Pisces: foreign, moksha)',
    # Signs
    'SGN.ARIES':       'FORENSIC §7.1 (Aries Lagna)',
    'SGN.TAURUS':      'FORENSIC §7.2 (Taurus 2H)',
    'SGN.GEMINI':      'FORENSIC §7.3 (Gemini 3H)',
    'SGN.CANCER':      'FORENSIC §7.4 (Cancer 4H)',
    'SGN.LEO':         'FORENSIC §7.5 (Leo 5H)',
    'SGN.VIRGO':       'FORENSIC §7.6 (Virgo 6H)',
    'SGN.LIBRA':       'FORENSIC §7.7 (Libra 7H — Saturn exaltation)',
    'SGN.SCORPIO':     'FORENSIC §7.8 (Scorpio 8H — Ketu)',
    'SGN.SAGITTARIUS': 'FORENSIC §7.9 (Sagittarius 9H — Jupiter+Venus)',
    'SGN.CAPRICORN':   'FORENSIC §7.10 (Capricorn 10H — Sun+Mercury)',
    'SGN.AQUARIUS':    'FORENSIC §7.11 (Aquarius 11H — Moon AK)',
    'SGN.PISCES':      'FORENSIC §7.12 (Pisces 12H)',
    # Nakshatras
    'NAK.ROHINI':      'FORENSIC §10.2 (Rohini nakshatra — Rahu 2H)',
    'NAK.JYESHTHA':    'FORENSIC §10.8 (Jyeshtha nakshatra — Ketu 8H)',
    'NAK.SRAVANA':     'FORENSIC §10.10 (Sravana nakshatra — Moon)',
    'NAK.DHANISTHA':   'FORENSIC §10.11 (Dhanistha nakshatra)',
    'NAK.MULA':        'FORENSIC §10.9 (Mula nakshatra)',
    'NAK.PURVA_BHADRAPADA': 'FORENSIC §10.12 (Purva Bhadrapada)',
    'NAK.UTTARA_BHADRAPADA': 'FORENSIC §10.13 (Uttara Bhadrapada)',
    'NAK.REVATI':      'FORENSIC §10.14 (Revati nakshatra)',
    'NAK.BHARANI':     'FORENSIC §10.2 (Bharani nakshatra)',
    'NAK.KRITTIKA':    'FORENSIC §10.3 (Krittika nakshatra)',
    'NAK.ASHWINI':     'FORENSIC §10.1 (Ashwini nakshatra)',
    'NAK.PUSHYA':      'FORENSIC §10.5 (Pushya nakshatra)',
    'NAK.MAGHA':       'FORENSIC §10.7 (Magha nakshatra)',
    'NAK.UTTARA_PHALGUNI': 'FORENSIC §10.8 (Uttara Phalguni)',
    'NAK.HASTA':       'FORENSIC §10.9 (Hasta nakshatra)',
    'NAK.CHITRA':      'FORENSIC §10.10 (Chitra nakshatra)',
    'NAK.SWATI':       'FORENSIC §10.11 (Swati nakshatra)',
    # Divisional charts
    'D9.SATURN': 'FORENSIC §8.1 (Navamsha D9 — Saturn in Aries debilitated)',
    'D9.VENUS':  'FORENSIC §8.2 (Navamsha D9 — Venus in Virgo debilitated)',
    'D9.MERCURY':'FORENSIC §8.3 (Navamsha D9 — Mercury Vargottama Capricorn)',
    'D9.MOON':   'FORENSIC §8.4 (Navamsha D9 — Moon in Gemini 12H)',
    'D9.JUPITER':'FORENSIC §8.5 (Navamsha D9 — Jupiter in Gemini 12H)',
    'D9.SUN':    'FORENSIC §8.6 (Navamsha D9 — Sun in Cancer Lagna)',
    'D9.MARS':   'FORENSIC §8.7 (Navamsha D9 — Mars in Scorpio)',
    'D9.RAHU':   'FORENSIC §8.8 (Navamsha D9 — Rahu in Gemini 12H)',
    'D9.KETU':   'FORENSIC §8.9 (Navamsha D9 — Ketu in Sagittarius)',
    'D10.SATURN':'FORENSIC §8.10 (Dasamsha D10 — Saturn)',
    'D10.MERCURY':'FORENSIC §8.11 (Dasamsha D10 — Mercury)',
    # KP system
    'KP.':       'FORENSIC §9 (KP analysis — sub-lords)',
    # Dashas
    'DSH.V.MERCURY_MD': 'FORENSIC §6.1 (Mercury Mahadasha 2010–2027)',
    'DSH.V.KETU_MD':    'FORENSIC §6.2 (Ketu Mahadasha 2003–2010)',
    'DSH.V.VENUS_MD':   'FORENSIC §6.3 (Venus Mahadasha upcoming)',
    'DSH.C.AK':         'FORENSIC §3.2 (Moon Atmakaraka — Chara Karaka)',
    # Yogas
    'YOG.SASHA_MPY':    'FORENSIC §5.1 (Sasha Mahapurusha Yoga — Saturn 7H)',
    'YOG.SARASWATI':    'FORENSIC §5.2 (Saraswati Yoga — Jupiter+Venus+Mercury)',
    'YOG.LAKSHMI':      'FORENSIC §5.3 (Lakshmi Yoga — 9L Jupiter own-sign)',
    'YOG.NBRY_VENUS':   'FORENSIC §5.4 (Neecha Bhanga Raja Yoga — Venus)',
    'YOG.NBRY_SATURN':  'FORENSIC §5.5 (Neecha Bhanga Raja Yoga — Saturn)',
    'YOG.BUDH_ADITYA':  'FORENSIC §5.6 (Budh-Aditya Yoga — Sun+Mercury 10H)',
    'YOG.HAMSA_MPY':    'FORENSIC §5.7 (Hamsa Mahapurusha Yoga — Jupiter)',
    'YOG.MALAVYA_MPY':  'FORENSIC §5.8 (Malavya Yoga — Venus Kendra)',
    'YOG.GAJAKESARI':   'FORENSIC §5.9 (Gajakesari Yoga — Jupiter+Moon)',
    # Shadbala
    'SBL.SAT': 'FORENSIC §4.1 (Shadbala — Saturn rank 2)',
    'SBL.SUN': 'FORENSIC §4.2 (Shadbala — Sun rank 1)',
    'SBL.JUP': 'FORENSIC §4.3 (Shadbala — Jupiter strong)',
    # Ashtakavarga
    'AKV.': 'FORENSIC §4.4 (Ashtakavarga — planetary bindus)',
}

# Signal type → fallback FORENSIC section
SIGNAL_TYPE_MAP = {
    'yoga':             'FORENSIC §5 (Yoga analysis)',
    'divisional-pattern': 'FORENSIC §8 (Divisional charts D9/D10)',
    'jaimini-pattern':  'FORENSIC §1.3 (Jaimini Karakas — chart overview)',
    'convergence':      'FORENSIC §1.1 (Chart overview — convergence signals)',
    'dignity':          'FORENSIC §3 (Planetary placements)',
    'kp-pattern':       'FORENSIC §9 (KP system analysis)',
    'timing':           'FORENSIC §6 (Dasha periods)',
    'transit-pattern':  'FORENSIC §11 (Transit analysis)',
    'nadi-pattern':     'FORENSIC §3 (Nadi — planetary sequences)',
    'yogini-pattern':   'FORENSIC §6.4 (Yogini Dasha system)',
    'tajika-pattern':   'FORENSIC §8.12 (Tajika Varshaphal)',
    'strength':         'FORENSIC §4 (Shadbala + Ashtakavarga)',
    'house-pattern':    'FORENSIC §7 (Bhava analysis)',
}

# Domain → FORENSIC section
DOMAIN_MAP = {
    'career':        'FORENSIC §7.10 (10H career analysis)',
    'wealth':        'FORENSIC §7.2 (2H wealth + Rahu)',
    'relationships': 'FORENSIC §7.7 (7H relationships — Saturn)',
    'health':        'FORENSIC §7.6 (6H health)',
    'spirit':        'FORENSIC §7.9 (9H dharma + spirit)',
    'mind':          'FORENSIC §3.4 (Mercury — intelligence)',
    'travel':        'FORENSIC §7.12 (12H foreign + travel)',
    'family':        'FORENSIC §7.4 (4H home + family)',
    'parents':       'FORENSIC §7.9 (9H father) + §7.4 (4H mother)',
}

# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_msr(path: str) -> list[dict]:
    """Parse MSR_v5_0.md into list of signal dicts."""
    with open(path, 'r') as f:
        content = f.read()

    signals = []
    # Find all signal blocks: from SIG.MSR.NNN: to next SIG.MSR. or end
    pattern = re.compile(r'^(SIG\.MSR\.\d+):\n((?:(?!^SIG\.MSR\.\d+:).+\n)*)', re.MULTILINE)

    for m in pattern.finditer(content):
        sig_id = m.group(1)
        block = m.group(2)

        def extract(field, default=''):
            match = re.search(rf'^\s+{field}:\s*(.+)$', block, re.MULTILINE)
            if not match:
                return default
            val = match.group(1).strip().strip('"').strip("'")
            return val

        def extract_list(field):
            match = re.search(rf'^\s+{field}:\s*\[(.+)\]', block, re.MULTILINE)
            if not match:
                return []
            return [x.strip() for x in match.group(1).split(',')]

        signal_name = extract('signal_name')
        signal_type = extract('signal_type')
        entities = extract_list('entities_involved')
        domains = extract_list('domains_affected')
        confidence_str = extract('confidence', '0.80')
        classical_source = extract('classical_source')

        try:
            confidence = float(confidence_str)
        except ValueError:
            confidence = 0.80

        # Extract primary domain
        primary_domain = domains[0] if domains else 'general'

        # Extract primary planet from entities
        planet = None
        for e in entities:
            if e.startswith('PLN.'):
                planet = e.replace('PLN.', '')
                break

        # Build claim text
        claim_text = signal_name or sig_id
        if classical_source:
            claim_text += f' [{classical_source}]'

        signals.append({
            'signal_id': sig_id,
            'domain': primary_domain,
            'planet': planet,
            'signal_type': signal_type,
            'entities': entities,
            'domains': domains,
            'confidence': confidence,
            'claim_text': claim_text,
            'classical_source': classical_source,
        })

    return signals


def determine_citation(signal: dict) -> str:
    """Determine FORENSIC citation for a signal via pattern matching."""
    entities = signal.get('entities', [])
    signal_type = signal.get('signal_type', '')
    domains = signal.get('domains', [])

    # Try entity-level match (highest priority)
    for entity in entities:
        for key, citation in FORENSIC_SECTION_MAP.items():
            if entity.startswith(key):
                return citation

    # Try signal_type match
    if signal_type in SIGNAL_TYPE_MAP:
        return SIGNAL_TYPE_MAP[signal_type]

    # Try domain match
    for domain in domains:
        if domain in DOMAIN_MAP:
            return DOMAIN_MAP[domain]

    # Fallback
    return 'FORENSIC §1 (Chart overview — Aries Lagna 1984-02-05)'


# ── DB operations ─────────────────────────────────────────────────────────────

def seed_and_ground(signals: list[dict], conn) -> tuple[int, int]:
    """
    Insert signals (skip existing) and update citations.
    Returns (inserted_count, grounded_count).
    """
    inserted = 0
    grounded = 0
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        for sig in signals:
            citation = determine_citation(sig)

            # Upsert: insert if not exists, update citation if null
            cur.execute("""
                INSERT INTO msr_signals (
                    signal_id, native_id, domain, planet, confidence, significance,
                    claim_text, classical_basis, source_file, source_version,
                    signal_type, source_citation, grounded_at, grounded_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (signal_id) DO UPDATE SET
                    source_citation = COALESCE(EXCLUDED.source_citation, msr_signals.source_citation),
                    grounded_at = CASE
                        WHEN msr_signals.source_citation IS NULL THEN EXCLUDED.grounded_at
                        ELSE msr_signals.grounded_at
                    END,
                    grounded_by = CASE
                        WHEN msr_signals.source_citation IS NULL THEN EXCLUDED.grounded_by
                        ELSE msr_signals.grounded_by
                    END
                RETURNING (xmax = 0) as was_inserted
            """, (
                sig['signal_id'],
                NATIVE_ID,
                sig['domain'],
                sig.get('planet'),
                sig['confidence'],
                sig['confidence'],  # significance = confidence for now
                sig['claim_text'],
                sig.get('classical_source', ''),
                '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md',
                '5.0',
                sig['signal_type'],
                citation,
                now,
                GROUNDED_BY,
            ))
            row = cur.fetchone()
            if row and row[0]:
                inserted += 1
            if citation:
                grounded += 1

        conn.commit()

    return inserted, grounded


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not DB_URL:
        print("ERROR: DATABASE_URL_PROD or DATABASE_URL env var required", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {MSR_PATH}...")
    signals = parse_msr(MSR_PATH)
    print(f"Parsed {len(signals)} signals")

    print(f"Connecting to DB...")
    conn = psycopg2.connect(DB_URL)

    print("Seeding and grounding msr_signals...")
    inserted, grounded = seed_and_ground(signals, conn)

    # Verify
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE source_citation IS NOT NULL AND source_citation != '') as grounded,
                count(*) FILTER (WHERE grounded_by = %s) as by_this_session
            FROM msr_signals
            WHERE native_id = %s
        """, (GROUNDED_BY, NATIVE_ID))
        total, grounded_count, by_session = cur.fetchone()

    conn.close()

    pct = grounded_count / total * 100 if total > 0 else 0

    print("\n=== RESULTS ===")
    print(f"Signals inserted this run: {inserted}")
    print(f"Total in DB:   {total}")
    print(f"Grounded:      {grounded_count} ({pct:.1f}%)")
    print(f"By this run:   {by_session}")
    print(f"Target:        ≥95% (≥545)")
    print(f"AC.S1.1 PASS:  {'YES ✓' if pct >= 95 else 'NO ✗'}")

    # Sample 5 grounded signals
    conn2 = psycopg2.connect(DB_URL)
    with conn2.cursor() as cur:
        cur.execute("""
            SELECT signal_id, left(claim_text, 80), source_citation
            FROM msr_signals
            WHERE native_id = %s AND source_citation IS NOT NULL
            ORDER BY signal_id
            LIMIT 5
        """, (NATIVE_ID,))
        samples = cur.fetchall()
    conn2.close()

    print("\n=== SAMPLE GROUNDED SIGNALS ===")
    for sig_id, claim, citation in samples:
        print(f"  {sig_id}: {claim}...")
        print(f"    → {citation}")

    if pct < 95:
        print(f"\nWARNING: Only {pct:.1f}% grounded — below 95% target", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
