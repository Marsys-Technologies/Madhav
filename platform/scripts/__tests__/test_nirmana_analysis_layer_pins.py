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

LIVE_PINS = json.loads(pins_module.PINS_PATH.read_text(encoding="utf-8"))
LIVE_INVENTORY = json.loads(
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


# LIVE_* is the committed document, which now carries the L0-repair successors
# (PR #2727, decision NATIVE-2026-09-24-L0-REPAIR-REPIN) on top of the chain that
# was delivered to protected main. Most tests below assert facts about THAT
# delivered chain, so CURRENT_* is the delivered chain: the live document with the
# three L0-repair successors rewound, and the inventory replaced by the archived
# predecessor slices. The tests at the end of the file assert the repair
# successors themselves against LIVE_*. This follows the file's own convention
# (see PRE_KSHETRA_PINS): rewind, do not weaken.
#
# CAUTION - a rewound document is only a valid `check()` input against a protected
# baseline that PREDATES the repair. Once the repair is on main, every baseline
# carries the repair successors, and checking the rewound document against it
# correctly reports "protected baseline generation ... is absent". So anything that
# asks "does the committed document verify?" must use LIVE_*, never CURRENT_*; the
# rewound CURRENT_* is for assertions ABOUT the earlier chain (indexes, prior bytes,
# and mutation tests that assert on failure text). This bit once: after PR #2727
# merged, two tests below called check_current() with the rewound default and failed
# every PR entering the merge queue while the tool's own --check stayed green.
REPAIR_LAYERS = ("L0", "L2", "L3")
CURRENT_PINS = LIVE_PINS
CURRENT_INVENTORY = LIVE_INVENTORY
for _layer in REPAIR_LAYERS:
    CURRENT_INVENTORY = replace_layer_writers(
        CURRENT_INVENTORY, _layer, CURRENT_PINS["history"][_layer][-1]["writer_digests"]
    )
    CURRENT_PINS = rewind_layer(CURRENT_PINS, _layer)


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


def _baseline_carries_live_generations() -> bool:
    """True when the protected baseline (if any) already carries the live successors."""
    baseline = os.environ.get("NIRMANA_ANALYSIS_PIN_BASELINE_COMMIT")
    if not baseline:
        return True
    try:
        baseline_pins = pins_module._pins_at_commit(baseline)
    except SystemExit:
        return False
    return all(
        baseline_pins.get("layers", {}).get(layer, {}).get("generation_id")
        == LIVE_PINS["layers"][layer].get("generation_id")
        for layer in ("L0", "L2", "L3")
    )


def _require_live_document_verifiable() -> None:
    """Skip, loudly, when the live document cannot be verified from this checkout.

    The one such case: a PR whose base predates the L0-repair successors while its
    tree already contains them. The successors are then NEW relative to the baseline,
    so their evidence commits must be dereferenced, and after a squash merge those
    commits are not ancestors of HEAD. That is not a defect in the pins: the tool's
    own --check fails for the same reason at that step, and the remedy is to update
    the branch from main so the protected baseline carries the successors.
    """
    if _baseline_carries_live_generations():
        return
    source = "7d40f8c706406ee8187eadb5c3930553800a1a4a"
    if pins_module._commit_is_ancestor_of_head(source):
        return
    pytest.skip(
        "PR base predates the L0-repair successors and their source commit is not an "
        "ancestor of HEAD (squash delivery): update the branch from main so the "
        "protected baseline carries them"
    )


@pytest.fixture(autouse=True)
def package_immutable_unit_fixtures(monkeypatch, request) -> None:
    """Exercise old generations from packaged bytes, not disposable side refs."""
    if request.node.name == "test_side_ref_only_historical_snapshot_is_rejected":
        return
    real_require = pins_module._require_reachable_commit
    real_is_ancestor_of_head = pins_module._commit_is_ancestor_of_head
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
    for binding in pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS.values():
        artifact = binding["record_artifact"]
        valid_artifacts.add(
            (
                artifact["commit"],
                artifact["path"],
                artifact["sha256"],
                artifact["decision_binding"],
            )
        )
        fixture_commits.update(
            {
                binding["reviewed_source_commit"],
                binding["integrated_equivalent_commit"],
                binding["common_base_commit"],
                artifact["commit"],
            }
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

    def commit_is_ancestor_of_head(commit: str) -> bool:
        return commit in fixture_commits or real_is_ancestor_of_head(commit)

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
    monkeypatch.setattr(
        pins_module, "_commit_is_ancestor_of_head", commit_is_ancestor_of_head
    )
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
        delivery_topology=(
            os.environ.get("NIRMANA_ANALYSIS_PIN_DELIVERY_TOPOLOGY") == "1"
        ),
    ) == []

    two_successors["history"]["L2"][1]["pin"]["convergence_commit"] = "0" * 40
    failures = pins_module.check(
        two_successors,
        second_inventory,
        protected_baseline_commit=protected_baseline,
        delivery_topology=(
            os.environ.get("NIRMANA_ANALYSIS_PIN_DELIVERY_TOPOLOGY") == "1"
        ),
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
    _require_live_document_verifiable()
    assert check_current(LIVE_PINS, LIVE_INVENTORY) == []
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
    pins_module.validate_post_integration_source_acceptance_bindings(
        delivery_topology=(
            os.environ.get("NIRMANA_ANALYSIS_PIN_DELIVERY_TOPOLOGY") == "1"
        )
    )


def test_post_integration_source_requires_artifact_to_descend_from_reviewed_tip(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    monkeypatch.setattr(pins_module, "validate_artifact_binding", lambda *_: None)
    real_is_ancestor = pins_module._commit_is_ancestor_of_commit
    artifact_commit = pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source][
        "record_artifact"
    ]["commit"]

    def unrelated_lineage(ancestor: str, descendant: str) -> bool:
        if ancestor == source and descendant == artifact_commit:
            return False
        return real_is_ancestor(ancestor, descendant)

    monkeypatch.setattr(
        pins_module, "_commit_is_ancestor_of_commit", unrelated_lineage
    )
    with pytest.raises(SystemExit, match="does not descend"):
        pins_module.validate_post_integration_source_acceptance_bindings()


def test_post_integration_delivery_accepts_squashed_exact_artifact(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    artifact_commit = pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source][
        "record_artifact"
    ]["commit"]
    real_is_ancestor = pins_module._commit_is_ancestor_of_head

    monkeypatch.setattr(
        pins_module,
        "_commit_is_ancestor_of_head",
        lambda commit: False if commit == artifact_commit else real_is_ancestor(commit),
    )

    pins_module.validate_post_integration_source_acceptance_bindings(
        delivery_topology=True
    )
    real_validate_artifact = pins_module.validate_artifact_binding

    def reject_unreachable_artifact(artifact: dict, label: str) -> None:
        if artifact.get("commit") == artifact_commit:
            raise SystemExit(
                f"artifact commit {artifact_commit} must be an ancestor of HEAD"
            )
        real_validate_artifact(artifact, label)

    monkeypatch.setattr(
        pins_module, "validate_artifact_binding", reject_unreachable_artifact
    )
    with pytest.raises(SystemExit, match="must be an ancestor of HEAD"):
        pins_module.validate_post_integration_source_acceptance_bindings()


def test_post_integration_source_rejects_artifact_not_yet_on_protected_baseline(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    artifact_commit = pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source][
        "record_artifact"
    ]["commit"]
    real_is_ancestor = pins_module._commit_is_ancestor_of_head

    monkeypatch.setattr(
        pins_module,
        "_commit_is_ancestor_of_head",
        lambda commit: False if commit == artifact_commit else real_is_ancestor(commit),
    )

    with pytest.raises(SystemExit, match="protected one-parent delivery"):
        pins_module.validate_post_integration_source_acceptance_bindings(
            protected_baseline_commit="4855fff4af1466719a3eb642a35fa5fa6c8b6379"
        )


def test_post_integration_source_accepts_exact_protected_squash_delivery(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    artifact_commit = pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source][
        "record_artifact"
    ]["commit"]
    real_is_ancestor = pins_module._commit_is_ancestor_of_head

    monkeypatch.setattr(
        pins_module,
        "_commit_is_ancestor_of_head",
        lambda commit: False if commit == artifact_commit else real_is_ancestor(commit),
    )

    pins_module.validate_post_integration_source_acceptance_bindings(
        protected_baseline_commit="8f62b44708a60ab7e5dbb91aa68e2d7e987d7a02"
    )


def test_post_integration_protected_squash_rejects_unbound_artifact(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    binding = copy.deepcopy(
        pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source]
    )
    artifact = binding["record_artifact"]
    delivered = b"status: SECURITY_CLEAR_SOURCE_ACCEPTED\nunbound record\n"
    artifact["sha256"] = pins_module.hashlib.sha256(delivered).hexdigest()
    artifact_path = artifact["path"]
    artifact_commit = artifact["commit"]
    real_is_ancestor = pins_module._commit_is_ancestor_of_head
    real_blob_at_revision = pins_module._blob_at_revision

    monkeypatch.setitem(
        pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS, source, binding
    )
    monkeypatch.setattr(
        pins_module,
        "_commit_is_ancestor_of_head",
        lambda commit: False if commit == artifact_commit else real_is_ancestor(commit),
    )

    def unbound_delivery(revision: str, path: str, label: str) -> bytes:
        if revision == "8f62b44708a60ab7e5dbb91aa68e2d7e987d7a02" and path == artifact_path:
            return delivered
        return real_blob_at_revision(revision, path, label)

    monkeypatch.setattr(pins_module, "_blob_at_revision", unbound_delivery)
    with pytest.raises(SystemExit, match="reviewed_branch_tip"):
        pins_module.validate_post_integration_source_acceptance_bindings(
            protected_baseline_commit="8f62b44708a60ab7e5dbb91aa68e2d7e987d7a02"
        )


def test_post_integration_delivery_rejects_unrelated_packaged_artifact(
    monkeypatch,
) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    binding = copy.deepcopy(
        pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source]
    )
    unrelated = b"status: SECURITY_CLEAR_SOURCE_ACCEPTED\nunrelated source record\n"
    binding["record_artifact"]["sha256"] = pins_module.hashlib.sha256(
        unrelated
    ).hexdigest()
    artifact_path = binding["record_artifact"]["path"]
    real_blob_at_revision = pins_module._blob_at_revision

    def unrelated_head_artifact(revision: str, path: str, label: str) -> bytes:
        if revision == "HEAD" and path == artifact_path:
            return unrelated
        return real_blob_at_revision(revision, path, label)

    monkeypatch.setitem(
        pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS, source, binding
    )
    monkeypatch.setattr(
        pins_module, "_blob_at_revision", unrelated_head_artifact
    )
    with pytest.raises(SystemExit, match="reviewed_branch_tip"):
        pins_module.validate_post_integration_source_acceptance_bindings(
            delivery_topology=True
        )


@pytest.mark.parametrize("mutation", ["missing", "invalid", "non_parent"])
def test_post_integration_source_acceptance_rejects_bad_common_base(monkeypatch, mutation: str) -> None:
    source = "ea9b27bfeba607c5332c51e10b037e100e97b717"
    binding = copy.deepcopy(pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS[source])
    if mutation == "missing":
        binding.pop("common_base_commit")
    elif mutation == "invalid":
        binding["common_base_commit"] = "0" * 40
    else:
        binding["common_base_commit"] = "a40215cae89af33aa7d7516629c79b33d0c0f3c7"
    monkeypatch.setitem(pins_module.POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS, source, binding)
    with pytest.raises(SystemExit):
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
    _require_live_document_verifiable()
    assert check_current(LIVE_PINS, LIVE_INVENTORY) == []
    assert dereferenced
    assert all(pins_module._commit_is_ancestor_of_head(commit) for commit in dereferenced)
    assert "da498ebd980cac87796eceb889c7f1c42cfb952b" not in dereferenced
    assert "7f21f27b14a7909424591a530096dc2f5d6e2b13" not in dereferenced
    assert "d2369b888e760e5b8d693328f00683877cbd5f28" not in dereferenced


# ── Squash-delivery admission (L0 repair, 2026-09) ────────────────────────────
#
# check() could always *verify* successors whose evidence commits were severed
# from ancestry by GitHub's squash delivery, but admit_successor() and
# validate_review_artifacts() could not *admit* one: every artifact commit had to
# be an ancestor of HEAD, and 5142109f7f2... never is for a branch cut from the
# squashed main. These tests pin the narrow fallback added for that and, just as
# importantly, everything it must NOT relax.


class _Recorder:
    def __init__(self) -> None:
        self.strict: list[str] = []
        self.squash: list[tuple[str, str]] = []


def _record_validators(monkeypatch, recorder: _Recorder, *, reachable: bool) -> None:
    monkeypatch.setattr(pins_module, "_commit_is_ancestor_of_head", lambda commit: reachable)
    monkeypatch.setattr(
        pins_module,
        "validate_artifact_binding",
        lambda artifact, label: recorder.strict.append(label),
    )
    monkeypatch.setattr(
        pins_module,
        "validate_protected_squash_artifact_binding",
        lambda artifact, label, baseline, **_: recorder.squash.append((label, baseline)),
    )


@pytest.mark.parametrize("layer", ["L0", "L2", "L3"])
def test_unreachable_review_artifacts_use_squash_path_only_with_a_baseline(
    monkeypatch, layer: str
) -> None:
    artifacts = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS[layer])
    baseline = "a" * 40

    with_baseline = _Recorder()
    _record_validators(monkeypatch, with_baseline, reachable=False)
    pins_module.validate_review_artifacts(layer, artifacts, "b" * 40, baseline)
    assert len(with_baseline.squash) == len(artifacts)
    assert all(b == baseline for _, b in with_baseline.squash)
    assert with_baseline.strict == []

    # No baseline: behaviour is exactly the old strict one, never the fallback.
    without = _Recorder()
    _record_validators(monkeypatch, without, reachable=False)
    pins_module.validate_review_artifacts(layer, artifacts, "b" * 40)
    assert without.squash == []
    assert len(without.strict) == len(artifacts)

    # A baseline does not divert an artifact that IS reachable.
    reachable = _Recorder()
    _record_validators(monkeypatch, reachable, reachable=True)
    pins_module.validate_review_artifacts(layer, artifacts, "b" * 40, baseline)
    assert reachable.squash == []
    assert len(reachable.strict) == len(artifacts)


