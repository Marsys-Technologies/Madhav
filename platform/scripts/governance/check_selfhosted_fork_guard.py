#!/usr/bin/env python3
"""check_selfhosted_fork_guard.py -- SR-SELFHOSTED-SPLIT (OWNER-SELFHOSTED-SPLIT-20261018), item 3.

The repository is public and some CI jobs run on the owner's own machine (label `madhav-db`). A pull request from a fork
runs the fork author's code, so a fork-reachable job must never be able to land on a self-hosted runner, and a job that
can must never mount a path of the machine into a container. This check reads every workflow under `.github/workflows`
and FAILS (exit 1) on:

  SELFHOSTED_UNFENCED   a job that can run on a non-GitHub-hosted runner, in a workflow a fork PR can reach (a
                        `pull_request` trigger), without the fork fence;
  SELFHOSTED_UNFENCEABLE  the same job in a workflow with a trigger the fence cannot protect (`pull_request_target`,
                        `workflow_run`, `issue_comment`, `workflow_call`, ... anything outside the allowed set);
  HOST_MOUNT            a job that can run on a self-hosted runner and mounts a host path (container / service
                        `volumes`, `-v` / `--volume` / `--mount type=bind` in `options` or in a `docker` command of a
                        `run` step).

A runner is "provably GitHub-hosted" only when every label is a literal `ubuntu-*` / `windows-*` / `macos-*`. Anything
else -- `self-hosted`, a custom label, a runner group, or an expression (`needs.*`, `matrix.*`, `fromJSON(...)`) -- is
treated as possibly self-hosted. A possibly-self-hosted job is fenced by exactly one of:

  runs-on: ${{ (FENCE) && <anything> || '<github-hosted label>' }}      (the form ci.yml uses: the fence is evaluated
                                                                        before the dynamic part; the only other
                                                                        branch is a hosted label)
  if: ... && (FENCE) && ...  (or `if: FENCE`)                           (the job is skipped for a fork PR)

where FENCE is, byte for byte after whitespace is collapsed:

  github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository

(I) INTERPRETATION: the host-mount rule applies to jobs that can run self-hosted, not to GitHub-hosted jobs (one hosted
job in ci.yml legitimately mounts /var/run/postgresql into its own throwaway service container; a GitHub-hosted VM is
destroyed after the job and exposes nothing of the owner's machine).

Usage:  check_selfhosted_fork_guard.py [--workflows DIR] [--json]     exit 0 clean, 1 violations, 2 usage / unreadable.
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
    print('check_selfhosted_fork_guard: PyYAML is required', file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKFLOWS = ROOT / '.github' / 'workflows'

FORK_FENCE = ("github.event_name != 'pull_request' || "
              "github.event.pull_request.head.repo.full_name == github.repository")
HOSTED_LABEL = re.compile(r'^(ubuntu|windows|macos)-[A-Za-z0-9._-]+$')
# Events a fenced (or fence-free) self-hosted job may sit under: all of them only fire for code already in this repository,
# except `pull_request`, which the fence handles. Every other event can be started by, or carry data from, a fork.
FENCE_FREE_EVENTS = {'push', 'merge_group', 'schedule', 'workflow_dispatch', 'release', 'repository_dispatch'}
FENCED_EVENTS = {'pull_request'}


def _norm(expr: str) -> str:
    expr = expr.strip()
    m = re.fullmatch(r'\$\{\{(.*)\}\}', expr, re.S)
    if m:
        expr = m.group(1)
    return re.sub(r'\s+', ' ', expr).strip()


def _split_top(expr: str, op: str) -> list[str]:
    """Split on `op` outside parentheses and outside '...' string literals (a '' inside a literal is an escaped quote)."""
    parts, depth, cur, i, in_str = [], 0, [], 0, False
    while i < len(expr):
        ch = expr[i]
        if in_str:
            cur.append(ch)
            if ch == "'":
                if expr[i + 1:i + 2] == "'":
                    cur.append("'")
                    i += 1
                else:
                    in_str = False
        elif ch == "'":
            in_str = True
            cur.append(ch)
        elif ch == '(':
            depth += 1
            cur.append(ch)
        elif ch == ')':
            depth -= 1
            cur.append(ch)
        elif depth == 0 and expr.startswith(op, i):
            parts.append(''.join(cur).strip())
            cur = []
            i += len(op)
            continue
        else:
            cur.append(ch)
        i += 1
    parts.append(''.join(cur).strip())
    return parts


def runs_on_texts(runs_on) -> list[str]:
    if runs_on is None:
        return []
    if isinstance(runs_on, str):
        return [runs_on]
    if isinstance(runs_on, list):
        return [str(x) for x in runs_on]
    if isinstance(runs_on, dict):
        out = ['group:' + str(runs_on['group'])] if 'group' in runs_on else []
        labels = runs_on.get('labels', [])
        return out + ([labels] if isinstance(labels, str) else [str(x) for x in labels])
    return [str(runs_on)]


def provably_hosted(runs_on) -> bool:
    texts = runs_on_texts(runs_on)
    return bool(texts) and all('${{' not in t and HOSTED_LABEL.match(t.strip()) for t in texts)


def runs_on_is_fenced(runs_on) -> bool:
    """`(FENCE) && <then> || '<hosted literal>'`: nothing dynamic is reachable unless the fence holds, and the only other
    branch is a GitHub-hosted label. A second top-level `||` would add a branch the fence does not cover."""
    if not isinstance(runs_on, str):
        return False
    expr = _norm(runs_on)
    ors = _split_top(expr, '||')
    if len(ors) != 2:
        return False
    else_lit = re.fullmatch(r"'([^']+)'", ors[1])
    if not else_lit or not HOSTED_LABEL.match(else_lit.group(1)):
        return False
    ands = _split_top(ors[0], '&&')
    return len(ands) >= 2 and ands[0] == f'({FORK_FENCE})'


def if_is_fenced(cond) -> bool:
    """The job `if:` contains the fence as a top-level `&&` conjunct (or is the fence) and has no top-level `||`."""
    if not isinstance(cond, str):
        return False
    expr = _norm(cond)
    if expr == FORK_FENCE or expr == f'({FORK_FENCE})':
        return True
    if len(_split_top(expr, '||')) != 1:
        return False
    return f'({FORK_FENCE})' in _split_top(expr, '&&')


def workflow_events(doc: dict) -> set[str]:
    on = doc.get('on', doc.get(True))  # PyYAML reads the bare key `on` as the boolean True
    if on is None:
        return set()
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return {str(x) for x in on}
    if isinstance(on, dict):
        return {str(k) for k in on}
    return set()


def _volume_is_host_path(spec: str) -> bool:
    spec = spec.strip().strip('"\'')
    parts = spec.split(':')
    if len(parts) < 2:
        return False  # an anonymous volume: container path only
    src = parts[0]
    return src.startswith(('/', '~', '.', '$')) or '${{' in src


def _mount_arg_is_host_path(arg: str) -> bool:
    fields = dict(kv.split('=', 1) if '=' in kv else (kv, '') for kv in arg.strip('"\'').split(','))
    kind = fields.get('type', 'volume')
    src = fields.get('source', fields.get('src', ''))
    return kind == 'bind' or (kind == 'volume' and src.startswith(('/', '~', '.')))


def _option_mounts(options: str) -> list[str]:
    try:
        toks = shlex.split(options)
    except ValueError:
        toks = options.split()
    found, i = [], 0
    while i < len(toks):
        t = toks[i]
        arg = None
        if t in ('-v', '--volume', '--mount') and i + 1 < len(toks):
            arg, flag = toks[i + 1], t
            i += 1
        elif t.startswith(('--volume=', '--mount=')):
            flag, arg = t.split('=', 1)
        elif t.startswith('-v') and len(t) > 2 and ':' in t:
            flag, arg = '-v', t[2:]
        if arg is not None:
            host = _mount_arg_is_host_path(arg) if flag == '--mount' else _volume_is_host_path(arg)
            if host:
                found.append(f'{flag} {arg}')
        i += 1
    return found


def _run_step_mounts(script: str) -> list[str]:
    found = []
    for line in re.sub(r'\\\n', ' ', script).splitlines():
        if not re.search(r'\b(docker|podman)\b', line):
            continue
        for m in re.finditer(r'(?:^|\s)(--volume|-v)(?:\s+|=)(["\']?[^\s"\']+)', line):
            if _volume_is_host_path(m.group(2)):
                found.append(f'{m.group(1)} {m.group(2)}')
        for m in re.finditer(r'(?:^|\s)--mount(?:\s+|=)(["\']?[^\s"\']+)', line):
            if _mount_arg_is_host_path(m.group(1)):
                found.append(f'--mount {m.group(1)}')
    return found


def job_host_mounts(job: dict) -> list[str]:
    found: list[str] = []
    containers = []
    if isinstance(job.get('container'), dict):
        containers.append(('container', job['container']))
    for name, svc in (job.get('services') or {}).items():
        if isinstance(svc, dict):
            containers.append((f'services.{name}', svc))
    for where, spec in containers:
        for vol in spec.get('volumes') or []:
            if _volume_is_host_path(str(vol)):
                found.append(f'{where}.volumes: {vol}')
        if isinstance(spec.get('options'), str):
            found += [f'{where}.options: {m}' for m in _option_mounts(spec['options'])]
    for step in job.get('steps') or []:
        if isinstance(step, dict) and isinstance(step.get('run'), str):
            found += [f"step {step.get('name', step.get('id', '?'))!r}: {m}" for m in _run_step_mounts(step['run'])]
    return found


def check_document(name: str, doc) -> list[dict]:
    out: list[dict] = []

    def add(job, code, message):
        out.append({'workflow': name, 'job': job, 'code': code, 'message': message})

    if not isinstance(doc, dict):
        add('-', 'UNPARSEABLE', 'workflow is not a YAML mapping; refusing to guess')
        return out
    events = workflow_events(doc)
    unfenceable = sorted(events - FENCE_FREE_EVENTS - FENCED_EVENTS)
    needs_fence = bool(events & FENCED_EVENTS)
    for job_id, job in (doc.get('jobs') or {}).items():
        if not isinstance(job, dict) or 'runs-on' not in job:
            continue
        runs_on = job['runs-on']
        if provably_hosted(runs_on):
            continue
        fenced = runs_on_is_fenced(runs_on) or if_is_fenced(job.get('if'))
        label = ' '.join(runs_on_texts(runs_on))
        if unfenceable:
            add(job_id, 'SELFHOSTED_UNFENCEABLE',
                f'runs-on {label!r} can be self-hosted, but the workflow is also triggered by {unfenceable}, '
                f'which a fork can reach and the fence cannot protect (never pull_request_target on a self-hosted label)')
        elif needs_fence and not fenced:
            add(job_id, 'SELFHOSTED_UNFENCED',
                f'runs-on {label!r} can be self-hosted and a fork PR reaches this job: add the fork fence '
                f'to runs-on ((FENCE) && ... || \'ubuntu-latest\') or to the job `if:`')
        for mount in job_host_mounts(job):
            add(job_id, 'HOST_MOUNT', f'a job that can run self-hosted mounts a host path ({mount})')
    return out


def check_directory(directory: Path) -> list[dict]:
    violations: list[dict] = []
    files = sorted([*directory.glob('*.yml'), *directory.glob('*.yaml')])
    for path in files:
        try:
            doc = yaml.safe_load(path.read_text(encoding='utf-8'))
        except yaml.YAMLError as exc:
            violations.append({'workflow': path.name, 'job': '-', 'code': 'UNPARSEABLE', 'message': str(exc).splitlines()[0]})
            continue
        violations += check_document(path.name, doc)
    return violations


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--workflows', type=Path, default=DEFAULT_WORKFLOWS)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if not args.workflows.is_dir():
        print(f'check_selfhosted_fork_guard: not a directory: {args.workflows}', file=sys.stderr)
        return 2
    violations = check_directory(args.workflows)
    if args.json:
        print(json.dumps(violations, indent=2))
    else:
        for v in violations:
            print(f"FAIL {v['workflow']} :: {v['job']} :: {v['code']}: {v['message']}")
        print(f"check_selfhosted_fork_guard: {len(violations)} violation(s) in {args.workflows}")
    return 1 if violations else 0


if __name__ == '__main__':
    raise SystemExit(main())
