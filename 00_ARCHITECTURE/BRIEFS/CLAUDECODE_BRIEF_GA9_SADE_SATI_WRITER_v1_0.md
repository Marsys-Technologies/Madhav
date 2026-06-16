---
artifact: CLAUDECODE_BRIEF_GA9_SADE_SATI_WRITER_v1_0.md
canonical_id: GA9_SADE_SATI_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 4, asset ga_sade_sati — smallest by rows, heaviest atomic-grain scrutiny)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A9_SADE_SATI_SPEC_v1_0.md (LOCKED — category authority)
depends_on: GA3 (schema), GA4 (panchanga + Tara bala baseline), GA6 (D10 Karya), GA7 (concurrent dashas all 7 systems), GA8 (argala matrix + Saturn-Moon natal yoga modifier), G2 ephemeris, G4 eclipses, G21 Saturn-sign-changes reference
---

# GA9 — Sade Sati Cycles Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A9_SADE_SATI_SPEC_v1_0.md` — **the category authority.** ~15 categories (§2), per-row fields incl. many JSONB (§3), 8 cancellation rules (§4), quarter intensity (§5), per-category two-pass (§6), row-count ~875/chart (§7), citations (§8), 1 MV (§9), tool contract (§10), implementation walk (§11).
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` — schema, **atomic grain (this writer tests it hardest)**, prime directive, FORENSIC gate.
- `00_ARCHITECTURE/GA8_T1_STRUCTURAL_WRITER_v1_0.md` — supplies argala + Saturn-Moon natal yoga modifier GA9 cross-references.

## §1 — Reality reconciliation (apply over the older spec)

A9 LOCKED 2026-05-29. **Translate:**

1. **Engine = `panchanga_engine`/swisseph (DE441) for Saturn transit detection 1950–2100**, PyJHora for natal Moon/Saturn — not `natal_engine`. **No JH-parity oracle** — two-pass is ephemeris-vs-G21-reference-table + algebraic invariant (~7.5y per cycle ±30 days).
2. **Asset id = `ga_sade_sati`.** Target table = **`chart_facts`** (the campaign storage map; A9 names `sade_sati_natal_baseline` precomputed lifetime windows per A3 §10 — store the cycle/phase/quarter rows in chart_facts). All categories ayanamsha-DEPENDENT → 5 rows per key. Window 1950–2100 (A7 Q3+ rule).
3. **Postgres-direct. No audience tier. Floors aspirational** — ~875 is a target. Compute the real cycles for the native (Moon in Purva Bhadrapada / Aquarius — so Sade Sati cycles key off Saturn transiting Capricorn→Aquarius→Pisces, the 12H/1H/2H from Aquarius). Never fabricate a cycle.

## §2 — Branch + topology

- Branch `feature/ga9-sade-sati-writer` off `main` **after GA3, GA4, GA6, GA7, GA8 land** (GA9 cross-references all of them). One PR when green.
- Target chart_id = **`482012f1-710e-4a25-994a-93821f5871aa`** (canonical; keyed). Parameterize. `362f9f17` dead — note A9's example "natal Moon in Aquarius" is consistent with the native (Moon nakshatra Purva Bhadrapada spans Aquarius/Pisces; the Moon's *sign* per ayanamsha must be read from GA3, not assumed).
- Dependency-strict: Step 0 verifies upstream rows exist for `482012f1` (GA7 dasha rows for concurrent overlay; GA8 argala; GA6 D10 Karya; GA4 Tara bala baseline). Halt-clean if absent.

## §3 — The ~15 categories (A9 §2 — implement every one)

`sade_sati_cycle` (CYCLE_1/2/3), `sade_sati_phase` (Vishakha/Janma/Anumukha per cycle), `sade_sati_phase_quarter` (Q1–Q4 per phase = 12/cycle), `dhaiya_period` (4H + 8H), `kantaka_shani_period` (4H), `ashtama_shani_period` (8H), `ardha_ashtama_shani_period`, `janma_shani_period` (peak), `vishakha_shani_period` (entry 12H), `anumukha_shani_period` (exit 2H), `sade_sati_saturn_retrograde_subset` (retrograde windows within phase, Q5), `sade_sati_cancellation_check` (per cycle + phase), `sade_sati_modifier_overlay` (concurrent Mars/Jupiter/Rahu/eclipse/Saturn-return), `sade_sati_concurrent_dasha_overlay` (all 7 systems from GA7), `sade_sati_downstream_cross_reference` (D10 Karya + argala + Tara bala).

All 8 cancellation rules (A9 §4), per-quarter High/Medium/Low intensity (A9 §5, BPHS Ch.71 + Phaladeepika + pada modifier), all Additions A–V.

## §4 — Atomic grain — THE critical gate for this writer (GA3 §5)

A9 §3 lists **many JSONB fields** — most must become **atomic columns/keys**, NOT blobs. The atomic-grain gate (campaign §E) scrutinizes GA9 hardest. Convert:
- All the per-period boolean flags (mars_aspect/jupiter_aspect/saturn_rahu_axis/eclipse_during_period/concurrent_saturn_return/…) → **atomic bool keys**, queryable individually.
- All the concurrent-dasha-lord fields (vimshottari_maha/antar, yogini, ashtottari, chara, naisargika, mudda, kalachakra) → **atomic text keys** (a reviewer must `WHERE concurrent_vimshottari_maha_lord='SAT'`).
- Saturn state during period (sign/dignity/nakshatra/pada/retrograde) → atomic keys.
- Quarter intensity classification → atomic text key; the *rationale rule-set* → sanctioned JSONB (`quarter_intensity_rationale_jsonb`) since the rule SET is the irreducible atom.

**Sanctioned JSONB ONLY:** `saturn_nakshatra_transitions_jsonb_atomic` (event-trigger windows list), `quarter_intensity_rationale_jsonb` (rule-set), `cancellation_rules_invoked_jsonb` (which of 8 fired — a set), `d10_karya_activation_facts_jsonb` (fact_id refs), `argala_during_period_jsonb` (matrix subset = set). Everything a `WHERE` should hit = atomic. Document each JSONB use with the irreducibility justification in code comments.

## §5 — Two-pass verification (A9 §6 — mandatory two_pass_verified)

Saturn sign-entry/exit timestamps: ephemeris detection vs G21 Saturn-sign-changes reference, ±30 days / ~7.5y invariant. Retrograde subsets vs G5 retrograde table. Concurrent modifiers vs independent G2+G4. Cancellation predicates vs independent classical re-derivation. Quarter intensity: BPHS Ch.71 vs Phaladeepika cross-check. Concurrent dashas: GA7 join vs independent dasha computation. `divergent_flagged` → halt.

## §6 — FORENSIC + native-specific grounding

The cycles MUST key off the native's actual natal Moon **sign per ayanamsha** (read from GA3 — Purva Bhadrapada spans Aquarius/Pisces, so the sign may differ by ayanamsha at the boundary; this is a real cross-ayanamsha divergence to capture, not an error). Saturn-over-natal-Moon (Janma peak) timestamps must reproduce from ephemeris. Do NOT copy A9's illustrative dates ("2nd cycle starts 2027-09-22", "Janma peak 2030-03-14") uncritically — compute for `482012f1` and verify against G21. The `~7.5y per cycle` invariant is the hard structural check.

## §7 — Materialized view (A9 §9)

`mv_chart_sade_sati_lifetime_summary` (natal-fixed; all cycles/phases wide per chart,ayanamsha). Refresh synchronous at build close. **NO** `mv_chart_sade_sati_active_at_date` (parametric on query_date = time-varying, forbidden per A3 §10).

## §8 — Build-state wiring

On success update `asset_throughput` for `ga_sade_sati` (chart_id `482012f1`): row count + state transition. chart_id targeted = keyed.

## §9 — Acceptance criteria (all `[verify-against: prod]`)

1. Upstream present (GA3/GA4/GA6/GA7/GA8 rows for `482012f1`); halt-clean if absent. `[verify: psql existence]`
2. `CHART_FACTS_SCHEMA.json` contains the ~15 A9 categories; drift_detector GREEN. `[verify: drift]`
3. All ~15 categories emitted ×5 ayanamsha; cycles key off the native's per-ayanamsha Moon sign (cross-ayanamsha divergence captured at the Aquarius/Pisces boundary). `[verify: psql + sample]`
4. **Atomic-grain GREEN**: per-period flags + concurrent-dasha-lords + Saturn-state are atomic columns/keys (queryable); only the 5 sanctioned JSONB fields hold sets, each justified. `[verify: jsonb audit — hardest gate]`
5. All 8 cancellation rules evaluated per cycle + phase; quarter intensity High/Med/Low per BPHS Ch.71 + pada modifier. `[verify: sample]`
6. Concurrent-dasha overlay references all 7 GA7 systems correctly. `[verify: join check]`
7. Every category `two_pass_verified` (zero `divergent_flagged`); ~7.5y/cycle invariant holds. `[verify: psql + invariant]`
8. FORENSIC: Janma peak reproduces from ephemeris; cycle count for native consistent. `[verify: assertion]`
9. `mv_chart_sade_sati_lifetime_summary` refreshes; no time-varying MV created. `[verify: \dm]`
10. `asset_throughput` ga_sade_sati updated, keyed to `482012f1`; cockpit bar moves. `[verify: cockpit + psql]`
11. CI green; merge-verify before done.

## §10 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, **atomic-grain (the defining discipline for this writer — 5 sanctioned JSONB only, each justified)**, two-pass-every-row, deterministic accuracy over volume, floors aspirational, never fabricate a cycle, dependency-strict. Halt on upstream-missing, two-pass divergence, ~7.5y invariant breach, any unjustified JSONB blob.

---

*End of GA9 brief v1.0. Smallest by rows (~875), heaviest atomic-grain scrutiny — the writer that proves the atomic-grain rule under maximum JSONB temptation.*
