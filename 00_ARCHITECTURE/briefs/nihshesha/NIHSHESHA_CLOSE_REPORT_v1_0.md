---
artifact: NIHSHESHA_CLOSE_REPORT
canonical_id: NIHSHESHA_CLOSE_REPORT
version: 1.0
status: CURRENT
created: 2026-07-31
campaign: NIḤŚEṢA ("leaving no remainder") — final wrap-up campaign after SAMĀPTI closed CLOSED-PARTIAL
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_CLOSE_REPORT_v1_0.md, SAMAPTI_KALA_HANDOVER_v1_0.md, BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md
---

# NIḤŚEṢA close report

## The plain answer

**Yes, one thing remains genuinely open by design, and it is named below (Track A's live end-to-end
proof). Everything else that was closeable has been closed** — either VERIFIED-FIXED and merged (or
merge-armed and draining automatically), HANDED-OVER to ṢAḌ-DARŚANA as a written spec, or
PARKED-HONEST with a precise resume condition. **No Kāla file (`kala_*`, `l3_*`, `ka_*`, `gochara_*`)
was edited or written to this session.** No credential was rotated; PR #905 merged as ordinary
hygiene per explicit native instruction, and a second credential-adjacent document (PR #907) was
closed out with the native's actual disposition recorded in place rather than left asserting a
now-superseded P0.

## 1 — What this session actually did (summary before the tables)

Starting from SAMĀPTI's CLOSED-PARTIAL state (18 merges, a Kāla handover, a protective-set close),
this session:

- Merged the already-VER-confirmed PB-3.1 loop backlog (G2/G3, G4/G5, G8, G6) plus 4 more real fixes
  produced fresh this session (2 by dedicated re-diagnosis, 2 by narration archaeology).
- Split one PR (#909) into a mergeable non-Kāla part and a Kāla-touching part that was **withheld**
  and instead written up as a handover spec addendum (PR #969) — the first concrete exercise of the
  "hold the audit, ship the guards, hand over the rest" doctrine from SAMĀPTI's own Ruling 83.
- Ran six parallel investigative tracks (B–G below) covering the narration residuals (SV-3..7), the
  FC-4 module-level-import sub-audit, two stuck PRs' real re-diagnosis, worktree-isolation
  verification + cleanup, four standing investigations (chart_dashas delta, MCP tool-count mismatch,
  the deferred 19-PR-body recheck, INF-3 restatement), and two PR builder-summary write-ups.
- Drained the wider VER-confirmed merge backlog (14 more PRs) serially, resolving three genuine
  merge conflicts along the way (one migration-number placeholder allocation, one clean three-way
  split, one deliberate park against actively-evolving concurrent CI-audit work).
- Closed one PR outright as superseded-by-already-merged-work (#903) rather than merging stale
  content backward over a newer version already on `main`.

## 2 — Disposition table: every NIḤŚEṢA-brief item

| Track | Item | Disposition | Evidence |
|---|---|---|---|
| A | G1 (mount LogToSamiksha) | VERIFIED-FIXED (prior — PR #902, already on `main`) | Confirmed merged before this session began. |
| A | G2/G3 (cron secret rename + un-skip CI DB-integration tests) | VERIFIED-FIXED, merged | PR #895 — rebased through 2 real conflicts (MIG-1 guard step ordering, `samiksha-daily.yml` env block), CI green, merge armed. |
| A | G4/G5 (one outcome map; calibration-leak guard that can fire) | VERIFIED-FIXED, merge-armed | PR #925 — clean rebase, no conflicts. |
| A | G6 (mount spec-conformant kāla-rekhā UI; kill fixture-fed dock card) | VERIFIED-FIXED, merge-armed | PR #920 — Track G independently reproduced every claim (16/16 + 283/20 tests, `tsc`/`eslint` clean) before I armed the merge; **note**: "kāla-rekhā" here is the frontend UI timeline widget (`platform/src/components/pariprashna/**`), not a `kala_*` backend file — confirmed zero backend Kāla files in its diff. |
| A | G7 (badge verify, C5-PB7-BADGE) | PARKED-HONEST (unchanged from SAMĀPTI Ruling 86) | Blocked on C4 below; not re-attempted. |
| A | G8 (byte-equality gate, full 12-fixture corpus) | VERIFIED-FIXED, merge-armed (non-blocking Ruling-80 gap noted, unchanged) | PR #927 — clean rebase. |
| A | C4-LOOP-LIVE-PROOF (a real deployed reading → ledger row → review tab → resolve → daily job → outcome map → leak guard, live, A1-A6) | **PARKED-HONEST — the one genuinely open item** | Cannot be run honestly until G2/G3/G4/G5/G6/G8 are confirmed *deployed*, not merely merge-armed, since the proof is explicitly required to be live-production, never a fixture. Resume condition: once the merge-armed PRs above land and deploy-verify (this session confirmed deploy health after each of its own direct merges; the auto-merge queue's remaining lanes need the same one-line `gcloud run revisions describe … commit-sha` check before C4 is attempted), run C4 as the very next action — it is the correct next step, not a re-scoping. |
| B | SV-3 (2nd fact_key-pinning instance) | NOT-APPLICABLE — no second instance exists | Track B ran `check_fact_category_pinning.py` estate-wide: 0 new violations; the original SV-3 fix (`ga_structural_writer.py:3369`) is intact and the only instance of the class. |
| B | SV-4 (2nd OpenAI-allowlist-drift instance) | NOT-APPLICABLE — no second instance exists | `narration_model` as a column name occurs in exactly one writer/table (`ph_phaladesa`), already fixed by migration 469. |
| B | SV-5 (mi_darshana narration gap) | VERIFIED-FIXED, merge-armed (as part of PR #971) | `mi_darshana.py` `verdict_note` restructured across grade × tradition-data-presence axes; dead `trad_by_class.get()` lookup removed; 4 new + 8 existing tests pass. |
| B | SV-6 (operational bug #1 — mi_gunanaka UUID subscript) | VERIFIED-FIXED, merge-armed (PR #971) | `str(chart_id)[:8]` fix for `'UUID' object is not subscriptable`; regression test reproduced the exact failure pre-fix, passes post-fix. |
| B | SV-7 (operational bug #2 — bo_laksana_rerank timeout config) | NOT-APPLICABLE — self-healed, nothing to fix | No `writer_timeout_seconds` override exists on this asset at all; consistent with SAMĀPTI's own prior §6.5 disposition. |
| C | FC-4 4th sub-audit (runner.py / staleness.py / dag_edge_guard.py / service_probes.py) | COMPLETE — nothing further to fix | `dag_edge_guard.py`'s prior fix re-verified intact in a clean DB-free venv; `staleness.py`/`service_probes.py` have no module-level heavy import to defer; `runner.py`/`global_runner.py` have no DB-free self-test path for the defect class to break, and their genuinely optional imports are already call-time-deferred. 31 passed/1 skipped. |
| D | B-N8-FIX (#952) — real CI mock-test failure | VERIFIED-FIXED, **merged** | Root cause: `test_bo_chart_gestalt_emits_one_row_per_ayanamsha`'s hardcoded 10-call cursor mock was stale against the legitimate 11-call sequence B-N8-FIX's own production fix introduced. Test fixture corrected (no production code touched); merged at commit `f1c0793f` → main. |
| D | B-SECRETSCAN-SCOPE (#911) — confused reopen state | VERIFIED-FIXED, merge-armed | The "confused state" was a local, never-pushed, 32-commits-diverged worktree; the actual PR branch (`866600a4`) was untouched. Rebuilt cleanly on top of it: Ruling-82's 2-item fix (CI job name reverted, 28th credential file registered) plus a newly-found second stale-register-row escalated as `DVA-ESCALATION-SEC-005`. Mutation-tested (planted credential → red; removed → green). |
| E | E1 — worktree isolation actually observed? | CONFIRMED OBSERVED | Zero local worktrees for any `shad-darshana/*` branch; ~130 recent shad-darshana commits show a clean branch→PR→merge flow throughout; shared checkout sits on its own campaign branch with no ṢAḌ-DARŚANA code. One harmless side-finding: a stray already-preserved SAMĀPTI dispatch-script copy sitting untracked in the shared checkout — debris, not a violation, left alone. |
| E | E2 — prune stale worktrees | DONE | 39 confirmed-safe worktrees removed (merged-PR duplicates, reachable-elsewhere scratch branches); 28 left alone with reasons (open PRs, uncommitted local work, live sibling NIḤŚEṢA tracks). Count: 68 → 43 at measurement time (a moving target — this session's own tracks were actively creating new worktrees concurrently, which is itself the expected, correct behavior). |
| E | E3 — confirm `satyadipa/orchestrator-lit-predicate` absent | CONFIRMED ABSENT (3rd confirmation) | `git ls-remote`/`git branch -a` both empty. Nothing to delete. |
| F | F1 — chart_dashas −52,084 delta | NOT-APPLICABLE — named hypothesis REFUTED, real mechanism found | Live count re-measured: 484,387 (chart_id 482012f1). The 4-level-Sukshma-truncation hypothesis is refuted — that cap is deliberate and unchanged. Actual mechanism, decomposed exactly to the row: Kalachakra −70,784 (a correctness fix, M-6 2026-07-10, replacing a naive repeating walker with PyJHora's real classical engine) + chara_karaka +16,600 + Narayana (new 8th system) +1,327 + Vimshottari/KP +605 + mudda +168 = net −52,084, exact match. |
| F | F2 — MCP tool-count 3-way mismatch | HANDED-OVER (fix already exists, not mine to merge) | Live-reproduced first-hand: 124 is authoritative (direct roster count), 152 is `mcp_server_info.tool_count`'s decoupled generated-manifest metric, 167 is the pre-RC14-gate raw registered count. PR #912 is the already-VER-confirmed fix; merge-armed this session. |
| F | F3 — deferred 19-PR-body recheck (Ruling 41) | VERIFIED-FIXED / COMPLETED | Re-run against all 24 currently-open SAMĀPTI PRs (a superset of the original 19). Zero no-overlap cases, zero corrupted bodies, zero duplicate bodies. |
| F | F4 — INF-3 restatement | CONFIRMED-ALREADY-CLOSED | Ruling 56's EXPLAINED disposition re-quoted and independently corroborated (the agent's own operating instructions carry the identical "do not Write report .md files" policy Ruling 56 attributes the original trigger to). |
| G | Missing builder summaries — #920, #922 | BOTH CONFIRMED READY, comments posted | Independent reproduction of every claim in both PR bodies (test counts, mutation-test outputs, byte-for-byte hash matches) before posting; both merged or merge-armed this session. |
| G | 6 stale "skipped in CI" test-comment fix | PREMISE FALSE — not done, correctly not done | The premise assumed #895's CI-DB-wiring had already merged to `main`; it had not (still open at investigation time). Editing the comments to claim live CI coverage would have been a false claim. No edit made; correct resume condition recorded (do it once #895 is confirmed merged — which happened later this same session). |
| G | PR #905 (credential redaction) | VERIFIED — merged as ordinary hygiene | Confirmed diff-by-diff: 27 files, DSN-literal → env-var only, zero Kāla file, zero logic change. Merged and deploy-health-verified (live revision SHA matched). |

## 3 — SAMĀPTI register carryover — every surviving register ID

| ID | Disposition | Evidence |
|---|---|---|
| SV-1..SV-2 | Already CLOSED (prior SAMĀPTI session, PRs #864/#862) | Confirmed still intact, not re-touched. |
| SV-3, SV-4 | NOT-APPLICABLE (see §2 Track B) | — |
| SV-5, SV-6 | VERIFIED-FIXED, merge-armed (see §2 Track B) | — |
| SV-7 | NOT-APPLICABLE (see §2 Track B) | — |
| INF-1, INF-4, INF-5 | Already CLOSED (SAMĀPTI, worktree isolation protocol #961) | Re-confirmed live by Track E1/E2 this session. |
| INF-3 | CONFIRMED-ALREADY-CLOSED (see §2 Track F4) | — |
| EP-1 | Still PARKED, unchanged from SAMĀPTI Ruling 86 (VOID-as-present-tense-claim; a real re-reconciliation still owed) | Not re-attempted — depends on C1-REBUILD, which nothing this session did makes newly worthwhile (no narration-fix lanes were rebuilt against; the fixes landed were test/detector fixes, not writer output changes needing a chart rebuild). |
| B-N8-FIX (#952) | VERIFIED-FIXED, merged | See §2 Track D. |
| B-SECRETSCAN-SCOPE (#911) | VERIFIED-FIXED, merge-armed | See §2 Track D. |
| B-DOCS-GOVERNANCE (#928) | Already merged (SAMĀPTI session, confirmed on `main` at `fc709aaa`) | — |
| B-MCP-CATALOG-GAP (#912) | HANDED-OVER — merge-armed, see §2 Track F2 | — |
| chart_dashas −52,084 delta (Ruling 16) | NOT-APPLICABLE — refuted + explained (see §2 Track F1) | — |
| MCP tool-count mismatch | HANDED-OVER (see §2 Track F2) | — |
| Deferred 19-PR-body check (Ruling 41) | VERIFIED-FIXED/COMPLETED (see §2 Track F3) | — |
| B-NAR-BO/GA/MI/PH remainder + B-NAR-TS non-Kāla files | PARTIALLY ADDRESSED this session (SV-5/SV-6 above); the remainder (B-NAR-BO/GA/PH proper, and B-NAR-TS's `capabilities.ts`/`envelope.ts`/`vidhi_registry_resource.ts`/`server.ts`/`register_p1_synthesis.ts`/`register_p1_ganita.ts`) still PARKED-HONEST, unstarted | Resume spec unchanged: PR #956's corrected 45-path partition. |
| B-N8-FIX/SWEEPFIX named residuals (F-13, F-15/F-16/F-17, strongest/weakest-domain bug) | Still PARKED-HONEST, not attempted this session | Named, cheap, non-Kāla follow-ups in `bo_pramana_mapa.py:265` and `bo_chart_gestalt.py`; out of this session's declared Track scope (Track B/C were scoped to SV-3..7 and FC-4 specifically). Carried into the consolidated backlog below. |
| Kāla-handed-over findings (7 files + kala_temporal.ts + gochara diagnosis + kala_envelope.ts F-20) | HANDED-OVER, unchanged + **one addition this session** | `SAMAPTI_KALA_HANDOVER_v1_0.md` §4 amended in place (§4-ADDENDUM, PR #969) with the newly-found kala_envelope.ts F-20 defect (freshness.stale always false) — spec only, no code merged, per the hard scope boundary. |
| Standalone-parked items (C3-BUILDSTATE-RECON, G7/C5-PB7-BADGE, C6-PB4-PURNATA) | Unchanged, still PARKED-HONEST | Not re-attempted; resume conditions unchanged from Ruling 86. |
| Credential incident (B-SECRET-ROTATE-PREP, #907) | **CLOSED** this session — by native disposition, not by rotation | See §4 below. |

## 4 — The credential item, explicitly (per the native's binding instruction this session)

PR #907 (the rotation-prep runbook + compromise assessment, previously `UNRESOLVED-PENDING-NATIVE-
EXECUTION`, `Priority: P0`) was **not** merged as-is — its live banner would have re-asserted a P0
claim the native has since superseded. Instead, this session amended it in place with a
`§9-NATIVE-DISPOSITION` section and a corrective banner recording the actual outcome: **the native
reviewed the credentials (INC-1/INC-2/INC-3) and classified them SECURE / accepted risk. No
rotation was performed. This is not re-raised as a P0.** The technical analysis (§0–§8) is retained
unedited as audit trail, per `ONGOING_HYGIENE_POLICIES §A` — only the priority/action conclusion is
superseded, and it's superseded by a new section, not by rewriting history. PR #905 (plaintext
redaction) merged separately as ordinary hygiene, independent of the rotation question.

## 5 — The ONE consolidated backlog (replaces all scattered parks)

Every item below has a named owner and a named resume condition. Nothing here needs re-deriving
scope from scratch.

| # | Item | Owner | Resume condition |
|---|---|---|---|
| 1 | C4-LOOP-LIVE-PROOF (real end-to-end reading→ledger→UI→outcome→daily-job proof, A1-A6) | Next PB-3-class session | Immediately, once this session's merge-armed PRs (#895/#920/#925/#927) are confirmed deployed via `gcloud run revisions describe … commit-sha`. This is the single highest-priority item in this backlog. |
| 2 | C5-PB7-BADGE | Next PB-3-class session | After item 1 (C4) lands — it's the acceptance gate C5 depends on. |
| 3 | C6-PB4-PURNATA / R-0 PB-4 | Next PB-3-class session | After items 1–2. |
| 4 | B-NAR-BO/GA/PH lanes (never dispatched) | Next narration-fix session | Dispatch from PR #956's corrected 45-path partition directly. |
| 5 | B-NAR-TS non-Kāla files (`capabilities.ts`, `envelope.ts`, `vidhi_registry_resource.ts`, `server.ts`, `register_p1_synthesis.ts`, `register_p1_ganita.ts`) | Next narration-fix session | Same partition; these are explicitly non-Kāla per that partition. |
| 6 | `bo_pramana_mapa.py:265` F-13 (`msr_no_threshold_drop_flag` tautology, identical shape to the already-fixed F-08) | Next available session, cheap | One-line fix, same pattern as F-08's fix — mirror it. |
| 7 | `bo_chart_gestalt.py` F-15/F-16/F-17 (`fragility_class` literal, `linking_mechanism` literal, contested-areas claim at fixed lines) + strongest/weakest-domain insertion-order bug | Next available session, cheap | Named file:line in SAMAPTI_DVARAPALA_LEDGER.md Ruling 86; not re-derived here, just carried forward. |
| 8 | EP-1 re-reconciliation (build_substep_progress vs. full plan) | Next session after a narration-writer rebuild happens | Genuinely blocked on C1-REBUILD being worth running — not worth doing standalone. |
| 9 | C3-BUILDSTATE-RECON | Same as EP-1 | Same condition. |
| 10 | ci.yml/chat-v2-ci.yml #913 (F-29/F-30/F-31 CI-gate hardening) | The concurrent CI-audit session, or whoever owns that file next | Genuinely conflicts with actively-evolving, already-authoritative concurrent work (PR #963's tier-4 hardening deleted/superseded two of the three stages #913 touches). Needs a human or a single coordinating session to reconcile deliberately, not a forced auto-resolution. |
| 11 | Kāla findings (unchanged: 7 ka_*/l3_* files + kala_temporal.ts slice + gochara root-cause + kala_envelope.ts F-20) | **ṢAḌ-DARŚANA** | `SAMAPTI_KALA_HANDOVER_v1_0.md` (amended, §4-ADDENDUM). No code to write — specs only. |
| 12 | Any residual auto-merge-armed PR from this session's batch that has not yet actually landed by the time this report is read | Whoever reads this next | Check `gh pr list --search "samapti in:head-ref-name"` — everything armed this session was CI-green or fixed at arm-time; a straggler is a queue-depth artifact, not a new defect. |

## 6 — Live crown re-verification

Direct `graha_portrait` call against the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`),
computed live at `2026-07-31T14:49:25Z`, this session:

> Sun = Capricorn · Lagna = Aries (12.43°) · Moon = Aquarius · current period Mercury MD / Saturn AD.
> `chart_header.name`: "Abhisek Mohanty". Grounded in 9 resolvable L1 `chart_facts.fact_id`s.

Matches the 7/7 FORENSIC birth anchors and the canonical chart_id exactly. No drift.

## 7 — Governance close

See the atomic close committed alongside this report: `SESSION_LOG.md` (new `NIHSHESHA-CLOSE-
2026-07-31` entry), `CURRENT_STATE_v1_0.md` (new top banner), `CLAUDE.md` (version bump + footer
changelog entry). No section/version collisions with the SAMĀPTI close's own entries — this is a
new, later entry appended after them, not an edit to them.

## 8 — Confirmation

**No file matching `kala_*`, `l3_*`, `ka_*`, or `gochara_*` was written to by this session.** The one
near-miss (PR #909's F-20 fix to `kala_envelope.ts`) was caught during the merge-conflict resolution,
split out, and the resulting code was withheld — only documented as a spec addendum
(`SAMAPTI_KALA_HANDOVER_v1_0.md` §4-ADDENDUM, PR #969). **No credential was rotated.** PR #905
merged as ordinary hygiene per explicit instruction; PR #907 was closed out with the native's actual
SECURE/accepted-risk disposition recorded in place, not re-raised as a P0.

---

*End of NIHSHESHA_CLOSE_REPORT_v1_0.md (2026-07-31).*
