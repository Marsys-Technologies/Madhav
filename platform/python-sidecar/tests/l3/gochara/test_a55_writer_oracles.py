"""A5.5 frozen test oracles — registered writer architecture + grain plateau
(GOCHARA_DESIGN_SPECS_v1_4 §10, §2.3 inv 4).

O-RW-1, O-RW-2, O-RW-3, O-GR-PLATEAU against the REAL production seams:
  * convention vector / convention_id (gochara_kernel.convention,
    gochara_kernel.ledger.convention_id_for) — O-RW-1(b)'s "contacts rebuilt
    under a new convention_id";
  * the kernel CoverageRecord honesty invariants (gochara_kernel.coverage)
    — O-RW-2's no-window coverage object;
  * the publication manifest lifecycle (gochara_kernel.ledger
    publish_candidate / PublishedGenerationRefusal) driven through a stub
    conn so the PRODUCTION branch logic executes — O-RW-3.

Where the oracle's 'then' has no production output to assert on, the test is
a strict-xfail FINDING (GENERAL RULE: no test-side re-implementation).
"""
from __future__ import annotations

import pytest

from services.gochara_kernel.convention import (
    CONVENTION_VECTOR, SPECIAL_DRISHTI_DEG, canonical_convention_id,
)
from services.gochara_kernel.coverage import CoverageRecord
from services.gochara_kernel.ledger import (
    PublishedGenerationRefusal, convention_id_for, publish_candidate,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class _Cur:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _ManifestConn:
    """Stub conn over the manifest table only: returns the pinned manifest
    row for SELECTs, records every DML call. The production branch logic in
    publish_candidate executes for real."""

    def __init__(self, manifest_row):
        self._row = manifest_row
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        low = sql.lower()
        if "insert into kala_gochara_publication" in low:
            return _Cur(("manifest-new-1",))
        if "from kala_gochara_publication" in low:
            return _Cur(self._row)
        raise AssertionError(f"unexpected SQL against stub: {sql}")


# ── O-RW-1 (§10; defects lineage, S-02) — dependency-driven invalidation ────
def test_o_rw_1_geometry_change_yields_new_convention_id_valence_cannot():
    # the pinned canonical convention id is stable and reproducible
    cid0 = canonical_convention_id()
    assert cid0 == canonical_convention_id()
    assert cid0 == convention_id_for(CONVENTION_VECTOR)

    # (b) an aspect-direction change is a GEOMETRY change: the convention
    # vector the id is computed over names the geometry conventions, and a
    # vector carrying altered geometry digests to a DIFFERENT convention_id
    # (contacts must be rebuilt under it — the id is the rebuild key).
    altered = dict(CONVENTION_VECTOR, ayanamsha="lahiri_chitrapaksha_v2_aspect_fix")
    assert convention_id_for(altered) != cid0
    # a missing geometry key is REFUSED, never silently digested
    incomplete = {k: v for k, v in CONVENTION_VECTOR.items() if k != "house_system"}
    with pytest.raises(ValueError):
        convention_id_for(incomplete)

    # (a) a valence-rule / weight change is NOT geometry: the digest input is
    # exactly the pinned geometry-vector keys — no valence, weight or path
    # field can enter the convention_id (a valence change therefore CANNOT
    # mint a new convention id and must never re-solve).
    assert set(CONVENTION_VECTOR) == {
        "zodiac", "ayanamsha", "sidereal_method", "node_model", "node_source",
        "epoch_convention", "time_scale", "house_system", "ephemeris_mode",
    }
    for non_geometry in ("valence_rule", "factor_weight", "path_algebra",
                         "evidence_weight"):
        assert non_geometry not in CONVENTION_VECTOR

    # the aspect-direction geometry itself is pinned (N-14: nodes cast
    # nothing — the S-02 aspect fix is live in the production table)
    assert SPECIAL_DRISHTI_DEG["Rahu"] == [] and SPECIAL_DRISHTI_DEG["Ketu"] == []
    assert SPECIAL_DRISHTI_DEG["Saturn"] == [60.0, 180.0, 270.0]


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.3 writer): NO production solver-invocation "
           "counter exists on the window path, and no dependency-driven "
           "invalidation API records 're-solve vs re-score, and why' (§10.1 "
           "'the writer records which fired and why'). grep over services/ "
           "finds no invocation counter and no invalidation writer. spec "
           "§10/O-RW-1(a) + the invalidation half of (b).")
