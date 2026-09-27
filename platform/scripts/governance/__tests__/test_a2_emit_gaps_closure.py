"""test_a2_emit_gaps_closure.py — D4 acceptance cases for the P3 closure loop (Nikaṣa wave 1, Lane A).

D4 ruling (nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md D4, R57 amended): the sandbox port
(`harness/asset_census_closing.py:649-679`) is NOT adopted unchanged — it fails four of six
acceptance cases. Each test below is one of those cases, run against the now-fixed production
`emit_gaps()` (`platform/scripts/governance/asset_census.py`). §N.8: every one of these is a case
that fails against the naive port and passes only because of the specific fix named in its
docstring — see `_naive_port_emit_gaps` at the bottom, which reproduces the sandbox port's actual
logic (not asset_census's) so the six cases can be shown failing under it directly, without
depending on any file outside this repo.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_a2_emit_gaps_closure.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import asset_census  # noqa: E402


def _write_ledger(dir_path: pathlib.Path, rows: list[dict]) -> None:
    p = dir_path / "asset_gaps.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _read_ledger(dir_path: pathlib.Path) -> list[dict]:
    p = dir_path / "asset_gaps.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _census(asset_id: str, crit: str, verdict: str, measured: str = "x") -> dict:
    return dict(layer="L0", assets=[dict(asset_id=asset_id,
                                         measurements={crit: dict(v=verdict, measured=measured)})])


@pytest.fixture()
def ctrl(monkeypatch, tmp_path):
    monkeypatch.setattr(asset_census, "CTRL", tmp_path)
    return tmp_path


# ── Acceptance case 1: CLOSED only on PASS/N-A, never NOT_GENERIC/UNKNOWN/errored/unmeasured ──

def test_case1_not_generic_never_closes_an_open_gap(ctrl):
    """A gap_id open on FAIL must stay open if a later run reports NOT_GENERIC for the same
    criterion — NOT_GENERIC is not a pass, and the naive port's `else: close` branch (anything
    not in the failing tuple closes) would wrongly close it."""
    _write_ledger(ctrl, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
                             what="w", change="", detector="d", owner="asset_census",
                             gate="this asset's certification", state="OPEN", ts="t0")])
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "NOT_GENERIC"))
    assert (added, skipped, closed, reopened) == (0, 0, 0, 0)
    rows = _read_ledger(ctrl)
    assert len(rows) == 1 and rows[0]["state"] == "OPEN", "NOT_GENERIC must never close a gap"


def test_case1_not_generic_never_opens_a_gap_either(ctrl):
    """A criterion that is NOT_GENERIC with no prior row must never create a ledger entry at all —
    it is not a defect, it is an undeclared generic case (CLAUDE.md: 'a prompt for the brief
    author, never a pass')."""
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Complete.width", "NOT_GENERIC"))
    assert (added, skipped, closed, reopened) == (0, 0, 0, 0)
    assert _read_ledger(ctrl) == []


# ── Acceptance case 2: IN_PROGRESS transitions to CLOSED on PASS, exactly like OPEN ──

def test_case2_in_progress_closes_on_pass(ctrl):
    """A hand-annotated IN_PROGRESS row (accepted, being worked) must close on PASS just like an
    OPEN row — the naive port only checked `state == 'OPEN'` and would leave an IN_PROGRESS row
    open forever even after the detector passes."""
    _write_ledger(ctrl, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
                             what="w", change="fix in flight", detector="d", owner="alice",
                             gate="this asset's certification", state="IN_PROGRESS", ts="t0")])
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS", "now clean"))
    assert closed == 1 and added == skipped == reopened == 0
    rows = _read_ledger(ctrl)
    assert rows[-1]["state"] == "CLOSED"
    assert "now clean" in rows[-1]["what"]


# ── Acceptance case 3: a closed row re-opens on regression ──

def test_case3_regression_reopens_a_closed_row(ctrl):
    _write_ledger(ctrl, [
        dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar", what="w",
             change="", detector="d", owner="asset_census", gate="this asset's certification",
             state="OPEN", ts="t0"),
        dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
             what="CLOSED by measurement: fixed", change="", detector="d", owner="asset_census",
             gate="this asset's certification", state="CLOSED", ts="t1"),
    ])
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL", "broke again"))
    assert reopened == 1 and added == skipped == closed == 0
    rows = _read_ledger(ctrl)
    assert rows[-1]["state"] == "OPEN"
    assert "RE-OPENED" in rows[-1]["what"] and "broke again" in rows[-1]["what"]


# ── Acceptance case 4: a superseded id is never resurrected ──

