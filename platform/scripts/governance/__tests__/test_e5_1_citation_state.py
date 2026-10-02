"""test_e5_1_citation_state.py — E5.1 record_version 2: `citation_state` on a certification record (SS N-74).

What a source-correspondence PASS rests on is part of what the certificate says. For Carr.D1 and Ldgr.source_presence
the writer reads `citation_state` (sourced | sourced_ocr_unverified | unsourced | refuted) FROM THE CENSUS CELL, never
from the caller (a caller value is only a cross-check that must equal it). Rules, each tested in both directions:
  * a PASS whose state is not `sourced` is a real PASS: it is written, with that state and `citation_state_caveat: true`;
  * `unsourced` / `refuted` with a PASS verdict is REFUSED (the census caps those at NO_DETECTOR);
  * any other criterion, and every addition, has citation_state null; a typed value there is refused;
  * citation_state is a CURRENCY field: a change of state is a new generation, an unchanged one appends nothing;
  * record_version is 2 on new records; v1 records (a ledger written by the E5.1 that is on main) stay readable, read as
    `citation_state: null` / not declared, and new v2 records chain onto them;
  * the reader checks a v2 record's field against the same rules (a hand edit cannot smuggle an inconsistent one).

Offline: the harness of test_e5_1_certify.py (tmp repo, committed census files, tmp ledgers).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402
from test_e5_1_certify import (  # noqa: E402,F401  (fixtures + helpers of the E5.1 suite)
    ENV, FP, FP2, RUN, W1, W2, WH, commit_all, cert_in_repo, doctor, env, fresh_repo, kw, ledger, lines, refused,
    session_repo, write_census_file,
)

LDGR = "Ldgr.source_presence"
D1 = "Carr.D1"
STATES = ("sourced", "sourced_ocr_unverified", "unsourced", "refuted")
CITE_COLS = ["id", "source_citation"]            # a recognised citation column: Ldgr.source_presence applies


@pytest.fixture(params=[LDGR, D1])
def crit(request, monkeypatch):
    """Both criteria the rule covers. Carr.D1 has detector NONE on today's registry (S2 builds it): give it one here, the
    way S2's registry will."""
    if request.param == D1:
        reg = dict(ac.CRITERION_REGISTRY)
        reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
        monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    return request.param


def req(ledger, crit, state=..., verdict="PASS", **over):
    """A request for `crit` whose census cell carries `state` (`...`: the cell carries none)."""
    cell = {} if state is ... else dict(citation_state=state)
    return kw(ledger, criterion=crit, verdict=verdict, cell=dict(cell, v=verdict) if verdict else cell,
              rec=dict(target_columns=CITE_COLS), **over)


def write(ledger, crit, state=..., verdict="PASS", **over):
    return nc.write_certification(**req(ledger, crit, state, verdict, **over))


# ───────────────────────── the record carries the field, record_version is 2 ─────────────────────────

def test_new_records_are_record_version_2_and_every_record_carries_both_fields(ledger):
    rec = nc.write_certification(**kw(ledger)).record                       # Build.registered: not a citation criterion
    assert nc.RECORD_VERSION == 2 and rec["record_version"] == 2
    assert rec["citation_state"] is None and rec["citation_state_caveat"] is False
    assert lines(ledger)[1]["record_version"] == 2


def test_citation_state_is_a_currency_field():
    assert "citation_state" in nc.CURRENCY_FIELDS


# ───────────────────────── the census cell supplies it ─────────────────────────

def test_a_sourced_pass_is_recorded_with_its_state_and_no_caveat(ledger, crit):
    rec = write(ledger, crit, "sourced").record
    assert rec["verdict"] == "PASS" and rec["citation_state"] == "sourced" and rec["citation_state_caveat"] is False
    assert rec["record_version"] == 2


def test_an_ocr_unverified_pass_is_a_real_pass_stored_with_the_caveat(ledger, crit):
    rec = write(ledger, crit, "sourced_ocr_unverified").record
    assert rec["verdict"] == "PASS" and rec["citation_state"] == "sourced_ocr_unverified"
    assert rec["citation_state_caveat"] is True
    assert lines(ledger)[1] == rec                                          # and it is what was appended


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_an_unsourced_or_refuted_pass_is_refused_and_nothing_is_written(ledger, crit, state):
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, crit, state)
    assert ei.value.code == "citation_state_pass_refused" and ledger.read_bytes() == before


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_the_same_states_are_recordable_on_no_detector_without_a_caveat(ledger, crit, state):
    rec = write(ledger, crit, state, "NO_DETECTOR").record
    assert rec["verdict"] == "NO_DETECTOR" and rec["citation_state"] == state and rec["citation_state_caveat"] is False


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_ldgr_partial_keeps_an_unsourced_or_refuted_state_but_carr_d1_partial_refuses_it(ledger, state):
    rec = write(ledger, LDGR, state, "PARTIAL").record                              # Ldgr: lenient, no caveat (not a PASS)
    assert rec["verdict"] == "PARTIAL" and rec["citation_state"] == state and rec["citation_state_caveat"] is False


