# Domain D — Generation / W1 substrate

Kāla Readiness Audit — packet "Domain D — Generation / W1 substrate"
Scope: the generation-head data-plane substrate (migrations 1035/1036) the L3 build
pipeline would depend on.

---

## Check 1 — What do the "1035/1036" functions actually do

Files found:
- `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql`
  ("data_plane_l1_producer_history" — DP-SD series)
- `platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql`
  ("data_plane_l2_producer_generations" — DP-SD-015)

These are **not** simple generation-head "advancement" functions. They install a full
exact-context, append-only, immutable snapshot/replay/rollback substrate per layer:

- 1035 (L1 / Gaṇita): tables `l1_data_plane_generations`,
  `l1_data_plane_generation_partitions`, `l1_data_plane_partition_contexts`,
  `l1_data_plane_row_snapshots`, `l1_data_plane_fact_snapshots`,
  `l1_data_plane_dasha_snapshots`, `l1_data_plane_configuration_snapshots`,
  `l1_data_plane_generation_heads`; functions `open_l1_data_plane_generation`,
  a row-capture trigger `l1_data_plane_capture_row`, `complete_l1_data_plane_partition`,
  `select_l1_data_plane_generation`, `rollback_l1_data_plane_generation`, plus
  immutability-enforcement triggers on every snapshot table.
- 1036 (L2 / Bodha): parallel structure —
  `data_plane_l2_producer_generations`, `l2_data_plane_generation_partitions`,
  `l2_data_plane_generation_runs`, `l2_data_plane_run_rows`,
  `l2_data_plane_partition_contexts`, `l2_data_plane_run_intents`,
  `l2_data_plane_input_bind_receipts`, `l2_data_plane_row_snapshots`,
  `l2_data_plane_generation_heads`, `l2_data_plane_asset_outputs`; functions
  `open_l2_data_plane_generation`, `bind_l2_exact_inputs`,
  `complete_l2_data_plane_partition`, `select_l2_data_plane_generation`,
  `rollback_l2_data_plane_generation`.

The generation *head* (`current_generation_id` in `l1_/l2_data_plane_generation_heads`)
only advances as a side effect of `complete_l1_data_plane_partition` /
`complete_l2_data_plane_partition` once **every** expected partition for a generation
has been recorded (see Check 4). So "generation-head advancement" is real, but it is
one small piece of a much larger exact-provenance/replay/immutable-history system —
not a standalone counter-bump function.

1036's own header comment is explicit: *"No row is backfilled and no L3 activation
authority is introduced."* — i.e. 1036 self-declares it does not extend this substrate
to L3.

Commands run:
```
find platform/migrations -maxdepth 1 -name "1035*" -o -name "1036*"
find platform -path "*migrations*" \( -name "1035*" -o -name "1036*" \)
```
(files live at `platform/supabase/migrations/`, not `platform/migrations/`)

**Verdict: informational — confirmed scope.** These are exact-provenance generation
substrates for L1 and L2 only; no L3 involvement is claimed or found.

---

## Check 2 — Does the gating actually enforce `session_user = 'data_plane_builder'`?

Confirmed. Exact predicates, quoted:

- `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql:579-581`
  (inside `open_l1_data_plane_generation`):
  ```sql
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L1 generation open requires direct data_plane_builder authentication';
  END IF;
  ```
- `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql:760-762`
  (inside the row-capture trigger `l1_data_plane_capture_row`):
  ```sql
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L1 governed capture requires direct data_plane_builder authentication';
  END IF;
  ```
- `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql:1326-1328`
  (inside `complete_l1_data_plane_partition`): same predicate/message pattern
  ("L1 partition completion requires direct data_plane_builder authentication").
- `platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql:948-950`
  (inside `open_l2_data_plane_generation`): identical pattern for L2.
- `platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql:804-806`
  (`bind_l2_exact_inputs`) and `:704-706`/`:712-713` (`assert_l2_msr_delete_safe`):
  same `session_user <> 'data_plane_builder'` guard.

A **separate, distinct** role gates rollback specifically:
- `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql:1623-1625`
  (`rollback_l1_data_plane_generation`):
  ```sql
  IF session_user <> 'data_plane_migrator' THEN
    RAISE EXCEPTION 'L1 rollback requires direct data_plane_migrator authentication';
  END IF;
  ```
- `platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql:1524-1526`:
  identical for L2, role `data_plane_migrator`.

All of these are `SECURITY DEFINER` functions with `SET search_path = pg_catalog,
public, pg_temp` — the role check is the actual authorization boundary, not row-level
security.

Commands run:
```
grep -rln "session_user" --include="*.sql" platform/supabase/migrations/
grep -n "session_user" platform/supabase/migrations/1035_*.sql platform/supabase/migrations/1036_*.sql
```

**Verdict: CONFIRMED as designed** — write/build paths require `data_plane_builder`;
rollback requires the separate `data_plane_migrator` role. This is a real, enforced
gate, not decorative.

---

## Check 3 — Real head tables: existence, row counts, columns

