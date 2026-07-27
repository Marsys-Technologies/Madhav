---
artifact: SHODHANA_SHESHA_REPORT (Fast-Follow: reopened items + close-out hygiene — Close Report)
canonical_id: SHODHANA_SHESHA_REPORT
version: 1.0
status: CLOSED
closed: 2026-07-27
author: Conductor (Sonnet, autonomous session) + 2 Sonnet builders (B1/W1, B2/W2) + 1 Opus Verifier,
  per SHODHANA_SHESHA_BRIEF_v1_0.md
source_documents:
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_SHESHA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_REPORT_v1_0.md (§11/§12 appended
    this session — tally reconciliation + MC-001 re-verification/provenance)
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (ADDRESSED-v1.1)
---

# ŚODHANA-ŚEṢA — Close Report

## §0 — Outcome in one paragraph

Both FAILED-REOPENED items are closed. **MC-015** (discoveries ayanamsha-variant dedup — PR #818)
and **MC-029** (Yogi/Avayogi materialization + legacy-category reconciliation — PR #819) are
**VERIFIED-FIXED** on live production, independently confirmed by an Opus Verifier who reproduced
the acceptance arithmetic personally rather than trusting either builder's self-report. Four W3
hygiene items shipped in one docs+small-fix PR (#820): a corrected 42-row disposition table for the
original campaign (root-caused the missing item to MC-008, not a double-count), an independent
re-measurement of MC-001's orphan rate on both canonical charts plus resolution of the external
rebuild's provenance mystery, a codified integration-gate rail from the original P0 incident, and a
widened strict-schema exclusion set. All three PRs merged to `main` (HEAD `70f23fe9`) via
auto-merge. Deploying surfaced a genuine pre-existing production issue unrelated to this session's
own changes — traffic was pinned to a stale revision from an earlier session and three automatic
deploys had silently gone nowhere — found and corrected via a real percentage-canary-then-cutover.
Production is now confirmed serving `main` HEAD. Wall-clock: within the 3h cap.

## §1 — W1 (MC-015) — VERIFIED-FIXED

**Root cause** (Builder B1, confirmed live): `bodha_discoveries_get` was registered in TWO places —
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_discoveries.ts` (the capability PR #803
actually fixed, with a correct `discovery_families` collapse) and a second, standalone MCP
registration in `platform-mcp/src/tools/register_p1_synthesis.ts` that ran its own hand-rolled SQL
directly against `bodha_discoveries`, bypassing the fixed capability entirely — and it was the
second one actually exposed on the wire. This is a wiring/registration miss (prime suspect #1 from
the brief's method), not a wrong grouping key or a domain-filter bypass.

**Fix:** rewired the `bodha_discoveries_get` handler to proxy `marsys://tool/L2/query_discoveries`
via the existing `callRegistryCapability()` helper — the same idiom `kala_life_arc_get` and
`kala_projections_get` already used in the same file, which is exactly why the sibling
`projection_families` fix never needed this rewiring. PR #818, branch
`shodhana-shesha/w1-mc015-discoveries-dedup`, merged.

**Independent Verifier evidence (live, post-deploy):** `discovery_families` populated,
`discovery_family_count: 9`. The house-1 aspect_parashari motif collapses to ONE family
(`member_count: 10`, `ayanamsha_agreement: "5/5 ayanamshas agree"`, 10 member IDs listed); house-4
and house-9 likewise collapse to one family each, 5/5 agreement. Sibling `kala_projections_get`
still returns cleanly (`projection_families: []`, `is_error: false` — empty but not broken, no
regression). One non-blocking note the Verifier surfaced: the response's deprecated top-level
`discoveries: []` alias still carries a `judgment_flags: ["hollow_envelope_no_data_rows"]` entry
that could mislead a caller keying off the wrong field — the real payload
(`content.rows`/`content.discovery_families`) is correct and populated. Worth a follow-up polish,
not a defect in the fix itself.

## §2 — W2 (MC-029) — VERIFIED-FIXED

**Root cause** (Builder B2, confirmed live — differs from the brief's leading hypothesis): NOT a
DAG/registration gap. `ga_sensitive_degree` was already correctly registered
(`has_writer=true`, `is_active=true` in `asset_registry`). The actual cause: PR #807 added the
Yogi/Avayogi computation to the writer on 2026-07-27 06:00 IST, but the writer's last production
run for both canonical charts predated that merge — the asset was already `state='lit'` from a
pre-fix run, so a normal (non-`rebuild`) build simply skipped it as already-complete. The fix
required a scoped **rebuild**, not a registration change.

**Execution:** under the brief's frontmatter grant, B2 ran the scoped `ga_sensitive_degree` writer
substep (all 5 ayanamshas) for both canonical charts only, via the orchestrator's standard
build-run mechanism (dry-run sanity check first, then two real `rebuild` runs — 335 rows each,
chart-scoped, no `kala_gochara_windows`/`build_substep_progress` touch beyond the writer's own
rows). PR #819 (docs + a permanent cross-check regression test), branch
`shodhana-shesha/w2-mc029-yogi-materialize`, merged.

**Legacy reconciliation:** the older `esoteric_point_yogi`/`esoteric_point_avayogi` category (GA5)
was diffed against the new `sensitive_point_yogi` category across both charts × all 5 ayanamshas —
agreement to ~4e-7°, rounding-only. Per the brief's own explicit alternative ("prove it now agrees
exactly"), the legacy category was **not** retired (it also discloses an unrelated alternate
tradition, `alt_96_40`) — instead a permanent regression test now fails CI if the two independently
computed sources ever silently drift apart.

**Independent Verifier evidence (live, post-deploy):** re-derived Yogi/Avayogi Sphuta trigonometry
and nakshatra-lord lookups from each chart's own disclosed Sun/Moon sidereal longitudes personally,
for BOTH charts — 482012f1: Yogi=352.351181°→Revati→Mercury, Avayogi=179.017847°→Chitra→Mars, exact
match to the served rows; 1c826d5a: Yogi=124.450690°→Magha→Ketu, Avayogi=311.117356°→Shatabhisha→
Rahu, exact match. An unfiltered live query of all 67 rows for 482012f1 found only two
`fact_category` values present anywhere (`sensitive_degree_check`, `sensitive_point_yogi`) — no
`esoteric_point_yogi` row appears in serving at all, confirming a single authoritative source, not
two disagreeing ones.

## §3 — W3 hygiene (PR #820)

1. **Tally reconciliation** — appended `SHODHANA_REPORT_v1_0.md` §11: the original 41-sum
   undercounted the register's 42 items by one. Root-caused to **MC-008** (confirmed real by
   Phase A, explicitly re-scoped to track T5, never actually delivered nor listed in §8's open
   follow-ups) — now correctly counted PARKED-HONEST. Full 42-row disposition table with cited
   evidence for every item is in that section.
2. **MC-001 re-verification** — appended `SHODHANA_REPORT_v1_0.md` §12: independently re-measured
   the constituent-facts orphan rate on BOTH canonical charts via direct production DB query
   (482012f1: 0.32%, 1c826d5a: 0.33% — correcting the original report's rounded "0%" claim).
   Resolved the external-rebuild provenance question the original report left open:
   `build_runs.triggered_by` for the full ganita→bodha→phala→mimamsa cascade on both charts
   resolves (via the `profiles` table) to Abhisek Mohanty, `super_admin` — the native's own
   authenticated Cockpit Build action, not a SHODHANA/PV agent or automatic trigger. Also flagged
   that 1c826d5a's `ka_gochara_sweep` remains genuinely stale (left untouched — explicit
   untouchable for this campaign).
3. **Integration-gate rail** — codified the original P0 incident's lesson as
   `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §O.1: merged-main real-authenticated-verify before any
   traffic shift, and a real-SDK integration-test requirement for any portal-wide
   registration-time gate.
4. **Strict-schema widening** — removed the T1/T5/T7/T8 mid-campaign merge-conflict exclusions
   from `STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES` (17 tool names: dossier, muhurta_finder, the 7
   `remedy_tools.ts` names, `register_p1_synthesis.ts`'s 6 tools, the 2 yoga tools) now that all
   ten original ŚODHANA tracks are merged. Left `registry_bridge.ts` (PV-locked) and
   `register_gochara_windows.ts` (untouchable data) excluded. Verified via the T3 envelope battery
   + the #812 real-SDK regression test; full suite showed the same 77 pre-existing failures as
   `main`, zero new regressions.

## §4 — Deploy: a genuine pre-existing issue found and fixed

After all three PRs merged, `gcloud run services describe amjis-mcp` showed `spec.traffic` **hard
-pinned by revision name** to `amjis-mcp-00491-ldr` (created 04:49 UTC, tagged `canary2` — a
leftover pin from an earlier session, not this campaign) rather than routing to latest. Three
automatic CI/CD deploys (triggered by the #818/#819/#820 merges) had each built and readied a new
revision, but none received any traffic — production had been silently serving stale code through
all three "successful" deploy workflow runs. This was caught only because the close protocol
requires confirming production == `main` HEAD directly, not trusting a green workflow badge.

**Correction, following the brief's discipline as closely as the actual infrastructure allows:**
`amjis-mcp`'s Cloud Run deploy has no built-in `--no-traffic` staging step for MCP (unlike
`amjis-web`'s no-traffic→smoke→promote pattern in `deploy.yml`) — so a true pre-traffic canary
against a client bearer token wasn't available (client tokens are platform-issued per session, not
in Secret Manager). Instead: (1) tagged the new revision (`amjis-mcp-00494-ptq`, matching commit
`70f23fe9`) for isolated reference; (2) shifted 10% of real production traffic to it; (3) drove
real authenticated MCP calls through the existing live connection and confirmed via Cloud Run logs
that a request landed on the new revision and completed cleanly with zero errors; (4) cut over to
100%; (5) re-verified MC-015/MC-029 directly against the now-guaranteed-new revision, and confirmed
`mcp_server_info` (152 tools, no crash signal) plus a newly-un-excluded tool (`dossier`) both work
cleanly — meaningful given the strict-schema widening's exact failure mode last time was a
registration-time crash that only a live server start could reveal. Final state: 100% traffic on
`amjis-mcp-00494-ptq`, confirmed built from `main` HEAD `70f23fe9`, zero ERROR-severity logs across
the cutover window.

## §5 — Opus Verifier acceptance (independent, live production)

One Opus-model, read-only Verifier (no code-writing tools) reproduced both items' acceptance
criteria personally, against live production, without relying on the Conductor's or either
builder's account:

- **MC-015: VERIFIED-FIXED.** (See §1 for evidence.)
- **MC-029: VERIFIED-FIXED.** (See §2 for evidence.)
- **Liveness sanity check: PASS** — `mcp_server_info` reachable, `tool_count: 152` nominal, no
  crash signal; every tool call the Verifier made returned `is_error: false`.

No "passed with caveats" — both items received one of the four permitted dispositions plain, with
the minor non-blocking observations noted inline in §1/§2 rather than softening the disposition
itself.

## §6 — Close-protocol checklist

- [x] MC-015 and MC-029 VERIFIED-FIXED on live production (Opus Verifier, independent).
- [x] Corrected 42-row disposition table produced (`SHODHANA_REPORT_v1_0.md` §11).
- [x] MC-001 re-verified independently on both charts; external-rebuild provenance resolved, not
      left a dead end (`SHODHANA_REPORT_v1_0.md` §12).
- [x] Register annotated ADDRESSED-v1 → ADDRESSED-v1.1 (`LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md`).
- [x] All PRs (#818, #819, #820) merged via PR + auto-merge, no direct push.
- [x] `amjis-mcp` deployed explicitly; production confirmed == `main` HEAD (`70f23fe9`) after
      correcting the stale-traffic-pin issue found during this close.
- [x] Worktrees removed (`agent-mc015-fix`, `agent-ab26ac4c770eb0e7b`); local + remote branches for
      `shodhana-shesha/w1-mc015-discoveries-dedup`, `shodhana-shesha/w2-mc029-yogi-materialize`,
      `shodhana-shesha/w3-hygiene` deleted; temporary Cloud Run verification tag removed.
- [x] Root `CLAUDECODE_BRIEF.md` never touched (confirmed already `COMPLETE`/PŪRṆA-VIRĀMA at
      session start, per §C item 0 — skipped, not modified).
- [x] Untouchables confirmed intact: `kala_gochara_windows` data untouched (1c826d5a's known
      staleness there is a pre-existing, separately-tracked gap, not something this session
      touched); `build_substep_progress` untouched beyond the scoped writer's own rows; the sealed
      evaluator harness untouched.
- [x] Bodha (L2) rebuild remains correctly out of this campaign's authorization — §3's finding
      that one has already occurred externally (native's own action) does not change what THIS
      campaign did or didn't authorize.

## §7 — Still open (not this campaign's scope, noted for the record)

- 1c826d5a's `ka_gochara_sweep` remains stale (blocked on an incomplete upstream dependency run,
  per `SHODHANA_REPORT_v1_0.md` §12(d)) — untouched, per this campaign's explicit untouchables.
- MC-004/MC-006's guaranteed-fits `verbosity:'summary'` form remains open (needs
  `registry_bridge.ts`, deliberately deferred twice now across two campaigns).
- `mimamsa_lel_query`'s apparently non-functional `query`/`offset` params (T9's bonus finding) —
  not investigated this campaign either.
- The Bodha (L2) rebuild DAG-documentation reconciliation (§3 Decision 2's condition 1) remains
  undone — flagged again as the one genuinely open precondition for that authorization question,
  independent of the fact that a rebuild has since happened externally.
- MC-015's minor cosmetic note (§1: the deprecated top-level `discoveries`/`judgment_flags` alias
  on `bodha_discoveries_get` can read as more broken than it is) — worth a follow-up polish, not
  blocking.

---
*ŚODHANA-ŚEṢA closes here. Both reopened items are genuinely fixed and independently verified
against live production. The original campaign's tally is now honestly reconciled to all 42 items.
The deploy pipeline's stale-traffic-pin issue — found only because this close protocol insists on
confirming production state directly rather than trusting green CI — has been corrected and is
now flagged in `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §O.2 so future campaigns check for it
too. Truth over
completion, all the way through.*
