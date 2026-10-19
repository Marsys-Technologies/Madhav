"""SR-EDGES-PROOF 2 / SR-HORIZON-PUBLIC: fleet/century_contract.json, its generator, and the executor's binding of a century dispatch to its sha256.

Distinct production claims, each with a doctrine-grounded oracle. Bounds in every generator fixture are SYNTHETIC (SR-HORIZON-PUBLIC: "Test fixtures: synthetic bounds").
E1 a century dispatch (and its dry run) carrying a contract sha other than the sha256 of fleet/century_contract.json AT ITS reviewed_commit is refused, and so is a request with no sha
   (SR-EDGES-PROOF 2: "fill binds to its sha") · E2 the contract is read at the request's reviewed_commit, not from a working tree (the same sha text over a different blob refuses) ·
E3 the contract's launch_args must be the request's args · E4 other kinds are not touched ·
H1 horizon: start = DEFAULT_HORIZON[0] of the writer, end = the birth date of root CLAUDE.md §B + 100 years, committed verbatim as ISO 8601 UTC strings, half-open (SR-HORIZON-PUBLIC,
   SR-W34-LEASE format) · H2 a horizon the sources cannot state (non-UTC start, no birth date) is refused, never guessed (B.10) ·
K1 classes: the scored classes are the registry's rows with a membership (ROW_MEMBERSHIP value not None; birth_anchor excluded) ·
P1 policy: the certification policy is the arm the writer takes for an unmarked run (STRICT = raise), read from the writer; P2 final rules / deferral come from the pack's VERIFY_DEFERRAL.json
   with its sha, and a non-boolean value refuses ·
T1 cap = the migration's SET writer_timeout_seconds; timeout = the pipeline job's own --task-timeout (not another job's); T2 a cap not below the task timeout is refused (the watchdog must fire first) ·
O1 output tables = the shared ABSENCE_TABLES, each proven by its CREATE TABLE migration to carry chart_id + generation, with its class column ·
L1 the committed file is exactly what the repository's sources generate (the staleness detector; the image digest is checked in test_century_contract_smalltest_image.py).
"""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from types import SimpleNamespace

import pytest

from test_executor_scheduler_reaper import COMMIT, FLEET, REPO, World

