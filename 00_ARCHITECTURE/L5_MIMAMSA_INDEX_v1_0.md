---
artifact: L5_MIMAMSA_INDEX_v1_0.md
canonical_id: L5_MIMAMSA_INDEX
version: 1.0
status: CURRENT — the consolidation index + complete decision register for the L5 Mīmāṃsā design corpus
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The single entry point to the L5 Mīmāṃsā design corpus authored in the 2026-06-22 Cowork session.
  Ties the five artifacts together, records EVERY native decision so far in one register, consolidates
  every open decision still needing native sign-off, and provides the coverage check that lets us
  proceed on the assumption "nothing discussed is missed." Read this first when resuming L5 work.
corpus_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md
  - L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md
  - L5_CONTRIBUTION_CONTROL_v1_0.md
  - L5_LEARNING_PROPAGATION_v1_0.md
  - ANTIGRAVITY_PASTE_L5_MIMAMSA_GROUND_AUDIT.md
  - L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md (the upstream entry point, native-supplied)
---

# L5 Mīmāṃsā — Consolidation Index & Decision Register

> Purpose: confirm **nothing discussed is missed**, give one map of the corpus, and record every
> decision (settled + open) so the next session expands on a firm baseline rather than re-deriving it.

---

## §1 — The corpus (what exists, what each does)

| # | Artifact | Status | What it owns |
|---|---|---|---|
| 0 | `L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md` | native-supplied | The campaign entry point: what L5 is, the structural-reality trap, the frozen contract, the ph_pramana seam |
| 1 | `L5_MIMAMSA_VISION_v1_0.md` | DRAFT | **The charter** — what L5 is + what it can be; the 6 value pillars; n=1/leakage honesty; the supreme-vs-complete argument; open decisions V1–V7 |
| 2 | `L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md` | DRAFT | **The arc + specs** — 6+2 phase campaign; per-asset specs for the 6 mi_*; corrected DAG; frozen-contract checklist; seal criteria |
| 3 | `L5_CONTRIBUTION_CONTROL_v1_0.md` | DRAFT | **User governance** — per-channel toggles (lel_citation, learning_influence); default-ON; per-request+saved-default; silent+metadata; portal/MCP parity; open decisions C1–C3 |
| 4 | `L5_LEARNING_PROPAGATION_v1_0.md` | DRAFT | **How learning reaches L1–L4** — overlay model; single-origin dedup; bounded+evidence-scaled; single master toggle = clean subtraction; open decisions P1–P5 |
| 5 | `L5_MIMAMSA_ELEVATION_v1_0.md` | DRAFT | **The ambitious-vision elevation** — deterministic-overlay + lifecycle (build-end + LEL-update recompute) + no-LEL mode; the tiered external-knowledge candidate catalog (astrophysics/chronobiology/statistical-astrology/esoteric) WITH the negative-control battery; the segregated controllable signal-family matrix. New decisions + reshapes V1/V7/C1/P |
| 5e | `L5_MIMAMSA_ASSET_ARCHITECTURE_v1_0.md` | DRAFT | **The corrected asset structure** (pre-build review) — 8 data + 2 service = 10 assets; table-ownership map (fold vs promote); corrected DAG; upstream-leverage map; orchestrator + registry-seed wiring spec. Supersedes the 6-asset list in CAMPAIGN_PLAN §3 |
| 5d | `L5_MIMAMSA_MASTER_ACTIVITY_LIST_v1_0.md` | CURRENT | **The end-to-end execution checklist** — every activity to get L5 ready, phases P-1→P8, dependencies/owners/gates, critical path. Drive the build from this |
| 5c | `L5_CALIBRATION_COMPARISON_MODEL_v1_0.md` | DRAFT | **How a prediction meets reality** — context-aware (full frozen bundle, not outcome-vs-outcome); multi-dimensional scorecard (timing/magnitude/domain/falsifier→composite, falsifier as judge); deterministic many-to-many matching; the scorecard→attribution link. The core of honest calibration |
| 5b | `L5_MIMAMSA_GAP_ANALYSIS_v1_0.md` | DRAFT | **The step-back supreme-product gap analysis** — gaps to elevate L5, organized by the 5 target qualities (realistic/current/reliable/high-confidence/deterministic); [UNWIRED] existing project rigor + [NEW] capabilities; the temporal meta-gap; prioritized Tier A/B/C closure |
| 6 | `ANTIGRAVITY_PASTE_L5_MIMAMSA_GROUND_AUDIT.md` | ready | **The deferred read-only audit** — to run in Claude Code AFTER L4 closes; replaces vision assumptions with ground truth |

**Dependency of ideas:** Vision (1) is the hub → Campaign Plan (2) executes it → Contribution Control
(3) + Learning Propagation (4) are the two backbone mechanisms it depends on → Audit (5) grounds (2)
against reality once L4 seals.

---

## §2 — Complete native decision register (everything ruled this session)

