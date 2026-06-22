"""
test_ph_wave6.py — Wave 6: ph_pramana (D5 NO-SCORING gate).

Covers:
  classify_window_status: pending / open / past_window
  parse_observable_criteria: extracts REFUTED/CONFIRMED + deadline
  classify_evidence_strength: direct/indirect/proxy taxonomy
  derive_pramana_records: evidence_type assignment; pending for open windows
  D5 gate: PramanaRecord has NO scoring fields
  Anti-drift: writer never inserts calibration_score etc.
"""
from __future__ import annotations

from datetime import date

import pytest

from services.ph_pramana.engine import (
    AnchorForPramana,
    LelEntry,
    PramanaContext,
    D5ViolationError,
    classify_window_status,
    parse_observable_criteria,
    classify_evidence_strength,
    derive_pramana_records,
    PramanaRecord,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _anchor(**kwargs) -> AnchorForPramana:
    defaults = dict(
        anchor_id='a1',
        domain='career',
        anchor_source='convergence',
        falsifier='REFUTED if no career shift by 2027-12-31. CONFIRMED if documented career change.',
        window_start=date(2026, 6, 1),
        window_end=date(2027, 12, 31),
        peak_date=date(2027, 1, 1),
        magnitude='major',
        confidence_high=0.55,
        derivation_ledger_jsonb={'anchor_source': 'convergence'},
    )
    defaults.update(kwargs)
    return AnchorForPramana(**defaults)


def _lel(domain='career', event_date=date(2027, 3, 15)) -> LelEntry:
    return LelEntry(
        lel_id=101, event_date=event_date, domain=domain,
        event_summary='Significant career transition observed.',
        outcome_valence='positive',
        lel_jsonb={'id': 101, 'event_date': str(event_date), 'summary': 'Career transition'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# WINDOW STATUS
# ══════════════════════════════════════════════════════════════════════════════

class TestClassifyWindowStatus:
    def test_pending_when_before_window(self):
        status = classify_window_status(date(2028, 1, 1), date(2029, 1, 1), date(2026, 6, 22))
        assert status == 'pending'

    def test_open_when_inside_window(self):
        status = classify_window_status(date(2026, 1, 1), date(2027, 12, 31), date(2026, 6, 22))
        assert status == 'open'

    def test_past_when_after_window(self):
        status = classify_window_status(date(2024, 1, 1), date(2025, 1, 1), date(2026, 6, 22))
        assert status == 'past_window'

    def test_none_window_defaults_open(self):
        status = classify_window_status(None, None, date(2026, 6, 22))
        assert status == 'open'


# ══════════════════════════════════════════════════════════════════════════════
# PARSE CRITERIA
# ══════════════════════════════════════════════════════════════════════════════

class TestParseObservableCriteria:
    def test_extracts_refuted_clause(self):
        c = parse_observable_criteria(
            'REFUTED if no career shift by 2027-12-31. CONFIRMED if career change documented.'
        )
        assert 'no career shift' in c['refuted_criterion']

    def test_extracts_confirmed_clause(self):
        c = parse_observable_criteria(
            'REFUTED if X. CONFIRMED if career change documented by 2027.'
        )
        assert 'career change' in c['confirmed_criterion']

    def test_extracts_deadline(self):
        c = parse_observable_criteria('REFUTED if nothing by 2027-12-31. CONFIRMED if Y.')
        assert c['deadline'] == '2027-12-31'

    def test_raw_field_present(self):
        c = parse_observable_criteria('REFUTED if X. CONFIRMED if Y.')
        assert 'raw' in c

    def test_empty_falsifier_graceful(self):
        c = parse_observable_criteria('')
        assert 'refuted_criterion' in c
        assert 'confirmed_criterion' in c


# ══════════════════════════════════════════════════════════════════════════════
# EVIDENCE STRENGTH
# ══════════════════════════════════════════════════════════════════════════════

class TestClassifyEvidenceStrength:
    def test_pending_observation_is_proxy(self):
        assert classify_evidence_strength('pending_observation', None, 'career') == 'proxy'

    def test_lel_same_domain_is_direct(self):
        assert classify_evidence_strength('life_event_match', 'career', 'career') == 'direct'

    def test_lel_different_domain_is_indirect(self):
        assert classify_evidence_strength('life_event_match', 'financial', 'career') == 'indirect'

    def test_self_report_is_indirect(self):
        assert classify_evidence_strength('self_report', None, 'career') == 'indirect'

    def test_life_event_miss_same_domain_is_direct(self):
        assert classify_evidence_strength('life_event_miss', 'career', 'career') == 'direct'


# ══════════════════════════════════════════════════════════════════════════════
# DERIVE PRAMANA RECORDS
# ══════════════════════════════════════════════════════════════════════════════

class TestDerivePramanaRecords:
    def test_open_window_no_lel_is_pending(self):
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[_anchor()], lel_entries=[])
        recs = derive_pramana_records(ctx)
        assert len(recs) == 1
        assert recs[0].evidence_type == 'pending_observation'
        assert recs[0].window_status == 'open'

    def test_past_window_no_lel_is_miss(self):
        a = _anchor(window_start=date(2024, 1, 1), window_end=date(2025, 1, 1))
        ctx = PramanaContext(chart_id='cid', today=date(2026, 6, 22),
                             anchors=[a], lel_entries=[])
        recs = derive_pramana_records(ctx)
        assert recs[0].evidence_type == 'life_event_miss'
        assert recs[0].window_status == 'past_window'

    def test_lel_match_in_window(self):
        ctx = PramanaContext(chart_id='cid', today=date(2027, 6, 1),
                             anchors=[_anchor()], lel_entries=[_lel()])
        recs = derive_pramana_records(ctx)
        assert recs[0].evidence_type == 'life_event_match'
        assert recs[0].lel_entry_id == 101

    def test_lel_outside_window_not_matched(self):
        a = _anchor(window_end=date(2026, 12, 31))
        lel = _lel(event_date=date(2028, 5, 1))  # outside window
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[a], lel_entries=[lel])
        recs = derive_pramana_records(ctx)
        assert recs[0].lel_entry_id is None

    def test_lel_wrong_domain_not_matched(self):
        lel = _lel(domain='health')   # anchor domain is 'career'
        ctx = PramanaContext(chart_id='cid', today=date(2027, 6, 1),
                             anchors=[_anchor()], lel_entries=[lel])
        recs = derive_pramana_records(ctx)
        assert recs[0].lel_entry_id is None

    def test_observable_criteria_always_populated(self):
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[_anchor()], lel_entries=[])
        recs = derive_pramana_records(ctx)
        assert recs[0].observable_criteria_jsonb
        assert 'refuted_criterion' in recs[0].observable_criteria_jsonb

    def test_d5_field_absent_from_record(self):
        """D5: PramanaRecord must NOT have calibration_score etc."""
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[_anchor()], lel_entries=[])
        recs = derive_pramana_records(ctx)
        for rec in recs:
            for forbidden in ('calibration_score', 'posterior_probability',
                              'accuracy_rate', 'hit_rate', 'brier_score'):
                assert not hasattr(rec, forbidden), \
                    f"D5 VIOLATION: PramanaRecord has forbidden field '{forbidden}'"

    def test_derivation_ledger_has_d5_note(self):
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[_anchor()], lel_entries=[])
        recs = derive_pramana_records(ctx)
        ledger_text = str(recs[0].derivation_ledger_jsonb)
        assert 'l5' in ledger_text.lower() or 'calibration' in ledger_text.lower()

    def test_empty_anchors_returns_empty(self):
        ctx = PramanaContext(chart_id='cid', today=date(2026, 10, 1),
                             anchors=[], lel_entries=[])
        recs = derive_pramana_records(ctx)
        assert recs == []


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-DRIFT / D5 ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════

