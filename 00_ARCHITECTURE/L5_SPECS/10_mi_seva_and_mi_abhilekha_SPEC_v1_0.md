---
artifact: 10_mi_seva_and_mi_abhilekha_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_SEVA_ABHILEKHA
asset_ids: [mi_seva, mi_abhilekha]
asset_kind: service
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec (the 2 service assets)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§E channel registry/resolver, §E lel_citation gate, §E learning_influence gate, §E per-family/tier/soundness controls, §E conversational defaults, §E MCP parity, §E contribution_state, §E preference store, §D effective-value cached views, §F transit-current binding, §F LEL-update recompute, §F prediction-due sweep, §F freshness marker, §F no-LEL reporting]
---

# mi_seva & mi_abhilekha — The Two L5 Services

> Two **callable/triggered services** (asset_kind: service, like L3's ka_* services) — NOT part of the
> build-DAG spine. `mi_seva` (Sevā, "service") is the **serve-time apply** layer the LLM hits per query.
> `mi_abhilekha` (Abhilekha, "record/journal") is the **journal + re-sync** layer triggered when life
> events are logged.

---

# PART A — `mi_seva` — Serve-Time Apply Service

## A1 — Purpose & value
The user's and the LLM's actual entry point to L5 at query time. It resolves the **effective value**
(base + overlay) under the **contribution-control toggles**, binds to the **current transit moment**, and
serves the right `mi_darshana` insight units — identically through portal and MCP (parity-gated). Nothing
is precomputed-stale: this runs per query.

## A2 — Owns: `mimamsa_preferences` (per-user × channel saved defaults)
```
user_id, channel_id, saved_state, updated_at   PRIMARY KEY (user_id, channel_id)
```

## A3 — Responsibilities (the contribution-control framework lives here)
1. **Channel registry + resolver** — resolve each channel per request: `per-request override → saved
   default (mimamsa_preferences) → system default (ON)`.
2. **`learning_influence` gate** — serve `effective_value` (base ⋈ `mi_adhilepa` overlay, via the cached
   `effective` views refreshed per calibration session) when ON; serve **base** when OFF. OFF == pre-L5
   baseline byte-for-byte (the base was never mutated).
3. **`lel_citation` gate** — suppress literal LEL event facts in served units when OFF (per C3).
4. **Per-family + tier-group + soundness_basis controls** — filter which `mi_kula` families influence
   (e.g. "scientific-only"); negative controls are `CONTROL_ONLY` and can never be served into a reading.
5. **Conversational defaults (C2)** — on an MCP/conversation start with unknown prefs, the service signals
   the LLM to **ASK** the user ("draw on your life events? apply learning adjustments?"); the answers
   become session defaults until changed. (Per-tool MCP args still allow explicit per-call override.)
6. **Transit-current binding (C-1)** — call the L3 services (`ka_gochara`/`ka_dasha_kala`/`ka_graha_sancara`)
   for TODAY's sky/dāśā so the served reading is current, not a build snapshot.
7. **`contribution_state` metadata** — attach to every response: which channels were ON/OFF + how resolved
   (per-request/saved/system) + `calibration_mode` (empirical / prior_only / structural_prior_only).
8. **Provenance endpoint** — on request, return the R4 chain + "what would change with learning on."
9. **Whole-Chart-Read integration** — add the L5 calibration view to B.11; route through L2 synthesis first.

## A4 — Determinism & parity gates
- The gate is a deterministic switch (not an LLM decision). No generative LLM computes a value; the LLM
  consumes served units + narrates.
- **OFF==baseline gate** (RL-2): with `learning_influence` off, served output == pre-L5 baseline (tested).
- **Parity gate** (`parity_check.ts` extension): portal and MCP expose identical channels/controls — CI
  fails on mismatch.
- Effective-value views are deterministic + cache-invalidated per calibration session.

## A5 — Registry / orchestrator
`asset_kind: 'service'`, `storage_type: 'service'` (mirrors `ka_dasha_kala`). Callable at serve time; not
in the click-Build sequential pass. `depends_on: ['mi_adhilepa']` (for catalog lineage; also reads
`mi_darshana`, `mi_kula`, L3 services). Service dir COPY'd in `Dockerfile.pipeline`.

---

# PART B — `mi_abhilekha` — Journal & Re-Sync Service

## B1 — Purpose & value
The engine of currency and the cure for n=1: it captures the **Prediction Journal** answers, turns them
into LEL events, and re-syncs L5 — incrementally, never rebuilding L1–L4. This is what grows the evidence
base through use.

## B2 — Owns: `mimamsa_journal`
```
chart_id, journal_id, prediction_id, prompt_shown, native_answer, answered_at,
resulting_event_id (nullable -- if the answer created an LEL event), provenance_tag
PRIMARY KEY (chart_id, journal_id)
```

## B3 — Responsibilities
1. **Journal surface** — stage **due** predictions (from `mi_bhavisya.lifecycle_status='due'`) and present
   "did this happen?" to the native (portal + MCP).
2. **Ingestion** — a journal answer that reports an event becomes an LEL event (written to `life_events`
   with provenance tags marking it journal-sourced, post-framework, candidate-clean), then triggers
   re-tag in `mi_jivanaghatana`.
3. **Prediction-due sweep (C-3)** — background pass: detect predictions whose `eval_date` passed AND that
   have candidate evidence → flip `mi_bhavisya.lifecycle_status` to `due` → surface for journaling.
4. **LEL-update recompute (the right-time policy)** — on new admissible events, mark L5 **stale** and
   recompute **L5-only**, in DAG order `mi_jivanaghatana → mi_bhavisya → mi_pramana → mi_gunanaka →
   mi_adhilepa → mi_pariksha → mi_sambandha → mi_darshana`. **Never rebuilds L1–L4** (LEL flows only up).
   **Debounced:** coalesce a burst into one recompute at session-close + a manual "recalibrate now" action.
5. **Freshness marker** — write/update `last_calibrated_at` + `lel_version` so the cockpit + `mi_darshana`
   can show "calibrated through event N (date D)" vs "stale — k new events pending."

## B4 — Determinism & gates
- The sweep + recompute are deterministic triggers; the recompute runs the same deterministic writers.
- **Incremental-correctness gate:** an LEL-update recompute touches only L5 tables (assert no L1–L4 write).
- Debounce is deterministic (session-close / explicit trigger), not time-flaky.
- Journal-sourced events get correct provenance so the leakage firewall classifies them properly.

## B5 — Registry / orchestrator
`asset_kind: 'service'`. Triggered (journal action / sweep / manual), not in the build-DAG spine.
`depends_on: ['mi_bhavisya']` (catalog lineage; also drives the L5-only recompute chain). Service dir
COPY'd in `Dockerfile.pipeline`.

---

## §C — Matrix rows satisfied (both services)
channel registry/resolver (§E) ✅ · lel_citation gate (§E) ✅ · learning_influence gate + effective views
(§E/§D) ✅ · per-family/tier/soundness controls (§E) ✅ · conversational defaults C2 (§E) ✅ · MCP parity
(§E) ✅ · contribution_state metadata (§E) ✅ · preference store (§E) ✅ · transit-current binding C-1 (§F) ✅ ·
LEL-update L5-only recompute (§F) ✅ · prediction-due sweep C-3 (§F) ✅ · freshness marker (§F) ✅ · no-LEL
reporting (§F) ✅ · OFF==baseline + parity gates (§G) ✅.

*End 10_mi_seva_and_mi_abhilekha_SPEC v1.0.*
