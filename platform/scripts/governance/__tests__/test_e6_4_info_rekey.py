"""test_e6_4_info_rekey.py -- Suvarna E6.4: the reviewed, idempotent ledger migration that re-keys the non-gate criteria
(Cost., Count., Complete., Reach.) from open `kind: gap` rows to `kind: info` (`ledger_e6_4_info_rekey.py`), and the
stricter-only emit rule (`asset_census.INFO_ONLY_GATES`) that keeps a later census from opening them again.

Every rule has a seeded defect (a mutant of the module under test) and a test that fails when the rule is removed:
  same-id append (the reader raises) - non-idempotent - a gate criterion touched - a CLOSED row touched - the evidence
  dropped - the byte-prefix broken - the canonical ledger without the fold's git preconditions - an unknown criterion
  prefix - the new ids collide - the emit rule removed.
The detector semantic is checked against an independent re-implementation of `ledger_no_open_gap_on` AND (when the tracker
checkout is present) the tracker's own detector. The reader proof uses the reader's own parser (`_e63_parse_gaps`,
`elevated_assets`). Offline: tmp ledgers, tmp git repos; the REAL ledger is only READ (a session guard hashes it).
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import inspect
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import threading
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import ledger_e6_4_info_rekey as rk  # noqa: E402
import nikasha_fold as nf  # noqa: E402
from _e6_3_fixtures import World, gap as wgap, load_tracker, mini_patch, git as fgit  # noqa: E402

REPO = HERE.parents[3]
REAL_LEDGER = REPO / nf.GAPS_REL
TS = "2026-10-03T12:00:00+05:30"
SCHEMA = {"asset": "_schema", "_doc": "Delta ledger. Append-only.", "kind_added_on": "2026-09-26"}
T = load_tracker()


@pytest.fixture
def mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture(scope="module", autouse=True)
def real_ledger_never_written():
    before = hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest()
    yield
    assert hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest() == before, "a test wrote to the REAL asset_gaps.jsonl"


def row(asset, crit, state="OPEN", kind="gap", gap_id=None, **over):
    r = dict(asset=asset, gap_id=gap_id or f"{asset}-{crit}", kind=kind, criterion=crit,
             what=f"measured: {asset} {crit} figure / required: the gate's claim", change="hand change",
             detector=f"asset_census.py --layer L0 ({crit})", owner="asset_census", gate="this asset's certification",
             state=state, ts="2026-09-26T13:19:10+05:30")
    r.update(over)
    return r


def led(*rows) -> bytes:
    return rk.dump_rows([SCHEMA, *rows])


def write(path, *rows):
    path.write_bytes(led(*rows))
    return path


def world_rows():
    """A small ledger: 3 open targets (one per family), a CLOSED target, a gate gap, an opportunity, near-miss prefixes."""
    return [
        row("bg_a", "Cost.baseline"), row("bg_a", "Count.floor"), row("bg_b", "Complete.depth"),
        row("bg_c", "Cost.baseline", state="CLOSED"),
        row("bg_a", "Earn.build_record"), row("bg_a", "Narr.x", kind="opportunity", gap_id="bg_a-OPP1"),
        row("bg_b", "Completeness.depth.dasha_link"), row("bg_b", "Reachability", gap_id="bg_b-Reachability"),
        row("bg_c", "Costly.x"), row("bg_c", "Count", gap_id="bg_c-Count"),
        row("bg_a", "Cost.baseline", gap_id="bg_a-G07"),                      # a hand-id row on a target criterion
    ]


def detector_view(rows):
    """Independent re-implementation of suvarna_tracker/detectors.py ledger_state + d_ledger_no_open_gap_on (read there)."""
    last = {}
    for d in rows:
        if d.get("asset") == "_schema" or "gap_id" not in d:
            continue
        last[d["gap_id"]] = d
    return [d for d in last.values() if d.get("state") in ("OPEN", "RE-OPENED") and d.get("kind", "gap") == "gap"
            and not d.get("superseded_by") and str(d.get("criterion", "")).startswith(("Cost.", "Count.", "Complete.", "Reach."))]


def lines(b):
    return [json.loads(x) for x in b.decode().split("\n") if x.strip()]


# ═══════════════════════════════ the migration's shape ═══════════════════════════════

def test_each_open_target_row_gets_a_new_info_id_row_then_a_superseding_row():
    old = lines(led(*world_rows()))
    new = rk.fold_info_rekeys(old, TS)
    assert len(new) == 8                                   # 4 live targets (Cost, Count, Complete, hand-id Cost) x 2
    infos = [r for r in new if r["kind"] == "info"]
    sups = [r for r in new if r.get("superseded_by")]
    assert [r["gap_id"] for r in infos] == ["bg_a-Cost.baseline#info", "bg_a-Count.floor#info", "bg_b-Complete.depth#info", "bg_a-G07#info"]
    assert [r["gap_id"] for r in sups] == ["bg_a-Cost.baseline", "bg_a-Count.floor", "bg_b-Complete.depth", "bg_a-G07"]
    assert new[0]["kind"] == "info" and new[1].get("superseded_by") == new[0]["gap_id"]      # info first, then the supersede
    for i, s in zip(infos, sups):
        assert s["superseded_by"] == i["gap_id"] and i["rekeyed_from"] == s["gap_id"] and i["rekey"] == rk.RULING
        assert i["ts"] == s["ts"] == TS and "superseded_by" not in i and s["kind"] == "gap"
        assert i["state"] == s["state"] == "OPEN"


def test_the_info_row_carries_the_old_measurement_evidence_verbatim():
    old = lines(led(*world_rows()))
    by_id = {r["gap_id"]: r for r in old[1:]}
    for r in rk.fold_info_rekeys(old, TS):
        if r["kind"] == "info":
            o = by_id[r["rekeyed_from"]]
            for k in ("asset", "criterion", "what", "change", "detector", "owner", "gate", "state"):
                assert r[k] == o[k], k


def test_only_live_never_superseded_target_rows_are_touched():
    old = lines(led(*world_rows()))
    touched = {r["gap_id"] for r in rk.fold_info_rekeys(old, TS) if r.get("superseded_by")}
    assert touched == {"bg_a-Cost.baseline", "bg_a-Count.floor", "bg_b-Complete.depth", "bg_a-G07"}
    # a gate criterion's OPEN gap, a CLOSED target, an opportunity and every near-miss prefix are left alone
    for gid in ("bg_a-Earn.build_record", "bg_c-Cost.baseline", "bg_a-OPP1", "bg_b-Completeness.depth.dasha_link",
                "bg_b-Reachability", "bg_c-Costly.x", "bg_c-Count"):
        assert gid not in touched


def test_in_progress_and_reopened_states_are_live():
    old = lines(led(row("bg_a", "Cost.baseline", state="IN_PROGRESS"), row("bg_a", "Count.floor", state="RE-OPENED")))
    assert len(rk.fold_info_rekeys(old, TS)) == 4
    assert rk.detector_open(lines(led(row("bg_a", "Count.floor", state="RE-OPENED"))))      # the detector reads RE-OPENED


def test_a_row_without_a_kind_reads_as_a_gap():
    r = row("bg_a", "Cost.baseline")
    r.pop("kind")
    assert len(rk.fold_info_rekeys(lines(led(r)), TS)) == 2


def test_an_unfoldable_live_target_row_without_a_gap_id_is_refused():
    r = row("bg_a", "Cost.baseline")
    r.pop("gap_id")
    with pytest.raises(rk.RekeyRefused) as e:
        rk.fold_info_rekeys(lines(led(r)), TS)
    assert e.value.code == "unfoldable_row"


def test_empty_schema_and_junk_ledgers_are_refused():
    for data, code in ((b"", "ledger_no_schema_row"), (b'{"asset": "bg_a"}\n', "ledger_no_schema_row"),
                       (led(row("bg_a", "Cost.baseline"))[:-1], "ledger_no_trailing_newline"),
                       (b'{"asset": "_schema"}\nnot json\n', "ledger_line_invalid"), (b'{"asset": "_schema"}\n[1]\n', "ledger_line_invalid"),
                       (b"\xff\xfe\n", "ledger_not_utf8")):
        with pytest.raises(rk.RekeyRefused) as e:
            rk.plan(data, TS)
        assert e.value.code == code, data


def test_a_ledger_with_nothing_to_rekey_plans_nothing():
    p = rk.plan(led(row("bg_a", "Earn.build_record"), row("bg_a", "Cost.baseline", state="CLOSED")), TS)
    assert p["new_rows"] == [] and p["new_bytes"] == b"" and p["open_before"] == p["open_after"] == 0


# ═══════════════════════════════ idempotence, determinism, byte-prefix ═══════════════════════════════

def test_a_second_run_is_a_noop_and_writes_nothing(tmp_path):
    src, dst = write(tmp_path / "src.jsonl", *world_rows()), tmp_path / "dst.jsonl"
    r1 = rk.run(src, dst, ts=TS)
    assert r1["status"] == "migrated" and r1["rekeyed"] == 4 and r1["open_gaps_before"] == 4 and r1["open_gaps_after"] == 0
    first = dst.read_bytes()
    mtime = dst.stat().st_mtime_ns
    r2 = rk.run(dst, dst, ts="2026-10-04T00:00:00+05:30")
    assert r2["status"] == "unchanged" and r2["appended_lines"] == 0 and dst.read_bytes() == first and dst.stat().st_mtime_ns == mtime
    r3 = rk.run(dst, tmp_path / "dst2.jsonl", ts=TS)
    assert r3["status"] == "unchanged" and not (tmp_path / "dst2.jsonl").exists()           # nothing to do: not even a copy


def test_the_output_is_deterministic_and_the_old_bytes_are_an_exact_prefix(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    rk.run(src, a, ts=TS)
    rk.run(src, b, ts=TS)
    assert a.read_bytes() == b.read_bytes() and a.read_bytes().startswith(src.read_bytes())
    assert a.read_bytes().endswith(b"\n") and len(a.read_bytes()) > len(src.read_bytes())
    assert src.read_bytes() == led(*world_rows())                                           # --src is never modified


def test_dry_run_writes_nothing(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    rep = rk.run(src, tmp_path / "dst.jsonl", ts=TS, dry_run=True)
    assert rep["status"] == "dry_run" and rep["rekeyed"] == 4 and not (tmp_path / "dst.jsonl").exists()
    assert rep["by_prefix"] == {"Cost.": 2, "Count.": 1, "Complete.": 1, "Reach.": 0}


def test_in_place_appends_only_the_new_lines(tmp_path):
    p = write(tmp_path / "l.jsonl", *world_rows())
    before = p.read_bytes()
    rep = rk.run(p, p, ts=TS)
    assert rep["status"] == "migrated" and rep["in_place"] and p.read_bytes().startswith(before) and p.read_bytes() != before


# ═══════════════════════════════ mutants: one per rule ═══════════════════════════════

def test_mutant_same_id_append_is_refused_and_the_reader_would_raise(monkeypatch, mini, tmp_path):
    """A `kind: info` row under the SAME gap_id: the reader raises ('may not change to kind info')."""
    monkeypatch.setattr(rk, "info_id", lambda gid: gid)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Cost.baseline")), TS)
    assert e.value.code == "info_id_collision"
    # the oracle: the reader's own parser really does reject that ledger, so the refusal above is not a false alarm
    w = World(tmp_path).default()
    w.gaps += [wgap("ga_alpha", "Cost.base"), wgap("ga_alpha", "Cost.base", kind="info")]
    w.commit()
    with pytest.raises(T.ElevatedInputError) as ei:
        w.elevated(T)
    assert ei.value.code == "malformed" and "may not change to kind" in str(ei.value)


def test_mutant_non_idempotent_second_pass_refuses_instead_of_double_writing(monkeypatch):
    first = lines(led(*world_rows()))
    out = first + rk.fold_info_rekeys(first, TS)
    orig = rk._latest

    def no_ever_sup(rows):
        latest, _ = orig(rows)
        return latest, set()
    monkeypatch.setattr(rk, "_latest", no_ever_sup)
    # the mutant sees the superseded rows as live again; it must not append a second set
    with pytest.raises(rk.RekeyRefused) as e:
        rk.fold_info_rekeys(out, TS)
    assert e.value.code in ("info_id_collision",)


def test_mutant_a_gate_criterion_is_touched_is_refused(monkeypatch):
    monkeypatch.setattr(rk, "_is_target", lambda r: True)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Earn.build_record")), TS)
    assert e.value.code == "gate_criterion_touched"


def test_mutant_a_closed_row_is_touched_is_refused(monkeypatch):
    monkeypatch.setattr(rk, "_is_live_gap", lambda r: True)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_c", "Cost.baseline", state="CLOSED")), TS)
    assert e.value.code == "closed_row_touched"


def test_mutant_dropped_evidence_is_refused(monkeypatch):
    orig = rk.fold_info_rekeys

    def drop(rows, ts):
        out = orig(rows, ts)
        for r in out:
            if r["kind"] == "info":
                r["what"] = ""
        return out
    monkeypatch.setattr(rk, "fold_info_rekeys", drop)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Cost.baseline")), TS)
    assert e.value.code == "evidence_dropped"


def test_mutant_a_missing_supersede_leaves_the_detector_red_and_is_refused(monkeypatch):
    orig = rk.fold_info_rekeys
    monkeypatch.setattr(rk, "fold_info_rekeys", lambda rows, ts: [r for r in orig(rows, ts) if r["kind"] == "info"])
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Cost.baseline")), TS)
    assert e.value.code == "detector_still_open"


def test_mutant_a_wrong_supersede_target_is_refused(monkeypatch):
    orig = rk.fold_info_rekeys

    def wrong(rows, ts):
        out = orig(rows, ts)
        for r in out:
            if r.get("superseded_by"):
                r["superseded_by"] = "bg_a-Nowhere#info"
        return out
    monkeypatch.setattr(rk, "fold_info_rekeys", wrong)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Cost.baseline")), TS)
    assert e.value.code == "dangling_supersede"


def test_mutant_a_broken_byte_prefix_is_refused_and_nothing_is_written(tmp_path, monkeypatch):
    src, dst = write(tmp_path / "src.jsonl", *world_rows()), tmp_path / "dst.jsonl"
    orig = rk.plan

    def rewrite(b, ts):
        p = orig(b, ts)
        p["out_bytes"] = b.replace(b"Delta ledger", b"DELTA ledger", 1) + p["new_bytes"]        # line 1 rewritten
        return p
    monkeypatch.setattr(rk, "plan", rewrite)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(src, dst, ts=TS)
    assert e.value.code == "not_append_only" and not dst.exists()


def test_in_place_refuses_when_the_ledger_changes_under_it(tmp_path, monkeypatch):
    p = write(tmp_path / "l.jsonl", *world_rows())
    orig_read = pathlib.Path.read_bytes
    calls = {"n": 0}

    def racing(self):
        data = orig_read(self)
        calls["n"] += 1
        if calls["n"] == 1 and self == p:                           # after the migration read the ledger, before the append re-checks it
            with open(p, "ab") as f:
                f.write(b'{"asset": "bg_z", "gap_id": "bg_z-x"}\n')
        return data
    monkeypatch.setattr(pathlib.Path, "read_bytes", racing)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(p, p, ts=TS)
    assert e.value.code == "ledger_changed_during_migration"


def test_mutant_unknown_criterion_prefix_is_never_matched():
    """Completeness.* / Reachability / Costly.* / bare `Count` do not start with the four prefixes (`<Family>.`)."""
    assert not any(rk._is_target(dict(criterion=c)) for c in ("Completeness.depth.dasha_link", "Reachability", "Costly.x", "Counter.x", "Build.Cost.x", "Earn.Count.floor", "Count", "Cost",
                                                              "Earn.build_record", "Narr.x", "", None, 7))
    assert all(rk._is_target(dict(criterion=c)) for c in ("Cost.baseline", "Count.floor", "Complete.depth", "Reach.fields", "Complete.width"))
    assert rk.INFO_PREFIXES == ("Cost.", "Count.", "Complete.", "Reach.")


def test_the_new_ids_colliding_with_existing_ones_are_refused():
    out = lines(led(row("bg_a", "Cost.baseline"), row("bg_a", "Cost.baseline", gap_id="bg_a-Cost.baseline#info", kind="info")))
    with pytest.raises(rk.RekeyRefused) as e:
        rk.fold_info_rekeys(out, TS)
    assert e.value.code == "info_id_collision"


def test_mutant_two_rows_share_one_info_id_is_refused(monkeypatch):
    monkeypatch.setattr(rk, "info_id", lambda gid: "bg_a-X#info")
    with pytest.raises(rk.RekeyRefused) as e:
        rk.plan(led(row("bg_a", "Cost.baseline"), row("bg_a", "Count.floor")), TS)
    assert e.value.code == "info_id_collision"


# ═══════════════════════════════ the canonical ledger path ═══════════════════════════════

def make_repo(tmp_path, *, cutover=True, commit=True):
    repo = tmp_path / "repo"
    (repo / "00_ARCHITECTURE/control").mkdir(parents=True)
    fgit(repo, "init", "-q", "-b", "main")
    p = repo / nf.GAPS_REL
    p.write_bytes(led(*world_rows()))
    if cutover:
        (repo / nf.CUTOVER_REL).parent.mkdir(parents=True, exist_ok=True)
        (repo / nf.CUTOVER_REL).write_text("{}")
    if commit:
        fgit(repo, "add", "-A")
        fgit(repo, "commit", "-q", "-m", "ledger")
    return repo, p


def test_canonical_ledger_in_place_after_the_fold_preconditions(tmp_path):
    repo, p = make_repo(tmp_path)
    before = p.read_bytes()
    rep = rk.run(p, p, ts=TS)
    assert rep["status"] == "migrated" and p.read_bytes().startswith(before)
    assert rk.run(p, p, ts=TS)["status"] == "unchanged"           # idempotent... (committed? the second run has no work, no preflight needed)


def test_canonical_ledger_refused_when_dirty_untracked_or_without_the_cutover(tmp_path):
    repo, p = make_repo(tmp_path)
    p.write_bytes(p.read_bytes() + b'{"asset": "bg_z", "gap_id": "bg_z-x", "kind": "gap", "criterion": "Earn.x", "state": "OPEN"}\n')
    with pytest.raises(nf.FoldRefused) as e:                                                    # uncommitted change
        rk.run(p, p, ts=TS)
    assert e.value.code == "ledger_dirty"
    fgit(repo, "checkout", "-q", "--", nf.GAPS_REL)
    p.write_bytes(p.read_bytes().replace(b"Delta", b"DELTA", 1))                                 # not a prefix of HEAD
    with pytest.raises(nf.FoldRefused) as e:
        rk.run(p, p, ts=TS)
    assert e.value.code == "ledger_not_append_only"
    fgit(repo, "checkout", "-q", "--", nf.GAPS_REL)
    fgit(repo, "rm", "-q", "--cached", "--", nf.GAPS_REL)                                        # untracked
    with pytest.raises(nf.FoldRefused) as e:
        rk.run(p, p, ts=TS)
    assert e.value.code == "ledger_untracked"
    fgit(repo, "add", nf.GAPS_REL)
    fgit(repo, "rm", "-q", "-f", "--", nf.CUTOVER_REL)                                           # cut-over not landed
    fgit(repo, "commit", "-q", "-m", "x")
    with pytest.raises(nf.FoldRefused) as e:
        rk.run(p, p, ts=TS)
    assert e.value.code == "cutover_not_landed"


def test_canonical_ledger_is_never_a_dst_or_src_of_a_different_file(tmp_path):
    repo, p = make_repo(tmp_path)
    other = write(tmp_path / "other.jsonl", *world_rows())
    before = p.read_bytes()
    with pytest.raises(nf.FoldRefused) as e:
        rk.run(other, p, ts=TS)                                                                   # would overwrite the canonical ledger
    assert e.value.code == "canonical_path" and p.read_bytes() == before
    with pytest.raises(nf.FoldRefused) as e:
        rk.run(p, tmp_path / "copy.jsonl", ts=TS)                                                 # the canonical src leaves via a COPY, not here
    assert e.value.code == "canonical_path" and not (tmp_path / "copy.jsonl").exists()


def test_dry_run_on_the_canonical_path_needs_no_preconditions_and_writes_nothing(tmp_path):
    repo, p = make_repo(tmp_path, cutover=False)
    p.write_bytes(p.read_bytes() + b"")
    before = p.read_bytes()
    rep = rk.run(p, p, ts=TS, dry_run=True)
    assert rep["status"] == "dry_run" and p.read_bytes() == before


def test_a_copy_inside_a_repo_at_a_non_canonical_path_takes_no_preconditions(tmp_path):
    repo, p = make_repo(tmp_path)
    copy = repo / "scratch_copy.jsonl"                                                            # untracked, not the canonical rel path
    copy.write_bytes(p.read_bytes())
    assert rk.run(copy, copy, ts=TS)["status"] == "migrated"


def test_the_canonical_path_definition_is_the_folds_not_a_second_copy():
    import ast
    tree = ast.parse(pathlib.Path(rk.__file__).read_text(encoding="utf-8"))
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "\n" not in n.value]
    assert rk.nf is nf and not [c for c in consts if "asset_gaps" in c or "00_ARCHITECTURE" in c]      # no second copy of the path
    assert "canonical_info" in rk._is_canonical.__code__.co_names


def test_cli_exit_codes_and_report(tmp_path, capsys):
    src = write(tmp_path / "src.jsonl", *world_rows())
    assert rk.main(["--src", str(src), "--dst", str(tmp_path / "d.jsonl"), "--dry-run", "--ts", TS]) == 0
    assert json.loads(capsys.readouterr().out)["rekeyed"] == 4
    assert rk.main(["--src", str(tmp_path / "missing.jsonl"), "--dst", str(tmp_path / "d.jsonl"), "--ts", TS]) == rk.EX_REFUSED
    assert "REFUSED src_missing" in capsys.readouterr().err
    assert rk.main(["--src", str(src), "--dst", str(tmp_path / "d.jsonl"), "--ts", "not-a-time"]) == rk.EX_REFUSED
    bad = tmp_path / "bad.jsonl"
    bad.write_bytes(b"\xff")
    assert rk.main(["--src", str(bad), "--dst", str(tmp_path / "d2.jsonl"), "--ts", TS]) == rk.EX_REFUSED
    assert rk.main(["--src", str(src), "--dst", str(tmp_path / "d.jsonl"), "--ts", TS]) == 0
    assert (tmp_path / "d.jsonl").read_bytes().startswith(src.read_bytes())


# ═══════════════════════════════ the detector, and a gate gap untouched ═══════════════════════════════

def test_after_the_migration_the_detector_is_green_and_a_gate_gap_is_untouched(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    dst = tmp_path / "dst.jsonl"
    rk.run(src, dst, ts=TS)
    before, after = lines(src.read_bytes()), lines(dst.read_bytes())
    assert len(detector_view(before)) == 4 and detector_view(after) == []
    # a gate criterion with an OPEN gap: still the very same latest open gap row
    for gid in ("bg_a-Earn.build_record",):
        assert [r for r in detector_view_any(after) if r["gap_id"] == gid] == [r for r in detector_view_any(before) if r["gap_id"] == gid]
    open_gate = lambda rows: sorted(r["gap_id"] for r in latest_rows(rows) if r.get("state") == "OPEN" and r.get("kind", "gap") == "gap"
                                    and not r.get("superseded_by") and not rk._is_target(r))
    assert open_gate(after) == open_gate(before) and "bg_a-Earn.build_record" in open_gate(after)
    # every pre-existing line is unchanged and every new line is on a target criterion
    assert after[:len(before)] == before and all(rk._is_target(r) for r in after[len(before):])


def latest_rows(rows):
    last = {}
    for r in rows:
        if r.get("gap_id"):
            last[r["gap_id"]] = r
    return list(last.values())


def detector_view_any(rows):
    return latest_rows(rows)


def _find_tracker():
    """The governance dir holding suvarna_tracker/: $SUVARNA_TRACKER_DIR, else any worktree of this repository (as the E5.2 parity test)."""
    env = os.environ.get("SUVARNA_TRACKER_DIR")
    cands = [pathlib.Path(env)] if env else []
    r = subprocess.run(["git", "-C", str(REPO), "worktree", "list", "--porcelain"], capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith("worktree "):
            cands.append(pathlib.Path(ln[9:]) / "platform/scripts/governance")
    cands.append(REPO / "platform/scripts/governance")
    return next((c for c in cands if (c / "suvarna_tracker" / "detectors.py").is_file()), None)


TRACKER_DETECTORS = _find_tracker()


def tracker_detector_result(tmp_path, ledger_bytes):
    """The tracker's OWN d_ledger_no_open_gap_on, run against a tmp git repo whose HEAD holds `ledger_bytes`."""
    sys.path.insert(0, str(TRACKER_DETECTORS))
    try:
        from suvarna_tracker import detectors as D
    finally:
        sys.path.remove(str(TRACKER_DETECTORS))
    root = tmp_path / "trk"
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    fgit(root, "init", "-q", "-b", "main")
    (root / nf.GAPS_REL).write_bytes(ledger_bytes)
    (root / nf.CERTS_REL).write_text('{"asset": "_schema"}\n')
    fgit(root, "add", "-A")
    fgit(root, "commit", "-q", "-m", "l")
    cfg = D.Config(repo=str(root), nikasha_root=str(root), pgenv=None, home=str(tmp_path))
    cls = next(c for c in vars(D).values() if inspect.isclass(c) and hasattr(c, "d_ledger_no_open_gap_on"))
    return cls(cfg).d_ledger_no_open_gap_on(dict(criteria_prefixes=["Cost.", "Count.", "Complete.", "Reach."]))


