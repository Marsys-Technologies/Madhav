"""Regression coverage for the complete bg_doshas replacement contract."""

import inspect

from brahmagyan.l0_doshas import seed_doshas


def test_writer_replaces_all_owned_projections() -> None:
    source = inspect.getsource(seed_doshas)

    assert "DELETE FROM reference_doshas" in source
    assert "DELETE FROM brahma_dosha_catalog" in source
    assert "DELETE FROM brahma_ontology WHERE entity_class = 'dosha'" in source
    assert "ON CONFLICT" not in source