def test_a_failing_ldgr_cell_keeps_its_state_too(ledger):
    rec = write(ledger, LDGR, "refuted", "FAIL").record
    assert rec["verdict"] == "FAIL" and rec["citation_state"] == "refuted" and rec["citation_state_caveat"] is False


def test_an_ldgr_pass_whose_census_cell_carries_no_state_is_stored_null_with_the_caveat_while_the_legacy_path_is_open(ledger):
    assert nc.LDGR_NULL_STATE_WRITE_ALLOWED is True                                  # today: the census does not emit it yet
    rec = write(ledger, LDGR, ...).record
    assert rec["verdict"] == "PASS" and rec["citation_state"] is None and rec["citation_state_caveat"] is True


@pytest.mark.parametrize("verdict", ["PASS", "PARTIAL"])
def test_a_carr_d1_pass_or_partial_with_no_state_in_the_cell_is_refused(ledger, monkeypatch, verdict):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, D1, ..., verdict)
    assert ei.value.code == "citation_state_missing" and ledger.read_bytes() == before


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_a_carr_d1_partial_with_an_unsourced_or_refuted_state_is_refused(ledger, monkeypatch, state):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, D1, state, "PARTIAL")
    assert ei.value.code == "citation_state_partial_refused" and ledger.read_bytes() == before


@pytest.mark.parametrize("state", ["sourced", "sourced_ocr_unverified"])
def test_a_carr_d1_partial_with_a_sourced_state_is_recordable_without_a_caveat(ledger, monkeypatch, state):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    rec = write(ledger, D1, state, "PARTIAL").record
    assert rec["verdict"] == "PARTIAL" and rec["citation_state"] == state and rec["citation_state_caveat"] is False


# ───────────────────────── the legacy lenient Ldgr write path (SS ruling (b)) ─────────────────────────

def test_the_legacy_ldgr_path_is_a_single_module_constant_and_closing_it_refuses_a_null_state_ldgr_pass(ledger, monkeypatch):
    monkeypatch.setattr(nc, "LDGR_NULL_STATE_WRITE_ALLOWED", False)
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, LDGR, ...)
    assert ei.value.code == "citation_state_missing" and ledger.read_bytes() == before
    # a state in the cell still writes, a non-PASS still writes, other criteria are untouched
    assert write(ledger, LDGR, "sourced").record["citation_state_caveat"] is False
    assert write(ledger, LDGR, "sourced_ocr_unverified", asset="bg_other").record["citation_state_caveat"] is True
    assert write(ledger, LDGR, ..., "NO_DETECTOR", asset="bg_third").record["citation_state"] is None
    assert nc.write_certification(**kw(ledger, criterion="Build.contract")).record["citation_state"] is None


def test_records_written_while_the_legacy_path_was_open_stay_readable_after_it_closes(ledger, monkeypatch):
    legacy = write(ledger, LDGR, ...).record                                         # null state + caveat true
    monkeypatch.setattr(nc, "LDGR_NULL_STATE_WRITE_ALLOWED", False)
    r = nc.read_ledger(ledger)["bg_ontology|gate|Ldgr.source_presence"][0]            # reading is not gated by the constant
    assert r["citation_state"] is None and r["citation_state_caveat"] is True and r["cert_id"] == legacy["cert_id"]
    assert write(ledger, LDGR, "sourced").record["generation"] == 2                   # and a new state supersedes it
    assert [x["citation_state"] for x in nc.parse_records(ledger.read_bytes())] == [None, "sourced"]


def test_the_reader_accepts_a_null_state_ldgr_pass_whatever_the_constant_says(ledger, monkeypatch):
    write(ledger, LDGR, ...)
    for value in (True, False):
        monkeypatch.setattr(nc, "LDGR_NULL_STATE_WRITE_ALLOWED", value)
        assert nc.read_ledger(ledger)["bg_ontology|gate|Ldgr.source_presence"][0]["citation_state_caveat"] is True


