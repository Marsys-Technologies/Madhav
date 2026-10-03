"""test_e4_3_cutover.py -- E4.3 ledger cut-over verifier (00_ARCHITECTURE/control/E4.3/verify_cutover.py).

Earned-signal tests (CLAUDE.md section N.8): the verifier must FAIL when a ledger byte changes, must report
NO_DETECTOR (non-zero, never a pass) when the cut commit cannot be read, and the permanent real-tree check is
the append-only PREFIX check -- the exact whole-file check is the one-off cut-over step and would (rightly) go
red the first time a census appends a row, so it is exercised only on tmp copies here.

Mutations are always made on tmp copies; no real file is touched.

The real asset_gaps.jsonl legitimately GROWS by appends (a census adds rows), so no test here may assume the real
tree's ledger is the cut-over ledger. Every test that needs "the ledger as it was at the cut" builds a tmp tree
from the CUT COMMIT'S BLOBS (`git show <cut_sha>:<path>`), never from the working-tree files; the real tree is
checked only by the append-only PREFIX check (first `old_bytes` bytes / `old_lines` lines / `old_md5`).
"""
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
E43 = REPO / "00_ARCHITECTURE/control/E4.3"
CUTOVER = E43 / "CUTOVER.json"

_spec = importlib.util.spec_from_file_location("verify_cutover", E43 / "verify_cutover.py")
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

GAPS = "00_ARCHITECTURE/control/asset_gaps.jsonl"
CERTS = "00_ARCHITECTURE/control/asset_certs.jsonl"
REGISTER = "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"


def _record() -> dict:
    return json.loads(CUTOVER.read_text(encoding="utf-8"))


def _cut_reachable_here() -> bool:
    return vc.cut_reachable(REPO, _record()["cut_sha"])


needs_cut = pytest.mark.skipif(
    not _cut_reachable_here(),
    reason="NO_DETECTOR: the cut commit is not reachable in this checkout, so the git-side comparison cannot run "
           "(this is a skip, never a pass)")


def _cut_tree_source(rel: str, rec: dict) -> bytes | None:
    """The bytes of `rel` AS THEY WERE AT THE CUT: `git show <cut_sha>:<rel>` when the cut commit is reachable
    (the normal case: local checkouts and the tag nikasha-cut-2a78ec64d). When it is not (shallow CI clone) the
    only remaining source is the working tree's first `old_bytes` bytes, accepted ONLY if their lines/bytes/md5
    equal the recorded cut (the register, which is not append-only, must be equal whole); otherwise None."""
    cut_sha = _record()["cut_sha"]
    blob = vc.git_show(REPO, cut_sha, rel) if vc.cut_reachable(REPO, cut_sha) else None
    if blob is not None:
        return blob
    wt = (REPO / rel).read_bytes()
    view = wt[: rec["old_bytes"]]
    want = {"lines": rec["old_lines"], "bytes": rec["old_bytes"], "md5": rec["old_md5"]}
    return view if vc.measure(view) == want else None


@pytest.fixture
def tmp_tree(tmp_path):
    """A tmp copy of the three cut-over files AT THE CUT (from the cut commit's blobs), independent of how far
    the real ledgers have since grown by appends. Skips (never passes) when the cut cannot be reproduced."""
    files = _record()["files"]
    for rel in (GAPS, CERTS, REGISTER):
        data = _cut_tree_source(rel, files[rel])
        if data is None:
            pytest.skip(f"NO_DETECTOR: cannot reproduce {rel} as of the cut (cut commit unreachable and the "
                        "working tree no longer matches the record); a skip, never a pass")
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    return tmp_path


def _append_rows(path: pathlib.Path, n: int) -> None:
    """Append n well-formed synthetic ledger rows (what a census does), newline-terminated."""
    with path.open("ab") as f:
        for i in range(n):
            f.write(b'{"asset":"synthetic","gap_id":"synthetic-G%d","state":"OPEN"}\n' % i)


def _flip_one_byte(path: pathlib.Path, offset: int) -> None:
    b = bytearray(path.read_bytes())
    b[offset] = b[offset] ^ 0x01
    path.write_bytes(bytes(b))


# ---- the record itself ---------------------------------------------------------------------------

