---
artifact: CLAUDECODE_BRIEF_L0_PHASE_BETA_v1_0
canonical_id: L0_PHASE_BETA_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahma Jñāna build — Phase β (writer infrastructure + bg_reference + bg_ontology)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v1_0.md
predecessor: Phase α — SEALED via PR #225 (12 assets registered, 14 tables provisioned)
branch: feature/l0-phase-beta
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0Beta (pre-create with `git worktree add`)
estimated_sessions: 3-4
estimated_time: 4-6 hours total
llm_cost: $0 (no LLM use; embeddings deferred to Phase δ)
---

# L0 Phase β — Writer Infrastructure + bg_reference + bg_ontology

> **Scope discipline:** Phase β has TWO deliverables: (1) the writer registration infrastructure that's been spec'd but doesn't exist in code; (2) the first two writers that prove the pattern (bg_reference + bg_ontology). Nothing more. Phase γ (yogas/dashas/doshas) comes after Phase β closes via Vimarśaka-β. ZERO LLM. ZERO embeddings (Phase δ adds those for bg_texts).

## §0 — Pre-read (mandatory before opening the worktree)

1. `00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md` (v1.1) — design rules + asset semantics
2. `00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v1_0.md` — multi-phase context
3. Phase α brief `CLAUDECODE_BRIEF_L0_PHASE_ALPHA_v1_0.md` — what's already in place
4. Memory `[[pyjhora-is-the-engine]]` and `[[deterministic-first-for-data-build]]`
5. Memory `[[feedback-pr-quality-gate-is-not-a-merge]]` — verify every PR claim via `gh pr view --json mergeCommit`

## §1 — Background: what's broken vs what's in place

**Cockpit "Build" on bg_texts errors with "no writer registered" because:**

- Phase α completed the SCHEMA (14 tables, 12 asset_registry rows, cockpit tiles)
- The WRITER LAYER (`pipeline/orchestrator/writers/`) has only `__init__.py` and tests
- No `@register('bg_texts')` decorator exists; no actual writer module exists; auto-discovery has nothing to discover
- Orchestrator processes builds correctly but every asset reports "no writer registered" because the registry is empty

**Phase β fixes both halves:**
1. Build the writer registration infrastructure (the @register decorator + auto-discovery + base class)
2. Author the first two writers as proof: bg_reference (smallest; 5 typed tables; ~88 rows) and bg_ontology (larger; ~700+ entries)

## §2 — Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune

# Verify current state
git checkout main
git pull --ff-only origin main
git log --oneline -3
# Expect db6cc7f3 or later (cockpit polish round merged)

# Pre-create the worktree
git worktree add -b feature/l0-phase-beta /Users/Dev/Vibe-Coding/Apps/MadhavL0Beta main

cd /Users/Dev/Vibe-Coding/Apps/MadhavL0Beta
git log --oneline -3  # confirm on main HEAD

# DB proxy
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_beta.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }

# Confirm Phase α state
psql_prod -c "SELECT count(*) FROM asset_registry WHERE layer='brahmagyan'"  # expect 12
psql_prod -c "SELECT to_regclass('brahma_ontology'), to_regclass('reference_planets')"  # both should resolve
```

**CHECKPOINT setup:** worktree on `feature/l0-phase-beta`; DB proxy live; Phase α state confirmed (12 assets registered, target tables exist).

## §3 — Step 1: Writer infrastructure

### §3.1 — Inspect what exists

```bash
ls platform/python-sidecar/pipeline/orchestrator/writers/ 2>&1
# Expect: __init__.py + maybe a tests/ dir
cat platform/python-sidecar/pipeline/orchestrator/writers/__init__.py 2>&1 | head -50
```

**CHECKPOINT 3.1:** confirm the directory is essentially empty (just `__init__.py` + tests, no actual writers). If there are existing writer modules, STOP and read them first — Phase β should EXTEND not replace.

### §3.2 — Author the registration substrate

Create or replace `platform/python-sidecar/pipeline/orchestrator/writers/__init__.py`:

```python
"""
L0 Brahma Jñāna writer registry — Phase β infrastructure.

Each writer module under this package registers itself via @register('bg_<id>').
The orchestrator imports this package and discovers all registered writers.

Per holistic design v1.1: ZERO LLM use in writers. Embeddings (Vertex AI) are
permitted as deterministic transforms for bg_texts in Phase δ; not used elsewhere.
"""
from __future__ import annotations
import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class ContextSpec:
    """Runtime context passed to every writer's run() method."""
    asset_id: str                              # e.g. 'bg_reference'
    build_id: str                              # unique per-build UUID for provenance
    db_conn: Any                               # psycopg connection (caller-owned; writer doesn't close)
    config: dict[str, Any] = field(default_factory=dict)  # writer-specific config (e.g. chart_id for per_chart writers; empty for global)
    dry_run: bool = False                      # if True, writer reports what it WOULD do but doesn't INSERT/UPDATE


@dataclass
class WriterResult:
    """What a writer returns after run()."""
    asset_id: str
    rows_inserted: int
    rows_updated: int = 0
    rows_skipped: int = 0
    duration_seconds: float = 0.0
    notes: str = ''


class WriterBase:
    """
    Base class for all L0 Brahma Jñāna writers.

    Subclasses MUST:
    - set class attribute `asset_id` (matches asset_registry.asset_id)
    - implement run(ctx: ContextSpec) -> WriterResult

    Subclasses SHOULD:
    - be deterministic (same input + same source = same output rows + same content hashes)
    - use INSERT ... ON CONFLICT DO NOTHING (or DO UPDATE) for idempotency
    - validate FK references to bg_ontology before insertion
    - log progress at INFO level every ~100-1000 rows
    """
    asset_id: str = ''  # subclass overrides

    def run(self, ctx: ContextSpec) -> WriterResult:
        raise NotImplementedError(f'{self.__class__.__name__} must implement run()')


# Registry: asset_id → writer class
_REGISTRY: dict[str, type[WriterBase]] = {}


def register(asset_id: str) -> Callable[[type[WriterBase]], type[WriterBase]]:
    """
    Decorator: register a writer class for an asset_id.

    Usage:
        @register('bg_reference')
        class ReferenceWriter(WriterBase):
            asset_id = 'bg_reference'
            def run(self, ctx): ...
    """
    def _decorate(cls: type[WriterBase]) -> type[WriterBase]:
        if asset_id in _REGISTRY:
            raise ValueError(f'duplicate writer registration for asset_id={asset_id}: '
                             f'existing={_REGISTRY[asset_id].__name__}, new={cls.__name__}')
        if not issubclass(cls, WriterBase):
            raise TypeError(f'{cls.__name__} must subclass WriterBase')
        _REGISTRY[asset_id] = cls
        logger.info(f'registered writer: {asset_id} → {cls.__name__}')
        return cls
    return _decorate


def get_writer(asset_id: str) -> type[WriterBase] | None:
    """Return the registered writer class for an asset_id, or None."""
    return _REGISTRY.get(asset_id)


def list_writers() -> dict[str, type[WriterBase]]:
    """Return a shallow copy of the registry (caller can iterate safely)."""
    return dict(_REGISTRY)


def discover_all() -> None:
    """
    Auto-discover and import all writer modules in this package.
    Called once at orchestrator startup; idempotent.
    """
    import sys
    # Import this module's package
    pkg_name = __name__
    pkg = sys.modules[pkg_name]
    for finder, mod_name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if mod_name.startswith('_') or mod_name == 'tests':
            continue
        full_name = f'{pkg_name}.{mod_name}'
        try:
            importlib.import_module(full_name)
            logger.debug(f'discovered writer module: {full_name}')
        except Exception as e:
            logger.error(f'failed to import writer {full_name}: {e}')
            raise  # hard-fail — registration gap is not silently OK


