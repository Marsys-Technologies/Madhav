# Lane 2 — Evidence-Sufficiency shard-2-b8 (Groups E/F: Dhana & Vivaha)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale). Mode: P-12 evidence-plan-then-acquire, DEPLOYED read-only MCP connector.
Charts: C1=482012f1-710e-4a25-994a-93821f5871aa (Abhisek) · C2=1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan).
Questions: E7 losses/theft/litigation erosion · E8 charity/expenditure disposition · F1 marriage timing · F2 spouse nature/direction/background — each × 2 charts × 2 variants (16 rows).

trim_seen = TRUE across the batch: `[budget-capped response — see structuredContent; text duplicate suppressed for this instrument per R5.1 C1]` on every assess_*/judgment_query text field (had to read structuredContent instead); `...[truncated for budget]` in ranking_basis.note, provenance notes, and every get_signals `signal_summary` (truncated mid-string); assess_marriage verdict_skeleton summaries truncated mid-clause.

---

## TOOL-BEHAVIOR DISCOVERY (governs E7/E8 verdicts)

**judgment_query with `domain=wealth` SILENTLY CLAMPS `about.bhava` to bhava 2 (dhana).** Requested `about.bhava:12` → returned `about.bhava:2`, karakas [Jupiter], operative_varga D2 on BOTH C1 and C2. Requested `about.bhava:6` → also bhava 2. The `receipt.bhava:true` asserts the bhava was honored — it was not. Contrast: `domain=relationship` DID honor `about.bhava:7` (returned bhava 7, D9). So the wealth-domain path is hardwired to the 2nd house and cannot be pointed at the vyaya (12), ripu (6), or randhra (8) bhavas that losses/theft/litigation/expenditure require. This single behavior defeats E7 and E8 at the retrieval plane. (`domain` param on get_temporal_windows likewise dropped — filters.domain=null.)

---

## Evidence plans + acquisition traces

### E7 — losses / theft / litigation erosion
PLAN (acharya needs): 12th (vyaya/loss) + 6th (ripu/litigation/debt/theft-enemies) + 8th (randhra/sudden loss) house & lord condition; chaura (theft) yogas; rina (debt) / kalaha-vyavahara (litigation) yogas; malefics/Rahu-Ketu in 2nd/dhana; Kemadruma/daridra; maraka-for-wealth dasha timing. Order: judgment_query bhava=12/6/8 → get_signals wealth (loss-signal family) → get_temporal_windows wealth (erosion windows).
ACQUIRED (C1 & C2 identical failure shape):
- judgment_query wealth bhava=12 → CLAMPED to bhava 2 (see discovery above). bhava=6 → clamped to bhava 2. The 12th/6th/8th are NOT examinable via the domain tool.
- get_signals wealth top_k=15 (C1): leading rows are generic nabhasa yogas (Yuga, Anapha) at identical composite 1.0465, salience 0.488, `domains_affected_array` = ALL 5 domains (career+wealth+health+relationship+spirituality) — non-discriminating, NOT loss/theft/litigation-typed. NO chaura / rina / vyavahara / dusthana-erosion signal family exists anywhere in the returned set.
- get_temporal_windows wealth (C1 & C2): activation_count 0.
VERDICT narrow: INSUFFICIENT. broad: INSUFFICIENT (both charts).
ROOT CAUSE: UNREACHABLE-BY-NONEXISTENCE — theft (chaura), litigation (vyavahara/kalaha), and debt (rina) are classical concepts the system never computes as a signal family; PLUS retrieval-plane clamp (wealth→bhava 2) blocks even a generic 12/6/8 dignity read. No erosion timing (windows empty). An answer would be pure fabrication.

### E8 — charity / expenditure disposition
PLAN: 12th house (vyaya = expenditure/charity/dana) + 2nd/12th-lord relation (spend-vs-save disposition); 9th (dharma/dana) condition; Jupiter (dana-karaka) condition; benefic-vs-malefic occupancy of 12th (auspicious spending vs waste); tyaga/dana yogas. Order: judgment_query bhava=12 → get_domain_reading spirituality (dharma/dana) → get_signals.
ACQUIRED:
- judgment_query wealth bhava=12 → CLAMPED to bhava 2 (both charts). The 12th (the exact house the question is about) is unreachable via the domain tool.
- No dana/tyaga/vyaya/expenditure-disposition signal family in get_signals (only nabhasa yogas). Charity/dharma partially adjacent to spirituality-domain convergence but never as an expenditure-disposition read.
VERDICT narrow: INSUFFICIENT. broad: INSUFFICIENT (both charts).
ROOT CAUSE: UNREACHABLE-BY-NONEXISTENCE (no vyaya/dana disposition analysis) + retrieval-plane clamp (wealth→bhava 2 blocks the 12th). System cannot say whether the native spends auspiciously, hoards, or wastes.

