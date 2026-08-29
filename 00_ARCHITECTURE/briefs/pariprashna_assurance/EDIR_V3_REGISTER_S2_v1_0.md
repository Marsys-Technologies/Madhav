---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S2
version: 1.0
status: LIVING — this is S2's OWN append-only findings register. Only S2
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S2's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S2 appending findings
  can never again produce a git merge conflict against S1, S3, S4, S5, S6
  appending their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md`
  §4a for the full rationale and the other five streams' files). Governed by
  the same Register law and Entry schema as the index file — this file does
  not restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S2
id_convention: >
  New S2 findings are `S2-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). No `S2-V3-E-*` id had been minted
  before this split. **The next S2 id to claim is `S2-V3-E-001`.** Note: S2
  authored and/or was the fix-owning stream for several findings pre-split
  under the shared, un-prefixed `V3-E-nnn` namespace (e.g. V3-E-030 fixed by
  S2; V3-E-021/V3-E-014/V3-E-015 authored during S2-territory investigation
  but filed to S4 as the root-cause-owning stream — "authored by" and "filed
  to" are not always the same stream in the pre-split text, so this file
  does not attempt to hand-attribute a specific list; grep the archive for
  `stream \*\*S2\*\*` / `filed to stream \*\*S2\*\*` to find them). Those
  entries stay in the archive exactly as written and are not renumbered or
  copied here.
changelog:
  - "1.1 (2026-08-30, closeout rebase): backfills three findings
    (V3-E-060, V3-E-061, V3-E-062) discovered and tracker-registered by S2
    on 2026-08-28, under the pre-split shared V3-E-nnn namespace, whose
    prose write-up was stranded on PR #1640 when the A5 split landed first
    (2026-08-29) and PR #1640 went DIRTY/CONFLICTING against the new
    per-stream file layout. These keep their already-minted tracker
    `finding_id`s verbatim (V3-E-060/061/062, not renumbered to
    S2-V3-E-nnn) because the ids are permanent identifiers on live
    `finding_discovered` tracker events — renaming them here would break
    the id↔event link, not just a doc heading. The next NEW S2 id to claim
    remains `S2-V3-E-001`; these three are backfill, not new claims."
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S2's pre-split entries stay in the archive under the shared V3-E-nnn
    namespace, findable there by grep (see id_convention); next id to claim
    is S2-V3-E-001."
---

# Paripraśna EDIR V3 — S2 register

Append new S2 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

## Entries

**Backfill note (2026-08-30):** the three entries below (V3-E-060,
V3-E-061, V3-E-062) were discovered 2026-08-28, before the 2026-08-29
per-stream split, and are backfilled here verbatim from the stranded PR
#1640 branch after a rebase onto the split layout. See the `changelog`
above. The next genuinely NEW S2 finding still claims `S2-V3-E-001`.

---

### V3-E-060 — On any real turn error, the reader sees only a short band label: the explanatory sentence and every safe-next-step action (retry/switch model/continue/settings) are computed but never rendered

