"""Deterministic rebuild coverage for the base and text-sweep remedy writers."""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from brahmagyan import l0_remedy_corpus


_CORPUS_DDL = """
CREATE TABLE brahma_remedy_corpus (
    remedy_id TEXT NOT NULL UNIQUE,
    planet TEXT, domain TEXT, remedy_type TEXT, prescription_text TEXT,
    mantra_text TEXT, gemstone TEXT, charity_action TEXT, day_of_week TEXT,
    color_associated TEXT, confidence NUMERIC, source_canonical_id TEXT,
    source_citation TEXT, classical_ref TEXT, category TEXT, deity TEXT,
    mantra_sanskrit TEXT, mantra_transliteration TEXT,
    ingredients_jsonb TEXT, timing_rules_jsonb TEXT, cost_tier TEXT,
    contraindications TEXT, classical_attestation_text TEXT,
    scaffold_status TEXT
)
"""


class _SqliteCursor:
    def __init__(self, raw: sqlite3.Connection) -> None:
        self._raw = raw
        self._cur = raw.cursor()
        self._synthetic_row: dict[str, int] | None = None

    def __enter__(self) -> "_SqliteCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount

    def execute(self, sql: str, params: Any = None) -> None:
        if "information_schema.tables" in sql:
            self._synthetic_row = {"count": 1}
            return
        if "WHERE NOT (remedy_id = ANY(%s))" in sql:
            remedy_ids = tuple(params[0])
            placeholders = ",".join("?" for _ in remedy_ids)
            self._cur.execute(
                f"DELETE FROM brahma_remedy_corpus WHERE remedy_id NOT IN ({placeholders})",
                remedy_ids,
            )
            self._synthetic_row = None
            return
        self._synthetic_row = None
        translated = re.sub(r"%\((\w+)\)s", r":\1", sql.replace("::jsonb", ""))
        self._cur.execute(translated, params or {})

    def fetchone(self) -> dict[str, int]:
        if self._synthetic_row is not None:
            return self._synthetic_row
        row = self._cur.fetchone()
        assert row is not None
        return {"count": row[0]}


class _SqliteConn:
    def __init__(self) -> None:
        self.raw = sqlite3.connect(":memory:")
        self.raw.execute(_CORPUS_DDL)

    def cursor(self) -> _SqliteCursor:
        return _SqliteCursor(self.raw)

    def commit(self) -> None:
        self.raw.commit()


def _base_row() -> dict[str, Any]:
    return {
        "remedy_id": "sun_matrix_mantra",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "prescription_text": "Canonical base prescription",
        "mantra_text": "Om Suryaya Namah",
        "gemstone": None,
        "charity_action": None,
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.9,
        "source_canonical_id": "BPHS",
        "source_citation": "BPHS Ch.88",
        "classical_ref": "BPHS Ch.88",
        "category": None,
        "deity": "Surya",
        "mantra_sanskrit": "ॐ सूर्याय नमः",
        "mantra_transliteration": "oṃ sūryāya namaḥ",
        "ingredients_jsonb": None,
        "timing_rules_jsonb": None,
        "cost_tier": "low",
        "contraindications": "None",
        "classical_attestation_text": None,
        "scaffold_status": "live",
    }


def _sweep_row() -> dict[str, Any]:
    return {
        "remedy_id": "sweep_fixture_001",
        "planet": "moon",
        "domain": "health",
        "remedy_type": "ayurvedic",
        "prescription_text": "Canonical sweep prescription",
        "mantra_text": None,
        "gemstone": None,
        "charity_action": None,
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.71,
        "source_canonical_id": "text_fixture",
        "source_citation": "Text fixture Ch.1",
        "classical_ref": "Text fixture Ch.1",
        "category": "corpus_sweep",
        "deity": None,
        "mantra_sanskrit": None,
        "mantra_transliteration": None,
        "ingredients_jsonb": {"herb": "canonical"},
        "timing_rules_jsonb": {"day": "Monday"},
        "cost_tier": "low",
        "contraindications": "Avoid excess",
        "classical_attestation_text": None,
        "scaffold_status": "review",
    }


def test_reseed_converges_every_writer_owned_output_field(monkeypatch) -> None:
    conn = _SqliteConn()
    monkeypatch.setattr(l0_remedy_corpus, "build_all_remedies", lambda: [_base_row()])
    monkeypatch.setattr(
        l0_remedy_corpus,
        "sweep_classical_text_chunks",
        lambda _conn: [_sweep_row()],
    )

    l0_remedy_corpus.seed_remedy_corpus(conn, autocommit=False)
    conn.raw.execute(
        """
        INSERT INTO brahma_remedy_corpus (
          remedy_id, planet, domain, remedy_type, prescription_text,
          source_canonical_id, source_citation, scaffold_status
        ) VALUES (
          'obsolete_remedy', 'mars', 'general', 'puja', 'stale',
          'stale', 'stale', 'live'
        )
        """
    )
    conn.raw.execute(
        """
        UPDATE brahma_remedy_corpus SET
          planet='bogus', domain='bogus', remedy_type='bogus',
          prescription_text='stale', mantra_text='stale', gemstone='stale',
          charity_action='stale', day_of_week='stale', color_associated='stale',
          confidence=0.01, source_canonical_id='stale', source_citation='stale',
          classical_ref='stale', category='stale', deity='stale',
          mantra_sanskrit='stale', mantra_transliteration='stale',
          ingredients_jsonb='{"stale":true}', timing_rules_jsonb='{"stale":true}',
          cost_tier='stale', contraindications='stale',
          classical_attestation_text='stale', scaffold_status='rejected'
        """
    )

    l0_remedy_corpus.seed_remedy_corpus(conn, autocommit=False)

    columns = [row[1] for row in conn.raw.execute("PRAGMA table_info(brahma_remedy_corpus)")]
    stored = {
        row[0]: dict(zip(columns, row))
        for row in conn.raw.execute(
            "SELECT * FROM brahma_remedy_corpus ORDER BY remedy_id"
        )
    }
    expected = {row["remedy_id"]: row for row in (_base_row(), _sweep_row())}
    assert stored.keys() == expected.keys()
    for remedy_id, canonical in expected.items():
        for column, value in canonical.items():
            if column in {"ingredients_jsonb", "timing_rules_jsonb"} and value is not None:
                assert stored[remedy_id][column] == l0_remedy_corpus.json.dumps(value)
            else:
                assert stored[remedy_id][column] == value
