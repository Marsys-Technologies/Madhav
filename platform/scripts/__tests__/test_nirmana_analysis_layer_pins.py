from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO / "platform/scripts/generate/nirmana_analysis_layer_pins.py"
SPEC = importlib.util.spec_from_file_location("nirmana_analysis_layer_pins", MODULE_PATH)
assert SPEC and SPEC.loader
pins_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pins_module)

CURRENT_PINS = json.loads(pins_module.PINS_PATH.read_text(encoding="utf-8"))
CURRENT_INVENTORY = json.loads(
    pins_module.WRITER_DIGESTS_PATH.read_text(encoding="utf-8")
)["writers"]


def rewind_layer(document: dict, layer: str) -> dict:
    """Reconstruct one predecessor from the immutable packaged history."""
    result = copy.deepcopy(document)
    archived = result["history"][layer].pop()
    result["layers"][layer] = archived["pin"]
    return result


def replace_layer_writers(
    base: dict[str, str], layer: str, writers: dict[str, str]
) -> dict[str, str]:
    """Return one complete inventory with exactly one packaged layer replaced."""
    prefix = pins_module.LAYER_PREFIX[layer]
    result = {
        key: value for key, value in copy.deepcopy(base).items() if not key.startswith(prefix)
    }
    result.update(writers)
    return result


# Unit fixtures must survive GitHub's squash topology and branch deletion.  The
# accepted predecessor bytes are already embedded in the v2 pin document, so do
# not make test collection depend on source-branch objects that protected main
# intentionally cannot retain as ancestors.
ACCEPTED_PINS = rewind_layer(rewind_layer(CURRENT_PINS, "L1"), "L2")
LEGACY_PINS = copy.deepcopy(ACCEPTED_PINS)
LEGACY_PINS["version"] = pins_module.LEGACY_PINS_VERSION
LEGACY_PINS["layers"]["L2"] = copy.deepcopy(CURRENT_PINS["history"]["L2"][0]["pin"])
LEGACY_PINS.pop("definition_bindings", None)
LEGACY_PINS.pop("history", None)
BASELINE = replace_layer_writers(
    CURRENT_INVENTORY, "L2", CURRENT_PINS["history"]["L2"][0]["writer_digests"]
)
CANDIDATE = replace_layer_writers(
    CURRENT_INVENTORY, "L2", CURRENT_PINS["history"]["L2"][1]["writer_digests"]
)
CANDIDATE = replace_layer_writers(
    CANDIDATE, "L1", CURRENT_PINS["history"]["L1"][-1]["writer_digests"]
)
KSHETRA_SOURCE = "87cc8c9baf894c615e167672c6c7af57a15cf71c"
PRE_KSHETRA_PINS = rewind_layer(CURRENT_PINS, "L3")
PRE_KSHETRA_INVENTORY = replace_layer_writers(
    CURRENT_INVENTORY, "L3", CURRENT_PINS["history"]["L3"][-1]["writer_digests"]
)
L2_CHANGED = sorted(
    asset_id
    for asset_id in set(BASELINE) | set(CANDIDATE)
    if asset_id.startswith("bo_") and BASELINE.get(asset_id) != CANDIDATE.get(asset_id)
)
L2_CLASSIFICATIONS = {
    asset_id: "approved_intentional_and_derived_import_change"
    for asset_id in L2_CHANGED
}


def check_current(
    document: dict | None = None,
    inventory: dict[str, str] | None = None,
) -> list[str]:
    baseline = os.environ.get("NIRMANA_ANALYSIS_PIN_BASELINE_COMMIT")
    delivery = os.environ.get("NIRMANA_ANALYSIS_PIN_DELIVERY_TOPOLOGY") == "1"
    return pins_module.check(
        document or CURRENT_PINS,
        inventory or CURRENT_INVENTORY,
        protected_baseline_commit=baseline,
        delivery_topology=delivery,
    )


