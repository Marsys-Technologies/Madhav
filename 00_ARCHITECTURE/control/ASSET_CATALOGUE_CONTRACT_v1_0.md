---
canonical_id: ASSET_CATALOGUE_CONTRACT
version: 1.0
status: DRAFT
authored_by: KĀRAKA (Nirmāṇa autonomous campaign, task M0-T2)
authored_at: 2026-08-23
certified_by: null   # I16/H7 — the author does not certify. PARĪKṢAKA + ADHIKĀRIN countersign.
supersedes: null
derives_from:
  - NIRMANA_ELEVATION_PLAN_v4_0.md §3 (v4.2) — the two field additions `domain` and `rung`
  - NIRMANA_ELEVATION_PLAN_v3_0.md §3.1–§3.6 — lifecycle, de-duplication, required-fields matrix,
    consumer map, SOURCE classification (carried forward unchanged)
  - CLAUDE.md §B.8 (versioning discipline), §N.1 (asset-id prefix), §N.4 (floors aspirational,
    cockpit truth), §N.8 (earned signal)
schema_baseline: asset_registry, public schema, measured live 2026-08-23 (see §9)
enforcement_status: >-
  IMPLEMENTED, WIRED, NOT GATING — corrected 2026-08-23 (M0-T32).
  `platform/scripts/governance/check_asset_catalogue_contract.py` (shipped by M0-T9,
  2026-08-23T05:14:37Z) implements all 28 §6/§8 rules plus 5 campaign-extension rules
  X-01…X-05, AND cross-checks itself against this document's §6 table (28/28 parsed,
  0 problems, verified 2026-08-23T07:29Z). It is invoked from
  `.github/workflows/nirmana-m0-guards.yml`. It is NOT gating: both jobs carry
  `continue-on-error: true` (deliberately, per M0-T9; flipping it is ADHIKĀRIN's G9 call),
  and the guard and workflow are ABSENT from `origin/main` (verified 2026-08-23T07:03Z by
  M0-T31). So: a detector exists and runs on demand; nothing it says blocks anything yet.
  Live verdict 2026-08-23T07:27Z: pass=13 fail=16 not_checkable=4; 15 BLOCKING failures.
enforcement_status_superseded: >-
  Until 2026-08-23 this field read "NOT YET ENFORCED — no CI guard implements this document
  as of v1.0. §8 is written so that one can be, without interpretation." That was true at
  authoring (M0-T2) and false from M0-T9 onward. Corrected in place rather than softened;
  the replacement above states which of the three halves — implemented / wired / gating —
  is actually true, because "enforced" collapses a distinction that matters here.
changelog:
  - version: 1.0
    date: 2026-08-23
    change: >
      First authoring. The v3.0 §3 contract and v4.1's two field additions rendered as a
      per-kind enforceable specification: for every field, its column type, allowed values,
      the condition under which it is REQUIRED, and the condition under which it MUST BE NULL.
      §8 states every conformance rule as a named assertion with the SQL predicate that
      detects its violation, and records the measured live violation count for each as of the
      baseline date. §10 lists the four questions this document could not settle without an
      ADHIKĀRIN ruling and leaves them explicitly undecided rather than guessing.
---

# The Asset Catalogue Contract v1.0 — enforceable per-kind specification

## §0 — What this document is, and what it is not

**Is:** the registration requirement for a row in `public.asset_registry`. Every rule in §8
is stated as a boolean assertion over that table with the SQL that detects its violation. A CI
guard is written by transcribing §8; nothing in §8 requires a judgment call to implement.

**Is not:** a build gate, a correctness claim about any asset's data, or a certification. This
document says what a well-formed *registration* looks like. Whether the data behind a
registration is right is `integrity_check_sql`'s job (§4.7), and whether that check passed is
the integrity-gate engine's verdict (Track M3) — never this document's, and never an author's.

**Standing rule inherited from CLAUDE.md §N.8 / plan I5:** every field in this contract whose
value asserts a status must have been produced by a detector that measures that specific
assertion. A field this contract marks REQUIRED and that no detector can populate honestly is
left NULL and reported as a gap. NULL is a legal, honest value everywhere the contract does not
require otherwise; an invented value never is.

---

## §1 — The classification axes

Four independent axes classify a registry row. Confusing them is the defect this contract
exists to prevent.

| Axis | Column | Values | Set by | Meaning |
|---|---|---|---|---|
| **Kind** | `asset_kind` | `data` · `service` · `artifact` · `source`¹ | the author, from the writer's nature | *What sort of thing it is.* Governs which fields are required. **The single authoritative classification column** (v3.0 §3.4). |
| **Lifecycle** | `catalog_status` (+ `superseded_by`, `data_disposition`) | `CURRENT` · `DRAFT` · `RETIRED` | ADHIKĀRIN (G1) | *How much authority the row carries.* §3. |
| **Domain** | `domain` | `shared` · `chart` | derived 1:1 from `scope` (§5.1) | *Where the data lives.* The planner's split axis (plan §6.2). Never chosen at dispatch time. |
| **Rung** | `rung` | `R0`…`R5` | derived 1:1 from `layer` (§5.2) | *Ladder position.* Sequences the campaign (plan §8.4). |

¹ `source` is specified by v3.0 §3.4 as a kind but is **not currently a permitted value** of the
live `asset_registry_asset_kind_check` constraint. See §10.1 — undecided, not assumed.

`asset_type` (`data` · `service`) is a **legacy** column predating `asset_kind` (seed comment:
"Migration 202+ fields"). It is retained for compatibility, it is not authoritative, and it
currently disagrees with `asset_kind` on 6 rows (§8, rule C-14). No new logic reads it.

---

## §2 — Kind definitions

- **`data`** — an asset a registered writer builds into one or more Postgres tables. It has a
  target table, a chart-scoped row count, a measured floor, and an invariant of its own.
- **`artifact`** — a *derived* data asset: built by a writer into a table like `data`, but its
  rows are narrative/derived products rather than the layer's base facts. Field requirements
  are identical to `data` in every respect this contract can enforce; the distinction is
  semantic and is retained because the cockpit and the plan use it. **A rule that applies to
  `data` applies to `artifact` unless this document says otherwise, and no rule in §8 currently
  says otherwise.** (Stated explicitly because a CI guard must not have to guess.)
- **`service`** — an asset that provides a live capability rather than a built table. It is
  probed for health, not counted for rows. It has no writer output to floor or to gate.
- **`source`** — ingested data the DAG reads and never builds (`lel_events` is the specimen,
  v3.0 §3.6). Exempt from writer, count, floor and integrity requirements, because none of them
  are meaningful for data the system did not produce. Outside the L0–L5 ladder.

---

## §3 — Lifecycle model — tombstone, never delete (I6)

| State | `catalog_status` | `is_active` | Meaning | Additional obligations |
|---|---|---|---|---|
| CURRENT | `'CURRENT'` | `true` | Live, buildable, authoritative | Full conformance to its kind's matrix; may depend only on CURRENT or `source` rows |
| DRAFT | `'DRAFT'` | `true` or `false` | Registered, not yet authoritative | A CURRENT asset may not depend on it (rule C-11) |
| RETIRED | `'RETIRED'` | `false` | No longer built; record retained | zero `asset_throughput` rows; `data_disposition` NOT NULL (rule C-08) |
| SUPERSEDED | `'RETIRED'` **+** `superseded_by` NOT NULL | `false` | Replaced by a named successor | as RETIRED, **plus** `superseded_by` resolves to an existing `asset_id` (rule C-09) |

**SUPERSEDED is not a fourth `catalog_status` value.** v3.0 §3.2 writes it `SUPERSEDED_BY(x)`;
the live CHECK constraint permits only three values, and v3.0 itself defines the state as
"As RETIRED + resolvable pointer". This contract therefore expresses it as `RETIRED` plus a
non-null `superseded_by`, which requires **no** change to the `catalog_status` CHECK constraint.
This is a representation choice, and it is recorded here so it is not silently re-litigated.

**A registry row is never deleted.** Exit from service is a state transition plus a
`data_disposition`, never a `DELETE`. Retired rows carry FK dependants and audit history;
migration 563 already failed on exactly that FK.

### 3.1 `data_disposition` — mandatory on exit

`data_disposition ∈ {RETAINED_AS_CAPITAL, SUPERSEDED_IN_PLACE, DROPPABLE}`

| Value | Means | Consequence |
|---|---|---|
| `RETAINED_AS_CAPITAL` | The rows are expensive-to-recreate capital and stay | Never a target of any clear/rebuild. `ka_gochara_sweep`'s 38,287 v1 rows are the specimen (charter P1). |
| `SUPERSEDED_IN_PLACE` | A successor writes the same table; the old rows were replaced | `superseded_by` must be non-null |
| `DROPPABLE` | The rows carry no remaining value | Still not dropped by this contract — dropping is a separate, approved operation |

`data_disposition` is REQUIRED when `catalog_status='RETIRED'` and MUST BE NULL otherwise.
A NULL disposition on a retired asset is the "retired-without-disposition" finding the M0 exit
criteria require to be zero.

---

## §4 — The per-kind field specification

Notation: **R** = required (NOT NULL / true); **N** = must be NULL; **C** = conditionally
required, condition stated in the field's own subsection; **–** = permitted, unconstrained.

| # | Field | `data` | `artifact` | `service` | `source` |
|---|---|---|---|---|---|
| 4.1 | `asset_id` prefix matches `layer` | R | R | R | N/A (exempt) |
| 4.2 | `layer`, `layer_index`, `layer_name` | R | R | R | exempt (outside L0–L5) |
| 4.3 | `sanskrit_name`, `english_name`, `english_description`, `sort_order`, `scope` | R | R | R | R |
| 4.4 | `catalog_status` + lifecycle fields (§3) | R | R | R | R |
| 4.5 | `target_table` · `count_sql` · `clear_tables` | R · R · – | R · R · – | N · N · N | N · N · N |
| 4.6 | `target_floor` | C | C | N | N |
| 4.7 | `integrity_check_sql` | C | C | N | N |
| 4.8 | `has_substeps` · `writer_timeout_seconds` · `estimated_seconds` | R · R · C | R · R · C | R(false) · R(default) · N | R(false) · R(default) · N |
| 4.9 | natural-key partition declaration | C (co-written tables) | C | N | N |
| 4.10 | `health_probe` · `provides_apis` · `service_health` | N | N | R | N |
| 4.11 | authority pointer + `protected_generations` | C (generation-bearing) | N | N | N |
| 4.12 | `depends_on` | R (may be empty) | R | R | N |
| 4.13 | consumers | R | R | R | R |
| 4.14 | `domain` | R | R | R | R |
| 4.15 | `rung` | R | R | R | N (outside the ladder) |

### 4.1 `asset_id` — `text`, PRIMARY KEY, NOT NULL

Immutable. The prefix before the first `_` must be the layer's prefix per CLAUDE.md §N.1:

| `layer` | required prefix |
|---|---|
| `brahmagyan` | `bg_` |
| `ganita` | `ga_` |
| `bodha` | `bo_` |
| `kala` | `ka_` |
| `phala` | `ph_` |
| `mimamsa` | `mi_` |

Dot-notation ids (`bodha.*`, `ganita.*`) are forbidden outright (§N.1, migration 224). A `source`
asset is exempt from the prefix rule *because it is outside the layer model* — it is not free to
use any prefix, it is required to declare its exemption via `asset_kind='source'`.

### 4.2 `layer` · `layer_index` · `layer_name`

- `layer` — `text NOT NULL`, CHECK ∈ {`brahmagyan`,`ganita`,`bodha`,`kala`,`phala`,`mimamsa`}.
  **This is the clean, authoritative layer column** and the sole input to `rung` (§5.2).
- `layer_index` — `text NULL`. Contract form is `L0`…`L5`. The live column is dirty: 15 NULLs
  and 6 rows carrying a bare digit (`'0'`,`'1'`,`'2'`,`'3'`). REQUIRED form is `^L[0-5]$`.
- `layer_name` — `text NULL`, derived display name. Contract form is the external lexicon
  spelling exactly: `Brahmagyan` · `Gaṇita` · `Bodha` · `Kāla` · `Phala` · `Mīmāṃsā`. The live
  column is dirty on the diacritics (`Ganita` ×2, `Kala` ×3) and 15 NULL.

Both derived columns must agree with `layer`. `layer` is never derived from them.

### 4.3 Descriptive fields

`sanskrit_name`, `english_name`, `english_description` — `text NOT NULL`, non-empty after trim.
`sort_order` — `integer NOT NULL`. `scope` — `text NOT NULL`, CHECK ∈ {`global`,`per_chart`};
legacy, superseded on serving paths by `domain` (§5.1) but retained until the rename migration.

### 4.4 Lifecycle fields

`catalog_status` — `text NOT NULL DEFAULT 'DRAFT'`, CHECK ∈ {`CURRENT`,`DRAFT`,`RETIRED`}.
`is_active` — `boolean DEFAULT true`. `superseded_by` — `text NULL`, FK-resolvable to
`asset_registry.asset_id`. `data_disposition` — `text NULL`, CHECK ∈ §3.1's three values.
Obligations are §3's table and §3.1.

### 4.5 `target_table` · `count_sql` · `clear_tables`

- `target_table` — `text`. REQUIRED for `data`/`artifact`; MUST BE NULL for `service`/`source`.
  Must name a table that exists in the `public` schema.
- `count_sql` — `text`. REQUIRED for `data`/`artifact`; MUST BE NULL for `service`/`source`.
  **Must return exactly one row, one integer column.** When `domain='chart'` it **must be
  chart-scoped**: it must contain the `$1` placeholder and every `$1` binds the same `chart_id`.
  This is the L1 cockpit trap named in CLAUDE.md §N.4 ("the stats route reads `count_sql`, NOT
  `asset_throughput`"): a chart-domain `count_sql` without `$1` reports the whole table as the
  chart's rows and is a hard violation, not a style preference.
- `clear_tables` — `text[]`. Optional. When present, every element must be an existing table,
  and the asset's `target_table` must be among them. It declares the delete scope of a
  clear+rebuild, so an incorrect entry is a destructive-operation hazard.

### 4.6 `target_floor` — `integer NULL`

The number of rows the asset is expected to produce for one chart. **Measured, never invented**
(I7, CLAUDE.md §N.4 "floors aspirational, not gates").

- REQUIRED (non-null) for a `data`/`artifact` asset whose `catalog_status='CURRENT'`.
- Permitted-NULL for a DRAFT asset that has never successfully built — an unmeasured floor is
  honestly absent, and writing a guess here is fabrication (H6).
- MUST BE NULL for `service` and `source`.
- `target_floor = 0` is a **legal and meaningful** value, but only with a non-null
  `volume_explanation` stating why zero rows is by design (plan §4 discipline 2, charter G4).
  Zero without an explanation is the "unbuilt vs by-design undecided" finding.
- A floor is set **only** to a count the measurement tooling returned. Never to a target, an
  estimate, a historical figure, or a number from a document. `ga_dashas`' 536,471 is the
  named specimen of a stale historical figure standing where a measurement belongs.

### 4.7 `integrity_check_sql` — `text NULL`

The asset's own invariant, expressed as SQL, run by the orchestrator **after** the writer's
commit. It is the detector that earns `lit` (CLAUDE.md §N.8; plan §4 discipline 1).

Required form, so the gate engine needs no per-asset special-casing:

1. Returns **exactly one row with exactly one integer column**, interpreted as a **violation
   count**. `0` = pass. Any positive value = fail → the asset is written `incomplete`, never
   `lit`.
2. For `domain='chart'` assets it is chart-scoped on `$1`, exactly as `count_sql` (§4.5).
3. It is **read-only**: no DML, no DDL, no `nextval`, no writes of any kind.
4. It expresses a **real invariant with a real detector** (charter G3, I5). A check that cannot
   return a positive number for any possible database state is not a check; it is a green light
   with no bulb. Examples of real invariants: single-row-per-natural-key across `build_id`
   generations (the accretion guard, plan §4 discipline 4); referential resolution of an
   asset's cited upstream ids; a domain constraint the writer is supposed to guarantee.
5. **Presence is a registration requirement; enforcement is a separate switch.** Under plan
   §14.1 the check is *authored* in each rung's stage 2 (§8.6) by the agent that knows the
   asset, and the *engine* is built in M3. Therefore:
   - REQUIRED (non-null) for a `data`/`artifact` asset **whose rung has been frozen**.
   - Permitted-NULL before its rung freezes. It is NOT permitted to be NULL at rung freeze.
   - MUST BE NULL for `service` and `source`.

No CI guard may assert this field is *satisfied* — only the gate engine's run does that, and only
against a live build. A registration guard checks presence and shape, nothing more.

### 4.8 `has_substeps` · `writer_timeout_seconds` · `estimated_seconds`

- `has_substeps` — `boolean NOT NULL DEFAULT false`. **Derived from the writer class, not
  declared by hand.** It must be `true` iff the registered writer implements
  `plan_substeps(ctx)` + `run_substep(ctx, step)` and `false` iff it implements `run(ctx)`
  (the FROZEN contract, CLAUDE.md §N.2). The truth source is the writer-class census (task
  M0-T1); the registry column must equal it. `service` and `source` rows are `false`.
- `writer_timeout_seconds` — `integer NOT NULL DEFAULT 600`. Because the column is NOT NULL with
  a default, "present" is not a meaningful assertion. The contract requirement is instead:
  for any asset whose telemetry shows a p95 build duration ≥ 0.5 × `writer_timeout_seconds`,
  the value must have been **explicitly set from measured telemetry**, not left at the default.
  **This rule is not checkable until Track M2 produces cleaned telemetry**; until then it is
  advisory and is recorded here so it is not forgotten, not asserted as green.
- `estimated_seconds` — `integer NULL`. Measured on first successful build; the seed writes it
  `null` by design ("always null — measured on first build"). REQUIRED for a `data`/`artifact`
  asset that has at least one successful build in `asset_throughput`; MUST BE NULL for
  `service`/`source`. A value never measured stays NULL (H6).

### 4.9 Natural-key partition declaration — **no schema column exists**

The de-duplication invariant is **one authoritative producer per
(`target_table` × generation × natural-key partition)** — never one per table. Four tables
legitimately have multiple active writers (`bodha_msr_signals` 7, `chart_facts` 5,
`brahma_class_priors` 2, `classical_text_chunks` 2, per v3.0 §3.3).

Each co-writer must declare the partition it owns, so the invariant is checkable rather than
assumed. **`asset_registry` has no column for this today** (§9 lists all 36 columns). This
contract therefore specifies the requirement and records that it is **not yet schema-backed**:
the column is not added by M0-T2's migration, because the plan does not name it and adding a
column this contract cannot yet fill would create exactly the empty-signal defect §N.8 forbids.
See §10.3.

### 4.10 `health_probe` · `provides_apis` · `service_health`

- `health_probe` — `jsonb`. REQUIRED for `service`; MUST BE NULL for every other kind. It
  declares how the probe is invoked; a service with no probe cannot have its health *detected*,
  so its `service_health` would be a status with no detector behind it (§N.8).
- `provides_apis` — `jsonb`. REQUIRED for `service`; MUST BE NULL for every other kind.
- `service_health` — `text NULL`, CHECK ∈ {`healthy`,`degraded`,`unhealthy`,`unknown`}.
  **Written only by the probe.** For a `service` asset with no `health_probe`, the only honest
  value is `unknown` or NULL — never `healthy`. Writing `healthy` on any basis other than a
  probe run is prohibited by charter H4. MUST BE NULL for every non-`service` kind.

### 4.11 Authority pointer · `protected_generations` — **no schema column exists**

For a generation-bearing asset (a table holding rows from more than one build generation,
`kala_gochara_windows` being the case in hand), the registry must name which generation is
authoritative and which are protected capital. **Neither column exists today.** Same treatment
as §4.9: specified, not schema-backed, not added by this task's migration. See §10.3.

Note the standing lesson recorded in migration 588: any such protection must be keyed on
(table, generation) and **never** on `asset_id` — keying it on `asset_id` is what blocked the
authoritative writer outright (defect D-02).

### 4.12 `depends_on` — `text[] NOT NULL DEFAULT '{}'`

Every element must (a) be an existing `asset_registry.asset_id`, (b) belong to an `is_active`
row, and (c) if the depending asset is `CURRENT`, itself be `CURRENT` or `source` — a CURRENT
asset may not depend on a DRAFT one. Self-reference is forbidden; the edge set must be acyclic.
An empty array is legal (root assets). MUST BE NULL/empty for `source` (a source is never built,
so it depends on nothing).

### 4.13 Consumers — **no schema column exists**

The consumer map is asset → {MCP tools, API routes, retrieval layers} reading its table, built
from `platform-mcp/src/tools/**`, `platform/src/app/api/**`, `platform/src/lib/retrieval/**`
(v3.0 §3.5). Without it, "is it safe to retire this?" is unanswerable. It is a **derived
artefact of the census**, not a registry column, and this contract does not propose making it
one — a hand-maintained consumer list drifts, a recomputed one cannot. The requirement is that
the census produce it, and that no asset be retired without consulting it.

### 4.14 `domain` — `text`, values `shared` | `chart`

See §5.1. REQUIRED (non-null) for every row of every kind, without exception: the planner's
split rule (plan §6.2) is a total function over the catalogue, and a NULL domain makes an asset
undispatchable rather than merely unlabelled.

### 4.15 `rung` — `text`, values `R0`…`R5`

See §5.2. REQUIRED for every ladder asset (`data`/`artifact`/`service`); MUST BE NULL for
`source`, which sits outside L0–L5 and therefore outside the ladder.

---

## §5 — The two derived fields: exact derivation

Both derivations are **total, mechanical and judgment-free** over the live table, because both
of their input columns are `NOT NULL` and constrained by a CHECK to exactly the value sets
below (§9). No asset is left NULL by either rule, and no asset requires a judgment call.

### 5.1 `domain` ← `scope`

| `scope` | `domain` | live count (2026-08-23) |
|---|---|---|
| `global` | `shared` | 44 |
| `per_chart` | `chart` | 84 |

The rename is 1:1 and information-preserving. `scope` is retained as a legacy column until the
rename migration (plan §6.1); after it, `domain` is the only column serving paths read, and no
new write of `'global'`-as-chart is accepted (plan §6.1, M1).

### 5.2 `rung` ← `layer`

| `layer` | ladder layer | `rung` | live count (2026-08-23) |
|---|---|---|---|
| `brahmagyan` | L0 | `R0` | 40 |
| `ganita` | L1 | `R1` | 19 |
| `bodha` | L2 | `R2` | 22 |
| `kala` | L3 | `R3` | 23 |
| `phala` | L4 | `R4` | 9 |
| `mimamsa` | L5 | `R5` | 15 |

**`layer` is the input, not `layer_index`.** This is deliberate and load-bearing: `layer` is
`NOT NULL` with a CHECK covering exactly six values, whereas `layer_index` is nullable and
measurably dirty (15 NULL, 6 rows carrying a bare digit rather than `Lx` — see §9). Deriving
`rung` from `layer_index` would propagate that dirt and leave 15 assets un-runged; deriving it
from `layer` cannot fail. `layer_index`'s own repair is a separate M0 item and does not gate
this one.

**One caveat recorded, not hidden:** `lel_events` carries `layer='mimamsa'` and so derives
`rung='R5'` mechanically, while §4.15 says a `source` asset should have `rung` NULL. Since
`lel_events` is not yet classified `source` (§10.1), the mechanical derivation applies to it
today and must be revisited when that classification is ruled on. This is stated rather than
special-cased, because special-casing it now would be deciding §10.1 by implementation.

---

## §6 — Conformance rules

Each rule is an assertion. `violations` is the row count returned by the SQL. A conformant
catalogue returns 0 for every rule. **Live violation counts below were measured 2026-08-23 and
are the baseline this contract freezes, not a claim that they are acceptable.**

> **DATED CORRECTION — 2026-08-23 (M0-T32).** Four cells in the table below carry the
> parenthetical *"(column does not exist yet)"* — C-08, C-10, C-18, C-19. That parenthetical is
> now **false**: migration `590_nirmana_m0_catalogue_contract_columns.sql` applied at
> **2026-08-23T05:36:13.833986+00:00** (`_migrations_applied` id 450) and all four columns
> (`domain`, `rung`, `superseded_by`, `data_disposition`) are live and populated — see the
> corrected §11. Those four rules are now genuinely checkable, and the shipped guard
> (`platform/scripts/governance/check_asset_catalogue_contract.py`) reports them live at
> 2026-08-23T07:27Z as: **C-08 = 1** (`ka_gochara_sweep`, RETIRED with no `data_disposition`
> — 0 rows in the whole table carry one), **C-10 = 0**, **C-18 = 0**, **C-19 = 0**.
>
> **The table's own numbers are NOT edited**, deliberately and for two reasons. First, §6 is
> declared above as a *frozen baseline measured 2026-08-23*, and a baseline that gets quietly
> re-pointed at today stops being a baseline. Second, this table is the spec input the guard
> cross-checks itself against (28/28 rules parsed, 0 problems, re-verified after this edit);
> rewriting cells in it is a deliberate act, not a passing correction. For a current figure,
> run the guard or read `m0_exit_scorecard.json`. What is corrected here is the parenthetical
> *claim about the schema*, which was a present-tense assertion and not a dated measurement.

Severity: **BLOCKING** = must be 0 before the M0 exit criteria are met. **RUNG** = must be 0
before the named rung freezes. **ADVISORY** = not yet mechanically checkable; recorded so it is
not lost, and explicitly NOT reported as green.

| Rule | Assertion | Severity | Live violations (2026-08-23) |
|---|---|---|---|
| C-01 | `asset_id` prefix matches `layer` (§4.1), for non-`source` rows | BLOCKING | **1** (`lel_events`) |
| C-02 | `layer_index` matches `^L[0-5]$` and agrees with `layer` | BLOCKING | **21** (15 NULL + 6 bare digits) |
| C-03 | `layer_name` is the exact lexicon spelling for `layer` | BLOCKING | **20** (15 NULL + `Ganita`×2 + `Kala`×3) |
| C-04 | `data`/`artifact` ⇒ `target_table` NOT NULL and the table exists | BLOCKING | **10** rows with NULL `target_table` (§8) |
| C-05 | `data`/`artifact` ⇒ `count_sql` NOT NULL | BLOCKING | **2** (`bg_ephemeris_engine`, `bg_panchanga`) |
| C-06 | `domain='chart'` ∧ `count_sql` NOT NULL ⇒ `count_sql` contains `$1` | BLOCKING | **0** |
| C-07 | `service` ⇒ `target_table`, `count_sql`, `target_floor`, `clear_tables` all NULL | BLOCKING | **4** (`ka_dasha_kala`, `ka_tulana`, `mi_abhilekha`, `mi_seva`) |
| C-08 | `catalog_status='RETIRED'` ⇒ `data_disposition` NOT NULL | BLOCKING | **1** (`ka_gochara_sweep` — column does not exist yet) |
| C-09 | `superseded_by` NOT NULL ⇒ it resolves to an existing `asset_id` | BLOCKING | **n/a** (column does not exist yet) |
| C-10 | `data_disposition` NOT NULL ⇒ `catalog_status='RETIRED'` | BLOCKING | **n/a** (column does not exist yet) |
| C-11 | `CURRENT` asset depends only on `CURRENT` (or `source`) assets | BLOCKING | **3** (`bo_laksana`→`ga_vichara`; `ka_kshetra`→`ka_dasha_kala`; `ka_taranga`→`ka_sangam`) |
| C-12 | every `depends_on` element resolves to an existing `asset_id` | BLOCKING | **0** |
| C-13 | `depends_on` graph is acyclic and self-reference-free | BLOCKING | not measured by this task |
| C-14 | `asset_kind` and `asset_type` are coherent (§8 mapping) | BLOCKING | **6** (`bg_ephemeris_engine`, `bg_panchanga`, `ka_graha_sancara`, `ka_muhurta_seva`, `mi_abhilekha`, `mi_seva`) |
| C-15 | `service` ⇒ `health_probe` NOT NULL ∧ `provides_apis` NOT NULL | BLOCKING | **6** (all 6 service rows) |
| C-16 | non-`service` ⇒ `service_health` IS NULL | BLOCKING | **0** |
| C-17 | `service_health='healthy'` ⇒ `health_probe` NOT NULL | BLOCKING | **3** (`ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`) |
| C-18 | `domain` NOT NULL for every row, and equals §5.1's derivation from `scope` | BLOCKING | **128** (column does not exist yet) |
| C-19 | `rung` NOT NULL for every non-`source` row, and equals §5.2's derivation from `layer` | BLOCKING | **128** (column does not exist yet) |
| C-20 | `CURRENT` ∧ `data`/`artifact` ⇒ `target_floor` NOT NULL | BLOCKING | measured by M0-T1 census, not by this task |
| C-21 | `target_floor = 0` ⇒ `volume_explanation` NOT NULL | BLOCKING | measured by M0-T1 census, not by this task |
| C-22 | rung-frozen ∧ `data`/`artifact` ⇒ `integrity_check_sql` NOT NULL | RUNG | **0 rungs frozen**, so vacuously 0 today; **0 of 128 assets carry a check** |
| C-23 | `has_substeps` equals the writer-class truth (`plan_substeps` present) | BLOCKING | requires the M0-T1 writer census; not measured by this task |
| C-24 | `clear_tables` elements all exist ∧ include `target_table` | BLOCKING | not measured by this task (1 row sets the field) |
| C-25 | co-written `target_table` ⇒ every co-writer declares its natural-key partition | BLOCKING | **not checkable — no column exists** (§4.9, §10.3) |
| C-26 | generation-bearing asset declares its authority pointer | BLOCKING | **not checkable — no column exists** (§4.11, §10.3) |
| C-27 | `writer_timeout_seconds` set from telemetry where p95 ≥ 0.5× the value | ADVISORY | not checkable until M2 telemetry |
| C-28 | `estimated_seconds` NOT NULL where a successful build exists | BLOCKING | measured by M0-T3 telemetry task, not by this task |

**Rules C-25, C-26 and C-27 must never be reported as passing.** They have no detector. Under
CLAUDE.md §N.8 a rule with no detector is null, not green; a CI guard implementing this document
emits them as `not_checkable` with the reason, and a dashboard that renders that as a pass is
itself a defect.

---

## §7 — SOURCE classification

A `source` asset is ingested data the DAG reads and never builds. It is exempt from the writer,
count, floor and integrity requirements **because those requirements are meaningless for data
the system did not produce**, not as a convenience.

`lel_events` is the specimen (v3.0 §3.6). It currently carries `layer='mimamsa'`,
`asset_kind='data'`, `catalog_status='DRAFT'`, `target_table` NULL — i.e. it is registered as a
buildable data asset that nothing builds. Reclassifying it is charter power G1 (ADHIKĀRIN), and
it is blocked on §10.1 because the live CHECK constraint does not permit `asset_kind='source'`.
**This document does not reclassify it and the M0-T2 migration does not touch it.**

The related v3.0 §3.6 finding — `bg_gochara_citation_resolution`, CURRENT with no writer, never
built — is a *provision / demote / retire* decision, also G1, also outside this task. Recorded
here so it is not lost: **never leave a CURRENT asset that nothing can build.**

---

## §8 — The detection SQL

Transcribe these into the CI guard. Each returns violating rows; conformance is 0 rows. Rules
whose column does not yet exist are written against the post-migration schema and are marked.

```sql
-- C-01  asset_id prefix must match layer
SELECT asset_id, layer FROM asset_registry
WHERE asset_kind <> 'source'
  AND left(asset_id, 3) IS DISTINCT FROM
      (CASE layer WHEN 'brahmagyan' THEN 'bg_' WHEN 'ganita' THEN 'ga_'
                  WHEN 'bodha'      THEN 'bo_' WHEN 'kala'   THEN 'ka_'
                  WHEN 'phala'      THEN 'ph_' WHEN 'mimamsa' THEN 'mi_' END);

-- C-02  layer_index must be Lx and agree with layer
SELECT asset_id, layer, layer_index FROM asset_registry
WHERE layer_index IS NULL
   OR layer_index !~ '^L[0-5]$'
   OR layer_index <> (CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1'
                                 WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3'
                                 WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END);

-- C-03  layer_name must be the exact external-lexicon spelling
SELECT asset_id, layer, layer_name FROM asset_registry
WHERE layer_name IS DISTINCT FROM
      (CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita'
                  WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla'
                  WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END);

-- C-04  data/artifact must name an existing target_table
SELECT a.asset_id, a.asset_kind, a.target_table FROM asset_registry a
WHERE a.asset_kind IN ('data','artifact')
  AND ( a.target_table IS NULL
     OR NOT EXISTS (SELECT 1 FROM information_schema.tables t
                    WHERE t.table_schema='public' AND t.table_name = a.target_table) );

-- C-05  data/artifact must have count_sql
SELECT asset_id, asset_kind FROM asset_registry
WHERE asset_kind IN ('data','artifact') AND count_sql IS NULL;

-- C-06  chart-domain count_sql must be chart-scoped   [post-migration: uses domain]
SELECT asset_id FROM asset_registry
WHERE domain = 'chart' AND count_sql IS NOT NULL AND position('$1' in count_sql) = 0;
-- pre-migration equivalent: ... WHERE scope='per_chart' AND ...

-- C-07  service rows carry no data-asset fields
SELECT asset_id, target_table, target_floor FROM asset_registry
WHERE asset_kind = 'service'
  AND (target_table IS NOT NULL OR count_sql IS NOT NULL
       OR target_floor IS NOT NULL OR clear_tables IS NOT NULL);

-- C-08  retired ⇒ disposition                         [post-migration]
SELECT asset_id FROM asset_registry
WHERE catalog_status = 'RETIRED' AND data_disposition IS NULL;

-- C-09  superseded_by must resolve                     [post-migration]
SELECT a.asset_id, a.superseded_by FROM asset_registry a
WHERE a.superseded_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id = a.superseded_by);

-- C-10  disposition only on retired rows               [post-migration]
SELECT asset_id FROM asset_registry
WHERE data_disposition IS NOT NULL AND catalog_status <> 'RETIRED';

-- C-11  CURRENT may not depend on DRAFT
SELECT a.asset_id, d AS dep, b.catalog_status AS dep_status
FROM asset_registry a
CROSS JOIN LATERAL unnest(a.depends_on) AS d
LEFT JOIN asset_registry b ON b.asset_id = d
WHERE a.catalog_status = 'CURRENT'
  AND (b.asset_id IS NULL OR (b.catalog_status <> 'CURRENT' AND b.asset_kind <> 'source'));

-- C-12  every dependency resolves
SELECT a.asset_id, d AS dep FROM asset_registry a
CROSS JOIN LATERAL unnest(a.depends_on) AS d
WHERE NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id = d);

-- C-13  acyclic, self-reference-free
SELECT asset_id FROM asset_registry WHERE asset_id = ANY(depends_on);
-- cycle detection: WITH RECURSIVE over the edge set; implemented in the guard, not inline here.

-- C-14  asset_kind / asset_type coherence
--   permitted pairs: (data,data) (artifact,data) (service,service)
SELECT asset_id, asset_kind, asset_type FROM asset_registry
WHERE (asset_kind, asset_type) NOT IN
      (('data','data'), ('artifact','data'), ('service','service'), ('source','data'));

-- C-15  service ⇒ probe + apis
SELECT asset_id FROM asset_registry
WHERE asset_kind = 'service' AND (health_probe IS NULL OR provides_apis IS NULL);

-- C-16  non-service ⇒ no service_health
SELECT asset_id, asset_kind, service_health FROM asset_registry
WHERE asset_kind <> 'service' AND service_health IS NOT NULL;

-- C-17  no green health without a probe  (charter H4, CLAUDE.md §N.8)
SELECT asset_id, service_health FROM asset_registry
WHERE service_health IN ('healthy','degraded','unhealthy') AND health_probe IS NULL;

-- C-18  domain present and correctly derived            [post-migration]
SELECT asset_id, scope, domain FROM asset_registry
WHERE domain IS DISTINCT FROM (CASE scope WHEN 'global' THEN 'shared'
                                          WHEN 'per_chart' THEN 'chart' END);

-- C-19  rung present and correctly derived              [post-migration]
SELECT asset_id, layer, rung FROM asset_registry
WHERE asset_kind <> 'source'
  AND rung IS DISTINCT FROM (CASE layer WHEN 'brahmagyan' THEN 'R0' WHEN 'ganita' THEN 'R1'
                                        WHEN 'bodha' THEN 'R2' WHEN 'kala' THEN 'R3'
                                        WHEN 'phala' THEN 'R4' WHEN 'mimamsa' THEN 'R5' END);

-- C-20  CURRENT data/artifact must carry a measured floor
SELECT asset_id FROM asset_registry
WHERE catalog_status = 'CURRENT' AND asset_kind IN ('data','artifact') AND target_floor IS NULL;

-- C-21  a zero floor needs a written explanation
SELECT asset_id FROM asset_registry
WHERE target_floor = 0 AND (volume_explanation IS NULL OR btrim(volume_explanation) = '');

-- C-22  a frozen rung's data assets must carry an integrity check
--   ':frozen_rungs' is supplied by the campaign state, not inferred from the registry.
SELECT asset_id, rung FROM asset_registry
WHERE asset_kind IN ('data','artifact') AND rung = ANY(:frozen_rungs)
  AND integrity_check_sql IS NULL;

-- C-24  clear_tables must exist and include target_table
SELECT a.asset_id, t AS listed FROM asset_registry a
CROSS JOIN LATERAL unnest(a.clear_tables) AS t
WHERE a.clear_tables IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM information_schema.tables i
                  WHERE i.table_schema='public' AND i.table_name = t)
UNION ALL
SELECT asset_id, target_table FROM asset_registry
WHERE clear_tables IS NOT NULL AND NOT (target_table = ANY(clear_tables));

-- C-25 / C-26 / C-27 — NOT CHECKABLE. Emit status 'not_checkable' with the reason.
--   Never emit pass. (CLAUDE.md §N.8: a signal with no detector is null, not green.)
```

---

## §9 — Live schema baseline (measured 2026-08-23)

`public.asset_registry`, 36 columns, 128 rows (127 `is_active`).

**The four contract columns `domain`, `rung`, `superseded_by`, `data_disposition` DO NOT EXIST.**
Verified by `information_schema.columns` returning 0 rows for them (verbatim query and result in
the M0-T2 report to PARĪKṢAKA).

Value sets and their CHECK constraints, as they actually are:

| Column | Type / nullability | CHECK | Live distinct values |
|---|---|---|---|
| `scope` | `text NOT NULL` | ∈ {`global`,`per_chart`} | `global` 44 · `per_chart` 84 |
| `layer` | `text NOT NULL` | ∈ 6 layer names | `brahmagyan` 40 · `ganita` 19 · `bodha` 22 · `kala` 23 · `mimamsa` 15 · `phala` 9 |
| `layer_index` | `text NULL` | none | `L0` 37 · `L1` 16 · `L2` 10 · `L3` 21 · `L4` 9 · `L5` 14 · `0` 1 · `1` 2 · `2` 1 · `3` 2 · NULL 15 |
| `layer_name` | `text NULL` | none | `Brahmagyan` 38 · `Gaṇita` 16 · `Ganita` 2 · `Bodha` 11 · `Kāla` 20 · `Kala` 3 · `Phala` 9 · `Mīmāṃsā` 14 · NULL 15 |
| `asset_kind` | `text NOT NULL DEFAULT 'data'` | ∈ {`data`,`service`,`artifact`} — **no `source`** | `data` 106 · `artifact` 16 · `service` 6 |
| `asset_type` | `text NOT NULL DEFAULT 'data'` | ∈ {`data`,`service`} | `data` 124 · `service` 4 |
| `catalog_status` | `text NOT NULL DEFAULT 'DRAFT'` | ∈ {`CURRENT`,`DRAFT`,`RETIRED`} — **no `SUPERSEDED`** | `CURRENT` 80 · `DRAFT` 47 · `RETIRED` 1 |
| `storage_type` | `text NOT NULL` | ∈ 7 values | `postgres_table` 115 · `service` 8 · `pgvector` 4 · `postgres_view` 1 |
| `service_health` | `text NULL` | ∈ {`healthy`,`degraded`,`unhealthy`,`unknown`} | 4 non-null |
| `has_substeps` | `boolean NOT NULL DEFAULT false` | — | `true` 14 (all `data`) |
| `writer_timeout_seconds` | `integer NOT NULL DEFAULT 600` | — | all 128 non-null |
| `integrity_check_sql` | `text NULL` | — | **0 of 128 populated** |
| `target_floor` | `integer NULL` | — | 103 of 128 populated |

Field population by kind (live):

| kind | n | target_table | count_sql | clear_tables | target_floor | integrity_check_sql | has_substeps=true | estimated_seconds | health_probe | provides_apis | service_health | has_writer=true | volume_explanation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `data` | 106 | 96 | 104 | 1 | 99 | **0** | 14 | 9 | 2 | 2 | 0 | 99 | 62 |
| `artifact` | 16 | 16 | 16 | 0 | **0** | **0** | 0 | 0 | 0 | 0 | 0 | 16 | 16 |
| `service` | 6 | 2 | 2 | 0 | 4 | **0** | 0 | 0 | **0** | **0** | 4 | 6 | 6 |

Two observations that fall out of that table and are stated as observations, not verdicts:
no asset anywhere carries an `integrity_check_sql`; and all 16 `artifact` assets carry a
`count_sql` but no `target_floor`, so C-20 will fire on every CURRENT one of them.

---

## §10 — What this contract could not settle (ADHIKĀRIN)

Each of these is a real fork. This document states the options and does not pick one; picking
one here would be deciding a G1-class question by writing it into a spec.

**10.1 — Is `source` a kind or a lifecycle state?**
v3.0 §3.2 lists `SOURCE` among lifecycle states; v3.0 §3.4 makes it a column of the required-
fields matrix (i.e. a kind) and says "`asset_kind` is the single authoritative classification
column". This contract adopts the §3.4 reading (kind) throughout, because §3.4 is the normative
matrix and it names the column. **But the live `asset_registry_asset_kind_check` constraint
permits only `data|service|artifact`,** so no row can be `source` until that constraint changes.
That is a schema change the plan does not name → charter P5. **Not decided here, and the M0-T2
migration does not touch the constraint.** Affects: `lel_events` (§7), rule C-01, C-14, C-19.

**10.2 — Does `RETIRED` + `superseded_by` adequately express `SUPERSEDED_BY(x)`?**
This contract says yes (§3), on v3.0 §3.2's own wording, and thereby avoids a `catalog_status`
CHECK change. The alternative is a fourth status value. Recorded as a representation choice so
it can be overturned cheaply if ADHIKĀRIN prefers the explicit status.

**10.3 — Three contract requirements have no schema column: §4.9 natural-key partition,
§4.11 authority pointer / `protected_generations`, §4.13 consumers.**
The M0-T2 migration deliberately adds **only** the four columns the plan names. Adding the
others now would create columns nothing can fill, and a NULL column that a guard reports as
"present" is the empty-signal defect §N.8 forbids. Consumers, in this author's view, should stay
a recomputed census artefact rather than becoming a hand-maintained column — but that is a
recommendation, not a decision. Rules C-25 and C-26 stay `not_checkable` until this is settled.

**10.4 — `asset_type` retirement.** The column is legacy, non-authoritative, and disagrees with
`asset_kind` on 6 rows. This contract's C-14 asserts coherence rather than proposing the drop,
because dropping a column is a schema change the plan does not name (P5) and 6 rows would need
a kind repair first (which is a separate M0 item). Recorded as the obvious follow-on.

---

## §11 — Relationship to the migration authored alongside this document

`platform/migrations/590_nirmana_m0_catalogue_contract_columns.sql` adds `domain`, `rung`,
`superseded_by` and `data_disposition` and backfills `domain` and `rung` per §5.

**STATUS — CORRECTED 2026-08-23 (M0-T32). That migration is APPLIED.**

`590_nirmana_m0_catalogue_contract_columns.sql` was applied at **2026-08-23T05:36:13.833986+00:00**
(`_migrations_applied` id **450**). All four columns are live in `public.asset_registry` and
populated on all 128 rows (`domain` 128/128, `rung` 128/128, both `text`), verified read-only at
2026-08-23T07:25Z. `rung` distribution live: R0 40 · R1 19 · R2 22 · R3 23 · R4 9 · R5 15.

> **What this section said until now, and why it was wrong.** It read: *"That migration is
> AUTHORED AND NOT APPLIED. Applying it is gated on an ADHIKĀRIN ruling that had been requested
> and had not returned at the time of authoring. No DDL or DML from it has been executed against
> any database."* That was true when authored (M0-T2) and became false 05:36:13Z the same day.
> Left standing it is the sentence a later reader consults to decide whether `domain`, `rung`,
> `superseded_by` and `data_disposition` exist — and it answers no about four columns that do.
> Found by M0-T31 (finding F-1), corrected here. **Only this status paragraph changed.** The
> rules, the derivations and the analysis in §0–§10 are untouched and were, and remain, accurate.

**The one claim below that this correction does NOT overturn:** *"Every claim in §9 comes from a
read-only query against the live schema as it stands* **before** *that migration."* §9 is a dated
pre-590 baseline and is correctly labelled as one; it is a historical measurement, not a present-
tense assertion, and it is left exactly as measured. A reader wanting the post-590 schema should
read the live schema or `m0_exit_scorecard.json` `_meta.asset_registry_columns_present`, not §9.
