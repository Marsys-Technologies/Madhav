"""Token-free local Observatory acceptance gate; never reads project env files or provider keys."""

import datetime
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

platform = pathlib.Path(__file__).resolve().parents[2]
repo = platform.parent
day = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
evidence = repo / "00_ARCHITECTURE" / "briefs" / "observatory_metering" / "verification" / day
evidence.mkdir(parents=True, exist_ok=True)

# An allowlist prevents real keys, production DB settings, or CLI bridge credentials
# from entering test or build subprocesses through the operator's shell.
base_env = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR", "LANG", "CI") if key in os.environ}
base_env["NEXT_TELEMETRY_DISABLED"] = "1"
if "AI_METERING_PG_BIN" in os.environ:
    base_env["AI_METERING_PG_BIN"] = os.environ["AI_METERING_PG_BIN"]
fixture_env = {
    "NEXT_PUBLIC_FIREBASE_API_KEY": "AIza" + "A" * 35,
    "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN": "example.invalid",
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "local-metering-test",
    "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET": "example.invalid",
    "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID": "123456789",
    "NEXT_PUBLIC_FIREBASE_APP_ID": "1:123456789:web:localtest",
    "NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED": "true",
    "MARSYS_FLAG_OBSERVATORY_ENABLED": "true",
}

results: dict[str, dict[str, object]] = {}


def run(name: str, args: list[str], extra: dict[str, str] | None = None, cwd: pathlib.Path = platform) -> bool:
    environment = dict(base_env, **(extra or {}))
    started = time.monotonic()
    completed = subprocess.run(args, cwd=cwd, env=environment, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = evidence / f"{name}.log"
    log.write_text(completed.stdout)
    results[name] = {"exit_code": completed.returncode, "duration_seconds": round(time.monotonic() - started, 2),
                     "log": str(log)}
    print(f"{name}: {'PASS' if completed.returncode == 0 else 'FAIL'} ({log})", flush=True)
    return completed.returncode == 0


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def http_status(opener: urllib.request.OpenerDirector, url: str) -> int:
    try:
        with opener.open(url, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def smoke_built_app() -> bool:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = dict(base_env, **fixture_env, MARSYS_FLAG_AI_METERING_ENABLED="true")
    server_log = evidence / "http-server.log"
    with server_log.open("w") as output:
        server = subprocess.Popen([str(platform / "node_modules/.bin/next"), "start", "-p", str(port)],
                                  cwd=platform, env=environment, stdout=output, stderr=subprocess.STDOUT)
        try:
            opener = urllib.request.build_opener(NoRedirect)
            base = f"http://127.0.0.1:{port}"
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError("Built app exited before HTTP smoke")
                try:
                    if http_status(opener, base + "/login") == 200:
                        break
                except (urllib.error.URLError, TimeoutError):
                    pass
                time.sleep(0.1)
            else:
                raise RuntimeError("Built app did not become ready")
            expected = {"/api/usage": 401, "/api/admin/observatory/metering": 401,
                        "/api/admin/observatory/metering/manage": 401,
                        "/usage": 307, "/observatory/metering": 307}
            actual = {path: http_status(opener, base + path) for path in expected}
            passed = actual == expected
            (evidence / "http-smoke.json").write_text(json.dumps({"expected": expected, "actual": actual}, indent=2) + "\n")
            results["http_smoke"] = {"exit_code": 0 if passed else 1,
                                     "log": str(evidence / "http-smoke.json")}
            print(f"http_smoke: {'PASS' if passed else 'FAIL'} ({actual})", flush=True)
            return passed
        except Exception as error:
            results["http_smoke"] = {"exit_code": 1, "error": str(error), "log": str(server_log)}
            print(f"http_smoke: FAIL ({error})", flush=True)
            return False
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


enabled = dict(base_env, MARSYS_FLAG_AI_METERING_ENABLED="true")
run("enabled_focused", [str(platform / "node_modules/.bin/vitest"), "run", "src/lib/metering",
                        "src/components/metering", "src/lib/ai-console/execution/__tests__",
                        "src/app/api/pariprashna", "src/app/api/chat/consult", "src/app/api/mcp/prashna_ask"], enabled)
run("disposable_postgres", [sys.executable, str(platform / "scripts/observatory/local_metering_db_test.py")], enabled)
run("full_default_off", ["npm", "test"], dict(base_env, MARSYS_FLAG_AI_METERING_ENABLED="false"))
run("lint", ["npm", "run", "lint"])
run("typescript", [str(platform / "node_modules/.bin/tsc"), "--noEmit"])
built = run("build", ["npm", "run", "build"], dict(base_env, **fixture_env,
                                                      MARSYS_FLAG_AI_METERING_ENABLED="true"))
if built:
    smoke_built_app()
else:
    results["http_smoke"] = {"exit_code": 2, "reason": "build_failed"}

summary = {"schema": "madhav.observatory.local-acceptance.v1", "date_ist": day,
           "credential_environment": "allowlisted_test_variables_only", "stages": results}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
print("local_metering_acceptance:", "PASS" if all(row["exit_code"] == 0 for row in results.values()) else "FAIL")
sys.exit(0 if all(row["exit_code"] == 0 for row in results.values()) else 1)
