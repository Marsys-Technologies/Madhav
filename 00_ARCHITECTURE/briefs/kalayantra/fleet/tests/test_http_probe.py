"""SR-PREBUILD-ALL / SR-TEARDOWN-AUTHORITY-GATE item 3: `http_probe` — a read-only, credential-free measurement of ONE fixed URL, printing the
`ky.http_probe/1` record the W5/W6 union pack's live gate reads (PACK EXPECTED_TABLE.json `http_probe.record`; gates.live: `schema`, `status ==
MEASURED`, `http_status == 200`, `generation`, `image`, `migration_set`, and `body_sha256` equal before and after a rollback — J-6r "served response
byte-identical to before the flip").

One oracle per distinct production claim. No network is touched: `fetch` is exercised against a double of `http.client.HTTPSConnection`, every other
test injects the transport.

  P1  the URL set is fixed: https, a bare host and path (no query, fragment or credential), and the only request argument is a probe id
  P2  a probe id outside the set, and the four probes that need a credential, are REFUSED with no request made
  P3  the record carries the pack's fields; MEASURED carries http_status, and a non-200 status is a measurement, not a failure
  P4  body_sha256 is over the canonical body: volatile keys never move it, a real change always does, and a non-object body hashes as raw bytes
  P5  generation / image / migration_set / revision / deployed_sha are what the response states in the exact shape, else null — never inferred
  P6  an unreachable URL is UNREACHABLE (no http_status), an unreadable or oversize response is REFUSED; neither is MEASURED
  P7  the request is one unauthenticated GET: no redirect followed, no credential header, no environment read for one
  P8  the table binds the kind exactly, DISABLED, and the real `validate` refuses a disabled kind, any other argument and another lane
  P9  end to end through the CLI: one JSON line, exit 0 / 1, and an extra argument exits 2 before any request
"""
import copy
import hashlib
import http.client
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "http_probe.py"

spec = importlib.util.spec_from_file_location("http_probe_under_test", SCRIPT)
HP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HP)

NOW = lambda: __import__("datetime").datetime(2026, 10, 20, 9, 30, 15, tzinfo=__import__("datetime").timezone.utc)   # noqa: E731
HEALTH = {"status": "ok", "service": "marsys-mcp", "version": "1.0.0", "deployed_sha": "0123456789abcdef0123456789abcdef01234567",
          "revision": "amjis-mcp-00042-abc", "tools": 88}
PACK_KEYS = {"schema", "status", "probe", "http_status", "generation", "image", "migration_set", "body_sha256", "measured_at"}


class Transport:
    def __init__(self, status=200, body=None):
        self.status, self.body, self.urls = status, json.dumps(HEALTH).encode() if body is None else body, []

    def __call__(self, url):
        self.urls.append(url)
        return self.status, self.body


def measure(transport=None, probe="mcp_health"):
    transport = transport or Transport()
    return HP.measure(probe, transport, NOW), transport


# ───────────── P1 the fixed URL set ─────────────

def test_p1_every_probe_url_is_a_credential_free_https_host_and_path():
    assert HP.PROBES, "no probe is defined"
    for probe, url in HP.PROBES.items():
        parts = urlsplit(url)
        assert parts.scheme == "https" and parts.hostname and parts.path.startswith("/"), probe
        assert not (parts.username or parts.password or parts.query or parts.fragment or parts.port), probe


def test_p1_the_mcp_health_probe_is_the_route_the_server_and_the_deploy_smoke_use():
    # platform-mcp/src/server.ts `app.get('/health')`; .github/workflows/deploy.yml reads "$SMOKE_MCP_URL/health"
    assert urlsplit(HP.PROBES["mcp_health"]).path == "/health"
    assert "app.get('/health'" in (REPO / "platform-mcp/src/server.ts").read_text()
    assert '"$SMOKE_MCP_URL/health"' in (REPO / ".github/workflows/deploy.yml").read_text()
    default_target = (REPO / "platform/scripts/audit/doctrine_harness/run.ts").read_text()
    assert f"'{HP.PROBES['mcp_health'].rsplit('/health', 1)[0]}/mcp'" in default_target      # the same service host the repository's audit scripts target


