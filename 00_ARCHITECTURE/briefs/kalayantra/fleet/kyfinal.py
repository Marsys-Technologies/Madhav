#!/usr/bin/env python3
"""Produce the final manifest and installation receipt from a measured bootstrap install.

Usage: kyfinal.py build --repo REPO --run RUN --rehearsal RESULTS.json
  --coverage REVIEW.json --packets LIST_OR_DIR --backfill-validator 'COMMAND ARGS'
  --out-manifest RUN/VERSIONS.json --out-receipt RUN/INSTALL_RECEIPT.json [--dry]

No service, network, git mutation or model launch. All admission checks precede
publication; a named refusal publishes nothing. --dry runs the same detectors,
including the supplied validator, and prints the proposed records without writing.
The validator is executed as argv (shlex), not a shell. This tool cannot undo a
supplied command's side effects; use a read-only validator when globally write-free
refusal/dry-run behaviour is required. It never publishes on a failed validator.

(I) INTERPRETATION: finalisation refuses deferred components; first bind/review and
reinstall the complete bundle. Source authority comes from VERSIONS.bootstrap.json,
not today's HEAD. Its observations must still match kymanifest.observe exactly.
(I) INTERPRETATION: list entries are paths relative to the list file (one per line,
blank lines and # comment lines ignored); a directory selects PACKET_*.md directly.
(I) INTERPRETATION: backfill exit evidence is INSTALL_RECEIPT.json.backfill.json;
kyversion F7 requires its path/hash, although gate A6 reads only validated.
(I) INTERPRETATION: final tracker_revision is the installer's measured package_sha256;
the entire previous measured object is retained as bootstrap_tracker_revision. It
asserts the installed package revision, not freshly observed process liveness.

Consumer map (paths relative to this directory):
  mode: kygate.sh:443; kyversion.sh:190-195 (F1)
  manifest.manifest_sha256: kygate.sh:447-454; kyversion.sh:250-259 (F3)
  final entrypoints/digest: kyversion.sh:225-246 (F2); kymanifest.py:368-371
  components/installed_path: kyversion.sh:263-281 (F4)
  generated_pairs: kyversion.sh:285-319 (F5)
  rehearsal.results {path,sha256}: kygate.sh:455-459; kyversion.sh:424-436 (F7)
  rehearsal.tested_components: kygate.sh:460-469; kyversion.sh:413-422 (F7)
  coverage {path,sha256,verdict}, packets[] {path,sha256}: kygate.sh:470-483;
    kyversion.sh:423-438 (F7)
  backfill {path,sha256,validated}: kygate.sh:484-487; kyversion.sh:425-440 (F7)
  tracker_revision: kyversion.sh:441-443 (F7)
  qualifications: kyversion.sh:323-345 (F8); activation chain:349-407 (F6)
  bootstrap measured sections: install.sh:1780-1819 (kept, except explicit mode,
    manifest binding and scalar tracker_revision conversion described above).

This does not create RELEASE_RECEIPT, OWNER_RESUME, an activation record, or remove
HOLD. Pre-resume A7 uses normal final checks. Full A7 needs the OWNER_RESUME digest
and a valid terminal activation link (kyversion D1/D2); gate N binds the release
receipt, bundle, decider and UTC timestamp (kygate.sh:525-580).
"""
import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
from pathlib import Path

# Also work when called with python -I (the installed cockpit's form).
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kymanifest as km

HEX = re.compile(r"[0-9a-f]{64}\Z")


class Refused(Exception):
    pass


def refuse(code, detail):
    raise Refused(f"{code}: {detail}")


def strict_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON member: " + key)
        out[key] = value
    return out


def invalid_constant(value):
    raise ValueError("non-JSON constant: " + value)


