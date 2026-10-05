"""test_e6_emit_gaps_withholding.py — SS ruling N-100: the withholding list enforced INSIDE emit_gaps.

`asset_census.emit_gaps_summary` (the one ledger writer; `emit_gaps` is its tuple wrapper; `main --emit-gaps` calls it)
used to be able to write a CLOSED (credit) row for a WITHHELD (asset, criterion) cell directly, bypassing the E5.2 fold
script (which strips withheld cells BEFORE calling it). The rule is now enforced where the rows are written:

  * a cell whose gap id `<asset>-<criterion>` is an entry of `CTRL/NIKASHA_WITHHOLDING.json` gets NO row of any kind
    (no OPEN, no RE-OPEN, no CLOSED credit), even when it now reads PASS/N-A and an OPEN row exists;
  * an ABSENT file changes nothing (the summary is byte-for-byte the old dict);
  * a PRESENT file that is malformed / not a regular file / untracked / not at HEAD / different from HEAD in content, mode
    or index, or a TRACKED file missing from the work tree, REFUSES the emit (WithholdingRefused) before the ledger is
    opened: the ledger stays byte-identical;
  * a scoped run applies the same filter; a census the fold already filtered gives the same ledger (idempotent).

Every guard has a mutation test: the real source is mutated textually (one change each, asserted to apply exactly once),
loaded as a throwaway module, and the scenario that pins that guard must FAIL on the mutant while a baseline scenario
still passes on it (so the mutant is alive, not merely broken).

Run: cd platform/scripts/governance && python3 -m pytest __tests__/test_e6_emit_gaps_withholding.py -q
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import types

import pytest

pytestmark = pytest.mark.skip(reason="the per-criterion certificate ceremony was dropped by owner decision N-152; the code stays in the repo, its tests are not run in CI")

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
sys.path.insert(0, str(GOV))

import asset_census as ac  # noqa: E402

SRC_PATH = GOV / "asset_census.py"
SRC = SRC_PATH.read_text(encoding="utf-8")

WH_REL = "00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json"
GAPS_REL = "00_ARCHITECTURE/control/asset_gaps.jsonl"
W_ASSET, W_CRIT = "bo_upaya", "Idem.pattern"
W_ID = f"{W_ASSET}-{W_CRIT}"
O_ASSET, O_CRIT = "bo_other", "Build.dag"          # an unwithheld cell
O_ID = f"{O_ASSET}-{O_CRIT}"


# ───────────────────────────── fixtures / helpers ─────────────────────────────

def _entry(asset=W_ASSET, crit=W_CRIT, **over):
    e = dict(asset=asset, criterion=crit, register_row="R244", reason="unearned PASS", condition="lifts on an SS decision",
             decided_by="test")
    e.update(over)
    return e


def wh_text(entries=None, **top) -> str:
    entries = {W_ID: _entry()} if entries is None else entries
    d = dict(version=1, doc="test", entries=entries)
    d.update(top)
    return json.dumps(d, indent=2) + "\n"


def _row(gid, state="OPEN", **kw):
    asset, crit = gid.split("-", 1)
    r = dict(asset=asset, gap_id=gid, kind="gap", criterion=crit, what="w", change="", detector="d", owner="asset_census",
             gate="this asset's certification", state=state, ts="t0")
    r.update(kw)
    return r


def _git(cwd, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        *args], capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr}")
    return p


class Env:
    """A temp git repo whose control dir holds the ledger and (optionally) the withholding file."""

    def __init__(self, tmp, *, rows=(), wh=None, commit=True, track_wh=True):
        self.repo = pathlib.Path(tmp) / "repo"
        self.ctrl = self.repo / "00_ARCHITECTURE" / "control"
        self.ctrl.mkdir(parents=True)
        self.gaps = self.ctrl / "asset_gaps.jsonl"
        self.wh = self.ctrl / "NIKASHA_WITHHOLDING.json"
        self.gaps.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        _git(self.repo, "init", "-q")
        if wh is not None:
            self.wh.write_text(wh, encoding="utf-8")
        _git(self.repo, "add", GAPS_REL)
        if wh is not None and track_wh:
            _git(self.repo, "add", WH_REL)
        if commit:
            _git(self.repo, "commit", "-q", "-m", "base")

    def commit_all(self):
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "more")

    def ledger(self) -> bytes:
        return self.gaps.read_bytes()


def census(cells, scope=None):
    """cells: [(asset, crit, verdict)] -> a layer census."""
    by: dict = {}
    for a, c, v in cells:
        by.setdefault(a, {})[c] = dict(v=v, measured=f"m-{v}")
    c = dict(layer="L0", assets=[dict(asset_id=a, measurements=m) for a, m in by.items()])
    if scope is not None:
        c["scope"] = dict(assets=list(scope), partial=True, layers=["L0"])
    return c


class use_ctrl:
    def __init__(self, m, path, root=None):
        self.m, self.path, self.root = m, path, root

    def __enter__(self):
        self.old = self.m.CTRL, self.m.ROOT
        self.m.CTRL = pathlib.Path(self.path)
        if self.root is not None:
            self.m.ROOT = pathlib.Path(self.root)        # the "canonical" control dir is ROOT/00_ARCHITECTURE/control

    def __exit__(self, *a):
        self.m.CTRL, self.m.ROOT = self.old


@pytest.fixture(scope="module")
def real():
    return ac


def refuses(m, env, code, cen=None):
    """True iff emit_gaps_summary raises m.WithholdingRefused(code) AND the ledger is byte-identical afterwards."""
    cen = cen or census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)])
    before = env.ledger()
    with use_ctrl(m, env.ctrl, root=env.repo):
        try:
            m.emit_gaps_summary(cen)
        except m.WithholdingRefused as e:
            return e.code == code and env.ledger() == before
        except Exception:  # noqa: BLE001 — any other failure is not the guard
            return False
    return False


def proceeds(m, env, cen=None):
    with use_ctrl(m, env.ctrl, root=env.repo):
        return m.emit_gaps_summary(cen or census([(O_ASSET, O_CRIT, m.PASS)]))


# ───────────────────────────── scenarios (module-parametrised: real or mutant) ─────────────────────────────

def sc_baseline(m, tmp):
    """A valid tracked+clean list; an UNWITHHELD cell is still closed by measurement (the mutant is alive)."""
    env = Env(tmp, rows=[_row(O_ID)], wh=wh_text())
    out = proceeds(m, env)
    rows = [json.loads(x) for x in env.ledger().decode().splitlines()]
    return out["closed"] == 1 and rows[-1]["gap_id"] == O_ID and rows[-1]["state"] == "CLOSED"


def sc_withheld_pass_no_credit(m, tmp):
    env = Env(tmp, rows=[_row(W_ID), _row(O_ID)], wh=wh_text())
    before = env.ledger()
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)]))
    new = env.ledger()[len(before):].decode()
    return (new.count("\n") == 1 and O_ID in new and W_ID not in new and out["closed"] == 1
            and out["withheld"] == [W_ID] and env.ledger().startswith(before))


def sc_withheld_fail_no_open(m, tmp):
    env = Env(tmp, rows=[], wh=wh_text())
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.FAIL)]))
    return env.ledger() == b"" and out["added"] == 0 and out["withheld"] == [W_ID]


def sc_withheld_fail_no_reopen(m, tmp):
    env = Env(tmp, rows=[_row(W_ID, "CLOSED")], wh=wh_text())
    before = env.ledger()
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.FAIL)]))
    return env.ledger() == before and out["reopened"] == 0


def sc_withheld_info_family_precedence(m, tmp):
    """Precedence with E6.4: a withheld cell on an info-only family (Count.*) is reported as WITHHELD, not as
    info_only_suppressed; an unwithheld info-family FAIL is still counted as info_only_suppressed."""
    wh = wh_text({"bo_upaya-Count.floor": _entry(crit="Count.floor")})
    env = Env(tmp, rows=[], wh=wh)
    before = env.ledger()
    out = proceeds(m, env, census([(W_ASSET, "Count.floor", m.FAIL), (W_ASSET, "Cost.baseline", m.FAIL)]))
    return (env.ledger() == before and out["withheld"] == ["bo_upaya-Count.floor"]
            and out.get("info_only_suppressed") == 1 and out["added"] == 0 and "withheld_unmatched" not in out)


def sc_summary_key_only_with_list(m, tmp):
    env = Env(tmp, rows=[_row(O_ID)], wh=wh_text({}))
    return "withheld" not in proceeds(m, env)


def sc_absent_unchanged(m, tmp):
    env = Env(tmp, rows=[_row(W_ID), _row(O_ID)], wh=None)
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)]))
    return out == dict(added=0, skipped=0, closed=2, reopened=0, retired_opportunity_rows_left=0)


def sc_absent_no_git(m, tmp):
    d = pathlib.Path(tmp) / "plain"
    d.mkdir(parents=True)
    (d / "asset_gaps.jsonl").write_text(json.dumps(_row(O_ID)) + "\n", encoding="utf-8")
    with use_ctrl(m, d):
        out = m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))
    return out["closed"] == 1


def sc_scoped_filter(m, tmp):
    env = Env(tmp, rows=[_row(W_ID), _row(O_ID)], wh=wh_text())
    before = env.ledger()
    cen = census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)], scope=[W_ASSET, O_ASSET])
    with use_ctrl(m, env.ctrl, root=env.repo):
        out = m.emit_gaps_summary(cen, assets=[W_ASSET])           # scoped to the withheld asset only
    ok1 = env.ledger() == before and out["closed"] == 0 and out["withheld"] == [W_ID]
    with use_ctrl(m, env.ctrl, root=env.repo):
        out = m.emit_gaps_summary(cen)                             # label-scoped (both assets)
    new = env.ledger()[len(before):].decode()
    return ok1 and out["withheld"] == [W_ID] and O_ID in new and W_ID not in new


def sc_double_filter_idempotent(m, tmp):
    full = census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)])
    pre = census([(O_ASSET, O_CRIT, m.PASS)])                     # what the fold hands emit_gaps_summary
    e1 = Env(pathlib.Path(tmp) / "a", rows=[_row(W_ID), _row(O_ID)], wh=wh_text())
    e2 = Env(pathlib.Path(tmp) / "b", rows=[_row(W_ID), _row(O_ID)], wh=wh_text())
    with use_ctrl(m, e1.ctrl):
        o1 = m.emit_gaps_summary(full)
    with use_ctrl(m, e2.ctrl):
        o2 = m.emit_gaps_summary(pre)
    strip = lambda b: [{k: v for k, v in json.loads(x).items() if k != "ts"} for x in b.decode().splitlines()]  # noqa: E731
    same = strip(e1.ledger()) == strip(e2.ledger()) and o1["closed"] == o2["closed"] == 1
    b = e1.ledger()
    with use_ctrl(m, e1.ctrl):
        m.emit_gaps_summary(full)
        m.emit_gaps_summary(pre)
    return same and e1.ledger() == b


def sc_untracked(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text(), track_wh=False)
    return refuses(m, env, "withholding_untracked")


def sc_dirty_content(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    env.wh.write_text(wh_text({}), encoding="utf-8")               # lifts the withholding in the work tree only
    return refuses(m, env, "withholding_dirty")


def sc_dirty_staged_only(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    env.wh.write_text(wh_text({}), encoding="utf-8")
    _git(env.repo, "add", WH_REL)                                  # index == work tree, both differ from HEAD
    return refuses(m, env, "withholding_dirty")


def sc_dirty_mode_only(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    os.chmod(env.wh, 0o755)                                        # bytes equal HEAD; only `git diff HEAD` sees the mode
    return refuses(m, env, "withholding_dirty")


def sc_dirty_hidden_by_assume_unchanged(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    _git(env.repo, "update-index", "--assume-unchanged", WH_REL)
    env.wh.write_text(wh_text({}), encoding="utf-8")               # git diff reports clean; the bytes differ from HEAD
    return refuses(m, env, "withholding_dirty")


def sc_no_head(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text(), commit=False)  # tracked (index) but no commit at all
    return refuses(m, env, "withholding_not_at_head")


def sc_not_in_git(m, tmp):
    d = pathlib.Path(tmp) / "plain"
    d.mkdir(parents=True)
    (d / "asset_gaps.jsonl").write_text(json.dumps(_row(W_ID)) + "\n", encoding="utf-8")
    (d / "NIKASHA_WITHHOLDING.json").write_text(wh_text(), encoding="utf-8")
    before = (d / "asset_gaps.jsonl").read_bytes()
    with use_ctrl(m, d):
        try:
            m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS)]))
        except m.WithholdingRefused as e:
            return e.code == "withholding_not_in_git" and (d / "asset_gaps.jsonl").read_bytes() == before
        except Exception:  # noqa: BLE001
            return False
    return False


def sc_deleted_tracked(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    env.wh.unlink()                                                # a deleted list must not lift every withholding
    return refuses(m, env, "withholding_deleted")


def sc_deleted_staged_never_committed(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text(), track_wh=False)   # HEAD has the ledger only
    _git(env.repo, "add", WH_REL)                                      # the list is in the index, never committed
    env.wh.unlink()
    return refuses(m, env, "withholding_deleted")


def sc_deleted_via_git_rm(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    _git(env.repo, "rm", "-q", WH_REL)                                 # deleted in work tree AND index; HEAD still has it
    return refuses(m, env, "withholding_deleted")


def _with_no_git(tmp, fn):
    old = os.environ.get("PATH")
    os.environ["PATH"] = str(pathlib.Path(tmp) / "empty-bin")      # git cannot be found
    try:
        return fn()
    finally:
        os.environ["PATH"] = old


def sc_absent_git_unavailable(m, tmp):
    """F3: no list file at all, git cannot answer, and CTRL sits inside a checkout: refuse (a deleted tracked list is
    indistinguishable from a never-existing one without git)."""
    env = Env(tmp, rows=[_row(O_ID)], wh=None)
    return _with_no_git(tmp, lambda: refuses(m, env, "withholding_git_unavailable", census([(O_ASSET, O_CRIT, m.PASS)])))


def sc_absent_git_unavailable_deleted_tracked(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    env.wh.unlink()                                                # tracked list deleted, and git cannot say so
    return _with_no_git(tmp, lambda: refuses(m, env, "withholding_git_unavailable"))


def sc_absent_git_unavailable_outside_checkout(m, tmp):
    d = pathlib.Path(tmp) / "plain"
    d.mkdir(parents=True)
    (d / "asset_gaps.jsonl").write_text(json.dumps(_row(O_ID)) + "\n", encoding="utf-8")

    def go():
        with use_ctrl(m, d):
            return m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))["closed"] == 1
    return _with_no_git(tmp, go)


def sc_absent_broken_git(m, tmp):
    """A `.git` entry git cannot read: rev-parse fails inside a checkout, so "not a repository" is not the answer."""
    d = pathlib.Path(tmp) / "broken"
    d.mkdir(parents=True)
    (d / ".git").write_text("gitdir: /nonexistent/nowhere\n", encoding="utf-8")
    (d / "asset_gaps.jsonl").write_text(json.dumps(_row(O_ID)) + "\n", encoding="utf-8")
    before = (d / "asset_gaps.jsonl").read_bytes()
    with use_ctrl(m, d):
        try:
            m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))
        except m.WithholdingRefused as e:
            return e.code == "withholding_git_unavailable" and (d / "asset_gaps.jsonl").read_bytes() == before
        except Exception:  # noqa: BLE001
            return False
    return False


def sc_symlink(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    real_file = env.ctrl / "elsewhere.json"
    real_file.write_text(wh_text(), encoding="utf-8")
    env.wh.unlink()
    env.wh.symlink_to(real_file)
    return refuses(m, env, "withholding_not_regular_file")


def sc_directory(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=None)
    env.wh.mkdir()
    return refuses(m, env, "withholding_not_regular_file")


def sc_unreadable(m, tmp):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return True                                                # root reads anything: nothing to test
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    os.chmod(env.wh, 0o000)
    try:
        return refuses(m, env, "withholding_unreadable")
    finally:
        os.chmod(env.wh, 0o644)


def sc_git_unavailable_present(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    old = os.environ.get("PATH")
    os.environ["PATH"] = str(pathlib.Path(tmp) / "empty-bin")      # git cannot be found
    try:
        return refuses(m, env, "withholding_git_unavailable")
    finally:
        os.environ["PATH"] = old


# ── F1: a relocated ledger that is a link to the canonical one is still governed ──

def _reloc(tmp, name):
    d = pathlib.Path(tmp) / name
    d.mkdir(parents=True)
    return d


def sc_symlinked_ledger_governed(m, tmp):
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(W_ID), _row(O_ID)], wh=wh_text())
    d = _reloc(tmp, "reloc")
    os.symlink(env.gaps, d / "asset_gaps.jsonl")
    before = env.ledger()
    with use_ctrl(m, d):
        out = m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS), (O_ASSET, O_CRIT, m.PASS)]))
    new = env.ledger()[len(before):].decode()
    return out["withheld"] == [W_ID] and out["closed"] == 1 and O_ID in new and W_ID not in new and env.ledger().startswith(before)


def sc_symlinked_ledger_dirty_canonical_list_refuses(m, tmp):
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(W_ID)], wh=wh_text())
    env.wh.write_text(wh_text({}), encoding="utf-8")           # the canonical list is dirty: same fail-closed rules there
    d = _reloc(tmp, "reloc")
    os.symlink(env.gaps, d / "asset_gaps.jsonl")
    before = env.ledger()
    with use_ctrl(m, d):
        try:
            m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS)]))
        except m.WithholdingRefused as e:
            return e.code == "withholding_dirty" and env.ledger() == before
        except Exception:  # noqa: BLE001
            return False
    return False


def sc_symlinked_dir_governed(m, tmp):
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(W_ID)], wh=wh_text())
    link = pathlib.Path(tmp) / "linkdir"
    os.symlink(env.ctrl, link)
    before = env.ledger()
    with use_ctrl(m, link):
        out = m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS)]))
    return out["withheld"] == [W_ID] and env.ledger() == before


def sc_hardlinked_ledger_refused(m, tmp):
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(W_ID)], wh=wh_text())
    d = _reloc(tmp, "reloc")
    os.link(env.gaps, d / "asset_gaps.jsonl")
    before = env.ledger()
    with use_ctrl(m, d, root=env.repo):
        try:
            m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS)]))
        except m.WithholdingRefused as e:
            return e.code == "withholding_ledger_hardlinked" and env.ledger() == before
        except Exception:  # noqa: BLE001
            return False
    return False


def sc_hardlinked_ledger_without_canonical_list_allowed(m, tmp):
    """Nothing to bypass when the canonical list does not exist (the state of main before #3012)."""
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(O_ID)], wh=None)
    d = _reloc(tmp, "reloc")
    os.link(env.gaps, d / "asset_gaps.jsonl")
    with use_ctrl(m, d, root=env.repo):
        return m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))["closed"] == 1


