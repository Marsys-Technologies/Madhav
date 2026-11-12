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
CURRENT_REGION = "${{ env.DEPLOY_REGION }}"


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
    (f'          GOOGLE_CLOUD_REGION="{CURRENT_REGION}" {cc._PROBE_RUN} post-repoint\n', ""),
    (f'          GOOGLE_CLOUD_REGION="{CURRENT_REGION}" {cc._PROBE_RUN} post-repoint\n',
     f'          GOOGLE_CLOUD_REGION="{CURRENT_REGION}" {cc._PROBE_RUN} verify-repoint\n'),
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


@pytest.mark.parametrize("change", ["value", "coordinate"])
def test_strict_v1_comparison_retains_timeout_value_line_and_cap(verified_pipeline, change):
    committed = json.loads((REPO / PATH).read_text())
    derived = copy.deepcopy(committed)
    path = verified_pipeline / cc.DEPLOY
    if change == "value":
        _replace_at(path, "            --task-timeout=86400", "            --task-timeout=86401")
        expected = {"cloud_run_task_timeout_seconds": 86401, "source": f"{cc.DEPLOY}:2543"}
    else:
        # Move the coordinate without altering the shell argv inside run: |.
        step = "      - name: Re-point Cloud Run Job at the new image"
        _replace_at(path, step, "      # synthetic YAML-only locator movement\n" + step)
        expected = {"cloud_run_task_timeout_seconds": 86400, "source": f"{cc.DEPLOY}:2544"}
    derived["timeout"] = cc.task_timeout(verified_pipeline)
    assert derived["timeout"] == expected
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
    with pytest.raises(cc.ContractError, match="unexpected Pipeline local image checks"):
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


