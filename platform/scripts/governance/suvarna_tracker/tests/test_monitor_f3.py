"""F3 (GPT-6 Astra independent review §2): the launch check matrix must not contradict itself
(isolation must not require the swarm's own reader credential to be unreadable) and must be
stage-aware (builder_scope informational before 'wave', required at 'wave')."""
import os

from suvarna_tracker import monitor as M


def cfg(tmp_path, **kw):
    home = kw.pop("home", str(tmp_path / "home"))
    return M.Config(home=home, **kw)


# ---- the isolation/reader-credential contradiction (F3's core claim) ---------------------------

def test_pgenv_is_never_in_the_isolation_unreadable_set(tmp_path):
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"))
    assert c.pgenv not in c.isolation_unreadable_paths


def test_native_files_are_still_in_the_isolation_unreadable_set(tmp_path):
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"))
    assert M.CODEX_PATH in c.isolation_unreadable_paths
    assert M.MADHAV_ADMIN_PATH in c.isolation_unreadable_paths
    assert all(p in c.isolation_unreadable_paths for p in M.DBENV_PATHS)
    assert M.NATIVE_CLAUDE_SETTINGS_PATH in c.isolation_unreadable_paths


class _FakeStat:
    def __init__(self, mode):
        self.st_mode = mode


def test_isolation_pgenv_problems_flags_unreadable_credential(tmp_path):
    """Negative case: the swarm's own reader credential must be readable — a config where it is
    NOT readable is a problem the check surfaces, never silently accepted."""
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"), isolation_access_fn=lambda path, mode: False,
           isolation_stat_fn=lambda path: _FakeStat(0o100600))
    problems = M._isolation_pgenv_problems(c)
    assert any("not readable" in p for p in problems)


def test_isolation_pgenv_problems_flags_wrong_mode(tmp_path):
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"), isolation_access_fn=lambda path, mode: True,
           isolation_stat_fn=lambda path: _FakeStat(0o100644))
    problems = M._isolation_pgenv_problems(c)
    assert any("group- or world-readable" in p for p in problems)


def test_isolation_pgenv_problems_clean_when_readable_and_mode_600(tmp_path):
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"), isolation_access_fn=lambda path, mode: True,
           isolation_stat_fn=lambda path: _FakeStat(0o100600))
    assert M._isolation_pgenv_problems(c) == []


def test_isolation_pgenv_problems_flags_unset_pgenv(tmp_path):
    c = cfg(tmp_path, pgenv=None)
    problems = M._isolation_pgenv_problems(c)
    assert any("no reader credential path configured" in p for p in problems)


# ---- stage-awareness: builder_scope ------------------------------------------------------------

def test_builder_scope_not_required_before_wave_is_ok_with_note(tmp_path):
    warn = M.CheckResult("builder_scope", "warn", "builder identity not provisioned (E7.2)")
    out = M.apply_stage([warn], "launch")
    r = out[0]
    assert r.status == "ok" and "not required at this stage" in r.detail


def test_builder_scope_still_ok_at_j1_stage(tmp_path):
    warn = M.CheckResult("builder_scope", "warn", "builder identity not provisioned (E7.2)")
    out = M.apply_stage([warn], "j1")
    assert out[0].status == "ok"


def test_builder_scope_unmeasured_is_block_at_wave_stage():
    """F3: 'a required check that cannot be measured is block at its stage' — builder_scope
    becomes required at 'wave', so its own 'warn' (cannot measure — not provisioned) becomes
    'block', never a soft warn a required check could otherwise slip past."""
    warn = M.CheckResult("builder_scope", "warn", "builder identity not provisioned (E7.2)")
    out = M.apply_stage([warn], "wave")
    r = out[0]
    assert r.status == "block" and "required at stage" in r.detail


def test_builder_scope_real_failure_stays_block_at_wave_stage():
    blocked = M.CheckResult("builder_scope", "block", "role=host (expected 'guest')")
    out = M.apply_stage([blocked], "wave")
    assert out[0].status == "block"


def test_builder_scope_ok_stays_ok_at_every_stage():
    ok = M.CheckResult("builder_scope", "ok", "builder x: role=guest status=active")
    for stage in M.STAGES:
        assert M.apply_stage([ok], stage)[0].status == "ok"


def test_other_checks_unaffected_by_stage():
    warn = M.CheckResult("power", "warn", "on battery at 80%")
    for stage in M.STAGES:
        out = M.apply_stage([warn], stage)
        assert out[0].status == "warn" and out[0].detail == "on battery at 80%"


def test_run_once_default_stage_is_launch_and_downgrades_builder_scope(tmp_path, monkeypatch):
    """Integration: a fresh environment (builder identity never provisioned) does not block launch
    by default, because builder_scope is not required until 'wave'."""
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"), power_source_fn=lambda: "ac",
           port_open_fn=lambda port: True, run_fn=lambda *a, **kw: (0, "caffeinate\n"),
           http_get_fn=lambda url, timeout: (200, '{"ok": true}', None),
           disk_free_fn=lambda path: 100 * 1024 ** 3,
           credential_query_fn=lambda pgenv, sql, timeout=10: (1, "", "no db"))
    os.makedirs(os.path.dirname(c.pgenv), exist_ok=True)
    with open(c.pgenv, "w") as f:
        f.write("export X=1\n")
    os.chmod(c.pgenv, 0o600)
    report = M.run_once(c, stage="launch")
    by_name = {ch["name"]: ch for ch in report["checks"]}
    assert by_name["builder_scope"]["status"] == "ok"
    assert "not required at this stage" in by_name["builder_scope"]["detail"]


def test_run_once_at_wave_stage_blocks_on_unprovisioned_builder_scope(tmp_path):
    c = cfg(tmp_path, pgenv=str(tmp_path / "pgenv.sh"), power_source_fn=lambda: "ac",
           port_open_fn=lambda port: True, run_fn=lambda *a, **kw: (0, "caffeinate\n"),
           http_get_fn=lambda url, timeout: (200, '{"ok": true}', None),
           disk_free_fn=lambda path: 100 * 1024 ** 3,
           credential_query_fn=lambda pgenv, sql, timeout=10: (1, "", "no db"))
    os.makedirs(os.path.dirname(c.pgenv), exist_ok=True)
    with open(c.pgenv, "w") as f:
        f.write("export X=1\n")
    os.chmod(c.pgenv, 0o600)
    report = M.run_once(c, stage="wave")
    by_name = {ch["name"]: ch for ch in report["checks"]}
    assert by_name["builder_scope"]["status"] == "block"
    assert report["overall"] == "block"


def test_cli_accepts_stage_flag():
    ap = M.build_arg_parser()
    ns = ap.parse_args(["--stage", "wave"])
    assert ns.stage == "wave"
    ns2 = ap.parse_args([])
    assert ns2.stage == "launch"