@pytest.fixture(autouse=True)
def package_immutable_unit_fixtures(monkeypatch, request) -> None:
    """Exercise old generations from packaged bytes, not disposable side refs."""
    if request.node.name == "test_side_ref_only_historical_snapshot_is_rejected":
        return
    real_require = pins_module._require_reachable_commit
    real_exists = pins_module._commit_exists
    real_inventory = pins_module._inventory_at_commit
    real_pins = pins_module._pins_at_commit
    real_blob_oid = pins_module._blob_oid_at_commit
    real_blob = pins_module._blob_at_commit
    real_validate_artifact = pins_module.validate_artifact_binding

    definition_commit = "5142109f7f219ea860f859e322646f79d875bee8"
    baseline_commit = "c558e60d3267ded79d65fd25f50ee926ce27b75a"
    accepted_commit = "7b1576d59f8300a608fce3acc1d1ec26e8bb3bda"
    pre_kshetra_commit = "6c1a65e23be6176322d7a9ab78e0c291feeec700"

    fixture_pins = {
        definition_commit: LEGACY_PINS,
        baseline_commit: LEGACY_PINS,
        accepted_commit: ACCEPTED_PINS,
        pre_kshetra_commit: PRE_KSHETRA_PINS,
    }
    fixture_inventories = {
        definition_commit: CURRENT_INVENTORY,
        baseline_commit: BASELINE,
        accepted_commit: CANDIDATE,
        pre_kshetra_commit: PRE_KSHETRA_INVENTORY,
        "d2369b888e760e5b8d693328f00683877cbd5f28": CANDIDATE,
        "149f8479ac4e22874aabe9a5e5b340fb86bc16fb": CURRENT_INVENTORY,
        KSHETRA_SOURCE: CURRENT_INVENTORY,
    }
    fixture_commits = set(fixture_pins) | set(fixture_inventories)
    for binding in pins_module.SOURCE_ACCEPTANCE_BINDINGS.values():
        fixture_commits.update(
            {
                binding["reviewed_source_commit"],
                binding["integrated_equivalent_commit"],
                binding["common_base_commit"],
            }
        )

    valid_artifacts: set[tuple[str, str, str, str]] = set()
    for expected in pins_module.EXPECTED_REVIEW_ARTIFACTS.values():
        valid_artifacts.update(
            (item["commit"], item["path"], item["sha256"], item["decision_binding"])
            for item in expected
        )
    for binding in pins_module.SOURCE_ACCEPTANCE_BINDINGS.values():
        for expected in binding["review_artifacts"].values():
            valid_artifacts.update(
                (item["commit"], item["path"], item["sha256"], item["decision_binding"])
                for item in expected
            )
    authority_content: dict[tuple[str, str], bytes] = {}
    for binding in pins_module.AUTHORITY_BINDINGS.values():
        valid_artifacts.add(
            (
                binding["evidence_commit"],
                binding["path"],
                binding["sha256"],
                binding["decision_binding"],
            )
        )
        authority_content[(binding["evidence_commit"], binding["path"])] = (
            f'{binding["decision_binding"]}\n{binding["authority_identity_binding"]}\n'.encode()
        )
        fixture_commits.add(binding["evidence_commit"])

    integrated_oids: dict[tuple[str, str], str] = {}
    for binding in pins_module.SOURCE_ACCEPTANCE_BINDINGS.values():
        integrated_oids.update(
            {
                (binding["integrated_equivalent_commit"], item["path"]): item["blob_oid"]
                for item in binding["reviewed_surface"]
            }
        )

    def require_fixture_or_ancestor(commit: str, label: str) -> None:
        if commit in fixture_commits:
            return
        real_require(commit, label)

    def commit_exists(commit: str) -> bool:
        return commit in fixture_commits or real_exists(commit)

    def inventory_at_commit(commit: str) -> dict[str, str]:
        if commit in fixture_inventories:
            return copy.deepcopy(fixture_inventories[commit])
        return real_inventory(commit)

    def pins_at_commit(commit: str) -> dict:
        if commit in fixture_pins:
            return copy.deepcopy(fixture_pins[commit])
        return real_pins(commit)

    def blob_oid_at_commit(commit: str, path: str) -> str:
        if (commit, path) in integrated_oids:
            return integrated_oids[(commit, path)]
        return real_blob_oid(commit, path)

    def blob_at_commit(commit: str, path: str) -> bytes:
        if (commit, path) in authority_content:
            return authority_content[(commit, path)]
        return real_blob(commit, path)

    def validate_artifact(artifact: dict, label: str) -> None:
        identity = (
            artifact.get("commit"),
            artifact.get("path"),
            artifact.get("sha256"),
            artifact.get("decision_binding"),
        )
        if identity in valid_artifacts:
            return
        if any(identity[:2] == expected[:2] for expected in valid_artifacts):
            raise SystemExit(f"{label} content digest does not match immutable binding")
        real_validate_artifact(artifact, label)

    monkeypatch.setattr(pins_module, "_require_reachable_commit", require_fixture_or_ancestor)
    monkeypatch.setattr(pins_module, "_commit_exists", commit_exists)
    monkeypatch.setattr(pins_module, "_inventory_at_commit", inventory_at_commit)
    monkeypatch.setattr(pins_module, "_pins_at_commit", pins_at_commit)
    monkeypatch.setattr(pins_module, "_blob_oid_at_commit", blob_oid_at_commit)
    monkeypatch.setattr(pins_module, "_blob_at_commit", blob_at_commit)
    monkeypatch.setattr(pins_module, "validate_artifact_binding", validate_artifact)


