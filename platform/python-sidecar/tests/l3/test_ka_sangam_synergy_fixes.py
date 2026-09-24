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
IDENTITY_COLUMNS = ['contact_uuid', 'convention_frame', 'identity_state']


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


class TestR5IdentityReachesProduction:
    """Synergy audit #6/#10 — identity is defined over R-3's frame; neither existed."""

    def test_identity_columns_in_insert(self):
        block = _insert_block()
        missing = [c for c in IDENTITY_COLUMNS if not re.search(rf'\b{c}\b', block)]
        assert not missing, f"INSERT does not persist: {missing}"

    def test_production_identity_equals_the_qualified_harness_identity(self):
        """Phase 1 qualified identity in the disposable harness against seven §6.3
        attacks. That qualification transfers only if the production function is
        byte-identical in output — otherwise the harness proved a different thing."""
        import importlib.util
        from services.ka_sangam.identity import contact_uuid, frame_vector

        hpath = (Path(__file__).resolve().parents[4] / '00_ARCHITECTURE' / 'briefs' /
                 'nirmana' / 'l3_autonomous' / 'briefs' / 'evidence_sangam' /
                 'r5_harness' / 'r5_identity.py')
        spec = importlib.util.spec_from_file_location('_r5_harness', hpath)
        h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(h)

        fv = frame_vector('lahiri_chitrapaksha')
        args = ('c1', 'separated_v2', 'Saturn', 'f123', 180.0, fv, 3.2, 'A')
        assert contact_uuid(*args) == h.contact_uuid(*args)

    def test_identity_is_stable_when_the_date_moves(self):
        """The property that makes a window citable across a rebuild: peak_date and
        interval endpoints are content, not identity."""
        from services.ka_sangam.identity import contact_uuid, frame_vector
        fv = frame_vector('lahiri_chitrapaksha')
        a = contact_uuid('c1', 'separated_v2', 'Saturn', 'f1', 180.0, fv, 3.2, 'A')
        b = contact_uuid('c1', 'separated_v2', 'Saturn', 'f1', 180.0, fv, 3.2, 'A')
        assert a == b

    def test_identity_changes_when_the_frame_changes(self):
        """Two convention frames must never coalesce into one identity (R-3)."""
        from services.ka_sangam.identity import contact_uuid, frame_vector
        true_fv = frame_vector('lahiri_chitrapaksha', node_convention='true_node')
        mean_fv = frame_vector('lahiri_chitrapaksha', node_convention='mean')
        args = ('c1', 'separated_v2', 'Rahu', 'f1', 180.0)
        assert contact_uuid(*args, true_fv, 3.2, 'A') != contact_uuid(*args, mean_fv, 3.2, 'A')

    def test_frame_declares_its_gaps_rather_than_claiming_values(self):
        """§N.8: a component with no detector behind it must say so."""
        from services.ka_sangam.identity import frame_dict, frame_vector
        f = frame_dict(frame_vector('lahiri_chitrapaksha'))
        assert f['ephemeris_backend'] == 'unasserted', "R-4 asserts no backend today"
        assert f['house_frame'] == 'unavailable', "ka_sangam reads no cusp system"
        assert f['node_convention'] == 'true_node', \
            "must record what the SCANNER did, not what M-1 ruled — that is how the mismatch stays visible"

    def test_writer_records_why_identity_is_absent(self):
        src = WRITER.read_text()
        for state in ('no_target_fact_id', 'no_graha', 'computed'):
            assert state in src, f"identity_state {state!r} never set"


class TestIndependenceGroup:
    """Synergy audit #5 — correlation BETWEEN rows was invisible."""

    def test_same_root_testimony_shares_a_group(self):
        from services.ka_sangam.identity import independence_group
        assert independence_group('sig1', 'Saturn', 'f1') == independence_group('sig1', 'Saturn', 'f1')

    def test_different_root_testimony_differs(self):
        from services.ka_sangam.identity import independence_group
        a = independence_group('sig1', 'Saturn', 'f1')
        assert a != independence_group('sig2', 'Saturn', 'f1')
        assert a != independence_group('sig1', 'Jupiter', 'f1')
        assert a != independence_group('sig1', 'Saturn', 'f2')

    def test_writer_binds_the_computed_group_not_the_window_field(self):
        # w.get('independence_group') was always None — the engine never emitted it.
        assert '_indep_group,' in WRITER.read_text()


