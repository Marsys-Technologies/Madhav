---
status: OPEN
session_id: PIV_QG_3
phase: QG.3
phase_name: "M1–M10 data-module integration audit"
next_session: PIV_QG_4
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_3
## Portal Integration Validation, Step 3 — M1–M10 Integration Audit

---

## §0 — Executor orientation

QG.3 is the heaviest of the nine sub-phases. It is the answer to the
native's literal concern: *every M1–M10 deliverable that exists in the
repo — is it actually wired into the running query pipeline, or is it
sitting in a folder that nothing reads?*

QG.0 already produced `QG0_M_MODULE_MAP.md` with a per-macro-phase
**validation hypothesis** ("If M<N> is wired, then …"). QG.3's job is
to test each of those hypotheses against the live system.

Live LLM calls allowed, cheap models only, per-request override
headers preferred over persistent config writes.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/PORTAL_INVENTORY.md (QG.0 — §2 integration seams)
3. 00_ARCHITECTURE/portal_validation/QG0_M_MODULE_MAP.md (QG.0 — per-M validation hypotheses)
4. 00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md
5. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (M1–M10 strategic arc)
6. 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
7. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (active phase pointer)
8. M-close sealing artifacts:
     00_ARCHITECTURE/M2_CLOSE_v1_0.md
     00_ARCHITECTURE/M3_CLOSE_v1_0.md
     06_LEARNING_LAYER/M4_CLOSE_v1_0.md
     06_LEARNING_LAYER/M5_CLOSE_v1_0.md
     M8_CLOSE, M9_CLOSE (locate via CAPABILITY_MANIFEST)
