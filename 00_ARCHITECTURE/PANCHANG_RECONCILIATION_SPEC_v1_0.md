---
artifact: PANCHANG_RECONCILIATION_SPEC_v1_0.md
type: RECONCILIATION_SPEC
version: 1.0
status: CURRENT
authored_by: Claude Code (PRECON-S1)
authored_on: 2026-05-20
session_id: PRECON-S1
compares:
  main: origin/main (SHA 039d993b)
  source: origin/feature/phase-4c-panchang (SHA ff0a60c7)
output_for: native review → re-scoped ship round
hard_constraint: READ-ONLY session — no code was changed to produce this document
---

# Panchang Reconciliation Spec v1.0

Produced by PRECON-S1 (2026-05-20). Answers all 8 analysis items from
`CLAUDECODE_BRIEF_PRECON_S1_v1_0.md`. Native must review before any ship session
proceeds. The reconciliation recommendation (§6) determines the re-scoped plan (§7).

---

## §1 — query_panchanga Tool Diff

Both branches export `tool: RetrievalTool` from
`platform/src/lib/retrieve/query_panchanga.ts` with `name='query_panchanga'`,
`version='1.0.0'`. The interfaces are **divergent, not compatible**.

### 1.1 Input parameters

| Param | Main (SQL) | Ours (Sidecar) | Notes |
|---|---|---|---|
| `date` | ✓ YYYY-MM-DD | ✓ YYYY-MM-DD | Same |
| `start_date` / `end_date` | ✓ range query | ✗ uses `range.from/to` | Different API shape |
| `range: {from, to}` | ✗ | ✓ | Sidecar range endpoint |
| `tithi` | ✓ filter (integer 1-30) | ✗ | Main-only |
| `tithi_name` | ✓ filter (string) | ✗ | Main-only |
| `paksha` | ✓ filter ('shukla'|'krishna') | ✗ | Main-only |
| `moon_nakshatra` | ✓ filter (string) | ✗ | Main-only |
| `vara_lord` | ✓ filter (string) | ✗ | Main-only |
| `yoga` | ✓ filter (string) | ✗ | Main-only |
| `karana` | ✓ filter (string) | ✗ | Main-only |
| `limit` | ✓ 1-500 (default 100) | ✗ | Main-only |
| `fields` | ✓ PanchangaField[] enum | ✓ string[] | Different type shape |
| `lat` / `lon` | ✗ (fixed Bhubaneswar) | ✓ override allowed | Ours allows custom observer |
| `tz_offset_minutes` | ✗ | ✓ | Ours explicit |
| `chart_id` | ✗ | ✓ native context overlay | Ours (4C-5 wiring) |

**Key structural difference:** Main queries `panchanga_daily` SQL table (fast, indexed,
filterable). Ours POSTs to sidecar `/api/compute/panchanga` (live, on-demand, no DB
filter). These serve different query patterns — filtering vs richness.

### 1.2 Return fields

All fields for a single calendar date, marked by who provides them:

| Field | Main | Ours | Section (ours) |
|---|---|---|---|
| `date` | ✓ | ✓ | five_angas |
| `tithi` (number 1-30) | ✓ | ✓ `.id` | five_angas |
| `tithi_name` | ✓ | ✓ `.name` | five_angas |
| `tithi_fraction` | ✓ (numeric) | ✗ | **Main-only** |
| `paksha` | ✓ | ✓ | five_angas |
| `karana` | ✓ (single, sunrise-active) | ✓ `.karana_first` + `.karana_second` | five_angas |
| `karana_position_in_month` | ✓ | ✗ | **Main-only** |
| `vara` | ✓ | ✓ `.name` | five_angas |
| `vara_lord` | ✓ | ✓ (via vara) | five_angas |
| `vara_index` | ✓ | ✗ | **Main-only** |
| `yoga` | ✓ (single, sunrise-active) | ✓ `.name` | five_angas |
| `yoga_index` | ✓ | ✗ | **Main-only** |
| `moon_nakshatra` | ✓ | ✓ `.name` | five_angas |
| `moon_nakshatra_index` | ✓ | ✗ | **Main-only** |
| `moon_nakshatra_pada` | ✓ | ✗ | **Main-only** |
| `moon_longitude_deg` | ✓ | ✗ | **Main-only** |
| `sun_longitude_deg` | ✓ | ✗ | **Main-only** |
| `sunrise_utc` | ✓ | ✓ | timings |
| `sunrise_jd` | ✓ | ✗ | **Main-only** |
| `sunrise_ist` | ✓ | ✗ | **Main-only** |
| `sunset_utc` | ✗ | ✓ | **Ours-only** — timings |
| `moonrise_utc` | ✗ | ✓ | **Ours-only** — timings |
| `moonset_utc` | ✗ | ✓ | **Ours-only** — timings |
| `inauspicious` (Rahu Kalam, Yamagandam, Gulika) | ✗ | ✓ | **Ours-only** — timings |
| `auspicious` (Brahma Muhurta, Abhijit) | ✗ | ✓ | **Ours-only** — timings |
| `choghadiya` (day + night) | ✗ | ✓ | **Ours-only** — choghadiya_hora |
| `hora` | ✗ | ✓ | **Ours-only** — choghadiya_hora |
| `special_yogas` (9 types with time windows) | ✗ | ✓ | **Ours-only** — special_yogas |
| `planets` (9 grahas: lon, sign, nak, retrograde, combust) | ✗ | ✓ | **Ours-only** — planets_at_sunrise |
| `native_context` (tara/chandra bala) | ✗ | ✓ (via chart_id) | **Ours-only** |
| `ayanamsha` | ✓ | ✗ (assumed lahiri) | **Main-only** |
| `observer_lat/lon/alt` | ✓ | ✓ (as input, not output) | |
| `ephemeris_version` | ✓ | ✓ | |

