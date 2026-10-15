---
artifact: CLAUDE_MD_CHANGELOG.md
version: "1.0"
status: CURRENT
role: >
  Full verbatim changelog for CLAUDE.md, moved out at v6.0 realignment (2026-06-12) to keep
  CLAUDE.md itself durable and short. Every entry from v2.0 (2026-04-24) onward is preserved
  here for audit trail. The CLAUDE.md file keeps only the last 2–3 entries inline.
---

# CLAUDE.md — Full Changelog

## v8.0 (2026-10-08, CLAUDE-MD-SLIM — native-authorized context cleanup)

CLAUDE.md cut from v7.5 (497 lines / ~56 KB, ~40% changelog) to durable rules only. Why: the file is
loaded into every session; its 16-item "read all of these every session" list (~1.8 MB incl. the
1 MB CURRENT_STATE) and stale live-state claims (§C.5 "currently L2 Bodha"/dual-campaign text, §E
"build arc complete", §C.0 forcing a Codex worktree brief on every session) were costing tokens and
misdirecting sessions. What changed:
- §C: mandatory 16-item reading list → "read what the task needs" table; CURRENT_STATE read via its
  §2 top banners only. CLAUDECODE_BRIEF applies only when it names the session.
- §D: snapshot version table removed (CAPABILITY_MANIFEST.json is authoritative); the drift_detector
  canonical path strings retained verbatim.
- §E/§F: no live layer status in this file; pointer to CURRENT_STATE §2.
- §G/§H, §K, §L, §M condensed; Gemini/Cowork/Portal-redesign tombstones dropped.
- §N.1–§N.8 kept with identical numbering (heavily cited by code/CI); prose tightened, rules unchanged.
  §N.6 heading kept verbatim for the doctrine-harness B8_n6_anchor assertion.
- Inline changelogs (frontmatter v6.3–v6.9, footer v7.0–v7.5) moved verbatim below.
- Nested CLAUDE.md files in 00_ARCHITECTURE/, 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/,
  03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/ refreshed (they cited superseded files/processes).

