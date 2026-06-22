---
artifact: L4_PHALA_CAMPAIGN_PLAN_v2_0.md
canonical_id: L4_PHALA_CAMPAIGN_PLAN
version: 2.0
status: CURRENT — the governing design for the supreme L4 Phala build; SUPERSEDES v1.0 (the 6-asset draft)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: L4_PHALA_CAMPAIGN_PLAN_v1_0.md (6-asset draft — SUPERSEDED-AS-DRAFT)
governs: 00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml
role: >
  The master design for the supreme L4 Phala layer: 4 upstream enablers (U1–U4) + 8 ph_* assets, each
  elevated to maximal capacity. The governing reference for the session_queue + kickoff. All decisions
  trace to L4_PHALA_DECISIONS_LEDGER_v1_0.md (D20–D46); all briefs are FINALIZED + CLOSED.
inputs:
  - L4_PHALA_DECISIONS_LEDGER_v1_0.md (D20–D46 — every ratified decision)
  - L4_PHALA_PROD_RECONCILIATION_v1_0.md (GATE A — prod-true state)
  - L4_PHALA_HOLISTIC_REVIEW_v1_0.md (the cross-brief review + fixes)
  - L4_PHALA_REGISTRY_AND_WIRING_SPEC_v1_0.md (GATE D/E register+wire)
  - 12 finalized briefs (CLAUDECODE_BRIEF_U1–U4 + CLAUDECODE_BRIEF_L4_PH_*)
---

# L4 Phala — Campaign Plan v2.0 (the supreme design)

## §1 — What L4 Phala IS
The applied / delivered-prediction layer — the FRUIT. It turns L3's scored time-windows + L2's
relational substrate into delivered products for the native: falsifiable predictions, auspicious
windows, mitigation programs, birth-time rectification, cross-domain dynamics, and a master-acharya
reading. Supreme = it holds correlation depth, chains, consensus, and calibration no human acharya can.

## §2 — The 12 components (4 enablers + 8 assets)

### Upstream enablers (sharpen the substrate before the assets consume it)
| id | what | elevation summary | decisions |
|---|---|---|---|
| **U1** | Multi-dāśā consensus | wire-only; surface 7-system agreement (zero new storage) | D30 |
| **U2** | Lifetime convergence | lifetime tier + the null-jivana_parva fix; Prāṇa DROPPED | D29, D31 |
| **U3** | Convergence currents | +7 currents (ashtakavarga/eclipse/t2t/station/vedha/tājika/school); reweight | D32, D33, D35 |
| **U4** | School consensus | de-hardcode 7 engines + persist + wire; disagreement-intelligence + authority-weighting | D18, D28, D36 |

### The 8 ph_* assets
| id | what | the supreme elevations | decisions |
|---|---|---|---|
| **ph_nimitta** | Predictive anchors (THE SPINE) | 8 axes + 5 elevations (magnitude, ranged-confidence, karmic-arc, actionability, contradiction) + kala_bhavishya inheritance | D37, D38 |
| **ph_muhurta** | Auspicious windows | chart-personalized + transit-scored + personal-danger-avoiding + prediction-fused + honest-verdict | D39 |
| **ph_pratikara** | Mitigation program | economics/feasibility + sequenced/conflict-free + muhūrta-timed + proportional + cross-tradition + outcome-loop | D40 |
| **ph_sodhana** | Rectification | whole-instrument scoring + leakage-firewall + body-witness + consensus cross-check + confidence-interval + tiered cost-guard | D41 |
| **ph_suddha_sodhana** | Best rectification | decisiveness + self-correcting verification loop + hypotheses-ledger + self-falsifier + flag/stage propagation (no auto-override) | D42, D43 |
| **ph_sankrama** | Cross-domain spillover | grounded lag + graph-bridge mechanism + multi-hop cascades + conflicts + trajectory + mitigation-routing | D44 |
| **ph_pramana** | Falsifiability scaffolding | unified machine-evaluable falsifiers + L5 contract + evaluation-staging + portfolio/reverse-channel (strictly NON-scoring) | D45 |
| **ph_phaladesa** | Delivered outlook (THE FINALE) | narrative weave + apex item + honest registers + multi-horizon/lens/person-anchor/traceability; deterministic-first prose | D46 |

