---
artifact: PARIPRASHNA_STREAM_CHARTER_S6
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S6
stream_name: Performance, Resilience & Observability
frozen_by: Session A, Phase A5
---

# Stream charter — S6 (Performance, Resilience & Observability)

- **Owner (actor to register):** `lead-s6`
- **Independent verifier:** `verifier` (Sonnet/high default)
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0`
- **Deployed revision pin:** `amjis-web` @ `cafa894ee7cfc2e86743bb92625e7faf293aec0a`, `amjis-mcp` @ `b8937e0c1a8af03863f5e4d121119f99c4db4060` — both stale; the web staleness is the Nirmana deploy blocker (PR #1601), unrelated to Paripraśna. Load/chaos measurements MUST be taken against whatever is actually deployed at measurement time, not assumed — record the exact image tag with every measurement.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s6-performance-resilience`
- **Approved ceiling:** 8h wall-clock; spend by judgment
- **Entry gate and dependencies:** CG-2 CLOSED (`031e03fc-7685-4c17-af34-bba115318246`); P2→P3 RESOLVED (`02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status

RESOLVED per A2 — needed for authenticated load-test traffic generation.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Load/chaos traffic must target this chart only; never generate load against the native's real chart `482012f1`.

## Scope (test plan v2.1 §10 complete; G5a)

**Primary file territory:** telemetry code (RUM/server-trace instrumentation), SSE/outbox/replay infrastructure, the load-chaos harness itself (build one if none exists yet — check first).

**Metrics to collect (test plan §10.1):** RUM plus server traces for first signal, TTFT, full-turn latency by work class, per-stage latency waterfall (feeds from/coordinates with S4's §4.3.4 output — don't duplicate S4's per-stage instrumentation, consume it), delta-to-commit lag, largest inter-event gap, reconnect/replay and snapshot rate, persistence outcome, client errors, Core Web Vitals, cost per turn/user/channel/model, safety verdicts, lint firings, prediction capture/resolution coverage. Segment by device class, network quality, model, request class.

**Provisional targets (test plan §10.2) — G5a establishes the FIRST measured baseline; targets stay provisional until two weeks of real measurement (G5b, owned by Session C's scheduled monitors, not you):** first signal <300ms; TTFT p50 <4s / p90 <12s for interpretive turns; factual TTFT p50 <2s; factual turn p95 <20s, interpretive p95 <90s, deep-dive p95 <240s; ≥99% replay recovery within buffer TTL with zero content loss; no settled turn silently undurable. Live seed on record: 81.3s end-to-end for one standard interpretive turn via MCP (2026-08-23, EDIR E-006), inside the provisional p95 but with >95% of wall time in planning/synthesis — that's where S4's per-stage data should direct your own optimization-attention reporting. Also track Core Web Vitals at p75: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1.

**Resilience/load battery (test plan §10.3):** controlled load and failure tests for slow first token, 1-byte trickle, long inter-event gap, provider timeout, malformed citation sentinel, giant table, citation-dense answer, reconnect inside/outside buffer TTL, visibility-change reconnect, server loss mid-persist, outbox retry, provider fallback, rate/spend rejection, concurrent interactive/batch pressure. Report tail latency, failures, recoveries, lost/duplicated blocks, memory/CPU growth, queue shedding, cost, AND whether the reader received an honest visible state — a throughput number without these user-outcome facts is explicitly NOT a pass (test plan §10.3 closing line).

**Scope boundary — this is G5a only, not G5b:** you establish baselines and run the load/chaos battery and a demonstrated-can-fail post-deploy smoke ONCE, in-session. The multi-day canary window (G5b, "seven consecutive green smokes") is explicitly NOT yours — Session C installs the scheduled monitors/cron whose results the tracker ingests over the following days; do not attempt to babysit a multi-day window from inside this session (elevation §9/R-3's G5 split exists exactly to prevent that).

**Silent-degradation prevention and cost ceilings:** name every mechanism that could silently degrade (a queue that sheds load without surfacing it, a fallback that switches models without disclosure, a retry that masks a real failure) and prove each is either visible to the reader or logged for operator visibility — this is the same §N.8 earned-signal discipline applied to the performance surface.

**Installs nothing long-running:** per elevation §11.2's S6 block — that's explicitly Session C's job (G5b's scheduled monitors), not yours.

Freeze your denominator: baseline measurement pass (one per metric category above) + the enumerated resilience/load scenarios + the demonstrated-can-fail smoke, before executing.

## Evidence rungs required

Baselines and load/chaos results are inherently LIVE-rung (real measurement against a real deployed instance) — record the exact deployed SHA with every measurement per the pin note above, so a later reader can tell which code version a given number describes.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — file S6 findings as `V3-E-0NN`, `stream: S6`.

## Posture

Measurement-heavy. Sonnet/medium/high as appropriate to volume vs. judgment split. Your waterfall/latency findings are a primary input to S4's synergy-test reporting (test plan §4.3.4) — coordinate, don't duplicate.
