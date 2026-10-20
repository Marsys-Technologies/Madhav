"""The part of the century contract that needs the sidecar dependencies (runs in the db-integration-tests-smalltest profile, `test_*smalltest*.py`).

I1 the image binding's writer-source digest is get_writer_source_hash('ka_gochara_v5') of this tree (a writer change makes the committed contract stale and this test fails until
   `century_contract.py --write` is run: the same staleness discipline as implementation_digest.lock.json) ·
I2 the contract's scored classes equal the writer's own SCORED_CLASSES and its horizon start equals the writer's DEFAULT_HORIZON start (the generator reads them by AST; the writer
   is the authority) · I3 the contract's output tables equal the shared module's ABSENCE_TABLES and every one is a table the century backup scope lists as written for the generation
   (the unmarked run writes no other table) · I4 the policy the contract states is the policy the writer takes for an unmarked run: POLICY_RAISE.
"""
import json
import sys
from pathlib import Path


FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
for p in (REPO / "platform/python-sidecar", REPO / "platform/scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from pipeline.orchestrator.writers import ka_gochara_v5 as writer  # noqa: E402
from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash  # noqa: E402
from services.gochara_kernel import contact_certify  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

CONTRACT = json.loads((FLEET / "century_contract.json").read_text())


def test_i1_the_image_binding_is_the_writer_source_digest_of_this_tree():
    assert CONTRACT["image"]["writer_source_digest"] == get_writer_source_hash("ka_gochara_v5")


def test_i2_classes_and_horizon_start_are_the_writers():
    assert CONTRACT["classes"]["scored"] == list(writer.SCORED_CLASSES) and CONTRACT["classes"]["count"] == len(writer.SCORED_CLASSES)
    assert CONTRACT["horizon"]["start"] == writer.DEFAULT_HORIZON[0].isoformat()


def test_i3_output_tables_are_the_generation_scoped_tables_the_century_scope_writes():
    assert [t["object"] for t in CONTRACT["output_tables"]] == [t for t, _ in shared.ABSENCE_TABLES]
    scope = json.loads((REPO / "platform/scripts/backup_v5_century_scope.json").read_text())
    scoped = {w["table"] for w in scope["written"] if w["group"] == "writer_generation_5_0"}
    assert {t["table"] for t in CONTRACT["output_tables"]} <= scoped


def test_i4_the_stated_certification_policy_is_what_an_unmarked_run_takes():
    assert CONTRACT["policy"]["certification"]["sink_policy"] == contact_certify.POLICY_RAISE and CONTRACT["policy"]["certification"]["strict"] is True
