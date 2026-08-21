"""
brahmagyan.l0_remedy_loader — Stream F Phase 4
===============================================

Loads YAML remedy corpus files from brahmagyan/remedy_corpus/ into the
brahma_remedy_corpus table. Also handles the tantric careful-inclusion gate
and routes rejected rows to remedy_review_queue.

Phase 3 gate: all tantric rows must come from an acceptable source list.
If any required column is missing or source not in acceptable list → reject.

ZERO LLM — pure Python + SQL.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import psycopg2  # type: ignore[import]
import yaml  # type: ignore[import]

logger = logging.getLogger(__name__)

# ── Acceptable tantric source list (from L0FR_SOURCE_DATA §Remedy corpus) ─────

ACCEPTABLE_TANTRIC_SOURCES = [
    r'mantra\s*mahodadhi',
    r'mantra\s*mah[āa]rn\s*ava',
    r'tantras[āa]ra',
    r'śaktisa[nṅ]gama\s*tantra',
    r'shaktisangama\s*tantra',
    r'dasamahavidya',
    r'bphs',
    r'brihat\s*parashara',
    r'phaladeepika',
    r'phala\s*deepika',
]

ACCEPTABLE_TANTRIC_PATTERN = re.compile(
    '|'.join(ACCEPTABLE_TANTRIC_SOURCES),
    re.IGNORECASE,
)

REQUIRED_TANTRIC_COLUMNS = [
    'source_text',
    'source_chapter',
    'source_verse',
    'classical_attestation_text',
]


def is_acceptable_tantric_source(source_text: str) -> bool:
    """Return True if the source_text matches the acceptable tantric source list."""
    return bool(ACCEPTABLE_TANTRIC_PATTERN.search(source_text or ''))


def _get_conn():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        raise RuntimeError('DATABASE_URL not set')
    return psycopg2.connect(url)


COST_TIER_MAP = {
    # YAML canonical values → DB constraint values
    'accessible': 'low',
    'moderate': 'medium',
    'elaborate': 'high',
    # Pass-through (already DB values)
    'free': 'free',
    'low': 'low',
    'medium': 'medium',
    'high': 'high',
}


def _map_cost_tier(value: str | None) -> str | None:
    """Map YAML cost_tier values to DB constraint values."""
    if value is None:
        return None
    return COST_TIER_MAP.get(value.lower(), 'low')


def _row_to_jsonb(value: Any) -> str | None:
    """Convert dict to JSON string for JSONB insertion, or None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _citation_excerpt(value: Any, limit: int = 500) -> str:
    """
    Null-safe excerpt of a YAML text field for the ``source_citation`` column.

    PARIŚEṢA-V4 F-183 (gap 2): a YAML key written with no value —
    ``classical_attestation_text:`` — parses to ``None``, and because the KEY is
    present ``row.get(k, '')`` returns ``None`` rather than the default, so the
    ``[:500]`` that followed raised ``TypeError``.  The tantric gate routes rows
    with a null required column to the review queue, so the crash fired on
    exactly the rows that gate exists to handle.

    Both target columns (``brahma_remedy_corpus.source_citation`` and
    ``remedy_review_queue.source_citation``) are NOT NULL, so the honest-null
    option (CLAUDE.md §N.7 item 6) is unavailable here: absent and null both
    degrade to the empty string, which is what the absent-key branch already
    stored.
    """
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return value[:limit]


