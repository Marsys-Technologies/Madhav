"""Hermetic tests for bodha_writers._idempotency._delete.

Regression guard for the bo_laksana native-rebuild timeout: a large chart's
idempotency DELETE (esp. replace_prior_msr_for_chart, which FK-cascades a
DELETE across bodha_msr_signals children) can exceed the DB role's default
statement_timeout (25-30s, sized for OLTP) and raise
psycopg.errors.QueryCanceled. Every bodha idempotency delete routes through
_delete, so _delete must SET LOCAL statement_timeout = 0 before the DELETE —
the same pattern as the ka_* writers (PR 422).
"""
import pathlib

import pytest

from bodha_writers import _idempotency as mod

_WRITERS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "pipeline" / "orchestrator" / "writers"
)

# bo_* orchestrator writers that issue an inline raw DELETE bypassing
# bodha_writers._idempotency._delete. Each must SET LOCAL statement_timeout = 0
# before its DELETE so a large native chart cannot HALT the rebuild the way
# bo_laksana did (ka_* precedent, PR 422).
_INLINE_DELETE_WRITERS = [
    "bo_anveshana",
    "bo_drishti",
    "bo_cgm_paths",
    "bo_cgm_motifs",
    "bo_pratijna",
    "bo_cdlm_summary",
    "bo_sangati",
    "bo_chart_gestalt",
]


class _FakeCursor:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _FakeConn:
    """Records every .execute() call in order and returns a cursor whose
    rowcount is configurable, so tests can assert call ordering + rowcount
    passthrough."""

    def __init__(self, rowcount: int = 7) -> None:
        self.calls: list[tuple[str, object]] = []
        self._rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        return _FakeCursor(self._rowcount)


def test_delete_sets_local_timeout_before_delete():
    conn = _FakeConn(rowcount=42)
    rc = mod._delete(conn, "DELETE FROM bodha_msr_signals WHERE chart_id = %s", ["cid"])

    # Two execute calls, in order: SET LOCAL first, DELETE second.
    assert len(conn.calls) == 2, conn.calls
    set_sql, set_params = conn.calls[0]
    del_sql, del_params = conn.calls[1]

    assert "SET LOCAL statement_timeout = 0" in set_sql
    assert "DELETE FROM bodha_msr_signals" in del_sql
    # The SET LOCAL precedes the DELETE.
    set_idx = next(i for i, (s, _) in enumerate(conn.calls) if "SET LOCAL statement_timeout" in s)
    del_idx = next(i for i, (s, _) in enumerate(conn.calls) if s.startswith("DELETE"))
    assert set_idx < del_idx

    # rowcount is returned exactly as before, from the DELETE cursor.
    assert rc == 42
    # DELETE receives the original params untouched.
    assert del_params == ["cid"]


def test_delete_returns_zero_when_rowcount_missing():
    class _NoRowcountCursor:
        pass

    class _Conn:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append(sql)
            return _NoRowcountCursor()

    conn = _Conn()
    rc = mod._delete(conn, "DELETE FROM bodha_cgm_nodes WHERE chart_id = %s", ["cid"])
    assert rc == 0
    # SET LOCAL still issued before the DELETE.
    assert "SET LOCAL statement_timeout = 0" in conn.calls[0]
    assert conn.calls[1].startswith("DELETE")


def test_replace_prior_msr_for_chart_guards_each_delete():
    """The heavy full-wipe path issues 3 DELETEs (embeddings, contradictions,
    signals); each must be preceded by its own SET LOCAL statement_timeout = 0."""
    conn = _FakeConn(rowcount=1)
    mod.replace_prior_msr_for_chart(conn, "cid", "lahiri")

    set_calls = [s for s, _ in conn.calls if "SET LOCAL statement_timeout" in s]
    del_calls = [s for s, _ in conn.calls if s.startswith("DELETE")]
    assert len(del_calls) == 3, conn.calls
    assert len(set_calls) == 3, conn.calls
    # Interleaved SET/DELETE/SET/DELETE/SET/DELETE ordering.
    kinds = ["SET" if "SET LOCAL" in s else "DELETE" for s, _ in conn.calls]
    assert kinds == ["SET", "DELETE", "SET", "DELETE", "SET", "DELETE"], kinds


# ──────────────────────────────────────────────────────────────────────────────
# Source-level guards: the bo_* writers that bypass _delete with an inline raw
# DELETE must SET LOCAL statement_timeout = 0 before that DELETE (same class of
# bug as bo_laksana; a large native chart could HALT the rebuild at any of them).
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("writer", _INLINE_DELETE_WRITERS)
def test_inline_delete_writer_has_timeout_guard_before_delete(writer):
    src = (_WRITERS_DIR / f"{writer}.py").read_text()
    assert "DELETE FROM bodha" in src, f"{writer}: expected an inline DELETE"
    guard_idx = src.find("SET LOCAL statement_timeout = 0")
    delete_idx = src.find("DELETE FROM bodha")
    assert guard_idx != -1, f"{writer}: missing SET LOCAL statement_timeout = 0 guard"
    assert guard_idx < delete_idx, (
        f"{writer}: SET LOCAL statement_timeout guard must precede the first "
        f"inline DELETE (guard@{guard_idx}, delete@{delete_idx})"
    )
