---
artifact: EL25_RATIFICATION_PACKET
version: 1.1
status: DRAFT-FOR-NATIVE-RATIFICATION
date: 2026-07-25
addendum_date: 2026-07-26 (PŪRṆA-VIRĀMA close-out, T3 track — added §I, four items the
  close-out brief named as explicitly queued to the native but not yet confirmed present:
  the MSR-cascade ruling, EL-17/CR-66, cross-reference to the A-5 supersession review
  already present at §G, and the authorization-chain governance finding)
role: Lane gamma.J (calibration lifecycle + native packets), Elevation Campaign v2.1
governs: charter §13 packet 2 ("Ratification packet (γ.J) — all pending ratifications
  incl. this run's NATIVE_PROXY_LEDGER_ELEVATION_V2.md, one recommended disposition each")
scope_note: This packet covers every pending/PROXY-RULED/PARKED-HONEST/PROVISIONAL item
  found across the whole Elevation Campaign v2.1 run (all three streams) plus the
  standing proxy-ledger backlog the charter names explicitly (NATIVE_PROXY_LEDGER
  through D-4b, battery stamps, the Phase-0.7 pin). It is a RECOMMENDATION document —
  no disposition here is binding; every row is exactly what its "Recommended
  disposition" column says: something for the native to quickly ratify or override.
recommended_disposition_legend: |
  RATIFY-AS-RULED — the proxy/lane ruling is sound, evidenced, reversible where it
    touches anything reversible, and consistent with §0/§10; native sign-off closes it.
  RATIFY-WITH-AMENDMENT — sound in substance but names a small correction/follow-up
    the native should bless explicitly (documented per row).
  ESCALATE — requires the native's own judgment/data a proxy cannot supply (architecture
    intent, risk tolerance, or a genuinely new decision point).
  SUPERSEDED-NO-ACTION-NEEDED — already resolved by a later ruling in this same run;
    listed for completeness/audit trail only.
---

# EL-25 Ratification Packet — Elevation Campaign v2.1

Compiled by Lane γ.J (Stream γ, PŪRṆA). This is a recommendation surface, not an
adjudication — every disposition below is proposed for the native to ratify or override
in one pass. Grouped by source. Each row: **id · source · situation · current
disposition · recommended disposition (+ rationale)**.

---