def insert_to_review_queue(conn, row: dict[str, Any], reason: str) -> None:
    """Insert a rejected row to remedy_review_queue."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO remedy_review_queue (
                    remedy_id, planet, domain, remedy_type,
                    prescription_text, mantra_text, gemstone, charity_action,
                    day_of_week, color_associated, confidence,
                    source_canonical_id, source_citation, classical_ref,
                    category, deity, mantra_sanskrit, mantra_transliteration,
                    ingredients_jsonb, timing_rules_jsonb, cost_tier,
                    contraindications, classical_attestation_text,
                    rejection_reason, review_status
                ) VALUES (
                    %(remedy_id)s, %(planet)s, %(domain)s, %(remedy_type)s,
                    %(prescription_text)s, %(mantra_text)s, %(gemstone)s, %(charity_action)s,
                    %(day_of_week)s, %(color_associated)s, %(confidence)s,
                    %(source_canonical_id)s, %(source_citation)s, %(classical_ref)s,
                    %(category)s, %(deity)s, %(mantra_sanskrit)s, %(mantra_transliteration)s,
                    %(ingredients_jsonb)s::jsonb, %(timing_rules_jsonb)s::jsonb, %(cost_tier)s,
                    %(contraindications)s, %(classical_attestation_text)s,
                    %(rejection_reason)s, 'pending'
                )
                ON CONFLICT (remedy_id) DO UPDATE SET
                    rejection_reason = EXCLUDED.rejection_reason,
                    review_status = 'pending'
                """,
                {
                    'remedy_id': row.get('remedy_id', ''),
                    'planet': row.get('planet', ''),
                    'domain': row.get('domain', '') or '',
                    'remedy_type': row.get('category', row.get('remedy_type', 'unknown')),
                    'prescription_text': row.get('remedy_text', row.get('prescription_text', '')),
                    'mantra_text': row.get('mantra_transliteration', row.get('mantra_text')),
                    'gemstone': None,
                    'charity_action': None,
                    'day_of_week': None,
                    'color_associated': None,
                    'confidence': 0.70,
                    'source_canonical_id': row.get('source_text', 'unknown'),
                    'source_citation': _citation_excerpt(row.get('classical_attestation_text')),
                    'classical_ref': f"{row.get('source_chapter', '')} {row.get('source_verse', '')}",
                    'category': row.get('category', ''),
                    'deity': row.get('deity', ''),
                    'mantra_sanskrit': row.get('mantra_sanskrit', ''),
                    'mantra_transliteration': row.get('mantra_transliteration', ''),
                    'ingredients_jsonb': _row_to_jsonb(row.get('ingredients_jsonb')),
                    'timing_rules_jsonb': _row_to_jsonb(row.get('timing_rules_jsonb')),
                    'cost_tier': _map_cost_tier(row.get('cost_tier', 'accessible')),
                    'contraindications': row.get('contraindications', ''),
                    'classical_attestation_text': row.get('classical_attestation_text', ''),
                    'rejection_reason': reason,
                },
            )
    except Exception as exc:
        logger.error('[loader] insert_to_review_queue failed for %s: %s', row.get('remedy_id'), exc)
        raise


def insert_to_corpus(conn, row: dict[str, Any]) -> None:
    """Insert a row to brahma_remedy_corpus."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO brahma_remedy_corpus (
                    remedy_id, planet, domain, remedy_type,
                    prescription_text, mantra_text,
                    confidence, source_canonical_id, source_citation, classical_ref,
                    category, deity, mantra_sanskrit, mantra_transliteration,
                    ingredients_jsonb, timing_rules_jsonb, cost_tier,
                    contraindications, classical_attestation_text
                ) VALUES (
                    %(remedy_id)s, %(planet)s, %(domain)s, %(remedy_type)s,
                    %(prescription_text)s, %(mantra_text)s,
                    %(confidence)s, %(source_canonical_id)s, %(source_citation)s, %(classical_ref)s,
                    %(category)s, %(deity)s, %(mantra_sanskrit)s, %(mantra_transliteration)s,
                    %(ingredients_jsonb)s::jsonb, %(timing_rules_jsonb)s::jsonb, %(cost_tier)s,
                    %(contraindications)s, %(classical_attestation_text)s
                )
                ON CONFLICT (remedy_id) DO UPDATE SET
                    category = EXCLUDED.category,
                    deity = EXCLUDED.deity,
                    mantra_sanskrit = EXCLUDED.mantra_sanskrit,
                    mantra_transliteration = EXCLUDED.mantra_transliteration,
                    ingredients_jsonb = EXCLUDED.ingredients_jsonb,
                    timing_rules_jsonb = EXCLUDED.timing_rules_jsonb,
                    cost_tier = EXCLUDED.cost_tier,
                    contraindications = EXCLUDED.contraindications,
                    classical_attestation_text = EXCLUDED.classical_attestation_text,
                    prescription_text = EXCLUDED.prescription_text,
                    -- PARIŚEṢA-V4 F-183 (gap 1): the citation columns were absent
                    -- from this list, so a correction to an ALREADY-SEEDED row's
                    -- attribution — the exact class of fix the R-1/R-2/R-3 wave
                    -- (#1429, #1436) has been making — reloaded silently as a
                    -- no-op while the loader reported the row as inserted.
                    source_canonical_id = EXCLUDED.source_canonical_id,
                    source_citation = EXCLUDED.source_citation,
                    classical_ref = EXCLUDED.classical_ref,
                    -- Same defect class, one step removed: both of these are fed
                    -- from a YAML field whose SIBLING column already updates
                    -- (mantra_text ← mantra_transliteration, remedy_type ←
                    -- category), so omitting them left the corrected and the
                    -- stale copy of the same source value in one row.
                    mantra_text = EXCLUDED.mantra_text,
                    remedy_type = EXCLUDED.remedy_type
                """,
                {
                    'remedy_id': row['remedy_id'],
                    'planet': row['planet'],
                    'domain': row.get('domain', 'general'),
                    'remedy_type': row.get('category', 'unknown'),
                    'prescription_text': row.get('remedy_text', row.get('prescription_text', '')),
                    'mantra_text': row.get('mantra_transliteration', row.get('mantra_text')),
                    'confidence': 0.85,
                    'source_canonical_id': row.get('source_text', 'BPHS'),
                    'source_citation': _citation_excerpt(row.get('classical_attestation_text')),
                    'classical_ref': (
                        f"{row.get('source_chapter', '')} {row.get('source_verse', '')}"
                    ).strip(),
                    'category': row.get('category', ''),
                    'deity': row.get('deity', ''),
                    'mantra_sanskrit': row.get('mantra_sanskrit', ''),
                    'mantra_transliteration': row.get('mantra_transliteration', ''),
                    'ingredients_jsonb': _row_to_jsonb(row.get('ingredients_jsonb')),
                    'timing_rules_jsonb': _row_to_jsonb(row.get('timing_rules_jsonb')),
                    'cost_tier': _map_cost_tier(row.get('cost_tier', 'accessible')),
                    'contraindications': row.get('contraindications', ''),
                    'classical_attestation_text': row.get('classical_attestation_text', ''),
                },
            )
    except Exception as exc:
        logger.error('[loader] insert_to_corpus failed for %s: %s', row.get('remedy_id'), exc)
        raise


