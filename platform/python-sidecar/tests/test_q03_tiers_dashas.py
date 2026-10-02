"""
test_q03_tiers_dashas.py -- Q03 / SS N-62 honest tiers for chart_dashas (TD-MUD, TD-NAR, TD-VIM).

  * SS tier rule (S-L1 follow-up): `classical_match` ONLY where the check compares against a classical
    reference table or constant the value could fail; `two_pass_verified` ONLY for a second
    implementation compared with a tolerance; a bounds / plausibility / same-arithmetic / tautological
    membership check earns `single`.
  * mudda keeps `classical_match` (the varsha-1 lord is compared with the transcribed nakshatra ->
    natal-lord -> varsha-lord table chain, which the value can fail; plus a 9-year periodicity
    invariant), applied by build_system's post-pass ONLY to the rows the verifier reads
    (level_n == 1, kp_sublevel None); every other row is `single`.
  * narayana (non-overlap ordering = bounds) and yogini / ashtottari / chara_karaka / naisargika
    (lord membership in the very table the producer draws from = tautology) earn `single`; the build
    still halts on an overlap / unknown lord.
  * Vimshottari keeps `two_pass_verified`, per row, from `_apply_vimshottari_independent_verification`
    (a separate Julian-day closed-form rebuild, discrimination-tested). If that call is skipped,
    every Vimshottari row must read `single` -- the row builders no longer pre-stamp the top tier.

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §3 / §5.
"""
from __future__ import annotations

import copy
import os
import pathlib
import pickle
import sys
from datetime import date

import pytest
import swisseph as swe

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from brahmagyan import verification_tiers as T
from ga_writers import ga_dashas_writer as W

MOON = 325.5  # Purva Bhadrapada (FORENSIC)
BIRTH_JD = swe.julday(1984, 2, 5, 5.21667)
BP = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245,
      "tz_offset_hours": 5.5, "place_name": "Bhubaneswar", "subject_label": "native"}
AYA = "lahiri"
CHART = W.CANONICAL_CHART_ID


def _row_cache(name, build):
    """Compute-once helper. `Q03_DASHAS_ROW_CACHE=<dir>` (a developer convenience for repeated
    mutation runs; unset in CI) pickles the engines' raw output so a mutant re-run does not pay the
    ~4 minute engine time again. The cache holds RAW compute-stage rows only."""
    d = os.environ.get("Q03_DASHAS_ROW_CACHE")
    if d:
        f = pathlib.Path(d) / f"{name}.pkl"
        if f.exists():
            return pickle.loads(f.read_bytes())
    value = build()
    if d:
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)
        (pathlib.Path(d) / f"{name}.pkl").write_bytes(pickle.dumps(value))
    return value


@pytest.fixture(scope="module")
def raw_mudda():
    """The REAL compute_mudda_system output, computed ONCE (the engines are slow; the verifiers and
    the post-pass under test are real, only the row SOURCE is cached)."""
    return _row_cache("mudda", lambda: W.compute_mudda_system(BIRTH_JD, AYA, CHART, "b"))


@pytest.fixture(scope="module")
def raw_vim():
    def build():
        rows = W.compute_vimshottari(MOON, BIRTH_JD, AYA, CHART, "b")
        return rows, W.compute_kp_subperiods(rows, CHART, "b", AYA)

    return _row_cache("vim", build)


def _cached(rows):
    """A fresh deep copy of cached engine rows on every call (the post-pass mutates rows)."""
    return lambda *a, **k: copy.deepcopy(rows)


def _build_capturing(monkeypatch, system_id, *, patch_compute=None):
    """Run the REAL build_system (skip_db) and capture the rows after the verification post-pass."""
    captured: dict = {}
    real = W.stabilize_hierarchical_uuids

    def spy(rows, **kw):
        captured["rows"] = rows
        return real(rows, **kw)

    monkeypatch.setattr(W, "stabilize_hierarchical_uuids", spy)
    monkeypatch.setattr(W, "_get_moon_position", lambda aya, birth=None: (MOON, BIRTH_JD))
    if patch_compute:
        for name, fn in patch_compute.items():
            monkeypatch.setattr(W, name, fn)
    result = W.build_system(system_id, AYA, CHART, birth_params=BP, skip_db=True)
    return result, captured["rows"]


def _examined(r):
    return r["level_n"] == 1 and r.get("kp_sublevel") is None


# ── TD-MUD ────────────────────────────────────────────────────────────────────


def test_verify_mudda_agreeing_is_classical_match_not_tpv(raw_mudda):
    rows = copy.deepcopy(raw_mudda)
    assert W._verify_mudda(rows, 24) == T.CLASSICAL_MATCH  # nakshatra 25 (0-based 24)
    assert W._verify_mudda(rows) == T.CLASSICAL_MATCH  # periodicity invariant only
    assert W._verify_mudda(rows, 24) != T.TWO_PASS_VERIFIED


