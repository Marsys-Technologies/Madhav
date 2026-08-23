# HANDOFF — Cowork Supervisor Conversation for PARIŚEṢA V4 (2026-08-21)

**Who this is for:** a fresh Claude (Cowork) conversation on the owner's NEW account,
taking over the supervising role a prior conversation held. The prior conversation is
lost with the account switch; this document is its replacement memory. Read all of it,
then the "How to load the rest of the context" section, before acting on anything.

**Who the owner is:** Marsys (the repo owner). Product: **Madhav** — a Vedic-astrology
(Jyotish) insight platform (repo `Marsys-Technologies/Madhav`, org GitHub account
`amonty84`). Quality bar the owner holds: "beyond Acharya-grade astrological insight,
interpretation completeness, and correctness of information." Status fact that many
decisions rest on: **pre-launch, no real customers; DB is routinely wiped/rebuilt and
treated as non-sensitive.** If that ever changes, several standing authorizations
below are void (see §4).

## 1. The two-session structure — critical to understand first

There have been TWO Claudes involved, with distinct roles:

1. **The campaign session** — an interactive Claude Code CLI session on the owner's
   Mac, inside tmux session `parisesa`, worktree
   `/Users/Dev/par-night/parisesa-v4-conductor`, launched with
   `--dangerously-skip-permissions`. It executes the PARIŚEṢA-RĀTRI V4 campaign
   ("Closure Factory") — closing a corpus of findings (originally 141, grown to 182+
   by discovery) in the Madhav repo. It journals everything to branch
   `parisesa/campaign-state`.
2. **The supervisor conversation (the role YOU are inheriting)** — a Cowork
   conversation that: authors/elevates the campaign's kickoff prompts and directives,
   independently VERIFIES the campaign's reports against the repo (never trusting
   prose), analyzes open/parked items, surfaces risks, and — under explicit owner
   delegation — issues owner-level rulings. The owner pastes your directives into the
   campaign session and pastes its reports back to you.

The supervisor's working method, proven repeatedly: **verify against primary sources**
(the `ledger.json` / `journal.ndjson` on `parisesa/campaign-state`, the GitHub API for
PR/merge state, live commits) rather than trusting any report's own claims. Two real
catches came from this: a stale local git mirror nearly misread as a false report, and
compressed summaries conflating two distinct findings (F-146 vs F-150).

## 2. Campaign history in brief (chronological)

- **Plan v1.0 → v1.1**: added a full cross-campaign isolation charter (§7) because the
  repo hosts multiple campaigns — PARIPRAŚNA (live autonomous swarm, corpus STRANGER —
  zero shared findings, pure contention hazard, never touch) and dormant siblings
  (`par/*`, `ekv/*`/EKAVĀKYATĀ, `samapti`, `sampurti`, etc. — corpus SIBLINGS whose
  git history is read-only prior-work evidence). Lease discipline via the
  `origin/campaign-coordination` branch before any merge/deploy.
- **v2.0 → v2.1**: full-autonomy design was safety-refused by a Claude Code session
  (correctly — it pre-authorized irreversible actions with a "never ask" framing);
  rebuilt as "overnight-build / morning-ship": build all night, hold merges/deploys/
  data-writes for a morning checkpoint. **v2.1.1** added model tiering (Sonnet 5 base,
  Opus 5 for judgment-critical work) and fixed launch mechanics (isolated worktree,
  tmux, literal-paste of the prompt — a `cat` once got summarized instead of pasted).
- **First overnight run (v2.1.1)**: 84→85/142 terminal, 21 PRs frozen for review, zero
  merges/deploys. Watchdog never fired (root cause later: PATH, not permissions).
- **Closeout & hardening sessions**: root-caused and rebuilt the watchdog (launchd
  agent, v5→v7 after Opus adversarial reviews found real defects incl. a cwd-scoping
  gap that once nearly hijacked a PARIPRAŚNA conversation via `claude --continue`),
  added session-ID pinning (`claude --resume <uuid>` from heartbeat.json), durable
  self-healing sleep prevention (dedicated KeepAlive caffeinate launchd job —
  the earlier in-watchdog version thrashed and was caught within minutes of go),
  STOP.flag kill-switch discipline throughout.
- **v3.0 FULL AUTONOMY run (the big one)**: owner explicitly authorized — after the
  supervisor made the tradeoffs explicit and confirmed pre-launch/no-real-users —
  removal of the morning checkpoint: unattended merges (GA-5: independent review +
  separate Opus-5 adversarial pre-merge review, whose defect hit-rate was very high
  and caught a real authorization bypass in #1390 pre-merge), deploys (canary +
  auto-rollback pipeline), GA-3 protected-data executions, architecture rulings
  (GA-2 decide-and-act), live-session access (synthetic/dev only). Result: 113/142
  terminal, 21/21 PRs merged, production in sync, honest disclosure of 2 self-caught
  errors (a misclassification corrected via broadened search; a PR-merged↔ledger sync
  gap that recurred twice → automated `check_ledger_pr_sync.py` was later built,
  lives at `00_ARCHITECTURE/briefs/parisesa/scripts/`).