def sc_plain_copy_allowed(m, tmp):
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(O_ID)], wh=wh_text())
    d = _reloc(tmp, "reloc")
    (d / "asset_gaps.jsonl").write_bytes(env.ledger())         # a COPY is a separate ledger: allowed by design
    before = env.ledger()
    with use_ctrl(m, d, root=env.repo):
        out = m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))
    return out["closed"] == 1 and env.ledger() == before


def sc_canonical_ledger_with_other_links_allowed(m, tmp):
    """The canonical control dir's own ledger having a second link is not the relocated case."""
    env = Env(pathlib.Path(tmp) / "c", rows=[_row(O_ID)], wh=wh_text())
    os.link(env.gaps, pathlib.Path(tmp) / "backup_link.jsonl")
    with use_ctrl(m, env.ctrl, root=env.repo):
        return m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.PASS)]))["closed"] == 1


# ── F2: a withheld entry that matches nothing is reported; a malformed asset id is refused ──

TYPO = "bo_upayaa-Idem.pattern"


def sc_unmatched_reported(m, tmp):
    wh = wh_text({W_ID: _entry(), TYPO: _entry(asset="bo_upayaa")})
    env = Env(tmp, rows=[_row(W_ID)], wh=wh)
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS)]))
    return out["withheld"] == [W_ID] and out["withheld_unmatched"] == [TYPO]


