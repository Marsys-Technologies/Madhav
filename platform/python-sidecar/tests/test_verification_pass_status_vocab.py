"""
test_verification_pass_status_vocab.py — R6-1f Ring-1 regression guard.

Found live during this lane's own Ring-1 self-verification rebuild attempt
(482012f1, 2026-07-10): `chart_dashas` and `chart_divisionals` both carry a
`verification_pass_status` CHECK constraint (migration 206) restricted to
exactly {'two_pass_verified', 'classical_match', 'divergent_flagged',
'single'} — NOT the wider vocabulary chart_facts allows (which has no such
constraint, and where "single_pass" / "documented_approximation" are valid,
already-wired tiers per bodha_writers/formulas.py VERIFICATION_RESCALE).

M-22's fix (demoting fabricated top-tier "two_pass_verified" stamps to an
honest tier) initially used "documented_approximation" uniformly across
every writer touched — correct for chart_facts writers (ga_sensitive,
ga_structural, ga_panchanga, chart_facts_writer_a3) but a live
psycopg.errors.CheckViolation for the two writers that target
chart_dashas (ga_dashas_writer._verify_mudda / _verify_kalachakra) and
chart_divisionals (ga_vargas_writer's D60 deity/quality + saptavargaja
rows) — both corrected to "single" instead.

This test is a permanent, DB-free guard: it hardcodes each table's real
CHECK-constraint vocabulary (verified once against the live schema — see
migration 206_ga3_supporting_tables.sql) and asserts every writer function
known to feed that table only emits values from the correct set. It cannot
detect a future schema change to the constraint itself (that would need a
live DB read), but it locks in the current contract so no writer silently
drifts back to the wider chart_facts vocabulary for these two tables.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Real CHECK constraint vocabulary, migration 206_ga3_supporting_tables.sql:
#   CHECK (verification_pass_status IN
#     ('two_pass_verified','classical_match','divergent_flagged','single'))
# Applies identically to both chart_dashas and chart_divisionals.
#
# SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 3): this set used to be hardcoded
# here — one more independent copy of a vocabulary that existed in five disagreeing
# places. It now comes from the single declaration, so a change to the constraint is
# made in exactly one file. (Re-verified against live pg_constraint 2026-07-30.)
from ga_writers.verification_vocab import RESTRICTED_TABLE_VOCAB  # noqa: E402


def test_verify_mudda_stays_within_chart_dashas_vocab():
    from ga_writers.ga_dashas_writer import _verify_mudda

    assert _verify_mudda([]) in RESTRICTED_TABLE_VOCAB
    assert _verify_mudda([{"level_n": 1, "lord_graha": "Ketu", "start_date": "1984-02-05"}]) in RESTRICTED_TABLE_VOCAB


def test_verify_kalachakra_stays_within_chart_dashas_vocab():
    from ga_writers.ga_dashas_writer import _verify_kalachakra, KALACHAKRA_SIGN_YEARS

    assert _verify_kalachakra([]) in RESTRICTED_TABLE_VOCAB
    sign = KALACHAKRA_SIGN_YEARS[0][0]
    rows = [{"level_n": 1, "lord_graha": sign}]
    assert _verify_kalachakra(rows) in RESTRICTED_TABLE_VOCAB


def test_d60_deity_rows_stay_within_chart_divisionals_vocab():
    """_build_deity_rows's D60 branch (M-17 fix) must emit a
    chart_divisionals-legal verification_pass_status, not the
    chart_facts-only 'documented_approximation' tier.

    M-17 (R6-1b) made D60 quality/deity a real DB-backed lookup against
    bg_shashtiamsha_deities (migration 430) — without a live `conn`, the
    function now correctly floors to zero rows (canonical-or-floor) rather
    than fabricating a value, so this test needs a minimal mock connection
    exercising the real code path, not a conn=None call."""
    from unittest.mock import MagicMock
    from ga_writers.ga_vargas_writer import _build_deity_rows

    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    # amsa_number=1 kroora row — matches whatever amsa 1° Aries resolves to;
    # test only needs the lookup to hit a real row, not a specific amsa.
    mock_cur.fetchall.return_value = [(n, "kroora" if n % 2 else "soumya", None) for n in range(1, 61)]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    rows = _build_deity_rows(
        "test-chart-id", "lahiri_chitrapaksha", "test-build-id",
        60, "D60", {"Sun": {"sign_idx": 0, "degree_in_sign": 1.0}},
        conn=mock_conn,
    )
    assert rows, "expected at least one D60 deity row when the reference table is reachable"
    for r in rows:
        assert r["verification_pass_status"] in RESTRICTED_TABLE_VOCAB, (
            f"D60 row verification_pass_status={r['verification_pass_status']!r} "
            f"violates chart_divisionals CHECK constraint"
        )

    # Conversely: with NO conn (table genuinely unreachable), the function must
    # floor honestly to zero rows rather than fabricate — not crash, not guess.
    import ga_writers.ga_vargas_writer as _mod
    _mod._SHASHTIAMSHA_CACHE = None  # reset the module-level cache between calls
    floored_rows = _build_deity_rows(
        "test-chart-id", "lahiri_chitrapaksha", "test-build-id",
        60, "D60", {"Sun": {"sign_idx": 0, "degree_in_sign": 1.0}},
    )
    assert floored_rows == [], (
        "expected zero rows (honest floor) when bg_shashtiamsha_deities is unreachable, "
        f"got {floored_rows!r}"
    )


def test_saptavargaja_rows_stay_within_chart_divisionals_vocab():
    """The saptavargaja bala rows (M-18 fix) must emit a
    chart_divisionals-legal verification_pass_status."""
    import inspect
    from ga_writers import ga_vargas_writer as mod

    src = inspect.getsource(mod)
    # Structural guard: the specific literal this lane's fix landed on.
    assert '"verification_pass_status": "single"' in src, (
        "saptavargaja verification_pass_status fix (M-18/M-22) not found — "
        "regression risk: chart_divisionals only allows "
        f"{sorted(RESTRICTED_TABLE_VOCAB)}"
    )
    assert '"verification_pass_status": "documented_approximation"' not in src, (
        "ga_vargas_writer.py must never emit 'documented_approximation' — "
        "chart_divisionals' CHECK constraint does not allow it "
        "(psycopg.errors.CheckViolation on insert)"
    )


def test_ga_dashas_writer_verify_functions_never_return_chart_facts_only_tiers():
    """Estate-wide guard: every _verify_* function in ga_dashas_writer.py
    (all feed chart_dashas, which does NOT allow the chart_facts-only tiers
    'documented_approximation' / 'single_pass') must return a value inside
    RESTRICTED_TABLE_VOCAB for representative real inputs. Direct functional
    check (not a source-text grep) — exercises the actual return values."""
    from ga_writers import ga_dashas_writer as mod

    checks = [
        (mod._verify_mudda, [[], [{"level_n": 1, "lord_graha": "Ketu", "start_date": "1984-02-05"}]]),
        (
            mod._verify_kalachakra,
            [[], [{"level_n": 1, "lord_graha": mod.KALACHAKRA_SIGN_YEARS[0][0]}]],
        ),
        (mod._verify_yogini, [[{"level_n": 1, "lord_graha": mod.YOGINI_SEQUENCE[0][0]}]]),
        (mod._verify_ashtottari, [[], [{"level_n": 1, "lord_graha": mod.ASHTOTTARI_LORDS_ORDER[0]}]]),
        (mod._verify_chara, [[], [{"level_n": 1, "lord_graha": "Aries"}]]),
        (mod._verify_naisargika, [[{"level_n": 1, "lord_graha": mod.NAISARGIKA_SEQUENCE[0][0]}]]),
    ]
    for fn, arg_variants in checks:
        for args in arg_variants:
            result = fn(args)
            assert result in RESTRICTED_TABLE_VOCAB, (
                f"{fn.__name__}({args!r}) returned {result!r}, not in "
                f"chart_dashas' allowed vocabulary {sorted(RESTRICTED_TABLE_VOCAB)}"
            )
