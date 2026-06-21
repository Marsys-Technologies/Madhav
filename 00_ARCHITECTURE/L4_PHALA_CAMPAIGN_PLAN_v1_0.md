---
artifact: L4_PHALA_CAMPAIGN_PLAN_v1_0.md
canonical_id: L4_PHALA_CAMPAIGN_PLAN
version: 1.0
status: DRAFT — governing design for the L4 Phala build; parent of the per-asset briefs
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
parent_audit: 00_ARCHITECTURE/L4_PHALA_AUDIT_v1_0.md
inherits_from: 00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md (§9 ratified params, §11 onboarding contract)
role: >
  The master design for L4 Phala — the applied / delivered-prediction layer. Settles the
  6-asset set + DAG, the L4/L5 boundary, per-asset scope, the ratified-param inheritance,
  the anti-drift discipline, and the build/seal method. The per-asset CLAUDECODE briefs
  implement this; the Conductor session_queue sequences it.
native_ratify_gates:
  - "G-RECT: ph_sodhana computes the ascendant via PyJHora compute_ascendant (vs. external-stub). RECOMMENDED — see §6.3."
  - "G-LADDER: the anchor calibration ladder as a deterministic transform over ka_sangam I-16 score (vs. legacy hand-assign). RECOMMENDED — see §6.1."
---

# L4 Phala — Campaign Plan v1.0

## §1 — What L4 Phala IS (the fruit)

L4 **Phala** (Sanskrit "fruit / result"; asset prefix `ph_*`, table prefix `phala_*`) is the
**applied / delivered-prediction layer**. Where L3 Kāla computed *when* the chart's structural
promise activates (scored convergence windows, danger windows, life-arc chapters), L4 turns those
windows into **delivered products for the native**:

1. **Predictive anchors** — phase-locked, falsifiable predictions per convergence window.
2. **Auspicious-window selection** — muhūrta picks for the native's actual decisions.
3. **Mitigation** — the window→intervention loop: for each flagged malefic period, an active remedy.
4. **Birth-time rectification** — a real, computed Aries/Taurus determination scored against life events.
5. **The delivered dossier** — a whole-chart-read composite the native actually reads.

L4 is the layer where the instrument stops being a substrate and becomes an **answer**.

**Boundary (inherited, non-negotiable):** L4 owns the *applied fruit*. The **prediction-record +
calibration + falsification** machinery is **L5 Mīmāṃsā** (`mi_bhavisya`, `mi_pramana`);
`ka_bhavishya_lekha` already hands prediction-records UP to L5. L4 does **not** re-own calibration —
it emits falsifiable products; L5 scores them against the Life-Event Log. See §5.

## §2 — Position in the arc (what L4 sits on)

| Layer | Name | Status | L4's relationship |
|---|---|---|---|
| L1 | Gaṇita | ✓ SEALED | read `chart_facts`, `ga_panchanga` (read-only) |
| L2 | Bodha | ✓ SEALED | read `bodha_msr_signals`, `bo_laksana`, `bo_upaya` (read-only) |
| L3 | Kāla | ✓ SEALED | read `kala_convergence` (ka_sangam), `kala_obstruction` (ka_vighnakara), `kala_activation` (ka_kalasutra); call services `ka_muhurta_seva`, `ka_tulana` (read-only) |
| **L4** | **Phala** | **→ THIS BUILD** | writes ONLY `phala_*` |
| L5 | Mīmāṃsā | pending | consumes L4's falsifiable products; owns calibration |

## §3 — The non-negotiable disciplines (inherited)

- **B.1 Facts/Interpretation separation.** L4 = applied prediction. Never collapse a layer.
- **Anti-drift / L3-is-authority (§N.5).** An L4 row NEVER restates a lower layer's computed value
  as its own truth — it **references the lower `convergence_id` / `signal_id` / `fact_id`** and
  inherits the value. A derivation that disagrees with the fact it cites is a halt-worthy bug. **L4
  writes nothing to `kala_*` / `bodha_*` / `ganita_*` / `mimamsa_*`.** (Grep gate: zero non-phala writes.)
