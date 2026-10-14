"""`kypacket.py check` (relaunch plan v2.7 §8; packet KV3-B-KYPACKET): one admitted packet of each kind, one packet
refused with exactly each reason code, the own-input (exit 66) and usage (exit 64) refusals, and the calibration of
the byte bound — on packets and a throwaway git repository built under the pytest base. The command line is the
contract, so every case runs the script as a child process."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
SCRIPT = FLEET / "kypacket.py"
F = "00_ARCHITECTURE/briefs/kalayantra/fleet"
T = "platform/scripts/governance/pravaha_tracker"
RECEIPTS = "00_ARCHITECTURE/control/kalayantra"
GIT = "/usr/bin/git"
GIT_ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="t",
               GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
for _name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "KY_GIT"):
    GIT_ENV.pop(_name, None)

sys.path.insert(0, str(FLEET))

import kypacket  # noqa: E402

PLAN_TEXT = "# Plan\n\nAlpha line one.\nAlpha line two — with §8.\n\nBeta paragraph, one line.\n"
NOTES_OLD = "note one\nnote two\n"
NOTES_NEW = "note one\nnote two, revised\n"
TEST_TEXT = "def test_feature():\n    assert False, 'expected 12 windows, found 0'\n"
EXCERPT = "```excerpt plan §8\nAlpha line one.\nAlpha line two — with §8.\n```\n"
ZEROS = "0" * 64
ABSENT_COMMIT = "1" * 40
KU = json.loads((FLEET / "templates" / "ku_bindings.json").read_text(encoding="utf-8"))["clauses"]


def sha(data) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def git(repo, *args) -> str:
    done = subprocess.run([GIT, "-C", str(repo), "-c", "commit.gpgsign=false", *args], env=GIT_ENV,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


class World:
    """the throwaway repository and what the packets pin in it"""

    def __init__(self, base: Path):
        self.repo = base / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        self.put("docs/PLAN.md", PLAN_TEXT)
        self.put("docs/NOTES.md", NOTES_OLD)
        self.put("tests/test_feature.py", TEST_TEXT)
        self.put(f"{RECEIPTS}/SCHEMA_RECEIPT_v9_9.json", json.dumps({"schema_receipt_id": "SR-TEST-1"}))
        self.c1 = self.commit("one")
        self.put("docs/NOTES.md", NOTES_NEW)
        self.c2 = self.commit("two")
        self.plan_blob = git(self.repo, "rev-parse", f"{self.c1}:docs/PLAN.md")

    def put(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, message) -> str:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def plan_source(self, **changes) -> dict:
        source = {"path": "docs/PLAN.md", "revision": self.c1, "section_range": "§8", "sha256": sha(PLAN_TEXT)}
        source.update(changes)
        return source

    def common(self, **front) -> dict:
        base = {"id": None, "kind": None, "wave": 0, "build_tier": "sonnet", "routing_reason": "test (plan §9)",
                "needs_chart_data": False, "max_loops": 3, "plan_version": "2.7",
                "spec_sources": [self.plan_source()], "schema_receipt_id": "SR-TEST-1",
                "pw_mechanism_version": "1.0", "release_pins": {"dash_build": "dash-1", "registry_revision": 412},
                "packet_sha256": ZEROS}
        base.update(front)
        return base

    def bootstrap(self, **front) -> dict:
        base = self.common(
            id="KV3-B-DEMO", kind="bootstrap", wave="B", build_tier="opus", schema_receipt_id=None,
            pw_mechanism_version=None, release_pins="not_applicable: bootstrap",
            d1_paths=["tools/demo.py", "tools/tests/test_demo.py"],
            acceptance={"command": "python3 -B -m pytest tools/tests/test_demo.py -q -p no:cacheprovider",
                        "expected_result": "all tests pass", "negative_cases": ["a refused input: exit 1"]})
        base.update(front)
        return base

    def feature(self, **front) -> dict:
        base = self.common(
            id="K4-2a", kind="feature", build_tier="opus", original_failing_base=self.c1,
            test_commits=[{"sha": self.c1, "digest": sha(TEST_TEXT), "path": "tests/test_feature.py"}],
            expected_failing_assertion="AssertionError: expected 12 windows, found 0")
        base.update(front)
        return base

    def artifact(self, **front) -> dict:
        base = self.common(id="J-0c", kind="artifact", semantic_acceptance="the join lists every member once",
                           negative_fixtures=["a member missing from the join"])
        base.update(front)
        return base


@pytest.fixture(scope="module")
def world(tmp_path_factory) -> World:
    return World(tmp_path_factory.mktemp("kypacket_world"))


def render(front: dict, body: str, stamp: bool = True) -> bytes:
    """the packet file: fenced front matter, then the body; stamped per the packet's check 3"""
    text = "```json\n" + json.dumps(front, ensure_ascii=False, indent=1) + "\n```\n" + body
    data = text.encode("utf-8")
    if stamp and front.get("packet_sha256") == ZEROS:
        field = f'"packet_sha256": "{ZEROS}"'.encode()
        assert data.count(field) == 1
        data = data.replace(field, f'"packet_sha256": "{sha(data)}"'.encode())
    return data


