"""
test_mi_pariksha_retrodiction_disclosure.py — F-148 pt.1 write-path cover.

`_substep_retrodiction`'s docstring and row `statement` were already honest (F-143):
the declared T-90d cutoff is never applied as a filter, window containment is never
checked, and event_type is never compared. But the row's NUMERIC fields still read
as earned evidence to a caller who does not read the prose:

  - `n_support` / `strength` look like a measured match count / measured posterior.
  - `evidence_refs` (`top_k_json`) carried, per anchor, a `rank_credit` field named
    like an NDCG relevance credit for a hit nothing adjudicated.

These tests pin the F-148 pt.1 fix: `evidence_refs` becomes a dict (not a bare list)
carrying explicit disclosure flags (`cutoff_enforced`, `window_containment_checked`,
`event_type_compared`, `n_adjudicated_hits`) plus an `n_support_semantics` string, and
the misleading `rank_credit` name is retired in favour of `rank_position_weight`.
"""
from __future__ import annotations

import json
from datetime import date

from pipeline.orchestrator.writers.mi_pariksha import MiParikshaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "FROM mimamsa_event_provenance" in s:
            self._result = list(self._conn.events)
        elif "information_schema.tables" in s:
            self._result = [(1,)] if self._conn.phala_anchors_table_exists else []
        elif "FROM phala_anchors" in s:
            domain = params[1] if params else None
            self._result = [a for a in self._conn.phala_anchors if a["domain"] == domain]
        elif s.startswith("DELETE"):
            self._result = []
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_discoveries" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, events, phala_anchors=None, phala_anchors_table_exists=True):
        self.events = list(events)
        self.phala_anchors = list(phala_anchors or [])
        self.phala_anchors_table_exists = phala_anchors_table_exists
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def _event(event_id="ev1", domain="career"):
    return {
        "event_id": event_id,
        "event_date": date(2024, 1, 1),
        "domain_primary": domain,
        "event_class_id": "ec1",
        "event_magnitude": 0.5,
    }


def _anchor(anchor_id, domain="career", posterior=0.7, window_start="2023-06-01"):
    return {
        "anchor_id": anchor_id,
        "domain": domain,
        "event_type": "promotion",
        "posterior": posterior,
        "magnitude": 0.5,
        "window_start": window_start,
        "window_end": "2024-06-01",
        "lift_vector_jsonb": {},
    }


def _run(events, phala_anchors=None, phala_anchors_table_exists=True):
    conn = _FakeConn(events, phala_anchors, phala_anchors_table_exists)
    writer = MiParikshaWriter()
    result = writer._substep_retrodiction(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


# Insert-tuple offsets mirror the INSERT column list in _substep_retrodiction.
STATEMENT, EVIDENCE_REFS, STRENGTH, N_SUPPORT = 3, 4, 5, 6


def _refs(row):
    return json.loads(row[EVIDENCE_REFS])


def test_evidence_refs_is_a_dict_not_a_bare_list():
    """Pre-F-148, evidence_refs for a retrodiction row was `json.dumps([...])` — a
    bare array with nowhere to carry a disclosure flag. It must now be a dict."""
    conn, result = _run(
        [_event()],
        phala_anchors=[_anchor("a1"), _anchor("a2", posterior=0.6)],
    )
    assert result.rows_inserted == 1
    refs = _refs(conn.inserted_rows[0])
    assert isinstance(refs, dict)
    assert isinstance(refs["top_k"], list)
    assert len(refs["top_k"]) == 2


def test_disclosure_flags_are_explicit_false_and_null_not_omitted():
    """The three unenforced checks must be recorded as explicit `false`, and the
    unmeasured adjudicated-hit count as explicit `null` — never simply absent,
    which a caller could mistake for 'not applicable' rather than 'not done'."""
    conn, _ = _run([_event()], phala_anchors=[_anchor("a1")])
    refs = _refs(conn.inserted_rows[0])
    assert refs["cutoff_enforced"] is False
    assert refs["window_containment_checked"] is False
    assert refs["event_type_compared"] is False
    assert refs["n_adjudicated_hits"] is None


def test_disclosure_flags_present_even_with_zero_anchor_matches():
    """The honesty carrier must not depend on there being a match to disclose
    about — an empty top_k is exactly when a caller most needs the semantics."""
    conn, _ = _run([_event()], phala_anchors=[])
    row = conn.inserted_rows[0]
    assert row[N_SUPPORT] == 0
    refs = _refs(row)
    assert refs["top_k"] == []
    assert refs["cutoff_enforced"] is False
    assert refs["window_containment_checked"] is False
    assert refs["event_type_compared"] is False
    assert refs["n_adjudicated_hits"] is None
    assert "n_support_semantics" in refs


def test_caller_reading_only_n_support_has_semantics_alongside():
    """The whole point of F-148 pt.1: a caller must not be able to read n_support
    in isolation without the semantics string sitting right next to it in the
    same served row."""
    conn, _ = _run([_event()], phala_anchors=[_anchor("a1"), _anchor("a2")])
    row = conn.inserted_rows[0]
    n_support_value = row[N_SUPPORT]
    refs = _refs(row)
    assert n_support_value == 2
    assert "n_support_semantics" in refs
    semantics = refs["n_support_semantics"]
    assert "window containment" in semantics
    assert "event_type" in semantics
    assert "NOT verified" in semantics
    assert "not an adjudicated hit" in semantics


def test_rank_credit_renamed_rank_position_weight():
    """`rank_credit` named an NDCG-style RELEVANCE credit for a match nothing has
    adjudicated — an invented judgment (§N.7 item 6). It must not appear under
    its old name; the renamed field keeps the same numeric weight."""
    conn, _ = _run([_event()], phala_anchors=[_anchor("a1"), _anchor("a2")])
    refs = _refs(conn.inserted_rows[0])
    for entry in refs["top_k"]:
        assert "rank_credit" not in entry
        assert "rank_position_weight" in entry
    # unchanged positional weighting: 1/log2(rank+1)
    assert refs["top_k"][0]["rank_position_weight"] == 1.0
    import math
    assert refs["top_k"][1]["rank_position_weight"] == round(1.0 / math.log2(3), 4)


def test_statement_and_evidence_refs_agree_nothing_was_verified():
    """The prose (already honest since F-143) and the numeric disclosure flags
    (new in F-148 pt.1) must never disagree about what ran."""
    conn, _ = _run([_event()], phala_anchors=[_anchor("a1")])
    row = conn.inserted_rows[0]
    statement = row[STATEMENT]
    refs = _refs(row)
    assert "not applied" in statement
    assert "not an adjudicated hit" in statement
    assert refs["cutoff_enforced"] is False


def test_no_admissible_events_yields_zero_rows():
    conn, result = _run([])
    assert result.rows_inserted == 0
    assert conn.inserted_rows == []
