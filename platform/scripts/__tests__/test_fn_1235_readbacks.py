"""C49 — tests for platform/scripts/fn-1235-readbacks.sh.

The runner is the post-apply READ-ONLY readback for migration
1235_ka_gochara_staged_candidate_evidence_function.sql (PR #3018). These tests stub `psql`
with a fake on PATH that logs its argv, answers by substring-matching the SQL text it receives
against a fixture map, and never touches a database. Because the runner PINS its SQL file by
sha256, the harness writes a fixture SQL file, hashes it, and runs a COPY of the runner whose
PINNED_SHA256_fn_1235_evidence_readback_sql constant is rewritten to the fixture hash.

Covered:
* the happy path (function present, right signature/owner/secdef/search_path, exactly the three
  EXECUTE grants, no PUBLIC, no grant option, the ledger row with the pinned sha256);
* one STOP each for: function MISSING, wrong owner, a PUBLIC entry, a grant option, an extra
  grantee, a missing ledger row, a wrong ledger sha256;
* the pin refusal (a tampered SQL file is never executed), the backslash refusal;
* the read-only refusal: SHOW transaction_read_only != on -> exit 2;
* the no-DSN guarantee: the stub's argv log carries no -d/--dbname/postgresql:// and PGOPTIONS
  forces default_transaction_read_only=on;
* against a REAL disposable cluster (when PostgreSQL binaries exist): the fixture-built
  post-1235 state (function owned by amjis_app, the three grants, the ledger row) PASSES, and a
  GRANT to PUBLIC makes the runner STOP by name — against real pg catalogs, not a stub.
"""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/fn-1235-readbacks.sh"
SHA_1235 = "930902f6af470d3a6cdfd1b707ea23e6e365ad8c464004b9ed2a924194353682"
LEDGER_NAME = "1235_ka_gochara_staged_candidate_evidence_function.sql"

sys.path.insert(0, str(REPO / "platform/scripts/governance/__tests__"))
try:
    from _disposable_pg import disposable_pg, point_psql_at  # noqa: F401  (fixture import)
except Exception:  # pragma: no cover - helper missing: the real-cluster tests skip
    @pytest.fixture(scope="session")
    def disposable_pg():
        pytest.skip("the _disposable_pg helper is unavailable")

    def point_psql_at(cl, monkeypatch):  # noqa: ARG001
        pytest.skip("the _disposable_pg helper is unavailable")


@pytest.fixture(scope="session", autouse=True)
def _c_locale():
    old = os.environ.get("LC_ALL")
    os.environ["LC_ALL"] = "C"
    yield
    if old is None:
        os.environ.pop("LC_ALL", None)
    else:
        os.environ["LC_ALL"] = old


STUB = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
with open(os.environ["PSQL_ARGV_LOG"], "a") as f:
    f.write("\\t".join(args) + "\\n")
    f.write("PGOPTIONS=" + os.environ.get("PGOPTIONS", "") + "\\n")
sql = ""
for i, a in enumerate(args):
    if a == "-c" and i + 1 < len(args):
        sql = args[i + 1]
    if a == "-f" and i + 1 < len(args):
        sql = open(args[i + 1]).read()
if not sql:
    sql = sys.stdin.read()
text = open(os.environ["PSQL_ANSWERS"]).read()
blocks = [b.strip("\\n") for b in text.split("@@") if b.strip("\\n")]
for b in blocks:
    marker, _, body = b.partition("\\n")
    if marker in sql:
        if body.strip() == "!FAIL":
            print("psql: ERROR: stubbed failure", file=sys.stderr)
            sys.exit(1)
        sys.stdout.write(body)
        if body and not body.endswith("\\n"):
            sys.stdout.write("\\n")
        sys.exit(0)
