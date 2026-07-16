---
artifact: BIND_D-1.6
type: BINDER PASS RECORD (CONDUCTOR_PROTOCOL §1 Binder / §2 step 1 OPEN)
wave: D-1.6 "Śuddhi"
bound_at: this session (2026-07-16, D-1.6 Binder pass; no runtime timestamp source)
binder: Claude Fable 5
brief_status_recommendation: BOUND (all BIND-AT-OPEN slots resolved below; conductor stamps)
probe_channel: >
  Live deployed connector, both faces per §8.1 ruling: marsys-jis-direct MCP tools (small
  payloads) + raw JSON-RPC POST to https://amjis-mcp-938361928218.asia-south1.run.app/mcp
  (?api_key seat) for byte-size probes and tools/list. NOTE: the Bearer face
  (amjis-mcp-qm256lasva-el.a.run.app + MARSYS_MCP_KEY from scripts/setup_mcp_env.sh) returned
  401 "Invalid or missing Bearer API key" this session — key appears rotated/stale. Flagged for
  Lane S-6/harness: the Gate Ś harness must verify its channel at open (the ?api_key face is
  confirmed live).
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek), ayanamsha lahiri_chitrapaksha
---

# BIND_D-1.6 — Binder findings

```yaml
wave: D-1.6
bound_at: this session (2026-07-16; no real-timestamp source in-session)

s7_probes:
  - item: CR-18 (shadbala required-minimum ratios)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_chart_facts_get(keyword=required_rupa) → 7 rows live, graha_shadbala_total.*.
      required_rupa (JUP 6.5, MAR 5.0, MER 7.0, MOON 6.0 …), ayanamsha_id=INVARIANT served
      (the D-1.5b B_shadbala_ratio IN($2,'INVARIANT') fix holds), verification=classical_match.

  - item: CR-50 (positions default ordering / upagraha flood)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_positions_get default page → categories=["graha_position"] only; 9 grahas + Lagna;
      include_upagrahas=false by default and upagrahas are served AFTER, never interleaved
      (tool contract states CR-50 explicitly; live rows confirm no PIDAA/PATALA on default page).

  - item: CR-58 (D2 hora semantic layer)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_chart_facts_get(divisional_chart=D2) → varga_hora_class rows live with
      surya_hora/chandra_hora + hora_d2_house per graha. Exact CR-58 type specimen reproduced:
      Sun/Jupiter/Rahu(+Ketu, Lagna) = surya_hora, D2 H1; Venus/Saturn/Mercury/Moon/Mars =
      chandra_hora, D2 H12 ("both wealth lords in the passive hora, in the 12th of the wealth
      chart" is now servable from stored facts).

  - item: CR-60 (dasha-lord capability index)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_dasha_lord_capability_get live → 9 lords with house_class, shadbala_percentile,
      functional_lordship, ratification_factor, deterministic warning_tier; fact_ids resolve;
      honest judgment_flags for Rahu/Ketu/Moon gaps. Register specimens served: Ketu percentile
      0.125 → watch; Venus 4.64 rupa / percentile 0.25 → watch.

  - item: CR-46 (phala anchor dedup)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      phala_anchors_get(2020–2030) → anchor_count=4, all 4 distinct event types (no 98-dup
      flood; count is post-dedup). Bonus honesty: a call without date_range is now REJECTED
      loudly (422 field-required), not silently defaulted. Payload 20KB (was 421KB).

  - item: CR-49 members (B-6/B-7 budget fixes)
    verdict: CLOSED_WITH_EVIDENCE (B-6/B-7-budgeted members) + residuals ROUTE_TO_LANE S-5
    evidence: >
      Live byte counts, default-ish args: bodha_domain_reading_get 41KB (per Gate B receipt),
      assess_career 47KB (was 724KB), event_anchors 14KB, ganita_tajaka_get 56KB (was
      unbounded), phala_anchors 20KB (was 421KB) — all under the 64KB Gate Ś ceiling.
      RESIDUAL >64KB (already in Lane S-5's brief text): get_cgm_subgraph 99.7KB,
      phala_mitigation_get 99.9KB (was 528KB — improved, still over), get_projections 70KB,
      traverse_graph 99KB at depth=1.
    lane_if_routed: S-5 (residual members only)

  - item: CR-57 (varga-ratification-divergence signal class)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      bodha_signals_get(signal_type_class=varga_ratification_divergence) → live signals, e.g.
      "SATURN: D1 exalted vs D9 debilitated — wealth/career/health ratification fails in D9",
      salience 1.2, signature_tier=major, valence=malefic (ga_vichara_v1), constituent facts
      resolve. Shipped by D-1 Night-1 Lane 4 (bo_laksana change 2.4) + ga_vichara LANE2.

  - item: S-12 (divisional-chart serving hole, 21,635 chart_divisionals rows)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_chart_facts_get(divisional_chart=D2|D9) serves a chart_divisionals-native
      divisional_facts section (D2: 200 rows; D9: 178 rows — per-varga dignity, vargottama,
      pushkara bhaga/navamsha, house lords/occupants, deities, rollups), budget-capped and
      source-tagged (D-1.5b #575). The EAV layer is MCP-visible.

  - item: S-14 (ganita_medical / ganita_vastu direct reads)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      Both tools live and chart-scoped: ganita_medical_get → 9 rows (per-graha dosha/organ
      watch, indication tiers, BPHS citations, not_diagnosis flag); ganita_vastu_get → 8 rows
      (graha→direction, condition_score, Mayamata citations). Matches CR-31 "shipped" note.

  - item: S-4 (graduated sputa/virupa drishti served)
    verdict: ROUTE_TO_LANE
    evidence: >
      ganita_structural_get(facet=aspects) declares aspect_parashari_given/_received in its
      categories but the default page leads with aspect_jaimini rasi-drishti boilerplate;
      virupa_strength rows not observed on the served page — this is exactly the standing A7
      PARK (writer verified correct in D-1.5a; 19 real aspect_parashari_given rows exist in DB;
      serving-layer facet routing never landed). Data computed; serving incomplete.
    lane_if_routed: S-5 (PARK-A7 + R-17 facet routing, already first bullet of that lane)

  - item: S-5 (gandanta computed-but-unserved)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_sensitive_degrees_get serves per-graha gandanta rows with degree evidence
      (e.g. JUP not_gandanta, arc 3.3333°, deg_in_sign 9.7875 — honest negative), inside the
      55-row sensitive_degree_check category; check_type filter exposed. Permanently in a tool
      enum → closable.

  - item: K-3-Sudarshan (Sudarśana Chakra rebuilt)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      bodha_signals_get(signal_type_class=sudarshana_agreement) → 9 tri-frame signals live
      (per-graha house/class from Lagna/Moon/Sun, agreement verdicts incl. contradicted /
      partial_2frame), constituent facts resolve 0-orphan. D-1.5b B-3 receipt confirmed live.
      NOTE: K-3's Sarvatobhadra remainder has nakshatra-occupancy recorded
      (sarvatobhadra_vedha row in sensitive_degree_check) but no vedha-line service; Kota not
      built — the K-3 register row stays open for those halves (not this S-7 item's scope);
      S-8 to disposition the register row as PARTIAL-with-pointer.

  - item: KP-4 (KP domain tags + cusp-longitude noise)
    verdict: CLOSED_WITH_EVIDENCE (domain-tag core) + noise residual ROUTE_TO_LANE S-5
    evidence: >
      bodha_signals_get(paradigm=kp, domain=wealth) → 19 kp rows reachable in the wealth slice
      (the original "Mars-in-Rahu's-star can NEVER surface in wealth" defect is dead);
      composite ranking tops with CUSP_11 sub_lord=Mercury (correct). RESIDUAL: raw
      cusp_longitude_sidereal noise rows still served at ranks 2–4 of the wealth slice — the
      WP-1.2 "cusp-longitude noise demotion" is not effective on the live composite path.
      Also all 19 rows carry valence_source=keyword_heuristic_v1 (evidence input for S-5's
      PARK-#4 scoping: the residual population is larger than the 5 "non-node" rows assertion
      #4 counts).
    lane_if_routed: S-5 (noise demotion residual; PARK-#4 scoping evidence)

  - item: R-48 (large-N synthesis skeleton, REMEDIATED-PENDING-W4)
    verdict: ROUTE_TO_LANE
    evidence: >
      Deployed tools/list (165KB, grepped live) contains NO synthesis/compose_large_n tool
      face (only synth_chart_brief_get / synth_tail_divergence_get). The register's
      "synthesis/compose_large_n deployed + 7/7 prod-verified" claim cannot be confirmed on
      the connector's tool surface — the module may be internal-only. NOT closable as served
      capability on this evidence.
    lane_if_routed: S-8 (re-disposition the register row: either evidence the internal path
      that W4-verifies it, or mark EXCLUDED-to-wave with pointer per DR-5's boundary ruling)

  - item: D-5 (digest entity attribution 299/300 UNATTRIBUTED)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      bodha_chart_digest_get(summary) → attribution block: served_unattributed_entities=0,
      served_unattributed_share=0, candidate_pool 300 with 0 unattributed (WP-1.2β note).
      BONUS (S-1 pre-evidence, not an S-7 item): digest weakest_graha="Venus" with source
      "shadbala_total_min (BPHS Ch.27; CR-55 fix)" — CR-55 appears already fixed live; Lane
      S-1 should verify-then-close rather than re-implement, keeping the regression assertion.

  - item: R-47 / sensitive_degrees (CR-31 55-row shipment vs S-9 per-sign compute)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      ganita_sensitive_degrees_get → total_matching=55 rows for 482012f1: per-graha
      mrityu-bhaga/gandanta/pushkara/kartari/22nd-drekkana class with degree+orb evidence
      (JUP papa_kartari fired with flanking grahas listed). The R-47 "labeled but never
      computed per graha" defect is dead; CR-31's shipment confirmed live on this chart.

  - item: CR-7 / R-11 (traverse_graph DSL first-character parse)
    verdict: CLOSED_WITH_EVIDENCE
    evidence: >
      traverse_graph(about="lord_of(bhava 10)", depth=1) → parses and resolves correctly
      (about_resolution: H10 from Aries lagna = Capricorn → Saturn → placed 7th Libra);
      15 nodes / 148 edges, is_error=false. Did-not-reproduce, matching CR-53's retest note.
      SIZE NOTE → S-5: the depth-1 response is 99KB (>64KB Gate Ś ceiling) — CR-49-family
      budget work, not a parse defect.

doctrine_rulings:
  - item: CR-23 (NBRY doctrine grounds)
    dr_id: DR-4 (register DIS.017)
    ruling: >
      Scope resolution: engine's D1 "not_applicable_or_intact" for Jupiter is CORRECT for D1;
      the classical NBRY derivation is varga-scoped — no doctrine conflict once every NB
      verdict carries its varga scope. Recognized cancel grounds (evaluated in the varga where
      the debility occurs, kendra from that varga's lagna or Moon): G-a dispositor in kendra;
      G-b graha-exalted-in-debility-sign in kendra; G-c exaltation-sign lord in kendra;
      G-d debilitated graha exalted in D9 (D1 case). G-e (debilitated graha itself in kendra)
      = supporting only, never sufficient alone. bhanga fires on any of G-a..G-d; raja_grade
      when >=2 grounds met or the cancelling graha is own-sign-or-better. grounds_jsonb records
      checked AND met per verdict. Varga-scoped NBRY never restates as a D1 fact.
    rationale: >
      Phaladeepika-mainline ground set; matches CR-34/CR-59 hand-derived specimens (Saturn D9
      Aries cancelled via G-b Sun-in-D9-lagna; Venus D9 Virgo cancelled via G-a/G-b Mercury in
      D9 H7); preserves B.10/§N.5 fact-layering; unblocks S-3 grading without letting either
      side of the P-3 conflict silently win.

  - item: C-6 (composed 2+-tool rubric product boundary)
    dr_id: DR-5 (register DIS.018)
    ruling: >
      Option (a) with a bridge: grade each tool call against its own contract, plus a
      composition check over an EXISTING composed instrument (judgment_query,
      synth_chart_brief_get, domain readings) where one covers the question. Items requiring
      cross-tool narrative synthesis with no existing composed instrument are EXCLUDED from
      the D-4 floor with an explicit product-boundary note, queued as R6/R-48-class candidates
      for native ratification. Building an in-product orchestrating-LLM step is REJECTED as a
      campaign deliverable (product-architecture change, PARK-class), without prejudice
      post-campaign.
    rationale: >
      Consistent with the ratified floor-model rule (§5) and §N.6 serving-density doctrine:
      the instrument serves dense honest composable layers; the consuming LLM composes. A gate
      must not be blocked on an engine class the campaign is designed not to build.

engineering_routed:
  - item: CR-28 (intent_classify returns a prompt, not a classification)
    note: >
      Routed to Opus adjudicator-engineering per §4.1 — prompt-delegation vs in-product
      classification is an engineering contract trade-off (latency, model-dependence, caller
      coupling), not a doctrine question. Not ruled here. Probe context: intent_classify +
      util_intent_classify both present on deployed tools/list.

rebuild_scope:
  full: false
  layers: >
    asset_set (minimal DAG cascade, §8.2 MINIMAL-CASCADE RULE), computed by the conductor from
    asset_registry.depends_on at rebuild time over the merged writers' changed-asset set.
    Expected changed assets from the lane map: ga_yoga (+ dosha verdict machinery, S-2/S-3),
    ga_structural only if S-3 touches aspect/firing substrate; ka_activation-family (S-4 R-45
    date population); ph_nimitta / ph_rectification (S-4 T-5/T-9 backfill + CR-47 honest flag);
    + their true downstream dependents (bo_laksana and Bodha closure for yoga/dosha signal
    classes; ka_yoga_activation-class consumers; ph_* anchors consumers). Lanes S-1/S-5/S-6
    are serving/TS/infra — no rebuild. Abhisek 482012f1 only; Abhinandan never rebuilt.
  rationale: >
    None of the three §8.2 full-rebuild triggers fires: (a) no NEW L1 fact category ingested
    downstream — S-2/S-3 extend existing yoga/dosha firing+verdict categories MSR already
    ingests, S-4 populates existing NULL date columns (writer-population defect, explicitly
    distinct from D-3 engine scope); (b) no shared-substrate change — valence formulas,
    Mechanism object and convergence kernel are all in the brief's must_not_touch/scope_ruling
    exclusions; (c) no migration altering existing column SEMANTICS — §N.4 surgical/additive
    discipline governs, and any migration here is additive (grounds_jsonb, verdict fields).
    CONDITIONAL FLAG for the conductor: if an implementer lands a genuinely NEW chart_facts
    category (e.g. per-dosha computed verdicts as a new fact_category consumed by MSR), that
    still does NOT force full L1→L5 — the asset_set cascade already includes the MSR ingest
    path (bo_laksana + Bodha closure); expand to the DEP-ASSERTed dependents only, per the
    minimal-cascade rule's own escalation clause.

binder_notes:
  - Bearer-face key (scripts/setup_mcp_env.sh MARSYS_MCP_KEY) returns 401 on
    amjis-mcp-qm256lasva-el.a.run.app — rotated or revoked. ?api_key face live. Gate Ś harness
    must channel-check at open (S-6/O-1 adjacency); key rotation remains the campaign-close
    hygiene item per §8.1.
  - S-7 tally: 13 CLOSED_WITH_EVIDENCE, 2 ROUTE_TO_LANE (S-4→S-5, R-48→S-8), 2 closed-core
    with residuals routed to S-5 (CR-49 oversize stragglers; KP-4 cusp-longitude noise).
  - Free evidence for other lanes: CR-55 weakest_graha=Venus already live (S-1 verify-then-
    close); phala_anchors date_range loud-rejection is receipt-honesty prior art (S-1);
    kp rows' valence_source=keyword_heuristic_v1 population sizes PARK-#4 (S-5).
  - Rollback pin (§2.1): conductor to record deployed image SHAs + Abhisek build_id at spawn —
    binder had no gcloud describe run in this pass; last known main @ aa1bad9f, amjis-mcp @
    470f2290 per REPORT_D-1.5b.
  - Binder remit item (S-8): CONDUCTOR_PROTOCOL read-only-enforcement note is S-8's to write —
    NOT written by this Binder pass (two prior incidents of planning-role writes are exactly
    why); this pass wrote only the two files its task remit allows.
```
