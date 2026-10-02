"""No database: the bound constants, the data-driven function list, the plan hash, the GATE_V2 wiring and the argument gates."""
from __future__ import annotations

import dataclasses
import difflib
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

import conftest as cf
from conftest import EXEC_DIR, GATE_FIXTURE, REPO, load_exec


def fresh(name="d6_fresh"):
    return load_exec(name)


# ---------------------------------------------------------------------------------------------------- the TBD pin test
def test_gate_pins_are_bound():
    """DELIBERATELY RED until the three GATE_V2 sha256 are bound (gate revision 3 not yet bound): the plan hash printed by this version is
    PROVISIONAL BY DESIGN. Bind the pins in GATE_PINS, re-freeze, and this test turns green."""
    m = fresh("d6_pins")
    unbound = [k for k, v in m.GATE_PINS.items() if v == m.GATE_TBD]
    assert not unbound, f"GATE_PINS are TBD for {unbound}: bind them at gate revision 3 (the plan hash is provisional until then)"


# ---------------------------------------------------------------------------------------------------- bound constants
def test_live_definitions_are_the_bound_pre_state(mod):
    for p in mod.FUNCTION_PATCHES:
        text = p.live_def()                      # raises ExpectedDiffError on any difference
        assert hashlib.md5(text.encode()).hexdigest() == p.live_md5 and len(text) == p.live_len
        assert hashlib.sha256(text.encode()).hexdigest() == p.live_sha256
    assert mod.CAPTURE_PATCH.live_md5 == "1e079261aa42eb97a1885a48035e7520"      # read live as suvarna_reader 2026-10-02


def test_every_hunk_matches_exactly_once_and_its_new_text_is_not_in_the_live_body(mod):
    for p in mod.FUNCTION_PATCHES:
        live = p.live_def()
        for name, old, new in p.hunks:
            assert live.count(old) == 1, name
            assert new not in live, name
            assert new != old


def test_patched_body_differs_from_live_ONLY_by_the_named_hunks(mod):
    """Reconstruct the zero-context diff and compare line by line with the hunk texts: nothing but H1, H2, H3a, H3b and the F-A2 hunk."""
    p = mod.CAPTURE_PATCH
    live, patched = p.live_def(), p.patched_def()
    removed, added = [], []
    for ln in difflib.unified_diff(live.splitlines(True), patched.splitlines(True), n=0):
        if ln.startswith(("---", "+++", "@@")):
            continue
        (removed if ln[0] == "-" else added).append(ln[1:])
    nl = lambda ls: [l if l.endswith("\n") else l + "\n" for l in ls]            # a hunk's last line carries no newline of its own
    old_lines = {l for _, old, _n in p.hunks for l in nl(old.splitlines(True))}
    new_lines = {l for _, _o, new in p.hunks for l in nl(new.splitlines(True))}
    assert all(l in old_lines for l in removed), [l for l in removed if l not in old_lines]      # every removed line is a hunk anchor line
    assert all(l in new_lines for l in added), [l for l in added if l not in new_lines]          # every added line is hunk text
    assert len(removed) == 3                                                                      # H3b's `),` and the F-A2 key and ORDER BY lines
    # and the transformation IS the hunk list: patching the live text with the hunks reproduces the body byte for byte
    assert mod.pa.apply_hunks(live, p.hunks) == patched
    assert [h[0] for h in p.hunks] == ["H1_declare_v_typed_col_v_companions", "H2_all_null_row_is_floored_or_unavailable",
                                       "H3a_typed_value_precedence_num_text_jsonb", "H3b_grain_jsonb_records_kept_and_dropped_columns",
                                       "F_A2_dependency_identity_fact_subject"]
    assert len(removed) == 3 and len(mod.pa.unified_hunks(live, patched)) == p.diff_hunks == 6
    assert hashlib.md5(patched.encode()).hexdigest() == p.patched_md5
    assert hashlib.sha256(patched.encode()).hexdigest() == p.patched_sha256
    assert mod.pa.diff_digest(live, patched) == p.diff_sha256


