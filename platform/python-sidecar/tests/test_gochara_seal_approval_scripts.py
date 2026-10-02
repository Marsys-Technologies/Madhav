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
    """The verifier job's last output line (Stream A head 7e81f2870): `{status: BRIEFED, sha256, persisted, brief_bytes, brief_file, brief_chunks}`."""
    p = payload() if p is None else p
    raw = brief_raw(p) if raw is None else raw
    c = {"brief_bytes": len(raw), "brief_chunks": True, "brief_file": None, "sha256": hashlib.sha256(raw).hexdigest(), "status": "BRIEFED",
         "persisted": {"brief_id": 7, "manifest_id": p.get("manifest", {}).get("manifest_id"), "state_digest": "c" * 64}}
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


# ── the log transport (Stream A's `--brief --brief-chunks`) ─────────────────────────────────────────────────────────────────────

def _logs(p=None, size=150, *, extra_before=(), extra_after=()):
    raw, c = pair(p)
    lines = bx.chunk_lines(raw, c["sha256"], size)
    entries = [{"textPayload": "starting"}, *[{"textPayload": x} for x in extra_before], *[{"textPayload": l} for l in lines],
               {"textPayload": json.dumps(c, sort_keys=True, separators=(",", ":"))}, *[{"textPayload": x} for x in extra_after], {"textPayload": "done"}]
    return raw, c, entries


def test_the_brief_is_reassembled_from_chunks_in_any_arrival_order_and_checks():
    raw, c, entries = _logs()
    chunks = [e for e in entries if e["textPayload"].startswith('{"b64"')]
    assert len(chunks) > 3
    for order in (entries, entries[::-1], sorted(entries, key=lambda e: e["textPayload"])):
        got, comp = bx.extract(order)
        assert got == raw and comp == c
    assert check(*bx.extract(entries[::-1])) == bc.digest(payload())
    got, _ = bx.extract(entries + [chunks[2]])                                               # an identical repeat (at-least-once delivery) is harmless
    assert got == raw
    assert bx.extract([{"jsonPayload": {"message": e["textPayload"]}} for e in entries])[0] == raw


def _chunk_edit(entries, idx, **over):
    out = list(entries)
    pos = [i for i, e in enumerate(entries) if e["textPayload"].startswith('{"b64"')][idx]
    d = json.loads(entries[pos]["textPayload"])
    d.update(over)
    out[pos] = {"textPayload": json.dumps(d)}
    return out


def _drop_chunk(entries, idx):
    pos = [i for i, e in enumerate(entries) if e["textPayload"].startswith('{"b64"')][idx]
    return entries[:pos] + entries[pos + 1:]


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
    (lambda en: [e for e in en if not e["textPayload"].startswith('{"brief_bytes"')], "no compact"),
    (lambda en: [e for e in en if e["textPayload"].startswith(('starting', 'done'))], "no compact"),
    (lambda en: en + [{"textPayload": json.dumps({**compact(), "sha256": "1" * 64}, sort_keys=True)}], "more than one distinct"),
    (lambda en: en + [{"textPayload": json.dumps({"status": "REFUSED", "code": "gate_not_clean", "detail": "x"})}], "did not produce a brief"),
    (lambda en: [e if not e["textPayload"].startswith('{"brief_bytes"') else {"textPayload": json.dumps({**json.loads(e["textPayload"]), "brief_chunks": False})} for e in en], "not run with --brief-chunks"),
    (lambda en: [e if not e["textPayload"].startswith('{"brief_bytes"') else {"textPayload": json.dumps({**json.loads(e["textPayload"]), "brief_bytes": 3})} for e in en], "bytes, the compact line says"),
])
def test_a_missing_altered_duplicated_or_mismatched_chunk_or_a_refusal_line_is_refused(mut, needle):
    _, _, entries = _logs()
    with pytest.raises(ValueError, match=needle):
        bx.extract(mut(entries))


def test_the_log_export_must_be_a_json_array_and_unrelated_log_lines_are_ignored():
    with pytest.raises(ValueError, match="not a JSON array"):
        bx.extract({"not": "an array"})
    raw, c, entries = _logs(extra_before=['{"level": "info", "msg": "something else"}', "{not json"])
    assert bx.extract(entries) == (raw, c)


