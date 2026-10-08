---
artifact: CLAUDE.md
version: "8.0"
status: CURRENT
role: >
  Root orientation surface for every Claude session on MARSYS-JIS. Holds DURABLE rules only.
  Live state lives in CURRENT_STATE_v1_0.md; full history lives in CLAUDE_MD_CHANGELOG.md.
produced_on: 2026-10-08
supersedes: "CLAUDE.md v7.5 (2026-09-20) — verbatim text preserved in git history and summarized in CLAUDE_MD_CHANGELOG.md"
changelog: "See 00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md (v8.0 entry explains this slim-down)."
---

# MARSYS-JIS — Master Instructions for Claude

Section letters (§A–§N) and §N.1–§N.8 numbering are stable anchors cited across code, CI and briefs — keep them when editing.

## §A — Project mission

Build an LLM-operated Jyotish instrument that, for the native (Abhisek Mohanty), (1) reads the chart with acharya-grade depth; (2) surfaces patterns and contradictions across layers and systems that no single astrologer could hold in working memory; (3) makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes — then extends the method beyond this native as a research tool. Bounded by the Ethical Framework in `MACRO_PLAN_v2_0.md` §Ethical Framework: probabilistic, calibrated, auditable outputs for consenting audiences; not a fortune-telling product.

## §B — Subject

Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India.