def test_the_precedence_in_the_hunk_is_num_then_text_then_jsonb(mod):
    new = mod.pa.H3A_NEW
    assert new.index("v_typed_col := 'fact_value_num'") < new.index("v_typed_col := 'fact_value_text'")
    assert "v_value_text := NULL; v_value_jsonb := NULL;" in new and "v_value_jsonb := NULL;" in new
    assert "typed_value_column" in mod.pa.H3B_NEW and "companion_value_columns" in mod.pa.H3B_NEW
    assert "'{}'::jsonb" in mod.pa.H3B_NEW                     # nothing dropped: grain_jsonb is exactly what it was


def test_expected_diff_is_generated_from_the_function_list(mod):
    ed = mod.EXPECTED_DIFF
    assert len(ed["functions"]) == len(mod.FUNCTION_PATCHES)
    for entry, p in zip(ed["functions"], mod.FUNCTION_PATCHES):
        assert entry["function"] == p.signature and entry["live_md5"] == p.live_md5 and entry["patched_md5"] == p.patched_md5
        assert entry["zero_context_diff_sha256"] == p.diff_sha256 and entry["differs_ONLY_by_hunks"] == [h[0] for h in p.hunks]


def test_adding_a_function_is_adding_data(mod, tmp_path, monkeypatch):
    """A second FunctionPatch changes EXPECTED_DIFF, the plan text and the plan hash, and the legs carry both steps."""
    m = fresh("d6_two")
    base_hash = m.plan_hash_unbound()
    live = tmp_path / "live_defs"
    live.mkdir()
    body = "CREATE OR REPLACE FUNCTION public.other_fn()\n RETURNS integer\n LANGUAGE sql\nAS $function$ SELECT 1 $function$\n"
    (live / "other_fn.LIVE.sql").write_bytes(body.encode())
    shutil.copy(m.CAPTURE_PATCH.live_file, live / m.CAPTURE_PATCH.live_file.name)
    monkeypatch.setattr(m, "LIVE_DEFS", live)
    hunk = ("X", "SELECT 1", "SELECT 2")
    new = m.pa.apply_hunks(body, [hunk])
    p2 = m.FunctionPatch(signature="other_fn()", live_md5=hashlib.md5(body.encode()).hexdigest(), live_len=len(body),
                         live_sha256=hashlib.sha256(body.encode()).hexdigest(), owner=m.OWNER, secdef=False, config="", acl="",
                         hunks=(hunk,), patched_md5=hashlib.md5(new.encode()).hexdigest(), patched_sha256=hashlib.sha256(new.encode()).hexdigest(),
                         diff_sha256=m.pa.diff_digest(body, new), diff_hunks=len(m.pa.unified_hunks(body, new)))
    monkeypatch.setattr(m, "FUNCTION_PATCHES", m.FUNCTION_PATCHES + (p2,))
    assert p2.patched_def() == new
    assert len(m.forward_leg().functions) == 2 and len(m.rollback_leg().functions) == 2
    assert "other_fn()" in m.render_plan() and m.plan_hash_unbound() != base_hash
    assert len(m._expected_functions()) == 2
    # a hunk anchor that is not unique is refused
    bad = dataclasses.replace(p2, hunks=(("X", "S", "T"),))
    with pytest.raises(m.ExpectedDiffError, match="occurs"):
        bad.patched_def()


# ---------------------------------------------------------------------------------------------------- plan hash
def test_plan_hash_binds_the_executor_the_diff_the_constants_and_the_gate(mod):
    base = mod.plan_hash()
    assert mod.plan_hash(sha="0" * 64) != base                                  # the executor's own sha is in the plan text
    for name in mod.GATE_PINS:
        assert mod.plan_hash(pins=dict(mod.GATE_PINS, **{name: "1" * 64})) != base, name
    es = mod.standards()
    unbound = mod.plan_hash_unbound()
    fp = {"gate_sha256": mod.GATE_PINS["prerun_gate.py"], "run_gated_sha256": mod.GATE_PINS["run_gated.sh"]}
    assert es.bind_gate_into_plan_hash(unbound, fp) == base
    assert es.bind_gate_into_plan_hash(unbound, dict(fp, gate_sha256="1" * 64)) != base
    assert es.bind_gate_into_plan_hash(unbound, dict(fp, run_gated_sha256="1" * 64)) != base
    # the formula is sha256(plan text + "\n" + json(EXPECTED_DIFF))
    text = mod.render_plan()
    assert unbound == hashlib.sha256((text + "\n" + json.dumps(mod.EXPECTED_DIFF, sort_keys=True)).encode()).hexdigest()
    ed = dict(mod.EXPECTED_DIFF, comments="x")
    assert hashlib.sha256((text + "\n" + json.dumps(ed, sort_keys=True)).encode()).hexdigest() != unbound
    for const in ("LIVE_TRG_DIGEST", "PATCHED_TRG_DIGEST"):
        assert getattr(mod, const) in text
    for p in mod.FUNCTION_PATCHES:
        for v in (p.live_md5, p.patched_md5, p.live_sha256, p.patched_sha256, p.diff_sha256):
            assert v in text


