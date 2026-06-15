---
artifact: CLAUDECODE_BRIEF_CLAUDE_MD_REALIGNMENT_v1_0.md
canonical_id: CLAUDE_MD_REALIGNMENT_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE
delivery_model: 1 branch, 1 PR (governance-only — no app code), merge-verify
goal: >
  Realign + prune CLAUDE.md (the file every session reads first). It is ~40 days stale —
  frozen at M5 while the project is L1-Gaṇita-COMPLETE / L2-Bodha-next. Keep the durable
  structure; delete/collapse the snapshot sections that restale; fix the wrong facts; move
  the changelog out. A surgical governance hygiene pass, NOT a rewrite.
decisions_locked: realign+prune (not rewrite, not minimal); changelog → separate CLAUDE_MD_CHANGELOG.md.
---

# CLAUDE.md Realignment — Execution Brief v1.0

## §0 — Why + the governing principle

CLAUDE.md is the orientation surface every Claude Code session reads first. It has drifted: §F
"you are here" is frozen at M5-A (2026-05-02), §E lists 15 mostly-completed workstreams, the §D
version table + the ~6,000-word changelog tail are bloated, and it still references the deleted
FORENSIC v8.0 markdown + old `ganita.*` naming. Meanwhile `CURRENT_STATE_v1_0.md` (v5.74) is the
true state: L1 Gaṇita CLOSED, `ready_for_L2=YES`, L2 Bodha next.

**Governing principle: CLAUDE.md holds DURABLE orientation; it never holds live STATE.** The root
cause of the drift is that snapshot sections tried to *be* the state instead of *pointing to it*.
The fix makes that delegation explicit and permanent, so it can never restale. (This is already the
documented intent — §C item 8 + the `feedback-verify-state-not-claude-md` rule both say "CURRENT_STATE
is authoritative, §F is frozen." We're finishing that design, not changing it.)

Follow the project's own versioning discipline (B.8): version bump + changelog entry + run
`drift_detector`/`schema_validator` after (CLAUDE.md is a validated governance surface).

## §1 — KEEP (the durable spine — do not gut these)

- §A mission · §B the native (but FIX the FORENSIC reference, §3 below) · §C mandatory-reading list
  (UPDATE the stale entries, §3) · §I operating principles + the 5 most-violated (B.1/B.3/B.8/B.10/B.11)
  · §J quality standard · §L do-nots · §M cadence. These are timeless orientation — keep.

## §2 — PRUNE / COLLAPSE (the sections that restale)

1. **§F "Current execution position (You are here)" → COLLAPSE to a pointer.** Replace the whole block
   with ~2 lines: "**State is authoritative in `CURRENT_STATE_v1_0.md` — read it at session open. Do NOT
   read 'you are here' from this file; §F is intentionally not maintained here** ([[feedback-verify-state-not-claude-md]])."
   Delete the M5/M4-D-S1/M5-A-S1 specifics entirely. This is the single most important change — §F must
   stop trying to be the state.
2. **§E concurrent workstreams → REPLACE the 15-item completed list with the current reality.** Almost all
   15 (Chat V2 R7–R11, MCP, MCP Transformation, Platform Modernization, Multi-Ayanamsha, Phase O, Phase 4C,
   DAR, GISMCP, Universal Parity, Conductor-as-was) are COMPLETE. Replace with a short current-state block:
   - **The layer build is the active arc:** L0 Brahmagyan ✓ built+sealed · L1 Gaṇita ✓ built+validated+closed
     (9 data assets + ga_pyjhora_engine service, ~586K rows, FORENSIC 7/7) · **L2 Bodha = NEXT** · L3 Kāla /
     L4 Phala / L5 Mīmāṃsā = registered (DRAFT), pending.
   - **The orchestrator is FROZEN** (ORCHESTRATOR_CONVERGENCE_CLOSE) — the product "click Build" drives any
     chart's assets in dependency order; future layers onboard by `@register('<id>')` conforming, never by
     extending. See the L2 handoff for the conformance contract.
   - Note the truly-still-open items only: the `feature/panchanga-service-registry` branch pending its own PR;
     R6-1 manifest registration of the orchestrator arc docs; the Phase 5 E2E + Abhinandan teardown if still open.
   - For deep history of completed arcs, point to CURRENT_STATE changelog + the per-arc CLOSE artifacts.
3. **§D snapshot version table → TRIM to currently-relevant canonical artifacts.** Keep the genuinely-current
   ones (FORENSIC→chart_facts, the L1/L2 closure + handoff docs, the orchestrator close, PROJECT_ARCHITECTURE,
   MACRO_PLAN, CURRENT_STATE, GOVERNANCE_INTEGRITY_PROTOCOL, CAPABILITY_MANIFEST). Drop the rows for retired/
   superseded artifacts (STEP_LEDGER governance-closed, old phase plans, FILE_REGISTRY superseded). Reaffirm
   the line "authoritative is CANONICAL_ARTIFACTS / CAPABILITY_MANIFEST — this is a cached snapshot."
4. **The ~6,000-word changelog tail → MOVE to `00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md`** (new file). CLAUDE.md
   keeps only the last 2–3 entries inline + a one-line pointer to the changelog file. Preserve the full history
   verbatim in the new file (audit trail intact).

## §3 — FIX the wrong facts (the "discussion we didn't execute")

1. **FORENSIC references (§B + §D).** CLAUDE.md still frames the FORENSIC v8.0 markdown as the model and the
   `forensic_render.ts` path. Current truth: **the canonical chart facts are the `chart_facts` DB table,
   built by the L1 GA writers; the FORENSIC v8.0 markdown is dead/archived; `forensic_render.ts` (GA2) was
   RETIRED** (L1 build — superseded 0-row stub, L2 retrieval + panchang service do its job). Update §B to:
   "Canonical L1 chart facts = the `chart_facts` DB table (built by the L1 ga_* writers; FORENSIC anchors are
   the 7 birth anchors — Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries, Tithi=Shukla Tritiya, Vara=Ravivara,
   Yoga=Shiva, Karana=Garaja). The v8.0 markdown is an archived cold benchmark only." Remove any framing that
   forensic_render.ts is the live source.