print("psql: ERROR: no stub answer for SQL: " + sql[:200], file=sys.stderr)
sys.exit(1)
"""

FIXTURE_SQL = "-- C49 test readback fixture\nSELECT 1;\n"
FIXTURE_MARKER = "C49 test readback fixture"

HAPPY_READBACK = (
    "function\tpresent\n"
    "signature\tp_asset_id text\tboolean\n"
    "owner\tamjis_app\n"
    "security_definer\tt\n"
    "search_path\tsearch_path=pg_catalog, pg_temp\n"
    "acl\tamjis_app\tEXECUTE\tf\n"
    "acl\tnirmana_campaign_control_writer\tEXECUTE\tf\n"
    "acl\tnirmana_evidence_ingress_writer\tEXECUTE\tf\n"
    "acl_public_entries\t0\n"
    "acl_non_owner_grant_options\t0\n"
    f"ledger\t{LEDGER_NAME}\t{SHA_1235}\n"
)


def _answers(readback: str) -> str:
    return (
        "SHOW transaction_read_only\non\n@@\n"
        "SHOW default_transaction_read_only\non\n@@\n"
        "SELECT current_user\n"
        "c49\tc49\tsuvarna_disposable\t127.0.0.1\t1\tPostgreSQL test\n@@\n"
        f"{FIXTURE_MARKER}\n{readback}@@\n"
    )


def _harness(tmp_path: Path, readback: str, sql_text: str = FIXTURE_SQL):
    """A stub psql on PATH, the answers file, and a copy of the runner re-pinned to the
    fixture SQL file's real sha256. Returns (runner, out_dir, argv_log)."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    stub = bindir / "psql"
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    answers = tmp_path / "answers.txt"
    answers.write_text(_answers(readback))
    argv_log = tmp_path / "argv.log"
    argv_log.touch()
    sql_file = tmp_path / "fn_1235_evidence_readback.sql"
    sql_file.write_text(sql_text)
    sha = hashlib.sha256(sql_text.encode()).hexdigest()
    runner = tmp_path / "fn-1235-readbacks.sh"
    text = SCRIPT.read_text()
    text = text.replace(
        'PINNED_SHA256_fn_1235_evidence_readback_sql="0523e577292020d3ad820f63e4a14e41431f039d1b00be6a9502c115874a76d3"',
        f'PINNED_SHA256_fn_1235_evidence_readback_sql="{sha}"')
    assert sha in text, "the runner copy was not re-pinned"
    runner.write_text(text)
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    out = tmp_path / "out"
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    env["PSQL_ARGV_LOG"] = str(argv_log)
    env["PSQL_ANSWERS"] = str(answers)
    for k in [k for k in env if k.startswith("PG")]:
        env.pop(k)
    return runner, out, argv_log, env, sql_file


def _run(tmp_path, readback, sql_text=FIXTURE_SQL, extra_args=()):
    runner, out, argv_log, env, sql_file = _harness(tmp_path, readback, sql_text)
    proc = subprocess.run([str(runner), "--out", str(out), "--sql-file", str(sql_file), *extra_args],
                          capture_output=True, text=True, env=env)
    return proc, out, argv_log


def test_happy_path_all_pass(tmp_path):
    proc, out, argv_log = _run(tmp_path, HAPPY_READBACK)
    assert proc.returncode == 0, proc.stderr
    for check in ("FN1235-exists", "FN1235-signature", "FN1235-owner", "FN1235-secdef",
                  "FN1235-search-path", "FN1235-acl-no-public", "FN1235-acl-no-grant-option",
                  "FN1235-ledger", "FN1235-acl-exact", "session-read-only", "SESSION-identity"):
        assert f"PASS {check}" in proc.stdout, check
    assert "STOP" not in proc.stderr
    assert (out / "MANIFEST.sha256").exists() and (out / "RUNNER_SHA256").exists()
    log = argv_log.read_text()
    assert "-d" not in log and "--dbname" not in log and "postgresql://" not in log
    assert "default_transaction_read_only=on" in log


def _stop_case(tmp_path, readback, check):
    proc, _out, _log = _run(tmp_path, readback)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"STOP {check}" in proc.stderr, proc.stderr


def test_missing_function_stops(tmp_path):
    _stop_case(tmp_path, "function\tMISSING\n", "FN1235-exists")


def test_wrong_owner_stops(tmp_path):
    _stop_case(tmp_path, HAPPY_READBACK.replace("owner\tamjis_app", "owner\tpostgres"),
               "FN1235-owner")


def test_public_entry_stops(tmp_path):
    _stop_case(tmp_path, HAPPY_READBACK.replace("acl_public_entries\t0", "acl_public_entries\t1"),
               "FN1235-acl-no-public")


def test_grant_option_stops(tmp_path):
    _stop_case(tmp_path,
               HAPPY_READBACK.replace("acl_non_owner_grant_options\t0",
                                      "acl_non_owner_grant_options\t1"),
               "FN1235-acl-no-grant-option")


def test_an_extra_grantee_stops(tmp_path):
    bad = HAPPY_READBACK.replace("acl_public_entries\t0",
                                 "acl\tsome_other_role\tEXECUTE\tf\nacl_public_entries\t0")
    _stop_case(tmp_path, bad, "FN1235-acl-exact")


def test_a_missing_ledger_row_stops(tmp_path):
    bad = "\n".join(l for l in HAPPY_READBACK.splitlines() if not l.startswith("ledger\t")) + "\n"
    _stop_case(tmp_path, bad, "FN1235-ledger")


def test_a_wrong_ledger_sha_stops(tmp_path):
    _stop_case(tmp_path, HAPPY_READBACK.replace(SHA_1235, "0" * 64), "FN1235-ledger")