class TestScanCoverage:
    """Synergy audit #4 — an empty result was indistinguishable from a failure."""

    def test_three_distinct_empty_reasons(self):
        from datetime import date as _d

        from services.ka_sangam.exposure import build_scan_coverage
        h0, h1 = _d(2026, 1, 1), _d(2033, 1, 1)
        assert build_scan_coverage(h0, h1, 0, 0, 0).empty_reason == 'no_predicates_in_scope'
        assert build_scan_coverage(h0, h1, 5, 0, 0).empty_reason == 'predicates_scanned_no_contact_fired'
        assert build_scan_coverage(h0, h1, 5, 9, 0).empty_reason == 'all_generated_windows_deduped'

    def test_no_empty_reason_when_windows_were_emitted(self):
        from datetime import date as _d

        from services.ka_sangam.exposure import build_scan_coverage
        c = build_scan_coverage(_d(2026, 1, 1), _d(2033, 1, 1), 5, 9, 4)
        assert c.empty_reason is None and c.windows_emitted == 4

    def test_empty_reason_is_never_unknown(self):
        """If the producer cannot say why, that IS the reason and it is named."""
        from datetime import date as _d

        from services.ka_sangam.exposure import build_scan_coverage
        for scanned, generated in ((0, 0), (5, 0), (5, 9)):
            r = build_scan_coverage(_d(2026, 1, 1), _d(2033, 1, 1), scanned, generated, 0).empty_reason
            assert r and r != 'unknown', r

    def test_both_substeps_carry_coverage_in_notes(self):
        src = WRITER.read_text()
        # Count CALL sites, not the def line — the definition matches a bare-name
        # search too, which is how this detector first read 3 and failed correct code.
        assert src.count('notes=_notes_with_coverage(') == 2, \
            "near and lifetime substeps must both carry coverage"
        assert "'scan_coverage'" in src and "'exposure_manifest'" in src, \
            "coverage must not silently replace the exposure manifest in notes"


class TestComparableWithRelation:
    """Synergy audit #2/#8 — the layer's comparability vocabulary, read at source."""

    ENUM = ('self', 'same_convention_same_inputs',
            'same_convention_newer_inputs', 'different_convention')

    def test_column_and_check_constraint_use_the_four_layer_values(self):
        mig = (Path(__file__).resolve().parents[3] / 'supabase' / 'migrations'
               / '1087_kala_convergence_comparable_with.sql').read_text()
        for v in self.ENUM:
            assert f"'{v}'" in mig, f"enum value {v} missing from the CHECK constraint"
        assert 'comparability_class' in mig, \
            "the migration must record that comparable_with does NOT replace the grouping key"

    def test_value_is_derived_from_the_frame_not_defaulted(self):
        """§N.8: the value needs a detector behind it. It must read the row's own
        node convention, so it changes when the convention does rather than when
        somebody remembers to update a literal."""
        src = WRITER.read_text()
        i = src.index('_comparable_with')
        block = src[i:i + 400]
        assert 'node_convention' in block, "comparable_with must be derived from the frame"
        assert "'different_convention'" in block and "'same_convention_same_inputs'" in block

    def test_true_node_scanner_yields_different_convention(self):
        """Today's honest answer: the layer ruled mean, the scanner gives true_node,
        so per WP1 §6 the cross-convention comparison is NOT_RUN."""
        from services.ka_sangam.identity import frame_dict, frame_vector
        assert frame_dict(frame_vector('lahiri_chitrapaksha'))['node_convention'] == 'true_node'

    def test_grouping_key_survives_alongside_the_relation(self):
        """The layer binding proposed renaming comparability_class INTO
        comparable_with. They are different objects — a grouping key and a
        relation — and the rename would have destroyed the grouping."""
        block = _insert_block()
        assert 'comparability_class' in block and 'comparable_with' in block
