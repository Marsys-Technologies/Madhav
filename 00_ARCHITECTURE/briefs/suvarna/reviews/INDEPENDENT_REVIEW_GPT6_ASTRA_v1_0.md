# SUVARNA_INDEPENDENT_REVIEW_v1_0.md

## 1. Verdict

**DO NOT APPROVE**

Do not approve N-1 for unattended execution in the bundled state. The plan has corrected several earlier dependency problems, but the implementation still allows native gates to appear complete without authorization, relies on a permission boundary that agent-written code can bypass, contains contradictory launch requirements, and does not implement the promised Conductor supervision. Later-stage defects also remain in ELEVATED integration, frozen wave membership, foreign-key verification, and evidence validation. These are material under the campaign’s own earned-signal and authority requirements. Sources: `CLAUDE.md` §N.8; Charter §§2, 6, 8, 13; findings F1–F16 below.

This was a read-only, bundle-only review following the package’s reading order. I inspected the source and tests, parsed the plan graph and decision snapshot, recounted the register, and verified the manifest hashes. I did **not** run the test suite, launch the tracker, access credentials, query production, or use the network. The Q16 counterexamples are static code-path analyses, not executed exploits.

All **81 manifest-listed files** match their SHA-256 values. The manifest marks **80 clean** and the decision snapshot **not-in-git**; none is marked modified or untracked. This establishes the reviewed bundle’s integrity, not deployment or runtime correctness. Sources: `MANIFEST.txt`, header and file entries; `README_FIRST.md`, bundle provenance bullets.

Citation abbreviations used throughout:

