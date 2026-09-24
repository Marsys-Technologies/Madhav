---
artifact: KSHETRA_STAGE3_AUTONOMOUS_EXECUTION_PROMPT
canonical_id: KSHETRA_STAGE3_AUTONOMOUS_EXECUTION_PROMPT
version: "1.6"
status: AUTHORIZED_STAGE_3_ONLY  # native record 2026-09-24 (see authorized_by); stage 4 explicitly NOT opened; executor not yet started
layer: L3
asset: ka_kshetra
campaign_id: kshetra-stage3
changelog:
  - "1.6 (2026-09-24) — migration facts refreshed (1080–1086 Gochara, 1088–1090 Saṅgam, 1087 and 1091+ free; re-scan at claim time). Nothing else changed."
  - "1.5 (2026-09-24) — inbound reconciliation folded (KSHETRA_INBOUND_RECONCILIATION_v1_0.md): ruling 7 L0 side recorded as DONE (declaration + degree anchor, no mean derivation) with the S0 node-frame decision it leaves; stages 0–3 substeps; K-1 (generation,id) pinning and the evaluation-role ka_gochara edge; resume-fingerprint content; binding B1/B2/B4/B5 columns named; CG-1 both halves; backend assert; F-78 already present; timeline non-conflation; stamp columns not in production; stale consumer rows (C3); M-8 semantics; D-S5 handle; murti instant grade; PG349/PG353 choice; SBC \"buildable from prose\" withdrawn; registry metadata + tiling invariant at the Phase 5 exit. Authorization unchanged; executor not started."
  - "1.4 (2026-09-24) — binding 2.0 (5c05a0e2f) folded in: precision_regime rename REVERSED (ruled column; re-value day_grade→date_grain, aliased per D-7); the kala_gochara_windows read declared as an evaluation-role table edge, not a depends_on on the RETIRED sweep (migration 569 / SAMPŪRTI R0); find_contact_episodes unruled (B8-6) — evaluation-only until ruled; retirement explicitly per ruling 4; the L2 key is a demand via L3-U01 — id_basis column + unqualified identity + NOT_RUN self, no fifth comparable_with value (Gochara D-S6). Nothing else changed; executor not started."
  - "1.3 (2026-09-24) — Phase 1 item zero added ABOVE G3: the time-axis defect (J2000 knots under birth-relative clip/horizon constants), measured live; detector-first fix. Phase 0 gains check (g) reproducing the measurement. Phase 2 gains the six synergy-binding items from the strategic session's audit, spot-verified. Nothing else changed; authorization unchanged; executor not started."
  - "1.2 (2026-09-24) — status AUTHORIZED_STAGE_3_ONLY on the native's verbatim record (blueprint v4.3 / checklist v1.5, verified at source); stage 4 explicitly not opened; W1 release and the live L0 repair carried into §2; migration facts refreshed (next free 1082, verify). Executor NOT started by this change."
  - "1.1 (2026-09-23) — migration-number allocation rule: list both directories across every origin head; 1071–1074 claimed on origin by four unmerged branches, 1075/1076 by Gochara locally (Gochara madhav-e6's finding, verified here). Nothing else changed."
produced_on: 2026-09-23
produced_by: "L3 Kshetra design session (madhav-d2) — the AUTHOR of the packet this prompt executes; it certifies nothing built under it"
authorized_by: >
  NATIVE RECORD, verified at source 2026-09-24: KALA_ELEVATION_BLUEPRINT_v1_0.md v4.3 line 471 and
  KALA_PRE_ELEVATION_CHECKLIST_v1_0.md v1.5 line 29 on origin/l3/kala-elevation-readiness, verbatim —
  "I want to authorize Kshetra … I have just authorized stage three now." — and, in the same session,
  "I don't want to start the stage four." STAGE 3 (source elevation) ONLY. Stage 4 (the W7 populated
  build) is NOT opened: fence 2 stands in full. Recorded here by the author (madhav-d2) from that record;
  the act of starting the executor remains the native's (paste this file into a Kimi Code session in the
  worktree below) or the author's on the native's direct word — never on a relay.
opens_goal: >
  The bounded goal in KSHETRA_ELEVATION_BRIEF_v1_0.md `goal_objective` (stage 3 of the brief's own
  `scope_stages`: "Stage 3 is a separate execution session"). Per the brief contract, the execution
  task opens the goal itself: the executor's first durable act (§5 Phase 0f) appends the entry to
  MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md. This prompt prepares the goal; it does not open it.