**Superset verdict:** Ours-only fields vastly outnumber main-only fields in semantic
richness (timings, special yogas, planets, choghadiya). Main-only fields are metadata
and filtering artifacts (indices, fraction, JD). For planner synthesis of muhurta and
auspicious-timing questions, **ours provides critical data main's tool lacks entirely.**
For filtered search queries across date ranges ("find all Purnima dates in 2027"),
**main's tool is the only viable option** — ours has no SQL filter path.

**Bottom line: the two tools are complementary, not substitutable.**

---

## §2 — Compute-Path Diff

### 2.1 Main's path: precomputed table (batch)

**Pipeline:** `bootstrap_panchanga.py` → `panchanga_daily` table (migration 060)

- **Scope:** 73,050 rows — 1900-01-01 to 2100-12-31, one row per calendar date
- **Observer:** fixed Bhubaneswar (lat 20.27021, lon 85.82966, alt 45m)
- **Algorithm:** For each date: compute sunrise JD via `swe.rise_trans` →
  compute Sun+Moon sidereal Lahiri longitudes at sunrise JD →
  derive 5 limbs via `panchanga_derivations.py` functions
- **Refresh:** operator-run (`bootstrap_panchanga.py --build-id ...`);
  idempotent via UPSERT; result staged then promoted per RUNBOOK_EPHEMERIS_REBUILD
- **Table name:** `panchanga_daily` (NOT `panchang_daily`)
- **Indexed on:** date, tithi, tithi=15 (Purnima), tithi=30 (Amavasya),
  tithi IN (11,26) (Ekadashi), moon_nakshatra, vara_lord
- **Stored special yogas:** NO
- **Stored timings** (Rahu Kalam, Yamagandam, etc.): NO
- **Stored planets at sunrise:** NO
- **Stored choghadiya/hora:** NO

**Is this the 4C-2 deferred cache?** YES. The feature branch's `query_panchanga.ts`
comment explicitly states: *"No SQL cache this session — 4C-2 will add panchang_daily
cache below the endpoint with zero changes to this tool."* Main independently built
the 4C-2 cache as `panchanga_daily` (with the 'a') before the full 4C module was
merged. Main already solved caching. Keeping it is a win — 73K rows, tested,
indexed, operational.

**Note on table name:** 4C-2 spec'd `panchang_daily` (no 'a'); main built it as
`panchanga_daily`. No conflict — the feature branch's deferred cache was never built.
Main's name wins.

### 2.2 Our path: live engine (on-demand)

**Pipeline:** `panchang_engine` library → sidecar FastAPI → `/api/compute/panchanga`
Next.js route → client

- **Scope:** Any date, any observer (lat/lon/tz configurable)
- **Observer:** defaults to Bhubaneswar, overridable per-call
- **Algorithm:** On each request: compute sunrise/sunset, moonrise/moonset via Swiss
  Ephemeris → compute 9 grahas at sunrise → derive 5 limbs → compute
  inauspicious timings (Rahu Kalam, Yamagandam, Gulika) → auspicious timings
  (Brahma Muhurta, Abhijit) → detect 9 special yogas with time-windows →
  compute Choghadiya + Hora
- **Refresh:** instantaneous — live per request; no precompute required
- **Special yogas:** YES (9 types: Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya,
  Guru Pushya, Tripushkar, Dwipushkar, Siddha, Bhadra/Vishti, Panchaka)
- **Timings:** YES (Rahu Kalam, Yamagandam, Gulika, Brahma Muhurta, Abhijit)
- **Planets at sunrise:** YES (9 grahas with sign, nakshatra, pada, retrograde, combust)
- **Choghadiya/Hora:** YES (full day + night breakdowns)
- **Native context:** YES (chart_id → tara bala, chandra bala via DB lookup)
- **Range endpoint:** `/api/compute/panchanga/range` (but no filter params)

### 2.3 Summary

| Capability | Main (SQL) | Ours (Engine) |
|---|---|---|
| 5 limbs (tithi/vara/nak/yoga/karana) | ✓ precomputed | ✓ live |
| Sunrise | ✓ | ✓ |
| Sunset / moonrise / moonset | ✗ | ✓ |
| Special yogas (9 types) | ✗ | ✓ |
| Inauspicious windows (Rahu Kalam etc.) | ✗ | ✓ |
| Auspicious windows (Brahma Muhurta etc.) | ✗ | ✓ |
| Choghadiya + Hora | ✗ | ✓ |
| Planetary positions at sunrise | ✗ | ✓ |
| Native overlay (tara/chandra bala) | ✗ | ✓ |
| Filtered range queries (find tithi=15) | ✓ (SQL WHERE) | ✗ |
| Date-range across 200 years | ✓ (73K rows) | slow (N live calls) |
| Response latency | ~5ms (SQL index) | ~200ms (sidecar) |

