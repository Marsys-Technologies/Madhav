# SAMPŪRTI IMPLEMENTATION PLAN v1.0 — three-session autonomous execution
# of SAMPURTI_ELEVATED_PLAN_v2_0 (P0–P8), with E2E/CSF gates at every joint

status: FOR NATIVE REVIEW — nothing dispatches until confirmed. On
confirmation the desk generates 3 kickoff prompts + 3 supervisor scripts
from this file verbatim.
plan_of_record_chain: GAP_REMEDIATION_MASTER_PLAN (rulings R13–R29) →
SAMPURTI_REBASE_PLAN_v1_0 (RB rails, N1–N4) → SAMPURTI_ELEVATED_PLAN_v2_0
(workstreams W-A/B/C, measurements #4/#5/#6, honesty clauses) → THIS FILE
(execution mechanics). Conflicts resolve upward; nothing here relaxes a rail.

════════════════════════════════════════════════════════════════════════
§1 — DEPTH-PASS ADDITIONS (the final pass's own findings; binding)
════════════════════════════════════════════════════════════════════════

1.1 BLIND-SPEC PARAMETER REGISTER (committed BEFORE any effect computed;
    CI-checkable by commit order; R13/R18):
  a. x13 seed β₁₃: ONE conservative structural value, chosen from the
     EXISTING modifier-β scale (read the seeded kala_field_weights x1–x12
     βs; β₁₃ = median of nonzero βs, documented as structural_prior,
     uncited-engineering flag). Never chosen after seeing window effects.
  b. clock voice w_s:gochara: ships 0.0 (inert); activation value = the
     smallest seeded daśā w_s (parity-with-weakest-voice principle,
     documented); flip is its own PR after G-P3a passes.
  c. resonance g_ℓ sharpening: multiplicative re-weight of route gain by
     normalized resonance weight, floor 0.5 / cap 1.5 (R18 bounded;
     mirrors existing modifier bounds), spec'd with worked example on one
     class BEFORE effects; qualifier-token rows (B4) excluded until fixed.
  d. Lattā quality-gate grade: maps to the EXISTING bg_vedha_malefic_scale
     grading path (no new scale invented); janma-nakṣatrā hit severity per
     the verse's own wording; Ketu absent, disclosed.
  e. w23 tara wiring: the register's 9-Tāra schedule verbatim (named
     source), multiplicative into activity, bounded by existing [0,1] λ.
1.2 CG-1 STRENGTHENED PIN (supersedes A1's minimal form): config_pin gains
    {gochara_generation, gochara_calibration_state, gochara_corpus_digest}
    where digest = md5(count(*) || max(computed_at) || max(id)) of the
    consumed generation's rows for that chart. ANY corpus change (YANTRA
    rebuild, future refit) is snapshot-visible by construction.
1.3 MEASUREMENT SCORING SPECIFICS: native chart ONLY for event scoring
    (Abhinandan has no LEL — R28; he serves as structure-only contrast,
    never scored); resolver (G14a) classifications = the event set, its
    PARKED-ambiguous rows excluded and listed; CRPS harness contenders
    registered as TemporalCurveModel over kala_field_windows λ; control =
    the harness's shuffled-birth mirror; noise floor = w42 pattern 1000
    shuffles seeded; sealed split honored even though we score
    retrodictively (train/test discipline: report both, gate on test-era).
    Degenerate-interval tripwire halts publication (R15).
1.4 DUAL-REFERENCE HONESTY: λ_v3 envelopes are resonance-target-anchored;
    Moon-primary attribution remains a SERVING-side presentation rule
    (SIX_VIEWS), not a hazard-side re-computation — no new astrology
    invented at integration time.
1.5 HEADLESS E2E CONNECTIVITY (verified): repo .mcp.json registers the
    deployed MCP (marsys-jis @ Cloud Run) — conductor sessions inherit it;
    FALLBACK if MCP unavailable in any headless attempt: the committed
    HTTP probes (platform/scripts/gochara/smoke_probe.ts,
    probe_gochara.py) extended per-gate. A gate NEVER passes on DB reads
    alone where a product surface exists (the iron rule).
1.6 THE BRILLIANCE GATE (recurring, operationalizing "astrologically
    brilliant"; §J standard): at G-P3b and G-P6, PRATINIDHI (opus, max
    effort, fresh) performs a FULL NATIVE READING via product tools only
    (kala_now_get, kala_ahead_get, kala_explain_get, judgment_query,
    assess_marriage, gochara_forecast_get) and grades it against a fixed
    rubric committed at P0: (i) timing claims at month/day resolution with
    falsifiers; (ii) daśā×gochara concurrence cited per claim with both
    legs named; (iii) verse-resolved citations where the corpus holds
    them, honest 'unresolved' where not; (iv) dual-reference language,
    Moon-primary; (v) honest tiers (thin-class silence ≠ rich-class
    silence); (vi) at least one insight the desk's own reading of the
    inputs did NOT anticipate ("reveals things I wouldn't have seen").
    Verdict written to ledger; a FAIL is a named defect lane, not a
    reroll. Post-hoc retrodiction READINGS (e.g., the 2013-12-11 marriage
    narrative) are evaluation artifacts — never inputs to any parameter.

════════════════════════════════════════════════════════════════════════
§2 — THREE PARALLEL SESSIONS (the velocity architecture)
════════════════════════════════════════════════════════════════════════

Three CONDUCTOR SESSIONS run concurrently, each its own supervisor script,
worktree home, ledger, and territory. This triples throughput because the
three tracks are resource-disjoint: α is DB/build-bound, β is python-code
+ one leased rebuild, γ is TS/serving-code with no chart locks.

┌─────────┬──────────────────────────┬───────────────────────────────────┐
│ SESSION │ SCOPE (phases/streams)   │ RESOURCES OWNED                   │
├─────────┼──────────────────────────┼───────────────────────────────────┤
│ α KṢETRA│ P0,P1,P2,P3 (W-A),      │ port 5433 proxy · chart advisory  │
│         │ measurements #4/#5       │ locks · ka_kshetra + field code · │
│         │                          │ worktrees sm-a-* · ledger §α      │
│ β YANTRA│ W-B (B1–B5), feeds P3   │ port 5434 proxy · gochara_v3 +    │
│         │                          │ grammar + resonance code · ONE    │
│         │                          │ leased corpus-rebuild window ·    │
│         │                          │ worktrees sm-b-* · ledger §β      │
│ γ VYĀKHYĀ│ W-C (C1–C5), P5 preps  │ platform-mcp + serving TS · NO    │
│         │                          │ DB builds, NO locks · worktrees   │
│         │                          │ sm-c-* · ledger §γ                │
└─────────┴──────────────────────────┴───────────────────────────────────┘
After P3 completes, α continues P5→P8 spine; β and γ close into α (their
supervisors exit on their DONE markers; α absorbs remaining lanes).

2.1 COLLISION-PROOFING (every mechanism already battle-tested this week):
  - DISTINCT script names (single-instance guard is per-name):
    run_sampurti_alpha.sh / _beta.sh / _gamma.sh; DISTINCT conductor
    identity strings ("CONDUCTOR of SAMPŪRTI-α|β|γ") so pid-liveness and
    peer-pgrep never cross-match.
  - SESSION MANIFEST appended to campaign-coordination at launch: the
    table above, verbatim — territory is machine-readable there.
  - Port split as tabled; NEITHER touches the other's proxy; γ needs no
    proxy (serving code + product-HTTP checks only).
  - DB builds: ONLY α and β, ALWAYS under lease (shared lease table,
    realistic expiry, renew, release). α's chart locks serialize its own
    runs; β's one rebuild window is leased exactly like PARIṢKĀRA's L-6.
  - MERGE DISCIPLINE: all lanes PR → main directly (RB-6); pinned-commit
    gate packets only; a session NEVER merges another session's PR; PR
    titles prefixed [SM-α|β|γ]. Merge-queue serializes across sessions.
  - MIGRATION NUMBERS: claimed in coordination §2 at PR-open (β and γ
    both may need one; α owns x13 weight-seed migration).
  - CROSS-SESSION HANDOFFS = coordination-file MARKERS (the proven
    W6-COMPLETE pattern):
      YANTRA-CORPUS-READY  (β→α): B1–B5 landed + leased rebuild done +
        gate G-B passed → α may execute A1's pin (P3 start).
      FIELD-BASELINE-DONE  (α→all): Measurement #4 published → β's
        corpus is FROZEN for the P3 window (no further rebuilds until
        FIELD-INTEGRATED posts).
      FIELD-INTEGRATED     (α→γ): P3 gates passed → γ's C4/C5 lanes
        unblock (they read integrated surfaces).
      SESSION-DONE-β / -γ: terminal markers; α adopts residuals.
  - RULING REGISTRY: one shared numbering SM-R# recorded in the
    coordination file + owning ledger; PRATINIDHI instances are fresh
    per decision but MUST read the SM-R registry first (consistency
    without shared memory).
  - PER-SESSION LEDGER FILES (refinement, native review 2026-08-13):
    three writers to ONE ledger file would contend on every heartbeat
    push (the non-fast-forward livelock class). Each session owns its
    OWN file: SAMPURTI_STATE.md (α, the spine ledger),
    SAMPURTI_STATE_BETA.md, SAMPURTI_STATE_GAMMA.md — same branch,
    disjoint files, so concurrent pushes auto-rebase cleanly.
  - NON-FAST-FORWARD RULE ADJUSTED for three-session normality: a
    rejected push to the ledger branch is EXPECTED contention → fetch,
    rebase, retry (bounded 3 attempts) WHEN the rebase touches only
    your own ledger file; it is a COLLISION ALARM (stop and inspect)
    only on a content conflict or when another writer touched YOUR
    file. Single-session semantics preserved everywhere else.
  - DEPLOY-VERIFICATION under interleaved merges: verify the deploy
    run whose HEAD CONTAINS your merge commit (ancestry check), not
    "the run for exactly your SHA" — later merges may supersede yours
    in the same pipeline window.
2.2 WHY NOT MORE SESSIONS: α's spine is inherently sequential (build →
  measure → integrate → measure); a 4th session would contend for α's
  locks or β/γ's territory. Three is the parallelism the resource graph
  actually offers. Builder caps: α ≤4, β ≤4, γ ≤4 (machine total ≤12 +
  3 conductors; below the observed comfortable ceiling).