def sc_unmatched_absent_when_all_match(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    return "withheld_unmatched" not in proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS)]))


def sc_seen_but_not_suppressed_is_not_unmatched(m, tmp):
    """The cell is measured (verdict NOT_GENERIC: never a transition), so the entry is neither suppressed nor unmatched."""
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.NOT_GENERIC)]))
    return out["withheld"] == [] and "withheld_unmatched" not in out


def sc_unmatched_scoped(m, tmp):
    wh = wh_text({W_ID: _entry(), O_ID: _entry(asset=O_ASSET, crit=O_CRIT)})
    env = Env(tmp, rows=[], wh=wh)
    cen = census([(W_ASSET, W_CRIT, m.PASS)], scope=[W_ASSET])
    with use_ctrl(m, env.ctrl, root=env.repo):
        out = m.emit_gaps_summary(cen)                          # O_ASSET is outside the scope: not a typo, not reported
    cen2 = census([(W_ASSET, "Build.dag", m.PASS)], scope=[W_ASSET])
    with use_ctrl(m, env.ctrl, root=env.repo):
        out2 = m.emit_gaps_summary(cen2)                        # in scope but its criterion was not measured: reported
    return "withheld_unmatched" not in out and out2["withheld_unmatched"] == [W_ID]


def sc_asset_case_variant_refused(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text({"BO_UPAYA-Idem.pattern": _entry(asset="BO_UPAYA")}))
    return refuses(m, env, "withholding_unknown_asset")


