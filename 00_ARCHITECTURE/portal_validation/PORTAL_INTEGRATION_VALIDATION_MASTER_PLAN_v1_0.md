---
artifact: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md
canonical_id: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN
version: 1.0
status: AWAITING_NATIVE_GO
phase: PIV (Portal Integration Validation)
authored_at: 2026-05-14
authored_by: Cowork brainstorm session (Opus 4.7)
purpose: >
  End-to-end validation that the post-AIOps-trilogy portal works as one
  coherent system: AIOps Control Panel + Adapter Layer + Consume UI +
  M1–M10 knowledge modules + audit/logging/observability. Audit-only;
  no code changes. Output is evidence + a categorized punch list.
execution_rules: 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md (reused)
related:
  - 00_ARCHITECTURE/portal_validation/briefs/PHASE_QG_0_BRIEF.md … PHASE_QG_8_BRIEF.md
  - 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md (Phase 1 reference)
  - 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md (Phase 2 reference)
  - 00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md (Phase 3 reference)
changelog:
  - v1.0 (2026-05-14): authored after AIOps trilogy merged; covers M1–M10 + AIOps trilogy + auditing/observability
---

# Portal Integration Validation (PIV)
## Master Plan v1.0

---

## §0 — TL;DR

After three days of AIOps construction (Control Panel + Adapter Layer +
Consume UI Overhaul) plus the M1–M10 MARSYS-JIS macro-phase arc, the
portal contains a *lot* of working pieces. Each piece passed its own
acceptance. **No one has yet validated that they work together as one
coherent system.**

PIV is that validation. Nine sub-phases (QG.0 → QG.8), audit-only (no
new code changes — discoveries become a separate Phase-N backlog),
autonomous execution via Claude Code with `--dangerously-skip-permissions`.
Live LLM calls (not mocked) but constrained to cost-effective models so
total spend is < $1.

End deliverable: `QG8_FINAL_REPORT.md` with categorized punch list
(BLOCKERS / HIGH / MEDIUM / LOW) and a final go/no-go declaration on
"the portal works seamlessly."

---

## §1 — The seven integration surfaces

The trilogy + M1–M10 created these seams between components. PIV
validates each.

1. **AIOps Control Panel ↔ runtime_config ↔ adapter** — Phase 1 ↔ Phase 2 seam.
2. **Adapter ↔ real provider behavior** — Phase 2 against live LLMs.
3. **Adapter events ↔ Consume UI state machine** — Phase 2 ↔ Phase 3 seam.
4. **M1–M10 data modules ↔ query pipeline** — knowledge modules into context/retrieval/synthesis. **The biggest open question.**
5. **Query path ↔ audit + observability** — every query trace complete across tables.
6. **Edge cases + failure modes** — DB down, provider auth_fail, mid-stream cancel, long context, flag flips.
7. **Performance + cost baseline** — re-baseline post-trilogy.

---

## §2 — Design philosophy

Five principles:

1. **Audit-only.** PIV writes no application code. Findings become a separate Phase-N backlog. Mixing audit + fixes blows up scope.
2. **Live, not mocked.** Mocked tests miss real provider quirks and real timing. PIV exercises real adapter against real providers, real DB, real Cloud Run.
3. **Cost-discipline.** Every live LLM call uses the cheapest model in the target stack (§3 below). Total PIV spend target: < $1.
4. **Evidence-first.** Every assertion has a captured artifact (DB query result, HTTP response, screenshot, log excerpt). Reports cite evidence files.
5. **Read-only against production.** PIV does NOT mutate production state. No new stack configurations applied, no new overrides persisted past the test (cleanup at phase close), no schema changes.

---

## §3 — Cost-effective model strategy

Per the native rule (DeepSeek → Gemini Flash Lite → NIM; Anthropic banned),
PIV's live LLM calls map to:

| Stack | Cheapest viable model for PIV | $ / 1M input | $ / 1M output | Notes |
|---|---|---|---|---|
| `nim` | `nvidia/nemotron-3-super-120b-a12b` | free | free | 1M ctx, default |
| `gemini` | `gemini-2.5-flash-lite` | $0.015 | $0.06 | tier=worker, role=both |
| `deepseek` | `deepseek-chat` | $0.14 | $0.28 | non-thinking; valid API ID |
| `gpt` | `gpt-4.1-nano` | $0.05 | $0.20 | 1M ctx |
| `anthropic` | **SKIPPED** | — | — | per standing native rule |
| `marsys` | `gemini-2.5-flash-lite` | $0.015 | $0.06 | MARSYS default = Gemini cheapest |

PIV uses `runtime_config`'s per-request override mechanism (header
`x-aiops-stack` or `x-aiops-model-<callType>-<role>`) to force the
cheapest model regardless of what the production AIOps config currently
points at. This means PIV is non-disruptive to actual users' config.

Estimated total spend: ~$0.30–$0.80 for the full arc.

---

## §4 — M1–M10 data module inventory (validation targets)

The query pipeline should leverage all of these. PIV's QG.3 walks each
module and asks: "Is this actually being consumed by the pipeline?"

| Module | Deliverables | Expected consumer in query pipeline |
|---|---|---|
| **M1** | L1 FORENSIC chart data (ascendant, planets, dashas, divisional charts) | `bundle_hydrator` → L1 facts in context |
| **M2** | L2.5 corpus (MSR base, UCN, CDLM, CGM, RM) | `bundle_hydrator` → L2.5 holistic synthesis in context |
| **M3** | Discovery layer (temporal animation, transit signals) | retrieval layer / discovery tools (035_DISCOVERY_LAYER) |
| **M4** | LEL ground-truth spine + LL.1 production weights (30 signals) | calibration scoring, LL.1 weights consulted for predictions |
| **M5** | DBN topology + CPT parameters; LL.2–LL.7 edge/discovery layer | DBN inference (shadow or active); LL.2 edge promotion |
| **M6** | Prediction ledger; scoring infrastructure; LL.8/LL.9 activation | `07_PROSPECTIVE_TESTING/` populated on synthesis predictions; LL.8 fires on LEL events |
| **M7** | (not in memory — verify existence) | — |
| **M8** | Classical text cross-reference (420 attributions, Nadi+BNN signals; MSR v4.0) | retrieval can fetch classical attributions; MSR has 29 net-new signals visible |
| **M9** | Multi-school triangulation (7 schools; MSR v5.0, 573 signals; tools 27+28) | structured planner picks tools 27+28 for relevant queries; MSR v5.0 active |
| **M10** | (acharya panel gate ≥3 reviewers; not yet active) | future quality bar — not in pipeline yet |

QG.3's brief walks each module systematically.

---

## §5 — Nine-sub-phase arc

| QG | Scope | Live LLM cost (est.) |
|---|---|---|
| **QG.0** | Inventory + map every component / integration / audit table / M1–M10 deliverable | $0 (read-only) |
| **QG.1** | AIOps Control Panel → runtime_config → adapter (config writes change query behavior) | $0.05 (a few config-change + canonical-query pairs) |
| **QG.2** | Provider matrix smoke: 5 active providers × 11 call types × {primary, fallback} | $0.20 (one probe per cell with cheap models) |
| **QG.3** | **M1–M10 data module integration audit** — does the pipeline actually consume each? | $0.10 (a few representative queries to inspect bundle content) |
| **QG.4** | Audit + observability trace — one canonical query, traced end-to-end | $0.05 (single canonical query, traced) |
| **QG.5** | UX flow validation — scripted checks against the new Consume UI | $0.10 (a few queries to exercise UI states) |
| **QG.6** | Edge cases + failure modes (DB down, auth_fail, cancel, long context, flag toggle) | $0.10 (small probes; some are pure failure tests with no LLM call) |
| **QG.7** | Performance + cost baseline — latency p50/p95/p99 per stack | $0.15 (representative volume per stack) |
| **QG.8** | Final report + categorized punch list + go/no-go | $0 (synthesis from prior phase outputs) |

Total estimated LLM spend: **~$0.75**. Wall-clock: ~8–12 hours of
autonomous execution.