# ───────────── P2 refused probes make no request ─────────────

@pytest.mark.parametrize("probe", ["", "mcp_health ", "MCP_HEALTH", "https://evil.example/health", "../health", "mcp_health,mcp_health", "nope"])
def test_p2_a_probe_id_outside_the_fixed_set_is_refused_without_a_request(probe):
    transport = Transport()
    with pytest.raises(HP.Refused, match="not in the fixed set"):
        HP.measure(probe, transport, NOW)
    assert transport.urls == []


@pytest.mark.parametrize("probe", ["gochara_served_head", "kala_now_sentinel", "kala_seven_views", "kala_arrival_line"])
def test_p2_the_probes_that_need_a_credential_say_so_and_make_no_request(probe):
    transport = Transport()
    with pytest.raises(HP.Refused, match="not measurable without a credential"):
        HP.measure(probe, transport, NOW)
    assert transport.urls == [] and probe not in HP.PROBES        # a URL registered for them would measure a login page, not the surface


# ───────────── P3 the record ─────────────

def test_p3_the_record_carries_the_pack_fields_and_one_request_goes_to_the_fixed_url():
    record, transport = measure()
    assert PACK_KEYS <= set(record) and record["schema"] == "ky.http_probe/1" and record["status"] == "MEASURED"
    assert (record["probe"], record["http_status"], record["measured_at"]) == ("mcp_health", 200, "2026-10-20T09:30:15Z")
    assert transport.urls == [HP.PROBES["mcp_health"]] and record["url"] == HP.PROBES["mcp_health"]


@pytest.mark.parametrize("status", [301, 404, 503])
def test_p3_a_non_200_response_is_a_measurement_and_says_its_status(status):
    record, _ = measure(Transport(status=status))
    assert record["status"] == "MEASURED" and record["http_status"] == status        # gates.live reads http_ok False from it, not NULL


@pytest.mark.parametrize("status", [None, True, "200", 99, 600])
def test_p3_a_response_without_a_real_http_status_is_refused(status):
    with pytest.raises(HP.Refused, match="no HTTP status"):
        HP.measure("mcp_health", Transport(status=status), NOW)


# ───────────── P4 the canonical body hash ─────────────

def sha(doc):
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_p4_volatile_keys_never_move_the_hash_and_key_order_never_does_either():
    a = measure(Transport(body=json.dumps({"b": 1, "a": 2, "observed_at": "t1", "timestamp": 5, "time": "x", "uptime_s": 9}).encode()))[0]
    b = measure(Transport(body=json.dumps({"a": 2, "observed_at": "t2", "b": 1, "timestamp": 6, "time": "y", "uptime_s": 10}).encode()))[0]
    assert a["body_sha256"] == b["body_sha256"] == sha({"a": 2, "b": 1}) and a["body_format"] == "json"


def test_p4_a_change_in_a_stable_field_always_moves_the_hash():
    # J-6r: "served response byte-identical to before the flip" — a real difference (here the served generation) must read different
    a = measure(Transport(body=json.dumps({"generation": "4.2", "observed_at": "t"}).encode()))[0]
    b = measure(Transport(body=json.dumps({"generation": "5.0", "observed_at": "t"}).encode()))[0]
    assert a["body_sha256"] != b["body_sha256"]
    nested = measure(Transport(body=json.dumps({"x": {"y": 1, "seen_at": "t"}}).encode()))[0]
    assert nested["body_sha256"] == sha({"x": {"y": 1}})                             # volatile keys are dropped at every depth


@pytest.mark.parametrize("body", [b"<html>login</html>", b"[1,2]", b'"text"', b""])
def test_p4_a_body_that_is_not_a_json_object_hashes_as_its_raw_bytes(body):
    record, _ = measure(Transport(body=body))
    assert record["body_sha256"] == hashlib.sha256(body).hexdigest() and record["body_format"] == "raw" and record["body_bytes"] == len(body)


# ───────────── P5 only what the response states ─────────────