---

## §3 — Planner Routing Diff

### 3.1 Main's rules (origin/main PLANNER_PROMPT_v2_0.md)

**R-TC (lines 681–726): TRANSIT-CONTEXT ENRICHMENT**
Broad rule: for ANY non-natal query, attach `query_ephemeris` at priority 2.
Trigger = any temporal anchor. Excludes pure natal, classical interpretation,
remedial codex, multi-school. References R-PA for panchanga elements.

**R-PA (lines 728–769): PANCHANGA ANCHOR**
Trigger set:
- (a) Lunar phase by name: Purnima, Amavasya, Ekadashi, "full moon", "new moon",
  "bright fortnight", "dark fortnight"
- (b) Moon's nakshatra on a specific date
- (c) Vara in astrological framing ("Saturn's day", "Budhavara")
- (d) Yoga / karana by name (generic; no specific names listed)
- (e) Muhurta / auspicious-day questions ("good day for marriage", "starting a venture",
  "travel")

**What R-PA DOES cover for muhurta:** The 5 limbs, vara, generic yoga/karana,
and muhurta/auspicious-day questions. Sufficient for basic muhurta assessment
using the SQL cache.

**What R-PA DOES NOT cover** (terms absent from trigger list):
- "rahu kalam", "yamagandam", "gulika" — Rahu Kalam queries would not fire R-PA
- "choghadiya", "hora" — no trigger
- "brahma muhurta", "abhijit", "amrit kalam" — no trigger
- "panchang for today", "today's panchang", "panchang for [date]" — no trigger
- Named special yogas: "Sarvartha Siddhi", "Amrit Siddhi", "Guru Pushya", "Ravi Pushya",
  "Tripushkar", "Bhadra", "Panchaka" — no triggers
- "chandra bala", "tara bala" — no trigger

### 3.2 Feature branch's rules (origin/feature/phase-4c-panchang PLANNER_PROMPT_v2_0.md)

**R-TC (lines 681–713): TRANSIT-CONTEXT ROUTING — Panchang vs. Ephemeris disambiguation**
Completely different from main's R-TC. Routes between two tools:
- (a) PANCHANG PATH → `query_panchanga` when query mentions: tithi, nakshatra, yoga,
  karana, vara, paksha, masa, **muhurat, choghadiya, hora, rahu kalam, yamagandam,
  gulika, abhijit, brahma muhurta, amrit kalam, sarvartha siddhi, amrit siddhi,
  guru pushya, ravi pushya, bhadra, panchaka, tripushkar**, OR "good day for X",
  "auspicious time for Y", "panchang for today"
- (b) EPHEMERIS PATH → `query_ephemeris` for raw positions, ingresses, exact degrees,
  retrogrades
- (c) BOTH → co-select when query needs both data types
Note: our R-TC REPLACES main's R-TC label — it is not complementary to it.

**R-PCI (lines 715–733): PANCHANG CONTEXT INHERITANCE** — novel, absent on main
When `<panchang_context>` block present in user query (injected by /panchang AskMadhavLink),
skip `query_panchanga` tool call — use injected context instead. R-PCI priority >
R-TC for same date/location. Exceptions for different date, explicit re-query,
truncated context.

### 3.3 Routing delta

| Trigger / Query phrase | Main R-PA | Feature R-TC | Gap direction |
|---|---|---|---|
| "tithi", "full moon", "Purnima" | ✓ | ✓ | — |
| "Moon nakshatra today" | ✓ | ✓ | — |
| "vara", "Saturn's day", "Budhavara" | ✓ | ✓ | — |
| "yoga name" (generic) | ✓ | ✓ | — |
| "good day for marriage" | ✓ | ✓ | — |
| "rahu kalam" | ✗ | ✓ | Main missing |
| "yamagandam", "gulika" | ✗ | ✓ | Main missing |
| "choghadiya", "hora" | ✗ | ✓ | Main missing |
| "brahma muhurta", "abhijit", "amrit kalam" | ✗ | ✓ | Main missing |
| "Sarvartha Siddhi Yoga" | ✗ | ✓ | Main missing |
| "Amrit Siddhi", "Guru Pushya", "Ravi Pushya" | ✗ | ✓ | Main missing |
| "Tripushkar", "Bhadra", "Panchaka" | ✗ | ✓ | Main missing |
| "panchang for today", "today's panchang" | ✗ | ✓ | Main missing |
| Context-inheritance skip when block present | ✗ | ✓ (R-PCI) | Main missing |
| "ephemeris + panchanga co-select" | via R-PA+R-TC | via R-TC(c) | Effectively same |