def test_the_constant_does_not_loosen_carr_d1(ledger, monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    for value in (True, False):
        monkeypatch.setattr(nc, "LDGR_NULL_STATE_WRITE_ALLOWED", value)
        with pytest.raises(nc.CertificationRefused) as ei:
            write(ledger, D1, ...)
        assert ei.value.code == "citation_state_missing"


@pytest.mark.parametrize("bad", ["maybe", "", "SOURCED", "Sourced", 5, True, ["sourced"], {"s": 1}])
def test_a_cell_state_outside_the_vocabulary_is_refused(ledger, crit, bad):
    refused(ledger, "bad_citation_state", **{k: v for k, v in req(ledger, crit, bad).items() if k != "ledger_path"})


# ───────────────────────── a caller value is only a cross-check ─────────────────────────

def test_a_caller_value_equal_to_the_census_cell_is_accepted(ledger, crit):
    assert write(ledger, crit, "sourced", citation_state="sourced").record["citation_state"] == "sourced"


@pytest.mark.parametrize("cell_state,typed", [("sourced_ocr_unverified", "sourced"), ("sourced", "sourced_ocr_unverified"),
                                              ("unsourced", "sourced"), ("sourced", "refuted")])
def test_a_caller_value_that_differs_from_the_census_cell_is_refused(ledger, crit, cell_state, typed):
    verdict = "NO_DETECTOR" if cell_state == "unsourced" else "PASS"
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, crit, cell_state, verdict, citation_state=typed)
    assert ei.value.code == "citation_state_conflict" and ledger.read_bytes() == before


def test_a_caller_value_cannot_supply_what_the_census_cell_does_not_carry(ledger, crit):
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, crit, ..., citation_state="sourced")                     # the cell has none: the caller cannot add one
    assert ei.value.code == "citation_state_conflict" and ledger.read_bytes() == before


@pytest.mark.parametrize("bad", ["maybe", "", 5, True, ["sourced"]])
def test_a_malformed_caller_value_is_refused(ledger, crit, bad):
    with pytest.raises(nc.CertificationRefused) as ei:
        write(ledger, crit, "sourced", citation_state=bad)
    assert ei.value.code == "bad_citation_state"


def test_the_caller_value_is_never_what_is_stored(ledger, crit):
    # equal values are accepted, but the stored one is the census cell's: pin it with a state whose spelling matters
    rec = write(ledger, crit, "sourced_ocr_unverified", citation_state="sourced_ocr_unverified").record
    assert rec["citation_state"] == "sourced_ocr_unverified"
    rec2 = write(ledger, crit, "sourced_ocr_unverified", asset="bg_other").record
    assert rec2["citation_state"] == "sourced_ocr_unverified"


# ───────────────────────── other criteria: null ─────────────────────────

def test_a_census_cell_state_on_another_criterion_is_ignored_and_the_field_is_null(ledger):
    rec = nc.write_certification(**kw(ledger, cell=dict(citation_state="sourced_ocr_unverified"))).record
    assert rec["criterion"] == "Build.registered"
    assert rec["citation_state"] is None and rec["citation_state_caveat"] is False


@pytest.mark.parametrize("crit_", ["Build.registered", "Idem.pattern", "Carr.D2", "Dens.served"])
def test_a_caller_value_on_another_criterion_is_refused(ledger, crit_):
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, criterion=crit_, citation_state="sourced",
                                    verdict="NO_DETECTOR" if crit_ == "Carr.D2" else "PASS"))
    assert ei.value.code == "citation_state_not_applicable"


def test_an_addition_has_no_citation_state_and_a_typed_one_is_refused(ledger):
    base = dict(asset="bg_ontology", layer="L0", kind="addition", criterion="D-GROUNDING", criterion_version=1,
                detector="grounding_probe.py", verdict="PASS", evidence=dict(census_run_id=RUN), verified_by="t",
                ledger_path=ledger, writer_files=[W1], writer_repo=ENV.repo, semantic_fingerprint=FP)
    rec = nc.write_certification(**base).record
    assert rec["citation_state"] is None and rec["citation_state_caveat"] is False and rec["record_version"] == 2
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**dict(base, citation_state="sourced", criterion="D-OTHER"))
    assert ei.value.code == "citation_state_not_applicable"


def test_an_applicability_na_on_a_citation_criterion_has_no_state(ledger, monkeypatch):
    rid = f"{LDGR}#columns_any"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22.test"})
    rec = nc.write_certification(**kw(ledger, criterion=LDGR, verdict="N/A", na_rule_id=rid, cell=...,
                                      rec=dict(target_columns=["id", "name"]), semantic_fingerprint=None,
                                      writer_files=...)).record
    assert rec["verdict"] == "N/A" and rec["citation_state"] is None and rec["citation_state_caveat"] is False


