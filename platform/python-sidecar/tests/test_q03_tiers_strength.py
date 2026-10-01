"""
test_q03_tiers_strength.py -- Q03 / SS N-62 honest tiers for ga_strength (TS-STR-1/2/3).

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §6 / §7 item 8 / §5, plus the lane's SS ruling
that the `floored_sarva_mismatch` string (not a vocabulary member) becomes the vocabulary member
`floored` with the reason carried in provenance.

  * `_verify_shadbala` / `_verify_ashtakavarga` return `classical_match` ONLY after their checks
    ran and passed (they raise TwoPassVerificationError on a violation).
  * That tier lands ONLY on the rows the checks examine: graha_shadbala_{sthana,dig,kala,cheshta,
    drik,total} of the seven classical grahas, and ashtakavarga_bindu / ashtakavarga_bindu_sign.
  * Every other category is `single` (no broadcast); per-varga ashtakavarga is
    `documented_approximation`; a per-varga SARVA mismatch is `floored` with the reason in the
    row's provenance.
  * Everything the builders can emit is a live-constraint member (checked against migration 539).

The shadbala / ashtakavarga inputs come from the REAL engine (PyJHora) for the native chart, as
in tests/test_ga3_writers.py, so the verifiers see genuine values.
"""
from __future__ import annotations

import collections
import copy
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from brahmagyan import verification_tiers as T
from ga_writers import ga_strength_writer as W

_REPO = pathlib.Path(__file__).resolve().parents[3]

NATIVE_BIRTH = {
    "datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27, "longitude_deg": 85.84,
    "tz_offset_hours": 5.5, "place_name": "Bhubaneswar", "subject_label": "Abhisek",
}
_KW = dict(lat=NATIVE_BIRTH["latitude_deg"], lon=NATIVE_BIRTH["longitude_deg"],
           tz=NATIVE_BIRTH["tz_offset_hours"])
AY = "lahiri_chitrapaksha"
CID, BID, NOW, ENG = "chart-x", "build-x", "2026-10-02T00:00:00+00:00", "eng/1.0"

_SHADBALA_EXAMINED = {
    "graha_shadbala_sthana", "graha_shadbala_dig", "graha_shadbala_kala",
    "graha_shadbala_cheshta", "graha_shadbala_drik", "graha_shadbala_total",
}
_AV_EXAMINED = {"ashtakavarga_bindu", "ashtakavarga_bindu_sign"}
_NODES = {"RAH_MEAN", "KET_MEAN"}


@pytest.fixture(autouse=True)
def _no_halt_log(monkeypatch):
    monkeypatch.setattr(W, "_write_halt_log", lambda *a, **k: None)


@pytest.fixture(scope="module")
def engine():
    from pyjhora_adapter.compute import compute_chart
    chart = compute_chart(inputs=NATIVE_BIRTH, ayanamsha_id="lahiri")
    jd = float(chart["provenance"]["jd_ut"])
    shadbala = W._derive_shadbala_from_positions(chart, AY, jd_ut=jd, **_KW)
    av = W._derive_ashtakavarga(jd, AY, **_KW)
    return {
        "chart": chart, "jd": jd, "shadbala": shadbala,
        "ik": W._derive_ishta_kashta(shadbala, jd, AY, **_KW),
        "vm": W._derive_vimsopaka(jd, AY, **_KW),
        "bav": av["bindus"], "pinda": av["pinda"],
        "grids": W._derive_ashtakavarga_shodhana_grids(jd, AY, **_KW),
        "prastara": W._derive_ashtakavarga_prastara(jd, AY, **_KW),
        "bhava": W._derive_bhava_bala(jd, AY, **_KW),
    }


def _shadbala_rows(e, tier):
    return W._build_shadbala_rows(e["shadbala"], e["ik"], e["vm"], CID, BID, AY, NOW, ENG, tier)


def _av_rows(e, tier):
    return W._build_ashtakavarga_rows(e["bav"], e["pinda"], CID, BID, AY, NOW, ENG, tier,
                                      grids=e["grids"], prastara=e["prastara"])


def _by_cat(rows):
    out = collections.defaultdict(collections.Counter)
    for r in rows:
        out[r["fact_category"]][r["verification_pass_status"]] += 1
    return out