def admission(classifications: dict[str, str] | None = None) -> dict:
    return pins_module.admit_successor(
        LEGACY_PINS,
        layer="L2",
        previous_writer_digests=BASELINE,
        candidate_writer_digests=CANDIDATE,
        source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
        review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
        authority_decision="DP-SD-018",
        authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
        reason="bounded fixture successor",
        classifications=classifications or L2_CLASSIFICATIONS,
        historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
        definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
    )


def test_successor_archives_complete_predecessor_and_exact_delta() -> None:
    result = admission()
    archived = result["history"]["L2"][0]
    active = result["layers"]["L2"]

    assert result["version"] == pins_module.PINS_VERSION
    assert archived["pin"] == LEGACY_PINS["layers"]["L2"]
    assert archived["writer_digests"] == {
        key: value for key, value in BASELINE.items() if key.startswith("bo_")
    }
    assert active["supersedes_generation_id"] == archived["generation_id"]
    assert archived["superseded_by_generation_id"] == active["generation_id"]
    assert active["admission"]["changed_assets"] == L2_CHANGED
    assert active["admission"]["delta_classifications"] == L2_CLASSIFICATIONS
    assert result["definition_bindings"] == pins_module.build_definition_bindings(
        "5142109f7f219ea860f859e322646f79d875bee8"
    )
    assert all(
        result["layers"][layer] == LEGACY_PINS["layers"][layer]
        for layer in pins_module.LAYER_PREFIX
        if layer != "L2"
    )


def test_successor_rejects_missing_wrong_layer_and_unapproved_classification() -> None:
    missing = dict(L2_CLASSIFICATIONS)
    missing.pop(L2_CHANGED[0])
    with pytest.raises(SystemExit, match="cover exactly"):
        admission(missing)

    wrong_layer = dict(L2_CLASSIFICATIONS)
    wrong_layer["ga_positions"] = "derived_import_change"
    with pytest.raises(SystemExit, match="cover exactly"):
        admission(wrong_layer)

    foreign = dict(L2_CLASSIFICATIONS)
    foreign[L2_CHANGED[0]] = "unapproved_foreign_source"
    with pytest.raises(SystemExit, match="cannot be admitted"):
        admission(foreign)

    unsupported = dict(L2_CLASSIFICATIONS)
    unsupported[L2_CHANGED[0]] = "invented_bypass"
    with pytest.raises(SystemExit, match="unsupported delta classifications"):
        admission(unsupported)