def write(tmp_path: Path, front: dict, body: str = "# demo\n\n" + EXCERPT, name=None, stamp=True) -> Path:
    path = tmp_path / (name or f"PACKET_{front['id']}_v1.md")
    path.write_bytes(render(front, body, stamp))
    return path


def run(packet, repo, script=SCRIPT, **env):
    return subprocess.run([sys.executable, "-B", str(script), "check", str(packet), "--repo", str(repo)],
                          env=dict(GIT_ENV, **env), capture_output=True, text=True)


def admitted(done) -> dict:
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout)
    assert report["admitted"] is True and report["reasons"] == [] and done.stderr == ""
    return report


def refused(done, code: str) -> dict:
    """exit 1, exactly the one reason code, named on stdout and on stderr"""
    assert done.returncode == 1, done.stdout + done.stderr
    report = json.loads(done.stdout)
    assert report["schema"] == "ky.packet_check/1" and report["admitted"] is False
    assert {reason["code"] for reason in report["reasons"]} == {code}, report["reasons"]
    lines = done.stderr.splitlines()
    assert len(lines) == len(report["reasons"])
    for line, reason in zip(lines, report["reasons"]):
        assert line == f"refused: {reason['code']}: {reason['detail']}"
    return report


# --------------------------------------------------------------------------------------------------------------
# admitted: one packet of each kind
# --------------------------------------------------------------------------------------------------------------
def test_a_bootstrap_packet_is_admitted_and_the_report_has_the_contract_shape(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    report = admitted(run(packet, world.repo))
    data = packet.read_bytes()
    stamped = json.loads(data.decode().split("```")[1][len("json"):])["packet_sha256"]
    assert list(report) == ["schema", "packet", "id", "admitted", "packet_sha256", "size", "labels", "reasons"]
    assert report["schema"] == "ky.packet_check/1"
    assert report["packet"] == str(packet) and os.path.isabs(report["packet"])
    assert report["id"] == "KV3-B-DEMO"
    assert report["packet_sha256"] == stamped == sha(data.replace(stamped.encode(), ZEROS.encode()))
    assert report["size"] == {"method": "calibrated_byte_bound", "bytes": len(data), "bound": 9000, "tokens": None}
    assert report["labels"] == []


def test_a_feature_packet_is_admitted(world, tmp_path):
    assert admitted(run(write(tmp_path, world.feature()), world.repo))["id"] == "K4-2a"


def test_an_artifact_packet_is_admitted(world, tmp_path):
    assert admitted(run(write(tmp_path, world.artifact()), world.repo))["id"] == "J-0c"


def test_the_check_is_read_only(world, tmp_path):
    packet = write(tmp_path, world.feature())
    before = (packet.read_bytes(), git(world.repo, "status", "--porcelain"), git(world.repo, "rev-parse", "HEAD"),
              sorted(p.name for p in tmp_path.iterdir()))
    admitted(run(packet, world.repo))
    assert before == (packet.read_bytes(), git(world.repo, "status", "--porcelain"),
                      git(world.repo, "rev-parse", "HEAD"), sorted(p.name for p in tmp_path.iterdir()))


def test_a_relative_packet_path_is_reported_absolute(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    done = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", packet.name, "--repo", str(world.repo)],
                          env=GIT_ENV, capture_output=True, text=True, cwd=tmp_path)
    assert os.path.isabs(admitted(done)["packet"])


def test_repo_may_precede_the_packet(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    done = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", "--repo", str(world.repo), str(packet)],
                          env=GIT_ENV, capture_output=True, text=True)
    admitted(done)


# --------------------------------------------------------------------------------------------------------------
# 1 format
# --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["packet.md", "PACKET_KV3-B-DEMO.md", "PACKET_KV3-B-DEMO_v1.txt",
                                  "PACKET_KV3-B-DEMO_v0.md", "PACKET_KV3-B-DEMO_v1.md.bak"])
def test_a_name_that_is_not_a_packet_name_is_refused(world, tmp_path, name):
    refused(run(write(tmp_path, world.bootstrap(), name=name), world.repo), "not_single_file")


def test_a_directory_a_symlink_and_a_missing_file_are_refused(world, tmp_path):
    folder = tmp_path / "d" / "PACKET_KV3-B-DEMO_v1.md"
    folder.mkdir(parents=True)
    report = refused(run(folder, world.repo), "not_single_file")
    assert report["packet_sha256"] is None and report["size"]["bytes"] is None
    real = write(tmp_path, world.bootstrap())
    link = tmp_path / "l" / real.name
    link.parent.mkdir()
    link.symlink_to(real)
    refused(run(link, world.repo), "not_single_file")
    refused(run(tmp_path / "PACKET_KV3-B-GONE_v1.md", world.repo), "not_single_file")


