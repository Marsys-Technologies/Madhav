"""check_no_new_ayanamsha_literal_lists: finds >=3-of-five literals, flags new files and stale allowlist entries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_no_new_ayanamsha_literal_lists as g  # noqa: E402

L = '["lahiri_chitrapaksha", "true_chitra", "krishnamurti"]'


def test_detects_list_tuple_set_and_dict_literals():
    assert g.literal_lines(f"A = {L}\n") == [1]
    assert g.literal_lines('A = ("lahiri_chitrapaksha", "true_chitra", "raman")\n') == [1]
    assert g.literal_lines('A = {"lahiri_chitrapaksha", "raman", "krishnamurti"}\n') == [1]
    assert g.literal_lines('A = {"lahiri_chitrapaksha": 1, "raman": 2, "true_chitra": 3}\n') == [1]


def test_two_ids_or_other_strings_are_not_a_list_of_the_five():
    assert g.literal_lines('A = ["lahiri_chitrapaksha", "true_chitra"]\n') == []
    assert g.literal_lines('A = ["a", "b", "c"]\n') == []
    assert g.literal_lines("def f(:\n") == []                      # syntax error: ignored


def test_check_flags_new_and_stale(tmp_path):
    assert g.check({"a.py": [1]}, ["a.py"]) == []
    new = g.check({"a.py": [1], "b.py": [3]}, ["a.py"])
    assert len(new) == 1 and "NEW local ayanamsha list in b.py" in new[0]
    stale = g.check({"a.py": [1]}, ["a.py", "c.py"])
    assert len(stale) == 1 and "c.py" in stale[0] and "remove it" in stale[0]


def test_exclusions():
    assert g._is_excluded("tests/x.py") and g._is_excluded("pkg/__tests__/x.py")
    assert g._is_excluded("pkg/test_x.py") and g._is_excluded("brahmagyan/ayanamsha_scope.py")
    assert not g._is_excluded("ga_writers/ga_yoga_writer.py")


def test_the_committed_allowlist_matches_the_tree():
    found = g.scan()
    assert g.check(found, g.load_allowlist()) == []
    assert json.loads(g.ALLOWLIST_PATH.read_text())["files"] == sorted(json.loads(g.ALLOWLIST_PATH.read_text())["files"])


def test_cli_main_exit_codes(tmp_path):
    (tmp_path / "w.py").write_text(f"A = {L}\n")
    allow = tmp_path / "allow.json"
    assert g.main(["--root", str(tmp_path), "--allowlist", str(allow), "--write-allowlist"]) == 0
    assert g.main(["--root", str(tmp_path), "--allowlist", str(allow)]) == 0
    (tmp_path / "n.py").write_text(f"B = {L}\n")
    assert g.main(["--root", str(tmp_path), "--allowlist", str(allow)]) == 1
    assert g.main(["--root", str(tmp_path / "missing")]) == 2