def test_chunks_of_the_real_size_stay_under_the_entry_limit():
    big = bc.canon({"classes": [{"event_class": f"c{i}", "x": "a" * 9000} for i in range(26)]}).encode()
    lines = bx.chunk_lines(big, hashlib.sha256(big).hexdigest())
    assert len(big) > 200 * 1024 and len(lines) >= 5
    assert max(len(l.encode("utf-8")) for l in lines) < 100 * 1024
    c = compact(raw=big)
    got, _ = bx.extract([{"textPayload": l} for l in lines] + [{"textPayload": json.dumps(c)}])
    assert got == big


# ── the approval ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

D = bc.digest(payload())


def review(state="approved", comment=None, login="steward-as-owner", env="gochara-seal"):
    c = f"brief-digest: {D}  run: {RUN}  attempt: {ATT}" if comment is None else comment
    return {"state": state, "comment": c, "user": {"login": login}, "environments": [{"name": env}]}


def test_a_good_approval_yields_the_seal_jobs_approval_file():
    out = approval.extract([review()], environment="gochara-seal", run_id=RUN, attempt=ATT, brief_digest=D, triggering_actor="steward-as-owner")
    assert out == {"schema": "seal_approval/1", "brief_digest": D, "run_id": int(RUN), "run_attempt": 1, "approver_login": "steward-as-owner",
                   "approved_by_note": approval.mechanical_note("steward-as-owner")}
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
    """Fable: `approved_by_note` is built by the workflow (ruling id + triggering actor + the fixed statement). Trailing text in the comment is not accepted as a note — it makes the
    comment line malformed and the approval is refused."""
    with pytest.raises(approval.Refused, match="no `brief-digest"):
        approval.extract([review(comment=f"brief-digest: {D} run: {RUN} attempt: {ATT} note: I read it, trust me")], environment="gochara-seal", run_id=RUN, attempt=ATT,
                         brief_digest=D, triggering_actor="steward-as-owner")
    for bad in ("", "x y", "a;b", "$(id)", "a" * 60):
        with pytest.raises(approval.Refused, match="triggering actor"):
            approval.extract([review()], environment="gochara-seal", run_id=RUN, attempt=ATT, brief_digest=D, triggering_actor=bad)


@pytest.mark.parametrize("history,needle", [
    ([], "no approval of environment"),                                                          # absent
    ([review(env="some-other-environment")], "no approval of environment"),
    ([review(state="rejected")], "not approved"),
    ([review(comment="")], "no comment"),
    ([review(comment="approved")], "no `brief-digest"),                                         # malformed
    ([review(comment=f"brief-digest: {D[:40]}  run: {RUN}  attempt: {ATT}")], "no `brief-digest"),
    ([review(comment=f"brief-digest: {D.upper()}  run: {RUN}  attempt: {ATT}")], "no `brief-digest"),
    ([review(comment=f"brief-digest: {D}  run: 999  attempt: {ATT}")], "this is run"),            # wrong run
    ([review(comment=f"brief-digest: {D}  run: {RUN}  attempt: 2")], "stale approval"),          # wrong attempt
    ([review(comment=f"brief-digest: {'f' * 64}  run: {RUN}  attempt: {ATT}")], "not the digest of the retained brief"),   # stale / changed brief
    ([review(login="")], "no approver login"),
    ([review(comment=f"brief-digest: {D}  run: {RUN}  attempt: {ATT}\nbrief-digest: {'e' * 64}  run: {RUN}  attempt: {ATT}")], "ambiguous"),
])
def test_an_absent_malformed_wrong_run_wrong_attempt_or_stale_approval_is_refused(history, needle):
    with pytest.raises(approval.Refused, match=needle):
        approval.extract(history, environment="gochara-seal", run_id=RUN, attempt=ATT, brief_digest=D, triggering_actor="steward-as-owner")


def _ex(history, attempt=ATT):
    return approval.extract(history, environment="gochara-seal", run_id=RUN, attempt=attempt, brief_digest=D, triggering_actor="steward-as-owner")


def _att(n, state="approved", login="steward-as-owner"):
    return review(state=state, login=login, comment=f"brief-digest: {D}  run: {RUN}  attempt: {n}")


@pytest.mark.parametrize("order", ["oldest_first", "newest_first"])
def test_the_approval_is_selected_by_the_attempt_it_names_never_by_the_apis_ordering(order):
    """F-R13-5: a legitimate re-run — attempt 1 was approved and its seal failed; attempt 2 is approved — is accepted whichever way the API orders its history; and an approval
    of ONLY an earlier attempt is stale whichever way it is ordered."""
    hist = [_att(1), _att(2)]
    hist = hist if order == "oldest_first" else hist[::-1]
    assert _ex(hist, attempt="2")["run_attempt"] == 2
    assert _ex(hist, attempt="1")["run_attempt"] == 1
    with pytest.raises(approval.Refused, match="stale approval"):
        _ex([_att(1)] if order == "oldest_first" else [_att(1)], attempt="2")