def front_matter_variants(world):
    good = render(world.bootstrap(), "# demo\n\n" + EXCERPT)
    text = good.decode()
    yield "first line has a trailing space", text.replace("```json\n", "```json \n", 1).encode()
    yield "first line is a bare fence", text.replace("```json\n", "```\n", 1).encode()
    yield "byte order mark", b"\xef\xbb\xbf" + good
    yield "carriage returns", text.replace("\n", "\r\n").encode()
    yield "not UTF-8", good.replace("§".encode(), b"\xa7")
    yield "no closing fence", text.replace("\n```\n", "\n", 1).replace(EXCERPT, "").encode()
    yield "an array", ("```json\n[]\n```\n" + EXCERPT).encode()
    yield "two objects", text.replace("\n```\n", "\n{}\n```\n", 1).encode()
    yield "duplicate key", text.replace('{\n "id"', '{\n "id": "KV3-B-DEMO",\n "id"', 1).encode()
    yield "NaN", text.replace('"max_loops": 3', '"max_loops": NaN', 1).encode()
    yield "empty file", b""


def test_front_matter_that_is_not_one_strict_json_object_is_refused(world, tmp_path):
    variants = dict(front_matter_variants(world))
    assert len(variants) == 11
    for index, (label, data) in enumerate(variants.items()):
        packet = tmp_path / str(index) / "PACKET_KV3-B-DEMO_v1.md"
        packet.parent.mkdir()
        packet.write_bytes(data)
        report = refused(run(packet, world.repo), "front_matter_json")
        assert report["packet_sha256"] is None, label
        assert report["size"]["bytes"] == len(data), label


# --------------------------------------------------------------------------------------------------------------
# 2 schema
# --------------------------------------------------------------------------------------------------------------
def test_a_front_matter_the_schema_refuses_is_refused(world, tmp_path):
    report = refused(run(write(tmp_path, world.bootstrap(max_loops=9)), world.repo), "schema")
    assert "max_loops" in report["reasons"][0]["detail"]
    refused(run(write(tmp_path, world.bootstrap(build_tier="sonnet")), world.repo), "schema")
    refused(run(write(tmp_path, world.artifact(surprise=1)), world.repo), "schema")


def test_an_id_that_is_not_the_name_s_id_is_refused(world, tmp_path):
    packet = write(tmp_path, world.bootstrap(), name="PACKET_KV3-B-OTHER_v1.md")
    report = refused(run(packet, world.repo), "name_id_mismatch")
    assert report["id"] == "KV3-B-DEMO"


