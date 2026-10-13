"""Final receipt producer: exercise real manifest observation, packet admission, gate and version checks.

The bootstrap fixture uses test_kymanifest's existing git/review/probe rig; launch
qualification is its offline harness stand-in. No real model, tracker or service starts.
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_kymanifest import rig as manifest_rig, git, km, sha
from test_kypacket import World as PacketWorld, render, EXCERPT
from test_kygate import digest_without

FLEET = Path(__file__).resolve().parent.parent
SCRIPT = FLEET / "kyfinal.py"

# Required measurements from plan §14 B-3 and surrogate answers 09 / 12.
OBLIGATIONS = (
    "component_tests_final_bundle", "fixture_live_events_unchanged",
    "fixture_no_live_tracker_access", "fixture_no_external_requests",
    "fixture_expected_transitions", "fixture_clean_stop",
    "live_build_by_fleet", "live_pr_opened", "live_verify_boundary",
    "live_accepted_pr_head_in_log", "live_merge_parked_no_auto_merge",
)
SUBSTITUTION = {"replaces": "fixture_model_jobs", "replacement": "live_first_item_under_watch",
                "ruling": "SURROGATE_ANSWER_09_B3_LEG3.md#6", "label": "live, not fixture"}


def write(path, doc):
    path.write_text(json.dumps(doc, sort_keys=True, indent=1) + "\n")


def read(path):
    return json.loads(path.read_text())


def tree_digest(root):
    rows = {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}
    return hashlib.sha256("".join(f"{digest}  {name}\n" for name, digest in sorted(rows.items())).encode()).hexdigest()


@pytest.fixture
def final_rig(manifest_rig, tmp_path):
    r = manifest_rig
    # Bind the real consumers and packet checker/dependencies into the reviewed fixture.
    for name in ("kygate.sh", "kyversion.sh", "kypacket.py", "kyschema.py", "schemas/packet.json", "schemas/release_receipt.json", "templates/ku_bindings.json", "kybackfill.py", "schemas/rehearsal_results.json"):
        rel = km.FLEET + "/" + name
        dest = r.repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FLEET / name, dest)
        if rel not in r.comps:
            r.comps.append(rel)
    tracker = "platform/scripts/governance/pravaha_tracker/server.py"
    wrapper = km.FLEET + "/bin/ky"
    for rel in (tracker, wrapper):
        dest = r.repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("# offline fixture\n")
        r.comps.append(rel)
    (r.repo / km.COMPONENT_LIST).write_text("\n".join(r.comps) + "\n")
    r.commit("real consumers and installed trees")
    r.write_review()
    built = r.build()
    assert built.returncode == 0, built.stderr
    m = read(r.run / "VERSIONS.bootstrap.json")
    root = tmp_path / "installed"
    live, track, bins = root / "fleet_live", root / "tracker_live", root / "bin"
    for directory in (live, track, bins):
        directory.mkdir(parents=True)
    components = []
    for row in m["components"]:
        rel = row["path"]
        if rel == tracker:
            dest = track / "pravaha_tracker/server.py"
        elif rel == wrapper:
            dest = bins / "ky"
        else:
            dest = live / rel.removeprefix(km.FLEET + "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(r.repo / rel, dest)
        components.append(dict(row, installed_path=str(dest)))
    bundle = []
    for role, row in m["entrypoints"].items():
        dest = live / "bundle" / row["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(r.repo / row["path"], dest)
        bundle.append({"role": role, "path": row["path"], "sha256": row["sha256"], "installed_path": str(dest)})
    qualifications = []
    for role in ("planner", "conductor"):
        receipt = r.run / (role + ".json")
        write(receipt, {"role": role, "model": "claude-opus-5-5", "result": "PASS"})
        qualifications.append({"role": role, "model": "claude-opus-5-5", "result": "PASS", "receipt": str(receipt), "receipt_sha256": sha(receipt)})
    bootstrap = {
        "schema": "ky.install_receipt/1", "mode": "bootstrap",
        "manifest": {"path": str(r.run / "VERSIONS.bootstrap.json"), "sha256": sha(r.run / "VERSIONS.bootstrap.json"), "manifest_sha256": m["manifest_sha256"]},
        "source": {"path": str(r.repo), "approved_source_commit": r.approved, "components_commit": m["components_commit"], "merge_commit": None},
        "components": components,
        "trees": {"fleet_live": {"path": str(live), "files": len(list(live.rglob("*"))) , "tree_sha256": tree_digest(live)},
                  "tracker_live": {"path": str(track), "files": 1, "tree_sha256": tree_digest(track)},
                  "bin": {"path": str(bins), "files": [{"name": "ky", "path": str(bins / "ky"), "sha256": sha(bins / "ky"), "mode": "0644"}]},
                  "bundle": bundle, "versions_bootstrap": {"path": str(r.run / "VERSIONS.bootstrap.json"), "sha256": sha(r.run / "VERSIONS.bootstrap.json")}},
        "qualifications": qualifications,
        "tracker_revision": {"package_sha256": tree_digest(track), "pid": 123, "process_start": "measured fixture", "health": {"ok": True, "server_started_at": "2026-10-13T00:00:00Z"}},
        "reviews": {"record": m["review"]}, "claude_bin": {"version": "fixture"}, "plists": [],
        "old_supervisors": {"matching": []}, "campaign_checkout": {"head": m["components_commit"]}, "model_actions": {}, "legacy": {"measured": True}}
    # installer counts regular files, including the installed entrypoint bundle.
    bootstrap["trees"]["fleet_live"]["files"] = sum(p.is_file() for p in live.rglob("*"))
    out_receipt = r.run / "INSTALL_RECEIPT.json"
    write(out_receipt, bootstrap)
    rehearsal, coverage = r.run / "REHEARSAL_RESULTS.json", r.run / "coverage.review.json"
    measurement = r.run / "measured-rehearsal.txt"
    measurement.write_text("offline rig measurements\n")
    write(rehearsal, {"schema": "ky.rehearsal_results/2", "tested_components": m["components"],
        "obligations": [{"id": name, "outcome": "PASS", "measured_by": "offline fixture detector",
                         "evidence": [{"path": str(measurement), "sha256": sha(measurement)}]}
                        for name in OBLIGATIONS], "substitutions": [SUBSTITUTION]})
    write(coverage, {"review": {"verdict": "ACCEPTED"}, "reviewer_session_id": "cards-reviewer"})
    # Reuse the packet rig's contract, but pin it to THIS fixture repository.
    packet_base = tmp_path / "packet-base"
    packet_base.mkdir()
    pw = PacketWorld(packet_base)
    shutil.copytree(pw.repo / "docs", r.repo / "docs")
    r.commit("packet source")
    front = pw.bootstrap()
    front["spec_sources"][0]["revision"] = git(r.repo, "rev-parse", "HEAD")
    packets = r.run / "packets"
    packets.mkdir()
    packet = packets / "PACKET_KV3-B-DEMO_v1.md"
    packet.write_bytes(render(front, "# demo\n\n" + EXCERPT))
    release = read(FLEET / "tests/fixtures/b0c/release_receipt_satisfied.json")
    release["conditions"]["certification"]["evidence"]["coordination_commit"] = r.approved
    release["conditions"]["regeneration"]["evidence"]["main_commit"] = r.approved
    release["digest"] = digest_without(release, "digest")
    write(r.run / "RELEASE_RECEIPT.json", release)
    git(r.repo, "update-ref", "refs/remotes/origin/main", r.approved)
    # Named backfill artefacts and the real governance detector, never a no-op oracle.
    gov = "platform/scripts/governance/"
    for name in ("schema_validator.py", "_ca_loader.py"):
        dest = r.repo / (gov + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FLEET.parents[3] / (gov + name), dest)
    banner = r.repo / "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
    session_log = r.repo / "00_ARCHITECTURE/SESSION_LOG.md"
    banner_id, entry_id = "KĀLA-YANTRA v3 — fixture backfill.", "KY_FIXTURE_BACKFILL"
    banner.write_text("## §2 — Canonical state block\n\n> **" + banner_id + "**\n"
                      "> Campaign handoff: SESSION_LOG.md#" + entry_id + "\n\n")
    opened = {"session_open": dict.fromkeys((
        "cowork_thread_name", "agent_name", "agent_version", "worktree_path",
        "step_number_or_layer", "predecessor_session", "mandatory_reading_confirmation",
        "mirror_pair_freshness_check", "native_directive_obligations", "red_team_due"), "fixture")}
    opened["session_open"].update(session_id=entry_id, tool="Codex", tool_profile="madhav-parity",
        coordination={"lease_id": "fixture", "lease_status_verified": True},
        cross_tool_state_read={"cross_cutting_decision_register": True},
        canonical_artifact_fingerprint_check=[], declared_scope={"may_touch": ["00_ARCHITECTURE/**"], "must_not_touch": ["platform/**"]})
    closed = {"session_close": dict.fromkeys(("closed_at", "registry_updates_made", "red_team_pass",
        "unblocks", "handoff_notes"), "fixture")}
    closed["session_close"].update(session_id=entry_id, tool="Codex", current_state_updated=True,
        session_log_appended=True, close_criteria_met=True,
        drift_detector_run={"exit_code": 0}, schema_validator_run={"exit_code": 0, "violations_found": 0},
        files_touched=[{"path": "00_ARCHITECTURE/CURRENT_STATE_v1_0.md", "sha256_after": sha(banner)},
                       {"path": "00_ARCHITECTURE/SESSION_LOG.md", "sha256_after": None}],
        cross_tool_sync={"work_order_outcome_recorded": True, "lease_release_recorded": True,
                         "lease_release_verified_on_remote": True, "ccd_entries_appended": []})
    # JSON mappings are valid YAML; validators parse the actual embedded blocks.
    open_text, close_text = json.dumps(opened), json.dumps(closed)
    handshake = r.repo / "00_ARCHITECTURE/briefs/kalayantra/sessions/SESSION_OPEN_kalayantra.yaml"
    handshake.parent.mkdir(parents=True, exist_ok=True)
    handshake.write_text(open_text)
    session_log.write_text("# Schema adoption point\n## " + entry_id + " — fixture\n"
        "```yaml\n" + open_text + "\n```\nBody\n```yaml\n" + close_text + "\n```\n"
        "### Next session objective\nComplete final acceptance.\n")
    validator = r.repo / (gov + "schema_validator.py")
    env = dict(os.environ, KY_ROOT=str(root), KY_RUN=str(r.run), KY_FLEET=str(live), KY_SOURCE_REPO=str(r.repo), GIT_OPTIONAL_LOCKS="0")

    def build(*extra, packet_input=packets):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "build", "--repo", str(r.repo), "--run", str(r.run),
            "--rehearsal", str(rehearsal), "--coverage", str(coverage), "--packets", str(packet_input),
            "--backfill-banner-file", "00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
            "--backfill-session-log", "00_ARCHITECTURE/SESSION_LOG.md",
            "--backfill-entry-id", entry_id, "--backfill-banner-id", banner_id, "--out-manifest", str(r.run / "VERSIONS.json"),
            "--out-receipt", str(out_receipt), *extra], capture_output=True, text=True, env=env)

    def consumer(name, *args):
        return subprocess.run(["/bin/bash", str(live / name), *args], capture_output=True, text=True, env=env)

    def snapshot():
        return {str(p): p.read_bytes() for base in (r.run, root) for p in base.rglob("*") if p.is_file()}

    return SimpleNamespace(r=r, m=m, root=root, live=live, track=track, bins=bins, bootstrap=bootstrap,
        rehearsal=rehearsal, coverage=coverage, packet=packet, packets=packets, validator=validator, banner=banner, session_log=session_log,
        banner_id=banner_id, entry_id=entry_id, handshake=handshake,
        out_receipt=out_receipt, build=build, consumer=consumer, snapshot=snapshot)


def test_generated_final_bundle_passes_real_gate_and_all_final_version_checks(final_rig):
    f = final_rig
    old = f.out_receipt.read_bytes()
    done = f.build()
    assert done.returncode == 0, done.stderr
    manifest, receipt = read(f.r.run / "VERSIONS.json"), read(f.out_receipt)
    assert manifest["mode"] == receipt["mode"] == "final"
    assert manifest["manifest_sha256"] == digest_without(manifest, "manifest_sha256")
    assert receipt["rehearsal"]["tested_components"] == f.m["components"]
    assert receipt["coverage"]["verdict"] == "ACCEPTED"
    assert receipt["packets"] == [{"path": str(f.packet), "sha256": sha(f.packet)}]
    assert receipt["tracker_revision"] == f.bootstrap["tracker_revision"]["package_sha256"]
    assert receipt["bootstrap_tracker_revision"] == f.bootstrap["tracker_revision"]
    for key in ("source", "components", "trees", "reviews", "qualifications", "claude_bin", "plists", "old_supervisors", "campaign_checkout", "model_actions", "legacy"):
        assert receipt[key] == f.bootstrap[key]
    assert Path(str(f.out_receipt) + ".bootstrap").read_bytes() == old
    backfill = receipt["backfill"]
    assert backfill["validated"] is True and sha(Path(backfill["path"])) == backfill["sha256"]
    evidence = read(Path(backfill["path"]))
    assert evidence["exit_code"] == 0
    assert evidence["validator"] == {"path": str(f.validator), "sha256": sha(f.validator)}
    assert evidence["artifacts"]["banner"] == {"path": str(f.banner), "sha256": sha(f.banner), "identifier": f.banner_id}
    assert evidence["artifacts"]["session_log"] == {"path": str(f.session_log), "sha256": sha(f.session_log), "entry_id": f.entry_id}
    assert evidence["checks"] == {name: {"violations": 0, "exit_code": 0}
                                  for name in ("handshake", "close_checklist", "scope_boundary", "session_entry")}
    version = f.consumer("kyversion.sh")
    assert version.returncode == 0, version.stderr
    gate = f.consumer("kygate.sh", "--pre-resume")
    assert gate.returncode == 0 and gate.stdout.startswith("READY_TO_START\n"), gate.stdout + gate.stderr
    # The full gate still needs an owner resume AND the activation chain.
    full = f.consumer("kygate.sh")
    assert full.returncode == 75 and "reason=resume_missing" in full.stdout
    digest = manifest["manifest_sha256"]
    expected = f.consumer("kyversion.sh", "--expected-manifest-digest", digest)
    assert expected.returncode == 1 and "REFUSED D2" in expected.stderr


def test_dry_run_checks_everything_and_prints_proposed_records_without_writing(final_rig):
    f = final_rig
    before = f.snapshot()
    done = f.build("--dry")
    assert done.returncode == 0, done.stderr
    proposal = json.loads(done.stdout)
    assert proposal["manifest"]["mode"] == proposal["receipt"]["mode"] == "final"
    assert proposal["receipt"]["backfill"]["validated"] is True
    assert f.snapshot() == before


@pytest.mark.parametrize("change,reason", [
    ("installed", "installed_bytes"), ("source", "source_observation"),
    ("bundle", "installed_bundle"), ("extra", "installed_tree"),
    ("coverage", "coverage_not_accepted"), ("tested", "tested_components_mismatch"),
    ("validator", "backfill_validator_failed"), ("packet", "packet_not_admitted"),
    ("qualification", "loop_qualification"), ("tracker", "tracker_revision_missing"),
    ("manifest", "bootstrap_manifest_digest"), ("review", "source_observation"),
    ("empty", "packets_missing"), ("receipt", "bootstrap_receipt_mode"),
])
def test_refusals_are_named_and_write_nothing(final_rig, change, reason):
    f = final_rig
    if change == "installed":
        Path(f.bootstrap["components"][0]["installed_path"]).write_text("tampered")
    elif change == "source":
        (f.r.repo / f.r.comps[1]).write_text("tampered")
    elif change == "bundle":
        Path(f.bootstrap["trees"]["bundle"][0]["installed_path"]).write_text("tampered")
    elif change == "extra":
        (f.live / "unbound.py").write_text("tampered")
    elif change == "coverage":
        write(f.coverage, {"verdict": "REJECTED"})
    elif change == "tested":
        doc = read(f.rehearsal)
        doc["tested_components"][0]["sha256"] = "0" * 64
        write(f.rehearsal, doc)
    elif change == "validator":
        f.validator.write_text("import sys\nsys.exit(9)\n")
    elif change == "packet":
        f.packet.write_bytes(f.packet.read_bytes() + b"tamper")
    elif change == "qualification":
        write(f.r.run / "planner.json", {"result": "FAIL"})
    elif change in ("tracker", "receipt"):
        doc = read(f.out_receipt)
        if change == "tracker":
            del doc["tracker_revision"]
        else:
            doc["mode"] = "final"
        write(f.out_receipt, doc)
    elif change == "manifest":
        doc = read(f.r.run / "VERSIONS.bootstrap.json")
        doc["qualifications_all_pass"] = False
        write(f.r.run / "VERSIONS.bootstrap.json", doc)
    elif change == "review":
        f.r.write_review(verdict="REJECTED")
    elif change == "empty":
        f.packet.unlink()
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and reason in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


def test_packet_list_resolves_relative_paths_and_hash_binds_them(final_rig):
    f = final_rig
    listing = f.r.run / "admitted.txt"
    listing.write_text("# admitted packets\npackets/" + f.packet.name + "\n")
    done = f.build(packet_input=listing)
    assert done.returncode == 0, done.stderr
    assert read(f.out_receipt)["packets"] == [{"path": str(f.packet), "sha256": sha(f.packet)}]


def test_inputs_changed_by_validator_are_refused_before_any_output(final_rig):
    f = final_rig
    f.validator.write_text(f"from pathlib import Path\nPath({str(f.coverage)!r}).write_text('changed')\n" + f.validator.read_text().replace("from __future__ import annotations\n", ""))
    done = f.build()
    assert done.returncode == 1 and "inputs_changed" in done.stderr, done.stderr
    assert not (f.r.run / "VERSIONS.json").exists()
    assert not Path(str(f.out_receipt) + ".bootstrap").exists()
    assert read(f.out_receipt)["mode"] == "bootstrap"


def test_second_build_refuses_without_overwriting_bootstrap_backup(final_rig):
    f = final_rig
    assert f.build().returncode == 0
    before = f.snapshot()
    again = f.build()
    assert again.returncode == 1 and "bootstrap_receipt_mode" in again.stderr
    assert before == f.snapshot()


@pytest.mark.parametrize("change,reason", [
    ("mode", "installed_bytes"), ("symlink", "installed_bytes"),
    ("tested_empty", "tested_components_mismatch"), ("tested_duplicate", "tested_components_mismatch"),
    ("coverage_missing", "coverage_unreadable"), ("coverage_conflict", "coverage_not_accepted"),
    ("activation", "activation_chain"), ("deferred", "deferred_components"),
    ("backup", "output_exists"), ("manifest_output", "output_exists"),
    ("duplicate_packets", "packets_duplicate"), ("tracker_digest", "tracker_revision_mismatch"),
])
def test_no_passing_defaults_or_deferred_installation(final_rig, change, reason):
    f = final_rig
    packet_input = f.packets
    if change in ("mode", "symlink"):
        path = Path(f.bootstrap["components"][0]["installed_path"])
        if change == "mode":
            path.chmod(0o600)
        else:
            target = f.r.run / "linked.py"
            target.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(target)
    elif change.startswith("tested_"):
        doc = read(f.rehearsal)
        if change == "tested_empty":
            doc["tested_components"] = []
        else:
            doc["tested_components"].append(copy.deepcopy(doc["tested_components"][0]))
        write(f.rehearsal, doc)
    elif change == "coverage_missing":
        f.coverage.unlink()
    elif change == "coverage_conflict":
        write(f.coverage, {"verdict": "ACCEPTED", "review": {"verdict": "REJECTED"}})
    elif change == "activation":
        write(f.r.run / "ACTIVATION_RECORD.json", {"final_manifest_digest": "bad"})
    elif change == "deferred":
        doc = read(f.r.run / "VERSIONS.bootstrap.json")
        doc["deferred_components"] = [{"path": "unreviewed.py", "sha256": "a" * 64}]
        write(f.r.run / "VERSIONS.bootstrap.json", km.with_digest(doc))
    elif change == "backup":
        Path(str(f.out_receipt) + ".bootstrap").write_text("previous install")
    elif change == "manifest_output":
        (f.r.run / "VERSIONS.json").write_text("existing manifest")
    elif change == "duplicate_packets":
        packet_input = f.r.run / "admitted.txt"
        packet_input.write_text(str(f.packet) + "\n" + str(f.packet) + "\n")
    elif change == "tracker_digest":
        doc = read(f.out_receipt)
        doc["tracker_revision"]["package_sha256"] = "0" * 64
        write(f.out_receipt, doc)
    before = f.snapshot()
    done = f.build(packet_input=packet_input)
    assert done.returncode == 1 and reason in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


def test_publication_failure_rolls_back_new_files_and_keeps_original_receipt(final_rig):
    f = final_rig
    Path(str(f.out_receipt) + ".kyfinal.tmp").mkdir()
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and "publication_failed" in done.stderr, done.stderr
    assert f.snapshot() == before


@pytest.mark.parametrize("target", ["rehearsal", "coverage", "packet", "component", "entrypoint", "qualification", "backfill"])
def test_real_consumers_detect_tampering_after_finalisation(final_rig, target):
    f = final_rig
    done = f.build()
    assert done.returncode == 0, done.stderr
    receipt = read(f.out_receipt)
    path = {
        "rehearsal": f.rehearsal, "coverage": f.coverage, "packet": f.packet,
        "component": Path(receipt["components"][0]["installed_path"]),
        "entrypoint": f.r.repo / km.PAIRS[0][1],
        "qualification": Path(receipt["qualifications"][0]["receipt"]),
        "backfill": Path(receipt["backfill"]["path"]),
    }[target]
    path.write_bytes(path.read_bytes() + b"tamper")
    version = f.consumer("kyversion.sh")
    assert version.returncode == 1, version.stdout + version.stderr
    gate = f.consumer("kygate.sh", "--pre-resume")
    assert gate.returncode == 75 and "reason=final_acceptance_unverified" in gate.stdout, gate.stdout + gate.stderr


def test_validator_cannot_leave_a_packet_with_changed_spec_sources_admitted(final_rig):
    f = final_rig
    source = f.r.repo / 'docs/PLAN.md'
    f.validator.write_text(f"from pathlib import Path\nPath({str(source)!r}).write_text('changed spec')\n" + f.validator.read_text().replace("from __future__ import annotations\n", ""))
    done = f.build()
    assert done.returncode == 1 and 'packet_not_admitted' in done.stderr, done.stdout + done.stderr
    assert not (f.r.run / 'VERSIONS.json').exists()
    assert read(f.out_receipt)['mode'] == 'bootstrap'


def test_ambiguous_json_coverage_cannot_earn_acceptance(final_rig):
    f = final_rig
    f.coverage.write_text('{"verdict":"REJECTED","verdict":"ACCEPTED"}')
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and 'coverage_unreadable' in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


@pytest.mark.parametrize("outcome", ["NOT_RUN", "FAIL", "UNKNOWN", None, "missing"])
def test_matching_components_cannot_mask_unearned_rehearsal(final_rig, outcome):
    f = final_rig
    doc = read(f.rehearsal)
    name = "live_accepted_pr_head_in_log"
    row = next(row for row in doc["obligations"] if row["id"] == name)
    if outcome == "missing":
        doc["obligations"].remove(row)
    elif outcome is None:
        del row["outcome"]
    else:
        row["outcome"] = outcome
    write(f.rehearsal, doc)
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and name in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


@pytest.mark.parametrize("change", ["hash", "missing", "empty", "measured_by", "duplicate", "schema", "substitution"])
def test_rehearsal_evidence_and_substitution_are_required(final_rig, change):
    f = final_rig
    doc = read(f.rehearsal)
    row = doc["obligations"][0]
    if change == "hash":
        row["evidence"][0]["sha256"] = "0" * 64
    elif change == "missing":
        Path(row["evidence"][0]["path"]).unlink()
    elif change == "empty":
        row["evidence"] = []
    elif change == "measured_by":
        row["measured_by"] = ""
    elif change == "duplicate":
        doc["obligations"].append(copy.deepcopy(row))
    elif change == "schema":
        doc["schema"] = "ky.rehearsal_results/1"
    else:
        doc["substitutions"] = []
    write(f.rehearsal, doc)
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and "rehearsal_" in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


def test_true_cannot_validate_backfill(final_rig):
    f = final_rig
    before = f.snapshot()
    done = f.build("--backfill-validator", "/usr/bin/true")
    assert done.returncode != 0, done.stdout + done.stderr
    assert f.snapshot() == before


@pytest.mark.parametrize("change", ["banner", "handshake", "close", "entry"])
def test_governance_rejected_backfill_cannot_earn_validated(final_rig, change):
    f = final_rig
    if change == "banner":
        f.banner.write_text(f.banner.read_text().replace(f.banner_id, "Wrong banner"))
    elif change == "handshake":
        f.session_log.write_text(f.session_log.read_text().replace('"tool_profile": "madhav-parity"', '"tool_profile": "unapproved"'))
        f.handshake.write_text(f.handshake.read_text().replace('"tool_profile": "madhav-parity"', '"tool_profile": "unapproved"'))
    elif change == "close":
        f.session_log.write_text(f.session_log.read_text().replace('"close_criteria_met": true', '"close_criteria_met": false'))
    else:
        f.session_log.write_text(f.session_log.read_text().replace('### Next session objective', '### Choices'))
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and "backfill_" in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


@pytest.mark.parametrize("name", OBLIGATIONS)
def test_each_required_measurement_must_be_present(final_rig, name):
    f = final_rig
    doc = read(f.rehearsal)
    doc["obligations"] = [row for row in doc["obligations"] if row["id"] != name]
    write(f.rehearsal, doc)
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and name in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before


def test_no_op_repository_validator_has_no_governance_detectors(final_rig):
    f = final_rig
    f.validator.write_text("# no-op, no governance detectors\n")
    before = f.snapshot()
    done = f.build()
    assert done.returncode == 1 and "governance detector missing" in done.stderr, done.stdout + done.stderr
    assert f.snapshot() == before
