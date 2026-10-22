"""SR-A55J-A55M-RESCOPE (surrogate ruling 2026-10-20): J-4b-a55j and J-4c-a55m are re-scoped to the 1378 reality.

Claims, one oracle each (the reversion named after it fails that test):
  1. neither item targets migration 1241: 1241 is not in the repository, 1378 is, and every 1241 mention is "superseded"
     (reversion: restore "1241 v7" as a live target in either title)
  2. the 1378 file in the repository is byte-identical to what production applied (ledger sha256 read back by the 2026-10-20
     recon, ledger row 2026-10-14T22:09:41Z) and the plan cites that same hash (reversion: cite a different hash)
  3. the dormant-role revoke act stays OPEN while its premise holds: 1378 contains no REVOKE statement and 1303 is not in the
     repository, so a retirement decision for it may exist only if a migration in the repository revokes
     (reversion: add D-J4B-1303-NA / D-J4C-DORMANT-NA while nothing revokes)
  4. acts 12, 13, 14 are each named in J-4c-a55m's brief with the runbook anchor, an evidence statement and a measurability
     statement; every readback kind the brief cites exists, enabled or not, in fleet/executor_ops.json and is read-only
     (reversion: drop an act, or cite a kind the table does not have)
  5. the "MEASURED GAP" the plan states for cloudrun_job_readback is true exactly while the kind cannot name the verification
     job (reversion: widen cloudrun_readback.JOB without removing the gap text, or the other way round)
  6. re-scoping retires nothing and adds nothing: both items stay mandatory members of the acceptance closure, none is
     not_applicable, and the closure headline the tests pin (181 since VC-2's retirement) is unchanged and the plan never has fewer than the 274 items it had
     before re-scoping (reversion: drop either item's edge)
  7. this file is run by required CI: some include glob of a profile in ci_test_suites.json matches it (A5 D-33)
     (reversion: remove the test_a55j*.py glob from governance-tool-tests-shard-7-0)
  8. OWNER-BUILD-FIRST-20261021: the pre-century chain and the century build do not wait on the owner's provisioning acts:
     neither J-4b-a55j nor J-4c-a55m is in the transitive upstream of J-4b, J-4c, J-4d, D-CLOUD or J-4e
     (reversion: restore the J-4b -> J-4b-a55j edge, or the J-4c -> J-4c-a55m edge)
  9. the same decision makes them gates before SEALING: J-5s, and what seals or publishes after it (J-6, D-FLIP), have both in
     their transitive upstream (reversion: drop either edge from J-5s)

Sources: OWNER-BUILD-FIRST-20261021 (claims 8-9), SR-A55J-A55M-RESCOPE and OWNER-GRANTS-MINIMAL-20261018 in /Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl;
platform/migrations/1378_gochara_verifier_sealer_inventory_grants.sql (header lines 4 and 53-57); runbook
ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md acts 12-14; fleet/CLOUDRUN_READBACK_v1_0.md.
"""
from __future__ import annotations

import fnmatch
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
FLEET = REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet"
M1378 = REPO / "platform/migrations/1378_gochara_verifier_sealer_inventory_grants.sql"
# the production ledger row for 1378 (recon J-4b-a55j.recon-20261020T1100Z, applied_at 2026-10-14 22:09:41 UTC)
LEDGER_SHA_1378 = "04540a995e849517d03d80835a4dfaae0ee588c081485337d976814e44a70108"
ITEMS = ("J-4b-a55j", "J-4c-a55m")