# --------------------------------------------------------------------------------------------------------------
# 3 packet_sha256
# --------------------------------------------------------------------------------------------------------------
def test_one_changed_body_byte_is_refused_and_the_computed_value_is_named(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    data = bytearray(packet.read_bytes())
    stamped = admitted(run(packet, world.repo))["packet_sha256"]
    at = data.index(b"# demo") + 2
    data[at] ^= 0x01
    packet.write_bytes(bytes(data))
    report = refused(run(packet, world.repo), "packet_sha256")
    computed = sha(bytes(data).replace(stamped.encode(), ZEROS.encode()))
    assert report["packet_sha256"] == computed != stamped
    assert computed in report["reasons"][0]["detail"]


def test_an_unstamped_packet_and_a_changed_front_matter_byte_are_refused(world, tmp_path):
    refused(run(write(tmp_path, world.bootstrap(), stamp=False), world.repo), "packet_sha256")
    packet = write(tmp_path, world.bootstrap())
    packet.write_bytes(packet.read_bytes().replace(b"test (plan", b"Test (plan", 1))
    refused(run(packet, world.repo), "packet_sha256")


def test_the_hash_is_over_the_file_with_only_the_field_zeroed(world, tmp_path):
    """the plain sha256 of the file (the launch input's hash, ruling P19) is not the front matter's"""
    front = world.bootstrap()
    data = render(front, "# demo\n\n" + EXCERPT, stamp=False)
    packet = tmp_path / "PACKET_KV3-B-DEMO_v1.md"
    packet.write_bytes(data.replace(ZEROS.encode(), sha(data.replace(ZEROS.encode(), b"")).encode()))
    refused(run(packet, world.repo), "packet_sha256")
    packet.write_bytes(data.replace(ZEROS.encode(), sha(data).encode()))
    admitted(run(packet, world.repo))


def test_a_second_packet_sha256_member_makes_the_field_ambiguous(world, tmp_path):
    front = world.common(id="KV3-SCHEMA-1", kind="schema-prerequisite",
                         intended_schema={"packet_sha256": ZEROS})
    data = render(front, "# demo\n\n" + EXCERPT, stamp=False)
    packet = tmp_path / "PACKET_KV3-SCHEMA-1_v1.md"
    packet.write_bytes(data)
    report = refused(run(packet, world.repo), "packet_sha256")
    assert report["packet_sha256"] is None


# --------------------------------------------------------------------------------------------------------------
# 4 pins
# --------------------------------------------------------------------------------------------------------------
def two_sources(world, **bad) -> list:
    """the plan, which carries the excerpt, and a second source that the case breaks"""
    second = {"path": "docs/NOTES.md", "revision": "v1", "section_range": "all", "sha256": sha(NOTES_NEW)}
    second.update(bad)
    return [world.plan_source(), second]


def test_a_spec_source_that_is_not_in_the_repository_is_refused(world, tmp_path):
    for path in ("docs/ABSENT.md", "docs", "/etc/hosts", str(world.repo / "docs/NOTES.md")):
        front = world.bootstrap(spec_sources=two_sources(world, path=path))
        report = refused(run(write(tmp_path, front), world.repo), "spec_source_missing")
        assert path in report["reasons"][0]["detail"]


def test_a_spec_source_reached_through_a_symlink_out_of_the_repository_is_refused(world, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text(NOTES_NEW, encoding="utf-8")
    link = world.repo / "docs" / "LINK.md"
    link.symlink_to(outside)
    try:
        front = world.bootstrap(spec_sources=two_sources(world, path="docs/LINK.md"))
        refused(run(write(tmp_path, front), world.repo), "spec_source_missing")
    finally:
        link.unlink()


def test_a_spec_source_with_another_sha256_is_refused(world, tmp_path):
    front = world.bootstrap(spec_sources=two_sources(world, sha256=sha(NOTES_OLD)))
    report = refused(run(write(tmp_path, front), world.repo), "spec_source_sha256")
    assert sha(NOTES_NEW) in report["reasons"][0]["detail"]


def test_a_pinned_commit_without_that_blob_is_refused(world, tmp_path):
    cases = {"the blob at that commit differs": world.c1, "no such commit": ABSENT_COMMIT,
             "a blob id, not a commit": world.plan_blob}
    for label, revision in cases.items():
        front = world.bootstrap(spec_sources=two_sources(world, revision=revision))
        refused(run(write(tmp_path, front), world.repo), "spec_source_revision")
    front = world.bootstrap(spec_sources=two_sources(world, revision=world.c2))
    admitted(run(write(tmp_path, front), world.repo))


def test_a_revision_that_is_a_document_version_is_pinned_by_its_sha256_alone(world, tmp_path):
    front = world.bootstrap(spec_sources=[world.plan_source(revision="v2.7")])
    admitted(run(write(tmp_path, front), world.repo))


def test_an_original_failing_base_that_is_not_a_commit_is_refused(world, tmp_path):
    for base in (ABSENT_COMMIT, world.plan_blob):
        front = world.feature(original_failing_base=base)
        report = refused(run(write(tmp_path, front), world.repo), "commit_unknown")
        assert base in report["reasons"][0]["detail"]


def test_a_schema_receipt_id_no_receipt_carries_is_refused(world, tmp_path):
    front = world.artifact(schema_receipt_id="SR-TEST-2")
    report = refused(run(write(tmp_path, front), world.repo), "schema_receipt_unresolved")
    assert "SR-TEST-2" in report["reasons"][0]["detail"]


def test_a_receipt_outside_the_receipt_location_does_not_resolve(world, tmp_path):
    stray = world.repo / "docs" / "SCHEMA_RECEIPT_v1_0.json"
    stray.write_text(json.dumps({"schema_receipt_id": "SR-STRAY"}), encoding="utf-8")
    broken = world.repo / RECEIPTS / "SCHEMA_RECEIPT_v0_0.json"
    broken.write_text('{"schema_receipt_id": "SR-BROKEN", "schema_receipt_id": "SR-BROKEN"}', encoding="utf-8")
    try:
        for receipt in ("SR-STRAY", "SR-BROKEN"):
            front = world.artifact(schema_receipt_id=receipt)
            refused(run(write(tmp_path, front), world.repo), "schema_receipt_unresolved")
        admitted(run(write(tmp_path, world.artifact()), world.repo))
    finally:
        stray.unlink()
        broken.unlink()


# --------------------------------------------------------------------------------------------------------------
# 5 size
# --------------------------------------------------------------------------------------------------------------
def sized(world, tmp_path, size: int) -> Path:
    body = "# demo\n\n" + EXCERPT
    short = len(render(world.bootstrap(), body))
    packet = write(tmp_path, world.bootstrap(), body + "x" * (size - short - 1) + "\n")
    assert packet.stat().st_size == size
    return packet


def test_a_9001_byte_packet_is_refused_and_a_9000_byte_packet_is_admitted(world, tmp_path):
    report = refused(run(sized(world, tmp_path, 9001), world.repo), "oversize")
    assert report["size"] == {"method": "calibrated_byte_bound", "bytes": 9001, "bound": 9000, "tokens": None}
    assert admitted(run(sized(world, tmp_path, 9000), world.repo))["size"]["bytes"] == 9000


def test_every_measured_card_is_under_4000_tokens_at_the_byte_bound():
    """the bound is calibrated, not measured: no record of the real program's measurement contradicts it"""
    measured = json.loads((FLEET / "cards" / "TOKEN_MEASUREMENT.json").read_text(encoding="utf-8"))
    assert len(measured["cards"]) >= 5
    for name, record in measured["cards"].items():
        assert record["tokens"] / record["bytes"] * kypacket.BYTE_BOUND <= 4000, name
    assert kypacket.BYTE_BOUND == 9000


# --------------------------------------------------------------------------------------------------------------
# 6 test availability
# --------------------------------------------------------------------------------------------------------------
def test_a_feature_packet_whose_test_blob_is_not_available_is_refused(world, tmp_path):
    good = world.feature()["test_commits"][0]
    cases = {"another digest": dict(good, digest=sha("other")), "no such path": dict(good, path="tests/absent.py"),
             "no such commit": dict(good, sha=ABSENT_COMMIT)}
    for label, entry in cases.items():
        front = world.feature(test_commits=[good, entry])
        report = refused(run(write(tmp_path, front), world.repo), "test_unavailable")
        assert len(report["reasons"]) == 1 and entry["path"] in report["reasons"][0]["detail"], label


@pytest.mark.parametrize("command", [
    "python3 -B -m pytest tools/tests/test_other.py -q",
    "python3 -B -m pytest xtools/tests/test_demo.py -q",
    "python3 -B -m pytest tools/tests/test_demo.pyc -q",
    "make test",
])
def test_a_bootstrap_packet_whose_command_names_no_d1_path_is_refused(world, tmp_path, command):
    front = world.bootstrap()
    front["acceptance"]["command"] = command
    refused(run(write(tmp_path, front), world.repo), "test_unavailable")


@pytest.mark.parametrize("command", [
    "python3 -B tools/demo.py --self-test && python3 -B -m pytest tools/tests/test_other.py -q",
    "python3 -B -m pytest 'tools/tests/test_demo.py' -q",
    "python3 -B -m pytest tools/tests/test_demo.py::test_one -q",
])
def test_a_bootstrap_command_that_names_a_d1_path_is_available(world, tmp_path, command):
    front = world.bootstrap()
    front["acceptance"]["command"] = command
    admitted(run(write(tmp_path, front), world.repo))


# --------------------------------------------------------------------------------------------------------------
# 7 excerpts
# --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("block", [
    "```excerpt plan §8\nAlpha line one.\nAlpha line two - with §8.\n```\n",
    "```excerpt plan §8\nAlpha line one.\n\nAlpha line two — with §8.\n```\n",
    "```excerpt plan §8\nAlpha line one. \n```\n",
    "```excerpt notes\nnote one\n```\n",
    "```excerpt plan §8\n```\n",
    "```excerpt plan §8\nAlpha line one.\n",
    "```excerpt plan §8\nAlpha line one.\n``` \n",
])
def test_an_excerpt_absent_from_its_pinned_sources_is_refused(world, tmp_path, block):
    report = refused(run(write(tmp_path, world.bootstrap(), "# demo\n\n" + block), world.repo),
                     "excerpt_not_in_source")
    assert len(report["reasons"]) == 1