Live query:
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE '%generation_heads%';
```
Result: `l1_data_plane_generation_heads`, `l2_data_plane_generation_heads` — both exist.
No L3 equivalent (see Check 5).

Row counts (live):
```sql
SELECT 'l1', count(*) FROM public.l1_data_plane_generation_heads
UNION ALL SELECT 'l2', count(*) FROM public.l2_data_plane_generation_heads;
```
Result: **l1 = 0, l2 = 0.**

Follow-up (to characterize what "0" means — has the mechanism ever been exercised at
all, even without a completed generation?):
```sql
SELECT 'l1_generations', count(*) FROM public.l1_data_plane_generations
UNION ALL SELECT 'l1_generations_complete', count(*) FROM public.l1_data_plane_generations WHERE status='complete'
UNION ALL SELECT 'l2_generations', count(*) FROM public.data_plane_l2_producer_generations
UNION ALL SELECT 'l2_generations_complete', count(*) FROM public.data_plane_l2_producer_generations WHERE state='complete';
```
Result: **all four = 0.** Not one generation has ever been opened (let alone
completed) for any chart/asset, in either L1 or L2, under this substrate.

Columns (`\d`), identical shape for both tables:
```
chart_id                uuid            not null
asset_id                text            not null
current_generation_id   text            not null
previous_generation_id  text
selected_at             timestamptz     not null   default clock_timestamp()
```

**Verdict: tables exist and are schema-correct, but are functionally unexercised in
production** — zero generations opened, zero completed, zero heads. This substrate has
never been used end-to-end on this environment (dev/proxy DB reached via dbenv.sh —
see caveat in Overall Verdict).

---

## Check 4 — First-ever generation: what can it roll back to if aborted mid-build?

Traced `complete_l1_data_plane_partition` (`1035_...sql:1305-1513`) and
`rollback_l1_data_plane_generation` (`1035_...sql:1611-1646`); parallel L2 logic at
`1036_...sql:1293-1482` (`complete_l2_data_plane_partition`) and `1036_...sql:1513-1552`
(`rollback_l2_data_plane_generation`).

**When does the head get created/advanced?** Only inside `complete_*_partition`, and
only once the *last* expected partition lands:
```sql
-- 1035_...sql:1417-1423
IF v_completed < v_expected THEN
  UPDATE public.l1_data_plane_generations
  SET completed_partitions = v_completed
  WHERE ...;
  RETURN;                      -- early return: head is NOT touched
END IF;
...
-- 1035_...sql:1501-1512 (only reached once v_completed = v_expected)
INSERT INTO public.l1_data_plane_generation_heads (...)
ON CONFLICT (chart_id, asset_id) DO UPDATE SET ...;
```
So a partially-completed generation (some but not all partitions done) never touches
`l1_data_plane_generation_heads` at all.

**What does rollback require?**
```sql
-- 1035_...sql:1633-1638
SELECT current_generation_id INTO v_current
FROM public.l1_data_plane_generation_heads
WHERE chart_id = p_chart_id AND asset_id = p_asset_id
FOR UPDATE;
IF v_current IS NULL THEN
  RAISE EXCEPTION 'asset % has no selected generation', p_asset_id;
END IF;
```
`rollback_*_data_plane_generation` also requires the **rollback target itself** to
already be `status/state = 'complete'` (line 1626-1631 / 1527-1532) — rollback moves
the head pointer between two already-complete generations; it does not undo a partial
build.

**Functional answer for a first-ever L3 generation aborted mid-build:**
1. Because the head row is only inserted at full completion, a first-ever generation
   for a (chart_id, asset_id) pair that aborts mid-build **never creates a head row**.
   `rollback_*_data_plane_generation` is therefore literally unusable in this exact
   scenario — it raises `'asset % has no selected generation'` the moment you'd want
   to invoke it, because there is nothing to roll back *from*.
2. This is not actually dangerous from a "wrong data served" standpoint: every
   consumer path that matters (`select_l1_data_plane_generation`,
   `l1_data_plane_current_rows`/`current_dashas`/`current_facts`/`current_configurations`
   views, `bind_l2_exact_inputs`) either filters on `status/state = 'complete'` or joins
   through the head table — both are empty/absent for the aborted generation, so
   nothing downstream ever sees or serves the partial data. Post-abort state is
   observationally identical to pre-build state for any *reader*.
3. However there **is no explicit safe rollback point** in the sense the charter
   question implies — there is no "rollback to nothing" or "abandon generation" call.
   The real recovery path is **resume, not rollback**: `open_l1_data_plane_generation`
   is idempotent (`ON CONFLICT (chart_id, asset_id, generation_id) DO NOTHING` at
   line 685, and re-declaring an already-declared partition is `ON CONFLICT DO
   NOTHING` at line 710) — a caller can reopen the *same* `generation_id` and resume
   from the partitions not yet completed.
4. The partial state already recorded (rows in `l1_data_plane_row_snapshots`,
   `l1_data_plane_partition_contexts`, `l1_data_plane_generation_partitions`, and the
   parent `l1_data_plane_generations` row itself, stuck permanently in `status =
   'building'` if the build is abandoned rather than resumed) is **append-only and
   immutable** (`l1_data_plane_reject_immutable_change` trigger forbids UPDATE/DELETE
   on the snapshot tables; the generation-row trigger forbids DELETE outright and
   forbids UPDATE once complete). Searched for an abandon/cancel/expire/GC function
   (`grep -n "abandon\|discard\|CREATE OR REPLACE FUNCTION public\.\(abandon\|expire\|gc_\|cancel\|cleanup\)"`
   across both files) — **none exists.** So an abandoned (not resumed) first-ever
   generation leaves permanently orphaned rows with no reclaim path; they are inert
   (never selected/served) but not erasable and not markable as failed/void.

**Verdict:** there is no dedicated "rollback the aborted first generation" operation,
and the one rollback function that exists is provably unusable in this exact
first-ever/mid-abort case (no head to roll back from). The design compensates via
resumability + read-side filtering (partial data is never served), not via rollback.
Orphaned partial state is retained forever with no cleanup function found.

---

## Check 5 — Does an L3-specific generation head table exist yet?

```sql
SELECT tablename FROM pg_tables
WHERE tablename LIKE '%l3%generation%' OR tablename LIKE '%kala%generation%';
```
Result: **empty — no rows.**

Cross-checked in source too:
```
grep -rln "generation_heads" --include="*.sql" platform/migrations/    → (none; wrong dir)
grep -rln "generation_heads" --include="*.sql" platform/supabase/migrations/
  → 1035_data_plane_l1_producer_history.sql
  → 1036_data_plane_l2_producer_generations.sql
