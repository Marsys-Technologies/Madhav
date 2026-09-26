---
artifact: L0_W_L0_6_PACKET_REPORT
version: 1.0
status: PACKET_CLOSED
packet: W-L0-6 (Native rulings — sarvatobhadra school, prasna facility)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-26
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2 W-L0-6
---

# W-L0-6 Packet Report — Native rulings, both decided

Per-packet report per the execution kickoff. This packet changes no code, applies
no migration, and writes nothing to production: it **records two rulings** and
closes on them. Convention retained for form: scope → measured state → rulings →
what was NOT done → detectors.

## Packet scope (strategy §4.2 W-L0-6 row — what it actually asks)

The W-L0-6 row names exactly **two** native rulings and withdraws three others:

> **`bg_sarvatobhadra_grid`'s school** (ADJUDICATION-11: a doctrinal choice with
> no in-repo answer); **`bg_prashna_rules`' facility** (a product-scope and
> disclosure decision). **Withdrawn as native rulings:** `bg_vidhi_floors`'
> status (the live registry description already answers it — a verification
> task, not a ruling); the remedy identity question (dissolved: one space with
> spelling drift, §1.3 seam 3); and whether sambandha typing / Bhāvat Bhāvam
> scope / varga construction become L0 data (assigned to the strategy document
> itself, taken in its §2.4).

The row's proof is procedural, not numerical: "rulings recorded in
`KALA_DELEGATED_DECISIONS` or its L0 equivalent; each packet above that depends
on one names it." Both rulings exist and are recorded; this report names them
for every dependent packet.

## Half 1 — Sarvatobhadra school: RULED closed-empty

**The ruling.** Standing Mandate 2026-09-26, **Ruling 3** (this branch,
`00_ARCHITECTURE/autonomy/STANDING_MANDATE_2026-09-26.md`), rules the school
question closed-empty on the measured basis; register entry **ADK-0004**
(`00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md`) records it. Ruling 3's
operative text:

> `bg_sarvatobhadra_grid` is empty by design per ADJUDICATION-11 … Admission
> requires a *sourced* school — real classical grid geometry with a citation —
> and B.10 forbids synthesizing it. No such source has been admitted. … the
> grid remains empty, and the emptiness is the answer, not a gap. Record it as
> an honest empty leg with the admission condition stated (a named classical
> source for the grid geometry, admitted by explicit ruling). Do not populate,
> do not infer activation, do not carry it as an open item. **W-L0-6 closes on
> this ruling.**

**Admission condition, verbatim** (the standing guard, carried exactly):

> **a named classical source for the grid geometry, admitted by explicit
> ruling.**

**ADJUDICATION-11, cited**
(`00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md:711`,
verified this session): the lane's refusal to transcribe a grid is **AFFIRMED**
— "where geometry varies by tradition, selecting one grid IS an interpretive
act, and seating it as an L0 base fact is a B.1 layer violation"; the table is
registered **EMPTY**, school-keyed, because "an empty school-keyed table
honestly states that variants exist and none is held"; corpus findings: 8
`sarvatobhadra` hits, all noise except one passing `[MEDIUM]` mention; R-19
closed CLOSED-PARTIAL-BY-DESIGN with the two halves stated separately. The
table's own migration, `platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql`,
carries the same ruling in its header ("WHY THIS TABLE IS DELIBERATELY EMPTY"
/ "ACTIVATION PATH (zero code change)").

**Register ADK-0004, cited:** rules the sarvatobhadra half closes
closed-empty, requires this report to carry the admission condition verbatim
and to cite ADJUDICATION-11 and the 44/44 measurement — both done here.
ADK-0004's stated scope boundary: it covers the sarvatobhadra half only; the
prasna half "is not before me" and is recorded from its own decision record
(Half 2).

### Measured state (production, read-only, 2026-09-26)

Both figures were re-measured live this session against production via
cloud-sql-proxy on 127.0.0.1:5433, wrapped in
`BEGIN TRANSACTION READ ONLY; … ROLLBACK;`. Nothing was written.

| probe | query | result |
|---|---|---|
| L0 grid table | `SELECT count(*) FROM bg_sarvatobhadra_grid;` | **0 rows** |
| Served sarvatobhadra rows | `SELECT count(*) FROM kala_vedha_gochara WHERE vedha_kind='sarvatobhadra';` | **44 rows** |
| NULL-tag measurement | `… GROUP BY chart_id` over the same predicate | chart `482012f1-710e-4a25-994a-93821f5871aa` (canonical): 24 rows, 0 tagged, **24 NULL**; chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (second): 20 rows, 0 tagged, **20 NULL** — **44/44 NULL**, all 44 with `grid_basis='algorithmic_approximation'` |

**Resolution of the apparent "0 rows vs 44 rows" tension — two different
physical tables, both figures correct:**

- The kickoff/ruling's "**`bg_sarvatobhadra_grid` stays at 0 rows**" is the
  **L0 base table** owned by migration 529 — the school-keyed grid-geometry
  store, registered empty by design. Measured: **0 rows**. This is the
  population the ruling is about.