2. **`ganita.*` → `ga_*` naming.** Any lingering `ganita.*` asset-id references → `ga_*`. Add the project-wide
   naming standard explicitly (it didn't exist when CLAUDE.md was written): **asset-id convention = underscore
   prefix per layer: `bg_*` L0 · `ga_*` L1 · `bo_*` L2 · `ka_*` L3 · `ph_*` L4 · `mi_*` L5** (dot-notation
   retired, migration 224).
3. **§C mandatory-reading list updates:** the "active phase plan" item still points to `PHASE_M5_PLAN` as
   active — change to "the active layer campaign per CURRENT_STATE (currently L2 Bodha — see
   `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md`)." The Conductor item describes the OLD conductor "ACTIVE on
   feature/phase-4c-panchang" — update to the FROZEN orchestrator (ORCHESTRATOR_CONVERGENCE_CLOSE). Add the
   L1/L2 closure + handoff docs + the orchestrator close to the reading list as current canonical orientation.

## §4 — ADD (things that didn't exist when CLAUDE.md was written, now core orientation)

Add a concise block (durable, not state) capturing the standards this project now runs on — so every future
session inherits them without rediscovery:
- **The layer model + naming** (L0–L5 = Brahmagyan…Mīmāṃsā; underscore ids).
- **The FROZEN orchestrator contract** — one-paragraph: writers onboard via `@register` WriterBase conforming
  (run on ctx.db_conn, never commit, orchestrator owns build-state + savepoints + sub-steps); if a writer seems
  to need a contract change, STOP and raise. Point to ORCHESTRATOR_CONVERGENCE_CLOSE §2/§5.
- **The idempotency standard per layer** ([[feedback-idempotency-pattern-per-layer]]): L0 ON-CONFLICT (don't
  refactor); L1/L2+ scoped delete-then-insert (replace, not accrete).
- **Floors are aspirational not gates; no audience tier; deterministic-first; no JH-parity oracle** — the
  ratified build principles.
- **L1 is the authority over L2.5 derivations** — the computed-value-drift rule ([[the MSR drift handoff]]):
  L2+ references L1 fact_ids, never re-derives over them.

## §5 — Method + rails

- Branch `chore/claude-md-realignment` off main. Governance-only PR (CLAUDE.md + new CLAUDE_MD_CHANGELOG.md +
  any §D/§C pointer fixes). No app code.
- **Verify every fact you assert against the live source before writing it** — read CURRENT_STATE v5.74, the
  L1/L2 closure + handoff docs, the orchestrator close, and `git log` for the true HEAD/state. Do NOT transcribe
  from the old CLAUDE.md (that's the stale source). ([[feedback-verify-state-not-claude-md]])
- Bump CLAUDE.md version (→ v6.0, a structural realignment) with a concise changelog entry (the verbose history
  now lives in CLAUDE_MD_CHANGELOG.md).
- Run `drift_detector.py` + `schema_validator.py` after — CLAUDE.md is a validated surface; the prune must not
  break a validator (if it does, that reveals a registry the prune got wrong — fix, don't suppress).
- Preserve cross-references: anything §C/§D points to that's still canonical must keep a valid path.
- Merge-verify (`gh pr view N --json mergeCommit,state`).

## §6 — Acceptance

1. §F is a 2-line pointer to CURRENT_STATE; no M5/M4 you-are-here specifics remain.
2. §E reflects the layer reality (L0✓/L1✓/L2-next/L3–5 pending + frozen orchestrator), not 15 completed arcs.
3. §D trimmed to current canonical artifacts; reaffirms CAPABILITY_MANIFEST as authoritative.
4. Changelog moved to CLAUDE_MD_CHANGELOG.md (full history preserved); CLAUDE.md keeps last 2–3 + pointer.
5. FORENSIC fixed (chart_facts table + 7 anchors; v8.0 markdown archived; forensic_render retired); ga_*
   naming + the underscore naming standard present.
6. §C reading list current (active campaign = L2 Bodha handoff; frozen orchestrator; L1/L2 closure docs added).
7. The §4 standards block present (orchestrator contract, idempotency-per-layer, floors/tier/determinism/JH,
   L1-authority-over-L2.5).
8. Every asserted fact verified against CURRENT_STATE/git, not the old CLAUDE.md. drift/schema validators green.
9. CLAUDE.md materially shorter + accurate; v6.0; merge-verified.

---

*End. Realign CLAUDE.md to the L1-done/L2-next reality: keep the durable spine, collapse §F to a CURRENT_STATE
pointer so it can't restale, prune the completed workstreams + changelog, fix the FORENSIC + naming facts, add
the orchestrator + idempotency + L1-authority standards. Governance hygiene, not a rewrite.*
