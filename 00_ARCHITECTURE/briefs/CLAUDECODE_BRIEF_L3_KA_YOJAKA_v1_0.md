---
artifact: CLAUDECODE_BRIEF_L3_KA_YOJAKA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_YOJAKA
brief_for: ka_yojaka — Yojaka / The ACTIVATION-PREDICATE BRIDGE (L3 Kāla; THE CRUX — Q2)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.2 + §5.12 (Q2 RESOLVED — class→template bound per signal), §5.12.3 (the taxonomy), §5.12.4 (the 3-part template), I-15 (author the templates), §6 (the L2→L3 contract: signature_class + NULL hooks), §5.7.3/I-7 (strength weights), §3.1 (signal_activator.py v1 = the seed)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K3
  blocked_by: [ka_graha_sancara, ka_dasha_kala, ka_gochara]  # the templates' triggers are evaluated by these engines
  blocks: [ka_sangam, ka_vighnakara, ka_kalasutra, ka_kala_darshana]  # everything that SEARCHES needs the predicates
  may_touch:
    - platform/python-sidecar/services/ka_yojaka/**                       # NEW — classifier + binder
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py   # NEW writer (artifact: the predicate table)
    - 00_ARCHITECTURE/L3_KALA_ACTIVATION_TEMPLATES_v1_0.md                 # NEW — the authored class→template table (I-15)
    - platform/scripts/temporal/signal_activator.py                        # READ-ONLY reference (the v1 seed)
    - platform/supabase/migrations/<next>_kala_activation_predicates.sql   # NEW table for the bound predicates
    - platform/scripts/seed/asset_registry_seed.ts                         # register ka_yojaka (artifact-kind)
  parallel_safe_with: [ka_muhurta_seva]   # disjoint; must follow the 3 engines it evaluates against
---

# CLAUDECODE BRIEF — ka_yojaka (The Activation-Predicate Bridge) — THE CRUX (Q2)

## §0 — What this asset IS
`ka_yojaka` (Yojaka, "the joiner") is the **activation-predicate bridge** — the glue between L2's
timeless structure and L3's temporal engines. For each L2 signal it (1) **CLASSIFIES** the signal into a
`signature_class` (an activation archetype), (2) **BINDS** that class's activation-rule TEMPLATE to the
signal's own constituents, producing (3) a concrete **activation predicate** = {a daśā-eligibility rule
for `ka_dasha_kala` + a transit-trigger condition for `ka_gochara` + a strength/affliction hook}. Without
`ka_yojaka`, the funnel, Mode B, the catalog, and the intervention loop have NOTHING to search FOR. **It
is the load-bearing crux of the layer (plan Q2).**

## §1 — Why it matters / strategic role
- **It is what makes "when does MY Lakshmi yoga fire" answerable** (plan §5.2) — it turns a structural
  signal into a *searchable temporal condition*.
- **It is deterministic-at-scale (plan §5.12.2).** Tens of thousands of MSR signals → ~10–15 archetypes
  → ~10–15 templates, each BOUND per signal. Not a per-signal rule (unmaintainable), not a free
  derivation (non-deterministic). **General per class; specific per signal.**
- **It fills the L2-reserved NULL hooks (plan §6).** L2 deliberately left `signature_class`,
  `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb`, `dasha_activation_proximity_score`
  NULL. `ka_yojaka` defines + populates `signature_class` (in an L3 artifact, REFERENCING the L2
  `signal_id` — **L3 NEVER writes back into the sealed L2 tables**).

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **`signature_class` is RESERVED but UNPOPULATED** — `bo_laksana.py` line 787 writes it `None`; no
  migration defines its vocabulary. The three L3 NULL hooks are at lines 787/792/793. **ka_yojaka
  defines the vocabulary + classifies.**
- **The signal carries the classification inputs** (`bo_laksana.py`): `signal_id`,
  `constituent_facts_array` (from `fact_value_jsonb.constituent_facts_array`), `yoga_label`/`yoga_fires`,
  `dosha_label`/`dosha_fires`, `kala_sarpa_per_varga`, `graha_yoga_karaka_flag`, plus the full per-varga
  relational config. These are the deterministic fields the classifier keys on (plan §5.12.3).
- **`bg_transit_rules`** (registered L0 writer) + **`ga_transit_anchors`** = the CLASSICAL rule + anchor
  source the templates cite (every template carries a DERIVATION_LEDGER to these). Read their actual
  schema at build time; cite specific rule_ids.
- **The v1 seed:** `signal_activator.py::decide_state` (daśā MD/AD lord ∈ `entities_involved` → "lit";
  next-AD-within-90d → "ripening") IS the YOGA-class daśā-eligibility rule in primitive form. Generalize
  it; replace its markdown-MSR parse with a DB read of `bodha_msr_signals`.

## §3 — The build (TWO artifacts + the binder)
**3.1 — The signature_class CLASSIFIER (deterministic, from existing fields).** An L3 unit reads each L2
signal and assigns ONE `signature_class` from the taxonomy (plan §5.12.3):
| class | assigned when |
|---|---|
| YOGA | `yoga_label`/`yoga_fires` set |
| DOSHA | `dosha_label`/`dosha_fires` set (incl. `kala_sarpa_per_varga`) |
| DIGNITY | graha dignity / `ga_strength` state is the signal's core |
| DISPOSITOR/RELATIONAL | `parivartana_per_varga` / dispositor-chain |
| SENSITIVE-POINT | arudha / karakamsa / kp_cuspal / swamsa |
| CONJUNCTION/ASPECT | `conjunction_within_orb` / `aspect_parashari_given` |
| SUBSYSTEM | `ga_sade_sati` / `ga_medical` / `ga_vastu` reference |
Output: one `(signal_id, signature_class)` row per L2 signal, in the L3 artifact (references signal_id;
never restates the signal). Handle precedence (a signal matching >1 → a documented priority order).

**3.2 — The class→template TABLE (I-15 — the authored artifact; the heart of this brief).** Author
`L3_KALA_ACTIVATION_TEMPLATES_v1_0.md`: ~10–15 templates, ONE per signature_class. Each template has the
plan §5.12.4 three parts, each a STRUCTURED, deterministic, CITED predicate:
1. **Daśā-eligibility rule** — e.g. YOGA: *eligible when MD/AD (or deeper) lord ∈ {constituent lords ∪
   their dispositors}*. (Generalizes the v1.)
2. **Transit-trigger rule** — a set of trigger-events from the `ka_gochara` vocabulary
   (aspect/conjunction/ingress/return/station), parameterized by the signal's houses/lords — e.g. *fires
   when a constituent lord or a benefic transits a kendra/trikona from the yoga's house, or aspects the
   yoga's lord, free of affliction*.
3. **Strength-modulation + affliction-veto hook** — which graha's dignity/shadbala scales the FORCE
   (I-7), and the affliction condition that vetoes/dampens (feeds the danger engine `ka_vighnakara`).
Each template carries a **DERIVATION_LEDGER** citing the `bg_transit_rules` rule_id(s) + the classical
source (the templates encode CLASSICAL activation principles, not invented ones — plan §5.12.5). **The
weights are native-ratified judgments (I-7) — PROPOSE each with classical rationale + source, mark
`[NATIVE-RATIFY]`, do NOT silently finalize. HALT for sign-off on the weight set (plan §5.7.3 guardrail).**

**3.3 — The BINDER.** For each classified signal, instantiate its class's template by reading the
signal's `constituent_facts_array` (which grahas/houses/signs) → a concrete predicate object the engines
can evaluate. Store the bound predicates in `kala_activation_predicates` (the new table), one per
signal, referencing `signal_id`. This is an ARTIFACT-asset (it stores rows) — `asset_kind='artifact'`.

**3.4 — Generalize the v1 (plan §5.12.7).** Reuse `signal_activator.py`'s daśā-interval lookup + transit
read; swap its `MSR_v3_0.md` markdown parse for a DB read of `bodha_msr_signals`; extend from "lit NOW"
to "the predicate object" the SEARCH evaluates over a horizon; replace flat-0.6 with the strength-
modulated magnitude (the rigor stratum scores it later, in `ka_sangam`).

## §4 — Asset registration
`ka_yojaka`: `asset_kind='artifact'`, `layer:'kala'`, sanskrit `'Yojaka'`, english `'Activation bridge'`,
`target_table:'kala_activation_predicates'`, `count_sql:'SELECT count(*) FROM kala_activation_predicates
WHERE chart_id=$1'`, `depends_on:['bo_laksana','bg_transit_rules','ga_dashas']` (reads L2 + L0 rules +
the daśā timeline; the engines it FEEDS depend on IT). Per-chart; delete-then-insert idempotency (plan §N.3).

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** every L2 signal for `482012f1` gets exactly ONE `signature_class`; the
   classification is deterministic (same input → same class); precedence documented + tested.
2. **[verify: pytest]** the YOGA-class predicate for a KNOWN yoga (e.g. a Lakshmi/Dhana yoga) binds to
   the correct constituent lords + houses from its `constituent_facts_array`.
3. **[verify: pytest]** each template's daśā-eligibility rule, evaluated against `ka_dasha_kala`, marks
   the correct periods live for a constructed signal; the transit-trigger, against `ka_gochara`, fires
   on the correct event.
4. **[verify: anti-drift]** every predicate row REFERENCES an L2 `signal_id` that resolves; ka_yojaka
   writes NOTHING into `bodha_msr_signals` or any L2 table (grep the writer — zero L2 writes).
5. **[verify: ledger]** every template carries a DERIVATION_LEDGER citing a real `bg_transit_rules`
   rule_id; no template rests on "as is known classically" without a source (plan B.3).
6. **[verify: NATIVE-RATIFY gate]** the influence-weight set (I-7) is presented as proposals with
   rationale + source and HALTS for native sign-off before finalization (not silently chosen).
7. **[verify: psql_prod + curl_prod]** `ka_yojaka` registered (artifact-kind) with a correct
   chart-scoped count_sql; cockpit shows a row count; rebuild is idempotent (delete-then-insert).
8. **[verify: FORENSIC]** the classifier + binder run cleanly on the 7/7-FORENSIC native chart; no signal
   fails to classify (a 100%-coverage assertion, or a documented residual list with reasons).
9. **[contract]** the writer runs on `ctx.db_conn`, never commits/rolls back it (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-yojaka
# the reserved hooks + classification inputs
sed -n '300,320p;720,800p' platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py
# the v1 seed to generalize
sed -n '140,210p' platform/scripts/temporal/signal_activator.py
# the classical rules to cite
grep -n "seed_transit_rules\|rule_id\|INSERT INTO" platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py
# tests
cd platform/python-sidecar && pytest -q services/ka_yojaka -k "yojaka or classify or template or predicate"
```
> Branch/merge: Madhav human-gated PR (plan memory). NOTE: the I-7 weight set + the I-15 template doc
> are NATIVE-RATIFY gates — the Conductor must HALT and surface them, not auto-finalize.

## §7 — Definition of done
- [ ] signature_class classifier: 1 class/signal, deterministic, full coverage for 482012f1.
- [ ] L3_KALA_ACTIVATION_TEMPLATES authored: ~10–15 cited templates (3 parts each), weights flagged for ratify.
- [ ] Binder → kala_activation_predicates (references signal_id; anti-drift clean).
- [ ] v1 generalized (DB read, not markdown).
- [ ] Registered artifact-kind; idempotent; FORENSIC-clean; native weight sign-off obtained.
- [ ] PR opened with AC evidence + the HALT for the I-7/I-15 ratify gate.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Builds the one piece without which nothing else can search** — every downstream engine (Mode A,
   Mode B, the catalog, the intervention loop) is inert until `ka_yojaka` turns structure into temporal
   predicates; this is the literal keystone of the layer.
2. **Defines the signature_class vocabulary L2 reserved but never filled** — closing a real gap (the
   hook was `None` with no migration) WITHOUT reopening the L2 seal, by owning the taxonomy in L3 and
   referencing the signal_id (pure anti-drift).
3. **Encodes classical activation as a deterministic, cited template set** — the ~10–15 templates make
   the layer acharya-grade AND machine-runnable at once: each carries a DERIVATION_LEDGER to
   `bg_transit_rules`, so no activation rests on hand-waving "per tradition."
4. **Resurrects and generalizes a working v1** — the stranded `signal_activator.py` already proved the
   daśā-lord-∈-constituents pattern works; the brief reuses its bones and spends its effort on the
   taxonomy + binding + strength-coupling, not on re-proving the concept.
5. **Forces the strength-weights through a native-ratify gate** — making the I-7 judgments explicit,
   sourced, and sign-off-gated means the layer's most subjective parameters are auditable and the
   build never silently invents weights (the corpus's canonical-or-floor discipline).
6. **Makes the whole layer testable against lived reality** — because the predicates are concrete and
   datable, a KNOWN past activation (an LEL event) can be replayed through them, which is exactly what
   L3's computational eval gate (§5.4) and L5's calibration later require.

---
*End of CLAUDECODE_BRIEF_L3_KA_YOJAKA v1.0. The crux. Two NATIVE-RATIFY gates inside (I-7 weights, I-15 templates).*
