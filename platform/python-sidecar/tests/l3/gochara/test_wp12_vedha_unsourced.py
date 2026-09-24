"""§12.10b — the vedha writer must not stamp UNSOURCED rules as cited.

Why this file exists. The L0 repair (PR #2727) left `bg_transit_rules` with 36
favourable-with-vedha rows cited to `Phaladipika Adh. XXVI, Sloka …` and 6
Rāhu/Ketu rows whose `classical_citation` begins `UNSOURCED` (the served corpus
carries no house-transit vedha doctrine for the nodes). `ka_vedha_gochara`'s
row selection is `rule_type='favourable' AND vedha_house IS NOT NULL`, which
includes those six, and the writer used to stamp EVERY house_vedha row
`uncited_extension=False`, `source_qualification='verse_cited'` — a
favourable-sounding default standing in for a known negative (CLAUDE.md §N.7
item 6). The pre-existing WP9 fixture never caught it because it seeds
pre-repair citation shapes, so no test row looked like production.

Discriminators are the L0 session's own falsifier predicates (migration 1079):
  `classical_citation LIKE 'UNSOURCED%'`                       -> 6 rows
  `classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%'`    -> 36 rows

Runs against the disposable WP6 Postgres only; skips NOT_RUN when unreachable.
"""
from __future__ import annotations

from types import SimpleNamespace

import psycopg
import pytest

from .test_wp9_stamp_columns import (
    BASE_DDL,
    CHART_ID,
    MIGRATION_1082,
    WP6_DSN,
    _seed,
    _wp6_reachable,
)

VERSE_CITED = "Phaladipika Adh. XXVI, Sloka 3 (PG322:C1)"
UNSOURCED = (
    "UNSOURCED — the served corpus carries no house-transit vedha doctrine for "
    "the nodes; the refuted 'BPHS Ch.29' citation was struck (ruling N-14)"
)


@pytest.fixture(scope="module")
def built():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.close()

    seed = psycopg.connect(WP6_DSN)
    _seed(seed)
    # Reshape the two seeded rules into POST-REPAIR production form.
    seed.execute(
        "UPDATE bg_transit_rules SET classical_citation = %s WHERE graha = 'sun'",
        (VERSE_CITED,),
    )
    seed.execute(
        "UPDATE bg_transit_rules SET classical_citation = %s WHERE graha = 'rahu'",
        (UNSOURCED,),
    )
    seed.commit()
    seed.close()

    import services.ka_vedha_gochara.writer as vedha_writer

    conn = psycopg.connect(WP6_DSN)
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID}, dry_run=False)
    orig = vedha_writer._compute_ayanamsha_offset
    vedha_writer._compute_ayanamsha_offset = lambda _d: 0.0
    try:
        vedha_writer.KaVedhaGocharaWriter().run(ctx)
        conn.commit()
    finally:
        vedha_writer._compute_ayanamsha_offset = orig
        conn.close()
    return True


def _rows(where: str):
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        return c.execute(
            "SELECT graha, classical_citation, uncited_extension, "
            "source_qualification, corpus_verifiable, precision_regime "
            "FROM kala_vedha_gochara WHERE vedha_kind = 'house_vedha' AND " + where
        ).fetchall()


def test_fixture_actually_contains_both_shapes(built):
    """Guard against a vacuous pass: both citation shapes must reach the output."""
    assert _rows("classical_citation LIKE 'UNSOURCED%'"), (
        "no UNSOURCED house_vedha output rows — the test below would pass vacuously"
    )
    assert _rows("classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%'"), (
        "no verse-cited house_vedha output rows — the control below would be vacuous"
    )


def test_unsourced_rules_are_not_stamped_as_cited(built):
    rows = _rows("classical_citation LIKE 'UNSOURCED%'")
    assert rows
    for graha, _cit, uncited, source_q, corpus_ok, _pr in rows:
        assert uncited is True, (
            f"{graha}: UNSOURCED rule stamped uncited_extension={uncited!r} "
            "(§N.7 item 6: a favourable default standing in for a known negative)"
        )
        assert source_q == "unsourced", (
            f"{graha}: UNSOURCED rule stamped source_qualification={source_q!r}"
        )
        assert corpus_ok is False, (
            f"{graha}: UNSOURCED rule stamped corpus_verifiable={corpus_ok!r}"
        )


def test_verse_cited_rules_stay_cited(built):
    """Negative control: the honest path must not be collateral damage."""
    rows = _rows("classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%'")
    assert rows
    for graha, _cit, uncited, source_q, corpus_ok, _pr in rows:
        assert uncited is False, f"{graha}: verse-cited rule marked uncited"
        assert source_q == "verse_cited", f"{graha}: got {source_q!r}"
        assert corpus_ok is True, f"{graha}: got corpus_verifiable={corpus_ok!r}"
