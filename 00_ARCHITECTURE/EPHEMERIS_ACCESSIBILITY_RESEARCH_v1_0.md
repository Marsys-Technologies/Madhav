---
artifact: EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0
canonical_id: EPHEMERIS_ACCESSIBILITY_RESEARCH
version: 1.1
status: APPROVED — execution plan authored at PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md
author: Claude (analysis stream)
authored_on: 2026-05-18
amended_on: 2026-05-18
mirror_pair: none
scope: research-dossier-only
related: RETRIEVAL_TOOLS_CONSOLIDATED_VIEW.html (peer artifact), retrieval_capability_spec.ts, PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md (execution plan)
changelog:
  - v1.0 (2026-05-18): initial dossier
  - v1.1 (2026-05-18): native approved §6 decisions; added §6.5 transit-context heuristic; status → APPROVED
---

# Ephemeris Accessibility — Research Dossier

## §0 Purpose

The native uploaded a full ephemeris CSV to GCS so that planetary positions for any date (1900–2100) could be looked up rather than recomputed on the fly. Phase 3 of the analysis campaign surfaced a coverage gap: the planner can reach ephemeris data only for forward-looking transit windows. This dossier maps (a) what data we actually have, (b) what Swiss Ephemeris (the upstream tooling) can give us, (c) which of those capabilities are planner-reachable today, and (d) where the gaps are. It closes with a phased enrichment proposal.

This is a research document, not an execution plan. Concrete briefs land separately once the native approves a scope.

## §1 What we have today

### §1.1 The CSV at GCS

`gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv` — `sha256:a0e8fbac0178610faa00fcbdc4f63b89b4071d8936ce8691eafb57ebb2a9791a` — also mirrored at `01_FACTS_LAYER/EPHEMERIS_MONTHLY_1900_2100.csv` (1.7 MB · 21,709 rows · uploaded 2026-04-29).

Schema:

| Column | Type | Example |
|---|---|---|
| `date_utc` | YYYY-MM-DD | `1900-01-01` (1st of each month) |
| `planet` | text | `Sun`, `Moon`, …, `Rahu`, `Ketu` (9 grahas) |
| `abs_long` | decimal | sidereal longitude 0–360° (Lahiri) |
| `sign` | text | `Sagittarius` |
| `deg_in_sign` | decimal | 0–30° |
| `deg_fmt` | text | `17°41'16"` |
| `nakshatra` | text | `Purva Ashadha` |
| `pada` | int | 1–4 |
| `retrograde` | Y/N | `N` |
| `speed_deg_per_day` | decimal | `1.01976` |

The CSV is **monthly** resolution (1st-of-month sample) — 201 years × 12 months × 9 planets = 21,708 rows + header. It does **not** serve as the production source; it is a verification spot-check only (see §1.3).

### §1.2 The Postgres production table — `ephemeris_daily`

Migration `015_ephemeris_daily.sql`. Schema:

```sql
CREATE TABLE ephemeris_daily (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  planet TEXT NOT NULL,              -- lowercase 'sun'..'ketu'
  longitude_deg NUMERIC(11,7),
  latitude_deg NUMERIC(11,7),
  speed_deg_per_day NUMERIC(11,7),
  is_retrograde BOOLEAN,
  sign TEXT,
  sign_degree NUMERIC(11,7),
  nakshatra TEXT,
  nakshatra_pada SMALLINT,
  ayanamsha TEXT DEFAULT 'lahiri',
  ephemeris_version TEXT,            -- 'pyswisseph-2.10.03.2'
  build_id TEXT REFERENCES build_manifests(build_id),
  UNIQUE(date, planet)
);
CREATE INDEX idx_ephemeris_date ON ephemeris_daily(date);
CREATE INDEX idx_ephemeris_planet_date ON ephemeris_daily(planet, date);
CREATE INDEX idx_ephemeris_retro ON ephemeris_daily(planet, date) WHERE is_retrograde = TRUE;
```

Population: **9 planets × 73,050 days = ~657,450 rows** for 1900-01-01 → 2100-12-31, daily resolution, midnight UT, Lahiri sidereal.

What it captures: planet longitude + latitude, speed, retrograde flag, sign + sign-degree, nakshatra + pada, ayanamsha + ephemeris version + build provenance.

