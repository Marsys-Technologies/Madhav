"""R12-2 — the sealing workflow's scripts: the brief check, the log extraction, the approval extraction and the gated orchestrator (the unit the `seal` job runs).

Every refusal is tested at the OUTERMOST boundary (the exit status of the script the workflow calls) and the orchestrator test proves the seal job is NEVER invoked after a
refusal. No database: the seal job is a recording shim here (Stream A's `seal_job` is the real caller; its transaction behaviour is tested against PostgreSQL in the
composed rehearsal)."""
from __future__ import annotations

import copy
import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import gochara_seal_approval as approval  # noqa: E402
import gochara_seal_brief_check as bc  # noqa: E402
import gochara_seal_brief_extract as bx  # noqa: E402
import gochara_seal_execution_check as xc  # noqa: E402
import gochara_verification_job_contract as xcheck_contract  # noqa: E402
import gochara_seal_reconcile as rc_  # noqa: E402

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
GEN = "5.0"
SHA = "a" * 40
RUN, ATT = "26104817", "1"


def payload(**over):
    p = {"schema": bc.SCHEMA, "chart_id": CHART, "generation": GEN, "manifest": {"manifest_id": "m", "status": "candidate"},
         "result_policy": bc.POLICY, "candidate_gate": {"source": "candidate_adapter/1", "violations": []},
         "classes": [{"event_class": "marriage", "grains": [{"path_id": "P1", "rule_version": "1.0.0", "status": "VERIFIED"}]}],
         "code": {"sealing_commit": SHA}, "seal_is_not_a_flip": "A seal is not a flip."}
    p.update(over)
    return p


def brief_raw(p=None):
    """The brief file: the CANONICAL JSON bytes of the approval payload (Stream A's `seal_brief.brief_bytes`); its sha256 is the brief digest."""
    return bc.canon(payload() if p is None else p).encode("utf-8")


def compact(p=None, raw=None, **over):
    """The verifier job's last output line (contract seal_brief_transport/1, ST-WIRE-2): `{status: BRIEFED, contract_version, sha256, persisted, producer, brief_bytes, brief_file, brief_chunks}`."""
    p = payload() if p is None else p
    raw = brief_raw(p) if raw is None else raw
    c = {"brief_bytes": len(raw), "brief_chunks": True, "brief_file": None, "contract_version": "seal_brief_transport/1", "sha256": hashlib.sha256(raw).hexdigest(), "status": "BRIEFED",
         "persisted": {"brief_id": 7, "manifest_id": p.get("manifest", {}).get("manifest_id"), "state_digest": "c" * 64},
         "producer": {"commit": SHA, "execution_id": "exec-1", "image_digest": "sha256:" + "a" * 64}}
    c.update(over)
    return c


def pair(p=None):
    raw = brief_raw(p)
    return raw, compact(p, raw)


def check(raw, c, **kw):
    return bc.check(raw, c, chart_id=kw.get("chart_id", CHART), generation=kw.get("generation", GEN), sealing_commit=kw.get("sealing_commit", SHA))


# ── the brief check ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_good_brief_verifies_and_returns_its_digest():
    p = payload()
    raw, c = pair(p)
    assert check(raw, c) == bc.digest(p) == hashlib.sha256(raw).hexdigest()


def _flip(raw):
    return raw[:-5] + (b"x" if raw[-5:-4] != b"x" else b"y") + raw[-4:]


@pytest.mark.parametrize("mut,needle", [
    (lambda raw, c: (_flip(raw), c), "truncated or altered"),                                          # a changed brief
    (lambda raw, c: (raw[:-10], c), "brief bytes"),                                                    # truncated (the length no longer matches)
    (lambda raw, c: (raw, {**c, "sha256": "0" * 64}), "truncated or altered"),
    (lambda raw, c: (raw, {**c, "sha256": "XYZ"}), "64-hex"),
    (lambda raw, c: (raw, {k: v for k, v in c.items() if k != "sha256"}), "BRIEFED"),
    (lambda raw, c: (raw, {**c, "extra": 1}), "BRIEFED"),
    (lambda raw, c: (raw, {**c, "status": "REFUSED"}), "BRIEFED"),
    (lambda raw, c: (raw, {**c, "brief_chunks": False}), "BRIEFED"),
    (lambda raw, c: (raw, {**c, "brief_bytes": len(raw) + 1}), "brief bytes"),
    (lambda raw, c: (raw, {k: v for k, v in c.items() if k != "persisted"}), "BRIEFED"),             # F-R13-1: a brief that was not persisted cannot be sealed
    (lambda raw, c: (raw, {**c, "persisted": {**c["persisted"], "manifest_id": "other"}}), "another manifest"),
    (lambda raw, c: (raw, {**c, "persisted": {**c["persisted"], "brief_id": 0}}), "not {brief_id"),
    (lambda raw, c: (raw, {**c, "persisted": {**c["persisted"], "brief_id": True}}), "not {brief_id"),
    (lambda raw, c: (raw, {**c, "persisted": {**c["persisted"], "state_digest": "zz"}}), "not {brief_id"),
    (lambda raw, c: (raw, {**c, "persisted": {**c["persisted"], "extra": 1}}), "not {brief_id"),
    (lambda raw, c: (raw, {**c, "persisted": True}), "not {brief_id"),
    (lambda raw, c: (b"", c), "empty"),
    (lambda raw, c: (raw, {k: v for k, v in c.items() if k != "contract_version"}), "BRIEFED"),                                   # a missing transport contract is refused
    (lambda raw, c: (raw, {**c, "contract_version": "seal_brief_transport/2"}), "transport contract"),                           # an unknown one too
    (lambda raw, c: (raw, {k: v for k, v in c.items() if k != "producer"}), "BRIEFED"),                                           # a brief of unknown producer
    (lambda raw, c: (raw, {**c, "producer": {**c["producer"], "commit": "b" * 40}}), "not this workflow's reviewed revision"),   # produced by other code
    (lambda raw, c: (raw, {**c, "producer": {**c["producer"], "image_digest": "latest"}}), "unknown producer"),
    (lambda raw, c: (raw, {**c, "producer": {**c["producer"], "execution_id": " "}}), "unknown producer"),
    (lambda raw, c: (raw, {**c, "producer": {**c["producer"], "extra": 1}}), "unknown producer"),
])
def test_a_malformed_or_altered_brief_is_refused(mut, needle):
    raw, c = mut(*pair())
    with pytest.raises(bc.Refused, match=needle):
        check(raw, c)