```
Only L1 and L2 have this generation-head mechanism. A separate, older, unrelated
mechanism named `*_gochara_generation*` exists (`527_kala_gochara_generation_authority.sql`,
`541_kala_gochara_v2_build_state.sql`, `542_kala_gochara_windows_v2.sql`,
`556_gochara_generation_schema.sql`, `560_ka_gochara_v3_century_materialize_seed.sql`,
`562_gochara_v3_dag_integration.sql`, `566_parishkara_mr06_gen3_protection.sql`) — this
is the retired `ka_gochara_sweep` asset's own bespoke "generation" concept (transit
sweep materialization versioning), unrelated to the exact-context DP-SD-021
generation-head/snapshot/rollback substrate audited here. It should not be conflated
with an "L3 generation head" for this campaign's purposes.

**Verdict: NO generation substrate of this design exists for L3 yet.** 1036's own
comment (Check 1) confirms this is intentional/current-scope, not an oversight:
*"no L3 activation authority is introduced."* If the L3 Kāla data-plane elevation
campaign intends to adopt this exact-context generation-head pattern, that adoption
(a migration analogous to 1035/1036, e.g. an `l3_data_plane_...` set) has not been
authored. If L3 instead relies on a different mechanism (e.g. the orchestrator's own
`asset_throughput`/`build_runs` state per CLAUDE.md §N.8, or none at all), that is a
separate question this packet did not chase further — but as stated, no generation
head table keyed to L3/Kāla exists.

---

## Overall verdict: **NEEDS DECISION**

Rationale:
- The 1035/1036 substrate is real, well-built, and its `session_user =
  'data_plane_builder'` / `data_plane_migrator` gating is genuinely enforced (Checks
  1–2) — this part is READY as designed.
- But it is scoped to **L1 and L2 only**, by explicit self-declaration in 1036's own
  header comment, and confirmed empty of any L3 table live (Check 5). If the L3 Kāla
  campaign's build pipeline is assumed to already have (or trivially inherit) this
  generation-head substrate, that assumption is false as of this audit.
- The substrate is also **entirely unexercised in production** on the environment
  reached via `dbenv.sh` — 0 rows in every generation/head table for both L1 and L2
  (Check 3). Whatever chart-build activity has happened on this environment did not
  go through `open_l1_data_plane_generation`/`open_l2_data_plane_generation` at all.
  This is either (a) expected because those adapters aren't deployed/wired yet, or
  (b) a sign this whole mechanism is dormant/unused scaffolding — this audit cannot
  distinguish the two from schema + row counts alone, hence NEEDS DECISION rather than
  a clean READY or NOT READY.
- The first-ever-generation rollback question (Check 4) has a coherent answer (resume,
  not rollback; partial data is never served) but it is a *designed* answer that has
  never been proven under a real abort, given zero generations have ever been opened.

**The one piece of evidence that would have flipped this to a clean READY:** live
proof of at least one `status/state = 'complete'` generation row in
`l1_data_plane_generations` or `data_plane_l2_producer_generations` for the canonical
chart (`482012f1-710e-4a25-994a-93821f5871aa`), showing the mechanism has actually run
end-to-end at least once. **The one piece of evidence that would have flipped this to
a clean NOT READY:** a broken/contradictory role-gate (e.g. `open_l1_data_plane_generation`
callable without `data_plane_builder`) or a live L3 head table with rows that
disagreed with this schema. I checked for both — the gate is intact (Check 2, quoted
predicates) and no L3 table exists at all (Check 5, empty query result) — so neither
failure condition is present; what remains is the honest "no evidence either way yet"
gap that makes this NEEDS DECISION rather than a guess in either direction.