def test_plan_text_names_executor_modules_live_definitions_and_gate_pins(mod):
    text = mod.render_plan()
    assert mod.exec_sha() in text
    for f in ("d6_f_a2_key_widening_DRAFT.py", "d6_capture_patch_a.py"):
        assert hashlib.sha256((EXEC_DIR / f).read_bytes()).hexdigest() in text
    for p in mod.FUNCTION_PATCHES:
        assert hashlib.sha256(p.live_file.read_bytes()).hexdigest() in text
    for v in mod.GATE_PINS.values():
        assert v in text
    assert "bind_gate_into_plan_hash" in text and "GATE_V2" in text and "outcome.json" in text and "exit 93" in text
    assert "run_gated.sh" in text and "--expect-plan" in text


def test_plan_txt_is_the_rendering_with_the_current_pins():
    m = fresh("d6_plantxt")
    assert (EXEC_DIR / "plan.txt").read_text() == m.render_plan() + "\n", "re-render plan.txt with make_plan.py --write"


def test_the_plan_hash_does_not_need_the_plan_file(mod):
    """The owner's authorisation binds the plan FILE's sha256; the plan hash must not contain it (no circularity): nothing in the executor
    reads a *.md plan file."""
    src = (EXEC_DIR / "d6_dataplane_capture_fa2_exec.py").read_text()
    assert "PLAN.md" not in src and "_PLAN_v" not in src and ".md" not in src.replace("md5", "")


def test_the_f_a2_writer_digest_in_the_frozen_draft_equals_the_repository_inventory(mod):
    inv = json.loads((REPO / "platform/src/generated/nirmana-writer-digests.json").read_text())
    assert inv["writers"]["ga_vargas"] == mod.fa2.WRITER_DIGEST


# ---------------------------------------------------------------------------------------------------- GATE_V2 launch
def marker(es, now=None, gate_dir=GATE_FIXTURE):
    return es.make_marker(str(gate_dir / "prerun_gate.py"), str(gate_dir / "run_gated.sh"), now=now)


def env_with(**kw):
    return dict({"DPFA2_TEST_GATE_DIR": str(GATE_FIXTURE), "PYTEST_CURRENT_TEST": "x"}, **kw)


def refused(mod, capsys, environ, reason):
    with pytest.raises(SystemExit) as e:
        mod.launch_gate(environ)
    assert e.value.code == 93
    err = capsys.readouterr().err
    assert "REFUSED" in err and reason in err