__all__ = ['ContextSpec', 'WriterResult', 'WriterBase', 'register', 'get_writer', 'list_writers', 'discover_all']
```

### §3.3 — Wire into orchestrator

Find where the orchestrator currently looks up writers (search for "no writer registered" error string):

```bash
grep -rn "no writer registered" platform/python-sidecar/pipeline 2>&1 | head -5
```

Once found, replace the lookup logic with:

```python
from pipeline.orchestrator.writers import discover_all, get_writer

# At orchestrator startup (once):
discover_all()

# When processing a build:
writer_cls = get_writer(asset_id)
if writer_cls is None:
    raise RuntimeError(f'no writer registered for asset_id={asset_id} — '
                       f'check pipeline/orchestrator/writers/ for the writer module')
writer = writer_cls()
result = writer.run(ContextSpec(asset_id=asset_id, build_id=build_id, db_conn=conn))
```

**CHECKPOINT 3.3:** orchestrator imports the writer registry; existing build flow still works for assets that DO have writers; assets without writers fail explicitly (not silently). Run any existing orchestrator tests to confirm nothing broke.

### §3.4 — Unit tests for the registration substrate

Create `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_registry.py`:

```python
import pytest
from pipeline.orchestrator.writers import (
    register, get_writer, list_writers, WriterBase, ContextSpec, WriterResult,
)


def test_register_and_get():
    @register('test_asset_1')
    class TestWriter(WriterBase):
        asset_id = 'test_asset_1'
        def run(self, ctx): return WriterResult(asset_id=self.asset_id, rows_inserted=0)
    assert get_writer('test_asset_1') is TestWriter


def test_duplicate_raises():
    @register('test_asset_dup')
    class A(WriterBase):
        asset_id = 'test_asset_dup'
        def run(self, ctx): return WriterResult(asset_id=self.asset_id, rows_inserted=0)
    with pytest.raises(ValueError, match='duplicate'):
        @register('test_asset_dup')
        class B(WriterBase):
            asset_id = 'test_asset_dup'
            def run(self, ctx): return WriterResult(asset_id=self.asset_id, rows_inserted=0)


def test_writer_must_subclass_base():
    with pytest.raises(TypeError):
        @register('bad_writer')
        class NotAWriter:  # noqa
            asset_id = 'bad_writer'