# ───────────────────────── currency: a change of state is a new generation ─────────────────────────

def test_an_unchanged_state_appends_nothing_and_a_changed_one_is_a_new_generation(ledger, crit):
    r1 = write(ledger, crit, "sourced")
    snap = ledger.read_bytes()
    assert write(ledger, crit, "sourced").status == "unchanged" and ledger.read_bytes() == snap
    r2 = write(ledger, crit, "sourced_ocr_unverified")
    assert r2.status == "appended" and r2.record["generation"] == 2
    assert ledger.read_bytes().startswith(snap)
    r3 = write(ledger, crit, "sourced")                                          # back again: generation 3, never a silent revert
    assert r3.status == "appended" and r3.record["generation"] == 3
    assert [x["citation_state"] for x in lines(ledger)[1:]] == ["sourced", "sourced_ocr_unverified", "sourced"]


def test_a_state_appearing_where_there_was_none_is_a_new_generation(ledger):
    write(ledger, LDGR, ...)
    r = write(ledger, LDGR, "sourced")
    assert r.status == "appended" and r.record["generation"] == 2


def test_the_state_is_part_of_the_identity_the_change_detector_compares(ledger, crit):
    a = nc.build_record(**{k: v for k, v in req(ledger, crit, "sourced").items() if k != "ledger_path"})
    b = nc.build_record(**{k: v for k, v in req(ledger, crit, "sourced_ocr_unverified").items() if k != "ledger_path"})
    assert nc._identity(a) != nc._identity(b)
    assert nc._identity(a) == nc._identity(dict(a, citation_state_caveat=True))   # the caveat is derived, not independent


# ───────────────────────── v1 ledgers: written by the E5.1 on main, read by this one ─────────────────────────

FROZEN = HERE / "fixtures" / "nikasha_certify_v1_frozen.py"
FROZEN_SHA256 = "48f16161acf6953e7f361366ee7d8e30a9ca34436deb16b96b7981f469bec310"