@pytest.mark.skipif(TRACKER_DETECTORS is None, reason="suvarna_tracker is on no worktree of this repository and $SUVARNA_TRACKER_DIR is unset")
def test_the_trackers_own_detector_goes_pending_to_done(tmp_path):
    p = rk.plan(led(*world_rows()), TS)
    assert tracker_detector_result(tmp_path / "a", led(*world_rows())).status == "pending"
    assert tracker_detector_result(tmp_path / "b", p["out_bytes"]).status == "done"


# ═══════════════════════════════ the reader's own parser ═══════════════════════════════

def test_the_reader_accepts_the_migrated_ledger_and_the_asset_stays_elevated(mini, tmp_path):
    w = World(tmp_path).default()
    base = {"ga_alpha", "bg_beta", "ka_gamma"}
    w.gaps += [wgap("ga_alpha", "Cost.base"), wgap("ga_alpha", "Cost.base", gap_id="ga_alpha-G9")]
    w.commit()
    assert w.elevated(T) == base                                              # info family: never blocks, before ...
    rows = [SCHEMA, *w.gaps]
    new = rk.fold_info_rekeys(rows, TS)
    assert len(new) == 4
    w.gaps += new
    w.commit()
    assert w.elevated(T) == base                                              # ... and after: the migration does not make the reader raise
    got = T._e63_parse_gaps(open(w.repo / nf.GAPS_REL, "rb").read(), {"ga_alpha"}, T._e63_registry_facts(str(w.repo), w.last), {})
    assert sorted((g["kind"], g["gap_id"]) for g in got) == [("info", "ga_alpha-Cost.base#info"), ("info", "ga_alpha-G9#info")]


