"""
PARIŚEṢA-V4 F-183 — remedy loader robustness regressions.

Two independent gaps disclosed during the F-178/F-180 mantra-corpus wave
(PR #1436), both in ``brahmagyan.l0_remedy_loader``:

  gap 1  ``insert_to_corpus``'s ``ON CONFLICT (remedy_id) DO UPDATE SET`` list
         omitted the citation columns, so re-loading a corrected YAML row over
         an already-seeded ``remedy_id`` silently kept the OLD attribution —
         precisely the correction class #1429/#1436 have been making.

  gap 2  ``row.get('classical_attestation_text', '')[:500]`` raised TypeError
         when the YAML key was present but null, because ``.get`` returns the
         stored ``None`` rather than the default.

Gap 1 is exercised against real upsert semantics (sqlite's ``ON CONFLICT ... DO
UPDATE`` with ``excluded.``) rather than by string-matching the SQL, so the test
measures the behaviour it claims — a stale row after reload — not the presence
of a substring (CLAUDE.md §N.8).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from brahmagyan import l0_remedy_loader


# ── Gap 1: real-upsert harness ────────────────────────────────────────────────

# Mirrors the production DDL for the columns insert_to_corpus writes
# (platform/migrations/ws2_l0_remedy_corpus.sql + the L0FR column additions).
_CORPUS_DDL = """
CREATE TABLE brahma_remedy_corpus (
    remedy_id                  TEXT NOT NULL UNIQUE,
    planet                     TEXT NOT NULL,
    domain                     TEXT NOT NULL,
    remedy_type                TEXT NOT NULL,
    prescription_text          TEXT NOT NULL,
    mantra_text                TEXT,
    confidence                 NUMERIC NOT NULL DEFAULT 0.85,
    source_canonical_id        TEXT NOT NULL,
    source_citation            TEXT NOT NULL,
    classical_ref              TEXT,
    category                   TEXT,
    deity                      TEXT,
    mantra_sanskrit            TEXT,
    mantra_transliteration     TEXT,
    ingredients_jsonb          TEXT,
    timing_rules_jsonb         TEXT,
    cost_tier                  TEXT,
    contraindications          TEXT,
    classical_attestation_text TEXT
)
"""


class _SqliteCursor:
    """Runs the loader's psycopg SQL against sqlite (pyformat → named params)."""

    def __init__(self, cur: sqlite3.Cursor) -> None:
        self._cur = cur

    def __enter__(self) -> "_SqliteCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, sql: str, params: Any = None) -> None:
        sql = sql.replace('::jsonb', '')
        sql = re.sub(r'%\((\w+)\)s', r':\1', sql)
        self._cur.execute(sql, params or {})


class _SqliteConn:
    def __init__(self, raw: sqlite3.Connection) -> None:
        self._raw = raw

    def cursor(self) -> _SqliteCursor:
        return _SqliteCursor(self._raw.cursor())

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()


def _yaml_row(*, citation: str, chapter: str, verse: str,
              translit: str, category: str) -> dict[str, Any]:
    return {
        'remedy_id': 'f183_saturn_bija',
        'planet': 'Saturn',
        'domain': 'career',
        'category': category,
        'remedy_text': 'Recite the Saturn bīja mantra.',
        'source_text': 'BPHS',
        'source_chapter': chapter,
        'source_verse': verse,
        'classical_attestation_text': citation,
        'mantra_sanskrit': 'ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः',
        'mantra_transliteration': translit,
    }


@pytest.fixture()
def corpus_conn():
    raw = sqlite3.connect(':memory:')
    raw.execute(_CORPUS_DDL)
    raw.row_factory = sqlite3.Row
    yield _SqliteConn(raw)
    raw.close()


def _stored(conn: _SqliteConn) -> sqlite3.Row:
    cur = conn._raw.execute('SELECT * FROM brahma_remedy_corpus')
    rows = cur.fetchall()
    assert len(rows) == 1, f'expected exactly one row, got {len(rows)}'
    return rows[0]


