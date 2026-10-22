"""SR-DASHA-SINGLE-TIER: the governed daśā reader admits `single` for five systems, only into a flagging consumer.

Ruling (surrogate, 2026-10-22, option (a) scoped): ashtottari, chara_karaka, kalachakra, naisargika and yogini are stored
at verification tier `single` at every level (production readback, chart 482012f1). The governed reader admits those rows
ONLY into a consumer that carries `single_tier_input` onto every row it derives (CLAUDE.md §N.6: counted and flagged
separately, never presented as verified). `ka_dasha_kala` is that consumer; every other reader keeps refusing `single`.

The table below is shaped like the production readback (tiers and levels per system) with synthetic periods -- it asserts
no native chart value. Real PostgreSQL, so the governed-view SQL itself is what is measured (the kala-db-tests job).
One test per distinct claim; the reversion that must fail it is named in each docstring.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import psycopg
import psycopg.rows
import pytest

from services.gochara_grammar import read_tier_policy as RTP
from services.gochara_kernel import dasha_read as reader
from services.ka_dasha_kala import tree_walk as tw
from services.ka_dasha_kala import writer as dk_writer
from services.ka_dasha_kala.service import KaDashaKalaService
from services.ka_dasha_kala.tree_walk import DashaInterval, _subdivide_prana, walk_eligible_intervals
from tests.l3.kala_db.test_j4p_malformed_settled_periods import AYA, BUILD, CHART

T, CM, SG = "two_pass_verified", "classical_match", "single"
LISTED = ("ashtottari", "chara_karaka", "kalachakra", "naisargika", "yogini")
MD_START, MD_END = datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2040, 1, 1, tzinfo=timezone.utc)
AD_START, AD_END = datetime(2015, 1, 1, tzinfo=timezone.utc), datetime(2025, 1, 1, tzinfo=timezone.utc)
WINDOW = dict(date_start=date(2010, 1, 1), date_end=date(2030, 12, 31))
SIGNATURE = dict(target_lords={"Saturn", "Rahu"}, related_lords={"Mercury", "Venus"})


def _insert(conn, system, level, tier, lord, parent=None, start=MD_START, end=MD_END):
    return conn.execute(
        """INSERT INTO chart_dashas
           (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id, level_n, parent_row_id, lord_graha,
            start_iso, end_iso, verification_pass_status, applies_to_this_chart_flag,
            is_truncated_at_window_start, is_truncated_at_window_end, start_date, end_date)
           VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, false, false, %s, %s)
           RETURNING dasha_row_id""",
        (CHART, BUILD, system, AYA, level, parent, lord, start, end, tier, start.date(), end.date())
    ).fetchone()["dasha_row_id"]


@pytest.fixture
def db(kala_db_dsn):
    """Tiers and levels as in the production readback (dasha-tier-readback2-20261022T1734Z): the five listed systems
    `single` at levels 1-2; vimshottari `two_pass_verified`; mudda L1 `classical_match`, L2 `single`; narayana and
    vimshottari_kp `single`, the latter with no level 1 (as stored)."""
    with psycopg.connect(kala_db_dsn, row_factory=psycopg.rows.dict_row) as conn:
        conn.execute("""CREATE TABLE chart_dashas (
            dasha_row_id uuid, chart_id uuid, build_id uuid, system_id text,
            ayanamsha_id text, level_n int, parent_row_id uuid, lord_graha text,
            start_iso timestamptz, end_iso timestamptz,
            verification_pass_status text, applies_to_this_chart_flag bool,
            is_truncated_at_window_start bool, is_truncated_at_window_end bool,
            start_date date, end_date date, lord_to_parent_relationship text,
            kp_sublevel text, kp_sub_lord text)""")
        for system in LISTED:
            md = _insert(conn, system, 1, SG, "Saturn")
            _insert(conn, system, 2, SG, "Rahu", md, AD_START, AD_END)
        vim = _insert(conn, "vimshottari", 1, T, "Saturn")
        _insert(conn, "vimshottari", 2, T, "Rahu", vim, AD_START, AD_END)
        mudda = _insert(conn, "mudda", 1, CM, "Saturn")
        _insert(conn, "mudda", 2, SG, "Rahu", mudda, AD_START, AD_END)
        nar = _insert(conn, "narayana", 1, SG, "Saturn")
        _insert(conn, "narayana", 2, SG, "Rahu", nar, AD_START, AD_END)
        _insert(conn, "vimshottari_kp", 2, SG, "Rahu", vim, AD_START, AD_END)
        yield conn
        conn.rollback()


def _query(conn, *, admit=None, systems=None, max_level=2):
    """admit=None leaves the argument OUT, exactly as ka_sangam / ph_nimitta / kala_permission call query()."""
    opt = {} if admit is None else {"admit_single_tier": admit}
    return KaDashaKalaService(conn).query(
        chart_id=CHART, ayanamsha_id=AYA, max_level=max_level, systems=systems, **opt, **SIGNATURE, **WINDOW)


def test_a_single_tier_row_of_a_listed_system_yields_a_flagged_window(db):
    """Claim 1 -- every window derived from a `single` row of a listed system carries single_tier_input, is counted apart,
    and the result names the judgment flag; a verified (vimshottari) window is NOT flagged and agreement splits the two.
    Reversion: tree_walk stops setting single_tier_input on the intervals (propagation removed)."""
    result = _query(db, admit=True, systems=set(LISTED) | {"vimshottari"})
    by_system = {}
    for w in result.windows:
        by_system.setdefault(w.system_id, []).append(w)
    assert set(by_system) == set(LISTED) | {"vimshottari"}
    for system in LISTED:
        assert by_system[system] and all(
            w.single_tier_input and w.verification_pass_status == SG for w in by_system[system]), system
    assert by_system["vimshottari"] and not any(w.single_tier_input for w in by_system["vimshottari"])
    assert result.single_tier_windows == sum(len(by_system[s]) for s in LISTED) > 0
    assert result.judgment_flags == [RTP.SINGLE_TIER_INPUT_FLAG]
    agreement = result.windows[0].cross_dasha_agreement
    assert agreement.single_tier_systems == sorted(LISTED) and agreement.count == 6
    assert agreement.verified_count == 1            # only vimshottari agrees without the flag


def test_without_the_opt_in_a_listed_system_still_refuses_single(db):
    """Claim 2 -- a consumer that does not ask (ka_sangam, ph_nimitta, kala_permission call query() as before) keeps
    refusing `single`: no window, no flag, no judgment flag. Reversion: admit_single_tier defaults to True."""
    result = _query(db, systems=set(LISTED) | {"vimshottari"})
    assert {w.system_id for w in result.windows} == {"vimshottari"}
    assert result.single_tier_windows == 0 and result.judgment_flags == []
    assert KaDashaKalaService(db).confirm_systems_present(CHART, AYA).keys() == {"vimshottari", "mudda", "narayana"}


def test_an_unlisted_system_at_single_still_refuses_even_with_the_opt_in(db):
    """Claim 3 -- vimshottari_kp (L2), narayana L2 and mudda L2 stay refused. (Mudda L1 `classical_match` and narayana L1
    are read by the PRE-EXISTING per-level policy, A58; the walk flags a narayana `single` L1 row honestly.)
    Reversion: SINGLE_TIER_ADMITTED_SYSTEMS gains narayana and vimshottari_kp."""
    for level in (1, 2):
        assert walk_eligible_intervals(
            db, CHART, AYA, "vimshottari_kp", max_level=level, admit_single_tier=True, **SIGNATURE, **WINDOW) == []
    assert walk_eligible_intervals(
        db, CHART, AYA, "narayana", max_level=2, admit_single_tier=True, **SIGNATURE, **WINDOW) == []
    nar_md = walk_eligible_intervals(
        db, CHART, AYA, "narayana", max_level=1, admit_single_tier=True, **SIGNATURE, **WINDOW)
    assert [(i.level_n, i.single_tier_input) for i in nar_md] == [(1, True)]
    mudda_ad = walk_eligible_intervals(
        db, CHART, AYA, "mudda", max_level=2, admit_single_tier=True, **SIGNATURE, **WINDOW)
    assert mudda_ad == []                                                       # L2 `single` refused
    mudda_md = walk_eligible_intervals(
        db, CHART, AYA, "mudda", max_level=1, admit_single_tier=True, **SIGNATURE, **WINDOW)
    assert [(i.level_n, i.verification_pass_status, i.single_tier_input) for i in mudda_md] == [(1, CM, False)]
    counts = KaDashaKalaService(db).confirm_systems_present_by_tier(CHART, AYA, admit_single_tier=True)
    assert set(counts) == set(LISTED) | {"vimshottari", "mudda", "narayana"}
    assert counts["mudda"] == {CM: 1} and counts["narayana"] == {SG: 1}


def test_vimshottari_reads_stay_strict_and_the_p1_operand_never_sees_single(db):
    """Claim 4 -- the 5.0 P1 operand (load_pinned_vimshottari) and the vimshottari rows stay two_pass_verified-only: a
    `single` vimshottari row is read by nobody, opt-in or not. Reversion: 'vimshottari' added to SINGLE_TIER_ADMITTED_SYSTEMS."""
    _insert(db, "vimshottari", 1, SG, "Mars", start=datetime(1990, 1, 1, tzinfo=timezone.utc), end=MD_START)
    rows, contract = reader.load_pinned_vimshottari(db, CHART)
    assert {r["verification_pass_status"] for r in rows} == {T} and contract["tier"] == T
    flagged = walk_eligible_intervals(
        db, CHART, AYA, "vimshottari", max_level=1, admit_single_tier=True,
        target_lords={"Mars", "Saturn"}, related_lords=set(), **WINDOW)
    assert {(i.lord_graha, i.verification_pass_status, i.single_tier_input) for i in flagged} == {("Saturn", T, False)}
    assert RTP.accepted_tiers_for("vimshottari", 1) == RTP.STRICT_TIERS
    assert not RTP.single_tier_admitted("vimshottari", SG)


def test_the_vote_and_permission_readers_still_refuse_single_for_listed_systems(db):
    """Claim 5 -- the per-level policy readers (plurality vote, permission, class context) cannot carry the flag, so they
    keep refusing `single` for the five systems. Reversion: the five systems enter LEVEL_TIER_POLICY."""
    got = reader.load_governed_dasha_periods(db, CHART, systems=list(LISTED), levels=(1, 2), level_tier_policy=True)
    assert got == []
    assert all(RTP.accepted_tiers_for(s, lv) == RTP.STRICT_TIERS for s in LISTED for lv in (1, 2, 3, 4))
    with pytest.raises(reader.DashaBuildRefused):
        reader.validate_live_dasha_periods(
            CHART, [{"system_id": "yogini", "level_n": 1, "verification_pass_status": SG, "build_id": BUILD,
                     "start_iso": MD_START, "end_iso": MD_END}], AYA, conn=db)


def test_the_opt_in_needs_a_projection_that_carries_the_tier(db):
    """Claim 6 -- structural: a projection that erases the tier cannot propagate the flag, so it cannot be read with the
    opt-in; neither can an explicit F2 clock tier. Reversion: the projection / clock-tier guards in
    execute_governed_dasha_query."""
    for name in ("tree_level1", "dasha_system_counts", "avadhi_periods", "kshetra_row_count"):
        with pytest.raises(reader.DashaBuildRefused, match="read_contract_mismatch"):
            reader.execute_governed_dasha_query(db, CHART, reader.dasha_query(name), (), admit_single_tier=True)
    with pytest.raises(reader.DashaBuildRefused, match="read_contract_mismatch"):
        reader.execute_governed_dasha_query(
            db, CHART, reader.dasha_query("dasha_system_tier_counts"), (CHART, AYA),
            admit_single_tier=True, clock_tier=SG)


def test_ka_dasha_kala_self_test_passes_on_a_production_shaped_table_and_flags_what_it_read(db):
    """Claim 7 -- the self-test that failed in K9 ("Missing systems in chart_dashas: [ashtottari, chara_karaka, kalachakra,
    naisargika, yogini]") passes, and its detail names the single-tier systems and the flagged-window count.
    Reversion: the writer self-test stops passing admit_single_tier=True."""
    ok, detail = dk_writer._run_selftest(db)
    body = json.loads(detail)
    assert ok, detail
    # narayana L1 `single` is read by the pre-existing per-level policy; the detail reports every `single` it saw
    assert body["single_tier_systems"] == sorted(set(LISTED) | {"narayana"})
    assert body["judgment_flags"] == [RTP.SINGLE_TIER_INPUT_FLAG] and body["windows_single_tier_input"] > 0
    assert set(body["systems_found"]) >= set(LISTED) | {"vimshottari", "mudda"}


def test_ka_dasha_kala_self_test_still_fails_when_a_system_is_absent(db):
    """Claim 8 (N.8) -- the missing-system assertion can still read false: with yogini removed the self-test fails by
    naming it. Reversion: the missing-system assertion removed."""
    db.execute("DELETE FROM chart_dashas WHERE system_id = 'yogini'")
    ok, detail = dk_writer._run_selftest(db)
    assert not ok and "yogini" in json.loads(detail)["error"]


def test_a_derived_interval_inherits_the_flag_from_a_single_ancestor_and_through_prana(monkeypatch):
    """Claim 9 -- an interval is flagged when ANY row it was derived from is `single` (its own or an ancestor's), and the
    in-memory level-5 subdivision inherits it. Reversion: _subdivide_prana drops single_tier_input / the walk drops the
    ancestor term. (A verified child under a `single` parent is not storable through the admitted tiers, so the walk is
    fed that row set directly.)"""
    md = {"dasha_row_id": "md", "lord_graha": "Saturn", "start_date": date(2000, 1, 1), "end_date": date(2040, 1, 1),
          "kp_sublevel": None, "kp_sub_lord": None, "verification_pass_status": SG}
    ad = {"dasha_row_id": "ad", "lord_graha": "Rahu", "start_date": date(2015, 1, 1), "end_date": date(2025, 1, 1),
          "level_n": 2, "parent_row_id": "md", "kp_sublevel": None, "kp_sub_lord": None, "verification_pass_status": T}

    class _Rows:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows
    monkeypatch.setattr(tw, "execute_governed_dasha_query",
                        lambda conn, chart, sql, params, **kw: _Rows([md] if "level_n        = 1" in sql else [ad]))
    out = walk_eligible_intervals(None, CHART, AYA, "yogini", max_level=2, admit_single_tier=True,
                                  **SIGNATURE, **WINDOW)
    assert [(i.level_n, i.verification_pass_status, i.single_tier_input) for i in out] == [(2, T, True)]
    sookshma = DashaInterval(
        dasha_row_id="s", chart_id=CHART, ayanamsha_id=AYA, system_id="yogini", level_n=4, lord_graha="Rahu",
        start_date=date(2020, 1, 1), end_date=date(2020, 3, 1), parent_row_id="p",
        verification_pass_status=SG, single_tier_input=True)
    prana = _subdivide_prana(sookshma)
    assert prana and all(p.level_n == 5 and p.single_tier_input for p in prana)
