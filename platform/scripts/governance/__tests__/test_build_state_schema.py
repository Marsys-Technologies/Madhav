"""Build-state contract: current output and retained historical mirror data."""

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/build_state.schema.json"


def current_payload():
    """Small valid snapshot, independent of serializer and schema implementation."""
    return {
        "schema_version": "0.2.0",
        "generated_at": "2026-11-15T00:00:00+00:00",
        "generated_by_session": "BUILD_STATE_CONTRACT_FIXTURE",
        "generator_version": "0.2.0",
        "source_fingerprints": {
            name: "a" * 64 for name in (
                "current_state", "canonical_artifacts", "session_log",
                "ongoing_hygiene_policies",
            )
        },
        "macro_phase": {"id": "M6", "title": "Fixture phase", "status": "active"},
        "phase_plan": {"path": "fixture.md", "version": "1.0", "sub_phase": "A", "status": "active"},
        "governance": {
            "rebuild_status": "closed", "baseline_artifact_path": None,
            "active_step": None, "active_step_status": None, "next_step": None,
            "next_quarterly_pass": None,
            "red_team": {"counter": 0, "threshold": 3, "due": False},
        },
        "last_session": {"id": "FIXTURE", "closed_at": "2026-11-15T00:00:00+00:00"},
        "next_session": {"objective": "Verify schema contract"},
        "native_directives": {"open": [], "addressed": []},
        "canonical_artifacts": [], "recent_sessions": [],
        "disagreement_register": {"open_count": 0, "resolved_count": 0, "entries": []},
        "red_team_passes": [], "staleness_register": [], "sessions_index": [],
        "phases_index": [], "cowork_ledger": [], "workstreams": [],
    }


def legacy_payload():
    payload = current_payload()
    # Historical rows preserve the shape in build_state.example.json (v0.1).
    payload["mirror_pairs"] = [
        {"pair_id": "MP.1", "claude_side": "CLAUDE.md", "gemini_side": ".geminirules",
         "authoritative_side": "claude", "mirror_mode": "adapted_parity"},
        {"pair_id": "MP.6", "claude_side": "00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md",
         "gemini_side": None, "authoritative_side": "claude", "mirror_mode": "claude_only"},
    ]
    return payload


class BuildStateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads(SCHEMA_PATH.read_text())
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema)

    def assert_valid(self, payload):
        self.assertEqual(list(self.validator.iter_errors(payload)), [])

    def assert_single_violation(self, payload, path, rule):
        errors = list(self.validator.iter_errors(payload))
        self.assertEqual(len(errors), 1, [error.message for error in errors])
        self.assertEqual(list(errors[0].absolute_path), path)
        self.assertEqual(errors[0].validator, rule)

    def test_current_snapshot_omits_retired_mirrors(self):
        self.assert_valid(current_payload())

    def test_incoming_phase_needs_no_retired_mirrors(self):
        payload = current_payload()
        payload["macro_phase"]["status"] = "incoming"
        self.assert_valid(payload)

    def test_supported_phase_statuses_preserve_historical_mirrors(self):
        for status in ("incoming", "active", "paused_governance_rebuild", "paused_native_hold", "closed"):
            with self.subTest(status=status):
                payload = legacy_payload()
                payload["macro_phase"]["status"] = status
                self.assert_valid(payload)

    def test_empty_historical_mirror_array_is_valid(self):
        payload = legacy_payload()
        payload["mirror_pairs"] = []
        self.assert_valid(payload)

    def test_all_active_top_level_fields_remain_required(self):
        for field in current_payload():
            with self.subTest(field=field):
                payload = legacy_payload()
                del payload[field]
                self.assert_single_violation(payload, [], "required")

    def test_active_nested_fields_remain_required(self):
        for group in ("source_fingerprints", "macro_phase", "phase_plan", "governance",
                      "last_session", "next_session", "native_directives", "disagreement_register"):
            for field in current_payload()[group]:
                with self.subTest(group=group, field=field):
                    payload = legacy_payload()
                    del payload[group][field]
                    self.assert_single_violation(payload, [group], "required")

    def test_invalid_phase_statuses_are_rejected(self):
        for status in ("unknown", "", "INCOMING", "incoming_typo", None, 1):
            with self.subTest(status=status):
                payload = legacy_payload()
                payload["macro_phase"]["status"] = status
                errors = list(self.validator.iter_errors(payload))
                self.assertTrue(errors)
                self.assertEqual({tuple(error.absolute_path) for error in errors}, {("macro_phase", "status")})

    def test_active_governance_values_remain_constrained(self):
        for field, value, rule in (("counter", -1, "minimum"), ("threshold", 0, "minimum"),
                                   ("due", "false", "type")):
            with self.subTest(field=field):
                payload = legacy_payload()
                payload["governance"]["red_team"][field] = value
                self.assert_single_violation(payload, ["governance", "red_team", field], rule)

    def test_malformed_retained_mirror_data_is_rejected(self):
        for value, path, rule in ((None, ["mirror_pairs"], "type"),
                                  ({}, ["mirror_pairs"], "type"),
                                  (["MP.1"], ["mirror_pairs", 0], "type")):
            with self.subTest(value=value):
                payload = legacy_payload()
                payload["mirror_pairs"] = value
                self.assert_single_violation(payload, path, rule)
        for field in ("pair_id", "mirror_mode", "authoritative_side"):
            with self.subTest(missing=field):
                payload = legacy_payload()
                del payload["mirror_pairs"][0][field]
                self.assert_single_violation(payload, ["mirror_pairs", 0], "required")
        for field, value, rule in (("pair_id", "MP.invalid", "pattern"),
                                   ("mirror_mode", None, "type"),
                                   ("authoritative_side", 1, "type"),
                                   ("days_since_verified", "yesterday", "type")):
            with self.subTest(field=field, value=value):
                payload = legacy_payload()
                payload["mirror_pairs"][0][field] = value
                self.assert_single_violation(payload, ["mirror_pairs", 0, field], rule)
        payload = legacy_payload()
        payload["mirror_pairs"][0]["unexpected"] = True
        self.assert_single_violation(payload, ["mirror_pairs", 0], "additionalProperties")


if __name__ == "__main__":
    unittest.main()