**Verdict:** Main's R-PA is sufficient for basic 5-limb and muhurta routing but
misses 13 trigger phrases for the richer content our engine provides. These phrases
become valid after our engine is integrated. R-PCI is pure additive (no collision).

---

## §4 — Net-New Inventory (no main equivalent)

All items below are confirmed absent on `origin/main` via the A-classification in
PSHIP_FILE_INVENTORY.md. These ship cleanly under any reconciliation option.

### 4.1 /panchang UI Page

| Item | File(s) |
|---|---|
| Page + layout + error + loading | `platform/src/app/panchang/page.tsx`, `layout.tsx`, `error.tsx`, `loading.tsx` |
| PanchangClientView (main client component) | `components/PanchangClientView.tsx` |
| PanchangHeader (date nav + chart selector) | `components/PanchangHeader.tsx` |
| PrimaryStrip (5 limbs display) | `components/PrimaryStrip.tsx` |
| SpecialYogasList (9 yogas with star ratings) | `components/SpecialYogasList.tsx` |
| TimingsPanel (sunrise/sunset/moonrise + inauspicious) | `components/TimingsPanel.tsx` |
| ChoghadiyaPanel (day + night Choghadiya) | `components/ChoghadiyaPanel.tsx` |
| HoraPanel (hourly Hora breakdowns) | `components/HoraPanel.tsx` |
| PlanetaryGrid (9 grahas at sunrise) | `components/PlanetaryGrid.tsx` |
| ActionBar (share, iCal subscribe, print) | `components/ActionBar.tsx` |

### 4.2 Muhurat Finder

| Item | File(s) |
|---|---|
| MuhuratFinderModal (date-range picker + event selector) | `components/MuhuratFinderModal.tsx` |
| MuhuratResultsList (sorted results with star ratings) | `components/MuhuratResultsList.tsx` |
| useMuhuratFinder hook (state + API calls) | `hooks/useMuhuratFinder.ts` |
| Scoring engine (6-event MVP) | `panchang_engine/muhurat.py` |
| Weights config (YAML per event) | `panchang_engine/config/muhurat_weights.yaml` |
| FastAPI muhurat router | `platform/python-sidecar/routers/muhurat.py` |
| Next.js `/api/compute/muhurat` route | `platform/src/app/api/compute/muhurat/route.ts` |
| 6 events: vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation | in muhurat.py |

### 4.3 iCal Export + Signed Feed

| Item | File(s) |
|---|---|
| iCal builder (ICS generation) | `platform/src/lib/panchang/ics_builder.ts` |
| iCal client (fetch + download) | `platform/src/lib/panchang/ics_client.ts` |
| Feed revocations (revoke/re-issue) | `platform/src/lib/panchang/feed_revocations.ts` |
| URL signing (HMAC, SESSION_SECRET) | `platform/src/lib/security/sign_url.ts` |
| Subscribe route | `platform/src/app/api/panchang/feed/subscribe/route.ts` |
| Revoke route | `platform/src/app/api/panchang/feed/revoke/route.ts` |
| ICS export route | `platform/src/app/api/panchang/ics/route.ts` |
| Feed serve route | `platform/src/app/api/panchang/feed.ics/route.ts` |

### 4.4 Ask-Madhav Context Injection

| Item | File(s) |
|---|---|
| AskMadhavLink component (deep-link with context) | `components/AskMadhavLink.tsx` |
| buildPanchangInitialMessages helper | in `consume/page.tsx` (M-file, PSHIP-S2) |
| System prompt panchang_context block | in `system-prompts.ts` (M-file, PSHIP-S2) |

### 4.5 Special Yoga Detection Engine

| Item | File(s) |
|---|---|
| special_yogas.py (9 yogas, time windows, source citations) | `panchang_engine/special_yogas.py` |
| shastra_tables.py (Sarvartha Siddhi, Amrit Siddhi, etc.) | `panchang_engine/shastra_tables.py` |
| Tests for all 9 yogas | `panchang_engine/tests/test_special_yogas.py` |

### 4.6 Panchang Engine Library (full)

| Item | File(s) |
|---|---|
| __init__.py (public API: compute_panchang, panchang_range, find_muhurat) | `panchang_engine/__init__.py` |
| angas.py (5 limb algorithms) | `panchang_engine/angas.py` |
| timings.py (sunrise/sunset, Rahu Kalam, choghadiya, hora) | `panchang_engine/timings.py` |
| planets.py (9 grahas via Swiss Ephemeris) | `panchang_engine/planets.py` |
| ayanamsha.py | `panchang_engine/ayanamsha.py` |
| types.py (Panchang, Anga, Timing, PlanetState, MuhuratWindow, NatalChart dataclasses) | `panchang_engine/types.py` |
| serialize.py (panchang_to_dict) | `panchang_engine/serialize.py` |
| config_loader.py | `panchang_engine/config_loader.py` |
| exceptions.py | `panchang_engine/exceptions.py` |
| tara_bala.py (sidecar) | `panchang_engine/tara_bala.py` |
| 230 unit tests (all pass per obs 2558) | `panchang_engine/tests/` |

### 4.7 FastAPI Sidecar Routers

