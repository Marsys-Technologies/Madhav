"""J-6l-a61 (W5W6-READINESS brief 01 Part B): `consumer_probe` — the authenticated consumer-path measurement. No network is touched: the script is exercised through an injected
transport and, for `fetch` itself, a double of `http.client.HTTPSConnection`; the executor is the real module on a throwaway KY_ROOT.

One oracle per distinct production claim. Sources: CLAUDE.md §N.7.6 / §N.8 (an unstated field is null; a signal needs a detector that can read false), the http_probe.py /
served_probe.py docstrings (fixed target set, no redirect, typed record), SR-TEARDOWN-AUTHORITY-GATE item 3, platform-mcp/src/server.ts (bearer header; `?api_key=` is the logged
form), platform-mcp/src/tools/kala_views/published_request.ts + registry_alias.ts (the published snapshot shape, the seven views) and
platform/src/lib/retrieval/registry/layers/L3_kala/arrival_state.ts (the arrival vocabulary), RFC 9110 §15.4 (3xx is not followed here).

  B1  the key travels only in the Authorization header, to the table host, and appears in no record, stdout, stderr, receipt or log
  B2  no redirect is followed; no host, path or tool comes from a request argument
  B3  the record is typed and carries no body, no chart id, no name
  B4  a field the response does not state is null, never inferred (generation, manifest_id; image and migration_set are always null)
  B5  admission refuses the kind without the capability and admits it with; no other kind's child receives the key
  B6  `consumer_probe_proof` rejects a record that echoes a credential or states credentials_sent:false (and the other ways a record fails to prove)
  B7  the per-probe `result` enums follow the doctrine of the surfaces they read (published snapshot, arrival vocabulary, Gochara coverage)
  B8  the table binds the kind exactly and the probe ids line up with the pack's declarations and the source's seven views
"""
import ast
import hashlib
import http.client
import io
import json
import re
import subprocess
import sys

import pytest

from test_executor_scheduler_reaper import COMMIT, FLEET, REPO, TABLE, World, load

CP = load(FLEET / "consumer_probe.py", "consumer_probe_under_test")
HP = load(FLEET / "http_probe.py", "http_probe_for_consumer_test")
CHART = CP.CANONICAL_CHART
NAME = "Zz Fixture Person"                                     # a planted name: it must never reach a record, a receipt or a log
KEY = "kyc_FIXTURE-key.0123456789abcdefABCDEF"                  # header-safe by KEY_SHAPE; never a real credential
MID = "0f9a3c1e-5b7d-4e21-9a64-2c8d1b7e4f30"
CAPS = {k: True for k in ("owner", "builder", "gcloud", "pgenv", "none", "consumer_reader")}
RECORD_KEYS = {"schema", "status", "probe", "tool", "http_status", "generation", "manifest_id", "image", "migration_set", "result", "effective_states",
               "body_sha256", "body_bytes", "measured_at", "operation_id", "request_sha256", "credentials_sent", "credential_echoed"}
NOW = lambda: __import__("datetime").datetime(2026, 10, 22, 6, 30, 15, tzinfo=__import__("datetime").timezone.utc)   # noqa: E731
REQ = {"operation_id": "op-consumer-probe-1", "kind": "consumer_probe", "args": {"probe": "gochara_served_head"}, "item_id": "J-6l"}
ENV = {CP.KEY_ENV: KEY, "KY_OPERATION_REQUEST": json.dumps(REQ, sort_keys=True, separators=(",", ":"))}


# ───────────── fixtures: the documented response shapes ─────────────
def obstruction(state, generation="5.0"):
    return {"source_table": "kala_obstruction", "qualification": "published", "data": {"generation": generation, "assertion": {"payload": {"effective_state": state}},
                                                                                     "note": f"about {NAME}"}}


def snapshot(view, rows=None, generation="5.0", manifest_id=MID):
    rows = [] if rows is None else rows
    return {"view": view, "chart_id": CHART, "manifest_id": manifest_id, "generation": generation, "empty_reason": None if rows else "no_matching_rows",
            "manifest": {"manifest_id": manifest_id, "generation": generation}, "rows": rows, "pagination": {"limit": 1, "offset": 0}, "generated_at": "2026-10-22T06:30:00Z"}


def unpublished(view):
    return {"view": view, "chart_id": CHART, "manifest_id": None, "generation": None, "empty_reason": "unpublished", "manifest": None, "rows": []}


def gochara(generation="5.0", windows=None, status=None, reachable=True, with_manifest=True):
    coverage = {"status": "unpublished", "note": "no authority"} if status == "unpublished" else {"event_classes_covered": ["marriage"]}
    if with_manifest and status != "unpublished":
        coverage["coverage_manifest"] = {"source": "kala_gochara_coverage", "generation": generation, "partitions": []}
    return {"windows": windows if windows is not None else [], "coverage": coverage,
            "provenance_envelope": {"source": "gochara_activation_get", "backing_data_reachable": reachable, "window_count": 0, "computed_at": "2026-10-22T06:30:01Z"},
            "chart_id": CHART, "owner": NAME}


