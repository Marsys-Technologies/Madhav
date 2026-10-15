"""regenerate_bg_rules_pins.py: (re)write the committed pin manifest of the bg_rules parser closure (Nikasa N-431).

The manifest `bg_rules_parser_pins_v1.json` (next to this script) is the REVIEWED declaration the census checks the sandbox run against: every file the bg_rules parser pulls in
(l0_rules.py, its import closure, the data file it reads at import, and the pinned adapter n431_rules_adapter.py) with its sha256, plus `runner_sha256`, the digest of
parser_sandbox.py (the child's own code). It is the ONLY place those digests are decided; the sandbox never discovers pins at run time, and a CI test (test_n431_corpus_derived_detector.py,
TestCommittedPinManifest) fails when the committed file differs from a fresh regeneration, i.e. when l0_rules.py, the adapter, a helper, the data file or parser_sandbox.py changed without
this script being re-run (and the diff reviewed).

Run from anywhere:
    python3 platform/scripts/governance/pins/regenerate_bg_rules_pins.py            # rewrite the manifest in place
    python3 platform/scripts/governance/pins/regenerate_bg_rules_pins.py --check    # exit 1 if the committed manifest is stale (no write)

HOW THE FILE SET IS CHOSEN. `discover_closure` runs the real adapter once in the sandbox with NO pins except the adapter and pins whatever the sandbox reports as an unpinned import,
until the run is accepted. That is a REGENERATION aid only (it executes the parser in the guarded child, which is what the sandbox is for); the manifest it writes is what is reviewed in git.
The discovery run passes the test-only escape `allow_unpinned_runner_for_tests`, because the runner digest it is about to pin does not exist yet.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MANIFEST_REL = "platform/scripts/governance/pins/bg_rules_parser_pins_v1.json"
MODULE_ROOT = "platform/python-sidecar"
ADAPTER_REL = "platform/python-sidecar/brahmagyan/n431_rules_adapter.py"
FUNCTION = "run_chunk"
SANDBOX_REL = "platform/scripts/governance/parser_sandbox.py"
VALID_IDS = ["bphs", "saravali"]
SMOKE_CHUNKS = [
    {"id": "11111111-1111-4111-8111-111111111111", "text_id": "bphs", "verse_ref": "1.1",
     "content_en": "If Jupiter is placed in the seventh house from the Lagna, the native will be learned and wealthy. Saturn in the tenth house gives power to the native."},
    {"id": "33333333-3333-4333-8333-333333333333", "text_id": "bphs", "verse_ref": "3.4", "content_en": "A note about the weather with no astrological content at all."},
]


def load_sandbox(repo_root=REPO_ROOT):
    """The parser_sandbox module of `repo_root`, loaded by file path under a private name."""
    path = pathlib.Path(repo_root) / SANDBOX_REL
    spec = importlib.util.spec_from_file_location("parser_sandbox_for_pin_regeneration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover_closure(sandbox, repo_root, adapter_rel=ADAPTER_REL, module_root=MODULE_ROOT, function=FUNCTION, inputs=None):
    """REGENERATION AID (never production): pin the adapter, run it in the sandbox, pin each file the sandbox reports as unpinned, repeat until the run is accepted.
    Returns (last result, [{"path", "sha256"}] in discovery order)."""
    root = pathlib.Path(repo_root)
    if inputs is None:
        inputs = [{"chunk": c, "valid_text_ids": VALID_IDS} for c in SMOKE_CHUNKS]
    pinned = []
    result = {"ok": False, "error": "no run"}
    for _ in range(60):
        result = sandbox.run_pinned_parser(str(root), module_root, pinned, adapter_rel, function, inputs, timeout_s=120, allow_unpinned_runner_for_tests=True)
        if result["ok"]:
            return result, pinned
        if result["error"].startswith("unpinned_import: "):
            new = result["unpinned_files"]
        elif not pinned or result["error"].startswith("pin_missing: file is not one of pinned_files"):
            new = [adapter_rel]
        else:
            return result, pinned
        have = {d["path"] for d in pinned}
        pinned = pinned + [{"path": n, "sha256": hashlib.sha256((root / n).read_bytes()).hexdigest()} for n in new if n not in have]
    return result, pinned


def build_manifest_doc(repo_root=REPO_ROOT) -> dict:
    """A fresh manifest document: the discovered closure (sorted by path, digests from the working tree) and the runner digest of the sandbox file in `repo_root`."""
    sandbox = load_sandbox(repo_root)
    result, pinned = discover_closure(sandbox, repo_root)
    if not result["ok"]:
        raise RuntimeError("the real parser closure could not be discovered: " + str(result.get("error")))
    if sandbox.RUNNER_SHA256 is None:
        raise RuntimeError("the sandbox runner digest is unavailable")
    return {"pinned_files": sorted(pinned, key=lambda d: d["path"]), "runner_sha256": sandbox.RUNNER_SHA256}


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    target = REPO_ROOT / MANIFEST_REL
    fresh = render(build_manifest_doc(REPO_ROOT))
    current = target.read_text(encoding="utf-8") if target.is_file() else None
    if check:
        if current != fresh:
            print("STALE: %s differs from a fresh regeneration; run this script and review the diff" % MANIFEST_REL)
            return 1
        print("ok: %s is current" % MANIFEST_REL)
        return 0
    if current != fresh:
        target.write_text(fresh, encoding="utf-8")
        print("wrote %s" % MANIFEST_REL)
    else:
        print("unchanged: %s" % MANIFEST_REL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
