---
artifact: CLAUDECODE_BRIEF_BODHA_L1E_GA_STRUCTURAL_ENRICHMENT_v1_0.md
canonical_id: BODHA_L1E_BRIEF
version: 3.0
status: READY_TO_EXECUTE (this is the FIRST runnable step of the L2 Bodha arc; B1 depends on it)
authored_by: Cowork (planning) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
v3_scope_expansion: >
  Native max-fidelity decisions (2026-06-17). L1-E is NOW A TWO-ASSET ENRICHMENT, executed in order:
  PHASE L1-E.A — extend ga_strength to compute shadbala + ashtakavarga PER-VARGA (D1–D30), not D1-only
    (CODE-VERIFIED: today ga_strength is D1-grain; its "varga" refs are vimsopaka aggregate schemes, not
    per-varga). Per-varga shadbala is a COMPUTED EXTENSION (classical shadbala is traditionally D1) — it
    MUST be labelled as such with method cited in formula_provenance, never presented as canonical Parashara.
    This reopens a SECOND sealed L1 asset (ga_strength) with its own verification + re-seal.
  PHASE L1-E.B — ga_structural builds the FULL multi-entity relationship graph, consuming per-varga strength.
  Expansions: D3 is now a MULTI-ENTITY graph (nodes = grahas, houses/bhavas+lords, signs/rashis,
  nakshatras(27)+lords/padas, vargas, special points [arudhas/AL, chara+sthira karakas, karakamsa/swamsa,
  upagrahas, sahams, special lagnas], AND CONFIGURATIONS as first-class nodes). Every EDGE carries a FULL
  VALUE VECTOR: intrinsic strength + benefic/malefic VALENCE + affected-domains + directionality +
  weight_varga_source provenance. Multi-hop chains bounded (defined edges only, genuine tie per hop,
  cycle-detection, max-depth cap). Configs-as-nodes lets grahas participate-in / houses be affected-by /
  configs reinforce-or-contradict each other. CODE-VERIFIED varga facts: ga_strength=D1, ga_sensitive=D1+D9,
  ga_structural=the only all-30-varga asset.
v2_enhancements: >
  Native-approved enhancements (2026-06-16), all consistent with L2_BODHA_MASTER_PLAN_v3_0 + the
  dedup/ownership rules. DEEPEN: D1 derive relationships across ALL 30 vargas (not D1-only — the ingested
  assets carry varga/ayanamsha grain, ga_structural already enumerates all vargas); D2 stamp a
  relationship_basis type on each derived tie (strength_weighted / av_supported / arudha_tie / kp_chain /
  panchanga_lord / sade_sati_structural — the L1 analog of B1's fact_kind); D3 capture multi-hop
  reasoning chains incl. 3+ hops, BOUNDED by deterministic guardrails (defined edges only, genuine tie
  per hop, cycle-detection, full hop-path stored with per-hop source fact_id). HARDEN: H1 the Trap-1
  guardrail becomes a BUILD-TIME ASSERTION (writer fails the build if a row would restate a single source
  value — not just a post-run check); H2 FORENSIC 7/7 is an IN-RUN pre-commit gate (refuse to commit if
  an anchor moved); H3 a rebuild-determinism proof (build→rebuild→identical count+fact_ids). PREPARE:
  P1 stamp each derived relationship's INTRINSIC strength as an L1 column here (intrinsic belongs at L1;
  B1 adds only population-level salience — keeps the intrinsic-vs-population line clean). DECLINED: P2 —
  ALL L0 classical bridging stays in B1 (no split across layers).
scope: L1-E ONLY — enrich ga_structural to ingest the 4 currently-un-ingested L1 assets and derive their
  RELATIONAL value, re-verify FORENSIC 7/7, re-seal at the new count. NOT bo_laksana (that is B1).