@pytest.mark.parametrize("order", ["oldest_first", "newest_first"])
def test_a_refusing_review_of_this_attempt_or_a_second_approval_of_it_refuses_whatever_the_order(order):
    for hist, needle in (([_att(1), _att(1, state="rejected")], "not approved"), ([_att(1), _att(1, login="someone-else")], "ambiguous"),
                         ([_att(1), review(state="rejected", comment="no")], "not approved")):
        with pytest.raises(approval.Refused, match=needle):
            _ex(hist if order == "oldest_first" else hist[::-1])


def test_a_rejection_that_names_another_attempt_does_not_block_this_attempt_and_a_malformed_old_approval_does_not_rescue_a_bad_one():
    assert _ex([_att(1, state="rejected"), _att(2)], attempt="2")["run_attempt"] == 2
    assert _ex([review(comment="lgtm"), _att(2)], attempt="2")["run_attempt"] == 2        # a malformed old approval is ignored when exactly one well-formed one names this attempt
    with pytest.raises(approval.Refused, match="no `brief-digest"):
        _ex([review(comment="lgtm")])                                                      # …and never selected on its own


# ── the gated orchestrator (the unit the `seal` job runs) ───────────────────────────────────────────────────────────────────────

ORCH = SCRIPTS / "gochara-seal-approved.sh"


@pytest.fixture()
def world(tmp_path):
    shim = tmp_path / "seal_job"
    calls = tmp_path / "seal_job_calls.txt"
    shim.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\necho "COMMIT=$GOCHARA_SEALING_COMMIT ACTOR=${{GITHUB_TRIGGERING_ACTOR:-unset}} DB=${{GOCHARA_SEALER_DB_URL:-unset}}" >> "{calls}"\nexit "${{SEAL_RC:-0}}"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    brief, comp = tmp_path / "brief.json", tmp_path / "brief.compact.json"
    raw, c = pair()
    brief.write_bytes(raw)
    comp.write_text(json.dumps(c))
    approvals = tmp_path / "approvals.json"
    approvals.write_text(json.dumps([review()]))
    return {"tmp": tmp_path, "shim": str(shim), "calls": calls, "brief": brief, "compact": comp, "approvals": approvals}


def orch(world, **over):
    env = {**os.environ, "BRIEF_FILE": str(world["brief"]), "BRIEF_COMPACT_FILE": str(world["compact"]), "APPROVALS_FILE": str(world["approvals"]), "CHART_ID": CHART, "GENERATION": GEN,
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
    assert json.loads((world["tmp"] / "approval.json").read_text())["brief_digest"] == D
    assert "SECRETMARKER" not in r.stdout + r.stderr and "SECRETMARKER" not in lines[0]                 # the sealer DSN is in the seal job's ENVIRONMENT only


@pytest.mark.parametrize("what", ["changed_brief", "wrong_revision_in_brief", "job_runs_from_another_commit", "no_approval", "wrong_run", "wrong_attempt", "stale_digest", "malformed_comment",
                                  "brief_digest_differs_from_the_published_one"])
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
        world["approvals"].write_text(json.dumps([review(comment=f"brief-digest: {D}  run: 5  attempt: {ATT}")]))
    elif what == "wrong_attempt":
        over["GITHUB_RUN_ATTEMPT"] = "2"
    elif what == "stale_digest":
        world["approvals"].write_text(json.dumps([review(comment=f"brief-digest: {'1' * 64}  run: {RUN}  attempt: {ATT}")]))
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


@pytest.mark.parametrize("rc,needle", [(2, "REFUSED"), (3, "approval does not match"), (4, "identity check failed"), (5, "rolled back"), (7, "rolled back")])
def test_the_seal_jobs_non_zero_status_fails_the_run_unchanged(world, rc, needle):
    """Including a failure AFTER publication: the seal job owns the transaction and rolls publication back; the workflow's job is to FAIL the run and say so (never swallow it)."""
    r = orch(world, SEAL_RC=str(rc))
    assert r.returncode == rc and needle in r.stderr, (rc, r.stdout, r.stderr)
    assert called(world)