def frozen_v1():
    """The E5.1 that was on main before record_version 2, byte for byte (a fixture, never edited)."""
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == FROZEN_SHA256, "the frozen v1 writer was edited"
    spec = importlib.util.spec_from_file_location("nikasha_certify_v1_frozen", FROZEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod                      # its dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


def write_v1(ledger, **over):
    old = frozen_v1()
    d = kw(ledger, **over)
    d.pop("citation_state", None)
    return old.write_certification(**d)


def test_the_frozen_writer_really_writes_record_version_1_without_the_fields(ledger):
    rec = write_v1(ledger).record
    assert rec["record_version"] == 1 and "citation_state" not in rec and "citation_state_caveat" not in rec


def test_a_v1_ledger_reads_under_the_new_code_with_citation_state_null(ledger):
    write_v1(ledger)
    write_v1(ledger, criterion="Build.contract", asset="bg_other")
    write_v1(ledger, criterion=LDGR, rec=dict(target_columns=CITE_COLS))
    by_key = nc.read_ledger(ledger)                                              # the whole chain verifies
    assert len(by_key) == 3
    for key, recs in by_key.items():
        r = recs[0]
        assert r["record_version"] == 1 and r["citation_state"] is None
        # the caveat is read by the SAME rule as a v2 null-state record: a PASS on a citation criterion cannot claim sourced
        assert r["citation_state_caveat"] is (key.endswith("|Ldgr.source_presence"))
    assert len(nc.read_records(ledger)) == 3 and len(nc.parse_records(ledger.read_bytes())) == 3
    assert nc.chain_head(ledger.read_bytes())[0] == 3


def test_reading_a_v1_ledger_never_changes_its_bytes(ledger):
    write_v1(ledger)
    before = ledger.read_bytes()
    nc.read_ledger(ledger)
    nc.parse_records(before)
    assert ledger.read_bytes() == before and b"citation_state" not in before


def test_new_v2_records_chain_onto_a_v1_ledger(ledger):
    v1 = write_v1(ledger).record
    before = ledger.read_bytes()
    v2 = nc.write_certification(**kw(ledger, criterion="Build.contract")).record
    assert v2["record_version"] == 2 and v2["seq"] == 2
    raw = ledger.read_bytes()
    assert raw.startswith(before)                                                # append-only
    ls = [x for x in raw.split(b"\n") if x.strip()]
    assert v2["prev_sha256"] == hashlib.sha256(ls[1]).hexdigest()               # chained from the v1 line, byte for byte
    assert [r["record_version"] for r in lines(ledger)[1:]] == [1, 2]
    assert nc.read_ledger(ledger)[v1["cert_key"]][0]["citation_state"] is None


def test_a_remeasurement_of_a_v1_non_citation_record_differs_only_by_the_declarations_binding(ledger):
    write_v1(ledger)
    snap = ledger.read_bytes()
    r = nc.write_certification(**kw(ledger))                                     # same measurement, new writer
    # citation_state alone would make it identical (v1 reads null = the new null); the declarations binding (a currency
    # field a v1 record never had) is what makes it a new, bound generation
    assert r.status == "appended" and r.record["generation"] == 2 and r.record["record_version"] == 2
    assert r.record["declarations_sha256"] is not None and ledger.read_bytes().startswith(snap)
    assert nc._identity(dict(nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"][0],
                             declarations_sha256=r.record["declarations_sha256"])) == nc._identity(r.record)


def test_a_v1_citation_record_gets_a_new_generation_when_a_state_is_now_declared(ledger):
    write_v1(ledger, criterion=LDGR, rec=dict(target_columns=CITE_COLS))
    r = write(ledger, LDGR, "sourced")
    assert r.status == "appended" and r.record["generation"] == 2 and r.record["record_version"] == 2
    # a v1 record read as "not declared" and a new measurement that still declares none differ only by the binding
    write_v1(ledger, criterion=LDGR, asset="bg_other", rec=dict(target_columns=CITE_COLS))
    r2 = write(ledger, LDGR, ..., asset="bg_other")
    assert r2.status == "appended" and r2.record["citation_state"] is None and r2.record["declarations_sha256"] is not None
    prev = nc.read_ledger(ledger)["bg_other|gate|Ldgr.source_presence"][0]
    assert nc._identity(dict(prev, declarations_sha256=r2.record["declarations_sha256"])) == nc._identity(r2.record)


def test_a_v1_upstream_can_be_cited_by_a_v2_record(ledger):
    up = write_v1(ledger).record["cert_id"]
    r = nc.write_certification(**kw(ledger, criterion="Build.contract", upstream_cert_ids=[up]))
    assert r.record["upstream_cert_ids"] == [up]


def test_the_public_append_api_still_takes_events_after_a_v1_ledger(ledger):
    write_v1(ledger)
    ev = dict(type="watermark", asset="_ledger", covers_seq=1, certs_processed=1, last_cert_id="x", commit="c")
    assert nc.append_records(ledger, [ev]) == 1
    assert nc.read_records(ledger)[-1]["type"] == "watermark"


# ───────────────────────── the reader holds a v2 record to the same rules ─────────────────────────

def raw_lines(p):
    return [x for x in p.read_bytes().split(b"\n") if x.strip()]


def rewrite(p, idx, **changes):
    """Edit record line `idx` and re-chain the lines after it (a deliberate, internally consistent hand edit)."""
    ls = raw_lines(p)
    out, prev = [], None
    for i, ln in enumerate(ls):
        r = json.loads(ln)
        if i == idx:
            r.update({k: v for k, v in changes.items() if v is not ...})
            for k, v in changes.items():
                if v is ...:
                    r.pop(k, None)
        if i >= 1:
            r["prev_sha256"] = prev
        b = nc._dump(r)
        prev = hashlib.sha256(b).hexdigest()
        out.append(b)
    p.write_bytes(b"\n".join(out) + b"\n")


def test_a_hand_edited_unsourced_pass_is_refused_on_read(ledger):
    write(ledger, LDGR, "sourced")
    rewrite(ledger, 1, citation_state="unsourced", citation_state_caveat=True)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "citation_state" in ei.value.message


@pytest.mark.parametrize("changes,why", [
    (dict(citation_state="refuted", citation_state_caveat=True), "refuted PASS"),
    (dict(citation_state="maybe"), "unknown state"),
    (dict(citation_state="maybe", citation_state_caveat=True), "unknown state with a consistent caveat"),
    (dict(citation_state=5, citation_state_caveat=True), "non-text state with a consistent caveat"),
    (dict(citation_state="SOURCED", citation_state_caveat=True), "wrong-case state"),
    (dict(citation_state=["sourced"], citation_state_caveat=True), "list state"),
    (dict(citation_state_caveat=False, citation_state="sourced_ocr_unverified"), "caveat missing on a non-sourced PASS"),
    (dict(citation_state_caveat=True), "caveat on a sourced PASS"),
    (dict(citation_state_caveat="yes"), "non-boolean caveat"),
    (dict(citation_state=...), "v2 record without citation_state"),
    (dict(citation_state_caveat=...), "v2 record without the caveat"),
    (dict(record_version=3), "unknown record_version"),
    (dict(record_version="2"), "non-int record_version"),
    (dict(record_version=True), "bool record_version"),
    (dict(record_version=0), "record_version 0"),
])
def test_an_inconsistent_citation_record_is_refused_on_read(ledger, changes, why):
    write(ledger, LDGR, "sourced")
    rewrite(ledger, 1, **changes)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger", why


def test_a_state_on_a_non_citation_record_is_refused_on_read(ledger):
    nc.write_certification(**kw(ledger))
    rewrite(ledger, 1, citation_state="sourced", citation_state_caveat=False)
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger)


