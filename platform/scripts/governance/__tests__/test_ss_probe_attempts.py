"""test_ss_probe_attempts.py -- SS 2026-10-05 `probe_attempts`: a writer-less service names the (asset, run) pairs that are its orchestrator health-probe runs; the census verifies each named run
still has the probe shape in the live rows (state complete, empty disposition, a receipt whose build_id is the run with output_digest_spec_sha256 NULL and receipt_state unknown) and that the asset has
no NON-PROBE build_run_assets row (a later orchestrated probe is tolerated). Then Earn.build_record reads N/A by a checked declaration; otherwise FAIL (or NO_DETECTOR where nothing could be established). Offline: fake rows, no database.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_ss_rd_service_static as rd  # noqa: E402

NA, FAIL, ND = ac.NA, ac.FAIL, ac.NO_DET
RUN = "cd79def6-c40d-42c5-9414-7d40895bac5c"
RUN2 = "759b43c7-b2d6-40a9-b9ef-8d1987ac898d"
OTHER = "11111111-2222-4333-8444-555555555555"
EVID = "platform/python-sidecar/pipeline/orchestrator/asset_runner.py:971"
PA = dict(attempts=[dict(run_id=RUN)], why="the service's only build_run_assets row is the orchestrator's health-probe run: a probe is not a build", evidence=EVID)
BLOCK = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])


def row(run=RUN, state="complete", disposition="", started=True, ep=100.0):
    return dict(run_id=run, state=state, disposition=disposition, started=started, created_epoch=ep)


def rcpt(build=RUN, spec_null=True, state="unknown"):
    return dict(build_id=build, spec_null=spec_null, receipt_state=state)


def grade(rows, receipts, pa=PA, block=BLOCK, kind="service"):
    return ac.grade_probe_attempts(pa, rows, receipts, block, kind)


# ───────────── the checked reading ─────────────

def test_the_probe_shape_with_no_other_row_reads_na_by_a_checked_declaration():
    g = grade([row()], [rcpt()])
    assert g["v"] == NA and g["cause"] == "declared-probe-runs-verified" and "declared probe runs verified against live rows" in g["measured"], g
    assert g["no_writer"]["verified"] is True and g["no_writer"]["probe_attempts"] is True and g["no_writer"]["service"] is True and g["no_writer"]["runs"] == [RUN], g


def test_an_extra_build_row_on_the_asset_fails():
    g = grade([row(), row(OTHER, disposition="build")], [rcpt()])
    assert g["v"] == FAIL and "non-probe build_run_assets row" in g["measured"] and OTHER[:8] in g["measured"] and g["no_writer"]["verified"] is False, g


def test_a_later_probe_shaped_extra_row_is_tolerated_and_counted():
    g = grade([row(), row(OTHER, ep=200.0)], [rcpt(), rcpt(OTHER)])
    assert g["v"] == NA and g["no_writer"]["tolerated_probe_runs"] == 1 and "1 later probe-shaped run(s) tolerated" in g["measured"], g


def test_a_later_probe_row_whose_receipt_was_overwritten_by_an_equal_or_newer_probe_is_tolerated():
    three = "33333333-2222-4333-8444-555555555555"
    g = grade([row(), row(OTHER, ep=200.0), row(three, ep=300.0)], [rcpt(), rcpt(three)])      # OTHER's receipt was upserted away by `three`'s
    assert g["v"] == NA, g


def test_an_extra_complete_row_with_no_receipt_and_no_newer_probe_receipt_fails():
    g = grade([row(), row(OTHER, ep=200.0)], [rcpt()])
    assert g["v"] == FAIL and OTHER[:8] in g["measured"] and "no receipt that proves it a probe" in g["measured"], g


def test_an_extra_row_older_than_a_probe_receipt_is_tolerated_and_one_newer_than_every_receipt_is_not():
    assert grade([row(OTHER, ep=50.0), row()], [rcpt()])["v"] == NA                  # RUN's probe receipt is newer than OTHER, so it could have overwritten OTHER's
    assert grade([row(OTHER, ep=500.0), row()], [rcpt()])["v"] == FAIL               # OTHER is NEWER than the only receipt and has none: nothing proves it a probe


def test_an_extra_row_whose_own_receipt_is_not_the_probe_shape_fails():
    g = grade([row(), row(OTHER, ep=200.0)], [rcpt(), rcpt(OTHER, spec_null=False)])
    assert g["v"] == FAIL and "not the probe shape" in g["measured"], g


def test_the_validator_caps_named_attempts_at_one_per_asset():
    assert ac.PROBE_MAX_ATTEMPTS == 1
    with pytest.raises(ac.DeclarationsError, match="1 to 1"):
        ac.validate_declarations(_doc(dict(PA, attempts=[dict(run_id=RUN), dict(run_id=RUN2)])))


@pytest.mark.parametrize("extra", [row(OTHER, state="queued", started=False), row(OTHER, state="error"), row(OTHER, disposition="skip_no_delta"), row(OTHER, disposition="probe_green")])
def test_any_other_row_whatever_its_state_or_disposition_fails(extra):
    assert grade([row(), extra], [rcpt()])["v"] == FAIL


def test_a_changed_disposition_on_the_named_row_fails():
    g = grade([row(disposition="build")], [rcpt()])
    assert g["v"] == FAIL and "disposition is 'build', not empty" in g["measured"], g
    assert grade([row(disposition="skip_no_delta")], [rcpt()])["v"] == FAIL


@pytest.mark.parametrize("state", ["error", "aborted", "building", "queued"])
def test_a_named_row_that_is_not_complete_fails(state):
    g = grade([row(state=state)], [rcpt()])
    assert g["v"] == FAIL and "not complete" in g["measured"], g


def test_a_missing_receipt_fails():
    g = grade([row()], [])
    assert g["v"] == FAIL and "has no provenance receipt" in g["measured"], g
    g = grade([row()], [rcpt(build="99999999-2222-4333-8444-555555555555")])   # a receipt naming a run that is not on the asset is not this run's and overwrites nothing of the asset's
    assert g["v"] == FAIL and "has no provenance receipt" in g["measured"], g


def test_a_named_runs_receipt_overwritten_by_a_newer_probe_receipt_is_no_detector_not_fail_and_not_a_release():
    g = grade([row(), row(OTHER, ep=200.0)], [rcpt(OTHER)])
    assert g["v"] == ND and "overwrote it" in g["measured"] and g["no_writer"]["verified"] is False, g
    g = grade([row(), row(OTHER, ep=200.0)], [rcpt(OTHER, spec_null=False)])             # the newer receipt is NOT a probe: nothing explains the loss
    assert g["v"] == FAIL, g
    g = grade([row(ep=300.0), row(OTHER, ep=200.0)], [rcpt(OTHER)])                       # the other run is OLDER than the named run: it could not have overwritten the named receipt
    assert g["v"] == FAIL, g


def test_a_destroyed_receipt_beside_a_non_probe_contradiction_still_fails():
    g = grade([row(), row(OTHER, ep=200.0), row("33333333-2222-4333-8444-555555555555", disposition="build", ep=300.0)], [rcpt(OTHER)])
    assert g["v"] == FAIL, g


def test_a_receipt_that_is_not_the_probe_shape_fails():
    assert "not the probe shape" in grade([row()], [rcpt(spec_null=False)])["measured"]                  # an output-digest spec is present: a writer build's receipt
    assert grade([row()], [rcpt(state="proven")])["v"] == FAIL
    assert grade([row()], [rcpt(state="")])["v"] == FAIL
    assert grade([row()], [rcpt(spec_null=False), rcpt()])["v"] == FAIL                                # ALL receipts of a named run must be probe-shaped, not any
    assert grade([row()], [rcpt(), rcpt(state="proven")])["v"] == FAIL


def test_a_named_run_absent_from_the_rows_fails_and_says_so():
    g = grade([row(OTHER)], [])
    assert g["v"] == FAIL and "ABSENT" in g["measured"] and RUN[:8] in g["measured"], g
    assert grade([], [])["v"] == FAIL                                                                    # no row at all: the named run is absent


def test_an_unnamed_row_and_an_absent_named_run_are_both_reported():
    g = grade([row(OTHER, disposition="build")], [])
    assert g["v"] == FAIL and "ABSENT" in g["measured"] and "not named" in g["measured"], g


def test_unreadable_rows_are_no_detector_not_a_release_and_not_a_fail():
    g = grade(None, None)
    assert g["v"] == ND and "could not be read" in g["measured"], g


@pytest.mark.parametrize("kind", ["data", "", None])
def test_a_registry_kind_that_is_not_service_establishes_nothing(kind):
    g = grade([row()], [rcpt()], kind=kind)
    assert g["v"] == ND and "not `service`" in g["measured"], g


@pytest.mark.parametrize("mut", [dict(declared=False), dict(registry_has_writer=True), dict(register_files=1), dict(register_mentions=["w.py"])])
def test_without_the_agreeing_no_writer_block_the_declaration_does_not_apply(mut):
    assert grade([row()], [rcpt()], block=dict(BLOCK, **mut)) is None


# ───────────── the declaration: validator ─────────────

def _doc(pa, **entry):
    e = {"kind": "service", "has_writer": False, "probe_attempts": pa}
    e.update(entry)
    return dict(version="x", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_s": e})


def test_a_well_formed_declaration_validates_and_the_doc_field_list_is_checked():
    ac.validate_declarations(_doc(json.loads(json.dumps(PA))))
    doc = _doc(json.loads(json.dumps(PA)))
    doc["probe_attempts_declaration_fields"] = ["attempts", "why"]
    with pytest.raises(ac.DeclarationsError, match="probe_attempts_declaration_fields"):
        ac.validate_declarations(doc)


@pytest.mark.parametrize("entry", [dict(kind="data"), dict(kind="static"), dict(has_writer=True), dict(has_writer=None)])
def test_a_probe_attempts_declaration_on_an_asset_with_a_writer_or_another_kind_is_refused(entry):
    doc = _doc(json.loads(json.dumps(PA)), **entry)
    if entry.get("has_writer") is None:
        doc["assets"]["bg_s"].pop("has_writer")
    with pytest.raises(ac.DeclarationsError, match="writer-less service only"):
        ac.validate_declarations(doc)


@pytest.mark.parametrize("patch,match", [
    (dict(attempts=[]), "attempts"),
    (dict(attempts=None), "attempts"),
    (dict(attempts=[dict(run_id="not-a-uuid")]), "attempts"),
    (dict(attempts=[dict(run_id=RUN.upper())]), "attempts"),
    (dict(attempts=[dict(run_id=RUN, extra=1)]), "attempts"),
    (dict(attempts=[dict(run_id=RUN), dict(run_id=RUN)]), "distinct"),
    (dict(attempts=[dict(run_id=f"{i:08x}-2222-4333-8444-555555555555") for i in range(2)]), "1 to"),
    (dict(attempts=[RUN]), "attempts"),
    (dict(why="short"), "why"),
    (dict(evidence="unverified:the production rows show it"), "evidence"),
    (dict(evidence="platform/nope.py:1"), "evidence"),
    (dict(extra="x"), "unknown field"),
])
def test_a_malformed_probe_attempts_declaration_is_refused(patch, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(dict(PA, **patch)))


# ───────────── rollup guard, rule row, cause ─────────────

def test_the_rule_row_the_cause_and_the_guard():
    assert "declared-probe-runs-verified" in ac.NA_CAUSES["Earn.build_record"]
    assert ac.NA_RULE_DECISIONS["Earn.build_record#measured:declared-probe-runs-verified"].startswith("SS 2026-10-05 probe_attempts")
    assert ac.NO_WRITER_CAUSES["Earn.build_record"] == ("no-writer-registry-agrees", "declared-probe-runs-verified")


def test_a_forged_probe_record_is_not_released():
    good = grade([row()], [rcpt()])
    assert ac.no_writer_na_problem("Earn.build_record", good) is None
    assert ac.rollup_asset("L0", {"Earn.build_record": good})["Earn"]["checks"][0]["v"] == NA
    for drop in ("probe_attempts", "verified", "service", "runs"):
        forged = dict(good, no_writer={k: v for k, v in good["no_writer"].items() if k != drop})
        assert ac.no_writer_na_problem("Earn.build_record", forged), drop
        assert ac.rollup_asset("L0", {"Earn.build_record": forged})["Earn"]["checks"][0]["v"] == ND, drop
    for k, bad in (("verified", False), ("runs", []), ("register_files", 1), ("declared", False)):
        assert ac.no_writer_na_problem("Earn.build_record", dict(good, no_writer=dict(good["no_writer"], **{k: bad}))), k


# ───────────── the live read ─────────────

def test_the_live_read_selects_every_row_and_every_receipt_of_the_asset(monkeypatch):
    seen = []

    def fake(sql, *a, **k):
        seen.append(sql)
        return [[RUN, "complete", "", "t", "100.5"]] if "build_run_assets" in sql else [[RUN, "t", "unknown"]]
    monkeypatch.setattr(ac, "psql", fake)
    rows, rc = ac.probe_attempt_rows("bg_ephemeris_engine")
    assert rows == [row(ep=100.5)] and rc == [rcpt()], (rows, rc)
    assert any("FROM build_run_assets" in q and "a.asset_id = 'bg_ephemeris_engine'" in q and "started_at IS NULL" not in q and "WHERE a.started_at" not in q for q in seen), seen   # no started-only filter
    assert any("asset_provenance_receipts" in q and "p.asset_id = 'bg_ephemeris_engine'" in q for q in seen)


def test_a_ragged_live_read_is_unknown_not_an_index_error(monkeypatch):
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["48"]])
    with pytest.raises(ac.Unknown, match="did not parse"):
        ac.probe_attempt_rows("bg_ephemeris_engine")


@pytest.mark.parametrize("bad", ["x'; DROP TABLE t; --", "Bg_x", "", "1abc", "a b"])
def test_the_live_read_refuses_a_non_plain_asset_id(monkeypatch, bad):
    monkeypatch.setattr(ac, "psql", lambda *a, **k: pytest.fail("must not run"))
    with pytest.raises(ac.Unknown, match="not a plain asset id"):
        ac.probe_attempt_rows(bad)


# ───────────── measure() wiring ─────────────

def _measure(monkeypatch, tmp_path, rows, receipts, *, kind="service", decl=None, writer=False, raises=False, raises_other=False):
    aid = rd.SVC
    reg = {aid: rd._row(aid, kind, has_writer=writer)}
    d = {aid: {"kind": "service", "has_writer": False, "probe_attempts": decl or PA}}
    rd._stub(monkeypatch, tmp_path, reg, d)

    def fake_rows(a):
        if raises:
            raise ac.Unknown("psql down")
        if raises_other:
            raise RuntimeError("unexpected")
        return rows, receipts
    monkeypatch.setattr(ac, "probe_attempt_rows", fake_rows)
    monkeypatch.setattr(ac, "build_attempt_log", lambda prefix, ids=None: {aid: [dict(scope="chart", state="complete", disposition="", when="2026-08-27", error="", started=True, epoch=1.0, receipt=True)]})
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    return rd._cells(ac.measure("L0"), aid)["Earn.build_record"]


def test_measure_verified_declaration_reads_na_with_the_new_cause(monkeypatch, tmp_path):
    c = _measure(monkeypatch, tmp_path, [row()], [rcpt()])
    assert c["v"] == NA and c["cause"] == "declared-probe-runs-verified" and "declared probe runs verified against live rows" in c["measured"], c
    assert ac.rollup_asset("L0", {"Earn.build_record": c})["Earn"]["checks"][0]["v"] == NA


def test_measure_an_extra_row_a_changed_row_or_an_absent_run_fail(monkeypatch, tmp_path):
    assert _measure(monkeypatch, tmp_path, [row(), row(OTHER, disposition="build")], [rcpt()])["v"] == FAIL
    c = _measure(monkeypatch, tmp_path, [row(), row(OTHER, ep=200.0)], [rcpt(), rcpt(OTHER)])              # a later probe is tolerated
    assert c["v"] == NA and c["cause"] == "declared-probe-runs-verified", c
    assert _measure(monkeypatch, tmp_path, [row(), row(OTHER, ep=200.0)], [rcpt(OTHER)])["v"] == ND         # overwritten receipt: nothing to verify, nothing contradicted
    assert _measure(monkeypatch, tmp_path, [row(disposition="build")], [rcpt()])["v"] == FAIL
    assert _measure(monkeypatch, tmp_path, [row()], [])["v"] == FAIL
    assert _measure(monkeypatch, tmp_path, [row(OTHER)], [])["v"] == FAIL


def test_measure_an_unreadable_read_is_no_detector_and_a_non_service_registry_kind_does_not_release(monkeypatch, tmp_path):
    assert _measure(monkeypatch, tmp_path, None, None, raises=True)["v"] == ND
    assert _measure(monkeypatch, tmp_path, [row()], [rcpt()], kind="data")["v"] == ND
    assert _measure(monkeypatch, tmp_path, None, None, raises_other=True)["v"] == ND                          # any read failure degrades this cell only


def test_without_a_probe_attempts_declaration_the_ordinary_reading_stands(monkeypatch, tmp_path):
    aid = rd.SVC
    rd._stub(monkeypatch, tmp_path, {aid: rd._row(aid, "service")}, {aid: {"kind": "service", "has_writer": False}})
    monkeypatch.setattr(ac, "probe_attempt_rows", lambda a: pytest.fail("no declaration: the live rows are not read"))
    c = rd._cells(ac.measure("L0"), aid)["Earn.build_record"]
    assert c.get("cause") != "declared-probe-runs-verified", c


# ───────────── the real declarations ─────────────

def test_the_two_real_services_declare_exactly_the_runs_the_evidence_names():
    d = ac.load_asset_declarations()
    assert d["bg_ephemeris_engine"]["probe_attempts"]["attempts"] == [dict(run_id=RUN)]
    assert d["bg_panchanga"]["probe_attempts"]["attempts"] == [dict(run_id=RUN2)]
    assert sorted(a for a, e in d.items() if "probe_attempts" in e) == ["bg_ephemeris_engine", "bg_panchanga"]
    assert all(d[a]["kind"] == "service" and d[a]["has_writer"] is False for a in ("bg_ephemeris_engine", "bg_panchanga"))
