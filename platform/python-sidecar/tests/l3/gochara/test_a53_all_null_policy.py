"""A5.3 — Codex round 9, R9-1: 'dynamic disabled' is not 'all NULL'.

Constant objectives and empty for-channel sums are still numeric with the dynamic solver disabled (the reviewer's three
cases). ONE named policy, `all_null_candidate/1`, is selected by the generation's MANIFEST and implemented four times —
the builder (`draft_windows(policy=…)`), the independent verifier, 1240's window CHECK and the candidate gate: EVERY
numerical result field (score, evidence_for, evidence_against, objective_value, severity) NULL for every path and
channel composition, the peak absent, the valence `unqualified`; geometry, supports, identifiers, memberships and the
accounting counts stay populated. `window_qualification/1` stays the policy that applies when numbers are enabled.
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import result_policy as rp
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .test_a53_window_sweep import _d, _draft, _p2, _p2_rows, _rec, _rows_declared

ALL_NULL = rp.POLICY_ALL_NULL
QUAL = rp.POLICY_QUALIFICATION


def _assert_all_null(w):
    assert (w.peak_instant, w.score, w.evidence_for, w.evidence_against, w.severity, w.objective_value) == (
        None, None, None, None, None, None)
    assert w.outcome_valence_for_native == "unqualified"
    assert w.unqualified_reason == rp.ALL_NULL_REASON and w.policy == ALL_NULL
    assert w.qualification()["policy"] == ALL_NULL and w.qualification()["unqualified_reason"] == rp.ALL_NULL_REASON


def _populated(w, *, members):
    """Geometry, identifiers and accounting counts stay populated under the policy."""
    assert w.interval[0] < w.interval[1] and len(w.record_ids) == members and w.members == members


# ── the reviewer's three reproductions: numeric before, all-NULL under the policy ────────────────────

def test_constant_p3_is_numeric_under_qualification_and_all_null_under_the_policy():
    rec = lambda: _rec("A", path="P3", supports=((0, 10),))
    (q,), _ = _draft([rec()], _rows_declared, policy=QUAL)
    assert (q.score, q.evidence_for, q.evidence_against) == (1.0, 1.0, 0.0) and q.objective_value == 1.0   # the defect
    (n,), _ = _draft([rec()], _rows_declared, policy=ALL_NULL)
    _assert_all_null(n)
    _populated(n, members=1)
    assert n.interval == (_d(0), _d(10)) and n.objective == q.objective        # the NAME of the objective is not a number


def test_constant_p4_is_numeric_under_qualification_and_all_null_under_the_policy():
    pair = lambda: [_rec("J", path="P4", agent="jupiter", root="RJ", supports=((0, 10),)),
                    _rec("S", path="P4", agent="saturn", root="RS", supports=((0, 10),))]
    (q,), _ = _draft(pair(), _rows_declared, policy=QUAL)
    assert q.score == 1.0 and q.evidence_for == 2.0 and q.objective_value == 1.0                         # the defect
    (n,), _ = _draft(pair(), _rows_declared, policy=ALL_NULL)
    _assert_all_null(n)
    _populated(n, members=2)


def test_all_against_p2_is_numeric_under_qualification_and_all_null_under_the_policy():
    vedha = lambda rec, t: 1.0
    rec = lambda: [_p2("a", "saturn", 8, supports=((3, 9),))]
    (q,), _ = _draft(rec(), _p2_rows, cls="marriage", vedha=vedha, policy=QUAL)
    assert q.evidence_for == 0.0 and q.peak_instant == _d(3) and q.objective_value == 0.0                # the defect
    (n,), _ = _draft(rec(), _p2_rows, cls="marriage", vedha=vedha, policy=ALL_NULL)
    _assert_all_null(n)
    _populated(n, members=1)


# ── every composition, not three examples ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cls", ["marriage", "bereavement", "career_entry"])
def test_no_composition_stores_a_number_under_the_policy(cls):
    vedha = lambda rec, t: 1.0
    cases = [
        ([_rec("A", path="P3", supports=((0, 10),))], _rows_declared, {}),
        ([_rec("A", path="P3", root="R1", supports=((0, 10),)), _rec("B", path="P3", root="R2", supports=((5, 15),))],
         _rows_declared, {}),
        ([_rec("J", path="P4", agent="jupiter", root="RJ", supports=((0, 10),)),
          _rec("S", path="P4", agent="saturn", root="RS", supports=((0, 10),))], _rows_declared, {}),
        ([_p2("a", "saturn", 8, supports=((3, 9),))], _p2_rows, {"vedha": vedha}),
        ([_p2("a", "jupiter", 5, supports=((3, 9),))], _p2_rows, {"vedha": vedha}),
        ([_p2("a", "saturn", 8, supports=((3, 9),)), _p2("b", "jupiter", 5, supports=((4, 8),))], _p2_rows,
         {"vedha": vedha}),
    ]
    for records, rows, kw in cases:
        drafts, _ = _draft(records, rows, cls=cls, policy=ALL_NULL, **kw)
        assert drafts
        for w in drafts:
            _assert_all_null(w)


def test_accounting_is_unchanged_by_the_policy():
    """The exclusion ledger, the window count and the per-window membership do not depend on the policy."""
    recs = lambda: [_rec("A", root="R1", supports=((0, 10),)), _rec("B", root="R2", supports=((20, 30),)),
                    _rec("T", root="R3", role="testimony", supports=((0, 5),))]
    q_drafts, q_ex = _draft(recs(), _rows_declared, policy=QUAL)
    n_drafts, n_ex = _draft(recs(), _rows_declared, policy=ALL_NULL)
    assert q_ex == n_ex
    assert [(d.interval, d.record_ids, d.members) for d in q_drafts] == [(d.interval, d.record_ids, d.members)
                                                                         for d in n_drafts]


def test_an_unqualified_member_keeps_its_reasons_under_the_policy():
    """The per-member classification still fills `unresolved` — the policy replaces the RESULT, not the audit trail."""
    unq = _rec("u", kind="varga_position", supports=((0, 10),))
    (n,), _ = _draft([unq], _rows_declared, policy=ALL_NULL)
    _assert_all_null(n)
    assert n.unresolved == {"object_kind_not_covered_by_applicability": 1} and n.qualified_members == 0


def test_an_unknown_policy_is_refused_not_defaulted():
    with pytest.raises(ws.SweepRefusal, match="result policy"):
        _draft([_rec("A", supports=((0, 10),))], _rows_declared, policy="all_null")


def test_mutation_a_builder_that_ignores_the_policy_stores_numbers():
    """Remove the policy early-out and the constant P3 window is numeric again — the tests above fail against it."""
    import inspect
    src = inspect.getsource(ws.draft_windows)
    assert "if policy == POLICY_ALL_NULL:" in src


# ── the verifier's OWN literals equal the builder's ──────────────────────────────────────────────────

def test_the_independent_verifier_keeps_its_own_literals_and_they_equal_the_builders():
    assert wv.ALL_NULL_POLICY == rp.POLICY_ALL_NULL and wv.POLICY_VERSION == rp.POLICY_QUALIFICATION
    assert wv.ALL_NULL_REASON == rp.ALL_NULL_REASON and wv.POLICIES == (rp.POLICY_ALL_NULL, rp.POLICY_QUALIFICATION)
    assert rp.RESULT_POLICIES == wv.POLICIES
    assert set(rp.NUMERIC_RESULT_FIELDS) == {"score", "evidence_for", "evidence_against", "objective_value", "severity"}
    import ast
    import inspect
    imported = set()
    for node in ast.walk(ast.parse(inspect.getsource(wv))):
        if isinstance(node, ast.ImportFrom):
            imported.add((node.module or "") + "." + ",".join(a.name for a in node.names))
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert not any("result_policy" in i or "window_sweep" in i for i in imported), imported   # independence