════════════════════════════════════════════════════════════════════════
§3 — SWARM ROLES + MODEL/EFFORT POLICY (per session, identical shape)
════════════════════════════════════════════════════════════════════════

CONDUCTOR (sonnet, runner-enforced): orchestration, ledger §, leases,
  markers, merge train for its own lanes. No product code. Heartbeat ≤10
  min with pid+host+session-tag; peer-liveness at step-0 scoped to its
  OWN identity string; verifies sibling sessions only via markers.
BUILDERS (sonnet, effort medium; haiku for mechanical sweeps — ledger
  formatting, grep censuses, log summaries): fresh worktree per lane,
  TDD failing-test-first, PR→main, model+effort EXPLICIT every dispatch.
VERIFIER — PARĪKṢAKA (OPUS, per native instruction; effort high; FRESH
  per verdict): sole authority for DONE. Default-REFUTED. Own live
  queries; serving claims ONLY via deployed product (MCP tools or HTTP
  probes); migrations execute-to-verify on production-shaped DB; MUTATION
  standard for guards; blind-spec commit-order check on every W-A/B
  parameter; measurement verdicts re-derive at least one headline number
  from raw harness output. No conductor self-verification, ever.
NATIVE-PRATINIDHI (OPUS, max effort, FRESH per decision): the human's
  voice for EVERYTHING a session would have asked the native — answers
  builder/conductor questions, makes delegated rulings with written
  rationale (SM-R registry), runs the BRILLIANCE GATE readings, performs
  end-to-end operational checks on every closed gap ("is every consuming
  surface demonstrably consuming it"). PARKED-FOR-NATIVE (hard, all
  sessions): LEL content · scope reductions · retiring any surface
  without parity · admitting empirically-calibrated gochara into the
  field (config_pin change) · the R27 acharya commissioning.
