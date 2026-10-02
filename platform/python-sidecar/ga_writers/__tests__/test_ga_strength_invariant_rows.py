"""ga_strength emits each ayanamsha-INVARIANT row once per build (TI-l1-writer-fixes-001).

Data-plane rehearsal finding: ``ga_strength`` reported 17,075 rows but the protected capture held
17,039 distinct row identities (``complete_l1_data_plane_partition``: "reported 17075 rows but
protected capture contains 17039").  Root cause, measured here with the REAL writer on a SYNTHETIC
chart: the ayanamsha-invariant rows (naisargika bala for 9 grahas, required shadbala rupa for 7)
were rebuilt inside EVERY ayanamsha batch, so 16 natural keys were emitted 5 times each (64
surplus rows).  The ``ON CONFLICT DO UPDATE`` upsert silently collapsed them to one stored row per
key while ``rows_inserted`` counted all five; the ``required_rupa`` rows additionally hashed their
``fact_id`` from the batch's live ayanamsha, so the one stored row carried five different
identities across the build (the capture kept all five, 28 of them phantom).
"""
from __future__ import annotations

import collections
import hashlib

import pytest

import ga_writers.ga_strength_writer as gs
from ga_writers._row_uniqueness import DuplicateNaturalKeyError, assert_unique_natural_keys
from ga_writers.ga_strength_writer import CANONICAL_AYANAMSHAS, build_ga_strength
from pyjhora_adapter.compute import compute_chart

CHART = "aaaaaaaa-1111-4222-8333-000000000001"  # synthetic: not a real chart id
BUILD = "bbbbbbbb-1111-4222-8333-000000000001"
SYNTHETIC_BP = {
    "datetime_iso": "1991-07-19T06:20:00",
    "latitude_deg": 18.52,
    "longitude_deg": 73.86,
    "tz_offset_hours": 5.5,
    "place_name": "synthetic",
    "subject_label": "syn",
}
_SUBJECT = {
    "Lagna": "LAGNA", "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
}
INVARIANT_CATEGORIES = {"graha_shadbala_naisargika"}


class _Result:
    rowcount = 0

    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchall(self):
        return self._rows


class _Cursor:
    def __init__(self, sink):
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def executemany(self, _sql, rows):
        self._sink.append(list(rows))

    def execute(self, *a, **k):
        return _Result()


class _FakeConn:
    """Serves the chart_divisionals reads from the adapter's own vargas; records every upsert batch."""

    def __init__(self, vargas):
        self._vargas = vargas
        self.batches: list[list[dict]] = []

    def cursor(self, *a, **k):
        return _Cursor(self.batches)

    def execute(self, sql, params=None):
        if "FROM chart_divisionals" not in sql:
            return _Result()
        _chart, _aya, varga = params
        out = []
        for g in self._vargas.get(varga, []):
            code = _SUBJECT.get(g["name"])
            if code is None:
                continue
            if "'varga_position'" in sql:
                out.append((f"{varga}.{code}", g["sign_id"]))
            else:
                out.append((f"{varga}.{code}", "neutral"))
        return _Result(out)


@pytest.fixture(scope="module")
def build():
    vargas = compute_chart(inputs=SYNTHETIC_BP, ayanamsha_id="lahiri")["vargas"]
    conn = _FakeConn(vargas)
    summary = build_ga_strength(CHART, BUILD, conn=conn, birth_params=SYNTHETIC_BP)
    return summary, conn.batches


def _natural_key(row):
    return (row["chart_id"], row["ayanamsha_id"], row["fact_category"],
            row["fact_subject"], row["fact_key"], row["build_id"])


def test_one_batch_per_canonical_ayanamsha(build):
    _summary, batches = build
    assert len(batches) == len(CANONICAL_AYANAMSHAS)


def test_no_natural_key_is_emitted_twice_in_a_build(build):
    _summary, batches = build
    counts = collections.Counter(_natural_key(r) for b in batches for r in b)
    repeated = {k[2:5]: n for k, n in counts.items() if n > 1}
    assert not repeated, f"natural keys emitted more than once in one build: {repeated}"


def test_reported_rows_equal_distinct_row_identities(build):
    """The exact equality complete_l1_data_plane_partition enforces (reported == distinct captured
    row_identity, which for chart_facts is fact_id)."""
    summary, batches = build
    rows = [r for b in batches for r in b]
    assert summary["total_chart_facts_rows"] == len(rows)
    assert len({r["fact_id"] for r in rows}) == summary["total_chart_facts_rows"]


