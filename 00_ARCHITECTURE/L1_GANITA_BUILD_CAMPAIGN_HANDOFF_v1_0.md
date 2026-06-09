---
artifact: L1_GANITA_BUILD_CAMPAIGN_HANDOFF_v1_0.md
canonical_id: L1_GANITA_BUILD_CAMPAIGN_HANDOFF
version: 1.0
status: CURRENT
authored_by: Claude (Cowork) 2026-06-09
authored_for: native (Abhisek Mohanty)
purpose: >
  Self-contained planning/orchestration handoff for the L1 Gaṇita (chart-facts) layer build,
  continuing from the just-sealed L0 Brahmagyan campaign. The receiving conversation is a
  Cowork planning surface: it runs a Nirīkṣaka current-state audit, reconciles the three
  divergent L1 representations that exist today, then authors the executable Antigravity
  briefs + pasteable kickoffs that build, deploy, and prove the L1 layer on the fresh Brahma
  prod DB. Execution happens in Claude Code in Antigravity — never as chat bullets.
read_in_combination_with:
  - CLAUDE.md (project root — mission + §C mandatory reading)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (you-are-here; read top block + latest changelog)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the Gate-0→3 swarm + Contract Registry)
  - 00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md (CRITICAL/HIGH operator queue — read before any deploy)
  - 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF_v1_0.md (the pattern this mirrors)
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (the L1 asset catalog, layer:"L1")
supersedes: none (new artifact)
changelog:
  - v1.0 (2026-06-09): Initial handoff. Reconciles the WS2 worktree L1 build, the L0 registry
    pattern (asset_registry + asset_runner), and the legacy A1–A22 charter into one
    Nirīkṣaka-first plan. Grounds every claim in observed git/disk state as of main HEAD
    95d2e4c0 (2026-06-09).
---

# L1 Gaṇita Build Campaign — Cowork Handoff v1.0

## §0 — How to use this document

This is the **first message context** for a fresh Cowork conversation. Cowork **plans**;
Claude Code in Antigravity **executes** ([[feedback-cowork-vs-antigravity-split]]). Your job
in the receiving conversation is to produce **executable `.md` briefs** (CLAUDECODE_BRIEF
format) and **pasteable kickoff prompts** — never chat bullets the native must hand-translate.

Order of work in the receiving conversation:

1. Open per CLAUDE.md §C mandatory reading. Verify state from `CURRENT_STATE_v1_0.md` top
   block + `git log`, **not** CLAUDE.md §F (frozen/stale — [[feedback-verify-state-not-claude-md]]).
2. Run the **Nirīkṣaka current-state audit** (§D) — this is the load-bearing first step,
   because three partial/divergent L1 representations exist (§C). Do not author build briefs
   before the audit resolves which representation is canonical.
3. Seed the L1 slice of the **Asset Contract Registry** (§E) from the audit.
4. Author the per-asset / per-stream Antigravity briefs + kickoffs (§F).
5. Every acceptance criterion is tagged `[verify-against: prod]`
   ([[feedback-ac-must-verify-target-environment]]).

## §A — Where the project is (reconciled from disk, 2026-06-09)

- **Active macro-phase:** M6 INCOMING. M5 closed. (CLAUDE.md §F is stale — confirm against
  `CURRENT_STATE_v1_0.md`, which is at **v5.69**, last session `BRAHMA-INFRA-PROVISIONING`,
  2026-06-03.)
- **Architecture:** Project BRAHMA re-architecture, sealed at design phase 2026-06-02
  (`MARSYS_MASTER_ARCHITECTURE v2.1`). External lexicon LOCKED: **Brahmagyan · Gaṇita · Bodha ·
  Kāla · Phala · Mīmāṃsā** = internal L0 · L1 · L2 · L3 · L4 · L5. No "L0–L5" shown externally.
  **L1 = Gaṇita = the chart-facts layer this campaign builds.**
- **Infrastructure was wiped to a clean Brahma baseline** (CURRENT_STATE v5.69, 2026-06-03):
  `DROP SCHEMA public CASCADE` then `001_baseline.sql` → **46 base tables**, pgvector 0.8.1,
  Cloud SQL right-sized to `db-g1-small`, `life_events=0` (expected). Firebase Hosting now
  serves `madhav.marsys.in`. **This is the prod target. Anything built before 2026-06-03 in a
  worktree is presumed absent from this DB until proven present.**
