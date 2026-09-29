---
artifact: SUVARNA_CAMPAIGN_PLAN
canonical_id: SUVARNA_CAMPAIGN_PLAN
version: "1.5"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-30
produced_in: session "Strategic Suvarṇa"
decision_owner: "Strategic Suvarṇa under N-28 (the native informed, with a veto at any time); the native for N-1, scope and end-state changes"
supersedes: "SUVARNA_CAMPAIGN_PLAN_v1_4.md (internal 1.4.1; v1.3, v1.2, v1.1, v1.0 before it). Earlier: succeeds the Nirmāṇa elevation campaign (NIRMANA_SUPERSESSION_RECORD_v1_0.md, PR #2751, merged)."
inherits:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                                  # tier 1 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md         # tier 2 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md        # tier 3 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md                      # tier 4 (draft)
uses: >
  The Nikaṣa engine as it stands on branch campaign/nikasha-test (PR #2736): the inspector (asset_census.py), tracker
  (asset_elevation_tracker.py), catalog provenance, the delta ledger (asset_gaps.jsonl), the certification ledger
  (asset_certs.jsonl), the change register (NIKASHA_CHANGE_REGISTER_v2_0.md) and the implementation plan.
review_disposition:
  - briefs/suvarna/reviews/REVIEW_PASS1_DISPOSITION_v1_0.md
  - briefs/suvarna/reviews/REVIEW_PASS2_DISPOSITION_v1_0.md
  - briefs/suvarna/reviews/REVIEW_PASS3_DISPOSITION_v1_0.md
  - briefs/suvarna/reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md
changelog:
  - "1.5 (2026-09-30, pre-final). Two native rulings and one independent review folded. N-28: the native is out of the loop — Strategic Suvarṇa decides every campaign decision with a recorded rationale (native informed, veto at any time); the native's acts shrink to the physical setup (new NATIVE_SETUP_v1_0.md), scope and end-state changes, and N-1; questions park to Strategic Suvarṇa, which gets its own unattended decision runtime (L.18). N-25b: the swarm's GitHub identity merges through a merge gate into main's squash merge queue (CI green, gate ACCEPT for the head SHA, path guard). N-29: production data is regenerable — destructive operations need a rebuild plan, a serving guard and a recorded fingerprint; the L0 dump becomes an impact statement plus a rebuild plan; new serving-guard principle (N-33). N-30: v1.5 pre-final → parallel reviews by GPT-6 Astra and Kimi K3 → reconcile → final → N-1. GPT-6 Astra's review (DO NOT APPROVE; F1–F18) disposed in reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md: ten launch gates LG.1–LG.10 in the plan model, CODE-36…65 for the tracker. Strategic Suvarṇa rulings N-31 (builder dispatches L0 through a server-enforced global grant), N-32 (F-3 concrete form: all eight keys dropped, the refusal guard retired, rebuild in wave order), N-33 (serving guard), N-34 (durable runtime before N-1; /loop dropped), N-35 (hold ledger; native veto), N-36 (build broker), N-37 (authority and control out of the swarm's reach), N-38 (merge gate); N-12, N-16, G16 and SEAL-G decided. Gochara is the Pravāha campaign (no 'L3 Gochara session'); its items map to Pravāha's tracker (peer_tracker_item); F2.5 dropped (Pravāha D-SCOPE). Saṅgam and Kṣetra: no family sessions exist; Suvarṇa's Track F owns their design now; implementation ownership decided at J1 (J1.FO). §1 end state and §2 standard unchanged in substance (only who rules)."
  - "1.4.1 (2026-09-30, review pass 3 folded in place): E1.10 (R34, R36); N-27 and E0.1/E0.1d; R244 DEFERRED only with withholding; level waves dispatch non-family assets only; E6.3 interface pinned; LEVEL_MAP.json; F3.FK target; census_run; FI-8 notice v1.2."
  - "1.4 (2026-09-29, review pass 2 folded): D6 applied; deadlocks removed; one branch rule; F-3 = cascade removed from eight keys; deploy = ancestry; per-wave fix items; lel_events N-14.R236; E6.3t; E5.6/E5.7 rehearsals; isolation proposed (N-25)."
  - "1.3 (2026-09-29, review pass 1 and D1–D6 folded): builder identity (E7); family certification (D2); gate detectors (E6); L0 dump and diff (D4); durable runtime (D5); reader login (D6); one J1 checklist."
  - "1.2 (2026-09-29): family sessions (N-17); launch readiness; the real-time tracker."
  - "1.1 (2026-09-28): parallel tracks with one join; Track F; companion documents."
  - "1.0 (2026-09-28): first full draft."
---

# Suvarṇa — the data-plane elevation campaign plan

## §0 · Reading guide

### 0.1 · Names

| Name | What it is |
|---|---|
| **Suvarṇa** (सुवर्ण, gold) | The campaign. Elevates every data-plane asset, L0 → L5. |
| **Nikaṣa** (निकष, touchstone) | The engine: four tiers, inspector, tracker, ledgers, detectors; with the build engine it depends on (N-2). |
| **Strategic Suvarṇa (SS)** | The deciding session. Plans, **decides every campaign decision with a recorded rationale (N-28)**, writes briefs, records decisions, performs control-plane changes (the control release, E0.1, E0.2). Never dispatches builds or runs lanes. Runs as the native's account, unattended through its own decision runtime (L.18). |
| **Nikaṣa Engine** · **Exec Suvarṇa** | The two execution sessions of the swarm (Track E; Tracks A, F-design, I, B). |
| **Pravāha** | The campaign that owns Gochara (a steward session and two Kimi Code sessions, its own tracker at `127.0.0.1:8766`, its own decisions D-*/ADK-*). Not part of the swarm; not bound by its charter. |
| **The native** | The project owner. Not a reviewer or supervisor (N-28). Acts only for: physical setup (`NATIVE_SETUP_v1_0.md`), credentials, scope or end-state changes, N-1, and the veto. |

- **Tracker ids.** Items such as `E5.3` or `LG.4` are ids in `00_ARCHITECTURE/control/suvarna/plan_model.json`;
  decision ids such as `N-12` are ids in the decisions log (§8). Pravāha's ids (e.g. `A6.1`, `D-SCOPE`) are cited as theirs.

### 0.2 · What this document is

- The master plan: end state, standard, tracks, gates, operating model.
- **Companions (v1.5 set):** `SUVARNA_AUTONOMY_CHARTER_v1_0.md` v1.5, `SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` v1.5,
  `NATIVE_SETUP_v1_0.md` v1.0, `SUVARNA_RUNBOOK_v1_0.md` v1.3, `tracks/TRACK_E_BRIEF_v1_0.md` and `TRACK_A_BRIEF_v1_0.md`
  v1.2, `runtime/INTERIM_RUNTIME_v1_0.md` v1.2, `roles/ROLE_*` v1.3, start prompts v1.3, `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md`
  v1.4, `SUVARNA_DOCUMENT_MAP_v1_0.md` v1.3, `SUVARNA_REVIEW_PACKAGE_v1_0.md` v2.1, `D6_SUVARNA_READER_RUNBOOK_v1_0.md` v1.4.
- A brief never contradicts this plan; if it must, the plan is revised first (§10).

### 0.3 · How to read it

§1–§3 where, by what standard, from where · §4–§5 tracks, gates, contents · §6 operating model · §7–§8 outside
dependencies and decisions · §9–§11 tracking, change, risks.

---

## §1 · End state (unchanged in substance)

### 1.1 · Asset level

An asset is **ELEVATED** when all four hold:

1. Every core gate its layer requires carries a current `PASS`, or an `N/A` computed from a declared registry rule, in
   `asset_certs.jsonl` (§2.1).
2. Every asset-specific addition declared for it is certified the same way (§2.3).
3. It has no open `gap` row **on a core gate or a declared addition**. Rows on non-gate criteria (Cost, Count, Complete,
   Reach) are information, re-keyed `kind: info`, and never block ELEVATED (D3).
4. Its disposition is recorded (keep, integrate, enrich, qualify, consolidate, historical, retire, unresolved).

- **"Current"** means the certification still matches what it was measured against: the writer's commit, the upstream
  certification ids, and the asset's **semantic fingerprint** (arch §12.16: natural-key order, canonical form, declared
  volatile columns excluded; E5.5), with the invalidation watermark at least the ledger ref.
