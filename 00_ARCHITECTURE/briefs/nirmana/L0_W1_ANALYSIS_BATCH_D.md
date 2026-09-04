# L0-W1 Analysis — Batch D (bg_nakshatra_medical, bg_dignity_reference, bg_class_priors, bg_vidhi_primitives, bg_formula_constants, bg_sky_calendar, bg_vidhi_floors, bg_muhurta_lattice)

Method note: for each asset the registry row in `l0_batch_D.json` was read as ground truth for
schema/dependencies/floors, then cross-checked against the live writer source under
`platform/python-sidecar/pipeline/orchestrator/writers/` and, where relevant, the seed module
under `platform/python-sidecar/brahmagyan/`. Leverage was checked by grepping
`platform/src/lib/retrieval/registry`, `platform-mcp/src`, and the writer tree for the asset's
`target_table`/`asset_id`. No DB was queried, no code was changed. `grounding_tier` was grepped
across all migrations — **it does not exist as a column anywhere in the schema yet**; this is
consistent with plan §5, which places the grounding matcher's build at L2 Bodha, not L0. That
absence is therefore noted once here and not re-litigated as a defect in every asset below unless
the asset's own content is itself an interpretive claim that plan §2 says should carry the tier.

---

## bg_nakshatra_medical

1. **Pillars:** D-GROUNDING (classical citation per row) and, secondarily, D-SERVICE (feeds
   `ganita_medical_get`/`ref_sign_medical_get` downstream via `ga_medical`). It is the right
   instrument for its purpose — a small, closed, citable reference table (27 nakshatras →
   body-part correspondences per Ashtanga Hridayam/BPHS) with FORENSIC anchoring (#25 Purva
   Bhadrapada → left_side, the native's Moon nakshatra). No role change indicated.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct —
   `bg_medical_mappings.py` (the writer that actually produces this table) reads only its own
   in-module Python literals (`brahmagyan/l0_medical.py`), no other table reads. depends_on is
   accurate.
3. **Leverage:** `has_writer=false` in the registry is misleading in isolation but not a defect —
   the asset is `producer_covered`: `bg_medical_mappings.py` carries three stacked
   `@register(...)` decorators (`bg_sign_medical`, `bg_nakshatra_medical`, `bg_medical_mappings`),
   so the orchestrator marks `bg_nakshatra_medical` built when the parent writer runs. This should
   be flagged for W2 as a `catalog_status`/`asset_kind` clarity item (see §8), not a build gap.
   Consumers: `ga_medical_writer.py` (L1) reads it into `ga_medical`; `query_nakshatra_medical.ts`
   exists as a real MCP-facing retrieval capability. No unplugged-consumer defect found.
4. **Grounding:** its rows are themselves classical citations (Ashtanga Hridayam / BPHS,
   `classical_citation` + `dosha` columns per the integrity SHA), i.e. this is exactly the kind
   of asset D-GROUNDING's `sruti` tier describes — a text-direct reference table. It has no
   `grounding_tier` column (none exist yet, see method note), but its `classical_citation` field
   already carries the sruti evidence; adding the tier label at L0 would be low-cost since the
   citation is already stored per row.
5. **Temporal identity:** N/A — chart-independent classical reference data, no time dimension.
6. **Service:** real consumer confirmed (`ga_medical_writer.py`, `query_nakshatra_medical.ts`).
   Floor = 27 (exact row count, not aspirational). `count_sql` is a simple `COUNT(*)`; sane.
   `integrity_check_sql` pins an exact row count AND a SHA-256 content hash over
   `(nakshatra_name, nakshatra_number, body_part, classical_citation, dosha)` — a strong,
   specific check, not a generic count gate.
7. **Cost:** unmeasured — would need runtime instrumentation. No documented cost figure found in
   the repo for this sub-table (it shares a build pass with `bg_medical_mappings`/`bg_sign_medical`,
   27+9+12=48 rows total, trivially cheap by row count, but no timing was found in text).
8. **Findings → W2:**
   - NOW: `has_writer=false` + `catalog_status=CURRENT` for a `producer_covered` asset is a
     registry-clarity gap, not a correctness bug — W2 should confirm `asset_kind`/disposition
     reads unambiguously as producer-covered-by-`bg_medical_mappings`, citing D-SERVICE (cockpit
     truth clause, §N.4).
   - NEVER/LATER: adding a formal `grounding_tier` column is out of scope for a single L0 asset —
     defer to the L2 grounding-matcher work named in plan §5, since D-GROUNDING's schema landing
     point is L2, not L0.

---

## bg_dignity_reference

1. **Pillars:** D-GROUNDING (every row cites BPHS/JP/PD/UK/Saravali) and D-SERVICE (it is a core
   strength/condition primitive many downstream engines depend on). Still the right instrument —
   a compact, citation-carrying, classically-sourced reference set; no role change indicated.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct — the
   writer (`bg_dignity_reference.py`) reads only its own static Python literals plus
   `brahmagyan/l0_dignity_reference.py` (the dignity-degree table, extracted per PAR-R-6 so the
   serving-side `dignity_oracle.py` shares one source rather than two). No live DB reads at build
   time. depends_on is accurate.
3. **Leverage:** strongly plugged in — `ga_condition_writer.py` (L1), `dignity_oracle.py` (shared
   serving-side classifier), `ka_vighnakara.py` (L3), plus four dedicated MCP retrieval
   capabilities (`query_motion_state_thresholds.ts`, `query_combustion_orbs.ts`,
   `query_graha_naisargika_friendship.ts`, `query_avastha_schemes.ts`). No unplugged-consumer
   defect found; this is one of the better-leveraged L0 reference tables in the batch.
4. **Grounding:** pure reference/statistical data by design — every row is already a citable
   classical fact (exaltation degree, friendship relation, avastha determination rule), each with
   its own `classical_citation` column. This is squarely `sruti`-tier content; no interpretive
   claim is synthesized here, so a uniform `grounding_tier` mandate would be redundant with the
   citation column already present (per plan §2, grounding is applied selectively, "never as a
   uniform per-row mandate" — this asset is a good illustration of why: it's already self-citing).
5. **Temporal identity:** N/A — static classical reference, chart- and time-independent.
6. **Service:** confirmed real, multi-consumer (see §3). Floor = 151 (9+72+35+27+8, exact sum,
   not aspirational). `count_sql` sums five sub-tables; sane. `integrity_check_sql` is unusually
   thorough — validates graha-set completeness across all five sub-tables, friendship-matrix
   symmetry/self-exclusion, and exact string-concatenated content for avastha states and motion
   thresholds. This is one of the most rigorous integrity checks in the batch.
7. **Cost:** unmeasured — would need runtime instrumentation. No documented build/serve cost
   figure found in the repo.
8. **Findings → W2:** no MUST-level defects found. NOW candidates: none required — this asset is
   already well-grounded, well-leveraged, and well-tested (dedicated `test_bg_dignity_reference.py`
   exists). Recommend W2 record a `verified_reuse`- or `rebuild_only`-class disposition with no
   remediation work, i.e. a clean pass.

---

## bg_class_priors

1. **Pillars:** D-SALIENCE (this is precisely the "class priors" feed plan §5 asks W1 to verify
   as real) and secondarily D-SYNTHESIS (feeds composite/convergence scoring downstream). Still
   the right instrument — role unchanged.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct — the
   writer (`bg_class_priors.py`) calls `brahmagyan.l0_class_priors.seed_class_priors(ctx.db_conn,
   ...)`, which inserts static, ratified Python literals (`CLASS_ROWS` etc.) — no upstream table
   reads. depends_on is accurate. One naming note: `english_description` cites "171" rows and
   `target_floor: 171`, while the writer module's own docstring/comment says "165 rows" and the
   `run()` notes string says "17 classes + 12 subsystems + 6 traditions + 30 vargas + 99
   graha×domain" (17+12+6+30+99 = 164, and elsewhere +1 for a header/sentinel convention could
   explain the drift to 165 or 171) — the three numbers (171 registry floor, 165 module docstring,
   164 from the writer's own itemized note) do not agree with each other. This is a real,
   concrete, checkable discrepancy worth flagging (see §8).
3. **Leverage:** genuinely well-plugged — real consumers include `ka_kshetra` (`stage4_field.py`,
   `stage8_spec.py`), `bo_laksana.py` (L2), `mi_kula.py` (L5), `bg_class_lifetime_counts.py`, and a
   dedicated MCP capability (`query_class_priors.ts`). This is a live D-SALIENCE feed, not a
   dormant table.
4. **Grounding:** each prior row carries `citation` and `ratified_by` columns (per the integrity
   SHA's field list: `citation, ratified_by, prior_basis, source_ref`) and a `contested` flag —
   i.e. the asset already distinguishes ratified/cited priors from contested ones. This is closer
   to `yukti` (principle-derived, cited) than `sruti` — priors are derived judgments about class
   weight, not verse-direct facts, and the schema already supports labeling that (via `citation`/
   `prior_basis`), so a formal `grounding_tier` value would be a natural, low-cost addition rather
   than new machinery.
5. **Temporal identity:** N/A — global, chart- and time-independent priors.
6. **Service:** real consumer confirmed (§3). `count_sql` filters `WHERE prior_version='1.0'`, and
   the natural-key partition documents versioning (`prior_version=1.0; (signal_type_class,
   fact_kind, source_subsystem, signal_tradition)`) — sane and specific.
   `integrity_check_sql` pins exact count AND a content SHA-256, ordered deterministically — a
   strong check.
7. **Cost:** unmeasured — would need runtime instrumentation.
8. **Findings → W2:**
   - MUST-candidate (documentation/registry-vs-code consistency, not proven data-correctness
     defect): the "171" (registry `english_description`/`target_floor`), "165" (writer module
     docstring), and "164" (writer's own itemized 17+12+6+30+99 breakdown in `run()`'s notes
     string) figures for this asset's row count disagree with each other. This should be verified
     against the live count and reconciled at W2/W3 — CLAUDE.md §B.8 (versioning discipline:
     "registries must not disagree") makes this the relevant class of defect. Flagged as a
     finding, not asserted as which number is wrong — an honest "needs reconciliation" per §N.8
     rather than a guess.
   - Per plan §5's explicit ask: class priors ARE verified real (ratified Python literals with
     citations, DR-3/CR-100-class ratification provenance visible in the source, live multi-layer
     consumers) — this is not a stub or placeholder table.
   - NOW: consider adding a `grounding_tier='yukti'` label per row (schema already carries the
     supporting `citation`/`prior_basis` columns) — cite D-GROUNDING, low bounded cost (schema
     column + writer literal tagging, no new computation).

---

## bg_vidhi_primitives

1. **Pillars:** D-SERVICE primarily (this is the registry that maps abstract "primitive" reads to
   live MCP tool names — the backbone of the Vidhi compiler) and D-SYNTHESIS secondarily (floors
   built from these primitives compose the deepdive verdict). Still the right instrument — its
   entire purpose is being the single normalized source the compiler and the DB both read from.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct — the
   writer holds `PRIMITIVE_ROWS` as static literals; no DB reads. depends_on is accurate. Note:
   this writer is explicitly a **content mirror** of `platform/src/lib/vidhi/registry_data.ts`
   (the TS file the compiler and tests actually read), kept in lockstep by a CI parity gate
   (`check_vidhi_registry_parity.mjs`) rather than by hand — a real, verifiable "one canonical
   source enforced by CI" design, not an unverified claim.
3. **Leverage:** consumed by `platform/src/lib/vidhi/types.ts` / `registry_data.ts` (TS mirror,
   compiler-facing) and `platform-mcp/src/resources/vidhi/types.ts`. The DB copy
   (`vidhi_primitives` table) itself has no dedicated MCP query capability under
   `platform/src/lib/retrieval/registry` — its stated purpose is "V-2's MCP-resource face" (per
   its own docstring), i.e. the DB row is meant to BE the resource, not to be wrapped by a
   separate query tool. This is a design choice (resource-not-tool), not obviously a
   built-but-unplugged defect, but W2 should confirm the V-2 MCP-resource face is actually live
   and reachable, since the docstring's claim was not independently verified here (no MCP resource
   registration for `vidhi_primitives` was found under `platform-mcp/src` beyond the types file).
4. **Grounding:** this is ritual/electional-adjacent registry content (per the task's flag) but its
   actual rows are not classical interpretive claims — each row is a primitive's *definition +
   live-tool mapping + fallback face + known_gap CR pointer*, i.e. engineering/routing metadata,
   not a Jyotish assertion needing sruti/yukti/pratyaksa labeling. `grounding_tier` does not apply
   to this table's content; the actual interpretive grounding happens downstream when a primitive
   is invoked against a chart. No gap found here.
5. **Temporal identity:** N/A — chart-agnostic registry of primitive definitions, no time question.
6. **Service:** consumer confirmed at the TS/compiler layer (§3); floor = 60 primitives (matches
   the writer's `len(PRIMITIVE_ROWS)`, verified by inspection — 52 base + the ṢAḌ-DARŚANA W5
   `kala_*` block of 8 = 60). `count_sql` is a simple count; sane. `integrity_check_sql` pins exact
   count + a content SHA-256 over all ten columns, ordered by `primitive_id` — strong and specific.
7. **Cost:** unmeasured — would need runtime instrumentation.
8. **Findings → W2:**
   - NOW: verify the "V-2 MCP-resource face" claim in the writer's own docstring is actually
     live/reachable (no resource registration was found for `vidhi_primitives` beyond the TS types
     file) — cheap to check, cite D-SERVICE ("every active asset has a consumer or a recorded
     disposition").
   - NEVER/LATER: no grounding-tier work needed on this table — its content is routing metadata,
     not interpretive claims.

---

## bg_formula_constants

1. **Pillars:** D-GROUNDING partially (constants carry `citation_or_ratification`) but mainly a
   cross-cutting substrate asset — it underlies almost every numerically-graded computation
   (combustion orbs, dignity scores, house weights, attention budget, calibration constants) used
   by L1–L5 writers. Still the right instrument; role unchanged. `data_disposition:
   RETAINED_AS_CAPITAL` in the registry signals this was already deliberately preserved rather
   than retired, consistent with its wide fan-out.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct — the
   writer calls `brahmagyan.l0_formula_constants.seed_formula_constants(ctx.db_conn, ...)`, which
   (per the writer's notes string) inserts CLASSICAL / NATIVE_JUDGMENT / ENGINEERING /
   conflation_bug-classed literals; no upstream reads at build time. depends_on is accurate.
3. **Leverage:** heavily consumed — real reads found in `mi_pramana.py`, `mi_gunanaka.py`,
   `mi_pariksha.py`, `ph_rectification/__init__.py`, `services/mimamsa/lel_calibration.py`,
   `services/ph_nimitta/base_rate.py`, `platform/src/lib/build/recalibrationEnqueue.ts`, plus a
   dedicated MCP capability (`query_formula_constants.ts`). One of the most widely-leveraged
   assets in this batch — no unplugged-consumer defect found.
4. **Grounding:** the asset's own class column already discriminates
   CLASSICAL/NATIVE_JUDGMENT/ENGINEERING (and reserves a `conflation_bug` class the integrity
   check explicitly asserts must be zero rows — `count(*) FILTER (WHERE class='conflation_bug') =
   0` — i.e. this table has its own hard-floor guard against exactly the kind of "unresolved
   defect operationalized as a constant" failure mode its own `english_description` warns against).
   This is closer to a mix of `sruti`/`yukti`/`pratyaksa` depending on class — CLASSICAL rows are
   citable (sruti/yukti), ENGINEERING rows are `pratyaksa` (instrument-emergent, no classical
   claim). The `class` column is doing informal grounding-tier work already; formalizing it as
   `grounding_tier` would be a natural low-cost mapping (CLASSICAL→sruti/yukti,
   ENGINEERING→pratyaksa, NATIVE_JUDGMENT→yukti) rather than new derivation work.
5. **Temporal identity:** N/A — global calibration/formula constants, chart- and time-independent.
6. **Service:** consumer confirmed, widely (§3). Floor = 17 (exact, matches
   `count(*) FILTER` logic in integrity check). `count_sql` is a simple count; sane.
   `integrity_check_sql` both pins exact count/content SHA-256 AND asserts zero
   `conflation_bug`-classed rows — a meaningful correctness guard, not just a row-count gate.
7. **Cost:** unmeasured — would need runtime instrumentation.
8. **Findings → W2:** no MUST-level defects found. NOW candidate: consider mapping the existing
   `class` column onto a formal `grounding_tier` value (bounded, cheap, reuses existing
   classification — cite D-GROUNDING). Given its wide fan-out into L4/L5 calibration surfaces, W2
   should also confirm this asset is scheduled early/`rebuild_only` so downstream calibration
   writers are never staled by a late-arriving constants change (invalidation-cascade economics,
   plan §1).

---

## bg_sky_calendar

1. **Pillars:** D-TIME — this is exactly the "ephemeris/sky-calendar" feed plan §5 names for
   verification. It is the right instrument for a chart-independent sky-event almanac; its own
   docstring draws an explicit, reasoned scope boundary against per-chart joins (deferred to
   `ka_kshetra`) and against the node-luminary-proximity eclipse proxy (uses real
   `sol_eclipse_when_glob`/`lun_eclipse_when` instead) — a genuinely considered design, not a
   placeholder.
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct at the
   DB-dependency level (chart-independent, no upstream writer table reads) — the writer computes
   live via `pyswisseph` (through `pipeline.transit_search`'s existing `find_ingress_events`,
   `find_station_events`, `find_conjunction_events`, reused as-is per the writer's own "do not
   reimplement astronomical math" note) plus direct `sol_eclipse_when_glob`/`lun_eclipse_when`
   calls for eclipses. No mismatch found between declared and actual reads.
3. **Leverage — the notable finding for this asset:** `bg_sky_calendar` has **no dedicated MCP
   retrieval capability** under `platform/src/lib/retrieval/registry` or `platform-mcp/src` (no
   `query_sky_calendar.ts`-equivalent file exists, unlike its sibling `bg_muhurta_lattice`, which
   does have one). Its only real consumers found are: (a) `w26_real_eclipses.py`
   (`services/gochara_v3/mechanisms/`) — a genuine internal consumer sourcing eclipse events from
   this table for L3 gochara computation; and (b) `ka_kshetra.py`'s own docstring, which explicitly
   lists `bg_sky_calendar` as **NOT yet an edge** ("· NOT bg_sky_calendar — the W3 edge-staging
   rule (§9.1); W3 adds it in the same PR that lands that asset's seed row") — i.e. the
   chart-contact join plan §5/the ṢAḌ-DARŚANA brief describes is explicitly staged as future work,
   not silently missing. This is a disclosed, intentional deferral for the `ka_kshetra` join, but
   the absence of ANY query surface for LLM-facing consultation (an analyst or MCP tool cannot
   currently ask "what ingresses happened in window X" against this table at all) is a genuine
   built-but-unplugged gap distinct from the disclosed `ka_kshetra` deferral.
4. **Grounding:** `pratyaksa` — this is instrument-emergent computational output (real ephemeris
   positions/eclipse timings), not a classical textual claim; the writer's own
   `source_citation` field (per the integrity check: `'pyswisseph DE441 (Swiss Ephemeris) via
   pipeline.transit_search + sol_eclipse_when_glob/lun_eclipse_when; Lahiri ayanamsha'`) already
   states its computational provenance plainly. No classical citation is claimed and none should
   be — correct as-is.
5. **Temporal identity (L3 concern):** the question this asset answers is "when did/will this sky
   event (ingress/station/eclipse/double-transit) occur, globally, independent of any chart?" It
   is explicitly NOT the "does this event touch THIS native's chart" question — that arbitration
   is deferred to `ka_kshetra` (L3), which per its own docstring has not yet wired the edge. No
   L3 arbiter currently consumes this table for chart-contact purposes; the one live L3-adjacent
   consumer (`w26_real_eclipses.py`, gochara_v3) uses it for eclipse-mechanism detection, not
   general temporal arbitration. This asset therefore currently answers a D-TIME *input* question
   without yet being wired into a D-TIME *arbiter* — consistent with plan §5's phrasing that
   verification here means confirming the feed is real, which it is; the arbitration wiring is
   named L3 work, not L0's.
6. **Service:** floor = 31,059 (event-count minimum across the 5 event types); `count_sql` is a
   simple count; sane. `integrity_check_sql` is thorough: minimum counts per event_type, natural-
   key uniqueness, non-empty `primary_body`, exact `secondary_body_key` derivation, non-null
   timestamps, pinned `ayanamsha_key='lahiri'` and `sampling_method`, and a rolling-horizon check
   (`min < 1900-02-01`, `max >= today+9y`). This is a strong, self-verifying integrity check. As
   noted in §3, "real consumer" is a mixed picture: one genuine internal Python consumer exists,
   but zero LLM/MCP-facing query surface exists yet.
7. **Cost:** unmeasured — would need runtime instrumentation. The writer's own docstring cites one
   performance figure for a *sub*-computation, not the full build: "9 planets x 12 signs x 5-year
   window = 1055 events in ~0.47s locally" for the ingress cache-hit behavior — this is a partial,
   narrow benchmark (not the full ~31k-row, 1900–2036 build), so it should not be read as "the
   asset's build cost" without further measurement.
8. **Findings → W2:**
   - Per plan §5's explicit ask: bg_sky_calendar's D-TIME feed IS verified real — genuine
     pyswisseph computation (not a stub/seed table), with a strong integrity check and a
     documented, reasoned scope boundary (chart-independent only; eclipse visibility and returns
     explicitly excluded and explained).
   - NOW: add a dedicated MCP/retrieval query capability for `bg_sky_calendar` (D-SERVICE — "every
     active asset has a consumer or a recorded disposition"; currently it has one narrow internal
     consumer and no general-purpose one, unlike its sibling `bg_muhurta_lattice`). Bounded cost:
     one new capability file mirroring `query_muhurta_lattice.ts`'s pattern.
   - NEVER/LATER (for THIS wave): the `ka_kshetra` chart-contact join is explicitly staged as W3
     work per `ka_kshetra.py`'s own docstring — out of scope for L0-W1, tracked, not forgotten.

---

## bg_vidhi_floors

1. **Pillars:** D-SERVICE (this is the compiled scope_tuple→contract input that assembles a
   deepdive's actual reading — the floor is literally the served content plan) and D-SYNTHESIS
   (floor composition is what turns primitive atoms into one coherent verdict-supporting read).
   Still the right instrument for its purpose.
2. **Real vs declared dependencies:** registry declares `depends_on: ["bg_vidhi_primitives"]`.
   Confirmed correct AND necessary — `vidhi_floor_items.primitive_id` is an FK into
   `vidhi_primitives` (per the writer's own docstring: "Depends on bg_vidhi_primitives (FK:
   vidhi_floor_items.primitive_id)"), and the writer's `run()` inserts floor items referencing
   `primitive_id` values that must already exist. depends_on is accurate and this is the one
   asset in the batch with a real (not empty) dependency edge.
3. **Leverage:** same TS-mirror/compiler pattern as `bg_vidhi_primitives` — consumed by
   `platform/src/lib/vidhi/registry_data.ts`/`types.ts` and `platform-mcp/src/resources/vidhi/
   types.ts`; kept in lockstep with the DB copy by the same `check_vidhi_registry_parity.mjs` CI
   gate. No dedicated MCP query capability for the DB table itself was found (same caveat as
   `bg_vidhi_primitives` — the DB row is meant to be the V-2 resource face, not wrapped by a
   separate tool; unverified whether that resource registration is actually live).
4. **Grounding:** floor items are compiled routing content (which primitive, in what order, at
   what band, with what args), not classical claims themselves — `grounding_tier` doesn't apply to
   floor *structure*. However, each floor's `cr27_coverage` and per-item `hard_floor` flag already
   function as a documented rationale trail (which CR-27 improvisation instances a floor
   guarantees against) — this is process/coverage metadata, correctly distinct from Jyotish
   grounding.
5. **Temporal identity:** N/A — floor composition is chart-agnostic routing content.
6. **Service:** consumer confirmed via the TS/compiler mirror (§3). Floor = 423
   (`vidhi_intent_floors` count + `vidhi_floor_items` count). `count_sql` sums both tables; sane.
   `integrity_check_sql` checks exact sub-counts (14 intent floors, 409 floor_items), per-intent
   `item_order` contiguity (`lo=1, hi=n, distinct_orders=n` — catches gaps/duplicates in ordering),
   and full referential integrity via LEFT JOINs against both `vidhi_intent_floors` and
   `vidhi_primitives` (`WHERE floor.intent IS NULL OR primitive.primitive_id IS NULL`) — this is a
   genuinely strong FK-completeness check, appropriate given the real dependency in point 2.
7. **Cost:** unmeasured — would need runtime instrumentation.
8. **Findings → W2 — the flagged status signal:**
   - **`catalog_status: "DRAFT"`, unlike every other asset in this batch (all `CURRENT`).** This is
     the single most notable status signal in the batch and is flagged here explicitly per the
     task's instruction, without asserting what it means — it could mean (a) the floor content is
     still being iterated pre-ratification, (b) the DRAFT tag is stale/should have flipped to
     CURRENT alongside its dependency `bg_vidhi_primitives` (which IS `CURRENT`), or (c) something
     about the 14-intent floor set is deliberately provisional (e.g. the newer
     `spirituality_deepdive`/`education_deepdive`/`progeny_deepdive` floors are marked
     `[MANDATORY]`/`[CANDIDATE]` in their own `notes` field within the writer, suggesting active,
     not-yet-fully-settled content). W2 should resolve this explicitly with a disposition decision
     — it is a correctness-adjacent status question (does the schema/registry status accurately
     reflect the content's actual maturity?), which is exactly the kind of registry-disagreement
     class CLAUDE.md §B.8 flags, so it is triaged **MUST** (status accuracy gates whether this
     asset can be treated as frozen content) rather than NOW, pending W2's actual disposition call.
   - NOW: as with `bg_vidhi_primitives`, verify whether the DB table's "V-2 MCP-resource face" is
     actually live/reachable — same unverified claim, same low cost to check.
   - No data-integrity defect found — the FK-completeness and ordering checks in the
     `integrity_check_sql` are strong and, as far as static review can tell, self-consistent.

---

## bg_muhurta_lattice

1. **Pillars:** D-TIME (electional/muhūrta substrate — one of plan §5's named D-TIME feeds
   alongside sky-calendar) and D-GROUNDING (every factor row carries `source_citation` and a
   `corpus_status` of `computed_cited` or `computed_uncited_convention`, honestly distinguishing
   cited classical content from uncited-but-live convention). Still the right instrument — the
   writer's docstring draws the same kind of careful, disclosed scope boundary as
   `bg_sky_calendar` (reference-location honesty, the `compute_day_muhurtas` midpoint-approximation
   caveat disclosed rather than silently assumed, per-chart contact joins deferred to
   `ka_kshetra`).
2. **Real vs declared dependencies:** registry declares `depends_on: []`. Confirmed correct at the
   DB level — the writer computes via `panchang_engine` (reused wholesale, same "do not
   reimplement classical-rule math" discipline as `bg_sky_calendar`), not via reads of other
   `bg_*`/`ga_*` tables. `has_substeps: true` (unlike every other asset in this batch) reflects the
   genuinely heavy compute (~165K rows across 9 factor families over a rolling window) — consistent
   with a substep-chunked writer, not a mismatch.
3. **Leverage — the notable finding for this asset:** a real MCP query capability exists
   (`query_muhurta_lattice.ts`), but **its `FACTOR_FAMILIES` allowlist covers only 4 of the 9
   factor families the writer actually produces and the DB constraint allows.** The capability's
   own constant is `const FACTOR_FAMILIES = ['agnivasa', 'combination_yoga', 'kalam',
   'ghati_muhurta'] as const`, and its `factor_family` argument validation rejects any other value
   with `factor_family must be one of: ${FACTOR_FAMILIES.join(', ')}`. Migration
   530 (`530_bg_muhurta_lattice_panchangika_families.sql`) added five more families —
   `hora`, `lagna`, `nakshatra`, `tithi`, `vara` — which the writer's own v2 `sampling_method`
   integrity check requires (minimum row counts: hora ≥43,824, lagna ≥23,798, nakshatra ≥1,826,
   tithi ≥1,826, vara ≥1,826 — roughly 72,580 of the table's ~165K rows, i.e. well over a third of
   the corpus). A caller cannot explicitly filter to any of these five families through this
   capability today — it 400s. (Omitting the filter entirely returns everything up to
   `MAX_ROWS=2000`, so the data is not fully unreachable, but targeted retrieval of the newer
   families is blocked, and the capability's own description text — "Four chart-independent factor
   families... Omit for all four" — is now inaccurate: it should say nine.) This is a concrete,
   verifiable partial-serving gap, squarely the kind of thing D-SERVICE's "built-but-unplugged"
   defect class (plan §2) names.
4. **Grounding:** per-row `corpus_status` (`computed_cited`/`computed_uncited_convention`) is
   already doing grounding-tier-shaped work, disclosed honestly rather than uniformly upgraded —
   this is a good existing model for what a formal `sruti`/`yukti`/`pratyaksa` labeling could build
   on later (computed_cited → sruti/yukti depending on the citation type; computed_uncited_
   convention → pratyaksa, since it is instrument-emergent convention without a classical source).
   No fabricated citation was found; the writer's docstring explicitly documents which underlying
   `shastra_tables.py` tables lack inline citations and marks those rows accordingly.
5. **Temporal identity (L3 concern):** the question this asset answers is "what
   muhūrta-relevant classical factor windows (agnivasa/yoga-spans/kālams/ghaṭīs/horas/lagnas/
   nakshatra-tithi-vara boundaries) hold at reference location Bhubaneswar/IST over the next ~5
   years?" — explicitly NOT "is this window good for THIS native," which is `ka_kshetra`'s
   deferred job per this writer's own docstring (mirroring the `bg_sky_calendar` deferral pattern).
   No L3 arbiter currently consumes this table for chart-contact purposes (no evidence found of
   `ka_kshetra` joining it yet, consistent with the `bg_sky_calendar` §3 finding that the join is
   staged, not landed). `bg_parihara_rules.py` is a genuine current consumer, but for remedy-rule
   citation cross-referencing (mapping remedy rules to specific `factor_family`/`factor_key`
   values), not temporal arbitration.
6. **Service:** floor = 91,477 (registry `target_floor`) vs. the writer's own integrity check,
   which requires the v2 corpus alone to be ≥164,575 rows — the registry `target_floor` appears to
   be a stale/lower bound relative to what the writer's own integrity check now demands (v2 lattice
   landed via migration 530 after some earlier floor was set, per the "Migration 530's nine-family
   v2 lattice is binding" comment in the integrity SQL itself). `count_sql` is a simple count;
   sane. `integrity_check_sql` is very thorough: per-family v2 minimums, natural-key uniqueness,
   non-empty keys, `end_utc > start_utc`, pinned reference location/ayanamsha, closed
   `sampling_method`/`corpus_status` enums, and a rolling-horizon check.
7. **Cost:** unmeasured — would need runtime instrumentation. No documented full-build timing
   figure was found (unlike `bg_sky_calendar`'s partial ingress-cache benchmark, no comparable
   number appears in this writer's comments).
8. **Findings → W2:**
   - MUST-candidate: the `factor_family` filter allowlist in `query_muhurta_lattice.ts` is
     incomplete relative to the writer's own v2 corpus (4 of 9 families filterable), and the
     capability's description text is now factually wrong ("Four... Omit for all four"). This is a
     correctness/consistency defect in the serving layer, not merely a nice-to-have — flag as
     **MUST** for W2, citing D-SERVICE's built-but-unplugged defect class.
   - NOW: reconcile `target_floor` (91,477) against the writer's own binding v2-corpus minimum
     (164,575) — the registry floor looks stale post-migration-530; cite CLAUDE.md §N.4 (floors
     are aspirational/achieved-count, not fabricated, so a floor that has drifted below what the
     writer itself now guarantees should be raised to match, bounded/cheap: a registry-value edit).
   - Per plan §5: this is a genuinely computed D-TIME feed (real `panchang_engine` computation, not
     a stub), consistent with the same verification plan §5 asks for `bg_sky_calendar`.
   - NEVER/LATER (for THIS wave): the `ka_kshetra` chart-contact join is explicitly W3-staged per
     this writer's own docstring, same disposition as `bg_sky_calendar` §8.