def test_every_excerpt_is_checked_and_part_of_a_line_is_an_excerpt(world, tmp_path):
    part = "```excerpt plan, part of a line\nparagraph, one\n```\n"
    admitted(run(write(tmp_path, world.bootstrap(), "# demo\n\n" + EXCERPT + part), world.repo))
    bad = "```excerpt plan\nGamma.\n```\n"
    report = refused(run(write(tmp_path, world.bootstrap(), "# demo\n\n" + EXCERPT + bad + bad), world.repo),
                     "excerpt_not_in_source")
    assert len(report["reasons"]) == 2


def test_an_excerpt_is_not_sought_in_a_source_whose_pin_failed(world, tmp_path):
    """the working file is the pinned source only while it hashes to the pin"""
    front = world.bootstrap(spec_sources=[world.plan_source(sha256=sha("another plan"), revision="v2.7")])
    done = run(write(tmp_path, front), world.repo)
    assert done.returncode == 1
    assert [r["code"] for r in json.loads(done.stdout)["reasons"]] == ["spec_source_sha256", "excerpt_not_in_source"]


@pytest.mark.parametrize("body", [
    "# demo\n\nAlpha line one.\n",
    "# demo\n\n```\nAlpha line one.\n```\n",
    "# demo\n\n```text\nAlpha line one.\n```\n",
    "# demo\n\n```text\n```excerpt plan\nAlpha line one.\n```\n",
    "# demo\n\n ```excerpt plan\nAlpha line one.\n```\n",
])
def test_a_packet_with_no_excerpt_block_is_refused(world, tmp_path, body):
    refused(run(write(tmp_path, world.bootstrap(), body), world.repo), "no_excerpt")


# --------------------------------------------------------------------------------------------------------------
# 8 reconciliation
# --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("line", [
    "Reconciliation: the existing procedure stays as it is.",
    "Reconciliation: the existing procedure is `docs/NOTES.md`.",
    "Reconciliation: the existing procedure is docs/PLAN.md.",
    "Reconciliation: see `docs/PLAN.md §8`.",
])
def test_a_reconciliation_line_that_names_no_pinned_source_is_refused(world, tmp_path, line):
    body = "# demo\n\n" + EXCERPT + line + "\n"
    report = refused(run(write(tmp_path, world.bootstrap(), body), world.repo), "reconciliation_unpinned")
    assert len(report["reasons"]) == 1