def test_the_reader_state_of_a_gate_gap_is_unchanged_by_the_migration(mini, tmp_path):
    w = World(tmp_path).default()
    w.gaps += [wgap("ga_alpha", "Idem.pat"), wgap("ga_alpha", "Cost.base")]
    w.commit()
    assert w.elevated(T) == {"bg_beta", "ka_gamma"}                           # the OPEN core-gate gap blocks
    w.gaps += rk.fold_info_rekeys([SCHEMA, *w.gaps], TS)
    w.commit()
    assert w.elevated(T) == {"bg_beta", "ka_gamma"}                           # still blocks after the migration (untouched)


def test_the_reader_raises_on_a_migration_that_re_keys_a_gate_criterion(mini, tmp_path):
    w = World(tmp_path).default()
    w.gaps += [wgap("ga_alpha", "Idem.pat"), wgap("ga_alpha", "Idem.pat", gap_id="ga_alpha-Idem.pat#info", kind="info", superseded_by=None),
               wgap("ga_alpha", "Idem.pat", superseded_by="ga_alpha-Idem.pat#info")]
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_the_real_committed_ledger_migrates_clean_through_the_readers_parser(tmp_path):
    data = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + nf.GAPS_REL], capture_output=True, check=True).stdout
    sha = T._e63_resolve_ref("HEAD", str(REPO))
    facts = T._e63_registry_facts(str(REPO), sha)
    known = set(T._e63_registry_assets(str(REPO), sha))
    expected = sorted(d["gap_id"] for d in detector_view(lines(data)))        # independent oracle: the detector's own open set
    p = rk.plan(data, TS)
    assert sorted(r["rekeyed_from"] for r in p["new_rows"] if r["kind"] == "info") == expected
    assert p["open_after"] == 0 and p["by_prefix"]["Reach."] == 0
    assert set(p["by_criterion"]) <= {"Cost.baseline", "Count.floor", "Complete.depth"}
    before = T._e63_parse_gaps(data, known, facts, {})
    after = T._e63_parse_gaps(p["out_bytes"], known, facts, {})                # raises on any identity / fold violation
    T._e63_check_info_rekeys(after, {}, facts)
    fam = ("Cost", "Count", "Complete", "Reach")
    blocking = lambda rows: sorted(g["gap_id"] for g in rows if T._e63_gap_blocks(g, (), facts.info_families))
    assert blocking(after) == blocking(before)                                 # verdict-neutral: what can block is identical
    assert not [g for g in after if g["kind"] == "gap" and g["state"] in ("OPEN", "IN_PROGRESS") and g["criterion"].split(".")[0] in fam]
    assert rk.plan(p["out_bytes"], TS)["new_rows"] == []                       # idempotent on the real ledger too


