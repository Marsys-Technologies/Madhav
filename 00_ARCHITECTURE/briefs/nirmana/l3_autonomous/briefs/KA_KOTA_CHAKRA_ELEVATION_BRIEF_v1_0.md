---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_KOTA_CHAKRA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference
asset_or_interface_ids: ["ka_kota_chakra", "SC-1 (build-time date.today() horizon → declared requested_horizon)", "SC-5 (coverage on the rolling horizon)", "SC-8 (the single ayanāṃśa offset as a declared convention)", "Gochara w25_kota_chakra proposed-use (N-8 / M-4 operand audit) — verification item", "L0 bg_kota_chakra_rings version pin"]
goal_objective: "Make the fort chart's rows say what horizon they were computed for and under which ring-table version, so that a rebuild on a different day is a declared re-scan rather than a silent replacement, the posture/severity synthesis is labelled the uncited extension it already admits to being, corpus non-verifiability is stamped rather than implied, and a consumer that admits Kota into scoring does so against a pinned partition."
source_revision: "9feac52d7 (l3/kala-layer-briefs)"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal at lahiri_chitrapaksha (fact id carried); L0 ephemeris_daily tropical knots (noon UT; accepted L0 revision f6fed12c7); L0 bg_kota_chakra_rings (ADJUDICATION-9; tier-iii citation; versioned vNN) — the writer reads MAX(table_version), i.e. latest, not a pin"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_KOTA_CHAKRA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_kota_chakra/{logic,writer}.py", "platform/python-sidecar/tests/**/test_ka_kota_chakra*.py", "one additive DDL migration on kala_kota_chakra (requested_horizon_start/end, ring_table_version, claim_grain, corpus_verifiable) — or a qualification JSONB (§10.2)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_kota_chakra.ts:83 (as_of default), platform-mcp/src/tools/kala_views/now.ts:415-440 (item 16)"]
must_not_touch: ["brahmagyan/l0_kota_chakra_rings.py, bg_kota_chakra_rings (L0 — the partition and its citation tier are L0's)", "ephemeris_daily / bg_ephemeris (L0)", "services/gochara_v3/mechanisms/w25_kota_chakra.py (Gochara-owned; the multipliers 1.30/1.15/1.08/1.04 are its own proposed-use item)", "supabase/migrations/520_kala_kota_chakra.sql, migration 670 (applied)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED when 670 (a)–(c) returns TRUE with the horizon/version stamps present on production; CONSUMER_INTEGRATED when now.ts/query_kota_chakra serve the stamps under a chart-tz as_of"
target_state_campaign: "ANALYZED → QUALIFIED at stage 3; no t3 event today"
wave: "W2 (foundation)"
shape: single asset, rows (chart × graha × ring-run over a rolling −60/+400-day horizon)
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 520, migration 670 ka_kota_chakra contract
  (a)–(c) [V]; blueprint v5.0 §3.5 row 9 / §4 / §16.2, Gochara G-9 corpus count, N-8 [A]; no
  database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_kota_chakra` elevation brief — a fort chart with a declared horizon

## §0 — The recommendation, in one paragraph

`ka_kota_chakra` places each transiting graha in one of four rings by its nakṣatra count from the
natal Moon, over a horizon of **`date.today()` − 60 d to + 400 d computed at build time**
(`writer.py:73-74,:2xx today = date.today()` [V]), against a ring partition read as the **latest**
`bg_kota_chakra_rings.table_version` (`MAX(table_version)`, `:88-91` [V]), with one ayanāṃśa
offset computed at `today` and applied across the horizon (disclosed as < 0.02° drift, `:23-32`
[V]). Its per-row disclosure is unusually honest — `start_truncated/end_truncated`,
`uncited_extension=TRUE` on every row for the posture/severity synthesis (`:2xx`, `logic.py:7-14`
[V]; DDL default TRUE, 520 `:51`), `ring_table_citation` copied from L0 — and its 670 contract
(a)–(c) checks ring = L0 partition, tiling, non-degeneracy and nine-graha presence. What the rows
do **not** say: which horizon they were computed for (so two builds a month apart carry different
window sets under the same key, and the earlier windows simply vanish — a re-scan disguised as a
rebuild, SC-1/SC-5); which partition version graded them (a bump of `bg_kota_chakra_rings` re-grades
every future rebuild silently, and 670(a) compares old rows to the *new* partition — a detector
that fires on the wrong thing); that no classical-corpus row supports "kota" (Gochara's G-9 count
= 0, `corpus_verifiable` unstamped); and `severity`/`posture` are free `TEXT` with no CHECK (520
`:43-44`) although the vocabulary is a closed template (`logic.py:66-70`). The served `as_of`
defaults to the server's date (`query_kota_chakra.ts:83`). Recommendation: **`QUALIFY_LIMIT`** —
stamp `requested_horizon` (as coverage), `ring_table_version` (pinned per row), `claim_grain=
'date_grain'`, `time_basis='noon_ut_knot'`, `source_qualification` split (ring: tier-iii cited;
posture: `algorithmic_approximation`, `uncited_extension`), `corpus_verifiable=false`,
`epistemic_class` per field, `severity`/`posture` CHECK-constrained; `as_of` in the chart's zone;
the Gochara multipliers remain proposed-use until N-8's ablation. No new computation. Decisions:
horizon policy and stamp home (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (ka_kota_chakra row) | contact overlay (posture) | — |
| Strategy §3 *Contact overlay* | posture over a contact; convention scope explicit | horizon and version are the missing scope |
| Blueprint §3.5 row 9 (`:325`), §4 (`:397`), §16.2 (`:907`) | served; corpus **0 rows** for "kota" (G-9); century **proposed-use** pending M-4 operand audit (N-8); `corpus_verifiable=false` stamped honestly; version pinned, not latest; testimony voice only until M-4 | binds §4 |
| Migration 520 (`:33-56`) | DDL: `nakshatra_idx 0..26`, `count_from_janma 1..27`, `kota_ring ∈ {stambha, durgantara, prakara, bahya}`, `posture TEXT`, `severity TEXT` (no CHECK), DATE windows, truncation flags, `uncited_extension DEFAULT TRUE`, `UNIQUE(chart, ayanamsha, graha, window_start)` | no horizon/version/grain column |
| Migration 670 (`:890-1016`) (a)–(c) | ring = L0 partition for the count; per-(chart, graha) tiling; non-degenerate + nine grahas | (a) compares to the **current** L0 partition — see §3 |
| ADJUDICATION-9 (`logic.py:17-35`, `l0_kota_chakra_rings.py`) | partition lives in L0, tier-iii citation, versioned `vNN` | the writer takes the latest |
| Gochara `w25_kota_chakra.py:9-29,:19-20,:50,:165-178` | *"Admission into the live scoring path requires ablation evidence"*; multipliers `stambha 1.30 / durgantara 1.15 / prakara 1.08 / bahya 1.04`; *"kala_kota_chakra … not surfaced in ClassContext.fetch()"* | proposed-use only; the mechanism cannot read the table today |
| Seed (`asset_registry_seed.ts:2472-2487`) | `depends_on: ['ga_positions', 'bg_ephemeris', 'bg_kota_chakra_rings']` | accurate |
| `now.ts:415-440` (item 16) | `current_only: true` pushed into SQL ahead of the row cap — honest-empty preserved | good pattern |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_kota_chakra'`, `scope: 'per_chart'`,
`catalog_status: 'CURRENT'`; 585 rows live [A]. Cost: one ephemeris range read (9 bodies × ~461
days) + one swisseph ayanāṃśa call; cheap; unmeasured.

### 2.2 The code [V]
- **Inputs**: natal Moon `longitude_sidereal` (`:76-81`, `_fetch_janma_nakshatra_idx`) → nakṣatra
  index `floor(lon / 13.333)` (the same formula as L0's `derive_sidereal`, `:18-22`); ring
  partition `MAX(table_version)` (`:84-91`); `ephemeris_daily` tropical for the horizon (`:94-99`);
  one `derive_sidereal` offset at `today` (`:23-32`).
- **Horizon**: `HORIZON_BACK_DAYS = 60`, `HORIZON_FORWARD_DAYS = 400` (`:73-74`) around
  `date.today()` at build; `_has_complete_daily_series` requires one row per inclusive day
  (`:118-128`) else refusal *"incomplete daily ephemeris coverage … prior partition preserved"*.
- **Rows**: per graha, `detect_ring_runs` → `count_from_janma` → `ring_for_count(ring_sets)` →
  `attack_defence_reading` (`logic.py:56-70`: `NATURAL_MALEFICS`/`BENEFICS` sets shared with L1
  writers; a closed template `ring → (posture, severity)`, e.g. `bahya → ('attacking','watch',
  'reinforcing_perimeter','supportive')`); every row `uncited_extension=True`; truncation flags
  from the horizon edge; `ring_table_citation` from L0.
- **Write**: DELETE by chart, then INSERT `ON CONFLICT DO NOTHING` (`:101,:115`); never commits.
- No ayanāṃśa loop (single canonical, disclosed `:41-45`).

### 2.3 Consumers (grep `kala_kota`, tests/seed/generated excluded) [V]
| consumer | reads | role |
|---|---|---|
| `query_kota_chakra.ts` | rows; `MAX_LIMIT 50` with `truncated` + `total_matching` (`:113-130`); `current_only`; `as_of` default `new Date()` (`:83`) | served `relevance_navigation` |
| `now.ts:415-440` | current ring per graha | served |
| `gochara_v3/mechanisms/w25_kota_chakra.py` | **declares** multipliers; **cannot read** the table (`:165-178`) | proposed-use (N-8) |
| Kāla writers, L4, Kṣetra | none | — |

**Live-path statement.** Served on two surfaces; scored by nobody; the server-date `as_of`
default is live on the wrapper.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `nakshatra_idx`, `count_from_janma`, windows | `COMPUTED_FACT_CONFIGURATION` | L0 knots + L1 Moon fact | `date_grain`, `noon_ut_knot`; single offset (`algorithmic_approximation`, bounded) |
| `kota_ring` | `QUALIFIED_RULE` (tier-iii, L0-cited) | `bg_kota_chakra_rings` **latest** | version unpinned on the row |
| `posture`, `severity`, `is_natural_malefic` | `INTERPRETIVE_INFERENCE` — template synthesis | this logic | `uncited_extension=TRUE` already; needs `source_qualification='algorithmic_approximation'` and a CHECK |
| corpus support | none | Gochara G-9: 0 rows | `corpus_verifiable=false` |
| horizon | build-time server date | this writer | undeclared on rows |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Build on day D: rows cover D−60…D+400. Rebuild on D+90: rows cover D+30…D+490; the windows in D−60…D+29 are deleted and nothing records that the horizon moved — a consumer that saved a `window_ref` from the first build finds it gone with no `unsearched_regions` to explain it. Bump `bg_kota_chakra_rings` to v03 and rebuild one chart: its rows are graded v03, every other chart's rows remain v02, and no row says which; 670(a) then reports the *un-rebuilt* charts as violating "ring = L0 partition" — the detector fires on staleness it cannot name. Meanwhile the row's `severity='watch'` is a free string a consumer cannot enumerate, and the wrapper's "current" row is chosen by the server's date |
| Evidence | `writer.py:73-74, :88-91, today = date.today()` (run body), `:101,:115`; 520 `:43-44,:51,:55`; 670 `:892-905` (a); `query_kota_chakra.ts:83`; `w25_kota_chakra.py:165-178` [V] |
| Expected contract | SC-1 (a horizon is declared input, never a server-date side effect), SC-5/B5 (coverage incl. `unsearched_regions` on every result), B3 (`window_ref` with `generation` — the ring-table version is part of the generation), B2 (`source_qualification` split between the cited partition and the uncited synthesis; `corpus_verifiable`), §N.7 item 3 (no wrapper-local constant shadows the L0 partition — satisfied), F28 |
| Defect class | **wrong context** (build-time server date as horizon) + **unpinned generation** (latest partition) + **unqualified** (free-text severity/posture; corpus stamp absent) + **coverage absent** |
| Impact | rolling re-scans indistinguishable from rebuilds; cross-chart grading inconsistency invisible; a Gochara admission (N-8) would be against an unpinned partition; an off-by-one "current" ring around midnight UTC |
| Non-claim | no ring assignment is wrong; the < 0.02° single-offset approximation is accepted as disclosed; 670 (a)–(c) is assumed green today (not queried); the 585-row count is [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q03/Q04 (a contact's posture as testimony, one voice); Q-K06. Not Q02/Q05.
2. **Horizon declared (SC-1/B5).** The horizon becomes an explicit input: `requested_horizon =
   [as_of − 60 d, as_of + 400 d]` where `as_of` comes from `ctx.config` (chart-zone today by
   default, echoed) — never `date.today()` read inside the writer; every row carries the
   `requested_horizon` it belongs to, and the per-build `coverage = {requested_horizon,
   completed_horizon, resolution:'calendar_day', partitions_searched:[9 grahas],
   exclusions:[grahas refused], unsearched_regions:[], completion_detector:
   '_has_complete_daily_series'}`. A rebuild that moves the horizon is a **new generation** with
   the old one's `unsearched_regions` = the dropped span, so a saved `window_ref` resolves to
   "outside the current horizon" rather than to nothing (§10.1 chooses whether old generations are
   retained or replaced).
3. **Partition version pinned (B3).** `ring_table_version` on every row (the `vNN` the writer
   read); `window_ref.generation = FORMULA_VERSION + ring_table_version + requested_horizon`;
   670(a)'s successor compares each row to the partition **it names**, and a separate
   `stale_partition` flag (not a contract failure) marks rows graded under a superseded version.
4. **Qualification (B2).** `epistemic_class` per field as §2.4; `source_qualification`:
   `kota_ring → 'verse_cited'` carrying L0's tier-iii citation (as today), `posture/severity →
   'algorithmic_approximation'` with `uncited_extension=TRUE` (as today); `corpus_verifiable=
   false` stamped with `basis='gochara_g9_count_0'`; `claim_grain='date_grain'`, `time_basis=
   'noon_ut_knot'`, `inclusivity='closed_closed'` (inclusive day runs, `:118-128`);
   `completeness_state='applied'` on graded rows, `'unavailable'` never written (refusal instead).
5. **Closed vocabularies.** `severity` and `posture` gain CHECK constraints from the template's
   value set (`logic.py:66-70`) — one additive migration.
6. **`as_of` (SC-1) at the wrapper.** Omitted `as_of` → today in the chart's zone, echoed.
7. **Gochara admission (N-8).** Unchanged: the multipliers are Gochara's proposed-use; this
   brief supplies the pinned, stamped rows the M-4 operand audit needs and nothing else.
8. **Old vs new.** Positive: rebuild with `as_of` → rows with horizon + version stamps + coverage.
   Negative: a graha's daily series incomplete → refusal names it (unchanged) and coverage
   `exclusions` records it. Boundary: a run touching the horizon edge → `start_truncated` (as
   today) **and** `unsearched_regions` names the span beyond. Missing: `bg_kota_chakra_rings` empty
   → refusal (unchanged). Duplicated: n/a (natural key).
9. **Simpler baseline.** The rows as they are.
10. **Ablation.** Rebuild on two dates: today the second build silently replaces the window set;
    after, the second generation's coverage names the dropped span and every row names its
    horizon — the difference is the named span.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: ring arithmetic; the L0 partition read (now pinned on the row); the single-offset
  approximation (disclosed); truncation flags; refusals; delete-then-insert; `uncited_extension`.
- `QUALIFY_LIMIT`: stamps in §4.2–4.5; CHECKs.
- `ENRICH_CORRECT` (one item): `as_of` from config instead of `date.today()`.
- **Migration**: one additive DDL (stamp columns or a `qualification` JSONB + the two CHECKs);
  670 (a) successor if the version pin lands (never an edit of 670).
- Fences: L0 partition untouched; Gochara's w25 untouched; L1 untouched.
- Rollback: additive; the writer reads `as_of` with a config default.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_kota_chakra`, L3 rows; epistemic: L0/L1 facts + tier-iii partition + template synthesis; placement correct; `QUALIFY_LIMIT` (+ one `ENRICH_CORRECT`) |
| B | three declared edges, all real; no hidden read; fan-out: two served surfaces; Gochara proposed-use |
| C | invariants: 670 (a)–(c) against the **named** partition; every row names horizon + version; severity/posture ∈ closed set; `as_of` echoed. Golden: canonical chart's rings on a fixed fixture date; boundary: horizon edge |
| D | corpus support absent (stamped, not fabricated) |
| E | served ×2; scored ×0 (proposed) |
| F | coverage, version, `corpus_verifiable`, closed vocabularies machine-readable |
| G | cheap; justified no-change |
| H | idempotent; refusal on incomplete series; no credentials |
| I | files in `may_touch`; W2; one additive DDL; 670(a) successor optional |
| J | this brief; §7; review |

---

## §7 — Proof matrix (tier `[U]` unit, `[I]` DB fixture, `[S]` served)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | I | fixture ephemeris 2026-01-01..2027-03-31, `as_of=2026-03-01`; rebuild; 670 | rows with `requested_horizon=[2025-12-31, 2027-04-05]`, `ring_table_version`, coverage; 670 TRUE | (a)–(c) + stamps | stamp absent / FALSE | integrity SQL |
| Negative | I | Mars series missing one day | refusal names Mars; prior partition kept | honest refusal | rows written | writer test |
| Relevant influence | U | natal Moon nakṣatra +1 | every `count_from_janma` −1; rings shift per partition | isolation | posture unchanged where ring changed | unit |
| Irrelevant control | S | `as_of` in UTC vs chart zone at the same instant | same current row | zone-invariant | differs (today) | wrapper test |
| Duplication | I | rebuild twice, same `as_of` | identical rows, one generation | idempotent | accretion / new generation | writer test |
| Context | I | rebuild with `as_of` + 90 d | new generation; previous span in `unsearched_regions` (or retained per §10.1) | declared re-scan | silent replacement (today) | writer test |
| Boundary | U | run starting on horizon day 1 | `start_truncated=true`; `unsearched_regions` names `< horizon_start` | edge honest | truncated without region | unit |
| Delivery | S | sentinel `corpus_verifiable=false` on one row | reaches `now.ts` item 16 and `query_kota_chakra` envelope | survives | absent | MCP/route test |
| Revision | I | `bg_kota_chakra_rings` v02 → v03; rebuild one chart | its rows `v03`; others `v02` + `stale_partition` flag; 670-successor TRUE for both | pinned | old rows flagged as contract failures | integrity SQL |
| Value | S | frozen Q-K06 question | a posture with its horizon, version and corpus stamp; baseline gives posture alone | — | no distinction | baseline |
| Evaluation | — | `not_applicable` | — | — | — | — |

Binding: **OFFERS** B1 (`inclusivity`, `time_basis`, `claim_grain`), B2 (`epistemic_class`,
`completeness_state`, `source_qualification`, `corpus_verifiable`, `operator_role='testimony'`),
B3 (`window_ref` with a version-bearing `generation`), B5 (`coverage`). B4: `independence_group`
= per graha (`declared_lineage`, one witness per graha; nine rows from one ephemeris are not nine
independent witnesses of one thing — declared). **Asset-local:** `ring_table_version`,
`requested_horizon`, `stale_partition`, `uncited_extension`, `start/end_truncated`.

---

## §8 — Prioritization

(1) horizon as input + coverage (the silent re-scan) → (2) version pin (cross-chart consistency)
→ (3) qualification stamps + CHECKs → (4) `as_of` at the wrapper → (5) hand the stamped rows to
N-8. T0; W2; fan-out nil; proposed-use gate untouched.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT` (+ `ENRICH_CORRECT` for the horizon input). Data-plane: `PRODUCER_READY` after
§7 `[U]`/`[I]`; `DATA_ACCEPTED` on production 670-successor TRUE with stamps; `CONSUMER_INTEGRATED`
when the served surfaces carry them. Campaign: `ANALYZED → QUALIFIED`. Non-claims: no
`VALUE_EVALUATED`; Gochara admission is N-8's; corpus support is absent and stays stamped so.

**Walkthrough (ordinary period).** "Where is Saturn in my fort right now?" → one current row:
`prakara`, `posture='attacking'`, `severity='moderate'` (closed set), `ring_table_version='v02'`,
`requested_horizon` shown, `corpus_verifiable=false`, `uncited_extension=true` — the reader knows
it is a cited ring with an engineered reading and no corpus behind the word "kota".

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Horizon policy on rebuild: replace (one generation, dropped span named in coverage) or retain prior generations keyed by `requested_horizon`?** | replace + name the span — the table is a rolling overlay, not a ledger; retention belongs to the learning loop (§13) if a window was ever cited |
| 2 | Stamp home: columns vs `qualification` JSONB | columns for `ring_table_version` + horizon (queryable); JSONB for the rest |
| 3 | CHECK constraints on `severity`/`posture` from the template set | yes |
| 4 | 670(a) successor comparing to the named version + `stale_partition` flag | yes, when the pin lands |

---

## §11 — Not verified here

1. Live 670 result and the 585-row count [A].
2. Which `table_version` of `bg_kota_chakra_rings` is live, and whether more than one exists.
3. Gochara G-9's corpus count (0 for "kota") — Gochara's measurement [A].
4. `now.ts` behaviour when `current_only` and the cap interact — read, not run.
5. No database query; no test run.