def encoded(doc):
    return (json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


class Inputs:
    """Hash every named input; recheck before publishing to detect validator/concurrent edits."""
    def __init__(self):
        self.hashes = {}

    def file(self, path, code, expected=None):
        path = Path(path)
        if not path.is_absolute():
            refuse(code, f"path is not absolute: {path}")
        try:
            if not stat.S_ISREG(path.lstat().st_mode):
                refuse(code, f"not a regular file: {path}")
            digest = km.sha256(path)
        except OSError as e:
            refuse(code, f"unreadable file: {path} ({type(e).__name__})")
        if expected is not None and digest != expected:
            refuse(code, f"hash differs: {path}")
        if str(path) in self.hashes and self.hashes[str(path)] != digest:
            refuse("inputs_changed", str(path))
        self.hashes[str(path)] = digest
        return {"path": str(path), "sha256": digest}

    def document(self, path, code):
        self.file(path, code)
        try:
            with Path(path).open(encoding="utf-8") as stream:
                doc = json.load(stream, object_pairs_hook=strict_object, parse_constant=invalid_constant)
            if not isinstance(doc, dict):
                raise ValueError("not a JSON object")
            return doc
        except (OSError, ValueError, RecursionError) as e:
            refuse(code, f"invalid JSON object: {path} ({type(e).__name__})")

    def unchanged(self):
        for path, digest in list(self.hashes.items()):
            self.file(path, "inputs_changed", digest)


def component_map(rows, code):
    if not isinstance(rows, list) or not rows:
        refuse(code, "no component entries")
    out = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) or not row["path"] \
                or not isinstance(row.get("sha256"), str) or not HEX.fullmatch(row["sha256"]) \
                or row["path"] in out:
            refuse(code, "not distinct {path,sha256} entries")
        out[row["path"]] = row["sha256"]
    return out


def tree_files(root):
    root = Path(root)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        refuse("installed_tree", f"not an absolute regular directory: {root}")
    rows = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in dirs:
            if Path(directory, name).is_symlink():
                refuse("installed_tree", f"linked directory: {Path(directory, name)}")
        for name in files:
            path = Path(directory, name)
            if not stat.S_ISREG(path.lstat().st_mode):
                refuse("installed_tree", f"not a regular file: {path}")
            rows[str(path.relative_to(root))] = km.sha256(path)
    return rows


def tree_digest(rows):
    # install.sh:1062-1063, exactly (paths relative to the installed tree).
    return hashlib.sha256("".join(f"{sha}  {rel}\n" for rel, sha in sorted(rows.items())).encode()).hexdigest()


def installed(receipt, manifest, inputs, repo):
    want = component_map(manifest["components"], "manifest_components")
    rows = receipt.get("components")
    have = component_map(rows, "installed_bytes")
    if have != want:
        refuse("installed_bytes", "installed component set/hashes differ from the reviewed manifest")
    destinations = set()
    for row in rows:
        ref = inputs.file(row.get("installed_path", ""), "installed_bytes", row["sha256"])
        if ref["path"] in destinations:
            refuse("installed_bytes", "duplicate installed destination")
        destinations.add(ref["path"])
    trees = receipt.get("trees")
    if not isinstance(trees, dict):
        refuse("installed_tree", "bootstrap receipt has no measured trees")
    entrypoints = manifest["entrypoints"]
    bundle = trees.get("bundle")
    if not isinstance(bundle, list) or len(bundle) != len(entrypoints):
        refuse("installed_bundle", "installed bundle is not the five entrypoints")
    seen = set()
    for row in bundle:
        if not isinstance(row, dict) or row.get("role") not in entrypoints or row["role"] in seen:
            refuse("installed_bundle", "invalid/duplicate bundle role")
        seen.add(row["role"])
        entry = entrypoints[row["role"]]
        if row.get("path") != entry["path"] or row.get("sha256") != entry["sha256"]:
            refuse("installed_bundle", f"entrypoint differs: {row['role']}")
        inputs.file(row.get("installed_path", ""), "installed_bundle", row["sha256"])
    # Compare the complete destination file sets, including the installed bundle.
    for name in ("fleet_live", "tracker_live", "bin"):
        section = trees.get(name)
        if not isinstance(section, dict) or not isinstance(section.get("path"), str):
            refuse("installed_tree", f"missing measured {name} tree")
        root = Path(section["path"])
        expected = {}
        for row in rows + (bundle if name == "fleet_live" else []):
            path = Path(row["installed_path"])
            if path.is_relative_to(root):
                expected[str(path.relative_to(root))] = row["sha256"]
        actual = tree_files(root)
        if not expected or actual != expected:
            refuse("installed_tree", f"{name} has missing, changed or unbound files")
        if name != "bin":
            if section.get("files") != len(actual) or section.get("tree_sha256") != tree_digest(actual):
                refuse("installed_tree", f"{name} measured count/digest differs")
        else:
            files = section.get("files")
            if not isinstance(files, list) or len(files) != len(actual):
                refuse("installed_tree", "bin measurement differs")
            for entry in files:
                if not isinstance(entry, dict) or entry.get("name") not in actual \
                        or entry.get("path") != str(root / entry["name"]) or entry.get("sha256") != actual[entry["name"]]:
                    refuse("installed_tree", "bin file measurement differs")
                mode = "%04o" % stat.S_IMODE(Path(entry["path"]).stat().st_mode)
                if mode != entry.get("mode"):
                    refuse("installed_tree", "bin file mode differs")
    for row in rows + bundle:
        # The source blob modes are established by install.sh:661-667, not current chmod.
        commit = manifest["approved_source_commit"] if "role" in row else manifest["components_commit"]
        result = km.git(str(repo), "ls-tree", commit, "--", row["path"])
        mode = result.stdout.split()[:1]
        want_mode = {"100644": 0o644, "100755": 0o755}.get(mode[0] if mode else None)
        if result.returncode or want_mode is None or stat.S_IMODE(Path(row["installed_path"]).stat().st_mode) != want_mode:
            refuse("installed_bytes", f"installed mode differs from reviewed blob: {row['path']}")
    tracker = receipt.get("tracker_revision")
    if not isinstance(tracker, dict) or not isinstance(tracker.get("package_sha256"), str) \
            or not HEX.fullmatch(tracker["package_sha256"]):
        refuse("tracker_revision_missing", "no measured tracker package_sha256")
    if tracker["package_sha256"] != trees["tracker_live"]["tree_sha256"]:
        refuse("tracker_revision_mismatch", "measured tracker package differs from installed tracker tree")
    return tracker["package_sha256"]