def test_record_is_well_formed_and_flags_are_computed_from_its_own_numbers():
    rec = _record()
    assert len(rec["cut_sha"]) == 40 and all(c in "0123456789abcdef" for c in rec["cut_sha"])
    assert rec["main_sha"] == vc.PLACEHOLDER or len(rec["main_sha"]) == 40
    files = rec["files"]
    assert set(files) == {GAPS, CERTS, REGISTER}
    ledgers_equal = all(files[p]["old_md5"] == files[p]["new_md5"] and files[p]["old_lines"] == files[p]["new_lines"]
                        for p in (GAPS, CERTS))
    assert rec["ledgers_md5_equal"] is ledgers_equal
    assert rec["register_md5_equal"] is (files[REGISTER]["old_md5"] == files[REGISTER]["new_md5"])
    assert files[GAPS]["append_only"] and files[CERTS]["append_only"] and not files[REGISTER]["append_only"]
    # the task's pinned numbers
    assert (files[GAPS]["old_lines"], files[GAPS]["old_md5"]) == (857, "f6b1d3c5eeff7ec5d56d45448df69d80")
    assert (files[CERTS]["old_lines"], files[CERTS]["old_md5"]) == (1, "514cbdfcf3fa71b3e382f84a978bf369")
    assert files[REGISTER]["old_md5"] == "e4df1c25920b5aeaf0fe9a4730484e6c"
    assert rec["schema_row_untouched"] is True


# ---- mutation: a changed byte must be detected ----------------------------------------------------

def test_unmutated_tmp_copy_matches_the_recorded_cut_in_exact_mode(tmp_tree):
    code, report = vc.verify(tmp_tree, _record(), "exact", use_git=False)
    # no git side -> NO_DETECTOR, but every recorded-vs-working comparison must have been ok
    assert code == vc.EXIT_NO_DETECTOR, report
    assert not any(line.startswith("FAIL") for line in report)


@pytest.mark.parametrize("rel,offset", [(GAPS, 100), (GAPS, 424000), (CERTS, 10), (REGISTER, 5000)])
def test_one_changed_byte_in_any_cut_file_fails_exact_mode(tmp_tree, rel, offset):
    _flip_one_byte(tmp_tree / rel, offset)
    code, report = vc.verify(tmp_tree, _record(), "exact", use_git=False)
    assert code == vc.EXIT_MISMATCH, report
    assert any(line.startswith("FAIL") and rel in line for line in report)


def test_one_changed_byte_in_a_ledger_fails_prefix_mode_too(tmp_tree):
    _flip_one_byte(tmp_tree / GAPS, 12345)
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_MISMATCH, report


def test_a_missing_file_is_a_mismatch_not_a_skip(tmp_tree):
    (tmp_tree / CERTS).unlink()
    code, _ = vc.verify(tmp_tree, _record(), "exact", use_git=False)
    assert code == vc.EXIT_MISMATCH


@needs_cut
def test_mutated_ledger_with_a_rewritten_record_is_still_caught_by_the_git_side(tmp_tree):
    """Edit the ledger AND make CUTOVER.json agree with the edit: the recorded-vs-working comparison now passes,
    only `git show <cut>` can still tell. This is why the git side exists."""
    _flip_one_byte(tmp_tree / GAPS, 777)
    forged = _record()
    m = vc.measure((tmp_tree / GAPS).read_bytes())
    forged["files"][GAPS].update(old_lines=m["lines"], old_bytes=m["bytes"], old_md5=m["md5"])
    # sanity: against the forged record alone (no git side) the tampered ledger now looks fine
    assert vc.verify(tmp_tree, forged, "exact", use_git=False)[0] == vc.EXIT_NO_DETECTOR
    code, report = vc.verify(tmp_tree, forged, "exact", git_repo=REPO)
    assert code == vc.EXIT_MISMATCH, report
    assert any("git show" in line and line.startswith("FAIL") for line in report)


@needs_cut
def test_untouched_tmp_copy_verifies_against_the_cut_commit(tmp_tree):
    code, report = vc.verify(tmp_tree, _record(), "exact", git_repo=REPO)
    assert code == vc.EXIT_OK, report


# ---- NO_DETECTOR, never pass, when the cut is unreachable ----------------------------------------

def test_unreachable_cut_reports_no_detector_and_never_zero(tmp_tree, tmp_path_factory):
    not_a_repo = tmp_path_factory.mktemp("no_git")
    code, report = vc.verify(tmp_tree, _record(), "exact", git_repo=not_a_repo)
    assert code == vc.EXIT_NO_DETECTOR and code != 0
    assert any("NO_DETECTOR" in line for line in report)


def test_unreachable_cut_does_not_mask_a_real_mismatch(tmp_tree, tmp_path_factory):
    _flip_one_byte(tmp_tree / GAPS, 50)
    code, _ = vc.verify(tmp_tree, _record(), "exact", git_repo=tmp_path_factory.mktemp("no_git"))
    assert code == vc.EXIT_MISMATCH


