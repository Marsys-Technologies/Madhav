---
artifact: REPORT_PB-2
canonical_id: PARIPRASHNA_BUILD_CAMPAIGN
type: WAVE CLOSE REPORT
campaign: PB — Paripraśna Build
wave: PB-2 SMṚTI — the canonical store & memory
version: 1.0
status: CLOSED — ship-degraded (one [integrity] gate item is a confirmed false-confidence gate, not green; see §3/§4 and FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md)
date: 2026-07-28
authored_by: Claude Code (autonomous execution session)
governing: BRIEF_PB-2.md, CAMPAIGN_PB_MASTER_BRIEF_v1_0.md
---

# REPORT_PB-2 — SMṚTI close

## §0 — Disposition

**CLOSED, ship-degraded on one named item.** The six lanes (M-1 canonical
schema, M-2 protocol↔storage, M-3 durable summaries, M-4 pgvector recall, M-5
resume, M-6 provenance stamp) were each built, independently Verifier-ACCEPTed,
integrated, deployed to the real production Cloud Run service behind the
already-flagged route, and exercised with real production readings against the
canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) through three
post-deploy hotfix cycles. All three hotfix cycles found and fixed real,
confirmed defects — the third of the three (bare L1 `fact_id`/CGM node-id
codes reaching the reader) was more severe than what it followed, not less;
each was independently verified against the redeployed production route before
moving to the next.

The wave's own §G gate was then run for real by three independent, fresh-
context gate-runner agents (not the implementer, not this session's own prior
claims) against the actually-deployed route and the real production database.
Of 12 named assertions: **9 PASS with direct evidence** (several live against
production), **1 is INCONCLUSIVE** (a real code path exists with no test
exercising it), **1 is a scope-wording overstatement** (the narrower, load-
bearing property holds; the literal claim as worded does not), and **1 — the
wave's own self-declared "[integrity] centerpiece" — is a confirmed FALSE-
CONFIDENCE GATE**: it has passed on every run without ever being capable of
falsifying the claim it exists to prove. That finding, why it is not a quick
fix, and its disposition are in §3 item 1 and
`FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`.

This wave is closing with the real production system working correctly per
extensive live verification, with three real defects found and fixed (not
zero), and with one gate item named honestly as unresolved rather than
rounded up to green. Native/Pratinidhi disposition on shipping past that named
gap: **ship-degraded, tracked, not silent** — consistent with the master
brief's own "(or ship-degraded per Pratinidhi MEMO)" allowance and this
campaign's practice throughout (PB-1 closed the same way, on smaller items).

## §1 — What shipped

| Lane | Delivered | Verifier verdict |
|---|---|---|
| M-1 (canonical schema) | `platform/migrations`/`supabase/migrations` additive migrations 467/468; `message_parts` closed-enum kind; `platform/src/lib/pariprashna/store/` DAL + `serializeCanonical()` | **ACCEPT** |
| M-2 (protocol↔storage) | `turn.commit` handler writes canonical parts transactionally via M-1's DAL; `route_writer_adapter.ts`; old write-path call removed for assistant-turn content | **ACCEPT** (see §3 item 1 for the gate this lane's own centerpiece test did not actually prove) |
| M-3 (durable summaries) | `conversation_summaries` table (migration 468); canonical-store-aware, citation-preserving, prefix-stable summarizer at `platform/src/lib/pariprashna/summaries/` | **ACCEPT** |
| M-4 (pgvector recall) | Cross-thread recall at `platform/src/lib/pariprashna/recall/`; `prior_reading` citation grade, structurally below `unverified`, never floor-satisfying | **ACCEPT** |
| M-5 (resume) | Ring buffer (`protocol/ring_buffer.ts`, Redis-primary/in-memory-fallback) + `Last-Event-ID` resume (`/api/pariprashna/resume`); `snapshot.apply` fallback; interrupted-turn marking | **ACCEPT** |
| M-6 (provenance stamp) | D-16 stamp wrapper (`provenance/stamp.ts`) around the pre-existing live computation; per-turn write into `metadata_json`; audit-drawer-only, zero streamed bytes | **ACCEPT** |
| Integration | 6 branches merged; migrations applied to production; deploy | **ACCEPT** |

## §2 — Deploy history (real production, `amjis-web`, project `madhav-astrology`)

