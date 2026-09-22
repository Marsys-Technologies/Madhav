---
artifact: LANE_D_ASSET_REGISTER
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_id: LANE_D_ASSET_REGISTER
scope: >
  Per-asset readiness register for the L3 Kāla assets NOT covered by the Kshetra/Sangam/Gochara
  lane: every active `ka_*` identity except `ka_kshetra`, `ka_sangam`, and the Gochara family
  (`ka_gochara`, `ka_gochara_resonance`, `ka_gochara_sweep`, `ka_vedha_gochara`,
  `ka_gochara_v3_century_materialize`).
produced_by: L3 Kāla readiness audit, Lane D (autonomous, Claude Code)
canonical_chart_id: "482012f1-710e-4a25-994a-93821f5871aa"
baseline_read_first: >
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md,
  KALA_DATA_CENSUS_v1_0.md, KALA_DAG_RECONCILIATION_v1_0.md,
  KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md,
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md — this
  document does not re-run that audit; it cites it by section, adds a small number of new
  direct code/DB checks (marked "Lane D direct check"), and renders the per-asset synthesis the
  audit's own cluster-report format did not produce.
---

# LANE D — L3 KĀLA PER-ASSET READINESS REGISTER

## 0. Roster reconciliation (resolve-yourself requirement)

Live `asset_registry` query (Lane D direct check, `SELECT asset_id FROM asset_registry WHERE
asset_id LIKE 'ka_%'`) returns **23 rows**. Of these, **22 are active** (registered writers) and
**1 is retired**: `ka_gochara_sweep` has a row in `asset_registry` and a file on disk
(`writers/ka_gochara_sweep.py`) but does **not** register with the orchestrator —
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` Domain C confirms "live count = 22 `ka_*` writers
registered... `ka_gochara_sweep.py` exists on disk but does not register — confirmed retired,"
and its own `asset_throughput` row (Lane D direct check) reads
`error | 0 | ... | no writer registered for ka_gochara_sweep`. So **22/22 matches the brief's
stated denominator** — no discrepancy to report there.

**This lane's scope is 16 assets**, arrived at as: 22 active − 6 active identities in the excluded
set (`ka_kshetra`, `ka_sangam`, `ka_gochara`, `ka_gochara_resonance`, `ka_vedha_gochara`,
`ka_gochara_v3_century_materialize`; the 7th excluded name, `ka_gochara_sweep`, is already retired
and not part of the 22-count either way). This matches the brief's own worked example list of 17
names *minus* `ka_temporal` — **`ka_temporal` is not a registered asset_id** (confirmed: it is
absent from the 23-row `asset_registry` query above). It is a shared **service module**
(`platform/python-sidecar/services/ka_temporal/`) imported by four writers
(`ka_kalasutra`, `ka_vighnakara`, `ka_yojaka`, and the century materializer — see Clusters §2
below) — real code, real hub role, but not itself an elevation-tracked asset. Flagged as a
discrepancy between the brief's example roster (17 names) and the true active+in-scope count
(16), not silently corrected.

**Final 16-asset roster for this register:** `ka_avadhi`, `ka_bhavishya_lekha`, `ka_dasha_kala`,
`ka_graha_sancara`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_kota_chakra`,
`ka_moorti_nirnaya`, `ka_muhurta_seva`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`,
`ka_tulana`, `ka_vighnakara`, `ka_yojaka`.

**Data sources used throughout:** live `asset_registry` and `asset_throughput` queries (Lane D
direct check, read-only, `chart_id='482012f1-710e-4a25-994a-93821f5871aa'`), the audit's
`KALA_DATA_CENSUS_v1_0.md` (F7, canonical + global row counts), `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`
(disposition/consumer findings), `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` (F1–F8, Domains A–J),
`KALA_DAG_RECONCILIATION_v1_0.md` (F3), and direct reads of writer source under
`platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py` and
`platform/python-sidecar/services/ka_*/`.

---

## 1. `ka_avadhi`

**1. WHAT IT COMPUTES.** For each chart, walks `chart_dashas` (MD+AD, all 7 systems) and emits one
period-dossier row per period: lord-condition **references** (fact_ids only — never restates a
computed value, per the file's own "BA trap-1 guard" comment), `activated_pratijna_ids` (L2
`bo_pratijna` IDs whose domain maps to the lord's significations and whose window overlaps), and an
AD-lord `sublord_modulation`. Classical technique: Vimśottarī/multi-system daśā period enumeration
with L2-referenced (not re-derived) interpretive linkage — a period dossier, not an independent
astrological computation. (`writers/ka_avadhi.py:1-18`)

**2. OUTPUT.** Target table `kala_avadhi`, grain chart × clock-system × level × start. Canonical
chart row count **1,169** (census, single build timestamp 2026-08-12). Live `asset_throughput`
state (Lane D direct check): **`error`**, `rows_written=1169`, `last_error`: `post-write integrity
check failed: integrity_check_sql → False`. **Claimed-vs-actual: count matches (1,169 = 1,169)**,
but the row is honestly in `error` state because a post-write integrity check fails — the data
exists but the writer's own contract says it should not be trusted as complete/correct. This is a
distinct defect class from the cascade-wipeout pattern seen elsewhere in this layer (§Cross-cutting
below): here the rows are physically present and counted correctly, but the writer's own
self-check disagrees with its own output.

**3. INPUTS.** `depends_on` (live registry): `{ga_dashas, bo_pratijna, bg_ghatana}`. **Undeclared
read confirmed** (`KALA_DAG_RECONCILIATION_v1_0.md §5`, independently visible at
`writers/ka_avadhi.py:29`): `from services.ka_dasha_kala.tree_walk import ALL_DASHA_SYSTEMS` — a
constant/vocabulary import from `ka_dasha_kala`, which does not appear in `ka_avadhi`'s
`depends_on` anywhere. The audit judges this "unlikely to be a real ordering bug" since it is a
Python constant import, not a table read, but it is structurally invisible to `dag_edge_guard.py`.

**4. CONSUMERS.** LIVE: `platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts`,
reached via `platform-mcp/src/tools/retrieval/kala_temporal.ts`
(`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` Spine #1; file presence independently confirmed, Lane
D direct check: `grep -rl kala_avadhi platform-mcp/src/tools platform/src/lib/retrieval`). No
U01–U11 product-interface item names `ka_avadhi` directly — the live consumer capability exists
outside the numbered obligation list (orphan obligation, not orphan work).

**5. DEFECTS.**
- Post-write integrity-check failure, live today (`asset_throughput.last_error`) — the single
  clearest, freshest defect signal of any asset in this register; needs its own root-cause pass
  before anything else here matters.
- Ten-row truncation: `writers/ka_avadhi.py:142` (`LIMIT 10`) and `:290`
  (`list(dict.fromkeys(activated_ids))[:10]`) — undisclosed caps on lord-condition refs and
  activated-pratijna lists (REGISTER:153, STRAT:282 "ten-row limits").
- Missing ayanamsha in the natural key and fixed-domain/soft-empty behavior — named in
  STRAT:282, not independently re-verified beyond the citation (COULD NOT VERIFY the exact schema
  column within Lane D's budget).

**6. BUILD REALITY.** Registered writer, LIGHT kind (single `run(ctx)`). Reads L1 `chart_dashas` +
L2 `bo_pratijna`/`bg_ghatana` — none of these are in F4's known-inaccessible-table list, so no
privilege block is expected. Cost driver: one row per daśā period per system (bounded, not
ephemeris-heavy). **Currently cannot be honestly called buildable-and-clean**: the live state is
`error` from its own integrity check, so a rebuild today would need that check's failure diagnosed
first, not merely a re-run.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q8** ("what is the honest truncation policy? every
cap... must become either complete coverage or an explicit, reported bound") names `avadhi`
directly among its six affected assets. A native ruling on Q8 is a precondition for closing this
asset's own truncation defects, and the live integrity-check failure is an open, undiagnosed
build-state defect on top of that — this is a design-decision-gated asset, not a pure bug-fix one.

---

## 2. `ka_bhavishya_lekha`

**1. WHAT IT COMPUTES.** "Probabilistic forward projection artifact" (module docstring). Reads
ranked signals and produces up to 100 forward-looking projection rows (rank, tier, probability
label, domain, window, falsifier, source), while separately preserving previously **issued**
outcome records across rebuilds via a `(signal_id, peak_date)` identity match
(`_reattach_outcome`/`_outcome_identity`, `writers/ka_bhavishya_lekha.py:16-33`) — explicitly so a
rebuilt projection that already had an observed outcome does not silently lose it, and so an
unmatched projection is never given "someone else's outcome." This is a synthesis/packaging asset,
not a classical technique in its own right — it re-ranks and packages signals sourced from
`ka_kala_darshana`/`ka_vighnakara`/`ka_sangam`/`bo_laksana`.

**2. OUTPUT.** Target table `kala_bhavishya`, grain chart × rank. Canonical chart row count
**0** (census — table is globally non-empty, 100 rows, all owned by a different chart,
`1c826d5a-…`). Live `asset_throughput` (Lane D direct check): state **`stale`**,
`rows_written=100`, `last_built_at=2026-08-13`, no `last_error`. **Claimed-vs-actual: CONFIRMED
MISMATCH** — the throughput row says 100 rows were written for this chart; the live table has 0.
This is the CASCADE pattern documented in the audit's `DATA_LOSS_DIAGNOSIS.md` (cited via
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F7 cross-reference): migration
`403_kala_signal_fk_cascade.sql` put `ON DELETE CASCADE` from this table's `signal_id` to
`bodha_msr_signals.signal_id`; `bo_laksana`/`bo_laksana_rerank` reissued fresh `signal_id`s on
2026-09-08/2026-09-11, after this writer's 2026-08-13 run, silently deleting the rows this asset
had written. `state='stale'` is set, but nothing escalates "stale AND now-empty" as distinct from
ordinary staleness.

**3. INPUTS.** `depends_on`: `{ka_kala_darshana, ka_vighnakara, ka_sangam, bo_laksana}` — all three
of `ka_kala_darshana`/`ka_vighnakara`/`ka_sangam` ultimately trace to `ka_sangam` as their common
ancestor (per the traceability matrix's Tension 6 finding), so three of four declared inputs are
one producer counted three times — a "triple-count risk" the audit already names (STRAT:291).

**4. CONSUMERS.** LIVE, multiple: `platform-mcp/src/tools/kala_views/ahead.ts`,
`platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts`,
`query_temporal_activation.ts` (Lane D direct check confirms all three reference `kala_bhavishya`).
U06 (qualified stages → PACT/promise spine via `ahead.ts`) and U09 (historical
comparison/prospective firewall) both name this asset; U09's firewall logic itself
"COULD NOT VERIFY" per the traceability matrix.

**5. DEFECTS.**
- `writers/ka_bhavishya_lekha.py:249-287` — `phala_anchors` read guarded by `to_regclass()`
  (table-existence check), not a privilege check; **safe on first build, fails on rebuild** once
  `existing_ids` is non-empty (`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F4, confirmed
  build-blocking-on-rebuild, not on first build).