spec = importlib.util.spec_from_file_location("century_contract_under_test", FLEET / "century_contract.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

PATH = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"
ARGS = {"classes": "all"}


def contract_body(**overrides):
    doc = {"schema": "ky.century_contract/1", "launch_args": dict(ARGS), "horizon": {"start": "2001-02-03T00:00:00+00:00", "end": "2090-03-04T00:00:00+00:00"}}
    doc.update(overrides)
    return (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode()


class CenturyWorld(World):
    """The real executor on a throwaway KY_ROOT with a Git double that serves one contract blob per commit."""

    def __init__(self, tmp_path, monkeypatch, blobs=None):
        super().__init__(tmp_path, monkeypatch, name="ky_exec_century_contract")
        self.blobs = {COMMIT: contract_body()} if blobs is None else blobs
        self.shown = []
        monkeypatch.setattr(self.mod, "smalltest_policy_problem", lambda req: None)     # the evidence policy has its own tests; this file judges the contract gate

    def git(self, *args, **kwargs):
        if len(args) == 2 and args[0] == "show" and args[1].endswith(":" + PATH):
            self.shown.append(args[1])
            commit = args[1].split(":", 1)[0]
            blob = self.blobs.get(commit)
            return SimpleNamespace(returncode=0 if blob is not None else 128, stdout=blob.decode() if blob is not None else "", stderr="")
        return super().git(*args, **kwargs)

    def request(self, kind="century_dispatch_dryrun", sha=None, args=None, **kw):
        req = super().request(kind, ARGS if args is None else args, **kw)
        req["item_id"] = "J-4e"
        req["century_contract_sha256"] = hashlib.sha256(contract_body()).hexdigest() if sha is None else sha
        return req


@pytest.fixture
def world(tmp_path, monkeypatch):
    return CenturyWorld(tmp_path, monkeypatch)


# ───────────────────────────── E1 the dispatch is bound to the contract's sha ─────────────────────────────
@pytest.mark.parametrize("kind", ["century_dispatch", "century_dispatch_dryrun"])
def test_e1_a_different_contract_sha_is_refused_and_the_matching_one_is_not(world, kind):
    m = world.mod
    good = world.request(kind)
    assert m.century_contract_problem(good) is None                                           # positive control: the sha of the blob at the reviewed commit
    other = world.request(kind, sha=hashlib.sha256(contract_body(horizon={"start": "x", "end": "y"})).hexdigest())
    assert "does not equal the sha256 of fleet/century_contract.json at the reviewed commit" in m.century_contract_problem(other)
    for missing in (None, "", "ABC", "a" * 63, 7):
        req = world.request(kind)
        req["century_contract_sha256"] = missing
        assert "century_contract_sha256 (64 lowercase hex) is required" in m.century_contract_problem(req), missing


def test_e1_validate_runs_the_gate_for_the_dry_run(world):
    assert world.validate(world.request()) is None
    refusal = world.validate(world.request(sha="0" * 64))
    assert refusal and "century_contract_sha256 does not equal" in refusal


# ───────────────────────────── E2 read at the reviewed commit ─────────────────────────────
def test_e2_the_contract_is_read_at_the_requests_reviewed_commit(tmp_path, monkeypatch):
    other_commit = "b" * 40
    w = CenturyWorld(tmp_path, monkeypatch, blobs={COMMIT: contract_body(), other_commit: contract_body(horizon={"start": "moved", "end": "moved"})})
    req = w.request()
    assert w.mod.century_contract_problem(req) is None and w.shown == [f"{COMMIT}:{PATH}"]
    req["reviewed_commit"] = other_commit                                                      # same sha text, a different blob at the other commit
    assert "does not equal the sha256" in w.mod.century_contract_problem(req)
    req["reviewed_commit"] = "c" * 40                                                          # no contract at that commit at all
    assert "not at the reviewed commit" in w.mod.century_contract_problem(req)


# ───────────────────────────── E3 launch_args are the request's args ─────────────────────────────
def test_e3_the_contracts_launch_args_must_be_the_requests_args(tmp_path, monkeypatch):
    blob = contract_body(launch_args={"classes": "one"})
    w = CenturyWorld(tmp_path, monkeypatch, blobs={COMMIT: blob})
    req = w.request(sha=hashlib.sha256(blob).hexdigest())
    assert "differ from the century contract's launch_args" in w.mod.century_contract_problem(req)
    notjson = b"not json\n"
    w2 = CenturyWorld(tmp_path / "b", monkeypatch, blobs={COMMIT: notjson})
    assert "is not JSON" in w2.mod.century_contract_problem(w2.request(sha=hashlib.sha256(notjson).hexdigest()))
    wrong = contract_body(schema="ky.century_contract/2")
    w3 = CenturyWorld(tmp_path / "c", monkeypatch, blobs={COMMIT: wrong})
    assert "is not a ky.century_contract/1" in w3.mod.century_contract_problem(w3.request(sha=hashlib.sha256(wrong).hexdigest()))


# ───────────────────────────── E4 other kinds are untouched ─────────────────────────────
@pytest.mark.parametrize("kind", ["century_teardown_dryrun", "century_cancel_dryrun", "smalltest_dispatch", "readback_sql"])
def test_e4_other_kinds_are_not_gated(world, kind):
    assert world.mod.century_contract_problem({"kind": kind, "reviewed_commit": COMMIT}) is None
    assert world.shown == []


# ───────────────────────────── generator fixtures (synthetic bounds) ─────────────────────────────
WRITER_REL = cc.WRITER


def tree(tmp_path, *, start="datetime(2001, 2, 3, tzinfo=timezone.utc)", unmarked="POLICY_RAISE", final_key="gochara_v5_final_rules", birth="born 1990-03-04"):
    root = tmp_path / "repo"
    files = {
        cc.WRITER: (f"DEFAULT_HORIZON = ({start},\n                   datetime(2030, 1, 1, tzinfo=timezone.utc))\nDEFER_VERIFY_KEY = \"gochara_v5_defer_in_build_verify\"\n"
                    f"policy = (gk_contact_certify.POLICY_SINK_ALL if slice_ is not None and slice_.run == \"x\" else gk_contact_certify.{unmarked})\n"
                    f"final = ctx.config.get(\"{final_key}\")\n"),
        cc.BIRTH_PATH: f"# Master\nThe synthetic subject, {birth}, somewhere.\n",
        cc.REGISTRY: "ROW_MEMBERSHIP: dict[str, str | None] = {\n    \"marriage\": \"m\",\n    \"birth_anchor\": None,\n    \"career_entry\": \"c\",\n    \"bereavement\": \"b\",\n}\n",
        cc.CERTIFY: "POLICY_RAISE = \"raise\"\nPOLICY_SINK_ALL = \"sink_all\"\n",
        cc.CAP_MIGRATION: "-- header SET writer_timeout_seconds = 1 in prose\nBEGIN;\n  UPDATE asset_registry\n     SET writer_timeout_seconds = 5000\n   WHERE asset_id = 'x';\n",
        cc.DEPLOY: ("      - run: |\n          gcloud run jobs update other-job \\\n            --task-timeout=300 \\\n            --quiet\n"
                    "          gcloud run jobs update brahma-build-pipeline-job \\\n            --region=r \\\n            --image=reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }} \\\n"
                    "            --task-timeout=9000 \\\n            --memory=16Gi \\\n            --quiet\n"),
        cc.DISPATCH: "LAUNCH_JOB = \"job-x\"\nLAUNCH_PROJECT = \"proj-x\"\nLAUNCH_REGION = \"region-x\"\n",
        "platform/migrations/0001_t.sql": ("CREATE TABLE IF NOT EXISTS public.syn_a (\n  id UUID PRIMARY KEY,\n  -- natural key (chart_id, generation, event_class),\n  chart_id UUID NOT NULL,\n"
                                          "  generation TEXT NOT NULL,\n  event_class TEXT NOT NULL,\n  CONSTRAINT syn_a_ck CHECK (generation <> '')\n);\n"
                                          "CREATE TABLE public.syn_b (chart_id UUID, generation TEXT);\nCREATE TABLE public.syn_cov (chart_id UUID, generation TEXT, partition_kind TEXT, partition_key TEXT);\n"
                                          "CREATE TABLE public.syn_nogen (chart_id UUID);\nALTER TABLE public.syn_b\n  ADD COLUMN event_class text;\n"),
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root


# ───────────────────────────── H1/H2 the horizon ─────────────────────────────
def test_h1_horizon_is_the_writers_start_and_birth_plus_100_years_as_iso_utc_strings(tmp_path):
    h = cc.horizon(tree(tmp_path))
    assert (h["start"], h["end"], h["interval"]) == ("2001-02-03T00:00:00+00:00", "2090-03-04T00:00:00+00:00", "[start, end)")     # birth 1990-03-04 + 100 y; NOT the writer's own end (2030-01-01)
    start, end = (dt.datetime.fromisoformat(h[k]) for k in ("start", "end"))
    assert start.utcoffset() == dt.timedelta(0) and end.utcoffset() == dt.timedelta(0) and start < end
    assert all(isinstance(h[k], str) for k in ("start", "end"))                                 # strings, never epoch integers (SR-W34-LEASE)


def test_h2_a_horizon_the_sources_cannot_state_is_refused(tmp_path):
    with pytest.raises(cc.ContractError, match="datetime"):
        cc.horizon(tree(tmp_path, start="datetime(2001, 2, 3)"))
    with pytest.raises(cc.ContractError, match="born"):
        cc.horizon(tree(tmp_path / "b", birth="no date here"))


# ───────────────────────────── K1 classes ─────────────────────────────
def test_k1_scored_classes_are_the_registry_rows_with_a_membership(tmp_path):
    k = cc.classes(tree(tmp_path), {"classes": "all"})
    assert (k["selector"], k["scored"], k["count"]) == ("all", ["bereavement", "career_entry", "marriage"], 3)


# ───────────────────────────── P1/P2 policy ─────────────────────────────
def test_p1_the_policy_is_the_writers_unmarked_arm(tmp_path):
    unmarked = cc.policy(tree(tmp_path), None)["certification"]
    assert (unmarked["sink_policy"], unmarked["strict"]) == ("raise", True)
    flipped = cc.policy(tree(tmp_path / "b", unmarked="POLICY_SINK_ALL"), None)
    assert (flipped["certification"]["sink_policy"], flipped["certification"]["strict"]) == ("sink_all", False)
    assert cc.policy(tree(tmp_path / "c"), None)["config_keys"] == {"final_rules": "gochara_v5_final_rules", "defer_in_build_verify": "gochara_v5_defer_in_build_verify"}


def test_p2_final_rules_and_deferral_are_the_packs_with_its_sha(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    body = json.dumps({"carrier": {"args": {"final_rules": "true", "defer_in_build_verify": "false"}}}).encode()
    (pack / cc.PACK_FILE).write_bytes(body)
    p = cc.policy(tree(tmp_path), pack)
    assert (p["final_rules"], p["defer_in_build_verify"], p["source"]["sha256"]) == (True, False, hashlib.sha256(body).hexdigest())
    (pack / cc.PACK_FILE).write_text(json.dumps({"carrier": {"args": {"final_rules": "yes", "defer_in_build_verify": "true"}}}))
    with pytest.raises(cc.ContractError, match="final_rules"):
        cc.policy(tree(tmp_path / "b"), pack)


# ───────────────────────────── T1/T2 cap and timeout ─────────────────────────────
def test_t1_cap_and_timeout_come_from_their_own_sources(tmp_path):
    root = tree(tmp_path)
    assert cc.cap(root)["writer_timeout_seconds"] == 5000                                      # the SET statement, not the figure quoted in the header prose
    t = cc.task_timeout(root)
    assert t["cloud_run_task_timeout_seconds"] == 9000 and t["source"].endswith(":8")        # the pipeline job's step, not the other job's 300
    assert cc.image(root, False)["repository"] == "reg.example/p/brahma-pipeline"


def test_t2_a_cap_not_below_the_task_timeout_is_refused():
    cc.check_cap_below_timeout({"writer_timeout_seconds": 5000}, {"cloud_run_task_timeout_seconds": 9000})
    for cap in (9000, 9001):
        with pytest.raises(cc.ContractError, match="not below the Cloud Run task timeout"):
            cc.check_cap_below_timeout({"writer_timeout_seconds": cap}, {"cloud_run_task_timeout_seconds": 9000})


# ───────────────────────────── O1 output tables ─────────────────────────────
def test_o1_output_tables_are_the_shared_absence_tables_proven_by_their_migrations(tmp_path):
    root = tree(tmp_path)
    shared = SimpleNamespace(ABSENCE_TABLES=(("syn_a", ""), ("syn_b", ""), ("syn_cov", " AND partition_kind = 'event_class'")))
    got = {t["object"]: (t["table"], t["class_column"], t["where"]) for t in cc.output_tables(root, shared)}
    assert got == {"syn_a": ("public.syn_a", "event_class", None), "syn_b": ("public.syn_b", "event_class", None),          # a comment's "(chart_id, generation," never splits a column
                   "syn_cov": ("public.syn_cov", "partition_key", "partition_kind = 'event_class'")}
    with pytest.raises(cc.ContractError, match="syn_nogen"):
        cc.output_tables(root, SimpleNamespace(ABSENCE_TABLES=(("syn_nogen", ""),)))


# ───────────────────────────── L1 the committed file is what the sources generate ─────────────────────────────
def test_l1_the_committed_contract_is_what_the_repository_sources_generate():
    committed = json.loads((REPO / PATH).read_text())
    derived = cc.derive(REPO, None, with_digest=False)
    assert cc.compare(committed, derived, with_digest=False, with_pack=False) == []
    assert (REPO / PATH).read_bytes().endswith(b"\n") and b"\r" not in (REPO / PATH).read_bytes()      # LF bytes: git show and the file hash the same
    assert isinstance(committed["image"]["writer_source_digest"], str) and len(committed["image"]["writer_source_digest"]) == 64


def test_l1_a_contract_that_drifted_from_its_sources_is_reported():
    committed = json.loads((REPO / PATH).read_text())
    derived = cc.derive(REPO, None, with_digest=False)
    moved = copy.deepcopy(committed)
    moved["horizon"]["end"] = "2085-02-05T00:00:00+00:00"
    assert cc.compare(moved, derived, with_digest=False, with_pack=False) == ["horizon"]
    moved = copy.deepcopy(committed)
    moved["policy"]["final_rules"] = "true"                                                    # a typed value that is not a boolean never passes the pack-less check
    assert cc.compare(moved, derived, with_digest=False, with_pack=False) != []