# ── the verifiers return the tier only after the checks ran ───────────────────


def test_verifiers_return_classical_match_on_real_engine_output(engine):
    assert W._verify_shadbala(engine["shadbala"]) == T.CLASSICAL_MATCH
    assert W._verify_ashtakavarga(engine["bav"]) == T.CLASSICAL_MATCH


def test_verify_shadbala_halts_on_a_negative_magnitude_sub_bala(engine):
    sb = copy.deepcopy(engine["shadbala"])
    sb["Sun"]["sthana"] = -0.5
    # keep sum(sub-balas) == total so ONLY the non-negativity guard can fire
    sb["Sun"]["total"] = sum(sb["Sun"][k] for k in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"))
    assert sb["Sun"]["total"] > 0
    with pytest.raises(W.TwoPassVerificationError, match="is negative"):
        W._verify_shadbala(sb)


def test_verify_shadbala_halts_on_a_non_positive_total(engine):
    sb = copy.deepcopy(engine["shadbala"])
    for k in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik", "total"):
        sb["Mars"][k] = 0.0  # sum == total == 0: only the total > 0 guard can fire
    with pytest.raises(W.TwoPassVerificationError, match="zero or negative"):
        W._verify_shadbala(sb)


def test_verify_shadbala_halts_on_an_implausible_drik(engine):
    sb = copy.deepcopy(engine["shadbala"])
    sb["Venus"]["drik"] = 50.0
    sb["Venus"]["total"] = sum(sb["Venus"][k] for k in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"))
    with pytest.raises(W.TwoPassVerificationError, match="drik-bala bounds"):
        W._verify_shadbala(sb)


def test_verify_shadbala_halts_on_a_sum_total_mismatch(engine):
    sb = copy.deepcopy(engine["shadbala"])
    sb["Moon"]["total"] = sb["Moon"]["total"] + 1.0
    with pytest.raises(W.TwoPassVerificationError):
        W._verify_shadbala(sb)


def test_verify_ashtakavarga_halts_on_sarva_not_337(engine):
    # keep SARVA == house-wise sum of the seven (check 2 passes) so ONLY the 337 total (check 1) fails
    bav = copy.deepcopy(engine["bav"])
    bav["Sun"][0] += 10
    bav["SARVA"][0] += 10
    with pytest.raises(W.TwoPassVerificationError, match="Sarvashtakavarga total"):
        W._verify_ashtakavarga(bav)


def test_verify_ashtakavarga_halts_when_sarva_is_not_the_sum_of_the_seven(engine):
    bav = copy.deepcopy(engine["bav"])
    bav["Sun"][0] += 1
    bav["Sun"][1] -= 1  # SARVA total unchanged -> still 337, but the house-wise sums now disagree
    with pytest.raises(W.TwoPassVerificationError, match="SARVA house"):
        W._verify_ashtakavarga(bav)


# ── TS-STR-1 / TS-STR-3: the tier lands only on the examined rows ─────────────


def test_shadbala_rows_tier_only_on_examined_categories(engine):
    rows = _shadbala_rows(engine, T.CLASSICAL_MATCH)
    for r in rows:
        st, cat, subj = r["verification_pass_status"], r["fact_category"], r["fact_subject"]
        nodal = subj in _NODES
        if nodal and r["fact_key"] == "rupa" and cat in {
                "graha_shadbala_dig", "graha_shadbala_kala", "graha_shadbala_cheshta",
                "graha_shadbala_naisargika"}:
            assert st == T.NOT_DEFINED_FOR_NODES
        elif nodal:
            assert st == T.SINGLE, (cat, subj, st)  # computed_extension, outside shad_bala
        elif cat in _SHADBALA_EXAMINED and r["fact_key"] == "rupa":
            assert st == T.CLASSICAL_MATCH, (cat, subj, st)
        else:
            assert st == T.SINGLE, (cat, r["fact_key"], subj, st)


def test_naisargika_and_required_rupa_are_single_not_hardcoded_classical_match(engine):
    rows = _shadbala_rows(engine, T.CLASSICAL_MATCH)
    sel = [r for r in rows if r["fact_subject"] not in _NODES and (
        r["fact_category"] == "graha_shadbala_naisargika" or r["fact_key"] == "required_rupa")]
    assert len(sel) == 14  # 7 naisargika + 7 required_rupa
    assert {r["verification_pass_status"] for r in sel} == {T.SINGLE}


def test_ratio_ishta_kashta_vimsopaka_are_single(engine):
    by = _by_cat(_shadbala_rows(engine, T.CLASSICAL_MATCH))
    for cat in ("graha_ishta_phala", "graha_kashta_phala", "graha_vimsopaka_shadvarga",
                "graha_vimsopaka_saptavarga", "graha_vimsopaka_dasavarga",
                "graha_vimsopaka_shodasavarga"):
        assert set(by[cat]) == {T.SINGLE}, cat
    ratio = [r for r in _shadbala_rows(engine, T.CLASSICAL_MATCH) if r["fact_key"] == "ratio"]
    assert len(ratio) == 7 and {r["verification_pass_status"] for r in ratio} == {T.SINGLE}


def test_stubbed_shadbala_verifier_drops_the_examined_rows_to_single(engine):
    """MUTANT / TS-STR-1: with the verifier's tier stubbed to UNVERIFIED_DEFAULT the examined
    categories fall to `single`. (Returning `classical_match` from a stub that checks nothing is
    caught by the halting tests above: corrupted inputs must raise.)"""
    rows = _shadbala_rows(engine, T.UNVERIFIED_DEFAULT)
    assert T.CLASSICAL_MATCH not in {r["verification_pass_status"] for r in rows}


def test_av_rows_tier_only_on_raw_bindu_categories(engine):
    rows = _av_rows(engine, T.CLASSICAL_MATCH)
    by = _by_cat(rows)
    for cat in _AV_EXAMINED:
        assert set(by[cat]) == {T.CLASSICAL_MATCH}, cat
        assert sum(by[cat].values()) == 96  # (7 grahas + SARVA) x 12
    unexamined = [c for c in by if c not in _AV_EXAMINED]
    assert {"ashtakavarga_trikona_shodhana", "ashtakavarga_ekadhipathya_shodhana",
            "ashtakavarga_pinda_sodhita", "ashtakavarga_pinda_bhinna", "ashtakavarga_pinda_raasi",
            "ashtakavarga_pinda_sarva", "ashtakavarga_kakshya_boundary"} <= set(unexamined)
    for cat in unexamined:
        assert set(by[cat]) == {T.SINGLE}, cat


def test_stubbed_ashtakavarga_verifier_drops_the_examined_rows_to_single(engine):
    rows = _av_rows(engine, T.UNVERIFIED_DEFAULT)
    assert T.CLASSICAL_MATCH not in {r["verification_pass_status"] for r in rows}


def test_bhava_bala_rows_stay_documented_approximation(engine):
    rows = W._build_bhava_bala_rows(engine["bhava"], CID, BID, AY, NOW, ENG, T.UNVERIFIED_DEFAULT)
    assert rows and {r["verification_pass_status"] for r in rows} == {T.DOCUMENTED_APPROXIMATION}


def test_broadcast_mutant_is_caught(engine):
    """MUTANT (TS-STR-3): broadcast the verifier tier onto every row again. The unexamined
    categories would then be classical_match -- exactly what the two tests above forbid."""
    rows = _av_rows(engine, T.CLASSICAL_MATCH)
    for r in rows:
        r["verification_pass_status"] = T.CLASSICAL_MATCH
    by = _by_cat(rows)
    assert any(set(by[c]) != {T.SINGLE} for c in by if c not in _AV_EXAMINED)


# ── offline reproduction of the audit §6 totals (canon: 5 ayanamshas) ─────────


def test_audit_section6_totals_reproduced_offline(engine):
    n_ay = 5  # per-ayanamsha structure is identical across the 5 canonical ayanamshas
    sb = _shadbala_rows(engine, T.CLASSICAL_MATCH)
    av = _av_rows(engine, T.CLASSICAL_MATCH)
    cm = [r for r in sb + av if r["verification_pass_status"] == T.CLASSICAL_MATCH]
    # shadbala/raw-bindu examined rows: 1,170 in the audit
    assert len(cm) * n_ay == 1170
    sb_cm = [r for r in sb if r["verification_pass_status"] == T.CLASSICAL_MATCH]
    av_cm = [r for r in av if r["verification_pass_status"] == T.CLASSICAL_MATCH]
    assert len(sb_cm) * n_ay == 210 and len(av_cm) * n_ay == 960
    # single rows the audit enumerates (§6): ratio 35, nodal 30, ishta/kashta 70, vimsopaka 140,
    # AV non-bindu (shodhana 840, kakshya 120, pinda 160 = 1,120)
    singles = collections.Counter()
    for r in sb + av:
        if r["verification_pass_status"] == T.SINGLE:
            singles[r["fact_category"] + ("/nodal" if r["fact_subject"] in _NODES else "")] += 1
    per_ay = lambda cat: singles[cat] * n_ay  # noqa: E731
    assert per_ay("graha_ishta_phala") + per_ay("graha_kashta_phala") == 70
    assert sum(v for k, v in singles.items() if k.startswith("graha_vimsopaka")) * n_ay == 140
    assert sum(1 for r in sb if r["fact_key"] == "ratio") * n_ay == 35
    assert sum(v for k, v in singles.items() if k.endswith("/nodal")) * n_ay == 30
    av_single = sum(v for k, v in singles.items() if k.startswith("ashtakavarga")
                    and k != "ashtakavarga_bindu_contributor")
    assert av_single * n_ay == 1120


# ── TS-STR-2: per-varga ashtakavarga ──────────────────────────────────────────


def _bav_varga(total_ok: bool = True) -> dict[str, list[int]]:
    """A synthetic per-varga set. SARVA sums to 337 when `total_ok`, else is off by 40."""
    base = [4, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4]  # 43 per graha x 7 = 301 -> pad to 337 below
    grahas = {g: list(base) for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    sarva = [sum(grahas[g][i] for g in grahas) for i in range(12)]
    diff = 337 - sum(sarva)
    sarva[0] += diff  # force the total to exactly 337
    if not total_ok:
        sarva[0] += 40
    return {**grahas, "SARVA": sarva}


def test_per_varga_rows_are_documented_approximation_when_sarva_is_337():
    rows = W._build_ashtakavarga_per_varga_rows(_bav_varga(True), "D9", CID, BID, AY, NOW, ENG)
    assert rows and {r["verification_pass_status"] for r in rows} == {T.DOCUMENTED_APPROXIMATION}
    assert len(rows) == 8 * 12 + 8  # bindu rows + pinda rows, per varga


def test_per_varga_sarva_mismatch_is_floored_with_reason_not_a_non_member_string():
    rows = W._build_ashtakavarga_per_varga_rows(_bav_varga(False), "D9", CID, BID, AY, NOW, ENG)
    tiers = {r["verification_pass_status"] for r in rows}
    assert tiers == {T.FLOORED}
    assert "floored_sarva_mismatch" not in tiers
    for r in rows:
        T.emit_tier(r["verification_pass_status"], table="chart_facts")  # legal vocab member
        assert "floored_reason=sarva_mismatch" in r["source_calculation"]
        assert "sarva_mismatch" in r["citation_human"]
    # the values are kept (honestly flagged, not fabricated or dropped)
    assert all(r["fact_value_num"] is not None for r in rows)


def test_reintroducing_the_non_member_string_would_fail_assert_legal():
    """MUTANT (TS-STR-2): reintroduce the non-vocabulary string -> `assert_legal` rejects it."""
    with pytest.raises(ValueError, match="not in the settled vocabulary"):
        T.emit_tier("floored_sarva_mismatch")


def _constraint_members() -> set[str]:
    sql = (_REPO / "platform/supabase/migrations/539_chart_facts_verification_pass_status_check.sql").read_text()
    return set(re.findall(r"'([a-z_0-9]+)'", sql.split("CHECK", 1)[1]))


def test_every_status_ga_strength_can_emit_is_accepted_by_the_live_chart_facts_constraint(engine):
    """The live `chart_facts_verification_pass_status_check` (migration 539; read from pg_constraint
    2026-10-02 and re-read from the migration text here) must accept every tier the builders emit,
    including the forced-SARVA-failure case that used to stamp a non-member string."""
    allowed = _constraint_members()
    assert {"floored", "classical_match", "single", "documented_approximation",
            "computed_extension", "not_defined_for_nodes"} <= allowed
    emitted: set[str] = set()
    emitted |= {r["verification_pass_status"] for r in _shadbala_rows(engine, T.CLASSICAL_MATCH)}
    emitted |= {r["verification_pass_status"] for r in _av_rows(engine, T.CLASSICAL_MATCH)}
    emitted |= {r["verification_pass_status"] for r in W._build_bhava_bala_rows(
        engine["bhava"], CID, BID, AY, NOW, ENG, T.UNVERIFIED_DEFAULT)}
    for ok in (True, False):
        emitted |= {r["verification_pass_status"] for r in W._build_ashtakavarga_per_varga_rows(
            _bav_varga(ok), "D9", CID, BID, AY, NOW, ENG)}
    emitted |= {r["verification_pass_status"] for r in W._build_kala_cheshta_floor_rows(
        CID, BID, AY, NOW, ENG, ["D9"])}
    assert emitted <= allowed, emitted - allowed


# ── end to end through build_ga_strength with a fake connection ───────────────


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def executemany(self, *a, **k):
        return None

    def execute(self, *a, **k):
        return self


class _FakeConn:
    def execute(self, sql, params=None):
        return _Cur([])

    def cursor(self, *a, **k):
        return _Cur([])

    def commit(self):
        return None


def _run_build(monkeypatch, *, sb_stub=None, av_stub=None):
    captured: list[dict] = []
    monkeypatch.setattr(W, "_insert_chart_facts_rows", lambda conn, rows: captured.extend(rows) or len(rows))
    if sb_stub is not None:
        monkeypatch.setattr(W, "_verify_shadbala", sb_stub)
    if av_stub is not None:
        monkeypatch.setattr(W, "_verify_ashtakavarga", av_stub)
    # one ayanamsha is enough for the wiring check (the 5 are structurally identical)
    first = next(iter(W.CANONICAL_AYANAMSHAS.items()))
    monkeypatch.setattr(W, "CANONICAL_AYANAMSHAS", dict([first]))
    summary = W.build_ga_strength("chart-q03-not-canonical", "build-q03", conn=_FakeConn(),
                                  birth_params=dict(NATIVE_BIRTH))
    return summary, captured


def test_build_wiring_applies_each_verifier_tier_to_its_own_examined_rows(monkeypatch):
    summary, rows = _run_build(monkeypatch)
    assert summary["two_pass_verified"] is False  # honest: nothing here earns two_pass_verified
    by = _by_cat(rows)
    for cat in _SHADBALA_EXAMINED:
        non_node = [r for r in rows if r["fact_category"] == cat and r["fact_subject"] not in _NODES
                    and r["fact_key"] == "rupa"]
        assert {r["verification_pass_status"] for r in non_node} == {T.CLASSICAL_MATCH}, cat
    for cat in _AV_EXAMINED:
        assert set(by[cat]) == {T.CLASSICAL_MATCH}
    assert T.TWO_PASS_VERIFIED not in {r["verification_pass_status"] for r in rows}
    assert "floored_sarva_mismatch" not in {r["verification_pass_status"] for r in rows}
    allowed = _constraint_members()
    assert {r["verification_pass_status"] for r in rows} <= allowed
    for r in rows:  # the writer's real insert choke point calls exactly this
        T.emit_tier(r["verification_pass_status"], table="chart_facts")


def test_build_mutant_stubbed_verifiers_drop_the_examined_rows(monkeypatch):
    _, rows = _run_build(monkeypatch, sb_stub=lambda sb, tolerance=0.02: T.UNVERIFIED_DEFAULT,
                         av_stub=lambda bav, tolerance=2: T.UNVERIFIED_DEFAULT)
    assert T.CLASSICAL_MATCH not in {r["verification_pass_status"] for r in rows}


def test_build_halts_when_a_verifier_raises(monkeypatch):
    def boom(*a, **k):
        raise W.TwoPassVerificationError("forced")
    with pytest.raises(W.TwoPassVerificationError):
        _run_build(monkeypatch, av_stub=boom)