GATE-EXECUTOR (OPUS, fresh per gate): pinned packets; floors = all checks
  COMPLETED SUCCESS + deploy-run GREEN (retry-once on the known secret
  flake, then structural) + _migrations_applied verified +
  production==main + probe outputs attached.

════════════════════════════════════════════════════════════════════════
§4 — PHASE-BY-PHASE LANES, PARALLELIZATION, AND E2E/CSF GATES
════════════════════════════════════════════════════════════════════════
Legend: [α/β/γ] session · (S/M/L) size · ∥ parallel group · G-* gate.
Every G-* gate: evidence PASTED in ledger; product-level wherever a
product surface exists; VERIFIER signs; failures become named lanes.

── P0 (α) CLOSE + SPEED — day-zero spine ────────────────────────────────
∥ α-01 (S) R1-CLOSE verifier packet: criteria (a)–(d) by query on the 6
    classes; (e) daśā-ladder spot-read ≥3 classes vs chart_dashas;
    window tables pasted; rung GREEN-PER-CLASS(6/27).
∥ α-02 (M) PERF TRIAD lane (TDD; behavior-preserving by construction):
    edge-free hazard.ln_lambda_only fast path · memoized
    FieldEvaluator.breakpoints() · substep-scoped terms_at memo (L1k
    pattern). CSF: identical window output on a fixture decade
    (byte-compare) + measured substep wall-clock.
∥ α-03 (S) Session-open hygiene automation (orphan reap via
    stop-flag-then-kill, phantom rows, locks=0, proxy check) as a
    committed script all three sessions call at open.