def sc_asset_unknown_layer_refused(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text({"zz_upaya-Idem.pattern": _entry(asset="zz_upaya")}))
    return refuses(m, env, "withholding_unknown_asset")


def sc_asset_non_identifier_refused(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text({"bo_up aya-Idem.pattern": _entry(asset="bo_up aya")}))
    return refuses(m, env, "withholding_unknown_asset")


# ── F4: the fold's nesting-depth limit ──

def _nested(n, extra_key="x"):
    return '{"version": 1, "entries": {}, "%s": %s1%s}' % (extra_key, "[" * n, "]" * n)


def _deep_case(n):
    def _sc(m, tmp):
        env = Env(tmp, rows=[_row(W_ID)], wh=_nested(n))
        return refuses(m, env, "withholding_malformed")
    _sc.__name__ = f"sc_depth_{n}_refused"
    return _sc


def sc_depth_64_accepted(m, tmp):
    env = Env(tmp, rows=[_row(O_ID)], wh=_nested(63))           # top object + 63 arrays = depth 64 = the limit
    return proceeds(m, env)["closed"] == 1


def sc_depth_string_brackets_ignored(m, tmp):
    doc = '{"version": 1, "entries": {}, "x": "%s", "y": "q\\"%s"}' % ("[" * 200, "[" * 200)
    env = Env(tmp, rows=[_row(O_ID)], wh=doc)
    return proceeds(m, env)["closed"] == 1


def sc_recursion_error_is_a_refusal(m, tmp):
    """Even when the depth pre-check lets a pathologically nested file through, json's RecursionError is a refusal."""
    old = m._wh_max_depth
    m._wh_max_depth = lambda text: 0
    try:
        env = Env(tmp, rows=[_row(W_ID)], wh=_nested(100000))
        return refuses(m, env, "withholding_malformed")
    finally:
        m._wh_max_depth = old


# ── the git-environment scrub ──

def sc_git_env_scrubbed(m, tmp):
    """GIT_DIR / GIT_WORK_TREE in the caller's environment must not redirect the reader to another repository."""
    other = pathlib.Path(tmp) / "other"
    other.mkdir(parents=True)
    _git(other, "init", "-q")
    env = Env(pathlib.Path(tmp) / "e", rows=[_row(W_ID)], wh=wh_text())
    bad = Env(pathlib.Path(tmp) / "b", rows=[_row(W_ID)], wh=wh_text())
    bad.wh.write_text(wh_text({}), encoding="utf-8")            # dirty: must still be refused
    saved = {k: os.environ.get(k) for k in ("GIT_DIR", "GIT_WORK_TREE")}
    os.environ["GIT_DIR"] = str(other / ".git")
    os.environ["GIT_WORK_TREE"] = str(other)
    try:
        ok = proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS)]))["withheld"] == [W_ID]
        return ok and refuses(m, bad, "withholding_dirty")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def sc_staged_edit_reverted_worktree_honours_head(m, tmp):
    """A staged weakening whose work tree is reverted to HEAD's bytes is not an edit the reader can see: HEAD's list rules."""
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    good = env.wh.read_bytes()
    env.wh.write_text(wh_text({}), encoding="utf-8")
    _git(env.repo, "add", WH_REL)
    env.wh.write_bytes(good)
    before = env.ledger()
    out = proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS)]))
    return out["withheld"] == [W_ID] and env.ledger() == before


def sc_toplevel_elsewhere(m, tmp):
    """core.worktree points git's work tree away from the control dir: the list cannot be located in that tree."""
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    elsewhere = pathlib.Path(tmp) / "elsewhere"
    elsewhere.mkdir()
    _git(env.repo, "config", "core.worktree", str(elsewhere))
    return refuses(m, env, "withholding_not_in_git")


def sc_git_unavailable_present_outside_checkout(m, tmp):
    d = pathlib.Path(tmp) / "plain"
    d.mkdir(parents=True)
    (d / "asset_gaps.jsonl").write_text(json.dumps(_row(W_ID)) + "\n", encoding="utf-8")
    (d / "NIKASHA_WITHHOLDING.json").write_text(wh_text(), encoding="utf-8")
    before = (d / "asset_gaps.jsonl").read_bytes()

    def go():
        with use_ctrl(m, d):
            try:
                m.emit_gaps_summary(census([(W_ASSET, W_CRIT, m.PASS)]))
            except m.WithholdingRefused as e:
                return e.code == "withholding_git_unavailable" and (d / "asset_gaps.jsonl").read_bytes() == before
            except Exception:  # noqa: BLE001
                return False
        return False
    return _with_no_git(tmp, go)


def sc_no_ledger_yet_relocated(m, tmp):
    """A relocated control dir with no ledger file yet (the append creates it) is not a hard-link case."""
    env = Env(pathlib.Path(tmp) / "c", rows=[], wh=wh_text())
    d = _reloc(tmp, "reloc")
    with use_ctrl(m, d, root=env.repo):
        out = m.emit_gaps_summary(census([(O_ASSET, O_CRIT, m.FAIL)]))
    return out["added"] == 1 and (d / "asset_gaps.jsonl").exists()


def sc_depth_siblings_accepted(m, tmp):
    doc = '{"version": 1, "entries": {}, "x": [%s]}' % ",".join(["[]"] * 200)
    env = Env(tmp, rows=[_row(O_ID)], wh=doc)
    return proceeds(m, env)["closed"] == 1


MALFORMED = {
    "not_json": "{ nope",
    "dup_key": '{"version": 1, "entries": {}, "entries": {}}',
    "nan": '{"version": 1, "entries": {}, "x": NaN}',
    "not_object": "[1]",
    "bad_version": json.dumps(dict(version=2, entries={})),
    "entries_list": json.dumps(dict(version=1, entries=[])),
    "entry_not_object": json.dumps(dict(version=1, entries={W_ID: 1})),
    "no_asset": json.dumps(dict(version=1, entries={"None-None": _entry(asset=None, crit=None)})),   # key agrees with the null fields
    "empty_asset": json.dumps(dict(version=1, entries={W_ID: _entry(asset="")})),
    "key_mismatch": json.dumps(dict(version=1, entries={"bo_upaya-Build.dag": _entry()})),
    "unknown_criterion": json.dumps(dict(version=1, entries={"bo_upaya-Zzz.nope": _entry(crit="Zzz.nope")})),
    "retired_criterion": json.dumps(dict(version=1, entries={"bo_upaya-Carr.detector": _entry(crit="Carr.detector")})),
    "no_reason": json.dumps(dict(version=1, entries={W_ID: _entry(reason=" ")})),
    "no_condition": json.dumps(dict(version=1, entries={W_ID: _entry(condition=None)})),
    "no_decided_by": json.dumps(dict(version=1, entries={W_ID: _entry(decided_by=5)})),
    "bad_register_row": json.dumps(dict(version=1, entries={W_ID: _entry(register_row="244")})),
}
MALFORMED_CODE = {"unknown_criterion": "withholding_unknown_criterion", "retired_criterion": "withholding_unknown_criterion"}


