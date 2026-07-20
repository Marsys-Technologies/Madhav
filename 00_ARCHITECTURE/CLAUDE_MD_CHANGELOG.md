---
artifact: CLAUDE_MD_CHANGELOG.md
version: "1.0"
status: CURRENT
role: >
  Full verbatim changelog for CLAUDE.md, moved out at v6.0 realignment (2026-06-12) to keep
  CLAUDE.md itself durable and short. Every entry from v2.0 (2026-04-24) onward is preserved
  here for audit trail. The CLAUDE.md file keeps only the last 2–3 entries inline.
---

# CLAUDE.md — Full Changelog

## v6.2 (2026-06-29, L4-PHALA-SEAL)

L4 Phala sealed. New canonical artifact `L4_PHALA_CLOSE_v1_0.md` (canonical_id `L4_PHALA_CLOSE`) — the definitive L4 closure record (9 ph_* assets, migrations 330–339 + fixes 362/363/366/367, contract-compliance CLEAN, ph_pramana D5 NO-SCORING gate, deterministic-phala / L5-owns-calibration boundary, L4→L5 onboarding). §E L4 row `✓ BUILT (seal pending)` → `✓ CLOSED`; §E "truly open items" note updated to record that **all six build layers L0–L5 are now sealed/closed — the build arc is complete**. Seal rests on: 9/9 registered + clean DAG (DB-verified), contract greps CLEAN, Abhinandan `1c826d5a` end-to-end L1→L5 build, and GATE A prod reconciliation; honest caveat recorded that the native chart is pre-global-build (cold) at seal time so live native L4 counts populate on the imminent build.

## v6.1 (2026-06-29, LAYER-STATUS-REALITY-REFRESH)

§E layer-build table corrected to match built/sealed reality (the v6.0 table was authored at L1-done/L2-next and went stale as L2–L5 were built). Changes: **L2 Bodha** `NEXT` → `✓ BUILT` (8 → 14 assets; ran end-to-end for Abhinandan L1→L5 2026-06-27); **L3 Kāla** `DRAFT/pending` → `✓ CLOSED` (12/12 buildable; seal `L3_KALA_CLOSE_v1_0.md`); **L4 Phala** `DRAFT/pending` → `✓ BUILT` (9/9; formal seal pending — no L4 CLOSE/SEAL artifact yet); **L5 Mīmāṃsā** `DRAFT/pending` → `✓ SEALED` in STRUCTURAL mode (seal `L5_SEAL_AND_SHIP_REPORT_v1_0.md`; neutral cold-start calibration values are by-design, not unfinished). L1 row: stale "585,710 total rows" dropped; seal ref `L1_GANITA_CLOSURE_v1_0.md` → `_v2_0.md`. §E "Truly open items" v5.74 hardcoded snapshot replaced with a CURRENT_STATE §2 pointer + durable note that the L4 formal seal is the one remaining layer-closure step. Companion (non-CLAUDE.md) change this session: `mi_jivanaghatana` reclassified global → per-chart (writer code + migration 372) — it writes the per-chart `mimamsa_event_provenance` table and its unscoped DELETE would have wiped cross-chart provenance once a second chart was built.

## v6.0 (2026-06-12, CLAUDE-MD-REALIGNMENT)

Structural realignment to L1-done/L2-next reality. §F collapsed to CURRENT_STATE pointer (M5/M4 you-are-here specifics deleted). §E replaced: 15 completed arcs → layer-reality block (L0✓/L1✓/L2-next/L3–L5 pending) + frozen orchestrator note + open items only. §D trimmed to currently-canonical artifacts (retired STEP_LEDGER, old phase plans, FILE_REGISTRY superseded rows dropped). Changelog moved to this file (full history preserved verbatim). §B fixed: chart_facts is the canonical L1 source; FORENSIC v8.0 markdown archived; forensic_render.ts RETIRED; 7 FORENSIC birth anchors named. Asset-id underscore convention + layer-name lexicon added. §C updated: item 5 → active campaign = L2 Bodha per CURRENT_STATE + L2_BODHA_CAMPAIGN_HANDOFF; item 13 → frozen orchestrator (ORCHESTRATOR_CONVERGENCE_CLOSE) with correct chart-build note; new §C items 14–16 add L1 closure, L2 handoff, and orchestrator-close docs. New §N standards block: orchestrator contract, idempotency-per-layer, floors/tier/determinism/JH, L1-authority-over-L2.5. Frontmatter version corrected (was "4.8" in frontmatter vs "5.1" in body footer — unified to 6.0).

## v5.1 (2026-06-09, GANITA-NAMING-RECONCILIATION)

Gaṇita naming reconciliation COMPLETE: migration 195 relabels 8 `ganita.*` asset_registry ids → `ga_*`; `GANITA_NAMING_RECONCILIATION` added to §D snapshot.