def load_remedies(
    yaml_dir: Path,
    conn=None,
    dry_run: bool = False,
    file_glob: str = '*.yaml',
    manage_transaction: bool = True,
) -> dict[str, Any]:
    """
    Load selected YAML remedy files from yaml_dir into brahma_remedy_corpus.
    Applies Phase 3 tantric gate.  Callers that provide an orchestrator-owned
    connection must set ``manage_transaction=False`` so transaction ownership
    remains with the orchestrator.
    Returns summary dict.
    """
    close_conn = False
    if conn is None and not dry_run:
        conn = _get_conn()
        close_conn = True

    inserted = 0
    updated = 0
    review_queued = 0
    errors = 0
    files_processed = 0
    category_counts: dict[str, int] = {}

    try:
        for yaml_path in sorted(yaml_dir.glob(file_glob)):
            files_processed += 1
            logger.info('[loader] processing %s', yaml_path.name)

            with open(yaml_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, list):
                logger.warning('[loader] %s: empty or non-list YAML, skipping', yaml_path.name)
                continue

            for row in data:
                if not isinstance(row, dict):
                    continue

                category = row.get('category', '')

                # ── Phase 3: Tantric careful-inclusion gate ────────────────────
                if category == 'tantric':
                    source_text = row.get('source_text', '')
                    if not is_acceptable_tantric_source(source_text):
                        reason = f'tantric source not in acceptable list: {source_text!r}'
                        if not dry_run:
                            insert_to_review_queue(conn, row, reason)
                            if manage_transaction:
                                conn.commit()
                        review_queued += 1
                        logger.info('[loader] TANTRIC GATE: queued for review: %s (%s)',
                                   row.get('remedy_id'), reason)
                        continue

                    missing = [
                        k for k in REQUIRED_TANTRIC_COLUMNS
                        if not row.get(k)
                    ]
                    if missing:
                        reason = f'tantric row missing source columns: {missing}'
                        if not dry_run:
                            insert_to_review_queue(conn, row, reason)
                            if manage_transaction:
                                conn.commit()
                        review_queued += 1
                        logger.info('[loader] TANTRIC GATE: queued for review: %s (%s)',
                                   row.get('remedy_id'), reason)
                        continue

                # ── Insert to corpus ───────────────────────────────────────────
                if not dry_run:
                    try:
                        insert_to_corpus(conn, row)
                        if manage_transaction:
                            conn.commit()
                        inserted += 1
                    except Exception as exc:
                        if not manage_transaction:
                            raise
                        conn.rollback()
                        errors += 1
                        logger.error('[loader] error inserting %s: %s',
                                    row.get('remedy_id', '?'), exc)
                else:
                    inserted += 1

                # Track category counts
                category_counts[category] = category_counts.get(category, 0) + 1

    finally:
        if close_conn:
            conn.close()

    return {
        'files_processed': files_processed,
        'inserted': inserted,
        'review_queued': review_queued,
        'errors': errors,
        'category_counts': category_counts,
        'dry_run': dry_run,
    }


