---
artifact: REPORT_D-1.6
type: WAVE CLOSE REPORT
wave: D-1.6 "Śuddhi"
status: closed
brief_version_bound: 1.0 (BRIEF_D1_6.md, BOUND 2026-07-16 by Binder per BIND_D-1.6.md)
governing: CONDUCTOR_PROTOCOL.md v1.2
---

# D-1.6 "Śuddhi" — Wave Close Report

## Lanes

| Lane | Verdict | Receipt |
|---|---|---|
| S-1 (silent-wrong-answer purge) | ACCEPT (round 2/3) | Opus, scope_warden=pass; CR-42/R-19/R-20 filter-honesty fixes + 3 regression tests added on verifier request; CR-51/CR-30 alias unification; T-8 live muhurta citation; CR-47 non_discriminating flag; CR-55 and R-21/R-22/CR-63 confirmed already-fixed pre-wave |
| S-2 (dosha integrity) | ACCEPT | Opus, scope_warden=pass; fixed shared-stub constituent_facts_array (item d) + Kāla-Sarpa agreement receipt (item c); items a/b confirmed already-fixed pre-wave, verified live |
| S-3 (yoga engine integrity) | ACCEPT (high confidence) | Opus, scope_warden=pass, independently re-verified via live MCP + source read; Y-2/Y-10/Y-12 fixed; Y-3/4/5/6/11/13 confirmed already-shipped; Gate Ś items 5/6/7 confirmed green live pre-deploy |
| S-4 (timing substrate) | ACCEPT + fix-2 ACCEPT | Opus, scope_warden=pass both rounds; R-45 lord-resolution fallbacks (fabrication-safe, independently proven); CR-5/12/48 flat-0.5 fix; fix-2 root-caused and closed Gate Ś #9/#10 (tiered dasha-window selection, dated-rows-first ranking, timing-honesty guard) |
| S-5 (serving-quality debt) | ACCEPT (with caveats) | Opus, scope_warden=pass; aspects-facet routing fix (closes A7 PARK + S-4-sputa-drishti); 4 oversize tools budgeted; D15b-F3 alias fix; R-18 param-noop harness (263 params/0 flags); PARK-#4 correctly deferred (bucket-7 excluded scope) |
| S-6 (infra one-liners) | ACCEPT | Opus, scope_warden=pass; CR-40/T-1 kala_temporal_bundle dead-route fix; harness 429-retry fix; CI collection fix; migration 439 (independently reviewed safe); alias-conformance harness; O-2/O-8 staged, applied post-native-approval |
| S-8 (governance/register reconciliation) | ACCEPT | Opus, scope_warden=pass; CR-90..107 register debt closed with verified pointer table; MARSYS registers synced; R-48 honestly re-dispositioned; Binder-remit note added to protocol |

Lane S-7 (verify-then-close) was folded at Binder-open into S-5/S-8 per BIND_D-1.6.md — 13/16 probed items closed with live evidence at bind time, 3 residuals routed to their respective lanes.

## Parked / residual

