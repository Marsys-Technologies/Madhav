---
artifact: PRAVAHA_CAMPAIGN_PLAN
canonical_id: PRAVAHA_CAMPAIGN_PLAN
version: "1.0"
status: ACTIVE
date: 2026-09-29
owner: "the native (Abhisek Mohanty); steward: the strategic Claude session that wrote this plan"
executors: "two Kimi Code sessions — Stream A (Karma) and Stream B (Śāstra) — run in parallel, one session each, never as sub-agents of each other"
governs: "everything from the sealed Gochara doctrine (FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md) to a served, retrodicted, flipped Gochara generation for chart 482012f1"
plan_model: 00_ARCHITECTURE/control/pravaha/plan_model.json
tracker: "http://127.0.0.1:8766 — see PRAVAHA_EXECUTION_ARCHITECTURE_v1_0.md"
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty) only — native directive 2026-09-29; no build for 1c826d5a"
changelog:
  - "1.0b (2026-09-29): native rule added to §7 — all reviews are initiated by the native only."
  - "1.0a (2026-09-29): the three late decisions (D-SPECS, D-FLIP, D-T2) now depend on their inputs (B3.6, J2, J2) in the plan model, so the tracker shows them as not yet due instead of ready; the native ruled the other 16 decisions ('Accept all recommendations')."
  - "1.0 (2026-09-29): first version, written at the native's instruction to fold the Gochara forward program (open items 1–12, phases 0–6) into one campaign with a real-time tracker and two parallel streams."
---

# Pravāha — the Gochara elevation campaign

**Name.** *Pravāha* (प्रवाह) is the cosmic wind that, in the Sūrya-Siddhānta and Purāṇic cosmology, carries
the planets along their courses — the force behind gochara itself. The word also means *stream*, which is how
this campaign runs: two streams, side by side, meeting only where the work must meet.

**What it delivers.** A Gochara generation for your chart that is astrologically sound by the sealed v3.0
doctrine, built by a registered writer on the governed Cloud Run path, measured against your lived events on a
protocol declared in advance, and served only after your flip decision.

**How to read this plan.** §1 is where we start. §2 is the strategy in five rules. §3 explains the two streams and
why they cannot collide. §4 is the phase map. §5 lists every activity (the same 68 items the tracker shows). §6 is
your decisions. §7 is the standing rules. The tracker is the live form of §5; this document and
`plan_model.json` must always agree (the steward checks at every change).

---

## 1. Starting position (2026-09-29)

| Thing | State |
|---|---|
| `'4.0'` / `'4.1'` code | Written on `l3/gochara-autonomous-wp0-7` (PR #2731): kernel, contact ledger, coverage, publication, windows writer, cutover kit, manifest-driven serving packets. **Not deployed.** PR #2731 is *conflicting* with `main`; CI has reds; E-022 (pins re-admission) waits on you |
| Served data | `'3.0'` on both charts. `'4.0'` burned for 482012f1 (flip reversed 2026-09-28); chart 2 holds candidate-only `'4.0'` rows |
| Century build | Never completed. Local century enumeration is prohibited (ADK-0028); it runs only as the Cloud Run job after #2731 is merged and deployed |
| Doctrine | `FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` — **SEALED** after Codex gpt-6-astra and Kimi K3 reviews. Copies in `briefs/pravaha/sealed/` |
| Astrological quality of the written code | Carries every Tier-0 defect in v3.0 §1 — including three in the geometry the century ledger is made of (mirrored Mars/Saturn aspects, fabricated Aries ingress, dropped truncated contacts) and the full scoring collapse (promise 1.0, constant permission, all-favourable valence, flat peaks) |
| Registered writer | None produces `'4.x'` (Disclosure 3); only the cutover scripts can |

## 2. Strategy — five rules

1. **Ship the plumbing, not the verdict.** Merge and deploy #2731 as code (serving packets, ledger schema, cutover
   kit are all generation-agnostic and needed). Never flip `'4.1'`: it would replace `'3.0'` with windows that read
   "favourable" for bereavement and deception (§N.7).
2. **Geometry before the expensive build.** The century ledger is the costly artifact; the projection is cheap to
   redo. So the kernel geometry fixes (Tier 0-G) land *before* the first Cloud Run century build, and that build
   (`'4.1'`) exists as an engineering proof and a geometric baseline — candidate-only, never published.