def payload_for(probe, **kw):
    reader = CP.PROBES[probe]["reader"]
    if reader == "gochara":
        return gochara(**kw)
    view = CP.PROBES[probe]["tool"][len("kala_"):-len("_get")]
    return snapshot(view, **kw)


def rpc(payload, framing="json", is_error=False, structured=True):
    result = {"content": [{"type": "text", "text": json.dumps(payload)}]}
    if structured:
        result["structuredContent"] = {"type": "object", "object": payload}
    if is_error:
        result["isError"] = True
    message = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result})
    if framing == "sse":
        return CP.Response(200, "text/event-stream", f"event: message\ndata: {message}\n\n".encode())
    return CP.Response(200, "application/json", message.encode())


class Transport:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.requests = response, error, []

    def __call__(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


def measure(probe, response, environ=ENV):
    transport = Transport(response)
    code, record = CP.measure(probe, environ, transport, NOW)
    return code, record, transport


def run_main(argv, response=None, error=None, environ=ENV):
    out, transport = io.StringIO(), Transport(response, error)
    code = CP.main(argv, environ=environ, transport=transport, out=out, clock=NOW)
    return code, out.getvalue(), transport


# ───────────── B1 the key is a header, to the table host, and nowhere else ─────────────
@pytest.mark.parametrize("probe", sorted(CP.PROBES))
def test_b1_the_key_is_sent_only_as_an_authorization_header_to_the_table_host(probe):
    code, record, transport = measure(probe, rpc(payload_for(probe)))
    assert code == 0 and len(transport.requests) == 1
    request = transport.requests[0]
    assert request["headers"]["Authorization"] == "Bearer " + KEY
    assert (request["host"], request["path"]) == (CP.HOST, "/mcp") and "?" not in request["path"]
    assert "api_key" not in json.dumps(request["headers"]).lower() + request["path"] + request["body"].decode().lower()
    assert KEY not in request["path"] and KEY.encode() not in request["body"] and [k for k, v in request["headers"].items() if KEY in v] == ["Authorization"]
    assert KEY not in json.dumps(record)


@pytest.mark.parametrize("response,error", [
    (rpc(gochara()), None), (CP.Response(401, "application/json", b'{"error":"Unauthorized"}'), None), (CP.Response(200, "text/plain", b"not json-rpc"), None),
    (None, CP.Unreachable("ConnectionResetError", True)), (None, RuntimeError(f"boom with {KEY} inside")), (None, OSError(f"{KEY}")),
])
def test_b1_the_key_is_in_no_output_on_any_path_including_errors(response, error, capsys):
    code, stdout, _ = run_main(["--probe", "gochara_served_head"], response, error)
    seen = stdout + capsys.readouterr().out + capsys.readouterr().err
    assert KEY not in seen and CHART not in seen and NAME not in seen
    assert json.loads(stdout.splitlines()[-1])["schema"] == "ky.consumer_probe/1"


class FakeHTTPS:
    """A double of http.client.HTTPSConnection that records every constructor and request call and answers one canned response."""
    log: list = []
    answer = (200, "application/json", b"{}")

    def __init__(self, host, timeout=None, context=None):
        FakeHTTPS.log.append(("connect", host, timeout))

    def request(self, method, path, body=None, headers=None):
        FakeHTTPS.log.append(("request", method, path, dict(headers or {}), body))

    def getresponse(self):
        status, ctype, body = FakeHTTPS.answer
        outer = self

        class R:
            pass
        r = R()
        r.status = status
        r.getheader = lambda name, default=None: ctype if name.lower() == "content-type" else default
        r.read = lambda n=-1: body[:n] if n >= 0 else body
        return r

    def close(self):
        FakeHTTPS.log.append(("close",))


def test_b1_fetch_posts_the_bearer_header_to_the_fixed_host_and_path(monkeypatch):
    FakeHTTPS.log, FakeHTTPS.answer = [], (200, "application/json", b"{}")
    monkeypatch.setattr(http.client, "HTTPSConnection", FakeHTTPS)
    CP.fetch(CP.build_request(CP.PROBES["kala_view_1"], KEY))
    connects = [e for e in FakeHTTPS.log if e[0] == "connect"]
    requests = [e for e in FakeHTTPS.log if e[0] == "request"]
    assert [c[1] for c in connects] == [CP.HOST] and len(requests) == 1
    _, method, path, headers, body = requests[0]
    assert (method, path) == ("POST", "/mcp") and headers["Authorization"] == "Bearer " + KEY and KEY.encode() not in body


def test_b1_the_executor_redacts_the_key_from_a_receipt_even_if_a_child_echoes_it(tmp_path, monkeypatch):
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    world = World(tmp_path, monkeypatch, name="ky_exec_consumer_redact")
    req = world.request("consumer_probe", {"probe": "gochara_served_head"})
    world.mod.receipt(req, "FAILED", "x", 1, f"child said {KEY} and kept going", None, f"stderr said {KEY}")
    stored = json.loads((world.mod.REC / f"{req['operation_id']}.json").read_text())
    texts = [json.dumps(stored), (world.mod.REC / f"{req['operation_id']}.output.txt").read_text(), (world.mod.REC / f"{req['operation_id']}.stderr.txt").read_text()]
    assert all(KEY not in t for t in texts) and "[REDACTED]" in texts[1] and "[REDACTED]" in texts[2]
    world.mod.log(f"a log line with {KEY}")
    assert KEY not in (world.mod.KY_ROOT / "logs" / "executor.log").read_text()


def test_b1_a_response_that_echoes_the_key_is_refused_and_nothing_of_it_is_kept():
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps({"echo": KEY, "owner": NAME})}]}}).encode()
    code, record, _ = measure("gochara_served_head", CP.Response(200, "application/json", body))
    assert code == 1 and record["status"] == "REFUSED" and record["credential_echoed"] is True and "http_status" not in record and "body_sha256" not in record
    assert KEY not in json.dumps(record) and NAME not in json.dumps(record)
    code, record, _ = measure("gochara_served_head", CP.Response(200, "text/plain; x=" + KEY, b"{}"))
    assert record["credential_echoed"] is True and record["status"] == "REFUSED"


