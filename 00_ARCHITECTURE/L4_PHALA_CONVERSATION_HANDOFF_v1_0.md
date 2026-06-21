---
artifact: L4_PHALA_CONVERSATION_HANDOFF_v1_0.md
canonical_id: L4_PHALA_CONVERSATION_HANDOFF
version: 1.0
status: HANDOFF — paste into the new Cowork conversation to open L4 Phala with full context
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
purpose: >
  Single self-contained context payload so a fresh conversation can open the L4 Phala
  campaign without re-reading the whole corpus. Grounds the new session in: the project
  mission, the L0→L3 arc, the current state, the L4 onboarding contract, the registered
  ph_* placeholder set, the inherited standards/traps, and the proven working method.
---

# L4 PHALA — NEW-CONVERSATION HANDOFF

> Paste this whole file as the opening context of the new conversation. It is the
> "everything you need to start L4 Phala" briefing. Authoritative sources are cited by
> path throughout — the new session should still do the §C mandatory reads, but this
> gives it the orientation to be productive from message one.

---

## 1 — What this project IS (mission, one paragraph)

**MARSYS-JIS** is an LLM-operated Jyotish (Vedic astrology) instrument for one native,
**Abhisek Mohanty** (born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India; canonical
`chart_id = 482012f1-710e-4a25-994a-93821f5871aa`). It reads the chart with acharya-grade
depth, surfaces patterns/contradictions no single astrologer could hold in working memory,
and makes **time-indexed, probabilistic, calibrated predictions** testable against lived
reality and correctable from outcomes — then generalizes the method into a research tool for
astrology as a discipline. Bounded by an Ethical Framework: probabilistic, calibrated,
auditable outputs, NOT a fortune-telling product. Governing file: **`CLAUDE.md`** (read it
first). Quality bar (§J): an independent senior acharya reviewing the corpus should say "this
is my own level / above it / reveals things I wouldn't have seen."

---

## 2 — The layer architecture + the arc so far (L0 → L3 all SEALED)

The instrument is built as a stack of layers. **External lexicon is LOCKED** — never show
"L0–L5" to a client; use the Sanskrit names. Asset-ids carry an underscore prefix per layer.

| Layer | Name | Means | Asset prefix | Status | What it holds |
|---|---|---|---|---|---|
| L0 | **Brahmagyan** | foundation | `bg_*` | ✓ SEALED | Ephemeris (825k rows), reference corpus, rules, ontology, nakshatra/medical/vastu/prashna reference. ~855k rows. |
| L1 | **Gaṇita** | computation | `ga_*` | ✓ SEALED | The chart itself: positions, divisionals, dashas (536k), strength, sensitive points, panchanga, structural facts. ~697k rows. FORENSIC 7/7 birth anchors pass. |
| L2 | **Bodha** | intelligence | `bo_*` | ✓ SEALED | Chart *interpretation* substrate: signal store (MSR), the chart graph (CGM nodes+edges), domain-linkage (CDLM), remediation (RM/upaya), embeddings, discovery engine. Deterministic relational ingredients the LLM synthesizes at query time. ~140k rows. |
| L3 | **Kāla** | time | `ka_*` | ✓ **SEALED 2026-06-21** | The "WHEN" layer — activates L2's structural promise across time. 12 assets: 7 stored artifacts + 5 live services. ~135k rows. (Just completed — see §4.) |
| **L4** | **Phala** | **fruit / result** | **`ph_*`** | **→ NEXT (this conversation)** | The **applied / prediction** layer: turns L3's windows into delivered predictions, auspicious-window picks, mitigation strategies, and birth-time rectification. |
| L5 | **Mīmāṃsā** | inquiry / evaluation | `mi_*` | pending | The learning/calibration layer — scores predictions against the life-event log, calibrates confidence, holds the falsification machinery. |

**The build is FROZEN-orchestrator-driven.** "Click Build" drives any chart's assets in
dependency order. A new layer onboards by writing `@register('<asset_id>')` `WriterBase`
subclasses that conform to the frozen contract — **never by changing the orchestrator.**

---

## 3 — The two non-negotiable disciplines (why the layers are separate)

- **B.1 Facts/Interpretation separation.** L1 = facts. L2 = interpretation. L3 = time. L4 =
  applied prediction. Never collapse a layer into another.
- **Anti-drift / L1-is-authority (the recurring trap).** A higher layer NEVER restates a
  lower layer's computed value as its own truth — it **references the lower `fact_id` /
  `signal_id`** and inherits the value. If a derivation disagrees with the fact it cites,
  that's a halt-worthy bug, not a stored divergence. **L4 reads `ka_*`, `bo_*`, `ga_*`,
  `chart_facts` (all read-only) and writes only `phala_*` tables.** It must never write to
  or restate `kala_*` / `bodha_*` values.
