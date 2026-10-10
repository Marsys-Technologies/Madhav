"""C34/C34b — tests for platform/scripts/gochara-window-readbacks.sh.

The runner is the protected-window sitting's READ-ONLY check harness. These tests stub `psql`
with a fake on PATH that logs its argv, answers by substring-matching the SQL text it receives
(-c / -f / stdin) against a fixture map, and never touches a database. Because the runner PINS
every SQL file it executes by sha256 (B5), the harness writes fixture SQL files, hashes them, and
runs a COPY of the runner whose PINNED_SHA256_* constants are rewritten to the fixture hashes.

Covered:
* every check's PASS path, in all four phases (pre-window, pre-train, pre-dispatch, post-window);
* W3 runs FIRST in pre-window (runbook order);
* B1 preread-refusals compare, B2 routine-predecessors (<=1240, window files excluded),
  B3a/B3b/B3c/B3d post-window readbacks, B4 W2(a) recheck against the pre-window baseline,
  B5 pin/backslash refusals (the tampered file is never executed), B6 session identity +
  --expect-db refusal;
* M2 REMOVED (C34c): --accept-dormant-holder no longer exists (usage refusal, exit 2) — a holder
  without EXECUTE is always a STOP;
  M3 REVIEW -> exit 3 (W5 production-only lines, W6 ka_gochara_boundary_* additions),
  M5 --expect-registry-rows/--expect-writers;
* C34c: R3-revoke-1302 (the 1302 ledger row, pinned sha) in pre-window, pre-train and pre-dispatch,
  and the ledger diff sorts BOTH sides LC_ALL=C (the unchanged-ledger false-STOP regression);
* one STOP per check -> exit 1 and 'STOP <id>' on stderr;
* the read-only refusal: SHOW transaction_read_only != on -> exit 2;
* the no-DSN guarantee: the stub's argv log carries no -d/--dbname/postgresql:// and the
  session env forces default_transaction_read_only=on;
* against a REAL disposable cluster (when PostgreSQL binaries exist): PGOPTIONS read-only makes an
  INSERT fail, and the runner itself records PASS session-read-only + SESSION-identity evidence and
  refuses a wrong --expect-db (it then STOPs at W3, as it must on an empty cluster).
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/gochara-window-readbacks.sh"
SHA_1243 = "88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321"
SHA_1302 = "35af45d0d545f7705f9bd8fd91635f715a2f27c288c83e999a5cd98c7983cb9e"

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
    """The disposable cluster's postmaster refuses to start under an invalid LC_ALL (macOS)."""
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
blocks = [b for b in text.split("@@") if b.strip("\\n")]
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

REGISTRY_FILE = "-- C34 test registry readback\nSELECT 1;\n"
PRIVILEGE_FILE = "-- C34 test privilege readback\nSELECT 1;\n"
MANIFEST_FILE = "-- C34 test trigger manifest\nSELECT 1;\n"
PREREAD_FILE = "-- C34 test preread refusals\nSELECT 1;\n"
EXPECTED_TSV = "TRG\tkala_gochara_coverage\ttg_a\nTRG\tkala_gochara_publication\ttg_b\n"

WINDOW_FILES = [
    "1204_gochara_av_qualifier_object_role.sql",
    "1206_gochara_search_inventory_completeness.sql",
    "1232_gochara_search_moon_scope_domain.sql",
    "1233_gochara_p1_period_anchor.sql",
    "1240_gochara_window_verification_gate.sql",
]
WINDOW_SHAS = ["ab" * 32, "cd" * 32, "ef" * 32, "01" * 32, "23" * 32]
EXPECTED_SHA_TXT = "".join(f"{s}  {n}\n" for n, s in zip(WINDOW_FILES, WINDOW_SHAS))
B3A_ANSWER = "\n".join(sorted(f"{n}\t{s}" for n, s in zip(WINDOW_FILES, WINDOW_SHAS)))