def test_b1_without_a_usable_key_nothing_is_sent():
    for key in (None, "", "short", "has space in it 123456", "line\r\nbreak-0123456789", "q" * 600):
        env = {k: v for k, v in ENV.items() if k != CP.KEY_ENV}
        if key is not None:
            env[CP.KEY_ENV] = key
        code, record, transport = measure("gochara_served_head", rpc(gochara()), env)
        assert code == 1 and record["status"] == "REFUSED" and record["credentials_sent"] is False and transport.requests == [], repr(key)


def test_b1_the_key_is_not_accepted_on_the_command_line():
    with pytest.raises(SystemExit) as stop:
        CP.main(["--probe", "gochara_served_head", "--key", KEY], environ=ENV, transport=Transport(rpc(gochara())), out=io.StringIO())
    assert stop.value.code == 2


# ───────────── B2 no redirect; nothing a request carries names a host, path or tool ─────────────
def test_b2_a_redirect_is_not_followed_it_is_a_measured_non_200():
    FakeHTTPS.log, FakeHTTPS.answer = [], (302, "text/html", b"")
    class Redirecting(FakeHTTPS):
        def getresponse(self):
            r = super().getresponse()
            r.getheader = lambda name, default=None: "https://evil.example/mcp" if name.lower() == "location" else ("text/html" if name.lower() == "content-type" else default)
            return r
    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(http.client, "HTTPSConnection", Redirecting)
        code, record = CP.measure("kala_view_1", ENV, CP.fetch, NOW)
    finally:
        mp.undo()
    assert [e[0] for e in FakeHTTPS.log].count("connect") == 1 and [e[0] for e in FakeHTTPS.log].count("request") == 1
    assert all("evil.example" not in str(e) for e in FakeHTTPS.log)
    assert code == 0 and record["status"] == "MEASURED" and record["http_status"] == 302 and record["result"] == "refused" and record["generation"] is None


@pytest.mark.parametrize("probe", ["https://evil.example/mcp", "../x", "gochara_activation_get", "kala_now_get", "", "kala_view_8", "kala_view_0", "GOCHARA_SERVED_HEAD"])
def test_b2_a_probe_id_outside_the_fixed_set_is_refused_before_any_call(probe):
    code, stdout, transport = run_main(["--probe", probe], rpc(gochara()))
    record = json.loads(stdout)
    assert code == 1 and record["status"] == "REFUSED" and record["probe"] is None and transport.requests == []


@pytest.mark.parametrize("extra", [["--url", "https://evil.example/"], ["--host", "evil.example"], ["--tool", "x"], ["--chart_id", "x"], ["--header", "X: y"]])
def test_b2_any_other_argument_exits_2_before_a_call(extra):
    transport = Transport(rpc(gochara()))
    with pytest.raises(SystemExit) as stop:
        CP.main(["--probe", "gochara_served_head", *extra], environ=ENV, transport=transport, out=io.StringIO())
    assert stop.value.code == 2 and transport.requests == []


def test_b2_every_call_is_built_from_the_script_table_alone():
    for probe, spec in CP.PROBES.items():
        request = CP.build_request(spec, KEY)
        body = json.loads(request["body"])
        assert (request["host"], request["path"]) == (CP.HOST, CP.PATH) and body["method"] == "tools/call"
        assert body["params"] == {"name": spec["tool"], "arguments": spec["arguments"]} and spec["arguments"]["chart_id"] == CHART, probe
    assert CP.HOST == "amjis-mcp-qm256lasva-el.a.run.app" and HP.PROBES["mcp_health"].startswith(f"https://{CP.HOST}/")   # the same service http_probe measures


