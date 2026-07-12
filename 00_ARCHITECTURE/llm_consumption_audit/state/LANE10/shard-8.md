# LANE10 shard-8 — PROMISE-vs-DELIVERY grading

Charter §7.5 (RATIFIED). Charts: Abhisek `482012f1-…5871aa` (primary), Abhinandan `1c826d5a-…e5f75a`.
DEPLOYED channel = https://amjis-mcp-qm256lasva-el.a.run.app/mcp. DB = read-only SELECT.

Deployed tool inventory grep: NO tool matching pram*/fals*/seva/vistara/export/prefer exists.

---

## AP-057 — mi_seva (L5, service) — promise re-sourced → DELIVERS
- promise_quote was "NOT FOUND"; 4-source re-search: no build brief; asset_registry `english_description` = **"Serve-time contribution-control gateway: effective-value resolution, toggle gates, transit-current binding, MCP parity"** (real declared intent) → promise_status=re-sourced.
- storage_type=service, target mimamsa_preferences. DB: `mimamsa_preferences` = 0 rows (user-set state; empty is legitimate — no user has saved toggles).
- Serve-time effect reachable: `mimamsa_calibration_get(chart=Abhisek)` returns `result.results[0].content.multipliers[...]` (LL1 effective-value multipliers) — effective-value resolution demonstrably served.
- data_plane=empty (by-design, preferences). retrieval=reachable (governed calibration surface serves). ranking=usable.
- Note (low): "MCP parity" (MCP applies same effective values as portal) + toggle-gate path not directly testable with 0 stored preferences — not a defect, an untestable facet.

## AP-058 — mi_vistara (L5, data) — promise re-sourced → PARTIAL (data-plane)
- promise "NOT FOUND"; re-search: asset_registry `english_description` = **"Audit log of all synthesis export events (PDF, JSON, MCP bundles)… writer generates zero rows and only verifies the table; actual rows written by mi_seva on export delivery"** → re-sourced.
- DB: `mimamsa_export_log` = 0 rows (both charts). By design (writer verifies table only). No export events have occurred.
- Retrieval: NO MCP tool reads the export log (grep empty) → UNREACHABLE via deployed channel. It is an internal audit log, not an LLM-consumer surface.
- Verdict PARTIAL: data-plane empty (legitimate 0-event log) + no retrieval path. Modest promise structurally met (table verified) but zero deliverable content and unreachable. Low severity (class 1 + class 4-lite).

## AP-059 — ph_muhurta (L4) → PARTIAL (ranking-form / depth)
- Brief promise: REUSE the classically-deep muhurta engine — ka_muhurta_seva.score+find_windows; panchang_engine **Panchaka/Anandadi/Vasa/Homa**; shastra_tables per-event quality tables; honest no-good-window verdict.
- DB: `phala_muhurta` Abhisek=4, Abhinandan=5 rows. Stored rows: `panchanga_snapshot_jsonb = {"graha":…, "source":"ka_muhurta_seva_proxy"}` — a **PROXY**, `has_panchaka=false`. tarabala_chandrabala + significators present. `window_quality_verdict="mediocre"`, `verdict_reason="Best available window scores 0.13 — below genuine threshold (0.55)…"` → honest no-good-window verdict DELIVERS.
- DEPLOYED: `muhurta_finder` (primary) + `kala_muhurta_get` (alias) both return ranked windows on-the-fly with 4 factors (panchanga/dasha/transit/signal) + panchanga_details (tithi/vara/nakshatra/yoga) + source_citation. Reachable, scored, honest.
- SHORTFALL: promised classical depth (Panchaka/Anandadi/Vasa/Homa; shastra per-event tables; tarabala/chandrabala/significators) is a **proxy in DB and absent from the served payload**. Core promise (personalized scored windows + honest verdict) met; the "classically-deep engine reuse" depth is not evidenced. shortfall=ranking-form (class 6/4-lite depth).

## AP-060 — ph_nimitta (L4, THE SPINE) → DELIVERS
- DB: `phala_anchors` Abhisek=195, Abhinandan=200.
- DEPLOYED: `phala_predictive_anchors_get`, `event_anchors`, `phala_outlook.anchors` all return calibrated anchors with magnitude, confidence band, falsifier, structured_falsifier, karmic_frame, malleability, derivation_ledger, source_citation (non-null), and **honest posterior_provenance** (`cardinality:null` + note "never fabricated… empirical analog is L5 query_calibration"). 8 axes / 5 elevations visible in derivation_ledger (`axes_applied`, `elevations`).
- No shortfall across data/retrieval/form. The spine delivers.

