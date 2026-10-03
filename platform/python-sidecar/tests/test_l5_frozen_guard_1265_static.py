"""1265 owner-path package: STATIC tier (DB-free). The package lives under 00_ARCHITECTURE/briefs/suvarna/exec/l5_frozen_guard_1265; the SQL is
NEVER under platform/migrations or platform/supabase/migrations (migrate.ts would pick it up and block deploys)."""
from __future__ import annotations

import ast
import hashlib
import io
import json
import re
import sys
import tokenize

import pytest

from tests.l5_frozen_guard_world import FORWARD, MIGRATIONS, PKG, REPO, ROLLBACK, body, load_exec

EX = load_exec("l5_frozen_guard_exec_static")
FW = FORWARD.read_text(encoding="utf8")
RB = ROLLBACK.read_text(encoding="utf8")


def code(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))


def flat(sql: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", sql, flags=re.M))


# ---- the standing rule: owner-path SQL never lives in platform/migrations ---------------------------------------------

def test_the_sql_is_in_the_executor_package_and_nowhere_under_a_migrations_directory():
    assert FORWARD.is_file() and ROLLBACK.is_file()
    assert "platform/migrations" not in FORWARD.as_posix() and "supabase/migrations" not in FORWARD.as_posix()
    for d in MIGRATIONS:
        names = [p.name for p in d.iterdir()]
        assert not [n for n in names if n.startswith("1265_")], d
    for d in MIGRATIONS:
        for p in d.glob("*.sql"):
            text = p.read_text(encoding="utf8", errors="ignore")
            assert "mimamsa_predictions_frozen_row_guard" not in text and "l5_frozen_chart_cascade_authorizes" not in text, p


def test_migrate_ts_discovery_does_not_list_the_package_sql():
    """migrate.ts reads exactly platform/migrations and platform/supabase/migrations (scripts/migrate.ts main(): dirs = [...]) and only *.sql files
    directly inside them. Reproduce its discovery and assert the package files are not in it, and that the dirs list in migrate.ts is still those two."""
    ts = (REPO / "platform/scripts/migrate.ts").read_text(encoding="utf8")
    assert "path.resolve(scriptDir, '../migrations')" in ts and "path.resolve(scriptDir, '../supabase/migrations')" in ts
    assert ts.count("fs.readdirSync(dir)") == 1
    found = sorted(p.name for d in MIGRATIONS for p in d.iterdir() if p.suffix == ".sql")
    assert "1265_l5_frozen_row_guards.sql" not in found and "1265_l5_frozen_row_guards.ROLLBACK.sql" not in found
    assert not any("frozen_row_guards" in n for n in found)


# ---- the shipped SQL carries exactly the bound bodies --------------------------------------------------------------

def test_verify_sql_bodies_passes_and_the_captured_builder_guard_is_byte_exact():
    EX.verify_sql_bodies()
    b = body(FW, "guard")
    assert hashlib.md5(b.encode()).hexdigest() == EX.BUILDER_MD5 and len(b.encode()) == EX.BUILDER_LEN == 1084
    assert b.startswith("\nBEGIN\n  IF current_user = 'data_plane_builder'") and b.endswith("\nEND\n")


@pytest.mark.parametrize("sig", sorted(EX.NEW_FUNCTIONS))
def test_every_new_function_body_is_pinned_in_the_script_the_rollback_and_the_executor(sig):
    tag, md5 = EX.NEW_FUNCTIONS[sig]
    assert hashlib.md5(body(FW, tag).encode()).hexdigest() == md5
    assert FW.count(md5) >= 2 and RB.count(md5) >= 1


def test_a_hand_edit_of_a_body_is_refused_before_any_database_work():
    for tag in ("predictions", "cascade", "helper", "bmpl", "prospective", "manifestation", "guard"):
        edited = FW.replace(body(FW, tag), body(FW, tag) + " ")
        with pytest.raises(EX.ExpectedDiffError):
            EX.verify_sql_bodies(forward=edited)


def test_plan_txt_is_current_and_the_two_hashes_are_reproducible():
    text = (PKG / "plan.txt").read_text(encoding="utf8")
    assert text.startswith(EX.render_plan())
    assert EX.exec_sha() in text and EX.sha_file(FORWARD) in text and EX.sha_file(ROLLBACK) in text
    for n in EX.VERIFY_FILES:
        assert EX.sha_file(PKG / "sql" / n) in text
    assert EX.plan_hash_unbound() != EX.plan_hash() and re.fullmatch(r"[0-9a-f]{64}", EX.plan_hash())
    assert json.loads(text.split("-- EXPECTED_DIFF\n", 1)[1]) == json.loads(json.dumps(EX.expected_diff()))


def test_the_plan_hash_changes_with_the_sql_the_executor_and_the_gate_pins():
    base = EX.plan_hash_unbound()
    assert EX.plan_hash_unbound(sha="0" * 64) != base
    pins = dict(EX.GATE_PINS, **{"run_gated.sh": "f" * 64})
    assert EX.plan_hash_unbound(pins=pins) != base
    assert EX.plan_hash(pins=pins) != EX.plan_hash()


def test_gate_pins_equal_the_gate_v2_files_in_the_repo():
    for n, pin in EX.GATE_PINS.items():
        assert hashlib.sha256((REPO / "00_ARCHITECTURE/briefs/suvarna/exec/gate_v2" / n).read_bytes()).hexdigest() == pin, n


# ---- the SQL script: shape ----------------------------------------------------------------------------------------

def test_script_is_schema_code_only_no_grant_no_registry_no_rls_no_transaction_control():
    c = code(FW)
    assert c.strip().startswith("SET LOCAL lock_timeout = '5s';")
    for s in (c, code(RB)):
        assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", s, re.M)
        assert not re.search(r"\bGRANT\b", s), "this script never issues a GRANT (the recorded builder grants are only asserted)"
        assert not re.search(r"asset_registry|_migrations_applied|CREATE POLICY|(ENABLE|DISABLE|NO FORCE|FORCE)\s+ROW LEVEL SECURITY\s*;", s), "the script never changes row security (it only READS relforcerowsecurity)"
    assert not re.search(r"\b(DROP TABLE|DROP COLUMN|ADD COLUMN|CREATE TABLE|CREATE INDEX|ALTER COLUMN)\b", c)
    assert len(re.findall(r"\bINSERT INTO\b", c)) == 4 and "1265_selftest_ok" in c      # only the rolled-back probes
    assert c.count("REVOKE ALL ON FUNCTION") == 5


def test_every_new_trigger_is_enable_always_and_only_the_planned_eight_are_created():
    c = code(FW)
    assert "EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I'" in c
    names = re.findall(r"\('(\w+)', '(\w+)', (\d+), '(\w+)'\)", c.split("DO $triggers$")[1].split("$triggers$;")[0])
    assert sorted((a, b, int(t)) for a, b, t, _ in names) == sorted((t[0], t[1], t[2]) for t in EX.NEW_TRIGGERS)


def test_gate_names_the_missing_privilege_and_the_assertions_raise():
    c = code(FW)
    for needle in ("has_schema_privilege(current_user, 'public', 'CREATE')", "pg_has_role(current_user, rel_owner, 'MEMBER')",
                   "this file records it, it does not create it", "is not the repo version", "refusing to overwrite it",
                   "refusing to overwrite a changed live guard", "1265 post-check", "1265 self-test FAILED", "LIKE prefix || '%'"):
        assert needle in c, needle


def test_the_guards_read_no_setting_and_test_no_role_name():
    for tag in ("predictions", "prospective", "manifestation", "bmpl", "helper", "cascade"):
        b = body(FW, tag)
        assert "current_setting" not in b and not re.search(r"current_user\s*=|session_user\s*=|rolsuper|usesuper", b), tag
    cas = body(FW, "cascade")
    assert "NOT EXISTS (SELECT 1 FROM public.charts c WHERE c.id = p_chart)" in cas
    assert not re.search(r"pg_trigger_depth\(\)", code(cas)) or "pg_trigger_depth" not in "\n".join(l for l in cas.splitlines() if not l.lstrip().startswith("--")), "the discriminator never uses trigger depth (spoofable)"
    assert "SECURITY DEFINER\n SET search_path = pg_catalog, pg_temp\nAS $cascade$" in FW, "SECURITY DEFINER because charts has row-level security"
    for tag in ("predictions", "prospective", "manifestation", "bmpl"):
        b = body(FW, tag)
        assert b.index("IF public.l5_frozen_chart_cascade_authorizes") < b.index("IF public.l5_frozen_withdrawal_authorizes") < b.rindex("cannot be deleted")


def test_allow_lists_are_exactly_the_decided_columns_and_everything_else_fails_closed():
    pred = body(FW, "predictions")
    assert re.findall(r"'([a-z_]+)'", re.search(r"c_mutable\s+CONSTANT text\[\] := ARRAY\[(.*?)\];", pred, re.S).group(1)) == [
        "lifecycle_status", "chart_context_stale_at", "chart_context_stale_reason", "chart_context_superseded_by_run_id"]
    pro = body(FW, "prospective")
    assert re.findall(r"'([a-z_]+)'", re.search(r"c_mutable\s+CONSTANT text\[\] := ARRAY\[(.*?)\];", pro, re.S).group(1)) == [
        "lifecycle_status", "matched_event_id", "matched_at", "match_note", "chart_context_stale_at", "chart_context_stale_reason",
        "chart_context_superseded_by_run_id"]
    for b in (pred, pro):
        assert "to_jsonb(OLD) - c_mutable" in b and "to_jsonb(NEW) - c_mutable" in b
    man = body(FW, "manifestation")
    assert "to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)" in man and "c_mutable" not in man, "no mutable column on manifestation sets"
    assert "UPDATE" not in body(FW, "bmpl").replace("-- UPDATE", ""), "the ledger's UPDATE freeze stays with trg_bmpl_freeze_confirmed"


def test_mimamsa_calibration_tables_are_not_guarded_by_ruling():
    c = code(FW)
    assert not re.search(r"ON public\.mimamsa_calibration", c)


def test_header_states_the_decisions_privilege_order_exceptions_and_what_is_not_done():
    h = flat(FW)
    for n in ("OWNER-PATH SQL, NOT A MIGRATION", "must never be placed under platform/migrations", "N-104 and N-107", "ASSERT-AND-RECORD",
              "data_plane_builder holds exactly SELECT, INSERT, DELETE", "never issues a GRANT",
              "TWO data-driven exceptions (SS N-107 and N-108)", "no charts row with that id", "frozen = every row, pending included",
              "NOT guarded by ruling: mimamsa_calibration and mimamsa_calibration_snapshot", "ORDER: after S-L1", "RLS is NOT armed",
              "Break-glass", "CAN disable a trigger"):
        assert n in h, n


def test_the_executor_names_who_runs_what_and_never_touches_deploy_infrastructure():
    src = (PKG / "l5_frozen_guard_exec.py").read_text(encoding="utf8")
    for n in ("GRANT CREATE ON SCHEMA public TO", "REVOKE CREATE ON SCHEMA public FROM", "data_plane_schema_owner", "GRANT \" + r + \" TO CURRENT_USER",
              "EXIT_INTERPRETER = 92", "EXIT_NO_LAUNCH = 93", "pre_writer_first", "pre_recorded_builder_grant_", "commit_state_unknown"):
        assert n in src, n
    rest = code_py(src.split('"""', 2)[2])      # after the module docstring, which explains why
    assert "deploy.yml" not in rest and "migrate.ts" not in rest


def code_py(src: str) -> str:
    return "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))


# ---- Python 3.11 floor --------------------------------------------------------------------------------------------

def _py_files():
    return sorted(p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: p.name)
def test_every_package_file_parses_under_the_python_311_grammar(path):
    ast.parse(path.read_text(), filename=str(path), feature_version=(3, 11))


def test_no_fstring_reuses_its_own_quote_type_inside_a_replacement_field():
    if sys.version_info < (3, 12):
        pytest.skip("on < 3.12 the parser itself rejects the construct")
    bad = []
    for path in _py_files() + [REPO / "platform/python-sidecar/tests/l5_frozen_guard_world.py"]:
        depth = []
        for tk in tokenize.generate_tokens(io.StringIO(path.read_text()).readline):
            if tk.type == tokenize.FSTRING_START:
                depth.append(tk.string.lstrip("rbfRBF")[0])
            elif tk.type == tokenize.FSTRING_END:
                depth.pop()
            elif tk.type == tokenize.STRING and depth and tk.string.lstrip("rbfRBF")[0] == depth[-1]:
                bad.append((path.name, tk.start))
    assert not bad, bad


# ---- STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on charts without revisiting the guard -------------------

def test_the_standing_constraint_is_in_the_readme_the_script_the_plan_and_the_hashed_verify_files():
    readme = (PKG / "README.md").read_text(encoding="utf8")
    assert "no FORCE ROW LEVEL SECURITY on `charts` without first revisiting this guard" in readme
    assert "Is this README inside the bound hash inputs? No." in readme
    h = flat(FW)
    assert "STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on public.charts" in h
    assert FW.count("relforcerowsecurity") >= 3                          # gate, post-check, discriminator
    assert "relforcerowsecurity" in body(FW, "cascade") and "RAISE EXCEPTION" in body(FW, "cascade")
    plan = EX.render_plan()
    assert "STANDING CONSTRAINT (SS): public.charts must NOT have FORCE ROW LEVEL SECURITY" in plan and "verify_charts_rls_constraint.sql" in plan
    assert "verify_charts_rls_constraint.sql" in EX.VERIFY_FILES and EX.sha_file(PKG / "sql" / "verify_charts_rls_constraint.sql") in plan
    assert "standing_constraint" in EX.expected_diff()
    src = (PKG / "l5_frozen_guard_exec.py").read_text(encoding="utf8")
    assert "pre_standing_constraint_charts_not_force_rls" in src and "post_standing_constraint_charts_not_force_rls" in src and "WARN: STANDING CONSTRAINT VIOLATED" in src


def test_readme_and_plan_txt_are_not_hash_inputs_but_the_executor_sql_and_verify_files_are():
    base = EX.plan_hash()
    # the plan hash reads the rendered text, which names sha256 of the sql, verify files and the executor; the README and plan.txt are never read by it
    assert "README" not in EX.render_plan() and "plan.txt" not in EX.render_plan()
    import pathlib
    readme = PKG / "README.md"
    original = readme.read_text(encoding="utf8")
    try:
        readme.write_text(original + "\nan edit\n", encoding="utf8")
        assert EX.plan_hash() == base
    finally:
        readme.write_text(original, encoding="utf8")