# Standalone reviewed historical fixtures. A shallow checkout must not need old
# Git objects to prove the original action and all pinned proof groups still work.
HISTORICAL_VERIFIED_ACTION = r'''name: Build and verify CGM image
description: Bind the normal build to a read-only probe of the packaged CGM writer registrations.
inputs:
  context:
    description: Existing Docker context
    required: true
  file:
    description: Existing Sidecar or Pipeline Dockerfile
    required: true
  push:
    description: Existing registry export mode
    default: 'false'
  load:
    description: Existing local export mode
    default: 'false'
  tags:
    description: Existing build tags
    required: true
  cache-from:
    description: Existing Buildx cache source
  cache-to:
    description: Existing Buildx cache destination
runs:
  using: composite
  steps:
    - id: build
      uses: docker/build-push-action@v6
      with:
        context: ${{ inputs.context }}
        file: ${{ inputs.file }}
        push: ${{ inputs.push }}
        load: ${{ inputs.load }}
        tags: ${{ inputs.tags }}
        cache-from: ${{ inputs.cache-from }}
        cache-to: ${{ inputs.cache-to }}
    - name: Verify exact packaged CGM registration
      shell: bash
      env:
        CGM_BUILD_CONTEXT: ${{ inputs.context }}
        CGM_BUILD_FILE: ${{ inputs.file }}
        CGM_BUILD_PUSH: ${{ inputs.push }}
        CGM_BUILD_LOAD: ${{ inputs.load }}
        CGM_BUILD_TAGS: ${{ inputs.tags }}
        CGM_BUILD_IMAGE_ID: ${{ steps.build.outputs.imageid }}
        CGM_BUILD_DIGEST: ${{ steps.build.outputs.digest }}
        CGM_BUILD_METADATA: ${{ steps.build.outputs.metadata }}
      run: python3 "$GITHUB_ACTION_PATH/probe_registration.py" verify-build
'''
HISTORICAL_VERIFIED_PROBE = r'''"""Read-only CGM registration probe for the two normal image shapes."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


SIDECAR = "amjis-sidecar"
PIPELINE = "brahma-pipeline"
REGISTRY = "asia-south1-docker.pkg.dev/madhav-astrology/amjis"
SOURCE_ROOT = "platform/python-sidecar"
BUILD_SHAPES = {
    "./platform/python-sidecar/Dockerfile": (SIDECAR, "./platform"),
    "./platform/python-sidecar/Dockerfile.pipeline": (PIPELINE, "."),
}
PACKAGE_ROOTS = {
    SIDECAR: "/app/python-sidecar",
    PIPELINE: "/app/platform/python-sidecar",
}
MODULES = (
    "bodha_writers.cgm_identity",
    "pipeline.orchestrator.writers.bo_bimba",
    "pipeline.orchestrator.writers.bo_karanajala",
)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
MANIFEST_TYPES = {
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}
INDEX_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}


class ProbeFailure(ValueError):
    """A fixed, safe diagnostic that can be written to the workflow log."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProbeFailure(reason)


def digest(value: object) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise ProbeFailure("missing or invalid image digest")
    return value


def command(*args: str, data: bytes | None = None, timeout: int = 30) -> bytes:
    result = subprocess.run(
        args,
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    require(result.returncode == 0, f"{args[0]} {args[1]} failed")
    return result.stdout


def manifest_identity(ref: str) -> tuple[str, str]:
    manifest = json.loads(command(
        "docker", "buildx", "imagetools", "inspect", "--format", "{{json .Manifest}}", ref,
    ))
    top = digest(manifest["digest"])
    if manifest["mediaType"] in MANIFEST_TYPES:
        return top, top
    require(manifest["mediaType"] in INDEX_TYPES, "unsupported image manifest")
    matches = [
        item for item in manifest["manifests"]
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == "amd64"
    ]
    require(len(matches) == 1, "expected exactly one Linux AMD64 platform image")
    require(matches[0]["mediaType"] in MANIFEST_TYPES, "unsupported platform manifest")
    return top, digest(matches[0]["digest"])


def inspect_loaded(ref: str, expected_id: str) -> str:
    image = json.loads(command("docker", "image", "inspect", "--format", "{{json .}}", ref))
    image_id = digest(image["Id"])
    require(image_id == expected_id, "loaded image identity mismatch")
    require((image["Os"], image["Architecture"]) == ("linux", "amd64"), "wrong image platform")
    require(not image["Config"].get("Volumes"), "probe image declares writable volumes")
    return image_id


def loaded_build_id() -> str:
    output = os.environ.get("CGM_BUILD_IMAGE_ID")
    metadata = json.loads(os.environ.get("CGM_BUILD_METADATA") or "{}")
    config = metadata.get("containerimage.config.digest")
    if output and config:
        require(output == config, "contradictory Buildx image IDs")
    return digest(output or config)


def source_commit() -> str:
    commit = os.environ["DEPLOY_SHA"]
    require(COMMIT.fullmatch(commit) is not None, "invalid deployment source")
    return commit


def check_pipeline_tag(tag: str, expected: tuple[str, str]) -> None:
    require(manifest_identity(tag) == expected, "Pipeline commit tag does not match the probed image")


def pipeline_reference(commit: str, image: str) -> str:
    repository = f"{REGISTRY}/{PIPELINE}"
    prefix = f"{repository}@"
    require(COMMIT.fullmatch(commit) is not None, "invalid Pipeline source")
    require(image.startswith(prefix), "wrong verified Pipeline repository")
    return f"{repository}:{commit}@{digest(image.removeprefix(prefix))}"


def verified_pipeline_reference() -> str:
    image = os.environ.get("CGM_VERIFIED_IMAGE", "")
    reference = pipeline_reference(source_commit(), image)
    require(
        os.environ.get("CGM_VERIFIED_PIPELINE_REF") == reference,
        "missing or rebound verified Pipeline reference",
    )
    return reference


def source_hashes(commit: str) -> list[str]:
    return [
        hashlib.sha256(command("git", "show", f"{commit}:{SOURCE_ROOT}/{name.replace('.', '/')}.py")).hexdigest()
        for name in MODULES
    ]


def probe_image(component: str, image_id: str, expected: list[str]) -> None:
    output = command(
        "docker", "run", "--pull=never", "--rm", "-i", "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--entrypoint=/usr/bin/env",
        image_id, "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "python", "-BI",
        "-X", "pycache_prefix=/dev/null", "-",
        "inside", component, *expected,
        data=Path(__file__).read_bytes(), timeout=30,
    )
    require(output == b"CGM registration verified\n", "missing exact packaged probe result")


def verify_build() -> None:
    component, context = BUILD_SHAPES[os.environ["CGM_BUILD_FILE"]]
    require(os.environ["CGM_BUILD_CONTEXT"] == context, "wrong Docker build context")
    mode = (os.environ["CGM_BUILD_PUSH"], os.environ["CGM_BUILD_LOAD"])
    tags = os.environ["CGM_BUILD_TAGS"].splitlines()
    head = command("git", "rev-parse", "HEAD").decode().strip()
    require(COMMIT.fullmatch(head) is not None, "invalid checkout source")
    expected = source_hashes(head)

    if mode == ("false", "true"):
        local_tag = f"{component}:pr-check"
        require(tags == [local_tag], "unexpected ordinary image tag")
        image_id = inspect_loaded(local_tag, loaded_build_id())
        probe_image(component, image_id, expected)
        print(f"CGM {component} source={head} image={image_id} registration verified")
        return

    require(mode == ("true", "false"), "unsupported build export mode")
    require(head == source_commit(), "deployment checkout mismatch")
    repository = f"{REGISTRY}/{component}"
    commit_tag = f"{repository}:{head}"
    require(tags == [commit_tag, f"{repository}:latest"], "unexpected release image tags")
    build_digest = digest(os.environ.get("CGM_BUILD_DIGEST"))
    top, platform = manifest_identity(f"{repository}@{build_digest}")
    require(top == build_digest, "registry image differs from Buildx output")
    image = f"{repository}@{platform}"
    manifest = json.loads(command("docker", "buildx", "imagetools", "inspect", "--raw", image))
    require(manifest["mediaType"] in MANIFEST_TYPES, "expected a platform image manifest")
    expected_id = digest(manifest["config"]["digest"])
    command("docker", "pull", "--platform", "linux/amd64", image, timeout=180)
    image_id = inspect_loaded(image, expected_id)
    probe_image(component, image_id, expected)
    if component == PIPELINE:
        check_pipeline_tag(commit_tag, (top, platform))

    # Publish only validated, non-secret identifiers to later steps of this job.
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as env_file:
        env_file.write(f"CGM_VERIFIED_IMAGE={image}\n")
        if component == PIPELINE:
            env_file.write(f"CGM_VERIFIED_PIPELINE_REF={pipeline_reference(head, image)}\n")
    print(f"CGM {component} source={head} image={image} registration verified")


def post_repoint() -> None:
    reference = verified_pipeline_reference()
    configured = command(
        "gcloud", "run", "jobs", "describe", "brahma-build-pipeline-job",
        "--region", os.environ["GOOGLE_CLOUD_REGION"],
        "--format=value(spec.template.spec.template.spec.containers[0].image)",
    ).decode().removesuffix("\n")
    require(configured == reference, "configured Pipeline image is not the verified combined reference")
    print(f"CGM Pipeline configuration verified image={reference}")


def verify_registration(root: Path, expected: list[str]) -> None:
    require(len(expected) == len(MODULES), "missing source fingerprints")
    paths = []
    for name, checksum in zip(MODULES, expected):
        path = root / f"{name.replace('.', '/')}.py"
        require(path.resolve(strict=True) == path, "shadowed packaged source")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == checksum, "packaged source hash mismatch")
        paths.append(path)

    sys.path.insert(0, str(root))
    identity, bimba, karanajala = (importlib.import_module(name) for name in MODULES)
    for module, path in zip((identity, bimba, karanajala), paths):
        require(Path(module.__file__).resolve(strict=True) == path, "wrong loaded module origin")
    registry = importlib.import_module("pipeline.orchestrator.writers")
    for asset, cls in (
        ("bo_bimba", bimba.BoBimbaWriter),
        ("bo_karanajala", karanajala.BoKaranajalaWriter),
    ):
        require(issubclass(cls, registry.WriterBase), "wrong writer base")
        require(registry.WRITER_REGISTRY.get(asset) is cls, "incorrect concrete registration")

    for module, aliases in (
        (bimba, {
            "_SUBJECT_TO_GRAHA": "SUBJECT_TO_GRAHA",
            "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
            "_yoga_config_name": "_yoga_config_name",
            "yoga_node_subject": "yoga_node_subject",
        }),
        (karanajala, {
            "_GRAHA_SUBJECT_MAP": "SUBJECT_TO_GRAHA",
            "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
            "_yoga_node_subject": "yoga_node_subject",
        }),
    ):
        for old, shared in aliases.items():
            require(getattr(module, old) is getattr(identity, shared), "incorrect historical alias identity")


def main() -> None:
    mode, *args = sys.argv[1:]
    if mode == "verify-build" and not args:
        verify_build()
    elif mode == "verify-repoint" and not args:
        verified_pipeline_reference()
    elif mode == "post-repoint" and not args:
        post_repoint()
    elif mode == "inside":
        component, *expected = args
        verify_registration(Path(PACKAGE_ROOTS[component]), expected)
        print("CGM registration verified")
    else:
        raise ProbeFailure("invalid probe mode")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never print raw registry, subprocess, or application output.
        if isinstance(exc, ProbeFailure):
            print(f"CGM verification failed: {exc}", file=sys.stderr)
        else:
            print("CGM verification failed: missing or invalid evidence", file=sys.stderr)
        raise SystemExit(1) from None
'''