# ═══════════════════════════════ the emit rule (the second trap) ═══════════════════════════════

@pytest.fixture()
def ctrl(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    return tmp_path


def census(*cells):
    """cells: (asset, criterion, verdict)."""
    by = collections.OrderedDict()
    for a, c, v in cells:
        by.setdefault(a, {})[c] = dict(v=v, measured="x")
    return dict(layer="L0", assets=[dict(asset_id=a, measurements=m) for a, m in by.items()])


def ledger_rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


FAMILY_CRITS = ("Cost.baseline", "Count.floor", "Complete.depth")


def test_a_later_emit_after_the_migration_appends_nothing_for_these_families(ctrl):
    write(ctrl / "asset_gaps.jsonl", *world_rows())
    rk.run(ctrl / "asset_gaps.jsonl", ctrl / "asset_gaps.jsonl", ts=TS)
    before = (ctrl / "asset_gaps.jsonl").read_bytes()
    cells = [(a, c, ac.FAIL) for a in ("bg_a", "bg_b", "bg_c", "bg_new") for c in FAMILY_CRITS]
    summary = ac.emit_gaps_summary(census(*cells))
    assert (ctrl / "asset_gaps.jsonl").read_bytes() == before                 # no OPEN, no RE-OPEN, no resurrection of an old id
    assert summary["added"] == 0 and summary["reopened"] == 0 and summary["closed"] == 0
    assert not detector_view(lines((ctrl / "asset_gaps.jsonl").read_bytes()))


def test_emit_never_opens_a_gap_on_an_info_family_even_without_a_prior_or_over_a_closed_row(ctrl):
    write(ctrl / "asset_gaps.jsonl", row("bg_c", "Cost.baseline", state="CLOSED"))
    ac.emit_gaps_summary(census(("bg_c", "Cost.baseline", ac.FAIL), ("bg_new", "Count.floor", ac.PARTIAL), ("bg_new", "Complete.depth", ac.NO_DET)))
    assert len(ledger_rows(ctrl / "asset_gaps.jsonl")) == 2                   # schema + the CLOSED row: nothing appended


def test_the_emit_rule_is_stricter_only_gate_criteria_and_closures_are_unchanged(ctrl):
    write(ctrl / "asset_gaps.jsonl", row("bg_a", "Cost.baseline"), row("bg_a", "Earn.build_record", state="OPEN"))
    s = ac.emit_gaps_summary(census(("bg_a", "Cost.baseline", ac.PASS), ("bg_new", "Earn.build_record", ac.FAIL),
                                    ("bg_new", "Null.blank_rows", ac.PARTIAL), ("bg_a", "Earn.build_record", ac.PASS)))
    rows = ledger_rows(ctrl / "asset_gaps.jsonl")[3:]
    assert s["closed"] == 2 and s["added"] == 2
    assert {(r["gap_id"], r["state"]) for r in rows} == {("bg_a-Cost.baseline", "CLOSED"), ("bg_a-Earn.build_record", "CLOSED"),
                                                          ("bg_new-Earn.build_record", "OPEN"), ("bg_new-Null.blank_rows", "OPEN")}


def test_mutant_without_the_emit_rule_a_later_census_reopens_the_detector(ctrl, monkeypatch):
    monkeypatch.setattr(ac, "INFO_ONLY_GATES", ())
    write(ctrl / "asset_gaps.jsonl", row("bg_c", "Cost.baseline", state="CLOSED"))
    ac.emit_gaps_summary(census(("bg_c", "Cost.baseline", ac.FAIL), ("bg_new", "Count.floor", ac.FAIL)))
    assert len(detector_view(ledger_rows(ctrl / "asset_gaps.jsonl"))) == 2


def test_info_only_gates_are_registry_gates_and_none_is_a_core_gate():
    gates = {e["gate"] for e in ac.CRITERION_REGISTRY.values()}
    assert tuple(g + "." for g in ac.INFO_ONLY_GATES) == rk.INFO_PREFIXES
    assert set(ac.INFO_ONLY_GATES) <= gates | {"Reach"} and not set(ac.INFO_ONLY_GATES) & set(ac.CELL_GATES)
    assert ac.LIVE_GAP_STATES == ("OPEN", "IN_PROGRESS")


# ═══════════════════════════════ review round (E6.4): H1, M1-M3, survivors, L1, L6 ═══════════════════════════════

def test_prefix_match_is_startswith_not_substring_at_plan_level():
    """M22: `Build.Cost.x`, `Earn.Count.floor`, `Costly.*`, `Counter.*` are never re-keyed, even when OPEN."""
    rows = [row("bg_a", c) for c in ("Build.Cost.x", "Earn.Count.floor", "Costly.x", "Counter.x", "Completeness.depth", "Reachability.f")]
    assert rk.plan(led(*rows), TS)["new_rows"] == []


def test_the_prefixes_are_derived_from_the_one_emit_constant():
    assert rk.INFO_PREFIXES == tuple(g + "." for g in ac.INFO_ONLY_GATES)
    fams = {e["gate"] for e in ac.CRITERION_REGISTRY.values()}
    assert set(ac.INFO_ONLY_GATES) <= fams - set(ac.CELL_GATES)          # each is a registry NON-gate family
    # `Completeness` is also a non-gate registry family; it stays a GAP family per the plan's four prefixes (an SS question, see the PR)
    assert "Completeness" in fams - set(ac.CELL_GATES) and "Completeness" not in ac.INFO_ONLY_GATES


# ── M2: --ts must be tz-aware ──

@pytest.mark.parametrize("ts", ["2026-10-03T12:00:00", "2026-10-03", "yesterday", ""])
def test_a_naive_or_malformed_ts_is_refused_and_nothing_is_written(tmp_path, ts):
    src = write(tmp_path / "src.jsonl", *world_rows())
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(src, tmp_path / "dst.jsonl", ts=ts)
    assert e.value.code == "bad_ts" and not (tmp_path / "dst.jsonl").exists()
    assert rk.main(["--src", str(src), "--dst", str(tmp_path / "dst.jsonl"), "--ts", ts or "x"]) == rk.EX_REFUSED
    assert rk.run(src, tmp_path / "dst.jsonl", ts="2026-10-03T12:00:00Z", dry_run=True)["status"] == "dry_run"


# ── M3: a hard link must not bypass the canonical protections ──

def test_a_hardlink_alias_of_the_canonical_ledger_is_refused(tmp_path, monkeypatch):
    repo, p = make_repo(tmp_path)
    monkeypatch.chdir(repo)                                           # the operator runs from the repository: its canonical ledger is known
    p.write_bytes(p.read_bytes() + b'{"asset": "bg_z", "gap_id": "bg_z-x", "kind": "gap", "criterion": "Earn.x", "state": "OPEN"}\n')   # dirty
    hard = tmp_path / "hard.jsonl"
    os.link(p, hard)
    before = p.read_bytes()
    assert rk.aliases_canonical(hard) is True and rk.aliases_canonical(p) is False
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(hard, hard, ts=TS)                                     # the dirty canonical, reached through an alias: no preflight would run
    assert e.value.code == "dst_hardlinked" and p.read_bytes() == before and hard.read_bytes() == before
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(p, hard, ts=TS)
    assert e.value.code == "dst_hardlinked"


def test_any_hardlinked_dst_is_refused_and_a_plain_copy_is_not(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    a = write(tmp_path / "a.jsonl", *world_rows())
    os.link(a, tmp_path / "b.jsonl")
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(src, a, ts=TS)
    assert e.value.code == "dst_hardlinked"
    assert rk.run(src, tmp_path / "c.jsonl", ts=TS)["status"] == "migrated"


# ── L6: a different existing dst is not silently overwritten; the mode is kept ──

def test_a_different_existing_dst_is_refused_but_an_identical_one_is_allowed(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    dst = tmp_path / "dst.jsonl"
    dst.write_bytes(b'{"asset": "_schema"}\nsomething else\n')
    before = dst.read_bytes()
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(src, dst, ts=TS)
    assert e.value.code == "dst_exists_different" and dst.read_bytes() == before
    dst.write_bytes(src.read_bytes())                                  # identical to the source: allowed
    assert rk.run(src, dst, ts=TS)["status"] == "migrated"
    out = dst.read_bytes()
    assert rk.run(src, dst, ts=TS)["status"] == "migrated" and dst.read_bytes() == out        # identical to the planned output: allowed, same bytes


def test_the_file_mode_is_preserved(tmp_path):
    src = write(tmp_path / "src.jsonl", *world_rows())
    os.chmod(src, 0o640)
    new = tmp_path / "new.jsonl"
    rk.run(src, new, ts=TS)
    assert stat.S_IMODE(new.stat().st_mode) == 0o640                     # a new copy takes the source's mode
    ex = tmp_path / "ex.jsonl"
    ex.write_bytes(src.read_bytes())
    os.chmod(ex, 0o604)
    rk.run(src, ex, ts=TS)
    assert stat.S_IMODE(ex.stat().st_mode) == 0o604                      # an existing dst keeps its own


# ── M11: a failed in-place write restores the ledger ──

def test_a_failed_append_truncates_the_torn_bytes_away(tmp_path, monkeypatch):
    p = write(tmp_path / "l.jsonl", *world_rows())
    before = p.read_bytes()
    real_write = os.write
    n = {"calls": 0}

    def torn(fd, data):
        n["calls"] += 1
        if n["calls"] == 1:
            return real_write(fd, bytes(data)[:50])                       # a torn partial write ...
        raise OSError("disk full")                                         # ... then the failure
    monkeypatch.setattr(os, "write", torn)
    with pytest.raises(rk.RekeyRefused) as e:
        rk.run(p, p, ts=TS)
    monkeypatch.undo()
    assert e.value.code == "ledger_write_failed" and p.read_bytes() == before


# ── M31: the append is serialised by flock; parallel in-place runs migrate exactly once ──

def test_append_waits_for_a_held_flock(tmp_path):
    import fcntl
    p = write(tmp_path / "l.jsonl", *world_rows())
    orig = p.read_bytes()
    holder = os.open(str(p), os.O_RDWR)
    fcntl.flock(holder, fcntl.LOCK_EX)
    done = threading.Event()
    t = threading.Thread(target=lambda: (rk._append(p, orig, b'{"x": 1}\n'), done.set()))
    t.start()
    time.sleep(0.6)
    blocked = not done.is_set()
    fcntl.flock(holder, fcntl.LOCK_UN)
    os.close(holder)
    t.join(10)
    assert blocked, "_append did not wait for the exclusive flock"
    assert p.read_bytes() == orig + b'{"x": 1}\n'


def test_five_parallel_in_place_runs_migrate_exactly_once(tmp_path):
    p = write(tmp_path / "l.jsonl", *world_rows())
    orig = p.read_bytes()
    script = pathlib.Path(rk.__file__)
    procs = [subprocess.Popen([sys.executable, str(script), "--src", str(p), "--dst", str(p), "--ts", TS],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(5)]
    outs = [(q.wait(), q.stdout.read(), q.stderr.read()) for q in procs]
    migrated = [o for o in outs if '"status": "migrated"' in o[1]]
    assert len(migrated) == 1, outs
    assert all(o[0] in (0, rk.EX_REFUSED) for o in outs)
    assert p.read_bytes() == orig + rk.plan(orig, TS)["new_bytes"]        # exactly one set of new lines, no duplicate


# ── L1: the census lock ──

def test_a_held_census_lock_stops_a_write_but_not_a_dry_run(tmp_path):
    lock = tmp_path / "census.lock"
    src = write(tmp_path / "src.jsonl", *world_rows())
    with nf.census_lock(lock):
        with pytest.raises(nf.LockHeld):
            rk.run(src, tmp_path / "d.jsonl", ts=TS, lock_file=lock)
        assert not (tmp_path / "d.jsonl").exists()
        assert rk.run(src, tmp_path / "d.jsonl", ts=TS, dry_run=True, lock_file=lock)["status"] == "dry_run"
        assert rk.main(["--src", str(src), "--dst", str(tmp_path / "d.jsonl"), "--ts", TS, "--lock-file", str(lock)]) == nf.EX_TEMPFAIL
    assert rk.run(src, tmp_path / "d.jsonl", ts=TS, lock_file=lock)["status"] == "migrated"      # released


# ── H1: the ledger-reading suite on the MIGRATED real ledger ──

def test_ledger_reading_suite_on_the_migrated_real_ledger(tmp_path):
    """The R81 test that broke when the migration was applied (bg_panchanga-Cost.baseline superseded) is exactly what this catches: copy the
    governance directory and the REAL ledger to a scratch tree, migrate the ledger there, run the ledger-reading tests that take a path-relative
    ledger. (test_e4_3_cutover / test_e5_2_fold / test_e6_3_* read git history: the apply runbook runs them on a committed scratch repo.)"""
    tree = tmp_path / "tree"
    (tree / "00_ARCHITECTURE/control").mkdir(parents=True)
    shutil.copytree(REPO / "platform/scripts/governance", tree / "platform/scripts/governance",
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    led_copy = tree / nf.GAPS_REL
    shutil.copyfile(REAL_LEDGER, led_copy)
    rep = rk.run(led_copy, led_copy, ts=TS)
    if rep["status"] == "migrated":
        assert rep["rekeyed"] == 219                                  # (the committed ledger is not yet migrated)
    else:
        assert rep["status"] == "unchanged" and not detector_view(lines(REAL_LEDGER.read_bytes()))      # (after the apply: nothing left to do)
    gov = tree / "platform/scripts/governance/__tests__"
    files = [gov / n for n in ("test_r15_r29_hand_row_census_run_id.py", "test_r80_schema_superseded_by_field.py",
                               "test_r81_apply_script.py", "test_r81_ledger_overlap_fold.py")]
    assert all(f.is_file() for f in files)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *map(str, files)], cwd=tree,
                       capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED="0"))
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-500:]


# ── M1 / E03 / E06: the emit rule's counter and its family matching ──

def test_info_only_suppression_is_its_own_counter_not_skipped(ctrl):
    write(ctrl / "asset_gaps.jsonl", row("bg_c", "Cost.baseline", state="CLOSED"), row("bg_o", "Earn.build_record"))
    s = ac.emit_gaps_summary(census(("bg_c", "Cost.baseline", ac.FAIL), ("bg_new", "Count.floor", ac.PARTIAL), ("bg_new", "Complete.depth", ac.NO_DET),
                                    ("bg_o", "Earn.build_record", ac.FAIL)))
    assert s["info_only_suppressed"] == 3 and s["skipped"] == 1 and s["added"] == 0     # the one skip is the already-open gate row
    assert ac.emit_gaps(census(("bg_c", "Cost.baseline", ac.FAIL)))[1] == 0              # the historical tuple's `skipped` stays honest too
    s2 = ac.emit_gaps_summary(census(("bg_o", "Earn.build_record", ac.FAIL)))
    assert "info_only_suppressed" not in s2                                             # present only when non-empty


@pytest.mark.parametrize("crit", ["Completeness.depth.dasha_link", "Costly.x", "Counter.x", "Reachability", "Reach", "CompleteX.depth"])
def test_family_matching_is_exact_near_misses_are_still_gaps(ctrl, crit):
    write(ctrl / "asset_gaps.jsonl")
    s = ac.emit_gaps_summary(census(("bg_n", crit, ac.FAIL)))
    assert s["added"] == 1 and "info_only_suppressed" not in s
    assert [r["state"] for r in ledger_rows(ctrl / "asset_gaps.jsonl")[1:]] == ["OPEN"]


def test_the_cli_prints_a_distinct_line_for_the_suppressed_cells(monkeypatch, capsys):
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "info_only_suppressed" in src.split("def main()", 1)[1]
    doc = ac.emit_gaps_summary.__doc__
    assert "info_only_suppressed" in doc and "INFO_ONLY_GATES" in doc