### Moved verbatim from CLAUDE.md v7.5 frontmatter changelog

  - v6.9 (2026-07-31, SAMĀPTI campaign close — CLOSED PARTIAL on a mid-run native strategic
      redirect): no doctrine or §N content changed by this entry — it records the campaign's
      close. Full account: `00_ARCHITECTURE/briefs/samapti/SAMAPTI_CLOSE_REPORT_v1_0.md` and
      `CURRENT_STATE_v1_0.md` v6.48. Headline: 18 real production merges (17 clean + 1
      self-inflicted-and-recovered within the hour), all 4 DVA RULING-73-CLOSE integrity
      residuals closed, crown re-verified live at close, Kāla (L3) layer work stopped mid-run and
      handed to ṢAḌ-DARŚANA as a written spec (that campaign is actively rewriting the layer into
      a six-views architecture — auditing code with a scheduled expiry is waste; see the close
      report §1 for the full rationale). One live item flagged for immediate native decision, not
      routine backlog: a VER-CONFIRMED credential-redaction fix (PR #905) remains unmerged against
      a real production credential exposure found earlier this campaign. New standing artifact:
      `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md` — the shared checkout is no longer a
      build surface for any campaign, effective this close.
  - v6.8 (2026-07-30, SAMĀPTI/B-DOCS-GOVERNANCE, DVA Ruling 58 / B-MIGGUARD finding R3):
      §N.4's "Surgical migrations only" line re-worded to its narrower, historically-accurate
      original intent. The prior wording ("never deploy.yml-auto or bulk `migrate.ts`") was found
      by B-MIGGUARD's R3 to be factually contradicted by the live pipeline: `deploy.yml` genuinely
      runs a bulk `migrate.ts` on every deploy, and DVA traced it to be transactional, tracked, and
      loud-failing — a well-built runner, not a hazard in itself. DVA traced the doctrine's own
      `[[feedback-deploy-migrations-silent-noop]]` tag to its original incident and found the real
      hazard was never "bulk migration is dangerous" — it was "migrations silently doing nothing
      while the deploy reports success." New wording: never RELY on the deploy-time bulk runner to
      apply a migration blindly; author it surgically, VERIFY it actually applied, and never edit a
      migration file after it has been applied. This is a wording correction to match the
      doctrine's own documented original intent, per Ruling 58's explicit boundary (same class as
      Ruling 15: corrects a mis-stated instance/wording, does not alter the principle's actual
      scope). **On `ONGOING_HYGIENE_POLICIES_v1_0.md`:** that file does not independently restate
      this line under its own "§N.4" — it has no section by that number (its own §N is "Appendix:
      fingerprint-rotation audit for Step 12 close"). It carries exactly **two** mentions of this
      doctrine, both in §R (Migration-directory ruling) and both citations by reference to
      `CLAUDE.md §N.4` rather than restatements: one glossing §N.4 as "surgical migrations only",
      the other as "never fabricate" (the §N.4 floors bullet, unaffected by Ruling 58). *Corrected
      2026-07-31 (reopen cycle, DVA Ruling 81): this entry originally said "three mentions" — the
      real count is two (`grep -c '§N.4'` = 2) — and originally concluded "Not edited; no matching
      line exists there to fix." The second half was wrong: the "surgical migrations only" gloss
      quotes the now-retired §N.4 heading verbatim and has been updated in place to the corrected
      heading, "Surgical migrations, verified:". No doctrine text in that file changed; only the
      quoted heading.* See `CLAUDE.md` §N.4 body for the corrected text.
  - v6.7 (2026-07-30, SAMĀPTI/B-DOCS-GOVERNANCE, DVA Ruling 16):
      §C item 14 re-pointed from the SUPERSEDED `L1_GANITA_CLOSURE_v1_0.md` to the CURRENT
      `L1_GANITA_CLOSURE_v2_0.md`; hardcoded row counts (chart_facts=27,554; chart_dashas=536,471;
      chart_divisionals=21,635) removed and replaced with a POINTER to the closure artifact's own
      §2.1 asset registry table — the artifact re-measures itself over time (it already documents
      its own figures as post-enrichment estimates, not a final count) and a second hardcoded copy
      here is exactly the mechanism that produced the drift being fixed (v1.0's numbers matched
      neither the v2.0 artifact's own figures nor live production; per DVA Ruling 16's live
      re-measurement, chart_facts=138,414 total across 5 ayanamshas, chart_divisionals=23,542 —
      both consistent with post-enrichment growth — but chart_dashas=484,387, a 52,084-row
      DECREASE against the "prod-confirmed" 536,471 figure that is NOT explained by enrichment and
      is separately assigned as a named investigation item, attached to C3-BUILDSTATE-RECON, not
      resolved by this edit). §D snapshot table's L1_GANITA_CLOSURE row corrected to match (path,
      version 2.1, SUPERSEDED v1.0 noted). §D snapshot CLAUDE self-row corrected 6.5 → 6.7 (a third
      location, beyond frontmatter/footer, where this file's own version had drifted).
  - v6.4 (2026-07-19, COWORK-RETRIEVAL-STRATEGY):
      §I B.11 amended with the RS-4 proportionality carve-out (native-authorized 2026-07-19):
      B.11 scoped to interpretive queries; pinpointed factual lookups (depth: retrieval) satisfy
      it via frame check (chart_header + session pin) + escalation valve (one-line flag + drill
      pointer when the fact touches an active contradiction, firing yoga, or open prediction
      window). Mirrors in-place amendments to PROJECT_ARCHITECTURE_v2_2.md §B.11/§H.4. Doctrine
      source: RETRIEVAL_STRATEGY_v1_0.md §3.6. §D snapshot CLAUDE row corrected 6.2 → 6.4.
  - v6.3 (2026-07-15, DOCTRINE-WAVES-D1.5B-B7):
      New §N.6 Serving Density Principle — codifies the density/confidence-layering discipline
      the `density_contract` field (registry/types.ts) and the response-budget `hardFloor`
      mechanism (platform-mcp/src/lib/response_budget.ts) already embody in production
      (judgment_query, ganita_yogas_get catalog-vs-confirmed handling). Frontmatter/footer
      version drift corrected (frontmatter had stayed "6.0" since the v6.0 unification while
      the footer advanced through v6.1/v6.2 — both now read 6.3). Full text: §N.6 body + footer.
  - v6.0 (2026-06-12, CLAUDE-MD-REALIGNMENT):
      Structural realignment to L1-done/L2-next reality. §F collapsed to CURRENT_STATE pointer
      (M5/M4 you-are-here specifics deleted). §E replaced: 15 completed arcs → layer-reality
      block (L0✓/L1✓/L2-next/L3–L5 pending) + frozen orchestrator note + open items only. §D
      trimmed to currently-canonical artifacts (retired STEP_LEDGER, old phase plans, FILE_REGISTRY
      superseded rows dropped). Changelog moved to 00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md (full
      history preserved verbatim). §B fixed: chart_facts is the canonical L1 source; FORENSIC v8.0
      markdown archived; forensic_render.ts RETIRED; 7 FORENSIC birth anchors named. Asset-id
      underscore convention + layer-name lexicon added. §C updated: item 5 → active campaign =
      L2 Bodha per CURRENT_STATE + L2_BODHA_CAMPAIGN_HANDOFF; item 13 → frozen orchestrator
      (ORCHESTRATOR_CONVERGENCE_CLOSE) with correct chart-build note; new §C items 14–16 add L1
      closure, L2 handoff, and orchestrator-close docs. New §N standards block: orchestrator
      contract, idempotency-per-layer, floors/tier/determinism/JH, L1-authority-over-L2.5.
      Frontmatter version corrected (was "4.8" in frontmatter vs "5.1" in body footer — unified to 6.0).
  - v5.1 (2026-06-09, GANITA-NAMING-RECONCILIATION):
      Gaṇita naming reconciliation COMPLETE: migration 195 relabels 8 ganita.* asset_registry ids → ga_*;
      GANITA_NAMING_RECONCILIATION added to §D snapshot.
  - v5.0 (2026-06-02, BUILD-GUARANTOR-SWARM-CHARTER):
      Build-Workflow Guarantor Swarm Charter authored and added to §C + §D.
  - "Prior history: 00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md (full verbatim record from v2.0)."

### Moved verbatim from CLAUDE.md v7.5 footer

*End of CLAUDE.md v7.5 (2026-09-20, L3 Kāla autonomous data-plane conductor, Packet B3, DP-SD-021
native-authorized) — §C item 5 rewritten to name the two parallel data-plane elevation campaigns
(Pūrṇa Anveṣaṇa in Codex ∥ L3 Kāla in Claude Code) and demote the ~3-month-stale "Currently L2
Bodha" claim; §E's L3 row corrected from the stale "✓ CLOSED, 12 ka_* assets, 12/12" to record the
original build-arc closure as historical alongside the active data-plane elevation campaign's 22
active identities and `Accepted N/22` headline metric — the original closure record is retained in
place, not erased, per the archival/retain-in-place hygiene policy. Both corrections were drafted
read-only by the prior conductor run (stopped mid-session for a model switch, not resumable) and
are retained here as reviewed-correct rather than redone. §D's own CLAUDE self-row corrected
7.4 → 7.5.*

*End of CLAUDE.md v7.4 (2026-08-06, post-salvage close-out, T3/S7 ruling, native-authorized) — §N.4
gains a new bullet: `single` is now a permitted tier for `ga_sensitive` (`ga_writers/ga_sensitive_writer.py`'s
build-fatal guard, which used to HALT the entire GA5 build on any `single` row, now stores such rows
honestly with a warning instead — see `demote_undeclared_predicate_tables.py`/T2 sibling PR for the
same "honest tier, not a promotion" doctrine applied elsewhere this campaign). Writers must still
emit tiers via `brahmagyan/verification_vocab.py` named constants, never a literal. §D's own CLAUDE
self-row version corrected 7.1 → 7.4 (had drifted behind the footer's own v7.2/v7.3 bumps — a
GA.1-class registry-disagreement, fixed in place, no content change beyond the number). Prior: v7.3
(2026-08-01, close-verification pass) — an independent, read-only
verification of the v7.2/PURNATA_CLOSE_REPORT close found two real discrepancies and fixed both,
nothing else touched: backlog items 2 and 5 cited blockers (C4, PR #910) that had already cleared
within this same arc — reworded to state the actual condition inline rather than an indirect
"unchanged" pointer that had gone stale; and the absolute "no kala_*/gochara_* file written" claim
was literally false (PR #900 added two read-only diagnosis scripts matching `gochara_*` by
basename) — now carved out to correctly scope the claim to Kāla PRODUCTION source, kept strong and
true rather than weakened into vagueness. Full account:
`00_ARCHITECTURE/briefs/purnata/PURNATA_CLOSE_REPORT_v1_0.md` v1.3. No doctrine changed by this
entry. Prior: v7.2 (2026-08-01, C4-LOOP-LIVE-PROOF close) — the arc's one remaining open item
closed out. All six criteria (A1–A6: real reading → real `detected` ledger row → live review-tab
render → real UI resolution with can't-tell→NULL DB-CHECK-enforced → real daily-job window
transition with CI's DB-integration suite actually running (129/129) → one outcome map with a live
caller → the calibration leak guard's mutation-proof independently re-run) plus badge-equals-SQL
were verified LIVE against the deployed app and the real production DB — no fixture substituted for
any of them. The cookie-content anomaly that paused C4 was diagnosed READ-ONLY to a fully-traced
benign root cause (dotenvx's own CLI banner sharing stdout with a wrapped script under a shell
redirect — zero application-code involvement) before any resumption, and tooling-fixed (stream
separation, PR #986) as the first act. Three synthetic test predictions generated to prove the loop
were dismissed via the real lifecycle mechanism afterward, returning the native's live review queue
to a true state (0 badge-countable rows) without touching the one row a real concurrent human user
had already dismissed mid-session — itself surfaced as corroborating evidence the surface under test
is genuinely live. Two honest, non-blocking findings carried to the backlog, not fixed in this pass:
`ANTHROPIC_API_KEY` is entirely unprovisioned in production (masked because the actual default
stack is `gemini`), and the concurrent-user observation. No `kala_*`/`l3_*`/`ka_*`/`gochara_*` file
was written to; no credential was rotated. Full account:
`00_ARCHITECTURE/briefs/purnata/PURNATA_CLOSE_REPORT_v1_0.md` v1.2 / `CURRENT_STATE_v1_0.md`
v6.51. Root `CLAUDECODE_BRIEF.md` flipped to `status: COMPLETE` for this arc — see its own
`stale_pointer_incident` field for a governance-hygiene note on why it had drifted. No doctrine
changed by this entry. Prior: v7.1 (2026-07-31, PŪRṆATĀ close) — the final close of the whole
layer-build arc (ŚUDDHA-VĀCA → SATYA-DĪPA → PARIPRAŚNA → SAMĀPTI → NIḤŚEṢA → PŪRṆATĀ). Drained
NIḤŚEṢA's entire auto-merge-armed queue (31 PRs merged this session), diagnosed and worked around a
real branch-protection livelock, caught and closed a self-authored consolidation branch before it
could revert merged work, fixed 3 live CI-gate failures on `main`, landed 6 real narration-fidelity
fixes (including a genuine privacy-leak repair), closed 5 named residuals, and reconciled one
previously-parked PR on the merits. No Kāla PRODUCTION file matching `kala_*`/`l3_*`/`ka_*`/
`gochara_*` was written to (PR #900 added two read-only governance diagnosis scripts whose
basenames match `gochara_*` — `gochara_fingerprint_reproducer.py` / `gochara_readonly_query.py`
under `00_ARCHITECTURE/briefs/samapti/diagnostics/`, the A6/GOCH-1 root-cause investigation, not
Kāla code; see `PURNATA_CLOSE_REPORT_v1_0.md` §8, corrected 2026-08-01); no credential was
rotated. The one item left genuinely open (C4-LOOP-LIVE-PROOF) was paused, not
blocked, on a safety flag raised mid-session — full account
`00_ARCHITECTURE/briefs/purnata/PURNATA_CLOSE_REPORT_v1_0.md` / `CURRENT_STATE_v1_0.md` v6.50. No
doctrine changed by this entry. Prior: v7.0 (2026-07-31, NIḤŚEṢA
close) — the SAMĀPTI wrap-up campaign drained the VER-confirmed merge backlog SAMĀPTI left queued
(PB-3.1 loop lanes, two re-diagnosed PRs, two narration fixes, ~a dozen standalone lanes), split one
PR mid-merge to withhold a Kāla-touching hunk and hand it to ṢAḌ-DARŚANA as a spec addendum instead
of code, and closed the credential item with the native's actual SECURE/accepted-risk disposition
recorded in place (no rotation). Full account
`00_ARCHITECTURE/briefs/nihshesha/NIHSHESHA_CLOSE_REPORT_v1_0.md` / `CURRENT_STATE_v1_0.md` v6.49.
Prior: v6.9 (2026-07-31, SAMĀPTI campaign close) — SAMĀPTI
closed CLOSED-PARTIAL on a mid-run native strategic redirect (Kāla-layer work stopped and handed to
ṢAḌ-DARŚANA as a written spec; full account `SAMAPTI_CLOSE_REPORT_v1_0.md` / `CURRENT_STATE_v1_0.md`
v6.48). Prior: v6.8 (2026-07-30, SAMĀPTI/B-DOCS-GOVERNANCE, DVA Ruling 58 /
B-MIGGUARD R3) — §N.4's
"Surgical migrations only" line re-worded to its narrower original intent: the deploy-time bulk
`migrate.ts` runner is fine and intended (transactional, tracked, loud-failing); the doctrine's real
hazard was always "migrations silently doing nothing while the deploy reports success," not "bulk
migration is dangerous." `ONGOING_HYGIENE_POLICIES_v1_0.md` carries two §N.4 citations-by-reference
(both in its §R); the one glossing §N.4 as "surgical migrations only" was updated in the 2026-07-31
reopen cycle (DVA Ruling 81) to quote the corrected heading, "Surgical migrations, verified:" —
superseding this footer's original claim that no matching line existed there. §D's own CLAUDE
self-row version corrected 6.7 → 6.8. Prior:
v6.7 (2026-07-30, SAMĀPTI/B-DOCS-GOVERNANCE, DVA Ruling 16) — §C item 14 and the
§D snapshot table re-pointed from the SUPERSEDED `L1_GANITA_CLOSURE_v1_0.md` to the CURRENT
`L1_GANITA_CLOSURE_v2_0.md`; the three hardcoded row counts removed in favor of a pointer to the
closure artifact's own re-measurable §2.1 table (hardcoding here is the mechanism that let the
number drift from both the artifact and live production — see the full account in the frontmatter
changelog above). §D's own CLAUDE self-row version corrected 6.5 → 6.7. **HELD, not in that pass:**
DVA Ruling 15 also authorizes correcting §N.8 instance 3's wording (the PB-2 byte-equality gate
description) and re-grading a PB-3 disposition, but gates the §N.8 edit specifically on independent
VER confirmation of the underlying A7-N8-AUDIT finding (F-33) — as of that edit VER had not yet
verified that lane, so §N.8 remains UNCHANGED per the ruling's own precondition; the PB-3 disposition
re-grade (a separate document, not gated the same way) is recorded in `REPORT_PB-3.md` directly. Prior:
v6.6 (2026-07-29, SATYA-DĪPA campaign) — new §N.8 Earned-Signal Principle,
generalizing §N.7 item 4's "a flag needs a real detector or it's null" doctrine to the build layer:
the orchestrator's no-op-completion promotion predicate asserted substep-plan completeness while
only ever checking row presence, the same defect class as D-1.6 one layer deeper. Fixed via the one
authorized freeze exception in `asset_runner.py` (see `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1
and `SATYA_DIPA_REPORT_v1_0.md`). Also corrects a stale carry-forward: §N.7's own footer (v6.5) said
"two P0 lanes remain PARKED on PARISHODHANA PRs #827/#828" — both merged 2026-07-28 and their lanes
(lane:serve-shadbala, lane:ga-tajaka) released the same day, making ŚUDDHA-VĀCA fully CLOSED (7/7),
not PARTIAL; this was independently re-verified live during SATYA-DIPA Phase 0 (serve-shadbala fix
confirmed still correct in production on the canonical chart). Prior: v6.5 (2026-07-28, ŚUDDHA-VĀCA
Phase C/D/E/F session) — new §N.7 Narration Fidelity Principle, codifying the discipline enforced by
the fact-category-pin-lint CI guard and five independently-verified writer fixes (bo_laksana,
sudarshana_emitter, l3_convergence, mi_darshana, ph_nimitta/engine.py) merged this wave. Prior: v6.4
(2026-07-19, Cowork retrieval-strategy session) — §I B.11
amended with the RS-4 proportionality carve-out (native-authorized): B.11 scoped to interpretive
queries; factual lookups satisfy it via frame check + escalation valve. Mirrors the in-place
amendments to `PROJECT_ARCHITECTURE_v2_2.md` §B.11/§H.4; doctrine source `RETRIEVAL_STRATEGY_v1_0.md`
§3.6. Prior: v6.3 (2026-07-15, DOCTRINE-WAVES D-1.5b Lane B-7) — new §N.6 Serving Density Principle:
codifies the density-layering discipline the `density_contract` field (types.ts) and the
response-budget `hardFloor` mechanism (response_budget.ts) already embody, drawn from `judgment_query`
and `ganita_yogas_get`'s catalog-vs-confirmed handling. Frontmatter/footer version drift corrected
(frontmatter had stayed "6.0" since v6.0 while the footer advanced to "6.2" — both now read 6.3).
Prior: v6.2 (2026-06-29 — L4 Phala SEALED: §E L4 BUILT→CLOSED (seal `L4_PHALA_CLOSE_v1_0.md`); §E
"truly open items" note updated — all six layers L0–L5 now sealed/closed, build arc complete). v6.1
(2026-06-29 — §E layer-reality refresh: L2 NEXT→BUILT, L3 draft→CLOSED, L4 draft→BUILT, L5
draft→SEALED). v6.0 (2026-06-12 — structural realignment). Full changelog history at
`00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md`.)*


## v6.2 (2026-06-29, L4-PHALA-SEAL)

L4 Phala sealed. New canonical artifact `L4_PHALA_CLOSE_v1_0.md` (canonical_id `L4_PHALA_CLOSE`) — the definitive L4 closure record (9 ph_* assets, migrations 330–339 + fixes 362/363/366/367, contract-compliance CLEAN, ph_pramana D5 NO-SCORING gate, deterministic-phala / L5-owns-calibration boundary, L4→L5 onboarding). §E L4 row `✓ BUILT (seal pending)` → `✓ CLOSED`; §E "truly open items" note updated to record that **all six build layers L0–L5 are now sealed/closed — the build arc is complete**. Seal rests on: 9/9 registered + clean DAG (DB-verified), contract greps CLEAN, Abhinandan `1c826d5a` end-to-end L1→L5 build, and GATE A prod reconciliation; honest caveat recorded that the native chart is pre-global-build (cold) at seal time so live native L4 counts populate on the imminent build.

## v6.1 (2026-06-29, LAYER-STATUS-REALITY-REFRESH)

§E layer-build table corrected to match built/sealed reality (the v6.0 table was authored at L1-done/L2-next and went stale as L2–L5 were built). Changes: **L2 Bodha** `NEXT` → `✓ BUILT` (8 → 14 assets; ran end-to-end for Abhinandan L1→L5 2026-06-27); **L3 Kāla** `DRAFT/pending` → `✓ CLOSED` (12/12 buildable; seal `L3_KALA_CLOSE_v1_0.md`); **L4 Phala** `DRAFT/pending` → `✓ BUILT` (9/9; formal seal pending — no L4 CLOSE/SEAL artifact yet); **L5 Mīmāṃsā** `DRAFT/pending` → `✓ SEALED` in STRUCTURAL mode (seal `L5_SEAL_AND_SHIP_REPORT_v1_0.md`; neutral cold-start calibration values are by-design, not unfinished). L1 row: stale "585,710 total rows" dropped; seal ref `L1_GANITA_CLOSURE_v1_0.md` → `_v2_0.md`. §E "Truly open items" v5.74 hardcoded snapshot replaced with a CURRENT_STATE §2 pointer + durable note that the L4 formal seal is the one remaining layer-closure step. Companion (non-CLAUDE.md) change this session: `mi_jivanaghatana` reclassified global → per-chart (writer code + migration 372) — it writes the per-chart `mimamsa_event_provenance` table and its unscoped DELETE would have wiped cross-chart provenance once a second chart was built.

## v6.0 (2026-06-12, CLAUDE-MD-REALIGNMENT)

Structural realignment to L1-done/L2-next reality. §F collapsed to CURRENT_STATE pointer (M5/M4 you-are-here specifics deleted). §E replaced: 15 completed arcs → layer-reality block (L0✓/L1✓/L2-next/L3–L5 pending) + frozen orchestrator note + open items only. §D trimmed to currently-canonical artifacts (retired STEP_LEDGER, old phase plans, FILE_REGISTRY superseded rows dropped). Changelog moved to this file (full history preserved verbatim). §B fixed: chart_facts is the canonical L1 source; FORENSIC v8.0 markdown archived; forensic_render.ts RETIRED; 7 FORENSIC birth anchors named. Asset-id underscore convention + layer-name lexicon added. §C updated: item 5 → active campaign = L2 Bodha per CURRENT_STATE + L2_BODHA_CAMPAIGN_HANDOFF; item 13 → frozen orchestrator (ORCHESTRATOR_CONVERGENCE_CLOSE) with correct chart-build note; new §C items 14–16 add L1 closure, L2 handoff, and orchestrator-close docs. New §N standards block: orchestrator contract, idempotency-per-layer, floors/tier/determinism/JH, L1-authority-over-L2.5. Frontmatter version corrected (was "4.8" in frontmatter vs "5.1" in body footer — unified to 6.0).

## v5.1 (2026-06-09, GANITA-NAMING-RECONCILIATION)

Gaṇita naming reconciliation COMPLETE: migration 195 relabels 8 `ganita.*` asset_registry ids → `ga_*`; `GANITA_NAMING_RECONCILIATION` added to §D snapshot.

## v5.0 (2026-06-02, BUILD-GUARANTOR-SWARM-CHARTER)

Build-Workflow Guarantor Swarm Charter authored: new canonical artifact `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` (canonical_id `BUILD_GUARANTOR_SWARM_CHARTER`) added to §C mandatory reading as item 13 and to the §D snapshot table; defines the agentic swarm guaranteeing the chart-build workflow across Gate 0 Assess&Author + Code/Deploy/Runtime gates, 12 roles, and the Asset Contract Registry schema; design pending native confirmation, asset catalog referenced to migration 158 (28 units A1–A22+META_α–ζ; A1–A14 wired, A15+ defined-not-wired) + VALIDATED_ASSET_REGISTRY; follow-ups: register in CAPABILITY_MANIFEST.json + run drift/schema validators.

## v4.9 (2026-05-30, MULTI-AYANAMSHA-DETERMINISTIC-BUILD)

Multi-Ayanamsha Deterministic Build COMPLETE: 4 parallel streams (A/B/C/D); 22 chart assets + 6 META synthesis layers; UTEE + BRIDGE + META-α–ε shipped; ~160 retrieval tools; 14 migrations (140-153); sealing artifact at `00_ARCHITECTURE/MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md`; operator queue: apply migrations 140-153, run ACC1 answer:eval after build job, ACC3 IS.8(b) red-team, ACC4/ACC5 smoke tests post-deploy, trigger native chart build.

## v4.8 (2026-05-28, PLATFORM-MODERNIZATION-SEALED)

Platform Modernization arc SEALED: Batch 5 Wave-4 final seal complete; 7 Wave-4 units shipped (4.refactor_pipeline_shim, 4.observability, 4.memorystore_caching, 4.edge_and_infra_hygiene, 4.build_trigger, 4.learning_loop, 4.red_team_seal); 0 class-1 red-team findings; 8/8 hard gates GREEN; 223/223 tests green on main; tools/program-tracker/ retired (ephemeral); seal artifact at `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md`; full red-team report at `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md`; operator queue: migrations 081–090/118/119 + 6 IaC apply.sh + Cloud Run env-var cleanup + answer:eval live baseline + BUILD_TRIGGER flag flip + amjis-tracker delete + amjis-db-password rotate + depth-selector native review.

## v4.7 (2026-05-26, MCP-TOOL-AUDIT-REMEDIATION-V2)

MCP Tool Audit Remediation v2 COMPLETE: 40/40 tools at 100% (Audit 4c). Session A backward-compat Zod aliases (ee498f34); Session B planet seed + signal confidence + mantras filter (a94b5caf); MARSYS_REPO_ROOT env var applied; amjis-mcp-00019-76h + amjis-web-00424-gv2; main HEAD 18a3b746; audit harness platform-mcp/scripts/audit4_live.ts; P3 CGM+L5 deferred non-blocking.

## v4.6 (2026-05-26, GISMCP-REMEDIATION)

GISMCP Remediation COMPLETE: all 40 MCP tools unconditional; RETRIEVAL_TOOLS 51→55; MSR 573/573 VERIFIED_NO_GAP; worktrees + branches cleaned; workstream added to §E.

## v4.5 (2026-05-25, UDA-2/3/4-COMPLETE)

UDA-2/3/4 COMPLETE: MCP tools 26→40; Universal Parity Campaign FULLY COMPLETE — all 34 sessions across UDA-Q/0/1/2/3/4; Portal 51 tools, MCP 40 tools, both channels at parity; INTERFACE_NORMALIZATION_REGISTER v1.0; PLANNER_PROMPT v2.7 R-NRM.1; 50 MSR citation scaffolds; bootstrap manifests auto-registration fixed; MadhavParity2 worktree retired; PR #164 merged at 79a8168f; CURRENT_STATE v5.57; SESSION_LOG appended.

## v4.4 (2026-05-25, UDA-1-COMPLETE)

UDA-1 COMPLETE: portal tools 36→51; 15 tools channel:both in CAPABILITY_MANIFEST; Universal Parity Campaign §E entry added; workstream count "Fourteen"→"Fifteen"; worktrees MadhavParity/R11A/R11B/R11CDE/R11F/R11G/ToolingFix retired; CURRENT_STATE v5.56; SESSION_LOG appended.

## v4.3 (2026-05-25, DAR-COMPLETE)

DAR workstream COMPLETE: 27 sessions, all 19 findings resolved; feature/data-asset-reconciliation merged to main; Cowork artifacts + tooling remediation cherry-picked at 45b049ad; worktrees MadhavDataAsset + Madhav(fix/ci-gate-cleanup) retired; branches deleted; 3 residuals documented; §E DAR bullet added; workstream count "Thirteen"→"Fourteen".

## v4.2 (2026-05-24, R11F-COMPLETE)

R11.F bounded agentic loop COMPLETE: merge 07e49964 + hotfixes 853c561e/2a4e3c55; all 5 R11E flags live =true; revision amjis-web-00390-csz; 10-min log watch clean; worktree MadhavR11FBound retired; branch chat-v2/r11f-agentic-loop deleted; residuals R11.F-RES-1/RES-2/RES-3 captured as CF.V13.5–7 in V1_3_AUDIT_QUEUE.

## v4.1 (2026-05-23, R11F-ARC-DECLARED)

R11.F bounded loop arc declared ACTIVE: 14-session plan authored, worktree MadhavR11FBound on chat-v2/r11f-agentic-loop pushed to origin; "Thirteen" → "Fourteen" concurrent workstreams.

## v4.0 (2026-05-23, R11G-COMPLETE)

R11.G COMPLETE: tool executor wired (executeMCPTool dispatches to MARSYS retrieval registry; all 5 provider gates real); SettingsDropdown ships (gear → 'Classic Marsys'/'Claude-style chat' radios; MultiProviderParityToggle deleted); NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY + NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL defaulted true in deploy.yml; PR #152 merge SHA 52e18cb5; production amjis-web-00367-b59; STREAM_R11V2_COMPLETE.md §8 added; CURRENT_STATE v5.53.

## v3.9 (2026-05-23, R11V2-DE-ROLLOUT)

R11 v2 D/E production flag rollout close-out: D.1 PASS, D.2 WAIVED, D.3 NOT_IMPLEMENTED (rolled back), E.1–E.4 NOT_IMPLEMENTED (not flipped); deploy.yml orphaned ADAPTERS_ENABLED renamed + D.1/D.2 baked; STREAM_R11V2_COMPLETE.md §7 added; ROLLOUT_PHASE_D/E_RESULT.md written; CURRENT_STATE v5.51.

## v3.8 (2026-05-22, R11V2-DISPATCH-WIRING)

R11 v2 COMPLETE: dispatch wiring shipped in PR #149; && false gate removed; real SDK calls in all 5 adapters; stubChat retired; build fixes: @supabase/supabase-js→pg (PR #150), Next.js 16 async params, ES2018 tsconfig target, bundle_adapters.js path; production revision amjis-web-00339-7nc; MARSYS_FLAG_R11V2_USE_ADAPTERS=true flipped in Cloud Run; STREAM_R11V2_COMPLETE.md §5 amended.

## v3.7 (2026-05-22, MCP-TRANSFORMATION-COMPLETE)

MCP Transformation COMPLETE: feature/mcpt-final merged to main; 17 sessions × 4 phases × 6 worktrees; 2,717 chart_facts rows, 4,589 rag_chunks, 573/573 MSR signals grounded, 21 MCP tools, 5 resources; 0 class-1 red-team findings; migrations 072–080 operator-pending; R11 v2 honesty amendment applied.

## v3.6 (2026-05-22, R11V2-COMPLETE)

Chat V2 R11 v2 Multi-Provider Parity (Claude Takeover) declared COMPLETE: 49 sessions across R11.A-E; 5 PRs #143/#144/#145/#146/#147 merged; 599 tests; capability adapter substrate + look-and-feel + streaming/thinking + caching + agentic loops across all 5 providers shipped.

## v3.5 (2026-05-22, MCP-TRANSFORMATION-DECLARED)

MCP Transformation declared as the 11th concurrent workstream; master plan + 7 session_queue YAMLs + 7 kickoff prompts + setup script under 00_ARCHITECTURE/CONDUCTOR/; 17 sub-phase briefs under 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_*; "Eleven" → "Thirteen" workstreams.

## v3.4 (2026-05-21, M5-COVERAGE-CAMPAIGN-COMPLETE)

M5 Coverage Campaign COMPLETE: 21 sessions shipped; DIS.013 sealed; RESOLVED artifact created; audit SUPERSEDED-AS-COMPLETE; v1.3 carry-forward queue created; "Nine" → "Ten" workstreams; CURRENT_STATE v5.36; SESSION_LOG appended; MP.1+MP.2 mirrors updated.

## v3.3 (2026-05-21, PR-111-REMEDIATION)

PR-111-REMEDIATION: 2 missing NEXT_PUBLIC R10 build-args added to cloudbuild.yaml; UI_REMEDIATION files relocated; CURRENT_STATE v5.29; SESSION_LOG appended; MP.2 mirror; CI investigation; PR #112 merged to main.

## v3.2 (2026-05-21, PHASE-4C-COMPLETE)

Phase 4C COMPLETE: post-merge operator steps closed; build_id `phase-4c-enrich-20260521-r2` populates `panchanga_daily` with 73,414 rows × full enrichment; FORENSIC-grounded spot-check at 1984-02-05 PASS 5/5; structural transit check PASS; Cloud Run `amjis-web-00258-9vq` + `amjis-sidecar-00224-4xs` live; worktree retired; open follow-up: bootstrap `build_manifests` auto-registration audit.

## v3.1 (2026-05-20, R10-COMPLETE)

R10 COMPLETE: PR #106 merged SHA 4dae9ed; all 21 sessions shipped; 566 unit tests green; R10 close-out complete — NEXT_PUBLIC_APP_URL build-arg, backfill script, pre-existing failures v1.1 baseline, Y-S5/Y-S9 queue marks; Phase 4C WAVE_1_COMPLETE PR #105 merged.

## v3.0 (2026-05-20, R10-PHASE-4C-MERGE)

R10 × Phase 4C merge resolution: chat-v2/round10 R10 governance setup COMPLETE + R10_MASTER_PLAN + 21 sub-briefs authored; Phase 4C Panchang + Conductor added as 8th/9th concurrent workstreams; "Seven" → "Nine"; R10 branch merged main post Phase-4C (PR #105).

## v2.9 (2026-05-20)

R10 governance setup + Phase 4C concurrent tracking.

## v2.8 (2026-05-20, R9-OPERATOR-CLOSEOUT)

R9 operator close-out COMPLETE: migrations 110/111/112 applied, all three R9 flags flipped and verified, routing fix b68f533 committed; backfill script not found — gap documented in BACKFILL_SCRIPT_NOT_FOUND.md.

## v2.7 (2026-05-20, R7-R8-R9-COMPLETE)

R7/R8/R9 all COMPLETE in §E; merge-train conductor session closed all three PRs #101/#102/#100 into main; worktrees retired.

## v2.6 (2026-05-20)

R7/R8/R9 declared ACTIVE; MERGE_TRAIN_ORDER authored.

## v2.5 (2026-05-18, §M.17)

Chat V2 Big Bang COMPLETE; sealing-merge `6c431f9` PR #82.

## v2.4 (2026-05-13)

M5 opened.

## v2.3 (2026-05-13)

Gate II.5 close.

## v2.2 (2026-05-11)

Pipeline-Transform-S1 close.

## v2.1 (2026-05-11)

Phase 11B — legacy code path deleted from route.ts; NEW_QUERY_PIPELINE_ENABLED flag retired.

## v2.0 (2026-04-24, STEP-9-CLAUDE-MD-REBUILD — initial install)

Full rebuild against the Step 9 brief. Section schema §A–§M installed per brief §3. Resolves GA.9 (LIFE_EVENT_LOG surfaced as concurrent workstream), GA.10 (GOVERNANCE_STACK surfaced via CANONICAL_ARTIFACTS import), GA.11 (supporting registries surfaced via import), GA.19 (§F currently-executing marker installed), GA.1/GA.2 (canonical paths imported from CANONICAL_ARTIFACTS_v1_0.md rather than duplicated inline). .geminirules mirror propagated in the same session per MP.1. BOOTSTRAP_HANDOFF reference retained as legacy orientation.

## v2.0 (amended in-place, 2026-04-24, STEP-15 — GOVERNANCE-BASELINE-CLOSE)

Rebuild-era banner removed from §F. §C item #8 rebuild-era qualifier replaced with steady-state CURRENT_STATE pointer. §D snapshot STEP_LEDGER row status updated to GOVERNANCE_CLOSED. §L rebuild-step-improvisation bullet removed (rebuild closed). PHASE_B_PLAN §C item #5 paused-note removed. §F narrative replaced with steady-state position. Footer updated. .geminirules MP.1 mirror propagated in the same session.

---

## v6.4 (2026-07-19) — RS-4 B.11 proportionality carve-out

§I B.11 bullet amended per native authorization (Cowork retrieval-strategy session): B.11 scoped to interpretive queries; pinpointed factual lookups (`depth: retrieval`) satisfy it via frame check (chart_header + session pin) + escalation valve (one-line flag + drill pointer when the fact touches an active contradiction, firing yoga, or open prediction window). §D snapshot CLAUDE row 6.2 → 6.4 (stale-row correction). Mirrors in-place amendments to `PROJECT_ARCHITECTURE_v2_2.md` §B.11/§H.4 (changelog entry 2026-07-19). Doctrine source: `RETRIEVAL_STRATEGY_v1_0.md` §3.6. Ruling id RS-4.

---

*Full changelog preserved verbatim from CLAUDE.md v6.0 realignment (2026-06-12). All prior entries are historical audit trail — do not edit. For current CLAUDE.md version and last 2–3 inline entries, see `CLAUDE.md` frontmatter.*