def test_a_bogus_cut_sha_in_a_real_repo_is_no_detector(tmp_tree):
    rec = _record()
    rec["cut_sha"] = "0" * 40
    code, _ = vc.verify(tmp_tree, rec, "exact", git_repo=REPO)
    assert code == vc.EXIT_NO_DETECTOR


def test_malformed_record_is_a_usage_error(tmp_tree):
    code, _ = vc.verify(tmp_tree, {"cut_sha": "abc", "files": {}}, "exact", use_git=False)
    assert code == vc.EXIT_USAGE


# ---- prefix (append-only) mode --------------------------------------------------------------------

def test_appended_rows_pass_prefix_mode_but_fail_exact_mode(tmp_tree):
    with (tmp_tree / GAPS).open("ab") as f:
        f.write(b'{"asset":"x","gap_id":"x-Y","state":"OPEN"}\n')
    assert vc.verify(tmp_tree, _record(), "prefix", use_git=False)[0] == vc.EXIT_NO_DETECTOR   # prefix agrees; git side off
    assert vc.verify(tmp_tree, _record(), "exact", use_git=False)[0] == vc.EXIT_MISMATCH


def test_truncated_ledger_fails_prefix_mode(tmp_tree):
    p = tmp_tree / GAPS
    p.write_bytes(p.read_bytes()[:-200])
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_MISMATCH and any("SHORTER" in line for line in report)


def test_tmp_tree_is_the_cut_exactly(tmp_tree):
    """The fixture itself: a tmp copy at the cut has exactly the recorded lines/bytes/md5, so the exact-mode tests
    above are not vacuous and do not depend on the real tree's current length."""
    for rel, rec in _record()["files"].items():
        m = vc.measure((tmp_tree / rel).read_bytes())
        assert (m["lines"], m["bytes"], m["md5"]) == (rec["old_lines"], rec["old_bytes"], rec["old_md5"]), rel


# Mutation matrix on an EXTENDED ledger (the cut plus census-style appends, 857 -> 1872 lines):

N_APPENDED = 1015


def test_extended_ledger_one_rewritten_historical_byte_fails_prefix_mode(tmp_tree):
    _append_rows(tmp_tree / GAPS, N_APPENDED)
    assert vc.verify(tmp_tree, _record(), "prefix", use_git=False)[0] == vc.EXIT_NO_DETECTOR   # control: grown, intact
    _flip_one_byte(tmp_tree / GAPS, 12345)                                                    # inside the first 857 lines
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_MISMATCH and any(line.startswith("FAIL") and GAPS in line for line in report), report


def test_extended_ledger_truncated_to_856_lines_fails_prefix_mode(tmp_tree):
    _append_rows(tmp_tree / GAPS, N_APPENDED)
    lines = (tmp_tree / GAPS).read_bytes().splitlines(keepends=True)
    assert len(lines) == _record()["files"][GAPS]["old_lines"] + N_APPENDED
    (tmp_tree / GAPS).write_bytes(b"".join(lines[:856]))
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_MISMATCH and any("SHORTER" in line for line in report), report


def test_extended_ledger_with_1015_appended_lines_still_passes_prefix_mode(tmp_tree):
    _append_rows(tmp_tree / GAPS, N_APPENDED)
    assert (tmp_tree / GAPS).read_bytes().count(b"\n") == _record()["files"][GAPS]["old_lines"] + N_APPENDED == 1872
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_NO_DETECTOR and not any(line.startswith("FAIL") for line in report), report
    assert any(line.startswith("ok") and GAPS in line for line in report), report


@needs_cut
def test_extended_ledger_prefix_matches_git_show_of_the_cut_and_exits_zero(tmp_tree):
    _append_rows(tmp_tree / GAPS, N_APPENDED)
    code, report = vc.verify(tmp_tree, _record(), "prefix", git_repo=REPO)
    assert code == vc.EXIT_OK, report


@needs_cut
def test_extended_ledger_rewritten_byte_is_caught_by_the_git_side_even_with_a_forged_record(tmp_tree):
    _append_rows(tmp_tree / GAPS, N_APPENDED)
    _flip_one_byte(tmp_tree / GAPS, 777)
    forged = _record()
    pre = (tmp_tree / GAPS).read_bytes()[: forged["files"][GAPS]["old_bytes"]]
    m = vc.measure(pre)
    forged["files"][GAPS].update(old_lines=m["lines"], old_md5=m["md5"])
    code, report = vc.verify(tmp_tree, forged, "prefix", git_repo=REPO)
    assert code == vc.EXIT_MISMATCH and any("git show" in line and line.startswith("FAIL") for line in report), report


