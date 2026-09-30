"""Shared fixtures for the gochara_eval tests.

Two fixture families:
  * fully synthetic inline fixtures (registry / extract / controls / oracles)
    built in tmp_path — the suite is meaningful without the campaign checkout;
  * the real campaign files, guarded by skipif on os.path.exists so CI without
    the checkout skips cleanly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SIDECAR_ROOT = Path(__file__).resolve().parents[3]
if str(SIDECAR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIDECAR_ROOT))

CAMPAIGN_MEASUREMENT = Path(
    "/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement")
CAMPAIGN_DESIGN = Path(
    "/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design")

REGISTRY_V2_3 = CAMPAIGN_MEASUREMENT / "event_registry_v2_3.json"
EXTRACT_3_0 = CAMPAIGN_MEASUREMENT / "baseline_3_0_extract_v1_0.json"
CONTROLS_V1_3 = CAMPAIGN_MEASUREMENT / "random_controls_v1_3.json"
ORACLES_V1_4 = CAMPAIGN_DESIGN / "GOCHARA_TEST_ORACLES_v1_4.json"

EXTRACT_3_0_PIN = ("70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079"
                   "ef84ff")

needs_campaign = pytest.mark.skipif(
    not REGISTRY_V2_3.exists(), reason="campaign checkout not present")


def synth_registry_counts() -> dict:
    return {"logged_events": 6, "dev": 3, "held_out": 2, "held_out_timing": 1,
            "held_out_year": 1, "excluded": 1, "annotation_rows": 0,
            "exact_cohort": 1, "month_grain": 0, "interval_grain": 0,
            "t_rank_floor": 1}


def synth_registry(events: list[dict] | None = None,
                   counts: dict | None = None) -> dict:
    if events is None:
        events = [
            # the three worked/dev events (never scored as held-out)
            {"eid": "EVT.2013.12.11.01", "tier": "dev", "obs_type": "point",
             "grain": "exact", "date": "2013-12-11", "class": "marriage"},
            {"eid": "EVT.2018.11.28.01", "tier": "dev", "obs_type": "point",
             "grain": "exact", "date": "2018-11-28", "class": "bereavement"},
            {"eid": "EVT.2022.01.03.01", "tier": "dev", "obs_type": "point",
             "grain": "exact", "date": "2022-01-03", "class": "career_entry"},
            # held-out
            {"eid": "EVT.2010.05.20.01", "tier": "held_out_timing",
             "obs_type": "point", "grain": "exact", "date": "2010-05-20",
             "class": "career_advancement"},
            {"eid": "EVT.2015.XX.XX.01", "tier": "held_out_year",
             "obs_type": "point", "grain": "year", "date": "2015",
             "class": "relocation"},
            {"eid": "EVT.CURRENT.01", "tier": "excluded", "obs_type": "status",
             "grain": "exact", "date": "2024-01-01", "class": "chronic_onset"},
        ]
    return {"artifact": "EVENT_REGISTRY", "version": "test",
            "horizon": {"start": "1998-01-01", "end": "2026-04-17",
                        "H_days": 10334},
            "conventions": {"counts": counts or synth_registry_counts()},
            "events": events}


def write_json(path: Path, doc: dict) -> Path:
    path.write_text(json.dumps(doc, indent=1))
    return path


@pytest.fixture()
def synth_registry_path(tmp_path: Path) -> Path:
    return write_json(tmp_path / "registry.json", synth_registry())


def synth_extract(rows: list[dict]) -> dict:
    return {"artifact": "baseline_extract_test", "version": "0",
            "row_count": len(rows), "rows": rows}


@pytest.fixture()
def synth_extract_path(tmp_path: Path) -> Path:
    rows = [
        # one window covering the exact held-out event 2010-05-20
        {"event_class": "career_advancement", "ws": "2010-04-01",
         "we": "2010-07-01", "pk": "2010-05-20", "si": 0.9, "valence": "gain"},
        # one window inside the 2015 year event
        {"event_class": "relocation", "ws": "2015-03-01", "we": "2015-04-01",
         "pk": "2015-03-10", "si": 0.5, "valence": "gain"},
    ]
    return write_json(tmp_path / "extract.json", synth_extract(rows))
