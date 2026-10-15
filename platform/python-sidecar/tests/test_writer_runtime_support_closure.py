"""Freeze exception 1/2 (N-266): ga_* / bo_* digest closures must stay service-free.

`get_writer_source_hash` walks every import (including function-local ones), so a
ga_*/bo_* writer that reached `asset_runner` used to pull `service_probes` and
`services/*` (Kāla) into its code digest. The digest helpers now live in
`writer_runtime_support`; this guard keeps the leak from coming back silently.
"""
from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner
from pipeline.orchestrator import writer_runtime_support as wrs
from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all

_SERVICES_PREFIX = "platform/python-sidecar/services/"


def test_no_ga_or_bo_writer_digest_closure_contains_a_services_file():
    discover_all()
    ids = sorted(a for a in WRITER_REGISTRY if a.startswith(("ga_", "bo_")))
    assert ids, "no ga_*/bo_* writers registered -- the guard would pass vacuously"
    for asset_id in ids:
        files = [p for p, _ in asset_runner._writer_source_files(asset_runner._writer_source_paths(asset_id))]
        leaked = [p for p in files if p.startswith(_SERVICES_PREFIX) or "service_probes" in p]
        assert not leaked, f"{asset_id} digest closure reaches services: {leaked[:3]}"


def test_get_writer_source_hash_is_still_exported_from_asset_runner():
    assert asset_runner.get_writer_source_hash is wrs.get_writer_source_hash
    assert asset_runner._duration_columns_present is wrs._duration_columns_present
    assert asset_runner._WRITER_HASH_VERSION == b"nirmana-writer-source-v1\\0"


def test_writer_runtime_support_imports_nothing_from_services_or_probes():
    tree = ast.parse(pathlib.Path(wrs.__file__).read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(("." * node.level) + (node.module or ""))
            names += [a.name for a in node.names]
    assert not [n for n in names if "services" in n or "service_probes" in n], names