| Item | File(s) |
|---|---|
| panchang router (`/api/compute/panchanga`, `/api/compute/panchanga/range`) | `routers/panchang.py` |
| muhurat router (`/api/compute/muhurat`) | `routers/muhurat.py` |

### 4.8 Panchang Client Libraries

| Item | File(s) |
|---|---|
| sidecar_mapper.ts (sidecar response → UI types) | `platform/src/lib/panchang/sidecar_mapper.ts` |
| chandra_bala.ts | `platform/src/lib/panchang/chandra_bala.ts` |
| tara_bala.ts | `platform/src/lib/panchang/tara_bala.ts` |
| usePanchangDay hook | `platform/src/app/panchang/hooks/usePanchangDay.ts` |
| useChartList hook | `platform/src/app/panchang/hooks/useChartList.ts` |

### 4.9 Observatory Panels

| Item | File(s) |
|---|---|
| PanchangCachePanel | `src/lib/components/observatory/panchang/PanchangCachePanel.tsx` |
| PanchangLatencyPanel | `src/lib/components/observatory/panchang/PanchangLatencyPanel.tsx` |

### 4.10 Shared UI Components (new)

| Item | File(s) |
|---|---|
| collapsible.tsx | `src/components/ui/collapsible.tsx` |
| zodiac icon index | `src/components/ui/icons/zodiac/index.ts` |
| star-rating.tsx | `src/components/ui/star-rating.tsx` |

---

## §5 — True-Collision Inventory

Three items genuinely collide (both branches define different content):

### 5.1 `platform/src/lib/retrieve/query_panchanga.ts`

**Main's version (SQL cache path):**
- Reads from `panchanga_daily` Postgres table via `getStorageClient().query()`
- Input: date/range params + 7 SQL filter params (tithi, tithi_name, paksha,
  moon_nakshatra, vara_lord, yoga, karana) + limit + fields
- Output: one flat ToolBundleResult per row, containing 5 limbs + sunrise metadata
- Logging: `writeToolExecutionLog` to monitoring
- ~230 lines

**Feature branch's version (sidecar-direct path):**
- POSTs to `${PYTHON_SIDECAR_URL}/api/compute/panchanga`
- Input: date, lat, lon, tz_offset_minutes, chart_id, fields, range
- Output: 5 ToolBundleResult entries per day (five_angas, timings, special_yogas,
  planets_at_sunrise, choghadiya_hora) — richer per-section structure
- No SQL dependency; requires PYTHON_SIDECAR_URL env var
- Error type: `RetrievalToolError` (custom class, exported)
- ~290 lines

**Why they conflict:** Same tool name, same version string, completely different
backends. Only one can occupy `platform/src/lib/retrieve/query_panchanga.ts`.

### 5.2 `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` — R-TC rule at line 678

**Main's R-TC:** "TRANSIT-CONTEXT ENRICHMENT" — attaches `query_ephemeris` to any
non-natal query. 46 lines. Few-shot 4.25 = "R-TC transit-context — historical LEL
event" (Saturn at marriage).

**Feature branch's R-TC:** "TRANSIT-CONTEXT ROUTING — Panchang vs. Ephemeris
disambiguation" — routes between the two tools. 35 lines. Few-shot 4.25 =
"Panchang query — single date, auspicious timing."

**Why they conflict:** Same rule label (`R-TC`), same insertion line (678), completely
different semantics. The feature branch's R-TC is a routing rule; main's R-TC is an
enrichment rule. They cannot coexist under the same name. Additionally:
- Both added a "4.25" few-shot with different content at the same example slot.
- Feature branch also adds R-PCI at the same line block (novel, no collision).

### 5.3 `platform/src/lib/retrieve/__tests__/query_panchanga.test.ts`

**Main's test:** Mocks `@/lib/storage` → SQL `mockQuery`; tests SQL filter params,
CURRENT_DATE default, empty-row diagnostic, ToolBundle shape. 5 test cases.

**Feature branch's test:** Mocks `global.fetch` (sidecar); tests five_angas section,
special_yogas section, range endpoint routing, `RetrievalToolError` on HTTP failure
and missing env var. 14 test cases; also exports `RetrievalToolError`.

**Why they conflict:** Both test the same module (`../query_panchanga`) but with
incompatible mock strategies — SQL vs fetch. Only one test file can be correct once
the implementation decision is made.

---

## §6 — Reconciliation Recommendation

### 6.1 Options evaluated

**Option R (replace):** Feature branch's sidecar tool supersedes main's SQL tool +
panchanga_daily precompute.
- Advantage: single tool, full richness, all data in one response.
- Problem 1: Loses filtered range queries across 200 years — "find all Saturdays
  in Pushya nakshatra in 2027" requires iterating 365 live sidecar calls. The SQL
  index makes this ~2ms; live calls make it infeasible for LLM query budgets.
- Problem 2: Destroys 73K-row precomputed asset (already live on main, already tested,
  already seeded). This is the 4C-2 deferred win that main already delivered.
- Problem 3: Every planner query incurs ~200ms sidecar latency; SQL is ~5ms.
- **Rejected.**