@pytest.fixture
def historical_verified_pipeline(verified_pipeline):
    action = verified_pipeline / cc._VERIFIED_ACTION / "action.yml"
    probe = verified_pipeline / cc._PROBE
    action.write_text(HISTORICAL_VERIFIED_ACTION)
    probe.write_text(HISTORICAL_VERIFIED_PROBE)
    workflow = verified_pipeline / cc.DEPLOY
    source = workflow.read_text().replace("DEPLOY_REGION", "GCP_REGION")
    start = source.index('          local_image="${CGM_VERIFIED_LOCAL_IMAGE_ID:')
    end = source.index(f"          {cc._PROBE_RUN} verify-repoint\n", start)
    assert [line.strip() for line in source[start:end].splitlines()] == list(cc._LOADED_REPOINT_PREAMBLE)
    # Preserve the original physical timeout coordinate while changing the form.
    padding = "          # historical fixture preamble padding\n" * len(cc._LOADED_REPOINT_PREAMBLE)
    source = source[:start] + padding + source[end:]
    tail = legacy_workflow().split("      - name: Verify ga_writers", 1)[1]
    tail = "      - name: Verify ga_writers" + tail
    tail = tail.replace("reg.example/p/brahma-pipeline:${{ env.DEPLOY_SHA }}", '"$CGM_VERIFIED_IMAGE"')
    source = source.replace("  deployment-outcome:\n", tail + "  deployment-outcome:\n")
    workflow.write_text(source)
    return verified_pipeline


