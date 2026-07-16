---
artifact: BRIEF_D1_6
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-1.6 "Śuddhi" — pre-D2 total cleanup (silent-wrong-answers, yoga/dosha integrity, timing
  substrate, serving debt, infra one-liners, verify-then-close, governance reconciliation)
version: 1.0
status: FROZEN — native-ordered 2026-07-16 ("everything taken care of, big or small, before D-2").
  Binder re-verifies every binding at open; several items are VERIFY-THEN-CLOSE candidates that
  D-1.5b may already have fixed (Lane S-7) — do not re-implement what a probe proves green.
authored_by: Fable 5 (Cowork 2026-07-16), from the full-estate open-items sweep of REPORT_D-1.5a/b,
  STATE_D-1.5b, POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0 (CR-1..107), MARSYS_DEFECT_GAP_REGISTER_v2_0
  (v3.0), CURRENT_STATE §2, DEPLOYED_TOOL_CENSUS_2026-07-13.
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md
prerequisite: D-1.5b gate GREEN (met — 17/17, main @ aa1bad9f)
scope_ruling: >
  Native-ratified 2026-07-16 (Cowork): bucket-7 engine work stays in its designed waves and is
  EXCLUDED here — MSR class-prior/tier-ceiling/valence internals (CR-81/82/83 → D-1 scope already
  absorbed), CGM→ranking (CR-84/85/86 → D-2), convergence engine + hardcoded-natal-constants +
  suppression model (CR-87/88/89, CR-107 → D-3), KP sub-lord engine (KP-1/2/3/5, CR-75 → its
  dispositioned wave), calibration loop (CR-79, T-11, C-5), LEL retrodiction (CR-68), chain-signal
  class (CR-24 → G-6/LCA-9a in D-2), leverage_index (CR-69), nakshatra-semantic + arudha + D11 +
  special-lagna ranking classes (CR-26/61/62/76/77 → D-1/D-2 signal-class work), discovery engine
  (CR-78), content-depth C-1/C-3/C-6 (D-4 gate). Touching these here dissolves the campaign design.
gate: Gate Ś (§G below) — all assertions as MCP calls on the DEPLOYED connector post-rebuild,
  same battery harness as Gate B; plus the register/state reconciliation checks (§G.14–16).
---

# D-1.6 Śuddhi — leave nothing behind

Definition of done (R-5, unchanged): merge → deploy → rebuild Abhisek (482012f1) SCOPE-LIMITED to
touched layers → Gate Ś green on the deployed connector → verified cleanup → registers updated.
Abhinandan (1c826d5a) read-only.

## FROZEN §F1 — Lane map (8 lanes + native-rulings queue)

### Lane S-1 — Silent-wrong-answer purge (highest priority; these actively mislead)
- CR-42 / R-19 / R-20: ref_*/remedial filter fallthrough — every filter param either HONORED or
  the call REJECTED loudly (Saturn query must never serve Jupiter remedies). Includes CR-10
  case-normalization (planet="Venus" vs "venus").
- CR-55: `weakest_graha` in the chart digest is factually wrong (says Mercury; actual Venus by its
  own metric) and is injected into nearly every reading — recompute from the live strength table,
  add a regression assertion pinning digest weakest_graha == argmin(shadbala-derived weakness).
- CR-51 / CR-30: twin aliases returning DIFFERENT payloads (query_calibration vs
  mimamsa_calibration_get) — one canonical face per capability; the capability map marks the live
  face; the other becomes a strict alias or is retired.
- T-8: stale hardcoded "Mercury MD (2026-2043)" citation on muhurta windows — derive from
  chart_dashas.
- R-21 / R-22 / CR-63: receipt honesty — no ✓/complete/timing_anchored:true with zero evidence
  rows; pact_status must not say chain_complete over a failed TRIGGER.
- CR-47: phala_rectification lel_fit_score flat 0 across 185 candidates yet presented as a
  successful ranking — serve an honest non_discriminating flag (full method fix stays K-6/later).

### Lane S-2 — Dosha integrity (CR-72 / CR-73 / CR-74 / Y-11-dosha-half)
All 22 dosha_label rows share ONE constituent fact and no per-chart computation — decorative.
(a) Per-dosha computed verdict (fired/not-fired) from real chart facts for the catalogued set;
(b) cancellation checks where classical (Kemadruma MUST NOT fire alongside fired Anapha/Sunapha —
the current false-positive specimen); (c) Kāla-Sarpa: serve the genuinely computed per-varga
verdict (kala_sarpa_per_varga) as the authoritative answer; the label row must never contradict it;
(d) constituent_facts_array points at the ACTUAL grounding facts per dosha (kills the shared-stub).
Doshas whose computation is genuinely not implementable this wave: quarantine honestly
(fire_reason=not_evaluated, excluded from default page) — B.10, no fake negatives either.