- **Canonical chart_id:** `482012f1-710e-4a25-994a-93821f5871aa`. `362f9f17-…` is a dead phantom — never write it.
- **Canonical L1 facts:** the `chart_facts` DB table (built by the L1 `ga_*` writers). The old FORENSIC v8.0 markdown is archived at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` as a cold benchmark, not a live source. No session re-derives the foundational chart.
- **7 FORENSIC birth anchors** (hard facts): Sun = Capricorn · Moon = Purva Bhadrapada · Lagna = Aries (all 5 ayanamshas) · Tithi = Shukla Tritiya · Vara = Ravivara · Yoga = Shiva · Karana = Garaja.

## §C — Session orientation (read what the task needs, not everything)

1. **Live state:** `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` is ~1 MB — read only the top banners of its §2 "Canonical state block" (newest first). Never take "you are here" from this file.
2. **Your campaign's own brief/charter** (named in your prompt, or in the newest CURRENT_STATE banners). If root `CLAUDECODE_BRIEF.md` exists, is not `status: COMPLETE`, and names your session/worktree, its `may_touch`/`must_not_touch` govern; otherwise ignore it.
3. **Read when relevant** (do not pre-read):

| When you are… | Read |
|---|---|
| Interpreting the chart or touching doctrine | `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` §B (principles B.1–B.12), §H.4 |
| Doing a formal session handshake/close | `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`, `SESSION_OPEN_TEMPLATE_v1_0.md`, `SESSION_CLOSE_TEMPLATE_v1_0.md`, `ONGOING_HYGIENE_POLICIES_v1_0.md` |
| Writing/altering any layer writer or the build | `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` (+ `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`) |
| Working on L1 / L2 / L3 / L4 / L5 | `L1_GANITA_CLOSURE_v2_0.md` / `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` + `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md` + `MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` / `L3_KALA_CLOSE_v1_0.md` / `L4_PHALA_CLOSE_v1_0.md` / `L5_SEAL_AND_SHIP_REPORT_v1_0.md` |
| Making a cross-campaign decision | `CROSS_CUTTING_DECISION_REGISTER_v1_0.md`, `DISAGREEMENT_REGISTER_v1_0.md` |
| Creating a branch, worktree or file | `WORKTREE_ISOLATION_PROTOCOL_v1_0.md`, `ROOT_FILE_POLICY.md` |
| Strategy / phase scoping | `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` (orientation only — never pre-build later phases) |

## §D — Canonical artifacts

`00_ARCHITECTURE/CAPABILITY_MANIFEST.json` is the single source of truth for canonical paths and versions (`CANONICAL_ARTIFACTS_v1_0.md` is a superseded historical registry). Do not duplicate version numbers here. Core synthesis artifacts (paths checked by `drift_detector.py` — keep these strings): `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` · `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` · `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` · `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` · `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` · `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` · `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` · (historical) `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md`.

## §E — Layer model

L0 Brahmagyan · L1 Gaṇita · L2 Bodha · L3 Kāla · L4 Phala · L5 Mīmāṃsā. All six were built and sealed in the original build arc (seals named in §C); several layers are now being re-elevated asset-by-asset by live campaigns. **Which layers/assets are currently open is live state — see CURRENT_STATE §2, never a table here.**

## §F — Current position

Not maintained here. Read CURRENT_STATE §2 (see §C.1).

## §G / §H — Session open and close

Sessions that do formal governance work emit the SESSION_OPEN handshake and SESSION_CLOSE checklist per the templates above, validated by `platform/scripts/governance/schema_validator.py`; only then is `00_ARCHITECTURE/SESSION_LOG.md` appended (open + body + close as one entry). The `session-close` skill automates the close. Campaign fleets may use one campaign-level handshake as their charter specifies. A session must not claim close without a validated checklist.

## §I — Operating principles

Full list: `PROJECT_ARCHITECTURE_v2_2.md` §B (B.1–B.12). The most-violated:

- **B.1 — Facts/interpretation separation.** Facts at L1; derivations at the Bodha boundary with an explicit ledger; interpretation at L2+ only.
- **B.3 — Derivation ledger.** Every L2+ claim lists the specific L1 fact IDs it consumes. No "as is known classically" without a source.
- **B.8 — Versioning discipline.** Canonical artifacts carry `version`, `status` and a changelog; registries must not disagree.
- **B.10 — No fabricated computation.** If a value needs a specialist tool and is not already in L1, mark it `[EXTERNAL_COMPUTATION_REQUIRED]` with an exact spec. Never invent chart values.
- **B.11 — Whole-chart read.** Interpretive queries route through L2 Bodha synthesis (MSR + CDLM + CGM + RM) first. Carve-out (RS-4): a pinpointed factual lookup satisfies B.11 via its frame check plus a one-line escalation flag when the fact touches an active contradiction, firing yoga or open prediction window (`RETRIEVAL_STRATEGY_v1_0.md` §3.6).
- **Scope:** declare what you may and must not touch before editing; respect other campaigns' `must_not_touch`.
- **Isolation:** never build or commit in the shared checkout — use a worktree and a PR (`WORKTREE_ISOLATION_PROTOCOL_v1_0.md`).

## §J — Quality standard

Acharya-grade: an independent senior Jyotish acharya should judge the work "my level", "above my level", or "shows me what I'd have missed on first pass". Nothing less.

## §K — Multi-agent collaboration

Gemini mirror discipline is retired (2026-05-27). Claude Code and Codex both work this repo; coordinate through PRs, decision registers and campaign briefs, never by editing another campaign's in-flight files.

## §L — Do not

- Produce generic astrology, or collapse layer separation.
- Skip the whole-chart read for interpretive work (B.11).
- Change architecture, or the FROZEN orchestrator contract, without the native's explicit approval.
- Restate canonical versions/paths or live state here — point to the manifest and CURRENT_STATE instead.
- Pre-build infrastructure for later macro-phases.

## §M — Cadence

Red-team passes are owed at the cadences in `MACRO_PLAN_v2_0.md` §IS.8 (every third session by default; every macro-phase close; yearly for the plan itself); the handshake's `red_team_due` field tracks it.

## §N — Build standards (durable; inherited by every layer)

### §N.1 — Layer naming (LOCKED)

External lexicon Brahmagyan · Gaṇita · Bodha · Kāla · Phala · Mīmāṃsā = internal L0–L5; never show "L0–L5" externally. Asset ids use underscore prefixes `bg_*` · `ga_*` · `bo_*` · `ka_*` · `ph_*` · `mi_*`. Dot-notation (`bodha.*`, `ganita.*`) is retired — never create one.

### §N.2 — FROZEN orchestrator contract

Sealed at `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2. Every writer: is a `@register('<asset_id>')` `WriterBase` subclass; implements `run(ctx) -> WriterResult` or `plan_substeps(ctx)` + `run_substep(ctx, step)`; runs on `ctx.db_conn` and NEVER commits or closes it (the orchestrator owns transaction + per-substep savepoint); never writes `asset_throughput` (the orchestrator is the sole build-state writer); takes `chart_id` + `birth_params` from `ctx.config`. Native-authorized freeze exceptions are recorded in that file (§7.1, SATYA-DĪPA) and in the campaign plans that granted them. **If a writer seems to need a contract change, STOP and raise it with the native.**

### §N.3 — Idempotency per layer