class TestPramanaAntiDrift:
    def test_writer_never_commits(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_pramana.py'
        )
        with open(path) as f:
            src = f.read()
        code_lines = [ln for ln in src.splitlines()
                      if not ln.strip().startswith('#') and '"""' not in ln]
        assert '.commit()' not in '\n'.join(code_lines)

    def test_writer_only_writes_phala_pramana(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_pramana.py'
        )
        with open(path) as f:
            src = f.read()
        assert 'INSERT INTO phala_pramana' in src
        assert 'INSERT INTO phala_anchors' not in src

    def test_writer_insert_has_no_scoring_columns(self):
        """D5: verify INSERT statement in writer does not include any scoring column."""
        import os, re
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_pramana.py'
        )
        with open(path) as f:
            src = f.read()
        # Extract only the INSERT INTO ... column list (between first ( and ) after INSERT INTO)
        insert_match = re.search(r'INSERT INTO phala_pramana \(\s*(.*?)\s*\) VALUES', src, re.DOTALL)
        insert_cols = insert_match.group(1).lower() if insert_match else ''
        forbidden = ['calibration_score', 'posterior_probability', 'accuracy_rate',
                     'hit_rate', 'brier_score', 'empirical_score']
        for col in forbidden:
            assert col not in insert_cols, \
                f"D5 VIOLATION: '{col}' found in ph_pramana INSERT column list"

    def test_migration_create_table_has_no_scoring_columns(self):
        """D5: verify CREATE TABLE block has no scoring column *definitions* (ignoring comments)."""
        import os, re
        path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'supabase', 'migrations', '336_phala_pramana.sql'
        )
        with open(path) as f:
            src = f.read()
        # Strip SQL line comments before checking
        src_no_comments = re.sub(r'--[^\n]*', '', src)
        ct_match = re.search(
            r'CREATE TABLE IF NOT EXISTS phala_pramana \((.*?)\);',
            src_no_comments, re.DOTALL,
        )
        ct_body = ct_match.group(1).lower() if ct_match else ''
        for col in ['calibration_score', 'posterior_probability', 'accuracy_rate', 'brier_score']:
            assert col not in ct_body, \
                f"D5 VIOLATION: '{col}' column definition found in migration 336 CREATE TABLE"
