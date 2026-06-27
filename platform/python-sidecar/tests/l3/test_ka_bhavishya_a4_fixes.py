"""
A4 remediation tests for ka_bhavishya_lekha (B4-consume) and mi_bhavisya (O2).

B4-consume: bhavishya domain is read from kc.domain (convergence column added by A3
            migration 361) and keyword inference is only the fallback when domain IS NULL.

O2:         mi_bhavisya driving_signals are matched to each prediction's domain instead
            of always returning the same first-5 signals across all predictions.

CONTRACT-2 note: these tests MOCK the kc.domain column — they do not require A3's
migration to have run. The production writer gracefully falls back if the column is
absent (pre-migration DB), but these tests validate the happy path where the column
is present and populated.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers — lightweight mock DB cursor / connection
# ---------------------------------------------------------------------------

def _make_cursor(rows=None, *, row_factory=None):
    """Return a mock cursor whose fetchall() yields `rows`."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall = MagicMock(return_value=rows or [])
    cur.fetchone = MagicMock(return_value=None)
    return cur


def _make_conn(*cursor_sequence):
    """
    Return a mock connection that yields cursors from `cursor_sequence` in order
    (one per context-manager __enter__ call). Excess calls reuse the last cursor.
    """
    seq = list(cursor_sequence)

    def _cursor(**kwargs):
        c = seq.pop(0) if seq else MagicMock()
        c.__enter__ = lambda s: s
        c.__exit__ = MagicMock(return_value=False)
        return c

    conn = MagicMock()
    conn.cursor = MagicMock(side_effect=_cursor)
    conn.rollback = MagicMock()
    return conn


# ---------------------------------------------------------------------------
# B4-consume — ka_bhavishya_lekha inherits domain from convergence column
# ---------------------------------------------------------------------------

