"""A58 — honest-tier readers (steward M20261002T094420-d113).

A base-layer rebuild relabels MUDDA / NARAYANA level-1 daśā rows from
`two_pass_verified` to `classical_match`. The pinned `two_pass_verified` read
would then come back EMPTY for them and the plurality would report them
INACTIVE — a silent omission that reads as a finding. Two repairs:

 1. a PER-(system, level) tier policy: ONLY mudda/narayana level 1 accept the
    honest computed tiers; every other (system, level) stays strict, so the row
    set read on today's data is IDENTICAL (the deeper `single` levels, and the
    level-1 rows already excluded today, stay excluded — a separate decision);
 2. a system with NO readable row is UNAVAILABLE (could not be checked), not
    inactive (checked, did not fire): the permission VALUE is unchanged
    (DR-14 fixes the weights over all generators and is silent on a missing
    one) and is marked partial, with the reason.

The vimshottari §4.0 read (the '5.0' writer's contract, AM-10, the build pin)
stays STRICT.

Pure stub-conn plumbing: no Swiss, no real DB. The stub conn EVALUATES the
tier predicate it is handed, so a reader that stops sending the policy fails.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import swisseph as swe

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
    expected = {V.TWO_PASS_VERIFIED, V.CLASSICAL_MATCH, RTP.SINGLE, RTP.SINGLE_PASS,
                RTP.DOCUMENTED_APPROXIMATION, RTP.COMPUTED_EXTENSION}
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
    for name in (RTP.SINGLE, RTP.SINGLE_PASS, RTP.DOCUMENTED_APPROXIMATION,
                 RTP.COMPUTED_EXTENSION, V.CLASSICAL_MATCH, V.TWO_PASS_VERIFIED):
        assert name in V.ALL_STATUSES


def test_tier_evidence_never_calls_an_unverified_tier_verified():
    assert RTP.tier_evidence(V.TWO_PASS_VERIFIED)["tier_verified"] is True
    for t in sorted(RTP.HONEST_COMPUTED_TIERS - {V.TWO_PASS_VERIFIED}):
        ev = RTP.tier_evidence(t)
        assert ev == {"verification_pass_status": t, "tier_verified": False}


# ── behaviour-neutral on today's rows (per-level) ───────────────────────────

T, CM, SG = V.TWO_PASS_VERIFIED, V.CLASSICAL_MATCH, RTP.SINGLE
SYSTEMS = ["vimshottari", "yogini", "ashtottari", "chara_karaka", "naisargika",
           "mudda", "narayana", "kalachakra"]


def _rows_from(spec):
    """spec: {(system, level): (tier, n)} -> stored rows (a parent chain per
    system so level 2/3 rows have a parent)."""
    rows, k = [], 0
    for (system, level), (tier, n) in spec.items():
        for i in range(n):
            k += 1
            rows.append(_row(f"{system}-{level}-{i}", system, tier, level=level,
                             parent=(None if level == 1 else f"{system}-{level - 1}-0"),
                             lord="Mars" if level == 1 else "Venus",
                             start=f"{2000 + 10 * level + i:04d}-01-01T00:00:00+00:00",
                             end=f"{2000 + 10 * level + i + 1:04d}-01-01T00:00:00+00:00"))
    return rows


# The live read-only count (chart 482012f1, lahiri, levels 1-3) TODAY, in miniature:
# mudda/narayana L1 two_pass, deeper `single`; yogini/ashtottari/chara_karaka/naisargika L1
# classical_match; kalachakra every level single; vimshottari every level two_pass.
TODAY = {
    ("vimshottari", 1): (T, 2), ("vimshottari", 2): (T, 2), ("vimshottari", 3): (T, 2),
    ("mudda", 1): (T, 3), ("mudda", 2): (SG, 3), ("mudda", 3): (SG, 4),
    ("narayana", 1): (T, 2), ("narayana", 2): (SG, 3),
    ("yogini", 1): (CM, 3), ("yogini", 2): (SG, 3),
    ("ashtottari", 1): (CM, 2), ("ashtottari", 2): (SG, 2),
    ("chara_karaka", 1): (CM, 2), ("chara_karaka", 2): (SG, 2),
    ("naisargika", 1): (CM, 2), ("naisargika", 2): (SG, 2),
    ("kalachakra", 1): (SG, 2), ("kalachakra", 2): (SG, 2),
}
AFTER = {**TODAY, ("mudda", 1): (CM, 3), ("narayana", 1): (CM, 2)}  # the rebuild's relabel


def _ids(rows):
    return sorted((r["system_id"], r["level_n"], r["dasha_row_id"]) for r in rows)


def test_on_todays_rows_the_policy_read_is_identical_to_the_strict_read_per_system_and_level():
    rows = _rows_from(TODAY)
    strict = DD.fetch_dasha_periods_multilevel(_Conn(rows), "c", systems=SYSTEMS)
    policy = DD.fetch_dasha_periods_multilevel(
        _Conn(rows), "c", systems=SYSTEMS, level_tier_policy=True)
    assert strict and _ids(strict) == _ids(policy)
    # and the strict read is what the DR-14 plurality sees TODAY: vimshottari L1-3,
    # mudda L1, narayana L1 — nothing deeper, no classical_match/single level-1 system
    assert {(r["system_id"], r["level_n"]) for r in strict} == {
        ("vimshottari", 1), ("vimshottari", 2), ("vimshottari", 3),
        ("mudda", 1), ("narayana", 1)}


def test_after_the_relabel_level_one_of_mudda_and_narayana_still_comes_back_carrying_its_tier():
    rows = _rows_from(AFTER)
    strict = DD.fetch_dasha_periods_multilevel(_Conn(rows), "c", systems=SYSTEMS)
    assert {r["system_id"] for r in strict} == {"vimshottari"}      # the defect
    policy = DD.fetch_dasha_periods_multilevel(
        _Conn(rows), "c", systems=SYSTEMS, level_tier_policy=True)
    # the SAME (system, level) set as today — nothing deeper started voting
    assert {(r["system_id"], r["level_n"]) for r in policy} == {
        ("vimshottari", 1), ("vimshottari", 2), ("vimshottari", 3),
        ("mudda", 1), ("narayana", 1)}
    assert {r["verification_pass_status"] for r in policy
            if r["system_id"] in ("mudda", "narayana")} == {CM}
    assert {r["verification_pass_status"] for r in policy
            if r["system_id"] == "vimshottari"} == {T}


def test_default_read_stays_strict_equality_on_the_contract_tier():
    conn = _Conn(_rows_from(TODAY))
    DD.fetch_dasha_periods_multilevel(conn, "c", systems=["vimshottari"])
    sql, params = conn.calls[0]
    assert "AND verification_pass_status = %s" in sql and "ANY(%s)\n" not in sql.split(
        "AND verification_pass_status =")[1][:12] + "\n"
    assert params[4] == DD.READ_CONTRACT_TIER == V.TWO_PASS_VERIFIED


@pytest.mark.parametrize("refused", [
    V.DIVERGENT_FLAGGED, "floored", "pending_w3_verification",
    "external_computation_required", None, "PASS", "made_up_tier"])
def test_policy_read_still_refuses_floored_divergent_pending_unknown_null(refused):
    rows = [_row("m1", "mudda", refused, lord="Mars")]
    assert DD.fetch_dasha_periods_multilevel(
        _Conn(rows), "c", systems=["mudda"], level_tier_policy=True) == []


def test_backstop_drops_a_row_that_escapes_the_predicate():
    class _Leaky(_Conn):
        def execute(self, sql, params):
            self.calls.append((sql, params))
            rows = self.rows

            class _X:
                def fetchall(_s):
                    return rows
            return _X()
    rows = [_row("m1", "mudda", V.DIVERGENT_FLAGGED), _row("m2", "mudda", RTP.SINGLE, level=2, parent="m1x",
            start="2031-01-01T00:00:00+00:00", end="2032-01-01T00:00:00+00:00"),
            _row("m3", "mudda", CM, start="2033-01-01T00:00:00+00:00", end="2034-01-01T00:00:00+00:00")]
    out = DD.fetch_dasha_periods_multilevel(
        _Leaky(rows), "c", systems=["mudda"], level_tier_policy=True)
    assert [r["dasha_row_id"] for r in out] == ["m3"]   # divergent L1 and single L2 both dropped


def test_the_policy_table_is_the_explicit_minimum():
    assert RTP.LEVEL_TIER_POLICY == {("mudda", 1): RTP.HONEST_COMPUTED_TIERS,
                                     ("narayana", 1): RTP.HONEST_COMPUTED_TIERS}
    assert RTP.accepted_tiers_for("vimshottari", 1) == RTP.STRICT_TIERS
    assert RTP.accepted_tiers_for("mudda", 2) == RTP.STRICT_TIERS
    assert RTP.accepted_tiers_for("yogini", 1) == RTP.STRICT_TIERS
    assert not RTP.row_tier_accepted("mudda", None, CM)      # a NULL level is strict


# ── step06a: vimshottari strict, the voting systems under the policy ────────

def test_step06a_pinned_read_keeps_vimshottari_strict_and_reads_relabelled_level_one():
    mod = _load_step06a()
    rows = _rows_from(AFTER) + [
        # a vimshottari row at an honest-but-unverified tier must NOT enter the pin
        _row("vx", "vimshottari", CM, lord="Saturn", build="b-other")]
    periods, contract = mod.load_pinned_dasha_periods(
        _Conn(rows), "not-the-canonical-chart", SYSTEMS)
    got = {(p["system_id"], p["level_n"]): p["verification_pass_status"] for p in periods}
    assert got == {("vimshottari", 1): T, ("vimshottari", 2): T, ("vimshottari", 3): T,
                   ("mudda", 1): CM, ("narayana", 1): CM}
    assert contract["tier"] == T and contract["builds_seen"] == [BUILD]


class _CountConn:
    """Serves the availability COUNT from stored rows (system, level, tier -> n)."""

    def __init__(self, rows):
        self.rows, self.sql = rows, []

    def execute(self, sql, params=None):
        self.sql.append(sql)
        if "GROUP BY" in sql:
            agg = {}
            for r in self.rows:
                k = (r[1], r[2], r[8])
                agg[k] = agg.get(k, 0) + 1
            out = [{"system_id": a, "level_n": b, "verification_pass_status": c, "n": n}
                   for (a, b, c), n in sorted(agg.items())]
        else:
            out = []

        class _X:
            def fetchall(_s):
                return out
        return _X()


def test_availability_document_says_why_a_system_has_no_readable_row():
    mod = _load_step06a()
    rows = _rows_from(TODAY)
    read = DD.fetch_dasha_periods_multilevel(
        _Conn(rows), "c", systems=SYSTEMS, level_tier_policy=True)
    av = mod.dasha_availability(_CountConn(rows), "c", read)
    assert av["vimshottari"]["state"] == av["mudda"]["state"] == av["narayana"]["state"] == "available"
    for sid in ("yogini", "ashtottari", "chara_karaka", "naisargika", "kalachakra"):
        assert av[sid]["state"] == "unavailable", sid
        assert av[sid]["reason"] == "all_stored_rows_refused_by_tier_policy"
        assert av[sid]["observed_rows_by_level_tier"]            # states what exists
    # a system with nothing stored is a different reason
    av2 = mod.dasha_availability(_CountConn([]), "c", [])
    assert {v["reason"] for v in av2.values()} == {"no_rows_stored"}


# ── the consumer ────────────────────────────────────────────────────────────

_MUDDA = {"system_id": "mudda", "lord_graha": "Mars",
          "start_iso": "2020-01-01T00:00:00+00:00", "end_iso": "2030-01-01T00:00:00+00:00"}
_REL = ({"Mars"}, set())
_T_ISO = "2025-06-01T00:00:00+00:00"


def test_permission_detail_carries_the_accepted_tier_and_is_unchanged_without_one():
    base = perm._dasha_contributions([_MUDDA], _T_ISO, *_REL)["mudda"]
    assert base["active"] and "verification_pass_status" not in base["detail"]
    hit = perm._dasha_contributions(
        [{**_MUDDA, "verification_pass_status": CM}], _T_ISO, *_REL)["mudda"]
    assert hit["active"] and hit["state"] == "active"
    assert hit["detail"]["verification_pass_status"] == CM
    assert hit["detail"]["tier_verified"] is False
    today = perm._dasha_contributions(
        [{**_MUDDA, "verification_pass_status": T}], _T_ISO, *_REL)["mudda"]
    assert today["detail"]["tier_verified"] is True


def test_a_system_with_no_rows_is_unavailable_not_inactive_and_a_covering_miss_is_inactive():
    rows = [_MUDDA, {**_MUDDA, "system_id": "narayana", "lord_graha": "Venus"}]  # narayana: lord misses
    out = perm._dasha_contributions(rows, _T_ISO, *_REL)
    assert out["mudda"]["state"] == "active"
    assert out["narayana"]["state"] == "inactive" and out["narayana"]["active"] is False
    for sid in perm.DASHA_SYSTEM_IDS:
        if sid not in ("mudda", "narayana"):
            assert out[sid]["state"] == "unavailable" and out[sid]["active"] is False
            assert out[sid]["detail"]["reason"] == perm.REASON_NO_READABLE_ROWS


def test_unavailable_changes_no_permission_value_and_marks_the_result_partial():
    """DR-14 fixes the weights over all generators and is silent on a missing one: the
    denominator is unchanged (today's value does not move) — the result is MARKED partial."""
    full = [{**_MUDDA, "system_id": sid, "lord_graha": "Mars"} for sid in perm.DASHA_SYSTEM_IDS]
    partial = [r for r in full if r["system_id"] in ("mudda", "narayana")]

    def run(periods):
        return perm.compute_permission(
            swe, None, "c", "career", [], 2460000.0, dasha_periods=periods)
    v_full, d_full = run(full)
    v_part, d_part = run(partial)
    # the value of the partial read equals what treating the missing systems as 0 always gave:
    expected = sum(perm.SYSTEM_WEIGHTS[s] for s in ("mudda", "narayana")) / sum(perm.SYSTEM_WEIGHTS.values())
    assert v_part == pytest.approx(expected)
    assert d_full["permission_partial"] is False and d_full["systems_unavailable"] == []
    assert d_part["permission_partial"] is True
    assert {u["system_id"] for u in d_part["systems_unavailable"]} == (
        set(perm.DASHA_SYSTEM_IDS) - {"mudda", "narayana"})
    assert all(s["state"] in ("active", "inactive", "unavailable")
               for s in d_part["systems"] if "state" in s)