def test_a_v1_record_carrying_a_v2_field_is_refused_on_read(ledger):
    write_v1(ledger)
    rewrite(ledger, 1, citation_state="sourced")
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger)
    rewrite(ledger, 1, citation_state=..., citation_state_caveat=False)
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger)


@pytest.mark.parametrize("bad", [True, False, "1", 1.0, None, [1], 3, 0, -1])
def test_a_v1_shaped_record_with_a_malformed_record_version_is_refused(ledger, bad):
    write_v1(ledger)                                                             # no v2 fields: only the version is wrong
    rewrite(ledger, 1, record_version=bad)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "record_version" in ei.value.message


def test_a_record_with_no_record_version_reads_as_v1(ledger):
    write_v1(ledger)
    rewrite(ledger, 1, record_version=...)
    r = nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"][0]
    assert r["citation_state"] is None and r["citation_state_caveat"] is False


def test_a_non_pass_unsourced_citation_record_reads_fine(ledger):
    write(ledger, LDGR, "unsourced", "NO_DETECTOR")
    assert nc.read_ledger(ledger)["bg_ontology|gate|Ldgr.source_presence"][0]["citation_state"] == "unsourced"


def test_ok_records_of_every_kind_read_back(ledger):
    write(ledger, LDGR, "sourced")
    write(ledger, LDGR, "sourced_ocr_unverified", asset="bg_other")
    write(ledger, LDGR, ..., asset="bg_third")
    nc.write_certification(**kw(ledger, criterion="Build.contract"))
    by_key = nc.read_ledger(ledger)
    got = sorted((k.split("|")[0], str(v[0]["citation_state"]), v[0]["citation_state_caveat"], k.split("|")[2])
                 for k, v in by_key.items())
    assert got == sorted([("bg_ontology", "sourced", False, LDGR), ("bg_other", "sourced_ocr_unverified", True, LDGR),
                          ("bg_third", "None", True, LDGR), ("bg_ontology", "None", False, "Build.contract")])


# ───────────────────────── CLI ─────────────────────────

def test_the_cli_citation_state_flag_is_a_cross_check_only(ledger, tmp_path, capsys):
    cf = write_census_file({LDGR: dict(v="PASS", measured="m", citation_state="sourced_ocr_unverified")},
                           rec=dict(target_columns=CITE_COLS))
    base = ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--criterion", LDGR, "--census", str(cf),
            "--verified-by", "t", "--semantic-fingerprint", FP, "--writer-repo", str(ENV.repo), "--writer-file", W1,
            "--writer-file", W2, "--measured", "m"]
    assert nc.main(base + ["--citation-state", "sourced_ocr_unverified"]) == 0
    assert lines(ledger)[1]["citation_state"] == "sourced_ocr_unverified" and lines(ledger)[1]["citation_state_caveat"] is True
    before = ledger.read_bytes()
    assert nc.main(base + ["--citation-state", "sourced"]) == 2                  # a differing flag is refused
    assert "citation_state_conflict" in capsys.readouterr().err and ledger.read_bytes() == before
    assert nc.main(base) == 0                                                    # no flag: the cell alone decides (unchanged)


# ───────────────────────── v1 and v2 read alike ─────────────────────────

