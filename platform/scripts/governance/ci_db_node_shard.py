"""Pytest collection partition for the replace-chain CI workers.

Explicitly loaded by ci_discovery; all files are collected on each worker, but
only its balanced node IDs execute. Fixture scopes and test IDs stay unchanged.
"""
import os

import pytest

from ci_db_shard import JOB_SHARDS, NODE_SHARD_JOBS, partition_nodes


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    # Apply pytest's -k/--deselect policy first, including under --collect-only.
    job = os.environ.get('CI_DB_SHARD_JOB')
    spec = os.environ.get('CI_DB_SHARD', '')
    if job not in NODE_SHARD_JOBS:
        raise pytest.UsageError('node shard plugin requires an owned DB shard job')
    try:
        index, count = map(int, spec.split('/'))
        if count != JOB_SHARDS[job] or not 1 <= index <= count:
            raise ValueError('invalid shard range/count')
        chosen = set(partition_nodes([item.nodeid for item in items], job, count)[index-1])
    except ValueError as exc:
        raise pytest.UsageError(str(exc)) from exc
    selected = [item for item in items if item.nodeid in chosen]
    deselected = [item for item in items if item.nodeid not in chosen]
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected  # retain pytest's original ordering and fixture lifecycle


def index_cache(factory):
    """Memoize real full-domain indexes; isolate callers with independent copies.

    The module fixture has already verified the pinned, read-only corpus. This
    saves repeated 87-year sampling in every record phase without substituting
    numerical data or changing the domain, solver, knots, or precision.
    """
    from copy import deepcopy
    from functools import lru_cache
    cached = lru_cache(maxsize=None)(factory)
    def get(body, ephe_path):
        return deepcopy(cached(body, ephe_path))
    get.cache_info = cached.cache_info
    return get


_INDEX_CACHES = []


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    outcome = yield
    if outcome.excinfo is not None:
        return
    if (fixturedef.argname == 'template'
            and fixturedef.func.__module__.endswith('.test_a55_replace_chain')):
        from pipeline.orchestrator.writers import ka_gochara_v5 as writer
        from services.gochara_kernel import substrate
        original = writer.production_arc_index
        original_kernel = substrate.production_arc_index
        cached = index_cache(original)
        writer.production_arc_index = cached
        substrate.production_arc_index = cached  # station lookups import this binding lazily
        def restore():
            writer.production_arc_index = original
            substrate.production_arc_index = original_kernel
        request.addfinalizer(restore)
        _INDEX_CACHES.append(cached)


def pytest_terminal_summary(terminalreporter):
    for cached in _INDEX_CACHES:
        terminalreporter.write_line(f'Real full-domain arc index cache: {cached.cache_info()}')