- **B.10 No fabricated computation.** Every number is either inherited from a lower layer or computed
  by the sealed engine (PyJHora / the L3 services). No hand-assigned magic numbers. (Resolves CORRECTION 3.)
- **B.11 Whole-Chart-Read.** `ph_phaladesa` enforces it structurally (composes all L4 sub-assets).
- **Frozen orchestrator contract.** `@register('ph_*')` `WriterBase`; `run(ctx)`; never commit
  `ctx.db_conn`; never write `asset_throughput`; delete-then-insert idempotency. (See AUDIT §2.)
- **Ratified params inherited UNCHANGED** (L3_KALA_CLOSE §9): I-16 convergence formula, I-17
  orb-strength curve, I-7 supporting weights, I-8 Mode-B threshold, confidence labels
  (high≥0.75 / moderate≥0.45 / speculative<0.45). **Do NOT re-pick** — any impulse = STUB+log, not a halt.

## §4 — The asset set (6 assets — 5 registered + 1 new composite)

```
                         ┌─────────────────────────────────────────────┐
   L3 (read-only)        │                  L4 PHALA                    │
                         │                                             │
  ka_sangam ───────────► │  ph_nimitta   (Predictive anchors)          │
  (kala_convergence)     │      │                                       │
                         │      ▼                                       │
  ka_kalasutra ────────► │  ph_muhurta   (Auspicious windows)          │
  ga_panchanga ────────► │      │                                       │
  ka_muhurta_seva(svc)   │      │                                       │
                         │      ▼                                       │
  bo_upaya ────────────► │  ph_pratikara (Mitigation: window→remedy)   │
  ka_vighnakara ───────► │      │                                       │
  (kala_obstruction)     │      │                                       │
                         │      ▼                                       │
  bo_laksana ──────────► │  ph_sodhana   (Rectification, PyJHora-computed)
  + LEL + PyJHora        │      │                                       │
                         │      ▼                                       │
                         │  ph_suddha_sodhana (Best rectification)      │
                         │      │                                       │
                         │      ▼                                       │
                         │  ph_phaladesa (NEW — composite dossier, B.11)│  ← reads all ph_* above
                         └─────────────────────────────────────────────┘
                                          │
                                          ▼  (falsifiable products only)
                                   L5 Mīmāṃsā (calibration)
```

### 4.1 — `ph_nimitta` — Nimitta — Predictive anchors  → `phala_anchors`
Derives phase-locked, falsifiable predictive anchors from `ka_sangam`'s real convergence windows.
Each anchor = (convergence window → human-readable event prediction + direction + domain +
explicit falsifier + calibrated confidence). **Confidence is a deterministic transform of the
window's I-16 `convergence_score` + independent-current count** (the harvested ladder, §6.1), NOT
hand-assigned. Cites the real `convergence_id` + `signal_id`. **depends_on: `ka_sangam`.**

### 4.2 — `ph_muhurta` — Muhūrta — Auspicious windows  → `phala_muhurta`
For a set of native action-classes (start_business, travel, signing, medical, ceremony, etc.),
scores candidate muhūrta windows by composing `ga_panchanga` (tithi/vara/nakshatra/yoga/karana) +
`ka_muhurta_seva` (Tāra Bala native overlay, 8 event classes) + `ka_kalasutra` activation overlap,
avoiding `ka_vighnakara` danger windows. Real panchanga values (NOT the legacy approximate
arithmetic). **depends_on: `ka_kalasutra`, `ga_panchanga`** (+ calls `ka_muhurta_seva`).

### 4.3 — `ph_pratikara` — Pratīkāra — Mitigation  → `phala_mitigation`
The **window→intervention loop**: for each active/upcoming `ka_vighnakara` obstruction window, binds
the matching `bo_upaya` remediation (mantra/charity/gemstone/behavioral, with BPHS chapter/verse
citation) to a *timed* intervention schedule. Output = "this obstruction, this window, this remedy,
start by this date." **depends_on: `bo_upaya`, `ka_vighnakara`.**

