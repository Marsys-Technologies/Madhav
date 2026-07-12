# Lane 2 Evidence-Sufficiency — Shard 2-b11 (Group G. Santana / Progeny)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale). Mode: P-12 evidence-plan-then-acquire.
Channel: deployed MCP connector (read-only). Charts: `482012f1` (native Abhisek) / `1c826d5a` (Abhinandan).
Rows: G1–G4 × {narrow, broad} × 2 charts = 16.

## Tools exercised (read-only)
get_chart_orientation · get_domain_reading(domain=children) · get_signals(domain=children) ·
get_remedies(domain=children) · get_temporal_windows(domain=children) · phala_outlook(domain=children) ·
graha_portrait(Jupiter) · query_chart_facts · chart_snapshot · get_dashas · judgment_query(bhava=5) ·
ganita_chart_facts_get(divisional_chart=D7).

## Cross-cutting acquisition findings (apply to every G row)

- **No progeny domain in the L2 domain surface.** `get_domain_reading`, `get_signals`,
  `get_remedies`, `get_temporal_windows` all use a fixed 6-domain vocabulary
  (career/character/health/relationship/spirituality/wealth). `domain="children"` →
  `note:"Domain 'children' not found"`, `lenses_total:0`, `signals:[]`, remedies `resonance_count:0`.
  Confirmed on BOTH charts. → class 4/1.
- **The governed progeny path is `judgment_query(bhava=5)`** — NOT any domain string. It returns
  a real deterministic classical checklist: `about.domain=progeny`, `karakas=[Jupiter]`,
  `operative_varga=D7`, bhava/bhavesha/karaka conditions with fact_ids + shadbala, verdict grade.
  The LLM must *know* to translate "children"→bhava=5; the domain-string tools do not route there
  → class 3 INCONSISTENT taxonomy + class 9 UNGOVERNED translation.
- **D7 saptamsa (THE progeny varga) is an empty/unusable shell.**
  `judgment_query.checklist.varga_confirmation.rows = []` on both charts.
  Drill-pointer sends to `ganita_chart_facts_get(divisional_chart=D7)` → `facts:[]` but
  `returned_count:160` and grounding lists **160 bare fact_ids** with no resolvable text/values.
  D7 data EXISTS in DB (160 facts) but is served as un-resolvable IDs + empty facts array.
  → class 1 UNREACHABLE-in-usable-form + class 6 UNUSABLE FORM (R-40 analog).
- **Dishonest receipt (both charts).** `judgment_query.verdict.receipt` reports
  `"varga_confirmed":"D7✓"` and `"timing_anchored":true` while `varga_confirmation.rows=[]`,
  `timing_hooks.lord_mahadasha_windows=[]`, `karaka_mahadasha_windows=[]`. Receipt contradicts
  payload → class 5 DISHONEST SELF-DESCRIPTION. (`epistemic.grade=structural_prior`, `coverage:null`.)
- **query_chart_facts filters silently ignored.** `fact_category`, `varga`, and free-text `query`
  args produce the identical fixed ~800-row alphabetical dump (reaches only up to `D12_*`;
  `pagination:null`). PutraKaraka (Jaimini PK), D7 subjects, 5th-lord specifics (alpha past the cap)
  are therefore unreachable via this tool. → class 6 + class 5.
- **Remedy writer gap self-disclosed.** `get_remedies` narration: `bo_upaya`
  `associated_doshas_array` and `estimated_cost_inr_range_jsonb` are **100% NULL for every chart**.
  No dosha→remedy mapping possible. → class 4.
- **trim_seen:** graha_portrait + large query_chart_facts returned budget-cap markers
  ("budget-capped response — see structuredContent"/"text duplicate suppressed per R5.1 C1"/S3).
  Disclosed (structuredContent supplied), not silent, but recorded.

## What IS reliably retrievable (D1-level checklist)
Native `482012f1`: 5th=Leo (empty); 5th-lord Sun in 10th Cap, dignity neutral, shadbala 8.47;
karaka Jupiter in 9th own sign, shadbala 7.8; 5th aspected by Jupiter + Moon; verdict
`convergent_moderate` (composite 2.1).
Abhinandan `1c826d5a`: 5th-lord Sun in 11th; karaka Jupiter **debilitated**; verdict
`contested` (composite −1.6); current MD Saturn (2010–2029). Discriminative at D1/checklist level.