```

```bash
cd platform/python-sidecar
python -m pytest pipeline/orchestrator/writers/tests/test_registry.py -v
```

**CHECKPOINT 3.4:** all registration tests pass.

## §4 — Step 2: bg_reference writer

### §4.1 — Author the writer

Create `platform/python-sidecar/pipeline/orchestrator/writers/bg_reference.py`:

```python
"""
bg_reference writer — populates the 5 typed reference tables.

Sources (all classical, public domain):
- reference_planets:    BPHS Ch.3 (Grahana-svarupa) + Ch.4 (Graha-mitra)
- reference_nakshatras: BPHS Ch.4 + Taittiriya Aranyaka
- reference_signs:      BPHS Ch.6 (Rasi-svarupa)
- reference_aspects:    BPHS Ch.26 (Drishti-phala)
- reference_vargas:     BPHS Ch.7 (Shodasha-varga)

Deterministic: hardcoded Python data; rerunning produces identical rows.
INSERT ... ON CONFLICT DO NOTHING for idempotency.

Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# Source data: extract the same constants that Phase α's l0_reference.py defined for the 5 tables.
# If l0_reference.py already lives at platform/python-sidecar/brahmagyan/l0_reference.py,
# IMPORT FROM IT rather than duplicating the data.
from brahmagyan.l0_reference import PLANETS, NAKSHATRAS, SIGNS, ASPECTS, VARGAS


@register('bg_reference')
class ReferenceWriter(WriterBase):
    asset_id = 'bg_reference'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        cur = ctx.db_conn.cursor()
        inserted = 0

        # reference_planets
        for p in PLANETS:
            cur.execute("""
                INSERT INTO reference_planets (
                  planet_id, canonical_name_en, canonical_name_sa,
                  exaltation_sign, exaltation_degree,
                  debilitation_sign, mooltrikona_sign,
                  own_signs, natural_benefic, karak_domains,
                  dasha_years, source_citation
                ) VALUES (
                  %(planet_id)s, %(canonical_name_en)s, %(canonical_name_sa)s,
                  %(exaltation_sign)s, %(exaltation_degree)s,
                  %(debilitation_sign)s, %(mooltrikona_sign)s,
                  %(own_signs)s, %(natural_benefic)s, %(karak_domains)s,
                  %(dasha_years)s, %(source_citation)s
                )
                ON CONFLICT (planet_id) DO NOTHING
            """, p)
            if cur.rowcount > 0:
                inserted += 1

        # reference_nakshatras
        for n in NAKSHATRAS:
            cur.execute("""
                INSERT INTO reference_nakshatras (
                  nakshatra_id, canonical_name_sa, deity, ruler,
                  pada_lords, nature, guna, source_citation
                ) VALUES (
                  %(nakshatra_id)s, %(canonical_name_sa)s, %(deity)s, %(ruler)s,
                  %(pada_lords)s, %(nature)s, %(guna)s, %(source_citation)s
                )
                ON CONFLICT (nakshatra_id) DO NOTHING
            """, n)
            if cur.rowcount > 0:
                inserted += 1

        # reference_signs
        for s in SIGNS:
            cur.execute("""
                INSERT INTO reference_signs (
                  sign_id, canonical_name_en, canonical_name_sa,
                  element, mode, lord, source_citation
                ) VALUES (
                  %(sign_id)s, %(canonical_name_en)s, %(canonical_name_sa)s,
                  %(element)s, %(mode)s, %(lord)s, %(source_citation)s
                )
                ON CONFLICT (sign_id) DO NOTHING
            """, s)
            if cur.rowcount > 0:
                inserted += 1

        # reference_aspects
        for a in ASPECTS:
            cur.execute("""
                INSERT INTO reference_aspects (
                  aspect_type, aspecting_planet, aspect_houses, source_citation
                ) VALUES (
                  %(aspect_type)s, %(aspecting_planet)s, %(aspect_houses)s, %(source_citation)s
                )
                ON CONFLICT (aspect_type, aspecting_planet) DO NOTHING
            """, a)
            if cur.rowcount > 0:
                inserted += 1

        # reference_vargas
        for v in VARGAS:
            cur.execute("""
                INSERT INTO reference_vargas (
                  varga_id, canonical_name_sa, divisor, source_citation
                ) VALUES (
                  %(varga_id)s, %(canonical_name_sa)s, %(divisor)s, %(source_citation)s
                )
                ON CONFLICT (varga_id) DO NOTHING
            """, v)
            if cur.rowcount > 0:
                inserted += 1

        ctx.db_conn.commit()
        cur.close()

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=time.time() - t0,
            notes=f'5 reference tables (planets/nakshatras/signs/aspects/vargas); ON CONFLICT DO NOTHING for idempotency'
        )
```

**Key:** the writer IMPORTS the same data structures (PLANETS, NAKSHATRAS, etc.) that `platform/python-sidecar/brahmagyan/l0_reference.py` already defines (from Phase α work). This avoids data duplication. If those structures don't exist there or use different shapes, ADAPT the imports — but do NOT re-author the data.

**CHECKPOINT 4.1:** writer file authored; imports resolve; `python -c "from pipeline.orchestrator.writers.bg_reference import ReferenceWriter; print(ReferenceWriter.asset_id)"` prints `bg_reference`.

### §4.2 — Smoke test the writer in isolation

```bash
cd platform/python-sidecar
python <<'EOF'
import os, sys
sys.path.insert(0, '.')
import psycopg
from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec
import uuid

discover_all()
writer_cls = get_writer('bg_reference')
print(f'Writer class: {writer_cls.__name__}')

conn = psycopg.connect(os.environ['PROD_DB_URL'])
ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=conn)
writer = writer_cls()
result = writer.run(ctx)
print(f'Result: {result}')
conn.close()
EOF
```

**Hard AC:** result shows `rows_inserted` > 0 on first run. Re-run immediately → `rows_inserted` = 0 (idempotency proven).

### §4.3 — End-to-end via cockpit

Open `/clients/<native>/build`. Click "Build" on `bg_reference` (or trigger via API):

```bash
NATIVE_SESSION=$(npx tsx platform/scripts/mint_session_cookie.ts 2>/dev/null || cat /tmp/native_session)
curl -s -X POST -b "__session=$NATIVE_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","scope":"asset","scope_target":"bg_reference","action":"build"}' \
  https://madhav.marsys.in/api/cockpit/runs
```

Watch the cockpit: `bg_reference` should transition `dormant → building → lit` with row count appearing.

**Hard AC:** cockpit shows `bg_reference` LIT with ~88 rows; `asset_throughput.last_built_at` populated.

## §5 — Step 3: bg_ontology writer

### §5.1 — Author the writer

Create `platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py`:

```python
"""
bg_ontology writer — populates brahma_ontology with canonical entity vocabulary.