# ───────────── B3 the record is typed and carries no body ─────────────
@pytest.mark.parametrize("probe", sorted(CP.PROBES))
def test_b3_the_record_is_typed_and_carries_no_body_chart_id_or_name(probe):
    planted = [{"source_table": "t", "qualification": "published", "data": {"owner": NAME, "chart": CHART}}]
    code, stdout, _ = run_main(["--probe", probe], rpc(payload_for(probe, **({} if CP.PROBES[probe]["reader"] == "gochara" else {"rows": planted}))))
    record = json.loads(stdout)
    assert code == 0 and set(record) == RECORD_KEYS and record["schema"] == "ky.consumer_probe/1" and record["status"] == "MEASURED"
    assert record["probe"] == probe and record["tool"] == CP.PROBES[probe]["tool"] and record["result"] in CP.RESULTS
    assert type(record["http_status"]) is int and type(record["body_bytes"]) is int and re.fullmatch(r"[0-9a-f]{64}", record["body_sha256"])
    assert record["credentials_sent"] is True and record["credential_echoed"] is False and record["measured_at"] == "2026-10-22T06:30:15Z"
    assert record["operation_id"] == REQ["operation_id"] and record["request_sha256"] == CP.request_digest(REQ)
    assert "body" not in record and not any(isinstance(v, (dict,)) for v in record.values())
    assert CHART not in stdout and NAME not in stdout and "windows" not in stdout and "rows" not in stdout


