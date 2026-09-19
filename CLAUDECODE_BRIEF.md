---
artifact: CLAUDECODE_BRIEF_L3_KALA
type: CLAUDECODE_BRIEF (governing scope for execution sessions)
version: 1.1
status: ACTIVE
authored_by: L3 Kāla autonomous conductor session (Claude Code, Sonnet 5, run 2), 2026-09-20
supersedes: >
  CLAUDECODE_BRIEF_PURNATA (this file's prior content, status COMPLETE, 2026-08-01). That arc is
  closed and its record remains at 00_ARCHITECTURE/briefs/purnata/PURNATA_CLOSE_REPORT_v1_0.md —
  nothing there is retracted. This file now governs the currently-active L3 campaign per
  CLAUDE.md §C item 0; it is not a "shortcut" edit — it is the exact governance-refresh packet
  (B3 / P0-4) the campaign's own governing plan authorizes.
changelog: >
  v1.1 (N1-E, 2026-09-20): added an explicit "Applicability" clause near the top, per the strategy
  session's finding that this file — while status ACTIVE — governs every Claude Code session in
  this repo under CLAUDE.md §C item 0, including sessions commissioned for unrelated work, which
  could otherwise misread "elevate 22 ka_* assets" as their own scope. Content otherwise unchanged.
authority: >
  DP-SD-017/018/019/020/021 (00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md
  §9-§13) and MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md. Native authorization for autonomous
  overnight execution recorded in MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE_v1_0.md frontmatter,
  2026-09-20.
---

# L3 Kāla data-plane elevation — ACTIVE

## Applicability (added N1-E, 2026-09-20)

Per `CLAUDE.md` §C item 0, this file governs **every** Claude Code session opened in this
repository while `status: ACTIVE` — including sessions commissioned for work unrelated to the L3
Kāla campaign. A session opened for a different purpose should: (1) note this file's existence and
its `status`, (2) confirm its own actual scope with the native rather than silently adopting "elevate
22 `ka_*` identities" as its governing scope, and (3) proceed under the scope the native confirms.
The `may_touch`/`must_not_touch` lists below bind *this campaign's own work*; they are not a
blanket prohibition on legitimate, separately-scoped work elsewhere in the repo — a session with a
native-confirmed different scope operates under that scope, not under this brief's restrictions.

**Scope:** elevate the 22 active `ka_*` identities to terminal acceptance
(`LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED`) for the
canonical chart `482012f1-710e-4a25-994a-93821f5871aa` against campaign definition
`t3-2026-09-11-8b884eac`. Headline metric: **`Accepted N/22`**. Live state:
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/STATE.md` (authoritative, updated every packet
close) — this brief is a scope pointer, not a progress tracker.

Governing documents, read in order: `MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE_v1_0.md` §B (the
conductor's operating instructions), `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` (the two-
campaign platform split), `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` +
`..._EXECUTION_BRIEF_v1_0.md` (the frozen L3 strategy/brief content, DP-SD-017), `..._ASTRA_REVIEW_RECORD_v1_0.md`,
`..._UNBLOCK_AND_RESUME_AMENDMENT_v1_0.md` (DP-SD-018).

## may_touch

Lifted from `MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md` (DP-SD-017), unchanged:

- `platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py` except protected retired sweep
- `platform/python-sidecar/services/ka_*/**`, `services/gochara_v3/**`, `services/w2g/**`
- `platform/python-sidecar/services/gochara_intensity/**`, `services/gochara_grammar/**`,
  `services/kala_trigger/**` (L3 contribution only, no method/source ratification)
- `platform/python-sidecar/pipeline/transit_search.py`
- `platform/python-sidecar/pipeline/orchestrator/service_probes.py` (L3 clauses only)
- `platform/python-sidecar/tests/l3/**` and exact changed-surface test files
- `platform/python-sidecar/scripts/validate_data_plane_l3_*.py`
- `platform/migrations/<reserved>_data_plane_l3_*.sql` in range **1070–1119** (see partition rule
  below) and explicitly reviewed upstream integration migrations
- `platform/src/lib/retrieval/registry/layers/L3_kala/**`
- `platform/src/lib/retrieval/registry/layers/register_d10_pact.ts` and L3 timing delegation in
  `register_d9_judgment.ts`
- `platform-mcp/src/tools/kala_views/**` and `platform-mcp/src/lib/promise_spine.ts`
- Generated writer/layer pins through their real generators after the appropriate gate
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_*` execution evidence, excluding pinned
  strategy/brief/review authority content
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md`
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/**` (this campaign's own durable state)
- Own campaign-coordination rows on `origin/campaign-coordination` (L3 party only)
- **Added by DP-SD-021 / Packet B3 (this brief's own authorized exception to "must_not_touch
  CLAUDE.md/CLAUDECODE_BRIEF.md as a shortcut" below):** this file; `CLAUDE.md` §C item 5 and §E's
  L3 row only; `CURRENT_STATE_v1_0.md` §2 top banner only — one governance-refresh act, not a
  standing license to edit these files routinely

## must_not_touch

- Pinned strategy, execution brief, prior acceptances and historical review/receipt content
- Frozen `WriterBase`, `runner`/`asset_runner` transaction and build-state contracts
- Shared Swiss-state serialization span and method/source/admission authority
- `ka_gochara_sweep` implementation, retained corpus/snapshot or its non-rebuild protection
- Foreign worktrees/campaign definitions, events, queues, goals, automations or branches —
  **including all Pūrṇa Anveṣaṇa territory**: `retrieval/registry/knowledge/**`,
  `register_prashna_*`, `purna/**`, `managed_prashna_jobs.ts`, `prashna_ask_bridge.ts`,
  planner/inquiry lifecycle, `capability_*` generators (regenerate via the shared generator only)
- Applied migrations **1033–1041**; anything in **1042–1069** (Pūrṇa's range)
- `.github/workflows/deploy.yml`, the data-plane/Pūrṇa ownership scripts
  (`data-plane-ownership-*.ts`, `purna-inquiry-ownership-*.ts`, `data-plane-protected-cutover.ts`,
  `data-plane-secret-isolation-preflight.ts`, `data-plane-admin-credential-diagnostic.ts`)
- Credentials/secrets/IAM/infra; branch protection; security/safety/CI gates
- `WATCHDOG_SECRET` (GCP secret) and revision `amjis-web-02826-huf` — human-owned incident
- L4/L5 writer/evaluation/issuance/model implementation outside separately approved later-layer work
- CLAUDE.md / CURRENT_STATE / SESSION_LOG / CAPABILITY_MANIFEST **beyond the one-time exception
  named above** — no routine edits as a shortcut to avoid real asset work

## activation_prohibitions

- No production mutation before exact environment, authority, protected source, canary,
  backup/restore, ownership and upstream-data gates pass
- No automatic lifting of century, source/method, protected-history, NIRMANA_HOLD or other named
  holds — the `ka_gochara_v3_century_materialize` hold is decided by the native, not this session
- No private event/outcome corpus or derived selector in prospective input; no claim/observation
  rewrites or unauthorized disclosure
- No grandfathered freeze, manual green status, fabricated generation/convergence pin or skipped
  required proof — an asset is `Accepted` only via an authenticated terminal/freeze event
- No blanket L0–L2 semantic redesign, new doctrine, planner-campaign takeover, or L4/L5 campaign
  start
- No production mutation while Codex holds a conflicting, unexpired lease on
  `origin/campaign-coordination` — check before every merge and before Wave E

## Migration numbering (DP-SD-021 / dual-campaign plan §3.3 rule 2)

Pūrṇa **1042–1069**; **L3 1070–1119**; anything cross-cutting **1120+** by a logged coordination
request. Never edit an applied migration (1033–1041 belong to the delivery gate now closed by
Codex; leave them alone).

## Delivery target

`LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED`; empirical
outcome evaluation excluded. `L4` and `L5` remain `WAITING_FOR_STRATEGIC_BRIEF`.

## Close condition

Per CLAUDE.md §C item 0: this brief flips to `status: COMPLETE` when the L3 data-plane elevation
campaign closes (22/22 accepted, or an honestly-scoped native-ruled partial close per the
governing plan's Phase 3 exit). Until then it stays `ACTIVE` and every session reads it first.
