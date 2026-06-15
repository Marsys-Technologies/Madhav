---
artifact: CLAUDECODE_BRIEF_GA6_VARGAS_WRITER_v1_0.md
canonical_id: GA6_VARGAS_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 3, asset ga_vargas — the largest L1 writer by row volume)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A6_VARGAS_SPEC_v1_0.md (LOCKED — category authority)
depends_on: GA3 (chart_facts schema + CHART_FACTS_SCHEMA.json), G16 Varga formula library, G41 Lal Kitab corpus, G44 Nadi tables
---

# GA6 — Vargas (Divisional Charts) Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A6_VARGAS_SPEC_v1_0.md` — **the category authority.** 30-varga set (§1), 8 locked Q-answers + 11 additions A–K (§2), ~25 fact_categories (§3), per-row enrichment (§4), per-category two-pass methodology (§5), dual citations (§6), row-count ~78,750/chart (§7), 2 MVs (§8), tool contract (§9), implementation notes (§10). **A6 §11: bumps the running enum to ~172 categories — GA3's `CHART_FACTS_SCHEMA.json` must include the ~25 A6 categories before this writer completes.**
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` — schema, atomic grain, prime directive, FORENSIC gate.
- `00_ARCHITECTURE/L1_GANITA_BUILD_CAMPAIGN_v1_0.md` — §A principles, §D conductor (context-decay protection matters here — biggest writer), §E gate-validators.

## §1 — Reality reconciliation (apply over the older spec)

A6 LOCKED 2026-05-29. **Translate:**

1. **Engine = PyJHora** (`pyjhora_adapter`), not `natal_engine`. PyJHora natively computes the named vargas. **The 6 generic vargas without a named PyJHora function** (per the earlier varga reconciliation — D5/D6/D8/D11/D14/D15 or whichever the adapter lacks) use a **generic `custom_divisional_chart(longitude, divisor)` function** (pure arithmetic: each sign's 30° split into `divisor` parts, mapped per the Parashari cyclic rule). **D2700 uses a custom function** — it's computable arithmetic beyond PyJHora's ~300-division cap (D2700 = 90 parts/sign; the cap is incidental, not a correctness limit). No `natal_engine`. **No JH-parity oracle** — two-pass is formula-vs-independent-re-derivation.
2. **Asset id = `ga_vargas`.** Target table = **`chart_divisionals`** (NOT chart_facts — this is the campaign storage map; verify the table's columns match the atomic-grain shape, extend via migration if needed). All categories ayanamsha-DEPENDENT → 5 rows per key.
3. **Postgres-direct, no JSONL.**
4. **No audience tier. Floors aspirational** — "~78,750 rows" is a target. Chase the full 30-varga × 25-category matrix with genuine deterministic formulas. If a specific deity/rishi attribution table is missing (D60/D40/D45/D108/D150/D2700), floor that attribution to absent (marked) rather than fabricate; still emit the position.

## §2 — Branch + topology

- Branch `feature/ga6-vargas-writer` off `main` **after GA3 merges**. One PR when green.
- Target chart_id = **`482012f1-710e-4a25-994a-93821f5871aa`** (confirmed canonical; `asset_throughput` keyed). Pass as parameter. `362f9f17` is dead — specs' `chart=362f9f17` examples are placeholders.
- **This is the largest writer (~78K rows)** — the conductor's context-decay protection (campaign §D) applies hardest here: batch the 30 vargas across sub-agent re-kicks, persist progress to build-state between batches, never hold the full row set in one context window. Write incrementally + idempotently so a re-kick resumes, not restarts.

## §3 — The 30 vargas (A6 §1 — all computable, none dropped)

- **Parashari 16 (Shodasavarga):** D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.
- **Supplementary 11:** D5, D6, D8, D11, D14, D15, D21, D32, D33, D50, D54.
- **Nadi 3:** D108, D150, D2700.

Per the varga reconciliation: 24 are named PyJHora functions; 6 generic use `custom_divisional_chart`; D2700 uses the custom fn. D9-sub-amsa D81 is **SKIPPED** (A6 §2 row J).

## §4 — The ~25 categories (A6 §3 — implement every one)

Implement all 25 from A6 §3 with their subjects. Do not drop entries. Key ones:
- `varga_position` (25 bodies × 30 vargas — the bulk; subject `<VARGA_ID>.<BODY>`), `varga_dignity`, `varga_vargottama_flag`.
- Cross-varga harmonics (post-pass, after all per-varga positions written): `varga_super_vargottama_flag` (same sign ≥3 vargas), `varga_trikona_vargottama_flag`, `varga_trans_vargottama_count`.
- `varga_pushkara_navamsa_flag` + `varga_pushkara_bhaga_flag` (D9-only split per Q7).
- `varga_house_lord`, `varga_house_occupant`, `varga_aspect_matrix` (every varga — heavy), `varga_ashtakavarga` (every varga where formula applies), `varga_rollup` (9 fields/varga).
- `varga_deity_attribution` (D60 60 deities BPHS Ch.7 exact table, D40/D45 devatas, D30 5-lord regions, D20/D24/D16/D9/D3/D2 attributions, D50/D54, D108 karma-type).
- `varga_formula_variant_position` (D3 Drekkana 3 variants Parashari/Jaimini/Mooltrikona; D2 Hora 2 variants Parashari/Jaimini — separate `formula_id` rows per Q8).
- `varga_d30_lord_per_amsa` (5-lord chain w/ odd/even sign variation), `varga_vimsopaka_contribution` + `varga_saptavargaja_bala_component` (consumed by GA8/strength — produce these for downstream join).
- `varga_d27_directional_quadrant` (N/S/E/W), `varga_d9_lagna_special` (Vargottama + Pushkara Lagna flags), `varga_karya_bhava_per_varga`.
- `karaka_per_varga` (8 Jaimini karakas × 30 vargas; Rahu in/out school variant per GA5/A5 rule).
- `varga_lal_kitab_special` (D9 Pakka Ghar + D12, via G41), `varga_d108_karma_attribution`, `varga_d150_rishi` + `varga_d2700_sub_rishi` (via G44).

## §5 — Atomic grain (GA3 §5 — binding)

`varga_position` per (varga, body) = its own subject with longitude/sign/lord/nakshatra/pada as separate keys. Deity attribution per amsa = its own row. The 60 D30 lord-per-amsa entries = 60 rows. Never collapse a varga's chart into one JSONB blob. Per-row carries the 6 Section-B enrichments (A5 §3 / GA5 §5): tolerance_arcsec, near-boundary flags, vargottama_flag_at_point, formula_provenance_text, cross_ayanamsha_divergence_arcsec — atomic.

## §6 — Prerequisite global assets (verify before writer completes)

- **G16 Varga formula library** with `formula_id` taxonomy (Parashari standard, Jaimini variants, Mooltrikona D3). Verify present; if a formula_id is missing, that variant floors (marked), position still emits via the generic fn where possible.
- **G41 Lal Kitab corpus** (for `varga_lal_kitab_special`), **G44 Nadi tables** (for D150/D2700 rishi). If absent → those categories floor + report; do not fabricate.
- D60/D40/D45/D108 deity/devata tables: embed as engine constants (BPHS Ch.7 exact for D60 — 60 entries, non-cyclic; A6 §10.2).

## §7 — Two-pass verification (A6 §5 — per-category, declared in schema)

Implement A6 §5 table verbatim. `single` for standard 16-varga positions + house lord/occupant + D27 quadrant (G16 + Swiss authoritative). `two_pass_verified` for D60/D108/D150/D2700 (small errors compound), dignity, all vargottama flags, deity attribution, formula variants, D30 lord-per-amsa, aspect/ashtakavarga per varga, vimsopaka/saptavargaja (feeds downstream), karya-bhava, karaka-per-varga, Lal Kitab, D9 Lagna special. `divergent_flagged` → halt + `CONDUCTOR_HALT_LOG.md`.

## §8 — FORENSIC grounding gate

Built on a chart that passed the 7 core anchors. Additionally assert D1 (=varga D1) reproduces the natal positions exactly (Sun=Capricorn, Lagna=Aries, Moon nak=Purva Bhadrapada) — D1 IS the rashi chart, so a D1 varga_position mismatch is an immediate halt. Verify the **D9 Lagna** and **vargottama** computations are internally consistent with the locked D1. Do NOT copy A6's illustrative example "Sun's D9 sign: Aries" uncritically — verify against the engine.

## §9 — Citations (A6 §6)

Both forms per row; real engine version string (not natal_engine/0.2.0); `chart=482012f1`. Human form e.g.: "Sun's Navamsa (D9) sign: <engine value> (Lahiri)." / "Sun's D60 amsa deity: <table value> (Lahiri)." / "Mercury's D150 Nadiamsa rishi: <G44 value> (Lahiri)."

## §10 — Materialized views (A6 §8)

`mv_chart_vargas_summary` (wide row per chart,ayanamsha,body,varga) + `mv_chart_super_vargottama_bodies` (high-signal small MV). Both natal-fixed; refresh synchronous at build close.

## §11 — Build-state wiring

On success update `asset_throughput` for `ga_vargas` (chart_id `482012f1`): row count + state transition. Because this writer batches, update incrementally so the cockpit bar advances during the build, not only at the end. chart_id targeted = keyed.

## §12 — Acceptance criteria (all `[verify-against: prod]`)

1. `CHART_FACTS_SCHEMA.json` contains the ~25 A6 categories; drift_detector GREEN. `[verify: drift run]`
2. `chart_divisionals` populated for all 30 vargas × 25 bodies × 5 ayanamsha; atomic rows. `[verify: psql GROUP BY varga_id, count distinct]`
3. All 6 generic vargas + D2700 computed via custom fn, values internally consistent. `[verify: sample + cross-ayanamsha spread]`
4. Cross-varga harmonics (super/trikona/trans vargottama) computed in post-pass, consistent with per-varga positions. `[verify: sample]`
5. Two-pass categories all `two_pass_verified` (zero `divergent_flagged`); deity/rishi attributions present OR cleanly floored + reported. `[verify: psql GROUP BY verification_pass_status + null audit]`
6. `varga_vimsopaka_contribution` + `varga_saptavargaja_bala_component` emitted (GA8/strength consumes these). `[verify: psql count]`
7. FORENSIC: D1 reproduces natal positions exactly (Sun=Capricorn, Lagna=Aries). `[verify: assertion]`
8. Atomic grain + prime directive + no-narration GREEN; zero fabricated attributions. `[verify: gates]`
9. Both MVs refresh at build close. `[verify: \dm]`
10. `asset_throughput` ga_vargas updated incrementally, keyed to `482012f1`; cockpit bar advances. `[verify: cockpit + psql]`
11. CI green; merge-verify before done.

## §13 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, atomic-grain, deterministic accuracy over volume, floors aspirational, never fabricate, **incremental idempotent writes (resumable under context-decay re-kick)**. Halt on D1-natal mismatch, two-pass divergence, missing prerequisite that can't cleanly floor.

---

*End of GA6 brief v1.0. The largest L1 writer: 30 vargas × ~25 categories × 5 ayanamsha ≈ 78K rows into chart_divisionals.*
