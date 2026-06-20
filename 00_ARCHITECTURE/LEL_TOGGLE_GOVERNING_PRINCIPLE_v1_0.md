---
artifact: LEL_TOGGLE_GOVERNING_PRINCIPLE_v1_0.md
canonical_id: LEL_TOGGLE_GOVERNING_PRINCIPLE
version: 1.0
status: GOVERNING PRINCIPLE (platform-wide — binds every asset, the retrieval layer, the serve layer, the UI)
authored_by: Cowork 2026-06-19
purpose: >
  Establish the platform-wide rule for how the Life Event Log (LEL) influences the instrument. LEL is
  SEMI-SUBJECTIVE (events are objective; their description/interpretation/astrological-attribution carry human
  judgment) — so anything LEL influences is no longer purely DETERMINISTIC. Therefore LEL-influence-on-responses
  must be a USER-CONTROLLED, platform-wide TOGGLE, applied as a SEPARABLE OVERLAY over a deterministic core that
  stays LEL-free. This doc is the single source of truth for that rule; every brief threads an LEL-compliance note.
---

# LEL Toggle — Platform-Wide Governing Principle v1.0

## §1 — Why LEL is different (the epistemological line)
- **L0/L1/L2 facts = DETERMINISTIC** — computed from the chart, reproducible, objective, auditable.
- **LEL = SEMI-SUBJECTIVE** — the ~56-57 events HAPPENED (objective), but how each was DESCRIBED, INTERPRETED, and
  ATTRIBUTED to astrological causes carries human judgment. LEL is INTERPRETED ground truth, not a planetary position.
- **Consequence:** anything LEL influences is no longer purely deterministic. If LEL silently flowed into every
  response, the instrument's "deterministic, auditable" promise would be quietly broken. So LEL influence on
  responses MUST be explicit + user-controlled.

## §2 — THE RULE (the decoupling — native-finalized 2026-06-19)
Three flows, fully decoupled:
1. **The DETERMINISTIC CORE stays LEL-FREE, ALWAYS.** Every L0/L1/L2 asset (MSR, ledgers, graph, discoveries,
   remedies, lenses, gestalt, scorecard) is computed WITHOUT any LEL input. The stored substrate is pure +
   reproducible. (This is already how the 9 briefs are designed — nothing READS LEL into the data; the
   calibration_hooks are EMPTY slots, not LEL-filled values.)
2. **The INTERNAL RESEARCH always runs + always PRODUCES calibration.** The held-out-LEL validation (B6 §6 / L5
   Mīmāṃsā) runs regardless of any user toggle — it measures whether the instrument's verdicts/discoveries
   correspond to lived events, and PRODUCES a calibration overlay (per-signal / per-domain / per-discovery
   adjustment). This is how WE learn whether the instrument works. It runs ALWAYS.
3. **The USER TOGGLE gates whether that calibration FLOWS INTO THE RESPONSE.**
   - **LEL OFF (default):** the response is free of **TWO** things, not one — (a) LEL CONTENT itself (no life-event
     facts leak in) AND (b) ANYTHING DERIVED FROM LEL (no calibration, no LEL-informed ranking, no validated-
     discovery boost, no confidence adjustment — NOTHING generated using LEL in ANY way). The response contains
     **ZERO LEL-DNA, direct or derived.** The DETERMINISTIC CORE is the ONLY thing that reaches the user. The
     calibration overlay still EXISTS internally — it simply has no path to the response.
   - **LEL ON (user-selected):** BOTH are permitted — LEL content MAY surface AND the calibration derived from the
     internal research IS APPLIED (calibrated confidence, LEL-informed weighting/ranking, validated-discovery boosts).
**In one line: the research never stops and always produces calibration; when LEL is OFF the response is provably
free of ALL LEL-origin influence (content AND derived-calibration); when LEL is ON, both LEL content and its
derived calibration may shape the response.** Research and response are fully decoupled.

