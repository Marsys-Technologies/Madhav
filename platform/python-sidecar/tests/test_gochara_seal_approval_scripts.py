"""R12-2 — the sealing workflow's scripts: the brief check, the log extraction, the approval extraction and the gated orchestrator (the unit the `seal` job runs).

Every refusal is tested at the OUTERMOST boundary (the exit status of the script the workflow calls) and the orchestrator test proves the seal job is NEVER invoked after a
refusal. No database: the seal job is a recording shim here (Stream A's `seal_job` is the real caller; its transaction behaviour is tested against PostgreSQL in the
composed rehearsal)."""
from __future__ import annotations

import copy
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


def brief_text(p=None, digest=None):
    p = payload() if p is None else p
    return json.dumps({"brief": p, "persisted": {"brief_id": 7, "manifest_id": p.get("manifest", {}).get("manifest_id"), "state_digest": "c" * 64}, "sha256": digest or bc.digest(p)})


# ── the brief check ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_good_brief_verifies_and_returns_its_digest():
    p = payload()
    assert bc.check(brief_text(p), chart_id=CHART, generation=GEN, sealing_commit=SHA) == bc.digest(p)


@pytest.mark.parametrize("mut,needle", [
    (lambda d: d.update(sha256="0" * 64), "truncated or altered"),                                    # a changed brief
    (lambda d: d["brief"].update(result_policy="numeric_policy/1"), "hashes to"),                      # (digest no longer matches the payload)
    (lambda d: d.update(sha256="XYZ"), "64-hex"),
    (lambda d: d.pop("sha256"), "exactly"),
    (lambda d: d.update(extra=1), "exactly"),
    (lambda d: d.pop("persisted"), "exactly"),                                                        # F-R13-1: the verifier's real output carries `persisted`; a brief without it was never persisted
    (lambda d: d["persisted"].update(manifest_id="other"), "another manifest"),
    (lambda d: d["persisted"].update(brief_id=0), "not {brief_id"),
    (lambda d: d["persisted"].update(brief_id=True), "not {brief_id"),
    (lambda d: d["persisted"].update(state_digest="zz"), "not {brief_id"),
    (lambda d: d["persisted"].update(extra=1), "not {brief_id"),
    (lambda d: d.update(persisted=True), "not {brief_id"),
])
def test_a_malformed_or_altered_brief_is_refused(mut, needle):
    d = json.loads(brief_text())
    mut(d)
    with pytest.raises(bc.Refused, match=needle):
        bc.check(json.dumps(d), chart_id=CHART, generation=GEN, sealing_commit=SHA)


