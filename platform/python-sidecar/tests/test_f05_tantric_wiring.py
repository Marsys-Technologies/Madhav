"""Focused F05 regression tests for tantric remedy rebuild wiring."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from brahmagyan import l0_remedy_loader
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers import bg_remedies

# PARIŚEṢA-V4 F-191: the ledger's original wording ("__main__ passes
# file_glob='*.yaml' by default via argparse") does not match the code —
# there is no argparse, and __main__ never passed file_glob at all, so it
# always fell through to load_remedies's '*.yaml' default and loaded all 13
# corpus files (145 rows), 5 of which carry an uncorrected-BPHS-attribution
# F-182 header note. The real fix (below) narrows the __main__ DEFAULT to
# tantric.yaml only, while keeping an explicit --file-glob override for a
# deliberate whole-corpus load.
_SIDECAR_ROOT = Path(l0_remedy_loader.__file__).resolve().parents[1]


def _tantric_row(*, source_text: str = "BPHS") -> str:
    return f"""\
- remedy_id: tantric-test
  planet: Saturn
  domain: health
  category: tantric
  remedy_text: A source-vetted tantric remedy.
  source_text: {source_text}
  source_chapter: Ch. 93
  source_verse: Verse 91
  classical_attestation_text: BPHS attestation.