## AP-061 — ph_phaladesa (L4, THE FINALE) → PARTIAL/compound
- DB: `phala_phaladesa` = 7 domains × both charts (14 rows). **`narration_status="pending"` on ALL 14 rows** (registry: "Narration pending via Gemini/DeepSeek only — Anthropic BANNED by DB CHECK"). narration_jsonb unfilled.
- Deterministic scaffold present (anchor_count, spillover, mitigation_available, muhurta_available, pramana_window_status) and a time-bound outlook IS reachable via `phala_outlook` (anchors+mitigations+rectification+auspicious_windows+summary_confidence).
- SHORTFALL (compound): (a) DATA-PLANE — the headline "DELIVERED OUTLOOK dossier" narration is empty (pending) on every row → the promised finale prose does not exist yet (class 4 empty-shell facet). (b) RETRIEVAL-PLANE — the phaladesa per-domain *result-declaration rows* are not surfaced by any dedicated tool; `phala_outlook` top keys = [ok,chart_id,horizon_months,query_window,anchors,mitigations,rectification,auspicious_windows,summary_confidence,provenance_envelope,trim_report] — **no "domains"/"phaladesa" key** (class 1 facet). Consumer gets raw anchors, not the domain synthesis.

## AP-062 — ph_pramana (L4, mission spine) → DELIVERS
- DB: `phala_pramana` Abhisek=195, Abhinandan=200 — one falsifier row per anchor (195↔195, 200↔200).
- Per-prediction falsifier is **uniformly present and reachable**: every anchor payload from `phala_predictive_anchors_get` carries `falsifier` (deny/confirm observable + evaluation_date/window); `phala_outlook.anchors[].structured_falsifier` = {domain, window_end, magnitude_floor, attestation_required, refutation_condition, confirmation_condition}. Non-scoring as promised.
- L5 contract populated: `mimamsa_calibration_get` returns `multipliers` (LL1) → L5 demonstrably reads the interface ph_pramana writes.
- Promise ("single point making predictions uniformly+mechanically testable + writes interface L5 reads") met. No dedicated pramana MCP tool, but the promise does not require one (falsifier surfaces via anchors; L5 reads via DB). No shortfall.

## AP-063 — ph_pratikara (L4) → PARTIAL (retrieval-plane; class 4 + class 3)
- Brief promise: managed remedy PROGRAM reusing bodha_rm_remedy_prescriptions; economics/feasibility tiers, sequenced schedule, muhurta-timed, severity-proportional, cross-tradition, outcome loop.
- DB: `phala_mitigation` Abhisek=602, Abhinandan=638 (rich program: program_jsonb, tradition_options_jsonb, recommended_tier_jsonb, initiation_muhurta_ref, outcome_hook_jsonb).
- **INCONSISTENT retrieval across three tools for the SAME asset:**
  - `mitigation_map` (semantically-named front) → `total_count: 0`, `mitigations: []` on **BOTH** charts (class 4 EMPTY SHELL — dead advertised path).
  - `phala_mitigation_get` (labeled "[Phase-1 alias] same as mitigation_map") → returns **638** remedies (Abhinandan), full program. WORKS.
  - `phala_outlook.mitigations` → **10** rows.
  - Same asset, three tools, three counts (0 / 10 / 638) → class 3 INCONSISTENT.
- Data IS reachable (via phala_mitigation_get + outlook), so the asset delivers — but its primary named tool is broken. shortfall=retrieval-plane.

---
### Verbatim evidence anchors
- `mitigation_map` Abhisek+Abhinandan: `"result":{"mitigations":[],"total_count":0,"all_cited":true}` (source "phala.mitigation")
- `phala_mitigation_get` Abhinandan: remedies_len=638
- `phala_muhurta` verdict_reason: "Best available window scores 0.13 — below genuine threshold (0.55). Moon may be afflicted or no fixed nakshatra available." ; panchanga_snapshot source="ka_muhurta_seva_proxy", has_panchaka=false
- `phala_phaladesa` narration_status="pending" ×14
- anchor posterior_provenance: `cardinality:null … "Not a sample-fit statistic … never fabricated"`