### Lane S-3 — Yoga engine integrity (the acharya-grade blocker cluster)
- Y-2 (CRIT): wire `ga_yoga_firings` into serving — `ganita_yoga_firings_get` becomes the
  firings-authoritative surface actually consumed by judgment/assess/digest paths; catalog
  yoga_label rows remain cross-check only (§N.6.1).
- Y-4 / CR-56 / CR-22 / CR-35: house-lord yoga family DETECTED and FIRING — Dhana family
  (2/5/9/11 lord combinations), Lakshmi, Saraswati, Budha-Aditya (with combustion guard),
  Dharma-Karmadhipati + Kendra-Trikona Raja (Y-8 stubs replaced with real logic; no silent
  `return False`). Type specimens (482012f1): Budha-Aditya H10 non-combust FIRES; Saraswati FIRES
  (Jup own Sag trikona + Ven H9 + Mer kendra); Dhana 2L+9L conjunct H9 FIRES.
- Y-3 / CR-59 / CR-34: NBRY per-varga — detector extended beyond D1 (D9 minimum), grounds recorded
  per verdict (which classical conditions checked/met). Type specimens: Saturn D9 Aries + Sun in
  D9 lagna kendra → NBRY fires; Venus D9 Virgo + Mercury D9 kendra → NBRY fires. Doctrine grounds
  per DR ruling from the native-rulings queue (CR-23) — lane BLOCKS on that ruling for grading,
  not for detection plumbing.
- Y-5 / Y-6: cancellation as a first-class state on firings (bhaṅga fields populated, D9
  cross-check modifiers no longer hardcoded 1.0).
- Y-10: skip-list comment cleanup + duplicate entry removed; tool descriptions updated (S-11) so
  no surface claims a family it doesn't evaluate — and none UNDER-claims post-this-lane.
- Y-11: constituent grounding — firings cite their real fact_ids (shared with S-2d).
- Y-12 / CR-33 / CR-43: v3 verdict-builder counts the rows it serves; never fabricates "not
  formed" from a truncated page; catalog rows never presented as confirmed findings.
- Y-13: land the in-progress redemption-map fix (pure-D9-context NBRY firings redeemable).

### Lane S-4 — Timing substrate (make time answerable without doing D-3's engine work)
- R-45 (CRIT root): kala_activation writer populates activation_start/end (~99% NULL today) —
  this is a WRITER date-population defect, distinct from the D-3 convergence-engine scope.
- CR-5 / CR-12 / CR-48: populate `active_dasha_periods_jsonb` + real dasha_alignment (kills the
  flat 0.5); yoga_activation_by_dasha returns dated rows over a 3-year window.
- CR-1 / R-39: judgment_query timing_hooks wired to chart_dashas + (now-dated) kala_activation.
- CR-4 / CR-29 / T-10: window-family collapse — one window, N member signals, per-domain flavor;
  budget get_temporal_windows; kala_projections domain filter + max_projections honored (CR-6).
- T-3: as_of_date forwarded; expired dashas never served as active; unreachable TRIGGER never
  counted complete (overlaps S-1 receipt honesty).
- T-12 / T-13: honest flags only this wave (single-transit-cycle limitation + build-date-artifact
  "near" windows disclosed in payload) — the multi-cycle generator is D-3.
- T-5 / T-9 (anchors predate birth; 1950 parvas): dedicated sub-lane via the Cloud Run job path
  (the D-1.5b-validated route around O-8). If the rebuild still can't complete the backfill, PARK
  with the O-8 root cause attached — but attempt is mandatory, 7 prior retries died to infra.

### Lane S-5 — Serving-quality debt (TypeScript; single owner of the retrieval registry)
- PARK-A7 + R-17: ganita_structural_get facet routing (aspects facet serves
  aspect_parashari_given/received; graha_yuddha/parivartana return their OWN row sets).
- PARK-#4 / CR-90: the 5 residual keyword_heuristic_v1 valence rows — re-emit from the fixed
  builder or re-classify; assertion #4 goes green or the rows are proven unreachable dead data.
- R-18: estate-wide silent parameter no-op audit (start/end/domain/limit) — honor or reject; add
  a harness assertion that every documented param provably filters.