3. **Measure before mechanism.** The LEL's computed annotations are wrong in three places; the evaluation protocol
   and held-out events are declared and reviewed before any new rule path is built (v3.0 Tier 3 moved into Tier 0).
4. **Design, review, freeze, then build.** Specs are reviewed by Kimi K3 and Codex gpt-6-astra (both max) and frozen
   by your ruling before Phase 5 code — the loop that just caught nine of the author's own errors.
5. **The tracker is the work queue.** Streams take their next item *from* the tracker (`pravaha next`), claim it
   (`pravaha start`), and close it with evidence. Work that is not on the tracker does not happen. That is what keeps
   the dashboard real-time: it is not a report written after the work, it is the instrument the work runs through.

The first astrologically sound candidate is labelled **`'5.0'`** (a different method and convention requires a new
generation under the immutability rule).

## 3. The two streams

Two Kimi Code sessions, each a full session in its own worktree — not agents, not sub-agents. They share nothing
but the frozen specs and the tracker.

| | **Stream A — Karma** (build & delivery) | **Stream B — Śāstra** (doctrine, design & measurement) |
|---|---|---|
| Worktrees | `/Users/Dev/madhav-l3/gochara-wp0-7` (Phases 0–1, lane branch) → `/Users/Dev/madhav-l3/pravaha-a` (Phase 2+, created from `main` after #2731 merges) | `/Users/Dev/madhav-l3/pravaha` (branch `campaign/pravaha`) → `/Users/Dev/madhav-l3/pravaha-b` (Phase 5 code) |
| Branches | `l3/gochara-autonomous-wp0-7`, `pravaha/a2-kernel-geometry`, `pravaha/a5-*` | `campaign/pravaha`, `pravaha/b5-rule-paths`, `pravaha/b5-eval-harness` |
| May touch | `services/gochara_kernel/**`, `pipeline/orchestrator/writers/ka_gochara*.py`, `scripts/kala_gochara_cutover/**`, `services/gochara_v3/**`, `services/gochara_intensity/**`, `services/ka_gochara_resonance/**`, `services/ka_vedha_gochara/**`, `services/ka_moorti_nirnaya/**`, migrations (numbered by fresh scan + MIG-1), Cloud Run job config, `00_ARCHITECTURE/autonomy/**` and the lane's `gochara_wp0_7/**` records, tests under `tests/l3/gochara/**` | `00_ARCHITECTURE/briefs/pravaha/**` (packets, amendment, specs, reviews, corpus reads, measurement), `services/gochara_rules/**` (new), `services/gochara_eval/**` (new), their tests; **read-only** everywhere else, including production (read-only role) and the corpus table |
| Must not touch | `briefs/pravaha/design/**` and `measurement/**` (B's), `services/gochara_rules/**`, `services/gochara_eval/**`, the LEL | anything in A's column; the LEL file itself (B writes a *derived* reconciliation); `kala_*` / `gochara_*` production rows; migrations |
| Talks to production | yes — only on the governed path (deploy pipeline, Cloud Run job), only with your authorisation, candidate-only until your flip | read-only queries only |

**Why they cannot collide.** File scopes are disjoint (enforced by the stream prompts and checked at every review).
The only shared contracts are the design specs, which B writes and *freezes* at J1 before A codes against them;
A's migrations implement B's frozen schema. Rule paths (B) plug into the writer (A) through the frozen rule-path
interface. The tracker refuses an event from one stream on the other stream's item.

**Cross-stream dependencies** (shown ⇄ on the dashboard): B4.4 waits on A2.6 (the `'4.1'` baseline needs the
build); A5.5 waits on B5.1/B5.2 (the rehearsal needs the rule paths); B5.4 waits on A5.6 (the report needs
`'5.0'`); B6.2/B6.3 wait on A6.x. Everything else runs independently.

## 4. Phase map

```
            Stream A (Karma)                              Stream B (Śāstra)
Phase 0     A0 hygiene: ADK-0029, re-merge, CI,     ∥     B0 decision packet, sealed brief committed
            readiness packet
Phase 1     A1 your merge of #2731 → deploy          ∥     B3 design round: amendment → specs →
            → DEPLOY_SHA → 12.10c                          corpus reads → coordination → K3+Astra
Phase 2     A2 Tier 0-G geometry → review → merge    ∥        review → reconcile → FROZEN
            → Cloud Run '4.1' (proof, no flip)       ∥     B4 measurement: LEL reconciled → protocol
            → evidence + benchmark                            → '3.0' baseline → '4.1' baseline ⇄A2.6
                              ╲                      ╱
                               J1  design frozen · geometry merged · protocol declared
                              ╱                      ╲
Phase 5     A5 migrations → sky substrate →          ∥     B5 rule paths P1–P6, promise & nature,
            registered writer + Tier 0-S repairs            retrodiction harness
            → rehearsal ⇄B5.1 → Cloud Run '5.0'
            → new gates                              ∥     → retrodiction report ⇄A5.6
                              ╲                      ╱
                               J2  '5.0' gated and retrodicted → YOUR FLIP DECISION
                              ╱                      ╲
Phase 6     A6 flip + soak → century writer retired  ∥     B6 Tier 2 doctrine, L5 hand-off, close
            → Tier 2 infrastructure
                               J3  campaign closed
```

## 5. Every activity

Owner: A = Stream A, B = Stream B, native = you, steward = the strategic session. "Done when" names the detector
the tracker uses; where none exists yet the stream closes the item with evidence, and B3.6 adds detectors for every
Phase 5 item at the freeze.

### Tracker
| ID | Activity | Owner | Depends on | Done when |
|---|---|---|---|---|
| T1 | Tracker live and supervised (launchd KeepAlive) | steward | — | `/api/health` answers |
| T2 | Campaign plan, execution architecture, stream prompts | steward | T1 | this file exists |

### Stream A — Karma
| ID | Activity | Depends on | Done when |
|---|---|---|---|
| A0.0 | Session connected (preflight) | T2 | evidence: preflight output |
| A0.1 | Record ADK-0029: build scope 482012f1 only; sequence amended per D-41; chart-2 `'4.0'` rows disposition | A0.0, N-SCOPE, N-41 | ADK-0029 row on the lane branch |
| A0.2 | Re-merge `origin/main` into the lane; conflicts resolved; PRAMĀṆIN verifies | A0.0 | evidence: merge commit + verification |
| A0.3 | #2731 mergeable, every check green | A0.2, N-E022 | detector `pr_ready` |
| A0.4 | Merge-readiness packet refreshed (merged tree; `migrate.ts --dry-run`; 12.10c plan) — gate | A0.3 | evidence: packet |
| A1.1 | **#2731 merged — your merge** — gate | A0.4 | detector `pr_merged` |
| A1.2 | Deploy verified from the service's `env.DEPLOY_SHA` (Trap 103) | A1.1 | evidence |
| A1.3 | 12.10c hygiene on the merged tree | A1.1 | evidence |
| A2.1 | Tier 0-G geometry: aspect direction · 0° seam · no fabricated ingress · truncated contacts kept · residence spans persisted · global boundary table · regression suite | A1.1, N-41 | evidence: PR |
| A2.2 | K3/O-2 independent review of the amended application set — gate | A2.1 | evidence: review |
| A2.3 | Geometry merged to `main` | A2.2 | detector `branch_merged` |
| A2.4 | Cloud Run job spec for century enumeration (streaming payloads; one chart) | A1.2 | evidence |
| A2.5 | **Century build `'4.1'` for 482012f1 on Cloud Run — candidate only** — gate | A2.3, A2.4, N-CLOUD | detector: publication row `'4.1'` |
| A2.6 | `'4.1'` evidence (Link-2, gates b/c, a–k, PRAMĀṆIN); benchmark metrics | A2.5 | evidence + metrics |
| A5.1 | Migrations for the frozen contracts, applied via deploy, verified | J1 | detector added at B3.6 |
| A5.2 | Sky-event substrate built (all bodies but the Moon) | A5.1 | detector added at B3.6 |
| A5.3 | Registered `ka_gochara` writer (three objects; per-path pruning; interval sweep; day tier on demand) | A5.1 | evidence: branch merged |
| A5.4 | Tier 0-S repairs: angular M-1 · per-instant permission · three-field valence · vedha interval relation · 90-day filter to serve time · `birth_anchor` excluded · honest mūrti flag · tārā key · kakṣyā key · resonance rebuild R-1..R-6 | J1 | evidence |
| A5.5 | Rehearsal, battery, K3/O-2 review — gate | A5.2, A5.3, A5.4, B5.1, B5.2 | evidence |
| A5.6 | **Candidate `'5.0'` for 482012f1 on Cloud Run** — gate | A5.5, N-CLOUD | detector: publication row `'5.0'` |
| A5.7 | New gates green on `'5.0'` | A5.6 | evidence |
| A6.1 | **Flip to `'5.0'`, soak trigger #0, soak** — gate | J2, N-FLIP | detector: authority = `'5.0'` |
| A6.2 | Century writer retired; registry and seed aligned; Disclosure 3 closed | A6.1 | evidence |
| A6.3 | Tier 2 infrastructure (annual Tājaka substrate; eclipses and stations) | A6.1, N-T2 | evidence |

### Stream B — Śāstra
| ID | Activity | Depends on | Done when |
|---|---|---|---|
| B0.0 | Session connected (preflight) | T2 | evidence |
| B0.1 | Native decision packet — each open decision with evidence and recommendation; each emitted `requested` | B0.0 | `NATIVE_DECISION_PACKET_v1_0.md` |
| B0.2 | Sealed v3.0 set committed on `campaign/pravaha` as the Gochara final brief | B0.0 | committed file says `status: SEALED` |
| B3.1 | Amendment reconciling plan v2.1 and ruling sheets with v3.0 | B0.2, N-BRIEF | `GOCHARA_PLAN_V3_AMENDMENT_v1_0.md` |
| B3.2 | Design specs: relationship record · rule paths P1–P6 · three-field valence · per-instant permission · vedha interval relation · sky-event substrate · solver method + uncertainty · bindu polarity · annual-object identity · registered-writer architecture · test oracles | B3.1 | `GOCHARA_DESIGN_SPECS_v1_0.md` |
| B3.3 | Corpus reads still `[U]` (Phaladīpikā XXVI.25–29; Muhūrta Cintāmaṇi tārā; Tājaka activation; BPHS Sun-AV father; KP Venus note; Moon/node recount) | B0.0 | `CORPUS_READS_v1_0.md` |
| B3.4 | Kṣetra / Saṅgam coordination note | B3.2 | `L3_FAMILY_COORDINATION_v1_0.md` |
| B3.5 | Independent review of the specs — Kimi K3 max and Codex gpt-6-astra max — gate | B3.2, B3.3, B3.4 | both reviews on disk |
| B3.6 | Reconcile; specs FROZEN; Phase 5 detectors added to the plan model | B3.5, N-P4, N-PADMIT, N-RQ1, N-RQ2, N-RQ4 | specs file says `status: FROZEN` |
| B4.1 | LEL chart-state annotations regenerated from L0/L1 (derived file) | B0.0 | `LEL_CHART_STATE_RECONCILED_v1_0.md` |
| B4.2 | Evaluation protocol pre-declared and reviewed — gate | B4.1 | `EVALUATION_PROTOCOL_v1_0.md` |
| B4.3 | `'3.0'` baseline scored | B4.2 | `BASELINE_3_0_v1_0.md` |
| B4.4 | `'4.1'` geometric baseline scored ⇄ | B4.2, A2.6 | `BASELINE_4_1_v1_0.md` |
| B5.1 | Rule-path catalogue and evaluators P1–P6 | J1 | evidence: branch merged |
| B5.2 | Promise (strength + condition), agent nature and maitrī, cited yoga→event map | J1 | evidence |
| B5.3 | Retrodiction harness | J1 | evidence: branch merged |
| B5.4 | Retrodiction report `'5.0'` vs `'3.0'` vs `'4.1'` ⇄ — gate | B5.3, A5.6, B4.3, B4.4 | `RETRODICTION_REPORT_5_0_v1_0.md` |
| B6.1 | Tier 2 doctrine (Jaimini, transit-to-transit, star-limb/sign-third, SBC grid) | J2, N-T2 | evidence |
| B6.2 | L5 calibration hand-off ⇄ | A6.1 | evidence |
| B6.3 | Close report, CURRENT_STATE, session log ⇄ | A6.2, A6.3, B6.1, B6.2 | evidence |

### Joins
| ID | Join | Depends on |
|---|---|---|
| J1 | Design frozen · geometry merged · protocol declared — Phase 5 may start | B3.6, N-SPECS, A2.3, B4.2 |
| J2 | `'5.0'` gated and retrodicted — your flip decision | A5.7, B5.4 |
| J3 | Campaign closed | B6.3 |

## 6. Your decisions

Each appears on the dashboard's "Waiting on you" panel the moment a stream requests it, with the recommendation.
Record a ruling with `pravaha decide <ID> --detail "<your words>"` (or tell the steward, who records it with
`--as steward` quoting you).

| ID | Decision | Recommendation | Gates |
|---|---|---|---|
| D-SCOPE | Build only for 482012f1 | Yes (you have said so; recorded) | A0.1 |
| D-T1 | Permanent read-only DB credential for the tracker's DB checks | `~/.config/pravaha/pgenv.sh`, mode 600 | DB detectors |
| D-41 | `'4.1'` = proof after geometry fixes; never flip; next label `'5.0'` | Yes | A0.1, A2.1 |
| D-BRIEF | Countersign sealed v3.0 as the Gochara final brief | Yes | B3.1 |
| D-E022 | Pins re-admission at #2731 merge | Yes, per runbook | A0.3 |
| D-CLOUD | Cloud Run century builds for 482012f1, candidate-only | Yes | A2.5, A5.6 |
| D-RQ1 … D-RQ8 | The eight ruling requests of v3.0 §7 | Yes (see packet) | B3.6 |
| D-P4 | Double transit as `[P]`, redefined | Yes, `uncited_extension` | B3.6 |
| D-PADMIT | Other `[P]` elements as testimony first | Yes | B3.6 |
| D-SPECS | Freeze the specs | **Not yet due** — becomes due when B3.6 (reconciled, reviewed specs) is done | J1 |
| D-FLIP | Flip to `'5.0'` | **Not yet due** — becomes due at J2; flip only if the gates pass and retrodiction beats `'3.0'` | A6.1 |
| D-T2 | Tier 2 admissions | **Not yet due** — becomes due at J2; path by path | A6.3, B6.1 |

## 7. Standing rules (both streams, every phase)

- **Reviews are initiated by the native only** (native, 2026-09-29: *"going forward all reviews are to be initiated by me, you don't do it for this campaign"*). Streams and the steward prepare review packets and hand them to the native; nobody dispatches Kimi K3, GPT-6 Astra or any other reviewer. A gate item waiting on a review is parked with its packet path until the native reports the review is done.
- No local century enumeration (ADK-0028). Century builds run only as the Cloud Run job, only with D-CLOUD.
- No flip of `'4.1'`. No flip of anything without D-FLIP.
- No calibration or weight-fitting on the collapsed score.
- No new rule path before Tier 0-G is merged and the specs are frozen.
- No LEL annotation used as ground truth until B4.1 has reconciled it; the LEL file itself is never edited by a stream.
- Every `[P]` enters only as `uncited_extension` with a ruling; nothing `[U]` enters a score.
- Every number with its predicate; every "done" with evidence; every production write on the governed path.
- Builds for chart 482012f1 only.
- The FROZEN orchestrator contract, the §N.4–§N.8 disciplines and the existing native rulings all stand.

## 8. Risks

| Risk | Mitigation |
|---|---|
| #2731 keeps drifting behind `main` | A0.2 re-merges immediately before A0.4; you merge soon after the packet |
| Cloud Run century build fails on memory (13.5 M episodes) | Tier 0-G removes duplicated solves (1.21 M of 1.35 M episodes per decade were duplicates) before A2.5; streaming payloads in A2.4 |
| Specs review returns REWORK | B3.5 → B3.6 loop is on B's critical path, not A's; A continues Phase 2 |
| A stream goes silent | the dashboard marks it stale (15 min) and silent (45 min) while work is running; git activity still shows commits |
| The tracker dies | launchd restarts it (measured 0.3 s); the event log is the truth and is replayed on start; the CLI reads the last snapshot if the server is down |
| The two streams touch the same file | disjoint scopes (§3); the tracker refuses cross-stream item events; reviews check scope |

## 9. Closing

The campaign closes at J3 with a close report (B6.3), CURRENT_STATE updated, and the tracker left running in
read-only mode as the historical record.