## v5.0 (2026-06-02, BUILD-GUARANTOR-SWARM-CHARTER)

Build-Workflow Guarantor Swarm Charter authored: new canonical artifact `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` (canonical_id `BUILD_GUARANTOR_SWARM_CHARTER`) added to §C mandatory reading as item 13 and to the §D snapshot table; defines the agentic swarm guaranteeing the chart-build workflow across Gate 0 Assess&Author + Code/Deploy/Runtime gates, 12 roles, and the Asset Contract Registry schema; design pending native confirmation, asset catalog referenced to migration 158 (28 units A1–A22+META_α–ζ; A1–A14 wired, A15+ defined-not-wired) + VALIDATED_ASSET_REGISTRY; follow-ups: register in CAPABILITY_MANIFEST.json + run drift/schema validators.

## v4.9 (2026-05-30, MULTI-AYANAMSHA-DETERMINISTIC-BUILD)

Multi-Ayanamsha Deterministic Build COMPLETE: 4 parallel streams (A/B/C/D); 22 chart assets + 6 META synthesis layers; UTEE + BRIDGE + META-α–ε shipped; ~160 retrieval tools; 14 migrations (140-153); sealing artifact at `00_ARCHITECTURE/MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md`; operator queue: apply migrations 140-153, run ACC1 answer:eval after build job, ACC3 IS.8(b) red-team, ACC4/ACC5 smoke tests post-deploy, trigger native chart build.

## v4.8 (2026-05-28, PLATFORM-MODERNIZATION-SEALED)

Platform Modernization arc SEALED: Batch 5 Wave-4 final seal complete; 7 Wave-4 units shipped (4.refactor_pipeline_shim, 4.observability, 4.memorystore_caching, 4.edge_and_infra_hygiene, 4.build_trigger, 4.learning_loop, 4.red_team_seal); 0 class-1 red-team findings; 8/8 hard gates GREEN; 223/223 tests green on main; tools/program-tracker/ retired (ephemeral); seal artifact at `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md`; full red-team report at `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md`; operator queue: migrations 081–090/118/119 + 6 IaC apply.sh + Cloud Run env-var cleanup + answer:eval live baseline + BUILD_TRIGGER flag flip + amjis-tracker delete + amjis-db-password rotate + depth-selector native review.

## v4.7 (2026-05-26, MCP-TOOL-AUDIT-REMEDIATION-V2)

MCP Tool Audit Remediation v2 COMPLETE: 40/40 tools at 100% (Audit 4c). Session A backward-compat Zod aliases (ee498f34); Session B planet seed + signal confidence + mantras filter (a94b5caf); MARSYS_REPO_ROOT env var applied; amjis-mcp-00019-76h + amjis-web-00424-gv2; main HEAD 18a3b746; audit harness platform-mcp/scripts/audit4_live.ts; P3 CGM+L5 deferred non-blocking.

## v4.6 (2026-05-26, GISMCP-REMEDIATION)

GISMCP Remediation COMPLETE: all 40 MCP tools unconditional; RETRIEVAL_TOOLS 51→55; MSR 573/573 VERIFIED_NO_GAP; worktrees + branches cleaned; workstream added to §E.

## v4.5 (2026-05-25, UDA-2/3/4-COMPLETE)

UDA-2/3/4 COMPLETE: MCP tools 26→40; Universal Parity Campaign FULLY COMPLETE — all 34 sessions across UDA-Q/0/1/2/3/4; Portal 51 tools, MCP 40 tools, both channels at parity; INTERFACE_NORMALIZATION_REGISTER v1.0; PLANNER_PROMPT v2.7 R-NRM.1; 50 MSR citation scaffolds; bootstrap manifests auto-registration fixed; MadhavParity2 worktree retired; PR #164 merged at 79a8168f; CURRENT_STATE v5.57; SESSION_LOG appended.

## v4.4 (2026-05-25, UDA-1-COMPLETE)

UDA-1 COMPLETE: portal tools 36→51; 15 tools channel:both in CAPABILITY_MANIFEST; Universal Parity Campaign §E entry added; workstream count "Fourteen"→"Fifteen"; worktrees MadhavParity/R11A/R11B/R11CDE/R11F/R11G/ToolingFix retired; CURRENT_STATE v5.56; SESSION_LOG appended.

## v4.3 (2026-05-25, DAR-COMPLETE)

DAR workstream COMPLETE: 27 sessions, all 19 findings resolved; feature/data-asset-reconciliation merged to main; Cowork artifacts + tooling remediation cherry-picked at 45b049ad; worktrees MadhavDataAsset + Madhav(fix/ci-gate-cleanup) retired; branches deleted; 3 residuals documented; §E DAR bullet added; workstream count "Thirteen"→"Fourteen".