def test_o_rw_1_solver_invocation_counter_and_invalidation_record():
    # (a) a valence rule changes ⇒ the solver is NOT invoked: the oracle
    # requires the counter itself asserted, not digests alone.
    from services.gochara_kernel import ledger as _ledger
    counter = getattr(_ledger, "solver_invocation_count", None)
    assert callable(counter), "no production solver-invocation counter"
    before = counter()
    # a valence-only change must leave the counter untouched and the windows
    # re-evaluated with new lineage; a geometry change must record the
    # invalidation with its dependency reason
    invalidation = getattr(_ledger, "invalidate_dependent_windows", None)
    assert callable(invalidation), "no production dependency-driven invalidation"
    assert counter() == before


# ── O-RW-2 (§10; defects §N.6, coverage-honesty) — coverage on no-window ────
def test_o_rw_2_no_window_answer_carries_coverage_object():
    # a no-window answer: zero resolved targets, ALL requested unresolved,
    # the searched horizon and relations named, an honest unsearched reason,
    # the unavailable inputs listed — the record constructs and carries all
    # four coverage content fields.
    cov = CoverageRecord(
        chart_id=CHART_ID, generation="5.0",
        partition_kind="event_class", partition_key="marriage",
        requested_horizon=(2460310.5, 2460675.5),
        completed_horizon=(2460310.5, 2460310.5),
        resolution_arcsec=60.0,
        relations_searched=("conjunction", "aspect", "residence"),
        targets_requested=4, targets_resolved=0, targets_unresolved=4,
        target_resolution_state_counts={"unavailable": 4},
        unavailable_inputs={"ashtakavarga_build": "absent"},
        unsearched_reason="no kala_gochara_coverage rows for this horizon",
        convention_id=canonical_convention_id(),
        ephemeris_backend={"backend": "swisseph", "version": "2.10"},
    )
    assert cov.targets_resolved == 0 and cov.targets_unresolved == 4
    assert cov.relations_searched and cov.unsearched_reason
    assert cov.unavailable_inputs["ashtakavarga_build"] == "absent"

    # mutation probes — a BARE 'no windows' fails the production invariants:
    # resolved + unresolved != requested raises…
    with pytest.raises(ValueError):
        CoverageRecord(
            chart_id=CHART_ID, generation="5.0",
            partition_kind="event_class", partition_key="marriage",
            requested_horizon=(2460310.5, 2460675.5),
            completed_horizon=(2460310.5, 2460310.5),
            resolution_arcsec=60.0, relations_searched=("conjunction",),
            targets_requested=4, targets_resolved=0, targets_unresolved=3,
            target_resolution_state_counts={"unavailable": 3},
            unavailable_inputs={},
            unsearched_reason="x",
            convention_id=canonical_convention_id(), ephemeris_backend={},
        )
    # …state counts not summing to targets_unresolved raises…
    with pytest.raises(ValueError):
        CoverageRecord(
            chart_id=CHART_ID, generation="5.0",
            partition_kind="event_class", partition_key="marriage",
            requested_horizon=(2460310.5, 2460675.5),
            completed_horizon=(2460310.5, 2460310.5),
            resolution_arcsec=60.0, relations_searched=("conjunction",),
            targets_requested=4, targets_resolved=0, targets_unresolved=4,
            target_resolution_state_counts={"unavailable": 2},
            unavailable_inputs={}, unsearched_reason="x",
            convention_id=canonical_convention_id(), ephemeris_backend={},
        )
    # …and a completed horizon DISJOINT from the requested one with NO
    # unsearched_reason (the silent bare answer) raises
    with pytest.raises(ValueError):
        CoverageRecord(
            chart_id=CHART_ID, generation="5.0",
            partition_kind="event_class", partition_key="marriage",
            requested_horizon=(2460310.5, 2460675.5),
            completed_horizon=(2459945.5, 2459945.5),
            resolution_arcsec=60.0, relations_searched=("conjunction",),
            targets_requested=4, targets_resolved=4, targets_unresolved=0,
            target_resolution_state_counts={},
            unavailable_inputs={}, unsearched_reason=None,
            convention_id=canonical_convention_id(), ephemeris_backend={},
        )


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.3 serving): the served window set does NOT "
           "count confirmed vs context rows separately — grep over "
           "ka_gochara/service.py finds no 'confirmed' count on the serving "
           "path; EpisodeBatch carries episodes + coverage only (§N.6 "
           "separate-count requirement unmet). spec §10/O-RW-2.")
