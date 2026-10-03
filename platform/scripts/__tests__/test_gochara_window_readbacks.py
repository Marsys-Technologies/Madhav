"""C34 — tests for platform/scripts/gochara-window-readbacks.sh.

The runner is the protected-window sitting's READ-ONLY check harness. These tests stub `psql`
with a fake on PATH that logs its argv, answers by substring-matching the SQL text it receives
(-c / -f / stdin) against a fixture map, and never touches a database. Covered:

* every check's PASS path, in all three phases (pre-window, pre-train, post-window);
* one STOP per check (wrong value or stubbed psql failure) -> exit 1 and 'STOP <id>' on stderr;
* the read-only refusal: SHOW transaction_read_only != on -> exit 2;
* the no-DSN guarantee: the stub's argv log carries no -d/--dbname/postgresql:// and the
  session env forces default_transaction_read_only=on.
"""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/gochara-window-readbacks.sh"
SHA_1243 = "88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321"

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
EXPECTED_TSV = "TRG\tkala_gochara_coverage\ttg_a\nTRG\tkala_gochara_publication\ttg_b\n"
W6_ROW = "kala_gochara_coverage\tlegacy_tg\tO\tpublic.legacy_fn\tCREATE TRIGGER legacy_tg"
GUARD_ROWS = "guard1\tt\tt\tt\nguard2\tt\tt\tt\nguard3\tt\tt\tt\nguard4\tt\tt\tt"


def default_answers() -> list[tuple[str, str]]:
    return [
        ("SHOW transaction_read_only", "on"),
        ("SHOW default_transaction_read_only", "on"),
        ("= '1243_ka_gochara_inert_registry_rows.sql'",
         f"1243_ka_gochara_inert_registry_rows.sql\t{SHA_1243}"),
        ("filename LIKE '1206%'", "0"),
        ("ka_gochara_search_inventory_verification", ""),
        ("WHERE has_writer", "124"),
        ("depends_on && ARRAY", "0"),
        ("asset_provenance_receipts", "0\t0\t0"),
        ("a0f3e234dff2fdd9e4c9a90897e00e13", "2"),
        ("SELECT count(*) FROM public.asset_registry", "131"),
        ("SELECT filename FROM public._migrations_applied", "1200_x.sql\n1243_ka_gochara_inert_registry_rows.sql"),
        ("to_regclass('public.kala_gochara_coverage')",
         "kala_gochara_coverage\tkala_gochara_publication\tkala_gochara_contacts\tkala_gochara_windows"),
        ("generation ~", ""),
        ("tbl_update", "kala_gochara_coverage\tamjis_app\tf\tt\tt\tt\t"),
        ("to_regprocedure('public.ka_gochara_lock_chart(uuid)')", ""),
        ("has_function_privilege", "amjis_app\tt"),
        ("pg_db_role_setting", ""),
        ("pg_get_triggerdef", W6_ROW),
        ("gochara_verifier','gochara_sealer", "gochara_sealer\ngochara_verifier"),
        ("has_database_privilege('gochara_sealer'", "t"),
        ("has_schema_privilege('amjis_app'", "f"),
        ("ka_gochara_boundary_guard_inventory", GUARD_ROWS),
        ("C34 test registry readback", ""),
        ("C34 test privilege readback", ""),
        ("C34 test trigger manifest", "TRG\tkala_gochara_coverage\ttg_a\nTRG\tkala_gochara_publication\ttg_b"),
    ]


def run_script(
    tmp_path: Path,
    phase: str,
    overrides: dict[str, str] | None = None,
    baseline_rows: list[str] | None = None,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    stub = bin_dir / "psql"
    if not stub.exists():
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    sql_dir = tmp_path / "sql"
    sql_dir.mkdir(exist_ok=True)
    (sql_dir / "registry_1243_readback.sql").write_text(REGISTRY_FILE, encoding="utf-8")
    (sql_dir / "window_privilege_readback.sql").write_text(PRIVILEGE_FILE, encoding="utf-8")
    (sql_dir / "window_trigger_manifest.sql").write_text(MANIFEST_FILE, encoding="utf-8")
    (sql_dir / "EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv").write_text(EXPECTED_TSV, encoding="utf-8")

    answers = list((overrides or {}).items()) + default_answers()
    answers_text = "".join(f"@@{m}\n{b}\n" for m, b in answers)
    answers_file = tmp_path / "answers.txt"
    answers_file.write_text(answers_text, encoding="utf-8")
    argv_log = tmp_path / "argv.log"
    argv_log.write_text("", encoding="utf-8")

    args = ["bash", str(SCRIPT), phase, "--out", str(tmp_path / "out"), "--sql-dir", str(sql_dir)]
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


def test_pre_window_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-window")
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS session-read-only",
        "PASS R2-ledger-snapshot",
        "PASS R2-ledger-1243",
        "PASS R2-1206-absent",
        "PASS R2-registry-1243",
        "PASS W3-legacy-relations",
        "PASS W1-governed-rows",
        "PASS W2a-holders",
        "PASS W2b-lock-execute",
        "PASS W2c-isolation",
        "PASS W6-baseline",
        "RESULT: all checks PASS",
    ):
        assert check in r.stdout, f"{check} missing\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    manifest = (tmp_path / "out" / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert "R2-ledger-1243.out" in manifest
    assert "W6-baseline.out" in manifest