def test_nonexistent_authority_and_review_commits_are_rejected() -> None:
    with pytest.raises(SystemExit, match="not bound"):
        pins_module.admit_successor(
            LEGACY_PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
            authority_decision="DP-SD-018",
            authority_commit="0" * 40,
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
        )

    nonexistent = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"][0])
    nonexistent["commit"] = "0" * 40
    with pytest.raises(SystemExit, match="must be an ancestor of HEAD"):
        pins_module.validate_artifact_binding(nonexistent, "fixture review")


def test_wrong_acceptance_artifact_or_content_digest_is_rejected() -> None:
    wrong_layer_artifact = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L3"])
    with pytest.raises(SystemExit, match="required acceptance artifacts"):
        pins_module.admit_successor(
            LEGACY_PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=wrong_layer_artifact,
            authority_decision="DP-SD-018",
            authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
        )

    wrong_digest = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"][0])
    wrong_digest["sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="content digest"):
        pins_module.validate_artifact_binding(wrong_digest, "fixture review")


@pytest.mark.parametrize("omitted_artifact_index", [0, 1])
def test_l2_requires_both_acceptance_artifacts(
    omitted_artifact_index: int,
) -> None:
    incomplete = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"])
    incomplete.pop(omitted_artifact_index)

    with pytest.raises(SystemExit, match="required acceptance artifacts"):
        pins_module.admit_successor(
            LEGACY_PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=incomplete,
            authority_decision="DP-SD-018",
            authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
        )


def test_definition_binding_rejects_wrong_digest_overlap_and_retired_sweep_loss() -> None:
    wrong_digest = copy.deepcopy(CURRENT_PINS)
    wrong_digest["definition_bindings"]["L3"]["membership_sha256"] = "0" * 64
    assert any(
        "definition membership digest" in failure
        for failure in check_current(wrong_digest)
    )

    overlap = copy.deepcopy(CURRENT_PINS)
    overlap["layers"]["L3"]["non_writer_assets"].append("ka_sangam")
    overlap["layers"]["L3"]["non_writer_assets"].sort()
    assert any(
        "writer-disjoint" in failure
        for failure in check_current(overlap)
    )

    retired_removed = copy.deepcopy(CURRENT_PINS)
    retired_removed["layers"]["L3"]["non_writer_assets"] = []
    retired_removed["layers"]["L3"]["receipt_count"] = 22
    assert any(
        "active membership differs from immutable definition" in failure
        for failure in check_current(retired_removed)
    )


def test_historical_pin_and_writer_rewrites_are_rejected() -> None:
    rewritten_writers = copy.deepcopy(CURRENT_PINS)
    rewritten_writers["history"]["L2"][0]["writer_digests"]["bo_anveshana"] = "0" * 64
    failures = check_current(rewritten_writers)
    assert any("protected baseline generation" in failure for failure in failures)

    rewritten_pin = copy.deepcopy(CURRENT_PINS)
    rewritten_pin["history"]["L2"][0]["pin"]["convergence_commit"] = "0" * 40
    failures = check_current(rewritten_pin)
    assert any("protected baseline generation" in failure for failure in failures)


def test_fabricated_unversioned_convergence_identity_is_rejected() -> None:
    fabricated = copy.deepcopy(CURRENT_PINS)
    fabricated["layers"]["L5"]["convergence_commit"] = "0" * 40
    failures = check_current(fabricated)
    assert any(
        "unversioned active pin differs from immutable definition snapshot" in failure
        for failure in failures
    )


def test_full_two_successor_chain_is_valid_and_rewrite_is_detected(monkeypatch) -> None:
    second_source = "1" * 40
    second_snapshot = "7b1576d59f8300a608fce3acc1d1ec26e8bb3bda"
    second_inventory = dict(CANDIDATE)
    second_inventory["bo_anveshana"] = "f" * 64
    real_inventory_at_commit = pins_module._inventory_at_commit
    real_pins_at_commit = pins_module._pins_at_commit
    real_commit_exists = pins_module._commit_exists

    def inventory_at_commit(commit: str) -> dict[str, str]:
        if commit == second_source:
            return second_inventory
        if commit == second_snapshot:
            return CANDIDATE
        return real_inventory_at_commit(commit)

    def pins_at_commit(commit: str) -> dict:
        if commit == second_snapshot:
            return ACCEPTED_PINS
        return real_pins_at_commit(commit)

    def commit_exists(commit: str) -> bool:
        return commit in {second_source, second_snapshot} or real_commit_exists(commit)

    monkeypatch.setattr(pins_module, "_inventory_at_commit", inventory_at_commit)
    monkeypatch.setattr(pins_module, "_pins_at_commit", pins_at_commit)
    monkeypatch.setattr(pins_module, "_commit_exists", commit_exists)
    monkeypatch.setitem(
        pins_module.AUTHORIZED_SOURCE_COMMITS["DP-SD-018"],
        "L2",
        frozenset({"d2369b888e760e5b8d693328f00683877cbd5f28", second_source}),
    )
    two_successors = pins_module.admit_successor(
        ACCEPTED_PINS,
        layer="L2",
        previous_writer_digests=CANDIDATE,
        candidate_writer_digests=second_inventory,
        source_commit=second_source,
        review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
        authority_decision="DP-SD-018",
        authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
        reason="second bounded fixture successor",
        classifications={"bo_anveshana": "approved_intentional_change"},
        historical_snapshot_commit=second_snapshot,
        definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
    )
    protected_baseline = "7b1576d59f8300a608fce3acc1d1ec26e8bb3bda"
    assert pins_module.check(
        two_successors,
        second_inventory,
        protected_baseline_commit=protected_baseline,
    ) == []

    two_successors["history"]["L2"][1]["pin"]["convergence_commit"] = "0" * 40
    failures = pins_module.check(
        two_successors,
        second_inventory,
        protected_baseline_commit=protected_baseline,
    )
    assert any("protected baseline" in failure for failure in failures)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["layers"]["L2"]["admission"].update(
                source_commit="0" * 40
            ),
            "source commit",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                generation_id="l2:stale:generation"
            ),
            "generation id",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                writer_inventory_sha256="0" * 64
            ),
            "writer_inventory_sha256 is stale",
        ),
    ],
)
def test_check_rejects_wrong_source_stale_generation_and_hash(
    mutate,
    message: str,
) -> None:
    result = copy.deepcopy(CURRENT_PINS)
    mutate(result)

    failures = check_current(result)

    assert any(message in failure for failure in failures)


