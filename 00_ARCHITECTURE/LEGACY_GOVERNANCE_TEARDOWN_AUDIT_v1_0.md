---
artifact: LEGACY_GOVERNANCE_TEARDOWN_AUDIT_v1_0.md
canonical_id: LEGACY_GOVERNANCE_TEARDOWN_AUDIT
version: 1.0
status: CURRENT — investigation complete; destructive cleanup DEFERRED to a gated pass
authored_by: Cowork (4 parallel forensic sub-agents + direct verification) 2026-06-16
purpose: >
  Thorough investigation of legacy governance still surviving in CLAUDE.md, config, CI/CD, scripts,
  and briefs — with a per-item KILL / KEEP / REPOINT / ARCHIVE verdict backed by reverse-citation
  evidence — so a later cleanup pass removes ONLY what is genuinely dead, never a live dependency.
  Investigation done now; the destructive cleanup is a SEPARATE gated Claude Code pass (see §6),
  deliberately deferred because a live L2 Bodha conversation shares this repo + prod.
method: read-only fan-out (dead-concepts / CI-CD / config+CLAUDE.md / briefs) + direct verification of the 2 highest-stakes claims
verdict_headline: >
  CLAUDE.md itself is clean (retired concepts are correctly marked). The real legacy lives in (1)
  dead mirror-enforcer code inside governance SCRIPTS, (2) a semantic G52 inconsistency (drop-then-
  recreate + spec still treats it as a prereq), (3) the dual migration-dir confusion, (4) near-dead
  natal_engine still referenced in panchanga_writer contracts, and above all (5) ~147 stale BRIEFS
  (of 368) — the predicate-era/JH-parity/phase-complete clutter the native flagged.
safety: >
  NOTHING in this doc is executed. A live Bodha conversation is on the same repo. The §6 cleanup
  brief is GATED on a Bodha checkpoint. Reverse-citation gate is mandatory before any delete
  ([[feedback-destructive-brief-reverse-citation-gate]]).
---

# Legacy Governance Teardown — Investigation Audit v1.0

## §0 — The honest headline (read first)
Two sub-agents reached opposite-sounding conclusions, and both are right about their slice:
- **CLAUDE.md + CAPABILITY_MANIFEST + asset_registry seed + .claude settings = CLEAN.** Every retired
  concept (B.1, ND.1/Mirror, audience_tier, JH-parity, STEP_LEDGER, FILE_REGISTRY, 362f9f17 phantom)
  is CORRECTLY MARKED retired/superseded in the docs. The doc layer is well-maintained — do NOT
  "fix" CLAUDE.md's retired-concept mentions; they are accurate statements of ratified decisions.
- **The SCRIPTS those docs govern carry DEAD CODE**, the migrations carry a semantic inconsistency,
  and the BRIEFS folder is 40% stale. That is where the real teardown is.

So this is not "rip out everything that says B.1." It is surgical: remove dead *code*, resolve one
*semantic* inconsistency, archive stale *briefs*, and document the dual-dir trap. The doctrine in
CLAUDE.md stays.

---

## §1 — KILL: genuinely dead code + cruft (safe after reverse-citation gate)

### 1.1 — Mirror-enforcer dead code (ND.1 retired 2026-05-27; the enforcer was deleted but its callers weren't)
These reference a `mirror_enforcer` / mirror-pair machinery that no longer exists. Not executed, but present:
- `platform/scripts/governance/schema_validator.py` — `validate_mirror_pair_structure()` + `validate_mirror_structural_block()` (dead functions, ~L230) + their invocation (~L1126) + mirror docstrings (~L12/231/552/840).
- `platform/scripts/governance/serialize_build_state.py` — `P_MIRROR_REPORTS_DIR` (~L96, dead path) + `mirror_enforcer_run` field reads (~L967/1129/1577).
- `platform/scripts/governance/manifest_reader.py` — `mirror_pairs()` logic (returns empty post-ND.1; dead).
- `artifact_schemas.yaml` — `mirror_obligations` / `mirror_updates_propagated` / `mirror_enforcer_run` schema fields (never checked).
- `build_state.schema.json` — `mirror_enforcer_run` field (~L159).
- **Verdict KILL.** These are orphan code/schema for a retired process. Reverse-citation gate: grep
  for each symbol before deleting; confirm no live caller. Low risk (the enforcer is already gone).