def test_p5_a_health_response_states_a_revision_and_a_commit_but_no_generation_image_or_migrations():
    record, _ = measure()
    assert (record["generation"], record["image"], record["migration_set"]) == (None, None, None)       # null, not inferred from the URL or the clock
    assert record["revision"] == HEALTH["revision"] and record["deployed_sha"] == HEALTH["deployed_sha"]


def test_p5_a_response_that_states_them_in_the_exact_shape_is_read_through():
    migrations = [{"filename": "1379_gochara_sealed_authority.sql", "sha256": "a" * 64}, {"filename": "1380_x.sql", "sha256": "b" * 64}]
    body = {"generation": "5.0", "image_digest": "sha256:" + "c" * 64, "migration_set": migrations}
    record, _ = measure(Transport(body=json.dumps(body).encode()))
    assert (record["generation"], record["image"], record["migration_set"]) == ("5.0", "sha256:" + "c" * 64, migrations)


@pytest.mark.parametrize("body", [
    {"generation": 5.0, "image_digest": "latest", "migration_set": "1379_x.sql", "deployed_sha": "short", "revision": 7},
    {"generation": "", "image_digest": "sha256:" + "C" * 64, "migration_set": [], "deployed_sha": "G" * 40},
    {"migration_set": [{"filename": "1379_x.sql"}]},
    {"migration_set": [{"filename": "x.sql", "sha256": "a" * 64}]},
    {"migration_set": [{"filename": "1379_x.sql", "sha256": "a" * 64, "extra": 1}]},
    {"migration_set": [{"filename": "1379_x.sql", "sha256": "a" * 64}, "1380"]},
])
def test_p5_a_malformed_statement_reads_null_and_is_never_repaired(body):
    record, _ = measure(Transport(body=json.dumps(body).encode()))
    assert (record["generation"], record["image"], record["migration_set"], record["deployed_sha"], record["revision"]) == (None,) * 5


# ───────────── P6 unreachable and unreadable ─────────────

def test_p6_a_failed_connection_is_unreachable_and_carries_no_http_status(capsys):
    def down(url):
        raise HP.Unreachable("TimeoutError")
    assert HP.cli(["--probe", "mcp_health"], down) == 1
    record = json.loads(capsys.readouterr().out)
    assert record["status"] == "UNREACHABLE" and record["reason"] == "TimeoutError" and "http_status" not in record and "body_sha256" not in record


def test_p6_an_oversize_or_non_bytes_body_is_refused_not_measured():
    for body in (b"x" * (HP.MAX_BODY + 1), "text", bytearray(b"x")):
        with pytest.raises(HP.Refused, match="size limit"):
            HP.measure("mcp_health", Transport(body=body), NOW)


# ───────────── P7 the request itself ─────────────

class FakeConn:
    last = None

    def __init__(self, host, timeout=None, context=None):
        FakeConn.last = self
        self.host, self.timeout, self.calls, self.closed = host, timeout, [], False

    def request(self, method, path, headers=None, **rest):
        self.calls.append((method, path, dict(headers or {}), rest))

    def getresponse(self):
        outer = self
        class Response:
            status = 302
            def read(self, n=-1):
                outer.read_limit = n
                return b"moved"
        return Response()

    def close(self):
        self.closed = True