execution_mode: CONTINUOUS within sub-steps; STOP on a real dependency miss or a Tier-3 event
  (destructive op / genuine ambiguity / needed architecture change → raise to native). NOTE: this brief
  REOPENS A SEALED L1 ASSET — that is the deliberate, native-approved purpose (new completeness, not
  reorganization). Treat the re-seal + FORENSIC re-pass as hard gates.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_MASTER_PLAN_v3_0.md §2 (L1-E in the dual-capture model)
  - L2_BODHA_L1E_SCOPE_AND_DEDUP_v1_0.md (the per-asset derivation scope + the ownership/dedup rules — THE spec for this brief)
  - L1_GANITA_CLOSURE_v1_0.md (the L1 sealed record this brief reopens) + L1_GANITA_BUILD_CLOSE_v1_0.md
  - MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1 — the load-bearing guardrail here)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract — ga_structural conforms)
precedent_to_follow:
  - "The GA8 completeness amendment (migration 227 + ga_structural_writer.py all-30-vargas rework) is the
     EXACT precedent: it already extended ga_structural with NEW relationship families (kala_sarpa_per_varga,
     lord_in_house_per_varga, graha_yuddha, combustion_relationship, …) and re-floored the count from
     6,075 → 74,644. L1-E is the SAME KIND of operation — new relationship families ingesting cross-asset
     data — done the same way. Read migration 227's header + the corresponding writer sections first."
target_files:
  - platform/python-sidecar/ga_writers/ga_strength_writer.py (L1-E.A — add per-varga shadbala + ashtakavarga)
  - platform/python-sidecar/ga_writers/ga_structural_writer.py (L1-E.B — ingestion + full relationship graph)
  - two surgical migrations (ga_strength re-floor + ga_structural depends_on/re-floor, mirroring migration 227)
must_not_touch:
  - the FROZEN orchestrator contract (WriterBase / registry mechanics / asset_throughput)
  - ga_sensitive / ga_sade_sati / ga_panchanga writers — L1-E READS their chart_facts output; does NOT modify them
  - (NOTE: ga_strength IS modified in L1-E.A — it is no longer read-only; ga_structural IS modified in L1-E.B)
  - any bo_* (L2) writer
---

# L1-E — Enrich ga_structural (the dual-capture model's L1 step)