- **B.10 No fabricated computation.** If a number isn't already computed in a lower layer and
  needs a specialist tool, mark `[EXTERNAL_COMPUTATION_REQUIRED]` — never invent chart values.
- **B.11 Whole-Chart-Read.** Every query routes through L2 synthesis first, then the
  domain-specific answer.

---

## 4 — L3 Kāla: what was just built (the layer L4 sits on)

L3 sealed 2026-06-21. The seal doc is **`00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md`** (read §9–§12).
The full design lives in **`L3_KALA_CAMPAIGN_PLAN_v0_10.md`**, the rigor params in
**`L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md`**.

**The 12 L3 assets L4 can consume (read-only):**

*Stored artifacts (7):*
- `ka_kalasutra` — bounded **activation artifact**; fills L2's reserved NULL hooks; 66,738 rows.
- `ka_sangam` — **convergence engine** output (the 3-plane structural×daśā×transit confluence,
  scored by the I-16 formula); 660 windows. **This is the heart L4 prediction consumes.**
- `ka_vighnakara` — **danger / obstruction** windows (7 obstruction types, severity-scored); 60.
- `ka_kala_darshana` — display-ready lifetime confluence catalog; 300.
- `ka_jivana_parva` — daśā macro-narrative / life-arc chapters; 739.
- `ka_bhavishya_lekha` — **prediction-record emitter** (probabilistic projections + falsifiability
  fields) — explicitly the L3→L5 learning hook; 50.
- `ka_yojaka` — activation bridge (signature_class classifier + template binder); 66,738.

*Live services (5; no stored rows, health-probed):*
- `ka_graha_sancara` — ephemeris service. `ka_dasha_kala` — daśā-eligibility service.
- `ka_gochara` — transit-search service (the from-scratch `transit_search.py` engine; **subsumed
  the old transit-almanac**). `ka_muhurta_seva` — panchāṅga/muhūrta service (live by date+location).
- `ka_tulana` — cross-pattern prioritization (ranks across windows/domains).

**Ratified params frozen and INHERITED by L4 (do not re-pick; L3_KALA_CLOSE §9):**
I-16 convergence formula `score = Π(necessary) × (1 − Π(1 − w_i·s_i))`; I-17 orb curve
`cos²((orb/max_orb)·π/2)` × (1.0 applying / 0.7 separating); I-7 supporting weights
(constituent_lord_transit 0.30, benefic_dṛṣṭi 0.20, cross_daśā 0.18, panchāṅga 0.12,
tāra_bala 0.12, nakṣatra 0.08); I-8 Mode-B threshold 0.6; confidence labels high ≥ 0.75 /
moderate ≥ 0.45 / speculative < 0.45; Mode A (daśā soft funnel) + Mode B (off-daśā anomaly sweep).

---

## 5 — L4 Phala: the onboarding contract (from L3_KALA_CLOSE §11)

The next layer is **L4 Phala** (`ph_*`). It inherits ALL L3/L2/L1 standards plus:

1. **Reads (read-only):** all `kala_*`, all `bodha_*`, `chart_facts`. **Writes:** only `phala_*`.
2. **Frozen orchestrator contract** — `@register('ph_*')` `WriterBase` subclass; `run(ctx)` (light)
   or `plan_substeps`+`run_substep` (heavy); runs on `ctx.db_conn` and **NEVER commits/rolls back/closes
   it**; never writes `asset_throughput` (orchestrator is the sole build-state writer); gets `chart_id`
   + `birth_params` from `ctx.config`. If a writer seems to need a contract change → STOP, raise with native.
3. **Idempotency:** per-chart **delete-then-insert** scoped to `(chart_id × natural key)` (mirror
   `ga_writers/_idempotency.py`). Rebuild REPLACES, never accretes.
4. **Asset IDs:** `ph_*` prefix only. No `phala.*` dot-notation.
5. **Migration numbers:** **L4 starts at 251+** (L3 used 242–250).
6. **First L4 migration SHOULD drop `kala_timeline`** — it is DEPRECATED (CF.L3.2; noted in mig 246
   COMMENT). Do NOT write to `kala_timeline`; if timeline data is needed, read `kala_activation`
   or `kala_convergence`.
7. **Cockpit truth:** each asset needs a correct chart-scoped `count_sql` using **`$1`** binding (NOT a
   `$$CHART_ID$$` literal — that exact bug cost an L3 remediation round). Stats route reads `count_sql`.
8. **No audience tier. Floors aspirational not gates. Deterministic-first.** (See §7 traps.)

---

## 6 — The 5 registered Phala placeholders (already in `asset_registry_seed.ts`, all `is_active:true`)

These are seeded but UNBUILT (no writers, empty tables). They embody the intended L4 product set —
the new campaign should AUDIT them first (the L3 method: don't trust the seed as gospel; verify
against the boundary decision that L4 = applied products consuming L3, while prediction-RECORDS +
calibration live in L5).