def test_exact_mode_on_the_cut_plus_one_appended_row_fails_exact_and_passes_prefix(tmp_tree):
    _append_rows(tmp_tree / GAPS, 1)
    code, report = vc.verify(tmp_tree, _record(), "exact", use_git=False)
    assert code == vc.EXIT_MISMATCH and any(line.startswith("FAIL") and GAPS in line for line in report), report
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code == vc.EXIT_NO_DETECTOR and not any(line.startswith("FAIL") for line in report), report


def test_prefix_mode_does_not_check_the_register(tmp_tree):
    _flip_one_byte(tmp_tree / REGISTER, 9)
    code, report = vc.verify(tmp_tree, _record(), "prefix", use_git=False)
    assert code != vc.EXIT_MISMATCH, report
    assert any(line.startswith("SKIP") and REGISTER in line for line in report)


# ---- permanent real-tree check: the ledgers' cut rows are intact (append-only) ---------------------

def test_real_ledgers_still_begin_with_the_cut_rows_byte_for_byte():
    code, report = vc.verify(REPO, _record(), "prefix", use_git=False)
    assert code in (vc.EXIT_NO_DETECTOR, vc.EXIT_OK), report
    assert not any(line.startswith("FAIL") for line in report), report
    # an empty files map, or a regression that emits no comparison, must not pass by having nothing to fail
    assert any(line.startswith("ok") for line in report), f"no comparison was made: {report}"


def test_real_ledgers_prefix_has_the_recorded_lines_bytes_and_md5_independently_of_the_verifier():
    """The permanent real-tree check, written without the verifier: however many rows were appended since, the
    first `old_bytes` bytes of each append-only ledger are the cut (`old_lines` lines, `old_md5`)."""
    for rel in (GAPS, CERTS):
        rec = _record()["files"][rel]
        data = (REPO / rel).read_bytes()
        assert len(data) >= rec["old_bytes"], f"{rel} is shorter than the cut: rows were removed"
        pre = data[: rec["old_bytes"]]
        assert pre.endswith(b"\n") and pre.count(b"\n") == rec["old_lines"], rel
        assert hashlib.md5(pre).hexdigest() == rec["old_md5"], f"{rel}: a historical row was rewritten"


@needs_cut
def test_real_tree_prefix_matches_git_show_of_the_cut():
    code, report = vc.verify(REPO, _record(), "prefix", git_repo=REPO)
    assert code == vc.EXIT_OK, report


def test_cli_exit_code_follows_verify(tmp_tree, capsys):
    rc = vc.main(["--root", str(tmp_tree), "--no-git", "--cutover", str(CUTOVER)])
    assert rc == vc.EXIT_NO_DETECTOR
    _flip_one_byte(tmp_tree / GAPS, 3)
    assert vc.main(["--root", str(tmp_tree), "--no-git", "--cutover", str(CUTOVER)]) == vc.EXIT_MISMATCH


# ---- review fixes: malformed record entries, informational fields -------------------------------

@pytest.mark.parametrize("key", ["old_lines", "old_bytes", "old_md5"])
def test_a_file_entry_missing_an_old_value_is_a_usage_error_not_a_traceback(tmp_tree, key):
    rec = _record()
    del rec["files"][GAPS][key]
    code, report = vc.verify(tmp_tree, rec, "exact", use_git=False)
    assert code == vc.EXIT_USAGE, report
    assert key in report[0] and GAPS in report[0]


def test_a_non_object_file_entry_is_a_usage_error(tmp_tree):
    rec = _record()
    rec["files"][CERTS] = "not an object"
    assert vc.verify(tmp_tree, rec, "prefix", use_git=False)[0] == vc.EXIT_USAGE


def test_cli_reports_usage_error_exit_2_for_an_incomplete_record(tmp_tree, tmp_path):
    rec = _record()
    del rec["files"][REGISTER]["old_md5"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(rec), encoding="utf-8")
    assert vc.main(["--root", str(tmp_tree), "--no-git", "--cutover", str(bad)]) == vc.EXIT_USAGE


def test_record_documents_that_main_sha_and_the_repoint_flag_are_informational():
    rec = _record()
    assert "INFORMATIONAL" in rec["_doc"] and "main_sha" in rec["_doc"] and "nikasha_ref_repointed" in rec["_doc"]


@needs_cut
def test_verified_run_says_main_sha_and_the_repoint_flag_are_informational(tmp_tree):
    code, report = vc.verify(tmp_tree, _record(), "exact", git_repo=REPO)
    assert code == vc.EXIT_OK, report
    assert any(line.startswith("info") and "INFORMATIONAL" in line and "main_sha" in line
               and "nikasha_ref_repointed" in line for line in report), report