def test_o_rw_2_window_set_counts_confirmed_vs_context_separately():
    from services.ka_gochara import service as _svc
    batch_fields = {f for f in dir(_svc.EpisodeBatch) if not f.startswith("_")}
    assert any("confirmed" in f for f in batch_fields), (
        "EpisodeBatch carries no confirmed-vs-context count")


# ── O-RW-3 (§10; defects N-10, D-41) — manifest provenance & republish ──────
def test_o_rw_3_provenance_names_ka_gochara_republish_from_manifest():
    # provenance: a fresh candidate manifest is written BY ka_gochara — the
    # writer_asset_id goes into the INSERT as a BOUND PARAMETER (never
    # string-matched from a branch name), defaulting to 'ka_gochara'.
    conn = _ManifestConn(manifest_row=None)
    manifest_id = publish_candidate(
        conn, CHART_ID, "5.0", canonical_convention_id(),
        {"input": "vector"}, {"backend": "swisseph"}, "[2026-01-01,2027-01-01)")
    assert manifest_id == "manifest-new-1"
    inserts = [c for c in conn.calls
               if "insert into kala_gochara_publication" in c[0].lower()]
    assert len(inserts) == 1
    sql, params = inserts[0]
    # the writer asset id is bound, not interpolated into the SQL text
    assert "ka_gochara" not in sql
    assert params[2] == "ka_gochara"

    # republish under a NEW label with no code change passes from the
    # manifest alone (a fresh candidate row for the new generation label)
    conn2 = _ManifestConn(manifest_row=None)
    assert publish_candidate(
        conn2, CHART_ID, "5.1", canonical_convention_id(),
        {"input": "vector"}, {"backend": "swisseph"},
        "[2026-01-01,2027-01-01)") == "manifest-new-1"

    # mutation probe: a rebuild under the SAME label after publication is
    # REFUSED by the manifest status — provenance is the manifest row, not
    # a string match on the label
    conn3 = _ManifestConn(manifest_row=("manifest-pub-1", "published"))
    with pytest.raises(PublishedGenerationRefusal) as exc:
        publish_candidate(
            conn3, CHART_ID, "5.0", canonical_convention_id(),
            {"input": "vector"}, {"backend": "swisseph"},
            "[2026-01-01,2027-01-01)")
    assert "NEW generation label" in str(exc.value)


# ── O-GR-PLATEAU (§2.3 inv 4; defects #24, E5) — grain lineage ──────────────
@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.3 writer lineage): served era/month/day "
           "rows carry NO lineage naming the grain-operating path — grep "
           "over gochara_v3/engine.py + ka_gochara_sweep finds peak_basis "
           "(precision vocabulary) but no per-row grain-path lineage, so "
           "'day rows trace only to P6' and the clipped-era-curve month-row "
           "flag (the 27-of-41 plateau shape) have no production output to "
           "assert on. spec §2.3 inv 4/O-GR-PLATEAU.")
def test_o_gr_plateau_grain_lineage_and_clipped_curve_flag():
    from services.gochara_v3 import engine as _engine
    emitter = getattr(_engine, "row_lineage", None)
    assert callable(emitter), "no production per-row grain lineage"
    # a month row whose boundaries and monotone-inherited score are a clipped
    # era curve must be flagged; day rows must trace only to P6
    month_row = emitter(grain="month", boundaries="identical-to-era",
                        score="monotone-inherited")
    assert month_row["clipped_era_curve"] is True
    day_row = emitter(grain="day")
    assert day_row["path"] == "P6"