W6_ROW = "kala_gochara_coverage\tlegacy_tg\tO\tpublic.legacy_fn\tCREATE TRIGGER legacy_tg"
BOUNDARY_ROW = ("kala_gochara_windows\tka_gochara_boundary_guard_x\tO\tpublic.ka_gochara_boundary_guard_fn"
                "\tCREATE TRIGGER ka_gochara_boundary_guard_x")
GUARD_ROWS = "guard1\tt\tt\tt\nguard2\tt\tt\tt\nguard3\tt\tt\tt\nguard4\tt\tt\tt"
W2A_ROW = "kala_gochara_coverage\tamjis_app\tf\tt\tt\tt\t"

PRE_LEDGER = ["1153_a.sql", "1230_b.sql", "1243_ka_gochara_inert_registry_rows.sql"]
POST_LEDGER = sorted(PRE_LEDGER + WINDOW_FILES)
MIGRATION_FIXTURES = [
    "1153_a.sql",
    "1206_gochara_search_inventory_completeness.sql",   # a window file: B2 must EXCLUDE it
    "1230_b.sql",
    "1242_c.sql",                                        # > 1240: B2 must ignore it
    "1300_future.sql",                                   # > 1240: B2 must ignore it
]

PREREAD_ANSWER = "t\n0\n0\n1\tt\tt\tt\n0\n0"


def default_answers(ledger: list[str]) -> list[tuple[str, str]]:
    return [
        ("= '1243_ka_gochara_inert_registry_rows.sql'",
         f"1243_ka_gochara_inert_registry_rows.sql\t{SHA_1243}"),
        ("= '1302_revoke_role_orchestrator_windows_dml.sql'",
         f"1302_revoke_role_orchestrator_windows_dml.sql\t{SHA_1302}"),
        ("SELECT filename FROM public._migrations_applied", "\n".join(sorted(ledger))),
        ("SHOW transaction_read_only", "on"),
        ("SHOW default_transaction_read_only", "on"),
        ("inet_server_port()", "me\tme\tmydb\t127.0.0.1\t5432\tPostgreSQL 17.4"),
        ("SELECT current_database()", "mydb"),
        ("filename LIKE '1206%'", "0"),
        ("ka_gochara_search_inventory_verification", ""),
        ("WHERE has_writer", "124"),
        ("depends_on && ARRAY", "0"),
        ("asset_provenance_receipts", "0\t0\t0"),
        ("a0f3e234dff2fdd9e4c9a90897e00e13", "2"),
        ("SELECT count(*) FROM public.asset_registry", "131"),
        ("to_regclass('public.kala_gochara_coverage')",
         "kala_gochara_coverage\tkala_gochara_publication\tkala_gochara_contacts\tkala_gochara_windows"),
        ("generation ~", ""),
        ("tbl_update", W2A_ROW),
        ("to_regprocedure('public.ka_gochara_lock_chart(uuid)')", ""),
        ("has_function_privilege(oid", "amjis_app\tt"),
        ("pg_stat_activity", "t\t0\t0\t0"),
        ("pg_db_role_setting", ""),
        ("pg_get_triggerdef", W6_ROW),
        ("gochara_verifier','gochara_sealer", "gochara_sealer\ngochara_verifier"),
        ("has_database_privilege('gochara_sealer'", "t"),
        ("has_schema_privilege('amjis_app'", "f"),
        ("1204_gochara_av_qualifier_object_role", B3A_ANSWER),
        ("pg_get_userbyid", ""),
        ("has_function_privilege('PUBLIC'", ""),
        ("ka_gochara_boundary_guard_inventory", GUARD_ROWS),
        ("C34 test registry readback", ""),
        ("C34 test privilege readback", ""),
        ("C34 test trigger manifest", EXPECTED_TSV.strip()),
        ("C34 test preread refusals", PREREAD_ANSWER),
    ]