| asset_id | Sanskrit | English | target_table | depends_on | Intent |
|---|---|---|---|---|---|
| `ph_nimitta` | Nimitta | Predictive anchors | `phala_anchors` | `ka_sangam` | Phase-locked predictive anchors derived from convergence windows |
| `ph_muhurta` | Muhūrta | Auspicious windows | `phala_muhurta` | `ka_kalasutra`, `ga_panchanga` | Candidate muhūrta windows scored by panchāṅga + transit + daśā alignment |
| `ph_sodhana` | Śodhana | Rectification | `phala_rectification` | `bo_laksana` | Birth-time rectification hypotheses scored against life events |
| `ph_pratikara` | Pratīkāra | Mitigation | `phala_mitigation` | `bo_upaya`, `ka_vighnakara` | Active mitigation strategies for flagged malefic configurations (window→intervention loop) |
| `ph_suddha_sodhana` | Śuddha-śodhana | Best rectification | `phala_rectification_best` | `ph_sodhana` | Top-scored rectification hypothesis per search run |

> Note the dependency graph already wired in the registry: `ph_nimitta ← ka_sangam`;
> `ph_muhurta ← ka_kalasutra + ga_panchanga`; `ph_pratikara ← bo_upaya + ka_vighnakara`;
> `ph_suddha_sodhana ← ph_sodhana`. The L4 campaign should confirm/extend this set — e.g. whether
> the **window→intervention→timing loop** (Pratīkāra) and the **rectification** sub-chain are the
> right scope, and whether anything is missing (the L3 lesson: do a holistic opening pass before
> settling the asset set).

**Boundary reminder (decided during L3):** L4 Phala = APPLIED products (muhūrta picks, mitigation,
rectification) consuming L3. The **prediction-record + calibration + falsification** machinery is
L5 Mīmāṃsā (`mi_bhavisya`, `mi_pramana`) — `ka_bhavishya_lekha` already hands prediction-records UP.
So L4 should not re-own calibration; it owns the *applied* fruit.

---

## 7 — Inherited standards + the hard-won traps (do not re-learn these)

- **Cowork vs Antigravity split.** This conversation (Cowork) does **planning / design / authoring
  briefs ONLY**. All implementation goes to Claude Code in the Google Antigravity IDE. Every output
  is a pasteable prompt or a committed `.md` brief — never chat bullets the native must translate.
- **Anthropic/Claude API is BANNED for the instrument's own LLM calls** (cost) — default Gemini,
  fallback DeepSeek. Flag any brief that hardcodes Anthropic.
- **The live cockpit, not the status report, is the seal signal.** This was validated ~4× in L3 — a
  swarm reported "SEALED" while prod was empty; the API showed green while the *visual* cockpit showed
  red dots because a fix sat on an unmerged branch. **A correct fix on an unmerged branch is invisible
  to prod.** Always confirm the Cloud Run revision == merge SHA before calling anything done; verify
  the visual surface, not just the JSON. Bake **live-cockpit + visual verification in as a HARD seal
  gate from the very start of L4.**
- **Floors are aspirational, not gates** — set `target_floor` = achieved count after build; never
  fabricate rows to hit a number; never halt a build for being under floor.
- **No audience tier** — writers emit all rows; serve-time governs access. Strip any tier branch on sight.
- **Deterministic-first** — Python over LLM for computation; embeddings (deterministic transforms) OK;
  generative LLM for curation is NOT.
- **Surgical migrations only** — never deploy.yml-auto or bulk migrate; never rewrite an applied migration.
- **`$1` not `$$CHART_ID$$`** in every `count_sql`.
- **localhost = code-plane only; data-plane is always prod** (Cloud SQL Auth Proxy). Writes from
  localhost ARE prod writes.

---

## 8 — Current state (you-are-here, 2026-06-21)