What it does **not** capture: combust state, dignity, vargottama, sign-ingress markers, panchanga elements (tithi/vara/karana/yoga), planet-to-planet aspect angles, house position (depends on observer lat/lon — not denormalized).

### §1.3 The loader — `bootstrap_ephemeris.py`

`platform/python-sidecar/pipeline/bootstrap_ephemeris.py`.

Authoritative source: **`pyswisseph` (Swiss Ephemeris Python binding)**, not the CSV. The script iterates dates 1900-01-01 → 2100-12-31, calls `swe.calc_ut(jd, planet_id, FLG_SIDEREAL | FLG_SPEED)` for each (date, planet) pair, derives sign/nakshatra/pada from the longitude, and upserts via `INSERT … ON CONFLICT (date, planet) DO UPDATE`. Lahiri ayanamsha set globally via `swe.set_sid_mode(swe.SIDM_LAHIRI)`.

The CSV is consulted only for a 100-row random spot-check at start of the run (0.01° tolerance against Swiss Ephemeris's recomputed value). If the GCS object is absent, the cross-check is skipped and the residual recorded.

Convention notes:

- **Rahu = `swe.TRUE_NODE`** (in `bootstrap_ephemeris.py`) vs **Rahu = `swe.MEAN_NODE`** (in `routers/ephemeris.py`, `compute_kp.py`, `compute_varshaphala.py`). This is an inconsistency — the production daily ephemeris uses TRUE_NODE, but most other compute paths use MEAN_NODE. Classical Jyotish typically uses MEAN. A future hygiene item.
- **Ketu** = Rahu + 180° (mirrored ecliptic latitude).
- Rahu/Ketu marked `is_retrograde=true` by Jyotish convention regardless of TRUE_NODE's variable speed sign.
- Midnight UT (not local IST). Native is asia/south1; any "transit on day X" interpretation has to apply the UT→IST offset (+5:30) downstream if precise.

### §1.4 The Python sidecar endpoints

`platform/python-sidecar/main.py` registers:

| Endpoint | Router | What it does |
|---|---|---|
| `POST /ephemeris` | `routers/ephemeris.py` | Computes **natal** chart positions on the fly via pyswisseph (uses `MEAN_NODE`). Inputs: birth_date, birth_time, lat/lng, ut_offset. |
| `POST /event_chart_states` | `routers/events.py` | LEL event chart-state hydration. |
| `POST /eclipses` | `routers/eclipses.py` | Eclipse table queries. |
| `POST /retrogrades` | `routers/retrogrades.py` | Retrograde period queries. |
| `POST /sade_sati` | `routers/sade_sati.py` | Sade Sati phase queries (Saturn over natal Moon). |
| `POST /jaimini_drishti` | `routers/jaimini.py` | Jaimini aspect queries. |
| `POST /v7_additions` | `routers/v7_additions.py` | Misc helpers. |
| `POST /dasha_chain` | `routers/dasha_chain.py` | 5-level Vimshottari MD/AD/PD/SD/PD2 at a date. |

Notably **`/ephemeris` is natal-only** — it does not query `ephemeris_daily` for arbitrary dates. The `temporal` retrieval tool that the planner can select calls `/transits` and `/ephemeris` for today's UT (forward-looking branch in `temporal.ts`); it does not query `ephemeris_daily` by date either.

### §1.5 What batch-compute scripts produce (Postgres-resident)

Eight pyswisseph-backed compute scripts at `platform/scripts/temporal/`:

| Script | Output table | Coverage | Planner-reachable? |
|---|---|---|---|
| `compute_transits.py` | `ephemeris_daily` (this dossier) | 1900–2100 daily | Via `temporal` (forward-only, not historical) |
| `compute_kp.py` | `kp_sublords` | Native chart | Yes — `query_kp_ruling_planets` |
| `compute_vimshottari.py` | `dasha_periods` | Native life span | Via `temporal` dasha branch |
| `compute_yogini.py` | (Yogini dasha) | Native life span | **No** |
| `compute_chara.py` | (Jaimini Chara dasha) | Native life span | **No** |
| `compute_narayana.py` | (Narayana dasha) | Native life span | **No** |
| `compute_varshaphala.py` | `varshaphala` | 1984–2061 annual | Yes — `query_varshaphala` |
| `compute_shadbala.py` | `chart_facts` (shadbala rows) | Native chart | Via `chart_facts_query` category=shadbala |

### §1.6 The planner-reachability map for ephemeris data

| Query class | Reachable today? | Through |
|---|---|---|
| Natal planet positions | Yes | `/ephemeris` sidecar (when wired from temporal — currently only for forward-looking) |
| Today's transit positions | Yes | `temporal` → `/transits` |
| Planet position on a specific historical date | **No** | Closest is `query_planet_position` (legacy Claude tool-use, not in RCS) or direct SQL (not planner-callable) |
| Planet position on a specific future date | Partially | `temporal` calls `/ephemeris` only with `forward_looking=true` AND `time_window` set |
| Planet position across a date range (e.g., daily for a month) | **No** | Same |
| Was planet X retrograde on date Y? | **No** for arbitrary Y | `temporal.retrograde_query` returns retrograde windows; `ephemeris_daily.is_retrograde` direct lookup not planner-reachable |
| Combust planets on date X | **No** | Not computed; would need Sun-longitude diff + classical thresholds |
| When does Mars enter Capricorn next? | **No** | No ingress-search tool |
| When does Saturn next aspect natal Moon? | **No** | No aspect-search tool |
| Sign-ingress events for a year | **No** | No ingress lookup |
| Panchanga (tithi/vara/karana/yoga/nakshatra) for date X | **No** | Not computed |
| Current dasha chain at date X | Yes | `/dasha_chain` via temporal |
| Eclipses in window | Yes | `temporal.eclipse_query` |
| Sade Sati phase at date X | Yes | `temporal.sade_sati_query` |
| KP sub-lord chain | Yes | `query_kp_ruling_planets` |
| Annual Varshaphala | Yes | `query_varshaphala` |

Net: the entire 657K-row `ephemeris_daily` table is unreachable by the planner for date-indexed queries.

## §2 What Swiss Ephemeris can provide (upstream capability inventory)

Source library: C library by Astrodienst (Zurich), Python binding `pyswisseph`. Based on JPL DE441/DE431; covers 13201 BCE → 17191 CE with sub-arcsecond precision when JPL/Swiss data files are present.

### §2.1 What we currently use

| API | Used in |
|---|---|
| `swe.calc_ut(jd, ipl, flags)` | All compute scripts + bootstrap |
| `swe.julday(y, m, d, ut)` | All compute scripts + bootstrap |
| `swe.set_sid_mode(SIDM_LAHIRI)` | All compute scripts + bootstrap |
| `swe.houses_ex(jd, lat, lon, 'P', FLG_SIDEREAL)` | `compute_shadbala.py`, `compute_chara.py`, `compute_narayana.py`, `compute_varshaphala.py` (Placidus only) |
| `FLG_SIDEREAL`, `FLG_SWIEPH`, `FLG_MOSEPH`, `FLG_SPEED`, `FLG_EQUATORIAL` | Various |
| `MEAN_NODE`, `TRUE_NODE` | KP uses MEAN; bootstrap_ephemeris uses TRUE (inconsistency, §1.3) |

### §2.2 What Swiss Ephemeris additionally exposes (and we don't use)

**Ayanamshas.** 42+ predefined modes including TRUE_CHITRA, TRUE_PUSHYA, TRUE_REVATI, KRISHNAMURTI, RAMAN, USHASHASHI, YUKTESHWAR, JN_BHASIN, SURYASIDDHANTA, ARYABHATA, plus user-defined offset. **We only use Lahiri.**

**House systems.** Codes for Placidus `P`, Koch `K`, Whole-sign `W`, Equal `E`/`A`, Sripati `S`, Porphyry `O`, plus 13 others. **We use Placidus only** — Bhava-chalit (Sripati `S`) and Whole-sign (`W`) are traditional Vedic alternatives we could surface.

**Fixed stars.** `swe.fixstar2_ut(name, jd, flags)` — ~800 stars including the nakshatra junction-stars (Spica/Chitra, Aldebaran/Rohini, Antares/Jyeshtha, Regulus/Magha, Algol/Krittika, etc.). **Unused.**

**Asteroids.** Ceres, Pallas, Juno, Vesta, Chiron, Pholus by built-in IDs (15–20). **Unused.**

**Eclipses (search).** `sol_eclipse_when_glob(jd, ifl, ifltype, backward)`, `sol_eclipse_when_loc(jd, geopos, …)`, `lun_eclipse_when(jd, ifl, backward)`. Returns full attribute set including saros, magnitude, obscuration, contacts. **We use static `eclipses` table; SE search would let us answer "when's the next solar eclipse?" or "is there an eclipse in March 2027?" with sub-arcsec timing without precomputing.**

**Risings/settings/transits.** `swe.rise_trans(jd_start, ipl, starname, epheflag, rsmi, geopos, atpress, attemp)` returns rise/set/upper-meridian-transit/lower-meridian-transit times. **Needed for sunrise-anchored panchanga vara.**

**Phase/elongation/magnitude.** `swe.pheno_ut(jd, ipl, flags)` returns phase angle, illuminated fraction, elongation from Sun (degrees), apparent diameter, apparent magnitude. **This is the foundation for classical combustion thresholds** (which differ per planet — Sun-Mercury < 12° awarm, < 14° cold, etc.).

**Coordinate transforms.** `swe.cotrans`, `cotrans_sp`. **For declination-based parallel/contraparallel aspect detection.**

**Time.** `swe.utc_to_jd` (UTC↔TT, leap-second-aware), `swe.deltat`, `swe.sidtime`. **Needed for precise UTC↔IST conversion and sidereal time at observer location.**

**`split_deg`.** Returns deg/sign/min/sec breakdown. **Already done in our code; could be replaced by the SE helper.**

**`solcross` / `mooncross`.** Compute next time Sun or Moon crosses a given longitude. **Foundation for sign-ingress search ("when does Sun next enter Aries?") and for Sankranti detection.**

### §2.3 What Swiss Ephemeris does NOT compute (caller-side derivations)

| Concept | SE provides | We must derive |
|---|---|---|
| Tithi (lunar day) | Sun + Moon longitudes | Yes — `(Moon - Sun) mod 360° / 12°` |
| Vara (day of week, sunrise-anchored) | `rise_trans` | Day index from sunrise |
| Karana (half-tithi) | tithi | tithi-based |
| Yoga (Sun+Moon) | Sun + Moon longitudes | `(Sun + Moon) mod 360° / 13.333°` |
| Nakshatra-pada of Moon at sunrise | calc_ut at sunrise | division by 3.333° |
| Vargas D1–D60 | D1 longitudes | Modular arithmetic per varga |
| KP sub-lord chain | calc_ut for Moon | Vimshottari proportions × nakshatra subdivisions |
| Ashtakavarga bindus | All planet longitudes | Classical rules per planet |
| Combustion | `pheno_ut` elongation + Sun longitude | Classical thresholds per planet (varies by Vedic school) |
| Dignity (uccha/mūla/svakṣetra) | longitudes | Static tables |
| Friendship (naisargika/tatkalika) | longitudes | Static + sign-position derived |
| Graha-yuddha (planetary war) | longitudes + latitudes | Within 1° + which planet "wins" |
| Avastha (10 states) | longitudes | Classical rules |
| All dasha systems | Moon nakshatra position | Vimshottari/Yogini/Chara/Narayana — we compute these already |
| Aspect timing | `calc_ut` iteration | Root-finding (no `next_aspect` API) |
| Sign-ingress events | `solcross`/`mooncross` only for Sun/Moon | Caller iterates for other planets |

## §3 Gap summary

Three classes of gap separate "what's possible" from "what the planner can do today":

### §3.1 Coverage gap — `ephemeris_daily` is invisible to the planner

The 657K-row daily ephemeris exists in Postgres but no planner-reachable retrieval tool reads from it. `query_planet_position` (legacy Claude tool-use stack) reads it directly, but it's not registered in `RETRIEVAL_TOOLS` or `RETRIEVAL_CAPABILITY_SPEC`. **Fix: wrap as a retrieval tool.**

### §3.2 Enrichment gap — derived state isn't denormalized

Even if we wrap the table, the planner would only get raw longitudes/signs. Derived state useful for synthesis (combust state, sign-ingress markers, dignity at date, vargottama at date, current-aspect partners) is not stored. **Fix: extend `ephemeris_daily` with computed columns or build a sibling `ephemeris_derived_daily` view.**

### §3.3 Search gap — no event-finding tool

The planner can ask "what is true on date X" but not "when does X next happen" — e.g., "when does Jupiter next enter Cancer?", "when does Saturn next conjunct natal Moon within 1°?". This requires either:

- An ingress-search retrieval tool that scans `ephemeris_daily` for sign-changes (denormalized at bootstrap time), OR
- A live-compute sidecar endpoint that uses `swe.solcross`/`mooncross` for Sun-Moon, root-finding for others, exposed as a retrieval tool.

## §4 Phased enrichment proposal

Four phases, sized in independent sessions; each can ship independently without breaking the others. The native picks scope.

### §4.A — Quick-win: `query_ephemeris` retrieval tool (1 session)

Wrap `query_planet_position` as a proper `RetrievalTool`. Tool name `query_ephemeris` (avoid name collision with structured-tool surface).

**Schema** (planner params):

```ts
{
  date?: string,            // YYYY-MM-DD, single date
  start_date?: string,      // YYYY-MM-DD, range start (alternative to date)
  end_date?: string,        // YYYY-MM-DD, range end
  planet?: PlanetName,      // omit for all 9
  planets?: PlanetName[],   // alternative to planet
  fields?: ('longitude' | 'sign' | 'nakshatra' | 'retrograde' | 'speed' | 'latitude')[],  // default all
  limit?: number,           // default 100, max 500
}
```

**Returns**: rows from `ephemeris_daily` with the requested fields. PLANNER_PROMPT R-rule trigger: any query that names a specific date or date range AND involves planets, transits, retrograde status, or nakshatra-of-Moon-on-a-day.

**Acceptance criteria**:
- `RETRIEVAL_TOOLS` registered
- `RETRIEVAL_CAPABILITY_SPEC` entry with optimal_patterns
- `ALL_21_RETRIEVAL_TOOLS` extended (closes the trace-display gap to 26 + 1 = 27, also fixes the 2-tool cosmetic gap from §1.6)
- 5 unit tests covering: single-date all-planets, single-date one-planet, date-range one-planet, invalid date, planet-name normalization
- Planner-only smoke test with 3 new golden-set entries:
  - "What was Saturn doing on my marriage day?" → planner picks `query_ephemeris` with date + `lel_query` for marriage date
  - "Was Mars retrograde in January 2019?" → planner picks `query_ephemeris` with date range + planet=mars
  - "Where was the Moon on the day of my graduation?" → planner picks `query_ephemeris` with date + planet=moon

**Estimated effort**: ~1 session.

### §4.B — Enrichment: derived columns in `ephemeris_daily` (1-2 sessions)

Extend the table (or build a view) with computed daily state. Migration `059_ephemeris_derived_columns.sql`:

| Column | Source | Use |
|---|---|---|
| `combust_status` | `pheno_ut` elongation + classical Sun-distance threshold | "Was Mercury combust on date X?" |
| `combust_orb_deg` | absolute degree-diff from Sun | "How combust was it — 3° or 14°?" |
| `dignity_d1` | sign + ownership tables | "Was Saturn exalted that day?" |
| `vargottama_today` | longitude mod 30° in D1 == sign in D9 | "Vargottama check" |
| `sign_ingress_today` | sign-change vs prior day | "When did Jupiter enter Aries?" |
| `nakshatra_change_today` | nakshatra-change vs prior day | Panchanga continuity |
| `pada_change_today` | pada-change vs prior day | Fine-grained transit timing |
| `graha_yuddha_with` | nullable planet name if within 1° of another | Classical war detection |

Backfill via a one-shot script `platform/python-sidecar/pipeline/enrich_ephemeris_daily.py` that runs after `bootstrap_ephemeris.py`. ~657K rows × <1ms compute = under 20 minutes.

The `query_ephemeris` tool (from §4.A) gains a `derived_fields` param to surface these.

**Estimated effort**: 1-2 sessions.

### §4.C — Panchanga: new `query_panchanga` retrieval tool (1 session)

Sunrise-anchored daily panchanga. Five elements: tithi, vara, nakshatra (Moon at sunrise), yoga, karana.

Two options:

**Option C1 (precomputed)**: Add `panchanga_daily` table (one row per date, ~73,050 rows). Computed once at bootstrap. Cheap reads.

**Option C2 (live compute)**: Sidecar endpoint `/panchanga` that uses `rise_trans` for sunrise time at native's birth location (or a standardized observer), then derives the 5 elements from Sun/Moon longitudes at sunrise.

C1 wins for date-indexed lookups; C2 wins if you want arbitrary observer locations later. The native-bound use case fits C1.

**Tool params**:

```ts
{
  date?: string,            // single date
  start_date?: string,
  end_date?: string,
  element?: ('tithi' | 'vara' | 'nakshatra' | 'yoga' | 'karana')[],
}
```

**Estimated effort**: ~1 session.

### §4.D — Live transit search (2 sessions)

`query_transit_event` retrieval tool, calling a new sidecar endpoint `/transit_search`.

Supported queries:

- **Ingress search**: "when does planet X next enter sign Y after date Z?"
- **Aspect search**: "when does planet X next aspect natal planet Y by angle A (within orb O)?"
- **Conjunction search**: "when do planet X and planet Y next conjoin within orb O?"
- **Retrograde station**: "when is planet X next at station retrograde / direct after date Z?"

The sidecar uses `swe.solcross`/`mooncross` for Sun/Moon longitude crossings (cheap) and root-finds via repeated `calc_ut` for other planets (more expensive). Caps at ±10 years from query date for latency reasons.

**Estimated effort**: ~2 sessions.

## §5 Ordering recommendation

If the native wants the minimum viable improvement that closes the ephemeris-accessibility gap surfaced at Phase 3 close:

1. **§4.A first** (1 session). Solves "what was Saturn doing on date X?" — the canonical use case. Closes the trace-display gap as a bonus.
2. **§4.B second** (1-2 sessions). Combust + dignity + vargottama enrichment unlocks much more accurate synthesis (e.g., "Mars was combust during your 2018 event, so the malefic activation was muted").
3. **§4.C third** (1 session). Panchanga matters for muhurta / electional queries and for any "what kind of day was that?" question.
4. **§4.D last** (2 sessions). Highest engineering cost; lowest-frequency query class. Defer unless transit-event queries surface in real traffic.

Total scope: 5-6 sessions to close ephemeris accessibility end-to-end. Phase A alone is the immediate fix.

## §6 Approved decisions (locked 2026-05-18 by native)

1. **TRUE_NODE → MEAN_NODE for Rahu in `ephemeris_daily`** — APPROVED. Fix folded into §4.B migration (one-time rebuild of 657K rows). Classical Jyotish convention; matches all other compute paths in the codebase; consistent with always-retrograde Vedic treatment.
2. **Panchanga sunrise observer → Native birth location (Bhubaneswar, 20.27°N 85.83°E)** — APPROVED. Internally consistent with FORENSIC + LEL chart_state hydration. M7 population-extension can introduce per-native sunrise later; not blocking.
3. **Combustion thresholds → BPHS classical (Parashara)** — APPROVED. Per-planet asymmetric orbs:
   - Sun-Moon: 12° · Sun-Mars: 17° · Sun-Mercury: 14° direct / 12° retrograde
   - Sun-Jupiter: 11° · Sun-Venus: 10° direct / 8° retrograde · Sun-Saturn: 15°
   - Source: BPHS Chapter 50. Documented in §4.B migration header.
4. **`query_ephemeris` shape → Single tool with optional date OR date_range params** — APPROVED. Matches the lel_query / query_signal_state / query_varshaphala pattern in the 26-tool RCS.
5. **Additional ayanamshas → No. Lahiri only.** APPROVED. FORENSIC v8.0, MSR, UCN, CDLM, every chart_fact + signal is anchored to Lahiri. Adding other ayanamshas would require recomputing 657K × N rows × 9 planets plus all derived state. Treat multi-ayanamsha as a future research workstream if ever needed.
6. **House systems → Add Whole-Sign as peer column; keep Placidus where wired; defer Bhava-Chalit** — APPROVED. Whole-Sign (Swiss Ephemeris code `W`) is the canonical Parashari bhava chart — most traditional acharyas read it. Add as a denormalized column in §4.B (or `houses_whole_sign` sibling table joined on date) so the planner can ask "what house is Saturn in by Parashari whole-sign on 2008-04-15?". Don't disturb the tested Placidus computations in shadbala/chara/narayana. Bhava-Chalit (Sripati `S`) deferred — refinement on top of Whole-Sign, not substitute.

## §6.5 Approved heuristic: transit-context enrichment for non-natal queries

The native surfaced this insight at v1.0 approval: most queries are not purely natal. A question about the present ("what's happening to me right now?"), the future ("when will my career take off?"), or a past event ("what was happening when I got married?") draws meaning from BOTH the natal chart (divisional charts give the natal position) AND the transit chart at the relevant moment (ephemeris gives the present/historical/future state). The planner must default to including ephemeris context for any non-natal query, not treat it as opt-in.

**Rule (new R-TC — Transit-Context, encoded in PLANNER_PROMPT in §4.A):**

For any query that is NOT a pure-natal-only question, attach `query_ephemeris` at priority 2 with the relevant date(s). Trigger sub-cases:

| Query temporal anchor | Date param |
|---|---|
| "now" / "currently" / "today" / "at this point" / "in my life right now" | `date = today UTC` |
| Specific past event that exists in LEL (marriage, job change, illness, etc.) | `date = LEL event date` (also attach `lel_query`) |
| Specific past date stated explicitly | `date = stated date` |
| Specific future date or event | `date = stated date` |
| Date range stated or implied ("next 2 years", "2026–2028", "this quarter") | `start_date + end_date` |
| Named dasha period (e.g., "Mercury AD 2025–2027") | `start_date + end_date` matching dasha window |

**Exclusion (the rule does NOT fire when):**

- Query is pure-natal with no temporal anchor: "what house is X in?", "what is my Y?", "describe my Z?", "what's my lagna lord?"
- Query is purely about classical interpretation: "what does Saturn in 10H mean classically?"
- Query is a remedial codex lookup: "what gemstone for Venus?"

This pairs with existing rules:

- R-TW1 (eclipse temporal scope) — keeps the `temporal` tool for eclipse-window queries, but R-TC now adds `query_ephemeris` for the Sun/Moon positions at the eclipse moment.
- R-TW2 (antardasha date-range scope) — keeps `time_window` semantics; R-TC adds the actual ephemeris lookup at the period boundaries.
- R7c (transit ban on vector_search for pure-timing queries) — unaffected; `query_ephemeris` and `vector_search` serve different purposes.

The result: every non-natal answer arrives at the synthesis layer with both (a) the native's natal positions from `chart_facts`/divisional_query and (b) the transit positions at the query's anchor date(s) from `query_ephemeris`. Synthesis can now actually compare natal-vs-transit, which is the foundation of every Vedic timing read.

## §7 Sources

- `platform/python-sidecar/pipeline/bootstrap_ephemeris.py` — production loader (this file).
- `platform/python-sidecar/routers/ephemeris.py` — `/ephemeris` POST natal endpoint.
- `platform/python-sidecar/routers/dasha_chain.py` — `/dasha_chain` POST.
- `platform/migrations/015_ephemeris_daily.sql` — table schema.
- `platform/src/lib/retrieve/temporal.ts` — current planner-facing tool.
- `platform/src/lib/tools/structured/query_planet_position.ts` — legacy Claude tool-use; the source of the wrap-as-RetrievalTool pattern for §4.A.
- `01_FACTS_LAYER/EPHEMERIS_MONTHLY_1900_2100.csv` — git-mirrored CSV.
- `verification_artifacts/MIGRATION_AUDIT/B_layer1/EPHEMERIS_MONTHLY.json` — GCS upload manifest (sha256 match).
- Swiss Ephemeris official docs:
  - https://www.astro.com/swisseph/swephinfo_e.htm — capability overview.
  - https://www.astro.com/swisseph/swephprg.htm — programmer's reference.
  - https://github.com/astrorigin/pyswisseph — Python binding source.
  - https://github.com/aloistr/swisseph — C source mirror.

## §8 Out of scope for this dossier

- Performance benchmarking (`ephemeris_daily` direct-SQL latency vs sidecar latency).
- License audit (Swiss Ephemeris is AGPL-3.0 or commercial; we likely need a commercial license for production SaaS — separate compliance question).
- Cross-school ayanamsha comparison study (research project, not infra).
- M6 prospective-testing integration (time-gated to ~2026-11-14; out of scope for analysis stream).

---

*End of EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0. Awaiting native scope-approval signal before authoring per-phase briefs.*
