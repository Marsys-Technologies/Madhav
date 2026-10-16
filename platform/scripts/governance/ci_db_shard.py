#!/usr/bin/env python3
"""File-balanced DB jobs. Discovery remains authoritative; timings only choose placement.

CI_DB_SHARD_JOB and CI_DB_SHARD=I/K apply one whole-job partition to every discovery
invocation, including mixed pytest/Vitest jobs. Empty shares of an individual step
are intentional; an empty whole-job shard or a selector outside its job is fatal.
"""
from __future__ import annotations

from collections import Counter
import json
import math
import os
from pathlib import Path

JOB_SHARDS = {
    'db-integration-tests': 4,
    'gochara-a55-replace-chain': 2,
    'gochara-a55-teardown': 3,
    'gochara-a55-teardown-round3': 2,
    'gochara-a55-round2-runner': 3,
    'gochara-a55-verifier-fixes': 3,
}
TIMINGS = Path(__file__).with_name('ci_db_shard_timings.json')
# (I) INTERPRETATION: an unmeasured/new file weighs one second until remeasured.
# This affects placement only, never discovery or whether a test runs.
DEFAULT_SECONDS = 1.0


def job_profiles(job: str) -> dict:
    from ci_discovery import profiles
    # The digit boundary prevents teardown from claiming teardown-round2/round3.
    return {key: p for key, p in profiles().items()
            if key.startswith(job+'-') and key[len(job)+1:len(job)+2].isdigit()}


def partition_job(root: Path, job: str, count: int, durations: dict | None = None) -> list[list[str]]:
    from ci_discovery import discover
    if count < 1:
        raise ValueError('DB shard count must be positive')
    profiles = job_profiles(job)
    if not profiles:
        raise ValueError(f'unknown DB shard job: {job}')
    files = {str(Path(p['cwd']) / f) for p in profiles.values() for f in discover(root, p)}
    if any((root / f).is_dir() for f in files):
        raise ValueError(f'{job}: DB file sharding requires file discovery, not directory selectors')
    fixed = {}
    if durations is None:
        timing = json.loads(TIMINGS.read_text())
        durations = timing['file_seconds']
        fixed = timing.get('shard_fixed_seconds', {}).get(job, {})
    loads = [float(fixed.get(str(i+1), 0)) for i in range(count)]
    if any(value < 0 or not math.isfinite(value) for value in loads):
        raise ValueError(f'{job}: invalid fixed shard work budget')
    shards: list[list[str]] = [[] for _ in range(count)]
    def weight(f):
        value = float(durations.get(f, DEFAULT_SECONDS))
        if value <= 0 or not math.isfinite(value):
            raise ValueError(f'invalid DB timing for {f}: {value}')
        return value
    for path in sorted(files, key=lambda f: (-weight(f), f)):
        index = min(range(count), key=lambda i: (loads[i], i))
        shards[index].append(path)
        loads[index] += weight(path)
    if any(not shard for shard in shards) or Counter(sum(shards, [])) != Counter(files):
        raise ValueError(f'{job}: shard partition is empty, incomplete or duplicated')
    return [sorted(shard) for shard in shards]


def selected_files(root: Path, suite: str | None, profile: dict, files: list[str]) -> list[str]:
    job, spec = os.environ.get('CI_DB_SHARD_JOB'), os.environ.get('CI_DB_SHARD')
    if job is None and spec is None:
        return files
    if not job or not spec or suite not in job_profiles(job):
        raise ValueError(f'DB shard context does not own discovery suite {suite!r}')
    try:
        index, count = map(int, spec.split('/'))
    except (ValueError, AttributeError):
        raise ValueError(f'DB shard must be I/K, got {spec!r}') from None
    if not 1 <= index <= count:
        raise ValueError(f'DB shard must satisfy 1 <= I <= K, got {spec!r}')
    if job in JOB_SHARDS and count != JOB_SHARDS[job]:
        raise ValueError(f'{job}: expected {JOB_SHARDS[job]} shards, got {count}')
    chosen = set(partition_job(root, job, count)[index-1])
    selected = [f for f in files if str(Path(profile['cwd']) / f) in chosen]
    print(f'DB shard {job} {spec}: {suite}: {len(selected)}/{len(files)} files', flush=True)
    return selected