- A retired or consolidated asset with a recorded reason is terminal; the exact function honours it and it stays in its
  wave's denominator as satisfied.
- "Frozen by Nirmāṇa" is not elevated (§3.3).
- **ELEVATED only through the exact function** (E6.3), called by the tracker's own caller (E6.3t). Until then every
  `levels_elevated`/`assets_elevated` detector reads **unknown**, never done.

### 1.2 · Layer level

A layer is **CLOSED** when:

- its layer instance is accepted **before the layer's first wave** (N-7.L0; N-10.L1.i … N-10.L5.i), which lifts the
  PROVISIONAL banner;
- every active asset in it is ELEVATED or terminally dispositioned;
- a **full-layer rebuild** succeeds under the orchestrator and re-measures clean;
- **Strategic Suvarṇa signs the close** (N-10.Lx.c) after a gate review and an independent review (§4.2).

**Full-layer rebuild.** One orchestrator run with `action=rebuild, clear_before=false` over every active asset of the
layer as an asset list, for the canonical chart (L1+) or globally (L0, under the builder's global-L0 grant, N-31).
- **L1–L5:** from scratch for the chart (every writer deletes and re-inserts its own rows), so it also proves Idem.
- **L0:** upserts never delete; the close proof is fingerprint equality before and after, or every row of the diff
  explained; the L0 rebuild drill (E5.7) on the rehearsal database is the evidence that L0 can be regenerated.
- **L2:** only after F3.FK and F3.GUARD read done (§5.3).
- **L3:** an asset list over L3 minus the family set (`FAMILY_ASSETS.json`); the layer closes only once the family
  assets and their L3 readers are certified.
- It is a production-visible action with every charter §6 precondition, the serving guard included.

### 1.3 · Campaign level

Suvarṇa is **COMPLETE** when all six layers are CLOSED; every `[TRANSFERS]` obligation is recorded as pending with its
owner; and the closure report is accepted by **Strategic Suvarṇa after both independent reviewers** (N-CLOSE). The
native is informed and may veto.

### 1.4 · How we will know

| Measure | Today | End |
|---|---|---|
| Assets ELEVATED | 0 of 127 | 127 of 127, or terminally dispositioned |
| Certification records | 0 | one per required gate per asset |
| Open gap rows (core gates and additions) | 799, before the non-gate rows are re-keyed (E6.4) | 0 |
| Gate cells (9 × 127) | 1,143 cells, 0 certified | all PASS or rule-computed N/A |

Gate cells are computed by one coded rollup (E6.2): worst applicable check wins (FAIL > ERRORED > NO_DETECTOR > PARTIAL >
PASS); N/A only when every applicable check is N/A by a declared rule; a gate with no registered check is NO_DETECTOR;
a criterion with `detector: NONE` never reaches PASS.

### 1.5 · Out of scope

- **Astrological correctness** (native ruling 11, 2026-09-25). Pravāha's measurement of the served '3.0' Gochara
  generation (T-cover 32/47 against random controls at 68.6 %; T-FP failing on 8 of 9 adverse classes) is recorded for
  the native in the focus-families document §1.5 as information, not as Suvarṇa work.
- The retrieval and conversation planes; empirical calibration (L5 fills by design); new assets; other charts (N-12:
  canonical only).

---

## §2 · The standard (unchanged in substance)

### 2.1 · The core: nine gates

| Gate | Plain meaning |
|---|---|
| **Ldgr** | Every derived value traces to the facts it came from. |
| **Idem** | A rebuild replaces its own rows; never accretes, never silently fails. |
| **Earn** | Every status or verdict has a detector that could read false. |
| **Null** | Where a value cannot be derived, it is null, never an invented default. |
| **Vocab** | Names and terms conform to the closed vocabularies. |
| **Carr** | Classical sources are carried and reproduced faithfully. |
| **Narr** | Generated text restates cited facts; never re-derives them. |
| **Dens** | What is served is layered by confidence, never flattened. |
| **Build** | The orchestrator can dispatch it, and a rebuild produces the right result. |

- Verdicts: `PASS · FAIL · PARTIAL · NO_DETECTOR · N/A` (plus `ERRORED`). **Only `PASS` or a rule-computed `N/A`
  closes a gap.**
- **N/A is computed, never typed (D3).** Applicability rules are decided once per gate by SS (N-22, with N-13); every
  rule cites its decision id (CODE-49). No reviewer and no agent types an N/A.
- **A reviewer's opinion is not a detector.** A PASS cites a criterion whose detector is not `NONE` and its census run.
- **Today's gap:** no `Null.*` or `Narr.*` criterion; `Carr.D1–D3` without a detector; `Ldgr` structural; `Dens.served`
  structural. E6 builds the generic detectors before J1; per-asset semantic detectors belong to Tracks A/I and gate
  those assets' ELEVATED.
- **"Required, per-asset detector pending"** reads `NO_DETECTOR` (blocks ELEVATED) until the asset's detector lands. After
  J1 the registry changes only by a versioned revision SS decides after an independent review.

### 2.2 · Principles every verdict obeys

Earned signal (§N.8) · honest null (§N.7) · L1 is the authority (§N.5) · rebuild replaces (§N.3) · measured, not claimed.

### 2.3 · Asset-specific additions

Declared in the asset's brief (requirement, detector, why). **SS approves each addition class once (N-11)**; assets
adopt approved classes in their briefs. Additions never weaken a core gate. Candidate classes: grounding tier
(D-GROUNDING), stored salience (D-SALIENCE), one temporal voice (D-TIME), consumer or disposition (D-SERVICE), null with
a reason (decided by D3; adopted per asset).

### 2.4 · Opportunities

`kind: opportunity` rows never block elevation; ruled in batches per layer by SS.

---

## §3 · Starting position (measured 2026-09-28 … 2026-09-30)

### 3.1–3.4 · Assets, ledgers, Nirmāṇa, the register

| Layer | Active | Kept from Nirmāṇa |
|---|---|---|
| L0 · L1 · L2 · L3 · L4 · L5 | 40 · 19 · 23 · 21 · 9 · 15 = **127** | 40 · 19 · 22 · 12 · 0 · 4 = 97 |

- Delta ledger: 857 lines, **799 open gaps** (572 on kept assets). Certification ledger: **0 records**.
- Known defects on kept assets: `bo_upaya` cannot rebuild (R244); six L2 assets rebuild only on the canonical chart
  (R243); `ka_gochara`'s registry names the wrong table (R240); `lel_events` has no writer (R236; N-14.R236 decided).
- Register v2.8: 252 rows, 180 open (4 freeze blockers open: R24, R39, R71, R244; R34, R36 `CLOSED_ON_BRANCH`; 95
  layer-blocking, 71 degrading, 10 cosmetic); tallies computed and detector-checked.

### 3.5 · The engine's own test (freeze criterion)

Frozen when T1–T5 pass in production tooling and the freeze-blocking rows are resolved (§4.2). Last evaluated
2026-09-26: T1 PARTIAL · T2 FAIL · T3 FAIL · T4 PARTIAL · T5 FAIL; not re-measured since three waves of fixes (E1.1 first).
This rule is the freeze rule of record; the register header's broader wording is aligned by E4.1-build-002 (Astra F18).

### 3.6 · The documents

Tiers 1–3 sealed with a reopen agenda ruled (about 32 clause fixes; Track E §6 lists 31, E2.1 reconciles). Tier 4 and the
L0 instance v3.0 are drafts. Five L0 pilot briefs.

### 3.7 · Where the code is

- **Nikaṣa tooling** on `campaign/nikasha-test` (PR #2736), not on `main`; split into fresh branches (N-3; Track E §4).
- **The build engine** on `campaign/nirmana-engine`: 10 engine commits; migrations 1094–1096 unapplied, renumbered into
  1200–1299 at landing (N-26); nothing deployed.
- **Build dispatch**: `POST /api/cockpit/runs`; writers run in the Cloud Run job `brahma-build-pipeline-job`, whose image
  tag is the deployed commit.

### 3.8 · Live work elsewhere and the environment

- **Pravāha (Gochara).** PR #2731 merged 2026-09-30 as `285bff17c`; post-merge deploy in flight (Pravāha item A1.2).
  Pravāha reports migrations 1071, 1072 and 1086 applied; not yet visible in `_migrations_applied` on 2026-09-30 (read as
  `suvarna_reader`; the newest Gochara row is 1150). D-SCOPE / ADK-0029: build for `482012f1` only, never `1c826d5a`.
  D-41: '4.1' an engineering proof, never flipped; the first sound candidate is **'5.0'**. The Gochara final brief is
  Pravāha's sealed doctrine `FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` (native-countersigned, D-BRIEF). Agreed with
  Pravāha: nothing Gochara is certifiable until the registered writer produces '5.0'.
- **Saṅgam, Kṣetra:** no family sessions exist (none has acknowledged anything; Pravāha has never been contacted by
  one). Their code sits on old branches (`consolidation/merge-sangam-stage3`, `codex/l3-kshetra-*`, 2026-09-15/24).
- **Pūrṇa, Jātaka:** separate campaigns with their own migration reservations; they also deploy to `main`.
- **D6** applied 2026-09-29 (`suvarna_reader`, read-only by privilege). **N-25a** applied 2026-09-30 (the two `dbenv`
  files mode 600).
- **`main`'s protection (measured 2026-09-30):** org ruleset 20141220 "main protection (org migration, merge queue)":
  four required checks (TypeScript, Unit Tests, Secret Scan, Governance Gates), pull requests with 0 required approvals, a
  **squash merge queue**, no bypass actors, no force-push, no deletion. Classic branch protection: none.
- **The MSR cascade (measured 2026-09-30, `pg_constraint` closure as `suvarna_reader`):** eight `ON DELETE CASCADE` keys
  into `bodha_msr_signals` from seven tables; four of the eight referencing columns are `NOT NULL`
  (`bodha_contradictions.signal_a_id`, `.signal_b_id`, `bodha_signal_embeddings.signal_id`, `kala_activation.signal_id`).
  Beyond them: `kala_convergence` cascades into `kala_darshana`, `kala_obstruction`, `phala_anchors` (SET NULL into
  `kala_bhavishya`); `phala_anchors` cascades into `phala_pramana`, `phala_sankrama`, `phala_sodhana`,
  `phala_suddha_sodhana` (SET NULL into `phala_mitigation`, `phala_muhurta`). `assert_l2_msr_delete_safe` refuses an MSR
  replacement that any `kala_*` row references through such a key.

---

## §4 · The shape: parallel tracks, one join, dependency waves

```
NOW ─┬─ TRACK E  Engine: tools · build engine · clause fixes · bo_upaya · landing · execution tooling (E5) ·   ─┐
     │           gate detectors (E6) · build identity (E7) · F-3 migration                                      │
     ├─ TRACK A  Analysis, all six layers at once (read-only)                                                   ├─► JOIN J1
     ├─ TRACK F  Gochara: Pravāha (evaluated, then certified) · Saṅgam, Kṣetra: design lanes owned by Suvarṇa;   │   (SS, after an
     │           implementation owner decided at J1 (J1.FO)                                                     │    independent review)
     TRACK I  Implementation, every wave, parallel lanes (from N-24; before J1 to trunk only)  ◄───────────────┤
     TRACK B  Rebuild and certify, one wave per dependency level  ◄───────────────────────────────────────────┘
              wave n = fixes merged by the swarm through the merge gate and deployed → broker dispatch → certify
              ├─ family assets and their readers outside wave completion, certified asset by asset
              ├─ MSR waves need F3.FK + F3.GUARD; cascades rebuilt in wave order, never refused
              ├─ G2 after levels 0–2: loop proven, cost measured (SS)
              └─ layer closes as each layer's last asset certifies (SS, independently reviewed)
     CLOSURE  whole-plane re-measure · [TRANSFERS] hand-over · closure report (SS, both reviewers)
```

### 4.1 · Why this shape

Only data forces order; the engine freezes before anything is certified; one reopen, not six; asset waves, not layer
gates; fix first, walk once (27 levels, a long thin chain); L0 first. (Unchanged from v1.4.)

### 4.2 · The gates

| Gate | Passes when | Who rules |
|---|---|---|
| **N-1 · Go** | every launch item of §5.0b reads done (FI-7's prerequisites) | **the native** (the only approval the native gives) |
| **J1 · Engine freeze** | every item of the J1 checklist below is done | **SS** (N-8), after an independent review of the J1 evidence packet |
| **G2 · Loop proven** | levels 0–2 certified (family set excluded; after F3.FK and F3.GUARD); cost per asset measured; §5.4 confirmed or revised | **SS** (N-9), from measured data; a checkpoint, not a stop |
| **G3.Lx · Layer close** | that layer CLOSED (§1.2) | **SS** (N-10.Lx.c), after a gate review and an independent review |
| **G4 · Campaign complete** | §1.3 | **SS** (N-CLOSE), after both independent reviewers; the native informed |

Every decision gate reads done only through the fail-closed gate evaluator (§9; CODE-36): a typed affirmative outcome
for the exact revision, recorded only while every prerequisite read done. The native may veto any of them.

**The J1 checklist.** One list, the same here, in the tracker (`J1.6` depends on each item) and in the Track E brief.
Items marked (A) carry `acceptance: true` in the plan model and may not use a presence-only detector (LG.8).

| # | Criterion | Tracker item | Proven by |
|---|---|---|---|
| 1 | T1–T5 pass in production tooling on `main` | E1.7 (A) | `scorecard_pass` bound to the inspector blob, the registry revision and a successful CI run (CODE-48) |
| 2 | R24 closed | E1.8 | register row closed |
| 3 | R39 closed: the census's Build checks on `main` all PASS (scorecard `engine_build_checks`) | E3.6 | register row closed; scorecard engine checks validated |
| 4 | R71 closed through the combined reopen | E2.2 | register row closed |
| 5 | R244: the `bo_upaya` fix merged and tested; closed, or DEFERRED only while the withholding holds and the fix PR is merged | E4.2 (A), E4.2r | `ci_job_passed` on the source-order test; `register_rows_state` with the deferred checks |
| 6 | No other freeze-blocking row open | J1.R | `register_freeze_clean` (R24, R34, R36, R39, R71, R244) |
| 6a | R34, R36 closed (build-engine fixes landed, migrated, deployed, proven at runtime) | E1.10 | register rows CLOSED/DONE |
| 7 | Combined reopen: the three agendas decided together; re-seals in order T1 → T2 → T3, each independently reviewed | J1.1a–J1.3 | SS decisions N-4.T1–T3, N-5.T1–T3 |
| 8 | Tier 4 accepted; the L0 instance revalidated and accepted | J1.4, A.L0v, J1.5 | SS decisions N-7.T4, N-7.L0 |
| 9 | The migration range opened; the build engine landed, migrated, deployed | E0.1, E3.2, E3.3, E3.7 | PR merged; landing PRs merged; `migrations_applied`; `deployed_contains` (ancestry) |
| 10 | Nikaṣa tools and register on `main`, inspector tests passing in CI; ledgers cut over | E4.1, E4.1c (A), E4.3 (A) | files on `main`; `ci_job_passed`; `evidence_verified` (both ledgers and the register md5-equal across the cut) |
| 11 | Execution tooling tested on `main`: certification writer, fold script, level-wave script (broker, serving guard, canary), fingerprint rotation, stale-certification detector, census `--assets`, serving-guard inventory, transitive footprint | E5.1–E5.5 (A), E1.9, E5.8, E5.9 | `ci_job_passed` on each test; inventory and footprint files |
| 12 | Gate detectors: every core gate × layer auto-measured, ruled N/A or declared per-asset-pending; rollup coded; ELEVATED exact; non-gate rows re-keyed | E6.3 (A), E6.4, E6.5 (A) | `ci_job_passed`; `ledger_no_open_gap_on`; `registry_coverage` strict (CODE-49) |
| 13 | Build identity provisioned and scoped; the broker's preflight green; the reader applied | E7.3, E5.3, L.10 | Monitor `builder_scope`, `credential_readonly` |
| 14 | Tracks I and B brief decided | J1.0 | SS decision N-24 |
| 15 | One end-to-end wave rehearsed off production; the L0 rebuild drill; the F-3 proof | E5.6 (A), E5.7 (A), F3.PROOF (A) | `evidence_verified` on each drill's acceptance cases |
| 16 | The tracker reads ELEVATED only from the exact function through its real caller | E6.3t (A) | `elevated_interface_ok` (CODE-44) |
| 17 | Implementation ownership of Saṅgam and Kṣetra decided | J1.FO | SS decision |

- **R244 and the J1 loop:** the live `bo_upaya` rebuild waits for its own wave (B.U); J1 takes the merged, tested fix.
- **Row 17 is new in v1.5** (N-28; no family sessions exist for Saṅgam or Kṣetra).

---

## §5 · Track detail

### 5.0 · First items

| Item | State |
|---|---|
| FI-1 relay F-0 and R240 to the Gochara workstream (now Pravāha) | done 2026-09-28 (ADK-0027) |
| FI-2 merge PR #2751 · FI-3 register tallies · FI-4 register rows · FI-5 CURRENT_STATE · FI-6 session names | done |
| **FI-8** the correction notice v1.3, **published on the coordination branch** (no native paste); acknowledged by Pravāha with a note whose detail is exactly `ACK FI-8 notice v1.3` | open; **no longer an N-1 prerequisite**; gates A.L3f |

### 5.0b · Launch readiness — what must be true before N-1

The process to N-1 (N-30): **v1.5 pre-final** (this set) → **parallel independent reviews** by GPT-6 Astra (xhigh) and
Kimi K3 on the same bundle (review package v2.1) → **SS reconciles both** into one disposition → **the final set** (plan
model updated in the same commit) → the native's **N-1**. FI-7 (N-1) waits for every row below.

| Item | Tracker | Owner | State (2026-09-30) |
|---|---|---|---|
| Plan set v1.5 pre-final (this revision), GPT-6 Astra disposition folded | L.19, L.9d | SS | this revision |
| Review package v2.1 and bundle (two reviewers, one bundle) | L.12r | SS | to rebuild (package text done) |
| Independent review of v1.5: GPT-6 Astra (xhigh) · Kimi K3 | L.20a · L.20b | reviewers | to do, in parallel |
| Reconciliation of both reviews · the final set | L.21 · L.22 | SS | to do |
| **Native setup** NS.1–NS.9 (user, broker account, credential lockdown, folder owners, bot and token, ruleset check, Claude token, services, power) | NS.1–NS.9 | **native** (NATIVE_SETUP), verified by the swarm | to do |
| SS preparation before the native starts (NS.0): stop tools running as the native; push and remove the old worktrees; the control checkout; the settings file | NS.0 | SS | to do |
| Control PR E0.2 (the `Suvarṇa path guard` CI job) merged, before NS.6 | E0.2 | SS | to do |
| Tracker and tools at a **pinned control release**, run from `/Users/Dev/suvarna/control` (CODE-36…65 landed) | L.17, LG.7 | SS + code agent | in progress |
| Isolation in place (Monitor `isolation` ok as `suvarna`) · the bot's identity verified · `main` protection v2 | L.16a · L.16g · L.16b | swarm verifies | to do |
| **Durable runtime** (launchd runners, change-triggered passes, fenced queues, per-session heartbeats, watchdog) — no `/loop` (N-34) | L.14 | SS + code agent | to build |
| **SS decision runtime** (answers parks unattended; SLA and escalation) | L.18 | SS + code agent | to build |
| Launch gates LG.1–LG.8, LG.10 (Astra's conditions; disposition §2) | LG.* | swarm drills, SS reads | to do |
| Reader applied (D6) · Track E and A briefs · role and prompt sweep · tracker additions | L.10 · L.11 · L.12 · L.13 | — | done (v1.5 sweep in this revision) |

- **No session starts before N-1** (ENGINE-EARLY-START): the runners are installed idle and start on the N-1 line.
- **E7 auth (E7.1) is post-N-1**, Track E's first landing after E0.1; the native's only post-N-1 act is provisioning the
  builder (NP.1) once E7.1 is deployed.
- **Tracks I and B brief:** drafted by SS once L0's fix designs exist (J1.0d), decided by SS (N-24). Track I starts there.

### 5.1 · Track E — the engine (session "Nikaṣa Engine")

Eight lanes (E0–E7) plus the F-3 lane; detail in `tracks/TRACK_E_BRIEF_v1_0.md` v1.2. Every lane whose output reaches
`main` branches from `suvarna/trunk`; source branches are read or cherry-picked with `-x`.

- **E0 · Control changes (SS, outside the swarm):** E0.1 the deny-list amendment (1200–1299 writable; coordinated with
  the L3 Kāla owner by a coordination note); **E0.2** the CI job `Suvarṇa path guard` (N-38).
- **E1 · Tooling:** measure first (E1.1 scorecard), close R245/R248/R249/R250, R226/R228/R229, R251, R24, R55, R246; census
  `--assets` (E1.9); R34/R36 runtime proof (E1.10); re-prove T1–T5 on `main` (E1.7). 30–50 h.
- **E2 · Clause fixes:** agendas per tier (E2.1, reconciling 31 listed vs 32 ruled), held for the combined reopen; R71
  closes with it (E2.2). 20–30 h.
- **E3 · The build engine:** land the 10 commits (E3.2, squash through the merge queue), migrations renumbered into the
  range (E3.3, N-26), carried items (E3.4), R39 (E3.6), deployed by ancestry (E3.7); C1/C2 alongside Track B (E3.5). 40–70 h.
- **E4 · Landing and `bo_upaya`:** code PR and evidence PR from fresh branches (E4.1, E4.1c); folds before the cut-over
  pushed to `campaign/nikasha-test`; the ledger cut-over (E4.3, md5 equality evidence); the `bo_upaya` fix (E4.2, E4.2r). 10–20 h.
- **E5 · Execution tooling:** certification writer (E5.1); fold script (E5.2); level-wave script through the broker with
  the serving guard, canary, transitive footprint and no dump (E5.3); per-entry fingerprint rotation (E5.4);
  stale-certification detector with the currency contract (E5.5); **wave rehearsal off production** on a local
  PostgreSQL cluster run by the swarm (E5.6); **L0 rebuild drill** (E5.7, replaces the dump, N-29); **serving-guard
  inventory** `SERVING_GUARD_INVENTORY.json` (E5.8, N-33); **transitive footprint** per wave (E5.9). 55–90 h.
- **E6 · Gate detectors (D3):** applicability rules (E6.0, N-22 by SS), generic detectors (E6.1), rollup (E6.2), exact
  ELEVATED (E6.3), the tracker's switch (E6.3t), non-gate re-key (E6.4), registry coverage (E6.5). 50–90 h.
- **E7 · Build identity:** the auth PR (E7.1) with **server enforcement** — dispatch rejects any asset outside scope, any
  family asset (from `FAMILY_ASSETS.json` at the deployed commit), `clear_before`, another chart, a concurrent run, a
  stale `expect_job_image_tag`; two grant forms: the canonical chart and **global L0** (N-31); the preflight route;
  provisioning by the native (E7.2 = NP.1); the Monitor's `builder_scope` through the broker (E7.3). 15–30 h.
- **F-3 lane (N-32):** one migration in the range drops all eight keys into `bodha_msr_signals` and replaces
  `assert_l2_msr_delete_safe` without its refusal (admitted-context check kept; referencing-row counts recorded as build
  evidence). Acceptance: F3.FK (zero keys of any kind), F3.GUARD, F3.PROOF (on the rehearsal database). 6–12 h.
- **Track E total to the freeze:** about **250–450 h** of agent effort (E0 3–6 · E1 30–50 · E2 20–30 · E3 40–70 · E4
  10–20 · E5 55–90 · E6 50–90 · E7 15–30 · F-3 6–12 = 229–398 h build, plus gate review at 25–40 % of the high-risk
  lanes). Re-estimated after E3.2 and after E5.6.

### 5.2 · Track A — analysis, all layers at once (session "Exec Suvarṇa")

Read-only. Per layer: **A.Lxi** census and instance draft (tier gaps; all the harvest and J1 wait for) → **A.Lx** briefs,
dispositions, fix designs (each brief declares the asset's **semantic fingerprint**: natural key, volatile columns,
equivalence policy; F14) → **A.Lxr** revalidation after J1 → **A.Lxa** instance accepted by SS (N-10.Lx.i). **A.L3f**
evaluates Pravāha's sealed doctrine and maps Gochara onto the nine gates (Suvarṇa's own work, never asked of Pravāha),
and evaluates the Track F Saṅgam and Kṣetra briefs. Brief approval: the Steward under G16, otherwise SS batched per layer.
~157 h derivability + 130–250 h briefs + 30–65 h revalidation; per-asset semantic detectors 60–180 h (shared with Track I).

### 5.3 · Track F — the L3 focus families

- **Gochara belongs to the Pravāha campaign.** Its sealed doctrine is the final brief (SEAL-G, decided by citing
  Pravāha's D-BRIEF). Suvarṇa never changes Gochara code or data (charter R8). Its progress is read from Pravāha's tracker
  by `peer_tracker_item` (CODE-54): F1.G ← Pravāha B0.2; F2 ← PR #2731 merged; F2.1 ← Pravāha **J2** ('5.0' gated and
  retrodicted); F2.3 ← A1.2 (deploy verified); F2.4 ← A6.1 (flip of `482012f1` to '5.0' with soak, gated on Pravāha's
  N-FLIP); F3.Ga ← A5.3 (registered writer); F3.Gb ← A5.6 ('5.0' built for `482012f1`); F3.Gc ← A6.2 (century writer
  retired; registry and seed aligned). **F2.5 (the `1c826d5a` switch) is dropped** (Pravāha D-SCOPE). Each campaign
  records its own rulings in its own log; Suvarṇa's log cites Pravāha's ids for Gochara facts.
- **Saṅgam and Kṣetra: Suvarṇa owns the design now (N-28).** Architect-led lanes write their final briefs on the tier-4
  template, with Pravāha's consumer contract `L3_FAMILY_COORDINATION_v1_0.md` as an input (F1.Sd, F1.Kd), independently
  reviewed, sealed by SS (SEAL-S, SEAL-K). Rulings F-1, F-2, F-4, F-6 are decided by SS from those lanes (the old
  delegations stay open until then). **J1.FO, at J1:** if a family session has acknowledged the notice (FI-8) or shown
  commits on Saṅgam or Kṣetra branches, that session owns implementation and R8 covers it; otherwise the swarm implements
  them as ordinary Track I/B work (R8 then covers Gochara only). The family prompts are kept for a session the native may
  open; the Gochara prompt is retired.
- **How a family asset is certified (D2).** Its own orchestrator rebuild (substep plan completed; never a cutover
  script) counts as the Build exercise; Suvarṇa's independent re-measure writes the certification (B.FG, B.FS, B.FK).
  **No Gochara certification before '5.0' is produced by the registered writer** (F3.Gb) and the century writer retired (F3.Gc).
- **Waves and families.** The family set and its readers live in `FAMILY_ASSETS.json`, frozen at J1 and pinned by hash in
  every wave item (CODE-45). They are excluded from wave completion; each reader waits asset by asset
  (`waiting_on_family`) and is certified under B.FR.L3/L4/L5.
- **F-3, decided by principle (N-28/N-29), concrete form N-32.** Derived rows are regenerable: the L2→L3 cascade is
  handled by rebuilding in wave order, never by refusing rebuilds. All eight keys into `bodha_msr_signals` are dropped
  (target `no_fk`); the refusal in `assert_l2_msr_delete_safe` is retired. Signal ids are deterministic (the
  `test_bo_*_signal_identity.py` tests), so unchanged signals keep their ids and references; changed or removed signals
  leave dangling references until the downstream asset rebuilds in its own wave (staleness propagation marks it; the
  serving guard covers the gap); `msr_referential_integrity.py` measures them after each wave. Family downstream
  (`kala_convergence`) is notified by lease note (charter R8's cascade exemption). **Alternative stated for the
  reviewers:** ON DELETE SET NULL on all eight — rejected: four of the eight referencing columns are NOT NULL (§3.8), so
  it needs nullability changes, and nulled references are served as meaningless rows. **Owner:** Track E, coordinated by
  lease with Saṅgam's owner (Track F's lane until J1.FO).
- **The coupling that binds Suvarṇa:** no L2 MSR asset is rebuilt until F3.FK and F3.GUARD read done; B.W0 and G2 wait
  for them (W0 holds `bo_sudarshana` and `bo_vargottama_dhana`). Saṅgam is certified only after its L2 upstreams (B.W2).
- **Hand-back:** SS records HB-G/HB-S/HB-K when a family's owner closes.
- **Kṣetra on the L5 critical path** (`mi_bhara`, `mi_sankalpa`): SS decides N-21 (accept, or `qualify` pending Kṣetra).

### 5.4 · The per-asset lifecycle (Tracks I and B)

1. **Brief approved:** the Steward under G16 (keep, enrich, qualify within approved classes); SS for every other
   disposition, output change or new addition class, batched per layer. Before J1 approval is provisional and covers only
   tier-independent designs.
2. **Implement** in a lane (from N-24; before J1 only tier-independent designs, to trunk).
3. **Gate review**, then merge to `suvarna/trunk`.
4. **Land:** the wave's fixes go to `main` from a landing branch cut from `origin/main`, **merged by the swarm through
   the merge gate** (N-38) into the squash merge queue; the deploy follows. Logical waves are kept for reporting; a wave
   may land as several smaller dependency-closed groups (Astra Q18), each with its own LANDING.json.
5. **Wait for the wave:** every upstream asset certified and current; every asset at this level deployed (the PR's merge
   commit an ancestor of the running commit; writer hashes equal).
6. **Rebuild** through the broker, one asset-list run over the level's non-family assets (L0 levels under the global grant,
   N-31), with every charter §6 precondition including the serving guard.
7. **Re-measure and certify.** Gaps close only on PASS or rule-computed N/A.
8. **Later upstream change:** E5.5 invalidates; the asset is re-measured and rebuilt only if its semantic fingerprint
   changed. **Bounded re-walks:** at most two per layer inside a layer's acceptance epoch before SS reviews the cause (F14).

| Layer | Specifics |
|---|---|
| L0 | Global. Four levels (24, 11, 4, 1 assets): four builder dispatches under the global grant (B.L0.0–B.L0.3), each with an impact statement, a rebuild plan (proved by E5.7), pre/post fingerprints and a diff (§6.4b). |
| L1 | Canonical chart only (N-12). |
| L2 | `bo_upaya`'s live proof (B.U). Waves with an MSR writer (W0, W1, W2) wait for F3.FK and F3.GUARD. |
| L3 | Gochara certified after '5.0'; Saṅgam and Kṣetra per J1.FO. `kala_field` (10.98 M rows) is the heaviest cost. |
| L4 | Nothing kept from Nirmāṇa; in the transitive footprint of `kala_convergence` and `phala_anchors`. |
| L5 | `lel_events` declared no-writer (N-14.R236); `mi_bhara`, `mi_sankalpa` per N-21. |

### 5.5 · Closure

Whole-plane re-measure (1,143 cells); `[TRANSFERS]` handed over; leftovers retired (R219); closure report decided by SS
after both independent reviewers (N-CLOSE).

---

## §6 · Operating model

### 6.1 · Sessions and flow

```
Strategic Suvarṇa (decides, records, briefs; unattended decision runtime L.18) ──brief──► Nikaṣa Engine / Exec Suvarṇa
      ▲                                                                                        │
      └────────────── parks, findings, reports ◄──────────────────────────────────────────────┘
   the native: informed by the digest and dashboard; veto at any time; N-1; physical setup; scope changes
```

- **SS** decides every campaign question with a recorded rationale (N-28), within the SLA of §6.7; decisions that need an
  independent review first say so (§4.2). SS never dispatches builds or runs lanes.
- **Execution sessions** run packets: build → report → gate review → corrections → fold → land. They never change this
  plan; they raise findings and park questions to SS.
- **Isolation** (N-25, decided; N-36, N-37): the swarm runs as the macOS user `suvarna`, with its own settings, GitHub
  identity and Claude token; the decisions log, holds and control code are native-owned and read-only to it; the builder
  credential is reachable only through the broker. Details: arch §2.4; charter §13.

### 6.2 · Roles and models

Opus 5.5 where judgement decides (Conductor, Steward, Architect, gate reviewers, SS); Sonnet 5 for volume (analysts,
builders); scripts for bookkeeping. Effort medium by default; high for algorithm design, high-risk reviews, reopen
drafting, the Steward's classifications and writer or ledger changes; low for mechanical roles. Independent reviewers
(GPT-6 Astra, Kimi K3) for plans, re-seals, J1, layer closes and the closure.

### 6.3 · Discipline

Packet, gate, fold · proof that could fail (failing-first test plus mutation run) · one row per commit, `git commit --
<paths>` · fingerprints last · ledgers only by `--emit-gaps` with the withholding list or a reviewed idempotent migration
script · computed tallies · per-packet scratch folders.

### 6.4 · Write authority

- **Code changes:** PRs to `main` from landing branches cut from `origin/main`, **merged by the swarm's GitHub identity
  only through `merge_gate`** (N-25b, N-38): every required check green on the head SHA, a gate-reviewer ACCEPT recorded
  for that SHA, the path guard clean, no active hold, the decisions log re-read. The server holds the rest: org ruleset
  20141220 (required checks including `Suvarṇa path guard`, squash merge queue, no bypass); the bot has Write only. A
  post-merge audit catches a bypass (hold, then a revert PR). Control-plane PRs (E0.1, E0.2, the control release) are
  SS's, outside the swarm. A native-opened family session merges under the native's own identity, outside this model.
- **Deployed means contains:** the PR's merge (squash) commit is an ancestor of the running commit, and the writer files
  at the running commit hash to the packet's recorded values.
- **Schema and data changes:** migrations only (1200–1299, N-27), applied by the deploy pipeline and verified read-only.
- **Builds:** the orchestrator only, through the broker (N-36), for the canonical chart or global L0 (N-31); never
  `clear_before`; never hand-written SQL.
- **Destructive operations (N-29):** a rebuild plan, a serving guard (§6.4c) and a recorded pre-operation fingerprint
  and row counts, and an SS decision. No native approval; no dump.
- **Credentials:** the reader (`suvarna_reader`) through the approved wrappers; the builder only through the broker;
  nothing else. Rotation is the native's (NATIVE_SETUP §2).

**6.4b · L0 wave safety (N-29, N-31).** L0 tables are global: an L0 wave changes every chart's inputs while only the
canonical chart's L1+ is rebuilt. Every L0 wave: an **impact statement**, measured not asserted (L0 assets whose output
changes; per other chart — `1c826d5a`, `cb73cd3d` today — the downstream closure now served from stale L0 inputs,
disclosed through the serving notice); a **rebuild plan** (the orchestrator runs that regenerate the affected rows, proved
by the E5.7 rebuild drill); pre/post semantic fingerprints and a row-level diff on the natural keys, retained to campaign
close; dispatch by the builder through the broker under the global grant. **Reversal:** hold; rebuild from the previous
code (revert the landing through the merge gate, redeploy, re-dispatch) — the rows are regenerable, so no dump is taken.

**6.4c · The serving guard (N-33).** Served output is never wrong or partial without an authority switch or a disclosed
maintenance window. For every served table a wave writes: **(a)** build the candidate, verify, switch authority, reverse
on failure (the Pravāha pattern; L2 producer generations); or **(b)** a disclosed maintenance window: a serving notice
the served envelope carries, a serving canary (golden reads of the served MCP tools for `482012f1`) before and after,
the window closed only on a passing canary, an unexplained difference triggering the reversal. The mode per table is in
`SERVING_GUARD_INVENTORY.json` (E5.8); a table not listed is not written. Charter §6 precondition 8.

### 6.5 · Environment

Database through the Cloud SQL proxy on 5433 as `suvarna_reader`; the Mac on AC power, lid open, no automatic updates
(NS.9); one census at a time through `census_run`; one worktree per lane; never the main checkout.

### 6.6 · Effort, capacity and calendar (Astra F17)

- **Agent effort:** Track E ~250–450 h (§5.1); launch code (CODE-36…65, runtime, SS runtime) ~60–110 h; Track A ~317–472 h;
  Track F Saṅgam/Kṣetra design ~30–60 h (implementation, if J1.FO gives it to Suvarṇa, is Track I/B work; Kṣetra alone was
  priced at 5–9 weeks); Tracks I and B 10²–10³ h including 60–180 h of per-asset detectors. **Review effort is included**
  at 25–40 % of build effort for high-risk packets and ~15 % otherwise.
- **Throughput assumptions (to be measured):** up to 6 analysts, 4 builders, 3 reviewers, 2 architects in parallel, limited
  in practice by review capacity and the one-census lock; a merge through the queue plus deploy ≈ 45–90 minutes; an SS
  decision under 1 hour; an independent review 1–2 days.
- **No native latency.** The native's acts are the setup before N-1 and NP.1 after E7.1 (NATIVE_SETUP).
- **Calendar = critical-path execution + deploy waits + independent-review waits + rework.** No dated range is published
  until it can be measured: **reforecast after the E5.6 rehearsal** (first real per-packet and per-wave costs) and **at G2**.
- **Hours are agent effort**, not calendar time; the 27-level build chain does not compress.

### 6.7 · Runtime (N-34)

- **Durable from launch, no `/loop`.** Each execution session's Conductor runs as a launchd service of the `suvarna` user
  (NS.8): a runner performs a cheap deterministic readiness check and starts one stateless `claude -p` pass **only when
  there is actionable change** (new events, ready items, decisions, failures, due timers), backing off to 30 minutes when
  idle (Astra Q17); one fenced owner per queue; a heartbeat per session; the Monitor's watchdog relaunches a stalled runner
  (three an hour, then a hold). Lanes start only through the lane launcher (atomic claim, caps, duplicate refusal).
- **SS's decision runtime (L.18)**, as the native's account: a pass starts on a new `decision requested` event or a gate
  whose prerequisites all read done; SLA under 1 hour; a park older than 24 h is escalated in the digest; older than 72 h the
  native is notified (information only).
- **Billing:** the native's subscription until G2 (N-23), through the swarm's own Claude token; spend metered per pass from
  the first pass (CODE-59); an API key revisited at G2 from measured data.

---

## §7 · Dependencies outside the plan

| Dependency | Owner | Needed by | Status |
|---|---|---|---|
| Build engine landed and deployed | Track E | J1 | 10 commits, no PR |
| Migration range open (deny-list amendment) | SS control PR E0.1 | every Suvarṇa migration | N-27 decided; PR to do |
| The F-3 migration | Track E | W0 and every MSR wave | to write |
| Native setup | the native (NATIVE_SETUP) | N-1 | to do |
| Builder provisioning (NP.1) | the native | Track B | after E7.1 |
| Pravāha: '5.0', flip, century writer retired | Pravāha | Gochara certification (B.FG); Saṅgam/Kṣetra rebuild on the new generation | in progress (J2 waiting) |
| `main` protection (ruleset 20141220 + path guard) | native adds the check (NS.6) after E0.2 | swarm merges | ruleset exists; check to add |
| Other workstreams deploying to `main` | Pūrṇa, Jātaka, Pravāha | — | coordination by lease; ancestry, never equality |

**Coordination rule:** before Suvarṇa touches an asset another live workstream is changing, the two agree an owner by
lease (arch §12.4). Cascade and staleness effects of a granted rebuild on another owner's assets are notified the same
day (charter R8). The pre-wave fingerprint and E5.5 are the tripwires for others' changes.

---

## §8 · Decisions

**The log is authoritative:** `$SUVARNA_HOME/authority/DECISIONS.jsonl`, appended only through
`python -m suvarna_tracker.decide`, only by SS, each line with a typed outcome, the revision decided and a rationale. As
of 2026-09-30. "SS v1.5" means ruled by SS in this plan revision and **recorded in the log with the final set** (the
commands are listed in the reconciliation).

### 8.1 · Decided

| ID | Decision | Source |
|---|---|---|
| NIRMANA-SUPERSESSION, FI-2 | Nirmāṇa set aside; PR #2751 merged | native |
| N-2 · N-3 · N-6 · N-17 · N-18 | engine under the Nikaṣa session · split #2736 · fix `bo_upaya` now · family relation (history; Gochara now Pravāha) · folder and branches | native |
| N-15 · N-19 · N-20 · CHARTER-AMEND-A-C | no ceilings · charter v1.1/v1.2 · credential file | native |
| INDEPENDENT-REVIEWER · ENGINE-EARLY-START | Astra at xhigh · no session before N-1 | native |
| D1–D6 | builder identity (D1's native L0 dispatch superseded by N-31) · family certification · gate detectors · L0 safety (D4's dump superseded by N-29) · durable runtime · reader login | native (reconciled) |
| F-0 · F-5 | deploy before switch · full century | native |
| **N-28 · N-29 · N-30** | native out of the loop · data regenerable, safety priorities · process to N-1 | native, 2026-09-30 |
| N-25 · N-25a · N-25b · N-26 · N-27 · N-14.R236 · N-23 | separate user · dbenv mode 600 · merge model · renumber 1094–1096 · range 1200–1299 · `lel_events` no-writer · subscription to G2 | SS under N-28 |
| F-3 | cascades handled by rebuilding in wave order; concrete form N-32 | SS under N-28/N-29 |
| **N-31 … N-38** | builder L0 grant · F-3 form · serving guard · durable runtime and SS runtime · hold ledger and veto · build broker · authority and control out of reach · merge gate | SS v1.5 |
| **N-12 · N-16 · G16 · SEAL-G** | canonical chart only · leave Nirmāṇa's record · Steward brief approval in force from N-1 · Gochara brief = Pravāha's sealed doctrine (D-BRIEF) | SS v1.5 |

### 8.2 · Open, in the order needed

| ID | Decision | Decider | When | Recommendation |
|---|---|---|---|---|
| **N-1** | Go on the final set | **native** | after §5.0b | — |
| N-22 (with N-13) | Per-gate applicability rules | SS | before E6.5 | start from D3's defaults |
| N-4.T1–T3 | The three reopen agendas, together | SS | after E2.1 and A.H | as one batch |
| N-5.T1–T3 | Re-seals, in order | SS + independent review | after redlines | — |
| N-7.T4 · N-7.L0 | Tier 4 · the L0 instance | SS | end of E2 | — |
| N-24 | Tracks I and B brief | SS | before J1 | — |
| J1.FO | Implementation owner of Saṅgam and Kṣetra | SS | at J1 | per §5.3 rule |
| N-8 | Engine freeze | SS + independent review | J1 | — |
| N-11 | Addition classes | SS | before L2 briefs | per class |
| N-14 | Data findings owned elsewhere (R219; R240 with Pravāha) | SS | per layer | — |
| F-1 · F-2 · F-4 · F-6 | Kṣetra W7/interim · Saṅgam keep or retire · Kṣetra classes · Saṅgam Mode D | SS from Track F's lanes (or a claiming session's recommendation) | before each family's rebuild | — |
| SEAL-S · SEAL-K | Saṅgam and Kṣetra final briefs | SS + independent review | when drafted | — |
| N-21 | Kṣetra on the L5 path | SS | before L5 briefs | — |
| N-9 | G2 | SS | after B.W0 | — |
| N-10.Lx.i · N-10.Lx.c | Layer instances · layer closes | SS (closes + independent review) | per layer | — |
| HB-G · HB-S · HB-K | Hand-backs | SS | when an owner closes | — |
| N-CLOSE | Closure report | SS + both reviewers | end | — |
| (scope) | Any added chart, added or dropped asset, end-state change | **native** | if ever | SS brings a recommendation |