def test_historical_verified_action_and_all_original_probe_groups_are_supported(historical_verified_pipeline):
    assert cc.image(historical_verified_pipeline, False)["repository"].endswith("/brahma-pipeline")
    assert cc.task_timeout(historical_verified_pipeline) == {
        "cloud_run_task_timeout_seconds": 86400, "source": f"{cc.DEPLOY}:2543",
    }


@pytest.mark.parametrize(("old", "new", "message"), [
    ("sha256:[0-9a-f]{64}", "sha256:[0-9a-f]+", "source and platform"),
    ("require(head == source_commit(),", "require(True,", "carrier construction"),
    ("require(configured == reference,", "require(configured.startswith(reference),", "readback"),
])
def test_historical_probe_proof_refusals_are_retained(historical_verified_pipeline, old, new, message):
    _replace_at(historical_verified_pipeline / cc._PROBE, old, new)
    with pytest.raises(cc.ContractError, match=message):
        cc.image(historical_verified_pipeline, False)


@pytest.mark.parametrize("region_name", ["GCP_REGION", "DEPLOY_REGION"])
def test_both_supported_region_names_bind_one_literal_launch_region(verified_pipeline, region_name):
    path = verified_pipeline / cc.DEPLOY
    path.write_text(path.read_text().replace("DEPLOY_REGION", region_name))
    assert cc.image(verified_pipeline, False)["region"] == cc._literal(cc.DISPATCH, "LAUNCH_REGION", verified_pipeline)


