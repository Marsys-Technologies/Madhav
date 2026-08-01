---
artifact: W3K_SUBSTRATE_INVENTORY (existing-substrate audit + layer-seating recommendation for item 18 / CR-75, the KP sub-lord engine)
canonical_id: W3K_SUBSTRATE_INVENTORY
version: 1.0
status: DRAFT-FOR-ADJUDICATION — this document is a RECOMMENDATION, not a ruling. The
  layer-seating question (bg_* vs ga_* vs ka_* split) is on ANTARYĀMIN's pre-queued docket
  (SHAD_DARSHANA_NIGHT_RUN_v1_0.md §A "Known adjudications" — "W3K layer seating (bg_ vs ga_
  split)") and is currently UNRULED (SHAD_DARSHANA_STATE.md line 883, 1116). Nothing in this
  document may be treated as an approved design; it is the K.1 "existing-substrate audit FIRST"
  step the brief requires before any build lane opens (SHAD_DARSHANA_BRIEF_v2_0.md §W3K).
created: 2026-08-01
author: w3k-inventory lane (NIGHT_RUN §C Track F, first act)
scope: >
  Item 18 (CR-75, KP sub-lord engine) only. Does not touch item 19 (W2G/GOCHARA-2.0), does not
  write production code, does not rule the layer-seating question, does not touch the ledger.
