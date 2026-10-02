"""test_e5_1_declarations_binding.py — a certificate is bound to the DECLARATIONS FILE it was measured under (SS N-74 add-on).

The census stamp (lane 3) records in every layer head `declarations_sha256` (sha256 of the BYTES of
platform/scripts/governance/asset_declarations.json as the run read it) and `declarations_version`, or null +
`declarations_unavailable`. The writer:
  (a) REFUSES a gate whose census head carries no usable `declarations_sha256` (`census_declarations_unbound`);
  (b) REFUSES one that differs from the sha256 of the file in the repo being certified (`census_declarations_mismatch`,
      both short shas and both versions in the message); that file is the working-tree file of the writer repo, which must
      be committed and clean (`declarations_not_committed`), or the blob at `writer_ref` when one is given;
  (c) records `declarations_sha256` and `declarations_version` in the record (gates; null on additions), and
      `declarations_sha256` is a CURRENCY field (a different file is a new generation);
  (d) verify_ledger_census_hashes REPORTS (never fails on) a latest-generation gate record whose recorded sha is not the
      file's sha at the ref as STALE, lists records written before the field as LEGACY, and FAILS a record whose recorded
      sha is not its own cited census head's (`census_declarations_mismatch`: a forgery).
record_version stays 2: the fields are additive for NEW records; a v2 record written before them reads as null (legacy).

Offline: the harness of test_e5_1_certify.py (tmp git repos, committed census files).
"""
from __future__ import annotations

import hashlib
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
    DECL_BYTES, DECL_REL, DECL_SHA, ENV, FP, RUN, W1, W2, add_call, add_kw, cert_in_repo, commit_all, doctor, env, fresh_repo, git, kw,
    ledger, lines, refused, session_repo, write_census_file,
)

NEW_BYTES = b'{"version": "1.8.0", "assets": {"bg_x": {}}}\n'
NEW_SHA = hashlib.sha256(NEW_BYTES).hexdigest()


def short(h):
    return h[:12]


def set_declarations(repo, data, commit=True):
    (repo / DECL_REL).write_bytes(data)
    if commit:
        commit_all(repo, "declarations edited")


# ───────────────────────── the record carries both fields ─────────────────────────

def test_a_gate_record_carries_the_declarations_sha_and_version(ledger):
    rec = nc.write_certification(**kw(ledger)).record
    assert rec["declarations_sha256"] == DECL_SHA and rec["declarations_version"] == "1.7.0"
    assert rec["record_version"] == 2                                              # additive under v2
    assert lines(ledger)[1] == rec


def test_an_addition_carries_none(ledger):
    rec = add_call(ledger).record
    assert rec["declarations_sha256"] is None and rec["declarations_version"] is None


def test_the_declarations_sha_is_a_currency_field_and_the_version_is_provenance():
    assert "declarations_sha256" in nc.CURRENCY_FIELDS and "declarations_version" not in nc.CURRENCY_FIELDS


# ───────────────────────── (a) the census must be bound to a declarations file ─────────────────────────

@pytest.mark.parametrize("head", [
    dict(declarations_sha256=...), dict(declarations_sha256=None), dict(declarations_sha256=""), dict(declarations_sha256=5),
    dict(declarations_sha256="abc"), dict(declarations_sha256="A" * 64), dict(declarations_sha256=DECL_SHA.upper()),
    dict(declarations_sha256=[DECL_SHA]), dict(declarations_sha256=True),
    dict(declarations_sha256=None, declarations_version=None, declarations_unavailable=True),
    dict(declarations_sha256=..., declarations_version=...),
])
def test_a_census_with_no_usable_declarations_sha_is_refused_and_nothing_is_written(ledger, head):
    before = ledger.read_bytes()
    e = refused(ledger, "census_declarations_unbound", head=head)
    assert "declarations_sha256" in str(e) and ledger.read_bytes() == before


def test_the_unavailable_flag_is_named_in_the_refusal(ledger):
    e = refused(ledger, "census_declarations_unbound",
                head=dict(declarations_sha256=None, declarations_version=None, declarations_unavailable=True))
    assert "unavailable" in str(e)


def test_the_six_archived_censuses_without_the_fields_cannot_be_cited(ledger):
    e = refused(ledger, "census_declarations_unbound", head=dict(declarations_sha256=..., declarations_version=...))
    assert "no declarations_sha256" in str(e) or "declarations" in str(e)