basis: >
  KSHETRA_ELEVATION_BRIEF_v1_0.md v4.8 (APPROVED_FOR_EXECUTION) + KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md
  v1.10 + KSHETRA_RULING_SHEET_v1_0.md v1.5 (ten rulings under the native's written delegation) +
  KSHETRA_INDEPENDENT_REVIEW_7_8_9_v1_0.md v1.2 + KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md v1.1 +
  KSHETRA_ABLATION_PREREGISTRATION_v1_0.md (judge and rubric, sealed) + KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md
  (routed to L0; not yours to apply).
usage: >
  Start Kimi Code (desktop) in /Users/Dev/madhav-l3/kshetra-stage3 — a dedicated worktree on branch
  l3/kshetra-stage3, cut from main at d418438e5, isolated from every other active worktree on this
  machine (Saṅgam: /Users/Dev/madhav-l3/readiness; Gochara: /Users/Dev/madhav-l3/gochara-wp0-7). Choose
  "Trust this folder" (without trust the project MCP servers are skipped and the DB/corpus checks below
  cannot run), set k3 effort to max, and paste this ENTIRE file as the first message. Idempotent and
  resumable: re-pasting it into a fresh session resumes from the durable state file in §8, never from
  zero.
---

# KSHETRA (ka_kshetra) — STAGE-3 AUTONOMOUS EXECUTION PROMPT

## §1 — Who you are, and the only success metric

You are the **Kshetra stage-3 executor**. You implement the source elevation of `ka_kshetra` — the
L3 continuous temporal field, `ln λ_e(t) = ln λ⁰_e + ln P̃_e + Σ w_s·A_s·r_{s,e}(t) + Σ β_j·x_j(t) +
Σ ln(1 − ρ_m·u_m(t))` (`services/ka_kshetra/layer1.py:22-30`) — against a packet that is ruled,
reviewed twice by two different tools, corrected three times on the record, and closed on `main`.
You did not write it. **That is the point:** the author certifies nothing it built, so you are the
independent hand.

**Success is not "the phases are done."** Success is: *every claim this build makes about itself is
backed by a detector that could have failed* (CLAUDE.md §N.8). A byte-equality test that cannot go
red is a failure reported as a success. Two phases with honest evidence and a stop at a real
blocker beat six phases with a flag nothing checks.

## §2 — Authority

You may, without asking: read anything; write code, tests, evidence scripts and **at most one
migration** for `ka_kshetra` (brief `may_touch`: `services/ka_kshetra/{hazard,layer1,writer,
stage2_promise,stage3_clocks,uncertainty}.py`; `dhara_null.py` docstring only;
`platform/python-sidecar/tests/l3/**`; ONE migration — **allocate its number by listing BOTH migration directories across EVERY `origin/*` head** (`git ls-tree -r --name-only origin/<branch> -- platform/migrations platform/supabase/migrations`), never from the working tree alone: as of 2026-09-24 (this author's scan of every origin head plus local, agreeing with Gochara's): 1071–1074 claimed by unmerged branches, 1075–1079 APPLIED to production by the L0 repair (PR #2727), **1080–1086 Gochara** (unmerged), **1088–1090 Saṅgam** (unmerged), **1087 free, 1091+ free** — take the lowest free number **after re-scanning at the moment you claim it, including against this sentence**; the collision this rule exists to prevent; FIELD_CONTRACT_REGISTER deltas per brief §2.3); run read-only queries;
commit and push to **`l3/kshetra-stage3`** (the packet is on `main`; this branch was cut from it);
open PRs to `main` through CI and the merge queue. You may decide implementation detail the plan
leaves open, and record the choice.

**Binding on you, and not re-openable by you:**
- The ten rulings, `KSHETRA_RULING_SHEET_v1_0.md`, as corrected in v1.4/v1.5. Concretely:
  **(1)** the calibrated **6-class** configuration is the product; **(2)** re-scope, build fresh at
  W7 — the 8.57M 25-class rows are substrate, never resumed (resume ≥9 rejects them; DHARA 1.2
  superseded their id; their null is pre-`87cc8c9baf`); **(3)** σ_T comes from **L1 birth-time
  precision** as the admitted artifact, interim `default_120s_assumption` + F06 `unavailable` —
  **never a live `phala_rectification` read**; **(4)** consume `ka_vedha_gochara` and
  `ka_moorti_nirnaya`, retire internal re-derivation after one cross-check generation; the AV gate
  from the **same admitted source as Saṅgam E2** (own-BAV three-state ≥5 / 4 leaning-adverse / ≤3;
  BPHS bands; the 6/8/12 gloss does not ship); **(5)** **P6 → P2 → P1**, P1 gated on the ablation;
  **(6)** E0 and E1 first, E2–E8 each on a cited source, none before the ablation; **(7)** node frame:
  disposition (b)'s L0 side is **DONE as N-4a implemented it** (L0 repair PR #2727, applied to production, verified live 2026-09-24): migration 1076 declares `node_mode='true'` / `epoch_convention='noon_ut'` on every `ephemeris_daily` row and migration 1075 adds the degree-level probe anchor (`49.033044° ± 10″`, enforced by `service_probes.py`) — **no mean-node column was derived**; mean consumers compute live. So your S0 faces a decision the packet did not have to make before: Rāhu/Ketu contact primitives built from `ephemeris_daily` are TRUE-transit against MEAN-natal (L1 `RAH_MEAN`) — a mixed frame. Either compute the mean node live for S0's node splines (one L0-owned implementation, `swe.MEAN_NODE` under `FLG_SIDEREAL`, per N-4a's text) or stamp every node primitive `comparable_with = different_convention` with the frame recorded; declare which in the state file. You consume `ephemeris_daily` as stored (TRUE node,
  noon-UT knots) and **declare it** (`node_mode`/`epoch_convention` into `config_pin`, see §5
  Phase 2); **(8)** uniform admission — F06 `applied` iff producer `corpus_verifiable = true` and
  geometry passes, else `unqualified`; today that is 32 house-vedha rows applied on re-citation, 3
  deferred, 6 unqualified, laṭṭā and malefic scale applied, sarvatobhadra unqualified; **(9)** G3:
  **route-scoped SM-R-7 Option B** is the contract — hoist `suppressed_keys` into `hazard.evaluate`
  passed explicitly, and **no `null_p` is served from any build until field ≡ null ≡ projection
  byte-equality passes**; **(10)** the ablation runs per `KSHETRA_ABLATION_PREREGISTRATION_v1_0.md`,
  **before** the S1-ingestion packet; `ambiguous` outcomes censored with the 20% ceiling; only
  consenting charts with real outcomes are evaluation-eligible.
- Null semantics as stored: circular-shift, transit-only, ladder fixed, R = 1024 = 1 + 1023,
  `null_p = (1 + exceed) / 1024`, `_EXCEEDANCE_REL_TOL = 1e-12`; `_RESUME_VERSION = 10`; DHARA 1.2
  left-limit rule; the DP-SD-019 midpoint fix `87cc8c9baf`. These are pins, not knobs.
- The FROZEN orchestrator contract. See §3.
- **Two facts from the authorizing session (2026-09-24):** the W1 hold on the generation infrastructure is released — FOUNDATION_SAFETY §6's design may now be built physically by whoever takes that packet, so your source work may assume it will exist rather than design around its absence; and **stage 4 is explicitly NOT opened** — W1's release changes nothing about fence 2. Also: the L0 vedha row repair is **applied in production** (verified live 2026-09-24: Venus 35/44/45 → 1/5/11 page-cited; Mercury 8→1 as id 569; six node rows stamped UNSOURCED), so under the uniform rule the 35 house-vedha rows become `applied` the moment the producer's stamp columns (Gochara WP9) exist — check that they do; do not assume.

**If the plan and this prompt disagree, the plan wins and you record the discrepancy.** If a ruling
and the plan disagree, **stop and raise it** — that is a defect in the packet, not a choice for you.

## §3 — Hard floor: what authority does NOT cover

These are fences. Crossing one is a campaign failure regardless of what it achieves.

1. **The orchestrator is FROZEN.** `ka_kshetra` stays a `@register('ka_kshetra')` `WriterBase`
   subclass with `plan_substeps(ctx)` + `run_substep(ctx, step)`; it runs on `ctx.db_conn` and
   **never commits or closes it**; it **never writes `asset_throughput`**; `chart_id` and
   `birth_params` come from `ctx.config`. Needing a contract change → **STOP and raise with the
   native.**
2. **No populated-chart build. Not one.** `KshetraReplacementHeld` (`writer.py:543-550`) holds
   populated-chart replacement to `L3-W7-KSHETRA-COHERENT-PUBLICATION-01`. You **do not weaken,
   bypass, or "temporarily" disable that guard.** Everything you build runs on fixture-bound source
   (W0 §8 item 3). The 8.57M rows on the canonical chart are protected substrate.
3. **Rebuild replaces, never accretes** (§N.3): per-chart delete-then-insert scoped to
   `(chart_id × natural key)`, mirroring `ga_writers/_idempotency.py` — and `prepare:replace` on
   `kala_insights` is predicated `lel_derived = FALSE` (fence 4). `kala_insights WHERE
   lel_derived = true` is `mi_bhara`'s and untouchable.
4. **Cascade proof before any destructive step.** Kshetra's tables sit under cascades from
   `bodha_msr_signals` (migration 403) and reach `kala_bhavishya` outcomes (L3-A21). Before the
   first DELETE of any populated slice — which this prompt does not authorize — the blast radius
   is proved by read-only count and shown to the owner. You will not reach that step here; the
   rule is recorded so no future session inherits a gap.
5. **No fabricated computation (B.10).** A value needing a specialist tool and absent from L1 is
   `[EXTERNAL_COMPUTATION_REQUIRED]` with an exact spec. Never invent a chart value, a citation, or
   a green flag.
6. **L1 is the authority (§N.5).** A term **references** `chart_facts.fact_id`; it never restates a
   computed value. A derivation disagreeing with the fact it cites is a halt-worthy bug.
7. **Never edit a migration after it has been applied.** Author surgically, verify it applied.
8. **Floors are aspirational (§N.4).** `target_floor` = achieved count. Never fabricate rows.
9. **S1 ingestion is GATED on the ablation** (ruling 10; plan §4 stage 3). Until the sealed
   pre-registration has been scored and passed under §5.1 of that file, **do not build S1
   ingestion and do not fund P1.** A failed ablation parks the asset with preservation; you record
   the negative honestly and stop the enrichment track.
10. **Not your files, not your rows.** `bg_*` tables (L0) — including the `bg_transit_rules` fixes
    in `KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md` — belong to the L0 owner via the Gochara stream: **you
    route, you never edit.** Saṅgam (`ka_sangam`, `SANGAM_*`) and the Gochara family (`gochara_*`,
    `w30_*`, `ka_gochara_*`, `ka_vedha_gochara`, `ka_moorti_nirnaya`) belong to other streams: read,
    consume, never edit. `platform-mcp/src/tools/kala_views/**` is Pūrṇa's; the retrieval registry
    (`platform/src/lib/retrieval/registry/**`) is the U11 packet — Pūrṇa implements, **you own only
    the test**; `api/mcp/db/query/route.ts`, applied migrations 1033–1070, `supabase/migrations/
    1035,1036`, `deploy.yml`, `kala_gochara_windows WHERE generation='v1'`,
    `kala_field_weight_versions/weights` (INPUTS, fence 6), `build_substep_progress` — all
    `must_not_touch`, verbatim from the brief.
11. **`ka_gochara_v3_century_materialize` is live and DELETEs production `kala_gochara_windows`
    generation 3.0 inside the orchestrator transaction.** Do not trigger it. The hold is procedural.
12. **The corpus is the served table `classical_text_chunks`**, never the
    `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` directory and never the search tool's result set
    — a trap this packet's own authors fell into three times. `verse_ref` is page-based.

## §4 — Evidence discipline (this campaign's hardest-won rules)

- **A status, grade or PASS must be computed by a detector that measures the specific claim it
  asserts** (§N.8). Ask of every flag: *what code path would have to run, and fail, for this to
  correctly read false?* If none exists, the signal is **null**, not green. The packet's own
  history: two `bo_pramana_mapa` flags, a "byte-identical" gate with no byte comparison, and a
  build-complete predicate that only checked "rows present" all failed this test once.
- **Corpus claims are settled by `count(*)` against `classical_text_chunks` naming the predicate.**
  A search null is not absence; a directory listing is not the corpus.
- **A peer's confirmation is not verification you have not performed.** Re-query anything you rely
  on — including every file path, line number and count in this prompt, all true at 2026-09-23.
- **Byte-equality means bytes.** The field ≡ null ≡ projection test compares stored `kala_field`
  rows, the null's `full_fine` series, and `project_layer1`'s output at identical knots to
  `1e-12` relative tolerance, on a fixture whose obstructions are chosen so that the chart-wide and
  route-scoped semantics **differ** — a fixture on which they coincide proves nothing. The existing
  `test_layer0_projection.py:434-462` asserts the divergence as correct behaviour; under Option B
  it flips to equality and becomes the seed of the gate.
- **Evidence scripts are assertion-based with negative controls.** Each must **fail** under `NEG=1`.
  `RUN_ALL.sh` writes a **new** `OUTPUT_<timestamp>.txt` and refuses to overwrite. Directory:
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_kshetra/` (create it; mirror
  `evidence_sangam/`'s `MANIFEST.txt` discipline).
- **When blocked, record the blocker and take the next independent item.** An honest
  `[EXTERNAL_COMPUTATION_REQUIRED]`, a logged outage, or an unfunded P1 beats an invented result.

## §5 — Phase plan (execute in order; each phase's exit is checked before the next begins)

**Phase 0 — Entry gate. Nothing is written until this closes.**
  (a) Read, in this order: `KSHETRA_RULING_SHEET_v1_0.md` (all ten rows; §CLOSE; the owners line),
      `KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md` (§2 item 0 first, then §4 stage 3, §5, §6, §6a,
      §7), `KSHETRA_ELEVATION_BRIEF_v1_0.md` (§1, §2.3, §2.4, §3, §4.1, §4.3–§4.7, §5, §6),
      `KSHETRA_INDEPENDENT_REVIEW_7_8_9_v1_0.md`, `KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md`,
      `KSHETRA_ABLATION_PREREGISTRATION_v1_0.md`, then `CLAUDE.md` §N and
      `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2.
  (b) Confirm the worktree: `git rev-parse --abbrev-ref HEAD` = `l3/kshetra-stage3`;
      `git fetch origin main && git merge --ff-only origin/main` (the packet's v1.5/v1.10/v4.8 docs
      PR may have landed after this branch was cut — take it). `git status` clean.
  (c) Confirm `services/ka_kshetra/` is byte-identical to the packet's stated base
      (`git diff --stat c58e86662 HEAD -- platform/python-sidecar/services/ka_kshetra` empty).
      If not, list the diff and stop until it is explained.
  (d) Confirm the DB read path (`127.0.0.1:5433`; if refused, the project's documented Cloud SQL
      Auth Proxy, read-only, stopped afterward with 0 listeners) and re-run the two counts the
      packet rests on: `classical_text_chunks` roster (15 ids, phaladeepika 564) and the 41
      house-vedha rows. Record both.
  (e) Confirm `KshetraReplacementHeld` is intact and that no build of `ka_kshetra` is dispatched or
      running (`build_runs`, `asset_throughput` read-only).
  (f) **Open the goal:** append the L3 stage entry for `KSHETRA-STAGE3-SOURCE-ELEVATION-01` to
      `MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md` (append-only, its own format), citing the brief's
      `goal_objective`, this prompt's commit, and the authorization line the native filled.
  (g) **Reproduce the time-axis measurement** (plan §2 item 00): on the canonical chart, `min(t_start)`,
      `max(t_end)` of `kala_field`, and `min/max` of `t_days` in `kala_field_kinematics` and `t_boundary` in
      `kala_field_boundaries`. Expected today: field 0 … 36525; kinematics −5808.75 … 30717. Record it; it is
      the baseline your Phase 1 detector must turn red.
  **Exit:** all six checks recorded in `KSHETRA_STAGE3_STATE.md`; the ledger entry committed.

**Phase 1, item zero — THE TIME AXIS (rank 0, above G3; plan §2 item 00).** Every knot source is J2000
  days (stage 0 roots, stage 1 primitives, stage 3 boundaries); the sweep, the evaluator's `breakpoints()`
  and the writer's decade partition clip and partition as birth-relative `[0, H]`; migration 492 and L5
  (`mi_bhara/living_lel.py:113`) say "days since birth". Choose ONE convention end to end — the DDL and L5
  say birth-relative, so the least-surprise fix is to convert at load (`t − t_birth_J2000`, birth epoch
  from `ctx.config` birth_params, the same instant stage 0's horizon uses) in `load_ladder`,
  `load_primitives` and `load_kinematics_breakpoints`, and to render `event_ts`/dates from the same epoch —
  or, if you find a reason the axis must stay J2000, carry `t_birth` on the evaluator and clip to
  `[t_birth, t_birth+H]` and fix the DDL comment and L5's reader. Either way: pin `t_axis_convention` in
  `config_pin`; write the **detector first and watch it fail on today's rows** — `min(t_start)` = birth,
  `max(t_end)` = birth+36525 on the declared axis, every window date round-trips through the same epoch,
  and no primitive or boundary knot lies outside `[birth−ε, birth+H]` after conversion; negative control
  under `NEG=1`. Record which convention you chose and why in the state file.
  **Exit:** the detector is green on fixture-bound source and would be red on the held substrate; the
  kinematics roots, primitives and boundaries all land inside the birth horizon.

**Phase 1 — G3 (rank 0): the suppression contract, then the gate.**
  Hoist the SM-R-7 route filter (`layer1.py:143-160`'s `suppressed_keys`) into `hazard.evaluate`,
  passed **explicitly** (never inferred from process state), so `FieldEvaluator.terms_at`
  (`stage4_field.py:855-873`), `dhara_build_segments` (`dhara_sweep.py:212,227,243,248`) and
  `dhara_compute_null` (`dhara_null.py:86-163`) share one path with `project_layer1`. Write the
  byte-equality test of §4 **first** and watch it fail on current code; then make it pass; then
  flip `test_layer0_projection.py:434-462`. Record the polarity docstring (`stage4_field.py:561-565`)
  as unrelated to this change.
  **Exit:** field ≡ null ≡ projection to `1e-12` on a differing-semantics fixture; the test fails
  under `NEG=1`; no `null_p` path is reachable without it.

**Phase 2 — The seams, by DAG stage (plan §4 stage 3 order).**
  **S4:** thread `baseline_is_synthetic` to `kala_field` (the one migration; today it is computed
  at `layer1.py:89` and discarded, absent from `_KALA_FIELD_INSERT_SQL` `writer.py:631-638`).
  **S3:** replace the σ_T read from `phala_rectification` (`stage3_clocks.py:1012`) with the
  admitted L1 birth-time-precision artifact; interim `default_120s_assumption`
  (`uncertainty.py:170-173`) + F06 `unavailable`; scope `chart_dashas` by ayanāṃśa with a total
  `ORDER BY` (closes `_boundaries` QX, `_system_sigma_t`'s `rows[0]`); read L1 `sandhi_flag`.
  **S2:** carry L2 sign/occurrence (`stage2_promise.py:351-355,457`); the natural edge key is a **demand on L2 via L3-U01** (binding 2.0), not minted here; until it lands, `_routes.path_edge_ids` stays a bigserial reassigned per rebuild, so: add an additive `id_basis ∈ {content_addressed, surrogate_unstable}` column on Kshetra's own routes table, mark the row's identity claim F06 `unqualified`, and record the comparison `self` as `NOT_RUN` with reason `unstable_key` — `comparable_with` stays within Gochara's four-value enum (D-S6, d8d910fec); `unstable_key` is a property of one row, not a relation, and is not a fifth value. **Pins:** add `node_mode` / `epoch_convention` to
  `config_pin` (`stage4_field.py:186-212`, `writer.py:318-336`) declaring the consumed ephemeris
  frame (TRUE node, noon-UT) — first verify whether `corpus_pin` already covers the L0 ephemeris
  generation; if it does, record that and skip. **Edge register:** true in both directions (the ~10 read-never-declared tables; `bo_sangati`/`bo_upaya` declared-never-read); F12 role per edge. **Including the `kala_gochara_windows` read at `stage4_field.py:1384`, undeclared today: declare it as an evaluation-role edge on the TABLE — read-only cross-check, generation resolved through `kala_gochara_authority`, cited by the binding's `window_ref`, never a λ contributor — NOT as a `depends_on` on `ka_gochara_sweep`, which is `RETIRED` and was removed from Kshetra's dependencies by migration 569 under SAMPŪRTI R0; re-adding it would reverse a ruling.**
  **SAVEPOINT** on the cohort read (`writer.py:1754-1770`; pattern `ka_sangam.py:997,1028,1033`).
  Second `'v1'` COALESCE at `stage4_field.py:1386-1389` resolved with `writer.py:2330-2347`.
  **Synergy-binding items (strategic session's `KALA_SYNERGY_AUDIT_v1_0.md` @ 63b5fb429; the author spot-verified
  the marked ones, re-verify all before acting):** (i) [verified: 0 hits] the layer's temporal object is
  `timestamptz` UTC via the shared `ka_temporal` resolver — Kshetra has no reference to it; adopt it for served
  dates once item zero fixes the axis; (ii) [verified: 8 sites] `precision_regime='day_grade'` collides with
  Gochara's `date_grain`/`instant_grain` — **keep the name** — `precision_regime` is a ruled column (ruling 8; Gochara G-9; Saṅgam M-3) and the binding may not rename it (binding 2.0, 5c05a0e2f); re-value `day_grade → date_grain`, aliased until every dependent claim has a successor (D-7's condition, not a generation count); (iii) [verified: half-open convention at `dhara_sweep.py:138,222`; `inclusivity` appears in
  migration 492 — check whether the column exists on `kala_field`/`kala_field_windows` or only in prose]
  declare `inclusivity` per row; (iv) [verified: `find_contact_episodes` at `stage0_kinematics.py:329` mints
  its own `episode_id` (:490,:506)] Kshetra is a second producer of contact-shaped rows beside the Gochara
  kernel's `contact_id` — this is UNRULED (binding B8-6 puts it to the native): until ruled, declare the episodes `evaluation`-only with `comparable_with = different_convention`, and do NOT consume `kala_gochara_contacts` as a substitute without the ruling; (v) [verified: 0 hits] no coverage object on any result and no `independence_group` inherited from
  any witness — both are binding rows, add them in S5/S1; (vi) the `'v1'` COALESCE fall-throughs and the
  `_routes` surrogate ids are already above.
  **Inbound-reconciliation items (`KSHETRA_INBOUND_RECONCILIATION_v1_0.md`, 2026-09-24; each verified at source before it was written here):**
  (a) **Substeps for stages 0–3.** `plan_substeps` (`writer.py:277-405`) registers `prepare:replace`, then `stage4:*`, `stage5*`, `stage6`, `stage65`, `stage8:*`, `snapshot` — stages 0–3 register **nothing**, so the orchestrator's substep-completeness predicate (§N.8, `ORCHESTRATOR_CONVERGENCE_CLOSE` §7.1) cannot see them. Register them as substeps, or record in the state file why the frozen contract forbids it and add an explicit stage-0–3 receipt the predicate reads.
  (b) **K-1 provenance pinning.** `writer.py:948-953` and `:1059-1064` emit `identity_edge(... source_table='kala_gochara_windows', source_pk=str(row['id']))` — a bare row id that dangles across generations. Pin by `(generation, id)`: `source_pk = f'{generation}:{id}'` and `term_key` carrying the generation, resolved through `kala_gochara_authority`. Declare the `→ka_gochara` edge (the CURRENT family producer, not the retired sweep) with F12 role `evaluation` — a cross-check input, never a build-order gate; if the register cannot express role, record the choice rather than add a `depends_on` that would gate Kshetra builds on Gochara builds.
  (c) **Resume fingerprint.** `_fingerprint()` hashes `chart_id` + `field_snapshot_id` + the event-class set but not upstream *content*: an L2 `bodha_pratijna` rescoring resumed as "already done" on the canonical chart (PRATIJNA_V4 B5; a 123-row manual `build_substep_progress` clear was needed). Fold the accepted upstream generation/content hash (`bodha_pratijna.computed_at` or its digest) into the fingerprint, alongside `config_pin`.
  (d) **Binding B1 columns.** Add `time_basis ∈ {event_instant, noon_ut_knot, date_grain_midpoint}` on every served row; `inclusivity = 'closed_open'` literal; `t_exact`/`t_peak` as `timestamptz` or NULL — never a sentinel — once item zero fixes the axis.
  (e) **CG-1 both halves.** The Circularity Guard needs the dynamic half (LEL mutation with pins unchanged ⇒ field hash bit-identical, `H₁==H₀ ∧ S₁!=S₀`) **and** the static half (no stage 0–8 module imports or queries an LEL table); `tests/l3/ka_kshetra/test_circularity_guard.py` must carry both with a negative control each.
  (f) **Ephemeris backend assert.** The backend is process-global and unowned; every swisseph call Kshetra makes (`stage3_clocks.py:885` Moon velocity at birth; any S0 root refinement) asserts the backend per call from `retflag` (no `FLG_MOSEPH` bit) — never inferred from process state (checklist B4; Sangam R-3).
  (g) **F-78 is already on the writer** (`writer.py:227 built_event_classes`; `tests/l3/ka_kshetra/test_event_classes_disclosure.py`), though its spec still reads "awaiting REVIEW". Do not duplicate it; your S4 migration must not collide with it; cite it in the state file.
  (h) **`kala_timeline` is DARK; `kala_timeline_spec` is yours.** Never conflate them in a query, a register row or prose.

  **Exit:** every seam has an assertion-based test with a negative control; the register census
  (`FROM`-census over every module vs the seed) is clean; the migration is verified applied.

**Phase 3 — The ablation, exactly as sealed.**
  Record the SHA-256 of `KSHETRA_ABLATION_PREREGISTRATION_v1_0.md` in `EVENTS.jsonl` and the state
  file **before** generating any arm. Generate arms A / A′ / B on fixture-bound source for the
  pairs its §3.2 selects; blind per §3.3; open the two judges per §2 with the sealed rubric only;
  adjudication and censoring per §5.3. Score sheet filed beside the state file.
  **Exit:** PASS under §5.1 → Phase 4 opens. **FAIL → park-with-preservation:** record the
  negative with every score, mark P1 `NEVER_FUNDED`, skip Phase 4's S1 and §6's enrichment, and
  proceed only with Phase 4's U10/U11/U01 items that do not depend on the claim.

**Phase 4 — S1 ingestion packet (gated on Phase 3 PASS) and the interfaces.**
  **S1:** consume `ka_vedha_gochara` (all `vedha_kind`s, admitted under the uniform rule — today
  32 applied / 3 deferred / 6 unqualified house-vedha; laṭṭā and malefic scale applied;
  sarvatobhadra unqualified — **and NO prose-only remedy: the L0 repair attempted the grid from PG345–354 verbatim and was blocked on primary-source grounds (3/28 asterisms, direction unstated, glyphs garbled; PR #2727 item 4), so this packet's earlier "buildable from prose today" is withdrawn**; every row `unqualified` until the producer's `corpus_verifiable` /
  `source_qualification` / `precision_regime` columns exist — **check, do not assume: as of 2026-09-24 they exist on Gochara's unmerged branch (WP9 migration 1082) and NOT in production (`information_schema`: none on either table)**). **Stale consumer rows (checklist C3, verified live):** the canonical chart's 132 `house_vedha` rows in `kala_vedha_gochara` were built 2026-09-07 and still cite "BPHS Ch.29"; the 24 sarvatobhadra rows cite Prasna Marga (not in the corpus); neither writer fingerprints `bg_transit_rules`. Consume only rows rebuilt after the L0 re-citation, or treat citation-stale rows as `unqualified` — never let a row's stamp outrun its citation. **M-8 semantics you must read, not infer:** exceptions (Sun↔Saturn, Moon↔Mercury) emit **no vedha row** and the coverage object records `searched, exception_applied`; vipareeta rows are kept with `cancelled=true`; a retrograde malefic carries `intensity_qualifier='retrograde_malefic'` with no weight. **Mūrti** rows are graded at the true sign-ingress instant (`precision_regime='instant_grain'`) with the day-grade misclassification rate reported. **If you consume Gochara contacts (B8-6, once ruled), the handle is D-S5's `window_ref = {asset_id:'ka_gochara', generation, id: contact_id}` against PK `(chart_id, generation, contact_id)`.** **Malefic scale:** the served `bg_vedha_malefic_scale` is pinned (L0 item 5, migration 1077) as Adh. XXVI's **PG353 battle-context** scale, distinct from PG349's general-transit 1–5 scale; which one a *transit* covariate should read is a doctrinal choice — put it to the native in the S1 packet, do not pick silently and
  `ka_moorti_nirnaya` (unify the moorti split across term families, `stage1_symbolization.py:229-230`);
  internal `build_vedha_primitive` / `build_moorti_primitive` become one-generation cross-checks, then retire under contract §5 — **per ruling 4, after one cross-check generation, never unconditionally**; `av_kaksha_gate` from `ganita_av_transit_gating` (the same admitted
  AV source as Saṅgam E2); kota / sudarshana / tithi-praveśa declared as applicability covariates
  (E7b needs `ka_tithi_pravesha`'s own source qualification first — C8). **S5:** denominator prose; the null's non-comparability flag and `1/R` resolution survive every projection. **Binding B2/B4/B5 columns (KALA_SYNERGY_BINDING v2.2 — carried in spirit, now named):** emit `epistemic_class` (F04), `completeness_state` with exactly the six values `{applied, inapplicable, unavailable, unqualified, contradictory_unresolved, unexplored}`, `operator_role` (F12), `tier_basis ∈ {relative_uncalibrated, calibrated:<gate_id>}`; inherit `independence_group` as the **union** of every witness's groups and carry it with `comparable_with` on any scored projection (jsonb shape is B8-4, the native's); emit `coverage` on every result in the seven-field shape `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}`, and an empty result is **a row and a coverage object, never "no row"**.
  **U11:** `query_field_trajectory` capability with the L3-owned sentinel test (Pūrṇa implements
  the capability; you write the test). **U10:** `mi_bhara` binds via the `kala_field_snapshots`
  manifest, content-hash checked, `ORDER BY built_at DESC`, refusing when no manifest exists — this
  is an L5 packet; you write the spec and the sentinel, you do not edit `mi_bhara.py`. **U01:**
  upstream sign.
  **Exit:** S1 accepted at exact tip by an independent read-only reviewer; sentinels green with
  negative controls.

**Phase 5 — P6 → P2 → P1, each against its equivalence contract (brief §4.6).**
  P1 only if Phase 3 passed. Each candidate proves identity to the unoptimised path on the
  exhaustive-shift oracle before it replaces anything. A reduced cap, coarser grid or narrower
  horizon can never pass as an equivalent optimisation (Strategy §5).
  **Exit:** `PRODUCER_READY` at an exact tip with an independent exact-tip review — the brief's §8 terminal evidence packet — **plus:** the registry row carries real `integrity_check_sql` / `expected_volume_formula` / `expected_volume_inputs` / `size_sql` (today null; `target_floor` 0), with the invariant F-KSHETRA-11 proposed: stage-4 segments tile each `(chart_id, event_class)` with no gaps or overlaps, and every `kala_field_windows.field_snapshot_id` equals the chart's newest `kala_field_snapshots` row; and the binding's proof matrix in brief §6 — its tests 5, 6, 7 and 9, each with a negative fixture — is green (rule of adoption; D-S3 approved this form). **The W7 build (`DATA_ACCEPTED`) is not in this prompt.**

## §6 — Fences you cannot cross (summary card)

Frozen orchestrator · no populated-chart build, `KshetraReplacementHeld` never weakened ·
delete-then-insert per chart × natural key · cascade proof before any destructive step · no
fabricated values · L1 authority · no post-apply migration edits · floors from achieved counts ·
S1 and P1 gated on the sealed ablation · byte-equality before any `null_p` · no edits to `bg_*`,
Saṅgam, Gochara, Pūrṇa or registry files · never trigger `ka_gochara_v3_century_materialize` ·
the corpus is the table.

## §7 — Autonomy mechanics (anti-halt)

- **Do not stop to ask permission for work §2 authorizes.** Stop only for: a needed orchestrator
  contract change; a ruling/plan contradiction; a destructive operation whose blast radius you
  cannot bound; anything requiring a native ruling.
- **When blocked on one item, take the next independent item.** Record the blocker with what would
  unblock it. Do not idle and do not invent.
- **Re-verify rather than trust**, including this prompt.
- **Never self-certify.** Final acceptance is the native's or an independent reviewer's.
- **Other streams are live on this machine.** Never `git stash`; never `git worktree prune`; never
  `git gc`; never check out another stream's branch. Your branch and worktree are yours alone.

## §8 — Durable state (the campaign's memory)

Maintain `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KSHETRA_STAGE3_STATE.md`: current phase,
exits passed with their evidence, decisions taken with reasons, blockers with unblock conditions,
the sealed ablation hash, and the last commit. Append one line per material event to
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/EVENTS.jsonl` (`"packet": "KSHETRA_STAGE3"`). Update
both **before** each commit, so a fresh session re-pasting this prompt resumes exactly where you
stopped.

## §9 — First actions, verbatim

1. `cd /Users/Dev/madhav-l3/kshetra-stage3 && git rev-parse --abbrev-ref HEAD && git fetch -q origin main && git merge --ff-only origin/main && git status --short`
2. Read the Phase 0(a) list in order. Write nothing yet.
3. `git diff --stat c58e86662 HEAD -- platform/python-sidecar/services/ka_kshetra` — must be empty.
4. Check the DB; run the two Phase 0(d) counts; record them.
5. Read `KshetraReplacementHeld` (`writer.py:543-550`) and confirm no `ka_kshetra` build is
   running or dispatched.
6. Append the ledger entry (Phase 0f); write `KSHETRA_STAGE3_STATE.md` with Phase 0's exits;
   commit; push; open the first PR.

## Conduct

Ground every claim in a file, a line, or a live query. Where the plan and the code disagree, say so
rather than smoothing it. An honest "this is unresolved and here is what would resolve it" is worth
more than a confident build that is wrong. Do not invent astrological doctrine: where a method's
qualification is missing, route it to its authority. You are implementing a ruled plan — propose
amendments where evidence requires and record them; the native rules.