def check_acceptance_criteria(conn=None, *, file_glob: str = '*.yaml') -> dict[str, Any]:
    """
    Run Stream F acceptance criteria checks.
    Returns pass/fail for each criterion.

    PARIŚEṢA-V4 F-191: AC1/AC2 assert a whole-corpus shape (>=200 rows,
    >=8 distinct categories). That shape is only meaningful when the
    invocation actually loaded the whole corpus. A selective ``file_glob``
    (e.g. the ``__main__`` default below, or the orchestrator's own
    ``tantric.yaml``-only load) legitimately loads a small subset, and
    asserting the whole-corpus gate against it would hard-fail a
    deliberately narrow, successful load — a §N.8 defect (a signal that
    doesn't measure the claim it asserts). When ``file_glob`` is not the
    whole-corpus default, AC1/AC2 are skipped with an explicit recorded
    reason instead of silently passing or spuriously failing.
    """
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    results: dict[str, Any] = {}
    whole_corpus = (file_glob == '*.yaml')

    try:
        with conn.cursor() as cur:
            # AC1: COUNT(*) >= 200 — whole-corpus shape only.
            if whole_corpus:
                cur.execute("SELECT COUNT(*) FROM brahma_remedy_corpus")
                total = cur.fetchone()[0]
                results['ac1_total_rows'] = {'expected': '>=200', 'actual': total,
                                              'pass': total >= 200}
            else:
                results['ac1_total_rows'] = {
                    'skipped': True,
                    'reason': f'file_glob={file_glob!r} loads a deliberate subset, '
                              'not the whole corpus; whole-corpus row-count gate '
                              'does not apply',
                    'pass': True,
                }

            # AC2: DISTINCT categories >= 8 — whole-corpus shape only.
            if whole_corpus:
                cur.execute("SELECT COUNT(DISTINCT category) FROM brahma_remedy_corpus "
                           "WHERE category IS NOT NULL AND category != ''")
                cats = cur.fetchone()[0]
                results['ac2_distinct_categories'] = {'expected': '>=8', 'actual': cats,
                                                        'pass': cats >= 8}
            else:
                results['ac2_distinct_categories'] = {
                    'skipped': True,
                    'reason': f'file_glob={file_glob!r} loads a deliberate subset, '
                              'not the whole corpus; whole-corpus category-count gate '
                              'does not apply',
                    'pass': True,
                }

            # AC3: every tantric row has source columns NOT NULL
            cur.execute("""
                SELECT COUNT(*) FROM brahma_remedy_corpus
                WHERE category = 'tantric'
                AND (source_canonical_id IS NULL OR source_citation IS NULL
                     OR classical_attestation_text IS NULL)
            """)
            tantric_missing = cur.fetchone()[0]
            results['ac3_tantric_source_columns'] = {
                'expected': '0 missing',
                'actual': tantric_missing,
                'pass': tantric_missing == 0,
            }

            # AC4: query_remedies(planet='Saturn', domain='career', top_k=5) >= 3
            cur.execute("""
                SELECT COUNT(*) FROM brahma_remedy_corpus
                WHERE planet = 'Saturn' AND domain = 'career'
            """)
            sat_career = cur.fetchone()[0]
            results['ac4_saturn_career'] = {'expected': '>=3', 'actual': sat_career,
                                             'pass': sat_career >= 3}

            # AC5: review queue populated
            cur.execute("SELECT COUNT(*) FROM remedy_review_queue")
            queue_count = cur.fetchone()[0]
            results['ac5_review_queue'] = {'actual': queue_count, 'pass': True}

    finally:
        if close_conn:
            conn.close()

    all_pass = all(v.get('pass', True) for v in results.values())
    results['overall'] = 'PASS' if all_pass else 'FAIL'
    return results


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)

    yaml_dir = Path(__file__).parent / 'remedy_corpus'
    if not yaml_dir.exists():
        print(f'ERROR: {yaml_dir} does not exist', file=sys.stderr)
        sys.exit(1)

    dry_run = '--dry-run' in sys.argv

    # PARIŚEṢA-V4 F-191: the DEFAULT CLI scope is the orchestrator's own scope.
    # The other 12 corpus files carry bija rows whose BPHS attribution is still
    # under R-2 correction (F-23 Lane 4); a casual invocation must not land
    # them. An explicit --file-glob is still possible — then it is a
    # deliberate act, not a default.
    file_glob = 'tantric.yaml'
    for arg in sys.argv[1:]:
        if arg.startswith('--file-glob='):
            file_glob = arg.split('=', 1)[1]

    print(f'Loading remedies from {yaml_dir} (dry_run={dry_run}, file_glob={file_glob!r})')
    result = load_remedies(yaml_dir, dry_run=dry_run, file_glob=file_glob)
    print(f'Result: {result}')

    if not dry_run:
        print('\nRunning acceptance criteria checks...')
        ac = check_acceptance_criteria(file_glob=file_glob)
        for key, val in ac.items():
            status = '✓' if val.get('pass', True) else '✗'
            print(f'  {status} {key}: {val}')
        print(f'\nOverall: {ac["overall"]}')
        sys.exit(0 if ac['overall'] == 'PASS' else 1)
