"""K9-23-N2 custody is preparation, with the implementation finding still open."""
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / "00_ARCHITECTURE/briefs/kalayantra"
NOTE = BRIEFS / "K9_23_N2_CUSTODY_v1_0.md"


def custody():
    assert NOTE.is_file(), "K9-23-N2 needs a retained custody note"
    return yaml.safe_load(NOTE.read_text().split("---", 2)[1])


def test_preparation_does_not_claim_the_implementation_finding_fixed():
    note = custody()
    assert note["finding"] == "K9-23-N2"
    assert note["status"] == "PREPARATION"
    assert note["finding_status"] == "open"
    assert note["implementation_fixed"] is False
    assert note["parent_accepted_head"] == "d1c027d63f765638c9adca49bd580d6509a19a1c"
    assert note["review_source"].endswith("X-20261015T231013Z-review2-k9-23/result.json")
    assert note["original_review_source"].endswith("X-20261015T221120Z-review-k9-23/result.json")


def test_child_keeps_independent_acceptance_without_reopening_parent():
    items = {i["id"]: i for i in json.loads(
        (ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text()
    )["items"]}
    child, parent = items["K9-23-N2"], items["K9-23"]
    assert child["mandatory"] is True
    assert child["depends_on"] == ["K9-23"]
    assert "K9-23-N2" not in parent["depends_on"]
    assert child["completion_kind"] == "code"
    assert child["reviewer_rule"] == parent["reviewer_rule"] == "v_exact_head_then_deploy_containment"
    # SR-DETECTOR-REFS: the source branch was deleted at merge, so the detector pins the PR #3606 squash commit
    # (K9-23-N2: pre-build K9-23-N2 (A6 D-40) (#3606)), which must stay contained in origin/main.
    detector = child["detector"]
    assert (detector["type"], detector["ref"], detector["packet_pr"]) == (
        "branch_merged", "ee51abe09bd5e62d8bba6999515ef160fe688cbc", 3606)
    assert "status" not in child and "steps" not in child


def test_k9_23_enablement_preserves_the_production_flags():
    ops = json.loads((BRIEFS / "fleet/executor_ops.json").read_text())["ops"]
    for kind in ("orchestrator_rebuild_dryrun", "orchestrator_rebuild",
                 "layer_verify", "layer_publish", "layer_rollback"):
        assert ops[kind]["enabled"] is True, kind               # SR-PREBUILD-ALL: K9-23 bound and enabled them
        assert ops[kind]["production"] is (not kind.endswith("_dryrun")), kind   # A8 §3.8: a dry run is read-only with a credential


def test_owed_proof_distinguishes_delegation_and_incomplete_outcome():
    proof = custody()["owed_regression"]
    assert proof["initial_state"] == "planned"
    assert proof["delegation"] == "execute_run(str(args.run_id)) exactly once"
    assert proof["success"] == "completed readback; exit 0; BUILD_COMPLETED"
    assert proof["incomplete"] == "non-completed or absent readback; exit 2; REFUSED"
    assert proof["mutation"] == "remove execute_run call; successful-delegation test must fail"
    assert proof["location"] == "CI-collected publication regression on the landed parent"


def test_custody_retains_each_activation_prerequisite():
    assert set(custody()["activation_prerequisites"]) == {
        "K9-1 exact publication_grains and complete run/writer/grain bindings",
        "independent semantic checks for every candidate writer",
        "frozen ordered canonical-chart rebuild plan and issued-forecast exclusion",
        "least-privilege verifier and protected migration qualification",
        "absent candidate, failed verification and stale expected-head refusals",
        "generation namespace excludes NONE and absent/existing-head CAS cases",
        "PLAN_ONLY never earns execution dry-run qualification",
        "D-R9 hold until coverage/refinement and backup capability qualification",
        "full rehearsal, lineage invalidation and measured restart loss",
        "retained previous-head and byte-exact full served-projection rollback",
        "J-1a qualified backup and restore capability",
        "independent exact-head acceptance, CI, merge and deploy containment",
        "live admission and parent completion gates",
    }


def test_custody_checks_are_collected_by_the_governance_shards():
    import ci_shard

    files = ci_shard.test_files()
    shards = ci_shard.partition(files, 5)
    assert Path(__file__).resolve() in files
    assert sum(Path(__file__).resolve() in shard for shard in shards) == 1
    assert ci_shard.verify(files, shards) == []
