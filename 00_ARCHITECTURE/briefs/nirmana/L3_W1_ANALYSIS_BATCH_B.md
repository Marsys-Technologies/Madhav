---
artifact: L3_W1_ANALYSIS_BATCH_B
canonical_id: L3_W1_ANALYSIS_BATCH_B
version: "1.0"
status: DRAFT-FOR-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3
batch: B
theme: "Quality overlays — consumed modulation vs shelf inventory"
assets:
  - ka_kota_chakra
  - ka_moorti_nirnaya
  - ka_vedha_gochara
  - ka_sudarshana_varsha
  - ka_tithi_pravesha
measurement_basis: "live prod DB via .l3-tools/q.sh (role amjis_app, SELECT only), 2026-09-05; DB CURRENT_DATE observed = 2026-09-04"
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
second_chart: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
---

# L3 W1 ANALYSIS — BATCH B: the quality overlays

## Batch summary

1. **Exactly one of the five is consumed modulation. Four are emitted-but-inert.**
   `ka_vedha_gochara` alone feeds a term that changes a served number: `quality_gates` in the
   gochara_v3 λ_v3 product (`services/gochara_v3/engine.py:629`,
   `_compute_quality_gates_from_context` at `:270-412`, fed by `ClassContext.vedha_rows`,
   `context.py:233/408`). The other four are read by `kala_now_get` and re-emitted verbatim as
   passive top-level fields; nothing downstream reads them.

2. **The mechanism modules that *would* consume kota / moorti / tithi-praveśa / sudarśana exist,
   are all `admission_state: candidate`, and are structurally unreachable — not merely unwired.**
   `w25_kota_chakra`, `w22_moorti_nirnaya`, `w27b/w27c` read `context.kota_*` /
   `context.moorti_rows` / `context.tithi_pravesha_rows` / `context.sudarshana_rows`. **None of
   those fields exists on `ClassContext`** (verified: `context.py:113-176` — the dataclass carries
   only `av_gate_rows`, `sade_sati_phases`, `vedha_rows`, `malefic_scale`). Every one of those
   mechanisms therefore returns its honest `modifier=1.0` on every call, on every chart, forever.
   `engine.py` imports only `_w23` and `_w30`. This is the D-SERVICE "built-but-unplugged" class,
   two layers deep: the table is built, the consumer is written, and the pipe between them was
   never laid.

3. **Migration 562 records a dependency edge that does not exist in code.**
   `asset_registry.depends_on` for `ka_gochara_v3_century_materialize` is
   `{ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya, ka_kota_chakra, ka_tithi_pravesha,
   bg_sky_calendar}` (measured), and migration 562's own comment justifies three of those with
   *"reads pre-built rows via ClassContext"* — which is false for moorti, kota and tithi_pravesha
   per finding 2. Three declared-but-unread edges; only `ka_vedha_gochara` (and
   `ka_gochara_resonance`) are real.

4. **HEADLINE DEFECT — the `kala_now_get` overlay fields are silently page-truncated, and the
   "honest empty" they emit is not earned (§N.8).** All three horizon-scanning capabilities cap at
   `MAX_LIMIT = 50` with **no offset/cursor**, order by `graha` (or `vedha_kind, graha`), and are
   called by `now.ts` with no filter; `now.ts` then filters the returned page client-side for
   `is_current`. Measured on the canonical chart, as of the DB's CURRENT_DATE:

   | field | rows truly current | rows the 50-row page can reach | dropped |
   |---|---|---|---|
   | `kota_chakra` | 9 (one per graha) | 4 (Jupiter, Ketu, Mars, Mercury) | **Moon, Rahu, Saturn, Sun, Venus** |
   | `moorti_nirnaya` | 8 | 7 | Venus |
   | `vedha_gochara` | 1 (house_vedha) | **0** | the only active vedha |

   Saturn is currently in **durgantara** — the single most classically load-bearing Kota reading —
   and is structurally unreachable through the serving surface. Worse, `vedha_gochara` returns
   empty and `now.ts` then attaches the coverage sentence *"no vedha-checkable transit /
   sarvatobhadra-vedha dwelling is currently active … honest empty (the classically normal state
   on most days), not fabricated"* (`now.ts:2003-2008`). That sentence asserts a **classical
   absence** where the actual cause is **pagination**. There is no detector that could ever make
   it read false. This is precisely §N.8's defect class and §N.7 item 4/6.

5. **`kala_vedha_gochara`'s uncited sarvatobhadra rows silently suppress a production score.**
   `engine.py:160-172` (IR-6 / PK-R-9) *removed* the v1 `sarvatobhadra_vedha` primitive from the
   activity set on the stated grounds that it is unconditionally `uncited_extension=True` and that
   `bg_sarvatobhadra_grid` is empty by design — and that "a future admission ruling is required
   before an algorithmic-approximation primitive … should be trusted to move a served, bounded
   intensity score." The **W1.3 `quality_gates` path re-admits the same content through the back
   door**: `_fetch_vedha_rows` (`context.py:408-465`) selects `vedha_kind, graha, window_start,
   window_end, classical_citation, detail` and **does not select `uncited_extension`,
   `grid_basis`, or `grid_school_tag`**; a sarvatobhadra row carries no `malefic_count` in
   `detail`, so it falls to the `malefic_count == 0` branch and multiplies λ_v3 by
   `_VEDHA_ZERO_MALEFIC_FACTOR = 0.85`. Measured: 44 sarvatobhadra rows exist (24 on the canonical
   chart), every one `grid_basis='algorithmic_approximation'`, `uncited_extension=true`. The
   emitted `fired_vedha` detail carries `classical_citation` but no uncitedness flag — a caller
   cannot tell a Phaladeepika-grounded suppression from an approximation. The information is
   present in `vrow.detail` (`grid_basis`, `grid_school_tag`, `r19_disclosure` are all keys on
   every sarvatobhadra row — measured) and is read and dropped.

6. **The writers themselves are good.** All five are §N.3-conformant (delete-then-insert), all
   read L1/L0 verbatim (§N.5), all degrade honestly on a missing dependency with a named
   `WriterResult.notes` reason rather than a fabricated value. The `bg_sarvatobhadra_grid`-empty
   path (ADJUDICATION-11) is handled *correctly and disclosed*, not silently — see §ka_vedha_gochara
   item 3(d). Every defect in this batch is in the **serving plane, the consumer wiring, or the
   registry metadata**, not in a writer's arithmetic. That is a good problem to have.