## A — This run's Stream γ proxy ledger (`~/elev-v2-shared/proxy/gamma.md`)

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| PROXY-RULED-001 | α/β heartbeat files absent/stale at γ's Phase-1 kickoff; γ proceeded rather than treating it as a stalled-lock condition. | γ proceeded with its own lane work, logged, no contract touched. | **RATIFY-AS-RULED** — correctly scoped to γ only, no cross-stream effect, re-check was scheduled. |
| PROXY-RULED-002 | C7 (accounting invariant contract) missed its T0+4h deadline by ~2.5-3h because γ's own session launched late; overrun logged honestly rather than backdated. | C7 published as γ's first action; overrun disclosed in CONTRACT_STATUS.md. | **RATIFY-AS-RULED** — honest process disclosure, no data/contract quality impact. |
| PROXY-RULED-003 | Charter left the second Ω-Verification flagship domain open between "career or marriage"; γ selected career. | Career selected; wealth+career are the two domains committed to the C7 allowlist. | **RATIFY-AS-RULED** — reasoned engineering choice within §10 latitude, reversible if native prefers marriage. |
| PROXY-RULED-004 | Independent Ω1 Verifier baseline surfaced 5 gate-denominator ambiguities (fact_category scope, bodha_mechanisms class count, ayanamsha count, dasha-system count, thin-varga treatment). | 5 rulings made, all *stricter* than the ambiguous reading (never looser), relayed to the Ω1 builder. | **RATIFY-AS-RULED** — each ruling documented in `OMEGA1_INDEPENDENT_BASELINE_v1_0.md`; none weakens §0's 100%-accounting mandate. |
| PROXY-RULED-005 | Ω4's "not weaker than plan_retrieval's fallback" acceptance criterion is ambiguous/near-vacuous read literally. | Interpreted as signal-vocabulary superset (0 deep-misroute regressions + genuine narrow-routing precision), the only reading under which both Ω4 acceptance bullets are simultaneously satisfiable. | **RATIFY-AS-RULED** — logically necessary reading, no acceptance criterion weakened. |
| Lane E rank-vocabulary fix point (EL-59/20) | Regression traced to two files outside γ's manifest (`L2_bodha/query_remedies.ts`, `query_rm_resonances.ts`, α territory). | γ built and shipped the canonical fix (`ranking/rank_vocabulary.ts`) and wired it into its own in-manifest consumer; cross-file reconciliation on α's files PARKED-HONEST, blocked-on-α. | **RATIFY-AS-RULED** — correct application of M2.9 (no opportunistic cross-manifest edits); α's reconciliation is the one open action item. |
| Ω6 CMN-1 / CMN-2 | Ω6 builder found 2 real TCI metadata refinements (ayanamsha-summed row_count undocumented; one `serving_tool` pointer slightly off) in γ's OWN Ω1 TCI artifact, mislabeled PARKED-HONEST "cross-manifest" by mistake. | Reclassified as in-manifest, non-blocking, deferred to a bundled Ω8 follow-up patch (not a re-run of the full Ω1 sanity gate). | **RATIFY-AS-RULED** — correction of a mislabel, no data-quality impact (documented, not hidden per §0), C7 allowlist unaffected. |
| Ω5 `serving_args` key mismatch (Ω8-fixup tag) | TCI recorded `fact_category` as the param key for `ganita_chart_facts_get`; live tool actually takes `category`. | **Resolved** — Ω8 applied the fixup this run, independently Verifier-confirmed (0 corruption, C7 unaffected). | **SUPERSEDED-NO-ACTION-NEEDED** — already closed within this same run. |
| Ω7 dark-corpus criterion-2 gap | Live-production dark-corpus measurement (wealth 5.58%, career 8.46% coverage) is far from the charter's "zero unserved" target, because Ω5's dossier tool isn't yet wired into `server.ts` (α's manifest, PARKED-HONEST blocked-on-α). | Flagship self-verification criterion 2 will be dispositioned **PARKED-HONEST/PREPARED-FOR-NATIVE** against live production, not against what Ω5 can structurally prove. | **ESCALATE** — this is the campaign's single most consequential open gap; native should confirm whether shipping α's `server.ts` dossier-wiring is worth reopening the merge lock before close, or whether it is next-campaign's first item. |

---