def test_p7_fetch_makes_one_unauthenticated_get_follows_no_redirect_and_cuts_the_body(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_SECRET")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("KY_BUILDER_DATABASE_URL", "postgres://secret")
    monkeypatch.setattr(HP.http.client, "HTTPSConnection", FakeConn)
    status, body = HP.fetch(HP.PROBES["mcp_health"])
    conn = FakeConn.last
    assert (status, body) == (302, b"moved")                                        # a redirect is read as a status; nothing follows it
    assert conn.host == urlsplit(HP.PROBES["mcp_health"]).netloc and len(conn.calls) == 1 and conn.closed
    method, path, headers, rest = conn.calls[0]
    assert (method, path, rest) == ("GET", "/health", {})
    assert {k.lower() for k in headers} == {"accept", "user-agent"}                 # no Authorization, Cookie or token header, ever
    assert "SECRET" not in json.dumps(headers) and conn.read_limit == HP.MAX_BODY + 1


def test_p7_a_transport_error_becomes_unreachable_with_only_the_failure_class(monkeypatch):
    class Boom(FakeConn):
        def request(self, *a, **k):
            raise ConnectionRefusedError("host 10.0.0.1 token ghp_LEAK")
    monkeypatch.setattr(HP.http.client, "HTTPSConnection", Boom)
    with pytest.raises(HP.Unreachable) as caught:
        HP.fetch(HP.PROBES["mcp_health"])
    assert str(caught.value) == "ConnectionRefusedError" and "LEAK" not in str(caught.value) and Boom.last.closed
    monkeypatch.setattr(HP.http.client, "HTTPSConnection", type("Bad", (FakeConn,), {"request": lambda *a, **k: (_ for _ in ()).throw(http.client.BadStatusLine("x"))}))
    with pytest.raises(HP.Unreachable, match="BadStatusLine"):
        HP.fetch(HP.PROBES["mcp_health"])


# ───────────── P8 the table binding, through the real validate ─────────────

def _executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec_ = importlib.util.spec_from_file_location(f"ky_exec_hp_{abs(hash(str(tmp_path)))}", FLEET / "executor.py")
    module = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(module)
    return module


def _req(**over):
    req = {"operation_id": "op-hp", "kind": "http_probe", "item_id": "J-6l", "idempotency_key": "key-hp", "requested_by": "adhikarin", "kyd": "kyd-1",
           "args": {"probe": "mcp_health"}}
    req.update(over)
    return req


def test_p8_table_entry_is_exact_shipped_disabled_and_the_real_validate_holds(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    entry = table["http_probe"]
    assert list(entry)[0] == "enabled" and entry["enabled"] is False                  # shipped disabled: the owner's flip enables it
    assert (entry["production"], entry["read_only"], entry["needs"], entry["fixed_args"], entry["allowed_args"]) == (False, True, "none", [], ["probe"])
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/http_probe.py" and (REPO / entry["script"]).is_file()
    assert entry["requesters"] == ["adhikarin", "v1", "v2"] and "also_needs" not in entry and entry["enabled_by"] == "J-6l"
    ex = _executor(tmp_path, monkeypatch)
    caps = {"none": True}
    assert "is not enabled" in ex.validate(_req(), table, caps)                         # disabled: refused today
    live = copy.deepcopy(table)
    live["http_probe"]["enabled"] = True
    assert ex.validate(_req(), live, caps) is None
    assert "disallowed args" in ex.validate(_req(args={"probe": "mcp_health", "url": "https://evil.example/"}), live, caps)
    assert "disallowed args" in ex.validate(_req(args={"url": "https://evil.example/"}), live, caps)
    assert "may not request" in ex.validate(_req(requested_by="sutradhara"), live, caps)
    assert "unsafe characters" in ex.validate(_req(args={"probe": "a b"}), live, caps)


# ───────────── P9 end to end through the CLI ─────────────

def test_p9_cli_prints_one_line_and_exits_0_for_a_measurement(capsys):
    assert HP.cli(["--probe", "mcp_health"], Transport()) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    line = next(l for l in lines if l.startswith("{") and "ky.http_probe/1" in l)         # evidence.record_in_output: the one JSON line carrying `schema`
    assert json.loads(line)["status"] == "MEASURED"


def test_p9_cli_refusals_exit_1_with_no_http_status_and_no_request(capsys):
    transport = Transport()
    for probe in ("kala_now_sentinel", "unknown"):
        assert HP.cli(["--probe", probe], transport) == 1
        record = json.loads(capsys.readouterr().out)
        assert record["status"] == "REFUSED" and "http_status" not in record and record["probe"] == probe
    assert transport.urls == []


def test_p9_the_script_itself_refuses_without_network_and_an_extra_argument_exits_2(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run([sys.executable, "-I", str(SCRIPT), "--probe", "gochara_served_head"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert done.returncode == 1 and json.loads(done.stdout)["status"] == "REFUSED"
    extra = subprocess.run([sys.executable, "-I", str(SCRIPT), "--probe", "mcp_health", "--url", "https://evil.example/"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert extra.returncode == 2 and extra.stdout == ""
    missing = subprocess.run([sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert missing.returncode == 2
