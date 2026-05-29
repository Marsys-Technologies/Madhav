---
artifact: A7_DASHAS_SPEC_v1_0.md
document: A7 — Dashas Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed 7-system acharya selection; 1950-2100 window; no history audit; no partitioning at ≤20-user scale)
intended_for: Claude Code sub-agents implementing the A7 dasha writer to chart_dashas table
prime_directive: Only computed facts. No narrative, no opinion. Two-pass verification MANDATORY on every row.
depends_on: A1 engine (Moon nakshatra, all graha longitudes), A3 §8 chart_dashas schema, G15 dasha-system rule library, G24 Vimshottari starting-lord, G44 Nadi tables (for special-dasha cross-checks), G2 ephemeris (for transit overlays)
---

# A7 — Dashas Specification

## §0 — Mission

For each chart per ayanamsha, compute the full timeline (1950-01-01 → 2100-12-31) for **7 acharya-selected dasha systems** at Prana depth (5 levels). Every row two-pass verified. Stored in `chart_dashas` table (A3 §8). Supports `query_dasha_branch_at_date` and concurrent-system queries.

## §1 — Locked decisions

| # | Decision | Locked |
|---|---|---|
| Q1 | Depth | **A — Prana (5 levels) for all 7 systems** |
| Q2 | Partitioning | **Defer per A3 §16. Revisit at 200 charts.** Scope: ≤20 users × ~5 charts = ~100 charts max → ~360M rows total → comfortable single-table |
| Q3 | History audit | **Skip chart_dashas_history.** Dashes are deterministic from engine inputs; reproducible without history table |
| Q3+ | Calculation window | **1950-01-01 → 2100-12-31** for all systems; backdate cycles for natives born after 1950 to cover pre-birth period; truncate after 2100 |
| Q4 | Tajik annual storage | **Hybrid: past + current + next 5 years pre-computed; rest on demand per varshphal query** |
| Q5 | Special dashes | Trimmed to **Kalachakra only** per acharya selection (§3). Sphuta/Vidhanottari/Hadda dropped. |
| Q7 | KP sub-divisions | **Emit KP sub-period rows under Vimshottari** (8-fold KP sub-divisions per nakshatra-pada lord) |
| Q8 | Sandhi window | **Per-system configurable; defaults to 5%** |

## §2 — Additions A-Q (from §6 of A7 review) — locked subset

| ID | Addition | Included? |
|---|---|---|
| A | Per-period lord context embedded inline (lord_natal_house_d1, sign, nakshatra, dignity_d1, shadbala_total) | **YES** |
| B | Sandhi-next-dasha explicit (sandhi_with_next_dasha_lord field) | **YES** |
| C | Cross-system concurrency annotations (jsonb of all other systems' current lords at this row's start) | **YES** |
| D | Convergence count at start (derivable from C; included as trivial annotation) | **YES** |
| E | System applicability declared explicitly (applies_to_this_chart_flag) | **YES — architecturally necessary** |
| F | Period deity/marker (Yogini named yoginis, Kalachakra cycle markers) | **YES** |
| G | Antar-lord relationship to Maha-lord (friend/enemy/neutral) | **YES** |
| H | Tajik year-lord cross-reference | **YES** |
| I | Kalachakra solar-return anchor (anchored_solar_return_iso) | **YES** |
| J | Triggered yogas per period (jsonb_atomic — deterministic predicate firing from G12 yoga library) | **YES** |
| K | Lord's transit state at period start (cheap G2 lookup; stored, not recomputed) | **YES** |
| L | KP sub-divisions emitted as additional rows under Vimshottari | **YES** |
| M | Sphuta-style Pravesha timestamps | **SKIP** |
| N | Naisargika age-anchoring beyond standard fields | **SKIP** (covered by standard fields) |
| O | Periodic shubha/ashubha composite classification | **SKIP** (predicate could be opinion-flavored; prime directive) |
| P | Maha-Antar compatibility composite score | **SKIP** (could violate prime directive) |
| Q | Per-period karakas active during period | **YES** |

## §3 — 7 acharya-selected dasha systems