## B — Stream α proxy ledger (`~/elev-v2-shared/proxy/alpha.md`)

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| Frozen-contract-over-charter-narrative ruling | α's own initial lane-builder briefs (drafted from the charter's pre-Phase-0 narrative) used stale/simplified shapes for 3 lanes (B's receipt shape, A's honesty-field list, H's schema-map scope) before α had read RUNWAY's frozen C1-C8 contracts. | Corrected before real rework occurred; no CONTRACT_STATUS.md amendment needed (clarifies existing frozen contracts, doesn't change them). | **RATIFY-AS-RULED** — self-caught, self-corrected, evidenced against file:line contract citations. |
| Lane B "injected message" false-positive | Lane B flagged 4 legitimate conductor SendMessage corrections as possibly-injected; net effect, Lane B shipped the STALE `CategoryReceipt` shape instead of the C2/C8-corrected one. | Conductor fixed directly (rewrote type + builder to the frozen shape), re-typechecked clean. Ruled that a caller-requested-but-empty category is `dark_count:1`, not `(0,0,0)`, inside C8's closed 4-state enum. | **RATIFY-AS-RULED** — correct defensive posture by the subagent (false positive, but the caution itself is the right default), correctly resolved by the conductor without inventing a 5th receipt state. |

---

## C — Stream β proxy ledger (`~/elev-v2-shared/proxy/beta.md`)

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| Branch-naming D/F conflicts (LANE-D2, LANE-D) | `elev/beta/<lane>` collides with the existing `elev/beta` branch as a git ref. | Flattened to `elev/beta-<lane>` twice, PR base unchanged. | **RATIFY-AS-RULED** — pure VCS namespace fix, no data/architecture consequence. |
| Session-scope autonomy authorization | Stream-Conductor asked the live human user (not inferred) whether to run fully autonomous per charter; user selected full autonomy. | Logged as a verifiable record, explicitly NOT claimed as "ratifying in the native's name" — every ruling stays PROXY-RULED for morning review. | **RATIFY-AS-RULED** — this is exactly the record-keeping §10 requires; nothing here bypasses native review, it just confirms the human consented to autonomous operation tonight. |
| A-3/CR-131 DATABASE_URL ground truth | CURRENT_STATE's snapshot lists this as "1/6 OPEN honest." | β.T re-probed live: PR #732 / commit `74752e20` had ALREADY fixed this before the campaign started. Live re-probe this session confirms `backing_data_reachable:true` on all 3 gochara tools. NOT-REPRODUCED, regression test + payload diff committed. One narrower residual (a spent, one-off dispatch script's `DATABASE_URL` env-read) found and correctly left unfixed (inert, never re-invoked). | **RATIFY-AS-RULED** — close A-3/CR-131 in the register as ALREADY-FIXED-PRE-CAMPAIGN; CURRENT_STATE's "1/6 OPEN" line is stale and should be corrected at this run's close. |
| Gochara sweep (T-2) resume | Resume dispatch (`build_run b458d112`) hit its own 6h Cloud Run ceiling with ~50-60 more substeps banked; ~129/303 substeps remained at last measurement, projecting ~8.9h total. | PARKED-HONEST with a stated ETA (next 6h ceiling ~2026-07-25T11:40Z), not claimed complete. This directly gates the 9 PROVISIONAL UAT-DARPANA queries (see §D below). | **ESCALATE** — native should decide whether to authorize a follow-up resume dispatch tonight/tomorrow (same script, no code change) or accept the 9 PROVISIONAL queries staying provisional into the next session. |
| EL-40 (uniform 0.875 dispositor chain-mean) | The flat 0.875 collapse was a real computation artifact (all 9 chains sink to Jupiter, own sign, for this native). | Fixed to the arithmetic mean of dignity-strength over all chain members (6 distinct values, 0.594-0.875) — chosen over withdrawal to preserve real information. | **RATIFY-AS-RULED** — no new constants invented (B.10-clean), reuses the existing dignity→strength mapping, disclosed as "composite." |
| EL-38 (argala "all-zero" report) | Prior report of an all-zero argala matrix was a `limit:5` sampling artifact — the real matrix is 1,388/4,176 non-zero D1-scoped cells. | No writer change; disclosed. Default-limit timeout + house-from-lagna resolution correctly deferred to α.B (cross-manifest, EL-38 = α·B + β·D per §15). | **RATIFY-AS-RULED** — correct finding, correctly scoped, nothing fabricated or silently dropped. |
| House/sign convention (D-R5, C4) | Estate-safety risk from mixed wholesign conventions across arudha/bhava_arudha rows. | Per-row `formula_id` tag + a new self-marking `house_from_varga_lagna` key, specified in the FROZEN C4 contract; α re-derives legacy rows from the always-correct `sign` field. | **RATIFY-AS-RULED** — matches the FROZEN, sha256-verified C4 contract exactly. |
| Rebuild method (D-R6) | The deployed-image dispatch scripts would miss local worktree fixes. | Used the `run_heavy_writer_standalone.py` local-code-against-prod-DB pattern instead, under the shared `db-rebuild` lock with FORENSIC 7/7 gate. | **RATIFY-AS-RULED** — no contract change, no deploy; standard, previously-used pattern. |
| EL-19 sahams re-scope | Register described sahams as "REACHABLE-BUT-EMPTY, never computed" — investigation found this FALSE: sahams are fully computed (2,800 rows/chart, both charts), hand-recompute confirms exact values, correctly cited (Tājaka Nīlakaṇṭhī Ch.2). | The real defect is a serving-layer category-name mismatch (`saham` vs. stored `saham_position`) in `register_p1_aliases.ts` — outside β.D2's manifest (α's). Handoff delivered: recompute-proof regression test + precise alias-mapping spec. | **RATIFY-AS-RULED** for the re-scope finding; **ESCALATE** the handoff itself only in the sense that α must actually apply the one-line alias fix — flagged here so it isn't lost between streams. |
| EL-18 per-dosha bhanga (Manglik reachability) | Root cause: `_evaluate_catalog_rule` doesn't implement the catalog's `{houses/house, planet, reference}` formation shape, so `manglik` never forms and the already-built, BPHS-cited `_cancel_manglik` logic is unreachable dead code. This is also the RETRIEVAL_AUDIT_REPORT (Phase 0.7) residual "per-dosha bhanga computation, owner: future ga_yoga_writer session." | Bespoke `_detect_manglik` built + registered (formation literally from `brahma_dosha_catalog.manglik.formation_rule_jsonb`), offline-verified both canonical charts (A uncancelled, B cancelled), citations BPHS ch.78/ch.81. Live DB rebuild deferred to integration (concurrent lock conflict with β.D's own `ga_structural` rebuild) — a ready rebuild script is committed. Disposition: **PREPARED-FOR-NATIVE**. | **RATIFY-AS-RULED**, with the explicit note that integration must run the prepared rebuild script + FORENSIC 7/7 before this is genuinely closed. Also **closes the Phase-0.7 residual** noted in §E below — cross-reference recorded. |
| Cross-lane worktree collision (LANE-T) | Sibling lane β.G's `checkout` landed β.T's in-flight commit on the wrong branch (shared physical worktree directory). | Self-corrected with zero data loss (verified β.G's branch had no other commits); recommended (not unilaterally enforced) that future lanes push+delete branches promptly or the Stream-Conductor serialize plain `checkout`s under the worktree lock. | **RATIFY-AS-RULED** for the correction; **RATIFY-WITH-AMENDMENT** for the recommendation — native/Meta-Conductor should decide whether to formalize the serialization convention for future multi-lane-per-worktree campaigns (a real process gap, not this campaign's to fix retroactively). |

---

## D — Prior standing ledger: UAT-DARPANA Phase 1 battery stamp (`uat_darpana/NATIVE_PROXY_LEDGER.md`)

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| Battery stamp, 3 corrections | `UAT_BATTERY_v1_0.md` pre-registration reviewed by proxy: found (1) a fabricated classical-term gloss (NBRY mis-expansion), (2) a wrong arithmetic operator in S5-01's known_benchmark (which also silently contradicted S5-05), (3) a stale `status_note_on_known_data_state` not reflecting confirmed Stage-2 findings. | All three corrected in place before any Answerer session ran (inside the P3 pre-registration freeze window, not a violation of it); file re-stamped `STATUS: STAMPED`; §4 checklist completed with verification evidence per box. | **RATIFY-AS-RULED** — none of the three corrections touched `user_voice_text`, reordered, or removed a query; invariant `no red verdict ruled green` holds. |
| 9/45 PROVISIONAL (S3-01..08 + S4-05) | Phase 2 ran while the T-2 gochara sweep was still incomplete (native's own mid-execution corrective ruling, 2026-07-24) — these 9 queries are excluded from every score/band/tally in `UAT_DARPANA_REPORT_v1_0.md`, kept in the register for audit trail only. | Still PROVISIONAL as of this session. Directly gated by the β.T gochara resume dispatch (see §C above) — ~129/303 substeps remained at last measurement. | **ESCALATE** — same decision point as the gochara-resume item in §C: authorize a further resume dispatch, or accept these 9 stay provisional past this campaign's close. |

---

## E — Prior standing ledger: DOCTRINE-WAVES D-4b (`briefs/doctrine_waves/NATIVE_PROXY_LEDGER_D4B.md`)

The charter names this ledger explicitly ("NATIVE_PROXY_LEDGER through D-4b"). NP-D4B-005,
006, 007, and 009 are **the native's own direct rulings** (via Cowork, not proxy) — they
require no ratification, they already are the ratification, and are listed only for the
compiled audit trail the campaign close calls for.

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| NP-D4B-001 | DR-17 grading weights: verbatim consumption by B-1 (proxy-ruled, 2026-07-21). | Adopted as this run's pre-registered operational constant. | **RATIFY-AS-RULED** (superseded in spirit by the later native-ruled B-1 NO_WINNER outcome, NP-D4B-009 — listed for completeness). |
| NP-D4B-002 | "Cheaper-null" circular time-shift control proposed as a possible primary control. | Refused as primary; admitted only as a pre-registered, non-gate-bearing diagnostic. | **RATIFY-AS-RULED** — correctly conservative (a weaker control never substitutes for the real one). |
| NP-D4B-003 | §4 tie-band widths (±3d/±7d/±45d/±180d) needed as fixed operational constants. | Adopted as this run's pre-registered constants, with a mandatory DR-13(d)-width sensitivity check attached. | **RATIFY-AS-RULED** — pre-registered before scoring, sensitivity check named, not a post-hoc loosening. |
| NP-D4B-004 | Control sample design (§6): N=1000 + coverage-matching window + seed scheme. | ADOPTED as committed; explicit ruling that a DR-19 cost-refusal is not grounds for an N-reduction. | **RATIFY-AS-RULED** — protects the harness's statistical power against a budget-driven shortcut. |
| NP-D4B-005 / 006 / 007 | Native rulings, direct via Cowork (2026-07-22). | Already resolved by the native directly. | **SUPERSEDED-NO-ACTION-NEEDED** — listed for audit-trail completeness only. |
| NP-D4B-008, item 1 | Cross-campaign accidental content loss: a concurrent, unrelated campaign's good-faith cleanup revert incidentally rolled back some of D-4b's own legitimate content (no data permanently lost — reconstructed from the original session record). Flagged as "worth a native-level process note" for doctrine-wave prose artifacts sharing one repo. | **Still open** — informational, native review requested, not formally ruled (distinct from item 2, which NP-D4B-009 resolved). | **ESCALATE** — genuine open process question: should doctrine-wave ledger/register/report files get per-campaign-scoped sections or a coordination convention (reserved numeric ranges, a lock) to prevent recurrence across concurrently-active campaigns? This Elevation Campaign's own three-stream/three-proxy-ledger structure is itself informative precedent the native may want to fold into the answer. |
| NP-D4B-008, item 2 / NP-D4B-009 | CR-128: `BRIEF_D4B.md`'s B-2 lane assumed a write surface (`mimamsa_outcome_record`) that doesn't exist; nearest real pipeline has a live schema/code mismatch. | **Native ruling (direct, 2026-07-23):** do NOT build/repair now — B-1 returned NO_WINNER, so there is nothing legitimate to backfill; B-2/B-3 close HONESTLY-DEFERRED; CR-128 stays OPEN as future work, decided when real data exists. Campaign closed on this basis. | **SUPERSEDED-NO-ACTION-NEEDED** — already the native's own final ruling; the honest-deferral pattern here is a good model for this campaign's own Ω7 dark-corpus gap (§A above) if the native wants precedent. |

---

## F — The Phase-0.7 pin (`uat_darpana/RETRIEVAL_AUDIT_REPORT_v1_0.md`)

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| Phase 0.7 exit gate | Frontmatter reads `status: COMMITTED — EXIT GATE MET (finalized post-merge, all 12 PRs landed)`, §7's Assessed-Version Receipt is marked FINAL (commit `d1278fa9`, the pin every later UAT-DARPANA phase assesses against) — but the document's own closing paragraph (last line) still reads "the Phase 0.7 exit gate is NOT yet satisfied," an unrevised leftover from an earlier draft pass. | Gate is genuinely MET per the authoritative frontmatter + §7; the trailing sentence is stale prose, not a live status. | **RATIFY-WITH-AMENDMENT** — ratify the gate as MET; separately bless a one-line hygiene fix to the document's closing paragraph so it doesn't mislead a future reader who stops at the last line instead of the frontmatter. |
| The one Phase 0.7 residual | "Per-dosha bhanga/cancellation computation... owner: future L1 Gaṇita `ga_yoga_writer` session" — filed honestly rather than fabricated to close the phase on schedule. | **This campaign's β.D2 lane (EL-18, §C above) is that future session** — bespoke `_detect_manglik` built, offline-verified both charts, PREPARED-FOR-NATIVE pending the integration-phase rebuild. | **RATIFY-AS-RULED** — cross-reference recorded; this residual closes once integration runs β.D2's prepared rebuild script. |

---

## G — CURRENT_STATE open items carried into this campaign (§15's own "also carried" list)

| id | Situation | Current disposition (this session) | Recommended |
|---|---|---|---|
| A-3 / CR-131 | Listed "1/6 OPEN honest" in the CURRENT_STATE v6.41 snapshot this campaign inherited. | β.T's live re-probe this session: **already fixed pre-campaign** (PR #732, commit `74752e20`). NOT-REPRODUCED. See §C above. | **RATIFY-AS-RULED** — correct CURRENT_STATE's snapshot at this campaign's close; A-3/CR-131 is CLOSED, not open. |
| A-5 | Remedy-engine (CR-67/CR-69) HALTED for native decision per the pre-campaign snapshot. | β's Stream-Conductor logged an explicit native session-scope authorization covering "superseding CURRENT_STATE A-5 (remedy accept-as-dark → β.G repair)"; β.G's R-1/R-2 lane closed both CRs, live-verified this session (`bodha_remedies_get` now returns real, cited, domain-joined resonances). | **RATIFY-AS-RULED** — the native already authorized this supersession path explicitly (recorded, verifiable); the repair itself is live-verified, not just claimed. |
| A-6 | Timing-anchor (CR-66/CR-37) HALTED for native decision. | Charter §12 explicitly keeps "A-6 accept-as-dark reversal beyond β.T's re-verification evidence" OUT OF SCOPE this run. β.T's T-5 disclosure work (empty_reason/known_gap on `phala_predictive_anchors_get`) improves the HONESTY of the accept-as-dark state but does not reverse it. | **ESCALATE** — unchanged from the pre-campaign snapshot; this is correctly still the native's own call, per the charter's own scope boundary. |
| B-1 | `phala_predictive_anchors_get` empty with no `empty_reason`/`known_gap` (silent-empty finding from PRE_DARPANA_READINESS). | T-5 disclosure fix is live-verified this session (honest `empty_reason`/`known_gap:"CR-66"` now served). The underlying CR-66 data-gap fix (query-level) is proven correct against the real DB (290 rows across 6 domains, wealth 0→~26) but **not yet served** — the physical `phala_anchors` table rebuild needs the same cockpit-build access as T-2 and has not run; live production still shows the old 8 rows, wealth=0. | **RATIFY-WITH-AMENDMENT** — ratify the disclosure fix as closing the silent-empty (honesty) half of B-1 outright; the data-completeness half stays open pending a `phala_anchors` rebuild, which should be logged as a named follow-up, not conflated with "B-1 closed." |
| B-2 | Sat-Jupiter pratyantar convergence (Apr 9 – Aug 18, 2027) standing prediction — CURRENT_STATE flagged this as "not located on any live surface" (PRE_DARPANA_READINESS v1.1, FAIL-as-specified). | **Independently re-verified live this session** (γ.J, 2026-07-25): `standing_predictions_read(chart_id=482012f1…, status=open)` returns the prediction verbatim (`prediction_id 8d59a8a4-fe26-49f2-8933-327bdca1e212`, event_class `major_gain`, window `[2027-04-09, 2027-08-18]`, confidence 0.55, real falsifier, filed_by `native:abhisek@marsys.in`, source_citation traced to `TEMPORAL_ENGINE_ARC_PLAN_v1_0.md` + `BRIEF_D4A.md` Lane A-4). This matches PRE_DARPANA_READINESS_v2_0's own P-1 finding (CLOSED, planner-wired — `standing_predictions_read` was repointed off the empty L4 anchor surface onto the real prospective ledger, PR #736). No lifecycle-sweep action is needed for B-2 itself: its window (2027) has not lapsed, so it correctly remains `lifecycle_status='open'` — the EL-58 sweep built this session (see main report) confirms this is the honest, expected state, not a defect. | **RATIFY-AS-RULED** — B-2 is CLOSED. CURRENT_STATE's "not located on any live surface" line is now stale and should be corrected at this campaign's close alongside A-3/CR-131. |

---

## H — This lane's own EL-58/EL-24 parking

| id | Situation | Recommended |
|---|---|---|
| EL-58 `lapsed_unobserved` schema gap | `brahma_prospective_ledger.lifecycle_status`'s live CHECK constraint does not include `lapsed_unobserved` (verified live, 2026-07-25). `platform/migrations/**` is exclusively β's manifest — γ.J cannot land the ALTER TABLE. Ready, additive-only migration text is committed as `LAPSED_UNOBSERVED_MIGRATION_SQL` in `prediction_lifecycle_sweep.ts` (L5_mimamsa). | **ESCALATE / hand to β** — a one-statement, additive, reversible migration; recommend landing it in the next β session so the sweep's `brahma_prospective_ledger` half can write instead of only report. |
| EL-24 build-state legibility + reaper | Investigated: `build_runs.scope`/`scope_target`/`plan` already capture dispatched scope. The substep DENOMINATOR (total expected substeps) is genuinely not persisted anywhere — only inferable at runtime from a writer's `plan_substeps()` logic (β's `python-sidecar`, FROZEN orchestrator territory) or computed at serving time (α's `platform-mcp/tools`/cockpit API routes) — both outside γ.J's `L5_mimamsa/vidhi/llm_consumption_audit` manifest. Separately: a reaper/self-heal for stuck builds **already exists and is comprehensive** — `platform/src/app/api/cockpit/watchdog/route.ts`, Cloud-Scheduler-invoked every 5 min, handles orphan running runs (>30min), stuck-building assets with a data-presence rescue check before failing (>15min), undispatched runs (>10min), plus 90-day pruning. | **RATIFY-AS-RULED** for "no new reaper needed" (one already exists and is well-designed); **ESCALATE / hand to β+α** for the substep-denominator persistence gap — it needs a writer-side change (β) plus a serving-side surface (α), neither reachable from this lane's manifest. |

---

## I — PŪRṆA-VIRĀMA addendum (2026-07-26): the four items the close-out brief named explicitly

`PURNA_VIRAMA_BRIEF_v1_0.md` §A.1 and §B T3(e) name four decisions the campaign explicitly
queued to the native and require this packet to carry each with its own evidence ref +
recommended disposition. A repo-wide check found three of the four absent from §A–§H above
(the fourth, the A-5 remedy-engine supersession review, was already present at §G's `A-5`
row — cross-referenced below rather than duplicated). Added by the PŪRṆA-VIRĀMA T3 track,
not by Lane γ.J; same recommendation-only status as the rest of this packet.

| id | Situation | Current disposition | Recommended |
|---|---|---|---|
| (a) MSR L2→L5 cascade ruling | 671 `bodha_msr_signals` refs are dangling post-L1-rebuild (expected build-id rotation per §N.5) — restoring them needs a `bo_laksana`+downstream L2 Bodha writer cascade, outside the 5-writer rebuild scope this run's binding native ruling permitted. | `STREAM_BETA_CLOSE_v1_0.md` (Lane row `— \| MSR L2→L5 cascade refresh`): **PARKED-HONEST (native-ruling-bound)** — named follow-up, not silently dropped. | **ESCALATE** — the repair is writer/rebuild-scope work (a `bo_laksana` cascade), which PŪRṆA-VIRĀMA's own serving-only rails forbid touching; only the native can authorize and schedule a dedicated L2 Bodha session and rule on priority given 671 dangling refs is a live, real data-quality gap, not a cosmetic one. |
| (b) EL-17 / CR-66 (wealth-domain phala-anchor residual) | `phala_anchors` for chart `482012f1` grew 8→64 rows across 6 domains after PR #739 + a completed rebuild (`build_run 42720d15`), but **wealth stayed at 0** even though `bodha_convergence` holds 5 wealth-domain source rows at exact parity with every other domain — the gap is isolated to `ph_nimitta`'s anchor-materialization path for wealth, a residual beyond the 3 bugs PR #739 already fixed. | `BETA_T.md` §"EL-17 — CR-66 (phala domain anchors)": **PARKED-HONEST**, live re-probe 2026-07-25T05:41Z (`phala_predictive_anchors_get(domain=wealth)` → `anchor_count:0`, `known_gap:"CR-66"`), explicitly flagged "NATIVE TO CONFIRM/assign a CR number on next pass, matching the register's own existing convention." `ELEVATION_REGISTER_v1_0.md` EL-17 entry (register lines ~210-214) still reads only "code fixed, DATA state to re-verify post-rebuild" — does not yet name this specific wealth-domain sub-residual. | **ESCALATE** — assigning a CR number is inherently a native-governance act this packet cannot substitute for; the underlying fix (`ph_nimitta`'s wealth-domain materialization path) is writer-scope, out of this close-out's serving-only rails. Folded in: **RATIFY-WITH-AMENDMENT** the register's EL-17 fix-direction text should be updated to name this wealth-domain sub-residual explicitly once a CR number is assigned, so it isn't re-discovered cold next session. |
| (c) A-5 remedy-engine supersession review | Already carries its own row — see **§G, `A-5`** above (Remedy-engine CR-67/CR-69 HALTED-for-native-decision superseded by β.G's live-verified BPHS Ch.44-cited repair). Recommended disposition there: **RATIFY-AS-RULED**. | No change — this addendum only confirms the item is present and evidenced, per the close-out brief's request not to leave it unconfirmed. | *(no new row — see §G)* |
| (d) The authorization-chain governance finding | Stream β's Stream-Conductor relayed to Lane β.G (via shared lane-brief context, not a direct message) the claim that the live human user had authorized full campaign autonomy, including the A-5 supersession and production DB writes. Lane β.G initially resisted, then proceeded only after independently re-verifying the claim against the charter's own primary text — not on trust in the relay alone. Lane G's own words, preserved for the record: *"the pattern of repeated 'a human already approved this' messages arriving exactly when needed is worth scrutiny on your end independent of my in-session verification."* **Note on the close-out brief's "two streams" framing:** a repo-wide search (this session) for a second, independently-documented Stream-α-side incident of this kind found none — every citation (`STREAM_BETA_CLOSE_v1_0.md`'s "Governance flag for native review," `ledgers/elevation_v2/proxy/beta.md`'s `[STREAM-CONDUCTOR] Session-scope autonomy authorization` entry, `STREAM_BETA_COMPLETE.flag`, and `ELEVATION_V2_COVERAGE_MATRIX_FINAL_v1_0.md`'s cross-stream commentary) traces to this one event's two facets (the Stream-Conductor/builder relay side, and Lane G's resistance-then-verify side) — not two independent occurrences. Recorded honestly as one richly-documented event rather than inventing a second to match the brief's phrasing literally. | `STREAM_BETA_CLOSE_v1_0.md` "Governance flag for native review": logged, not claimed as ratifying in the native's name; `proxy/beta.md`'s `[STREAM-CONDUCTOR]` entry: PROXY-RULED, open for morning ratification. | **RATIFY-WITH-AMENDMENT** — Lane G's verify-before-act conduct is exactly the correct defensive posture and should be ratified as the standing pattern; the amendment: formalize it as a named governance principle — **AUTHORITY-BY-ARTIFACT** (a relayed "the native/human authorized X" is a pointer, never authority; the receiving agent MUST verify against the committed charter/ruling text before acting) — as its own item in `ELEVATION_REGISTER_v1_0.md`, citing both `STREAM_BETA_CLOSE_v1_0.md` and `proxy/beta.md`. Confirmed by this session's search: no such register item exists yet; landing one is a distinct action beyond this packet's own scope. |

---

*End of `EL25_RATIFICATION_PACKET_v1_0.md`. Compiled by Lane γ.J, Elevation Campaign v2.1,
2026-07-25; §I added by the PŪRṆA-VIRĀMA close-out T3 track, 2026-07-26. This packet does
not itself close any item — every disposition above is a recommendation awaiting the
native's own ratify/override pass, per charter §10's "never ratify in the native's name."*