- **S/** = `00_ARCHITECTURE/briefs/suvarna/`
- **T/** = `platform/scripts/governance/suvarna_tracker/`
- **Plan** = `S/SUVARNA_CAMPAIGN_PLAN_v1_4.md`, internal version 1.4.1
- **Charter** = `S/SUVARNA_AUTONOMY_CHARTER_v1_0.md`, internal version 1.4.1
- **Arch** = `S/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md`, internal version 1.4.1
- **Track E / Track A** = `S/tracks/TRACK_E_BRIEF_v1_0.md` / `TRACK_A_BRIEF_v1_0.md`
- **Runbook** = `S/SUVARNA_RUNBOOK_v1_0.md`
- **Runtime** = `S/runtime/INTERIM_RUNTIME_v1_0.md`
- **Model** = `00_ARCHITECTURE/control/suvarna/plan_model.json`, cited by item ID
- **Register** = `00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md`, internal version 2.8
- **Implementation plan** = `00_ARCHITECTURE/briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md`

Assessments and recommended changes below are reviewer judgments; cited statements about the bundle are evidence.

## 2. Findings table

| # | Severity | Where — file and section/function | Finding, with evidence | Recommended fix |
|---|---|---|---|---|
| **F1** | **BLOCKER** | `T/state.py::item_status`, `build_snapshot`; `T/events.py::validate`; Charter §§2, 6 | **Native gates can complete without an approving native decision.** With an authoritative log supplied but no matching ruling, `item_status` falls through to `elif last: out["status"] = last["state"]`; an ordinary `item` event can therefore mark FI-7 or J1.6 done. A logged `state:"decided"` also means done regardless of whether its detail refuses approval. `build_snapshot` records open prerequisites but does not prevent a done item from releasing dependents. | Make authorization gates require a typed affirmative outcome, the approved artifact revision, valid authority, and satisfied prerequisites. Reject item-event completion of decision gates. Add negative tests for refusal, revocation, absent decisions, forged item events, and prematurely recorded approval. |
| **F2** | **BLOCKER** | Arch §2.4; `T/runtime/settings.template.json::permissions`; `T/decisions.py::main`, `load_decisions`; `T/monitor.py::_isolation_measure`, `check_decision_writers` | **The proposed isolation does not protect all authority-bearing files or credentials from agent code.** Tests, governance scripts and TypeScript execution are allowed while lanes are editable. Those processes run as the user owning `pgenv.sh` and `builder.env`. File-tool denies do not constrain that code. Arch makes `run/` group-writable while protecting only the decision file; the Monitor checks file writability, not replacement through its parent. The hook code also resides in group-writable hq. `writer:"strategic-suvarna"` is self-declared. | Require N-25a and protect complete directory ancestry, executable controls and decision storage from the swarm. Run untrusted tests without credentials. Put credential use and privileged dispatch behind a separately owned broker with validated requests. Verify effective UID and filesystem permissions, including replacement attempts. |
| **F3** | **BLOCKER** | Runbook §2 steps 2a, 6; both start prompts §0; `T/monitor.py::Config.__post_init__`, `check_isolation`, `check_builder_scope`, `_safe_check`; Model E7.1–E7.3 | **Launch requirements contradict each other.** Default isolation checks demand that `cfg.pgenv` be unreadable, while the reader check must source it. After N-25, startup requires exit 0, but absent post-launch E7.2 provisioning makes `builder_scope` warn. Native credential directories are expanded relative to the running user’s home. Unexpected check exceptions become warnings although ordinary dispatch stops only on exit 2. | Define stage-specific required checks. Before N-1, require reader access and native-secret isolation while reporting builder provisioning as not yet applicable. Before builds, require builder scope and every safety check to pass. Pin native paths and UIDs explicitly; treat failure to measure a required safety check as blocking. |
| **F4** | **BLOCKER** | `T/hold_guard.py::main`, `evaluate`; `T/hold_guard.sh`, fallback classifier; `T/tests/test_hold_guard.py::test_main_malformed_stdin_exits_0_and_logs`, `test_wrapper_allows_malformed_stdin_when_guard_cannot_load`; Charter §8 | **The hold hook fails open and is not an enforceable production stop.** Malformed input deliberately returns 0. The fallback also permits malformed input or failure of its classifier. Dispatch recognition is a substring list; an allowed test or script can perform an equivalent action without those strings. Hold deletion protection recognizes only particular `rm`/`unlink` spellings. | Enforce hold state at the trusted dispatch endpoint, independently of the command text. Fail closed on unclassifiable protected calls. Make clearing the hold native-only at the storage/broker boundary. Exercise malformed payloads, unavailable interpreters, indirect dispatch and hold replacement. |
| **F5** | **BLOCKER** | `T/detectors.py::d_main_protected`, `_main_protected_from_rules`, `_main_protected_from_classic`, `_ruleset_bypass_actors`; Model L.16b; Arch §2.4 | **`main_protected` does not prove native-only merging.** One approving review suffices. Classic protection and rules without a `ruleset_id` return done with bypass explicitly unverified. Missing/malformed `bypass_actors` becomes an empty list. The model’s literal `native` is used as a GitHub login. Requiring native approval is also a different claim from forbidding the swarm from executing a merge after approval. | Pin the actual native and swarm identities. Verify all relevant rules and effective merge/update permissions. Unknown bypass policy must remain unknown. Demonstrate that the swarm cannot merge even an otherwise approved, passing throwaway PR. |
| **F6** | **BLOCKER** | Arch §§5.5, 12.8, 12.12; `T/monitor.py::_latest_conductor_heartbeat_ts`, `check_conductor_heartbeat`, `repair`; `T/lane_launch.py::check_refusal`, `launch` | **The unattended runtime lacks exclusive ownership and the promised supervision.** The Monitor checks the newest heartbeat from either `actor:"conductor"`; one healthy session can mask the other. Its repair function does not implement the described Conductor watchdog. The launcher has no queue claim, duplicate-process exclusion or cap enforcement and starts a process before recording its PID/event. | Before unattended launch, implement one fenced owner per queue, separate session heartbeats, idempotent lane launch, process reconciliation and interim stall/hold behavior. Require the durable supervised loop before B.W1, as planned. |
| **F7** | **MAJOR — before J1** | Track E §8; `T/detectors.py::_load_exact_elevated_assets_fn`, `d_levels_elevated`, `d_assets_elevated`; Model E6.3t | **The ELEVATED interface remains incompatible.** Track E pins `elevated_assets(ref, repo)`; both callers still invoke `elevated_fn(self.cfg)`. A conforming implementation will raise. E6.3t checks that the module and a test file exist, not that the running tracker calls the interface successfully. | Implement CODE-31 exactly and require an integration test through the real tracker caller at the approved commit. |
| **F8** | **MAJOR — before J1** | `T/detectors.py::d_levels_elevated`, `_family_assets_checked`, `_family_set_union`; Track E §8; Model B.W0–B.W5 | **Wave membership is still mutable.** `spec["level_map"]` is ignored; membership comes from the live registry DAG. Moving or deactivating an unfinished asset can reduce a wave’s denominator. Family-file validation checks key presence, not a correct union or approved population; an inflated exclusion list can hide unfinished assets. | Read the frozen map, validate exact population and family-set invariants, and require an authorized version transition for changes. Keep terminal dispositions visible rather than removing assets from the denominator. |
| **F9** | **MAJOR — before the first MSR rebuild** | `T/detectors.py::d_fk_no_cascade`; Model F3.FK; Register §2.14 R243; `S/l3_recon/SANGAM_RECON.md` §§3.2, 6.1 C2 | **F3.FK does not measure its stated target or rebuild safety.** It ignores `target`, queries only CASCADE/NO ACTION/RESTRICT, and therefore accepts SET NULL or SET DEFAULT keys for a `no_fk` target. Its separate `allow` parameter can approve restrictive keys. It does not test the independent `assert_l2_msr_delete_safe` guard identified in the recon. | Check every FK against the ruled target, remove the restrictive-key escape, and prove the complete delete/reinsert path with referencing rows present. Include the guard, generation/reference integrity and downstream effects in F-3 acceptance. |
| **F10** | **MAJOR — before J1** | `T/detectors.py::d_scorecard_pass`; Track E §5; Model E1.7, E3.6 | **A scorecard can be current-looking without current test results.** The detector validates the generator’s path/hash and an ancestral inspector commit, then trusts JSON PASS values. An old PASS survives a later inspector change if the generator is unchanged; fabricated results with correct public metadata also pass. Engine Build results are not validated by E1.7’s T1–T5 check. | Bind results to the exact inspector, registry, fixtures/data snapshot and test execution. Validate required populations and engine checks. Reproduce deterministic results or verify a protected CI attestation. |
| **F11** | **MAJOR — before J1** | `T/detectors.py::d_registry_coverage`, `d_main_has_files`, `d_main_file_contains`; Model E4.1c, E4.3, E5.1–E5.5, E6.3t; Plan §4.2 | **Several J1 predicates prove presence rather than the claimed behavior.** A coverage report with null revisions, `covered_cells:0` and an empty uncovered list returns done. Files named like tests prove neither execution nor success; a workflow text match need not be an executed CI step. E4.3’s file predicate does not prove cutover equality or the running ref change. | Validate schemas, counts and exact revisions; require successful test/CI artifacts and explicit cutover evidence. Separate “landed” from “accepted and running.” |
| **F12** | **MAJOR — before relying on detector completion** | `T/detectors.py::_fetch_main`, `_fetch_nikasha_ref_if_needed`, `poll`, `get`; `T/state.py::item_status` | **Failed refreshes can produce fresh-looking completion from stale data.** Fetch return codes are ignored and refresh timestamps advance even on failure. Cached results have no hard expiry in state evaluation while a replacement measurement is outstanding. | Record source commit, successful refresh time and maximum usable age. Failed refresh or expired evidence must block dependent action, not renew a previous PASS. Apply an overall deadline to detector execution. |
| **F13** | **MAJOR — before production dispatch** | Charter §6; Track E §§7–8; `T/detectors.py::d_wave_deployed`; `S/l3_recon/SANGAM_RECON.md` §1.3 | **Production dispatch checks are weaker than the authority promised.** `wave_deployed` checks a branch-name prefix and merge ancestry, but not base `main`, exact packet contents, writer hashes or serving deployment. The proposed builder can request canonical layer/asset scopes; exclusion of family assets is specified in the client wave script, not the server grant. Saṅgam also has outgoing cascades beyond the eight MSR FKs. | Enforce approved asset scope, family exclusions, hold, concurrency and execution revision at the server. Bind landing evidence to exact packet commits and both deployment components. Inventory the transitive write/delete footprint, not only direct writer tables. |
| **F14** | **MAJOR — before J1** | Plan §§1.1–1.4, 5.3–5.4; Arch §§6.2, 12.16; Track E §§7–8; Model B.FR.L3–L5, G3.L0–L5 | **Certification currency lacks a complete, convergent contract.** The documents name hashes and certification IDs but do not define canonical row hashing, global scope, nondeterministic fields, equivalent rebuilds, or a freshness watermark for invalidations. The pure ELEVATED function assumes invalidations are already in the ledger. Rebuilds and family changes can therefore cause repeated invalidation or temporarily stale PASS. | Define semantic fingerprints and certificate generations, a complete invalidation watermark, and a finite acceptance epoch with coordinated change windows. Reconcile family readers individually and order close rebuilds to avoid unnecessary downstream rework. |
| **F15** | **MAJOR — before the first L0 wave** | Plan §6.4b; Track E §7 E5.7; `S/reviews/FABLE_REVIEW_D1_D5_v1_0.md` D4 | **L0 recovery is not demonstrated, and retention ends too early.** Listing a dump and checking counts does not demonstrate successful restoration with dependencies and grants. Purging after a level certifies removes the recovery artifact before downstream and other-chart effects necessarily emerge. | Perform a restore and surgical-revert drill on an isolated database. Retain dumps, pre/post fingerprints and diffs through an agreed downstream validation and rollback window. |
| **F16** | **MAJOR — before J1** | Track E §7 E5.6, §8 E7; Plan §4.2 rows 6a, 15; Model E1.10, E5.6–E5.7; `T/events.py::validate` | **The rehearsal and runtime-proof route is incompletely specified.** Production builder scope is canonical-only, while rehearsal allows a scratch database or scratch chart. No separate provisioning/dispatch path is specified. A scratch chart alone does not isolate global L0 writes. Evidence events require only a nonempty evidence value. | Assign native ownership of an isolated rehearsal environment, identity and production-equivalent build image. Specify executable acceptance cases and validate their artifacts before J1. Historical production evidence must match the deployed fixes and required scenarios. |
| **F17** | **MAJOR — before promising unattended duration or completion dates** | Plan §§6.6–6.7; Arch §§3.3, 5.5, 12.8; Track E §9; Model decision gates | **Capacity, native availability and standing orchestration cost lack a usable operating model.** Hours omit review effort, native latency has no service commitment, and frequent large Conductor passes recur regardless of useful work. Launcher parameters do not enforce the stated concurrency or effort policy. | Publish stage throughput assumptions, native review windows, queue-age escalation and measured token usage. Trigger passes on actionable changes, with backoff. Reforecast after a small representative rehearsal and G2. |
| **F18** | **MINOR** | Track E §§6–7, 9; Runbook §2.6; Runtime §5; `S/SUVARNA_DOCUMENT_MAP_v1_0.md` §§1, 7–8; Register §1 | **Residual document drift remains.** E5 is 30–50 h in its heading but 40–65 h in the estimate; 31 listed clause fixes remain unreconciled with 32; 45 minutes is described as warning before a three-by-ten-minute threshold; the document map calls this rebuilt package stale. The inherited register freeze language is broader than the master checklist. | Reconcile the canonical counts and freeze rule, distinguish historical snapshots from current instructions, and generate operational summaries from the same machine-readable specification. |

## 3. Answers

### Q1 · Deadlocks

**The machine graph is acyclic, but the operational system is not presently executable as specified.** Parsing all 176 Model items found no cycles or dangling dependency IDs. That does not resolve the launch contradictions in F3 or the ELEVATED interface failure in F7. Source: Model `items`; `T/monitor.py::Config.__post_init__`, `check_builder_scope`; `T/detectors.py::d_levels_elevated`.

The complete J1 checklist maps as follows:

| Plan §4.2 row | Path and assessment |
|---|---|
| **1** | E4.1 and inspector work → E1.7 → J1.6. Structurally reachable; scorecard provenance is insufficient under F10. |
| **2** | E1 work → E1.8, closing R24 → J1.R/J1.6. A register state alone does not prove the required production L3 census. Sources: Model E1.8; Register §2.5 R24. |
| **3** | Engine landing, deployment and tests → E3.6, closing R39 → J1.6. Required engine Build evidence must be validated, not inferred from the row’s state. Sources: Model E3.6; Track E §3.2. |
| **4** | E2 agenda work → ordered tier re-seals → E2.2, closing R71 → J1.6. No graph cycle. Sources: Model E2.2, J1.1–J1.3. |
| **5** | E4.2 fix/test → E4.2r CLOSED/DONE or DEFERRED with withholding → J1.6. The former pre-J1 live-build cycle is removed. B.U owns later live closure. The withholding and merged-PR checks remain defeatable; see Q16. Sources: Plan §4.2, “R244 and the J1 loop”; Model E4.2r, B.U. |
| **6** | E1.8/E1.10/E2.2/E3.6/E4.2r → J1.R → J1.6. Expected rows are explicitly pinned. Sources: Model J1.R, J1.6. |
| **6a** | E3.2 + E3.3 + E3.7 → E1.10. Historical deployed evidence or isolated E5.6 work can avoid prohibited pre-J1 production rebuilding. Whether suitable history exists **cannot determine from the bundle**; the scratch execution route needs F16. Sources: Plan §4.2 row 6a; Track E §5 E1.10. |
| **7** | E2.1 + A.H → three N-4 agenda approvals; only N-5 re-seals remain ordered T1 → T2 → T3. No agenda-approval cycle. Sources: Model J1.1a–J1.3. |
| **8** | Re-sealed tiers → J1.4; A.L0v → J1.5. L0 revalidation precedes acceptance. Sources: Model J1.4, A.L0v, J1.5. |
| **9** | N-27/E0.1d → permission amendment E0.1; N-26/E3.2n follows the range decision; E3.2 → E3.3 → deployed E3.7. The intended ordering is sound, subject to pinning the actual migration numbers and PRs. Sources: Model E0.1d–E3.7; Track E §§3.3, 9. |
| **10** | E4.1 → E4.3. The old tools/ledgers cycle is removed: E4.1 no longer requires the ledgers. Cutover verification remains too weak under F11. Sources: Model E4.1, E4.1c, E4.3. |
| **11** | E5.1–E5.5 and E1.9 → J1.6. Their landing predicates do not establish tested operation. Sources: Model corresponding detector specifications; F11. |
| **12** | E6 registry/rollup/exact computation/re-key → E6.3–E6.5 → J1.6. Required per-asset detectors may remain pending without certifying assets; coverage and membership verification require F8/F11. Sources: Plan §2.1; Track E §8. |
| **13** | E7.1 → native E7.2 → E7.3 → E5.3, with L.10. This is a valid post-N-1 sequence, but startup’s all-green requirement makes it circular operationally. Sources: Model E7.1–E7.3; Runbook §2.6; F3. |
| **14** | A.L0 → J1.0d → N-24/J1.0. No graph cycle. Sources: Model J1.0d, J1.0. |
| **15** | E5.6/E5.7 → J1.6. Reachable once the isolated environment and evidence contract are supplied. Sources: Track E §7; F15/F16. |
| **16** | E6.3 → E6.3t → J1.6. The dependency is present, but file existence cannot detect the incompatible actual call. Sources: Model E6.3t; F7. |

L.16a correctly waits for L.16d/N-25. Its implementation still cannot satisfy the intended default reader/isolation combination. Source: Model L.16a; F3.

After J1, the model proceeds through revalidated briefs and instance acceptance → I.W0 → B.W0M → native L0 dispatches and F3.LOCK/F3.FK → B.W0 → G2. W1 additionally requires L.14; subsequent waves proceed through W5. Family certification and reader certification join the six layer closes; CL.1 → CL.2 → CL.3 implements G4/N-CLOSE. G2 is deliberately a checkpoint rather than a prerequisite for B.W1M. Sources: Model I.W0–CL.3; Plan §4.2.

Two qualifications remain:

- B.U is a prerequisite of **G3.L2**, not B.W2 itself. Correct withholding and exact ELEVATED must therefore prevent premature `bo_upaya` certification. Sources: Model B.U, B.W2, G3.L2.
- B.FR.L3–L5 each wait on all three families, despite “asset by asset” wording. N-21 does not remove B.FK from B.FR.L5. Sources: Model B.FR.L3–L5; Plan §5.3.

### Q2 · The first wave depends on others

It is safe to **wait**, but it makes G2 an expensive first demonstration. W0 already contains `bo_sudarshana` and `bo_vargottama_dhana`, so F-3 and the applied safety change are real prerequisites, not administrative obstacles. Sources: Plan §5.3 and Appendix A; Model B.W0, F3.LOCK, F3.FK.

There is no automatic fallback authority. If Saṅgam stalls, the native must arrange a bounded F-3 task, delegate it explicitly to another owner, or revise the campaign’s first demonstration. Suvarṇa cannot silently take the family’s work. Sources: Charter R1/R8; `run/DECISIONS.jsonl`, F-3 and N-17.

My recommendation is a small isolated end-to-end rehearsal followed, if useful, by a separately named production pilot containing no MSR writer or affected descendant. Moving the two writers out of W0 is acceptable only through an explicit revised dependency map and pilot definition; it must not make the existing G2 claim appear satisfied. Sources: Plan §4.2 G2; Track E §7 E5.6; F8/F9.

The question’s four L0 dispatches span **W0 and W1**. G2’s path includes three: B.L0.0–B.L0.2. B.L0.3 follows W1’s landing. Source: Model B.L0.0–B.L0.3, G2.

### Q3 · Estimates and calendar

The stated effort is approximately **617–1,812 agent-hours** for E + A + I/B, before launch work, reviews and family-session effort:

- E: 200–340.
- A: 157 + 130–250 + 30–65 = 317–472.
- I/B: 100–1,000, **already including** the 60–180 hours of semantic detectors.

Adding the separately estimated 30–55 launch hours gives **647–1,867 hours**. These are arithmetic combinations of estimates, not measured forecasts. Sources: Plan §6.6; Track E §9; Track A §11.

A realistic completion calendar **cannot determine from the bundle**. Productive agent throughput, packet counts, serialized build durations, review rework, family delivery dates and native response times are missing. The stated Kṣetra estimate alone is 5–9 weeks of its own work; it is not a guaranteed campaign completion bound. Sources: Plan §§5.3, 6.6; `S/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md`, Kṣetra effort section.

For planning, use:

`calendar = critical-path execution + serialized native waits + deployment waits + rework`

For illustration only, ten unbatchable native waits at one business day each add ten business days; at three days each they add thirty. This is sensitivity arithmetic, not a prediction. The plan needs committed review windows before a dated range is credible. Sources for the serialized acts: Track E §9; Model J1.1–J1.3 and wave landings.

The least defensible estimate is I/B’s tenfold range. E7’s 8–15 hours also deserves early re-estimation because its described scope includes authorization changes, provisioning, a credential wrapper and negative security tests. Sources: Plan §6.6; Track E §8 E7.

The required figure cross-checks yielded:

| Figure checked | Result and source |
|---|---|
| Active assets | 40 + 19 + 23 + 21 + 9 + 15 = **127**; consistent across Plan Appendix A, Track A §1 and review package §1. |
| Gate cells | 9 × 127 = **1,143**; consistent with Plan §1.4 and Model CL.1. |
| Kept assets | Layer breakdown totals **97**, versus 98 predecessor freezes; these are different measures. Sources: Plan §3.3; review-pass-1 consistency, “Checked and consistent.” |
| Register population | Recounted **252** row IDs. Source: Register §§2.1–2.15. |
| Register states | Recounted **180 OPEN, 51 CLOSED, 16 DONE, 2 CLOSED_ON_BRANCH, 2 PARTIAL, 1 MEASURED**; matches Register §0.1. |
| Open severities | Recounted **4/95/71/10**; sum 180. Source: Register §0.2 and rows. |
| Closed-class aggregate | **70** includes CLOSED_ON_BRANCH and MEASURED; it does not mean 70 fully runtime-proven closures. Sources: Register §0.1; R34/R36. |
| Wave populations | **65 + 13 + 14 + 17 + 9 + 9 = 127**, before family exclusions. Sources: Plan Appendix A; Model I.W0–I.W5. |
| L0 distribution | **24 + 11 + 4 + 1 = 40**; three dispatches before G2, four through W1. Sources: Plan §6.4b; Model B.L0.0–B.L0.3. |
| MSR exposure | Seven writers across W0/W1/W2; eight FK edges from seven tables are consistently reported. Current catalog state **cannot determine from the bundle**. Sources: Plan §5.3; pass-2 disposition, “Measured for this pass.” |
| Decision backlog | **68** modeled IDs; **21** decided in the snapshot; **47** not decided. The log has 26 records: 21 decided and five delegated. Sources: Model `decisions`; `run/DECISIONS.jsonl`. |
| Track E total | Components sum **198–340**, reasonably rounded to 200–340. E5’s heading remains **30–50**, while its total uses **40–65**. Source: Track E §§7, 9. |
| Pre-J1 merge count | Listed components sum **11–13**, not 11–14. E0.1 and the separately mentioned F-3 migration need explicit inclusion. Sources: Track E §9; Plan §6.6; Model E0.1. |
| Clause fixes | **31 listed versus 32 claimed** remains explicitly unresolved. Sources: Track E §6; Plan §3.6. |
| Asset briefs | 127 minus five family assets = **122** authored briefs; literal 1–2 hours each is 122–244, rounded to 130–250. Sources: Plan §5.2; Track A §§1, 11. |
| J1 checklist | Numbering is 1–16 **plus 6a: 17 entries**. Source: Plan §4.2. |
| 799 gaps / zero certificates | Cross-document assertions agree, but the ledgers are deliberately excluded; independent recount **cannot determine from the bundle**. Sources: Plan §1.4; review package §3 exclusions. |

### Q4 · The native as bottleneck

Tracing G2’s transitive prerequisites yields **27 decision-backed items**, five already decided and **22 unresolved**, including N-1, N-25, N-27, N-26, N-22, four non-L0 instance acceptances, F-3, N-24, three agenda approvals, three re-seals, two N-7 acceptances, N-8, N-12, N-14.R236 and N-9. Sources: Model G2 dependency closure; `run/DECISIONS.jsonl`.

The remaining work also includes:

| Act | Count or qualification |
|---|---|
| Engine landing merges | Listed components imply **11–13**, subject to grouping. Source: Track E §9. |
| Additional named merges | E0.1 amendment and F-3 migration are not clearly included above; W0 requires another landing. Sources: Model E0.1, B.W0M; Plan §6.6. |
| Native L0 dispatches through G2 | **3**, not four. Source: Model B.L0.0–B.L0.2. |
| Family correction relays | **3** sessions. Source: `S/prompts/L3_FAMILY_CORRECTION_NOTICE_2026-09-29.md`, relay instructions. |
| Provisioning and operation | OS/GitHub isolation, builder account/grant/credentials, startup, tooling restarts and incident attendance. Exact action count **cannot determine from the bundle**. Sources: Runbook §2; Track E §§8–9. |

Under the stated merge grouping, that is **42–44 countable rulings, merges, dispatches and family relays**, plus provisioning and operational acts. It is a lower-bound inventory, not a precise count of clicks or attendance sessions. Additional applicability/addition decisions may also be needed by particular briefs. Sources: preceding inventory; Plan §§2.1, 2.3.

Steward batching helps, but “lead time” is not a capacity reservation. Delegate evidence assembly, routine brief acceptance under bounded G16, and mechanical verification. Keep authority changes, production credentials, destructive/global actions, standard revisions and final acceptance with the native unless explicitly re-delegated. Sources: Charter §§3–7; F17.

### Q5 · Walking the chain

There is no convergence argument. E5.5 may invalidate descendants whenever upstream inputs change, while family sessions remain independently active. Full-layer close rebuilds add further opportunities for changes to certification IDs or fingerprints. Sources: Arch §6.2; Plan §§1.1–1.2, 5.3; Track E §7 E5.5.

Require a versioned acceptance epoch with fixed asset population, standard revision and semantic input generations; short coordinated change windows; bounded retries; and explicit ownership of rework. An output-equivalent rebuild should not invalidate descendants merely because an attempt ID or timestamp changed. Material changes should invalidate them. These are recommended amendments to F14, not properties already demonstrated.

### Q6 · Forged or stale decisions

**Yes. Without N-25a, a swarm process can append a valid-looking decision using the native user’s filesystem authority.** Denying the named CLI does not deny writes through an allowed test or script. `decision_writers` proves only that the latest accepted `decided` records contain the expected string; it does not authenticate their author, native presence or artifact scope. Sources: `T/decisions.py::main`, `load_decisions`; `T/monitor.py::check_decision_writers`; F2.

The N-25 classifier now requires explicit `outcome=yes` or `outcome=no` markers and treats absent/conflicting markers as unclear. That is better than searching ordinary affirmative words, but a marker inside prose remains an untyped control input. It also cannot independently represent the package’s N-25a/N-25b split. Sources: `T/monitor.py::_classify_n25_outcome`; review package §2.

Other unsafe interpretation points include:

- `decided` becoming approval regardless of the ruling’s substance.
- Register state text becoming completion.
- Note-prefix matching becoming a family acknowledgment.
- A nonempty evidence string becoming event completion.

Sources: `T/state.py::item_status`; `T/detectors.py::classify_state`, `d_register_rows_state`, `d_acks_from`; `T/events.py::validate`.

Malformed decision lines are skipped, so an unreadable newer revocation can leave an older decision effective. Require corruption to block authorization evaluation and use typed outcomes, scope, revision and supersession. Source: `T/decisions.py::load_decisions`; F1/F2.

### Q7 · Production writes

The bundle describes or exposes these paths:

| Path | Boundary and remaining concern |
|---|---|
| Native merge followed by deployment/migrations | Intended production path; requires effective native-only merge policy and verified deployment contents. Sources: Plan §6.4; F5/F13. |
| Builder calls to cockpit runs | Intended non-clearing canonical builds; production code and tests implementing the grant are absent. Sources: Track E §8 E7; F16. |
| Native L0 dispatch | Authorized global change after snapshot and scope ruling; affects more than the canonical chart. Source: Plan §6.4b. |
| Pre-cutover fold push | Changes the register/ledger evidence later consumed by gates and cutover; it is not itself proof of an application deployment. Source: Arch §§12.7, 12.13. |
| Certification, gap and registry changes | Can change whether later production actions are permitted. Their integrity is operationally consequential. Sources: Plan §§1.1, 2.1; Track E §§7–8. |
| Allowed arbitrary code | Can use whatever credentials and filesystem authority the process possesses, bypassing tool-name restrictions. Actual current production reach **cannot determine from the bundle**. Source: F2. |
| Indirect effects of normal rebuilds | Deletes, triggers, cascades, shared-table writes and global-reference changes can exceed the directly named asset. Sources: Register R243/R244; Saṅgam recon §1.3; Plan §6.4b. |

The E7 grant is usefully narrower than super-admin, but **canonical chart + no clear_before is not sufficient** to enforce the charter’s family, packet and hold boundaries. The server must reject prohibited asset lists and indirect expansion, including scope aliases and dependency inclusion. Sources: Track E §8; Charter R8 and §6.

The planned 403 tests are necessary but incomplete. Add family/L0 assets supplied through every scope, disabled/revoked identity, concurrent requests, stale approval, duplicate dispatch and indirect destructive-effect cases. These are recommendations addressing F13/F16.

### Q8 · Credentials

**Yes, the allowed forms permit arbitrary code under the credential-owning user.** A test file or governance script can read a file even when the model’s `Read` tool is denied. TypeScript execution adds another route. The reader-form prefix does not validate the actual SQL/client command content or all client-side execution capabilities. Sources: `T/runtime/settings.template.json::permissions.allow/deny`; Arch §2.4.

N-25a materially reduces access to the native’s credentials if filesystem isolation is correct. It does **not** protect the swarm-owned reader/builder secrets from swarm-owned code. Declining N-25a makes the exposure wider because the native’s own credentials and decision-writing authority share the process identity. Sources: Arch §2.4; Runbook §2.2a; F2.

Whether network exfiltration is blocked **cannot determine from the bundle**; no enforced network policy is supplied. The safe design is credential-free test execution plus a separately owned, narrow credential broker.

### Q9 · Limits of the permission model

The bundle does not establish “allow exactly these forms, deny the rest” as a security boundary. It explicitly says project permissions still merge, while allowed interpreters can execute agent-controlled code. Sources: Arch §2.4; `T/runtime/settings.template.json::_meta`, `permissions`.

The template also conflicts with its own documented prefix semantics: several denies and the `pg_dump -Fc * -f …/*` rule contain multiple wildcards. Its own allow list lacks the documented reader-wrapped dump and Engine fold-push forms. Whether inherited rules happen to permit them **cannot determine from the bundle** without effective settings and CLI integration results. Sources: template `_meta.findings_v2_1_239`, `permissions`; Runbook §2.9; Arch §12.7.

The hold hook does not fail closed; F4 identifies both the code and tests preserving that behavior. Role separation, approved write sets, effort selection and many dispatch preconditions remain prompt obligations rather than enforced capabilities. Sources: `T/lane_launch.py::launch`, `build_argv`; Charter §§3, 6; Arch §3.

### Q10 · The family boundary

**Yes, permitted-looking actions can still affect family data.**

- The MSR cascade is only one coupling; F3.FK does not inspect the separate deletion guard or outgoing Saṅgam cascades.
- Global L0 changes can alter family inputs.
- The proposed build grant does not itself exclude family assets from a layer/list request.
- Coordination leases do not serialize transactions or deployments.

Sources: Plan §§5.3, 6.4b; Track E §8; Register R243; Saṅgam recon §§1.3, 3.2; Arch §12.4.

Conversely, a family rebuild can delete non-family dependent rows: the recon identifies CASCADE edges from `kala_convergence` to `phala_anchors`, `kala_darshana` and `kala_obstruction`, plus SET NULL to `kala_bhavishya`. These are beyond the eight MSR incoming keys. Source: Saṅgam recon §1.3.

Whether E5.5 would detect every such change promptly **cannot determine from the bundle**. Its implementation, complete runtime dependency map and polling/transaction contract are absent. The pure ELEVATED interface assumes invalidations have already been written. Sources: Track E §§7–8; F14.

### Q11 · L0 is global

The proposed safeguards are a good minimum, but insufficient for unattended acceptance. Native dispatch, impact reporting and a dump do not establish a tested recovery path or consistency for the other charts. Sources: Plan §6.4b; F15.

The bundle reports roughly 1.08 GB across 37 L0 tables and identifies two other charts with L1+ rows. Those are reported measurements, not a verified current dump size or current user-impact inventory. Current values **cannot determine from the bundle**. Sources: Fable review D4; Plan §6.4b.

Purging after level certification is premature. Retain a rolling recovery chain through downstream canaries, affected-chart checks and an explicit rollback window. Require a restore drill, a surgical-revert drill, and a policy for serving stale derived data. D6 dump-readability must be proven by E5.7 before any L0 wave. Sources: Track E §7 E5.7; Plan §6.4b.

### Q12 · Isolation from other workstreams

The local census `flock` enforces mutual exclusion **among processes that use the same lock**. It does not force other sessions to use it, and loss of the parent lock-holder can release it while its child remains active. Coordination-branch leases are an agreement, not database enforcement. Sources: `T/census_lock.py::acquire`, `run_locked`; Arch §§12.4, 12.15.

The hq lock serializes commits, not the entire queue read/claim/dispatch/update transaction. The orchestrator’s per-chart database lock is described, but its implementation is not supplied; current enforcement **cannot determine from the bundle**. Sources: `T/hq_commit.py`; Arch §§3.3, 12.12; F6.

An unrelated later deployment should pass an ancestry test if it contains the accepted work. A later overwrite must fail a writer-hash check. The charter correctly requires both, but `wave_deployed` implements only the ancestry portion. Even a correct preflight has a check-to-dispatch race unless the executing image/revision is pinned or revalidated at execution. Sources: Charter §6.4; `T/detectors.py::d_wave_deployed`; F13.

### Q13 · Nine gates, real detectors

The inspector and actual E6 implementation are not bundled, so whether every proposed detector will exist and pass at J1 **cannot determine from the bundle**. The plan’s intended coverage is:

| Gate | Assessment |
|---|---|
| **Ldgr** | Citation presence and build receipts are falsifiable structural checks, but do not prove every derived value’s lineage. L2+ constituent resolution is stronger; value-level attribution still needs asset-specific coverage. Sources: Plan §2.1; Track E §8. |
| **Idem** | Writer-pattern checks need exercised rebuilds and FK/guard checks. R243/R244 demonstrate why syntactic delete/insert recognition is insufficient. Sources: Register §2.14; Track E §5. |
| **Earn** | Literal lint and build evidence can fail, but the tracker itself violates this gate through F1/F10/F11. Sources: Track E §8; `CLAUDE.md` §N.8. |
| **Null** | Planned default, AST and constant-column checks detect some defects; constant values alone must not earn PASS. Semantic inability-to-derive cases and declared reasons need asset tests. Sources: Plan §2.1; Track E §8. |
| **Vocab** | Closed-vocabulary membership can be mechanically falsified. Completeness of the vocabulary and all output paths **cannot determine from the bundle**. Sources: Plan §2.1; review package §3 exclusions. |
| **Carr** | Generic presence/verification checks are not full faithful-source reproduction. Required per-asset correspondence detectors remain necessary. Sources: Plan §2.1; Track E §8. |
| **Narr** | Existing lint concepts plus golden tests can fail. Lints alone cannot prove text restates cited facts faithfully. Sources: `CLAUDE.md` §N.7; Track E §8. |
| **Dens** | Explicitly structural: contract plus a tier/confidence field in a served SELECT. It does not prove downstream presentation preserves distinctions. Sources: Track E §8; Fable review D3 residual risks. |
| **Build** | Needs a real orchestrator run with the required substeps and correct output evidence. File existence, registration or a hand-run cutover cannot substitute. Sources: Plan §2.1; `S/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §7. |

“Required, per-asset detector pending” is sound **only as an explicit NO_DETECTOR block on ELEVATED**. J1 may freeze a measurement framework before every asset’s semantic detector exists, but must not present that framework as universal semantic coverage. Sources: Plan §§1.4, 2.1; F11.

### Q14 · ELEVATED and “current”

ELEVATED is a useful high-level definition, but not yet an unambiguous executable contract. Missing details include stable row ordering, natural-key serialization, global scope, volatile columns, stochastic outputs, evidence freshness and authorization of terminal dispositions. Sources: Plan §1.1; Arch §12.16; Track E §§7–8; F14.

An idempotent rebuild may change timestamps, attempt IDs or surrogate references without changing meaning. Conversely, ignoring too many fields can conceal a material change. Each asset needs an explicit semantic fingerprint contract. Embeddings need a declared reproducibility/equivalence policy; the bundle does not supply one. Source: Arch §12.16; Track E §7 E5.5.

The pure `elevated_assets(ref, repo)` interface is appropriate for reproducible ledger evaluation. It cannot independently establish live currency because its contract forbids database reads and assumes E5.5 invalidations are already present. Add a validated measurement manifest/watermark and keep operational freshness separate from pure historical evaluation. Source: Track E §8.

The actual tracker must first adopt that interface; it currently does not. Source: F7.

### Q15 · N/A policy

A registry rule can become a blanket waiver if applicability is defined too broadly or changed without comparing affected cells. Native approval and versioning are specified, but the bundled coverage detector checks neither approval nor a meaningful revision binding. Sources: Plan §2.1; `T/detectors.py::d_registry_coverage`; F11.

Require exact rule IDs, affected populations, reasons, approval references and tests showing neighboring applicable cases remain required. N-14.R236 should name `lel_events` explicitly rather than create a general “missing writer means N/A” escape. Sources: Register R236; review package §2.

D3’s separation of non-gate criteria is defensible: informational Cost/Count/Complete/Reach rows need not block a fixed nine-gate standard. But a completeness or reachability defect that violates a core gate or declared addition must still block under that criterion. Moving its label must not erase the substantive obligation. Sources: Plan §§1.1, 2.3; `run/DECISIONS.jsonl`, D3.

### Q16 · Earned signals in the tracker

All requested detector families have a static false-completion route or an integration defect. None of the following was executed against live state.

| Detector | Counterexample derived from bundled code |
|---|---|
| **`scorecard_pass`** | Commit JSON containing the correct pinned generator path/hash, an ancestral inspector SHA and PASS objects. The function does not verify that the tests ran. Later change the inspector while leaving the generator unchanged: the old inspector remains an ancestor, so the old PASS still qualifies. Source: `T/detectors.py::d_scorecard_pass`; F10. |
| **`register_rows_state` with DEFERRED** | A withholding object containing `{"bo_upaya-Idem.pattern": false}` satisfies `entry in data`. Pair it with a DEFERRED row and a PR reported MERGED; neither active withholding semantics nor merge base/content is checked. CLOSED/DONE bypass those extra checks altogether. Source: `T/detectors.py::_withholding_has_entry`, `d_register_rows_state`. |
| **`fk_no_cascade`** | Retype keys to SET NULL or SET DEFAULT while Model F3.FK still requires `target:"no_fk"`. The query filters those keys out, sees no offending rows and returns done. A separate `allow:"no_fk"` also permits restrictive keys. Source: `T/detectors.py::d_fk_no_cascade`; F9. |
| **`wave_deployed`** | Supply a merged PR with a matching head prefix and a merge commit ancestral to the job image, although the packet is incomplete or a later commit reverted its writers. Base branch, packet contents and writer hashes are not checked. Prefix matching also accepts a wave-like name such as `suvarna/land/B.W01…` for B.W0. Source: `T/detectors.py::d_wave_deployed`; F13. |
| **`levels_elevated`** | Once callable, remove or move an unfinished asset out of the live wave range while leaving one completed asset inside; the denominator shrinks and can report done. The supplied frozen-map path is ignored. Inflating `family_set` is another exclusion route. Source: `T/detectors.py::d_levels_elevated`, `_family_set_union`; F8. |
| **`assets_elevated`** | Supply a nonempty named family list containing only completed members while omitting an unfinished required member. Validation checks required keys, not the approved membership. Separately, the specified two-argument E6.3 implementation raises under the current one-argument call. Sources: `T/detectors.py::_family_assets_checked`, `d_assets_elevated`; F7/F8. |
| **`main_protected`** | Return classic protection requiring one approval while bypass remains unverified, or a ruleset rule without `ruleset_id`; both return done. The latter behavior is explicitly tested. Sources: `T/detectors.py::_main_protected_from_classic`, `_main_protected_from_rules`; `T/tests/test_detectors_v13.py::test_main_protected_ruleset_with_no_ruleset_id_is_done_unbypass_unchecked`. |
| **`acks_from`** | Append three notes with the required self-declared actor names and details starting `ACK FI-8`. Old acknowledgments and even a prefix such as `ACK FI-80` qualify. There is no binding to correction-notice v1.2, prompt v1.3, an authenticated session or an acknowledgment deadline. Sources: `T/detectors.py::d_acks_from`; Model FI-8; pass-3 disposition §5. |

These findings do not negate fixes that landed: the scorecard generator pin is now checked, missing coverage keys error, absent exact ELEVATED does not fall back to the old completion proxy, and merge ancestry replaces substring equality. The remaining counterexamples attack what those fixes still fail to prove. Source: the corresponding functions in `T/detectors.py`; pass-3 disposition §3 CODE-24, CODE-29–33.

### Q17 · Parallelism, spend and review load

At a ten-minute cadence, two Conductors produce **288 passes/day**. At the architecture’s 50–100k input tokens/pass, standing reread volume is **14.4–28.8 million input tokens/day**, or **100.8–201.6 million/week**, excluding outputs and all worker/reviewer activity. Sources: Arch §5.5; Plan §6.7. These are arithmetic volumes, not billable uncached-token estimates.

Actual money cost **cannot determine from the bundle**: prices, cache hit rates, measured pass sizes, subscription limits and N-23’s choice are absent. N-15 removes ceilings, not the obligation to report spend. Source: `run/DECISIONS.jsonl`, N-15; Arch §12.8.

My assessment is that the standing loop is inefficient without change detection and backoff. Use a deterministic readiness check to invoke a Conductor only when work, decisions or failures change. Keep periodic health checks scripted. Batch mechanical evidence review while retaining independent review for writer, ledger, authorization, algorithm and standard changes. Sources for current roles/review policy: Arch §§3.1–3.3; Plan §6.3.

Concurrency should be governed by measured reviewer and census throughput, not just available worker slots. The current launcher neither enforces caps nor applies the supplied effort value to the CLI. Source: `T/lane_launch.py::launch`, `build_argv`; F6/F17.

### Q18 · Wave granularity

Per-level execution is appropriate for dependency safety. A single W0 landing covering a gross 65 assets is a large first integration batch, especially before per-asset cost and rollback behavior are measured. Sources: Plan Appendix A; Arch §6.2; Model B.W0M.

Keep logical waves for reporting, but allow smaller dependency-closed landing groups within a wave, each with exact commits and evidence. Preserve per-level dispatch and upstream certification. A small rehearsal should determine the practical batch size; neither “always one PR per wave” nor “one PR per asset” is justified by measured throughput yet. Sources: Plan §§5.4, 6.6; Track E §7 E5.6.

The native’s three W0 L0 dispatches cannot all occur before intervening prerequisite certification. Batching their preparation reduces attendance overhead but does not eliminate the ordering. Sources: Plan §6.4b; Charter §6.6.

### Q19 · Failure modes

| Failure | Bundled handling and gap |
|---|---|
| Two Conductors on one queue | No whole-pass exclusion or atomic claim. A commit lock alone is insufficient. Sources: `T/hq_commit.py`; `T/lane_launch.py::launch`; F6. |
| Stale hq lock | An ordinary exited lock-holder releases `flock`; a live hung process can retain it. The lock file’s existence is not ownership. Source: `T/hq_commit.py`, lock acquisition/release. |
| Torn event write | Single append plus fsync is useful, and readers retain incomplete tails. Short writes are not checked; malformed complete lines are skipped. Source: `T/events.py::append`, `EventLog.refresh`. |
| Event rotation between passes | Stateful `EventLog` tracks inode; `read_since_offset` does not. Replacement by a larger file can skip its initial events. Source: `T/events.py::read_since_offset`. |
| Lane dies after pushing | Reconciliation of remote commits with queue state is left to the Conductor; launch records are not an idempotent transaction. Sources: `S/roles/ROLE_CONDUCTOR_v1_0.md`, pass/failure handling; `T/lane_launch.py::launch`. |
| Lane ignores its role | Role/model strings are not capabilities; allowed code retains process authority. Sources: template permissions; F2/F6. |
| Clock/timezone skew | Heartbeat selection compares timestamp strings, and future timestamps can remain healthy. No monotonic receipt-time freshness proof exists. Source: `T/monitor.py::_latest_conductor_heartbeat_ts`, `check_conductor_heartbeat`. |
| Context rollover mid-fold | Commit-per-pass is specified, but no transaction spans fold, push, event and queue checkpoint. Sources: Arch §§5.5, 12.7, 12.12. |
| One Conductor dies | A healthy heartbeat from the other can mask it; the promised watchdog is absent from `repair`. Source: F6. |
| Usage limit | Wait rather than restart-loop is specified, but implemented classification/recovery **cannot determine from the bundle**. Sources: Arch §5.5; `T/monitor.py::repair`. |
| Mac loss/sleep/reboot | Power checks and caffeinate help; off-machine recovery and reconstruction evidence are not supplied. Sources: Runbook §§5–6; review package §3 exclusions. |

A single Mac can be acceptable as a **recoverable scheduling host**, provided production rejects unsafe requests independently and durable state survives host loss. Those properties are not established here. This is my assessment under F2/F4/F6.

### Q20 · Before launch

Ranked requirements:

1. **Enforced authority and credential boundaries:** negative tests under the actual swarm identity, including decision-file replacement and approved-PR merge attempts. Sources: F1–F5.
2. **Whole-swarm sandbox rehearsal:** concurrent Conductors, malicious/malformed inputs, indirect command execution, hold, process death and recovery. Sources: F4/F6/F16.
3. **A committed, independently tested control release:** real CLI permission integration, not only string-membership/unit fixtures. Sources: template `_meta`; `T/tests/test_hold_guard.py`; F7–F12.
4. **Machine-enforced later-stage entry criteria:** exact J1 tests, builder scope, F-3 proof, immutable populations and current certificates. Sources: Plan §4.2; F7–F14.
5. **Recovery and operational evidence:** restore drill, canaries, retention, native response windows, separate session health and measured spend alerts. Sources: F6/F15/F17.

The first three are N-1 requirements. Production build, restore and certification acceptance work may remain post-N-1 only behind effective, testable stage gates.

### Q21 · Single biggest risk

**The largest risk is an unearned green status becoming permission for autonomous action.** The campaign is intended to replace weak verification, yet ordinary events, self-reported verdicts and file presence can still satisfy critical completion paths. Sources: Plan §§1.1, 4.2; `CLAUDE.md` §N.8; F1/F10/F11.

The cheapest high-impact change is one centralized, fail-closed gate evaluator: an authorization gate is satisfied only by a valid affirmative decision for the exact revision, satisfied prerequisites and current required evidence. Start with the F1 negative cases. This would not replace OS or server enforcement, but would remove a broad class of premature progression.

### Q22 · Open native decisions

| Decision | Judgment, reason and cost of a wrong decision |
|---|---|
| **N-25a** | **Agree; require it for unattended execution.** Shared native UID collapses the credential and decision boundary. Separate users still need protected directories and credential-free test execution. A wrong “no” has the widest potential authority exposure. Sources: Arch §2.4; F2. |
| **N-25b** | **Agree, with stronger acceptance tests.** Separate GitHub identity, secret-file hardening and effective native-only merge policy are necessary. Review-count checks alone are insufficient. Wrong implementation permits unintended production deployment. Sources: Runbook §2.2a; F5. |
| **N-26** | **Agree to renumber if still unapplied.** Reverify that fact and pin the new numbers consistently. Current applicability **cannot determine from the bundle** beyond the supplied snapshot. Wrong handling risks collision or editing applied migrations. Sources: Track E §3.3; pass-3 disposition, “Measured for this pass”; `CLAUDE.md` §N.4. |
| **N-27** | **Agree to a reserved range; condition the permission amendment.** The supplied scan supports 1200–1299 at its recorded time, not indefinitely. The proposed global deny change opens 12xx for repository sessions generally; pair it with ownership/reservation checks. Wrong scoping risks collisions and broader migration authority. Sources: pass-3 disposition §4; Arch §12.5. |
| **N-14.R236** | **Agree conditionally to the explicit no-writer classification.** The asset’s intended source and consumer contract must justify it. Do not generalize missing writers into automatic Build/Idem N/A. Wrong classification hides missing functionality while allowing W0 completion. Sources: Register R236; Plan §5.4 L5 row. |
| **F-3** | **Agree that cascades must be removed before MSR rebuilding; do not approve “drop all keys” as a complete safety proof.** Resolve the independent guard, reference lifetimes and downstream integrity. Wrong implementation can either block rebuilding or preserve dangling references and stale family data. Sources: F9; Saṅgam recon §§3.2, 6.1 C2. |
| **N-23** | **No unconditional billing recommendation is supportable.** Meter representative passes first. Prefer the mode that meets the agreed unattended availability requirement with observable cost and tested limit handling. Current prices and entitlements **cannot determine from the bundle**. Wrong choice causes either recurring pauses or poorly observed spend. Sources: Plan §6.7; Arch §5.5; Q17. |
| **G16** | **Agree with bounded delegation.** Require an exact approved class/revision, traceable acceptance and no discretion to waive gates or change outputs. This removes routine native load; a wrong implementation launders scope changes through brief approval. Sources: Charter G16; Plan §5.4 step 1; Track A §10. |
| **N-4.T1–T3** | **Agree with batching presentation and agenda approval, not blanket approval of unseen text.** Preserve separate signed agenda versions and ordered re-seals. Actual agenda adequacy **cannot determine from the bundle**. Wrong approval propagates an inconsistent standard across every asset. Sources: Track E §6; Model J1.1a–J1.3. |

**N-25a decided wrongly has the greatest authority risk.** F-3 decided wrongly has the most immediate identified data-plane integrity risk. Sources: Arch §2.4; Register R243; Saṅgam recon §3.2.

## 4. Conditions for launch

Before the native approves N-1:

1. **Authorization gates pass negative tests** for absent/refused/revoked decisions, forged item events, wrong artifact revisions and unmet prerequisites. No such case may release dependent work. Sources: F1; Charter §§2, 6.
2. **The actual swarm identity cannot alter native authority or control code**, including replacing the decision log through its parent directory, changing the hook, or reading native secrets. Untrusted tests must not receive builder credentials. Source: F2.
3. **The launch check matrix is stage-aware and executable:** reader access and isolation pass together; unavailable post-launch builder provisioning cannot deadlock launch; failure to measure a required safety property blocks the relevant action. Source: F3.
4. **Hold enforcement passes an end-to-end negative test**, including malformed hook input, indirect script dispatch, unavailable hook dependencies and attempted hold removal. The trusted dispatch boundary must refuse new protected actions. Source: F4.
5. **GitHub refuses the swarm’s merge/update attempts**, including a passing PR already approved by the native. Evidence must identify actual actors and effective rules, with no unverified bypass accepted as done. Source: F5.
6. **The interim runtime proves exclusive queue ownership and recoverable launch**, with separate Conductor heartbeats, duplicate-launch refusal, crash reconciliation and tested stall/hold behavior. Durable runtime remains an enforced B.W1 prerequisite. Source: F6.
7. **A pinned control release passes an independent regression and real-CLI integration run.** Record the exact code/settings/model hashes and test results; update the manifest and reconcile the pass-3 CODE dispositions against that release. Sources: F7–F12; pass-3 disposition §3.
8. **Later-stage acceptance is explicitly gated by substantive evidence:** ELEVATED interface, frozen membership, scorecard/coverage validation, cutover equality, F-3 target and deletion-guard proof, server-enforced build scope, and certification freshness. No filename or free-text event may substitute. Sources: F7–F14/F16.
9. **The isolated rehearsal and recovery plans have named owners, provisionable identities and executable acceptance cases**, including a production-equivalent image, global-L0 isolation, restore/revert drill and retention window. Their successful completion must block J1 or the affected production wave. Sources: F15/F16.
10. **The native accepts a concrete operating schedule and evidence packet:** unresolved decisions are enumerated, review/merge attendance windows assigned, the current family notice acknowledged by exact version, and token/spend reporting demonstrated. Sources: Charter §7; F17; Q4/Q17.

## 5. What could not be assessed

| Cannot assess from this bundle | Evidence that would settle it |
|---|---|
| **Current production privileges, FKs, guard functions, deployed images and chart impact — cannot determine from the bundle.** | Dated read-only catalog/privilege results, deployed image digests, route responses and chart-impact measurements. Sources identifying these dependencies: Track E §§7–8; D6 runbook §§2–5. |
| **Whether D6 remains effective after later schema or privilege changes — cannot determine from the bundle.** | Current effective-privilege checks, accepted SECURITY DEFINER exceptions and their reviewed implementations, plus the actual provisioned file ownership. Sources: `S/D6_SUVARNA_READER_RUNBOOK_v1_0.md` §§2, 5; `T/monitor.py::check_credential_readonly`. |
| **Actual Claude Code permission behavior across user/project/local scopes — cannot determine from the bundle.** | Installed CLI version, effective settings, enabled integrations and recorded positive/negative integration tests under the real swarm user. Source: template `_meta.findings_v2_1_239`. |
| **The nine-gate standard’s full derivation and semantic adequacy — cannot determine from the bundle.** | Sealed tier documents, criterion registry, inspector implementation, mutation fixtures and representative asset briefs. Source: review package §3 exclusions; Plan §2.1. |
| **The 799 gaps, zero certificates, frozen level/family populations and complete dependency closure — cannot determine from the bundle independently.** | Exact ledger snapshots, generated maps, registry export and reproducible census outputs at identified revisions. Sources: Plan Appendix A; Track E §8. |
| **Successful current tests or CI deployment of the reviewed tracker — cannot determine from the bundle.** | A fresh run tied to the reviewed hashes, including the counterexamples in this report and actual CLI/runtime integration. I did not execute the supplied suite. Source: `MANIFEST.txt`; `T/tests/`. |
| **Rehearsal, restore, kill-switch and incident-recovery success — cannot determine from the bundle.** | Reproducible drill records, commands, inputs, outputs, failure injections and acceptance review. Sources: Track E §7 E5.6/E5.7; Runbook §§5–6. |
| **Current family acceptance, authoritative acknowledgments and delivery dates — cannot determine from the bundle.** | Sealed family briefs, authenticated/version-bound acknowledgments, owner commitments and native rulings. Sources: Model F1.G/S/K, FI-8; `run/DECISIONS.jsonl`. |
| **A defensible completion date or monetary budget — cannot determine from the bundle.** | Measured packet throughput, build/census duration, native response times, review rejection rates, cache/billing data and family schedules. Sources: Plan §6.6; Arch §§5.5, 12.8. |