class TestB4ConsumeKaBhavishya:
    """
    B4-consume: bhavishya row domain comes from kc.domain (convergence column),
    not from keyword inference against signal_type_id.
    """

    def _make_darshana_row(self, domain_col_value):
        """
        Simulate a row from the JOIN query that includes kc.domain.
        signal_type_id is intentionally a machine code ('L3:ka:gochara:0042')
        that contains NO keywords from _DOMAIN_KEYWORDS, so keyword inference
        would fall back to 'general'. The domain should still be `domain_col_value`
        thanks to B4-consume.
        """
        row = {
            'convergence_id': 'conv-001',
            'signal_id': 'sig-001',
            'net_label': 'auspicious_strong',
            'effective_score': 0.78,
            'peak_date': date(2027, 3, 15),
            'window_start': date(2027, 2, 1),
            'window_end': date(2027, 4, 30),
            'narrative': 'test narrative',
            'obstruction_summary': None,
            'confidence_label': 'high',
            'rarity_years': 12.0,
            'mode': 'vimshottari',
            'domain': domain_col_value,  # from kc.domain (migration 361)
        }
        return row

    def test_domain_inherited_from_convergence(self):
        """
        B4-consume: bhavishya row gets domain='relationship' from kc.domain,
        even though the signal_type_id contains no relationship-domain keywords.
        Previously this would fall to 'general'; now it reads the column directly.
        """
        from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
            KaBhavishyaLekhaWriter,
        )

        # Darshana row with kc.domain = 'relationship'
        darshana_row = self._make_darshana_row('relationship')

        # Cursor sequence:
        # 1. DELETE kala_bhavishya  (idempotency)
        # 2. SELECT darshana + convergence JOIN  -> returns our row with domain col
        # 3. SELECT signal_type_id from bodha_msr_signals  -> machine code, no keyword match
        # 4. INSERT kala_bhavishya
        cur_delete = _make_cursor()
        cur_darshana = _make_cursor([darshana_row])
        cur_signals = _make_cursor([{'signal_id': 'sig-001', 'signal_type_id': 'L3:ka:gochara:0042'}])
        cur_insert = _make_cursor()

        conn = _make_conn(cur_delete, cur_darshana, cur_signals, cur_insert)

        ctx = SimpleNamespace(
            db_conn=conn,
            config={'chart_id': 'chart-abc', 'birth_params': {}},
        )

        writer = KaBhavishyaLekhaWriter()
        result = writer.run(ctx)

        assert result.rows_inserted == 1, f"Expected 1 row, got {result.rows_inserted}"

        # Inspect the inserted row tuple: position 3 is `domain`
        inserted_rows = cur_insert.executemany.call_args[0][1]
        assert len(inserted_rows) == 1
        inserted_domain = inserted_rows[0][3]  # (chart_id, rank, tier, domain, ...)
        assert inserted_domain == 'relationship', (
            f"Expected domain='relationship' from kc.domain column, got '{inserted_domain}'. "
            "B4-consume fix may not be reading kc.domain correctly."
        )

    def test_domain_falls_back_to_keyword_when_convergence_domain_is_null(self):
        """
        B4-consume: when kc.domain IS NULL, keyword inference is used as fallback.
        signal_type_id contains 'kalatra' -> should map to 'relationship' via keyword.
        """
        from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
            KaBhavishyaLekhaWriter,
        )

        darshana_row = self._make_darshana_row(None)  # domain IS NULL

        cur_delete = _make_cursor()
        cur_darshana = _make_cursor([darshana_row])
        # Signal type contains 'kalatra' -> keyword match -> 'relationship'
        cur_signals = _make_cursor([{'signal_id': 'sig-001', 'signal_type_id': 'kalatra_yoga_v1'}])
        cur_insert = _make_cursor()

        conn = _make_conn(cur_delete, cur_darshana, cur_signals, cur_insert)

        ctx = SimpleNamespace(
            db_conn=conn,
            config={'chart_id': 'chart-abc', 'birth_params': {}},
        )

        writer = KaBhavishyaLekhaWriter()
        result = writer.run(ctx)

        inserted_rows = cur_insert.executemany.call_args[0][1]
        inserted_domain = inserted_rows[0][3]
        assert inserted_domain == 'relationship', (
            f"Expected keyword fallback to 'relationship' when kc.domain IS NULL, got '{inserted_domain}'"
        )

    def test_relationship_domain_now_possible_not_general(self):
        """
        Regression: with keyword-only inference, machine-code signal_type_ids always
        fell to 'general'. B4-consume allows non-general domains when kc.domain is set.
        """
        from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
            KaBhavishyaLekhaWriter,
        )

        domains_seen = set()
        for test_domain in ['relationship', 'financial', 'spiritual', 'psychological']:
            darshana_row = self._make_darshana_row(test_domain)

            cur_delete = _make_cursor()
            cur_darshana = _make_cursor([darshana_row])
            cur_signals = _make_cursor([{'signal_id': 'sig-001', 'signal_type_id': 'L3:ka:0001'}])
            cur_insert = _make_cursor()

            conn = _make_conn(cur_delete, cur_darshana, cur_signals, cur_insert)
            ctx = SimpleNamespace(
                db_conn=conn,
                config={'chart_id': 'chart-abc', 'birth_params': {}},
            )

            writer = KaBhavishyaLekhaWriter()
            writer.run(ctx)

            inserted_rows = cur_insert.executemany.call_args[0][1]
            domains_seen.add(inserted_rows[0][3])

        # All 4 test domains should appear in output (not collapsed to 'general')
        assert 'relationship' in domains_seen
        assert 'spiritual' in domains_seen

    def test_domain_col_absent_graceful_fallback(self):
        """
        If kc.domain column doesn't exist yet (pre-A3 migration), the writer falls
        back to the no-domain query (fresh cursor after rollback) and keyword inference
        without crashing.

        Cursor order in retry path:
          1. DELETE (idempotency)
          2. first darshana SELECT with domain col -> raises (column absent)
          3. rollback is called on conn
          4. retry darshana SELECT without domain col -> returns rows
          5. SELECT signal_type_id from bodha_msr_signals
          6. INSERT kala_bhavishya
        """
        from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
            KaBhavishyaLekhaWriter,
        )

        darshana_row_no_domain = {
            'convergence_id': 'conv-001',
            'signal_id': 'sig-001',
            'net_label': 'auspicious_strong',
            'effective_score': 0.78,
            'peak_date': date(2027, 3, 15),
            'window_start': date(2027, 2, 1),
            'window_end': date(2027, 4, 30),
            'narrative': 'test narrative',
            'obstruction_summary': None,
            'confidence_label': 'high',
            'rarity_years': 12.0,
            'mode': 'vimshottari',
            # No 'domain' key — simulates pre-migration schema
        }

        cur_delete = _make_cursor()

        # Cursor 2: raises on execute (simulates column-absent error)
        cur_failing = MagicMock()
        cur_failing.__enter__ = lambda s: s
        cur_failing.__exit__ = MagicMock(return_value=False)
        cur_failing.execute = MagicMock(side_effect=Exception("column kc.domain does not exist"))

        # Cursor 3 (retry path — fresh cursor opened after rollback)
        cur_retry = _make_cursor([darshana_row_no_domain])
        cur_signals = _make_cursor([{'signal_id': 'sig-001', 'signal_type_id': 'raja_yoga_v1'}])
        cur_insert = _make_cursor()

        conn = _make_conn(cur_delete, cur_failing, cur_retry, cur_signals, cur_insert)

        ctx = SimpleNamespace(
            db_conn=conn,
            config={'chart_id': 'chart-abc', 'birth_params': {}},
        )

        writer = KaBhavishyaLekhaWriter()
        # Should not raise — graceful fallback
        result = writer.run(ctx)

        assert result.rows_inserted == 1, f"Expected 1 row, got {result.rows_inserted}"
        # conn.rollback() should have been called once (for the failed query)
        conn.rollback.assert_called_once()
        # Domain should come from keyword inference ('raja_yoga_v1' -> 'career')
        inserted_rows = cur_insert.executemany.call_args[0][1]
        assert inserted_rows[0][3] == 'career', (
            f"Expected 'career' from keyword inference, got '{inserted_rows[0][3]}'"
        )


