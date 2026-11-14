"""Stale deploy-candidate tags are swept before every candidate deploy (owner-approved, 2026-10-23).

A cancelled deploy leaves its `probe-*` tag behind and the tagged revision keeps a min-instance warm: two such MCP tags cost
~Rs 7,700 a month for five weeks. These tests pin (1) which tags the sweep removes and which it must never touch, using a fake
gcloud, and (2) that deploy.yml runs the sweep, keeping its own tag, before each of the three candidate deploys.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'platform/scripts/ci/sweep_stale_candidate_tags.py'
_spec = importlib.util.spec_from_file_location('sweep_stale_candidate_tags', SCRIPT)
sweep_mod = importlib.util.module_from_spec(_spec)
sys.modules['sweep_stale_candidate_tags'] = sweep_mod
_spec.loader.exec_module(sweep_mod)

KEEP = 'probe-0cc2198dbec8-39837722805-1'
STALE_A = 'probe-dd82ef952cd4-35450010050-1'
STALE_B = 'probe-ee1b9f22390a-35458376340-1'


def service(*entries) -> dict:
    return {'status': {'traffic': list(entries)}}


LIVE = {'revisionName': 'amjis-mcp-probe-d339567d401e-39833381094-1', 'percent': 100}


def test_only_zero_traffic_candidate_shaped_tags_other_than_keep_are_stale():
    doc = service(
        LIVE,
        {'revisionName': 'r-keep', 'tag': KEEP},
        {'revisionName': 'r-a', 'tag': STALE_A},
        {'revisionName': 'r-b', 'tag': STALE_B, 'percent': 0},
        {'revisionName': 'r-manual', 'tag': 'mcp-iam-a'},            # hand-made: never touched
        {'revisionName': 'r-canary', 'tag': 'limits-canary'},        # hand-made: never touched
        {'revisionName': 'r-odd', 'tag': 'probe-rollback-verify'},   # not the deploy shape
        {'revisionName': 'r-serving', 'tag': 'probe-aaaaaaaaaaaa-1-1', 'percent': 10},  # carries traffic
    )
    assert sweep_mod.stale_tags(doc, KEEP) == [STALE_A, STALE_B]


def test_nothing_stale_means_no_update_call():
    calls = []

    def gcloud(args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(service(LIVE, {'tag': KEEP})), '')

    assert sweep_mod.sweep('amjis-mcp', KEEP, 'asia-south1', 'madhav-astrology', gcloud=gcloud) == []
    assert len(calls) == 1 and calls[0][:3] == ['run', 'services', 'describe']


def test_sweep_removes_exactly_the_stale_tags_in_one_update():
    calls = []

    def gcloud(args):
        calls.append(args)
        if args[1:2] == ['services'] and args[2] == 'describe':
            return subprocess.CompletedProcess(args, 0, json.dumps(service(LIVE, {'tag': KEEP}, {'tag': STALE_B}, {'tag': STALE_A})), '')
        return subprocess.CompletedProcess(args, 0, '', '')

    assert sweep_mod.sweep('amjis-mcp', KEEP, 'asia-south1', 'madhav-astrology', gcloud=gcloud) == [STALE_A, STALE_B]
    update = calls[1]
    assert update[:4] == ['run', 'services', 'update-traffic', 'amjis-mcp']
    assert f'--remove-tags={STALE_A},{STALE_B}' in update
    assert not any(a.startswith('--to-') or a.startswith('--set-tags') for a in update)  # never moves traffic


def test_dry_run_and_gcloud_failures_never_raise_or_update(capsys):
    calls = []

    def gcloud(args):
        calls.append(args)
        if args[2] == 'describe':
            return subprocess.CompletedProcess(args, 0, json.dumps(service({'tag': STALE_A})), '')
        return subprocess.CompletedProcess(args, 1, '', 'conflict')

    assert sweep_mod.sweep('amjis-web', KEEP, 'r', 'p', dry_run=True, gcloud=gcloud) == [STALE_A]
    assert len(calls) == 1
    assert sweep_mod.sweep('amjis-web', KEEP, 'r', 'p', gcloud=gcloud) == []
    assert '::warning::' in capsys.readouterr().out

    def broken(args):
        return subprocess.CompletedProcess(args, 1, '', 'permission denied')

    assert sweep_mod.sweep('amjis-web', KEEP, 'r', 'p', gcloud=broken) == []


def test_main_always_exits_zero_even_without_gcloud(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError('gcloud')

    monkeypatch.setattr(sweep_mod.subprocess, 'run', boom)
    assert sweep_mod.main(['--service', 'amjis-web', '--keep', KEEP]) == 0


def test_deploy_sweeps_before_each_candidate_deploy_and_keeps_its_own_tag():
    jobs = yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())['jobs']
    for job, service_name, candidate in (('deploy-web', 'amjis-web', 'web-candidate'),
                                         ('deploy-sidecar', 'amjis-sidecar', 'sidecar-candidate'),
                                         ('deploy-mcp', 'amjis-mcp', 'mcp-candidate')):
        steps = jobs[job]['steps']
        names = [s.get('name', '') for s in steps]
        sweep_i = next(i for i, s in enumerate(steps) if 'sweep_stale_candidate_tags.py' in s.get('run', ''))
        ident_i = next(i for i, s in enumerate(steps) if s.get('id') == candidate)
        deploy_i = next(i for i, s in enumerate(steps) if s.get('uses', '').startswith('google-github-actions/deploy-cloudrun'))
        assert ident_i < sweep_i < deploy_i, (job, names)
        step = steps[sweep_i]
        assert f'--service {service_name}' in step['run']
        assert '--keep "$KEEP_TAG"' in step['run']
        assert step['env']['KEEP_TAG'] == '${{ steps.%s.outputs.tag }}' % candidate
        assert 'if' not in step  # runs on every deploy of that service
