---
artifact: PARIPRASHNA_ASBUILT_BASELINE_v1_0
canonical_id: PARIPRASHNA_ASBUILT_BASELINE
version: 1.1
status: LIVING — regenerated at every gate close; every row carries an evidence class + date
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18); P1-I addendum (Claude Code, 2026-08-19)
date: 2026-08-18
baseline_of: git HEAD dfbdfe620 (branch ekv/b-01-dignity-oracle-fix snapshot) + live MCP census 2026-08-18 + PB close corpus
authoritative_side: claude
role: >
  What EXISTS, dated and evidence-classed — the current-state companion to
  PARIPRASHNA_ARCHITECTURE_v1_0.md, which carries no current-state claims itself.
  Successor to TA v0.11 §16.9. Regeneration rule: at each gate close, re-verify
  every row, refresh dates, move satisfied gaps to the closed table. Never
  normative; never aspirational.
changelog:
  - "1.0 (2026-08-18): first generation, from the v0.11 §16.9 census + v0.12 evidence ledger."
  - "1.1 (2026-08-19): P1-I lane — live re-verification of every UNVERIFIED row
    (PITR, DB roles, flag env, serving revision) against the LIVE tip of
    origin/pariprashna/p1 (33b9db230, G1-B/D/F/H/E/C merged) and the real
    deployed environment. New §6 addendum carries the full re-check with
    command + timestamp evidence; the affected §1/§3 cells are annotated
    in place with a pointer rather than silently overwritten, since G1 has
    not gate-closed and other lanes may be relying on the original rows."
---

# Paripraśna — As-Built Baseline (2026-08-18)

Evidence classes per NFR annex §1. UNVERIFIED rows are the re-verification
worklist for the next gate.

## §1 — Doors and deployment

| Fact | Class · date |
|---|---|
| Portal surface + `/api/pariprashna` (+resume, +samiksha/confirm) live behind `PARIPRASHNA_ENABLED`; flag default `false` in code | STATIC_VERIFIED @ dfbdfe620 |
| Flag ON in production via Cloud Run env (since `amjis-web-01218-4ng`) | DOCUMENT_ASSERTED (REPORT_PB-1) · 2026-07-28 |
| Current Cloud Run env value / serving revision | RE-VERIFIED — see §6.4 · 2026-08-19 |
| C4-LOOP-LIVE-PROOF: full prediction loop live, six criteria, real concurrent user | DOCUMENT_ASSERTED (PURNATA_CLOSE §9) · 2026-08-01 |
| MCP: 125 tools on `full` profile; `catalog-1+t152+r653c2a1a98c8`; profiles full/compact/consult; `prashna_ask`+`prashna_status` job-handle, rejected on consult | LIVE_VERIFIED · 2026-08-18 |
| `ganita_ayurdaya_get` served UNGATED on the MCP surface | LIVE_VERIFIED · 2026-08-18 |
| PB-4 cutover (default flip, consult retirement, flag deletion): NEVER RUN; consult/consume still the un-gated default | STATIC_VERIFIED @ dfbdfe620 |

## §2 — What is BUILT and live-path (STATIC_VERIFIED @ dfbdfe620 unless noted)

15-event Zod SSE protocol + typed emitter (zero `as any`) + calibration-leak
guard on every write · stream-first route (turn.open before planner; faults
in-stream; clarification streams as a block) · acharya-floor compilation on
Door 1 (B.11 + dasha floors + budget arbitration + NO-LEAKAGE arm-2 filter) ·
append-only renderer (FrozenBlock always-equal memo; single volatile tail;
owned scroll; dock) · register-leak lint, server-side, 6 pattern classes,
2 call points · canonical `message_parts` (mig 467) + summaries (468,
prefix-stable splice) · ring-buffer resume (Redis, seq replay, snapshot
fallback, interrupted finalize) · D-16 stamp per turn, copied into ledger
under `trg_bmpl_freeze_confirmed` · 9-state prediction ledger (mig 470) with
legal-transition matrix; review tab, batch resolve, daily job, Brier at
resolution; `mcp_predictions` retired (471) · fail-closed chart authz
(CHART_REQUIRED) · SHA-256 chart-scoped cache keys + echo-back.