### 1.2 — serialize_build_state.py stale asset-version pointers
- `P_CGM = "...CGM_v2_0.md"` + `P_MSR = "...MSR_v3_0.md"` (~L103-105) — current canon is CGM_v9_0 + MSR_v5_0 (CLAUDE.md §D). **Verdict REPOINT** to current versions (verify the files exist first).

### 1.3 — Dead phantom chart_id `362f9f17-…` in MCP test fixtures + tool docs
- Correctly marked dead in CLAUDE.md §B, but still hardcoded in `platform-mcp/src/__tests__/*` (kala/phala tests) and embedded in `platform-mcp/src/tools/phala_event_anchors.ts` JSDoc/body (~L22/182/243).
- **Verdict KILL** — replace all with the canonical `482012f1-710e-4a25-994a-93821f5871aa`. Test-only +
  doc-string; no prod-data risk (the phantom isn't in the DB). Verify no MCP tool WRITES to it.

### 1.4 — chat-v2-ci.yml pure no-op scaffolding stages (8 k6 load, 9 provider-drift)
- Echo-no-op placeholders for PM1/PA1 future work that does not exist. **Verdict KILL-or-MOVE** to a
  separate future workflow (cosmetic; zero operational value now). Stages 2-7/10-14 are KEEP-as-scaffold.

---

## §2 — RESOLVE: the G52 semantic inconsistency (the one real "blocker"-class item)
**Not a migration conflict (verified).** `223_retire_signal_type_registry.sql` (in `platform/migrations/`)
DROPs `signal_type_registry`; `226_bodha_spec_tables.sql` (in `platform/supabase/migrations/`) RECREATES
it. migrate.ts reads both dirs by filename, so it's a clean drop-then-recreate, not a clash. (The
`223` in supabase/migrations is a *different* file — `223_orchestrator_rebuild_probe_dag.sql`.)

**The real inconsistency is SEMANTIC:** the architecture decision DROPPED the predicate-firing model
([[feedback-l1-l2-relationship-architecture]]) — G52 survives only as a name/citation catalog, NOT a
firing registry. But `226` recreates it AND `A10_MSR_SPEC` + `L2_BODHA_BUILD_CAMPAIGN §3.4` still list
it as a "P0.2 prerequisite to seed with 500-700 predicates." **Verdict RESOLVE (native decision needed):**
either (a) G52 stays as a thin label/citation catalog (recreate is fine; respec A10/§3.4 to say
"labeling only, NOT firing"), or (b) G52 is fully dropped and 226 should not recreate it. This is a
Bodha-architecture decision — flag to the Bodha conversation, do NOT unilaterally resolve here.
The BODHA_BUILDOUT_CONTEXT_HANDOFF §5 item 6 already flags this; this audit confirms it's live in code.

---

## §3 — REPOINT/VERIFY: near-dead but referenced
### 3.1 — natal_engine (JH-parity-era engine, replaced by PyJHora) — FORENSICALLY CONFIRMED LEGACY
**The disambiguation the native demanded — verified by direct grep:**
- **LIVE engine = `pyjhora_adapter/`** (PyJHora). EVERY live `ga_writers/*.py` imports
  `from pyjhora_adapter.compute import compute_chart`. **DO NOT TOUCH pyjhora_adapter.**
- **LEGACY engine = `platform/python-sidecar/natal_engine/`** — a real 606-line module
  ("PyJHora Superset Natal Engine", legacy dot-notation asset id `ganita.engine` GA-1-1, engine_version
  1.0.0). **Decisive test: ZERO live modules import `natal_engine`** (grep for `from/import natal_engine`
  outside its own dir + tests returned EMPTY). The ONLY tie is a docstring/comment in
  `pipeline/writers/panchanga_writer.py` (L11, L83, L320 — comments, NOT imports).

**⚠️ TRAP — two `l25_builder` dirs; one is LIVE:**
- `pyjhora_adapter/l25_builder/` is **LIVE** — imported by `pyjhora_adapter/__init__.py:15`
  (`from .l25_builder import build_all, canonical_jsonl`). **KEEP — part of the current engine.**
- `natal_engine/l25_builder/` is the LEGACY one (inside the dead tree). Remove only this one.
- A blind "delete all l25_builder" would BREAK the live engine. The cleanup must target the
  `natal_engine/` path specifically, never the bare name `l25_builder`.

