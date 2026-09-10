"""Earned row-count contract for the two co-writers of brahma_class_priors."""
from __future__ import annotations

from brahmagyan import l0_class_priors
from brahmagyan.l0_class_priors import seed_class_priors
from pipeline.orchestrator.writers import bg_class_priors


def test_class_prior_writer_owns_exactly_171_version_1_rows() -> None:
    expected = (
        len(l0_class_priors.CLASS_ROWS)
        + len(l0_class_priors.SUBSYSTEM_ROWS)
        + len(l0_class_priors.TRADITION_ROWS)
        + len(l0_class_priors.VARGA_ROWS)
        + len(l0_class_priors.GRAHA_DOMAIN_ROWS)
    )
    assert expected == 171
    assert l0_class_priors.PRIOR_VERSION == "1.0"
    assert seed_class_priors(None, dry_run=True) == {"brahma_class_priors": 171}


def test_writer_and_seed_document_the_current_24_class_contract() -> None:
    assert len(l0_class_priors.CLASS_ROWS) == 24
    assert "171 rows" in (l0_class_priors.__doc__ or "")
    assert "171 rows" in (bg_class_priors.__doc__ or "")