**Option L (layer):** Keep main's SQL tool + R-PA as the query path; add our net-new
layer on top without touching the query tool.
- Advantage: least conflict — only touch R-PA (add missing triggers) and ship all
  net-new files.
- Problem: The /panchang UI page and Muhurat Finder need special yogas, timings,
  and planets — data the SQL tool doesn't return. The UI would need to call the
  sidecar directly anyway (which the feature branch already does via /api/panchanga).
  So the sidecar path is required regardless. This makes R-PA alone insufficient for
  chat queries about rahu kalam / special yogas / choghadiya — the planner still
  needs a path to that data.
- Option L is viable ONLY if we accept that special-yoga chat queries ("Is Sarvartha
  Siddhi present today?") route to the SQL tool, which returns nothing for those
  fields → synthesis answers with no evidence.
- **Rejected** for chat-query correctness; the missing data path is unacceptable.

**Option H (hybrid): RECOMMENDED.**
Keep main's SQL tool as the primary query path for the 5-limb + filtered search case.
Extend the SQL precompute (one migration + bootstrap update) to add special yogas,
inauspicious windows, and key timings as a JSONB column in `panchanga_daily`. This
enables the planner tool to return the richer fields without a live sidecar call for
every query. The sidecar path (live engine via /api/panchanga) remains the data source
for the /panchang UI page and Muhurat Finder, which need the freshest computation
and accept higher latency.

### 6.2 Option H: architecture detail

```
┌─────────────────────────────────────────────────────────────────┐
│  PLANNER TOOL PATH (query_panchanga.ts — main's SQL version)    │
│  panchanga_daily table (extended):                              │
│    5 limbs + sunrise   ← already there                         │
│    special_yogas JSONB ← NEW: migration 061 + bootstrap update  │
│    inauspicious JSONB  ← NEW: Rahu Kalam, Yamagandam, Gulika    │
│    auspicious JSONB    ← NEW: Brahma Muhurta, Abhijit           │
│  Latency: ~5ms SQL. Supports filtered range queries.            │
└─────────────────────────────────────────────────────────────────┘
        ↑ planner calls query_panchanga tool
        
┌─────────────────────────────────────────────────────────────────┐
│  UI + MUHURAT PATH (sidecar-direct, live)                       │
│  /panchang page → /api/panchanga → sidecar → panchang_engine    │
│  Muhurat Finder → /api/compute/muhurat → sidecar → muhurat.py   │
│  Full richness: choghadiya, hora, planets, native context       │
│  Latency: ~200ms. No filter. Accepts it (UI use case).          │
└─────────────────────────────────────────────────────────────────┘
```

**query_panchanga.ts (main's version, extended):** Add 3 optional output fields
when `fields` includes `special_yogas` | `inauspicious` | `auspicious`:
pull from the new JSONB columns. The interface stays SQL-backed; the new columns
are populated by the extended bootstrap. Filter params (tithi, nakshatra, etc.)
continue to work unchanged.

**Planner PROMPT changes under Option H:**
- Main's R-TC: KEEP UNCHANGED. It's the ephemeris enrichment rule; no collision.
- Main's R-PA: EXTEND trigger list to include the 13 missing terms (rahu kalam,
  choghadiya, etc., special yoga names, "panchang for today"). Rename nothing.
- Feature branch's R-TC: DO NOT USE (it was the disambiguation rule for the sidecar
  path; the hybrid architecture restores R-PA as the primary panchanga trigger).
- Feature branch's R-PCI: ADD after R-PA as a new rule (novel, no collision; it's
  the context-inheritance skip that saves a tool call when /panchang injects context).