- **v3.1 FULL CLOSURE run**: addressed all 30 then-parked items, Opus 5 primary.
  Corpus grew to 182 findings (investigation kept surfacing real new defects);
  **134/182 terminal** at last verified read (journal seq ~950). F-23 carve-out
  (classical-content authority) produced a provisional ruling document instead of
  unilateral action. Two process-integrity disclosures: **F-146** (GA-3 rollback
  rehearsals ran against an FK-incomplete replica — no damage, production FK refused
  correctly) and **F-150** (an authorized rebuild's automatic stale-cascade flipped
  the `state` field of the ka_kshetra row protected by standing ruling PAR-R-9 —
  metadata only, specimen data intact, session correctly declined to "fix" it with
  another write and escalated).

## 3. Where everything lives (all on branch `parisesa/campaign-state` unless noted)

- `00_ARCHITECTURE/briefs/parisesa/state/ledger.json` — authoritative per-finding
  state (182 rows at handoff; check `findings_terminal_count`).
- `.../state/journal.ndjson` — append-only hash-chained event journal (truth).
- `.../state/CLOSURE_REPORT_20260821.md` — v3.0 run's full record (updated by v3.1).
- `.../state/CLOSEOUT_AND_HARDENING_REPORT_20260820.md`,
  `.../state/PREFLIGHT_HARDENING_ADDENDUM_20260820.md` — watchdog/hardening history.
- `.../state/F23_PROVISIONAL_RULING_20260821.md` — the F-23 draft ruling + 4 open
  questions.
- `.../state/OWNER_RULINGS_20260821.md` — **committed alongside this handoff**: the
  nine rulings R-1..R-9 issued on the owner's behalf (see §5).
- `.../state/RESUME.md`, `heartbeat.json` — campaign resume pointer + liveness.
- `.../scripts/check_ledger_pr_sync.py` — PR↔ledger drift detector; run it before
  trusting terminal counts.
- Watchdog: `/Users/Dev/par-night/parisesa-v4-conductor/watchdog.sh` (v7) + launchd
  jobs `com.marsys.parisesa-v4-watchdog` and `com.marsys.parisesa-v4-caffeinate`
  (Mac-local, not in repo).