def sc_malformed(name):
    def _sc(m, tmp):
        env = Env(tmp, rows=[_row(W_ID)], wh=MALFORMED[name])      # committed and clean: only the content is bad
        return refuses(m, env, MALFORMED_CODE.get(name, "withholding_malformed"))
    return _sc


def sc_valid_no_register_row(m, tmp):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text({W_ID: {k: v for k, v in _entry().items() if k != "register_row"}}))
    return proceeds(m, env, census([(W_ASSET, W_CRIT, m.PASS)]))["withheld"] == [W_ID]


# ───────────────────────────── behaviour tests (real module) ─────────────────────────────

POSITIVE = [sc_baseline, sc_withheld_info_family_precedence, sc_withheld_pass_no_credit, sc_withheld_fail_no_open, sc_withheld_fail_no_reopen,
            sc_summary_key_only_with_list, sc_absent_unchanged, sc_absent_no_git, sc_absent_git_unavailable_outside_checkout, sc_scoped_filter,
            sc_double_filter_idempotent, sc_valid_no_register_row,
            sc_symlinked_ledger_governed, sc_symlinked_dir_governed, sc_hardlinked_ledger_without_canonical_list_allowed,
            sc_plain_copy_allowed, sc_canonical_ledger_with_other_links_allowed, sc_unmatched_reported,
            sc_unmatched_absent_when_all_match, sc_seen_but_not_suppressed_is_not_unmatched, sc_unmatched_scoped,
            sc_depth_64_accepted, sc_depth_string_brackets_ignored, sc_depth_siblings_accepted, sc_no_ledger_yet_relocated, sc_git_env_scrubbed,
            sc_staged_edit_reverted_worktree_honours_head]
REFUSALS = [sc_untracked, sc_dirty_content, sc_dirty_staged_only, sc_dirty_mode_only, sc_dirty_hidden_by_assume_unchanged,
            sc_no_head, sc_not_in_git, sc_deleted_tracked, sc_deleted_staged_never_committed, sc_deleted_via_git_rm, sc_symlink, sc_directory,
            sc_unreadable, sc_git_unavailable_present, sc_absent_git_unavailable, sc_absent_git_unavailable_deleted_tracked,
            sc_absent_broken_git, sc_git_unavailable_present_outside_checkout, sc_toplevel_elsewhere, sc_symlinked_ledger_dirty_canonical_list_refuses, sc_hardlinked_ledger_refused,
            sc_asset_case_variant_refused, sc_asset_unknown_layer_refused, sc_asset_non_identifier_refused,
            sc_recursion_error_is_a_refusal] + [_deep_case(n) for n in (64, 69, 5000)] + [sc_malformed(n) for n in MALFORMED]


@pytest.mark.parametrize("sc", POSITIVE, ids=lambda f: f.__name__)
def test_scenario_holds_on_real_module(sc, tmp_path):
    assert sc(ac, tmp_path) is True


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_malformed_list_refuses_and_ledger_is_byte_identical(name, tmp_path):
    assert sc_malformed(name)(ac, tmp_path) is True


@pytest.mark.parametrize("sc", [f for f in REFUSALS if f.__name__ != "_sc"], ids=lambda f: f.__name__)
def test_unprovable_list_refuses_and_ledger_is_byte_identical(sc, tmp_path):
    assert sc(ac, tmp_path) is True


def test_withheld_close_via_tuple_wrapper_is_also_suppressed(tmp_path):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text())
    before = env.ledger()
    with use_ctrl(ac, env.ctrl):
        assert ac.emit_gaps(census([(W_ASSET, W_CRIT, ac.PASS)])) == (0, 0, 0, 0)
    assert env.ledger() == before


def test_withheld_na_cell_is_not_credited_either(tmp_path):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text())
    before = env.ledger()
    cen = census([(W_ASSET, W_CRIT, ac.NA)])
    with use_ctrl(ac, env.ctrl):
        out = ac.emit_gaps_summary(cen)
    assert env.ledger() == before and out["withheld"] == [W_ID]


def test_withheld_superseded_id_still_gets_nothing(tmp_path):
    env = Env(tmp_path, rows=[_row(W_ID, superseded_by="x")], wh=wh_text())
    before = env.ledger()
    with use_ctrl(ac, env.ctrl):
        ac.emit_gaps_summary(census([(W_ASSET, W_CRIT, ac.PASS)]))
    assert env.ledger() == before


def test_a_lifted_entry_resumes_normal_closure(tmp_path):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text())
    env.wh.write_text(wh_text({}), encoding="utf-8")
    env.commit_all()                                               # the reviewed lift is a committed change
    with use_ctrl(ac, env.ctrl):
        out = ac.emit_gaps_summary(census([(W_ASSET, W_CRIT, ac.PASS)]))
    assert out["closed"] == 1 and "withheld" not in out


def test_withholding_never_touches_retired_criterion_closure(tmp_path):
    """RETIRED criteria are not registry criteria, so they cannot be withheld (validator) and retirement closure is unchanged."""
    rid = "bo_x-Carr.detector"
    env = Env(tmp_path, rows=[_row(rid)], wh=wh_text())
    with use_ctrl(ac, env.ctrl):
        out = ac.emit_gaps_summary(census([(O_ASSET, O_CRIT, ac.PASS)]))
    assert out["closed"] == 1 and json.loads(env.ledger().decode().splitlines()[-1])["closed_by"] == "retirement"


def test_refusal_happens_before_the_ledger_is_even_created(tmp_path):
    env = Env(tmp_path, rows=[], wh="{ nope")
    env.gaps.unlink()
    _git(env.repo, "rm", "-q", "--cached", GAPS_REL)
    with use_ctrl(ac, env.ctrl), pytest.raises(ac.WithholdingRefused):
        ac.emit_gaps_summary(census([(W_ASSET, W_CRIT, ac.FAIL)]))
    assert not env.gaps.exists()


# ───────────────────────────── CLI (`--emit-gaps`) ─────────────────────────────

def _stub_main(monkeypatch, env, cen, m=ac):
    out = pathlib.Path(env.repo) / "census_out.json"
    monkeypatch.setattr(m, "CTRL", env.ctrl)
    full = dict(cen, layer_name="Stub", scoring="fidelity", n_assets=len(cen["assets"]), registered_ids=0, registry_has_writer=0,
                population_active=len(cen["assets"]), population_registry_total=len(cen["assets"]), population_excluded_inactive=[],
                never_exercised_with_writer=[], phantom_registered=[], global_runs=0, global_runs_touching_layer=0, generated="t")
    called = []
    monkeypatch.setattr(m, "measure", lambda k, **kw: (called.append(k), dict(full))[1])
    monkeypatch.setattr(m, "census_stamp", lambda: {})
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--emit-gaps", "--out", str(out)])
    return out, called


def test_cli_emit_gaps_reports_withheld_and_writes_no_credit(monkeypatch, tmp_path, capsys):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text())
    before = env.ledger()
    out, _ = _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, ac.PASS)]))
    assert ac.main() == 0
    assert env.ledger() == before
    assert f"WITHHELD (no row of any kind written): {W_ID}" in capsys.readouterr().out


def sc_cli_refusal(m, tmp, monkeypatch):
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text(), track_wh=False)
    before = env.ledger()
    out, called = _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, m.PASS)]))
    rc = m.main()
    return rc == m.EXIT_WITHHOLDING == 7 and env.ledger() == before and not called and not out.exists()