∥ γ-00 / β-00 (S) Session launches: manifest + territory + ledger §
    skeletons + BRILLIANCE-GATE RUBRIC committed (1.6) + blind-spec
    register file committed EMPTY (specs land per-lane before effects).
G-P0 GATE: α-01 rung entry + α-02 ≥2× measured speedup on a stage-4
    substep sample + all three sessions heartbeating without cross-match.

── P1 (α) COMPLETION ∥ (β) YANTRA CODE ∥ (γ) VYĀKHYĀ EARLY ─────────────
α-10 (L, sequential) Field completion: remaining 21 classes via
    checkpoint-resume runs inside S5 asset_set (native chart first);
    RB rails absolute (exclusions, clear_before=false, one run per
    chart, protection counts each merge).
α-11 (M, after native 27/27) Abhinandan full-DAG (bump verified deployed
    → his 123 stale checkpoints invalidated correctly; ancient six
    windows fall).
α-12 (M) S6 acceptance lanes (∥ within): 4 Kāla planes · CDLM==13
    (investigate honestly if 11 persists) · 4 L3 query tools · facade
    VERIFY-OR-WIRE · G13 assess_domain live.
∥ β-10..14 (M each) B1 w23 wire + unit/parity suites · B2 w30 nodal
    drishti mechanism (L1 constants verbatim, hedge preserved) · B3
    Lattā consumption into quality_gates · B4 resonance tokenizer fix ·
    (then) B5 leased corpus rebuild folding B1–B4, PARIṢKĀRA-L-6
    evidence conditions + w43 ablation per wired mechanism + honest w44
    refit (non-zero now possible; stamps only via w45 §N.8 gate).
∥ γ-10 (M) C1 term_breakdown+verse_refs serving · γ-11 (S) C2 hierarchy
    nesting · γ-12 (S) C3 coverage-tier facet · γ-13 (M) C5 re-key
    DESIGN+build behind flag (activation waits for FIELD-INTEGRATED).
G-P1 GATE (α, product-level): 27/27 classes with >1 window · minority
    fraction · via deployed product: kala_now_get sub-elevation LIT for
    native · kala_explain_get returns field-diff · judgment_query domain
    reading carries field-backed timing · Abhinandan battery repeat ·
    zero ancient windows remain.
G-B GATE (β, before marker): per-mechanism ablation table (real deltas
    or honest zeros) · corpus profile diff pasted · protection counts ·
    smoke probe green · nodal trines present in corpus (query: windows
    whose term_breakdown cites w30 targets) → post YANTRA-CORPUS-READY.
G-γ1 GATE: via product — gochara_forecast_get response carries
    term_breakdown summary + citation_verse_refs + nested hierarchy +
    coverage tier; seeded-failure test of each facet.

── P2 (α) MEASUREMENT #4 (baseline; corpus frozen by marker) ───────────
α-20 (M) Harness registration (field as TemporalCurveModel) + noise
    floor + sealed-split guard + tripwire; publish #4 at earned tier.
G-P2 GATE: #4 published with CRPS + skill-vs-control + floor + per-class
    table; VERIFIER re-derives one number from raw output; honest-null
    acceptable and publishable. → FIELD-BASELINE-DONE.

── P3 (α) DVIPRAMĀṆA (blind specs already committed per-lane) ──────────
α-30 (S) A1 pin (1.2 strengthened form) — THE first integration commit.
α-31 (M) A2 resonance lane → scoped re-field (native) →
G-P3a GATE: provenance edges show resonance/clock terms with real
    log_contributions summing (§5.4 reconciliation asserted); window
    BOUNDARIES unchanged vs P2 snapshot (clock-lane property proven);
    magnitudes changed; product explain shows new terms.
α-32 (M) A3 clock voice ships inert → activation PR after G-P3a.
α-33 (L) A4 x13: schema bump x13_v0 + β₁₃ seed migration + envelope
    builder + circular-shift participation test (the null actually
    tests it — replicate-vs-real divergence check) → full re-field
    (both charts) →
G-P3b GATE: windows MOVED (boundary diff vs P2 snapshot, pasted) ·
    Measurement #5 beside #4 + per-seam ablation table · BRILLIANCE
    GATE #1 (1.6 rubric, full product reading) → FIELD-INTEGRATED.

── P4 (γ finishing) VYĀKHYĀ LIVE ────────────────────────────────────────
γ-40 C4 unified NOW/AHEAD narrative (both surfaces, Moon-primary
    attribution, honest tiers) · γ-41 C5 ACTIVATE re-key →
G-P4 GATE (product): one real kala_ahead_get call files a prospective
    row keyed to a field window_id + authority_basis (live row shown);
    unified narrative sample pasted; A5 agreement facet in explain.
    → SESSION-DONE-γ (α adopts).