def test_a_reconciliation_line_that_names_a_pinned_source_is_bound(world, tmp_path):
    body = ("# demo\n\n" + EXCERPT + "Reconciliation: `tools/x.py` is as `docs/PLAN.md` says.\n"
            "8. Reconciliation: a numbered line is not a claim.\n")
    admitted(run(write(tmp_path, world.bootstrap(), body), world.repo))
    report = refused(run(write(tmp_path, world.bootstrap(), body + "Reconciliation: none.\n"), world.repo),
                     "reconciliation_unpinned")
    assert len(report["reasons"]) == 1


# --------------------------------------------------------------------------------------------------------------
# 9 KU bindings
# --------------------------------------------------------------------------------------------------------------
def ku_body(*texts) -> str:
    return "# demo\n\n" + EXCERPT + "".join(f"```\n{text}\n```\n" for text in texts)


def owning(world, *paths) -> dict:
    return world.bootstrap(d1_paths=list(paths) + ["tools/tests/test_demo.py"])


def test_ku_01_altered_by_one_character_in_a_packet_owning_kyverdicts_is_refused(world, tmp_path):
    text = KU["KU-01"]["text"]
    front = owning(world, f"{F}/kyverdicts.py")
    assert admitted(run(write(tmp_path, front, ku_body(text)), world.repo))["labels"] == ["kyverdicts"]
    for altered in (text.replace("Audit", "audit", 1), text.replace("\n\n", "\n", 1), text[:-1]):
        assert altered != text
        report = refused(run(write(tmp_path, front, ku_body(altered)), world.repo), "ku_clause_missing")
        assert [r["detail"] for r in report["reasons"]] == ["KU-01"]
        assert report["labels"] == ["kyverdicts"]
    report = refused(run(write(tmp_path, front), world.repo), "ku_clause_missing")
    assert [r["detail"] for r in report["reasons"]] == ["KU-01"]


def test_each_registry_label_binds_the_clauses_that_require_it(world, tmp_path):
    for label, path in kypacket.REGISTRY.items():
        owned = path + "state.py" if path.endswith("/") else path
        needed = sorted(ku for ku, clause in KU.items() if label in clause["required_in"])
        assert needed, label
        report = refused(run(write(tmp_path, owning(world, owned)), world.repo), "ku_clause_missing")
        assert [r["detail"] for r in report["reasons"]] == needed and report["labels"] == [label]
        body = ku_body(*(KU[ku]["text"] for ku in needed))
        assert admitted(run(write(tmp_path, owning(world, owned), body), world.repo))["labels"] == [label]


def test_the_registry_is_the_packet_s_and_covers_every_binding():
    assert kypacket.REGISTRY == {
        "kyverdicts": f"{F}/kyverdicts.py", "kylock": f"{F}/kylock.sh", "kyversion": f"{F}/kyversion.sh",
        "local-db": f"{F}/local_db.sh", "preflight-v3": f"{F}/preflight.sh", "finalize-v3": f"{F}/finalize.sh",
        "dispatcher-ready-receipts": f"{F}/kyd_admit.py", "kyloop-crash-cleanup": f"{F}/kyloop.py",
        "tracker-semantics": f"{T}/"}
    assert {label for clause in KU.values() for label in clause["required_in"]} == set(kypacket.REGISTRY)


def test_a_path_beside_the_tracker_directory_carries_no_label(world, tmp_path):
    front = owning(world, f"{T}_other/state.py", f"{F}/kyverdicts.py.bak", "platform/scripts/governance/x.py")
    assert admitted(run(write(tmp_path, front), world.repo))["labels"] == []


def test_a_packet_owning_two_components_carries_every_clause(world, tmp_path):
    front = owning(world, f"{F}/kyverdicts.py", f"{F}/kyversion.sh", f"{T}/verdicts.py")
    report = refused(run(write(tmp_path, front, ku_body(KU["KU-01"]["text"])), world.repo), "ku_clause_missing")
    assert [r["detail"] for r in report["reasons"]] == ["KU-03"]
    assert report["labels"] == ["kyverdicts", "kyversion", "tracker-semantics"]


# --------------------------------------------------------------------------------------------------------------
# every failure is reported; no pass without a check
# --------------------------------------------------------------------------------------------------------------
def test_every_failure_is_reported_in_one_run(world, tmp_path):
    front = world.feature(original_failing_base=ABSENT_COMMIT, schema_receipt_id="SR-NONE", max_loops=9,
                          spec_sources=[world.plan_source(), world.plan_source(path="docs/ABSENT.md")])
    packet = write(tmp_path, front, "# demo\n\nReconciliation: none.\n" + "x" * 9000 + "\n",
                   name="PACKET_OTHER_v1.md")
    packet.write_bytes(packet.read_bytes() + b"\n")
    done = run(packet, world.repo)
    assert done.returncode == 1
    report = json.loads(done.stdout)
    assert [r["code"] for r in report["reasons"]] == [
        "schema", "name_id_mismatch", "packet_sha256", "spec_source_missing", "spec_source_revision",
        "commit_unknown", "schema_receipt_unresolved", "oversize", "no_excerpt", "reconciliation_unpinned"]
    assert done.stderr.count("\n") == len(report["reasons"]) and report["admitted"] is False