def version_api(repo):
    """Use the reviewed real consumer's F2/F5/F6/F8 checks without staging or writing files.

    kyversion.sh itself executes this embedded stdlib program; only its definitions
    are loaded here. The caller has already verified it against its reviewed blob.
    """
    text = (repo / km.FLEET / "kyversion.sh").read_text(encoding="utf-8")
    program = text.split("\n: <<'KYVERSION_PY'\n", 1)[1].rsplit("\nKYVERSION_PY\n", 1)[0]
    definitions = program.rsplit("\ntry:\n    status = main(sys.argv[2:])", 1)[0]
    namespace = {"__name__": "kyfinal_version_checks"}
    exec(compile(definitions, "kyversion.sh", "exec"), namespace)
    return namespace


def check_version(api, receipt, manifest, repo, run, inputs):
    for code, findings in (
        ("final_manifest", api["check_final_manifest"](manifest, "")),
        ("installed_pairs", api["check_pairs"](manifest, "", str(repo))),
        ("loop_qualification", api["check_loop_qualifications"](receipt, "")),
    ):
        if findings:
            refuse(code, "; ".join(findings))
    links, reason = api["activation_chain"](str(run))
    if reason:
        refuse("activation_chain", reason)
    for link in links:
        inputs.file(run / link["file"], "activation_chain", link["sha256"])
    for row in receipt["qualifications"]:
        inputs.file(row["receipt"], "loop_qualification", row["receipt_sha256"])


