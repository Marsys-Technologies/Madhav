"""A58 — honest-tier readers (steward M20261002T094420-d113).

A base-layer rebuild relabels MUDDA / NARAYANA daśā rows to the tier they
honestly earn. The pinned `two_pass_verified` read of the non-pinned DR-14
systems would then come back EMPTY and the plurality would report those
systems INACTIVE — a silent omission that reads as a finding. The reader now
accepts any honestly emitted COMPUTED tier for the systems that only vote, and
still refuses floored / divergent / pending / unknown / NULL; the accepted
tier is carried to the permission detail (never implied verified). The
vimshottari §4.0 read (the '5.0' writer's contract, AM-10, the build pin)
stays STRICT.

Pure stub-conn plumbing: no Swiss, no real DB. The stub conn EVALUATES the
tier predicate it is handed, so a reader that stops sending the policy fails.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from brahmagyan import verification_vocab as V  # noqa: E402
from services.gochara_grammar import dasha_data as DD  # noqa: E402
from services.gochara_grammar import read_tier_policy as RTP  # noqa: E402
from services.gochara_intensity import permission as perm  # noqa: E402

STEP06A = (Path(__file__).resolve().parents[3]
           / "scripts" / "kala_gochara_cutover" / "step06a_class_context.py")

BUILD = "b-vim"


def _row(rid, system, tier, level=1, parent=None, lord="Jupiter",
         start="2020-01-01T00:00:00+00:00", end="2030-01-01T00:00:00+00:00",
         build=BUILD):
    return [rid, system, level, parent, lord, start, end, build, tier]


class _Conn:
    """Applies the reader's tier predicate (equality param or ANY(list)) and
    the system filter to its rows — the DB's job, emulated."""

    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        _chart, _ayan, systems, levels, tier_param = params[:5]
        accepted = (set(tier_param) if "ANY(%s)\n" in sql.split(
            "verification_pass_status =")[1][:20] + "\n" else {tier_param})
        keep = [r for r in self.rows
                if r[1] in systems and r[2] in levels and r[8] in accepted]
        if len(params) > 5:
            keep = [r for r in keep if r[7] == params[5]]

        class _X:
            def fetchall(_s):
                return keep
        return _X()


def _load_step06a():
    spec = importlib.util.spec_from_file_location("step06a_a58", STEP06A)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── the policy itself ───────────────────────────────────────────────────────

def test_policy_accepts_exactly_the_honest_computed_tiers_and_refuses_the_rest():
    expected = {V.TWO_PASS_VERIFIED, V.CLASSICAL_MATCH, V.SINGLE, V.SINGLE_PASS,
                V.DOCUMENTED_APPROXIMATION, V.COMPUTED_EXTENSION}
    assert RTP.HONEST_COMPUTED_TIERS == frozenset(expected)
    assert RTP.STRICT_TIERS == frozenset({V.TWO_PASS_VERIFIED})
    for status in sorted(V.ALL_STATUSES):
        assert RTP.tier_accepted(status) is (status in expected), status
    for refused in (V.DIVERGENT_FLAGGED, "floored", "pending_w3_verification",
                    "not_defined_for_nodes", "scope_cap_sentinel",
                    "skipped_malformed_source", "external_computation_required"):
        assert not RTP.tier_accepted(refused)
    # NULL, bare pass, case variants and unknown spellings are never accepted
    for bad in (None, "", "pass", "PASS", "Two_Pass_Verified", "verified", 3):
        assert not RTP.tier_accepted(bad), bad


def test_names_are_the_vocabulary_constants_not_new_members():
    for name in (V.SINGLE, V.SINGLE_PASS, V.DOCUMENTED_APPROXIMATION,
                 V.COMPUTED_EXTENSION, V.CLASSICAL_MATCH, V.TWO_PASS_VERIFIED):
        assert name in V.ALL_STATUSES


def test_tier_evidence_never_calls_an_unverified_tier_verified():
    assert RTP.tier_evidence(V.TWO_PASS_VERIFIED)["tier_verified"] is True
    for t in sorted(RTP.HONEST_COMPUTED_TIERS - {V.TWO_PASS_VERIFIED}):
        ev = RTP.tier_evidence(t)
        assert ev == {"verification_pass_status": t, "tier_verified": False}


# ── behaviour-neutral on today's rows ───────────────────────────────────────

def _today():
    T = V.TWO_PASS_VERIFIED
    return [_row("v1", "vimshottari", T), _row("m1", "mudda", T, lord="Mars"),
            _row("n1", "narayana", T, lord="Taurus")]


def test_on_todays_all_two_pass_rows_the_policy_read_equals_the_strict_read():
    strict = DD.fetch_dasha_periods_multilevel(
        _Conn(_today()), "c", systems=["mudda", "narayana"])
    policy = DD.fetch_dasha_periods_multilevel(
        _Conn(_today()), "c", systems=["mudda", "narayana"],
        accept_tiers=RTP.HONEST_COMPUTED_TIERS)
    assert strict and strict == policy


def test_default_read_stays_strict_equality_on_the_contract_tier():
    conn = _Conn(_today())
    DD.fetch_dasha_periods_multilevel(conn, "c", systems=["vimshottari"])
    sql, params = conn.calls[0]
    assert "verification_pass_status = %s" in sql and "ANY(%s)\n" not in sql.split(
        "verification_pass_status =")[1][:20] + "\n"
    assert params[4] == DD.READ_CONTRACT_TIER == V.TWO_PASS_VERIFIED


