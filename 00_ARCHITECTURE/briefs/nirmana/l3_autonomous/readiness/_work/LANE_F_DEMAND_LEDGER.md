---
artifact: LANE_F_DEMAND_LEDGER
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_by: L3 Kāla elevation readiness — Lane F (demand ledger), read-only research pass
scope: >
  What downstream layers/surfaces actually demand from Kāla today (evidence-based, not
  aspirational), what Kāla needs from upstream that it does not cleanly get, the scoped
  bodha_msr_signals CASCADE constraint, and the L2/L3 campaign coordination risk it implies.
  Builds on, and does not redo, the completed audit at
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/*.md.
---

# LANE F — Demand Ledger: what everyone needs FROM Kāla, and what Kāla needs FROM upstream

**Method note.** All row counts are from the completed audit's `KALA_DATA_CENSUS_v1_0.md` (F7,
2026-09-22) unless a fresh query is shown inline. All code citations were opened and read in this
pass; none are re-quoted from a prior report without independent verification. Where I could not
verify a claim, it is marked `COULD NOT VERIFY`. A grep that found no caller is reported as a
search-scope result, not proof of absence.

**Headline finding, load-bearing for everything below:** a governance log this worktree can read
— `00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md` — shows that a **separate, currently active
"Nirmāṇa" multi-session campaign** (sessions at `~/nirmana-s/{l0,l1,l2,l3,l4,l5}`, a CONDUCTOR
adjudicating cross-layer conflicts on GitHub issue #1713) has **already discovered, measured, and
partially mitigated** the exact CASCADE mechanism this brief was asked to scope (§3), and has
**already built the tool** this brief was asked to design a minimum viable rule for (§4:
`platform/scripts/nirmana/cascade_check.sql`). This is not this worktree's own git history (branch
`l3/kala-elevation-readiness`, committer "PB-3 Bot") — it is a parallel campaign track visible from
the same repository. Section 4 treats this as binding prior art, not as something to
re-invent.

---

## 1. Downstream demand on Kāla

### 1a. L4 Phala (SEALED) — exact readers, exact fields, and what they do with them

Grep scope: `platform/python-sidecar/pipeline/orchestrator/writers/ph_*.py` (8 files present;
CLAUDE.md's §E table claims 9 `ph_*` assets — one is a service/wrapper without its own writer
file in this directory, not investigated further; flagged as a minor count discrepancy, not
chased since it doesn't change the demand picture). Of the 8, **3 read `kala_*` tables directly**;
the other 5 (`ph_phaladesa`, `ph_sodhana`, `ph_pramana`, `ph_suddha_sodhana`, `ph_sankrama`) have
zero `kala_` hits and were not investigated further (search-scope result, not proof they have no
transitive dependency via `phala_anchors`).

| Writer | Reads | Exact fields consumed | What L4 does with them |
|---|---|---|---|
| `ph_nimitta.py` (THE SPINE of L4; file header line 7) | `kala_convergence`, `kala_bhavishya`, `kala_activation_predicates` | `kala_convergence` (lines 324–347): `convergence_id, chart_id, signal_id, mode, peak_date, window_start, window_end, convergence_score, rarity_years, constituent_factors, source_citation, independent_current_count, confidence_score, confidence_label, domain` — ranked `PARTITION BY domain` so no one domain monopolizes the top-200 (a documented anti-flattening fix, line 320). `kala_bhavishya` (lines 350–361): `id, chart_id, signal_id, convergence_id, domain, peak_date, window_start, window_end, probability_tier, effective_score, falsifiability, source_chain, narrative, outcome_recorded`. `kala_activation_predicates` (lines 478–486): **only** `signal_id` and `(dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count')::int` — see the richness-discarded finding in §2 below; the same row also carries `multi_system_confirmation_by_domain`, `cdlm_domain_strength_by_domain`, `pratijna_ids_by_domain` (ka_yojaka writer, confirmed persisted — see §2) that `ph_nimitta` never selects. | Builds `phala_anchors` (delete-then-insert per chart) — L4's spine table, later frozen into L5's `mimamsa_predictions`/`mimamsa_calibration`/`mimamsa_reliability` (see §1b). |
| `ph_pratikara.py` (mitigation program, file header line 7) | `kala_obstruction`, `kala_convergence` (bridge join) | Lines 220–227: `o.id`, `o.severity`, `o.override` (implied by "severity vocab" comment), `c.window_start`/`c.window_end` (obstruction carries no dates of its own — every date is inherited from the `kala_convergence` row it bridges to via `convergence_id`), `c.constituent_factors->>'planet'` (graha). | Builds `phala_mitigation` (per-chart delete-then-insert); every mitigation row is temporally and causally downstream of a `kala_obstruction`+`kala_convergence` pair existing. |
| `ph_muhurta.py` (lines 270–390) | `kala_obstruction` JOIN `kala_convergence` | `o.id`, `c.window_start`, `c.window_end` (same bridge pattern as `ph_pratikara`). Also documents (lines 362–378) that a **prior version** queried a non-existent `FROM kala_gochara` table (an L3 *service*, not a table) — the read always errored, was silently swallowed, and permanently zeroed the transit score; now explicitly returns `{}` with a logged reason instead. | Feeds `_load_obstruction_windows`'s influenceable-anchor overlap check for muhurta scoring. |

**Compatibility-constraint flag (CLAUDE.md §E: L4 is SEALED).** Per the completed census (F7),
for the **canonical chart**, `kala_convergence = 0 rows`, `kala_bhavishya = 0 rows`,
`kala_obstruction = 0 rows` — all three tables `ph_nimitta`/`ph_pratikara`/`ph_muhurta` read
directly. Live re-query in this pass confirms this is still true today (2026-09-22):

```sql
-- (canonical chart_id)
phala_anchors     = 4     -- vs. asset_throughput's last recorded write: 139 rows, 2026-08-13
phala_mitigation  = 536   -- asset_throughput's last recorded write: 536 rows, 2026-08-13 (unchanged)
mimamsa_predictions  = 139
mimamsa_calibration  = 57
```

`asset_throughput` (queried live) confirms `ph_nimitta`/`ph_pratikara` both last built
**2026-08-13** and are marked `state='stale'` today, with no `last_error` — i.e. their inputs
disappeared out from under a "successful" prior build, not that the writer is broken. **Any Kāla
elevation change that alters `kala_convergence`/`kala_bhavishya`/`kala_obstruction`'s schema,
grain, or domain semantics is a compatibility break against a layer CLAUDE.md declares SEALED and
"ran end-to-end"** — the honest state today is that L4's sealed run already happened against data
that has since been destroyed (see §3/§4), so "L4 is sealed" should be read as "L4's *contract* is
sealed," not "L4's current data reflects that contract's inputs."

### 1b. L5 Mīmāṃsā — indirect (via L4) plus one direct reader

Grep scope: all 14 `mi_*.py` writers. **Zero** of `mi_bhavisya.py` (DP15a claim issuance),
`mi_pramana.py` (DP15b adjudication/calibration), `mi_darshana.py`, `mi_jivanaghatana.py` read
`kala_*` tables directly (confirmed by direct grep, no hits). L5's demand on Kāla for frozen
claims and prediction windows is **entirely mediated through L4**:

- `mi_bhavisya.py` (lines 50, 80, 134–142) reads `phala_anchors` and freezes
  `window_start`/`window_end` (falling back to `start_date`/`end_date` if absent) into
  `mimamsa_predictions`'s immutable bundle. Those bounds originated in `kala_convergence`'s
  `window_start`/`window_end` or `kala_bhavishya`'s, via `ph_nimitta`. **Kāla's temporal
  precision is L5's claim-window precision** — there is no L5-side re-derivation.
- `mi_pramana.py` matches those frozen claims against LEL events; it does not read Kāla.

**One direct reader exists:** `mi_bhara.py` ("Kāla Bhāra, the weight of time" — STAGE 9 of the
temporal-field calibration pipeline, file header lines 1–5) reads `kala_field` directly (line 403:
`SELECT field_snapshot_id FROM kala_field WHERE chart_id = %s LIMIT 1`) — the `ka_kshetra`
continuous-field table (8,570,075 rows for the canonical chart per F7). This is L5's actual
"knowledge time" plumbing demand: a calibration fit keyed to whatever temporal field exists.
Critically, `mi_bhara.py` was **built to degrade honestly** when `kala_field` is absent (a named
`WriterResult` note `kala_field_absent`, lines 33–37, 119–129) — it does not read
`kala_field_snapshots` (the S8 "complete snapshot" terminus the audit already found empty for the
canonical chart at 0/1 rows) and is therefore **not** blocked by that particular gap. **Plumbing
exists and degrades honestly; it has not been observed to run against a populated field for this
chart in this pass** (`COULD NOT VERIFY` whether `mi_bhara` has ever produced a non-classical-prior
fit for the canonical chart — no query was run against `mimamsa_*` weight-fit output tables to
avoid scope creep beyond the demand question).

### 1c. Served surfaces — MCP `kala_views/*` and retrieval `L3_kala/*`

Both directories are large (29 files under `platform-mcp/src/tools/kala_views/`, 28 under
`platform/src/lib/retrieval/registry/layers/L3_kala/`). Two were read in full or near-full; the
pattern generalizes per the audit's own T1 receiving-operator table (already exhaustive per-asset,
not re-walked here).

- **`query_convergence_windows.ts`** (178 lines, read in full) — well-built: selects nearly every
  `kala_convergence` column (`convergence_id, signal_id, window_start, window_end, peak_date,
  mode, convergence_score, orb_strength, rarity_years, confidence_score, confidence_label,
  independent_current_count, is_off_dasha_discovery, horizon_tier, domain,
  constituent_factors, source_citation`), returns honest pagination (`buildHonestPagination`,
  never a silent top-K trim), and returns `signal_id_refs` for drill-down. **Its own docstring
  (line 4) says "19,482 rows per chart"** — stale, written before the CASCADE wipe documented in
  §3/§4; the true canonical-chart count today is 0. This mismatch is itself evidence the wipe
  happened after this tool's description was last updated.
- **`query_temporal_activation.ts`** (676 lines; relevant sections read at lines 270–300,
  378–400, 460–545) — also disciplined: preserves both `kala_activation`'s DATE columns (via
  `to_char`) and does not fabricate a "strongest" ranking (a documented fix, lines 291–297,
  switched the primary sort key off `orb_strength` — 99.6% NULL, measured — onto
  `dasha_activation_proximity_score`, 0% NULL). Explicitly labels its `kala_bhavishya` fallback
  as **incompatible and closed** when an explicit ayanamsha or `min_activation_strength` filter is
  present (lines 470–475: "Never drop either constraint while echoing it as honored"), and reports
  an honest `empty_reason` naming the exact filter and coverage (lines 460–466) rather than a bare
  empty result.
- **The one confirmed field-dropping case is at the L3→L4 boundary, not inside a served surface**:
  `ka_yojaka.py` (lines 845–917) computes and **persists** a complete per-domain breakdown
  (`cdlm_domain_strength_by_domain`, `multi_system_confirmation_by_domain`,
  `pratijna_ids_by_domain` — all written into `kala_activation_predicates.dasha_eligibility_rule_jsonb`
  at the INSERT, line 428) precisely because "the complete map preserves secondary-domain support
  without cross-domain inflation" (line 855 docstring). `ph_nimitta.py` (line 479) reads **only**
  the single derived scalar `multi_system_confirmation_count` — the primary-domain-only figure —
  and never selects the three richer keys. The richness reaches the table; it is fetched into L4
  and dropped before synthesis.

**Pattern across served surfaces:** the MCP/retrieval code itself is disciplined about honest
gaps (§N.6/§N.7 style: `empty_reason`, `more_available`, no silent truncation observed in the two
files read in depth). The actual "dropped before synthesis" failure mode found in this pass is not
sloppy serving code — it is (a) upstream tables being empty for the canonical chart (§3/§4) and
(b) one confirmed richness-discarded boundary (`ka_yojaka` → `ph_nimitta`, above). The audit's own
T1 table (`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`) already catalogs per-asset receiving-operator
confidence exhaustively; this pass does not repeat that enumeration.

### 1d. The product's own promises that require a time answer

From `MADHAV_PRODUCT_DEFINITION_v3_0.md` (the adopted, CURRENT target — v2.2 is SUPERSEDED):

| Promise | Product text | Owning Kāla capability | Status |
|---|---|---|---|
| §3.10 "Kāla: structure meeting time" | Daśā systems, gochara, annual/return methods, Tājaka, tithi-praveśa, Sudarśana, aṣṭakavarga, vedha; "compare nearest and stronger later windows using a named criterion" | `ka_dasha_kala`, `ka_gochara*`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`, `ka_vedha_gochara`, `ka_kalasutra`/`ka_tulana` (nearest-vs-strongest) | Per the audit's T1: `ka_dasha_kala`'s own writer output has **no confirmed consumer** (`call_dasha_eligibility` bypasses it, reading `chart_dashas` directly); `ka_tulana`'s consumer reads `kala_activation` (owned by `ka_kalasutra`), not any `ka_tulana` table — **NOT-FOUND, confirmed**. The nearest-vs-strongest promise has no single asset that both computes and is read for it end-to-end. |
| P09 "Does this yoga form, and when might it manifest?" | formation → activation → manifestation chain | `ka_yojaka` (`kala_activation_predicates`) → `ph_nimitta` | Data exists (50,678 rows) but qualification is `COULD NOT VERIFY` per census (79/50,678 unresolved MSR refs) and consumption is low-medium confidence per T1. |
| P10 "What chapter am I entering...cross-domain trajectories" | `ka_jivana_parva` | `kala_jivana_parva` (100 rows, canonical chart) | LIVE, medium-high confidence (`query_life_arc.ts` → `kala_life_arc_get`, confirmed registered). One of only two genuinely wired-and-populated Spine assets per T1. |
| P11 "When might I initiate something...voluntary attributed practices" | `ka_muhurta_seva` | Live per T1 (medium confidence, `score_muhurat()` reuse) | **T1's own orphan-obligation finding stands**: `ka_muhurta_seva` has **no proving-journey citation** in the product doc's §12 worked examples despite being P11's direct answer — a real gap in the product's own worked-example coverage, not a code defect. |
| P22 "pañcāṅga and permitted personal relevance" | general calendar context | Not owned by any single audited `ka_*` asset in T1 (closest: `ka_avadhi`'s clock enumeration, and L0's `call_panchanga_service` which `now.ts` already joins against per its own header, lines 12–24) | Served today via an L0 service join inside a `kala_views` facade, not a dedicated L3 writer — consistent with the product's own §3.11 distinction that pañcāṅga/Praśna/Muhūrta are separate practices; not a gap, a correctly-placed boundary. |
| P05/P06 "marriage timing," family-domain windows | `kala_bhavishya`/`kala_convergence` with `domain='relationship'` | Same tables as §1a — **0 rows canonical chart** | Demand with no current supply for this chart, not a missing capability — the capability exists and is starved (§3/§4). |

**Promises with no owning capability at all (orphan demand), per the audit's own T1 orphan lists,
independently spot-confirmed in this pass:**

- **7 of 9 Frontier assets have no U-id** (`ka_graha_sancara`, `ka_muhurta_seva`,
  `ka_gochara_resonance`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`,
  `ka_tithi_pravesha`) — T1's own finding, not re-derived here, cited because it is exactly the
  "demand with no supply" question this ledger was asked to answer at the interface layer.
- **The century materialiser (`ka_gochara_v3_century_materialize`) has no U-id at all** — no
  interface obligation names it despite "more code than the other twenty combined" (T1).
- **`ka_kshetra`'s own U01 obligation is unsatisfied**: the only candidate receiving operator is
  low-medium confidence and directly contradicted by the audit's PARK-5 finding (a served surface
  hard-codes "field empty" against a table holding 8.57M rows) — confirmed still true in this pass
  (no PARK-5 file was independently re-read; cited from T1 as a known, not re-verified, finding).

---

## 2. Kāla's upstream requirements — what it needs from L0/L1/L2 that it does not cleanly get

### 2a. Ayanamsha convention mismatches (beyond the already-known one)

The task brief names one known defect: `call_dasha_eligibility` defaults to bare `'lahiri'` instead
of canonical `lahiri_chitrapaksha`. Confirmed still live at
**`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:328`**:
```ts
const ayanamsha_id  = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri'
```
The input-schema description at line 298 even documents the wrong default in the tool's own
user-facing text (`"Ayanamsha (default: 'lahiri')."`). Mechanism: `chart_dashas` is scoped by
`ayanamsha_id='lahiri_chitrapaksha'` for the canonical build, so an omitted-parameter caller
silently gets **zero rows**, not an error — the exact "no eligible window found" masquerading as
relief that the product definition (§7.1) explicitly warns against.

**Three additional, previously undocumented instances found in this pass:**

1. **`platform/python-sidecar/services/ka_graha_sancara/engine.py:302-306`** — the live
   Swiss-Ephemeris compute path (this is L3-A01, the Frontier's foundational
   position/motion service every other Kāla asset ultimately traces to for arbitrary-instant
   computation):
   ```python
   if ayanamsha != "lahiri":
       raise NotImplementedError(
           f"Live swisseph path only supports 'lahiri' ayanamsha; got {ayanamsha!r}. "
   ```
   This is not a *default* mismatch, it is a **hard equality gate against the literal string
   `"lahiri"`** — calling this path with the canonical `lahiri_chitrapaksha` string would raise,
   not silently misbehave. Whether any live caller actually passes `lahiri_chitrapaksha` through
   to this function is `COULD NOT VERIFY` in this pass (would require tracing every call site);
   flagged because it means the foundational service **cannot even accept** the canonical
   convention name today, regardless of caller discipline.
2. **`platform/python-sidecar/services/ka_sangam/engine.py:1099`** —
   `ayanamsha_id = predicate.get('ayanamsha_id') or 'lahiri'` inside `ka_sangam` itself, the
   campaign's own named chokepoint ("THE VALUABLE CORE," 7/21 assets depend on it per T1).
3. **`platform/python-sidecar/services/ph_nimitta/dasha_consensus.py:157`** —
   `ayanamsha_id: str = 'lahiri'` as a Python default parameter in an **L4** module that consumes
   Kāla's daśā consensus — meaning the mismatch is not confined to L3's own boundary; it recurs at
   the L3→L4 handoff too.

**Fix ownership:** all four instances are readers/callers defaulting incorrectly, not L0's
`DEFAULT_AYANAMSHA` constant itself being wrong (confirmed correct value cited in the audit:
`lahiri_chitrapaksha`, used correctly by "the other 4 wrappers in the same file" per
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md:477`). **Fix belongs at each reader**, not upstream —
L0's convention is right; these are call-site defaults that never import it.

### 2b. Precision loss

The most consequential precision-loss defect found (**already fixed**, cited as a positive
pattern, not a live defect) is the DATE-column timezone bug documented inline at
`query_convergence_windows.ts:112-116` and `query_active_dashas.ts:125`: `window_start`,
`window_end`, `peak_date`, `activation_start`/`end` are DATE columns; naive node-postgres
serialization parses them at IST midnight then re-emits as UTC, shifting e.g. `1990-05-14` to
`"1990-05-13T18:30:00.000Z"` — an off-by-one plus a spurious time component. **Both files now use
`to_char(col, 'YYYY-MM-DD')` to pin the true calendar value.** This is upstream-caused (the schema
chose DATE, not the reader), fixed at the reader per the note; flagged here only because it is
exactly the class of defect the task asked to check for, and other DATE-typed `kala_*` columns not
audited in this pass (e.g. in `kala_jivana_parva`, `kala_taranga`) were not individually checked
for the same fix — `COULD NOT VERIFY` whether the `to_char` discipline is applied consistently
everywhere DATE columns are read.

**One residual, minor precision concern, not independently confirmed as a live bug:**
`query_active_dashas.ts:133` filters the active chain with
`start_date <= $3::date AND end_date >= $3::date` — using the DATE columns, not the co-located
`start_iso`/`end_iso` TIMESTAMPTZ columns that `chart_dashas` also carries (confirmed present via
live schema query: both `start_date`/`end_date` DATE and `start_iso`/`end_iso`
`timestamp with time zone` columns exist). A daśā period that starts at 23:50 IST would read as
"active" for the entire calendar day it starts on. Whether this ever produces a materially wrong
answer for a boundary-sensitive question (e.g. "which daśā governs this exact hour") is
`COULD NOT VERIFY` without a specific test case — flagged as a candidate boundary-precision gap,
not confirmed.

### 2c. Richness discarded

Covered in full in §1c above: `ka_yojaka` computes and persists a complete per-domain map into
`kala_activation_predicates.dasha_eligibility_rule_jsonb`; `ph_nimitta` reads only the
primary-domain scalar derived from it. This is a **downstream** (L3→L4) richness-discard, the
mirror image of an upstream one, but it is exactly the pattern the task asked to find, and it is
the one instance in this pass with a confirmed, cited, currently-live code trail on both the
write side and the read side.

No upstream (L0/L1/L2 → L3) richness-discard instance was independently confirmed with the same
rigor in this pass; the audit's own T1 already documents several candidates at the L2→L3 boundary
("one-domain/five-link flattening" required for `ka_yojaka`, REGISTER:147/STRAT:281) which this
pass independently re-confirmed is **partially fixed** (the per-domain map now exists, per above)
but **not fully** — `primary_domain = domains[0] if domains else None`
(`ka_yojaka.py:886`) remains the value actually exposed through the legacy scalar path, "exactly
matching `ph_nimitta`'s existing `domains_affected_array[1]` selection" per the code's own
docstring (line 855) — i.e. the flattening is now a *documented, intentional* backward-compatible
scalar, not an accidental one, but it is still the value L4 actually consumes.

### 2d. Grain mismatch

Not independently re-derived beyond what T1 already documents (`ka_avadhi`: "assess missing
ayanamsha, fixed domains, ten-row limits, soft-empty behavior", REGISTER:153/STRAT:282). One new,
independently confirmed grain fact: `chart_dashas` is a **flat one-row-per-(level, lord)** model
(confirmed by `call_service_wrappers.ts`'s own input-schema comment, line ~310: "`chart_dashas` is
a flat one-row-per-level model (`level_n` + `lord_graha`)"), while several Kāla consumers
(`ka_avadhi`, `ka_dasha_kala`) need a **hierarchical** parent/child clock structure per DP07's own
contract language ("parent/child clock, hierarchy"). Whether this flat-to-hierarchical
reconstruction happens correctly and consistently across all Kāla readers of `chart_dashas` was
not independently tested in this pass — flagged as a grain question worth a dedicated test, not
asserted as a confirmed defect.

---

## 3. The cascade constraint — scoped, and a candidate stable binding

### 3.1 The five tables, confirmed live (not merely cited from migration 403)

Live query against `pg_constraint` (2026-09-22, this pass):
```sql
SELECT conrelid::regclass AS child_table, confdeltype
FROM pg_constraint
WHERE contype='f' AND confrelid='bodha_msr_signals'::regclass;
```
Result — **eight** FKs total, confirming the audit's "all eight" claim independently:

| Child table | Layer | `confdeltype` |
|---|---|---|
| `kala_convergence` | L3 | `c` (CASCADE) |
| `kala_activation` | L3 | `c` (CASCADE) |
| `kala_obstruction` | L3 | `c` (CASCADE) |
| `kala_darshana` | L3 | `c` (CASCADE) |
| `kala_bhavishya` | L3 | `c` (CASCADE) |
| `bodha_contradictions` (×2 FK columns) | L2 | `c` (CASCADE) |
| `bodha_signal_embeddings` | L2 | `c` (CASCADE) |

**Exactly the five `kala_*` tables named in the task are confirmed.** `kala_activation_predicates`
(ka_yojaka's own table, the single largest live-for-canonical-chart Kāla surface, 50,678 rows) is
**not** among the eight — it has no CASCADE-enforced FK to `bodha_msr_signals` at all. This is
independently consistent with the census's own finding of 79/50,678 (0.156%) unresolved
`signal_id` references in that table: without a CASCADE FK, a signal deletion leaves
`kala_activation_predicates` rows **silently dangling** instead of being cleanly removed — a
different, arguably worse failure mode (silent orphan vs. clean cascade) than the five tables that
do have the FK.

### 3.2 The mechanism, traced to source

`platform/python-sidecar/bodha_writers/_idempotency.py:136-185`
(`replace_prior_msr_for_chart`) is the shared idempotency helper all six `bodha_msr_signals`
producer writers call (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`,
`bo_vargottama_dhana`, `bo_nakshatra_semantic` — confirmed by grep, each imports this exact
function). Its own in-code comment (added after the incident it describes) states plainly:

> "Every FK onto `bodha_msr_signals` is `ON DELETE CASCADE`... one MSR rebuild removes 864,733
> rows across 12 tables in three layers, only 150,126 of which are deleted by the statements
> below. The rest Postgres removes without a word."

This is a **blanket delete of every row the calling writer owns** for `(chart_id, ayanamsha_id)`,
scoped by `signal_type_class` allowlist (not a diffed/targeted delete of only changed rows) — every
rebuild of any of the six producers deletes and reinserts its *entire* owned row set, and Postgres
fires the CASCADE at DELETE time, before the matching INSERT recreates rows in the same
transaction.

**Deterministic identity already exists and is already wired — but does not, by itself, prevent
the destructive event.** `bo_laksana.py:3140-3230` (`assign_deterministic_signal_ids`) replaces
`uuid4()` with `bodha_signal_identity(chart_id, ayanamsha_id, signal_type_id, varga_id,
configuration_jsonb)` — a deterministic hash function (migration 660/661, confirmed via grep and
via `bo_laksana.py`'s own citations), verified live "150,150/150,150 rows re-derivable" per the
code's own comment. This was built specifically as the fix to a related, already-adjudicated
finding (`CAMPAIGN_STATE.md` D-CND-11, "a stable identity key excludes every graded, calibrated or
recomputed quantity"; `#1804`, "D-CND-11 as amended"). **Why this doesn't solve the cascade
problem**: a DELETE statement fires `ON DELETE CASCADE` immediately, regardless of whether a
later INSERT in the same transaction recreates a row with an identical primary key. Determinism
means a Kāla row can be **correctly re-derived and re-attached** to the same `signal_id` after a
rebuild (which is exactly what `_idempotency.py`'s comment and `CAMPAIGN_STATE.md:156-157`
describe as the operational mitigation: "L3 confirmed its five `kala_*` tables re-runnable from a
rebuilt MSR base") — it does not mean the Kāla row **survives** the rebuild without being deleted
and rewritten.

### 3.3 A DB-side guard exists, but it authorizes, it does not protect blast radius

`_idempotency.py:37-52` calls `public.assert_l2_msr_delete_safe(...)` (defined in migration
`1036_data_plane_l2_producer_generations.sql:687-727`) before every scoped delete. Read in full:
this function requires the delete to run as `session_user = 'data_plane_builder'` under an
**admitted, currently-`building`** L2 generation record (`l2_data_plane_run_intents` joined to
`data_plane_l2_producer_generations`), and `FOR UPDATE`-locks the exact rows about to be deleted to
close a check/delete race. **It is an authorization and race-safety gate, not a cross-layer
blast-radius gate** — it does not query whether any `kala_*`/other-layer row currently references
the rows it is about to delete. The actual blast-radius protection is a **procedural** tool run
before dispatch (§4), not a schema-enforced backstop.

### 3.4 Candidate stable natural key

`bodha_msr_signals`'s live schema (confirmed via `information_schema.columns` +
`pg_constraint`) already carries a near-natural key as its declared UNIQUE constraint:
**`(chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb)`**. `build_id` is the
problem column for stability — it changes every rebuild by design, so this UNIQUE constraint does
not by itself give a rebuild-stable identity.

**The actually-stable candidate is the tuple `bodha_signal_identity()` already hashes over:
`(chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb)`** — excluding `build_id`
entirely. This is not a proposal; it is the **existing, deployed, verified-live** function
(migration 660/661) that `signal_id` itself is now computed *as*, for the six current producer
writers. The identity is therefore already available to any Kāla writer as
`bodha_signal_identity(...)` — no schema change needed to compute it.

**What a genuinely survivable binding would require, beyond what exists today** (this is the
input the task asked for; none of the following is built or authorized by this pass):

1. A Kāla row's cross-layer reference should **not** be a hard FK with `ON DELETE CASCADE` onto
   `bodha_msr_signals.signal_id` at all — because `signal_id` *is* the stable hash today, but the
   *row* it names is still subject to a delete-then-recreate cycle within one upstream
   transaction. A Kāla row that stores the same five-tuple (or its hash) as a **plain value
   column** (no enforced FK, or a `DEFERRABLE INITIALLY DEFERRED` FK checked only at transaction
   commit, if Postgres's cascade-on-delete semantics can be deferred that way — `COULD NOT VERIFY`
   without a dedicated Postgres-semantics test whether `DEFERRABLE` changes cascade-timing
   behavior; flagged as the one open technical question a `ka_sangam` brief would need to close
   before choosing this route) would not be destroyed by the upstream delete; it would simply
   become momentarily "unverified" and re-verifiable by re-computing
   `bodha_signal_identity(...)` from its own stored tuple.
2. Short of a schema change, changing `replace_prior_msr_for_chart` from a blanket
   delete-then-insert to a **diff-based upsert** (delete only signals whose derived identity is
   genuinely absent from the new batch; `ON CONFLICT (signal_id) DO UPDATE` for unchanged ones)
   would make the CASCADE fire only for signals that actually disappeared or changed — the
   correct, desired case — rather than for every signal on every rebuild. This is a change to
   shared L2 infrastructure (`_idempotency.py`), out of L3's own authority, and would need to be
   proposed to the L2 owner, not built unilaterally by a Kāla session.
3. Absent either of the above, the durable near-term binding is **operational**: any Kāla writer
   that reads `bodha_msr_signals` should be able to detect "my `signal_id` no longer resolves"
   (the 79/50,678 dangling case in `kala_activation_predicates` shows this detection is not yet
   universal) and re-derive its correct identity via `bodha_signal_identity(...)` rather than
   silently orphaning or erroring.

---

## 4. L2 coordination risk

**This is not a hypothetical to be designed for — it has already happened, more than once, on the
canonical chart, and is already governed (imperfectly) by a live process.**

### 4.1 Evidence it already happened

Live `asset_throughput` query (this pass, canonical chart):

| Asset | State | Rows written | Last built |
|---|---|---:|---|
| `ka_sangam` | stale | 14,868 | 2026-08-13 01:07 |
| `ka_vighnakara` | stale | 536 | 2026-08-13 01:08 |
| `ka_kalasutra` | stale | 335,403 | 2026-08-13 01:15 |
| `ka_kala_darshana` | stale | 750 | 2026-08-13 01:15 |
| `ka_bhavishya_lekha` | stale | 100 | 2026-08-13 01:15 |
| `ph_nimitta` | stale | 139 | 2026-08-13 01:16 |
| `ph_pratikara` | stale | 536 | 2026-08-13 01:16 |
| `bo_laksana` | **lit** | 50,529 | **2026-09-08** 18:22 |
| `bo_arudha` | lit | 25 | 2026-09-10 00:18 |
| `bo_sudarshana` | lit | 45 | 2026-09-10 00:18 |
| `ka_yojaka` | stale | 50,678 | 2026-09-10 17:17 |
| `bo_special_lagna` | lit | 20 | 2026-09-11 12:09 |
| `bo_nakshatra_semantic` | lit | 45 | 2026-09-11 12:09 |
| `bo_vargottama_dhana` | lit | 14 | 2026-09-11 12:09 |

Every Kāla/Phala asset in this table that reads `bodha_msr_signals` shows `state='stale'` with a
2026-08-13 last-build timestamp — **before** `bo_laksana`'s 2026-09-08 rebuild and three more L2
producer rebuilds (09-10, 09-11) that followed it. `kala_convergence`/`kala_bhavishya`/
`kala_obstruction`/`kala_darshana`/`kala_activation` all show 0 rows for the canonical chart today
(§1a, §3.1) despite `asset_throughput` recording real, substantial writes on 2026-08-13. This is
the CASCADE mechanism (§3) having actually fired, at least once, between 2026-08-13 and today,
consistent with (and independently corroborating) the audit's own "the data existed once and is
gone, unexplained" finding — this pass's contribution is that it is **no longer unexplained**: the
governance log (§4.2) names the exact mechanism and the exact session that triggered the
authorized version of it.

### 4.2 The governance process already exists — and already ruled on this

`00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md` (lines 162-227, "the CASCADE finding") documents
issue **#1770**: an L2 session, before dispatching a `bo_laksana` MSR rebuild, found (a) the prior
Conductor ruling on #1748 had relied on a **false code comment** claiming the FKs were `NO ACTION`
(they are all CASCADE — `confdeltype='c'`, independently re-confirmed live in §3.1 above), and (b)
the transitive closure of one `bo_laksana` rebuild is **864,733 rows across 12 tables in three
layers** (L2 150,126 · L3 710,899 · L4 3,708) — including `phala_anchors`, the exact table a
separate hold (#1732/D-CND-04) existed to protect. The campaign took an instance-level snapshot
(`cloudsql-backup:1788566627645`) before proceeding, and released the hold on the L3 write **only
after** "L3 confirmed its five `kala_*` tables re-runnable from a rebuilt MSR base"
(`CAMPAIGN_STATE.md:156`) — i.e. the resolution was procedural (re-run Kāla after L2), not
structural (prevent the cascade).

Two standing rulings now bind every future dispatch in that campaign:

- **D-CND-15**: "the campaign's DAG models ANCESTORS... `ON DELETE CASCADE` makes DESCENDANTS a
  destruction surface... Before any `rebuild_only` dispatch, the owning session enumerates the
  transitive CASCADE closure of every table its writer deletes from and holds if it crosses a
  layer boundary."
- **D-CND-16**: "a comment asserting a schema property is not evidence of that property... the
  check queries the catalogue."

**The tool already built for this** is `platform/scripts/nirmana/cascade_check.sql` — read in this
pass. Its own header states the rule plainly: "RUN THIS BEFORE EVERY `rebuild_only` DISPATCH, for
every table your writer deletes from," reports `depth`/`layer`/`live_rows`/`verdict` per
CASCADE-reachable descendant, and prints `CROSS-LAYER *** HOLD ***` for any table outside the
calling writer's own layer. Its own documented honest limit: it only catches FK-declared CASCADE,
not no-FK orphans (the `kala_activation_predicates` case in §3.1) or `ON DELETE SET NULL` — a
second and third query in the same file cover those two cases respectively (D-CND-18/D-CND-19).

### 4.3 What must be coordinated, stated plainly

1. **Any Kāla elevation session that dispatches a `rebuild_only` for any of `ka_sangam` /
   `ka_kalasutra` / `ka_vighnakara` / `ka_kala_darshana` / `ka_bhavishya_lekha` (the five
   cascade-exposed writers) is a *reader* of a destruction surface it does not own** — the
   dependency runs the other way (L2 deletes, L3 is destroyed), so a Kāla session cannot protect
   itself by holding its own writers; it can only (a) detect that its data was destroyed by an L2
   rebuild it didn't dispatch, and (b) re-run its own writers afterward, per the already-ruled
   pattern.
2. **The minimum viable rule, with no code change, already exists and is not L3-specific — it must
   simply be adopted by whichever process is coordinating this Kāla elevation campaign**:
   - Before any L2 session dispatches a rebuild of `bo_laksana`/`bo_arudha`/`bo_special_lagna`/
     `bo_sudarshana`/`bo_vargottama_dhana`/`bo_nakshatra_semantic`, run
     `cascade_check.sql -v table=bodha_msr_signals` and treat any `CROSS-LAYER *** HOLD ***` row
     touching a `kala_*` table as a hold, per D-CND-15 — file an adjudication, take a snapshot,
     get the owning Kāla session to confirm its tables are re-runnable **before** the L2 rebuild
     proceeds (the exact sequence already exercised on #1770).
   - Any Kāla elevation work that runs `ka_sangam`/`ka_kalasutra`/`ka_vighnakara`/
     `ka_kala_darshana`/`ka_bhavishya_lekha` should **expect** to need a re-run immediately after
     any concurrent L2 MSR producer rebuild, and should not treat a "stale" `asset_throughput`
     state with no `last_error` on these five assets as a Kāla-side bug before checking whether an
     L2 rebuild happened in between (exactly what this pass found, independently, before reading
     `CAMPAIGN_STATE.md`).
   - If this Kāla elevation campaign is coordinated through a **different** process than the
     `~/nirmana-s/*` CONDUCTOR track (this worktree's own git history, branch
     `l3/kala-elevation-readiness`, suggests it may be), that process needs an explicit bridge to
     the Nirmāṇa CONDUCTOR's issue #1713 coordination channel, or its own equivalent —
     **duplicating the CASCADE discovery from scratch, without reading `CAMPAIGN_STATE.md` first,
     is the single most avoidable waste this ledger can flag.**
3. **If Kāla's own elevation work is scoped separately from the L2 Nirmāṇa track** (as the
   git log at the top of this session's context suggests — "L2 cycle #82," "L2 cycle #81" —
   possibly a different numbering/session lineage than `~/nirmana-s/l2`), confirm which L2 process
   is authoritative for `bodha_msr_signals` writes against the canonical chart **before** treating
   either the audit's F7 census or this ledger's live re-query as a stable baseline — both are
   snapshots that an unrelated, already-observed-to-be-active L2 rebuild can invalidate without
   warning.

---

## Evidence index (file:line, for anything load-bearing above not already inline)

- `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:7,320-361,478-486`
- `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:7,205-227`
- `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:270-390`
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py:50,68,80,134-142`
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py:1-37,119-129,403`
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py:1-21` (no kala_ hits, confirmed)
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts:1-178` (full file)
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:270-300,378-400,460-545`
- `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:296-330`
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts:46-159`
- `platform/python-sidecar/services/ka_graha_sancara/engine.py:283-308`
- `platform/python-sidecar/services/ka_sangam/engine.py:1099`
- `platform/python-sidecar/services/ph_nimitta/dasha_consensus.py:97,157`
- `platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py:845-917`
- `platform/python-sidecar/bodha_writers/_idempotency.py:37-52,136-185`
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:108-130,3140-3230,3580-3660`
- `platform/supabase/migrations/403_kala_signal_fk_cascade.sql` (full file, 33 lines)
- `platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql:687-727`
- `platform/scripts/nirmana/cascade_check.sql:1-60` (header + rule text)
- `00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md:20-60,140-230,299-354`
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/KALA_DATA_CENSUS_v1_0.md` (F7, full)
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` (T1, full)
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/KALA_DAG_RECONCILIATION_v1_0.md` (F3, full)
- `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` (full, adopted target)
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md` (full)
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` (full)
- Live DB queries (this pass, read-only, `default_transaction_read_only` session):
  `pg_constraint` FK/CASCADE enumeration on `bodha_msr_signals`; `asset_throughput` per-asset
  state/rows/timestamp for 14 named assets; `phala_anchors`/`phala_mitigation`/
  `mimamsa_predictions`/`mimamsa_calibration` row counts; `bodha_msr_signals` and `chart_dashas`
  column/constraint introspection — all scoped to `chart_id='482012f1-710e-4a25-994a-93821f5871aa'`
  or unscoped metadata queries; no narrative/interpretive content selected.
