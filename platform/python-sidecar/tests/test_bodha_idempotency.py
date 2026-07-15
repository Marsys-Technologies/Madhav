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
    """The heavy scoped-wipe path issues 3 DELETEs (embeddings, contradictions,
    signals); each must be preceded by its own SET LOCAL statement_timeout = 0."""
    conn = _FakeConn(rowcount=1)
    mod.replace_prior_msr_for_chart(conn, "cid", "lahiri", ["yoga", "dosha"])

    set_calls = [s for s, _ in conn.calls if "SET LOCAL statement_timeout" in s]
    del_calls = [s for s, _ in conn.calls if s.startswith("DELETE")]
    assert len(del_calls) == 3, conn.calls
    assert len(set_calls) == 3, conn.calls
    # Interleaved SET/DELETE/SET/DELETE/SET/DELETE ordering.
    kinds = ["SET" if "SET LOCAL" in s else "DELETE" for s, _ in conn.calls]
    assert kinds == ["SET", "DELETE", "SET", "DELETE", "SET", "DELETE"], kinds


def test_replace_prior_msr_for_chart_scopes_every_delete_to_owned_classes():
    """D-1.5b regression guard: every DELETE issued by
    replace_prior_msr_for_chart must be scoped to the caller's
    owned_signal_type_classes allowlist — never a blanket
    (chart_id, ayanamsha_id)-only wipe. This is the exact defect that let
    bo_laksana's rebuild silently destroy bo_sudarshana's
    'sudarshana_agreement' rows (see D-1.5b full-rebuild post-mortem,
    chart 482012f1)."""
    conn = _FakeConn(rowcount=1)
    owned = ["yoga", "dosha", "composite_state"]
    mod.replace_prior_msr_for_chart(conn, "cid", "lahiri", owned)

    del_calls = [(s, p) for s, p in conn.calls if s.startswith("DELETE")]
    assert len(del_calls) == 3, conn.calls
    for sql, params in del_calls:
        assert "signal_type_class" in sql, (
            f"DELETE not scoped by signal_type_class — would blanket-wipe: {sql}"
        )
        assert owned in params, (
            f"DELETE does not bind the owned_signal_type_classes allowlist: {sql} {params}"
        )
    # The final (bodha_msr_signals) DELETE must not target bo_sudarshana's class.
    final_sql, final_params = del_calls[-1]
    assert "bodha_msr_signals" in final_sql
    assert "sudarshana_agreement" not in owned


def test_replace_prior_msr_for_chart_rejects_empty_allowlist():
    """A caller MUST declare what it owns; refusing an empty list prevents a
    silent regression back to the blanket-delete bug."""
    conn = _FakeConn(rowcount=1)
    with pytest.raises(ValueError):
        mod.replace_prior_msr_for_chart(conn, "cid", "lahiri", [])


class _RealisticFakeConn:
    """Simulates real DELETE semantics (row-level filtering) well enough to
    prove cross-writer isolation, without a live Postgres connection: holds
    an in-memory table of bodha_msr_signals-shaped dict rows and applies the
    same WHERE-clause semantics replace_prior_msr_for_chart depends on
    (chart_id, ayanamsha_id, signal_type_class = ANY(list))."""

    def __init__(self, signal_rows: list[dict]):
        self.signal_rows = signal_rows  # bodha_msr_signals
        self.embedding_rows: list[dict] = []
        self.contradiction_rows: list[dict] = []

    def execute(self, sql, params=None):
        if "SET LOCAL statement_timeout" in sql:
            return _FakeCursor(0)
        if sql.startswith("DELETE FROM bodha_signal_embeddings"):
            chart_id, ayanamsha_id, owned = params
            owned_signal_ids = {
                r["signal_id"] for r in self.signal_rows
                if r["chart_id"] == chart_id and r["ayanamsha_id"] == ayanamsha_id
                and r["signal_type_class"] in owned
            }
            before = len(self.embedding_rows)
            self.embedding_rows = [r for r in self.embedding_rows if r["signal_id"] not in owned_signal_ids]
            return _FakeCursor(before - len(self.embedding_rows))
        if sql.startswith("DELETE FROM bodha_contradictions"):
            chart_id = params[0]
            ayanamsha_id, owned = params[1], params[2]
            owned_signal_ids = {
                r["signal_id"] for r in self.signal_rows
                if r["chart_id"] == chart_id and r["ayanamsha_id"] == ayanamsha_id
                and r["signal_type_class"] in owned
            }
            before = len(self.contradiction_rows)
            self.contradiction_rows = [
                r for r in self.contradiction_rows
                if r["signal_a_id"] not in owned_signal_ids and r["signal_b_id"] not in owned_signal_ids
            ]
            return _FakeCursor(before - len(self.contradiction_rows))
        if sql.startswith("DELETE FROM bodha_msr_signals"):
            chart_id, ayanamsha_id, owned = params
            before = len(self.signal_rows)
            self.signal_rows = [
                r for r in self.signal_rows
                if not (r["chart_id"] == chart_id and r["ayanamsha_id"] == ayanamsha_id
                        and r["signal_type_class"] in owned)
            ]
            return _FakeCursor(before - len(self.signal_rows))
        raise AssertionError(f"unexpected SQL in test double: {sql}")


def test_bo_sudarshana_rows_survive_bo_laksana_rebuild_cycle():
    """The D-1.5b regression itself, end to end at the row-semantics level:
    bo_sudarshana writes its 'sudarshana_agreement' rows, then bo_laksana runs
    its own delete-then-insert idempotency cycle (as it does on every
    rebuild) — bo_sudarshana's rows must still be present afterwards.

    Before the fix, replace_prior_msr_for_chart(conn, chart_id, ayanamsha_id)
    (no class scoping) wiped bodha_msr_signals unconditionally for the
    (chart_id, ayanamsha_id) pair, taking bo_sudarshana's rows down to 0."""
    chart_id, aya = "482012f1", "lahiri_chitrapaksha"

    # bo_sudarshana's prior write (its own, correctly-scoped, delete-then-insert
    # already ran and left these rows in place).
    sudarshana_rows = [
        {"signal_id": f"sud-{i}", "chart_id": chart_id, "ayanamsha_id": aya,
         "signal_type_class": "sudarshana_agreement"}
        for i in range(9)
    ]
    # bo_laksana's OWN prior rows from an earlier build, about to be replaced.
    laksana_prior_rows = [
        {"signal_id": f"lak-old-{i}", "chart_id": chart_id, "ayanamsha_id": aya,
         "signal_type_class": "yoga"}
        for i in range(3)
    ]
    conn = _RealisticFakeConn(signal_rows=sudarshana_rows + laksana_prior_rows)

    from pipeline.orchestrator.writers.bo_laksana import BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES

    deleted = mod.replace_prior_msr_for_chart(
        conn, chart_id, aya, BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES,
    )
    assert deleted == 3, "should delete only bo_laksana's 3 prior 'yoga' rows"

    remaining_classes = {r["signal_type_class"] for r in conn.signal_rows}
    assert remaining_classes == {"sudarshana_agreement"}, (
        f"bo_sudarshana rows did not survive bo_laksana's delete-then-insert "
        f"cycle: {conn.signal_rows}"
    )
    remaining_ids = {r["signal_id"] for r in conn.signal_rows}
    assert remaining_ids == {r["signal_id"] for r in sudarshana_rows}


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
