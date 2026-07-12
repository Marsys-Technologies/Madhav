# Lane 2 — Evidence-Sufficiency Shard 2-b13 (Group H: Bandhu, Ripu & Vyavahara — H3–H6)

status: COMPLETE
worker: Lane 2 evidence-sufficiency (P-12 evidence-plan-then-acquire)
charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale)
channel: DEPLOYED MCP connector (read-only) — amjis-mcp-qm256lasva-el.a.run.app
charts: NATIVE 482012f1-710e-4a25-994a-93821f5871aa · ABHINANDAN 1c826d5a-41cb-4450-b4dc-59d440e5f75a (both Aries lagna — bhava geometry mirrors)
rows: 16 (H3/H4/H5/H6 × narrow/broad × 2 charts)

---

## Cross-question doctrinal note (Group H = 6th/12th-house family)

H3 (open+hidden enemies), H4 (litigation), H5 (betrayal/cheating windows), H6
(employees/servants) are ALL significations of the **6th bhava (ripu/roga/rina/dispute/
servant)** plus the **12th bhava (hidden enemies/loss)**. The system serves this family
through ONE undifferentiated surface — `judgment_query(bhava=6)` / `judgment_query(bhava=12)`.
There is **no signification routing**: the 6th-house's five distinct significations
(enemies, disease, debt, litigation, servants) collapse into a single "Bhava 6" verdict
bundle. Consequence: H3, H4, H6 receive the IDENTICAL evidence payload; the executor LLM
must improvise the taxonomy→life-language mapping (which 6th-house fact speaks to
"employees" vs "open enemies" vs "a lawsuit") every single time — a first-class **class-9
UNGOVERNED-JUDGMENT** act, logged per question below.

## Retrievability census for Group H (both charts)

| Evidence an acharya needs | Tool path | Result |
|---|---|---|
| 6th bhava condition (lagna+chandra), 6th-lord, occupants, aspects, timing hook | `judgment_query bhava=6` | **SERVED** — deterministic classical checklist + current-MD timing hook |
| 12th bhava (hidden enemies/loss) same dossier | `judgment_query bhava=12` | **SERVED** |
| Named-domain reading for enemies/litigation/betrayal/servants | `get_domain_reading` | **UNREACHABLE (class 1)** — only 6 domains: career, character, health, relationship, spirituality, wealth. `domain:"enemies"`/`"litigation"` → `"Domain 'X' not found."`, `question_lenses:[]` |
| Ripu-karaka (Mars/Saturn) condition | `judgment_query` receipt | **EMPTY (class 4)** — `karaka_condition:[]`, receipt `karaka:false` on EVERY bhava call, both charts |
| Bhava-bearing yogas / bhanga (cancellation) | `judgment_query` receipt | **EMPTY (class 4)** — `yogas_checked:0`, `bhanga_checked:false` (honestly disclosed via flag) |
| Computed timing windows for disputes/betrayal | `get_temporal_windows` / `kala_windows_get` | **EMPTY SHELL (class 4)** — `activation_count:0, predicate_count:0` on BOTH charts, bounded AND unbounded. Rediscovers **R-45**. |
| Predictive event anchors for conflict/litigation/betrayal | `phala_outlook horizon=48mo` | **WIDTH GAP** — only event families emitted: `career_discovery_event` + `transition_discovery_event`; zero conflict/litigation/betrayal families |
| Ripu-relevant ranked signals | `get_signals limit=60` | **DROWNED (class 7)** — top-60 = 100% structural trivia (dispositor_chain ×15, centrality ×14, dispositor_tree ×13, dignity D108 ×8, convergence_count ×8); ZERO enemy/ripu/6th/litigation/servant/betray/12th hits. No `house` filter to reach them. `total_matching_filters:13364`. |
| Dasha timeline for MD/AD dispute activation | `get_dashas` | **SERVED** — full vimshottari; native current MD = Mercury (2010→2027), and Mercury IS 6th-lord on native (usable enemy-activation inference) |

### Honesty markers captured
- **DISHONEST SELF-DESCRIPTION (class 5):** `get_signals` → `truncated:false` while
  `returned_count:60` vs `total_matching_filters:13364`, `pagination.total:null,
  next_cursor:null`. Reads as "complete set delivered." Misleading.
- **UNATTRIBUTED wall (class 7, R-44 anchor):** orientation digest embedded across responses
  carries `entity_profiles[0]={entity:"UNATTRIBUTED", signal_count:299}`.
