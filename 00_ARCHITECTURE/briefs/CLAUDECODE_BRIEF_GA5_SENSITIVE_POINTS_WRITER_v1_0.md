---
artifact: CLAUDECODE_BRIEF_GA5_SENSITIVE_POINTS_WRITER_v1_0.md
canonical_id: GA5_SENSITIVE_POINTS_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 2, asset ga_sensitive — esoteric/Tajik/KP/Nadi/Lal Kitab points)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A5_SENSITIVE_POINTS_SPEC_v1_0.md (LOCKED — category authority)
depends_on: GA3 (chart_facts schema), GA4 (uses birth-day sunrise), G14 Saham library, G44 Nadi tables, G41 Lal Kitab corpus
---

# GA5 — Sensitive Points Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A5_SENSITIVE_POINTS_SPEC_v1_0.md` — **the category authority.** 30 fact_categories (§2), universal Section-B enrichment fields (§3), per-category two-pass methodology (§4), dual citations (§5), row-count projection (§6, ~13,000/chart), tool contract (§8), implementation notes (§9), locked decisions (§10). **Note A5 §10: it bumps the A3 enum from ~131 to ~147 — GA3's `CHART_FACTS_SCHEMA.json` must include the 16 new categories before this writer runs.**
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` — schema + atomic grain + prime directive.
- `00_ARCHITECTURE/GA4_PANCHANGA_WRITER_v1_0.md` — supplies birth-day sunrise GA5 needs for Hora-lagna-derived points.

## §1 — Reality reconciliation (apply over the older spec)

A5 LOCKED 2026-05-29. **Translate:**

1. **Engine = PyJHora** (`pyjhora_adapter`), not `natal_engine/sensitive_points.py`. A5 §9.1 says "existing natal_engine/sensitive_points.py covers ~6 categories — extend to 30": read it for **intent only** ([[feedback-rebuild-skepticism-of-existing-code]]); implement against PyJHora + explicit classical formulas. Where PyJHora natively supplies a point (upagrahas, karakas, arudhas, Bhrigu Bindu, Yogi/Avayogi), use it; where it doesn't (full 70+ Saham catalogue, Hadda 60-zone, Maharsi sphutas, Lal Kitab points, Aprakasha), implement the classical formula deterministically in the writer. **No JH-parity oracle** — two-pass is internal-consistency (formula vs independent re-derivation), never "match JH".
2. **Asset id = `ga_sensitive`.** Target = `chart_facts`. All 30 categories ayanamsha-DEPENDENT → 5 rows per key.
3. **Postgres-direct, no JSONL.**
4. **No audience tier. Floors aspirational** — "~13,000 rows" is a target. Chase the full catalogue with genuine deterministic formulas; if a Saham/Maharsi point has no verifiable deterministic formula, floor it (null + marked) rather than fabricate.

## §2 — Branch + topology

- Branch `feature/ga5-sensitive-points-writer` off `main` **after GA3 merges** (needs the 16 new categories in `CHART_FACTS_SCHEMA.json`; if GA3 didn't add them, this brief adds them to the schema as step 1). May run **parallel to GA4** (both depend on GA3, not each other; GA5 uses GA4's sunrise but can read it from the panchanga service directly if GA4 hasn't landed). One PR when green.
- Target chart_id (RESOLVED) = **`482012f1-710e-4a25-994a-93821f5871aa`** (confirmed canonical 2026-06-10; only real native row; `asset_throughput` already keyed; no re-keying). Pass as a parameter; no longer a halt condition. **`362f9f17-…` is a dead phantom** — the specs' `chart=362f9f17` citation examples (incl. A5's illustrative longitudes) are placeholders, not a real id; write `482012f1-…` and verify all values against the engine.

## §3 — Prerequisite global assets (verify present before writer completes)

A5 depends on global reference assets. **Verify on prod before the writer can finish** ([[feedback-brief-schema-promise-audit]]):
- **G14 Saham library** extended to 70+ formulas (A5 §9.2 — was 50). If absent/short, this is a global-asset bump that must land first; flag if missing.
- **G44 Nadi-rishi attribution table** (for Maharsi sphutas + nadiamsa rishi).
- **G41 Lal Kitab corpus** (for Lal Kitab special points).
- **G20 ayanamsha registry**, **G24 nakshatra lord**.
If any prerequisite is absent, the categories depending on it floor to absent (marked) — do NOT fabricate; report the gap.

## §4 — The 30 categories (A5 §2 — implement every one)

Implement all 30 from A5 §2 with their subjects. Highlights of scope (full detail in A5 §2 table — do not drop entries):
1. `upagraha_position` (6: Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, Kala)
2. `saturn_derived_point` (Gulika both reckonings, Mandi, Yamaganda sphuta, Maandi)
3–15. Esoteric bindus: Bhrigu Bindu, Yogi (**2 formula variants** 93°20'+96°40'), Avayogi (2), Mrityu (**3 variants** BPHS-Ch39 + Saravali + Tajik-Aapamrityu), Trisphuta, Chatushphuta, Panchasphuta (**2 variants** Saturn+Rahu), Pranapada sphuta, Trikona-dasha sphuta, Sri Yantra (3), Brahma/Vishnu/Shiva (Jaimini)
16. `saham_position` (70+ Hellenistic-Tajik catalogue)
17. `karaka_chara_position` (**8-karaka** Atma→Stri; emit both Parashari Rahu-excluded AND KN-Rao Rahu-included when order differs)
18–20. Karakamsa, Swamsa (12), Arudha (A1–A12 + 7 graha arudhas = 19)
21. `midpoint` (54: 36 graha-graha + 9 ASC-graha + 9 MC-graha)
22–23. KP: `kp_ruling_planets_natal` (5), `kp_cuspal_significators` (12 cusps × significator arrays)
24. `aprakasha_position` (5: Dhwaja, Patala, Kandanga, Pidaa, Vighni)
25–27. Tajik: Hadda (60 zones), Triraashipathi, Vargottama-specific
28. `lal_kitab_special_point` (Pakka Ghar etc.)
29. `maharsi_specific_point` (Vasishtha/Atri/Bharadwaja/Agastya/… sphutas)
30. `bhrigu_nadi_point`

## §5 — Universal Section-B enrichment (A5 §3 — every row carries these)

Beyond the A3 standard fields, every GA5 row carries the 6 enrichments — stored as **atomic keys/columns, never one JSONB blob**:
`tolerance_arcsec`, `near_sign_boundary_flag` (within 0°30'), `near_nakshatra_boundary_flag` (within 0°48'), `vargottama_flag_at_point`, `formula_provenance_text` (classical citation), `cross_ayanamsha_divergence_arcsec` (spread across the 5 ayanamshas — a research signal). These enable surgical caveats ("sits 5′ from a sign boundary; ayanamsha choice flips its sign in 2 of 5 schools").

`formula_id` distinguishes variant rows (e.g., Yogi `bphs_93_20` vs `alt_96_40` are two rows with the same subject, different `formula_id`).

## §6 — Two-pass verification — MANDATORY for every GA5 row (A5 §4)

A5 is the strictest writer: **every row two-pass verified.** Per-category primary/secondary/tolerance is in A5 §4 verbatim — implement that table. Examples:
- `upagraha_position`: swisseph derivation vs BPHS-formula re-derivation, ≤10″.
- `karaka_chara_position`: Rahu-excluded vs Rahu-included sort; variance HALTS only if the **Atmakaraka assignment** differs (otherwise both emitted).
- `kp_ruling_planets_natal` / `kp_cuspal_significators`: exact match required.
- Variant-family points (Yogi/Mrityu/Panchasphuta): variance always logged, both/all emitted as separate `formula_id` rows.

`verification_pass_status='divergent_flagged'` for any in-tolerance violation → halt build, `CONDUCTOR_HALT_LOG.md`. Integrity is the hard gate.

## §7 — Atomic grain (GA3 §5)

Hadda 60 zones = 60 subjects. Swamsa 12 houses = 12 rows. 54 midpoints = 54 subjects. Every enrichment field = its own column/key. JSONB only for genuinely irreducible composites.

## §8 — FORENSIC grounding gate

GA5 doesn't compute the 7 core anchors directly, but it MUST be built on a chart that passed them (positions/panchanga gates upstream). Additionally, **assert internal-consistency anchors** where A5 gives examples to sanity-check the engine: e.g., Atmakaraka derivation should be stable; Bhrigu Bindu = midpoint(Moon, Rahu) must place consistently given Moon in Purva Bhadrapada. If a sensitive point's derivation is internally inconsistent with the locked natal positions → flag. No fabricated example values — verify against the engine, do not copy A5's illustrative longitudes (e.g., "Bhrigu Bindu 247°33′") uncritically.

## §9 — Materialized view (A5 §7)

`mv_chart_sensitive_points_summary` — wide row per (chart, ayanamsha, point_subject). Refresh synchronous at build close. Serves "show all sensitive points / all Sahams / what's my Atmakaraka".

## §10 — Build-state wiring

On success update `asset_throughput` for `ga_sensitive` (canonical chart_id). Cockpit bar moves. chart_id targeted = keyed.

## §11 — Acceptance criteria (all `[verify-against: prod]`)

1. `CHART_FACTS_SCHEMA.json` contains all 30 A5 categories (16 new beyond GA3's base); drift_detector GREEN. `[verify: drift run]`
2. Prerequisite global assets (G14 70+ Sahams, G44, G41, G20, G24) present OR the dependent categories cleanly floored + reported. `[verify: psql + gap report]`
3. All 30 categories emitted into `chart_facts` ×5 ayanamsha for the native; variant points emit multiple `formula_id` rows. `[verify: psql GROUP BY fact_category]`
4. **Every row `two_pass_verified`** (zero `single`, zero `divergent_flagged`). `[verify: psql GROUP BY verification_pass_status]`
5. Section-B enrichment fields populated atomically on every row; zero JSONB blobs holding queryable values. `[verify: column audit + jsonb audit]`
6. Atomic grain: Hadda=60, Swamsa=12, midpoints=54 subjects, etc. `[verify: psql count per category]`
7. Zero fabricated values; floored points null+marked; no-narration linter GREEN. `[verify: null audit + linter]`
8. 8-karaka emits both schools when order diverges; AK-difference halts. `[verify: sample + halt-log check]`
9. `mv_chart_sensitive_points_summary` refreshes at build close. `[verify: \dm + count]`
10. `asset_throughput` ga_sensitive updated, keyed to canonical chart_id; cockpit bar moves. `[verify: cockpit + psql]`
11. CI green; merge-verify before done.

## §12 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, atomic-grain, two-pass-every-row, deterministic accuracy over volume, floors aspirational, never fabricate. Halt on AK-divergence, any two-pass divergence beyond tolerance, missing prerequisite that can't be cleanly floored, unresolved chart_id.

---

*End of GA5 brief v1.0. The strictest writer: ~13,000 two-pass-verified esoteric/Tajik/KP/Nadi/Lal-Kitab points.*