def test_pre_train_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "pre-train")
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS R7-roles-exist",
        "PASS W4-sealer-connect",
        "PASS R2-1206-absent",
        "PASS R2-ledger-1243",
    ):
        assert check in r.stdout, f"{check} missing\n{r.stdout}\n{r.stderr}"


def test_post_window_all_pass(tmp_path: Path) -> None:
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW])
    assert r.returncode == 0, r.stderr
    for check in (
        "PASS P9-privilege-readback",
        "PASS P9-schema-create",
        "PASS W2b-lock-execute",
        "PASS W2c-isolation",
        "PASS W5-manifest",
        "PASS W6-post",
    ):
        assert check in r.stdout, f"{check} missing\n{r.stdout}\n{r.stderr}"
    assert "0 production-only line(s)" in r.stdout
    assert "0 addition(s)" in r.stdout


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


STOP_CASES = [
    ("pre-window", {"= '1243_ka_gochara_inert_registry_rows.sql'": "1243_ka_gochara_inert_registry_rows.sql\tdeadbeef"}, "R2-ledger-1243"),
    ("pre-window", {"filename LIKE '1206%'": "1"}, "R2-1206-absent"),
    ("pre-window", {"SELECT count(*) FROM public.asset_registry": "130"}, "R2-registry-1243"),
    ("pre-window", {"to_regclass('public.kala_gochara_coverage')": "kala_gochara_coverage\t\tkala_gochara_contacts\tkala_gochara_windows"}, "W3-legacy-relations"),
    ("pre-window", {"generation ~": "11111111-0000-0000-0000-000000000000\t5.0"}, "W1-governed-rows"),
    ("pre-window", {"tbl_update": "!FAIL"}, "W2a-holders"),
    ("pre-window", {"to_regprocedure('public.ka_gochara_lock_chart(uuid)')": "ka_gochara_lock_chart",
                    "has_function_privilege": "amjis_app\tf"}, "W2b-lock-execute"),
    ("pre-window", {"pg_db_role_setting": "(all roles)\t(all databases)\t{work_mem=4MB}"}, "W2c-isolation"),
    ("pre-window", {"pg_get_triggerdef": "!FAIL"}, "W6-baseline"),
    ("pre-window", {"SELECT filename FROM public._migrations_applied": "!FAIL"}, "R2-ledger-snapshot"),
    ("pre-train", {"gochara_verifier','gochara_sealer": "gochara_verifier"}, "R7-roles-exist"),
    ("pre-train", {"has_database_privilege('gochara_sealer'": "f"}, "W4-sealer-connect"),
    ("post-window", {"C34 test privilege readback": "amjis_app\tpublic\tCREATE"}, "P9-privilege-readback"),
    ("post-window", {"has_schema_privilege('amjis_app'": "t"}, "P9-schema-create"),
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
    r = run_script(tmp_path, "post-window", baseline_rows=[W6_ROW, "kala_gochara_windows\told_tg\tO\tpublic.old_fn\tCREATE TRIGGER old_tg"])
    assert r.returncode == 1
    assert "STOP W6-post " in r.stderr
    assert "preservation failed" in r.stderr


def test_first_stop_aborts_remaining_checks_without_all(tmp_path: Path) -> None:
    r = run_script(
        tmp_path,
        "pre-window",
        overrides={"= '1243_ka_gochara_inert_registry_rows.sql'": "1243_ka_gochara_inert_registry_rows.sql\tdeadbeef"},
    )
    assert r.returncode == 1
    assert "STOP R2-ledger-1243 " in r.stderr
    assert "to_regclass('public.kala_gochara_coverage')" not in argv_log(tmp_path)
    assert "PASS W3-legacy-relations" not in r.stdout


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