## §3 — THE MECHANISM (separable overlay — why the toggle is clean)
LEL must NEVER be baked INTO a stored deterministic value (then you couldn't toggle it off). It is applied as a
SEPARABLE OVERLAY:
- **The calibration overlay is its own layer** (L5 Mīmāṃsā artifact) that REFERENCES the deterministic signals by
  `signal_id` / `discovery_id` / ledger id — it never OVERWRITES them. A signal has its DETERMINISTIC confidence
  (always present) AND, separately, its LEL-CALIBRATED confidence (in the overlay).
- **The `calibration_hook` fields** we deliberately left EMPTY across the assets (epistemic_jsonb.calibration_hook,
  the scorecard calibration frame) are EXACTLY the overlay's attachment points — populated by the internal research,
  applied conditionally.
- **`lel_enabled: true|false`** is a request/config flag the retrieval + serve layer reads. ON → JOIN the overlay
  (additive). OFF → simply don't join it (the natural default — deterministic values returned as-is).
Because the overlay is a conditional JOIN, "off" is the natural state and "on" is purely additive — no separate code path that could drift.

### §3.1 — LEL-PROVENANCE TAGGING (the ENFORCEMENT — how "zero LEL-DNA when off" is GUARANTEED, not judged)
"OFF = no LEL content AND nothing derived from LEL" is enforced by PROVENANCE, not by per-element judgment:
- **Anything generated using LEL — in ANY way — is TAGGED with LEL-provenance** (`lel_origin: true` on the row /
  field / overlay element, including TRANSITIVELY: if value B was computed from an LEL-tagged value A, B is also
  LEL-tagged). LEL content itself, calibration adjustments, LEL-informed rankings, validated-discovery boosts — all carry the tag.
- **When `lel_enabled = false`, EVERY LEL-provenance-tagged element is EXCLUDED at the retrieval/serve boundary** —
  a hard filter, not a guess. If a value/ranking/boost/confidence carries ANY LEL lineage, it is removed; the
  deterministic value (which always exists alongside) is returned instead. No leakage path survives because the
  exclusion keys on the TAG, not on what looks "LEL enough."
- **Verification:** a toggle-off response can be PROVEN LEL-free by asserting zero LEL-provenance-tagged elements
  in the entire return (bo_pramana_mapa + B6 audit this). This makes the strict rule machine-checkable.

## §4 — WHAT EVERY ASSET / LAYER MUST DO (the compliance contract)
- **Every bo_* asset:** compute + store DETERMINISTIC values only; leave the calibration_hook EMPTY; never read LEL into the build.
- **bo_pramana_mapa (scorecard):** its calibration-readiness frame IS the overlay's measurement surface (records the held-out validation; produces the calibration adjustments).
- **bo_anveshana (discovery):** discoveries are deterministic; their FALSIFIABLE-hypothesis validation (vs held-out LEL) produces the discovery-calibration overlay — applied to discovery ranking ONLY when lel_enabled.
- **Everything LEL-touched is TAGGED `lel_origin` (transitively, §3.1)** — content, calibration, rankings, boosts.
- **The retrieval layer:** every tool accepts `lel_enabled`; ON → returns calibrated values (deterministic + overlay); OFF → EXCLUDES every `lel_origin`-tagged element (hard filter) and returns pure deterministic. The provenance return states WHICH mode produced the values.
- **The serve/LLM layer:** honors `lel_enabled`; when OFF, the response is provably free of ALL LEL-DNA (content AND derived — zero lel_origin-tagged elements); when ON, it states that LEL content/calibration is applied (transparency).
- **The UI:** provides the LEL toggle (a clear control); default OFF (deterministic); ON is the user's explicit choice.
- **B6 eval harness:** runs in BOTH modes (LEL-off = pure deterministic baseline; LEL-on = calibrated) and measures the DELTA — this is itself scientifically valuable (it quantifies what LEL contributes).
- **The held-out LEL partition stays SACROSANCT in BOTH modes** — read once for validation, never tuned against.

## §5 — Why this serves the north star
This makes the SUBJECTIVE layer OPT-IN and CLEANLY SEPARATED from the DETERMINISTIC core. A user (or a researcher)
can ALWAYS get the pure-deterministic reading, AND separately see how the LEL-informed reading differs. That
separation is scientifically valuable — it lets us MEASURE the delta LEL contributes (the toggle-off vs toggle-on
comparison is a calibration experiment). It is the research-instrument ethic made concrete: deterministic by
default, subjective-influence explicit + measurable + reversible.

## §6 — Threading into the build
Every per-asset brief carries a one-line "LEL-COMPLIANCE" note: "deterministic-only build; calibration_hook left
empty for the L5/LEL overlay; honors lel_enabled at retrieval/serve, never at build." B6 carries the dual-mode
requirement (§4). The L5 Mīmāṃsā layer OWNS the overlay computation (the internal research → calibration). The
retrieval-strategy doc + the serve layer carry the `lel_enabled` propagation.

---
*End of LEL_TOGGLE_GOVERNING_PRINCIPLE v1.0. LEL is semi-subjective, so its influence on responses is a
user-controlled platform-wide TOGGLE over an always-LEL-free deterministic core. The internal research always runs
+ always produces a calibration OVERLAY (a separable L5 layer referencing deterministic signals, filling the empty
calibration_hooks); the user toggle gates ONLY whether that calibration FLOWS INTO THE RESPONSE (off = pure
deterministic default; on = calibrated). The overlay is a conditional additive JOIN, so off is natural + on can't
drift. B6 runs both modes + measures the delta. Held-out LEL sacrosanct in both. Deterministic by default;
subjective-influence explicit, measurable, reversible — the research-instrument ethic made concrete.*
