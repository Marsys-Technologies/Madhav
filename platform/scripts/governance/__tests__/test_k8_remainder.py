"""K8-REG remainder (SR-K8REG-OPEN): the five elements PR #3557 left open, each measured by its own detector.

PR #3557 (migration 1392) corrected depends_on / has_writer / has_substeps / count_sql and declared the first L3 fingerprint (ka_sangam).
Both independent reviews (X-20261018T053833Z NB-1, X-20261018T094646Z NB-4) recorded that the item title also names: integrity_check_sql in
engine form, produced_tables, lifecycle fields, writer-digest entries and further L3 fingerprint declarations. This file is the whole-item
oracle: the plan model's K8-REG detector is "this file, with the five-element line below, is on origin/main", and CI runs it.

The database half of the integrity element (the migration run against real candidate-jury output, the replay of the registry-writing
migrations) is platform/python-sidecar/tests/l3/kala_db/registry/test_k8_remainder.py.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "platform" / "python-sidecar"))

import asset_census as ac  # noqa: E402
import kala_fingerprint_declarations as kfd  # noqa: E402

K8_REG_ELEMENTS = ("integrity_engine_form", "produced_tables", "lifecycle", "writer_digest", "fingerprint")

DECLS = ROOT / "platform" / "scripts" / "governance" / "asset_declarations.json"
MIGRATIONS = ROOT / "platform" / "migrations"
SEED = ROOT / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
DIGESTS = ROOT / "platform" / "src" / "generated" / "nirmana-writer-digests.json"
PLAN = ROOT / "00_ARCHITECTURE" / "control" / "kalayantra" / "plan_model.json"


def declarations() -> dict:
    return json.loads(DECLS.read_text(encoding="utf-8"))["assets"]


def remainder_migration() -> pathlib.Path:
    found = sorted(MIGRATIONS.glob("*_k8_registry_remainder.sql"))
    assert len(found) == 1, f"exactly one K8-REG remainder migration expected, found {[p.name for p in found]}"
    return found[0]


def migration_1392_rows() -> list[dict]:
    text = (MIGRATIONS / "1392_k8_registry_truth.sql").read_text(encoding="utf-8")
    return json.loads(re.search(r"\$k8_rows\$(.*?)\$k8_rows\$", text, re.S)[1])


# ═════════════════════════════ integrity_engine_form ═════════════════════════════

def sangam_670_contract() -> str:
    """The registered ka_sangam contract exactly as migration 670 stores it (the only migration that ever wrote it)."""
    text = (MIGRATIONS / "670_nirmana_l3_w3_integrity_contracts.sql").read_text(encoding="utf-8")
    mine = []
    for block in text.split("UPDATE asset_registry SET integrity_check_sql = $ck$")[1:]:
        body, _, after = block.partition("$ck$")
        if re.match(r"\s*WHERE asset_id = 'ka_sangam';", after):
            mine.append(body)
    assert len(mine) == 1, "ka_sangam contract not found exactly once in migration 670"
    return mine[0]


def engine_form_problem(sql: str) -> str | None:
    """Engine form = a single read-only SELECT/WITH (asset_census.integrity_sql_problem) that takes no bind parameter, because
    asset_runner._probe_asset executes the stored text with no parameters."""
    problem = ac.integrity_sql_problem(sql)
    if problem:
        return problem
    if re.search(r"\$\d+", re.sub(r"--[^\n]*", "", sql)):
        return "a bind parameter: the engine passes none"
    return None


def jury_conjunct() -> str:
    m = re.search(r"\$k8_jury\$(.*?)\$k8_jury\$", remainder_migration().read_text(encoding="utf-8"), re.S)
    assert m, "the K8-REG remainder migration carries no $k8_jury$ conjunct"
    return m[1]


def spliced_sangam_contract() -> str:
    old = sangam_670_contract()
    tail = re.search(r"\s*AS integrity_passed\s*$", old)[0]
    return old[: len(old) - len(tail)] + jury_conjunct() + "\n  AS integrity_passed\n"


def test_integrity_engine_form_of_the_spliced_ka_sangam_contract():
    """Plan section 7, Build row: unparameterised, read-only, truthy first column (asset_runner._probe_asset; asset_census.integrity_sql_problem)."""
    sql = spliced_sangam_contract()
    assert engine_form_problem(sql) is None
    assert sql.rstrip().endswith("AS integrity_passed")
    old_body = re.sub(r"\s*AS integrity_passed\s*$", "", sangam_670_contract())
    assert sql.startswith(old_body), "every 670 conjunct is kept byte for byte"
    assert "ka_sangam integrity contract" in sql and "kala_convergence" in sql


def test_integrity_engine_form_refuses_a_parameterised_or_writing_conjunct():
    """The detector can read false: the same splice with a bind parameter or a write in the conjunct is refused."""
    old = sangam_670_contract()
    tail = re.search(r"\s*AS integrity_passed\s*$", old)[0]
    base = old[: len(old) - len(tail)]
    assert engine_form_problem(base + " AND (SELECT count(*) FROM kala_jury_candidate WHERE chart_id = $1) >= 0 AS integrity_passed")
    assert engine_form_problem(base + " AND (WITH d AS (DELETE FROM kala_jury_candidate RETURNING 1) SELECT true) AS integrity_passed")


def test_integrity_conjunct_states_only_contract_stated_invariants():
    """Each conjunct names the contract sentence it measures (candidate_contract.json); none is invented (B.10)."""
    contract = json.loads((ROOT / "platform/python-sidecar/services/ka_sangam/jury/candidate_contract.json").read_text(encoding="utf-8"))
    assert "exactly one canonical jury assertion" in contract["grain"]
    assert "half-open boundaries" in contract["outputs"]["kala_jury_candidate_segment"]
    assert "group support vectors and allowed source roots" in contract["outputs"]["kala_jury_candidate_segment"]
    text = jury_conjunct()
    for tag in ("(K8-a)", "(K8-b)", "(K8-c)"):
        assert text.count(tag) == 1, tag


# ═════════════════════════════ produced_tables ═════════════════════════════

# Writers whose static write scan is not complete: they delegate to the shared candidate-partition helper, so the scanner itself says the
# written set is unproven (produced_set_written()["complete"] is False). Their produced set is therefore NOT claimed (B.10).
INCOMPLETE_SCAN = {
    "ka_avadhi", "ka_gochara_v5", "ka_jivana_parva", "ka_kala_darshana", "ka_kalasutra", "ka_kota_chakra", "ka_moorti_nirnaya",
    "ka_sudarshana_varsha", "ka_taranga", "ka_tithi_pravesha", "ka_vedha_gochara", "ka_vighnakara",
}
# Registered ka_* writers that have no entry in asset_declarations.json at all (the census does not grade them today).
UNDECLARED_ASSETS = {"ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate", "ka_gochara_v5"}
NOT_DECLARED_NOTE = re.compile(r"produced_tables (?:not declared|total is asserted)|No produced_tables total is asserted|no N-150 produced_tables sum is declared", re.I)


@pytest.fixture(scope="module")
def scans() -> dict:
    return {aid: ac.produced_set_written(aid, files) for aid, files in sorted(ac.registered_ids("ka_").items())}


def test_produced_tables_every_multi_table_ka_writer_declares_the_set_or_states_why_not(scans):
    """Build.completion rev 4 (N-150): a declared set must SUM to rows_written. A complete scan naming more than one table obliges the asset's
    declaration to either carry the set or say why no sum is asserted; an unstated disposition is a signal with no detector behind it (N.8)."""
    decl = declarations()
    for aid, scan in scans.items():
        if aid in UNDECLARED_ASSETS or not scan["complete"] or len(scan["written"]) <= 1:
            continue
        entry = decl[aid]
        if entry.get("produced_tables") is not None:
            assert sorted(t["table"] for t in entry["produced_tables"]) == scan["written"], f"{aid}: declared set differs from the scan"
        else:
            assert NOT_DECLARED_NOTE.search(entry["evidence"]["kind"]), f"{aid}: scan names {scan['written']} and the declaration is silent"


def test_produced_tables_incomplete_scans_are_exactly_the_disclosed_set(scans):
    """An incomplete scan proves no set. The disclosed list may shrink as the scanner improves; it may not silently gain an asset."""
    incomplete = {aid for aid, scan in scans.items() if not scan["complete"]}
    assert incomplete <= INCOMPLETE_SCAN, f"new incomplete-scan assets need a disposition: {sorted(incomplete - INCOMPLETE_SCAN)}"


def test_produced_tables_no_ka_declaration_asserts_a_set_the_scan_cannot_support(scans):
    for aid, entry in declarations().items():
        if not aid.startswith("ka_") or entry.get("produced_tables") is None:
            continue
        scan = scans[aid]
        assert scan["complete"], f"{aid} declares produced_tables but its writer scan is incomplete"
        assert sorted(t["table"] for t in entry["produced_tables"]) == scan["written"]


def test_produced_tables_undeclared_assets_are_the_registered_writers_missing_from_the_declarations(scans):
    assert UNDECLARED_ASSETS == {aid for aid in scans if aid not in declarations()}


# ═════════════════════════════ lifecycle ═════════════════════════════

def seed_lifecycle() -> dict[str, dict]:
    text = SEED.read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    parts = re.split(r"\n    asset_id: '", text)[1:]
    for part in parts:
        aid = part.split("'", 1)[0]
        if not aid.startswith("ka_"):
            continue
        body = part.split("\n  },", 1)[0]
        active = re.search(r"\bis_active: (true|false)", body)
        status = re.search(r"\bcatalog_status: '(\w+)'", body)
        out[aid] = dict(is_active=active[1] == "true" if active else None, catalog_status=status[1] if status else None)
    return out


def plan_items() -> dict[str, dict]:
    return {i["id"]: i for i in json.loads(PLAN.read_text(encoding="utf-8"))["items"]}


# Each lifecycle cutover K8-REG does NOT make, with the plan item that owns it. A cutover without its accepted gate would be a retirement of a
# live writer on a claim (packet section 4: "Lifecycle requires accepted cutover").
CUTOVER_OWNERS = {
    "ka_gochara": ("J-7a", "lifecycle fields set"),
    "ka_gochara_v3_century_materialize": ("D-R9", "century materializer hold retained"),
    "ka_tulana": ("D-R6", "Tulana"),
}


def test_lifecycle_inactive_ka_rows_are_exactly_the_three_settled_or_gated_ones():
    state = seed_lifecycle()
    inactive = {a for a, s in state.items() if s["is_active"] is False}
    assert inactive == {"ka_gochara_sweep", "ka_gochara_v4_41_candidate", "ka_gochara_v5"}
    assert state["ka_gochara_sweep"]["catalog_status"] == "RETIRED"
    assert all(state[a]["catalog_status"] != "RETIRED" for a in state if a != "ka_gochara_sweep")


def test_lifecycle_the_retired_sweep_is_settled_by_593_and_restated_by_1392():
    sql593 = (MIGRATIONS / "593_nirmana_t0_retired_gochara_disposition.sql").read_text(encoding="utf-8")
    assert "superseded_by = 'ka_gochara'" in sql593 and "RETAINED_AS_CAPITAL" in sql593
    sql1392 = (MIGRATIONS / "1392_k8_registry_truth.sql").read_text(encoding="utf-8")
    assert "data_disposition='RETAINED_AS_CAPITAL'" in sql1392


def test_lifecycle_no_cutover_is_made_without_its_owning_item():
    """Neither 1392 nor the remainder migration assigns is_active / superseded_by / catalog_status in a SET clause (the cutovers wait for their
    gates), and every cutover left open names a plan item that really owns it."""
    for path in (MIGRATIONS / "1392_k8_registry_truth.sql", remainder_migration()):
        body = "\n".join(line.split("--", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
        for assigned in re.findall(r"\bSET\b(.*?)\bWHERE\b", body, re.S):
            assert not re.search(r"\b(?:is_active|superseded_by|catalog_status)\b", assigned), f"{path.name} assigns a lifecycle column: {assigned[:80]}"
    items = plan_items()
    for aid, (item_id, phrase) in CUTOVER_OWNERS.items():
        assert item_id in items, f"{aid}: owning item {item_id} is not in the plan model"
        assert phrase.lower() in items[item_id]["title"].lower(), f"{aid}: {item_id} no longer says {phrase!r}"


# ═════════════════════════════ writer_digest ═════════════════════════════

def test_writer_digest_every_registered_ka_writer_has_an_inventory_entry_and_no_other_does():
    """The inventory is machine-owned (regenerated by CI from main, never edited in a branch); membership is what a branch can break: a new
    @register'd ka_* writer without an entry, or an entry for a class that no longer registers. Bytes are the generator's business."""
    registered = set(ac.registered_ids("ka_"))
    inventory = {a for a in json.loads(DIGESTS.read_text(encoding="utf-8"))["writers"] if a.startswith("ka_")}
    assert registered == inventory, f"missing {sorted(registered - inventory)}, extra {sorted(inventory - registered)}"


def test_writer_digest_registry_has_writer_flag_equals_the_registered_set():
    """has_writer in 1392 (the live registry truth) agrees with the registered classes, which agree with the digest inventory."""
    rows = migration_1392_rows()
    assert {r["asset_id"] for r in rows if r["has_writer"]} == set(ac.registered_ids("ka_"))
    assert [r["asset_id"] for r in rows if not r["has_writer"]] == ["ka_gochara_sweep"]


# ═════════════════════════════ fingerprint ═════════════════════════════

def test_fingerprint_second_declaration_ka_gochara_resonance_validates_against_real_ddl_and_writer():
    fp = declarations()["ka_gochara_resonance"]["fingerprint"]
    assert kfd.validate("ka_gochara_resonance", fp)["coverage"] == "partial"
    assert {t["name"] for t in fp["tables"]} == {"kala_f1_target_object", "kala_f1_relationship"}
    assert [n["name"] for n in fp["not_covered_tables"]] == ["gochara_resonance_map"]
    ac.validate_declarations(json.loads(DECLS.read_text(encoding="utf-8")))


def test_fingerprint_every_committed_declaration_is_valid_partial_and_never_full():
    found = {a: e["fingerprint"] for a, e in declarations().items() if a.startswith("ka_") and e.get("fingerprint") is not None}
    assert {"ka_sangam", "ka_gochara_resonance"} <= set(found)
    for aid, fp in found.items():
        assert kfd.validate(aid, fp)["coverage"] == "partial", aid


def test_fingerprint_resonance_candidate_dispatch_is_wired_into_the_registered_writer():
    """The declaration attributes the F1 tables to ka_gochara_resonance; that holds only while the registered writer reaches the storage module."""
    writer = (ROOT / "platform/python-sidecar/services/ka_gochara_resonance/writer.py").read_text(encoding="utf-8")
    assert "candidate_generation" in writer and "relationship_storage import build_candidate_projection" in writer


# (asset, candidate table, why the current validator cannot evidence a declaration). The validator needs a literal `INSERT INTO <table>` in a
# file whose path names the asset (kala_fingerprint_declarations.validate); extending it is the separate engine/custodian PR of packet section 4.
BLOCKED_FINGERPRINTS = [
    ("ka_vedha_gochara", "kala_vedha_gochara_candidate"),
    ("ka_vedha_gochara", "kala_vedha_gochara_interval"),
    ("ka_kalasutra", "kala_activation_candidate"),
    ("ka_kala_darshana", "kala_darshana_candidate"),
    ("ka_jivana_parva", "kala_jivana_parva_candidate"),
    ("ka_taranga", "kala_taranga_candidate"),
]


def asset_bound_files(aid: str) -> list[pathlib.Path]:
    base = ROOT / "platform" / "python-sidecar"
    return [p for p in base.rglob("*.py") if aid in str(p.relative_to(base)) and "tests" not in p.parts and "__tests__" not in p.parts]


@pytest.mark.parametrize("aid,table", BLOCKED_FINGERPRINTS)
def test_fingerprint_blocked_assets_have_no_asset_bound_literal_insert(aid, table):
    """The block is a measured fact, not a habit: the day an asset-bound file inserts the table literally, this fails and the declaration is owed."""
    pattern = re.compile(r"INSERT\s+INTO\s+(?:public\.)?" + table + r"\b", re.I)
    assert not [p for p in asset_bound_files(aid) if pattern.search(p.read_text(encoding="utf-8", errors="replace"))]


def test_fingerprint_kshetra_g2_candidate_is_not_dispatched_by_the_registered_writer():
    """kala_kshetra_g2_candidate has a literal INSERT and a plain key, but nothing in the registered ka_kshetra writer reaches it (only its test), so a
    declaration would attribute a table to an asset that does not write it."""
    base = ROOT / "platform" / "python-sidecar"
    callers = [str(p.relative_to(base)) for p in base.rglob("*.py")
               if "g2_candidate" in p.read_text(encoding="utf-8", errors="replace") and p.name != "g2_candidate.py" and "tests" not in p.parts]
    assert callers == []


# ═════════════════════════════ whole-item detector and closure ═════════════════════════════

def test_every_named_element_has_an_oracle_in_this_file_or_the_database_file():
    names = re.findall(r"^def (test_\w+)", pathlib.Path(__file__).read_text(encoding="utf-8"), re.M)
    db_file = ROOT / "platform/python-sidecar/tests/l3/kala_db/registry/test_k8_remainder.py"
    names += re.findall(r"^def (test_\w+)", db_file.read_text(encoding="utf-8"), re.M)
    for element in K8_REG_ELEMENTS:
        assert [n for n in names if n.startswith(f"test_{element}")], f"no oracle named test_{element}*"


def test_plan_model_k8_reg_detector_measures_the_whole_item():
    item = plan_items()["K8-REG"]
    det = item["detector"]
    assert det["type"] == "branch_file_contains" and det["ref"] == "origin/main"
    path = ROOT / det["path"]
    assert path == pathlib.Path(__file__).resolve(), "the detector must point at this whole-item oracle"
    assert re.search(det["pattern"], path.read_text(encoding="utf-8"), re.M), "the detector pattern does not match the file it names"
    line = "K8_REG_ELEMENTS = (" + ", ".join(f'"{e}"' for e in K8_REG_ELEMENTS) + ")"
    assert re.search(det["pattern"], line), "the detector pattern must be the five-element line and nothing weaker"


def test_plan_model_k8_reg_detector_is_false_for_a_partial_delivery():
    """Fail-closed: a file that lists fewer elements (the #3557-only state has no such file) does not satisfy the pattern."""
    pattern = plan_items()["K8-REG"]["detector"]["pattern"]
    four = 'K8_REG_ELEMENTS = ("integrity_engine_form", "produced_tables", "lifecycle", "writer_digest")'
    assert not re.search(pattern, four, re.M)


def test_closure_v3_matches_the_plan_model():
    base = ROOT / "00_ARCHITECTURE"
    result = subprocess.run(
        [sys.executable, "-I", str(base / "briefs/kalayantra/fleet/kyclosure.py"), "--model", str(base / "control/kalayantra/plan_model.json"),
         "--roots", str(base / "control/kalayantra/ACCEPTANCE_ROOTS_v3.json"), "--check", str(base / "control/kalayantra/CLOSURE_v3.json")],
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