def _write_pinned_runner(tmp_path: Path, sql_dir: Path) -> Path:
    """A copy of the runner whose PINNED_SHA256_* constants name the FIXTURE files' hashes."""
    text = SCRIPT.read_text(encoding="utf-8")
    for f in sorted(sql_dir.iterdir()):
        var = "PINNED_SHA256_" + re.sub(r"[.-]", "_", f.name)
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        text, n = re.subn(rf'{var}="[0-9a-f]{{64}}"', f'{var}="{sha}"', text, count=1)
        if n:
            continue
        # not every fixture is pinned (EXPECTED_WINDOW_SHA256.txt is read, never executed)
    runner = tmp_path / "runner.sh"
    runner.write_text(text, encoding="utf-8")
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    return runner


def run_script(
    tmp_path: Path,
    phase: str,
    overrides: dict[str, str] | None = None,
    baseline_rows: list[str] | None = None,
    extra_args: list[str] | None = None,
    ledger: list[str] | None = None,
    w2a_baseline_rows: list[str] | None = None,
    tamper: str | None = None,
    backslash: str | None = None,
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True, parents=True)
    stub = bin_dir / "psql"
    if not stub.exists():
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    sql_dir = tmp_path / "sql"
    sql_dir.mkdir(exist_ok=True)
    fixtures = {
        "registry_1243_readback.sql": REGISTRY_FILE,
        "window_privilege_readback.sql": PRIVILEGE_FILE,
        "window_trigger_manifest.sql": MANIFEST_FILE,
        "window_preread_refusals.sql": PREREAD_FILE,
        "EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv": EXPECTED_TSV,
        "EXPECTED_WINDOW_SHA256.txt": EXPECTED_SHA_TXT,
    }
    for name, content in fixtures.items():
        if backslash == name:
            content += "\\! echo pwned\n"
        (sql_dir / name).write_text(content, encoding="utf-8")
    runner = _write_pinned_runner(tmp_path, sql_dir)
    if tamper:
        with open(sql_dir / tamper, "a", encoding="utf-8") as fh:   # AFTER the pin was computed
            fh.write("-- tampered after pinning\n")

    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir(exist_ok=True)
    for name in MIGRATION_FIXTURES:
        (mig_dir / name).write_text("-- fixture\n", encoding="utf-8")

    if ledger is None:
        ledger = POST_LEDGER if phase in ("pre-dispatch", "post-window") else PRE_LEDGER
    answers = list((overrides or {}).items()) + default_answers(ledger)
    answers_text = "".join(f"@@{m}\n{b}\n" for m, b in answers)
    answers_file = tmp_path / "answers.txt"
    answers_file.write_text(answers_text, encoding="utf-8")
    argv_log = tmp_path / "argv.log"
    argv_log.write_text("", encoding="utf-8")

    args = ["bash", str(runner), phase, "--out", str(tmp_path / "out"),
            "--sql-dir", str(sql_dir), "--migrations-dir", str(mig_dir)]
    if phase in ("pre-dispatch", "post-window"):
        snapshot = tmp_path / "ledger_snapshot.tsv"
        snapshot.write_text("".join(r + "\n" for r in sorted(PRE_LEDGER)), encoding="utf-8")
        args += ["--ledger-snapshot", str(snapshot)]
    if phase == "post-window":
        rows = [W2A_ROW] if w2a_baseline_rows is None else w2a_baseline_rows
        w2a_base = tmp_path / "w2a_baseline.tsv"
        w2a_base.write_text("".join(r + "\n" for r in sorted(rows)), encoding="utf-8")
        args += ["--w2a-baseline", str(w2a_base)]
    if baseline_rows is not None:
        baseline = tmp_path / "baseline.tsv"
        baseline.write_text("".join(r + "\n" for r in sorted(baseline_rows)), encoding="utf-8")
        args += ["--baseline", str(baseline)]
    args += extra_args or []

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["PSQL_ANSWERS"] = str(answers_file)
    env["PSQL_ARGV_LOG"] = str(argv_log)
    env.pop("PGOPTIONS", None)
    return subprocess.run(args, env=env, capture_output=True, text=True, timeout=120)


def argv_log(tmp_path: Path) -> str:
    return (tmp_path / "argv.log").read_text(encoding="utf-8")


# ── PASS paths ────────────────────────────────────────────────────────────────