EXPECTED_L1_SECURITY_DELTA = [
    "ga_ayurdaya",
    "ga_condition",
    "ga_dashas",
    "ga_nakshatra",
    "ga_panchanga",
    "ga_positions",
    "ga_sade_sati",
    "ga_sensitive",
    "ga_sensitive_degree",
    "ga_strength",
    "ga_structural",
    "ga_tajaka",
    "ga_vargas",
    "ga_yoga",
]
EXPECTED_L2_SECURITY_DELTA = [
    "bo_arudha",
    "bo_bimba",
    "bo_grounding",
    "bo_karanajala",
    "bo_laksana",
    "bo_laksana_rerank",
    "bo_nakshatra_semantic",
    "bo_pramana_mapa",
    "bo_samskara",
    "bo_sangati",
    "bo_special_lagna",
    "bo_sudarshana",
    "bo_upaya",
    "bo_vargottama_dhana",
]
SECURITY_SOURCE = "149f8479ac4e22874aabe9a5e5b340fb86bc16fb"
DP019_SOURCE = "64facb9763d13eece7098b5b24cc03dfb8e3ba81"


def test_current_successors_are_exact_and_preserve_prior_bytes() -> None:
    assert check_current() == []
    for layer, expected_delta in (
        ("L1", EXPECTED_L1_SECURITY_DELTA),
        ("L2", EXPECTED_L2_SECURITY_DELTA),
    ):
        active = CURRENT_PINS["layers"][layer]
        prior = ACCEPTED_PINS["layers"][layer]
        assert active["admission"]["source_commit"] == SECURITY_SOURCE
        assert active["admission"]["changed_assets"] == expected_delta
        assert active["admission"]["source_acceptance"] == (
            pins_module._source_acceptance_public(
                pins_module.SOURCE_ACCEPTANCE_BINDINGS[SECURITY_SOURCE]
            )
        )
        assert CURRENT_PINS["history"][layer][:-1] == ACCEPTED_PINS["history"][layer]
        assert CURRENT_PINS["history"][layer][-1]["pin"] == prior
        assert CURRENT_PINS["history"][layer][-1]["writer_digests"] == (
            pins_module.layer_writer_slice(CANDIDATE, pins_module.LAYER_PREFIX[layer])
        )
        assert active["supersedes_generation_id"] == prior["generation_id"]

    assert CURRENT_PINS["layers"]["L1"]["admission"]["delta_classifications"] == {
        asset_id: (
            "approved_intentional_and_derived_import_change"
            if asset_id in {"ga_condition", "ga_dashas"}
            else "derived_import_change"
        )
        for asset_id in EXPECTED_L1_SECURITY_DELTA
    }
    assert set(
        CURRENT_PINS["layers"]["L2"]["admission"]["delta_classifications"].values()
    ) == {"derived_import_change"}
    for layer in ("L0", "L4", "L5"):
        assert CURRENT_PINS["layers"][layer] == ACCEPTED_PINS["layers"][layer]
        assert CURRENT_PINS["history"][layer] == ACCEPTED_PINS["history"][layer]

    l3_active = CURRENT_PINS["layers"]["L3"]
    l3_prior = PRE_KSHETRA_PINS["layers"]["L3"]
    assert l3_active["admission"]["source_commit"] == KSHETRA_SOURCE
    assert l3_active["admission"]["authority_decision"] == "DP-SD-019"
    assert l3_active["admission"]["changed_assets"] == ["ka_kshetra"]
    assert l3_active["admission"]["delta_classifications"] == {
        "ka_kshetra": "approved_intentional_change",
    }
    assert l3_active["admission"]["source_acceptance"] == (
        pins_module._source_acceptance_public(
            pins_module.SOURCE_ACCEPTANCE_BINDINGS[KSHETRA_SOURCE]
        )
    )
    assert CURRENT_PINS["history"]["L3"][:-1] == PRE_KSHETRA_PINS["history"]["L3"]
    assert CURRENT_PINS["history"]["L3"][-1]["pin"] == l3_prior
    assert CURRENT_PINS["history"]["L3"][-1]["writer_digests"] == (
        pins_module.layer_writer_slice(
            PRE_KSHETRA_INVENTORY, pins_module.LAYER_PREFIX["L3"]
        )
    )
    assert l3_active["supersedes_generation_id"] == l3_prior["generation_id"]