def test_a_non_canonical_but_self_consistent_brief_is_refused():
    """The digest of the FILE'S BYTES is the brief digest, so a file in some other JSON form could hash consistently; this script refuses it because the verifier's encoder and
    this one must agree on the canonical form (a difference would otherwise be approved under a digest the two sides compute differently)."""
    raw = json.dumps(payload(), indent=1).encode("utf-8")
    with pytest.raises(bc.Refused, match="canonical form"):
        check(raw, compact(raw=raw))


@pytest.mark.parametrize("over,needle", [
    ({"schema": "other/1"}, "schema"),
    ({"chart_id": "00000000-0000-0000-0000-000000000000"}, "another chart"),
    ({"generation": "4.1"}, "another chart or generation"),
    ({"manifest": {"manifest_id": "m", "status": "published"}}, "not a candidate"),
    ({"candidate_gate": {"violations": ["marriage/P3@1.0.0:output_grain_not_permitted"]}}, "not clean"),
    ({"result_policy": "numeric/1"}, "requires all_null_candidate/1"),
    ({"code": {"sealing_commit": "b" * 40}}, "not this workflow's reviewed revision"),
    ({"code": {}}, "not this workflow's reviewed revision"),
    ({"classes": []}, "no classes"),
    ({"classes": [{"event_class": "marriage", "grains": []}]}, "no persisted verification"),
    ({"classes": [{"event_class": "marriage", "grains": [{"path_id": "P1", "rule_version": "1.0.0", "status": "UNVERIFIED_DYNAMIC"}]}]}, "not VERIFIED"),
])
def test_a_brief_for_the_wrong_thing_is_refused_even_with_a_self_consistent_digest(over, needle):
    p = payload(**over)
    raw, c = pair(p)                                                                        # the digest is computed over the altered payload: it is self-consistent
    with pytest.raises(bc.Refused, match=needle):
        check(raw, c)


def test_the_workflow_revision_must_be_a_40_hex_sha():
    with pytest.raises(bc.Refused, match="40-hex"):
        check(*pair(), sealing_commit="main")


def test_the_canonical_digest_equals_the_sidecars_own_payload_digest_wherever_it_is_importable():
    """The script is stdlib-only and carries its own canonical JSON; where Stream A's `seal_brief` is importable (the integration ref) the two MUST agree byte for byte."""
    sidecar = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(sidecar))
    try:
        from services.gochara_kernel import seal_brief
    except Exception:                                                                       # noqa: BLE001 — not on this branch: the parity is asserted on the integration ref
        pytest.skip("NOT_RUN: services.gochara_kernel.seal_brief is not on this branch")
    for p in (payload(), {"a": [1, 2, {"b": None}], "z": Decimal("1.50"), "k": "é", "t": True}):
        assert bc.digest(p) == seal_brief.payload_digest(p)


# ── the log transport (Stream A's `--brief`, always chunked) ─────────────────────────────────────────────────────────────────────

def _entry(line, how="root"):
    """One Cloud Logging entry for a printed line. `root`: Cloud Run parses a JSON object on stdout into the ROOT `jsonPayload` (the real representation, R13-1); `text` and `message` are the
    FALLBACK forms (`textPayload`; a string in `jsonPayload.message`) and must go through the same validation. Labels/resource ride along: they are never consulted."""
    meta = {"resource": {"type": "cloud_run_job", "labels": {"job_name": "gochara-verification-job"}}, "labels": {"run.googleapis.com/execution_name": "exec-1"}}
    if how == "root":
        return {**meta, "jsonPayload": _struct(json.loads(line))}
    if how == "message":
        return {**meta, "jsonPayload": {"message": line}}
    return {**meta, "textPayload": line}


def _struct(doc):
    """What Cloud Run's protobuf Struct does to a printed JSON object: key order is lost and EVERY number becomes a double (3 -> 3.0). Reading must not depend on either."""
    def d(v):
        if isinstance(v, bool) or v is None or isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict):
            return {k: d(v[k]) for k in sorted(v, reverse=True)}
        return [d(x) for x in v]
    return d(doc)


def _logs(p=None, size=150, *, how="root", extra_before=(), extra_after=()):
    raw, c = pair(p)
    lines = bx.chunk_lines(raw, c["sha256"], size)
    compact_line = json.dumps(c, sort_keys=True, separators=(",", ":"))
    entries = [{"textPayload": "starting"}, *[_entry(x, "text") for x in extra_before], *[_entry(l, how) for l in lines], _entry(compact_line, how),
               *[_entry(x, "text") for x in extra_after], {"textPayload": "done"}]
    return raw, c, entries


def _is_chunk(e):
    jp = e.get("jsonPayload")
    return (isinstance(jp, dict) and "brief_chunk" in jp) or '"brief_chunk"' in (e.get("textPayload") or "") or '"brief_chunk"' in str((jp or {}).get("message"))


def _is_compact(e):
    jp = e.get("jsonPayload")
    return (isinstance(jp, dict) and jp.get("status") == "BRIEFED") or '"BRIEFED"' in (e.get("textPayload") or "") or '"BRIEFED"' in str((jp or {}).get("message"))


