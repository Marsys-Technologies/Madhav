#!/usr/bin/env python3
"""Flag-drift guard for every `gcloud` call in the GitHub workflows (CLAUDE.md §N.8).

Why: the Gochara verification-job definition workflow (run 39736105931, 2026-10-22) died in production on
`gcloud run jobs deploy ... --clear-args` — "unrecognized arguments: --clear-args". Nothing in CI had ever asked gcloud
whether the flag exists. This tool asks, in two modes, each measuring one claim:

  static  every flag a workflow passes to gcloud is in the per-command allow-list of `gcloud_flag_reference_v1.json`
          (transcribed from Google's official reference pages; the fixture labels its source). Needs no gcloud, no cloud.
  live    every flag a workflow passes to gcloud appears in the real `gcloud <command> --help` of the gcloud on THIS machine
          (the runner image's gcloud). `--help` makes no API call and needs no credential. This is the detector that reads
          false when the runner's gcloud drifts from the reference or a flag was never real.

Scanned: `run:` scripts of `.github/workflows/*.yml` and `.github/actions/*/action.yml` (composite steps), plus the `flags:`
input of `google-github-actions/deploy-cloudrun` steps (passed to `gcloud run deploy`). A gcloud command that is not in the
reference fixture is a failure too (an unknown command is not "no flags"), so a new call site must add its reference.

Usage: gcloud_flag_drift.py {static|live} [--root REPO_ROOT] [--reference FILE]
Exit: 0 clean, 1 drift/unknown command, 2 usage or tool error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_REFERENCE = HERE / 'gcloud_flag_reference_v1.json'
DEPLOY_CLOUDRUN_ACTION = 'google-github-actions/deploy-cloudrun'
DEPLOY_CLOUDRUN_COMMAND = 'run deploy'

_EXPR = re.compile(r'\$\{\{.*?\}\}', re.S)
_GCLOUD = re.compile(r'(?<![\w./$-])gcloud(?=\s)')
_FLAG = re.compile(r'^--[A-Za-z][A-Za-z0-9-]*')
_PATH_WORD = re.compile(r'^[a-z][a-z0-9-]*$')
_TERMINATORS = set('|;&<>)`\n')
_ARRAY_DEF = re.compile(r'^[ \t]*([A-Za-z_]\w*)=\(\n(.*?)\n[ \t]*\)[ \t]*$', re.S | re.M)
_ARRAY_USE = re.compile(r'^\$\{([A-Za-z_]\w*)\[@\]\}$')


@dataclass(frozen=True)
class Call:
    file: str
    step: str
    words: tuple[str, ...]      # tokens after `gcloud`, quotes removed

    def flags(self) -> list[str]:
        return [m.group(0) for w in self.words if (m := _FLAG.match(w))]


def tokenize_command(text: str) -> list[str]:
    """Words of one shell command starting at `text[0]`, ending at an unquoted | ; & < > ) ` or newline."""
    words: list[str] = []
    cur: list[str] = []
    started = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in ' \t':
            if started:
                words.append(''.join(cur)); cur, started = [], False
        elif ch in _TERMINATORS:
            break
        elif ch == '#' and not started:
            break
        elif ch == '\\' and i + 1 < n:
            cur.append(text[i + 1]); started = True; i += 1
        elif ch in '\'"':
            j = text.find(ch, i + 1)
            while ch == '"' and j != -1 and text[j - 1] == '\\':
                j = text.find(ch, j + 1)
            j = n if j == -1 else j
            cur.append(text[i + 1:j]); started = True; i = j
        else:
            cur.append(ch); started = True
        i += 1
    if started:
        words.append(''.join(cur))
    return words


def logical_script(script: str) -> str:
    """Placeholders for ${{ }}, backslash continuations joined, full-line comments dropped."""
    script = _EXPR.sub('GHEXPR', script)
    script = re.sub(r'\\\n[ \t]*', ' ', script)
    return '\n'.join(l for l in script.split('\n') if not l.strip().startswith('#'))


def calls_in_script(script: str, file: str, step: str) -> list[Call]:
    """Each `gcloud` call's words; a `"${NAME[@]}"` word is expanded from a bash array `NAME=( ... )` defined in the same script."""
    text = logical_script(script)
    arrays = {m.group(1): tokenize_command(m.group(2).replace('\n', ' ')) for m in _ARRAY_DEF.finditer(text)}
    calls = []
    for m in _GCLOUD.finditer(text):
        words: list[str] = []
        for w in tokenize_command(text[m.end():]):
            use = _ARRAY_USE.match(w)
            words += arrays.get(use.group(1), [w]) if use else [w]
        calls.append(Call(file, step, tuple(words)))
    return calls


def _steps(doc: dict):
    for job in (doc.get('jobs') or {}).values():
        yield from (job.get('steps') or [])
    yield from ((doc.get('runs') or {}).get('steps') or [])


def collect_calls(root: Path) -> list[Call]:
    files = sorted((root / '.github/workflows').glob('*.yml')) + sorted((root / '.github/actions').glob('*/action.yml'))
    calls: list[Call] = []
    for path in files:
        doc = yaml.safe_load(path.read_text()) or {}
        rel = str(path.relative_to(root))
        for step in _steps(doc):
            name = str(step.get('name') or step.get('id') or '?')
            if step.get('run'):
                calls += calls_in_script(str(step['run']), rel, name)
            if str(step.get('uses', '')).startswith(DEPLOY_CLOUDRUN_ACTION) and (step.get('with') or {}).get('flags'):
                words = tuple(tokenize_command(logical_script(str(step['with']['flags'])).replace('\n', ' ')))
                calls.append(Call(rel, name, (*DEPLOY_CLOUDRUN_COMMAND.split(), *words)))
    return calls


def load_reference(path: Path) -> dict:
    ref = json.loads(path.read_text())
    assert ref.get('schema') == 'ky.gcloud_flag_reference/1', f'{path}: unexpected schema'
    return ref


def resolve_command(call: Call, commands: dict) -> str | None:
    """Longest reference command that is a prefix of the call's leading path words."""
    path: list[str] = []
    for w in call.words:
        if not _PATH_WORD.match(w):
            break
        path.append(w)
    for size in range(len(path), 0, -1):
        candidate = ' '.join(path[:size])
        if candidate in commands:
            return candidate
    return None


def uses_by_command(calls: list[Call], reference: dict) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """({command: {flag: [where, ...]}}, [unknown-command problems])."""
    used: dict[str, dict[str, list[str]]] = {}
    problems: list[str] = []
    for call in calls:
        where = f'{call.file} :: {call.step}'
        command = resolve_command(call, reference['commands'])
        if command is None:
            problems.append(f'{where}: gcloud command not in the reference fixture: gcloud {" ".join(call.words[:4])} ...')
            continue
        for flag in call.flags():
            used.setdefault(command, {}).setdefault(flag, []).append(where)
    return used, problems


def static_problems(used: dict, reference: dict) -> list[str]:
    allowed_global = set(reference['global_flags'])
    problems = []
    for command, flags in sorted(used.items()):
        allowed = set(reference['commands'][command]) | allowed_global
        for flag, places in sorted(flags.items()):
            if flag not in allowed:
                problems.append(f'`gcloud {command}` has no flag {flag} in the reference ({places[0]})')
    return problems


def help_flags(help_text: str) -> set[str]:
    """Every long flag named in `--help` output; `--[no-]x` counts as both --x and --no-x."""
    text = re.sub(r'--\[no-\]([A-Za-z0-9-]+)', r'--\1 --no-\1', help_text)
    return set(re.findall(r'(?<![\w-])(--[A-Za-z][A-Za-z0-9-]*)', text))


def live_problems(used: dict, run_help=None) -> list[str]:
    run_help = run_help or _gcloud_help
    problems = []
    for command, flags in sorted(used.items()):
        help_text = run_help(command)
        known = help_flags(help_text)
        if not known:
            problems.append(f'`gcloud {command} --help` printed no flags at all; cannot verify')
            continue
        for flag, places in sorted(flags.items()):
            if flag not in known:
                problems.append(f'`gcloud {command} --help` on this runner does not list {flag} ({places[0]})')
    return problems


def _gcloud_help(command: str) -> str:
    result = subprocess.run(['gcloud', *command.split(), '--help'], capture_output=True, text=True, timeout=120,
                            env={'PATH': os.environ['PATH'], 'HOME': os.environ.get('HOME', '/tmp'),
                                 'CLOUDSDK_CORE_DISABLE_PROMPTS': '1', 'CLOUDSDK_PAGER': '', 'TERM': 'dumb'})
    if result.returncode != 0:
        raise RuntimeError(f'`gcloud {command} --help` exited {result.returncode}: {result.stderr.strip()[:300]}')
    return result.stdout


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('mode', choices=['static', 'live'])
    ap.add_argument('--root', type=Path, default=HERE.parents[2])
    ap.add_argument('--reference', type=Path, default=DEFAULT_REFERENCE)
    args = ap.parse_args(argv)
    try:
        reference = load_reference(args.reference)
        calls = collect_calls(args.root)
        used, problems = uses_by_command(calls, reference)
        if args.mode == 'static':
            problems += static_problems(used, reference)
        else:
            print(subprocess.run(['gcloud', 'version'], capture_output=True, text=True, timeout=60).stdout.strip())
            problems += live_problems(used)
    except (OSError, RuntimeError, subprocess.SubprocessError, AssertionError, yaml.YAMLError) as exc:
        print(f'gcloud_flag_drift: tool error: {exc}', file=sys.stderr)
        return 2
    n_flags = sum(len(f) for f in used.values())
    print(f'gcloud_flag_drift[{args.mode}]: {len(calls)} gcloud calls, {len(used)} commands, {n_flags} distinct command/flag pairs')
    for p in problems:
        print(f'::error::gcloud flag drift: {p}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