L0: `ON CONFLICT DO NOTHING/UPDATE` on global reference tables. L1+: per-chart **delete-then-insert** scoped to `(chart_id × natural key)` — a rebuild replaces, never accretes (shared helper pattern: `_idempotency.py`).

### §N.4 — Ratified build principles

- **Floors are aspirational, not gates:** set `target_floor` to the achieved count; never fabricate rows to hit a number.
- **No audience tier in writers:** emit all rows; serving governs access.
- **Deterministic-first:** Python over LLM for computation; embeddings are fine; generative LLM curation is not.
- **No JH-parity oracle:** verify by internal consistency, classical-rule re-derivation and FORENSIC grounding.
- **Cockpit truth:** each asset needs a correct chart-scoped `count_sql` on `asset_registry` (the stats route reads `count_sql`, not `asset_throughput`).
- **Surgical migrations, verified:** the deploy-time `migrate.ts` runner is fine, but verify your migration actually applied, and never edit a migration file after it has been applied.
- **Honest verification tiers:** `single` is a permitted tier for `ga_sensitive` (stored with a warning, not build-fatal). Never emit `two_pass_verified` for a row nothing double-checked. Emit tiers via the named constants in `verification_vocab.py`, never bare string literals.

### §N.5 — L1 is the authority over L2+

An L2+ signal never restates an L1 computed value as its own truth — it references the L1 `fact_id` and inherits its value. A derivation that disagrees with the L1 fact it cites is a halt-worthy bug, not a stored divergence. MSR `constituent_facts_array` entries must resolve to `chart_facts.fact_id`.

### §N.6 — Serving Density Principle

Every served surface layers rows by verification/confidence density; never flatten them into one undifferentiated list.

1. **Catalog matches are not confirmed findings.** Single-pass catalog rows (e.g. `fire_reason: 'requires_pass'`) are still served (B.10 forbids silent drops) but counted and flagged separately (`catalog_only_rows_in_page`, `judgment_flags: catalog_only_rows_present`), with a pointer to the firings-authoritative surface.
2. **Budget trims protect the densest layer first.** Sections carrying confirmed findings declare `hardFloor: true` in `response_budget.ts` so their `minKeep` survives the hard-cap pass; label catalogs and secondary corroboration trim first.
3. **A verdict layer is never empty when grounding data exists.** Confirmed rows sort ahead of corroboration; an honest gap is reported in `judgment_flags`, never hidden behind a hollow envelope.
4. **Density signaling is data, not narration.** `density_contract` on `CapabilityDescriptor` declares `paginated`, `facets` and `empty_reason` discipline machine-readably; a capability that claims it must ship the `empty_reason` behind it.

### §N.7 — Narration Fidelity Principle

1. Narration is a deterministic restatement of L1-referenced facts: it reads a cited `fact_id`, never re-derives it.
2. Any selection that reduces a set to one row pins `fact_key` and carries a total `ORDER BY` (or `DISTINCT ON` / `LIMIT 1` equivalent) — enforced by the `check_fact_category_pinning.py` CI guard.
3. No wrapper-local constant may shadow an L1-computed value, even if currently correct.
4. A verification flag must have a real detector behind it, or be null.
5. Verified fact ≠ verified prose: every narration layer needs its own semantic/golden-value test.
6. An honest null beats an invented judgment — never substitute a plausible-sounding default.

### §N.8 — Earned-Signal Principle

Every status, grade or PASS must be computed by a detector that measures the specific claim it asserts; a signal without such a detector is null, not green. Audit question: *what code path would have to run — and fail — for this signal to correctly read false?* If none exists, or it checks a proxy, the signal is null. Confirmed instances (detail in `SATYA_DIPA_REPORT_v1_0.md` and ORCHESTRATOR_CONVERGENCE_CLOSE §7.1):

1. Ṣaḍbala selector regression — served the wrong strength column; no test compared served vs. source.
2. Two `bo_pramana_mapa` flags — could read true without their check ever running.
3. The PB-2 byte-equality gate — a "byte-identical" claim with no byte comparison.
4. The orchestrator no-op-completion predicate — `state = 'lit'` checked "rows present", not "substep plan finished" (fixed 2026-07-29).

---

*CLAUDE.md v8.0 (2026-10-08) — slimmed from v7.5 (~56 KB) to durable rules only, native-authorized. History: `00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md`.*
