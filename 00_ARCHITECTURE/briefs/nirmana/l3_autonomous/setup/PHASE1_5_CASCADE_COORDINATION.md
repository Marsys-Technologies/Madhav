---
artifact: PHASE1_5_CASCADE_COORDINATION.md
canonical_id: L3_PHASE1_5_CASCADE_COORDINATION
version: "1.0"
status: CURRENT
produced_on: 2026-09-22
layer: L3 — Kāla (pre-elevation setup, Phase 1.5)
scope: coordination + documentation. No production write, no migration, no DDL, no code change.
authorised_by: >
  L3 pre-elevation setup Phase 1.5 (CASCADE COORDINATION). Explicitly NOT a new mechanism:
  the adjudication (D-CND-15/D-CND-16) and the tool (cascade_check.sql) already exist and
  belong to the Nirmāṇa campaign. This artifact coordinates with them and adopts the tool.
gated_out_of_scope: >
  Phase 2 structural fix (binding L3 rows to an L2 generation) is FROZEN at W0
  (FOUNDATION_SAFETY §6) and HELD on L3-W1-UPSTREAM-GENERATIONS-01 pending an RI-01
  precursor release. Neither re-decided nor implemented here.
changelog:
  - "1.0 (2026-09-22): first issue. Nirmāṇa state verified live; cascade_check.sql adopted
     unmodified; FK constraint set measured at pg_constraint; interim build-order rule agreed."
---

# Phase 1.5 — CASCADE COORDINATION

**Outcome in one line: this item is purely documentary. No code was written, the Nirmāṇa
tool was adopted unmodified, and no rival mechanism was built.** That is a real result, not
an absence of one — the instruction was to coordinate, and the coordination target turned out
to be alive, correct, and sufficient. The one thing that *is* new here is the build-order rule
in §5, and one previously-unrecorded gap in §6.

---

## §1 — The Nirmāṇa campaign's verified current state

Verified live rather than assumed. Every claim below carries file:line or the exact query.

### 1.1 The rulings — still CURRENT, and extended since

| Ruling | Location | Status |
|---|---|---|
| **D-CND-15** | `00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md:200-206` | CURRENT, not superseded |
| **D-CND-16** | `00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md:207-209` | CURRENT, not superseded |

`CAMPAIGN_STATE.md` frontmatter reads `status: LIVE` (`:1-8`). The campaign is not concluded.

**D-CND-15** (`CAMPAIGN_STATE.md:200-206`, verbatim sense): the campaign's DAG models
*ancestors* and the E-gate gates on ancestors; `ON DELETE CASCADE` makes *descendants* a
destruction surface that nothing in the E-gate, the run-slot protocol or a writer's own
idempotency helper models. Before any `rebuild_only` dispatch the owning session enumerates the
transitive CASCADE closure of every table its writer deletes from, and **holds if it crosses a
layer boundary**. A §N.3 in-layer delete-then-insert is only "in-layer" *if the FKs say so*.

**D-CND-16** (`CAMPAIGN_STATE.md:207-209`): a comment asserting a schema property is not
evidence of that property. Where safety depends on FK delete behaviour, **query the catalogue**.

The rulings have not been superseded, but the *tool* implementing them has been amended three
times since, each amendment documented in its own header:

- **D-CND-18** (2026-09-05, #1805) — `cascade_check.sql:47-57`. The no-FK scan under-reported;
  replaced name-equality matching with a type-and-shape candidate scan plus a live resolution
  check, and per-COLUMN (not per-table) FK exclusion.
- **D-CND-19** (2026-09-10, #2564) — `cascade_check.sql:59-69`. The orphan resolution check
  crashed a live Postgres backend against `kala_field` (11M rows); its own first fix was then
  killed by Cloud SQL's memory guardian.
- **D-CND-20** (2026-09-10, #2564 second ruling) — `cascade_check.sql:71-80`. Probe the target's
  native PK index directly; cast the candidate *value* toward the PK type, never the indexed side.

**This matters for adoption:** the tool is not a 2026-09-05 artifact that has sat still. It was
last changed `895e6253a` (2026-09-10, #2569) and is byte-identical to `origin/main` in this
worktree (`git diff origin/main -- platform/scripts/nirmana/cascade_check.sql` → empty).

### 1.2 The tool — where it lives and what it checks

`platform/scripts/nirmana/cascade_check.sql`, 306 lines. Invocation (`:6`):

```
psql "$DATABASE_URL" -v table=<your table> -f platform/scripts/nirmana/cascade_check.sql
```

Three independent queries, deliberately kept separate (the header at `:285-295` argues
explicitly that conflating them would misreport in both directions, citing §N.8):

1. **CASCADE closure** (`:87-131`) — recursive walk of `pg_constraint` where
   `contype='f' AND confdeltype='c'`, depth ≤ 8, with a per-row `IN-LAYER` /
   `CROSS-LAYER *** HOLD ***` verdict inferred from table-name prefixes.
2. **No-FK orphan scan** (`:178-283`) — the tables that *orphan* rather than cascade. Needs a
   session-local `TEMP TABLE`. See §2.2: this is the query that could not be run here.
3. **ON DELETE SET NULL** (`:297-306`) — `confdeltype='n'`. A *mutation* surface: rows survive,
   but the FK column is nulled and the provenance record with it.

### 1.3 Is it wired into anything? The live-path test

- **No automated caller found within scope searched** — repo-wide `grep -rn "cascade_check"`
  (excluding `node_modules`, `.git`), plus an explicit `grep -rn "cascade_check" .github/`.
  Every hit is either the file itself, campaign prose, or an operator runbook.
- It is **operator-invoked by protocol**, and that protocol is live: `SESSION_CHARTER_V21.md:221`
  and `sessions/resume/RESUME_L3.md:118,126` both instruct L3 sessions to run it. Its header
  (`:8`) says "RUN THIS BEFORE EVERY `rebuild_only` DISPATCH."
- **A related mechanism IS automated and does have a live caller**: `blast_radius()` at
  `platform/scripts/dispatch_nirmana_campaign_wave.py:759`, gated at `:1349-1372` (the "WP-6"
  gate). It re-implements *query 1 only* — the transitive CASCADE closure — and refuses to
  commit when `destroys_rows` is true without `--acknowledge-destroys`. It does **not**
  implement the orphan scan or the SET NULL scan.
- **The gap that matters most to L3, recorded in §6.1:** `platform/scripts/dispatch_frozen_rebuild.py`
  — the L3 lane's own single-asset rebuild dispatcher (`:1-14` describes itself as generalized
  from the L3 lane's `dispatch_ka_gochara_frozen.py`) — contains **no blast-radius gate at all**
  (`grep -n "blast_radius\|cascade\|destroys\|confdeltype\|acknowledge"` → no matches).

### 1.4 Evidence the tool is actively maintained, and deliberately left alone

`9b3c3b219` (2026-09-21, #2706) changed `egate.sql` and `capsule_audit.sql` in the same
directory — one day before this writing — and did **not** touch `cascade_check.sql`. The
directory is live and under active ownership. This is an additional reason adopting it
unmodified was the correct call: editing it from outside the Nirmāṇa campaign would have been
a change to a live shared surface owned by another campaign.

---

## §2 — What was adopted

### 2.1 Adopted as-is, unmodified

**`platform/scripts/nirmana/cascade_check.sql` is adopted as the L3 cascade-checking tool,
with no modification and no extension.** No rival mechanism was written. It covers what L3
needs: the L3 questions are exactly "what does a delete from this table destroy, what orphans,
and what gets nulled," which are its three queries.

No code change was made, so there is no test to fail-before/pass-after. Per the task's own
framing, this item is documentary; a code change here would have been manufactured.

### 2.2 What it reported, run read-only against production

Run `2026-09-22` against production, canonical chart context
`482012f1-710e-4a25-994a-93821f5871aa`.

**`-v table=bodha_msr_signals` — query 1 (CASCADE closure), whole-table live rows:**

| depth | cascade deletes from | layer | live rows | verdict |
|---:|---|---|---:|---|
| 1 | `kala_activation` | L3 | 337,148 | CROSS-LAYER HOLD |
| 1 | `kala_convergence` | L3 | 20,497 | CROSS-LAYER HOLD |
| 1 | `kala_darshana` | L3 | 750 | CROSS-LAYER HOLD |
| 1 | `kala_obstruction` | L3 | 747 | CROSS-LAYER HOLD |
| 1 | `kala_bhavishya` | L3 | 100 | CROSS-LAYER HOLD |
| 2 | `phala_anchors` | L4 | 60 | CROSS-LAYER HOLD |
| 3 | `phala_sankrama` | L4 | 630 | CROSS-LAYER HOLD |
| 3 | `phala_suddha_sodhana` | L4 | 60 | CROSS-LAYER HOLD |
| 3 | `phala_pramana` | L4 | 60 | CROSS-LAYER HOLD |
| 3 | `phala_sodhana` | L4 | 41 | CROSS-LAYER HOLD |
| 1 | `bodha_signal_embeddings` | L2 | 150,724 | IN-LAYER |
| 1 | `bodha_contradictions` | L2 | 45 | IN-LAYER |

Query 3 (SET NULL) for `bodha_msr_signals`: **0 rows**.

**`-v table=kala_convergence` — query 1:**

| depth | cascade deletes from | layer | live rows | verdict |
|---:|---|---|---:|---|
| 1 | `phala_anchors` | L4 | 60 | CROSS-LAYER HOLD |
| 2 | `phala_sankrama` | L4 | 630 | CROSS-LAYER HOLD |
| 2 | `phala_pramana` | L4 | 60 | CROSS-LAYER HOLD |
| 2 | `phala_suddha_sodhana` | L4 | 60 | CROSS-LAYER HOLD |
| 2 | `phala_sodhana` | L4 | 41 | CROSS-LAYER HOLD |
| 1 | `kala_darshana` | L3 | 750 | IN-LAYER |
| 1 | `kala_obstruction` | L3 | 747 | IN-LAYER |

**COULD NOT VERIFY: query 2 (the no-FK orphan scan) did not run in this lane.** It failed with
`ERROR: cannot execute CREATE TABLE in a read-only transaction` at `cascade_check.sql:178`,
cascading to `:179,180,279,283`.

Diagnosed rather than assumed. `SHOW default_transaction_read_only` → `on`; the setting comes
from this lane's own `PGOPTIONS` (set in `/Users/Dev/madhav-l3/dbenv.sh`), **not** from the
database role — `SELECT rolname, rolconfig FROM pg_roles WHERE rolname=current_user` returns
`amjis_app | {idle_in_transaction_session_timeout=600s,statement_timeout=1800s}`, with no
read-only entry, and there is no `pg_db_role_setting` row for the database.

So: **this is a limitation of this lane's read-only harness, not a defect in the tool.** A
Nirmāṇa operator on a normal connection is unaffected. The tool's own scratch space is
session-local `TEMP` (header `:2-4`, `:165-177`) and writes nothing durable. **The tool was
deliberately not modified to work around this lane's own safety guard** — doing so would be
altering another campaign's live shared instrument to suit my session, which is precisely the
wrong direction.

Consequence to carry: **no conclusion of "no orphans exist" may be drawn from this run.** The
specific L3 orphan surface was instead measured directly with plain read-only `SELECT`s (§4).

---

## §3 — The measured FK constraint set, and §4.2

Per D-CND-16, measured at `pg_constraint` rather than read from prose. The existing blast-radius
analysis is cited, not re-derived: `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md`
**§4.2** at `:164-180`, and `MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` **fence #7**
at `:761`. The route-level statement is at `00_ARCHITECTURE/briefs/nirmana/L3_C13_BLAST_RADIUS_v1_0.md:20-37`.

### 3.1 Children of `bodha_msr_signals` — 8 constraints, 7 tables, all `confdeltype='c'`

| constraint | child table | child column | del |
|---|---|---|---|
| `bodha_contradictions_signal_a_id_fkey` | `bodha_contradictions` | `signal_a_id` | c |
| `bodha_contradictions_signal_b_id_fkey` | `bodha_contradictions` | `signal_b_id` | c |
| `bodha_signal_embeddings_signal_id_fkey` | `bodha_signal_embeddings` | `signal_id` | c |
| `kala_activation_signal_id_fkey` | `kala_activation` | `signal_id` | c |
| `kala_bhavishya_signal_id_fkey` | `kala_bhavishya` | `signal_id` | c |
| `kala_convergence_signal_id_fkey` | `kala_convergence` | `signal_id` | c |
| `kala_darshana_signal_id_fkey` | `kala_darshana` | `signal_id` | c |
| `kala_obstruction_signal_id_fkey` | `kala_obstruction` | `signal_id` | c |

→ §4.2's claim (five `kala_*` tables plus L2 embeddings/contradictions): **CONFIRMED exactly.**

### 3.2 Children of `kala_convergence`

`kala_darshana.convergence_id` (c) · `kala_obstruction.convergence_id` (c) ·
`phala_anchors.convergence_id` (**c**) · `kala_bhavishya.convergence_id` (**n** — SET NULL).

→ §4.2's "deleting convergence cascades obstruction and Darshana, nulls Bhavishya convergence,
and cascades through `phala_anchors` into multiple L4 tables": **CONFIRMED exactly**, including
the SET NULL direction on Bhaviṣya.

### 3.3 Children of `kala_bhavishya`

`phala_anchors.bhavishya_id` (n). → §4.2's "deleting Bhavishya nulls `phala_anchors.bhavishya_id`":
**CONFIRMED.**

### 3.4 Children of `phala_anchors` — the L4 reach

| child table | column | del |
|---|---|---|
| `phala_pramana` | `anchor_id` | c |
| `phala_sankrama` | `source_anchor_id` | c |
| `phala_sodhana` | `anchor_id` | c |
| `phala_suddha_sodhana` | `anchor_id` | c |
| `phala_mitigation` | `linked_anchor_id` | **n** |
| `phala_muhurta` | `linked_anchor_id` | **n** |

### 3.5 Children of `kala_activation`, `kala_darshana`, `kala_obstruction`

**Zero.** No outbound FK of any delete action. These three are cascade sinks.

### 3.6 Divergence from §4.2 — one addition, no correction

**No correction to §4.2 was found. Its every specific claim measured true.**

One **addition**: §4.2 says the convergence delete "cascades through `phala_anchors` into
multiple L4 tables" — true, and four such tables are CASCADE. It does not record that **two
further L4 tables, `phala_mitigation` and `phala_muhurta`, are `ON DELETE SET NULL` children of
`phala_anchors`.** Those rows survive, so they never appear in a CASCADE closure and never trip
`destroys_rows` in the WP-6 gate — but their `linked_anchor_id` is silently nulled, and with it
the record of what they were derived from. `cascade_check.sql:285-295` argues exactly this case
and says to treat it as a real provenance cost reported separately. Recorded here so the next
reader of §4.2 has it; §4.2 is not wrong, it is incomplete on the mutation surface.

### 3.7 Fence #7, cited not re-derived

`MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md:761` — Bhaviṣya history: outcome-bearing
or `phala_anchors`-referenced matched rows are **immutable absent a generation schema**; a content
change **fails before DML**. Its cited evidence is real and fail-closed: the guard raises
`RuntimeError` before any write at `ka_bhavishya_lekha.py:133,192,200`, and probes for
`phala_anchors` references at `:243-262` before deciding. The fence has a detector behind it —
it is not a §N.8 unearned signal.

---

## §4 — The cascade already fired, and what it missed

### 4.1 The five FK-bound tables — empty, and the cockpit still reports otherwise

Canonical chart `482012f1-710e-4a25-994a-93821f5871aa`, live counts:
`kala_activation` **0** · `kala_bhavishya` **0** · `kala_convergence` **0** ·
`kala_darshana` **0** · `kala_obstruction` **0**.

`asset_throughput` for the same chart:

| asset | state | rows_written |
|---|---|---:|
| `ka_kalasutra` (→ `kala_activation`) | stale | 335,403 |
| `ka_sangam` (→ `kala_convergence`) | stale | 14,868 |
| `ka_kala_darshana` (→ `kala_darshana`) | stale | 750 |
| `ka_vighnakara` (→ `kala_obstruction`) | stale | 536 |
| `ka_bhavishya_lekha` (→ `kala_bhavishya`) | stale | 100 |

One honest nuance worth recording rather than glossing: **`state` reads `stale`, not `lit`.**
The cockpit is not claiming these assets are built. But `rows_written` still carries the
pre-cascade figure, and nothing recomputes it — there is no detector behind `rows_written` for
"do these rows still exist" (§N.8). A reader taking `rows_written` as current is misled; a
reader taking `state` at face value is not.

### 4.2 The three tables the cascade did NOT reach — verified before restating

Both facts a parallel lane reported were **independently re-measured here, not restated**.

**Catalogue (no MSR FK — confirmed):**

| table | FKs to `bodha_msr_signals` | total FKs |
|---|---:|---:|
| `kala_activation_predicates` | 0 | 0 |
| `kala_taranga` | 0 | 0 |
| `kala_jivana_parva` | 0 | 1 (not to MSR) |

**Canonical-chart rows still held:** `kala_activation_predicates` **50,678** ·
`kala_taranga` **92,412** · `kala_jivana_parva` **100**.

**Dangling references, measured directly:**
- Canonical chart, predicates whose `signal_id` is absent from same-chart MSR: **79** — confirms
  the parallel lane exactly.
- Same 79 are absent from `bodha_msr_signals` *entirely*, on any chart — so this is a genuinely
  dead reference, not a cross-chart artifact.
- All charts: **49,809** — confirms the parallel lane exactly.
- `bodha_msr_signals` itself holds **50,678** rows for the canonical chart: MSR was rebuilt, and
  79 signal ids did not survive the rebuild while their dependent predicates did.

**Live-path test — all three are genuinely served:**
- `kala_activation_predicates` → `platform-mcp/src/tools/kala_views/ahead.ts`,
  `platform-mcp/src/tools/kala_views/now.ts` (read-only citation; `kala_views/` is Pūrṇa-owned
  and was not edited).
- `kala_jivana_parva` → `platform-mcp/src/tools/kala_views/story.ts`,
  `.../ahead.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`.
- `kala_taranga` → `platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts`;
  `platform/python-sidecar/services/taranga_service.py`.

### 4.3 What that implies — the tables the cascade missed matter more

The five tables the cascade emptied fail **loudly**: 0 rows is an honest empty, and any surface
reading them returns nothing rather than something wrong. That is the §N.6/§N.7 preferred
failure — an honest null over an invented judgment.

The three tables it missed fail **quietly**. They still hold rows, still hold derived values
computed from signals that no longer exist, and are still served to live callers. 79 of 50,678
is 0.16% — small enough never to surface as an outage, large enough to be wrong. **The FK
cascade, by destroying its children, produced the honest failure; the absence of an FK produced
the dishonest one.** An ordering rule cannot detect this class at all, which is why §5's R6
exists and why §6 says only Phase 2 closes it.

---

## §5 — The agreed interim build-order rule

Grounded in the FK direction measured in §3 and in fence #7 (§3.7). **Procedural, not
structural** — see §6 before relying on it.

### R0 — Ordering invariant

`bodha_msr_signals` is the root of every dependency measured in §3.1. **Never rebuild
`bodha_msr_signals` and any `kala_*` asset in the same window.** After *any* MSR rebuild, all
five FK-bound `kala_*` tables are empty for that chart and must be rebuilt before any surface
reading them is trusted; and the three no-FK tables (§4.2) must be rebuilt too **even though
they still hold rows** — they are the silent-corruption surface, not the safe one.

### R1 — Check before every rebuild

For **every table the writer deletes from**, run the adopted tool:

```
psql "$DATABASE_URL" -v table=<table> -f platform/scripts/nirmana/cascade_check.sql
```

Run it on a connection that permits `TEMP` tables. If query 2 errors with
`cannot execute CREATE TABLE in a read-only transaction`, the orphan scan **did not run** —
record that, and do **not** infer "no orphans" from its absence (§2.2).

### R2 — Verdict handling (D-CND-15, unchanged)

Any `CROSS-LAYER *** HOLD ***` row → **do not rebuild.** Snapshot, file an adjudication naming
the owning layer, obtain a ruling. Only an all-`IN-LAYER` result proceeds without adjudication.
The gate is on **layer-crossing, not on measured scale** — L2 explicitly declined to
self-authorise past this on a "probably fine, only 2,442 rows" argument
(`sessions/L2_STATE.md:754`), and that precedent binds here.

### R3 — Build order for a full L3 rebuild of one chart

Derived from §3's measured FK direction: cascade sources before sinks, parents before children.

1. **`bodha_msr_signals` (L2)** — only if L2 itself requires it, and only under R2. It is
   upstream of everything below.
2. **`ka_sangam` → `kala_convergence`** — the *only* L3 asset with an L4 reach (§3.2). Requires
   R2 clearance from L4 **every time**, not once.
3. **`ka_kala_darshana` → `kala_darshana`** and **`ka_vighnakara` → `kala_obstruction`** — both
   are CASCADE children of `kala_convergence`, so they must follow it, never precede it.
4. **`ka_kalasutra` / `ka_yojaka` → `kala_activation`** (+ `kala_activation_predicates`, which
   `ka_yojaka` also deletes from — `writers/ka_yojaka.py`). `kala_activation` is a cascade sink
   (§3.5), so this step destroys nothing downstream.
5. **`ka_bhavishya_lekha` → `kala_bhavishya` LAST among the FK-bound set.** Fence #7 makes it
   fail-closed on any changed outcome-bearing or `phala_anchors`-referenced row. Running it last
   means its inputs are settled, so a failure is a real signal rather than an ordering artifact.
6. **`ka_taranga`, `ka_jivana_parva`** — after all of the above. They carry no FK to force the
   issue (§4.2) and derive from values the steps above produce, so nothing but this ordering
   makes them correct.

### R4 — What must never run concurrently

- Any L2 MSR rebuild with **any** L3 writer.
- `ka_sangam` with `ka_kala_darshana` or `ka_vighnakara` (shared cascade ancestor).
- Any L3 rebuild with an L4 `ph_*` build reading `phala_anchors`.

The database already enforces **one active run per chart**
(`build_runs_one_active_per_chart_idx`, observed in `sessions/L2_STATE.md:729`). That is a real
structural backstop for same-chart concurrency — but it **orders nothing**, and does not reach
cross-chart or cross-layer sequencing. Do not mistake it for this rule.

### R5 — Operator action when the check fails

1. **Stop before dispatch.** Do not proceed on a scale argument.
2. Take a **verified** snapshot — verify via `gcloud sql backups list`, not the create command's
   own output (the L2 precedent, `sessions/L2_STATE.md:783`).
3. Obtain the owning layer's confirmation **in writing that its data is regenerable, before the
   snapshot is spent.**
4. File the adjudication naming the owning layers.
5. Only then re-run the check and proceed. Never self-authorise `--acknowledge-destroys`.

### R6 — Verify the no-FK surfaces after every rebuild, because nothing else will

The dangling-predicate query of §4.2 is the pattern; run it for `kala_activation_predicates`,
`kala_taranga` and `kala_jivana_parva`. A dangling count that has **increased** means the
rebuild orphaned further references. Current baseline to compare against: **79** for the
canonical chart, **49,809** across all charts.

---

## §6 — Limits, stated plainly

**This is a procedural control, not a structural guarantee.** Every clause above is advisory.
The database will execute any order an operator chooses. The rule does not survive an operator
who does not follow it, a script that dispatches without reading it, or a session that has never
opened this file.

### 6.1 The largest hole: the L3 lane's own dispatcher has no gate

The campaign's only *automated* cascade guard is WP-6 in
`platform/scripts/dispatch_nirmana_campaign_wave.py:1349-1372`. **`platform/scripts/dispatch_frozen_rebuild.py`
— the L3 lane's own single-asset rebuild dispatcher — has no blast-radius check of any kind.**
So on the exact path an L3 elevation rebuild is most likely to take, R1 and R2 are enforced by
operator discipline alone.

This is not closed here. Closing it would mean either building a second cascade mechanism
(forbidden by this item's own terms) or changing another campaign's dispatcher. It is recorded
as a finding and handed on.

### 6.2 What the rule does not protect against

- **Concurrent rebuilds from different worktrees or sessions**, especially on different charts —
  the per-chart run-slot index does not reach them.
- **A rebuild that succeeds but produces different `signal_id`s.** This is what actually happened:
  the 79 dangling predicates (§4.2) came from a *successful* MSR rebuild. No ordering can prevent
  it, because nothing was done out of order.
- **Silent staleness of the three no-FK tables** between rebuilds. R6 detects it after the fact;
  nothing prevents it.
- **A partial or failed rebuild** leaving a chart half-populated.
- **Irreversibility.** A snapshot exists but **a restore has never been exercised** —
  `CAMPAIGN_STATE.md:192-195` states this honestly, it remains true, and this session did not
  exercise one either.

### 6.3 Limits of the tool itself

- Query 1 reports **whole-table** `live_rows`, not chart-scoped. It reported `kala_activation`
  337,148 while the canonical chart holds **0**. For a per-chart rebuild that number overstates
  the loss; scope it yourself before acting on it.
- Query 2's orphan scan is **sampled** (500 values per candidate, `cascade_check.sql:264`). Its
  header is explicit: it finds a real orphan surface with high confidence, it does **not** prove
  the absence of one.
- Query 2 did not run in this lane at all (§2.2).

### 6.4 Only Phase 2 fixes this

An ordering convention cannot express *"these L3 rows belong to that L2 generation."* Until L3
rows carry a generation reference to the L2 rows they derive from:

- a correct rebuild in the wrong order and an incorrect rebuild are **indistinguishable after the
  fact**; and
- the no-FK tables **cannot be told they are stale** — there is no generation to compare against,
  which is exactly why 79 rows have been served over dead references without anything noticing.

That design is FROZEN at W0 (`FOUNDATION_SAFETY §6`) and its implementation is HELD on
`L3-W1-UPSTREAM-GENERATIONS-01` pending an RI-01 precursor release. **This rule is a stopgap
until that lands. It is not an alternative to it, and it should not be cited as one.**

---

## §7 — Collision risk with the other campaign's open work

Checked via `gh pr list` (16 open PRs) on 2026-09-22.

- **No open PR touches `platform/scripts/nirmana/cascade_check.sql`.** Adoption collides with
  nothing.
- **#2713** (`l3/kala-elevation-readiness`) — the sibling L3 lane. Touches
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/` docs, but no file under `setup/`. This artifact
  is a new file at `l3_autonomous/setup/PHASE1_5_CASCADE_COORDINATION.md` — **no path overlap.**
- **#2695** (`codex/madhav-l3-claude-code`) — **the one real collision risk.** It modifies
  `platform/scripts/dispatch_frozen_rebuild.py`, the exact dispatcher §6.1 finds gate-less, and
  also touches `l3_autonomous/STATE.md` and `EVENTS.jsonl`. No overlap with this file, but **the
  §6.1 finding must be re-checked against #2695's merged state** — it was measured against
  `origin/main` at `c58e86662`.
- **The Nirmāṇa tooling directory is actively maintained**: #2706 changed `egate.sql` and
  `capsule_audit.sql` on 2026-09-21, one day before this writing. Any future edit to
  `cascade_check.sql` from an L3 lane would be a change to a live surface owned by another
  campaign and should be raised with them rather than committed.
- **The Nirmāṇa L2 session is still running** (the main checkout carries `L2 cycle #82` commits).
  Any rebuild recommended by §5 would contend with that campaign's run slots, and R4's
  concurrency clauses apply across campaigns, not just within this lane.

---

## §8 — What could not be verified

1. **`cascade_check.sql` query 2 (no-FK orphan scan) — COULD NOT VERIFY in this lane.** Blocked
   by this lane's own read-only `PGOPTIONS` guard, which forbids the session-local `TEMP TABLE`
   the scan requires. Root cause diagnosed (§2.2), tool not defective, not worked around.
   Compensated by direct read-only measurement of the specific L3 orphan surface (§4.2), which is
   narrower than a schema-wide scan.
2. **Snapshot restorability — not verified, by anyone.** Carried forward from
   `CAMPAIGN_STATE.md:192-195`, unchanged.
3. **Whether §6.1's gate-less finding survives #2695.** Measured against `origin/main` at
   `c58e86662`; #2695 is open and modifies that file.
