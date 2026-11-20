#!/usr/bin/env python3
"""
sweep_stale_candidate_tags.py — remove zero-traffic `probe-*` candidate tags that
earlier deploy runs left on a Cloud Run service (owner-approved, 2026-10-23).

Each deploy tags its zero-traffic candidate `probe-<sha12>-<run_id>-<attempt>` and
removes the tag at the end. A run cancelled mid-deploy never removes it, and a
tagged revision keeps its min-instance warm forever: two such MCP tags from
2026-09-19 cost ~Rs 7,700 a month until removed by hand on 2026-10-22, and
amjis-sidecar had 93 of them (no cost, but each kept an old revision reachable).

deploy.yml runs this before each candidate deploy. Deploys on main are serialized
(workflow-level concurrency, cancel-in-progress false), so any other `probe-*`
tag belongs to a finished or cancelled run. Only tags of that exact shape that
carry no traffic percent are removed; hand-made tags and the live revision are
never touched. A failure is reported as a workflow warning and never fails the
deploy: the next deploy retries the sweep.

Usage:
    python3 sweep_stale_candidate_tags.py --service amjis-web --keep <this run's tag> \
        [--region asia-south1] [--project madhav-astrology] [--dry-run]

Exit code is always 0 unless the arguments are invalid (2).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

CANDIDATE_TAG = re.compile(r'^probe-[0-9a-f]{12}-\d+-\d+$')


def stale_tags(service_json: dict, keep: str) -> list[str]:
    """Tags of the deploy-candidate shape, other than `keep`, on entries that carry no traffic."""
    out = []
    for entry in (service_json.get('status') or {}).get('traffic') or []:
        tag = entry.get('tag')
        if not tag or tag == keep or not CANDIDATE_TAG.match(tag):
            continue
        if entry.get('percent'):
            continue
        out.append(tag)
    return sorted(set(out))


def _gcloud(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(['gcloud', *args], capture_output=True, text=True, timeout=300)


def sweep(service: str, keep: str, region: str, project: str, dry_run: bool = False, gcloud=_gcloud) -> list[str]:
    where = ['--region', region, '--project', project]
    described = gcloud(['run', 'services', 'describe', service, *where, '--format=json'])
    if described.returncode != 0:
        print(f'::warning::stale-tag sweep: could not read {service}: {described.stderr.strip()[:300]}')
        return []
    tags = stale_tags(json.loads(described.stdout), keep)
    if not tags:
        print(f'stale-tag sweep: {service} has no stale candidate tags')
        return []
    print(f'stale-tag sweep: {service}: removing {len(tags)} stale candidate tag(s): {", ".join(tags)}')
    if dry_run:
        return tags
    removed = gcloud(['run', 'services', 'update-traffic', service, *where, f'--remove-tags={",".join(tags)}', '--quiet'])
    if removed.returncode != 0:
        print(f'::warning::stale-tag sweep: could not remove tags from {service}: {removed.stderr.strip()[:300]}')
        return []
    return tags


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Remove stale zero-traffic probe-* candidate tags from a Cloud Run service.')
    ap.add_argument('--service', required=True)
    ap.add_argument('--keep', required=True, help="this run's own candidate tag (never removed)")
    ap.add_argument('--region', default='asia-south1')
    ap.add_argument('--project', default='madhav-astrology')
    ap.add_argument('--dry-run', action='store_true')
    ns = ap.parse_args(argv)
    try:
        sweep(ns.service, ns.keep, ns.region, ns.project, ns.dry_run)
    except Exception as exc:  # never fail a deploy over housekeeping
        print(f'::warning::stale-tag sweep: {ns.service}: {exc}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