**The complete legacy natal_engine footprint to REMOVE (verified distinct from live):**
1. `platform/python-sidecar/natal_engine/` — entire dir: the 606-line `__init__.py` + `natal_engine/l25_builder/`
   + the legacy smoke/parity test battery in `natal_engine/tests/` (test_jh_parity, test_l25_builder,
   test_no_llm, test_scaffold, test_g1_internal_invariants, test_pyswisseph_crosscheck,
   test_cross_ayanamsha_report, test_vargas_all_bodies, test_true_mean_nodes, test_lilith,
   test_asteroids_outer, test_heliocentric, test_declination_ra_altaz) + all `__pycache__`.
2. `platform/python-sidecar/tests/test_natal_engine_forensic.py` — sibling legacy forensic smoke test;
   `from natal_engine import ENGINE_VERSION, compute_chart` — tests dead code, dies with it.
3. `platform/src/app/api/engine/current/route.ts` + `platform/src/app/api/engine/__tests__/current_route.test.ts`
   — the legacy engine-version endpoint ([BUILD-ORCH-D-06]); **verified NO live `src` component fetches
   `/api/engine/current`** (only its own file + the api/build integration test reference it). Orphaned.
   Reverse-citation gate: the stale `api/build` tests reference it — remove together or after the api/build
   tombstone cleanup (§1.3 sibling).
4. Stale `natal_engine/0.x.x` version-string fixtures: `platform/src/app/api/charts/__tests__/ayanamsha_status.test.ts`
   (multiple) + `platform/src/app/api/build/start/__tests__/route.test.ts:211` (`natal_engine/0.2.0-jh-parity`).
   Repoint to the PyJHora `ENGINE_VERSION` or remove with the dead tests.

- **Verdict REPOINT-THEN-KILL:** (1) repoint `panchanga_writer.py` docstrings → pyjhora_adapter; (2)
  delete the `natal_engine/` dir + `test_natal_engine_forensic.py`; (3) remove `/api/engine/current` +
  its test (gated with the api/build tombstones); (4) fix the version-string fixtures. NEVER touch
  `pyjhora_adapter/` or `pyjhora_adapter/l25_builder/`. There is already a
  `CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md` (ACTIVE) scoped to this — check if it ran; if
  not, this is its scope. Also archive the legacy `_archive/086-089/137_l25_*.sql` migrations are ALREADY
  in `_archive/` (no action) and the `CONDUCTOR/modernization/briefs/BRIEF_2a_l25_build.md` (archive with §4).

### 3.2 — drift_detector.py WARN.8 whitelist (Gemini mirror dead pointers)
- drift_detector passes CI at exit-code 3 with WARN.2-8 baseline-whitelisted. WARN.8 = Gemini mirror
  dead pointers. **Verdict REPOINT** — once §1.1 mirror code is killed, clear WARN.8 from the whitelist
  (and WARN.6/7 CLAUDE.md-helper pointers, likely already dead post-v6.0). Do at a quarterly governance
  pass, not mid-Bodha.

### 3.3 — forensic_render.ts
- Marked RETIRED in CLAUDE.md but the file exists, retained for read-side retrieval. **Verdict KEEP** —
  not cruft; a dormant render util. (The config agent confirmed this is appropriately positioned.)

---

## §4 — ARCHIVE: the brief clutter (the native's main complaint, quantified)
**475 `*_BRIEF_*`/`*_PLAN_*` files repo-wide; 368 in `00_ARCHITECTURE/BRIEFS/` alone.** ~147 (40%) are
clearly archivable. Existing convention: `99_ARCHIVE/`. Recommend `99_ARCHIVE/BRIEFS_RETIRED/` + a
`BRIEFS_INDEX.md` mapping old→replacement.

**Tier-1 dead-model briefs (archive first — the predicate/JH-parity era the native flagged):**
- `CLAUDECODE_BRIEF_PARITY_UDA_{0,1,2,3}_S*` (~22 files, all COMPLETE, dead JH-parity-oracle alignment — zero live refs; superseded by GA8 enumeration).
- `CLAUDECODE_BRIEF_L0FR_STREAM_{A-G}` (7 files, audience_tier-era foundation rebuild — work landed in _archive migrations 082/090).
- the old predicate-model GA8 brief (superseded by `CLAUDECODE_BRIEF_GA8_STRUCTURAL_ENUMERATION_v2_0`).

**Tier-2 phase-complete history (archive):**
- `CLAUDECODE_BRIEF_MCPT_V{32,33,34,310}_S*` (~50-75 files, COMPLETE rollout history).
- `CLAUDECODE_BRIEF_M2_{A-G}*` (~40 files, COMPLETE M2 phase).
- `CLAUDECODE_BRIEF_BHISMA_*` (8 files, COMPLETE).
- closed gates: `GATE_I_CLOSEOUT`, `GATE_I_v1_0`, `GATE_II_v2_0`, `GATE_III_v1_0`.
- superseded top-level plans: `MACRO_PLAN_v1_0` (→ v2_0), old CHAT_V2_*/M1_M2_*_DRAFT plans.

