---
artifact: G9_DISPOSITION
version: "1.0"
status: DISPOSITION_RECORDED
date: 2026-09-24
disposes: "migration 1085_nirmana_l0_bg_transit_rules_vedha_repair.sql (brief §8.4 / G-9) — RETIRED, file and test removed"
decided_by: "L3 Gochara session under the native's delegation of 2026-09-24 ('address each one of the points')"
---

# G-9 disposition — migration 1085 retired

## What 1085 was
The brief §8.4 deliverable: a file-only migration to repair `bg_transit_rules` from
`KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md` (re-cite 35 rows, fix three Venus vedha houses, insert the Mercury 8→1
pair, strike BPHS Ch.29, mark six Rāhu/Ketu rows uncited).

## Why it is retired rather than rewritten
1. **Its target state no longer exists anywhere.** The L0 vedha-and-frame repair (PR #2727, migrations
   1075–1079 + the fixed L0 writer) already applied every one of those repairs to production. A freshly
   seeded database gets the repaired rows from the fixed writer. There is no database on which 1085 is both
   valid and needed.
2. **As written it aborts in production.** Its §5 sweep raised if any row still cited `BPHS Ch.29`; 19 rows
   deliberately still do (outside the repair's verified predicate). The whole migration, including its
   `ADD COLUMN`, rolls back. Its own premise ("exactly 39 in the live database") was wrong: 58 before the
   repair. Attributed to the L0 session; the file-level facts (the `RAISE`, the `:133` comment, the
   `ON CONFLICT DO UPDATE`) were verified here.
3. **Loosening the sweep would be worse.** The Mercury upsert and the node-row `CASE` overwrite fields inside
   the 1078 content hash, turning the L0 integrity check red in production.
4. **The one piece worth keeping does not need a migration.** The L0 session suggested keeping a
   `bg_transit_rules.uncited_extension` column. It would duplicate what the row's own citation already says
   (`classical_citation LIKE 'UNSOURCED%'`) and create a second source of truth that an L0 rebuild could
   reset to false. The actual defect (§12.10b) was the *writer* stamping UNSOURCED rows as cited; that is
   fixed at `4d8f83050` by deriving every stamp from the citation. If a persisted column is still wanted, it
   is an L0-lane change to L0's own table, not ours.

## What survives elsewhere
- **Mercury phala "Gain of wealth and birth of children" (śloka 17).** Judged better-sourced than the L0
  session's synthesized text (an independent reviewer flagged that one). It sits inside the 1078 content
  hash, so applying it needs a **reseal computed against production state** — an L0-lane item this session
  cannot compute. Recorded here as a suggestion for the L0 owner.
- **Step 4 of the cutover kit** no longer applies 1085 or 1086; a `REFUSED` set makes re-adding either exit 3
  before any database is touched. 1086 (G-10, an L1 `ga_strength` digest-contract revision) is a real
  deliverable but was never authorised by sheet A-2 for tranche 1, and needs a writer deploy + governed
  rebuild; it is renamed `1086_nirmana_l1_…` (it is L1, not L0) and left for the L1 lane.

## Historical references intentionally left unchanged
`ESCALATIONS.md` E-009, `REMAINDER_FINAL_REPORT_v1_0.md`, `REVIEW_REQUEST_8_4_G9.md`, the rulings sheet §7.5
table and the Saṅgam/Kṣetra instruction files describe 1085 as it stood when written. They are records, not
instructions; this file supersedes them on 1085.
