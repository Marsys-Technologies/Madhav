---
artifact: CLAUDECODE_BRIEF_WS2_AUTONOMOUS_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS2_AUTONOMOUS_ACTIVATION
version: 1.0
status: READY_FOR_EXECUTION (kick after WS-1 wave-close OR in parallel from WS-1 start; different worktree, no file overlap)
project_codename: Brahma — WS-2 Depth Build (Honest Volume Floors)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code in Antigravity — Conductor + RUNTIME_GUARDIAN_MODE
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + AUTONOMOUS_MODE + RUNTIME_GUARDIAN_MODE
predecessor: tag `legacy-cleanup-arc-complete` (ccc66c77)
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS2
branch: feature/ws2-depth-build
no_backup: true
human_gates: NONE
external_dependency: WS-3 must close before L2-grounded session releases
---

# WS-2 Autonomous Activation — Depth Build

Six layers, asset-by-asset, honest volume floors. RUNTIME_GUARDIAN_MODE: Drashta drives real chart-builds through the live portal (the WS-1 cockpit observes them); Pramāṇa enforces volume floor ≥ expected; Sambandha enforces dependency completeness; Darpaṇa enforces render-coverage. AUTONOMOUS_MODE rails on. **One layer can park without halting other layers within the same layer-group** — assets within a layer build in parallel.

## §1 The honest volume contract (the headline change vs WS-1's thin-data baseline)

Per BRAHMA_COMPLETION_PLAN §D: the root cause of the thin first slice (9 positions vs 9 × 5 ayanamshas; 819 dashas vs Sukshma depth; 21 graph edges vs 573 signals) was volume-floor gates passing thin data green. WS-2 fixes this by declaring an explicit `volume_floor` per asset, computed from FORENSIC v8.0 coverage benchmark × ayanamsha count, and the acceptance gate asserts `actual_rows ≥ floor` OR amber. No green-on-thin.

The per-asset Contract Registry the swarm consumes lives at `00_ARCHITECTURE/CONDUCTOR/ws2/contract_registry.yaml` and seeds from the existing per-layer specs (LAYER_0..LAYER_5 design docs + the v2 MASTER_ARCHITECTURE additions).

## §2 Setup (CC executes once)

```bash
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../MadhavWS2 -b feature/ws2-depth-build legacy-cleanup-arc-complete
cd MadhavWS2

# Bot identity — same brahma-swarm-bot, same scope
# Conductor + contract-registry setup
mkdir -p 00_ARCHITECTURE/CONDUCTOR/ws2

# Seed the contract registry from the existing per-layer specs.
# CC reads each LAYER_N_*_DESIGN_v1_0.md + the master architecture v2.1 §D additions
# and emits one entry per asset listed there.
```

## §3 Conductor queue topology (6 layer groups + sync points)