Every decision the native made in the 2026-06-22 session, in one place. (D# = this register's id;
"where" = the artifact that implements it.)

### Session framing
| id | decision | where |
|---|---|---|
| N1 | **Plan the L5 vision NOW** (what Mīmāṃsā is + can be to be a supreme layer); ground-truth audit is a SEPARATE step deferred until native closes L4 (worked in parallel). Vision does not need ground reality. | Vision, Campaign §P1 |
| N2 | **Deep per-file audit** when the audit runs (not inventory-level). | Audit brief Step 3 |
| N3 | **Output = both** committed `.md` artifacts AND a pasteable Antigravity prompt. | whole corpus |

### Contribution control (user governance of L5 influence)
| id | decision | where |
|---|---|---|
| N4 | **L5 fully available; user controls its IMPACT on responses.** Engine always computes; toggles act at serve time. | Contribution §1 |
| N5 | **Extensible channel framework; 2 channels lit now** — `lel_citation` + `learning_influence`. | Contribution §2 |
| N6 | **Default = BOTH ON** (full power); user opts out. | Contribution §3 |
| N7 | **Scope = per-request override on top of a saved user default.** | Contribution §3 |
| N8 | **Transparency = silent suppression + queryable metadata** (clean output, full audit). | Contribution §6 |
| N9 | **Must work identically via portal AND MCP** — parity-gated. | Contribution §4 |

