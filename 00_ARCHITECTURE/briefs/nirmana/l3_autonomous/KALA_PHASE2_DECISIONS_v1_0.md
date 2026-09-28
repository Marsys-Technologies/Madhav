---
artifact: KALA_PHASE2_DECISIONS
canonical_id: KALA_PHASE2_DECISIONS
version: "1.0"
status: AWAITING_NATIVE_RULING
date: 2026-09-22
author: Kāla pre-elevation setup session (Phase 0.5), worktree l3/kala-setup-phase01
source_of_the_five: KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §6 (verbatim; that artifact is
  on open PR #2712 and is NOT on `main` — verified by `git log main -- <path>` returning empty)
supersedes_or_amends:
  - "KALA_NATIVE_RULING_SHEET_v1_0.md R4 (the MSR cascade) — D1 and D3 below SUPERSEDE R4's
     step 2 ('Sangam brief designs a stable signal key + upstream generation') by naming the
     substrate that step needs and by showing R4's step 1 (a standing rebuild-ordering rule)
     is not sufficient once L2 runs generation-governed. R4's REJECTION of a FK switch to
     RESTRICT stands and is reinforced: migration 1036 already achieves the RESTRICT outcome
     by a different route. R4's measured row facts stand, re-measured below."
  - "KALA_NATIVE_RULING_SHEET_v1_0.md R3 (who is authorized to start) — D5 below AMENDS R3.3:
     the '11 foundation-tier assets admitted on a one-page note' route is unchanged, but the
     acceptance baseline those notes are written against is set by D5, not by R3."
  - "KALA_NATIVE_RULING_SHEET_v1_0.md R6 (builder read access) — UNCHANGED, left standing.
     D1 does not alter the grant question or the `phala_rectification` hold."
  - "KALA_NATIVE_RULING_SHEET_v1_0.md R1 (inheritance under t3), R2 (headline metric),
     R5 (PR #2695 dispatcher split) — UNCHANGED, left standing. None of the five below
     touches them."
blocks:
  - "D1 blocks: Strategy §6.4 W1 in full; review §7 Phase 2.1/2.3; the cascade repair; the
     determinism gate; any L3 asset claiming DATA_ACCEPTED (Strategy §4 step 6)."
  - "D2 blocks: review §7 Phase 2.4; every per-asset §6.4 packet's 'method qualification' and
     'field-level transformations' fields; Strategy L3-Q05/Q07 proofs."
  - "D3 blocks: review §7 Phase 1.1 (W0); therefore ALL other Kāla work, since W0 gates W1+."
  - "D4 blocks: ka_tithi_pravesha promotion past PRODUCER_READY; W2 credit for it. Does NOT
     block its use as the path proof."
  - "D5 blocks: review §7 Phase 0.1 (freeze the baseline); therefore Phase 0 measurement has
     nothing to measure against."
does_not_authorize: "any change; every item is a proposal until the native rules"
changelog:
  - "1.0 (2026-09-22): first issue. Five decisions prepared early so the native can rule while
     Phase 1 executes. Three corrections to the critical review's own evidence are recorded in
     D1 and D3 — each found by verifying at the authority rather than re-running the review's
     query."
---

# Kāla — the five decisions that Phase 1 cannot be finished without

## §1 — How to use this sheet, and what ruling on it unlocks

This sheet prepares the five decisions that `KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §6`
names but deliberately does not resolve. It is issued **early, before Phase 1 runs**, so the
ruling and the execution can proceed in parallel rather than in series.

**Nothing in this document authorizes anything.** No migration is written, no grant proposed, no
code changed, no row touched. Every "recommend" below is a position taken so the native has
something to agree with or overrule — not a decision already taken. The whole of Phase 1 as
written in review §7 can start without any of these five being answered; what cannot start is
listed per-decision under *What is blocked until this is ruled*.

**Answer format.** Each decision ends with a ruling block:

```
RULING: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

Tick one. "adopt with change" and "defer" both want one line of why; "reject" wants the
alternative named, because every one of these five has a live consequence either way.

**What ruling on all five unlocks.** D3 unlocks W0 (and therefore everything). D1 unlocks W1 and
the whole of review §7 Phase 2. D5 unlocks Phase 0.1, which is what Phase 0's measurements are
measured *against*. D2 unlocks Phase 2.4 and every per-asset packet's method-qualification field.
D4 unlocks one asset only. Ruled together, the campaign has a baseline, a substrate, a safety
gate and a vocabulary; ruled apart, each is a separate stall.

**Proof tiers are kept separate throughout (F24).** Live-production SQL, source at `file:line`,
and governing-document quotation are labelled as what they are and never blended. Where I could
not verify something, it says `COULD NOT VERIFY` and why, rather than a plausible default (§N.7
item 6, F28).

**Three findings below correct the review that asked these questions.** They are in D1 (the L2
guard is already armed, which changes what "adopt generations" costs) and D3 (the review's named
fix for B1 targets a code path that is never reached; the live hazard is a different one, and
there is a second, unnoticed one). The review's *conclusions* survive all three; its *mechanisms*
do not. This is exactly the discipline the review itself asked for — verify at the authority,
never by re-running the claim's own query.

---

## §2 — The five at one screen

| # | Decision | Recommendation | Blocked until ruled | Reversible? |
|---|---|---|---|---|
| **D1** | Adopt the migrations 1035/1036 generation pattern for L3? | **YES — adopt.** It is the strategy's own design, and migration 1036's cross-layer guard has already made the alternative structurally untenable. | Strategy W1 entire; review §7 Phase 2.1 + 2.3; cascade repair; determinism gate; any L3 `DATA_ACCEPTED` claim | **Partly.** New tables + functions are additive and droppable while empty. Re-keying `kala_*` off `signal_id` is a data migration that is reversible in schema but costly in rebuild. |
| **D2** | "Confidence attached" = binding to F04 + F06 + F12 + Temporal Testimony, with no scalar standing in? | **YES — confirm the typed binding; reject the scalar.** Product §5.2 forbids the substitution in terms. | Review §7 Phase 2.4; the `method qualification` + `field-level transformations` fields of every §6.4 asset packet; the L3-Q05/Q07 proofs | **Yes, cheaply, in one direction only.** Adding fields later to a scalar-shaped store is a migration per asset; dropping fields later from a typed store is trivial. Asymmetric — which is the argument for typed now. |
| **D3** | Does "data is disposable" EXCLUDE the sweep snapshot, issued claims/observations (F17), and `kala_bhavishya`'s retained outcomes (L3-A21)? | **YES — confirm all three as protected classes.** And note: the live deletion path is **not** the one the review named, and a second exposure (FK CASCADE onto `kala_bhavishya`) protects nothing today. | Review §7 Phase 1.1 = Strategy W0 — which gates W1 and therefore every subsequent wave | **No, for the data.** 16,297 canonical + 19,323 control + 2,667 third-chart `generation='v1'` rows are declared never-rebuildable. The *guard* is reversible; the deletion it prevents is not. |
| **D4** | Who source-qualifies `ka_tithi_pravesha`'s Moon-return method, against which admitted source? | **Defer the asset; commission the corpus work now.** The corpus cannot currently supply the citation — 0 praveśa hits in 10,651 chunks — so the honest route is a named ingestion work item, not an asset-level judgement. Keep the asset as the path proof. | `ka_tithi_pravesha` promotion past PRODUCER_READY; its W2 credit. Nothing else. | **Yes, fully.** No data changes; the asset already stores `not_in_corpus` honestly. Reversing = raising the citation later and re-running one 0.61 s build. |
| **D5** | Baseline = L3-Q01–Q13 + Product §14 proving set, with Lane E's sixteen MAPPED IN not adopted? | **YES — adopt the ratified thirteen + the three §14 cases + one ordinary-period case; map Lane E in.** Lane E's sixteen are a coverage audit, not a rival authority. | Review §7 Phase 0.1; therefore Phase 0's measurements have no frozen thing to measure against | **Yes, cheaply.** A baseline is a document. Changing it later costs a re-measure, not a rebuild. |

---

## §3 — The five decisions in full

---

### D1 — Generations for L3

#### The decision

**Does L3 adopt the migrations 1035/1036 producer-generation pattern — immutable generations,
declared partitions, row snapshots, a head table, and publish/select/rollback functions — as the
substrate every `ka_*` asset binds to?**

#### The options

**Option A — Adopt (recommended).** Author an `l3_data_plane_*` family mirroring 1035/1036:
`l3_data_plane_generations` (chart × asset × generation, `status building|complete`, a
`semantic_output_digest` that only exists when complete), `..._partition_contexts` +
`..._generation_partitions` (declare-then-complete, so a zero-row partition is legitimate but an
arbitrary key cannot manufacture an empty completed generation), `..._row_snapshots`,
`..._generation_heads` (chart × asset → `current_generation_id` + `previous_generation_id`), plus
`open_/complete_/select_/rollback_l3_data_plane_generation` and a compatibility predicate that
walks the dependency vector against **published L1 and L2 heads**. Kāla rows then reference a
stable upstream key + generation rather than the surrogate `bodha_msr_signals.signal_id`.

**Option B — Defer; keep the standing rebuild-ordering rule (prior R4 step 1).** No new tables.
Kāla's signal-bound assets are rebuilt after any L2 signal rebuild by convention, and the
readiness query reports `claimed rows ≠ actual rows` as a defect.

**Option C — Adopt a thinner L3-local variant.** Generation id + partition table for L3's own
idempotency, but *no* binding to upstream L1/L2 heads — L3 pins its own outputs, reads upstream
`public` rows live.

#### Recommendation — plainly

**Adopt Option A.** Not because it is elegant but because migration 1036 has already made
Options B and C structurally untenable, and I do not think the review's authors knew that when
they wrote §6.1.

#### The evidence

**Live, at the authority (read-only SQL, 2026-09-22):**

```sql
SELECT 'l1_heads', count(*) FROM l1_data_plane_generation_heads
UNION ALL SELECT 'l1_generations', count(*) FROM l1_data_plane_generations
UNION ALL SELECT 'l1_partitions', count(*) FROM l1_data_plane_generation_partitions
UNION ALL SELECT 'l2_heads', count(*) FROM l2_data_plane_generation_heads
UNION ALL SELECT 'l2_partitions', count(*) FROM l2_data_plane_generation_partitions
UNION ALL SELECT 'l2_runs', count(*) FROM l2_data_plane_generation_runs
UNION ALL SELECT 'l2_producer_generations', count(*) FROM data_plane_l2_producer_generations;
-- l1_heads|0  l1_generations|0  l1_partitions|0
-- l2_heads|0  l2_partitions|0   l2_runs|0   l2_producer_generations|0
```

```sql
SELECT count(*) FROM information_schema.tables
WHERE table_schema='public' AND (table_name LIKE 'l3\_%' OR table_name LIKE '%l3_data_plane%');
-- 0
```

So: **the L1 and L2 generation tables exist; zero generations have ever been opened for either;
no L3 head table exists at all.** This confirms review §C1's measurement independently.

**The pattern, read in full at source.** `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql`
(2,233 lines) and `1036_data_plane_l2_producer_generations.sql` (2,092 lines).

- The head is a *pointer*, not a copy: `1035:269-279` —
  `l1_data_plane_generation_heads(chart_id, asset_id, current_generation_id, previous_generation_id, selected_at)`,
  PK `(chart_id, asset_id)`, FK to `l1_data_plane_generations` `ON DELETE RESTRICT`. `previous_generation_id`
  is the column that makes the native's own "if it gets wiped, we rebuild" safe: the prior generation
  is retained and pointed at until the new one is published.
- Completion is a real state, not a label: `1035:32-43` — `status IN ('building','complete')` with a
  CHECK that `complete` implies both `completed_at IS NOT NULL` **and** `semantic_output_digest IS NOT NULL`.
  A generation cannot be called complete without a digest. This is §N.8's earned-signal rule enforced in DDL.
- Declaration precedes completion: `1035:62-73` — a partition must exist in `l1_data_plane_partition_contexts`
  before a completion receipt can reference it, with the migration's own comment: *"Keeping declaration separate
  from completion preserves legitimate zero-row partitions without allowing an arbitrary key to manufacture an
  empty completed generation."*
- Select reads only complete generations: `1035:1516-1610` (`select_l1_data_plane_generation`) —
  `JOIN ... WHERE g.status = 'complete'`, `DISTINCT ON (source_table, row_identity)` ordered by
  `captured_at DESC`. Note this is a *read* function; publication is the head row.
- Compatibility is digest-equality across the whole vector: `1036:634-680`
  (`l2_data_plane_generation_is_compatible`) walks each dependency, resolves its layer's **head**, and
  `RETURN false` if `v_digest IS DISTINCT FROM v_dep->>'semantic_output_digest'`. This is F09's
  "compatible dependency sets, not independent latest-per-layer rows" in code, and
  `FOUNDATION:106`'s "`latest` is never a compatibility rule."
- No fall-through to mutable rows: `1036:790-793` comment on `bind_l2_exact_inputs` — *"Every governed
  source relation gets a transaction-local shadow table, including an empty one when that exact generation
  has no rows. A missing snapshot therefore cannot silently fall through to a mixed legacy active table."*
  This is Strategy `:145-147` step 3 implemented.

**The finding that changes the decision — the L2 guard is already armed.** This corrects the
framing of review §C1, which treats generations as a not-yet-built choice:

```sql
SELECT tgname, tgrelid::regclass::text, tgenabled FROM pg_trigger
WHERE NOT tgisinternal AND tgname LIKE '%data_plane%';
-- l2_data_plane_capture        | bodha_msr_signals | O
-- l2_data_plane_mutation_guard | bodha_msr_signals | O     (…and on ~20 other bodha_* tables)
```

`tgenabled='O'` = enabled. And the guard body, `1036:1584-1588`:

```
IF session_user <> 'data_plane_builder' THEN
  RAISE EXCEPTION 'protected L2 % requires direct data_plane_builder authentication', TG_OP;
END IF;
IF v_asset IS NULL OR v_asset='' OR v_chart IS NULL OR v_generation IS NULL
   OR v_partition IS NULL OR v_build IS NULL THEN
  RAISE EXCEPTION 'protected L2 % has no admitted transaction context', TG_OP;
END IF;
```

And `assert_l2_msr_delete_safe`, `1036:728-767`, discovers every FK pointing at `bodha_msr_signals`
from `pg_constraint`, exempts exactly two in-L2 tables, and otherwise:

```
RAISE EXCEPTION 'L2 MSR replacement blocked by cross-layer dependent rows in %.%', ...
```

with its own comment at `1036:684-686`: *"Delete-then-insert is permitted only while it remains inside
L2. Discover every current FK from the catalogue so a future L3/L4 reference also fails closed without
relying on a stale hand-maintained table list."*

The cross-layer FKs that would trip it, live:

```sql
SELECT c.relname, a.attname, k.confdeltype FROM pg_constraint k
JOIN pg_class c ON c.oid=k.conrelid JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=k.conkey[1]
WHERE k.contype='f' AND k.confrelid='public.bodha_msr_signals'::regclass;
-- bodha_contradictions|signal_a_id|c      bodha_contradictions|signal_b_id|c
-- bodha_signal_embeddings|signal_id|c     (both exempted by name at 1036:741-744)
-- kala_activation|signal_id|c
-- kala_bhavishya|signal_id|c
-- kala_convergence|signal_id|c
-- kala_darshana|signal_id|c
-- kala_obstruction|signal_id|c
```

Five `kala_*` FKs, all `confdeltype='c'` (CASCADE), none exempted. **So the choice is not
"generations or the status quo." It is: L3 binds by generation, or the first L2 MSR rebuild that
runs through the governed path hard-fails while any Kāla row exists.** That is the RESTRICT
outcome prior-R4 explicitly rejected for breaking the L2 campaign — already in the schema, by a
route R4 did not inspect.

**The cascade's effect, re-measured today** (this is the other half: today the guard is bypassed
because nothing runs through it, and CASCADE wins):

```sql
SELECT chart_id, count(*) FROM kala_activation GROUP BY 1;
-- 1c826d5a-…|336093     cb73cd3d-…|1055     (canonical 482012f1: ABSENT = 0)
SELECT chart_id, count(*) FROM kala_convergence GROUP BY 1;
-- 1c826d5a-…|17957      cb73cd3d-…|2540     (canonical: 0)
SELECT chart_id, count(*) FROM kala_activation_predicates GROUP BY 1;
-- 482012f1-…|50678      1c826d5a-…|50171    cb73cd3d-…|49875
```

Canonical `kala_activation` is empty while its `kala_activation_predicates` holds 50,678 rows —
the cascade emptied one and left the other, which is precisely the "both failure modes at once"
the review describes. And:

```sql
SELECT count(*) FROM kala_activation_predicates p
WHERE p.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND NOT EXISTS (SELECT 1 FROM bodha_msr_signals s
                  WHERE s.signal_id=p.signal_id AND s.chart_id=p.chart_id);
-- 79
```

79 dangling predicates, matching Strategy `:117` and the review exactly, independently re-measured.

**Governing text.** Strategy `:145-147` (bind one compatible transitive dependency vector; no
implicit fall-through); `:154-157` (*"Publish/select the complete compatible generation; downstream
eligibility opens only after this data acceptance"*); `:163-167` (*"A publication manifest/head can
point to retained immutable partitions so publication is atomic"* — and the explicit warning that
*"Any proposed change to WriterBase/orchestrator requires a separately named architecture decision"*,
i.e. this is additive, not a §N.2 freeze exception); `:169-172` (*"the accepted L2 guard deliberately
refuses unsafe cross-layer deletion. L3 cannot silently disable that guard in order to rebuild"* —
which is the same guard I measured above); FOUNDATION F09 `:36`; FOUNDATION `:106`.

**What cuts AGAINST the recommendation — honestly:**

1. **L3 cannot finish this alone.** `l2_data_plane_generation_is_compatible` resolves dependencies
   through `l2_data_plane_generation_heads`, which has **0 rows**. Until L2 opens *and publishes* a
   generation, an L3 generation has nothing to bind to. Adopting D1 therefore buys a substrate that
   sits idle until the L2 campaign delivers W1. That is a real dependency on a team this session does
   not control, and Strategy §6.4 W1 `:373` says so: *"accepted code alone or old public rows are
   insufficient."*
2. **The pattern is large.** 4,325 lines across two migrations for L1+L2. An L3 equivalent is not a
   weekend. The strategy's own §6.4 gives it a whole wave (W1) for a reason.
3. **Zero operational experience.** 0 generations opened in either layer means the pattern has never
   been exercised end-to-end in production. Adopting it for a third layer on the strength of a
   design nobody has run is a genuine risk. `COULD NOT VERIFY: whether an L2 build currently
   succeeds or fails under the armed guard` — establishing that requires running a build, which is a
   write, which this session is forbidden. The guard is armed and the generation count is zero;
   which of those two facts wins in practice is an empirical question I did not answer.
4. Option C (L3-local generations, live upstream reads) is genuinely cheaper and delivers L3's own
   idempotency and rollback. It just does not fix the cascade, does not pin the determinism gate's
   inputs, and leaves the 1036 guard's collision in place. It solves the second-most-important
   problem.

#### The cost of being wrong — both directions

**If the native adopts and I am wrong.** The L3 generation family is built and L2 never publishes,
so it sits empty. Cost: the W1 effort, plus the risk that an unexercised substrate carries its own
defects into first use. Blast radius is *additive*: new `l3_data_plane_*` tables with no rows can be
dropped. The non-reversible part is the `kala_*` re-key — changing five tables' FK from
`bodha_msr_signals(signal_id)` to a stable key + generation is a data migration over 337,148 +
20,497 + 750 + 747 + 100 rows (live counts). Schema-reversible; the rebuild to repopulate is not free.
Estimated rework: one wave, no data loss.

**If the native defers (Option B) and that is wrong.** Two things break, on different clocks.
*Near term:* the cascade keeps emptying Kāla whenever L2 rebuilds — already demonstrated on the
canonical chart, which has 0 `kala_activation` rows and 0 `kala_convergence` rows today while the
control chart has 336,093 and 17,957. A Kāla freeze taken now can be silently emptied while its
freeze event stands (prior R4's finding, still live). *The moment L2 goes generation-governed:*
`assert_l2_msr_delete_safe` fires and the L2 MSR rebuild **fails**, because five `kala_*` FKs are
cross-layer and unexempted. That is a hard stop on the L2 campaign caused by L3 data existing —
the exact outcome R4's rejection of `RESTRICT` was meant to avoid. Reversible only by deleting
Kāla's rows or by doing D1 then. Rework: the same wave, later, under pressure, with an L2 campaign
blocked on it.

**If the native takes Option C and that is wrong.** L3 gets idempotency and rollback and still has
both the cascade and the guard collision. The determinism gate stays undefined, because the inputs
are still mutable `public` rows that L2's active campaign changes underneath a running build. Rework
is the delta from C to A, which is most of A.

#### What is blocked until this is ruled

- **Strategy §6.4 W1 entire** (`:373`) — "Establish physical upstream truth." Its exit criterion is
  literally "accepted immutable dependency vectors."
- **Review §7 Phase 2.1** ("Adopt L3 generations; bind to published L1/L2 generations") and
  **Phase 2.3** ("Determinism gate relative to the pinned vector") — 2.3 is undefined without 2.1.
- **The cascade repair** (prior R4 step 2), which needs a generation to key against.
- **Any L3 asset reaching `DATA_ACCEPTED`** — Strategy `:395` requires "the asset's actual
  generation/partitions satisfy semantic, coverage, dependency and integrity contracts," and
  `:154-155` makes downstream eligibility conditional on it. Assets can reach `PRODUCER_READY`
  (`:394`) without this.

Phase 0 (freeze + measure) and Phase 1 (W0 safety) are **not** blocked and should proceed.

#### What this does NOT decide

- It does not decide **who builds L2's generation publication**, or when. D1 is L3 adopting the
  pattern; L2 publishing is the L2 campaign's own work and this sheet has no authority over it.
- It does not decide the **cascade's replacement key** — "a stable signal key + upstream generation"
  names a shape, not a column. That is the Sangam brief's design work (prior R4 step 2, standing).
- It does not authorize a **migration number**, a schema, or any DDL. Adopting D1 authorizes
  *designing* the L3 family inside W1, reviewed as a §6.4 packet.
- It does not touch the **FROZEN orchestrator contract** (§N.2). Generations are DB substrate; no
  `WriterBase` change is implied, and Strategy `:167` says explicitly that any such change would need
  its own named architecture decision.
- It does not decide anything about **`phala_rectification`** or the grants in prior R6.

#### Reversibility

**Partial.** The `l3_data_plane_*` family is additive and can be dropped while empty — fully
reversible at near-zero cost up to first use. Re-keying the five `kala_*` tables off `signal_id` is
reversible in schema (the FK can be restored) but the intervening data is rebuild-only. Once an L3
generation is published and a downstream consumer binds to it, reversal means a correction
generation, not a rollback — which is the pattern's own designed behaviour (`1036:1513+`
`rollback_l2_data_plane_generation`, and FOUNDATION `:110`: *"Rollback restores a compatible prior
set and records why; it never rewrites the original receipt."*).

```
RULING D1: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

---

### D2 — Typed confidence, not a scalar

#### The decision

**Does "confidence or salience attached to Kāla's outputs" mean binding every output row to F04
(six epistemic classes) + F06 (six completeness states) + F12 (eight operator roles) + the Strategy
§3 Temporal-Testimony object — with the explicit consequence that no single number may stand in for
that binding?**

#### The options

**Option A — Typed binding, no scalar (recommended).** Every Kāla output row declares: its F04
epistemic class; its F06 completeness state *per method, per window* with `reason`/`owner`/
`evidence_ref`/`next_eligible_action`; its F12 operator role as an input to whatever consumes it;
and the eight Temporal-Testimony fields (target structure, exact evidence roots, method/family,
units/polarity, applicability, support/opposition/silence, independence group, material
uncertainty), plus a comparable-scale flag. A numeric strength may still exist where it is
genuinely computed — it simply may not be the *only* thing carried, and may not be read as
confidence.

**Option B — A single salience/confidence scalar per row**, with the typed information left to
whatever the serving layer or the LLM can reconstruct.

**Option C — Scalar now, typed later.** Ship one number per row, add the typed fields in a later
wave once consumption patterns are known.

#### Recommendation — plainly

**Adopt Option A, and reject Option B in terms.** Product §5.2 does not leave room: *"A probability,
a comparative structural grade, an astronomical timestamp and a reliability interval are not
substitutes."* One number cannot be four incommensurable things.

#### The evidence

**Governing text, verbatim.**

- Product `:224` (§5.2): *"Keep deterministic fact, structural prior, classical prior, empirically
  calibrated claim and unresolved interpretation distinct. A probability, a comparative structural
  grade, an astronomical timestamp and a reliability interval are not substitutes. Numeric confidence
  must not imply empirical calibration that has not passed its gates."*
- FOUNDATION F06 `:33`: six states, and the Required-execution-evidence column reads — verbatim —
  *"No null/zero/empty fallback collapses these states."* A scalar has exactly one way to say
  "nothing here": a number. That collapses `inapplicable`, `unavailable`, `unqualified`,
  `contradictory_unresolved` and `unexplored` into one value. The contract forbids it by name.
- FOUNDATION F04 `:31` / codified `:63-68`: `SOURCE_TESTIMONY`, `QUALIFIED_RULE`,
  `COMPUTED_FACT_CONFIGURATION`, `INTERPRETIVE_INFERENCE`, `EXTERNAL_CLAIM_FORECAST`,
  `EVALUATION_EVIDENCE` — each with an explicit "must not establish alone" limit (`:65`, `:66`).
- FOUNDATION F12 `:39`: eight operator roles — `computation`, `applicability`, `counterevidence`,
  `uncertainty`, `interpretation`, `exclusion`, `relevance_navigation`, `evaluation` — *"Every
  important input declares an operator: … Operator field plus receiving output and test."*
- Strategy `:93`, the Temporal-Testimony row verbatim: *"Target structure, exact evidence roots,
  method/family, units/polarity, applicability, support/opposition/silence, independence group and
  material uncertainty | Sangam/Vighnakara and method adapters; **compare only declared comparable
  quantities**."*
- Strategy `:66` (L3-Q05): the required added distinction includes *"non-comparable scales"*, and
  the named primary proof is *"Remove a method; show actual changed and unchanged evidence without a
  forced consensus."* A scalar cannot pass that proof — removing a method changes the number, and
  nothing in the number says which method left or whether it was even comparable.
- FOUNDATION `:74`: *"A component may reach different rungs for different questions, subjects,
  methods or channels."* One row-level scalar has one rung.

**The layer already does part of this, honestly.** Lane E's audit records `ka_sangam` storing
`tier_basis='relative_uncalibrated'` per row, and `ka_bhavishya_lekha.py:552-590` refusing
probability language unless `tier_basis='calibrated'`
(`.../readiness/_work/LANE_E_LAYER_VALUE_MODEL.md:346`). That is F04/F06 discipline in miniature,
already shipped. Option A extends an existing practice rather than importing a new one.

**What cuts AGAINST the recommendation — honestly:**

1. **The native's own stated preference was for the LLM to reconcile in context.** Option A is
   heavier than that framing invites: it puts structure in the *data* rather than trusting the model
   to infer it. The honest counter-argument is that the model cannot infer what was never stored —
   but "heavier than asked for" is a real cost and the native should weigh it.
2. **Storage and writer cost is not trivial.** Eight Temporal-Testimony fields plus three vocabulary
   bindings per row, against tables like `kala_activation` at 337,148 rows and
   `kala_activation_predicates` at 50,678 rows per chart (live counts). This is a per-asset writer
   change across the layer, not a config flag.
3. **Nothing yet consumes it.** Lane E found `independent_current_count` is read by no `ka_*`
   consumer and `confidence_label_relative` by none either (`LANE_E_LAYER_VALUE_MODEL.md:346, :353`).
   Strategy `:100-106` is blunt about this: *"A fetched or cited field with no declared effect has
   not met the use contract."* Adopting A without also naming the receiving operator risks building
   more unconsumed fields — which is why the recommendation includes F12's *receiving output* as
   part of the binding, not an afterthought.
4. **I found no existing Kāla row carrying a single scalar sold as confidence across the layer** —
   `COULD NOT VERIFY: whether any current writer would actually have to *remove* a scalar, versus
   simply add fields alongside one.` The review names `confidence_score = ICC/13 sold as confidence`
   as a Phase-3 force-fit instance; I did not independently locate and read that code in this pass.
   So D2's cost may be purely additive, which would make it cheaper than I am claiming. Weak
   evidence on the removal side; strong on the addition side.

#### The cost of being wrong — both directions

**If the native adopts and I am wrong.** Kāla carries typed fields nobody reads. Cost: writer work
across ~18 row-producing identities, storage, and the review burden of fields with no declared
effect (Strategy `:100-106`'s own "unserved" gap class). Fully reversible — dropping columns is
cheap, and no reader depends on them by hypothesis.

**If the native rules for the scalar (Option B) and that is wrong.** The damage is not a wrong
number; it is an *unrecoverable* one. Once "unavailable," "inapplicable" and "unqualified" have all
been written as the same value, the distinction is gone from the data and can only be restored by
rebuilding every affected asset. Product `:224` is violated at the store, so every downstream
surface inherits the violation. The concrete failure the review names: the LLM compares a Tājika
score to a daśā score as commensurable, because nothing in either number says they are on different
scales. Rework: a full-layer rebuild. **This is the asymmetry that drives the recommendation** —
typed→scalar is a cheap projection; scalar→typed is a rebuild.

**If the native takes Option C (scalar now, typed later)** — that is Option B with a promise. The
rows written in between are the ones that cannot be recovered. It is the more expensive option
disguised as the cheaper one.

#### What is blocked until this is ruled

- **Review §7 Phase 2.4** ("Bind every output to F04/F06/F12 + Temporal Testimony; comparability
  flag per method").
- The **`method qualification`** and **`field-level transformations`** fields of every §6.4 asset
  packet (`Strategy:382-387`) — an asset packet cannot state its method qualification before the
  vocabulary it states it in is ruled.
- The **L3-Q05** (`:66`) and **L3-Q07** (`:68`) proofs, both of which require method-level
  applicability to be a stored property.
- Review §2 **A3** ("Comparability and applicability per method per window").

Not blocked: everything in Phase 0 and Phase 1, and D1's substrate work.

#### What this does NOT decide

- It does not decide **the serving contract**. How typed confidence is rendered to a person, or
  budgeted in a response, is Pūrṇa-owned (review C6/D5; `L3-U04`/`L3-U11` at `Strategy:444, :451`).
  L3 owns the data and the sentinel test; not `platform-mcp/src/tools/kala_views/`.
- It does not decide **any new field**. The recommendation is explicitly to add *no* field these
  four vocabularies already cover — creating a rival vocabulary is the failure this is meant to
  prevent.
- It does not decide **whether numeric strength values may exist at all**. They may, where they are
  genuinely computed. D2 decides that a number may not be the sole carrier and may not be labelled
  confidence without calibration (Product `:224` third sentence).
- It does not resolve **calibration**. F24 `:51` keeps computational correctness, explanatory value
  and empirical performance as separate proof tiers; D2 lives entirely in the first.

#### Reversibility

**Yes, and cheaply — in one direction.** Typed→scalar is a projection computable at read time, so
adopting A keeps B available forever. Scalar→typed cannot be computed from what was stored. Adopting
A is the reversible choice; adopting B is the irreversible one. That asymmetry is the whole
argument.

```
RULING D2: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

---

### D3 — The protected classes

#### The decision

**Does "data is disposable" EXCLUDE three classes — (i) the `ka_gochara_sweep` `generation='v1'`
snapshot, (ii) issued claims and observations (F17), and (iii) `kala_bhavishya`'s retained outcomes
(L3-A21) — such that no rebuild, Clear route, or cascade may delete them?**

#### The options

**Option A — Confirm all three as protected; guard each at the mechanism that can reach it
(recommended).** "Disposable" retains its full force for rebuildable projections. The three named
classes get real guards, not conventions.

**Option B — Confirm the principle, defer the guards.** The three classes are declared protected in
doctrine; the code guards are scheduled into a later wave.

**Option C — Keep "disposable" as a blanket.** Registry truth is fixed so the *label* is right; the
data is treated as reconstructible.

#### Recommendation — plainly

**Adopt Option A.** And the native should know that the review's own prescription for this item
names the wrong code path, misses the live one, and misses a second exposure entirely. All three
corrections are below. The review's *conclusion* — that B1 belongs in W0, before anything else — is
right, and more urgently right than it argued.

#### The evidence

**Live row counts, at the authority (read-only, 2026-09-22):**

```sql
SELECT generation, chart_id, count(*) FROM kala_gochara_windows GROUP BY 1,2 ORDER BY 1;
-- 3.0 | 1c826d5a-… |   916
-- 3.0 | 482012f1-… |   914
-- v1  | cb73cd3d-… |  2667
-- v1  | 1c826d5a-… | 19323
-- v1  | 482012f1-… | 16297      ← canonical chart's share of the protected snapshot
-- (v1 total = 38,287, matching the review)

SELECT chart_id, count(*) FROM kala_bhavishya GROUP BY 1;
-- 1c826d5a-…|100      (canonical 482012f1: 0 rows — nothing to review, per review §5)

SELECT count(*) FROM build_protected_assets;
-- 0
```

**Correction 1 — the review's named fix targets a path that is never reached.**
The review's C4 says: *"Fix: `ka_gochara.target_table` → `_v2`."* Live registry:

```sql
SELECT asset_id, scope, target_table, is_active, count_sql FROM asset_registry
WHERE asset_id IN ('ka_gochara','ka_gochara_sweep');
-- ka_gochara       | per_chart | kala_gochara_windows | t
--   count_sql: SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'
-- ka_gochara_sweep | per_chart | kala_gochara_windows | f
--   count_sql: SELECT COUNT(*) FROM kala_gochara_windows  WHERE chart_id=$1 AND generation='v1'
```

`target_table` on `ka_gochara` is indeed stale — but the Clear route's resolution order is
documented at `platform/src/app/api/cockpit/clear/route.ts:159-162`: *"1. EXPLICIT_CLEAR_OPS
… 2. deriveDeleteSqlFromCountSql (count_sql auto-transformable) 3. target_table fallback."*
`ka_gochara` **has** a `count_sql`, so step 2 wins at `:185` and step 3 never runs. Its derived
DELETE targets `kala_gochara_windows_v2` (live: 163 rows at `generation='2.0'`), not the v1
snapshot. Fixing `target_table` is correct hygiene and changes nothing about the hazard.

**Correction 2 — the live deletion path is the retired asset's own row, via the missing
`is_active` filter.** `ka_gochara_sweep` is `is_active = f`, but the Clear route loads the
registry with no such filter — `route.ts:115-117`:

```sql
SELECT asset_id, layer, COALESCE(depends_on,'{}') AS depends_on, estimated_seconds,
       scope, target_table, count_sql, english_name, sanskrit_name
FROM asset_registry ORDER BY layer, sort_order
```

and the scope filter, `platform/src/lib/cockpit/clearScopeFilter.ts:29-30`, is:

```ts
} else if (scope === 'layer') {
  return registry.filter(r => r.layer === scopeTarget && allowedScopes.includes(r.scope))
```

— `layer` and `scope` only; **no `is_active`**. `ka_gochara_sweep` is `layer='kala'`,
`scope='per_chart'`, and `allowedScopes = ['per_chart']` for a non-super-admin (`route.ts:93`). It
therefore survives the filter, `deriveDeleteSqlFromCountSql` (`assetClearSpec.ts:40-45`, a
`SELECT count(*) FROM` → `DELETE FROM` rewrite that refuses only JOIN-bearing SQL) transforms its
`count_sql` into `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'`, and I
confirmed `EXPLICIT_CLEAR_OPS` has **no** `ka_gochara*` entry (`grep -c ka_gochara
assetClearSpec.ts` → 0), so no explicit op overrides it. **The retired asset's own row carries a
live, correct, generation-scoped DELETE against the one thing the strategy says can never be
rebuilt.** 16,297 rows for the canonical chart.

One precision on reachability the review stated loosely: the route is **not** open to any
authenticated user. `route.ts:84-92` requires `authorizeChartAccess(...) !== 'all'` → 403, i.e.
owner or super_admin, and the comment there records that this was tightened in P2-B-007. So the
exposure is "the chart's own owner clicking layer-Clear on kala" — for the canonical chart, the
native. That is smaller than "any user" and still sufficient to lose the snapshot.

**Correction 3 — the guard exists, is wired, is empty, and reads the wrong column.**
`build_protected_assets` is real and the Clear route already consults it (`route.ts:118-125`), and
so does the execute route (`execute/route.ts:96-98`, whose own comment calls it *"the ONLY guard for
any other asset a native later adds"*). But:

```sql
SELECT column_name FROM information_schema.columns WHERE table_name='build_protected_assets';
-- asset_id | chart_id | protected_since | reason | protected_generations (ARRAY)
SELECT count(*) FROM build_protected_assets;   -- 0
```

Two defects. (a) **0 rows** — the guard is armed and empty; `protectedAssetIds` is an empty Set
(`route.ts:126`) and withholds nothing. (b) Both routes select **`asset_id` only**. The table has a
`protected_generations` ARRAY column and neither route reads it — so even fully populated, the
guard can protect an *asset*, never a *generation*. Since `ka_gochara` (active, `generation='2.0'`
in `_v2`) and `ka_gochara_sweep` (retired, `generation='v1'`) are different assets over an
overlapping table family, generation-grain is exactly the grain this case needs. This is a §N.8
Earned-Signal instance: the signal "protected" exists, a detector exists, and the detector measures
a coarser claim than the one being made.

**Class (iii) is unprotected by anything at all.** From D1's FK measurement: `kala_bhavishya` holds
an `ON DELETE CASCADE` FK on `bodha_msr_signals(signal_id)`. The projections table that carries
*retained outcomes* is deleted by an upstream L2 rebuild, with no Clear route involved and no guard
consulted. Live: `kala_bhavishya` has 100 rows, all on `1c826d5a`, **0 on the canonical chart** —
consistent with the canonical chart having been through an L2 rebuild.

**Governing text.**
- Strategy `:172-173`, verbatim: *"`ka_gochara_sweep` remains retired, snapshot-protected and never
  rebuildable."* And `:293` (L3-H01): *"Preserve snapshot and references, keep the non-rebuild
  detector, exclude from dispatch."*
- Strategy `:169-172`: *"Before replacement, inventory transitive FK `CASCADE`/`SET NULL` actions and
  non-FK referrers, preserve restorable snapshots and prove rollback."*
- FOUNDATION F17 `:44`: *"Freeze completed issued claims before later outcomes … Never evaluate a
  retrospective rewrite."*
- FOUNDATION F19 `:46`: preserve *"historical readings, failed forecasts, tests, receipts…"*
- Strategy `:450` (L3-U10): *"Candidate regeneration does not reset a delivered forecast. Empty
  rebuild preserves observations."*
- Strategy `:291` (L3-A21): *"Preserve projection usefulness and observations … rebuildable
  projections cannot own or rewrite issued history."*
- Strategy `:222` (P0): Bhavishya's *"empty-input early return follows deletion but precedes its
  outcome-preservation guard,"* required exit *"restore prior data/outcomes."*

**What cuts AGAINST the recommendation — honestly:**

1. **"Disposable" is the native's own stated posture and it is mostly correct.** Three protected
   classes out of a 22-identity layer is a narrow carve-out, but it is still a carve-out from a
   principle the native chose deliberately, and every protected class is a future rebuild that
   cannot simply be re-run. The strongest case for Option C is that a protected class you cannot
   rebuild is a permanent liability, and the honest alternative is to accept the loss once and
   rebuild clean. That argument is real for classes (i) — but it dies on the text: `:172-173` says
   *never rebuildable*, so accepting the loss is accepting a permanent gap, not a rebuild.
2. **The FK CASCADE on `kala_bhavishya` was deliberate** (migration 403, per prior R4). Reversing it
   is not an oversight-correction; it is a design change with L2-campaign consequences — which is
   exactly what D1 is for. D3 alone cannot fix class (iii); it can only declare it.
3. **`kala_bhavishya` holds 0 rows for the canonical chart today.** The thing being protected is,
   for the native's own chart, already gone. Protecting it now protects future outcomes and the
   control chart's 100 rows — which is worth doing, but the native should not read D3 as recovering
   anything.
4. `COULD NOT VERIFY: that a layer-scoped Clear on 'kala' actually executes the derived DELETE
   end-to-end.` Proving it requires POSTing the route or running the DELETE, both writes, both
   forbidden here. What is verified is every link in the chain by reading: registry row → no
   `is_active` filter → scope filter passes → no EXPLICIT_CLEAR_OPS override → `deriveDelete…`
   transform applies → `protectedAssetIds` empty. I did not execute it.

#### The cost of being wrong — both directions

**If the native adopts and I am wrong.** Three classes are guarded that did not need guarding.
Cost: populating `build_protected_assets` (a few rows), an `is_active` predicate in two files, and
— for generation-grain — teaching both Clear routes to read `protected_generations`. Small, and
every part of it is a guard that can be removed. The only real cost of over-protection is that a
legitimate future rebuild of `kala_gochara_windows` v1 gets blocked, which is the intended
behaviour.

**If the native keeps "disposable" as a blanket (Option C) and that is wrong.** 38,287
never-rebuildable rows (16,297 of them the native's own chart) are deleted by one layer-Clear, and
the strategy's standing ruling is violated with no recovery path — `:172-173` says never rebuildable,
so there is no rebuild to fall back on. Separately, `kala_bhavishya`'s retained outcomes keep being
CASCADE-deleted by L2 rebuilds, which destroys F17's issuance-predates-outcome chain and makes
L5 calibration unprovable for those claims (FOUNDATION `:142`: empirical evaluation may not be
claimed from *"Fixtures, retrodiction or explanatory value"* — and a deleted outcome is none of the
three). **Irreversible.** Rework: not rework; loss.

**If the native takes Option B (principle now, guards later).** The exposure stays open for exactly
as long as the deferral. Given it is one `is_active` predicate plus rows in a table that already
exists and is already consulted, the deferral buys very little.

#### What is blocked until this is ruled

- **Review §7 Phase 1.1** — *"Close B1: registry `target_table` truth, `is_active` on Clear, real
  guard on `generation='v1'`"* — which is **Strategy W0** (`:372`), whose exit criterion includes
  *"restorable preservation proof."*
- Because W0 gates W1 and W1 gates W2+ (`Strategy:372-374`), **D3 transitively blocks the whole
  campaign.** It is the only one of the five with that property, which is why it should be ruled
  first if the native rules them one at a time.
- **Strategy W7** (`:379`) exit explicitly requires *"protected sweep preserved."*
- **L3-A21's W6 gate** (`:378`): *"Bhavishya after stable-history preservation proof."*

#### What this does NOT decide

- It does not decide **how** each guard is implemented — DB trigger, populated
  `build_protected_assets` rows, an `is_active` predicate, or all three. That is W0's design work,
  reviewed as a §6.4 packet.
- It does not decide the **FK cascade's disposition**. Declaring `kala_bhavishya`'s outcomes
  protected does not by itself remove the CASCADE; that needs D1's substrate and prior-R4 step 2's
  re-key. D3 establishes the obligation; D1 supplies the means.
- It does not weaken "disposable" for anything else. Every rebuildable projection in the layer
  remains disposable. This is a three-item exclusion list, not a new default.
- It does not decide whether `ka_gochara_sweep`'s **registry row should be deleted**. Strategy `:293`
  says preserve its references and exclude it from dispatch — deletion and exclusion are different
  acts, and only exclusion is authorized by the text.
- It does not touch `kala_gochara_windows_v2`'s `generation='2.0'` (163 rows) or `g3_utkarsha`
  (1,830 rows), which are active-asset output and remain disposable.

#### Reversibility

**The guards: fully reversible.** The deletions they prevent: **not reversible at all** — `:172-173`
declares the sweep never rebuildable, and F17's issuance-predates-outcome ordering cannot be
reconstructed after the fact by definition. This is the one decision on the sheet where the
downside of the wrong answer is permanent loss rather than rework.

```
RULING D3: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

---

### D4 — `ka_tithi_pravesha` source qualification

#### The decision

**Who qualifies the implemented Moon-return method against the admitted tithi-praveśa method, and
from which admitted source?**

#### The options

**Option A — Commission a corpus ingestion work item; defer the asset's promotion (recommended).**
Name an owner for ingesting a praveśa-bearing primary source at citation grade (chapter/verse, not
page-scan), against the already-ingested `tajaka_neelakanthi` or a new admitted edition. The asset
stays `PRODUCER_READY`, keeps serving with its honest `not_in_corpus`, and is not counted as W2
progress. Promotion follows the citation.

**Option B — Qualify from the existing corpus now.** Have the Kāla session locate a praveśa passage
in the ingested texts and cite it.

**Option C — Qualify by expert testimony.** Record a named acharya-level judgement that the
implemented Moon-return instant *is* the admitted tithi-praveśa method, as `SOURCE_TESTIMONY`
(F04), with no chapter/verse.

**Option D — Promote on Product §3.10's admission alone.** The Product names tithi-praveśa as an
admitted instrument; treat that as the qualification.

#### Recommendation — plainly

**Adopt Option A. Option B is not available — I checked, and the citation is not in the corpus.**
Option D should be rejected explicitly, because it confuses "this instrument is admitted" with
"this implementation matches that instrument," which is the actual open question.

#### The evidence

**The writer's own citation, verbatim at source** —
`platform/python-sidecar/services/ka_tithi_pravesha/writer.py:64-70`:

```python
CLASSICAL_SOURCE_CITATION = (
    "not_in_corpus: Tithi-Praveśa (lunar-return annual chart) named in "
    "KALA_TRANSFORMATION_HANDOFF_v1_0.md's glossary as the lunar-return "
    "counterpart to Tājika Vārṣaphala; no primary-source chapter/verse "
    "citation for the technique specifically is ingested in this corpus — "
    "an ingestion work item is filed, not fabricated here (§N.7 item 6)."
)
```

Stored per row at `writer.py:274`. The writer's header comment at `:35` says it reads *"honestly
`not_in_corpus` on every row — never a fabricated chapter reference."* **The writer is already
behaving correctly.** This is not a defect to fix; it is a gap to fill.

**The corpus, checked at the authority (read-only, 2026-09-22).** The live corpus is
`classical_text_chunks` (10,651 rows across 15 texts); `classical_chunks` exists but is **empty**
(0 rows) — worth noting, since a naive search there returns a false negative.

```sql
SELECT count(*) FILTER (WHERE content_en ILIKE '%praves%' OR content_sa ILIKE '%praves%') AS praves,
       count(*) FILTER (WHERE content_en ILIKE '%varsha%' OR content_en ILIKE '%varṣa%') AS varsha,
       count(*) FILTER (WHERE content_en ILIKE '%annual chart%')                          AS annual_chart,
       count(*) FILTER (WHERE content_en ILIKE '%tithi%')                                 AS tithi
FROM classical_text_chunks;
-- praves | varsha | annual_chart | tithi
--   0    |   36   |      0       |  149
```

**Zero praveśa-family hits in the entire ingested corpus.** The writer's `not_in_corpus` is
verified true, not merely asserted.

**The right text is present but not usable at citation grade.** `tajaka_neelakanthi` — Tājika
Nīlakaṇṭhī, Nilakantha, tier 2, public domain, license cleared — is ingested with 290 chunks. But:

```sql
SELECT COALESCE(translation_status,'null'), count(*) FROM classical_text_chunks
WHERE text_id='tajaka_neelakanthi' GROUP BY 1;
-- null | 290
```

Its `verse_ref` values are page/column identifiers (`PG1:C1` … `PG288:C1`), not chapter/verse, and
`chapter` holds the page number. Reading two sample chunks returns untranslated Devanagari/Hindi
commentary — e.g. the chunk at page 52 opens `( ५२) ताजिकनीखकण्टी ।` — with visible OCR corruption
in the surrounding corpus (the BPHS samples are heavily garbled). So the source that *should* carry
the varṣa-praveśa doctrine is in the corpus, and is not currently retrievable as a chapter/verse
citation in any language a qualification could quote. **That is why Option B fails: not because the
text is absent, but because the ingestion is page-scanned, untranslated and unverified.**

**The live-path test — and a correction to the review.** Review C8 relays L3-A09's *"Current v3
does not read it"* (`Strategy:279`). That is true of the **gochara_v3 engine** and I verified why:
the only mechanism consuming it is `w27b_tithi_pravesha`, whose module header states at
`platform/python-sidecar/services/gochara_v3/mechanisms/w27_annual_stack.py:16-17`:

> *"CANDIDATE mechanisms (Wave 2, Lane W2.7). **NOT wired into engine.py** — that wiring is Wave 4
> work."*

and which degrades honestly when absent (`:332-341`, `getattr(context, "tithi_pravesha_rows", None)
or []` → `reason="no_annual_data"`, modifier 1.0).

**But there IS a live consumer the review did not account for.** The retrieval registry registers a
serving capability for it:

- `platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts:27-34` — descriptor
  `marsys://tool/L3/query_tithi_pravesha`, layer L3, querying `kala_tithi_pravesha` at `:91`.
- `platform/src/lib/retrieval/registry/layers/L3_kala/index.ts:55` imports it and `:78` calls
  `registerCapability(queryTithiPraveshaCapability)`.

And it has data: `SELECT count(*) FROM kala_tithi_pravesha WHERE chart_id='482012f1-…'` → **120**
(240 rows across 2 charts). So the asset is *served today*, carrying `not_in_corpus` on every row.
The unqualified method is already reachable by a consumer. That sharpens D4 rather than softening
it — Strategy `:395`/`:396` gate `DATA_ACCEPTED` on qualification, and something serving without it
is the more urgent case, not the less.

**Product's admission.** Product `:160` (§3.10), verbatim: *"Daśā systems and their nested periods,
gochara, relevant transit conditions, annual/return methods, Tājaka, **tithi-praveśa**, Sudarśana,
aṣṭakavarga, vedha, sensitive contacts and other admitted temporal instruments retain
method-specific roles."* Tithi-praveśa is admitted as an instrument. Product `:160` does **not**
say which computation realizes it — the qualification question is precisely the gap between the
admission and the implementation.

**What cuts AGAINST the recommendation — honestly:**

1. **Option C (expert testimony) is legitimate under the contract and I am recommending against it
   anyway.** F04 `:31` admits `SOURCE_TESTIMONY` as a first-class epistemic class, and `:63` gives it
   its own "must not establish alone" limit rather than excluding it. If the native is willing to be
   the named authority, Option C is faster, textually admissible, and unblocks W2 credit for this
   asset immediately. My argument against is that it leaves the layer's *only* path-proof asset
   resting on testimony when the text that would settle it is already sitting in the corpus needing
   translation — but that is a preference for durability over speed, and the native may reasonably
   weigh it the other way. **This is the weakest recommendation on the sheet.**
2. **Corpus ingestion has no named owner and is not L3 work.** Option A commissions something
   outside this campaign's scope and therefore outside its control — the same objection D1 faces with
   L2 publication. It could sit indefinitely.
3. **The blast radius is one asset.** Unlike D1/D3/D5, getting D4 wrong stalls `ka_tithi_pravesha`
   and nothing else. It does not deserve to hold up a ruling session.
4. `COULD NOT VERIFY: whether any *runtime caller* actually invokes query_tithi_pravesha in
   production.` I verified the capability is registered in the registry and that the table holds 120
   canonical rows; I did not trace an MCP tool or UI surface calling it. The descriptor comment at
   `query_tithi_pravesha.ts:14-17` names `kala_now_get` and `kala_ahead_get` as intended callers and
   calls the latter *"a documented follow-on not built in this PR."* So "registered and queryable"
   is verified; "invoked" is not.
5. `COULD NOT VERIFY: the 0.61 s build time and the mutation-proven verification flag` the review
   cites — both would require running the build.

#### The cost of being wrong — both directions

**If the native adopts Option A and I am wrong.** `ka_tithi_pravesha` sits at `PRODUCER_READY`
waiting on a corpus item nobody schedules. Cost: one asset's W2 credit, indefinitely. The asset
keeps working, keeps serving its 120 canonical rows, keeps telling the truth about its own source.
Fully reversible — the native can switch to Option C at any moment and promote it the same day.
Strategy `:374` (W2 exit) does say *"Any required unqualified method remains a closure blocker"* —
so if this asset is required for W2 closure, Option A stalls W2, not just the asset. That is the
real cost and I want it stated plainly.

**If the native takes Option D (promote on §3.10's admission) and that is wrong.** The layer ships
a Moon-return computation labelled as the classical tithi-praveśa method with nothing establishing
that they are the same technique. Under F04 `:65`, `COMPUTED_FACT_CONFIGURATION` *"must not
establish alone: unique meaning, manifestation or causation"* — a computed return instant does not
establish that it is the admitted instrument. Under §N.7 item 1, narration must trace to a cited
fact it reads, not one it re-derives. Reversible (relabel, re-run one 0.61 s build), but the
interval during which it was served as qualified is not recoverable, and it sets the precedent that
Product-level admission substitutes for method qualification — which would quietly unqualify a lot
more than this asset.

**If the native takes Option C and that is wrong** — i.e. the expert judgement is later contradicted
by the text — the cost is a corrected citation and one rebuild. Small. Which is the honest reason
Option C deserves serious consideration despite my recommendation.

#### What is blocked until this is ruled

- `ka_tithi_pravesha`'s promotion past `PRODUCER_READY` (`Strategy:394`) toward `DATA_ACCEPTED`
  (`:395`).
- Its **W2 credit** (`Strategy:374`), and — if it is a *required* W2 member — W2's closure, per
  `:374`'s "unqualified method remains a closure blocker."
- **Nothing else.** In particular this does **not** block its continued use as the path proof
  (build → receipt → evidence → freeze) or as the vehicle for the 5.5-hour timezone fix, which the
  review explicitly preserves in §4 "What survives unchanged."

#### What this does NOT decide

- It does not decide **the method's correctness**. Whether the implemented Moon-return instant is
  astronomically right is a separate question from whether it is the admitted classical technique.
  D4 is about the second only.
- It does not decide **`w27b`'s Wave-4 wiring** into `gochara_v3/engine.py`. That is W4 work
  (`Strategy:376`) and has its own gate.
- It does not decide whether **`query_tithi_pravesha` should stop serving** pending qualification.
  My reading is that it should keep serving — B.10 forbids silently dropping data and the row
  already carries `not_in_corpus` honestly (§N.6 part 1: serve it, flag it, never let it read as
  confirmed). But the native may rule otherwise, and that would be a separate instruction.
- It does not decide **corpus policy** — which editions get ingested, at what tier, under what
  license. Option A commissions one work item; it does not set a standard.

#### Reversibility

**Fully reversible, at the lowest cost on this sheet.** No data changes either way. The asset
already stores the honest string. Reversing Option A = raise the citation later, update one
constant, re-run one build. Reversing Option D = relabel and re-run, with the served-as-qualified
interval being the only unrecoverable part.

```
RULING D4: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

---

### D5 — Baseline authority

#### The decision

**Is the frozen acceptance baseline L3-Q01–Q13 (Strategy §2) plus Product §14's first proving set —
with Lane E's sixteen questions MAPPED IN as a coverage audit rather than adopted as a rival
question authority?**

#### The options

**Option A — Thirteen + three §14 cases + one ordinary-period case; Lane E mapped in (recommended).**
The baseline is `Strategy:62-74` (L3-Q01–Q13, each with its strategy-named primary proof), plus
Product `:490`'s three proving-set cases, plus one ordinary-period case added per Product `:348`.
Lane E's Q-K01–Q-K16 are mapped onto them; any Q-K that maps to nothing is raised as a proposed
strategy amendment or dropped.

**Option B — Adopt Lane E's sixteen as the baseline.** They are more recent, asset-traced, and
written from the consumer's side.

**Option C — Adopt both, side by side.** Twenty-nine questions, two authorities.

#### Recommendation — plainly

**Adopt Option A.** Not because Lane E is weak — it is the better *audit* — but because two
question sets means two acceptance verdicts, and the campaign has already demonstrated what
competing authorities cost.

#### The evidence

**The ratified thirteen exist, each with a named primary proof.** `Strategy:62-74`, §2 spanning
`:53-80`. Each row carries three columns: question/product obligation, required added distinction,
and primary proof. The proofs are ablation-shaped, e.g. L3-Q01 `:62` — *"Perturb the qualifying
condition while holding geometry fixed"*; L3-Q05 `:66` — *"Remove a method; show actual changed and
unchanged evidence without a forced consensus"*; L3-Q07 `:68` — *"Destroy the structural bridge
while retaining coincident dates; the cross-domain inference must disappear"*; L3-Q13 `:74` — *"A
sentinel only in a low-ranked, non-default field reaches the allowed consumer and saved result."*
**That last one is the same sentinel test review C6 assigns to L3 while Pūrṇa owns the code — the
ratified set already contains the serving obligation.**

§2's closing paragraph `:76-80` supplies the acceptance rule: *"L3 should provide affirmative
qualified temporal results where supported. It cannot earn full completion solely by returning
unavailable states. Unsupported methods retain explicit gaps with owners; no doctrine or predictive
probability is invented to complete the matrix."*

**Product §14's first proving set, verbatim at `:490`:**

> *"The first proving set should include **a deep structural question without a forced forecast**;
> **a structure–time question with accountable permitted forward claims when earned**; and **a
> historical challenge that actively seeks misfit**."*

**The ordinary-period case, required by Product `:348`:** *"The experience must work for ordinary
charts and ordinary periods, not only dramatic named yogas or the repeatedly studied native chart."*
Reinforced at `:479`: *"ordinary as well as dramatic cases."* Every fixture the campaign currently
has is dramatic, per review A4 — hence the fourth case.

**Lane E's sixteen exist and are exactly as described.**
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/readiness/_work/LANE_E_LAYER_VALUE_MODEL.md` (1,011
lines). The portfolio is stated as a baseline at `:122`: *"The portfolio is the acceptance baseline
in this sense: a Kāla that can answer Q-K01…Q-K16 with…"*. The sixteen are headed at `:128`
(Q-K01) through `:307` (Q-K16), each tagged by kind — ORDINARY, PRECISE LOOKUP, COMPOUND,
COMPARISON, DISAGREEMENT, UNCERTAINTY, CONTINUITY, ELECTION, RECURRENCE, BOUNDARY, NEGATIVE,
RETRODICTION — and the traceability table at `:340-355` maps each to owning assets with per-column
verdicts.

**Lane E is the better audit, and this is the strongest case against my own recommendation.** Its
traceability table is asset-traced and falsifiable in a way §2 is not. Examples I read directly:
`:344` finds `ka_tulana`'s only caller is a self-test probe (`service_probes.py:841-845`) after
grepping three source trees; `:346` finds `ka_sangam` stores `tier_basis='relative_uncalibrated'`
and that `ka_bhavishya_lekha.py:552-590` refuses probability language unless calibrated — an
*unusually honest* positive finding; `:350` finds `max_windows=8` undisclosed and contradicted by
the writer's own comment; `:352` finds Q-K12 *"structurally unanswerable"* with no owning asset.
That is real, specific, verified work. Option B is not a straw man.

**But Lane E's own two named gaps argue for mapping rather than adopting.** GAP-E1 (`:361`,
cross-clock agreement has no owning asset) is L3-Q05's territory (`Strategy:66`). GAP-E2 (`:374`,
provenance-aware de-correlation has no owner) is the Temporal-Testimony object's **independence
group** field (`Strategy:93`). Both Lane E gaps are already *named* in the ratified set. They are
findings about implementation against §2's requirements, not questions §2 omits — which is
precisely what "map in, don't adopt" means in practice.

**Governing text against rival authorities.** FOUNDATION `:20`: *"If a strategic brief conflicts
with the adopted Product Definition v3.0, ratified architecture, safety policy or an accepted
upstream contract, execution stops and returns the conflict to the strategic parent."* And `:22`:
*"No proposal becomes adopted because it was authored, committed, tested, deployed, previously
sealed or left uncontested."* Lane E's sixteen were authored and are uncontested; under `:22` that
is explicitly not adoption. FOUNDATION `:154`: *"Activity, checks or deployment never self-authorize
the next stage."*

**What cuts AGAINST the recommendation — honestly:**

1. **Lane E may contain a question §2 genuinely lacks.** Q-K14 (*"Is this an unusual period for me,
   or an ordinary one?"* — within-chart rarity, `:285`/`:353`) has no obvious L3-Q counterpart; §2's
   nearest is L3-Q02's "stronger under a named criterion," which is comparative, not distributional.
   If the mapping finds real orphans, Option A's own escape hatch (raise as a strategy amendment)
   has to actually be used, not quietly dropped. `COULD NOT VERIFY: whether all sixteen map cleanly.`
   Doing the mapping is Phase 0.1's work; I did not perform it here and will not assert it succeeds.
2. **Thirteen is not obviously the right number.** §2's ratification is an act of authorship, not a
   proof of completeness. Option A treats a ratified set as authoritative because it is ratified —
   which is close to the circularity FOUNDATION `:22` warns about, pointed the other way.
3. **Four fixture cases is thin** for a 22-identity layer. Option A's baseline is 13 questions + 4
   cases; Lane E's is 16 questions with per-asset traces. The mapping must import Lane E's rigour or
   the baseline will be less testable than what it supersedes.

#### The cost of being wrong — both directions

**If the native adopts Option A and I am wrong.** A real consumer question — Q-K14's rarity
question is the likeliest candidate — is not in the baseline, so the layer can pass acceptance
without answering it. Cost: a strategy amendment and a re-measure. **Fully reversible, and cheap:
a baseline is a document, and the campaign has already shown it can amend strategy in place.**
The honest mitigation is that Option A's mapping step is designed to surface exactly this before
the freeze.

**If the native adopts Option B and that is wrong.** Two authorities exist for what Kāla must
answer, and every acceptance verdict can be contested by pointing at the other. The review names
this as *"the pattern this whole review keeps finding"* (§C3), and FOUNDATION `:20` requires that a
brief conflicting with ratified architecture **stop and return the conflict upward** — so a
Lane-E-based verdict that disagrees with §2 does not resolve, it halts. Worse, Lane E's sixteen
carry no *primary proofs*: §2 pairs each question with an ablation that falsifies it
(`:62`–`:74`), while Lane E pairs each with an asset trace. Trading proofs for traces makes the
baseline diagnostic rather than falsifiable. Rework: re-freeze the baseline and re-measure — a
document cost, not a rebuild, but it invalidates whatever Phase 0 measured in between.

**If the native adopts Option C (both).** Twenty-nine questions, guaranteed contradictions, and no
tie-break rule. This is Option B's failure mode with extra bookkeeping.

#### What is blocked until this is ruled

- **Review §7 Phase 0.1** — *"Freeze L3-Q01–Q13 + the three §14 proving-set cases + one
  ordinary-period case, with today's answers recorded."*
- Because Phase 0.2 (P0 safety confirmation), 0.3 (five cost profiles) and 0.4 (the input/output/use
  matrix) all measure *against* a frozen baseline, **Phase 0's measurements have nothing to be
  measured against** until D5 is ruled. Phase 0 can start on 0.2 and 0.4 (both baseline-independent);
  0.1 and the recording of "today's answers" cannot.
- The **acceptance criteria** for every per-asset §6.4 packet, which must state consumer effects
  against something.

#### What this does NOT decide

- It does not **discard Lane E**. Its seven lane deliverables remain evidence (review §4, "What
  survives unchanged"), its traceability table remains the best asset-level map the campaign has,
  and its two named gaps remain open findings. Option A demotes it from *authority* to *audit*; it
  does not shelve it.
- It does not decide **the fixtures**. Which charts, which periods, which ordinary case — that is
  Phase 0.1's work under the ruled baseline.
- It does not decide whether **§2 may be amended**. It may; Option A's mapping step is the intended
  route, and a genuine orphan is an amendment proposal, not a defeat.
- It does not decide the **headline metric** — prior R2's `Data-accepted N/22` + `Delivered N/22`
  two-number restatement stands untouched. A baseline is what "answerable" means; the headline is
  what gets counted.
- It does not decide **who reviews** acceptance. §6.4 `:382-387` requires "an independent reviewer"
  per packet; naming them is separate.

#### Reversibility

**Fully reversible, cheapest on the sheet.** The baseline is a document with a version and a
changelog. Changing it later costs a re-measure of whatever Phase 0 recorded against the old one —
real, but bounded, and involving no data and no rebuild.

```
RULING D5: [ ] adopt   [ ] adopt with change   [ ] reject   [ ] defer — reason:
```

---

## §4 — Questions the native may reasonably ask back

**"If the L2 guard already blocks cross-layer deletes, why is Kāla's data being deleted at all?"**
Because nothing currently runs through the guard. `l2_data_plane_guard_active_mutation`
(`1036:1584-1588`) only fires for `session_user = 'data_plane_builder'` with a full
`madhav.l2_*` transaction context — and `data_plane_l2_producer_generations` has 0 rows, so no
generation has ever been opened. Today the plain FK `ON DELETE CASCADE` wins and Kāla is emptied.
The moment L2 runs a governed rebuild, `assert_l2_msr_delete_safe` (`1036:740-767`) fires instead
and the rebuild *fails* while Kāla rows exist. Two different failures, one before the switch and one
after. D1 is what makes both stop.

**"Can I rule D3 alone and get the safety benefit immediately?"** Yes for classes (i) and (ii) —
those are guards at the Clear route and the issuance path, both L3-reachable. **No for class (iii):**
`kala_bhavishya`'s outcomes are deleted by an FK CASCADE from `bodha_msr_signals`, which no Clear
guard sees. Protecting class (iii) in practice needs D1's substrate and the prior-R4 step-2 re-key.
D3 alone declares the obligation and closes two thirds of it.

**"Which one should I rule first if I only rule one tonight?"** **D3.** It is the only one that
transitively blocks the whole campaign (W0 gates W1 gates W2+), and it is the only one whose wrong
answer is permanent loss rather than rework. D1 second — it has the longest lead time and an
external dependency on L2. D5 third — it is what Phase 0's measurements need. D2 fourth, D4 last.

**"D1 says adopt a 4,325-line pattern. Is that a §N.2 orchestrator freeze exception?"** No. §N.2
freezes the `WriterBase`/orchestrator contract; 1035/1036 are DB substrate — tables, triggers and
functions — with no `WriterBase` change. Strategy `:167` states the same boundary explicitly:
*"Any proposed change to WriterBase/orchestrator requires a separately named architecture
decision."* If W1's design finds it *cannot* be done without a writer-contract change, §N.2 says
STOP and raise it with you. D1 does not pre-authorize that.

**"D2 sounds like a lot of columns. Can it be a JSONB blob?"** The contract does not care about
physical shape. Strategy `:84-85` says these are *"logical objects and relations, not a mandate to
create a new table or writer for every row."* What F06 `:33` forbids is the *collapse* —
`unavailable` and `inapplicable` reading identically. A JSONB payload that keeps them distinct
satisfies D2; a numeric column that cannot satisfies it in no shape.

**"Why not just take D4's Option C — I can qualify the method myself?"** You can, and F04 `:31`
admits `SOURCE_TESTIMONY` as a real epistemic class for exactly this. My recommendation against it
is a preference for a durable citation over a fast one, given Tājika Nīlakaṇṭhī is already in the
corpus needing only translation. It is the weakest recommendation on this sheet and I have said so
in D4's evidence. If you want W2 unblocked this week, Option C is defensible on the text.

**"Lane E did more verification than §2 did. Why does the less-verified document win?"** Because
they answer different questions. §2 says *what Kāla must be able to answer*, with an ablation proof
per question. Lane E says *what Kāla can answer today*, with an asset trace per question. The first
is a specification; the second is a measurement of it. Option A keeps both in their roles. What it
refuses is letting a measurement become the specification — which is how you end up unable to fail.

**"Three of these corrections say the review I commissioned got it wrong. Should I trust the
review?"** Yes, on its conclusions — all three findings I corrected leave the review's verdict
standing and in two cases make it more urgent. What I corrected were *mechanisms*: the review
inferred the Clear hazard from `target_table` without reading the route's resolution order, and it
framed generations as an open choice without reading migration 1036's cross-layer guard. That is
the normal cost of a review written at document-level. The rule that caught all three is the one
the review itself stated: verify at the authority, never by re-running the claim's own query.

**"What did you not check?"** Named in-place as `COULD NOT VERIFY` in each decision. The four that
matter: (1) whether an L2 build currently succeeds or fails under the armed guard — requires a write;
(2) whether a layer-Clear on `kala` actually executes the derived DELETE end-to-end — requires a
write; (3) whether any runtime caller invokes `query_tithi_pravesha` — traced to registration, not
to invocation; (4) whether all sixteen Lane E questions map onto the thirteen — that is Phase 0.1's
work, not this sheet's. I also did not verify PR #2712's state (the GitHub connector failed to
authenticate this session); what I did verify is that
`KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md` is **not on `main`** (`git log --oneline -1 main --
<path>` returned empty).

---

## §5 — What this sheet does NOT establish

1. **It authorizes nothing.** No migration, no grant, no build, no code change, no row written. This
   session was read-only against production throughout and wrote exactly one file, uncommitted.
2. **It does not close the review.** Review §1's eight corrections (C1–C8), §2's seven additions
   (A1–A7) and §3's six drops (D1–D6) are not ruled here. Only §6's five decisions are prepared.
   The other twenty-one items remain as the review left them.
3. **It does not supersede the prior ruling sheet's R1, R2, R5 or R6.** Inheritance under t3, the
   headline metric, the PR #2695 dispatcher split and the builder grants stand untouched. R3 is
   amended only as to which baseline an admission note is written against (D5); R4 is superseded
   only as to its step 2's mechanism (D1/D3), with its rejection of `RESTRICT` reinforced rather
   than reversed.
4. **It does not judge the Jyotish correctness of any asset.** D4 is about whether a computation is
   *the admitted classical method*, not whether it is astronomically or interpretively right.
5. **It does not establish that the corrections in D1 and D3 are complete.** I found three defects
   the review missed by reading two code paths and one trigger catalogue. That is evidence the
   reading is productive, not evidence it is exhaustive. W0's asset/field/edge register
   (`Strategy:372`) is where completeness is supposed to be established.
6. **It does not measure anything the review measured without re-measuring it.** Every number in
   this sheet was taken live today against production, read-only, or read at `file:line`. Where a
   figure matches the review (38,287 v1 rows; 79 dangling predicates; 0 generations) that is
   independent corroboration, not a citation.
7. **It does not set a deadline.** Prepared early by design so the native can rule while Phase 1
   executes. Phase 0 (0.2, 0.4) and Phase 1 in full can proceed with none of the five answered.
8. **It does not constitute a session close.** No `session_close` checklist is emitted by this
   artifact; per CLAUDE.md §H that remains the session's own obligation.