- `writers/ka_bhavishya_lekha.py:155` — `LIMIT 1` (single top-ranked-darshana-window read; see
  file comment at line ~146, "next 5 years").
- `writers/ka_bhavishya_lekha.py:179` — `LIMIT 100`, an in-file comment at line 175 itself flags
  that "of the eligible windows survived LIMIT 100 varied build-to-build" — the cap is
  acknowledged unstable by the code's own comment, not merely externally observed.
- Rank-as-identity instability (REGISTER:156, STRAT:291): `projection_rank` is used as part of the
  row's identity in places but is explicitly noted to move on re-rank — a latent identity bug class
  separate from the reattach-by-`(signal_id, peak_date)` fix already in place.
- Empty-input deletion path (STRAT:291 "fix the empty-input deletion path") — not independently
  re-verified at a specific line within Lane D's budget (COULD NOT VERIFY exact code location).

**6. BUILD REALITY.** Buildable on a first run; the `phala_rectification`/`phala_anchors` privilege
gap (F4) turns a **rebuild** unsafe once rows exist. Cost driver: bounded to `LIMIT 100`, cheap.
Currently non-functional for the canonical chart in the sense that its one populated build has been
cascade-deleted — a rebuild today would re-populate it, but would immediately re-hit the same
CASCADE exposure the next time `bo_laksana` regenerates.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q5** ("prospective claims: what may Bhavishya
assert? Rank-as-identity, five-year/top-100 scope, non-probability meaning, and the firewall
between issued history and rebuildable projection") names this asset by its own short name and
states the question "touches the Ethical Framework directly." This is squarely a design-decision
gate, not a bug list — the CASCADE/privilege defects are real but secondary to the open question of
what this asset is allowed to claim and how issued history is protected from rebuild.

---

## 3. `ka_dasha_kala`

**1. WHAT IT COMPUTES.** Nothing is written to any domain table. The registered writer
(`services/ka_dasha_kala/writer.py`) runs a **self-test only**: asserts all 7 daśā systems
(`vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra`) are present in L1
`chart_dashas` for the canonical chart, checks a query window returns non-empty valid intervals,
and writes `service_health`/`selftest_detail` to `asset_registry` — never `chart_dashas` or any
`kala_*` table (`services/ka_dasha_kala/writer.py:1-30`). The underlying `KaDashaKalaService`
class (used by the self-test) exposes real capability — `confirm_systems_present` and (per the
traceability matrix) a broader traversal/eligibility API — but nothing outside the self-test was
found to call it.

**2. OUTPUT.** `storage_type=service`, no `target_table`, `count_sql` empty (live registry).
`asset_throughput` (Lane D direct check): state **`lit`**, `rows_written=0`, consistent with a
self-test-only service asset — no claimed-vs-actual mismatch (0 is the correct expectation).

**3. INPUTS.** `depends_on`: `{ga_dashas}`. No undeclared-read finding beyond what's already
flagged for the *consumer* side (see Defects).

**4. CONSUMERS.** **NOT-FOUND — confirmed real gap**
(`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F5, `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`
Frontier #2). `call_dasha_eligibility` (the MCP-facing wrapper) runs a raw
`SELECT ... FROM chart_dashas WHERE chart_id=$1 AND ayanamsha_id=$2 ...` directly against L1 —
`grep -rn KaDashaKalaService` outside the self-test path found no hits anywhere in the serving
code. Search scope: `platform-mcp/src/tools/`, `platform/src/lib/retrieval/`, the sidecar's own
`routers/`. **No caller found within that scope** beyond the self-test itself — stated as a search
boundary, not asserted as proof the class is dead code.

**5. DEFECTS.** No truncation/NULL-default/line-level defect found in the writer itself (it is a
self-test, not a data producer). The real defect is architectural: a registered, self-testing
service whose production capability (`KaDashaKalaService`'s traversal/eligibility methods beyond
`confirm_systems_present`) is, on current evidence, never exercised by any production caller — F8's
own PR #2695 finding independently touches the same wrapper (`call_dasha_eligibility` defaults
`ayanamsha_id` to `'lahiri'` instead of canonical `DEFAULT_AYANAMSHA`, `'lahiri_chitrapaksha'` — a
live, unpatched-on-`main` bug in the exact code path that bypasses this asset).

**6. BUILD REALITY.** Trivially buildable — no ephemeris calls, no fan-out, reads a bounded set of
rows from `chart_dashas`. Zero build-cost risk. The open question is entirely about whether the
service is *used*, not whether it *builds*.

**7. ELEVATION TIER: MODERATE.** No open native design question in the elevation plan's Q1–Q8 list
names this asset directly, and the self-test/health-check design is coherent and self-consistent —
but "does this service's own capability reach any consumer, or should the bypass be made official
and the class retired/simplified" is a real, unresolved reconciliation question, structurally the
same shape as elevation-plan Q2 (assets "consumed by nothing today") even though Q2 does not name
`ka_dasha_kala` explicitly. Graded MODERATE rather than HEAVY because the fix path (wire the
consumer to the service, or document the bypass as intentional and retire the unused method
surface) does not require new architecture — it requires a decision to act on evidence already in
hand, which is smaller than the open-ended design questions carried elsewhere in this register.

---

## 4. `ka_graha_sancara`

**1. WHAT IT COMPUTES.** Nothing is materialized. The writer's **sole job**, per its own docstring,
is a FORENSIC self-test: compute ephemeris for the native's exact birth instant (1984-02-05 10:43
IST), assert 9 grahas present with non-null speeds, assert natal Moon sign = Aquarius (a FORENSIC
anchor), then write `service_health='healthy'` + `last_selftest_at` to `asset_registry`
(`writers/ka_graha_sancara.py:1-20`). This is a Swiss-Ephemeris-backed position/motion probe, not
an independent classical technique — it validates the ephemeris substrate other assets assume.

**2. OUTPUT.** `storage_type=service`, no target table. `asset_throughput` state not separately
queried (service, zero rows by design — `WriterResult(rows_inserted=0)` is the writer's declared
contract per its own docstring, so no claimed-vs-actual question arises).

**3. INPUTS.** `depends_on`: `{bg_ephemeris}`.

**4. CONSUMERS.** **DIVERGENT, by design, per the code's own comment** — not treated here as a
defect. `call_ephemeris_at_t` (the production wrapper) calls the sidecar's own
`/api/compute/ephemeris_at_t` route, which does `import swisseph as swe` directly and states
in-file it does this "rather than a second swisseph integration"
(`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F5, `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`
Frontier #1, confirmed high confidence: `grep -n ka_graha_sancara
platform/python-sidecar/routers/ephemeris.py` → zero import/call hits, only a naming comment). No
U-id names this asset.

**5. DEFECTS.** None found in the registered writer itself — the self-test does exactly what it
declares. The only "defect" is a documentation/scope gap: the self-test proves correctness for
**one** arbitrary instant (the native's own birth moment); the disposition register's own required
work is "prove exact conventions, time, arbitrary-chart input, provenance, failures — a canonical
probe is not full service qualification" (REGISTER:134) — i.e. the self-test's scope is narrower
than what "service qualification" would require, not that it is wrong.

**6. BUILD REALITY.** Trivially buildable; single self-test, no materialization, no fan-out.

**7. ELEVATION TIER: LIGHT.** The writer does exactly its declared job and the production
divergence is a documented, deliberate architectural split (avoid a second Swiss Ephemeris
integration), not an unexplained gap — matching the register's own framing that elevation work here
is *proving the self-test's claims hold beyond one FORENSIC instant* (arbitrary chart, arbitrary
time, provenance, failure modes), which is qualification-and-proof work, not rework or a design
decision.

---

## 5. `ka_jivana_parva`

**1. WHAT IT COMPUTES.** Life-arc "chapter" hierarchy: one row per MD/AD/(current-only) PD period,
year-bounds/lord/theme/class, clipped to `[birth_date, ...)` so a pre-birth "balance of dasha at
birth" period is never served as a lived chapter (`writers/ka_jivana_parva.py:1-25` — the clip
logic is explicitly reasoned through in the module docstring: "a 1984 native has no lived
experience of a chapter that 'began' in 1950"). Also computes `dominant_signal_class` per MD span
via a frequency count of `signature_class` across convergence windows. Classical technique:
Vimśottarī MD/AD/PD chaptering with birth-instant clipping — a genuinely careful, non-trivial
correctness fix (T-9 clip) already implemented, not merely aspirational.

**2. OUTPUT.** Target table `kala_jivana_parva`, grain chart × level/index. Canonical chart row
count **100** (census, single build 2026-08-13). `asset_throughput` (Lane D direct check): state
**`stale`**, `rows_written=100` — **matches** the census count exactly, no claimed-vs-actual
mismatch (this table is not in the CASCADE-vulnerable set per `DATA_LOSS_DIAGNOSIS.md`'s named
list).

**3. INPUTS.** `depends_on`: `{ka_kala_darshana, ka_dasha_kala, ka_sangam, ka_yojaka, ga_dashas}`.
Note `ka_kala_darshana` and `ka_sangam` are declared separately even though `ka_kala_darshana`
itself composes `ka_sangam` — the same triple-count-risk shape flagged for `ka_bhavishya_lekha`
above (STRAT Tension 6: "chapter-level narrative agreement across these is agreement with
`ka_sangam`, restated").

**4. CONSUMERS.** LIVE, registered: `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts`
+ `platform-mcp/src/tools/kala_views/story.ts`, confirmed reachable via
`register_p1_synthesis.ts:726-764` → `kala_life_arc_get` (traceability matrix, medium-high
confidence). Lane D direct check confirms `kala_jivana_parva` referenced in
`platform-mcp/src/tools/register_p1_synthesis.ts`, `kala_views/register_all.ts`,
`kala_views/ahead.ts`, `kala_views/story.ts`, and `query_life_arc.ts` — the best-attested consumer
surface of any asset in this register.

**5. DEFECTS.**
- `writers/ka_jivana_parva.py:124` — `LIMIT 1` inside a LATERAL join resolving each window's
  activation predicate, ordered only by the join's implicit row order (comment at line ~113: "join
  via signal_id (LATERAL LIMIT 1..."), not by any declared tie-break column — this is the
  "unordered `LIMIT 1`" defect the register names (STRAT:290): "replace unordered predicate `LIMIT
  1` selection with a qualified relation." Confirmed present at this line; no `ORDER BY` inside the
  LATERAL subquery was found before the `LIMIT 1`.
- Triple-count risk via `ka_kala_darshana`/`ka_sangam` co-declaration (above).

**6. BUILD REALITY.** Buildable; reads no F4-flagged inaccessible table directly (relies on
upstream writers for the harder reads). Cost driver: bounded per-chart (~100–247 rows per the
module's own O6 comment about PD-level row-count management to avoid smallint overflow).

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q8** (truncation-policy ruling) names `jivana_parva`
directly, and the unordered `LIMIT 1` is exactly the kind of undisclosed-selection defect Q8 asks
the native to rule on portfolio-wide rather than fix seven times independently. The underlying
chaptering/clipping logic itself is comparatively mature (T-9 clip is a real, reasoned fix already
shipped) — the gate here is the selection-policy ruling, not a rewrite.

---

## 6. `ka_kala_darshana`

**1. WHAT IT COMPUTES.** A presentation/join layer: reads `kala_convergence` (ordered by
`convergence_score DESC NULLS LAST`, `LIMIT 750`) and `kala_obstruction`, and produces one row per
convergence × obstruction-summary pairing — an "effective score" join, not an independent
computation (`writers/ka_kala_darshana.py:1-45`, `@register('ka_kala_darshana')` at line 9). The
strategy doc's own correction is worth repeating verbatim: "current computation reads
convergence/obstruction, not `kala_activation` as the registry claims" (STRAT:289) — i.e. even the
registry's own `count_sql`/target-table story about what feeds this asset has drifted from what the
code actually reads.

**2. OUTPUT.** Target table `kala_darshana`, grain chart × convergence × signal × window.
Canonical chart row count **0** (census — globally non-empty, 750 rows, all owned by chart
`1c826d5a-…`). `asset_throughput` (Lane D direct check): state **`stale`**, `rows_written=750`.
**CONFIRMED MISMATCH** — same CASCADE pattern as `ka_bhavishya_lekha`: this is one of the tables
`DATA_LOSS_DIAGNOSIS.md` names as CASCADE-exposed via `kala_darshana`'s dependency chain on
`kala_convergence`'s own signal_id references, and directly downstream of `ka_sangam`'s own
canonical-chart emptiness (§Cross-cutting below).

**3. INPUTS.** `depends_on`: `{ka_sangam, ka_vighnakara, ka_kalasutra}`. Idempotency confirmed
present and correct: `writers/ka_kala_darshana.py` deletes-then-inserts scoped to `chart_id` before
reading (delete at line ~17, matching §N.3).

**4. CONSUMERS.** LIVE, confirmed not dark: `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts`
(medium confidence per traceability matrix), reachable via `kala_temporal.ts`. This is the
genuinely-live half of the disputed "KA-3-1 kala.timeline" asset-id pairing (`ka_avadhi` is the
other live half; a third file, `kala_timeline.ts`, claims the same conceptual asset id but is
confirmed **DARK on three axes** — never registered on the MCP server, not whitelisted on the
primitives route, no writer targets `kala_timeline` — per
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` Domain F).

**5. DEFECTS.**
- `writers/ka_kala_darshana.py:31` — `LIMIT 750` on the `kala_convergence` read, confirmed live,
  unqualified, with a stated live effect on every served row ("`ka_sangam`'s top-750 intake is 100%
  Mode C, so every served row carried the wrong..." — comment at line ~197).
- `writers/ka_kala_darshana.py:78-96` — the NULL→0.5 default on missing convergence score is
  **already fixed and annotated**: the code comment at lines 78-82 explicitly documents this was
  "`conv_score or 0.5`... a middling substitution... never fired as of L3-W3," and line 96 shows
  the retained literal `0.5` is now a *reached, understood* fallback rather than a silent trap —
  this is the one defect in this register that has already moved from "silent" to "disclosed," per
  §N.7. The top-750 cap remains live and unqualified.

**6. BUILD REALITY.** Buildable in isolation, but **structurally starved today**: its sole real
input, `kala_convergence`, is 0 rows for the canonical chart (§Cross-cutting), so a rebuild right
now would legitimately produce 0 rows for `kala_darshana` too, honestly reflecting empty upstream
data rather than a bug in this writer.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q8** names `darshana` directly for the
truncation-policy ruling. Layered on top of Q8 is the fact this asset cannot even be meaningfully
rebuilt today without `ka_sangam` (out of this lane's scope) first regaining canonical-chart data —
a cross-lane sequencing dependency, not merely an in-lane code fix.

---

## 7. `ka_kalasutra`

**1. WHAT IT COMPUTES.** Resolves each activation predicate's date window against the L1
Vimśottarī daśā timeline via the shared `services.ka_temporal` helper: when a `kala_convergence`
peak date exists it refines the window (legacy path); when it doesn't (the docstring states this is
"the ~99% NULL-date case"), the matched daśā period supplies real L1-sourced start/end/peak dates —
explicitly no fabricated dates (`writers/ka_kalasutra.py:1-11`, citing §N.5/B.10 directly in its own
header). This is an interval-resolution/recurrence kernel over daśā-plus-convergence evidence, not
a standalone classical calculation.

**2. OUTPUT.** Target table `kala_activation`, grain chart × signal × ayanamsha × period. Canonical
chart row count **0** (census — table globally non-empty, 337,148 rows, 100% owned by other
charts). `asset_throughput` (Lane D direct check): state **`stale`**, `rows_written=335403`,
`last_built_at=2026-08-13`. **CONFIRMED MISMATCH**, the largest by row-count magnitude in this
register — this is the writer the `DATA_LOSS_DIAGNOSIS.md` CASCADE root-cause analysis names first
by example: `kala_activation.signal_id` has `ON DELETE CASCADE` to `bodha_msr_signals.signal_id`
(migration `403_kala_signal_fk_cascade.sql`), and `bo_laksana`'s 2026-09-08/2026-09-11 regenerations
happened after this writer's 2026-08-13 run with 100% signal-set turnover in between — proven on a
second chart via a decisive join (100% of surviving rows resolve to the pre-rebuild MSR generation,
0% to post-rebuild, per F7).

**3. INPUTS.** `depends_on`: `{ka_yojaka, ka_sangam, bo_laksana}`. **Undeclared read found (Lane D
direct check):** `writers/ka_kalasutra.py:16-19` imports `load_dasha_timeline`,
`resolve_activation_windows`, `resolve_birth_date` from `services.ka_temporal`, which reads L1
`chart_dashas` per its own docstring ("L1 Vimśottarī daśā timeline") — but no `ga_dashas`-equivalent
L1 dependency appears in `ka_kalasutra`'s declared `depends_on` set. Same class of finding as
`ka_avadhi`'s undeclared `ka_dasha_kala` import (§1 above), independently found here rather than
carried from the audit.

**4. CONSUMERS.** U04 names Kalasutra explicitly, rated Y (traceability matrix). Live reads
confirmed at `query_temporal_activation.ts`, `kala_views/ahead.ts`, `now.ts` (high confidence, own
declared table + a documented L2 join). Separately, **`ka_tulana`'s consumer wrapper reads this
table** (`kala_activation`) instead of any table traceable to `ka_tulana`'s own writer (§13 below) —
worth noting here because it means `ka_kalasutra`'s table is serving double duty as a stand-in for
a different asset's advertised capability.

**5. DEFECTS.**
- Default-eight truncation and implicit "today" (STRAT:286, elevation-plan Tier A entry) — **not
  independently re-located at a specific line within Lane D's budget** (the module's own top-level
  logic delegates window resolution to `services.ka_temporal`, and the `[:8]`/day-count default was
  not found by direct grep of `writers/ka_kalasutra.py` itself — COULD NOT VERIFY the exact file:line;
  most likely lives inside `services/ka_temporal/`'s `resolve_activation_windows`, not inspected
  within budget).
- Redundant payload duplication named in the register (STRAT:286) — not independently verified.

**6. BUILD REALITY.** Buildable; reads L1 `chart_dashas` (no F4 privilege issue) plus
`kala_convergence` (empty for canonical chart today — degrades but does not block the ~99%
NULL-date fallback path, per the writer's own design). Fan-out driven by predicate count
(50,678 from `ka_yojaka`), a meaningful but not extreme cost driver.

**7. ELEVATION TIER: HEAVY.** Doubly gated: elevation-plan **Q7** ("nearest vs strongest — by which
criterion, for your actual use?") names `kalasutra` alongside `tulana`/`muhurta_seva` as a shared
open ranking-semantics question, and **Q8** (truncation policy) also names `kalasutra` directly for
its default-eight cap. Two separate open native decisions converge on one asset.

---

## 8. `ka_kota_chakra`

**1. WHAT IT COMPUTES.** "Ring/run" fort-chart (Koṭa Cakra) geometry: for each chart × ayanamsha ×
graha × transit interval, computes ring membership/severity/root against a versioned ring-partition
reference table (`bg_kota_chakra_rings`, "moved off an inline writer-code dict onto this versioned
L0 asset" — `writers/ka_kota_chakra.py:1-22`). LIGHT writer, all logic in
`services/ka_kota_chakra/{logic,writer}.py`. Classical technique: Koṭa Cakra ring/fort assignment
per transiting graha.

**2. OUTPUT.** Target table `kala_kota_chakra`, grain chart × ayanamsha × graha × interval start.
Canonical chart row count **585** (census, single build 2026-09-07). `asset_throughput` (Lane D
direct check): state **`lit`**, `rows_written=585` — **matches exactly**, no mismatch.

**3. INPUTS.** `depends_on`: `{ga_positions, bg_ephemeris, bg_kota_chakra_rings}`.

**4. CONSUMERS.** LIVE, exact table match: `platform/src/lib/retrieval/registry/layers/L3_kala/query_kota_chakra.ts`
+ `platform-mcp/src/tools/kala_views/now.ts` (Lane D direct check confirms both reference
`kala_kota_chakra`) — **but this is in direct tension with the strategy document itself**, which
states "current v3 implementation does not consume it: qualify and prove any proposed integration"
(STRAT:277). Two different, both independently-sourced claims about whether the century-materializer
v3 pipeline treats this as a real input — not reconciled by any prior packet, not reconciled here
either (flagged, not resolved).

**5. DEFECTS.** None found at the code level within Lane D's search — REGISTER:138's own framing is
about **usage scope**, not a coding defect: "not an independent adverse vote by default," i.e. a
ring hit here should not, on its own, be read as an independent confirming signal alongside other
witnesses that share the same underlying geometry.

**6. BUILD REALITY.** Buildable; no F4-flagged table in its dependency set. Small, bounded row
count (585), cheap.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q2** names `ka_kota_chakra` explicitly as one of
"three assets consumed by nothing today... wire them into a qualified operator, or retire with
evidenced disposition?" — a portfolio-level native call. The now.ts/query_kota_chakra.ts consumer
found by this lane and by F5 is real, but Q2 was written with full knowledge of that same consumer
surface and still frames the question as open (the STRAT-vs-consumer contradiction above is
precisely why) — the correct near-term action (wire in vs. retire) is a decision, not a repair.

---

## 9. `ka_moorti_nirnaya`

**1. WHAT IT COMPUTES.** "Run detection" — per ingress (graha entering a new sign/nakshatra
region), classifies the transiting graha's Mūrti-nirṇaya quality using a rolling −60/+400-day,
day-grade Lahiri-referenced coverage window against `bg_transit_moorti`
(`writers/ka_moorti_nirnaya.py:1-23`; logic in `services/ka_moorti_nirnaya/{logic,writer}.py`).
Classical technique: Mūrti-nirṇaya (planetary "form/posture" classification per ingress).

**2. OUTPUT.** Target table `kala_moorti_nirnaya`, grain chart × ayanamsha × graha × interval
start. Canonical chart row count **71** (census, single build 2026-09-07). `asset_throughput`
(Lane D direct check): state **`lit`**, `rows_written=71` — **matches exactly**.

**3. INPUTS.** `depends_on`: `{ga_positions, bg_ephemeris, bg_transit_rules}`.

**4. CONSUMERS.** LIVE, exact table match, STRAT-confirmed as **actual v3 input** (the strongest
current-integration statement of any Frontier asset — STRAT:276 explicitly says so, unlike the
tension found for `ka_kota_chakra`/`ka_sudarshana_varsha`/`ka_tithi_pravesha`):
`query_moorti_nirnaya.ts` + `kala_views/now.ts` (Lane D direct check confirms both).

**5. DEFECTS.** None found in the writer's own logic. The real, documented issue is **environmental,
not a code defect in this writer**: `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F4 confirms
`_fetch_moorti_table`, called unconditionally from `run()`, reads `bg_transit_moorti` with **no
try/except anywhere** — and `data_plane_builder` currently has no `SELECT` grant on that table. F4
labels this "CONFIRMED HARD FAIL," a LIGHT writer with no substep boundary to isolate the failure.

**6. BUILD REALITY.** **The strongest asset in this register on data/consumer confirmation, but
currently one grant away from being un-buildable.** The last successful build (2026-09-07,
`state='lit'`, matching row count) evidently predates whatever removed `data_plane_builder`'s
`SELECT` on `bg_transit_moorti` — F6 traces a related privilege regression to a "2026-09-18
ownership cutover." A rebuild attempted today, unpatched, would hard-fail per F4 with no exception
boundary to contain it. Cost driver: small, bounded (71 rows), no ephemeris-heavy fan-out beyond
what `bg_ephemeris`/`ga_positions` already supply.

**7. ELEVATION TIER: LIGHT.** No open elevation-plan Q names this asset. The computation is
correct, the consumer is live and STRAT-confirmed as the genuine production input, and the
canonical-chart data is present and matches its own claimed count. The one blocker — F4's grant gap
— is an environment/privilege fix (grant `SELECT` on `bg_transit_moorti` to `data_plane_builder`,
plus adding a try/except boundary so a future gap degrades rather than hard-fails) applied *to the
environment*, not a design decision or a rewrite of this asset's own logic.

---

## 10. `ka_muhurta_seva`

**1. WHAT IT COMPUTES.** Panchāṅga/election (muhūrta) scoring and window search. All computation
lives in `services/ka_muhurta_seva/service.py` (public `score`/`find_windows` API); the registered
writer (`writers/ka_muhurta_seva.py`) is a thin self-test + health-write shim, same self-test-only
pattern as `ka_dasha_kala`/`ka_graha_sancara`
(`writers/ka_muhurta_seva.py:1-22`). Classical technique: Pañcāṅga-based muhūrta suitability
scoring.

**2. OUTPUT.** `storage_type=service`, no target table, `count_sql` empty. No materialized rows by
design — no claimed-vs-actual question arises.

**3. INPUTS.** `depends_on`: `{}` (empty set, live registry). **Confirmed deliberate, not an
oversight** (`KALA_DAG_RECONCILIATION_v1_0.md` §2): migration
`676_nirmana_l3_n5_muhurta_seva_depends_on.sql` corrected LIVE to zero dependencies after verifying
the writer touches no producer table, and the migration's own text states SEED-TS (which still
shows 1 dependency) is deliberately left un-synced as "the seed file is the as-originally-authored
record." A real, documented, permanent SEED-TS/LIVE divergence, invisible to `dag_edge_guard.py`.

**4. CONSUMERS.** LIVE, medium confidence: `call_muhurta_score` and `muhurta_finder.ts` reuse
`score_muhurat()` per an in-file comment (the traceability matrix notes the primitive source itself
was not independently re-confirmed beyond that comment).

**5. DEFECTS.** No proving-journey citation exists for this asset despite being the direct answer
to elevation-plan's P11 (traceability matrix, Frontier orphan obligation #2) — a coverage gap in
the product-obligation documentation, not a code defect.

**6. BUILD REALITY.** Trivially buildable (self-test only, no fan-out, no materialization).

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q7** ("nearest vs strongest — by which criterion,
for your actual use?") names `muhurta_seva` directly alongside `tulana`/`kalasutra` — this asset's
own `score`/`find_windows` ranking semantics are exactly what Q7 asks the native to rule on before
any further "which window is best" work is meaningful.

---

## 11. `ka_sudarshana_varsha`

**1. WHAT IT COMPUTES.** Annual three-reference-frame progression (Sudarśana Cakra year-wheel):
for each chart × ayanamsha × year, computes a return/progression result across three lagna
reference frames (`writers/ka_sudarshana_varsha.py:1-27` — explicitly distinguished in its own
header from the unrelated, static `bo_sudarshana` L2 asset: "a confirmed namesake-only collision,
different layer, different (static, non-temporal) computation... BINDING NAMING RULING (do not
revisit)"). LIGHT writer, 120 rows/chart, "pure arithmetic" per its own docstring. Classical
technique: Sudarśana Cakra triple-lagna annual progression.

**2. OUTPUT.** Target table `kala_sudarshana_varsha`, grain chart × ayanamsha × year. Canonical
chart row count **120** (census, single build 2026-09-07). `asset_throughput` (Lane D direct
check): state **`lit`**, `rows_written=120` — **matches exactly**.

**3. INPUTS.** `depends_on`: `{ga_positions}`.

**4. CONSUMERS.** LIVE, medium-high confidence table match: `query_sudarshana_varsha.ts` +
`kala_views/now.ts` (Lane D direct check confirms both) — **but STRAT explicitly states the live
v3 pipeline does not read it** ("current v3 does not read it; integration requires a qualified
operator, not a dependency label" — STRAT:280), the same tension pattern as `ka_kota_chakra`.

**5. DEFECTS.** None found at the code level. The disposition register's framing (REGISTER:141) is
scope-preservation, not a bug: "preserve actual annual scope; not static `bo_sudarshana` duplication
or proof of full sub-daśā."

**6. BUILD REALITY.** Buildable; no F4-flagged table; small bounded row count, cheap, pure
arithmetic per its own docstring (no ephemeris root-finding needed beyond natal positions already
in `ga_positions`).

**7. ELEVATION TIER: HEAVY.** Doubly named: elevation-plan **Q2** (consumed-by-nothing-today
triad) and **Q3** ("what counts as an independent witness? Sangam currently treats shared natal
roots as independent; Sudarshana's three frames share roots too") both name this asset directly.
Q3 in particular is a genuine epistemics question the audit itself flags as determining "whether
convergence strength means anything" — not resolvable by code changes alone.

---

## 12. `ka_taranga`

**1. WHAT IT COMPUTES.** Monthly (1950–2100) convolution of three 0–1 components per chart ×
month × scope (domain + event_class): `dasha_contribution` (fraction of the month's daśā lord(s)
activating the scope), `transit_contribution` (mean `kala_convergence.convergence_score` for
overlapping windows), and `promise_contribution` (`bodha_pratijna` grade/10) — combined via
harmonic mean when all three are positive, else an arithmetic mean of the available components
(`writers/ka_taranga.py:1-27`). Coarse multiresolution trend projection, not a classical technique
per se — a synthesis waveform.

**2. OUTPUT.** Target table `kala_taranga`, grain chart × month × scope kind/ID. Canonical chart
row count **92,412** (census, single build 2026-08-13). `asset_throughput` (Lane D direct check):
state **`stale`**, `rows_written=92412` — **matches exactly**; this table is not in the
CASCADE-vulnerable set (it reads `kala_convergence` live at build time rather than storing a
foreign-keyed `signal_id`, per the writer's own SQL at `writers/ka_taranga.py:111`), so its count
survived the `bo_laksana` regeneration that wiped `ka_kalasutra`/`ka_sangam`/`ka_kala_darshana`.
One of only two Spine-tier assets (with `ka_jivana_parva`) both wired *and* genuinely populated for
the canonical chart, per the traceability matrix.

**3. INPUTS.** `depends_on`: `{ka_avadhi, bo_pratijna, ka_sangam, ga_dashas, bg_ghatana}`. **Declared
but reportedly unused edge**: STRAT:288 states "the declared Avadhi dependency is **not read**
today" — the inverse of an undeclared-read defect (declared-but-absent), not independently
re-verified against the writer's own SQL within Lane D's budget beyond the STRAT citation (COULD
NOT VERIFY directly — `ka_avadhi` did not appear in the grep excerpt taken from
`writers/ka_taranga.py`, consistent with, but not conclusive proof of, the claim).

**4. CONSUMERS.** LIVE, medium confidence: `query_activation_waveform.ts` (Lane D direct check
confirms the reference to `kala_taranga`).

**5. DEFECTS.** `writers/ka_taranga.py:106-130` — `transit_contribution` averages
`kala_convergence` (itself an `ka_sangam` output that is L2-Bodha-enriched) with
`promise_contribution` from `bodha_pratijna` (the *same* L2 Bodha substrate) — the traceability
matrix's Tension 6: "the average reads as corroboration between two views of one source," exactly
the DP08/10 defect the disposition register already names for this asset (double-counting a single
underlying signal as if it were two independent witnesses).

**6. BUILD REALITY.** Buildable; reads `kala_convergence` live (currently 0 rows for canonical
chart — a rebuild today would silently zero out `transit_contribution` for every month/scope,
degrading to the arithmetic-mean-of-available-components fallback rather than failing outright,
per the writer's own stated formula). Cost driver: 1950–2100 monthly grid × scope count — the
largest row count of any in-scope asset (92,412), driven by time-grid density, not ephemeris calls.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q6** ("is monthly resolution over 1950–2100 the
right Taranga contract, and what should class-specific meaning be when it currently degenerates to
domain maxima?") names `taranga` directly and frames it as "scope and semantics, not
implementation" — exactly the kind of question that gates a design decision rather than a bug fix,
compounded by the real double-counting defect found independently above.

---

## 13. `ka_tithi_pravesha`

**1. WHAT IT COMPUTES.** Lunar-return annual chart (Tithi Praveśa): for each chart × ayanamsha ×
year, numerically roots-finds the Moon-longitude return instant and casts an annual chart at that
moment — "real ephemeris root-find + annual-chart cast per row, benchmarked ~3.4ms/row"
(`writers/ka_tithi_pravesha.py:1-23`; logic in `services/ka_tithi_pravesha/{logic,writer}.py`).
Classical technique: Tithi Praveśa (lunar-return progression), one of the more numerically
substantive per-row computations in this register.

**2. OUTPUT.** Target table `kala_tithi_pravesha`, grain chart × ayanamsha × year. Canonical chart
row count **120** (census, single build 2026-09-07). `asset_throughput` (Lane D direct check):
state **`lit`**, `rows_written=120` — **matches exactly**.

**3. INPUTS.** `depends_on`: `{ga_positions}`.

**4. CONSUMERS.** **The sharpest source-tension in this register.** Lane D direct check confirms a
LIVE, exact-table-match consumer: `query_tithi_pravesha.ts` + `kala_views/now.ts`, both referencing
`kala_tithi_pravesha` directly — yet elevation-plan **Q2** groups this exact asset among "three
assets consumed by nothing today." F5 (consumed, high confidence) and the elevation plan (not
consumed) directly disagree; not resolved by this lane either — flagged, not adjudicated, per the
audit's own prior treatment.

**5. DEFECTS.** Register-named method-adjudication question (REGISTER:142): "named method/equation
needs source adjudication; current Moon-longitude return is not accepted merely from name" — i.e.
whether the implemented numerical method matches the classically-admitted definition of Tithi
Praveśa has not been independently confirmed. No code-level truncation/NULL-default defect found.

**6. BUILD REALITY.** Buildable; no F4-flagged table; moderate per-row cost (numerical root-find,
~3.4ms/row per the writer's own header) but bounded to ~120 rows/chart — cheap in aggregate.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q2** names this asset directly for the
wire-in-or-retire portfolio decision, and the F5-vs-elevation-plan consumer dispute means even the
prerequisite fact ("is this asset served today, yes or no") is not settled — a native ruling is
needed before "elevate" vs. "retire" can even be scoped, let alone executed.

---

## 14. `ka_tulana`

**1. WHAT IT COMPUTES.** A stateless cross-pattern comparison/prioritization service: given a set
of `WindowInput`s, ranks/compares them (nearest vs. strongest framing). The registered writer
(`writers/ka_tulana.py`) returns `WriterResult(rows_inserted=0)` — no data rows by design; all
logic lives in `services/ka_tulana/writer.py` (`writers/ka_tulana.py:1-19`). Not a classical
technique — a generic ranking/comparison kernel applied to other assets' outputs.

**2. OUTPUT.** `storage_type=service`, no target table. `asset_throughput` (Lane D direct check):
state **`stale`**, `rows_written=0` — consistent with a service asset, no mismatch on the writer's
own claim (0 rows is what it declares).

**3. INPUTS.** `depends_on`: `{ka_sangam, ka_vighnakara, ka_kala_darshana}`.

**4. CONSUMERS.** **NOT-FOUND — confirmed real gap**
(`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` F5, `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`
Spine #9). The consumer wrapper's SQL selects from `kala_activation` — a table `ka_kalasutra`
owns, not any table traceable to `ka_tulana`'s own writer; `grep target_table|INSERT INTO` on
`services/ka_tulana/writer.py` found zero hits, and no `kala_tulana` table exists anywhere in the
37-table census. U04 rates this "Y (tool exists)" but explicitly flags "the 'Tulana' half of this
U-item has an open §N.8-flagged gap even though the tool itself is callable" — genuinely unresolved
whether this is an intentional shared-table design (comparison service legitimately reads a
neighbor's stored data rather than owning its own) or a silent substitution.

**5. DEFECTS.** The consumer-table substitution itself is the primary defect/open question — see
Consumers above. No other code-level defect found (self-test/service pattern, no materialization to
audit for truncation/NULL-default issues).

**6. BUILD REALITY.** Trivially buildable (pure comparison service, `rows_inserted=0` by design).
No fan-out cost of its own; cost is entirely in whatever `WindowInput`s a caller supplies.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q7** ("nearest vs strongest") names `tulana`
directly as the asset whose product framing is most exposed by the open ranking-criterion question,
compounded by the unresolved consumer-substitution gap — "present" for this asset's own output is,
per the traceability matrix, "ambiguous by design vs. defect, not merely unverified," which is
itself a design question this lane cannot close by code inspection alone.

---

## 15. `ka_vighnakara`

**1. WHAT IT COMPUTES.** Explicit counter-indicator (obstruction) detection across five independent
detector types, all backed by live ephemeris/panchāṅga calls rather than proxies (module docstring,
`writers/ka_vighnakara.py:1-18`, "D5... replaced all proxy detectors with live ephemeris and real
panchāṅga calls"): (1) `malefic_transit` — Saturn/Rahu adversarial to natal lagna/moon via swisseph
at peak_date; (2) `panchanga_obstruction` — Rikta tithi (4/9/14) from `ka_muhurta_seva`'s real
tithi computation; (3) `gandanta` — Moon in the last 3°20′ of a water sign at peak_date; (4)
`papakartari` — lagna hemmed between malefics in adjacent signs; (5) `combustion` — any planet
within 6° of the Sun. Classical technique: a composite of five named obstruction/counter-indicator
rules, not a single named yoga.

**2. OUTPUT.** Target table `kala_obstruction`, grain chart × signal (optional convergence) ×
kind/severity/override/roots. Canonical chart row count **0** (census — globally non-empty, 747
rows across 2 other charts). `asset_throughput` (Lane D direct check): state **`stale`**,
`rows_written=536`. **CONFIRMED MISMATCH** — `kala_obstruction` is named in
`DATA_LOSS_DIAGNOSIS.md`'s CASCADE-exposed table list; this is the same wipeout pattern as
`ka_kalasutra`/`ka_sangam`/`ka_kala_darshana`/`ka_bhavishya_lekha`. Independently, this asset is one
of only 3 (with `ka_kalasutra` and an entity recorded as `ka_gochara_v`) that the audit found have
**zero campaign evidence in any generation, ever** (F2).

**3. INPUTS.** `depends_on`: `{ka_sangam, ka_muhurta_seva, ga_positions, bg_dignity_reference,
ka_yojaka}`. **Two undeclared reads found (Lane D direct check):**
`writers/ka_vighnakara.py:24` imports `serialized_swiss_state` from `panchang_engine.swiss_state` —
a direct ephemeris read with no `bg_ephemeris` entry in `depends_on`; and
`writers/ka_vighnakara.py:29` imports `load_dasha_timeline` (and siblings) from `services.ka_temporal`
— the same L1 `chart_dashas` read pattern already flagged undeclared for `ka_avadhi`/`ka_kalasutra`
above, again with no `ga_dashas`-equivalent entry declared here.

**4. CONSUMERS.** U03 names Vighnakara explicitly, rated **Y**. LIVE, high confidence, direct read:
`query_obstruction_periods.ts` (Lane D direct check confirms `FROM kala_obstruction`-style
reference).

**5. DEFECTS.**
- `writers/ka_vighnakara.py:182` — `LIMIT 500` (top-500 coverage cap), confirmed present.
- Null-convergence association and deterministic-tie handling named in the disposition register
  (STRAT:287) — not independently re-located at a specific line beyond the citation.
- Structural independence defect (T5 Tension 5, traceability matrix): `ka_kala_darshana`'s net
  score composes `ka_sangam` with `ka_vighnakara`, but `ka_vighnakara` itself reads `ka_sangam` —
  "so convergence × obstruction is not two independent readings; both legs descend from
  `ka_sangam`" — a real epistemic double-count, distinct from the two undeclared-read findings
  above.
- Two undeclared `depends_on` reads (bg_ephemeris, L1 chart_dashas via ka_temporal) — see Inputs.

**6. BUILD REALITY.** Buildable; none of its reads hit an F4-flagged inaccessible table. Cost
driver: real swisseph calls per candidate peak_date across five detector types — the most
ephemeris-call-heavy asset in this register by detector count, though still per-chart bounded (not
century-wide). Currently structurally degraded if rebuilt today: `ka_sangam`'s own
`kala_convergence` is 0 rows for the canonical chart, so the "optional convergence" association leg
of this detector would find nothing to associate against, even though the other four detector types
are independent of `kala_convergence` and would still fire normally.

**7. ELEVATION TIER: HEAVY.** Elevation-plan **Q8** (truncation-policy ruling) names `vighnakara`
directly for its top-500 cap, and this asset carries the most defect volume of any in this
register (one live truncation cap, two undeclared cross-layer reads, and a confirmed structural
double-count via `ka_sangam`) layered on top of the CASCADE data-loss pattern — the combination of
an open portfolio-policy question and a genuinely elevated defect count puts this solidly in HEAVY
rather than MODERATE.

---

## 16. `ka_yojaka`

**1. WHAT IT COMPUTES.** The activation-predicate "bridge": for each L2 MSR signal, compiles a
typed activation predicate (eligibility/trigger/strength payload) and resolves the *actual* forming
graha(s) that should date it, sourced from authoritative L1 tables rather than the ratified
binder's own (broken) constituent-lord extraction — for YOGA signals via
`ga_yoga_firings.constituent_planets` keyed by `yoga_canonical_id`, for DOSHA signals via the
graha_position facts of the fired dosha (`writers/ka_yojaka.py:1-30`). A Nabhasa/ākṛti
"distribution" yoga with no single activating lord is honestly left `UNDATED` with an inspectable
`always_on_reason`, per the writer's own §N.6-citing comment — a genuinely careful anti-fabrication
design (every emitted lord traces to a real L1 row, per §N.5). Also enriches predicates with a
`cgm_centrality_weight` from `bodha_cgm_nodes`/`bodha_cdlm_cells`.

**2. OUTPUT.** Target table `kala_activation_predicates`, grain chart × ayanamsha × signal ×
predicate signature. Canonical chart row count **50,678** (census, single build 2026-09-10 17:17,
"a single `bound_at` instant, batch write"). `asset_throughput` (Lane D direct check): state
**`stale`**, `rows_written=50678` — **matches exactly**, the largest populated table of any
in-scope asset and, notably, **not** wiped by the `bo_laksana` CASCADE that hit
`ka_kalasutra`/`ka_sangam`/`ka_kala_darshana`/`ka_vighnakara`/`ka_bhavishya_lekha` — because this
writer's own `bound_at` (2026-09-10 17:17) is *after* `bo_laksana_rerank`'s 2026-09-11 regeneration
window closed relative to its own last run... more precisely, its 50,678 rows are the
freshly-regenerated set itself, not survivors of an earlier one. A small residual mismatch remains:
**79 of 50,678 (0.156%) rows have a `signal_id` that does not resolve against
`bodha_msr_signals`** for the same chart (F7, independently re-confirmed via anti-join by the
audit) — a genuine, small, unresolved-reference population, not a full wipeout but not zero either.

**3. INPUTS.** `depends_on`: `{bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati,
bo_pratijna, bg_ghatana}` — the widest declared dependency set of any asset in this register (7
edges), consistent with its role as "mechanism compiler."

**4. CONSUMERS.** U01 names Yojaka explicitly: "served via `kala_views/{ahead,priority,ritual,
story}.ts` per F5." **But F5 itself rates both candidate consumers
(`query_temporal_activation.ts` and the `kala_views` family) low-medium confidence** — neither
trace confirms the consumer actually reads `kala_activation_predicates` (this writer's own table)
rather than a neighboring table, the same unresolved-consumer-table class as `ka_tulana`/
`ka_dasha_kala`, just not yet promoted to a CONFIRMED gap.

**5. DEFECTS.**
- 79/50,678 unresolved `signal_id` references against `bodha_msr_signals` (F7, confirmed via
  anti-join — a real, small, nonzero population).
- One-domain/five-link "flattening" defect named in the disposition register (REGISTER:147,
  `writers/ka_yojaka.py:479-510` per the traceability matrix's citation) — Lane D read
  `writers/ka_yojaka.py:479-510` directly and found SAVEPOINT-guarded house-lord/fact-subject
  lookup helpers there, not an obviously flattening code path; **COULD NOT VERIFY** the exact
  flattening logic at that specific citation within this lane's budget — the defect is
  well-attested in the disposition register's own text but the precise line range may have shifted
  since REGISTER:147 was written, or the flattening lives in a different function than the one at
  that line range today.
- Low-medium-confidence consumer-table binding (see Consumers).

**6. BUILD REALITY.** Buildable; none of its 7 dependencies is F4-flagged. Cost driver: fan-out
over every MSR signal for the chart (50,678 signals) × predicate compilation — the widest fan-out of
any asset in this register by input-signal count, though the build evidently completes (fresh
2026-09-10 batch write).

**7. ELEVATION TIER: MODERATE.** No elevation-plan Q1–Q8 item names `ka_yojaka` directly — its
required work (REGISTER:147, STRAT:281) is substantial semantic repair (resolve the 79 unmatched
refs, confirm/complete the consumer binding, verify the flattening claim against current code) but
is not gated on an open native design question the way the Q-tagged assets above are. Graded
MODERATE rather than LIGHT because of the nonzero unresolved-MSR-reference defect and the
low-medium-confidence consumer binding, both of which are real, named gaps requiring investigation
before this asset could honestly be called "essentially correct."

---

# CROSS-CUTTING SECTION 1 — DEAD-OR-DARK

**Search boundary stated up front, per the evidence-discipline instructions:** "no consumer found"
below means no reference was found by `grep -rl <target_table>` across
`platform-mcp/src/tools/`, `platform/src/lib/retrieval/`, and the sidecar's own `routers/`/
`services/` directories, within this lane's read budget. This is a search-scope finding, not proof
of disuse — every item below is marked accordingly.

1. **`ka_dasha_kala` (§3) and `ka_tulana` (§14) — unresolved use, not confirmed dead.** Both have a
   registered, self-consistent capability (a real service class with real methods) and a
   *confirmed-negative* finding for their advertised production consumer: `ka_dasha_kala`'s
   `KaDashaKalaService` traversal API is called only by its own self-test; `ka_tulana`'s consumer
   wrapper demonstrably reads a *different* asset's table (`kala_activation`, owned by
   `ka_kalasutra`) instead of anything traceable to `ka_tulana`. Neither is "no caller found" in the
   weaker sense (grep silence) — both are "a caller was found, and it reads something else" — a
   stronger and more actionable finding than ordinary dark-code suspicion. Marked **unresolved use**
   because it remains possible `ka_tulana`'s neighbor-table read is an intentional, undocumented
   shared-storage design rather than a substitution bug.
2. **`ka_kota_chakra` and `ka_sudarshana_varsha` (§8, §11) — contested, not dark.** Both have a
   real, exact-table-match consumer confirmed live by this lane and by F5, yet the strategy
   document independently states the production v3 (century-materializer) pipeline does not read
   either. This is neither "dead" nor "clearly alive" — it is two different production surfaces
   disagreeing about which of them is the intended integration. Marked **unresolved use**, not
   redundancy.
3. **`ka_tithi_pravesha` (§13) — the one item in this section closest to a genuine open
   contradiction rather than a search-boundary gap.** F5 and this lane both found a live,
   exact-table-match consumer; the elevation plan's own Q2 asserts this asset is "consumed by
   nothing today." Both cannot be fully correct as stated; not adjudicated here.
4. **No asset in this lane's 16-item scope was found to be unambiguously dead** (i.e., zero
   consumer reference of any kind, confirmed by a positive statement that no caller exists rather
   than by grep silence alone). The closest candidates (`ka_dasha_kala`, `ka_tulana`) both have a
   confirmed-but-misdirected consumer, which is evidence of a wiring gap, not of disuse. `ka_avadhi`
   and `ka_kala_darshana` (§1, §6) both have live, working consumers (`kala_temporal.ts`'s two
   halves) that no numbered `U`-interface item claims — an obligation-list coverage gap, not a
   dead-asset finding, and explicitly not "unused" per the instructions' own caution.

---

# CROSS-CUTTING SECTION 2 — CLUSTERS

Assets sharing a hub module, target table, or scoring kernel — these should be elevated together,
not independently, because a fix or a design ruling on the shared component moves every asset in
the cluster at once.

1. **`services/ka_temporal` hub** — imported by `ka_kalasutra` (`writers/ka_kalasutra.py:16-19`),
   `ka_vighnakara` (`writers/ka_vighnakara.py:29`), `ka_yojaka` (per the elevation plan's own hub
   table, "Owns `ka_temporal`, `kala_trigger`, `taranga_kernel`" — `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`
   line 123-124), and the century materializer (out of this lane's scope). Both `ka_kalasutra` and
   `ka_vighnakara` read L1 `chart_dashas` through this exact shared helper *without* either one
   declaring the L1 dependency in its own `depends_on` — the same undeclared-read defect,
   independently confirmed in two different writers via the same import path. **A single fix to
   how `ka_temporal` declares/exposes its own upstream dependency would close both findings at
   once**, rather than patching `depends_on` twice.
2. **Elevation-plan Q8 truncation-policy cluster** — `ka_vighnakara`, `ka_kala_darshana`,
   `ka_kalasutra`, `ka_avadhi`, `ka_jivana_parva` (plus `ka_sangam`, out of this lane's scope) all
   carry an undisclosed row-count cap (`LIMIT 500`/`750`/default-eight/`10`/unordered `LIMIT 1`
   respectively) that the elevation plan itself proposes ruling on **once, portfolio-wide**, rather
   than asset-by-asset ("cheaper to rule once than seven times" — elevation plan Q8's own stated
   rationale). This is the single largest elevation-tier lever in this register: one native ruling
   on "what is the honest truncation policy" reclassifies the defect-resolution path for 5 of this
   lane's 16 assets simultaneously.
3. **The `ka_sangam`-descent cluster** (out-of-scope root, in-scope consumers) —
   `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_taranga`, `ka_vighnakara` all
   declare `ka_sangam` as an input, several of them *twice over* via a second declared input that
   itself composes `ka_sangam` (`ka_kala_darshana` for `ka_bhavishya_lekha`/`ka_jivana_parva`;
   `bodha_pratijna`'s shared L2 substrate for `ka_taranga`). Every one of these five assets'
   "independent evidence" framing is compromised by the same single upstream producer, and every
   one of them is also currently starved of real canonical-chart data because `ka_sangam`'s own
   `kala_convergence` is 0 rows for this chart. **This is the highest-leverage cross-cutting fact in
   this lane's entire register**: fixing `ka_sangam`'s canonical-chart data (out of this lane's
   scope, but the dependency is entirely in-scope) would simultaneously un-starve `ka_kala_darshana`,
   `ka_bhavishya_lekha`, and partially `ka_taranga`/`ka_vighnakara`/`ka_jivana_parva`, without a
   single line of code changing in any of them.
4. **Self-test-only service triad** — `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva` share
   one structural pattern: a thin `writers/ka_*.py` shim whose sole job is "import the real service
   module (a deliberate side-effect import to trigger `@register`) and run a FORENSIC self-test that
   writes `service_health`/`selftest_detail` to `asset_registry`, never a domain table." All three
   declare `WriterResult(rows_inserted=0)` by design. A single qualification methodology (what does
   "prove exact conventions, arbitrary chart/time, provenance, failure modes" mean, concretely, for
   a self-test-only asset) would apply near-identically to all three rather than being separately
   invented per asset.
5. **`bo_laksana` CASCADE-exposure cluster (migration `403_kala_signal_fk_cascade.sql`)** —
   `ka_kalasutra`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_vighnakara` (plus `ka_sangam`,
   out of scope) all carry a `signal_id`-keyed `ON DELETE CASCADE` to `bodha_msr_signals`, and all
   four show the identical claimed-vs-actual mismatch signature in this register (`asset_throughput`
   recording a large historical `rows_written`, live table at 0 rows for the canonical chart,
   `state='stale'`, no `last_error`). This is one root cause (a migration whose comment "assumed
   lockstep L3-after-L2 rebuilding that nothing actually enforces," per
   `DATA_LOSS_DIAGNOSIS.md`) producing four separate-looking defect rows in this register. Any
   remediation (rebuild-order sequencing, an escalation on "stale AND empty," or revisiting the
   CASCADE itself) should be designed once for the cluster, not per asset. Note `ka_yojaka`
   (§16) reads/writes `signal_id` too but was NOT hit by this CASCADE in its latest build — its own
   `bound_at` is a fresh 2026-09-10 batch that post-dates the relevant `bo_laksana_rerank` window,
   which is itself informative: the cluster's exposure is timing-dependent (whichever `kala_*`
   writer last ran *before* an L2 MSR regeneration is the one left holding stale-then-cascaded
   `signal_id` references), not a permanent property of the table.

---

# SUMMARY TABLE — asset → elevation tier

| Asset | Elevation tier | One-line justification |
|---|---|---|
| `ka_avadhi` | **HEAVY** | Q8 truncation-policy ruling names it directly; also live `error` state from a failing post-write integrity check. |
| `ka_bhavishya_lekha` | **HEAVY** | Q5 (prospective-claims/history-firewall policy) names it directly; CASCADE-wiped for canonical chart. |
| `ka_dasha_kala` | MODERATE | Real, unexplained consumer-bypass gap (Q2-shaped but unlisted); no open native design question; fix is a wiring/retire decision, not architecture. |
| `ka_graha_sancara` | LIGHT | Self-test does its declared job; production divergence is documented-deliberate, not a defect. |
| `ka_jivana_parva` | **HEAVY** | Q8 names it directly; confirmed unordered `LIMIT 1` selection defect at `:124`. |
| `ka_kala_darshana` | **HEAVY** | Q8 names it directly; CASCADE-wiped and its sole real input (`kala_convergence`) is empty for the canonical chart. |
| `ka_kalasutra` | **HEAVY** | Named by both Q7 (ranking criterion) and Q8 (truncation policy) — two open native decisions on one asset. |
| `ka_kota_chakra` | **HEAVY** | Q2 (wire-in-or-retire) names it directly, compounded by an unreconciled STRAT-vs-consumer contradiction. |
| `ka_moorti_nirnaya` | LIGHT | Correct, live-consumer-confirmed, data matches; sole blocker is an external grant gap (F4), not a design or code defect. |
| `ka_muhurta_seva` | **HEAVY** | Q7 (ranking criterion) names it directly. |
| `ka_sudarshana_varsha` | **HEAVY** | Named by both Q2 (wire-in-or-retire) and Q3 (independent-witness epistemics). |
| `ka_taranga` | **HEAVY** | Q6 (contract/semantics) names it directly; confirmed double-counting defect (transit+promise both trace to one L2 source). |
| `ka_tithi_pravesha` | **HEAVY** | Q2 names it directly; F5-vs-elevation-plan dispute means even "is it served" is unsettled. |
| `ka_tulana` | **HEAVY** | Q7 names it directly; consumer confirmed to read a different asset's table, not its own. |
| `ka_vighnakara` | **HEAVY** | Q8 names it directly; highest defect count in this register (truncation, 2 undeclared reads, structural double-count, CASCADE-wiped). |
| `ka_yojaka` | MODERATE | Real, substantial defects (79 unresolved MSR refs, low-confidence consumer binding) but no open native design question gates it. |

**16/16 assets accounted for. Tier distribution: 12 HEAVY, 2 MODERATE, 2 LIGHT, 0 unassigned.**
The dominant driver of HEAVY grading in this lane is not code quality (several HEAVY-graded assets
have clean, correct, well-commented implementations — `ka_kalasutra`, `ka_jivana_parva`'s clip
logic, `ka_yojaka`'s anti-fabrication dating design) but the elevation plan's own **Q1–Q8** open
native decision list, which names 10 of this lane's 16 assets across seven of its eight items
(all but Q1 and Q4, which belong to the out-of-scope `ka_gochara_v3_century_materialize` and
`ka_kshetra`). This is itself a finding: **this lane cannot be elevated primarily through
engineering work** — most of its assets are gated on a small number of portfolio-level rulings
(truncation policy, ranking criterion, independent-witness definition, prospective-claims policy,
consumed-by-nothing disposition) that, once made, would reclassify several HEAVY assets toward
MODERATE or LIGHT without further code change.