def test_the_check_applies_to_the_layer_head_chosen_not_to_a_decoy_layer(ledger):
    # the real multi-layer shape: the decoy layer carries the fields, the chosen one does not (and vice versa)
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, head=dict(declarations_sha256=...), multi=True)
    d = kw(ledger, census_path=cf)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**d)
    assert ei.value.code == "census_declarations_unbound"


# ───────────────────────── (b) and the file in the repo being certified ─────────────────────────

@pytest.mark.parametrize("bad", ["f" * 64, NEW_SHA, "0" * 64])
def test_a_census_stamped_with_another_declarations_sha_is_refused_with_both_shas_and_versions(ledger, bad):
    before = ledger.read_bytes()
    e = refused(ledger, "census_declarations_mismatch", head=dict(declarations_sha256=bad, declarations_version="9.9.9"))
    msg = str(e)
    assert short(bad) in msg and short(DECL_SHA) in msg and "9.9.9" in msg and "1.7.0" in msg
    assert ledger.read_bytes() == before


def test_a_declarations_file_edited_after_the_census_is_a_mismatch(fresh_repo, ledger):
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})              # stamped with DECL_SHA
    set_declarations(fresh_repo, NEW_BYTES)                                                  # edited AND committed after
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code == "census_declarations_mismatch"
    assert short(DECL_SHA) in str(ei.value) and short(NEW_SHA) in str(ei.value) and "1.8.0" in str(ei.value)


def test_a_declarations_file_that_is_edited_but_not_committed_is_refused(fresh_repo, ledger):
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    set_declarations(fresh_repo, DECL_BYTES + b" ", commit=False)                            # dirty working tree
    before = ledger.read_bytes() if ledger.exists() else None
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code == "declarations_not_committed" and (not ledger.exists() or ledger.read_bytes() == before)


def test_a_declarations_file_that_is_untracked_or_missing_is_refused(fresh_repo, ledger):
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    git(fresh_repo, "rm", "-q", "--cached", DECL_REL)                                        # staged for deletion, file still there
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code == "declarations_not_committed"
    (fresh_repo / DECL_REL).unlink()
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code in ("declarations_not_committed", "declarations_unreadable")


def test_a_gitignored_untracked_declarations_file_is_refused_though_status_is_clean(fresh_repo, ledger):
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    git(fresh_repo, "rm", "-q", DECL_REL)
    (fresh_repo / ".gitignore").write_text(DECL_REL + "\n")
    git(fresh_repo, "add", ".gitignore")
    commit_all(fresh_repo, "declarations untracked and ignored")
    (fresh_repo / DECL_REL).parent.mkdir(parents=True, exist_ok=True)
    (fresh_repo / DECL_REL).write_bytes(DECL_BYTES)                                         # present, ignored, status clean
    assert git(fresh_repo, "status", "--porcelain", "--", DECL_REL).strip() == ""
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code == "declarations_not_committed" and "not tracked" in str(ei.value)


def test_the_recorded_version_is_the_files_not_the_censuss(ledger):
    rec = nc.write_certification(**kw(ledger, head=dict(declarations_version="9.9.9"))).record     # sha equal, version differs
    assert rec["declarations_sha256"] == DECL_SHA and rec["declarations_version"] == "1.7.0"


def test_with_a_writer_ref_the_file_at_that_ref_is_the_one_compared(fresh_repo, ledger):
    base = git(fresh_repo, "rev-parse", "HEAD").strip()
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})              # stamped with the base file
    set_declarations(fresh_repo, NEW_BYTES)                                                  # the tree moved on
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert ei.value.code == "census_declarations_mismatch"
    r = nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo, writer_ref=base))
    assert r.record["declarations_sha256"] == DECL_SHA and r.record["declarations_version"] == "1.7.0"


def test_with_a_writer_ref_a_ref_without_the_file_is_refused(fresh_repo, ledger):
    git(fresh_repo, "rm", "-q", DECL_REL)
    commit_all(fresh_repo, "declarations removed")
    no_file = git(fresh_repo, "rev-parse", "HEAD").strip()
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo, writer_ref=no_file))
    assert ei.value.code == "declarations_unreadable"


def test_the_declarations_check_does_not_apply_to_additions(ledger):
    assert add_call(ledger).status == "appended"                    # no census, no declarations


# ───────────────────────── currency ─────────────────────────

