"""Use the scanner's match-scoped tolerance on synthetic password stand-ins; never suppress a file."""
import ast
import re
import subprocess
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
SCANNER = FLEET.parents[3] / "platform/scripts/governance/secret_scan.sh"


def findings(path, tmp_path):
    listed = tmp_path / "scan-files.txt"
    listed.write_text(str(path) + "\n")
    definitions = SCANNER.read_text().split("\nrun_scan() {", 1)[0]
    result = subprocess.run(["/bin/bash", "-c", definitions + '\nREPO_ROOT="$2"\ncollect_findings "$1"',
                             str(SCANNER), str(listed), str(FLEET.parents[3])],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("name", ["test_cards.py", "test_kyctl.py"])
def test_source_bytes_pass_the_scanners_real_patterns(name, tmp_path):
    assert findings(FLEET / "tests" / name, tmp_path) == ""
    negative = tmp_path / "negative.py"
    negative.write_text("PGPASSWORD=" + "unmarked-standin-value" + "\n")
    assert "env_password_assign\t" in findings(negative, tmp_path)


def tolerated(match):
    # Load the real scanner's definitions only, stopping before its file census/main.
    definitions = SCANNER.read_text().split("# File enumeration", 1)[0]
    result = subprocess.run(["/bin/bash", "-c", definitions + '\nis_tolerated "$1" env_password_assign',
                             str(SCANNER), match], capture_output=True, text=True, timeout=30)
    return result.returncode == 0


@pytest.mark.parametrize("name", ["test_cards.py", "test_kyctl.py"])
def test_password_test_standins_use_scanner_placeholders(name):
    tree = ast.parse((FLEET / "tests" / name).read_text())
    matches = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "PGPASSWORD" and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                matches.append("PGPASSWORD=" + node.value.value)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            matches.extend(re.findall("PGPASSWORD" + r"=([^\s]+)", node.value))
    assert matches
    for value in matches:
        match = value if value.startswith("PGPASSWORD=") else "PGPASSWORD=" + value
        assert tolerated(match), name + ": synthetic stand-in is not marked as a scanner placeholder"
    assert not tolerated("PGPASSWORD=" + "synthetic-live-like-value"), "negative: scanner must still reject unmarked values"
