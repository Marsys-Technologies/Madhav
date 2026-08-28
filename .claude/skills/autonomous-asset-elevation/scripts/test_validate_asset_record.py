#!/usr/bin/env python3
"""Regression tests for Asset Elevation Record validation."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_asset_record import validate


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "valid-frozen-optimized.json"


def frozen_record() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def set_no_rebuild(record: dict, reason: str = "terminal disposition does not own a row build") -> None:
    record["release"].update(
        {
            "rebuild_applicability": "NOT_APPLICABLE",
            "production_rebuild_receipt": None,
            "not_applicable_reason": reason,
        }
    )


def configure_disposition(record: dict, disposition: str) -> None:
    record["disposition"] = disposition
    quality = record["quality"]
    quality.update(
        {
            "change_kind": "DISPOSITION",
            "output_comparison": "NOT_APPLICABLE",
            "performance_gain_ref": None,
            "expected_delta_ref": None,
        }
    )

    if disposition == "OPTIMIZED":
        quality.update(
            {
                "change_kind": "OPTIMIZATION",
                "output_comparison": "EQUIVALENT",
                "performance_gain_ref": "evidence://performance",
            }
        )
    elif disposition == "ENRICHED_CORRECTED":
        quality.update(
            {
                "change_kind": "CORRECTNESS_ENRICHMENT",
                "output_comparison": "EXPECTED_DELTA",
                "expected_delta_ref": "evidence://expected-delta",
            }
        )
    elif disposition == "EXPANDED_ADOPTION":
        quality.update({"change_kind": "ADOPTION", "output_comparison": "EQUIVALENT"})
    elif disposition == "JUSTIFIED_NO_CHANGE":
        quality.update({"change_kind": "NONE", "output_comparison": "EQUIVALENT"})
    elif disposition == "RETAINED_LIMITED_USE":
        quality.update({"change_kind": "NONE", "output_comparison": "EQUIVALENT"})
    elif disposition == "SOURCE_ONLY":
        record["asset_type"] = "SOURCE"
        quality["change_kind"] = "NONE"
        set_no_rebuild(record, "source freshness is verified without a row build")
    elif disposition == "SERVICE_PROBE":
        record["asset_type"] = "PROBE"
        quality["change_kind"] = "NONE"
        set_no_rebuild(record, "probe acceptance uses live behavior, not a row build")
    elif disposition == "PRODUCER_COVERED":
        record["asset_type"] = "PRODUCER_COVERED"
        set_no_rebuild(record, "producer receipt is inherited by this denominator member")
        record["producer_coverage"] = {
            "covered_by_asset_id": "producer_asset",
            "inherited_production_rebuild_receipt": "evidence://producer-rebuild",
            "inherited_acceptance_receipt": "evidence://producer-acceptance",
        }
        quality["result_refs"].append("evidence://producer-rebuild")
        record["evidence"]["references"].append("evidence://producer-acceptance")
    elif disposition in {"MERGED_SPLIT", "RETIRED_SUPERSEDED"}:
        set_no_rebuild(record)


class AssetRecordValidationTests(unittest.TestCase):
    def assert_valid(self, record: dict) -> None:
        self.assertEqual(validate(record), [])

    def assert_invalid_with(self, record: dict, fragment: str) -> None:
        errors = validate(record)
        self.assertTrue(errors, "record unexpectedly validated")
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_known_good_frozen_optimized_fixture(self) -> None:
        self.assert_valid(frozen_record())

    def test_every_terminal_disposition_has_a_valid_form(self) -> None:
        dispositions = (
            "OPTIMIZED",
            "ENRICHED_CORRECTED",
            "EXPANDED_ADOPTION",
            "JUSTIFIED_NO_CHANGE",
            "MERGED_SPLIT",
            "RETAINED_LIMITED_USE",
            "RETIRED_SUPERSEDED",
            "SOURCE_ONLY",
            "SERVICE_PROBE",
            "PRODUCER_COVERED",
        )
        for disposition in dispositions:
            with self.subTest(disposition=disposition):
                record = frozen_record()
                configure_disposition(record, disposition)
                self.assert_valid(record)

    def test_every_lifecycle_state_has_a_valid_form(self) -> None:
        states = (
            "RECONCILED",
            "ELIGIBLE",
            "ANALYZED",
            "OPTIMIZED",
            "INTEGRATED",
            "DEPLOYED",
            "REBUILT_ONCE",
            "INDEPENDENTLY_VERIFIED",
            "FROZEN",
        )
        for state in states:
            with self.subTest(state=state):
                record = frozen_record()
                record["lifecycle_state"] = state
                self.assert_valid(record)

        no_change = frozen_record()
        no_change["lifecycle_state"] = "JUSTIFIED_NO_CHANGE"
        configure_disposition(no_change, "JUSTIFIED_NO_CHANGE")
        self.assert_valid(no_change)

        quarantined = frozen_record()
        quarantined["lifecycle_state"] = "QUARANTINED"
        quarantined["blockers"] = ["external source unavailable"]
        self.assert_valid(quarantined)

    def test_intermediate_states_enforce_their_earned_evidence(self) -> None:
        cases = []

        integrated = frozen_record()
        integrated["lifecycle_state"] = "INTEGRATED"
        integrated["release"]["merge_sha"] = None
        cases.append((integrated, "requires release.merge_sha"))

        deployed = frozen_record()
        deployed["lifecycle_state"] = "DEPLOYED"
        deployed["release"]["production_verified"] = False
        cases.append((deployed, "production_verified=true"))

        rebuilt = frozen_record()
        rebuilt["lifecycle_state"] = "REBUILT_ONCE"
        rebuilt["release"]["production_rebuild_receipt"] = None
        cases.append((rebuilt, "lacks a receipt"))

        independently_verified = frozen_record()
        independently_verified["lifecycle_state"] = "INDEPENDENTLY_VERIFIED"
        independently_verified["evidence"]["independent_verdict"] = "NOT_RUN"
        cases.append((independently_verified, "independent_verdict='ACCEPT'"))

        for record, fragment in cases:
            with self.subTest(state=record["lifecycle_state"]):
                self.assert_invalid_with(record, fragment)

    def test_non_build_terminal_can_skip_rebuild_but_not_verification(self) -> None:
        record = frozen_record()
        configure_disposition(record, "PRODUCER_COVERED")
        self.assert_valid(record)

        missing_reason = copy.deepcopy(record)
        missing_reason["release"]["not_applicable_reason"] = None
        self.assert_invalid_with(missing_reason, "requires a reason")

        missing_verdict = copy.deepcopy(record)
        missing_verdict["evidence"]["independent_verdict"] = "NOT_RUN"
        self.assert_invalid_with(missing_verdict, "independent_verdict='ACCEPT'")

        mismatched_disposition = copy.deepcopy(record)
        mismatched_disposition["disposition"] = "JUSTIFIED_NO_CHANGE"
        mismatched_disposition["quality"].update({"change_kind": "NONE", "output_comparison": "EQUIVALENT"})
        self.assert_invalid_with(mismatched_disposition, "requires the matching disposition")

        missing_producer_receipt = copy.deepcopy(record)
        missing_producer_receipt["producer_coverage"]["inherited_production_rebuild_receipt"] = None
        self.assert_invalid_with(missing_producer_receipt, "inherited producer rebuild receipt")

    def test_schema_rejects_nested_extras_and_wrong_types(self) -> None:
        extra = frozen_record()
        extra["release"]["untracked_receipt"] = "forged"
        self.assert_invalid_with(extra, "unexpected keys")

        wrong_bool = frozen_record()
        wrong_bool["release"]["production_verified"] = 1
        self.assert_invalid_with(wrong_bool, "must have type boolean")

        wrong_ref = frozen_record()
        wrong_ref["evidence"]["references"] = [7]
        self.assert_invalid_with(wrong_ref, "must have type string")

    def test_stale_definition_sha_and_fence_are_rejected(self) -> None:
        cases = []
        definition = frozen_record()
        definition["run_binding"]["definition_digest"] = "definition-old"
        cases.append((definition, "definition does not match"))

        sha = frozen_record()
        sha["run_binding"]["code_sha"] = "older-sha"
        cases.append((sha, "code_sha does not match"))

        fence = frozen_record()
        fence["run_binding"]["lease_fence"] = 2
        cases.append((fence, "lease fence does not match"))

        generation = frozen_record()
        generation["run_binding"]["run_generation"] = 0
        cases.append((generation, "positive run_generation"))

        for record, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assert_invalid_with(record, fragment)

    def test_frozen_requires_protected_acceptance_and_no_blockers(self) -> None:
        record = frozen_record()
        record["evidence"]["protected_terminal_writer"] = False
        record["evidence"]["accepted_receipt"] = None
        record["blockers"] = ["still waiting"]
        errors = validate(record)
        self.assertTrue(any("protected terminal" in error for error in errors), errors)
        self.assertTrue(any("accepted_receipt" in error for error in errors), errors)
        self.assertTrue(any("cannot retain blockers" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
