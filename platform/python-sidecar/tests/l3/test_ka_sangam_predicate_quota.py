"""
Tests for ka_sangam._select_top_predicates_with_class_quota — D-3 FIX-PSEL
(MEMO_D-3_1.md: predicate-selection bug, 100% SUBSYSTEM/Mode-C on chart
482012f1, TRIGGER never exercised).

Covers:
  - Quota floor: a synthetic skew mirroring the real one (SUBSYSTEM vastly
    outnumbering every other class) must NOT produce a 100%-SUBSYSTEM
    selection once every populated class has real predicates.
  - Deterministic content-hash tiebreak: same input predicates (any input
    order) → same selected set, same output order — no dependence on
    insertion order.
  - No systematic class bias from the tiebreak itself (shuffling input order
    does not change which predicates are selected).
  - Edge cases: empty input, limit <= 0, a class with fewer predicates than
    its floor, a single populated class.
"""
from __future__ import annotations

import hashlib
import os
import random
import sys

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from pipeline.orchestrator.writers.ka_sangam import (
    _select_top_predicates_with_class_quota,
    _QUOTA_FLOOR_DIVISOR,
    _QUOTA_FLOOR_MIN,
)


def _hash(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def _make_predicate(signal_id: str, signature_class: str, dignity_score, insertion_id: int) -> dict:
    """Mirrors the shape plan_substeps() builds: signature_class + dignity_score
    + a content_hash derived the same way as the SQL (signal_id|signature_class|
    rule_jsonb). `insertion_id` is carried ONLY so a test can assert the
    selection does NOT depend on it (it must never be read by the selector)."""
    return {
        "id": insertion_id,
        "signal_id": signal_id,
        "signature_class": signature_class,
        "dignity_score": dignity_score,
        "content_hash": _hash(signal_id, signature_class, ""),
    }


def _skewed_fixture():
    """Mirrors the real skew from MEMO_D-3_1.md at reduced scale: one dominant
    SUBSYSTEM class (all tied at the max score, low insertion ids — exactly the
    condition that starved every other class under the old `id ASC` tiebreak)
    plus a handful of predicates in each of the other 5 real signature classes,
    also tied at the max score but with higher insertion ids."""
    preds = []
    insertion_id = 0
    # 100 SUBSYSTEM predicates, all tied at max score, LOWEST ids (the old bug's
    # exact winning condition).
    for i in range(100):
        preds.append(_make_predicate(f"subsys-{i}", "SUBSYSTEM", 1.0, insertion_id))
        insertion_id += 1
    # A handful of each other real class, also tied at the max score, but with
    # HIGHER insertion ids than any SUBSYSTEM row.
    for cls, n in (
        ("DISPOSITOR_RELATIONAL", 6),
        ("DIGNITY", 4),
        ("DOSHA", 5),
        ("YOGA", 2),
        ("CLASSIFY_RESIDUAL", 5),
    ):
        for i in range(n):
            preds.append(_make_predicate(f"{cls.lower()}-{i}", cls, 1.0, insertion_id))
            insertion_id += 1
    return preds


class TestQuotaGivesNonSubsystemRepresentation:
    def test_small_limit_is_not_100_percent_subsystem(self):
        """The regression this lane exists to fix: under the old
        `ORDER BY dignity_score DESC, id ASC LIMIT 20`-style selection, this
        exact fixture (SUBSYSTEM has the lowest ids AND ties at the max score)
        would select 20/20 SUBSYSTEM. The quota selector must not."""
        preds = _skewed_fixture()
        selected = _select_top_predicates_with_class_quota(preds, limit=20)
        assert len(selected) == 20
        classes = {p["signature_class"] for p in selected}
        assert classes != {"SUBSYSTEM"}, "quota selection collapsed to 100% SUBSYSTEM"
        # Every populated class with at least floor_per_class predicates
        # available must be represented.
        non_subsystem = [p for p in selected if p["signature_class"] != "SUBSYSTEM"]
        assert len(non_subsystem) > 0

    def test_every_populated_class_gets_at_least_the_floor(self):
        preds = _skewed_fixture()
        limit = 60  # mirrors the real lifetime-tier LIMIT
        selected = _select_top_predicates_with_class_quota(preds, limit=limit)
        num_classes = len({p["signature_class"] for p in preds})
        expected_floor = max(_QUOTA_FLOOR_MIN, limit // (num_classes * _QUOTA_FLOOR_DIVISOR))
        counts: dict[str, int] = {}
        for p in selected:
            counts[p["signature_class"]] = counts.get(p["signature_class"], 0) + 1
        available = {}
        for p in preds:
            available.setdefault(p["signature_class"], 0)
            available[p["signature_class"]] += 1
        for cls, avail in available.items():
            floor_here = min(expected_floor, avail)
            assert counts.get(cls, 0) >= floor_here, (
                f"class {cls} got {counts.get(cls, 0)} slots, expected >= {floor_here}"
            )

    def test_near_tier_limit_200_still_diversifies(self):
        preds = _skewed_fixture()
        selected = _select_top_predicates_with_class_quota(preds, limit=200)
        # Fixture only has 122 predicates total, so everything is selected —
        # sanity: limit larger than pool returns the whole (deduped) pool.
        assert len(selected) == len(preds)
        classes = {p["signature_class"] for p in selected}
        assert classes == {p["signature_class"] for p in preds}


class TestDeterministicContentHashTiebreak:
    def test_same_input_same_output_repeated_calls(self):
        preds = _skewed_fixture()
        first = _select_top_predicates_with_class_quota(list(preds), limit=20)
        second = _select_top_predicates_with_class_quota(list(preds), limit=20)
        assert [p["content_hash"] for p in first] == [p["content_hash"] for p in second]

    def test_selection_independent_of_input_order(self):
        """Shuffling the input list must not change which predicates are
        selected (only insertion-order tiebreaks are order-sensitive; a
        content-hash tiebreak is not)."""
        preds = _skewed_fixture()
        selected_a = _select_top_predicates_with_class_quota(list(preds), limit=20)

        shuffled = list(preds)
        random.Random(42).shuffle(shuffled)
        selected_b = _select_top_predicates_with_class_quota(shuffled, limit=20)

        hashes_a = sorted(p["content_hash"] for p in selected_a)
        hashes_b = sorted(p["content_hash"] for p in selected_b)
        assert hashes_a == hashes_b, "selection changed when only input order changed"

    def test_insertion_id_never_used_as_tiebreak(self):
        """Two predicates identical in every scored field except insertion id
        must be an arbitrary-but-STABLE choice driven by content_hash, not by
        which one has the lower id. Construct a case where the LOWER-id row
        has the LEXICOGRAPHICALLY LARGER content_hash and assert the
        higher-id/lexicographically-smaller-hash row wins the single slot."""
        a = {"id": 1, "signal_id": "a", "signature_class": "SUBSYSTEM",
             "dignity_score": 1.0, "content_hash": "zzzz"}
        b = {"id": 2, "signal_id": "b", "signature_class": "SUBSYSTEM",
             "dignity_score": 1.0, "content_hash": "aaaa"}
        selected = _select_top_predicates_with_class_quota([a, b], limit=1)
        assert len(selected) == 1
        assert selected[0]["content_hash"] == "aaaa", (
            "tiebreak picked by insertion id, not content_hash"
        )


class TestEdgeCases:
    def test_empty_input(self):
        assert _select_top_predicates_with_class_quota([], limit=200) == []

    def test_limit_zero_or_negative(self):
        preds = _skewed_fixture()
        assert _select_top_predicates_with_class_quota(preds, limit=0) == []
        assert _select_top_predicates_with_class_quota(preds, limit=-5) == []

    def test_single_populated_class(self):
        preds = [_make_predicate(f"s{i}", "SUBSYSTEM", 1.0, i) for i in range(10)]
        selected = _select_top_predicates_with_class_quota(preds, limit=5)
        assert len(selected) == 5
        assert {p["signature_class"] for p in selected} == {"SUBSYSTEM"}

    def test_class_with_fewer_predicates_than_floor_takes_all_it_has(self):
        preds = _skewed_fixture()  # YOGA only has 2 predicates
        selected = _select_top_predicates_with_class_quota(preds, limit=60)
        yoga_selected = [p for p in selected if p["signature_class"] == "YOGA"]
        assert len(yoga_selected) == 2, "a starved class should contribute all it has, not error"

    def test_none_dignity_score_sorts_last_but_is_still_selectable(self):
        preds = [
            _make_predicate("a", "SUBSYSTEM", None, 0),
            _make_predicate("b", "SUBSYSTEM", 0.5, 1),
        ]
        selected = _select_top_predicates_with_class_quota(preds, limit=2)
        assert len(selected) == 2
        assert selected[0]["signal_id"] == "b"  # scored row ranks ahead of None
        assert selected[1]["signal_id"] == "a"

    def test_result_never_exceeds_limit(self):
        preds = _skewed_fixture()
        for limit in (1, 5, 20, 60, 200, 1000):
            selected = _select_top_predicates_with_class_quota(preds, limit=limit)
            assert len(selected) <= limit
            assert len(selected) <= len(preds)

    def test_no_duplicate_predicates_in_selection(self):
        preds = _skewed_fixture()
        selected = _select_top_predicates_with_class_quota(preds, limit=60)
        hashes = [p["content_hash"] for p in selected]
        assert len(hashes) == len(set(hashes)), "quota floor and fill phases selected overlapping rows"