def test_a_git_that_cannot_read_objects_never_admits(world, tmp_path):
    fake = tmp_path / "git"
    fake.write_text(f'#!/bin/sh\ncase " $* " in *" rev-parse "*) exec {GIT} "$@";; esac\nexit 1\n')
    fake.chmod(0o755)
    packet = write(tmp_path, world.feature())
    done = run(packet, world.repo, KY_GIT=str(fake))
    assert done.returncode == 1
    assert [r["code"] for r in json.loads(done.stdout)["reasons"]] == [
        "spec_source_revision", "commit_unknown", "test_unavailable"]
    admitted(run(packet, world.repo, KY_GIT=GIT))


# --------------------------------------------------------------------------------------------------------------
# exit 66: an own input is missing, unreadable or invalid
# --------------------------------------------------------------------------------------------------------------
def tool(tmp_path: Path) -> Path:
    """a copy of the script and of what it reads beside itself"""
    root = tmp_path / "tool"
    (root / "schemas").mkdir(parents=True)
    (root / "templates").mkdir()
    for name in ("kypacket.py", "kyschema.py", "schemas/packet.json", "templates/ku_bindings.json"):
        shutil.copyfile(FLEET / name, root / name)
    return root


def own_input_refused(done):
    assert done.returncode == 66, done.stdout + done.stderr
    assert done.stdout == "" and done.stderr.startswith("kypacket: ")


def rewrite_bindings(root: Path, change):
    path = root / "templates" / "ku_bindings.json"
    bindings = json.loads(path.read_text(encoding="utf-8"))
    change(bindings)
    path.write_text(json.dumps(bindings, ensure_ascii=False, indent=1), encoding="utf-8")


def test_the_copied_tool_admits_as_the_original_does(world, tmp_path):
    admitted(run(write(tmp_path, world.bootstrap()), world.repo, script=tool(tmp_path) / "kypacket.py"))


def test_a_required_in_label_outside_the_registry_is_exit_66(world, tmp_path):
    root = tool(tmp_path)
    rewrite_bindings(root, lambda b: b["clauses"]["KU-03"]["required_in"].append("kyunknown"))
    done = run(write(tmp_path, world.bootstrap()), world.repo, script=root / "kypacket.py")
    own_input_refused(done)
    assert "kyunknown" in done.stderr and "KU-03" in done.stderr


def test_a_clause_whose_text_is_not_its_text_sha256_is_exit_66(world, tmp_path):
    root = tool(tmp_path)

    def alter(bindings):
        bindings["clauses"]["KU-01"]["text"] = bindings["clauses"]["KU-01"]["text"].replace("Audit", "audit", 1)

    rewrite_bindings(root, alter)
    done = run(write(tmp_path, world.bootstrap()), world.repo, script=root / "kypacket.py")
    own_input_refused(done)
    assert "KU-01" in done.stderr


@pytest.mark.parametrize("change", [
    lambda b: b.pop("clauses"),
    lambda b: b.update(clauses={}),
    lambda b: b.update(clauses=[]),
    lambda b: b.update(schema="ky.ku_bindings/2"),
    lambda b: b["clauses"]["KU-02"].pop("required_in"),
    lambda b: b["clauses"]["KU-02"].update(required_in=[]),
    lambda b: b["clauses"]["KU-02"].update(required_in="local-db"),
    lambda b: b["clauses"]["KU-02"].pop("text_sha256"),
    lambda b: b["clauses"]["KU-02"].update(text="", text_sha256=sha("")),
    lambda b: b["clauses"].update({"KU-04": "text"}),
])
def test_malformed_bindings_are_exit_66(world, tmp_path, change):
    root = tool(tmp_path)
    rewrite_bindings(root, change)
    own_input_refused(run(write(tmp_path, world.bootstrap()), world.repo, script=root / "kypacket.py"))


@pytest.mark.parametrize("name", ["kyschema.py", "schemas/packet.json", "templates/ku_bindings.json"])
def test_a_missing_or_unparseable_own_file_is_exit_66(world, tmp_path, name):
    root = tool(tmp_path)
    packet = write(tmp_path, world.bootstrap())
    (root / name).write_text("{", encoding="utf-8")
    done = run(packet, world.repo, script=root / "kypacket.py")
    own_input_refused(done)
    assert Path(name).name in done.stderr
    (root / name).unlink()
    done = run(packet, world.repo, script=root / "kypacket.py")
    own_input_refused(done)
    assert Path(name).name in done.stderr