- Kickoff/directive lineage (files were delivered into the OLD account's conversation;
  their content is summarized in §2 and their governing terms in §4 — the v3.0 prompt
  also exists in-repo as referenced by the closure report's §0).

## 4. Standing authority framework (what the campaign may do without asking)

v3.0 authority, owner-confirmed in live conversation (recorded in the closure
report §0 and the lease record on `campaign-coordination`): unattended merges via
GA-5 (independent review + Opus-5 adversarial pre-merge review + fresh lease read),
unattended deploys (canary → smoke → promote, auto-rollback), GA-3 protected-data
execution once a complete 5-clause packet exists (now amended by ruling R-7: full
FK-connected replica for rollback rehearsal; before-images verified against measured
rows_written), GA-2 architecture decisions (decide-and-act, journal rationale +
rejected alternatives), synthetic/dev live-session access. Sonnet 5 default,
**Opus 5 for all judgment-critical work** (adversarial reviews, irreversible calls,
domain-correctness verification). Acharya-grade bar: domain correctness verified
against classical sources, distinct from code correctness; ambiguity journaled, never
silently resolved.

**VOID CONDITIONS — check before relying on any of the above:** the authority rests
on (a) pre-launch / no real customers, (b) non-durable, non-sensitive data, (c) the
owner's delegation standing. If ANY changes, the morning-checkpoint boundary
(v2.1.1) re-applies by default. Isolation absolutes (PARIPRAŚNA/sibling namespaces,
lease-before-merge/deploy, no stash/gc/prune/force-push, no credential ops) were
NEVER relaxed by any autonomy grant. STOP.flag in the conductor worktree root
overrides everything, always.

**Delegation boundaries the prior supervisor held (inherit these):** broad "decide
for me" instructions were honored for engineering/operational judgment but NOT
silently extended to (1) classical-scholarly content rulings — carved out until the
owner explicitly re-delegated, at which point rulings R-1..R-4 were issued WITH
stated confidence and the recorded caveat that human-scholar review remains
worthwhile; (2) anything touching real users — moot pre-launch, revisit at launch.
When the owner explicitly overrides after seeing the tradeoff stated, that is
honored and recorded (that is how v3.0 came to be).

## 5. The nine standing rulings (R-1..R-9, issued 2026-08-21 on owner delegation)

Full text in `.../state/OWNER_RULINGS_20260821.md`. One-line each: **R-1** Saturn
bīja: Devanagari (*śanaiścarāya*) correct, fix the transliteration. **R-2** BPHS
bīja attribution ruled incorrect-as-stated → reattribute to tantric/Mantra-Mahodadhi
tradition. **R-3** Nakshatra rows keep nāma-mantra as served form; TB 3.1.1–2 as
attestation enrichment; correct the over-claiming citations now. **R-4** F-23 Lane 4
authorized under strict attestation gating; 4-lane plan ratified; column contract
adopted. **R-5** F-150: accept current state, no restorative write; preservation
rulings must scope frozen columns; F-152 audit trigger endorsed. **R-6** F-141:
metadata-fix permanently refused; real rebuild authorized ONLY after F-149 lands +
R-7-compliant packet + specimen archived first. **R-7** F-146's two GA-3 template
amendments adopted as mandatory. **R-8** F-31: synthetic dev-session verification
authorized. **R-9** priority order: F-175 first (affirmative false-clean in
assess_*), then the 6 DATA_PARKED GA-3 executions (F-35, F-52, F-62, F-63, F-71,
F-104), then F-23 Lanes 2–3, F-149 design (gates F-141 rebuild).

## 6. Open items at handoff (verify against ledger before acting — this list ages)

At last verified read (ledger at 182 findings, 134 terminal, journal seq ~950):
~48 non-terminal. Key active set: **F-175** (top priority, GA-5 reviewer's explicit
flag), 6 DATA_PARKED rebuilds, **F-149** (streaming content-hash rewrite — hard
prerequisite for F-141's rebuild; current code would deterministically OOM),
**F-141** (conditionally authorized per R-6), **F-23** Lanes 2–4 (unblocked by
R-1..R-4; F-144 = Lane 1, urgent, no scholarly gate), **F-150** follow-through
(PAR-R-9 scope update + F-152 audit trigger), F-31 synthetic-session verification,
plus the remainder visible in the ledger (statuses: DECISION_PARKED / DATA_PARKED /
EXTERNAL_HOLD / STRANDED / OPEN / UNKNOWN / LANDED-not-terminal).

## 7. Known risks / watch items

1. `claude --continue` cwd-collision on the Mac: mitigated by watchdog v7's session-ID
   pinning, but remains the sharpest residual local risk when multiple Claude Code
   sessions coexist.
2. The ledger-sync defect class recurred twice; `check_ledger_pr_sync.py` exists but
   has known false-positive modes (documented in its docstring) — run it, read it
   critically.
3. Corpus growth: every deep investigation has minted new findings (142→182). Expect
   the terminal denominator to move; never quote a stale count.
4. Report prose vs ledger truth: summaries have conflated findings before (F-146 vs
   F-150). Always resolve to the per-finding ledger entries.
5. The local git mirror in any sandbox may be stale and may not be able to fetch
   (proxy 403). Use the GitHub API tools for fresh state.
6. F-150's policy gap (cascade vs preservation rulings) is ruled (R-5) but the F-152
   audit trigger is not yet built.

## 8. How to load the rest of the context (do this in your first turn)

1. Read `00_ARCHITECTURE/briefs/parisesa/state/OWNER_RULINGS_20260821.md` (same
   branch as this file) in full.
2. Read `.../state/CLOSURE_REPORT_20260821.md` in full.
3. Pull `.../state/ledger.json`, recompute the terminal/parked split yourself from
   the per-finding `status` fields (terminal = SERVICE_CLOSED, CONTROL_CLOSED,
   HISTORICAL_STALE_CLOSED, NOT_APPLICABLE_CLOSED), and list the current non-terminal
   set — do not reuse §6's snapshot numbers.
4. Check `.../state/RESUME.md` + `heartbeat.json` for whether a campaign session is
   currently live or idle.
5. Then report to the owner: current true counts, whether the campaign is
   running/idle, the top of the R-9 queue, and wait for direction. Do not launch or
   direct any campaign work without the owner asking.

**Access paths:** the owner's Mac (Claude desktop app) usually has the Madhav folder
connected — the repo is then at the `Madhav` mount, and GitHub API tools are
available via the bridge (`mcp__remote-devices__github__*`). The local mirror may be
stale; prefer the GitHub API for branch-fresh reads of `parisesa/campaign-state`.

*End of handoff. The prior supervisor's parting note: the discipline that made this
work was (1) verify everything against primary sources, (2) state tradeoffs before
accepting broad delegation, (3) record every ruling with its basis so it can be
overruled item-by-item, and (4) treat honest disclosure of one's own errors — the
campaign's and your own — as the load-bearing habit. Keep those four and the rest
follows.*
