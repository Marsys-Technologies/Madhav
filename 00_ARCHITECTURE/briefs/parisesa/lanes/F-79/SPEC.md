---
lane: F-79
stream: S6_ADHARA
stage: S (SPEC) — COMPLETE
author: ADHARA-LEAD (sonnet)
---

# F-79 — SPEC

## 1. Root cause

One commit (`54c809bc5`, 2026-07-19, renumbering migration 456→457 to resolve a
cross-directory numbering collision) performed the rename correctly at the git level but
did not also copy the superseded filename into `platform/migrations/_archive/`, the way
every other renumbered/superseded migration in this project's history was — an isolated
omission in that one commit, not a systemic policy gap (6 siblings checked, all correctly
archived).

## 2. Files changed

- `platform/migrations/_archive/456_lel_schema_v2_event_shapes.sql` (**new**) — recovered
  verbatim via `git show 54c809bc5^:platform/migrations/456_lel_schema_v2_event_shapes.sql`
  (the parent commit's version, before the rename). Cryptographically verified identical in
  SQL effect to the live `457_lel_schema_v2_event_shapes.sql` via the project's own
  `sqlIdentityOf`/`normalizeSqlForIdentity` (DIAGNOSIS.md §2) — this is not a guess at what
  456 contained, it is the exact historical file, independently confirmed correct.

**Explicitly not changed:** no `_migrations_applied` row. Backfilling `sql_identity` for the
456 row (now computable with proof — see DIAGNOSIS.md §2) is a real, low-risk follow-up but
is a DB write, and this campaign's standing rule is that any DB write needs its own
PRATINIDHI ruling regardless of size; not self-authorized here. This SPEC's fix is scoped to
the file-system archival gap only.

## 3. Exit test

Not a red→green unit test (this is a repo-hygiene/documentation-completeness fix, not a code
defect with runtime behavior). The verifiable claim: `find platform/migrations
platform/migrations/_archive -iname '456_lel_schema_v2_event_shapes.sql'` returns zero
results pre-fix, one result (`_archive/456_lel_schema_v2_event_shapes.sql`) post-fix — and
`diff` between that file and `git show 54c809bc5^:platform/migrations/
456_lel_schema_v2_event_shapes.sql` is empty (the archived copy is byte-identical to the
historical original, not a reconstruction).

## 4. Sibling sites covered

The 6 siblings the original finding cited (118/124/125/126/127_build_notifications/
133_notification_views) were confirmed already correctly archived (DIAGNOSIS.md §4) — no
action needed on those. A full sweep of all 430 `_migrations_applied` rows for the same gap
was not performed (out of scope for this pass); flagged as a possible follow-up, not treated
as a silent assumption that 456 is provably the only instance.

## 5. Recurrence guard

Not added in this pass. The gap was a one-off omission in a single historical commit, not a
missing process — `ONGOING_HYGIENE_POLICIES.md`'s archival-retain-in-place convention already
exists and is followed correctly everywhere else checked. A CI check enforcing "every
`_migrations_applied` filename must exist somewhere under `platform/migrations/`, active or
`_archive/`" would be a genuine, cheap recurrence guard for this class — noted as a
worthwhile follow-up, not built here (scope discipline: this SPEC fixes the one confirmed
gap, not a speculative general-purpose lint on top of it).

## 6. Dependencies / rollback

No dependencies. Rollback: `git rm platform/migrations/_archive/456_lel_schema_v2_event_shapes.sql`
— purely additive, no risk to any live system, no migration re-run, no DB write.

## 7. Sub-claim coverage table

| Sub-claim | Status | Spec element |
|---|---|---|
| C1 — 456's source absent from disk | Confirmed true, now remedied | §2 archived file |
| C2 — "unrecoverable... for audit or rollback-safety review" | **Corrected: false.** Recoverable via git history; now also restored to the working tree under the established archive convention | DIAGNOSIS.md §2, §2 archived file |