Per holistic design v1.1 §3.4: ontology stores names + synonyms + one-line typing
description ONLY. Doctrinal data goes to reference_* tables, not here.

Entity classes (~700-1000 total entries):
- planet (11): Sun/Moon/.../Rahu/Ketu + Lagna/MC
- nakshatra (27)
- sign (12)
- house (12)
- dasha_system (15-20): Vimshottari, Yogini, Chara, Kalachakra, etc.
- yoga (200-300): Gajakesari, Raja, Dhana, Pancha-Maha-Purusha, ...
- dosha (50-80): Manglik, Kala-sarpa, Kemadruma, ...
- karaka (60-100): Sthira karakas + Chara karakas (Jaimini)
- upagraha (8-11): Gulika, Mandi, Dhuma, ...
- domain (30-50): career, marriage, health + subdomains
- concept (100-200): Drishti types, Bhava, Hora, etc.
- aspect_type (10-15): parashari_7th, mars_4th, jupiter_5th, ...
- remedy_type (10-15): mantra, yantra, gemstone, charity, ...
- school (6-10): parashari, jaimini, kp, tajaka, lal-kitab
- text (15): BPHS, Phaladeepika, Jataka Parijata, ... (mirror bg_texts)

Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# Import existing data structures from brahmagyan/l0_ontology.py (Phase α).
# If they don't exist there, this module defines ENTITIES inline.
try:
    from brahmagyan.l0_ontology import ENTITIES
except ImportError:
    # Fallback: inline data. NOTE: subsequent phases expand this; for Phase β we ship the 11+27+12 base set
    # so cockpit shows lit + ontology resolvers work. Yogas/doshas/dashas/karakas etc. added in Phase γ + δ.
    ENTITIES = []
    # ... (see §5.2 for the inline data if l0_ontology.py is missing)


@register('bg_ontology')
class OntologyWriter(WriterBase):
    asset_id = 'bg_ontology'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        cur = ctx.db_conn.cursor()
        inserted = 0

        for entry in ENTITIES:
            # Defensive: every entry must have canonical_id + entity_class
            if not entry.get('canonical_id') or not entry.get('entity_class'):
                logger.warning(f'skipping malformed ontology entry: {entry}')
                continue

            cur.execute("""
                INSERT INTO brahma_ontology (
                  entity_class, canonical_id, canonical_name_en, canonical_name_sa,
                  synonyms, description, source_citation
                ) VALUES (
                  %(entity_class)s, %(canonical_id)s, %(canonical_name_en)s, %(canonical_name_sa)s,
                  %(synonyms)s, %(description)s, %(source_citation)s
                )
                ON CONFLICT (canonical_id) DO NOTHING
            """, entry)
            if cur.rowcount > 0:
                inserted += 1
                if inserted % 100 == 0:
                    logger.info(f'bg_ontology: inserted {inserted} so far...')

        ctx.db_conn.commit()
        cur.close()

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=time.time() - t0,
            notes='canonical entity vocabulary; deterministic; ON CONFLICT DO NOTHING'
        )
