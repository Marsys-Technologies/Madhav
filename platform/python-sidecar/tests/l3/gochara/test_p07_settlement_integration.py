"""P07-R1: exercise the real settlement loader, DB row adapter and both consumers.

Only SQL transport is replaced; receipt parsing, tier filtering, canonicalization
and consumer routing execute unchanged. Dates/row IDs below are synthetic.
"""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
from uuid import UUID

from services.gochara_kernel import dasha_read

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD = "ca17639b-f3cf-42c7-9866-0a61f3855802"
ROW = UUID("11111111-1111-4111-8111-111111111111")
LO = datetime(2026, 1, 1, tzinfo=timezone.utc)
HI = datetime(2026, 1, 9, tzinfo=timezone.utc)


class SqlTransport:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        assert "chart_dashas" in sql
        if "SELECT DISTINCT" in sql:
            self.result = [(BUILD,)]
        else:
            # Match the actual SELECT projection; do not fake the adapter's dicts.
            assert "dasha_row_id, system_id, level_n, parent_row_id" in sql
            self.result = [(ROW, "vimshottari", 1, None, "Saturn", LO, HI,
                            UUID(BUILD), "two_pass_verified")]
        return self

    def fetchall(self):
        return self.result


def test_settled_build_survives_real_row_adapter_and_canonicalization():
    conn = SqlTransport()
    rows, contract = dasha_read.load_pinned_vimshottari(conn, CHART)
    assert contract["build_id"] == BUILD
    assert len(rows) == 1 and rows[0]["dasha_row_id"] == ROW
    assert rows[0]["start_iso"] == LO and rows[0]["end_iso"] == HI
    assert rows[0]["merged_row_ids"] == [str(ROW)] and rows[0]["index"] == 0
    assert conn.calls[-1][1][-1] == BUILD and "AND build_id = %s" in conn.calls[-1][0]


def test_registered_writer_operand_uses_the_real_settled_loader():
    conn = SqlTransport()
    rows_for, contract = dasha_read.make_period_rows_for(conn, CHART)
    assert rows_for("saturn", "md") == [{"start_iso": LO, "end_iso": HI}]
    assert contract["read"] is True and contract["build_id"] == BUILD
    assert rows_for("saturn", "ad") == []
    assert len(conn.calls) == 3  # one guarded raw read and one build-pinned read, cached


def test_class_context_delegates_vimshottari_to_the_shared_settlement_loader(monkeypatch):
    path = Path(__file__).resolve().parents[3] / "scripts/kala_gochara_cutover/step06a_class_context.py"
    spec = importlib.util.spec_from_file_location("p07_step06a", path)
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)
    actual = dasha_read.load_pinned_vimshottari
    calls = []
    def observed(conn, chart_id):
        calls.append(chart_id)
        return actual(conn, chart_id)
    monkeypatch.setattr(dasha_read, "load_pinned_vimshottari", observed)
    rows, contract = consumer.load_pinned_dasha_periods(SqlTransport(), CHART, ["vimshottari"])
    assert rows[0]["dasha_row_id"] == ROW and contract["build_id"] == BUILD
    assert calls == [CHART], "class-context bypasses the shared settlement-bound loader (J-4p-owned amendment)"
