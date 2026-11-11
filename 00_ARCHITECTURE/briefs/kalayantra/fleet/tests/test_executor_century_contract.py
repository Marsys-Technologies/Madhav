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
import subprocess
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


def legacy_workflow():
    return """env:
  GCP_REGION: region-x
  DEPLOY_SHA: ${{ github.event.workflow_run.head_sha || github.sha }}
jobs:
  another-job:
    steps:
      - run: |
          gcloud run jobs update other-job --task-timeout=300
  deploy-pipeline-job:
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ env.DEPLOY_SHA }}
      - name: Build and push pipeline job image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform/python-sidecar/Dockerfile.pipeline
          push: true
          tags: |
            reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }}
            reg.example/p/brahma-pipeline:latest
          cache-from: type=gha,scope=brahma-pipeline
          cache-to: type=gha,mode=max,scope=brahma-pipeline
      - name: Re-point Cloud Run Job at the new image
        run: |
          gcloud run jobs update brahma-build-pipeline-job \\
            --region=${{ env.GCP_REGION }} \\
            --image=reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }} \\
            --task-timeout=9000 \\
            --quiet
      - name: Verify ga_writers is importable in the pushed image
        run: |
          docker run --rm --entrypoint python \\
            reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }} \\
            -c "import ga_writers; print('ga_writers OK:', ga_writers.__file__)"
      - name: Verify the gochara century runner exists in the pushed image
        run: |
          docker run --rm --entrypoint /bin/sh \\
            reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }} \\
            -n /app/platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh
          docker run --rm --entrypoint python \\
            reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }} \\
            -c "import sys; sys.path.insert(0, '/app/platform/python-sidecar/scripts/kala_gochara_cutover'); import common; print('cutover common OK:', common.__file__)"
"""


