---
artifact: CLAUDECODE_BRIEF_L3_KA_KALA_DARSHANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_KALA_DARSHANA
brief_for: ka_kala_darshana — Kāla-darśana / THE LIFETIME CONFLUENCE CATALOG (L3 Kāla; the standing discovery product) [NEW]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.11.4-K (the lifetime confluence catalog — L3's bo_anveshana twin), QT-7 (discovery/wonder), §5.11.5 (apex insights: off-daśā activations, cross-subsystem convergence, window-collision, cost-of-omission), §5.13.C1 + I-13 (cross-subsystem temporal convergence), §5.10 (chart-bound + finite → PRECOMPUTE), §7 (discovery engine applied to time)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K5
  blocked_by: [ka_sangam, ka_vighnakara]   # the catalog is Mode-B run exhaustively over the engines' output
  blocks: [ka_tulana, ka_bhavishya_lekha]  # prioritization + prediction-records draw from the catalog
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py   # NEW writer (exhaustive Mode-B sweep + store)
    - platform/python-sidecar/services/ka_kala_darshana/**                        # NEW
    - platform/supabase/migrations/<next>_kala_darshana.sql                       # NEW table (mirrors bodha_discoveries shape)
    - platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py       # READ-ONLY reference (the structural twin)
    - platform/scripts/seed/asset_registry_seed.ts                                # register ka_kala_darshana (artifact-kind)
  parallel_safe_with: []   # CORRECTED 2026-06-21 (collision audit): NOT parallel with ka_vighnakara — the catalog's window-collision detection (§3.4) READS danger windows, so ka_vighnakara must land first within K5. Runs after ka_vighnakara.
---

# CLAUDECODE BRIEF — ka_kala_darshana (The Lifetime Confluence Catalog) [NEW]

## §0 — What this asset IS
`ka_kala_darshana` (Kāla-darśana, "the vision/seeing of time") is **the standing lifetime discovery
product**: the convergence engine (`ka_sangam` Mode B) run EXHAUSTIVELY once over chart × the native's
lifetime × all subsystems, with the rarest, most consequential temporal confluences STORED, ranked, and
provenanced — "the wonders of your timeline." It is **L3's twin of L2's `bo_anveshana`** (plan §5.11.4-K,
§7): structural discovery finds the consequential pattern in the static chart; this finds the rare FUTURE
MOMENT no acharya could compute by hand. It serves **QT-7 (discovery/wonder)** and is what lets the LLM
VOLUNTEER opportune moments the client never thought to ask about (plan §5.11.1 #1).

## §1 — Why it matters / strategic role
- **It is the apex discovery product (plan §5.11.5).** It surfaces: off-daśā anomalous activations (Mode
  B); **cross-subsystem temporal convergence** (transit+daśā+nakshatra+yoga independently agree — the
  single deepest L3 insight, I-13); window-collision/interference; and the cost-of-omission ("won't recur
  for 19 years").
- **It is precomputable (plan §5.10).** Unlike a generic timing query, the native's OWN lifetime
  confluences are chart-bound + finite → a stored artifact (computed once, served instantly). This is the
  one place exhaustive precompute is correct.
- **It proves "same machine, run exhaustively" (plan §5.11.7).** It is NOT new machinery — it is
  `ka_sangam`'s Mode B swept across the whole lifetime and stored. The brief is mostly orchestration +
  ranking + the discovery-record schema, not new search logic.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The structural twin's record shape EXISTS** (`bo_anveshana.py` → `bodha_discoveries`): `discovery_id,
  chart_id, ayanamsha_id, build_id, discovery_class, discovery_subsystem, non_obviousness_score,
  consequence_score, composite_discovery_rank, constituent_refs_jsonb, reasoning_chain_jsonb,
  why_an_acharya_misses_it, hypothesis_text, falsifier_jsonb, calibration_hook, novelty_class`. **MIRROR
  this shape on the temporal axis** — it is the proven, B6-validated discovery-record schema. L2 produced
  1,411 discoveries + 4,359 anomalies (5,770) this way.
- **`bo_anveshana` ranks by `non_obviousness_score DESC`** with a latent-insight threshold (top-30
  candidates). REUSE this ranking discipline.
- **`ka_sangam` Mode B** (this brief's input) already FLAGS off-daśā discoveries (`is_off_dasha_discovery`).
  `ka_kala_darshana` collects, scores for non-obviousness, ranks, and stores them.

## §3 — The build (exhaustive Mode-B sweep + the discovery record)
**3.1 — Exhaustive lifetime sweep.** Run `ka_sangam` Mode B (the un-gated anomaly search) across EVERY L2
signal × the native's lifetime horizon (birth → plausible lifespan + margin, e.g. to ~2080 — confirm the
horizon, not 2150). Collect every high-magnitude confluence. The §5.9 spine keeps it bounded; the
ephemeris cache (I-9) is essential here (one exhaustive sweep, many repeated instants).

**3.2 — The temporal discovery record (mirror bo_anveshana).** For each confluence, store:
`temporal_discovery_class` (off_dasha_activation / cross_subsystem_convergence / window_collision /
rare_return / eclipse_hit / …), `discovery_subsystem`, `non_obviousness_score` (how invisible to
daśā-first human reasoning), `consequence_score` (how consequential the underlying pattern, from L2),
`composite_rank`, `constituent_refs_jsonb` (the L2 signal_id + the temporal factors), `reasoning_chain_jsonb`,
`why_an_acharya_misses_it`, `hypothesis_text` (the falsifiable datable prediction), `falsifier_jsonb`,
`calibration_hook` (→ L5), `novelty_class`, PLUS the temporal fields: `window_start/end/peak_date`,
`rarity_years`, `confidence_score/label`.

**3.3 — Cross-subsystem temporal convergence (the apex, I-13).** A FIRST-CLASS discovery_class: detect a
moment where MULTIPLE subsystems (transit + daśā + nakshatra-overlay + yoga) INDEPENDENTLY point at the
same window. CRUCIAL: use `ka_sangam`'s independence discount (I-22) so a daśā+nakshatra "agreement"
(coupled) is NOT counted as two — the non_obviousness/consequence must reflect TRUE independent
convergence, not an echo (plan §5.13.C1). This is the single deepest insight; weight it highest.

**3.4 — Window-collision / interference + cost-of-omission (plan §5.11.5).** Detect overlapping
confluence windows (constructive = amplifying; destructive = a benefic+malefic collision, joins
`ka_vighnakara`). Compute cost-of-omission: for each top confluence, the gap to its next recurrence
(`rarity_years` made actionable — "won't recur for N years").

**3.5 — Ranking + the catalog.** Rank by a composite (non_obviousness × consequence × rarity), store the
top-N as the standing catalog (per chart, per ayanamsha). Idempotent delete-then-insert (plan §N.3).
**Set `target_floor` = achieved count after build; never fabricate to a number (plan §N.4 floors-aspirational).**

## §4 — Asset registration (NEW, artifact-kind)
`ka_kala_darshana`: `asset_kind='artifact'`, `layer:'kala'`, sanskrit `'Kāla-darśana'`, english
`'Lifetime confluence catalog'`, `target_table:'kala_darshana'`, chart-scoped count_sql,
`depends_on: ['ka_sangam','ka_vighnakara']`. Per-chart, ×5 ayanamsha (matching L2's discipline).

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** the exhaustive sweep covers every L2 signal × the lifetime horizon; the catalog
   is non-empty for `482012f1` with `non_obviousness_score > 0` for all rows (mirrors the bo_anveshana B6 gate).
2. **[verify: pytest]** cross-subsystem convergence discoveries use the INDEPENDENCE DISCOUNT — a coupled
   daśā+nakshatra agreement does NOT inflate the convergence count (assert vs. two independent currents).
3. **[verify: pytest]** off-daśā discoveries from `ka_sangam` Mode B appear in the catalog, flagged, with
   `why_an_acharya_misses_it` populated.
4. **[verify: pytest]** window-collision detection finds a constructive + a destructive overlap;
   cost-of-omission = the gap to next recurrence for a top confluence.
5. **[verify: pytest]** each row has a falsifiable `hypothesis_text` + `falsifier_jsonb` + a
   `calibration_hook` (so L5 can later validate — the learning loop).
6. **[verify: anti-drift]** every discovery references a resolving L2 `signal_id` + temporal facts; no L2
   writes; constituent refs resolve.
7. **[verify: psql_prod + curl_prod]** `ka_kala_darshana` registered (artifact-kind); cockpit count;
   target_floor = achieved (not fabricated); idempotent rebuild; FORENSIC chart unaffected.
8. **[contract]** the writer never commits/rolls back `ctx.db_conn` (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-kala-darshana
# the structural twin to mirror
sed -n '54,80p;340,400p' platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py
# tests
cd platform/python-sidecar && pytest -q services/ka_kala_darshana -k "darshana or catalog or convergence or discovery"
```
> Branch/merge: Madhav human-gated PR (plan memory); Conductor stages, master plan gates.

## §7 — Definition of done
- [ ] Exhaustive lifetime Mode-B sweep over all signals; bounded via the spine + ephemeris cache.
- [ ] Temporal discovery record mirrors bo_anveshana + temporal fields.
- [ ] Cross-subsystem convergence (I-13) with the independence discount; window-collision; cost-of-omission.
- [ ] Falsifiable hypothesis + calibration_hook per row (learning-loop ready).
- [ ] Registered artifact-kind; target_floor = achieved; anti-drift clean; idempotent; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Gives the layer its "wonders of your timeline" product** — a standing, precomputed catalog of the
   rarest, most consequential lifetime windows means the instrument can VOLUNTEER the once-in-decades
   opening the client would never know to ask about — the §5.11.1 behavior that separates a supreme
   instrument from a query box.
2. **Realizes temporal discovery as L2's proven twin** — by mirroring the B6-validated `bo_anveshana`
   record schema (non_obviousness, why_an_acharya_misses_it, falsifier), it inherits a battle-tested
   discovery discipline rather than inventing one, and stays gradeable.
3. **Makes cross-subsystem convergence a first-class, HONEST insight** — the apex L3 insight, computed
   with the independence discount so it can never be an echo chamber; this is where "transit+daśā+
   nakshatra+yoga independently agree" becomes a real, defensible discovery.
4. **Turns rarity into agency (cost-of-omission)** — quantifying "this won't recur for 19 years" makes the
   catalog actionable, not just impressive; it tells the client what it COSTS to miss a window.
5. **Honors the precompute boundary exactly** — the native's own lifetime is the one finite, chart-bound
   thing worth exhaustive precompute, so the catalog is the legitimate stored discovery artifact while
   arbitrary timing stays a service (§5.10).
6. **Wires the learning loop at the discovery level** — every catalog entry is a falsifiable, calibratable
   datable prediction, so the rarest insights are exactly the ones L5 can later validate against lived reality.

---
*End of CLAUDECODE_BRIEF_L3_KA_KALA_DARSHANA v1.0. The wonders of the timeline — temporal discovery, L2's twin.*
