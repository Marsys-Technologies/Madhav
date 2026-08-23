# SAMPŪRTI REBASE PLAN — DRAFT-3 (grounded 2026-08-12, pre-confirmation)

status: CONFIRMED (native, 2026-08-12) — N1 RULED: RETAIN gochara_* serving
surfaces (carved out of R4 retirement list permanently; R-COORD-4 resolves as
RETAIN, to be recorded in the coordination file at conductor open). N2 RULED:
G15 runs ONCE, LAST. N3 MOOT. This file is the plan of record; the conductor
copies it into the repo at first run.
method: every claim live-verified (DB, registry, git, coordination file) at
2026-08-12 morning IST. Prior drafts' audit findings carried where still true,
struck where the world moved.

## §1 — GROUNDED DELTA (what PARIṢKĀRA delivered since DRAFT-2)

D11. YIELD LIFTED by native (Aug-11 17:3x, "C8") → waves 4–5 merged to MAIN:
     MR-37/40 (wave 4); MR-11/12/16/19/20/23/38/39/41/42 (wave 5); MR-44/45
     (hierarchy peak retention + resolution in natural key, Aug-12 00:34).
D12. THE CORPUS IS NOW THE ELEVATED ASSET, MATERIALLY: native chart gen-3.0 =
     **17 classes · 326 rows · 197 intervals + 29 points + 100 CHAINS**;
     hierarchy LIVE (42 day + 42 month + 14 era resolution-tagged rows; 249
     pre-tag rows NULL); suppression now FIRES (322 of 432 rows non-empty
     across both charts — the founding v1 pathology measurably dead);
     resonance map rebuilt at **27 classes both charts** (17 materialized;
     10 presumably honest-thin — preflight pins the exact profile).
D13. PG-31 STILL NOT ON MAIN (verified by ancestry + grep). RB-3 blocker
     unchanged and now MORE severe: v1 rows still coexist, corpus bigger.
D14. RB-1 DEGRADED TO BROKEN-TODAY: ka_gochara_sweep throughput row flipped
     'lit' → **'stale'** — the Python runner's dependency seeding refuses
     non-lit states → ka_kshetra deadlock-blocks ON DISPATCH. The depends_on
     fix is no longer "permanent hygiene"; it is a HARD pre-R1 gate.
D15. _RESUME_VERSION still = 2 on main → RB-2 (Abhinandan's 123 pre-fix
     checkpoints) still open; the bump rides our gate packet.
D16. RB-13 UNCHANGED: ka_gochara registry row still mis-pointed (production
     target_table/count_sql, staging writer) → clear_before stays FORBIDDEN.
D17. L-7 lease shows ACTIVE with NO conductor running (PARIṢKĀRA's close-out
     session ended without releasing). Adjudicate at conductor open per the
     expiry rule; likely DEAD-BY-EXPIRY → override with note.