```

### §5.2 — If `brahmagyan/l0_ontology.py` doesn't exist or is incomplete

Author the data file `platform/python-sidecar/brahmagyan/l0_ontology.py` (or extend it). Phase β target: at MINIMUM the 11 planets + 27 nakshatras + 12 signs + 12 houses = 62 entries.

Source pattern per holistic design v1.1 §3.4: pure-Python list of dicts. Native or future phases extend with yogas/doshas/dashas/karakas.

Example seed entries (extend the existing l0_ontology.py if it has these):
```python
ENTITIES = [
  {
    'entity_class': 'planet', 'canonical_id': 'sun',
    'canonical_name_en': 'Sun', 'canonical_name_sa': 'Sūrya',
    'synonyms': ['surya', 'ravi', 'aditya', 'arka', 'bhaskar'],
    'description': 'The Sun graha; ātmakāraka in Jaimini; first of the navagrahas',
    'source_citation': 'BPHS Ch.3'
  },
  # ... rest of planets, nakshatras, signs, houses
]
```

**Phase β floor:** ≥62 entries. Phase γ/δ expand toward the ~700-1000 target as their content authoring proceeds.

### §5.3 — Smoke test bg_ontology

Same pattern as §4.2 — isolated Python invocation, then end-to-end via cockpit. Confirm cockpit shows `bg_ontology` LIT with ≥62 rows after build.

## §6 — Step 4: Tests for both writers

Author `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_reference.py`:

```python
import pytest, os
import psycopg
from pipeline.orchestrator.writers.bg_reference import ReferenceWriter
from pipeline.orchestrator.writers import ContextSpec
import uuid


@pytest.fixture
def db_conn():
    conn = psycopg.connect(os.environ['DATABASE_URL'])
    yield conn
    conn.rollback()
    conn.close()


def test_bg_reference_writer_runs(db_conn):
    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    assert result.asset_id == 'bg_reference'
    assert result.rows_inserted >= 0  # may be 0 on idempotent re-run


def test_bg_reference_writer_idempotent(db_conn):
    """Running twice should leave row counts identical (ON CONFLICT DO NOTHING)."""
    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    writer.run(ctx)
    cur = db_conn.cursor()
    cur.execute("SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) AS total")
    count_1 = cur.fetchone()[0]
    writer.run(ctx)
    cur.execute("SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) AS total")
    count_2 = cur.fetchone()[0]
    assert count_1 == count_2, f'idempotency broken: {count_1} != {count_2}'
```

Same pattern for `test_bg_ontology.py`.

```bash
cd platform/python-sidecar
DATABASE_URL=$PROD_DB_URL python -m pytest pipeline/orchestrator/writers/tests/ -v
```

**CHECKPOINT 6:** all tests pass against prod DB. Idempotency proven.

## §7 — Step 5: Vimarśaka-β review (autonomous, programmatic)

Author `platform/scripts/vimarsaka/vimarsaka_beta.py`:

```python
"""
Vimarśaka-β: 6 programmatic checks for Phase β acceptance.
Returns: APPROVE | REJECT_WITH_FEEDBACK
"""
import psycopg, os, sys
from hashlib import sha256


