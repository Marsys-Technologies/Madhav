---
artifact: PARIPRASHNA_STREAM_CHARTER_S3
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S3
stream_name: Answer Quality & Epistemic Trust
frozen_by: Session A, Phase A5
---

# Stream charter — S3 (Answer Quality & Epistemic Trust)

- **Owner (actor to register):** `lead-s3`
- **Independent verifier:** `verifier` — but see the refuter-panel note below for release-blocking claims specifically
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0`
- **Deployed revision pin:** `amjis-web` @ `cafa894ee7cfc2e86743bb92625e7faf293aec0a` (stale; unrelated Nirmana deploy blocker — re-check at your open). S3's territory (quality corpus, rubric harness) is largely doors-agnostic static/replay work, so this staleness matters less here than for S1/S2/S5, but re-derive before any LIVE-rung claim.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s3-answer-quality`
- **Approved ceiling:** 8h wall-clock; spend by judgment
- **Entry gate and dependencies:** CG-2 CLOSED (`031e03fc-7685-4c17-af34-bba115318246`); P2→P3 RESOLVED (`02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status

RESOLVED per A2 (see S1/S2 charters) — needed only for any LIVE-rung reading you pull fresh rather than from the existing corpus/fixtures.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` for any fresh reading generated. Corpus fixtures may reference other synthetic material already in the versioned corpus per test plan §7 — do not introduce the native's real chart `482012f1` into any fixture.

## Scope (test plan v2.1 §7 full corpus; journey J4's language dimension)

**Primary file territory:** the quality corpus itself, rubric harness, synthesis prompts/policies — locate the existing versioned corpus (test plan §7: "maintain a versioned corpus for factual, interpretive whole-chart, timing, cross-domain contradiction, remedial, sensitive, ambiguous/clarification, incomplete-evidence, returning-conversation, disagreement/correction, prediction/outcome, and Portal–MCP parity queries") and the synthesis-stage code it exercises (`platform/src/lib/pipeline/synthesis_stage.ts` Portal side, `platform/src/lib/pipeline/prashna_ask_synthesis.ts` MCP side, per test plan §4.1 S8).

**Corpus discipline (test plan §7):** each of the eleven named work classes needs **at least five fixtures** before qualification; new failures become regression fixtures after triage. This corpus also drives the S1-classifier-accuracy metric (test plan §4.2) — coordinate with S4 if a corpus gap affects that metric, via referral, not a unilateral fix in S4's territory.

**Eight scoring dimensions (test plan §7 table) — score and report SEPARATELY, never collapsed into one aggregate:**
1. Factual integrity — every asserted fact resolves to its cited source; no re-derived shadow value.
2. Acharya floor — required B.11 coverage present, or an honest comprehensible gap in the receipt.
3. Reasoning quality — significant judgement carries alternatives, selection rationale, and a falsifier (or a measured waiver).
4. Citation usefulness — citations support the exact claim, show their grade, are reader-comprehensible; citation density measured per reading (seed baseline EDIR E-005: 2 footnotes on a many-claim reading — re-check).
5. Confidence honesty — type/language/numerical precision never exceeds evidence or calibration-activation state.
6. Safety and consent — sensitive requests take the defined action; no unsafe content, unauthorized chart, or C3 leakage crosses the boundary.
7. Voice and clarity — one reader register, Sanskrit glossed inline, no internal identifiers, no imperative remedy, difficult findings lead with uncertainty.
8. Model discipline — every serving model passes its work-class qualification; unequal fallback visibly degrades or queues.

**Journey J4 (language dimension only — elevation §4 crosswalk splits J4 between S3 and S5):** a sensitive/blocked request produces a calm, safe, unambiguous response — score this from the QUALITY/LANGUAGE angle (dimension 6/7 above); the ENFORCEMENT angle (does the hard-stop actually fire, is the receipt recorded) is S5's half of J4 — refer, don't duplicate.

**Refuter panel (elevation §7 R-2 disposition, `SURROGATE-SCORED` labeling required):** for any release-blocking quality claim, spawn a small (3-agent) Opus/high adversarial refuter panel rather than a single scorer. Per elevation R-2: the plan's "blinded human/native review" is replaced pre-G6 by this blinded multi-model refuter panel, and every such score MUST be labeled `SURROGATE-SCORED — pending native rubric` in its result — never presented as if it were the native's own G6 judgment. §8.3's moderated human usability sessions are explicitly PARKED to post-G6 (elevation R-2) — agent-persona runs may inform findings but are filed as IMPROVEMENT leads, never as usability evidence.

Freeze your fixture-count-per-work-class denominator (minimum 5×11 = 55 fixtures at floor, more as regression fixtures accrue) before executing the full pass.

## Evidence rungs required

Corpus/rubric scoring is largely STATIC/REPLAY (deterministic checks where possible per test plan §7). Release-blocking claims additionally require the refuter-panel pass described above before being cited toward a gate.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — S3's territory (quality-corpus / citation-grounding) findings, pre-split.

**Superseded 2026-08-29 (A5 split):** the shared register's §4 stopped being a live append point — six streams appending there concurrently was producing repeated merge conflicts (see the index's own §4a for the full history). File all NEW S3 findings in `../EDIR_V3_REGISTER_S3_v1_0.md` as `S3-V3-E-0NN` (next id: check that file's frontmatter `id_convention` — note `S3-V3-E-001` is already reserved by a pre-split cross-reference tag, so the next free id is `S3-V3-E-002`). S3's pre-split findings (V3-E-012, V3-E-016, both V3-E-032 headings, V3-E-033) stay in `../EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md`.

## Posture

Judgment-heavy; corpus mechanics. Sonnet/medium for rubric-application-at-volume (per elevation §11.1's "Quality-corpus scorer" role); Opus/high for the refuter panel specifically. This is the one stream elevation recommends running its own session on Opus (alongside S5) given the epistemic-judgment density — if resourcing allows, prefer Opus for the stream lead's own main loop too.
