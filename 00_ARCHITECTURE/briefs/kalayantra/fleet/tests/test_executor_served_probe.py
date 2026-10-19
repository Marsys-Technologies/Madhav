"""SR-TEARDOWN-AUTHORITY-GATE item 3: the read-only `served_probe` kind — GET one served URL from a fixed allow-list and record what answered.

One doctrine-grounded oracle per distinct production claim; the network is a fake fetcher (no socket is opened), the executor is the real module on a throwaway KY_ROOT.
Sources of the expected values: the ruling SR-TEARDOWN-AUTHORITY-GATE (DECISIONS_SURROGATE.jsonl: "a read-only HTTP/MCP probe kind (production:false, fixed URL set,
one review)") with the task brief ("GETs one URL from a FIXED allow-list declared in the ops table ... records status, content-type, byte length, sha256 of the body and
the body itself only if it carries no personal data (the response of a chart-scoped endpoint for the native: store digest + length only) ... never a token in a receipt ...
off-list URL refused; digest recorded; non-2xx is a FAILED receipt"), FIPS 180-4 sha256 (hashlib, computed in the test from the bytes the fake serves), RFC 9110 §15.2-15.5
(2xx is success; 3xx/4xx/5xx are not) and CLAUDE.md §N.8 (a signal needs a detector that can read false). Distinct claims:
P1 a name not on the allow-list is refused at admission and by the script, before any fetch · P2 the URL fetched is exactly the declared one (no argument carries a URL)
· P3 status, content-type, byte length and sha256 of the body are recorded · P4 a non-2xx answer (incl. a redirect, never followed) is a FAILED receipt carrying the
observed status · P5 the body is stored only for an endpoint declared store_body, and a chart-scoped endpoint stores digest + length only · P6 a body with a
personal-data marker is withheld even from a store_body endpoint · P7 no credential is sent or recorded · P8 the executor re-checks the record: one that does not bind
this operation/endpoint/URL, or whose stored body disagrees with its digest, is a FAILED receipt even at exit 0 · P9 a 2xx probe is accepted mechanically like readback_sql
· P10 the script's allow-list equals the table's.
"""
import hashlib
import io
import json
import urllib.error

import pytest

from test_executor_scheduler_reaper import ALL_CAPS, COMMIT, FLEET, TABLE, World, load, utc_now

probe = load(FLEET / "served_probe.py", "served_probe_under_test")
URL = "https://madhav.marsys.in/api/health"
OK_BODY = b'{"status":"ok"}'
TOKEN = "ya29.FIXTURE-TOKEN-THAT-MUST-NEVER-BE-PRINTED-0123456789"


class Fetcher:
    """A fake `fetch(url)`: records every URL it is asked for and answers (status, content-type, body, truncated)."""

    def __init__(self, status=200, content_type="application/json", body=OK_BODY, truncated=False, error=None):
        self.answer, self.error, self.urls = (status, content_type, body, truncated), error, []

    def __call__(self, url, *rest, **kw):
        self.urls.append(url)
        assert not rest and not kw, "the script passes the URL and nothing else (no header, no credential)"
        if self.error: raise self.error
        return self.answer


class ProbeWorld(World):
    def __init__(self, tmp_path, monkeypatch, fetcher=None, table=None):
        super().__init__(tmp_path, monkeypatch, name="ky_exec_probe")
        self.fetcher = fetcher or Fetcher()
        self.table = table or TABLE
        monkeypatch.setattr(self.mod, "load_table", lambda: self.table)

    def execute(self, req, op):
        args = list(op.get("fixed_args", []))                                                # what the real execute() builds
        for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
        out = io.StringIO()
        rc = probe.main(args, environ={"KY_OPERATION_REQUEST": json.dumps(req, sort_keys=True, separators=(",", ":"))}, fetch=self.fetcher, out=out)
        return rc, out.getvalue()

    def probe_request(self, endpoint="app_health", **kw):
        return self.request("served_probe", {"endpoint": endpoint}, **kw)

    def validate(self, req):
        return self.mod.validate(req, self.table, ALL_CAPS)

    def run(self, req):
        path = self.mod.INFLIGHT / f"{req['operation_id']}.json"
        path.write_text(json.dumps(req))
        self.mod.run_one(path, req, self.table[req["kind"]])
        return json.loads((self.mod.REC / f"{req['operation_id']}.json").read_text())


