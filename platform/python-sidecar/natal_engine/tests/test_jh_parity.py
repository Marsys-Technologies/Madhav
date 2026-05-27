"""
test_jh_parity.py — Unit 1.2 parity harness skeleton.

This test asserts the natal_engine output matches the pinned Jagannatha Hora
oracle (G1, `jh_oracle_pinned` gate). The actual field-by-field comparison
lands in unit 1.2.

State at unit 1.1: SKIPPED — `fixtures/jh_oracle.json` is not present. The
test is collectable (pytest --collect-only picks it up) and would xfail/skip
with an explicit reason rather than fail or error.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from natal_engine.fixtures.jh_oracle_loader import (
    JH_ORACLE_PATH,
    jh_oracle_present,
)


@pytest.mark.skipif(
    not jh_oracle_present(),
    reason=(
        "jh_oracle_pinned gate red — fixtures/jh_oracle.json not present. "
        f"Expected at: {JH_ORACLE_PATH}. Native owes the JH oracle export; "
        "until then unit 1.2 parity cannot run."
    ),
)
def test_parity_against_oracle() -> None:
    """Unit 1.2 will fill the body: load oracle, run compute_chart, diff
    field-by-field (longitudes within arcsecond tolerance, signs/nakshatras/
    padas exact, mahadasha sequence within seconds-tolerance, etc.).

    Today (unit 1.1) the body is intentionally a no-op TODO — the test only
    needs to be PRESENT and COLLECTABLE for the unit 1.1 acceptance
    criteria. The @pytest.mark.skipif guard above makes the gate-red state
    visible without breaking CI.
    """
    # TODO(unit 1.2): implement JH parity diff per master plan §1.2.
    pytest.fail(
        "Unit 1.1 placeholder — jh_oracle.json is present but parity logic "
        "ships in unit 1.2. If you see this failure, unit 1.2 must implement "
        "the actual comparison."
    )