def test_a_v1_pass_on_a_citation_criterion_reads_the_same_caveat_as_a_v2_null_state_pass(ledger, monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    write_v1(ledger, criterion=LDGR, rec=dict(target_columns=CITE_COLS))
    write_v1(ledger, criterion=D1, asset="bg_other", rec=dict(target_columns=CITE_COLS))
    write(ledger, LDGR, ..., asset="bg_third")                                      # v2, null state
    by_key = nc.read_ledger(ledger)
    v1_ldgr = by_key["bg_ontology|gate|Ldgr.source_presence"][0]
    v2_ldgr = by_key["bg_third|gate|Ldgr.source_presence"][0]
    assert v1_ldgr["record_version"] == 1 and v2_ldgr["record_version"] == 2
    assert (v1_ldgr["citation_state"], v1_ldgr["citation_state_caveat"]) == (v2_ldgr["citation_state"],
                                                                              v2_ldgr["citation_state_caveat"]) == (None, True)
    # a v1 Carr.D1 PASS (impossible to write today) still READS, as null + caveat: reading never refuses a v1 record
    v1_d1 = by_key["bg_other|gate|Carr.D1"][0]
    assert v1_d1["citation_state"] is None and v1_d1["citation_state_caveat"] is True


def test_a_v1_non_pass_and_a_non_citation_v1_record_read_with_no_caveat(ledger):
    write_v1(ledger, criterion=LDGR, verdict="NO_DETECTOR", rec=dict(target_columns=CITE_COLS))
    write_v1(ledger, criterion="Build.contract", asset="bg_other")
    by_key = nc.read_ledger(ledger)
    assert all(v[0]["citation_state"] is None and v[0]["citation_state_caveat"] is False for v in by_key.values())


# ───────────────────────── the reader and the new rules ─────────────────────────

def test_the_reader_refuses_a_state_on_an_applicability_na(ledger, monkeypatch):
    rid = f"{LDGR}#columns_any"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22.test"})
    nc.write_certification(**kw(ledger, criterion=LDGR, verdict="N/A", na_rule_id=rid, cell=...,
                                rec=dict(target_columns=["id", "name"]), semantic_fingerprint=None, writer_files=...))
    assert nc.read_ledger(ledger)                                                   # control: as written, it reads
    rewrite(ledger, 1, citation_state="sourced", citation_state_caveat=False)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "applicability" in ei.value.message


def test_a_measured_cause_na_may_carry_the_cells_state_and_reads_fine(ledger, monkeypatch):
    rid = f"{LDGR}#measured:no-prose"
    monkeypatch.setattr(ac, "NA_CAUSES", dict(ac.NA_CAUSES, **{LDGR: ("no-prose",)}))
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22.nr"})
    rec = nc.write_certification(**kw(
        ledger, criterion=LDGR, verdict="N/A", na_rule_id=rid, cell=dict(v="N/A", cause="no-prose", citation_state="sourced"),
        rec=dict(target_columns=CITE_COLS), semantic_fingerprint=FP2)).record
    assert rec["citation_state"] == "sourced" and nc.read_ledger(ledger)


@pytest.mark.parametrize("verdict,state", [("PASS", None), ("PARTIAL", None), ("PARTIAL", "unsourced"), ("PARTIAL", "refuted")])
def test_the_reader_holds_a_carr_d1_pass_or_partial_to_the_writers_rule(ledger, monkeypatch, verdict, state):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    write(ledger, D1, "sourced", verdict)
    assert nc.read_ledger(ledger)                                                   # control
    rewrite(ledger, 1, citation_state=state, citation_state_caveat=(verdict == "PASS" and state is None))
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger"


# ───────────────────────── CI verification compares citation_state to the census cell ─────────────────────────

def ldgr_in_repo(repo, state="sourced_ocr_unverified", **over):
    cert_in_repo(repo, criterion=LDGR, cell=dict(citation_state=state), rec=dict(target_columns=CITE_COLS), **over)
    commit_all(repo)


def test_verify_passes_a_record_whose_state_and_caveat_match_the_cell(fresh_repo):
    ldgr_in_repo(fresh_repo)
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "PASS"
    assert nc.read_ledger(fresh_repo / nc.LEDGER_RELPATH)["bg_ontology|gate|Ldgr.source_presence"][0][
        "citation_state_caveat"] is True


def test_verify_catches_a_forged_sourced_state_over_an_ocr_unverified_cell(fresh_repo):
    ldgr_in_repo(fresh_repo)
    doctor(fresh_repo, citation_state="sourced", citation_state_caveat=False)        # internally consistent: the READER accepts it
    nc.read_ledger(fresh_repo / nc.LEDGER_RELPATH)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert ei.value.code == "census_citation_mismatch" and "citation_state" in str(ei.value)


@pytest.mark.parametrize("cell_state,forged", [("sourced", None), ("sourced_ocr_unverified", "sourced"), (None, "sourced"),
                                               ("sourced", "sourced_ocr_unverified")])
def test_verify_catches_every_state_that_differs_from_the_cell(fresh_repo, cell_state, forged):
    if cell_state is None:
        cert_in_repo(fresh_repo, criterion=LDGR, rec=dict(target_columns=CITE_COLS))
        commit_all(fresh_repo)
    else:
        ldgr_in_repo(fresh_repo, cell_state)
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "PASS"
    doctor(fresh_repo, citation_state=forged, citation_state_caveat=(forged != "sourced"))
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert ei.value.code == "census_citation_mismatch"


def test_verify_catches_a_caveat_inconsistent_with_the_verdict_even_when_the_reader_is_bypassed(fresh_repo):
    # the reader refuses an inconsistent caveat; verify must too (defence in depth: it compares what the cell implies)
    ldgr_in_repo(fresh_repo, "sourced")
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "PASS"
    cell_vs = nc._citation_vs_cell(dict(kind="gate", record_version=2, criterion=LDGR, verdict="PASS",
                                        citation_state="sourced", citation_state_caveat=True), dict(citation_state="sourced"))
    assert cell_vs[0] == "census_citation_mismatch" and "caveat" in cell_vs[1]


def test_verify_does_not_apply_the_citation_comparison_to_a_v1_record(fresh_repo):
    old = frozen_v1()
    old.write_certification(**kw(fresh_repo / nc.LEDGER_RELPATH, init=True, writer_repo=fresh_repo, criterion=LDGR,
                                 cell=dict(citation_state="sourced"), rec=dict(target_columns=CITE_COLS)))
    commit_all(fresh_repo)
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "PASS"   # the v1 record predates the field


def test_verify_a_record_on_a_non_citation_criterion_must_carry_no_state(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "PASS"
    assert nc._citation_vs_cell(dict(kind="gate", record_version=2, criterion="Build.registered", verdict="PASS",
                                     citation_state="sourced", citation_state_caveat=False),
                                dict(citation_state="sourced"))[0] == "census_citation_mismatch"


# ───────────────────────── CLI: the flag is a cross-check, both ways, on both criteria ─────────────────────────

def cli_base(ledger, crit_, cell, tmp=None):
    cf = write_census_file({crit_: dict(v="PASS", measured="m", **cell)}, rec=dict(target_columns=CITE_COLS))
    return ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--criterion", crit_, "--census", str(cf),
            "--verified-by", "t", "--semantic-fingerprint", FP, "--writer-repo", str(ENV.repo), "--writer-file", W1,
            "--writer-file", W2, "--measured", "m"]


def test_cli_carr_d1_flag_accept_refuse_and_missing(ledger, monkeypatch, capsys):
    reg = dict(ac.CRITERION_REGISTRY)
    reg[D1] = dict(reg[D1], detector="asset_census.py:carriage_d1")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    base = cli_base(ledger, D1, dict(citation_state="sourced"))
    assert nc.main(base + ["--citation-state", "sourced"]) == 0
    assert lines(ledger)[1]["citation_state"] == "sourced" and lines(ledger)[1]["citation_state_caveat"] is False
    before = ledger.read_bytes()
    assert nc.main(base + ["--citation-state", "refuted"]) == 2
    assert "citation_state_conflict" in capsys.readouterr().err and ledger.read_bytes() == before
    assert nc.main(base + ["--citation-state", "bogus"]) == 2
    assert "bad_citation_state" in capsys.readouterr().err
    # a cell with no state: Carr.D1 refuses outright (S2's rollup would read NO_DETECTOR)
    assert nc.main(cli_base(ledger, D1, {})) == 2
    assert "citation_state_missing" in capsys.readouterr().err and ledger.read_bytes() == before


def test_cli_flag_cannot_supply_a_state_the_cell_lacks_and_is_refused_on_other_criteria(ledger, capsys):
    before = ledger.read_bytes()
    assert nc.main(cli_base(ledger, LDGR, {}) + ["--citation-state", "sourced"]) == 2
    assert "citation_state_conflict" in capsys.readouterr().err and ledger.read_bytes() == before
    assert nc.main(cli_base(ledger, LDGR, {}) + []) == 0                              # no flag: the null-state legacy write
    assert lines(ledger)[1]["citation_state"] is None and lines(ledger)[1]["citation_state_caveat"] is True
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    args = ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--criterion", "Build.registered",
            "--census", str(cf), "--verified-by", "t", "--semantic-fingerprint", FP, "--writer-repo", str(ENV.repo),
            "--writer-file", W1, "--writer-file", W2, "--measured", "m", "--citation-state", "sourced"]
    assert nc.main(args) == 2 and "citation_state_not_applicable" in capsys.readouterr().err