def test_the_same_declarations_appends_nothing_and_a_new_file_is_a_new_generation(fresh_repo, ledger):
    r1 = nc.write_certification(**kw(ledger, writer_repo=fresh_repo))
    snap = ledger.read_bytes()
    assert nc.write_certification(**kw(ledger, writer_repo=fresh_repo)).status == "unchanged" and ledger.read_bytes() == snap
    set_declarations(fresh_repo, NEW_BYTES)
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")},
                           head=dict(declarations_sha256=NEW_SHA, declarations_version="1.8.0"))
    r2 = nc.write_certification(**kw(ledger, census_path=cf, writer_repo=fresh_repo))
    assert r2.status == "appended" and r2.record["generation"] == 2 and r2.record["declarations_sha256"] == NEW_SHA
    assert ledger.read_bytes().startswith(snap) and r1.record["declarations_sha256"] == DECL_SHA


def test_the_declarations_sha_is_part_of_the_identity_the_change_detector_compares(ledger):
    a = nc.build_record(**{k: v for k, v in kw(ledger).items() if k != "ledger_path"})
    assert nc._identity(a) != nc._identity(dict(a, declarations_sha256=NEW_SHA))
    assert nc._identity(a) == nc._identity(dict(a, declarations_version="9.9"))               # the version is provenance


# ───────────────────────── reading: new records, legacy v2 records, bad values ─────────────────────────

def raw_lines(p):
    return [x for x in p.read_bytes().split(b"\n") if x.strip()]


def rewrite(p, idx, **changes):
    ls = raw_lines(p)
    out, prev = [], None
    for i, ln in enumerate(ls):
        r = json.loads(ln)
        if i == idx:
            for k, v in changes.items():
                if v is ...:
                    r.pop(k, None)
                else:
                    r[k] = v
        if i >= 1:
            r["prev_sha256"] = prev
        b = nc._dump(r)
        prev = hashlib.sha256(b).hexdigest()
        out.append(b)
    p.write_bytes(b"\n".join(out) + b"\n")


def test_a_v2_record_written_before_the_fields_still_parses_and_reads_as_null(ledger):
    nc.write_certification(**kw(ledger))
    rewrite(ledger, 1, declarations_sha256=..., declarations_version=...)                    # a legacy v2 record
    r = nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"][0]
    assert r["record_version"] == 2 and r["declarations_sha256"] is None and r["declarations_version"] is None
    assert nc.read_records(ledger)[0]["declarations_sha256"] is None


def test_new_records_chain_onto_a_legacy_v2_ledger_and_the_legacy_record_is_a_new_generation_when_rewritten(ledger):
    nc.write_certification(**kw(ledger))
    rewrite(ledger, 1, declarations_sha256=..., declarations_version=...)
    r = nc.write_certification(**kw(ledger))                                                  # same measurement, now bound
    assert r.status == "appended" and r.record["generation"] == 2 and r.record["declarations_sha256"] == DECL_SHA
    assert nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"][1]["declarations_sha256"] == DECL_SHA


@pytest.mark.parametrize("changes", [
    dict(declarations_sha256="abc"), dict(declarations_sha256="A" * 64), dict(declarations_sha256=5),
    dict(declarations_sha256=True), dict(declarations_sha256=[DECL_SHA]),
    dict(declarations_version=5), dict(declarations_version=""), dict(declarations_version="  "), dict(declarations_version=["1"]),
])
def test_malformed_declarations_fields_are_refused_on_read(ledger, changes):
    nc.write_certification(**kw(ledger))
    rewrite(ledger, 1, **changes)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger"


def test_a_version_without_a_sha_or_a_sha_on_an_addition_is_refused_on_read(ledger):
    add_call(ledger)
    rewrite(ledger, 1, declarations_sha256=DECL_SHA, declarations_version="1.7.0")
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger)
    ledger2 = ledger.parent / "l2.jsonl"
    ledger2.write_text(ledger.read_text().split("\n")[0] + "\n")
    nc.write_certification(**kw(ledger2))
    rewrite(ledger2, 1, declarations_sha256=None, declarations_version="1.7.0")
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger2)


