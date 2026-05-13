---
artifact: ll2_promotion_campaign_v1_0.md
version: "1.0"
status: CLOSED
phase: M5-A
authored_session: M5-A-S1
authored_date: 2026-05-13
scope: "LL.2 per-edge promotion campaign — 8 MED-tier Pancha-MP anchor edges"
---

# LL.2 Per-Edge Promotion Campaign — M5-A

## §1 — Purpose

This document presents the 8 MED-tier Pancha-MP anchor edges from `ll2_edge_weights_v1_0.json` for native review and sign-off. These edges are the highest-confidence signal pairs in the LL.2 corpus and are required as fixed-architecture edges in the M5 DBN (Dynamic Bayesian Network) structure.

**Context:** The edges were blocked at M4-B by `promotion_blocked_reason: "LL.1 NAP.M4.5 pending"`. NAP.M4.5 has since been resolved; the structural blocker is cleared. The remaining gate is native sign-off per `SHADOW_MODE_PROTOCOL_v1_0.md §3` (LL.7 native-only mode — native sign-off is the promotion gate).

**Effect of promotion:** Each approved edge moves from `promotion_eligible: false` → `promotion_eligible: true` in `ll2_edge_weights_v1_0.json` and becomes available as a DBN architecture edge in M5-B.

---

## §2 — Signal Reference

| Signal ID | Name (abbreviated) | LL.1 match_rate | LL.1 status |
|---|---|---|---|
| SIG.MSR.117 | Hamsa Near-Miss — Jupiter 9H Trikona not Kendra | 0.3636 | `shadow_indefinite_low_match_rate` |
| SIG.MSR.118 | Ruchaka ABSENT — Mars enemy sign not kendra | 0.909¹ | `promotion_eligible_pending_two_pass` |
| SIG.MSR.119 | Malavya ABSENT — Venus not own/exalted kendra | 0.4545 | `promotion_eligible_pending_two_pass` |
| SIG.MSR.143 | Sarpa Yoga ABSENT — no three serpent planets in angles | 0.4545 | `promotion_eligible_pending_two_pass` |
| SIG.MSR.145 | Parivartana Exchange Saturn-10L / Venus-7L | 0.9091 | `promotion_eligible_pending_two_pass` |
| SIG.MSR.402 | Hidden-Pinnacle 8H Architecture via Varnada+Ghati Lagnas | 0.7273 | `promotion_eligible_pending_two_pass` |

¹ SIG.MSR.118 match_rate read from edge endpoint data. SIG.MSR.117 is `shadow_indefinite_low_match_rate`; its endpoint status means the edge inherits a conditional-promotion note at §3 below.

---

## §3 — 8 MED-Tier Edge Promotion Requests

### EDGE-01: SIG.MSR.145 ↔ SIG.MSR.402

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_145__SIG_MSR_402` |
| Signal pair | Parivartana Exchange (Saturn-10L/Venus-7L) ↔ Hidden-Pinnacle 8H Architecture |
| Co-count | 7 (highest in corpus) |
| Normalized weight | 0.1892 |
| LL.7 classification | NOVEL (no CDLM anchor — MSR.145 not patchable, OPEN_ITEM.P1.1) |
| Current promotion status | BLOCKED (NAP.M4.5 cleared; now pending native sign-off) |
| Both endpoints eligible | Yes (both `promotion_eligible_pending_two_pass`) |
| Astrology rationale | The Parivartana creates a Saturn-Venus mutual reception tightly linking career (10H) and relationship/desire (7H). The 8H Hidden-Pinnacle (Varnada+Ghati Lagna) configuration activates under sustained dasha pressure — empirically these co-fire across transformative career-and-relationship junctures. co_count=7 out of 37 training events is the strongest observed signal pair. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

### EDGE-02: SIG.MSR.118 ↔ SIG.MSR.145

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_118__SIG_MSR_145` |
| Signal pair | Ruchaka ABSENT (Mars not in own/exalted kendra) ↔ Parivartana Exchange |
| Co-count | 5 |
| Normalized weight | 0.1351 |
| LL.7 classification | NOVEL |
| Both endpoints eligible | Yes |
| Astrology rationale | Ruchaka's absence means Mars energy routes via lesser channels — under conditions where the Parivartana (Saturn-Venus exchange) is active, the absence of Ruchaka creates a characteristic pattern: career and relationship moves happen through diplomatic/saturnine channels rather than martial assertion. Co-fires across 5 career-pivot events. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