- Few-shot renumbering: Feature branch's 4.25 (panchang auspicious timing) →
  renumber to 4.28 (after main's 4.25–4.27). Feature branch's 4.26 (Rahu Kalam)
  → 4.29. Feature branch's 4.27 (mixed panchang+ephemeris) → 4.30.

### 6.3 Rationale for rejecting alternatives

Option R destroys a working 73K-row precomputed asset and eliminates the range-filter
query path — a capability the SQL tool uniquely enables for the planner. Option L
leaves the planner unable to answer special-yoga / rahu-kalam queries from evidence,
which is a B.10 violation (no fabricated computation). Option H preserves both
capabilities, adds the missing richness to the SQL cache via a small schema extension,
and keeps the sidecar as the UI/muhurat path where latency is acceptable.

**Schema extension cost:** bootstrap_panchanga.py currently processes 73K dates in
batch mode. Calling `special_yogas.detect_all_special_yogas()` + `compute_inauspicious_timings()`
per date adds ~50ms/date of compute → ~60 minutes for a full rebuild. This is a one-time
operator cost, then the JSONB columns are cached permanently. The panchang_engine already
passes 230 tests including `test_special_yogas.py` — the code is production-ready.

---

## §7 — Re-Scoped Ship Session Plan

Replaces the original PSHIP-S1–S4 plan (which assumed a simpler integration).

**Total sessions: 5** (S2H–S6H, excluding S1 which is now PRECON-S1+PSHIP-S1 combined).
**Autonomous sessions: 3** (S2H, S3H, S5H).
**Human decision gates: 2** (S4H planner prompt, S6H deploy).

---

### PSHIP-S2H — Shared-file merge (19 files, no collision)

**Scope:** Apply all LOW + MED risk shared-file changes excluding `query_panchanga.ts`,
`query_panchanga.test.ts`, and `PLANNER_PROMPT_v2_0.md`. Follow
`PSHIP_CONFLICT_MAP.md §5` execution order (items 1–15 of that order, skipping #16).

**Files touched:** 17 files (see PSHIP_CONFLICT_MAP §4 table — all LOW+MED except
the 3 collisions above and PLANNER_PROMPT).

**Key actions:**
- `package.json`: add `ical-generator` + `npm install`
- `python-sidecar/main.py`: append panchang + muhurat router imports/registrations
- `AppShellRail.tsx` + `MobileNavSheet.tsx`: insert /panchang nav entry
- `.env.example` + `.env.local.example`: insert SESSION_SECRET
- `test-setup.ts`: insert next/navigation mock (after grep-check)
- `system-prompts.ts`: insert panchang_context block (verify blindMode still present)
- `OverviewClient.tsx`: insert panchang observatory panels
- `retrieve/index.ts`: verify-only (main already has queryPanchanga import)
- `CAPABILITY_MANIFEST.json`: insert PANCHANG_DAILY entry + increment entry_count
- `consume/page.tsx`: insert buildPanchangInitialMessages
- `.geminirules` + `.gemini/project_state.md`: insert 4C entries + R7/R8/R9 parity
- `CURRENT_STATE_v1_0.md`: append 4C session history (check version numbering)
- `SESSION_LOG.md`: append 1607-line 4C session history
- `CLAUDE.md`: merge §E; human review before commit on this file alone
- `PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md`: apply 4C close-out state

**Gate:** TypeScript typecheck zero errors; `npm run build` clean; panchang_engine
pytest still 230/230.

**Autonomous:** YES (except CLAUDE.md which needs native review per conflict-map §2.3).

---

### PSHIP-S3H — Query tool reconciliation (panchanga_daily schema extension)

**Scope:** Extend the SQL precompute to include special yogas + inauspicious +
auspicious windows. Reconcile `query_panchanga.ts` and `query_panchanga.test.ts`.

**Key actions:**
1. Write migration 061 to add three JSONB columns to `panchanga_daily`:
   - `special_yogas JSONB` — array of yoga objects with name/start_utc/end_utc/strength
   - `inauspicious JSONB` — array of window objects (rahu_kalam, yamagandam, gulika)
   - `auspicious JSONB` — array of window objects (brahma_muhurta, abhijit)
2. Update `bootstrap_panchanga.py` to call `panchang_engine` for the 3 new columns per date
3. Extend `query_panchanga.ts` (main's SQL version) to:
   - Add `special_yogas`, `inauspicious`, `auspicious` to `PanchangaField` enum
   - Project new JSONB columns when requested in `fields`
4. Keep main's test file as the SQL mock base; add test cases for the 3 new fields
5. Drop feature branch's `query_panchanga.ts` sidecar implementation — the SQL tool
   supersedes it under Option H. The sidecar path remains live for the UI via
   `/api/panchanga` route (untouched — it's A-classified, already transplanted).

**Gate:** main's 5 existing SQL tests pass; new field tests pass; typecheck clean;
bootstrap dry-run succeeds for a 7-day range sample.

**Autonomous:** YES.

---

### PSHIP-S4H — Planner prompt merge (HUMAN DECISION GATE)

**Scope:** Merge `PLANNER_PROMPT_v2_0.md`. Requires native approval.

**Key actions:**
1. Keep main's R-TC (transit-context enrichment) UNCHANGED at line 681.
2. Extend main's R-PA trigger list to include the 13 missing terms:
   - Add to (d): "Yoga / karana by name — including Sarvartha Siddhi, Amrit Siddhi,
     Guru Pushya, Ravi Pushya, Tripushkar, Dwipushkar, Siddha, Bhadra, Panchaka"
   - Add new sub-trigger (f): "Inauspicious window queries: 'rahu kalam', 'yamagandam',
     'gulika', 'brahma muhurta', 'abhijit', 'amrit kalam', 'choghadiya', 'hora'"
   - Add new sub-trigger (g): "'panchang for today', 'today's panchang', 'panchang for
     [date]' — direct panchang data requests"
3. Add R-PCI rule (feature branch) after R-PA — insert verbatim; it's novel.
4. Renumber feature branch few-shots: 4.25→4.28, 4.26→4.29, 4.27→4.30.
   Main's 4.25 (R-TC LEL event), 4.26 (R-PA Purnima), 4.27 (R-TE transit search)
   are kept at their existing positions.
5. Update version footer.

**Human judgment required:**
- Approve R-PA extension trigger list (does native want the full list of special
  yoga names as explicit triggers, or a more generic phrase?)
- Confirm R-PCI rule text from feature branch is acceptable as-is.
- Approve few-shot renumbering.

**Gate:** Planner routing tests in `platform/tests/planner/panchang_routing.test.ts`
(transplanted A-file) must pass.

**Autonomous:** NO — human review and approval before commit.

---

### PSHIP-S5H — Integration verification

**Scope:** End-to-end verification pass before PR.

**Actions:**
- panchang_engine pytest 230/230 (+ new bootstrap tests)
- TypeScript typecheck zero errors across platform/
- `npm run build` clean
- Planner routing tests pass
- Observatory panels render (if dev server available)
- migration 061 dry-run against a test DB instance (or verify SQL syntax only)

**Gate:** All checks green before PSHIP-S6H.

**Autonomous:** YES.

---

### PSHIP-S6H — PR creation and deploy (HUMAN GATE)

**Scope:** Push `feature/panchang-ship` to remote, create PR against main, coordinate
deploy sequence.

**Deploy sequence notes:**
- Apply migration 061 (new JSONB columns) BEFORE deploying
- Run `bootstrap_panchanga.py` with `--rebuild` for the 3 new columns after migration
  (operator ~60 min compute; existing rows get NULL for new columns until rebuild completes;
  acceptable — tool falls back gracefully on null JSONB columns)
- Feature flags for panchang features (if needed): confirm with native

**Autonomous:** NO — requires human push/PR/deploy authorization.

---

## §8 — Disposition of PSHIP-S1's Work

PSHIP-S1 transplanted 129 A-classified files and left 3 A-RECLASSIFIED→M files
at their main versions. Under Option H:

### 8.1 Files that survive unchanged (KEEP — 127 files)

All transplanted A-files that are pure additive survive under any reconciliation option:
- All `/panchang` UI page components (27 files)
- All `panchang_engine` library + tests (31 files)
- All `routers/panchang.py` + `routers/muhurat.py` (2 files)
- All `panchang/` client libraries (9 files)
- All `/api/panchanga`, `/api/compute/muhurat`, `/api/panchang/*` routes (7 files)
- All observatory panels (3 files)
- All new UI components — collapsible, star-rating, zodiac icons (3 files)
- All test artifacts (14 files)
- All architecture docs, phase briefs, close docs (31 files)
- `HANDOFF.md`, `HANDOFF_WAVE_1.md`, `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (3 files)

**Specifically: the /api/panchanga Next.js route (A-classified, transplanted) is
essential — it's the proxy to the sidecar for the UI path. KEEP.**

### 8.2 Files handled by PSHIP-S3H (supersede, not drop)

| Transplanted File | Status | Action in PSHIP-S3H |
|---|---|---|
| `query_panchanga.ts` (A-RECLASSIFIED→M) | NOT transplanted — main's SQL version is on branch | Extend main's version; feature branch's sidecar implementation not used as planner tool |
| `query_panchanga.test.ts` (A-RECLASSIFIED→M) | NOT transplanted — main's SQL test is on branch | Keep main's SQL tests; add new-field tests; discard feature branch's fetch-mock tests |

Note: because PSHIP-S1 correctly reclassified these as M and left main's versions in
place, there is nothing to "drop." Main's versions are already on the branch. PSHIP-S3H
extends them.

### 8.3 What PSHIP-S1's conflict map remains valid for

`PSHIP_CONFLICT_MAP.md` §2–§4 execution order is still valid for PSHIP-S2H.
The only entries that change under this spec:
- §6.2 query_panchanga.ts "replace main's version with source branch's" → REVERSED.
  Main's SQL version is kept; feature branch's sidecar version is not used as the
  planner tool.
- §6.3 query_panchanga.test.ts "replace main's test suite" → REVERSED.
  Main's SQL tests are kept and extended.
- §1 PLANNER_PROMPT integration → MODIFIED per §7 PSHIP-S4H (R-TC stays; R-PA extended;
  R-PCI added; no rename of main's R-TC required; feature branch's R-TC not inserted).

Everything else in PSHIP_CONFLICT_MAP.md (§2.1–§3.9) is correct and PSHIP-S2H executes
it as-is.

---

## §9 — Summary: Decision Points for Native Review

Before re-scoped ship sessions begin, native must decide:

| # | Decision | Recommended answer |
|---|---|---|
| D1 | Accept Option H (hybrid)? | YES — keep SQL tool + extend schema |
| D2 | Accept schema extension (migration 061 + bootstrap ~60min)? | YES — one-time cost, permanent win |
| D3 | R-PA extended trigger list acceptable? | YES with native review of specific terms |
| D4 | R-PCI rule text from feature branch acceptable verbatim? | YES — review at PSHIP-S4H |
| D5 | Few-shot renumbering 4.25→4.28 etc.? | YES |
| D6 | Feature branch's sidecar query_panchanga.ts: confirm NOT used as planner tool? | YES — UI uses sidecar directly; planner uses SQL tool |

Native approval of this spec is the gate for PSHIP-S2H to begin.

---

*End PANCHANG_RECONCILIATION_SPEC_v1_0.md — produced PRECON-S1, 2026-05-20.
All 8 analysis items completed. Recommendation: Option H (hybrid). Re-scoped plan:
PSHIP-S2H through PSHIP-S6H (5 sessions; 3 autonomous, 2 human-gated).*
