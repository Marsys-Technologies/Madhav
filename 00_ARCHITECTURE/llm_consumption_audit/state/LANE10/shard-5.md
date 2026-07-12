# LANE 10 — PROMISE-vs-DELIVERY — shard-5 (L3 Kāla assets AP-036..AP-042)

Charter §7.5 facet-grained attribution. Native chart `482012f1-710e-4a25-994a-93821f5871aa`.
DEPLOYED channel: https://amjis-mcp-qm256lasva-el.a.run.app/mcp (primary, read-only).

## DB truth (E-6, verbatim SELECT counts, native chart)
- kala_darshana native=750 (all=1500)
- kala_jivana_parva native=100 (all=200)
- kala_taranga native=79728 (all=159456)
- kala_convergence native=6484 (all=9443)
- kala_activation native=66836 ; kala_activation_predicates native=66836

## Deployed L3 tool probe results
- `query_planet_position` (date arg) → WORKS: positions w/ tropical_longitude, sign_number, nakshatra, is_retrograde, speed_dps, source_citation "pyswisseph DE441". (ephemeris → ka_graha_sancara)
- `kala_life_arc_get` → WORKS: parvas w/ dasha_planet, parva_quality, theme_keywords, high_convergence_count, avg_effective_score, narrative, source_citation `ka_jivana_parva:v2.0`. (→ ka_jivana_parva)
- `kala_muhurta_get` (date+lat+lon+event_class) → WORKS: scored windows, panchanga_details, factors(panchanga/dasha/transit/signal), source_citation, location honored. (→ ka_muhurta_seva)
- `kala_projections_get` → WORKS: 25 projections, provenance table=**kala_bhavishya**, effective_score, probability_tier, falsifiability, convergence_id, source_chain. (fronts ka_bhavishya_lekha; exposes convergence_id derivatively)
- `kala_windows_get` → **BROKEN/EMPTY**: activation_count=0, predicate_count=0, provenance tables=[kala_activation,kala_activation_predicates] which hold 66836 rows; **ignores passed date_from/date_to** (echoes default 2026-07-12→2027-07-12 even when 1984→2050 passed). (→ ka_kalasutra)
- `kala_temporal_bundle` → **EMPTY**: timeline_excerpt=[], convergence_windows=[], obstructions=[], snapshot="Sidecar unavailable — no Kāla data can be computed". mode=fallback_empty. (the aggregate temporal surface — starves convergence/darshana)
- `kala_yoga_activation_get` → activated_yogas=[], total_count=0 (joins kala_activation → same emptiness).
- No deployed tool matches taranga / darshana / convergence-windows (tool-list regex → only yoga_activation). `query_convergence_windows` referenced in drill_next is NOT deployed.

## Verdicts
- **AP-036 ka_graha_sancara** — DELIVERS (core). Ephemeris reachable+usable. Facet gap: promise bundles "Sade Sati state and eclipse-point proximity"; query_planet_position payload omits both (Sade Sati reachable via separate ganita_sade_sati_get; eclipse-proximity not found). Low finding, class 1.
- **AP-037 ka_jivana_parva** — DELIVERS. kala_life_arc_get serves full parva dossier, self-describing, cited.
- **AP-038 ka_kala_darshana** — SHORTFALL / retrieval-plane. Data present (750). No deployed tool serves kala_darshana; only surface (temporal_bundle) empty. + Promise INCONSISTENT (class 3): brief=§0 "standing lifetime discovery product / apex" vs asset_registry+CLOSE §143 "Display-ready temporal view, serve-time UI layer".
- **AP-039 ka_kalasutra** — SHORTFALL / retrieval-plane. Data present (66836). Fronting tool kala_windows_get returns count=0 and ignores date params → class 4 EMPTY SHELL. L2 null-hook fill unreachable via deployed channel.
- **AP-040 ka_muhurta_seva** — DELIVERS. kala_muhurta_get serves scored windows w/ panchanga + factors + citation; location mandatory honored.
- **AP-041 ka_sangam** — PARTIAL / retrieval-plane. "THE VALUABLE CORE" (6484). No direct convergence-window tool deployed; temporal_bundle.convergence_windows=[] (sidecar). Ranked windows reachable only derivatively via kala_projections_get (convergence_id + effective_score exposed) but rigor-stratum metrics (rarity_years, orb-strength cos², confidence_score, independent_current_count) not surfaced → degraded form.
- **AP-042 ka_taranga** — SHORTFALL / retrieval-plane; promise **re-sourced** (task quote NOT FOUND; no brief exists; re-sourced from asset_registry CURRENT row "Monthly activation waveform 1950–2100"). Data present (79728). NO deployed tool serves kala_taranga → class 1 UNREACHABLE. (Governance sub-note: only L3 asset with no build brief.)
