#!/usr/bin/env python3
"""check_registry_pull_guard.py -- no workflow may download this project's own container images back out of Artifact Registry.

A pull from `asia-south1-docker.pkg.dev/madhav-astrology/...` to a GitHub-hosted runner is billed as Artifact Registry internet
egress. deploy.yml's pipeline-job verify steps used to `docker run` the ~3.7 GB image they had just pushed, so every pipeline
deploy downloaded it again: 615 GiB / ~Rs 5,566 in the 30 days to 2026-10-22 (owner-approved fix, 2026-10-23). The image is now
kept with `load: true` and run with `--pull=never`. This check reads every workflow under `.github/workflows` and FAILS (exit 1) on:

  REGISTRY_PULL       a `docker pull` of a project registry image in a `run` step;
  REGISTRY_RUN_PULLS  a `docker run` / `docker create` of a project registry image without `--pull=never` (Docker pulls a missing
                      image silently; `--pull=never` turns a missing local copy into a loud failure instead of a download);
  REGISTRY_CONTAINER  a job `container:` or `services:` image from the project registry (the runner pulls it before any step).

Deploying an image to Cloud Run / Cloud Run Jobs (`gcloud run ... --image=...`) is not a pull to the runner and is not checked.

Usage:  check_registry_pull_guard.py [--workflows DIR] [--json]     exit 0 clean, 1 violations, 2 usage / unreadable.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs pyyaml for every governance job
    print('check_registry_pull_guard: PyYAML is required', file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKFLOWS = ROOT / '.github' / 'workflows'

PROJECT = 'madhav-astrology'
# <region>-docker.pkg.dev/<project>/..., the legacy gcr.io/<project>/... hosts, and the bare registry host form.
REGISTRY_IMAGE = re.compile(r'(?:^|[\s"\'=])(?:[a-z0-9-]+-docker\.pkg\.dev|(?:[a-z]+\.)?gcr\.io)/' + re.escape(PROJECT) + r'/')
DOCKER_CMD = re.compile(r'\bdocker\s+(?:container\s+|image\s+)?(run|create|pull)\b')


def _logical_lines(script: str) -> list[str]:
    """Join backslash continuations so a `docker run` split over several lines is one command."""
    return re.sub(r'\\\n', ' ', script).splitlines()


def _commands(line: str) -> list[str]:
    """Split a shell line on `&&`, `||`, `;` and `|` (good enough for workflow steps; quoting is not interpreted here)."""
    return [c.strip() for c in re.split(r'&&|\|\||;|\|', line) if c.strip()]


def _has_pull_never(command: str) -> bool:
    try:
        toks = shlex.split(command, comments=True)
    except ValueError:
        toks = command.split()
    for i, t in enumerate(toks):
        if t == '--pull=never' or (t == '--pull' and i + 1 < len(toks) and toks[i + 1] == 'never'):
            return True
    return False


def check_run(where: str, script: str) -> list[dict]:
    out = []
    for line in _logical_lines(script):
        if line.lstrip().startswith('#'):
            continue
        for cmd in _commands(line):
            m = DOCKER_CMD.search(cmd)
            if not m or not REGISTRY_IMAGE.search(cmd):
                continue
            verb = m.group(1)
            if verb == 'pull':
                out.append({'code': 'REGISTRY_PULL', 'where': where, 'command': cmd})
            elif not _has_pull_never(cmd):
                out.append({'code': 'REGISTRY_RUN_PULLS', 'where': where, 'command': cmd})
    return out


def _image_of(spec) -> str | None:
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict) and isinstance(spec.get('image'), str):
        return spec['image']
    return None


def check_document(name: str, doc: dict) -> list[dict]:
    out = []
    jobs = (doc or {}).get('jobs') or {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        images = [('container', _image_of(job.get('container')))]
        images += [(f'services.{k}', _image_of(v)) for k, v in (job.get('services') or {}).items()]
        for field, image in images:
            if image and REGISTRY_IMAGE.search(' ' + image):
                out.append({'code': 'REGISTRY_CONTAINER', 'where': f'{name}:{job_id}.{field}', 'command': image})
        for i, step in enumerate(job.get('steps') or []):
            if isinstance(step, dict) and isinstance(step.get('run'), str):
                label = step.get('name') or f'step {i + 1}'
                out += check_run(f'{name}:{job_id} / {label}', step['run'])
    return out


def check_directory(directory: Path) -> list[dict]:
    out = []
    for path in sorted(list(directory.glob('*.yml')) + list(directory.glob('*.yaml'))):
        out += check_document(path.name, yaml.safe_load(path.read_text()))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Fail on workflow steps that download project images from Artifact Registry.')
    ap.add_argument('--workflows', type=Path, default=DEFAULT_WORKFLOWS)
    ap.add_argument('--json', action='store_true')
    ns = ap.parse_args(argv)
    if not ns.workflows.is_dir():
        print(f'check_registry_pull_guard: not a directory: {ns.workflows}', file=sys.stderr)
        return 2
    try:
        violations = check_directory(ns.workflows)
    except (OSError, yaml.YAMLError) as exc:
        print(f'check_registry_pull_guard: unreadable workflow: {exc}', file=sys.stderr)
        return 2
    if ns.json:
        print(json.dumps(violations, indent=2))
    else:
        for v in violations:
            print(f"{v['code']}: {v['where']}: {v['command']}")
        print(f'check_registry_pull_guard: {len(violations)} violation(s)')
    return 1 if violations else 0


if __name__ == '__main__':
    sys.exit(main())