def packet_paths(path, inputs):
    if path.is_dir() and not path.is_symlink():
        paths = sorted(path.glob("PACKET_*.md"))
    else:
        inputs.file(path, "packets_missing")
        paths = [path.parent / line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
    if not paths:
        refuse("packets_missing", "no packets selected")
    paths = [Path(os.path.abspath(p)) for p in paths]
    if len(paths) != len(set(paths)):
        refuse("packets_duplicate", "packet list contains duplicates")
    return paths


def child_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PYTHON")) and k != "KY_GIT"}
    env.update(GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1")
    return env


def child(argv, cwd, code):
    try:
        return subprocess.run(argv, cwd=cwd, env=child_env(), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        refuse(code, f"command could not complete ({type(e).__name__})")


def admit_packets(selected, repo, inputs):
    packets = []
    for packet in selected:
        ref = inputs.file(packet, "packet_not_admitted")
        done = child([sys.executable, "-I", "-B", str(repo / km.FLEET / "kypacket.py"),
                      "check", str(packet), "--repo", str(repo)], repo, "packet_not_admitted")
        try:
            report = json.loads(done.stdout)
        except ValueError:
            report = None
        if done.returncode or not isinstance(report, dict) or report.get("admitted") is not True \
                or report.get("schema") != "ky.packet_check/1" or report.get("packet") != str(packet):
            refuse("packet_not_admitted", f"{packet}: exit {done.returncode}: {' '.join(done.stderr.split())}")
        packets.append(ref)
    return packets


def observe(repo, run, bootstrap):
    try:
        review = repo / bootstrap["review"]["path"]
        return km.observe(str(repo), str(run), bootstrap["approved_source_commit"], str(review),
                          components_commit=bootstrap["components_commit"],
                          recorded_locations=bootstrap["review"].get("area_reviews", []))
    except (km.Refused, KeyError, TypeError, OSError, ValueError) as e:
        refuse("source_observation", str(e))


def build(a):
    repo, run = Path(os.path.abspath(a.repo)), Path(os.path.abspath(a.run))
    out_manifest, out_receipt = Path(os.path.abspath(a.out_manifest)), Path(os.path.abspath(a.out_receipt))
    if out_manifest != run / "VERSIONS.json" or out_receipt != run / "INSTALL_RECEIPT.json":
        refuse("output_path", "outputs must be RUN/VERSIONS.json and RUN/INSTALL_RECEIPT.json")
    inputs = Inputs()
    original = inputs.document(out_receipt, "bootstrap_receipt_missing")
    if original.get("mode") != "bootstrap":
        refuse("bootstrap_receipt_mode", "only a bootstrap receipt may be finalised")
    backup = Path(str(out_receipt) + ".bootstrap")
    backfill_path = Path(str(out_receipt) + ".backfill.json")
    for path in (out_manifest, backup, backfill_path):
        if os.path.lexists(path):
            refuse("output_exists", f"will not overwrite {path}")
    bootstrap_path = run / "VERSIONS.bootstrap.json"
    bootstrap = inputs.document(bootstrap_path, "bootstrap_manifest_missing")
    if km.with_digest(bootstrap)["manifest_sha256"] != bootstrap.get("manifest_sha256"):
        refuse("bootstrap_manifest_digest", "bootstrap manifest digest differs from content")
    if bootstrap.get("mode") != "bootstrap":
        refuse("bootstrap_manifest_mode", "not a bootstrap manifest")
    if bootstrap.get("deferred_components"):
        refuse("deferred_components", "review, bind and reinstall every component first")
    binding = original.get("manifest")
    if not isinstance(binding, dict) or binding.get("manifest_sha256") != bootstrap["manifest_sha256"] \
            or binding.get("sha256") != inputs.hashes[str(bootstrap_path)]:
        refuse("bootstrap_manifest_binding", "installer receipt does not bind this bootstrap manifest")
    source = original.get("source")
    if not isinstance(source, dict) or any(source.get(key) != bootstrap.get(key)
                                           for key in ("approved_source_commit", "components_commit")):
        refuse("bootstrap_source_binding", "installer source commits differ from bootstrap manifest")
    top = km.git(str(repo), "rev-parse", "--show-toplevel")
    if top.returncode or Path(os.path.realpath(top.stdout.strip())) != Path(os.path.realpath(repo)):
        refuse("source_repo", "--repo is not the top of a git work tree")
    observed = observe(repo, run, bootstrap)
    if km.with_digest(observed) != bootstrap:
        refuse("source_observation", "bootstrap manifest no longer matches reviewed source/probes/qualifications")
    for row in observed["components"] + list(observed["entrypoints"].values()):
        inputs.file(repo / row["path"], "source_observation", row["sha256"])
    for pair in observed["generated_pairs"]:
        for key in ("canonical", "compatibility"):
            inputs.file(repo / pair[key], "source_observation", pair["sha256"])
    inputs.file(repo / observed["review"]["path"], "source_observation", observed["review"]["sha256"])
    for row in observed["review"]["area_reviews"]:
        inputs.file(repo / row["record"], "source_observation", row["record_sha256"])
    for row in [observed["probes"]] + observed["qualifications"]:
        inputs.file(row["path"], "source_observation", row["sha256"])
    tracker_revision = installed(original, observed, inputs, repo)
    rehearsal_path, coverage_path = Path(os.path.abspath(a.rehearsal)), Path(os.path.abspath(a.coverage))
    rehearsal = inputs.document(rehearsal_path, "rehearsal_unreadable")
    tested = component_map(rehearsal.get("tested_components"), "tested_components_mismatch")
    if tested != component_map(observed["components"], "manifest_components"):
        refuse("tested_components_mismatch", "rehearsal did not test the exact final component hashes")
    coverage = inputs.document(coverage_path, "coverage_unreadable")
    # Area-review records use review.verdict; aggregate reviews use top-level verdict.
    nested = coverage.get("review")
    verdicts = ([coverage["verdict"]] if "verdict" in coverage else [])
    if isinstance(nested, dict) and "verdict" in nested:
        verdicts.append(nested["verdict"])
    if not verdicts or any(v != "ACCEPTED" for v in verdicts):
        refuse("coverage_not_accepted", "coverage review verdict is not unambiguously ACCEPTED")
    selection = Path(os.path.abspath(a.packets))
    selected = packet_paths(selection, inputs)
    packets = admit_packets(selected, repo, inputs)
    manifest = copy.deepcopy(observed)
    manifest.update(schema="ky.versions/1", mode="final", authorises="final reviewed installed bundle")
    manifest.pop("deferred_note")
    manifest = km.with_digest(manifest)
    receipt = copy.deepcopy(original)
    receipt.update(mode="final", bootstrap_tracker_revision=copy.deepcopy(original["tracker_revision"]),
                   tracker_revision=tracker_revision)
    receipt["manifest"] = {"path": str(out_manifest), "sha256": hashlib.sha256(encoded(manifest)).hexdigest(),
                           "manifest_sha256": manifest["manifest_sha256"]}
    receipt["rehearsal"] = {"results": inputs.file(rehearsal_path, "rehearsal_unreadable"),
                            "sha256": inputs.hashes[str(rehearsal_path)], "tested_components": rehearsal["tested_components"]}
    receipt["coverage"] = dict(inputs.file(coverage_path, "coverage_unreadable"), verdict="ACCEPTED")
    receipt["packets"] = packets
    api = version_api(repo)
    check_version(api, receipt, manifest, repo, run, inputs)
    try:
        argv = shlex.split(a.backfill_validator)
    except ValueError as e:
        refuse("backfill_validator_command", str(e))
    if not argv:
        refuse("backfill_validator_command", "empty command")
    done = child(argv, repo, "backfill_validator_failed")
    if done.returncode != 0:
        refuse("backfill_validator_failed", f"exit {done.returncode}; no validated signal earned")
    evidence = {"schema": "ky.backfill_validation/1", "argv": argv, "cwd": str(repo), "exit_code": done.returncode}
    # No stdout/stderr copied: a validator may emit unrelated sensitive content.
    receipt["backfill"] = {"path": str(backfill_path), "sha256": hashlib.sha256(encoded(evidence)).hexdigest(),
                           "validated": done.returncode == 0}
    inputs.unchanged()
    if packet_paths(selection, inputs) != selected:
        refuse("inputs_changed", "packet directory selection changed")
    if observe(repo, run, bootstrap) != observed:
        refuse("inputs_changed", "source observations changed during validation")
    installed(original, manifest, inputs, repo)   # reverify installed bytes against FINAL manifest
    if admit_packets(selected, repo, inputs) != packets:
        refuse("inputs_changed", "packet admission changed during validation")
    check_version(api, receipt, manifest, repo, run, inputs)
    inputs.unchanged()
    proposed = {"manifest": manifest, "receipt": receipt, "backfill_evidence": evidence}
    if a.dry:
        print(json.dumps(proposed, indent=1, sort_keys=True, ensure_ascii=False))
        return 0
    # No refusal path above has written. Reserve all new files exclusively; roll back
    # publication on I/O failure. Receipt replacement is last (the acceptance switch).
    files = [(backup, out_receipt.read_bytes()), (backfill_path, encoded(evidence)), (out_manifest, encoded(manifest))]
    created = []
    temporary = Path(str(out_receipt) + ".kyfinal.tmp")
    try:
        for path, data in files + [(temporary, encoded(receipt))]:
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary, out_receipt)
    except OSError as e:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        refuse("publication_failed", type(e).__name__)
    print(json.dumps({"out_manifest": str(out_manifest), "out_receipt": str(out_receipt),
                      "manifest_sha256": manifest["manifest_sha256"], "components": len(manifest["components"])}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("build")
    for name in ("repo", "run", "rehearsal", "coverage", "packets", "backfill-validator", "out-manifest", "out-receipt"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--dry", action="store_true")
    args = parser.parse_args(argv)
    try:
        return build(args)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, IndexError) as e:
        print(f"refused: input_unreadable: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
