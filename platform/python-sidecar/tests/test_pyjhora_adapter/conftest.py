"""Shared fixtures for pyjhora_adapter tests.

Sets QT_QPA_PLATFORM=offscreen before any jhora import (headless safety) and
exposes the native birth data + a computed native chart.
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

# Native birth data (Abhisek Mohanty — 1984-02-05 10:43 IST Bhubaneswar).
NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.2961,
    "longitude_deg": 85.8245,
    "place_name": "Bhubaneswar",
    "subject_label": "abhisek_mohanty_native",
}

# Julian day (local wall-clock) for the native instant — for unit-level tests.
NATIVE_JD = 2445735.9465277777


@pytest.fixture(scope="session")
def native_inputs() -> dict:
    return dict(NATIVE_INPUTS)


@pytest.fixture(scope="session")
def native_jd() -> float:
    return NATIVE_JD


@pytest.fixture(scope="session")
def native_chart() -> dict:
    from pyjhora_adapter import compute_chart
    return compute_chart(
        inputs=dict(NATIVE_INPUTS),
        ayanamsha_id="lahiri",
        computed_at_iso="2026-06-01T00:00:00+00:00",
    )
