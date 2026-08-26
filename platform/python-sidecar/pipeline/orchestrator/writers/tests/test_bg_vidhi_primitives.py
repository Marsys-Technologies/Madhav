from __future__ import annotations

from contextlib import contextmanager

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_vidhi_primitives import (
    PRIMITIVE_ROWS,
    VidhiPrimitivesWriter,
)


class _RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class _Connection:
    def __init__(self) -> None:
        self.cursor_instance = _RecordingCursor()

    @contextmanager
    def cursor(self):
        yield self.cursor_instance


def test_writer_converges_changed_rows_and_removes_unknown_primitives():
    """A stale DB-only primitive must not survive a canonical registry replay."""
    conn = _Connection()

    VidhiPrimitivesWriter().run(ContextSpec(
        asset_id="bg_vidhi_primitives",
        build_id="vidhi-convergence",
        db_conn=conn,
    ))

    statements = [sql for sql, _ in conn.cursor_instance.calls]
    upserts = [sql for sql in statements if "INSERT INTO vidhi_primitives" in sql]
    deletes = [sql for sql in statements if "DELETE FROM vidhi_primitives" in sql]
    assert len(upserts) == len(PRIMITIVE_ROWS)
    assert all("DO UPDATE SET" in sql and "IS DISTINCT FROM" in sql for sql in upserts)
    assert len(deletes) == 1
    assert "ANY" in deletes[0]
