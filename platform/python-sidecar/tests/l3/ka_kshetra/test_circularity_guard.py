"""
tests/l3/ka_kshetra/test_circularity_guard.py — ṢAḌ-DARŚANA W2 §8.3.

THE CIRCULARITY GUARD, stated exactly (design §8.3, CG-1):

    Let H(chart, corpus_pin, config_pin, weights_version, cohort_version) be the
    field CONTENT hash of §7.4 — the digest over the canonical serialization of
    every row written by stages 0–8 for that chart, excluding rows with
    lel_derived = TRUE and excluding the columns id / computed_at / created_at /
    released_at.

    For ANY mutation of that chart's lived-history corpus — insert, update, or
    delete of any life-event row — that leaves (corpus_pin, config_pin,
    weights_version, cohort_version) unchanged, H is BIT-IDENTICAL before and
    after.

This is a HARD, unsoftenable campaign gate — a peer of LAW ZERO, not a nice-to-
have. Its purpose is to make the instrument's claims falsifiable: if the field
could adjust itself in response to what already happened, then "the field
predicted this" would be unfalsifiable by construction and the published skill
score would be measuring the fitter's memory rather than the sky's information.

THREE INDEPENDENT HALVES IN THIS FILE, each catching what the others cannot:

  1. STATIC CENSUS — a textual scan over every `services/ka_kshetra/*` source and
     the orchestration shim. Catches the syntactic addition of a corpus read
     instantly, on every CI run, with no DB. Cheap and total.

  2. VACUITY CHECK (the §N.7/§N.8 half the design names explicitly) — the census
     is run against a deliberately-poisoned synthetic file and MUST report it.
     Without this, a census with a broken scanner would pass silently and the
     Guard would be a signal with no detector.

  3. DYNAMIC HASH INVARIANCE — two full writer builds whose fixture databases
     differ ONLY in their lived-history rows, asserting (a) the field content
     hash is bit-identical and (b) not one statement the writer issued mentions
     the corpus. (b) is what gives (a) teeth: without it, "the hash didn't move"
     would also be satisfied by a build that read the corpus and ignored it —
     which would be one refactor away from not ignoring it.

This test COMPLEMENTS `tests/l3/test_ka_jivana_parva_circularity_guard.py`, which
the W1 lane wrote against a proxy subject because `ka_kshetra` did not exist yet.
Its own docstring says: "THIS TEST MUST BE RE-POINTED AT `ka_kshetra` (or
`mi_bhara`'s weighted output) ONCE W2 LANDS." This file is the ka_kshetra-specific
half of that re-pointing; the W1 file's live-DB proof stays in place until the
field runs in production, so neither is deleted on a promise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import stage5_null as S5, writer as W  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402

_SIDECAR_ROOT = Path(__file__).resolve().parents[3]

#: Identifiers that would constitute a read of the lived-history corpus. Written
#: as fragments so this file can name what it forbids without itself containing a
#: token that the sibling repo-wide census (which scans `services/ka_*`
#: recursively, and would otherwise flag this very file) treats as a violation.
_FORBIDDEN_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ('life', 'events'),
    ('life', 'event_log'),
    ('lel', 'query'),
    ('mimamsa', 'lel'),
    ('standing', 'predictions'),
)


def _forbidden_tokens() -> list[str]:
    return [a + '_' + b for a, b in _FORBIDDEN_FRAGMENTS]


def _stage_path_sources() -> list[Path]:
    """Every source file on the stage 0–8 code path that Lane C ships."""
    files = sorted((_SIDECAR_ROOT / 'services' / 'ka_kshetra').glob('*.py'))
    shim = _SIDECAR_ROOT / 'pipeline' / 'orchestrator' / 'writers' / 'ka_kshetra.py'
    if shim.exists():
        files.append(shim)
    return files


def scan_for_corpus_reads(text: str) -> list[str]:
    """The census scanner, factored out so the vacuity check can exercise it."""
    lowered = text.lower()
    return [tok for tok in _forbidden_tokens() if tok in lowered]


# ── half 1: the static census ────────────────────────────────────────────────

class TestStaticCensus:
    def test_no_ka_kshetra_source_references_the_lived_history_corpus(self):
        offenders: dict[str, list[str]] = {}
        for path in _stage_path_sources():
            hits = scan_for_corpus_reads(path.read_text(encoding='utf-8'))
            if hits:
                offenders[str(path.relative_to(_SIDECAR_ROOT))] = hits
        assert not offenders, (
            'CIRCULARITY GUARD VIOLATION (§8.3, CG-1): stage 0–8 source references the '
            f'lived-history corpus: {offenders}. Only stage 9 (mi_bhara) may see lived '
            'outcomes. If a genuinely new stage-9-adjacent module needs the corpus, it '
            'does NOT belong on this code path.'
        )

    def test_the_census_actually_covers_the_shipped_modules(self):
        # A census over an empty file list would pass trivially. This asserts the
        # scanner is pointed at real, present files — the §N.8 "does the detector
        # measure the claim" question applied to the detector's own input.
        names = {p.name for p in _stage_path_sources()}
        for required in ('hazard.py', 'integrator.py', 'stage4_field.py',
                         'stage5_null.py', 'writer.py', 'ka_kshetra.py'):
            assert required in names, f'census missed {required}'

    def test_no_transitive_import_of_a_corpus_module(self):
        # The static scan is textual; this one is structural. Every module the
        # stage 0–8 path imports from within this repo is itself scanned, so a
        # read hidden one indirection away is still caught.
        import importlib
        from types import ModuleType

        seen: set[str] = set()
        frontier = ['services.ka_kshetra.writer']
        while frontier:
            name = frontier.pop()
            # Scoped to the package Lane C ships. The orchestrator's own modules
            # are outside this lane's ownership and are covered by the repo-wide
            # census in tests/l3/test_ka_jivana_parva_circularity_guard.py.
            if name in seen or not name.startswith('services.ka_kshetra'):
                continue
            seen.add(name)
            module = importlib.import_module(name)
            source_file = getattr(module, '__file__', None)
            if source_file:
                hits = scan_for_corpus_reads(Path(source_file).read_text(encoding='utf-8'))
                assert not hits, f'CIRCULARITY GUARD: {name} references {hits}'
            for attr in vars(module).values():
                # Both edges matter: `import x as y` binds a ModuleType, while
                # `from x import f` binds an object carrying `__module__`.
                # Following only one of the two leaves a real blind spot.
                if isinstance(attr, ModuleType):
                    frontier.append(attr.__name__)
                mod_name = getattr(attr, '__module__', None)
                if isinstance(mod_name, str):
                    frontier.append(mod_name)
        for required in ('services.ka_kshetra.stage4_field',
                         'services.ka_kshetra.stage5_null',
                         'services.ka_kshetra.hazard',
                         'services.ka_kshetra.integrator',
                         'services.ka_kshetra.contracts'):
            assert required in seen, f'traversal never reached {required}'


# ── half 2: the vacuity check (§N.7 item 4 / §N.8) ──────────────────────────

class TestCensusHasPower:
    @pytest.mark.parametrize('token', _forbidden_tokens())
    def test_the_scanner_reports_a_poisoned_source(self, token):
        poisoned = f'''"""a synthetic module."""\ndef f(conn):\n    conn.execute("SELECT 1 FROM {token}")\n'''
        assert scan_for_corpus_reads(poisoned) == [token]

    def test_the_scanner_does_not_fire_on_innocuous_prose(self):
        # A guard that flags the word "life" would be turned off within a week.
        clean = '"""The field never consults lived history; only stage 9 does."""\n'
        assert scan_for_corpus_reads(clean) == []

    def test_a_poisoned_file_would_fail_the_census_assertion(self, tmp_path):
        # Runs the census's own assertion shape over a directory containing a
        # violation, proving the assertion — not merely the scanner — has power.
        bad = tmp_path / 'stage_x.py'
        bad.write_text('q = "SELECT * FROM life_events"\n', encoding='utf-8')
        offenders = {p.name: scan_for_corpus_reads(p.read_text())
                     for p in tmp_path.glob('*.py')}
        offenders = {k: v for k, v in offenders.items() if v}
        with pytest.raises(AssertionError):
            assert not offenders, f'CIRCULARITY GUARD VIOLATION: {offenders}'


# ── half 3: dynamic hash invariance under corpus mutation ───────────────────

class TestDynamicInvariance:
    @staticmethod
    def _build(monkeypatch, life_event_rows: int):
        monkeypatch.setattr(W, 'HORIZON_DAYS', 400.0)
        monkeypatch.setattr(S5, 'DEFAULT_REPLICATES', 8)
        monkeypatch.setattr(S5, 'DEFAULT_BLOCK_SIZE', 4)
        conn = FakeConn(F.build_tables(life_event_rows=life_event_rows))
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        for step in writer.plan_substeps(ctx):
            writer.run_substep(ctx, step)
        return conn

    def test_CG1_field_content_hash_is_invariant_under_corpus_mutation(self, monkeypatch):
        before = self._build(monkeypatch, life_event_rows=0)
        after = self._build(monkeypatch, life_event_rows=37)
        h0 = before.tables['kala_field_snapshots'][0]['field_content_hash']
        h1 = after.tables['kala_field_snapshots'][0]['field_content_hash']
        assert h0 == h1, (
            'CIRCULARITY GUARD VIOLATION (CG-1): the field content hash moved when the '
            'chart\'s lived-history corpus changed, with every pin held fixed. The field '
            'is meant to be a pure function of (chart, corpus_pin, config_pin, '
            'weights_version, cohort_version).'
        )

    def test_the_mutation_is_real_so_the_invariance_is_not_vacuous(self, monkeypatch):
        # If the two fixtures were identical, the assertion above would hold for
        # a reason having nothing to do with the Guard.
        a = F.build_tables(life_event_rows=0)
        b = F.build_tables(life_event_rows=37)
        differing = [k for k in a if a[k] != b.get(k)]
        assert differing, 'the two fixture databases must genuinely differ'
        assert all(len(b[k]) != len(a[k]) for k in differing)

    def test_not_one_statement_the_writer_issued_mentions_the_corpus(self, monkeypatch):
        # THE HALF THAT GIVES THE HASH ASSERTION TEETH. A build that READ the
        # corpus and happened not to use it would still produce an invariant
        # hash — and would be one refactor away from not being invariant.
        conn = self._build(monkeypatch, life_event_rows=37)
        assert conn.executed, 'the build must have issued SQL at all'
        for stmt in conn.executed:
            hits = scan_for_corpus_reads(stmt)
            assert not hits, (
                f'CIRCULARITY GUARD VIOLATION: the writer issued a statement referencing '
                f'{hits}:\n{stmt[:300]}')

    def test_the_fixture_corpus_table_exists_so_a_read_would_have_succeeded(self, monkeypatch):
        # The Guard must not pass merely because a read would have errored. The
        # fixture DB genuinely holds the rows; the writer simply never asks.
        conn = self._build(monkeypatch, life_event_rows=37)
        assert len(conn.tables['lived_history_fixture']) == 37

    def test_the_field_DOES_move_when_a_legitimate_pin_moves(self, monkeypatch):
        # The complementary half: the hash must be SENSITIVE to the things it is
        # supposed to depend on. An always-constant hash would satisfy CG-1 and
        # be worthless.
        monkeypatch.setattr(W, 'HORIZON_DAYS', 400.0)
        monkeypatch.setattr(S5, 'DEFAULT_REPLICATES', 8)
        monkeypatch.setattr(S5, 'DEFAULT_BLOCK_SIZE', 4)
        base = self._build(monkeypatch, life_event_rows=0)
        tables = F.build_tables()
        tables['kala_field_weight_versions'][0]['version_id'] = 'v1_fitted'
        for row in tables['kala_field_weights']:
            row['version_id'] = 'v1_fitted'
        conn = FakeConn(tables)
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        for step in writer.plan_substeps(ctx):
            writer.run_substep(ctx, step)
        assert (base.tables['kala_field_snapshots'][0]['field_content_hash']
                != conn.tables['kala_field_snapshots'][0]['field_content_hash'])
