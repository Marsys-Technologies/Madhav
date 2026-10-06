"""Native rule 2026-10-01: Kimi K3-256k — LOW effort for execution/coding (stream runners), HIGH for reviews."""
import subprocess
import sys

from pravaha_tracker import kimi_review, runner

CONFIG = '''default_model = "kimi-code/k3-256k"

[models."kimi-code/k3"]
default_effort = "max"

[models."kimi-code/k3-256k"]
model = "k3-256k"
default_effort = "{effort}"
'''


def _effort(path, model="kimi-code/k3-256k"):
    inside = False
    for ln in open(path).read().split("\n"):
        if ln.startswith("["):
            inside = ln.strip() == f'[models."{model}"]'
        elif inside and ln.startswith("default_effort"):
            return ln.split("=")[1].strip().strip('"')


def _patch(monkeypatch, tmp_path, effort):
    cfg = tmp_path / "config.toml"
    cfg.write_text(CONFIG.format(effort=effort))
    monkeypatch.setattr(runner, "KIMI_CONFIG", str(cfg))
    monkeypatch.setattr(runner, "CONFIG_LOCK", str(tmp_path / "lock"))
    monkeypatch.setattr(runner, "EFFORT_SETTLE_S", 0.3)
    return cfg


def test_defaults_are_k3_256k_low_for_execution_and_high_for_review():
    assert runner.MODEL_ID == "kimi-code/k3-256k" and runner.EFFORT == "low"
    assert kimi_review.REVIEW_MODEL == "kimi-code/k3-256k" and kimi_review.REVIEW_EFFORT == "high"


def test_stream_start_resets_a_rewritten_config_to_low(monkeypatch, tmp_path):
    cfg = _patch(monkeypatch, tmp_path, "high")          # another tool rewrote it
    seen = tmp_path / "seen"
    probe = [sys.executable, "-c", f"import shutil; shutil.copy({str(cfg)!r}, {str(seen)!r})"]
    runner.launch_with_effort(runner.MODEL_ID, runner.EFFORT, probe).wait()
    assert _effort(seen) == "low"                         # what the starting process read
    assert _effort(cfg) == "low"
    assert _effort(cfg, "kimi-code/k3") == "max"          # other models untouched


def test_review_start_sees_high_and_leaves_low_behind(monkeypatch, tmp_path):
    cfg = _patch(monkeypatch, tmp_path, "low")
    seen = tmp_path / "seen"
    probe = [sys.executable, "-c", f"import shutil; shutil.copy({str(cfg)!r}, {str(seen)!r})"]
    runner.launch_with_effort(kimi_review.REVIEW_MODEL, kimi_review.REVIEW_EFFORT, probe).wait()
    assert _effort(seen) == "high"
    assert _effort(cfg) == "low"                          # execution default restored


def test_unknown_model_block_refuses_to_start(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path, "low")
    try:
        runner.launch_with_effort("kimi-code/absent", "low", [sys.executable, "-c", "pass"])
    except RuntimeError as exc:
        assert "no default_effort" in str(exc)
    else:
        raise AssertionError("started at an unknown effort")