```yaml
# 00_ARCHITECTURE/CONDUCTOR/ws2/session_queue.yaml
wave: ws2
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS2
branch: feature/ws2-depth-build
mode: AUTONOMOUS_MODE + RUNTIME_GUARDIAN_MODE
max_run_budget_usd: 5000
max_spend_per_asset_usd: 300  # rule-extraction asset gets 1000 per AUTONOMOUS_MODE §C
parallel_assets_per_layer: true  # assets within a layer build in parallel worktree subdirs

sessions:
  - id: l0-brahmagyan
    layer: brahmagyan
    assets:
      - brahmagyan.ephemeris       # ephemeris, full date range × bodies
      - brahmagyan.reference       # all chakra tables, dignities, nakshatra attrs
      - brahmagyan.texts           # BPHS, Jaimini, KP, Tajaka (licensing per text — hard-blocker)
      - brahmagyan.text_index      # hybrid retrieval (HNSW + BM25 + reranker)
      - brahmagyan.ontology        # controlled vocab + synonyms
      - brahmagyan.almanac         # location-parameterized panchang
      - brahmagyan.remedy_corpus   # NEW v2 — classical upaya texts indexed
      # brahmagyan.rules is WS-3 territory (not here)
    volume_floors: per L0_CONTRACT_REGISTRY_SEED + master arch §D L0
    acceptance: |
      Per asset: real volume ≥ floor; provenance envelope present; retrieval tool live web + MCP;
      tool tested against the freshly-generated data; astronomical ground-truth check passes
      (Swiss/JPL spot-check — not JH parity).
    notes: |
      L0 is one-time global. After L0 verifies, every later chart sees Brahmagyan already green.
      Native may want to spot-check the classical-text licensing decisions before bulk text import —
      flag in Smṛti if uncertain.

  - id: l1-ganita
    depends_on: [l0-brahmagyan]
    layer: ganita
    assets:
      - ganita.engine              # PyJHora superset of FORENSIC v8.0
      - ganita.positions           # 5 ayanamshas × bodies (NOT 1 × grahas)
      - ganita.divisionals         # D1–D60
      - ganita.dashas              # 12 systems to Sukshma depth (NOT MD/AD/PD only)
      - ganita.strength            # shadbala + ashtakavarga + bhava_bala
      - ganita.sensitive_points    # upagrahas + special lagnas + sahams + arudhas
      - ganita.panchanga           # birth-moment panchang
      - ganita.facts_store + ganita.forensic_render
    volume_floors: enumerated superset per FACT_ENGINE_A1_SCOPE_ANALYSIS
    acceptance: |
      Engine reproduces the FORENSIC v8.0 superset; ayanamsha-invariant split working;
      determinism hash-stable across re-runs; per-asset tool live + tested.

  - id: l2-bodha-scaffold
    depends_on: [l1-ganita]
    layer: bodha
    assets:
      - bodha.signals              # MSR — SCAFFOLD ONLY (ungrounded; awaits WS-3 rules)
      - bodha.graph                # CGM
      - bodha.domain_links         # CDLM
      - bodha.resonance            # RM
      - bodha.lenses + bodha.negative_space + bodha.salience
      - bodha.embeddings           # vector per signal
      - bodha.holistic_bundle      # composite tool — B.11 whole-chart-read
      # bodha.remediation depends on WS-3 too (cites remedy rules); ungrounded scaffold here
    volume_floors: 573-signal target from MSR v5.0 + ~K-edge target from CGM v9.0
    acceptance: |
      Scaffold: signal-derivation logic + tool surfaces in place; volumes meet floor;
      EXPLICITLY MARKED UNGROUNDED in provenance envelope (rule_id = null, awaiting WS-3).
      L2-grounded session (later) re-derives every signal against the Rule Base.
    notes: |
      This session establishes the scaffold + tools. The "grounded" pass is l2-bodha-grounded
      below, which depends on WS-3 closing.

  - id: l3-kala
    depends_on: [l2-bodha-scaffold]
    layer: kala
    assets:
      - kala.timeline              # dasha × transit alignment
      - kala.convergence           # convergence windows
      - kala.obstruction + kala.snapshot
      - kala.temporal              # composite
      # kala.spatial deferred per master arch §I.4
    acceptance: |
      Fabric deterministic (hash-stable re-runs); convergence windows reproduce against known
      life-period alignments from LEL.

  - id: l4-phala
    depends_on: [l2-bodha-scaffold, l3-kala]
    layer: phala
    assets:
      - phala.anchors              # event anchors with explicit falsifiers + calibrated confidence
      - phala.mitigation
      - phala.rectification        # train/test split inside LEL — no leakage
      - phala.muhurta              # NEW v2 — electional inversion of L4
      - phala.outlook              # composite
    acceptance: |
      Every anchor carries a falsifier; rectification leak-free; muhurta returns ranked windows
      for a desired action. Correlation-aware confidence per master arch §C7.

  - id: l5-mimamsa
    depends_on: [l4-phala]
    layer: mimamsa
    assets:
      - mimamsa.lel_intake         # full 57 events from LIFE_EVENT_LOG_v1_2.md
      - mimamsa.event_chart_state_index
      - mimamsa.calibration_substrate
      - mimamsa.learning_multiplier
      - mimamsa.bigquery_export    # OLAP path per master arch §C3
    acceptance: |
      LEL stays isolated (never feeds generation); event chart-state index derives from PyJHora;
      multiplier mechanism wired but at 1.0 until corpus evidence exists.

  # ===== WS-3 SYNC POINT =====
  # The grounded session below is RELEASED only when WS-3's rule extraction has tagged
  # `ws3-rule-base-complete`. The Conductor polls for that tag every 15 min during this gap.
  # =============================

  - id: l2-bodha-grounded
    depends_on: [l2-bodha-scaffold, ws3-tag:ws3-rule-base-complete]
    layer: bodha
    assets:
      - bodha.signals (re-derive)  # every signal grounded to WS-3 rule_id, cited
      - bodha.remediation          # NEW v2 — now real, with cited remedies
      - bodha.lenses (re-verify)
    acceptance: |
      Every signal carries rule_id + verse citation; remediation prescriptions cite L0 remedy corpus.

  - id: l3-l4-reverify
    depends_on: [l2-bodha-grounded]
    scope: re-verify L3 / L4 outputs that inherited from ungrounded signals
    acceptance: temporal fabric + anchors still pass their gates against grounded signals.

  - id: red-team-is8b
    depends_on: [l3-l4-reverify, l5-mimamsa]
    role: adversarial swarm (Pramāṇa + external red-team agent)
    scope: per master arch §IS.8(b) — full-instrument red team on the grounded, full-depth instrument
    acceptance: no class-1 findings; class-2 findings have remediation plan committed.

  - id: wave-close
    role: Sūtradhāra + Pramāṇa + Pratiṣṭhā
    scope: |
      Final WS-2 AC sweep; PR opens; CI green; swarm merges; tag `ws2-depth-build-complete`.
```