### F1 — marriage timing
PLAN: activation/convergence windows filtered to marriage over a multi-decade horizon; 7th-lord dasha + Venus (kalatra-karaka) dasha/antardasha; Jupiter transit to 7th/Moon/Venus; D9 activation; maraka-for-marriage. Order: get_temporal_windows marriage → assess_marriage → get_dashas → judgment_query relationship (timing_hooks).
ACQUIRED:
- get_temporal_windows domain=marriage AND domain=relationship (C1 & C2): activation_count 0, predicate_count 0, filters.domain=null (domain param dropped). GLOBAL EMPTY SHELL — no marriage window layer.
- assess_marriage (C1): top_10_composite is an IDENTICAL-SCORE WALL — Sasa, Shoola, Vasi, Yuga, Gola yogas ALL at composite 1.0465 — generic nabhasa / pancha-mahapurusha yogas, none marriage-specific, no timing attached.
- get_dashas (C1): WORKS — vimshottari MD Mercury→2027-08-18, then Ketu; level≤3, two_pass_verified. judgment_query relationship timing_hooks surfaced Venus MD 2034-08-18→2054-08-18 (kalatra-karaka dasha). This is a raw dasha scaffold, NOT a marriage window.
VERDICT narrow: INSUFFICIENT (no marriage-timing convergence; the dedicated window layer is empty; only raw dasha rows, un-annotated for marriage). broad: SUFFICIENT-WITH-GAPS (an LLM can hand-assemble a coarse "Venus MD / 7th-lord period" indication from get_dashas + timing_hooks, honest about the absence of transit/convergence confirmation). Both charts.
ROOT CAUSE: class 4 EMPTY SHELL (kala_activation for marriage) + class 9 (the marriage-timing krama — which dasha/transit rule fires the event — is ungoverned; consumer must choose).

### F2 — spouse nature / direction / background
PLAN: 7th house + 7th-lord condition in D1 AND D9 (navamsa depth); Venus (kalatra-karaka) condition; Upapada Lagna (UL) + 2nd-from-UL (spouse-family/background); Darakaraka (Jaimini) + DK-navamsa; 7th-lord sign/nakshatra → spouse direction & appearance/background; occupants/aspects on 7th (temperament). Order: judgment_query relationship bhava=7 operative_varga=D9 → varga depth → get_domain_reading relationship.
ACQUIRED (C1): 7th from lagna Libra; 7th-lord Venus in 9th Sagittarius, dignity neutral, shadbala 4.64; karaka Venus in 9th; 7th occupants Mars+Saturn (two malefics); aspecting []; verdict "mixed" composite -1. **varga_confirmation.varga=D9 but `rows:[]`** — the D9/navamsa depth the receipt claims (`varga_confirmed:"D9✓"`) is NOT actually delivered. No UL, no Darakaraka, no spouse-direction, no appearance/background attribute anywhere.
ACQUIRED (C2): 7th-lord Venus EXALTED in 12th Pisces (shadbala 7.75); karaka Venus exalted; 7th occupant Ketu; aspected by Mars+Rahu. Same `varga_confirmation.rows:[]` empty D9.
VERDICT narrow: INSUFFICIENT (spouse DIRECTION, BACKGROUND, and navamsa-depth are all absent; no UL/DK; D9 rows empty). broad: SUFFICIENT-WITH-GAPS (generic spouse NATURE composable from 7th-lord dignity + Venus condition + malefic occupancy → "challenging/mature partner" tenor, honest that direction/background are not served). Both charts.
ROOT CAUSE: UNREACHABLE-BY-NONEXISTENCE for direction/UL/Darakaraka/spouse-background; class 5/6 for the empty D9 varga_confirmation (receipt claims D9-confirmed, payload has zero D9 rows).

---

## Findings (class per §4)