| Step | Ref | Result |
|---|---|---|
| PR #850 merge to main | — | Merged after a self-healing auto-nudge cycle against a very active concurrent-campaign merge train |
| Migrations 467/468 applied | via `scripts/migrate.ts` against production Cloud SQL | Confirmed post-apply: `conversation_messages` gained `schema_version`/`model_id`/`provider`; new tables `message_parts`, `conversation_summaries`; legacy row count unchanged |
| Deploy | revision `amjis-web-01234-rb7` (and successors below) | Standard CI → Deploy-to-Cloud-Run chain |
| Round 1 production reading | — | Found real [integrity] defect: the model's own prose directly cited internal register acronyms (`"(UCN §XX)"`, `"Cross-Domain Linkage Matrix (CDLM)"`). Root cause: PB-1 lane S-3's citation/register-leak-lint pipeline was built, tested, and ACCEPTED in PB-1 but was **never actually wired into `route.ts`** — a known, disclosed PB-1 residual that was never closed during integration |
| PR #854 (hotfix 1) | merged, deployed as `amjis-web-01235-zhz` | Wired `lintReaderProse` into both the `text_delta` handler (pre-`blockDelta`) and `commitBlock()` (boundary backstop) |
| Round 2 production reading (re-verify) | — | Registers fully clean (7 scrub events fired, zero raw leaks), but found the fix was incomplete in two ways: (a) the lint only matched bare acronyms, not the model spelling out full names ("the Unified Chart Narrative"); (b) redacting an acronym used as a sentence's grammatical subject left broken prose ("The UCN concludes..." → "The concludes...") |
| PR #855 (hotfix 2) | merged (self-healing auto-nudge through 2 BEHIND cycles from concurrent-campaign traffic), deployed as `amjis-web-01239-xvr` | Added a `register_full_name` pattern (6 full names incl. both "Chart Graph Model" and "Causal Graph Model" spellings, and RM/"Resonance Map" which had no acronym-pattern entry at all); redesigned redaction to swap a leading-article+token span for a neutral "This"/"this" instead of deleting the token alone; fixed a `tidyAfterRedaction` ordering bug (double-space collapse ran before, not after, emptied-parens removal) |
| Round 3 production reading (re-verify) | — | Registers clean (42 scrub events, zero raw leaks incl. spelled-out names), but surfaced a **third, more severe** leak class: bare `chart_facts.fact_id`/CGM node-id namespace codes (`PLN.SUN`, `HSE.10`, `KRK.C8.AMATYA`, `SEN.ARD.AL`, `YGA.BUDH_ADITYA`, ...) reaching the reader verbatim, often backtick-wrapped as inline code. Worse than the register leaks: a reader has no chance of parsing `"KRK.C8.AMATYA"` as anything, versus a plausible-sounding acronym |
| PR #856 (hotfix 3) | merged (one more self-healing BEHIND cycle), deployed as `amjis-web-01239-xvr`'s successor | Added a `fact_id_namespace` hard pattern (generic `PREFIX.SEGMENT[.SEGMENT]` shape, deliberately not a hand-enumerated namespace whitelist since no central registry of the namespace vocabulary exists to enumerate from); explicitly excluded `SIG.` since that namespace already has its own dedicated hard + near-miss patterns with different semantics (caught by a regression test before shipping); extended `tidyAfterRedaction` to collapse the emptied-backtick artifacts this redaction leaves |
| Round 4 production reading (final re-verify, `deep_dive`) | — | All three fixed leak classes confirmed clean against a fresh deep-dive reading baiting all of them at once (42+ scrub events, zero raw leaks of any class). One lower-severity, disclosed residual found and left unfixed — see §5.1 |

Each hotfix was shipped as a fresh branch cut directly from current `origin/main`
(not a rebase of the prior hotfix branch) after this campaign hit the
squash-merge-divergence problem twice in PB-1 — this avoided it recurring in
PB-2 across all three cycles. Every hotfix: `tsc --noEmit` clean, full
`tests/pariprashna` + `src/lib/pariprashna` suite green, `git diff origin/main
-- src/app/api/chat/` empty (consult untouched), before merge.

## §3 — §G gate assertions (BRIEF_PB-2.md §G), against the deployed route + real production DB

Verified by three independent, fresh-context opus gate-runner agents dispatched
specifically for this close (not this session's own prior claims, not the
lane implementers).