def table_with(endpoints):
    table = json.loads(json.dumps(TABLE))
    table["served_probe"]["probe_endpoints"] = endpoints
    return table


@pytest.fixture
def world(tmp_path, monkeypatch):
    return ProbeWorld(tmp_path, monkeypatch)


# P1
def test_p1_a_name_off_the_list_is_refused_at_admission_and_nothing_is_fetched(world):
    for name in ("not_listed", "https://evil.example/x", "../api/health", ""):
        assert world.validate(world.probe_request(name)) in (
            "endpoint is not on the served-probe allow-list in the operation table", "an argument value has unsafe characters"), name
    assert world.validate(world.request("served_probe", {})) == "endpoint is not on the served-probe allow-list in the operation table"
    assert world.validate(world.request("served_probe", {"endpoint": "app_health", "url": "https://evil.example/"})) == "disallowed args ['url']"
    assert world.validate(world.probe_request("app_health")) is None
    receipt = world.run(world.probe_request("not_listed"))
    assert receipt["status"] == "REFUSED" and world.fetcher.urls == []


def test_p1_the_script_itself_refuses_a_name_off_its_list_before_any_fetch():
    fetch = Fetcher()
    rc, record = probe.run("not_listed", {}, fetch)
    assert rc == 1 and record["status"] == "REFUSED" and record["endpoint"] is None and record["http_status"] is None and fetch.urls == []


# P2
def test_p2_exactly_the_declared_url_is_fetched_and_a_declared_url_off_the_fixed_host_is_refused():
    fetch = Fetcher()
    rc, record = probe.run("app_health", {}, fetch)
    assert rc == 0 and fetch.urls == [URL] and record["url"] == URL and record["method"] == "GET"
    for bad in ("http://madhav.marsys.in/api/health", "https://evil.example/api/health", "https://madhav.marsys.in@evil.example/x", "https://user:pw@madhav.marsys.in/x"):
        fetch = Fetcher()
        rc, record = probe.run("e", {}, fetch, endpoints={"e": {"url": bad, "store_body": True}})
        assert rc == 1 and record["status"] == "REFUSED" and fetch.urls == [], bad


# P3
def test_p3_status_content_type_length_and_sha256_of_the_body_are_recorded(world):
    body = b'{"status":"ok","image":"abc"}'
    world.fetcher = Fetcher(200, "application/json; charset=utf-8", body)
    receipt = world.run(world.probe_request())
    rec = receipt["probe"]
    assert receipt["status"] == "COMPLETED" and receipt["exit_code"] == 0
    assert (rec["http_status"], rec["content_type"], rec["body_bytes"]) == (200, "application/json; charset=utf-8", len(body))
    assert rec["body_sha256"] == hashlib.sha256(body).hexdigest() and rec["body"] == body.decode() and rec["status"] == "OK"


# P4
@pytest.mark.parametrize("status", [301, 302, 401, 403, 404, 500, 503])
def test_p4_a_non_2xx_answer_is_a_failed_receipt_with_the_observed_status(world, status):
    world.fetcher = Fetcher(status, "text/html", b"<html>nope</html>")
    receipt = world.run(world.probe_request())
    assert receipt["status"] == "FAILED" and receipt["reason"] == f"the served response is HTTP {status}, not 2xx"
    assert receipt["probe"]["http_status"] == status and receipt["probe"]["body_sha256"] == hashlib.sha256(b"<html>nope</html>").hexdigest()


@pytest.mark.parametrize("status,ok", [(200, True), (204, True), (299, True), (199, False), (300, False), (404, False), (500, False)])
def test_p4_the_script_exits_zero_only_for_a_2xx_answer(status, ok):
    rc, record = probe.run("app_health", {}, Fetcher(status, "text/plain", b"x"))
    assert (rc == 0, record["status"] == "OK") == (ok, ok) and record["http_status"] == status


def test_p4_the_executor_fails_a_record_of_a_non_2xx_answer_even_when_the_script_exited_zero(world, monkeypatch):
    receipt = _run_with_record(world, monkeypatch, lambda r: r.update(http_status=503, status="OK"))
    assert receipt["exit_code"] == 0 and receipt["status"] == "FAILED" and receipt["reason"] == "the served response is HTTP 503, not 2xx"


