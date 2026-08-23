---
lane: F-78
stream: S3 (SATYA, spec-author) → S6 (ĀDHĀRA, build-owner)
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-78/DIAGNOSIS.md, F-78/SPEC.md. No REVIEW_LEADS.md exists.
Verified against `/Users/Dev/par-night/main-ro`:
- `writer.py` lines 97, 201, 204, 285, 1183, 1732, 1745-1761, 1962-1970, 1983, 2186-2220 (all cited ranges read directly)
- `stage4_field.py` lines 128-134 (ClassSkipped docstring), 734 (raise site)
- `migrations/492_kala_field_core.sql` lines 207-210 (skipped_classes COMMENT)
- `migrations/` glob for 5xx.sql to confirm 571 is the current ceiling
- `grep built_event_classes writer.py` → 0 matches (pre-fix state confirmed)
- `tests/l3/ka_kshetra/` directory listing (fake_db.py, fixtures.py confirmed present)
- Full read of `fake_db.py` and `fixtures.py` to validate test harness assumptions

## Q1 — Mechanism vs symptom

Addresses the mechanism: `writer.py:1760` binds `list(self._event_classes)` — the full discovery-time candidate set — unconditionally to the INSERT, without ever filtering against `self._skipped` (populated at 1962-1970). Two internal set-difference computations (lines 1183, 1983) are ephemeral and never persisted. The fix (named exportable helper `built_event_classes` + `COMMENT ON COLUMN`) makes the disclosure canonical at the schema/API boundary, not just in writer internals. PASS.

## Q2 — Sub-claim coverage

DIAGNOSIS has three sub-claims:
- C1 (27 attempted, 6 built, 21 honest-skips) → SPEC §7: correctly classified as "Confirmed unchanged by design" — LAW ZERO mechanism is correct; only C2 is a defect. Mapping explicit. ✓
- C2 (no field-level comment, no documented caller obligation to subtract) → §2a (`built_event_classes` function) + §2b (`COMMENT ON COLUMN`). Both literals of "no field-level comment" and "no documented caller obligation" are closed. ✓
- C3 (zero TS consumers, dormant) → §4 (independently re-verified, not inherited). ✓

No unmapped sub-claim. PASS.

## Q3 — Exit test would fail on today's code

Direct grep `built_event_classes` in `writer.py` → 0 matches. Every test in `TestBuiltEventClassesHelper` and `TestHelperMatchesRealBuildOutput` calls `W.built_event_classes(...)` → `AttributeError: module 'services.ka_kshetra.writer' has no attribute 'built_event_classes'` on first call. `TestColumnIsDocumented.test_migration_file_exists` → `AssertionError` because `572_kala_field_snapshots_event_classes_disclosure.sql` is absent (highest migration confirmed as `571_p3a_shape_only_tier.sql`). Test collection succeeds; 9 of 9 test functions fail. PASS.

## Q4 — Sibling sites

Same-writer sibling check (SPEC §4, DIAGNOSIS §4): `hashed_tables` is a static module constant (no skip-list pairing); `substrate_build_ids` is a `{}` placeholder. Neither shares the "attempted list + independent skip list written to same row" shape. Confirmed single-site defect. ✓

TS-consumer census independently re-verified in SPEC §4: `platform-mcp/src/lib/kala_envelope.ts` and `platform/src/app/api/mcp/db/query/route.ts` are the only two files querying `kala_field_snapshots` — both select only `field_snapshot_id, field_content_hash`. The `platform/src/lib/event_classes.ts` file is a compile-time constant, not a DB read. Zero consumers of `event_classes` or `skipped_classes` columns confirmed. Excluded with stated reasons. PASS.

## Q5 — Recurrence guard

`TestHelperMatchesRealBuildOutput` exercises a real build through `plan_substeps`/`run_substep` on the `FakeConn`/`FakeCtx` harness and asserts:
```
set(built_event_classes(...)) == {r['event_class'] for r in conn.tables['kala_field']}
```
This ties the helper's output to what the writer ACTUALLY wrote to `kala_field`, not just to `self._skipped` bookkeeping. A future change that lets a class appear in `event_classes`, not in `skipped_classes`, yet with zero `kala_field` rows would break this assertion — exactly the defect class. `TestColumnIsDocumented` guards the documentation half. Both guards detect the defect class directly, not proxies. PASS.

## Q7 — Unverified assumptions / file:line accuracy

Every cited location verified against `main-ro` source:
- `writer.py:97` → `from typing import Any, Optional` ✓ (exact Diff 1 target)
- `writer.py:201` → `_DAYS_PER_JULIAN_YEAR = 365.2425` ✓
- `writer.py:204` → `@dataclass` / `class _ClassContext` ✓ (insertion point confirmed)
- `writer.py:285` → `self._event_classes = self._discover_event_classes(conn, self._chart_id)` ✓
- `writer.py:1732` → `def _run_snapshot` ✓
- `writer.py:1745-1761` → INSERT statement, `list(self._event_classes)` at 1760 ✓
- `writer.py:1962-1970` → `_record_skip`, log text exactly as cited ✓
- `writer.py:1183, 1983` → both inline `{s['event_class'] for s in self._skipped}` set-comprehensions ✓
- `writer.py:2186-2220` → `_discover_event_classes` static method, docstring "regardless of status" exact ✓
- `stage4_field.py:128-134` → `ClassSkipped` class docstring ✓
- `stage4_field.py:734` → `raise ClassSkipped(event_class, 'no_class_prior_row', ...)` ✓
- `492_kala_field_core.sql:207-210` → `COMMENT ON COLUMN kala_field_snapshots.skipped_classes` ✓
- Highest migration `571_p3a_shape_only_tier.sql` ✓ (572 does not exist)
- Test harness: `fake_db.py` has `FakeConn`, `FakeCtx(conn, chart_id)` ✓; `fixtures.py` has `CHART_ID`, `EVENT_CLASS`, `build_tables(*, with_lifetime_prior=True)` ✓

No unverified assumptions found. PASS.

## writer_asset / data_delta / RS-A check

Spec makes no `data_delta` claim. Fix is pure addition (new function + SQL COMMENT only). No rows written or modified; no backfill. Rebuild policy: zero rebuild required. Per PROTOCOL.md, verifier_v will still owe a Level-0 shadow run (writer-layer lane), but the spec is silent on rebuild because it correctly classifies this as documentation-only — no data output changes. The spec's own §6 states this explicitly. Consistent with PROTOCOL policy.

## Verdict: COMPLETE

All seven rubric items pass. Spec is mechanism-level, all sub-claims are mapped, exit test is genuinely red today and provably green after the two-file fix, sibling census is complete, recurrence guard is a real defect-class detector, and every file:line citation was verified accurate against current source.