def sc_cli_refusal_in_loop(m, tmp, monkeypatch):
    """The preflight passes, the list then goes bad before the emit (a race): the per-layer emit refuses too, exit 7."""
    env = Env(tmp, rows=[_row(W_ID)], wh=wh_text())
    before = env.ledger()
    out, called = _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, m.PASS)]), m)
    real_load, n = m.load_withholding_entries, []

    def flaky():
        n.append(1)
        if len(n) == 1:
            return {}
        raise m.WithholdingRefused("withholding_dirty", "went bad mid-run")

    monkeypatch.setattr(m, "load_withholding_entries", flaky)
    # emit_gaps_summary calls the module-level name too: the second call (inside it) is the one that raises
    rc = m.main()
    return rc == 7 and env.ledger() == before and bool(called) and not out.exists() and len(n) == 2 and real_load is not flaky


def test_cli_warns_when_an_entry_matches_no_measured_cell(monkeypatch, tmp_path, capsys):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text({W_ID: _entry(), TYPO: _entry(asset="bo_upayaa")}))
    _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, ac.PASS)]))
    assert ac.main() == 0
    out = capsys.readouterr().out
    assert f"WARNING — withholding entr(ies) matched no measured cell of this run" in out and TYPO in out
    assert f"WITHHELD (no row of any kind written): {W_ID}" in out


def test_cli_no_warning_when_every_entry_matched(monkeypatch, tmp_path, capsys):
    env = Env(tmp_path, rows=[_row(W_ID)], wh=wh_text())
    _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, ac.PASS)]))
    assert ac.main() == 0
    assert "WARNING" not in capsys.readouterr().out


def sc_cli_warning(m, tmp, monkeypatch):
    """True iff the unmatched WARNING line is printed exactly when an entry matched nothing."""
    import contextlib
    import io
    buf = io.StringIO()
    env = Env(pathlib.Path(tmp) / "a", rows=[_row(W_ID)], wh=wh_text({W_ID: _entry(), TYPO: _entry(asset="bo_upayaa")}))
    _stub_main(monkeypatch, env, census([(W_ASSET, W_CRIT, m.PASS)]), m)
    try:
        with contextlib.redirect_stdout(buf):
            m.main()
    except Exception:  # noqa: BLE001 — a mutant that crashes the CLI is a kill
        return False
    env2 = Env(pathlib.Path(tmp) / "b", rows=[_row(W_ID)], wh=wh_text())
    _stub_main(monkeypatch, env2, census([(W_ASSET, W_CRIT, m.PASS)]), m)
    buf2 = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf2):
            m.main()
    except Exception:  # noqa: BLE001
        return False
    return "WARNING" in buf.getvalue() and "WARNING" not in buf2.getvalue()


def test_cli_refuses_with_exit_7_before_measuring(monkeypatch, tmp_path, capsys):
    assert sc_cli_refusal(ac, tmp_path, monkeypatch) is True
    assert "withholding refused" in capsys.readouterr().err


# ───────────────────────────── parity with nikasha_fold.load_withholding (when the fold module exists) ─────────────────────────────

FOLD_PATH = GOV / "nikasha_fold.py"


@pytest.mark.skipif(not FOLD_PATH.is_file(), reason="nikasha_fold.py (E5.2, PR #3012) is not on this checkout yet: parity with its "
                                                     "load_withholding is asserted once it lands")