### 4.4 — `ph_sodhana` — Śodhana — Rectification  → `phala_rectification`
Birth-time rectification. **Computes** (via PyJHora `compute_ascendant`, §6.3) the ascendant degree
at each candidate time in the 10:13–11:13 IST grid → the real Aries→Taurus cusp crossing for
1984-02-05 Bhubaneswar → scores each candidate against the **training set** of life events (derived
from LEL + `bo_laksana`, pre-2020 only). Preserves the **leakage discipline** (post-2020 +
late-disclosed events are sacrosanct holdout). One row per candidate hypothesis with its score +
marker analysis. **depends_on: `bo_laksana`** (+ LEL + PyJHora adapter).

### 4.5 — `ph_suddha_sodhana` — Śuddha-śodhana — Best rectification  → `phala_rectification_best`
The top-scored rectification hypothesis per search run (accumulates across runs). Selects the
argmax over `ph_sodhana` rows + holds the verification-protocol state (which holdout events have
since occurred and how they scored). **depends_on: `ph_sodhana`.**

### 4.6 — `ph_phaladesa` — Phaladeśa — Delivered outlook dossier  → `phala_outlook`  **[NEW]**
> *Phaladeśa* — "the declaration of the fruit." The composite the native reads.

Composes, for a requested horizon, the active `ph_nimitta` anchors + the relevant `ph_muhurta`
picks + the active `ph_pratikara` mitigations + the current rectification posture into ONE
horizon-scoped, **whole-chart-read (B.11)** prediction dossier with a single readiness/headline
read and a structured narrative. This is the legacy `phala.outlook` pattern, rebuilt as a stored
artifact. **depends_on: `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `ph_suddha_sodhana`** (+ calls
`ka_tulana` for cross-pattern prioritization). Native-added this session; registers in the seed.

## §5 — The L4 / L5 boundary (explicit)

| Concern | Layer | Why |
|---|---|---|
| A falsifiable prediction with a confidence + a falsifier | **L4** (`ph_nimitta`) | applied fruit |
| The prediction-RECORD emitted for scoring | **L3→L5** (`ka_bhavishya_lekha` → `mi_bhavisya`) | already wired up |
| Scoring the prediction against what actually happened | **L5** (`mi_pramana`) | calibration machinery |
| Confidence *calibration* (are my 0.7s actually 70%?) | **L5** | needs the outcome log |
| The auspicious window / remedy / rectification a person acts on | **L4** | applied fruit |

L4 emits products that are **falsifiable by construction** (every anchor carries an explicit
falsifier) so L5 can score them — but L4 does not score itself. This keeps the calibration loop
honest (no marking your own homework).

## §6 — The three native-ratify recommendations (carried from the audit)

### 6.1 — G-LADDER: calibration ladder as a deterministic transform  `[NATIVE-RATIFY — RECOMMENDED]`
The legacy ladder (single≤0.55, 2≤0.65, 3≤0.72, 3+kala≤0.78, ≥4+kala≤0.80, hard ceiling 0.80) is
sound domain judgment. **Recommendation:** keep the ladder's *shape* but drive it from `ka_sangam`'s
real `convergence_score` (I-16) and `independent_current_count` (I-22) — i.e. `anchor_confidence =
min(ceiling(n_independent_currents), f(convergence_score))`, a pure deterministic transform. This
honors deterministic-first + anti-drift (no hand-assigned floats). HALT for the exact mapping sign-off.

### 6.2 — Anchor domain taxonomy  `[inherit — no ratify needed]`
Reuse the 6 legacy domains (career / relationship / financial / spiritual / health / transition).
They map cleanly onto the CDLM domain-linkage vocabulary; no new judgment required.

### 6.3 — G-RECT: PyJHora-computed rectification  `[NATIVE-RATIFY — RECOMMENDED]`
**Finding (AUDIT §5):** `pyjhora_adapter/houses.compute_ascendant(jd_ut, ayanamsha, lat, lon, tz)`
returns the ascendant to fractional degree at any time; PyJHora is the sealed engine (no JH-parity
gate). **Recommendation:** `ph_sodhana` calls it to compute the real cusp crossing and score
candidates — turning the legacy `[EXTERNAL_COMPUTATION_REQUIRED]` stub into a real deterministic
deliverable, leakage discipline preserved. This is the single biggest value-add of the layer. HALT
for sign-off that PyJHora is an acceptable rectification oracle (consistent with the PyJHora-is-the-
engine decision).

## §7 — Migration plan (CORRECTION 1 applied)

- **All L4 migrations start at 330** (global max across BOTH `platform/migrations/` and
  `platform/supabase/migrations/` is 329), placed in `platform/supabase/migrations/`. Pre-allocate
  in DAG order at Conductor pre-fan-out (the "two-174 trap" step).
- **Migration 330 (the first) ALSO drops `kala_timeline`** (CF.L3.2 — deprecated by mig 246).
- One migration per asset table: `phala_anchors`, `phala_muhurta`, `phala_mitigation`,
  `phala_rectification`, `phala_rectification_best`, `phala_outlook`. Each: chart-scoped, the
  natural-key unique index for delete-then-insert, FK to the L3/L2 row it cites where applicable.
- `asset_registry_seed.ts`: the 5 ph_* rows already exist (confirm `target_floor: null` → set to
  achieved count post-build, floors-aspirational); **add the `ph_phaladesa` row** (sort_order 6,
  layer 'phala', depends_on the 4 upstream ph_*). Serialize seed edits per wave (CS1).

## §8 — Build method + the HARD seal gate

Follows the proven L3 wave method. The non-negotiable gate, learned the hard way in L3 (burned ~4×):

> **The live VISUAL cockpit + Cloud-Run-revision == merge-SHA is the ONLY seal signal.** A green
> `/api/cockpit/stats`, a swarm "SEALED" report, or a correct fix sitting on an unmerged branch are
> ALL false positives. **Bake visual cockpit verification (prod revision confirmed == merge SHA, the
> Phala panel shows 6 lit assets with real counts, zero error/missing_table) as a HARD seal gate from
> the start.** Verify the visual surface, not just the JSON.

Other inherited gates: PROD-VERIFY every AC against prod (not a worktree DB); FORENSIC 7/7 holds;
only chart `482012f1`; anti-drift grep (zero non-phala writes, zero `.commit()/.rollback()`);
spine-first internal gate on `ph_nimitta` (prove one anchor end-to-end before the rest fan out);
model policy Gemini/DeepSeek (Anthropic banned).

## §9 — Wave structure (sequenced in the session_queue)

```
P0  Pre-fan-out: PRE-1 prod==main gate; PRE-2 pre-allocate migs 330+ (two-174 trap) + the
    kala_timeline drop; PRE-3 pin ratified params read-only; PRE-4 register ph_phaladesa in seed.