@pytest.mark.parametrize("how", ["root", "message", "text"])
def test_the_brief_is_reassembled_from_chunks_in_any_arrival_order_and_checks(how):
    raw, c, entries = _logs(how=how)
    chunks = [e for e in entries if _is_chunk(e)]
    assert len(chunks) > 3
    for order in (entries, entries[::-1], entries[1::2] + entries[0::2]):
        got, comp = bx.extract(order)
        assert got == raw and comp == c
    assert check(*bx.extract(entries[::-1])) == bc.digest(payload())
    got, _ = bx.extract(entries + [chunks[2]])                                               # an IDENTICAL repeat (at-least-once delivery) is TOLERATED: it cannot change the bytes
    assert got == raw


def test_an_identical_repeat_is_tolerated_for_chunks_and_for_the_compact_line_and_a_different_one_is_refused():
    """R13-1: 'exactly one' is decided and the code says what the prose says — a byte-identical repeat of a chunk or of the compact line is collapsed (at-least-once log delivery cannot alter
    the reassembled bytes, and the whole is hash-checked); anything DIFFERENT under the same index / a second distinct compact line is refused."""
    raw, c, entries = _logs()
    comp = next(e for e in entries if _is_compact(e))
    assert bx.extract(entries + [comp, comp])[0] == raw
    other = {"jsonPayload": {**comp["jsonPayload"], "persisted": {**comp["jsonPayload"]["persisted"], "brief_id": 99}}}
    with pytest.raises(ValueError, match="more than one distinct"):
        bx.extract(entries + [other])


def _chunk_edit(entries, idx, **over):
    out = list(entries)
    pos = [i for i, e in enumerate(entries) if _is_chunk(e)][idx]
    e = entries[pos]
    d = dict(e["jsonPayload"])
    d.update(over)
    out[pos] = {**e, "jsonPayload": d}
    return out


def _drop_chunk(entries, idx):
    pos = [i for i, e in enumerate(entries) if _is_chunk(e)][idx]
    return entries[:pos] + entries[pos + 1:]


def _edit_compact(entries, **over):
    return [e if not _is_compact(e) else {**e, "jsonPayload": {**e["jsonPayload"], **over}} for e in entries]


@pytest.mark.parametrize("mut,needle", [
    (lambda en: _drop_chunk(en, 1), "incomplete"),                                                       # a missing chunk
    (lambda en: _drop_chunk(en, -1), "incomplete"),                                                      # a truncated tail
    (lambda en: _chunk_edit(en, 0, b64=base64.b64encode(b"x" * 10).decode()), "not the one"),            # altered data
    (lambda en: _chunk_edit(en, 1, brief_chunk=0), "two different chunks carry index 0"),
    (lambda en: _chunk_edit(en, 1, of=99), "disagree"),
    (lambda en: _chunk_edit(en, 1, sha256="0" * 64), "disagree"),
    (lambda en: _chunk_edit(en, 1, brief_chunk=77), "incomplete or has foreign"),
    (lambda en: _chunk_edit(en, 1, b64=5), "malformed"),
    (lambda en: _chunk_edit(en, 1, b64="@@@@"), "base64"),
    (lambda en: [e for e in en if not _is_compact(e)], "no compact"),
    (lambda en: [e for e in en if not _is_chunk(e) and not _is_compact(e)], "no compact"),
    (lambda en: en + [{"jsonPayload": {"status": "REFUSED", "code": "gate_not_clean", "detail": "x"}}], "did not produce a brief"),
    (lambda en: _edit_compact(en, brief_chunks=False), "does not announce chunks"),
    (lambda en: _edit_compact(en, brief_bytes=3), "bytes, the compact line says"),
    (lambda en: _edit_compact(en, sha256="1" * 64), "not the one"),                                      # the compact line declares another digest than the chunks
    (lambda en: _edit_compact(en, extra=1), "malformed"),
    (lambda en: _edit_compact(en, contract_version="seal_brief_transport/2"), "contract_version"),          # an unknown transport contract
    (lambda en: _edit_compact(en, contract_version=None), "contract_version"),
    (lambda en: _edit_compact(en, producer={"commit": "x"}), "producer"),                                    # a brief of unknown producer
    (lambda en: _edit_compact(en, producer={"commit": " ", "execution_id": "e", "image_digest": "sha256:" + "a" * 64}), "producer"),
    (lambda en: _edit_compact(en, brief_bytes=3.5), "not an integer"),                                       # a non-integral double is refused, never rounded
    (lambda en: _edit_compact(en, brief_bytes=True), "boolean"),
    (lambda en: _chunk_edit(en, 1, brief_chunk=1.5), "not an integer"),
    (lambda en: _chunk_edit(en, 1, of=float("nan")), "not an integer"),
    (lambda en: _edit_compact(en, persisted={"brief_id": 2.5, "manifest_id": "m", "state_digest": "c" * 64}), "not an integer"),
    (lambda en: _edit_compact(en, sha256="1" * 63 + "\n"), "malformed|not the one"),                                # a trailing newline is not a digest (full-string validation)
])
def test_a_missing_altered_duplicated_or_mismatched_chunk_or_a_refusal_line_is_refused(mut, needle):
    _, _, entries = _logs()
    with pytest.raises(ValueError, match=needle):
        bx.extract(mut(entries))


def test_log_labels_and_resource_fields_are_never_producer_attestation():
    """Cloud Logging does not authenticate who wrote an entry, so the extractor must not select entries by labels: the same objects with the labels of ANOTHER execution/job still reassemble
    (and are checked by the execution check and the persisted brief id, not by what a log line says about itself)."""
    raw, c, entries = _logs()
    forged = [{**e, "resource": {"type": "other", "labels": {"job_name": "x"}}, "labels": {"run.googleapis.com/execution_name": "someone-else"}} if "jsonPayload" in e else e for e in entries]
    assert bx.extract(forged)[0] == raw