def test_a_tampered_sql_file_is_never_executed(tmp_path):
    runner, out, argv_log, env, sql_file = _harness(tmp_path, HAPPY_READBACK)
    sql_file.write_text(FIXTURE_SQL + "-- tampered\n")   # the runner's pin names the ORIGINAL bytes
    proc = subprocess.run([str(runner), "--out", str(out), "--sql-file", str(sql_file)],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 1
    assert "STOP FN1235-readback" in proc.stderr and "sha256" in proc.stderr
    # the tampered file was refused BEFORE execution: psql never saw a -f call
    assert "-f" not in argv_log.read_text()


def test_a_backslash_line_is_refused(tmp_path):
    proc, _out, argv_log = _run(tmp_path, HAPPY_READBACK, sql_text=FIXTURE_SQL + "\\echo hi\n")
    assert proc.returncode == 1
    assert "backslash" in proc.stderr


def test_a_writable_session_is_refused(tmp_path):
    runner, out, _log, env, sql_file = _harness(tmp_path, HAPPY_READBACK)
    answers = Path(env["PSQL_ANSWERS"])
    answers.write_text(_answers(HAPPY_READBACK).replace(
        "SHOW transaction_read_only\non\n", "SHOW transaction_read_only\noff\n"))
    proc = subprocess.run([str(runner), "--out", str(out), "--sql-file", str(sql_file)],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 2
    assert "REFUSAL: the session is not read-only" in proc.stderr


def test_expect_db_refusal(tmp_path):
    proc, _out, _log = _run(tmp_path, HAPPY_READBACK, extra_args=("--expect-db", "production"))
    assert proc.returncode == 2
    assert "--expect-db" in proc.stderr


# ── real disposable cluster ─────────────────────────────────────────────────

SETUP = f"""
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    CREATE ROLE amjis_app NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN
    CREATE ROLE nirmana_campaign_control_writer NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    CREATE ROLE nirmana_evidence_ingress_writer NOLOGIN; END IF;
END $$;
DROP FUNCTION IF EXISTS public.ka_gochara_staged_candidate_has_runtime_evidence(text) CASCADE;
CREATE TABLE IF NOT EXISTS public.asset_provenance_receipts (asset_id text);
CREATE TABLE IF NOT EXISTS public.build_run_assets (asset_id text);
CREATE TABLE IF NOT EXISTS public.asset_throughput (asset_id text);
CREATE TABLE IF NOT EXISTS public._migrations_applied
  (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now(), sha256 text NOT NULL);
GRANT CREATE ON SCHEMA public TO amjis_app;
SET ROLE amjis_app;
CREATE FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(p_asset_id text)
RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp AS $fn$
BEGIN
  IF p_asset_id IS NULL OR p_asset_id NOT IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5') THEN
    RAISE EXCEPTION 'not a staged Gochara candidate' USING ERRCODE = 'invalid_parameter_value';
  END IF;
  RETURN EXISTS (SELECT 1 FROM public.asset_provenance_receipts WHERE asset_id = p_asset_id)
      OR EXISTS (SELECT 1 FROM public.build_run_assets WHERE asset_id = p_asset_id)
      OR EXISTS (SELECT 1 FROM public.asset_throughput WHERE asset_id = p_asset_id);
END
$fn$;
REVOKE ALL ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO amjis_app;
GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text)
  TO nirmana_campaign_control_writer;
GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text)
  TO nirmana_evidence_ingress_writer;
RESET ROLE;
REVOKE CREATE ON SCHEMA public FROM amjis_app;
DELETE FROM public._migrations_applied WHERE filename = '{LEDGER_NAME}';
INSERT INTO public._migrations_applied (filename, sha256) VALUES ('{LEDGER_NAME}', '{SHA_1235}');
"""

def _real_run(disposable_pg, monkeypatch, tmp_path, setup_sql):
    point_psql_at(disposable_pg, monkeypatch)
    env = dict(os.environ)
    setup = subprocess.run(["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", setup_sql],
                           capture_output=True, text=True, env=env)
    assert setup.returncode == 0, setup.stderr
    out = tmp_path / "out-real"
    proc = subprocess.run(
        [str(SCRIPT), "--out", str(out),
         "--sql-file", "platform/scripts/readbacks/fn_1235_evidence_readback.sql"],
        capture_output=True, text=True, env=env, cwd=REPO)
    return proc


def test_real_cluster_fixture_state_passes(disposable_pg, monkeypatch, tmp_path):
    proc = _real_run(disposable_pg, monkeypatch, tmp_path, SETUP)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS FN1235-acl-exact" in proc.stdout and "PASS FN1235-ledger" in proc.stdout


def test_real_cluster_a_public_grant_stops(disposable_pg, monkeypatch, tmp_path):
    proc = _real_run(disposable_pg, monkeypatch, tmp_path, SETUP + (
        "GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text)"
        " TO PUBLIC;"))
    assert proc.returncode == 1
    assert "STOP FN1235-acl-no-public" in proc.stderr
    assert "STOP FN1235-acl-exact" in proc.stderr


def test_real_cluster_a_missing_ledger_row_stops(disposable_pg, monkeypatch, tmp_path):
    setup = SETUP.replace(
        f"INSERT INTO public._migrations_applied (filename, sha256) VALUES ('{LEDGER_NAME}', '{SHA_1235}');",
        "")
    proc = _real_run(disposable_pg, monkeypatch, tmp_path, setup)
    assert proc.returncode == 1
    assert "STOP FN1235-ledger" in proc.stderr