@pytest.mark.parametrize("change", ["duplicate", "both-names", "expression", "wrong-literal", "quoted", "nested"])
def test_region_sources_cannot_be_duplicated_ambiguous_or_indirect(verified_pipeline, change):
    path = verified_pipeline / cc.DEPLOY
    region = cc._literal(cc.DISPATCH, "LAUNCH_REGION", verified_pipeline)
    declaration = f"  DEPLOY_REGION: {region}\n"
    replacement = {
        "duplicate": declaration * 2,
        "both-names": declaration + f"  GCP_REGION: {region}\n",
        "expression": "  DEPLOY_REGION: ${{ vars.REGION }}\n",
        "wrong-literal": "  DEPLOY_REGION: wrong-region\n",
        "quoted": f"  'DEPLOY_REGION': {region}\n",
        "nested": f"  REGION_BLOCK:\n    DEPLOY_REGION: {region}\n",
    }[change]
    _replace_at(path, declaration, replacement)
    with pytest.raises(cc.ContractError):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize(("old", "new"), [
    ('local_image="${CGM_VERIFIED_LOCAL_IMAGE_ID:?missing verified local image}"', 'local_image="fixture:unverified"'),
    ('[[ "$local_image" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 1', 'true'),
    ('--platform=linux/amd64 --format', '--platform=linux/arm64 --format'),
    ('test "$local_platform" = "${CGM_VERIFIED_IMAGE##*@}" || exit 1', 'true'),
    ('--pull=never', '--pull=always'),
    ('--network=none', '--network=host'),
    ('--entrypoint /bin/sh', '--entrypoint python'),
    ('-n /app/platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh', '-c pass'),
])
def test_loaded_preamble_keeps_exact_identity_platform_and_three_local_checks(verified_pipeline, old, new):
    path = verified_pipeline / cc.DEPLOY
    source = path.read_text()
    start = source.index("      - name: Re-point Cloud Run Job at the new image\n")
    before = source[:start]
    active = source[start:]
    assert old in active
    path.write_text(before + active.replace(old, new))
    with pytest.raises(cc.ContractError):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("change", ["run-comment", "space-after-backslash"])
def test_loaded_pipeline_rejects_broken_shell_continuations_without_locator_drift(verified_pipeline, change):
    path = verified_pipeline / cc.DEPLOY
    lines = path.read_text().splitlines()
    start = lines.index("      - name: Re-point Cloud Run Job at the new image")
    command = next(i for i in range(start, len(lines)) if lines[i].strip().startswith("docker run "))
    assert lines[command].endswith("\\") and lines[command + 1].strip().startswith("-c ")

    def bash_result(smoke):
        # The stub checks the actual run command's argv; Docker never runs.
        script = ('local_image=synthetic\n'
                  'docker() { [[ "$#" == 10 && "${9}" == -c ]]; }\n'
                  + "\n".join(smoke))
        return subprocess.run(["/bin/bash", "--noprofile", "--norc", "-e", "-c", script],
                              env={}, capture_output=True, check=False).returncode

    assert bash_result(lines[command:command + 2]) == 0
    timeout = cc.task_timeout(verified_pipeline)
    if change == "run-comment":
        lines.insert(command + 1, "          # synthetic comment breaks the continued command")
        assert bash_result(lines[command:command + 3]) != 0
        del lines[max(i for i in range(start) if not lines[i].strip())]
    else:
        lines[command] += " "
        assert bash_result(lines[command:command + 2]) != 0
    assert timeout["source"] == f"{cc.DEPLOY}:2543"
    assert lines[2542].strip() == "--task-timeout=86400 \\"
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(cc.ContractError, match="physically contiguous"):
        cc.task_timeout(verified_pipeline)