def test_pre_window_all_pass_w3_first(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window")
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS session-read-only",
        "PASS SESSION-identity",
        "PASS W3-legacy-relations",
        "PASS R2-ledger-snapshot",
        "PASS R2-ledger-1243",
        "PASS R3-revoke-1302",
        "PASS R2-1206-absent",
        "PASS R2-registry-1243",
        "PASS R-preread-refusals",
        "PASS R2-routine-predecessors",
        "PASS W1-governed-rows",
        "PASS W2a-holders",
        "PASS W2b-lock-execute",
        "PASS W2c-isolation",
        "PASS W6-baseline",
        "RESULT: all checks PASS",
    ):
        assert check in r.stdout, f"{check} missing\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert r.stdout.index("PASS W3-legacy-relations") < r.stdout.index("PASS R2-ledger-snapshot"), \
        "W3 must run FIRST"
    assert (tmp_path / "out" / "baseline_legacy.tsv").read_text(encoding="utf-8").strip() == W6_ROW
    manifest = (tmp_path / "out" / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert "R2-ledger-1243.out" in manifest
    assert "SESSION-identity.out" in manifest
    assert "baseline_legacy.tsv" in manifest


def test_pre_train_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-train")
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS R7-roles-exist",
        "PASS W4-sealer-connect",
        "PASS R2-1206-absent",
        "PASS R2-ledger-1243",
        "PASS R3-revoke-1302",
        "PASS R2-registry-1243",
    ):
        assert check in r.stdout, f"{check} missing\n{r.stdout}\n{r.stderr}"


def test_pre_dispatch_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-dispatch")
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS R-preread-refusals",
        "PASS R2-1206-absent",
        "PASS R7-roles-exist",
        "PASS R8-ledger-diff",
        "PASS R2-ledger-1243",
        "PASS R3-revoke-1302",
    ):
        assert check in r.stdout, f"{check} missing\n{r.stdout}\n{r.stderr}"
    assert "5 new" in r.stdout   # only the five window files are new vs the row-2 snapshot


def test_post_window_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW])
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS P9-privilege-readback",
        "PASS P9-schema-create",
        "PASS P9-window-files-ledger",
        "PASS P9-ka-gochara-ownership",
        "PASS P9-public-execute",
        "PASS P9-ledger-diff",
        "PASS W2b-lock-execute",
        "PASS W2c-isolation",
        "PASS P9-w2a-recheck",
        "PASS W5-manifest",
        "PASS W6-post",
    ):
        assert check in r.stdout, f"{check} missing\n{r.stdout}\n{r.stderr}"
    assert "0 production-only line(s)" in r.stdout
    assert "0 addition(s)" in r.stdout


def test_expect_db_pass_and_refusal(tmp_path: Path) -> None:
    ok = run_script(tmp_path / "ok", "pre-train", extra_args=["--expect-db", "mydb"])
    assert ok.returncode == 0, ok.stderr
    assert "PASS SESSION-expect-db current_database()=mydb" in ok.stdout
    bad = run_script(tmp_path / "bad", "pre-train", extra_args=["--expect-db", "wrong"])
    assert bad.returncode == 2
    assert "REFUSAL: current_database() is 'mydb', --expect-db says 'wrong'" in bad.stderr


