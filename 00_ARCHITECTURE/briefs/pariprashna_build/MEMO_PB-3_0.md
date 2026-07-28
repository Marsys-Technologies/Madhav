---
artifact: MEMO_PB-3_0
type: PRATINIDHI RULING (executes OT-11, per BRIEF_PB-3 §0 first act)
campaign: PB — Paripraśna Build
wave: PB-3 SAMĪKṢĀ
version: 1.0
status: EXECUTED
date: 2026-07-28
authored_by: Claude Code (autonomous execution session, acting as Pratinidhi per CAMPAIGN_PB_MASTER_BRIEF_v1_0.md's "Pratinidhi replaces every human gate")
evidence_base: 00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-5.md (PC-8 — facts assembled, no choice made, decision reserved for this level)
---

# MEMO_PB-3_0 — OT-11 ledger-reconciliation ruling, executed

## Context

X-5 (evidence base) established, under PC-8 (assemble facts, make no choice),
that OT-11's "two ledgers" framing understates the landscape: there are
**three** prediction-tracking tables (`mimamsa_predictions` 384 rows,
`mcp_predictions` 0 rows, `brahma_prospective_ledger` 5 rows, all as of X-5's
snapshot — a live re-check at this memo's BIND found 286 / 12 / 7
respectively, reflecting an intervening chart rebuild and ongoing ambient
writes; see item 2's BIND-AT-OPEN correction below for the one discrepancy
that matters to this ruling) plus `phala_anchors` (the anchor set the
sidecar's `record_outcome` actually resolves against), and **none of the
three ledger tables satisfies §14.3 without a schema change** — none carries
a `message_part_id` FK, a `created_from_channel` column, or the 8-state
lifecycle. X-5 costed both "merge into one" and "keep the split, document it"
without picking either, per its own governance constraint.

BRIEF_PB-3 §0 already pre-commits the shape of the ruling this memo formalizes
(a fresh table + retire the empty interim relay + leave the populated,
referenced table alone) rather than leaving the choice fully open at this
level — this memo's job is to execute that shape with the specific decisions
X-5 left unmade (the new table's exact name, the rollback path, the
documentation), not to reopen Option A vs Option B from first principles.

## Ruling

**1. A fresh table, `brahma_mimamsa_prediction_ledger`, is created.**

This is exactly the name §14.3 already specifies as its target — X-5 confirmed
that name "matches no live table." Rather than inventing a fifth name, this
memo closes that exact gap: the table §14.3 was always describing now exists,
built from row one against the full field set L-1's lane charge specifies
(`chart_id`, `message_part_id` FK → PB-2's `message_parts.id`, `claim_text`,
`domain`, `window daterange`, `confidence numrange`, `direction`,
`technique_refs[]`, `grounding_fact_ids[]`, `created_from_channel`, the 8-state
lifecycle, co-located outcome columns, and the D-16 stamp COPIED at
confirmation time per D-16(d)). This is effectively X-5's "Option A" schema
target, but scoped to a **new** table rather than a destructive migration of
either existing populated ledger — avoiding X-5's identified Option-A risk
concentration ("the only populated + referenced ledger," "what breaks if done
wrong: the `mimamsa_calibration` FK, the `mi_pramana` build step, the cockpit
count, the §7.4 NO-LEAKAGE role") entirely, by never touching that table at
all. Full field spec, transition matrix, and acceptance criteria: L-1's lane
charge (BRIEF_PB-3.md §F1, Lane L-1) — this memo does not restate it.

**2. `mcp_predictions` is RETIRED.**

Justification, from X-5: sole writer is `ppl_writer.ts`, self-described in its
own migration (071) as an interim relay predating §14; no downstream
analytical consumer and no inbound FK ("No writer touches both...
`mcp_predictions` → read only by its own self-UPDATE... No downstream
analytical consumer, no inbound FK").

**BIND-AT-OPEN re-verification correction (this memo, 2026-07-28, before any
migration ran):** X-5's diagnostic snapshot recorded 0 rows; that count is now
stale. A live query at BIND found **12 rows**, accumulated since X-5's pass
via `calibration_producer.ts`'s `recordCalibrationStamp()` — an ambient write
on real `/api/pariprashna` turns (9 of the 12 rows' timestamps match this
campaign's own PB-2 gate-verification readings exactly; 3 predate this
session, from unrelated prior chart work). This is disclosed here rather than
silently reconciled, because the ruling below still holds but "0 rows, no
data to lose" is no longer literally true and must not be repeated as current
fact by a future reader of this memo. What the 12 rows actually are: every
non-key column (`prediction_text`, `domain`, `horizon`, `confidence`,
`verified`, `outcome_text`, `key_id`) is NULL on all 12 — only
`prediction_id` (all `PPL.CAL.*`, the `calibration_producer.ts` namespace,
never the `ppl_writer.ts` `PPL.MCP.*` namespace X-5's writer-map also names),
`chart_id`, and `logged_at` are populated. There is no claim text, no domain,
no stated confidence, no outcome — nothing a human ever confirmed and nothing
any downstream consumer could act on. **The substantive conclusion is
unchanged: there is no meaningful content in this table to lose**, but the
count is 12, not 0, and the rollback backup below captures whatever is
actually live at migration time (not a hardcoded assumption of emptiness) for
exactly this reason. `calibration_producer.ts`'s `recordCalibrationStamp()`
writing only 3 of 24 columns on every real turn is itself a latent,
pre-existing defect — noted here for L-5 or a future session's awareness, not
fixed by this memo (out of PB-3's scope; this table is being retired, not
repaired).

There is no *meaningful* data to lose and nothing else in the system depends
on this table existing. This is a destructive migration (table drop) and is
therefore Pratinidhi-level per BRIEF_PB-3's own classification — ruled here,
with the rollback path below, rather than left implicit.

**Rollback path (written before the retirement migration runs, per BIND-AT-OPEN
B-6):**
- Pre-migration: `CREATE TABLE mcp_predictions_retired_backup AS TABLE
  mcp_predictions;` (captures whatever rows are actually live at migration
  time — 12 content-empty stamp rows as of this memo's writing, verified
  above — plus the exact schema verbatim) inside the same migration
  transaction, before the `DROP TABLE`.
- Rollback (if ever needed): `CREATE TABLE mcp_predictions AS TABLE
  mcp_predictions_retired_backup;` re-recreates the original schema and every
  row backed up above; `ppl_writer.ts` would need to be un-repointed as a
  separate code-revert (git revert of the L-1 commit that repoints it), not a
  SQL-only rollback — recorded here so a future session doesn't assume the SQL
  rollback alone is sufficient.
- `platform-mcp`'s reference to `ppl_writer.ts`/`logPrediction()`/
  `recordOutcome()`: L-1 repoints or deletes these call sites as part of the
  same lane (per BRIEF_PB-3's `may_touch` grant for `ppl_writer.ts`
  specifically, under this MEMO). `calibration_producer.ts`'s
  `recordCalibrationStamp()` — confirmed by X-5 to write only to
  `mcp_predictions` — is retired alongside it.

**3. `mimamsa_predictions` and `brahma_prospective_ledger` are UNTOUCHED.**

`mimamsa_predictions` is the only populated (286 rows at this memo's live
BIND re-check — X-5's 384 reflected a snapshot before an intervening chart
rebuild; row count naturally moves with L5 STRUCTURAL-mode rebuilds via
`mi_bhavisya.py`'s documented DELETE-then-INSERT idempotency pattern, §N.3)
AND referenced (`mimamsa_calibration` FKs to it; `mi_pramana.py` reads it; L5
STRUCTURAL-mode calibration depends on it) ledger in the system. X-5's own
analysis: touching it concentrates all of Option A's migration risk onto the
one table nothing else in this campaign needs to change. This memo rules it
**hash-pinned at BIND** (schema + the live 286-row count recorded now, before
PB-3's lanes open, re-verified unchanged at gate close — row count is
expected to move only via a legitimate future chart rebuild, never via any
PB-3 lane) and out of scope for every PB-3 lane except as a read-only
reference for L-5's disposition work on `record_outcome`/`outcome.py`.
`brahma_prospective_ledger` (7 rows at live BIND re-check, up from X-5's 5 —
an active, independent write path per D-4a §11's explicit-filing design, not
tied to the mimamsa/phala rebuild cycle) is a **different, already-
purposed** table serving a different design (§11's explicit-filing concept, not
the conversational §14 detection loop this wave builds) — left alone entirely,
not merged, not documented-and-deprecated. Per BRIEF_PB-3 §F2's own
`must_not_touch`: "no schema/row change — hash-pinned" (mimamsa_predictions);
"disposition recorded only" (brahma_prospective_ledger).

**4. A ledger-map is committed.** See `LEDGER_MAP_PB-3.md` (this directory),
written alongside this memo, per this ruling's item 4 requirement.

## What this ruling is NOT

This is not X-5's Option A (full merge) or Option B (keep-both-document) — it
is a third path X-5's own costing gestured at but didn't fully spell out
("For a *truly* single ledger, also fold in `brahma_prospective_ledger`... the
merge surface is 3–4 tables, not 2" — implying a full merge was already a
larger undertaking than OT-11's original framing assumed). This ruling instead:
creates the ONE new table §14.3 always specified (closing that gap directly,
rather than retrofitting an existing, differently-typed table into it);
retires only the one table that is genuinely dead weight (no meaningful
content, no consumer); and leaves the two tables that carry real data and
real downstream
dependents (`mimamsa_predictions`, `brahma_prospective_ledger`) completely
alone. It resolves OT-11 by making the "three ledgers" landscape into "three
ledgers with non-overlapping, now-documented roles" rather than collapsing it
into one — a deliberate, disclosed choice, not a default.

**PF-1's `outcome.py`/`phala_anchors` schema-drift defect** (X-5 §4: the
sidecar references columns absent from the live `phala_anchors` table;
`record_outcome` has never been callable) is **not resolved by this memo** —
it is L-5's charge (BRIEF_PB-3.md §F1, Lane L-5), which must diagnose
rename-vs-missing before writing any fix, and which may legitimately park with
a costed spec rather than force a fix this wave. Any `phala_anchors` schema
change requires its own, separate Pratinidhi MEMO per W-4 — this memo does not
authorize one.

*End MEMO_PB-3_0 v1.0 — EXECUTED. Lanes bind to `brahma_mimamsa_prediction_ledger` as the table name.*