P1  ph_nimitta  — SPINE-FIRST HARD GATE (prove one anchor end-to-end: ka_sangam window →
    calibrated anchor → falsifier → anti-drift clean) BEFORE P2 fans out.
P2  (parallel, disjoint) ph_muhurta · ph_pratikara
P3  ph_sodhana  — PyJHora-computed rectification (native-ratify G-RECT first)
P4  ph_suddha_sodhana — argmax over ph_sodhana
P5  ph_phaladesa — composite dossier (reads P1–P4); B.11 whole-chart-read enforced
SEAL  live-cockpit VISUAL gate (6 lit) + prod-revision==SHA + anti-drift audit + DRAFT→CURRENT +
      L4_PHALA_CLOSE_v1_0.md (+ L5 onboarding contract) + CURRENT_STATE + SESSION_LOG.
```

## §10 — Retrieval (how the instrument serves L4)

L4 outputs serve through the existing retrieval-layer registry (tools/resources/prompts; no tier
gating). New tools: `query_phala_anchors(chart_id, window, domain?, min_confidence?)`;
`find_phala_muhurta(chart_id, action_class, window)`; `query_phala_mitigation(chart_id, window)`;
`query_rectification(chart_id)`; `phala_outlook(chart_id, horizon)` (the dossier; B.11 composite).
All route through the Whole-Chart-Read protocol (L2 synthesis first). Detailed in the closing review.

---
*End of L4_PHALA_CAMPAIGN_PLAN v1.0. 6 assets, migrations 330+, PyJHora-computed rectification, the
live-cockpit HARD seal gate. The per-asset briefs implement this; the session_queue sequences it.*