- **L0 Brahmagyan campaign SEALED** ([[project-l0-brahmagyan-campaign-state]]) via PR #231
  (merge 2026-06-09 — verify `gh pr view 231 --json mergeCommit,state`). 11 global classical
  assets built deterministically, ZERO LLM (except `bg_texts` embeddings), Vimarśaka-Ω 6/6
  integrity PASS. `bg_ephemeris` 825,084 rows (PR #228/#229). **L1 builds on top of L0.**
- **PyJHora is the engine** ([[project-pyjhora-is-the-engine]], native decision 2026-06-01).
  `natal_engine/` deleted; `pyjhora_adapter/` (PyJHora==4.8.6) is canonical. Verification is by
  **internal consistency + FORENSIC grounding only — NO JH-parity oracle anywhere**
  ([[feedback-no-jh-parity-anywhere]]).
- **Native chart exists in prod:** `362f9f17-95a5-490b-a5a7-027d3e0efda0`, built 2026-06-01
  (build_id `a494ec15`) on PyJHora. All 65 `(category × ayanamsha_id)` `chart_facts` cells
  non-zero; panchanga FORENSIC spot-check 5/5. **Caveat:** `forensic` asset is still a 0-row
  stub (Stream F, see OPERATOR_ACTIONS_PENDING). This chart is the build/verify target.
- **main HEAD at handoff:** `95d2e4c0`.

## §B — The native (subject) — invariant

Abhisek Mohanty, born **1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India**. Canonical L1
chart facts live in the **`chart_facts` DB table** rendered via
`platform/src/lib/ganita/forensic_render.ts` (`canonical_id: FORENSIC`). FORENSIC v8.0 cold
benchmark at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md`. **No session
re-derives the foundational chart** — it is computed by the PyJHora engine and grounded
against the FORENSIC anchors below.

FORENSIC grounding anchors (the L1 acceptance bedrock — every L1 writer asserts against these):
Sun in **Capricorn**; Moon nakshatra **Purva Bhadrapada** (lord Jupiter); Lagna **Aries**
(MET.LAGNA.SIGN = Aries per FORENSIC v6.0 — *not* Scorpio, a known trap); Tithi **Shukla
Tritiya**; Vara **Ravivara**; Yoga **Shiva**; Karana **Garaja**. *(These 7+ anchors are the
WS2 build's FORENSIC gate, confirmed 7/7 PASS in the worktree — see §C.1.)*

## §C — The three divergent L1 representations (why audit comes first)

The dominant fact about L1 is **not** that it is unbuilt — it is that **three partial,
non-identical L1 representations exist**, and no single one is both complete and live on the
new prod DB. The receiving conversation's first job is to reconcile them. Do **not** assume
any one is canonical without the audit.

### C.1 — The WS2 worktree build (rich, tested, NOT on main)

Branch **`feature/ws2-depth-build`**. Session `l1-ganita` (Smṛti close
`00_ARCHITECTURE/CONDUCTOR/ws2/smriti/l1-ganita-pass.md`, 2026-06-05) reports **7 L1 assets
built, 192 tests GREEN, FORENSIC 7/7 PASS**, PyJHora/pyswisseph engine. Writers live under
`platform/python-sidecar/brahmagyan/ganita/` (engine.py, graha_sthana_writer.py, l1_dashas.py,
l1_divisionals.py, l1_positions.py, l1_sensitive_points.py, l1_strength.py,
l1_panchanga_birth.py, l1_engine_check.py, gate.py) and
`platform/python-sidecar/brahma/l1/ganita/` (divisionals_writer.py + tests).

WS2 asset inventory (from the Smṛti pass — **achieved vs floor**):
`ganita.engine` (9 grahas, smoke GREEN) · `ganita.positions` (50 = 5 ayanamsha × 10 bodies) ·
`ganita.divisionals` (160 = 16 × 10) · `ganita.dashas` (6560 Vimshottari-to-Sukshma + ~70
Yogini/Kalachakra/Ashtottari) · `ganita.strength` (115 = 7 shadbala + 96 ashtakavarga + 12
bhava) · `ganita.sensitive_points` (27 = upagrahas + special lagnas + sahams + arudhas) ·
`ganita.panchanga + facts_store + forensic_render` (FORENSIC gate 7/7).

**Critical merge-state finding** (verified `git merge-base --is-ancestor`, 2026-06-09):
representative WS2 commits `7fa3ae3e`, `77f240e6`, `4416a880` are **NOT on `origin/main`**.
This is the exact seal-vs-prod divergence class from [[feedback-ac-must-verify-target-environment]]
and [[feedback-phase-sealed-needs-merge-verification]]: built+tested in a worktree, never
landed on main, therefore **certainly not on the post-2026-06-03 wiped prod DB**.

### C.2 — The L0/registry pattern actually on main (the proven, working spine)

Some L1 Gaṇita pieces **are** on main, landed via the Stream G / PyJHora arcs, and they follow
the **registry-driven orchestrator pattern** the L0 campaign proved out:

- `platform/migrations/brahma_ganita.sql` — `ganita_positions` + `ganita_dashas` tables
  (on main via `b70d906d`). Note the per-asset gate language in its header:
  *"GA-1-2 positions gate: astronomical sanity + internal structural anchors (NOT FORENSIC
  parity); GA-1-4 dashas gate: Vimshottari mathematical dates (NOT FORENSIC dates)."*
- `platform/migrations/002_ganita_divisionals.sql` (on main via `a3083da0`).
- `platform/migrations/174_ganita_graha_sthana.sql` (on main via `c5ddf69b`, Stream G).
- `platform/scripts/seed/asset_registry_seed.ts` — declares **8 GANITA assets**:
  `ga_positions` (→ `ganita_positions`), `ga_vargas`, `ga_dashas`
  (→ `ganita_dashas`), `ga_strength`, `ga_sensitive`, `ga_panchanga`,
  `ga_sade_sati`, `ga_tajaka`. Each carries `count_sql` (`WHERE chart_id = $1`),
  `target_floor`, `volume_explanation`, `depends_on[]`.
  *(Renamed from `ganita.*` → `ga_*` in migration 195, 2026-06-09.)*
- `asset_registry` table (`platform/supabase/migrations/167_asset_registry.sql`) is the L0
  orchestrator's source of truth; `asset_runner.py`
  (`platform/python-sidecar/pipeline/orchestrator/`) walks it with savepoint isolation,
  downstream-closure stale-marking, upstream-hash gating.
- L1 retrieval registry stub: `platform/src/lib/retrieval/registry/layers/L1_ganita/index.ts`
  (currently a near-empty placeholder — capabilities not yet registered).

**This pattern — not WS2's standalone writers, not the old charter — is the one the L0
campaign deployed and sealed.** The likely-correct end state is the WS2 *computation depth*
expressed through *this* registry/orchestrator spine.

### C.3 — The legacy A1–A22 charter (historical, do NOT rebuild from)

`BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md §C` (2026-06-02) describes a 28-unit A1–A22 + META DAG
with migrations 140–153. **This predates the Brahma L0–L5 lexicon and the L0 campaign's
registry pattern.** Treat the charter's **Gate-0→3 + Contract Registry + role model (§D–§G)** as
canonical method, but treat its **A1–A22 asset numbering** as legacy reference for *intent*
only ([[feedback-rebuild-skepticism-of-existing-code]]) — the live asset identities are the
8 `ga_*` ids in `asset_registry_seed.ts` (§C.2), not "A2–A9".

### C.4 — The reconciliation the audit must produce

A single answer to: **which writers, which migrations, which registry rows are canonical, and
what is the gap to a fully-built-and-deployed L1 on the current prod DB?** Candidate
resolution (to be confirmed/refuted by the audit, not assumed): adopt the C.2 registry spine;
port/verify WS2's computation depth (C.1) into the registry writers where the on-main writers
are thinner; discard A1–A22 numbering (C.3); land everything via PR to main; deploy + prove on
prod.

## §D — Nirīkṣaka current-state audit (the mandatory first pass)

Author this as the **first executable brief** the receiving conversation produces (it is a
read-only audit — safe to run before any native build gate). Per
`BUILD_GUARANTOR_SWARM_CHARTER §E.1`, for **each** of the 8 `ga_*` assets determine, with
evidence:

1. **Writer state** — does a writer exist; is it a real computation or a stub/0-row; WS2 vs
   on-main version; which is deeper? (`platform/python-sidecar/brahmagyan/ganita/` +
   `brahma/l1/ganita/` + `pipeline/orchestrator/writers/`.)
2. **Migration/table state on prod** — does the target table exist on the **wiped prod DB**?
   `[verify-against: prod]` via Cloud SQL Auth Proxy ([[feedback-localhost-codeplane-prod-dataplane]];
   data-plane is always prod). Tables to probe: `ganita_positions`, `ganita_dashas`, +
   whatever `ga_vargas / ga_strength / ga_sensitive / ga_panchanga / ga_sade_sati / ga_tajaka` map to.
3. **Registry state** — is the asset row in `asset_registry` (seeded into prod), with correct
   `depends_on`, `count_sql`, `target_floor`?
4. **Wiring state** — is the writer wired into the orchestrator (`asset_runner.py` / WRITER
   registry / `DAG_ORDER`), or standalone? (The WS2 writers were tested standalone; the
   charter's dominant historical gap was *built-not-wired*.)
5. **Runtime state on the native chart** — for `362f9f17-…`, how many rows does each asset
   actually have in prod **right now**? `[verify-against: prod]`. (Expect mostly 0 if WS2 never
   deployed — confirm, don't assume.)
6. **FORENSIC grounding** — does the writer assert against the §B anchors?

Output: a per-asset table (`built | partial | stub | missing` + evidence + `fresh | delta`
build-mode) that seeds §E. **This audit run IS the data the native commissioned; do not author
build work before reviewing its findings with the native.**

## §E — Asset Contract Registry — L1 slice

Seed one Contract Registry entry (schema = `BUILD_GUARANTOR_SWARM_CHARTER §F`) per `ganita.*`
asset from the §D audit. Binding rules:

- **`owns` = one domain, one unit.** Do not bolt forensic-render content onto other assets
  (the historical drift the charter names).
- **No unit without an `acceptance_gate`** — a shell/test command that proves it per gate
  (Code / Deploy / Runtime).
- **No `runtime_contract` claim without FORENSIC grounding** (§B anchors).
- **`depends_on`** mirrors the real DAG: positions → divisionals/strength/sensitive_points →
  dashas → panchanga → (sade_sati, tajaka). The L1 layer as a whole `depends_on` the L0
  `bg_ephemeris` + `bg_reference` assets.

## §F — Floors discipline (binding on every L1 asset)

Per [[feedback-floors-are-aspirational-not-gates]] (native-ratified 2026-06-09):

- A writer extracts/computes **as much genuine, source-cited, deterministic data as the
  sources legitimately yield**, then sets `asset_registry.target_floor = the REAL achieved
  count` (so the cockpit reads 100% = "all the real data there is"). Aspirational targets go in
  `volume_explanation` ("achieved N / aspired M"), never as the floor.
- **Never fabricate / pad to hit a number.** **A low count never halts a build.** Only
  **integrity** violations halt: non-determinism, fabrication, broken FK, missing citation, LLM
  where banned, schema mismatch.
- For L1 the floors are largely **mathematically determinate** (e.g. positions = 5 ayanamsha ×
  10 bodies = 50; divisionals = 16 × 10 = 160), so achieved should equal the structural count
  unless a source genuinely can't supply it.

## §G — Build constraints (non-negotiable, carry into every brief)

- **Deterministic-first.** L1 is pure computation — Python/PyJHora, **zero generative LLM**
  ([[feedback-deterministic-first-for-data-build]]). Embeddings (deterministic transforms) are
  fine; nothing else.
- **PyJHora is the engine.** No `natal_engine`. No JH-parity gate. Internal consistency +
  FORENSIC grounding only.
- **Prod ACs.** Every acceptance criterion `[verify-against: prod] [via: psql_prod | curl_prod
  | gcloud]`; a wave-complete prod gate re-checks headline row counts on **live prod** after
  internal ACs ([[feedback-ac-must-verify-target-environment]]). Divergence → delta-deploy
  session, not a tag.
- **Merge verification.** Before marking any asset sealed, `git merge-base --is-ancestor
  <commit> origin/main` **and** `gh pr view N --json mergeCommit,state` (mergeCommit:null =
  unclicked) ([[feedback-phase-sealed-needs-merge-verification]], [[feedback-pr-quality-gate-is-not-a-merge]]).
- **No audience tier** anywhere ([[feedback-no-audience-tier]]).
- **Branch isolation.** Each stream owns its branch; recover contamination by cherry-pick to
  main ([[feedback-two-stream-branch-policy]]). Brahma arc may run autonomous under
  AUTONOMOUS_MODE rails if the native elects it; otherwise human-gated.
- **Cowork plans, Antigravity executes.** Briefs embed all git + terminal commands for paste
  ([[feedback-claude-code-executor]]); the executor is Claude Code in VS Code "Antigravity",
  not the CLI.
- **LLM model selection (for any agentic dev-loop, not the data itself):** Anthropic banned
  unless native explicitly asks; default Gemini, fallback DeepSeek ([[feedback-llm-model-selection]]).
- **Verification swarm.** Use the charter's Gate-3 lenses — Pramāṇa (data-integrity battery),
  Sambandha (dependency-completeness: every dependency-satisfied asset actually built, no
  `…_not_computed` sentinels), Darpaṇa (render-coverage vs contract). Name the integrity gate
  **Vimarśaka** to match the L0 campaign's sealing role.

## §H — Suggested stream decomposition (refine after the §D audit)

Provisional; the audit may re-cut these. Mirror the L0 campaign's per-asset-writer +
registry-orchestrator shape.

1. **Stream RECON** — the §D Nirīkṣaka audit (read-only; runs first; native reviews output).
2. **Stream SPINE** — confirm/repair the `asset_registry` L1 rows on prod, the orchestrator
   wiring (`asset_runner.py` WRITER registry + `depends_on` DAG), and the
   `L1_ganita/index.ts` retrieval registration. No new computation — just make the spine
   walk L1 correctly.
3. **Stream COMPUTE** — per-asset writers to their contract, porting WS2 depth into the
   registry writers where on-main is thinner: positions, divisionals, dashas, strength,
   sensitive_points, panchanga, sade_sati, tajaka. FORENSIC-grounded tests each.
4. **Stream DEPLOY+PROVE** — apply migrations to prod, run the native chart build job, Pramāṇa
   + Sambandha + Darpaṇa battery, wave-complete prod gate re-checks row counts on live prod,
   PR-merge + merge-verification, seal artifact `L1_GANITA_CLOSE_v1_0.md` + CURRENT_STATE bump.

Each stream = its own branch, its own Antigravity brief + kickoff, its own acceptance gate.

## §I — Open questions for the native (raise in the receiving conversation)

1. **Autonomy:** run the L1 arc under AUTONOMOUS_MODE (like recent Brahma waves) or
   human-gated per stream? (Affects brief framing + the merge/deploy gates.)
2. **WS2 disposition:** port WS2 writers into the registry spine (recommended), or rebuild the
   thin on-main writers fresh? The §D audit informs this; the native confirms.
3. **`forensic` asset:** Stream F left `forensic_writer` a 0-row stub. Is closing it in-scope
   for the L1 campaign or a separate Stream-F follow-on? (It is the renderer over L1 facts, so
   arguably L1's capstone.)
4. **Scope ceiling:** L1 only, or fold the L0-tail Nadi-texts / forensic-v8 governance sweep
   that L0 left open ([[project-l0-brahmagyan-campaign-state]] §"Open / next")?

## §J — Verification checklist before declaring L1 done (Darpaṇa/Pramāṇa)

`[verify-against: prod]` throughout:
- [ ] All 8 `ganita.*` `asset_registry` rows present on prod with correct `depends_on` + floors.
- [ ] Each target table exists on prod (46-table baseline + L1 additions).
- [ ] Native chart `362f9f17-…` has non-zero rows for every L1 asset whose deps are satisfied,
      matching its `volume_explanation` achieved count (no `…_not_computed` sentinels).
- [ ] FORENSIC 7+/7 anchors (§B) re-asserted against the **prod** rows, not worktree.
- [ ] Determinism: re-run the build job → bit-identical row content (the destructive
      delete-and-rebuild proof, native-gated — mirror L0 Doc 15).
- [ ] L1 capabilities registered in `L1_ganita/index.ts` and reachable from the retrieval layer.
- [ ] PR(s) merge-verified on main; CURRENT_STATE bumped; seal artifact written; OPERATOR_
      ACTIONS_PENDING updated.

---

*End of L1_GANITA_BUILD_CAMPAIGN_HANDOFF v1.0 — authored in Cowork 2026-06-09, grounded against
main HEAD 95d2e4c0. The receiving conversation owns the §D audit, §E contract seed, and §F–§H
brief authoring; the native owns the §I decisions and every build/deploy gate.*
