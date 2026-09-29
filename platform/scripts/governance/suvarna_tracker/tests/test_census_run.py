"""census_run.py (B6, review pass 3): the one command allowed to run the Nikaṣa asset census
inspector under the swarm's own permissions — it builds the fixed, validated invocation itself
from --layer/--out, never taking a caller-supplied command, and always runs it with
census_lock's --census-only re-validation."""
import subprocess
import sys

import pytest

from suvarna_tracker import census_lock as CL
from suvarna_tracker import census_run as CR


def test_build_command_shape():
    cmd = CR.build_command("ka_gochara", "/Users/Dev/suvarna/evidence/census.json")
    assert cmd[:2] == ["bash", "-c"]
    assert "asset_census.py" in cmd[2]
    assert "--layer ka_gochara" in cmd[2]
    assert "--out /Users/Dev/suvarna/evidence/census.json" in cmd[2]


def test_build_command_output_passes_is_census_only_command():
    cmd = CR.build_command("ka_gochara", "/Users/Dev/suvarna/evidence/census.json")
    assert CL.is_census_only_command(cmd)


# ---- CODE-35 (review pass 3 disposition): SUVARNA_CENSUS_ROOT, restricted to the two named roots -

def test_census_root_defaults_to_the_legacy_nikasha_checkout(monkeypatch):
    monkeypatch.delenv(CR.CENSUS_ROOT_ENV, raising=False)
    assert CR.census_root() == CR.DEFAULT_NIKASHA_ROOT


def test_census_root_reads_the_env_when_it_names_trunk(monkeypatch):
    monkeypatch.setenv(CR.CENSUS_ROOT_ENV, CR.TRUNK_ROOT)
    assert CR.census_root() == CR.TRUNK_ROOT


def test_census_root_refuses_an_arbitrary_env_value(monkeypatch):
    monkeypatch.setenv(CR.CENSUS_ROOT_ENV, "/tmp/not-an-allowed-checkout")
    with pytest.raises(CR.CensusRunError):
        CR.census_root()


def test_build_command_uses_trunk_root_when_env_names_it(monkeypatch):
    monkeypatch.setenv(CR.CENSUS_ROOT_ENV, CR.TRUNK_ROOT)
    cmd = CR.build_command("ka_gochara", "/Users/Dev/suvarna/evidence/census.json")
    assert f"cd {CR.TRUNK_ROOT} &&" in cmd[2]
    assert CL.is_census_only_command(cmd)


def test_build_command_refuses_an_explicit_root_outside_the_two():
    with pytest.raises(CR.CensusRunError):
        CR.build_command("ka_gochara", "/Users/Dev/suvarna/evidence/census.json",
                         nikasha_root="/Users/Dev/some-other-checkout")


def test_census_lock_and_census_run_agree_on_the_allowed_roots():
    """The two independent copies (census_lock.CENSUS_ALLOWED_ROOTS, census_run.CENSUS_ALLOWED_ROOTS)
    must name the same set — a drift between them would mean one validates against roots the other
    would refuse."""
    assert set(CL.CENSUS_ALLOWED_ROOTS) == set(CR.CENSUS_ALLOWED_ROOTS)


@pytest.mark.parametrize("layer", ["", "bad layer", "bad;layer", "bad&&layer", "../etc"])
def test_build_command_refuses_bad_layer(layer):
    with pytest.raises(CR.CensusRunError):
        CR.build_command(layer, "/tmp/out.json")


@pytest.mark.parametrize("out", ["", "relative/path.json", "/tmp/x;rm -rf ~", "/tmp/$(whoami).json",
                                 "/tmp/`whoami`.json", "/tmp/a b.json"])
def test_build_command_refuses_bad_out(out):
    with pytest.raises(CR.CensusRunError):
        CR.build_command("ka_gochara", out)


def test_main_refuses_bad_layer_without_running_anything(tmp_path, capsys):
    rc = CR.main(["--layer", "bad;layer", "--out", "/tmp/out.json", "--home", str(tmp_path)])
    assert rc == 2
    assert "refused" in capsys.readouterr().err


def test_main_runs_the_built_command_under_census_only(tmp_path, monkeypatch):
    home = str(tmp_path)
    captured = {}

    def fake_run_locked(home_, command, wait=0.0, emit_flag=False, actor="census", census_only=False):
        captured["command"] = command
        captured["census_only"] = census_only
        return 0

    monkeypatch.setattr(CR.census_lock, "run_locked", fake_run_locked)
    rc = CR.main(["--layer", "ka_gochara", "--out", "/Users/Dev/suvarna/evidence/census.json", "--home", home])
    assert rc == 0
    assert captured["census_only"] is True
    assert CL.is_census_only_command(captured["command"])


def test_main_requires_layer_and_out():
    with pytest.raises(SystemExit):
        CR.main([])


def test_end_to_end_with_a_stand_in_asset_census_script(tmp_path, monkeypatch):
    """No real /Users/Dev/madhav-nikasha checkout: exercise the whole path (build_command ->
    census_lock.run_locked -> subprocess) with subprocess.run substituted for a harmless stand-in,
    confirming the exact command that would run passes --census-only end to end."""
    home = str(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0))
    rc = CR.main(["--layer", "ka_gochara", "--out", "/Users/Dev/suvarna/evidence/census.json", "--home", home])
    assert rc == 0