def test_the_log_export_must_be_a_json_array_and_unrelated_log_lines_are_ignored():
    with pytest.raises(ValueError, match="not a JSON array"):
        bx.extract({"not": "an array"})
    raw, c, entries = _logs(extra_before=['{"level": "info", "msg": "something else"}', "{not json"])
    entries.append({"jsonPayload": {"level": "info", "msg": "an unrelated structured line"}})
    assert bx.extract(entries) == (raw, c)


def test_chunks_of_the_real_size_stay_under_the_entry_limit():
    big = bc.canon({"classes": [{"event_class": f"c{i}", "x": "a" * 9000} for i in range(26)]}).encode()
    lines = bx.chunk_lines(big, hashlib.sha256(big).hexdigest())
    assert len(big) > 200 * 1024 and len(lines) >= 5
    assert max(len(l.encode("utf-8")) for l in lines) < 100 * 1024
    c = compact(raw=big)
    got, _ = bx.extract([_entry(l) for l in lines] + [_entry(json.dumps(c))])
    assert got == big


# ── the approval ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

D = bc.digest(payload())
BID = "7"                                                                                           # the persisted brief id carried by `compact()` above


def line(digest=None, run=None, att=None, bid=None):
    return f"brief-digest: {digest or D}  run: {run or RUN}  attempt: {att or ATT}  brief-id: {bid or BID}"


def review(state="approved", comment=None, login="steward-as-owner", env="gochara-seal"):
    return {"state": state, "comment": line() if comment is None else comment, "user": {"login": login}, "environments": [{"name": env}]}


PEID = "exec-1"


def _ex(history, attempt=ATT, digest=D, bid=BID, peid=PEID, **kw):
    return approval.extract(history, environment="gochara-seal", run_id=RUN, attempt=attempt, brief_digest=digest, brief_id=bid, producer_execution_id=peid,
                            triggering_actor="steward-as-owner", **kw)


def test_a_good_approval_yields_the_seal_jobs_approval_file():
    out = _ex([review()])
    assert out == {"schema": "seal_approval/2", "brief_digest": D, "brief_id": int(BID), "producer_execution_id": PEID, "run_id": int(RUN), "run_attempt": 1,
                   "approver_login": "steward-as-owner", "approved_by_note": approval.mechanical_note("steward-as-owner")}
    assert out["approved_by_note"] == "ruling:NATIVE_DIRECT_RULINGS_20261002#2; actor:steward-as-owner"


def test_the_note_is_exactly_stream_as_grammar_wherever_it_is_importable():
    """ONE format wins in both places: the workflow's note must satisfy `seal_flow.NOTE_FORMAT` (Stream A) — checked here for the integration ref, skipped where seal_flow is absent."""
    sidecar = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(sidecar))
    try:
        from services.gochara_kernel import seal_flow
    except Exception:                                                                       # noqa: BLE001
        pytest.skip("NOT_RUN: services.gochara_kernel.seal_flow is not on this branch")
    for actor in ("steward-as-owner", "amonty84", "github-actions[bot]", "a"):
        m = seal_flow.NOTE_FORMAT.match(approval.mechanical_note(actor))
        assert m and m.group("actor") == actor and m.group("ruling") == approval.RULING
    for text in (approval.mechanical_note("x") + "\n", approval.mechanical_note("x") + " (not an independent human check)"):
        assert not seal_flow.NOTE_FORMAT.match(text)


def test_the_note_is_mechanical_never_free_text_from_the_comment():
    """`approved_by_note` is built by the workflow (ruling id + triggering actor). Trailing text in the comment is not accepted as a note — it makes the line malformed and the approval is refused."""
    with pytest.raises(approval.Refused, match="no well-formed"):
        _ex([review(comment=line() + " note: I read it, trust me")])
    for bad in ("", "x y", "a;b", "$(id)", "a" * 60):
        with pytest.raises(approval.Refused, match="triggering actor"):
            approval.extract([review()], environment="gochara-seal", run_id=RUN, attempt=ATT, brief_digest=D, brief_id=BID, producer_execution_id=PEID, triggering_actor=bad)


@pytest.mark.parametrize("history,needle", [
    ([], "no approval of environment"),                                                          # absent
    ([review(env="some-other-environment")], "no approval of environment"),
    ([review(state="rejected")], "not approved"),
    ([review(comment="")], "no well-formed"),
    ([review(comment="approved")], "no well-formed"),                                           # malformed
    ([review(comment=f"brief-digest: {D}  run: {RUN}  attempt: {ATT}")], "no well-formed"),        # the pre-R13 grammar (no brief-id) is refused
    ([review(comment=line(digest=D[:40]))], "no well-formed"),
    ([review(comment=line(digest=D.upper()))], "no well-formed"),
    ([review(comment=line() + "\n\n")], None),                                                   # trailing blank lines are fine (splitlines); a trailing NEWLINE inside a line is not a form
    ([review(comment=line(run="999"))], "no approval of environment 'gochara-seal' names run"),   # wrong run: stale, never reused
    ([review(comment=line(att="2"))], "no approval of environment 'gochara-seal' names run"),     # wrong attempt: stale
    ([review(comment=line(digest="f" * 64))], "not the digest of the retained brief"),            # a changed brief
    ([review(comment=line(bid="8"))], "names persisted brief 8"),                                 # another persisted brief
    ([review(login="")], "no approver login"),
    ([review(comment=line() + "\n" + line(digest="e" * 64))], "ambiguous"),
])
def test_an_absent_malformed_wrong_run_wrong_attempt_or_stale_approval_is_refused(history, needle):
    if needle is None:
        assert _ex(history)["brief_digest"] == D
        return
    with pytest.raises(approval.Refused, match=needle):
        _ex(history)


@pytest.mark.parametrize("bad", ["", " ", "a b", "x\n", "a;b", "$(id)"])
def test_the_producer_execution_id_must_be_present_and_well_formed(bad):
    with pytest.raises(approval.Refused, match="producer execution id"):
        _ex([review()], peid=bad)