## v4.2 (2026-05-24, R11F-COMPLETE)

R11.F bounded agentic loop COMPLETE: merge 07e49964 + hotfixes 853c561e/2a4e3c55; all 5 R11E flags live =true; revision amjis-web-00390-csz; 10-min log watch clean; worktree MadhavR11FBound retired; branch chat-v2/r11f-agentic-loop deleted; residuals R11.F-RES-1/RES-2/RES-3 captured as CF.V13.5–7 in V1_3_AUDIT_QUEUE.

## v4.1 (2026-05-23, R11F-ARC-DECLARED)

R11.F bounded loop arc declared ACTIVE: 14-session plan authored, worktree MadhavR11FBound on chat-v2/r11f-agentic-loop pushed to origin; "Thirteen" → "Fourteen" concurrent workstreams.

## v4.0 (2026-05-23, R11G-COMPLETE)

R11.G COMPLETE: tool executor wired (executeMCPTool dispatches to MARSYS retrieval registry; all 5 provider gates real); SettingsDropdown ships (gear → 'Classic Marsys'/'Claude-style chat' radios; MultiProviderParityToggle deleted); NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY + NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL defaulted true in deploy.yml; PR #152 merge SHA 52e18cb5; production amjis-web-00367-b59; STREAM_R11V2_COMPLETE.md §8 added; CURRENT_STATE v5.53.

## v3.9 (2026-05-23, R11V2-DE-ROLLOUT)

R11 v2 D/E production flag rollout close-out: D.1 PASS, D.2 WAIVED, D.3 NOT_IMPLEMENTED (rolled back), E.1–E.4 NOT_IMPLEMENTED (not flipped); deploy.yml orphaned ADAPTERS_ENABLED renamed + D.1/D.2 baked; STREAM_R11V2_COMPLETE.md §7 added; ROLLOUT_PHASE_D/E_RESULT.md written; CURRENT_STATE v5.51.

## v3.8 (2026-05-22, R11V2-DISPATCH-WIRING)

R11 v2 COMPLETE: dispatch wiring shipped in PR #149; && false gate removed; real SDK calls in all 5 adapters; stubChat retired; build fixes: @supabase/supabase-js→pg (PR #150), Next.js 16 async params, ES2018 tsconfig target, bundle_adapters.js path; production revision amjis-web-00339-7nc; MARSYS_FLAG_R11V2_USE_ADAPTERS=true flipped in Cloud Run; STREAM_R11V2_COMPLETE.md §5 amended.

## v3.7 (2026-05-22, MCP-TRANSFORMATION-COMPLETE)

MCP Transformation COMPLETE: feature/mcpt-final merged to main; 17 sessions × 4 phases × 6 worktrees; 2,717 chart_facts rows, 4,589 rag_chunks, 573/573 MSR signals grounded, 21 MCP tools, 5 resources; 0 class-1 red-team findings; migrations 072–080 operator-pending; R11 v2 honesty amendment applied.

## v3.6 (2026-05-22, R11V2-COMPLETE)

Chat V2 R11 v2 Multi-Provider Parity (Claude Takeover) declared COMPLETE: 49 sessions across R11.A-E; 5 PRs #143/#144/#145/#146/#147 merged; 599 tests; capability adapter substrate + look-and-feel + streaming/thinking + caching + agentic loops across all 5 providers shipped.

## v3.5 (2026-05-22, MCP-TRANSFORMATION-DECLARED)

MCP Transformation declared as the 11th concurrent workstream; master plan + 7 session_queue YAMLs + 7 kickoff prompts + setup script under 00_ARCHITECTURE/CONDUCTOR/; 17 sub-phase briefs under 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_*; "Eleven" → "Thirteen" workstreams.

## v3.4 (2026-05-21, M5-COVERAGE-CAMPAIGN-COMPLETE)

M5 Coverage Campaign COMPLETE: 21 sessions shipped; DIS.013 sealed; RESOLVED artifact created; audit SUPERSEDED-AS-COMPLETE; v1.3 carry-forward queue created; "Nine" → "Ten" workstreams; CURRENT_STATE v5.36; SESSION_LOG appended; MP.1+MP.2 mirrors updated.

## v3.3 (2026-05-21, PR-111-REMEDIATION)

PR-111-REMEDIATION: 2 missing NEXT_PUBLIC R10 build-args added to cloudbuild.yaml; UI_REMEDIATION files relocated; CURRENT_STATE v5.29; SESSION_LOG appended; MP.2 mirror; CI investigation; PR #112 merged to main.

## v3.2 (2026-05-21, PHASE-4C-COMPLETE)

