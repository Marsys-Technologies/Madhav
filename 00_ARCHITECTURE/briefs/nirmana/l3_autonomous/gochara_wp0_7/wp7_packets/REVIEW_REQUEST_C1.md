---
artifact: WP7_REVIEW_REQUEST_C1
packet_id: C-1
version: "1.0"
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, WP7 packet run)"
design_file: PACKET_C1_cockpit_clear.md v1.0
commit: 7bd66b450
---

# REVIEW REQUEST — C-1: cockpit Clear `EXPLICIT_CLEAR_OPS['ka_gochara']`

## What landed

- `platform/src/lib/cockpit/assetClearSpec.ts`
  - `ClearOp` extended with optional `guard { sql, refuse_message, cascade? }` (packet §3 Option A).
  - `EXPLICIT_CLEAR_OPS['ka_gochara']`: three DELETEs in dependency order
    (coverage → contacts → windows), each `WHERE chart_id = $1 AND generation = '4.0'`, no JOIN;
    guard on the first op with the packet's exact guard SQL, refuse_message, and cascade
    (`DELETE FROM kala_gochara_authority …` + `UPDATE kala_gochara_publication SET status='cleared' …`).
- `platform/src/app/api/cockpit/clear/execute/route.ts`
  - Explicit-ops branch now evaluates `guard` before any statement: guard match + non-release
    principal → whole-asset refusal into `failed_tables` (no SAVEPOINT, no statements); guard
    match + release authority (`isSuperAdmin`) → three DELETEs + cascade inside the same
    per-asset SAVEPOINT.

## Acceptance tests run (packet §5)

Route/spec level (vitest, mocked pool — 38 tests, all green):
- (a) chart-owner Clear when `'4.0'` is authoritative → refused, zero DELETE/cascade/SAVEPOINT issued,
  `failed_tables[0].error` carries the refusal message.
- (b) super_admin (release authority) → exactly the three DELETEs + authority-reset DELETE +
  publication `status='cleared'` UPDATE, one SAVEPOINT.
- (c) authority `'3.0'` chart → three DELETEs only, authority untouched, no cascade.
- (d) explicit entry takes precedence over `count_sql` (derived windows-only DELETE never runs).
- Spec-shape: dependency order, `'4.0'` literal on every statement, no JOIN, guard only on op 1.

Live-DB rows of §5 (zero-row verification across the three relations, conjunct (k),
P-1d `unpublished` hand-off after cascade) require the disposable Postgres with
`kala_gochara_authority`/`kala_gochara_publication` populated — **NOT_RUN** here
(disposable DB reachable but these are pre-WP10 relations with no seeded authority
rows in the test harness); flagged for the independent reviewer.

## Gates

- vitest (4 clear/spec files): 38/38 green.
- `tsc --noEmit --skipLibCheck`: 0 errors. ESLint: 0 errors (590 pre-existing warnings).

## Known deviations / notes for the reviewer

1. "Release authority" is mapped to the route's existing `isSuperAdmin` role — the only
   release-class principal the route knows. If the release authority is a distinct
   principal kind, the guard check needs one line changed.
2. Packet §4 (`clear_tables` registry display UPDATE + F-24 caveat) is a registry
   migration — the packet itself says it does NOT edit the registry; **not done here**,
   owed to the §6.3 migration owner.
3. The `status='cleared'` value needs the WP6 CHECK on `kala_gochara_publication.status`
   to admit `'cleared'` (packet §3 flags this for the two owners) — not part of this commit.