@pytest.mark.parametrize("over,needle", [
    ({"schema": "other/1"}, "schema"),
    ({"chart_id": "00000000-0000-0000-0000-000000000000"}, "another chart"),
    ({"generation": "4.1"}, "another chart or generation"),
    ({"manifest": {"status": "published"}}, "not a candidate"),
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
    with pytest.raises(bc.Refused, match=needle):
        bc.check(brief_text(p), chart_id=CHART, generation=GEN, sealing_commit=SHA)        # the digest is recomputed over the altered payload: it is self-consistent


def test_the_workflow_revision_must_be_a_40_hex_sha():
    with pytest.raises(bc.Refused, match="40-hex"):
        bc.check(brief_text(), chart_id=CHART, generation=GEN, sealing_commit="main")


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


# ── the log transport ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_brief_is_extracted_from_exactly_one_log_entry():
    entries = [{"textPayload": "starting"}, {"textPayload": brief_text()}, {"textPayload": "done"}]
    assert json.loads(bx.extract(entries))["sha256"] == bc.digest(payload())
    assert bx.extract([{"jsonPayload": {"message": brief_text()}}])


@pytest.mark.parametrize("entries,needle", [
    ([{"textPayload": "REFUSED: no brief"}], "no log entry carries the brief"),
    ([{"textPayload": brief_text()}, {"textPayload": brief_text(payload(generation="9.9"))}], "more than one distinct brief"),
    ([{"textPayload": brief_text()[:200]}], "not valid JSON"),                                  # split / truncated by the logging system
    ({"not": "an array"}, "not a JSON array"),
])
def test_a_missing_ambiguous_or_truncated_brief_is_refused(entries, needle):
    with pytest.raises(ValueError, match=needle):
        bx.extract(entries)


# ── the chunked log transport (F-R13-2) ───────────────────────────────────────────────────────────────────────────────────────

def _chunks(size=500, text=None):
    text = brief_text() if text is None else text
    return [{"textPayload": line} for line in bx.chunk_brief(text, size)]


def test_a_chunked_brief_reassembles_in_any_arrival_order_and_checks_like_the_single_line_brief():
    text = brief_text()
    ch = _chunks(150)
    assert len(ch) > 3
    for order in (ch, ch[::-1], ch[1::2] + ch[0::2]):
        assert bx.extract([{"textPayload": "starting"}, *order, {"textPayload": "done"}]) == text
    assert bc.check(bx.extract(ch[::-1]), chart_id=CHART, generation=GEN, sealing_commit=SHA) == bc.digest(payload())
    assert bx.extract(ch + [ch[2]]) == text                                              # an identical repeat (at-least-once delivery) is harmless


def _ed(entry, **over):
    c = json.loads(entry["textPayload"])
    c["brief_chunk"].update(over)
    return {"textPayload": json.dumps(c)}


@pytest.mark.parametrize("mut,needle", [
    (lambda ch: ch[:1] + ch[2:], "incomplete"),                                                      # a missing chunk
    (lambda ch: ch[:-1], "incomplete"),                                                              # a truncated tail
    (lambda ch: [_ed(ch[0], data=ch[0] and "x" + json.loads(ch[0]["textPayload"])["brief_chunk"]["data"])] + ch[1:], "sha256 is not the one"),   # altered data
    (lambda ch: ch[:1] + [_ed(ch[1], index=0)] + ch[2:], "two different chunks carry index 0"),       # a duplicate index with other data
    (lambda ch: ch[:1] + [_ed(ch[1], total=99)] + ch[2:], "disagree"),                                # another total
    (lambda ch: ch[:1] + [_ed(ch[1], sha256="0" * 64)] + ch[2:], "disagree"),                         # another whole-brief hash
    (lambda ch: ch[:1] + [_ed(ch[1], index=77)] + ch[2:], "outside"),
    (lambda ch: ch[:1] + [_ed(ch[1], data=5)] + ch[2:], "malformed"),
    (lambda ch: ch + [{"textPayload": brief_text()}], "both a single-line brief and chunks"),
    (lambda ch: [{"textPayload": "{\"brief_chunk\": nope"}] + ch, "not valid JSON"),
])
def test_a_missing_altered_duplicated_or_mixed_chunk_is_refused(mut, needle):
    with pytest.raises(ValueError, match=needle):
        bx.extract(mut(_chunks(150)))


def test_chunks_of_the_real_size_stay_under_the_entry_limit_even_with_json_escaping():
    big = json.dumps({"brief": {"x": ["a" * 40 + '"' * 20] * 6000}, "persisted": {}, "sha256": "0" * 64})
    lines = bx.chunk_brief(big)
    assert len(big) > 256 * 1024 and len(lines) >= 4
    assert max(len(l.encode("utf-8")) for l in lines) < 200 * 1024
    assert bx.extract([{"textPayload": l} for l in lines]) == big


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
    brief = tmp_path / "brief.json"
    brief.write_text(brief_text())
    approvals = tmp_path / "approvals.json"
    approvals.write_text(json.dumps([review()]))
    return {"tmp": tmp_path, "shim": str(shim), "calls": calls, "brief": brief, "approvals": approvals}


def orch(world, **over):
    env = {**os.environ, "BRIEF_FILE": str(world["brief"]), "APPROVALS_FILE": str(world["approvals"]), "CHART_ID": CHART, "GENERATION": GEN,
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
        d = json.loads(world["brief"].read_text()); d["brief"]["result_policy"] = "numeric/1"; world["brief"].write_text(json.dumps(d))
    elif what == "wrong_revision_in_brief":
        world["brief"].write_text(brief_text(payload(code={"sealing_commit": "c" * 40})))
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