def _closure(model):
    """The closure of THIS model: a pure function of plan_model.json + ACCEPTANCE_ROOTS (kyclosure.compute). The committed
    CLOSURE_v3.json is CI-generated from main (SR-CHURN-CUT 3), so a model change is pinned against the recomputation."""
    spec = importlib.util.spec_from_file_location("kyclosure", REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/kyclosure.py")
    kyclosure = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = kyclosure     # dataclass-style lookups need the module registered
    spec.loader.exec_module(kyclosure)
    roots = json.loads((REPO / "00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v3.json").read_text(encoding="utf-8"))
    return kyclosure.compute(model, roots)


@pytest.fixture(scope="module")
def model():
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _item(model, iid):
    return next(i for i in model["items"] if i["id"] == iid)


def _text(item):
    b = item["brief"]
    return " ".join([item["title"], *b["spec"], *b["tests"], b["notes"]])


def test_neither_item_targets_the_superseded_1241(model):  # claim 1
    assert not list((REPO / "platform/migrations").glob("1241_*")) and M1378.is_file()
    for iid in ITEMS:
        item = _item(model, iid)
        assert "1378" in item["title"], iid
        for field in [item["title"], *item["brief"]["spec"], *item["brief"]["tests"], item["brief"]["notes"]]:
            for m in re.finditer(r"1241", field):
                assert re.search(r"supersed", field[max(0, m.start() - 60): m.end() + 60]), (iid, field[:120])


def test_the_repository_1378_is_what_production_applied_and_the_plan_cites_it(model):  # claim 2
    assert hashlib.sha256(M1378.read_bytes()).hexdigest() == LEDGER_SHA_1378
    assert LEDGER_SHA_1378 in _text(_item(model, "J-4b-a55j"))


def test_the_dormant_role_revoke_clause_is_dropped_only_by_the_declared_decision(model):  # claim 3
    # SR-AUDIT-BOOKKEEPING (audit R3): D-J4B-1303-NA (DECISIONS_SURROGATE.jsonl, 2026-10-21T03:17Z) declares the revokes not applicable
    # on the window2 readback receipt; the plan carries the declaration and the step no longer lists 1303 / the revokes as OPEN. The
    # ruling rests on two measured facts, asserted here: 1378 revokes nothing and 1303 never merged - a migration that revokes would void it.
    sql = "\n".join(line for line in M1378.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--"))
    revoked_by_a_migration = any(
        re.search(r"(?im)^\s*REVOKE\b", p.read_text(encoding="utf-8", errors="replace"))
        for p in (REPO / "platform/migrations").glob("13[0-9][0-9]_*.sql")
        if "dormant" in p.read_text(encoding="utf-8", errors="replace").lower()
    )
    assert not re.search(r"(?im)^\s*REVOKE\b", sql)          # 1378 revokes nothing
    assert not list((REPO / "platform/migrations").glob("1303_*"))   # 1303 was never merged
    assert not revoked_by_a_migration
    declared = [d["id"] for d in model["decisions"] if d["id"] in ("D-J4B-1303-NA", "D-J4C-DORMANT-NA")]
    assert declared == ["D-J4B-1303-NA"]
    item = _item(model, "J-4c-a55m")
    assert "dormant-role revokes" not in item["title"] and "1303" not in item["title"]
    clause = next(t for t in item["brief"]["tests"] if t.startswith("1303 and the dormant-role revokes"))
    assert "NOT APPLICABLE by D-J4B-1303-NA" in clause and "OPEN" not in clause


def test_acts_12_13_14_are_named_with_evidence_and_measurability(model):  # claim 4
    tests = _item(model, "J-4c-a55m")["brief"]["tests"]
    ops = json.loads((FLEET / "executor_ops.json").read_text(encoding="utf-8"))["ops"]
    for n in (12, 13, 14):
        row = [t for t in tests if t.startswith(f"Act {n} (")]
        assert len(row) == 1, n
        assert f"'Act {n}'" in row[0] and "Evidence:" in row[0], n
        assert re.search(r"NO existing readback kind measures it|indirectly", row[0]), n
    cited = {k for t in tests for k in re.findall(r"\b(readback_sql|cloudrun_job_readback|github_run_readback)\b", t)}
    assert cited >= {"readback_sql", "cloudrun_job_readback", "github_run_readback"}
    for kind in cited:
        assert ops[kind].get("read_only") is True, kind


def test_the_cloudrun_gap_is_stated_exactly_while_it_is_true(model):  # claim 5
    src = (FLEET / "cloudrun_readback.py").read_text(encoding="utf-8")
    kind_can_name_verification_job = "gochara-verification-job" in src
    stated = "MEASURED GAP" in _text(_item(model, "J-4b-a55j"))
    assert stated == (not kind_can_name_verification_job)


def test_rescoping_retires_nothing_and_the_headline_is_unchanged(model):  # claim 6
    closure = _closure(model)
    assert closure["closure_count"] == len(closure["closure"]) == 181   # 183 -> 181: VC-1 and VC-2 leave with the retired VC-2 (SR-CLOSE-NOW 5)
    assert len(model["items"]) >= 274   # retires nothing: the plan only grows (275 once #3632 merged); an exact pin goes red on every unrelated merge
    for iid in ITEMS:
        item = _item(model, iid)
        assert item["mandatory"] is True and iid in closure["closure"]
        assert item["steps"] and item["detector"]["path"].endswith(f"/{iid}.json")
    # OWNER-BUILD-FIRST-20261021: a55m now also waits on a55j (its judge binds the a55j step receipt); a55j's own edges are unchanged
    assert _item(model, "J-4c-a55m")["depends_on"] == ["J-0m", "J-4b", "J-4c-a55l", "J-4b-a55j"]
    assert _item(model, "J-4b-a55j")["depends_on"] == ["J-0m", "J-4a"]


def _upstream(model, iid):
    by_id = {i["id"]: i for i in model["items"]}
    seen, stack = set(), [iid]
    while stack:
        for dep in by_id[stack.pop()]["depends_on"]:
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def test_the_century_chain_does_not_wait_on_the_owner_provisioning_acts(model):  # claim 8
    for iid in ("J-4b", "J-4c", "J-4c-a55l", "J-4d", "D-CLOUD", "J-4e"):
        assert not set(ITEMS) & _upstream(model, iid), iid


def test_the_owner_provisioning_acts_gate_sealing_and_what_follows_it(model):  # claim 9
    for iid in ("J-5s", "J-6", "D-FLIP"):
        assert set(ITEMS) <= _upstream(model, iid), iid


def test_this_file_is_matched_by_a_ci_suite_glob():  # claim 7
    suites = json.loads((REPO / "platform/scripts/governance/ci_test_suites.json").read_text(encoding="utf-8"))
    me = Path(__file__).resolve().relative_to(REPO).as_posix()
    globs = [g for prof in suites["suites"].values() for g in prof.get("include", [])]
    assert any(fnmatch.fnmatch(me, g) for g in globs), me