def tree(tmp_path, *, start="datetime(2001, 2, 3, tzinfo=timezone.utc)", unmarked="POLICY_RAISE", final_key="gochara_v5_final_rules", birth="born 1990-03-04"):
    root = tmp_path / "repo"
    files = {
        cc.WRITER: (f"DEFAULT_HORIZON = ({start},\n                   datetime(2030, 1, 1, tzinfo=timezone.utc))\nDEFER_VERIFY_KEY = \"gochara_v5_defer_in_build_verify\"\n_RESULT_POLICY_KEY = \"result_policy\"\n"
                    f"policy = (gk_contact_certify.POLICY_SINK_ALL if slice_ is not None and slice_.run == \"x\" else gk_contact_certify.{unmarked})\n"
                    f"final = ctx.config.get(\"{final_key}\")\n"),
        cc.SHARED: "CENTURY_RESULT_POLICIES = ('all_null_candidate/1', 'window_qualification/1')\n",
        cc.BIRTH_PATH: f"# Master\nThe synthetic subject, {birth}, somewhere.\n",
        cc.REGISTRY: "ROW_MEMBERSHIP: dict[str, str | None] = {\n    \"marriage\": \"m\",\n    \"birth_anchor\": None,\n    \"career_entry\": \"c\",\n    \"bereavement\": \"b\",\n}\n",
        cc.CERTIFY: "POLICY_RAISE = \"raise\"\nPOLICY_SINK_ALL = \"sink_all\"\n",
        cc.CAP_MIGRATION: "-- header SET writer_timeout_seconds = 1 in prose\nBEGIN;\n  UPDATE asset_registry\n     SET writer_timeout_seconds = 5000\n   WHERE asset_id = 'x';\n",
        cc.DEPLOY: legacy_workflow(),
        cc.DISPATCH: 'LAUNCH_JOB = "brahma-build-pipeline-job"\nLAUNCH_PROJECT = "proj-x"\nLAUNCH_REGION = "region-x"\n',
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
    assert cc.policy(tree(tmp_path / "c"), None)["config_keys"] == {"final_rules": "gochara_v5_final_rules", "defer_in_build_verify": "gochara_v5_defer_in_build_verify",
                                                                                 "result_policy": "result_policy"}


def test_p2_final_rules_and_deferral_are_the_packs_with_its_sha(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    body = json.dumps({"carrier": {"args": {"final_rules": "true", "defer_in_build_verify": "false", "result_policy": "window_qualification/1"}}}).encode()
    (pack / cc.PACK_FILE).write_bytes(body)
    p = cc.policy(tree(tmp_path), pack)
    assert (p["final_rules"], p["defer_in_build_verify"], p["source"]["sha256"]) == (True, False, hashlib.sha256(body).hexdigest())
    assert p["result_policy"] == "window_qualification/1"                                       # OD-1: the policy is the pack's, like the other two
    (pack / cc.PACK_FILE).write_text(json.dumps({"carrier": {"args": {"final_rules": "yes", "defer_in_build_verify": "true", "result_policy": "window_qualification/1"}}}))
    with pytest.raises(cc.ContractError, match="final_rules"):
        cc.policy(tree(tmp_path / "b"), pack)
    for bad in (None, "all_null", "numeric/1"):                                                  # absent or unnamed policy: refused, never defaulted
        args = {"final_rules": "true", "defer_in_build_verify": "true", **({} if bad is None else {"result_policy": bad})}
        (pack / cc.PACK_FILE).write_text(json.dumps({"carrier": {"args": args}}))
        with pytest.raises(cc.ContractError, match="result_policy"):
            cc.policy(tree(tmp_path / "c"), pack)


# ───────────────────────────── T1/T2 cap and timeout ─────────────────────────────
def test_t1_cap_and_timeout_come_from_their_own_sources(tmp_path):
    root = tree(tmp_path)
    assert cc.cap(root)["writer_timeout_seconds"] == 5000                                      # the SET statement, not the figure quoted in the header prose
    t = cc.task_timeout(root)
    timeout_line = next(i for i, line in enumerate(legacy_workflow().splitlines(), 1) if "--task-timeout=9000" in line)
    assert t == {"cloud_run_task_timeout_seconds": 9000, "source": f"{cc.DEPLOY}:{timeout_line}"}
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


@pytest.fixture
def verified_pipeline(tmp_path):
    # Only the existing source wiring, never execution or a registry response.
    paths = (cc.DEPLOY, cc.DISPATCH, f"{cc._VERIFIED_ACTION}/action.yml", cc._PROBE)
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((REPO / relative).read_bytes())
    return tmp_path


def _replace_at(path, old, new, *, after=None, before=None):
    source = path.read_text()
    prefix, active = "", source
    if after is not None:
        at = source.index(after) + len(after)
        prefix, active = source[:at], source[at:]
    suffix = ""
    if before is not None:
        end = active.index(before)
        active, suffix = active[:end], active[end:]
    assert active.count(old) == 1
    path.write_text(prefix + active.replace(old, new) + suffix)


def test_verified_pipeline_uses_the_same_repository_and_physical_timeout(verified_pipeline):
    committed = json.loads((REPO / PATH).read_text())
    image = cc.image(verified_pipeline, False)
    assert image["repository"] == committed["image"]["repository"]
    assert cc.task_timeout(verified_pipeline) == {
        "cloud_run_task_timeout_seconds": 86400, "source": f"{cc.DEPLOY}:2543",
    }


@pytest.mark.parametrize(("old", "new"), [
    ("  deploy-pipeline-job:\n", "  decoy-job:\n"),
    ("  deploy-pipeline-job:\n", "  deploy-pipeline-job:\n  deploy-pipeline-job:\n"),
    ("  deploy-pipeline-job:\n", '  "deploy-pipeline-job": {}\n  deploy-pipeline-job:\n'),
    ("  deploy-pipeline-job:\n", "  deploy-pipeline-job:\n    env:\n      DEPLOY_SHA: rebound\n"),
    ("      - name: Build and push pipeline job image\n", "      - name: Other builder\n"),
    ("      - name: Build and push pipeline job image\n", "      - name: Build and push pipeline job image\n" * 2),
    ("      - name: Re-point Cloud Run Job at the new image\n", "      - name: Unbound repoint\n"),
    ("      - name: Re-point Cloud Run Job at the new image\n", "      - name: Re-point Cloud Run Job at the new image\n" * 2),
    ("      - name: Re-point Cloud Run Job at the new image\n",
     "      - name: Extra builder\n        uses: docker/build-push-action@v6\n"
     "      - name: Re-point Cloud Run Job at the new image\n"),
    ("      - name: Re-point Cloud Run Job at the new image\n",
     "      - name: Rebind carrier\n        run: fixture-command\n"
     "      - name: Re-point Cloud Run Job at the new image\n"),
    ("    steps:\n", "    steps: []\n    steps:\n"),
    ("          ref: ${{ env.DEPLOY_SHA }}\n", "          ref: stale\n"),
    ("      - name: Set up Docker Buildx\n",
     "      - uses: actions/checkout@v4\n      - name: Set up Docker Buildx\n"),
    ("      - name: Set up Docker Buildx\n",
     "      - id: decoy\n        name: Build and push pipeline job image\n"
     "      - name: Set up Docker Buildx\n"),
    ("      - name: Set up Docker Buildx\n",
     "      - uses: docker/build-push-action@v6\n      - name: Set up Docker Buildx\n"),
    ("          context: .\n", "          context: ./platform\n"),
    ("          file: ./platform/python-sidecar/Dockerfile.pipeline\n", "          file: ./other/Dockerfile\n"),
    ("          push: true\n", "          push: false\n"),
    ("brahma-pipeline:${{ env.DEPLOY_SHA }}\n", "wrong-pipeline:${{ env.DEPLOY_SHA }}\n"),
    ("brahma-pipeline:${{ env.DEPLOY_SHA }}\n", "brahma-pipeline:${{ github.sha }}\n"),
    (f"          {cc._PROBE_RUN} verify-repoint\n", ""),
    (f"          {cc._PROBE_RUN} verify-repoint\n",
     f"          {cc._PROBE_RUN} post-repoint\n"),
    (f'          GOOGLE_CLOUD_REGION="{cc._REGION}" {cc._PROBE_RUN} post-repoint\n', ""),
    (f'          GOOGLE_CLOUD_REGION="{cc._REGION}" {cc._PROBE_RUN} post-repoint\n',
     f'          GOOGLE_CLOUD_REGION="{cc._REGION}" {cc._PROBE_RUN} verify-repoint\n'),
    (cc._VERIFIED_REF, "${{ env.DEPLOY_SHA }}"),
    (cc._VERIFIED_REF, "reg.example/p/brahma-pipeline@sha256:broken"),
    (cc._VERIFIED_REF, ' "$CGM_VERIFIED_IMAGE"'),
    ("--task-timeout=86400", "--task-timeout=0"),
    ("--task-timeout=86400", "--flags-file=fixture.yaml"),
    ("--task-timeout=86400", "--task-timeout=86400 --task-timeout=1"),
    ("          gcloud run jobs update brahma-build-pipeline-job",
     "          printf '%s' gcloud run jobs update brahma-build-pipeline-job"),
    ("--image=", "--image "),
])
def test_unbound_or_ambiguous_pipeline_wiring_fails(verified_pipeline, old, new):
    path = verified_pipeline / cc.DEPLOY
    after = None if old.startswith("  deploy-pipeline-job:") else "  deploy-pipeline-job:\n"
    _replace_at(path, old, new, after=after, before="  deployment-outcome:\n")
    with pytest.raises(cc.ContractError):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize(("relative", "old", "new", "message"), [
    (f"{cc._VERIFIED_ACTION}/action.yml", "steps.build.outputs.digest", "steps.decoy.outputs.digest", "Buildx output"),
    (f"{cc._VERIFIED_ACTION}/action.yml", "runs:\n", "runs: {}\nruns:\n", "duplicate top-level"),
    (f"{cc._VERIFIED_ACTION}/action.yml", "  load:\n", "  'load': {}\n  load:\n", "exact inputs"),
    (f"{cc._VERIFIED_ACTION}/action.yml", "default: 'false'\n  tags:", "default: 'true'\n  tags:", "push-only"),
    (cc._PROBE, 'sha256:[0-9a-f]{64}', 'sha256:[0-9a-f]+', "source and platform"),
    (cc._PROBE, 'require(head == source_commit(),', 'require(True,', "carrier construction"),
    (cc._PROBE, 'require(configured == reference,', 'require(configured.startswith(reference),', "readback"),
])
def test_mutated_action_or_probe_cannot_supply_the_verified_carrier(verified_pipeline, relative, old, new, message):
    _replace_at(verified_pipeline / relative, old, new)
    with pytest.raises(cc.ContractError, match=message):
        cc.image(verified_pipeline, False)


def test_unrelated_comments_and_probe_formatting_do_not_change_the_proof(verified_pipeline):
    for relative in (cc._PROBE, f"{cc._VERIFIED_ACTION}/action.yml"):
        path = verified_pipeline / relative
        path.write_text("# comment-only fixture change\n" + path.read_text() + "\n")
    assert cc.image(verified_pipeline, False)["repository"].endswith("/brahma-pipeline")


@pytest.mark.parametrize("replacement", [
    "            --task-timeout=86401",
    "            # fixture moved the locator\n            --task-timeout=86400",
])
def test_strict_v1_comparison_retains_timeout_value_line_and_cap(verified_pipeline, replacement):
    committed = json.loads((REPO / PATH).read_text())
    derived = copy.deepcopy(committed)
    path = verified_pipeline / cc.DEPLOY
    _replace_at(path, "            --task-timeout=86400", replacement)
    derived["timeout"] = cc.task_timeout(verified_pipeline)
    assert cc.compare(committed, derived, with_digest=True, with_pack=True) == ["timeout"]
    derived["cap"]["writer_timeout_seconds"] += 1
    assert cc.compare(committed, derived, with_digest=True, with_pack=True) == ["cap", "timeout"]


def test_wrong_job_cannot_supply_a_decoy_image_repoint(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + """
  decoy-job:
    steps:
      - run: |
          gcloud run jobs update brahma-build-pipeline-job --image=reg.example/brahma-pipeline:stale
""")
    with pytest.raises(cc.ContractError, match="outside the Pipeline job"):
        cc.image(verified_pipeline, False)


def test_rebound_global_deploy_source_is_refused(verified_pipeline):
    _replace_at(verified_pipeline / cc.DEPLOY, cc._SOURCE_ENV, "DEPLOY_SHA: ${{ github.sha }}")
    with pytest.raises(cc.ContractError, match="DEPLOY_SHA source"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("command", [
    "gcloud  run jobs update brahma-build-pipeline-job",
    "gcloud run \\\n  jobs update brahma-build-pipeline-job",
    "gcloud\trun jobs update 'brahma-build-pipeline-job'",
])
def test_later_pipeline_image_override_is_refused_despite_shell_spacing(verified_pipeline, command):
    command += " --image=synthetic.example/project/brahma-pipeline:other --task-timeout=96000"
    observed = subprocess.run(
        ["/bin/bash", "-c", 'gcloud() { printf "%s\\n" "$@"; }\n' + command],
        env={}, check=True, capture_output=True, text=True,
    )
    assert observed.stdout.splitlines() == [
        "run", "jobs", "update", "brahma-build-pipeline-job",
        "--image=synthetic.example/project/brahma-pipeline:other", "--task-timeout=96000",
    ]
    step = "      - name: Later fixture repoint\n        run: |\n" + "".join(
        f"          {line}\n" for line in command.splitlines()
    )
    _replace_at(verified_pipeline / cc.DEPLOY, "  deployment-outcome:\n", step + "  deployment-outcome:\n")
    with pytest.raises(cc.ContractError, match="one actual Pipeline job update"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("flag", [
    "--task-timeout 96000", "--image=synthetic.example/project/brahma-pipeline:other",
    "--flags-file=fixture.yaml",
])
def test_other_job_cannot_override_pipeline_repoint_through_shell_spacing(verified_pipeline, flag):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + (
        "\n  decoy-job:\n    steps:\n      - run: |\n"
        "          gcloud --project=fixture run \\\n"
        f"            jobs update {flag} 'brahma-build-pipeline-job'\n"
    ))
    with pytest.raises(cc.ContractError, match="outside the Pipeline job"):
        cc.image(verified_pipeline, False)


def test_other_job_can_keep_its_credential_only_update(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + """
  credential-fixture:
    steps:
      - run: |
          gcloud  run jobs update 'brahma-build-pipeline-job' --set-secrets=VALUE=fixture:latest
""")
    assert cc.image(verified_pipeline, False)["repository"].endswith("/brahma-pipeline")
    assert cc.task_timeout(verified_pipeline)["source"] == f"{cc.DEPLOY}:2543"



@pytest.mark.parametrize("run_field", [
    '        run: "gcloud run jobs update brahma-build-pipeline-job --task-timeout=96000"\n',
    "        run: >-\n          gcloud run\n          jobs update brahma-build-pipeline-job --task-timeout=96000\n",
])
def test_later_pipeline_override_cannot_hide_in_another_yaml_run_form(verified_pipeline, run_field):
    step = "      - name: Later fixture override\n" + run_field
    _replace_at(verified_pipeline / cc.DEPLOY, "  deployment-outcome:\n", step + "  deployment-outcome:\n")
    with pytest.raises(cc.ContractError, match="one actual Pipeline job update"):
        cc.image(verified_pipeline, False)


def test_a_retained_smoke_step_cannot_be_replaced_with_an_unreviewed_command(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    old = '''            -c "import ga_writers; print('ga_writers OK:', ga_writers.__file__)"'''
    _replace_at(path, old, "            -c fixture_modified", after="  deploy-pipeline-job:\n")
    with pytest.raises(cc.ContractError, match="unexpected Pipeline step after"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("run_field", [
    '        run: "gcloud run jobs update brahma-build-pipeline-job --task-timeout=96000"\n',
    "        run: >-\n          gcloud run\n          jobs update brahma-build-pipeline-job --task-timeout=96000\n",
    "        run: 'gcloud run jobs update brahma-build-pipeline-job --task-timeout=96000'\n",
])
def test_dependent_job_cannot_hide_a_pipeline_override_in_a_run_scalar(verified_pipeline, run_field):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + (
        "\n  dependent-fixture:\n    needs: [deploy-pipeline-job]\n    steps:\n"
        "      - name: Fixture override\n" + run_field
    ))
    with pytest.raises(cc.ContractError, match="outside the Pipeline job"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("run_field", [
    '        run: "gcloud run jobs update brahma-build-pipeline-job --set-secrets=VALUE=fixture:latest"\n',
    "        run: >-\n          gcloud run\n          jobs update brahma-build-pipeline-job --set-secrets=VALUE=fixture:latest\n",
])
def test_credential_only_rebind_still_accepts_run_scalars(verified_pipeline, run_field):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + (
        "\n  credential-scalar-fixture:\n    needs: [deploy-pipeline-job]\n    steps:\n"
        "      - name: Fixture credentials\n" + run_field
    ))
    assert cc.image(verified_pipeline, False)["repository"].endswith("/brahma-pipeline")
    assert cc.task_timeout(verified_pipeline)["source"] == f"{cc.DEPLOY}:2543"


def test_visible_override_inside_a_literal_shell_argument_keeps_the_prior_guard(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + """
  literal-shell-fixture:
    needs: [deploy-pipeline-job]
    steps:
      - run: |
          bash -c 'gcloud run jobs update brahma-build-pipeline-job --task-timeout=96000'
""")
    with pytest.raises(cc.ContractError, match="outside the Pipeline job"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("run_header", [
    "        run: >2-\n",
    '        "run": >-\n',
    "        'run': >-2\n",
])
def test_unbound_folded_pipeline_mutation_is_refused(verified_pipeline, run_header):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + (
        "\n  dependent-fixture:\n    needs: [deploy-pipeline-job]\n    steps:\n"
        "      - name: Ambiguous override\n" + run_header +
        "          gcloud run\n          jobs update brahma-build-pipeline-job --task-timeout=96000\n"
    ))
    with pytest.raises(cc.ContractError, match="ambiguous Pipeline image or timeout mutation"):
        cc.image(verified_pipeline, False)


def test_unbound_pipeline_mutation_cannot_hide_in_an_earlier_step(verified_pipeline):
    marker = "      - name: Build and push pipeline job image\n"
    step = """      - name: Ambiguous earlier override
        "run": >2-
          gcloud run
          jobs update brahma-build-pipeline-job --image=synthetic.example/project/brahma-pipeline:other
"""
    _replace_at(verified_pipeline / cc.DEPLOY, marker, step + marker)
    with pytest.raises(cc.ContractError, match="ambiguous Pipeline image or timeout mutation"):
        cc.image(verified_pipeline, False)


def test_credential_only_step_stays_separate_from_an_unrelated_job_update(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text() + """
  credential-fixture:
    needs: [deploy-pipeline-job]
    steps:
      - name: Fixture credentials
        "run": >2-
          gcloud run
          jobs update brahma-build-pipeline-job --set-secrets=VALUE=fixture:latest
      - name: Unrelated fixture
        run: gcloud run jobs update fixture-other-job --image=synthetic.example/project/other:tag
""")
    assert cc.image(verified_pipeline, False)["repository"].endswith("/brahma-pipeline")
    assert cc.task_timeout(verified_pipeline)["source"] == f"{cc.DEPLOY}:2543"