def test_invariant_rows_are_emitted_in_the_first_batch_only(build):
    _summary, batches = build
    for index, batch in enumerate(batches):
        invariant = [r for r in batch if r["ayanamsha_id"] == "INVARIANT"]
        if index == 0:
            assert {r["fact_category"] for r in invariant} == {
                "graha_shadbala_naisargika", "graha_shadbala_total"}
            # 9 grahas of naisargika + 7 classical required_rupa
            assert len(invariant) == 16
        else:
            assert invariant == []


def test_required_rupa_fact_id_is_hashed_from_the_stored_ayanamsha(build):
    """fact_id must be derived from the SAME ayanamsha the row is stored under."""
    _summary, batches = build
    rows = [r for b in batches for r in b
            if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa"]
    assert len(rows) == 7
    for r in rows:
        expected = hashlib.sha256(
            f"graha_shadbala_total|{r['fact_subject']}|required_rupa|{CHART}|INVARIANT".encode()
        ).hexdigest()[:16]
        assert r["ayanamsha_id"] == "INVARIANT"
        assert r["fact_id"] == expected


def test_ayanamsha_dependent_rows_still_emitted_for_every_ayanamsha(build):
    """The fix must not thin the ayanamsha-dependent rows: every batch carries the ratio rows."""
    _summary, batches = build
    for batch in batches:
        ratios = [r for r in batch if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "ratio"]
        assert len(ratios) == 7


def test_single_batch_call_still_returns_the_complete_invariant_set():
    """Default emit_invariant=True keeps a direct call (and every existing caller) complete."""
    shadbala = {
        g: {"sthana": 1.0, "dig": 1.0, "kala": 1.0, "cheshta": 1.0, "naisargika": 1.0,
            "drik": 1.0, "total": 6.0}
        for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    }
    args = (shadbala, {}, {}, CHART, BUILD, "raman", "2026-01-01T00:00:00+00:00", "test", "two_pass_verified")
    full = gs._build_shadbala_rows(*args)
    thin = gs._build_shadbala_rows(*args, emit_invariant=False)
    dropped = [r for r in full if r not in thin]
    assert {r["ayanamsha_id"] for r in dropped} == {"INVARIANT"}
    assert len(dropped) == 16
    assert all(r["ayanamsha_id"] != "INVARIANT" for r in thin)


# ── the general guard ───────────────────────────────────────────────────────

def _row(subject="SUN", key="rupa", ayanamsha="raman", fact_id="f1", category="c"):
    return {"chart_id": CHART, "ayanamsha_id": ayanamsha, "fact_category": category,
            "fact_subject": subject, "fact_key": key, "build_id": BUILD, "fact_id": fact_id}


def test_guard_rejects_a_repeated_key_within_a_batch_and_names_it():
    with pytest.raises(DuplicateNaturalKeyError, match=r"fact_subject.*SUN.*fact_key.*rupa"):
        assert_unique_natural_keys([_row(fact_id="a"), _row(fact_id="b")], context="unit")


def test_guard_rejects_a_key_repeated_across_batches():
    seen: dict = {}
    assert assert_unique_natural_keys([_row()], seen) == 1
    with pytest.raises(DuplicateNaturalKeyError, match="duplicate natural key"):
        assert_unique_natural_keys([_row()], seen)


def test_guard_rejects_one_fact_id_naming_two_keys():
    with pytest.raises(DuplicateNaturalKeyError, match="names two natural keys"):
        assert_unique_natural_keys([_row(subject="SUN"), _row(subject="MOON")])


def test_guard_accepts_distinct_keys():
    rows = [_row(subject=s, fact_id=s) for s in ("SUN", "MOON", "MAR")]
    assert assert_unique_natural_keys(rows) == 3


def test_build_fails_loudly_if_an_invariant_row_is_re_emitted(monkeypatch):
    """Mutation guard: re-introducing the per-batch emission must raise, naming the key, before any
    row is written -- not surface later as 'reported N rows but protected capture contains M'."""
    real = gs._build_shadbala_rows

    def always_emit(*args, **kwargs):
        kwargs["emit_invariant"] = True
        return real(*args, **kwargs)

    monkeypatch.setattr(gs, "_build_shadbala_rows", always_emit)
    vargas = compute_chart(inputs=SYNTHETIC_BP, ayanamsha_id="lahiri")["vargas"]
    conn = _FakeConn(vargas)
    with pytest.raises(DuplicateNaturalKeyError, match="INVARIANT"):
        build_ga_strength(CHART, BUILD, conn=conn, birth_params=SYNTHETIC_BP)
    assert len(conn.batches) == 1  # the first batch landed; the second was refused before its write


# ── through the real registered writer + the data-plane runtime boundary ─────────────────────

class _CaptureCursor(_Cursor):
    def __init__(self, conn):
        super().__init__(conn.batches)
        self._owner = conn

    def execute(self, sql, params=None):
        if "complete_l1_data_plane_partition" in sql:
            self._owner.reported = params[-1]
            # The protected capture keeps one revision per DISTINCT fact_id (chart_facts row identity),
            # including identities a later upsert overwrote (the 28 phantom versions).
            captured = len({r["fact_id"] for b in self._owner.batches for r in b})
            if self._owner.reported != captured:
                raise RuntimeError(
                    f"L1 partition {params[3]} reported {self._owner.reported} rows but protected "
                    f"capture contains {captured}"
                )
        return _Result()


class _BoundaryConn(_FakeConn):
    _l1_contract_test_double = True

    def __init__(self, vargas):
        super().__init__(vargas)
        self.reported = None

    def cursor(self, *a, **k):
        return _CaptureCursor(self)


def _run_registered_writer():
    from pipeline.orchestrator.writers import ContextSpec, discover_all, list_writers

    discover_all()
    vargas = compute_chart(inputs=SYNTHETIC_BP, ayanamsha_id="lahiri")["vargas"]
    conn = _BoundaryConn(vargas)
    ctx = ContextSpec(
        asset_id="ga_strength", build_id=BUILD, db_conn=conn,
        config={"chart_id": CHART, "birth_params": SYNTHETIC_BP},
    )
    result = list_writers()["ga_strength"]().run(ctx)  # raises on a reported != captured partition
    return result, conn


def test_registered_writer_partition_completes_reported_equals_captured():
    result, conn = _run_registered_writer()
    stored = {_natural_key(r) for b in conn.batches for r in b}
    assert result.rows_inserted == conn.reported == len(stored) == 17011
    assert len({r["fact_id"] for b in conn.batches for r in b}) == 17011


def test_mutation_emitting_invariant_rows_every_pass_fails_the_partition(monkeypatch):
    """Fix 1 reverted (the guard bypassed so the real boundary is what fails): 80 INVARIANT emissions
    for 16 stored rows -> reported 17,075 against 17,011 captured."""
    real = gs._build_shadbala_rows

    def always_emit(*args, **kwargs):
        kwargs["emit_invariant"] = True
        return real(*args, **kwargs)

    monkeypatch.setattr(gs, "_build_shadbala_rows", always_emit)
    monkeypatch.setattr(gs, "assert_unique_natural_keys", lambda *a, **k: 0)
    with pytest.raises(RuntimeError, match=r"reported 17075 rows but protected capture contains 17011"):
        _run_registered_writer()


def test_mutation_both_fixes_reverted_reproduces_the_rehearsal_failure(monkeypatch):
    """The original code: every pass emits AND required_rupa hashes the loop ayanamsha ->
    'reported 17075 rows but protected capture contains 17039' (the 28 phantom versions)."""
    real = gs._build_shadbala_rows

    def original(*args, **kwargs):
        kwargs["emit_invariant"] = True
        rows = real(*args, **kwargs)
        loop_ayanamsha = args[5]
        for r in rows:
            if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa":
                r["fact_id"] = hashlib.sha256(
                    f"graha_shadbala_total|{r['fact_subject']}|required_rupa|{CHART}|{loop_ayanamsha}".encode()
                ).hexdigest()[:16]
        return rows

    monkeypatch.setattr(gs, "_build_shadbala_rows", original)
    monkeypatch.setattr(gs, "assert_unique_natural_keys", lambda *a, **k: 0)
    with pytest.raises(RuntimeError, match=r"reported 17075 rows but protected capture contains 17039"):
        _run_registered_writer()


def test_mutation_fact_id_hashed_from_the_loop_ayanamsha_changes_the_identity(monkeypatch):
    """Fix 2 reverted alone: counts still agree (one emission), but the stored identity is no longer
    derived from the stored ayanamsha -- the stable-id test above is the detector."""
    real = gs._build_shadbala_rows

    def loop_hash(*args, **kwargs):
        rows = real(*args, **kwargs)
        for r in rows:
            if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa":
                r["fact_id"] = hashlib.sha256(
                    f"graha_shadbala_total|{r['fact_subject']}|required_rupa|{CHART}|{args[5]}".encode()
                ).hexdigest()[:16]
        return rows

    monkeypatch.setattr(gs, "_build_shadbala_rows", loop_hash)
    _result, conn = _run_registered_writer()
    rupa = [r for b in conn.batches for r in b
            if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa"]
    stable = hashlib.sha256(
        f"graha_shadbala_total|{rupa[0]['fact_subject']}|required_rupa|{CHART}|INVARIANT".encode()
    ).hexdigest()[:16]
    assert rupa[0]["fact_id"] != stable
