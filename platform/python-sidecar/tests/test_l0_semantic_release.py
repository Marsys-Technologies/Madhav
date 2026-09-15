from __future__ import annotations

import pytest

from brahmagyan.graha_vocabulary import norm_graha
from brahmagyan.l0_semantic_release import (
    AmbiguousGrahaIdentity,
    SEMANTIC_RELEASE,
    SEMANTIC_RELEASE_DIGEST,
    UnknownGrahaIdentity,
    graha_subject_code,
    release_digest_for_test,
    resolve_graha_identity,
)


@pytest.mark.parametrize("alias", ["Sun", "Surya", "Sūrya", "Ravi", "SUN"])
def test_sun_aliases_resolve_to_one_released_identity(alias: str) -> None:
    resolved = resolve_graha_identity(alias)
    assert resolved["identity_id"] == "sun"
    assert resolved["canonical_subject_code"] == "SUN"
    assert resolved["semantic_release_id"] == SEMANTIC_RELEASE["semantic_release_id"]


def test_explicit_true_and_mean_nodes_remain_distinct() -> None:
    assert graha_subject_code("Rahu") == "RAH_MEAN"
    assert graha_subject_code("RAH_MEAN") == "RAH_MEAN"
    assert graha_subject_code("RAH_TRUE") == "RAH_TRUE"
    assert graha_subject_code("Ketu") == "KET_MEAN"
    assert graha_subject_code("KET_TRUE") == "KET_TRUE"
    assert resolve_graha_identity("Rahu")["legacy_default"] is True
    assert resolve_graha_identity("RAH_TRUE")["physical_variant_id"] == "true_node"


def test_strict_unknown_and_ambiguous_states_are_detectable() -> None:
    with pytest.raises(UnknownGrahaIdentity):
        graha_subject_code("Pluto")
    with pytest.raises(AmbiguousGrahaIdentity):
        graha_subject_code("lunar node")


def test_legacy_wrapper_preserves_unknown_compatibility_without_node_collapse() -> None:
    assert norm_graha("legacy_private_token") == "LEGACY_PRIVATE_TOKEN"
    assert norm_graha("RAH_TRUE") == "RAH_TRUE"
    assert norm_graha("KET_TRUE") == "KET_TRUE"


def test_release_digest_is_recomputed_and_not_label_only() -> None:
    assert release_digest_for_test() == SEMANTIC_RELEASE_DIGEST
    assert len(SEMANTIC_RELEASE_DIGEST) == 64


def test_aliases_are_unique_outside_explicit_ambiguity_registry() -> None:
    seen: dict[str, str] = {}
    for entity in SEMANTIC_RELEASE["entities"]:
        for alias in entity["aliases"]:
            key = alias.strip().casefold()
            assert key not in seen or seen[key] == entity["identity_id"]
            seen[key] = entity["identity_id"]
    assert set(SEMANTIC_RELEASE["ambiguous_aliases"]).isdisjoint(seen)