9. platform/src/lib/pipeline/bundle_hydrator.ts
10. platform/src/lib/pipeline/pipeline_planner.ts
11. platform/src/lib/pipeline/manifest.ts
12. platform/src/lib/tools/** (all 27/28 tools)
13. platform/src/lib/synthesis/synthesize.ts + system_prompts.ts
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG3_M_INTEGRATION_AUDIT.md       # NEW — main deliverable
00_ARCHITECTURE/portal_validation/qg3_evidence/                      # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code (read-only).
- All data artifacts under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `06_LEARNING_LAYER/` (read-only).

---

## §3 — Work plan

### 3.1 — Per-M validation matrix

For each macro-phase M1 → M10, run the validation hypothesis from
QG0_M_MODULE_MAP.md. Below is the audit grid; rows are
**non-negotiable** — every M-phase gets a row even if the hypothesis
returns "not yet integrated".

#### M1 — L1 Forensic chart layer
**Hypothesis:** L1 FORENSIC v8.0 is the authoritative source for chart
data accessible to the query pipeline. Pipeline never invents numerical
chart values (B.10 discipline).
**Tests:**
- Grep `bundle_hydrator.ts` + `manifest.ts` for `forensic` / `L1` /
  `FORENSIC_ASTROLOGICAL_DATA`. Verify the asset is loaded into the
  context bundle.
- Submit a chart-data query ("what is the exact degree of my Mars?")
  with a cheap synthesis model. Capture the response.
- Assert: response cites a fact ID from L1 OR emits
  `[EXTERNAL_COMPUTATION_REQUIRED]`. Fabricated chart values = HIGH
  finding.

#### M2 — Corpus activation (L2.5 holistic synthesis)
**Hypothesis:** MSR + UCN + CDLM + RM + CGM are bundled into the
synthesis context. A holistic query (B.11 Whole-Chart-Read) consumes
them.
**Tests:**
- Grep `bundle_hydrator.ts` for `MSR` / `UCN` / `CDLM` / `RM` / `CGM`
  and confirm all five are wired (canonical ID resolution).
- Submit: *"Whole-chart synthesis: what is the most consequential
  pattern in this chart and why?"*
- Assert: synthesis response surfaces at least one MSR signal ID, one
  UCN node, one CDLM linkage in the derivation ledger.

#### M3 — Temporal animation / Discovery
**Hypothesis:** Dasha/transit overlays + Discovery-Layer endpoints
emit time-indexed signals that the planner can request.
**Tests:**
- Inspect `lib/tools/` for time-aware tools (saturn transits, dasha
  windows, etc.).
- Submit a time-bound query: *"What's running in my chart over the next
  6 months?"*
- Capture `tool_call` events from the adapter event stream. Assert at
  least one time/dasha tool was invoked.

#### M4 — Calibration + LEL ground-truth spine
**Hypothesis:** LEL v1.6 events + LL.1 calibration weights are
retrievable. Calibrated confidence appears on predictive answers.
**Tests:**
- Grep production code for `LL.1` / `signal_weights` / `LEL` paths.
- Submit a prediction-class query and inspect the response for
  calibrated probability + confidence band.
- Assert: response contains a probabilistic claim with a confidence
  interval, OR clearly states why calibration is unavailable.

#### M5 — DBN topology + LL.2–LL.7 learning substrate
**Hypothesis:** LL.2 per-edge weights and the DBN topology inform the
planner's tool-choice or the synthesis's signal-weighting.
**Tests:**
- Grep for `dbn` / `LL.2` / `signal_weights/production` references.
- Submit a multi-signal query and inspect the synthesis derivation
  ledger for evidence of weighted aggregation.
- Note: if M5 is not yet wired into the runtime path (likely —
  CURRENT_STATE shows M5 is the active phase, not closed), document as
  "scaffolded, not pipeline-consumed yet" with severity LOW.

#### M6 — Prospective prediction ledger
**Hypothesis:** When a prediction is made, it's logged to the
prospective ledger with falsifier + horizon before outcome is observed.
**Tests:**
- Inspect `06_LEARNING_LAYER/` for the ledger schema + writer.
- Submit a prediction query.
- Query the ledger DB for the new row. If table doesn't exist or write
  didn't fire, mark MEDIUM finding (M6 is TIME-GATED ~2026-11-14 per
  memory; pre-time-gate, the writer should be scaffolded but data may
  be sparse).

#### M7 — Verify-existence audit
**Hypothesis:** A "verify-existence" mode is callable and returns
either a citation or `[EXTERNAL_COMPUTATION_REQUIRED]`.
**Tests:**
- Locate the verify-existence tool / endpoint.
- Submit a fact-check query: *"Verify that my Atmakaraka is Mars."*
- Assert: response either cites L1 fact ID OR returns EXTERNAL marker.
  Pure-LLM speculation = HIGH finding.

#### M8 — Classical attributions
**Hypothesis:** 420 attributions from M8 are bundled when relevant; a
synthesis response on a classical-knowledge query surfaces
classical-source citations.
**Tests:**
- Grep `bundle_hydrator.ts` for `attribution` / classical text refs.
- Submit a classical-grounded query: *"Per Parashara, what does Saturn
  in 10H signify for career?"*
- Assert: response cites at least one classical attribution ID. Missing
  attribution = MEDIUM finding (M8 is closed; bundle should include).

#### M9 — Multi-school triangulation + MSR v5.0
**Hypothesis:** MSR v5.0 (573 signals) is the bundled MSR (not v4.0,
not v3.0). Tools 27 + 28 (multi-school query) are callable.
**Tests:**
- Read the MSR canonical ID resolution in bundle_hydrator. Assert the
  path resolves to `MSR_v5_0.md` (or equivalent — confirm via
  CAPABILITY_MANIFEST).
- Submit a school-triangulation query: *"What do Parashara, Jaimini,
  and Nadi say about my career?"*
- Inspect tool_call events for tools 27 and 28.
- Assert: response surfaces ≥2 schools with attributions.

#### M10 — Acharya panel (future)
**Hypothesis:** M10 is GATED (acharya panel ≥3 reviewers); should not
be wired into pipeline yet.
**Tests:**
- Grep for `acharya_panel` / `M10` integration points.
- Assert: no production code path consumes acharya panel reviews yet.
  If a stub exists, document as "scaffolded, deferred to ≥3-acharya
  recruitment milestone".

### 3.2 — Per-M findings classification

For each M-row, classify the integration state into one of:

- **WIRED + EXERCISED** — code path consumes the deliverable; live
  query verified surfacing of it.
- **WIRED + UNEXERCISED** — code references the deliverable but the
  live query didn't trigger its use. Possible: wrong query, wrong
  classifier route, or genuinely dormant code.
- **NOT WIRED** — no code path consumes the deliverable. Either
  pre-pipeline-integration (M5/M6) or a finding (M8 attributions
  missing).
- **GATED / FUTURE** — deliberately deferred (M10 acharya panel).

### 3.3 — Cross-M findings

Some findings cut across Ms. Audit for:
- **Stale MSR version** — production code resolving to v3.0 or v4.0
  instead of v5.0 (CURRENT canonical).
- **Stale LEL version** — production code resolving to LEL v1.2 paths
  (renamed/archived).
- **Discovery Layer Gemini side** — does Claude know about Gemini's
  Discovery Layer outputs? Are they retrievable in the bundle?
- **Held-out-sacrosanct rule** — every prediction route MUST NOT see
  outcome before predict. Audit M6/M7 paths for leak vectors.

### 3.4 — Author QG3_M_INTEGRATION_AUDIT.md

The deliverable, structured as:

```
§1 — Executive summary
  Per-M integration state at a glance (table):
  | M | Phase Name | State | Live verification | Severity |
  |---|---|---|---|---|
  | M1 | Forensic L1 | WIRED + EXERCISED | <run-id> | — |
  ...

§2 — Per-M deep dives (M1 → M10)
  For each:
  - Hypothesis tested
  - Tests run + run-id + commands
  - Result
  - State classification
  - Findings (if any) with severity

§3 — Cross-M findings
  - Stale-version checks
  - Held-out-sacrosanct audit
  - Discovery Layer cross-native

§4 — Severity-ordered finding list
  BLOCKER → HIGH → MEDIUM → LOW

§5 — Open questions for QG.4 (audit trace verification)
```

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG3.1 | Per-M validation matrix has 10 rows (M1–M10) | grep |
| AC.QG3.2 | Each row has tests run + result + state classification | parametrized |
| AC.QG3.3 | At least one live LLM query per M (where applicable) | run-id refs |
| AC.QG3.4 | MSR version check: production resolves to v5.0 | assertion |
| AC.QG3.5 | Held-out-sacrosanct check: no leak vector found, or finding logged | audit |
| AC.QG3.6 | Severity-ordered finding list authored | grep §4 |
| AC.QG3.7 | Total LLM cost < $0.40 | sum |
| AC.QG3.8 | Anthropic stack untouched | audit query |
| AC.QG3.9 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
docs(piv-QG.3): M1–M10 data-module integration audit

- 10-row per-M validation matrix authored.
- Live-LLM queries executed per M with cheap models.
- N findings (BLOCKER/HIGH/MEDIUM/LOW) captured.
- Cross-M audits: MSR version, LEL version, held-out-sacrosanct, Discovery cross-native.

AC summary: 9/9 PASS
```

Rotate to QG.4.

---

## §6 — BAIL OUT

- A WIRED claim from QG.0's QG0_M_MODULE_MAP turns out to be fictional
  (no actual code consumes the deliverable). Capture and continue — do
  not bail unless the count exceeds 3.
- Production code is found resolving to a SUPERSEDED data artifact path
  (e.g., MSR v3.0 instead of v5.0). Document as BLOCKER and continue.
- Held-out-sacrosanct leak vector found in M6 or M7. STOP and report
  immediately.

---

*End of PHASE_QG_3_BRIEF.md*
