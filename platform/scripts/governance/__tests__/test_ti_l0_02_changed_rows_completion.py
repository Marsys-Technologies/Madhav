"""TI-L0-02 (Track I, L0 INDEX section 8, SS Q1 option A, R, PROVISIONAL until the J1 review): Build.completion
for a converged rerun.

A converged L0 rerun legitimately reports `rows_written = 0` (the writers upsert conditionally and report only
changed rows). The rule, decided by SS 2026-10-01 (Q1): `rows_written = 0` against a populated table reads
Build.completion PASS ONLY IF (1) the asset's declaration states the changed-rows convention with a writer
`file:line`, AND (2) Build.count_integrity PASSes (count_sql and integrity_check_sql both registered) AND (3) the
table is populated at or above its declared floor (Count.floor PASS). Completion is then proven by the count, not
by `rows_written`. Every other path is unchanged: no declaration, a live count below the floor, no integrity SQL,
no positive floor, a non-completed build record, or `rows_written` > 0 but different from live all stay FAIL.

The declaration is an optional entry key `rows_written_convention` = {convention: "changed_rows", why, evidence}.
No asset declares it yet (TI-L0-01 owns the declarations file), so on the real data this change is inert until
TI-L0-01 lands; the validator below is what keeps a later declaration honest.

Same offline `measure()` harness as test_r99_empty_table_agreeing_build_record.py.
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

AID = "bg_conv"
TABLE = "bg_conv_rows"
EVIDENCE = "platform/python-sidecar/brahmagyan/l0_ontology.py:1115"
DECL = dict(convention="changed_rows",
            why="conditional upsert leaves exact rows untouched, so a converged rerun reports 0 changed rows",
            evidence=EVIDENCE)


def _reg_row(has_integrity=True, floor="100"):
    return dict(asset_id=AID, has_writer=True, target_table=TABLE,
                count_sql=f"SELECT count(*) FROM {TABLE}", has_integrity=has_integrity, depends_on=[],
                target_floor=floor, catalog_status="CURRENT", asset_kind="data")


def _stub_layer(monkeypatch, ctrl, reg, live, rec, declarations):
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={TABLE}, cols={TABLE: ["id", "v"]},
                                                       keys={TABLE: []}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: live for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(rec)} for aid in reg})
    monkeypatch.setattr(ac, "build_history",
                        lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=live, full=[], never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: copy.deepcopy(declarations))


_REC = dict(state="lit", rows_written="0", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False,
            _key=(0.0, 0.0), built_epoch="0", duration=None)


def _completion(monkeypatch, tmp_path, *, live=500, rw="0", state="lit", floor="100", has_integrity=True,
                declaration=DECL):
    decls = {AID: dict(kind="data", rows_written_convention=declaration)} if declaration is not None else {}
    _stub_layer(monkeypatch, tmp_path, {AID: _reg_row(has_integrity, floor)}, live,
                dict(_REC, rows_written=rw, state=state), decls)
    census = ac.measure("L0")
    return next(a for a in census["assets"] if a["asset_id"] == AID)["measurements"]["Build.completion"]


# ───────────────────────────── the verdict rule ─────────────────────────────

def test_declared_convention_with_count_integrity_and_floor_reads_pass(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path)
    assert res["v"] == ac.PASS, res
    assert "changed_rows" in res["measured"] and EVIDENCE in res["measured"], res
    assert "live=500" in res["measured"] and "floor=100" in res["measured"], res


def test_undeclared_zero_rows_written_still_fails(monkeypatch, tmp_path):
    """The key test: without the declaration `rows_written = 0` against a populated table is still FAIL."""
    res = _completion(monkeypatch, tmp_path, declaration=None)
    assert res["v"] == ac.FAIL, res
    assert "rows_written=0 against live=500" in res["measured"], res


def test_declared_but_live_below_floor_fails(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path, live=50)
    assert res["v"] == ac.FAIL, res
    assert "floor" in res["measured"], res


def test_declared_but_no_integrity_sql_fails(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path, has_integrity=False)
    assert res["v"] == ac.FAIL, res
    assert "count_integrity" in res["measured"], res


@pytest.mark.parametrize("floor", [None, "0", "many"])
def test_declared_without_a_positive_whole_number_floor_fails(monkeypatch, tmp_path, floor):
    """A floor of 0 cannot be breached and no floor is no claim: neither proves the table is populated."""
    res = _completion(monkeypatch, tmp_path, floor=floor)
    assert res["v"] == ac.FAIL, res


def test_declared_but_build_record_not_completed_still_fails(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path, state="error")
    assert res["v"] == ac.FAIL and "is not a completed build" in res["measured"], res


def test_declared_with_positive_rows_written_that_disagrees_with_live_still_fails(monkeypatch, tmp_path):
    """Option A is scoped to `rows_written = 0`; a positive figure that disagrees with live is not rescued."""
    res = _completion(monkeypatch, tmp_path, rw="7")
    assert res["v"] == ac.FAIL and "disagrees" in res["measured"], res


def test_declared_convention_does_not_touch_the_agreeing_positive_path(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path, rw="500")
    assert res["v"] == ac.PASS and "rows_written=500 = live=500" in res["measured"], res


def test_declared_convention_does_not_change_the_empty_table_path(monkeypatch, tmp_path):
    res = _completion(monkeypatch, tmp_path, live=0, floor="100")
    assert res["v"] == ac.FAIL and "empty: live=0" in res["measured"], res


def _with_integrity(monkeypatch, tmp_path, outcome):
    reg_row = dict(_reg_row(), integrity_sql="SELECT true")
    decls = {AID: dict(kind="data", rows_written_convention=DECL)}
    _stub_layer(monkeypatch, tmp_path, {AID: reg_row}, 500, dict(_REC), decls)
    monkeypatch.setattr(ac, "_integrity_outcome", lambda sql: dict(outcome, sha="abc123abc123", secs=0.0))
    return next(a for a in ac.measure("L0")["assets"] if a["asset_id"] == AID)["measurements"]["Build.completion"]


def test_the_released_pass_still_goes_through_the_n99_integrity_guard_holds(monkeypatch, tmp_path):
    res = _with_integrity(monkeypatch, tmp_path, dict(state="holds", detail="true"))
    assert res["v"] == ac.PASS and "changed_rows" in res["measured"] and "integrity_check_sql holds" in res["measured"], res


def test_the_released_pass_is_not_a_pass_when_the_declared_integrity_sql_does_not_hold(monkeypatch, tmp_path):
    """N-99 applies to this PASS too: counts proven, integrity SQL false -> PARTIAL, never PASS."""
    res = _with_integrity(monkeypatch, tmp_path, dict(state="fails", detail="false"))
    assert res["v"] == ac.PARTIAL and "does NOT hold" in res["measured"], res


# ───────────────────────────── the declaration validator ─────────────────────────────

def _doc(entry):
    return dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS), assets={AID: entry})


def _validate(rwc):
    return ac.validate_declarations(_doc(dict(kind="data", rows_written_convention=rwc)))


def test_validator_accepts_a_well_formed_declaration():
    assert _validate(dict(DECL))[AID]["rows_written_convention"]["evidence"] == EVIDENCE


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(convention="rows_updated"),                  # option B is not the decided convention
    lambda d: d.update(convention=None),
    lambda d: d.pop("why"),
    lambda d: d.update(why="  "),
    lambda d: d.update(why="two\nlines"),
    lambda d: d.pop("evidence"),
    lambda d: d.update(evidence="platform/python-sidecar/brahmagyan/l0_ontology.py"),            # no :LINE
    lambda d: d.update(evidence="platform/python-sidecar/brahmagyan/does_not_exist.py:3"),
    lambda d: d.update(evidence="platform/python-sidecar/brahmagyan/l0_ontology.py:99999999"),   # beyond the file
    lambda d: d.update(evidence="platform/scripts/governance/__tests__/test_r99_empty_table_agreeing_build_record.py:10"),
    lambda d: d.update(evidence="platform/migrations/1094_asset_throughput_duration.sql:1"),      # not writer code
    lambda d: d.update(extra="x"),
])
def test_validator_refuses_a_malformed_declaration(mutate):
    d = dict(DECL)
    mutate(d)
    with pytest.raises(ac.DeclarationsError):
        _validate(d)


def test_validator_refuses_a_non_object():
    with pytest.raises(ac.DeclarationsError):
        _validate("changed_rows")