"""


def test_loader_selects_tantric_file_and_keeps_review_gate(tmp_path: Path, monkeypatch):
    """Selective rebuild input must not bypass the tantric source-review gate."""
    (tmp_path / "tantric.yaml").write_text(
        _tantric_row() + _tantric_row(source_text="uncited modern blog"),
        encoding="utf-8",
    )
    (tmp_path / "unrelated.yaml").write_text(
        "- remedy_id: unrelated\n  category: behavioral\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        l0_remedy_loader,
        "_get_conn",
        lambda: (_ for _ in ()).throw(AssertionError("dry run must not open a DB connection")),
    )

    result = l0_remedy_loader.load_remedies(
        tmp_path,
        dry_run=True,
        file_glob="tantric.yaml",
    )

    assert result["files_processed"] == 1
    assert result["inserted"] == 1
    assert result["review_queued"] == 1
    assert result["category_counts"] == {"tantric": 1}


def test_writer_loads_tantric_file_on_orchestrator_connection_without_transaction_control():
    """F05 must make tantric source rows part of every bg_remedies rebuild."""
    conn = MagicMock()
    ctx = ContextSpec(asset_id="bg_remedies", build_id="f05-test", db_conn=conn)
    seed_counts = {
        "remedies_inserted": 10,
        "remedies_skipped": 2,
        "live_count": 10,
        "total_built": 10,
    }
    tantric_counts = {"inserted": 4, "review_queued": 0}

    with patch.object(bg_remedies, "seed_remedy_corpus", return_value=seed_counts), patch.object(
        bg_remedies.l0_remedy_loader,
        "load_remedies",
        return_value=tantric_counts,
    ) as load_remedies:
        result = bg_remedies.RemediesWriter().run(ctx)

    load_remedies.assert_called_once_with(
        yaml_dir=Path(bg_remedies.__file__).resolve().parents[3] / "brahmagyan" / "remedy_corpus",
        conn=conn,
        dry_run=False,
        file_glob="tantric.yaml",
        manage_transaction=False,
    )
    assert result.rows_inserted == 14
    assert result.rows_skipped == 2
    assert "tantric: 4 inserted / 0 review_queued" in result.notes


def test_actual_tantric_corpus_load_is_gated_and_leaves_writer_transaction_untouched():
    """All four shipped tantric rows are accepted without committing caller state."""
    corpus_dir = Path(l0_remedy_loader.__file__).resolve().parent / "remedy_corpus"

    with patch.object(l0_remedy_loader, "insert_to_corpus") as insert_to_corpus:
        result = l0_remedy_loader.load_remedies(
            corpus_dir,
            conn=object(),
            file_glob="tantric.yaml",
            manage_transaction=False,
        )

    assert result["files_processed"] == 1
    assert result["inserted"] == 4
    assert result["review_queued"] == 0
    assert result["errors"] == 0
    assert result["category_counts"] == {"tantric": 4}
    assert insert_to_corpus.call_count == 4


def test_writer_dry_run_counts_actual_tantric_rows_without_opening_a_connection(monkeypatch):
    """Dry-run proof must exercise the same selective source path without DB access."""
    monkeypatch.setattr(
        l0_remedy_loader,
        "_get_conn",
        lambda: (_ for _ in ()).throw(AssertionError("dry run must not open a DB connection")),
    )
    expected_live = sum(
        1 for row in bg_remedies.build_all_remedies() if row.get("scaffold_status") == "live"
    )

    result = bg_remedies.RemediesWriter().run(
        ContextSpec(asset_id="bg_remedies", build_id="f05-dry-run", db_conn=None, dry_run=True)
    )

    assert result.rows_inserted == expected_live + 4
    assert "tantric: 4 inserted / 0 review_queued" in result.notes


# PARIŚEṢA-V4 F-182-noted files: real entries, but carrying the shared
# "PARIŚEṢA-V4 F-182 / owner ruling R-2" header note pending row-level
# correction under F-23 Lane 4. A casual `__main__` invocation must not
# land these.
_F182_NOTED_FILES = {
    "gemstones.yaml",
    "supplemental_b.yaml",
    "behavioral.yaml",
    "vrata.yaml",
    "yantras.yaml",
}


def _run_loader_cli(*extra_args: str) -> dict:
    """Invoke `python -m brahmagyan.l0_remedy_loader --dry-run [extra_args]`
    as a real subprocess (no DB access, since --dry-run short-circuits
    every INSERT), and parse the printed `Result: {...}` dict."""
    proc = subprocess.run(
        [sys.executable, "-m", "brahmagyan.l0_remedy_loader", "--dry-run", *extra_args],
        capture_output=True,
        text=True,
        cwd=str(_SIDECAR_ROOT),
        timeout=30,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    result_line = next(
        line for line in proc.stdout.splitlines() if line.startswith("Result: ")
    )
    return eval(result_line[len("Result: "):])  # noqa: S307 - trusted subprocess of our own script


class TestF191CliDefaultScope:
    """The ruled fix: __main__'s DEFAULT scope must not reach the 12 non-tantric
    corpus files (5 of which still carry an uncorrected F-182 attribution note)."""

    def test_no_arguments_default_loads_only_tantric_file(self):
        result = _run_loader_cli()

        assert result["files_processed"] == 1
        assert result["category_counts"] == {"tantric": 4}
        assert result["inserted"] == 4

    def test_default_invocation_cannot_see_any_f182_noted_file(self):
        """Direct proof the R-2 exposure is closed: none of the 5 F-182-noted
        files are even opened by a casual `python l0_remedy_loader.py` run."""
        corpus_dir = _SIDECAR_ROOT / "brahmagyan" / "remedy_corpus"
        for fname in _F182_NOTED_FILES:
            assert (corpus_dir / fname).exists(), f"fixture drift: {fname} missing from corpus"

        result = _run_loader_cli()

        # Only tantric.yaml was processed; category_counts has no categories
        # belonging to any F-182-noted file.
        assert result["files_processed"] == 1
        assert set(result["category_counts"]) == {"tantric"}

    def test_explicit_file_glob_star_yaml_still_loads_the_whole_corpus(self):
        """Positive control: the whole-corpus path remains reachable, but only
        as a deliberate, explicit act — not the default."""
        result = _run_loader_cli("--file-glob=*.yaml")

        assert result["files_processed"] == 13
        assert result["inserted"] == 145
        # F-182-noted files' entries were carried through — corpus category
        # totals reflect all 13 files, not just tantric.yaml (contrast the
        # default-scope test above, which sees only {"tantric": 4}).
        assert result["category_counts"] != {"tantric": 4}
        assert sum(result["category_counts"].values()) == 145


class TestF191AcceptanceGateScoping:
    """check_acceptance_criteria() must not assert whole-corpus shape (AC1/AC2)
    against a deliberately narrow, non-'*.yaml' load — that would hard-fail a
    successful selective load, the exact §N.8 defect the ruling warns against."""

    def test_default_glob_skips_whole_corpus_gates_instead_of_failing(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        # AC1/AC2 are skipped for a non-whole-corpus glob, so only AC3, AC4,
        # AC5 issue a query, in that order: 0 missing tantric source columns
        # (pass), 5 Saturn/career rows (pass, >=3), 10 queued rows (always pass).
        cur.fetchone.side_effect = [[0], [5], [10]]

        ac = l0_remedy_loader.check_acceptance_criteria(conn=conn, file_glob="tantric.yaml")

        assert ac["ac1_total_rows"]["pass"] is True
        assert ac["ac1_total_rows"].get("skipped") is True
        assert ac["ac2_distinct_categories"]["pass"] is True
        assert ac["ac2_distinct_categories"].get("skipped") is True
        assert ac["overall"] == "PASS"

    def test_whole_corpus_glob_still_asserts_ac1_and_ac2(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        # Simulate a corpus that fails both whole-corpus gates: 5 rows, 1 category.
        cur.fetchone.side_effect = [[5], [1], [0], [0], [0]]

        ac = l0_remedy_loader.check_acceptance_criteria(conn=conn, file_glob="*.yaml")

        assert ac["ac1_total_rows"]["pass"] is False
        assert ac["ac2_distinct_categories"]["pass"] is False
        assert ac["overall"] == "FAIL"