D18. PARIṢKĀRA still OPEN: MR-12 verdict in flight (#1225), MR-29 re-close
     queued, MR-32/33/41/42/43 open; MR-42 explicitly says "fix BEFORE next
     corpus rebuild." It may run its remaining sessions during our overnight.
D19. Two FAILED runs (Aug-11 16:32, one with empty asset list) + corpus
     provenance for the 326 rows needs one reconciliation read (their MR-29
     will document; we PIN the corpus profile + HEAD SHA at R0 regardless).
D20. LUCKY SEQUENCING FACT: kala_field_windows = 0 (P-G1 never ran) → there
     is nothing to RE-field. The FIRST field build runs against the fully
     elevated corpus (hierarchy+chains+17 classes). The PA-5 re-field
     obligation is satisfied BY CONSTRUCTION; MR-16's corpus landed before
     our first build. Decision N3 (interleave) is MOOT.

## §2 — VERIFIED DONE (adopt, never redo)

Wave 0 complete · S1/S2 wiring + L1b–L1j fix chain merged · PG-31 merged to
sampurti/integration (NOT main — see P0) · PG-32 · G12 CLOSED · G14b · G14a
(ambiguous rows parked-for-native) · clocks proven live (8) · kinematics/
boundaries/routes populated from run 7 lineage · G13 deferred on CDLM
substrate (now 11 domains; target 13 at S6).

## §3 — GAP REGISTER, FINAL (every gap, with disposition)

RB-1/14/16 [HARD, pre-R1] Retired-dep edge + 'stale' throughput + dag-guard:
  MIGRATION (SAMPŪRTI territory): ka_kshetra.depends_on drops
  ka_gochara_sweep (edge choice for guard cleanliness decided in-lane, guard
  run as its test). Until it lands, NO dispatch. Interim assert removed —
  the row is 'stale'; we fix the edge, we don't resurrect the row.
RB-2/15 [HARD, rides gate packet] _RESUME_VERSION 2→3 before ANY Abhinandan
  build (123 pre-fix checkpoints would silently skip).
RB-3 [HARD BLOCKER, P0] PG-31 to main via gate packet (merge
  sampurti/integration → main), deploy-verified. Without it the field build
  loads 4,600+ v1 rows/class → the 350× INSERT storm that killed runs 5–11.
RB-4 [CLOSED] timeout already fixed on main (verify-once during Run 12).
RB-5/13 [STANDING CONFIG] S5 scope='asset_set' (never global); exclusion =
  {ka_gochara, ka_gochara_v3_century_materialize, ka_gochara_resonance,
  ka_vedha_gochara, ka_kota_chakra}; clear_before=FALSE always.
RB-6 [STANDING CONFIG] Lanes PR → MAIN directly (sampurti/integration not in
  CI allowlist; zero-check merges forbidden).
RB-7 [SCHEDULED] Abhinandan's ancient six windows fall at S5 chart-2.
RB-8 [GATE] CDLM 11→13 at S6, honest reason if short.
RB-9 [RULED→plan] G15 once, last (after all corpus/field motion). (N2)
RB-10 [OPEN NATIVE DECISION N1] Wave-2 retirement list: gochara_* surfaces
  carved out pending R-COORD-4 (desk rec: RETAIN).
RB-11 [MOOT by D20] PA-5 satisfied by construction; if PARIṢKĀRA rebuilds
  corpus again post-field (MR-41/42 fixes), xref edges are value-inert
  provenance — accepted drift, SHA-pinned evidence, scoped xref re-verify
  lane queued only if their rebuild happens.
RB-12 [STANDING] deploy retry-once-then-structural + run-green + tracker
  verification on every gate packet.
RB-17 [AT OPEN] L-7 adjudicated per expiry rule before first lease claim.
RB-18 [AT R0] Corpus profile + registry state + main HEAD pinned into the
  ledger as the build's declared inputs (provenance independence from
  PARIṢKĀRA's pending MR-29).
RB-19 [COORDINATION] PARIṢKĀRA concurrent: leases serialize DB builds; its
  MR-42 note means the corpus MAY be rebuilt during our window — our field
  evidence pins SHAs; no SAMPŪRTI lane touches gochara code/data, ever.

## §4 — PHASES (R0–R6)

R0 PREFLIGHT+GATE-PACKET (sequential spine, one session-segment):
  liveness/L-7 adjudication → lease → pin corpus profile+SHA (RB-18) →
  ONE gate packet to main carrying: sampurti/integration merge (PG-31 = P0)
  + depends_on migration (RB-1) + _RESUME_VERSION bump (RB-2) → CI green →
  merge → deploy verified green + migrations tracker + PG-31 grep on main →
  dispatch-config asserts (RB-5/6/13).
R1 P-G1 RUN 12: single-asset ka_kshetra, 482012f1, fresh plan. Rung criteria
  (a)–(e) unchanged; paste window tables; expected xref profile = the R0 pin
  (per-class gen-3.0 counts), recorded BEFORE dispatch. On GREEN → hard
  block lifts. On RED → root-cause before Run 13; never blind-retry.
R2 S5' FULL-DAG both charts sequential (482012f1 → 1c826d5a): stale ka_/bo_/
  mi_/ph_ set by DAG query minus the five exclusions; clear_before=false;
  sweep-corpus protection counts verified per chart; Abhinandan build only
  after RB-2 bump confirmed deployed.
R3 S6 + S7: four Kāla planes populated + CDLM==13 + four L3 query tools live
  + facade consumption verified-or-wired + G13 assess_domain LIVE →
  MEASUREMENT #4 (R14-versioned, published at earned tier, degenerate-
  interval tripwire).
R4 WAVE 2': L2a divergence audit (v1 baseline intact+protected) →
  authority_basis census armed-to-fail → staged retirement of NON-gochara
  legacy surfaces (PA-7 parity + PRATINIDHI ruling each); gochara_* held
  out per N1. L2b/c/d live checks; L2e anchors.
R5 WAVE 3: cycles F-STRENGTH → F3 → F-CONDITION+R24(+portal audit)+PA-3
  upaya wire; G9 mini-cycles; PA-5 close: scoped re-field only if corpus
  moved since R1 (else skip with reason) → MEASUREMENT #5 beside #4 →
  G14c engine-pinned skill-CI gate.