class TestCitationColumnsUpsert:
    """F-183 gap 1 — a citation correction must APPLY on reseed."""

    def test_corrected_citation_applies_to_existing_row(self, corpus_conn):
        original = _yaml_row(
            citation='BPHS Ch.91-94 (Upaya-adhyaya) prescribes this bīja.',
            chapter='Ch. 91', verse='V. 12',
            translit='Om Praam Preem Praum Sah Shanaye Namah',
            category='mantra',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, original)

        # The R-2/R-1-class correction: reattributed source, corrected IAST.
        corrected = _yaml_row(
            citation='Navagraha bīja tradition (Mantra Mahodadhi, Mahīdhara, 16th c.).',
            chapter='Ch. 12', verse='V. 4',
            translit='oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ',
            category='mantra',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, corrected)

        row = _stored(corpus_conn)
        assert row['source_citation'] == (
            'Navagraha bīja tradition (Mantra Mahodadhi, Mahīdhara, 16th c.).'
        ), 'source_citation kept the superseded attribution after reseed'
        assert row['classical_ref'] == 'Ch. 12 V. 4', (
            'classical_ref kept the superseded chapter/verse after reseed'
        )
        assert row['mantra_transliteration'] == (
            'oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ'
        )

    def test_source_canonical_id_correction_applies(self, corpus_conn):
        row_v1 = _yaml_row(
            citation='attestation', chapter='Ch. 91', verse='V. 12',
            translit='om', category='mantra',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v1)

        row_v2 = dict(row_v1, source_text='Mantra Mahodadhi')
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v2)

        assert _stored(corpus_conn)['source_canonical_id'] == 'Mantra Mahodadhi', (
            'source_canonical_id kept the superseded source after reseed'
        )

    def test_mantra_text_and_remedy_type_track_their_source_field(self, corpus_conn):
        """Both are fed by a YAML field whose sibling column already updated."""
        row_v1 = _yaml_row(
            citation='attestation', chapter='Ch. 91', verse='V. 12',
            translit='Om Shanaye Namah', category='mantra',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v1)

        row_v2 = _yaml_row(
            citation='attestation', chapter='Ch. 91', verse='V. 12',
            translit='oṃ śanaiścarāya namaḥ', category='tantric',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v2)

        row = _stored(corpus_conn)
        assert row['mantra_text'] == row['mantra_transliteration'], (
            'mantra_text went stale while mantra_transliteration was corrected'
        )
        assert row['remedy_type'] == row['category'] == 'tantric', (
            'remedy_type went stale while category was corrected'
        )

    def test_previously_covered_columns_still_update(self, corpus_conn):
        """Guard against the fix narrowing what already worked."""
        row_v1 = _yaml_row(
            citation='attestation-v1', chapter='Ch. 91', verse='V. 12',
            translit='om', category='mantra',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v1)

        row_v2 = dict(
            row_v1,
            classical_attestation_text='attestation-v2',
            deity='Śani',
            remedy_text='Corrected prescription.',
        )
        l0_remedy_loader.insert_to_corpus(corpus_conn, row_v2)

        row = _stored(corpus_conn)
        assert row['classical_attestation_text'] == 'attestation-v2'
        assert row['deity'] == 'Śani'
        assert row['prescription_text'] == 'Corrected prescription.'


# ── Gap 2: null-safe truncation ───────────────────────────────────────────────

class _RecordingCursor:
    def __init__(self, sink: list[tuple[str, dict[str, Any]]]) -> None:
        self._sink = sink

    def __enter__(self) -> "_RecordingCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, sql: str, params: Any = None) -> None:
        self._sink.append((sql, dict(params or {})))


class _RecordingConn:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def cursor(self) -> _RecordingCursor:
        return _RecordingCursor(self.calls)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:  # pragma: no cover — only on failure paths
        pass

    def params_for(self, table: str) -> dict[str, Any]:
        for sql, params in self.calls:
            if table in sql:
                return params
        raise AssertionError(f'no statement touched {table}; calls={len(self.calls)}')


_NULL_ATTESTATION_YAML = """\
- remedy_id: f183-null-attestation
  planet: Saturn
  domain: career
  category: behavioral
  remedy_text: A remedy whose attestation field was left empty in YAML.
  source_text: BPHS
  classical_attestation_text:
"""

_NULL_ATTESTATION_TANTRIC_YAML = """\
- remedy_id: f183-null-attestation-tantric
  planet: Saturn
  domain: health
  category: tantric
  remedy_text: A tantric remedy whose attestation field was left empty in YAML.
  source_text: Mantra Mahodadhi
  source_chapter: Ch. 12
  source_verse: V. 4
  classical_attestation_text:
"""


class TestNullSafeTruncation:
    """F-183 gap 2 — a null YAML field must not crash the loader."""

    def test_null_field_parses_to_none_not_the_get_default(self):
        """The premise: the key IS present, so .get's default never fires."""
        import yaml

        row = yaml.safe_load(_NULL_ATTESTATION_YAML)[0]
        assert 'classical_attestation_text' in row
        assert row['classical_attestation_text'] is None

    def test_corpus_path_survives_null_attestation(self, tmp_path: Path):
        (tmp_path / 'nulls.yaml').write_text(_NULL_ATTESTATION_YAML, encoding='utf-8')
        conn = _RecordingConn()

        result = l0_remedy_loader.load_remedies(
            tmp_path, conn=conn, file_glob='nulls.yaml', manage_transaction=False,
        )

        assert result['errors'] == 0
        assert result['inserted'] == 1
        assert conn.params_for('brahma_remedy_corpus')['source_citation'] == ''

    def test_review_queue_path_survives_null_required_column(self, tmp_path: Path):
        """The gate routes null-column tantric rows here — it must not crash."""
        (tmp_path / 'tantric.yaml').write_text(
            _NULL_ATTESTATION_TANTRIC_YAML, encoding='utf-8',
        )
        conn = _RecordingConn()

        result = l0_remedy_loader.load_remedies(
            tmp_path, conn=conn, file_glob='tantric.yaml', manage_transaction=False,
        )

        assert result['review_queued'] == 1
        assert result['errors'] == 0
        params = conn.params_for('remedy_review_queue')
        assert params['source_citation'] == ''
        assert 'missing source columns' in params['rejection_reason']

    def test_long_attestation_is_still_truncated_to_500(self):
        assert l0_remedy_loader._citation_excerpt('x' * 900) == 'x' * 500

    def test_absent_key_and_null_value_agree(self):
        """NOT NULL on both target columns rules out the honest-null option."""
        assert l0_remedy_loader._citation_excerpt(None) == ''
        assert l0_remedy_loader._citation_excerpt('') == ''