---

## §6 — Branch + worktree

**Branch:** `feature/portal-integration-validation`, cut from `main`
(currently at `d35a40b` — Phase 3 merge).

**Worktree:** `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`.

Same pattern as AIOps phases. The branch is local-only (NOT pushed) per
the standing rule. Reports get committed to the branch; at QG.8 close
the native reviews and merges to main.

### Scope boundaries (every phase)

```yaml
may_touch:
  - 00_ARCHITECTURE/portal_validation/**        # ALL PIV docs
  - CLAUDECODE_BRIEF.md                          # rotation
  # No code changes anywhere. PIV is audit-only.

must_not_touch:
  - platform/**                                  # production code; PIV is read-only
  - 01_FACTS_LAYER/**                            # canonical L1 data
  - 025_HOLISTIC_SYNTHESIS/**                    # canonical L2.5
  - 06_LEARNING_LAYER/**                         # learning artifacts
  - 035_DISCOVERY_LAYER/**                       # M3 deliverables
  - 07_PROSPECTIVE_TESTING/**                    # M6 deliverables
  - All other 00_ARCHITECTURE/ subdirs except portal_validation/
  - .github/workflows/**                         # CI config — no PIV-related deploys
```

The only thing PIV writes are its own audit reports under
`00_ARCHITECTURE/portal_validation/`.

---

## §7 — Definition of done

PIV is **DONE** when, after QG.8 closes:

- [ ] All 9 sub-phases CLOSED.
- [ ] Every QG.N produces its named report in `00_ARCHITECTURE/portal_validation/`.
- [ ] `QG8_FINAL_REPORT.md` contains:
  - Aggregated findings from QG.0–QG.7.
  - Categorized punch list (BLOCKERS / HIGH / MEDIUM / LOW).
  - Per-finding: evidence path, suggested remediation, estimated effort.
  - Go/no-go declaration on "seamlessly working portal."
- [ ] Branch ready for native review + merge.
- [ ] Madhav worktree unchanged throughout (or REPORT-not-BAIL on independent activity).

---

## §8 — Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| PIV's queries pollute production audit tables | LOW | Tag every PIV query with `x-piv-test-run: <run-id>` header; queries are filterable + deletable post-run |
| PIV's config changes leak into user-visible state | MED | Use per-request override headers, not persistent DB writes |
| Live LLM cost exceeds budget | LOW | Cheapest models specified in §3; cap at ~$1 with abort threshold |
| M1–M10 data path requires running the actual pipeline end-to-end | MED | QG.3 uses real queries through `/api/chat/consume` with audit trace, not synthetic introspection |
| Validation surfaces a real production bug | EXPECTED | This is the point — it goes into the punch list |
| Madhav worktree disturbed | LOW | All PIV ops use `git -C` with absolute paths; never `cd` into Madhav |

---

## §9 — Trigger protocol

Same shape as AIOps phases:

1. Native approves this master plan + the 9 briefs.
2. Native runs the pre-launch Claude Code prompt → creates `../madhav-piv-tmp`, imports briefs, stages QG.0 brief.
3. Native opens `madhav-piv-tmp` in Antigravity, pastes the autonomous loop prompt.
4. Loop executes QG.0 → QG.8, rotating `CLAUDECODE_BRIEF.md` between phases.
5. At QG.8 close, `CLAUDECODE_BRIEF.md` flips to `status: COMPLETE`. Native reviews `QG8_FINAL_REPORT.md` and decides next move (merge for record-keeping; whether to commission a fix-it Phase 5).

---

## §10 — Open questions resolved (per native decisions)

| # | Question | Resolution |
|---|---|---|
| Q1 | Scope of data module integration audit | **M1–M10**, the full macro-phase arc |
| Q2 | Live LLM calls vs mocked | **Live**, cost-effective models per §3 |
| Q3 | Branch model | **Worktree** at `madhav-piv-tmp`, same as AIOps |
| Q4 | Timing | **Now** (during the 48h Phase 3 watch) |

---

*End of PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md*
*Awaiting native acceptance for launcher trigger.*