def test_verify_mudda_wrong_varsha1_lord_halts(raw_mudda):
    rows = copy.deepcopy(raw_mudda)
    l1 = sorted((r for r in rows if r["level_n"] == 1), key=lambda r: r["start_date"])
    l1[0]["lord_graha"] = "Rahu" if l1[0]["lord_graha"] != "Rahu" else "Ketu"
    with pytest.raises(ValueError, match="varsha-1 year-lord"):
        W._verify_mudda(rows, 24)


def test_verify_mudda_non_9_year_cycle_halts(raw_mudda):
    rows = copy.deepcopy(raw_mudda)
    l1 = sorted((r for r in rows if r["level_n"] == 1), key=lambda r: r["start_date"])
    assert len(l1) > 10
    l1[9]["lord_graha"] = "Rahu" if l1[9]["lord_graha"] != "Rahu" else "Ketu"
    with pytest.raises(ValueError, match="not 9-year cyclic"):
        W._verify_mudda(rows)


def test_mudda_build_stamps_classical_match_only_on_examined_rows(monkeypatch, raw_mudda):
    result, rows = _build_capturing(monkeypatch, "mudda",
                                    patch_compute={"compute_mudda_system": _cached(raw_mudda)})
    assert result["verification"] == T.CLASSICAL_MATCH
    ex = [r for r in rows if _examined(r)]
    rest = [r for r in rows if not _examined(r)]
    assert ex and rest
    assert {r["verification_pass_status"] for r in ex} == {T.CLASSICAL_MATCH}
    assert {r["verification_pass_status"] for r in rest} == {T.SINGLE}


def test_mudda_stubbed_verifier_mutant_drops_examined_rows_to_single(monkeypatch, raw_mudda):
    """MUTANT: the verifier stubbed to return without checking/earning anything."""
    _, rows = _build_capturing(
        monkeypatch, "mudda", patch_compute={
            "compute_mudda_system": _cached(raw_mudda),
            "_verify_mudda": lambda rows, idx=None: T.UNVERIFIED_DEFAULT})
    assert {r["verification_pass_status"] for r in rows} == {T.SINGLE}


# ── TD-NAR ────────────────────────────────────────────────────────────────────


def _nar_rows():
    return [
        {"level_n": 1, "lord_graha": "Aries", "start_date": date(2000, 1, 1), "end_date": date(2010, 1, 1)},
        {"level_n": 1, "lord_graha": "Taurus", "start_date": date(2010, 1, 1), "end_date": date(2020, 1, 1)},
    ]


def test_verify_narayana_non_overlap_is_single_not_classical_match_or_tpv():
    got = W._verify_narayana(_nar_rows())
    assert got == T.SINGLE and got not in {T.CLASSICAL_MATCH, T.TWO_PASS_VERIFIED}


def test_verify_narayana_overlap_halts():
    rows = _nar_rows()
    rows[0]["end_date"] = date(2015, 1, 1)
    with pytest.raises(ValueError, match="overlapping MD periods"):
        W._verify_narayana(rows)


def test_narayana_build_rows_are_all_single(monkeypatch):
    """Drive the real post-pass for system_id == narayana with a patched row source (the real
    narayana engine needs a DB connection); the verifier and the post-pass are the real ones."""
    def fake_narayana(birth_jd, ayanamsha_id, chart_id, build_id, conn=None):
        return W.compute_naisargika_system(birth_jd, ayanamsha_id, chart_id, build_id)

    result, rows = _build_capturing(monkeypatch, "narayana",
                                    patch_compute={"compute_narayana_system": fake_narayana})
    assert result["verification"] == T.SINGLE
    assert rows and {r["verification_pass_status"] for r in rows} == {T.SINGLE}


def test_narayana_hardcoded_tier_mutant_is_caught(monkeypatch):
    """MUTANT (hard-coded tier): `_verify_narayana` that ignores overlapping periods still returns
    a passing tier -> the overlap-halts test above would fail on it."""
    monkeypatch.setattr(W, "_verify_narayana", lambda rows: T.SINGLE)
    rows = _nar_rows()
    rows[0]["end_date"] = date(2015, 1, 1)
    assert W._verify_narayana(rows) == T.SINGLE  # mutant masks the violation


def test_mutant_classical_match_narayana_is_visible(monkeypatch):
    """MUTANT (the pre-ruling behaviour): a narayana verifier returning classical_match is exactly what
    the single-tier tests above reject."""
    monkeypatch.setattr(W, "_verify_narayana", lambda rows: T.CLASSICAL_MATCH)
    assert W._verify_narayana(_nar_rows()) == T.CLASSICAL_MATCH != T.SINGLE


# ── membership-only verifiers (yogini / ashtottari / chara / naisargika): tautology -> single ─────────


def _l1(lord):
    return [{"level_n": 1, "lord_graha": lord, "start_date": date(2000, 1, 1), "end_date": date(2001, 1, 1)}]