## §4 RUNTIME_GUARDIAN integration (the live observability loop)

Per RUNTIME_GUARDIAN_MODE §B: every layer session runs by driving a real chart-build through `madhav.marsys.in` (the WS-1 portal). Drashta clicks Build; the swarm watches per-asset events fire; Pramāṇa checks data lands at volume; the WS-1 cockpit's Layer Tower is the human-readable observability surface.

This means **WS-2 implicitly depends on WS-1 S2 being live for the best observability experience** — but it's NOT a hard dependency. Without WS-1 S2, the swarm reads progress from `build_events` directly via psql + Cloud Run logs. With WS-1 S2, the cockpit makes the same data visible to the native at a glance.

## §5 Acceptance criteria (wave-complete)

- AC-1: Every asset in §3 passes its acceptance_gate or is explicitly parked + logged with reason
- AC-2: For every parked asset, Smṛti contains the failure trace + every attempted fix
- AC-3: Total run spend ≤ $5000; no single asset exceeded its $300 cap (or $1000 for rules)
- AC-4: Astronomical ground-truth spot-checks pass for L0/L1 (Swiss/JPL — not FORENSIC parity)
- AC-5: L2-grounded ≥ 95% signal grounding coverage (every signal cites a rule_id from WS-3)
- AC-6: L5 LEL ingested at 57 events with derived event chart-state index
- AC-7: Red-team IS.8(b) — zero class-1 findings on the full-depth grounded instrument
- AC-8: PR auto-merged; tag `ws2-depth-build-complete` pushed

## §6 Hard stops — none synchronous

The wave runs to completion without native intervention. All exceptional events route through `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`:

- **L0 classical-text licensing block** → Tier-2 disposition classifier parks the affected text + STUB the dependent retrieval tools; adjacent texts continue; Smṛti logs the disposition.
- **L1 engine astronomical ground-truth fail** → Tier-2 engine self-repair (§B.4): pin known-good PyJHora → Swiss Ephemeris fallback → auto-file upstream issue → continue on safe path. Only parks if all three fail.
- **L2-grounded waits on WS-3 tag** → Tier-2: Conductor polls every 15 min; no notification needed until 14 days elapse (then async Smṛti entry).
- **Spend approaches cap** → Tier-2 auto-budget raise (§B.3): per-asset $300 → $600 → $1000 → $2000 within wave ceiling.
- **Class-1 red-team finding** → Tier-1 Severity Remediator (§C.2): elevated-rigor autonomous fix; Vimarśaka audits with extra scrutiny.
- **Wave hits absolute $5k ceiling** → Tier-3 (only event): swarm stops at next checkpoint, async notification, native authorizes ceiling raise from any device, swarm resumes.

## §7 Out of WS-2 scope

| # | Item | Owner |
|---|------|-------|
| 1 | Rule Base extraction | WS-3 |
| 2 | Spatial (relocational) module | post-single-chart per master arch §I.4 |
| 3 | Relational/composite graph (multi-native) | post-single-chart per master arch §I.4 |
| 4 | Portal UI work | WS-1 (parallel wave) |

---

*End of WS-2 Autonomous Activation. RUNTIME_GUARDIAN_MODE + AUTONOMOUS_MODE + 6 layer groups + WS-3 sync point + IS.8(b) red-team. Swarm drives; native observes via cockpit + Smṛti.*
