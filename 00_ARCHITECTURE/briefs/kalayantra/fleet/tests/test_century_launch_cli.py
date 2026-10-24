"""century_launch.cli's process boundary (SR-J4E-FIX): a named refusal shows its message, every other exception stays type-only.

The incident: the real century_dispatch refused with a precise, id/relation-only reason, and the launcher printed only "century launch failed (Refused)".
Only bridge.Refused (smalltest_launch) and v5_small_test_shared.Refused are shown (their texts are ids/counts/relation names by contract); a connection error
can carry credentials in its text, so any other exception, including one that merely looks like a refusal, prints its type alone."""
import importlib.util
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parents[5] / "platform/scripts"
for folder in (FLEET, SCRIPTS):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import smalltest_launch as bridge  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

SECRET = "postgresql://builder:hunter2-not-a-real-secret@db.example/postgres"


def load_launcher():
    spec = importlib.util.spec_from_file_location("century_launch_under_test", FLEET / "century_launch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_cli(monkeypatch, capsys, exc):
    launcher = load_launcher()

    def boom(argv=None):
        raise exc
    monkeypatch.setattr(launcher, "run", boom)
    code = launcher.cli([])
    return code, capsys.readouterr().err


@pytest.mark.parametrize("refusal", [bridge.Refused, shared.Refused], ids=["bridge.Refused", "shared.Refused"])
def test_a_named_refusal_prints_its_message(monkeypatch, capsys, refusal):
    code, err = run_cli(monkeypatch, capsys, refusal("scoped content could not be measured now: scope relation missing: public.ka_x"))
    assert code == 1
    assert err.strip() == ("century launch refused: scoped content could not be measured now: scope relation missing: public.ka_x; "
                           "reconcile retained evidence, never retry")


@pytest.mark.parametrize("make", [lambda: RuntimeError(SECRET), lambda: type("Refused", (RuntimeError,), {})(SECRET), lambda: OSError(SECRET)],
                         ids=["runtime", "refused-by-name-only", "oserror"])
def test_every_other_exception_prints_only_its_type(monkeypatch, capsys, make):
    exc = make()
    code, err = run_cli(monkeypatch, capsys, exc)
    assert code == 1
    assert err.strip() == f"century launch failed ({type(exc).__name__}); reconcile retained evidence, never retry"
    assert "hunter2" not in err and SECRET not in err
