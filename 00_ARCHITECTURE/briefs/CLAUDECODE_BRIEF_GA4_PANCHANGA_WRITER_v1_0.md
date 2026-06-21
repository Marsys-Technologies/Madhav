---
artifact: CLAUDECODE_BRIEF_GA4_PANCHANGA_WRITER_v1_0.md
canonical_id: GA4_PANCHANGA_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 2, asset ga_panchanga — persisted birth-instant panchanga)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md (LOCKED — category authority)
depends_on: GA3 (chart_facts schema + CHART_FACTS_SCHEMA.json must land first)
---

# GA4 — Panchanga (birth-instant) Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md` — **the category authority.** ~33 fact_categories (§2), per-category emission detail (§3), verification mins (§4), dual citations (§5), row-count projection (§9, ~600–800/chart), locked decisions (§10).
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` (this batch) — the chart_facts schema + atomic-grain rule + prime-directive enforcement GA4 obeys.
- `00_ARCHITECTURE/PANCHANGA_ENGINE_REARCHITECTURE_v1_0.md` — the L0 `panchanga_engine` service GA4 calls (`panchanga_instant`).
- `00_ARCHITECTURE/UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md` — build-state.

## §1 — Reality reconciliation (apply over the older spec)

A4 LOCKED 2026-05-29, before the panchang re-architecture and the engine/naming decisions. **Translate:**

1. **Panchang source = the L0 `panchanga_engine` service, via `panchanga_instant(...)`** — NOT `natal_engine/panchanga.py`. The re-architecture (PR #234, now on main `c78c0d45`) established `panchanga_engine/__init__.py` with `panchanga_instant(instant, lat, lon, tz_offset) → PanchangaInstant` (swisseph/DE441, deterministic, canonical for panchang). GA4 calls that one API at the birth instant and persists the result. This is the A4 "persisted panchanga_instant @ birth, 1:1" decision — **A4 is KEPT** (the earlier "drop A4" idea was reversed/VOID).
2. **Engine for chart-side bodies = PyJHora** where A4 needs graha rise/set/positions; panchang limbs come from `panchanga_engine`. No `natal_engine`. **No JH-parity oracle.**
3. **Asset id = `ga_panchanga`.** Target = `chart_facts` (the panchanga_* categories) — birth-instant, persisted 1:1 from the service call. (The *daily/forward* panchang is the L0 service + `/panchang` product; GA4 stores only the **natal instant**.)
4. **Postgres-direct.** Call `panchanga_instant`, persist atomic rows into `chart_facts`. No JSONL.
5. **No audience tier. Floors aspirational** — A4's "~600–800 rows" is a target; chase genuine deterministic limbs/windows, floor un-computable topics to absent (`computed:false` / null), never fabricate.

## §2 — Branch + topology

- Branch `feature/ga4-panchanga-writer` off `main` **after GA3 merges** (needs `CHART_FACTS_SCHEMA.json` + chart_facts DDL). One PR when green.
- Target chart_id (RESOLVED) = **`482012f1-710e-4a25-994a-93821f5871aa`** (confirmed canonical 2026-06-10; only real native row; `asset_throughput` already keyed; no re-keying). Pass as a parameter; no longer a halt condition. **`362f9f17-…` is a dead phantom** — the specs' `chart=362f9f17` citation examples are placeholders, not a real id; write `482012f1-…`.
- Birth coordinates (invariant): **1984-02-05T10:43:00 IST, lat 20.27, lon 85.84, tz_offset +5:30** (Bhubaneswar). Pass these to `panchanga_instant`.

## §3 — Categories to emit (A4 §2 — the full locked set)

**Ayanamsha-INVARIANT** (`ayanamsha_id='INVARIANT'`, 1 row per key) — the Sun-Moon-separation-based limbs + day-structure windows:
`panchanga_tithi`, `panchanga_vara`, `panchanga_yoga`, `panchanga_karana`, `panchanga_hora_birth`, `panchanga_choghadiya_birth`, `panchanga_rahu_kalam`, `panchanga_yamaganda_kalam`, `panchanga_gulika_kalam`, `panchanga_durmuhurta`, `panchanga_varjyam`, `panchanga_visha_ghati`, `panchanga_sashtighati`, `panchanga_yamakantaka`, `panchanga_krakaca`, `panchanga_abhijit_muhurta`, `panchanga_brahma_muhurta`, `panchanga_pratah_sandhya`, `panchanga_madhyahna_sandhya`, `panchanga_sayam_sandhya`, `panchanga_amrit_kaal`, `panchanga_vijaya_muhurta`, `panchanga_godhuli_muhurta`, `panchanga_nishita_kala`, `panchanga_solar_context`, `panchanga_calendrical`, `panchanga_astronomical`, `panchanga_sun_moon_dynamics`, `panchanga_disha_shul`, `panchanga_tithi_shoonya_rashi`, `panchanga_nakshatra_shoonya_rashi`, `panchanga_agni_vasa`.

**Ayanamsha-DEPENDENT** (5 rows per key, one per canonical ayanamsha) — nakshatra-shifted at boundaries:
`panchanga_nakshatra_moon`, `panchanga_special_yoga_combinations`, `panchanga_panchaka_classification`, `tara_bala_natal_baseline` (27-row state table), `chandra_bala_natal_baseline` (12-row state table), `panchaka_flag`, `bhadra_flag`, `eclipse_proximity_natal`.

Per-category key detail is in **A4 §3 verbatim** — implement every key listed there (tithi: name/number/paksha/type/deity/lord/percent_elapsed/pravesh_iso/arambha_iso/inauspicious_flag; nakshatra_moon: 17 keys incl. gana/nadi/yoni/pakshi/varna/tatva/paramayus; the 9 inauspicious + 9 auspicious windows with start_iso/end_iso/duration_minutes; etc.). Do not summarize away keys.

## §4 — Atomic grain (GA3 §5 — binding here too)

Every key = its own row. The 27-row Tara bala baseline = **27 rows** (subject `TRANSIT_NAK_<NAME>`, key `tara_class`), the 12-row Chandra bala = **12 rows** (subject `TRANSIT_SIGN_<NAME>`). The 5 panchakas = 5 rows + 1 overall. A window's start/end/duration = separate keys. JSONB only for the genuinely irreducible (e.g., `special_yoga_combinations.constituent_facts_jsonb_atomic` tithi+vara+nakshatra triple; `eclipse.natal_points_within_1deg_array`).

## §5 — Mapping A4 categories to the service output

The `panchanga_instant` rich-output contract (PR #235, 22/23 topics built) supplies most limbs/windows directly. **Map service fields → A4 categories**; do not recompute what the service already returns:
- Service `five angas` → `panchanga_tithi/_vara/_nakshatra_moon/_yoga/_karana`.
- Service inauspicious windows → `_rahu_kalam/_yamaganda_kalam/_gulika_kalam/_durmuhurta/_varjyam/…`.
- Service auspicious windows → `_abhijit_muhurta/_brahma_muhurta/_amrit_kaal/…`.
- Service choghadiya/hora → `_choghadiya_birth/_hora_birth`.
- Service calendrical (masa, samvat ×4, samvatsara, ritu, ayana, sankranti) → `_calendrical/_solar_context`.
- Service rise/set + planetary state → `_astronomical/_sun_moon_dynamics`.
- Service Anandadi/Vasa/Panchaka/Shoonya → `_special_yoga_combinations/_agni_vasa/_panchaka_classification/_tithi_shoonya_rashi/_nakshatra_shoonya_rashi`.

For the **1 floored topic** (whichever PR #235 left `computed:false`) and any A4 category the service doesn't supply: emit the row with null value + the row's own marker reflecting un-computed status, OR omit — **never fabricate**. Document which A4 categories map to floored service topics.

**Tara/Chandra bala baselines** are NOT in the instant service output — they're a join of the native's natal nakshatra/sign × the global G22/G23 reference matrices (per A4 §3, §8.5). Compute these in the writer from the native's Moon nakshatra (Purva Bhadrapada) / Moon sign × the reference tables.

## §6 — Verification (A4 §4)

- `single` for Swiss-Ephemeris-authoritative limbs (tithi/vara/yoga/karana/nakshatra, rise/set, solar context, calendrical, Tara/Chandra matrices — static reference).
- `two_pass_verified` for table-driven windows (inauspicious/auspicious), special-yoga combinations, panchaka classification, Agni Vasa (modular arithmetic + table). Pass-2 = independent re-derivation; on divergence → `divergent_flagged`, halt.

## §7 — FORENSIC grounding gate (hard correctness gate)

The panchang limbs ARE four of the FORENSIC anchors — this writer is where they're directly checked:
- Tithi **Shukla Tritiya** · Vara **Ravivara** · Yoga **Shiva** · Karana **Garaja** · Moon nakshatra **Purva Bhadrapada**.

`panchanga_instant` at the native birth instant MUST return these. If any diverges → halt, `CONDUCTOR_HALT_LOG.md`, escalate. (This also independently validates the L0 panchang service against the natal anchor — a useful cross-check.)

## §8 — Citations (A4 §5)

Both forms per row. Correct the stale citation-engine string — use the real PyJHora/`panchanga_engine` version at runtime, not `natal_engine/0.2.0`. Human form example: "Tithi at birth: Shukla Tritiya." / "Moon's nakshatra at birth: Purva Bhadrapada (Lahiri)." / "Agni Vasa at birth: Bhumi (Earth)." / "Rahu Kalam on birth day: 16:30–18:00 IST."

## §9 — Materialized view (A4 §7)

`mv_chart_panchanga_birth_summary` — wide row per (chart, ayanamsha) joining all `panchanga_*`. Refresh synchronous at build close. NO MV for Tara/Chandra bala at transit date (those compute live from the baseline state tables × transit Moon).

## §10 — Build-state wiring

On success update `asset_throughput` for `ga_panchanga` (canonical chart_id): row count + state transition. Cockpit bar moves. chart_id targeted = chart_id keyed (§GA3 §11).

## §11 — Acceptance criteria (all `[verify-against: prod]`)

1. `panchanga_instant(1984-02-05T10:43 IST, 20.27, 85.84, +5:30)` returns FORENSIC-consistent angas (Shukla Tritiya / Purva Bhadrapada / Shiva / Garaja / Ravivara). `[verify: assertion]`
2. All A4 §2 categories emitted into `chart_facts` for the native: invariant categories at `ay='INVARIANT'`, dependent categories ×5 ayanamsha. `[verify: psql GROUP BY fact_category, ayanamsha_id]`
3. Every A4 §3 key present per category (no key dropped); atomic rows (Tara=27, Chandra=12, panchaka=5+1). `[verify: psql count per category]`
4. Floored/un-computable topics are null + marked, **zero fabricated values**. `[verify: null audit + no-narration linter]`
5. Two-pass categories all `two_pass_verified` (zero `divergent_flagged`). `[verify: psql GROUP BY verification_pass_status]`
6. Both citations non-null, human form renders correctly, engine string is real (not natal_engine). `[verify: sample]`
7. `mv_chart_panchanga_birth_summary` refreshes at build close. `[verify: \dm + count]`
8. `asset_throughput` ga_panchanga updated, keyed to canonical chart_id; cockpit bar moves. `[verify: cockpit + psql]`
9. Atomic-grain + prime-directive gates GREEN. CI green; merge-verify before done.

## §12 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, atomic-grain, deterministic accuracy over volume, floors aspirational, never fabricate. Halt on FORENSIC failure, two-pass divergence, unresolved chart_id, or service unavailability.

---

*End of GA4 brief v1.0. Persists the birth-instant panchanga 1:1 from the L0 service into chart_facts.*
