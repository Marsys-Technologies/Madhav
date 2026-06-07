"""
brahmagyan.l0_remedy_yaml_scaffolder — Stream F Phase 2
========================================================

Scaffolds YAML stubs from classical_text_chunks by finding passages
containing remedy-related keywords (BPHS Ch. 91-94, Phaladeepika Ch. 27).

Output: prints YAML stubs to stdout or writes to a file.
These stubs have source fields auto-filled; remedy_text and category
are left blank for native authoring.

ZERO LLM — pure regex + SQL extraction.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

import psycopg2  # type: ignore[import]
import yaml  # type: ignore[import]

logger = logging.getLogger(__name__)

# ── Remedy keyword patterns ────────────────────────────────────────────────────

REMEDY_TRIGGERS = [
    r'remed(y|ies)',
    r'upay[a]',
    r'mantra',
    r'yantra',
    r'd[āa]na',
    r'charity',
    r'vrata',
    r'fasting',
    r'gemstone',
    r'\bgem\b',
    r'puja',
    r'worship',
    r'yagna',
    r'homa',
    r'shaanti',
    r'sh[aā]nti',
    r'propitiat',
    r'pacif',
]

# Classical chapters known to contain remedies
REMEDY_CHAPTERS = [
    # BPHS
    ('BPHS', 'Ch. 88'),
    ('BPHS', 'Ch. 91'),
    ('BPHS', 'Ch. 92'),
    ('BPHS', 'Ch. 93'),
    ('BPHS', 'Ch. 94'),
    # Phaladeepika
    ('Phaladeepika', 'Ch. 27'),
    ('Phaladeepika', 'Ch. 28'),
]

PLANET_KEYWORDS = {
    'Sun': ['sun', 'surya', 'ravi', 'aditya', 'solar'],
    'Moon': ['moon', 'chandra', 'soma', 'lunar'],
    'Mars': ['mars', 'kuja', 'mangala', 'bhumi'],
    'Mercury': ['mercury', 'budha', 'budh'],
    'Jupiter': ['jupiter', 'guru', 'brihaspati'],
    'Venus': ['venus', 'shukra', 'sukra'],
    'Saturn': ['saturn', 'shani', 'shanaischara'],
    'Rahu': ['rahu', 'dragon.*head', 'ascending node'],
    'Ketu': ['ketu', 'dragon.*tail', 'descending node'],
}


def _get_conn():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        raise RuntimeError('DATABASE_URL not set')
    return psycopg2.connect(url)


def _detect_planet(text: str) -> str:
    """Detect the primary planet mentioned in a text snippet."""
    text_lower = text.lower()
    for planet, keywords in PLANET_KEYWORDS.items():
        for kw in keywords:
            if re.search(kw, text_lower):
                return planet
    return ''


def _make_remedy_id(source_text: str, source_chapter: str, source_verse: str, index: int) -> str:
    """Create a deterministic remedy_id from source fields."""
    raw = f'{source_text}_{source_chapter}_{source_verse}_{index}'
    return 'scaffold_' + hashlib.md5(raw.encode()).hexdigest()[:12]


def scaffold_from_classical_chunks(
    conn=None,
    output_path: str | None = None,
    max_stubs: int = 50,
) -> list[dict[str, Any]]:
    """
    Scan classical_text_chunks for remedy-related passages.
    Returns list of YAML stub dicts; also writes YAML if output_path given.

    Each stub has:
    - source_text, source_chapter, source_verse, classical_attestation_text: auto-filled
    - planet: auto-detected from content
    - remedy_text, category, domain: blank (for native to fill)
    """
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    pattern = '|'.join(REMEDY_TRIGGERS)
    remedy_regex = re.compile(pattern, re.IGNORECASE)

    stubs: list[dict[str, Any]] = []

    try:
        with conn.cursor() as cur:
            # Try to query classical_text_chunks
            try:
                cur.execute("""
                    SELECT chunk_id, source_canonical_id, chapter_ref, verse_ref,
                           content, metadata
                    FROM classical_text_chunks
                    WHERE source_canonical_id IN ('BPHS', 'Phaladeepika', 'Tajaka',
                                                   'Saravali', 'Jataka_Parijata')
                    ORDER BY source_canonical_id, chapter_ref, verse_ref
                    LIMIT 2000
                """)
                rows = cur.fetchall()
            except Exception as exc:
                logger.warning('[scaffolder] classical_text_chunks unavailable: %s', exc)
                conn.rollback()
                return []

        for i, (chunk_id, source_text, chapter_ref, verse_ref, content, metadata) in enumerate(rows):
            if not content:
                continue
            if not remedy_regex.search(content):
                continue

            planet = _detect_planet(content)
            stub_id = _make_remedy_id(
                source_text or '',
                chapter_ref or '',
                verse_ref or '',
                i,
            )

            stub: dict[str, Any] = {
                'remedy_id': stub_id,
                'planet': planet,  # auto-detected; native should verify
                'domain': '',      # BLANK — native to fill
                'category': '',    # BLANK — native to fill
                'deity': '',       # BLANK — native to fill
                'remedy_text': '',  # BLANK — native to fill
                'mantra_sanskrit': '',
                'mantra_transliteration': '',
                'ingredients_jsonb': {},
                'timing_rules_jsonb': {},
                'cost_tier': 'accessible',
                'contraindications': '',
                'source_text': source_text or '',
                'source_chapter': chapter_ref or '',
                'source_verse': verse_ref or '',
                'classical_attestation_text': content[:500] if content else '',
            }
            stubs.append(stub)

            if len(stubs) >= max_stubs:
                break

    finally:
        if close_conn:
            conn.close()

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(stubs, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        logger.info('[scaffolder] wrote %d stubs to %s', len(stubs), output_path)

    return stubs