R6 WAVE 4: G14 loop live · G2 Tranche-3 (career first, ADJUDICATION-2 +
  framing test, PRATINIDHI T2 ratifications) · R23 T2/T3 serving tiers
  (dashboard ≥12 quantitative, 27/27 speaking) · G15 LAST (21-question
  dark-corpus, both charts, beside the 2026-07-25 baseline).
TERMINAL: all gaps closed or honest-deferred-with-trigger; Measurements #4/#5
published; ledger sealed; SESSION_LOG + CURRENT_STATE updated (SAMPŪRTI
territory); acharya-review handoff note (R27 — native commissions).

## §5 — OVERNIGHT EXECUTION ARCHITECTURE (per native spec, this session)

Supervisor script (run_sampurti_overnight.sh): proven pattern — nohup+
caffeinate, single-instance guard (fixed form), env -u CLAUDECODE, cd pinned,
stream-json logs archived per run, ledger-blob-SHA terminal-marker baseline,
14h cap. CONDUCTOR resumes from ledger; PID-heartbeat lease ≤10min; peer-
pgrep liveness (both fixes baked).
ROLES: CONDUCTOR (sonnet) — orchestration/ledger/merge-train only.
BUILDERS ≤6 parallel, fresh worktrees off main (lanes PR → MAIN, RB-6).
VERIFIER-PARĪKṢAKA — dedicated, fresh per verdict, default-REFUTED, own live
queries, deployed-product rule, migration=execute-to-verify.
NATIVE-PRATINIDHI — dedicated, answers all queries + delegated rulings with
written rationale; parks only physically-native items (LEL, scope
reductions, retirements without parity).
GATE-EXECUTOR — packet floors incl. deploy-run-green + tracker + RB-12.
MODEL POLICY (native-granted flexibility, cost⇄velocity optimized):
  haiku → mechanical lanes: doc/ledger formatting, count checks, grep
    censuses, worktree hygiene, log summarization.
  sonnet (default) → conductor, all standard builder lanes, probes,
    dispatch scripts, S5 monitoring.
  opus → VERIFIER verdicts, PRATINIDHI rulings, GATE-EXECUTOR, and the
    three judgment-heavy lanes only: R1 red-diagnosis (if Run 12 fails),
    Wave-3 amendment specs, Measurement #4/#5 publication writeups.
  EFFORT: low for mechanical, medium default, high for verifier/adjudicator
    verdicts and any red-diagnosis. Model+effort EXPLICIT on every dispatch;
    an omitted model is a policy violation (the Opus-inheritance incident).
PARALLELIZATION MAP: R0 spine sequential → R1 solo (DB lease) → during R1
  compute-wait: Wave-2 PREP lanes (census arming, parity-audit drafts) +
  Wave-3 blind spec drafting (commit-before-effects) in worktrees (code-only,
  no DB) → R2 solo per chart (lease) with R4-prep continuing → R3 partial-
  parallel (S6 verification lanes parallel; S7 sequential after) → R4 lanes
  parallel except serialized retirement batches → R5 cycles strictly
  sequential (adoptions never overlap; specs pipeline) → R6 fully parallel
  except G15 last. PARIṢKĀRA coexistence: lease serializes every DB build;
  code lanes never touch gochara; coordination file checked before every
  production action; port 5433 ours / 5434 theirs.

## §6 — DECISIONS FOR CONFIRMATION (with this plan)

N1 R-COORD-4: RETAIN gochara_* serving tools (desk rec) — shapes R4 list.
N2 G15 once, last (desk rec) — already reflected in R6.
N3 MOOT (D20).
N4 RULED (native, 2026-08-13 00:5x IST): P-G1 CLOSES PER-CLASS. The rung's
evidence standard is met on the 6 built classes (6,708 windows, avg 1.5d,
max 27d vs the 36,525-day baseline — ~1,300× precision gain; criteria a–d
verifiable by query). Formal closure = a VERIFIER (opus) packet: criteria
a–d by live query + criterion e (daśā-ladder tracking) spot-read + window
tables pasted + rung recorded GREEN-PER-CLASS(6/27) in the ledger. The
remaining 21 classes complete INCREMENTALLY via ka_kshetra checkpoint-resume
during R2/S5 — bounded per-run progress is success; the monolithic-single-run
requirement is retired (≈30 runs proved output correctness and run-durability
are separate problems; correctness is proven).
CONFIRM: this plan as the campaign scope + §5 as the execution architecture.
On confirmation: desk generates the kickoff prompt + supervisor script
(implementation plan), nothing dispatches before that handoff.
