---
artifact: KSHETRA_L0_VEDHA_ROW_FIXES
canonical_id: KSHETRA_L0_VEDHA_ROW_FIXES
version: "1.3"
status: APPLIED_IN_PRODUCTION  # verified live 2026-09-24 via ref_transit_rules_get: §2 Venus 35/44/45 → 1/5/11 (page-cited PG323:C1); §3 Mercury 8→1 as id 569; §4 exceptions declared in rule_notes as a precision limit; §5 node rows stamped UNSOURCED and retained (B.10, N-14). Applied by the L0 repair (PR #2727, open at the time of writing). Nineteen non-vedha rows outside this spec's predicate still carry the refuted citation — correctly untouched. §6 (producer stamp columns) remains Gochara WP9
date: 2026-09-23
routed_to: >
  the L0 owner of `bg_transit_rules`, via the Gochara family stream (madhav-e6), whose
  F-23/G-8 lane already owns the page-grain re-citation of these rows. Kshetra consumes these rows
  through `ka_vedha_gochara` and does not edit them — `bg_*` is outside its `may_touch`.
authority: >
  none. This is a specification with verification SQL; the L0 owner authors and verifies
  the migration surgically (CLAUDE.md §N.4). Nothing here is applied by the Kshetra stream.
verified_by: >
  KSHETRA_INDEPENDENT_REVIEW_7_8_9_v1_0.md v1.1 (row-by-row against phaladeepika PG322:C1
  / PG323:C1), corroborated by the Kshetra author at the served corpus and again by Kimi K3
  (KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md). The repair semantics in §2 correct a wrong instruction the
  packet carried for one revision ("dedup") — see §2.1.
---

# `bg_transit_rules` house-vedha rows — the fixes the classical text requires

