---
lane: F-78
stream: S3_SATYA (spec) -> S6_ADHARA (build)
stage: S (SPEC) — COMPLETE, awaiting REVIEW
author: SATYA sub-agent (sonnet)
routing_note: >
  F-78's mechanism lives in platform/python-sidecar/services/ka_kshetra/writer.py
  and stage4_field.py — an L3 Kāla service directory, not in any file S3's OWNS
  list (L4_phala/**, L5_mimamsa/**, ph_nimitta/**, muhurta.py) actually covers.
  Per conductor's ruling (see DIAGNOSIS.md §6), this SPEC is written by S3 but
  routes to S6 (ĀDHĀRA) to BUILD, under S6's lease extension covering
  services/ka_kshetra/** for this purpose. This document is written to be
  executed directly by an S6 builder with no access to the S3 conversation that
  produced it — every file path, function name, and diff below is concrete and
  independently verifiable against the lines cited.
---

# SPEC — F-78: `kala_field_snapshots.event_classes` conflates attempted with built

## Relationship to F-34 (CL-13 exemplar) — read this first

One of the five CL-13 siblings the plan (§2/§5) designates for exemplar-then-replicate: F-34
(`lanes/F-34/SPEC.md` §9) establishes the reviewed general shape — locate the surface's own
"what was actually delivered" signal, compare it to the full attempted/requested set, expose the
gap structurally. This finding's own shape is slightly different (attempted-vs-built at write
time, not requested-vs-served at read time, since — per §3/§7 below — there is currently no live
TS consumer to serve a comparison to), so the fix here is a schema/writer-level disclosure
(computed column + doc comment + recurrence-guard test) rather than a response-field addition like
F-34's. Stage R should take "structural disclosure over silent conflation" as settled by F-34 and
focus review on whether this document's narrower, dormant-column shape is the right adaptation.

## 0. Read first — the finding, verbatim (from `pp2-audit/manifest.json`, id F-78)

> kala_field_snapshots.event_classes for the second chart (1c826d5a) declares 27
> event classes, but only 6 (childbirth, foreign_settlement, marriage,
> relocation, separation, surgery) actually have rows in kala_field /
> kala_field_null. The remaining 21 are all present in the same row's
> skipped_classes array with reason 'no_class_prior_row' (honest-skip per
> require_baseline()/ClassSkipped in stage4_field.py) -- so this is NOT a
> silent data-loss bug, but event_classes conflates 'classes the writer
> attempted to build' with 'classes actually built', with no field-level
> comment distinguishing the two and no documented caller obligation to
> subtract skipped_classes before treating event_classes as the built set. No
> serving-layer TypeScript code currently reads
> kala_field_snapshots.event_classes (grep across platform/src and
> platform-mcp/src found zero consumers), so this is presently dormant rather
> than user-facing, but any future reader of this column risks misreporting
> build coverage.

Live reproduction confirmed exactly as claimed — see `DIAGNOSIS.md` §1
(`raw_reproduce.json` in this lane dir). This is a CL-13 disclosure defect,
naming/documentation-class, matching S3's charter.

## 1. Root-cause statement (mechanism-level)

`writer.py`'s `_run_snapshot` (`platform/python-sidecar/services/ka_kshetra/writer.py:1745-1761`)
writes `self._event_classes` — the full discovery-time candidate list produced by
`_discover_event_classes` (`:2186-2220`, assigned at `:285`) — unconditionally to
`kala_field_snapshots.event_classes` at `:1760`, without ever computing or
persisting the set-difference against `self._skipped` (populated by
`_record_skip` at `:1962-1970` on every `ClassSkipped` raised from
`stage4_field.py:734`); the column carries no `COMMENT ON COLUMN` (unlike its
sibling `skipped_classes`, commented at migration `492_kala_field_core.sql:207-210`)
stating that it is the *attempted* set rather than the *built* set; and the
subtraction the writer needs to answer "what did this snapshot actually build"
is performed twice, inline and only for the writer's own internal use
(`:1183`, `:1983`), never as a named, reusable, or persisted artifact — so any
future reader of this column has no canonical way to derive the built-only set
without independently re-deriving the same subtraction from scratch, which is
exactly the conflation risk the finding names.

## 2. Files to change

### 2a. `platform/python-sidecar/services/ka_kshetra/writer.py` — add the disclosure helper

**What:** add one new module-level pure function, `built_event_classes`, plus a
`Iterable`/`Mapping` import, and add nothing else — no change to `_run_snapshot`,
no new column, no change to `_run_snapshot`'s INSERT statement or its bound
parameters.

**Why here, not a new file:** this is where `self._event_classes` and
`self._skipped` already live and where the subtraction is already performed
twice for internal use (`:1183`, `:1983`). Putting the canonical definition
anywhere else would create a *third*, disconnected implementation of the same
subtraction — the opposite of the fix. A pure module-level function (not a
method) is required so a future caller with only a raw DB row (no live
`KaKshetraWriter` instance) can still call it: `from services.ka_kshetra.writer
import built_event_classes`.

**Diff 1 — import (`:97`):**

Current:
```python
from typing import Any, Optional
```
New:
```python
from typing import Any, Iterable, Mapping, Optional
```

**Diff 2 — new function, inserted between the existing constant block and
`class _ClassContext`** (current file: `_DAYS_PER_JULIAN_YEAR = 365.2425` ends
at line 201; `@dataclass` / `class _ClassContext` begins at line 204 — insert
the new block in the blank space between them, i.e. immediately after line 201):

```python
def built_event_classes(
    event_classes: Iterable[str], skipped_classes: Iterable[Mapping[str, str]],
) -> list[str]:
    """F-78 disclosure helper: the CLASSES-ACTUALLY-BUILT set, not the attempted set.

    `kala_field_snapshots.event_classes` is the discovery-time ATTEMPTED list —
    every class `_discover_event_classes` found a `bodha_pratijna` row for,
    regardless of whether stage 4/5 produced any `kala_field` rows for it (see
    that function's own docstring: "regardless of status"). `skipped_classes`
    records, honestly (LAW ZERO), every class from that attempted list the
    build could NOT produce rows for, and why. Neither column alone tells a
    caller which classes actually got `kala_field` rows written for this
    snapshot — that is this function's one job:
    `set(event_classes) - {skipped event_class values}`, sorted for
    determinism. A caller reading `kala_field_snapshots.event_classes` and
    treating it as "classes this snapshot covers" is the exact conflation
    F-78 named — call this function instead of subtracting the two columns
    ad hoc.
    """
    skipped_ids = {s['event_class'] for s in skipped_classes}
    return sorted(set(event_classes) - skipped_ids)
```

No existing call site (`:1183`, `:1983`) is touched by this spec — both are
membership checks (`ec in {...}`), not full built-set computations, and
rewriting them is unrelated cosmetic risk in a FROZEN-orchestrator writer that
this spec does not need to take on. (If S6's builder wants to dedupe those two
inline set-comprehensions against `built_event_classes` as a follow-on
cleanup, that is a separate, optional commit — NOT required for this spec's
exit test, and it must not touch `_run_snapshot`'s INSERT.)

### 2b. `platform/supabase/migrations/572_kala_field_snapshots_event_classes_disclosure.sql` — new migration, comment-only

**What:** a new, additive-only migration adding a `COMMENT ON COLUMN
kala_field_snapshots.event_classes` — no `ALTER TABLE`, no new column, no data
change. `572` is confirmed the next free migration number (`571_p3a_shape_only_tier.sql`
is the current highest at time of writing — S6 MUST re-verify this is still
true immediately before creating the file, per CLAUDE.md §N.4 "Surgical
migrations, verified").

**Why:** `kala_field_snapshots.skipped_classes` already carries a `COMMENT ON
COLUMN` (`492_kala_field_core.sql:207-210`) explaining LAW ZERO; `event_classes`
has none. A DB column comment is the discoverability surface a future
engineer or governance script sees FIRST (`\d+ kala_field_snapshots`, any
`information_schema.columns` introspection) — before they would ever find
`writer.py`'s docstrings. This closes the diagnosis's literal words: "no
field-level comment distinguishing the two."

**Exact file content:**

```sql
-- migration 572: F-78 disclosure — kala_field_snapshots.event_classes is the
-- ATTEMPTED set, not the BUILT set (PARIŚEṢA S3/CL-13, DIAGNOSIS.md F-78).
--
-- Comment-only, additive, non-destructive. Mirrors the existing
-- skipped_classes comment (492_kala_field_core.sql:207-210) so both columns
-- of the same disclosure pair are documented, not just one.
--
-- Rollback (non-destructive):
--   COMMENT ON COLUMN kala_field_snapshots.event_classes IS NULL;

COMMENT ON COLUMN kala_field_snapshots.event_classes IS
  'F-78 disclosure: the ATTEMPTED set, not the built set -- every event class '
  '_discover_event_classes() found a bodha_pratijna row for, regardless of '
  'whether stage 4/5 wrote any kala_field rows for it. A class present here '
  'AND in this row''s skipped_classes was NOT built (see that column''s own '
  'comment). To get the classes actually built for a snapshot, subtract: '
  'services.ka_kshetra.writer.built_event_classes(event_classes, '
  'skipped_classes). Never read this column alone as "classes covered."';
```

`COMMENT ON COLUMN` is naturally idempotent (re-running it just resets the same
text) — no `IF NOT EXISTS` / conditional guard needed, and none of the
`ON CONFLICT` idempotency machinery `§N.3` requires applies (no row is written).

### 2c. New test file — `platform/python-sidecar/tests/l3/ka_kshetra/test_event_classes_disclosure.py`

**What:** a new, dedicated test file (not appended to `test_writer.py`, so the
exit test and recurrence guard for this one finding are independently
runnable and reviewable). Uses the same `FakeConn`/`FakeCtx`/`fixtures`
harness every other `ka_kshetra` writer test uses — no live DB required.

**Why a new file, not appended to `test_writer.py`:** Stage S §3 requires
"the exact command/test... Name the file it lives in" — a dedicated file
makes the exit-test command unambiguous (`pytest
tests/l3/ka_kshetra/test_event_classes_disclosure.py`) without depending on
`test_writer.py`'s ~700 other assertions also passing.

**Exact file content:**

```python
"""
tests/l3/ka_kshetra/test_event_classes_disclosure.py — F-78 (PARIŚEṢA S3->S6):
kala_field_snapshots.event_classes is the ATTEMPTED set, not the BUILT set.

Exit test for F-78's SPEC.md. Before the fix: `services.ka_kshetra.writer` has
no `built_event_classes` function, so every test in TestBuiltEventClassesHelper
and TestHelperMatchesRealBuildOutput fails (AttributeError). After the fix:
the function exists, its output matches what the writer ACTUALLY wrote to
kala_field (not just its own self._skipped bookkeeping), and the disclosure
migration's COMMENT ON COLUMN exists and names both the conflation and the fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import writer as W  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402


def _run_full_build(tables) -> tuple[W.KaKshetraWriter, FakeConn]:
    conn = FakeConn(tables)
    ctx = FakeCtx(conn, F.CHART_ID)
    writer = W.KaKshetraWriter()
    for step in writer.plan_substeps(ctx):
        writer.run_substep(ctx, step)
    return writer, conn


# ── exit test: fails today (AttributeError — built_event_classes doesn't
# exist yet), passes once §2a lands ─────────────────────────────────────────

class TestBuiltEventClassesHelper:
    def test_helper_subtracts_skipped_from_attempted(self):
        attempted = ['marriage', 'career_change', 'surgery']
        skipped = [{'event_class': 'career_change', 'reason': 'no_class_prior_row',
                    'detail': 'no bg_class_priors lifetime-count row'}]
        assert W.built_event_classes(attempted, skipped) == ['marriage', 'surgery']

    def test_helper_is_order_independent_and_deduplicated(self):
        skipped = [{'event_class': 'b', 'reason': 'x', 'detail': 'x'}]
        assert W.built_event_classes(['b', 'a', 'a'], skipped) == ['a']

    def test_nothing_skipped_returns_the_full_attempted_set(self):
        assert (W.built_event_classes(['marriage', 'surgery'], [])
                == ['marriage', 'surgery'])

    def test_everything_skipped_returns_empty(self):
        skipped = [{'event_class': 'marriage', 'reason': 'r', 'detail': 'd'}]
        assert W.built_event_classes(['marriage'], skipped) == []


# ── recurrence guard (§3 element 5): ties the helper's answer to what the
# writer ACTUALLY wrote to kala_field, not just to its own self._skipped
# bookkeeping, so a future divergence between "attempted", "skipped", and
# "has real rows" fails this closed ─────────────────────────────────────────

class TestHelperMatchesRealBuildOutput:
    def test_fully_built_snapshot(self):
        writer, conn = _run_full_build(F.build_tables())
        built = W.built_event_classes(writer._event_classes, writer._skipped)
        assert set(built) == {r['event_class'] for r in conn.tables['kala_field']}
        assert set(built) == set(writer._event_classes)  # nothing skipped this build

    def test_fully_skipped_snapshot(self):
        writer, conn = _run_full_build(F.build_tables(with_lifetime_prior=False))
        built = W.built_event_classes(writer._event_classes, writer._skipped)
        assert built == []
        assert conn.tables['kala_field'] == []

    def test_snapshot_column_still_carries_the_unfiltered_attempted_set(self):
        # This fix does NOT change what is written to
        # kala_field_snapshots.event_classes (still the full attempted list,
        # per its new comment) — it adds a way to DERIVE the built set: it
        # does not filter the column itself at write time.
        writer, conn = _run_full_build(F.build_tables(with_lifetime_prior=False))
        snap = conn.tables['kala_field_snapshots'][0]
        assert snap['event_classes'] == writer._event_classes
        assert F.EVENT_CLASS in snap['event_classes']


# ── the doc-comment half of the fix, made checkable ──────────────────────────

class TestColumnIsDocumented:
    MIGRATION_PATH = (
        Path(__file__).resolve().parents[4]
        / 'supabase' / 'migrations'
        / '572_kala_field_snapshots_event_classes_disclosure.sql'
    )

    def test_migration_file_exists(self):
        assert self.MIGRATION_PATH.exists(), (
            f'{self.MIGRATION_PATH} not found -- F-78 disclosure comment migration missing'
        )

    def test_comment_names_the_conflation_and_the_fix(self):
        sql = self.MIGRATION_PATH.read_text()
        assert 'COMMENT ON COLUMN kala_field_snapshots.event_classes' in sql
        assert 'built_event_classes' in sql
        assert 'skipped_classes' in sql
```

## 3. Exit test

**Command:**
```
cd platform/python-sidecar && python -m pytest tests/l3/ka_kshetra/test_event_classes_disclosure.py -v
```
**File:** `platform/python-sidecar/tests/l3/ka_kshetra/test_event_classes_disclosure.py` (§2c, full
content above).

**Fails today** — confirmed by direct grep before writing this spec:
`grep -n "built_event_classes" platform/python-sidecar/services/ka_kshetra/writer.py`
returns nothing. Every test in `TestBuiltEventClassesHelper` and
`TestHelperMatchesRealBuildOutput` calls `W.built_event_classes(...)`, which
raises `AttributeError: module 'services.ka_kshetra.writer' has no attribute
'built_event_classes'` — collection succeeds, every test in those two classes
fails. `TestColumnIsDocumented.test_migration_file_exists` also fails today
(file `572_...sql` does not exist).

**Passes after** §2a + §2b land: the function exists and is correct (4 unit
cases + 2 real-build cases), and the migration file exists with the required
substrings.

## 4. Sibling sites covered

**Same-writer sibling check (from DIAGNOSIS.md §4):** no other column in
`writer.py`'s `_run_snapshot` INSERT shares the "attempted list written
unconditionally alongside an independently-tracked skip list" shape.
`hashed_tables` is a static module constant; `substrate_build_ids` is an
unused `{}` placeholder. **Confirmed single-site defect — no sibling column
inside this writer needs the same fix.**

**Cross-file TS-consumer sibling check (from DIAGNOSIS.md §4, independently
re-verified, not inherited from the corpus unchecked):**
`grep -rn "event_classes" platform/src platform-mcp/src` and
`grep -rn "kala_field_snapshots" platform/src platform-mcp/src` found zero
TypeScript readers of either `kala_field_snapshots.event_classes` or
`.skipped_classes`. The only two files that query `kala_field_snapshots` at
all (`platform-mcp/src/lib/kala_envelope.ts`,
`platform/src/app/api/mcp/db/query/route.ts`) select only
`field_snapshot_id, field_content_hash` — never these two columns. **No
serving-layer sibling site exists to fix or exclude; this is confirmed
schema/writer-only, zero downstream consumers, per B in the assignment's fix
menu.** If a future TS surface starts reading `event_classes`, it now finds
(a) the column comment pointing at the correct derivation and (b) a Python
reference implementation to port — that is the recurrence guard's job (§5),
not a sibling this spec needs to touch today.

## 5. Recurrence guard

`TestHelperMatchesRealBuildOutput` (§2c) is the guard: it does not merely
assert the helper computes a set difference correctly in isolation (that's
`TestBuiltEventClassesHelper`, pure-function unit tests) — it runs a REAL
build through `plan_substeps`/`run_substep` and asserts the helper's output
equals the actual distinct `event_class` values found in `conn.tables['kala_field']`
after that build. This is the check that "actually detects the defect
class" (Stage R Q5): if a future change to `writer.py` ever lets a class be
recorded as `built` (no `kala_field` rows, but also missing from
`self._skipped`) — the exact "attempted but not accounted for" shape the
original finding described — `test_fully_built_snapshot`'s
`set(built) == {r['event_class'] for r in conn.tables['kala_field']}`
assertion fails, because `built_event_classes` would then wrongly include a
class with zero rows.

Additionally, `TestColumnIsDocumented` guards the documentation half: if a
future migration or manual `ALTER`/`COMMENT` ever drops or rewrites the
`event_classes` comment to remove the pointer to `built_event_classes` or
`skipped_classes`, that test fails — the doc gap cannot silently regress
without a red CI run.

## 6. Dependencies and rollback

**Dependencies:** none. No other PARIŚEṢA lane touches `writer.py`,
`stage4_field.py`, or `kala_field_snapshots` (DIAGNOSIS.md §5: "no known
control asserts on... zero risk of control regression"; "no other lanes
sharing this file" beyond the lease-routing question itself, which this
routing note resolves). No DB migration required beyond §2b's comment-only
addition — no backfill, no data migration, no orchestrator rebuild needed for
any existing chart (existing rows are unaffected; the comment applies to the
column definition, not stored values).

**Rollback:**
- §2a (writer.py): revert the one commit; `built_event_classes` is a new,
  unused-by-any-existing-call-site function — removing it changes nothing
  else in the writer.
- §2b (migration 572): `COMMENT ON COLUMN kala_field_snapshots.event_classes
  IS NULL;` — non-destructive, no data loss, stated in the migration file's
  own header per convention (see `571_p3a_shape_only_tier.sql`'s rollback
  comment style).
- §2c (test file): delete the file; no other test imports from it.

**Build-order note for S6:** §2a and §2b can build/land in either order or
together in one commit (they do not depend on each other functionally — the
comment references the function by name as documentation, not as a runtime
dependency). §2c depends on §2a existing (else it fails at import-of-attribute
time as designed) and references §2b's exact filename (must match exactly, or
`TestColumnIsDocumented.test_migration_file_exists` fails).

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element |
|---|---|
| C1 — `event_classes` declares 27 classes; only 6 have real rows; 21 are honest-skips recorded in `skipped_classes` | Confirmed unchanged by design (LAW ZERO honest-skip mechanism, `stage4_field.py:734` / `writer.py:1962-1970`) — this spec does NOT change the skip mechanism itself, only makes the resulting column pair disclosable. Not a defect to fix; the defect is C2. |
| C2 — naming/documentation conflation: `event_classes` reads as "covered" but means "attempted", no field-level comment, no documented caller obligation to subtract `skipped_classes` | §2a (`built_event_classes` — the documented, callable obligation) + §2b (the field-level `COMMENT ON COLUMN` itself, closing "no field-level comment" literally) |
| C3 — zero live TS consumers today (dormant, not user-facing) | §4 (independently re-verified sibling census — confirms C3, and confirms this stays schema/writer-only per the assignment's low-blast-radius framing; no serving-layer file needs a change) |
| Blast radius: risk if unfixed — next TS coverage-reporting tool will misreport build coverage (same class as F-34) | §2a + §2b together close this: a future reader now finds a documented column pointing at a canonical helper, rather than an undocumented column inviting the same conflation F-34 hit |
| Lease-scope flag (`PAR-F78-NEEDS-LEASE platform/python-sidecar/services/ka_kshetra/writer.py`) | Frontmatter `routing_note` + this document's existence as an S3-authored, S6-executable spec — resolves the routing question this spec itself was blocked on |