def test_readonly_refusal_exit2(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", overrides={"SHOW transaction_read_only": "off"})
    assert r.returncode == 2
    assert "REFUSAL: the session is not read-only" in r.stderr


def test_no_dsn_on_argv_and_pgoptions_forces_readonly(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window")
    assert r.returncode == 0, r.stderr
    log = argv_log(tmp_path)
    for line in log.splitlines():
        if line.startswith("PGOPTIONS="):
            assert "default_transaction_read_only=on" in line
            continue
        args = line.split("\t")
        assert "-d" not in args and "--dbname" not in args
        assert not any(a.startswith("--dbname=") for a in args)
        assert "postgresql://" not in line


# ── B5: pins and the backslash refusal ───────────────────────────────────────

def test_tampered_file_is_refused_before_execution(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", tamper="window_preread_refusals.sql")
    assert r.returncode == 1
    assert "STOP R-preread-refusals " in r.stderr
    assert "sha256" in r.stderr and "tampered or stale" in r.stderr
    assert "window_preread_refusals.sql" not in argv_log(tmp_path), \
        "the tampered file must never reach psql"


def test_backslash_line_is_refused(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", backslash="window_preread_refusals.sql")
    assert r.returncode == 1
    assert "STOP R-preread-refusals " in r.stderr
    assert "backslash" in r.stderr
    assert "window_preread_refusals.sql" not in argv_log(tmp_path)


# ── W2b: a holder without EXECUTE is always a STOP (no dormant exception) ─────

LOCK_OVERRIDES = {
    "to_regprocedure('public.ka_gochara_lock_chart(uuid)')": "ka_gochara_lock_chart",
    "has_function_privilege(oid": "amjis_app\tt\nrole_orchestrator\tf",
}


def test_holder_without_lock_execute_stops(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", overrides=dict(LOCK_OVERRIDES))
    assert r.returncode == 1
    assert "STOP W2b-lock-execute " in r.stderr
    assert "always a STOP" in r.stderr


def test_accept_dormant_holder_option_is_gone(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", overrides=dict(LOCK_OVERRIDES),
                   extra_args=["--accept-dormant-holder", "role_orchestrator"])
    assert r.returncode == 2                      # usage refusal: the option no longer exists


# ── B3d: the ledger diff sorts BOTH sides LC_ALL=C (C34c regression) ──────────

def test_ledger_diff_passes_when_the_db_order_is_not_the_c_order(tmp_path: Path) -> None:
    # Stream B's C34b review: on production the ledger comes back in the DATABASE collation, and
    # comm against the C-sorted snapshot reported 3 phantom "new" entries on an UNCHANGED ledger.
    # The stub emits the row-2 names in a non-C order; an unchanged ledger must PASS with 0 new.
    scrambled = ["1243_ka_gochara_inert_registry_rows.sql", "1153_a.sql", "1230_b.sql"]
    r = run_script(tmp_path, "pre-dispatch",
                   overrides={"SELECT filename FROM public._migrations_applied": "\n".join(scrambled)})
    assert r.returncode == 0, r.stderr
    assert "PASS R8-ledger-diff" in r.stdout
    assert "0 new" in r.stdout


# ── M3: REVIEW -> exit 3 ─────────────────────────────────────────────────────

def test_w5_production_only_lines_are_a_review_exit3(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW],
                   overrides={"C34 test trigger manifest":
                              EXPECTED_TSV.strip() + "\nTRG\tkala_gochara_windows\ttg_extra"})
    assert r.returncode == 3, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert "REVIEW W5-production-only" in r.stdout
    assert "RESULT: checks PASS with 1 REVIEW(s)" in r.stdout


def test_w6_boundary_addition_is_a_review_exit3(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW],
                   overrides={"pg_get_triggerdef": W6_ROW + "\n" + BOUNDARY_ROW})
    assert r.returncode == 3, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert "REVIEW W6-additions" in r.stdout
    assert "ka_gochara_boundary_" in r.stdout


# ── M5 / B4: extra STOP paths ────────────────────────────────────────────────

def test_expect_registry_rows_mismatch_stops(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window", extra_args=["--expect-registry-rows", "999"])
    assert r.returncode == 1
    assert "STOP R2-registry-1243 " in r.stderr
    assert "registry_rows=131/999" in r.stderr


def test_w2a_recheck_stops_on_a_new_holder(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW], w2a_baseline_rows=[])
    assert r.returncode == 1
    assert "STOP P9-w2a-recheck " in r.stderr
    assert "NEW effective UPDATE/DELETE holder" in r.stderr


# ── one STOP per check ────────────────────────────────────────────────────────

STOP_CASES = [
    ("pre-window", {"= '1243_ka_gochara_inert_registry_rows.sql'": "1243_ka_gochara_inert_registry_rows.sql\tdeadbeef"}, "R2-ledger-1243"),
    ("pre-window", {"= '1302_revoke_role_orchestrator_windows_dml.sql'": ""}, "R3-revoke-1302"),
    ("pre-train", {"= '1302_revoke_role_orchestrator_windows_dml.sql'": "1302_revoke_role_orchestrator_windows_dml.sql\tdeadbeef"}, "R3-revoke-1302"),
    ("pre-window", {"filename LIKE '1206%'": "1"}, "R2-1206-absent"),
    ("pre-window", {"SELECT count(*) FROM public.asset_registry": "130"}, "R2-registry-1243"),
    ("pre-window", {"to_regclass('public.kala_gochara_coverage')": "kala_gochara_coverage\t\tkala_gochara_contacts\tkala_gochara_windows"}, "W3-legacy-relations"),
    ("pre-window", {"generation ~": "11111111-0000-0000-0000-000000000000\t5.0"}, "W1-governed-rows"),
    ("pre-window", {"tbl_update": "!FAIL"}, "W2a-holders"),
    ("pre-window", {"to_regprocedure('public.ka_gochara_lock_chart(uuid)')": "ka_gochara_lock_chart",
                    "has_function_privilege(oid": "amjis_app\tf"}, "W2b-lock-execute"),
    ("pre-window", {"pg_db_role_setting": "(all roles)\t(all databases)\t{work_mem=4MB}"}, "W2c-isolation"),
    ("pre-window", {"pg_get_triggerdef": "!FAIL"}, "W6-baseline"),
    ("pre-window", {"SELECT filename FROM public._migrations_applied": "!FAIL"}, "R2-ledger-snapshot"),
    ("pre-window", {"C34 test preread refusals": "t\n0\n0\n0\tt\tt\tt\n0\n0"}, "R-preread-refusals"),
    ("pre-window", {"SELECT filename FROM public._migrations_applied": "1153_a.sql\n1243_ka_gochara_inert_registry_rows.sql"},
     "R2-routine-predecessors"),
    ("pre-train", {"gochara_verifier','gochara_sealer": "gochara_verifier"}, "R7-roles-exist"),
    ("pre-train", {"has_database_privilege('gochara_sealer'": "f"}, "W4-sealer-connect"),
    ("pre-dispatch", {"SELECT filename FROM public._migrations_applied":
                      "\n".join(sorted(POST_LEDGER + ["1241_evil.sql"]))}, "R8-ledger-diff"),
    ("post-window", {"C34 test privilege readback": "amjis_app\tpublic\tCREATE"}, "P9-privilege-readback"),
    ("post-window", {"has_schema_privilege('amjis_app'": "t"}, "P9-schema-create"),
    ("post-window", {"1204_gochara_av_qualifier_object_role":
                     B3A_ANSWER.replace("ab" * 32, "ff" * 32)}, "P9-window-files-ledger"),
    ("post-window", {"pg_get_userbyid": "relation\tka_gochara_x\tpostgres"}, "P9-ka-gochara-ownership"),
    ("post-window", {"has_function_privilege('PUBLIC'": "ka_gochara_evil"}, "P9-public-execute"),
    ("post-window", {"SELECT filename FROM public._migrations_applied":
                     "\n".join(sorted(POST_LEDGER + ["1241_evil.sql"]))}, "P9-ledger-diff"),
    ("post-window", {"C34 test trigger manifest": "TRG\tkala_gochara_coverage\ttg_a"}, "W5-manifest"),
    ("post-window", {"ka_gochara_boundary_guard_inventory": "guard1\tt\tt\tt"}, "W5-guard-inventory"),
]


@pytest.mark.parametrize(("phase", "overrides", "stop_id"), STOP_CASES, ids=[c[2] for c in STOP_CASES])
def test_one_stop_per_check(tmp_path: Path, phase: str, overrides: dict[str, str], stop_id: str) -> None:
    baseline = [W6_ROW] if phase == "post-window" else None
    r = run_script(tmp_path, phase, overrides=overrides, baseline_rows=baseline)
    assert r.returncode == 1, f"expected exit 1\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert f"STOP {stop_id} " in r.stderr, r.stderr


def test_w6_post_stops_when_a_baseline_trigger_is_gone(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window",
                   baseline_rows=[W6_ROW, "kala_gochara_windows\told_tg\tO\tpublic.old_fn\tCREATE TRIGGER old_tg"])
    assert r.returncode == 1
    assert "STOP W6-post " in r.stderr
    assert "preservation failed" in r.stderr


def test_first_stop_aborts_remaining_checks_without_all(tmp_path: Path) -> None:
    r = run_script(
        tmp_path,
        "pre-window",
        overrides={"to_regclass('public.kala_gochara_coverage')": "kala_gochara_coverage"},
    )
    assert r.returncode == 1
    assert "STOP W3-legacy-relations " in r.stderr
    assert "generation ~" not in argv_log(tmp_path), "W1 must not run after W3 STOPs"
    assert "PASS R2-ledger-snapshot" not in r.stdout


def test_all_flag_collects_multiple_stops(tmp_path: Path) -> None:
    r = run_script(
        tmp_path,
        "pre-train",
        overrides={
            "gochara_verifier','gochara_sealer": "gochara_verifier",
            "has_database_privilege('gochara_sealer'": "f",
        },
        extra_args=["--all"],
    )
    assert r.returncode == 1
    assert "STOP R7-roles-exist " in r.stderr
    assert "STOP W4-sealer-connect " in r.stderr
    assert "RESULT: 2 STOP(s)" in r.stderr


# ── M8: against a REAL disposable cluster (skips only when no PG binaries) ────

def test_pgoptions_readonly_session_cannot_write(disposable_pg) -> None:
    cl = disposable_pg
    cl.psql("CREATE TABLE IF NOT EXISTS c34_ro_probe (id int)")
    env = {k: v for k, v in os.environ.items() if not (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL"))}
    env.update(cl.env())
    env["PGOPTIONS"] = "-c default_transaction_read_only=on"
    p = subprocess.run([str(cl.bin_dir / "psql"), "-X", "-q", "-c", "INSERT INTO c34_ro_probe VALUES (1)"],
                       env=env, capture_output=True, text=True, timeout=60)
    assert p.returncode != 0
    assert "read-only transaction" in p.stderr


def test_runner_against_a_real_cluster(disposable_pg, tmp_path, monkeypatch) -> None:
    cl = disposable_pg
    point_psql_at(cl, monkeypatch)
    out = tmp_path / "out"
    r = subprocess.run(
        ["bash", str(SCRIPT), "pre-window", "--out", str(out), "--sql-dir", str(tmp_path / "no-such-dir")],
        capture_output=True, text=True, timeout=180)
    assert r.returncode == 1, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert "PASS session-read-only" in r.stdout
    assert "PASS SESSION-identity" in r.stdout
    assert "STOP W3-legacy-relations" in r.stderr   # an empty disposable cluster has no legacy relations
    identity = (out / "SESSION-identity.out").read_text(encoding="utf-8")
    assert cl.user in identity and "PostgreSQL" in identity
    assert (out / "MANIFEST.sha256").exists()

    wrong = subprocess.run(
        ["bash", str(SCRIPT), "pre-window", "--out", str(tmp_path / "out2"),
         "--sql-dir", str(tmp_path / "no-such-dir"), "--expect-db", "definitely_not_this_db"],
        capture_output=True, text=True, timeout=180)
    assert wrong.returncode == 2
    assert "REFUSAL: current_database()" in wrong.stderr

    right = subprocess.run(
        ["bash", str(SCRIPT), "pre-window", "--out", str(tmp_path / "out3"),
         "--sql-dir", str(tmp_path / "no-such-dir"), "--expect-db", cl.dbname],
        capture_output=True, text=True, timeout=180)
    assert right.returncode == 1
    assert f"PASS SESSION-expect-db current_database()={cl.dbname}" in right.stdout