def test_delivery_topology_requires_protected_baseline() -> None:
    failures = pins_module.check(
        CURRENT_PINS,
        CURRENT_INVENTORY,
        delivery_topology=True,
    )
    assert "delivery topology requires a protected baseline commit" in failures


def test_protected_baseline_rejects_packaged_history_rewrite() -> None:
    baseline = os.environ.get("NIRMANA_ANALYSIS_PIN_BASELINE_COMMIT")
    assert baseline, "CI must provide the protected pin baseline"
    rewritten = copy.deepcopy(CURRENT_PINS)
    rewritten["history"]["L3"][0]["writer_digests"]["ka_avadhi"] = "0" * 64
    failures = pins_module.check(
        rewritten,
        CURRENT_INVENTORY,
        protected_baseline_commit=baseline,
    )
    assert any("protected baseline generation" in failure for failure in failures)


def test_protected_baseline_rejects_history_metadata_rewrite() -> None:
    baseline = os.environ.get("NIRMANA_ANALYSIS_PIN_BASELINE_COMMIT")
    assert baseline, "CI must provide the protected pin baseline"
    rewritten = copy.deepcopy(CURRENT_PINS)
    rewritten["history"]["L3"][0]["historical_snapshot_commit"] = "0" * 40
    failures = pins_module.check(
        rewritten,
        CURRENT_INVENTORY,
        protected_baseline_commit=baseline,
    )
    assert any("protected baseline history entry" in failure for failure in failures)


