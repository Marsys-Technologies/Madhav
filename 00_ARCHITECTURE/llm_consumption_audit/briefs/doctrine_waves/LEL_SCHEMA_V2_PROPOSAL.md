---
artifact: LEL_SCHEMA_V2_PROPOSAL
type: SCHEMA PROPOSAL — APPROVED, staged for D-4, not yet migrated
status: APPROVED (native, 2026-07-18, D-3 closeout directive). Additive migration executes in
  D-4's own migration lane, not this session — approval covers the design, not the apply.
depends_on: DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md (RATIFIED)
authored_by: D-3 conductor session, pre-D-4 wrap-up pass, 2026-07-18
current_schema_verified_live: "life_events table, confirmed via live schema query 2026-07-18 —
  id(uuid), event_id(text), event_date(date), category(text), description(text),
  significance(text), chart_state(jsonb), source_section(text), build_id(text),
  provenance(jsonb), event_type(text), domain(text), source_citation(text),
  outcome_observed(boolean), chart_id(uuid), recorded_at(timestamptz), pool_consent(boolean),
  contributed_to_pool_at(timestamptz)"
---

# LEL Schema v2 — additive proposal implementing DR-13's event shapes

## Discipline

**Additive migration only. No rewriting of existing event data.** Every existing row keeps its
current single `event_date` and is implicitly `shape='point'`, `date_confidence='exact'` unless
explicitly retagged (a deliberate, reviewable act — see the questionnaire flow, not a bulk
reclassification script). This is a `platform/migrations/` surgical migration per CLAUDE.md §N.4
— new nullable columns + one new child table, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, no
`DROP`/`ALTER TYPE` on existing columns, migration-guard receipt required before apply (not
applied this session — staged for D-4's own migration lane).

## New columns on `life_events`

| Column | Type | Default | Purpose |
|---|---|---|---|
| `shape` | `text` | `'point'` | `point \| interval \| chain` — DR-13(a). CHECK constraint on the 3 values. |
| `date_confidence` | `text` | `'exact'` | `exact \| month_known \| year_only` — DR-13(d). CHECK constraint. |
| `interval_start` | `date` | `NULL` | Populated only when `shape='interval'`. DR-13(b). |
| `interval_end` | `date` | `NULL` | Populated only when `shape='interval'`. DR-13(b). |
| `chain_parent_event_id` | `text` | `NULL` | FK-style reference (to `event_id`, not `id`, matching the existing text-based `event_id` convention) — set on a MILESTONE row to point at its parent chain's synthetic grouping id. `NULL` for `point`/`interval` events and for the chain's own (optional) summary row. DR-13(c). |
| `milestone_label` | `text` | `NULL` | e.g. `'exam_written'`, `'result_declared'`, `'enrollment_confirmed'` — only set on chain-milestone rows. |
| `date_tightened_at` | `timestamptz` | `NULL` | Set when a native-provided tightened date (from the questionnaire flow) is applied — distinguishes "always was this precise" from "was fuzzy, native pinned it." Audit trail, not used in scoring. |
| `date_tightened_by_source` | `text` | `NULL` | e.g. `'native_questionnaire_2026-07-18'` — provenance for a tightened date, so a future session can trace WHY a previously-vague event now scores differently. |

## A chain is represented as N+1 rows, not 1 row with a JSON blob

Rejected alternative: cramming milestone dates into a `jsonb` array on one row. Reasoning: the
existing scoring harness (`t0_retrodiction/lib/lel.ts`'s pagination, `checks.ts`'s per-event
scoring) already operates on one-row-per-scoreable-event; keeping that invariant means a chain's
milestones are each their own `life_events` row (`shape='point'` or `'interval'` at the milestone
level, `chain_parent_event_id` linking them) rather than requiring every scoring consumer to grow
JSON-unpacking logic. The chain's ORIGINAL fuzzy-date row (if one already exists in the live
data) is retained, unmodified, with a new `superseded_by_chain` boolean-or-note (see below) so
nothing is silently orphaned — B.10 discipline, no fabricated computation, no silent drops.

**Additional column for this**: `superseded_by_chain_note` (`text`, `NULL` default) — set on a
legacy fuzzy row when its milestones have been separately recorded, pointing at the
`chain_parent_event_id` value the milestones now use. The legacy row stays queryable (so nothing
that depended on it breaks) but a scoring harness reading `shape` sees the note and knows to
prefer the milestone rows for any NEW scoring pass.

## Year-only secondary battery

No new table needed — `date_confidence='year_only'` + `shape='interval'` (with
`interval_start`/`interval_end` set to the calendar year's bounds, e.g. `2021-01-01`/`2021-12-31`
for "sometime in 2021") is sufficient. The SECONDARY-battery discipline (DR-13(d): never silently
folded into the primary hit-rate) is a SCORING-time filter (`WHERE date_confidence != 'year_only'`
for the primary battery, a separate pass for the secondary), not a schema-level separation — this
keeps the migration smaller and the data model uniform.

## Migration sketch (staged, NOT applied this session)

```sql
-- platform/migrations/<NNN>_lel_schema_v2_event_shapes.sql
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS shape text NOT NULL DEFAULT 'point'
  CHECK (shape IN ('point','interval','chain'));
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_confidence text NOT NULL DEFAULT 'exact'
  CHECK (date_confidence IN ('exact','month_known','year_only'));
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS interval_start date;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS interval_end date;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS chain_parent_event_id text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS milestone_label text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_tightened_at timestamptz;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_tightened_by_source text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS superseded_by_chain_note text;
-- CHECK: interval bounds only set when shape='interval' or a year_only point; left as an
-- application-layer invariant (not a DB CHECK) since it spans two nullable-conditional columns
-- and a CHECK referencing shape+interval_start+interval_end jointly is a reasonable follow-up,
-- not blocking this migration.
```

No `event_id`/`id`/existing-column semantics change. Every current query against `life_events`
(the T-0 harness, `lel_query` MCP tool, any L5 mimamsa intake) continues to work unmodified —
new columns are additive and default-populated for all existing rows.

## Consumption points that will need updating at D-4 (not part of this proposal, listed for
scoping only)

- `t0_retrodiction/lib/lel.ts`'s `LelEvent` type + `isScorable` — extend to read `shape`/
  `date_confidence`, not just `event_date`.
- The C-1 matcher spec (D-4) — the actual scoring-loop consumer of DR-13(b)/(c)/(d)/(e).
- `lel_query` MCP tool's served shape — should expose the new columns once populated, per B.10 (no
  fabricated computation — a served row with `shape='chain'` but no linked milestones yet is
  honestly reported as `chain, milestones: []`, not silently hidden).