- **Gate Ś item 8** (yoga_activation_by_dasha, signal_type_class='yoga' filter): PARKED with evidence. 74 rows on chart 482012f1, 0 dated, confirmed structurally different from the now-fixed DIGNITY/SUBSYSTEM classes — these are birth-moment/catalog facts (panchanga_yoga:*, panchanga_special_yoga_combinations:*, graha_yoga_karaka_flag:*, catalog yoga_label matches) lacking a real natal planetary constituent_lord to match against a forward dasha window. The general activation/window mechanism is proven working (Gate Ś #9/#10 both green with real evidence). Fixing this narrow residual requires new work in the yoga-signal-class's `dasha_eligibility_rule` construction — a fresh, bounded task for a future wave, not a same-session fix-3. The authoritative yoga-firing surface (`ganita_yoga_firings_get`, Gate Ś items 5/6/7) is unaffected — this residual only touches a secondary MSR-signal corroboration path.
- **PARK-#4** (5 residual `keyword_heuristic_v1` valence rows): correctly excluded per the brief's own scope_ruling (bucket-7 MSR valence internals) — not touched, not closed, routed to its dispositioned wave.
- **O-2/O-8 pause**: staged by S-6, applied this session after explicit native go-ahead (terraform apply for scheduler URI + header re-provision; Cloud Monitoring alert policy creation). No outstanding action.
- **Orchestrator state-commit race** (discovered during the D-1.6 rebuild, NOT a D-1.6 lane defect): a narrow-scope rebuild of `ka_yojaka`'s DAG closure hit a race where `ka_sangam`'s data write completed correctly (2,488 rows verified in `kala_convergence`) but its `asset_throughput.state` never transitioned to `'lit'`, tripping a DEP-ASSERT on a downstream sibling and cascading 24 BLOCKED errors. Recovered by verifying the underlying data was genuinely correct, manually correcting the stuck state flag, and resuming the remaining assets (all completed cleanly on resume). This is a pre-existing orchestrator-level defect (FROZEN per CLAUDE.md §N.2 — not touched), flagged here as the first agenda item for the next session/native review. It did not affect data correctness in the end, only wall-clock time.

## Gate Ś (16 items)

**Green (11):** #1 filter honesty (Saturn-only remedy query), #2 digest weakest_graha, #3 alias parity (identical result_hash), #4 dosha verdicts (Kemadruma/Kāla-Sarpa correctly absent, zero shared-stub), #5 yoga firings (Budha-Aditya/Saraswati/Dhana grounded), #6 NBRY (Saturn-D9/Venus-D9 grounded per DR-4), #7 v3 verdict honesty (Sasa correctly "formed"), #9 window families (post fix-2: real dated windows, activation_count=50), #10 receipt honesty (post fix-2: timing_anchored genuinely backed by evidence), #12 PARK-A7/#4 disposition, #13 infra (transit/rules/sidecar all live, no 401).

**Parked with evidence (1):** #8 (see above).

**Confirmed by construction (4):** #11 (oversize sweep — spot-checked during live testing, budget/trim discipline visibly active, no failures encountered), #14 (registers — S-8's reconciliation verified by its own Opus verifier), #15 (CURRENT_STATE/CLAUDECODE_BRIEF pointers — advanced at this close), #16 (full-battery sanity — effectively what this session's live testing constituted across both deploys).

## Deploy

- **Deploy 1** (all 7 original lanes): PR #578, merged `38d82105`, deploy run `29492213040` success. amjis-web + amjis-mcp live at `38d8210554807dfdc90aa797a7023fdca49465b9`.
- **Deploy 2** (S-4 fix-2): PR #580, merged `08245669`, deploy run `29499032988` success. amjis-web + amjis-mcp live at `0824566951a3189bc750e24d20eab650f5542fb4`.

## Rebuild

- **Rebuild 1**: scope-limited asset_set, 47 assets (true DAG closure of ga_structural/ga_yoga/ka_yojaka, the writers this wave's lanes changed), run `83949839-fff3-472f-bbb1-cbf6c3b1bb8a`. 47/47 lit, zero errors. Build-health: FORENSIC 7/7, DEFECT-001 0% orphaned, chart_facts growth (27,554→138,279) investigated and confirmed legitimate (zero duplicate rows, clean build_id separation — `ga_structural`'s correct combinatorial output, not an accumulation bug).
- **Rebuild 2** (post fix-2): scope-limited asset_set, 27 assets (ka_yojaka's own closure). Hit the orchestrator state-race documented above; recovered via one manual state correction + a resume run (`8a353d5d-032f-4c49-b0e1-66e3eed8d381`, 25/25 complete). Full 27-asset closure confirmed lit.

## Adjudications

- **DR-4** (Fable, doctrine): CR-23 NBRY doctrine grounds — recognized grounds G-a (dispositor-in-kendra) / G-b (exalted-in-sign) / G-c (exaltation-lord-in-kendra) / G-d (exalted-in-D9), G-e supporting-only; bhaṅga on any one ground; `raja_grade` ≥2 or dignified canceller; `grounds_jsonb` mandatory. Unblocked Lane S-3's Y-3 work.
- **DR-5** (Fable, doctrine): C-6 composed-rubric product boundary — option (a) with a bridge: grade per-instrument plus composition checks over existing composed instruments; un-servable synthesis items excluded from the D-4 floor with a boundary note; in-product orchestrating-LLM rejected as a campaign deliverable.
- **CR-28** (intent_classify prompt-vs-classification contract): routed to Opus engineering adjudication at Binder-open; not separately ruled this session — carried forward as an open item.

## Register updates

CR-90..107 reconciled (S-8, verified by its Opus verifier): `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` §A-§I+§M remains system-of-record for CR-1..89+CR-107; CR-90..106 formally SUPERSEDED with a live-verified pointer table into `DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §8` + doctrine-wave briefs — no dangling row range. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` synced against this wave's S-7 probe findings and R-48's honest re-disposition. §E CR-33..38 permanent-ID assignments recorded. Legacy M-series carry-forwards triaged (3 CLOSED-OBSOLETE, 2 KEEP-with-owner).

## Rollback pin (at wave open)

- amjis-web: `aa1bad9fa4822f388b8d6bb1c42728d176465632`
- amjis-mcp: `1a4b935f8cd59a4c63edfe2aeedf51e079d71005`
- Abhisek build state: D-1.5b-closed baseline (pre-D-1.6)

## Next-wave (D-2) bind notes

- The orchestrator state-commit race (documented above) should be the D-2 Binder's first-agenda item — it's a real, reproducible defect in the asset_throughput state-write path under narrow-scope concurrent rebuilds, independent of any wave's lane code.
- Gate Ś item 8's residual (yoga-signal-class dasha eligibility) is available as a bounded pickup item for D-2 or a dedicated MSR-timing pass — not urgent (the authoritative yoga-firing surface is unaffected), but should not be forgotten (tracked here + in MARSYS_DEFECT_GAP_REGISTER_v2_0.md).
- CR-28 (intent_classify contract) remains open for Opus engineering adjudication.
- D-2 (Vidhi Engine + Mechanism wave) opens onto a clean substrate per CLAUDECODE_BRIEF.md's wave_sequence.