def test_security_source_surface_binding_rederives_exact_equivalence() -> None:
    binding = pins_module.SOURCE_ACCEPTANCE_BINDINGS[SECURITY_SOURCE]
    paths, digest = pins_module._source_surface_mapping(
        binding["reviewed_surface"],
        binding["integrated_equivalent_commit"],
    )
    assert len(paths) == 23
    assert digest == binding["source_surface_sha256"]


def test_post_integration_source_acceptance_rederives_route_repair() -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    binding = pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source]
    paths, digest = pins_module._source_surface_mapping(
        binding["reviewed_surface"], binding["integrated_equivalent_commit"]
    )
    assert paths == [
        "platform/scripts/data-plane-migration-attestation.ts",
        "platform/scripts/data-plane-ownership-preflight.ts",
        "platform/scripts/data-plane-protected-cutover.ts",
        "platform/tests/unit/data_plane_security_contract.test.ts",
    ]
    assert digest == "89fdc9c7ef43031faffcf7e9d633114bed4892e7b401703d7d9bb951bcb2dde1"
    pins_module.validate_post_integration_source_acceptance_bindings()


def test_dp019_source_surface_binding_rederives_exact_equivalence() -> None:
    binding = pins_module.SOURCE_ACCEPTANCE_BINDINGS[DP019_SOURCE]
    paths, digest = pins_module._source_surface_mapping(
        binding["reviewed_surface"],
        binding["integrated_equivalent_commit"],
    )
    assert paths == [
        "platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py",
        "platform/python-sidecar/tests/l3/test_ka_yojaka_multidomain.py",
    ]
    assert digest == binding["source_surface_sha256"]


def test_kshetra_source_surface_binding_rederives_exact_equivalence() -> None:
    binding = pins_module.SOURCE_ACCEPTANCE_BINDINGS[KSHETRA_SOURCE]
    paths, digest = pins_module._source_surface_mapping(
        binding["reviewed_surface"],
        binding["integrated_equivalent_commit"],
    )
    assert paths == [
        "platform/python-sidecar/services/ka_kshetra/dhara_null.py",
        "platform/python-sidecar/services/ka_kshetra/dhara_null_vec.py",
        "platform/python-sidecar/services/ka_kshetra/layer1.py",
        "platform/python-sidecar/services/ka_kshetra/tests/test_dhara_null.py",
        "platform/python-sidecar/services/ka_kshetra/tests/test_dhara_null_vectorized.py",
        "platform/python-sidecar/services/ka_kshetra/tests/test_stage1_symbolization.py",
    ]
    assert digest == "8eb4cce85bdc32434cad92d649837a1fcb80e63e941efedc9838c6e5e8c62cbe"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["layers"]["L1"]["admission"].pop(
                "source_acceptance"
            ),
            "missing or has the wrong source-acceptance binding",
        ),
        (
            lambda document: document["layers"]["L1"]["admission"][
                "source_acceptance"
            ].update(reviewed_source_commit="0" * 40),
            "missing or has the wrong source-acceptance binding",
        ),
        (
            lambda document: document["layers"]["L2"]["admission"][
                "source_acceptance"
            ].update(integrated_equivalent_commit="0" * 40),
            "missing or has the wrong source-acceptance binding",
        ),
        (
            lambda document: document["layers"]["L2"]["admission"].update(
                review_artifacts=[]
            ),
            "required acceptance artifacts",
        ),
        (
            lambda document: document["layers"]["L2"]["admission"][
                "review_artifacts"
            ][0].update(sha256="0" * 64),
            "required acceptance artifacts",
        ),
    ],
)
def test_security_successor_rejects_omitted_or_wrong_bindings(mutate, message: str) -> None:
    result = copy.deepcopy(CURRENT_PINS)
    mutate(result)
    failures = check_current(result)
    assert any(message in failure for failure in failures)


