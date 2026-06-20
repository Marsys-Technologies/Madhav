---
artifact: CLAUDECODE_BRIEF_L3_KA_TULANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_TULANA
brief_for: ka_tulana — Tulanā / CROSS-PATTERN PRIORITIZATION (L3 Kāla; QT-4) [NEW]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.11.4-C (cross-pattern prioritization) + I-11, QT-4 (comparative — "options A vs B, which timing is more favorable, why"), §5.11.5 #4 (window-collision/interference), §5.13.C2/I-23 (temporal dissonance consumer), §5.11.6 (confidence vocabulary for the verdict)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K6
  blocked_by: [ka_sangam, ka_vighnakara, ka_kala_darshana]   # ranks ACROSS the windows these produce
  blocks: []   # a serve-time/logic product; nothing downstream depends on it in the build DAG
  may_touch:
    - platform/python-sidecar/services/ka_tulana/**            # NEW (ranking logic; serve-time)
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_tulana.py   # OPTIONAL thin artifact (cached rankings) — see §3.5
    - platform/scripts/seed/asset_registry_seed.ts            # register ka_tulana
  parallel_safe_with: [ka_jivana_parva, ka_bhavishya_lekha]   # all K6 serve-time/derived; disjoint
---

# CLAUDECODE BRIEF — ka_tulana (Cross-Pattern Prioritization) [NEW]

## §0 — What this asset IS
`ka_tulana` (Tulanā, "weighing / comparison") answers **QT-4 (comparative)**: *"I have options A and B —
which timing is more favorable, and why?"* and the implicit *"of my N good windows, which matters MOST?"*
A client has finite attention; `ka_tulana` ranks **across DIFFERENT patterns and life-domains** (not just
within one), and resolves head-to-head comparisons with a reasoned verdict. It is a serve-time / logic
product over the windows `ka_sangam` (opportune) and `ka_vighnakara` (danger) already produce — it adds
NO new search, only cross-window judgment (plan §5.11.7 — reasoning over the same stored outputs).

## §1 — Why it matters / strategic role
- **It makes the instrument STRATEGIC, not just informative (plan §5.11.4-C).** Per-pattern ranking
  exists in `ka_sangam`; the missing capability is ranking ACROSS patterns/domains so the client spends
  attention where it matters most ("THIS window, because…").
- **It is the consumer of TEMPORAL DISSONANCE (plan §5.13.C2).** When an opportune window for one domain
  collides with a danger window for another, `ka_tulana` is where that tension becomes a comparative
  verdict ("favorable for marriage, but financially exposed — net: defer or proceed-with-mitigation").
- **It speaks the confidence vocabulary (plan §5.11.6).** Every comparative verdict carries a
  high/moderate/speculative label, so the client knows how much to trust the ranking.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The canonical life-domains EXIST** — `bo_sangati.py::KNOWN_DOMAINS` + each signal's
  `domains_affected_array` (career, relationship, wealth, spirituality, health, … — the L2 CDLM 6-domain
  set). **`ka_tulana` ranks across THESE established domains — do NOT invent a new domain taxonomy
  (anti-drift).**
- **The window inputs are fully scored** — `ka_sangam` windows carry convergence_score, rarity_years,
  confidence, peak_date, independent_current_count; `ka_vighnakara` windows carry severity + dissonance.
  `ka_tulana` ranks over these EXISTING scores; it does not recompute them.
- **Window-collision** (plan §5.11.5 #4) is detected in `ka_kala_darshana`; `ka_tulana` consumes the
  collision/dissonance flags for its verdicts.

## §3 — The build (a ranking model over existing windows)
**3.1 — The cross-pattern ranking function.** Given a set of candidate windows (across patterns/domains),
rank by a composite of: convergence_score (or severity, signed), rarity_years (rarer ranks higher —
cost-of-omission), confidence_score (discount low-confidence), consequence (the underlying L2 pattern's
importance), and proximity (sooner vs. later, a tunable preference). **The composite weights are
native-ratified (I-11/I-7) — PROPOSE with rationale, `[NATIVE-RATIFY]`, HALT.** Keep it explainable: the
output must say WHY A > B (which factors drove it), not just a number (QT-4 demands the "why").

**3.2 — Head-to-head comparison (the explicit QT-4 query).** `compare(window_A, window_B) -> verdict`
returning: the ranked winner, the per-factor breakdown (where each wins/loses), the confidence label, and
a natural-language-ready rationale chain (the LLM narrates from it — `ka_tulana` provides the structured
reasoning, not prose).

**3.3 — Dissonance-aware verdicts (plan §5.13.C2).** When a window is opportune for domain X but
collides with a danger window for domain Y, the verdict NAMES the tension and offers the decomposition
(proceed / defer / proceed-with-mitigation→`ph_pratikara`). NEVER collapse a dissonance into a single
bland score (the I-23 discipline).

**3.4 — Multi-domain attention budget.** Beyond pairwise: given the native's top windows across ALL
domains over a horizon, produce a ranked "what matters most" list with the domains each serves — the
strategic attention map (the QT-4 "of my three good windows, this one" use case).

**3.5 — Storage decision (artifact vs. pure serve-time).** Prioritization is cheap reasoning over already-
stored windows. DEFAULT: a serve-time SERVICE (no stored rows) — register `asset_kind='service'`.
OPTIONAL: if a cached "current top-N ranking" is wanted in the cockpit, add a thin artifact table
(`kala_priority`) refreshed on rebuild. **Flag the choice; lean service** (avoids storing derivable data).

## §4 — Asset registration
`ka_tulana`: `layer:'kala'`, sanskrit `'Tulanā'`, english `'Cross-pattern prioritization'`. If service:
`asset_kind='service'`, `count_sql:null`, self-test = rank a known set + a known A-vs-B compare for
`482012f1`. If artifact: `asset_kind='artifact'`, `target_table:'kala_priority'`, chart-scoped count_sql.
`depends_on: ['ka_sangam','ka_vighnakara','ka_kala_darshana']`.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** ranking across two DIFFERENT patterns/domains returns a stable order; the output
   includes a per-factor "why A > B" breakdown (not just a scalar) — the QT-4 explainability requirement.
2. **[verify: pytest]** `compare(A,B)` returns the winner + breakdown + confidence label; a low-confidence
   window is correctly down-ranked vs. a high-confidence one of similar raw score.
3. **[verify: pytest]** dissonance-aware: a window opportune for X but colliding with danger for Y yields
   a verdict that NAMES the tension + offers proceed/defer/mitigate — not a single averaged score.
4. **[verify: pytest]** the ranking uses ONLY the established `KNOWN_DOMAINS` (no invented domains); rarer
   windows (higher rarity_years) rank above commoner ones at equal convergence.
5. **[verify: NATIVE-RATIFY]** the I-11 composite weights HALT for native sign-off.
6. **[verify: anti-drift]** `ka_tulana` reads `ka_sangam`/`ka_vighnakara` scores; it does NOT recompute or
   restate them, and writes nothing to L2 or to those engines' tables.
7. **[verify: psql_prod + curl_prod]** registered (service or artifact per §3.5); cockpit reflects it
   correctly (health badge or count); self-test passes for `482012f1`.
8. **[contract]** if it has a writer, it never commits/rolls back `ctx.db_conn` (plan §9).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-tulana
# the canonical domains to rank across
grep -n "KNOWN_DOMAINS" platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py
# tests
cd platform/python-sidecar && pytest -q services/ka_tulana -k "tulana or prioritize or compare or rank"
```
> Branch/merge: Madhav human-gated PR. NATIVE-RATIFY gate (I-11 weights) — Conductor HALTS.

## §7 — Definition of done
- [ ] Cross-pattern ranking function (explainable, established domains, native-ratified weights).
- [ ] Head-to-head compare(A,B) with per-factor breakdown + confidence label.
- [ ] Dissonance-aware verdicts (name the tension; proceed/defer/mitigate).
- [ ] Multi-domain attention map.
- [ ] Storage decision made (lean service); registered; anti-drift clean; self-test green; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Turns a pile of windows into a strategy** — without `ka_tulana` the layer hands the client N
   separate good moments; with it, the client gets "THIS one matters most, because…" — the difference
   between data and decision-support, and the direct answer to the QT-4 comparative query.
2. **Makes dissonance actionable** — it is where "great for marriage, bad financially" becomes a
   verdict with a proceed/defer/mitigate decomposition, instead of a number that hides the conflict;
   this is the consumer that gives I-23's dissonance its payoff.
3. **Enforces explainability** — by requiring a per-factor "why A > B" breakdown (not a scalar), it keeps
   the instrument auditable and lets the LLM narrate a real rationale, not a black-box ranking.
4. **Reuses scores instead of recomputing** — ranking over the already-rigor-scored windows (no new
   search, no restated values) keeps the layer DRY and anti-drift-clean, honoring §5.11.7.
5. **Ranks across the ESTABLISHED domains** — by binding to L2's `KNOWN_DOMAINS` it avoids inventing a
   parallel life-domain taxonomy (a classic drift hazard) and keeps L3's comparisons consistent with the
   chart's structural domain model.
6. **Carries confidence into the verdict** — attaching the high/moderate/speculative label to every
   comparison means the client is told not just which window wins, but how much to trust the call.

---
*End of CLAUDECODE_BRIEF_L3_KA_TULANA v1.0. The weighing — strategy over a pile of windows. NATIVE-RATIFY gate (I-11) inside.*
