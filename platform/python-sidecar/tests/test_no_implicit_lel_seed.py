"""
test_no_implicit_lel_seed.py — lifeevents-audit F4 (SS N-109).

`seed_lel_intake(chart_id=...)` writes the native's hard-coded 57-event corpus
into the given chart's `life_events`. The deleted legacy `pipeline/brahma_pipeline.py`
called it for ANY chart during a build. Seeding must only ever happen through the
explicit operator CLI (`python -m brahmagyan.mimamsa.lel_intake seed --chart-id ...`),
never from a build pipeline / orchestrator / writer path.

Pure source scan (no DB, no network).
"""
from __future__ import annotations

import re
from pathlib import Path

SIDECAR = Path(__file__).resolve().parent.parent

# Names that plant the in-source native event corpus into a chart.
_SEEDERS = re.compile(r"\b(seed_lel_intake|seed_event_chart_state_index)\b")

# The ONLY non-test modules allowed to mention a seeder: their own definitions and
# the explicit operator CLI (`_cmd_seed`, which requires --chart-id).
_ALLOWED_MENTIONS = {
    "brahmagyan/mimamsa/lel_intake.py",
    "brahmagyan/mimamsa/l5_lel_intake.py",
    "brahmagyan/mimamsa/l5_event_chart_state_index.py",
}

# Trees that run during a chart build / for arbitrary charts: must never seed.
_BUILD_PATH_DIRS = ("pipeline", "ga_writers", "bodha_writers", "services", "routers", "scripts")


def _py_files(root: Path) -> list[Path]:
    return [
        p for p in root.rglob("*.py")
        if "tests" not in p.relative_to(SIDECAR).parts and "__pycache__" not in p.parts
    ]


def mentions_seeder(src: str) -> bool:
    return bool(_SEEDERS.search(src))


def test_legacy_brahma_pipeline_module_stays_deleted():
    assert not (SIDECAR / "pipeline" / "brahma_pipeline.py").exists()


def test_no_build_path_module_references_a_life_events_seeder():
    offenders = []
    for d in _BUILD_PATH_DIRS:
        base = SIDECAR / d
        if not base.exists():
            continue
        for p in _py_files(base):
            if mentions_seeder(p.read_text(encoding="utf-8", errors="replace")):
                offenders.append(str(p.relative_to(SIDECAR)))
    assert offenders == []


def test_seeders_are_only_mentioned_by_their_own_modules():
    offenders = []
    for p in _py_files(SIDECAR):
        rel = str(p.relative_to(SIDECAR))
        if rel in _ALLOWED_MENTIONS:
            continue
        if mentions_seeder(p.read_text(encoding="utf-8", errors="replace")):
            offenders.append(rel)
    assert offenders == []


def test_operator_cli_seed_requires_explicit_chart_id():
    """The one legitimate call site must not default a chart."""
    src = (SIDECAR / "brahmagyan/mimamsa/lel_intake.py").read_text(encoding="utf-8")
    m = re.search(r"def seed_lel_intake\(\s*\*,\s*chart_id: str,", src)
    assert m, "seed_lel_intake must take a REQUIRED keyword-only chart_id"


def test_scanner_self_check_synthetic():
    assert mentions_seeder("from brahmagyan.mimamsa.lel_intake import seed_lel_intake")
    assert mentions_seeder("seed_event_chart_state_index(chart_id=c)")
    assert not mentions_seeder("def seed_other(chart_id): pass")
