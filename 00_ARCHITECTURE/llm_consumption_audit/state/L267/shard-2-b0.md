# Lane 2 — Evidence-Sufficiency Shard 2-b0 (Group A: Deha & Ayus, A1–A4)

Charter: `LLM_CONSUMPTION_AUDIT_CHARTER` §7.3 (4-point scale). Mode: P-12 evidence-plan-then-acquire.
Channel: deployed MCP connector (read-only). Charts: `482012f1…` (Abhisek, C1), `1c826d5a…` (Abhinandan, C2).
Grader: worker b0. trim_seen: **TRUE** (judgment_query `trim_report`, apex `caps_applied`, orientation family-collapse 300→67→10).

## Tools called (both charts unless noted)
`apex_health_assess`, `assess_health`, `get_domain_reading{domain:health}`, `get_temporal_windows`,
`kala_windows_get`, `get_dashas`, `kala_life_arc_get`, `phala_outlook_get`, `ganita_strength_get`,
`judgment_query{domain:health}`, `judgment_query{bhava:8}`.

---

## Shared evidence-plane facts (apply to all 4 questions)

- **judgment_query is the one governed health surface.** `{domain:health}` returns a deterministic
  classical checklist: lagna condition (from-lagna + from-chandra), bhavesha (Mars, house 7, dignity
  neutral, shadbala_rupa 5.57), Sun karaka, `varga_confirmed:D6✓`, `yogas_checked:7–8`, honest
  `receipt` of what was actually checked, resolvable `grounding.fact_ids`. Composable for A1.
- **`get_temporal_windows` / `kala_windows_get` return EMPTY on BOTH charts** — `activation_count:0`,
  `predicate_count:0`, `signal_id_refs:[]`; `kala_activation` table has 0 rows. Default window is
  ONE year (2026-07-12→2027-07-12). Class-4 EMPTY SHELL. Kills A3.
