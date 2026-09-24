"""Synergy-audit fixes: R-6 fields reach the table (#1); 29-Feb horizon (#3);
tz offset at the birth instant (#3); declared vedha edge (#7).

These are detectors for the gaps the synergy audit confirmed at sangam/stage3,
written so each can fail: the INSERT checks parse the writer's own SQL rather
than asserting a constant.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from pipeline.orchestrator.writers.ka_sangam import _add_years

WRITER = Path(__file__).resolve().parents[2] / 'pipeline' / 'orchestrator' / 'writers' / 'ka_sangam.py'
SEED = Path(__file__).resolve().parents[3] / 'scripts' / 'seed' / 'asset_registry_seed.ts'

KERNEL_COLUMNS = ['activity', 'valence', 'applicability',
                  'comparability_class', 'kernel_version', 'independence_group']


def _split_top_level(s: str):
    """Split on commas that are not inside parentheses — NOW() must stay one slot."""
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return out


def _insert_block() -> str:
    src = WRITER.read_text()
    i = src.index('INSERT INTO kala_convergence')
    return src[i:src.index('"""', i)]


class TestKernelFieldsReachTheTable:
    """Synergy audit #1 — separate_kernel()'s output was computed and discarded."""

    def test_all_six_kernel_columns_in_insert(self):
        block = _insert_block()
        missing = [c for c in KERNEL_COLUMNS if not re.search(rf'\b{c}\b', block)]
        assert not missing, f"INSERT does not persist: {missing}"

    def test_value_slot_count_matches_column_count(self):
        """Columns must equal VALUE SLOTS, counting SQL literals like NOW().

        Counting only `%s` is wrong here — `computed_at` is filled by NOW() — and
        getting that wrong is exactly the off-by-one this test exists to catch.
        """
        block = _insert_block()
        cols_part, values_part = block.split('VALUES', 1)
        cols = [c.strip() for c in _split_top_level(
            cols_part[cols_part.index('(') + 1:cols_part.rindex(')')]) if c.strip()]
        vals = [v.strip() for v in _split_top_level(
            values_part[values_part.index('(') + 1:values_part.rindex(')')]) if v.strip()]
        assert len(cols) == len(vals), (
            f"{len(cols)} columns vs {len(vals)} value slots — this INSERT would raise "
            "at runtime, which no test that never executes the SQL would catch.\n"
            f"columns={cols}\nvalues={vals}"
        )

    def test_kernel_version_is_persisted_not_only_in_memory(self):
        # The §4.5 never-pool rule needs kernel_version as a COLUMN; before the fix
        # it was set on the in-memory window and never written.
        assert re.search(r"w\.get\('kernel_version'\)", WRITER.read_text())


class TestHorizonLeapYear:
    """Synergy audit #3 — date(y+N, 2, 29) raises whenever y+N is not a leap year."""

    def test_feb_29_clamps_to_28(self):
        assert _add_years(date(2024, 2, 29), 7) == date(2031, 2, 28)

    def test_feb_29_to_leap_year_keeps_29(self):
        assert _add_years(date(2024, 2, 29), 4) == date(2028, 2, 29)

    def test_ordinary_date_unchanged(self):
        assert _add_years(date(2026, 9, 24), 7) == date(2033, 9, 24)

    def test_raw_constructor_would_have_crashed(self):
        # The defect this fix repairs, stated so the test explains itself.
        with pytest.raises(ValueError):
            date(2024 + 7, 2, 29)


class TestTimezoneOffsetAtBirthInstant:
    """Synergy audit #3 — the offset was taken at run time, not the birth instant."""

    def test_writer_resolves_a_birth_instant(self):
        src = WRITER.read_text()
        assert '_birth_instant_for_offset' in src
        assert re.search(r'utcoffset\(_at or datetime\.now\(\)\)', src), \
            "offset must be evaluated at the birth instant when one is available"

    def test_fallback_is_declared_not_silent(self):
        src = WRITER.read_text()
        i = src.index('_at = self._birth_instant_for_offset')
        assert 'logger.warning' in src[i:i + 900], \
            "falling back to run time must be logged, never silent (B.10)"


class TestDeclaredVedhaEdge:
    """Synergy audit #7 — the kala_vedha_gochara read was undeclared."""

    def test_vedha_declared_in_depends_on(self):
        t = SEED.read_text()
        i = t.index("asset_id: 'ka_sangam'")
        # Anchor on the DECLARATION, not the word: the surrounding comment mentions
        # `depends_on` too, and a loose search reads the comment instead of the code
        # — the same read-the-wrong-shape error this audit item came from.
        j = t.index('\n    depends_on: [', i)
        arr = re.findall(r"'([^']+)'", t[j:t.index(']', j)])
        assert 'ka_vedha_gochara' in arr, f"ka_sangam.depends_on = {arr}"

    def test_writer_actually_reads_that_relation(self):
        # The edge must be declared because the read exists — not the reverse.
        assert 'kala_vedha_gochara' in WRITER.read_text()