def test_p4_a_transport_error_is_a_failed_receipt_with_null_facts(world):
    world.fetcher = Fetcher(error=TimeoutError("timed out talking to 203.0.113.9"))
    receipt = world.run(world.probe_request())
    rec = receipt["probe"]
    assert receipt["status"] == "FAILED" and rec["http_status"] is None and rec["body_sha256"] is None and rec["body_bytes"] is None
    assert "203.0.113.9" not in json.dumps(receipt) and rec["reason"] == "the request failed: TimeoutError"


def test_p4_the_default_fetcher_never_follows_a_redirect():
    handler = probe._NoRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/") is None


def test_p4_an_oversize_body_has_no_digest_rather_than_the_digest_of_a_prefix():
    rc, record = probe.run("app_health", {}, Fetcher(200, "application/json", b"x" * 10, truncated=True))
    assert rc == 1 and record["status"] == "FAILED" and record["body_sha256"] is None and record["body_bytes"] is None and record["body_withheld"] == "body_too_large_to_digest"


# P5
def test_p5_a_digest_only_endpoint_stores_no_body_but_records_digest_and_length(tmp_path, monkeypatch):
    chart_scoped = {"chart_view": {"url": URL, "store_body": False}}
    world = ProbeWorld(tmp_path, monkeypatch, Fetcher(200, "application/json", b'{"planets":[1,2,3]}'), table_with(chart_scoped))
    monkeypatch.setattr(probe, "ENDPOINTS", chart_scoped)
    receipt = world.run(world.probe_request("chart_view"))
    rec = receipt["probe"]
    assert receipt["status"] == "COMPLETED" and rec["body"] is None and rec["body_withheld"] == "endpoint_declared_digest_only"
    assert rec["body_bytes"] == 19 and rec["body_sha256"] == hashlib.sha256(b'{"planets":[1,2,3]}').hexdigest()
    assert "planets" not in json.dumps(receipt) and "planets" not in (world.mod.REC / f"{rec['operation_id']}.output.txt").read_text()


def test_p5_the_executor_fails_a_record_that_stored_a_body_for_a_digest_only_endpoint(tmp_path, monkeypatch):
    chart_scoped = {"app_health": {"url": URL, "store_body": False}}                 # the table says digest-only; the (reviewed) script's own list says it may store
    world = ProbeWorld(tmp_path, monkeypatch, table=table_with(chart_scoped))
    receipt = world.run(world.probe_request())
    assert receipt["status"] == "FAILED" and receipt["reason"] == "a body was stored for an endpoint declared digest-only"


# P6
@pytest.mark.parametrize("marker", ["482012f1-710e-4a25-994a-93821f5871aa", "Abhisek", "MOHANTY", "1984-02-05", "Bhubaneswar"])
def test_p6_a_body_with_a_personal_data_marker_is_withheld_even_from_a_store_body_endpoint(world, marker):
    body = json.dumps({"status": "ok", "note": f"x {marker} y"}).encode()
    world.fetcher = Fetcher(200, "application/json", body)
    receipt = world.run(world.probe_request())
    rec = receipt["probe"]
    assert receipt["status"] == "COMPLETED" and rec["body"] is None and rec["body_withheld"] == "personal_data_marker"
    assert rec["body_sha256"] == hashlib.sha256(body).hexdigest() and rec["body_bytes"] == len(body)
    assert marker.lower() not in json.dumps(receipt).lower() and marker.lower() not in (world.mod.REC / f"{rec['operation_id']}.output.txt").read_text().lower()


# P7
def test_p7_no_credential_is_sent_or_recorded(world, monkeypatch):
    monkeypatch.setenv("KY_BUILDER_DATABASE_URL", "postgresql://u:" + TOKEN + "@h/db")
    monkeypatch.setenv("MCP_INTERNAL_TOKEN", TOKEN)
    world.fetcher = Fetcher(200, "application/json", OK_BODY)                       # Fetcher.__call__ asserts the script passes the URL and nothing else
    receipt = world.run(world.probe_request())
    assert receipt["probe"]["credentials_sent"] is False and receipt["status"] == "COMPLETED"
    assert TOKEN not in json.dumps(receipt) and TOKEN not in (world.mod.REC / f"{receipt['operation_id']}.output.txt").read_text()