- R-1 / R-8 / CR-49 residuals: oversize stragglers (assess_career, event_anchors, phala_anchors/
  mitigation 421/528KB, get_cgm_subgraph) under C1-style budgets with hardFloor discipline (§N.6).
- Small-bore fixes: R-23/CR-50 residual (canonical content leads), R-25 (tajaka current-varsha
  reachable), R-28 (house_from_frame delivered or param removed), R-30 (judgment v3 narration),
  R-32 (narration budget mid-sentence cut), R-24 (grounding honors limit), R-26 (strip embedding
  vectors), R-27 (class vocab), R-29 (double-encoded JSON), R-33 (dosha_fires v3 default), R-34
  (triage), R-35/S-1-adjacent (honest vargottama list shape), R-36 (stale-marker contradiction),
  R-2 (derive epistemic grade), R-5 (no raw SQL in errors), R-6, R-7 residuals, CR-15 (pact names
  activating graha), CR-11 residual (empty_reason estate-wide), CR-45 (headline subjects), CR-44 /
  R-8 (assess_* payload sections), D-12/D-14 (brief contradictions; grounding_score=0 bug),
  D15b-F3 (min_weight→min_salience alias), CR-16 (special-lagna services accept chart_id).
- S-13: coverage-matrix CI gate reads live category enumeration (so S-class gaps CAN fail CI).
- S-7 / S-12 residual: per-varga siblings + divisional serving holes closed or honestly faceted.

### Lane S-6 — Infra one-liners + ops hardening
- R-15 / O-6: remedy bundle DATABASE_URL (6 primitives + 6 aliases up).
- R-16 / O-5: ref_transit_rules whitelist gap + asset_registry proxy isPublic gap (two fixes).
- Census stragglers: ref_planet_position_get literal-"undefined" date; ref_ephemeris_year_get 404
  URI registration.
- Track-2 CONFIRM: ephemeris/transit sidecar green — ref_planet_transit_get answers without 401
  AND kala_temporal_bundle sidecar_available=true (CR-40/T-1; hard prereq for D-3 — if not green,
  this lane executes the restore per the Track-2 scope note in CLAUDECODE_BRIEF).
- O-2: stream-reaper Cloud Scheduler URI (terraform apply).
- O-1 + D15b-F1: minimal server-side rate limiting + harness client throttle/backoff + non-5xx
  error-body retry (the Gate-B 429 cascade).
- D15b-F2: bodha_writers/__tests__ collected by the standing CI gate.
- D15b-F4: deploy.yml path-detection ruling (platform/-only change → amjis-mcp rebuild needed or
  provably not).
- D15b-F5: ga_vargas target_floor re-baseline.
- O-8: root cause documented + a detection alarm (proxy-kill cycle); full fix may PARK with
  evidence — the Cloud Run job path remains the sanctioned workaround.
- O-7: alias→primitive conformance check added to the harness (pairs S-1 canonical-face work).

### Lane S-7 — Verify-then-close pass (probe first; close register rows; NO re-implementation)
Probe on the deployed connector and mark CLOSED-with-evidence or route back into S-lanes:
CR-18 (shadbala ratios — B-5), CR-50 (ordering — B-6), CR-58 (D2 hora — B-5/B-7), CR-60
(dasha_lord_capability — B-7), CR-46 (anchor dedup — B-5), CR-49 members (B-6/B-7 budgets),
CR-57 (varga-ratification-divergence — check whether shipped), S-12 (divisional_facts — B-7),
S-14 (ganita_medical/vastu tools), S-4/S-5 (sputa drishti; gandanta), K-3-Sudarshan (B-3),
KP-4 (final close), R-48 (skeleton REMEDIATED-PENDING-W4), D-5 (attribution 0% claim), R-47/
sensitive_degrees overlap (CR-31 55-row shipment vs S-9 per-sign compute), CR-7/R-11
(traverse_graph — CR-53 says did-not-reproduce; retest and close or reopen).