── P5 (α) WAVE-2' RETIREMENTS ──────────────────────────────────────────
Per legacy surface (NON-gochara list only): PA-7 parity audit →
PRATINIDHI ruling → tombstone; census armed-to-fail red-then-green;
L2b/c/d/e live checks. Batches serialized; no adoption deploy mid-batch.
G-P5: census gate green with seeded violation demo; every retirement
    carries its parity evidence; gochara tools untouched (N1 verified).

── P6 (α) WAVE-3 RUBRIC CYCLES + #6 ────────────────────────────────────
Cycles strictly sequential (blind spec → variant off → side-by-side both
charts all 27 → PARĪKṢAKA mutation+R13 → PRATINIDHI adoption per R25 →
flip+gate+scoped re-run + scoreboard vNext): F-STRENGTH → F3 →
F-CONDITION(+R24 portal audit precedes)+PA-3 upaya wire → G9 minis.
G-P6: Measurement #6 beside #5 · G14c engine-pinned CI gate ·
    BRILLIANCE GATE #2 · PA-3 CSF: one live kala_upaya_get coherent
    with condition magnitudes.

── P7 (α) WAVE-4 LOOP + TIERS + G15 ────────────────────────────────────
G14 loop live (with C5: outcomes now calibrate the FIELD) · G2 Tranche-3
(career first; ADJUDICATION-2 + framing test; PRATINIDHI T2 ratify) ·
R23 T2/T3 tiers (27/27 speaking; thin labeled via coverage tiers) ·
G-P7: loop live-proof (real filed row → outcome-recordable trace shown) ·
    dashboard ≥12 quantitative · THEN G15 last, both charts, beside the
    2026-07-25 baseline.

── P8 (α) CLOSE ─────────────────────────────────────────────────────────
Independent re-close VERIFIER verdict (MR-29 pattern) · ledger
reconciliation · CURRENT_STATE + SESSION_LOG · residuals honest-deferred
with triggers (incl. anything β/γ handed over) · worktree/branch hygiene
zero-residue · RUN-TERMINAL: ARC-COMPLETE.
AWAITING-NATIVE recorded, never attempted: acharya review (R27) ·
Abhinandan LEL (R28) · Tier-2 charts · calibrated-corpus admission.

════════════════════════════════════════════════════════════════════════
§5 — CRITICAL-PATH + FAILURE POSTURE
════════════════════════════════════════════════════════════════════════
Critical path: α-02 → α-10 → G-P1 → #4 → P3 → #5 → P6 → P7. β must post
YANTRA-CORPUS-READY before α reaches A1 (expected: β finishes during
α-10's machine-time; if late, α proceeds to P2 on the CURRENT corpus and
β's rebuild waits for a post-#4 window — order guarded by markers either
way). Failure posture everywhere: diagnose-fix-retry with named lanes;
never blind-retry; honest FAIL/null publishable; a red BRILLIANCE gate
spawns defect lanes, not despair. Every session close: NEXT-ACTION
current; supervisors relaunch on drop; terminal only by marker.

════════════════════════════════════════════════════════════════════════
§6 — WHAT THE NATIVE REVIEWS IN THIS FILE
════════════════════════════════════════════════════════════════════════
(1) the three-session split + its collision-proofing; (2) the blind-spec
parameter register (1.1) — the only numbers anyone will ever tune, fixed
before effects; (3) the BRILLIANCE GATE rubric (1.6) as the definition of
"astrologically brilliant"; (4) gate placement/strictness; (5) the
critical path trade in §5. On confirmation: 3 kickoffs + 3 scripts
generated verbatim from this file; launch = three terminal commands.

════════════════════════════════════════════════════════════════════════
§7 — THIRD PASS (Fable 5): FAILURE-MODE REGISTER FROM THE ACTUAL LOGS
════════════════════════════════════════════════════════════════════════
Every failure this campaign family actually hit, mapped to its live
countermeasure. A kickoff that cannot cite this table is not launchable.

FM-01 merged-to-integration ≠ on-main (PG-31; 350× INSERT storm killed
      runs 5–11) → R0 packet merges integration→main; VERIFIER greps the
      seam ON MAIN post-merge; deploy-green before any dispatch.
FM-02 OOM: 19× EnvelopeIndex ≈2GB (runs 1–4) → shared index landed; iron
      rule: builders profile any new per-substep allocation ≥100MB.