def test_p7_the_default_fetcher_builds_one_get_with_no_credential_header(monkeypatch):
    seen = []

    class Response:
        status, headers = 200, {"Content-Type": "application/json"}
        def read(self, n): return OK_BODY
        def __enter__(self): return self
        def __exit__(self, *a): return False

    class Opener:
        def open(self, request, timeout=None):
            seen.append(request)
            return Response()

    monkeypatch.setenv("MCP_INTERNAL_TOKEN", TOKEN)
    monkeypatch.setattr(probe.urllib.request, "build_opener", lambda *handlers: Opener())
    assert probe.default_fetch(URL) == (200, "application/json", OK_BODY, False)
    assert len(seen) == 1 and seen[0].get_method() == "GET" and seen[0].full_url == URL and seen[0].data is None
    assert {k.lower() for k in seen[0].headers} <= {"accept", "user-agent"} and TOKEN not in json.dumps(dict(seen[0].headers))


def test_p7_the_executor_fails_a_record_that_does_not_say_no_credential_was_sent(world, monkeypatch):
    original = probe.run

    def lying_run(*a, **kw):
        rc, record = original(*a, **kw)
        record["credentials_sent"] = True
        return rc, record
    monkeypatch.setattr(probe, "run", lying_run)
    receipt = world.run(world.probe_request())
    assert receipt["status"] == "FAILED" and receipt["reason"] == "probe record does not state that no credential was sent"


# P8
def _run_with_record(world, monkeypatch, edit):
    original = probe.run

    def edited(*a, **kw):
        rc, record = original(*a, **kw)
        edit(record)
        return rc, record
    monkeypatch.setattr(probe, "run", edited)
    return world.run(world.probe_request())


@pytest.mark.parametrize("field,value", [("operation_id", "someone-else"), ("request_sha256", "0" * 64), ("endpoint", "other"), ("url", "https://madhav.marsys.in/api/other")])
def test_p8_a_record_that_does_not_bind_this_operation_endpoint_and_url_fails_even_at_exit_zero(world, monkeypatch, field, value):
    receipt = _run_with_record(world, monkeypatch, lambda r: r.__setitem__(field, value))
    assert receipt["exit_code"] == 0 and receipt["status"] == "FAILED"
    assert receipt["reason"] == "probe record does not bind this operation, request and declared endpoint"


def test_p8_a_stored_body_that_disagrees_with_its_digest_fails(world, monkeypatch):
    receipt = _run_with_record(world, monkeypatch, lambda r: r.__setitem__("body", '{"status":"tampered"}'))
    assert receipt["exit_code"] == 0 and receipt["status"] == "FAILED" and receipt["reason"] == "the stored body does not match its recorded length and sha256"


def test_p8_an_exit_zero_with_no_record_is_failed(world, monkeypatch):
    monkeypatch.setattr(world.mod, "execute", lambda req, op: (0, "ok\n"))
    receipt = world.run(world.probe_request())
    assert receipt["status"] == "FAILED" and receipt["reason"] == "probe record missing or not unique"


# P9
def test_p9_a_2xx_probe_is_accepted_mechanically_and_a_failed_one_is_not(tmp_path, monkeypatch):
    world = ProbeWorld(tmp_path, monkeypatch)
    for status, accepted in ((200, True), (503, False)):
        world.fetcher = Fetcher(status, "application/json", OK_BODY)
        req = world.probe_request(oid=f"op-probe-{status}")
        receipt = world.run(req)
        post = world.mod.ACC / f"{req['operation_id']}.post.json"
        assert post.exists() is accepted, (status, receipt["status"])
        if accepted:
            document = json.loads(post.read_text())
            assert document["by"] == "executor-mechanical" and document["checks"]["kind_read_only_per_table"] is True


def test_p9_the_kind_is_read_only_and_unfenced_in_the_table():
    entry = TABLE["served_probe"]
    assert entry["read_only"] is True and entry["production"] is False and entry["needs"] == "none" and "remote_async" not in entry
    assert entry["allowed_args"] == ["endpoint"] and entry["enabled_by"] == "J-6l"


# P10
def test_p10_the_scripts_allow_list_equals_the_tables_and_the_whole_script_is_standard_library():
    assert probe.ENDPOINTS == TABLE["served_probe"]["probe_endpoints"]
    assert all(v["url"].startswith(f"https://{probe.HOST}/") for v in probe.ENDPOINTS.values())
    imports = {l.split()[1].split(".")[0] for l in (FLEET / "served_probe.py").read_text().splitlines() if l.startswith(("import ", "from "))}
    assert imports <= {"__future__", "argparse", "datetime", "hashlib", "json", "os", "re", "sys", "urllib"}


def test_p10_the_scripts_request_digest_is_the_executors(world):
    req = world.probe_request()
    assert probe.request_digest(req) == world.mod.request_digest(req)