## §3 — Gap register (open)

| # | Gap | Class · date | Owner |
|---|---|---|---|
| GAP-1 | MP §3.5.B/C/D/F: NO safety gate, disclosure-class model, consent schema, or minor exclusion anywhere in the serving path (§3.5.E is the exception — seal/freeze/transitions live) | STATIC_VERIFIED · 2026-08-18 | G1 (PPR-12/14/24) |
| GAP-2 | NO-LEAKAGE arm-1: five roles now DEFINED (migration 576, `pariprashna/p1` branch tip) but INERT — NOLOGIN/no members, RLS policies stored but not enabled, `amjis_app` untouched — and migration 576 itself is NOT YET APPLIED to production (not merged to `main`, where `deploy.yml`'s migration runner triggers from). Production today is still exactly the pre-G1-C state: single `amjis_app` credential, no RLS. See §6.2. | RE-VERIFIED — see §6.2 · 2026-08-19 | G1 (PPR-21/22) |
| GAP-3 | No middleware, no rate limit, no blocking spend cap on either chat tree | STATIC_VERIFIED · 2026-08-18 | G1 (PPR-25) |
| GAP-4 | PITR disabled, no restore drill (last verified F-25t) | RE-VERIFIED — still disabled (`False`) — see §6.1 · 2026-08-19 | G1 (PPR-33) |
| GAP-5 | `ANTHROPIC_API_KEY` unprovisioned in production (anthropic stack fails instantly, masked by Gemini default) | DOCUMENT_ASSERTED (PURNATA §5.1a) · 2026-08-01 | G1 |
| GAP-6 | Live wire renders paragraphs only (FD-1): table/verse/gap-ribbon/heading/roles/prediction_card have no live producer | STATIC_VERIFIED | G2 (PPR-07) |
| GAP-7 | S-3 citation rewriter built, unwired; `citation.define` post-hoc; grounding summary client-synthesized (FD-2/FD-6) | STATIC_VERIFIED | G2 (PPR-08) |
| GAP-8 | Model/Length pickers cosmetic; `length_tier` nonfunctional; depth from picker not scope tuple (FD-3/FD-12) | STATIC_VERIFIED | G2 (PPR-09/16) |
| GAP-9 | No durable-persistence protocol (settled_visual vs durably_persisted undistinguished); parity invariant unbuilt; capture flag OFF per Ruling 80 (FD-9 — apparatus repurposed per PPR-10) | STATIC_VERIFIED | G2 (PPR-10) |
| GAP-10 | No AcharyaReadingReceipt: B.4 sets, typed confidence, prose binding, safety_decision all unemitted | STATIC_VERIFIED | G3 (PPR-01..05) |
| GAP-11 | prashna_ask is single-pass without lint/sentinel/receipt; unified plan type unwritten; store covers assistant turns only | STATIC_VERIFIED / DOCUMENT_ASSERTED | G4 (PPR-30) |
| GAP-12 | Recall built-unwired (FD-5); LogToSamiksha unmounted (FD-4); window-opening ask unbuilt; dispute capture absent; feedback endpoint still discards (F-25c); digest transport log-only (FD-10) | STATIC_VERIFIED | G8 (PPR-18/31) |
| GAP-13 | Calibration sink (Rulings 55/79) unbuilt; `model_p` column absent; method-version column is a PROPOSED Ruling-79 amendment | STATIC_VERIFIED | G9 (PPR-28/29) |
| GAP-14 | Cost/latency metrics schema exists with 0 rows (F-25o); no TTFT aggregates; SLOs unbaselined | STATIC_VERIFIED 2026-07-19 · presumed standing | G2 (PPR-33) |
| GAP-15 | Two error classifiers (adapter bands live; `classify-error.ts` dead, zero importers) | STATIC_VERIFIED · 2026-08-18 | G7 sweep |
| GAP-16 | PB-9-DETECTOR (no-auto-promotion CI detector) open — property true by inspection only | DOCUMENT_ASSERTED (REPORT_PB-3 §G.9) | G1/G2 |
| GAP-17 | audience_tier residue: type/comment-level + two JSON-schema `required` fields (load-bearing sites excised) | STATIC_VERIFIED · 2026-08-18 | G7 sweep |
| GAP-18 | Post-six-views narration audit (PŪRṆATĀ handoff #2) not run | DOCUMENT_ASSERTED · 2026-08-01 | G8+ |

## §4 — Engine content beneath the surface (DOCUMENT_ASSERTED, CURRENT_STATE §2)

PRATIJÑĀ v4.1 adopted (marriage verdict conditional/0.450 MODERATE — first
amendment-set production verdict) · GOCHARA v3 under PARIṢKĀRA's honest
re-close (structural_prior stamps) · ṢAḌ-DARŚANA KP sub-lord clock ·
ADHIṢṬHĀNA fact-identity index · SAMPŪRTI domains 7→13. Serving rule for all
of it: PPR-03 (earned tier only).

## §5 — Regeneration protocol

At each gate close: re-verify every UNVERIFIED row live; re-date every
STATIC row against the then-HEAD; move closed gaps to a dated CLOSED table
(append-only); bump version minor. The Baseline never says MUST — if a row
tempts normative language, the content belongs in the Architecture.

## §6 — P1-I live re-verification addendum (2026-08-19)

Lane P1-I ("Ground truth: re-verify every UNVERIFIED Baseline row live"),
read-only audit, no code touched. Branch point: `origin/pariprashna/p1` @
`33b9db230` (G1-B/D/F/H/E/C merged into the campaign branch; **not** merged
to `main` as of this check — confirmed via
`git merge-base --is-ancestor 33b9db230 origin/main` → NO, and `main` HEAD
`c97871dd8` lacks `platform/supabase/migrations/576_pariprashna_roles_rls_arm3.sql`
entirely). This section supersedes the four rows it covers; it does not
alter or delete any other claim in this document.

### §6.1 — PITR status

Command (read-only `describe`, no state change):
```
gcloud sql instances describe amjis-postgres --project=madhav-astrology \
  --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"
```
Run 2026-08-19T18:36:47Z. Result: **`False`**. Unchanged from the last
P0-F check (F-25t, 2026-07-19) — GAP-4 stands exactly as described; no
restore drill has been executed; RPO/RTO + DR runbook (G1-E work item)
remains open on production regardless of what `pariprashna/p1` has built.

### §6.2 — DB roles (NO-LEAKAGE arm-1, migration 576)

Verified by static/branch inspection, not a live DB query (no DB write/query
tooling was exercised against production for this check, per the read-only
constraint). Two independent confirmations that migration 576 has **not**
reached production:

1. `platform/supabase/migrations/576_pariprashna_roles_rls_arm3.sql` exists
   at the `pariprashna/p1` tip but is absent from `origin/main`
   (`git show origin/main:platform/supabase/migrations/576_...sql` →
   `fatal: path ... exists on disk, but not in 'origin/main'`).
2. `.github/workflows/deploy.yml`'s push triggers are scoped to
   `branches: [main]` only — the deploy/migration pipeline never runs
   against `pariprashna/p1` directly. Since the migration isn't on `main`,
   it cannot have been applied through the normal deploy path. (This does
   not rule out an out-of-band manual `psql` apply, which cannot be
   confirmed without production DB query access — noted honestly, not
   assumed.)

Independent of deployment status, the migration's own header (read in
full) states it is **designed to be inert even once applied**: the five
roles are created `NOLOGIN`/`NOBYPASSRLS` with no members, RLS policies
are `CREATE`d but `ROW LEVEL SECURITY` is not `ENABLE`d on any table, and
`amjis_app` is untouched — arming is a separate, deliberate operator act
(`platform/scripts/pariprashna/g1c_arm_rls.sql`, outside the migrations
directory, never auto-applied). So the G1-C claim ("created the roles,
explicitly did not apply to production or arm RLS") is confirmed true on
two independent grounds: the migration hasn't reached prod, and even if it
had, it would not have changed serving behavior. Production today serves
every read on the single `amjis_app` credential with no RLS, unchanged.

### §6.3 — Flag env (code default vs. live override)

Code defaults read from `platform/src/lib/config/feature_flags.ts`
(`DEFAULT_FLAGS`) at the checked-out `pariprashna/p1` tip:

| Flag | Code default | Live env override (amjis-web, read via `gcloud run services describe --format="json(spec.template.spec.containers[0].env)"`, 2026-08-19T18:38Z) |
|---|---|---|
| `PARIPRASHNA_ENABLED` | `false` | **`MARSYS_FLAG_PARIPRASHNA_ENABLED=true`** — set, overrides default to ON. Confirms the §1 "Flag ON in production" row still holds. |
| `PARIPRASHNA_LIMITS_ENABLED` | `false` | not set — serves at code default (`false`, dark) |
| `SUBJECT_CONSENT_ENFORCEMENT` | `false` | not set — serves at code default (`false`, dark) |
| `PARIPRASHNA_ROLE_SEPARATION` | `false` | not set — serves at code default (`false`, dark) |
| `PARIPRASHNA_LEDGER_OUT_OF_PROCESS` | `false` | not set — serves at code default (`false`, dark) |
| `PARIPRASHNA_SAFETY_GATE_ENABLED` | **does not exist** on this branch — not in the `FeatureFlag` union or `DEFAULT_FLAGS` at all (grep confirmed zero hits) | n/a |

Full env dump on `amjis-web` was fetched (54 vars total) and grepped for
`MARSYS_FLAG`/`PARIPRASHNA`; the four other live-set flags in the dump
(`HISTORY_COMPRESSION_ENABLED`, `BUILD_TRIGGER_ENABLED`,
`VECTOR_SEARCH_ENABLED`, `OBSERVATORY_ENABLED`) are unrelated to this
campaign and listed only for completeness. `amjis-mcp`'s env (17 vars) was
also checked — zero `MARSYS_FLAG`/`PARIPRASHNA` vars present there at all,
i.e. the MCP door has no flag override of any kind. This is a **`describe`
read only**; no flag was changed.

### §6.4 — Serving revision

Commands (read-only `describe`):
```
gcloud run services describe amjis-web --project=madhav-astrology --region=asia-south1 \
  --format="value(status.latestReadyRevisionName,status.traffic)"
gcloud run services describe amjis-mcp --project=madhav-astrology --region=asia-south1 \
  --format="value(status.latestReadyRevisionName,status.traffic)"
```
Run 2026-08-19T18:36:49Z. Results:

| Service | Latest ready revision | Traffic |
|---|---|---|
| `amjis-web` | `amjis-web-01529-hf8` | 100% → `amjis-web-01529-hf8` (latestRevision) |
| `amjis-mcp` | `amjis-mcp-00575-pgx` | 100% → `amjis-mcp-00575-pgx` (latestRevision) |

Both well past the `amjis-web-01218-4ng` revision the original §1 row cited
(REPORT_PB-1, 2026-07-28) — expected, given the volume of merges into
`main` since. No `pariprashna/p1`-branch-specific code is live on these
revisions beyond whatever has already merged to `main` (G1-C/roles work has
not merged, per §6.2); the live `PARIPRASHNA_ENABLED=true` override governs
whatever Paripraśna surface IS on `main` at `amjis-web-01529-hf8`.

### §6.5 — What this addendum could not verify

No live DB query access was exercised (no `mcp__postgres__query` or
equivalent call made against production) — §6.2's roles/RLS conclusion
rests on branch/deploy-pipeline inspection, not a direct
`SELECT rolname FROM pg_roles` or `SELECT * FROM supabase_migrations...`
against the real instance. If a tighter guarantee is needed than "the
normal deploy path never touched it," that would require either explicit
authorization to run a read-only `SELECT` against production, or the
operator's own migration-tracking record.

*End PARIPRASHNA_ASBUILT_BASELINE v1.1 (2026-08-18; P1-I addendum 2026-08-19).*
