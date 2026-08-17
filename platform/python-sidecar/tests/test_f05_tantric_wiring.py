"""Focused F05 regression tests for tantric remedy rebuild wiring."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from brahmagyan import l0_remedy_loader
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers import bg_remedies


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