inputs_read:
  - SHAD_DARSHANA_BRIEF_v2_0.md §1 item 18, §3 W3K section (K.1–K.4, Gate W3K)
  - SHAD_DARSHANA_NIGHT_RUN_v1_0.md §C Track F, §A adjudication docket
  - KALA_SUPREME_ELEVATION_v1_0.md (single item-18 cross-reference; no dedicated KP section)
  - KALA_W2_FIELD_DESIGN_v1_0.md §4.1, §11.4 (the field's own KP-extension seam)
  - Live production DB (READ-ONLY, mcp__postgres__query) — both canonical charts
  - platform/ + platform-mcp/ source, migrations (live + _archive), 05_TEMPORAL_ENGINES/kp/
---

# W3K Substrate Inventory — item 18 / CR-75, the KP sub-lord engine

## §0 — Headline finding (read this first)

**The brief's premise that "KP exists nowhere in this codebase" (SHAD_DARSHANA_BRIEF_v2_0.md
§W3K, opening line) is FALSE, and the falseness is load-bearing for how W3K should be scoped.**
A real, live, two-pass-verified KP sub-lord substrate already exists, is stored in
`chart_facts` and `chart_dashas`, is served by a registered MCP tool
(`ganita_kp_cusps_get`) on both canonical charts across all 5 stored ayanamshas, and — most
consequentially — **a KP-variant time-indexed dasha system (`vimshottari_kp`) already exists
in `chart_dashas`, already serves through `get_dashas.ts`/`query_active_dashas.ts`, and is
already deliberately excluded from one live consumer (`gochara_intensity/permission.py`) with
a documented doctrinal rationale.** The brief's own duplicate-copy rail anticipated this
possibility exactly ("`ganita_kp_cusps_get` is a live registered tool today, so SOME KP
substrate ... already exists") but the live substrate is considerably deeper than "cusps at
minimum" — it reaches into the dasha-clock layer that K.3 was written to build.

This changes W3K's shape: it is **not** a from-zero build of a "whole missing capability." It
is (a) formalizing an existing, scattered, ad-hoc substrate into first-class layer-seated
assets with registry rows and count_sql (§N.4 cockpit truth — currently absent for every KP
fact category), (b) closing three genuine capability gaps (real classical significators,
KP-native ruling-planet-at-query-time for horary/muhūrta use, and Law-1-gated field
concurrence), and (c) resolving one live, apparently stale disposition (§4 below) that
predates the substrate it disagrees with.

---

## §1 — The complete substrate inventory (evidence-backed)

### 1.1 The serving tool: `ganita_kp_cusps_get`

- **MCP registration:** `platform-mcp/src/tools/register_p1_ganita.ts` lines 776–822
  (comment tags it "SARVA-SIDDHI W-4 D-4, CR-30"). Calls
  `callRegistryCapability('marsys://tool/L1/get_kp_cusps', …)`.
- **Underlying capability:** `platform/src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts`
  (283 lines, landed 2026-07-24, PR #738 — `feat(sarva-siddhi): dedicated first-class KP
  cusp/sub-lord serving face (CR-30)`). Pure serving route (B.10-compliant — "NO new
  computation... every value returned here is already computed and stored in chart_facts").
  Assembles four fact categories into a per-cusp KP chain (sign_lord/star_lord/sub_lord/
  sub_sub_lord/prana_lord), cuspal significators, Placidus+Sripati cusp degrees, and natal
  ruling planets; optional per-graha KP chain via `include_graha_kp_lords`.
- **Vidhi planner face:** `platform/src/lib/vidhi/registry_data.ts` lines 643–658 —
  primitive `kp_cusp_sublord_read`, `live_tool: ganita_kp_cusps_get`, **CR-30 CLOSED**,
  prevents CR-36. Wired into the planner, not just the raw MCP surface.
- **Tests:** `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_kp_cusps.test.ts`
  — structural/assembly tests only (fixture-mocked DB rows), no classical-value verification.

### 1.2 The computation: `compute_kp_lords` (real 249-fold Vimśottarī subdivision, 4 levels)

- **File:** `platform/python-sidecar/ga_writers/ga_nakshatra_compute.py`, function
  `compute_kp_lords(longitude: float)` (lines 38–71). Algorithm: Vimśottarī-proportional
  subdivision of a sidereal longitude to 4 nested levels — star_lord (nakshatra lord) →
  sub_lord → sub_sub_lord → prana_lord. This **is** the classical 249-division algorithm
  (star × sub = 249 segments across the zodiac), carried one and two levels deeper
  (sub-sub, prana) than the "249" figure names.
- **Emission:** `platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py`,
  `emit_kp_lords()` (lines 123–178). Emits `graha_kp_lords` (per-body, 9 grahas + Lagna) and
  `cusp_kp_lords` (per-cusp, 12 houses) fact rows. **B.10-honest on the cusp side**: cusp
  sub-lords are computed from REAL Placidus cusp longitudes (`bhava_chalit.placidus.
  cusp_boundaries`, house_code='P' via `drik.bhaava_madhya_swe`); if that input is absent the
  writer emits an explicit `[EXTERNAL_COMPUTATION_REQUIRED]` marker rather than a fabricated
  equal-house fallback (a documented prior bug, now fixed — comment cites the removal of
  "FAKE precision").
- **Additional cuspal fact categories** (sign_lord/star_lord/sub_lord chain restated per
  cusp, cusp degrees, natal ruling planets) are emitted by a **second, separate writer**:
  `platform/python-sidecar/ga_writers/ga_sensitive_writer.py` — Category 22
  (`kp_ruling_planets_natal`, lines ~1749–1810) and Category 23 (`kp_cuspal_significators`,
  lines ~1817–1920). `get_kp_cusps.ts` cross-checks the two writers' outputs at assembly
  time and surfaces any `star_lord`/`sub_lord` divergence as a `chain_divergence` flag rather
  than silently picking one — i.e., the current serving layer already treats two independent
  writer-paths converging on the same value as a thing worth verifying, which is exactly the
  Gate-W3K discipline the brief asks for.
- **`bhava_cusps`** (cusp degrees, Placidus + Sripati start/madhya/end) is a third fact
  category, also from `ga_sensitive_writer.py`.

### 1.3 Live data, both canonical charts, all 5 ayanamshas (verified via read-only DB query)

| fact_category | rows/chart/ayanamsha | 482012f1 (Abhisek) | 1c826d5a (Abhinandan) |
|---|---:|---|---|
| `graha_kp_lords` | 40 | ✓ (all 5 ayanamshas) | ✓ (all 5 ayanamshas) |
| `cusp_kp_lords` | 48 | ✓ | ✓ |
| `kp_cuspal_significators` | 60 | ✓ | ✓ |
| `bhava_cusps` | 72 | ✓ | ✓ |
| `kp_ruling_planets_natal` | 10 (5 roles × 2 keys) | ✓ | ✓ |

Identical coverage on both charts, all 5 stored ayanamshas (krishnamurti, lahiri_chitrapaksha,
raman, surya_siddhanta_classical, true_chitra). `kp_ruling_planets_natal` carries 5 roles:
`RP_ASC_LORD`, `RP_ASC_SUB_LORD`, `RP_DAY_LORD`, `RP_MOON_SIGN_LORD`, `RP_MOON_STAR_LORD` —
this is the **natal** ruling-planet set (fixed at birth), not the query-moment set KP horary
practice normally computes (see gap G-2, §2).

Inspected `kp_cuspal_significators.significators_json` content directly (chart 482012f1,
krishnamurti): for CUSP_1 → `["Mars","Ketu","Mercury"]`, for CUSP_10 →
`["Saturn","Sun","Saturn"]`. This is **`[sign_lord, star_lord, sub_lord]` of the cusp itself**,
not the classical 4-fold KP significator derivation (planets that signify a house via
occupying/owning the house or the nakshatra of its occupant/owner, ranked). See gap G-1.

### 1.4 The KP dasha/window substrate: `chart_dashas.system_id = 'vimshottari_kp'` (the big finding)

`chart_dashas` (the same L1 table serving all 9 dasha systems) already carries KP-native
columns — `kp_sublevel`, `kp_sub_lord`, `kp_sub_sub_lord` — and a **distinct `system_id`,
`vimshottari_kp`**, live and populated:

| system_id | level_n | rows (482012f1) | kp_sub_lord populated | kp_sub_sub_lord populated |
|---|---:|---:|---:|---:|
| `vimshottari_kp` | 2 (KP sub-period) | 576 | 576 | 0 |
| `vimshottari_kp` | 3 (KP sub-sub-period) | 5,184 | 5,184 | 5,184 |

- **Writer:** `platform/python-sidecar/ga_writers/ga_dashas_writer.py` (`KP_SYSTEM_ID =
  "vimshottari_kp"`, lines 85, 1169–1290ish). Computes KP sub/sub-sub periods as
  Vimśottarī-proportional subdivisions of each classical Mahādaśā's real start/end window —
  the same proportional-subdivision principle as §1.2, applied to time instead of longitude.
  Full-precision datetime boundaries (not midnight-only), window-clipped to the
  1950–2100 build horizon.
- **A documented incident (V-12), already fixed:** the writer's own comment records that KP
  sub-period rows were originally written under `system_id="vimshottari"` (same namespace as
  classical Antardasha), which collided with `get_dashas.ts`'s default facets
  (`system=vimshottari AND level<=3`) and returned two divergent-end-date rows for the same
  start date. Fixed by giving KP its own `system_id`. This is exactly the class of "silent
  reconciliation" bug the brief's K.2 warns against for the ayanamsha/house-system
  divergence — evidence the existing substrate already had, and fixed, one instance of the
  failure mode W3K is scoped to guard against.
- **Already served:** `platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts`
  lists `vimshottari_kp` as one of the 9 baseline systems it expects and reports honestly if
  absent for a chart (no fabrication). `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`
  also recognizes the system_id.
- **Already consumed downstream — with an explicit, reasoned EXCLUSION:**
  `platform/python-sidecar/services/gochara_intensity/permission.py` (lines ~10–36) computes
  DR-14's timing-system-plurality PERMISSION term across 8 `chart_dashas` systems + 4 other
  generators, and **deliberately excludes `vimshottari_kp`**: *"a KP-variant sub-period
  system... it is a finer subdivision of the same Vimśottarī family already counted once, not
  an independent generator; double-counting it would inflate PERMISSION's plurality count
  without adding a genuinely independent timing system."* This is a **correct** ruling for
  the narrow question it answers (is the KP sub-period window a fifth independent *timing
  generator*? — no, it shares MD/AD boundaries with classical Vimśottarī) but it is not the
  same question as item 18's stated value proposition ("KP is methodologically independent of
  Parāśari... a genuine fourth voice"). See §4 for why this matters and is not a
  contradiction once the two questions are told apart.

### 1.5 The field's own extension seam for KP (already designed, not yet exercised)

`KALA_W2_FIELD_DESIGN_v1_0.md` §11 "Open questions this design deliberately does NOT decide,"
item 4: *"KP as a fourth Law-2 voice. `S_pred(e)` is open by construction — W3K's KP clock
joins by adding a `bg_dasha_systems` row and a `q_s` rule (§4.1 step 4), with no change to
§5.1."* This is the field design's own designated attachment point for W3K — confirmed live:

- `bg_dasha_systems` (design-doc name) = this repo's `brahma_dasha_systems` (mapping noted in
  `platform/python-sidecar/services/ka_kshetra/stage3_clocks.py` line 17).
- Queried live: `brahma_dasha_systems` holds 18 rows (parashari + jaimini schools:
  vimshottari, yogini, ashtottari, chara_jaimini, brahma_dasha, tara_dasha, etc.) — **no `kp`
  row exists.** This is the one concrete, well-scoped action K.3 needs at the field-integration
  layer: one new `brahma_dasha_systems` row (school='kp') + one `q_s` applicability rule.
  Everything else about the field's hazard/salience/serving machinery is untouched.
- **Current W2 state** (SHAD_DARSHANA_STATE.md line 901): W2 is BUILT-NOT-CLOSED,
  PARKED-HONEST — the clock tables (`kala_field_clocks`, migration 490, item 12 applicability)
  are live in production, but `ka_kshetra` writes **zero field rows** pending the unruled N_e
  lifetime-count-priors blocker. So "W2's clock machinery" (the NIGHT_RUN Track F trigger for
  W3K) exists as schema + writer code, not yet as populated data — W3K's true dependency is
  narrower than "W2 closed": it needs the `kala_field_clocks` table shape and the
  `bg_dasha_systems`/`q_s` seam, both of which already exist independent of N_e.

### 1.6 Dead/legacy KP artifacts (confirm NOT the substrate to extend)

- **`platform/migrations/_archive/024_kp_sublords.sql`** — a `kp_sublords` table, string
  `chart_id` (not UUID — `'abhisek_mohanty_primary'`), 9 hardcoded graha rows, Lahiri only.
  ARCHIVED. Confirmed dead: no live `.ts`/`.py` file outside comments references the table
  name at runtime (`grep` hits are all in explanatory comments about its retirement).
- **`platform/src/lib/schools/kp_engine.ts`** — a "School Engine 4" scoring module consumed
  by `school_runner.ts` (used by the `assess_career`/`assess_health`/`assess_marriage`/
  `assess_wealth` MCP tools' multi-school convergence machinery). Its `defaultSignals()`
  fallback path is **hardcoded fabricated data**: a fixed `KP_SUBLORD_ACTIVATION` map by
  house number with a code comment "In production: query kp_sublords table (migration 024)"
  — i.e. it still names the archived table as its intended real source — plus literal
  invented `SIG.MSR.*` IDs and pre-written prose ("Saturn as 10H sub-lord in its own sign
  Libra (exalted)..."). It is explicitly a `FALLBACK-OF-LAST-RESORT` (module comment,
  `school_runner.ts` line 6) used only when `liveSignals` for the `kp` school is absent from
  the caller. **This is a pre-existing B.10-adjacent concern independent of W3K** — flagged
  here for visibility, not proposed as in-scope for this wave (it is a fallback path in a
  different, older serving system — the "7 school engines" convergence layer — not the L1–L5
  layer stack W3K builds in). Recommend a separate ledger note; do not fold into W3K's gate.
- **`00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/BRIEF_D5.md` §7 /
  `TEMPORAL_ENGINE_ARC_PLAN_v1_0.md` §4.6** — both explicitly listed "KP sub-lord engine
  (CR-75 — no substrate exists...)" as OUT of D-5 scope. True at time of writing (D-5
  predates CR-30, which landed 2026-07-24); now **stale** relative to the substrate in §1.1–1.5,
  but those documents' own scope boundary (D-5 is closed) means this is a historical-accuracy
  footnote, not an open item — D-5 correctly excluded KP either way.

---

## §2 — Gap list: what item 18 actually still needs

Ordered by what Gate W3K's own acceptance criteria (brief §W3K) name.

**G-1. Real classical significators (K.2).** What exists (`kp_cuspal_significators.
significators_json`) is `[sign_lord, star_lord, sub_lord]` of the cusp — a restated lordship
chain, not the classical KP significator derivation (planets signifying a house by: occupying
the house / owning the house / occupying the nakshatra of the house's occupant / occupying the
nakshatra of the house's owner — the standard 4-limbed KP significator ladder, typically
computed per-house AND per-planet, both directions). No code path computes this. **This is the
one genuine new-computation item in K.2** — it is a deterministic join over already-stored L1
facts (graha house placement, graha nakshatra, house cuspal lord chain), not new astronomy.

**G-2. Query-moment ruling planets (for horary/muhūrta use).** `kp_ruling_planets_natal` is
fixed-at-birth. Classical KP horary practice (and KP-informed muhūrta) computes ruling
planets **at the moment of judgment/query**, not natal. No such computation exists (praśna's
own `kp_number`-based lagna casting in `ga_prashna_writer.py` is a related but distinct
classical-KP-numbering horary technique, already built for a different purpose — worth
citing as precedent for the arithmetic, not a substitute).

**G-3. Cockpit truth (§N.4) — no count_sql covers any KP fact category correctly.**
Verified live: `ga_nakshatra`'s `count_sql` explicitly lists `graha_kp_lords, cusp_kp_lords`
(covered). `ga_sensitive`'s `count_sql` has a wildcard `fact_category LIKE 'kp_%'` which
catches `kp_cuspal_significators` and `kp_ruling_planets_natal` (covered, incidentally).
**`bhava_cusps` matches neither pattern and is NOT counted by any asset's `count_sql`** —
confirmed by direct query (`count_sql ILIKE '%bhava_cusp%'` → 0 rows in `asset_registry`).
Small, concrete, pre-existing §N.4 violation; fixing it is a one-line `count_sql` edit, not
part of the new build, but should ride the same PR since W3K touches this area anyway.

**G-4. The KP window stream as a Law-1-gated field voice (K.3).** The `vimshottari_kp`
sub/sub-sub period data exists (§1.4); what's missing is the field-integration seam: the
`brahma_dasha_systems` row (school='kp') + a `q_s` applicability rule (per
`KALA_W2_FIELD_DESIGN_v1_0.md` §4.1 step 4) so KP's sub-period boundaries can be evaluated
for Law-1 applicability and enter `S_pred(e)` as an actual fourth voice — i.e., the
**judgment layer** ("does the running dasha lord match this house's KP significator?"),
layered over the existing timing substrate, not a new timing clock. This is the resolution
to the apparent tension in §4 below.

**G-5. Serving/School-tag integration (K.4).** No `kala_now_get`/`kala_windows_get`/etc. path
currently surfaces KP concurrence or dissent as a labeled voice; those tools exist (real,
substantial implementations post-Night-3, not stubs — `now.ts` 1,728 lines, `ahead.ts` 1,586
lines) but have no KP input yet. This is downstream of G-1 and G-4.

**G-6. Worked-example citation for Gate W3K's two-pass verification.** A real crosscheck
already exists: `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` (M3-W3-C2-KP-VARSHAPHALA,
2026-05-01) — cross-checks a KP sub-lord engine (`compute_kp.py`, the archived-table-era
predecessor of today's `compute_kp_lords`) against FORENSIC §4.2's KP Planetary Positions
table: **Star Lord 9/9 PASS, Sub Lord 9/9 PASS, Sub-Sub Lord WITHIN_TOLERANCE** (4/9 exact,
5/9 boundary-flips explained by the standing GAP.09 ayanamsha-precision band — same
documented effect as Vimśottarī dasha date offsets). This satisfies the brief's citation-source
hierarchy tier (ii)/(iii) territory (a committed, dated, methodologically-explained fixture)
for the **algorithm's correctness on star/sub lord**; it does not yet cover the cusp
sub-lords, the `vimshottari_kp` dasha windows, or the (not-yet-built) significator derivation
— **Gate W3K should re-run/extend this exact crosscheck methodology against the live
`get_kp_cusps` output and the `vimshottari_kp` windows**, rather than starting a citation
search from zero. It is the strongest first-pass source in the hierarchy the brief specifies.

**Not a gap — already closed:** ayanamsha/house-system divergence serving (K.2's "never
silently reconciled" requirement). KP-canonical Krishnamurti ayanamsha is already the
`get_kp_cusps` default (school_conventions.ts §3 cites this convention); the project's
default house system elsewhere is whole-sign (`ga_vargas_writer.py`), while KP requires
Placidus — both Placidus AND Sripati cusp degrees are already stored side-by-side in
`bhava_cusps` per chart per ayanamsha. The divergence is data, not a silent pick, today.

---

## §3 — A live, currently-stale disposition this inventory surfaces

`platform/src/lib/router/retrieval_capability_spec.ts` (lines ~257–262, ~460–466) and
`platform/src/lib/contract/tool_metadata.ts` (lines ~715–721) all carry a **WP-1.3(h)/LCA-12
§7.3 "PHANTOM DROPPED"** disposition for two planner-facing capability names (`kp_query`,
`query_kp_ruling_planets`): *"no KP engine backs them... migration 024_kp_sublords is
ARCHIVED... `schools/kp_engine.ts` is a signal-scoring engine with hardcoded activation
values, not a cusp/sublord query... Re-instate only if a real KP engine is built and
registered."* Git-blamed: this comment set landed **2026-07-13** (PR #555). `get_kp_cusps.ts`
(the real KP engine these comments say doesn't exist) landed **2026-07-24** (PR #738,
11 days later) and is a live, registered, tested capability today. **These three comments are
now stale relative to the codebase they describe** — not because the underlying disposition
(don't advertise phantom names) was wrong, but because the premise ("no real KP engine
exists") flipped under them without the comment being revisited. Likewise
`school_conventions.ts` §3/§4/§5 (the MCP resource `marsys://school-conventions`) still
documents fact-category names `kp_cusp`, `kp_planet`, `kp_significator`, `varshphal` — **all
four confirmed 0 rows in production** (direct query) — none of which match the real category
names (`cusp_kp_lords`, `kp_cuspal_significators`, `kp_ruling_planets_natal`, `bhava_cusps`,
`graha_kp_lords`). This resource is stale documentation, not stale code (nothing queries by
the wrong names), but an LLM consumer reading `school-conventions` today would be told to
query fact categories that don't exist. **Recommend**: whichever W3K lane does the
significator work (G-1) also refreshes `school_conventions.ts` §3–5's category names and
re-evaluates whether `kp_query`/`query_kp_ruling_planets` should be re-instated now that a
real engine exists (a naming/registration decision, not a computation one — plausibly
foldable into ANTARYĀMIN's layer-seating ruling rather than a separate adjudication).

---

## §4 — Resolving the apparent "independent voice" vs. "not independent" tension

The brief states KP's value is being "methodologically independent of Parāśari... a genuine
fourth voice instead of a restatement of evidence already counted" (§W3K opening). The live
`gochara_intensity/permission.py` architecture states the opposite about `vimshottari_kp`:
it is "a finer subdivision of the same Vimśottarī family already counted once... not an
independent generator." **Both are correct, because they answer different questions:**

- **Timing-generator independence** (DR-14's question, answered by `permission.py`): does KP
  offer a *different clock* — different period boundaries computed by a different rule? No.
  Classically and in this codebase, KP's sub/sub-sub periods are proportional subdivisions of
  the *same* Vimśottarī Mahādaśā/Antardaśā windows every other Parāśarī reading already uses.
  Counting it as a fifth independent generator in DR-14's PERMISSION plurality sum would be
  double-counting the same clock twice. `permission.py`'s exclusion is doctrinally correct
  and should not be revisited by W3K.
- **Judgment-method independence** (item 18's question, answered by nothing yet — this is
  G-4): does KP reach a *verdict* about a given period through a rule Parāśari doesn't use? Yes
  — "does the currently-running dasha lord (at whatever level) match this house's KP
  significator?" is a judgment rule with no Parāśarī analogue; it can agree or disagree with
  the Parāśarī reading of the *same* time window. **This is where KP earns its fourth-voice
  status** — not by proposing a new clock, but by proposing a new verdict-rule layered on the
  clock everyone already shares. K.3/K.4's design should be read this way: the "independent
  clock" language in the brief is slightly imprecise and risks being misread as "KP needs its
  own timing generator" (which would in fact violate DR-14's already-settled position); the
  correct scope is KP as an independent **applicability/verdict rule** (`q_s` in the field
  design's own vocabulary) riding the existing `vimshottari_kp` window data. Recommend
  ANTARYĀMIN's ruling note this distinction explicitly so a future builder doesn't try to
  invent a genuinely separate KP clock that would then collide with DR-14.

---

## §5 — Layer-seating RECOMMENDATION (bg_* / ga_* / ka_* split)

**Status: RECOMMENDATION ONLY, pending ANTARYĀMIN ratification.** Argued from CLAUDE.md
§N.1 (asset-id convention, underscore prefix per layer) and the existing L0/L1/L3 semantics
this codebase already enforces elsewhere (chart-independent reference data is `bg_*`;
per-chart facts derived from a specific native's birth moment are `ga_*`; time-indexed,
build-forward windows are `ka_*`).

### 5.1 `bg_*` — chart-independent reference geometry

**What seats here:** a canonical **249-fold sub-lord reference table** — for every degree (or
arcminute-resolution band) of the 360° zodiac, the star_lord/sub_lord/sub_sub_lord/prana_lord
chain, computed once from Vimśottarī proportions and independent of any chart. This does not
exist today as a table — `compute_kp_lords()` recomputes the subdivision inline, per call, per
longitude, in Python. That inline function is correct and cheap enough that a lookup table is
not a correctness requirement, but §N.1's layer semantics are about *what the value depends
on*, not runtime cost: the sub-lord-at-a-given-longitude mapping depends on nothing chart-specific
— it is exactly the "chart-independent reference, e.g. the 249-sub-lord table derived purely
from Vimśottarī proportions" the task brief anticipates. **Recommend:** a `bg_kp_sublords`
(or `bg_249_division`) reference asset, `@register`-conformant per §N.2, built once
(global, L0 idempotency = upsert per §N.3), holding the 249 (or finer) canonical sub-lord
segments as degree ranges + lord chains. Also seats here: the one new
`brahma_dasha_systems` row (school='kp') that §1.5/G-4 identifies as the field's extension
seam — it is reference/ontology data (a school description), not a per-chart fact, matching
the other 18 rows already in that table.

**Why not ga_\*:** the sub-lord-per-degree mapping is pure arithmetic over a fixed
9-planet Vimśottarī-years table and the 27-nakshatra grid; it has no dependency on any
native's birth data. Storing it per-chart would duplicate an identical 249-row table once per
chart in the database — the same anti-pattern §N.1 exists to prevent (compare: nakshatra/pada
static attributes are already `bg_nakshatra`-authority, joined per-chart by `ga_nakshatra`,
per `ga_nakshatra_emitters.py`'s own header comment "bg_nakshatra is AUTHORITY for static
attrs... they do not recompute static values, they relay them with provenance").

### 5.2 `ga_*` — per-chart projections onto the reference geometry

**What seats here (already does, via existing writers — confirm-and-extend, not build):**
`graha_kp_lords`, `cusp_kp_lords` (`ga_nakshatra_emitters.emit_kp_lords`, JOINing a chart's
specific graha/cusp longitudes against whatever seats at §5.1); `kp_cuspal_significators`,
`bhava_cusps`, `kp_ruling_planets_natal` (`ga_sensitive_writer.py`). **New in this seating:**
G-1's real significator derivation (per-house, per-planet, 4-limbed) is a per-chart join over
already-stored L1 facts (house occupancy, nakshatra placement, cuspal lordship) — it belongs
in `ga_*`, most naturally as new fact_categories on the existing `ga_sensitive` or
`ga_nakshatra` asset (extending, per the brief's own "the wave EXTENDS what exists and never
twins it") rather than a new writer. G-2's query-moment ruling planets are per-*query*, not
per-chart, and don't fit `ga_*`'s "per birth-chart" semantics cleanly — see 5.4.

**Cockpit-truth housekeeping (G-3):** whichever asset gains the new significator rows should
also pick up `bhava_cusps` in its `count_sql` (currently uncounted anywhere) in the same PR —
same asset family, same fix motion, avoids a second migration touching the same table.

### 5.3 `ka_*` — the time-indexed KP window stream (K.3/G-4)

**What seats here:** nothing new as *data* — `vimshottari_kp` sub/sub-sub windows already
live in `chart_dashas` (an L1/`ga_*`-owned table, per §1.4) and are correctly NOT duplicated
into a `ka_*` table (§N.5's L1-authority principle: L2+ never restates an L1 computed value as
its own). What seats at `ka_*` is the **applicability/verdict evaluation** — G-4's `q_s` rule,
evaluated at build time against `kala_field_clocks` (already-live schema, migration 490) —
i.e. a modification to the existing Stage-3 clocks writer
(`services/ka_kshetra/stage3_clocks.py`) to recognize the new `brahma_dasha_systems` KP row
and evaluate its applicability the same way every other daśā system already is, per
`KALA_W2_FIELD_DESIGN_v1_0.md`'s own stated seam. This is genuinely `ka_*`-seated: it is
time-indexed (evaluated per instant `t`), field-integrated, and Law-1-gated exactly like every
other clock — no FROZEN-contract change, no new table family, additive rows only.

### 5.4 Open question this recommendation does NOT resolve (flagging for ANTARYĀMIN, not deciding)

G-2 (query-moment ruling planets for horary/muhūrta) doesn't fit neatly into any of the three
buckets above under the chart-scoped framing this recommendation otherwise uses — it's
per-query-instant, not per-birth-chart and not a build-time field window. Two candidate
seatings, deliberately left to adjudication: (a) treat it as a `ka_*` on-demand computation
(closer to `ph_muhurta`'s pattern of instant-scoped, non-persisted reads), or (b) defer it
entirely out of W3K's first build lane since neither K.1–K.4 nor Gate W3K's acceptance
criteria name it explicitly (it is this inventory's own inference from "KP horary practice,"
not a brief requirement) — **recommend (b)**, i.e. park G-2 as a documented future item and
keep W3K's first lane scoped to K.1–K.4 as written. Naming it here only so it isn't
rediscovered as a surprise mid-build.

---

## §6 — Proposed build plan for the two W3K lanes (NIGHT_RUN §A: "2 lanes, Opus doctrine")

Both lanes need Opus/high per NIGHT_RUN §B.3 ("W3K sub-lord doctrine" is an explicit
mandatory-escalation line item). Sequencing below assumes ANTARYĀMIN's layer-seating ruling
(§5) lands before either lane opens — per NIGHT_RUN §D SESSION-OPEN PROTOCOL step (c), that
ruling should be discharged up front, not mid-lane.

**Lane 1 — Reference substrate + real significators (bg_* + ga_* extension).**
1. `bg_kp_sublords` (or equivalent name, collision-checked against `asset_registry` first —
   none found in this audit) — the 249-division canonical reference table, built once,
   `@register`-conformant, upsert idempotency (§N.3 L0 rule).
2. `brahma_dasha_systems` new row: `canonical_id='kp'`, `school='kp'`, citing KP Reader /
   Stellar Astrology per `school_conventions.ts` §3's existing classical-anchor list.
3. G-1: real 4-limbed significator derivation, new fact_categories on the existing
   `ga_sensitive` (or `ga_nakshatra`) writer — per-house AND per-planet directions, both
   charts, all 5 ayanamshas.
4. G-3 housekeeping: `bhava_cusps` added to whichever `count_sql` is most natural (likely
   `ga_sensitive`'s existing wildcard needs a literal addition since `bhava_cusps` doesn't
   match `kp_%`).
5. G-6: extend `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md`'s methodology to cover
   `get_kp_cusps`'s live cusp output and the new significator derivation — this is Gate
   W3K's two-pass verification discharge, and it has a strong existing precedent to extend
   rather than invent.
6. §3 housekeeping (can ride this lane or split off): refresh `school_conventions.ts` §3–5
   category names; adjudicate (with ANTARYĀMIN) whether to re-instate `kp_query`/
   `query_kp_ruling_planets` at the retrieval_capability_spec/tool_metadata layer now that a
   real engine exists, or retire the phantom-dropped comments as historically resolved
   without re-adding the names (a naming call, not a computation one).

**Lane 2 — Field integration (ka_* clock seam, K.3/K.4).**
1. G-4: `stage3_clocks.py` recognizes the new KP `brahma_dasha_systems` row, evaluates
   Law-1 applicability for `vimshottari_kp` windows exactly as for the other 8 systems already
   handled there — additive, no FROZEN-contract change.
2. Wire the resulting KP applicability signal into `S_pred(e)` per the field design's own
   §11.4 seam ("no change to §5.1").
3. G-5: once G-1's significators exist, surface KP concurrence/dissent as a school-tagged
   voice in at least one of `now.ts`/`ahead.ts`/`explain.ts` (Gate W3K requires "at least one
   served dissent" — this needs a real disagreement case between KP's significator verdict and
   the Parāśarī reading of the same window on one of the two canonical charts, found not
   manufactured).
4. Depends on Lane 1's G-1 output (significators) to have anything to evaluate agree/disagree
   against — **sequence Lane 2 behind Lane 1's step 3**, not fully parallel, though Lane 2's
   step 1 (the `q_s` rule scaffold itself) can start immediately since it only needs the
   `brahma_dasha_systems` row shape, which Lane 1 step 2 produces early.
5. Note the §1.5 dependency correction: Lane 2 does NOT need to wait for Gate W2 to fully
   close (the N_e-blocked field population) — it needs `kala_field_clocks`'s schema and the
   Stage-3 writer's code path, both already live independent of N_e. Confirm this narrower
   dependency with the Conductor before treating "W2 closed" as a blocking precondition.

**Both lanes' Gate W3K discharge (shared, sequential last step):** worked-example
verification on BOTH charts (G-6) · cuspal sub-lords computed both charts (already true,
§1.3 — re-verify against the extended crosscheck) · KP as a distinct concurrence AND at
least one dissent voice (Lane 2 step 3) · Law-1 applicability evaluated not assumed
(Lane 2 step 1) · ayanamsha/house-system divergence served explicitly (already true, §2
"not a gap") · specificity gate still HARD-green with KP prose included (verify at
integration, no reason to expect regression given KP rows are additive).

---

## §7 — Evidence index (files/tables cited above)

**Live code:**
`platform-mcp/src/tools/register_p1_ganita.ts:776-822` ·
`platform/src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts` ·
`platform/src/lib/vidhi/registry_data.ts:643-658` ·
`platform/python-sidecar/ga_writers/ga_nakshatra_compute.py:38-71` ·
`platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py:123-178` ·
`platform/python-sidecar/ga_writers/ga_sensitive_writer.py:~1749-1920` ·
`platform/python-sidecar/ga_writers/ga_dashas_writer.py:85,1169-1290` ·
`platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts` ·
`platform/python-sidecar/services/gochara_intensity/permission.py:10-36` ·
`platform/python-sidecar/services/ka_kshetra/stage3_clocks.py:17` ·
`platform/src/lib/schools/kp_engine.ts` + `platform/src/lib/schools/school_runner.ts` ·
`platform/src/lib/router/retrieval_capability_spec.ts:257-262,460-466` ·
`platform/src/lib/contract/tool_metadata.ts:715-721` ·
`platform-mcp/src/resources/school_conventions.ts:69-138` ·
`platform/python-sidecar/ga_writers/ga_prashna_writer.py`.

**Dead/archived:** `platform/migrations/_archive/024_kp_sublords.sql`.

**Doctrine/design:** `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
KALA_W2_FIELD_DESIGN_v1_0.md §4.1,§11.4` ·
`00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/
DR_14_15_16_TEMPORAL_DOCTRINE_v1_0.md` (DR-14) ·
`00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/BRIEF_D5.md §7` ·
`05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md`.

**Live DB (read-only, verified 2026-08-01):** `chart_facts` (5 KP-related fact_category
values × 5 ayanamshas × 2 canonical charts, row counts in §1.3) · `chart_dashas`
(`vimshottari_kp` system_id, row counts in §1.4) · `brahma_dasha_systems` (18 rows, no `kp`)
· `asset_registry` (no `%kp%`/`%sublord%` asset_id; `count_sql` coverage checked for all 5
KP fact categories, gap identified for `bhava_cusps`).

---

*End of W3K_SUBSTRATE_INVENTORY_v1_0.md. RECOMMENDATION status per frontmatter — the §5
layer-seating split and the §3 stale-disposition/re-instatement question both require
ANTARYĀMIN ratification before any Lane 1/Lane 2 builder opens a migration.*