# ── after the relabel ───────────────────────────────────────────────────────

def _relabelled():
    return [
        _row("v1", "vimshottari", V.TWO_PASS_VERIFIED),
        _row("m1", "mudda", V.CLASSICAL_MATCH, lord="Mars"),
        _row("n1", "narayana", V.SINGLE, lord="Taurus"),
    ]


def test_strict_read_comes_back_empty_for_relabelled_systems_the_defect():
    assert DD.fetch_dasha_periods_multilevel(
        _Conn(_relabelled()), "c", systems=["mudda", "narayana"]) == []


def test_policy_read_returns_relabelled_rows_each_carrying_its_own_tier():
    out = DD.fetch_dasha_periods_multilevel(
        _Conn(_relabelled()), "c", systems=["mudda", "narayana"],
        accept_tiers=RTP.HONEST_COMPUTED_TIERS)
    assert {r["system_id"]: r["verification_pass_status"] for r in out} == {
        "mudda": V.CLASSICAL_MATCH, "narayana": V.SINGLE}


@pytest.mark.parametrize("refused", [
    V.DIVERGENT_FLAGGED, "floored", "pending_w3_verification",
    "external_computation_required", None, "PASS", "made_up_tier"])
def test_policy_read_still_refuses_floored_divergent_pending_unknown_null(refused):
    rows = [_row("m1", "mudda", refused, lord="Mars")]
    assert DD.fetch_dasha_periods_multilevel(
        _Conn(rows), "c", systems=["mudda"],
        accept_tiers=RTP.HONEST_COMPUTED_TIERS) == []


def test_backstop_drops_a_row_that_escapes_the_predicate():
    class _Leaky(_Conn):
        def execute(self, sql, params):
            self.calls.append((sql, params))
            rows = self.rows

            class _X:
                def fetchall(_s):
                    return rows
            return _X()
    rows = [_row("m1", "mudda", V.DIVERGENT_FLAGGED), _row("m2", "mudda", V.SINGLE,
            start="2031-01-01T00:00:00+00:00", end="2032-01-01T00:00:00+00:00")]
    out = DD.fetch_dasha_periods_multilevel(
        _Leaky(rows), "c", systems=["mudda"], accept_tiers=RTP.HONEST_COMPUTED_TIERS)
    assert [r["dasha_row_id"] for r in out] == ["m2"]


# ── step06a: vimshottari strict, the voting systems honest ──────────────────

def test_step06a_pinned_read_keeps_vimshottari_strict_and_reads_relabelled_others():
    mod = _load_step06a()
    rows = _relabelled() + [
        # a vimshottari row at an honest-but-unverified tier must NOT enter
        _row("v2", "vimshottari", V.CLASSICAL_MATCH, lord="Saturn", build="b-other")]
    periods, contract = mod.load_pinned_dasha_periods(
        _Conn(rows), "not-the-canonical-chart", ["vimshottari", "mudda", "narayana"])
    by = {(p["system_id"], p["dasha_row_id"]): p["verification_pass_status"]
          for p in periods}
    assert by == {("vimshottari", "v1"): V.TWO_PASS_VERIFIED,
                  ("mudda", "m1"): V.CLASSICAL_MATCH,
                  ("narayana", "n1"): V.SINGLE}
    assert contract["tier"] == V.TWO_PASS_VERIFIED
    assert contract["builds_seen"] == [BUILD]  # the classical_match vim row never seen
    # the document states what it read and at which tier
    assert mod._rows_by_system_tier([dict(zip(DD._MULTILEVEL_KEYS, r))
                                     for r in _relabelled()]) == {
        "mudda": {V.CLASSICAL_MATCH: 1}, "narayana": {V.SINGLE: 1},
        "vimshottari": {V.TWO_PASS_VERIFIED: 1}}


# ── the consumer: the plurality keeps the system and states its tier ────────

def test_permission_detail_carries_the_accepted_tier_and_is_unchanged_without_one():
    t_iso = "2025-06-01T00:00:00+00:00"
    relevant = ({"Mars"}, set())
    mudda = {"system_id": "mudda", "lord_graha": "Mars",
             "start_iso": "2020-01-01T00:00:00+00:00",
             "end_iso": "2030-01-01T00:00:00+00:00"}
    # a tier-less (MD-only fetch) row: detail keys exactly as before
    base = perm._dasha_contributions([mudda], t_iso, *relevant)["mudda"]
    assert base["active"] and "verification_pass_status" not in base["detail"]
    # a relabelled multilevel row: active AND states its unverified tier
    hit = perm._dasha_contributions(
        [{**mudda, "verification_pass_status": V.CLASSICAL_MATCH}], t_iso, *relevant)["mudda"]
    assert hit["active"]
    assert hit["detail"]["verification_pass_status"] == V.CLASSICAL_MATCH
    assert hit["detail"]["tier_verified"] is False
    # and today's two_pass row says verified
    today = perm._dasha_contributions(
        [{**mudda, "verification_pass_status": V.TWO_PASS_VERIFIED}], t_iso, *relevant)["mudda"]
    assert today["detail"]["tier_verified"] is True