# ---------------------------------------------------------------------------
# O2 — mi_bhavisya domain-matched driving signals
# ---------------------------------------------------------------------------

class TestO2MiBhavisyaDomainSignals:
    """
    O2: predictions in different domains get different driving_signals sets,
    not the same first-5 generic signals.
    """

    def _make_anchor(self, anchor_id: str, domain: str) -> dict:
        return {
            'anchor_id': anchor_id,
            'domain': domain,
            'life_domain': None,
            'outcome_claim': f'{domain} outcome claim',
            'prediction_text': None,
            'summary': None,
            'window_start': date(2027, 1, 1),
            'window_end': date(2027, 6, 30),
            'start_date': None,
            'end_date': None,
            'eval_date': None,
            'magnitude': 'moderate',
            'confidence_low': 0.4,
            'confidence_high': 0.7,
            'falsifier_spec': None,
            'falsifier': None,
        }

    def _make_msr_signal(self, signal_id: str, salience: float, domains: list[str]) -> dict:
        return {
            'signal_id': signal_id,
            'computed_salience': salience,
            'domains_affected_array': domains,
        }

    def _run_mi_bhavisya(self, anchors: list[dict], msr_signals: list[dict]):
        """
        Run MiBhavisyaWriter with mocked DB returning given anchors and MSR signals.
        Returns list of prediction row tuples that would be inserted.
        """
        from pipeline.orchestrator.writers.mi_bhavisya import MiBhavisyaWriter

        # Cursors needed:
        # 1. _table_exists('phala_anchors')        -> True (fetchone returns something)
        # 2. SELECT * FROM phala_anchors           -> anchors
        # 3. _table_exists('bodha_msr_signals')    -> True
        # 4. SELECT signal_id, computed_salience, domains_affected_array -> msr_signals
        # 5. DELETE mimamsa_manifestation_sets
        # 6. DELETE mimamsa_predictions
        # 7. executemany INSERT mimamsa_predictions
        # 8. executemany INSERT mimamsa_manifestation_sets

        cur_phala_exists = MagicMock()
        cur_phala_exists.__enter__ = lambda s: s
        cur_phala_exists.__exit__ = MagicMock(return_value=False)
        cur_phala_exists.fetchone = MagicMock(return_value=(1,))

        cur_anchors = MagicMock()
        cur_anchors.__enter__ = lambda s: s
        cur_anchors.__exit__ = MagicMock(return_value=False)
        cur_anchors.fetchall = MagicMock(return_value=anchors)

        cur_msr_exists = MagicMock()
        cur_msr_exists.__enter__ = lambda s: s
        cur_msr_exists.__exit__ = MagicMock(return_value=False)
        cur_msr_exists.fetchone = MagicMock(return_value=(1,))

        cur_msr = MagicMock()
        cur_msr.__enter__ = lambda s: s
        cur_msr.__exit__ = MagicMock(return_value=False)
        cur_msr.fetchall = MagicMock(return_value=msr_signals)

        cur_deletes = MagicMock()
        cur_deletes.__enter__ = lambda s: s
        cur_deletes.__exit__ = MagicMock(return_value=False)

        cur_inserts = MagicMock()
        cur_inserts.__enter__ = lambda s: s
        cur_inserts.__exit__ = MagicMock(return_value=False)
        inserted_pred_rows = []
        inserted_mset_rows = []

        def _executemany(sql, rows):
            if 'mimamsa_predictions' in sql:
                inserted_pred_rows.extend(rows)
            elif 'mimamsa_manifestation_sets' in sql:
                inserted_mset_rows.extend(rows)

        cur_inserts.executemany = MagicMock(side_effect=_executemany)

        # We need to supply cursors in the order MiBhavisyaWriter calls them.
        # _table_exists calls conn.cursor() (no row_factory); SELECT calls use row_factory.
        # We use a side_effect list to handle the alternating call signatures.
        cursor_queue = [
            cur_phala_exists,    # _table_exists('phala_anchors')
            cur_anchors,         # SELECT * FROM phala_anchors
            cur_msr_exists,      # _table_exists('bodha_msr_signals')
            cur_msr,             # SELECT signal_id, ... FROM bodha_msr_signals
            cur_deletes,         # DELETE + DELETE (same cursor reused via __enter__)
            cur_inserts,         # executemany PRED + MSET
        ]

        def _cursor(**kwargs):
            return cursor_queue.pop(0) if cursor_queue else MagicMock()

        conn = MagicMock()
        conn.cursor = MagicMock(side_effect=_cursor)

        ctx = SimpleNamespace(
            db_conn=conn,
            config={'chart_id': 'chart-xyz', 'birth_params': {}},
            dry_run=False,
        )

        writer = MiBhavisyaWriter()
        result = writer.run(ctx)

        return result, inserted_pred_rows, inserted_mset_rows

    def test_driving_signals_are_domain_matched(self):
        """
        O2: predictions in 'career' and 'relationship' domains get different
        driving_signals sets (domain-specific, not the same first-5 generic signals).
        """
        anchors = [
            self._make_anchor('a1', 'career'),
            self._make_anchor('a2', 'relationship'),
        ]

        msr_signals = [
            self._make_msr_signal('sig-career-1', 0.95, ['career']),
            self._make_msr_signal('sig-career-2', 0.90, ['career']),
            self._make_msr_signal('sig-rel-1',    0.88, ['relationship']),
            self._make_msr_signal('sig-rel-2',    0.85, ['relationship']),
            self._make_msr_signal('sig-generic',  0.50, ['health']),
        ]

        result, pred_rows, _ = self._run_mi_bhavisya(anchors, msr_signals)

        assert len(pred_rows) == 2, f"Expected 2 prediction rows, got {len(pred_rows)}"

        # driving_signals is at index 13 in the tuple
        # (chart_id[0], prediction_id[1], anchor_id[2], outcome_claim[3], domain[4],
        #  obs_window[5], eval_date[6], conf_band[7], magnitude[8], falsifier[9],
        #  base_rate[10], emitted_at[11], lifecycle_status[12], driving_signals[13], ...)
        driving_0 = json.loads(pred_rows[0][13])  # career
        driving_1 = json.loads(pred_rows[1][13])  # relationship

        ids_0 = {d['signal_id'] for d in driving_0}
        ids_1 = {d['signal_id'] for d in driving_1}

        assert ids_0 != ids_1, (
            "O2 fix not applied: career and relationship predictions have the SAME "
            f"driving_signals: {ids_0}"
        )
        assert 'sig-career-1' in ids_0, f"Career signal missing from career prediction: {ids_0}"
        assert 'sig-rel-1' in ids_1, f"Relationship signal missing from relationship prediction: {ids_1}"

        # Cross-contamination check: career signal should NOT drive relationship prediction
        assert 'sig-career-1' not in ids_1, (
            "sig-career-1 should not be in relationship driving_signals"
        )
        assert 'sig-rel-1' not in ids_0, (
            "sig-rel-1 should not be in career driving_signals"
        )

    def test_driving_signals_fallback_when_no_domain_match(self):
        """
        O2: when no MSR signals are tagged to a prediction's domain, fall back to
        first-5 generic signals (not crash, not empty list).
        """
        anchors = [self._make_anchor('a1', 'unknown_exotic_domain')]

        msr_signals = [
            self._make_msr_signal('sig-1', 0.9, ['career']),
            self._make_msr_signal('sig-2', 0.8, ['health']),
        ]

        result, pred_rows, _ = self._run_mi_bhavisya(anchors, msr_signals)

        assert len(pred_rows) == 1
        driving = json.loads(pred_rows[0][13])
        # Should fall back to generic signals, not be empty
        assert len(driving) > 0, "Fallback driving_signals should not be empty"

    def test_domain_signals_capped_at_five(self):
        """
        O2: at most 5 driving signals per domain even if more are available.
        """
        anchors = [self._make_anchor('a1', 'career')]

        # 8 career-domain signals
        msr_signals = [
            self._make_msr_signal(f'sig-career-{i}', 1.0 - i * 0.05, ['career'])
            for i in range(8)
        ]

        result, pred_rows, _ = self._run_mi_bhavisya(anchors, msr_signals)

        assert len(pred_rows) == 1
        driving = json.loads(pred_rows[0][13])
        assert len(driving) <= 5, f"Expected <=5 driving signals, got {len(driving)}"

    def test_different_domains_no_shared_generic_signals(self):
        """
        Regression: before O2 fix, ALL predictions got the same first-5 signals
        regardless of domain. Verify that no longer happens when domain-specific
        signals exist.
        """
        anchors = [
            self._make_anchor('a1', 'career'),
            self._make_anchor('a2', 'spiritual'),
            self._make_anchor('a3', 'relationship'),
        ]

        # Each domain gets its own exclusive signals
        msr_signals = (
            [self._make_msr_signal(f'career-sig-{i}', 0.9 - i * 0.1, ['career']) for i in range(3)]
            + [self._make_msr_signal(f'spiritual-sig-{i}', 0.8 - i * 0.1, ['spiritual']) for i in range(3)]
            + [self._make_msr_signal(f'rel-sig-{i}', 0.7 - i * 0.1, ['relationship']) for i in range(3)]
        )

        result, pred_rows, _ = self._run_mi_bhavisya(anchors, msr_signals)

        assert len(pred_rows) == 3

        driving_career   = {d['signal_id'] for d in json.loads(pred_rows[0][13])}
        driving_spiritual = {d['signal_id'] for d in json.loads(pred_rows[1][13])}
        driving_rel      = {d['signal_id'] for d in json.loads(pred_rows[2][13])}

        # All three sets should be distinct
        assert driving_career != driving_spiritual, "career and spiritual domains share signals"
        assert driving_career != driving_rel, "career and relationship domains share signals"
        assert driving_spiritual != driving_rel, "spiritual and relationship domains share signals"