- **F-b8-1 (class 5 DISHONEST SELF-DESCRIPTION + class 1 UNREACHABLE, HIGH):** judgment_query `domain=wealth` silently clamps `about.bhava` to 2 (both charts, both a `bhava:12` and `bhava:6` request returned `bhava:2`), while `receipt.bhava:true` asserts the requested bhava was honored. The vyaya(12)/ripu(6)/randhra(8) houses — required for losses, litigation, expenditure, charity — are not examinable via the domain judgment path. Contrast domain=relationship, which DOES honor about.bhava. Defeats E7 AND E8 on both charts. Suspected layer: serving-query (domain→bhava map overrides caller input without disclosure).
- **F-b8-2 (class 1 UNREACHABLE-BY-NONEXISTENCE, HIGH):** No loss/theft/litigation/debt concept family (chaura, rina, vyavahara-kalaha yogas; dusthana-erosion signals) is computed at any layer; get_signals(wealth) surfaces only generic nabhasa yogas tagged to all 5 domains. Defeats E7 on both charts. Data-plane gap.
- **F-b8-3 (class 1 UNREACHABLE-BY-NONEXISTENCE, HIGH):** No expenditure/charity/dana disposition analysis (vyaya-bhava spend-vs-save, dana-karaka, tyaga yogas). Defeats E8 on both charts. Data-plane gap (compounded by F-b8-1 clamp).
- **F-b8-4 (class 4 EMPTY SHELL, HIGH):** get_temporal_windows returns activation_count 0 / predicate_count 0 for domain=marriage AND domain=relationship on BOTH charts; `filters.domain` comes back null (the domain arg is dropped). The marriage-timing window layer serves nothing. Defeats F1 timing. Likely R-45 (kala_activation) rediscovery. Suspected layer: L3-writer / data-plane (kala_activation unpopulated).
- **F-b8-5 (class 7 DROWNED, HIGH):** assess_marriage `top_10_composite` is an identical-score wall — Sasa, Shoola, Vasi, Yuga, Gola yogas ALL at composite 1.0465 — generic nabhasa/pancha-mahapurusha yogas carrying zero marriage/spouse decision weight; the ranker cannot discriminate (co-tied) and surfaces no 7th-house/Venus/kalatra signal at top. Acharya-tolerance rationale: a marriage top-10 whose every leading row is a whole-chart nabhasa yoga (Gola = "all grahas in one sign" tendency) contains no partnership-specific information; the actual kalatra evidence is buried below. Suspected layer: ranking (composite_4d class_prior over-weights yoga rows; topic_relevance=1 for all, non-discriminating).
- **F-b8-6 (class 6 UNUSABLE FORM / class 5, MED):** judgment_query relationship reports `varga_confirmation.varga:"D9"` with `rows:[]` and a `receipt.varga_confirmed:"D9✓"` — the receipt claims navamsa confirmation while the payload delivers zero D9 rows. Defeats the D9-depth axis of F2 (spouse via navamsa) on both charts. Suspected layer: serving-query (varga_confirmation query returns empty yet receipt marks ✓).
- **F-b8-7 (class 1 UNREACHABLE-BY-NONEXISTENCE, MED-HIGH):** No spouse-direction, Upapada Lagna (UL) / 2nd-from-UL (spouse-family/background), Darakaraka (Jaimini) or spouse-appearance/background taxonomy is reachable by any tool. judgment_query relationship serves only 7th-lord + Venus dignity + occupants. Defeats the direction/background axes of F2 on both charts. Data-plane gap.
- **F-b8-8 (class 6/7 UNUSABLE FORM, LOW-MED):** get_signals(domain=wealth) returns signals whose `domains_affected_array` lists all 5 domains (a "wealth" query returns a signal equally tagged career/health/relationship/spirituality) — the domain filter is non-discriminating, so no domain-scoped signal set is actually retrievable. Suspected layer: serving-query/signal-tagging.
- **F-b8-9 (class 5 receipt-honesty, LOW):** `bhanga_checked:false` on every judgment_query (documented design gap) — arishta/dosha cancellation never evaluated; relevant to any malefic-heavy verdict (e.g. C1 7th with Mars+Saturn, composite -1) which may be over-negative absent bhanga.

## Class-9 UNGOVERNED-JUDGMENT improvisations (first-class findings)

- **J-b8-1 (taxonomy→bhava/tool translation, E7/E8):** No krama maps "losses/theft/litigation" or "charity/expenditure" to houses/tools. I improvised 12/6/8 for losses and 12/9 for charity — and then could not even execute the route because the wealth judgment path clamps to bhava 2. Different acharya kramas (e.g. theft from 6th-lord + Rahu vs 2nd-from-lagna) would seek different evidence.
- **J-b8-2 (method choice, F1):** With the activation-window layer empty, I had to decide WHICH timing rule produces a marriage window — Venus mahadasha vs 7th-lord dasha vs Jupiter transit to 7th/Moon vs D9-activation. The system governs none; any window I state is a self-chosen method.
- **J-b8-3 (spouse-direction improvisation, F2):** To answer "direction/background" I would hand-map the 7th-lord sign (C1 Sagittarius→NE-ish; C2 Pisces) and Venus condition to a compass direction and social background from classical memory — entirely ungoverned; no UL/DK served.
- **J-b8-4 (conflict adjudication, E8):** Charity sits between wealth(2nd, clamped), vyaya(12th, unreachable) and dharma/spirituality(9th) — I had to decide which frame owns "charity disposition" with no system authority ordering.
- **J-b8-5 (event-tense adjudication, F1):** Both natives are adults (C1 age 42); "marriage timing" is ambiguous between verifying a past event and predicting a future one. The system offers no life-stage anchor, so I had to decide which sense to answer — ungoverned.
- **J-b8-6 (spouse-nature synthesis, F2):** Composing "spouse nature" from 7th-lord dignity + Venus + malefic occupancy (C1: two malefics Mars+Saturn in 7th → difficult; C2: Venus exalted but in 12th + Ketu → renunciate/foreign tenor) is a taxonomy→life-language translation the system never performs; I improvised the mapping.

## Anchor rediscovery
F-b8-4 ≈ R-45 (kala_activation empty-shell). F-b8-5/F-b8-8 ≈ R-37/R-44 family (drowned/identical-score-wall, non-attributed domain tagging). F-b8-1 (wealth→bhava-2 silent clamp) and F-b8-6 (D9 varga_confirmation empty-but-✓) appear to be NEW rows (dedupe vs R-37..R-48 negative) — candidate register appends. Independently rediscovered via Lane-2 acquisition.