## §0 — What L1-E is, in one paragraph
`ga_structural` is L1's cross-asset RELATIONAL synthesizer. Today it ingests positions/vargas/upagrahas/
chara-karakas but NOT the relational consequences of strength, the rest of sensitive, sade-sati, and
panchanga. L1-E completes that wiring: ga_structural INGESTS those 4 assets' chart_facts and derives the
NEW RELATIONSHIPS among them (relationships that cannot exist without cross-asset data — e.g. "weak Saturn
aspects the 10th-lord"). It stays L1, stays relational. The output is the richer relational fabric that B1
(bo_laksana) will later project. **This reopens the ga_structural seal — deliberately, for genuine new
completeness — and re-seals it only after FORENSIC 7/7 re-passes.**

## §0B — TWO-PHASE STRUCTURE (execute in order)
**L1-E.A — ga_strength per-varga** (reopens ga_strength). Compute shadbala + ashtakavarga across all 30
vargas (D1–D30) × 5 ayanamshas, so every varga relationship in L1-E.B has native-varga strength.
**L1-E.B — ga_structural full relationship graph** (reopens ga_structural). Consumes per-varga strength;
builds the multi-entity typed/signed/weighted relationship graph.
L1-E.A MUST complete + re-seal before L1-E.B runs (B reads A's output). Each phase has its own FORENSIC/
verification gate + re-seal.

## §0C — PHASE L1-E.A — ga_strength per-varga (the new strength substrate)
**Goal:** shadbala (+ components) and ashtakavarga computed PER VARGA (D1–D30), not just D1.
- Today (verified): ga_strength computes shadbala/ashtakavarga from D1; its shadvarga/saptavarga/dasavarga/
  shodasavarga refs are vimsopaka AGGREGATE schemes, NOT per-varga strength. Extend it to compute the
  strength set in each of the 30 vargas GA6 produces (reuse ga_structural's `ALL_30_VARGAS` list as the
  canonical varga set so the two assets agree).
- **PROVENANCE HONESTY (mandatory):** per-varga shadbala is a COMPUTED EXTENSION. Classical shadbala is
  traditionally a D1 (rāśi) computation. Every per-varga strength row MUST carry `formula_provenance_text`
  marking it "computed extension: shadbala method applied to <varga> chart; not classical-D1 shadbala" +
  the method reference. Do NOT present per-varga shadbala as canonical Parāśara. (This is the same
  honesty-of-provenance discipline used everywhere — a research-instrument extension, labelled as such.)
- Idempotency: per-chart delete-then-insert (§N.3). Two-pass verification per varga (the ashtakavarga
  sum=337 invariant applies PER VARGA's rāśi frame — verify the per-varga analog holds).
- **D1 strength is unchanged** — the existing D1 rows keep their exact values + fact_ids (no perturbation;
  this is purely ADDITIVE — new per-varga rows alongside the existing D1 rows).
- Re-floor ga_strength target_floor to achieved; widen count_sql to include the new per-varga categories.
**L1-E.A acceptance [verify-against: prod]:** per-varga shadbala+ashtakavarga present for all 30 vargas ×
5 ayanamshas; D1 values UNCHANGED (existing fact_ids stable); every per-varga row labelled as a computed
extension; two-pass per-varga invariant holds; ga_strength re-sealed at new count. **Then proceed to L1-E.B.**

## §1 — THE LOAD-BEARING GUARDRAIL (Trap 1 / dedup-by-ownership) — read before any code
Per `L2_BODHA_L1E_SCOPE_AND_DEDUP §1`: **a raw value is owned by the asset that computes it; ga_structural
owns only RELATIONSHIPS.** When ga_structural ingests another asset's fact, it emits a row **only if that
row is a NEW relationship (a tie between ≥2 elements, OR an enrichment edge over an existing tie)**. It
**NEVER restates the source's bare value as its own structural row** — it REFERENCES the source `fact_id`
in the derivation provenance. Magnitude stays owned by ga_strength (one fact_id); the relationship is a new
fact_id citing it. **Crossing this line builds the drift trap into L1.** Every new row carries its source
fact_id(s) in provenance; this is verified at acceptance.

**Derived-relationship tail policy (native decision):** derive EVERY structurally-valid relationship;
store its strength/salience as a COLUMN; NEVER drop (no-threshold-drop). A "genuine tie" = the elements
stand in a defined classical relation (aspect / conjunction / lordship / dispositor / argala / co-tenancy /
significator); strength is a column on that tie, not a gate.

**Inherited non-negotiables:** deterministic-first (Python; no LLM); no audience tier; no silent drops
(skips logged, zero in a clean run); per-chart isolation; **real sha256 fact_ids, never mock**; FROZEN
orchestrator contract (ga_structural stays a conforming WriterBase — runs on ctx.db_conn, never commits,
no asset_throughput writes); two-pass verification on all new rows (the existing ga_structural discipline);
count_sql data-truth; floors aspirational. **If a contract change seems needed → STOP, raise with native.**

## §1B — Enhancements (v2.0) — deepen + harden, all plan-consistent
Apply these THROUGHOUT §3–§5. They make the relational layer richer and more provably honest — which is
exactly what CGM and the synthesis LLM inherit.

**D1 — Multi-varga derivation (the biggest depth lever).** Every derived relationship is computed across
ALL 30 vargas where it applies, NOT D1-only. The ingested assets carry varga + ayanamsha grain
(ga_strength: varga+ayanamsha; ga_sensitive: D1/D9+ayanamsha) and ga_structural already enumerates all 30
vargas. So "weak Saturn aspects 10th-lord" is derived in D10 (career), D9 (dharma), etc. — each a DISTINCT
fully-qualified row (varga × sign × ayanamsha × houses), per the existing ga_structural disambiguation rule.
Volume grows; that is the intended completeness (no-drop).

**D2 — relationship_basis typing.** Stamp each derived tie with a `relationship_basis` ∈ {strength_weighted,
av_supported, arudha_tie, karakamsa_tie, kp_chain, panchanga_lord, sade_sati_structural, comparative_strength}.
This is the L1 analog of B1's fact_kind — it lets CGM weight edges by type and lets the LLM later say WHY
two elements relate. Deterministic column; no value restated.

**D3 — THE FULL MULTI-ENTITY RELATIONSHIP GRAPH (the centerpiece — think of it as building the graph at L1).**
Not planet-to-planet chains — a typed, signed, weighted, multi-entity fabric. This is where the synthesis
LLM's reasoning power comes from, so build it deepest.

*NODE TYPES (entities that can stand in relationships):* grahas (9 incl. Rahu/Ketu); houses/bhavas (12) +
house-lords; signs/rashis (12) + lords/element/modality; nakshatras (27) + lords/padas (Moon's especially);
vargas (D1–D30) as contexts + vargottama status; special points (Arudhas incl. AL, chara + sthira karakas,
Karakamsa/Swamsa, Upagrahas, Sahams, special lagnas); and **CONFIGURATIONS as first-class nodes** (a named
yoga / dosha / conjunction / aspect-pattern is itself a node).

*EDGE TYPES:* aspect (Parashari/Jaimini/Tajik); conjunction / co-tenancy; lordship / dispositor;
nakshatra-lordship; argala / virodha-argala; occupancy (graha-in-house / -sign / -nakshatra); participation
(graha is a constituent of config X); vargottama / cross-varga correspondence; combustion / graha-yuddha;
significator (KP chains, karaka significations); comparative (stronger-than). Configs-as-nodes adds:
grahas PARTICIPATE-IN a config; houses are AFFECTED-BY a config; configs REINFORCE or CONTRADICT each other.

*EVERY EDGE CARRIES THE FULL VALUE VECTOR (native decision — deterministic from existing facts):*
`intrinsic_strength` (orb tightness + the per-varga shadbala/bindu weighting it + participant dignity);
`valence` (benefic / malefic / mixed — does the tie help or harm); `affected_domains` (life-areas it
touches); `directionality` (directed for aspects/argala/significator; mutual for conjunction); and
`weight_varga_source` (which varga's strength weighted it — now NATIVE per-varga after L1-E.A, so a D10 tie
uses D10 strength). This is what lets the LLM say "Saturn AFFLICTS the 10th, malefic, tight orb, career-domain, in D10."

*DEEP-RELATIONSHIP IDEAS (build these, not just pairwise edges):*
1. **Dispositor cascade as a directed tree** to the self-disposited root (the chart's center of gravity) —
   store the whole tree, not one-hop links.
2. **Bhāva-to-bhāva edges via lords** ("10th-lord in 5th" → house 10 relates to house 5) — how acharyas read houses.
3. **Argala as a signed directional intervention sub-graph** (X intervenes on Y, Z blocks it).
4. **Karaka significator web** (chara + sthira; the Ātmakāraka's relationships = the Jaimini spine).
5. **Reinforcement-vs-contradiction edges between configurations** (feeds bodha_contradictions + convergence at B2).
6. **Cross-varga persistence edges** ("this tie holds in 7/16 vargas" — persistence is itself a strength signal).

*MULTI-HOP CHAINS — BOUNDED (deterministic guardrails mandatory):* chains traverse ONLY the defined edges
above (never arbitrary pairs); every hop is a genuine tie; **cycle detection** closes revisits; a
configurable max-depth cap (default 6) keeps the space finite; the FULL ordered hop-path is stored with
**each hop citing its own source fact_id** (Trap-1 per hop); stored as rows with `relationship_basis=chain`
+ `hop_count`. A chain not deterministically constructible within these rules is NOT emitted (no guessing).
Feeds `bodha_cgm_paths` at B2.

**H1 — Trap-1 as a BUILD-TIME ASSERTION (not just post-run verify).** Before inserting any new row, the
writer asserts it has ≥2 constituent fact_ids OR is an explicit enrichment edge over an existing tie. A row
that would restate a single source asset's bare value FAILS THE BUILD (loud error, not a silent skip).
Reuse the existing `_get_constituent_fact_ids` machinery (ga_structural_writer.py ~line 1309). This makes the
drift trap structurally impossible, not merely caught.

**H2 — FORENSIC 7/7 as an IN-RUN pre-commit gate.** Compute the 7 birth anchors inside the writer's
verification pass and REFUSE TO COMMIT the enrichment if any anchor moved. The enrichment is purely additive
(new relationship rows), so the anchors CANNOT legitimately move — any movement is a bug, caught immediately
rather than after the whole build.

**H3 — Rebuild-determinism proof.** After the first build, rebuild ga_structural and assert IDENTICAL count
AND identical fact_ids (deterministic, delete-then-insert, no accretion). Guards the "accretes on rebuild" bug.

**P1 — Intrinsic strength stamped at L1 (clean intrinsic-vs-population line).** Each derived relationship
stores its INTRINSIC strength as an L1 column (orb tightness, the shadbala/bindu that weighted it, the
composite tie-strength) — computed ONCE here. B1 then adds ONLY population-level salience (rank / convergence
/ contradiction) over it. This keeps the plan's L1-intrinsic-vs-L2-population boundary clean and prevents
intrinsic strength from leaking into L2.

**P2 — DECLINED (kept for the record).** L0 classical-source stamping is NOT done here — ALL L0 bridging
(catalog + rules + texts) happens in B1, in one place, per the master plan. L1-E stays purely relational.

## §2 — Preconditions (verify on prod; fix-forward if any fail)
1. Cloud SQL proxy up (127.0.0.1:5433).
2. The ingested assets are BUILT for the native chart: ga_strength, ga_sensitive (8,055), ga_sade_sati
   (11,019), ga_panchanga (221), and GA6 divisionals (the 30-varga source). If any is unbuilt, STOP.
3. **L1-E.A (per-varga strength) is COMPLETE + re-sealed before L1-E.B** (B reads A's per-varga output).
4. Record CURRENT counts as baselines for the re-floors: ga_strength (~2,184), ga_structural (74,644).
5. Read migration 227 + the all-30-varga sections of ga_structural_writer.py (the precedent) + GA6's
   `ALL_30_VARGAS` list (the canonical varga set both phases must agree on).

## §3 — The work: ingest + derive, per asset (implements L2_BODHA_L1E_SCOPE_AND_DEDUP §2)
Extend `ga_structural_writer.py` following its existing `_load_*` ingestion pattern (e.g. `_load_varga_
positions`, `_load_special_points` at lines ~634 / ~2820 read chart_facts today — mirror that). For EACH
asset below, add a loader + a relationship-derivation pass. Each new row carries: real sha256 fact_id;
source fact_id(s) in `constituent_facts_array` (≥2, or an enrichment-edge marker — enforced by H1);
`relationship_basis` (D2); INTRINSIC strength column (P1); and is derived across ALL applicable vargas
(D1). Multi-hop chains (D3) additionally carry the ordered hop-path + `hop_count`, each hop citing its
source fact_id. Two-pass verified.

### 3.1 — ga_strength → strength-conditioned relationships
Ingest shadbala (total + components), ashtakavarga bindus, bhava-bala, ishta/kashta phala, vimsopaka.
Derive (each cites the strength fact_id + the structural tie's fact_id):
- strength-weighted aspect/conjunction enrichment edges over EXISTING ga_structural aspects/conjunctions
  (tie already exists → annotate with the strength relation; do NOT create a new pair, do NOT restate the
  bare shadbala number);
- ashtakavarga-supported vs starved house-occupancy ties;
- strength-modulated yoga-participation ties (per fired yoga, each participant's strength contribution);
- comparative relative-strength ties where they change a dispositor/lordship consequence.
**MUST NOT** re-store the bare shadbala/bindu/phala value (ga_strength owns it; it reaches MSR by B1
projecting ga_strength directly).

### 3.2 — ga_sensitive (non-ingested part: arudhas, karakamsa, swamsa, KP significators)
Ingest the 12 arudha padas, karakamsa, swamsa, KP cuspal significators + ruling planets.
Derive: arudha↔graha / arudha↔house aspect-ties; karakamsa significator ties (lord/occupants/aspects);
swamsa aspect/occupancy ties; KP significator chains (cusp → graha → star-lord → sub-lord).
**MUST NOT** re-store the bare arudha/karakamsa POSITION (ga_sensitive owns it).

### 3.3 — ga_sade_sati → STRUCTURAL ties only (temporal activation is L3 Kāla, NOT here)
Ingest cycle/phase/quarter/overlay/cancellation rows.
Derive the STRUCTURAL tie only: "Saturn-transit-house structurally ties to natal Moon-significations",
flagged `sade_sati_relevant=true`; cancellation-relationship where a cancellation rule depends on a
structural config. **MUST NOT** store time-windows/phases as structural rows (ga_sade_sati owns them) and
**MUST NOT** compute WHEN it is active (that is L3 — do not reach into the time layer).

### 3.4 — ga_panchanga → birth-moment structural ties
Ingest tithi/vara/yoga/karana/nakshatra/hora/etc.
Derive: panchanga-yoga↔graha ties (the yoga lord's relationships to natal grahas); tithi/vara-lord↔chart
ties; Moon's-nakshatra-lord placement/aspect ties. **MUST NOT** re-store the bare tithi/vara/yoga value
(ga_panchanga owns it).

## §4 — DAG + registry update (surgical migration, mirror migration 227)
- Add to `ga_structural.depends_on`: `[ga_strength, ga_sensitive, ga_sade_sati, ga_panchanga]` (it already
  transitively depends on positions/vargas). The orchestrator self-orders from this.
- Re-floor `ga_structural.target_floor` to the achieved post-enrichment count (floors aspirational — set to
  achieved, never fabricate). Update `count_sql` if the category family filter needs widening to include
  the new relationship categories (so the cockpit tile counts them).
- Fresh migration number (no collision); apply surgically to prod; readback after.

## §5 — Run + verify (the gates)
1. Run ga_structural for the native chart via the orchestrator (single-asset rebuild). It reads the 4
   assets' chart_facts and emits the new relationship rows (delete-then-insert idempotency). **H1 (build-time
   Trap-1 assertion) and H2 (in-run FORENSIC pre-commit gate) fire DURING this run — the build fails/refuses
   to commit if a row restates a bare value or an anchor moved.**
2. **FORENSIC 7/7 RE-PASS (hard gate, also verified post-run):** Sun=Capricorn · Moon=Purva Bhadrapada ·
   Lagna=Aries · Tithi=Shukla Tritiya · Vara=Ravivara · Yoga=Shiva · Karana=Garaja, all 5 ayanamshas. The
   enrichment must NOT perturb the 7 birth anchors. `[verify-against: prod]` **If FORENSIC fails, HALT.**
3. **Trap-1 / dedup proof:** every NEW row is a relationship (≥2 constituent elements OR an enrichment edge)
   AND cites its source fact_id(s); ZERO rows restate a single source asset's bare value (H1 should already
   guarantee this — verify it held). Spot-check 10 new rows + 3 multi-hop chains resolve all cited source
   fact_ids per hop. `[verify-against: prod]`
4. **Count grew honestly:** record old 74,644 → new N; report the delta broken down per ingested asset AND
   per relationship_basis (D2) AND per varga (D1) AND chains vs direct (D3). `[verify-against: prod]`
5. **H3 rebuild-determinism:** rebuild once; assert identical count + identical fact_ids (no accretion).
6. **Two-pass verified; no silent drops** (skips logged = zero). **Cockpit truth:** ga_structural tile shows
   the new count via its count_sql (widened to include the new relationship categories).

## §6 — Re-seal
Only AFTER §5 all-green: update the L1 sealed record (`L1_GANITA_CLOSURE` / `L1_GANITA_BUILD_CLOSE`) to the
new counts of BOTH reopened assets with a changelog note ("L1-E dual-capture enrichment: (A) ga_strength
per-varga shadbala+ashtakavarga D1–D30, +<delta_A> rows, labelled computed-extension, D1 unchanged;
(B) ga_structural full multi-entity relationship graph ingesting per-varga-strength/ga_sensitive/
ga_sade_sati/ga_panchanga → +<delta_B> relationship rows incl. config-nodes + full edge-value vector;
FORENSIC 7/7 re-passed on both; Trap-1 build-time assertion held"). Update CURRENT_STATE §2 + append
SESSION_LOG atomically. Both assets re-sealed at their new counts. **L1-E done → B1 (bo_laksana) unblocked.**

## §7 — Acceptance (the whole gate)
- [ ] **L1-E.A:** ga_strength computes shadbala + ashtakavarga per-varga (D1–D30 × 5 ayanamshas); D1 values UNCHANGED (fact_ids stable); every per-varga row labelled a computed extension (provenance honesty); two-pass per-varga invariant holds; ga_strength re-sealed.
- [ ] ga_structural ingests per-varga-strength + ga_sensitive(remainder) + ga_sade_sati + ga_panchanga.
- [ ] New rows are RELATIONSHIPS only, each citing source fact_id(s); ZERO bare-value restatements — **enforced as a build-time assertion (H1), not just verified.**
- [ ] **D3 graph:** multi-entity nodes (grahas/houses/signs/nakshatras/vargas/special-points/CONFIGS); full edge-type set; the 6 deep-relationship structures (dispositor tree, bhāva-to-bhāva, argala sub-graph, karaka web, reinforce/contradict, cross-varga persistence) built.
- [ ] **Edge value vector:** every edge carries intrinsic_strength + valence + affected_domains + directionality + weight_varga_source.
- [ ] **D1:** relationships derived across all applicable vargas (per-varga rows, not D1-only), weighted with NATIVE per-varga strength.
- [ ] **D2:** every derived tie stamped with relationship_basis.
- [ ] **D3:** multi-hop chains captured, bounded (defined edges only, genuine tie per hop, cycle-detected, max-depth capped, full hop-path stored with per-hop source fact_id); non-deterministic chains NOT emitted.
- [ ] **P1:** each relationship stamped with its INTRINSIC strength column at L1 (B1 adds only population salience).
- [ ] Derived-relationship tail: all real ties derived, strength as a column, none dropped.
- [ ] sade-sati = structural tie + flag only; NO temporal activation computed (L3 boundary respected).
- [ ] **P2 boundary held:** NO L0 classical stamping here (all L0 bridging is B1's).
- [ ] depends_on updated; target_floor re-floored to achieved; count_sql counts new categories; cockpit true.
- [ ] **FORENSIC 7/7 re-passed on all 5 ayanamshas** — as an **in-run pre-commit gate (H2)** AND post-run; two-pass verified; no silent drops.
- [ ] **H3:** rebuild-determinism proven (identical count + fact_ids on rebuild).
- [ ] ga_structural re-sealed at the new count; CURRENT_STATE + SESSION_LOG updated.
- [ ] FROZEN contract honored; migration fresh; surgical apply + readback held.

## §OUT OF SCOPE for L1-E
bo_laksana / MSR projection (B1 — consumes this output). Any L2 asset. Computing WHEN a relationship is
active (L3 Kāla). Modifying the 4 ingested writers (read-only). Re-firing predicates / G52. Any
orchestrator-contract change.

---
*End of BODHA_L1E v1.0 — ga_structural ingests the 4 un-ingested L1 assets and derives their relational
value (relationships only, citing source fact_ids, Trap-1-guarded, all real ties kept + ranked, sade-sati
structural-tie-only). Same operation class as the GA8 amendment (migration 227 precedent). FORENSIC 7/7
re-pass is the hard gate before re-seal. Completing this unblocks B1.*