### Learning propagation (how the learning reaches the layers)
| id | decision | where |
|---|---|---|
| N10 | **Attach model = OVERLAY** — L5 writes its own tables keyed to upstream ids; base L1–L4 NEVER mutated. | Propagation §3 |
| N11 | **Propagate FULL L1→L4; never L0** (L0 is global/classical, priors locked). | Propagation §1, §2 |
| N12 | **Deterministic value & adapted value STRICTLY segregated at every node; NO duplication of shared assets.** | Propagation §3, §4 |
| N13 | **Single master `learning_influence` toggle** = clean subtraction across all layers (v1; per-layer attribution stored for future per-layer toggles). | Propagation §6 |
| N14 | **Modulation BOUNDED + EVIDENCE-SCALED** — per-layer cap × evidence factor; thin n → near-zero shift. | Propagation §5 |
| N15 | **Deduplication via single-origin attribution** — a correction lives at one origin, applied exactly once per consumption path; downstream inherits by reading the corrected origin; attribution ledger blocks a second overlay from the same evidence. (Native's explicit "no double-counting across reused assets" requirement.) | Propagation §4 |

### Inherited hard rules re-affirmed (not new, but binding on L5)
| id | rule | where |
|---|---|---|
| N16 | Canonical chart `482012f1` immutable; 7 FORENSIC anchors never modulated. | Propagation §9 P4 |
| N17 | Deterministic-first; no generative LLM computes a calibration/overlay number. | Vision §8, Propagation §5 |
| N18 | L-is-authority (reference ids, never restate computed values). | Vision §6, Propagation §1 |
| N19 | Frozen orchestrator contract; Anthropic banned for instrument LLM; no audience tier; floors aspirational. | Vision §8, Campaign §4 |

---

## §3 — Consolidated OPEN decisions (everything still needing native sign-off)

All open forks across the corpus, gathered so none is lost. None blocks documentation; each shapes the build.

### From the Vision (V-series — campaign shape)
| id | decision | Cowork lean |
|---|---|---|
| V1 | First build scope: core (SCORE+ATTRIBUTE+reverse-rails) first vs full LL.1–LL.10 suite | core first |
| V2 | Re-point `mi_bhavisya` at `phala_*` now | yes, correct now |
| V3 | Held-out strategy (provenance-clean + prospective vs random 20% vs both) | both, headline the clean one |
| V4 | Reverse channel: stage-only (shadow) in v1 vs live write-back | stage-only, native-gated promotion |
| V5 | Multi-chart rails: design schema chart-keyed now vs defer | design in now |
| V6 | `mi_pariksha` scope: predictions-only vs +synthesis-answer QA | predictions-only v1 |
| V7 | Headline calibration metrics | reliability curve + Brier + hit-rate-by-tier |

### From Contribution Control (C-series — toggle details)
| id | decision | Cowork lean |
|---|---|---|
| C1 | Per-domain toggles vs global-per-request | global-per-request v1 |
| C2 | MCP exposes toggles as per-tool args vs a session-prefs tool | per-tool optional args |
| C3 | `lel_citation` OFF suppresses paraphrase too, or only literal facts | literal facts v1 |

### From Learning Propagation (P-series — mechanism constants)
| id | decision | Cowork lean |
|---|---|---|
| P1 | Exact per-layer caps `CAP_layer` | tight L1 (≤±5–10%) → wide L4 (≤±25–30%) |
| P2 | min-n gate value (below which evidence_factor=0) | reuse the calibration min-n gate (one gate) |
| P3 | Effective values: live serve-time join vs cached `effective` views | **cached views** (15+ consumer fan-out; perf) |
| P4 | FORENSIC/canonical fact exclusion list (never modulated) | 7 anchors + canonical computed facts excluded |
| P5 | Confirm v1 single-master toggle but store per-layer attribution | yes |

> **The highest-leverage open call is P3** (cached vs live effective values) because of the
> `bodha_msr_signals` 10-reader fan-out. Recommend settling it early in the build-planning session.

---

## §4 — Coverage check (did we capture everything discussed?)

Tracing every thing raised in the session to where it lives:

- ✅ "What Mīmāṃsā is and what it can be / supreme layer" → Vision §1–§3, §9.
- ✅ "L5 fully available, user controls impact" → Contribution (whole artifact); N4.
- ✅ "LEL as an L5 asset; two ways it contributes (cited facts vs full-engine calibration)" →
  Contribution §2 (the two channels are exactly these two ways); `mi_jivanaghatana` in Vision §5.
- ✅ "Turn LEL citation on/off; turn learning impact on/off; portal + MCP" → Contribution §2–§4, N5–N9.
- ✅ "Pure reading without adaptive learning vs enhanced-accuracy with it" → Contribution §5
  (learning_influence OFF == pure classical baseline); N13.
- ✅ "Learning impacts assets/responses across layers; not L0; L1→L5; structured; impact controlled" →
  Propagation (whole artifact); N10–N15.
- ✅ "Segregate deterministic vs adapted value; no deduplication of reused assets; understand how each
  asset moves across layers / who leverages it / appropriate adjusted calibration" → Propagation §2
  (real lineage from code), §3 (segregation), §4 (single-origin dedup); N12, N15.
- ✅ "Deeply understood, researched, designed" → lineage extracted from actual writer SELECTs, not
  assumed (Propagation §2; the keystone `bodha_msr_signals` 10-reader / 15+-consumer finding).
- ✅ "Document everything; nothing missed; proceed and expand" → this index.

**Known gaps that are INTENTIONAL (not misses), flagged so they're not surprises:**
1. **L4 not yet sealed** — no `L4_PHALA_CLOSE_v1_0.md`; CURRENT_STATE stale at v5.90. The audit brief
   HALTs until L4 seals. (Native is closing L4 in parallel.)
2. **Schemas are proposals** — every per-asset / overlay-table schema is vision-level, to be hardened
   against ground truth in the deferred audit, then native-ratified.
3. **The corrected DAG is a proposal** — re-pointing `mi_bhavisya` at `phala_*` (V2) awaits ground-truth
   confirmation + native sign-off.
4. **Exact numeric constants are open** — caps (P1), min-n (P2) — deliberately left for native.

---

## §5 — Proceed-from-here baseline (the assumption we build on)

When L5 work resumes, this is the agreed state to expand from:

1. **The vision is the charter** — Mīmāṃsā = the loop-closing learning/calibration layer; 6 pillars
   (SCORE, ATTRIBUTE, LEARN, FEED-BACK, EXAMINE-SELF, BE-GOVERNABLE).
2. **Two backbone mechanisms are designed** — contribution control (user governance) + learning
   propagation (overlay/dedup/bounds), both native-ruled, both grounded in real lineage.
3. **The build arc is set** — 8 phases (P0 prod-truth → P1 audit → P2 holistic → P3 specs → P4 wire →
   P5 retrieval → P5.5 contribution control → P5.6 propagation → P6 seal).
4. **Sequencing gate** — the deferred ground-truth audit runs first thing after L4 seals; it hardens
   the proposals; then native ratifies V/C/P decisions; then the autonomous build.
5. **Everything is versioned + cross-linked** — frontmatter `version`/`status`, mutual references,
   this index as the hub. Drift-detector / schema-validator registration happens when these move from
   DRAFT to CURRENT (a governance step at native's discretion; see §6).

---

## §6 — Governance housekeeping (so the corpus is properly registered)

To make this corpus first-class in the project's governance (not strictly required to *proceed*, but
required before it's CURRENT, per `CLAUDE.md §B.8` versioning discipline):

- [ ] Register the 5 new artifacts in `CAPABILITY_MANIFEST.json` (the canonical artifact catalog) when
      they move DRAFT → CURRENT.
- [ ] Add them to `CANONICAL_ARTIFACTS_v1_0.md §1` for audit-trail parity.
- [ ] At L5 campaign open, flip `CURRENT_STATE_v1_0.md` to point at the L5 campaign (and record that L4's
      missing seal was resolved upstream first).
- [ ] These artifacts are DRAFT by design until the ground-truth audit reconciles them; that
      reconciliation is when they earn CURRENT status + manifest registration.

---

*End of L5_MIMAMSA_INDEX v1.0. Five artifacts, 15 settled native decisions (N1–N15 + 4 inherited rules),
15 open decisions consolidated (V1–7, C1–3, P1–5), a full coverage check confirming nothing discussed is
missed, and the proceed-from-here baseline. This is the hub; expand from here.*