def test_a_v1_record_carrying_the_field_is_refused_and_a_v1_record_reads_null(ledger):
    import importlib.util
    spec = importlib.util.spec_from_file_location("v1_frozen_decl", HERE / "fixtures" / "nikasha_certify_v1_frozen.py")
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    d = kw(ledger)
    d.pop("citation_state", None)
    old.write_certification(**d)
    r = nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"][0]
    assert r["record_version"] == 1 and r["declarations_sha256"] is None and r["declarations_version"] is None
    rewrite(ledger, 1, declarations_sha256=DECL_SHA)
    with pytest.raises(nc.CertificationRefused):
        nc.read_ledger(ledger)


# ───────────────────────── (d) verify: stale, legacy, forged ─────────────────────────

def test_verify_reports_a_matching_record_as_neither_stale_nor_legacy(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert res["status"] == "PASS" and res["stale_declarations"] == [] and res["legacy_declarations"] == []
    assert res["declarations_at_ref"] == dict(sha256=DECL_SHA, version="1.7.0")


def test_verify_reports_a_record_stale_when_the_declarations_were_edited_after_certification(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    set_declarations(fresh_repo, NEW_BYTES)
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")                                  # reported, NOT a failure
    assert res["status"] == "PASS" and res["checked"] == 1
    assert res["stale_declarations"] == [dict(cert_id="bg_ontology|gate|Build.registered@1", recorded_sha256=DECL_SHA,
                                              recorded_version="1.7.0", at_ref_sha256=NEW_SHA, at_ref_version="1.8.0")]
    assert res["legacy_declarations"] == []
    assert res["declarations_at_ref"] == dict(sha256=NEW_SHA, version="1.8.0")


def test_verify_at_the_ref_before_the_edit_still_reads_current(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    before = git(fresh_repo, "rev-parse", "HEAD").strip()
    set_declarations(fresh_repo, NEW_BYTES)
    assert nc.verify_ledger_census_hashes(fresh_repo, before)["stale_declarations"] == []
    assert len(nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["stale_declarations"]) == 1


def test_verify_reports_a_removed_declarations_file_as_stale(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    git(fresh_repo, "rm", "-q", DECL_REL)
    commit_all(fresh_repo, "declarations removed")
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert res["status"] == "PASS" and res["declarations_at_ref"] == dict(sha256=None, version=None)
    assert [x["at_ref_sha256"] for x in res["stale_declarations"]] == [None]


def test_only_the_latest_generation_of_a_key_is_reported_stale(fresh_repo):
    cert_in_repo(fresh_repo)
    cert_in_repo(fresh_repo, semantic_fingerprint="b" * 64)                                    # generation 2, same declarations
    commit_all(fresh_repo)
    set_declarations(fresh_repo, NEW_BYTES)
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert res["checked"] == 2 and [x["cert_id"] for x in res["stale_declarations"]] == ["bg_ontology|gate|Build.registered@2"]


def test_a_record_certified_under_the_new_declarations_is_not_stale_after_the_edit(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    set_declarations(fresh_repo, NEW_BYTES)
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")},
                           head=dict(declarations_sha256=NEW_SHA, declarations_version="1.8.0"))
    nc.write_certification(**kw(fresh_repo / nc.LEDGER_RELPATH, census_path=cf, writer_repo=fresh_repo))
    commit_all(fresh_repo)
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert res["stale_declarations"] == []                                                    # the latest generation is current


def test_verify_lists_a_record_written_before_the_field_as_legacy_not_stale_not_failed(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    doctor(fresh_repo, declarations_sha256=None, declarations_version=None)                  # null = legacy / unbound
    res = nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert res["status"] == "PASS" and res["stale_declarations"] == []
    assert res["legacy_declarations"] == ["bg_ontology|gate|Build.registered@1"]


def test_verify_fails_a_record_whose_recorded_sha_is_not_its_own_cited_censuss(fresh_repo):
    cert_in_repo(fresh_repo)
    commit_all(fresh_repo)
    doctor(fresh_repo, declarations_sha256=NEW_SHA)                                           # a forgery: another file's sha
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.verify_ledger_census_hashes(fresh_repo, "HEAD")
    assert ei.value.code == "census_declarations_mismatch" and "declarations" in str(ei.value)


def test_verify_still_reports_nothing_for_a_ledger_with_no_gate_record(fresh_repo):
    nc.write_certification(**kw(fresh_repo / nc.LEDGER_RELPATH, init=True, writer_repo=fresh_repo, **add_kw(None)))
    commit_all(fresh_repo)
    assert nc.verify_ledger_census_hashes(fresh_repo, "HEAD")["status"] == "NO_DETECTOR"