### Lane S-8 — Governance & register reconciliation (docs/data only; no code)
- CR-90..107 merge debt: re-integrate into POST_REMEDIATION_CONSUMPTION_REGISTER (or formally
  stamp the register §A–§I rows as the intake and the doctrine-briefs as system-of-record, with a
  SUPERSEDED-pointer note) — one system of record, no dangling row ranges (CR-96's own lesson).
- MARSYS_DEFECT_GAP_REGISTER_v2_0: sync every row this wave closes/parks; assign permanent IDs to
  §E CR-33..38 per the register's merge protocol.
- CURRENT_STATE §2: already advanced to the D-1.5b-close/D-2-incoming banner (Cowork 2026-07-16);
  conductor re-advances at THIS wave's close.
- Legacy M-series carry-forwards (KR.M4A.RT.LOW.1, R.LL1TPA.1, GAP.M4A.04, F-020, OPEN_ITEM.P1.1):
  triage to CLOSED-OBSOLETE / KEEP-with-owner — a one-table disposition appended to CURRENT_STATE.
- Binder remit: add the read-only enforcement note to CONDUCTOR_PROTOCOL (2 recorded incidents of
  planning-role writes outside remit; the structural fix is tool-access restriction).
- MARSYS_DEFECT_GAP_REGISTER_v1_0: confirm ARCHIVED-retained-in-place marker (hygiene §A), no edits.

### Native-rulings queue (PARK class — route to native, never auto-adjudicate)
1. CR-23 / DR-candidate: NB doctrine — which classical grounds the detector recognizes (engine vs
   two-ground derivation; first live P-3 case). S-3 grading blocks on this.
2. CR-28: intent_classify returns a prompt, not a classification — RATIFY as the P-10 contract or
   redesign.
3. C-6: composed 2+-tool rubric items — product-boundary call (feeds D-4's gate, decide now).

## §G — Gate Ś (all MCP on deployed connector post-rebuild)
1. Filter honesty: Saturn remedy query returns only-Saturn or explicit rejection (never Jupiter).
2. Digest weakest_graha == recomputed argmin (regression-pinned).
3. Alias parity: canonical face == alias payload for every twin pair in the capability map.
4. Dosha verdicts: Kemadruma NOT fired (Anapha cancellation); Kāla-Sarpa served verdict ==
   kala_sarpa_per_varga computed fact; zero shared-stub constituent arrays on the default page.
5. Yoga firings: Budha-Aditya + Saraswati + Dhana(2L·9L) FIRE on 482012f1 via
   ganita_yoga_firings_get, each grounded in real fact_ids.
6. NBRY: Saturn-D9 and Venus-D9 firings present with recorded grounds (post-DR ruling).
7. v3 verdict counts served rows: a page containing the Sasa row can never say "Sasa not formed".
8. Timing: judgment_query(482012f1, wealth) timing_hooks non-empty and dated;
   yoga_activation_by_dasha returns ≥1 dated activation in 2026–2029; no flat-0.5 alignment wall.
9. Window families: get_temporal_windows top-50 contains >1 distinct window; ≤40KB.
10. Receipts: zero ✓-with-empty-evidence across the battery; pact TRIGGER honesty.
11. Oversize: no tool >64KB default page across the 32-battery sweep (hardFloor sections intact).
12. PARK-#4 and A7 assertions green (or #4's residual rows proven dead with evidence).
13. Infra: remedy primitives answer; asset_registry 200; ref_transit_rules 200;
    ref_planet_transit_get no-401; sidecar_available=true; scheduler URI verified.
14. Registers: no OPEN row in either register left un-dispositioned (CLOSED / PARK-with-evidence /
    EXCLUDED-to-wave-N with pointer); CR-90..107 range resolved to one system of record.
15. CURRENT_STATE + CLAUDECODE_BRIEF pointers advanced; SESSION_LOG close block appended.
16. Full 32-battery re-run: everything green except items EXPLICITLY parked with evidence this
    wave; zero NEW reds vs the D-1.5b baseline.

## §S — Scope declaration
may_touch: platform/** (writers, retrieval registry, harness), platform-mcp/**, pyjhora_adapter/**,
  migrations (surgical only, §N.4), 00_ARCHITECTURE/llm_consumption_audit/** (registers, briefs,
  STATE_D-1.6/REPORT_D-1.6), 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (§2 banner at close),
  CONDUCTOR_PROTOCOL.md (Binder-remit note only), infra config for S-6 items.
must_not_touch: FROZEN orchestrator core (§N.2 — writers conform, never extend), bucket-7 engine
  internals listed in scope_ruling (MSR prior/tier/valence formulas, CGM ranking joins, convergence
  engine, KP sub-lord engine, calibration/LEL loop), 99_ARCHIVE/**, chart data for 1c826d5a
  (read-only), CLAUDE.md (except version-bump if the conductor's close requires), deploy.yml
  auto-migration paths (§N.4).

## §C — Close condition
Gate Ś 16/16 (or 15 + evidence-backed PARKs, native-visible), REPORT_D-1.6.md + STATE_D-1.6.md
sealed, registers reconciled, pointers advanced to current_wave: D-2, worktrees cleaned. D-2 then
opens onto a clean substrate with Track-3 vidhi drafts ready for its Binder.
