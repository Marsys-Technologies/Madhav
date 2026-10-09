"""sidecar_shard.py: pytest plugin that runs ONE deterministic, size-balanced shard of the Governance Gates python-sidecar suite.

The `Governance Gates (drift / schema / edge / native-literal / py-sidecar)` check spent 21.5-24.9 of its 22-26 minutes in one serial pytest
call over the python-sidecar suite. ci.yml now runs that call as K parallel shard jobs (`governance-gates-py-sidecar-shard`) plus an aggregate
job that keeps the ORIGINAL required name. Each shard runs today's command UNCHANGED (same positional paths, same --ignore list, same -m
expression, same environment) with two extra arguments:

    PYTHONPATH=<this directory> pytest <today's selection> -p sidecar_shard --ci-shard I/K

so pytest collects exactly what the unsharded job collected, and this plugin then keeps only the tests of the FILES assigned to shard I and
reports the rest as deselected. Splitting by file (never inside one) keeps module- and class-scoped fixtures built once, as today.

Assignment: every test file of the real collection (the nodeid's path before '::', after -m deselection), heaviest first (ties by path), is
placed on the currently lightest shard (ties: lowest index). A file's weight is its measured CI seconds from FILE_SECONDS when listed, else
DEFAULT_SECONDS_PER_TEST times its number of selected tests. A pure function of the collection plus this table: no timings are read at run
time, nothing is random, so a shard's content does not move between runs. A new test file lands in some shard automatically.

Completeness (fails closed): every shard computes the WHOLE K-way partition from the full collection it actually made and stops with a usage
error (exit 4, no test runs) unless the K shards together hold every collected test exactly once and no shard is empty. All K shards run the
same check on the same collection, so a test can be neither dropped nor run twice without the shards going red. The terminal summary prints
the shard's share and a digest of the full collection, so the K logs can be compared by eye.

`--ci-shard-plan` prints the whole partition (file -> shard, estimated seconds) to the terminal summary: run it with --collect-only for a dry
partition over the real collection.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict

import pytest

#: Measured CI seconds of the 41 files of 4 s or more, which are ~90% of the suite's run time. Source: the serial Governance Gates run on
#: main at 9a99847 (job 113261736442, 2026-10-08, 1447 s of pytest): each `-q` progress line's timestamp delta (72 tests) was mapped onto
#: the collection order (aligned on the 32 xfail markers) and apportioned within the line by a local per-test timing run. The rest of the
#: suite (~13,000 tests, ~120 s) averages DEFAULT_SECONDS_PER_TEST per selected test, which is what an unlisted or NEW file weighs.
#: A listed path that is no longer collected is simply unused; test_ci_sidecar_shard.py fails if a listed path is not a file on the tree,
#: so the table cannot rot silently. Re-measure (same method) when a shard runs well above the others.
FILE_SECONDS: dict[str, float] = {
    "tests/l3/gochara/test_station_refine.py": 230,
    "tests/test_ga7_writer.py": 116,
    "tests/test_gochara_grammar.py": 98,
    "tests/l3/ka_kshetra/test_event_classes_disclosure.py": 97,
    "tests/test_migration_1252_ga_medical_band_scope.py": 89,
    "tests/l3/ka_kshetra/test_stage4_field.py": 74,
    "tests/test_migration_1262_chart_fact_identity_registration.py": 47,
    "tests/test_migration_1254_ga_sensitive_tiers.py": 46,
    "tests/test_q03_tiers_dashas.py": 46,
    "tests/l3/ka_kshetra/test_writer.py": 39,
    "tests/test_migration_1275_chart_delete_per_chart_tables.py": 38,
    "tests/test_migration_1255_builder_reference_grants.py": 35,
    "tests/test_l5_frozen_guard_1265_guards.py": 31,
    "tests/test_l5_frozen_guard_1265_truncate_fk.py": 30,
    "tests/l3/gochara/test_c49_wrap_cut_support.py": 25,
    "pipeline/orchestrator/writers/tests/test_bg_sky_calendar.py": 23,
    "tests/test_special_lagna_sunrise_sun.py": 22,
    "tests/test_argala_migration_1221_sql.py": 19,
    "tests/l3/gochara/test_a53_aspect_span.py": 18,
    "tests/test_migration_1222_1223_ga_vargas.py": 13,
    "tests/test_u3_convergence_currents.py": 13,
    "pipeline/orchestrator/tests/test_provenance.py": 12,
    "tests/l3/gochara/test_vedha_interval_gate.py": 12,
    "tests/l3/gochara/test_c46_slice_round2.py": 11,
    "tests/test_migration_1304_ka_gochara_v5_registry_row.py": 11,
    "tests/test_l1_emitted_categories_have_ownership.py": 9,
    "tests/test_l5_reference_resolution_ledger_design.py": 9,
    "tests/test_seed_native_anchors_severed.py": 9,
    "tests/test_yoga_formation_band_route.py": 9,
    "tests/test_data_plane_revert_gate_states.py": 8,
    "tests/l3/ka_kshetra/test_circularity_guard.py": 6,
    "tests/test_bg_kp_sublord_division.py": 6,
    "tests/test_migration_1299_bo_sangati_integrity_conjunct3.py": 6,
    "tests/test_swiss_backend_helper.py": 6,
    "tests/l0/test_citation_pass2_transit.py": 5,
    "tests/test_migration_1259_integrity_scope_own_output.py": 5,
    "tests/test_wave_scheduler.py": 5,
    "tests/l0/test_citation_pass2_yogas.py": 4,
    "tests/l3/test_ka_sangam.py": 4,
    "tests/test_ga_uuid_chart_id_orchestrator_path.py": 4,
    "tests/test_migration_1302_revoke_orchestrator_windows.py": 4,
}
DEFAULT_SECONDS_PER_TEST = 0.009

_KEY = pytest.StashKey[dict]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("sidecar_shard", "deterministic CI sharding of the governance-gates python-sidecar suite")
    group.addoption("--ci-shard", metavar="I/K", default=None, help="run only shard I (1-based) of K")
    group.addoption("--ci-shard-plan", action="store_true", default=False, help="print the whole partition in the terminal summary")


def parse_shard(spec: str) -> tuple[int, int]:
    try:
        i_s, k_s = spec.split("/")
        i, k = int(i_s), int(k_s)
    except (ValueError, AttributeError):
        raise pytest.UsageError(f"--ci-shard must be I/K (e.g. 2/4), got {spec!r}") from None
    if k < 1 or not 1 <= i <= k:
        raise pytest.UsageError(f"--ci-shard {spec!r}: need 1 <= I <= K")
    return i, k


def file_of(nodeid: str) -> str:
    return nodeid.split("::", 1)[0]


def weights(nodeids: list[str]) -> dict[str, float]:
    count: dict[str, int] = defaultdict(int)
    for n in nodeids:
        count[file_of(n)] += 1
    return {f: FILE_SECONDS.get(f, DEFAULT_SECONDS_PER_TEST * c) for f, c in count.items()}


def partition(nodeids: list[str], k: int) -> list[list[str]]:
    """The K file lists (each sorted) of a collection: largest-weight-first greedy onto the lightest shard."""
    w = weights(nodeids)
    shards: list[list[str]] = [[] for _ in range(k)]
    load = [0.0] * k
    for f in sorted(w, key=lambda p: (-w[p], p)):
        i = min(range(k), key=lambda j: (load[j], j))
        shards[i].append(f)
        load[i] += w[f]
    return [sorted(s) for s in shards]


def verify(nodeids: list[str], shards: list[list[str]]) -> list[str]:
    """Problems that would make the K shards together run something other than the full collection exactly once (empty = sound)."""
    problems = []
    flat = [f for s in shards for f in s]
    files = {file_of(n) for n in nodeids}
    seen: set[str] = set()
    doubled = sorted({f for f in flat if f in seen or seen.add(f)})
    if doubled:
        problems.append("test files in more than one shard: " + ", ".join(doubled))
    if files - set(flat):
        problems.append("test files in no shard: " + ", ".join(sorted(files - set(flat))))
    if set(flat) - files:
        problems.append("shard files that were not collected: " + ", ".join(sorted(set(flat) - files)))
    empty = [i + 1 for i, s in enumerate(shards) if not s]
    if empty:
        problems.append(f"empty shard(s): {empty}")
    sets = [set(s) for s in shards]
    per_shard = [sum(1 for n in nodeids if file_of(n) in s) for s in sets]
    if sum(per_shard) != len(nodeids):
        problems.append(f"the shards hold {sum(per_shard)} tests, the collection has {len(nodeids)}")
    return problems


def digest(nodeids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodeids)).encode()).hexdigest()[:16]


@pytest.hookimpl(trylast=True)          # after -m / -k deselection: shard what would actually run today
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    spec = config.getoption("ci_shard")
    if spec is None:
        return
    i, k = parse_shard(spec)
    nodeids = [it.nodeid for it in items]
    if not nodeids:
        raise pytest.UsageError(f"ci-shard {spec}: the full collection is empty; refusing to report a shard of nothing as green")
    shards = partition(nodeids, k)
    problems = verify(nodeids, shards)
    if problems:
        raise pytest.UsageError(f"ci-shard {spec}: the {k} shards are not exactly the full collection: " + "; ".join(problems))
    mine = set(shards[i - 1])
    keep = [it for it in items if file_of(it.nodeid) in mine]
    drop = [it for it in items if file_of(it.nodeid) not in mine]
    if drop:
        config.hook.pytest_deselected(items=drop)
    items[:] = keep
    w = weights(nodeids)
    config.stash[_KEY] = {
        "spec": spec, "i": i, "k": k, "total": len(nodeids), "files": len(w), "digest": digest(nodeids),
        "kept": len(keep), "kept_files": len(mine), "shards": shards, "w": w,
        "est": [sum(w[f] for f in s) for s in shards],
    }


def pytest_terminal_summary(terminalreporter, exitstatus, config: pytest.Config) -> None:
    st = config.stash.get(_KEY, None)
    if st is None:
        return
    tr = terminalreporter
    est = ", ".join(f"{e:.0f}s" for e in st["est"])
    tr.write_line(
        f"ci-shard {st['spec']}: {st['kept']} of {st['total']} tests in {st['kept_files']} of {st['files']} files "
        f"(full collection digest {st['digest']}; estimated shard seconds {est})"
    )
    if config.getoption("ci_shard_plan"):
        for n, s in enumerate(st["shards"], 1):
            tr.write_line(f"ci-shard plan {n}/{st['k']}: {len(s)} files, est {st['est'][n - 1]:.0f}s")
            for f in s:
                tr.write_line(f"  [{n}] {st['w'][f]:8.2f}s  {f}")