def test_squash_fallback_does_not_relax_the_required_artifact_set(monkeypatch) -> None:
    baseline = "a" * 40
    _record_validators(monkeypatch, _Recorder(), reachable=False)
    tampered = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"])
    tampered[0]["sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="do not match the required acceptance artifacts"):
        pins_module.validate_review_artifacts("L2", tampered, "b" * 40, baseline)
    with pytest.raises(SystemExit, match="do not match the required acceptance artifacts"):
        pins_module.validate_review_artifacts("L2", tampered[:1], "b" * 40, baseline)


def test_squash_fallback_rejects_an_artifact_the_baseline_does_not_carry(monkeypatch) -> None:
    def refuse(artifact, label, baseline, **_):
        raise SystemExit(f"{label} is not an exact protected one-parent delivery")

    monkeypatch.setattr(pins_module, "_commit_is_ancestor_of_head", lambda commit: False)
    monkeypatch.setattr(pins_module, "validate_protected_squash_artifact_binding", refuse)
    with pytest.raises(SystemExit, match="not an exact protected one-parent delivery"):
        pins_module.validate_review_artifacts(
            "L0",
            copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L0"]),
            "b" * 40,
            "a" * 40,
        )


def _definition_fixture(monkeypatch, *, baseline_bindings):
    built: list[str] = []

    def fake_build(snapshot: str):
        built.append(snapshot)
        raise SystemExit("re-derived from snapshot")

    monkeypatch.setattr(pins_module, "_require_reachable_commit", lambda commit, label: None)
    monkeypatch.setattr(
        pins_module, "_pins_at_commit", lambda commit: {"definition_bindings": baseline_bindings}
    )
    monkeypatch.setattr(pins_module, "build_definition_bindings", fake_build)
    return built


def test_definition_bindings_are_carried_only_when_the_baseline_carries_them(monkeypatch) -> None:
    existing = copy.deepcopy(CURRENT_PINS["definition_bindings"])
    label = existing["L0"]["snapshot_commit"]
    baseline = "a" * 40

    built = _definition_fixture(monkeypatch, baseline_bindings=copy.deepcopy(existing))
    assert pins_module._resolve_definition_bindings(existing, label, baseline) == existing
    assert built == []  # carried verbatim, never re-derived from the severed commit

    # No baseline -> the old strict re-derivation, which refuses an unreachable commit.
    built = _definition_fixture(monkeypatch, baseline_bindings=copy.deepcopy(existing))
    with pytest.raises(SystemExit, match="re-derived from snapshot"):
        pins_module._resolve_definition_bindings(existing, label, None)
    assert built == [label]

    # Bindings the baseline does NOT carry (a rewritten membership) are re-derived.
    rewritten = copy.deepcopy(existing)
    rewritten["L2"]["membership_sha256"] = "0" * 64
    built = _definition_fixture(monkeypatch, baseline_bindings=copy.deepcopy(existing))
    with pytest.raises(SystemExit, match="re-derived from snapshot"):
        pins_module._resolve_definition_bindings(rewritten, label, baseline)
    assert built == [label]

    # A snapshot label that does not match what is recorded is re-derived, not carried.
    built = _definition_fixture(monkeypatch, baseline_bindings=copy.deepcopy(existing))
    with pytest.raises(SystemExit, match="re-derived from snapshot"):
        pins_module._resolve_definition_bindings(existing, "c" * 40, baseline)
    assert built == ["c" * 40]

    # A record covering fewer layers than L0-L5 is never carried.
    partial = {k: v for k, v in existing.items() if k != "L5"}
    built = _definition_fixture(monkeypatch, baseline_bindings=copy.deepcopy(partial))
    with pytest.raises(SystemExit, match="re-derived from snapshot"):
        pins_module._resolve_definition_bindings(partial, label, baseline)


def test_admission_refuses_a_candidate_whose_membership_disagrees_with_carried_bindings(
    monkeypatch,
) -> None:
    """The carried bindings are trusted only as evidence, never as an override:
    admit_successor still re-derives membership and compares it to them."""
    tampered_definitions = copy.deepcopy(CURRENT_PINS["definition_bindings"])
    tampered_definitions["L2"]["membership_sha256"] = "0" * 64
    document = copy.deepcopy(LEGACY_PINS)
    document["definition_bindings"] = copy.deepcopy(tampered_definitions)
    baseline = "a" * 40
    fixture_pins_at_commit = pins_module._pins_at_commit

    def pins_at_commit(commit: str) -> dict:
        if commit == baseline:
            return {"definition_bindings": copy.deepcopy(tampered_definitions)}
        return fixture_pins_at_commit(commit)

    monkeypatch.setattr(pins_module, "_pins_at_commit", pins_at_commit)
    monkeypatch.setattr(pins_module, "_require_reachable_commit", lambda commit, label: None)
    with pytest.raises(SystemExit, match="candidate membership does not match"):
        pins_module.admit_successor(
            document,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
            authority_decision="DP-SD-018",
            authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
            protected_baseline_commit=baseline,
        )


# ── The L0-repair successors themselves (PR #2727) ────────────────────────────

REPAIR_DECISION = "NATIVE-2026-09-24-L0-REPAIR-REPIN"
# The approval identity and the pinned source commit are DIFFERENT commits, on purpose
# (see L0_REPAIR_ANALYSIS_REPIN_DECISION_ADDENDUM_v1_0.md): the inventory at the approved
# state was stale, so the source is the commit that regenerates it, with writer sources
# byte-identical to the approved state.
REPAIR_APPROVED_STATE = "101171f76517fa3c6b0b44fa9d1cc46358612eee"
REPAIR_SOURCE = "7d40f8c706406ee8187eadb5c3930553800a1a4a"
REPAIR_INTENTIONAL = {
    "bg_transit_rules", "bg_transit_engine", "bg_vedha_malefic_scale",
    "bg_phaladeepika_latta", "bg_ephemeris",
}
REPAIR_BOTH = {"ka_vedha_gochara"}


def test_live_document_with_repair_successors_verifies() -> None:
    _require_live_document_verifiable()
    assert check_current(LIVE_PINS, LIVE_INVENTORY) == []


@pytest.mark.parametrize("layer", REPAIR_LAYERS)
def test_repair_successor_is_append_only_and_names_its_exact_predecessor(layer: str) -> None:
    delivered_active = CURRENT_PINS["layers"][layer]
    live_active = LIVE_PINS["layers"][layer]
    delivered_history = CURRENT_PINS["history"][layer]
    live_history = LIVE_PINS["history"][layer]

    # every previously packaged history entry survives byte-for-byte, in order
    assert live_history[: len(delivered_history)] == delivered_history
    assert len(live_history) == len(delivered_history) + 1
    # the delivered active pin is archived whole as the new predecessor
    archived = live_history[-1]
    assert archived["pin"] == delivered_active
    assert archived["generation_id"] == (
        delivered_active.get("generation_id") or pins_module.generation_id(layer, delivered_active)
    )
    assert live_active["supersedes_generation_id"] == archived["generation_id"]
    assert archived["superseded_by_generation_id"] == live_active["generation_id"]
    # and the predecessor's writer slice is exactly what the delivered inventory said
    assert archived["writer_digests"] == pins_module.layer_writer_slice(
        CURRENT_INVENTORY, pins_module.LAYER_PREFIX[layer]
    )


@pytest.mark.parametrize("layer", REPAIR_LAYERS)
def test_repair_successor_records_the_approved_decision_and_source(layer: str) -> None:
    admission = LIVE_PINS["layers"][layer]["admission"]
    assert admission["authority_decision"] == REPAIR_DECISION
    # the approval is anchored to the approved state; the pinned source is the commit
    # that carries a true inventory for it
    assert admission["authority_commit"] == REPAIR_APPROVED_STATE
    assert admission["source_commit"] == REPAIR_SOURCE
    assert REPAIR_APPROVED_STATE != REPAIR_SOURCE
    assert LIVE_PINS["layers"][layer]["convergence_commit"] == REPAIR_SOURCE
    assert admission["review_artifacts"] == pins_module.EXPECTED_REVIEW_ARTIFACTS[layer]
    assert "source_acceptance" not in admission
    assert pins_module.AUTHORIZED_SOURCE_COMMITS[REPAIR_DECISION][layer] == frozenset({REPAIR_SOURCE})


@pytest.mark.parametrize("layer", REPAIR_LAYERS)
def test_repair_classifications_equal_the_actual_digest_delta(layer: str) -> None:
    prefix = pins_module.LAYER_PREFIX[layer]
    before = pins_module.layer_writer_slice(CURRENT_INVENTORY, prefix)
    after = pins_module.layer_writer_slice(LIVE_INVENTORY, prefix)
    exact_delta = sorted(a for a in set(before) | set(after) if before.get(a) != after.get(a))
    admission = LIVE_PINS["layers"][layer]["admission"]
    assert admission["changed_assets"] == exact_delta
    assert exact_delta, "a successor with no delta must not have been admitted"
    for asset_id, classification in admission["delta_classifications"].items():
        if asset_id in REPAIR_BOTH:
            expected = "approved_intentional_and_derived_import_change"
        elif asset_id in REPAIR_INTENTIONAL:
            expected = "approved_intentional_change"
        else:
            expected = "derived_import_change"
        assert classification == expected, asset_id
    assert "unapproved_foreign_source" not in admission["delta_classifications"].values()


def test_repair_leaves_every_other_layer_and_the_definitions_untouched() -> None:
    for layer in pins_module.LAYER_PREFIX:
        if layer in REPAIR_LAYERS:
            continue
        assert LIVE_PINS["layers"][layer] == CURRENT_PINS["layers"][layer]
        assert LIVE_PINS["history"][layer] == CURRENT_PINS["history"][layer]
    assert LIVE_PINS["definition_bindings"] == CURRENT_PINS["definition_bindings"]
    assert LIVE_PINS["version"] == CURRENT_PINS["version"]


def test_repair_only_l0_l2_l3_are_authorised_for_the_decision() -> None:
    authorised = pins_module.AUTHORIZED_SOURCE_COMMITS[REPAIR_DECISION]
    assert set(authorised) == set(REPAIR_LAYERS)
    for layer in ("L1", "L4", "L5"):
        with pytest.raises(SystemExit, match="is not authorized by"):
            pins_module.validate_authorized_source(REPAIR_DECISION, layer, REPAIR_SOURCE)


def test_repair_authority_chain_binds_the_recorded_decision_document() -> None:
    binding = pins_module.AUTHORITY_BINDINGS[REPAIR_DECISION]
    assert binding["authority_commit"] == REPAIR_APPROVED_STATE
    assert binding["authority_identity_binding"] == f"`{REPAIR_APPROVED_STATE}`"
    assert binding["decision_binding"] == "status: L0_REPAIR_REPIN_APPROVED"
    pins_module.validate_authority_binding(REPAIR_DECISION, REPAIR_APPROVED_STATE)
    with pytest.raises(SystemExit, match="is not bound to"):
        pins_module.validate_authority_binding(REPAIR_DECISION, "0" * 40)