---

## §9 · Tracking

The live view is the real-time tracker (arch §11): the plan model, the event log, the decisions log and detectors. Rules:

- **One fail-closed gate evaluator** (CODE-36; Astra Q21): a `done_by: decision` item is done only for a typed affirmative
  outcome on the exact revision, by an allowed writer, recorded while every prerequisite read done; a corrupt log line
  blocks; an item event never completes a decision item.
- **Detectors decide done** wherever one exists; an event that disagrees is a conflict. A detector whose type does not
  exist yet (the CODE-44, -47, -50 types), whose spec is unpinned (`pinned_by`) or whose evidence is stale reads
  **unknown**, never done (CODE-51).
- **Acceptance items never use presence-only detectors** (the plan-model lint, LG.8).
- **Weekly scorecard**, every figure with its query: assets ELEVATED per layer; certifications and invalidations; open gaps
  by gate and layer; open register rows by severity; T1–T5 until J1; effort and **spend** against estimate; SS decision
  latency and park age.

---

## §10 · Adapting the plan

Findings change briefs, not the plan, unless they change a track, a gate, the standard or the end state. Triggers: an
estimate missing by more than half; an unmeasurable criterion; a new defect class; a scope decision. **How:** SS drafts the
change with a changelog entry and the plan-model change in the same commit, has a change to a gate, the standard or the
charter independently reviewed, records the decision, bumps the version. A scope or end-state change goes to the native.
An execution session that finds the plan wrong stops that packet and reports.