Phase 4C COMPLETE: post-merge operator steps closed; build_id `phase-4c-enrich-20260521-r2` populates `panchanga_daily` with 73,414 rows × full enrichment; FORENSIC-grounded spot-check at 1984-02-05 PASS 5/5; structural transit check PASS; Cloud Run `amjis-web-00258-9vq` + `amjis-sidecar-00224-4xs` live; worktree retired; open follow-up: bootstrap `build_manifests` auto-registration audit.

## v3.1 (2026-05-20, R10-COMPLETE)

R10 COMPLETE: PR #106 merged SHA 4dae9ed; all 21 sessions shipped; 566 unit tests green; R10 close-out complete — NEXT_PUBLIC_APP_URL build-arg, backfill script, pre-existing failures v1.1 baseline, Y-S5/Y-S9 queue marks; Phase 4C WAVE_1_COMPLETE PR #105 merged.

## v3.0 (2026-05-20, R10-PHASE-4C-MERGE)

R10 × Phase 4C merge resolution: chat-v2/round10 R10 governance setup COMPLETE + R10_MASTER_PLAN + 21 sub-briefs authored; Phase 4C Panchang + Conductor added as 8th/9th concurrent workstreams; "Seven" → "Nine"; R10 branch merged main post Phase-4C (PR #105).

## v2.9 (2026-05-20)

R10 governance setup + Phase 4C concurrent tracking.

## v2.8 (2026-05-20, R9-OPERATOR-CLOSEOUT)

R9 operator close-out COMPLETE: migrations 110/111/112 applied, all three R9 flags flipped and verified, routing fix b68f533 committed; backfill script not found — gap documented in BACKFILL_SCRIPT_NOT_FOUND.md.

## v2.7 (2026-05-20, R7-R8-R9-COMPLETE)

R7/R8/R9 all COMPLETE in §E; merge-train conductor session closed all three PRs #101/#102/#100 into main; worktrees retired.

## v2.6 (2026-05-20)

R7/R8/R9 declared ACTIVE; MERGE_TRAIN_ORDER authored.

## v2.5 (2026-05-18, §M.17)

Chat V2 Big Bang COMPLETE; sealing-merge `6c431f9` PR #82.

## v2.4 (2026-05-13)

M5 opened.

## v2.3 (2026-05-13)

Gate II.5 close.

## v2.2 (2026-05-11)

Pipeline-Transform-S1 close.

## v2.1 (2026-05-11)

Phase 11B — legacy code path deleted from route.ts; NEW_QUERY_PIPELINE_ENABLED flag retired.

## v2.0 (2026-04-24, STEP-9-CLAUDE-MD-REBUILD — initial install)

Full rebuild against the Step 9 brief. Section schema §A–§M installed per brief §3. Resolves GA.9 (LIFE_EVENT_LOG surfaced as concurrent workstream), GA.10 (GOVERNANCE_STACK surfaced via CANONICAL_ARTIFACTS import), GA.11 (supporting registries surfaced via import), GA.19 (§F currently-executing marker installed), GA.1/GA.2 (canonical paths imported from CANONICAL_ARTIFACTS_v1_0.md rather than duplicated inline). .geminirules mirror propagated in the same session per MP.1. BOOTSTRAP_HANDOFF reference retained as legacy orientation.

## v2.0 (amended in-place, 2026-04-24, STEP-15 — GOVERNANCE-BASELINE-CLOSE)

Rebuild-era banner removed from §F. §C item #8 rebuild-era qualifier replaced with steady-state CURRENT_STATE pointer. §D snapshot STEP_LEDGER row status updated to GOVERNANCE_CLOSED. §L rebuild-step-improvisation bullet removed (rebuild closed). PHASE_B_PLAN §C item #5 paused-note removed. §F narrative replaced with steady-state position. Footer updated. .geminirules MP.1 mirror propagated in the same session.

---

## v6.4 (2026-07-19) — RS-4 B.11 proportionality carve-out

§I B.11 bullet amended per native authorization (Cowork retrieval-strategy session): B.11 scoped to interpretive queries; pinpointed factual lookups (`depth: retrieval`) satisfy it via frame check (chart_header + session pin) + escalation valve (one-line flag + drill pointer when the fact touches an active contradiction, firing yoga, or open prediction window). §D snapshot CLAUDE row 6.2 → 6.4 (stale-row correction). Mirrors in-place amendments to `PROJECT_ARCHITECTURE_v2_2.md` §B.11/§H.4 (changelog entry 2026-07-19). Doctrine source: `RETRIEVAL_STRATEGY_v1_0.md` §3.6. Ruling id RS-4.

---

*Full changelog preserved verbatim from CLAUDE.md v6.0 realignment (2026-06-12). All prior entries are historical audit trail — do not edit. For current CLAUDE.md version and last 2–3 inline entries, see `CLAUDE.md` frontmatter.*
