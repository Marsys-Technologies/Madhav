"""
F-A16 regression test: strength_formula_version must never claim a formula ran when
`strength` itself is honestly NULL (constituent_bala_v1 has no resolvable shadbala for
the yoga's constituents — the Rahu-only karakāṃśa case, which has no classical shadbala).

Prior to the fix, both ga_yoga_firings insert sites wrote
`derivation or STRENGTH_FORMULA_VERSION` — since `derivation` is None whenever
`_compute_constituent_bala_strength` legitimately found nothing to compute, this silently
substituted an UNRELATED constant (STRENGTH_FORMULA_VERSION, actually the Pancha Mahapurusha
dignity formula's own label from a different code path) as if a formula had run.

Confirmed live on production: jaimini_karakamsha_rahu on chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a
carried strength_formula_version='yogi_strength_formula_v1' with strength=NULL on all 4 built
ayanamshas -- exactly this defect. Migration 746 (F-A14 for ga_yoga) ships a real detector for it
and reads genuinely red until affected charts are rebuilt with this fix.
"""
from __future__ import annotations

from ga_writers.ga_yoga_writer import ChartState, _build_karakamsha_firings


class _FakeCursor:
    """Captures every execute() call's parameter tuple; no real DB involved."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.calls.append((sql, params))


def _rahu_only_karakamsha_state() -> ChartState:
    """A minimal chart state: Rahu sits in the karakāṃśa sign (occupation fires), and no
    other karakāṃśa graha (sun/moon/mars/jupiter/venus/saturn) has a sign at all -- so only
    jaimini_karakamsha_rahu is eligible to fire."""
    facts = [
        {
            "fact_id": "rahu_sign_fact",
            "fact_category": "graha_position",
            "fact_subject": "RAH_MEAN",
            "fact_key": "sign",
            "fact_value_text": "Aries",
            "fact_value_num": None,
        },
        {
            "fact_id": "karakamsa_sign_fact",
            "fact_category": "karakamsa_position",
            "fact_subject": "KARAKAMSA",
            "fact_key": "sign",
            "fact_value_text": "Aries",
            "fact_value_num": None,
        },
    ]
    return ChartState(facts)


def test_rahu_karakamsha_strength_formula_version_is_null_not_invented():
    """The exact F-A16 scenario: Rahu has no classical shadbala, so strength AND
    strength_formula_version must both stay honestly NULL -- never the unrelated
    Pancha Mahapurusha constant."""
    state = _rahu_only_karakamsha_state()
    cur = _FakeCursor()

    rows_inserted = _build_karakamsha_firings(
        cur,
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        build_uuid="00000000-0000-0000-0000-000000000000",
        ayanamsha_id="lahiri_chitrapaksha",
        state=state,
        shadbala_map={},  # empty -- no classical shadbala for Rahu (or anyone)
        family_map={},
    )

    assert rows_inserted == 1, "only jaimini_karakamsha_rahu should be eligible to fire"
    assert len(cur.calls) == 1

    _sql, params = cur.calls[0]
    # Positional order in the INSERT: chart_id, build_id, ayanamsha_id, yoga_canonical_id,
    # fired, constituent_fact_ids, constituent_planets, constituent_houses, strength,
    # strength_formula_version, partial_formation_pct, is_partial, bhanga_active,
    # bhanga_rule_fired, bhanga_na_reason, derivation, strength_label, citation_ref,
    # citation_human, family_ids.
    strength = params[8]
    strength_formula_version = params[9]

    assert strength is None, "Rahu has no classical shadbala -- strength must be NULL"
    assert strength_formula_version is None, (
        "F-A16 regression: strength_formula_version must be NULL alongside strength, "
        "never fall back to an unrelated formula-version constant"
    )