def test_case4_superseded_id_never_resurrected(ctrl):
    """A gap_id that has been folded into a newer criterion (`superseded_by` set, R80) must never
    receive another transition row — not OPEN, not CLOSED, not RE-OPENED — no matter what the
    census measures for that old criterion string on a later run."""
    _write_ledger(ctrl, [dict(asset="bg_x", gap_id="bg_x-Vocab.rule1.alias", kind="gap",
                             criterion="Vocab.rule1.alias", what="w", change="", detector="d",
                             owner="asset_census", gate="this asset's certification",
                             state="OPEN", ts="t0", superseded_by="bg_x-Vocab.alias")])
    for verdict in ("FAIL", "PASS", "PARTIAL", "N/A"):
        added, skipped, closed, reopened = asset_census.emit_gaps(
            _census("bg_x", "Vocab.rule1.alias", verdict))
        assert (added, skipped, closed, reopened) == (0, 0, 0, 0), (
            f"a superseded id must never transition, got a write for verdict={verdict}")
    rows = _read_ledger(ctrl)
    assert len(rows) == 1, "no new row may ever be appended under a superseded gap_id"


# ── F4 (A_REVIEW.md): WITHDRAWN is terminal, never re-opened by inference ──

def test_case_withdrawn_is_terminal_never_reopened(ctrl):
    """emit_gaps()'s own docstring says a row whose state is anything other than OPEN/IN_PROGRESS/
    CLOSED "is left alone rather than re-opened by inference" — but the code re-opened WITHDRAWN
    rows anyway (treating any non-live, non-OPEN state as "CLOSED or terminal" and reopening it on
    a failing measurement). WITHDRAWN is a human, out-of-band decision (the schema's own _schema
    line names it) and must stay WITHDRAWN even when the census now measures FAIL for that
    criterion."""
    _write_ledger(ctrl, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
                             what="withdrawn by the native — accepted risk", change="", detector="d",
                             owner="asset_census", gate="this asset's certification",
                             state="WITHDRAWN", ts="t0")])
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL", "still broken"))
    assert (added, closed, reopened) == (0, 0, 0), "a WITHDRAWN row must never be re-opened by measurement"
    assert skipped == 1
    rows = _read_ledger(ctrl)
    assert len(rows) == 1 and rows[0]["state"] == "WITHDRAWN", "no new row may be appended over a WITHDRAWN one"


# ── Acceptance case 5: hand change/owner/gate carried onto every transition row ──

def test_case5_hand_metadata_carried_onto_closed_row(ctrl):
    _write_ledger(ctrl, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
                             what="w", change="scope count_sql to this writer's rows",
                             detector="per-class producer census", owner="bg_x brief",
                             gate="bg_x brief acceptance", state="OPEN", ts="t0")])
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS"))
    rows = _read_ledger(ctrl)
    closed_row = rows[-1]
    assert closed_row["change"] == "scope count_sql to this writer's rows"
    assert closed_row["owner"] == "bg_x brief"
    assert closed_row["gate"] == "bg_x brief acceptance"


def test_case5_hand_metadata_carried_onto_reopened_row(ctrl):
    _write_ledger(ctrl, [
        dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar", what="w",
             change="hand fix X", detector="d", owner="bob", gate="bg_x brief", state="OPEN", ts="t0"),
        dict(asset="bg_x", gap_id="bg_x-Foo.bar", kind="gap", criterion="Foo.bar",
             what="CLOSED by measurement: ok", change="hand fix X", detector="d", owner="bob",
             gate="bg_x brief", state="CLOSED", ts="t1"),
    ])
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL", "regressed"))
    rows = _read_ledger(ctrl)
    reopened_row = rows[-1]
    assert reopened_row["change"] == "hand fix X"
    assert reopened_row["owner"] == "bob"
    assert reopened_row["gate"] == "bg_x brief"


def test_case5_first_open_row_uses_census_defaults(ctrl):
    """The carry-forward rule only applies once a prior row exists — the very first OPEN row for a
    gid has nothing to carry, so it (and only it) uses the census's own defaults."""
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    rows = _read_ledger(ctrl)
    assert rows[0]["owner"] == "asset_census"
    assert rows[0]["gate"] == "this asset's certification"
    assert rows[0]["change"] == ""


# ── Acceptance case 6: emit_gaps twice on an unchanged target appends nothing ──

def test_case6_rerun_unchanged_failing_target_appends_nothing(ctrl):
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    n_after_first = len(_read_ledger(ctrl))
    added, skipped, closed, reopened = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    assert added == 0 and closed == 0 and reopened == 0 and skipped == 1
    assert len(_read_ledger(ctrl)) == n_after_first


def test_case6_rerun_unchanged_passing_target_appends_nothing(ctrl):
    """Once closed, a criterion that keeps passing must never write another CLOSED row."""
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS"))
    n_after_close = len(_read_ledger(ctrl))
    asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS"))
    assert len(_read_ledger(ctrl)) == n_after_close


# ── The full loop, in miniature: OPEN -> CLOSED -> RE-OPENED -> CLOSED on one row ──