@pytest.mark.parametrize("bad", ["x" * 3, "0", "-1", "7\n", "7 ", ""])
def test_the_brief_id_the_workflow_expects_must_be_a_positive_integer(bad):
    with pytest.raises(approval.Refused, match="brief id"):
        _ex([review()], bid=bad)


def _att(n, state="approved", login="steward-as-owner", bid=BID):
    return review(state=state, login=login, comment=line(att=str(n), bid=bid))


@pytest.mark.parametrize("order", ["oldest_first", "newest_first"])
def test_the_approval_is_selected_by_the_attempt_it_names_never_by_the_apis_ordering(order):
    """R13-4: a legitimate re-run — attempt 1 was approved and its seal failed; attempt 2 is approved — is accepted whichever way the API orders its history; an approval of ONLY an earlier
    attempt is stale whichever way it is ordered."""
    hist = [_att(1), _att(2)]
    hist = hist if order == "oldest_first" else hist[::-1]
    assert _ex(hist, attempt="2")["run_attempt"] == 2
    assert _ex(hist, attempt="1")["run_attempt"] == 1
    with pytest.raises(approval.Refused, match="names run"):
        _ex([_att(1)], attempt="2")


@pytest.mark.parametrize("order", ["oldest_first", "newest_first"])
def test_any_ambiguity_for_this_attempt_refuses_whatever_the_order(order):
    """R13-4: an approval and a refusal of one attempt (either order), two approvals of one attempt, a comment with two lines, and a review that names no attempt at all each REFUSE and
    require a fresh run."""
    cases = (([_att(1), _att(1, state="rejected")], "not approved"),
             ([_att(1), _att(1, login="someone-else")], "more than one approval"),
             ([_att(1), review(state="rejected", comment="no")], "no well-formed"),
             ([_att(1), review(comment="lgtm")], "no well-formed"),
             ([_att(1), _att(1, bid="8")], "more than one approval"))
    for hist, needle in cases:
        with pytest.raises(approval.Refused, match=needle):
            _ex(hist if order == "oldest_first" else hist[::-1])


def test_a_rejection_that_names_another_attempt_does_not_block_this_attempt():
    assert _ex([_att(1, state="rejected"), _att(2)], attempt="2")["run_attempt"] == 2
    assert _ex([_att(2), _att(1, state="rejected")], attempt="2")["run_attempt"] == 2


# ── the executed resource and the retained envelope (R13-3) ───────────────────────────────────────────────────────────────────

IMG = "sha256:" + "a" * 64
SA = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
ARGS = ["--chart", CHART, "--generation", GEN, "--brief", "--sealing-commit", SHA]


REPO = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"


