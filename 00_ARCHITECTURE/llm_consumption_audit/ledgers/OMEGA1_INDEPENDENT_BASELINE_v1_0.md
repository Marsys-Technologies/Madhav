---
artifact: OMEGA1_INDEPENDENT_BASELINE
version: 1.0
status: FROZEN
authored_by: Stream-γ Verifier (independent, read-only SQL against live DB)
purpose: >
  Frozen ground-truth reference for the Ω1 TCI sanity gate (charter: "distinct fact_category count
  in the TCI must be ≥ distinct fact_category count in production, asserted by an INDEPENDENT query
  written by your Verifier, plus ≥1 entry per bodha_mechanisms class, dasha system, varga and
  ayanamsha"). Computed from scratch, without reference to the Ω1 builder's generator or output.
---

# Ω1 independent baseline

| Dimension | Ground-truth number | Exact query |
|---|---|---|
| distinct fact_category (OVERALL, gate denominator) | **218** | `SELECT COUNT(DISTINCT fact_category) FROM chart_facts` |
| fact_category (primary chart 482012f1 only) | 216 | `...GROUP BY chart_id` |
| fact_category (second chart 1c826d5a only) | 211 | `...GROUP BY chart_id` |
| bodha_mechanisms classes materialized in DB | 4 (convergent_dispositor_chain, graha_bhava_affliction, mutual_aspect, mutual_aspect_triangle) | `SELECT COUNT(DISTINCT mechanism_class) FROM bodha_mechanisms` |
| bodha_mechanisms classes documented (writer/tool design enum) | **10 (gate denominator per PROXY-RULED-004)** | writer source enum, not SQL |
| dasha systems built | **9** (ashtottari, chara_karaka, kalachakra, mudda, naisargika, narayana, vimshottari, vimshottari_kp, yogini) | `SELECT COUNT(DISTINCT system_id) FROM chart_dashas` |
| vargas (D-series) | **31** D-vargas (D1-D150, D2700; excludes ALL_VARGAS/CROSS markers) | `SELECT COUNT(DISTINCT varga) FROM chart_divisionals WHERE varga LIKE 'D%'` |
| ayanamshas, real astronomical | **5** (krishnamurti, lahiri_chitrapaksha, raman, surya_siddhanta_classical, true_chitra) | `SELECT COUNT(DISTINCT ayanamsha_id) FROM chart_facts` minus INVARIANT sentinel |
| ayanamsha_id distinct incl. sentinel | 6 (adds INVARIANT — non-ayanamsha-varying facts) | same query, no filter |
| asset_registry total | 107 (102 data + 5 service) | `SELECT COUNT(*) FROM asset_registry` |

## Gate denominator rulings (PROXY-RULED-004, see proxy/gamma.md) — BINDING on Ω1 generator + sanity gate

1. **fact_category gate uses 218 (global), never a chart-scoped subset.** A chart-scoped generator
   under-counts (216 or 211) and would silently fail the true gate while looking populated.
2. **bodha_mechanisms gate denominator is 10 (documented design classes), not 4 (DB-materialized).**
   6 of 10 classes never fire for either canonical chart today. The TCI MUST carry a
   `ConceptAccountingRow`-shaped entry for all 10, with the 6 absent-for-these-charts classes marked
   `not_computed_globally` or `empty_for_this_chart` (never silently dropped) — sourced from the
   writer's class enum, never `SELECT DISTINCT mechanism_class`. Silently shipping only 4 entries is
   the exact "silent omission = build failure" failure mode §0 exists to prevent.
3. **ayanamsha gate denominator is 5 real ayanamshas; `INVARIANT` is tagged as a sentinel, not a 6th
   ayanamsha**, to avoid corrupting Lane I's cross-ayanamsha agreement (`n/6` would be wrong; must be
   `n/5`). The TCI still carries an entry for `INVARIANT` (ayanamsha-invariant facts are a real
   concept) but flags it `is_ayanamsha_variant: false` so it's excluded from agreement-score math.
4. **dasha systems gate uses the 9 DB-built systems**, not `ref_dasha_systems_get`'s advertised list
   (which references `shodashottari`, not currently materialized). A documented-but-unbuilt system is
   out of scope for γ to fabricate — γ's TCI reflects what's actually computed; a gap here is a β
   (Gaṇita/compute) concern, not something γ builds around.
5. Thin-row vargas (D30 n=100, D81 n=2) are present, not absent — no gate exception needed; TCI's
   `row_count_per_canonical_chart` field already carries the honest low number.

This baseline is frozen for the duration of the run. The Verifier re-uses it unchanged when
G4-checking the builder's TCI output — it is not recomputed per check.