| # | Assertion | Status | Evidence |
|---|---|---|---|
| 1 | Golden byte-equality: replay→reducer ≡ persisted parts, full fixture corpus AND one real deployed reading [integrity] | **FAIL — false-confidence gate** | The test passes, but proves less than it claims on both halves. **Fixtures half:** runs against exactly ONE hand-authored inline fixture, not the 12-fixture corpus at `tests/pariprashna/fixtures/`; its "reducer path" is a test-owned reimplementation, not the shipped `s1LiveAdapter.ts`. **Real-reading half:** no mechanism exists anywhere to capture a real reading's raw SSE stream, so there is nothing to replay-and-diff against a real reading's DB rows — the claim cannot even be constructed, let alone has it been run. This is the exact anti-gaming failure mode the brief's own charge names almost verbatim. Full writeup + why this isn't a quick fix + recommended disposition: `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md` |
| 2 | Schema conformance on real rows: `schema_version` NOT NULL, closed `kind` enum, `model_visible` NOT NULL, canonical tool name [integrity] | **PASS** | Real DB query against all 5 live new-route rows (11 parts): `schema_version`/`model_id`/`provider` populated on 100%; DB CHECK constraint `message_parts_kind_check` matches the exact required 7-value enum; actual distinct kinds present (`text`, `prediction_candidate`) both in-enum; `model_visible IS NULL` count = 0. The `tool_call` canonical-name sub-check is vacuously satisfied — zero `tool_call` rows exist in production (the writer adapter deliberately never maps that kind, by disclosed M-2 design, to avoid inventing data) |
| 3 | Zero UIMessage/`parts_json` writes on the new route [integrity] | **Overstated as worded; narrower load-bearing property holds** | The new-route **assistant-turn canonical content** never touches `parts_json` (0 of 5 `schema_version=1` rows have non-empty `parts_json`; `store/writer.ts` never writes it). But the route as a whole is not `parts_json`-free: it still writes conversation **history**/user-turn rows through the retained legacy `writeConversationMessages` path — a disclosed, deliberate M-2 scope decision (`route.ts` lines 825–833, 989–996), not a leak. The claim's literal wording ("zero... writes on the new route") is false; the property that actually matters (assistant-turn canonical content is clean) is true |
| 4 | Every migration additive-only with Migration-guard ACCEPT [integrity] | **PASS** | Migrations 467/468 read in full: `ADD COLUMN IF NOT EXISTS` (nullable, no default) / `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` only; the only `DROP` statements are inside commented-out, non-executed `-- DOWN` rollback blocks |
| 5 | Disconnect/resume battery green on the deployed route | **PASS** | Unit: 11/11 (`ring_buffer.test.ts`). Live against production: full turn captured; resume from mid-turn replayed exactly the unseen tail with zero re-delivery; re-resume from the same point was byte-identical (idempotent); a genuine client-side mid-stream kill (`curl --max-time 2`) was a non-event — reconnect tailed live and delivered the rest with strictly increasing seq, no duplicates. Buffer-eviction and server-grace-window-interrupt sub-paths verified by unit test only (not safely live-inducible against production without risking other traffic — flagged honestly, not skipped silently) |
| 6 | `visibilitychange` reconnect green at mobile viewport | **INCONCLUSIVE** | The behavior exists in code (`useLiveStream.ts`, real `visibilitychange` listener → `reconnectLoop` → resume endpoint), but no test anywhere fires it — grep across the whole test tree for `visibilitychange`/`useLiveStream`/`reconnectLoop` returns nothing. A mobile-viewport Playwright project exists for this route but its specs test unrelated concerns (citation-chip tap, viewport height stability), not reconnect. Not rounded up to PASS |
| 7 | Half-committed turn marked `interrupted`, provably excluded from prediction detection | **PASS** | `ring_buffer.test.ts`'s dedicated describe block: behavioral (a stale turn seeded with deliberately prediction-shaped text is finalized `interrupted` and never scored) + structural (`detectPredictionCandidates` absent from source of both the abort path and the ring-buffer/resume path). Code-path confirmed: the detector is called at exactly one site, reached only after the abort-check has already returned |
| 8 | Summaries: threshold writes the row; restart reuses it; splice prefix-stable | **PASS** on tests (25/2-skipped); production-data sub-check **INCONCLUSIVE** (`conversation_summaries` has 0 rows in production yet — nothing to falsify, not a failure) |
| 9 | Summarized-turn fact_ids survive verbatim | **PASS** | `citation_survival.test.ts`, all green — deterministic (`appendCitationBlock`), independent of LLM output, per migration 468's documented contract |
| 10 | Cross-thread recall green; `prior_reading` never satisfies an acharya floor (rejection test) | **PASS** | `floor_gate.test.ts` 8/8 (incl. "no parameter can force prior_reading to served", and an end-to-end real-vidhi-contract test showing `coverage.served === 0` for a prior_reading-only plan); `recall/` tests 12/12 (cross-thread fixture returns the prior thread's conclusion, ranked correctly; `prior_reading` confirmed the strict minimum citation-grade weight) |
| 11 | Stamp on every assistant turn; drift fixture renders edge-state row; stamp fields in ZERO streamed non-audit bytes (wire-tap) [integrity] | **PASS** | Wire-tap: live grep of a full captured production SSE stream for `build_id`/`priors_version`/`formula_versions`/`ranking_config` → zero occurrences (unit suite green alongside: 35/35). Stamp-on-every-turn: directly confirmed via production DB query — all 5 real rows carry a populated `metadata_json.provenance_stamp`. A real chart rebuild happened mid-session (`build_id` changed between two consecutive real rows: `bf2ea4ce...` → `8141e71d...`), the exact drift condition; `provenance_stamp.test.ts` (14/14) covers the drift-fixture assertion |
| 12 | Consult route byte-identical to base pin [integrity] | **PASS** | `git diff origin/main -- src/app/api/chat/` — 0 lines, re-confirmed at every merge/hotfix point across the whole wave (6 separate checks across §2's history) |

**Final proof** ("kill the server mid-turn on the deployed flagged route;
reconnect resumes with zero loss; at settle the persisted parts byte-equal the
replayed reducer state. One byte of disagreement, no wave."): **PARTIALLY
PROVEN, honestly split.** The **resume-with-zero-loss** half is proven live
against production (§3 item 5) — a real mid-stream client-side connection kill
(the sanctioned proxy for a true server-process kill, which was not attempted
against shared production infrastructure for safety) resumed cleanly with no
duplicated blocks and no lost content. The **byte-equal-the-replayed-reducer-
state** half is **not proven**, for the identical root-cause reason as gate
item 1: no mechanism captures a real reading's stream to replay and diff
against its persisted rows. "One byte of disagreement, no wave" — read
literally — cannot currently be evaluated at all for a real reading, which is
a stronger statement than "it might disagree"; it is "there is no way to check
today."

## §4 — Anti-gaming self-check

Per the wave's anti-gaming charge ("find the byte-equality run only against
fixtures, never the deployed reading's DB rows — or the kill-test run against
local dev"): **the charge's first predicted failure mode is exactly what §3
item 1 found**, independently, by a gate-runner agent explicitly instructed to
try to break the claim rather than confirm it. This is reported as a finding,
not softened into a residual, per the master brief's own definition of
anti-gaming (a gate that always reports the same result regardless of whether
the underlying property holds). The charge's second predicted failure mode
(kill-test run against local dev) did **not** occur — the disconnect/resume
battery (§3 item 5) was run against the actual deployed production route, with
a real client-side connection kill, not local dev; the substitution of
client-kill for server-kill was made for shared-infrastructure safety reasons
and is disclosed, not hidden, in §3's final-proof note. Every other
[integrity]-tagged item (2, 4, 11, 12) has direct evidence gathered against
either real production rows or a live production request in this close cycle,
not carried forward from lane-level Verifier claims alone.

## §5 — Residuals (disclosed, not silent)

1. **Cosmetic artifact: dotted domain-pair fragments survive redaction.**
   A fourth production-reading finding, lower severity than the three fixed
   leaks: fragments like `` `this.D1.D1` ``, `` `This.D1.D3` `` appear in
   final prose — the register name got correctly substituted to "this"/"This",
   but a trailing citation suffix (traced to a real `domain_pair` field
   returned by the CDLM retrieval tool, per `retrieval_capability_spec.ts:874`)
   stays attached with no separating space. This is a formatting artifact, not
   an information leak — `D1`/`D2` etc. are already legitimate, established
   divisional-chart vocabulary a reader can parse, unlike the three fixed
   leak classes. **Not fixed this wave**: the SSE stream only ever exposes
   post-lint text (the lint runs delta-by-delta before any event reaches the
   client), so there is no way to capture the true raw pre-redaction string to
   build and verify a targeted fix with the same rigor used for the three
   confirmed fixes. Recommend a follow-up session temporarily instrument the
   delta handler to log raw-vs-cleaned text side by side for one debug
   reading, then design the fix from real data rather than inference.
2. **The golden byte-equality gate is a false-confidence gate, not a passing
   gate with a documented gap.** See §3 item 1 and
   `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md` for the full writeup,
   why the obvious fix is not quick, and the recommended two-part disposition
   (fixture-corpus bridge; real-reading stream capture — independent pieces
   of work, both required before the gate can honestly report what it claims).
3. **`visibilitychange` reconnect at mobile viewport has no test.** The
   behavior exists in shipped code; nothing exercises it. Recommend a
   component or Playwright test firing a real `visibilitychange` event against
   `useLiveStream.ts` at the existing mobile viewport project before this is
   ever cited as verified.
4. **Buffer-eviction and server-grace-window-interrupt paths: unit-tested
   only, not live-triggered.** Both require conditions (500+ buffered events;
   60s of real server silence on an open turn) that were not safe to induce
   against shared production infrastructure this wave. The unit tests for
   both are green; neither has live corroboration.
5. **`conversation_summaries` has zero production rows.** No real reading in
   this wave's verification crossed the summarization threshold, so the
   "sample a real row, confirm no `[multipart content]`, confirm citation
   survival" DB-data sub-check of gate item 8 has nothing to sample —
   INCONCLUSIVE, not a failure, but genuinely unverified against real data.
6. **`tool_call`-kind parts: zero exist in production.** The canonical-name
   sub-check of gate item 2 is vacuously true (nothing to falsify) rather than
   positively demonstrated, because the writer adapter deliberately never
   maps this kind (by disclosed M-2 design — mapping it risked either leaking
   a raw provider tool name or inventing unavailable data).

## §6 — Coordination with the concurrent Śuddha-Vāca / Parishodhana campaigns

Confirmed via `git worktree list` at close: this wave's three hotfix branches
(`pb/2/hotfix-register-leak`, `-v2`, `-v3`) were each cut fresh from
`origin/main` and never touched, merged, or rebased any `suddhavaca/*` or
`parishodhana/*` worktree/branch (both present and active in the worktree list
throughout — `suddhavaca-phase-f-close`, `suddhavaca-rebuild2`, and roughly
two dozen `parishodhana/*` agent worktrees). PB's file scope
(`platform/src/lib/pariprashna/citations/register_leak_lint.ts` and its test,
for all three hotfixes) never overlapped either campaign's territory; confirmed
by diffing every hotfix commit against `platform-mcp/` and
`platform/python-sidecar/` — zero touches, in every case. All three PRs landed
via a self-healing auto-merge monitor that repeatedly nudged BEHIND states
caused by very frequent concurrent commits from both other campaigns landing
on `main` during this wave — none of those concurrent commits were merged,
rebased, or altered by this session; they were only ever fetched as the new
`origin/main` base for a fresh branch.

## §7 — Memo index / Pratinidhi disposition

No Pratinidhi was spawned as a literal separate persona this wave; per the
master brief's allowance, most forks were already answered by BRIEF_PB-2's own
pre-committed rulings (W-1…W-5). One disposition beyond those rulings is
recorded here, in this session's own Pratinidhi-equivalent capacity per the
master brief's "Pratinidhi replaces every human gate":

**Ruling:** PB-2 closes SHIP-DEGRADED on §G item 1 (golden byte-equality) and
the corresponding half of the Final Proof. The real, deployed system was
extensively and independently re-verified to work correctly (§2's four
production-reading rounds, §3's 9 direct PASSes, the live disconnect/resume/
wire-tap evidence) — the gap is specifically in the automated proof mechanism
for one structural claim, not in observed production behavior. Building the
real fix (a genuine 12-fixture-shape bridge with no clean 1:1 mapping for two
event types, plus an entirely separate real-reading stream-capture mechanism)
is out of proportion to attempt inside this close session without the same
Verifier rigor every other fix in this campaign received, and rushing it risks
producing exactly the kind of half-built, silently-lossy bridge this finding
exists to prevent. Filed as `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`,
unscheduled, no owner yet — surfaced explicitly rather than left to be
rediscovered.

## §8 — What PB-3 inherits

- The real, deployed, verified canonical store (`message_parts`,
  `conversation_messages.schema_version`) is the substrate PB-3's ledger binds
  its `message_part_id` FK to.
- The D-16 provenance stamp's read API (`getLastTurnStamp`) is what PB-3's
  ledger-confirmation code calls to COPY stamp fields at confirmation time
  (D-16(d): copy, never a live join) — confirmed live-populated on every real
  turn (§3 item 11).
- **PB-3 should NOT cite PB-2's golden byte-equality gate as proof that the
  canonical store's reducer/writer/DB agree in general.** Per §3 item 1 and
  the follow-up document, it currently proves only that one authored fixture
  round-trips through two independently-coded in-memory functions. Any
  PB-3 (or later) claim resting on canonical-store byte-equality should either
  cite the follow-up's eventual resolution or re-derive its own evidence.
- The three hotfix cycles' register/fact_id-namespace lint (now covering 3
  distinct leak classes) is the citation-safety baseline PB-3's prediction-
  ledger surfacing should inherit and extend, not rebuild.

*End REPORT_PB-2 v1.0 — wave CLOSED, ship-degraded on §G item 1.*