**KEEP (current/actionable):** the Bodha briefs (`BODHA_B1_FULL_PROJECTION`, `BODHA_P0E_SEED_CORRECTION`),
the GA enumeration/writer briefs (still cited), the cockpit briefs, the two open-PR briefs (#275/#276),
`BODHA_BUILDOUT_CONTEXT_HANDOFF`, and THIS audit. **Reverse-citation gate before archiving ANY brief**
— a COMPLETE brief that a live file still references (e.g. JH_PARITY_RESIDUE_CLEANUP is cited in
CLAUDE.md via `[[feedback-no-jh-parity-anywhere]]`) is NOT safe to move without repointing first.

---

## §5 — KEEP (verified clean — do NOT touch in cleanup)
- **CLAUDE.md** — all retired-concept mentions correctly marked; §C reading list current; §N standards live.
- **CAPABILITY_MANIFEST.json** — internally consistent, no retired-concept pollution, no phantom IDs.
- **asset_registry_seed.ts** — the null-target_table check is now correct defensive code (the old
  auto-deactivate bug was already fixed); no audience_tier, no l25_ refs.
- **.claude/ settings** — clean.
- **The REQUIRED CI gates** (typecheck, unit, coverage_gate, secret_scan, schema_validator,
  naming_lint, assert_no_native_literal, deploy) — all enforce CURRENT rules, all green. KEEP.
- **The doctrine** (B.3 derivation-ledger, B.10 no-native-literal, B.11 whole-chart-read, N.4 no-tier/
  no-JH-parity/floors-aspirational) — these are LIVE ratified rules, not legacy. KEEP.
- **brahma-conductor.yml** — operational but in terminal state (all layers built); KEEP as infra.
- **FILE_REGISTRY_v1_0..v1_15** (16 files) — superseded but zero live tooling refs; ARCHIVE-optional, harmless in place.

---

## §6 — The deferred cleanup pass (GATED — do NOT run mid-Bodha)
The destructive cleanup is a SEPARATE Claude Code pass, gated on the L2 Bodha conversation reaching a
checkpoint (shared repo + prod). When authorized, it runs in this order, each phase with a
reverse-citation gate + on its own branch + PR (never direct-to-main, never touching bo_*/bodha_*):

1. **Code-dead KILL** (§1.1-1.4): mirror-enforcer dead code, stale serializer versions, phantom-id
   fixtures, no-op CI stages. Reverse-citation grep each symbol first. Tests must stay green.
2. **natal_engine REPOINT-THEN-KILL** (§3.1): repoint panchanga_writer contract → PyJHora; confirm
   zero importers; archive the dir. (Check if JH_PARITY_RESIDUE_CLEANUP brief already did this.)
3. **Brief ARCHIVE** (§4): move the ~147 Tier-1+Tier-2 stale briefs to 99_ARCHIVE/BRIEFS_RETIRED/ +
   write BRIEFS_INDEX.md. Reverse-citation gate per brief (grep filename across platform/+.github/+CLAUDE.md).
4. **Whitelist + doc REPOINT** (§3.2, §1.2): clear WARN.6/7/8 from drift_detector once their targets
   are gone; fix serializer version pointers.
5. **G52 SEMANTIC RESOLVE** (§2): NOT in this pass — it's a Bodha-architecture decision; route to the
   Bodha conversation (label-only vs fully-dropped).

Each phase: branch → reverse-citation gate → change → tests green → PR. The native merges. No phase
touches the live Bodha files, main directly, prod data, or any REQUIRED-gate-enforced CURRENT rule.

---
*End of LEGACY_GOVERNANCE_TEARDOWN_AUDIT v1.0. Headline: CLAUDE.md/doctrine are CLEAN; the real legacy
is dead mirror-enforcer code in governance scripts, a near-dead natal_engine referenced in
panchanga_writer, a semantic G52 inconsistency (drop-then-recreate + spec-still-treats-as-prereq), the
dual migration-dir trap (documented), and ~147 stale briefs (of 368) from the predicate/JH-parity/
phase-complete era. Cleanup is surgical + reverse-citation-gated + DEFERRED to a Bodha checkpoint.
NOTHING is deleted by this audit. G52 routes to the Bodha conversation as an architecture decision.*