FM-03 idle_in_transaction hangs, two DISTINCT sub-classes (2026-08-13/14
      stop-and-analyze pass — do not conflate them):
      (a) idle-with-no-query (the original bug): db.py's
      idle_in_transaction_session_timeout was disabled (=0) as a fix for
      an EARLIER premature-kill incident, which meant a transaction gone
      idle with no active query never auto-recovered → hours-long hangs
      requiring manual pg_terminate_backend. FIXED: S7459/PR #1269 + the
      earlier-landed MR-39 routing (both confirmed on the deployed image,
      SHA 4747ea831 — MR-39 predates and is included in the S7459 commit,
      NOT a later gap) bound it to 1800000ms (30 min) via BOTH a startup
      option AND a committed session-level `SET`, applied through the
      single `db.py::connect()` factory that every standalone build-
      runner script now routes through. Confirmed structurally correct
      and comprehensively deployed on re-audit — do not re-litigate this
      sub-class without new evidence.
      (b) lock-wait hangs (newly identified, UNFIXED as of this entry):
      a query BLOCKED waiting to acquire a lock shows as
      state='active'/wait_event_type='Lock' in pg_stat_activity, NOT
      'idle in transaction' — idle_in_transaction_session_timeout does
      not apply to this state at ANY value. Every orchestrator connection
      also sets statement_timeout=0 (unbounded) and NO connection anywhere
      in the codebase sets lock_timeout. A genuinely lock-blocked query
      (contention, or a lock orphaned by an earlier crashed/killed
      session) therefore has ZERO auto-recovery today. This is the
      leading candidate for the second, post-S7459-deployment hang
      (stage2_promise.py's bodha_pratijna SELECT, distinct call site from
      the first incident's writer.py COUNT query) — NOT a failure of the
      S7459 fix, but a different failure mode the fix was never designed
      to cover. (The earlier "role-level 600s default is winning"
      hypothesis from mid-session live diagnosis is WITHDRAWN on this
      re-audit: it was inferred from `pg_roles.rolconfig`, which shows
      only the role's DEFAULT, not a live session's actual effective GUC
      — Postgres exposes no SQL-level read of another backend's SET
      values — and a plain committed `SET` durably overrides the role
      default for the rest of that session per Postgres semantics, so
      the mechanism proposed does not actually hold up.) MITIGATION
      (P0 for Δ1's restart, before any further field-build dispatch):
      add `SET lock_timeout = '<bounded>'` (e.g. 5–10 min) to
      `db.py::connect()` alongside the existing idle/statement timeouts,
      so a lock-blocked query raises a catchable exception instead of
      hanging forever; VERIFIER confirms via a live worker session at R1
      (extend the existing GUC-verification duty to include lock_timeout,
      not idle_in_transaction alone). SECONDARY, non-causal but real:
      `amjis_app`'s role-level idle_in_transaction_session_timeout has
      drifted from its migration-tracked value (migration 241: 120s) to
      a live-observed 600s via an untracked `ALTER ROLE` outside the
      migration system — reconcile with a proper numbered migration
      (§N.4 surgical-migrations-verified) even though it is not the hang
      cause. See FM-21 for the structural (conductor-side) half of this
      mitigation.
FM-04 single-row INSERT storms (5–10 min/decade; 30-min finalize) →
      executemany landed; iron rule: NO new per-row DB loop in any
      writer lane; VERIFIER checks batching on every write-path diff.
FM-05 monolithic-run ops model vs resumable design (~30 timed attempts)
      → N4: per-class closure; checkpoint-resume inside S5; bounded
      per-run progress IS success; NEVER delete build_substep_progress.
FM-06 orphan orchestrators: 0%-CPU zombie polling stop flags, child pid
      survives parent kill, advisory lock held for hours → committed
      hygiene script (stop_requested_at → wait 25s → kill → terminate
      idle lock-holders → locks==0 assert) runs at EVERY session open
      AND before every dispatch; every dispatch records run-id+pid in
      the ledger so recovery targets precisely.
FM-07 supervisor cap kills conductor mid-orchestrator run → caps stay
      (safety); nohup'd orchestrator survives conductor death BY DESIGN;
      next session's step-0 hygiene adopts-or-reaps it via the recorded
      run-id; asset progress persists via substep checkpoints.
FM-08 heartbeat gaps 75+ min while working → ≤10-min duty restated: a
      long wait is a REASON to heartbeat; watcher-visible.
FM-09 ledger lags reality at kill → step-0 reconcile (adopt, never
      redo): PRs/merges/_migrations_applied/DB state before dispatching.
FM-10 dual conductors (timestamp-as-liveness) → pid-liveness + peer-
      pgrep scoped to DISTINCT identity strings per session.
FM-11 single-instance guard false-positive (matched its own caffeinate
      wrapper; blocked every launch) → proven form: pgrep -f
      "bash .*<script>" excluding $$ only; regression-tested.
FM-12 worktree-on-branch collision at launch (git forbids two worktrees
      on one branch) → scripts ADOPT an existing worktree holding the
      branch (worktree move), else create; per-session HOME BRANCHES
      make recurrence structurally impossible (see 7.1).
FM-13 deploy failures: PROD_DATABASE_URL flake (retry-once rule) + an
      unappliable FK migration that PASSED prose review twice →
      execute-to-verify on production-shaped DB, always; deploy checked
      by RUN conclusion + ancestry (§2.1), never by merge status.
FM-14 zero-CI lane merges (allowlist gap) → lanes PR → MAIN, full CI;
      zero-check merges forbidden.
FM-15 gate-packet livelock (PR head tracked a moving branch; 4+ CI
      restarts, nothing reached main) → pinned-commit packets; no lane
      merges while a packet's CI runs.
FM-16 seed/ON-CONFLICT migrations silently reversing later state (the
      cutover-reversal class) → any seed-file touch ships with a CI
      shadow-DB guard asserting post-state survives a seed rerun.
FM-17 stale-checkpoint delta-skip (ENGINE_VERSION class; 123 pre-fix
      checkpoints) → RULE: ANY output-changing writer edit bumps its
      resume/version constant IN THE SAME PR — applies to P3 itself:
      A2/A4 bump _RESUME_VERSION (4, 5, …) as part of their lanes.
FM-18 foreign-script accident (a conductor executed another campaign's
      dispatch script; no arg guard → ran fully) → every dispatch
      script ships argparse with required --chart/--confirm; conductors
      never execute scripts outside their territory path.
FM-19 credential leak into transcripts (.env.local read) → secret-
      manager recipe only; grep-guard in VERIFIER checklist.
FM-20 headless MCP availability → .mcp.json verified; per-gate HTTP
      probe fallback committed; a gate never passes on DB reads alone.
FM-21 no ACTIVE hang detection on the conductor side (2026-08-14
      stop-and-analyze finding): every recovery this campaign has done —
      including the original hours-long idle-with-no-query hang that
      predated any server-side timeout at all — required a HUMAN (this
      desk session) to notice, diagnose, and manually
      pg_terminate_backend + cancel the execution. No server-side timeout
      (idle_in_transaction, statement_timeout, or the new lock_timeout
      from FM-03b) fully substitutes for this: each bounds ONE failure
      mode, and a bug in code not yet audited (a future standalone script
      that bypasses db.py::connect() again, per the MR-39 precedent of
      this having already happened once) can always reintroduce an
      unbounded wait. STRUCTURAL FIX: the conductor's own long-run
      monitoring loop (LONG-RUN AUTONOMY RULES, sm_common_rails.md) polls
      pg_stat_activity for its own dispatched build's longest-running
      query on each heartbeat (≤10 min per FM-08); a query running longer
      than a generous ceiling (e.g. 25 min) with wait_event_type='Lock'
      OR with zero substep-progress-row growth in that window is a
      self-diagnosed hang — the conductor recovers it itself (same
      stop-flag → terminate → cancel → verify-locks==0 sequence this desk
      session has been doing by hand) and records the recovery in its own
      ledger, rather than waiting for a human to catch it. This closes
      the actual gap: not "which GUC value is correct" but "nothing
      autonomous was watching."
FM-22 manual-intervention discipline (2026-08-14 investigation F-4/F-5 —
      binds the DESK as much as conductors): premature desk kills at
      T+10–15min prevented the 30-min server-side layer from ever firing,
      which kept the failure "mysterious" for a full day; one kill was
      justified by a GUC misread (current_setting() reads only the CALLING
      session — a desk psql session reads the amjis_app role default, NOT
      the hung backend's value; Postgres offers no SQL read of another
      backend's session GUC — the per-run smoke-log (FM-03b) is the only
      per-connection truth). RULES: (a) no manual kill of a hung build
      before T+35min unless its locks demonstrably block other critical
      work — the 30-min layer firing IS the missing evidence, let it; (b)
      capture pg_stat_activity + job logs BEFORE any kill; (c) desk gcloud
      actions are audit-logged under the NATIVE's identity (the SM-R-3
      false-park mechanism) — a coordination entry describing the action
      ALWAYS precedes the action itself.

FM-23 built-but-unwired module (2026-08-14, the 9-hour finding): three of
      the four merged DHARA modules — dhara_null (PR #1263, the vectorized
      1024-replicate null engine), dhara_term_matrix (PR #1266, the n2
      artifact/EXPLAIN deliverable), dhara_pin_matrix (PR #1264, the
      surgical stage×class rebuild architecture) — were designed, built,
      TDD-tested, parity-covered, merged, and DEPLOYED, yet imported by
      NOTHING in the production path (only their own tests). The field
      build ran 9h because the fast null engine existed on disk in the
      running container and was never CALLED. §N.8 applied to modules: a
      merged optimization with no production call site is a null signal
      wearing a green PR. COUNTERMEASURE: CI guard asserting every
      services module family (dhara_*) is imported by production code;
      integration lanes (the wiring) are first-class planned lanes with
      their own acceptance evidence, never assumed to ride along with the
      module lanes; PARĪKṢAKA rate/perf diagnoses MUST cite the exact
      substep keys measured and reconcile observed cost against the
      design's own estimate — "slow because CPU" is not a diagnosis when
      the design promised 20 minutes (SM-R-6 F-13/F-14).

FM-24 timeout-disable-as-guard (SM-R-7, 2026-08-14): PR #1274 "protected"
      a slow substep with `SET LOCAL idle_in_transaction_session_timeout
      = 0`, disabling the only auto-recovery layer — the next transport
      stall became unbounded (bxnww, 33+min hung on that exact statement).
      Third instance of the disable-a-timeout-as-a-fix pattern (S7459's
      original =0, MR-39's gap, now this). RULE: a slow-but-legitimate
      operation gets a LARGER bound, never an infinite one; no PR may set
      any timeout GUC to 0/disabled as a regression guard.
FM-25 performance claim without a performance detector (SM-R-8 audit):
      dhara_null was titled and docstring'd "vectorized" while being a
      sequential per-replicate Python loop; every correctness gate passed
      and the false speed claim shipped to production, costing the 9h
      saga. §N.8 applied to performance: a perf claim ships a perf test
      (CI fixture with a hard time ceiling), or the claim is null.
FM-26 built-vs-designed drift (SM-R-8 audit): a module can be merged,
      TDD-green, parity-green, and still implement a DIFFERENT algorithm
      than its frozen spec (dhara_null computed its merged knot array and
      never used it). COUNTERMEASURE: implementation lanes cite the
      design § they implement; PARĪKṢAKA verifies the ALGORITHM against
      the frozen spec, not only outputs; V-batteries include the design's
      quantitative claims (complexity/timing), not correctness alone.

7.1 THIRD-PASS CORRECTIONS (supersede earlier text where conflicting):
  a. PER-SESSION LEDGER **BRANCHES** (supersedes per-file-same-branch):
     α = sampurti/integration (existing home) · β = sampurti/yantra ·
     γ = sampurti/vyakhya (each cut from main; single-writer branches —
     the strongest contention fix; FM-12 impossible by construction).
     The ONLY multi-writer surface remains campaign-coordination
     (append-only + bounded push-retry, proven). Cross-session state
     reads = git fetch + show (proven pattern).
  b. TELEMETRY LANE (engineering best-in-class): ka_kshetra populates
     WriterResult.duration_seconds + per-substep wall-clock into notes
     (α-02 rider) — future runs get real timing data instead of
     commit-message archaeology.
  c. MCP-AS-PROOF DOCTRINE (native directive, third pass): the deployed
     MCP (the customer's own surface; marsys-jis in .mcp.json) is THE
     acceptance instrument. Every G-* gate lists its MCP calls; the
     standing battery (smoke-probe pattern) extends per phase; the two
     BRILLIANCE GATE readings use MCP tools exclusively; P8's close
     includes a full customer-journey transcript (now → ahead →
     explain → judgment → assess_marriage → gochara forecast → upaya)
     pasted as the arc's final exhibit. DB checks corroborate; MCP
     proves.

7.2 FOURTH-PASS CORRECTION (2026-08-13, live root-cause — binding):
  d. THE 27/27 FIELD GATE WAS AN OVER-PROMISE. λ⁰ₑ requires a ratified
     lifetime-count prior (brahma_class_priors, fact_kind=
     'lifetime_count_per_100y'; ADJUDICATION-2 Tier N-i evidence bar);
     6 classes hold one (Tranche-1); Tranche-2 refuted 9/9. ClassSkipped/
     no_class_prior_row is B.10 honesty, not a defect. G-P1's gate is
     REFRAMED: "every prior-backed class built + honest skip ledger."
     27/27 lives at the R23 serving-tier level (P7), as originally ruled.
     NEW LANE G2-EARLY (pulled from P7): Tranche-3 sourcing through
     ADJUDICATION-2 + framing test, PRATINIDHI-ratified (R29), batch
     APPEND-ONLY seeding, folded into P3's re-field (fingerprint's
     class-list forces full replan — one rebuild, never per-class).
     MEASUREMENT ISOLATION: #4↔#5 delta on the matched class subset
     only; G2-early classes report as first-measurement rows.