- **`apex_health_assess` top-10 is DROWNED (100.6 KB payload):** 5 of top-10 are
  `combustion_per_varga|is_combust=False` NON-events (Saturn/Mars/Jupiter/Mercury/Venus each "not
  combust"), + 5 yogas tied at identical score 1.0465 (identical-score wall). `by_stage.karaka/lord/
  strength/varga/temporal` all EMPTY — only `yoga` populated, despite the advertised "composite_4d"
  strength+temporal dimensions. `activating_dasha.activations:[]`. `karaka_analysis` is MISLABELED —
  returns CDLM cross-domain linkage cells (career×health 748 shared signals), NOT graha-karaka dossiers.
- **UNATTRIBUTED wall (R-44 rediscovery):** `get_domain_reading{health}` entity_profiles =
  `UNATTRIBUTED` (299 signals, dominant_domains career/character/wealth — not health) + `KETU` (1).
  `top_signals:[]`. Health surfaces as one convergence row (748) drowned under career (12,364).
- **No ayurdaya anywhere.** No Pindayu/Nisargayu/Amsayu, no alpayu/madhyayu/purnayu band, no markesh.
  `judgment_query{bhava:8}` gives 8th-house structure but `receipt.karaka:false`, `yogas_checked:0`
  (both charts: C1 composite −0.8, C2 −0.5).
- **No body-system taxonomy.** Health is a single domain; no cardiac/GI/neuro/respiratory mapping.
- `get_dashas` works (Vimshottari L1–3, natal house/sign/nakshatra, two_pass_verified, 50 rows) but
  `lord_natal_dignity_d1`/`shadbala_total` NULL and window defaults 2021–2031 (no full-life span,
  no maraka annotation). `kala_life_arc_get` gives dasha-parva life phases (quality/theme) — coarse.
- `assess_health` text is budget-capped ("text duplicate suppressed per R5.1 C1"); payload only in
  `structuredContent` — a consumer reading `content[0].text` gets nothing usable (form note).

---

## Per-question evidence plans + verdicts (verdicts identical C1/C2 — tool behavior mirrors)

### A1 — vitality/constitution
**Plan:** (1) lagna + lagna-lord condition → judgment_query{domain:health}; (2) Sun/Moon vitality
karaka dossier → apex karaka_analysis + ganita_strength; (3) D1+D6 → varga_confirmed; (4) lagna-lord
shadbala → ganita_strength_get.
**Acquired:** judgment_query gives lagna (Aries)+lord Mars (h7, shadbala 5.57)+Sun karaka+D6✓+7–8 yogas
(C1 +0.7 / C2 −0.8). ganita_strength exposes shadbala/vimsopaka categories. BUT depth-axis fails:
apex `karaka_analysis` is CDLM cells not a Sun dossier; `by_stage.karaka/strength` empty; bhanga not
checked (`bhanga_not_checked` flag); Moon/ojas not surfaced as vitality karaka.
**narrow → SUFFICIENT-WITH-GAPS** (one governed answer composable; gaps honest).
**broad → SUFFICIENT-WITH-GAPS** (broad demands full width/depth — Sun+Moon+lagna+lagna-lord dossiers,
avastha, D1/D6/D9, lagna ashtakavarga — depth axis fails per Mercury standard; more gaps than narrow).

### A2 — longevity band
**Plan:** (1) ayurdaya (Pindayu/Amsayu/Nisargayu) → sought, none; (2) 8th house+lord → jq{bhava:8};
(3) Saturn ayus-karaka → sought; (4) markesh + maraka dasha → sought.
**Acquired:** jq{bhava:8} gives 8th-house (Scorpio/Virgo) + lord Mars, but `receipt.karaka:false`
(Saturn not wired), `yogas_checked:0`, no ayurdaya band, no alpayu/madhyayu/purnayu, no markesh timing.
Nothing yields a quantified longevity band.
**narrow → INSUFFICIENT.  broad → INSUFFICIENT.** Root cause: **UNREACHABLE-BY-NONEXISTENCE** — the
ayurdaya computation (core classical ayus method) was never built into the data plane.

### A3 — health-crisis timing windows
**Plan:** (1) temporal activation windows → get_temporal_windows/kala_windows; (2) maraka/markesh
dasha → get_dashas + phala; (3) health near-future anchors → phala_outlook.
**Acquired:** temporal windows EMPTY (activation_count 0, both charts, 1-yr window). phala_outlook
returns near-future anchors but domain `transition` (not health), 12-mo horizon. get_dashas gives the
timeline (C1 Mercury MD→2027/Ketu next; C2 Saturn MD/Rahu AD) but unannotated for crisis/maraka. No
health-crisis window computed.
**narrow → INSUFFICIENT.  broad → INSUFFICIENT.** Root cause: class-4 EMPTY SHELL (`kala_activation`
0 rows) + class-1 UNREACHABLE (no maraka-window / health-crisis computation served).

### A4 — chronic-disease propensity by system
**Plan:** (1) 6th house+lord+D6 rogamsha → jq{bhava:6}+chart_facts D6; (2) per-body-system disease
taxonomy → sought; (3) graha→body-part/dhatu mapping → sought.
**Acquired:** judgment_query gives an overall health verdict (bhava 1, D6✓) but NO per-system
decomposition. No cardiac/GI/neuro/respiratory/endocrine taxonomy; no graha→dhatu/anga mapping. D6
placements reachable via drill but carry no disease-system classification.
**narrow → INSUFFICIENT.  broad → INSUFFICIENT.** Root cause: **UNREACHABLE-BY-NONEXISTENCE** — health
is modeled as one domain; "by system" granularity was never computed.

---

## Class-9 UNGOVERNED-JUDGMENT improvisations logged
1. **Method choice (A2):** no governed krama for longevity → routed via `judgment_query{bhava:8}`; no ayurdaya path exists.
2. **Silent decomposition (A4):** "by system" has no governed decomposition → improvised 6th-house/D6 drill as proxy.
3. **Conflict adjudication (A1):** apex_health composite (top signal 2.16 = a combustion NON-event) vs judgment_query verdict (+0.7) disagree on what is "chart-defining for health"; had to pick judgment_query as authoritative.
4. **Taxonomy→life-language (A1/A4):** signals arrive as raw `category=combustion_per_varga|key=is_combust|value_num=0`; translating to constitution language is un-governed.
5. **Timing-method substitution (A3):** kala empty → fell back to get_dashas + would hand-identify maraka windows — ungoverned.

## Anchor rediscovery
- **R-44** (298/300 unattributed): rediscovered — orientation entity_profiles `UNATTRIBUTED` = 299 signals.
- **R-37/R-44a-b** (DROWNED / trivia ranked chart-defining): rediscovered — apex_health top-10 = 5 combustion NON-events + 5 identical-score-wall yogas.