### EDGE-03: SIG.MSR.119 ↔ SIG.MSR.402

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_119__SIG_MSR_402` |
| Signal pair | Malavya ABSENT (Venus not in own/exalted kendra) ↔ Hidden-Pinnacle 8H Architecture |
| Co-count | 5 |
| Normalized weight | 0.1351 |
| LL.7 classification | NOVEL |
| Both endpoints eligible | Yes |
| Astrology rationale | Malavya's absence (Venus not in a kendra in own/exalted sign) means Venus operates via transformation channels rather than direct pleasure/comfort. The 8H Hidden-Pinnacle co-fires with Venus operating in this mode — empirically these coincide across transformative events where pleasure/relationships are an undercurrent rather than the primary domain. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

### EDGE-04: SIG.MSR.143 ↔ SIG.MSR.145

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_143__SIG_MSR_145` |
| Signal pair | Sarpa Yoga ABSENT (no three serpent planets in angles) ↔ Parivartana Exchange |
| Co-count | 5 |
| Normalized weight | 0.1351 |
| LL.7 classification | NOVEL |
| Both endpoints eligible | Yes |
| Astrology rationale | Sarpa Yoga's absence is a positive finding (its presence would constrict outcomes). The Parivartana co-fires with this absent-Sarpa condition across 5 events spanning 2000–2007 — a period of significant career and relationship architecture. The combination signals a structural openness in outcomes when the Parivartana is active. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

### EDGE-05: SIG.MSR.143 ↔ SIG.MSR.402

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_143__SIG_MSR_402` |
| Signal pair | Sarpa Yoga ABSENT ↔ Hidden-Pinnacle 8H Architecture |
| Co-count | 5 |
| Normalized weight | 0.1351 |
| LL.7 classification | NOVEL |
| Both endpoints eligible | Yes |
| Astrology rationale | Same event cluster as EDGE-04 (2000–2007). When the 8H Hidden-Pinnacle is active, the absence of constricting Sarpa Yoga allows the hidden-pinnacle architecture to manifest at elevated amplitude. These are co-present structurally, not causally ordered. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

### EDGE-06: SIG.MSR.117 ↔ SIG.MSR.119

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_117__SIG_MSR_119` |
| Signal pair | Hamsa Near-Miss (Jupiter 9H Trikona not Kendra) ↔ Malavya ABSENT |
| Co-count | 4 |
| Normalized weight | 0.1081 |
| LL.7 classification | NOVEL |
| Endpoint caveat | SIG.MSR.117 is `shadow_indefinite_low_match_rate` (0.3636). Promotion of this edge is conditional on SIG.MSR.117 remaining in the DBN as a shadow node. |
| Astrology rationale | Jupiter in a Trikona but not a Kendra (near-miss Hamsa) + absent Malavya = both benefic yoga absences together. These co-fire across transformative inflection points where benefic yoga potential exists structurally but does not manifest in the classical form — relevant to periods of effort-before-reward or near-breakthrough events. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE (conditional on MSR.117 shadow-node status) ☐ DEFER ☐ REJECT |

---