def test_the_fixture_gate_files_are_the_byte_identical_gate_v2_rev3_files(mod):
    """tests/gate_fixture = exec/gate_v2 at PR #2938 head 7f0db55c3 (revision 3); GATE_REV3_PROPOSED is the proposal, NOT a binding."""
    assert cf.fixture_pins() == mod.GATE_REV3_PROPOSED == {
        "prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
        "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
        "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
    gv2 = EXEC_DIR.parent / "gate_v2"
    if gv2.exists():                                                  # once PR #2938 is merged the fixture must still equal it
        for n in mod.GATE_REV3_PROPOSED:
            assert (gv2 / n).read_bytes() == (GATE_FIXTURE / n).read_bytes(), n


def test_the_proposed_pins_are_not_the_bound_pins():
    m = fresh("d6_proposed")
    assert all(v == m.GATE_TBD for v in m.GATE_PINS.values()) and m.GATE_REV3_PROPOSED != m.GATE_PINS


def test_an_under_test_launch_marker_is_refused_in_every_mode_outside_pytest(mod, capsys):
    es = mod.standards(env_with())
    ut = es.make_marker(str(GATE_FIXTURE / "prerun_gate.py"), str(GATE_FIXTURE / "run_gated.sh"), under_test=True)
    # the verifier (executor_standards) is itself under test when GATE_V2_UNDER_TEST=1 is in the operator's shell, so it ACCEPTS the marker...
    fp = mod.launch_gate(env_with(GATE_V2_LAUNCH=ut))
    assert fp["under_test"] is True
    # ...and the executor refuses it anyway, before the arguments are parsed, unless it runs inside pytest
    operator_env = {"GATE_V2_UNDER_TEST": "1"}
    with pytest.raises(SystemExit) as e:
        mod.refuse_under_test_outside_pytest(fp, environ=operator_env)
    assert e.value.code == 93 and "ran under test" in capsys.readouterr().err
    mod.refuse_under_test_outside_pytest(fp, environ={"PYTEST_CURRENT_TEST": "x"})            # the harness
    mod.refuse_under_test_outside_pytest(dict(fp, under_test=False), environ=operator_env)    # a production marker
    src = (EXEC_DIR / "d6_dataplane_capture_fa2_exec.py").read_text()
    body = src[src.index("def main("):]
    assert body.index("launch_gate()") < body.index("refuse_under_test_outside_pytest(gate_fp)") < body.index("parse_args(")


def test_launch_gate_refuses_without_a_marker(mod, capsys):
    refused(mod, capsys, env_with(), "no_marker")
    refused(mod, capsys, env_with(GATE_V2_LAUNCH=""), "no_marker")


def test_launch_gate_accepts_a_launcher_marker_for_the_pinned_files(mod):
    es = mod.standards(env_with())
    fp = mod.launch_gate(env_with(GATE_V2_LAUNCH=marker(es)))
    assert fp["gate_sha256"] == mod.GATE_PINS["prerun_gate.py"] and fp["run_gated_sha256"] == mod.GATE_PINS["run_gated.sh"]
    assert fp["under_test"] is False


def test_launch_gate_refuses_forged_stale_future_and_edited(mod, capsys, tmp_path):
    es = mod.standards(env_with())
    m = marker(es)
    refused(mod, capsys, env_with(GATE_V2_LAUNCH=m[:-1] + ("0" if m[-1] != "0" else "1")), "marker_check_mismatch")
    refused(mod, capsys, env_with(GATE_V2_LAUNCH="garbage"), "malformed_marker")
    import time
    refused(mod, capsys, env_with(GATE_V2_LAUNCH=marker(es, now=time.time() - 7 * 3600)), "marker_stale")
    refused(mod, capsys, env_with(GATE_V2_LAUNCH=marker(es, now=time.time() + 3600)), "marker_from_the_future")
    # an edited gate file: marker made on the edited copy, but the pins are the reviewed shas
    d = tmp_path / "gate"
    shutil.copytree(GATE_FIXTURE, d)
    (d / "prerun_gate.py").write_text((d / "prerun_gate.py").read_text() + "\n# edited\n")
    env = env_with(DPFA2_TEST_GATE_DIR=str(d), GATE_V2_LAUNCH=marker(es, gate_dir=d))
    refused(mod, capsys, env, "gate_sha_differs_from_plan")
    (d / "prerun_gate.py").write_bytes((GATE_FIXTURE / "prerun_gate.py").read_bytes())
    (d / "executor_standards.py").write_text((d / "executor_standards.py").read_text() + "\n# edited\n")
    with pytest.raises(SystemExit) as e:
        mod.launch_gate(env_with(DPFA2_TEST_GATE_DIR=str(d), GATE_V2_LAUNCH=marker(es, gate_dir=GATE_FIXTURE)))
    assert e.value.code == 93
    assert "executor_standards.py differs" in capsys.readouterr().err


def test_launch_gate_refuses_while_the_pins_are_tbd(capsys):
    m = fresh("d6_tbd")                         # the shipped constants
    assert all(v == m.GATE_TBD for v in m.GATE_PINS.values())
    es = m.standards(env_with())
    refused(m, capsys, env_with(GATE_V2_LAUNCH=marker(es)), "TBD")


def test_main_calls_launch_gate_FIRST_before_arguments_and_before_any_secret(mod, monkeypatch, capsys):
    monkeypatch.delenv("GATE_V2_LAUNCH", raising=False)
    monkeypatch.setattr(mod, "connect_admin", lambda: pytest.fail("connected"))
    with pytest.raises(SystemExit) as e:
        mod.main(["--this-is-not-an-argument"])          # argparse would exit 2; the launch gate must refuse first (93)
    assert e.value.code == 93
    src = (EXEC_DIR / "d6_dataplane_capture_fa2_exec.py").read_text()
    body = src[src.index("def main("):]
    assert body.index("launch_gate()") < body.index("parse_args(") < body.index("install_signal_handlers()")


# ---------------------------------------------------------------------------------------------------- arguments, test variables
def test_every_connecting_mode_requires_expect_plan_and_apply_rollback_require_evidence(mod):
    for flags in (["--count"], ["--dry-run"], ["--apply"], ["--rollback-dry-run"], ["--rollback"]):
        with pytest.raises(SystemExit) as e:
            mod.parse_args(flags)
        assert e.value.code == 2, flags
    with pytest.raises(SystemExit):
        mod.parse_args(["--apply", "--expect-plan", "0" * 64, "--writer-commit", cf.COMMIT])           # no --expect-evidence
    with pytest.raises(SystemExit):
        mod.parse_args(["--rollback", "--expect-plan", "0" * 64])
    with pytest.raises(SystemExit):
        mod.parse_args(["--apply", "--expect-plan", "0" * 64, "--expect-evidence", "0" * 64])          # no --writer-commit
    with pytest.raises(SystemExit):
        mod.parse_args(["--dry-run", "--apply", "--expect-plan", "0" * 64])                            # exclusive
    assert mod.parse_args(["--dry-run", "--expect-plan", "0" * 64]).mode == "dry-run"


def test_a_wrong_plan_hash_is_refused_before_any_connection_and_recorded(mod, tmp_path):
    args = mod.parse_args(["--dry-run", "--expect-plan", "0" * 64])
    with pytest.raises(SystemExit) as e:
        mod.execute(args, lambda: pytest.fail("connected"))
    assert "REFUSED" in str(e.value)
    outs = list((tmp_path / "ev").glob("*/outcome.json"))
    assert len(outs) == 1
    body = json.loads(outs[0].read_text())
    assert body["status"] == "failed" and body["failed_checks"] == ["args_expect_plan_mismatch"]
    assert oct(outs[0].stat().st_mode & 0o777) == "0o600" and oct(outs[0].parent.stat().st_mode & 0o777) == "0o700"


def test_stray_test_variables_are_refused_outside_pytest(mod, capsys):
    with pytest.raises(SystemExit) as e:
        mod.resolve_evidence_root(environ={"DPFA2_TEST_EVIDENCE_ROOT": "/tmp/x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        mod.resolve_evidence_root(environ={"DPFA2_TEST_EVIDENCE_ROOT": "", "PYTEST_CURRENT_TEST": "x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        mod.gate_dir(environ={"DPFA2_TEST_GATE_DIR": str(GATE_FIXTURE)})
    assert e.value.code == 95
    assert mod.resolve_evidence_root(environ={}) == mod.EVIDENCE_ROOT
    assert mod.gate_dir(environ={}) == EXEC_DIR.parent / "gate_v2"


def test_the_real_gate_launcher_chain_refuses_a_direct_start(tmp_path):
    """Started directly (no run_gated.sh), the executor refuses with 93 and prints no plan. No network, no credential: a bare environment."""
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    r = subprocess.run([sys.executable, str(EXEC_DIR / "d6_dataplane_capture_fa2_exec.py"), "--dry-run", "--expect-plan", "0" * 64],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path))
    assert r.returncode == 93, (r.stdout, r.stderr)
    assert "REFUSED" in r.stderr and "Traceback" not in r.stderr
