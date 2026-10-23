#!/usr/bin/env python3
"""Apply the verified `ci-generated` overlay of a reviewed source SHA onto a checkout, and nothing else.

The seal workflow checks out `github.sha` raw, but under SR-CHURN-CUT 3 the committed copy of every machine-owned file (the Gochara
`implementation_digest.lock.json` among them) is stale by design: CI regenerates them from main and publishes the `ci-generated` artifact.
deploy.yml bakes that artifact into the image through `.github/actions/restore-generated`; this tool lets the seal job run on the SAME bytes.

It is stricter than the restore action, which extracts the artifact straight into the tree: the artifact is first extracted into a quarantine
directory (`--artifact`), checked there, and only the manifest's files are copied into `--root`.

  apply_generated_overlay.py --artifact DIR --sha SHA [--root ROOT]

Refused (exit 1, one `generated overlay refused: <name>: ...` line per finding on stderr, nothing copied):
  - a manifest that is missing, has another schema or another source SHA, is `test_only`, or does not list exactly `ci_generated.OUTPUTS`;
  - a listed path that is not in `generated_paths.json` (so no source or workflow file can ride in through the overlay);
  - any byte of any listed file that differs from its manifest digest (`ci_generated.verify`);
  - any file in the artifact that the manifest does not list, a symlink, or a destination whose path crosses a symlink.
Exit 0: every manifest file is copied and re-verified in place."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ci_generated  # noqa: E402
import generated_paths  # noqa: E402


def findings(artifact: Path, doc: dict, sha: str) -> list[str]:
    out = []
    if not artifact.is_dir() or artifact.is_symlink():
        return ['artifact_missing: ' + str(artifact) + ' is not a directory']
    out += ['overlay_unverified: ' + e for e in ci_generated.verify(artifact, doc, sha)]
    files = doc.get('files') if isinstance(doc.get('files'), dict) else {}
    if set(files) != set(ci_generated.OUTPUTS):
        out.append('overlay_incomplete: the manifest does not list exactly the declared generated outputs')
    reg = generated_paths.load()
    out += ['path_not_generated: ' + p for p in sorted(files) if not generated_paths.is_generated(p, reg)]
    allowed = set(files) | {ci_generated.MANIFEST}
    for dirpath, dirnames, filenames in os.walk(artifact, followlinks=False):
        base = Path(dirpath)
        for name in dirnames + filenames:
            entry = base / name
            rel = entry.relative_to(artifact).as_posix()
            if entry.is_symlink():
                out.append('symlink_in_artifact: ' + rel)
            elif entry.is_file() and rel not in allowed:
                out.append('unlisted_file_in_artifact: ' + rel)
    return out


def apply(artifact: Path, sha: str, root: Path) -> list[str]:
    manifest = artifact / ci_generated.MANIFEST
    if not manifest.is_file() or manifest.is_symlink():
        return ['manifest_missing: ' + ci_generated.MANIFEST]
    try:
        doc = json.loads(manifest.read_text())
    except ValueError as exc:
        return ['manifest_unreadable: ' + str(exc)]
    if not isinstance(doc, dict):
        return ['manifest_unreadable: not an object']
    bad = findings(artifact, doc, sha)
    if bad:
        return bad
    for rel in sorted(doc['files']) + [ci_generated.MANIFEST]:
        target = root / rel
        walk = target
        while walk != root:
            if walk.is_symlink():
                return ['destination_symlink: ' + rel]
            walk = walk.parent
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(artifact / rel, target)
    return ['overlay_not_applied: ' + e for e in ci_generated.verify(root, doc, sha)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--artifact', type=Path, required=True, help='the extracted ci-generated artifact (a quarantine directory)')
    ap.add_argument('--sha', required=True, help='the reviewed source SHA the overlay must be bound to')
    ap.add_argument('--root', type=Path, default=ci_generated.ROOT, help='the checkout to overlay (default: this repository)')
    ns = ap.parse_args(argv)
    errors = apply(ns.artifact, ns.sha, ns.root.resolve())
    for error in errors:
        print('generated overlay refused: ' + error, file=sys.stderr)
    if not errors:
        print(f'generated overlay applied: {len(ci_generated.OUTPUTS)} files bound to {ns.sha}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