def test_full_loop_open_closed_reopened_closed(ctrl):
    r1 = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    assert _read_ledger(ctrl)[-1]["state"] == "OPEN"
    r2 = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS"))
    assert _read_ledger(ctrl)[-1]["state"] == "CLOSED"
    r3 = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "FAIL"))
    assert _read_ledger(ctrl)[-1]["state"] == "OPEN"
    assert "RE-OPENED" in _read_ledger(ctrl)[-1]["what"]
    r4 = asset_census.emit_gaps(_census("bg_x", "Foo.bar", "PASS"))
    assert _read_ledger(ctrl)[-1]["state"] == "CLOSED"
    assert (r1[0], r2[2], r3[3], r4[2]) == (1, 1, 1, 1)  # added, closed, reopened, closed


# ── Reproduces the sandbox port's OWN logic, to show these same cases fail under it ──
# (harness/asset_census_closing.py:620-680, transcribed here as a decision function so this test
# file needs no filesystem path into another campaign's harness tree; see A_REPORT.md for the run
# transcript diffing this against the fixed asset_census.emit_gaps.)

def _naive_port_emit_gaps(ctrl_dir: pathlib.Path, census: dict) -> tuple[int, int, int, int]:
    path = ctrl_dir / "asset_gaps.jsonl"
    latest: dict[str, dict] = {}
    if path.exists():
        for ln in path.read_text(encoding="utf-8").split("\n"):
            if ln.strip():
                r = json.loads(ln)
                if r.get("gap_id"):
                    latest[r["gap_id"]] = r
    added = skipped = closed = reopened = 0
    with path.open("a", encoding="utf-8") as f:
        for a in census["assets"]:
            for crit, res in a["measurements"].items():
                gid = f"{a['asset_id']}-{crit}"
                failing = res["v"] in (asset_census.FAIL, asset_census.PARTIAL, asset_census.NO_DET)
                prior = latest.get(gid)
                if failing:
                    if prior is None:
                        f.write(json.dumps(dict(asset=a["asset_id"], gap_id=gid, state="OPEN",
                                                what=f"measured: {res['measured']}", change="",
                                                owner="asset_census",
                                                gate="this asset's certification")) + "\n")
                        added += 1
                    elif prior.get("state", "OPEN").upper() == "CLOSED":
                        f.write(json.dumps(dict(asset=a["asset_id"], gap_id=gid, state="OPEN",
                                                what=f"RE-OPENED by measurement: {res['measured']}",
                                                change="", owner="asset_census",
                                                gate="this asset's certification")) + "\n")
                        reopened += 1
                    else:
                        skipped += 1
                else:
                    if prior is not None and prior.get("state", "OPEN").upper() == "OPEN":
                        f.write(json.dumps(dict(asset=a["asset_id"], gap_id=gid, state="CLOSED",
                                                what=f"CLOSED by measurement: {res['measured']}",
                                                change="", owner="asset_census",
                                                gate="this asset's certification")) + "\n")
                        closed += 1
    return added, skipped, closed, reopened


def test_naive_port_fails_case1_closes_on_not_generic(tmp_path):
    """Demonstrates D4 finding #6 directly: the sandbox port's `else: close` branch treats
    NOT_GENERIC (anything not in the failing tuple) as a pass and wrongly closes the row."""
    _write_ledger(tmp_path, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", state="OPEN")])
    added, skipped, closed, reopened = _naive_port_emit_gaps(
        tmp_path, _census("bg_x", "Foo.bar", "NOT_GENERIC"))
    assert closed == 1, "the naive port DOES wrongly close on NOT_GENERIC — this is the bug D4 names"


def test_naive_port_fails_case2_in_progress_never_closes(tmp_path):
    _write_ledger(tmp_path, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", state="IN_PROGRESS")])
    added, skipped, closed, reopened = _naive_port_emit_gaps(
        tmp_path, _census("bg_x", "Foo.bar", "PASS"))
    assert closed == 0, "the naive port never closes an IN_PROGRESS row — this is the bug D4 names"


def test_naive_port_fails_case4_superseded_id_resurrected(tmp_path):
    _write_ledger(tmp_path, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", state="OPEN",
                                  superseded_by="bg_x-Foo.baz")])
    added, skipped, closed, reopened = _naive_port_emit_gaps(
        tmp_path, _census("bg_x", "Foo.bar", "PASS"))
    assert closed == 1, "the naive port has no superseded_by handling at all — it resurrects the id"


def test_naive_port_fails_case5_drops_hand_metadata(tmp_path):
    _write_ledger(tmp_path, [dict(asset="bg_x", gap_id="bg_x-Foo.bar", state="OPEN",
                                  change="hand fix X", owner="bob", gate="bg_x brief")])
    _naive_port_emit_gaps(tmp_path, _census("bg_x", "Foo.bar", "PASS"))
    rows = _read_ledger(tmp_path)
    assert rows[-1]["owner"] == "asset_census" and rows[-1]["owner"] != "bob", (
        "the naive port replaces hand owner/gate/change with its own defaults on every "
        "transition row — this is the bug D4 names"
    )