def test_b3_the_digest_is_over_the_canonical_tool_result_not_the_framing():
    payload = snapshot("now", [obstruction("evaluated_silent")])
    plain = measure("kala_view_1", rpc(payload))[1]
    sse = measure("kala_view_1", rpc(payload, "sse"))[1]
    text_only = measure("kala_view_1", rpc(payload, structured=False))[1]
    assert plain["body_sha256"] == sse["body_sha256"] == text_only["body_sha256"] and plain["body_bytes"] != sse["body_bytes"]
    assert plain["body_sha256"] == hashlib.sha256(json.dumps(CP.canonical(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    moved = dict(payload, generated_at="2030-01-01T00:00:00Z")
    assert measure("kala_view_1", rpc(moved))[1]["body_sha256"] == plain["body_sha256"]                      # a volatile key never moves it
    changed = snapshot("now", [obstruction("evaluated_silent")], generation="5.1")
    assert measure("kala_view_1", rpc(changed))[1]["body_sha256"] != plain["body_sha256"]                    # a real change always does


# ───────────── B4 a field the response does not state is null ─────────────
@pytest.mark.parametrize("probe", sorted(CP.PROBES))
def test_b4_generation_is_what_the_response_states_else_null(probe):
    stated = measure(probe, rpc(payload_for(probe, generation="5.0")))[1]
    other = measure(probe, rpc(payload_for(probe, generation="7.3")))[1]
    assert stated["generation"] == "5.0" and other["generation"] == "7.3"
    if CP.PROBES[probe]["reader"] != "gochara":
        assert stated["manifest_id"] == MID
    # not stated: unpublished snapshot / gochara answer with no generation anywhere
    silent = unpublished("now") if CP.PROBES[probe]["reader"] != "gochara" else gochara(with_manifest=False)
    record = measure(probe, rpc(silent if CP.PROBES[probe]["reader"] != "gochara" else silent))[1]
    assert record["generation"] is None and record["manifest_id"] is None
    # an HTTP error states nothing
    assert measure(probe, CP.Response(503, "text/plain", b"unavailable"))[1]["generation"] is None


def test_b4_image_and_migration_set_are_null_even_if_a_response_claims_them():
    payload = snapshot("now", [obstruction("evaluated_silent")])
    payload.update(image_digest="sha256:" + "a" * 64, migration_set=[{"filename": "1_x.sql", "sha256": "b" * 64}], generation="5.0")
    record = measure("kala_view_1", rpc(payload))[1]
    assert record["image"] is None and record["migration_set"] is None and record["generation"] == "5.0"


def test_b4_a_manifest_id_that_is_not_a_uuid_is_not_recorded():
    record = measure("kala_view_1", rpc(snapshot("now", [obstruction("evaluated_silent")], manifest_id="not-a-uuid")))[1]
    assert record["manifest_id"] is None and record["generation"] == "5.0"


# ───────────── B7 per-probe result enums follow the surfaces' doctrine ─────────────
def result_of(probe, payload):
    return measure(probe, rpc(payload))[1]


@pytest.mark.parametrize("view_n,view", list(enumerate(CP.KALA_VIEWS, start=1)))
def test_b7_the_seven_views_read_the_published_snapshot_states(view_n, view):
    probe = f"kala_view_{view_n}"
    assert CP.PROBES[probe]["tool"] == f"kala_{view}_get"
    assert result_of(probe, snapshot(view, [{"source_table": "t"}]))["result"] == "served"
    assert result_of(probe, snapshot(view, []))["result"] == "no_matching_rows"                       # published_request.ts: rows empty => empty_reason 'no_matching_rows'
    assert result_of(probe, unpublished(view))["result"] == "absent"                                  # unpublished => manifest_id null, empty_reason 'unpublished', generation null
    bad = snapshot(view, [{"x": 1}])
    bad["manifest"]["generation"] = "other"                                                             # manifest and snapshot disagree => not a snapshot
    assert result_of(probe, bad)["result"] == "refused" and result_of(probe, bad)["generation"] is None
    assert result_of(probe, snapshot("ahead" if view != "ahead" else "now", [{"x": 1}]))["result"] == "refused"      # another view's snapshot is not this view's
    other_chart = dict(snapshot(view, [{"x": 1}]), chart_id="00000000-0000-4000-8000-000000000000")
    assert result_of(probe, other_chart)["result"] == "refused"
    assert measure(probe, rpc(snapshot(view, [{"x": 1}]), is_error=True))[1]["result"] == "refused"   # the tool's own unavailable() envelope is an error


def test_b7_the_arrival_line_follows_arrival_state_ts():
    probe = "kala_arrival_line"
    served = result_of(probe, snapshot("now", [obstruction("obstruction_contested"), obstruction("evaluated_silent"), obstruction("evaluated_silent")]))
    assert served["result"] == "served" and served["effective_states"] == ["evaluated_silent", "obstruction_contested"]            # sorted, de-duplicated
    assert result_of(probe, snapshot("now", [{"source_table": "other", "qualification": "published"}]))["result"] == "no_obstruction_state"   # arrivalFromPublishedNow => null
    unqualified = obstruction("evaluated_silent")
    unqualified["qualification"] = "candidate"
    assert result_of(probe, snapshot("now", [unqualified]))["result"] == "no_obstruction_state"
    assert result_of(probe, snapshot("now", [obstruction("not_a_state")]))["result"] == "no_obstruction_state"                       # a state outside the labels voids it
    assert result_of(probe, snapshot("now", [obstruction("evaluated_silent", generation="4.0")]))["result"] == "no_obstruction_state"   # row generation != snapshot generation
    assert result_of(probe, snapshot("now", []))["result"] == "no_matching_rows"
    assert result_of(probe, unpublished("now"))["result"] == "absent" and result_of(probe, unpublished("now"))["effective_states"] is None


def test_b7_the_negative_space_sentinel_is_the_silent_states_only():
    probe = "kala_now_sentinel"
    for states in (["information_unavailable"], ["evaluated_silent"], ["information_unavailable", "evaluated_silent"]):
        record = result_of(probe, snapshot("now", [obstruction(s) for s in states]))
        assert record["result"] == "sentinel_negative_space" and record["effective_states"] == sorted(states)
    mixed = result_of(probe, snapshot("now", [obstruction("evaluated_silent"), obstruction("obstruction_in_force")]))
    assert mixed["result"] == "served" and mixed["effective_states"] == ["evaluated_silent", "obstruction_in_force"]
    assert result_of(probe, snapshot("now", [obstruction("obstruction_in_force")]))["result"] == "served"
    assert result_of(probe, unpublished("now"))["result"] == "absent"
    assert result_of("kala_view_1", snapshot("now", [obstruction("evaluated_silent")]))["effective_states"] is None      # other probes never carry states


def test_b7_the_gochara_served_head_follows_the_coverage_the_tool_states():
    probe = "gochara_served_head"
    assert result_of(probe, gochara("5.0"))["result"] == "served"
    assert result_of(probe, gochara("5.0", windows=[{"generation": "5.0"}, {"generation": "5.0"}]))["generation"] == "5.0"
    only_windows = result_of(probe, gochara(windows=[{"generation": "5.0"}], with_manifest=False))
    assert only_windows["generation"] == "5.0" and only_windows["result"] == "served"
    assert result_of(probe, gochara(status="unpublished"))["result"] == "absent" and result_of(probe, gochara(status="unpublished"))["generation"] is None
    assert result_of(probe, gochara(with_manifest=False))["result"] == "unstated"
    assert result_of(probe, gochara("5.0", windows=[{"generation": "3.0"}]))["result"] == "refused"                # two generations in one answer
    assert result_of(probe, gochara("5.0", reachable=False))["result"] == "refused"
    assert result_of(probe, {"windows": []})["result"] == "refused"


def test_b7_http_and_rpc_failures_are_measured_refusals_not_successes():
    for response in (CP.Response(401, "application/json", b'{"error":"Unauthorized"}'), CP.Response(429, "text/plain", b"slow down"), CP.Response(503, "text/plain", b"x")):
        code, record, _ = measure("kala_view_1", response)
        assert code == 0 and record["status"] == "MEASURED" and record["http_status"] == response.status and record["result"] == "refused" and record["body_sha256"] is None
    error = json.dumps({"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "bad"}}).encode()
    assert measure("kala_view_1", CP.Response(200, "application/json", error))[1]["result"] == "refused"
    assert measure("kala_view_1", CP.Response(200, "application/json", b"not json"))[1]["status"] == "REFUSED"
    wrong_id = json.dumps({"jsonrpc": "2.0", "id": 99, "result": {}}).encode()
    assert measure("kala_view_1", CP.Response(200, "application/json", wrong_id))[1]["status"] == "REFUSED"
    assert measure("kala_view_1", CP.Response(200, "application/json", b"x" * (CP.MAX_BODY + 1)))[1]["status"] == "REFUSED"


def test_b7_an_unreachable_service_is_unreachable_with_the_class_name_only():
    transport = Transport(error=CP.Unreachable("TimeoutError", True))
    code, record = CP.measure("kala_view_1", ENV, transport, NOW)
    assert code == 1 and record["status"] == "UNREACHABLE" and record["reason"] == "TimeoutError" and "http_status" not in record and record["credentials_sent"] is True
    code, record = CP.measure("kala_view_1", ENV, Transport(error=CP.Unreachable("SSLError", False)), NOW)
    assert record["credentials_sent"] is False


# ───────────── B8 the table, the ids and the source's own vocabulary ─────────────
def test_b8_the_kind_is_bound_exactly_read_only_and_needs_its_own_capability():
    entry = TABLE["consumer_probe"]
    assert entry["enabled"] is True and list(entry)[0] == "enabled" and entry["production"] is False and entry["read_only"] is True
    assert entry["needs"] == "consumer_reader" and "also_needs" not in entry and entry["allowed_args"] == ["probe"] and entry["fixed_args"] == []
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/consumer_probe.py" and entry["timeout_s"] <= 300 and entry["enabled_by"] == "J-6l"
    assert set(entry["requesters"]) == {"adhikarin", "v1", "v2"} and "probe_endpoints" not in entry and "lane_dry_run" not in entry


def test_b8_the_probe_ids_line_up_with_the_packs_declarations_and_the_seven_views_of_the_source():
    ids = set(CP.PROBES)
    assert {"gochara_served_head", "kala_now_sentinel", "kala_arrival_line"} <= ids and ids - {"gochara_served_head", "kala_now_sentinel", "kala_arrival_line"} == {f"kala_view_{n}" for n in range(1, 8)}
    assert {"gochara_served_head", "kala_now_sentinel", "kala_arrival_line"} <= set(HP.NOT_MEASURABLE) and "kala_seven_views" in HP.NOT_MEASURABLE   # what http_probe hands over
    source = (REPO / "platform-mcp/src/tools/kala_views/registry_alias.ts").read_text()
    union = re.search(r"export type KalaView = ([^\n]+)", source).group(1)
    assert tuple(re.findall(r"'(\w+)'", union)) == CP.KALA_VIEWS                                          # the seven views, in the source's order


def test_b8_the_arrival_vocabulary_equals_arrival_state_ts():
    source = (REPO / "platform/src/lib/retrieval/registry/layers/L3_kala/arrival_state.ts").read_text()
    labels = re.search(r"const labels = \{(.*?)\} as const", source, re.S).group(1)
    assert tuple(re.findall(r"^\s*(?:\w+: '[^']*',?\s*)", labels, re.M)) and set(re.findall(r"(\w+): '", labels)) == set(CP.EFFECTIVE_STATES)


def test_b8_the_script_is_standard_library_only_so_the_executor_can_copy_the_single_file():
    tree = ast.parse((FLEET / "consumer_probe.py").read_text())
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imported <= set(sys.stdlib_module_names) | {"__future__"}


def test_b8_the_script_runs_as_a_process_and_refuses_without_a_key(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "KY_OPERATION_REQUEST": json.dumps(REQ)}
    done = subprocess.run([sys.executable, str(FLEET / "consumer_probe.py"), "--probe", "kala_view_1"], capture_output=True, text=True, env=env, cwd=tmp_path, timeout=60)
    record = json.loads(done.stdout)
    assert done.returncode == 1 and record["status"] == "REFUSED" and record["credentials_sent"] is False and done.stderr == ""


# ───────────── B5 admission and the child environment ─────────────
@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.delenv(CP.KEY_ENV, raising=False)
    w = World(tmp_path, monkeypatch, name="ky_exec_consumer")
    monkeypatch.setattr(w.mod, "capabilities", lambda _=True: CAPS)
    return w


def test_b5_admission_refuses_the_kind_without_the_capability_and_admits_it_with(world):
    req = world.request("consumer_probe", {"probe": "kala_view_1"})
    assert world.mod.validate(req, TABLE, {**CAPS, "consumer_reader": False}) == "capability_missing: consumer_reader"
    assert world.mod.validate(req, TABLE, {k: v for k, v in CAPS.items() if k != "consumer_reader"}) == "capability_missing: consumer_reader"
    assert world.mod.validate(req, TABLE, CAPS) is None
    assert world.mod.validate(world.request("consumer_probe", {"probe": "kala_view_1", "url": "https://evil.example/"}), TABLE, CAPS) == "disallowed args ['url']"
    # the other capabilities do not stand in for it
    assert world.mod.validate(req, TABLE, {**CAPS, "consumer_reader": False, "builder": True, "owner": True, "gcloud": True}) == "capability_missing: consumer_reader"


def test_b5_the_capability_is_the_executors_possession_of_the_key(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky2"))
    mod2 = load(FLEET / "executor.py", "ky_exec_consumer_caps_real")                                     # the real, unpatched capabilities()
    mod2.OPS.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod2, "main_revision", lambda: None)
    monkeypatch.setattr(mod2, "refresh_state", lambda: "ACTIVE")
    monkeypatch.setattr(mod2.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "", ""))
    monkeypatch.delenv(CP.KEY_ENV, raising=False)
    assert mod2.capabilities(True)["consumer_reader"] is False
    monkeypatch.setenv(CP.KEY_ENV, "")
    assert mod2.capabilities(True)["consumer_reader"] is False
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    caps = mod2.capabilities(True)
    assert caps["consumer_reader"] is True and KEY not in json.dumps(caps) and KEY not in (mod2.OPS / "CAPABILITIES.json").read_text()


@pytest.mark.parametrize("kind,args", [("readback_sql", {"sql_file": "x.sql"}), ("migration_readback", {"migration": "1"}), ("served_probe", {"endpoint": "app_health"}),
                                      ("http_probe", {"probe": "mcp_health"}), ("finalize", {}), ("cloudrun_job_readback", {})])
def test_b5_no_other_kinds_child_receives_the_key(tmp_path, monkeypatch, kind, args):
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    for name in ("KY_BUILDER_DATABASE_URL", "KY_OWNER_DATABASE_URL", "KY_LAYER_VERIFIER_DATABASE_URL"):
        monkeypatch.setenv(name, "postgresql://u:fixture@h/db")
    envs = real_execute_envs(tmp_path, monkeypatch, kind, args)
    assert envs and all(CP.KEY_ENV not in e and KEY not in "".join(map(str, e.values())) for e in envs)


def test_b5_the_consumer_probe_child_alone_receives_the_key_under_one_fixed_name(tmp_path, monkeypatch):
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    for name in ("KY_BUILDER_DATABASE_URL", "KY_OWNER_DATABASE_URL", "KY_LAYER_VERIFIER_DATABASE_URL"):
        monkeypatch.setenv(name, "postgresql://u:fixture@h/db")
    (env,) = real_execute_envs(tmp_path, monkeypatch, "consumer_probe", {"probe": "kala_view_2"})
    assert env[CP.KEY_ENV] == KEY and CP.KEY_ENV == "KY_CONSUMER_PROBE_KEY"
    assert [k for k, v in env.items() if v == KEY] == [CP.KEY_ENV]
    assert not {"DATABASE_URL", "KY_BUILDER_DATABASE_URL", "KY_OWNER_DATABASE_URL", "KY_LAYER_VERIFIER_DATABASE_URL"} & set(env)         # no database credential rides along


def real_execute_envs(tmp_path, monkeypatch, kind, args):
    """Run the REAL `execute` for `kind` with `run_group` and the Git read doubled; return every environment the child was given."""
    monkeypatch.setenv("KY_ROOT", str(tmp_path / f"ky-{kind}"))
    mod = load(FLEET / "executor.py", f"ky_exec_consumer_env_{kind}")
    envs = []
    monkeypatch.setattr(mod, "git", lambda *a, **k: subprocess.CompletedProcess(a, 0, "#!/bin/sh\n", ""))
    monkeypatch.setattr(mod, "run_group", lambda argv, cwd, env, timeout: envs.append(dict(env)) or subprocess.CompletedProcess(argv, 0, "", ""))
    mod.TMP.mkdir(parents=True, exist_ok=True)
    req = {"operation_id": f"op-{kind}", "kind": kind, "args": args, "reviewed_commit": COMMIT}
    mod.execute(req, TABLE[kind])
    return envs


def test_b5_the_child_env_allow_list_does_not_name_the_key():
    mod = load(FLEET / "executor.py", "ky_exec_consumer_allow")
    assert CP.KEY_ENV not in mod.CHILD_ENV_ALLOW and mod.CONSUMER_PROBE_KEY == CP.KEY_ENV


# ───────────── B6 the executor's proof ─────────────
def good_record(**over):
    rec = {"schema": "ky.consumer_probe/1", "status": "MEASURED", "probe": "kala_view_1", "operation_id": "op-1", "http_status": 200, "body_bytes": 123,
           "body_sha256": "a" * 64, "credentials_sent": True, "credential_echoed": False, "result": "served", "generation": "5.0"}
    rec.update(over)
    return rec


@pytest.fixture
def proof(world):
    req = {"operation_id": "op-1", "kind": "consumer_probe", "args": {"probe": "kala_view_1"}, "item_id": "J-6l"}

    def check(record, rc=0, out=None, stderr="", request=req):
        record = dict(record)
        record.setdefault("request_sha256", world.mod.request_digest(request))
        text = json.dumps(record) if out is None else out
        return world.mod.consumer_probe_proof(request, rc, text, stderr)
    check.world = world
    return check


def test_b6_a_good_record_proves(proof):
    rec, problem = proof(good_record())
    assert problem is None and rec["probe"] == "kala_view_1"


@pytest.mark.parametrize("over,needle", [
    ({"credentials_sent": False}, "sent in the header"), ({"credentials_sent": None}, "sent in the header"), ({"credentials_sent": "yes"}, "sent in the header"),
    ({"credential_echoed": True}, "was not echoed"), ({"credential_echoed": None}, "was not echoed"),
    ({"status": "REFUSED"}, "not MEASURED"), ({"status": "UNREACHABLE"}, "not MEASURED"),
    ({"http_status": 401}, "HTTP 401"), ({"http_status": 302}, "HTTP 302"), ({"http_status": None}, "HTTP None"), ({"http_status": True}, "HTTP True"),
    ({"body_sha256": None}, "body length and sha256"), ({"body_sha256": "xyz"}, "body length and sha256"), ({"body_bytes": None}, "body length and sha256"),
    ({"body": "{}"}, "carries a body"),
    ({"probe": "kala_view_2"}, "does not bind"), ({"operation_id": "op-other"}, "does not bind"), ({"request_sha256": "0" * 64}, "does not bind"),
])
def test_b6_a_record_that_does_not_prove_is_rejected(proof, over, needle):
    rec, problem = proof(good_record(**over))
    assert problem and needle in problem, (over, problem)


def test_b6_no_record_two_records_or_a_foreign_schema_prove_nothing(proof):
    assert proof(good_record(), out="not json at all")[1] == "consumer probe record missing or not unique"
    assert proof(good_record(), out=json.dumps(good_record()) + "\n" + json.dumps(good_record()))[1] == "consumer probe record missing or not unique"
    assert proof(good_record(schema="ky.http_probe/1"))[1] == "consumer probe record missing or not unique"


def test_b6_the_credential_in_stdout_or_stderr_is_a_failure_even_with_a_perfect_record(proof, monkeypatch):
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    line = json.dumps(good_record(request_sha256=proof.world.mod.request_digest({"operation_id": "op-1", "kind": "consumer_probe", "args": {"probe": "kala_view_1"}, "item_id": "J-6l"})))
    assert proof(good_record(), out=line)[1] is None
    assert proof(good_record(), out=line + "\n" + KEY)[1] == "the credential appears in the probe's output"
    assert proof(good_record(), out=line, stderr="warn " + KEY)[1] == "the credential appears in the probe's output"


def run_one_with(world, monkeypatch, record_edit=None, out_extra="", rc=0, stderr=""):
    """The real run_one for a consumer_probe whose child output is the REAL script run in-process against a fake transport."""
    req = world.request("consumer_probe", {"probe": "kala_view_1"})
    path = world.mod.INFLIGHT / f"{req['operation_id']}.json"
    path.write_text(json.dumps(req))

    def execute(request, op):
        out = io.StringIO()
        code = CP.main(["--probe", "kala_view_1"], environ={CP.KEY_ENV: KEY, "KY_OPERATION_REQUEST": json.dumps(request, sort_keys=True, separators=(",", ":"))},
                       transport=Transport(rpc(snapshot("now", [obstruction("evaluated_silent")]))), out=out, clock=NOW)
        text = out.getvalue()
        if record_edit:
            rec = json.loads(text)
            record_edit(rec)
            text = json.dumps(rec) + "\n"
        world.mod.child_stderrs()[request["operation_id"]] = stderr
        return (code if rc is None else rc), text + out_extra

    monkeypatch.setattr(world.mod, "execute", execute)
    monkeypatch.setenv(CP.KEY_ENV, KEY)
    world.mod.run_one(path, req, TABLE["consumer_probe"])
    return req, json.loads((world.mod.REC / f"{req['operation_id']}.json").read_text())


def test_b6_end_to_end_a_measured_200_is_completed_and_leaks_nothing(world, monkeypatch):
    req, receipt = run_one_with(world, monkeypatch)
    assert receipt["status"] == "COMPLETED" and receipt["consumer_probe"]["result"] == "served" and receipt["consumer_probe"]["generation"] == "5.0"
    everything = "".join(p.read_text() for p in world.mod.REC.glob("*")) + (world.mod.KY_ROOT / "logs" / "executor.log").read_text()
    assert KEY not in everything and CHART not in everything and NAME not in everything and "ky.consumer_probe/1" in everything
    assert (world.mod.ACC / f"{req['operation_id']}.post.json").exists()                                # a read-only kind is accepted mechanically


def test_b6_end_to_end_a_record_that_stops_proving_is_a_failed_receipt_even_at_exit_zero(world, monkeypatch):
    _, receipt = run_one_with(world, monkeypatch, record_edit=lambda r: r.update(credentials_sent=False))
    assert receipt["exit_code"] == 0 and receipt["status"] == "FAILED" and "sent in the header" in receipt["reason"]
    _, receipt = run_one_with(world, monkeypatch, record_edit=lambda r: r.update(credential_echoed=True))
    assert receipt["status"] == "FAILED" and "was not echoed" in receipt["reason"]
    _, receipt = run_one_with(world, monkeypatch, record_edit=lambda r: r.update(http_status=401))
    assert receipt["status"] == "FAILED" and "HTTP 401" in receipt["reason"]


def test_b6_end_to_end_a_leaked_key_in_output_fails_the_receipt_and_is_redacted(world, monkeypatch):
    req, receipt = run_one_with(world, monkeypatch, out_extra=f"debug {KEY}\n")
    assert receipt["status"] == "FAILED" and receipt["reason"] == "the credential appears in the probe's output"
    stored = json.dumps(receipt) + (world.mod.REC / f"{req['operation_id']}.output.txt").read_text()
    assert KEY not in stored and "[REDACTED]" in stored


def test_b6_the_scripts_request_digest_is_the_executors_byte_for_byte(world):
    req = {"operation_id": "op-9", "kind": "consumer_probe", "args": {"probe": "kala_view_3"}, "item_id": "J-6l", "expires_at": "2026-10-22T07:00:00Z",
           "lease_expires_at": "2026-10-22T08:00:00Z", "acceptance_receipt": "/x/y.json", "reviewed_commit": COMMIT}
    assert CP.request_digest(req) == world.mod.request_digest(req)
    assert CP.request_digest(dict(req, expires_at="2030-01-01T00:00:00Z", acceptance_receipt="/z")) == CP.request_digest(req)        # lawful post-signing changes
    assert CP.request_digest(dict(req, args={"probe": "kala_view_4"})) != CP.request_digest(req)