def test_security_admission_rejects_wrong_or_omitted_review_artifact() -> None:
    expected = pins_module.SOURCE_ACCEPTANCE_BINDINGS[SECURITY_SOURCE][
        "review_artifacts"
    ]["L1"]
    classifications = {
        asset_id: (
            "approved_intentional_and_derived_import_change"
            if asset_id in {"ga_condition", "ga_dashas"}
            else "derived_import_change"
        )
        for asset_id in EXPECTED_L1_SECURITY_DELTA
    }
    for invalid in ([], copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L1"])):
        with pytest.raises(SystemExit, match="required acceptance artifacts"):
            pins_module.admit_successor(
                ACCEPTED_PINS,
                layer="L1",
                previous_writer_digests=CANDIDATE,
                candidate_writer_digests=CURRENT_INVENTORY,
                source_commit=SECURITY_SOURCE,
                review_artifacts=invalid,
                authority_decision="DP-SD-018",
                authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
                reason="security fixture",
                classifications=classifications,
                historical_snapshot_commit="7b1576d59f8300a608fce3acc1d1ec26e8bb3bda",
                definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
            )

    assert expected == CURRENT_PINS["layers"]["L1"]["admission"]["review_artifacts"]


def test_side_ref_only_historical_snapshot_is_rejected() -> None:
    document = copy.deepcopy(CURRENT_PINS)
    document["history"]["L1"][-1]["historical_snapshot_commit"] = (
        "8ebb3737cedfd4fde802f30845d94f8e8a641c33"
    )
    failures = pins_module.check(document, CURRENT_INVENTORY)
    assert any("must be an ancestor of HEAD" in failure for failure in failures)


@pytest.mark.parametrize("mutation", ["wrong", "extra", "omitted"])
def test_reviewed_surface_rejects_wrong_extra_or_omitted_paths(
    monkeypatch, mutation: str
) -> None:
    binding = copy.deepcopy(pins_module.SOURCE_ACCEPTANCE_BINDINGS[SECURITY_SOURCE])
    surface = binding["reviewed_surface"]
    if mutation == "wrong":
        surface[0]["path"] = "CLAUDE.md"
    elif mutation == "extra":
        surface.append(
            {
                "path": "CLAUDE.md",
                "blob_oid": "f" * 40,
            }
        )
        surface.sort(key=lambda item: item["path"])
    else:
        surface.pop()
    monkeypatch.setitem(pins_module.SOURCE_ACCEPTANCE_BINDINGS, SECURITY_SOURCE, binding)

    with pytest.raises(SystemExit):
        pins_module.validate_source_acceptance(
            SECURITY_SOURCE, pins_module._source_acceptance_public(binding)
        )


def test_reviewed_surface_rejects_wrong_integrated_blob(monkeypatch) -> None:
    binding = pins_module.SOURCE_ACCEPTANCE_BINDINGS[SECURITY_SOURCE]
    real_blob_oid = pins_module._blob_oid_at_commit
    target = binding["reviewed_surface"][0]["path"]

    def wrong_blob_oid(commit: str, path: str) -> str:
        if commit == binding["integrated_equivalent_commit"] and path == target:
            return "0" * 40
        return real_blob_oid(commit, path)

    monkeypatch.setattr(pins_module, "_blob_oid_at_commit", wrong_blob_oid)
    with pytest.raises(SystemExit, match="integrated source differs"):
        pins_module.validate_source_acceptance(
            SECURITY_SOURCE, pins_module._source_acceptance_public(binding)
        )


def test_every_commit_dereferenced_by_check_is_an_ancestor_of_head(monkeypatch) -> None:
    dereferenced: list[str] = []
    real_require = pins_module._require_reachable_commit

    def record(commit: str, label: str) -> None:
        dereferenced.append(commit)
        real_require(commit, label)

    monkeypatch.setattr(pins_module, "_require_reachable_commit", record)
    assert check_current() == []
    assert dereferenced
    assert all(pins_module._commit_is_ancestor_of_head(commit) for commit in dereferenced)
    assert "da498ebd980cac87796eceb889c7f1c42cfb952b" not in dereferenced
    assert "7f21f27b14a7909424591a530096dc2f5d6e2b13" not in dereferenced
    assert "d2369b888e760e5b8d693328f00683877cbd5f28" not in dereferenced
