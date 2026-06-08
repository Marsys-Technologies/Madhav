import pytest
from pipeline.orchestrator.writers import (
    register, get_writer, list_writers, WriterBase, ContextSpec, WriterResult,
)


def test_register_and_get():
    @register('test_infra_asset_1')
    class TestWriter(WriterBase):
        asset_id = 'test_infra_asset_1'
        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)
    assert get_writer('test_infra_asset_1') is TestWriter


def test_duplicate_raises():
    @register('test_infra_asset_dup')
    class A(WriterBase):
        asset_id = 'test_infra_asset_dup'
        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)
    with pytest.raises(ValueError, match='duplicate'):
        @register('test_infra_asset_dup')
        class B(WriterBase):
            asset_id = 'test_infra_asset_dup'
            def run(self, ctx):
                return WriterResult(asset_id=self.asset_id, rows_inserted=0)


def test_writer_must_subclass_base():
    with pytest.raises(TypeError):
        @register('bad_infra_writer')
        class NotAWriter:
            asset_id = 'bad_infra_writer'


def test_context_spec_defaults():
    from unittest.mock import MagicMock
    conn = MagicMock()
    ctx = ContextSpec(asset_id='bg_test', build_id='run-1', db_conn=conn)
    assert ctx.dry_run is False
    assert ctx.config == {}


def test_writer_result_defaults():
    r = WriterResult(asset_id='bg_test', rows_inserted=5)
    assert r.rows_updated == 0
    assert r.rows_skipped == 0
    assert r.duration_seconds == 0.0
    assert r.notes == ''
