"""Unit tests for ci_db_test_coverage_audit.py — small synthetic fixtures only,
no database, no network."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ci_db_test_coverage_audit as audit  # noqa: E402


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture()
def tree(tmp_path):
    """A minimal repo: platform/python-sidecar/tests with a conftest carrying a DB
    fixture chain, plus .github/workflows/ci.yml."""
    root = tmp_path
    _write(root, "platform/python-sidecar/tests/conftest.py", '''
import psycopg
import pytest

@pytest.fixture()
def db_conn():
    c = psycopg.connect("postgresql://x/y")
    yield c
    c.close()

@pytest.fixture()
def wrapped(db_conn):
    return db_conn

@pytest.fixture()
def pure():
    return 42
''')
    _write(root, "platform/python-sidecar/tests/test_uses_db_fixture.py",
           "def test_one(db_conn):\n    assert db_conn\n")
    _write(root, "platform/python-sidecar/tests/test_uses_wrapped.py",
           "def test_one(wrapped):\n    assert wrapped\n")
    _write(root, "platform/python-sidecar/tests/test_pure.py",
           "def test_one(pure):\n    assert pure == 42\n")
    _write(root, "platform/python-sidecar/tests/test_direct.py",
           "import psycopg\ndef test_one():\n    psycopg.connect('postgresql://x/y')\n")
    _write(root, "platform/python-sidecar/tests/test_monkeypatched_away.py",
           "import psycopg\n"
           "def test_one(monkeypatch):\n"
           "    monkeypatch.setattr(psycopg, 'connect', boom)  # psycopg.connect must never be reached\n"
           "    monkeypatch.setenv('DATABASE_URL', 'postgresql://unused')\n")
    _write(root, "platform/python-sidecar/tests/test_sibling.py",
           "from .test_direct import test_one as _t\n\ndef test_two():\n    _t()\n")
    _write(root, "platform/python-sidecar/tests/test_skips_not_run.py",
           "import pytest\n"
           "def test_one():\n"
           "    pytest.skip('NOT_RUN: disposable WP6 database unreachable')\n")
    _write(root, ".github/workflows/ci.yml", '''
jobs:
  db-job:
    services:
      postgres:
        image: postgres:16
    steps:
      - name: DB tests
        run: |
          cd platform/python-sidecar
          python -m pytest tests/test_uses_db_fixture.py -q
  plain-job:
    steps:
      - name: plain tests
        run: |
          cd platform/python-sidecar
          python -m pytest tests/test_pure.py tests/test_direct.py -q
  proxy-job:
    steps:
      - name: tunnel
        run: ./cloud-sql-proxy proj:region:amjis-postgres &
      - name: live tests
        run: |
          cd platform/python-sidecar
          python -m pytest tests/test_uses_wrapped.py -q
''')
    return root


def test_discovery_only_test_dirs(tree):
    sidecar = tree / "platform" / "python-sidecar"
    _write(sidecar, "services/x/test_not_in_scope.py", "def test_x():\n    pass\n")
    files = {p.name for p in audit.discover_test_files(sidecar)}
    assert "test_uses_db_fixture.py" in files
    assert "test_not_in_scope.py" not in files        # not under tests/ or __tests__/


def test_conftest_fixture_chain(tree):
    fixtures = audit.analyse_conftest(tree / "platform/python-sidecar/tests/conftest.py")
    assert fixtures["db_conn"][0] and "psycopg" in fixtures["db_conn"][1]
    assert fixtures["wrapped"][0] and "db_conn" in fixtures["wrapped"][1]
    assert not fixtures["pure"][0]


def test_file_verdicts(tree):
    rows, _notes = audit.run_audit(tree)
    by_file = {r["file"]: r for r in rows}
    side = "platform/python-sidecar/tests/"
    # DB-needing, with reasons
    assert "db_conn" in by_file[side + "test_uses_db_fixture.py"]["why"]
    assert "wrapped" in by_file[side + "test_uses_wrapped.py"]["why"]
    assert "direct reference" in by_file[side + "test_direct.py"]["why"]
    assert "sibling" in by_file[side + "test_sibling.py"]["why"]
    assert "NOT_RUN" in by_file[side + "test_skips_not_run.py"]["why"]
    # NOT DB-needing: pure fixture, and machinery that is only monkeypatched away
    assert side + "test_pure.py" not in by_file
    assert side + "test_monkeypatched_away.py" not in by_file


def test_ci_coverage_classification(tree):
    rows, _notes = audit.run_audit(tree)
    by_file = {r["file"]: r for r in rows}
    side = "platform/python-sidecar/tests/"
    # postgres service job → with DB
    assert "db-job" in by_file[side + "test_uses_db_fixture.py"]["ci_db"]
    # cloud-sql-proxy elsewhere in the job → job-level DB infrastructure
    assert "proxy-job" in by_file[side + "test_uses_wrapped.py"]["ci_db"]
    # executed in a plain job → NEVER with a database, and the silent-skip column names it
    direct = by_file[side + "test_direct.py"]
    assert direct["ci_db"] == "NEVER"
    assert "plain-job" in direct["ci_no_db"]
    # never executed at all
    assert by_file[side + "test_sibling.py"]["ci_no_db"] == ""


def test_check_fails_on_unexcluded_never(tree):
    rows, _ = audit.run_audit(tree)
    assert audit.check(rows) == 1
    audit.EXCLUSIONS.clear()
    for r in rows:
        if r["ci_db"] == "NEVER":
            audit.EXCLUSIONS[r["file"]] = "test exclusion"
    assert audit.check(rows) == 0
    audit.EXCLUSIONS.clear()


def test_pytest_targets_tracks_cd():
    targets, dynamic = audit._pytest_targets(
        "cd platform/python-sidecar\npython -m pytest tests/a.py tests/b.py -q\n",
        ".", Path("/nonexistent"))
    assert targets == ["platform/python-sidecar/tests/a.py",
                       "platform/python-sidecar/tests/b.py"]
    assert not dynamic
    _t, dynamic = audit._pytest_targets("pytest ${FILES[@]} -q", ".", Path("/nonexistent"))
    assert dynamic



def test_integration_marker_distinguishes_deselected_from_unmarked():
    assert audit.integration_marker("import pytest\npytestmark = pytest.mark.integration\n") == "module"
    assert audit.integration_marker("import pytest\npytestmark = [pytest.mark.slow, pytest.mark.integration]\n") == "module"
    assert audit.integration_marker("import pytest\n@pytest.mark.integration\ndef test_x(): ...\n") == "some"
    assert audit.integration_marker("import pytest\ndef test_x(): ...\n") == ""
    assert audit.integration_marker("# pytest.mark.integrations are described elsewhere\n") == ""      # the word boundary: `integrations` is not the marker


def test_the_marker_reaches_the_tsv_and_the_markdown_summary(tree):
    _write(tree, "platform/python-sidecar/tests/test_marked.py", """
import psycopg, pytest
pytestmark = pytest.mark.integration
def test_a():
    psycopg.connect("postgresql://x")
""")
    rows, notes = audit.run_audit(tree)
    marked = [r for r in rows if r["file"].endswith("test_marked.py")]
    assert marked and marked[0]["integration"] == "module"
    tsv = audit.to_tsv(rows).splitlines()
    assert tsv[0].endswith("\tintegration_marker")
    assert any(line.startswith("platform/python-sidecar/tests/test_marked.py") and line.endswith("\tmodule") for line in tsv)
    md = audit.to_markdown(rows, notes)
    assert "carry the `integration` marker" in md