## §3 — The wave DAG (F1-corrected)
```
PRE   prod==main · pre-allocate migs 330–340 · pin ratified params · register the 3 new assets
W1    U1 (dāśā consensus, wire-only)
W2    [serialized on ka_sangam — F3]  U3 currents(6) → U4(de-hardcode+GATE+persist+wire)
        → U3 school-current(C13) → U2(lifetime+null-fix) → RE-SEAL L3
W3    ph_nimitta  (SPINE — alone; SPINE-FIRST hard gate)
W4    ph_muhurta · ph_pratikara · ph_sankrama   (parallel; blocked_by ph_nimitta)
W5    ph_sodhana (LEAKAGE-FIREWALL gate) → ph_suddha_sodhana (NO-AUTO-OVERRIDE gate)
W6    ph_pramana  (NO-SCORING gate)
W7    ph_phaladesa (B.11 gate + DETERMINISTIC-FIRST gate)
SEAL  HARD VISUAL COCKPIT gate → DRAFT→CURRENT → L4_PHALA_CLOSE + L5 contract → CURRENT_STATE/SESSION_LOG
```

## §4 — The non-negotiable disciplines (inherited + reaffirmed)
- **Anti-drift:** every L4 row references a lower-layer id; ZERO writes outside `phala_*`.
- **Reuse rule (D10):** READ-asset → CALL-service → RECOMPUTE-PyJHora-ONLY-if-absent. PyJHora computes
  only in ph_sodhana (hypothetical birth-times) + Tājaka varsha 49+.
- **Frozen orchestrator contract:** `@register`/`WriterBase`/`run(ctx)`/never commit/`rows_inserted`/delete-then-insert/`$1`.
- **L4/L5 boundary:** L4 makes predictions falsifiable + L5-ready; L5 owns ALL scoring/calibration (D5).
- **Deterministic-first:** the only generative LLM is ph_phaladesa's narration over a fixed scaffold (D46).
- **No canonical-chart mutation:** ph_sodhana/ph_suddha_sodhana stage but never auto-apply a chart revision (D43/B.10).
- **The HARD VISUAL SEAL gate:** the live cockpit (revision==SHA, 8 lit, zero errors) is the ONLY seal signal.
- **Model policy:** Gemini/DeepSeek; Anthropic banned.
- **5 hard gates:** spine-first (ph_nimitta), chart-generality (U4), leakage-firewall (ph_sodhana),
  no-auto-override (ph_suddha), no-scoring (ph_pramana), B.11 + deterministic-first (ph_phaladesa).

## §5 — The four coherence threads (why it's a system, not a pile of features)
1. **Consensus spine** — U1 dāśā + U4 school → ph_nimitta Axis 6 → every prediction carries multi-method agreement.
2. **Convergence accuracy** — U3 enriches the score every anchor inherits → uniform uplift.
3. **Honesty discipline** — ranged confidence + contradiction-carry → discount → proportionality → decisiveness → non-scoring → honest dossier registers.
4. **Actionability loop** — influenceable anchors → mitigation → muhūrta-timed → spillover pre-emption.

## §6 — The build method
Single autonomous wave (D26) under AUTONOMY_RESILIENCE_PATTERN + the swarm charter. Cowork authored;
Claude Code in Antigravity implements. Native input: ONLY the $5k Tier-3 ceiling + (if it fires) a
chart-revision adoption decision. Everything else self-heals (Tier-1/2 + Vimarśaka auto-revert).

## §7 — Retrieval + L5 (post-seal)
Retrieval tools (query_phala_anchors / find_phala_muhurta / query_phala_mitigation /
query_rectification / phala_outlook) — a thin post-seal wave. L5 Mīmāṃsā onboards against ph_pramana's
contract (the next campaign).

---
*End of L4_PHALA_CAMPAIGN_PLAN v2.0. 4 enablers + 8 supreme assets, the F1-corrected wave DAG, the
coherence threads, the disciplines + 5 hard gates. Governs the session_queue + kickoff.*