- **trim_seen = TRUE:** `judgment_query` text budget-suppressed ("[budget-capped response —
  see structuredContent; text duplicate suppressed per R5.1 C1]"); `trim_report` = "full
  trim_report omitted to fit budget", `recover_via: response_format:legacy`. Disclosed, but default is trimmed.
- **RELIABILITY:** one `judgment_query bhava=12` returned only the 110-byte text preamble
  (structuredContent absent, stream cut); retry succeeded. Intermittent SSE-body truncation.

---

## Per-question verdicts (evidence plans + traces)

### H3 — open + hidden enemies
Plan: 6th dossier (open) → 12th dossier (hidden) → ripu-karaka → ranked signals → named domain → timing.
Acquired: NATIVE 6L Mercury in 10th (neutral, shadbala 7.55), no occupants, **Rahu aspects 6th**, verdict mixed/−0.3; 12L Jupiter in 9th own, **Ketu aspects 12th**, verdict conv_moderate/+2.2. ABH 6L Mercury in 11th (asp Jup/Mars/Ven); 12th occupied Mars+Venus, 12L Jupiter in 10th. Karaka [] both. Domain-reading path absent; signals drowned.
The open(6th)/hidden(12th) split — the classical structure of the question — IS cleanly retrievable via the two bhava calls. Gaps: karaka unevaluated, yogas uninspected, no timing.
- narrow → **SUFFICIENT-WITH-GAPS** · broad → **SUFFICIENT-WITH-GAPS**

### H4 — litigation outcome + timing
No litigation-outcome adjudicator: system emits a "Bhava 6" grade but NOT a win/lose synthesis nor the self-vs-opponent (lagnesh-vs-6L) comparison litigation judgment requires. `get_temporal_windows` EMPTY → no computed window; `phala_outlook` has no litigation family. Timing reducible only to raw dasha inference.
- narrow → **INSUFFICIENT** (outcome verdict + specific timing uncomputable; class 4/9)
- broad → **SUFFICIENT-WITH-GAPS** (dispute-propensity composable; outcome+timing improvised)

### H5 — betrayal/cheating windows
Structural markers usable (native Rahu-on-6th, Ketu-on-12th = deceit indicators). But **the "windows" ask is directly defeated by the empty temporal-windows shell (class 4)** — 0 activations both charts; no betrayal signal family; `phala_outlook` has no deception event type.
- narrow → **INSUFFICIENT** (windows are the question; temporal surface empty — class 4)
- broad → **SUFFICIENT-WITH-GAPS** (general betrayal-vulnerability composable; windows gap logged)

### H6 — employee/servant troubles
Only the undifferentiated bhava=6 bundle (identical to H3/H4). Servant signification NOT separated from enemy/disease/debt; no employee-specific analysis; no applicability check; timing empty. Servant reading is 100% improvised signification-routing (class 9).
- narrow → **INSUFFICIENT** (no servant disaggregation or timing; class 4/9)
- broad → **SUFFICIENT-WITH-GAPS** (generic 6th-house subordinate-friction tendency)

---

## Class-9 UNGOVERNED-JUDGMENT log (Group H)
1. **Method/krama choice** — every H-question forced `judgment_query(bhava=N)` because no named domain matches (enemies/litigation/betrayal/servant absent from the 6-domain enum). Ungoverned tool-selection.
2. **Taxonomy→life-language** — mapping one "Bhava 6" verdict onto "open enemies"/"a lawsuit"/"problem employees"; no system signification split. (H3/H4/H6.)
3. **Litigation win/lose adjudication** — entire self-vs-opponent balance + outcome verdict improvised; no adjudicator asset. (H4.)
4. **Betrayal-window construction** — temporal-windows empty, so any "window" is improvised from raw dasha. (H5.)
5. **Conflict adjudication** — native bhava-6 verdict (mixed/−0.3, adverse) vs bhava-12 (conv_moderate/+2.2, favourable) point opposite for "enemies"; nothing reconciles open- vs hidden-enemy weighting — executor adjudicates. (H3.)

## Calibration-anchor rediscoveries
- **R-45** (kala_activation empty) — rediscovered (temporal_windows/kala_windows 0 activations, both charts).
- **R-44** (UNATTRIBUTED ranked wall) — rediscovered (entity_profiles UNATTRIBUTED 299 signals).