The 41 rows selected by the producer's own predicate (`rule_type='favourable' AND vedha_house IS
NOT NULL`, `services/ka_vedha_gochara/writer.py:100-101`) were compared row-by-row with Phaladīpikā
Adh. XXVI ślokas 3–8 (`phaladeepika:PG322:C1`, `PG323:C1`). 32 match; 3 contradict the text; 6 have
no counterpart there; the text has one pair the table lacks. Each item below carries the exact
rows, the text's value, and a SELECT that proves the item before and after.

## §1 — Re-citation (Gochara F-23/G-8 lane; restated for completeness, not re-owned)
39 rows cite `BPHS Ch.29 (Gochara Phala — Transit Results)`; in the served corpus BPHS page 29 is
Bhāva Padas, and no BPHS transit-vedha chapter exists. The 35 rows that match or, after §2, will
match ślokas 3–8 re-cite to `phaladeepika:PG322:C1` (Sun śl. 3, Moon śl. 4, Mars/Saturn śl. 5) or
`phaladeepika:PG323:C1` (Mercury śl. 6, Jupiter śl. 7, Venus śl. 8), at page grain — `verse_ref`
in this corpus is page-based; a chapter.śloka citation does not resolve.

## §2 — The three Venus rows: UPDATE `vedha_house`, do not delete

| id | graha | primary_house | stored vedha_house | text (śl. 8) | fix |
|---|---|---|---|---|---|
| 35 | venus | 3 | 11 | **1** | `UPDATE … SET vedha_house = 1 WHERE id = 35` |
| 44 | venus | 8 | 1 | **5** | `UPDATE … SET vedha_house = 5 WHERE id = 44` |
| 45 | venus | 9 | 2 | **11** | `UPDATE … SET vedha_house = 11 WHERE id = 45` |

### 2.1 Why "update", and the correction of a wrong instruction
Rows 35 and 44 are exact **transpositions** of correct rows already in the table (35 = id 179's
(11,3) reversed; 44 = id 33's (1,8) reversed) — that explains their origin as a column swap. For one
revision the packet then said their repair was "dedup, not fresh geometry." **That is wrong as a
repair:** deleting 35 and 44 would remove the only rows for Venus in the 3rd and 8th houses, and the
text's 3→1 and 8→5 pairs would be missing. The `primary_house` values are correct and needed; only
`vedha_house` is wrong. All three rows are updated to the text; nothing is deleted. Rows 179 and 33
are untouched.

**Verify before:** `SELECT id, primary_house, vedha_house FROM bg_transit_rules WHERE id IN (35,44,45,33,179);`
→ 35:(3,11) 44:(8,1) 45:(9,2) 33:(1,8) 179:(11,3).
**Verify after:** the same SELECT → 35:(3,1) 44:(8,5) 45:(9,11); 33 and 179 unchanged; and
`SELECT count(*) FROM bg_transit_rules WHERE graha='venus' AND rule_type='favourable' AND vedha_house IS NOT NULL` = 9, matching the text's nine pairs exactly:
(1,8) (2,7) (3,1) (4,10) (5,9) (8,5) (9,11) (11,3) (12,6).

## §3 — The missing Mercury pair: INSERT
Śloka 6 gives Mercury six pairs; the table holds five (ids 21–25: 2→5, 4→3, 6→9, 10→8, 11→12).
**Missing: Mercury transiting the 8th, vedha from the 1st.**
Insert one row: `graha='mercury', rule_type='favourable', primary_house=8, vedha_house=1,
classical_citation='Phaladīpikā Adh. XXVI śl. 6 — phaladeepika:PG323:C1'`, `phala` transcribed from
the L0 owner's existing Mercury phrasing convention (not invented here).
**Verify after:** `SELECT count(*) FROM bg_transit_rules WHERE graha='mercury' AND rule_type='favourable' AND vedha_house IS NOT NULL` = 6.

## §4 — Exceptions the table cannot express (record, do not encode silently)
The text excepts one graha per rule set — a transit of that graha through the vedha place does
**not** spoil the result: Saturn for the Sun (śl. 3), Mercury for the Moon (śl. 4), the Sun for
Saturn (śl. 5), the Moon for Mercury (śl. 6). `bg_transit_rules` has no exception column. Until the
L0 owner adds one (or records the exceptions in `rule_notes` with a declared `exception_graha`
convention), the producer's vedha detection over-fires for those four cases. Kshetra's uniform
admission rule treats such rows as `applied` on geometry — so this is an **honest precision limit
to declare** on the producer (`precision_regime`), not a reason to withhold the rows.

## §5 — The six Rāhu/Ketu rows: disposition for the L0 owner, not a fix
ids 187, 188, 189 (Rāhu) and 196, 197, 198 (Ketu) encode (3,9), (6,12), (11,5) — the Sun's set less
(10,4). Ślokas 3–8 name only the seven classical grahas; no vedha-bearing chunk of any served text
gives house-transit vedha pairs for the nodes. (PG348:C1 does give a Rāhu/Ketu vedha rule — for the
Sarvatobhadra chakra's asterism-direction vedha, a different mechanism — so the doctrine is not
absent; this specific pair set is unsourced.) Under the uniform rule they remain `unqualified`. The
L0 owner decides whether to keep them stamped `source_qualification = 'unsourced'` /
`corpus_verifiable = false` (honest, servable as unqualified) or remove them. Kshetra does not
decide this and consumes whichever the producer stamps.

## §6 — Producer-side columns the uniform rule needs (`ka_vedha_gochara`, not L0)
`kala_vedha_gochara` today has no `corpus_verifiable`, `source_qualification` or `precision_regime`
column (17 columns, DDL in migration 526). The uniform admission rule's precondition — "the producer
stamps" — is unbuilt. That is a `ka_vedha_gochara` work item (Gochara stream), sequenced before
Kshetra's S1-ingestion packet can admit any vedha row as `applied`; until it lands every row is
`unqualified` under the rule, by construction.

## §7 — Not in this spec (pointers only)
- The node-frame store fix (`ephemeris_daily` TRUE-node knots vs the declared mean) — ruling 7 / Gochara
  N-4a, L0 owner — **including a degree-level forensic anchor**: migration 624's sign-level anchor cannot
  detect the slip (MEAN 49.033° and TRUE 50.049° share sign 2 and nakṣatra 4; only the pāda differs), so it
  is a detector that provably cannot fail (§N.8); the L0 work adds expected mean-node longitude 49.033° ±
  arcseconds at JD 2445735.717361.
- The sarvatobhadra grid population from PG346–352 prose — migration 526's partition invariant,
  L0 owner; vedha-pair partitions transcribable today, letter cells need the PG345 diagram.