def check_writer_registration(conn):
    """Both bg_reference and bg_ontology writers must be registered."""
    sys.path.insert(0, 'platform/python-sidecar')
    from pipeline.orchestrator.writers import discover_all, get_writer
    discover_all()
    ok = bool(get_writer('bg_reference')) and bool(get_writer('bg_ontology'))
    return ok, f'bg_reference={bool(get_writer("bg_reference"))} bg_ontology={bool(get_writer("bg_ontology"))}'


def check_row_counts(conn):
    """bg_reference ≥88, bg_ontology ≥62."""
    cur = conn.cursor()
    cur.execute("SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas)")
    ref = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM brahma_ontology")
    ont = cur.fetchone()[0]
    ok = ref >= 88 and ont >= 62
    return ok, f'reference={ref}/88 ontology={ont}/62'


def check_source_citation_not_null(conn):
    """Every row has non-NULL source_citation."""
    cur = conn.cursor()
    failed = []
    for tbl in ['reference_planets', 'reference_nakshatras', 'reference_signs', 'reference_aspects', 'reference_vargas', 'brahma_ontology']:
        cur.execute(f"SELECT count(*) FROM {tbl} WHERE source_citation IS NULL")
        n = cur.fetchone()[0]
        if n > 0: failed.append(f'{tbl}={n}')
    return len(failed) == 0, f'null source_citation rows: {failed or "none"}'


def check_idempotent_rerun(conn):
    """Re-running each writer leaves row counts unchanged."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM brahma_ontology"); before = cur.fetchone()[0]
    sys.path.insert(0, 'platform/python-sidecar')
    from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec
    import uuid
    discover_all()
    ctx = ContextSpec(asset_id='bg_ontology', build_id=str(uuid.uuid4()), db_conn=conn)
    get_writer('bg_ontology')().run(ctx)
    cur.execute("SELECT count(*) FROM brahma_ontology"); after = cur.fetchone()[0]
    return before == after, f'before={before} after={after}'


def check_asset_throughput_updated(conn):
    """asset_throughput shows last_built_at populated for both assets after build."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM asset_throughput WHERE asset_id IN ('bg_reference','bg_ontology') AND last_built_at IS NOT NULL")
    n = cur.fetchone()[0]
    return n >= 2, f'last_built_at populated for {n}/2 assets'


def check_cockpit_displays_lit(conn):
    """asset_throughput state = lit for both assets."""
    cur = conn.cursor()
    cur.execute("SELECT asset_id, state FROM asset_throughput WHERE asset_id IN ('bg_reference','bg_ontology')")
    states = dict(cur.fetchall())
    ok = all(states.get(a) == 'lit' for a in ['bg_reference', 'bg_ontology'])
    return ok, f'states={states}'


CHECKS = [
    ('writer_registration', check_writer_registration),
    ('row_counts', check_row_counts),
    ('source_citation_not_null', check_source_citation_not_null),
    ('idempotent_rerun', check_idempotent_rerun),
    ('asset_throughput_updated', check_asset_throughput_updated),
    ('cockpit_displays_lit', check_cockpit_displays_lit),
]


def main():
    conn = psycopg.connect(os.environ['PROD_DB_URL'])
    passed = []; failed = []
    for name, fn in CHECKS:
        ok, msg = fn(conn)
        status = '✓ PASS' if ok else '✗ FAIL'
        print(f'{status}  {name}: {msg}')
        (passed if ok else failed).append(name)
    print(f'\nResult: {len(passed)}/{len(CHECKS)} PASS')
    if failed:
        print(f'FAIL: {failed}')
        sys.exit(1)
    print('SEAL: Phase β APPROVED')

if __name__ == '__main__':
    main()
```

```bash
python platform/scripts/vimarsaka/vimarsaka_beta.py
```

**CHECKPOINT 7:** 6/6 PASS. If any FAIL, HALT and report — do not commit Phase β until all pass.

## §8 — Step 6: Commit + push + PR

```bash
git add -A
git status
git commit -m "feat(l0/phase-beta): writer infrastructure + bg_reference + bg_ontology writers

