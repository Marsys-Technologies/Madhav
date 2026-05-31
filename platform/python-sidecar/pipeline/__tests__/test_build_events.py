"""
test_build_events.py — Unit tests for build_events emitter module.
Uses unittest.mock to avoid real DB connections.
≥ 20 assertions covering all three public functions.
"""
import json
import unittest
from unittest.mock import MagicMock, call, patch

from pipeline.build_events import emit_event, emit_step_event, format_sse_row, emit_node_added, emit_edge_added


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_conn(fetchone_return=None):
    """Return a mock psycopg2-style connection."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    if fetchone_return is not None:
        cursor.fetchone.return_value = fetchone_return
    return conn, cursor


# ─────────────────────────────────────────────────────────────────────────────
# emit_event tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitEvent(unittest.TestCase):

    def test_returns_notif_id_string(self):
        """emit_event returns notif_id as a string when INSERT succeeds."""
        fake_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        result = emit_event(conn, build_id="build-1", event_type="build_started")

        self.assertEqual(result, fake_uuid)  # assertion 1
        self.assertIsInstance(result, str)   # assertion 2

    def test_returns_none_when_fetchone_is_none(self):
        """emit_event returns None when cursor.fetchone() returns None."""
        conn, cursor = _make_conn(fetchone_return=None)
        cursor.fetchone.return_value = None

        result = emit_event(conn, build_id="build-2", event_type="build_queued")

        self.assertIsNone(result)  # assertion 3

    def test_inserts_into_build_notifications(self):
        """emit_event calls INSERT into build_notifications with correct event_type."""
        fake_uuid = "00000000-0000-0000-0000-000000000001"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(conn, build_id="build-3", event_type="step_started")

        cursor.execute.assert_called_once()  # assertion 4
        call_args = cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        self.assertIn("build_notifications", sql)  # assertion 5
        self.assertEqual(params[1], "step_started")  # assertion 6

    def test_payload_contains_required_fields(self):
        """emit_event payload has type, build_id, and timestamp fields."""
        fake_uuid = "00000000-0000-0000-0000-000000000002"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(conn, build_id="build-4", event_type="build_complete")

        call_args = cursor.execute.call_args
        params = call_args[0][1]
        payload = json.loads(params[2])

        self.assertIn("type", payload)       # assertion 7
        self.assertIn("build_id", payload)   # assertion 8
        self.assertIn("timestamp", payload)  # assertion 9
        self.assertEqual(payload["type"], "build_complete")    # assertion 10
        self.assertEqual(payload["build_id"], "build-4")       # assertion 11

    def test_payload_contains_optional_fields(self):
        """emit_event payload includes asset_id, ayanamsha_id, stage, status."""
        fake_uuid = "00000000-0000-0000-0000-000000000003"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(
            conn,
            build_id="build-5",
            event_type="step_complete",
            asset_id="A3_chart_facts",
            ayanamsha_id="lahiri",
            stage="persist",
            status="complete",
            rows_written=42,
        )

        call_args = cursor.execute.call_args
        payload = json.loads(call_args[0][1][2])

        self.assertEqual(payload["asset_id"], "A3_chart_facts")  # assertion 12
        self.assertEqual(payload["ayanamsha_id"], "lahiri")       # assertion 13
        self.assertEqual(payload["stage"], "persist")             # assertion 14
        self.assertEqual(payload["rows_written"], 42)             # assertion 15

    def test_extra_fields_appear_in_payload(self):
        """Extra kwargs passed to emit_event appear in the serialised payload."""
        fake_uuid = "00000000-0000-0000-0000-000000000004"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(
            conn,
            build_id="build-6",
            event_type="build_started",
            extra={"custom_key": "custom_value", "run_index": 7},
        )

        call_args = cursor.execute.call_args
        payload = json.loads(call_args[0][1][2])

        self.assertEqual(payload["custom_key"], "custom_value")  # assertion 16
        self.assertEqual(payload["run_index"], 7)                # assertion 17

    def test_non_fatal_on_db_failure(self):
        """emit_event swallows DB exceptions and returns None (non-fatal)."""
        conn = MagicMock()
        conn.cursor.side_effect = Exception("DB connection lost")

        # Must not raise
        result = emit_event(conn, build_id="build-7", event_type="build_failed")

        self.assertIsNone(result)  # assertion 18
        conn.rollback.assert_called_once()  # assertion 19

    def test_commit_called_on_success(self):
        """emit_event calls conn.commit() after a successful insert."""
        fake_uuid = "00000000-0000-0000-0000-000000000005"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(conn, build_id="build-8", event_type="build_queued")

        conn.commit.assert_called_once()  # assertion 20

    def test_payload_json_is_valid(self):
        """Payload stored in DB is valid JSON (json.loads does not raise)."""
        fake_uuid = "00000000-0000-0000-0000-000000000006"
        conn, cursor = _make_conn(fetchone_return=(fake_uuid,))

        emit_event(conn, build_id="build-9", event_type="step_failed", error="timeout")

        call_args = cursor.execute.call_args
        payload_str = call_args[0][1][2]
        # Should not raise
        parsed = json.loads(payload_str)
        self.assertEqual(parsed["error"], "timeout")  # assertion 21


# ─────────────────────────────────────────────────────────────────────────────
# emit_step_event tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitStepEvent(unittest.TestCase):

    def _call_step(self, status, rows_written=0, error=None):
        conn, cursor = _make_conn()
        emit_step_event(
            conn,
            build_id="build-10",
            asset_id="A3_chart_facts",
            ayanamsha_id="lahiri",
            stage="persist",
            status=status,
            rows_written=rows_written,
            error=error,
        )
        return conn, cursor

    def test_started_sets_status_running(self):
        """emit_step_event status='started' issues UPDATE to set status='running'."""
        conn, cursor = self._call_step("started")

        # First execute call should be the UPDATE
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        self.assertIn("running", first_call_sql)  # assertion 22

    def test_started_sets_started_at(self):
        """emit_step_event status='started' sets started_at=NOW()."""
        conn, cursor = self._call_step("started")
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        self.assertIn("started_at", first_call_sql)  # assertion 23

    def test_complete_sets_row_count(self):
        """emit_step_event status='complete' sets row_count in build_steps."""
        conn, cursor = self._call_step("complete", rows_written=500)
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        first_call_params = cursor.execute.call_args_list[0][0][1]
        self.assertIn("row_count", first_call_sql)       # assertion 24
        self.assertIn(500, first_call_params)            # assertion 25

    def test_complete_sets_completed_at(self):
        """emit_step_event status='complete' sets completed_at=NOW()."""
        conn, cursor = self._call_step("complete")
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        self.assertIn("completed_at", first_call_sql)  # assertion 26

    def test_failed_sets_error_msg(self):
        """emit_step_event status='failed' sets error_msg column."""
        conn, cursor = self._call_step("failed", error="engine_timeout")
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        first_call_params = cursor.execute.call_args_list[0][0][1]
        self.assertIn("error_msg", first_call_sql)             # assertion 27
        self.assertIn("engine_timeout", first_call_params)     # assertion 28

    def test_failed_sets_completed_at(self):
        """emit_step_event status='failed' sets completed_at=NOW()."""
        conn, cursor = self._call_step("failed")
        first_call_sql = cursor.execute.call_args_list[0][0][0]
        self.assertIn("completed_at", first_call_sql)  # assertion 29

    def test_started_maps_to_step_started_event(self):
        """status='started' inserts event_type='step_started' into notifications."""
        conn, cursor = self._call_step("started")
        # Second execute is the INSERT into build_notifications
        notif_call_params = cursor.execute.call_args_list[1][0][1]
        self.assertEqual(notif_call_params[1], "step_started")  # assertion 30

    def test_complete_maps_to_step_complete_event(self):
        """status='complete' inserts event_type='step_complete' into notifications."""
        conn, cursor = self._call_step("complete")
        notif_call_params = cursor.execute.call_args_list[1][0][1]
        self.assertEqual(notif_call_params[1], "step_complete")  # assertion 31

    def test_failed_maps_to_step_failed_event(self):
        """status='failed' inserts event_type='step_failed' into notifications."""
        conn, cursor = self._call_step("failed")
        notif_call_params = cursor.execute.call_args_list[1][0][1]
        self.assertEqual(notif_call_params[1], "step_failed")  # assertion 32

    def test_notification_payload_contains_correct_fields(self):
        """Notification payload for a step event contains expected fields."""
        conn, cursor = self._call_step("complete", rows_written=99)
        notif_call_params = cursor.execute.call_args_list[1][0][1]
        payload = json.loads(notif_call_params[2])

        self.assertEqual(payload["type"], "step_complete")        # assertion 33
        self.assertEqual(payload["asset_id"], "A3_chart_facts")   # assertion 34
        self.assertEqual(payload["ayanamsha_id"], "lahiri")       # assertion 35
        self.assertEqual(payload["rows_written"], 99)             # assertion 36

    def test_non_fatal_on_db_failure(self):
        """emit_step_event swallows DB exceptions (non-fatal)."""
        conn = MagicMock()
        conn.cursor.side_effect = Exception("timeout")

        # Must not raise
        emit_step_event(
            conn, "build-11", "A1_engine", "kp", "compute", "started"
        )
        conn.rollback.assert_called_once()  # assertion 37

    def test_commit_called_on_success(self):
        """emit_step_event commits the transaction on success."""
        conn, cursor = self._call_step("complete")
        conn.commit.assert_called_once()  # assertion 38


# ─────────────────────────────────────────────────────────────────────────────
# format_sse_row tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatSseRow(unittest.TestCase):

    def test_starts_with_id_field(self):
        """SSE row begins with 'id: <notif_id>'."""
        result = format_sse_row("abc-123", "step_complete", {"type": "step_complete"})
        self.assertTrue(result.startswith("id: abc-123\n"))  # assertion 39

    def test_contains_event_field(self):
        """SSE row contains 'event: <event_type>' line."""
        result = format_sse_row("abc-123", "build_started", {})
        self.assertIn("event: build_started\n", result)  # assertion 40

    def test_contains_data_field(self):
        """SSE row contains a 'data: ' line with JSON."""
        payload = {"type": "build_started", "build_id": "b1"}
        result = format_sse_row("abc-123", "build_started", payload)
        self.assertIn("data: ", result)  # assertion 41

    def test_ends_with_double_newline(self):
        """SSE row ends with the required double newline separator."""
        result = format_sse_row("abc-123", "step_failed", {})
        self.assertTrue(result.endswith("\n\n"))  # assertion 42

    def test_data_is_valid_json(self):
        """The data field in the SSE row is valid JSON."""
        payload = {"type": "step_complete", "rows_written": 77}
        result = format_sse_row("some-id", "step_complete", payload)
        # Extract the data line
        data_line = [l for l in result.splitlines() if l.startswith("data: ")][0]
        parsed = json.loads(data_line[len("data: "):])
        self.assertEqual(parsed["rows_written"], 77)  # assertion 43

    def test_sse_field_order(self):
        """SSE row has fields in order: id, event, data."""
        result = format_sse_row("id-001", "build_complete", {"x": 1})
        lines = result.strip().split("\n")
        self.assertTrue(lines[0].startswith("id:"))      # assertion 44
        self.assertTrue(lines[1].startswith("event:"))   # assertion 45
        self.assertTrue(lines[2].startswith("data:"))    # assertion 46

    def test_payload_preserved_in_data(self):
        """All payload keys survive round-trip through format_sse_row."""
        payload = {
            "type": "build_failed",
            "build_id": "b-999",
            "error": "oom_killed",
        }
        result = format_sse_row("x-id", "build_failed", payload)
        data_line = [l for l in result.splitlines() if l.startswith("data: ")][0]
        parsed = json.loads(data_line[len("data: "):])
        self.assertEqual(parsed["error"], "oom_killed")    # assertion 47
        self.assertEqual(parsed["build_id"], "b-999")      # assertion 48


# ─────────────────────────────────────────────────────────────────────────────
# emit_node_added tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitNodeAdded(unittest.TestCase):

    def _call_node(self, **kwargs):
        conn, cursor = _make_conn(fetchone_return=("notif-node-1",))
        defaults = dict(
            conn=conn,
            build_id="build-node-1",
            chart_id="chart-abc",
            asset_id="A3_chart_facts",
            ayanamsha_id="lahiri",
            row_count=100,
            layer="synthesis",
        )
        defaults.update(kwargs)
        result = emit_node_added(**defaults)
        return result, conn, cursor

    def test_node_added_returns_notif_id(self):
        """emit_node_added returns notif_id on success."""
        result, _, _ = self._call_node()
        self.assertEqual(result, "notif-node-1")  # assertion 49

    def test_node_added_inserts_build_notifications(self):
        """emit_node_added inserts into build_notifications with event_type='node_added'."""
        _, conn, cursor = self._call_node()
        call_args = cursor.execute.call_args
        params = call_args[0][1]
        self.assertEqual(params[1], "node_added")  # assertion 50

    def test_node_added_payload_has_graphnode_fields(self):
        """emit_node_added payload includes FE-required GraphNode fields."""
        _, conn, cursor = self._call_node()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertIn("id", payload)       # assertion 51
        self.assertIn("label", payload)    # assertion 52
        self.assertIn("assetId", payload)  # assertion 53
        self.assertIn("status", payload)   # assertion 54
        self.assertIn("layer", payload)    # assertion 55

    def test_node_added_payload_id_format(self):
        """emit_node_added payload id is '<asset_id>:<ayanamsha_id>'."""
        _, conn, cursor = self._call_node()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertEqual(payload["id"], "A3_chart_facts:lahiri")  # assertion 56

    def test_node_added_payload_status_running(self):
        """emit_node_added payload status is 'running'."""
        _, conn, cursor = self._call_node()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertEqual(payload["status"], "running")  # assertion 57

    def test_node_added_non_fatal_on_db_failure(self):
        """emit_node_added swallows DB exceptions (non-fatal)."""
        conn = MagicMock()
        conn.cursor.side_effect = Exception("DB error")
        result = emit_node_added(
            conn, "build-x", "chart-x", "A1", "kp", 0, "layer1"
        )
        self.assertIsNone(result)  # assertion 58
        conn.rollback.assert_called_once()  # assertion 59


# ─────────────────────────────────────────────────────────────────────────────
# emit_edge_added tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitEdgeAdded(unittest.TestCase):

    def _call_edge(self, **kwargs):
        conn, cursor = _make_conn(fetchone_return=("notif-edge-1",))
        defaults = dict(
            conn=conn,
            build_id="build-edge-1",
            chart_id="chart-abc",
            from_asset="A1_engine",
            to_asset="A3_chart_facts",
            edge_kind="data_flow",
        )
        defaults.update(kwargs)
        result = emit_edge_added(**defaults)
        return result, conn, cursor

    def test_edge_added_returns_notif_id(self):
        """emit_edge_added returns notif_id on success."""
        result, _, _ = self._call_edge()
        self.assertEqual(result, "notif-edge-1")  # assertion 60

    def test_edge_added_inserts_build_notifications(self):
        """emit_edge_added inserts into build_notifications with event_type='edge_added'."""
        _, conn, cursor = self._call_edge()
        params = cursor.execute.call_args[0][1]
        self.assertEqual(params[1], "edge_added")  # assertion 61

    def test_edge_added_payload_has_graphedge_fields(self):
        """emit_edge_added payload includes FE-required GraphEdge fields."""
        _, conn, cursor = self._call_edge()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertIn("source", payload)  # assertion 62
        self.assertIn("target", payload)  # assertion 63
        self.assertIn("type", payload)    # assertion 64

    def test_edge_added_payload_source_target(self):
        """emit_edge_added payload source/target match from_asset/to_asset."""
        _, conn, cursor = self._call_edge()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertEqual(payload["source"], "A1_engine")       # assertion 65
        self.assertEqual(payload["target"], "A3_chart_facts")  # assertion 66

    def test_edge_added_payload_type(self):
        """emit_edge_added payload type matches edge_kind."""
        _, conn, cursor = self._call_edge()
        payload = json.loads(cursor.execute.call_args[0][1][2])
        self.assertEqual(payload["type"], "data_flow")  # assertion 67

    def test_edge_added_non_fatal_on_db_failure(self):
        """emit_edge_added swallows DB exceptions (non-fatal)."""
        conn = MagicMock()
        conn.cursor.side_effect = Exception("DB error")
        result = emit_edge_added(conn, "build-y", "chart-y", "A1", "A3", "dep")
        self.assertIsNone(result)  # assertion 68
        conn.rollback.assert_called_once()  # assertion 69


if __name__ == "__main__":
    unittest.main()