7. **Registry metadata is uniformly empty and cheaply fixable.** All five:
   `integrity_check_sql = NULL`, `expected_volume_formula = NULL`, `expected_volume_inputs = NULL`,
   `volume_explanation = NULL`, `target_floor = 0`. `count_sql` is correct and chart-scoped on all
   five (verified against migration 562's re-assertions). Eight candidate non-count invariants were
   **executed against live data and all returned 0 violations** (see each asset's item 8) — they
   are real, they are cross-table, and none is a `count(*) = N` pin. This is directly reusable in W3.

8. **Freshness is unsignalled.** kota/moorti/vedha are `date.today()`-anchored rolling snapshots
   (`HORIZON_BACK_DAYS = 60`, `HORIZON_FORWARD_DAYS = 400`). Measured horizon on the canonical
   chart: **2026-06-14 … 2027-09-17**, built 2026-08-12/13. As of today, 82 of the 461 scanned days
   are already in the past. `now.ts` calls `buildKalaFreshness({ ephemerisVersion: null,
   sweepBuildDate: null, … })` — it passes literal nulls, so nothing tells a caller how old the
   scan is. `asset_throughput.state` is `stale` for kota/vedha on the canonical chart and `dormant`
   on the second chart (measured) — the cockpit knows; the served envelope does not.

---

## ka_kota_chakra

**One-line identity:** Per-graha occupancy of the four Kota-Chakra fort rings (stambha / durgantara
/ prakara / bahya), counted from the janma nakshatra, with entry/exit windows and a template
attack-vs-defence posture.

**Temporal question (D-TIME):** *"Right now — and across the scanned horizon — how deep inside the
native's fort is each graha, and is it attacking or defending?"*

### 1. Instrument fit
D-TIME (P6) primarily: it is a windowed state-of-the-sky-relative-to-this-native engine.
D-SALIENCE (P5) secondarily via `severity` (watch / elevated / high / acute). D-SERVICE (P8) is
where it fails — see item 6. It is the right instrument for a *siege-intensity* overlay on adverse
transit windows, which is exactly what `w25_kota_chakra` was written to consume; it is the wrong
instrument for a standalone answer, and it is not currently used as either.

### 2. Dependencies (declared vs real)
Declared: `{ga_positions, bg_ephemeris, bg_kota_chakra_rings}`. All three are real reads —
`chart_facts` MOON `longitude_sidereal` (`writer.py:_FETCH_JANMA_MOON_SQL`), `ephemeris_daily`
(`_FETCH_EPHEMERIS_RANGE_SQL`), `bg_kota_chakra_rings` (`_FETCH_RING_ASSIGNMENTS_SQL`, latest
`table_version`). **No undeclared read.** One undeclared *import*: `services.ka_graha_sancara.engine`
for `ALL_GRAHAS / NAKSHATRAS / NAK_SIZE_DEG` — a pure-constant import, not a data edge; no registry
change warranted. **Reverse edge is wrong:** `ka_gochara_v3_century_materialize` declares
`ka_kota_chakra` in `depends_on` but never reads `kala_kota_chakra` (batch summary 2/3).

### 3. Leverage / NULL check
No column is NULL (every column is `NOT NULL` by schema). The leverage loss is not NULL columns —
it is **rows that cannot be reached**:
- 588 rows on the canonical chart, 585 on the second (measured). **442 of 588 (75.2%) are Moon
  rows** — the Moon changes nakshatra ~daily, so it generates one run per day of the 461-day
  horizon. Signal-to-volume is poor and it is the Moon block that pushes the table past the
  serving page cap.
- **The designed consumer reads nothing.** `w25_kota_chakra.compute()` probes
  `context.kota_chakra_data / kota_rings / kota` — none exists on `ClassContext` — and returns
  `modifier=1.0` on 100% of calls. Its own registry YAML states the case against itself: *"v1 built
  kala_kota_chakra but never used it in lambda computation"*, `admission_state: candidate`,
  `ablation_evidence_link: null`, `admission_ruling_id: null`.
- **Latent vocabulary mismatch that would silently null the mechanism even after wiring.**
  `bg_kota_chakra_rings.ring_name` values are `stambha(4) / durgantara(8) / prakara(8) / bahya(7)`
  — measured, 27 total — and the `kala_kota_chakra_kota_ring_check` CHECK constraint pins exactly
  that vocabulary. `w25_kota_chakra.RING_MODIFIERS` keys are `stambha / **madhya** / **pragara** /
  bahya`, and `_determine_ring` rejects any ring not in `VALID_RINGS`. Wiring the mechanism as
  written would map durgantara and prakara — 697 of 1173 rows (59.4%), and Saturn's *current*
  ring — to `"none"` → `1.00`. The mechanism would report a clean unit modifier while silently
  discarding the majority of its input.

### 4. Grounding tier
Three-tier, and honestly separated already: the ring partition is `sruti`-adjacent but disclosed
tier-(iii) secondary transcription, carried per-row as `ring_table_citation` sourced from the L0
row (ADJUDICATION-9, no writer-local literal — a §N.7 item 3 pass); `count_from_janma` /
`kota_ring` / the run boundaries are `pratyaksa` (pure arithmetic over an L1 longitude and an L0
partition); `posture` / `severity` are `yukti` at best and the writer says so — `uncited_extension =
true` on 100% of rows, verbatim in the served payload. **This asset's labelling is correct as
built.** Recommend making the tier explicit rather than inferring it from `uncited_extension`.

### 5. Temporal identity + arbitration
Overlapping engines: `ka_graha_sancara` (the same daily sidereal series, same nakshatra index, same
`NAK_SIZE_DEG` floor — kota is a *relabelling* of sancara's nakshatra runs by distance from janma),
`ka_gochara_sweep`/`gochara_v3` (transit windows over the same ephemeris), `ka_moorti_nirnaya`
(same writer shape, sign-runs instead of nakshatra-runs, same horizon constants).
**Arbitration:** `ka_graha_sancara`'s nakshatra-run boundaries must be authoritative — kota derives
its runs from the identical primitive and must never disagree. Where kota's `severity` and
gochara_v3's λ disagree about how bad a window is, **gochara_v3 arbitrates**, because kota's
severity is an uncited template and λ is a bounded, calibratable score. Both single-ayanamsha
(`lahiri_chitrapaksha`) and both day-grade — no precision conflict. This is a clean, low-risk
Concordance Contract entry: *kota is a labelling overlay on sancara's nakshatra tiling; it never
originates a boundary.*

### 6. Service
Consumer: `query_kota_chakra` (`platform/src/lib/retrieval/registry/layers/L3_kala/`) →
`fetchKotaChakraNow` (`platform-mcp/src/tools/kala_views/now.ts:417`) → `kala_now_get.kota_chakra`,
plus a `coverage` entry and `provenance_envelope.kota_chakra_reachable`. It is **served but not
consulted**: nothing in `reading`, `reading_prose`, `windows`, `tri_plane` or any score reads it.
`density_contract`: **not declared** (no L3_kala capability declares one; L1_ganita capabilities do).
Drill to L1: 1 hop — `janma_nakshatra_fact_id` is on every row and is returned by the handler. ✅
**Page truncation:** measured, 4 of 9 current rings reachable (batch summary 4). `more_available:
true` is emitted honestly, but `MAX_LIMIT` is a hard cap (`Math.min(…, MAX_LIMIT)`) with no
offset/cursor parameter — a caller told "more available" has **no mechanism to fetch it**.

### 7. Measured cost
Build, declared: `estimated_seconds = 3`. Build, **measured** from `build_run_assets` where
`state='complete'` (n=3): mean **2.62 s**, min 2.11 s, max 3.16 s. `asset_throughput.rows_per_second`
is NULL and `measurement_count = 0` for all five assets — the throughput telemetry has never fired.
Historical failures on record: 3 `error` runs, all the same since-fixed `KeyError: 1` (DB9 dict_row
regression at `writer.py:126`), 3 `aborted`. Serve cost: unmeasured; two queries (page + COUNT),
both on the `(chart_id, ayanamsha_id, graha, window_start)` unique index, ≤50 rows returned.

### 8. Findings
- **F-KOTA-1 (MUST · D-SERVICE, §N.8)** — `kala_now_get.kota_chakra` structurally cannot serve
  Moon/Rahu/Saturn/Sun/Venus current rings: `now.ts` calls `query_kota_chakra` unfiltered, the
  handler hard-caps at 50 rows `ORDER BY graha, window_start`, and 588 rows exist. Measured: 4/9
  current rows reachable, Saturn-in-durgantara excluded. **Fix:** push the `as_of` currency filter
  into the SQL (`WHERE window_start <= as_of AND window_end >= as_of`) instead of filtering the
  page client-side — this also makes the query cheaper. Cost: ~10 lines in `query_kota_chakra.ts`,
  no writer change, no rebuild.
- **F-KOTA-2 (MUST · §N.8 earned signal)** — the `coverage` entry for `kota_chakra` cannot
  distinguish "not built" from "horizon does not cover as_of" from "truncated by the page cap".
  The third cause is currently the actual one and is not in the sentence. Fix alongside F-KOTA-1.
- **F-KOTA-3 (NOW · D-SERVICE)** — `w25_kota_chakra`'s ring vocabulary (`madhya`, `pragara`)
  contradicts the L0 table and the DB CHECK constraint (`durgantara`, `prakara`). 59.4% of rows,
  including Saturn's current ring, would map to `"none"` on the day the mechanism is wired. Fix in
  the mechanism module (L3-owned) before any admission ruling. Cost: 4 string literals + its test.
- **F-KOTA-4 (NOW · C12/D-126)** — `integrity_check_sql` is NULL. Proposed, **executed against live
  data, 0 violations**: (a) ring↔partition agreement —
  `SELECT count(*) FROM kala_kota_chakra k JOIN bg_kota_chakra_rings r ON r.ring_position =
  k.count_from_janma WHERE r.ring_name <> k.kota_ring` must be 0 (this is the real invariant: the
  served ring must equal what the L0 partition says for that count, §N.5); (b) per-graha run
  contiguity/tiling — `lead(window_start) OVER (PARTITION BY chart_id, graha ORDER BY window_start)
  = window_end + 1` for every non-terminal run, 0 gaps and 0 overlaps.
- **F-KOTA-5 (NOW · C12)** — `expected_volume_formula` is NULL. Derived from the writer:
  `rows = Σ_over 9 grahas (number of maximal same-nakshatra runs over
  [today − HORIZON_BACK_DAYS, today + HORIZON_FORWARD_DAYS])`, i.e.
  `≈ Σ_g ceil(H / (13.3333° ÷ mean_daily_motion_g)) + 1` with `H = 461`.
  `expected_volume_inputs = {horizon_days: 461, grahas: 9, nakshatra_arc_deg: 13.3333,
  mean_daily_motion_by_graha}`. Sanity-check against measurement: Moon at ~13.18°/day ⇒ ~1.01
  days/nakshatra ⇒ ~456 expected vs **442 measured** (retrograde-free bodies over-count slightly;
  the formula is an upper bound, which is the correct shape for a `target_floor` companion).
  `target_floor` should be set to the achieved 588 per §N.4, never fabricated upward.
- **F-KOTA-6 (NEVER-LATER · D-TIME)** — 75% of the table is Moon rows of ~1-day duration. A
  `graha <> 'Moon'` serving default (or a separate Moon-summary row) would make the table far more
  legible, but this is a shape preference, not a correctness defect; log it.
- **F-KOTA-7 (NEVER-LATER)** — `_INSERT_SQL` uses `ON CONFLICT … DO NOTHING` on the natural key
  immediately after a full per-chart DELETE. Correct today (runs are distinct by `window_start`),
  but the clause would mask a genuine duplicate-run bug rather than raise it. Log.

**Route recommendation (W2 input):** `changed` — the writer output is correct and re-derivable, but
the serving handler must change (F-KOTA-1/2) and the rolling horizon has already burned 82 of its
461 days, so a rebuild rides along.

---

## ka_moorti_nirnaya

**One-line identity:** The classical gold/silver/copper/iron (svarṇa/rajata/tāmra/loha) grade of each
transiting graha's stay in a sign, fixed by the Moon's nakshatra at the moment of that sign-ingress,
offset from the janma nakshatra.

**Temporal question (D-TIME):** *"For each sign-transit a graha is making, what quality of stay did
its moment of entry lock in — gold, silver, copper or iron?"*

### 1. Instrument fit
D-TIME (P6) + D-GROUNDING (P3): this is the most *cited* asset in the batch. The grade is not
computed — it is looked up verbatim from `bg_transit_moorti` (27 rows, measured) keyed by
`nakshatra_offset`, and the citation string travels with the row. It is the right instrument for a
transit-quality multiplier; `w22_moorti_nirnaya` exists precisely to be that multiplier.

### 2. Dependencies (declared vs real)
Declared `{ga_positions, bg_ephemeris, bg_transit_rules}`; all three read (`chart_facts` MOON,
`ephemeris_daily` for the 8 non-Moon grahas **plus Moon** — the Moon is fetched as the
ingress-nakshatra source, not as a subject — and `bg_transit_moorti`). No undeclared read. Note
`bg_transit_moorti` is reached via the `bg_transit_rules` asset id; the declared edge is correct at
asset granularity. **Reverse edge is wrong** (batch summary 3).

### 3. Leverage / NULL check
- **The eight moorti-derived columns are NULL on exactly 11.1% of rows (16 of 144; 8 per chart),
  and that is correct, not a defect.** `moorti_computed = false ⇔ start_truncated` — the sign-run
  began before the scanned horizon, so the ingress moment (and therefore the Moon's nakshatra at
  ingress) is genuinely unknown. The `kala_moorti_nirnaya_computed_consistency` CHECK enforces
  all-or-nothing population. This is a §N.7 item 6 pass: an honest NULL, DB-enforced.
- Grade distribution (measured, both charts): tamra 39, swarna 34, rajata 28, loha 27, NULL 16.
- **The designed consumer reads nothing.** `w22_moorti_nirnaya._find_overlapping_moorti` reads
  `getattr(context, "moorti_rows", None)`; `ClassContext` has no such field; the function returns
  `None` and `compute()` returns `modifier=1.0` unconditionally in production. Its own docstring
  concedes it: *"Currently kala_moorti_nirnaya data is NOT plumbed into ClassContext (that is Wave
  4 wiring work)."* The four multipliers it defines (1.25 / 1.10 / 0.90 / 0.75) have never moved a
  served number.
- Romanisation: the DB stores `swarna`; the mechanism normalises `swarna → svarna`. Handled.

### 4. Grounding tier
`sruti` for the grade itself — Phaladeepika Ch.27 / BPHS Ch.28 via `bg_transit_moorti`, carried
per-row as `moorti_classical_citation`, never re-derived (§N.5 pass). `pratyaksa` for the sign-run
boundaries and `nakshatra_offset` arithmetic. No `yukti` layer and none needed. **The cleanest
grounding story of the five** — and note the contrast with kota: this asset sets
`uncited_extension` nowhere because it has no synthesis of its own. Correct.

### 5. Temporal identity + arbitration
Overlapping engines: `ka_graha_sancara` (sign-ingress boundaries — the identical primitive),
`ka_kota_chakra` (same horizon, same writer shape, nakshatra-runs vs sign-runs), `gochara_v3`
(sign-transit windows), `ga_tajaka` (annual quality, different axis).
**Arbitration:** sign-ingress instants are `ka_graha_sancara`'s to own; moorti must inherit them,
never re-derive. Where moorti's grade and gochara_v3's valence disagree about whether a transit is
good, **they are not in conflict** — moorti grades the *stay* (fixed at ingress, constant for the
whole run), λ_v3 grades the *moment*. That distinction belongs in the Concordance Contract
explicitly, because a reader will otherwise treat a `loha` stay as contradicting a high-λ window.

### 6. Service
Same shape as kota: `query_moorti_nirnaya` → `fetchMoortiNirnayaNow` → `kala_now_get.moorti_nirnaya`
(a passive field) + coverage + `moorti_nirnaya_reachable`. No `density_contract`. Drill to L1: 1 hop
via `janma_nakshatra_fact_id`. **Page truncation measured:** 72 rows/chart vs `MAX_LIMIT = 50`,
`ORDER BY graha, window_start` ⇒ the page reaches Jupiter…Sun and drops Venus; 7 of 8 current rows
served. Less severe than kota, same root cause, same fix.

### 7. Measured cost
Declared `estimated_seconds = 3`; **measured** (`state='complete'`, n=4): mean **2.56 s**, min
1.26 s, max 4.51 s. 3 `error` runs on record, same since-fixed DB9 `KeyError: 1`
(`ka_moorti_nirnaya/writer.py:171`). `rows_per_second` NULL, `measurement_count = 0`. Serve cost
unmeasured; ≤50 rows, indexed.

### 8. Findings
- **F-MOORTI-1 (MUST · D-SERVICE)** — same page-truncation class as F-KOTA-1: 72 rows/chart, 50-row
  hard cap, no cursor; Venus's current moorti is unreachable at `kala_now_get`. Fix identically —
  push the currency predicate into SQL. Cost: ~10 lines, no rebuild required for the fix itself.
- **F-MOORTI-2 (NOW · D-SERVICE, "built-but-unplugged")** — `kala_moorti_nirnaya` has **zero**
  consumers that change an output. Two dispositions, and W2 should pick one explicitly rather than
  leave it implicit: **(a) WIRE** — add `moorti_rows` to `ClassContext.fetch()` (one savepointed
  SELECT alongside the existing `_fetch_vedha_rows`, ~30 lines in `context.py`) and admit
  `w22_moorti_nirnaya` through the existing ablation path (`scripts/kala_admission/w44_weight_fitting.py`
  already lists it); estimated ~1 day including ablation evidence, and it is the only one of the four
  dormant mechanisms whose data is *cited* rather than approximated, so it is the highest-value
  wire. **(b) RECORD** — leave it as a served-but-inert overlay and say so in the registry
  (`data_disposition`), so no future audit re-discovers it as a defect. **Recommend (a).**
- **F-MOORTI-3 (NOW · C12/D-126)** — `integrity_check_sql` NULL. Proposed, **executed, 0
  violations**: (a) grade fidelity to L0 —
  `SELECT count(*) FROM kala_moorti_nirnaya m JOIN bg_transit_moorti b USING (nakshatra_offset)
  WHERE m.moorti_computed AND (m.moorti_name <> b.moorti_name OR m.quality_tier <> b.quality_tier)`
  must be 0 (the §N.5 "L0 is the authority" invariant, and the one a future writer refactor would
  most plausibly break); (b) per-graha sign-run tiling contiguity, `lead(window_start) = window_end
  + 1`, 0 gaps.
- **F-MOORTI-4 (NOW · C12)** — `expected_volume_formula` NULL. Derived:
  `rows = Σ_over 8 grahas (maximal same-sign runs over the 461-day horizon)`
  `≈ Σ_g ceil(H / (30° ÷ mean_daily_motion_g)) + 1`. Inputs:
  `{horizon_days: 461, grahas: 8 (all except Moon), sign_arc_deg: 30, mean_daily_motion_by_graha}`.
  Measured 72/chart, distributed Mercury 20 / Venus 17 / Sun 16 / Mars 9 / Jupiter 4 / Rahu 2 /
  Ketu 2 / Saturn 2 — matches the inverse-of-mean-motion shape. `target_floor` → 72 (achieved).
  Companion invariant worth pinning as a second `integrity_check_sql` clause: the count of
  `moorti_computed = false` rows should equal the count of `start_truncated = true` rows (measured:
  16 = 16), which is the writer's own stated rule made checkable.
- **F-MOORTI-5 (NEVER-LATER · D-GROUNDING)** — `quality_tier` (1..4) and `moorti_name` are
  redundant encodings of the same L0 fact; harmless, but a consumer could grade off one and cite
  the other. Log.

**Route recommendation (W2 input):** `changed` — serving fix (F-MOORTI-1) plus an explicit
wire-or-record disposition (F-MOORTI-2); writer arithmetic verified, rebuild only to roll the
horizon.

---

## ka_vedha_gochara

**One-line identity:** Three classical obstruction mechanisms — `house_vedha` (BPHS Ch.29 /
Phaladeepika Ch.26, cited), `latta` (Phaladeepika PG338-339, cited) and `sarvatobhadra`
(nakshatra-level, **algorithmic approximation**, disclosed) — applied to the chart's active and
forward transits.

**Temporal question (D-TIME):** *"Which of this chart's currently-active transit promises are being
obstructed right now, by which graha, and how badly?"*

### 1. Instrument fit
D-TIME (P6) + D-SALIENCE (P5) + **the only D-SERVICE (P8) success in the batch**. This is the
suppression side of the transit story, and unlike its four batch-mates it is genuinely wired: it is
the `quality_gates` factor of the production λ_v3 formula. It is also the batch's D-GROUNDING (P3)
stress case, because two of its three mechanisms are cited and one is not — and the consumer cannot
currently tell them apart (item 3).

### 2. Dependencies (declared vs real)
Declared: `{ga_positions, bg_ephemeris, bg_transit_rules, bg_sarvatobhadra_grid,
bg_vedha_malefic_scale, bg_phaladeepika_latta}` — six, the richest in the batch, and **all six are
really read** (verified in `writer.py`: `_FETCH_JANMA_*`, `_fetch_daily_sidereal_by_body`,
`_fetch_vedha_rules`, `_fetch_school_tagged_vedha_pair`, `_fetch_malefic_scale`,
`_fetch_latta_rules`). Measured L0 state: `bg_transit_rules` populated, `bg_vedha_malefic_scale` = 5
rows, `bg_phaladeepika_latta` = 8 rows, **`bg_sarvatobhadra_grid` = 0 rows** (deliberately empty,
ADJUDICATION-11). One **undeclared read attempt**: `_vedha_pairs_from_db`
(`services/gochara_grammar/sarvatobhadra.py:95`) queries `l1_sarvatobhadra_vedha` — **that relation
does not exist in the database** (measured: `ERROR: relation "l1_sarvatobhadra_vedha" does not
exist`). It is caught and savepointed (DB9c), so it is a dead fallback, not a live edge; it should
not be added to `depends_on`, it should be noted as vestigial.
**Reverse edge is correct here:** `ka_gochara_v3_century_materialize → ka_vedha_gochara` is the one
real new edge migration 562 added.

### 3. Leverage / NULL check
- 176 rows on the canonical chart, 178 on the second. Kind split (canonical): `house_vedha` 132,
  `sarvatobhadra` 24, `latta` 20. Mean window: house_vedha 10.5 d, sarvatobhadra 3.0 d, latta 1.6 d.
- **`grid_school_tag` is 100% NULL** (44/44 sarvatobhadra rows across both charts) — correct and
  forced: `bg_sarvatobhadra_grid` is empty, so `grid_basis = 'algorithmic_approximation'` and the
  `kala_vedha_gochara_grid_fields_scope` CHECK permits a NULL tag only in that state. The column is
  a *ready socket*, not dead weight; it activates with zero code change if a school's grid is ever
  ingested.
- **The leverage failure is on the consumer side and it is the batch's second-worst finding.**
  `_fetch_vedha_rows` (`context.py:425-433`) selects six columns and **omits `uncited_extension`,
  `grid_basis`, `grid_school_tag`**. `_compute_quality_gates_from_context` then treats a
  sarvatobhadra row exactly like a cited one: `detail.get("malefic_count", 0)` → 0 →
  `_VEDHA_ZERO_MALEFIC_FACTOR = 0.85` → `product *= 0.85`. The emitted `fired_vedha` entry carries
  `classical_citation` and `scale_citation` but **no uncitedness signal**. Every ingredient needed
  to fix this is already inside `vrow.detail` — measured, all 44 sarvatobhadra rows carry
  `grid_basis`, `grid_school_tag` and `r19_disclosure` as JSONB keys. It is read and dropped.
  This directly contradicts `engine.py:160-172`'s own stated IR-6 rule that an
  algorithmic-approximation primitive with no populated corpus must not move a served bounded score
  without an admission ruling.
- Today's actual modulation is small but real: 1 of 176 rows (a `house_vedha`) overlaps the current
  date, so today's `quality_gates ≈ 0.85` rather than 1.0 — a measurable ~15% suppression of λ_v3.

### 3(d). What happens when `bg_sarvatobhadra_grid` is empty — the §N.8 question, answered
**The writer behaves correctly and does not emit a confident result over an empty source.** The
resolution order is: (1) `bg_sarvatobhadra_grid` (`_fetch_school_tagged_vedha_pair`) → returns None
because the table is empty; (2) `l1_sarvatobhadra_vedha` via `_vedha_pairs_from_db` → returns None
because the relation does not exist, inside an explicit `SAVEPOINT _vedha_db_probe` added by the
DB9c fix specifically so the aborted transaction does not silently kill the writer's subsequent
DELETE; (3) `opposite_nakshatra_id` — the 14-positions-away algorithmic approximation. The writer
then sets `grid_basis = 'algorithmic_approximation'`, `grid_school_tag = NULL`,
`uncited_extension = True`, and writes an `r19_disclosure` sentence into `detail`. A DB CHECK
enforces the basis/tag scoping, and a second (verified) invariant holds: `uncited_extension =
(grid_basis = 'algorithmic_approximation')` on 44/44 rows. **It produces fewer, honestly-labelled
rows — not a wrong or silently-degraded result.** The §N.8 defect is one layer downstream: the
label the writer worked to attach is dropped by the only consumer that acts on the row.

### 4. Grounding tier
Genuinely mixed and already machine-separable — the best-instrumented grounding in the batch.
`house_vedha` (132 rows): `sruti`, `uncited_extension = false`, real `classical_citation`.
`latta` (20 rows): `sruti`, `uncited_extension = false`, Phaladeepika PG338-339; Ketu deliberately
absent from `bg_phaladeepika_latta` and therefore absent from the output by construction — a
disclosed classical gap, not a bug. `sarvatobhadra` (24 rows): `pratyaksa`/`yukti` at best,
`uncited_extension = true`, `grid_basis = 'algorithmic_approximation'`. **An honest `pratyaksa` here
is success**, and the write path already treats it as such. Recommend the Concordance Contract
adopt this asset's three-way split as the reference pattern for the layer.

### 5. Temporal identity + arbitration
Overlapping engines: `gochara_v3`/`engine.py` (consumes it — not a peer), the retired v1
`vedha_cancellation` / `sarvatobhadra_vedha` / `kartari_pincer` suppression trio (superseded, per
`engine.py:756-760`), `gochara_vedha_pair` (still an activity primitive reading `bg_transit_rules`
directly — the *same L0 rules* this writer reads, on a different axis), `ka_gochara_sweep` v1
windows.
**Arbitration — and this is the sharpest arbitration question in the batch:** `gochara_vedha_pair`
(activity, from `bg_transit_rules` at query time) and `kala_vedha_gochara.house_vedha`
(suppression, from `bg_transit_rules` at build time) are two readings of one L0 rule set that can
disagree if the writer's horizon is stale while the query-time primitive is live. **The
build-time table must not arbitrate over live L0**: where they disagree, `bg_transit_rules` +
current ephemeris wins, and `kala_vedha_gochara` should be treated as a cache with a declared
staleness bound (see F-VEDHA-4). Within the suppression path itself, `latta` short-circuits the
`malefic_count` branch by design (`_LATTA_EFFECTIVE_MALEFIC_COUNT = 3`, an explicit structural
prior) — that precedence is correct and should be written into the Contract, not left in a comment.

### 6. Service
**Two consumers, one real.** (a) **Real:** `gochara_v3` λ_v3 `quality_gates` — a genuine
score-modulating consumption, the only one in this batch. (b) **Passive:** `query_vedha_gochara` →
`fetchVedhaGocharaNow` → `kala_now_get.vedha_gochara`. No `density_contract`. Drill to L1: 1 hop via
`janma_reference_fact_id`. **Page truncation is worst here and produces a false claim:** 176
rows/chart, 50-row cap, `ORDER BY vedha_kind, graha, window_start` ⇒ the page never leaves
`house_vedha`, and **0 of the 1 currently-active vedha rows survive** to `kala_now_get`, which then
emits the "no vedha … is currently active — honest empty (the classically normal state on most
days)" coverage sentence. That sentence is not merely uninformative; **it is false today, and no
code path exists that could make it read false correctly.**

### 7. Measured cost
Declared `estimated_seconds = 4`; **measured** (`state='complete'`, n=3): mean **3.12 s**, min
2.83 s, max 3.36 s — the most expensive of the five, consistent with six dependency reads and three
mechanisms. 1 `error`, 4 `queued`, 3 `aborted` on record. `rows_per_second` NULL,
`measurement_count = 0`. Serve cost: on the λ path it is a single pre-fetch per `ClassContext`
(zero per-JD DB access by design) — architecturally cheap; unmeasured in wall-clock.

### 8. Findings
- **F-VEDHA-1 (MUST · §N.8 earned signal, §N.7 item 4)** — `kala_now_get.vedha_gochara` serves an
  empty array with a coverage sentence claiming classical absence, while a `house_vedha` row is in
  fact active (measured: 1 current row, 0 reachable within the 50-row page). Fix: push the currency
  predicate into `query_vedha_gochara`'s SQL, and make the coverage sentence distinguish
  not-built / horizon-miss / truncated / genuinely-none — the last of which is only assertable once
  the query is currency-scoped. Cost: ~15 lines across two files, no writer change.
- **F-VEDHA-2 (MUST · D-GROUNDING, §N.6, and `engine.py`'s own IR-6 rule)** — an
  `uncited_extension = true`, `grid_basis = 'algorithmic_approximation'` sarvatobhadra row
  multiplies the served λ_v3 by 0.85 and the emitted `fired_vedha` detail gives the caller no way
  to know. **Minimum fix (L3-owned, small):** add `grid_basis` (or read it from the already-present
  `vrow.detail`) to `fired_vedha` and to `quality_gates_detail`, and count uncited suppressors
  separately — the §N.6 "never present catalog matches as confirmed findings" discipline applied to
  suppression. **The stronger question — should an approximation be permitted to move λ_v3 at all,
  given IR-6 explicitly said no for the same content on the activity side — is an admission ruling,
  not a code change**; W2 should route it as such rather than let the code settle it by default.
  Measured blast radius: 24 of 176 rows on the canonical chart (13.6%).
- **F-VEDHA-3 (NOW · C12/D-126)** — `integrity_check_sql` NULL. Proposed, **all executed, 0
  violations**: (a) grounding-flag coherence — `count(*) WHERE vedha_kind='sarvatobhadra' AND
  uncited_extension <> (grid_basis = 'algorithmic_approximation')` must be 0 (this is the
  §N.7-item-4 detector for the honesty label itself, and it is the invariant a future grid ingest
  is most likely to break); (b) latta well-formedness — every `latta` row must be a janma-nakshatra
  hit: `count(*) WHERE vedha_kind='latta' AND detail->>'latta_nakshatra_idx' IS DISTINCT FROM
  detail->>'janma_nakshatra_idx'` must be 0 (this is the writer's *stated* construction rule, which
  `engine.py`'s latta short-circuit silently depends on — if it ever breaks, λ_v3 mis-suppresses);
  (c) kind-vocabulary closure is already a DB CHECK, do not duplicate it.
- **F-VEDHA-4 (NOW · D-TIME)** — the asset is a `date.today()`-anchored cache consumed by a live
  scoring path, with no staleness bound. `ClassContext` reads whatever `kala_vedha_gochara` last
  contained; if the build is months old, λ_v3's suppression term is computed against an expired
  horizon and nothing says so. Propose: carry the build's `horizon_end` (or `max(window_end)`) into
  `quality_gates_detail` and flag when the evaluation JD lies outside it. Cost: ~10 lines in
  `context.py` + `engine.py`.
- **F-VEDHA-5 (NOW · C12)** — `expected_volume_formula` NULL. Derived (three additive terms, which
  is why this one is genuinely useful rather than cosmetic):
  `rows = house_vedha + sarvatobhadra + latta`, where
  `house_vedha ≈ Σ_g (sign-runs of g over H) × (vedha-checkable rules matching g's primary_house)`,
  `sarvatobhadra ≈ Σ_g (nakshatra-dwellings of g over H that hit the vedha-paired nakshatra)`,
  `latta ≈ Σ_{g ∈ bg_phaladeepika_latta} (janma-nakshatra latta hits over H)`. Inputs:
  `{horizon_days: 461, grahas: 9, bg_transit_rules vedha-checkable row count,
  bg_phaladeepika_latta rows: 8, nakshatra_arc_deg: 13.3333}`. `target_floor` → 176 (achieved,
  §N.4).
- **F-VEDHA-6 (NEVER-LATER)** — `_vedha_pairs_from_db` targets `l1_sarvatobhadra_vedha`, a relation
  that does not exist. Harmless (savepointed, honest-None) but it costs a round-trip per nakshatra
  probe per build and misleads a reader into thinking a second corpus path is live. Log for removal
  or for a real table. **Hand-off note:** the fix touches `services/gochara_grammar/`, shared with
  the v1 grammar — confirm ownership before editing.

**Route recommendation (W2 input):** `changed` — this is the batch's highest-value asset (the only
consumed one) and carries its two most serious findings; the write path is verified correct, the
consumer and serving handler both need change, and the admission question in F-VEDHA-2 needs a
ruling rather than a patch.

---

## ka_sudarshana_varsha

**One-line identity:** The rotating annual house-per-year progression of the tri-lagna framework
(Janma / Chandra / Sūrya Lagna), one row per year of a 120-year lifespan, pure calendar arithmetic
over three natal sign facts.

**Temporal question (D-TIME):** *"In the native's Nth year of life, which sign does each of the
three reference lagnas occupy on the rotating year-wheel?"*

### 1. Instrument fit
D-TIME (P6) only, and at the coarsest possible grain: one row per year of life, no ephemeris, no
sub-period. It is a legitimate classical scaffold, but as built it answers a question no served
surface asks. **It is the purest shelf-inventory case in the batch** — and unlike moorti and kota it
does not even have a written-but-dormant consumer that reads its actual table (`w27c_sudarshana`'s
registry YAML names its data source as *"kala_sudarshana / bo_sudarshana"* — `kala_sudarshana` is
not a table in this database; the real table is `kala_sudarshana_varsha`, and `bo_sudarshana` is the
explicitly-disclaimed L2 namesake). The dormant consumer is pointed at the wrong name.

### 2. Dependencies (declared vs real)
Declared `{ga_positions}` — correct and complete. Real reads: three `chart_facts` sign facts
(Lagna / Moon / Sun), each carried back as `lagna_fact_id` / `moon_fact_id` / `sun_fact_id` on every
row (§N.5 pass, and the best drill-to-L1 provenance in the batch — three fact ids per row). No
ephemeris, no L0. **No undeclared read; no declared-but-unread edge.** The only asset in the batch
whose dependency declaration is exactly right in both directions.

### 3. Leverage / NULL check
- 120 rows for the canonical chart. **Zero rows for the second chart (`1c826d5a`)** — measured, and
  `asset_throughput` has no row for that chart at all, versus the other four assets which all have
  build history on both. The asset has simply never been dispatched for Abhinandan. All four
  siblings ran on both charts.
- No NULL columns (every column `NOT NULL`).
- **`tri_lagna_convergence` is FALSE on 120 of 120 rows — and it is mathematically incapable of
  being anything else for this chart, or for almost any chart.** `compute_tri_lagna_year`
  (`logic.py:100-118`) advances all three reference signs by the *same* offset,
  `active_house_offset(varsha_year) = (varsha_year − 1) % 12`, and then flags `jl == cl == sl`.
  Since the offset is identical for all three, `jl == cl == sl` holds **iff the three natal signs
  are equal** — a chart-level property, constant across all 120 years. For this native (Lagna
  Aries, Moon in Purva Bhādrapadā, Sun Capricorn) it is false in every year, and no rebuild will
  ever change that. The docstring calls it *"a classically notable alignment year"*; it is not a
  year-level quantity at all. This is a per-row flag carrying exactly zero per-row information,
  served through `query_sudarshana_varsha` and re-emitted on `kala_now_get.sudarshana_varsha` — a
  §N.8 signal with no detector that could distinguish the years it claims to distinguish.
- **No consumer of any kind changes an output.** `w27c_sudarshana` reads
  `context.sudarshana_rows`, which does not exist on `ClassContext`; it returns `1.0` always. Its
  12-house modifier schedule (0.75–1.30) has never been applied.

### 4. Grounding tier
`yukti` — the tri-lagna year-wheel is a real Parāśarī framework, but the writer implements only the
rotating wheel and explicitly scopes out the 10-year primary / yearly secondary sub-dasha structure
(`logic.py:25-35`, an honest disclosure). The arithmetic itself is `pratyaksa`. There is no
`classical_citation` column on this table at all — the one asset in the batch that carries no
citation field, which is defensible for pure arithmetic but leaves the `yukti` scoping claim
undischargeable at serve time. Recommend an explicit `pratyaksa`+scope-note label rather than
inventing a citation.

### 5. Temporal identity + arbitration
Overlapping engines: `ka_jivana_parva` (life-arc partitioning over the same 120-year span),
`ka_tithi_pravesha` (also 120 annual rows, also birthday-anchored — **the two tile the same
lifetime on nearly the same boundaries**), `ga_tajaka` (varṣaphala year-lord, same annual axis),
`bo_sudarshana` (L2, same classical name, static, non-temporal — a confirmed namesake-only
collision, correctly ruled on and not to be revisited).
**Arbitration:** this asset uses a **day-grade calendar anniversary** window
(`birth_date + relativedelta(years=N−1)`, explicitly *not* a solar-return instant — `logic.py:42-47`),
whereas `ka_tithi_pravesha` uses a **real ephemeris root-find instant**. They will disagree about
where year N begins by up to ~a fortnight. **`ka_tithi_pravesha` must arbitrate the annual boundary**
— it is the instrument that actually computes one; `ka_sudarshana_varsha`'s window is a labelling
convenience and should be documented as such in the Concordance Contract, not treated as a
competing answer. This is the single most concrete boundary-disagreement pair in the batch and
belongs in the Contract verbatim.

### 6. Service
`query_sudarshana_varsha` → `fetchSudarshanaVarshaNow` → `kala_now_get.sudarshana_varsha` (the
current year's row only) + coverage + reachable flag. **No other consumer anywhere** (verified by
repo-wide grep: only the writer, the migration, the seed, the handler, `now.ts`, and tests).
`MAX_LIMIT = 120` — correctly sized to the full lifespan, so **this asset has no truncation defect**;
the handler comment says as much and is right. No `density_contract`. Drill to L1: 1 hop, three
fact ids. Minor: the handler hardcodes `LIMIT $5` rather than deriving the placeholder index; it is
correct today because the filter list is fixed, but it is brittle if a filter is ever added.

### 7. Measured cost
Declared `estimated_seconds = 2` — the cheapest declared. **Measured** (`state='complete'`, n=3):
mean **2.09 s**, min 1.89 s, max 2.42 s. No `error` runs on record (the only asset in the batch that
has never failed); 3 `aborted`. `rows_per_second` NULL, `measurement_count = 0`. Serve cost:
unmeasured, 120 rows, single indexed scan. Rebuild is nearly free and has no horizon dependency —
the rows are birth-anchored, not `today()`-anchored, so unlike kota/moorti/vedha **this asset never
goes stale**.

### 8. Findings
- **F-SUD-1 (MUST · §N.8 earned signal, §N.7 item 6)** — `tri_lagna_convergence` is a per-row
  boolean that is provably constant per chart (all three lagnas share one offset), measured false on
  120/120 rows, and is served as if it marked notable years. Either (a) drop the column from the
  served projection and record why, or (b) redefine it to the quantity the technique actually wants
  — e.g. pairwise convergence (`jl == cl`, `cl == sl`, `jl == sl`), which *is* year-invariant too
  and therefore equally degenerate, so more likely (c) replace it with the genuinely year-varying
  quantity: which *house from each natal lagna* the wheel has reached. **Recommend (a) now, (c) as
  the real fix.** Leaving a flag that cannot vary is exactly the "signal with no detector behind
  it" §N.8 forbids.
- **F-SUD-2 (MUST · build coverage)** — the asset has never been built for chart `1c826d5a`
  (0 rows, no `asset_throughput` row), while all four batch siblings have. Any cross-chart claim
  about L3 coverage is currently false for this asset. Fix: dispatch the writer for the second
  chart — measured cost ~2.1 s, zero risk (pure arithmetic, delete-then-insert, no ephemeris).
- **F-SUD-3 (NOW · D-SERVICE, "built-but-unplugged")** — zero consumers modulate anything, and the
  one dormant candidate (`w27c_sudarshana`) names a non-existent table (`kala_sudarshana`) as its
  data source. Of the four unplugged assets this is the **weakest wire candidate** (coarsest grain,
  weakest grounding, no citation column) — recommend a **recorded disposition** (`data_disposition`
  on `asset_registry`, stating "served as annual-context reference; not admitted to any scoring
  path") rather than a wire, and fix the YAML's `data_source` string so the next auditor is not
  misled. Cost: one registry UPDATE + one YAML line.
- **F-SUD-4 (NOW · C12/D-126)** — `integrity_check_sql` NULL. Proposed, **executed, 0 violations**:
  (a) lifespan tiling with no gaps or overlaps —
  `lead(window_start) OVER (PARTITION BY chart_id ORDER BY varsha_year) = window_end` for all 119
  non-terminal rows; (b) progression fidelity —
  `count(*) WHERE jl_active_sign_idx <> (jl_natal_sign_idx + (varsha_year − 1)) % 12` (and the same
  for `cl`/`sl`) must be 0, which pins the technique's defining arithmetic rather than a row count.
- **F-SUD-5 (NOW · C12)** — `expected_volume_formula` NULL. Derived and **exact**, not approximate:
  `rows = DEFAULT_MAX_VARSHA_YEAR = 120` per (chart × ayanamsha), with
  `expected_volume_inputs = {max_varsha_year: 120, ayanamshas: 1}`. Note for W3: this is a
  *derived* constant (it reads the writer's own horizon constant), not a `count(*) = 120` pin — the
  distinction C12/D-126 draws. `target_floor` → 120 (achieved).
- **F-SUD-6 (NEVER-LATER)** — the sub-dasha structure is scoped out and disclosed; log as a
  documented completeness gap, not a defect.

**Route recommendation (W2 input):** `changed` — F-SUD-1 changes what is served and F-SUD-2 requires
a first build on the second chart; the arithmetic is verified correct and needs no rework.

---

## ka_tithi_pravesha

**One-line identity:** The lunar-return annual chart — for each of 120 years, the exact instant the
transiting Moon returns to its natal sidereal longitude nearest that year's solar-birthday
anniversary, plus the full annual chart cast at that instant (Praveśa Lagna + all nine graha
positions).

**Temporal question (D-TIME):** *"At what exact instant does the native's Nth lunar year begin, and
what chart is standing at that instant?"*

### 1. Instrument fit
D-TIME (P6) at the highest precision in the batch — the only one of the five that performs a real
Swiss-Ephemeris root-find rather than reading a daily grid — plus D-GROUNDING (P3) via a genuine
two-pass verification. It is the correct instrument for annual-chart anchoring and it is
well-built. Its problem is entirely that nothing downstream anchors to it.

### 2. Dependencies (declared vs real)
Declared `{ga_positions}`. Real reads: the natal MOON `longitude_sidereal` fact from `chart_facts`
(carried back as `moon_fact_id`) — read verbatim, never re-derived (§N.5 pass). Everything else
comes from `ctx.config['birth_params']` (FROZEN-contract input) and the `pyjhora_adapter` ephemeris
engine — a *compute* dependency, not a table read, correctly absent from `depends_on`. **No
undeclared read.** **Reverse edge is wrong:** migration 562 declares
`ka_gochara_v3_century_materialize → ka_tithi_pravesha` on the stated basis that it "reads pre-built
rows via ClassContext" — `ClassContext` has no `tithi_pravesha_rows` field (batch summary 2/3).

### 3. Leverage / NULL check
- 120 rows per chart, **both charts built** (240 total, measured).
- **`verification_pass_status = 'two_pass_verified'` on 240/240 rows, and — uniquely in this batch —
  it has a real detector behind it.** `_compute_one_year` (`writer.py:196-210`) computes the annual
  chart's Moon longitude through the *full independent position pipeline* and compares it to the
  root-find target: `cross_check_diff = abs(ang_diff(annual_moon_long, natal_moon_long))`; the
  status is `two_pass_verified` only if `audit["converged"] AND cross_check_diff <=
  LUNAR_RETURN_TOL_DEG`, else `divergent_flagged`. A DB CHECK pins the vocabulary to exactly those
  two values, the writer counts divergences into `WriterResult.notes`, and the raw diff is stored in
  `ephemeris_audit_jsonb.annual_chart_moon_cross_check_diff_deg`. **This is what §N.8 asks for and
  the batch's one unambiguous earned signal.** 240/240 passing is a real result, not a broadcast.
- `pravesha_lagna_sign_idx` / `_name` / `_degree`: 0 NULL. `start_converged` / `end_converged`:
  0 false. `graha_positions_jsonb`: JSON array on 240/240, minimum length 9 — no empty payloads.
- **No consumer modulates anything.** `w27b_tithi_pravesha` reads `context.tithi_pravesha_rows`
  (absent from `ClassContext`) → `modifier = 1.0` always. The only non-serving code that touches
  the table is `scripts/backfill/drain_prohibited_verification_status.py`, which reads its CHECK
  constraint for a guard and writes nothing to it.

### 3(e). Cross-layer hand-off fact for L4 — the Discovery's D-7
**Verified negative: no L4 `ph_*` writer reads `kala_tithi_pravesha` or `kala_sudarshana_varsha`.**
A repo-wide grep across `platform/python-sidecar/services/ph_*` and
`pipeline/orchestrator/writers/ph_*.py` for both table names, for `tithi_pravesha`/`sudarshana_varsha`
as substrings, and for `varsha`/`varshaphal` returned **zero matches**. The complete consumer set for
`kala_tithi_pravesha` is: the writer, migrations 531/532/557/562, `asset_registry_seed.ts`,
`query_tithi_pravesha.ts`, `kala_views/now.ts`, the dormant `w27_annual_stack`, the
`kala_admission` weight-fitting scripts, the drain script's guard, and tests. **D-7's claim —
"varshaphala/tithi-praveśa consumption into anchors proven" — is not satisfied by
`ka_tithi_pravesha`.** If L4 anchors consume varshaphala at all, they do so through the L1 Tājaka
path (`ga_tajaka` / `l1_tajik_varsha_year_lords`), not through this L3 asset. **This is an L4
hand-off, not an L3 NOW item** — the fix, if D-7 is to be satisfied as written, belongs to the
`ph_*` write set, which L3 must not touch.

### 4. Grounding tier
`pratyaksa` — and this is the honest and correct label, per the rubric's own note that purely
computational ephemeris output should be `pratyaksa` and needs no classical claim. The praveśa
*instant* is instrument-emergent (a root-find), not verse-direct. `classical_source_citation` is
populated on every row for the *technique's* provenance (the Tājaka/Kṛṣṇa-Miśra lunar-return
framework) — correctly scoped to the method, not to the number. No `uncited_extension` column and
none needed. **Recommend `pratyaksa` explicitly; do not reach for `sruti` on a root-find.**

### 5. Temporal identity + arbitration
Overlapping engines — this is the batch's densest arbitration node: `ga_tajaka` (solar-return
varṣaphala, the *same* annual axis via the *same* `pyjhora_adapter` engine, but Sun-anchored rather
than Moon-anchored), `ka_sudarshana_varsha` (120 birthday-anchored calendar rows over the identical
lifespan), `ka_jivana_parva` (life-arc partitions), `ka_avadhi`/dasha engines (a different periodicity
entirely).
**Arbitration:** `ga_tajaka` and `ka_tithi_pravesha` are **not** competitors — solar return and lunar
return are two distinct annual charts and both are classically valid; the Contract must say so
explicitly, because a reader seeing two different "year begins" instants will otherwise read a
contradiction where there is a deliberate distinction. Against `ka_sudarshana_varsha`, however,
there **is** a genuine boundary conflict (calendar anniversary vs computed instant, differing by up
to ~a fortnight) and **`ka_tithi_pravesha` arbitrates** — it is the only one of the two that
computes a boundary rather than assuming one. Where the praveśa instant and any dasha boundary
disagree, neither arbitrates: they are different periodicities and the Contract should forbid
resolving one against the other.

### 6. Service
`query_tithi_pravesha` → `fetchTithiPraveshaNow` → `kala_now_get.tithi_pravesha` (current year's row
only) + coverage + reachable flag. No other consumer. **No truncation defect** — `MAX_LIMIT = 120`
matches the exact row count, and `ORDER BY pravesha_year` is total. No `density_contract`. Drill to
L1: 1 hop via `moon_fact_id`. The coverage message correctly names both honest-empty causes
(pre-birth `as_of`, beyond the 120-year horizon). **This asset's serving surface is the batch's
cleanest**; its gap is consumption, not presentation.

### 7. Measured cost
Declared `estimated_seconds = 3`; **measured** (`state='complete'`, n=4): mean **2.20 s**, min
1.83 s, max 2.43 s — for 120 root-finds plus 120 full chart casts, which matches the writer's own
documented ~3.4 ms/row benchmark. 3 `error` runs on record (same since-fixed DB9 `KeyError: 1`
class), 3 `aborted`, 2 `queued`. `rows_per_second` NULL, `measurement_count = 0`. Serve cost
unmeasured; 120 rows, single indexed scan, but note `graha_positions_jsonb` is a 9-element array per
row — a full-lifespan fetch returns a materially larger payload than the other four assets, which is
the one place a `density_contract` byte cap would earn its keep.

### 8. Findings
- **F-TITHI-1 (NOW · D-SERVICE, cross-layer hand-off)** — `kala_tithi_pravesha` has no consumer that
  modulates any output, at L3 or L4; the Discovery's D-7 anchor-consumption claim is unproven for
  this asset (evidence in item 3(e)). **Recommend: record the disposition at L3 and raise D-7 as an
  L4 hand-off.** Do not attempt the `ph_*` wiring from this layer.
- **F-TITHI-2 (NOW · D-SERVICE)** — the in-layer wire option: adding `tithi_pravesha_rows` to
  `ClassContext.fetch()` would activate `w27b_tithi_pravesha`. Of the four unplugged assets this is
  the **second-best wire candidate** after moorti (real ephemeris precision, real verification, but
  annual grain against a windowed scorer). Cost ~30 lines in `context.py` plus ablation evidence;
  recommend deferring behind moorti and behind the F-VEDHA-2 admission ruling, since admitting
  annual-tone modifiers before settling the uncited-suppression question compounds two open
  admission decisions.
- **F-TITHI-3 (NOW · C12/D-126)** — `integrity_check_sql` NULL. Proposed, **executed, 0 violations**:
  (a) lifetime tiling contiguity — `lead(window_start) OVER (PARTITION BY chart_id ORDER BY
  pravesha_year) = window_end` for all 119 non-terminal rows (this is the invariant that the
  *end* root-find of year N and the *start* root-find of year N+1 agree, and it is exactly what a
  root-find regression would break); (b) verification honesty — every row with
  `verification_pass_status = 'two_pass_verified'` must satisfy
  `(ephemeris_audit_jsonb->>'annual_chart_moon_cross_check_diff_deg')::float <= LUNAR_RETURN_TOL_DEG`
  **and** `start_converged`, i.e. the stored status must be re-derivable from the stored audit — the
  §N.8 "the flag must have a detector" rule made permanently checkable in SQL.
- **F-TITHI-4 (NOW · C12)** — `expected_volume_formula` NULL. Derived and exact:
  `rows = DEFAULT_MAX_PRAVESHA_YEAR = 120` per (chart × ayanamsha);
  `expected_volume_inputs = {max_pravesha_year: 120, ayanamshas: 1}`. `target_floor` → 120
  (achieved, §N.4).
- **F-TITHI-5 (NEVER-LATER · §N.4)** — the writer emits the literal strings `"two_pass_verified"` /
  `"divergent_flagged"` rather than importing the named constants from
  `brahmagyan/verification_vocab.py`, which §N.4 requires ("never a bare string literal"). The
  *values* are correct and the DB CHECK pins them, so this is a hygiene defect, not a truth defect.
  Cost: 2 import lines. Log for W3 unless a vocabulary pass is already scheduled.
- **F-TITHI-6 (NEVER-LATER)** — single-ayanamsha scope (`lahiri_chitrapaksha`), consistent with the
  L3 convention and disclosed; not a defect, log for completeness.

**Route recommendation (W2 input):** `verified_reuse` — the data is measured correct on both charts,
the verification signal is genuinely earned, the tiling invariant holds, and the serving surface has
no truncation defect. Everything outstanding is registry metadata (F-TITHI-3/4) plus a consumption
decision that is partly L4's. No rebuild required.

---

## Cross-asset W2 input: the four routes at a glance

| asset | consumed? | evidence | route | rebuild needed |
|---|---|---|---|---|
| `ka_kota_chakra` | **no** | `ClassContext` has no kota field; `w25` returns 1.0 always; ring vocabulary mismatch would null it even if wired | `changed` | yes (horizon roll) |
| `ka_moorti_nirnaya` | **no** | `w22` reads absent `context.moorti_rows`; own docstring concedes it | `changed` | yes (horizon roll) |
| `ka_vedha_gochara` | **yes** | `quality_gates` factor of λ_v3, `engine.py:629`; measured ~0.85 today | `changed` | yes (horizon roll) |
| `ka_sudarshana_varsha` | **no** | zero consumers; dormant `w27c` names a non-existent table | `changed` | yes (never built on chart 2) |
| `ka_tithi_pravesha` | **no** | `w27b` reads absent field; no `ph_*` reader (D-7 unproven) | `verified_reuse` | no |

**If W2 takes only three actions from this batch, take these:**
1. Push the currency predicate into the SQL of `query_kota_chakra` / `query_moorti_nirnaya` /
   `query_vedha_gochara` and repair their coverage sentences (F-KOTA-1/2, F-MOORTI-1, F-VEDHA-1).
   One defect class, three files, and it removes a false claim currently on a served surface.
2. Surface `grid_basis` in `quality_gates_detail` and route the "may an approximation move λ_v3"
   question to an admission ruling (F-VEDHA-2) — the code currently answers it by default, in
   contradiction of its own IR-6 rule.
3. Fill `integrity_check_sql` + `expected_volume_formula` for all five from the invariants and
   formulas above — every invariant listed was executed against live data and returned 0 violations,
   and no proposal is a `count(*) = N` pin.
