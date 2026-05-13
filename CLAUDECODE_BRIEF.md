---
status: COMPLETE
session_id: M5-B-S1
session_scope: >
  DBN Topology Design — draft DBN_TOPOLOGY_v1_0.md; resolve LL.2 per-edge campaign;
  emit session-open handshake; close with CURRENT_STATE + SESSION_LOG update.
authored: 2026-05-13
authored_by: Claude Sonnet 4.6 (Cowork session — Madhav M5-B-S1 handshake)
supersedes: "M5-A-S1 CLAUDECODE_BRIEF (COMPLETE)"
---

# CLAUDECODE_BRIEF — M5-B-S1
## MARSYS-JIS | DBN Topology Design

---

## §0 — Executor orientation

**Read this file's `status` first.** If `status: COMPLETE`, skip and proceed with `CLAUDE.md §C` normally.

**Status is OPEN. This brief governs you entirely for this session.**

You are executing M5-B-S1 of MARSYS-JIS: the first session of sub-phase M5-B (DBN Topology Design). M5-A is fully closed. Your single primary deliverable is `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` — the first committed draft of the Dynamic Bayesian Network topology for this native's chart. You will also advance the LL.2 per-edge promotion campaign and close the session properly.

**Execution vehicle:** marsys-m5-dbn worktree on `feature/m5-probabilistic-model` (check it exists; if not, create it: `git worktree add ../marsys-m5-dbn feature/m5-probabilistic-model` or `git checkout -b feature/m5-probabilistic-model` if the branch doesn't exist yet).

**LLM stack rule (hard constraint):** Gemini → DeepSeek → NIM. **No Anthropic/Claude API calls.** If any scaffold or eval code calls a model, it must call DeepSeek or Gemini. Flag any violation.

**Held-out partition rule (hard constraint):** The held-out LEL partition (formally declared at M5-A-S1) is SACROSANCT. Do not read held-out event outcomes during topology design. The topology must be committed before the held-out data is consulted. Any held-out event IDs found in the partition declaration file must NOT be loaded for their outcome/notes fields. Load event IDs only; treat outcome fields as blinded.

---

## §1 — Mandatory reading at session open (in order)

Execute these reads **before any file creation or modification**:

```
1.  CLAUDE.md                                                          (project instructions)
2.  00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2                          (canonical state block — confirm M5-B INCOMING)
3.  00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md §3 M5-B                    (M5-B scope + ACs)
4.  00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M5                            (DBN scope + risks + agent roles)
5.  06_LEARNING_LAYER/M4_CLOSE_v1_0.md §5                             (M5 setup recommendations from M4 close)
6.  06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
                                                                        (30 production signals — full scan)
7.  06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json
                                                                        (9,922 edges — read schema + top-weight rows)
8.  06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll7_discovery_prior_v1_0.json
                                                                        (243 edges: 107 novel + 136 unconfirmed)
9.  06_LEARNING_LAYER/dbn/ll2_promotion_campaign_v1_0.md               (8 MED-tier edges — PENDING_NATIVE_APPROVAL)
10. 06_LEARNING_LAYER/dbn/ll8_bayesian_update/LL8_SPEC_v1_0.md         (LL.8 scaffold — understand update interface)
11. 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL5_DASHA_TRANSIT_DESIGN_v1_0.md
                                                                        (dasha-transit axis-weight modulator — time-slice reference)
12. 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL4_PREDICTION_PRIOR_v1_0.md
                                                                        (domain priors — informs CPT initialization)
13. 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md                                (81 cross-domain linkage cells — domain edge structure)
14. 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md §I                               (signal set declared count + domain buckets)
15. 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §1 §2 §5 §6      (core chart: ascendant, planets, dashas — topology foundation)
16. 01_FACTS_LAYER/LIFE_EVENT_LOG_*.md                                  (TRAINING PARTITION ONLY — load event metadata, NOT held-out outcomes)
    ↳ Read the held-out partition declaration file (authored at M5-A-S1; find it in 06_LEARNING_LAYER/dbn/ or 01_FACTS_LAYER/)
      to identify held-out event IDs. Then read the LEL but skip outcome/notes fields for those IDs.
17. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–C.6     (enforcement axes)
18. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md                       (handshake schema)
19. 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md                      (close-checklist schema)
```

---

## §2 — Session-open handshake (emit before any substantive work)

After completing the mandatory reads, emit the following handshake to stdout and append it to `00_ARCHITECTURE/SESSION_LOG.md` as the opening block of the M5-B-S1 entry:

```yaml
session_open:
  session_id: M5-B-S1
  cowork_thread_name: "Madhav M5-B-S1 — DBN Topology Design"
  agent_name: claude-sonnet-4-6          # or whichever model is running this
  agent_version: claude-sonnet-4-6
  step_number_or_macro_phase: M5.B.1
  predecessor_session: M5-A-S1
  mandatory_reading_confirmation:
    # Populate with actual fingerprint_sha256 from sha256sum of each file at read time.
    # Use: sha256sum <file> | awk '{print $1}'
    - file: CLAUDE.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 06_LEARNING_LAYER/dbn/ll2_promotion_campaign_v1_0.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    - file: 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
      fingerprint_sha256: "<computed>"
      read_at: "<ISO timestamp>"
    # ... (add remaining mandatory reads)
  canonical_artifact_fingerprint_check:
    - canonical_id: FORENSIC
      declared_fingerprint: "<from CAPABILITY_MANIFEST.json>"
      observed_fingerprint: "<computed>"
      match: true
    - canonical_id: CDLM
      declared_fingerprint: "<from CAPABILITY_MANIFEST.json>"
      observed_fingerprint: "<computed>"
      match: true
    - canonical_id: MSR
      declared_fingerprint: "<from CAPABILITY_MANIFEST.json>"
      observed_fingerprint: "<computed>"
      match: true
    - canonical_id: MACRO_PLAN
      declared_fingerprint: "<from CAPABILITY_MANIFEST.json>"
      observed_fingerprint: "<computed>"
      match: true
  declared_scope:
    may_touch:
      - 06_LEARNING_LAYER/dbn/**
      - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json
      - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      - 00_ARCHITECTURE/SESSION_LOG.md
      - .geminirules
      - .gemini/project_state.md
    must_not_touch:
      - 01_FACTS_LAYER/**
      - 025_HOLISTIC_SYNTHESIS/**
      - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/**
      - 06_LEARNING_LAYER/dbn/PRIOR_SPEC_v1_0.md
      - 06_LEARNING_LAYER/dbn/dbn_params_v1_0.json
      - platform/src/**
      - platform/lib/**
      - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  mirror_pair_freshness_check:
    - pair_id: MP.1
      claude_side: CLAUDE.md
      gemini_side: .geminirules
      last_verified_on: 2026-05-13
      days_since_verification: 0
      stale: false
    - pair_id: MP.2
      claude_side: "composite(CURRENT_STATE + SESSION_LOG + PHASE_M5_PLAN pointer)"
      gemini_side: .gemini/project_state.md
      last_verified_on: 2026-05-13
      days_since_verification: 0
      stale: false
    - pair_id: MP.4
      claude_side: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
      gemini_side: "phase-plan pointer in .gemini/project_state.md"
      last_verified_on: 2026-05-13
      days_since_verification: 0
      stale: false
    - pair_id: MP.6
      claude_side: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
      gemini_side: null
      claude_only: true
      stale: false
    - pair_id: MP.7
      claude_side: 00_ARCHITECTURE/SESSION_LOG.md
      gemini_side: null
      claude_only: true
      stale: false
  native_directive_obligations:
    - directive_id: ND.1
      status: "addressed (2026-04-24 at Step 7 close)"
      obligation_summary: "No open directives. Mirror discipline ongoing."
      acknowledged: true
  red_team_due: false
    # red_team_counter: 1 at M5-A-S1 close. This session = 2. IS.8(a) fires at 3.
  notes: >
    M5-B-S1. Primary deliverable: DBN_TOPOLOGY_v1_0.md (DRAFT status at this session;
    CLOSED at NAP.M5.1). Held-out partition is sacrosanct — do not consult outcomes.
    LL.2 per-edge campaign document exists at ll2_promotion_campaign_v1_0.md;
    8 edges PENDING_NATIVE_APPROVAL. LLM stack: Gemini→DeepSeek→NIM; no Anthropic API.
```

---

## §3 — Pre-flight checks (before topology authoring)

Run these checks before writing any new files:

### 3.1 — M5-A deliverable inventory
Confirm each M5-A AC is present on disk:

```bash
# LL.8 scaffold
ls 06_LEARNING_LAYER/dbn/ll8_bayesian_update/LL8_SPEC_v1_0.md
ls 06_LEARNING_LAYER/dbn/ll8_bayesian_update/parameter_register_stub.json

# LL.9 scaffold
ls 06_LEARNING_LAYER/miss_registry/LL9_SPEC_v1_0.md

# LL.2 campaign
ls 06_LEARNING_LAYER/dbn/ll2_promotion_campaign_v1_0.md

# Held-out partition declaration
find 06_LEARNING_LAYER/dbn/ 01_FACTS_LAYER/ -name "*held_out*" -o -name "*partition*" | head -20
find 06_LEARNING_LAYER/ -name "*ppl*" -o -name "*prospective*" | head -20

# DIS.009 closure
grep -l "DIS.009\|RESOLVED_R1" 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md

# answer:eval scaffold
ls platform/scripts/eval/ 2>/dev/null || echo "MISSING — flag if M5-A did not create this"
```

Report any missing item but **do not block** on them — M5-B-S1 is not a remediation session. Carry missing items as a note in the session log.

### 3.2 — Production signal extraction
Parse `ll1_weights_promoted_v1_0.json` to extract a working table:

```bash
python3 - << 'EOF'
import json, sys
with open('06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json') as f:
    d = json.load(f)
weights = d.get('signal_weights', {})
rows = []
for sig_id, sig in weights.items():
    rows.append({
        'signal_id': sig_id,
        'domain': sig.get('domain', 'unknown'),
        'production_weight': sig.get('production_weight', 0),
        'mean_match_rate': sig.get('mean_match_rate', 0),
        'status': sig.get('status', ''),
        'n_observations': sig.get('n_observations', 0),
    })
rows.sort(key=lambda r: -r['production_weight'])
print(f"Total production signals: {len(rows)}")
print("\n--- Signal table (sorted by production weight) ---")
print(f"{'SIG_ID':<20} {'DOMAIN':<20} {'PROD_WT':<10} {'MATCH_RT':<10} {'N_OBS':<6}")
print("-" * 70)
for r in rows:
    print(f"{r['signal_id']:<20} {r['domain']:<20} {r['production_weight']:<10.4f} {r['mean_match_rate']:<10.4f} {r['n_observations']:<6}")
EOF
```

Save this table — you will use it to assign every production signal to a DBN node type (observed / latent / exogenous) in §4 below.

### 3.3 — Edge-weight corpus summary
```bash
python3 - << 'EOF'
import json
with open('06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json') as f:
    d = json.load(f)
edges = d.get('edges', d) if isinstance(d, dict) else d
# Try both schemas
if isinstance(edges, dict):
    edge_list = list(edges.values())
elif isinstance(edges, list):
    edge_list = edges
else:
    edge_list = []
edge_list_sorted = sorted(edge_list, key=lambda e: -e.get('normalized_weight', e.get('weight', 0)))
print(f"Total edges: {len(edge_list)}")
print("\n--- Top 20 edges by weight ---")
for e in edge_list_sorted[:20]:
    src = e.get('source', e.get('signal_a', e.get('sig_a', '?')))
    tgt = e.get('target', e.get('signal_b', e.get('sig_b', '?')))
    wt = e.get('normalized_weight', e.get('weight', 0))
    co = e.get('co_count', e.get('co_occurrence', '?'))
    ll7 = e.get('ll7_classification', '?')
    print(f"  {src} ↔ {tgt}  weight={wt:.4f}  co_count={co}  ll7={ll7}")
EOF
```

### 3.4 — LL.7 classification summary
```bash
python3 - << 'EOF'
import json
with open('06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll7_discovery_prior_v1_0.json') as f:
    d = json.load(f)
# Count by classification
from collections import Counter
edges = d.get('edges', [])
if isinstance(edges, dict):
    edges = list(edges.values())
counts = Counter(e.get('classification', e.get('ll7_classification', 'unknown')) for e in edges)
print(f"LL.7 edge count: {len(edges)}")
print("Classification breakdown:", dict(counts))
# Novel edges only
novel = [e for e in edges if 'novel' in str(e.get('classification', e.get('ll7_classification', ''))).lower()]
novel_sorted = sorted(novel, key=lambda e: -e.get('co_count', 0))
print(f"\nTop 10 NOVEL edges:")
for e in novel_sorted[:10]:
    src = e.get('source', e.get('sig_a', '?'))
    tgt = e.get('target', e.get('sig_b', '?'))
    co = e.get('co_count', '?')
    print(f"  {src} ↔ {tgt}  co_count={co}")
EOF
```

### 3.5 — CDLM domain matrix read
From `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`, extract the domain pair structure (9×9 = 81 cells). You are looking for:
- Which MSR signal IDs appear as `msr_anchors` in each cell
- Which domain pairs have HIGH linkage strength (to inform DBN cross-domain edges)

Parse or read manually. Summarize: which 4-5 domain pairs have the most and strongest CDLM anchors? These will be the cross-domain edges in the DBN topology.

---

## §4 — Primary deliverable: `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md`

This is the main work of M5-B-S1. Author this file in full. Below are the design decisions that must be encoded, followed by the required section structure.

---

### 4.1 — Design decisions (pre-committed; encode in §2 of the artifact)

These decisions are made before the held-out partition is seen. They must be committed in writing before any fitting happens.

**Decision D1 — Time-slice unit: Vimshottari antardasha period**

Rationale: The Vimshottari antardasha (sub-period) is the natural atomic unit for Jyotish prediction. Antardasha periods average 12–24 months — the right granularity for life events in the LEL. The LEL events are annotated with dasha/antardasha context. LL.5 already computes dasha-transit axis-weight modulators at this level. Commit to antardasha as the primary time-slice; solar year as a secondary axis for transit-only signals.

**Decision D2 — Domain scope in v1.0: 4 domains**

The 4 domains with the richest LEL coverage and the strongest CDLM signal:
- `CAREER` — professional role changes, promotions, relocations, business events
- `HEALTH` — physical symptoms, procedures, recovery arcs
- `RELATIONSHIP` — marriage, partnerships, significant relationship events
- `SPIRITUAL_PSYCHOLOGICAL` — spiritual practice onset/deepening, psychological shifts, creative expression

**Rationale for exclusion:** Finance as a separate domain has insufficient LEL events at this stage (financial context is often embedded in career events). Education events are pre-1990 and too sparse in the training partition. These become v2.0 additions when LEL corpus grows.

**Decision D3 — Node types**

*Type A — Natal static nodes (exogenous, fixed throughout native's life):*
All 30 production MSR signals. These are structural chart properties that do not change with time. They are the "prior evidence" that conditions all domain activations from t=0. In the DBN, they appear as evidence nodes with observed values fixed from the chart.

*Type B — Dasha-state node (time-varying, categorical):*
At each time-slice t, a tuple `(mahadasha_lord, antardasha_lord)` — 81 possible states (9×9 planet combinations). This is observed (not hidden) because we know the Vimshottari sequence precisely from the native's birth date. Source: FORENSIC §5 (dasha sequence) + LL.5.

*Type C — Domain activation nodes (latent, time-varying, 3-state):*
One per domain: `CAREER_STATE(t)`, `HEALTH_STATE(t)`, `RELATIONSHIP_STATE(t)`, `SPIRITUAL_STATE(t)`. States: `{ELEVATED, NORMAL, SUPPRESSED}`. These are the hidden variables the DBN infers — they are NOT directly observed; only the occurrence of events (Type D) is observed.

*Type D — Event occurrence nodes (observed, binary):*
Per domain per time-slice: `CAREER_EVENT(t)`, `HEALTH_EVENT(t)`, `RELATIONSHIP_EVENT(t)`, `SPIRITUAL_EVENT(t)`. Value 1 if ≥1 LEL event in this domain falls in this time-slice; 0 otherwise. These are the observation model nodes.

**Decision D4 — Edge types**

*Static natal → domain activation (at every t):*
Each natal signal (Type A) has a directed edge to each domain it is relevant to, weighted by LL.1 production weight × CDLM domain-linkage strength. The edge is computed once and held constant across all t. High-weight signals (production_weight > 0.7) are "strong conditioning" edges; lower-weight signals are "weak conditioning." Read the CDLM to determine which signals are relevant to which domains.

*Dasha-state → domain activation (at each t):*
The dasha-state tuple (mahadasha+antardasha) conditions domain activation via LL.5 axis-weight modulation. Implement as: dasha_state(t) → [CAREER_STATE(t), HEALTH_STATE(t), RELATIONSHIP_STATE(t), SPIRITUAL_STATE(t)]. The conditional distribution is initialized from LL.5 dasha-transit weights + LL.4 domain priors.

*Domain persistence (temporal):*
Domain activation(t) → domain activation(t+1). A SUPPRESSED state tends to persist; an ELEVATED state decays toward NORMAL unless renewed by dasha/natal evidence. Express as a persistence probability matrix. Initial parameter: P(same_state_at_t+1 | state_at_t) = 0.65 across all states (calibrate in M5-D).

*Cross-domain edges (at same t):*
Sourced from CDLM domain-pair linkages and LL.2 promoted edges. For v1.0, use only HIGH-linkage CDLM pairs. Candidate edges (verify against CDLM read):
- CAREER(t) ↔ RELATIONSHIP(t) (Parivartana Saturn-Venus: strong career-relationship co-activation)
- CAREER(t) → SPIRITUAL(t) (professional transitions often coincide with spiritual deepening in this chart — verify in CDLM and LL.7 novel edges)
- HEALTH(t) ↔ SPIRITUAL(t) (health crises in the chart correlate with intensified spiritual practice)

**Decision D5 — Parameterization strategy (Hybrid-C)**

Per PHASE_M5_PLAN §0 declared tooling:
- CPTs (conditional probability tables) are **manually computed from LL outputs** — JSON format
- LLM (DeepSeek) performs **inference queries** against the fitted CPT structure
- LLM-assisted **signal selection** refines which natal signals condition which domains

In M5-B, produce the CPT *structure specification* (schema + placeholder values). Actual fitted values land in M5-D after DBN fitting on training data.

**Decision D6 — v1.0 scope boundary**

Explicitly out of scope for DBN_TOPOLOGY v1.0:
- Transit nodes beyond dasha-lord context (added in v2.0 if warranted)
- Finance, Education, Creative domains (insufficient LEL coverage in training partition)
- Navamsa (D9) or divisional chart signals (added post-M8 classical cross-reference)
- N-step ahead prediction horizon (added in M6 with forward predictions)

---

### 4.2 — Required artifact structure

Author `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` with exactly this section structure:

```markdown
---
artifact: DBN_TOPOLOGY_v1_0.md
canonical_id: DBN_TOPOLOGY
version: "1.0"
status: DRAFT              # DRAFT at this session; flipped to CLOSED at NAP.M5.1
phase: M5-B
sub_phase: M5-B-S1
authored_by: M5-B-S1
authored_at: 2026-05-13
nap_gate: NAP.M5.1         # topology is frozen after native approval
held_out_status: >
  Topology committed WITHOUT consulting held-out partition.
  Held-out partition IDs: [enumerate from partition declaration file].
  First consultation of held-out outcomes: M5-D fitting phase only.
predecessor_artifacts:
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll7_discovery_prior_v1_0.json
  - 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL5_DASHA_TRANSIT_DESIGN_v1_0.md
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL4_PREDICTION_PRIOR_v1_0.md
derivation_ledger:
  - claim: "Antardasha is the atomic time-slice"
    l1_source: "FORENSIC §5 — Vimshottari dasha sequence for native's birth date"
    ll_source: "LL5_DASHA_TRANSIT_DESIGN §2 — dasha period granularity rationale"
  - claim: "4 domains selected"
    l1_source: "LEL training partition domain distribution"
    ll_source: "LL4_PREDICTION_PRIOR §2 — domain prior coverage"
  # ... (add one derivation ledger entry per major design claim per B.3 mandate)
changelog:
  - v1.0 (2026-05-13, M5-B-S1): Initial committed topology. DRAFT pending NAP.M5.1.
---

# DBN TOPOLOGY — v1.0

## §1 — Purpose and scope

[One paragraph: what the DBN models, what it does NOT model in v1.0, and the philosophical stance
(topology must be committed before held-out data is seen — Learning Layer discipline #4).]

## §2 — Committed design decisions

[Reproduce decisions D1–D6 from §4.1 of this brief, in prose + structured form, with derivation
ledger entries for each. This is the pre-commitment record.]

## §3 — Node inventory

### §3.1 — Type A nodes: Natal static signals (exogenous)

[Table: every one of the 30 production MSR signals. Columns: Signal_ID | Signal_name | LL.1_production_weight | Domains_conditioned | Conditioning_strength (HIGH / MED / LOW based on weight + CDLM linkage)]

Derive conditioning strength as follows:
  HIGH = production_weight ≥ 0.7 AND CDLM msr_anchor present in ≥1 relevant domain cell
  MED  = production_weight ≥ 0.4 OR CDLM msr_anchor present
  LOW  = production_weight < 0.4 AND no CDLM anchor (natal chart presence only)

### §3.2 — Type B node: Dasha-state (time-varying, observed)

[Define the (mahadasha_lord, antardasha_lord) tuple encoding. List the 9×9 = 81 possible states.
Map each dasha-lord to its natural domain associations from classical Jyotish + LL.5 weights.
Example: (Saturn-MD, Mercury-AD) → tends to elevate CAREER, suppress RELATIONSHIP per LL.5.]

Native's dasha sequence (from FORENSIC §5): enumerate the sequence of antardasha periods
from 1984-02-05 forward, identifying which antardasha falls within each training LEL event.
This is the time-slice index for the training data. Use actual dates from FORENSIC; mark
any antardasha period that falls entirely in the held-out window as BLINDED.

### §3.3 — Type C nodes: Domain activation (latent, time-varying)

[One row per domain. For each: state space {ELEVATED, NORMAL, SUPPRESSED}, base prior
from LL.4 domain priors, persistence probability initial value per D4.]

| Domain | State space | Base prior | Persistence_init | Primary conditioning signals (top 3 from §3.1) |
|---|---|---|---|---|
| CAREER | {E, N, S} | [from LL.4] | 0.65 | [...] |
| HEALTH | {E, N, S} | [from LL.4] | 0.65 | [...] |
| RELATIONSHIP | {E, N, S} | [from LL.4] | 0.65 | [...] |
| SPIRITUAL_PSYCHOLOGICAL | {E, N, S} | [from LL.4] | 0.65 | [...] |

### §3.4 — Type D nodes: Event occurrence (observed, binary)

[One row per domain: binary Y/N for ≥1 LEL event in domain in antardasha time-slice.
State space: {EVENT, NO_EVENT}. Conditional on Type C domain activation.]

Observation model (initial, to be fitted in M5-D):
  P(EVENT=1 | domain_state=ELEVATED)  = 0.70
  P(EVENT=1 | domain_state=NORMAL)    = 0.20
  P(EVENT=1 | domain_state=SUPPRESSED) = 0.05

These are initial values from LL.4 priors + calibration rubric. Fitted values replace them in M5-D.

## §4 — Edge inventory

### §4.1 — Natal → domain edges (Type A → Type C)

[Table: Signal_ID | Domain | Edge_weight | Source (LL.1 weight + CDLM) | Conditioning_direction]

Rule for edge weight computation:
  edge_weight = LL.1_production_weight × CDLM_linkage_strength_score
  where CDLM_linkage_strength_score: HIGH=1.0, MED=0.6, LOW=0.2, ABSENT=0.0

Only include edges where edge_weight > 0.0. Signals with no CDLM linkage to any domain
still get a LOW score in the domain most classically associated with their house placement
(per FORENSIC §2).

### §4.2 — Dasha-state → domain edges (Type B → Type C)

[Table: Mahadasha_lord | Domain | Directionality | LL.5_basis | Classical basis]

Map each of the 9 mahadasha lords to their domain tendency:
- Sun MD: CAREER elevation; SPIRITUAL neutral; HEALTH neutral; RELATIONSHIP suppression tendency
- Moon MD: HEALTH prominent; RELATIONSHIP prominent; SPIRITUAL variable
- Mars MD: CAREER active; HEALTH risk; RELATIONSHIP conflict-prone
- Mercury MD: CAREER (communication/writing); SPIRITUAL (study); HEALTH neutral
- Jupiter MD: SPIRITUAL elevation; CAREER expansion; RELATIONSHIP growth
- Venus MD: RELATIONSHIP prominent; SPIRITUAL_PSYCHOLOGICAL (art/aesthetics); CAREER (wealth aspects)
- Saturn MD: CAREER restructuring; HEALTH chronic patterns; RELATIONSHIP contraction then stability
- Rahu MD: CAREER disruption/leap; SPIRITUAL unsettled; HEALTH unusual conditions
- Ketu MD: SPIRITUAL deepening; CAREER dissolution/withdrawal; HEALTH subtle

Encode antardasha modulation as a multiplier on the mahadasha tendency (from LL.5 axis-weight data).

### §4.3 — Domain persistence edges (Type C(t) → Type C(t+1))

[3×3 persistence matrix per domain — initial values from D4. Same structure across all 4 domains in v1.0.]

Persistence matrix (symmetric initial; to be fitted in M5-D):
  ELEVATED(t) → ELEVATED(t+1): 0.55
  ELEVATED(t) → NORMAL(t+1):   0.35
  ELEVATED(t) → SUPPRESSED(t+1): 0.10
  NORMAL(t)   → NORMAL(t+1):   0.65
  NORMAL(t)   → ELEVATED(t+1): 0.20
  NORMAL(t)   → SUPPRESSED(t+1): 0.15
  SUPPRESSED(t) → SUPPRESSED(t+1): 0.60
  SUPPRESSED(t) → NORMAL(t+1): 0.35
  SUPPRESSED(t) → ELEVATED(t+1): 0.05

### §4.4 — Cross-domain edges (Type C(t) ↔ Type C(t))

[For each cross-domain pair: CDLM basis | LL.2/LL.7 supporting edges | Directionality | Initial weight]

Cross-domain edges for v1.0 (verify each against CDLM read):
1. CAREER(t) ↔ RELATIONSHIP(t): bidirectional, weight=0.35
   Basis: SIG.MSR.145 Parivartana Saturn-10L/Venus-7L (CDLM career-relationship cell; LL.2 EDGE-01/02/04)
2. CAREER(t) ↔ SPIRITUAL(t): bidirectional, weight=0.20
   Basis: LL.7 novel edges in career-spiritual cluster; verify CDLM career-spiritual cell anchor
3. HEALTH(t) ↔ SPIRITUAL(t): bidirectional, weight=0.25
   Basis: PSY.A (vertigo/debilitation coincides with spiritual seeking); verify CDLM cell

[If CDLM read reveals additional HIGH-linkage pairs, include them. Do not fabricate CDLM claims —
mark any edge as [CDLM_VERIFICATION_REQUIRED] if the CDLM cell does not explicitly support it.]

## §5 — CPT structure specification (Hybrid-C scaffold)

[This section specifies the JSON schema for the CPT files. Actual numerical values are fitted in M5-D.
The structure must be complete so that M5-D fitting has a target format to fill.]

### CPT file paths declared:
- `06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json`  — Type A → C edges (one row per signal-domain pair)
- `06_LEARNING_LAYER/dbn/cpt/dasha_to_domain.json`   — Type B → C (81×4 conditional distribution table)
- `06_LEARNING_LAYER/dbn/cpt/persistence.json`        — Type C(t)→C(t+1) (3×3 per domain)
- `06_LEARNING_LAYER/dbn/cpt/cross_domain.json`       — Type C↔C inter-domain edges
- `06_LEARNING_LAYER/dbn/cpt/observation.json`        — Type C → D observation model

### JSON schema per CPT file:
```json
{
  "cpt_id": "natal_to_domain",
  "version": "scaffold_M5-B-S1",
  "status": "UNFITTED_SCAFFOLD",
  "fit_session": null,
  "entries": [
    {
      "signal_id": "SIG.MSR.XXX",
      "domain": "CAREER",
      "edge_weight": 0.0,
      "initial_value": 0.0,
      "fitted_value": null,
      "derivation": "ll1_weight * cdlm_strength"
    }
  ]
}
```

**Create the scaffold CPT files** (with initial values from §4.1–§4.4, `fitted_value: null`) as part of this session's output. These are the targets that M5-D filling will populate.

## §6 — LL.2 integration status

### §6.1 — Promoted edges included in topology

[State which of the 8 LL.2 campaign edges from `ll2_promotion_campaign_v1_0.md` are incorporated
as cross-domain edges or natal→domain edges in the topology. Note: at session open, these edges
are PENDING_NATIVE_APPROVAL. Record them as `pending_promotion: true` — they are in the topology
design but marked pending; they become confirmed after native approves the campaign.]

### §6.2 — Conditional nodes (MSR.117)

SIG.MSR.117 (Hamsa Near-Miss — `shadow_indefinite_low_match_rate`) is included as a **shadow node**
in the topology: it conditions domain activation at a reduced weight (LOW tier) and is not promoted
as a primary edge until its match-rate stabilizes. EDGE-06 and EDGE-07 in the LL.2 campaign depend
on this shadow status.

## §7 — Risk register entry (per PHASE_M5_PLAN §4)

Document in this section the per-topology risk entries:

| Risk ID | Risk | Mitigation in this topology | Severity |
|---|---|---|---|
| R.M5.4 | Topology overfit to LEL history | Held-out partition sacrosanct; decisions D1–D6 committed before seeing outcomes | HIGH |
| R.M5.2 | DBN under-identification at n=1 | Shadow mode; v2.0 plan; conservative initial CPT values; n=1 caveat on all outputs | HIGH |
| R.M5.3 | Learned-vs-classical divergence | Persistence matrix initialized conservatively; any posterior contradicting classical rules by >0.3 triggers DISAGREEMENT_REGISTER entry | MED |
| RT.M5B.1 | Domain scope too narrow (misses finance/education) | V2.0 extension plan declared; M5-D validation will expose domain gaps | MED |

## §8 — Gemini two-pass topology review (surrogate pass)

Per MACRO_PLAN §M5 agent roles: "Gemini on topology proposals + prior elicitation." Gemini is
FINAL_NOT_REACHABLE (R.LL1TPA.1). Execute the surrogate pass per the established protocol:

**Surrogate review criteria (Claude, acting as Gemini surrogate, independently reviews):**
1. Is the time-slice unit (antardasha) defensible? Are there stronger alternatives? (Note any.)
2. Are the 4 domains the right 4? What is lost by excluding Finance and Education?
3. Are the node types complete? Is there a missing latent variable?
4. Are the cross-domain edges motivated or fabricated? Check each against CDLM explicitly.
5. Are the initial CPT values reasonable priors or are they implicitly fitted to training data?
6. Is the held-out sacrosanct rule verifiably enforced? Can the topology design be reproduced without the held-out outcomes?

Document the surrogate review output in this section with format:
```
SURROGATE_REVIEWER: Claude (acting for Gemini per R.LL1TPA.1 FINAL_NOT_REACHABLE protocol)
REVIEW_DATE: 2026-05-13
REVIEW_FINDINGS:
  - [finding 1]
  - [finding 2]
  - ...
CLAUDE_RESPONSE:
  - [response to finding 1]
  - ...
UNRESOLVED (native adjudication required):
  - [any finding Claude cannot resolve unilaterally]
SURROGATE_DISCLOSURE: This review substitutes for Gemini Pass 1 per LL1_TWO_PASS_APPROVAL_v1_0.md
  §5 surrogate protocol. Outcome subject to retroactive Gemini ratification if Gemini becomes
  reachable in M5. Added to surrogate disclosure ledger at session close.
```

## §9 — Version and changelog

[Frontmatter changelog block — v1.0 entry only at this session.]

---

*End of DBN_TOPOLOGY_v1_0.md section specification.*
```

---

## §5 — LL.2 per-edge campaign: resolve or carry

The campaign document at `06_LEARNING_LAYER/dbn/ll2_promotion_campaign_v1_0.md` is `PENDING_NATIVE_APPROVAL`. In M5-B-S1, two outcomes are possible:

**Outcome A — Native approves during this session** (via Cowork message or in-session instruction):
- Update `ll2_edge_weights_v1_0.json`: for each approved edge, set `promotion_eligible: true`
  and append to `approval_chain`: `{pass_2_reviewer: "native", pass_2_nap_id: "NAP.M5.EDGE-BATCH",
  pass_2_status: "approved", pass_2_date: "2026-05-13", pass_2_session: "M5-B-S1"}`
- Update `ll2_promotion_campaign_v1_0.md` status: `APPROVED → CLOSED`
- Update `DBN_TOPOLOGY_v1_0.md §6.1`: change `pending_promotion: true` → `promotion_approved: true`
  for approved edges
- Mark AC.M5B.4 PASS in the session-close block

**Outcome B — Native approval deferred** (no instruction received):
- Leave campaign document as-is (PENDING_NATIVE_APPROVAL)
- Leave topology §6.1 entries as `pending_promotion: true`
- Note in session-close: "LL.2 promotion deferred — awaiting native instruction;
  AC.M5B.4 NOT YET DISCHARGEABLE; propose approval at next Cowork session"

Do NOT advance to Outcome A unless explicit native instruction is received in this session.

---

## §6 — Scaffold CPT files (create alongside topology)

Create the directory structure and scaffold CPT files:

```bash
mkdir -p 06_LEARNING_LAYER/dbn/cpt
```

Create 5 JSON files under `06_LEARNING_LAYER/dbn/cpt/`:

### `cpt/natal_to_domain.json`
One entry per (signal_id, domain) pair where edge_weight > 0. Use the signal table from §3.2
pre-flight check and the CDLM read. Populate `initial_value` from LL.1 weight × CDLM strength.
Leave `fitted_value: null`.

### `cpt/dasha_to_domain.json`
81 rows (9 mahadasha × 9 antardasha lords). For each, a 4-domain conditional distribution:
{CAREER_tendency, HEALTH_tendency, RELATIONSHIP_tendency, SPIRITUAL_tendency} where each
value is an initial probability drawn from LL.5 weights and classical Jyotish domain association
(Decision D4, §4.2 of this brief). The three values per domain must sum to 1.0 across {ELEVATED, NORMAL, SUPPRESSED}.
Leave the full table as initializing priors.

### `cpt/persistence.json`
4 domains × 3×3 transition matrix. Initial values from §4.3. Leave `fitted_values: null`.

### `cpt/cross_domain.json`
One row per cross-domain edge. Fields: domain_a, domain_b, direction (bidirectional/a_to_b/b_to_a),
initial_weight, cdlm_basis, ll2_edges_supporting, pending_promotion.

### `cpt/observation.json`
4 rows (one per domain). Per-row: `P_event_given_ELEVATED`, `P_event_given_NORMAL`,
`P_event_given_SUPPRESSED` — initial values from §3.4, `fitted_values: null`.

---

## §7 — Register new artifacts in CAPABILITY_MANIFEST.json

After creating the topology and CPT scaffolds, register them:

```bash
python3 - << 'EOF'
import json, hashlib, datetime

manifest_path = '00_ARCHITECTURE/CAPABILITY_MANIFEST.json'
with open(manifest_path) as f:
    manifest = json.load(f)

# Read current version
current_version = manifest.get('manifest_version', '2.5')
# Increment minor version
parts = str(current_version).split('.')
new_version = f"{parts[0]}.{int(parts[1]) + 1}"

new_entries = [
    {
        "canonical_id": "DBN_TOPOLOGY",
        "path": "06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md",
        "version": "1.0",
        "status": "DRAFT",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    },
    {
        "canonical_id": "DBN_CPT_NATAL_TO_DOMAIN",
        "path": "06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json",
        "version": "scaffold_M5-B-S1",
        "status": "UNFITTED_SCAFFOLD",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    },
    {
        "canonical_id": "DBN_CPT_DASHA_TO_DOMAIN",
        "path": "06_LEARNING_LAYER/dbn/cpt/dasha_to_domain.json",
        "version": "scaffold_M5-B-S1",
        "status": "UNFITTED_SCAFFOLD",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    },
    {
        "canonical_id": "DBN_CPT_PERSISTENCE",
        "path": "06_LEARNING_LAYER/dbn/cpt/persistence.json",
        "version": "scaffold_M5-B-S1",
        "status": "UNFITTED_SCAFFOLD",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    },
    {
        "canonical_id": "DBN_CPT_CROSS_DOMAIN",
        "path": "06_LEARNING_LAYER/dbn/cpt/cross_domain.json",
        "version": "scaffold_M5-B-S1",
        "status": "UNFITTED_SCAFFOLD",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    },
    {
        "canonical_id": "DBN_CPT_OBSERVATION",
        "path": "06_LEARNING_LAYER/dbn/cpt/observation.json",
        "version": "scaffold_M5-B-S1",
        "status": "UNFITTED_SCAFFOLD",
        "phase": "M5-B",
        "created_session": "M5-B-S1",
        "created_at": "2026-05-13"
    }
]

# Add entries (check for duplicates by canonical_id)
existing_ids = {e.get('canonical_id') for e in manifest.get('entries', [])}
for entry in new_entries:
    if entry['canonical_id'] not in existing_ids:
        manifest.setdefault('entries', []).append(entry)
        print(f"  Added: {entry['canonical_id']}")
    else:
        print(f"  Already exists: {entry['canonical_id']} — update manually if version changed")

manifest['manifest_version'] = new_version
manifest['last_updated'] = '2026-05-13'
manifest['last_updated_session'] = 'M5-B-S1'
manifest['entry_count'] = len(manifest.get('entries', []))

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"\nManifest updated: v{current_version} → v{new_version}")
print(f"Entry count: {manifest['entry_count']}")
EOF
```

Verify the manifest is valid JSON after writing:
```bash
python3 -c "import json; json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')); print('JSON_OK')"
```

---

## §8 — Session-close obligations

Execute these **in order** at session close:

### 8.1 — Validate all deliverables present
```bash
echo "--- AC checklist ---"
test -f 06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md && echo "AC.M5B.1 PARTIAL (DRAFT authored)" || echo "AC.M5B.1 FAIL — topology missing"
test -f 06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json && echo "CPT NATAL: present" || echo "CPT NATAL: MISSING"
test -f 06_LEARNING_LAYER/dbn/cpt/dasha_to_domain.json && echo "CPT DASHA: present" || echo "CPT DASHA: MISSING"
test -f 06_LEARNING_LAYER/dbn/cpt/persistence.json && echo "CPT PERSIST: present" || echo "CPT PERSIST: MISSING"
test -f 06_LEARNING_LAYER/dbn/cpt/cross_domain.json && echo "CPT CROSS: present" || echo "CPT CROSS: MISSING"
test -f 06_LEARNING_LAYER/dbn/cpt/observation.json && echo "CPT OBS: present" || echo "CPT OBS: MISSING"
python3 -c "import json; json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')); print('MANIFEST: JSON_OK')"
grep -l "DBN_TOPOLOGY" 00_ARCHITECTURE/CAPABILITY_MANIFEST.json && echo "MANIFEST ENTRY: present" || echo "MANIFEST ENTRY: MISSING"
```

### 8.2 — Update CURRENT_STATE v4.0 → v4.1

Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`:
- Frontmatter: `version: 4.1`
- Add changelog entry for this session (v4.0 → v4.1):
  - Session M5-B-S1 opened M5-B. DBN_TOPOLOGY_v1_0.md drafted (DRAFT status; NAP.M5.1 pending). Scaffold CPTs created. LL.2 campaign: [APPROVED/DEFERRED per outcome A/B]. Gemini two-pass: surrogate pass executed; Gemini FINAL_NOT_REACHABLE_M5 status confirmed. Manifest updated to v[new].
- Update `active_phase_plan_sub_phase`: augment with "M5-B OPEN — DBN_TOPOLOGY_v1_0.md DRAFT authored at M5-B-S1."
- Update `file_updated_at`: 2026-05-13
- Update `file_updated_by_session`: M5-B-S1
- DO NOT change `active_macro_phase` or `active_phase_plan` — those are correct.

### 8.3 — Mirror update (MP.1 + MP.2)

If any governance-level information changed (CURRENT_STATE sub-phase pointer, session count):

Update `.geminirules` (MP.1) — adapted parity: update the active sub-phase line to read
"M5-B OPEN — DBN Topology Design — M5-B-S1 opened 2026-05-13."

Update `.gemini/project_state.md` (MP.2) — adapted parity: update the state block to reflect
M5-B open, DBN_TOPOLOGY DRAFT, LL.2 campaign status, surrogate review completed.

### 8.4 — Emit session-close block and append to SESSION_LOG

```yaml
session_close:
  session_id: M5-B-S1
  status: CLOSED
  closed_at: "<ISO timestamp>"
  deliverables_produced:
    - path: 06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md
      status: DRAFT
      note: "NAP.M5.1 pending — topology frozen when approved"
    - path: 06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json
      status: UNFITTED_SCAFFOLD
    - path: 06_LEARNING_LAYER/dbn/cpt/dasha_to_domain.json
      status: UNFITTED_SCAFFOLD
    - path: 06_LEARNING_LAYER/dbn/cpt/persistence.json
      status: UNFITTED_SCAFFOLD
    - path: 06_LEARNING_LAYER/dbn/cpt/cross_domain.json
      status: UNFITTED_SCAFFOLD
    - path: 06_LEARNING_LAYER/dbn/cpt/observation.json
      status: UNFITTED_SCAFFOLD
  ac_status:
    AC.M5B.1: "PARTIAL — DBN_TOPOLOGY_v1_0.md DRAFT; CLOSED at NAP.M5.1"
    AC.M5B.2: "PARTIAL — Gemini surrogate pass executed; native adjudication items noted in §8"
    AC.M5B.3: "DEFERRED — LL.3 retrieval-domain alignment to M5-B-S2"
    AC.M5B.4: "[APPROVED / DEFERRED — fill per Outcome A or B]"
    AC.M5B.5: "NOT YET — awaiting NAP.M5.1"
    AC.M5B.6: "PASS — Risk register §7 in DBN_TOPOLOGY"
    AC.M5B.7: "DEFERRED — AC.IV.6 after LL.3 fixes"
  ll2_campaign_status: "[APPROVED / DEFERRED]"
  gemini_two_pass_status: "SURROGATE_EXECUTED (Gemini FINAL_NOT_REACHABLE_M5)"
  surrogate_disclosure_ledger_updated: true   # add entry to surrogate ledger in LL1_TWO_PASS_APPROVAL
  current_state_updated: true
  mirror_updates_propagated:
    - pair_id: MP.1
      updated: true
      update_summary: "Active sub-phase pointer → M5-B OPEN"
    - pair_id: MP.2
      updated: true
      update_summary: "project_state.md reflects M5-B open, DBN_TOPOLOGY DRAFT"
  red_team_counter: 2
    # Was 1 at M5-A-S1 close. Increments to 2. IS.8(a) fires at 3 (next regular session).
  scope_violations: none
  notes: >
    M5-B-S1 close. Primary deliverable DBN_TOPOLOGY_v1_0.md is DRAFT — topology is
    committed but not native-approved. NAP.M5.1 is the freeze gate. Surrogate two-pass
    conducted; findings documented in §8 of topology. LL.2 per-edge campaign: [resolution].
    AC.M5B.3 (LL.3 retrieval alignment) deferred to M5-B-S2 per declared scope.
```

Append the full session entry (session_open block + work summary + session_close block)
to `00_ARCHITECTURE/SESSION_LOG.md` atomically as a single new entry.

### 8.5 — Commit

```bash
git add \
  06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md \
  06_LEARNING_LAYER/dbn/cpt/ \
  06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json \
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json \
  00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
  00_ARCHITECTURE/SESSION_LOG.md \
  .geminirules \
  .gemini/project_state.md \
  CLAUDECODE_BRIEF.md   # flip status: COMPLETE

git commit -m "feat(M5-B-S1): DBN topology v1.0 DRAFT + CPT scaffolds + LL.2 campaign [resolution]

DBN_TOPOLOGY_v1_0.md: time-slice=antardasha; 4 domains (CAREER/HEALTH/RELATIONSHIP/SPIRITUAL);
30 natal static nodes + dasha-state node + 4 latent domain-activation nodes + 4 event nodes.
CPT scaffolds created (5 files) — unfitted; M5-D fitting targets.
LL.2 per-edge campaign: [APPROVED 8 edges / DEFERRED pending native].
Gemini two-pass: surrogate pass executed (FINAL_NOT_REACHABLE_M5).
CAPABILITY_MANIFEST: v[old] → v[new] (+6 entries).
CURRENT_STATE: v4.0 → v4.1 (M5-B OPEN).
AC.M5B.1 PARTIAL, AC.M5B.4 [PASS/DEFERRED], AC.M5B.6 PASS."
```

### 8.6 — Flip this brief to COMPLETE

Edit this file's frontmatter: `status: COMPLETE`

---

## §9 — Acceptance criteria for M5-B-S1 close

| AC | Description | Gate |
|---|---|---|
| AC.S1.1 | `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` exists with frontmatter `status: DRAFT` and all 9 sections (§1–§9) populated | Hard |
| AC.S1.2 | Topology commits to D1–D6 in writing BEFORE any held-out event outcome is mentioned | Hard (sacrosanct) |
| AC.S1.3 | All 5 CPT scaffold files exist under `06_LEARNING_LAYER/dbn/cpt/` with valid JSON | Hard |
| AC.S1.4 | Every signal in ll1_weights_promoted_v1_0.json is assigned a node type (A/B/C/D) in §3.1 | Hard |
| AC.S1.5 | Surrogate two-pass review documented in DBN_TOPOLOGY §8 with surrogate_disclosure block | Hard |
| AC.S1.6 | CAPABILITY_MANIFEST.json is valid JSON after update; entry_count incremented | Hard |
| AC.S1.7 | CURRENT_STATE v4.1 written; M5-B sub-phase status updated | Hard |
| AC.S1.8 | SESSION_LOG.md has complete M5-B-S1 entry (open + body + close) | Hard |
| AC.S1.9 | Single clean git commit with specified message format | Hard |
| AC.S1.10 | CLAUDECODE_BRIEF.md `status: COMPLETE` | Hard |
| AC.S1.11 | LL.2 campaign outcome (A or B) documented in topology §6.1 and session-close block | Soft |

---

## §10 — Hard constraints

1. **Held-out sacrosanct (absolute).** Do not read or reference held-out event *outcomes* during topology authoring. You may use event IDs to confirm blinding. If you accidentally see a held-out outcome, note it in the session log and the topology's `held_out_status` frontmatter field, and flag it for native review.

2. **No Claude/Anthropic API.** LLM stack = Gemini → DeepSeek → NIM. If any inference is needed to check topology reasoning, use DeepSeek (deepseek-v4-pro or equivalent).

3. **No L1/L2.5 writes.** `01_FACTS_LAYER/` and `025_HOLISTIC_SYNTHESIS/` are read-only this session.

4. **No production weight changes.** `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/` is frozen. Do not edit the production JSON.

5. **B.10 compliance.** If any value in the topology requires a chart computation not already present in FORENSIC (e.g., exact antardasha dates not listed), mark it `[EXTERNAL_COMPUTATION_REQUIRED: compute via Swiss Ephemeris: {spec}]` — do not invent values.

6. **B.3 derivation ledger.** Every claim in DBN_TOPOLOGY_v1_0.md must have a derivation ledger entry citing the specific L1 fact ID or LL file it derives from. Claims without citations fail B.3.

7. **Commit topology before reviewing it against held-out data.** The commit timestamp is the pre-registration seal. M5-D fitting (which may consult held-out data) is a future session.

---

## §11 — Scope boundary reference

### may_touch
```
06_LEARNING_LAYER/dbn/**
06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json
00_ARCHITECTURE/CAPABILITY_MANIFEST.json
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
.geminirules
.gemini/project_state.md
CLAUDECODE_BRIEF.md                    ← flip to COMPLETE only
```

### must_not_touch
```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/**
platform/src/**
platform/lib/**
00_ARCHITECTURE/MACRO_PLAN_v2_0.md
00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md      ← read-only; don't amend mid-session
```

---

## §12 — What this session does NOT need to do

The following are M5-B scope but deferred to M5-B-S2 or later:
- LL.3 retrieval-domain alignment (R.LL3.1/.2/.3) — requires platform/lib/ edits; separate session
- AC.IV.6 golden-set eval re-run — after LL.3 fixes land
- NAP.M5.1 formal topology approval — issued by native at next Cowork session after topology review
- Full Gemini two-pass (second agent) — FINAL_NOT_REACHABLE; surrogate only this session

---

*End of CLAUDECODE_BRIEF — M5-B-S1*
*Authored: 2026-05-13 by Claude Sonnet 4.6 (Cowork session: Madhav M5-B-S1 — DBN Topology Design)*
*Execute in marsys-m5-dbn worktree on feature/m5-probabilistic-model.*