Phase β of L0_BRAHMAGYAN_BUILD_MASTER. Per holistic design v1.1: ZERO LLM use.

Writer infrastructure:
- pipeline/orchestrator/writers/__init__.py: @register decorator, auto-discovery,
  WriterBase, ContextSpec, WriterResult dataclasses
- Orchestrator wired to discover_all() + get_writer() lookup

First two writers:
- bg_reference.py: 5 typed tables (planets/nakshatras/signs/aspects/vargas) ~88 rows
- bg_ontology.py: canonical entity vocab; Phase β floor 62 (planets+nakshatras+signs+houses);
  subsequent phases expand toward ~700-1000

Tests:
- test_registry.py: registration semantics + duplicate-rejection + subclass check
- test_bg_reference.py: idempotency proof
- test_bg_ontology.py: same pattern

Vimarśaka-β: 6/6 PASS (writer registration, row counts, source citation,
idempotent re-run, asset_throughput updated, cockpit displays lit).

Cockpit verification:
- bg_reference: lit, 88 rows
- bg_ontology: lit, ≥62 rows
- 'no writer registered' error eliminated for these 2 assets

Subsequent phases populate the remaining 10 L0 assets.

Parent design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md
Parent plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v1_0.md"

git push -u origin feature/l0-phase-beta

gh pr create --title "feat(l0/phase-beta): writer infrastructure + bg_reference + bg_ontology" \
  --body "Phase β of L0 Brahma Jñāna build. Writer registration substrate + first 2 writers (bg_reference + bg_ontology). ZERO LLM. Vimarśaka-β: 6/6 PASS.

Parent plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v1_0.md
Sub-brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0_PHASE_BETA_v1_0.md" \
  --base main --head feature/l0-phase-beta
```

## §9 — Post-merge verification

After PR merges (and you've VERIFIED the merge via `gh pr view N --json mergeCommit` per [[feedback-pr-quality-gate-is-not-a-merge]]):

```bash
# Confirm fresh Cloud Run revision
gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'

# Re-run Vimarśaka against prod
DATABASE_URL=$PROD_DB_URL python platform/scripts/vimarsaka/vimarsaka_beta.py
# Expect: 6/6 PASS

# Cockpit visual:
# - bg_reference shows LIT with ~88 rows
# - bg_ontology shows LIT with ≥62 rows
# - clicking 'Build' on either re-runs the writer (idempotent; rows unchanged)
```

## §10 — Hard stops

- §3.1 audit reveals UNEXPECTED writer modules already exist → STOP, read them first, integrate rather than replace
- §3.3 orchestrator wiring breaks existing test → STOP, investigate; do not push broken main
- §4.1 imports from `brahmagyan.l0_reference` fail → check the module path or fall back to inline data; halt to review
- §4.2 isolated smoke fails with FK or schema error → likely Phase α schema gap; cross-check `psql_prod -c "\d brahma_ontology"`; halt
- §4.3 cockpit build returns error other than "no writer registered" → orchestrator pathway has a different bug; investigate before declaring Phase β done
- §7 Vimarśaka fails any check → fix the gap before committing; don't ship a partial phase

## §11 — Out of scope (explicit non-action list)

- Embeddings (Phase δ)
- 10 missing texts (Phase δ)
- Yogas / dashas / doshas content (Phase γ)
- Rules / remedies expansion (Phase ε)
- Concordance / compendium (Phase ζ)
- The autonomous-rebuild proof (Phase η)
- Tier B branch cleanup (separate workstream)
- Brahma Jñāna data beyond the 62-row ontology floor (subsequent phases expand)

## §12 — Memory update after merge

Update `[[l0-phase-alpha-truly-sealed]]` with Phase β completion note. Add new memory `[[l0-phase-beta-sealed]]` with PR number + Vimarśaka-β results + writer infrastructure description.

Begin §2 setup.

---

*End of Phase β brief.*
