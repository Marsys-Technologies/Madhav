/**
 * signal_glossary.generated.ts — DO NOT HAND-EDIT.
 * ============================================================================
 * GENERATED from platform/python-sidecar/brahmagyan/signal_register_glossary.py
 * by platform/scripts/generate_signal_glossary_mirror.ts (`npm run codegen:signal-glossary`).
 *
 * The Python module is the single source of truth for these tables. Edit it, then
 * regenerate. `signal_glossary.parity.test.ts` re-hashes the .py and fails if this
 * file is stale, so hand edits (or an un-regenerated Python edit) are caught in CI.
 *
 * Behaviour built ON these tables lives in the hand-written sibling
 * `signal_glossary.ts` — this file is data only.
 */

/** sha256 of the canonical Python source at generation time (drift detector). */
export const SOURCE_SHA256 = "c50fa183897bb98b93aa634d0ba67b02d40362f1558153985e976dfe05f06476"

/** Relative path of the canonical source, for error messages and the parity test. */
export const SOURCE_PATH = 'platform/python-sidecar/brahmagyan/signal_register_glossary.py'

/** raw `fact_category` (snake_case, as written to chart_facts) → acharya-grade display label. */
export const FACT_CATEGORY_DISPLAY_LABEL: Readonly<Record<string, string>> = Object.freeze({
  "graha_nakshatra_join": "Graha–Nakshatra Junction",
  "bhrigu_nadi_point": "Bhrigu Nadi Special Point",
  "esoteric_point_shiva": "Esoteric Shiva Point",
  "upagraha_position": "Upagraha (Shadow Planet) Position",
  "midpoint": "Chart-Point Pair Midpoint (graha/lagna/MC)",
  "graha_pada_join": "Graha–Pada Junction",
  "saham_position": "Saham (Arabic Lot) Position",
  "aprakasha_position": "Aprakāśa (Dark Body) Position",
  "arudha_pada": "Arudha Pāda",
  "graha_cheshta_bala_per_varga": "Graha Ceṣṭā Bala per Varga",
  "graha_dignity_per_varga": "Graha Dignity per Varga",
  "lord_in_house_per_varga": "House Lord Placement per Varga",
  "lord_aspects_lord_per_varga": "Inter-Lord Aspect per Varga",
  "karaka_house_lord_overlap_flag": "Kāraka–House-Lord Overlap",
  "argala_natal_matrix": "Argala (Intervention) Matrix",
  "virodha_argala_natal_matrix": "Virodha Argala (Counter-Intervention) Matrix",
  "aspect_parashari_natal": "Pārāśarī Graha Drishti (Natal)",
  "aspect_jaimini_per_varga": "Jaimini Rāśi Drishti per Varga",
  "bhava_chalit_rasi_divergence": "Bhāva Chālit vs Rāśi Divergence",
  "graha_shadbala_total": "Graha Ṣaḍbala (Six-Strength Total)",
  "house_bhava_bala_total": "Bhāva Bala (House Strength) Total",
  "house_bhava_bala_subscore": "Bhāva Bala Component Score",
  "panchamahapurusha_yoga": "Pañcamahāpuruṣa Yoga",
  "maitri_graha_natural": "Naisargika Graha Maitri (Natural Friendship)",
  "graha_position": "Graha Natal Position",
  "varga_position": "Varga (Divisional) Position",
  "yoga_natal_condition": "Yoga Condition (Natal)",
  "yoga_fired": "Confirmed Yoga Firing",
  "dosha_natal": "Dosha (Natal)",
  "bhava_arudha": "Bhāva Arudha (Arudha Pāda of House)",
  "graha_vimsopaka_shadvarga": "Viṃśopaka Bala (Shadvarga)",
  "graha_vimsopaka_saptavarga": "Viṃśopaka Bala (Saptavarga)",
  "graha_vimsopaka_dasavarga": "Viṃśopaka Bala (Daśavarga)",
  "graha_vimsopaka_shodasavarga": "Viṃśopaka Bala (Ṣoḍaśavarga)",
  "ashtakavarga_bindu": "Ashtakavarga Bindu (Transit Score)",
  "ashtakavarga_pinda_sodhita": "Pinda Shodhita (Purified Ashtaka Score)",
  "graha_nakshatra": "Graha Nakshatra",
  "nakshatra_pada": "Nakshatra Pāda",
  "sensitive_degree_check": "Sensitive Degree Check (Puṣkara/Gaṇḍānta/Mṛtyu-bhāga/Kartari)",
  "lagna_position": "Lagna (Ascendant) Position",
  "panchanga_element": "Pañcāṅga Element",
  "tithi": "Tithi (Lunar Day)",
  "vara": "Vara (Weekday)",
  "nakshatra_of_day": "Janma Nakshatra",
  "tajaka_aspect": "Tājaka Aspect (Varṣaphala)",
  "tajaka_yoga": "Tājaka Yoga (Annual Chart Yoga)",
  "special_lagna": "Special Lagna",
  "varga_dignity": "Varga Dignity",
  "varga_house_lord": "Varga House Lord",
  "varga_house_occupant": "Varga House Occupant",
  "varga_vargottama_flag": "Vargottama Flag",
})

/** Leaked headline token (space-separated form) → display label. Includes the two
 *  computation-abstention marker glosses. */
export const SIGNAL_TYPE_GLOSSARY: Readonly<Record<string, string>> = Object.freeze({
  "graha nakshatra join": "Graha–Nakshatra Junction",
  "bhrigu nadi point": "Bhrigu Nadi Special Point",
  "esoteric point shiva": "Esoteric Shiva Point",
  "upagraha position": "Upagraha (Shadow Planet) Position",
  "midpoint": "Chart-Point Pair Midpoint (graha/lagna/MC)",
  "graha pada join": "Graha–Pada Junction",
  "saham position": "Saham (Arabic Lot) Position",
  "aprakasha position": "Aprakāśa (Dark Body) Position",
  "arudha pada": "Arudha Pāda",
  "graha cheshta bala per varga": "Graha Ceṣṭā Bala per Varga",
  "no_canonical_per_varga_method": "[COMPUTATION-ABSTENTION: no canonical classical formula for this varga — not an astrological finding]",
  "floored": "[FLOOR-VALUE: computation abstained per §B.10 — not an astrological finding]",
})

/** Substrings identifying rows that are NOT astrological findings — internal
 *  floor/abstention markers written when no verifiable classical formula exists
 *  (§B.10 / §N.4), plus catalog-only rows awaiting cross-verification.
 *  Order is load-bearing: first match wins in `classifySignalMarker`. */
export const INTERNAL_MARKER_PATTERNS: readonly string[] = Object.freeze([
  "floored: no_canonical_per_varga_method",
  "no_canonical_per_varga_method",
  "floored:",
  "[COMPUTATION-ABSTENTION",
  "[FLOOR-VALUE",
  "floor_reason=",
  "requires_pass",
])