def execution(name="exec-1", **over):
    ex = {"metadata": {"name": name},
          "spec": {"taskCount": 1, "template": {"spec": {"serviceAccountName": SA, "maxRetries": 0,
                  "containers": [{"image": f"{REPO}@{IMG}", "command": list(xcheck_contract.ENTRYPOINT), "args": ARGS,
                                  "env": [{"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}, {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": IMG},
                                          {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url", "key": "latest"}}}]}]}}},
          "status": {"conditions": [{"type": "Completed", "status": "True"}], "succeededCount": 1}}
    for k, v in over.items():
        ex[k] = v
    return ex


def xcheck(ex=None, v2_execution=None, **over):
    kw = dict(v2_execution=v2_execution, execution_name="exec-1", image_repo=REPO, image_digest=IMG, service_account=SA, runner_commit=SHA, args=ARGS, secret_name="gochara-verifier-db-url")
    kw.update(over)
    return xc.check(execution() if ex is None else ex, **kw)


def _mut(path, value):
    ex = execution()
    d = ex
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = value
    return ex


T = ("spec", "template", "spec")


def _del(path):
    ex = execution()
    d = ex
    for k in path[:-1]:
        d = d[k]
    d.pop(path[-1])
    return ex


def test_the_executed_resource_is_verified_and_the_envelope_binds_run_attempt_commit_and_brief():
    v = xcheck()
    assert v["image_digest"] == IMG and v["execution"] == "exec-1"
    env = xc.build_envelope(v, run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id=7, producer_execution_id=PEID)
    assert xc.check_envelope(env, run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id="7") == env
    assert xc.check_envelope(json.loads(json.dumps(env)), run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id="7")


@pytest.mark.parametrize("ex,needle", [
    (_mut(("metadata", "name"), "another"), "not 'exec-1'"),
    (_mut((*T, "containers", 0, "image"), "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:" + SHA), "image is"),               # a tag, not a digest
    (_mut((*T, "containers", 0, "image"), "x/brahma-pipeline@sha256:" + "b" * 64), "image is"),                                                    # another digest
    (_mut((*T, "serviceAccountName"), "github-actions@madhav-astrology.iam.gserviceaccount.com"), "service account is"),
    (_mut((*T, "containers", 0, "env"), [{"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": IMG}, {"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}]), "environment variables"),                                  # no secret
    (_mut((*T, "containers", 0, "env"), [{"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": IMG}, {"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}, {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "data-plane-builder-db-url"}}}]), "reference to the secret"),
    (_mut((*T, "containers", 0, "env"), [{"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": IMG}, {"name": "GOCHARA_RUNNER_COMMIT", "value": "b" * 40}, {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url"}}}]), "RUNNER_COMMIT"),
    (_mut((*T, "containers", 0, "args"), ARGS[:-1] + ["b" * 40]), "args are"),
    (_mut((*T, "containers", 0, "env"), [{"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}, {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url"}}}]), "RUNNER_IMAGE_DIGEST"),   # no digest env: the verifier would refuse to brief
    (_mut((*T, "containers", 0, "env"), [{"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}, {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": "sha256:" + "b" * 64}, {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url"}}}]), "RUNNER_IMAGE_DIGEST"),
    (_mut((*T, "maxRetries"), 3), "maxRetries"),
    (_mut((*T, "containers", 0, "command"), ["python", "-m", "pipeline.orchestrator.main"]), "command"),                 # R14-3: the builder entry point swapped back
    (_mut((*T, "containers", 0, "command"), None), "command"),                                                          # …or the command omitted
    (_mut((*T, "containers", 0, "env"), [*execution()["spec"]["template"]["spec"]["containers"][0]["env"], {"name": "EXTRA", "value": "x"}]), "environment variables"),   # an extra variable
    (_mut((*T, "containers", 0, "env", 0), {"name": "GOCHARA_RUNNER_COMMIT", "valueFrom": {"secretKeyRef": {"name": "x"}}}), "plain value"),
    (_mut((*T, "volumes"), [{"name": "s", "secret": {"secretName": "gochara-verifier-db-url"}}]), "volumes"),            # a secret volume
    (_mut((*T, "containers", 0, "volumeMounts"), [{"name": "s", "mountPath": "/secrets"}]), "volumeMounts"),
    (_mut((*T, "containers", 0, "envFrom"), [{"secretRef": {"name": "data-plane-builder-db-url"}}]), "envFrom"),
    (_mut((*T, "containers"), [execution()["spec"]["template"]["spec"]["containers"][0], {"image": "x"}]), "not exactly one"),   # a sidecar
    (_del((*T, "maxRetries")), "maxRetries"),                                                                          # R14-3: ABSENT retries is the API default of 3, never zero
    (_mut(("spec", "taskCount"), 2), "more than one task"),
    (_mut(("status", "conditions"), [{"type": "Completed", "status": "False"}]), "FAILED"),
    (_mut(("status", "succeededCount"), 0), "RUNNING"),
    (_mut((*T, "containers"), []), "not exactly one"),
])
def test_an_execution_that_is_not_the_deployed_verifier_at_this_commit_is_refused(ex, needle):
    with pytest.raises(xc.Refused, match=needle):
        xcheck(ex)


def test_a_job_style_nesting_is_accepted_and_a_shapeless_resource_is_refused():
    ex = execution()
    nested = {"metadata": ex["metadata"], "spec": {"taskCount": 1, "template": {"spec": {"template": ex["spec"]["template"]}}}, "status": ex["status"]}
    assert xcheck(nested)["execution"] == "exec-1"
    with pytest.raises(xc.Refused, match="no container specification"):
        xcheck({"metadata": {"name": "exec-1"}, "spec": {}})


@pytest.mark.parametrize("mut,needle", [
    (lambda e: {**e, "run_attempt": 2}, "run_attempt"),                      # a brief of another attempt is never reused
    (lambda e: {**e, "run_id": 5}, "run_id"),
    (lambda e: {**e, "sealing_commit": "c" * 40}, "commit"),
    (lambda e: {**e, "runner_commit": "c" * 40}, "commit"),
    (lambda e: {**e, "brief_digest": "f" * 64}, "digest"),
    (lambda e: {**e, "brief_id": 8}, "persisted brief id"),
    (lambda e: {**e, "brief_id": True}, "persisted brief id"),
    (lambda e: {**e, "image_digest": "latest"}, "image digest"),
    (lambda e: {**e, "producer_execution_id": "another-execution"}, "producer execution id"),
    (lambda e: {**e, "producer_execution_id": " "}, "producer execution id"),
    (lambda e: {**e, "extra": 1}, "not a seal_execution_envelope"),
    (lambda e: {k: v for k, v in e.items() if k != "execution"}, "not a seal_execution_envelope"),
])
def test_the_retained_envelope_must_be_for_this_run_attempt_commit_and_brief(mut, needle):
    env = xc.build_envelope(xcheck(), run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id=7, producer_execution_id=PEID)
    with pytest.raises(xc.Refused, match=needle):
        xc.check_envelope(mut(env), run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id="7")


def _v2_execution(retries=0):
    """The v2 REST `executions.get` representation: the task template is at `template`, and `maxRetries` is a union (oneof) member — present when set, even when 0."""
    t = {"containers": [{"image": "x"}]}
    if retries is not None:
        t["maxRetries"] = retries
    return {"name": "projects/p/locations/l/jobs/j/executions/exec-1", "template": t}


def test_maxretries_is_read_from_the_presence_bearing_v2_representation_and_absence_is_never_zero():
    """F-R15-3: v1 omits the field -> the v2 value decides (a real 0 is accepted); absent in BOTH -> refused; present and different -> refused; never 'absent = 0'."""
    absent_v1 = _del((*T, "maxRetries"))
    assert xcheck(absent_v1, v2_execution=_v2_execution(0))["execution"] == "exec-1"            # v1 omitted a proto3 zero; v2 carries it
    with pytest.raises(xc.Refused, match="maxRetries"):
        xcheck(absent_v1, v2_execution=_v2_execution(None))                                    # absent in BOTH ⇒ the API default of 3
    with pytest.raises(xc.Refused, match="maxRetries"):
        xcheck(absent_v1, v2_execution=_v2_execution(3))
    with pytest.raises(xc.Refused, match="disagrees"):
        xcheck(execution(), v2_execution=_v2_execution(3))                                      # v1 says 0, v2 says 3
    assert xcheck(execution(), v2_execution=_v2_execution(0))["execution"] == "exec-1"
    assert xcheck(execution(), v2_execution=_v2_execution(None))["execution"] == "exec-1"       # v1 carries it; v2 absent is not a contradiction
    with pytest.raises(xc.Refused, match="maxRetries"):
        xcheck(absent_v1)                                                                      # no v2 supplied: strict v1 rule stands


def test_retries_from_v2_reads_jobs_and_executions_and_never_defaults():
    import gochara_verification_job_contract as vjc
    assert vjc.retries_from_v2({"template": {"template": {"maxRetries": 0}}}, "job") == 0
    assert vjc.retries_from_v2({"template": {"maxRetries": 0}}, "execution") == 0
    assert vjc.retries_from_v2({"template": {"template": {}}}, "job") is None
    assert vjc.retries_from_v2({"template": {"maxRetries": True}}, "execution") is None
    assert vjc.retries_from_v2(None, "job") is None


PROD = {"commit": SHA, "execution_id": PEID, "image_digest": IMG}


def test_the_briefs_producer_must_be_the_resource_this_workflow_read():
    """ST-WIRE-2: the compact line's producer (commit, execution id, image digest) is bound to the EXECUTED resource — a brief produced by another image, another execution or other code is refused."""
    v = xcheck()
    xc.bind_producer(v, PROD, execution_name="exec-1", sealing_commit=SHA)
    xc.bind_producer(v, {**PROD, "execution_id": "projects/p/locations/l/jobs/j/executions/exec-1"}, execution_name="exec-1", sealing_commit=SHA)   # the long resource form is the same execution
    for bad, needle in (({**PROD, "image_digest": "sha256:" + "b" * 64}, "image digest"), ({**PROD, "execution_id": "exec-2"}, "execution id"),
                        ({**PROD, "execution_id": "xexec-1"}, "execution id"), ({**PROD, "commit": "c" * 40}, "commit")):
        with pytest.raises(xc.Refused, match=needle):
            xc.bind_producer(v, bad, execution_name="exec-1", sealing_commit=SHA)


def test_the_execution_state_drives_the_wait_loop():
    assert xc.state(execution()) == "SUCCEEDED"
    assert xc.state({"status": {}}) == "RUNNING"
    assert xc.state({"status": {"conditions": [{"type": "Completed", "status": "False"}]}}) == "FAILED"
    assert xc.state({"status": {"failedCount": 1}}) == "FAILED"
    assert xc.state({"status": {"cancelledCount": 1}}) == "FAILED"


# ── the reconciliation after the seal (R13-4) ───────────────────────────────────────────────────────────────────────────────────

def _rc(pub, seals, recs):
    return rc_.classify(pub, seals, recs, digest=D, run_id=int(RUN), attempt=int(ATT))[0]


@pytest.mark.parametrize("pub,seals,recs,want", [
    ("candidate", 0, [], "NOT_SEALED"),
    ("published", 1, [{"brief_digest": D, "run_id": int(RUN), "run_attempt": int(ATT)}], "SEALED"),
    ("published", 1, [{"brief_digest": "f" * 64, "run_id": int(RUN), "run_attempt": int(ATT)}], "INCONSISTENT"),
    ("published", 1, [{"brief_digest": D, "run_id": 5, "run_attempt": int(ATT)}], "INCONSISTENT"),
    ("published", 1, [{"brief_digest": D, "run_id": int(RUN), "run_attempt": 2}], "INCONSISTENT"),
    ("published", 1, [], "INCONSISTENT"),                      # a seal without a receipt
    ("published", 0, [], "INCONSISTENT"),                      # published but not sealed
    ("candidate", 1, [], "INCONSISTENT"),
    (None, 0, [], "INCONSISTENT"),                             # no publication row at all
])
def test_the_reconcile_classifies_what_is_actually_true(pub, seals, recs, want):
    assert _rc(pub, seals, recs) == want


def test_an_unreadable_database_is_unknown_never_not_sealed(monkeypatch, capsys):
    monkeypatch.delenv("GOCHARA_SEALER_DB_URL", raising=False)
    assert rc_.main(["--chart-id", CHART, "--generation", GEN, "--brief-digest", D, "--run-id", RUN, "--attempt", ATT]) == 12
    assert json.loads(capsys.readouterr().out)["state"] == "UNREADABLE"


ORCH = SCRIPTS / "gochara-seal-approved.sh"


@pytest.fixture()
def world(tmp_path):
    shim = tmp_path / "seal_job"
    calls = tmp_path / "seal_job_calls.txt"
    shim.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\necho "COMMIT=$GOCHARA_SEALING_COMMIT ACTOR=${{GITHUB_TRIGGERING_ACTOR:-unset}} DB=${{GOCHARA_SEALER_DB_URL:-unset}}" >> "{calls}"\nexit "${{SEAL_RC:-0}}"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    brief, comp, envf = tmp_path / "brief.json", tmp_path / "brief.compact.json", tmp_path / "brief.envelope.json"
    raw, c = pair()
    brief.write_bytes(raw)
    comp.write_text(json.dumps(c))
    envf.write_text(json.dumps(xc.build_envelope(xcheck(), run_id=RUN, attempt=ATT, sealing_commit=SHA, brief_digest=D, brief_id=int(BID), producer_execution_id=PEID)))
    approvals = tmp_path / "approvals.json"
    approvals.write_text(json.dumps([review()]))
    return {"tmp": tmp_path, "shim": str(shim), "calls": calls, "brief": brief, "compact": comp, "envelope": envf, "approvals": approvals}


def orch(world, **over):
    env = {**os.environ, "BRIEF_FILE": str(world["brief"]), "BRIEF_COMPACT_FILE": str(world["compact"]), "BRIEF_ENVELOPE_FILE": str(world["envelope"]), "APPROVALS_FILE": str(world["approvals"]), "CHART_ID": CHART, "GENERATION": GEN,
           "EXPECTED_SEALING_COMMIT": SHA, "EXPECTED_BRIEF_DIGEST": D, "GITHUB_RUN_ID": RUN, "GITHUB_RUN_ATTEMPT": ATT, "GITHUB_SHA": SHA, "TRIGGERING_ACTOR": "steward-as-owner",
           "SEAL_JOB_CMD": world["shim"], "APPROVAL_FILE": str(world["tmp"] / "approval.json"), "PYTHON_BIN": sys.executable,
           "GOCHARA_SEALER_DB_URL": "postgresql://gochara_sealer:SECRETMARKER@127.0.0.1:5432/x", **over}
    return subprocess.run(["bash", str(ORCH)], env=env, capture_output=True, text=True, timeout=60)


def called(world):
    return world["calls"].exists()


def test_the_orchestrator_calls_the_seal_job_once_with_the_approval_file_and_the_reviewed_commit(world):
    r = orch(world)
    assert r.returncode == 0 and "SEALED" in r.stdout, r.stdout + r.stderr
    lines = world["calls"].read_text().splitlines()
    assert lines[0] == f"--chart {CHART} --generation {GEN} --approval-file {world['tmp'] / 'approval.json'}" and f"COMMIT={SHA} ACTOR=steward-as-owner" in lines[1]
    af = json.loads((world["tmp"] / "approval.json").read_text())
    assert af["brief_digest"] == D
    assert af["schema"] == "seal_approval/2" and af["brief_id"] == int(BID) and af["producer_execution_id"] == PEID        # ST-WIRE-2: /1 is refused by the seal job
    assert "SECRETMARKER" not in r.stdout + r.stderr and "SECRETMARKER" not in lines[0]                 # the sealer DSN is in the seal job's ENVIRONMENT only


@pytest.mark.parametrize("what", ["changed_brief", "wrong_revision_in_brief", "job_runs_from_another_commit", "no_approval", "wrong_run", "wrong_attempt", "stale_digest", "malformed_comment",
                                  "brief_digest_differs_from_the_published_one", "envelope_of_another_attempt", "envelope_of_another_brief", "approval_names_another_brief_id", "pre_r13_grammar",
                                  "seal_only_rerun_without_a_fresh_brief"])
def test_every_refusal_stops_before_the_seal_job_is_invoked(world, what):
    over = {}
    if what == "changed_brief":
        world["brief"].write_bytes(_flip(world["brief"].read_bytes()))
    elif what == "wrong_revision_in_brief":
        raw, c = pair(payload(code={"sealing_commit": "c" * 40}))
        world["brief"].write_bytes(raw)
        world["compact"].write_text(json.dumps(c))
    elif what == "job_runs_from_another_commit":
        over["GITHUB_SHA"] = "d" * 40
    elif what == "no_approval":
        world["approvals"].write_text("[]")
    elif what == "wrong_run":
        world["approvals"].write_text(json.dumps([review(comment=line(run="5"))]))
    elif what == "wrong_attempt":
        over["GITHUB_RUN_ATTEMPT"] = "2"
    elif what == "seal_only_rerun_without_a_fresh_brief":
        # attempt 2 re-runs ONLY the seal job: the approval for attempt 2 exists but the retained brief envelope is attempt 1's — it must NOT be reused
        over["GITHUB_RUN_ATTEMPT"] = "2"
        world["approvals"].write_text(json.dumps([review(comment=line(att="2"))]))
    elif what == "stale_digest":
        world["approvals"].write_text(json.dumps([review(comment=line(digest="1" * 64))]))
    elif what == "envelope_of_another_attempt":
        e = json.loads(world["envelope"].read_text()); e["run_attempt"] = 2; world["envelope"].write_text(json.dumps(e))
    elif what == "envelope_of_another_brief":
        e = json.loads(world["envelope"].read_text()); e["brief_id"] = 99; world["envelope"].write_text(json.dumps(e))
    elif what == "approval_names_another_brief_id":
        world["approvals"].write_text(json.dumps([review(comment=line(bid="99"))]))
    elif what == "pre_r13_grammar":
        world["approvals"].write_text(json.dumps([review(comment=f"brief-digest: {D}  run: {RUN}  attempt: {ATT}")]))
    elif what == "malformed_comment":
        world["approvals"].write_text(json.dumps([review(comment="looks good")]))
    elif what == "brief_digest_differs_from_the_published_one":
        over["EXPECTED_BRIEF_DIGEST"] = "2" * 64
    r = orch(world, **over)
    assert r.returncode == 2 and "nothing was sealed" in r.stderr or "REFUSED" in r.stderr, (what, r.returncode, r.stdout, r.stderr)
    assert r.returncode != 0 and not called(world), (what, "the seal job must NOT be invoked after a refusal")


def test_a_disagreeing_triggering_actor_is_refused_before_the_seal_job(world):
    r = orch(world, GITHUB_TRIGGERING_ACTOR="someone-else")
    assert r.returncode == 2 and "differs from the workflow's triggering actor" in r.stderr and not called(world)


@pytest.mark.parametrize("rc,needle", [(2, "SEAL JOB REFUSED"), (3, "approval does not match"), (4, "OWN-CHECKOUT check failed"), (5, "rolled back"), (7, "rolled back")])
def test_the_seal_jobs_non_zero_status_fails_the_run_unchanged(world, rc, needle):
    """Including a failure AFTER publication: the seal job owns the transaction and rolls publication back; the workflow's job is to FAIL the run and say so (never swallow it)."""
    r = orch(world, SEAL_RC=str(rc))
    assert r.returncode == rc and needle in r.stderr, (rc, r.stdout, r.stderr)
    assert called(world)


# R14-3: the verification-job contract is ONE file carried by BOTH #2975 (executed-resource check) and #2976 (definition readback). If the two copies ever diverge, one of these two tests fails
# (the pinned digest is the same constant in both PRs; change it in both when the contract is deliberately changed).
CONTRACT_SHA256 = "3cd8ece1dcb0427b1436996b9c1aec6f7eb6509c951bb903398f7474b6a726fd"


def test_the_shared_verification_job_contract_is_the_file_both_prs_carry():
    import hashlib
    import gochara_verification_job_contract as _vjc
    assert hashlib.sha256(Path(_vjc.__file__).read_bytes()).hexdigest() == CONTRACT_SHA256