def test_membership_verifiers_return_single_and_still_halt_on_an_unknown_lord():
    known = {
        "yogini": (W._verify_yogini, W.YOGINI_SEQUENCE[0][0]),
        "ashtottari": (W._verify_ashtottari, W.ASHTOTTARI_LORDS_ORDER[0]),
        "chara": (W._verify_chara, "Aries"),
        "naisargika": (W._verify_naisargika, W.NAISARGIKA_SEQUENCE[0][0]),
    }
    for name, (fn, lord) in known.items():
        assert fn(_l1(lord)) == T.SINGLE, name
        if name in {"ashtottari", "chara"}:
            assert fn([]) == T.SINGLE, name  # nothing examined -> nothing earned
        with pytest.raises(ValueError):
            fn(_l1("Not-A-Lord"))


def test_mutant_membership_verifier_returning_classical_match_is_visible(monkeypatch):
    monkeypatch.setattr(W, "_verify_yogini", lambda rows: T.CLASSICAL_MATCH)
    assert W._verify_yogini(_l1("x")) != T.SINGLE


# ── TD-VIM ────────────────────────────────────────────────────────────────────


def test_vimshottari_rows_two_pass_verified_per_row_via_the_real_write_path(monkeypatch, raw_vim):
    vim, kp = raw_vim
    _, rows = _build_capturing(monkeypatch, "vimshottari", patch_compute={
        "compute_vimshottari": _cached(vim), "compute_kp_subperiods": lambda *a, **k: copy.deepcopy(kp)})
    l14 = [r for r in rows if r["level_n"] in (1, 2, 3, 4) and r.get("kp_sublevel") is None]
    assert l14
    assert {r["verification_pass_status"] for r in l14} == {T.TWO_PASS_VERIFIED}
    kp_rows = [r for r in rows if r.get("kp_sublevel") is not None]
    assert kp_rows and {r["verification_pass_status"] for r in kp_rows} == {T.SINGLE}


def test_vimshottari_swapped_lord_is_divergent_flagged_in_the_real_write_path(monkeypatch, raw_vim):
    vim, _kp = raw_vim

    def corrupted(*a, **k):
        rows = copy.deepcopy(vim)
        l1 = [r for r in rows if r["level_n"] == 1]
        idx = W.VIMSHOTTARI_SEQUENCE.index(l1[1]["lord_graha"])
        l1[1]["lord_graha"] = W.VIMSHOTTARI_SEQUENCE[(idx + 1) % 9]
        return rows

    _, rows = _build_capturing(monkeypatch, "vimshottari", patch_compute={
        "compute_vimshottari": corrupted, "compute_kp_subperiods": lambda *a, **k: []})
    statuses = [r["verification_pass_status"] for r in rows
                if r["level_n"] == 1 and r.get("kp_sublevel") is None]
    assert T.DIVERGENT_FLAGGED in statuses
    assert statuses.count(T.TWO_PASS_VERIFIED) >= 1  # per-row, not a chart-wide broadcast


def test_vimshottari_skipping_the_independent_verifier_drops_every_row_to_single(monkeypatch, raw_vim):
    """MUTANT (TD-VIM): skip `_apply_vimshottari_independent_verification`. The row builders no
    longer pre-stamp `two_pass_verified`, so with the verifier skipped NOTHING can read verified."""
    vim, kp = raw_vim
    _, rows = _build_capturing(
        monkeypatch, "vimshottari",
        patch_compute={"compute_vimshottari": _cached(vim),
                       "compute_kp_subperiods": lambda *a, **k: copy.deepcopy(kp),
                       "_apply_vimshottari_independent_verification": lambda rows, moon, jd: 0})
    assert T.TWO_PASS_VERIFIED not in {r["verification_pass_status"] for r in rows}
    assert {r["verification_pass_status"] for r in rows} == {T.SINGLE}


def test_compute_stage_rows_are_never_pre_stamped_verified(raw_vim, raw_mudda):
    """The row builders emit the honest default; tiers are applied only after a verifier ran."""
    vim, kp = raw_vim
    for rows in (vim, kp, raw_mudda):
        assert {r["verification_pass_status"] for r in rows} == {T.SINGLE}


def test_every_tier_the_dashas_post_pass_emits_passes_emit_tier_for_chart_dashas(monkeypatch, raw_mudda, raw_vim):
    """chart_dashas has the narrow CHECK vocabulary (RESTRICTED_TABLE_VOCAB): classical_match, single,
    two_pass_verified must all be accepted by emit_tier(table='chart_dashas'); the l1 tajik table has no
    restriction."""
    _, mudda = _build_capturing(monkeypatch, "mudda", patch_compute={"compute_mudda_system": _cached(raw_mudda)})
    vim, kp = raw_vim
    _, vrows = _build_capturing(monkeypatch, "vimshottari", patch_compute={
        "compute_vimshottari": _cached(vim), "compute_kp_subperiods": lambda *a, **k: copy.deepcopy(kp)})
    tiers = {r["verification_pass_status"] for r in mudda + vrows}
    assert {T.CLASSICAL_MATCH, T.SINGLE, T.TWO_PASS_VERIFIED} <= tiers
    for t in tiers:
        T.emit_tier(t, table="chart_dashas")
    T.emit_tier(T.CLASSICAL_MATCH, table="l1_tajik_varsha_year_lords")