- The L3 batch's "**`grid_school_tag` is 100% NULL (44/44 sarvatobhadra rows
  across both charts)**" (`L3_W1_ANALYSIS_BATCH_B.md:385`) is the **served
  vedha-rows table `kala_vedha_gochara`**, whose `grid_basis`/`grid_school_tag`
  columns are owned by migration 526
  (`platform/supabase/migrations/526_kala_vedha_gochara.sql:96,121,165` —
  `grep -rn "grid_school_tag" platform/supabase/migrations/` confirms no other
  table carries the column). Its 44 `vedha_kind='sarvatobhadra'` rows (24
  canonical + 20 second chart) all carry the NULL tag with the disclosed
  `algorithmic_approximation` basis — the honest-null socket ADJUDICATION-11
  Part 3 mandated, correct **because** the L0 grid table is empty, and
  activating with zero code change the moment a sourced grid lands.

So: **0 rows in `bg_sarvatobhadra_grid`; 44 rows in
`kala_vedha_gochara WHERE vedha_kind='sarvatobhadra'`, 44/44 with NULL
`grid_school_tag`.** Not a contradiction — one is the unpopulated source of
grid truth, the other is the served approximation honestly disclosing that.

**Disposition.** Per Ruling 3 and ADK-0004: **not populated, not inferred, not
carried as an open item.** The emptiness is the answer. Reopening condition, as
the register records: "a sourced classical geometry admitted by explicit ruling
reopens it as a new packet" — fully reversible, never silently.

## Half 2 — Prasna facility: RULED closed, recorded not re-litigated

The facility question ("`bg_prashna_rules` — open the horary facility?") was
ruled by the native on 2026-09-25 and is recorded at
`00_ARCHITECTURE/briefs/nirmana/NATIVE_DECISIONS_2026-09-25_v1_0.md:19` on this
branch, and identically on `origin/l3/kala-layer-briefs` (same line 19,
verified via `git show`). The ruling:

> **Decision 2 — RULED: "Keep closed. Nothing in L0 requires it; it deserves
> its own product decision."**

Per that ruling the facility is **not opened**: no `bg_prashna_rules` target
expansion, no facility build, no activation inference of any kind was performed
or is proposed. It stays a product-scope decision belonging to its own future
product process, exactly as the ruling states. This half is recorded, not
re-litigated; nothing in this packet re-opens it. (ADK-0004 expressly scoped
itself to the sarvatobhadra half and left this half to its own record — this
line is that record's citation into the W-L0-6 packet.)

## What was NOT done

- **No population** — zero rows were inserted into `bg_sarvatobhadra_grid` or
  anywhere else; the L0 grid table remains at 0 rows by design.
- **No activation inference** — no chart, profile, or writer was pointed at a
  school_tag; the `kala_paddhati_profile` selection route
  (`factor_family='sarvatobhadra_grid'`) was not exercised.
- **No production writes** — the only production interaction was the read-only
  probe block above (`BEGIN TRANSACTION READ ONLY` / `ROLLBACK`); no migration
  applied, none staged.
- **No open items carried** — the sarvatobhadra half closes closed-empty (not
  "pending source" as an open task: the admission condition is the standing
  guard, and reopening is a new packet, not a tracked debt); the prasna half
  closes on Decision 2 and is explicitly *not* an L0 follow-up.
- **No git mutations** — this report is the packet's only artifact; committing
  is the orchestrator's.

## Detectors

**This packet has no detector of its own** — it records rulings; inventing a
mechanical gate for a recorded decision would be decoration, not verification.
The standing guard is the **admission condition itself**, and it is already
enforced by instruments that exist independent of this packet:

- the `kala_vedha_gochara_grid_fields_scope` CHECK (migration 526:121) permits
  a NULL `grid_school_tag` only in the empty-grid state — the schema itself
  fails loud if a tagged approximation row is ever written;
- the writer's DB-sourced-grid-first path
  (`services/ka_vedha_gochara/writer.py::_fetch_school_tagged_vedha_pair`,
  affirmed by ADJUDICATION-11 Part 2) is the zero-code-change activation
  socket; it activates only when rows land under a `school_tag`, which the
  admission condition gates;
- the throughput/freshness sentinels on `bg_sarvatobhadra_grid` (migrations
  553, 911, 912) keep the empty table under surveillance rather than silent.

## Exit-condition accounting (strategy §4.2 W-L0-6)

- *Rulings recorded in `KALA_DELEGATED_DECISIONS` or its L0 equivalent* —
  **met**: sarvatobhadra in ADK-0004 (L0-equivalent register) per Standing
  Mandate Ruling 3; prasna in `NATIVE_DECISIONS_2026-09-25_v1_0.md` Decision 2.
- *Each packet that depends on one names it* — **met for this packet's own
  halves**: both rulings named with citations above; dependent packets may cite
  ADK-0004 / Decision 2 directly.
- Both halves decided, neither carried open: **PACKET_CLOSED**.