@pytest.mark.parametrize(("old", "new"), [
    ("type=docker", "type=registry"),
    ("type=provenance,mode=max", "type=provenance,mode=min"),
    ("CGM_BUILD_LOAD: ${{ inputs.push == 'true' && 'true' || inputs.load }}", "CGM_BUILD_LOAD: ${{ inputs.load }}"),
])
def test_loaded_action_export_provenance_and_mode_are_exact(verified_pipeline, old, new):
    _replace_at(verified_pipeline / cc._VERIFIED_ACTION / "action.yml", old, new)
    with pytest.raises(cc.ContractError, match="Buildx output"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize(("old", "new"), [
    ('require(image_id == loaded_build_id(),', 'require(True,'),
    ('"--platform=linux/amd64",) if platform else ()', '"--platform=linux/arm64",) if platform else ()'),
    ('digest(descriptor.get("digest")) == expected_id', 'True'),
    ('require(not config.get("Volumes"),', 'require(True,'),
    ('check_loaded_descriptor(selected, platform_digest, MANIFEST_TYPES)', 'check_loaded_descriptor(selected, local_id, MANIFEST_TYPES)'),
    ('content_digest(raw), json_object(raw, stage)', '"sha256:" + "a" * 64, json_object(raw, stage)'),
    ('"--network=none", "--read-only"', '"--network=host", "--read-only"'),
])
def test_loaded_identity_and_isolation_proof_cannot_be_weakened(verified_pipeline, old, new):
    _replace_at(verified_pipeline / cc._PROBE, old, new)
    with pytest.raises(cc.ContractError, match="source and platform"):
        cc.image(verified_pipeline, False)


def test_loaded_commit_tag_check_is_required_for_both_release_components(verified_pipeline):
    _replace_at(verified_pipeline / cc._PROBE, "check_release_tag(commit_tag, (top, platform))", "require(True, 'unbound tag')")
    with pytest.raises(cc.ContractError, match="carrier construction"):
        cc.image(verified_pipeline, False)


@pytest.mark.parametrize("change", ["extra-import", "extra-definition", "reordered-definition"])
def test_loaded_probe_scaffolding_definition_membership_and_order_are_bound(verified_pipeline, change):
    path = verified_pipeline / cc._PROBE
    source = path.read_text()
    if change == "extra-import":
        source = "import socket\n" + source
    elif change == "extra-definition":
        source += "\ndef unexpected_helper():\n    return None\n"
    else:
        old = "def content_digest(data: bytes) -> str:\n    return f\"sha256:{hashlib.sha256(data).hexdigest()}\"\n\n\n"
        assert source.count(old) == 1
        source = source.replace(old, "")
        source = source.replace("def command(", old + "def command(", 1)
    path.write_text(source)
    with pytest.raises(cc.ContractError, match="declaration order|imports and entry point"):
        cc.image(verified_pipeline, False)


def test_loaded_policy_cannot_accept_the_historical_probe(verified_pipeline):
    (verified_pipeline / cc._PROBE).write_text(HISTORICAL_VERIFIED_PROBE)
    with pytest.raises(cc.ContractError, match="declaration order"):
        cc.image(verified_pipeline, False)


def test_historical_policy_cannot_accept_the_loaded_probe(historical_verified_pipeline):
    (historical_verified_pipeline / cc._PROBE).write_bytes((REPO / cc._PROBE).read_bytes())
    with pytest.raises(cc.ContractError, match="declaration order"):
        cc.image(historical_verified_pipeline, False)


def test_loaded_mode_refuses_every_additional_tail_step(verified_pipeline):
    path = verified_pipeline / cc.DEPLOY
    source = path.read_text().replace(
        "  deployment-outcome:\n",
        "      - name: Unreviewed tail\n        run: true\n  deployment-outcome:\n",
    )
    path.write_text(source)
    with pytest.raises(cc.ContractError, match="unexpected Pipeline step after"):
        cc.image(verified_pipeline, False)