- **Class / severity:** DEFECT · S2 major (proposed — directly contradicts
  the test plan's Errors/recovery region requirement: "a failure explains
  what happened... provides a safe next step")
- **Lens(es):** L-CODE (+ L-USER for the live reproduction below)
- **Pipeline stage:** SURFACE (S2: working region / error display)
- **Journey:** composer/errors battery (charter's dedicated
  Send/Stop/retry/validation + network-kill scenarios)
- **Observed (2026-08-28, code read + LIVE reproduction against the
  deployed synthetic-chart Portal, chart `1c826d5a`):**
  - `lib/pariprashna/errors/classify.ts`'s `classifyPariprashnaError`
    produces a rich, genuinely useful `ClassifiedError` for every one of
    its ~10 error kinds: a short `bandLabel`, a fuller explanatory
    `sentence` (e.g. `"Nothing was lost. Try again shortly, or switch
    models."`, `"What arrived is above. The reading can be continued."`),
    and a typed `actions: Array<'retry' | 'switch_model' | 'continue' |
    'settings'>` naming the specific safe next step(s) available.
  - A full-tree grep of every `.tsx` file under `components/pariprashna`
    confirms **zero consumers** of `.sentence` or `.actions` anywhere —
    only `WorkingBand.tsx`'s `turn.error.bandLabel` is ever rendered. No
    retry button, no switch-model affordance, no continue action, no
    longer explanation — for ANY error kind, ever.
  - Live-reproduced: intercepted the turn-submission POST
    (`page.route('**/api/pariprashna', route => route.abort(...))`) to
    force the `NETWORK_HTTPFAIL` path. Result: the band correctly showed
    "The connection was lost" (the bandLabel — accurate) but nothing else
    — no "What arrived is above; nothing was altered." sentence, no
    action. The composer re-enabled empty (not locked, unlike V3-E-024),
    but the reader's only path to retry is to manually retype the entire
    question from scratch — there is no one-click retry despite `actions:
    ['continue']`/`['retry']` being computed for exactly this case.
  - This is the same defect CLASS as V3-E-030's original root cause
    (`gradeSummaryLabel` computed, zero readers) and E-073's
    `unmappedPrimitives`/`compileFailed` — a §N.8 "computed then discarded"
    signal, here spanning the entire typed `ClassifiedErrorAction` surface
    rather than one field.
- **Proposed fix class:** render `turn.error.sentence` (a second line
  under the band label) and `turn.error.actions` (real buttons — Retry
  re-submits the same user text via `CLIENT_SUBMIT_TURN`; Switch model
  opens the model picker; Continue re-opens the stream from the last
  committed block; Settings opens whatever settings surface owns API-key
  renewal) wherever a turn is `status === 'errored'`. This is a genuine
  UI-feature-completion item (new component + click-handler wiring, not a
  one-line fix) — NOT attempted inline during this scenario-completion
  pass per its own scope instruction (land a fix only if small and
  blocking; this blocks nothing — the scenario itself still ran and is
  reported honestly as a gap below).
- **Status:** OPEN, filed to **S2** (own territory) — NOT fixed this
  session; recommended as S2's next real-fix candidate if the stream
  resumes for further remediation work.
- **Close rung required:** INTEGRATION (a fixture/turn reaching `errored`
  status renders a real, clickable action matching `actions[0]`) or LIVE.

---

### V3-E-061 — CRITICAL: the register-leak lint's OWN redaction path times out and leaks a raw, malformed citation sentinel (`⟦cite: ⟧`) straight into reader-facing prose

- **Class / severity:** DEFECT · **S1 blocking (proposed)** — the exact
  mechanism CLAUDE.md names as load-bearing for preventing internal
  fact-id-namespace leaks (`citations/register_leak_lint.ts`,
  `citations/rewriter.ts`) has a live failure mode where a timeout in its
  own redaction step results in malformed internal template syntax
  reaching the reader — precisely the class of defect the "No Raw Token
  in Narrative" CI gate (D-01e) exists to catch, observed live in
  production despite that gate.
- **Lens(es):** L-WIRE + L-USER
- **Pipeline stage:** S8/S9 (synthesis + citation rewriter/register-leak
  lint) — NOT S2; this is server-side wire content, not a client
  rendering defect (confirmed below).
- **Journey:** J9 mobile sub-run (J2-equivalent standard reading); not
  mobile-specific — the defect is in the server response body itself and
  would reproduce identically on desktop.
- **Observed (2026-08-28, LIVE, deployed `amjis-web@cafa894ee`, chart
  `1c826d5a`, question: "What does this period ask of my career?"):** the
  settled reading's final sentence read, verbatim: *"Because wealth-
  building is currently shadowed by the A6 Arudha of competitors ⟦cite:
  ⟧, sustainable career success right now depends entirely on..."* — a
  literal, empty, malformed citation-sentinel token (`⟦cite: ⟧`), not a
  resolved `[9]`-style chip reference, sitting directly in the rendered
  paragraph. The dock's own persistent hint text confirms the intended
  design: "Cited in prose as ⟦n⟧ — a chip click opens its row here" — this
  is that exact syntax family, broken.
- **Root cause, confirmed via the raw SSE capture (proves this is NOT a
  client rendering bug):** immediately before the malformed delta arrived,
  the wire carried two flag events back-to-back:
  ```
  flag: register_leak:redact, detail: fact_id_namespace   (level: warn)
  flag: malformed_sentinel,   detail: timeout             (level: warn)
  ```
  followed immediately by the next `block.delta` containing the raw
  `⟦cite: ⟧` text. Reading this in sequence: the register-leak lint
  correctly DETECTED an attempted internal fact-id-namespace leak in the
  model's own output and tried to redact/rewrite it — but that
  redaction/rewrite step **timed out**, and instead of a safe fallback
  (drop the sentinel silently, or substitute a genuinely resolved
  citation, or at minimum emit a well-formed empty state), the pipeline's
  degraded path sent the raw, half-rewritten sentinel straight through to
  the client, which faithfully rendered exactly what it received.
  `AnswerRegion.tsx`/`FrozenBlock.tsx` (S2, confirmed by code read) do no
  sentinel-specific post-processing of committed block text — they render
  server-provided HTML/text as-is, exactly as designed; the leak happens
  upstream of anything S2 owns.
- **Why S1-severity, not S3/S4-minor cosmetic:** this is not merely an
  ugly rendering artifact — it is a live, reproducible failure of the
  SPECIFIC mechanism whose job is preventing internal namespace strings
  from reaching the reader (`register_leak:redact` firing on
  `fact_id_namespace` is itself evidence the model attempted to emit
  something requiring redaction). In this instance the fallback path's
  malformed output happened to be an EMPTY placeholder rather than the
  raw internal content itself — but the failure mode (timeout → send the
  half-processed intermediate state anyway, rather than a safe redacted
  fallback) is exactly the shape of bug that COULD leak real internal
  content on a slower/larger redaction case. This needs to be verified
  further to see whether a timeout can also leak actual pre-redaction
  content, not assumed safe on this one observation.
- **Proposed fix class:** the citation-rewriter/register-leak-lint stage's
  timeout path must fail CLOSED (drop the malformed segment or substitute
  an honest "[citation pending]"-class placeholder, never forward
  unresolved internal template syntax) rather than failing open by
  forwarding whatever partial state existed at timeout. Squarely S4
  (pipeline S8/S9 stage) territory per the elevation crosswalk, with a
  direct cross-reference to **S5** given the security-adjacent nature
  (this is the register-leak-prevention mechanism itself failing, not an
  unrelated formatting bug).
- **Status:** OPEN, filed to stream **S4** (primary — pipeline S8/S9
  root cause) with a cross-reference to **S5** (security-adjacent: verify
  whether the timeout path can leak genuine internal content, not just an
  empty malformed sentinel, on a different/slower turn). NOT fixed by S2
  (out of territory; S2's own rendering confirmed correct).
- **Close rung required:** INTEGRATION (a seeded slow-redaction fixture
  demonstrating the timeout path now fails closed) or LIVE re-proof.
- **Corroboration (2026-08-28, S2, coverage-completion pass):** reproduced
  a SECOND time on an independent turn/question ("What does my 7th house
  lord placement say about partnerships?") — "It resides there alongside
  Jupiter, the 9th lord sitting powerfully in its own sign ⟦cite: ⟧." —
  confirming this is a real, recurring defect, not a one-off fluke.
- **Disposition update (2026-08-30, closeout rebase, backfilled from the
  live tracker, not this file):** the Native Surrogate disposed this
  finding as `COMMISSION_FIX_THIS_CAMPAIGN` (tracker event `d9fd0274`).
  A fix is in flight on PR #1659 ("fix(pariprashna): V3-E-061 citation
  register-leak fails closed, not open (CRITICAL)"), targeting
  `platform/src/lib/pariprashna/citations/rewriter.ts` +
  `citations/types.ts`, with new fail-closed tests. As of this backfill
  PR #1659 is OPEN (not yet merged) — S2 is not duplicating that fix here;
  see PR #1659 and the tracker's own remediation record for the
  authoritative close.
- **Addendum — V3-E-024 (safety-hold turns also affected) (2026-08-28, S2,
  coverage-completion pass, J4 mobile sub-run):** the SAME root cause as
  V3-E-024 (the `turn.close`/`turn.commit` composer-lock bug, see the
  archived pre-split entry) reproduces on a second, independent trigger
  path — a mortality question ("Exactly what year and how will I die?")
  correctly hit the safety hard-stop and sealed with a calm, well-written
  review-pending message (`flag:safety_decision:seal_pending_signoff`, "2
  safety class(es) detected"), but its wire trace is identical in shape to
  the clarification case: `block.commit` → `phase:plan end` → `turn.close,
  status:"ok", ms:448` — **no `turn.commit`, same stuck-composer
  symptom**. This means the deployed bug's real-world exposure is broader
  than originally scoped: EVERY safety-held/sealed turn (not only
  clarifications) currently locks the composer on production. The
  already-landed fix (broadened `turn.close` guard, PR #1612) covers this
  path too — no separate fix needed — but this raised the urgency of the
  deploy-sync re-proof, since it meant the hard-stop corpus itself was
  briefly unusable end-to-end on the live site (the safety message
  displayed correctly; the reader just could not ask a follow-up
  afterward without a hard reload). Filed here as an addendum rather than
  in the archived V3-E-024 entry per this file's own append-only law (do
  not edit an existing entry's observed text).

---

### V3-E-062 — The Portal renders zero heading elements anywhere on the page; visual hierarchy (wordmark, "Ask the chart.", section labels) is entirely unconveyed to assistive technology

- **Class / severity:** DEFECT · S3 minor-to-moderate (proposed — a real
  gap past the automated axe floor, matching test plan §8.2's own warning
  that "automated axe is a floor, not proof"; the existing `g-axe.spec.ts`
  gate passed "zero critical/serious violations" on this exact surface
  without catching this, because heading-structure rules are typically
  best-practice-tier in axe-core's default ruleset, not wcag2a/aa)
- **Lens(es):** L-CODE + L-USER
- **Pipeline stage:** SURFACE (S2: empty-state / thread-header / working
  region — none of these currently emit an `<h1>`–`<h6>`)
- **Journey:** collateral (a11y manual-verification pass, past the
  automated axe floor per charter's explicit mandate: "every
  accessibility claim is manual-verified past the axe floor")
- **Observed (2026-08-28, LIVE, deployed `amjis-web@cafa894ee`, chart
  `1c826d5a`):** `document.querySelectorAll('h1,h2,h3,h4,h5,h6')` returns
  an EMPTY array on the empty-state page. Landmarks (`<nav>`×2, `<main>`)
  and the skip-link ARE correctly present and functional (confirmed:
  `#main-content` target exists) — this is not a full landmark-structure
  failure, specifically a missing-headings gap. The visually
  heading-styled "Ask the chart." prompt (large serif text, the page's
  own de facto title for the empty state) and the "Paripraśna" wordmark
  are both plain `<span>`/`<div>` elements with no semantic heading role
  — a screen-reader user navigating by heading (a standard AT shortcut,
  e.g. VoiceOver's rotor, NVDA's `H` key) finds nothing on this surface at
  all, regardless of how much content has settled.
- **Proposed fix class:** mark the empty-state's "Ask the chart." prompt
  (and/or the chart-holder's name in `ThreadHeader.tsx`) as a real
  heading element (`<h1>` for the page's primary content anchor), and
  consider whether settled-turn section labels warrant `<h2>`/`<h3>` — a
  design decision for whoever owns the heading-hierarchy call, not
  assumed here.
- **Status:** OPEN, filed to **S2** (own territory: `ThreadHeader.tsx`,
  the empty-state prompt component) — NOT fixed this pass (a heading-level
  choice is a small design decision better made deliberately than as a
  drive-by edit during a coverage-completion pass).
- **Close rung required:** INTEGRATION (a component test asserting at
  least one heading element exists on every Portal surface state) or LIVE.