def test_a_schema_the_validator_refuses_is_exit_66(world, tmp_path):
    root = tool(tmp_path)
    (root / "schemas" / "packet.json").write_text('{"type": "object", "format": "x"}', encoding="utf-8")
    own_input_refused(run(write(tmp_path, world.bootstrap()), world.repo, script=root / "kypacket.py"))


def test_a_repository_that_is_not_one_is_exit_66(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    plain = tmp_path / "plain"
    plain.mkdir()
    for repo in (plain, tmp_path / "absent", world.repo / "docs", "repo", packet):
        own_input_refused(run(packet, repo))


def test_a_git_that_cannot_run_is_exit_66(world, tmp_path):
    packet = write(tmp_path, world.bootstrap())
    own_input_refused(run(packet, world.repo, KY_GIT=str(tmp_path / "no-git")))
    own_input_refused(run(packet, world.repo, KY_GIT="/usr/bin/false"))


# --------------------------------------------------------------------------------------------------------------
# exit 64: usage
# --------------------------------------------------------------------------------------------------------------
def test_a_malformed_command_line_is_exit_64(world, tmp_path):
    packet = str(write(tmp_path, world.bootstrap()))
    repo = str(world.repo)
    for argv in ([], ["check"], ["check", packet], ["check", packet, "--repo"], ["check", packet, repo],
                 ["admit", packet, "--repo", repo], ["check", packet, packet, "--repo", repo],
                 ["check", packet, "--repo", repo, "--force"], ["check", "--repo", repo],
                 ["check", packet, "--repo", repo, "--repo", repo]):
        done = subprocess.run([sys.executable, "-B", str(SCRIPT), *argv], env=GIT_ENV, capture_output=True, text=True)
        assert done.returncode == 64, argv
        assert done.stdout == "" and done.stderr.startswith("usage: "), argv


def test_the_script_imports_the_standard_library_only():
    source = SCRIPT.read_text(encoding="utf-8")
    imported = {line.split()[1].split(".")[0] for line in source.splitlines()
                if line.startswith(("import ", "from "))}
    assert imported <= {"__future__", "hashlib", "importlib", "json", "os", "re", "shlex", "subprocess", "sys",
                        "pathlib"}


# --------------------------------------------------------------------------------------------------------------
# every reason code, alone
# --------------------------------------------------------------------------------------------------------------
def _raw(tmp_path, data: bytes) -> Path:
    packet = tmp_path / "PACKET_KV3-B-DEMO_v1.md"
    packet.write_bytes(data)
    return packet


ALONE = {
    "not_single_file": lambda w, t: write(t, w.bootstrap(), name="packet.md"),
    "front_matter_json": lambda w, t: _raw(t, ("```json\n[]\n```\n" + EXCERPT).encode()),
    "schema": lambda w, t: write(t, w.bootstrap(max_loops=9)),
    "name_id_mismatch": lambda w, t: write(t, w.bootstrap(), name="PACKET_KV3-B-OTHER_v1.md"),
    "packet_sha256": lambda w, t: _raw(t, render(w.bootstrap(), "# demo\n\n" + EXCERPT) + b"\n"),
    "spec_source_missing": lambda w, t: write(t, w.bootstrap(spec_sources=two_sources(w, path="docs/ABSENT.md"))),
    "spec_source_sha256": lambda w, t: write(t, w.bootstrap(spec_sources=two_sources(w, sha256=sha(NOTES_OLD)))),
    "spec_source_revision": lambda w, t: write(t, w.bootstrap(spec_sources=two_sources(w, revision=w.c1))),
    "commit_unknown": lambda w, t: write(t, w.feature(original_failing_base=ABSENT_COMMIT)),
    "schema_receipt_unresolved": lambda w, t: write(t, w.artifact(schema_receipt_id="SR-TEST-2")),
    "oversize": lambda w, t: sized(w, t, 9001),
    "test_unavailable": lambda w, t: write(t, w.feature(test_commits=[
        {"sha": w.c1, "digest": sha("other"), "path": "tests/test_feature.py"}])),
    "excerpt_not_in_source": lambda w, t: write(t, w.bootstrap(), "# demo\n\n```excerpt plan\nGamma.\n```\n"),
    "no_excerpt": lambda w, t: write(t, w.bootstrap(), "# demo\n"),
    "reconciliation_unpinned": lambda w, t: write(t, w.bootstrap(), "# demo\n\n" + EXCERPT + "Reconciliation: none.\n"),
    "ku_clause_missing": lambda w, t: write(t, owning(w, f"{F}/kyverdicts.py"),
                                            ku_body(KU["KU-01"]["text"].replace("Audit", "audit", 1))),
}


def test_the_reason_codes_are_the_packet_s_sixteen():
    assert set(ALONE) == set(kypacket.REASON_CODES) and len(kypacket.REASON_CODES) == 16


@pytest.mark.parametrize("code", sorted(ALONE))
def test_each_reason_code_has_a_packet_refused_with_exactly_it(world, tmp_path, code):
    done = run(ALONE[code](world, tmp_path), world.repo)
    report = refused(done, code)
    assert len(report["reasons"]) == 1
    assert done.stderr.startswith(f"refused: {code}: ")