## Per-question verdicts

### G1 — children yes/count band  (narrow & broad, both charts)
Plan: (1) judgment_query bhava=5 for 5th/lord/karaka + verdict; (2) graha_portrait Jupiter dossier;
(3) D7 saptamsa for count/multiplicity; (4) 5th occupants/aspects.
Acquired: checklist verdict + Jupiter dossier present → likelihood ("children yes, moderate") is
composable. **Count band unsupported**: D7 empty-shell, no count/multiplicity estimator anywhere
in the system. → **SUFFICIENT-WITH-GAPS** (likelihood answerable; count-band gap is honest, class 4/1).

### G2 — conception windows  (narrow & broad, both charts)
Plan: judgment_query timing_hooks → get_temporal_windows(children) → get_dashas AD/PD → transit triggers.
Acquired: `lord_mahadasha_windows=[]`, `karaka_mahadasha_windows=[]`, native `current=[]`;
`get_temporal_windows(children)` = 0 activations (domain arg ignored); `phala_outlook(children)`
returns generic `transition` anchors, not progeny. Only raw `mahadasha_windows_by_graha`
(e.g. Sun MD 2054–2060 — far future) with no conception mapping, no AD/PD, no Jupiter-transit trigger.
Mapping raw MD→conception is ungoverned. → **INSUFFICIENT** (class 4 EMPTY SHELL + class 9).

### G3 — santana dosha + remedial path  (narrow & broad, both charts)
Plan: bearing_yogas/dosha on bhava-5 → dosha-tagged remedies → mantra/charity path.
Acquired: `bearing_yogas=[]` (no putra-dosha surfaced on the progeny bhava); `get_remedies(children)`
empty; `associated_doshas_array` 100% NULL chartwide → no dosha→remedy linkage exists.
→ **INSUFFICIENT** (class 4 EMPTY SHELL + class 1; remedy path structurally unlinkable).

### G4 — children's wellbeing from parent chart  (narrow & broad, both charts)
Plan: derived-relative reading (child = native of 5th/D7-derived chart) → their houses/dashas.
Acquired: system models no derived-relative / bhavat-bhavam chart; D7 empty-shell; no child-as-native
framework on any tool. Only proxy = Jupiter condition + 5th benefic/malefic contact.
→ **INSUFFICIENT** (derived-relative reading is **UNANSWERABLE-BY-DESIGN** — scope note; the acharya
concept exists in canon but the platform never computed a derived-relative surface → data-plane
UNREACHABLE-BY-NONEXISTENCE).

## Class-9 UNGOVERNED-JUDGMENT log (first-class findings)
1. **Taxonomy→life-language**: "children" not a domain; had to translate to `bhava=5` to reach any
   governed reading. No tool documents this mapping.
2. **Cross-tool taxonomy conflict**: judgment_query knows "progeny"; domain-string tools don't —
   adjudicated by picking judgment_query (method choice).
3. **Silent decomposition of G1**: split "yes" (answerable) from "count band" (unanswerable) with no
   system guidance on how count is derived.
4. **Method choice for G2**: had to decide raw `mahadasha_windows_by_graha` was the only timing
   surface and that mapping it to conception windows was my own inference, not governed.
5. **Retrieval-path guessing**: query_chart_facts filters ignored → had to improvise reachability
   for PK/D7/5th-lord (and conclude unreachable).

## Findings (§4 class) summary
- F1 class 1/6 — D7 saptamsa: 160 facts exist, served as bare IDs + empty `facts:[]` (both charts).
- F2 class 5 — judgment_query receipt `D7✓`/`timing_anchored:true` contradicts empty payload (both).
- F3 class 4 — timing_hooks lord/karaka mahadasha windows + bearing_yogas empty (both).
- F4 class 4/1 — no progeny domain in domain_reading/signals/remedies/temporal_windows (both).
- F5 class 3/9 — progeny domain taxonomy inconsistent across tools; LLM must translate.
- F6 class 6/5 — query_chart_facts silently ignores filters; alpha-capped; pagination null.
- F7 class 4 — bo_upaya associated_doshas + INR 100% NULL → no dosha→remedy path.
- F8 class 9 — no count-of-children estimator anywhere (G1 count band requires fabrication).

trim_seen: true (disclosed budget-caps on graha_portrait + query_chart_facts).