| # | system_id | Class | Cycle | Why this one |
|---|---|---|---|---|
| 1 | `vimshottari` | Nakshatra-based | 120y, 9 lords | Universal default. 95%+ of professional astrologers. Foundation of all timing. |
| 2 | `yogini` | Nakshatra-based | 36y, 8 yoginis | Short-cycle refinement. Widely used as cross-check. |
| 3 | `ashtottari` | Nakshatra-based | 108y, 8 lords | Applies in specific Krishna paksha + nakshatra conditions. Complementary canonical. |
| 4 | `chara_karaka` | Jaimini sign-based | Variable per signs | Modern Jaimini essential. KN Rao's contribution. Most consequential Jaimini dasha. |
| 5 | `naisargika` | Age-based | 120y fixed brackets | Life-stage anchor. No chart-dependence — purely age-based cross-reference. |
| 6 | `mudda` | Tajik annual | Per-varsha (~9K rows/year) | Year-specific predictions. Hybrid storage (past+current+next-5y pre-computed). |
| 7 | `kalachakra` | Special | 100y complex w/ paramayush | Classical longevity (BPHS Ch.53). Essential life-span context. |

**Dropped (24 systems):** All other nakshatra-based (Shodashottari/Dvadashottari/Panchottari/Shatabdika/Chatturashitika/Dvisaptati/Shashtihayani/Shatatrimshat/Tara), 11 other Jaimini (Sthira/Niryana Shoola/Trikona/Brahma/Vimsa/Sudasa/Drig/Mandukya/Padakrama/Brahma-variant), 3 other Tajik (Patyayini/Sahama/Yogini-annual), 3 other special (Sphuta/Vidhanottari/Hadda). **None used routinely in acharya practice.**

## §4 — chart_dashas row schema (A3 §8 base + A7 additions)

A3 §8 base fields (recap): `dasha_row_id, chart_id, ayanamsha_id, build_id, system_id, level_n (1-5), parent_row_id, lord_graha, lord_sign, start_date, end_date, start_iso, end_iso, duration_days, sandhi_flag, karaka_role_at_period, verification_pass_status, verification_method, citation_ref, citation_human, computed_at, engine_version`.

**A7 additions (per §2 included items):**

```sql
-- Lord natal context inline (Addition A)
lord_natal_house_d1            INT
lord_natal_sign                TEXT
lord_natal_nakshatra           TEXT
lord_natal_dignity_d1          TEXT
lord_natal_shadbala_total      NUMERIC

-- Sandhi-next-dasha (Addition B)
sandhi_with_next_dasha_lord    TEXT
next_dasha_start_iso           TIMESTAMPTZ

-- Cross-system concurrency (Additions C + D)
concurrent_system_lords_jsonb  JSONB    -- {vimshottari: SAT, chara: VEN, yogini: MAR, ...}
convergence_count_at_start     INT      -- count of systems agreeing on this row's lord_graha at start_date

-- Applicability (Addition E)
applies_to_this_chart_flag     BOOLEAN  -- false for systems not applicable (e.g., Ashtottari conditions)

-- Period deity/marker (Addition F)
period_deity_or_marker         TEXT

-- Antar-lord relationship to Maha-lord (Addition G)
lord_to_parent_relationship    TEXT     -- 'friend' | 'enemy' | 'neutral' (composite)

-- Tajik year-lord cross-reference (Addition H)
varsha_year_lord               TEXT     -- only set for Tajik annual rows

-- Kalachakra solar-return anchor (Addition I)
anchored_solar_return_iso      TIMESTAMPTZ  -- only set for Kalachakra rows

-- Triggered yogas per period (Addition J)
triggered_yogas_jsonb_atomic   JSONB    -- list of yogas from G12 that activate during this period

-- Lord transit state at period start (Addition K)
lord_transit_at_period_start_jsonb JSONB  -- {sign, nakshatra, longitude_sidereal, retrograde_state}

-- Karaka activation (Addition Q)
karakas_active_during_period   TEXT[]    -- subset of 8 karakas active at any level in this branch
```

## §5 — KP sub-divisions under Vimshottari (Addition L)

KP astrology subdivides Vimshottari periods into KP sub-levels via 27-fold nakshatra subdivision applied recursively. For each Vimshottari L1-L5 row, emit additional KP-flavored sub-rows:

```sql
-- KP sub-level rows (extension of level_n model)
level_n                         INT     -- extended: 1-5 = standard Vimshottari; 6 = KP sub; 7 = KP sub-sub
kp_sub_lord                     TEXT    -- only set on level_n=6 rows
kp_sub_sub_lord                 TEXT    -- only set on level_n=7 rows
```

KP sub-row depth: typically 6 (sub-lord) is sufficient for production; 7 (sub-sub) emitted only for Vimshottari L1 + L2 to keep row count tractable.

Row count impact: Vimshottari L5 alone is ~59K rows; adding L6 (KP sub) under each = ~530K; full L7 only on L1+L2 = ~6K. Total Vimshottari with KP: ~600K instead of ~66K. **~10× row inflation for Vimshottari.**

## §6 — Calculation window (Q3+ explicit rule)

For every dasha system:
- `start_date` filter: ≥ 1950-01-01
- `end_date` filter: ≤ 2100-12-31
- Native born **before 1950**: compute from 1950 only (don't backdate further)
- Native born **between 1950-2100**: backdate cycles to 1950 (pre-birth lord assignment per backward-cycle walk from Moon nakshatra elapsed at birth)
- Native born **after 2100**: out-of-scope (system design assumes natives born ≤ 2100)

For each row stored in chart_dashas, both `start_iso ≥ 1950-01-01` AND `end_iso ≤ 2100-12-31` must hold; periods spanning 1950 or 2100 boundary are truncated to the window.

## §7 — Verification methodology (per system, declared in CHART_FACTS_SCHEMA.json)

Mandatory `verification_pass_status ∈ {two_pass_verified, classical_match}`. Halt on `divergent_flagged`.

| System | Primary | Secondary | Tertiary | Halt tolerance |
|---|---|---|---|---|
| Vimshottari | Engine nakshatra-elapsed | Independent re-derivation from Moon-nakshatra-pada × cycle-table | Sage Parashara worked example (BPHS Ch.47) match | ±1 day at L5 Sookshma; ±10 sec at L5 Prana |
| Yogini | Engine 8-cycle | Independent classical-rule | Algebraic invariant: sum = 36y | ±1 day |
| Ashtottari | Engine 108y cycle | Independent (lord sequence: Sun/Moon/Mars/Mercury/Saturn/Jupiter/Rahu/Venus) | Algebraic invariant: sum = 108y | ±1 day |
| Chara Karaka | Engine Jaimini sign-progression | Independent classical (Jaimini Sutram Ch.2) | KN Rao worked example match | ±1 day |
| Naisargika | Engine age-based bracket assignment | Independent classical | Algebraic invariant: 120y total | ±1 day |
| Mudda | Engine within-varshphal | Independent Tajik rule | Algebraic | ±1 day |
| Kalachakra | Engine paramayush + deha/jeeva | Independent BPHS Ch.53 algorithm | Classical worked example (BPHS Ch.53 examples) match | ±5 days at L5 |

## §8 — Citations (dual form per A3 §6)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Vimshottari Saturn Maha (Lahiri) | `chart_dashas.vimshottari.L1.SAT@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Vimshottari Saturn Mahadasha (Lahiri): 2003-04-12 → 2022-04-12." |
| Sun-Saturn Antar | `chart_dashas.vimshottari.L2.SAT-SUN@chart=...:ay=lahiri:...` | "Saturn-Sun Antardasha (Lahiri): 2014-09-22 → 2017-09-22." |
| KP sub under Vimshottari | `chart_dashas.vimshottari.L6.SAT-SUN-MAR@chart=...:ay=lahiri:...` | "Vimshottari Saturn-Sun-Mars KP sub-period (Lahiri): 2015-06-15 → 2015-08-23." |
| Yogini Mangala | `chart_dashas.yogini.L1.MAR-Mangala@chart=...:ay=lahiri:...` | "Yogini Mangala Mahadasha (Lahiri): 1984-11-22 → 1985-11-22; deity: Mangala." |
| Chara AK dasha | `chart_dashas.chara_karaka.L1.<sign>@chart=...:ay=lahiri:...` | "Chara dasha Capricorn period (Lahiri): 2015-03-10 → 2027-03-10." |
| Kalachakra | `chart_dashas.kalachakra.L1.<sign>@chart=...:ay=lahiri:...` | "Kalachakra Capricorn period (paramayush-anchored, Lahiri): 1984-02-05 → 2002-04-18." |

## §9 — Row count projection (with all trims)

| System | Rows per (chart, ayanamsha) |
|---|---|
| Vimshottari (standard L1-L5) + KP sub (L6) + KP sub-sub (L7 on L1+L2 only) | ~600K |
| Yogini (Prana depth × ~4 cycles in 150y) | ~150K |
| Ashtottari (Prana depth × ~1.4 cycles) | ~46K |
| Chara Karaka (Prana depth, variable cycle) | ~50K |
| Naisargika (5 levels × fixed brackets) | ~1K |
| Mudda (hybrid: past + current + next-5y pre-computed, ~11 years × 9K) | ~100K |
| Kalachakra (Prana depth × ~1.5 cycles) | ~120K |

**Total per (chart, ayanamsha): ~1.07M rows**
**× 5 ayanamshas = ~5.4M rows per chart**

For 100 charts (≤20 users × 5 charts): **~540M rows total** — well within Postgres single-table comfort.

## §10 — Tool retrieval contract

- `query_dasha_branch_at_date(chart_id, ayanamsha_id, system_id, date)` → 5 rows (L1-L5 branch) or 7 (with KP sub for Vimshottari)
- `query_concurrent_dashas_at_date(chart_id, ayanamsha_id, date)` → 7 rows (one L1 per system)
- `query_dasha_lord_lifetime(chart_id, ayanamsha_id, system_id, lord_graha)` → all periods where this graha is lord at any level
- `query_dasha_sandhi_windows(chart_id, ayanamsha_id, system_id)` → sandhi windows for this system
- `query_dasha_triggered_yogas(chart_id, ayanamsha_id, system_id, level_n, lord_graha)` → triggered_yogas_jsonb_atomic for this period

## §11 — Materialized views

**None.** Per A3 §10 rule: chart_dashas IS the precomputed timeline. Direct indexed queries are single-millisecond. No MV needed.

The original A3 §10 listing of `mv_chart_dasha_at_date` was correctly removed earlier (it was parametric on query_date = time-varying).

## §12 — Implementation notes

1. G15 dasha-system rule library extension: ensure all 7 systems' rules are encoded
2. KP sub-division logic: implement 27-fold recursive subdivision per nakshatra-pada lord
3. Backdating logic for natives born > 1950: backward-cycle walk from Moon nakshatra-elapsed at birth
4. Triggered yogas computation per period: pre-compute G12 yoga firing conditions × per-period chart-state snapshot
5. Two-pass verification gates per system; halt with `divergent_flagged` on tolerance breach
6. Sandhi window default 5%, per-system configurable via `system_config_jsonb` column on chart_dashas (optional)
7. Lord transit state at period start: single G2 ephemeris lookup per row; cheap
8. Cross-system concurrency: post-pass after all 7 systems compute; join across systems on start_date to populate concurrent_system_lords_jsonb

## §13 — Locked decisions (final committed surface)

1. 7 dasha systems (Vimshottari + Yogini + Ashtottari + Chara Karaka + Naisargika + Mudda + Kalachakra)
2. Depth: Prana (5 levels) for all 7; KP sub-divisions extend Vimshottari to L7 (sub + sub-sub)
3. Calculation window: 1950-01-01 → 2100-12-31 only
4. Storage: chart_dashas single table; no partitioning at ≤20-user scale; revisit at 200 charts
5. History: no chart_dashas_history (deterministic from inputs)
6. Tajik annual: hybrid storage (past + current + next-5y pre-computed; rest on demand)
7. Two-pass verification MANDATORY per A3 §8
8. 13 of 17 row-additions A-Q included (M, N, O, P skipped)
9. ~5.4M rows per chart × 100 charts = ~540M total at peak (within Postgres comfort)
10. No materialized views — chart_dashas IS the timeline

---

*End of A7_DASHAS_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