### EDGE-07: SIG.MSR.117 ↔ SIG.MSR.402

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_117__SIG_MSR_402` |
| Signal pair | Hamsa Near-Miss ↔ Hidden-Pinnacle 8H Architecture |
| Co-count | 4 |
| Normalized weight | 0.1081 |
| LL.7 classification | NOVEL |
| Endpoint caveat | SIG.MSR.117 `shadow_indefinite_low_match_rate`. Conditional promotion as above. |
| Astrology rationale | Jupiter's near-Hamsa condition + the 8H Hidden-Pinnacle co-fire across 4 transformative events including the birth event and 2001/2003/2011 junctures. Jupiter as near-benefic modulates the 8H intensity without classical Hamsa protection — a characteristic pattern of this chart's resilience under transformation pressure. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE (conditional on MSR.117 shadow-node status) ☐ DEFER ☐ REJECT |

---

### EDGE-08: SIG.MSR.119 ↔ SIG.MSR.145

| Field | Value |
|---|---|
| Edge ID | `EDGE.SIG_MSR_119__SIG_MSR_145` |
| Signal pair | Malavya ABSENT ↔ Parivartana Exchange |
| Co-count | 4 |
| Normalized weight | 0.1081 |
| LL.7 classification | NOVEL |
| Both endpoints eligible | Yes |
| Astrology rationale | Malavya ABSENT (Venus not in own/exalted kendra) + Parivartana Exchange (Saturn-Venus mutual): a chart in which Venus operates via exchange rather than autonomous kendra placement. The co-firing pattern across EVT.1984/2000/2001/2003 captures the foundational structural condition that applies across the lifespan, not just episodically. |
| **NATIVE APPROVAL REQUEST** | ☐ APPROVE for DBN edge inclusion ☐ DEFER ☐ REJECT |

---

## §4 — Batch Approval Option

~~Batch approval option superseded by per-edge native review at NAP.M5.1 (Cowork-M5-B-S1-NAP.M5.1, 2026-05-13). See §6 for outcomes.~~

---

## §5 — Residuals and Open Items

| Item | Status |
|---|---|
| OPEN_ITEM.P1.1 — MSR.145 CDLM cell absent | CARRIED FORWARD; SIG.MSR.145 label correction now also required (M5-B-S2) |
| SIG.MSR.117 shadow_indefinite status | Remains in shadow; EDGE-06 approved conditional on this |
| LL.7 classification for all 8 edges | NOVEL (no CDLM anchor confirmed at M5-A-S1) |
| SIG.MSR.145 label correction | NEW — "Parivartana" label confirmed incorrect by native 2026-05-13; relabeling required in M5-B-S2 |
| SIG.MSR.402 invalidation resolution | NEW — SIG.MSR.402 invalidated in MSR v2.0; edges using it need SIG.MSR.402b co-occurrence re-check in M5-B-S2 |

---

## §6 — NAP.M5.1 Native Review Outcomes — FINAL (2026-05-13)

Two-round review at Cowork-M5-B-S1-NAP.M5.1:
- Round 1: Signal label verification (SIG.MSR.145 Parivartana voided; SIG.MSR.402 invalidation confirmed)
- Round 2: Native correlation questioning — plain-language empirical confirmation per edge

| Edge | Signal Pair | Final Decision | Basis |
|---|---|---|---|
| EDGE-01 | SIG.MSR.145 ↔ SIG.MSR.402 | **APPROVED_CONDITIONAL** | Empirical correlation confirmed by native ("career/finance shifts co-move with relationship quality throughout life"). SIG.MSR.402 endpoint requires 402b substitution in M5-B-S2 before DBN inclusion. |
| EDGE-02 | SIG.MSR.118 ↔ SIG.MSR.145 | **REJECTED** | Native cannot speak definitively to this correlation. |
| EDGE-03 | SIG.MSR.119 ↔ SIG.MSR.402 | **REJECTED** | Native cannot speak definitively to this correlation. |
| EDGE-04 | SIG.MSR.143 ↔ SIG.MSR.145 | **APPROVED** ✓ | Native confirmed: authority structures not obstructing career; progress through people and relationships. Both endpoints valid. |
| EDGE-05 | SIG.MSR.143 ↔ SIG.MSR.402 | **REJECTED** | Native cannot speak definitively to this correlation. |
| EDGE-06 | SIG.MSR.117 ↔ SIG.MSR.119 | **APPROVED** ✓ | Confirmed (Round 1 + Round 2). Conditional on SIG.MSR.117 shadow-node status. |
| EDGE-07 | SIG.MSR.117 ↔ SIG.MSR.402 | **REJECTED** | Native cannot speak definitively to this correlation. |
| EDGE-08 | SIG.MSR.119 ↔ SIG.MSR.145 | **APPROVED** ✓ | Native confirmed: career shifts and relationship shifts move together throughout life. Both endpoints valid. |

**Final net: 3 fully approved (EDGE-04, EDGE-06, EDGE-08) + 1 conditional (EDGE-01, pending 402b) + 4 rejected (EDGE-02, 03, 05, 07).**

**M5-B-S2 one remaining action:**
- EDGE-01 only: substitute SIG.MSR.402 → SIG.MSR.402b, run co-occurrence re-check, confirm empirical pattern holds under corrected endpoint, then promote to `promotion_eligible: true`.

**SIG.MSR.145 label correction:** COMPLETE — relabeled in MSR_v3_0.md at NAP.M5.1 (2026-05-13). Now reads "Structural — Saturn-10L Tenanting Venus's Sign (Libra 7H): One-Way Dispositorship Chain, No Parivartana."

---

*Authored M5-A-S1 (2026-05-13). Final decisions recorded 2026-05-13 at Cowork-M5-B-S1-NAP.M5.1-final. Status: CLOSED — 3 approved, 1 conditional (M5-B-S2), 4 rejected.*