---

## §11 · Risks

| Risk | Signal | Mitigation |
|---|---|---|
| **An unearned green becomes permission** (Astra's largest risk) | a gate or item reads done without its evidence | One fail-closed gate evaluator (CODE-36); typed decisions; acceptance items never presence-only (LG.8); stale evidence reads unknown (CODE-51); launch gates proven by drills (LG.1–LG.10) |
| SS decides wrongly with nobody checking (N-28) | a decision later reversed | Recorded rationale on the dashboard; independent reviews on re-seals, J1, layer closes and closure; the native's veto; decisions typed and revision-bound |
| The swarm acts outside its grant | a merge, a foreign credential, a forged decision, a cleared hold | OS separation (`suvarna`, `_suvarnabuild`), native-owned authority and control (N-36, N-37), append-only holds (N-35), server-side scope (E7.1), merge gate and path guard (N-38); Monitor `isolation`, `decision_log_integrity`, `merge_audit` |
| A swarm merge breaks `main` for others | another workstream's CI or deploy fails after a Suvarṇa merge | Required checks and merge queue; path guard; revert through the merge gate is the safe direction; lease notifications |
| Served output wrong or partial during a wave | the serving canary differs | Serving guard per table (N-33); candidate/switch or disclosed window; reversal by rebuild |
| Cascade surprises | rows deleted beyond the write set | Transitive footprint per wave (E5.9); rebuild in wave order; notification to owners |
| L0 wave affects other charts | other charts serve stale derived data | Impact statement, disclosure, rebuild plan; canonical only (N-12) |
| The engine stage never ends | E2 or E6 grows | Closed agendas; one J1 checklist; per-asset detectors outside J1 |
| Stale certification | an upstream change after certification | Semantic fingerprints, generations, invalidation watermark; bounded re-walks |
| The runtime dies unattended | no heartbeat | launchd KeepAlive, watchdog, hold and park; state in files and git |
| Pravāha slips | J2 or A6.1 stays open | Gochara readers wait asset by asset; nothing else waits on Gochara |
| Saṅgam/Kṣetra ownership unclear | no session claims them | J1.FO rule; Suvarṇa owns the design meanwhile |
| Spend grows unnoticed | tokens per pass rise | Metered per pass from the first pass; change-triggered passes; reported weekly; G2 revisit |
| A committed permission blocks the campaign | a migration edit denied | E0.1 before E7.1; never step around a deny (P13) |

---

## Appendix A · Fact baseline and sources

| Fact | Value | Source |
|---|---|---|
| Active assets | 127 | `asset_registry` where active, not dead, by layer |
| Nirmāṇa freezes | 98 (97 active); 72 under definition t0 | `nirmana_evidence…asset_frozen` |
| Delta ledger · open gaps · kept-asset gaps | 857 lines · 799 · 572 | `asset_gaps.jsonl` on `campaign/nikasha-test` |
| Certifications | 0 | `asset_certs.jsonl` |
| Register | 252 rows; 180 open; freeze blockers R24, R39, R71, R244; R34, R36 `CLOSED_ON_BRANCH` | register v2.8 |
| Build engine | 10 engine commits; 1094–1096 unapplied | Track E §3.1; `_migrations_applied` |
| Wave composition | W0 65 · W1 13 · W2 14 · W3 17 · W4 9 · W5 9; L0 by level 24/11/4/1 | `dag_levels` over `asset_registry.depends_on` (2026-09-29) |
| MSR keys and nullability; transitive closure | 8 CASCADE keys from 7 tables; 4 NOT NULL; closure as §3.8 | `pg_constraint`, `pg_attribute`, recursive closure, as `suvarna_reader`, 2026-09-30 |
| `assert_l2_msr_delete_safe` | plpgsql, SECURITY DEFINER; refuses when a cross-layer key references the replaced scope | `pg_proc` (2026-09-30); caller `bodha_writers/_idempotency.py` |
| Signal ids deterministic | emitters tested for no `uuid4` | `test_bo_{laksana,arudha,sudarshana}_signal_identity.py`, `test_bo_shared_msr_signal_identity.py` |
| `main` protection | ruleset 20141220: 4 required checks, 0 approvals, squash merge queue, no bypass; no classic protection | `gh api …/rulesets/20141220`, `…/branches/main/protection` (404), 2026-09-30 |
| Repository | `Marsys-Technologies/Madhav`, org-owned, public | `gh repo view`, 2026-09-30 |
| 1200–1299 free | 0 files, 0 PRs, 0 of 883 `_migrations_applied` rows | sweep 2026-09-30 |
| Pravāha | PR #2731 merged as `285bff17c`; N-BRIEF, A1.1, B0.2 done; A1.2 ready; J2, A5.6, A6.1, A6.2 waiting | `git log origin/main`; `http://127.0.0.1:8766/api/state`, 2026-09-30 |
| Pravāha '3.0' measurement | T-cover 32/47 vs controls 68.6 %; T-FP 8/9 FAIL at 99.87 % | `pravaha/measurement/BASELINE_3_0_v2_1.md` |
| World-readable secret-like files under the native home | about 20 (`.env*`, `*key*.pem`), before NS.3 | `find … -perm -o=r`, 2026-09-30 |
| Claude Code | 2.1.239 (native install); `setup-token` available | `claude --version`, `claude --help` |

## Appendix B · Glossary

Asset · gate · gap row · certification record · layer instance · asset brief · emit · withholding list · family set ·
full-layer rebuild (§1.2) · **builder identity** (dispatch-only account; two grants: canonical chart, global L0) ·
**build broker** (the only path to the builder credential, N-36) · **merge gate** (the only path to a swarm merge, N-38) ·
**serving guard** (N-33) · **hold ledger** (N-35) · **control checkout** (native-owned, pinned control release, N-37) ·
**semantic fingerprint** (arch §12.16) · [TRANSFERS].