def test_validator_parity_with_the_fold(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("nikasha_fold_parity", FOLD_PATH)
    fold = importlib.util.module_from_spec(spec)
    sys.modules["nikasha_fold_parity"] = fold
    try:
        spec.loader.exec_module(fold)
    finally:
        sys.modules.pop("nikasha_fold_parity", None)
    cases = dict(MALFORMED)
    cases["valid"] = wh_text()
    cases["valid_empty"] = wh_text({})
    cases["valid_no_register_row"] = wh_text({W_ID: {k: v for k, v in _entry().items() if k != "register_row"}})
    for n in (62, 63, 64, 65, 69, 70, 5000):
        cases[f"depth_{n}_extra"] = _nested(n)
    cases["brackets_in_strings"] = '{"version": 1, "entries": {}, "x": "%s", "y": "q\\"%s"}' % ("[" * 200, "[" * 200)
    cases["many_siblings"] = '{"version": 1, "entries": {}, "x": [%s]}' % ",".join(["[]"] * 200)
    for name, text in cases.items():
        p = tmp_path / f"{name}.json"
        p.write_text(text, encoding="utf-8")
        try:
            want = ("ok", sorted(fold.load_withholding(p)["entries"]))
        except fold.FoldRefused as e:
            want = ("refused", e.code)
        try:
            got = ("ok", sorted(ac._wh_validate(text.encode())))
        except ac.WithholdingRefused as e:
            got = ("refused", e.code)
        assert got == want, f"{name}: asset_census {got} vs fold {want}"


# ───────────────────────────── mutation tests: one per guard ─────────────────────────────

def _mutant(old, new):
    src = SRC
    for o, n in (zip(old, new) if isinstance(old, list) else [(old, new)]):
        assert src.count(o) == 1, f"mutation anchor must match exactly once: {o!r} ({src.count(o)})"
        src = src.replace(o, n)
    m = types.ModuleType("asset_census_mutant")
    m.__file__ = str(SRC_PATH)
    sys.modules["asset_census_mutant"] = m
    try:
        exec(compile(src, str(SRC_PATH), "exec"), m.__dict__)
    finally:
        sys.modules.pop("asset_census_mutant", None)
    return m


def _alive(m, tmp):
    return sc_baseline(m, pathlib.Path(tmp) / "alive") is True


MUTATIONS = {
    # the filter itself
    "filter_off": ("                if gid in withheld:\n                    suppressed.add(gid)\n                    continue",
                   "                if False:\n                    suppressed.add(gid)\n                    continue", [sc_withheld_pass_no_credit]),
    "info_precedence_swapped": ("                if gid in withheld:\n                    suppressed.add(gid)",
                                "                if gid in withheld and not (v in FAILING and crit.startswith(tuple(g + \".\" for g in INFO_ONLY_GATES))):\n                    suppressed.add(gid)",
                                [sc_withheld_info_family_precedence]),
    "filter_no_continue": ("                    suppressed.add(gid)\n                    continue    # N-100",
                           "                    suppressed.add(gid)\n                    pass    # N-100", [sc_withheld_pass_no_credit]),
    "list_not_loaded": ("    withheld = load_withholding_entries()       # N-100",
                        "    withheld = {}       # N-100", [sc_withheld_pass_no_credit, sc_untracked]),
    "summary_key_always": ('    if withheld:\n        out["withheld"]', '    if True:\n        out["withheld"]', [sc_summary_key_only_with_list]),
    "summary_key_never": ('    if withheld:\n        out["withheld"]', '    if False:\n        out["withheld"]', [sc_withheld_pass_no_credit]),
    # absent-file handling
    "absent_refused": ("        return {}                       # absent file, not in a checkout, no git: nothing to prove deleted",
                       "        raise WithholdingRefused('x', 'x')", [sc_absent_git_unavailable_outside_checkout]),
    "absent_not_repo_refused": ("        return {}                       # absent and not a repo: no withholding",
                                "        raise WithholdingRefused('x', 'x')", [sc_absent_no_git]),
    # presence guards
    "git_missing_ignored": ("        if present or _wh_git_ancestor(p.parent):\n            raise  ", "        if False:\n            raise  ", [sc_git_unavailable_present_outside_checkout, sc_absent_git_unavailable]),
    "git_missing_present_dropped": ("        if present or _wh_git_ancestor(p.parent):\n            raise  ", "        if _wh_git_ancestor(p.parent):\n            raise  ", [sc_git_unavailable_present_outside_checkout]),
    "git_missing_ancestor_dropped": ("        if present or _wh_git_ancestor(p.parent):\n            raise  ", "        if present:\n            raise  ", [sc_absent_git_unavailable, sc_absent_git_unavailable_deleted_tracked]),
    "git_rc_ancestor_dropped": ("        if _wh_git_ancestor(p.parent):\n            raise WithholdingRefused(\"withholding_git_unavailable\", \"git cannot answer",
                                "        if False:\n            raise WithholdingRefused(\"withholding_git_unavailable\", \"git cannot answer", [sc_absent_broken_git]),
    "git_ancestor_parents_dropped": ("for q in (real, *real.parents))", "for q in (real,))", [sc_absent_git_unavailable]),
    "git_ancestor_never": ("    return any(os.path.lexists(q / \".git\") for q in (real, *real.parents))", "    return False", [sc_absent_git_unavailable, sc_absent_broken_git]),
    "toplevel_containment_off": ("    if not real_dir.is_relative_to(top):", "    if False:", [sc_toplevel_elsewhere]),
    # F1
    "ledger_realdir_ignored": ("    if real != here:\n        dirs.append(real)", "    if False:\n        dirs.append(real)", [sc_symlinked_ledger_governed, sc_symlinked_ledger_dirty_canonical_list_refuses]),
    "hardlink_guard_off": ("        if nlink > 1:", "        if False:", [sc_hardlinked_ledger_refused]),
    "hardlink_ge1": ("        if nlink > 1:", "        if nlink >= 1:", [sc_plain_copy_allowed]),
    "hardlink_needs_no_canonical_list": ("    if here != canonical and os.path.lexists(canonical / WITHHOLDING_NAME):", "    if here != canonical:", [sc_hardlinked_ledger_without_canonical_list_allowed]),
    "hardlink_applies_to_canonical": ("    if here != canonical and os.path.lexists(canonical / WITHHOLDING_NAME):", "    if os.path.lexists(canonical / WITHHOLDING_NAME):", [sc_canonical_ledger_with_other_links_allowed]),
    "hardlink_missing_ledger_refused": ("            nlink = 1                   # no ledger yet", "            nlink = 2                   # no ledger yet", [sc_no_ledger_yet_relocated]),
    # F2
    "summary_lists_all_entries": ('out["withheld"] = sorted(suppressed)', 'out["withheld"] = sorted(withheld)', [sc_seen_but_not_suppressed_is_not_unmatched, sc_unmatched_reported]),
    "unmatched_never": ("        if unmatched:", "        if False:", [sc_unmatched_reported]),
    "unmatched_always": ("        if unmatched:", "        if True:", [sc_unmatched_absent_when_all_match]),
    "unmatched_seen_not_recorded": ("                seen.add(f\"{a['asset_id']}-{crit}\")\n", "                pass\n", [sc_unmatched_absent_when_all_match]),
    "unmatched_seen_only_if_suppressed": ([ "                seen.add(f\"{a['asset_id']}-{crit}\")\n", "                    suppressed.add(gid)\n"],
                                          ["                pass\n", "                    suppressed.add(gid); seen.add(gid)\n"], [sc_seen_but_not_suppressed_is_not_unmatched]),
    "unmatched_scope_ignored": ('(scope is None or e["asset"] in scope)', "True", [sc_unmatched_scoped]),
    "asset_check_off": ('        if not (_ASSET_ID.fullmatch(asset) and any(asset.startswith(v["prefix"]) for v in LAYERS.values())):', "        if False:",
                        [sc_asset_case_variant_refused, sc_asset_unknown_layer_refused, sc_asset_non_identifier_refused]),
    "asset_format_off": ("_ASSET_ID.fullmatch(asset) and any(", "True and any(", [sc_asset_non_identifier_refused]),
    "asset_prefix_off": ('any(asset.startswith(v["prefix"]) for v in LAYERS.values())', "True", [sc_asset_unknown_layer_refused]),
    # F4
    "depth_check_off": ("    if _wh_max_depth(text) > WH_MAX_JSON_DEPTH:", "    if False:", [_deep_case(64), _deep_case(69)]),
    "depth_off_by_one": ("    if _wh_max_depth(text) > WH_MAX_JSON_DEPTH:", "    if _wh_max_depth(text) >= WH_MAX_JSON_DEPTH:", [sc_depth_64_accepted]),
    "depth_limit_65": ("WH_MAX_JSON_DEPTH = 64 ", "WH_MAX_JSON_DEPTH = 65 ", [_deep_case(64)]),
    "depth_strings_counted": ("        elif ch == '\"':\n            in_str = True", "        elif ch == '\"':\n            in_str = False", [sc_depth_string_brackets_ignored]),
    "depth_escape_ignored": ('            elif ch == "\\\\":\n                esc = True', "            elif False:\n                esc = True", [sc_depth_string_brackets_ignored]),
    "depth_close_ignored": ("            depth -= 1\n    return best", "            pass\n    return best", [sc_depth_siblings_accepted]),
    "recursion_unguarded": ('    except RecursionError as exc:\n        raise ValueError("nesting too deep") from exc', '    except ZeroDivisionError as exc:\n        raise ValueError("nesting too deep") from exc', [sc_recursion_error_is_a_refusal]),
    # git env
    "git_env_not_scrubbed": ("capture_output=True, timeout=30, env=_git_env(), shell=False)", "capture_output=True, timeout=30, shell=False)", [sc_git_env_scrubbed]),
    "not_in_git_ignored": ('        if present:\n            raise WithholdingRefused("withholding_not_in_git", f"{WITHHOLDING_NAME} is present',
                           '        if False:\n            raise WithholdingRefused("withholding_not_in_git", f"{WITHHOLDING_NAME} is present', [sc_not_in_git]),
    "deleted_ignored": ("        if tracked or _wh_git(top, \"cat-file\", \"-e\", f\"HEAD:{rel}\").returncode == 0:",
                        "        if False:", [sc_deleted_tracked]),
    "deleted_index_only_ignored": ("        if tracked or _wh_git(top, \"cat-file\", \"-e\", f\"HEAD:{rel}\").returncode == 0:",
                                  "        if _wh_git(top, \"cat-file\", \"-e\", f\"HEAD:{rel}\").returncode == 0:", [sc_deleted_staged_never_committed]),
    "deleted_head_only_ignored": ("        if tracked or _wh_git(top, \"cat-file\", \"-e\", f\"HEAD:{rel}\").returncode == 0:",
                                 "        if tracked:", [sc_deleted_via_git_rm]),
    "regular_file_ignored": ("    if p.is_symlink() or not p.is_file():", "    if False:", [sc_symlink, sc_directory]),
    "symlink_allowed": ("    if p.is_symlink() or not p.is_file():", "    if not p.is_file():", [sc_symlink]),
    "directory_allowed": ("    if p.is_symlink() or not p.is_file():", "    if p.is_symlink():", [sc_directory]),
    "unreadable_swallowed": ("    except OSError as exc:\n        raise WithholdingRefused(\"withholding_unreadable\"",
                             "    except ZeroDivisionError as exc:\n        raise WithholdingRefused(\"withholding_unreadable\"", [sc_unreadable]),
    "untracked_ignored": ("    if not tracked:\n        raise WithholdingRefused(\"withholding_untracked\"",
                          "    if False:\n        raise WithholdingRefused(\"withholding_untracked\"", [sc_untracked]),
    "head_missing_ignored": ("    if head.returncode != 0:\n        raise WithholdingRefused(\"withholding_not_at_head\"",
                             "    if False:\n        raise WithholdingRefused(\"withholding_not_at_head\"", [sc_no_head]),
    "git_diff_ignored": ("    if _wh_git(top, \"diff\", \"--quiet\", \"HEAD\", \"--\", rel).returncode != 0:", "    if False:", [sc_dirty_mode_only]),
    "git_diff_exit1_only": ("    if _wh_git(top, \"diff\", \"--quiet\", \"HEAD\", \"--\", rel).returncode != 0:",
                            "    if _wh_git(top, \"diff\", \"--quiet\", \"HEAD\", \"--\", rel).returncode == 1000:", [sc_dirty_mode_only]),
    "byte_compare_ignored": ("    if head.stdout != raw:", "    if False:", [sc_dirty_hidden_by_assume_unchanged]),
    # validator
    "not_dict_ignored": ("    if not isinstance(data, dict) or data.get(\"version\") != 1 or not isinstance(data.get(\"entries\"), dict):",
                         "    if False:", [sc_malformed("bad_version"), sc_malformed("entries_list"), sc_malformed("not_object")]),
    "version_ignored": ("data.get(\"version\") != 1 or not isinstance(data.get(\"entries\"), dict):",
                        "False or not isinstance(data.get(\"entries\"), dict):", [sc_malformed("bad_version")]),
    "entries_type_ignored": ("data.get(\"version\") != 1 or not isinstance(data.get(\"entries\"), dict):",
                             "data.get(\"version\") != 1 or False:", [sc_malformed("entries_list")]),
    "dup_keys_allowed": ("            raise ValueError(f\"duplicate object key {k!r}\")", "            pass", [sc_malformed("dup_key")]),
    "nan_allowed": ("    raise ValueError(f\"non-finite constant {c}\")", "    return 0", [sc_malformed("nan")]),
    "json_error_swallowed": ("    except (UnicodeDecodeError, ValueError) as exc:\n        raise WithholdingRefused(\"withholding_malformed\"",
                             "    except UnicodeDecodeError as exc:\n        raise WithholdingRefused(\"withholding_malformed\"", [sc_malformed("not_json")]),
    "entry_type_ignored": ("        if not isinstance(e, dict):\n            raise WithholdingRefused(\"withholding_malformed\", f\"entry {key!r} is not an object\")",
                           "        if False:\n            raise WithholdingRefused(\"withholding_malformed\", f\"entry {key!r} is not an object\")", [sc_malformed("entry_not_object")]),
    "asset_crit_ignored": ("        if not (isinstance(asset, str) and asset and isinstance(crit, str) and crit):",
                           "        if False:", [sc_malformed("no_asset")]),
    "key_mismatch_ignored": ("        if key != f\"{asset}-{crit}\":", "        if False:", [sc_malformed("key_mismatch")]),
    "registry_check_ignored": ("        if crit not in CRITERION_REGISTRY:\n            raise WithholdingRefused(\"withholding_unknown_criterion\"",
                               "        if False:\n            raise WithholdingRefused(\"withholding_unknown_criterion\"",
                               [sc_malformed("unknown_criterion"), sc_malformed("retired_criterion")]),
    "text_fields_ignored": ("            if not (isinstance(e.get(f), str) and e[f].strip()):", "            if False:",
                            [sc_malformed("no_reason"), sc_malformed("no_condition"), sc_malformed("no_decided_by")]),
    "strip_ignored": ("            if not (isinstance(e.get(f), str) and e[f].strip()):", "            if not isinstance(e.get(f), str):", [sc_malformed("no_reason")]),
    "register_row_ignored": ("        if rr is not None and not (isinstance(rr, str) and re.fullmatch(r\"R\\d+\", rr)):", "        if False:",
                             [sc_malformed("bad_register_row")]),
    "register_row_required": ("        if rr is not None and not (isinstance(rr, str) and re.fullmatch(r\"R\\d+\", rr)):",
                              "        if not (isinstance(rr, str) and re.fullmatch(r\"R\\d+\", rr)):", [sc_valid_no_register_row]),
    # CLI
    "cli_exit_code": ("            return EXIT_WITHHOLDING\n\n    stamp = census_stamp()", "            return 0\n\n    stamp = census_stamp()", None),
    "cli_preflight_removed": ("            load_withholding_entries()      # N-100: refuse a bad withholding list before any measuring",
                              "            pass      # N-100", None),
    "cli_warning_dropped": ("            if g.get(\"withheld_unmatched\"):\n", "            if False:\n", "warn"),
    "cli_warning_always": ("            if g.get(\"withheld_unmatched\"):\n", "            if True:\n", "warn"),
    "cli_loop_catch_exit": ("                return EXIT_WITHHOLDING\n            print(f\"  ledger:", "                return 0\n            print(f\"  ledger:", "loop"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_mutation_is_killed(name, tmp_path, monkeypatch):
    old, new, scenarios = MUTATIONS[name]
    m = _mutant(old, new)
    assert _alive(m, tmp_path), f"{name}: the mutant must still pass the baseline (else it is merely broken)"
    if scenarios is None:                                   # the CLI preflight
        assert sc_cli_refusal(m, tmp_path / "cli", monkeypatch) is False
        return
    if scenarios == "warn":                                 # the CLI unmatched warning
        assert sc_cli_warning(m, tmp_path / "cli", monkeypatch) is False
        return
    if scenarios == "loop":                                 # the CLI per-layer catch
        assert sc_cli_refusal_in_loop(m, tmp_path / "cli", monkeypatch) is False
        return
    killed = []
    for i, sc in enumerate(scenarios):
        try:
            ok = sc(m, tmp_path / f"s{i}")
        except Exception:  # noqa: BLE001 — a mutant that breaks the scenario is also a kill
            ok = False
        killed.append(ok is not True)
    assert any(killed), f"{name}: NO scenario failed on the mutant ({[s.__name__ for s in scenarios]})"


def test_cli_refusal_inside_the_layer_loop_is_exit_7_too(monkeypatch, tmp_path):
    assert sc_cli_refusal_in_loop(ac, tmp_path, monkeypatch) is True


def test_every_mutation_scenario_passes_on_the_real_module(tmp_path):
    seen = {}
    for _name, (_o, _n, scs) in MUTATIONS.items():
        for sc in scs if isinstance(scs, list) else ():
            seen[sc.__name__ if sc.__name__ != "_sc" else id(sc)] = sc
    for i, sc in enumerate(seen.values()):
        assert sc(ac, tmp_path / f"r{i}") is True