- **`CURRENT_STATE_v1_0.md` is at v5.89** ("supersedes v5.88 premature seal; L3 genuinely built +
  cockpit-verified"). Read its §2 state block + `git log` at session open — do NOT read "you are
  here" from CLAUDE.md §F (it's intentionally stale).
- **Whole arc: L0 ✓ · L1 ✓ · L2 ✓ · L3 ✓ → L4 Phala is genuinely next.**
- **In-flight cleanup (not a blocker for L4 planning):** a small cockpit-cosmetics stream is finishing
  on branch `fix/l3-cockpit-ui-service-pill-and-floor` (PR #321 already merged service_ok-green +
  aria-label + RETIRED-state fixes). The native also decided to **hard-remove the subsumed
  `ka_transit_almanac`** tombstone (orphan, zero dependents) so the Kāla panel reads 12 assets — a
  consolidated prompt for that is authored. None of this gates L4; it's Kāla polish.
- **Independent open items:** CF.L3.1 (Phase E non-native E2E on Abhinandan `1c826d5a`) is
  operator-gated and independent. CF.L3.8 (L3 build-state was stamped via one-shot reconcile, not the
  orchestrator) is a process note — **future L3 rebuilds must go through the orchestrator click-Build
  path**; L4 builds should use the orchestrator from the start.

- **⚠️ MUST-FIX BEFORE L4 MIGRATIONS (CI silent-skip).** Discovered 2026-06-21 during the
  ka_transit_almanac removal: **CI is NOT applying migrations to prod** — the `PROD_DATABASE_URL`
  secret is unset in CI, so migrations "pass" in CI while applying NOTHING to the prod database
  (migrations 328+329 silently no-op'd; the DELETE had to be hand-applied via psql). This is the
  deploy.yml-auto / silent-noop trap class. **L4 starts at migration 251+ — every one of them will
  silently skip in CI until this is fixed.** The L4 campaign should fix CI migration application (set
  `PROD_DATABASE_URL` in CI, or establish the surgical-psql-apply protocol as the documented norm)
  BEFORE building any `ph_*` asset, and treat "migration applied to prod" as a verify-via-psql gate,
  never "CI green." Related secondary findings: the `asset_registry.catalog_status` CHECK constraint
  was expanded to allow `RETIRED` (was CURRENT/DRAFT only); deleting an asset_registry row requires
  deleting its `asset_throughput` row first (FK). Also fixed in the same pass: `StatusDot` treated
  `catalog_status='DRAFT'` as unconditionally red, overriding healthy runtime state — corrected to
  `(isDraft && !isHealthy)` so DRAFT only shows red when the asset isn't actually built.

---

## 9 — Mandatory session-open reads for the new conversation (CLAUDE.md §C order)

The new session should open by reading, in order: `CLAUDE.md` → `CAPABILITY_MANIFEST.json` →
`PROJECT_ARCHITECTURE_v2_2.md` → `MACRO_PLAN_v2_0.md` → `CURRENT_STATE_v1_0.md §2` →
`GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` → the session templates → `L3_KALA_CLOSE_v1_0.md` (the layer
it inherits) → this handoff. It emits a SESSION_OPEN handshake (per `SESSION_OPEN_TEMPLATE_v1_0.md`)
with `may_touch`/`must_not_touch` globs and a proposed Cowork thread name before substantive work.

---

## 10 — The proven method to run L4 (the L3 playbook, which worked)

Use the same arc that produced L3 cleanly (native-ratified approach):

1. **Audit-first** — verify the 5 `ph_*` placeholders against reality (tables exist? writers exist?
   what does each truly need?); don't trust the seed or any handoff claim ("engines exist, just wire"
   was FALSE in L3 — the heart was unbuilt). Code-verify.
2. **Holistic opening pass** — before settling assets, ask what the *applied prediction* layer must
   deliver for the native (the QT-style consumer question-space): delivered predictions, auspicious-window
   selection, mitigation/intervention loop, rectification. Elevate to "supremely valuable product."
3. **Settle the asset set** — confirm/extend the 5 placeholders; resolve naming + any subsume; lock the DAG.
4. **Per-asset maximal-value briefs** — one `.md` brief per asset (swarm-coordination header: wave /
   blocked_by / blocks / may_touch; prod-tagged acceptance criteria; a VALUE-ADDED section). Document
   in DETAIL from the start so nuances are retained (native directive).
5. **Holistic closing review** — step back, find gaps, missed cross-links.
6. **Retrieval tools** — how the instrument serves L4 outputs.
7. **Author the master autonomous execution plan + Conductor session_queue + KICKOFF** — then native
   launches the agentic swarm in Antigravity.
8. **Clean seal** — with the live-cockpit + visual verification baked in as a HARD gate (the #1 L3 lesson).

> Documentation-first discipline + "improvisation = creative latitude in shaping the layer, NOT
> loosening determinism gates." Persistence lesson: after any `git mv`, use Write+readback (file-tool
> edits can desync from disk).

---

## 11 — Memory pointer

The running L3 audit/decision log is the memory file **`project_l3_kala_engine_audit.md`** (in the
Cowork memory dir) — it holds the full L3 decision trail, the traps, and the cockpit-verification
lessons. The new L4 conversation should start its own `project_l4_phala_*` memory thread and link back
to it. Durable preferences (Cowork/Antigravity split, Anthropic-banned, deterministic-first, floors-
aspirational, no-audience-tier, verify-state-from-CURRENT_STATE) are already in the memory index.

---

*End of L4_PHALA_CONVERSATION_HANDOFF v1.0. Paste this whole file to open the L4 Phala campaign with
full arc context. The fruit of the tree — where the chart's structural promise, activated across time,
becomes delivered prediction and actionable intervention for the native.*
