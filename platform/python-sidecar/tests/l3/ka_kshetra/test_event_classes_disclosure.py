"""
tests/l3/ka_kshetra/test_event_classes_disclosure.py — F-78 (PARIŚEṢA S3->S6):
kala_field_snapshots.event_classes is the ATTEMPTED set, not the BUILT set.

Exit test for F-78's SPEC.md. Before the fix: `services.ka_kshetra.writer` has
no `built_event_classes` function, so every test in TestBuiltEventClassesHelper
and TestHelperMatchesRealBuildOutput fails (AttributeError). After the fix:
the function exists, its output matches what the writer ACTUALLY wrote to
kala_field (not just its own self._skipped bookkeeping), and the disclosure
migration's COMMENT ON COLUMN exists and names both the conflation and the fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import writer as W  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402


# SAMPŪRTI G1 (2026-08-10): stage0/1/3 are now wired into plan_substeps but
# require swisseph + ephemeris_daily DB rows that FakeConn doesn't provide.
# Exclude them from the import table so writer.py's __import__ silently skips
# them — matching the autouse fixture in test_writer.py exactly.
# stage2_promise is also patched (same reason as test_writer.py §MERGE-TRAIN
# NOTE 2026-07-30) so the fallback kala_field_routes path is used.
@pytest.fixture(autouse=True)
def _patch_g1_stages(monkeypatch):
    monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage2_promise', None)
    monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage0_kinematics', None)
    monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage1_symbolization', None)
    monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage3_clocks', None)
    yield


def _run_full_build(tables) -> tuple[W.KaKshetraWriter, FakeConn]:
    conn = FakeConn(tables)
    ctx = FakeCtx(conn, F.CHART_ID)
    writer = W.KaKshetraWriter()
    for step in writer.plan_substeps(ctx):
        writer.run_substep(ctx, step)
    return writer, conn


# ── exit test: fails today (AttributeError — built_event_classes doesn't
# exist yet), passes once §2a lands ─────────────────────────────────────────

class TestBuiltEventClassesHelper:
    def test_helper_subtracts_skipped_from_attempted(self):
        attempted = ['marriage', 'career_change', 'surgery']
        skipped = [{'event_class': 'career_change', 'reason': 'no_class_prior_row',
                    'detail': 'no bg_class_priors lifetime-count row'}]
        assert W.built_event_classes(attempted, skipped) == ['marriage', 'surgery']

    def test_helper_is_order_independent_and_deduplicated(self):
        skipped = [{'event_class': 'b', 'reason': 'x', 'detail': 'x'}]
        assert W.built_event_classes(['b', 'a', 'a'], skipped) == ['a']

    def test_nothing_skipped_returns_the_full_attempted_set(self):
        assert (W.built_event_classes(['marriage', 'surgery'], [])
                == ['marriage', 'surgery'])

    def test_everything_skipped_returns_empty(self):
        skipped = [{'event_class': 'marriage', 'reason': 'r', 'detail': 'd'}]
        assert W.built_event_classes(['marriage'], skipped) == []


# ── recurrence guard (§3 element 5): ties the helper's answer to what the
# writer ACTUALLY wrote to kala_field, not just to its own self._skipped
# bookkeeping, so a future divergence between "attempted", "skipped", and
# "has real rows" fails this closed ─────────────────────────────────────────

class TestHelperMatchesRealBuildOutput:
    def test_fully_built_snapshot(self):
        writer, conn = _run_full_build(F.build_tables())
        built = W.built_event_classes(writer._event_classes, writer._skipped)
        assert set(built) == {r['event_class'] for r in conn.tables['kala_field']}
        assert set(built) == set(writer._event_classes)  # nothing skipped this build

    def test_fully_skipped_snapshot(self):
        writer, conn = _run_full_build(F.build_tables(with_lifetime_prior=False))
        built = W.built_event_classes(writer._event_classes, writer._skipped)
        assert built == []
        assert conn.tables['kala_field'] == []

    def test_snapshot_column_still_carries_the_unfiltered_attempted_set(self):
        # This fix does NOT change what is written to
        # kala_field_snapshots.event_classes (still the full attempted list,
        # per its new comment) — it adds a way to DERIVE the built set: it
        # does not filter the column itself at write time.
        writer, conn = _run_full_build(F.build_tables(with_lifetime_prior=False))
        snap = conn.tables['kala_field_snapshots'][0]
        assert snap['event_classes'] == writer._event_classes
        assert F.EVENT_CLASS in snap['event_classes']


# ── the doc-comment half of the fix, made checkable ──────────────────────────

class TestColumnIsDocumented:
    MIGRATION_PATH = (
        Path(__file__).resolve().parents[4]
        / 'supabase' / 'migrations'
        / '579_kala_field_snapshots_event_classes_disclosure.sql'
    )

    def test_migration_file_exists(self):
        assert self.MIGRATION_PATH.exists(), (
            f'{self.MIGRATION_PATH} not found -- F-78 disclosure comment migration missing'
        )

    def test_comment_names_the_conflation_and_the_fix(self):
        sql = self.MIGRATION_PATH.read_text()
        assert 'COMMENT ON COLUMN kala_field_snapshots.event_classes' in sql
        assert 'built_event_classes' in sql
        assert 'skipped_classes' in sql
